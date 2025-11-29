/**
 * DOCUMENTS SEARCH FUNCTIONALITY
 */

let currentDocPage = 0;
let currentDocQuery = '';
let currentDocFilters = {
    type: '',
    source: '',
    entity: ''
};
let totalDocPages = 1;
let documentsCache = null;
let documentsViewInitialized = false;

/**
 * Initialize documents view
 */
async function initDocumentsView() {
    console.log('Initializing documents view...');

    // Load initial documents
    await searchDocuments();

    // Load filter options only once
    if (!documentsViewInitialized) {
        await loadDocumentFilters();

        // Add enter key listener to search input (only once)
        const searchInput = document.getElementById('doc-search-input');
        if (searchInput) {
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    searchDocuments();
                }
            });
        }

        documentsViewInitialized = true;
    }
}

/**
 * Load available filter options
 */
async function loadDocumentFilters() {
    try {
        const response = await fetch('/api/documents?limit=1');
        const data = await response.json();

        if (data.filters) {
            // Populate type filter
            const typeFilter = document.getElementById('doc-type-filter');
            if (typeFilter && data.filters.types) {
                // Clear existing options (except first "All Types" option)
                typeFilter.innerHTML = '<option value="">All Document Types</option>';

                // Get unique types and sort them
                const uniqueTypes = [...new Set(data.filters.types)].sort();

                uniqueTypes.forEach(type => {
                    const option = document.createElement('option');
                    option.value = type;
                    option.textContent = capitalizeDocType(type);
                    typeFilter.appendChild(option);
                });
            }

            // Populate source filter
            const sourceFilter = document.getElementById('doc-source-filter');
            if (sourceFilter && data.filters.sources) {
                // Clear existing options (except first "All Sources" option)
                sourceFilter.innerHTML = '<option value="">All Sources</option>';

                // Get unique sources and sort them
                const uniqueSources = [...new Set(data.filters.sources)].sort();

                uniqueSources.forEach(source => {
                    const option = document.createElement('option');
                    option.value = source;
                    option.textContent = source;
                    sourceFilter.appendChild(option);
                });
            }
        }
    } catch (error) {
        console.error('Error loading document filters:', error);
    }
}

/**
 * Search documents with current filters
 */
async function searchDocuments(resetPage = true) {
    if (resetPage) {
        currentDocPage = 0;
    }

    // Get search query
    const searchInput = document.getElementById('doc-search-input');
    currentDocQuery = searchInput ? searchInput.value.trim() : '';

    // Get filter values
    const typeFilter = document.getElementById('doc-type-filter');
    const sourceFilter = document.getElementById('doc-source-filter');
    const entityFilter = document.getElementById('doc-entity-filter');

    currentDocFilters = {
        type: typeFilter ? typeFilter.value : '',
        source: sourceFilter ? sourceFilter.value : '',
        entity: entityFilter ? entityFilter.value : ''
    };

    // Build query parameters
    const params = new URLSearchParams({
        limit: '20',
        offset: (currentDocPage * 20).toString()
    });

    if (currentDocQuery) params.append('q', currentDocQuery);
    if (currentDocFilters.type) params.append('doc_type', currentDocFilters.type);
    if (currentDocFilters.source) params.append('source', currentDocFilters.source);
    if (currentDocFilters.entity) params.append('entity', currentDocFilters.entity);

    try {
        const response = await fetch(`/api/documents?${params}`);
        const data = await response.json();

        documentsCache = data;

        // Calculate total pages
        totalDocPages = Math.ceil(data.total / 20);

        // Update results count
        updateDocResultsCount(data.total, data.offset, data.limit);

        // Render documents
        renderDocuments(data.documents);

        // Update pagination
        updateDocPagination();

    } catch (error) {
        console.error('Error searching documents:', error);
        showDocError('Failed to load documents. Please try again.');
    }
}

/**
 * Render document cards
 */
function renderDocuments(documents) {
    const container = document.getElementById('documents-list');
    if (!container) return;

    if (!documents || documents.length === 0) {
        container.innerHTML = `
            <div class="no-results">
                <i data-lucide="file-x" style="width: 48px; height: 48px;"></i>
                <p>No documents found matching your criteria.</p>
            </div>
        `;
        lucide.createIcons();
        return;
    }

    container.innerHTML = documents.map(doc => createDocumentCard(doc)).join('');
    lucide.createIcons();
}

/**
 * Create a document card HTML
 */
function createDocumentCard(doc) {
    const title = doc.filename || doc.id || 'Untitled Document';
    const type = doc.classification || 'unknown';
    const badgeClass = getDocTypeBadgeClass(type);
    const entities = doc.entities_mentioned || [];

    // Create preview snippet (first 200 chars of path or filename)
    const preview = doc.path ? doc.path.substring(0, 200) : '';

    return `
        <div class="document-card" onclick="viewDocument('${doc.id}')">
            <div class="document-card-header">
                <div>
                    <div class="document-title">${escapeHtml(title)}</div>
                    <div class="document-meta">
                        <span><i data-lucide="folder" style="width: 12px; height: 12px;"></i> ${escapeHtml(doc.source || 'Unknown')}</span>
                        ${doc.file_size ? `<span><i data-lucide="file" style="width: 12px; height: 12px;"></i> ${formatFileSize(doc.file_size)}</span>` : ''}
                    </div>
                </div>
                <div class="document-badges">
                    <span class="document-badge ${badgeClass}">${type}</span>
                </div>
            </div>
            ${preview ? `<div class="document-preview">${escapeHtml(preview)}...</div>` : ''}
            ${entities.length > 0 ? `
                <div class="document-entities">
                    ${entities.slice(0, 5).map(entity => `
                        <span class="entity-tag" onclick="filterByEntity('${escapeHtml(entity)}', event)">
                            ${escapeHtml(entity)}
                        </span>
                    `).join('')}
                    ${entities.length > 5 ? `<span class="entity-tag">+${entities.length - 5} more</span>` : ''}
                </div>
            ` : ''}
        </div>
    `;
}

/**
 * Get badge class for document type
 */
function getDocTypeBadgeClass(type) {
    const typeMap = {
        'email': 'badge-email',
        'court_filing': 'badge-court',
        'court filing': 'badge-court',
        'flight_log': 'badge-flight',
        'flight log': 'badge-flight',
        'financial': 'badge-financial'
    };
    return typeMap[type.toLowerCase()] || 'badge-unknown';
}

/**
 * Capitalize document type for display
 */
function capitalizeDocType(type) {
    return type.split('_').map(word =>
        word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
}

/**
 * Format file size
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

/**
 * Filter documents by entity
 */
function filterByEntity(entityName, event) {
    if (event) {
        event.stopPropagation();
    }

    const entityFilter = document.getElementById('doc-entity-filter');
    if (entityFilter) {
        entityFilter.value = entityName;
    }

    searchDocuments(true);
}

/**
 * View document in modal
 */
async function viewDocument(docId) {
    try {
        const response = await fetch(`/api/documents/${docId}`);
        const data = await response.json();

        if (data.error) {
            showDocError(data.error);
            return;
        }

        const doc = data.document;
        const content = data.content;

        // Update modal title
        const titleEl = document.getElementById('modal-doc-title');
        if (titleEl) {
            titleEl.textContent = doc.filename || doc.id || 'Document';
        }

        // Update modal content
        const contentEl = document.getElementById('modal-doc-content');
        if (contentEl) {
            if (content) {
                contentEl.innerHTML = `<pre style="white-space: pre-wrap; font-family: inherit;">${escapeHtml(content)}</pre>`;
            } else {
                contentEl.innerHTML = '<p style="color: var(--text-secondary);">Content not available for this document.</p>';
            }
        }

        // Update metadata sidebar
        const metaEl = document.getElementById('modal-doc-meta');
        if (metaEl) {
            metaEl.innerHTML = `
                <p><strong>Type:</strong> ${capitalizeDocType(doc.classification || 'unknown')}</p>
                <p><strong>Source:</strong> ${escapeHtml(doc.source || 'Unknown')}</p>
                ${doc.file_size ? `<p><strong>Size:</strong> ${formatFileSize(doc.file_size)}</p>` : ''}
                ${doc.classification_confidence ? `<p><strong>Confidence:</strong> ${Math.round(doc.classification_confidence * 100)}%</p>` : ''}
                ${doc.date_extracted ? `<p><strong>Extracted:</strong> ${new Date(doc.date_extracted).toLocaleDateString()}</p>` : ''}
            `;
        }

        // Update entities sidebar
        const entitiesEl = document.getElementById('modal-doc-entities');
        if (entitiesEl) {
            const entities = doc.entities_mentioned || [];
            if (entities.length > 0) {
                entitiesEl.innerHTML = entities.map(entity => `
                    <span class="entity-tag" onclick="filterByEntityFromModal('${escapeHtml(entity)}')">
                        ${escapeHtml(entity)}
                    </span>
                `).join('');
            } else {
                entitiesEl.innerHTML = '<p style="color: var(--text-secondary); font-size: 13px;">No entities identified</p>';
            }
        }

        // Show modal
        const modal = document.getElementById('document-modal');
        if (modal) {
            modal.classList.add('active');
        }

        lucide.createIcons();

    } catch (error) {
        console.error('Error loading document:', error);
        showDocError('Failed to load document content.');
    }
}

/**
 * Close document modal
 */
function closeDocumentModal() {
    const modal = document.getElementById('document-modal');
    if (modal) {
        modal.classList.remove('active');
    }
}

/**
 * Filter by entity from modal and close
 */
function filterByEntityFromModal(entityName) {
    closeDocumentModal();
    switchTab('documents');

    setTimeout(() => {
        filterByEntity(entityName);
    }, 300);
}

/**
 * Change page
 */
function changePage(direction) {
    const newPage = currentDocPage + direction;
    if (newPage >= 0 && newPage < totalDocPages) {
        currentDocPage = newPage;
        searchDocuments(false);
    }
}

/**
 * Update pagination buttons
 */
function updateDocPagination() {
    const prevBtn = document.getElementById('doc-prev-page');
    const nextBtn = document.getElementById('doc-next-page');
    const pageInfo = document.getElementById('doc-page-info');

    if (prevBtn) {
        prevBtn.disabled = currentDocPage === 0;
    }

    if (nextBtn) {
        nextBtn.disabled = currentDocPage >= totalDocPages - 1 || totalDocPages === 0;
    }

    if (pageInfo) {
        pageInfo.textContent = `Page ${currentDocPage + 1} of ${totalDocPages || 1}`;
    }
}

/**
 * Update results count
 */
function updateDocResultsCount(total, offset, limit) {
    const countEl = document.getElementById('doc-results-count');
    if (countEl) {
        const start = offset + 1;
        const end = Math.min(offset + limit, total);
        countEl.textContent = `Showing ${start}-${end} of ${total.toLocaleString()} documents`;
    }
}

/**
 * Show document error
 */
function showDocError(message) {
    const container = document.getElementById('documents-list');
    if (container) {
        container.innerHTML = `
            <div class="no-results">
                <i data-lucide="alert-circle" style="width: 48px; height: 48px; color: var(--accent-blue);"></i>
                <p>${escapeHtml(message)}</p>
            </div>
        `;
        lucide.createIcons();
    }
}

/**
 * Set document view mode (list/grid)
 */
function setDocumentView(view) {
    const buttons = document.querySelectorAll('.view-toggle button');
    buttons.forEach(btn => btn.classList.remove('active'));

    event.target.closest('button').classList.add('active');

    // TODO: Implement grid view if needed
    console.log('View mode:', view);
}

/**
 * View entity's documents (called from entity cards)
 */
function viewEntityDocuments(entityName) {
    switchTab('documents');

    setTimeout(() => {
        const searchInput = document.getElementById('doc-search-input');
        if (searchInput) {
            searchInput.value = '';
        }

        const entityFilter = document.getElementById('doc-entity-filter');
        if (entityFilter) {
            // Add entity to filter if not already there
            let found = false;
            for (let option of entityFilter.options) {
                if (option.value === entityName) {
                    found = true;
                    break;
                }
            }

            if (!found) {
                const option = document.createElement('option');
                option.value = entityName;
                option.textContent = entityName;
                entityFilter.appendChild(option);
            }

            entityFilter.value = entityName;
        }

        searchDocuments(true);
    }, 300);
}

// Make document functions globally available
window.initDocumentsView = initDocumentsView;
window.searchDocuments = searchDocuments;
window.viewDocument = viewDocument;
window.closeDocumentModal = closeDocumentModal;
window.filterByEntity = filterByEntity;
window.filterByEntityFromModal = filterByEntityFromModal;
window.changePage = changePage;
window.setDocumentView = setDocumentView;
window.viewEntityDocuments = viewEntityDocuments;
