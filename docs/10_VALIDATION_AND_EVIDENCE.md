# 10 — Validation and Evidence

## The evidence gate, exactly as implemented

`app/core/evidence.py`:

```python
def gate(result):
    reasons = []
    if result.tentative_matches < 8:   reasons.append('too_few_tentative_matches')
    if result.inliers < 12:            reasons.append('too_few_inliers')
    if result.inlier_ratio < 0.35:     reasons.append('low_inlier_ratio')
    if result.coverage < 0.35:         reasons.append('low_spatial_coverage')
    if result.rmse_px is None or result.rmse_px > 2.5:
        reasons.append('high_or_missing_rmse')
    return {'status': 'VALIDATED' if not reasons else 'INSUFFICIENT_EVIDENCE', 'reasons': reasons}
```

A result is `VALIDATED` **only if all five conditions pass simultaneously**:

| Threshold | Requirement | Rationale |
|---|---|---|
| Tentative matches | ≥ 8 | Below this, RANSAC has too little to fit against |
| RANSAC inliers | ≥ 12 | A minimum floor of spatially-consistent correspondences |
| Inlier ratio | ≥ 0.35 | At least ~35% of candidates must agree with one geometric model |
| Spatial coverage | ≥ 0.35 | Inliers must span a meaningful fraction of the overlap area, not cluster in one corner |
| RMSE | ≤ 2.5 px (common-grid pixels) | Residual geometric error must be small |

If any threshold fails, the result is `INSUFFICIENT_EVIDENCE` and the JSON output lists exactly
which reason(s) failed (e.g. `["low_inlier_ratio", "high_or_missing_rmse"]`) — the failure is
diagnosable, not a bare "failed."

## Independent evidence vs. descriptive/visual output

The five gate inputs above (tentative matches, inliers, inlier ratio, coverage, RMSE) are all
computed directly from the geometrically-verified correspondence set — this is the project's
**independent evidence**. The PNG correspondence visualization rendered for the Evidence &
Metrics page and for exports is a **descriptive rendering of that same evidence** for human
inspection; it is not a second, separate source of evidence, and it is never generated or shown
for a pair that produced no result. The dashboard and reports keep these visually and
structurally distinct (see [`docs/05_SCIENTIFIC_METHOD.md`](05_SCIENTIFIC_METHOD.md)).

## Software correctness vs. scientific validation

These are two different claims and this project does not conflate them:

- **Software correctness** — does the code run without error, do the unit tests pass, does the
  self-test on a synthetic, known-warp scene recover that warp within tolerance? See
  [`docs/TEST_AND_VALIDATION_REPORT.md`](TEST_AND_VALIDATION_REPORT.md). This is currently true:
  18/18 unit tests pass, and the synthetic self-test passes its own gate.
- **Scientific validation** — does a real OHRC↔TMC-2, OHRC↔IIRS, or TMC-2↔IIRS pair, run on
  actual Chandrayaan-2 products, clear the evidence gate above? This is **not asserted by this
  document** and must be established by running the `mission` command or the Correspondence Lab
  against real data and reading the resulting `status` field.

## Three-sensor verdict

`python -m app.cli.main mission` sets `project_verdict = 'EVIDENCE_SUFFICIENT_FOR_THREE_SENSOR'`
only if **all three** pairwise gates report `VALIDATED`; otherwise it reports `NOT_VALIDATED`.
This verdict is never manually overridden.

## Current status

See [`docs/CLAIMS_MATRIX.md`](CLAIMS_MATRIX.md) for the up-to-date, claim-by-claim status table.
As of this delivery: the pipeline is implemented and self-tests pass; real-data validation for
all three pairs must be (re-)run on the current engine version before any `VALIDATED` claim can
be made for real Chandrayaan-2 products.
