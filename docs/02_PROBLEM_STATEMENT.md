# 02 — Problem Statement

## The problem

Chandrayaan-2 carries three payloads relevant to this project — OHRC, TMC-2, and IIRS — that
image the same lunar surface under conditions that differ along nearly every axis that makes
image correspondence hard:

| Axis | OHRC | TMC-2 | IIRS |
|---|---|---|---|
| Modality | Panchromatic | Panchromatic | Hyperspectral |
| Native GSD | ~0.3 m | ~5 m | ~80 m |
| Scale ratio vs. OHRC | 1× | ~17× coarser | ~270× coarser |
| Acquisition date | Independent orbit pass | Independent orbit pass | Independent orbit pass |
| Illumination (sun angle) | Independent | Independent | Independent |

A pixel-for-pixel or even feature-for-feature match between, say, OHRC and IIRS is not something
a generic feature matcher (SIFT/ORB/etc. run directly on the raw images) handles reliably: the
appearance of the same crater or ridge changes with resolution, with sun angle, and with sensing
modality, and the two images may have a 270× difference in effective ground sampling. A naive
match is easy to obtain and easy to be wrong about.

## Why this matters

Being able to relate a location in one Chandrayaan-2 product to the corresponding location in
another is a prerequisite for:

- combining panchromatic detail (OHRC) with spectral information (IIRS) at a given site,
- change detection between TMC-2 passes,
- building consistent multi-sensor mosaics or analysis products.

## What "solved" would mean, and why this project does not claim it

A genuinely solved correspondence system would report, for any real pair of overlapping
Chandrayaan-2 products, a geometric transform with quantified, independently-verified accuracy —
not just "some matches were found." CHANDRABHAR-2 implements the full pipeline needed to attempt
this and to *measure* whether it succeeded (see
[`docs/10_VALIDATION_AND_EVIDENCE.md`](10_VALIDATION_AND_EVIDENCE.md)), but whether it succeeds
on any specific real pair of products is an empirical question this document does not
pre-answer. See [`docs/CLAIMS_MATRIX.md`](CLAIMS_MATRIX.md) for the current status.

## Scope boundaries

- CHANDRABHAR-2 works on Chandrayaan-2 OHRC/TMC-2/IIRS products specifically (via the ISRO GRD
  Scan/Pixel geometry convention); it is not a general-purpose remote-sensing registration tool,
  though its adapter boundary (see [`docs/15_DEVELOPER_GUIDE.md`](15_DEVELOPER_GUIDE.md)) is
  designed to be extensible.
- It is CPU-first by design (see [`docs/18_LIMITATIONS_AND_FUTURE_WORK.md`](18_LIMITATIONS_AND_FUTURE_WORK.md))
  and does not require a GPU or large-scale infrastructure to run.
