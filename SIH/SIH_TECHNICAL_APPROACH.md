# SIH Technical Approach — CHANDRABHAR-2

## Why this approach, specifically

1. **Physical GSD, not pixel GSD.** Instead of matching each sensor at its native pixel grid
   (where "one pixel" means a wildly different ground distance per sensor), both products are
   warped onto a common geographic grid at a deliberately chosen physical ground-sample-distance
   before any matching happens. See
   [`../docs/08_GSD_AND_SCALE_NORMALIZATION.md`](../docs/08_GSD_AND_SCALE_NORMALIZATION.md).
2. **True swath geometry, not bounding boxes.** Footprint overlap is computed as the actual
   sampled-swath polygon intersection from the ISRO GRD geometry table, avoiding the overstated
   overlap a bounding-box approach would produce for tilted/non-rectangular passes. See
   [`../docs/07_GEOMETRIC_MODEL.md`](../docs/07_GEOMETRIC_MODEL.md).
3. **Illumination-aware representation, not raw intensity.** Structural/gradient/directional
   features are used instead of raw pixel brightness, reducing (not eliminating) sensitivity to
   the different sun angles between independent orbital passes. See
   [`../docs/09_ILLUMINATION_HANDLING.md`](../docs/09_ILLUMINATION_HANDLING.md).
4. **A matcher cascade with fallback, not a single brittle method.** SIFT → phase correlation →
   ECC affine, so a single method's failure mode doesn't end the attempt — but every candidate
   still has to survive RANSAC and the evidence gate regardless of which stage found it.
5. **A fixed, mechanically-enforced evidence gate**, not a judgment call in the UI. Five
   thresholds (tentative matches, inliers, inlier ratio, coverage, RMSE) must all pass; two unit
   tests specifically guarantee a weak fallback match can never be misreported as validated
   (`test_ecc_dense_fallback_never_validates_without_independent_matches`,
   `test_phase_dense_fallback_never_counts_as_independent_validation` — see
   [`../docs/TEST_AND_VALIDATION_REPORT.md`](../docs/TEST_AND_VALIDATION_REPORT.md)).
6. **CPU-first**, so the prototype runs on the hardware available to a hackathon team, not only
   on GPU infrastructure. See
   [`../docs/03_SYSTEM_ARCHITECTURE.md`](../docs/03_SYSTEM_ARCHITECTURE.md).

## Technology choices

Python, NumPy, OpenCV (SIFT/ECC/phase correlation, image ops), SciPy (geometry interpolation),
Shapely (exact polygon intersection), Streamlit (dashboard). No deep-learning model is used for
matching — the pipeline is classical computer vision, chosen for CPU feasibility, interpretability
of failure modes, and because the evidence-gate approach depends on being able to reason about
*why* a match did or did not pass, which is harder to guarantee with an opaque learned matcher.

## Where the hard engineering actually is

Not the matcher itself (SIFT/ECC/phase correlation are standard OpenCV primitives) — the hard
parts are (a) correctly discovering and using each product's true swath geometry rather than an
approximation, (b) keeping the physical-GSD decision independent of any memory-driven tiling
decision so the reported resolution is never a display artifact, and (c) making the evidence gate
airtight enough that a fallback matching stage cannot accidentally produce a false positive — see
the unit tests referenced above.
