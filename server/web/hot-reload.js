// Hot-Reload System using Server-Sent Events (SSE)

class HotReloadClient {
    constructor() {
        this.eventSource = null;
        this.reconnectDelay = 5000; // 5 seconds
        this.reconnectTimer = null;
        this.isConnected = false;
        this.handlers = new Map();

        // Check if SSE is supported
        this.sseSupported = typeof EventSource !== 'undefined';

        // Polling fallback
        this.pollingInterval = null;
        this.pollingDelay = 30000; // 30 seconds
        this.lastCheckTimestamps = new Map();
    }

    /**
     * Initialize hot-reload connection
     */
    init() {
        console.log('[Hot-Reload] Initializing...');

        if (this.sseSupported) {
            this.connectSSE();
        } else {
            console.warn('[Hot-Reload] SSE not supported, falling back to polling');
            this.startPolling();
        }
    }

    /**
     * Connect to SSE endpoint
     */
    connectSSE() {
        try {
            // Session is in HTTP-only cookie, EventSource will send it automatically
            // EventSource automatically includes cookies for same-origin requests
            this.eventSource = new EventSource(`/api/sse/updates`);

            this.eventSource.addEventListener('connected', (e) => {
                const data = JSON.parse(e.data);
                console.log('[Hot-Reload] Connected:', data.message);
                this.isConnected = true;
                this.clearReconnectTimer();
            });

            this.eventSource.addEventListener('ping', (e) => {
                // Keepalive ping - no action needed
                console.debug('[Hot-Reload] Keepalive ping received');
            });

            // Listen for data update events
            this.eventSource.addEventListener('entity_network_updated', (e) => {
                this.handleUpdate('entity_network', e);
            });

            this.eventSource.addEventListener('timeline_updated', (e) => {
                this.handleUpdate('timeline', e);
            });

            this.eventSource.addEventListener('entities_updated', (e) => {
                this.handleUpdate('entities', e);
            });

            this.eventSource.addEventListener('documents_updated', (e) => {
                this.handleUpdate('documents', e);
            });

            this.eventSource.addEventListener('cases_updated', (e) => {
                this.handleUpdate('cases', e);
            });

            this.eventSource.addEventListener('victims_updated', (e) => {
                this.handleUpdate('victims', e);
            });

            this.eventSource.addEventListener('entity_mappings_updated', (e) => {
                this.handleUpdate('entity_mappings', e);
            });

            this.eventSource.addEventListener('entity_filter_updated', (e) => {
                this.handleUpdate('entity_filter', e);
            });

            // Handle errors and reconnection
            this.eventSource.onerror = (error) => {
                console.error('[Hot-Reload] Connection error:', error);
                this.isConnected = false;

                // Close and reconnect
                this.eventSource.close();
                this.scheduleReconnect();
            };

        } catch (error) {
            console.error('[Hot-Reload] Failed to connect:', error);
            this.scheduleReconnect();
        }
    }

    /**
     * Handle update event
     */
    handleUpdate(dataType, event) {
        try {
            const data = JSON.parse(event.data);
            console.log(`[Hot-Reload] ${dataType} updated:`, data.filename);

            // Show toast notification
            this.showToast(`${dataType.replace('_', ' ')} updated - reloading...`);

            // Call registered handlers
            const handlers = this.handlers.get(dataType) || [];
            handlers.forEach(handler => {
                try {
                    handler(data);
                } catch (err) {
                    console.error(`[Hot-Reload] Handler error for ${dataType}:`, err);
                }
            });

        } catch (error) {
            console.error('[Hot-Reload] Failed to parse update event:', error);
        }
    }

    /**
     * Register handler for specific data type
     */
    on(dataType, handler) {
        if (!this.handlers.has(dataType)) {
            this.handlers.set(dataType, []);
        }
        this.handlers.get(dataType).push(handler);
    }

    /**
     * Schedule reconnection attempt
     */
    scheduleReconnect() {
        this.clearReconnectTimer();

        console.log(`[Hot-Reload] Reconnecting in ${this.reconnectDelay / 1000}s...`);

        this.reconnectTimer = setTimeout(() => {
            if (this.sseSupported) {
                this.connectSSE();
            } else {
                this.startPolling();
            }
        }, this.reconnectDelay);
    }

    /**
     * Clear reconnect timer
     */
    clearReconnectTimer() {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
    }

    /**
     * Fallback polling method (for browsers without SSE)
     */
    async startPolling() {
        console.log('[Hot-Reload] Starting polling mode');

        // Initial check
        await this.pollForUpdates();

        // Set up interval
        this.pollingInterval = setInterval(() => {
            this.pollForUpdates();
        }, this.pollingDelay);
    }

    /**
     * Poll for file updates
     */
    async pollForUpdates() {
        try {
            // Check entity network
            await this.checkFileModified('entity_network', '/api/network');

            // Check timeline
            await this.checkFileModified('timeline', '/api/timeline');

            // Check entities (lightweight check - just count)
            await this.checkFileModified('entities', '/api/entities?limit=1');

        } catch (error) {
            console.error('[Hot-Reload] Polling error:', error);
        }
    }

    /**
     * Check if file was modified
     */
    async checkFileModified(dataType, endpoint) {
        try {
            const response = await fetch(endpoint, {
                method: 'HEAD',
                credentials: 'include' // Include session cookie
            });

            const lastModified = response.headers.get('Last-Modified');
            if (!lastModified) return;

            const timestamp = new Date(lastModified).getTime();
            const previousTimestamp = this.lastCheckTimestamps.get(dataType);

            if (previousTimestamp && timestamp > previousTimestamp) {
                // File was modified
                console.log(`[Hot-Reload] ${dataType} modified (polling)`);
                this.handleUpdate(dataType, {
                    data: JSON.stringify({
                        filename: dataType,
                        timestamp: timestamp / 1000
                    })
                });
            }

            this.lastCheckTimestamps.set(dataType, timestamp);

        } catch (error) {
            console.debug(`[Hot-Reload] Failed to check ${dataType}:`, error);
        }
    }

    /**
     * Show toast notification
     */
    showToast(message, duration = 3000) {
        // Remove existing toasts
        const existingToasts = document.querySelectorAll('.hot-reload-toast');
        existingToasts.forEach(toast => toast.remove());

        // Create new toast
        const toast = document.createElement('div');
        toast.className = 'hot-reload-toast';
        toast.textContent = message;

        // Add to DOM
        document.body.appendChild(toast);

        // Animate in
        setTimeout(() => {
            toast.classList.add('show');
        }, 10);

        // Remove after duration
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }

    /**
     * Disconnect and cleanup
     */
    disconnect() {
        console.log('[Hot-Reload] Disconnecting...');

        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }

        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }

        this.clearReconnectTimer();
        this.isConnected = false;
    }

    /**
     * Get connection status
     */
    getStatus() {
        return {
            connected: this.isConnected,
            method: this.sseSupported ? 'SSE' : 'Polling',
            handlers: this.handlers.size
        };
    }
}

// Create global instance
const hotReload = new HotReloadClient();

// Auto-initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        hotReload.init();
    });
} else {
    hotReload.init();
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    hotReload.disconnect();
});

// Export for global access
window.hotReload = hotReload;
