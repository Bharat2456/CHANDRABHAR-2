# CHANDRABHAR-2 — Technical Design Report

## 1. Executive summary

CHANDRABHAR-2 is a CPU-first research prototype that attempts geometric correspondence between
Chandrayaan-2's OHRC, TMC-2, and IIRS imaging products, across a ~270× native scale range and
independent illumination/acquisition conditions. It implements a full pipeline — format
adaptation, geometric footprint intersection, physical-GSD common-grid normalization,
illumination-aware representation, a multi-method matcher cascade, RANSAC verification, and a
fixed evidence gate — and reports `VALIDATED` only when the gate's thresholds are met. This
report describes the design as actually implemented; it is not a claim of real-data validation
(see §23).

## 2. Problem statement

See [`docs/02_PROBLEM_STATEMENT.md`](02_PROBLEM_STATEMENT.md).

## 3. Requirements

See [`docs/SOFTWARE_REQUIREMENTS_SPECIFICATION.md`](SOFTWARE_REQUIREMENTS_SPECIFICATION.md).

## 4. Design goals

1. Handle real Chandrayaan-2 product formats and geometry conventions directly (no synthetic
   pre-processing required).
2. Never mislabel computational convenience (tiling, downsampling) as scientific resolution.
3. Never report a stronger validation status than the evidence supports.
4. Run on CPU-only, laptop-class hardware.
5. Keep the scientific core small, inspectable, and dependency-light.
6. Make every stage of the pipeline separately visible and testable.

## 5. System architecture

See [`docs/03_SYSTEM_ARCHITECTURE.md`](03_SYSTEM_ARCHITECTURE.md) for the full component map and
data-flow diagram.

## 6. Data flow

```
Mission Data → Data Discovery → Metadata / Geometry → Geographic Overlap → Common Lunar Grid
  → Physical GSD Normalization → Illumination-Aware Representation → Correspondence
  → Geometric Verification → Evidence Gate → Results / Export
```
Diagram: [`docs/assets/diagrams/system_architecture.md`](assets/diagrams/system_architecture.md).

## 7. Component architecture

See the component-ownership table in
[`docs/03_SYSTEM_ARCHITECTURE.md`](03_SYSTEM_ARCHITECTURE.md#component-ownership-what-each-file-is-responsible-for).

## 8. Scientific pipeline

See [`docs/06_CORRESPONDENCE_PIPELINE.md`](06_CORRESPONDENCE_PIPELINE.md) for the full
stage-by-stage description.

## 9. Metadata processing

Each product's native label (PDS4 XML / ENVI HDR / raw+sidecar) is parsed by its adapter into a
canonical `SceneSpec`; only fields actually present in the label are populated (see
[`docs/04_DATA_AND_SENSORS.md`](04_DATA_AND_SENSORS.md)).

## 10. Geographic overlap

True sampled-swath polygon intersection, not bounding-box overlap — see
[`docs/07_GEOMETRIC_MODEL.md`](07_GEOMETRIC_MODEL.md).

## 11. Common lunar grid

Both products are warped onto one shared geographic grid before matching — see
[`docs/03_SYSTEM_ARCHITECTURE.md`](03_SYSTEM_ARCHITECTURE.md).

## 12. Physical GSD normalization

`plan_common_gsd()` cascade — see
[`docs/08_GSD_AND_SCALE_NORMALIZATION.md`](08_GSD_AND_SCALE_NORMALIZATION.md).

## 13. Illumination-aware representation

See [`docs/09_ILLUMINATION_HANDLING.md`](09_ILLUMINATION_HANDLING.md).

## 14. Correspondence generation

SIFT → phase correlation → ECC affine cascade — see
[`docs/06_CORRESPONDENCE_PIPELINE.md`](06_CORRESPONDENCE_PIPELINE.md#stage-6--matching-cascade).

## 15. Geometric verification

RANSAC homography/affine fit, inlier/outlier separation — see
[`docs/07_GEOMETRIC_MODEL.md`](07_GEOMETRIC_MODEL.md#geometric-verification-ransac).

## 16. Evidence gate

Fixed thresholds, implemented in `app/core/evidence.py` — see
[`docs/10_VALIDATION_AND_EVIDENCE.md`](10_VALIDATION_AND_EVIDENCE.md).

## 17. Subpixel refinement

The ECC (Enhanced Correlation Coefficient) stage in the matcher cascade refines an affine
alignment iteratively to sub-integer-pixel precision when it is reached in the cascade; this is
an alignment-refinement technique, not an independently benchmarked subpixel-accuracy claim — no
"subpixel accurate" claim is made without a specific measured benchmark (see
[`branding/brand_guidelines.md`](../branding/brand_guidelines.md)).

## 18. CPU-first design

No GPU dependency anywhere in the pipeline; see
[`docs/18_LIMITATIONS_AND_FUTURE_WORK.md`](18_LIMITATIONS_AND_FUTURE_WORK.md) for the resulting
performance trade-offs.

## 19. Memory considerations

Products are memory-mapped where the adapter supports it, and processed via overlapping tiles
(`app/core/tiles.py`, `make_tiles(h, w, tile=1024, overlap=0.2)`) independent of the physical-GSD
decision, so a multi-gigabyte product is never required to load fully into RAM.

## 20. Error handling

Exceptions during a pair's registration are caught, written to that pair's result JSON as
`{"status": "ERROR", "error_type": ..., "error": ...}`, and surfaced in the dashboard behind an
expandable diagnostics panel rather than crashing the run of other pairs — see
[`docs/16_TROUBLESHOOTING.md`](16_TROUBLESHOOTING.md).

## 21. Outputs

Per-pair JSON, `summary.json`, `pair_summary.csv`, PNG evidence visualizations,
`workflow_state.json` — see [`docs/12_RESULTS_INTERPRETATION.md`](12_RESULTS_INTERPRETATION.md).

## 22. Testing

See [`docs/TEST_AND_VALIDATION_REPORT.md`](TEST_AND_VALIDATION_REPORT.md).

## 23. Validation

**Not asserted as complete for real Chandrayaan-2 data in this report.** See
[`docs/10_VALIDATION_AND_EVIDENCE.md`](10_VALIDATION_AND_EVIDENCE.md) and
[`docs/CLAIMS_MATRIX.md`](CLAIMS_MATRIX.md).

## 24. Limitations

See [`docs/18_LIMITATIONS_AND_FUTURE_WORK.md`](18_LIMITATIONS_AND_FUTURE_WORK.md).

## 25. Future work

See [`docs/18_LIMITATIONS_AND_FUTURE_WORK.md`](18_LIMITATIONS_AND_FUTURE_WORK.md#future-work).
