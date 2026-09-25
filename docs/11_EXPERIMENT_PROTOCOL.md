# 11 — Experiment Protocol

This is the step-by-step protocol CHANDRABHAR-2 follows for a real-mission experiment, as
implemented by `python -m app.cli.main mission` and mirrored by the dashboard's Correspondence
Lab. It supersedes and incorporates the original `REAL_MISSION_PROTOCOL.md` from the pre-rebrand
codebase (preserved for provenance at [`docs/history/`](history/)).

## Protocol steps

1. **Label and geometry consistency check.** Each product's XML/HDR label is inspected and
   binary-size consistency with the declared array shape/dtype is verified before any processing.
2. **Confirm native GSD and acquisition/illumination metadata.** Only what the label actually
   states is used; missing fields are reported as missing (see
   [`docs/04_DATA_AND_SENSORS.md`](04_DATA_AND_SENSORS.md)).
3. **Restrict to the documented geographic overlap.** Processing is restricted to the true swath
   intersection (`docs/07_GEOMETRIC_MODEL.md`) when a trusted geometry table is available.
4. **Build representations at common physical GSD levels** per the cascade in
   [`docs/08_GSD_AND_SCALE_NORMALIZATION.md`](08_GSD_AND_SCALE_NORMALIZATION.md).
5. **Keep computational tiling separate from physical GSD** at all times (see
   [`docs/03_SYSTEM_ARCHITECTURE.md`](03_SYSTEM_ARCHITECTURE.md)).
6. **Estimate geometry with RANSAC**, requiring spatially distributed inliers (the `coverage`
   gate threshold), not just a numerically large inlier count clustered in one region.
7. **Report pairwise evidence independently** for OHRC↔TMC-2, OHRC↔IIRS, and TMC-2↔IIRS — each
   pair's evidence gate is evaluated on its own; one pair passing does not influence another's
   reported status.
8. **Only then report a three-sensor correspondence verdict**, and only as
   `EVIDENCE_SUFFICIENT_FOR_THREE_SENSOR` if all three pairwise gates independently pass.
9. **Preserve product IDs, labels, configuration, code version, and metrics** in the output
   report (`summary.json`, per-pair JSON, `pair_summary.csv`) so the experiment is traceable and
   reproducible (see [`docs/17_REPRODUCIBILITY.md`](17_REPRODUCIBILITY.md)).

## Running it

```powershell
python -m app.cli.main mission --root "C:\path\to\mission_data" --out outputs\mission_validation
```

or via the dashboard's **Correspondence Lab** tab, selecting "run all three pairs."

## Development candidate audit

A geometry-only audit (no matching, just geometry/footprint sanity-checking) is available
separately:

```powershell
python -m app.cli.main geometry-audit --root "C:\path\to\mission_data"
```

This confirms the selected products' geometry tables parse and their pairwise footprint
intersections compute — it is a catalogue/geometry sanity check, not a registration or validation
result.
