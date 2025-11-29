/**
 * Epstein Archive Explorer - Modular Client Application
 * Phase 1: Infrastructure modules integrated
 */

// Import core modules
import { appState } from './core/state-manager.js';
import { eventBus } from './core/event-bus.js';

// Import utilities
import { domCache } from './utils/dom-cache.js';
import {
    formatEntityName,
    escapeHtml,
    escapeForJS,
    formatDate,
    formatNumber,
    truncate,
    capitalize
} from './utils/formatter.js';
import { loadMarkedJS, renderMarkdown } from './utils/markdown.js';

// Import components
import { Toast } from './components/toast.js';

// API Configuration
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
    console.log('Authentication check disabled');
    return true;
}

// Override fetch to always include credentials
const originalFetch = window.fetch;
window.fetch = function(url, options = {}) {
    if (!options.credentials) {
        options.credentials = 'include';
    }
    return originalFetch(url, options);
};

// Pre-cache common DOM elements on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Initializing Epstein Archive Explorer (Modular)');

    // Pre-cache frequently accessed elements
    const commonElements = [
        'toast',
        'entity-list',
        'network-graph',
        'timeline-container',
        'flight-map',
        'entity-details',
        'search-input',
        'filter-panel'
    ];

    domCache.preCache(commonElements);

    console.log('✅ DOM cache initialized with', commonElements.length, 'elements');
    console.log('📊 Cache stats:', domCache.getStats());

    // Initialize state
    console.log('✅ State manager initialized');
    console.log('✅ Event bus ready');

    // Load markdown library for entity bios
    loadMarkedJS().then(() => {
        console.log('✅ Markdown renderer ready');
    }).catch(err => {
        console.error('❌ Failed to load markdown renderer:', err);
    });

    // Show welcome toast
    Toast.success('Application initialized successfully', 2000);

    // Log module status
    console.log('\n📦 Loaded Modules:');
    console.log('  - State Manager:', typeof appState);
    console.log('  - Event Bus:', typeof eventBus);
    console.log('  - DOM Cache:', typeof domCache);
    console.log('  - Formatters:', typeof formatEntityName);
    console.log('  - Toast:', typeof Toast);
    console.log('  - Markdown:', typeof renderMarkdown);

    // Backward compatibility check
    console.log('\n🔄 Backward Compatibility:');
    console.log('  - window.__appState:', typeof window.__appState);
    console.log('  - window.__domCache:', typeof window.__domCache);
    console.log('  - window.showToast:', typeof window.showToast);
    console.log('  - window.__formatter:', typeof window.__formatter);
});

// Export for backward compatibility and debugging
window.modules = {
    appState,
    eventBus,
    domCache,
    Toast,
    formatEntityName,
    escapeHtml,
    escapeForJS,
    formatDate,
    formatNumber,
    truncate,
    capitalize,
    renderMarkdown
};

console.log('✨ Modular app.js loaded - Phase 1 complete');

// ============================================================================
// PLACEHOLDER: Original app.js functions will be gradually migrated below
// ============================================================================

// Example: How to use the new modules in existing functions

// OLD WAY:
// let networkData = null;
// document.getElementById('entity-list').innerHTML = '...';

// NEW WAY:
// appState.set('network.data', data);
// const entityList = domCache.get('entity-list');
// entityList.innerHTML = '...';

// Example function using new modules
async function loadEntityData() {
    try {
        const response = await fetch(`${API_BASE}/entities`);
        const data = await response.json();

        // Store in state manager
        appState.set('entities.list', data.entities || []);

        // Use DOM cache
        const entityList = domCache.get('entity-list');
        if (entityList) {
            // Use formatter
            const html = data.entities.map(e =>
                `<div>${formatEntityName(e.name)}</div>`
            ).join('');
            entityList.innerHTML = html;
        }

        // Show success toast
        Toast.success('Entities loaded successfully');

        // Emit event for other components
        eventBus.emit('entities:loaded', data.entities);

    } catch (error) {
        console.error('Error loading entities:', error);
        Toast.error('Failed to load entities');
    }
}

// Example: Subscribe to state changes
appState.subscribe('network.selectedNode', (node) => {
    console.log('Selected node changed:', node);
    eventBus.emit('node:selected', node);
});

// Example: Event bus usage
eventBus.on('entities:loaded', (entities) => {
    console.log('Entities loaded event received:', entities.length);
});

// Expose example function for testing
window.loadEntityData = loadEntityData;
