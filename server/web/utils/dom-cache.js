/**
 * DOM Cache Utility
 * Replaces 173+ getElementById calls with cached lookups for better performance
 */
export class DOMCache {
    constructor() {
        this.cache = new Map();
        this.stats = {
            hits: 0,
            misses: 0,
            lookups: 0
        };
    }

    /**
     * Get element by ID with caching
     * @param {string} id - Element ID
     * @returns {HTMLElement|null} Cached or fresh DOM element
     */
    get(id) {
        this.stats.lookups++;

        if (!this.cache.has(id)) {
            this.stats.misses++;
            const element = document.getElementById(id);
            if (element) {
                this.cache.set(id, element);
            } else {
                // Don't cache null to allow for dynamic elements
                return null;
            }
        } else {
            this.stats.hits++;
        }

        return this.cache.get(id);
    }

    /**
     * Invalidate a cached element (e.g., after DOM manipulation)
     * @param {string} id - Element ID to invalidate
     */
    invalidate(id) {
        this.cache.delete(id);
    }

    /**
     * Clear all cached elements
     */
    clear() {
        this.cache.clear();
    }

    /**
     * Get cache statistics
     * @returns {Object} Stats object with hits, misses, hit rate
     */
    getStats() {
        const hitRate = this.stats.lookups > 0
            ? (this.stats.hits / this.stats.lookups * 100).toFixed(2)
            : 0;

        return {
            ...this.stats,
            hitRate: `${hitRate}%`,
            cacheSize: this.cache.size
        };
    }

    /**
     * Pre-cache common elements at page load
     * @param {string[]} ids - Array of element IDs to pre-cache
     */
    preCache(ids) {
        ids.forEach(id => this.get(id));
    }
}

// Singleton instance
export const domCache = new DOMCache();

// Backward compatibility - expose to window
window.__domCache = domCache;

// Helper function for backward compatibility
export function getElementById(id) {
    return domCache.get(id);
}
