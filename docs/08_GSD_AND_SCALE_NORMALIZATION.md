# 08 — GSD and Scale Normalization

## The scale problem

OHRC (~0.3 m), TMC-2 (~5 m), and IIRS (~80 m) differ by up to ~270× in ground sampling distance.
Matching directly at native resolution is not meaningful — a single IIRS pixel covers roughly the
same ground area as ~70,000 OHRC pixels. CHANDRABHAR-2 addresses this by explicitly choosing a
**common physical ground-sample-distance (GSD)** before any matching happens, rather than
matching each sensor at its own native pixel grid and hoping a feature matcher compensates for
the scale gap implicitly.

## `plan_common_gsd()`

Implemented in `app/core/physical.py`:

```python
def plan_common_gsd(ref_gsd, src_gsd, mode='native_coarse', levels=(1.0,1.5,2.5,4.0,6.0)):
    base = max(ref_gsd, src_gsd)
    targets = [base * x for x in levels]   # mode='native_coarse' (default)
    return [PhysicalPlan(target_gsd_m=t, ref_factor=t/ref_gsd, src_factor=t/src_gsd, ...) for t in targets]
```

- The cascade always starts from **the coarser of the pair's native GSDs** (`base =
  max(ref_gsd, src_gsd)`) — the system never invents a resolution finer than what the coarser
  sensor can actually resolve.
- It then tries progressively coarser levels (1.0×, 1.5×, 2.5×, 4.0×, 6.0× the base GSD) as a
  cascade: correspondence is attempted at the finest common-sense level first, and the pipeline
  can fall back to coarser levels if finer ones do not yield enough structure to match on.
- Each level records the exact resample factor (`ref_factor`, `src_factor`) each sensor needs to
  reach that target GSD — this is what `app/core/geowarp.py` uses to actually resample.

## The physical-GSD invariant

**The GSD the system reports is always the physical target GSD chosen by `plan_common_gsd()`,
never a value implied by tile size, display size, or a memory-driven downsample.** This is
enforced by keeping tiling (`app/core/tiles.py`) architecturally separate from GSD planning — see
[`docs/03_SYSTEM_ARCHITECTURE.md`](03_SYSTEM_ARCHITECTURE.md#why-tiling-and-physical-gsd-are-kept-separate).
A result's JSON output includes the `scale_cascade` actually used, so the reported GSD is always
traceable to a specific, physically-grounded number, not a display artifact.

## Reported fields

Each pairwise result includes both `rmse_px` (residual in the common-grid pixel units at the
chosen GSD) and `rmse_m` (the same residual converted to meters using that GSD) — so scientific
readers can judge accuracy in physical, sensor-independent terms rather than pixels that mean a
different ground distance for every level of the cascade.
