import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Loader2, AlertCircle, Sparkles, Calendar, Cpu, Zap } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8081';

/**
 * AI Summary Response from backend
 */
interface AiSummaryResponse {
  document_id: string;
  summary: string;
  summary_generated_at: string;
  summary_model: string;
  word_count: number;
  from_cache: boolean;
}

/**
 * Error response structure
 */
interface ApiError {
  detail?: string;
  message?: string;
}

interface DocumentSummaryProps {
  documentId: string;
  onSummaryLoad?: (summary: string) => void;
  className?: string;
}

/**
 * DocumentSummary Component
 *
 * Displays AI-generated summaries for PDF documents.
 *
 * Design Decision: Fetch summary on mount for immediate display
 * - Provides instant value to users (summary loads faster than full PDF)
 * - Caching on backend ensures sub-second load times for cached summaries
 * - Falls back gracefully when summary unavailable
 *
 * Error Handling Strategy:
 * - 404: Document not found
 * - 422: Scanned PDF without OCR text
 * - 503: AI service unavailable
 * - Network errors: Clear connectivity messages
 *
 * Trade-offs:
 * - User Experience: Summary-first approach vs. traditional PDF-first
 * - Performance: Additional API call vs. combined endpoint (chose separation for flexibility)
 * - Cache Strategy: Backend handles caching (frontend stays simple)
 */
export function DocumentSummary({
  documentId,
  onSummaryLoad,
  className = '',
}: DocumentSummaryProps) {
  const [summary, setSummary] = useState<AiSummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [errorType, setErrorType] = useState<'not_found' | 'no_ocr' | 'service_unavailable' | 'network' | 'unknown'>('unknown');

  useEffect(() => {
    loadSummary();
  }, [documentId]);

  const loadSummary = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${API_BASE_URL}/api/documents/${documentId}/ai-summary`, {
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        // Parse error response
        let errorData: ApiError = {};
        try {
          errorData = await response.json();
        } catch {
          // Response not JSON
        }

        const errorDetail = errorData.detail || errorData.message || response.statusText;

        // Handle specific error codes
        if (response.status === 404) {
          setErrorType('not_found');
          setError('Document not found. Please check the document ID.');
        } else if (response.status === 422) {
          setErrorType('no_ocr');
          setError('This is a scanned document without OCR text. Please download the PDF to view it.');
        } else if (response.status === 503) {
          setErrorType('service_unavailable');
          setError('Unable to generate summary at this time. Please try again or download the PDF.');
        } else {
          setErrorType('unknown');
          setError(`Error loading summary: ${errorDetail}`);
        }
        return;
      }

      const data: AiSummaryResponse = await response.json();
      setSummary(data);

      // Notify parent component
      if (onSummaryLoad) {
        onSummaryLoad(data.summary);
      }
    } catch (err) {
      console.error('Failed to load AI summary:', err);

      // Network error detection
      if (err instanceof TypeError && (err.message.includes('Failed to fetch') || err.message.includes('NetworkError'))) {
        setErrorType('network');
        setError(`Cannot connect to backend server at ${API_BASE_URL}. Please ensure the backend is running.`);
      } else {
        setErrorType('unknown');
        setError('Unable to load summary. Please try downloading the PDF instead.');
      }
    } finally {
      setLoading(false);
    }
  };

  // Loading state
  if (loading) {
    return (
      <Card className={className}>
        <CardContent className="pt-6">
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground mr-3" />
            <div className="text-center">
              <p className="text-sm font-medium">Generating AI Summary...</p>
              <p className="text-xs text-muted-foreground mt-1">This may take 5-10 seconds</p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Error state
  if (error) {
    // Different variants for different error types
    const alertVariant = errorType === 'no_ocr' ? 'default' : 'destructive';

    return (
      <Alert variant={alertVariant} className={className}>
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>
          {errorType === 'not_found' && 'Document Not Found'}
          {errorType === 'no_ocr' && 'OCR Text Unavailable'}
          {errorType === 'service_unavailable' && 'Service Unavailable'}
          {errorType === 'network' && 'Connection Error'}
          {errorType === 'unknown' && 'Error Loading Summary'}
        </AlertTitle>
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  // Success state
  if (!summary) {
    return null;
  }

  const generatedDate = new Date(summary.summary_generated_at);
  const modelName = summary.summary_model.split('/').pop()?.split(':')[0] || summary.summary_model;

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-purple-500" />
            <CardTitle className="text-lg">AI-Generated Document Summary</CardTitle>
          </div>
          {summary.from_cache && (
            <Badge variant="outline" className="gap-1">
              <Zap className="h-3 w-3" />
              Cached
            </Badge>
          )}
        </div>
        <CardDescription>
          Auto-generated summary • {summary.word_count} words
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Summary Text */}
        <div className="prose prose-sm dark:prose-invert max-w-none">
          <p className="leading-relaxed text-foreground whitespace-pre-wrap">
            {summary.summary}
          </p>
        </div>

        {/* Metadata Footer */}
        <div className="flex flex-wrap items-center gap-3 pt-3 border-t text-xs text-muted-foreground">
          <div className="flex items-center gap-1">
            <Cpu className="h-3 w-3" />
            <span>Generated by {modelName}</span>
          </div>
          <div className="flex items-center gap-1">
            <Calendar className="h-3 w-3" />
            <span>
              {generatedDate.toLocaleDateString()} at {generatedDate.toLocaleTimeString()}
            </span>
          </div>
          {summary.from_cache && (
            <div className="flex items-center gap-1 text-green-600 dark:text-green-400">
              <Zap className="h-3 w-3" />
              <span>Instant retrieval</span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
