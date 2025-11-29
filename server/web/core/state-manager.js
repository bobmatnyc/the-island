/**
 * Centralized State Manager
 * Replaces 33+ global variables with reactive state management
 */
export class StateManager {
    constructor() {
        this.state = {
            network: {
                data: null,
                simulation: null,
                svg: null,
                g: null,
                node: null,
                link: null,
                label: null,
                zoom: null,
                selectedNode: null,
                visibleNodes: new Set(),
                connectionSliderValue: 300
            },
            entities: {
                bios: {},
                tags: {},
                list: [],
                searchResults: [],
                currentSearchIndex: 0,
                activeFilters: {
                    billionaires: false,
                    high: false,
                    medium: false,
                    low: false,
                    entityTypes: [],
                    sources: [],
                    tags: [],
                    searchTerm: ''
                }
            },
            flights: {
                routes: [],
                map: null,
                routeLayers: [],
                markedLoaded: false,
                filters: {
                    passenger: '',
                    airport: '',
                    dateRange: { start: null, end: null }
                }
            },
            timeline: {
                events: [],
                currentMonth: null,
                filters: {}
            },
            ui: {
                currentTab: 'entities',
                theme: localStorage.getItem('theme') || 'light'
            }
        };

        this.subscribers = new Map();
    }

    /**
     * Get value from state using dot notation
     * @param {string} path - Path like 'network.data' or 'entities.bios'
     * @returns {*} Value at path
     */
    get(path) {
        const keys = path.split('.');
        return keys.reduce((obj, key) => obj?.[key], this.state);
    }

    /**
     * Set value in state using dot notation
     * @param {string} path - Path like 'network.data'
     * @param {*} value - Value to set
     */
    set(path, value) {
        const keys = path.split('.');
        const lastKey = keys.pop();
        const target = keys.reduce((obj, key) => obj[key], this.state);
        target[lastKey] = value;

        // Notify subscribers
        this.notify(path, value);
    }

    /**
     * Subscribe to state changes
     * @param {string} path - Path to watch
     * @param {Function} callback - Callback when value changes
     */
    subscribe(path, callback) {
        if (!this.subscribers.has(path)) {
            this.subscribers.set(path, []);
        }
        this.subscribers.get(path).push(callback);
    }

    /**
     * Notify all subscribers of a state change
     * @param {string} path - Path that changed
     * @param {*} value - New value
     */
    notify(path, value) {
        const callbacks = this.subscribers.get(path) || [];
        callbacks.forEach(cb => cb(value));
    }

    /**
     * Get the entire state tree (for debugging)
     * @returns {Object} State tree
     */
    getState() {
        return this.state;
    }

    /**
     * Reset a section of state to default
     * @param {string} section - Top-level section (network, entities, etc.)
     */
    reset(section) {
        if (section === 'network') {
            this.state.network = {
                data: null,
                simulation: null,
                svg: null,
                g: null,
                node: null,
                link: null,
                label: null,
                zoom: null,
                selectedNode: null,
                visibleNodes: new Set(),
                connectionSliderValue: 300
            };
        }
        // Add more sections as needed
        this.notify(section, this.state[section]);
    }
}

// Singleton instance
export const appState = new StateManager();

// Backward compatibility - expose to window for gradual migration
window.__appState = appState;
