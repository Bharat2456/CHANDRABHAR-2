# SIH Limitations and Next Steps — CHANDRABHAR-2

Stated plainly, for evaluators, in one place.

## What is not yet done

1. **Real three-sensor validation.** No `VALIDATED` result on real OHRC↔TMC-2, OHRC↔IIRS, or
   TMC-2↔IIRS Chandrayaan-2 products is asserted by this delivery. See
   [`../docs/CLAIMS_MATRIX.md`](../docs/CLAIMS_MATRIX.md).
2. **Real UI screenshots.** The four dashboard tabs were not captured against a live browser in
   the environment used to prepare this documentation (see
   [`../docs/assets/screenshots/README.md`](../docs/assets/screenshots/README.md)); only a
   synthetic self-test evidence image is included.
3. **Software license.** Not yet confirmed by the project author — see
   [`../LEGAL/LICENSE.md`](../LEGAL/LICENSE.md).
4. **OHRC↔IIRS scale gap.** At ~270×, this is the hardest pair for the current matcher cascade;
   `INSUFFICIENT_EVIDENCE` here is a plausible honest outcome that would motivate future
   coarse-to-fine matching work, not necessarily a defect.
5. **No dedicated CLI test suite.** CLI commands are exercised manually (`python run.py`,
   `pytest`) rather than via dedicated automated CLI tests.

## Next steps, in priority order

1. Obtain a real, geographically-overlapping OHRC/TMC-2/IIRS product set from PRADAN and run the
   full `mission` protocol, publishing the resulting JSON/CSV/PNG package (whatever the outcome).
2. Capture real dashboard screenshots on that run.
3. Resolve the software license with the project author/team.
4. If OHRC↔IIRS specifically proves `INSUFFICIENT_EVIDENCE` on real data, investigate a
   coarse-to-fine multi-resolution search extension before concluding the pair is unmatchable
   with this approach.
5. Add a dedicated (optionally opt-in, real-data) integration test once real products are
   available in a CI-safe location.

## Why this list exists

Per this project's own standards (see
[`../branding/brand_guidelines.md`](../branding/brand_guidelines.md) and
[`../docs/CLAIMS_MATRIX.md`](../docs/CLAIMS_MATRIX.md)), an honest limitations list is treated as
part of the deliverable, not an afterthought — an evaluator should be able to find every caveat
in one place rather than having to infer it.
