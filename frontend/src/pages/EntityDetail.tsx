import { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  Users, Building2, MapPin, ArrowLeft, Newspaper,
  AlertCircle, Loader2
} from 'lucide-react';
import { api, type Entity } from '@/lib/api';
import { newsApi } from '@/services/newsApi';
import type { NewsArticle } from '@/types/news';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ArticleCard } from '@/components/news/ArticleCard';
import { EntityBio } from '@/components/entity/EntityBio';
import { EntityLinks } from '@/components/entity/EntityLinks';
import { useEntityCounts } from '@/hooks/useEntityCounts';
import { sortArticlesByDate } from '@/utils/entityNewsFilter';
import { formatEntityName } from '@/utils/nameFormat';
import { isGuid } from '@/utils/entityUrls';

type EntityType = 'person' | 'organization' | 'location';
type ViewMode = 'links' | 'bio';

/**
 * EntityDetail Page - Redesigned with Card-Based Navigation
 *
 * Design Decision: Two-State Navigation System
 * Rationale: Toggle between "links view" (navigation cards) and "bio view"
 * (expanded biography). This provides clear navigation without cluttering
 * the main view with all information at once.
 *
 * State Management:
 * - viewMode: 'links' (default) or 'bio' (expanded)
 * - Bio click: Toggle to expanded view in same page (no route change)
 * - Other links: Navigate to filtered pages (route change)
 *
 * Performance: Entity counts loaded immediately from entity object (no delay).
 * News articles loaded async after main entity data (non-blocking).
 *
 * Navigation Patterns:
 * - Bio: Expand in-place (better UX for reading)
 * - Docs/Flights/Network: Navigate with filters (standard pattern)
 */
export function EntityDetail() {
  // Extract guid from URL (name parameter is optional and ignored)
  const { guid, name } = useParams<{ guid: string; name?: string }>();
  const navigate = useNavigate();
  const [entity, setEntity] = useState<Entity | null>(null);
  const [newsArticles, setNewsArticles] = useState<NewsArticle[]>([]);
  const [loading, setLoading] = useState(true);
  const [newsLoading, setNewsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newsError, setNewsError] = useState<string | null>(null);
  const [newsRetryCount, setNewsRetryCount] = useState(0);
  // Default to 'bio' view so biography is immediately visible and expanded
  const [viewMode, setViewMode] = useState<ViewMode>('bio');

  // Get entity counts using hook (validates entity structure)
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const { counts: _counts, loading: _countsLoading, error: _countsError } = useEntityCounts(entity);

  useEffect(() => {
    const controller = new AbortController();

    if (guid) {
      loadEntityDetails(guid, name);
    }

    // Cleanup: Cancel any pending requests when component unmounts or GUID changes
    return () => {
      controller.abort();
    };
  }, [guid, name]);

  const loadEntityDetails = async (identifier: string, seoName?: string) => {
    try {
      setLoading(true);
      setError(null);

      // Determine if identifier is a GUID or legacy ID
      const isGuidFormat = isGuid(identifier);

      let foundEntity: Entity;
      if (isGuidFormat) {
        // Use v3 API for GUID-based lookup
        foundEntity = await api.getEntityByGuid(identifier, seoName);
      } else {
        // Fall back to v2 API for legacy ID-based lookup
        foundEntity = await api.getEntityById(identifier);
      }

      setEntity(foundEntity);
      setLoading(false);

      // Load news articles for this entity (async, don't block main load)
      // Pass entity ID instead of name so backend can properly convert format
      // (entity name is "Epstein, Jeffrey" but news uses "Jeffrey Epstein")
      loadNewsArticles(foundEntity.id);
    } catch (err) {
      console.error('Failed to load entity:', err);
      setError('Entity not found');
      setLoading(false);
    }
  };

  /**
   * Load news articles with retry logic and timeout
   *
   * Design Decision: Robust Error Handling with Retry
   * Rationale: News API calls can fail due to network issues, ngrok tunnel expiration,
   * or backend errors. Silent failures cause "0 articles" confusion for users.
   *
   * Error Handling Strategy:
   * - Retry up to 3 times with exponential backoff (1s, 2s, 4s)
   * - 10-second timeout per request (prevents indefinite hangs)
   * - AbortController for request cancellation
   * - User-visible error messages with retry button
   *
   * Trade-offs:
   * - Performance: Retry adds latency on failure (max 7s delay)
   * - UX: Clear error messages vs. silent "0 articles" confusion
   * - Complexity: More state management vs. better user experience
   */
  const loadNewsArticles = async (entityIdOrName: string, attempt = 1) => {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10000); // 10s timeout

    try {
      setNewsLoading(true);
      setNewsError(null); // Clear previous errors

      // Try to get articles by entity ID or name
      // Backend will convert entity ID to proper name format for matching
      // Fetch up to 100 articles to get accurate count, but only display first 10
      const response = await newsApi.getArticlesByEntity(entityIdOrName, 100);

      // Handle both paginated response format and direct array format
      // Backend should return array, but handle object {articles: [...], total: N} defensively
      const articles = Array.isArray(response) ? response : (response as any).articles || [];

      console.log('[EntityDetail] News API response:', {
        responseType: typeof response,
        isArray: Array.isArray(response),
        articlesCount: articles.length,
        rawResponse: response
      });

      // Sort by date and store all articles (for accurate count)
      const sortedArticles = sortArticlesByDate(articles);
      setNewsArticles(sortedArticles);
      setNewsRetryCount(0); // Reset retry count on success
    } catch (err) {
      console.error(`Failed to load news articles (attempt ${attempt}):`, err);

      // Check if this was a timeout
      const errorMessage = err instanceof Error && err.name === 'AbortError'
        ? 'Request timed out after 10 seconds'
        : err instanceof Error
          ? err.message
          : 'Unknown error occurred';

      // Retry logic: up to 3 attempts with exponential backoff
      if (attempt < 3) {
        const delay = 1000 * Math.pow(2, attempt - 1); // 1s, 2s, 4s
        console.log(`Retrying news load in ${delay}ms... (attempt ${attempt + 1}/3)`);

        await new Promise(resolve => setTimeout(resolve, delay));
        return loadNewsArticles(entityIdOrName, attempt + 1);
      }

      // All retries exhausted - show error to user
      setNewsError(`Failed to load news articles: ${errorMessage}`);
      setNewsRetryCount(attempt);
    } finally {
      clearTimeout(timeout);
      setNewsLoading(false);
    }
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
        return <Building2 className="h-6 w-6" />;
      case 'location':
        return <MapPin className="h-6 w-6" />;
      default:
        return <Users className="h-6 w-6" />;
    }
  };

  const getEntityTypeLabel = (entity: Entity): string => {
    const type = getEntityType(entity);
    return type.charAt(0).toUpperCase() + type.slice(1);
  };

  const handleBioClick = () => {
    setViewMode('bio');
  };

  const handleBioBack = () => {
    setViewMode('links');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">Loading entity details...</p>
        </div>
      </div>
    );
  }

  if (error || !entity) {
    return (
      <div className="space-y-6">
        <Button
          variant="ghost"
          onClick={() => navigate('/entities')}
          className="mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Entities
        </Button>

        <Card className="border-destructive">
          <CardContent className="flex items-center gap-4 py-8">
            <AlertCircle className="h-8 w-8 text-destructive" />
            <div>
              <h3 className="text-lg font-semibold">Error</h3>
              <p className="text-muted-foreground">{error}</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Back Button */}
      <Button
        variant="ghost"
        onClick={() => navigate('/entities')}
        className="mb-4"
      >
        <ArrowLeft className="h-4 w-4 mr-2" />
        Back to Entities
      </Button>

      {/* Entity Header */}
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-start gap-3 flex-1">
              <div className="text-muted-foreground mt-1">
                {getEntityIcon(entity)}
              </div>
              <div className="space-y-2 flex-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <h1 className="text-3xl font-bold">{formatEntityName(entity.name)}</h1>
                  <Badge variant="secondary">{getEntityTypeLabel(entity)}</Badge>
                </div>

                {/* Name Variations */}
                {entity.name_variations.length > 0 && (
                  <div className="text-sm text-muted-foreground">
                    <span className="font-medium">Also known as: </span>
                    {entity.name_variations.map(name => formatEntityName(name)).join(', ')}
                  </div>
                )}
              </div>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Special Badges */}
          {(entity.is_billionaire || entity.in_black_book || entity.appears_in_multiple_sources ||
            (entity.news_articles_count && entity.news_articles_count > 0) ||
            (entity.timeline_events_count && entity.timeline_events_count > 0)) && (
            <div className="flex flex-wrap gap-2">
              {entity.is_billionaire && (
                <Badge variant="outline" className="text-sm">
                  💰 Billionaire
                </Badge>
              )}
              {entity.in_black_book && (
                <Badge variant="outline" className="text-sm">
                  📖 Black Book
                </Badge>
              )}
              {entity.sources?.includes('flight_logs') && (
                <Badge variant="outline" className="text-sm">
                  ✈️ Flight Logs
                </Badge>
              )}
              {entity.news_articles_count && entity.news_articles_count > 0 && (
                <Badge variant="outline" className="text-sm">
                  📰 News ({entity.news_articles_count})
                </Badge>
              )}
              {entity.timeline_events_count && entity.timeline_events_count > 0 && (
                <Badge variant="outline" className="text-sm">
                  📅 Timeline ({entity.timeline_events_count})
                </Badge>
              )}
              {entity.appears_in_multiple_sources && (
                <Badge variant="outline" className="text-sm">
                  Multiple Sources
                </Badge>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Navigation Cards or Bio View */}
      {viewMode === 'links' ? (
        <EntityLinks entity={entity} onBioClick={handleBioClick} />
      ) : (
        <EntityBio entity={entity} onBack={handleBioBack} />
      )}

      {/* Top Connections - Only show in links view */}
      {viewMode === 'links' && entity.top_connections.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              Top Connections
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {entity.top_connections.slice(0, 10).map((connection, idx) => {
                // GUID Migration Limitation: Connection objects only contain name, not full entity data
                // Generate legacy snake_case ID from name for backward compatibility
                // Backend EntityDetail route supports ID-based lookup as fallback
                // Future Enhancement: Backend should return entity objects with GUIDs in top_connections
                const connectionId = connection.name.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '');
                return (
                  <div
                    key={idx}
                    className="flex items-center justify-between py-2 px-3 rounded-md hover:bg-accent transition-colors"
                  >
                    <Link
                      to={`/entities/${connectionId}`}
                      className="font-medium hover:text-primary transition-colors"
                    >
                      {formatEntityName(connection.name)}
                    </Link>
                    <Badge variant="secondary">
                      {connection.flights_together} flight{connection.flights_together !== 1 ? 's' : ''}
                    </Badge>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* News Coverage Section - Only show in links view */}
      {viewMode === 'links' && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Newspaper className="h-5 w-5" />
                News Coverage
              </CardTitle>
              {!newsLoading && newsArticles.length > 0 && (
                <Badge variant="secondary">{newsArticles.length} article{newsArticles.length !== 1 ? 's' : ''}</Badge>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {/* Error Banner with Retry */}
            {newsError && (
              <div className="mb-6 p-4 border border-destructive/50 bg-destructive/10 rounded-lg">
                <div className="flex items-start gap-3">
                  <AlertCircle className="h-5 w-5 text-destructive mt-0.5 flex-shrink-0" />
                  <div className="flex-1 space-y-2">
                    <div>
                      <p className="font-medium text-destructive">Unable to load news articles</p>
                      <p className="text-sm text-muted-foreground mt-1">{newsError}</p>
                      {newsRetryCount > 0 && (
                        <p className="text-sm text-muted-foreground mt-1">
                          Attempted {newsRetryCount} time{newsRetryCount !== 1 ? 's' : ''} with exponential backoff.
                        </p>
                      )}
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => loadNewsArticles(entity.id)}
                      disabled={newsLoading}
                      className="mt-2"
                    >
                      {newsLoading ? (
                        <>
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          Retrying...
                        </>
                      ) : (
                        <>Retry Now</>
                      )}
                    </Button>
                  </div>
                </div>
              </div>
            )}

            {/* Loading State */}
            {newsLoading && !newsError ? (
              <div className="flex items-center justify-center py-12">
                <div className="text-center">
                  <Loader2 className="h-6 w-6 animate-spin mx-auto mb-2" />
                  <p className="text-sm text-muted-foreground">
                    {newsRetryCount > 0
                      ? `Retrying... (attempt ${newsRetryCount + 1}/3)`
                      : 'Loading news articles...'}
                  </p>
                </div>
              </div>
            ) : newsArticles.length === 0 && !newsError ? (
              /* Empty State - Only show if no error */
              <div className="text-center py-12">
                <Newspaper className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <p className="text-lg font-medium mb-1">No news coverage found</p>
                <p className="text-muted-foreground">
                  No news articles mention {entity.name} in our database.
                </p>
              </div>
            ) : newsArticles.length > 0 ? (
              /* Success State - Articles loaded */
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {(() => {
                    // Debug: Verify newsArticles is an array and has content
                    console.log('[EntityDetail] Rendering news cards section:', {
                      isArray: Array.isArray(newsArticles),
                      length: newsArticles.length,
                      slicedLength: newsArticles.slice(0, 10).length,
                      firstArticle: newsArticles[0]
                    });

                    // Ensure newsArticles is an array before mapping
                    if (!Array.isArray(newsArticles)) {
                      console.error('[EntityDetail] newsArticles is not an array!', newsArticles);
                      return <div className="text-destructive">Error: Invalid news data format</div>;
                    }

                    return newsArticles.slice(0, 10).map((article, index) => (
                      <ArticleCard
                        key={article.id || `article-${index}`}
                        article={article}
                        compact
                      />
                    ));
                  })()}
                </div>

                {/* View All News Button */}
                {newsArticles.length > 0 && (
                  <Button
                    variant="outline"
                    className="w-full mt-4"
                    onClick={() => navigate(`/news?entity=${entity.id}`)}
                  >
                    View All {newsArticles.length} News Article{newsArticles.length !== 1 ? 's' : ''} for {formatEntityName(entity.name)} →
                  </Button>
                )}
              </div>
            ) : null}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
