# LunaMatch 7.0.6

## IIRS tile-window and mission-run resilience fix

- Corrects local-to-absolute native coordinate conversion for physical tiles.
- Prevents empty/reversed IIRS native windows from reaching OpenCV resize.
- Adds regression coverage for non-zero parent-window offsets and empty-window safety.
- Mission CLI now records an unexpected pair exception as `ERROR` and continues with remaining sensor pairs.
- Keeps the true sampled-swath geometry and physical-GSD behavior from 7.0.5 unchanged.
- Real Chandrayaan-2 validation remains evidence-gated.
