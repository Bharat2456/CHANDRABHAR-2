# 09 — Illumination Handling

## Why illumination matters here

OHRC, TMC-2, and IIRS passes over the same lunar terrain happen on different orbits and dates,
under different sun elevation and azimuth angles. On airless, high-relief lunar terrain, shading
direction and shadow length change dramatically with sun angle — the same crater can look very
different in raw pixel intensity between two passes even with no change in the terrain itself.
Matching directly on raw intensity is therefore fragile across sun-angle differences.

## What the representation stage does about it

`app/core/representation.py`'s `illumination_invariant(x, solar_elev, solar_az)` builds a
4-channel representation instead of using raw intensity directly:

1. **Log-compressed intensity** (`log1p`-scaled) — reduces sensitivity to overall brightness
   scale/gain differences between sensors and passes.
2. **High-pass** (image minus a Gaussian-blurred version of itself) — removes slowly-varying
   shading gradients, keeping local structure.
3. **Structural magnitude** (Sobel gradient magnitude, via `structural()`) — edges and ridgelines
   are far less sensitive to which direction the sun is shining from than raw intensity is.
4. **Sun-azimuth-directional gradient** — when solar azimuth is known from the product metadata,
   the gradient is projected along that direction (`cos(az)*gx + sin(az)*gy`); when it is not
   known, an isotropic `|gx|+|gy|` fallback is used instead of guessing an azimuth.

## Honesty note on "illumination-aware" vs. "illumination-invariant"

The project's copy consistently says **illumination-aware**, not "illumination-invariant" or
"shadow-corrected": the representation above reduces sensitivity to shading direction, it does
not perform physical photometric correction (no bidirectional reflectance modeling, no shadow
removal). This is a deliberate, accurate distinction — see
[`branding/brand_guidelines.md`](../branding/brand_guidelines.md) for the project's disallowed
overclaiming phrases.

## Multi-band (IIRS) case

For hyperspectral input, `modality_rep()` does not run the single-band illumination pipeline
directly; instead it uses a spectral median/spread/structural representation
(`docs/05_SCIENTIFIC_METHOD.md`) that is inherently less sensitive to any single band's
illumination-driven brightness shift, since it summarizes across the sampled band set rather than
matching on one band's raw values.
