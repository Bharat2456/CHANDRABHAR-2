# LunaMatch 8.0.2 — Evidence Integrity Patch

- Phase-correlation dense grid points are explicitly marked model-generated and non-independent.
- Global tiled RANSAC no longer pools phase/ECC model-generated points as independent correspondence evidence.
- SIFT feature correspondences remain eligible for validation.
- This prevents dense registration fallbacks from inflating mission validation metrics.
