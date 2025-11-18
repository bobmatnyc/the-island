/**
 * API Client - Frontend API abstraction layer
 *
 * Design Decision: API-First Architecture
 * Rationale: All business logic moved to backend services.
 * Frontend makes simple API calls and renders results.
 *
 * No business logic in this file - just API calls.
 * All filtering, sorting, calculations happen server-side.
 */

const API_BASE = window.location.protocol + '//' + window.location.host;
const API_V2_BASE = API_BASE + '/api/v2';

/**
 * Generic fetch wrapper with error handling
 */
async function apiFetch(url, options = {}) {
    // Always include credentials for session cookies
    if (!options.credentials) {
        options.credentials = 'include';
    }

    try {
        const response = await fetch(url, options);

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
            throw new Error(error.detail || `HTTP ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

/**
 * ============================================================================
 * Entity API
 * ============================================================================
 */

const EntityAPI = {
    /**
     * Get filtered entity list
     * @param {Object} filters - { search, entity_type, tag, source, filter_billionaires, filter_connected, sort_by, limit, offset }
     * @returns {Promise<{entities, total, offset, limit}>}
     */
    async getEntities(filters = {}) {
        const params = new URLSearchParams();

        if (filters.search) params.append('search', filters.search);
        if (filters.entity_type) params.append('entity_type', filters.entity_type);
        if (filters.tag) params.append('tag', filters.tag);
        if (filters.source) params.append('source', filters.source);
        if (filters.filter_billionaires) params.append('filter_billionaires', 'true');
        if (filters.filter_connected) params.append('filter_connected', 'true');
        if (filters.sort_by) params.append('sort_by', filters.sort_by);
        if (filters.limit) params.append('limit', filters.limit);
        if (filters.offset) params.append('offset', filters.offset);

        return apiFetch(`${API_V2_BASE}/entities?${params}`);
    },

    /**
     * Get single entity with all details
     * @param {string} entityName - Entity name
     * @returns {Promise<Object>} Entity data with bio, tags, connections
     */
    async getEntity(entityName) {
        return apiFetch(`${API_V2_BASE}/entities/${encodeURIComponent(entityName)}`);
    },

    /**
     * Get entity connections
     * @param {string} entityName - Entity name
     * @param {Object} options - { max_hops, min_strength }
     * @returns {Promise<{entity, direct_connections, network}>}
     */
    async getEntityConnections(entityName, options = {}) {
        const params = new URLSearchParams();
        if (options.max_hops) params.append('max_hops', options.max_hops);
        if (options.min_strength) params.append('min_strength', options.min_strength);

        return apiFetch(`${API_V2_BASE}/entities/${encodeURIComponent(entityName)}/connections?${params}`);
    },

    /**
     * Get entity statistics
     * @returns {Promise<{total_entities, by_type, by_tag, billionaires, connected}>}
     */
    async getStatistics() {
        return apiFetch(`${API_V2_BASE}/entities/stats/summary`);
    }
};

/**
 * ============================================================================
 * Flight API
 * ============================================================================
 */

const FlightAPI = {
    /**
     * Get filtered flight list
     * @param {Object} filters - { passenger, from_airport, to_airport, start_date, end_date, limit, offset }
     * @returns {Promise<{flights, total, filters}>}
     */
    async getFlights(filters = {}) {
        const params = new URLSearchParams();

        if (filters.passenger) params.append('passenger', filters.passenger);
        if (filters.from_airport) params.append('from_airport', filters.from_airport);
        if (filters.to_airport) params.append('to_airport', filters.to_airport);
        if (filters.start_date) params.append('start_date', filters.start_date);
        if (filters.end_date) params.append('end_date', filters.end_date);
        if (filters.limit) params.append('limit', filters.limit);
        if (filters.offset) params.append('offset', filters.offset);

        return apiFetch(`${API_V2_BASE}/flights?${params}`);
    },

    /**
     * Get flights grouped by route for map visualization
     * @returns {Promise<{routes, total_flights, unique_routes, unique_passengers, date_range, airports}>}
     */
    async getFlightRoutes() {
        return apiFetch(`${API_V2_BASE}/flights/routes`);
    },

    /**
     * Get flights for specific passenger
     * @param {string} passengerName - Passenger name
     * @returns {Promise<{passenger, flights, total_flights, routes, date_range}>}
     */
    async getPassengerFlights(passengerName) {
        return apiFetch(`${API_V2_BASE}/flights/passenger/${encodeURIComponent(passengerName)}`);
    },

    /**
     * Get flight statistics
     * @returns {Promise<{total_flights, unique_passengers, unique_routes}>}
     */
    async getStatistics() {
        return apiFetch(`${API_V2_BASE}/flights/stats`);
    }
};

/**
 * ============================================================================
 * Document API
 * ============================================================================
 */

const DocumentAPI = {
    /**
     * Search documents with filters
     * @param {Object} filters - { q, entity, doc_type, source, classification, limit, offset }
     * @returns {Promise<{documents, total, facets}>}
     */
    async searchDocuments(filters = {}) {
        const params = new URLSearchParams();

        if (filters.q) params.append('q', filters.q);
        if (filters.entity) params.append('entity', filters.entity);
        if (filters.doc_type) params.append('doc_type', filters.doc_type);
        if (filters.source) params.append('source', filters.source);
        if (filters.classification) params.append('classification', filters.classification);
        if (filters.limit) params.append('limit', filters.limit);
        if (filters.offset) params.append('offset', filters.offset);

        return apiFetch(`${API_V2_BASE}/documents/search?${params}`);
    },

    /**
     * Get single document with full content
     * @param {string} docId - Document ID
     * @returns {Promise<{document, content}>}
     */
    async getDocument(docId) {
        return apiFetch(`${API_V2_BASE}/documents/${encodeURIComponent(docId)}`);
    },

    /**
     * Get documents mentioning entity
     * @param {string} entityName - Entity name
     * @returns {Promise<{entity, documents, total}>}
     */
    async getEntityDocuments(entityName) {
        return apiFetch(`${API_V2_BASE}/documents/entity/${encodeURIComponent(entityName)}`);
    },

    /**
     * Get document statistics
     * @returns {Promise<{total_documents, by_type, by_classification, by_source}>}
     */
    async getStatistics() {
        return apiFetch(`${API_V2_BASE}/documents/stats`);
    }
};

/**
 * ============================================================================
 * Network API
 * ============================================================================
 */

const NetworkAPI = {
    /**
     * Get network graph data
     * @param {Object} options - { min_connections, max_nodes, deduplicate, entity_filter }
     * @returns {Promise<{nodes, edges, metadata}>}
     */
    async getNetworkGraph(options = {}) {
        const params = new URLSearchParams();

        if (options.min_connections !== undefined) params.append('min_connections', options.min_connections);
        if (options.max_nodes) params.append('max_nodes', options.max_nodes);
        if (options.deduplicate !== undefined) params.append('deduplicate', options.deduplicate);
        if (options.entity_filter) params.append('entity_filter', options.entity_filter);

        return apiFetch(`${API_V2_BASE}/network/graph?${params}`);
    },

    /**
     * Find shortest path between two entities
     * @param {string} entityA - First entity name
     * @param {string} entityB - Second entity name
     * @returns {Promise<{path, edges, distance, found}>}
     */
    async findPath(entityA, entityB) {
        const params = new URLSearchParams({
            entity_a: entityA,
            entity_b: entityB
        });

        return apiFetch(`${API_V2_BASE}/network/path?${params}`);
    },

    /**
     * Get subgraph centered on entity
     * @param {string} entityName - Entity name
     * @param {Object} options - { max_hops, min_strength }
     * @returns {Promise<{center, nodes, edges, metadata}>}
     */
    async getEntitySubgraph(entityName, options = {}) {
        const params = new URLSearchParams();
        if (options.max_hops) params.append('max_hops', options.max_hops);
        if (options.min_strength) params.append('min_strength', options.min_strength);

        return apiFetch(`${API_V2_BASE}/network/subgraph/${encodeURIComponent(entityName)}?${params}`);
    },

    /**
     * Get network statistics
     * @returns {Promise<{total_nodes, total_edges, density, most_connected}>}
     */
    async getStatistics() {
        return apiFetch(`${API_V2_BASE}/network/stats`);
    }
};

/**
 * ============================================================================
 * Unified Search API
 * ============================================================================
 */

const SearchAPI = {
    /**
     * Unified search across all data types
     * @param {string} query - Search query
     * @param {Object} options - { type, limit }
     * @returns {Promise<{query, results, total}>}
     */
    async search(query, options = {}) {
        const params = new URLSearchParams({ q: query });

        if (options.type) params.append('type', options.type);
        if (options.limit) params.append('limit', options.limit);

        return apiFetch(`${API_V2_BASE}/search?${params}`);
    }
};

/**
 * ============================================================================
 * Legacy API v1 (backward compatibility)
 * ============================================================================
 */

const LegacyAPI = {
    /**
     * Get stats (v1 endpoint for backward compatibility)
     */
    async getStats() {
        return apiFetch(`${API_BASE}/api/stats`);
    },

    /**
     * Get entity biographies
     */
    async getEntityBiographies() {
        return apiFetch(`${API_BASE}/api/entity-biographies`);
    },

    /**
     * Get entity tags
     */
    async getEntityTags() {
        return apiFetch(`${API_BASE}/api/entity-tags`);
    },

    /**
     * Get old network endpoint (v1)
     */
    async getNetwork(options = {}) {
        const params = new URLSearchParams();
        if (options.min_connections) params.append('min_connections', options.min_connections);
        if (options.max_nodes) params.append('max_nodes', options.max_nodes);
        if (options.deduplicate !== undefined) params.append('deduplicate', options.deduplicate);

        return apiFetch(`${API_BASE}/api/network?${params}`);
    }
};

/**
 * ============================================================================
 * Export API Client
 * ============================================================================
 */

// Export as global for use in existing code
window.API = {
    Entity: EntityAPI,
    Flight: FlightAPI,
    Document: DocumentAPI,
    Network: NetworkAPI,
    Search: SearchAPI,
    Legacy: LegacyAPI
};

// Also export individual APIs
window.EntityAPI = EntityAPI;
window.FlightAPI = FlightAPI;
window.DocumentAPI = DocumentAPI;
window.NetworkAPI = NetworkAPI;
window.SearchAPI = SearchAPI;
window.LegacyAPI = LegacyAPI;

console.log('✓ API Client loaded (v2 endpoints)');
