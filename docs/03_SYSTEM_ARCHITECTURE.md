# 03 — System Architecture

## Layered structure

```
app/
├── adapters/    # format-specific readers → canonical SceneSpec (PDS4, ENVI, raw+sidecar, NumPy)
├── geo/         # ISRO GRD Scan/Pixel <-> Lat/Lon geometry mapper, footprint intersection
├── io/          # out-of-core / memory-mapped product reading
├── core/        # the scientific pipeline itself (physical GSD, representation, matcher, evidence, tiling)
├── cli/         # command-line entry points (inspect, inventory, geometry-audit, mission, register, self-test)
└── selftest.py  # synthetic end-to-end regression check
dashboard.py     # Streamlit UI — Mission Overview / Correspondence Lab / Evidence & Metrics / Products & Export
```

## Data flow

```
Mission Data (local folder)
     │
     ▼
Data Discovery ─ app/adapters ─ finds *.xml / *.hdr / *.npy, classifies sensor via AdapterRegistry.inspect()
     │
     ▼
Metadata / Geometry ─ app/geo/mapper.py ─ reads the ISRO GRD geometry CSV, fits Scan/Pixel <-> Lat/Lon
     │
     ▼
Geographic Overlap ─ sampled swath perimeter intersection (Shapely if available, else a
                      polygon fallback) between the two products' footprints
     │
     ▼
Common Lunar Grid ─ app/core/physical.py plan_common_gsd() ─ a cascade of physically-meaningful
                     target GSDs (coarsest-of-the-pair × {1.0, 1.5, 2.5, 4.0, 6.0})
     │
     ▼
Physical GSD Normalization ─ app/core/geowarp.py ─ both products resampled onto the same
                              geographic grid at the chosen physical GSD
     │
     ▼
Illumination-Aware Representation ─ app/core/representation.py ─ robust-normalized,
                                     log/high-pass/structural/sun-azimuth-directional channels
                                     (or spectral median+IQR for hyperspectral IIRS)
     │
     ▼
Correspondence ─ app/core/matcher.py ─ SIFT → phase correlation → ECC affine cascade
     │
     ▼
Geometric Verification ─ RANSAC homography/affine fit, inlier/outlier separation
     │
     ▼
Evidence Gate ─ app/core/evidence.py gate() ─ VALIDATED vs INSUFFICIENT_EVIDENCE
     │
     ▼
Results / Export ─ JSON result + CSV summary + PNG evidence visualization + workflow_state.json
```

## Component ownership (what each file is responsible for)

| File | Responsibility |
|---|---|
| `app/adapters/*.py` | Parse a product's native metadata/label into a canonical `SceneSpec` (sensor, product ID, array, GSD, sun angle, geometry CSV path) |
| `app/geo/mapper.py` | `GeometryMapper` — fits and inverts the ISRO GRD Scan/Pixel↔Lat/Lon relation; computes footprint bounding boxes and true polygon intersections between two products |
| `app/core/physical.py` | `plan_common_gsd()` — produces a `PhysicalPlan` cascade of target physical GSDs and the resample factor each sensor needs to reach them |
| `app/core/geowarp.py` | Warps both products onto the shared geographic grid at a chosen physical GSD |
| `app/core/representation.py` | `robust_norm`, `structural`, `illumination_invariant`, `modality_rep` — turns raw pixel values into matching-ready representations |
| `app/core/tiles.py` | `make_tiles()` — splits a large array into overlapping tiles for out-of-core / memory-conscious processing, independent of the physical-GSD decision |
| `app/core/matcher.py` | The SIFT → phase-correlation → ECC matcher cascade and RANSAC verification |
| `app/core/evidence.py` | `gate()` — the fixed thresholds that decide `VALIDATED` vs `INSUFFICIENT_EVIDENCE` |
| `app/core/pipeline.py` | `Engine` — orchestrates the full stage sequence above for a `register()` call, and `save()`s the JSON result |
| `dashboard.py` | Streamlit UI: mission scanning, execution, live workflow state, evidence rendering, export |
| `app/cli/main.py` | `inspect`, `inventory`, `geometry-audit`, `mission` (all three pairs), `register` (one pair), `self-test` |

## Why tiling and physical GSD are kept separate

A key architectural decision, preserved unchanged from the original engine: **computational
tiling (`app/core/tiles.py`) never changes the physical GSD the system reports.** Tiling exists
purely to bound memory use on large products; the physical-GSD cascade in `physical.py` is
computed independently and is what actually gets reported as the registration's ground
resolution. This prevents a display-resolution or memory-driven resize from being mislabeled as
scientific common-resolution registration.

## CPU-first design

No component requires a GPU. See
[`docs/18_LIMITATIONS_AND_FUTURE_WORK.md`](18_LIMITATIONS_AND_FUTURE_WORK.md) for the
performance implications of this choice.
