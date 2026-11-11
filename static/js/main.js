/**
 * KriptoApp - Main JavaScript
 * Handles webcam, AJAX, file preview, and UI interactions
 */

document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) {
                bsAlert.close();
            }
        }, 5000);
    });

    // Highlight active nav link
    highlightActiveNav();

    // Add animation delays to cards
    animateCards();
});

/**
 * Highlight the active navigation link based on current URL
 */
function highlightActiveNav() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');

    navLinks.forEach(function(link) {
        const href = link.getAttribute('href');
        if (href && currentPath.startsWith(href) && href !== '/') {
            link.classList.add('active');
            link.style.color = '#00ff41';
        } else if (href === '/' && currentPath === '/') {
            link.classList.add('active');
            link.style.color = '#00ff41';
        }
    });
}

/**
 * Add staggered animation to cards
 */
function animateCards() {
    const cards = document.querySelectorAll('.feature-card');
    cards.forEach(function(card, index) {
        card.style.animationDelay = (index * 0.1) + 's';
    });
}

/**
 * Format file size to human-readable format
 * @param {number} bytes - File size in bytes
 * @returns {string} Formatted file size
 */
function formatFileSize(bytes) {
    if (bytes >= 1048576) {
        return (bytes / 1048576).toFixed(1) + ' MB';
    } else if (bytes >= 1024) {
        return (bytes / 1024).toFixed(1) + ' KB';
    }
    return bytes + ' bytes';
}

/**
 * Copy text to clipboard with visual feedback
 * @param {string} text - Text to copy
 * @param {HTMLElement} button - Button element for feedback
 */
function copyToClipboard(text, button) {
    navigator.clipboard.writeText(text).then(function() {
        const originalText = button.innerHTML;
        button.innerHTML = '<i class="bi bi-check2 me-1"></i>Disalin!';
        button.classList.add('btn-success');
        setTimeout(function() {
            button.innerHTML = originalText;
            button.classList.remove('btn-success');
        }, 2000);
    }).catch(function(err) {
        console.error('Failed to copy:', err);
    });
}

/**
 * Show a confirmation dialog before destructive actions
 * @param {string} message - Confirmation message
 * @returns {boolean} User's choice
 */
function confirmAction(message) {
    return confirm(message || 'Apakah Anda yakin?');
}

/**
 * Display a loading spinner on a button
 * @param {HTMLElement} button - Button element
 * @param {string} loadingText - Text to display while loading
 */
function setButtonLoading(button, loadingText) {
    button.disabled = true;
    button.dataset.originalText = button.innerHTML;
    button.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> ' + (loadingText || 'Loading...');
}

/**
 * Restore button from loading state
 * @param {HTMLElement} button - Button element
 */
function resetButton(button) {
    button.disabled = false;
    if (button.dataset.originalText) {
        button.innerHTML = button.dataset.originalText;
    }
}

/**
 * Show a toast notification
 * @param {string} message - Notification message
 * @param {string} type - Alert type (success, danger, warning, info)
 */
function showNotification(message, type) {
    type = type || 'info';
    const container = document.querySelector('.container-fluid');
    const alert = document.createElement('div');
    alert.className = 'alert alert-' + type + ' alert-dismissible fade show cyber-alert mt-2';
    alert.setAttribute('role', 'alert');

    let icon = 'info-circle-fill';
    if (type === 'success') icon = 'check-circle-fill';
    else if (type === 'danger') icon = 'exclamation-triangle-fill';
    else if (type === 'warning') icon = 'exclamation-circle-fill';

    alert.innerHTML = '<i class="bi bi-' + icon + ' me-2"></i>' + message +
        '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>';

    container.insertBefore(alert, container.firstChild);

    setTimeout(function() {
        const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
        if (bsAlert) bsAlert.close();
    }, 5000);
}
