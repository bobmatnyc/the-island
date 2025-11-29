import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  ExternalLink,
  Calendar,
  Award,
  ChevronDown,
  ChevronUp,
  User,
  Archive
} from 'lucide-react';
import type { NewsArticle } from '@/types/news';
import { EntityTooltip } from '@/components/entity/EntityTooltip';

interface NewsTimelineItemProps {
  article: NewsArticle;
  onEntityClick?: (entity: string) => void;
}

/**
 * Timeline Item Component
 *
 * Design: Individual article entry in vertical timeline
 * - Timeline marker with connecting line
 * - Expandable card for full details
 * - Color-coded by credibility score
 * - Smooth expand/collapse animations
 */
export function NewsTimelineItem({ article, onEntityClick }: NewsTimelineItemProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  // Format date for display
  const formatDate = (dateString: string) => {
    if (!dateString) return 'Unknown date';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  // Get credibility tier and color
  const getCredibilityTier = (score: number) => {
    if (score >= 0.90) return { tier: 'high', color: 'bg-green-500', textColor: 'text-green-600 dark:text-green-400' };
    if (score >= 0.75) return { tier: 'medium', color: 'bg-blue-500', textColor: 'text-blue-600 dark:text-blue-400' };
    return { tier: 'low', color: 'bg-gray-500', textColor: 'text-gray-600 dark:text-gray-400' };
  };

  const credibility = getCredibilityTier(article.credibility_score);

  // Truncate text
  const truncateText = (text: string, maxLength: number) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength).trim() + '...';
  };

  return (
    <div className="relative flex gap-4 pb-8 group">
      {/* Timeline Marker & Line */}
      <div className="relative flex flex-col items-center">
        {/* Connecting Line */}
        <div className="absolute top-0 bottom-0 w-0.5 bg-border" style={{ left: '0.75rem' }} />

        {/* Marker Circle */}
        <div className={`relative z-10 w-6 h-6 rounded-full ${credibility.color} ring-4 ring-background flex items-center justify-center flex-shrink-0`}>
          <div className="w-2 h-2 rounded-full bg-white" />
        </div>
      </div>

      {/* Content Card */}
      <div className="flex-1 -mt-1">
        <Card className="hover:shadow-lg transition-all duration-200 group-hover:border-primary/50">
          <CardContent className="p-4 space-y-3">
            {/* Header Row */}
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 space-y-2">
                {/* Date */}
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Calendar className="h-4 w-4" />
                  <span className="font-medium">{formatDate(article.published_date)}</span>
                </div>

                {/* Title */}
                <Link
                  to={`/news/${article.id}`}
                  className="group/title"
                >
                  <h3 className="text-lg font-semibold leading-tight group-hover/title:text-primary transition-colors">
                    {article.title}
                  </h3>
                </Link>

                {/* Metadata */}
                <div className="flex flex-wrap items-center gap-2">
                  {/* Publication */}
                  <Badge variant="secondary" className="text-xs">
                    {article.publication}
                  </Badge>

                  {/* Author */}
                  {article.author && (
                    <div className="flex items-center gap-1 text-xs text-muted-foreground">
                      <User className="h-3 w-3" />
                      <span>{article.author}</span>
                    </div>
                  )}

                  {/* Credibility Score */}
                  <div className="flex items-center gap-1">
                    <Award className={`h-4 w-4 ${credibility.textColor}`} />
                    <span className={`text-xs font-medium ${credibility.textColor}`}>
                      {(article.credibility_score * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              </div>

              {/* Expand/Collapse Button */}
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsExpanded(!isExpanded)}
                className="flex-shrink-0"
              >
                {isExpanded ? (
                  <ChevronUp className="h-4 w-4" />
                ) : (
                  <ChevronDown className="h-4 w-4" />
                )}
              </Button>
            </div>

            {/* Excerpt (Always Visible) */}
            <p className="text-sm text-muted-foreground leading-relaxed">
              {truncateText(article.content_excerpt, isExpanded ? 500 : 150)}
            </p>

            {/* Entity Tags (Preview) */}
            {article.entities_mentioned.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {article.entities_mentioned.slice(0, isExpanded ? undefined : 3).map((entity) => {
                  const entityId = entity.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '');
                  return (
                    <EntityTooltip key={entity} entityId={entityId} entityName={entity}>
                      <Badge
                        variant="outline"
                        className="text-xs cursor-pointer hover:bg-accent transition-colors"
                        onClick={() => onEntityClick?.(entity)}
                      >
                        {entity}
                      </Badge>
                    </EntityTooltip>
                  );
                })}
                {!isExpanded && article.entities_mentioned.length > 3 && (
                  <Badge variant="outline" className="text-xs text-muted-foreground">
                    +{article.entities_mentioned.length - 3}
                  </Badge>
                )}
              </div>
            )}

            {/* Expanded Details */}
            {isExpanded && (
              <div className="space-y-3 pt-3 border-t animate-in fade-in slide-in-from-top-2">
                {/* Tags */}
                {article.tags.length > 0 && (
                  <div className="space-y-2">
                    <label className="text-xs font-medium text-muted-foreground">Tags</label>
                    <div className="flex flex-wrap gap-1.5">
                      {article.tags.map((tag) => (
                        <Badge key={tag} variant="secondary" className="text-xs">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex gap-2">
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

                {/* Additional Metadata */}
                <div className="flex flex-wrap gap-4 text-xs text-muted-foreground">
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
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
