# GitHub → Vercel deployment

The site is a **static Vite build**; Vercel needs no serverless function, database or environment variable.

## Settings (also encoded in `vercel.json`)

| Setting | Value |
|---|---|
| Framework preset | Vite |
| Install command | `npm ci` |
| Build command | `npm run build` (generates the engine bundle, verifies vendored runtime checksums, type-checks, builds) |
| Output directory | `dist` |
| Node.js | 20.x or newer |
| Environment variables | none |
| Root directory | repository root |

## Steps

1. Push this repository to GitHub (`git add -A && git commit && git push`). `public/pyodide/` (≈43 MB, 8 files, largest 16 MB) **is committed**; `public/engine/` is generated at build and git-ignored.
2. In Vercel: *Add New → Project → Import* the GitHub repository. Accept the detected Vite preset (the values above are read from `vercel.json`).
3. Click **Deploy**. The first build takes about a minute.
4. Verify (see below), then optionally attach a custom domain.

CLI alternative: `npm i -g vercel && vercel --prod`.

## Routing

The app uses hash routes (`/#/workspace`), so refresh and deep links need no rewrites and cannot 404.

## Headers (from `vercel.json`)

* `Content-Security-Policy`: `default-src 'self'; script-src 'self' 'wasm-unsafe-eval'; connect-src 'self' blob:; worker-src 'self' blob:; font-src 'self'; img-src 'self' data: blob:; object-src 'none'; frame-ancestors 'none'; …` — **no `unsafe-eval`** (verified: the engine runs with eval disabled), no third-party origin of any kind, so mission data cannot be sent anywhere by page script.
* `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, `X-Frame-Options: DENY`, COOP/CORP `same-origin`, restrictive `Permissions-Policy`. HTTPS/HSTS are provided by Vercel.
* Caching: `/assets/*` immutable 1 year (content-hashed); `/pyodide/*` 1 day + stale-while-revalidate 7 days (pinned, large); `/engine/*` must-revalidate (changes with each build).
* `.wasm` is served as `application/wasm`; Vercel applies Brotli/gzip to text and wasm.

## Reproducibility

* `package-lock.json` pins JS dependencies; `npm ci` is used.
* The runtime is vendored with SHA-256 manifest; `npm run vendor:pyodide` re-creates it from the official GitHub release tarball (checksum pinned in `scripts/vendor-pyodide.mjs`). `scripts/check-assets.mjs` fails the build if any file is missing or altered.
* Python engine is packed from `app/` by `scripts/build-engine-bundle.mjs` (content hash shown in Settings).

## Post-deploy verification checklist

```bash
curl -sI https://<your-app>.vercel.app/ | grep -i -E "content-security-policy|x-content-type|referrer"
curl -sI https://<your-app>.vercel.app/pyodide/pyodide.asm.wasm | grep -i -E "content-type|cache-control"
```
Then open the site → *Mission Overview → Try the synthetic demo → Run registration*; expect "Processing completed" and a passed gate on the synthetic pair. Settings → *Run engine self-test* should pass. In DevTools → Network confirm only same-origin requests.

## Status of deployment in this delivery

**The site was not deployed by the author of this package** (no Vercel/GitHub credentials were available). The production build, the static server that reproduces `vercel.json`, and every check in `WEB_TEST_REPORT.md` were run locally; **no public URL exists yet and none is claimed.** Follow the steps above to obtain it.

## Plan limits to be aware of

Vercel Hobby/Pro limits change over time. The largest static file is ≈16 MB and the deployment ≈45 MB, well below documented per-file limits at time of writing; confirm against current Vercel documentation.

## Licensing caution before going public

A public deployment makes the Python engine source (`/engine/engine-bundle.json`) and the JavaScript **downloadable by every visitor**. The repository's `LICENSE.md` grants no licence to third parties. The copyright holder must decide whether public hosting is intended and, if so, add appropriate terms.
