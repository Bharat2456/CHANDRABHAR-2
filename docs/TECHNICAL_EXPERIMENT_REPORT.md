# CHANDRABHAR-2 — Technical Experiment Report

## Actual sensor products used

**None, in this report.** No real Chandrayaan-2 products were available in the environment used
to prepare this documentation delivery. Every number in this report comes from the software's
own synthetic self-test (`app/selftest.py`) or from the unit test suite — both are clearly
labeled as such throughout. See [`docs/TECHNICAL_DEMONSTRATION_REPORT.md`](TECHNICAL_DEMONSTRATION_REPORT.md)
§7 for the exact synthetic setup.

When this report is next updated against real data, this section should list: the specific
OHRC/TMC-2/IIRS product IDs used, their PRADAN download date, and their label-stated acquisition
context.

## Acquisition context

Not applicable to the synthetic demonstration in this report (single synthetic scene, no real
acquisition metadata). For real products, see
[`docs/04_DATA_AND_SENSORS.md`](04_DATA_AND_SENSORS.md) for what metadata the adapters extract.

## GSD

Synthetic demonstration used an assumed 0.25 m GSD for both "sensors" (same value for both, since
the synthetic scene is a same-resolution self-consistency check — see
[`docs/08_GSD_AND_SCALE_NORMALIZATION.md`](08_GSD_AND_SCALE_NORMALIZATION.md) for how real,
differing native GSDs are actually handled by `plan_common_gsd()`).

## Geographic overlap

Not applicable — the synthetic scene has 100% overlap by construction (same frame, warped). Real
products' overlap is computed as described in
[`docs/07_GEOMETRIC_MODEL.md`](07_GEOMETRIC_MODEL.md).

## Processing stages

All nine stages in [`docs/06_CORRESPONDENCE_PIPELINE.md`](06_CORRESPONDENCE_PIPELINE.md) executed
for the synthetic pair; `Engine(levels=(1.0,))` was used (single-level cascade, since the
synthetic scene needs no coarse-to-fine scale search).

## Experiment pairs

Only one synthetic pair was run for this report ("synthetic" — base image vs. its own
rotated+translated copy). No real OHRC↔TMC-2, OHRC↔IIRS, or TMC-2↔IIRS pair was run.

## Metrics

| Metric | Value (synthetic pair) |
|---|---|
| Tentative matches | 907 |
| Inliers | 327 |
| Inlier ratio | 0.3605 |
| Coverage | 0.9375 |
| RMSE (px) | 0.7986 |
| Status | `VALIDATED` |

(Captured from an actual `python run.py` execution during preparation of this report; re-run to
confirm, exact values may vary slightly.)

## Evidence-gate logic

See [`docs/10_VALIDATION_AND_EVIDENCE.md`](10_VALIDATION_AND_EVIDENCE.md) for the exact
thresholds and rationale.

## Actual results

The synthetic pair passed all five gate thresholds and was correctly reported `VALIDATED`. This
demonstrates the gate mechanism works as designed (it does reward a genuinely strong,
geometrically-consistent result) — it does not demonstrate that any real Chandrayaan-2 pair will
pass.

## Limitations

- No real-data results are reported here — see
  [`docs/18_LIMITATIONS_AND_FUTURE_WORK.md`](18_LIMITATIONS_AND_FUTURE_WORK.md).
- The synthetic scene is single-modality (same image, geometrically warped) and does not exercise
  the illumination-invariance or cross-modality (panchromatic vs. hyperspectral) aspects of the
  real problem — see [`docs/09_ILLUMINATION_HANDLING.md`](09_ILLUMINATION_HANDLING.md).
- The synthetic scene uses a single assumed GSD for both images and does not exercise the
  multi-level `plan_common_gsd()` cascade the way a real OHRC↔IIRS pair (~270× scale gap) would.

## Interpretation

This report should be read as evidence that the software mechanism is sound (self-consistent,
gate-enforcing, reproducible), not as evidence of correspondence between any real Chandrayaan-2
sensor pair. See [`docs/CLAIMS_MATRIX.md`](CLAIMS_MATRIX.md) for the current claim-by-claim
status.
