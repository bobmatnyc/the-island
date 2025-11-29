/**
 * Formatter Utilities
 * Centralized text and data formatting functions
 */

/**
 * Format entity name from "Lastname, Firstname" to "Firstname Lastname"
 * @param {string} name - Entity name to format
 * @returns {string} Formatted name
 */
export function formatEntityName(name) {
    if (!name) return '';

    // Already in "Firstname Lastname" format
    if (!name.includes(',')) {
        return name.trim();
    }

    // Convert "Lastname, Firstname" to "Firstname Lastname"
    const parts = name.split(',').map(p => p.trim());
    if (parts.length === 2) {
        return `${parts[1]} ${parts[0]}`;
    }

    return name.trim();
}

/**
 * Escape HTML special characters
 * @param {string} text - Text to escape
 * @returns {string} HTML-safe text
 */
export function escapeHtml(text) {
    if (!text) return '';

    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Escape text for JavaScript string literals
 * @param {string} str - String to escape
 * @returns {string} JS-safe string
 */
export function escapeForJS(str) {
    if (!str) return '';

    return str
        .replace(/\\/g, '\\\\')
        .replace(/'/g, "\\'")
        .replace(/"/g, '\\"')
        .replace(/\n/g, '\\n')
        .replace(/\r/g, '\\r')
        .replace(/\t/g, '\\t');
}

/**
 * Format date to readable string
 * @param {string|Date} date - Date to format
 * @param {string} format - Format type ('short', 'long', 'iso')
 * @returns {string} Formatted date
 */
export function formatDate(date, format = 'short') {
    if (!date) return '';

    const d = typeof date === 'string' ? new Date(date) : date;

    if (isNaN(d.getTime())) return '';

    switch (format) {
        case 'short':
            return d.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            });
        case 'long':
            return d.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });
        case 'iso':
            return d.toISOString().split('T')[0];
        default:
            return d.toLocaleDateString();
    }
}

/**
 * Format number with thousands separators
 * @param {number} num - Number to format
 * @returns {string} Formatted number
 */
export function formatNumber(num) {
    if (num === null || num === undefined) return '';
    return num.toLocaleString('en-US');
}

/**
 * Truncate text with ellipsis
 * @param {string} text - Text to truncate
 * @param {number} maxLength - Maximum length
 * @returns {string} Truncated text
 */
export function truncate(text, maxLength = 100) {
    if (!text || text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

/**
 * Capitalize first letter of each word
 * @param {string} text - Text to capitalize
 * @returns {string} Capitalized text
 */
export function capitalize(text) {
    if (!text) return '';
    return text
        .toLowerCase()
        .split(' ')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

/**
 * Format file size in human-readable format
 * @param {number} bytes - Size in bytes
 * @returns {string} Formatted size
 */
export function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Backward compatibility - expose to window
if (typeof window !== 'undefined') {
    window.__formatter = {
        formatEntityName,
        escapeHtml,
        escapeForJS,
        formatDate,
        formatNumber,
        truncate,
        capitalize,
        formatFileSize
    };
}
