# Dependencies and licences (web platform)

Confirm each licence text against upstream before redistribution; this is a good-faith summary.

| Component | Version | Licence | Use |
|---|---|---|---|
| Pyodide (CPython 3.13 → WASM) | 0.29.5 | MPL-2.0 (CPython: PSF) | runtime, vendored in `public/pyodide` |
| NumPy | 2.2.5 | BSD-3-Clause | engine |
| SciPy | 1.14.1 | BSD-3-Clause | engine |
| opencv-python (WASM build) | 4.11.0.86 | Apache-2.0 | engine |
| Shapely (+ GEOS) | 2.0.7 | BSD-3-Clause (GEOS: LGPL-2.1) | engine |
| React / React DOM | 18.3.x | MIT | UI |
| Vite, @vitejs/plugin-react, TypeScript, Vitest | see `package.json` | MIT / Apache-2.0 | build/test |
| @fontsource-variable/inter, /jetbrains-mono | 5.x | OFL-1.1 | self-hosted fonts |
| puppeteer-core, @sparticuz/chromium | see `package.json` | Apache-2.0 / MIT (Chromium: BSD-style + components) | dev-only E2E testing, not shipped |

Wheels in `public/pyodide` are unmodified upstream artefacts (each contains its own licence files); SHA-256 values are in `public/pyodide/VENDOR_MANIFEST.json`. Original project notices remain in `LEGAL/`. The engine's native Python requirements (`requirements.txt`) are unchanged.
