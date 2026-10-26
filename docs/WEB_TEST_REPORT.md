# Test and validation report (platform 3.0.1-web / engine 8.1.0)

Run on the delivered source tree. Raw evidence: `docs/evidence/e2e-results.json`, `docs/evidence/parity-result.json`, screenshots in `docs/evidence/`.

| Suite | Command | Result |
|---|---|---|
| Python: original tests (31) + new engine/security/bridge tests (50), run in the CI-pinned environment (NumPy 2.2.5, SciPy 1.14.1, Shapely 2.0.7, OpenCV 4.11.0) | `python -m pytest -q` | **81 passed** |
| JS unit tests (paths, ingestion, preflight, exporters, ZIP, transform metric, CI-pin sync) — 45 | `npm test` | **45 passed** |
| WASM-vs-native parity — 12 (run with native reference pinned **and** with latest native libraries) | `npm test` | **12 passed** in both |
| Real-browser E2E (Chromium 153) | `npm run test:e2e` | **65 / 65 passed** |
| Type-check + production build | `npm run build` | passes; clean-clone `npm ci && npm run build` verified |
| Original engine self-test | `python -m app.cli.main self-test` | passes (known-transform error ≈ 0.12 px) |

## Scientific correctness (all **synthetic**)
* Geographic-warp registration of two sensors (2 m and 5 m, one rotated 8°, different radiometry) sampled from one analytic surface through PDS4 labels and ISRO-style geometry CSVs: **VALIDATED**, 174 inliers / 201 tentative, RMSE 1.04 px, translation (−0.055, −0.19) px, residual affine ≈ identity. True swath intersection used.
* Non-overlapping footprints ⇒ empty intersection (no fabricated overlap).
* Flat, independent-noise and unrelated-noise pairs ⇒ **INSUFFICIENT_EVIDENCE**.
* Documented limit: an image matched with its own copy passes the gate (gate ≠ ground truth).
* Determinism: identical input ⇒ identical inliers and homography (native and WASM). This comes from OpenCV's fixed internal RANSAC generator; `cv2.setRNGSeed` has no effect on `findHomography` (verified, see `test_ransac_determinism_does_not_depend_on_global_seed`).
* Known-transform self-test: recovered within 0.12 px (native) / 0.13 px (WASM).
* Not exercised: rotation/scale sweeps, noise sweeps, partial-overlap sweeps beyond the above, IIRS spectral cubes in the registration path, repetitive-texture outliers. **Listed as gaps, not claims.**

## Parity (native CPython vs Pyodide, OpenCV 4.11.0)
Transform criterion: worst-case displacement over the common grid < 0.5 px (derivation and the CI failure analysis: `WEB_PARITY_ANALYSIS.md`). Records: `evidence/parity-result-pinned-deps.json`, `evidence/parity-result-latest-deps.json`.

| Quantity | Native, pinned to runtime versions | Native, latest (OpenCV 4.13, NumPy 2.4, SciPy 1.17, Shapely 2.2) | WASM |
|---|---|---|---|
| Tentative matches | 201 | 201 | 201 |
| Inliers | 164 | 174 | 164 |
| Transform displacement vs WASM | 4.0e-5 px | 3.9e-5 px | — |
| Max coefficient delta (affine) | 3.9e-7 | 3.8e-7 | — |
| Raw pixel windows (4 formats, 10 windows) | bit-identical | bit-identical | — |
| Gate outcome, grid, overlap area, metadata | identical | identical | — |

The inlier-count difference with latest OpenCV is a behaviour change in `findHomography`'s returned mask (≥ 4.12 recomputes it after refinement), not a different transform.
**The reported CI failure (affine coefficient delta 0.00213) was not reproducible locally**; see the analysis for what was ruled out and what CI evidence is needed if it recurs.

## Security / privacy (E2E, real Chromium)
Every request same-origin; no non-GET request; no mission names in URLs; zero CSP violations with a policy lacking `unsafe-eval`; no console errors/warnings; traversal, truncated-file, entity-bomb, 3.2 GB file and malformed-size cases handled; opt-in IndexedDB persistence, reload, "clear all" and workspace reset verified.

## Browser behaviour verified
File input and **folder input (webkitdirectory)** ingestion with relative paths; preview; run with live tile progress; cancel → clean restart → new run; Lab canvas renders and responds to keyboard; overlay before/after; five exports plus ZIP (CRC-checked by Python, PNG signature checked); theme persistence; deep-link refresh; routes at 1360/820/390 px with no horizontal overflow; skip link is first Tab stop; visible focus; landmarks; live regions.

## Not verified (honest gaps)
Firefox/Safari/mobile devices; screen-reader behaviour (only landmarks/ARIA presence); drag-and-drop with real folder entries (synthetic events cannot supply `webkitGetAsEntry`; code path implemented but unverified in E2E); `showDirectoryPicker`; real Chandrayaan-2 products; long-running (>minutes) workloads; low-memory devices; actual Vercel deployment.
