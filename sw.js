// Network first, cache fallback: always the newest cards when online, still opens offline.
const CACHE = 'neuro-flashcards-v2';
const CORE = ['./', './index.html', './day/', './day/index.html', './manifest.webmanifest', './day/manifest.webmanifest',
  './icons/icon-192.png', './icons/icon-day-192.png',
  './img/brainstem-cranial-nerve-nuclei.png', './img/levator-palpebrae-superioris-lateral.jpg',
  './img/levator-palpebrae-superioris-tarsal-plate.jpg', './img/extraocular-muscles.jpg'];
self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(CORE)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  e.respondWith(
    fetch(e.request).then(r => {
      if (r.ok && new URL(e.request.url).origin === location.origin) {
        const copy = r.clone(); caches.open(CACHE).then(c => c.put(e.request, copy));
      }
      return r;
    }).catch(() => caches.match(e.request, {ignoreSearch: true}))
  );
});
