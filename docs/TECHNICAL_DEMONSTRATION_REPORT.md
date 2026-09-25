# CHANDRABHAR-2 — Technical Demonstration Report

*(Note on terminology: "TDR" is ambiguous between "Technical Design Report" and "Technical
Demonstration Report." This document is the latter — a record of what running the system
actually demonstrates. The former is [`docs/TECHNICAL_DESIGN_REPORT.md`](TECHNICAL_DESIGN_REPORT.md).
Neither is an official government TDR format.)*

## 1. Project background

CHANDRABHAR-2 is a renamed, re-productized continuation of an existing working prototype (see
[`CHANGELOG.md`](../CHANGELOG.md)) targeting cross-sensor correspondence across Chandrayaan-2
OHRC, TMC-2, and IIRS imagery.

## 2. Problem statement

See [`docs/02_PROBLEM_STATEMENT.md`](02_PROBLEM_STATEMENT.md).

## 3. Objectives

1. Demonstrate a working, inspectable pipeline from raw Chandrayaan-2 products through to a
   gated correspondence result.
2. Demonstrate that the evidence gate genuinely distinguishes strong from weak results (shown
   here on a synthetic, known-answer scene since real mission data was not available in the
   environment used to prepare this report — see §7).
3. Demonstrate the live workflow visibility (per-stage status) and export packaging.

## 4. System architecture

See [`docs/03_SYSTEM_ARCHITECTURE.md`](03_SYSTEM_ARCHITECTURE.md) and
[`docs/assets/diagrams/`](assets/diagrams/).

## 5. Methodology

See [`docs/05_SCIENTIFIC_METHOD.md`](05_SCIENTIFIC_METHOD.md) and
[`docs/06_CORRESPONDENCE_PIPELINE.md`](06_CORRESPONDENCE_PIPELINE.md).

## 6. Implementation

See [`docs/15_DEVELOPER_GUIDE.md`](15_DEVELOPER_GUIDE.md).

## 7. Experimental setup (this report)

Because this report was prepared in an environment without access to real Chandrayaan-2 mission
products or a local browser/display, the demonstration evidence in this report is the software's
own **synthetic self-test** (`app/selftest.py`, invoked via `python run.py`), run for real as
part of preparing this document:

- **Scene:** a 1200×1200 synthetic panchromatic-style image (random circles and line segments,
  seeded for reproducibility, `numpy.random.default_rng(7)`).
- **Perturbation:** a known affine transform — 4° rotation about (600,600) plus a (+12, −9) pixel
  translation — applied to produce a second "sensor" image from the same scene.
- **Assumed GSD:** 0.25 m for both (same-GSD self-consistency check; this test does not exercise
  the cross-scale GSD cascade the way a real OHRC↔IIRS pair would).

This demonstrates the matcher → RANSAC → evidence-gate → export chain end to end, on a scene
where the "correct answer" (the applied transform) is known — it is a software self-consistency
demonstration, not a scientific validation on real sensor data.

## 8. Sensor information

See [`docs/04_DATA_AND_SENSORS.md`](04_DATA_AND_SENSORS.md) for OHRC/TMC-2/IIRS characteristics.
No real sensor products were processed for this report.

## 9. Processing pipeline

See [`docs/06_CORRESPONDENCE_PIPELINE.md`](06_CORRESPONDENCE_PIPELINE.md).

## 10. Results (this report's demonstration run)

Actual output of `python run.py`, captured while preparing this document:

```
CHANDRABHAR-2 ENGINE SELF-TEST PASSED
{'passed': True, 'inliers': 327, 'ratio': 0.3605, 'coverage': 0.9375, 'rmse_px': 0.7986}
```

Gate evaluation: `tentative_matches` sufficient, `inliers=327 ≥ 12`, `inlier_ratio=0.36 ≥ 0.35`,
`coverage=0.94 ≥ 0.35`, `rmse_px=0.80 ≤ 2.5` → **all five thresholds met → `VALIDATED`** for this
synthetic pair. Evidence visualization:
[`docs/assets/screenshots/synthetic_selftest_evidence.png`](assets/screenshots/synthetic_selftest_evidence.png).

## 11. Validation

This result validates the software mechanism (matcher, RANSAC, evidence gate, export all work
correctly together and correctly recover a known transform). It does **not** validate scientific
correspondence on real Chandrayaan-2 data — see
[`docs/10_VALIDATION_AND_EVIDENCE.md`](10_VALIDATION_AND_EVIDENCE.md).

## 12. Limitations

See [`docs/18_LIMITATIONS_AND_FUTURE_WORK.md`](18_LIMITATIONS_AND_FUTURE_WORK.md).

## 13. Future work

Re-run this same demonstration protocol against real OHRC↔TMC-2, OHRC↔IIRS, and TMC-2↔IIRS
product pairs, and publish the resulting JSON/CSV/PNG alongside a revision of this report with
real results substituted for the synthetic ones above.

## 14. Reproducibility

`python run.py` reproduces §10 (exact numbers may vary slightly run to run due to floating-point
and any algorithmic randomness in the matcher cascade, but should remain well within the gate's
thresholds on this scene). See [`docs/17_REPRODUCIBILITY.md`](17_REPRODUCIBILITY.md).

## 15. Deployment instructions

See [`docs/13_INSTALLATION_WINDOWS.md`](13_INSTALLATION_WINDOWS.md) and
[`docs/14_USER_GUIDE.md`](14_USER_GUIDE.md).

## 16. Screenshots

See [`docs/assets/screenshots/README.md`](assets/screenshots/README.md) for what is and is not
included in this delivery.

## 17. Diagrams

See [`docs/assets/diagrams/`](assets/diagrams/).

## 18. References

- ISRO PRADAN Chandrayaan-2 archive: https://pradan.issdc.gov.in/ch2/ (external reference —
  verify current terms there; see [`LEGAL/ISRO_DATA_ATTRIBUTION.md`](../LEGAL/ISRO_DATA_ATTRIBUTION.md)).
