# LunaMatch 7.0.2

## Real-mission IIRS performance correction

- Fixed IIRS tile representation to read only the native-pixel window corresponding to the current physical-GSD tile.
- Removed the large `nanpercentile` call over the full AOI for every tile.
- Replaced the hyperspectral spread calculation with a deterministic order-statistic robust spread over sampled bands.
- Added a bounded native-window mapper for IIRS tiles.

This fixes the 7.0.1 real-run stall observed during IIRS processing without changing the physical-GSD invariant.
