# Using CHANDRABHAR-2 in the browser

No installation, account or terminal. Open the site in a current desktop browser (a large screen is best for image inspection).

1. **Mission Overview** – orientation, workspace status, recent results. *Try the synthetic demo* runs the whole pipeline on generated imagery with known geometry. It is **not mission data**.
2. **Data Workspace** – drag files or a whole archive folder onto the drop area, or use *Select files* / *Select folder*. Nothing is uploaded. For each product select the label **and** its binary, and ideally the geometry CSV (picking the archive folder does this automatically). You will see: file types and instant warnings (missing companion, unsafe/empty file), then — once the engine has loaded (≈43 MB, downloaded once and cached) — the authoritative inspection: sensor, size, GSD, data type, geometry, warnings, metadata, and an optional decimated preview. If a GSD or sensor is missing you can supply it; overrides are recorded in the manifest.
3. **Image Registration** – choose reference (fixed frame) and source. The compatibility panel shows GSD ratio, the overlap method (true swath intersection vs. fallback) and overlap area. Parameters: scale cascade, tile size, overlap, SIFT ratio, RANSAC seed. Evidence-gate thresholds are shown but fixed. *Run registration* shows live stage, level and tile progress. *Cancel run* terminates and restarts the engine (a few seconds); your files stay selected.
4. **Correspondence Lab** – side-by-side or overlay views of the common grid with synchronised pan/zoom (drag, wheel, pinch, arrow keys, `+`/`−`/`0`). Rings are RANSAC inliers, crosses outliers; the overlay can show *before* vs *after* alignment. A residual histogram and transform summary sit alongside.
5. **Evidence & Results** – four **separate** statements: processing completed · transformation estimated · evidence gate passed/not passed · ground-truth validation (always *not established*). Gate criteria with measured values and thresholds, reasons for failure, transformation diagnostics, the scale cascade, which matcher paths actually ran and any warnings.
6. **Reports & Export** – metrics JSON, summary CSV, correspondences CSV, evidence PNG, run manifest JSON, or everything as a ZIP. Files are generated locally and saved to your device.
7. **Settings & About** – theme, motion, memory preset, opt-in local saving, *Clear all local data*, browser capability table, engine self-test, supported formats, limitations, privacy.

## Interpreting results

* **Gate passed** means: enough tentative matches, ≥ 12 inliers, inlier ratio ≥ 35 %, ≥ 35 % of the 4×4 spatial grid covered, RMSE ≤ 2.5 px. It means the correspondences are geometrically self-consistent. It does **not** mean the registration is correct in absolute terms.
* **Not passed / insufficient evidence** is a legitimate outcome (low texture, small overlap, strong modality gap, poor geometry).
* RMSE is in common-grid pixels; the metre equivalent is shown (1 px = common-grid GSD).
* On a geographically warped grid, a faithful transform is near the identity; large rotation/scale/perspective values are flagged.
* A common-grid GSD larger than requested means the memory preset capped the grid (`grid_capped` warning).

## Troubleshooting

| Symptom | Cause / action |
|---|---|
| "Engine could not start" | Browser lacks Workers/WebAssembly, or the download was blocked. Reload; try a current Chrome/Edge/Firefox/Safari. |
| "Binary size does not match the label" | Truncated or wrong data file. Re-copy it. |
| "Companion file missing" | Select the binary referenced by the label together with it. |
| No true swath intersection | Geometry CSV not selected, or footprints do not overlap. |
| Run fails / tab crashes | Use *Conservative* memory preset, a single-level cascade or 256 px tiles. |
| Very slow | WebAssembly is single-threaded and slower than native; try fewer levels. |
