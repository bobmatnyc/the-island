import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { Search, Users, Building2, MapPin, Eye, Sparkles, X, ArrowRight } from 'lucide-react';
import { api, type Entity } from '@/lib/api';
import { Card, CardContent, CardHeader, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { formatEntityName } from '@/utils/nameFormat';
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from '@/components/ui/pagination';

type EntityType = 'all' | 'person' | 'organization' | 'location';

const PAGE_SIZE = 100;

// Unified filter state interface
interface FilterState {
  search: string;
  entityType: EntityType;
  hasBiography: boolean;
  categories: string[];
  minConnections: number;
  page: number;
}

// Note: Default filter values are defined inline in useState initializer

export function Entities() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [entities, setEntities] = useState<Entity[]>([]);
  const [totalEntities, setTotalEntities] = useState(0);
  const [loading, setLoading] = useState(true);
  const [globalMaxConnections, setGlobalMaxConnections] = useState(100);

  // Unified filter state
  const [filters, setFilters] = useState<FilterState>(() => {
    // Initialize from URL parameters
    const params = Object.fromEntries(searchParams.entries());
    return {
      search: params.search || '',
      entityType: (params.type as EntityType) || 'all',
      hasBiography: params.bio === 'true',
      categories: params.categories ? params.categories.split(',').filter(Boolean) : [],
      minConnections: parseInt(params.minConnections || '0', 10),
      page: parseInt(params.page || '1', 10),
    };
  });

  // Debounced search query
  const [debouncedSearch, setDebouncedSearch] = useState(filters.search);

  // Debounce search with 500ms delay
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(filters.search);
    }, 500);

    return () => clearTimeout(timer);
  }, [filters.search]);

  // Fetch global max connection count once on mount
  useEffect(() => {
    const fetchGlobalMax = async () => {
      try {
        // Fetch all entities to find true maximum
        const response = await api.getEntities({ limit: 2000 });

        // Find the maximum connection_count across ALL entities
        const max = Math.max(
          ...response.entities.map(e => e.connection_count || 0),
          100 // Fallback minimum
        );

        setGlobalMaxConnections(max);
        console.log(`Global max connections: ${max}`);
      } catch (error) {
        console.error('Failed to fetch global max connections:', error);
        // Fallback to a reasonable default
        setGlobalMaxConnections(1500);
      }
    };

    fetchGlobalMax();
  }, []); // Empty dependency array = run once on mount

  // Update filters with automatic page reset
  const updateFilter = <K extends keyof FilterState>(
    key: K,
    value: FilterState[K]
  ) => {
    setFilters(prev => ({
      ...prev,
      [key]: value,
      // Reset to page 1 when any filter changes (except page itself)
      page: key === 'page' ? value as number : 1,
    }));
  };

  // Sync filters to URL parameters
  useEffect(() => {
    const params = new URLSearchParams();

    if (filters.search) params.set('search', filters.search);
    if (filters.entityType !== 'all') params.set('type', filters.entityType);
    if (filters.hasBiography) params.set('bio', 'true');
    if (filters.categories.length > 0) params.set('categories', filters.categories.join(','));
    if (filters.minConnections > 0) params.set('minConnections', filters.minConnections.toString());
    if (filters.page > 1) params.set('page', filters.page.toString());

    setSearchParams(params, { replace: true });
  }, [filters, setSearchParams]);

  // Single useEffect for data loading - triggers when filters or debounced search changes
  useEffect(() => {
    const loadEntities = async () => {
      setLoading(true);
      try {
        const offset = (filters.page - 1) * PAGE_SIZE;
        const response = await api.getEntities({
          limit: PAGE_SIZE,
          offset,
          search: debouncedSearch || undefined,
          entity_type: filters.entityType !== 'all' ? filters.entityType : undefined,
          has_biography: filters.hasBiography || undefined,
        });

        // Apply client-side filters
        let filteredEntities = response.entities;

        // Category filter (OR logic: entity matches ANY selected category)
        if (filters.categories.length > 0) {
          filteredEntities = filteredEntities.filter(entity =>
            filters.categories.some(selectedCat =>
              entity.bio?.relationship_categories?.some(cat => cat.type === selectedCat)
            )
          );
        }

        // Connection filter (minimum connections)
        filteredEntities = filteredEntities.filter(entity =>
          (entity.connection_count || 0) >= filters.minConnections
        );

        setEntities(filteredEntities);
        setTotalEntities(filteredEntities.length);
      } catch (error) {
        console.error('Failed to load entities:', error);
      } finally {
        setLoading(false);
      }
    };

    loadEntities();
  }, [debouncedSearch, filters.entityType, filters.hasBiography, filters.categories, filters.minConnections, filters.page]);

  const handleBadgeClick = (categoryType: string) => {
    setFilters(prev => {
      const isSelected = prev.categories.includes(categoryType);
      const updated = isSelected
        ? prev.categories.filter(cat => cat !== categoryType)
        : [...prev.categories, categoryType];

      return {
        ...prev,
        categories: updated,
        page: 1, // Reset to page 1
      };
    });
  };

  const handleRemoveCategory = (categoryType: string) => {
    setFilters(prev => ({
      ...prev,
      categories: prev.categories.filter(cat => cat !== categoryType),
      page: 1,
    }));
  };

  const handleClearAllFilters = () => {
    setFilters(prev => ({
      ...prev,
      categories: [],
      page: 1,
    }));
  };

  // Helper to get category display data from ontology
  const getCategoryData = (categoryType: string) => {
    const categoryMap: Record<string, { label: string; color: string; bg_color: string }> = {
      'victims': { label: 'Victims', color: '#DC2626', bg_color: '#FEE2E2' },
      'co-conspirators': { label: 'Co-Conspirators', color: '#EA580C', bg_color: '#FFEDD5' },
      'frequent_travelers': { label: 'Frequent Travelers', color: '#EAB308', bg_color: '#FEF9C3' },
      'social_contacts': { label: 'Social Contacts', color: '#84CC16', bg_color: '#ECFCCB' },
      'associates': { label: 'Associates', color: '#F59E0B', bg_color: '#FEF3C7' },
      'legal_professionals': { label: 'Legal Professionals', color: '#06B6D4', bg_color: '#CFFAFE' },
      'investigators': { label: 'Investigators', color: '#3B82F6', bg_color: '#DBEAFE' },
      'public_figures': { label: 'Public Figures', color: '#8B5CF6', bg_color: '#EDE9FE' },
      'peripheral': { label: 'Peripheral', color: '#6B7280', bg_color: '#F3F4F6' },
    };
    return categoryMap[categoryType] || { label: categoryType, color: '#6B7280', bg_color: '#F3F4F6' };
  };

  const getEntityType = (entity: Entity): EntityType => {
    if (entity.entity_type === 'organization') return 'organization';
    if (entity.entity_type === 'location') return 'location';
    return 'person';
  };

  const getEntityIcon = (entity: Entity) => {
    const type = getEntityType(entity);
    switch (type) {
      case 'organization':
        return <Building2 className="h-5 w-5" />;
      case 'location':
        return <MapPin className="h-5 w-5" />;
      default:
        return <Users className="h-5 w-5" />;
    }
  };

  // Initial loading state (full page spinner)
  if (loading && entities.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent mb-4" />
          <p className="text-muted-foreground">Loading entities...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)]">
      {/* FIXED FILTER HEADER */}
      <div className="sticky top-0 z-10 bg-background border-b p-6 space-y-4">
        {/* Page Title */}
        <div>
          <h1 className="text-3xl font-bold mb-2">Entities</h1>
          <p className="text-muted-foreground">
            Explore {totalEntities.toLocaleString()} people, organizations, and locations from the Epstein archive.
          </p>
        </div>

        {/* Search Input */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            type="text"
            placeholder="Search all 1,637 entities by name..."
            value={filters.search}
            onChange={(e) => updateFilter('search', e.target.value)}
            className="pl-10"
          />
          {filters.search !== debouncedSearch && (
            <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-solid border-current border-r-transparent" />
            </div>
          )}
        </div>

        {/* Type Filters */}
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => updateFilter('entityType', 'all')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              filters.entityType === 'all'
                ? 'bg-primary text-primary-foreground'
                : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
            }`}
          >
            All
          </button>
          <button
            onClick={() => updateFilter('entityType', 'person')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2 ${
              filters.entityType === 'person'
                ? 'bg-primary text-primary-foreground'
                : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
            }`}
          >
            <Users className="h-4 w-4" />
            Person
          </button>
          <button
            onClick={() => updateFilter('entityType', 'organization')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2 ${
              filters.entityType === 'organization'
                ? 'bg-primary text-primary-foreground'
                : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
            }`}
          >
            <Building2 className="h-4 w-4" />
            Organization
          </button>
          <button
            onClick={() => updateFilter('entityType', 'location')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2 ${
              filters.entityType === 'location'
                ? 'bg-primary text-primary-foreground'
                : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
            }`}
          >
            <MapPin className="h-4 w-4" />
            Location
          </button>

          {/* Biography Filter - Divider */}
          <div className="w-px bg-border mx-1" />

          {/* Biography Filter */}
          <button
            onClick={() => updateFilter('hasBiography', !filters.hasBiography)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2 ${
              filters.hasBiography
                ? 'bg-primary text-primary-foreground'
                : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
            }`}
            title="Filter entities that have AI-generated biographies"
          >
            <Sparkles className="h-4 w-4" />
            With Biography
          </button>
        </div>

        {/* Connection Threshold Slider */}
        <div className="bg-secondary/30 border border-border rounded-lg p-4">
          <div className="flex items-center justify-between gap-4 mb-3">
            <label className="text-sm font-medium flex items-center gap-2">
              Minimum Connections: <span className="text-primary font-bold">{filters.minConnections}</span>
              <span
                className="text-muted-foreground cursor-help"
                title="Connections represent co-appearances in flight logs. Not all entities appear in the flight network."
              >
                ℹ️
              </span>
            </label>
            <span className="text-xs text-muted-foreground">
              (Showing {totalEntities.toLocaleString()} entities)
            </span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-muted-foreground">0</span>
            <input
              type="range"
              min="0"
              max={globalMaxConnections}
              value={filters.minConnections}
              onChange={(e) => updateFilter('minConnections', Number(e.target.value))}
              className="flex-1 h-2 bg-secondary rounded-lg appearance-none cursor-pointer accent-primary"
              title={`Filter entities with at least ${filters.minConnections} connections`}
            />
            <span className="text-xs text-muted-foreground">{globalMaxConnections}</span>
          </div>
          <div className="mt-2 text-xs text-muted-foreground">
            {filters.minConnections === 0 && "Showing all entities (including those with no connections)"}
            {filters.minConnections === 1 && "Hiding entities with 0 connections"}
            {filters.minConnections > 1 && `Showing only entities with ${filters.minConnections}+ connections`}
          </div>
        </div>

        {/* Active Category Filters Bar */}
        {filters.categories.length > 0 && (
          <div className="bg-primary/5 border border-primary/20 rounded-lg p-4">
            <div className="flex items-center justify-between gap-4 flex-wrap">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-sm font-medium">Filters:</span>

                {/* Individual removable category badges */}
                {filters.categories.map(catType => {
                  const catData = getCategoryData(catType);
                  return (
                    <button
                      key={catType}
                      onClick={() => handleRemoveCategory(catType)}
                      className="inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm font-semibold transition-all hover:opacity-80 hover:scale-105 cursor-pointer focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                      style={{
                        backgroundColor: catData.bg_color,
                        color: catData.color,
                        border: `1px solid ${catData.color}40`
                      }}
                      title={`Remove ${catData.label} filter`}
                    >
                      {catData.label}
                      <X className="h-3.5 w-3.5" />
                    </button>
                  );
                })}

                {/* Count */}
                <span className="text-sm text-muted-foreground">
                  ({totalEntities} {totalEntities === 1 ? 'entity' : 'entities'})
                </span>
              </div>

              {/* Clear All button */}
              <Button
                variant="ghost"
                size="sm"
                onClick={handleClearAllFilters}
                className="gap-2"
              >
                <X className="h-4 w-4" />
                Clear All
              </Button>
            </div>
          </div>
        )}

        {/* Results Count */}
        <div className="text-sm text-muted-foreground">
          {totalEntities === 0 ? (
            'No entities found'
          ) : (
            <>
              Showing {((filters.page - 1) * PAGE_SIZE) + 1}-{Math.min(filters.page * PAGE_SIZE, totalEntities)} of {totalEntities.toLocaleString()} entities
              {(debouncedSearch || filters.entityType !== 'all' || filters.hasBiography || filters.categories.length > 0) && (
                <span className="ml-2 text-primary">
                  (filtered)
                </span>
              )}
            </>
          )}
        </div>
      </div>

      {/* SCROLLABLE GRID SECTION */}
      <div className="flex-1 overflow-y-auto p-6 relative">
        {/* Loading Overlay (for filter changes) */}
        {loading && entities.length > 0 && (
          <div className="absolute inset-0 bg-background/50 flex items-center justify-center z-20">
            <div className="bg-background border rounded-lg p-6 shadow-lg">
              <div className="animate-spin rounded-full h-8 w-8 border-4 border-primary border-t-transparent mx-auto mb-3" />
              <p className="text-sm text-muted-foreground">Loading entities...</p>
            </div>
          </div>
        )}

        {/* Entities Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {entities.map((entity) => {
            // Get primary category if available
            const primaryCategory = entity.bio?.relationship_categories?.reduce((prev, curr) =>
              curr.priority < prev.priority ? curr : prev
            );

            return (
              <Card
                key={entity.id}
                className="hover:shadow-lg transition-shadow h-full flex flex-col"
                data-testid="entity-card"
              >
                <CardHeader className="pb-3">
                  {/* Entity Name (clickable) + Details Button */}
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start gap-2 flex-1 min-w-0">
                      <div className="text-muted-foreground mt-1">{getEntityIcon(entity)}</div>
                      <Link
                        to={`/entities/${entity.id}`}
                        className="text-xl font-semibold leading-tight break-words hover:text-primary hover:underline transition-colors"
                      >
                        {formatEntityName(entity.name, entity.entity_type)}
                      </Link>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      asChild
                      className="shrink-0 -mt-1"
                    >
                      <Link to={`/entities/${entity.id}`} className="gap-1">
                        Details
                        <ArrowRight className="h-4 w-4" />
                      </Link>
                    </Button>
                  </div>
                </CardHeader>

                <CardContent className="space-y-3 flex-1">
                  {/* Stats */}
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div className="flex items-center gap-1.5">
                      <Users className="h-4 w-4 text-muted-foreground" />
                      <span className="text-muted-foreground">Connections:</span>
                      <span className="font-medium">{entity.connection_count}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Eye className="h-4 w-4 text-muted-foreground" />
                      <span className="text-muted-foreground">Documents:</span>
                      <span className="font-medium">{entity.total_documents}</span>
                    </div>
                  </div>

                  {/* Biography Summary */}
                  {entity.bio?.summary && (
                    <div className="pt-2 border-t">
                      <p className="text-sm text-muted-foreground italic line-clamp-3">
                        {entity.bio.summary}
                      </p>
                    </div>
                  )}
                </CardContent>

                {/* Footer with Category Badge + Source Badges */}
                <CardFooter className="flex flex-wrap gap-2 pt-4 border-t">
                  {/* Category Badge - Clickable Filter with Selection Indicator */}
                  {primaryCategory && (
                    <button
                      onClick={(e) => {
                        e.preventDefault();
                        handleBadgeClick(primaryCategory.type);
                      }}
                      className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold transition-all hover:opacity-80 hover:scale-105 cursor-pointer focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 ${
                        filters.categories.includes(primaryCategory.type) ? 'ring-2 ring-offset-2' : ''
                      }`}
                      style={{
                        backgroundColor: primaryCategory.bg_color,
                        color: primaryCategory.color,
                        border: filters.categories.includes(primaryCategory.type)
                          ? `2px solid ${primaryCategory.color}`
                          : `1px solid ${primaryCategory.color}40`
                      }}
                      title={filters.categories.includes(primaryCategory.type)
                        ? `Remove ${primaryCategory.label} filter`
                        : `Filter by ${primaryCategory.label}`}
                    >
                      {primaryCategory.label}
                      {filters.categories.includes(primaryCategory.type) && (
                        <span className="ml-1 text-xs">✓</span>
                      )}
                    </button>
                  )}

                  {/* Source Badges - Informational */}
                  {entity.in_black_book && (
                    <Badge variant="outline" className="cursor-default text-xs">
                      📖 Black Book
                    </Badge>
                  )}
                  {entity.sources.includes('flight_logs') && (
                    <Badge variant="outline" className="cursor-default text-xs">
                      ✈️ Flight Logs
                    </Badge>
                  )}
                  {entity.news_articles_count && entity.news_articles_count > 0 && (
                    <Badge variant="outline" className="cursor-default text-xs">
                      📰 News ({entity.news_articles_count})
                    </Badge>
                  )}
                  {entity.timeline_events_count && entity.timeline_events_count > 0 && (
                    <Badge variant="outline" className="cursor-default text-xs">
                      📅 Timeline ({entity.timeline_events_count})
                    </Badge>
                  )}
                  {entity.is_billionaire && (
                    <Badge variant="outline" className="cursor-default text-xs">
                      💰 Billionaire
                    </Badge>
                  )}
                  {entity.bio?.summary && (
                    <Badge variant="outline" className="cursor-default text-xs bg-primary/5 border-primary/20 text-primary">
                      <Sparkles className="h-3 w-3 mr-1" />
                      Biography
                    </Badge>
                  )}
                </CardFooter>
              </Card>
            );
          })}
        </div>

        {/* Empty State */}
        {entities.length === 0 && !loading && (
          <div className="text-center py-12">
            <Users className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <p className="text-lg font-medium mb-1">No entities found</p>
            <p className="text-muted-foreground">
              {debouncedSearch || filters.entityType !== 'all' || filters.hasBiography || filters.categories.length > 0
                ? 'Try adjusting your search or filter criteria'
                : 'No entities available'}
            </p>
          </div>
        )}

        {/* Pagination Controls */}
        {totalEntities > PAGE_SIZE && (
          <Pagination className="mt-8">
            <PaginationContent>
              <PaginationItem>
                <PaginationPrevious
                  onClick={(e) => {
                    e.preventDefault();
                    if (filters.page > 1) {
                      updateFilter('page', filters.page - 1);
                    }
                  }}
                  className={filters.page === 1 ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
                />
              </PaginationItem>

              {/* Page Numbers */}
              {(() => {
                const totalPages = Math.ceil(totalEntities / PAGE_SIZE);
                const pages: React.ReactNode[] = [];
                const maxVisible = 5;

                let startPage = Math.max(1, filters.page - Math.floor(maxVisible / 2));
                let endPage = Math.min(totalPages, startPage + maxVisible - 1);

                if (endPage - startPage < maxVisible - 1) {
                  startPage = Math.max(1, endPage - maxVisible + 1);
                }

                // First page
                if (startPage > 1) {
                  pages.push(
                    <PaginationItem key={1}>
                      <PaginationLink
                        onClick={(e) => {
                          e.preventDefault();
                          updateFilter('page', 1);
                        }}
                        isActive={filters.page === 1}
                        className="cursor-pointer"
                      >
                        1
                      </PaginationLink>
                    </PaginationItem>
                  );
                  if (startPage > 2) {
                    pages.push(
                      <PaginationItem key="ellipsis-1">
                        <PaginationEllipsis />
                      </PaginationItem>
                    );
                  }
                }

                // Middle pages
                for (let i = startPage; i <= endPage; i++) {
                  pages.push(
                    <PaginationItem key={i}>
                      <PaginationLink
                        onClick={(e) => {
                          e.preventDefault();
                          updateFilter('page', i);
                        }}
                        isActive={filters.page === i}
                        className="cursor-pointer"
                      >
                        {i}
                      </PaginationLink>
                    </PaginationItem>
                  );
                }

                // Last page
                if (endPage < totalPages) {
                  if (endPage < totalPages - 1) {
                    pages.push(
                      <PaginationItem key="ellipsis-2">
                        <PaginationEllipsis />
                      </PaginationItem>
                    );
                  }
                  pages.push(
                    <PaginationItem key={totalPages}>
                      <PaginationLink
                        onClick={(e) => {
                          e.preventDefault();
                          updateFilter('page', totalPages);
                        }}
                        isActive={filters.page === totalPages}
                        className="cursor-pointer"
                      >
                        {totalPages}
                      </PaginationLink>
                    </PaginationItem>
                  );
                }

                return pages;
              })()}

              <PaginationItem>
                <PaginationNext
                  onClick={(e) => {
                    e.preventDefault();
                    const totalPages = Math.ceil(totalEntities / PAGE_SIZE);
                    if (filters.page < totalPages) {
                      updateFilter('page', filters.page + 1);
                    }
                  }}
                  className={filters.page >= Math.ceil(totalEntities / PAGE_SIZE) ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
                />
              </PaginationItem>
            </PaginationContent>
          </Pagination>
        )}
      </div>
    </div>
  );
}
