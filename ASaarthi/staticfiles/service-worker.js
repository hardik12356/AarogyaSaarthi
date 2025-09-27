// ====== VERSIONING ======
const CACHE_VERSION = "v1.0.2"; // updated version
const STATIC_CACHE = `static-${CACHE_VERSION}`;
const RUNTIME_CACHE = `runtime-${CACHE_VERSION}`;
const IMAGE_CACHE = `images-${CACHE_VERSION}`;

// ====== STATIC ASSETS (local) ======
const STATIC_ASSETS = [
  "/",                     // homepage
  "/offline.html",         // offline fallback
  "/static/css/style.css",
  "/static/js/script.js",
  "/static/icons/icon-192.png", // added icons here
  "/static/icons/icon-512.png"
];

// ====== CDN RESOURCES ======
const CDN_RESOURCES = [
  "https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css",
  "https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js",
  "https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js",
  "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css",
  "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
];

// ====== API ENDPOINTS ======
const API_ENDPOINTS = ["/api/summary/", "/api/alerts/"];

// ====== INSTALL ======
self.addEventListener("install", event => {
  event.waitUntil(
    Promise.all([
      caches.open(STATIC_CACHE).then(cache => cache.addAll([...STATIC_ASSETS, ...CDN_RESOURCES])),
      caches.open(IMAGE_CACHE).then(cache => cache.addAll(STATIC_ASSETS.filter(path => path.includes('icon'))))
    ])
  );
  self.skipWaiting();
});

// ====== ACTIVATE ======
self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys
          .filter(key => ![STATIC_CACHE, RUNTIME_CACHE, IMAGE_CACHE].includes(key))
          .map(key => caches.delete(key))
      )
    )
  );
  self.clients.claim();
});

// ====== FETCH ======
self.addEventListener("fetch", event => {
  if (event.request.method !== "GET") return;

  const url = new URL(event.request.url);
  const urlPath = url.pathname;

  // ---- Static Assets + CDN (cache-first) ----
  if (STATIC_ASSETS.includes(urlPath) || CDN_RESOURCES.includes(event.request.url)) {
    event.respondWith(
      caches.match(event.request).then(cached => cached || fetch(event.request))
    );
    return;
  }

  // ---- Images / Icons (cache-first with runtime put) ----
  if (event.request.destination === "image" || STATIC_ASSETS.filter(p => p.includes('icon')).includes(urlPath)) {
    event.respondWith(
      caches.open(IMAGE_CACHE).then(cache =>
        cache.match(event.request).then(cachedResponse =>
          cachedResponse ||
          fetch(event.request).then(networkResponse => {
            cache.put(event.request, networkResponse.clone());
            return networkResponse;
          })
        )
      )
    );
    return;
  }

  // ---- API (stale-while-revalidate) ----
  if (API_ENDPOINTS.includes(urlPath)) {
    event.respondWith(
      caches.open(RUNTIME_CACHE).then(cache =>
        cache.match(event.request).then(cachedResponse => {
          const networkFetch = fetch(event.request)
            .then(networkResponse => {
              cache.put(event.request, networkResponse.clone());
              return networkResponse;
            })
            .catch(() => cachedResponse);
          return cachedResponse || networkFetch;
        })
      )
    );
    return;
  }

  // ---- Other Requests (network-first with offline fallback) ----
  event.respondWith(
    fetch(event.request)
      .then(networkResponse =>
        caches.open(RUNTIME_CACHE).then(cache => {
          cache.put(event.request, networkResponse.clone());
          return networkResponse;
        })
      )
      .catch(() => {
        if (event.request.mode === "navigate") {
          return caches.match("/offline.html");
        }
        return caches.match(event.request);
      })
  );
});
