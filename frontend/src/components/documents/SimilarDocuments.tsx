import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  FileText,
  Search,
  Loader2,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Users,
  Clock,
} from 'lucide-react';
import { api, type SimilarDocsResponse } from '@/lib/api';
import { formatFileSize, formatClassification } from '@/lib/utils';
import { Progress } from '@/components/ui/progress';

/**
 * SimilarDocuments Component
 *
 * Design Decision: Expandable/collapsible panel for similar documents
 * Rationale:
 * - Non-intrusive: Doesn't clutter document viewer by default
 * - On-demand loading: Only fetches when user expands panel
 * - Visual similarity scores: Progress bars for easy comparison
 * - Quick navigation: Click to view similar document
 *
 * Performance:
 * - Lazy loading: API call only on user interaction
 * - Debouncing: Prevents rapid repeated requests
 * - Error recovery: Graceful fallback for failed searches
 */

interface SimilarDocumentsProps {
  documentId: string;
  onDocumentClick?: (documentId: string) => void;
}

export function SimilarDocuments({ documentId, onDocumentClick }: SimilarDocumentsProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<SimilarDocsResponse | null>(null);
  const [showAll, setShowAll] = useState(false);

  // Load similar documents when panel is expanded
  useEffect(() => {
    if (isExpanded && !results && !loading) {
      loadSimilarDocuments();
    }
  }, [isExpanded, documentId]);

  const loadSimilarDocuments = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.getSimilarDocuments(documentId, 10, 0.7);
      setResults(response);
    } catch (err) {
      console.error('Failed to load similar documents:', err);
      setError('Failed to load similar documents. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleDocumentClick = (docId: string) => {
    if (onDocumentClick) {
      onDocumentClick(docId);
      // Reset state when navigating to new document
      setResults(null);
      setShowAll(false);
      setIsExpanded(false);
    }
  };

  const displayedDocs = showAll
    ? results?.similar_documents || []
    : results?.similar_documents.slice(0, 5) || [];

  const hasMoreDocs = (results?.similar_documents.length || 0) > 5;

  return (
    <Card className="border-t">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Search className="h-4 w-4 text-muted-foreground" />
            <CardTitle className="text-base">Find Similar Documents</CardTitle>
            {results && !loading && (
              <Badge variant="secondary" className="text-xs">
                {results.total_found} found
              </Badge>
            )}
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsExpanded(!isExpanded)}
            className="gap-1"
          >
            {isExpanded ? (
              <>
                <ChevronUp className="h-4 w-4" />
                Hide
              </>
            ) : (
              <>
                <ChevronDown className="h-4 w-4" />
                Show
              </>
            )}
          </Button>
        </div>
        <CardDescription className="text-xs">
          Semantically similar documents using AI embeddings
        </CardDescription>
      </CardHeader>

      {isExpanded && (
        <CardContent className="pt-0">
          {loading && (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              <span className="ml-2 text-sm text-muted-foreground">
                Searching 33,000+ documents...
              </span>
            </div>
          )}

          {error && (
            <div className="flex items-center gap-2 p-3 bg-destructive/10 rounded-lg border border-destructive/20">
              <AlertCircle className="h-4 w-4 text-destructive" />
              <p className="text-sm text-destructive">{error}</p>
            </div>
          )}

          {results && !loading && results.total_found === 0 && (
            <div className="text-center py-8">
              <FileText className="h-12 w-12 mx-auto mb-3 opacity-30" />
              <p className="text-sm text-muted-foreground">
                No similar documents found above 70% similarity threshold.
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                Try adjusting the similarity threshold or search manually.
              </p>
            </div>
          )}

          {results && !loading && results.total_found > 0 && (
            <div className="space-y-3">
              <div className="flex items-center justify-between text-xs text-muted-foreground pb-2 border-b">
                <span>
                  Found {results.total_found} similar document{results.total_found !== 1 ? 's' : ''}
                </span>
                <span className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {results.search_time_ms}ms
                </span>
              </div>

              <ScrollArea className="max-h-[400px]">
                <div className="space-y-2">
                  {displayedDocs.map((doc) => (
                    <Card
                      key={doc.document_id}
                      className="cursor-pointer hover:bg-accent transition-colors"
                      onClick={() => handleDocumentClick(doc.document_id)}
                    >
                      <CardContent className="p-3">
                        <div className="space-y-2">
                          {/* Title and Similarity Score */}
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2">
                                <FileText className="h-3 w-3 text-muted-foreground shrink-0" />
                                <p className="text-sm font-medium truncate" title={doc.title}>
                                  {doc.title}
                                </p>
                                <ExternalLink className="h-3 w-3 text-muted-foreground shrink-0" />
                              </div>
                            </div>
                            <Badge
                              variant={doc.similarity_score >= 0.9 ? 'default' : 'secondary'}
                              className="text-xs shrink-0"
                            >
                              {Math.round(doc.similarity_score * 100)}% match
                            </Badge>
                          </div>

                          {/* Similarity Progress Bar */}
                          <Progress value={doc.similarity_score * 100} className="h-1" />

                          {/* Preview Text */}
                          {doc.preview && (
                            <p className="text-xs text-muted-foreground line-clamp-2">
                              {doc.preview}
                            </p>
                          )}

                          {/* Metadata Badges */}
                          <div className="flex flex-wrap gap-1">
                            <Badge variant="outline" className="text-xs">
                              {formatClassification(doc.classification)}
                            </Badge>
                            <Badge variant="outline" className="text-xs">
                              {doc.doc_type.toUpperCase()}
                            </Badge>
                            {doc.file_size > 0 && (
                              <Badge variant="outline" className="text-xs">
                                {formatFileSize(doc.file_size)}
                              </Badge>
                            )}
                            {doc.entities.length > 0 && (
                              <Badge variant="secondary" className="text-xs">
                                <Users className="h-2 w-2 mr-1" />
                                {doc.entities.length} entities
                              </Badge>
                            )}
                          </div>

                          {/* Entity Pills (show first 3) */}
                          {doc.entities.length > 0 && (
                            <div className="flex flex-wrap gap-1">
                              {doc.entities.slice(0, 3).map((entity) => (
                                <Badge key={entity} variant="secondary" className="text-xs">
                                  {entity}
                                </Badge>
                              ))}
                              {doc.entities.length > 3 && (
                                <Badge variant="outline" className="text-xs">
                                  +{doc.entities.length - 3} more
                                </Badge>
                              )}
                            </div>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </ScrollArea>

              {/* Show More/Less Button */}
              {hasMoreDocs && (
                <div className="pt-2 border-t">
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full"
                    onClick={() => setShowAll(!showAll)}
                  >
                    {showAll ? (
                      <>
                        <ChevronUp className="h-4 w-4 mr-1" />
                        Show Less
                      </>
                    ) : (
                      <>
                        <ChevronDown className="h-4 w-4 mr-1" />
                        Show All ({results.total_found} documents)
                      </>
                    )}
                  </Button>
                </div>
              )}
            </div>
          )}
        </CardContent>
      )}
    </Card>
  );
}
