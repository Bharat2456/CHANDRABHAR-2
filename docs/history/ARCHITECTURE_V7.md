# LunaMatch v7 — physical-scale, tile-first architecture

## What changed
1. **Physical GSD planning is independent of computational limits.** A memory cap may create tiles/strides, but the software reports the effective physical sampling and never relabels a display resize as exact common-GSD registration.
2. **Out-of-core reads.** PDS4, ENVI/QUAD, NumPy and raw+sidecar products are memory-mapped.
3. **Multi-modal representation.** Registration uses robust intensity/log/high-pass/gradient structure; hyperspectral IIRS can use spectral median + IQR features without loading all bands at once.
4. **Conservative evidence gate.** Weak matches are reported as insufficient evidence, not as success.
5. **Adapter boundary.** New formats implement `can_open()` + `inspect()` and expose a canonical `SceneSpec`.
6. **Three-sensor experiment.** Pairwise results can be combined only after independent evidence gates pass.

## Important scientific limitation
The package is engineered for real Chandrayaan-2 products, but code validation on synthetic data is not the same as mission validation. The included real-product configuration therefore makes no success claim until the user's downloaded products are actually processed.
