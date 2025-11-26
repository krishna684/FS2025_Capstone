// Offline support and Service Worker registration

// Register Service Worker
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/sw.js')
            .then((registration) => {
                console.log('[App] Service Worker registered:', registration.scope);
                
                // Check for updates
                registration.addEventListener('updatefound', () => {
                    const newWorker = registration.installing;
                    console.log('[App] Service Worker update found');
                    
                    newWorker.addEventListener('statechange', () => {
                        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                            // New service worker available
                            showUpdateNotification();
                        }
                    });
                });
            })
            .catch((error) => {
                console.error('[App] Service Worker registration failed:', error);
            });
    });
}

// Show update notification
function showUpdateNotification() {
    if (typeof showToast === 'function') {
        showToast('A new version is available. Refresh to update.', 'info');
    }
}

// Monitor online/offline status
window.addEventListener('online', async () => {
    console.log('[App] Back online');
    if (typeof showToast === 'function') {
        showToast('Connection restored', 'success');
    }
    
    // Trigger queued image uploads
    if (typeof processQueuedImages === 'function') {
        try {
            const result = await processQueuedImages();
            console.log('[App] Queue processing result:', result);
        } catch (error) {
            console.error('[App] Failed to process queue:', error);
        }
    }
    
    // Retry failed requests
    if (typeof retryFailedRequests === 'function') {
        retryFailedRequests();
    }
});

window.addEventListener('offline', () => {
    console.log('[App] Gone offline');
    if (typeof showToast === 'function') {
        showToast('You are offline. Some features may be limited.', 'warning');
    }
});

// Check if currently online
function isOnline() {
    return navigator.onLine;
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { isOnline };
}
