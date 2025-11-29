import { useState, useEffect, useCallback, useRef } from 'react';
import {
  Search,
  Filter,
  X,
  Clock,
  TrendingUp,
  FileText,
  Users,
  Newspaper,
  Loader2,
  Sparkles,
  Calendar,
  Tag,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';

/**
 * Advanced Search Page
 *
 * Features:
 * - Multi-field search (entities, documents, flights, news)
 * - Fuzzy matching for typo tolerance
 * - Search-as-you-type with debouncing
 * - Search history and popular queries
 * - Faceted filtering sidebar
 * - Boolean operators (AND, OR, NOT)
 * - Date range filtering
 * - Search result highlighting
 * - Real-time autocomplete suggestions
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8081';

// Types
interface SearchResult {
  id: string;
  type: 'entity' | 'document' | 'news' | 'flight';
  title: string;
  description: string;
  similarity: number;
  metadata: Record<string, any>;
  highlights?: string[];
}

interface SearchResponse {
  query: string;
  total_results: number;
  search_time_ms: number;
  results: SearchResult[];
  facets: {
    types: Record<string, number>;
    sources: Record<string, number>;
    doc_types: Record<string, number>;
    entity_types: Record<string, number>;
  };
  suggestions: string[];
}

interface SearchSuggestion {
  text: string;
  type: string;
  score: number;
  metadata?: Record<string, any>;
}

interface SearchAnalytics {
  total_searches: number;
  top_queries: Array<{ query: string; count: number }>;
  recent_searches: Array<{ query: string; timestamp: string; fields: string }>;
  last_updated: string;
}

const SEARCH_HISTORY_KEY = 'advanced-search-history';
const MAX_HISTORY_ITEMS = 20;

export function AdvancedSearch() {
  // Search state
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchTime, setSearchTime] = useState(0);
  const [totalResults, setTotalResults] = useState(0);

  // Filter state
  const [filterOpen, setFilterOpen] = useState(true);
  const [selectedFields, setSelectedFields] = useState<string[]>(['all']);
  const [selectedTypes, setSelectedTypes] = useState<string[]>([]);
  const [selectedSources, setSelectedSources] = useState<string[]>([]);
  const [minSimilarity, setMinSimilarity] = useState(0.5);
  const [dateStart, setDateStart] = useState('');
  const [dateEnd, setDateEnd] = useState('');
  const [fuzzyEnabled, setFuzzyEnabled] = useState(true);

  // Facets state
  const [facets, setFacets] = useState<SearchResponse['facets']>({
    types: {},
    sources: {},
    doc_types: {},
    entity_types: {},
  });

  // Suggestions state
  const [suggestions, setSuggestions] = useState<SearchSuggestion[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [relatedQueries, setRelatedQueries] = useState<string[]>([]);

  // Analytics state
  const [analytics, setAnalytics] = useState<SearchAnalytics | null>(null);
  const [searchHistory, setSearchHistory] = useState<string[]>([]);

  // Refs for debouncing
  const searchTimeoutRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const suggestTimeoutRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  // Load search history from localStorage
  useEffect(() => {
    const stored = localStorage.getItem(SEARCH_HISTORY_KEY);
    if (stored) {
      try {
        setSearchHistory(JSON.parse(stored));
      } catch (error) {
        console.error('Failed to load search history:', error);
      }
    }
  }, []);

  // Load analytics on mount
  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/search/analytics`);
      if (response.ok) {
        const data = await response.json();
        setAnalytics(data);
      }
    } catch (error) {
      console.error('Failed to load analytics:', error);
    }
  };

  /**
   * Save search to history
   */
  const saveToHistory = (searchQuery: string) => {
    if (!searchQuery.trim()) return;

    const updated = [searchQuery, ...searchHistory.filter((q) => q !== searchQuery)].slice(
      0,
      MAX_HISTORY_ITEMS
    );
    setSearchHistory(updated);
    localStorage.setItem(SEARCH_HISTORY_KEY, JSON.stringify(updated));
  };

  /**
   * Debounced search handler
   */
  const handleSearchDebounced = useCallback(
    (searchQuery: string) => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }

      searchTimeoutRef.current = setTimeout(() => {
        if (searchQuery.trim().length >= 3) {
          performSearch(searchQuery);
        }
      }, 500); // 500ms debounce
    },
    [selectedFields, selectedTypes, selectedSources, minSimilarity, dateStart, dateEnd, fuzzyEnabled]
  );

  /**
   * Debounced suggestions handler
   */
  const handleSuggestionsDebounced = useCallback((searchQuery: string) => {
    if (suggestTimeoutRef.current) {
      clearTimeout(suggestTimeoutRef.current);
    }

    if (searchQuery.trim().length < 2) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }

    suggestTimeoutRef.current = setTimeout(() => {
      loadSuggestions(searchQuery);
    }, 300); // 300ms debounce for suggestions
  }, []);

  /**
   * Perform search API call
   */
  const performSearch = async (searchQuery: string) => {
    if (!searchQuery.trim()) {
      setResults([]);
      setTotalResults(0);
      return;
    }

    setLoading(true);

    try {
      const params = new URLSearchParams();
      params.set('query', searchQuery);
      params.set('limit', '50');
      params.set('fuzzy', fuzzyEnabled.toString());
      params.set('min_similarity', minSimilarity.toString());

      // Set fields to search
      if (selectedFields.length > 0 && !selectedFields.includes('all')) {
        params.set('fields', selectedFields.join(','));
      }

      // Set filters
      if (selectedTypes.length > 0) {
        params.set('doc_type', selectedTypes.join(','));
      }
      if (selectedSources.length > 0) {
        params.set('source', selectedSources.join(','));
      }
      if (dateStart) {
        params.set('date_start', dateStart);
      }
      if (dateEnd) {
        params.set('date_end', dateEnd);
      }

      const response = await fetch(`${API_BASE_URL}/api/search/unified?${params.toString()}`);

      if (!response.ok) {
        throw new Error(`Search failed: ${response.statusText}`);
      }

      const data: SearchResponse = await response.json();

      setResults(data.results);
      setTotalResults(data.total_results);
      setSearchTime(data.search_time_ms);
      setFacets(data.facets);
      setRelatedQueries(data.suggestions);

      // Save to history
      saveToHistory(searchQuery);
      loadAnalytics(); // Refresh analytics
    } catch (error) {
      console.error('Search failed:', error);
      setResults([]);
      setTotalResults(0);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Load autocomplete suggestions
   */
  const loadSuggestions = async (searchQuery: string) => {
    try {
      const params = new URLSearchParams();
      params.set('query', searchQuery);
      params.set('limit', '10');

      const response = await fetch(`${API_BASE_URL}/api/search/suggestions?${params.toString()}`);

      if (response.ok) {
        const data: SearchSuggestion[] = await response.json();
        setSuggestions(data);
        setShowSuggestions(data.length > 0);
      }
    } catch (error) {
      console.error('Failed to load suggestions:', error);
    }
  };

  /**
   * Handle query input change
   */
  const handleQueryChange = (value: string) => {
    setQuery(value);
    handleSearchDebounced(value);
    handleSuggestionsDebounced(value);
  };

  /**
   * Handle search submit
   */
  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setShowSuggestions(false);
    performSearch(query);
  };

  /**
   * Select a suggestion
   */
  const selectSuggestion = (suggestion: SearchSuggestion) => {
    setQuery(suggestion.text);
    setShowSuggestions(false);
    performSearch(suggestion.text);
  };

  /**
   * Clear search history
   */
  const clearHistory = () => {
    setSearchHistory([]);
    localStorage.removeItem(SEARCH_HISTORY_KEY);
  };

  /**
   * Toggle field selection
   */
  const toggleField = (field: string) => {
    if (field === 'all') {
      setSelectedFields(['all']);
    } else {
      const newFields = selectedFields.includes(field)
        ? selectedFields.filter((f) => f !== field && f !== 'all')
        : [...selectedFields.filter((f) => f !== 'all'), field];

      setSelectedFields(newFields.length === 0 ? ['all'] : newFields);
    }
  };

  /**
   * Get result type icon
   */
  const getResultIcon = (type: string) => {
    switch (type) {
      case 'entity':
        return <Users className="h-5 w-5 text-blue-500" />;
      case 'document':
        return <FileText className="h-5 w-5 text-green-500" />;
      case 'news':
        return <Newspaper className="h-5 w-5 text-purple-500" />;
      default:
        return <FileText className="h-5 w-5 text-gray-500" />;
    }
  };

  /**
   * Get similarity color
   */
  const getSimilarityColor = (similarity: number) => {
    if (similarity >= 0.8) return 'bg-green-100 text-green-800 border-green-300';
    if (similarity >= 0.6) return 'bg-yellow-100 text-yellow-800 border-yellow-300';
    return 'bg-blue-100 text-blue-800 border-blue-300';
  };

  /**
   * Highlight query terms in text
   */
  const highlightText = (text: string, highlights?: string[]) => {
    if (!highlights || highlights.length === 0) return text;

    let highlightedText = text;
    highlights.forEach((term) => {
      const regex = new RegExp(`(${term})`, 'gi');
      highlightedText = highlightedText.replace(regex, '<mark class="bg-yellow-200">$1</mark>');
    });

    return <span dangerouslySetInnerHTML={{ __html: highlightedText }} />;
  };

  return (
    <div className="flex h-[calc(100vh-4rem)]" data-testid="advanced-search-page">
      {/* Filter Sidebar */}
      <aside
        className={`${
          filterOpen ? 'w-[320px]' : 'w-0'
        } border-r bg-muted/30 transition-all duration-200 overflow-hidden flex flex-col`}
        data-testid="filter-sidebar"
      >
        <div className="p-4 border-b bg-background">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold flex items-center gap-2">
              <Filter className="h-4 w-4" />
              Filters
            </h2>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setFilterOpen(false)}
              aria-label="Close filters"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          {/* Search Fields */}
          <div className="space-y-2">
            <Label className="text-sm font-medium">Search In</Label>
            <div className="space-y-2">
              {['all', 'entities', 'documents', 'news'].map((field) => (
                <div key={field} className="flex items-center space-x-2">
                  <Checkbox
                    id={`field-${field}`}
                    checked={selectedFields.includes(field)}
                    onCheckedChange={() => toggleField(field)}
                  />
                  <Label htmlFor={`field-${field}`} className="text-sm capitalize cursor-pointer">
                    {field}
                  </Label>
                </div>
              ))}
            </div>
          </div>

          {/* Fuzzy Matching */}
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <Checkbox
                id="fuzzy"
                checked={fuzzyEnabled}
                onCheckedChange={(checked) => setFuzzyEnabled(checked as boolean)}
              />
              <Label htmlFor="fuzzy" className="text-sm cursor-pointer">
                Enable Fuzzy Matching
              </Label>
            </div>
            <p className="text-xs text-muted-foreground">
              Tolerates typos and spelling variations
            </p>
          </div>

          {/* Minimum Similarity */}
          <div className="space-y-2">
            <Label className="text-sm font-medium">
              Minimum Similarity: {(minSimilarity * 100).toFixed(0)}%
            </Label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={minSimilarity}
              onChange={(e) => setMinSimilarity(parseFloat(e.target.value))}
              className="w-full"
            />
          </div>

          {/* Date Range */}
          <div className="space-y-2">
            <Label className="text-sm font-medium flex items-center gap-2">
              <Calendar className="h-4 w-4" />
              Date Range
            </Label>
            <div className="space-y-2">
              <Input
                type="date"
                value={dateStart}
                onChange={(e) => setDateStart(e.target.value)}
                placeholder="Start date"
              />
              <Input
                type="date"
                value={dateEnd}
                onChange={(e) => setDateEnd(e.target.value)}
                placeholder="End date"
              />
            </div>
          </div>

          {/* Result Types Facet */}
          {Object.keys(facets.types).length > 0 && (
            <div className="space-y-2">
              <Label className="text-sm font-medium">Result Types</Label>
              <div className="space-y-1">
                {Object.entries(facets.types).map(([type, count]) => (
                  <div
                    key={type}
                    className="flex items-center justify-between text-sm p-2 rounded hover:bg-muted/50 cursor-pointer"
                  >
                    <span className="capitalize">{type}</span>
                    <Badge variant="secondary">{count}</Badge>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Sources Facet */}
          {Object.keys(facets.sources).length > 0 && (
            <div className="space-y-2">
              <Label className="text-sm font-medium">Sources</Label>
              <div className="space-y-1">
                {Object.entries(facets.sources)
                  .slice(0, 5)
                  .map(([source, count]) => (
                    <div
                      key={source}
                      className="flex items-center justify-between text-sm p-2 rounded hover:bg-muted/50 cursor-pointer"
                    >
                      <span className="truncate">{source}</span>
                      <Badge variant="secondary">{count}</Badge>
                    </div>
                  ))}
              </div>
            </div>
          )}

          {/* Reset Filters */}
          <Button
            variant="outline"
            size="sm"
            className="w-full"
            onClick={() => {
              setSelectedFields(['all']);
              setSelectedTypes([]);
              setSelectedSources([]);
              setMinSimilarity(0.5);
              setDateStart('');
              setDateEnd('');
              setFuzzyEnabled(true);
            }}
          >
            Reset Filters
          </Button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        <div className="flex-1 overflow-y-auto p-6">
          {/* Header */}
          <header className="mb-6">
            <h1 className="text-3xl font-bold mb-2 flex items-center gap-2">
              <Sparkles className="h-8 w-8 text-primary" />
              Advanced Search
            </h1>
            <p className="text-muted-foreground">
              Multi-field search with fuzzy matching, boolean operators, and advanced filtering
            </p>
          </header>

          {/* Search Bar */}
          <form onSubmit={handleSearchSubmit} className="mb-6">
            <div className="relative">
              <div className="relative flex gap-2">
                {!filterOpen && (
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setFilterOpen(true)}
                    aria-label="Open filters"
                  >
                    <Filter className="h-4 w-4" />
                  </Button>
                )}
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                  <Input
                    type="text"
                    placeholder="Search entities, documents, news... (supports AND, OR, NOT operators)"
                    value={query}
                    onChange={(e) => handleQueryChange(e.target.value)}
                    onFocus={() => query.length >= 2 && setShowSuggestions(suggestions.length > 0)}
                    onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
                    className="pl-10 pr-10 h-12 text-base"
                    data-testid="search-input"
                  />
                  {loading && (
                    <Loader2 className="absolute right-3 top-1/2 transform -translate-y-1/2 h-5 w-5 animate-spin text-muted-foreground" />
                  )}
                </div>
                <Button type="submit" size="lg" disabled={loading || !query.trim()}>
                  Search
                </Button>
              </div>

              {/* Autocomplete Suggestions */}
              {showSuggestions && suggestions.length > 0 && (
                <Card className="absolute z-10 w-full mt-2 shadow-lg">
                  <CardContent className="p-0">
                    <div className="divide-y">
                      {suggestions.map((suggestion, idx) => (
                        <button
                          key={idx}
                          type="button"
                          className="w-full text-left p-3 hover:bg-muted/50 transition-colors flex items-center gap-3"
                          onMouseDown={() => selectSuggestion(suggestion)}
                        >
                          <Search className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                          <div className="flex-1 min-w-0">
                            <div className="text-sm font-medium truncate">{suggestion.text}</div>
                            <div className="text-xs text-muted-foreground capitalize">
                              {suggestion.type.replace('_', ' ')}
                            </div>
                          </div>
                          <Badge variant="outline" className="text-xs">
                            {(suggestion.score * 100).toFixed(0)}%
                          </Badge>
                        </button>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </form>

          {/* Search Info */}
          {totalResults > 0 && (
            <div className="mb-4 flex items-center justify-between text-sm text-muted-foreground">
              <span>
                Found <strong className="text-foreground">{totalResults.toLocaleString()}</strong>{' '}
                results in <strong className="text-foreground">{searchTime.toFixed(0)}ms</strong>
              </span>
              {relatedQueries.length > 0 && (
                <div className="flex items-center gap-2">
                  <span className="text-xs">Related:</span>
                  {relatedQueries.slice(0, 3).map((related, idx) => (
                    <Badge
                      key={idx}
                      variant="outline"
                      className="cursor-pointer hover:bg-accent"
                      onClick={() => {
                        setQuery(related);
                        performSearch(related);
                      }}
                    >
                      {related}
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Search History & Analytics */}
          {!query && !loading && results.length === 0 && (
            <div className="space-y-6">
              {/* Recent Searches */}
              {searchHistory.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg flex items-center gap-2">
                      <Clock className="h-5 w-5" />
                      Recent Searches
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-2">
                      {searchHistory.slice(0, 10).map((historyQuery, idx) => (
                        <Badge
                          key={idx}
                          variant="secondary"
                          className="cursor-pointer hover:bg-secondary/80"
                          onClick={() => {
                            setQuery(historyQuery);
                            performSearch(historyQuery);
                          }}
                        >
                          {historyQuery}
                        </Badge>
                      ))}
                      <Button variant="ghost" size="sm" onClick={clearHistory}>
                        Clear
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Popular Queries */}
              {analytics && analytics.top_queries.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg flex items-center gap-2">
                      <TrendingUp className="h-5 w-5" />
                      Popular Searches
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {analytics.top_queries.slice(0, 10).map((item, idx) => (
                        <button
                          key={idx}
                          className="w-full text-left flex items-center justify-between p-2 rounded hover:bg-muted/50 transition-colors"
                          onClick={() => {
                            setQuery(item.query);
                            performSearch(item.query);
                          }}
                        >
                          <span className="text-sm">{item.query}</span>
                          <Badge variant="outline">{item.count} searches</Badge>
                        </button>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Search Tips */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Search Tips</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm text-muted-foreground">
                  <p>
                    <strong>Boolean Operators:</strong> Use AND, OR, NOT to refine searches
                  </p>
                  <p>
                    <strong>Example:</strong> "Ghislaine Maxwell AND Prince Andrew NOT denied"
                  </p>
                  <p>
                    <strong>Fuzzy Matching:</strong> Automatically tolerates typos and variations
                  </p>
                  <p>
                    <strong>Multi-field:</strong> Searches across entities, documents, and news
                  </p>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Search Results */}
          {results.length > 0 && (
            <div className="space-y-4">
              {results.map((result, idx) => (
                <Card key={idx} className="hover:shadow-md transition-shadow">
                  <CardHeader className="pb-3">
                    <div className="flex items-start gap-4">
                      <div className="mt-1">{getResultIcon(result.type)}</div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap mb-1">
                          <Badge
                            variant="outline"
                            className={`text-xs ${getSimilarityColor(result.similarity)}`}
                          >
                            {(result.similarity * 100).toFixed(1)}% match
                          </Badge>
                          <Badge variant="secondary" className="text-xs capitalize">
                            {result.type}
                          </Badge>
                        </div>
                        <CardTitle className="text-lg leading-tight">
                          {highlightText(result.title, result.highlights)}
                        </CardTitle>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <p className="text-sm text-muted-foreground line-clamp-3">
                      {highlightText(result.description, result.highlights)}
                    </p>

                    {/* Metadata */}
                    {Object.keys(result.metadata).length > 0 && (
                      <div className="flex flex-wrap gap-2 text-xs">
                        {result.metadata.source && (
                          <Badge variant="outline">
                            <Tag className="h-3 w-3 mr-1" />
                            {result.metadata.source}
                          </Badge>
                        )}
                        {result.metadata.categories &&
                          result.metadata.categories.slice(0, 3).map((cat: string, i: number) => (
                            <Badge key={i} variant="outline">
                              {cat}
                            </Badge>
                          ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {/* Empty State */}
          {!loading && query && results.length === 0 && (
            <div className="text-center py-12">
              <Search className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-lg font-medium mb-1">No results found</p>
              <p className="text-muted-foreground mb-4">
                Try adjusting your search query or filters
              </p>
              {relatedQueries.length > 0 && (
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">Try searching for:</p>
                  <div className="flex flex-wrap gap-2 justify-center">
                    {relatedQueries.map((related, idx) => (
                      <Badge
                        key={idx}
                        variant="secondary"
                        className="cursor-pointer hover:bg-secondary/80"
                        onClick={() => {
                          setQuery(related);
                          performSearch(related);
                        }}
                      >
                        {related}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
