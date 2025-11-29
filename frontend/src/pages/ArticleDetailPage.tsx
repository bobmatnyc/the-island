import { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import {
  ExternalLink,
  Archive,
  Calendar,
  User,
  Award,
  ArrowLeft,
  Share2,
  Users,
  Clock,
  AlertCircle,
  Copy,
  Check,
} from 'lucide-react';
import { ArticleCard } from '@/components/news/ArticleCard';
import { newsApi } from '@/services/newsApi';
import type { NewsArticle } from '@/types/news';

export function ArticleDetailPage() {
  const { articleId } = useParams<{ articleId: string }>();
  const navigate = useNavigate();
  const [article, setArticle] = useState<NewsArticle | null>(null);
  const [similarArticles, setSimilarArticles] = useState<NewsArticle[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    async function loadArticle() {
      if (!articleId) {
        setError('Article ID is required');
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);

        // Load article and similar articles
        const [articleData, similarData] = await Promise.all([
          newsApi.getArticle(articleId),
          newsApi.getSimilarArticles(articleId, 5).catch(() => []),
        ]);

        setArticle(articleData);
        setSimilarArticles(similarData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load article');
        console.error('Error loading article:', err);
      } finally {
        setLoading(false);
      }
    }

    loadArticle();
  }, [articleId]);

  // Format date
  const formatDate = (dateString: string) => {
    if (!dateString) return 'Unknown date';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  // Get credibility color
  const getCredibilityColor = (score: number) => {
    if (score >= 0.90) return 'text-green-600 dark:text-green-400';
    if (score >= 0.75) return 'text-blue-600 dark:text-blue-400';
    return 'text-gray-600 dark:text-gray-400';
  };

  // Get credibility label
  const getCredibilityLabel = (score: number) => {
    if (score >= 0.90) return 'High Credibility';
    if (score >= 0.75) return 'Medium Credibility';
    return 'Lower Credibility';
  };

  // Copy link to clipboard
  const handleCopyLink = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy link:', err);
    }
  };

  // Share on Twitter
  const handleShareTwitter = () => {
    if (!article) return;
    const text = `${article.title} - The Epstein Archive`;
    const url = window.location.href;
    window.open(
      `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(url)}`,
      '_blank'
    );
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6 max-w-5xl space-y-6">
        <Button variant="ghost" onClick={() => navigate('/news')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to News
        </Button>

        <Card>
          <CardHeader className="space-y-4">
            <Skeleton className="h-10 w-3/4" />
            <Skeleton className="h-6 w-full" />
            <Skeleton className="h-4 w-1/2" />
          </CardHeader>
          <CardContent className="space-y-4">
            <Skeleton className="h-40 w-full" />
            <Skeleton className="h-20 w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error || !article) {
    return (
      <div className="container mx-auto p-6 max-w-5xl">
        <Button variant="ghost" onClick={() => navigate('/news')} className="mb-6">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to News
        </Button>

        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error || 'Article not found'}</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 max-w-5xl space-y-6">
      {/* Back Button */}
      <Button variant="ghost" onClick={() => navigate('/news')}>
        <ArrowLeft className="h-4 w-4 mr-2" />
        Back to News
      </Button>

      {/* Article Content */}
      <Card>
        <CardHeader className="space-y-6">
          {/* Title */}
          <h1 className="text-3xl md:text-4xl font-bold leading-tight">
            {article.title}
          </h1>

          {/* Metadata Row */}
          <div className="flex flex-wrap items-center gap-4 text-sm">
            {/* Publication */}
            <Badge variant="secondary" className="text-base px-3 py-1">
              {article.publication}
            </Badge>

            {/* Author */}
            {article.author && (
              <div className="flex items-center gap-2 text-muted-foreground">
                <User className="h-4 w-4" />
                <span>{article.author}</span>
              </div>
            )}

            {/* Date */}
            <div className="flex items-center gap-2 text-muted-foreground">
              <Calendar className="h-4 w-4" />
              <span>{formatDate(article.published_date)}</span>
            </div>

            {/* Reading Time */}
            <div className="flex items-center gap-2 text-muted-foreground">
              <Clock className="h-4 w-4" />
              <span>{Math.ceil(article.word_count / 200)} min read</span>
            </div>
          </div>

          {/* Credibility Score */}
          <div className="flex items-center gap-3 p-4 bg-muted/50 rounded-lg">
            <Award className={`h-5 w-5 ${getCredibilityColor(article.credibility_score)}`} />
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <span className="font-semibold">
                  {getCredibilityLabel(article.credibility_score)}
                </span>
                <Badge variant="outline" className={getCredibilityColor(article.credibility_score)}>
                  {(article.credibility_score * 100).toFixed(0)}%
                </Badge>
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Based on source reputation and editorial standards
              </p>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Full Excerpt */}
          <div className="prose prose-slate dark:prose-invert max-w-none">
            <p className="text-lg leading-relaxed">{article.content_excerpt}</p>
            {article.access_type === 'paywall' && (
              <p className="text-sm text-muted-foreground italic mt-4">
                Full article may be behind a paywall
              </p>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap gap-3 pt-4 border-t">
            {article.url && (
              <Button asChild size="lg" className="flex-1 min-w-[200px]">
                <a
                  href={article.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center justify-center gap-2"
                >
                  <ExternalLink className="h-5 w-5" />
                  Read Original Article
                </a>
              </Button>
            )}

            {article.archive_url && (
              <Button asChild variant="outline" size="lg">
                <a
                  href={article.archive_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2"
                >
                  <Archive className="h-5 w-5" />
                  View on Archive.org
                </a>
              </Button>
            )}
          </div>

          {/* Share Buttons */}
          <div className="flex gap-2 pt-2">
            <Button variant="outline" size="sm" onClick={handleCopyLink}>
              {copied ? (
                <>
                  <Check className="h-4 w-4 mr-2" />
                  Copied!
                </>
              ) : (
                <>
                  <Copy className="h-4 w-4 mr-2" />
                  Copy Link
                </>
              )}
            </Button>
            <Button variant="outline" size="sm" onClick={handleShareTwitter}>
              <Share2 className="h-4 w-4 mr-2" />
              Share on X
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Entity Mentions */}
      {article.entities_mentioned.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              Entity Mentions
            </CardTitle>
            <CardDescription>
              People and organizations mentioned in this article
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {article.entities_mentioned.map((entity) => (
                <Link key={entity} to={`/entities?search=${encodeURIComponent(entity)}`}>
                  <Badge
                    variant="outline"
                    className="cursor-pointer hover:bg-accent text-base px-3 py-1"
                  >
                    {entity}
                    {article.entity_mention_counts[entity] > 1 && (
                      <span className="ml-2 text-xs text-muted-foreground">
                        ({article.entity_mention_counts[entity]})
                      </span>
                    )}
                  </Badge>
                </Link>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tags */}
      {article.tags.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Topics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {article.tags.map((tag) => (
                <Badge key={tag} variant="secondary" className="text-sm px-3 py-1">
                  {tag}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Similar Articles */}
      {similarArticles.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-2xl font-bold">Similar Articles</h2>
          <div className="space-y-4">
            {similarArticles.map((similarArticle) => (
              <ArticleCard key={similarArticle.id} article={similarArticle} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
