import { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import {
  Search,
  FileText,
  Download,
  Filter,
  ChevronLeft,
  ChevronRight,
  Users,
  Eye,
} from 'lucide-react';
import { api, type Document, type DocumentsResponse } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  formatFileSize,
  formatClassification,
  formatSource,
  getConfidenceColor,
} from '@/lib/utils';
// DocumentViewer import removed - now using dedicated /documents/:id route
// import { DocumentViewer } from '@/components/documents/DocumentViewer';

const ITEMS_PER_PAGE = 50;

/**
 * Documents Page
 *
 * Design Enhancement: URL Parameter Support for Entity Filtering
 * Rationale: Support deep linking from entity detail pages with pre-applied entity filter.
 * URL params: ?entity=<name> for entity-specific document filtering.
 *
 * Navigation Flow:
 * EntityDetail → /documents?entity=Jeffrey%20Epstein → Auto-apply entity search
 *
 * Implementation: Sets searchQuery from URL param, which triggers document filtering
 * through existing search functionality.
 */
export function Documents() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [selectedSource, setSelectedSource] = useState<string>('all');
  const [offset, setOffset] = useState(0);
  const [availableTypes, setAvailableTypes] = useState<string[]>([]);
  const [availableSources, setAvailableSources] = useState<string[]>([]);
  // Keep modal state for backward compatibility (currently unused with URL navigation)
  // Uncomment these if switching back to modal behavior
  // const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  // const [isViewerOpen, setIsViewerOpen] = useState(false);

  // Read URL parameters on mount
  useEffect(() => {
    const entityParam = searchParams.get('entity');
    if (entityParam) {
      setSearchQuery(decodeURIComponent(entityParam));
    }
  }, [searchParams]);

  // Load documents whenever filters or pagination change
  useEffect(() => {
    loadDocuments();
  }, [offset, selectedType, selectedSource, searchQuery]);

  const loadDocuments = async () => {
    try {
      setLoading(true);
      const response: DocumentsResponse = await api.getDocuments({
        limit: ITEMS_PER_PAGE,
        offset,
        type: selectedType,
        source: selectedSource,
        search: searchQuery || undefined,
      });

      setDocuments(response.documents);
      setTotal(response.total);
      setAvailableTypes(response.filters.types);
      setAvailableSources(response.filters.sources);
    } catch (error) {
      console.error('Failed to load documents:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchChange = (value: string) => {
    setSearchQuery(value);
    setOffset(0); // Reset to first page on search
  };

  const handleTypeChange = (value: string) => {
    setSelectedType(value);
    setOffset(0); // Reset to first page on filter change
  };

  const handleSourceChange = (value: string) => {
    setSelectedSource(value);
    setOffset(0); // Reset to first page on filter change
  };

  const handlePreviousPage = () => {
    setOffset(Math.max(0, offset - ITEMS_PER_PAGE));
  };

  const handleNextPage = () => {
    if (offset + ITEMS_PER_PAGE < total) {
      setOffset(offset + ITEMS_PER_PAGE);
    }
  };

  const currentPage = Math.floor(offset / ITEMS_PER_PAGE) + 1;
  const totalPages = Math.ceil(total / ITEMS_PER_PAGE);

  const handleDownload = (doc: Document) => {
    // Construct download URL using centralized API base URL
    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8081';
    const downloadUrl = `${API_BASE_URL}/api/documents/${doc.id}/download`;
    window.open(downloadUrl, '_blank');
  };

  const handleViewContent = (doc: Document) => {
    // Navigate to dedicated document page (recommended for addressable URLs)
    navigate(`/documents/${doc.id}`);

    // Option 2: Keep modal for inline viewing (uncomment below to preserve modal behavior)
    // setSelectedDocument(doc);
    // setIsViewerOpen(true);
  };

  // Entity click handler removed - entity navigation now handled in DocumentDetail page
  // const handleEntityClick = (entityName: string) => {
  //   setSearchQuery(entityName);
  // };

  if (loading && documents.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent mb-4" />
          <p className="text-muted-foreground">Loading documents...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold mb-2">Documents</h1>
        <p className="text-muted-foreground">
          Browse and search {total.toLocaleString()} documents from the Epstein archive.
        </p>
      </div>

      {/* Search and Filters */}
      <div className="space-y-4">
        {/* Search Input */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            type="text"
            placeholder="Search documents by filename or content..."
            value={searchQuery}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="pl-10"
          />
        </div>

        {/* Filter Section */}
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex items-center gap-2 flex-1">
            <Filter className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm font-medium">Classification:</span>
            <Select value={selectedType} onValueChange={handleTypeChange}>
              <SelectTrigger className="w-[200px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                {availableTypes.map((type) => (
                  <SelectItem key={type} value={type}>
                    {formatClassification(type)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center gap-2 flex-1">
            <Filter className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm font-medium">Source:</span>
            <Select value={selectedSource} onValueChange={handleSourceChange}>
              <SelectTrigger className="w-[200px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Sources</SelectItem>
                {availableSources.map((source) => (
                  <SelectItem key={source} value={source}>
                    {formatSource(source)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Active Filters Display */}
        <div className="flex flex-wrap gap-2">
          {selectedType !== 'all' && (
            <Badge variant="secondary" className="gap-1">
              Type: {formatClassification(selectedType)}
              <button
                onClick={() => handleTypeChange('all')}
                className="ml-1 hover:bg-secondary-foreground/20 rounded-full p-0.5"
              >
                ×
              </button>
            </Badge>
          )}
          {selectedSource !== 'all' && (
            <Badge variant="secondary" className="gap-1">
              Source: {formatSource(selectedSource)}
              <button
                onClick={() => handleSourceChange('all')}
                className="ml-1 hover:bg-secondary-foreground/20 rounded-full p-0.5"
              >
                ×
              </button>
            </Badge>
          )}
          {searchQuery && (
            <Badge variant="secondary" className="gap-1">
              Search: "{searchQuery}"
              <button
                onClick={() => handleSearchChange('')}
                className="ml-1 hover:bg-secondary-foreground/20 rounded-full p-0.5"
              >
                ×
              </button>
            </Badge>
          )}
        </div>
      </div>

      {/* Results Count and Pagination Controls */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div className="text-sm text-muted-foreground">
          Showing {offset + 1} - {Math.min(offset + ITEMS_PER_PAGE, total)} of{' '}
          {total.toLocaleString()} documents
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handlePreviousPage}
            disabled={offset === 0 || loading}
          >
            <ChevronLeft className="h-4 w-4 mr-1" />
            Previous
          </Button>
          <span className="text-sm text-muted-foreground">
            Page {currentPage} of {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={handleNextPage}
            disabled={offset + ITEMS_PER_PAGE >= total || loading}
          >
            Next
            <ChevronRight className="h-4 w-4 ml-1" />
          </Button>
        </div>
      </div>

      {/* Documents Grid */}
      {loading ? (
        <div className="flex items-center justify-center min-h-[200px]">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent" />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {documents.map((doc) => (
            <Card key={doc.id} className="hover:shadow-lg transition-shadow">
              <CardHeader className="pb-3">
                <div className="flex items-start gap-2">
                  <FileText className="h-5 w-5 text-muted-foreground mt-1 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <CardTitle className="text-base leading-tight break-words">
                      {doc.filename}
                    </CardTitle>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {/* Badges */}
                <div className="flex flex-wrap gap-2">
                  <Badge variant="outline" className="text-xs">
                    {formatClassification(doc.classification)}
                  </Badge>
                  <Badge variant="secondary" className="text-xs">
                    {formatSource(doc.source)}
                  </Badge>
                  <Badge variant="outline" className="text-xs">
                    {doc.doc_type.toUpperCase()}
                  </Badge>
                </div>

                {/* Stats */}
                <div className="space-y-1.5 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">File Size:</span>
                    <span className="font-medium">{formatFileSize(doc.file_size)}</span>
                  </div>

                  {doc.classification_confidence > 0 && (
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Confidence:</span>
                      <span
                        className={`font-medium ${getConfidenceColor(
                          doc.classification_confidence
                        )}`}
                      >
                        {(doc.classification_confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                  )}

                  {doc.entities_mentioned.length > 0 && (
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground flex items-center gap-1">
                        <Users className="h-3 w-3" />
                        Entities:
                      </span>
                      <span className="font-medium">{doc.entities_mentioned.length}</span>
                    </div>
                  )}

                  {doc.date_extracted && (
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Extracted:</span>
                      <span className="font-medium text-xs">
                        {new Date(doc.date_extracted).toLocaleDateString()}
                      </span>
                    </div>
                  )}
                </div>

                {/* Action Buttons */}
                <div className="flex gap-2">
                  <Button
                    variant="default"
                    size="sm"
                    className="flex-1"
                    onClick={() => handleViewContent(doc)}
                  >
                    <Eye className="h-4 w-4 mr-2" />
                    View Content
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleDownload(doc)}
                  >
                    <Download className="h-4 w-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Empty State */}
      {!loading && documents.length === 0 && (
        <div className="text-center py-12">
          <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <p className="text-lg font-medium mb-1">No documents found</p>
          <p className="text-muted-foreground">
            Try adjusting your search or filter criteria
          </p>
        </div>
      )}

      {/* Bottom Pagination */}
      {!loading && documents.length > 0 && (
        <div className="flex justify-center items-center gap-2 pt-4">
          <Button
            variant="outline"
            size="sm"
            onClick={handlePreviousPage}
            disabled={offset === 0}
          >
            <ChevronLeft className="h-4 w-4 mr-1" />
            Previous
          </Button>
          <span className="text-sm text-muted-foreground">
            Page {currentPage} of {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={handleNextPage}
            disabled={offset + ITEMS_PER_PAGE >= total}
          >
            Next
            <ChevronRight className="h-4 w-4 ml-1" />
          </Button>
        </div>
      )}

      {/* Document Viewer Modal - Removed (now using dedicated /documents/:id route) */}
      {/* Uncomment below if switching back to modal behavior */}
      {/* <DocumentViewer
        document={selectedDocument}
        isOpen={isViewerOpen}
        onClose={() => setIsViewerOpen(false)}
        onEntityClick={handleEntityClick}
      /> */}
    </div>
  );
}
