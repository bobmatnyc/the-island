/**
 * Custom hook for integrating news articles with timeline events
 */

import { useState, useEffect } from 'react';
import { newsApi } from '@/services/newsApi';
import type { NewsArticle } from '@/types/news';

interface DateRange {
  start: string;
  end: string;
}

interface ArticlesByDate {
  [date: string]: NewsArticle[];
}

interface UseTimelineNewsResult {
  newsArticles: NewsArticle[];
  articlesByDate: ArticlesByDate;
  loading: boolean;
  error: string | null;
  totalArticles: number;
}

/**
 * Hook to fetch and manage news articles for timeline date ranges
 * @param dateRange - Start and end dates for the timeline (YYYY-MM-DD format)
 * @param enabled - Whether to fetch news articles (toggle control)
 */
export function useTimelineNews(
  dateRange: DateRange,
  enabled: boolean
): UseTimelineNewsResult {
  const [newsArticles, setNewsArticles] = useState<NewsArticle[]>([]);
  const [articlesByDate, setArticlesByDate] = useState<ArticlesByDate>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    console.log('[useTimelineNews] Effect triggered', {
      enabled,
      dateRange,
      hasStartDate: !!dateRange.start,
      hasEndDate: !!dateRange.end,
      timestamp: new Date().toISOString(),
    });

    // Skip if not enabled or invalid date range
    if (!enabled || !dateRange.start || !dateRange.end) {
      console.log('[useTimelineNews] Skipping fetch', {
        enabled,
        hasStartDate: !!dateRange.start,
        hasEndDate: !!dateRange.end,
      });
      setNewsArticles([]);
      setArticlesByDate({});
      return;
    }

    let isCancelled = false;

    const fetchNewsArticles = async () => {
      try {
        console.log('[useTimelineNews] Starting fetch', {
          dateRange,
          timestamp: new Date().toISOString(),
        });

        setLoading(true);
        setError(null);

        // Fetch ALL articles for the date range (no limit - fetch all pages)
        const articles = await newsApi.getArticlesByDateRange(
          dateRange.start,
          dateRange.end
          // No limit parameter = fetch all articles via pagination
        );

        console.log('[useTimelineNews] Fetch complete', {
          articleCount: articles.length,
          totalArticles: articles.length, // Now accurate (all articles fetched)
          sampleArticles: articles.slice(0, 3).map(a => ({
            title: a.title,
            date: a.published_date,
          })),
          timestamp: new Date().toISOString(),
        });

        if (isCancelled) return;

        // Group articles by date
        const grouped = groupArticlesByDate(articles);

        console.log('[useTimelineNews] Articles grouped by date', {
          totalArticles: articles.length,
          uniqueDates: Object.keys(grouped).length,
          sampleDates: Object.keys(grouped).slice(0, 5),
          articlesPerDate: Object.fromEntries(
            Object.entries(grouped).slice(0, 5).map(([date, arts]) => [date, arts.length])
          ),
        });

        setNewsArticles(articles);
        setArticlesByDate(grouped);
      } catch (err) {
        if (isCancelled) return;
        console.error('[useTimelineNews] Failed to fetch timeline news:', err);
        setError('Failed to load news articles for timeline');
        setNewsArticles([]);
        setArticlesByDate({});
      } finally {
        if (!isCancelled) {
          console.log('[useTimelineNews] Fetch finished, loading=false');
          setLoading(false);
        }
      }
    };

    fetchNewsArticles();

    // Cleanup function to prevent state updates after unmount
    return () => {
      isCancelled = true;
    };
  }, [dateRange.start, dateRange.end, enabled]);

  return {
    newsArticles,
    articlesByDate,
    loading,
    error,
    totalArticles: newsArticles.length,
  };
}

/**
 * Group articles by their published date (YYYY-MM-DD)
 */
function groupArticlesByDate(articles: NewsArticle[]): ArticlesByDate {
  const grouped: ArticlesByDate = {};

  articles.forEach(article => {
    if (!article.published_date) return;

    // Extract date part (YYYY-MM-DD)
    const date = article.published_date.split('T')[0];

    if (!grouped[date]) {
      grouped[date] = [];
    }

    grouped[date].push(article);
  });

  // Sort articles within each date by published_date
  Object.keys(grouped).forEach(date => {
    grouped[date].sort((a, b) => {
      const timeA = new Date(a.published_date).getTime();
      const timeB = new Date(b.published_date).getTime();
      return timeB - timeA; // Newest first
    });
  });

  return grouped;
}

/**
 * Get article count for a specific date
 */
export function getArticleCountForDate(
  articlesByDate: ArticlesByDate,
  date: string
): number {
  return articlesByDate[date]?.length || 0;
}

/**
 * Check if a date has any articles
 */
export function hasArticlesForDate(
  articlesByDate: ArticlesByDate,
  date: string
): boolean {
  return !!articlesByDate[date] && articlesByDate[date].length > 0;
}
