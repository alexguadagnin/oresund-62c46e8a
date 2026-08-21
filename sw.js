/* Service worker — mette in cache tutto al primo avvio, poi serve sempre dalla cache.
   Risultato: l'app funziona in aereo, in metropolitana, senza campo. */
const CACHE = "oresund-v2";
const ASSETS = [
  "./", "./index.html", "./manifest.webmanifest",
  "./icon-192.png", "./icon-512.png", "./icon-maskable-512.png", "./apple-touch-icon.png",
  "https://fonts.googleapis.com/css2?family=Familjen+Grotesk:wght@500;600;700&family=Public+Sans:ital,wght@0,400;0,500;0,600;1,400&family=IBM+Plex+Mono:wght@400;500;600&display=swap"
];

self.addEventListener("install", e => {
  e.waitUntil(
    caches.open(CACHE)
      .then(c => Promise.allSettled(ASSETS.map(u => c.add(u))))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys()
      .then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", e => {
  const r = e.request;
  if (r.method !== "GET") return;
  // I link a Google Maps devono uscire sulla rete: non intercettarli.
  if (new URL(r.url).origin === "https://www.google.com") return;
  e.respondWith(
    caches.match(r, { ignoreSearch: true }).then(hit => {
      if (hit) {
        // aggiorna in background, ma intanto serve subito dalla cache
        fetch(r).then(res => res.ok && caches.open(CACHE).then(c => c.put(r, res))).catch(() => {});
        return hit;
      }
      return fetch(r)
        .then(res => {
          if (res.ok) { const cp = res.clone(); caches.open(CACHE).then(c => c.put(r, cp)); }
          return res;
        })
        .catch(() => caches.match("./index.html"));
    })
  );
});
