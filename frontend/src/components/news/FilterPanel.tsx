import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Search, X, Filter } from 'lucide-react';
import type { NewsSearchParams } from '@/types/news';
import { isGuid, hydrateEntityName } from '@/utils/guidUtils';
import { getCachedEntityName, cacheEntityName } from '@/utils/entityNameCache';

interface FilterPanelProps {
  onFilterChange: (params: NewsSearchParams) => void;
  availablePublications?: string[];
  availableTags?: string[];
  initialFilters?: NewsSearchParams;
  className?: string;
}

export function FilterPanel({
  onFilterChange,
  availablePublications = [],
  availableTags = [],
  initialFilters,
  className = '',
}: FilterPanelProps) {
  const [searchQuery, setSearchQuery] = useState(initialFilters?.query || '');
  const [selectedPublications, setSelectedPublications] = useState<string[]>(
    initialFilters?.publication ? [initialFilters.publication] : []
  );
  const [selectedTags, setSelectedTags] = useState<string[]>(initialFilters?.tags || []);
  const [startDate, setStartDate] = useState(initialFilters?.start_date || '');
  const [endDate, setEndDate] = useState(initialFilters?.end_date || '');
  const [minCredibility, setMinCredibility] = useState(initialFilters?.min_credibility || 0.0);
  const [entityFilter, setEntityFilter] = useState(initialFilters?.entity || '');
  const [entityDisplayValue, setEntityDisplayValue] = useState(''); // Display value for UI (hydrated name)

  // Hydrate GUID to entity name on mount or when entityFilter changes
  useEffect(() => {
    if (entityFilter) {
      // Check cache first for instant display
      const cachedName = getCachedEntityName(entityFilter);
      if (cachedName) {
        setEntityDisplayValue(cachedName);
        return;
      }

      // If it's a GUID, hydrate it from API
      if (isGuid(entityFilter)) {
        hydrateEntityName(entityFilter).then(name => {
          setEntityDisplayValue(name);
          cacheEntityName(entityFilter, name);
        });
      } else {
        // Not a GUID, use as-is
        setEntityDisplayValue(entityFilter);
      }
    } else {
      setEntityDisplayValue('');
    }
  }, [entityFilter]);

  // Debounce search query
  useEffect(() => {
    const timer = setTimeout(() => {
      applyFilters();
    }, 300);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Apply filters whenever they change
  useEffect(() => {
    applyFilters();
  }, [selectedPublications, selectedTags, startDate, endDate, minCredibility, entityFilter]);

  const applyFilters = useCallback(() => {
    const params: NewsSearchParams = {
      query: searchQuery,
      limit: 20,
    };

    if (selectedPublications.length > 0) {
      params.publication = selectedPublications[0]; // API only supports one publication
    }

    if (selectedTags.length > 0) {
      params.tags = selectedTags;
    }

    if (startDate) {
      params.start_date = startDate;
    }

    if (endDate) {
      params.end_date = endDate;
    }

    if (minCredibility > 0) {
      params.min_credibility = minCredibility;
    }

    if (entityFilter) {
      params.entity = entityFilter;
    }

    onFilterChange(params);
  }, [searchQuery, selectedPublications, selectedTags, startDate, endDate, minCredibility, entityFilter, onFilterChange]);

  const clearAllFilters = () => {
    setSearchQuery('');
    setSelectedPublications([]);
    setSelectedTags([]);
    setStartDate('');
    setEndDate('');
    setMinCredibility(0.0);
    setEntityFilter('');
    setEntityDisplayValue('');
  };

  const togglePublication = (pub: string) => {
    setSelectedPublications(prev =>
      prev.includes(pub) ? prev.filter(p => p !== pub) : [pub] // Only allow one
    );
  };

  const toggleTag = (tag: string) => {
    setSelectedTags(prev =>
      prev.includes(tag) ? prev.filter(t => t !== tag) : [...prev, tag]
    );
  };

  const hasActiveFilters =
    searchQuery.length > 0 ||
    selectedPublications.length > 0 ||
    selectedTags.length > 0 ||
    startDate.length > 0 ||
    endDate.length > 0 ||
    minCredibility > 0 ||
    entityFilter.length > 0;

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Filter className="h-5 w-5" />
          Filters
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Search Input */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Search</label>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              type="text"
              placeholder="Search articles..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>

        {/* Entity Filter */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Entity</label>
          <Input
            type="text"
            placeholder="Filter by entity name..."
            value={entityDisplayValue}
            onChange={(e) => {
              const newValue = e.target.value;
              setEntityDisplayValue(newValue);
              setEntityFilter(newValue);
            }}
          />
        </div>

        {/* Credibility Slider */}
        <div className="space-y-2">
          <label className="text-sm font-medium">
            Min Credibility: {(minCredibility * 100).toFixed(0)}%
          </label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={minCredibility}
            onChange={(e) => setMinCredibility(parseFloat(e.target.value))}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>0%</span>
            <span>50%</span>
            <span>100%</span>
          </div>
        </div>

        {/* Date Range */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Date Range</label>
          <div className="space-y-2">
            <Input
              type="date"
              placeholder="Start date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
            />
            <Input
              type="date"
              placeholder="End date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
            />
          </div>
        </div>

        {/* Publications */}
        {availablePublications.length > 0 && (
          <div className="space-y-2">
            <label className="text-sm font-medium">
              Publication ({selectedPublications.length} selected)
            </label>
            <div className="max-h-48 overflow-y-auto space-y-1 border rounded-md p-2">
              {availablePublications.map((pub) => (
                <div
                  key={pub}
                  onClick={() => togglePublication(pub)}
                  className={`cursor-pointer p-2 rounded text-sm hover:bg-accent transition-colors ${
                    selectedPublications.includes(pub) ? 'bg-accent' : ''
                  }`}
                >
                  {pub}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tags */}
        {availableTags.length > 0 && (
          <div className="space-y-2">
            <label className="text-sm font-medium">
              Tags ({selectedTags.length} selected)
            </label>
            <div className="flex flex-wrap gap-2">
              {availableTags.slice(0, 10).map((tag) => (
                <Badge
                  key={tag}
                  variant={selectedTags.includes(tag) ? 'default' : 'outline'}
                  className="cursor-pointer"
                  onClick={() => toggleTag(tag)}
                >
                  {tag}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Active Filters */}
        {hasActiveFilters && (
          <div className="space-y-2 pt-4 border-t">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium">Active Filters</label>
              <Button
                variant="ghost"
                size="sm"
                onClick={clearAllFilters}
                className="h-auto py-1"
              >
                Clear All
              </Button>
            </div>
            <div className="flex flex-wrap gap-2">
              {searchQuery && (
                <Badge variant="secondary" className="gap-1">
                  Search: {searchQuery}
                  <X
                    className="h-3 w-3 cursor-pointer"
                    onClick={() => setSearchQuery('')}
                  />
                </Badge>
              )}
              {selectedPublications.map((pub) => (
                <Badge key={pub} variant="secondary" className="gap-1">
                  {pub}
                  <X
                    className="h-3 w-3 cursor-pointer"
                    onClick={() => togglePublication(pub)}
                  />
                </Badge>
              ))}
              {selectedTags.map((tag) => (
                <Badge key={tag} variant="secondary" className="gap-1">
                  {tag}
                  <X
                    className="h-3 w-3 cursor-pointer"
                    onClick={() => toggleTag(tag)}
                  />
                </Badge>
              ))}
              {entityFilter && (
                <Badge variant="secondary" className="gap-1">
                  Entity: {entityDisplayValue}
                  <X
                    className="h-3 w-3 cursor-pointer"
                    onClick={() => {
                      setEntityFilter('');
                      setEntityDisplayValue('');
                    }}
                  />
                </Badge>
              )}
              {minCredibility > 0 && (
                <Badge variant="secondary" className="gap-1">
                  Min {(minCredibility * 100).toFixed(0)}%
                  <X
                    className="h-3 w-3 cursor-pointer"
                    onClick={() => setMinCredibility(0)}
                  />
                </Badge>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
