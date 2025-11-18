// Epstein Archive Explorer - Client Application
const API_BASE = window.location.protocol + '//' + window.location.host + '/api';

// Global error handlers for debugging
window.addEventListener('error', (e) => {
    console.error('🚨 Global error caught:', e.error);
    console.error('Message:', e.message);
    console.error('File:', e.filename, 'Line:', e.lineno, 'Col:', e.colno);
});

window.addEventListener('unhandledrejection', (e) => {
    console.error('🚨 Unhandled promise rejection:', e.reason);
    console.error('Promise:', e.promise);
});

// Authentication check - DISABLED FOR DEVELOPMENT
function checkAuthentication() {
    // Authentication disabled - allow all access
    console.log('Authentication check disabled');
    return true;
}

// Authentication check disabled - no redirect
// checkAuthentication();

// Override fetch to always include credentials (cookies)
const originalFetch = window.fetch;
window.fetch = function(url, options = {}) {
    // Always include credentials for same-origin requests
    if (!options.credentials) {
        options.credentials = 'include';
    }

    return originalFetch(url, options);
};

let networkData = null;
let simulation = null;
let svg = null;
let g = null;
let node = null;
let link = null;
let label = null;
let zoom = null;

// Entity biographies and tags cache
let entityBios = {};
let entityTags = {};

// Network state management
let selectedNode = null;
let searchResults = [];
let currentSearchIndex = 0;
let activeFilters = {
    billionaires: false,
    high: false,
    medium: false,
    low: false
};
let visibleNodes = new Set();
let markedLoaded = false;

// Entity Type Detection
function detectEntityType(entityName) {
    const name = entityName.toLowerCase();

    // Business/Organization indicators
    const businessKeywords = [
        'corp', 'corporation', 'inc', 'incorporated', 'llc', 'ltd', 'limited',
        'company', 'co.', 'enterprises', 'group', 'holdings', 'international',
        'partners', 'associates', 'ventures', 'capital', 'investments',
        'foundation', 'trust', 'fund', 'bank', 'financial', 'consulting'
    ];

    // Location indicators
    const locationKeywords = [
        'island', 'airport', 'beach', 'estate', 'ranch', 'street', 'avenue',
        'road', 'boulevard', 'drive', 'place', 'manor', 'villa', 'palace',
        'hotel', 'resort', 'club'
    ];

    // Organization indicators (non-profit, government, etc.)
    const organizationKeywords = [
        'foundation', 'institute', 'university', 'college', 'school',
        'department', 'agency', 'commission', 'board', 'council',
        'society', 'association', 'federation', 'alliance'
    ];

    // Check for business
    if (businessKeywords.some(keyword => name.includes(keyword))) {
        return 'business';
    }

    // Check for organization
    if (organizationKeywords.some(keyword => name.includes(keyword))) {
        return 'organization';
    }

    // Check for location
    if (locationKeywords.some(keyword => name.includes(keyword))) {
        return 'location';
    }

    // Default to person
    return 'person';
}

function getEntityIcon(entityType) {
    const icons = {
        'person': 'user',
        'business': 'building-2',
        'location': 'map-pin',
        'organization': 'briefcase'
    };
    return icons[entityType] || 'user';
}

function getEntityTypeBadge(entityName) {
    const entityType = detectEntityType(entityName);
    const icon = getEntityIcon(entityType);
    // Use empty i tag to prevent text duplication when Lucide initializes
    return `<span class="entity-type-icon ${entityType}"><i data-lucide="${icon}" aria-hidden="true"></i> <span class="entity-type-label">${entityType}</span></span>`;
}

/**
 * Format entity name - clean up and standardize display
 * API already returns names in "Lastname, Firstname" format, so we just clean them up
 * Handles edge cases: removes trailing commas, extra spaces, etc.
 */
function formatEntityName(name) {
    if (!name) return '';

    // Clean up the name
    name = name.trim();

    // Remove any trailing commas and spaces
    name = name.replace(/,+\s*$/g, '');

    // Remove any double commas
    name = name.replace(/,+/g, ',');

    // Normalize spacing around commas
    name = name.replace(/\s*,\s*/g, ', ');

    // Remove any trailing spaces again after normalization
    name = name.trim();

    return name;
}

// ============================================================================
// Entity Linking System - 4 Types of Links
// ============================================================================

/**
 * Escape string for safe use in JavaScript onclick attributes
 */
function escapeForJS(str) {
    if (!str) return '';
    return str.replace(/'/g, "\\'").replace(/"/g, '\\"').replace(/\n/g, '\\n');
}

/**
 * Create entity action links (Bio, Flights, Docs, Network)
 * These links allow users to explore an entity across different views
 * Now with conditional rendering based on data availability
 */
function createEntityLinks(entityName, entity = {}) {
    const escaped = escapeForJS(entityName);

    // Determine what data is available
    const hasBio = entityBios[entityName]?.summary && entityBios[entityName].summary.length > 0;
    const hasConnections = (entity.connection_count || 0) > 0;
    const hasFlights = (entity.flight_count || 0) > 0;
    const hasDocs = (entity.total_documents || entity.document_count || 0) > 0;

    const links = [];

    // Connections - show if entity has connections
    if (hasConnections) {
        links.push(`
            <button onclick="highlightInNetwork('${escaped}')"
                    class="entity-link-btn entity-link-connections" title="View Connections">
                <i data-lucide="users"></i> Connections (${entity.connection_count || 0})
            </button>
        `);
    }

    // Docs - only if entity mentioned in documents
    if (hasDocs) {
        links.push(`
            <button onclick="filterDocsByEntity('${escaped}')"
                    class="entity-link-btn entity-link-docs" title="View Documents">
                <i data-lucide="file-text"></i> Docs (${entity.total_documents || entity.document_count || 0})
            </button>
        `);
    }

    // Flights - only if entity appears in flight logs
    if (hasFlights) {
        links.push(`
            <button onclick="filterFlightsByEntity('${escaped}')"
                    class="entity-link-btn entity-link-flights" title="View Flights">
                <i data-lucide="plane"></i> Flights (${entity.flight_count || 0})
            </button>
        `);
    }

    // Network - always show (for entities without connections, this shows the node in isolation)
    if (!hasConnections) {
        links.push(`
            <button onclick="highlightInNetwork('${escaped}')"
                    class="entity-link-btn entity-link-network" title="View Network">
                <i data-lucide="git-branch"></i> Network
            </button>
        `);
    }

    return `
        <div class="entity-links">
            ${links.join('')}
        </div>
    `;
}

/**
 * Unified entity rendering function
 * Renders entity with bio, tags, and action links
 * @param {Object} entity - Entity object with name, connections, etc.
 * @param {string} renderMode - 'card' | 'compact' | 'inline'
 * @returns {string} HTML string
 */
function renderEntity(entity, renderMode = 'card') {
    const formattedName = formatEntityName(entity.name);
    const escapedName = formattedName.replace(/&/g, '&amp;')
                                      .replace(/</g, '&lt;')
                                      .replace(/>/g, '&gt;')
                                      .replace(/"/g, '&quot;')
                                      .replace(/'/g, '&#39;');
    const rawName = entity.name.replace(/'/g, "\\'");

    // Get bio
    const bio = entityBios[entity.name]?.summary || '';
    const shortBio = bio ? (bio.substring(0, 200) + (bio.length > 200 ? '...' : '')) : '';
    const escapedBio = shortBio.replace(/&/g, '&amp;')
                                .replace(/</g, '&lt;')
                                .replace(/>/g, '&gt;')
                                .replace(/"/g, '&quot;')
                                .replace(/'/g, '&#39;');

    // Get tags
    const tags = entityTags[entity.name]?.tags || [];
    const tagsHTML = tags.length > 0 ? `
        <div class="entity-tags-inline">
            ${tags.slice(0, 3).map(tag => `<span class="tag tag-${tag.toLowerCase().replace(/\s+/g, '-')}">${tag}</span>`).join('')}
        </div>
    ` : '';

    // Get entity type badge
    const typeBadge = getEntityTypeBadge(entity.name);

    if (renderMode === 'card') {
        return `
            <div class="entity-card">
                <div class="entity-card-header" onclick="showEntityCard('${rawName}')">
                    <h4 style="font-size: 15px; font-weight: 600; margin: 0;">${escapedName}</h4>
                    ${entity.is_billionaire ? '<span class="billionaire-badge">BILLIONAIRE</span>' : ''}
                </div>
                <div class="entity-card-content" onclick="showEntityCard('${rawName}')">
                    ${tagsHTML}
                    ${escapedBio ? `<p class="entity-bio">${escapedBio}</p>` : ''}
                    <div style="margin-bottom: 12px;">${typeBadge}</div>
                </div>
                ${createEntityLinks(entity.name, entity)}
            </div>
        `;
    } else if (renderMode === 'compact') {
        return `
            <div class="entity-compact" onclick="showEntityCard('${rawName}')">
                <span class="entity-name">${escapedName}</span>
                ${tagsHTML}
            </div>
        `;
    } else { // inline
        return `<span class="entity-inline" onclick="showEntityCard('${rawName}')">${escapedName}</span>`;
    }
}

/**
 * Show entity biography card (modal popup)
 */
async function showEntityCard(entityName) {
    const bio = entityBios[entityName] || {};
    const tags = entityTags[entityName]?.tags || [];
    const primaryTag = entityTags[entityName]?.primary_tag || '';

    // Get entity stats from network data
    const entityNode = networkData?.nodes?.find(n => n.name === entityName);
    const connections = entityNode?.connection_count || 0;
    const documents = entityNode?.document_count || 0;
    const flights = entityNode?.flight_count || 0;

    // Count timeline events mentioning this entity
    const timelineEvents = typeof timelineData !== 'undefined'
        ? timelineData.filter(event => {
            const eventText = `${event.title} ${event.description}`.toLowerCase();
            return eventText.includes(entityName.toLowerCase());
        }).length
        : 0;

    // Create modal with bio, stats, and tags
    const tagsHTML = tags.length > 0 ? `
        <div class="entity-tags">
            ${tags.map(tag => `<span class="tag tag-${tag.toLowerCase().replace(/\s+/g, '-')}">${tag}</span>`).join('')}
        </div>
    ` : '';

    // Build sources/Wikipedia links HTML if available
    const sourcesHTML = bio.sources && bio.sources.length > 0 ? `
        <div class="entity-sources" style="margin-top: 16px; padding-top: 16px; border-top: 1px solid var(--border-color);">
            <div style="font-weight: 600; margin-bottom: 8px; color: var(--text-secondary); font-size: 12px;">SOURCES</div>
            <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                ${bio.sources.map(source => {
                    const url = typeof source === 'string' ? source : source.url;
                    const name = typeof source === 'string'
                        ? (url.includes('wikipedia.org') ? 'Wikipedia' : new URL(url).hostname.replace('www.', ''))
                        : (source.name || new URL(url).hostname.replace('www.', ''));
                    return `<a href="${url}" target="_blank" rel="noopener noreferrer" class="source-link" style="font-size: 12px; color: var(--accent-blue); text-decoration: none; padding: 4px 8px; background: var(--surface-elevated); border-radius: 4px; border: 1px solid var(--border-color);">${name}</a>`;
                }).join('')}
            </div>
        </div>
    ` : '';

    const modal = `
        <div class="entity-modal-overlay" onclick="closeEntityCard()">
            <div class="entity-modal-card" onclick="event.stopPropagation()">
                <button class="modal-close-btn" onclick="closeEntityCard()">&times;</button>
                <h2 style="margin-bottom: 12px;">${formatEntityName(entityName)}</h2>
                ${tagsHTML}
                <p class="entity-bio-full">${bio.summary || 'No biographical information available.'}</p>
                ${sourcesHTML}
                <div class="entity-stats-grid">
                    <div class="stat"><span>Connections:</span> <strong>${connections}</strong></div>
                    <div class="stat"><span>Documents:</span> <strong>${documents}</strong></div>
                    <div class="stat"><span>Flights:</span> <strong>${flights}</strong></div>
                </div>
                <div class="entity-card-actions">
                    <button onclick="filterFlightsByEntity('${escapeForJS(entityName)}'); closeEntityCard();" class="action-btn" ${flights === 0 ? 'disabled' : ''}>
                        <i data-lucide="plane"></i>
                        <span>Flights</span>
                        <span class="action-badge">${flights}</span>
                    </button>
                    <button onclick="filterDocsByEntity('${escapeForJS(entityName)}'); closeEntityCard();" class="action-btn" ${documents === 0 ? 'disabled' : ''}>
                        <i data-lucide="file-text"></i>
                        <span>Docs</span>
                        <span class="action-badge">${documents}</span>
                    </button>
                    <button onclick="highlightInNetwork('${escapeForJS(entityName)}'); closeEntityCard();" class="action-btn">
                        <i data-lucide="share-2"></i>
                        <span>Network</span>
                        <span class="action-badge">${connections}</span>
                    </button>
                    <button onclick="filterTimelineByEntity('${escapeForJS(entityName)}'); closeEntityCard();" class="action-btn" ${timelineEvents === 0 ? 'disabled' : ''}>
                        <i data-lucide="calendar"></i>
                        <span>Timeline</span>
                        <span class="action-badge">${timelineEvents}</span>
                    </button>
                </div>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modal);
    lucide.createIcons();
}

/**
 * Close entity card modal
 */
function closeEntityCard() {
    const modal = document.querySelector('.entity-modal-overlay');
    if (modal) {
        modal.remove();
    }
}

/**
 * Filter flights by entity (switch to flights tab and apply filter)
 */
function filterFlightsByEntity(entityName) {
    console.log('Filtering flights by entity:', entityName);

    // Switch to flights tab
    switchTab('flights');

    // Wait for tab to load, then apply filter
    setTimeout(() => {
        // Check if flight filter exists
        const passengerFilter = document.getElementById('flight-passenger-filter');
        if (passengerFilter) {
            // Set the search input value directly
            passengerFilter.value = entityName;

            // Trigger filter application
            if (typeof applyFlightFilters === 'function') {
                applyFlightFilters();
            }
        }

        showToast(`Showing flights for ${formatEntityName(entityName)}`);
    }, 100);

    // Update URL hash for deep linking
    window.location.hash = `flights?entity=${encodeURIComponent(entityName)}`;
}

/**
 * Filter documents by entity (switch to documents tab and apply filter)
 */
function filterDocsByEntity(entityName) {
    console.log('Filtering documents by entity:', entityName);

    // Switch to documents tab
    switchTab('documents');

    setTimeout(() => {
        // Use existing viewEntityDocuments function if available
        if (typeof viewEntityDocuments === 'function') {
            viewEntityDocuments(entityName);
        } else {
            // Fallback: set entity filter if it exists
            const entityFilter = document.getElementById('doc-entity-filter');
            if (entityFilter) {
                entityFilter.value = entityName;
                // Trigger search
                if (typeof searchDocuments === 'function') {
                    searchDocuments('', { entity: entityName });
                }
            }
        }

        showToast(`Showing documents mentioning ${formatEntityName(entityName)}`);
    }, 100);

    // Update URL hash for deep linking
    window.location.hash = `documents?entity=${encodeURIComponent(entityName)}`;
}

/**
 * Highlight entity in network graph (switch to network tab and search)
 */
function highlightInNetwork(entityName) {
    console.log('Highlighting in network:', entityName);

    // Switch to network tab
    switchTab('network');

    setTimeout(() => {
        // Use existing network search
        const searchInput = document.getElementById('network-search');
        if (searchInput) {
            searchInput.value = entityName;
            // Trigger search event
            const event = new Event('input', { bubbles: true });
            searchInput.dispatchEvent(event);

            // Also call handleNetworkSearch if it exists
            if (typeof handleNetworkSearch === 'function') {
                handleNetworkSearch(entityName);
            }
        }

        showToast(`Highlighting ${formatEntityName(entityName)} in network`);
    }, 100);

    // Update URL hash for deep linking
    window.location.hash = `network?entity=${encodeURIComponent(entityName)}`;
}

/**
 * Filter timeline by entity (switch to timeline tab and apply filter)
 */
function filterTimelineByEntity(entityName) {
    console.log('Filtering timeline by entity:', entityName);

    // Switch to timeline tab
    switchTab('timeline');

    setTimeout(() => {
        // Use timeline search functionality
        const searchInput = document.getElementById('timeline-search-input');
        if (searchInput) {
            searchInput.value = entityName;

            // Trigger search
            if (typeof filterTimelineBySearch === 'function') {
                filterTimelineBySearch(entityName);
            }
        }

        showToast(`Showing timeline for ${formatEntityName(entityName)}`);
    }, 100);

    // Update URL hash for deep linking
    window.location.hash = `timeline?entity=${encodeURIComponent(entityName)}`;
}

/**
 * Show toast notification
 */
function showToast(message, duration = 3000) {
    // Remove existing toast if present
    const existingToast = document.querySelector('.toast-notification');
    if (existingToast) {
        existingToast.remove();
    }

    const toast = document.createElement('div');
    toast.className = 'toast-notification';
    toast.textContent = message;
    document.body.appendChild(toast);

    // Trigger animation
    setTimeout(() => toast.classList.add('show'), 10);

    // Remove after duration
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

/**
 * Clear a filter input field and trigger appropriate filter update
 */
function clearFilterInput(inputId) {
    const input = document.getElementById(inputId);
    if (!input) return;

    input.value = '';

    // Hide the clear button
    const clearBtn = input.nextElementSibling;
    if (clearBtn && clearBtn.classList.contains('filter-clear-btn')) {
        clearBtn.style.display = 'none';
    }

    // Trigger appropriate filter update based on input ID
    if (inputId === 'entity-search') {
        filterEntities('');
    } else if (inputId === 'flight-airport-filter') {
        applyFlightFilters();
    } else if (inputId === 'timeline-search-input') {
        if (typeof filterTimelineBySearch === 'function') {
            filterTimelineBySearch('');
        }
    }
}

/**
 * Toggle visibility of clear button based on input value
 */
function toggleClearButton(input) {
    const clearBtn = input.nextElementSibling;
    if (clearBtn && clearBtn.classList.contains('filter-clear-btn')) {
        clearBtn.style.display = input.value.trim() !== '' ? 'flex' : 'none';
    }
}

// Make functions globally available
window.showEntityCard = showEntityCard;
window.closeEntityCard = closeEntityCard;
window.filterFlightsByEntity = filterFlightsByEntity;
window.filterDocsByEntity = filterDocsByEntity;
window.highlightInNetwork = highlightInNetwork;
window.filterTimelineByEntity = filterTimelineByEntity;
window.createEntityLinks = createEntityLinks;
window.clearFilterInput = clearFilterInput;
window.toggleClearButton = toggleClearButton;

// Load marked.js library for markdown rendering
function loadMarkedJS() {
    if (markedLoaded) return Promise.resolve();

    return new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/marked@11.0.0/marked.min.js';
        script.onload = () => {
            markedLoaded = true;
            // Configure marked for security
            if (typeof marked !== 'undefined') {
                marked.setOptions({
                    breaks: true,
                    gfm: true,
                    headerIds: false,
                    mangle: false
                });
            }
            resolve();
        };
        script.onerror = reject;
        document.head.appendChild(script);
    });
}

// Feature link patterns for auto-linking
const featureLinks = {
    'network graph': { text: 'Network Graph', action: "switchTab('network')" },
    'entity network': { text: 'Entity Network', action: "switchTab('network')" },
    'knowledge graph': { text: 'Knowledge Graph', action: "switchTab('network')" },
    'entities list': { text: 'Entities', action: "switchTab('entities')" },
    'view entities': { text: 'Entities', action: "switchTab('entities')" },
    'roadmap': { text: 'Roadmap', action: "switchTab('roadmap')" },
    'project roadmap': { text: 'Roadmap', action: "switchTab('roadmap')" },
    'suggest a source': { text: 'Suggest a Source', action: "showSourceForm()" },
    'ingestion status': { text: 'Ingestion Status', action: "switchTab('ingestion')" },
    'ocr progress': { text: 'OCR Progress', action: "switchTab('ingestion')" },
    'overview': { text: 'Overview', action: "switchTab('overview')" }
};

// Enhance text with feature links
function enhanceWithFeatureLinks(text) {
    let enhanced = text;

    // Guard: Don't enhance already-enhanced content (prevents double-processing)
    if (enhanced.includes('class="feature-link"')) {
        return enhanced;
    }

    // Sort patterns by length (longest first) to avoid partial matches
    const patterns = Object.keys(featureLinks).sort((a, b) => b.length - a.length);

    patterns.forEach(pattern => {
        const link = featureLinks[pattern];
        // Case-insensitive match, but preserve original case in non-link text
        // Don't match if already inside an HTML tag
        const regex = new RegExp(`(?![^<]*>)\\b(${pattern})\\b`, 'gi');
        enhanced = enhanced.replace(regex, (match) => {
            const openTag = '<a href="javascript:void(0)" onclick="' + link.action + '" class="feature-link">';
            const closeTag = '</a>';
            return openTag + match + closeTag;
        });
    });

    return enhanced;
}

// Render markdown with security and feature link enhancement
function renderMarkdown(text) {
    // First, enhance with feature links (before markdown parsing)
    let enhanced = enhanceWithFeatureLinks(text);

    // Render markdown
    if (markedLoaded && typeof marked !== 'undefined') {
        try {
            // Use marked for full markdown support
            let html = marked.parse(enhanced);

            // Basic XSS prevention: remove script tags
            html = html.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');

            return html;
        } catch (error) {
            console.error('Markdown rendering error:', error);
            return basicMarkdownRender(enhanced);
        }
    }

    // Fallback: basic markdown rendering
    return basicMarkdownRender(enhanced);
}

// Basic markdown renderer (fallback if marked.js fails to load)
function basicMarkdownRender(text) {
    let html = text;

    // Escape HTML first
    html = html.replace(/&/g, '&amp;')
               .replace(/</g, '&lt;')
               .replace(/>/g, '&gt;');

    // Headers
    html = html.replace(/^#### (.*$)/gim, '<h4>$1</h4>');
    html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
    html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');

    // Bold
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/__(.*?)__/g, '<strong>$1</strong>');

    // Italic
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
    html = html.replace(/_(.*?)_/g, '<em>$1</em>');

    // Code blocks (must come before inline code)
    html = html.replace(/```([^\n]*)\n([\s\S]*?)```/g, '<pre><code class="language-$1">$2</code></pre>');

    // Inline code
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

    // Links
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');

    // Blockquotes
    html = html.replace(/^&gt; (.*$)/gim, '<blockquote>$1</blockquote>');

    // Unordered lists
    html = html.replace(/^\* (.*$)/gim, '<li>$1</li>');
    html = html.replace(/^- (.*$)/gim, '<li>$1</li>');

    // Ordered lists
    html = html.replace(/^\d+\. (.*$)/gim, '<li>$1</li>');

    // Wrap consecutive list items
    html = html.replace(/(<li>.*?<\/li>\n?)+/g, '<ul>$&</ul>');

    // Horizontal rules
    html = html.replace(/^---$/gim, '<hr>');
    html = html.replace(/^\*\*\*$/gim, '<hr>');

    // Line breaks
    html = html.replace(/\n\n/g, '</p><p>');
    html = html.replace(/\n/g, '<br>');

    // Wrap in paragraphs
    html = '<p>' + html + '</p>';

    // Clean up extra paragraph tags around block elements
    html = html.replace(/<p>(<h[1-6]>)/g, '$1');
    html = html.replace(/(<\/h[1-6]>)<\/p>/g, '$1');
    html = html.replace(/<p>(<ul>)/g, '$1');
    html = html.replace(/(<\/ul>)<\/p>/g, '$1');
    html = html.replace(/<p>(<ol>)/g, '$1');
    html = html.replace(/(<\/ol>)<\/p>/g, '$1');
    html = html.replace(/<p>(<blockquote>)/g, '$1');
    html = html.replace(/(<\/blockquote>)<\/p>/g, '$1');
    html = html.replace(/<p>(<pre>)/g, '$1');
    html = html.replace(/(<\/pre>)<\/p>/g, '$1');
    html = html.replace(/<p>(<hr>)/g, '$1');
    html = html.replace(/(<hr>)<\/p>/g, '$1');

    return html;
}

// Theme Management
function loadTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    applyTheme(savedTheme);
}

function applyTheme(theme) {
    const root = document.documentElement;
    const themeIcon = document.getElementById('theme-icon');

    if (theme === 'dark') {
        root.setAttribute('data-theme', 'dark');
        if (themeIcon) themeIcon.textContent = '🌙';
    } else {
        root.removeAttribute('data-theme');
        if (themeIcon) themeIcon.textContent = '☀️';
    }

    localStorage.setItem('theme', theme);
}

function toggleTheme() {
    const root = document.documentElement;
    const currentTheme = root.hasAttribute('data-theme') ? 'dark' : 'light';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    applyTheme(newTheme);
}

// Initialize app
document.addEventListener('DOMContentLoaded', async () => {
    loadTheme();

    // Initialize Lucide icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }

    // Load marked.js for markdown rendering
    loadMarkedJS().catch(err => {
        console.warn('Failed to load marked.js, using fallback renderer:', err);
    });

    await loadStats();
    loadIngestionStatus();
    await loadNetworkData();
    await loadEntityBiographies();  // Load bios BEFORE rendering entities
    await loadEntityTags();          // Load tags BEFORE rendering entities
    await loadEntitiesList();        // Now render with complete bio/tag data
    await loadRecentCommits();

    // Handle URL hash parameters for deep linking
    handleHashNavigation();
});

/**
 * Handle URL hash navigation for deep linking to filtered views
 */
function handleHashNavigation() {
    const hash = window.location.hash;
    if (!hash || hash === '#') return;

    // Parse hash format: #tab?entity=Name
    const hashMatch = hash.match(/#([^?]+)(?:\?(.+))?/);
    if (!hashMatch) return;

    const [, tab, params] = hashMatch;

    if (params && params.includes('entity=')) {
        const entityParam = params.split('&').find(p => p.startsWith('entity='));
        if (!entityParam) return;

        const entityName = decodeURIComponent(entityParam.split('=')[1]);

        // Navigate based on tab
        switch(tab) {
            case 'flights':
                filterFlightsByEntity(entityName);
                break;
            case 'documents':
                filterDocsByEntity(entityName);
                break;
            case 'network':
                highlightInNetwork(entityName);
                break;
            case 'timeline':
                filterTimelineByEntity(entityName);
                break;
            default:
                console.warn('Unknown tab in hash:', tab);
        }
    }
}

// Load entity biographies
async function loadEntityBiographies() {
    try {
        const response = await fetch(`${API_BASE}/entity-biographies`, {
            credentials: 'include'
        });
        if (response.ok) {
            entityBios = await response.json();
            console.log(`Loaded biographies for ${Object.keys(entityBios).length} entities`);
        }
    } catch (error) {
        console.error('Failed to load entity biographies:', error);
    }
}

// Load entity tags
async function loadEntityTags() {
    try {
        const response = await fetch(`${API_BASE}/entity-tags`, {
            credentials: 'include'
        });
        if (response.ok) {
            entityTags = await response.json();
            console.log(`Loaded tags for ${Object.keys(entityTags).length} entities`);
        }
    } catch (error) {
        console.error('Failed to load entity tags:', error);
    }
}

// Load statistics
async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/stats`, {
            credentials: 'include'  // Include HTTP Basic Auth credentials
        });
        const data = await response.json();

        document.getElementById('stat-entities').textContent = data.total_entities.toLocaleString();
        document.getElementById('stat-connections').textContent = data.total_connections.toLocaleString();
        document.getElementById('stat-documents').textContent = data.total_documents.toLocaleString();

        document.getElementById('overview-entities').textContent = `${data.total_entities.toLocaleString()} unique entities extracted`;
        document.getElementById('overview-connections').textContent = `${data.total_connections.toLocaleString()} network connections`;
        document.getElementById('overview-documents').textContent = `${data.total_documents.toLocaleString()} documents classified`;
        document.getElementById('overview-ocr').textContent = `OCR processing in progress...`;

        if (data.sources && data.sources.length > 0) {
            document.getElementById('sources-list').innerHTML = data.sources
                .map(source => `<li>${source}</li>`)
                .join('');
        }
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

// Load ingestion status
async function loadIngestionStatus() {
    try {
        const response = await fetch(`${API_BASE}/ingestion/status`, {
            credentials: 'include'  // Include HTTP Basic Auth credentials
        });
        const data = await response.json();

        const progressHTML = `
            <div style="font-size: 14px; line-height: 2;">
                <p><strong>Status:</strong> ${data.status}</p>
                <p><strong>Files Processed:</strong> ${data.files_processed.toLocaleString()} / ${data.total_files.toLocaleString()}</p>
                <p><strong>Progress:</strong> ${data.progress_percentage.toFixed(1)}%</p>
                <div style="background: #0d1117; border-radius: 8px; height: 24px; margin: 16px 0; overflow: hidden;">
                    <div style="background: linear-gradient(90deg, #1f6feb, #0969da); height: 100%; width: ${data.progress_percentage}%; transition: width 0.5s;"></div>
                </div>
                ${data.current_source ? `<p><strong>Current Source:</strong> ${data.current_source}</p>` : ''}
                ${data.last_updated ? `<p style="font-size: 12px; color: #8b949e;"><em>Last updated: ${new Date(data.last_updated).toLocaleString()}</em></p>` : ''}
            </div>
        `;

        const progressEl = document.getElementById('ingestion-progress');
        const overviewEl = document.getElementById('overview-ocr');

        if (progressEl) {
            progressEl.innerHTML = progressHTML;
        }
        if (overviewEl) {
            overviewEl.textContent = `OCR: ${data.files_processed.toLocaleString()}/${data.total_files.toLocaleString()} (${data.progress_percentage.toFixed(1)}%)`;
        }
    } catch (error) {
        console.error('Failed to load ingestion status:', error);
        const progressEl = document.getElementById('ingestion-progress');
        if (progressEl) {
            progressEl.innerHTML = '<p style="color: #8b949e;">Unable to load ingestion status</p>';
        }
    }
}

// Load recent git commits
async function loadRecentCommits() {
    const container = document.getElementById('commits-container');

    try {
        const response = await fetch(`${API_BASE}/git/recent-commits?limit=10`, {
            credentials: 'include'
        });

        if (!response.ok) {
            throw new Error(`Failed to fetch commits: ${response.statusText}`);
        }

        const data = await response.json();

        if (!data.commits || data.commits.length === 0) {
            container.innerHTML = '<div class="commits-loading">No commits found</div>';
            return;
        }

        // Render commits
        container.innerHTML = data.commits.map(commit => {
            const typeClass = `commit-type-${commit.type}`;
            const scopeBadge = commit.scope ? `<span class="commit-scope">${commit.scope}</span>` : '';
            const breakingBadge = commit.breaking ? '<span class="commit-breaking">BREAKING</span>' : '';

            return `
                <div class="commit-card">
                    <div class="commit-type-badge ${typeClass}">
                        ${commit.type}
                    </div>
                    <div class="commit-info">
                        <div class="commit-message">
                            ${breakingBadge}
                            ${scopeBadge}
                            ${escapeHtml(commit.message)}
                        </div>
                        <div class="commit-meta">
                            <span class="commit-hash">
                                <i data-lucide="git-commit" class="commit-icon"></i>
                                ${commit.hash}
                            </span>
                            <span class="commit-author">
                                <i data-lucide="user" class="commit-icon"></i>
                                ${escapeHtml(commit.author)}
                            </span>
                            <span class="commit-date">
                                <i data-lucide="clock" class="commit-icon"></i>
                                ${commit.date}
                            </span>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        // Re-initialize Lucide icons for the new elements
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    } catch (error) {
        console.error('Failed to load commits:', error);
        container.innerHTML = `
            <div class="commits-loading">
                <i data-lucide="alert-circle" style="width: 20px; height: 20px; margin-bottom: 8px;"></i>
                <div>Unable to load recent commits</div>
            </div>
        `;

        // Re-initialize Lucide icons for error icon
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }
}

// Helper function to escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Load and render roadmap
let roadmapLoaded = false;
async function loadRoadmap() {
    if (roadmapLoaded) return;

    try {
        // Ensure marked.js is loaded first
        await loadMarkedJS();

        const response = await fetch('/ROADMAP.md', {
            credentials: 'include'  // Include HTTP Basic Auth credentials
        });
        const markdown = await response.text();

        // Use renderMarkdown for full markdown support with feature links
        let html = renderMarkdown(markdown);

        // Make roadmap sections collapsible
        html = makeRoadmapCollapsible(html);

        document.getElementById('roadmap-content').innerHTML = html;
        roadmapLoaded = true;
    } catch (error) {
        console.error('Failed to load roadmap:', error);
        document.getElementById('roadmap-content').innerHTML = `
            <div style="text-align: center; padding: 40px;" class="chat-message system">
                Failed to load roadmap. Please check the console for errors.
            </div>
        `;
    }
}

// Make roadmap sections collapsible with completed sections hidden by default
function makeRoadmapCollapsible(html) {
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, 'text/html');

    const h2Elements = doc.querySelectorAll('h2');

    h2Elements.forEach((h2) => {
        const headingText = h2.textContent;

        // Only make Phase sections collapsible
        if (!headingText.includes('Phase')) {
            return;
        }

        // Create details element
        const details = doc.createElement('details');
        details.className = 'roadmap-section';

        // Create summary from h2 content
        const summary = doc.createElement('summary');
        summary.className = 'roadmap-summary';
        summary.innerHTML = h2.innerHTML;

        // Create content wrapper
        const contentDiv = doc.createElement('div');
        contentDiv.className = 'roadmap-content';

        // Collect all content until next h2
        let nextElement = h2.nextElementSibling;
        const contentElements = [];

        while (nextElement && nextElement.tagName !== 'H2') {
            contentElements.push(nextElement);
            nextElement = nextElement.nextElementSibling;
        }

        // Move content into wrapper
        contentElements.forEach(el => {
            contentDiv.appendChild(el.cloneNode(true));
        });

        // Check if section is completed
        // Count ✅ vs total task markers (✅, 🔄, 📋, ⏸️)
        const contentText = contentDiv.textContent;
        const allTasks = (contentText.match(/[✅🔄📋⏸️]/g) || []).length;
        const completedTasks = (contentText.match(/✅/g) || []).length;
        const inProgressTasks = (contentText.match(/🔄/g) || []).length;

        // Section is "completed" if all tasks are done (no in-progress or planned tasks)
        const isCompleted = allTasks > 0 && completedTasks === allTasks;

        // Open by default if not completed or has in-progress tasks
        if (!isCompleted || inProgressTasks > 0) {
            details.setAttribute('open', '');
        }

        // Build the details element
        details.appendChild(summary);
        details.appendChild(contentDiv);

        // Replace h2 and its content with details element
        h2.parentNode.insertBefore(details, h2);

        // Remove original elements
        h2.remove();
        contentElements.forEach(el => {
            if (el.parentNode) {
                el.remove();
            }
        });
    });

    return doc.body.innerHTML;
}

// Note: markdownToHTML() removed - using renderMarkdown() for all markdown rendering
// renderMarkdown() provides full marked.js support with feature link enhancement

// Tab switching
function switchTab(tabName, clickedTab) {
    // Cancel flight loading if switching away from flights tab
    if (typeof window.cancelFlightLoading === 'function') {
        window.cancelFlightLoading();
    }

    // Remove active class from all tabs
    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));

    // Add active class to clicked tab (if provided) or find by data attribute
    if (clickedTab) {
        clickedTab.classList.add('active');
    } else {
        // Find tab by onclick attribute matching tabName
        const targetTab = Array.from(document.querySelectorAll('.tab')).find(
            tab => tab.getAttribute('onclick')?.includes(`'${tabName}'`)
        );
        if (targetTab) targetTab.classList.add('active');
    }

    // Switch views
    document.querySelectorAll('.view').forEach(view => view.classList.remove('active'));
    document.getElementById(`${tabName}-view`).classList.add('active');

    // Load content for specific tabs
    if (tabName === 'network' && !simulation) {
        renderNetwork();
    }

    if (tabName === 'roadmap') {
        loadRoadmap();
    }

    if (tabName === 'ingestion') {
        loadIngestionStatus();
    }

    if (tabName === 'sources') {
        loadSources();
    }

    if (tabName === 'documents') {
        initDocumentsView();
    }

    if (tabName === 'flights') {
        initFlightsView();
    }

    if (tabName === 'timeline') {
        console.log('🔄 Tab switched to timeline - calling loadTimeline()');
        // Use setTimeout to ensure DOM is ready after tab switch
        setTimeout(() => {
            if (typeof loadTimeline === 'function') {
                loadTimeline();
            } else {
                console.error('❌ loadTimeline function not found!');
            }
        }, 150);
    }

    // Initialize Lucide icons when switching tabs
    if (typeof lucide !== 'undefined') {
        setTimeout(() => lucide.createIcons(), 100);
    }
}

// Load network data
async function loadNetworkData() {
    if (networkData) return networkData;

    try {
        const response = await fetch(`${API_BASE}/network`, {
            credentials: 'include'  // Include HTTP Basic Auth credentials
        });
        networkData = await response.json();

        // Initialize visible nodes set
        visibleNodes = new Set(networkData.nodes.map(n => n.id));
        updateFilteredCount();

        return networkData;
    } catch (error) {
        console.error('Failed to load network data:', error);
        return null;
    }
}

// Render network visualization
async function renderNetwork() {
    if (!networkData) {
        networkData = await loadNetworkData();
    }

    if (!networkData) {
        console.error('No network data available');
        return;
    }

    const container = document.getElementById('network-container');
    const width = container.clientWidth;
    const height = container.clientHeight;

    // Clear any existing SVG
    d3.select('#network-container').selectAll('*').remove();

    // Create SVG with zoom
    svg = d3.select('#network-container')
        .append('svg')
        .attr('width', width)
        .attr('height', height);

    // Add SVG filter for glow effect
    const defs = svg.append('defs');
    const filter = defs.append('filter')
        .attr('id', 'glow');
    filter.append('feGaussianBlur')
        .attr('stdDeviation', '3')
        .attr('result', 'coloredBlur');
    const feMerge = filter.append('feMerge');
    feMerge.append('feMergeNode').attr('in', 'coloredBlur');
    feMerge.append('feMergeNode').attr('in', 'SourceGraphic');

    g = svg.append('g');

    zoom = d3.zoom()
        .scaleExtent([0.1, 4])
        .on('zoom', (event) => {
            g.attr('transform', event.transform);
        });

    svg.call(zoom);

    // Create simulation with enhanced collision prevention
    simulation = d3.forceSimulation(networkData.nodes)
        .force('link', d3.forceLink(currentEdges)  // Use filtered edges
            .id(d => d.id)
            .distance(100)  // Increased from 80 for better spacing
            .strength(0.8))  // Reduced from 1.0 to allow more flexibility
        .force('charge', d3.forceManyBody().strength(-800))  // Increased repulsion from -500
        .force('center', d3.forceCenter(width / 2, height / 2).strength(0.05))
        .force('collision', d3.forceCollide()
            .radius(d => {
                // Calculate node radius (same as visual radius)
                const nodeRadius = Math.max(5, Math.sqrt(d.connection_count || 1) * 3);
                // Add label width estimation (10px font, ~6px per char avg)
                const labelWidth = formatEntityName(d.id).length * 6;
                // Total collision radius: node + label + 5% overlap allowance
                return nodeRadius + (labelWidth / 2) + 5;
            })
            .strength(0.95)  // 95% collision prevention (5% overlap allowed)
            .iterations(3))  // Multiple iterations for better collision resolution
        .alphaDecay(0.015)  // Slower decay from 0.02 for better stabilization
        .velocityDecay(0.3);  // Reduced from 0.4 for smoother movement

    const rootStyles = getComputedStyle(document.documentElement);
    const borderColor = rootStyles.getPropertyValue('--border-color').trim();
    const accentBlue = rootStyles.getPropertyValue('--accent-blue').trim();
    const bgPrimary = rootStyles.getPropertyValue('--bg-primary').trim();
    const textPrimary = rootStyles.getPropertyValue('--text-primary').trim();

    // Connection type color scheme
    const CONNECTION_TYPES = {
        FLEW_TOGETHER: { color: '#0969da', label: 'Flew Together' },
        BUSINESS: { color: '#8250df', label: 'Business Partner' },
        FAMILY: { color: '#cf222e', label: 'Family Member' },
        LEGAL: { color: '#bf8700', label: 'Legal/Attorney' },
        EMPLOYMENT: { color: '#1a7f37', label: 'Employment' },
        UNKNOWN: { color: borderColor, label: 'Connection' }
    };

    /**
     * Get edge thickness based on connection strength (weight)
     * 5 tiers as per requirements
     */
    function getEdgeThickness(weight) {
        if (weight >= 21) return 8;       // Very bold (21+ connections)
        if (weight >= 11) return 6.5;     // Bold (11-20 connections)
        if (weight >= 6) return 5;        // Medium (6-10 connections)
        if (weight >= 3) return 3;        // Light (3-5 connections)
        return 1.5;                       // Thin (1-2 connections)
    }

    /**
     * Get edge color based on relationship type
     */
    function getEdgeColor(edge) {
        const type = edge.relationship_type || 'FLEW_TOGETHER';
        return CONNECTION_TYPES[type]?.color || CONNECTION_TYPES.UNKNOWN.color;
    }

    // Progressive loading: Start with subset of edges
    // Sort edges by weight (importance) and limit initially
    const maxEdgesInitial = 300; // Start with 300 strongest connections
    const sortedEdges = [...networkData.edges].sort((a, b) => (b.weight || 1) - (a.weight || 1));
    const currentEdges = sortedEdges.slice(0, Math.min(maxEdgesInitial, sortedEdges.length));

    // Store for progressive loading
    window.networkEdges = {
        all: sortedEdges,
        current: currentEdges,
        displayed: maxEdgesInitial
    };

    // Create links with enhanced styling
    link = g.append('g')
        .selectAll('line')
        .data(currentEdges)
        .join('line')
        .attr('stroke', d => getEdgeColor(d))
        .attr('stroke-width', d => getEdgeThickness(d.weight || 1))
        .attr('stroke-opacity', 0.6)
        .style('cursor', 'pointer')
        .on('mouseover', function(event, d) {
            // Highlight edge on hover
            d3.select(this)
                .transition()
                .duration(200)
                .attr('stroke-opacity', 1)
                .attr('stroke-width', getEdgeThickness(d.weight || 1) * 1.3);

            // Show tooltip
            showEdgeTooltip(event, d);
        })
        .on('mouseout', function(event, d) {
            // Reset edge
            if (!selectedNode || (d.source.id !== selectedNode && d.target.id !== selectedNode)) {
                d3.select(this)
                    .transition()
                    .duration(200)
                    .attr('stroke-opacity', 0.6)
                    .attr('stroke-width', getEdgeThickness(d.weight || 1));
            }

            // Hide tooltip
            hideEdgeTooltip();
        })
        .on('click', (event, d) => {
            event.stopPropagation();
            showConnectionDetailsPanel(d);
        });

    // Create nodes
    node = g.append('g')
        .selectAll('circle')
        .data(networkData.nodes)
        .join('circle')
        .attr('r', d => Math.max(5, Math.sqrt(d.connection_count || 1) * 3))
        .attr('fill', d => d.is_billionaire ? '#ffd700' : accentBlue)
        .attr('stroke', bgPrimary)
        .attr('stroke-width', 2)
        .style('cursor', 'pointer')
        .call(d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended))
        .on('click', (event, d) => selectNode(d.id))
        .on('mouseover', function(event, d) {
            if (!selectedNode || selectedNode !== d.id) {
                d3.select(this)
                    .transition()
                    .duration(200)
                    .attr('r', Math.max(8, Math.sqrt(d.connection_count || 1) * 4));
            }
        })
        .on('mouseout', function(event, d) {
            if (!selectedNode || selectedNode !== d.id) {
                d3.select(this)
                    .transition()
                    .duration(200)
                    .attr('r', Math.max(5, Math.sqrt(d.connection_count || 1) * 3));
            }
        });

    // Add edge labels for strong connections (>50 co-occurrences)
    const edgeLabels = g.append('g')
        .selectAll('text')
        .data(networkData.edges.filter(d => (d.weight || 1) > 50))
        .join('text')
        .attr('class', 'edge-label')
        .text(d => d.weight)
        .attr('font-size', 8)
        .attr('fill', accentBlue)
        .attr('font-weight', 600)
        .attr('text-anchor', 'middle')
        .style('pointer-events', 'none')
        .style('opacity', 0.8);

    // Add node labels
    label = g.append('g')
        .selectAll('text')
        .data(networkData.nodes)
        .join('text')
        .text(d => formatEntityName(d.id))
        .attr('font-size', 10)
        .attr('fill', textPrimary)
        .attr('dx', 12)
        .attr('dy', 4)
        .style('pointer-events', 'none');

    // Enhanced legend with thickness tiers and relationship colors
    const legend = g.append('g')
        .attr('class', 'network-legend')
        .attr('transform', 'translate(20, ' + (height - 340) + ')');

    // Legend background with increased height for both sections
    legend.append('rect')
        .attr('width', 240)
        .attr('height', 320)
        .attr('fill', 'var(--bg-secondary)')
        .attr('stroke', 'var(--border-color)')
        .attr('stroke-width', 1)
        .attr('rx', 8)
        .style('opacity', 0.95);

    // Section 1: Connection Strength
    legend.append('text')
        .attr('x', 10)
        .attr('y', 20)
        .attr('font-size', 13)
        .attr('font-weight', 600)
        .attr('fill', textPrimary)
        .text('Connection Strength:');

    // All 5 thickness tiers with accurate widths
    const lineData = [
        {strength: "Very Bold (21+)", width: 8, y: 40},
        {strength: "Bold (11-20)", width: 6.5, y: 60},
        {strength: "Medium (6-10)", width: 5, y: 80},
        {strength: "Light (3-5)", width: 3, y: 100},
        {strength: "Thin (1-2)", width: 1.5, y: 120}
    ];

    lineData.forEach(d => {
        legend.append('line')
            .attr('x1', 10)
            .attr('x2', 50)
            .attr('y1', d.y)
            .attr('y2', d.y)
            .attr('stroke', accentBlue)
            .attr('stroke-width', d.width)
            .attr('stroke-opacity', 0.8);

        legend.append('text')
            .attr('x', 60)
            .attr('y', d.y + 4)
            .attr('font-size', 11)
            .attr('fill', textPrimary)
            .text(d.strength);
    });

    // Section 2: Relationship Types
    legend.append('text')
        .attr('x', 10)
        .attr('y', 155)
        .attr('font-size', 13)
        .attr('font-weight', 600)
        .attr('fill', textPrimary)
        .text('Relationship Types:');

    const colorData = [
        {type: 'FLEW_TOGETHER', y: 175},
        {type: 'BUSINESS', y: 200},
        {type: 'FAMILY', y: 225},
        {type: 'LEGAL', y: 250},
        {type: 'EMPLOYMENT', y: 275}
    ];

    let activeTypeFilter = null;

    colorData.forEach(d => {
        const typeConfig = CONNECTION_TYPES[d.type];

        // Clickable colored line
        const line = legend.append('line')
            .attr('x1', 10)
            .attr('x2', 50)
            .attr('y1', d.y)
            .attr('y2', d.y)
            .attr('stroke', typeConfig.color)
            .attr('stroke-width', 4)
            .attr('stroke-opacity', 0.8)
            .style('cursor', 'pointer')
            .on('click', function() {
                // Toggle filter for this relationship type
                if (activeTypeFilter === d.type) {
                    // Clear filter
                    activeTypeFilter = null;
                    link.transition().duration(300)
                        .attr('stroke-opacity', 0.6)
                        .attr('display', 'block');
                    d3.select(this).attr('stroke-opacity', 0.8);
                } else {
                    // Apply filter
                    activeTypeFilter = d.type;
                    link.transition().duration(300)
                        .attr('stroke-opacity', edge =>
                            (edge.relationship_type || 'FLEW_TOGETHER') === d.type ? 0.9 : 0.1)
                        .attr('display', edge =>
                            (edge.relationship_type || 'FLEW_TOGETHER') === d.type ? 'block' : 'none');

                    // Highlight this legend item
                    legend.selectAll('line').filter(function() {
                        return this !== line.node();
                    }).attr('stroke-opacity', 0.3);
                    d3.select(this).attr('stroke-opacity', 1);
                }
            })
            .on('mouseover', function() {
                if (activeTypeFilter !== d.type) {
                    d3.select(this).attr('stroke-opacity', 1);
                }
            })
            .on('mouseout', function() {
                if (activeTypeFilter !== d.type) {
                    d3.select(this).attr('stroke-opacity', 0.8);
                } else if (activeTypeFilter === null) {
                    d3.select(this).attr('stroke-opacity', 0.8);
                }
            });

        legend.append('text')
            .attr('x', 60)
            .attr('y', d.y + 4)
            .attr('font-size', 11)
            .attr('fill', textPrimary)
            .text(typeConfig.label)
            .style('pointer-events', 'none');
    });

    // Add hint text
    legend.append('text')
        .attr('x', 10)
        .attr('y', 305)
        .attr('font-size', 9)
        .attr('fill', 'var(--text-tertiary)')
        .attr('font-style', 'italic')
        .text('Click colors to filter connections');

    // Update positions on tick
    simulation.on('tick', () => {
        link
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);

        node
            .attr('cx', d => d.x)
            .attr('cy', d => d.y);

        label
            .attr('x', d => d.x)
            .attr('y', d => d.y);

        // Position edge labels at midpoint of connections
        edgeLabels
            .attr('x', d => (d.source.x + d.target.x) / 2)
            .attr('y', d => (d.source.y + d.target.y) / 2);

        // Update legend position to stay in bottom-left corner
        legend.attr('transform', 'translate(20, ' + (height - 120) + ')');
    });

    // Apply initial filters
    applyFilters();

    // Initialize progressive loading controls
    updateConnectionControls();
}

// Drag functions
function dragstarted(event, d) {
    if (!event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
}

function dragged(event, d) {
    d.fx = event.x;
    d.fy = event.y;
}

function dragended(event, d) {
    if (!event.active) simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
}

// Node selection and highlighting
function selectNode(nodeId) {
    if (!networkData || !node) return;

    selectedNode = nodeId;
    const nodeData = networkData.nodes.find(n => n.id === nodeId);
    if (!nodeData) return;

    // Get connected nodes
    const connectedNodeIds = getConnectedNodes(nodeId);

    // Update node appearances
    node.transition()
        .duration(300)
        .attr('r', d => {
            if (d.id === nodeId) {
                return Math.max(10, Math.sqrt(d.connection_count || 1) * 5);
            } else if (connectedNodeIds.has(d.id)) {
                return Math.max(7, Math.sqrt(d.connection_count || 1) * 3.5);
            }
            return Math.max(5, Math.sqrt(d.connection_count || 1) * 3);
        })
        .attr('opacity', d => {
            if (d.id === nodeId || connectedNodeIds.has(d.id)) return 1;
            return 0.2;
        })
        .attr('filter', d => d.id === nodeId ? 'url(#glow)' : null);

    // Update link appearances
    link.transition()
        .duration(300)
        .attr('stroke-opacity', d => {
            if (d.source.id === nodeId || d.target.id === nodeId) return 0.8;
            return 0.1;
        })
        .attr('stroke-width', d => {
            if (d.source.id === nodeId || d.target.id === nodeId) {
                return Math.sqrt(d.weight || 1) * 2;
            }
            return Math.sqrt(d.weight || 1);
        });

    // Update label appearances
    label.transition()
        .duration(300)
        .attr('opacity', d => {
            if (d.id === nodeId || connectedNodeIds.has(d.id)) return 1;
            return 0.2;
        });

    // Center on node with smooth zoom
    focusNode(nodeId);

    // Show connected entities panel
    showConnectedEntities(nodeData);
}

// Focus camera on specific node
function focusNode(nodeId) {
    const nodeData = networkData.nodes.find(n => n.id === nodeId);
    if (!nodeData || !svg || !zoom) return;

    const container = document.getElementById('network-container');
    const width = container.clientWidth;
    const height = container.clientHeight;

    const scale = 1.5;
    const x = -nodeData.x * scale + width / 2;
    const y = -nodeData.y * scale + height / 2;

    svg.transition()
        .duration(750)
        .call(zoom.transform, d3.zoomIdentity.translate(x, y).scale(scale));
}

// Get connected nodes
function getConnectedNodes(nodeId) {
    const connected = new Set();

    networkData.edges.forEach(edge => {
        if (edge.source.id === nodeId) connected.add(edge.target.id);
        if (edge.target.id === nodeId) connected.add(edge.source.id);
    });

    return connected;
}

// Show connected entities panel
function showConnectedEntities(node) {
    const panel = document.getElementById('connected-entities-panel');
    const connectedNodeIds = getConnectedNodes(node.id);

    // Update panel header
    document.getElementById('connected-entity-name').textContent = formatEntityName(node.id);
    document.getElementById('connected-count').textContent = connectedNodeIds.size;
    document.getElementById('connected-documents').textContent = node.total_documents || 0;
    document.getElementById('connected-billionaire').textContent = node.is_billionaire ? 'Yes' : 'No';

    // Build connections list
    const connections = [];
    networkData.edges.forEach(edge => {
        if (edge.source.id === node.id) {
            connections.push({
                name: edge.target.id,
                weight: edge.weight || 1
            });
        } else if (edge.target.id === node.id) {
            connections.push({
                name: edge.source.id,
                weight: edge.weight || 1
            });
        }
    });

    // Sort by connection strength
    connections.sort((a, b) => b.weight - a.weight);

    // Render connections list
    const connectionsList = document.getElementById('connections-list');

    if (connections.length === 0) {
        connectionsList.innerHTML = '<div class="no-connections">No connections found</div>';
    } else {
        connectionsList.innerHTML = connections.map(conn => {
            // Format name to "Lastname, Firstname" and escape HTML
            const formattedName = formatEntityName(conn.name);
            const escapedName = formattedName.replace(/&/g, '&amp;')
                                         .replace(/</g, '&lt;')
                                         .replace(/>/g, '&gt;')
                                         .replace(/"/g, '&quot;')
                                         .replace(/'/g, '&#39;');

            return `
            <div class="connection-item" onclick="selectNode('${conn.name.replace(/'/g, "\\'")}')">
                <span class="entity-name">${escapedName}</span>
                <span class="connection-strength">${conn.weight} co-occurrence${conn.weight > 1 ? 's' : ''}</span>
            </div>
            `;
        }).join('');
    }

    panel.style.display = 'flex';
}

// Clear selection
function clearSelection() {
    selectedNode = null;

    if (node) {
        node.transition()
            .duration(300)
            .attr('r', d => Math.max(5, Math.sqrt(d.connection_count || 1) * 3))
            .attr('opacity', d => visibleNodes.has(d.id) ? 1 : 0.2)
            .attr('filter', null);
    }

    if (link) {
        link.transition()
            .duration(300)
            .attr('stroke-opacity', 0.6)
            .attr('stroke-width', d => Math.sqrt(d.weight || 1));
    }

    if (label) {
        label.transition()
            .duration(300)
            .attr('opacity', d => visibleNodes.has(d.id) ? 1 : 0.2);
    }

    document.getElementById('connected-entities-panel').style.display = 'none';
}

// Edge tooltip functionality
let edgeTooltip = null;

function showEdgeTooltip(event, edgeData) {
    // Create tooltip if doesn't exist
    if (!edgeTooltip) {
        edgeTooltip = d3.select('body')
            .append('div')
            .attr('class', 'edge-tooltip')
            .style('position', 'absolute')
            .style('pointer-events', 'none')
            .style('background', 'var(--bg-secondary)')
            .style('border', '1px solid var(--border-color)')
            .style('border-radius', '8px')
            .style('padding', '12px')
            .style('font-size', '12px')
            .style('box-shadow', '0 4px 12px rgba(0, 0, 0, 0.3)')
            .style('z-index', '10000')
            .style('max-width', '300px')
            .style('opacity', 0);
    }

    const sourceName = edgeData.source.id || edgeData.source;
    const targetName = edgeData.target.id || edgeData.target;
    const weight = edgeData.weight || 1;
    const contexts = edgeData.contexts || ['unknown'];
    const relType = edgeData.relationship_type || 'FLEW_TOGETHER';

    const contextText = contexts.map(c => {
        if (c === 'flight_log') return 'Flight Logs';
        if (c === 'contact_book') return 'Contact Book';
        if (c === 'document') return 'Documents';
        return c;
    }).join(', ');

    // Get relationship type info (defined earlier in initializeNetworkGraph)
    const typeColors = {
        FLEW_TOGETHER: '#0969da',
        BUSINESS: '#8250df',
        FAMILY: '#cf222e',
        LEGAL: '#bf8700',
        EMPLOYMENT: '#1a7f37',
        UNKNOWN: 'var(--border-color)'
    };
    const typeLabels = {
        FLEW_TOGETHER: 'Flew Together',
        BUSINESS: 'Business Partner',
        FAMILY: 'Family Member',
        LEGAL: 'Legal/Attorney',
        EMPLOYMENT: 'Employment',
        UNKNOWN: 'Connection'
    };
    const relColor = typeColors[relType] || typeColors.UNKNOWN;
    const relLabel = typeLabels[relType] || typeLabels.UNKNOWN;

    // Determine strength tier
    let strengthTier = 'Thin';
    if (weight >= 21) strengthTier = 'Very Bold';
    else if (weight >= 11) strengthTier = 'Bold';
    else if (weight >= 6) strengthTier = 'Medium';
    else if (weight >= 3) strengthTier = 'Light';

    const tooltipContent = `
        <div style="margin-bottom: 8px;">
            <strong style="color: ${relColor};">${weight} connection${weight > 1 ? 's' : ''}</strong>
            <span style="color: var(--text-secondary); font-size: 10px; margin-left: 8px;">(${strengthTier})</span>
        </div>
        <div style="margin-bottom: 8px;">
            <div style="display: inline-block; width: 12px; height: 3px; background: ${relColor}; margin-right: 6px; vertical-align: middle;"></div>
            <strong style="color: ${relColor};">${relLabel}</strong>
        </div>
        <div style="margin-bottom: 4px;">
            <strong>Between:</strong><br/>
            ${formatEntityName(sourceName)} ↔ ${formatEntityName(targetName)}
        </div>
        <div style="color: var(--text-secondary); font-size: 11px; margin-top: 8px;">
            <strong>Source:</strong> ${contextText}
        </div>
        <div style="color: var(--text-tertiary); font-size: 10px; margin-top: 8px; font-style: italic;">
            Click for details
        </div>
    `;

    edgeTooltip
        .html(tooltipContent)
        .style('left', (event.pageX + 15) + 'px')
        .style('top', (event.pageY - 15) + 'px')
        .transition()
        .duration(200)
        .style('opacity', 1);
}

function hideEdgeTooltip() {
    if (edgeTooltip) {
        edgeTooltip
            .transition()
            .duration(200)
            .style('opacity', 0);
    }
}

// Connection details panel
function showConnectionDetailsPanel(edgeData) {
    const panel = document.getElementById('connection-details-panel');
    if (!panel) {
        createConnectionDetailsPanel();
        return showConnectionDetailsPanel(edgeData);
    }

    const sourceName = edgeData.source.id || edgeData.source;
    const targetName = edgeData.target.id || edgeData.target;
    const weight = edgeData.weight || 1;
    const contexts = edgeData.contexts || ['unknown'];
    const relType = edgeData.relationship_type || 'FLEW_TOGETHER';

    // Escape HTML in names
    const escapedSource = sourceName.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    const escapedTarget = targetName.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

    // Get relationship type display info
    const typeColors = {
        FLEW_TOGETHER: '#0969da',
        BUSINESS: '#8250df',
        FAMILY: '#cf222e',
        LEGAL: '#bf8700',
        EMPLOYMENT: '#1a7f37'
    };
    const typeLabels = {
        FLEW_TOGETHER: 'Flew Together',
        BUSINESS: 'Business Partnership',
        FAMILY: 'Family Relationship',
        LEGAL: 'Legal/Attorney',
        EMPLOYMENT: 'Employment'
    };
    const relColor = typeColors[relType] || '#0969da';
    const relLabel = typeLabels[relType] || 'Connection';

    const contextsList = contexts.map(c => {
        let displayName = c;
        let description = '';

        if (c === 'flight_log') {
            displayName = 'Flight Logs';
            description = 'Appeared together on flight passenger lists';
        } else if (c === 'contact_book') {
            displayName = 'Contact Book';
            description = 'Both appear in contact records';
        } else if (c === 'document') {
            displayName = 'Documents';
            description = 'Co-mentioned in document analysis';
        }

        return `
            <div style="padding: 8px; background: var(--bg-tertiary); border-radius: 4px; margin-bottom: 8px;">
                <div style="font-weight: 600; color: var(--accent-blue);">${displayName}</div>
                <div style="font-size: 11px; color: var(--text-secondary); margin-top: 4px;">${description}</div>
            </div>
        `;
    }).join('');

    panel.innerHTML = `
        <div class="panel-header" style="position: sticky; top: 0; z-index: 101; background: var(--bg-secondary); margin: -20px -20px 0 -20px; padding: 16px 20px; border-bottom: 1px solid var(--border-color); border-radius: 12px 12px 0 0;">
            <div style="flex: 1;">
                <h3 style="margin: 0 0 8px 0; font-size: 16px;">Connection Details</h3>
                <div style="font-size: 13px; color: var(--text-secondary);">
                    ${escapedSource} ↔ ${escapedTarget}
                </div>
            </div>
            <button onclick="closeConnectionDetails()" class="close-panel-btn">×</button>
        </div>

        <div class="panel-scrollable-content" style="padding: 20px;">
            <div style="background: var(--bg-tertiary); border-radius: 8px; padding: 16px; margin-bottom: 16px;">
                <div style="margin-bottom: 12px;">
                    <span style="display: inline-block; padding: 6px 12px; background: ${relColor}; color: white; border-radius: 4px; font-size: 12px; font-weight: 600;">
                        ${relLabel}
                    </span>
                </div>
                <div style="font-size: 24px; font-weight: 700; color: var(--accent-blue); margin-bottom: 4px;">
                    ${weight}
                </div>
                <div style="font-size: 12px; color: var(--text-secondary);">
                    Total connection${weight > 1 ? 's' : ''}
                </div>
            </div>

            <div style="margin-bottom: 16px;">
                <h4 style="font-size: 13px; margin: 0 0 12px 0; color: var(--text-primary);">Data Sources</h4>
                ${contextsList}
            </div>

            <div style="font-size: 11px; color: var(--text-tertiary); padding: 12px; background: var(--bg-tertiary); border-radius: 4px; border-left: 3px solid var(--accent-blue);">
                <strong>Note:</strong> Co-occurrences represent documented instances where these entities appear together in source materials.
                This includes flight manifests, contact lists, and other available documents.
            </div>

            <div style="display: flex; gap: 8px; margin-top: 16px;">
                <button onclick="selectNode('${sourceName.replace(/'/g, "\\'")}'); closeConnectionDetails();"
                        style="flex: 1; padding: 8px; background: var(--accent-blue); color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">
                    View ${escapedSource}
                </button>
                <button onclick="selectNode('${targetName.replace(/'/g, "\\'")}'); closeConnectionDetails();"
                        style="flex: 1; padding: 8px; background: var(--accent-blue); color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">
                    View ${escapedTarget}
                </button>
            </div>
        </div>
    `;

    panel.style.display = 'block';
}

function createConnectionDetailsPanel() {
    const panel = document.createElement('div');
    panel.id = 'connection-details-panel';
    panel.style.cssText = `
        position: fixed;
        right: 20px;
        top: 100px;
        width: 350px;
        max-height: calc(100vh - 140px);
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
        z-index: 1000;
        display: none;
        overflow-y: auto;
        overflow-x: hidden;
    `;
    document.body.appendChild(panel);
}

function closeConnectionDetails() {
    const panel = document.getElementById('connection-details-panel');
    if (panel) {
        panel.style.display = 'none';
    }
}

// Search functionality
function handleNetworkSearch(query) {
    const clearBtn = document.querySelector('.search-clear-btn');
    const searchInfo = document.getElementById('search-results-info');
    const searchNav = document.getElementById('search-navigation');

    if (!query.trim()) {
        clearNetworkSearch();
        return;
    }

    clearBtn.style.display = 'block';

    // Search for matching nodes
    const lowerQuery = query.toLowerCase();
    searchResults = networkData.nodes.filter(n =>
        n.id.toLowerCase().includes(lowerQuery)
    );

    if (searchResults.length === 0) {
        searchInfo.textContent = 'No matches found';
        searchNav.style.display = 'none';

        // Reset all nodes to visible filter state
        if (node) {
            node.transition()
                .duration(300)
                .attr('opacity', d => visibleNodes.has(d.id) ? 1 : 0.2);
        }
        if (label) {
            label.transition()
                .duration(300)
                .attr('opacity', d => visibleNodes.has(d.id) ? 1 : 0.2);
        }
    } else {
        searchInfo.textContent = `${searchResults.length} match${searchResults.length > 1 ? 'es' : ''} found`;
        searchNav.style.display = searchResults.length > 1 ? 'block' : 'none';
        currentSearchIndex = 0;

        // Highlight matching nodes
        highlightSearchResults();

        // Focus on first result
        if (searchResults.length > 0) {
            focusNode(searchResults[0].id);
        }
    }
}

function highlightSearchResults() {
    const matchingIds = new Set(searchResults.map(n => n.id));

    if (node) {
        node.transition()
            .duration(300)
            .attr('opacity', d => matchingIds.has(d.id) ? 1 : 0.2)
            .attr('filter', d => matchingIds.has(d.id) ? 'url(#glow)' : null);
    }

    if (label) {
        label.transition()
            .duration(300)
            .attr('opacity', d => matchingIds.has(d.id) ? 1 : 0.2);
    }
}

function navigateSearchResults(direction) {
    if (searchResults.length === 0) return;

    if (direction === 'prev') {
        currentSearchIndex = (currentSearchIndex - 1 + searchResults.length) % searchResults.length;
    } else {
        currentSearchIndex = (currentSearchIndex + 1) % searchResults.length;
    }

    const currentNode = searchResults[currentSearchIndex];
    focusNode(currentNode.id);

    const searchInfo = document.getElementById('search-results-info');
    searchInfo.textContent = `${currentSearchIndex + 1} of ${searchResults.length} matches`;
}

function clearNetworkSearch() {
    document.getElementById('network-search').value = '';
    document.querySelector('.search-clear-btn').style.display = 'none';
    document.getElementById('search-results-info').textContent = '';
    document.getElementById('search-navigation').style.display = 'none';

    searchResults = [];
    currentSearchIndex = 0;

    // Reset node appearances based on current filters
    applyFilters();
}

// Filter functionality
function applyFilters() {
    if (!networkData || !node) {
        // Update filter checkboxes state
        activeFilters.billionaires = document.getElementById('filter-billionaires')?.checked || false;
        activeFilters.high = document.getElementById('filter-high')?.checked || false;
        activeFilters.medium = document.getElementById('filter-medium')?.checked || false;
        activeFilters.low = document.getElementById('filter-low')?.checked || false;
        return;
    }

    activeFilters.billionaires = document.getElementById('filter-billionaires').checked;
    activeFilters.high = document.getElementById('filter-high').checked;
    activeFilters.medium = document.getElementById('filter-medium').checked;
    activeFilters.low = document.getElementById('filter-low').checked;

    // Determine which nodes pass filters
    visibleNodes.clear();

    networkData.nodes.forEach(n => {
        let passes = true;

        // If any filter is active, node must match at least one
        const anyFilterActive = Object.values(activeFilters).some(v => v);

        if (anyFilterActive) {
            passes = false;

            if (activeFilters.billionaires && n.is_billionaire) passes = true;
            if (activeFilters.high && (n.connection_count || 0) > 10) passes = true;
            if (activeFilters.medium && (n.connection_count || 0) >= 5 && (n.connection_count || 0) <= 10) passes = true;
            if (activeFilters.low && (n.connection_count || 0) < 5) passes = true;
        }

        if (passes) {
            visibleNodes.add(n.id);
        }
    });

    // Update visual appearance
    node.transition()
        .duration(300)
        .attr('opacity', d => visibleNodes.has(d.id) ? 1 : 0.2);

    label.transition()
        .duration(300)
        .attr('opacity', d => visibleNodes.has(d.id) ? 1 : 0.2);

    updateFilteredCount();
}

function updateFilteredCount() {
    const filterCount = document.getElementById('filter-count');
    if (filterCount) {
        const total = networkData ? networkData.nodes.length : 0;
        filterCount.textContent = `Showing: ${visibleNodes.size} of ${total} nodes`;
    }
}

// Update network controls
function updateLinkDistance(value) {
    document.getElementById('link-distance-value').textContent = value;
    if (simulation) {
        simulation.force('link').distance(value);
        simulation.alpha(0.3).restart();
    }
}

function updateChargeStrength(value) {
    document.getElementById('charge-value').textContent = value;
    if (simulation) {
        simulation.force('charge').strength(value);
        simulation.alpha(0.3).restart();
    }
}

// Progressive Network Loading Controls
let sliderUpdateTimeout = null;

/**
 * Update the network visualization with specified number of connections
 * @param {number} count - Number of connections to display
 */
function updateNetworkEdges(count) {
    if (!window.networkEdges || !window.networkEdges.all) {
        console.warn('Network edges data not available');
        return;
    }

    // Show loading indicator
    const loadingIndicator = document.getElementById('loading-indicator');
    if (loadingIndicator) {
        loadingIndicator.classList.add('active');
    }

    // Clamp count to valid range
    const totalEdges = window.networkEdges.all.length;
    const edgeCount = Math.max(100, Math.min(count, totalEdges));

    // Get subset of edges
    const newEdges = window.networkEdges.all.slice(0, edgeCount);

    // Update stored current edges
    window.networkEdges.current = newEdges;
    window.networkEdges.displayed = edgeCount;

    // Update D3 visualization
    if (link && simulation && g) {
        // Helper function to get edge color
        const getEdgeColorLocal = (edge) => {
            const type = edge.relationship_type || 'FLEW_TOGETHER';
            const CONNECTION_TYPES = {
                FLEW_TOGETHER: { color: '#0969da' },
                BUSINESS: { color: '#8250df' },
                FAMILY: { color: '#cf222e' },
                LEGAL: { color: '#bf8700' },
                EMPLOYMENT: { color: '#1a7f37' },
                UNKNOWN: { color: '#30363d' }
            };
            return CONNECTION_TYPES[type]?.color || CONNECTION_TYPES.UNKNOWN.color;
        };

        // Helper function to get edge thickness
        const getEdgeThicknessLocal = (weight) => {
            if (weight >= 21) return 8;
            if (weight >= 11) return 6.5;
            if (weight >= 6) return 5;
            if (weight >= 3) return 3;
            return 1.5;
        };

        // Select the links group and update data
        const linkSelection = g.select('g').selectAll('line')
            .data(newEdges, d => {
                // Create unique key for each link
                const sourceId = d.source.id || d.source;
                const targetId = d.target.id || d.target;
                return `${sourceId}-${targetId}`;
            });

        // Remove old links with transition
        linkSelection.exit()
            .transition()
            .duration(300)
            .attr('stroke-opacity', 0)
            .remove();

        // Add new links with event handlers
        const newLinks = linkSelection.enter()
            .append('line')
            .attr('stroke', d => getEdgeColorLocal(d))
            .attr('stroke-width', d => getEdgeThicknessLocal(d.weight || 1))
            .attr('stroke-opacity', 0)
            .style('cursor', 'pointer')
            .on('mouseover', function(event, d) {
                // Highlight edge on hover
                d3.select(this)
                    .transition()
                    .duration(200)
                    .attr('stroke-opacity', 1)
                    .attr('stroke-width', getEdgeThicknessLocal(d.weight || 1) * 1.3);

                // Show tooltip if function exists
                if (typeof showEdgeTooltip === 'function') {
                    showEdgeTooltip(event, d);
                }
            })
            .on('mouseout', function(event, d) {
                // Reset edge
                if (!selectedNode || (d.source.id !== selectedNode && d.target.id !== selectedNode)) {
                    d3.select(this)
                        .transition()
                        .duration(200)
                        .attr('stroke-opacity', 0.6)
                        .attr('stroke-width', getEdgeThicknessLocal(d.weight || 1));
                }

                // Hide tooltip if function exists
                if (typeof hideEdgeTooltip === 'function') {
                    hideEdgeTooltip();
                }
            })
            .on('click', (event, d) => {
                event.stopPropagation();
                if (typeof showConnectionDetailsPanel === 'function') {
                    showConnectionDetailsPanel(d);
                }
            });

        // Fade in new links
        newLinks.transition()
            .duration(300)
            .attr('stroke-opacity', 0.6);

        // Merge and update global link reference
        link = newLinks.merge(linkSelection)
            .attr('stroke', d => getEdgeColorLocal(d))
            .attr('stroke-width', d => getEdgeThicknessLocal(d.weight || 1));

        // Update simulation with new edges
        simulation.force('link').links(newEdges);
        simulation.alpha(0.3).restart();
    }

    // Update UI displays
    updateConnectionControls();

    // Hide loading indicator after short delay
    setTimeout(() => {
        if (loadingIndicator) {
            loadingIndicator.classList.remove('active');
        }
    }, 500);
}

/**
 * Update connection control UI elements
 */
function updateConnectionControls() {
    if (!window.networkEdges) return;

    const currentCount = window.networkEdges.displayed;
    const totalCount = window.networkEdges.all.length;

    // Update count display
    const shownElement = document.getElementById('connections-shown');
    const totalElement = document.getElementById('connections-total');
    const slider = document.getElementById('connections-slider');

    if (shownElement) {
        shownElement.textContent = currentCount.toLocaleString();
    }
    if (totalElement) {
        totalElement.textContent = totalCount.toLocaleString();
    }
    if (slider) {
        slider.value = currentCount;
        slider.max = totalCount;
    }

    // Update button states
    const loadMoreBtn = document.getElementById('load-more-btn');
    const showAllBtn = document.getElementById('show-all-btn');
    const resetBtn = document.getElementById('reset-connections-btn');

    const isMaxed = currentCount >= totalCount;
    const isDefault = currentCount === 300;

    if (loadMoreBtn) {
        loadMoreBtn.disabled = isMaxed;
        loadMoreBtn.textContent = isMaxed ? 'All Loaded' : 'Load More (+100)';
    }

    if (showAllBtn) {
        showAllBtn.disabled = isMaxed;
    }

    if (resetBtn) {
        resetBtn.disabled = isDefault;
    }
}

/**
 * Handle slider input with debouncing
 * @param {string|number} value - Slider value
 */
function handleConnectionSlider(value) {
    const count = parseInt(value, 10);

    // Update display immediately for responsiveness
    const shownElement = document.getElementById('connections-shown');
    if (shownElement) {
        shownElement.textContent = count.toLocaleString();
    }

    // Debounce the actual network update
    if (sliderUpdateTimeout) {
        clearTimeout(sliderUpdateTimeout);
    }

    sliderUpdateTimeout = setTimeout(() => {
        updateNetworkEdges(count);
    }, 200);
}

/**
 * Load 100 more connections
 */
function loadMoreConnections() {
    if (!window.networkEdges) return;

    const currentCount = window.networkEdges.displayed;
    const totalCount = window.networkEdges.all.length;
    const newCount = Math.min(currentCount + 100, totalCount);

    // Update slider
    const slider = document.getElementById('connections-slider');
    if (slider) {
        slider.value = newCount;
    }

    updateNetworkEdges(newCount);
}

/**
 * Show all connections (may impact performance)
 */
function showAllConnections() {
    if (!window.networkEdges) return;

    const totalCount = window.networkEdges.all.length;

    // Confirm if showing a very large number
    if (totalCount > 1000) {
        const confirmed = confirm(
            `Warning: Loading all ${totalCount.toLocaleString()} connections may impact performance.\n\nContinue?`
        );
        if (!confirmed) return;
    }

    // Update slider
    const slider = document.getElementById('connections-slider');
    if (slider) {
        slider.value = totalCount;
    }

    updateNetworkEdges(totalCount);
}

/**
 * Reset to default connection count (300)
 */
function resetConnections() {
    const defaultCount = 300;

    // Update slider
    const slider = document.getElementById('connections-slider');
    if (slider) {
        slider.value = defaultCount;
    }

    updateNetworkEdges(defaultCount);
}

// Chat sidebar toggle
function toggleChatSidebar() {
    const sidebar = document.getElementById('chat-sidebar');
    const icon = document.getElementById('toggle-icon');

    sidebar.classList.toggle('collapsed');
    icon.textContent = sidebar.classList.contains('collapsed') ? '▶' : '◀';
}

// Chat functionality
function handleChatKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

async function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();

    if (!message) return;

    addChatMessage('user', message);
    input.value = '';

    const loadingId = 'loading-' + Date.now();
    addChatMessage('loading', 'Searching and thinking...', loadingId);

    try {
        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            credentials: 'include',  // Include HTTP Basic Auth credentials
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message })
        });

        if (!response.ok) {
            throw new Error('Chat request failed');
        }

        const data = await response.json();

        const loadingMsg = document.getElementById(loadingId);
        if (loadingMsg) loadingMsg.remove();

        addChatMessage('assistant', data.response);

        if (data.search_results) {
            if (data.search_results.entities && data.search_results.entities.length > 0) {
                const entitiesText = 'Found entities: ' + data.search_results.entities.map(e => formatEntityName(e.name)).join(', ');
                addChatMessage('system', entitiesText);
            }
            if (data.search_results.documents && data.search_results.documents.length > 0) {
                const docsText = 'Found documents: ' + data.search_results.documents.length + ' matching files';
                addChatMessage('system', docsText);
            }
        }
    } catch (error) {
        console.error('Chat error:', error);

        const loadingMsg = document.getElementById(loadingId);
        if (loadingMsg) loadingMsg.remove();

        addChatMessage('system', 'Error: Could not get response. The LLM may be unavailable or slow to respond. Please try again.');
    }
}

function addChatMessage(type, content, id) {
    const messagesContainer = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${type}`;

    if (id) {
        messageDiv.id = id;
    }

    if (type === 'loading') {
        messageDiv.innerHTML = `
            ${content}
            <div class="loading-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
        `;
    } else if (type === 'assistant') {
        // Render markdown for assistant messages
        messageDiv.innerHTML = renderMarkdown(content);
    } else {
        // Plain text for user and system messages
        messageDiv.textContent = content;
    }

    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Source suggestion modal
function showSourceForm() {
    document.getElementById('source-modal').classList.add('show');
}

function hideSourceForm() {
    document.getElementById('source-modal').classList.remove('show');
    document.getElementById('source-url').value = '';
    document.getElementById('source-description').value = '';
    document.getElementById('source-name').value = '';
}

async function submitSource() {
    const url = document.getElementById('source-url').value.trim();
    const description = document.getElementById('source-description').value.trim();
    const name = document.getElementById('source-name').value.trim();

    if (!url || !description) {
        addChatMessage('system', 'Please provide both URL and description');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/suggest-source`, {
            method: 'POST',
            credentials: 'include',  // Include HTTP Basic Auth credentials
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                url,
                description,
                source_name: name || null
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Submission failed');
        }

        const data = await response.json();
        addChatMessage('system', data.message);
        hideSourceForm();
    } catch (error) {
        console.error('Source submission error:', error);
        addChatMessage('system', error.message);
    }
}

// Close modal when clicking outside
document.addEventListener('click', (event) => {
    const modal = document.getElementById('source-modal');
    if (event.target === modal) {
        hideSourceForm();
    }
});

// Entities list functionality
let allEntitiesData = [];

async function loadEntitiesList() {
    try {
        // Use v2 API for proper entity_type enrichment
        const response = await fetch(`${API_BASE}/v2/entities?limit=1000`, {
            credentials: 'include'  // Include HTTP Basic Auth credentials
        });
        const data = await response.json();
        // Handle paginated response structure
        allEntitiesData = data.entities || data;
        updateEntitiesStats(allEntitiesData);
        renderEntitiesList(allEntitiesData);
    } catch (error) {
        console.error('Failed to load entities:', error);
        document.getElementById('entities-list').innerHTML = '<div class="chat-message system" style="grid-column: 1/-1; text-align: center; padding: 40px;">Failed to load entities</div>';
    }
}

function updateEntitiesStats(entities) {
    if (!entities || entities.length === 0) return;

    // Calculate stats
    const totalCount = entities.length;
    const billionaireCount = entities.filter(e => e.is_billionaire).length;

    // Count entities from different sources (check if entity has data from that source)
    const blackbookCount = entities.filter(e =>
        e.sources && e.sources.includes('black_book')
    ).length;
    const flightsCount = entities.filter(e =>
        (e.flight_count || 0) > 0
    ).length;

    // Update DOM
    const totalEl = document.getElementById('entities-total-count');
    const billionaireEl = document.getElementById('entities-billionaire-count');
    const blackbookEl = document.getElementById('entities-blackbook-count');
    const flightsEl = document.getElementById('entities-flights-count');

    if (totalEl) totalEl.textContent = totalCount;
    if (billionaireEl) billionaireEl.textContent = billionaireCount;
    if (blackbookEl) blackbookEl.textContent = blackbookCount || '~1,740';
    if (flightsEl) flightsEl.textContent = flightsCount || '~387';
}

function renderEntitiesList(entities) {
    const container = document.getElementById('entities-list');

    if (!entities || entities.length === 0) {
        container.innerHTML = '<div class="chat-message system" style="grid-column: 1/-1; text-align: center; padding: 40px;">No entities found</div>';
        return;
    }

    // Use consolidated renderEntity() function for all entity cards
    container.innerHTML = entities.map(entity => renderEntity(entity, 'card')).join('');

    // Initialize Lucide icons after rendering entities
    if (typeof lucide !== 'undefined') {
        lucide.createIcons({
            attrs: {
                'stroke-width': 2,
                width: 16,
                height: 16
            }
        });
    }
}

function filterEntities(searchQuery) {
    const filter = document.getElementById('entity-filter').value;
    const query = searchQuery.toLowerCase();

    let filtered = allEntitiesData;

    // Apply text search filter
    if (query) {
        filtered = filtered.filter(entity =>
            entity.name.toLowerCase().includes(query)
        );
    }

    // Apply advanced filters
    if (filter === 'billionaire') {
        filtered = filtered.filter(entity => entity.is_billionaire);
    } else if (filter === 'high-connections') {
        filtered = filtered.filter(entity => (entity.connection_count || 0) > 10);
    } else if (filter === 'medium-connections') {
        filtered = filtered.filter(entity => {
            const count = entity.connection_count || 0;
            return count >= 5 && count <= 10;
        });
    } else if (filter === 'low-connections') {
        filtered = filtered.filter(entity => (entity.connection_count || 0) < 5);
    } else if (filter.startsWith('type:')) {
        const type = filter.substring(5); // Remove 'type:' prefix
        // Use entity_type field from API v2 instead of keyword detection
        filtered = filtered.filter(entity => {
            const entityType = entity.entity_type || detectEntityType(entity.name);
            return entityType === type;
        });
    } else if (filter.startsWith('tag:')) {
        const tag = filter.substring(4).toLowerCase(); // Remove 'tag:' prefix
        filtered = filtered.filter(entity => {
            // Use tags field from API v2 if available
            const tags = entity.tags || entityTags[entity.name]?.tags || [];
            return tags.some(t => t.toLowerCase() === tag);
        });
    } else if (filter.startsWith('source:')) {
        const source = filter.substring(7); // Remove 'source:' prefix
        filtered = filtered.filter(entity => {
            // Check if entity appears in the specified source
            if (source === 'black_book') {
                return entity.in_black_book || entityTags[entity.name]?.sources?.includes('black_book') || false;
            } else if (source === 'flight_logs') {
                return (entity.flight_count || 0) > 0;
            } else if (source === 'documents') {
                return (entity.total_documents || entity.document_count || 0) > 0;
            }
            return false;
        });
    }

    renderEntitiesList(filtered);
}

function showEntityDetails(entityName) {
    const entity = allEntitiesData.find(e => e.name === entityName);
    if (!entity) {
        console.warn('Entity not found:', entityName);
        return;
    }

    // BUG FIX #2: Properly switch to network tab and wait for rendering
    switchTab('network');

    // Wait for tab switch to complete, then render/select
    setTimeout(() => {
        if (!simulation) {
            renderNetwork().then(() => {
                // Additional delay to ensure D3 simulation has started
                setTimeout(() => {
                    selectNode(entityName);
                }, 300);
            });
        } else {
            // Ensure node exists in the network before selecting
            const nodeExists = networkData && networkData.nodes.find(n => n.id === entityName);
            if (nodeExists) {
                selectNode(entityName);
            } else {
                console.warn('Node not found in network:', entityName);
                addChatMessage('system', `Entity "${entityName}" is not in the network graph (may have no connections)`);
            }
        }
    }, 100);
}

// BUG FIX #3: Handle document links for entities
async function showEntityDocuments(entityName) {
    // Navigate to documents tab and filter by entity
    if (typeof viewEntityDocuments === 'function') {
        viewEntityDocuments(entityName);
    } else {
        console.error('viewEntityDocuments function not available');
        addChatMessage('system',
            `Document search is loading. Please try again in a moment.`
        );
    }
}

// ===== SOURCES TAB FUNCTIONS =====

// Sources feature state
let sourcesData = null;
let filteredSources = null;
let currentSortColumn = 'total';
let currentSortDirection = 'desc';

async function loadSources() {
    // Only load once
    if (sourcesData) {
        renderSourcesTable();
        renderCrossSourceAnalysis();
        return;
    }

    try {
        // Load master document index
        const response = await fetch(`${API_BASE}/sources/index`, {
            credentials: 'include'
        });

        if (!response.ok) {
            throw new Error('Failed to load sources');
        }

        sourcesData = await response.json();
        filteredSources = sourcesData.sources;

        // Update summary cards
        document.getElementById('total-files').textContent = sourcesData.total_files.toLocaleString();
        document.getElementById('unique-docs').textContent = sourcesData.unique_documents.toLocaleString();
        document.getElementById('duplicates-removed').textContent =
            (sourcesData.total_files - sourcesData.unique_documents).toLocaleString();
        const dedupRate = ((sourcesData.total_files - sourcesData.unique_documents) / sourcesData.total_files * 100).toFixed(1);
        document.getElementById('dedup-rate').textContent = dedupRate + '%';

        // Render sources table
        renderSourcesTable();

        // Render cross-source analysis
        renderCrossSourceAnalysis();

    } catch (error) {
        console.error('Error loading sources:', error);
        document.getElementById('total-files').textContent = 'Error';
        document.getElementById('unique-docs').textContent = 'Error';
        document.getElementById('duplicates-removed').textContent = 'Error';
        document.getElementById('dedup-rate').textContent = 'Error';

        document.getElementById('sources-tbody').innerHTML = `
            <tr>
                <td colspan="6" style="text-align: center; padding: 40px;">
                    <div class="chat-message system">Error loading sources: ${error.message}</div>
                </td>
            </tr>
        `;
    }
}

function renderSourcesTable() {
    const tbody = document.getElementById('sources-tbody');
    tbody.innerHTML = '';

    if (!filteredSources || filteredSources.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" style="text-align: center; padding: 40px;">
                    <div class="chat-message system">No sources match your filter</div>
                </td>
            </tr>
        `;
        return;
    }

    filteredSources.forEach(source => {
        const row = document.createElement('tr');

        const duplicates = source.total_files - source.unique_docs;
        const dedupRate = source.total_files > 0 ? ((duplicates / source.total_files) * 100).toFixed(1) : '0.0';

        row.innerHTML = `
            <td><strong>${source.name}</strong></td>
            <td>${source.total_files.toLocaleString()}</td>
            <td>${source.unique_docs.toLocaleString()}</td>
            <td>${duplicates.toLocaleString()}</td>
            <td>${dedupRate}%</td>
            <td>${formatFileSize(source.total_size)}</td>
        `;

        tbody.appendChild(row);
    });
}

function filterSources(filterType) {
    if (!sourcesData) return;

    // Update active button
    document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');

    // Filter sources
    if (filterType === 'all') {
        filteredSources = sourcesData.sources;
    } else if (filterType === 'downloaded') {
        filteredSources = sourcesData.sources.filter(s => s.status === 'downloaded');
    } else if (filterType === 'large') {
        filteredSources = sourcesData.sources.filter(s => s.total_files > 1000);
    }

    // Re-apply search if active
    const searchValue = document.getElementById('source-search').value;
    if (searchValue.trim()) {
        searchSources(searchValue);
    } else {
        renderSourcesTable();
    }
}

function searchSources(query) {
    if (!sourcesData) return;

    const currentFilter = document.querySelector('.filter-btn.active')?.textContent.toLowerCase();
    let baseList = sourcesData.sources;

    // Apply filter first
    if (currentFilter && currentFilter.includes('downloaded')) {
        baseList = baseList.filter(s => s.status === 'downloaded');
    } else if (currentFilter && currentFilter.includes('large')) {
        baseList = baseList.filter(s => s.total_files > 1000);
    }

    // Then apply search
    if (!query.trim()) {
        filteredSources = baseList;
    } else {
        const lowerQuery = query.toLowerCase();
        filteredSources = baseList.filter(s =>
            s.name.toLowerCase().includes(lowerQuery)
        );
    }

    renderSourcesTable();
}

function sortSourcesTable(column) {
    if (!filteredSources) return;

    // Toggle direction if clicking same column
    if (currentSortColumn === column) {
        currentSortDirection = currentSortDirection === 'asc' ? 'desc' : 'asc';
    } else {
        currentSortColumn = column;
        currentSortDirection = 'desc';
    }

    // Sort the filtered sources
    filteredSources.sort((a, b) => {
        let valA, valB;

        switch (column) {
            case 'name':
                valA = a.name.toLowerCase();
                valB = b.name.toLowerCase();
                break;
            case 'total':
                valA = a.total_files;
                valB = b.total_files;
                break;
            case 'unique':
                valA = a.unique_docs;
                valB = b.unique_docs;
                break;
            case 'duplicates':
                valA = a.total_files - a.unique_docs;
                valB = b.total_files - b.unique_docs;
                break;
            case 'rate':
                valA = a.total_files > 0 ? (a.total_files - a.unique_docs) / a.total_files : 0;
                valB = b.total_files > 0 ? (b.total_files - b.unique_docs) / b.total_files : 0;
                break;
            case 'size':
                valA = a.total_size;
                valB = b.total_size;
                break;
            default:
                return 0;
        }

        // Compare values
        if (typeof valA === 'string') {
            return currentSortDirection === 'asc' ?
                valA.localeCompare(valB) : valB.localeCompare(valA);
        } else {
            return currentSortDirection === 'asc' ?
                valA - valB : valB - valA;
        }
    });

    renderSourcesTable();
}

function formatFileSize(bytes) {
    if (!bytes || bytes === 0) return '0 B';
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    return (bytes / (1024 * 1024 * 1024)).toFixed(1) + ' GB';
}

function renderCrossSourceAnalysis() {
    const container = document.getElementById('duplicate-details');

    if (!sourcesData || !sourcesData.cross_source_duplicates || sourcesData.cross_source_duplicates.length === 0) {
        container.innerHTML = '<div style="text-align: center; padding: 20px;"><div class="chat-message system">No cross-source duplicates found.</div></div>';
        return;
    }

    let html = '';
    const duplicates = sourcesData.cross_source_duplicates.slice(0, 20); // Top 20

    duplicates.forEach(dup => {
        html += `
            <div class="duplicate-item">
                <div class="duplicate-item-name">${dup.document}</div>
                <div class="duplicate-item-sources">
                    Found in ${dup.sources.length} sources (${dup.file_count} total files):
                    ${dup.sources.map(s => `<span class="source-badge">${s}</span>`).join('')}
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}

// ============================================================================
// Pipeline Status Functions
// ============================================================================

let pipelineStatusInterval = null;

// Toggle stage expansion
function toggleStage(stageName) {
    const header = document.querySelector(`#${stageName}-content`).previousElementSibling;
    const content = document.getElementById(`${stageName}-content`);
    const toggle = document.getElementById(`${stageName}-toggle`);
    
    if (content.classList.contains('collapsed')) {
        content.classList.remove('collapsed');
        header.classList.remove('collapsed');
        toggle.textContent = '▼';
    } else {
        content.classList.add('collapsed');
        header.classList.add('collapsed');
        toggle.textContent = '◀';
    }
}

// Update pipeline status (called every 5 seconds when on ingestion tab)
async function updatePipelineStatus() {
    try {
        const response = await fetch(`${API_BASE}/ingestion/status`, {
            credentials: 'include'
        });
        const data = await response.json();

        // Update overview cards
        updatePipelineOverview(data);

        // Update detailed stages
        updateDownloadsStage(data);
        updateConversionStage(data);
        updateEmailsStage(data);
        updateClassificationStage(data);
        updateDeduplicationStage(data);
        updateEntitiesStage(data);

    } catch (error) {
        console.error('Failed to fetch pipeline status:', error);
        showPipelineError(error.message);
    }
}

function updatePipelineOverview(data) {
    // Downloads
    const downloadCount = data.downloads?.total || 0;
    const downloadStatus = data.downloads?.status || 'idle';
    document.getElementById('downloads-count').textContent = downloadCount.toLocaleString();
    updateStatusBadge('downloads-status', downloadStatus);

    // Conversion (OCR)
    const conversionPct = data.progress_percentage || 0;
    document.getElementById('conversion-count').textContent = Math.round(conversionPct) + '%';
    updateStatusBadge('conversion-status', data.status || 'idle');

    // Emails
    const emailsFound = data.documents?.emails_found || 0;
    document.getElementById('emails-count').textContent = emailsFound.toLocaleString();
    updateStatusBadge('emails-status', emailsFound > 0 ? 'complete' : 'idle');

    // Classification
    const classified = data.documents?.classified || 0;
    const totalDocs = data.documents?.total || 0;
    const classifyPct = totalDocs > 0 ? Math.round((classified / totalDocs) * 100) : 0;
    document.getElementById('classification-count').textContent = `${classifyPct}%`;
    updateStatusBadge('classification-status', classified === totalDocs && totalDocs > 0 ? 'complete' : 'in-progress');

    // Deduplication
    const dedupRate = data.deduplication?.rate || 0;
    document.getElementById('dedup-count').textContent = dedupRate.toFixed(1) + '%';
    updateStatusBadge('dedup-status', 'complete');

    // Entities
    const totalEntities = data.entities?.total || 0;
    const networkNodes = data.network?.nodes || 0;
    document.getElementById('entities-count').textContent = totalEntities.toLocaleString();
    updateStatusBadge('entities-status', totalEntities > 0 ? 'complete' : 'idle');
}

function updateStatusBadge(elementId, status) {
    const element = document.getElementById(elementId);
    element.className = `pipeline-status ${status}`;
    
    const statusText = {
        'idle': 'Not started',
        'in-progress': 'In progress...',
        'processing': 'Processing...',
        'complete': 'Complete',
        'failed': 'Failed'
    };
    
    element.textContent = statusText[status] || status;
}

function updateDownloadsStage(data) {
    const downloads = data.downloads || {};
    const summary = document.getElementById('downloads-summary');
    const progress = document.getElementById('downloads-progress');
    const details = document.getElementById('downloads-details');
    
    if (!downloads.total || downloads.total === 0) {
        summary.textContent = 'No active downloads';
        progress.style.width = '0%';
        details.innerHTML = '<div class="loading-message">No download queue information available</div>';
        return;
    }
    
    const completed = downloads.completed || 0;
    const total = downloads.total || 0;
    const pct = total > 0 ? Math.round((completed / total) * 100) : 0;
    
    summary.textContent = `${completed.toLocaleString()} / ${total.toLocaleString()} files`;
    progress.style.width = pct + '%';
    progress.textContent = pct + '%';
    
    if (pct >= 100) {
        progress.classList.add('complete');
    }
    
    details.innerHTML = `
        <div class="detail-item">
            <div class="detail-label">Total Files</div>
            <div class="detail-value">${total.toLocaleString()}</div>
        </div>
        <div class="detail-item">
            <div class="detail-label">Downloaded</div>
            <div class="detail-value">${completed.toLocaleString()}</div>
        </div>
        <div class="detail-item">
            <div class="detail-label">Pending</div>
            <div class="detail-value">${(total - completed).toLocaleString()}</div>
        </div>
        <div class="detail-item">
            <div class="detail-label">Failed</div>
            <div class="detail-value">${downloads.failed || 0}</div>
        </div>
    `;
}

function updateConversionStage(data) {
    const summary = document.getElementById('conversion-summary');
    const progress = document.getElementById('conversion-progress');
    const details = document.getElementById('conversion-details');
    
    const processed = data.files_processed || 0;
    const total = data.total_files || 0;
    const pct = data.progress_percentage || 0;
    
    summary.textContent = `${processed.toLocaleString()} / ${total.toLocaleString()} files (${Math.round(pct)}%)`;
    progress.style.width = pct + '%';
    progress.textContent = Math.round(pct) + '%';
    
    if (pct >= 100) {
        progress.classList.add('complete');
    }
    
    const ocrData = data.ocr || {};
    const rate = ocrData.processing_rate || 0;
    const eta = ocrData.eta_minutes || 0;
    
    details.innerHTML = `
        <div class="detail-item">
            <div class="detail-label">Files Processed</div>
            <div class="detail-value">${processed.toLocaleString()}</div>
        </div>
        <div class="detail-item">
            <div class="detail-label">Total Files</div>
            <div class="detail-value">${total.toLocaleString()}</div>
        </div>
        <div class="detail-item">
            <div class="detail-label">Processing Rate</div>
            <div class="detail-value">${rate.toFixed(1)} files/sec</div>
        </div>
        <div class="detail-item">
            <div class="detail-label">ETA</div>
            <div class="detail-value">${eta > 0 ? Math.round(eta) + ' min' : 'Complete'}</div>
        </div>
        <div class="detail-item">
            <div class="detail-label">Current Source</div>
            <div class="detail-value" style="font-size: 12px;">${data.current_source || 'N/A'}</div>
        </div>
    `;
}

function updateEmailsStage(data) {
    const emailsFound = data.documents?.emails_found || 0;
    const summary = document.getElementById('emails-summary');
    const progress = document.getElementById('emails-progress');
    const details = document.getElementById('emails-details');
    
    summary.textContent = `${emailsFound.toLocaleString()} emails extracted`;
    
    // Assume email extraction is complete if OCR is done
    const isComplete = data.status === 'complete';
    progress.style.width = isComplete ? '100%' : '0%';
    progress.textContent = isComplete ? '100%' : '0%';
    
    if (isComplete) {
        progress.classList.add('complete');
    }
    
    details.innerHTML = `
        <div class="detail-item">
            <div class="detail-label">Emails Found</div>
            <div class="detail-value">${emailsFound.toLocaleString()}</div>
        </div>
        <div class="detail-item">
            <div class="detail-label">Status</div>
            <div class="detail-value">${isComplete ? 'Complete' : 'Waiting for OCR'}</div>
        </div>
        <div class="detail-item">
            <div class="detail-label">Date Range</div>
            <div class="detail-value">Multiple years</div>
        </div>
    `;
}

function updateClassificationStage(data) {
    const classified = data.documents?.classified || 0;
    const total = data.documents?.total || 0;
    const pct = total > 0 ? (classified / total) * 100 : 0;
    
    const summary = document.getElementById('classification-summary');
    const progress = document.getElementById('classification-progress');
    const details = document.getElementById('classification-details');
    
    summary.textContent = `${classified.toLocaleString()} / ${total.toLocaleString()} documents`;
    progress.style.width = pct + '%';
    progress.textContent = Math.round(pct) + '%';
    
    if (pct >= 100) {
        progress.classList.add('complete');
    }
    
    details.innerHTML = `
        <div class="detail-item">
            <div class="detail-label">Classified</div>
            <div class="detail-value">${classified.toLocaleString()}</div>
        </div>
        <div class="detail-item">
            <div class="detail-label">Total Documents</div>
            <div class="detail-value">${total.toLocaleString()}</div>
        </div>
        <div class="detail-item">
            <div class="detail-label">Pending</div>
            <div class="detail-value">${(total - classified).toLocaleString()}</div>
        </div>
        <div class="detail-item">
            <div class="detail-label">Classification Rate</div>
            <div class="detail-value">${pct.toFixed(1)}%</div>
        </div>
    `;
}

function updateDeduplicationStage(data) {
    const dedup = data.deduplication || {};
    const totalFiles = dedup.total_files || 0;
    const uniqueDocs = dedup.unique_documents || 0;
    const duplicates = totalFiles - uniqueDocs;
    const rate = dedup.rate || 0;
    
    const summary = document.getElementById('dedup-summary');
    const progress = document.getElementById('dedup-progress');
    const details = document.getElementById('dedup-details');
    
    summary.textContent = `${duplicates.toLocaleString()} duplicates removed (${rate.toFixed(1)}%)`;
    progress.style.width = '100%';
    progress.textContent = '100%';
    progress.classList.add('complete');
    
    details.innerHTML = `
        <div class="detail-item">
            <div class="detail-label">Total Files</div>
            <div class="detail-value">${totalFiles.toLocaleString()}</div>
        </div>
        <div class="detail-item">
            <div class="detail-label">Unique Documents</div>
            <div class="detail-value">${uniqueDocs.toLocaleString()}</div>
        </div>
        <div class="detail-item">
            <div class="detail-label">Duplicates Removed</div>
            <div class="detail-value">${duplicates.toLocaleString()}</div>
        </div>
        <div class="detail-item">
            <div class="detail-label">Deduplication Rate</div>
            <div class="detail-value">${rate.toFixed(1)}%</div>
        </div>
    `;
}

function updateEntitiesStage(data) {
    const entities = data.entities || {};
    const network = data.network || {};
    const totalEntities = entities.total || 0;
    const inNetwork = entities.in_network || network.nodes || 0;
    const billionaires = entities.billionaires || 0;
    const duplicatesMerged = entities.duplicates_merged || 0;

    const summary = document.getElementById('entities-summary');
    const progress = document.getElementById('entities-progress');
    const details = document.getElementById('entities-details');

    summary.textContent = `${totalEntities.toLocaleString()} entities, ${inNetwork.toLocaleString()} in network`;
    progress.style.width = '100%';
    progress.textContent = '100%';
    progress.classList.add('complete');

    details.innerHTML = `
        <div class="detail-item">
            <div class="detail-label">Total Entities</div>
            <div class="detail-value">${totalEntities.toLocaleString()}</div>
        </div>
        <div class="detail-item">
            <div class="detail-label">In Network Graph</div>
            <div class="detail-value">${inNetwork.toLocaleString()}</div>
        </div>
        <div class="detail-item">
            <div class="detail-label">Billionaires</div>
            <div class="detail-value">${billionaires.toLocaleString()}</div>
        </div>
        <div class="detail-item">
            <div class="detail-label">Duplicates Merged</div>
            <div class="detail-value">${duplicatesMerged.toLocaleString()}</div>
        </div>
        <div class="detail-item">
            <div class="detail-label">Network Connections</div>
            <div class="detail-value">${(network.edges || 0).toLocaleString()}</div>
        </div>
    `;
}

function showPipelineError(message) {
    console.error('Pipeline error:', message);
    // Could add UI error display here if needed
}

// Start/stop auto-refresh when switching to/from ingestion tab
function startPipelineStatusUpdates() {
    if (pipelineStatusInterval) return; // Already running
    
    updatePipelineStatus(); // Immediate update
    pipelineStatusInterval = setInterval(updatePipelineStatus, 5000); // Every 5 seconds
}

function stopPipelineStatusUpdates() {
    if (pipelineStatusInterval) {
        clearInterval(pipelineStatusInterval);
        pipelineStatusInterval = null;
    }
}

// Note: Timeline tab loading is now handled in the main switchTab function above
// Pipeline updates for ingestion tab
const originalSwitchTab = switchTab;
switchTab = function(tabName, element) {
    originalSwitchTab(tabName, element);

    if (tabName === 'ingestion') {
        startPipelineStatusUpdates();
    } else {
        stopPipelineStatusUpdates();
    }
};

// ============================================================================
// Timeline Functions
// ============================================================================

let timelineData = [];
let filteredTimelineData = [];
let timelineFilters = {
    type: 'all',
    startDate: null,
    endDate: null,
    search: ''
};

// Baseline hardcoded timeline events
const baselineEvents = [
    {
        date: '2019-07-06',
        title: 'Epstein Arrested at Teterboro Airport',
        description: 'Jeffrey Epstein arrested upon arrival at Teterboro Airport in New Jersey on charges of sex trafficking of minors.',
        type: 'case',
        source_type: 'court',
        source_url: 'https://www.justice.gov/usao-sdny/pr/jeffrey-epstein-charged-manhattan-federal-court-sex-trafficking-minors',
        source_name: 'US Attorney SDNY',
        entities: ['Jeffrey Epstein'],
        documents: []
    },
    {
        date: '2019-08-10',
        title: 'Epstein Found Dead in MCC',
        description: 'Jeffrey Epstein found unresponsive in his cell at Metropolitan Correctional Center, New York. Death ruled suicide by hanging.',
        type: 'case',
        source_type: 'court',
        source_url: 'https://www.justice.gov/opa/pr/statement-attorney-general-william-p-barr-death-jeffrey-epstein',
        source_name: 'US Department of Justice',
        entities: ['Jeffrey Epstein'],
        documents: []
    },
    {
        date: '2025-11-13',
        title: 'House Oversight Committee Releases 67,144 Epstein Documents',
        description: '13GB archive with 33,572 images converted to PDF and OCR\'d. Size: 12.9 GB covering comprehensive Epstein-related materials released to Internet Archive.',
        type: 'documents',
        source_type: 'web',
        source_url: 'https://archive.org/details/epstein-pdf',
        source_name: 'Internet Archive',
        entities: [],
        documents: ['House Oversight Nov 2025 Collection']
    },
    {
        date: '2008-06-30',
        title: 'Epstein Pleads Guilty in Florida',
        description: 'Epstein pleads guilty to state charges of procuring a minor for prostitution and solicitation of prostitution in Palm Beach, Florida.',
        type: 'case',
        source_type: 'court',
        source_url: 'https://www.miamiherald.com/news/local/article220097825.html',
        source_name: 'Miami Herald',
        entities: ['Jeffrey Epstein'],
        documents: []
    },
    {
        date: '2005-03-01',
        title: 'Palm Beach Police Begin Investigation',
        description: 'Palm Beach Police Department opens investigation into Epstein following complaints from parents of underage victims.',
        type: 'case',
        source_type: 'court',
        source_url: 'https://www.palmbeachpost.com/story/news/crime/2019/07/08/jeffrey-epstein-timeline-billionaires-road-to-sex-trafficking-charges/39658521/',
        source_name: 'Palm Beach Post',
        entities: ['Jeffrey Epstein'],
        documents: []
    },
    {
        date: '2019-12-16',
        title: 'Prince Andrew BBC Interview',
        description: 'Prince Andrew gives interview to BBC Newsnight regarding his association with Jeffrey Epstein.',
        type: 'life',
        source_type: 'web',
        source_url: 'https://www.bbc.com/news/uk-50449339',
        source_name: 'BBC News',
        entities: ['Prince Andrew', 'Jeffrey Epstein'],
        documents: []
    },
    {
        date: '2021-12-29',
        title: 'Ghislaine Maxwell Convicted',
        description: 'Ghislaine Maxwell found guilty on five federal counts including sex trafficking of minors for Jeffrey Epstein.',
        type: 'case',
        source_type: 'court',
        source_url: 'https://www.justice.gov/usao-sdny/pr/ghislaine-maxwell-convicted-charges-including-sex-trafficking-minors-jeffrey-epstein',
        source_name: 'US Attorney SDNY',
        entities: ['Ghislaine Maxwell', 'Jeffrey Epstein'],
        documents: []
    },
    {
        date: '2015-12-30',
        title: 'Virginia Giuffre Files Defamation Lawsuit',
        description: 'Virginia Giuffre files defamation lawsuit against Ghislaine Maxwell in federal court.',
        type: 'case',
        source_type: 'court',
        source_url: 'https://www.courthousenews.com/wp-content/uploads/2019/08/Giuffre-unseal.pdf',
        source_name: 'Federal Court Filing',
        entities: ['Virginia Giuffre', 'Ghislaine Maxwell'],
        documents: []
    },
    {
        date: '2019-08-09',
        title: 'Court Unseals Epstein Documents',
        description: 'Federal court unseals approximately 2,000 pages of documents from Giuffre v. Maxwell defamation case.',
        type: 'documents',
        source_type: 'court',
        source_url: 'https://www.courtlistener.com/docket/4355835/giuffre-v-maxwell/',
        source_name: 'Court Records',
        entities: ['Virginia Giuffre', 'Ghislaine Maxwell'],
        documents: ['Giuffre v Maxwell Documents']
    },
    {
        date: '1953-01-20',
        title: 'Jeffrey Epstein Born',
        description: 'Jeffrey Edward Epstein born in Brooklyn, New York.',
        type: 'life',
        source_type: 'web',
        source_url: 'https://www.biography.com/crime-figure/jeffrey-epstein',
        source_name: 'Biography.com',
        entities: ['Jeffrey Epstein'],
        documents: []
    },
    {
        date: '1991-12-25',
        title: 'Ghislaine Maxwell Born',
        description: 'Ghislaine Noelle Marion Maxwell born in Maisons-Laffitte, France.',
        type: 'life',
        source_type: 'web',
        source_url: 'https://www.biography.com/crime-figure/ghislaine-maxwell',
        source_name: 'Biography.com',
        entities: ['Ghislaine Maxwell'],
        documents: []
    },
    {
        date: '2022-06-28',
        title: 'Ghislaine Maxwell Sentenced',
        description: 'Ghislaine Maxwell sentenced to 20 years in federal prison for sex trafficking.',
        type: 'case',
        source_type: 'court',
        source_url: 'https://www.justice.gov/usao-sdny/pr/ghislaine-maxwell-sentenced-20-years-prison-conspiring-jeffrey-epstein-sexually-abuse',
        source_name: 'US Attorney SDNY',
        entities: ['Ghislaine Maxwell'],
        documents: []
    },
    {
        date: '2008-07-01',
        title: 'Epstein Begins Prison Sentence',
        description: 'Epstein begins serving 13-month sentence at Palm Beach County jail with work release privileges.',
        type: 'case',
        source_type: 'court',
        source_url: 'https://www.miamiherald.com/news/local/article220097825.html',
        source_name: 'Miami Herald',
        entities: ['Jeffrey Epstein'],
        documents: []
    },
    {
        date: '2019-07-08',
        title: 'Epstein Indicted in Manhattan',
        description: 'Federal grand jury in Manhattan indicts Epstein on sex trafficking charges.',
        type: 'case',
        source_type: 'court',
        source_url: 'https://www.justice.gov/usao-sdny/press-release/file/1177406/download',
        source_name: 'Federal Indictment',
        entities: ['Jeffrey Epstein'],
        documents: []
    },
    {
        date: '2020-07-02',
        title: 'Ghislaine Maxwell Arrested',
        description: 'FBI arrests Ghislaine Maxwell in New Hampshire on charges related to Epstein case.',
        type: 'case',
        source_type: 'court',
        source_url: 'https://www.fbi.gov/news/press-releases/press-releases/ghislaine-maxwell-arrested-on-charges-she-facilitated-and-participated-in-sexual-exploitation-of-minor-girls',
        source_name: 'FBI Press Release',
        entities: ['Ghislaine Maxwell'],
        documents: []
    }
];

async function loadTimeline() {
    console.log('🔍 loadTimeline() called');
    console.log('📊 Baseline events:', baselineEvents.length);

    try {
        // Try to fetch timeline from API
        const url = `${API_BASE}/timeline`;
        console.log('📡 Fetching from:', url);

        const response = await fetch(url, {
            credentials: 'include'
        });

        console.log('📊 Response status:', response.status, response.statusText);

        if (response.ok) {
            const data = await response.json();
            console.log('✅ API data received:', data);
            console.log('📊 API events count:', data.events?.length || 0);

            // Merge API events with baseline
            timelineData = [...baselineEvents, ...(data.events || [])];
        } else {
            console.warn('⚠️ API response not OK, using baseline only');
            // Use baseline events only
            timelineData = [...baselineEvents];
        }

        console.log('📋 Total timeline data:', timelineData.length, 'events');

        // Sort by date (most recent first)
        timelineData.sort((a, b) => new Date(b.date) - new Date(a.date));

        // Update statistics
        updateTimelineStats();

        // Initial render
        filteredTimelineData = [...timelineData];
        console.log('🎨 About to render', filteredTimelineData.length, 'events');
        renderTimeline();

    } catch (error) {
        console.error('❌ Error loading timeline:', error);
        console.error('Stack trace:', error.stack);
        // Use baseline events on error
        timelineData = [...baselineEvents];
        timelineData.sort((a, b) => new Date(b.date) - new Date(a.date));
        updateTimelineStats();
        filteredTimelineData = [...timelineData];
        renderTimeline();
    }
}

function updateTimelineStats() {
    const stats = {
        total: timelineData.length,
        case: timelineData.filter(e => e.category === 'case').length,
        life: timelineData.filter(e => e.category === 'biographical').length,
        documents: timelineData.filter(e => e.category === 'documents').length,
        legal: timelineData.filter(e => e.category === 'legal').length,
        political: timelineData.filter(e => e.category === 'political').length
    };

    document.getElementById('timeline-total').textContent = stats.total;
    document.getElementById('timeline-case').textContent = stats.case;
    document.getElementById('timeline-life').textContent = stats.life;
    document.getElementById('timeline-docs').textContent = stats.documents;
}

function renderTimeline() {
    console.log('🎨 renderTimeline() called');
    console.log('📊 filteredTimelineData.length:', filteredTimelineData.length);

    const container = document.getElementById('timeline-events');
    console.log('📦 Container element:', container);

    if (!container) {
        console.error('❌ CRITICAL: Container #timeline-events not found in DOM!');
        return;
    }

    if (filteredTimelineData.length === 0) {
        console.log('⚠️ No events to display (showing empty state)');
        container.innerHTML = `
            <div class="timeline-empty">
                <div class="timeline-empty-icon"><i data-lucide="search"></i></div>
                <div class="timeline-empty-text">No events match your filters</div>
            </div>
        `;
        // Initialize icons for empty state
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
        return;
    }

    console.log('✅ Rendering', filteredTimelineData.length, 'events to container');

    container.innerHTML = filteredTimelineData.map(event => {
        const eventDate = new Date(event.date);
        const formattedDate = eventDate.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });

        // Provenance icon
        const provenanceIcon = event.source_type === 'court' ? '<i data-lucide="scale"></i>' :
                              event.source_type === 'web' ? '<i data-lucide="globe"></i>' : '<i data-lucide="file-text"></i>';

        // Entities HTML
        const entitiesHTML = event.related_entities && event.related_entities.length > 0 ? `
            <div class="timeline-entities">
                ${event.related_entities.filter(entity => entity && entity.trim()).map(entity => `
                    <span class="timeline-entity-tag" onclick="showEntityDetails('${entity.replace(/'/g, "\\'")}')">${formatEntityName(entity)}</span>
                `).join('')}
            </div>
        ` : '';

        // Documents HTML
        const documentsHTML = event.related_documents && event.related_documents.length > 0 ? `
            <div class="timeline-documents">
                ${event.related_documents.filter(doc => doc && doc.trim()).map(doc => `
                    <a href="#" class="timeline-doc-link" onclick="event.preventDefault(); alert('Document viewer coming soon')">${doc}</a>
                `).join('')}
            </div>
        ` : '';

        return `
            <div class="timeline-event" data-type="${event.category}" data-date="${event.date}">
                <div class="timeline-date-col">
                    <div class="timeline-date">${formattedDate}</div>
                </div>

                <div class="timeline-marker">
                    <div class="timeline-dot ${event.category}"></div>
                </div>

                <div class="timeline-content">
                    <div class="timeline-event-header">
                        <div>
                            <div class="timeline-event-title">${event.title}</div>
                        </div>
                        <span class="timeline-event-type ${event.category}">${event.category}</span>
                    </div>

                    <div class="timeline-event-description">${event.description}</div>

                    <div class="timeline-event-meta">
                        <div class="timeline-provenance">
                            <span class="timeline-provenance-icon">${provenanceIcon}</span>
                            <a href="${event.source_url}" target="_blank" rel="noopener noreferrer" class="timeline-provenance-link">
                                ${event.source}
                            </a>
                        </div>

                        ${entitiesHTML}
                        ${documentsHTML}
                    </div>
                </div>
            </div>
        `;
    }).join('');

    // Initialize Lucide icons after rendering timeline
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
}

function filterTimelineByType(type) {
    timelineFilters.type = type;

    // Update button states
    document.querySelectorAll('.timeline-filter-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');

    applyTimelineFilters();
}

function filterTimelineByDate() {
    const startInput = document.getElementById('timeline-start-date');
    const endInput = document.getElementById('timeline-end-date');

    timelineFilters.startDate = startInput.value || null;
    timelineFilters.endDate = endInput.value || null;

    applyTimelineFilters();
}

function filterTimelineBySearch(query) {
    timelineFilters.search = query.toLowerCase();
    applyTimelineFilters();
}

function applyTimelineFilters() {
    console.log('🔍 applyTimelineFilters() called');
    console.log('📊 Current filters:', timelineFilters);
    console.log('📊 Timeline data length:', timelineData.length);

    filteredTimelineData = timelineData.filter(event => {
        // Type filter
        if (timelineFilters.type !== 'all' && event.category !== timelineFilters.type) {
            return false;
        }

        // Date range filter
        if (timelineFilters.startDate && event.date < timelineFilters.startDate) {
            return false;
        }
        if (timelineFilters.endDate && event.date > timelineFilters.endDate) {
            return false;
        }

        // Search filter
        if (timelineFilters.search) {
            const searchText = [
                event.title,
                event.description,
                event.source,
                ...(event.related_entities || []),
                ...(event.related_documents || [])
            ].join(' ').toLowerCase();

            if (!searchText.includes(timelineFilters.search)) {
                return false;
            }
        }

        return true;
    });

    console.log('📊 Filtered timeline data length:', filteredTimelineData.length);
    renderTimeline();
}

// Logout function
async function logout() {
    // Call server logout endpoint to clear session cookie
    try {
        await fetch('/api/logout', {
            method: 'POST',
            credentials: 'include'
        });
    } catch (error) {
        console.error('Logout error:', error);
    }

    // Redirect to login page
    window.location.href = '/static/login.html';
}


// ============================================================================
// Hot-Reload Integration
// ============================================================================

// Register hot-reload handlers when the module loads
if (window.hotReload) {
    // Entity network updates
    hotReload.on('entity_network', (data) => {
        console.log('[App] Entity network updated, reloading...');
        if (typeof loadNetwork === 'function') {
            loadNetwork();
        }
    });

    // Timeline updates
    hotReload.on('timeline', (data) => {
        console.log('[App] Timeline updated, reloading...');
        if (typeof loadTimeline === 'function') {
            loadTimeline();
        }
    });

    // Entities list updates
    hotReload.on('entities', (data) => {
        console.log('[App] Entities updated, reloading...');
        if (typeof loadEntities === 'function') {
            loadEntities();
        }
    });

    // Documents index updates
    hotReload.on('documents', (data) => {
        console.log('[App] Documents updated, reloading stats...');
        // Reload overview stats
        if (typeof loadStats === 'function') {
            loadStats();
        }
    });

    // Cases index updates
    hotReload.on('cases', (data) => {
        console.log('[App] Cases updated, reloading...');
        // If there's a cases loading function
        if (typeof loadCases === 'function') {
            loadCases();
        }
    });

    // Victims index updates
    hotReload.on('victims', (data) => {
        console.log('[App] Victims updated, reloading...');
        // If there's a victims loading function
        if (typeof loadVictims === 'function') {
            loadVictims();
        }
    });

    // Entity mappings updates
    hotReload.on('entity_mappings', (data) => {
        console.log('[App] Entity mappings updated, reloading entities...');
        if (typeof loadEntities === 'function') {
            loadEntities();
        }
        if (typeof loadNetwork === 'function') {
            loadNetwork();
        }
    });

    // Entity filter updates
    hotReload.on('entity_filter', (data) => {
        console.log('[App] Entity filter updated, reloading entities...');
        if (typeof loadEntities === 'function') {
            loadEntities();
        }
    });

    console.log('[App] Hot-reload handlers registered');
}

// ===========================
// FLIGHTS PAGE FUNCTIONS
// ===========================

/**
 * Open flight details panel with smooth slide-in animation
 */
/**
 * Show flight details in centered popup modal with all flights on route
 */
function showFlightPopup(flightData) {
    const overlay = document.getElementById('flight-popup-overlay');
    const popup = document.getElementById('flight-popup');

    if (!overlay || !popup) return;

    // Update popup content
    const fromName = flightData.fromName || flightData.from;
    const toName = flightData.toName || flightData.to;
    const frequency = flightData.frequency || 1;

    document.getElementById('popup-flight-title').textContent =
        `${flightData.from} → ${flightData.to}`;

    // Show frequency if multiple flights on this route
    if (frequency > 1) {
        document.getElementById('popup-flight-date').textContent =
            `${frequency} flights on this route`;
    } else {
        document.getElementById('popup-flight-date').textContent =
            flightData.date || 'Unknown Date';
    }

    document.getElementById('popup-flight-origin').textContent = fromName;
    document.getElementById('popup-flight-destination').textContent = toName;

    // Build passenger links (unique passengers across all flights on route)
    const passengerList = document.getElementById('popup-passenger-list');
    if (flightData.passengers && flightData.passengers.length > 0) {
        passengerList.innerHTML = flightData.passengers.map(passenger => `
            <a href="#" class="passenger-link" onclick="viewPassengerNetwork('${passenger.replace(/'/g, "\\'")}'); return false;">
                <span>${formatEntityName(passenger)}</span>
                <i data-lucide="arrow-right"></i>
            </a>
        `).join('');

        // Re-initialize Lucide icons for new content
        if (window.lucide) {
            lucide.createIcons();
        }
    } else {
        passengerList.innerHTML = '<p style="color: var(--text-secondary); font-size: 13px;">No passenger data available</p>';
    }

    // Show detailed flight list if multiple flights on route (max 10)
    if (flightData.flights && flightData.flights.length > 1) {
        const flightListHTML = flightData.flights.slice(0, 10).map(flight => `
            <div style="padding: 8px; border-bottom: 1px solid var(--border-color); font-size: 13px;">
                <div style="font-weight: 600; color: var(--accent-color);">${flight.date}</div>
                <div style="color: var(--text-secondary); margin-top: 4px;">
                    ${flight.passenger_count} passengers: ${flight.passengers.slice(0, 3).map(p => formatEntityName(p)).join(', ')}${flight.passengers.length > 3 ? '...' : ''}
                </div>
            </div>
        `).join('');

        // Add flight list section after passenger list
        const existingFlightList = popup.querySelector('.flight-list-section');
        if (existingFlightList) {
            existingFlightList.remove();
        }

        const flightListSection = document.createElement('div');
        flightListSection.className = 'flight-list-section';
        flightListSection.style.marginTop = '20px';
        flightListSection.innerHTML = `
            <h3 style="font-size: 14px; font-weight: 600; margin-bottom: 12px; color: var(--text-primary);">
                Recent Flights (${Math.min(10, flightData.flights.length)} of ${flightData.flights.length})
            </h3>
            <div style="max-height: 300px; overflow-y: auto; border: 1px solid var(--border-color); border-radius: 6px;">
                ${flightListHTML}
            </div>
        `;

        passengerList.parentElement.appendChild(flightListSection);
    } else {
        // Remove flight list section if only one flight
        const existingFlightList = popup.querySelector('.flight-list-section');
        if (existingFlightList) {
            existingFlightList.remove();
        }
    }

    // Show popup with animation
    overlay.classList.add('active');
    popup.classList.add('active');
}

/**
 * Close flight popup modal
 */
function closeFlightPopup() {
    const overlay = document.getElementById('flight-popup-overlay');
    const popup = document.getElementById('flight-popup');

    if (overlay && popup) {
        overlay.classList.remove('active');
        popup.classList.remove('active');
    }
}

/**
 * Toggle statistics panel minimized state
 */
function toggleStatsPanel() {
    const panel = document.getElementById('flight-stats-panel');
    if (panel) {
        panel.classList.toggle('minimized');
    }
}

/**
 * Toggle timeline panel minimized state
 */
function toggleTimelinePanel() {
    const panel = document.getElementById('flight-timeline-panel');
    if (panel) {
        panel.classList.toggle('minimized');
    }
}

/**
 * Group flights by year-month
 */
function groupFlightsByMonth(routes) {
    const monthMap = new Map();

    routes.forEach(route => {
        route.flights.forEach(flight => {
            if (!flight.date) return;

            // Get year-month key (e.g., "2002-09")
            const date = new Date(flight.date);
            const yearMonth = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;

            if (!monthMap.has(yearMonth)) {
                monthMap.set(yearMonth, {
                    yearMonth,
                    label: date.toLocaleDateString('en-US', { year: 'numeric', month: 'short' }),
                    year: date.getFullYear(),
                    month: date.getMonth() + 1,
                    flights: [],
                    routes: new Set()
                });
            }

            const monthData = monthMap.get(yearMonth);
            monthData.flights.push({ ...flight, route });
            monthData.routes.add(route);
        });
    });

    // Convert to sorted array
    const monthsArray = Array.from(monthMap.values()).sort((a, b) =>
        a.yearMonth.localeCompare(b.yearMonth)
    );

    // Convert routes Set to Array for each month
    monthsArray.forEach(month => {
        month.routes = Array.from(month.routes);
    });

    return monthsArray;
}

/**
 * Initialize flight timeline slider with month selector
 */
function initFlightTimeline() {
    if (!window.allFlightRoutes || window.allFlightRoutes.length === 0) {
        console.warn('No flight data available for timeline initialization');
        return;
    }

    // Group flights by month
    const monthsWithFlights = groupFlightsByMonth(window.allFlightRoutes);

    if (monthsWithFlights.length === 0) {
        console.warn('No valid dates found in flight data');
        return;
    }

    // Store globally for navigation
    window.flightMonths = monthsWithFlights;
    window.currentMonthIndex = monthsWithFlights.length - 1; // Default to last month

    console.log(`Timeline: ${monthsWithFlights.length} months with flights (${monthsWithFlights[0].yearMonth} to ${monthsWithFlights[monthsWithFlights.length - 1].yearMonth})`);

    // Initialize noUiSlider
    const sliderElement = document.getElementById('flight-timeline-slider');
    if (!sliderElement) {
        console.error('Timeline slider element not found');
        return;
    }

    // Destroy existing slider if present
    if (sliderElement.noUiSlider) {
        sliderElement.noUiSlider.destroy();
    }

    // Create single-value slider
    noUiSlider.create(sliderElement, {
        start: monthsWithFlights.length - 1, // Start at last month
        step: 1,
        range: {
            'min': 0,
            'max': monthsWithFlights.length - 1
        },
        tooltips: {
            to: function(value) {
                const index = Math.round(value);
                return monthsWithFlights[index].label;
            }
        },
        pips: {
            mode: 'steps',
            stepped: true,
            density: 100 / monthsWithFlights.length,
            filter: function(value, type) {
                // Show only every few labels to avoid crowding
                if (monthsWithFlights.length <= 12) return 1; // Show all if <= 12 months
                if (monthsWithFlights.length <= 24) return value % 2 === 0 ? 1 : 0; // Show every 2nd
                if (monthsWithFlights.length <= 48) return value % 4 === 0 ? 1 : 0; // Show every 4th
                return value % 6 === 0 ? 1 : 0; // Show every 6th
            },
            format: {
                to: function(value) {
                    const index = Math.round(value);
                    const month = monthsWithFlights[index];
                    // Show abbreviated format for pips
                    const date = new Date(month.year, month.month - 1);
                    return date.toLocaleDateString('en-US', { year: '2-digit', month: 'short' });
                }
            }
        }
    });

    // Update display on slider change
    sliderElement.noUiSlider.on('update', function(values, handle) {
        const monthIndex = Math.round(values[0]);
        window.currentMonthIndex = monthIndex;
        updateMonthDisplay(monthIndex);
        updateNavigationButtons(); // Update button states
    });

    // Apply filtering when slider is released
    sliderElement.noUiSlider.on('change', function(values, handle) {
        const monthIndex = Math.round(values[0]);
        applyMonthFilter(monthIndex);
    });

    // Initial render - show last month
    updateMonthDisplay(window.currentMonthIndex);
    applyMonthFilter(window.currentMonthIndex);
    updateNavigationButtons(); // Set initial button states

    console.log('✓ Flight timeline slider initialized (month selector mode)');
}

/**
 * Update month display in timeline header
 */
function updateMonthDisplay(monthIndex) {
    if (!window.flightMonths || monthIndex < 0 || monthIndex >= window.flightMonths.length) {
        return;
    }

    const selectedMonth = window.flightMonths[monthIndex];
    const monthLabelEl = document.getElementById('current-month-label');
    const monthCountEl = document.getElementById('month-flight-count');

    if (monthLabelEl) {
        monthLabelEl.textContent = selectedMonth.label;
    }

    if (monthCountEl) {
        const flightCount = selectedMonth.flights.length;
        const routeCount = selectedMonth.routes.length;
        monthCountEl.textContent = `${routeCount} route${routeCount !== 1 ? 's' : ''}, ${flightCount} flight${flightCount !== 1 ? 's' : ''}`;
    }
}

/**
 * Update navigation button states based on current position
 */
function updateNavigationButtons() {
    if (!window.flightMonths || window.currentMonthIndex === undefined) {
        return;
    }

    // Get button elements (search by onclick content since they don't have IDs)
    const buttons = document.querySelectorAll('.timeline-nav-btn');
    const prevButton = Array.from(buttons).find(btn => btn.onclick?.toString().includes('previousMonth'));
    const nextButton = Array.from(buttons).find(btn => btn.onclick?.toString().includes('nextMonth'));

    // Alternative: search by text content
    const allNavButtons = document.querySelectorAll('.timeline-nav-btn');
    const prevBtn = Array.from(allNavButtons).find(btn => btn.textContent.includes('Previous'));
    const nextBtn = Array.from(allNavButtons).find(btn => btn.textContent.includes('Next'));

    const isAtStart = window.currentMonthIndex === 0;
    const isAtEnd = window.currentMonthIndex === window.flightMonths.length - 1;

    // Update Previous button
    if (prevBtn) {
        prevBtn.disabled = isAtStart;
        prevBtn.style.opacity = isAtStart ? '0.5' : '1';
        prevBtn.style.cursor = isAtStart ? 'not-allowed' : 'pointer';
    }

    // Update Next button
    if (nextBtn) {
        nextBtn.disabled = isAtEnd;
        nextBtn.style.opacity = isAtEnd ? '0.5' : '1';
        nextBtn.style.cursor = isAtEnd ? 'not-allowed' : 'pointer';
    }
}

/**
 * Apply month filter to show only flights from selected month
 */
function applyMonthFilter(monthIndex) {
    if (!window.flightMonths || monthIndex < 0 || monthIndex >= window.flightMonths.length) {
        console.warn('Invalid month index:', monthIndex);
        return;
    }

    if (!window.flightMap) {
        showToast('Flight map not initialized yet', 'warning');
        return;
    }

    const selectedMonth = window.flightMonths[monthIndex];
    console.log(`Filtering to month: ${selectedMonth.label} (${selectedMonth.flights.length} flights, ${selectedMonth.routes.length} routes)`);

    // Get current filter values from filter bar
    const passenger = document.getElementById('flight-passenger-filter')?.value?.toLowerCase()?.trim();
    const airport = document.getElementById('flight-airport-filter')?.value?.toUpperCase()?.trim();

    // Clear current display
    window.flightRoutes.forEach(route => route.remove());
    window.flightMarkers.forEach(marker => marker.remove());
    window.flightRoutes = [];
    window.flightMarkers = [];
    window.flightBounds = null;

    // Filter routes for this month (and apply other active filters)
    let filteredRoutes = selectedMonth.routes;

    // Apply passenger filter if active
    if (passenger) {
        filteredRoutes = filteredRoutes.filter(route =>
            route.flights.some(flight =>
                flight.passengers.some(p => p.toLowerCase().includes(passenger))
            )
        );
    }

    // Apply airport filter if active
    if (airport) {
        filteredRoutes = filteredRoutes.filter(route => {
            const originMatch = route.origin.code.toUpperCase().includes(airport);
            const destMatch = route.destination.code.toUpperCase().includes(airport);
            return originMatch || destMatch;
        });
    }

    console.log(`Rendering ${filteredRoutes.length} routes for ${selectedMonth.label}`);

    if (filteredRoutes.length === 0) {
        showToast(`No flights in ${selectedMonth.label}${passenger || airport ? ' matching filters' : ''}`, 'warning');
        return;
    }

    // Re-render filtered routes
    filteredRoutes.forEach(route => {
        const firstFlight = route.flights[0];
        const allPassengers = new Set();
        route.flights.forEach(flight => {
            flight.passengers.forEach(p => allPassengers.add(p));
        });

        const flightData = {
            from: route.origin.code,
            to: route.destination.code,
            fromName: route.origin.name,
            toName: route.destination.name,
            date: firstFlight.date,
            passengers: Array.from(allPassengers),
            flights: route.flights,
            frequency: route.frequency
        };

        drawFlightPath(route.origin, route.destination, flightData, route.frequency);
    });

    // Auto-zoom to filtered results
    if (window.flightBounds) {
        fitMapToFlightBounds();
    }

    showToast(`Showing ${selectedMonth.label}: ${filteredRoutes.length} route${filteredRoutes.length !== 1 ? 's' : ''}`, 'success');
}

/**
 * Navigate to previous month in timeline
 */
function previousMonth() {
    console.log('[Timeline Nav] Previous button clicked');

    if (!window.flightMonths || window.currentMonthIndex === undefined) {
        console.error('Timeline not initialized');
        showToast('Timeline not ready', 'error');
        return;
    }

    const currentIndex = window.currentMonthIndex;
    console.log(`[Timeline Nav] Current index: ${currentIndex}`);

    if (currentIndex > 0) {
        const newIndex = currentIndex - 1;
        const sliderElement = document.getElementById('flight-timeline-slider');

        if (!sliderElement) {
            console.error('Slider element not found');
            showToast('Slider not found', 'error');
            return;
        }

        if (!sliderElement.noUiSlider) {
            console.error('Slider not initialized');
            showToast('Slider not initialized', 'error');
            return;
        }

        console.log(`[Timeline Nav] Moving to index ${newIndex} (${window.flightMonths[newIndex].label})`);
        sliderElement.noUiSlider.set(newIndex);
    } else {
        console.log('[Timeline Nav] Already at first month');
        showToast('Already at first month', 'info');
    }
}

/**
 * Navigate to next month in timeline
 */
function nextMonth() {
    console.log('[Timeline Nav] Next button clicked');

    if (!window.flightMonths || window.currentMonthIndex === undefined) {
        console.error('Timeline not initialized');
        showToast('Timeline not ready', 'error');
        return;
    }

    const currentIndex = window.currentMonthIndex;
    const maxIndex = window.flightMonths.length - 1;
    console.log(`[Timeline Nav] Current index: ${currentIndex}, Max: ${maxIndex}`);

    if (currentIndex < maxIndex) {
        const newIndex = currentIndex + 1;
        const sliderElement = document.getElementById('flight-timeline-slider');

        if (!sliderElement) {
            console.error('Slider element not found');
            showToast('Slider not found', 'error');
            return;
        }

        if (!sliderElement.noUiSlider) {
            console.error('Slider not initialized');
            showToast('Slider not initialized', 'error');
            return;
        }

        console.log(`[Timeline Nav] Moving to index ${newIndex} (${window.flightMonths[newIndex].label})`);
        sliderElement.noUiSlider.set(newIndex);
    } else {
        console.log('[Timeline Nav] Already at last month');
        showToast('Already at last month', 'info');
    }
}

/**
 * Reset timeline to show last month (latest)
 */
function resetTimelineFilter() {
    console.log('[Timeline Nav] Latest button clicked');

    if (!window.flightMonths || window.flightMonths.length === 0) {
        console.error('Timeline not initialized');
        showToast('Timeline not ready', 'error');
        return;
    }

    const sliderElement = document.getElementById('flight-timeline-slider');
    if (!sliderElement) {
        console.error('Slider element not found');
        showToast('Slider not found', 'error');
        return;
    }

    if (!sliderElement.noUiSlider) {
        console.error('Slider not initialized');
        showToast('Slider not initialized', 'error');
        return;
    }

    // Set to last month
    const lastIndex = window.flightMonths.length - 1;
    const currentIndex = window.currentMonthIndex;

    if (currentIndex === lastIndex) {
        console.log('[Timeline Nav] Already at latest month');
        showToast('Already showing latest month', 'info');
        return;
    }

    console.log(`[Timeline Nav] Jumping to latest month (index ${lastIndex}: ${window.flightMonths[lastIndex].label})`);
    sliderElement.noUiSlider.set(lastIndex);
    showToast(`Jumped to ${window.flightMonths[lastIndex].label}`, 'success');
}

/**
 * View passenger network (placeholder for integration)
 */
function viewPassengerNetwork(passengerName) {
    console.log('Viewing network for:', passengerName);
    // TODO: Switch to network view and highlight this passenger
    closeFlightPopup();
    // switchTab('network');
    alert(`Switching to network view for ${passengerName} (full integration pending)`);
}

/**
 * Apply filters to flight data and zoom to filtered results
 */
function applyFlightFilters() {
    const dateStart = document.getElementById('flight-date-start')?.value;
    const dateEnd = document.getElementById('flight-date-end')?.value;
    const passenger = document.getElementById('flight-passenger-filter')?.value?.toLowerCase()?.trim();
    const airport = document.getElementById('flight-airport-filter')?.value?.toUpperCase()?.trim();

    console.log('Applying flight filters:', { dateStart, dateEnd, passenger, airport });

    if (!window.allFlightRoutes || !window.flightMap) {
        showToast('Flight data not loaded yet', 'warning');
        return;
    }

    // Get timeline filter range if active
    let timelineStartDate = null;
    let timelineEndDate = null;
    const sliderElement = document.getElementById('flight-timeline-slider');
    if (sliderElement && sliderElement.noUiSlider) {
        const values = sliderElement.noUiSlider.get();
        const startTimestamp = parseInt(values[0]);
        const endTimestamp = parseInt(values[1]);
        const range = sliderElement.noUiSlider.options.range;

        // Only apply timeline filter if it's not at full range
        if (startTimestamp !== range.min || endTimestamp !== range.max) {
            timelineStartDate = new Date(startTimestamp).toISOString().split('T')[0];
            timelineEndDate = new Date(endTimestamp).toISOString().split('T')[0];
            console.log('Timeline filter active:', { timelineStartDate, timelineEndDate });
        }
    }

    // Clear current display
    window.flightRoutes.forEach(route => route.remove());
    window.flightMarkers.forEach(marker => marker.remove());
    window.flightRoutes = [];
    window.flightMarkers = [];
    window.flightBounds = null;

    // Filter routes based on criteria
    let filteredRoutes = window.allFlightRoutes.filter(route => {
        // Timeline filter (takes precedence over date inputs)
        if (timelineStartDate || timelineEndDate) {
            const hasMatchingDate = route.flights.some(flight => {
                const flightDate = flight.date;
                if (timelineStartDate && flightDate < timelineStartDate) return false;
                if (timelineEndDate && flightDate > timelineEndDate) return false;
                return true;
            });
            if (!hasMatchingDate) return false;
        }
        // Date filter (from input fields)
        else if (dateStart || dateEnd) {
            const hasMatchingDate = route.flights.some(flight => {
                const flightDate = flight.date;
                if (dateStart && flightDate < dateStart) return false;
                if (dateEnd && flightDate > dateEnd) return false;
                return true;
            });
            if (!hasMatchingDate) return false;
        }

        // Passenger filter (search by name substring)
        if (passenger) {
            const hasMatchingPassenger = route.flights.some(flight =>
                flight.passengers.some(p => p.toLowerCase().includes(passenger))
            );
            if (!hasMatchingPassenger) return false;
        }

        // Airport filter (match origin or destination)
        if (airport) {
            const originMatch = route.origin.code.toUpperCase().includes(airport);
            const destMatch = route.destination.code.toUpperCase().includes(airport);
            if (!originMatch && !destMatch) return false;
        }

        return true;
    });

    // Show results count
    const totalRoutes = window.allFlightRoutes.length;
    console.log(`Filtered: ${filteredRoutes.length} / ${totalRoutes} routes`);

    if (filteredRoutes.length === 0) {
        showToast('No flights match the selected filters', 'warning');
        return;
    }

    // Re-render filtered routes
    filteredRoutes.forEach(route => {
        const firstFlight = route.flights[0];
        const allPassengers = new Set();
        route.flights.forEach(flight => {
            flight.passengers.forEach(p => allPassengers.add(p));
        });

        const flightData = {
            from: route.origin.code,
            to: route.destination.code,
            fromName: route.origin.name,
            toName: route.destination.name,
            date: firstFlight.date,
            passengers: Array.from(allPassengers),
            flights: route.flights,
            frequency: route.frequency
        };

        drawFlightPath(route.origin, route.destination, flightData, route.frequency);
    });

    // Auto-zoom to filtered results
    if (window.flightBounds) {
        fitMapToFlightBounds();
    }

    showToast(`Showing ${filteredRoutes.length} of ${totalRoutes} routes`, 'success');
}

/**
 * Clear all flight filters and reset view
 */
function clearFlightFilters() {
    const dateStart = document.getElementById('flight-date-start');
    const dateEnd = document.getElementById('flight-date-end');
    const passenger = document.getElementById('flight-passenger-filter');
    const airport = document.getElementById('flight-airport-filter');

    if (dateStart) dateStart.value = '';
    if (dateEnd) dateEnd.value = '';
    if (passenger) passenger.value = '';
    if (airport) airport.value = '';

    console.log('Flight filters cleared - reloading all flights');

    if (!window.allFlightRoutes || !window.flightMap) {
        showToast('Flight data not loaded yet', 'warning');
        return;
    }

    // Clear current display
    window.flightRoutes.forEach(route => route.remove());
    window.flightMarkers.forEach(marker => marker.remove());
    window.flightRoutes = [];
    window.flightMarkers = [];
    window.flightBounds = null;

    // Re-render all routes
    window.allFlightRoutes.forEach(route => {
        const firstFlight = route.flights[0];
        const allPassengers = new Set();
        route.flights.forEach(flight => {
            flight.passengers.forEach(p => allPassengers.add(p));
        });

        const flightData = {
            from: route.origin.code,
            to: route.destination.code,
            fromName: route.origin.name,
            toName: route.destination.name,
            date: firstFlight.date,
            passengers: Array.from(allPassengers),
            flights: route.flights,
            frequency: route.frequency
        };

        drawFlightPath(route.origin, route.destination, flightData, route.frequency);
    });

    // Auto-zoom to all flights
    if (window.flightBounds) {
        fitMapToFlightBounds();
    }

    showToast('Filters cleared - showing all flights', 'success');
}

/**
 * Initialize flights view when tab is activated
 */
function initFlightsView() {
    console.log('Initializing flights view...');

    // Load flight statistics
    loadFlightStats();

    // Initialize map (if not already initialized)
    initFlightMap();

    // Add Enter key support for filter inputs
    const passengerFilter = document.getElementById('flight-passenger-filter');
    const airportFilter = document.getElementById('flight-airport-filter');
    const dateStartFilter = document.getElementById('flight-date-start');
    const dateEndFilter = document.getElementById('flight-date-end');

    // Remove existing listeners to prevent duplicates
    const handleEnter = (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            applyFlightFilters();
        }
    };

    [passengerFilter, airportFilter, dateStartFilter, dateEndFilter].forEach(input => {
        if (input) {
            // Remove old listener if exists
            input.removeEventListener('keypress', handleEnter);
            // Add new listener
            input.addEventListener('keypress', handleEnter);
        }
    });
}

/**
 * Load flight statistics into stats cards
 */
async function loadFlightStats() {
    try {
        // Stats will be loaded by loadFlightRoutes() with real data
        console.log('Flight stats will be loaded with route data...');
    } catch (error) {
        console.error('Error loading flight stats:', error);
    }
}

/**
 * Update flight statistics display with real data
 */
function updateFlightStats(stats) {
    try {
        // Update header stats (top of page)
        const headerTotalEl = document.getElementById('flights-total-header');
        const headerDateRangeEl = document.getElementById('flights-date-range-header');
        const headerPassengersEl = document.getElementById('flights-passengers-header');

        if (headerTotalEl) {
            headerTotalEl.textContent = stats.total.toLocaleString();
        }

        if (headerPassengersEl) {
            headerPassengersEl.textContent = stats.unique_passengers.toLocaleString();
        }

        if (headerDateRangeEl && stats.date_range) {
            headerDateRangeEl.textContent = `${stats.date_range.start} to ${stats.date_range.end}`;
        }

        // Update panel stats (side panel)
        const panelTotalEl = document.getElementById('flights-total');
        const panelDateRangeEl = document.getElementById('flights-date-range');
        const panelPassengersEl = document.getElementById('flights-passengers');

        if (panelTotalEl) {
            panelTotalEl.textContent = stats.total.toLocaleString();
        }

        if (panelPassengersEl) {
            panelPassengersEl.textContent = stats.unique_passengers.toLocaleString();
        }

        if (panelDateRangeEl && stats.date_range) {
            panelDateRangeEl.textContent = `${stats.date_range.start} to ${stats.date_range.end}`;
        }

        console.log(`✓ Flight stats updated: ${stats.total} flights, ${stats.unique_passengers} passengers`);
    } catch (error) {
        console.error('Error updating flight stats:', error);
    }
}

/**
 * Initialize the Leaflet map for flights with fullscreen background
 */
function initFlightMap() {
    const mapElement = document.getElementById('flight-map');
    if (!mapElement) return;

    // Check if map is already initialized
    if (window.flightMap) {
        console.log('Flight map already initialized');
        window.flightMap.invalidateSize(); // Refresh map size
        return;
    }

    // Initialize Leaflet map with dark theme
    window.flightMap = L.map('flight-map', {
        center: [25.0, -50.0],
        zoom: 3,
        zoomControl: false, // Remove default zoom control
        attributionControl: true
    });

    // Add zoom control to bottom left
    L.control.zoom({
        position: 'bottomleft'
    }).addTo(window.flightMap);

    // Add light-themed tile layer (CartoDB Voyager - balanced light/dark hybrid)
    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 20
    }).addTo(window.flightMap);

    console.log('Flight map initialized with Voyager theme');

    // Store flight routes for filtering
    window.flightRoutes = [];
    window.flightMarkers = [];

    // Initialize bounds tracking for auto-zoom
    window.flightBounds = null;
    window.userHasZoomed = false; // Track if user manually zoomed
    window.programmaticZoom = false; // Flag to distinguish programmatic zooms from user zooms

    // Add "Reset View" button to map controls
    const resetViewButton = L.Control.extend({
        options: {
            position: 'topleft'
        },
        onAdd: function(map) {
            const container = L.DomUtil.create('div', 'leaflet-bar leaflet-control');
            const button = L.DomUtil.create('a', 'leaflet-control-reset-view', container);
            button.innerHTML = '<i data-lucide="maximize-2" style="width: 18px; height: 18px;"></i>';
            button.href = '#';
            button.title = 'Reset View (Fit All Flights)';
            button.style.cssText = 'display: flex; align-items: center; justify-content: center; width: 30px; height: 30px; line-height: 30px; text-decoration: none; background: white;';

            L.DomEvent.on(button, 'click', function(e) {
                L.DomEvent.preventDefault(e);
                L.DomEvent.stopPropagation(e);
                resetMapView();
            });

            return container;
        }
    });

    window.flightMap.addControl(new resetViewButton());

    // Track user manual zoom/pan
    // Only set userHasZoomed flag for actual user interactions (not programmatic zooms)
    window.flightMap.on('zoomstart', function(e) {
        // Check if this is a user-initiated zoom (not from fitBounds or other programmatic calls)
        if (!window.programmaticZoom && e.originalEvent) {
            console.log('User manually zoomed - disabling auto-fit');
            window.userHasZoomed = true;
        }
    });

    window.flightMap.on('dragstart', function(e) {
        // Only track manual drags (with mouse/touch events)
        if (e.originalEvent) {
            console.log('User manually panned - disabling auto-fit');
            window.userHasZoomed = true;
        }
    });

    // Load and display flight routes
    loadFlightRoutes();
}

/**
 * Calculate angle between two coordinates for plane rotation
 */
function calculateBearing(lat1, lon1, lat2, lon2) {
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const y = Math.sin(dLon) * Math.cos(lat2 * Math.PI / 180);
    const x = Math.cos(lat1 * Math.PI / 180) * Math.sin(lat2 * Math.PI / 180) -
              Math.sin(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.cos(dLon);
    const bearing = Math.atan2(y, x) * 180 / Math.PI;
    return (bearing + 360) % 360;
}

/**
 * Get line weight based on flight frequency
 */
function getLineWeight(frequency) {
    if (frequency >= 10) return 4;
    if (frequency >= 5) return 3;
    return 2;
}

/**
 * Draw curved geodesic flight path on map
 */
function drawFlightPath(origin, destination, flightData, frequency = 1) {
    if (!window.flightMap) return;

    const originCoords = [origin.lat, origin.lon];
    const destCoords = [destination.lat, destination.lon];

    // Update bounds for auto-zoom
    if (!window.flightBounds) {
        window.flightBounds = L.latLngBounds(originCoords, destCoords);
    } else {
        window.flightBounds.extend(originCoords);
        window.flightBounds.extend(destCoords);
    }

    // Calculate control point for curve (perpendicular offset at midpoint)
    const midLat = (origin.lat + destination.lat) / 2;
    const midLon = (origin.lon + destination.lon) / 2;
    const distance = Math.sqrt(
        Math.pow(destination.lat - origin.lat, 2) +
        Math.pow(destination.lon - origin.lon, 2)
    );
    const offset = distance * 0.2; // 20% offset for curve
    const controlLat = midLat + offset;
    const controlLon = midLon;

    // Create curved path using quadratic bezier
    const curve = L.curve(
        [
            'M', originCoords,
            'Q', [controlLat, controlLon],
            destCoords
        ],
        {
            color: getComputedStyle(document.documentElement).getPropertyValue('--accent-color').trim() || '#58a6ff',
            weight: getLineWeight(frequency),
            opacity: 0.6,
            smoothFactor: 1,
            className: 'flight-path-curve'
        }
    ).addTo(window.flightMap);

    // Add click event to show flight details
    curve.on('click', () => {
        showFlightPopup(flightData);
    });

    // Add hover effect
    curve.on('mouseover', function() {
        this.setStyle({ opacity: 0.9, weight: this.options.weight + 1 });
    });

    curve.on('mouseout', function() {
        this.setStyle({ opacity: 0.6, weight: this.options.weight - 1 });
    });

    // Store route reference
    window.flightRoutes.push(curve);

    // Add plane icon marker at midpoint
    addPlaneMarker(midLat, midLon, origin, destination, flightData);
}

/**
 * Add animated plane icon marker on flight route
 */
function addPlaneMarker(lat, lon, origin, destination, flightData) {
    if (!window.flightMap) return;

    // Calculate rotation angle based on flight direction
    const bearing = calculateBearing(origin.lat, origin.lon, destination.lat, destination.lon);

    // Create custom plane icon with rotation
    const planeIcon = L.divIcon({
        html: `<i data-lucide="plane" class="flight-plane-icon" style="transform: rotate(${bearing}deg);"></i>`,
        className: 'plane-marker',
        iconSize: [24, 24],
        iconAnchor: [12, 12]
    });

    // Add marker to map
    const marker = L.marker([lat, lon], {
        icon: planeIcon,
        title: `${origin.code} → ${destination.code}`
    }).addTo(window.flightMap);

    // Click event to show passenger popup
    marker.on('click', () => {
        showFlightPopup(flightData);
    });

    // Store marker reference
    window.flightMarkers.push(marker);

    // Re-initialize Lucide icons for the new SVG
    if (window.lucide) {
        lucide.createIcons();
    }
}

/**
 * Show/update flight loading progress indicator
 */
function updateFlightLoadingProgress(current, total) {
    let progressEl = document.getElementById('flight-loading-progress');

    if (!progressEl) {
        // Create progress indicator if it doesn't exist
        const mapContainer = document.getElementById('flight-map');
        progressEl = document.createElement('div');
        progressEl.id = 'flight-loading-progress';
        progressEl.style.cssText = `
            position: absolute;
            top: 10px;
            right: 10px;
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 12px 16px;
            z-index: 1000;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            font-size: 13px;
            color: var(--text-primary);
        `;
        mapContainer.appendChild(progressEl);
    }

    const percentage = Math.round((current / total) * 100);
    progressEl.innerHTML = `
        <div style="display: flex; align-items: center; gap: 12px; justify-content: space-between;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <div class="spinner" style="width: 16px; height: 16px; border-width: 2px;"></div>
                <span>Loading flights... ${current} / ${total} (${percentage}%)</span>
            </div>
            <button
                onclick="window.cancelFlightLoading()"
                style="
                    background: var(--danger-color, #f85149);
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 11px;
                    cursor: pointer;
                    transition: opacity 0.2s;
                "
                onmouseover="this.style.opacity='0.8'"
                onmouseout="this.style.opacity='1'"
            >Cancel</button>
        </div>
    `;
}

/**
 * Hide flight loading progress indicator
 */
function hideFlightLoadingProgress() {
    const progressEl = document.getElementById('flight-loading-progress');
    if (progressEl) {
        progressEl.remove();
    }
}

/**
 * Load flight routes from API and display on map
 * Uses progressive loading to prevent UI freezing
 */
async function loadFlightRoutes() {
    try {
        console.log('Loading all 1,167 flights from API...');

        // Fetch all flights from new endpoint
        // Credentials are automatically included via fetch override
        const response = await fetch('/api/flights/all');

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        console.log(`Loaded ${data.total_flights} flights across ${data.unique_routes} unique routes`);
        console.log(`Date range: ${data.date_range.start} to ${data.date_range.end}`);
        console.log(`Unique passengers: ${data.unique_passengers}`);

        // Store routes globally for filtering
        window.allFlightRoutes = data.routes;

        // Show loading progress
        updateFlightLoadingProgress(0, data.routes.length);

        // Progressive loading configuration
        const BATCH_SIZE = 10; // Render 10 flights at a time
        const BATCH_DELAY = 50; // 50ms delay between batches
        let currentIndex = 0;
        let cancelled = false;

        // Store cancellation function globally
        window.cancelFlightLoading = () => {
            cancelled = true;
            hideFlightLoadingProgress();
        };

        // Process routes in batches (async, non-blocking)
        function loadNextBatch() {
            if (cancelled) {
                console.log('Flight loading cancelled by user');
                return;
            }

            if (currentIndex >= data.routes.length) {
                // All routes loaded - finish up
                finishFlightLoading(data);
                return;
            }

            // Get next batch
            const endIndex = Math.min(currentIndex + BATCH_SIZE, data.routes.length);
            const batch = data.routes.slice(currentIndex, endIndex);

            // Render batch
            batch.forEach(route => {
                // Create flight data for popup (use first flight for basic info)
                const firstFlight = route.flights[0];
                const allPassengers = new Set();

                // Collect all unique passengers across all flights on this route
                route.flights.forEach(flight => {
                    flight.passengers.forEach(p => allPassengers.add(p));
                });

                const flightData = {
                    from: route.origin.code,
                    to: route.destination.code,
                    fromName: route.origin.name,
                    toName: route.destination.name,
                    date: firstFlight.date,
                    passengers: Array.from(allPassengers),
                    flights: route.flights,  // Include all flights on this route
                    frequency: route.frequency
                };

                drawFlightPath(route.origin, route.destination, flightData, route.frequency);
            });

            // Update progress
            currentIndex = endIndex;
            updateFlightLoadingProgress(currentIndex, data.routes.length);

            // Schedule next batch
            setTimeout(loadNextBatch, BATCH_DELAY);
        }

        // Start progressive loading
        loadNextBatch();

    } catch (error) {
        console.error('Error loading flight routes:', error);
        showToast(`Error loading flights: ${error.message}`, 'error');
        hideFlightLoadingProgress();
    }
}

/**
 * Finish flight loading - add airports and update stats
 */
function finishFlightLoading(data) {
    // Add airport markers for all unique airports
    const airportSet = new Set();
    data.routes.forEach(route => {
        airportSet.add(JSON.stringify({
            code: route.origin.code,
            name: route.origin.name,
            lat: route.origin.lat,
            lon: route.origin.lon
        }));
        airportSet.add(JSON.stringify({
            code: route.destination.code,
            name: route.destination.name,
            lat: route.destination.lat,
            lon: route.destination.lon
        }));
    });

    // Add markers for each unique airport
    airportSet.forEach(airportJson => {
        const airport = JSON.parse(airportJson);
        addAirportMarker(airport);
    });

    // Update statistics display
    updateFlightStats({
        total: data.total_flights,
        unique_routes: data.unique_routes,
        unique_passengers: data.unique_passengers,
        date_range: data.date_range
    });

    // Hide progress indicator
    hideFlightLoadingProgress();

    // Auto-zoom to fit all flights (only if user hasn't manually zoomed)
    if (window.flightBounds && !window.userHasZoomed) {
        fitMapToFlightBounds();
    }

    // Initialize timeline slider with loaded data
    initFlightTimeline();

    // Re-initialize Lucide icons for all new buttons
    if (window.lucide) {
        lucide.createIcons();
    }

    console.log(`✓ Map initialized with ${data.unique_routes} routes and ${airportSet.size} airports`);
}

/**
 * Add airport marker to map
 */
function addAirportMarker(airport) {
    if (!window.flightMap) return;

    const airportIcon = L.divIcon({
        html: `<div style="background: var(--accent-color); color: white; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; white-space: nowrap; box-shadow: 0 2px 8px rgba(0,0,0,0.3);">${airport.code}</div>`,
        className: 'airport-marker',
        iconSize: [40, 24],
        iconAnchor: [20, 12]
    });

    const marker = L.marker([airport.lat, airport.lon], {
        icon: airportIcon,
        title: airport.name
    }).addTo(window.flightMap);

    marker.bindPopup(`<strong>${airport.name}</strong><br/>${airport.code}`);
}

/**
 * Fit map view to all current flight bounds with smooth animation
 */
function fitMapToFlightBounds() {
    if (!window.flightMap || !window.flightBounds) {
        console.warn('Cannot fit bounds: map or bounds not initialized');
        return;
    }

    // Check if bounds are valid (has at least one point)
    if (!window.flightBounds.isValid()) {
        console.warn('Flight bounds are not valid');
        return;
    }

    // Calculate zoom level based on number of distinct points
    // For single point or very close points, use moderate zoom
    const southwest = window.flightBounds.getSouthWest();
    const northeast = window.flightBounds.getNorthEast();
    const latDiff = Math.abs(northeast.lat - southwest.lat);
    const lngDiff = Math.abs(northeast.lng - southwest.lng);
    const isSinglePoint = latDiff < 0.1 && lngDiff < 0.1;

    // Debug logging
    console.log('🗺️ Fitting map to bounds:', {
        bounds: window.flightBounds.toBBoxString(),
        southwest: southwest,
        northeast: northeast,
        latDiff: latDiff,
        lngDiff: lngDiff,
        isSinglePoint: isSinglePoint,
        currentCenter: window.flightMap.getCenter(),
        currentZoom: window.flightMap.getZoom()
    });

    const fitOptions = {
        padding: [50, 50], // 50px padding on all sides
        maxZoom: isSinglePoint ? 8 : 12, // Don't zoom too close for single flights
        animate: true,
        duration: 0.5 // 500ms smooth animation
    };

    // Set flag to indicate this is a programmatic zoom
    window.programmaticZoom = true;
    window.flightMap.fitBounds(window.flightBounds, fitOptions);

    // Clear the flag after animation completes
    setTimeout(() => {
        window.programmaticZoom = false;
        console.log('🗺️ Map fitted. New state:', {
            center: window.flightMap.getCenter(),
            zoom: window.flightMap.getZoom()
        });
    }, 600);
}

/**
 * Reset map view to show all flights (user-triggered)
 */
function resetMapView() {
    if (!window.flightBounds) {
        console.warn('No flight bounds to reset to');
        showToast('No flights loaded yet', 'warning');
        return;
    }

    // Reset user zoom flag and fit bounds
    window.userHasZoomed = false;
    fitMapToFlightBounds();
    console.log('Map view reset to show all flights');
}

// Make flight functions globally available
window.showFlightPopup = showFlightPopup;
window.closeFlightPopup = closeFlightPopup;
window.toggleStatsPanel = toggleStatsPanel;
window.viewPassengerNetwork = viewPassengerNetwork;
window.applyFlightFilters = applyFlightFilters;
window.clearFlightFilters = clearFlightFilters;
window.initFlightsView = initFlightsView;
window.resetMapView = resetMapView;
window.fitMapToFlightBounds = fitMapToFlightBounds;

// ========================================
// TIMELINE DEBUG AUTO-LOADER
// ========================================
// This helps diagnose why timeline isn't loading
console.log('🧪 Timeline Debug Auto-Loader Initialized');

window.addEventListener('DOMContentLoaded', () => {
    console.log('🧪 DEBUG: DOMContentLoaded event fired');
    console.log('🧪 DEBUG: loadTimeline function exists:', typeof loadTimeline);

    // Wait a bit for everything to initialize
    setTimeout(() => {
        const container = document.getElementById('timeline-events');
        console.log('🧪 DEBUG: Timeline container found:', container ? 'YES' : 'NO');

        if (container) {
            console.log('🧪 DEBUG: Container HTML:', container.innerHTML.substring(0, 200));
        }

        // Test if we're on the timeline tab
        const timelineTab = document.querySelector('.tab-content[data-tab="timeline"]');
        if (timelineTab) {
            console.log('🧪 DEBUG: Timeline tab element found');
            console.log('🧪 DEBUG: Timeline tab is active:', timelineTab.classList.contains('active'));
        }
    }, 500);
});
