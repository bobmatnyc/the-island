import { useState, useMemo, useCallback, memo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Calendar,
  TrendingUp,
  TrendingDown,
  Newspaper
} from 'lucide-react';
import { NewsTimelineItem } from './NewsTimelineItem';
import type { NewsArticle } from '@/types/news';

interface NewsTimelineProps {
  articles: NewsArticle[];
  loading?: boolean;
  onEntityClick?: (entity: string) => void;
}

interface DateGroup {
  year: number;
  month: number;
  articles: NewsArticle[];
}

/**
 * News Timeline Component
 *
 * Design: Chronological vertical timeline of news articles
 * - Groups articles by year/month
 * - Color-coded timeline markers by credibility
 * - Expandable article cards
 * - Sorting options (ascending/descending)
 * - Performance optimized with memoization
 *
 * Performance:
 * - Memoized grouping for large article lists
 * - Virtualization ready (currently showing all, can be enhanced)
 * - Efficient re-renders with React.memo
 */
export const NewsTimeline = memo(function NewsTimeline({
  articles,
  loading = false,
  onEntityClick,
}: NewsTimelineProps) {
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // Group articles by year and month with memoization
  const groupedArticles = useMemo(() => {
    if (!articles.length) return [];

    // Sort articles by date
    const sorted = [...articles].sort((a, b) => {
      const dateA = new Date(a.published_date).getTime();
      const dateB = new Date(b.published_date).getTime();
      return sortOrder === 'desc' ? dateB - dateA : dateA - dateB;
    });

    // Group by year and month
    const groups = new Map<string, DateGroup>();

    sorted.forEach((article) => {
      const date = new Date(article.published_date);
      const year = date.getFullYear();
      const month = date.getMonth();
      const key = `${year}-${month}`;

      if (!groups.has(key)) {
        groups.set(key, { year, month, articles: [] });
      }

      groups.get(key)!.articles.push(article);
    });

    return Array.from(groups.values());
  }, [articles, sortOrder]);

  // Toggle sort order
  const toggleSortOrder = useCallback(() => {
    setSortOrder(prev => prev === 'desc' ? 'asc' : 'desc');
  }, []);

  // Format month/year header
  const formatGroupHeader = (year: number, month: number) => {
    const date = new Date(year, month);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
    });
  };

  // Loading skeleton
  if (loading) {
    return (
      <div className="space-y-6">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="flex gap-4">
            <Skeleton className="w-6 h-6 rounded-full flex-shrink-0" />
            <Card className="flex-1">
              <CardHeader className="space-y-3">
                <Skeleton className="h-6 w-3/4" />
                <Skeleton className="h-4 w-full" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-20 w-full" />
              </CardContent>
            </Card>
          </div>
        ))}
      </div>
    );
  }

  // Empty state
  if (articles.length === 0) {
    return (
      <Card>
        <CardContent className="pt-12 pb-12">
          <div className="text-center">
            <Newspaper className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No articles found</h3>
            <p className="text-muted-foreground">
              Try adjusting your filters or search criteria
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Timeline Controls */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="h-5 w-5" />
                Timeline View
              </CardTitle>
              <CardDescription>
                {articles.length} articles across {groupedArticles.length} time periods
              </CardDescription>
            </div>

            {/* Sort Toggle */}
            <Button
              variant="outline"
              size="sm"
              onClick={toggleSortOrder}
              className="flex items-center gap-2"
            >
              {sortOrder === 'desc' ? (
                <>
                  <TrendingDown className="h-4 w-4" />
                  Newest First
                </>
              ) : (
                <>
                  <TrendingUp className="h-4 w-4" />
                  Oldest First
                </>
              )}
            </Button>
          </div>
        </CardHeader>
      </Card>

      {/* Timeline Groups */}
      <div className="space-y-8">
        {groupedArticles.map((group) => (
          <div key={`${group.year}-${group.month}`} className="space-y-4">
            {/* Period Header */}
            <div className="sticky top-14 z-20 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 py-3 -mx-4 px-4">
              <div className="flex items-center gap-3">
                <div className="flex-1 h-px bg-border" />
                <Badge variant="secondary" className="text-sm font-semibold px-4 py-1.5">
                  <Calendar className="h-3.5 w-3.5 mr-2 inline" />
                  {formatGroupHeader(group.year, group.month)}
                </Badge>
                <Badge variant="outline" className="text-xs">
                  {group.articles.length} article{group.articles.length !== 1 ? 's' : ''}
                </Badge>
                <div className="flex-1 h-px bg-border" />
              </div>
            </div>

            {/* Articles in this period */}
            <div className="space-y-0">
              {group.articles.map((article) => (
                <NewsTimelineItem
                  key={article.id}
                  article={article}
                  onEntityClick={onEntityClick}
                />
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Timeline End Marker */}
      <div className="flex items-center justify-center pt-8 pb-4">
        <div className="flex items-center gap-3 text-sm text-muted-foreground">
          <div className="h-px w-12 bg-border" />
          <span>End of timeline</span>
          <div className="h-px w-12 bg-border" />
        </div>
      </div>
    </div>
  );
});
