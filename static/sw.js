const CACHE_NAME = "futbol-ai-v2";

self.addEventListener("install", event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache =>
            cache.addAll([
                "/",
                "/static/style.css",
                "/static/app.js",
                "/static/manifest.json"
            ])
        )
    );

    self.skipWaiting();
});

self.addEventListener("activate", event => {
    event.waitUntil(
        caches.keys().then(keys =>
            Promise.all(
                keys
                    .filter(key => key !== CACHE_NAME)
                    .map(key => caches.delete(key))
            )
        )
    );

    self.clients.claim();
});

self.addEventListener("fetch", event => {
    if (event.request.method !== "GET") return;

    const url = new URL(event.request.url);

    if (url.pathname.startsWith("/api/")) return;

    event.respondWith(
        fetch(event.request).catch(() => caches.match(event.request))
    );
});
