import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, TrendingUp, Users } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';

/**
 * RelatedEntities Component
 *
 * Displays entities similar to the current entity using semantic similarity search.
 * Powered by entity biography embeddings in ChromaDB vector store.
 *
 * Features:
 * - Semantic similarity ranking (0-1 scale)
 * - Category grouping
 * - Biography excerpts
 * - Navigation to related entities
 * - Expandable category clusters
 *
 * API Endpoint: GET /api/entities/{entity_id}/similar
 *
 * Design Rationale:
 * - Uses semantic similarity vs. explicit connections for entity discovery
 * - Complements EntityConnections component (explicit graph connections)
 * - Helps users discover entities with similar roles/activities
 * - Useful for validating entity categorization
 */

interface SimilarEntity {
  entity_id: string;
  display_name: string;
  similarity_score: number;
  primary_category: string;
  quality_score: number;
  word_count: number;
  biography_excerpt: string;
}

interface RelatedEntitiesProps {
  entityId: string;
  limit?: number;
  minSimilarity?: number;
  showCategories?: boolean;
}

export function RelatedEntities({
  entityId,
  limit = 8,
  minSimilarity = 0.0,
  showCategories = false,
}: RelatedEntitiesProps) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [similarEntities, setSimilarEntities] = useState<SimilarEntity[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());

  // Fetch similar entities
  useEffect(() => {
    const fetchSimilarEntities = async () => {
      try {
        setLoading(true);
        setError(null);

        const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8081';
        const url = `${API_BASE_URL}/api/entities/${entityId}/similar?limit=${limit}&min_similarity=${minSimilarity}`;

        const response = await fetch(url, {
          headers: {
            'Content-Type': 'application/json',
          },
        });

        if (!response.ok) {
          if (response.status === 404) {
            setError('Entity not found in similarity index');
            setSimilarEntities([]);
            return;
          }
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();

        if (data && data.similar_entities) {
          setSimilarEntities(data.similar_entities);
        } else {
          setSimilarEntities([]);
        }
      } catch (err: any) {
        console.error('Error fetching similar entities:', err);
        setError('Failed to load related entities');
        setSimilarEntities([]);
      } finally {
        setLoading(false);
      }
    };

    fetchSimilarEntities();
  }, [entityId, limit, minSimilarity]);

  // Navigate to entity
  const handleEntityClick = (clickedEntityId: string) => {
    navigate(`/entities/${clickedEntityId}`);
  };

  // Toggle category expansion
  const toggleCategory = (category: string) => {
    setExpandedCategories((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(category)) {
        newSet.delete(category);
      } else {
        newSet.add(category);
      }
      return newSet;
    });
  };

  // Group entities by category
  const groupedByCategory = similarEntities.reduce((acc, entity) => {
    const category = entity.primary_category || 'unknown';
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(entity);
    return acc;
  }, {} as Record<string, SimilarEntity[]>);

  // Get similarity badge variant
  const getSimilarityVariant = (score: number): 'default' | 'secondary' | 'outline' => {
    if (score >= 0.6) return 'default';
    if (score >= 0.4) return 'secondary';
    return 'outline';
  };

  // Loading state
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5" />
            Related Entities
          </CardTitle>
          <CardDescription>Finding similar entities...</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="space-y-2">
              <Skeleton className="h-5 w-3/4" />
              <Skeleton className="h-4 w-full" />
            </div>
          ))}
        </CardContent>
      </Card>
    );
  }

  // Error state
  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5" />
            Related Entities
          </CardTitle>
          <CardDescription className="text-destructive">{error}</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  // Empty state
  if (similarEntities.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5" />
            Related Entities
          </CardTitle>
          <CardDescription>No similar entities found</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  // Show category grouping
  if (showCategories) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Related Entities by Category
          </CardTitle>
          <CardDescription>
            {Object.keys(groupedByCategory).length} categories • {similarEntities.length} entities
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {Object.entries(groupedByCategory).map(([category, entities]) => (
            <div key={category} className="space-y-2">
              <Button
                variant="ghost"
                className="w-full justify-between p-0 h-auto hover:bg-transparent"
                onClick={() => toggleCategory(category)}
              >
                <div className="flex items-center gap-2">
                  <Badge variant="secondary">{category}</Badge>
                  <span className="text-sm text-muted-foreground">
                    {entities.length} {entities.length === 1 ? 'entity' : 'entities'}
                  </span>
                </div>
                <TrendingUp className="h-4 w-4" />
              </Button>

              {expandedCategories.has(category) && (
                <div className="ml-4 space-y-3 border-l-2 border-border pl-4">
                  {entities.slice(0, 5).map((entity) => (
                    <div
                      key={entity.entity_id}
                      className="cursor-pointer hover:bg-accent rounded-lg p-2 transition-colors"
                      onClick={() => handleEntityClick(entity.entity_id)}
                    >
                      <div className="flex items-start justify-between gap-2 mb-1">
                        <h4 className="font-medium text-sm">{entity.display_name}</h4>
                        <Badge variant={getSimilarityVariant(entity.similarity_score)}>
                          {(entity.similarity_score * 100).toFixed(0)}%
                        </Badge>
                      </div>
                      {entity.biography_excerpt && (
                        <p className="text-xs text-muted-foreground line-clamp-2">
                          {entity.biography_excerpt}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </CardContent>
      </Card>
    );
  }

  // Default list view
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="h-5 w-5" />
          Related Entities
        </CardTitle>
        <CardDescription>
          {similarEntities.length} similar {similarEntities.length === 1 ? 'entity' : 'entities'} found
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {similarEntities.map((entity) => (
          <div
            key={entity.entity_id}
            className="cursor-pointer hover:bg-accent rounded-lg p-3 transition-colors border border-border"
            onClick={() => handleEntityClick(entity.entity_id)}
          >
            <div className="flex items-start justify-between gap-2 mb-2">
              <div className="flex-1 min-w-0">
                <h4 className="font-medium text-sm truncate">{entity.display_name}</h4>
                <div className="flex items-center gap-2 mt-1">
                  <Badge variant="outline" className="text-xs">
                    {entity.primary_category}
                  </Badge>
                  <Badge variant={getSimilarityVariant(entity.similarity_score)} className="text-xs">
                    {(entity.similarity_score * 100).toFixed(0)}% similar
                  </Badge>
                </div>
              </div>
            </div>

            {entity.biography_excerpt && (
              <p className="text-xs text-muted-foreground line-clamp-2 mt-2">
                {entity.biography_excerpt}
              </p>
            )}
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
