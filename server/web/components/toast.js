/**
 * Toast Notification Component
 * Simple toast notification system
 */

export class Toast {
    /**
     * Show a toast notification
     * @param {string} message - Message to display
     * @param {string} type - Type of toast ('info', 'success', 'error', 'warning')
     * @param {number} duration - Duration in milliseconds
     */
    static show(message, type = 'info', duration = 3000) {
        const toast = document.getElementById('toast');
        if (!toast) {
            console.warn('Toast element not found in DOM');
            return;
        }

        toast.textContent = message;
        toast.className = `toast show ${type}`;

        // Auto-hide after duration
        setTimeout(() => {
            toast.classList.remove('show');
        }, duration);
    }

    /**
     * Show success toast
     * @param {string} message - Success message
     * @param {number} duration - Duration in milliseconds
     */
    static success(message, duration = 3000) {
        Toast.show(message, 'success', duration);
    }

    /**
     * Show error toast
     * @param {string} message - Error message
     * @param {number} duration - Duration in milliseconds
     */
    static error(message, duration = 4000) {
        Toast.show(message, 'error', duration);
    }

    /**
     * Show warning toast
     * @param {string} message - Warning message
     * @param {number} duration - Duration in milliseconds
     */
    static warning(message, duration = 3500) {
        Toast.show(message, 'warning', duration);
    }

    /**
     * Show info toast
     * @param {string} message - Info message
     * @param {number} duration - Duration in milliseconds
     */
    static info(message, duration = 3000) {
        Toast.show(message, 'info', duration);
    }

    /**
     * Hide any currently visible toast
     */
    static hide() {
        const toast = document.getElementById('toast');
        if (toast) {
            toast.classList.remove('show');
        }
    }
}

// Backward compatibility - expose to window
if (typeof window !== 'undefined') {
    window.showToast = Toast.show;
    window.__Toast = Toast;
}

export default Toast;
