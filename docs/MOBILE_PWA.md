# Android and PWA guide

## Open directly on a phone in the same network

Run the frontend with `npm run dev -- --host 0.0.0.0`, discover the computer's
LAN address and open `http://COMPUTER_IP:5173` on Android. The firewall must
allow the port. Installation as a PWA normally requires HTTPS, except localhost.

## Publish the offline demonstration

Build from the `frontend` directory:

- build command: `npm ci && npm run build`
- output directory: `dist`
- environment `VITE_API_URL`: leave empty for demo offline

After publishing over HTTPS, open the URL in Chrome and choose **Install app**
or **Add to home screen**. Visit once online so the generated assets and all
three cases enter the offline cache.

## Publish with a backend

Deploy FastAPI over HTTPS and build with:

```bash
VITE_API_URL=https://navalforge-concept-api.onrender.com npm run build
```

Add the PWA HTTPS origin to `CORS_ORIGINS` on the backend.

The current public PWA is <https://navalforgeconcept.pages.dev>. After opening it,
select a case and touch **Executar projeto**. A successful live calculation
changes the status seal from **DEMO OFFLINE** to **BACKEND ONLINE**.

## Remove an old PWA on Android

Long-press the NavalForge icon, open **App info** and choose **Uninstall**. If an
old service worker remains in Chrome, also clear the site's stored data before
reinstalling. The cache name includes the version and 0.1.6 removes earlier
NavalForge caches during activation.

## 3D orientation

The engineering geometry is converted explicitly to Three.js as:

- X: transom to bow;
- Y: vertical upward;
- Z: port to starboard.

The viewer does not rotate the hull to compensate for another axis convention.
ISO, LADO, PROA and TOPO buttons reset the camera to known orientations.
