# CHANDRABHAR-2 — Software Requirements Specification

## 1. Functional requirements

| ID | Requirement | Status |
|---|---|---|
| FR-1 | Discover Chandrayaan-2 OHRC/TMC-2/IIRS products in a local folder and extract metadata | Implemented (`app/adapters`) |
| FR-2 | Parse ISRO GRD Scan/Pixel↔Lat/Lon geometry tables and compute true swath footprint intersection | Implemented (`app/geo/mapper.py`) |
| FR-3 | Plan a common physical GSD cascade for a sensor pair | Implemented (`app/core/physical.py`) |
| FR-4 | Warp both products onto a shared geographic grid at the chosen GSD | Implemented (`app/core/geowarp.py`) |
| FR-5 | Produce an illumination-aware representation of each product | Implemented (`app/core/representation.py`) |
| FR-6 | Search for correspondences via a multi-method matcher cascade | Implemented (`app/core/matcher.py`) |
| FR-7 | Verify correspondences geometrically (RANSAC) and separate inliers/outliers | Implemented |
| FR-8 | Gate the result against fixed evidence thresholds before reporting `VALIDATED` | Implemented (`app/core/evidence.py`) |
| FR-9 | Report `INSUFFICIENT_EVIDENCE` with specific failure reasons, never silently upgraded | Implemented |
| FR-10 | Provide a CLI for inspect / inventory / geometry-audit / mission / register / self-test | Implemented (`app/cli/main.py`) |
| FR-11 | Provide a dashboard with Mission Overview / Correspondence Lab / Evidence & Metrics / Products & Export | Implemented (`dashboard.py`) |
| FR-12 | Persist and reflect workflow/run state across dashboard pages | Implemented (`workflow_state.json`) |
| FR-13 | Export per-pair JSON, CSV summary, PNG evidence visualization | Implemented |

## 2. Non-functional requirements

| ID | Requirement | Status |
|---|---|---|
| NFR-1 | CPU-only operation, no GPU dependency | Met |
| NFR-2 | Memory-conscious handling of large products (memory-mapped I/O, tiling) | Met (`app/core/tiles.py`, adapter mmap usage) |
| NFR-3 | Runs on Windows 10/11 with Python 3.10+ | Met (target platform); also verified on Linux/Python 3.12 in this delivery's sandbox |
| NFR-4 | No data leaves the local machine | Met — dashboard reads a local folder only, no network calls in the pipeline |
| NFR-5 | UI remains usable at 1366×768 through 1920×1080 | Design target — see [`docs/30`... layout notes below] |
| NFR-6 | Errors are presented with cause/action before raw traceback | Met — dashboard diagnostics panel |

## 3. Input requirements

- Chandrayaan-2 product binary + PDS4 XML label (or ENVI `.hdr`, or raw+JSON/text sidecar).
- Optional ISRO GRD geometry CSV referenced by the label, for footprint intersection and
  Scan/Pixel↔Lat/Lon mapping.

## 4. Output requirements

Per [`docs/12_RESULTS_INTERPRETATION.md`](12_RESULTS_INTERPRETATION.md): per-pair JSON with
`status`, `tentative_matches`, `inliers`, `inlier_ratio`, `coverage`, `rmse_px`, `rmse_m`,
`scale_cascade`; `summary.json` with `project_verdict`; `pair_summary.csv`; PNG evidence
visualization; `workflow_state.json`.

## 5. UI requirements

Four-tab structure (Mission Overview / Correspondence Lab / Evidence & Metrics / Products &
Export), Correspondence Lab as the sole execution surface, live per-stage status
(`WAITING/RUNNING/COMPLETE/FAILED/INSUFFICIENT EVIDENCE`), non-color-only status indicators,
tooltips for technical terms. See [`docs/14_USER_GUIDE.md`](14_USER_GUIDE.md).

## 6. Scientific requirements

- No fabricated matches, inliers, accuracy, precision, recall, RMSE, or subpixel claims.
- Evidence gate thresholds are fixed and documented, not tunable from the UI to produce a
  desired status.
- Software-correctness claims (tests passing) are never presented as scientific-validation
  claims. See [`docs/10_VALIDATION_AND_EVIDENCE.md`](10_VALIDATION_AND_EVIDENCE.md).

## 7. Performance requirements

CPU-first; large products handled via memory-mapping and tiling rather than full in-RAM loads
(NFR-2). No specific latency SLA is claimed — see
[`docs/18_LIMITATIONS_AND_FUTURE_WORK.md`](18_LIMITATIONS_AND_FUTURE_WORK.md).

## 8. Reproducibility requirements

Every result traceable to a specific code version, configuration, and product ID set — see
[`docs/17_REPRODUCIBILITY.md`](17_REPRODUCIBILITY.md).

## 9. Error-handling requirements

Per-pair exceptions do not crash a multi-pair run; caught and reported as `status: "ERROR"` with
type/message, with full traceback available in an expandable diagnostics panel, not the main UI
flow by default.

## 10. Security / privacy considerations

- No mission data is transmitted off the local machine by the pipeline or dashboard.
- No telemetry or analytics collection is implemented in this codebase.
- Output folders are written under the user's chosen mission-data parent directory or an
  explicit `--out` path; no writes outside user-specified locations.

## 11. Acceptance criteria

- `python -m pytest -q` passes with no failures.
- `python run.py` (synthetic self-test) passes its own evidence gate.
- Dashboard launches, scans a mission folder, and all four tabs render without error against
  real or self-test data.
- No status is ever displayed as `VALIDATED` unless `app/core/evidence.py`'s `gate()` function
  actually returned that status for that specific result.
