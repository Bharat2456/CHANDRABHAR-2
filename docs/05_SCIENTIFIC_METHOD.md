# 05 — Scientific Method

## Guiding principle

The system is deliberately conservative: **weak real-data matches are not promoted to success.**
This is enforced mechanically by the evidence gate (`app/core/evidence.py`), not left to
interpretation in the UI or the report text.

## Method, stage by stage

1. **Metadata and geometry discovery.** Every product's native label is parsed; nothing about
   its geometry, GSD, or acquisition context is assumed — it is read from the label or the
   accompanying ISRO GRD geometry CSV.
2. **True geographic overlap.** The two products' footprints are intersected as sampled swath
   polygons (with an exact Shapely intersection when the optional dependency is installed, and a
   convex-hull-based fallback otherwise), not as axis-aligned bounding boxes, which would
   overstate overlap for boresight-tilted or non-rectangular swaths.
3. **Common physical grid.** Both products are warped onto one shared lunar geographic grid at a
   deliberately chosen physical GSD (see [`docs/08_GSD_AND_SCALE_NORMALIZATION.md`](08_GSD_AND_SCALE_NORMALIZATION.md)),
   so that correspondence is being searched for at a resolution where it is actually meaningful
   to compare the two sensors, rather than at each sensor's arbitrary native pixel grid.
4. **Illumination-aware representation.** Because sun angle differs between passes, raw
   pixel-intensity matching is avoided in favor of structural/gradient/directional
   representations less sensitive to shading direction (see
   [`docs/09_ILLUMINATION_HANDLING.md`](09_ILLUMINATION_HANDLING.md)).
5. **Matcher cascade with fallback, not a single method.** SIFT is attempted first; if it does
   not produce enough candidates, phase correlation and then ECC affine refinement are tried.
   This is a robustness choice, not a way to manufacture more matches — every candidate still
   has to survive RANSAC and the evidence gate regardless of which stage produced it.
6. **Independent geometric verification.** RANSAC is used to separate genuine, spatially
   consistent inliers from the tentative candidate set; only inliers count toward the evidence
   gate's thresholds.
7. **Evidence gate — the actual scientific claim boundary.** A result is reported `VALIDATED`
   only if it passes fixed, documented thresholds on inlier count, inlier ratio, spatial
   coverage, and residual error simultaneously (see
   [`docs/10_VALIDATION_AND_EVIDENCE.md`](10_VALIDATION_AND_EVIDENCE.md)). Anything else is
   reported `INSUFFICIENT_EVIDENCE` with the specific reason(s) it failed.

## What counts as "independent" evidence

RANSAC inlier count, inlier ratio, spatial coverage, and RMSE are all computed from the same
correspondence set and are the project's **independent, gate-relevant evidence.** They are kept
visually and structurally distinct in the Evidence & Metrics page from any purely descriptive or
visualization-only output (e.g. a rendered overlay), which is **not** independent evidence of
correctness by itself. See the "independent vs. model-generated evidence" distinction in
[`docs/10_VALIDATION_AND_EVIDENCE.md`](10_VALIDATION_AND_EVIDENCE.md).

## What this method deliberately does not do

- It does not average or ensemble multiple weak results into a stronger claim.
- It does not treat software tests (regression/self-test passing) as scientific validation — see
  [`docs/TEST_AND_VALIDATION_REPORT.md`](TEST_AND_VALIDATION_REPORT.md) for that distinction.
- It does not report a three-sensor "solved" verdict unless all three pairwise gates pass
  independently (`app/cli/main.py mission` command, `project_verdict` field).
