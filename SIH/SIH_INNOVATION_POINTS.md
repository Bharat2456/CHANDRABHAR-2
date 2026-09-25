# SIH Innovation Points — CHANDRABHAR-2

1. **A conservative, mechanically-enforced evidence gate**, rather than a system that always
   reports "a match." Weak or spurious correspondence is reported as
   `INSUFFICIENT_EVIDENCE` with specific, diagnosable reasons — never silently upgraded. This is
   unusual for a hackathon prototype, where the incentive normally runs toward always showing a
   "success" result.

2. **True swath-perimeter geometry** instead of the far more common bounding-box overlap
   approximation, directly using ISRO's own GRD Scan/Pixel↔Lat/Lon convention.

3. **A physical-GSD invariant kept architecturally separate from computational tiling** — the
   reported ground resolution is never accidentally a display or memory-driven artifact, which is
   a subtle correctness trap this project explicitly engineered around (see
   [`../docs/03_SYSTEM_ARCHITECTURE.md`](../docs/03_SYSTEM_ARCHITECTURE.md)).

4. **Explicit separation of software correctness from scientific validation** throughout the
   entire documentation set and the UI itself — a distinction most student/hackathon prototypes
   blur, and one this project's evidence gate and docs both consistently maintain (see
   [`../docs/10_VALIDATION_AND_EVIDENCE.md`](../docs/10_VALIDATION_AND_EVIDENCE.md)).

5. **A genuinely CPU-first design** for a problem (multimodal, multi-scale image correspondence)
   that is often approached with GPU-heavy learned matchers — making the prototype runnable on
   ordinary hackathon/evaluation laptops.

6. **A single, disciplined execution surface** (Correspondence Lab) in the UI, with every other
   tab strictly read-only over that execution's output — avoiding the common dashboard anti-pattern
   of hidden computation triggered from multiple places with inconsistent state.

## What is *not* claimed as innovation

The individual computer-vision techniques used (SIFT, phase correlation, ECC, RANSAC) are
standard, well-established methods — the innovation here is in their disciplined combination,
the geometry/GSD handling around them, and the evidence-gate/documentation discipline, not in a
novel matching algorithm itself. See
[`SIH_LIMITATIONS_AND_NEXT_STEPS.md`](SIH_LIMITATIONS_AND_NEXT_STEPS.md) for an honest accounting
of what is not yet demonstrated.
