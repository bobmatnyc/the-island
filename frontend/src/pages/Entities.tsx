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

export function Entities() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [entities, setEntities] = useState<Entity[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [selectedType, setSelectedType] = useState<EntityType>('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalEntities, setTotalEntities] = useState(0);
  const [showOnlyWithBio, setShowOnlyWithBio] = useState(false);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [minConnections, setMinConnections] = useState(1);  // Default: hide 0-connection entities
  const [maxConnections, setMaxConnections] = useState(100);  // Will be updated from data

  // Initialize filters from URL parameters on mount
  useEffect(() => {
    const bioParam = searchParams.get('bio');
    const categoriesParam = searchParams.get('categories');
    const minConnsParam = searchParams.get('minConnections');

    if (bioParam === 'true') {
      setShowOnlyWithBio(true);
    }
    if (categoriesParam) {
      setSelectedCategories(categoriesParam.split(',').filter(Boolean));
    }
    if (minConnsParam) {
      const minConns = parseInt(minConnsParam, 10);
      if (!isNaN(minConns) && minConns >= 0) {
        setMinConnections(minConns);
      }
    }
  }, []);

  // Debounce search query (500ms delay)
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchQuery);
    }, 500);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Load entities when page, search, type, biography, category, or connection filter changes
  useEffect(() => {
    loadEntities();
  }, [currentPage, debouncedSearch, selectedType, showOnlyWithBio, selectedCategories, minConnections]);

  // Reset to page 1 when search or filters change
  useEffect(() => {
    if (currentPage !== 1) {
      setCurrentPage(1);
    }
  }, [debouncedSearch, selectedType, showOnlyWithBio, selectedCategories, minConnections]);

  const loadEntities = async () => {
    try {
      setLoading(true);
      const offset = (currentPage - 1) * PAGE_SIZE;
      const response = await api.getEntities({
        limit: PAGE_SIZE,
        offset,
        search: debouncedSearch || undefined,
        entity_type: selectedType !== 'all' ? selectedType : undefined,
        has_biography: showOnlyWithBio  // Server-side biography filter
      });

      // Apply client-side filters
      let filteredEntities = response.entities;

      // Category filter (OR logic: entity matches ANY selected category)
      if (selectedCategories.length > 0) {
        filteredEntities = filteredEntities.filter(entity =>
          selectedCategories.some(selectedCat =>
            entity.bio?.relationship_categories?.some(cat => cat.type === selectedCat)
          )
        );
      }

      // Connection filter (minimum connections)
      filteredEntities = filteredEntities.filter(entity =>
        (entity.connection_count || 0) >= minConnections
      );

      // Calculate max connections from filtered data
      const maxConns = Math.max(...filteredEntities.map(e => e.connection_count || 0), 100);
      setMaxConnections(maxConns);

      setEntities(filteredEntities);
      setTotalEntities(filteredEntities.length);
    } catch (error) {
      console.error('Failed to load entities:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleBioFilterToggle = () => {
    const newValue = !showOnlyWithBio;
    setShowOnlyWithBio(newValue);

    // Update URL parameter
    const newParams = new URLSearchParams(searchParams);
    if (newValue) {
      newParams.set('bio', 'true');
    } else {
      newParams.delete('bio');
    }
    setSearchParams(newParams);
  };

  const handleBadgeClick = (categoryType: string) => {
    console.log('🟢 BADGE CLICKED - TOGGLING:', categoryType);

    setSelectedCategories(prev => {
      // Toggle: if already selected, remove it; otherwise add it
      const isSelected = prev.includes(categoryType);
      const updated = isSelected
        ? prev.filter(cat => cat !== categoryType)
        : [...prev, categoryType];

      // Update URL parameter
      const newParams = new URLSearchParams(searchParams);
      if (updated.length > 0) {
        newParams.set('categories', updated.join(','));
      } else {
        newParams.delete('categories');
      }
      setSearchParams(newParams);

      return updated;
    });

    // Scroll to top of page
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleRemoveCategory = (categoryType: string) => {
    setSelectedCategories(prev => {
      const updated = prev.filter(cat => cat !== categoryType);

      // Update URL parameter
      const newParams = new URLSearchParams(searchParams);
      if (updated.length > 0) {
        newParams.set('categories', updated.join(','));
      } else {
        newParams.delete('categories');
      }
      setSearchParams(newParams);

      return updated;
    });
  };

  const handleClearAllFilters = () => {
    setSelectedCategories([]);

    // Update URL parameter
    const newParams = new URLSearchParams(searchParams);
    newParams.delete('categories');
    setSearchParams(newParams);
  };

  const handleMinConnectionsChange = (value: number) => {
    setMinConnections(value);

    // Update URL parameter
    const newParams = new URLSearchParams(searchParams);
    if (value > 0) {
      newParams.set('minConnections', value.toString());
    } else {
      newParams.delete('minConnections');
    }
    setSearchParams(newParams);
  };

  // Helper to get category display data from ontology
  const getCategoryData = (categoryType: string) => {
    // Static mapping from entity_relationship_ontology.json
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
    // Use entity_type field from backend (populated by entity classification service)
    // Fall back to 'person' if field is missing (backward compatibility)
    if (entity.entity_type === 'organization') return 'organization';
    if (entity.entity_type === 'location') return 'location';
    return 'person';  // Default for legacy entities without entity_type
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

  if (loading) {
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
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold mb-2">Entities</h1>
        <p className="text-muted-foreground">
          Explore {totalEntities.toLocaleString()} people, organizations, and locations from the Epstein archive.
        </p>
      </div>

      {/* Search and Filters */}
      <div className="space-y-4">
        {/* Search Input */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            type="text"
            placeholder="Search all 1,637 entities by name..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
          {searchQuery !== debouncedSearch && (
            <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-solid border-current border-r-transparent" />
            </div>
          )}
        </div>

        {/* Type Filters */}
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setSelectedType('all')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              selectedType === 'all'
                ? 'bg-primary text-primary-foreground'
                : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
            }`}
          >
            All
          </button>
          <button
            onClick={() => setSelectedType('person')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2 ${
              selectedType === 'person'
                ? 'bg-primary text-primary-foreground'
                : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
            }`}
          >
            <Users className="h-4 w-4" />
            Person
          </button>
          <button
            onClick={() => setSelectedType('organization')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2 ${
              selectedType === 'organization'
                ? 'bg-primary text-primary-foreground'
                : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
            }`}
          >
            <Building2 className="h-4 w-4" />
            Organization
          </button>
          <button
            onClick={() => setSelectedType('location')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2 ${
              selectedType === 'location'
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
            onClick={handleBioFilterToggle}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2 ${
              showOnlyWithBio
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
            <label className="text-sm font-medium">
              Minimum Connections: <span className="text-primary font-bold">{minConnections}</span>
            </label>
            <span className="text-xs text-muted-foreground">
              (Showing {totalEntities.toLocaleString()} of entities)
            </span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-muted-foreground">0</span>
            <input
              type="range"
              min="0"
              max={maxConnections}
              value={minConnections}
              onChange={(e) => handleMinConnectionsChange(Number(e.target.value))}
              className="flex-1 h-2 bg-secondary rounded-lg appearance-none cursor-pointer accent-primary"
              title={`Filter entities with at least ${minConnections} connections`}
            />
            <span className="text-xs text-muted-foreground">{maxConnections}</span>
          </div>
          <div className="mt-2 text-xs text-muted-foreground">
            {minConnections === 0 && "Showing all entities (including those with no connections)"}
            {minConnections === 1 && "Hiding entities with 0 connections (default)"}
            {minConnections > 1 && `Showing only entities with ${minConnections}+ connections`}
          </div>
        </div>
      </div>

      {/* Active Category Filters Bar */}
      {selectedCategories.length > 0 && (
        <div className="bg-primary/5 border border-primary/20 rounded-lg p-4">
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-sm font-medium">Filters:</span>

              {/* Individual removable category badges */}
              {selectedCategories.map(catType => {
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
            Showing {((currentPage - 1) * PAGE_SIZE) + 1}-{Math.min(currentPage * PAGE_SIZE, totalEntities)} of {totalEntities.toLocaleString()} entities
            {(debouncedSearch || selectedType !== 'all' || showOnlyWithBio || selectedCategories.length > 0) && (
              <span className="ml-2 text-primary">
                (filtered)
              </span>
            )}
          </>
        )}
      </div>

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
                      {formatEntityName(entity.name)}
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
                      selectedCategories.includes(primaryCategory.type) ? 'ring-2 ring-offset-2' : ''
                    }`}
                    style={{
                      backgroundColor: primaryCategory.bg_color,
                      color: primaryCategory.color,
                      border: selectedCategories.includes(primaryCategory.type)
                        ? `2px solid ${primaryCategory.color}`
                        : `1px solid ${primaryCategory.color}40`
                    }}
                    title={selectedCategories.includes(primaryCategory.type)
                      ? `Remove ${primaryCategory.label} filter`
                      : `Filter by ${primaryCategory.label}`}
                  >
                    {primaryCategory.label}
                    {selectedCategories.includes(primaryCategory.type) && (
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
            {debouncedSearch || selectedType !== 'all' || showOnlyWithBio || selectedCategories.length > 0
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
                href="#"
                onClick={(e) => {
                  e.preventDefault();
                  if (currentPage > 1) {
                    setCurrentPage(currentPage - 1);
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                  }
                }}
                className={currentPage === 1 ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
              />
            </PaginationItem>

            {/* Page Numbers */}
            {(() => {
              const totalPages = Math.ceil(totalEntities / PAGE_SIZE);
              const pages: React.ReactNode[] = [];
              const maxVisible = 5;

              let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
              let endPage = Math.min(totalPages, startPage + maxVisible - 1);

              if (endPage - startPage < maxVisible - 1) {
                startPage = Math.max(1, endPage - maxVisible + 1);
              }

              // First page
              if (startPage > 1) {
                pages.push(
                  <PaginationItem key={1}>
                    <PaginationLink
                      href="#"
                      onClick={(e) => {
                        e.preventDefault();
                        setCurrentPage(1);
                        window.scrollTo({ top: 0, behavior: 'smooth' });
                      }}
                      isActive={currentPage === 1}
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
                      href="#"
                      onClick={(e) => {
                        e.preventDefault();
                        setCurrentPage(i);
                        window.scrollTo({ top: 0, behavior: 'smooth' });
                      }}
                      isActive={currentPage === i}
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
                      href="#"
                      onClick={(e) => {
                        e.preventDefault();
                        setCurrentPage(totalPages);
                        window.scrollTo({ top: 0, behavior: 'smooth' });
                      }}
                      isActive={currentPage === totalPages}
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
                href="#"
                onClick={(e) => {
                  e.preventDefault();
                  const totalPages = Math.ceil(totalEntities / PAGE_SIZE);
                  if (currentPage < totalPages) {
                    setCurrentPage(currentPage + 1);
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                  }
                }}
                className={currentPage >= Math.ceil(totalEntities / PAGE_SIZE) ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
              />
            </PaginationItem>
          </PaginationContent>
        </Pagination>
      )}
    </div>
  );
}
