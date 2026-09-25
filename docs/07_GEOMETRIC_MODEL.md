# 07 — Geometric Model

## The ISRO GRD geometry convention

Chandrayaan-2 products ship a Geometry Reference Data (GRD) table: samples of
`(Scan, Pixel, Longitude, Latitude)` giving the ground location of specific
image-space coordinates. `app/geo/mapper.py`'s `GeometryMapper` reads this table (capped at
`max_samples=200000` rows for memory safety) and builds two things from it:

1. **A Scan/Pixel ↔ Lon/Lat mapping** — a SciPy `LinearNDInterpolator` fit when SciPy is
   available (`_HAS_SCIPY`), used to convert between image coordinates and ground coordinates in
   either direction.
2. **The true swath footprint polygon** — traced by walking the *perimeter* of the sampled
   Scan×Pixel grid (`_grid_boundary()`: top edge at the first scan line, right edge at the last
   pixel column, bottom edge at the last scan line reversed, left edge at the first pixel column
   reversed), not a convex hull or bounding box of all sample points. This matters because a
   pushbroom swath is a long thin non-convex-adjacent strip; a convex hull would substantially
   overstate its extent.

## Footprint intersection

Two products' footprints are intersected with:
- an exact polygon intersection via **Shapely** (`unary_union`, `Polygon`) when the optional
  dependency is installed, or
- a documented convex-hull-based fallback (`_convex_hull()`, a standard monotone-chain
  algorithm) otherwise.

`intersection_bbox()` and `intersection_polygon()` (used by
`python -m app.cli.main geometry-audit`) expose both the bounding box and the polygon vertex
count of the actual overlap region between any two products.

## Why not just use a bounding box everywhere

A bounding-box overlap between two independently-oriented, independently-timed orbital swaths
routinely includes ground area that only one of the two products actually images. Restricting
correspondence search (and, later, the common lunar grid) to the true polygon intersection avoids
wasting computation on — and avoids ever attempting to match against — regions with no real
overlap.

## Geometric verification (RANSAC)

Once tentative correspondences exist (Stage 6 of
[`docs/06_CORRESPONDENCE_PIPELINE.md`](06_CORRESPONDENCE_PIPELINE.md)), RANSAC fits a
homography/affine transform and separates inliers (points consistent with one global geometric
model) from outliers. Only inliers are counted toward the evidence gate.

## Known geometric model limitations

- The Scan/Pixel↔Lon/Lat fit assumes the GRD sample grid is dense and accurate enough to
  interpolate between; very sparse geometry tables reduce fit quality (`rms` field on
  `GeometryMapper` reports the fit residual actually observed).
- The fallback convex-hull path (no Shapely) will overstate footprint area relative to the exact
  polygon path for strongly non-convex swaths.
