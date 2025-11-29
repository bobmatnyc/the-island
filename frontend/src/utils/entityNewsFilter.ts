/**
 * Utility functions for filtering news articles by entity names
 */

import type { NewsArticle } from '@/types/news';

/**
 * Normalize entity name for matching (lowercase, trim spaces)
 */
function normalizeEntityName(name: string): string {
  return name.toLowerCase().trim();
}

/**
 * Check if entity name matches any of the article's mentioned entities
 * Handles case-insensitive matching and common aliases
 */
function entityMatchesArticle(entityName: string, article: NewsArticle): boolean {
  const normalizedQuery = normalizeEntityName(entityName);

  // Check entities_mentioned array
  const matchesEntity = article.entities_mentioned.some(
    entity => normalizeEntityName(entity) === normalizedQuery
  );

  if (matchesEntity) return true;

  // Check if entity is mentioned in title or excerpt (case-insensitive)
  const titleMatch = article.title.toLowerCase().includes(normalizedQuery);
  const excerptMatch = article.content_excerpt.toLowerCase().includes(normalizedQuery);

  return titleMatch || excerptMatch;
}

/**
 * Filter articles by entity name
 * Returns articles that mention the specified entity
 */
export function filterArticlesByEntity(
  articles: NewsArticle[],
  entityName: string
): NewsArticle[] {
  if (!entityName || !articles.length) {
    return [];
  }

  return articles.filter(article => entityMatchesArticle(entityName, article));
}

/**
 * Get count of articles mentioning a specific entity
 */
export function getArticleCountByEntity(
  articles: NewsArticle[],
  entityName: string
): number {
  return filterArticlesByEntity(articles, entityName).length;
}

/**
 * Sort articles by published date (newest first)
 */
export function sortArticlesByDate(articles: NewsArticle[]): NewsArticle[] {
  return [...articles].sort((a, b) => {
    const dateA = new Date(a.published_date || 0).getTime();
    const dateB = new Date(b.published_date || 0).getTime();
    return dateB - dateA; // Descending (newest first)
  });
}

/**
 * Filter articles by date range
 */
export function filterArticlesByDateRange(
  articles: NewsArticle[],
  startDate: string,
  endDate: string
): NewsArticle[] {
  const start = new Date(startDate).getTime();
  const end = new Date(endDate).getTime();

  return articles.filter(article => {
    if (!article.published_date) return false;
    const articleDate = new Date(article.published_date).getTime();
    return articleDate >= start && articleDate <= end;
  });
}

/**
 * Get articles published within a window around a specific date
 * @param date - Center date (YYYY-MM-DD)
 * @param windowDays - Number of days before and after (default: 7)
 */
export function getArticlesNearDate(
  articles: NewsArticle[],
  date: string,
  windowDays: number = 7
): NewsArticle[] {
  const centerDate = new Date(date);
  const startDate = new Date(centerDate);
  startDate.setDate(startDate.getDate() - windowDays);
  const endDate = new Date(centerDate);
  endDate.setDate(endDate.getDate() + windowDays);

  return filterArticlesByDateRange(
    articles,
    startDate.toISOString().split('T')[0],
    endDate.toISOString().split('T')[0]
  );
}
