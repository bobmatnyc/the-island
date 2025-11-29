import { useEffect, useState, useMemo } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { Calendar, Clock, FileText, Users, ExternalLink, Filter, Newspaper } from 'lucide-react';
import { api, type TimelineEvent } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { useTimelineNews, getArticleCountForDate } from '@/hooks/useTimelineNews';
import { formatEntityName } from '@/utils/nameFormat';

type CategoryFilter = 'all' | 'biographical' | 'case' | 'documents';
type SourceFilter = 'all' | 'timeline' | 'news';

const categoryColors: Record<string, string> = {
  biographical: 'bg-blue-100 text-blue-800 border-blue-300',
  case: 'bg-red-100 text-red-800 border-red-300',
  documents: 'bg-green-100 text-green-800 border-green-300',
  default: 'bg-gray-100 text-gray-800 border-gray-300',
};

/**
 * Convert entity name to URL-safe ID format
 * Converts name to lowercase and replaces spaces/special chars with underscores
 * Example: "Clinton, Bill" -> "clinton_bill"
 */
const entityNameToId = (name: string): string => {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, ''); // Remove leading/trailing underscores
};

export function Timeline() {
  // URL parameter detection for news coverage
  const [searchParams] = useSearchParams();
  const forceShowNews = searchParams.get('news') === 'true' || searchParams.get('showNews') === 'true';

  console.log('[Timeline URL Params]', {
    newsParam: searchParams.get('news'),
    showNewsParam: searchParams.get('showNews'),
    forceShowNews,
    timestamp: new Date().toISOString(),
  });

  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [filteredEvents, setFilteredEvents] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<CategoryFilter>('all');
  const [showNews, setShowNews] = useState(forceShowNews);
  const [sourceFilter, setSourceFilter] = useState<SourceFilter>('all');

  // Calculate date range from events for news fetching
  const dateRange = useMemo(() => {
    if (events.length === 0) {
      return { start: '', end: '' };
    }
    const dates = events.map(e => e.date).filter(Boolean).sort();
    return {
      start: dates[0] || '',
      end: dates[dates.length - 1] || '',
    };
  }, [events]);

  // Fetch news articles for timeline
  const { articlesByDate, loading: newsLoading, totalArticles } = useTimelineNews(
    dateRange,
    showNews
  );

  useEffect(() => {
    loadTimeline();
  }, []);

  // Handle URL parameter changes for news coverage
  useEffect(() => {
    if (forceShowNews && !showNews) {
      console.log('[Timeline] URL param forcing news coverage ON', {
        forceShowNews,
        currentShowNews: showNews,
        timestamp: new Date().toISOString(),
      });
      setShowNews(true);
    }
  }, [forceShowNews]);

  useEffect(() => {
    // Debug logging for filter state
    console.log('[Timeline Filter Debug]', {
      sourceFilter,
      showNews,
      newsLoading,
      articlesCount: Object.keys(articlesByDate).length,
      totalArticles,
      eventsCount: events.length,
      filteredCount: filteredEvents.length,
      sampleEventDate: events[0]?.date,
      sampleArticleDates: Object.keys(articlesByDate).slice(0, 5),
      forceShowNews,
    });
    filterEvents();
  }, [events, searchQuery, selectedCategory, sourceFilter, showNews, articlesByDate]);

  const loadTimeline = async () => {
    try {
      setLoading(true);
      const response = await api.getTimeline();
      // Reverse to show most recent first
      setEvents([...response.events].reverse());
    } catch (error) {
      console.error('Failed to load timeline:', error);
    } finally {
      setLoading(false);
    }
  };

  const filterEvents = () => {
    // Start with a copy of all events to avoid mutation issues
    let filtered = [...events];

    // Apply source filter
    if (sourceFilter === 'news') {
      // When news filter is active, automatically enable news toggle
      if (!showNews) {
        setShowNews(true);
        // Don't return - let the effect trigger again on next render
        // Keep current filtered events visible during transition
        return;
      }

      // Wait for news articles to finish loading before filtering
      if (newsLoading) {
        // Keep showing current events with loading indicator
        // Don't update filteredEvents to avoid showing "0 events"
        return;
      }

      if (Object.keys(articlesByDate).length === 0) {
        // No news articles found - show empty state
        setFilteredEvents([]);
        return;
      }

      // Filter to only events that have news coverage
      filtered = filtered.filter(event => {
        const articleCount = getArticleCountForDate(articlesByDate, event.date);
        return articleCount > 0;
      });
    } else if (sourceFilter === 'timeline') {
      // Show only timeline events (no additional filtering needed)
      // All events in the array are timeline events, so no filter needed
    }
    // 'all' shows everything (no source filter applied)

    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter((event) => {
        const titleMatch = event.title.toLowerCase().includes(query);
        const descMatch = event.description.toLowerCase().includes(query);
        const entityMatch = event.related_entities.some((e) =>
          e.toLowerCase().includes(query)
        );
        return titleMatch || descMatch || entityMatch;
      });
    }

    // Apply category filter
    if (selectedCategory !== 'all') {
      filtered = filtered.filter((event) => event.category === selectedCategory);
    }

    setFilteredEvents(filtered);
  };

  const formatDate = (dateString: string): string => {
    const parts = dateString.split('-');
    if (parts.length !== 3) return dateString;

    const [year, month, day] = parts;

    // Handle partial dates (00 for unknown day/month)
    if (day === '00' && month === '00') {
      return year;
    } else if (day === '00') {
      const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      return `${monthNames[parseInt(month) - 1]} ${year}`;
    }

    const date = new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const getCategoryColor = (category: string): string => {
    return categoryColors[category] || categoryColors.default;
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'biographical':
        return <Users className="h-4 w-4" />;
      case 'case':
        return <FileText className="h-4 w-4" />;
      case 'documents':
        return <FileText className="h-4 w-4" />;
      default:
        return <Clock className="h-4 w-4" />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent mb-4" />
          <p className="text-muted-foreground">Loading timeline...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold mb-2">Timeline</h1>
        <p className="text-muted-foreground">
          Comprehensive chronological view of {events.length} events
          {showNews && totalArticles > 0 && ` and ${totalArticles} news articles`}
          {events.length > 0 && ` spanning ${formatDate(events[0].date)} to ${formatDate(events[events.length - 1].date)}`}
        </p>
      </div>

      {/* Search and Filters */}
      <div className="space-y-4">
        {/* Search Input */}
        <div className="relative">
          <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            type="text"
            placeholder="Search timeline events..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>

        {/* News Coverage Toggle */}
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Switch
                id="show-news"
                checked={showNews}
                onCheckedChange={setShowNews}
              />
              <Label htmlFor="show-news" className="flex items-center gap-2 cursor-pointer">
                <Newspaper className="h-4 w-4" />
                <span>Show News Coverage</span>
                {showNews && !newsLoading && (
                  <Badge variant="secondary" className="ml-2">
                    {totalArticles} articles
                  </Badge>
                )}
                {showNews && newsLoading && (
                  <span className="text-xs text-muted-foreground ml-2">Loading...</span>
                )}
              </Label>
            </div>
          </div>
        </Card>

        {/* Source Type Filter */}
        <Card className="p-4">
          <div className="space-y-3">
            <Label className="text-sm font-medium">Source Type</Label>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => setSourceFilter('all')}
                className={`px-3 py-1.5 rounded-md text-sm transition-colors ${
                  sourceFilter === 'all'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-secondary hover:bg-secondary/80'
                }`}
              >
                All Sources
              </button>
              <button
                onClick={() => setSourceFilter('timeline')}
                className={`px-3 py-1.5 rounded-md text-sm transition-colors ${
                  sourceFilter === 'timeline'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-secondary hover:bg-secondary/80'
                }`}
              >
                Timeline Events
              </button>
              <button
                onClick={() => setSourceFilter('news')}
                className={`px-3 py-1.5 rounded-md text-sm transition-colors ${
                  sourceFilter === 'news'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-secondary hover:bg-secondary/80'
                }`}
              >
                News Articles
              </button>
            </div>
          </div>
        </Card>

        {/* Category Filters */}
        <div className="flex flex-wrap gap-2 items-center">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <button
            onClick={() => setSelectedCategory('all')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              selectedCategory === 'all'
                ? 'bg-primary text-primary-foreground'
                : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
            }`}
          >
            All Categories
          </button>
          <button
            onClick={() => setSelectedCategory('biographical')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2 ${
              selectedCategory === 'biographical'
                ? 'bg-primary text-primary-foreground'
                : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
            }`}
          >
            <Users className="h-4 w-4" />
            Biographical
          </button>
          <button
            onClick={() => setSelectedCategory('case')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2 ${
              selectedCategory === 'case'
                ? 'bg-primary text-primary-foreground'
                : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
            }`}
          >
            <FileText className="h-4 w-4" />
            Legal Case
          </button>
          <button
            onClick={() => setSelectedCategory('documents')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2 ${
              selectedCategory === 'documents'
                ? 'bg-primary text-primary-foreground'
                : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
            }`}
          >
            <FileText className="h-4 w-4" />
            Documents
          </button>
        </div>
      </div>

      {/* Results Count */}
      <div className="text-sm text-muted-foreground">
        Showing {filteredEvents.length.toLocaleString()} of {events.length.toLocaleString()} events
      </div>

      {/* Loading state for news filter */}
      {sourceFilter === 'news' && newsLoading && (
        <div className="text-center py-8">
          <div className="inline-block h-6 w-6 animate-spin rounded-full border-4 border-solid border-current border-r-transparent mb-2" />
          <p className="text-muted-foreground">Loading news articles...</p>
        </div>
      )}

      {/* Timeline */}
      <div className="relative space-y-6">
        {/* Timeline Line */}
        <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-border" />

        {/* Events */}
        {filteredEvents.map((event, index) => {
          const eventDate = event.date;
          const articleCount = showNews ? getArticleCountForDate(articlesByDate, eventDate) : 0;
          const eventArticles = showNews && articlesByDate[eventDate] ? articlesByDate[eventDate].slice(0, 3) : [];

          return (
            <div key={index} className="relative pl-14">
              {/* Timeline Dot */}
              <div className={`absolute left-4 top-2 w-4 h-4 rounded-full border-4 border-background ${
                articleCount > 0 ? 'bg-blue-500' : 'bg-primary'
              }`} />

              <Card className="hover:shadow-lg transition-shadow">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between gap-4">
                    <div className="space-y-1 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <Badge variant="outline" className={getCategoryColor(event.category)}>
                          <span className="mr-1">{getCategoryIcon(event.category)}</span>
                          {event.category}
                        </Badge>
                        <span className="text-sm text-muted-foreground">
                          {formatDate(event.date)}
                        </span>
                        {articleCount > 0 && (
                          <Badge variant="secondary" className="bg-blue-100 text-blue-800">
                            <Newspaper className="h-3 w-3 mr-1" />
                            {articleCount} news {articleCount === 1 ? 'article' : 'articles'}
                          </Badge>
                        )}
                      </div>
                      <CardTitle className="text-lg leading-tight">
                        {event.title}
                      </CardTitle>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                {/* Description */}
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {event.description}
                </p>

                {/* Related Entities */}
                {event.related_entities.length > 0 && (
                  <div className="space-y-1.5">
                    <div className="text-xs font-medium text-muted-foreground">
                      Related Entities:
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {event.related_entities.map((entity, idx) => {
                        const entityId = entityNameToId(entity);
                        return (
                          <Link
                            key={idx}
                            to={`/entities/${entityId}`}
                            className="inline-block transition-transform hover:scale-105"
                            aria-label={`View ${formatEntityName(entity)} profile`}
                          >
                            <Badge
                              variant="secondary"
                              className="text-xs cursor-pointer hover:bg-secondary/80 transition-colors"
                            >
                              {formatEntityName(entity)}
                            </Badge>
                          </Link>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Source */}
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <span className="font-medium">Source:</span>
                  {event.source_url ? (
                    <a
                      href={event.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 hover:text-primary transition-colors"
                    >
                      {event.source}
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  ) : (
                    <span>{event.source}</span>
                  )}
                </div>

                {/* Related News Articles */}
                {eventArticles.length > 0 && (
                  <div className="mt-4 pt-4 border-t">
                    <div className="text-xs font-medium text-muted-foreground mb-2 flex items-center gap-1">
                      <Newspaper className="h-3 w-3" />
                      Related News Articles:
                    </div>
                    <div className="space-y-2">
                      {eventArticles.map((article) => (
                        <div key={article.id} className="text-xs p-2 rounded-md bg-secondary/50 hover:bg-secondary transition-colors">
                          <a
                            href={article.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="font-medium hover:text-primary transition-colors line-clamp-2"
                          >
                            {article.title}
                          </a>
                          <div className="flex items-center gap-2 mt-1 text-muted-foreground">
                            <span>{article.publication}</span>
                            <span>•</span>
                            <span>{new Date(article.published_date).toLocaleDateString()}</span>
                          </div>
                        </div>
                      ))}
                      {articleCount > 3 && (
                        <div className="text-xs text-muted-foreground text-center pt-1">
                          +{articleCount - 3} more articles on this date
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
          );
        })}
      </div>

      {/* Empty State */}
      {filteredEvents.length === 0 && (
        <div className="text-center py-12">
          <Calendar className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <p className="text-lg font-medium mb-1">No events found</p>
          <p className="text-muted-foreground">
            Try adjusting your search or filter criteria
          </p>
        </div>
      )}
    </div>
  );
}
