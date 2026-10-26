# Models, learning and performance work — findings

## Does the project contain trained models?
**No.** The audit found no learned weights, training code or datasets. The pipeline is classical computer vision (SIFT, phase correlation, ECC, RANSAC) plus geometry. The UI says so. The software does not learn from user files and no user data is used for training.

## Learned matchers (not added)
A browser-capable learned matcher (e.g. SuperPoint/LightGlue-class ONNX models) was considered. It was **not added** because the brief requires measurable evidence on held-out data with documented weights/licences, and no legitimately usable Chandrayaan-2 ground-truth pairs were available here. Adding a model without such evidence would be decoration. Future work: assemble licensed, independently registered OHRC/TMC-2/IIRS pairs, hold out a test set, and compare against the existing baseline.

## WebGPU (not used)
The hot spots (SIFT, ECC, warping) live inside OpenCV WASM; there is no WebGPU path for them. Re-implementing them on the GPU would forfeit parity. No benchmark justified it.

## Improvements implemented (engineering, not accuracy claims)
| Item | Evidence |
|---|---|
| Real tile-level progress, stage reporting, cancellation, crash recovery | E2E tests |
| Bounded memory: stream reads, capped grid with explicit warning, size/geometry limits | 3.2 GB E2E, lazy-array tests |
| Reproducibility: RANSAC is deterministic for identical input (fixed internal OpenCV RNG; the recorded seed does not influence it); every parameter recorded (`Engine.config()`) | `test_runs_are_reproducible`, WASM repeat test |
| Method traceability: matcher path per tile, levels attempted, overlap method | Evidence page, manifest |
| Single source of truth for gate thresholds | `test_gate_thresholds_single_source` |
| Corrected `.npy` pixel-offset bug | regression test |
| Honest self-test against a known transform | native + WASM |

## Registration improvements considered but **not** implemented
Coarse-to-fine pyramids with propagated initialisation, ambiguity/repetition rejection beyond the ratio test, adaptive feature budgets, robust model selection (similarity/affine vs. homography) and low-texture handling. Each would change scientific behaviour and must be justified by held-out measurements; none was claimed or changed. The cascade over common GSD levels already provides a multi-resolution search.

## Accuracy claims
None. Nothing in this release claims improved registration accuracy.
