/* Network first, cache fallback: online, pages and data come fresh from the network;
   offline, the last copy that was loaded is served. */
const CACHE = "jw-v3";
const SHELL = ["./", "index.html", "browse.html", "market.html", "assets/site.css", "assets/site.js",
  "assets/today.js", "assets/browse.js", "assets/market.js", "manifest.webmanifest",
  "icons/icon-192.png", "icons/icon-512.png", "data/history.csv", "data/status.json"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => Promise.allSettled(SHELL.map(u => c.add(u)))));
  self.skipWaiting();
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const req = e.request, url = new URL(req.url);
  if (req.method !== "GET" || url.origin !== location.origin) return;
  e.respondWith((async () => {
    const cache = await caches.open(CACHE);
    try {
      const res = await fetch(req);
      if (res.ok) cache.put(req, res.clone());
      return res;
    } catch (err) {
      const hit = await cache.match(req, { ignoreSearch: true });
      if (!hit) return Response.error();
      if (!url.pathname.includes("/data/")) return hit;
      const h = new Headers(hit.headers); h.set("x-jw-offline", "1");
      return new Response(await hit.blob(), { status: 200, headers: h });
    }
  })());
});
