# Known limitations and future work

**Scientific**
* No independent ground-truth validation exists in this project or was added. A passed gate is internal consistency only (an image trivially matches its own copy — see `test_documented_limit_identical_copy_passes_gate`).
* Real Chandrayaan-2 products were **not available** for this delivery. All end-to-end results here use synthetic fixtures (`app/synthetic.py`), including the browser tests. Real-product behaviour (label variants, geometry tables, huge OHRC swaths, IIRS spectral cubes) is untested.
* IIRS/OHRC with extreme GSD ratios (≈360×) are supported by design (common grid at the coarser GSD) but unverified in the browser.
* Result quality depends on the accuracy of supplied geometry tables.

**Engineering**
* Compiled code is single-threaded in WebAssembly; expect several-fold slowdown vs native. Multi-worker tiling is future work.
* Cancel = restart the engine (no resumable runs).
* WebAssembly memory is bounded (~2–4 GB). Very large swaths are processed by tiling, but the common grid is capped by the memory preset.
* The engine runtime download is ≈43 MB on first visit (then cached).
* Only Chromium (headless) was tested. Firefox/Safari/mobile are unverified.
* The Lab displays a normalised common-grid representation, not raw detector counts, and shows at most 30,000 correspondences.
* Hash routing (`#/…`) is used for deployment robustness.
* No Vercel deployment was performed by the author; no public URL is claimed.
* The repository's proprietary licence conflicts with publishing downloadable engine source — owner decision required.

**Future work:** held-out evaluation set and learned-matcher baseline; coarse-to-fine initialisation; parallel workers; real-data validation protocol under `docs/11_EXPERIMENT_PROTOCOL.md`; Firefox/Safari CI; resumable runs.
