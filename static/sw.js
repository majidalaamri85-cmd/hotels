// Service Worker for offline support and performance optimization
const CACHE_VERSION = 'v1.0.0';
const CACHE_NAME = `hotels-cache-${CACHE_VERSION}`;
const RUNTIME_CACHE = `hotels-runtime-${CACHE_VERSION}`;

// Assets to cache during install
const ASSETS_TO_CACHE = [
  '/',
  '/static/css/main.css',
  '/static/images/ministry-logo.png',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.rtl.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js',
  'https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap'
];

// Install event - cache essential assets
self.addEventListener('install', event => {
  console.log('[Service Worker] Installing...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('[Service Worker] Caching assets');
        return cache.addAll(ASSETS_TO_CACHE);
      })
      .then(() => self.skipWaiting())
      .catch(err => console.error('[Service Worker] Install failed:', err))
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  console.log('[Service Worker] Activating...');
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME && cacheName !== RUNTIME_CACHE) {
            console.log('[Service Worker] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch event - implement network-first strategy
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Skip chrome extensions
  if (url.protocol === 'chrome-extension:') {
    return;
  }

  // Cache-first strategy for static assets
  if (request.url.includes('/static/') || 
      request.url.includes('cdn.jsdelivr.net') ||
      request.url.includes('fonts.googleapis.com')) {
    event.respondWith(
      caches.match(request)
        .then(response => response || fetch(request)
          .then(response => {
            if (!response || response.status !== 200) {
              return response;
            }
            const responseToCache = response.clone();
            caches.open(CACHE_NAME)
              .then(cache => cache.put(request, responseToCache));
            return response;
          })
          .catch(() => {
            // Return a fallback for failed static assets
            if (request.destination === 'image') {
              return caches.match('/static/images/ministry-logo.png');
            }
            return new Response('Offline - Resource unavailable');
          })
        )
    );
    return;
  }

  // Network-first strategy for HTML and API requests
  event.respondWith(
    fetch(request)
      .then(response => {
        if (!response || response.status !== 200) {
          return response;
        }
        const responseToCache = response.clone();
        caches.open(RUNTIME_CACHE)
          .then(cache => cache.put(request, responseToCache));
        return response;
      })
      .catch(() => {
        return caches.match(request)
          .then(response => response || new Response('Offline - Page unavailable', {
            status: 503,
            statusText: 'Service Unavailable',
            headers: new Headers({
              'Content-Type': 'text/plain'
            })
          }));
      })
  );
});

// Handle background sync for form submissions (when back online)
self.addEventListener('sync', event => {
  if (event.tag === 'sync-forms') {
    event.waitUntil(
      // Retry pending form submissions
      self.clients.matchAll().then(clients => {
        clients.forEach(client => {
          client.postMessage({
            type: 'SYNC_FORMS',
            message: 'Connection restored, retrying forms'
          });
        });
      })
    );
  }
});
