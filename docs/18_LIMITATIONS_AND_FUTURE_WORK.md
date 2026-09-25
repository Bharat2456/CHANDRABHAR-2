# 18 — Limitations and Future Work

## Current limitations

### Scientific
- **No confirmed real-data validation is asserted by this delivery.** The pipeline, evidence
  gate, and self-test are implemented and pass; whether specific real OHRC↔TMC-2, OHRC↔IIRS, or
  TMC-2↔IIRS product pairs clear the evidence gate has not been asserted here and must be run and
  read from actual output. See [`docs/10_VALIDATION_AND_EVIDENCE.md`](10_VALIDATION_AND_EVIDENCE.md).
- The ~270× scale gap between OHRC and IIRS is at the edge of what the current matcher cascade
  (SIFT → phase correlation → ECC) is likely to handle reliably; `INSUFFICIENT_EVIDENCE` on this
  pair specifically is a plausible and scientifically honest outcome, not necessarily a defect.
- The illumination-aware representation (`docs/09_ILLUMINATION_HANDLING.md`) reduces but does not
  eliminate sensitivity to sun-angle differences; it performs no physical photometric correction.
- The convex-hull footprint fallback (no Shapely) overstates non-convex swath area relative to
  the exact polygon path.

### Engineering
- CPU-first design means large products are processed more slowly than a GPU-accelerated
  pipeline would allow; this is an intentional trade-off for laptop-class accessibility, not an
  oversight (see [`docs/03_SYSTEM_ARCHITECTURE.md`](03_SYSTEM_ARCHITECTURE.md)).
- The geometry mapper's `LinearNDInterpolator` fit quality depends on the density of the supplied
  GRD geometry table; very sparse tables reduce Scan/Pixel↔Lat/Lon accuracy.
- Real screenshots of the dashboard on real mission data were not captured as part of this
  delivery (no local browser/display in the environment used to build this documentation set;
  see [`docs/assets/screenshots/`](assets/screenshots/)).

### Process
- The software license status requires author confirmation before distribution — see
  [`LEGAL/LICENSE.md`](../LEGAL/LICENSE.md).
- Legal/attribution wording for Chandrayaan-2 data should be checked against the current PRADAN
  terms before any public presentation — see
  [`LEGAL/ISRO_DATA_ATTRIBUTION.md`](../LEGAL/ISRO_DATA_ATTRIBUTION.md).

## Future work

- Re-run and publish real three-pair validation results on a specific, cited set of Chandrayaan-2
  product IDs, with the resulting JSON/CSV checked into a results archive (not fabricated ahead
  of time).
- Extend the matcher cascade with a coarse-to-fine multi-resolution search specifically tuned for
  the OHRC↔IIRS scale gap.
- Add an optional GPU-accelerated path for the matcher stage (kept strictly optional, per the
  project's CPU-first requirement — see `docs/03_SYSTEM_ARCHITECTURE.md`).
- Expand the adapter boundary to additional PDS4 product types as they become relevant.
- Capture a full real-data screenshot set once run on a machine with actual mission products and
  a browser/display available.
