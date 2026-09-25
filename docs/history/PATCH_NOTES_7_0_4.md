# LunaMatch 7.0.4

## Geometry correctness release

- Native ISRO CH-2 GRD columns `Scan, Pixel, Latitude, Longitude` are now parsed directly.
- PDS4 adapter discovers sibling `*_g_grd_*.csv` geometry products robustly.
- Geometry footprints are derived from sampled geometry points using a convex hull.
- Pair AOI can be derived from geometry-hull intersection rather than only XML corner bounding boxes.
- Pixel windows are mapped from the actual sampled geometry for the selected AOI.
- Existing non-mission formats retain their generic footprint behavior.

This release does **not** claim real Chandrayaan-2 validation. It fixes the geometry ingestion/mapping path required for such validation.
