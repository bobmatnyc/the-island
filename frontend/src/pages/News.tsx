import { useEffect, useState, useCallback } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import { AlertCircle, Newspaper, Calendar } from 'lucide-react';
import { NewsFilters } from '@/components/news/NewsFilters';
import { NewsTimeline } from '@/components/news/NewsTimeline';
import { NewsStats } from '@/components/news/NewsStats';
import { newsApi } from '@/services/newsApi';
import type { NewsArticle, NewsSearchParams, NewsStats as NewsStatsType } from '@/types/news';

/**
 * News Page Component
 *
 * Design: Timeline-based news browsing
 * - Chronological vertical timeline view
 * - Advanced filtering and search
 * - Statistics dashboard toggle
 * - URL state persistence for sharing
 *
 * Performance:
 * - Parallel data loading (articles, publications, stats)
 * - Debounced search input
 * - Memoized timeline grouping
 * - Efficient re-renders with React.memo
 */
export function News() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [stats, setStats] = useState<NewsStatsType | null>(null);
  const [publications, setPublications] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showStats, setShowStats] = useState(false);

  // Get initial filters from URL params
  const getInitialFilters = (): NewsSearchParams => {
    return {
      query: searchParams.get('query') || '',
      entity: searchParams.get('entity') || undefined,
      publication: searchParams.get('publication') || undefined,
      min_credibility: searchParams.get('min_credibility')
        ? parseFloat(searchParams.get('min_credibility')!)
        : undefined,
      start_date: searchParams.get('start_date') || undefined,
      end_date: searchParams.get('end_date') || undefined,
      limit: 100, // Timeline needs more articles
    };
  };

  const [filters, setFilters] = useState<NewsSearchParams>(getInitialFilters());

  // Load initial data
  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        setError(null);

        // Load articles, publications, and stats in parallel
        const [articlesData, publicationsData, statsData] = await Promise.all([
          newsApi.searchNews(filters),
          newsApi.getPublications(),
          newsApi.getStats(),
        ]);

        setArticles(articlesData);
        setPublications(publicationsData);
        setStats(statsData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load news articles');
        console.error('Error loading news data:', err);
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  // Handle filter changes
  const handleFilterChange = useCallback(async (newFilters: NewsSearchParams) => {
    try {
      setLoading(true);
      setError(null);
      setFilters(newFilters);

      // Update URL params for sharing
      const params = new URLSearchParams();
      if (newFilters.query) params.set('query', newFilters.query);
      if (newFilters.entity) params.set('entity', newFilters.entity);
      if (newFilters.publication) params.set('publication', newFilters.publication);
      if (newFilters.min_credibility) params.set('min_credibility', newFilters.min_credibility.toString());
      if (newFilters.start_date) params.set('start_date', newFilters.start_date);
      if (newFilters.end_date) params.set('end_date', newFilters.end_date);
      setSearchParams(params);

      // Fetch new articles
      const articlesData = await newsApi.searchNews(newFilters);
      setArticles(articlesData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to search articles');
      console.error('Error searching articles:', err);
    } finally {
      setLoading(false);
    }
  }, [setSearchParams]);

  // Handle entity click
  const handleEntityClick = useCallback((entity: string) => {
    handleFilterChange({ ...filters, entity });
  }, [filters, handleFilterChange]);

  // Error state
  if (error) {
    return (
      <div className="container mx-auto p-6">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Page Header */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold tracking-tight flex items-center gap-3">
              <Newspaper className="h-10 w-10" />
              News Coverage
            </h1>
            <p className="text-xl text-muted-foreground mt-2">
              {stats
                ? `${stats.total_articles.toLocaleString()} articles from ${stats.publications.length} publications`
                : 'Loading news articles...'}
            </p>
          </div>

          {/* Stats Toggle */}
          {stats && (
            <Button
              variant="outline"
              onClick={() => setShowStats(!showStats)}
            >
              {showStats ? 'Hide Statistics' : 'Show Statistics'}
            </Button>
          )}
        </div>

        {/* Statistics Dashboard */}
        {showStats && stats && <NewsStats stats={stats} />}
      </div>

      {/* Suggest Timeline View */}
      <Alert className="border-blue-200 bg-blue-50">
        <Calendar className="h-4 w-4 text-blue-600" />
        <AlertTitle className="text-blue-900">Unified Timeline View Available</AlertTitle>
        <AlertDescription className="text-blue-800">
          For a comprehensive chronological view combining news articles with timeline events,{' '}
          <Link to="/timeline" className="font-medium underline hover:text-blue-600">
            visit the Timeline page
          </Link>.
        </AlertDescription>
      </Alert>

      {/* Timeline Content */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Filters (1/4 width) */}
        <NewsFilters
          className="lg:col-span-1"
          onFilterChange={handleFilterChange}
          availablePublications={publications}
        />

        {/* Timeline (3/4 width) */}
        <div className="lg:col-span-3">
          <NewsTimeline
            articles={articles}
            loading={loading}
            onEntityClick={handleEntityClick}
          />
        </div>
      </div>
    </div>
  );
}
