/* Service worker — l'app funziona in aereo, in metropolitana, senza campo.
 *
 * Strategia: cache-first per la velocità, ma con avviso esplicito quando esce
 * una versione nuova. Non si aggiorna mai di nascosto: mostra una barretta e
 * aspetta che sia l'utente a toccarla.
 */
const CACHE = "oresund-v4";
const ASSETS = [
  "./", "./index.html", "./manifest.webmanifest",
  "./icon-192.png", "./icon-512.png", "./icon-maskable-512.png", "./apple-touch-icon.png",
  "https://fonts.googleapis.com/css2?family=Familjen+Grotesk:wght@500;600;700&family=Public+Sans:ital,wght@0,400;0,500;0,600;1,400&family=IBM+Plex+Mono:wght@400;500;600&display=swap"
];

self.addEventListener("install", e => {
  // Niente skipWaiting qui: il nuovo worker resta in attesa finché non è
  // l'utente a dire di aggiornare. Così la pagina aperta non cambia sotto i piedi.
  e.waitUntil(
    caches.open(CACHE).then(c => Promise.allSettled(ASSETS.map(u => c.add(u))))
  );
});

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys()
      .then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

// La pagina chiede di passare alla versione nuova.
self.addEventListener("message", e => {
  if (e.data && e.data.type === "AGGIORNA") self.skipWaiting();
});

self.addEventListener("fetch", e => {
  const r = e.request;
  if (r.method !== "GET") return;
  let url;
  try { url = new URL(r.url); } catch (_) { return; }
  // I link a Google Maps devono uscire sulla rete: non intercettarli.
  if (url.origin === "https://www.google.com") return;

  e.respondWith(
    caches.match(r, { ignoreSearch: true }).then(hit => {
      if (hit) {
        // Serve subito dalla cache, e intanto rinfresca in silenzio.
        fetch(r).then(res => {
          if (res && res.ok) caches.open(CACHE).then(c => c.put(r, res.clone()));
        }).catch(() => {});
        return hit;
      }
      return fetch(r)
        .then(res => {
          if (res && res.ok) { const cp = res.clone(); caches.open(CACHE).then(c => c.put(r, cp)); }
          return res;
        })
        .catch(() => caches.match("./index.html"));
    })
  );
});
