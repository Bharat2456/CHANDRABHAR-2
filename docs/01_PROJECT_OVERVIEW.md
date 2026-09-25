# 01 — Project Overview

## What CHANDRABHAR-2 is

CHANDRABHAR-2 is a CPU-first, offline-first research prototype for cross-sensor image
correspondence across Chandrayaan-2's three primary imaging payloads: **OHRC**, **TMC-2**, and
**IIRS**. It was built as a Smart India Hackathon (SIH) demonstration and is intended to be
technically defensible in front of research reviewers — the software is explicit about what has
been implemented, what has been tested, and what remains scientifically unvalidated.

## Origin and provenance

CHANDRABHAR-2 is the renamed and re-productized continuation of an existing working codebase
(internally developed as "LunaMatch", engine line v7 → v8.0.2, platform line 1.0.1 → 1.3.1). The
scientific core (adapters, geometry, physical GSD planning, representation, matcher, evidence
gate) is **unchanged** by this productization pass; only presentation, documentation, and
packaging were added. See [`CHANGELOG.md`](../CHANGELOG.md) for the full version history and the
provenance of every prior release.

## Who this is for

- **SIH evaluators** — see [`SIH/SIH_EVALUATOR_GUIDE.md`](../SIH/SIH_EVALUATOR_GUIDE.md) for a
  5-minute path through the prototype.
- **Researchers / professors** — see
  [`docs/05_SCIENTIFIC_METHOD.md`](05_SCIENTIFIC_METHOD.md) and
  [`docs/10_VALIDATION_AND_EVIDENCE.md`](10_VALIDATION_AND_EVIDENCE.md).
- **Developers / future collaborators** — see
  [`docs/15_DEVELOPER_GUIDE.md`](15_DEVELOPER_GUIDE.md) and
  [`docs/03_SYSTEM_ARCHITECTURE.md`](03_SYSTEM_ARCHITECTURE.md).

## What this document set does not claim

No document in this repository claims that CHANDRABHAR-2 is validated on real Chandrayaan-2
data, endorsed by ISRO, or "mission ready." See
[`branding/brand_guidelines.md`](../branding/brand_guidelines.md) for the specific phrasing this
project avoids, and [`docs/CLAIMS_MATRIX.md`](CLAIMS_MATRIX.md) for a claim-by-claim status
table.
