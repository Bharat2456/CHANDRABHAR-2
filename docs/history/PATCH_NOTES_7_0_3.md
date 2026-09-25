# LunaMatch 7.0.3 — geographic AOI correctness patch

## Fixed
- Pair-specific geographic AOI is now derived from the intersection of the two product footprints.
- Mission geometry CSVs are used by direct geographic-sample containment before any affine fallback.
- Removed the fixed South-Pole AOI fallback from the Chandrayaan-2 registration path.
- Added diagnostics for the pair AOI and geometry-window source.
- Generic products without footprint metadata retain full-scene behavior; this does not affect PDS4 Chandrayaan-2 products carrying footprints.

## Scientific invariant
Physical GSD remains explicit and unchanged by computational tiling. A real mission pair is no longer allowed to silently compare unrelated full-scene portions merely because their arrays have compatible dimensions.
