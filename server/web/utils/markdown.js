/**
 * Markdown Utilities
 * Handles markdown loading and rendering
 */

let markedLoaded = false;

/**
 * Load marked.js library dynamically
 * @returns {Promise<void>} Resolves when marked.js is loaded
 */
export async function loadMarkedJS() {
    if (markedLoaded) return;

    return new Promise((resolve, reject) => {
        // Check if already loaded
        if (typeof marked !== 'undefined') {
            markedLoaded = true;
            resolve();
            return;
        }

        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/marked/marked.min.js';
        script.onload = () => {
            markedLoaded = true;
            console.log('✅ Marked.js loaded successfully');
            resolve();
        };
        script.onerror = (error) => {
            console.error('❌ Failed to load marked.js:', error);
            reject(new Error('Failed to load marked.js'));
        };
        document.head.appendChild(script);
    });
}

/**
 * Render markdown text to HTML
 * @param {string} text - Markdown text to render
 * @returns {Promise<string>} HTML output
 */
export async function renderMarkdown(text) {
    if (!text) return '';

    await loadMarkedJS();

    try {
        return marked.parse(text);
    } catch (error) {
        console.error('Error rendering markdown:', error);
        return escapeHtml(text); // Fallback to escaped plain text
    }
}

/**
 * Render markdown synchronously (requires marked.js to be pre-loaded)
 * @param {string} text - Markdown text to render
 * @returns {string} HTML output
 */
export function renderMarkdownSync(text) {
    if (!text) return '';

    if (typeof marked === 'undefined') {
        console.warn('marked.js not loaded, returning plain text');
        return escapeHtml(text);
    }

    try {
        return marked.parse(text);
    } catch (error) {
        console.error('Error rendering markdown:', error);
        return escapeHtml(text);
    }
}

/**
 * Escape HTML for safe rendering
 * @param {string} text - Text to escape
 * @returns {string} HTML-safe text
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Check if marked.js is loaded
 * @returns {boolean} True if loaded
 */
export function isMarkedLoaded() {
    return markedLoaded && typeof marked !== 'undefined';
}

// Backward compatibility - expose to window
if (typeof window !== 'undefined') {
    window.__markdown = {
        loadMarkedJS,
        renderMarkdown,
        renderMarkdownSync,
        isMarkedLoaded
    };
}
