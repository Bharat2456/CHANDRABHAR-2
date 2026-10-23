<p align="center"><img src="branding/logo_transparent.png" width="200" alt="CHANDRABHAR-2 logo"></p>

<h1 align="center">CHANDRABHAR-2</h1>
<p align="center"><b>Multi-modal, illumination-aware and scale-aware image correspondence for Chandrayaan-2 OHRC, TMC-2 and IIRS imagery</b></p>
<p align="center">Browser-native · files never leave your device · Engine v8.1.0 · Platform v3.0.0-web · Independent research prototype, not an official ISRO product</p>

---

## What it is

A web workspace that registers Chandrayaan-2 products against each other **entirely in your browser**. The project's own Python engine (PDS4/ENVI/NumPy/raw adapters → true swath intersection → common physical GSD grid → illumination-aware representations → SIFT → phase-correlation → ECC cascade → RANSAC → explicit evidence gate) is compiled to WebAssembly with Pyodide and runs in a Web Worker. There is no server, login, database, telemetry or external AI service.

> **Scientific honesty.** The evidence gate tests internal geometric consistency. Passing it is **not** independent ground-truth validation, which this project has not established. All built-in demos and tests use *synthetic* data.

## Use it

Open the deployed site (see *Deploy*), then **Mission Overview → Try the synthetic demo**, or **Data Workspace → select your products**. Guide: [`docs/WEB_USER_GUIDE.md`](docs/WEB_USER_GUIDE.md).

## Develop

```bash
npm ci
npm run dev            # http://localhost:5173  (generates the engine bundle first)
npm run build          # production build into dist/
npm run preview        # serve dist/ locally
npm test               # unit tests + WebAssembly-vs-native parity (needs python3 with numpy/opencv/scipy/shapely)
npm run test:e2e       # real headless Chromium against the production build (run `npm run build` first)
python -m pytest -q    # scientific engine, adapters, security, bridge (79+ tests)
npm run vendor:pyodide # re-create public/pyodide from the pinned official release
```
Node ≥ 20 and Python ≥ 3.10 with `requirements.txt` for the native reference tests. The local Streamlit UI (`dashboard.py`, `run.py`) still works as before.

## Deploy (GitHub → Vercel)

Push to GitHub → *Import project* in Vercel → keep the detected **Vite** preset (`npm ci`, `npm run build`, output `dist`) → Deploy. Full steps, headers and verification: [`docs/WEB_DEPLOYMENT.md`](docs/WEB_DEPLOYMENT.md). **No deployment has been performed by the author of this package, so no public URL is claimed.**

## Documentation

| Topic | File |
|---|---|
| Architecture, diagrams, memory model | [`docs/WEB_ARCHITECTURE.md`](docs/WEB_ARCHITECTURE.md) |
| Python→WASM migration matrix and parity | [`docs/WEB_MIGRATION_PARITY.md`](docs/WEB_MIGRATION_PARITY.md) |
| Privacy & security | [`docs/WEB_PRIVACY_AND_SECURITY.md`](docs/WEB_PRIVACY_AND_SECURITY.md) |
| Formats & companion files | [`docs/WEB_FORMATS.md`](docs/WEB_FORMATS.md) |
| Browser compatibility | [`docs/WEB_BROWSER_COMPATIBILITY.md`](docs/WEB_BROWSER_COMPATIBILITY.md) |
| Performance & limits | [`docs/WEB_PERFORMANCE.md`](docs/WEB_PERFORMANCE.md) |
| Test & validation report | [`docs/WEB_TEST_REPORT.md`](docs/WEB_TEST_REPORT.md) |
| Models & improvements findings | [`docs/WEB_ML_AND_IMPROVEMENTS.md`](docs/WEB_ML_AND_IMPROVEMENTS.md) |
| Known limitations | [`docs/KNOWN_LIMITATIONS.md`](docs/KNOWN_LIMITATIONS.md) |
| Dependencies & licences | [`docs/DEPENDENCIES.md`](docs/DEPENDENCIES.md) |
| Original docs (science, protocol, claims) | [`docs/01_…18_*.md`](docs/), [`docs/LEGACY_README.md`](docs/LEGACY_README.md) |
| Changelog | [`CHANGELOG.md`](CHANGELOG.md) |

The original scientific documentation, experiment protocol, claims matrix, `SIH/` materials and `LEGAL/` notices are preserved unchanged.

## Licence

Proprietary — see [`LICENSE.md`](LICENSE.md) and `LEGAL/`. **Note:** publishing the web build makes the engine source downloadable by visitors; the copyright holder must confirm this is intended before deploying.
