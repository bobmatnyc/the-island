import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ExternalLink, Archive, Calendar, User, Award } from 'lucide-react';
import type { NewsArticle } from '@/types/news';

interface ArticleCardProps {
  article: NewsArticle;
  onEntityClick?: (entity: string) => void;
  compact?: boolean;
}

export function ArticleCard({ article, onEntityClick, compact = false }: ArticleCardProps) {
  // Format date
  const formatDate = (dateString: string) => {
    if (!dateString) return 'Unknown date';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  // Get credibility color class
  const getCredibilityColor = (score: number) => {
    if (score >= 0.90) return 'text-green-600 dark:text-green-400';
    if (score >= 0.75) return 'text-blue-600 dark:text-blue-400';
    return 'text-gray-600 dark:text-gray-400';
  };

  // Truncate excerpt
  const truncateExcerpt = (text: string, maxLength: number = 200) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength).trim() + '...';
  };

  // Compact variant rendering
  if (compact) {
    return (
      <Card className="hover:shadow-md transition-shadow">
        <CardHeader className="pb-2 space-y-2">
          {/* Title */}
          <Link
            to={`/news/${article.id}`}
            className="group"
          >
            <h3 className="text-base font-semibold leading-tight group-hover:text-primary transition-colors line-clamp-2">
              {article.title}
            </h3>
          </Link>

          {/* Metadata Row */}
          <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
            {/* Publication */}
            <Badge variant="secondary" className="text-xs">
              {article.publication}
            </Badge>

            {/* Date */}
            <div className="flex items-center gap-1">
              <Calendar className="h-3 w-3" />
              <span>{formatDate(article.published_date)}</span>
            </div>

            {/* Credibility Score */}
            <div className="flex items-center gap-1">
              <Award className={`h-3 w-3 ${getCredibilityColor(article.credibility_score)}`} />
              <span className={getCredibilityColor(article.credibility_score)}>
                {(article.credibility_score * 100).toFixed(0)}%
              </span>
            </div>
          </div>
        </CardHeader>

        <CardContent className="pt-2 space-y-2">
          {/* Excerpt - First line only */}
          <p className="text-xs leading-relaxed text-muted-foreground line-clamp-2">
            {truncateExcerpt(article.content_excerpt, 120)}
          </p>

          {/* Action Button */}
          {article.url && (
            <Button
              variant="outline"
              size="sm"
              asChild
              className="w-full h-8"
            >
              <a
                href={article.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center gap-2"
              >
                <ExternalLink className="h-3 w-3" />
                Read Article
              </a>
            </Button>
          )}
        </CardContent>
      </Card>
    );
  }

  // Full variant rendering (original)
  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader className="space-y-3">
        {/* Title */}
        <Link
          to={`/news/${article.id}`}
          className="group"
        >
          <h3 className="text-xl font-semibold leading-tight group-hover:text-primary transition-colors">
            {article.title}
          </h3>
        </Link>

        {/* Metadata Row */}
        <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
          {/* Publication */}
          <Badge variant="secondary" className="font-medium">
            {article.publication}
          </Badge>

          {/* Author */}
          {article.author && (
            <div className="flex items-center gap-1">
              <User className="h-3 w-3" />
              <span>{article.author}</span>
            </div>
          )}

          {/* Date */}
          <div className="flex items-center gap-1">
            <Calendar className="h-3 w-3" />
            <span>{formatDate(article.published_date)}</span>
          </div>

          {/* Credibility Score */}
          <div className="flex items-center gap-1">
            <Award className={`h-3 w-3 ${getCredibilityColor(article.credibility_score)}`} />
            <span className={getCredibilityColor(article.credibility_score)}>
              {(article.credibility_score * 100).toFixed(0)}%
            </span>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Excerpt */}
        <p className="text-sm leading-relaxed text-muted-foreground">
          {truncateExcerpt(article.content_excerpt)}
          {article.content_excerpt.length > 200 && (
            <Link
              to={`/news/${article.id}`}
              className="ml-1 text-primary hover:underline font-medium"
            >
              Read more
            </Link>
          )}
        </p>

        {/* Entity Tags */}
        {article.entities_mentioned.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {article.entities_mentioned.slice(0, 5).map((entity) => (
              <Badge
                key={entity}
                variant="outline"
                className="cursor-pointer hover:bg-accent"
                onClick={() => onEntityClick?.(entity)}
              >
                {entity}
              </Badge>
            ))}
            {article.entities_mentioned.length > 5 && (
              <Badge variant="outline" className="text-muted-foreground">
                +{article.entities_mentioned.length - 5} more
              </Badge>
            )}
          </div>
        )}

        {/* Tags */}
        {article.tags.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {article.tags.map((tag) => (
              <Badge key={tag} variant="secondary" className="text-xs">
                {tag}
              </Badge>
            ))}
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-2 pt-2">
          {article.url && (
            <Button
              variant="default"
              size="sm"
              asChild
              className="flex-1"
            >
              <a
                href={article.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center gap-2"
              >
                <ExternalLink className="h-4 w-4" />
                Read Full Article
              </a>
            </Button>
          )}

          {article.archive_url && (
            <Button
              variant="outline"
              size="sm"
              asChild
            >
              <a
                href={article.archive_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2"
              >
                <Archive className="h-4 w-4" />
                Archive
              </a>
            </Button>
          )}
        </div>

        {/* Word Count & Language */}
        <div className="flex gap-4 text-xs text-muted-foreground pt-2 border-t">
          <span>{article.word_count.toLocaleString()} words</span>
          {article.language && article.language !== 'en' && (
            <span className="uppercase">{article.language}</span>
          )}
          {article.access_type && article.access_type !== 'public' && (
            <Badge variant="outline" className="text-xs">
              {article.access_type}
            </Badge>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
