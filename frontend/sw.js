// Service Worker — Anexo Risk 2.x
// Cache-first for app shell, stale-while-revalidate for API

const CACHE_NAME = "anexo-risk-v3";
const APP_SHELL = [
  "./",
  "./index.html",
  "./manifest.json",
  "./assets/logo/anexo-icon.png",
  "./css/variables.css",
  "./css/style.css",
  "./js/spa.js",
  "./js/shared/config.js",
  "./js/sections/mapa.js",
  "./js/sections/alertas.js",
  "./js/sections/ayudas.js",
  "./js/sections/dashboard.js",
  "./js/sections/decision-center.js",
  "./js/sections/risk-card.js",
  "./js/sections/timeline.js",
  "./js/sections/freshness.js",
  "./js/core/normalization/index.js",
  "./js/core/normalization/domain.js",
  "./js/core/normalization/sources.js",
];

const API_CACHE = "anexo-api-v1";
const API_CACHE_TTL = 120000; // 2 min for local API

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.filter((k) => k !== CACHE_NAME && k !== API_CACHE).map((k) => caches.delete(k))
      )
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") return;

  const url = new URL(request.url);

  // Local API — stale-while-revalidate
  if (url.origin === location.origin && url.pathname.startsWith("/api/")) {
    event.respondWith(
      caches.open(API_CACHE).then(async (cache) => {
        const cached = await cache.match(request);
        const fetchPromise = fetch(request).then((response) => {
          if (response.ok) cache.put(request, response.clone());
          return response;
        }).catch(() => cached);
        return cached || fetchPromise;
      })
    );
    return;
  }

  // App shell — cache first
  if (url.origin === location.origin) {
    event.respondWith(
      caches.match(request).then((cached) => {
        if (cached) return cached;
        return fetch(request).then((response) => {
          if (response.ok) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
          }
          return response;
        }).catch(() => caches.match("./index.html"));
      })
    );
    return;
  }

  // External APIs (GDACS, FIRMS, Open-Meteo, GeoRisk, Leaflet CDN) — cache with fallback
  if (url.host.includes("firms.modaps.eosdis.nasa.gov") ||
      url.host.includes("open-meteo.com") ||
      url.host.includes("gdacs.org") ||
      url.host.includes("localhost:8000") ||
      url.host.includes("unpkg.com")) {
    event.respondWith(
      caches.match(request).then((cached) => {
        return fetch(request).then((response) => {
          if (response.ok) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
          }
          return response;
        }).catch(() => cached);
      })
    );
  }
});
