import { readdirSync, readFileSync, writeFileSync } from 'node:fs'
import { extname, join } from 'node:path'

const dist = new URL('../dist/', import.meta.url)
const assetsDirectory = new URL('./assets/', dist)
const assets = readdirSync(assetsDirectory)
  .filter((name) => ['.js', '.css'].includes(extname(name)))
  .map((name) => `/assets/${name}`)
  .sort()
const serviceWorkerPath = join(dist.pathname, 'sw.js')
const source = readFileSync(serviceWorkerPath, 'utf8')
const replacement = `const BUILD = ${JSON.stringify(assets, null, 2)}`
if (!source.includes('const BUILD = []')) {
  throw new Error('Service-worker build placeholder not found')
}
writeFileSync(serviceWorkerPath, source.replace('const BUILD = []', replacement))
console.log(`Injected ${assets.length} production assets into the offline cache manifest`)
