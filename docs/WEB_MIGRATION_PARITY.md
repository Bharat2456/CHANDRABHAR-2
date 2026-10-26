# Scientific-engine migration matrix and parity report

Strategy: **no algorithm was re-implemented**. Each Python module runs unchanged in WebAssembly. Classification below uses the categories from the brief; "Portable" = runs as-is in Pyodide.

| Python module / algorithm | Class | Browser implementation | Known differences | Tests | Status |
|---|---|---|---|---|---|
| `adapters/pds4.py` – label parsing, dtype, axes, offset, size check, GSD, solar geometry, geometry-CSV discovery | Portable (hardened) | Same code; companion lookup confined to workspace root; DTD refused | Search never leaves workspace | `test_security_and_adapters.py`, parity (metadata equality) | **Validated (synthetic PDS4)** |
| `adapters/envi.py` | Portable (hardened) | Same | size check added | adapters tests, parity (BIL big-endian pixels bit-exact) | **Validated** |
| `adapters/numpy_adapter.py` | Portable — **bug fixed** | Header-aware offset | Original shifted pixels by header length | regression test + parity | **Validated** |
| `adapters/raw_sidecar.py` | Portable (hardened) | Same | size check added | adapters tests, parity (BIP exact) | **Validated** |
| `io/lazy_array.py`, `io/reader.py` | Portable (new backend) | `stream` backend; JS 64-bit slice reads in wasm | memmap unavailable on WORKERFS | `test_lazy_array.py` (memmap≡stream across 4 layouts × 5 dtypes), parity, 3.2 GB E2E | **Validated** |
| `geo/mapper.py` – SciPy `LinearNDInterpolator`, Shapely footprint/intersection | Portable (WASM wheels) | Same | none observed | geo fixture tests, parity (area equal to 1e-6 km²) | **Validated (synthetic geometry)** |
| `core/geowarp.py` – common lunar grid, tile warping, polygon mask | Portable | Same | none observed | fixture pipeline, parity (grid identical) | **Validated** |
| `core/physical.py` – GSD planning | Portable | Same | — | existing tests | Validated |
| `core/representations.py` – sensor/illumination-aware normalisation | Portable | Same | — | existing tests, fixture run | Validated |
| `core/matcher.py` – SIFT → phase → ECC, RANSAC (`cv2.findHomography`), coverage, RMSE | Portable (OpenCV 4.11 WASM) | Same; inlier mask retained (note: OpenCV ≥ 4.12 recomputes the mask after refinement, 4.11 does not — see analysis) | Native dev env used OpenCV 4.13 | parity tolerances below | **Validated within tolerance** |
| `core/pipeline.py` – cascade, tiling, best-level selection | Portable (+hooks) | Same; progress/capture hooks | hooks are observers only | fixture + hooks tests | Validated |
| `core/evidence.py` – gate | Portable | Same thresholds, now exported constants | none | gate tests, parity (identical outcome) | Validated |
| `selftest.py` | Portable | Same | now checks known transform | native + WASM | Validated |
| `cli/`, `ui/`, `dashboard.py` (Streamlit) | Not needed in browser | Replaced by React UI | UI only | legacy tests retained | Retained for local use |

No component was found **Not feasible**. Not ported: GPU acceleration and learned models (no evidence they help; see `WEB_ML_AND_IMPROVEMENTS.md`).

## Parity results

Test: `tests-web/engine-parity.test.ts` — identical synthetic fixtures through native CPython and Pyodide-in-Node.

| Quantity | Requirement |
|---|---|
| Metadata of all 5 products | exactly equal |
| Raw pixel windows (PDS4 u2, ENVI BIL i2 big-endian, NPY f4, raw BIP f4) | **bit-identical (SHA-256)** |
| Geometry intersection | status equal; area equal to 6 decimals |
| Common grid (H, W, GSD) | identical |
| Evidence-gate outcome | identical |
| Inliers / tentative matches | within 15 % |
| RMSE / coverage | within 0.25 px / 0.1 |
| Homography | worst-case displacement over the common grid < 0.5 px (was: per-coefficient 0.002; see `WEB_PARITY_ANALYSIS.md`) |
| Self-test known-transform error | both < 1.5 px, difference < 0.3 px |
| Reproducibility | repeat run on identical input ⇒ identical homography (WASM) |

Measured values are in `WEB_TEST_REPORT.md`. Differences stem from different OpenCV minor versions (native 4.13 vs WASM 4.11) and floating-point/SIMD paths, not from different algorithms.

## What parity does **not** show

Parity proves the WASM engine reproduces the native engine. It does not validate either against real Chandrayaan-2 ground truth. See `KNOWN_LIMITATIONS`.
