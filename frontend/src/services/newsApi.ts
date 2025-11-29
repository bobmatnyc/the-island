/**
 * News API Client
 * Handles all news-related API requests
 */

import type {
  NewsArticle,
  NewsSearchParams,
  NewsSearchResult,
  SourceSummary,
  NewsStats,
} from '@/types/news';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8081';

/**
 * Fetch wrapper with timeout and error handling
 *
 * Design Decision: Robust API Client with Fallback
 * Rationale: News API uses ngrok which can be unreliable. Implementing
 * timeout, retry, and fallback to localhost prevents silent failures.
 *
 * Features:
 * - 10-second timeout per request (configurable)
 * - Fallback to localhost if primary URL fails
 * - Detailed error messages for debugging
 * - AbortController support for request cancellation
 *
 * Trade-offs:
 * - Performance: Fallback adds latency on failure (1-2s)
 * - Complexity: More error handling code
 * - UX: Better error messages vs. generic failures
 */
async function fetchAPI<T>(
  endpoint: string,
  options?: RequestInit & { timeout?: number }
): Promise<T> {
  const timeout = options?.timeout ?? 10000; // Default 10s timeout
  const urls = [API_BASE_URL, 'http://localhost:8081'].filter(
    (url, index, self) => self.indexOf(url) === index // Remove duplicates
  );

  let lastError: Error | null = null;

  // Try each URL in sequence
  for (const baseUrl of urls) {
    const url = `${baseUrl}${endpoint}`;

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout);

      // Combine user's signal with timeout signal
      const signal = options?.signal
        ? combineSignals([options.signal, controller.signal])
        : controller.signal;

      const response = await fetch(url, {
        ...options,
        signal,
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      lastError = error as Error;

      // Check if this was a timeout
      if (lastError.name === 'AbortError') {
        lastError = new Error(`Request timeout after ${timeout}ms`);
      }

      console.error(`Failed to fetch ${url}:`, lastError.message);

      // If this is the last URL, throw the error
      if (baseUrl === urls[urls.length - 1]) {
        throw lastError;
      }

      // Otherwise, try the next URL
      console.log(`Falling back to next URL...`);
    }
  }

  // Should never reach here, but TypeScript needs it
  throw lastError || new Error('All API requests failed');
}

/**
 * Combine multiple AbortSignals into one
 * Helper for supporting both user cancellation and timeout
 */
function combineSignals(signals: AbortSignal[]): AbortSignal {
  const controller = new AbortController();

  for (const signal of signals) {
    if (signal.aborted) {
      controller.abort();
      break;
    }

    signal.addEventListener('abort', () => controller.abort(), { once: true });
  }

  return controller.signal;
}

/**
 * Convert search result to NewsArticle format
 */
function convertSearchResultToArticle(result: NewsSearchResult): NewsArticle {
  const metadata = result.metadata;

  return {
    id: result.id,
    title: metadata.title || 'Untitled Article',
    publication: metadata.publication || 'Unknown',
    author: metadata.author,
    published_date: metadata.published_date || '',
    url: metadata.url || '',
    archive_url: metadata.archive_url,
    content_excerpt: result.text_excerpt,
    word_count: metadata.word_count || 0,
    entities_mentioned: metadata.entity_mentions
      ? metadata.entity_mentions.split(',').map(e => e.trim())
      : [],
    entity_mention_counts: {},
    related_timeline_events: [],
    credibility_score: metadata.credibility_score || 0.5,
    tags: metadata.tags ? metadata.tags.split(',').map(t => t.trim()) : [],
    language: metadata.language || 'en',
    access_type: metadata.access_type || 'public',
  };
}

export const newsApi = {
  /**
   * Search news articles with filters
   */
  async searchNews(params: NewsSearchParams): Promise<NewsArticle[]> {
    const queryParams = new URLSearchParams();

    queryParams.set('limit', (params.limit || 20).toString());

    if (params.publication) {
      queryParams.set('publication', params.publication);
    }

    if (params.min_credibility !== undefined) {
      queryParams.set('min_credibility', params.min_credibility.toString());
    }

    if (params.entity) {
      queryParams.set('entity', params.entity);
    }

    if (params.start_date) {
      queryParams.set('start_date', params.start_date);
    }

    if (params.end_date) {
      queryParams.set('end_date', params.end_date);
    }

    // Use the correct /api/news/articles endpoint
    const response = await fetchAPI<{ articles: NewsArticle[]; total: number; limit: number; offset: number }>(
      `/api/news/articles?${queryParams.toString()}`
    );

    return response.articles;
  },

  /**
   * Get a single article by ID
   */
  async getArticle(id: string): Promise<NewsArticle> {
    const response = await fetchAPI<NewsArticle>(
      `/api/news/articles/${id}`
    );

    return response;
  },

  /**
   * Get all news sources/publications
   */
  async getSources(): Promise<SourceSummary[]> {
    // This endpoint may need to be implemented on the backend
    // For now, return mock data based on common sources
    // TODO: Implement backend endpoint for source aggregation
    return [];
  },

  /**
   * Get news statistics
   */
  async getStats(): Promise<NewsStats> {
    // Use the /api/news/stats endpoint
    const response = await fetchAPI<{
      total_articles: number;
      total_sources: number;
      date_range: { earliest: string; latest: string };
      articles_by_source: Record<string, number>;
      last_updated?: string;
    }>('/api/news/stats');

    // Fetch all articles with pagination (backend max limit is 100)
    const allArticles: NewsArticle[] = [];
    let offset = 0;
    const limit = 100; // Backend maximum allowed limit

    while (true) {
      const articlesResponse = await fetchAPI<{ articles: NewsArticle[]; total: number }>(
        `/api/news/articles?limit=${limit}&offset=${offset}`
      );

      allArticles.push(...articlesResponse.articles);

      // Stop if we've fetched all articles
      if (allArticles.length >= articlesResponse.total || articlesResponse.articles.length === 0) {
        break;
      }

      offset += limit;
    }

    const credibilityTiers = allArticles.reduce((acc, article) => {
      if (article.credibility_score >= 0.90) acc.high++;
      else if (article.credibility_score >= 0.75) acc.medium++;
      else acc.low++;
      return acc;
    }, { high: 0, medium: 0, low: 0 });

    const entityCounts = allArticles.reduce((acc, article) => {
      article.entities_mentioned.forEach(entity => {
        acc[entity] = (acc[entity] || 0) + 1;
      });
      return acc;
    }, {} as Record<string, number>);

    const topPublications = Object.entries(response.articles_by_source)
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 5);

    const topEntities = Object.entries(entityCounts)
      .map(([name, mention_count]) => ({ name, mention_count }))
      .sort((a, b) => b.mention_count - a.mention_count)
      .slice(0, 10);

    return {
      total_articles: response.total_articles,
      date_range: response.date_range,
      publications: topPublications,
      credibility_tiers: credibilityTiers,
      top_entities: topEntities,
      timeline: [], // Would need date aggregation
    };
  },

  /**
   * Get similar articles to a given article
   */
  async getSimilarArticles(id: string, limit: number = 5): Promise<NewsArticle[]> {
    const response = await fetchAPI<{
      source_doc_id: string;
      similar_documents: NewsSearchResult[];
      total_results: number;
    }>(`/api/rag/similar-news/${id}?limit=${limit}`);

    return response.similar_documents.map(convertSearchResultToArticle);
  },

  /**
   * Get all available publications from search results
   */
  async getPublications(): Promise<string[]> {
    const response = await fetchAPI<{ sources: Array<{ publication: string }>; total_sources: number }>(
      '/api/news/sources'
    );

    return response.sources.map(s => s.publication).sort();
  },

  /**
   * Get all available tags from search results
   */
  async getTags(): Promise<string[]> {
    // Fetch all articles with pagination (backend max limit is 100)
    const allArticles: NewsArticle[] = [];
    let offset = 0;
    const limit = 100; // Backend maximum allowed limit

    while (true) {
      const response = await fetchAPI<{ articles: NewsArticle[]; total: number }>(
        `/api/news/articles?limit=${limit}&offset=${offset}`
      );

      allArticles.push(...response.articles);

      // Stop if we've fetched all articles
      if (allArticles.length >= response.total || response.articles.length === 0) {
        break;
      }

      offset += limit;
    }

    const tags = new Set<string>();
    allArticles.forEach(article => {
      article.tags.forEach(tag => tags.add(tag));
    });

    return Array.from(tags).sort();
  },

  /**
   * Get articles for specific entity
   */
  async getArticlesByEntity(entityName: string, limit: number = 10): Promise<NewsArticle[]> {
    return this.searchNews({ entity: entityName, limit });
  },

  /**
   * Get articles for date range
   *
   * Design Decision: Fetch ALL articles with pagination
   * Rationale: Timeline needs complete article set, not just first page.
   * Previous implementation only fetched 100 articles (first page), causing
   * incorrect counts in Timeline badge and missing articles.
   *
   * Performance: Uses pagination to fetch all articles in batches of 100.
   * For 200 articles, this means 2 API calls (~200ms total).
   *
   * Trade-offs:
   * - Correctness: Shows all articles vs. missing data
   * - Performance: Multiple requests vs. single incomplete request
   * - UX: Brief loading vs. incorrect counts
   */
  async getArticlesByDateRange(startDate: string, endDate: string, limit?: number): Promise<NewsArticle[]> {
    // If explicit limit provided, use single fetch (backwards compatibility)
    if (limit !== undefined) {
      return this.searchNews({ start_date: startDate, end_date: endDate, limit });
    }

    // Otherwise, fetch ALL articles with pagination
    const allArticles: NewsArticle[] = [];
    let offset = 0;
    const batchSize = 100; // Backend maximum allowed limit

    while (true) {
      const response = await fetchAPI<{ articles: NewsArticle[]; total: number }>(
        `/api/news/articles?start_date=${startDate}&end_date=${endDate}&limit=${batchSize}&offset=${offset}`
      );

      allArticles.push(...response.articles);

      // Stop if we've fetched all articles
      if (allArticles.length >= response.total || response.articles.length === 0) {
        break;
      }

      offset += batchSize;
    }

    console.log(`[newsApi.getArticlesByDateRange] Fetched ${allArticles.length} articles for date range ${startDate} to ${endDate}`);

    return allArticles;
  },

  /**
   * Get articles around specific date (±windowDays)
   */
  async getArticlesNearDate(date: string, windowDays: number = 7, limit: number = 50): Promise<NewsArticle[]> {
    const centerDate = new Date(date);
    const startDate = new Date(centerDate);
    startDate.setDate(startDate.getDate() - windowDays);
    const endDate = new Date(centerDate);
    endDate.setDate(endDate.getDate() + windowDays);

    const start = startDate.toISOString().split('T')[0];
    const end = endDate.toISOString().split('T')[0];

    return this.getArticlesByDateRange(start, end, limit);
  },

  /**
   * Semantic search for news articles
   * Uses keyword-based relevance scoring on backend
   */
  async searchSemantic(params: {
    query: string;
    limit?: number;
    similarity_threshold?: number;
    publication?: string;
    start_date?: string;
    end_date?: string;
    min_credibility?: number;
    entities?: string[];
  }): Promise<{
    query: string;
    results: Array<{
      article: NewsArticle;
      similarity_score: number;
      matched_excerpt: string;
      search_method: string;
    }>;
    total: number;
    filters_applied: Record<string, any>;
  }> {
    const queryParams = new URLSearchParams();

    queryParams.set('query', params.query);

    if (params.limit) {
      queryParams.set('limit', params.limit.toString());
    }

    if (params.similarity_threshold !== undefined) {
      queryParams.set('similarity_threshold', params.similarity_threshold.toString());
    }

    if (params.publication) {
      queryParams.set('publication', params.publication);
    }

    if (params.start_date) {
      queryParams.set('start_date', params.start_date);
    }

    if (params.end_date) {
      queryParams.set('end_date', params.end_date);
    }

    if (params.min_credibility !== undefined) {
      queryParams.set('min_credibility', params.min_credibility.toString());
    }

    if (params.entities && params.entities.length > 0) {
      queryParams.set('entities', params.entities.join(','));
    }

    return fetchAPI(`/api/news/search/semantic?${queryParams.toString()}`);
  },

  /**
   * Find articles similar to a given article
   * Uses article content to find semantically similar articles
   */
  async findSimilar(
    articleId: string,
    options?: {
      limit?: number;
      similarity_threshold?: number;
    }
  ): Promise<{
    reference_article_id: string;
    similar_articles: Array<{
      article: NewsArticle;
      similarity_score: number;
      matched_excerpt: string;
    }>;
    total: number;
  }> {
    const queryParams = new URLSearchParams();

    if (options?.limit) {
      queryParams.set('limit', options.limit.toString());
    }

    if (options?.similarity_threshold !== undefined) {
      queryParams.set('similarity_threshold', options.similarity_threshold.toString());
    }

    return fetchAPI(`/api/news/search/similar/${articleId}?${queryParams.toString()}`);
  },

  /**
   * Get semantic search statistics
   */
  async getSearchStats(): Promise<{
    total_articles: number;
    indexed_articles: number;
    unindexed_articles: number;
    search_method: string;
    note?: string;
    recommendation?: string;
  }> {
    return fetchAPI('/api/news/search/stats');
  },
};
