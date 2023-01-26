// Bump this version number each time a cached or asset changes.
// If you don't, the SW won't be reinstalled and the pages you cache initially won't be updated
// (by default at least, see next sections for more on caching).
const VERSION = '{{ version }}';
const urlsToCache = ["/static/jumboIcon.png", "/offline"];
const cacheName = "pwa-assets-" + VERSION;

self.addEventListener('install', (event) => {
    console.log('[SW] Installing SW version:', VERSION);

    event.waitUntil(async () => {
      const cache = await caches.open(cacheName);
      return cache.addAll(urlsToCache);
   });
});

self.addEventListener("fetch", event => {
   event.respondWith(
     caches.match(event.request)
     .then(cachedResponse => {
	   // It can update the cache to serve updated content on the next request
         return cachedResponse || fetch(event.request);
     }
   )
  )
});