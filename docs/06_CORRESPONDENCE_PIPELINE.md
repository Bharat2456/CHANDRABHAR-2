# 06 — Correspondence Pipeline

This document walks `app/core/pipeline.py`'s `Engine.register(reference, source, name)` call
stage by stage, as actually implemented.

## Inputs

Two `SceneSpec` objects (produced by `AdapterRegistry.inspect()`), each carrying: sensor name,
product ID, a (possibly memory-mapped) pixel array, native GSD, solar elevation/azimuth, and a
path to the product's ISRO GRD geometry CSV.

## Stage 1 — Geometry and overlap

`app/geo/mapper.py`'s `GeometryMapper` loads each product's geometry CSV (Scan/Pixel ↔
Latitude/Longitude samples), fits the Scan/Pixel↔Lat/Lon relation (SciPy `LinearNDInterpolator`
when available, else a documented fallback), and derives the footprint polygon. The two
footprints are intersected (`intersection_bbox` / `intersection_polygon`) — this is a true
sampled-swath intersection, not a bounding-box overlap.

## Stage 2 — Physical GSD planning

`app/core/physical.py`'s `plan_common_gsd(ref_gsd, src_gsd)` computes a cascade of candidate
target GSDs based on the coarser of the two sensors' native GSD, at multiplier levels `(1.0,
1.5, 2.5, 4.0, 6.0)`. Each level is a `PhysicalPlan` carrying the target GSD and the exact
resample factor each sensor needs to reach it.

## Stage 3 — Common-grid warp

`app/core/geowarp.py` resamples both products onto the shared geographic grid at the chosen
physical GSD, using the geometry mapper's Lat/Lon↔Scan/Pixel relation — this is what makes "one
grid cell" mean the same ground distance for both sensors.

## Stage 4 — Representation

`app/core/representation.py`:
- `robust_norm` — percentile-clipped (2nd/98th) normalization, robust to outlier pixels.
- `structural` — Sobel-gradient-magnitude representation.
- `illumination_invariant` — a 4-channel stack (log-compressed intensity, high-pass, structural
  magnitude, sun-azimuth-directional gradient) used for panchromatic sensors.
- `modality_rep` — dispatches to a spectral median/spread/structural representation for
  multi-band (IIRS) input, or to `illumination_invariant` for single-band input.

## Stage 5 — Tiling (memory management only)

`app/core/tiles.py`'s `make_tiles(h, w, tile=1024, overlap=0.2)` splits the (potentially large)
common-grid arrays into overlapping tiles purely to bound memory use. This stage has no effect on
the physical GSD already fixed in Stage 2 — see
[`docs/03_SYSTEM_ARCHITECTURE.md`](03_SYSTEM_ARCHITECTURE.md#why-tiling-and-physical-gsd-are-kept-separate).

## Stage 6 — Matching cascade

`app/core/matcher.py` attempts, in order, until enough candidate correspondences are found:
1. Structural SIFT keypoint matching.
2. Phase correlation (frequency-domain shift estimation).
3. ECC (Enhanced Correlation Coefficient) affine refinement.

## Stage 7 — Geometric verification

Candidate correspondences are fit with RANSAC to a homography/affine model; points that are not
spatially consistent with the fitted model are marked outliers and excluded from the reported
inlier set.

## Stage 8 — Evidence gate

`app/core/evidence.py`'s `gate(result)` checks the verified result against fixed thresholds — see
[`docs/10_VALIDATION_AND_EVIDENCE.md`](10_VALIDATION_AND_EVIDENCE.md) — and returns `VALIDATED`
or `INSUFFICIENT_EVIDENCE` with the specific reasons.

## Stage 9 — Output

`Engine.save(result, path)` writes the full result (matches, inliers, inlier ratio, coverage,
RMSE in pixels and meters, scale cascade used, evidence-gate status and reasons) as JSON. The
dashboard additionally renders a PNG evidence visualization and a CSV pair summary.
