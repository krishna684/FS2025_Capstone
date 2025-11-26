// Service Worker for AGBOT - Offline Support
const CACHE_VERSION = 'agbot-v1';
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const API_CACHE = `${CACHE_VERSION}-api`;

// Static assets to cache on install
const STATIC_ASSETS = [
    '/',
    '/static/css/style.css',
    '/static/js/main.js',
    '/static/js/offline.js',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
    console.log('[Service Worker] Installing...');
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then((cache) => {
                console.log('[Service Worker] Caching static assets');
                return cache.addAll(STATIC_ASSETS);
            })
            .then(() => self.skipWaiting())
            .catch((error) => {
                console.error('[Service Worker] Failed to cache static assets:', error);
            })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('[Service Worker] Activating...');
    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames
                        .filter((cacheName) => {
                            return cacheName.startsWith('agbot-') && 
                                   cacheName !== STATIC_CACHE && 
                                   cacheName !== API_CACHE;
                        })
                        .map((cacheName) => {
                            console.log('[Service Worker] Deleting old cache:', cacheName);
                            return caches.delete(cacheName);
                        })
                );
            })
            .then(() => self.clients.claim())
    );
});

// Fetch event - implement caching strategies
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }

    // Network-first strategy for analysis endpoint
    if (url.pathname.includes('/analyze') || url.pathname.includes('/api/scan')) {
        event.respondWith(networkFirstStrategy(request));
        return;
    }

    // Cache-first strategy for history and static content
    if (url.pathname.includes('/api/history') || 
        url.pathname.includes('/static/') ||
        url.pathname.includes('cdnjs.cloudflare.com')) {
        event.respondWith(cacheFirstStrategy(request));
        return;
    }

    // Network-first for other API calls
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(networkFirstStrategy(request));
        return;
    }

    // Cache-first for everything else (HTML pages, etc.)
    event.respondWith(cacheFirstStrategy(request));
});

// Network-first strategy: Try network, fall back to cache
async function networkFirstStrategy(request) {
    try {
        const response = await fetch(request);
        
        // Cache successful responses
        if (response && response.status === 200) {
            const cache = await caches.open(API_CACHE);
            cache.put(request, response.clone());
        }
        
        return response;
    } catch (error) {
        console.log('[Service Worker] Network request failed, trying cache:', request.url);
        const cachedResponse = await caches.match(request);
        
        if (cachedResponse) {
            return cachedResponse;
        }
        
        // Return offline page or error response
        return new Response(
            JSON.stringify({ 
                error: 'Network unavailable', 
                offline: true,
                message: 'Please check your internet connection and try again.'
            }),
            {
                status: 503,
                headers: { 'Content-Type': 'application/json' }
            }
        );
    }
}

// Cache-first strategy: Try cache, fall back to network
async function cacheFirstStrategy(request) {
    const cachedResponse = await caches.match(request);
    
    if (cachedResponse) {
        // Update cache in background
        fetch(request).then((response) => {
            if (response && response.status === 200) {
                caches.open(STATIC_CACHE).then((cache) => {
                    cache.put(request, response);
                });
            }
        }).catch(() => {
            // Ignore network errors in background update
        });
        
        return cachedResponse;
    }
    
    try {
        const response = await fetch(request);
        
        if (response && response.status === 200) {
            const cache = await caches.open(STATIC_CACHE);
            cache.put(request, response.clone());
        }
        
        return response;
    } catch (error) {
        console.error('[Service Worker] Failed to fetch:', request.url, error);
        
        // Return a basic offline response
        return new Response('Offline - Content not available', {
            status: 503,
            statusText: 'Service Unavailable'
        });
    }
}

// Handle messages from clients
self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
    
    if (event.data && event.data.type === 'CLEAR_CACHE') {
        event.waitUntil(
            caches.keys().then((cacheNames) => {
                return Promise.all(
                    cacheNames.map((cacheName) => caches.delete(cacheName))
                );
            })
        );
    }
});
