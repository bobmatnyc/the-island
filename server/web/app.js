// Epstein Archive Explorer - Client Application
const API_BASE = window.location.protocol + '//' + window.location.host + '/api';

let networkData = null;
let simulation = null;

// Initialize app
document.addEventListener('DOMContentLoaded', async () => {
    await loadStats();
    loadIngestionStatus();

    // Auto-load network data on first load (for overview stats)
    await loadNetworkData();

    // Load entities list
    await loadEntitiesList();
});

// Load statistics
async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/stats`);
        const data = await response.json();

        // Update header stats
        document.getElementById('stat-entities').textContent = data.total_entities.toLocaleString();
        document.getElementById('stat-connections').textContent = data.total_connections.toLocaleString();
        document.getElementById('stat-documents').textContent = data.total_documents.toLocaleString();

        // Update overview cards
        document.getElementById('overview-entities').textContent = `${data.total_entities.toLocaleString()} unique entities extracted`;
        document.getElementById('overview-connections').textContent = `${data.total_connections.toLocaleString()} network connections`;
        document.getElementById('overview-documents').textContent = `${data.total_documents.toLocaleString()} documents classified`;
        document.getElementById('overview-ocr').textContent = `OCR processing in progress...`;

        // Update sources list
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

// Tab switching
function switchTab(tabName) {
    // Update active tab
    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
    event.target.classList.add('active');

    // Update active view
    document.querySelectorAll('.view').forEach(view => view.classList.remove('active'));
    document.getElementById(`${tabName}-view`).classList.add('active');

    // Load network if switching to network tab
    if (tabName === 'network' && !simulation) {
        renderNetwork();
    }

    // Refresh ingestion status
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

    // Create SVG
    const svg = d3.select('#network-container')
        .append('svg')
        .attr('width', width)
        .attr('height', height);

    // Add zoom behavior
    const g = svg.append('g');

    svg.call(d3.zoom()
        .scaleExtent([0.1, 4])
        .on('zoom', (event) => {
            g.attr('transform', event.transform);
        }));

    // Create simulation
    simulation = d3.forceSimulation(networkData.nodes)
        .force('link', d3.forceLink(networkData.edges)
            .id(d => d.id)
            .distance(50))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(20));

    // Create links
    const link = g.append('g')
        .selectAll('line')
        .data(networkData.edges)
        .join('line')
        .attr('stroke', '#30363d')
        .attr('stroke-width', d => Math.sqrt(d.weight || 1))
        .attr('stroke-opacity', 0.6);

    // Create nodes
    const node = g.append('g')
        .selectAll('circle')
        .data(networkData.nodes)
        .join('circle')
        .attr('r', d => Math.max(5, Math.sqrt(d.connection_count || 1) * 3))
        .attr('fill', d => d.is_billionaire ? '#ffd700' : '#58a6ff')
        .attr('stroke', '#0d1117')
        .attr('stroke-width', 2)
        .style('cursor', 'pointer')
        .call(d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended))
        .on('click', (event, d) => showEntityPanel(d))
        .on('mouseover', function(event, d) {
            d3.select(this)
                .transition()
                .duration(200)
                .attr('r', Math.max(8, Math.sqrt(d.connection_count || 1) * 4));
        })
        .on('mouseout', function(event, d) {
            d3.select(this)
                .transition()
                .duration(200)
                .attr('r', Math.max(5, Math.sqrt(d.connection_count || 1) * 3));
        });

    // Add labels
    const label = g.append('g')
        .selectAll('text')
        .data(networkData.nodes)
        .join('text')
        .text(d => d.id)
        .attr('font-size', 10)
        .attr('fill', '#c9d1d9')
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
}

// Show entity details panel
function showEntityPanel(entity) {
    document.getElementById('entity-name').textContent = entity.id;
    document.getElementById('entity-connections').textContent = entity.connection_count || 0;
    document.getElementById('entity-documents').textContent = entity.total_documents || 0;
    document.getElementById('entity-billionaire').textContent = entity.is_billionaire ? 'Yes' : 'No';
    document.getElementById('entity-centrality').textContent = (entity.degree_centrality || 0).toFixed(4);

    document.getElementById('entity-panel').classList.add('show');
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

    // Add user message
    addChatMessage('user', message);
    input.value = '';

    // Add loading message
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

        // Remove loading message
        const loadingMsg = document.getElementById(loadingId);
        if (loadingMsg) loadingMsg.remove();

        // Add assistant response
        addChatMessage('assistant', data.response);

        // If search results are provided, show them
        if (data.search_results) {
            if (data.search_results.entities && data.search_results.entities.length > 0) {
                const entitiesText = '📊 Found entities: ' + data.search_results.entities.map(e => e.name).join(', ');
                addChatMessage('system', entitiesText);
            }
            if (data.search_results.documents && data.search_results.documents.length > 0) {
                const docsText = '📄 Found documents: ' + data.search_results.documents.length + ' matching files';
                addChatMessage('system', docsText);
            }
        }
    } catch (error) {
        console.error('Chat error:', error);

        // Remove loading message
        const loadingMsg = document.getElementById(loadingId);
        if (loadingMsg) loadingMsg.remove();

        addChatMessage('system', '❌ Error: Could not get response. The LLM may be unavailable or slow to respond. Please try again.');
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
    } else {
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
    // Clear form
    document.getElementById('source-url').value = '';
    document.getElementById('source-description').value = '';
    document.getElementById('source-name').value = '';
}

async function submitSource() {
    const url = document.getElementById('source-url').value.trim();
    const description = document.getElementById('source-description').value.trim();
    const name = document.getElementById('source-name').value.trim();

    if (!url || !description) {
        addChatMessage('system', '⚠️ Please provide both URL and description');
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
        addChatMessage('system', '✅ ' + data.message);
        hideSourceForm();
    } catch (error) {
        console.error('Source submission error:', error);
        addChatMessage('system', '❌ ' + error.message);
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
        document.getElementById('entities-list').innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 40px; color: #8b949e;">Failed to load entities</div>';
    }
}

function renderEntitiesList(entities) {
    const container = document.getElementById('entities-list');

    if (!entities || entities.length === 0) {
        container.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 40px; color: #8b949e;">No entities found</div>';
        return;
    }

    container.innerHTML = entities.map(entity => `
        <div style="background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; cursor: pointer; transition: all 0.2s;"
             onmouseover="this.style.borderColor='#58a6ff'; this.style.transform='translateY(-2px)'"
             onmouseout="this.style.borderColor='#30363d'; this.style.transform='translateY(0)'"
             onclick="showEntityDetails('${entity.name.replace(/'/g, "\\'")}')">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
                <h4 style="font-size: 15px; font-weight: 600; color: #f0f6fc; margin: 0;">
                    ${entity.name}
                </h4>
                ${entity.is_billionaire ? '<span style="background: linear-gradient(135deg, #ffd700, #ffed4e); color: #0d1117; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: 600;">BILLIONAIRE</span>' : ''}
            </div>
            <div style="display: flex; gap: 16px; font-size: 12px; color: #8b949e;">
                <div>
                    <div style="color: #58a6ff; font-weight: 600; font-size: 16px;">${entity.connection_count || 0}</div>
                    <div>Connections</div>
                </div>
                <div>
                    <div style="color: #58a6ff; font-weight: 600; font-size: 16px;">${entity.total_documents || 0}</div>
                    <div>Documents</div>
                </div>
                ${entity.flight_count ? `<div>
                    <div style="color: #58a6ff; font-weight: 600; font-size: 16px;">${entity.flight_count}</div>
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

    // Apply search filter
    if (query) {
        filtered = filtered.filter(entity =>
            entity.name.toLowerCase().includes(query)
        );
    }

    // Apply category filter
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

    // Switch to network tab and highlight entity
    switchTab('network');

    // If network not loaded yet, load it first
    if (!simulation) {
        renderNetwork().then(() => {
            highlightEntity(entityName);
        });
    } else {
        highlightEntity(entityName);
    }
}

function highlightEntity(entityName) {
    // Find and zoom to entity in network
    const entity = networkData.nodes.find(n => n.id === entityName);
    if (entity) {
        showEntityPanel(entity);
    }
}
