import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Loader2, AlertCircle, Download, Eye } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { api, type Document } from '@/lib/api';
import { DocumentViewer } from '@/components/documents/DocumentViewer';
import { DocumentSummary } from '@/components/documents/DocumentSummary';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8081';

/**
 * DocumentDetail Page
 *
 * Displays AI-generated summary first, then download and optional PDF viewer.
 *
 * Design Decision: Summary-first approach for better UX
 * - AI summary loads faster than full PDF rendering
 * - Users get value immediately (200-300 word overview)
 * - Download option prominently displayed
 * - PDF viewer collapsed by default (experimental feature)
 *
 * GUID Migration Limitation:
 * - Entity navigation uses name-based URLs: /entities/{encodedName}
 * - Document entity references only provide entity names, not full objects with GUIDs
 * - Backend EntityDetail route supports name-based lookup for backward compatibility
 * - Future Enhancement: Backend should include entity IDs/GUIDs in document entity data
 *   to enable proper GUID-based navigation: /entities/{guid}/{name-slug}
 *
 * Navigation Strategy:
 * - handleEntityClick: Navigates using URL-encoded entity name
 * - Backend resolves name to entity and redirects if needed
 * - Maintains backward compatibility with existing document data structure
 */
export function DocumentDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [document, setDocument] = useState<Document | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showPdfViewer, setShowPdfViewer] = useState(false);

  useEffect(() => {
    if (id) {
      loadDocument(id);
    }
  }, [id]);

  const loadDocument = async (docId: string) => {
    try {
      setLoading(true);
      setError(null);
      // api.getDocumentById returns { document: Document, content: string | null }
      const response = await api.getDocumentById(docId);
      setDocument(response.document);
    } catch (err) {
      console.error('Failed to load document:', err);
      setError('Document not found');
    } finally {
      setLoading(false);
    }
  };

  const handleEntityClick = (entityName: string) => {
    // Navigate to entity detail page
    navigate(`/entities/${encodeURIComponent(entityName)}`);
  };

  const handleBack = () => {
    navigate(-1); // Go back to previous page
  };

  const handleDownload = () => {
    if (!id) return;
    const downloadUrl = `${API_BASE_URL}/api/documents/${id}/download`;
    window.open(downloadUrl, '_blank');
  };

  // Determine if PDF viewer should be available (small files only)
  const showPdfViewerOption = document && document.file_size < 5_000_000; // 5MB limit

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">Loading document...</p>
        </div>
      </div>
    );
  }

  if (error || !document) {
    return (
      <div className="space-y-6">
        <Button variant="outline" onClick={handleBack}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        <div className="flex items-center gap-2 p-4 bg-destructive/10 rounded-lg">
          <AlertCircle className="h-5 w-5 text-destructive" />
          <p className="font-medium">{error || 'Document not found'}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Back Button */}
      <Button variant="outline" onClick={handleBack}>
        <ArrowLeft className="h-4 w-4 mr-2" />
        Back to Documents
      </Button>

      {/* Document Title and Metadata */}
      <div className="space-y-2">
        <h1 className="text-2xl font-bold">{document.filename}</h1>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <span>{document.doc_type.toUpperCase()}</span>
          <span>•</span>
          <span>{(document.file_size / 1024 / 1024).toFixed(2)} MB</span>
          {document.date_extracted && (
            <>
              <span>•</span>
              <span>Extracted: {new Date(document.date_extracted).toLocaleDateString()}</span>
            </>
          )}
        </div>
      </div>

      {/* AI Summary Section */}
      {id && (
        <DocumentSummary
          documentId={id}
          className="border-primary/20"
        />
      )}

      {/* Download Button */}
      <div className="flex items-center gap-3">
        <Button onClick={handleDownload} size="lg" className="gap-2">
          <Download className="h-5 w-5" />
          Download Full PDF
        </Button>
        {showPdfViewerOption && !showPdfViewer && (
          <Button
            variant="outline"
            onClick={() => setShowPdfViewer(true)}
            size="lg"
            className="gap-2"
          >
            <Eye className="h-5 w-5" />
            View in Browser
          </Button>
        )}
        {showPdfViewer && (
          <Button
            variant="outline"
            onClick={() => setShowPdfViewer(false)}
            size="lg"
          >
            Hide Viewer
          </Button>
        )}
      </div>

      {/* Optional PDF Viewer (for small files) */}
      {showPdfViewerOption && showPdfViewer && (
        <div className="border rounded-lg p-4 bg-muted/30">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-semibold">Browser PDF Viewer</h2>
            <span className="text-xs text-muted-foreground">Experimental - May not work for all PDFs</span>
          </div>
          <DocumentViewer
            document={document}
            isOpen={true}
            onClose={() => setShowPdfViewer(false)}
            onEntityClick={handleEntityClick}
            standalone={true}
          />
        </div>
      )}

      {/* Message for large files */}
      {!showPdfViewerOption && (
        <div className="p-4 bg-blue-50 dark:bg-blue-950/20 rounded-lg border border-blue-200 dark:border-blue-800">
          <p className="text-sm text-blue-900 dark:text-blue-100">
            <strong>Large file detected:</strong> This document is too large to view in the browser.
            Please download it to view the full PDF.
          </p>
        </div>
      )}
    </div>
  );
}
