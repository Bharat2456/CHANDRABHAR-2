# Performance and memory — measured, with caveats

All figures below were measured **once**, in **headless Chromium 153 on a 1-vCPU Linux sandbox** (local loopback server, no GPU). They are indicative, not benchmarks; no claim is made for other devices or browsers.

| Measurement | Result |
|---|---|
| Cold start: click "Use demo" → engine downloaded, compiled, packages loaded, products inspected (uncached) | ≈ 38 s |
| Engine assets (cached afterwards by the browser) | ≈ 43 MB (Pyodide core 12 MB; NumPy 2.8, SciPy 16.4, OpenCV 10.6, Shapely 0.8 MB wheels) |
| Same boot in Node (warm disk) | ≈ 9.5 s |
| Registration of the synthetic 520×520 (2 m) vs 260×260 (5 m, rotated) pair, single level | 6.8 s (E2E run, includes UI) |
| Same pair, full cascade enabled (stops at level 1 once the gate passes) | 4.9 s |
| Engine self-test (1200×1200 synthetic, native 4/10-level SIFT) in WASM | ≈ 5.2–5.5 s (native: < 1 s) |
| Inspect + decimated preview of a **3.2 GB** sparse PDS4 product (40,000 × 40,000 uint16) | inspect 0.1 s; preview 2.0 s |
| Main-thread JS heap after the large-file test | ≈ 10 MB (rasters live only in the worker, read in slices) |

No peak-WASM-memory measurement is available from the browser API used; do not infer one. No real Chandrayaan-2 workloads were run, so **real-product timings are unknown**.

## What bounds memory

| Component | Bound |
|---|---|
| Raster reads | requested window only (row block or per-row segments) |
| Tiles | tile_px² × float32 × a few buffers (≤768² selectable) |
| Common grid | `max_grid_pixels` (4 M / 12 M / 24 M by preset); GSD is coarsened beyond it and the run reports `grid_capped` |
| Geometry CSV | refused above 64 / 256 / 512 MB by preset |
| Previews/evidence canvases | 512–1024 px preview, 1000–1800 px evidence canvas |
| Wasm heap | browser-dependent, ~2–4 GB ceiling |

When a limit is hit the product is flagged (`geometry_too_large`) or the grid is coarsened and reported; if the tab nevertheless runs out of memory the worker crash handler shows an actionable message and restarts the engine.

## Not done
Profiling on real swaths, multi-worker parallel tiling, WebGPU (no benefit available inside OpenCV-WASM), peak-memory instrumentation. These are listed as future work.
