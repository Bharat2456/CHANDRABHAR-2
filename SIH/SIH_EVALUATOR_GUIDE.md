# SIH Evaluator Guide — CHANDRABHAR-2

## Understand this prototype in ~5 minutes

1. **What it's trying to do (30 s).** Relate locations across Chandrayaan-2's three imagers
   (OHRC ~0.3 m, TMC-2 ~5 m, IIRS ~80 m hyperspectral) despite very different scale, modality,
   illumination, and acquisition date. See
   [`../docs/02_PROBLEM_STATEMENT.md`](../docs/02_PROBLEM_STATEMENT.md).

2. **What's actually built (1 min).** A full pipeline: format-aware product discovery → true
   swath geometry intersection → common physical-GSD grid → illumination-aware representation →
   matcher cascade (SIFT/phase-correlation/ECC) → RANSAC → a fixed evidence gate. Read the
   pipeline diagram at
   [`../docs/assets/diagrams/system_architecture.md`](../docs/assets/diagrams/system_architecture.md).

3. **What "done" means here (1 min).** A result is only reported `VALIDATED` if it passes five
   specific, documented thresholds (inliers ≥ 12, inlier ratio ≥ 0.35, coverage ≥ 0.35, RMSE ≤
   2.5 px, plus a minimum tentative-match floor) — see
   [`../docs/10_VALIDATION_AND_EVIDENCE.md`](../docs/10_VALIDATION_AND_EVIDENCE.md). This is
   enforced in code (`app/core/evidence.py`), not asserted in a slide.

4. **What's tested vs. what's validated (1 min).** 18/18 unit tests pass, and a synthetic,
   known-answer self-test correctly passes the evidence gate (see
   [`../docs/TEST_AND_VALIDATION_REPORT.md`](../docs/TEST_AND_VALIDATION_REPORT.md)). This is
   software correctness. Real Chandrayaan-2 data validation across all three pairs has **not**
   been asserted as complete in this delivery — see
   [`../docs/CLAIMS_MATRIX.md`](../docs/CLAIMS_MATRIX.md). The team is not claiming more than
   this.

5. **Where to poke at it (1.5 min).** Run the dashboard, point it at real or synthetic data, run
   a pair in Correspondence Lab, and check that the Evidence & Metrics numbers match what
   `app/core/evidence.py`'s thresholds would imply. If a pair reports `INSUFFICIENT_EVIDENCE`,
   check the `reasons` field — it should be specific and diagnosable, not a bare failure.

## Questions worth asking (and where the answer lives)

| Question | Answer location |
|---|---|
| "Has this actually been run on real Chandrayaan-2 data?" | [`../docs/CLAIMS_MATRIX.md`](../docs/CLAIMS_MATRIX.md) — honestly: not asserted complete in this delivery |
| "How do you know the evidence gate isn't just always passing?" | [`../docs/TEST_AND_VALIDATION_REPORT.md`](../docs/TEST_AND_VALIDATION_REPORT.md) — two unit tests specifically check that fallback matcher stages can't produce a false positive |
| "What happens with a bounding-box vs. real overlap?" | [`../docs/07_GEOMETRIC_MODEL.md`](../docs/07_GEOMETRIC_MODEL.md) |
| "Does this need a GPU?" | No — [`../docs/03_SYSTEM_ARCHITECTURE.md`](../docs/03_SYSTEM_ARCHITECTURE.md) |
| "Is this an ISRO product?" | No — [`../LEGAL/ISRO_DATA_ATTRIBUTION.md`](../LEGAL/ISRO_DATA_ATTRIBUTION.md) |

## Red flags this project deliberately avoids (and how to check)

- No status is ever shown as `VALIDATED` without the specific numeric thresholds in
  `app/core/evidence.py` being met — inspect that file directly, it's four lines of readable
  logic.
- No screenshot or figure in `docs/assets/screenshots/` is fabricated — see that folder's own
  README for exactly what is real vs. not included.
- No unsupported superlatives ("solves", "ISRO-certified", "mission-ready", "fully validated") —
  see [`../branding/brand_guidelines.md`](../branding/brand_guidelines.md).
