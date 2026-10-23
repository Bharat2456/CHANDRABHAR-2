# Test and validation report (platform 3.0.0-web / engine 8.1.0)

Run on the delivered source tree. Raw evidence: `docs/evidence/e2e-results.json`, `docs/evidence/parity-result.json`, screenshots in `docs/evidence/`.

| Suite | Command | Result |
|---|---|---|
| Python: original tests (31) + new engine/security/bridge tests (49) | `python -m pytest -q` | **80 passed** |
| JS unit tests (paths, ingestion, preflight, exporters, ZIP) — 36 | `npm test` | **36 passed** |
| WASM-vs-native parity — 12 | `npm test` | **12 passed** |
| Real-browser E2E (Chromium 153) | `npm run test:e2e` | **65 / 65 passed** |
| Type-check + production build | `npm run build` | passes; clean-clone `npm ci && npm run build` verified |
| Original engine self-test | `python -m app.cli.main self-test` | passes (known-transform error ≈ 0.12 px) |

## Scientific correctness (all **synthetic**)
* Geographic-warp registration of two sensors (2 m and 5 m, one rotated 8°, different radiometry) sampled from one analytic surface through PDS4 labels and ISRO-style geometry CSVs: **VALIDATED**, 174 inliers / 201 tentative, RMSE 1.04 px, translation (−0.055, −0.19) px, residual affine ≈ identity. True swath intersection used.
* Non-overlapping footprints ⇒ empty intersection (no fabricated overlap).
* Flat, independent-noise and unrelated-noise pairs ⇒ **INSUFFICIENT_EVIDENCE**.
* Documented limit: an image matched with its own copy passes the gate (gate ≠ ground truth).
* Determinism: same seed ⇒ same inliers and homography (native and WASM).
* Known-transform self-test: recovered within 0.12 px (native) / 0.13 px (WASM).
* Not exercised: rotation/scale sweeps, noise sweeps, partial-overlap sweeps beyond the above, IIRS spectral cubes in the registration path, repetitive-texture outliers. **Listed as gaps, not claims.**

## Parity (native CPython, OpenCV 4.13 vs Pyodide, OpenCV 4.11)
| Quantity | Native | WASM |
|---|---|---|
| Tentative matches | 201 | 201 |
| Inliers | 174 | 164 (−5.7 %) |
| Inlier ratio | 0.866 | 0.816 |
| RMSE (px) | 1.038 | 0.893 |
| Homography translation difference | — | < 1e-5 px |
| Raw pixel windows (4 formats, 10 windows) | — | bit-identical |
| Gate outcome, grid, overlap area, product metadata | — | identical |

The inlier count differs because RANSAC consensus sets differ between OpenCV builds; the estimated transform is the same to < 1e-5 px.

## Security / privacy (E2E, real Chromium)
Every request same-origin; no non-GET request; no mission names in URLs; zero CSP violations with a policy lacking `unsafe-eval`; no console errors/warnings; traversal, truncated-file, entity-bomb, 3.2 GB file and malformed-size cases handled; opt-in IndexedDB persistence, reload, "clear all" and workspace reset verified.

## Browser behaviour verified
File input and **folder input (webkitdirectory)** ingestion with relative paths; preview; run with live tile progress; cancel → clean restart → new run; Lab canvas renders and responds to keyboard; overlay before/after; five exports plus ZIP (CRC-checked by Python, PNG signature checked); theme persistence; deep-link refresh; routes at 1360/820/390 px with no horizontal overflow; skip link is first Tab stop; visible focus; landmarks; live regions.

## Not verified (honest gaps)
Firefox/Safari/mobile devices; screen-reader behaviour (only landmarks/ARIA presence); drag-and-drop with real folder entries (synthetic events cannot supply `webkitGetAsEntry`; code path implemented but unverified in E2E); `showDirectoryPicker`; real Chandrayaan-2 products; long-running (>minutes) workloads; low-memory devices; actual Vercel deployment.
