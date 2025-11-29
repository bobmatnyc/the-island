/**
 * TypeScript type definitions for news articles and related data
 */

export interface NewsArticle {
  id: string;
  title: string;
  publication: string;
  author?: string;
  published_date: string;
  url: string;
  archive_url?: string;
  content_excerpt: string;
  word_count: number;
  entities_mentioned: string[];
  entity_mention_counts: Record<string, number>;
  related_timeline_events: string[];
  credibility_score: number;
  tags: string[];
  language: string;
  access_type: string;
  doc_type?: string;
}

export interface NewsSearchParams {
  query?: string;
  entity?: string;
  publication?: string;
  start_date?: string;
  end_date?: string;
  min_credibility?: number;
  tags?: string[];
  limit?: number;
  offset?: number;
}

export interface SourceSummary {
  publication: string;
  article_count: number;
  avg_credibility: number;
  date_range: {
    start: string;
    end: string;
  };
}

export interface NewsStats {
  total_articles: number;
  date_range: {
    earliest: string;
    latest: string;
  };
  publications: Array<{
    name: string;
    count: number;
  }>;
  credibility_tiers: {
    high: number; // >= 0.90
    medium: number; // 0.75-0.90
    low: number; // < 0.75
  };
  top_entities: Array<{
    name: string;
    mention_count: number;
  }>;
  timeline: Array<{
    month: string;
    count: number;
  }>;
}

export interface NewsSearchResult {
  id: string;
  similarity: number;
  text_excerpt: string;
  metadata: {
    title?: string;
    publication?: string;
    author?: string;
    published_date?: string;
    url?: string;
    archive_url?: string;
    credibility_score?: number;
    entity_mentions?: string;
    tags?: string;
    word_count?: number;
    language?: string;
    access_type?: string;
  };
}

export interface NewsSearchResponse {
  query: string;
  results: NewsSearchResult[];
  total_results: number;
  search_time_ms: number;
}
