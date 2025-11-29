/**
 * Event Bus for Component Communication
 * Simple pub/sub system for decoupled component communication
 */

export class EventBus {
    constructor() {
        this.events = new Map();
        this.debug = false;
    }

    /**
     * Subscribe to an event
     * @param {string} eventName - Name of event
     * @param {Function} callback - Callback function
     * @returns {Function} Unsubscribe function
     */
    on(eventName, callback) {
        if (!this.events.has(eventName)) {
            this.events.set(eventName, []);
        }

        this.events.get(eventName).push(callback);

        // Return unsubscribe function
        return () => this.off(eventName, callback);
    }

    /**
     * Subscribe to an event (one-time only)
     * @param {string} eventName - Name of event
     * @param {Function} callback - Callback function
     */
    once(eventName, callback) {
        const onceWrapper = (...args) => {
            callback(...args);
            this.off(eventName, onceWrapper);
        };
        this.on(eventName, onceWrapper);
    }

    /**
     * Unsubscribe from an event
     * @param {string} eventName - Name of event
     * @param {Function} callback - Callback function to remove
     */
    off(eventName, callback) {
        if (!this.events.has(eventName)) return;

        const callbacks = this.events.get(eventName);
        const index = callbacks.indexOf(callback);

        if (index > -1) {
            callbacks.splice(index, 1);
        }

        // Clean up empty event arrays
        if (callbacks.length === 0) {
            this.events.delete(eventName);
        }
    }

    /**
     * Emit an event
     * @param {string} eventName - Name of event
     * @param {*} data - Data to pass to callbacks
     */
    emit(eventName, data) {
        if (this.debug) {
            console.log(`[EventBus] Emitting: ${eventName}`, data);
        }

        if (!this.events.has(eventName)) return;

        const callbacks = this.events.get(eventName);
        callbacks.forEach(callback => {
            try {
                callback(data);
            } catch (error) {
                console.error(`Error in event handler for ${eventName}:`, error);
            }
        });
    }

    /**
     * Clear all event listeners
     */
    clear() {
        this.events.clear();
    }

    /**
     * Get all registered events
     * @returns {string[]} Array of event names
     */
    getEvents() {
        return Array.from(this.events.keys());
    }

    /**
     * Get listener count for an event
     * @param {string} eventName - Name of event
     * @returns {number} Number of listeners
     */
    listenerCount(eventName) {
        return this.events.has(eventName) ? this.events.get(eventName).length : 0;
    }

    /**
     * Enable debug logging
     */
    enableDebug() {
        this.debug = true;
    }

    /**
     * Disable debug logging
     */
    disableDebug() {
        this.debug = false;
    }
}

// Singleton instance
export const eventBus = new EventBus();

// Backward compatibility - expose to window
if (typeof window !== 'undefined') {
    window.__eventBus = eventBus;
}

export default eventBus;
