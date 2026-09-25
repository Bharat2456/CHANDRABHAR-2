# 12 — Results Interpretation

## Reading a pairwise result

Each pair produces a JSON result (and a row in `pair_summary.csv`) with these fields:

| Field | Meaning |
|---|---|
| `status` | `VALIDATED` or `INSUFFICIENT_EVIDENCE` (or `ERROR` with `error_type`/`error`) |
| `tentative_matches` | Candidate correspondences before geometric verification |
| `inliers` | Correspondences consistent with the fitted geometric model after RANSAC |
| `inlier_ratio` | `inliers / tentative_matches` |
| `coverage` | Fraction of the overlap area spanned by inlier locations |
| `rmse_px` | Residual error in common-grid pixels at the chosen physical GSD |
| `rmse_m` | The same residual converted to meters using that GSD |
| `scale_cascade` | Which physical-GSD level from `plan_common_gsd()` was actually used |
| `reasons` (on `INSUFFICIENT_EVIDENCE`) | Which specific gate threshold(s) failed |

## `VALIDATED`

All five evidence-gate thresholds passed. This means: enough candidate matches existed, RANSAC
found a geometrically consistent inlier set well above the floor, those inliers were spread
across a meaningful fraction of the overlap area (not clustered), and the residual error was
small. It does **not** by itself mean the transform is scientifically publication-grade — treat
it as "the automated evidence gate found this trustworthy by its stated criteria," and inspect
the visual evidence and RMSE in physical units before relying on it further.

## `INSUFFICIENT_EVIDENCE`

One or more gate thresholds failed; the specific `reasons` list says which. Common
interpretations:
- `too_few_tentative_matches` / `too_few_inliers` — the matcher cascade could not find enough
  structure in common between the two representations at the chosen GSD (possible causes:
  genuinely low visual overlap, one product mostly featureless terrain, or scale mismatch too
  large for the attempted cascade level).
- `low_inlier_ratio` — many candidates were found but most were geometrically inconsistent with
  each other (possible mismatch or repetitive-terrain confusion).
- `low_spatial_coverage` — inliers exist but are clustered in a small area, which is a weaker
  basis for a whole-scene geometric transform.
- `high_or_missing_rmse` — the fitted model does not explain the inlier positions precisely
  enough, or RMSE could not be computed at all.

This status is a scientifically useful, actionable result, not a bug — see
[`docs/18_LIMITATIONS_AND_FUTURE_WORK.md`](18_LIMITATIONS_AND_FUTURE_WORK.md) for what to try
next.

## `ERROR`

A software-level exception occurred (e.g. a product could not be located or parsed). `error_type`
and `error` in the JSON carry the underlying Python exception; the dashboard's expandable
diagnostics panel shows the full traceback (see
[`docs/16_TROUBLESHOOTING.md`](16_TROUBLESHOOTING.md)).

## Reading the three-sensor verdict

`project_verdict` in `summary.json` is `EVIDENCE_SUFFICIENT_FOR_THREE_SENSOR` only if all three
pairs independently report `VALIDATED`; otherwise it is `NOT_VALIDATED`. A single failing pair is
enough to keep the overall verdict `NOT_VALIDATED`, by design.
