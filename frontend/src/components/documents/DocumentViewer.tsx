import { useEffect, useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  FileText,
  X,
  Search,
  Copy,
  Download,
  Users,
  ZoomIn,
  ZoomOut,
  AlertCircle,
  Loader2,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { api, type Document } from '@/lib/api';
import { formatFileSize, formatClassification, formatSource } from '@/lib/utils';
import { Document as PDFDocument, Page as PDFPage, pdfjs } from 'react-pdf';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

// Configure PDF.js worker - use local worker for Vite compatibility
import workerSrc from 'pdfjs-dist/build/pdf.worker.min.mjs?url';
pdfjs.GlobalWorkerOptions.workerSrc = workerSrc;

interface DocumentViewerProps {
  document: Document | null;
  isOpen: boolean;
  onClose: () => void;
  onEntityClick?: (entityName: string) => void;
  standalone?: boolean; // New prop for non-modal rendering
}

export function DocumentViewer({
  document,
  isOpen,
  onClose,
  onEntityClick,
  standalone = false, // Default to modal mode
}: DocumentViewerProps) {
  const [content, setContent] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [fontSize, setFontSize] = useState(14);
  const [useMonospace, setUseMonospace] = useState(false);

  // PDF viewer state
  const [numPages, setNumPages] = useState<number | null>(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [pdfScale, setPdfScale] = useState(1.0);
  const [useFallbackViewer, setUseFallbackViewer] = useState(false);

  // Load document content when document changes
  useEffect(() => {
    if (!document || !isOpen) {
      setContent(null);
      setError(null);
      return;
    }

    loadDocumentContent();
  }, [document?.id, isOpen]);

  const loadDocumentContent = async () => {
    if (!document) return;

    try {
      setLoading(true);
      setError(null);

      const response = await api.getDocumentById(document.id);
      setContent(response.content || null);
    } catch (err) {
      console.error('Failed to load document content:', err);
      setError('Failed to load document content. The full text may not be available.');
      setContent(null);
    } finally {
      setLoading(false);
    }
  };

  const handleCopyToClipboard = () => {
    if (content) {
      navigator.clipboard.writeText(content);
    }
  };

  const handleDownload = () => {
    if (!document) return;
    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8081';
    const downloadUrl = `${API_BASE_URL}/api/documents/${document.id}/download`;
    window.open(downloadUrl, '_blank');
  };

  const highlightEntities = (text: string): React.ReactNode => {
    if (!document || !text) return text;

    const entities = document.entities_mentioned;
    if (entities.length === 0) return text;

    // Split text into paragraphs first
    const paragraphs = text.split('\n');

    return paragraphs.map((paragraph, pIdx) => {
      if (!paragraph.trim()) {
        return <br key={`br-${pIdx}`} />;
      }

      let highlightedText: React.ReactNode[] = [paragraph];

      // Highlight each entity
      entities.forEach((entity) => {
        const newHighlightedText: React.ReactNode[] = [];

        highlightedText.forEach((segment, segIdx) => {
          if (typeof segment === 'string') {
            // Case-insensitive search for entity names
            const regex = new RegExp(`\\b(${entity.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})\\b`, 'gi');
            const parts = segment.split(regex);

            parts.forEach((part, partIdx) => {
              if (part.toLowerCase() === entity.toLowerCase()) {
                // Entity match - make it clickable
                newHighlightedText.push(
                  <button
                    key={`entity-${pIdx}-${segIdx}-${partIdx}`}
                    onClick={() => onEntityClick?.(entity)}
                    className="bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100 px-1 rounded hover:bg-blue-200 dark:hover:bg-blue-800 transition-colors cursor-pointer font-medium"
                    title={`Click to view ${entity}`}
                  >
                    {part}
                  </button>
                );
              } else if (part) {
                newHighlightedText.push(
                  <span key={`text-${pIdx}-${segIdx}-${partIdx}`}>{part}</span>
                );
              }
            });
          } else {
            newHighlightedText.push(segment);
          }
        });

        highlightedText = newHighlightedText;
      });

      return (
        <p key={`p-${pIdx}`} className="mb-2">
          {highlightedText}
        </p>
      );
    });
  };

  const highlightSearchTerm = (text: React.ReactNode): React.ReactNode => {
    if (!searchTerm.trim() || typeof text === 'string') {
      return text;
    }

    // For now, search highlighting is basic - can be enhanced later
    return text;
  };

  const onDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages);
    setPageNumber(1);
  };

  const onDocumentLoadError = (error: Error) => {
    console.error('PDF load error:', error);
    setError('Failed to load PDF document. The file may be corrupted or too large.');
    // Automatically try fallback viewer
    setUseFallbackViewer(true);
  };

  const renderContent = () => {
    if (loading) {
      return (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          <span className="ml-2 text-muted-foreground">Loading document content...</span>
        </div>
      );
    }

    if (error) {
      return (
        <div className="flex items-center gap-2 p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg border border-yellow-200 dark:border-yellow-800">
          <AlertCircle className="h-5 w-5 text-yellow-600 dark:text-yellow-500" />
          <div>
            <p className="font-medium text-yellow-900 dark:text-yellow-100">{error}</p>
            <p className="text-sm text-yellow-700 dark:text-yellow-300 mt-1">
              Try using the RAG search to find specific information from this document.
            </p>
          </div>
        </div>
      );
    }

    // Check if document is PDF and should use PDF viewer
    const isPDF = document?.doc_type === 'pdf' || document?.filename?.endsWith('.pdf');

    if (isPDF) {
      const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8081';
      // Use /view endpoint for inline PDF display (not /download which forces download)
      const pdfUrl = `${API_BASE_URL}/api/documents/${document?.id}/view`;

      // Use iframe fallback if react-pdf fails or user requests it
      if (useFallbackViewer) {
        return (
          <div className="flex flex-col gap-4 w-full h-full">
            <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
              <span className="text-sm text-muted-foreground">
                Using browser PDF viewer
              </span>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setUseFallbackViewer(false);
                    setError(null);
                  }}
                >
                  Try Enhanced Viewer
                </Button>
                <Button variant="outline" size="sm" onClick={handleDownload}>
                  <Download className="h-4 w-4 mr-1" />
                  Download PDF
                </Button>
              </div>
            </div>
            <iframe
              src={`${pdfUrl}#toolbar=1&navpanes=0`}
              className="w-full h-[600px] border rounded-lg"
              title={`PDF Viewer: ${document?.filename}`}
              allow="cross-origin-isolated"
            />
          </div>
        );
      }

      return (
        <div className="flex flex-col items-center gap-4">
          <PDFDocument
            file={pdfUrl}
            onLoadSuccess={onDocumentLoadSuccess}
            onLoadError={onDocumentLoadError}
            loading={
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                <span className="ml-2 text-muted-foreground">Loading PDF...</span>
              </div>
            }
            options={{
              // Disable text layer for better performance with large PDFs
              disableStream: false,
              disableAutoFetch: false,
            }}
          >
            <PDFPage
              pageNumber={pageNumber}
              scale={pdfScale}
              renderTextLayer={true}
              renderAnnotationLayer={true}
            />
          </PDFDocument>

          {/* PDF Controls */}
          {numPages && (
            <div className="flex items-center gap-4 p-3 bg-muted rounded-lg">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPageNumber((p) => Math.max(1, p - 1))}
                disabled={pageNumber <= 1}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>

              <span className="text-sm">
                Page {pageNumber} of {numPages}
              </span>

              <Button
                variant="outline"
                size="sm"
                onClick={() => setPageNumber((p) => Math.min(numPages, p + 1))}
                disabled={pageNumber >= numPages}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>

              <div className="border-l pl-4 ml-2 flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPdfScale((s) => Math.max(0.5, s - 0.25))}
                  title="Zoom out"
                >
                  <ZoomOut className="h-4 w-4" />
                </Button>
                <span className="text-sm min-w-[4rem] text-center">
                  {Math.round(pdfScale * 100)}%
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPdfScale((s) => Math.min(3, s + 0.25))}
                  title="Zoom in"
                >
                  <ZoomIn className="h-4 w-4" />
                </Button>
              </div>

              <div className="border-l pl-4 ml-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setUseFallbackViewer(true)}
                  title="Use browser PDF viewer instead"
                >
                  Browser Viewer
                </Button>
              </div>
            </div>
          )}
        </div>
      );
    }

    // Text content view (for markdown files)
    if (!content) {
      return (
        <div className="text-center py-12 text-muted-foreground">
          <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p>No content available for this document.</p>
          <p className="text-sm mt-2">
            {isPDF
              ? 'PDF viewer failed to load. Try downloading the file instead.'
              : 'Use RAG search to find relevant excerpts.'}
          </p>
        </div>
      );
    }

    const highlighted = highlightEntities(content);

    return (
      <div
        className={`prose dark:prose-invert max-w-none ${
          useMonospace ? 'font-mono' : ''
        }`}
        style={{ fontSize: `${fontSize}px` }}
      >
        {highlightSearchTerm(highlighted)}
      </div>
    );
  };

  if (!document) return null;

  // Standalone mode: render without Dialog wrapper
  if (standalone) {
    return (
      <div className="max-w-5xl mx-auto">
        {/* All the same content from DialogContent but without Dialog wrapper */}
        <div className="flex flex-col border rounded-lg bg-card">
          {/* Header */}
          <div className="p-6 pb-4 border-b">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <h2 className="text-xl font-semibold leading-tight break-words">
                  {document.filename}
                </h2>
                <div className="mt-2">
                  <div className="flex flex-wrap gap-2">
                    <Badge variant="outline" className="text-xs">
                      {formatClassification(document.classification)}
                    </Badge>
                    <Badge variant="secondary" className="text-xs">
                      {formatSource(document.source)}
                    </Badge>
                    <Badge variant="outline" className="text-xs">
                      {document.doc_type.toUpperCase()}
                    </Badge>
                    <Badge variant="outline" className="text-xs">
                      {formatFileSize(document.file_size)}
                    </Badge>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Document Summary */}
          {document.summary && (
            <div className="px-6 py-4 border-b bg-blue-50 dark:bg-blue-950/20">
              <div className="flex items-start gap-2">
                <FileText className="h-4 w-4 mt-0.5 text-blue-600 dark:text-blue-400 shrink-0" />
                <div className="flex-1">
                  <div className="text-sm font-medium text-blue-900 dark:text-blue-100 mb-1">
                    Document Summary
                  </div>
                  <p className="text-sm text-blue-800 dark:text-blue-200 leading-relaxed">
                    {document.summary}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Toolbar */}
          <div className="px-6 py-3 border-b bg-muted/30 space-y-3">
            {/* Search Bar */}
            <div className="flex items-center gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  type="text"
                  placeholder="Search within document..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
              <div className="flex items-center gap-1">
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => setFontSize(Math.max(10, fontSize - 2))}
                  title="Decrease font size"
                >
                  <ZoomOut className="h-4 w-4" />
                </Button>
                <span className="text-xs text-muted-foreground px-2">{fontSize}px</span>
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => setFontSize(Math.min(24, fontSize + 2))}
                  title="Increase font size"
                >
                  <ZoomIn className="h-4 w-4" />
                </Button>
              </div>
              <Button
                variant={useMonospace ? 'default' : 'outline'}
                size="sm"
                onClick={() => setUseMonospace(!useMonospace)}
              >
                <code className="text-xs">Aa</code>
              </Button>
              <Button variant="outline" size="sm" onClick={handleCopyToClipboard}>
                <Copy className="h-4 w-4 mr-1" />
                Copy
              </Button>
              <Button variant="outline" size="sm" onClick={handleDownload}>
                <Download className="h-4 w-4 mr-1" />
                Download
              </Button>
            </div>

            {/* Entity Badges */}
            {document.entities_mentioned.length > 0 && (
              <div className="flex items-start gap-2">
                <div className="flex items-center gap-1 text-sm text-muted-foreground shrink-0">
                  <Users className="h-3 w-3" />
                  <span className="font-medium">Entities ({document.entities_mentioned.length}):</span>
                </div>
                <div className="flex flex-wrap gap-1">
                  {document.entities_mentioned.map((entity) => (
                    <Badge
                      key={entity}
                      variant="secondary"
                      className="text-xs cursor-pointer hover:bg-primary hover:text-primary-foreground transition-colors"
                      onClick={() => onEntityClick?.(entity)}
                    >
                      {entity}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Content with ScrollArea */}
          <ScrollArea className="flex-1 px-6 py-4 max-h-[calc(100vh-300px)]">
            {renderContent()}
          </ScrollArea>

          {/* Footer */}
          {document.date_extracted && (
            <div className="px-6 py-3 border-t bg-muted/30 text-xs text-muted-foreground">
              Extracted: {new Date(document.date_extracted).toLocaleDateString()}
              {document.classification_confidence > 0 && (
                <span className="ml-4">
                  Classification confidence: {(document.classification_confidence * 100).toFixed(0)}%
                </span>
              )}
            </div>
          )}
        </div>
      </div>
    );
  }

  // Modal mode: existing Dialog implementation
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-5xl max-h-[90vh] flex flex-col p-0">
        {/* Header */}
        <DialogHeader className="p-6 pb-4 border-b">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              <DialogTitle className="text-xl leading-tight break-words">
                {document.filename}
              </DialogTitle>
              <DialogDescription className="mt-2">
                <div className="flex flex-wrap gap-2">
                  <Badge variant="outline" className="text-xs">
                    {formatClassification(document.classification)}
                  </Badge>
                  <Badge variant="secondary" className="text-xs">
                    {formatSource(document.source)}
                  </Badge>
                  <Badge variant="outline" className="text-xs">
                    {document.doc_type.toUpperCase()}
                  </Badge>
                  <Badge variant="outline" className="text-xs">
                    {formatFileSize(document.file_size)}
                  </Badge>
                </div>
              </DialogDescription>
            </div>
            <Button variant="ghost" size="icon" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>
        </DialogHeader>

        {/* Document Summary */}
        {document.summary && (
          <div className="px-6 py-4 border-b bg-blue-50 dark:bg-blue-950/20">
            <div className="flex items-start gap-2">
              <FileText className="h-4 w-4 mt-0.5 text-blue-600 dark:text-blue-400 shrink-0" />
              <div className="flex-1">
                <div className="text-sm font-medium text-blue-900 dark:text-blue-100 mb-1">
                  Document Summary
                </div>
                <p className="text-sm text-blue-800 dark:text-blue-200 leading-relaxed">
                  {document.summary}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Toolbar */}
        <div className="px-6 py-3 border-b bg-muted/30 space-y-3">
          {/* Search Bar */}
          <div className="flex items-center gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                type="text"
                placeholder="Search within document..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <div className="flex items-center gap-1">
              <Button
                variant="outline"
                size="icon"
                onClick={() => setFontSize(Math.max(10, fontSize - 2))}
                title="Decrease font size"
              >
                <ZoomOut className="h-4 w-4" />
              </Button>
              <span className="text-xs text-muted-foreground px-2">{fontSize}px</span>
              <Button
                variant="outline"
                size="icon"
                onClick={() => setFontSize(Math.min(24, fontSize + 2))}
                title="Increase font size"
              >
                <ZoomIn className="h-4 w-4" />
              </Button>
            </div>
            <Button
              variant={useMonospace ? 'default' : 'outline'}
              size="sm"
              onClick={() => setUseMonospace(!useMonospace)}
            >
              <code className="text-xs">Aa</code>
            </Button>
            <Button variant="outline" size="sm" onClick={handleCopyToClipboard}>
              <Copy className="h-4 w-4 mr-1" />
              Copy
            </Button>
            <Button variant="outline" size="sm" onClick={handleDownload}>
              <Download className="h-4 w-4 mr-1" />
              Download
            </Button>
          </div>

          {/* Entity Badges */}
          {document.entities_mentioned.length > 0 && (
            <div className="flex items-start gap-2">
              <div className="flex items-center gap-1 text-sm text-muted-foreground shrink-0">
                <Users className="h-3 w-3" />
                <span className="font-medium">Entities ({document.entities_mentioned.length}):</span>
              </div>
              <div className="flex flex-wrap gap-1">
                {document.entities_mentioned.map((entity) => (
                  <Badge
                    key={entity}
                    variant="secondary"
                    className="text-xs cursor-pointer hover:bg-primary hover:text-primary-foreground transition-colors"
                    onClick={() => onEntityClick?.(entity)}
                  >
                    {entity}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Content */}
        <ScrollArea className="flex-1 px-6 py-4">
          {renderContent()}
        </ScrollArea>

        {/* Footer */}
        {document.date_extracted && (
          <div className="px-6 py-3 border-t bg-muted/30 text-xs text-muted-foreground">
            Extracted: {new Date(document.date_extracted).toLocaleDateString()}
            {document.classification_confidence > 0 && (
              <span className="ml-4">
                Classification confidence: {(document.classification_confidence * 100).toFixed(0)}%
              </span>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
