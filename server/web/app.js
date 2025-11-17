// Epstein Archive Explorer - Client Application
const API_BASE = window.location.protocol + '//' + window.location.host + '/api';

let networkData = null;
let simulation = null;
let svg = null;
let g = null;
let node = null;
let link = null;
let label = null;
let zoom = null;

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

    // Sort patterns by length (longest first) to avoid partial matches
    const patterns = Object.keys(featureLinks).sort((a, b) => b.length - a.length);

    patterns.forEach(pattern => {
        const link = featureLinks[pattern];
        // Case-insensitive match, but preserve original case in non-link text
        const regex = new RegExp(`\\b(${pattern})\\b`, 'gi');
        enhanced = enhanced.replace(regex, (match) => {
            return `<a href="javascript:void(0)" onclick="${link.action}" class="feature-link">${match}</a>`;
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

    // Load marked.js for markdown rendering
    loadMarkedJS().catch(err => {
        console.warn('Failed to load marked.js, using fallback renderer:', err);
    });

    await loadStats();
    loadIngestionStatus();
    await loadNetworkData();
    await loadEntitiesList();
});

// Load statistics
async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/stats`);
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
        const response = await fetch(`${API_BASE}/ingestion/status`);
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

        document.getElementById('ingestion-progress').innerHTML = progressHTML;
        document.getElementById('overview-ocr').textContent = `OCR: ${data.files_processed.toLocaleString()}/${data.total_files.toLocaleString()} (${data.progress_percentage.toFixed(1)}%)`;
    } catch (error) {
        console.error('Failed to load ingestion status:', error);
        document.getElementById('ingestion-progress').innerHTML = '<p style="color: #8b949e;">Unable to load ingestion status</p>';
    }
}

// Load and render roadmap
let roadmapLoaded = false;
async function loadRoadmap() {
    if (roadmapLoaded) return;

    try {
        // Ensure marked.js is loaded first
        await loadMarkedJS();

        const response = await fetch('/ROADMAP.md');
        const markdown = await response.text();

        // Use renderMarkdown for full markdown support with feature links
        const html = renderMarkdown(markdown);
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

// Note: markdownToHTML() removed - using renderMarkdown() for all markdown rendering
// renderMarkdown() provides full marked.js support with feature link enhancement

// Tab switching
function switchTab(tabName, clickedTab) {
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
}

// Load network data
async function loadNetworkData() {
    if (networkData) return networkData;

    try {
        const response = await fetch(`${API_BASE}/network`);
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

    // Create simulation
    simulation = d3.forceSimulation(networkData.nodes)
        .force('link', d3.forceLink(networkData.edges)
            .id(d => d.id)
            .distance(50))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(20));

    const rootStyles = getComputedStyle(document.documentElement);
    const borderColor = rootStyles.getPropertyValue('--border-color').trim();
    const accentBlue = rootStyles.getPropertyValue('--accent-blue').trim();
    const bgPrimary = rootStyles.getPropertyValue('--bg-primary').trim();
    const textPrimary = rootStyles.getPropertyValue('--text-primary').trim();

    // Create links
    link = g.append('g')
        .selectAll('line')
        .data(networkData.edges)
        .join('line')
        .attr('stroke', borderColor)
        .attr('stroke-width', d => Math.sqrt(d.weight || 1))
        .attr('stroke-opacity', 0.6);

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

    // Add labels
    label = g.append('g')
        .selectAll('text')
        .data(networkData.nodes)
        .join('text')
        .text(d => d.id)
        .attr('font-size', 10)
        .attr('fill', textPrimary)
        .attr('dx', 12)
        .attr('dy', 4)
        .style('pointer-events', 'none');

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
    });

    // Apply initial filters
    applyFilters();
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
    document.getElementById('connected-entity-name').textContent = node.id;
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
        connectionsList.innerHTML = connections.map(conn => `
            <div class="connection-item" onclick="selectNode('${conn.name.replace(/'/g, "\\'")}')">
                <span class="entity-name">${conn.name}</span>
                <span class="connection-strength">${conn.weight} co-occurrence${conn.weight > 1 ? 's' : ''}</span>
            </div>
        `).join('');
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
                const entitiesText = 'Found entities: ' + data.search_results.entities.map(e => e.name).join(', ');
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
        const response = await fetch(`${API_BASE}/entities`);
        const entities = await response.json();
        allEntitiesData = entities;
        renderEntitiesList(entities);
    } catch (error) {
        console.error('Failed to load entities:', error);
        document.getElementById('entities-list').innerHTML = '<div class="chat-message system" style="grid-column: 1/-1; text-align: center; padding: 40px;">Failed to load entities</div>';
    }
}

function renderEntitiesList(entities) {
    const container = document.getElementById('entities-list');

    if (!entities || entities.length === 0) {
        container.innerHTML = '<div class="chat-message system" style="grid-column: 1/-1; text-align: center; padding: 40px;">No entities found</div>';
        return;
    }

    container.innerHTML = entities.map(entity => `
        <div class="entity-card"
             data-entity-name="${entity.name.replace(/"/g, '&quot;')}"
             onclick="showEntityDetails('${entity.name.replace(/'/g, "\\'")}')">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
                <h4 style="font-size: 15px; font-weight: 600; margin: 0; color: var(--text-primary);">
                    ${entity.name}
                </h4>
                ${entity.is_billionaire ? '<span class="billionaire-badge">BILLIONAIRE</span>' : ''}
            </div>
            <div style="display: flex; gap: 16px; font-size: 12px; color: var(--text-secondary);">
                <div>
                    <div style="color: var(--accent-blue); font-weight: 600; font-size: 16px;">${entity.connection_count || 0}</div>
                    <div>Connections</div>
                </div>
                <div>
                    <div style="color: var(--accent-blue); font-weight: 600; font-size: 16px;">${entity.total_documents || 0}</div>
                    <div>Documents</div>
                </div>
                ${entity.flight_count ? `<div>
                    <div style="color: var(--accent-blue); font-weight: 600; font-size: 16px;">${entity.flight_count}</div>
                    <div>Flights</div>
                </div>` : ''}
            </div>
        </div>
    `).join('');
}

function filterEntities(searchQuery) {
    const filter = document.getElementById('entity-filter').value;
    const query = searchQuery.toLowerCase();

    let filtered = allEntitiesData;

    if (query) {
        filtered = filtered.filter(entity =>
            entity.name.toLowerCase().includes(query)
        );
    }

    if (filter === 'billionaire') {
        filtered = filtered.filter(entity => entity.is_billionaire);
    } else if (filter === 'high-connections') {
        filtered = filtered.filter(entity => (entity.connection_count || 0) > 10);
    }

    renderEntitiesList(filtered);
}

function showEntityDetails(entityName) {
    const entity = allEntitiesData.find(e => e.name === entityName);
    if (!entity) return;

    switchTab('network');

    if (!simulation) {
        renderNetwork().then(() => {
            selectNode(entityName);
        });
    } else {
        selectNode(entityName);
    }
}
