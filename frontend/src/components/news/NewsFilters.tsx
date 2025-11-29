import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Search, X, SlidersHorizontal, Calendar } from 'lucide-react';
import type { NewsSearchParams } from '@/types/news';

interface NewsFiltersProps {
  onFilterChange: (params: NewsSearchParams) => void;
  availablePublications?: string[];
  className?: string;
}

/**
 * News Filters Component
 *
 * Design: Timeline-specific filter controls
 * - Search by title/content
 * - Filter by publication
 * - Filter by date range
 * - Filter by credibility score
 * - Filter by entity mentions
 * - Debounced search input (300ms)
 * - Active filter badges with clear functionality
 */
export function NewsFilters({
  onFilterChange,
  availablePublications = [],
  className = '',
}: NewsFiltersProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedPublication, setSelectedPublication] = useState<string>('all');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [minCredibility, setMinCredibility] = useState(0);
  const [entityFilter, setEntityFilter] = useState('');

  // Debounced search - applies filters after 300ms of no typing
  useEffect(() => {
    const timer = setTimeout(() => {
      applyFilters();
    }, 300);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Apply filters immediately when non-search fields change
  useEffect(() => {
    applyFilters();
  }, [selectedPublication, startDate, endDate, minCredibility, entityFilter]);

  // Build and apply filter params
  const applyFilters = useCallback(() => {
    const params: NewsSearchParams = {
      limit: 100, // Fetch more for timeline view
    };

    if (searchQuery.trim()) {
      params.query = searchQuery.trim();
    }

    if (selectedPublication && selectedPublication !== 'all') {
      params.publication = selectedPublication;
    }

    if (startDate) {
      params.start_date = startDate;
    }

    if (endDate) {
      params.end_date = endDate;
    }

    if (minCredibility > 0) {
      params.min_credibility = minCredibility / 100; // Convert percentage to decimal
    }

    if (entityFilter.trim()) {
      params.entity = entityFilter.trim();
    }

    onFilterChange(params);
  }, [searchQuery, selectedPublication, startDate, endDate, minCredibility, entityFilter, onFilterChange]);

  // Clear all filters
  const clearAllFilters = () => {
    setSearchQuery('');
    setSelectedPublication('all');
    setStartDate('');
    setEndDate('');
    setMinCredibility(0);
    setEntityFilter('');
  };

  // Check if any filters are active
  const hasActiveFilters =
    searchQuery.length > 0 ||
    (selectedPublication.length > 0 && selectedPublication !== 'all') ||
    startDate.length > 0 ||
    endDate.length > 0 ||
    minCredibility > 0 ||
    entityFilter.length > 0;

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <SlidersHorizontal className="h-5 w-5" />
          Filters
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-5">
        {/* Search Input */}
        <div className="space-y-2">
          <Label htmlFor="search" className="text-sm font-medium">
            Search Articles
          </Label>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              id="search"
              type="text"
              placeholder="Search by title or content..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
            {searchQuery && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSearchQuery('')}
                className="absolute right-1 top-1/2 -translate-y-1/2 h-7 w-7 p-0"
              >
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>

        {/* Entity Filter */}
        <div className="space-y-2">
          <Label htmlFor="entity" className="text-sm font-medium">
            Entity Mentioned
          </Label>
          <Input
            id="entity"
            type="text"
            placeholder="Filter by entity name..."
            value={entityFilter}
            onChange={(e) => setEntityFilter(e.target.value)}
          />
        </div>

        {/* Publication Select */}
        {availablePublications.length > 0 && (
          <div className="space-y-2">
            <Label htmlFor="publication" className="text-sm font-medium">
              Publication
            </Label>
            <Select value={selectedPublication} onValueChange={setSelectedPublication}>
              <SelectTrigger id="publication">
                <SelectValue placeholder="All publications" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All publications</SelectItem>
                {availablePublications.map((pub) => (
                  <SelectItem key={pub} value={pub}>
                    {pub}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}

        {/* Date Range */}
        <div className="space-y-2">
          <Label className="text-sm font-medium flex items-center gap-2">
            <Calendar className="h-4 w-4" />
            Date Range
          </Label>
          <div className="space-y-2">
            <Input
              type="date"
              placeholder="Start date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="text-sm"
            />
            <Input
              type="date"
              placeholder="End date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="text-sm"
            />
          </div>
        </div>

        {/* Credibility Filter */}
        <div className="space-y-2">
          <Label htmlFor="credibility" className="text-sm font-medium">
            Minimum Credibility: {minCredibility}%
          </Label>
          <input
            id="credibility"
            type="range"
            min="0"
            max="100"
            step="5"
            value={minCredibility}
            onChange={(e) => setMinCredibility(parseInt(e.target.value))}
            className="w-full accent-primary"
          />
          <div className="flex justify-between text-xs text-muted-foreground px-1">
            <span>0%</span>
            <span>50%</span>
            <span>100%</span>
          </div>
        </div>

        {/* Active Filters */}
        {hasActiveFilters && (
          <div className="space-y-3 pt-4 border-t">
            <div className="flex items-center justify-between">
              <Label className="text-sm font-medium">Active Filters</Label>
              <Button
                variant="ghost"
                size="sm"
                onClick={clearAllFilters}
                className="h-auto py-1 px-2 text-xs"
              >
                Clear All
              </Button>
            </div>

            <div className="flex flex-wrap gap-2">
              {searchQuery && (
                <Badge variant="secondary" className="gap-1.5 pr-1">
                  <span className="text-xs">Search: {searchQuery.substring(0, 20)}{searchQuery.length > 20 ? '...' : ''}</span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setSearchQuery('')}
                    className="h-4 w-4 p-0 hover:bg-transparent"
                  >
                    <X className="h-3 w-3" />
                  </Button>
                </Badge>
              )}

              {selectedPublication && selectedPublication !== 'all' && (
                <Badge variant="secondary" className="gap-1.5 pr-1">
                  <span className="text-xs">{selectedPublication}</span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setSelectedPublication('all')}
                    className="h-4 w-4 p-0 hover:bg-transparent"
                  >
                    <X className="h-3 w-3" />
                  </Button>
                </Badge>
              )}

              {entityFilter && (
                <Badge variant="secondary" className="gap-1.5 pr-1">
                  <span className="text-xs">Entity: {entityFilter}</span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setEntityFilter('')}
                    className="h-4 w-4 p-0 hover:bg-transparent"
                  >
                    <X className="h-3 w-3" />
                  </Button>
                </Badge>
              )}

              {(startDate || endDate) && (
                <Badge variant="secondary" className="gap-1.5 pr-1">
                  <span className="text-xs">
                    {startDate && endDate
                      ? `${startDate} to ${endDate}`
                      : startDate
                      ? `From ${startDate}`
                      : `Until ${endDate}`}
                  </span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setStartDate('');
                      setEndDate('');
                    }}
                    className="h-4 w-4 p-0 hover:bg-transparent"
                  >
                    <X className="h-3 w-3" />
                  </Button>
                </Badge>
              )}

              {minCredibility > 0 && (
                <Badge variant="secondary" className="gap-1.5 pr-1">
                  <span className="text-xs">Min {minCredibility}%</span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setMinCredibility(0)}
                    className="h-4 w-4 p-0 hover:bg-transparent"
                  >
                    <X className="h-3 w-3" />
                  </Button>
                </Badge>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
