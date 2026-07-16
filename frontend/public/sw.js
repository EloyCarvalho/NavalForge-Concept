const CACHE = 'navalforge-concept-v0.1.7'
const BUILD = []
const CORE = [
  '/',
  '/manifest.webmanifest',
  '/icons/icon.svg',
  '/icons/icon-192.png',
  '/icons/icon-512.png',
  '/demo/nf-demo-service-7m.project.json',
  '/demo/nf-demo-service-7m.result.json',
  '/demo/nf-demo-patrol-10m.project.json',
  '/demo/nf-demo-patrol-10m.result.json',
  '/demo/nf-demo-rescue-12m.project.json',
  '/demo/nf-demo-rescue-12m.result.json',
  '/demo/reports/nf-demo-service-7m.pdf',
  '/demo/reports/nf-demo-service-7m.docx',
  '/demo/reports/nf-demo-service-7m.xlsx',
  '/demo/reports/nf-demo-service-7m.csv',
  '/demo/reports/nf-demo-service-7m.json',
  '/demo/reports/nf-demo-patrol-10m.pdf',
  '/demo/reports/nf-demo-patrol-10m.docx',
  '/demo/reports/nf-demo-patrol-10m.xlsx',
  '/demo/reports/nf-demo-patrol-10m.csv',
  '/demo/reports/nf-demo-patrol-10m.json',
  '/demo/reports/nf-demo-rescue-12m.pdf',
  '/demo/reports/nf-demo-rescue-12m.docx',
  '/demo/reports/nf-demo-rescue-12m.xlsx',
  '/demo/reports/nf-demo-rescue-12m.csv',
  '/demo/reports/nf-demo-rescue-12m.json',
  '/release.json',
  ...BUILD,
]

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(CORE)).then(() => self.skipWaiting()))
})

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key))))
      .then(() => self.clients.claim()),
  )
})

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return
  const url = new URL(event.request.url)
  if (url.pathname.startsWith('/api/') || url.pathname === '/health') return
  event.respondWith(
    caches.match(event.request).then((cached) => {
      const network = fetch(event.request)
        .then((response) => {
          if (response.ok && url.origin === self.location.origin) {
            const clone = response.clone()
            caches.open(CACHE).then((cache) => cache.put(event.request, clone))
          }
          return response
        })
        .catch(() => cached || caches.match('/'))
      return cached || network
    }),
  )
})
