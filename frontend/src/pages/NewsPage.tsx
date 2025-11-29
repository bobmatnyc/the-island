import { useEffect, useState, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import { ChevronLeft, ChevronRight, AlertCircle, Newspaper } from 'lucide-react';
import { ArticleCard } from '@/components/news/ArticleCard';
import { FilterPanel } from '@/components/news/FilterPanel';
import { NewsStats } from '@/components/news/NewsStats';
import { newsApi } from '@/services/newsApi';
import type { NewsArticle, NewsSearchParams, NewsStats as NewsStatsType } from '@/types/news';

export function NewsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [stats, setStats] = useState<NewsStatsType | null>(null);
  const [publications, setPublications] = useState<string[]>([]);
  const [tags, setTags] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [showStats, setShowStats] = useState(false);
  const articlesPerPage = 20;

  // Get initial filter from URL params
  const getInitialFilters = (): NewsSearchParams => {
    return {
      query: searchParams.get('query') || '',
      entity: searchParams.get('entity') || undefined,
      publication: searchParams.get('publication') || undefined,
      min_credibility: searchParams.get('min_credibility')
        ? parseFloat(searchParams.get('min_credibility')!)
        : undefined,
      limit: articlesPerPage,
    };
  };

  const [filters, setFilters] = useState<NewsSearchParams>(getInitialFilters());

  // Load initial data
  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        setError(null);

        // Load articles, publications, tags, and stats in parallel
        const [articlesData, publicationsData, tagsData, statsData] = await Promise.all([
          newsApi.searchNews(filters),
          newsApi.getPublications(),
          newsApi.getTags(),
          newsApi.getStats(),
        ]);

        setArticles(articlesData);
        setPublications(publicationsData);
        setTags(tagsData);
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
      setCurrentPage(1);

      // Update URL params
      const params = new URLSearchParams();
      if (newFilters.query) params.set('query', newFilters.query);
      if (newFilters.entity) params.set('entity', newFilters.entity);
      if (newFilters.publication) params.set('publication', newFilters.publication);
      if (newFilters.min_credibility) params.set('min_credibility', newFilters.min_credibility.toString());
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
  const handleEntityClick = (entity: string) => {
    handleFilterChange({ ...filters, entity });
  };

  // Pagination
  const totalPages = Math.ceil(articles.length / articlesPerPage);
  const startIndex = (currentPage - 1) * articlesPerPage;
  const endIndex = startIndex + articlesPerPage;
  const currentArticles = articles.slice(startIndex, endIndex);

  const goToPage = (page: number) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

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
        {showStats && stats && (
          <NewsStats stats={stats} />
        )}
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Filter Panel (1/4 width on large screens) */}
        <FilterPanel
          className="lg:col-span-1"
          onFilterChange={handleFilterChange}
          availablePublications={publications}
          availableTags={tags}
          initialFilters={getInitialFilters()}
        />

        {/* Article List (3/4 width on large screens) */}
        <div className="lg:col-span-3 space-y-6">
          {/* Results Header */}
          <Card>
            <CardHeader>
              <CardTitle>
                {loading ? 'Loading...' : `${articles.length} Articles Found`}
              </CardTitle>
              <CardDescription>
                {!loading && articles.length > 0 && (
                  <>
                    Showing {startIndex + 1}-{Math.min(endIndex, articles.length)} of{' '}
                    {articles.length} results
                  </>
                )}
              </CardDescription>
            </CardHeader>
          </Card>

          {/* Loading State */}
          {loading && (
            <div className="space-y-4">
              {[...Array(5)].map((_, i) => (
                <Card key={i}>
                  <CardHeader className="space-y-3">
                    <Skeleton className="h-6 w-3/4" />
                    <Skeleton className="h-4 w-full" />
                  </CardHeader>
                  <CardContent>
                    <Skeleton className="h-20 w-full" />
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {/* Article Grid */}
          {!loading && articles.length > 0 && (
            <>
              <div className="space-y-4">
                {currentArticles.map((article) => (
                  <ArticleCard
                    key={article.id}
                    article={article}
                    onEntityClick={handleEntityClick}
                  />
                ))}
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <Card>
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <Button
                        variant="outline"
                        onClick={() => goToPage(currentPage - 1)}
                        disabled={currentPage === 1}
                      >
                        <ChevronLeft className="h-4 w-4 mr-2" />
                        Previous
                      </Button>

                      <div className="flex items-center gap-2">
                        <span className="text-sm text-muted-foreground">
                          Page {currentPage} of {totalPages}
                        </span>
                      </div>

                      <Button
                        variant="outline"
                        onClick={() => goToPage(currentPage + 1)}
                        disabled={currentPage === totalPages}
                      >
                        Next
                        <ChevronRight className="h-4 w-4 ml-2" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )}
            </>
          )}

          {/* No Results */}
          {!loading && articles.length === 0 && (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center py-12">
                  <Newspaper className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                  <h3 className="text-lg font-semibold mb-2">No articles found</h3>
                  <p className="text-muted-foreground">
                    Try adjusting your filters or search query
                  </p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
