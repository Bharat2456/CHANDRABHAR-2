# LunaMatch 7.0.5

## True swath geometry release

- Reconstructs the perimeter of native ISRO GRD Scan x Pixel geometry samples instead of using a global affine fit or convex hull for mission overlap decisions.
- Uses polygon intersection on the sampled swath perimeter when Shapely is available.
- Maps the exact intersection polygon back to native Scan/Pixel windows before physical-GSD tiling.
- Geometry audit now reports footprint method, intersection vertex count, and the true-swath intersection bbox.
- Adds Shapely as a required geometry dependency for deterministic mission-data processing.
- Does not claim real Chandrayaan-2 correspondence validation until the user's downloaded products are executed end-to-end.
