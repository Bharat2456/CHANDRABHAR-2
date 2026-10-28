# Parity analysis: `estimated homographies agree … < 0.002 in the affine part` (CI failure, 0.00213)

## Summary

| Question | Answer (with evidence) |
|---|---|
| Is the scientific engine inconsistent between native and WebAssembly? | **No.** Same code; on every environment I could build the two matrices agree to **≤ 4×10⁻⁷** per coefficient (**≈ 4×10⁻⁵ px** worst-case displacement). |
| Was the failure reproduced? | **No.** I could not obtain 0.00213 on any local environment (below). The CI log excerpt did not include which coefficient failed or the two matrices, so the exact CI inputs are unknown. |
| What is the most probable cause? | The test asserted a **per-coefficient** limit (0.002) that is tighter than the transform can physically be resolved, so it only passes when two machines produce virtually identical correspondences. On this fixture 0.00213 is **0.42 px** worst-case on a 199×191 px grid, versus the estimator's own sampling uncertainty of **1.1 px (median) / 2.5 px (p95)**. Any CI hardware/library combination whose SIFT output differs at the ~10⁻² px level can exceed it (shown by simulation, below). |
| Fix | Compare transforms by what they *do* (worst-case displacement over the common grid, in px) with a documented 0.5 px limit; make the failure message self-diagnosing; pin the native reference libraries to the versions inside the WASM runtime; add a non-blocking latest-dependencies job and an artifact upload. **No algorithm, gate threshold, UI behaviour or security control was changed.** |

## Evidence

Fixture: synthetic OHRC/TMC-2 pair (`app/synthetic.py`), levels = [1.0], geographic-warp path, common grid 199×191 px, 201 tentative matches.

### 1. Version / hardware matrix vs. the WebAssembly runtime (OpenCV 4.11.0, NumPy 2.2.5)
Probe: `tools/parity_probe.py` (full-precision matrices, points, masks).

| Native environment | max abs Δ affine | max abs Δ translation | inliers | notes |
|---|---|---|---|---|
| OpenCV 4.10 / NumPy 2.5 | 3.9e-7 | 7.5e-6 px | 164 | |
| OpenCV 4.11 / NumPy 2.5 | 3.9e-7 | 7.5e-6 px | 164 | same OpenCV as WASM |
| **Pinned to Pyodide: NumPy 2.2.5, SciPy 1.14.1, Shapely 2.0.7, OpenCV 4.11.0** | 3.9e-7 | 7.4e-6 px | **164** | identical counts to WASM |
| OpenCV 4.12 / NumPy 2.2.6 | 3.8e-7 | 7.2e-6 px | 174 | |
| OpenCV 4.13 / NumPy 2.4 / SciPy 1.17 / Shapely 2.2 | 3.8e-7 | 7.2e-6 px | 174 | |
| 4.13 with all SIMD dispatch disabled | 1.0e-8 | 6.4e-7 px | 174 | |
| 4.11 with all SIMD dispatch disabled | 1.3e-8 | 7.6e-7 px | 164 | |

SIFT keypoints (691/982), tentative matches (201) and correspondence coordinates (≤ 5×10⁻⁴ px) agree everywhere; the host CPU has AVX-512.

### 2. Inlier-count difference (174 vs 164) = OpenCV version behaviour, not nondeterminism
OpenCV ≥ 4.12 returns an inlier mask that equals "reprojection error ≤ 3 px under the final refined H" (verified: 201/201 entries). OpenCV 4.11 (the WASM runtime) returns the pre-refinement RANSAC model's mask (12 more points excluded). The refined matrix is the same to 4×10⁻⁷. Pinning the native reference to 4.11 gives 164 = 164.

### 3. RNG seeding
`cv2.setRNGSeed` has **no effect** on `findHomography(RANSAC)` (5 seeds → one distinct result on OpenCV 4.11 and 4.13). RANSAC is deterministic for identical input because OpenCV uses a fixed internal generator. The engine's recorded `rng_seed` therefore does not influence results; earlier wording ("seeded RANSAC") was inaccurate and has been corrected (UI label, docs, changelog). `tests/test_geo_fixture_pipeline.py::test_ransac_determinism_does_not_depend_on_global_seed` pins this behaviour.

### 4. How sensitive is the matrix to tiny differences in the correspondences?
300 trials per level, Gaussian perturbation of both point sets, `findHomography` as in the engine (identical on OpenCV 4.11 and 4.13):

| σ per coordinate | median max\|ΔA\| | p95 | fraction ≥ 0.002 |
|---|---|---|---|
| 1e-4 px | 6.7e-7 | 1.5e-6 | 0 |
| 5e-4 px | 3.5e-6 | 9.5e-6 | 0 |
| 1e-3 px | 7.7e-6 | 3.1e-4 | 0 |
| 3e-3 px | 2.8e-4 | 1.0e-3 | 0 |
| **1e-2 px** | 5.7e-4 | 2.8e-3 | **0.17** |

So 0.002 is exceeded when the two environments' SIFT output differs by ~10⁻² px (or when one extra/missing match changes the consensus set), well below anything scientifically meaningful but above what a different CPU kernel/library build can occasionally produce. I could not verify that this is what happened on the CI runner; that requires the CI artifact described below.

### 5. What does 0.002 mean physically, and how well can the transform be known?
`tools/parity_estimator_uncertainty.py` (`docs/evidence/parity-estimator-uncertainty.json`):
* a 0.002 error in one affine coefficient = **0.38–0.40 px** worst-case displacement over the 199×191 grid (it would be 2 px on a 1000×1000 grid — the limit was grid-size dependent);
* bootstrap of the engine's own 201 correspondences (500 resamples): displacement **median 1.11 px, p95 2.53 px**; 98.8 % of resamples differ by ≥ 0.002 in some coefficient.

The former assertion therefore demanded agreement ~3× finer than the estimator's resolution; it detected "identical numerics", not "same transform".

## The fix

1. **Test** (`tests-web/engine-parity.test.ts`): replaced the per-coefficient assertion by `maxDisplacement(H_native, H_wasm)` over the common grid corners and centre (`tests-web/transformMetric.ts`, unit-tested) with limit `TRANSFORM_EQUIVALENCE_PX = 0.5`. Strictness relative to the old limit: 0.40 px → 0.5 px on this fixture (+25 %), but now grid-size independent, expressed in the engine's own units, and still < half the estimator's median sampling uncertainty and 5 × tighter than the gate's RMSE ceiling (2.5 px). Real divergences (a different algorithm, a mis-scaled grid, a wrong convention) displace by pixels to tens of pixels and still fail.
   On failure the message now contains: displacement, grid size, every coefficient delta, native/WASM library versions and CPU feature flags, inliers, tentative matches, keypoint counts and both matrices — enough to diagnose from the log without a re-run.
2. **CI reproducibility**: `requirements-ci.txt` pins the native reference libraries to the exact versions inside the WASM runtime; `tests-web/ci-pins.test.ts` fails if the pins drift from `public/pyodide/VENDOR_MANIFEST.json`.
3. **Drift detection without blocking**: a separate `latest-deps` job (`continue-on-error`) runs the same tests against the newest libraries; the failure is visible but does not block.
4. **Artifacts**: `parity-result.json`, E2E results and screenshots are uploaded (`if: always()`).
5. **Node deprecation**: actions moved to Node-24 versions after checking each `action.yml` (`checkout@v6`, `setup-python@v6`, `setup-node@v6`, `upload-artifact@v6` — note `upload-artifact@v5` is still Node 20); the project's Node set to 22.

Unchanged: matching cascade, representations, geowarp, evidence-gate thresholds and logic, security controls, UI behaviour (one help-text correction on the RNG-seed field), deployment configuration.

## If it fails again
Download the `diagnostics` artifact (`parity-result.json`) or read the assertion message. Required to settle the root cause: both matrices, `native_env` (OpenCV/NumPy/SciPy/Shapely versions, CPU feature lines), keypoint and tentative counts, and — if the displacement is large — `python tools/parity_probe.py <fixture>` output from the runner to compare point sets directly.

---

# Addendum (platform 3.0.2): OpenCV 5.0.0 — `latest-deps` parity failure, **reproduced and explained**

CI log (job `latest-deps`): displacement **0.903 px**, inliers 172/164, tentative 206/201, keypoints 696/978 vs 691/982, grid 199×191, native NumPy 2.5.4 / OpenCV 5.0.0 / SciPy 1.18.1 / Shapely 2.2.0 vs WASM NumPy 2.2.5 / OpenCV 4.11.0 / SciPy 1.14.1 / Shapely 2.0.7.

**Reproduced exactly** here (`pip install opencv-python-headless==5.0.0.93` with NumPy 2.5.4, SciPy 1.18.1, Shapely 2.2.0): 696/978 keypoints, 206 matches, 172 inliers, displacement 0.903 px. The result is deterministic, so this is a behaviour change, not noise. Evidence: `docs/evidence/opencv5-parity-analysis.json`.

## Root cause: `cv2.remap` interpolation precision changed in OpenCV 5.0

Bisecting by primitive (same input, three OpenCV versions):

| Primitive | 4.11 | 4.13 | 5.0.0 |
|---|---|---|---|
| SIFT keypoints/descriptors (uint8 input) | identical | identical | identical |
| GaussianBlur, resize (AREA/LINEAR/CUBIC), CLAHE, Sobel | identical | identical | identical (≤ 1e-6 relative) |
| **`cv2.remap`, `INTER_LINEAR`, float32 maps** | **fixed-point** | **fixed-point** (bit-identical to 4.11) | **exact bilinear** |

Versus an exact float64 bilinear reference (`tools/opencv_resampling_analysis.py`, `docs/evidence/opencv-resampling-*.json`):

| | noise image: max / rms error (gray levels) | smooth image: max / rms |
|---|---|---|
| OpenCV 4.11 and 4.13 | 5.37 / 1.06 | 0.187 / 0.057 |
| OpenCV 5.0.0 | **2×10⁻⁵ / 0** | **2×10⁻⁵ / 0** |

OpenCV ≤ 4.13 quantises sampling coordinates to 1/32 px (fixed-point); 5.0.0 computes the exact value. A fitted offset search found **no coordinate-convention shift** (best offset 0, 0 in all versions). The engine's geographic warp (`app/core/geowarp.py`, `cv2.remap(INTER_LINEAR)`) therefore hands SIFT very slightly different pixels, SIFT finds a few different keypoints (696/978 vs 691/982) and matches (206 vs 201), RANSAC fits a different consensus set, and the transform moves by 0.903 px.

## Is the OpenCV 5.0 result wrong? No — and it is not better either

* 0.903 px is **inside the estimator's own sampling uncertainty** (bootstrap of the correspondences: median 1.11 px, p95 2.53 px).
* Against the fixture's **known truth** (identity on the common grid): 4.11/4.13 are 0.60 px off, 5.0 is 0.83 px off. Different realisation of the same estimate; neither is "the truth".
* The evidence gate **passes** under OpenCV 5.0 (172 inliers, ratio 0.835, RMSE 1.00 px).

## Decision

* **The required parity test stays strict (0.5 px, pinned reference).** The shipped WebAssembly runtime is OpenCV 4.11; the engine's results are defined by that build. Raising the tolerance to hide the difference would erase a real, explained behaviour difference.
* **OpenCV ≥ 5.0 is documented as not yet qualified.** Moving the runtime or the pins to OpenCV 5 requires re-running the parity suite, re-deriving the tolerance and a decision that the new resampling is acceptable scientifically. Pyodide itself currently ships OpenCV 4.11.0.
* `latest-deps` stays informational: it reports the drift as a warning annotation, a run summary and the `diagnostics-latest-deps` artifact (`parity-result.json` + `latest-deps-probe.json`), without failing the job or the commit.
* A canary test (`tests/test_opencv_resampling_canary.py`) fails only if OpenCV's sub-pixel convention changes to something other than the two known behaviours (a half-pixel offset would misregister every product). The parity records now include `opencv_remap_mode`.
* No engine algorithm, threshold or gate logic was changed.

**This also explains the earlier "0.00213" failure (3.0.1).** Under OpenCV 5.0.0 the per-coefficient deltas against the WebAssembly runtime are `H[0][0]` +0.00134, **`H[0][1]` −0.00213024**, `H[1][0]` −0.00075, `H[1][1]` +0.00540, translation (+0.230, −0.127) px (`docs/evidence/parity-result-opencv5.json`). The CI value then reported, 0.002130152…, equals `|H[0][1]|` to four significant digits. At the time no OpenCV 5 environment was available for reproduction, so the cause was attributed to environment-dependent numerics in general; with OpenCV 5.0.0 reproduced, `cv2.remap` precision is the identified cause. (The 3.0.1 coefficient-based assertion was replaced by the displacement metric; the displacement here, 0.903 px, still exceeds the 0.5 px limit, which is why the informational job still reports it.)
