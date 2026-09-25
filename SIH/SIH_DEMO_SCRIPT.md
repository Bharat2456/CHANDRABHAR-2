# SIH Demo Script — CHANDRABHAR-2

Target length: ~5–7 minutes. Matches the evaluator's expected path in
[`SIH_EVALUATOR_GUIDE.md`](SIH_EVALUATOR_GUIDE.md).

## 1. Introduce the problem (30–45 s)
"Chandrayaan-2 has three cameras that see the Moon completely differently — one at 0.3 meters per
pixel, one at 5 meters, one at 80 meters and in color-like spectral bands instead of plain
brightness. Relating a point in one to a point in another isn't a simple image-matching problem."

## 2. Show mission data (30 s)
Open **Mission Overview**, scan a mission-data folder, point out the three discovered products
and their real metadata (GSD, sun angle, acquisition time) — emphasize these values come straight
from the product's own label, nothing is invented.

## 3. Show the three sensors and scale difference (30–45 s)
Point at the GSD figures side by side: ~0.3 m vs ~5 m vs ~80 m. Make the ~270x OHRC-to-IIRS scale
gap concrete ("one IIRS pixel covers roughly the same ground as tens of thousands of OHRC
pixels").

## 4. Run correspondence (30 s)
Switch to **Correspondence Lab**, pick a pair, hit run.

## 5. Show live processing (45–60 s)
Narrate the phases as they appear: Prepare & Align → Normalize & Represent → Match & Verify.
Point out that nothing shows a checkmark before it's actually done, and that the terminal (if
visible) is printing real progress, not a fake percentage.

## 6. Show visual evidence (30–45 s)
Once complete, open **Evidence & Metrics**. Show the correspondence visualization — green lines
are RANSAC inliers — and explain it's rendered directly from the returned correspondence
coordinates, not a stock image.

## 7. Show scientific metrics (30–45 s)
Point at inlier count, inlier ratio, coverage, RMSE (px and m). Explain each briefly using the
tooltips/help text already in the UI.

## 8. Show the evidence gate (30–45 s)
Show the `VALIDATED` or `INSUFFICIENT_EVIDENCE` badge and explain the five thresholds behind it
(`../docs/10_VALIDATION_AND_EVIDENCE.md`). If the demo pair is `INSUFFICIENT_EVIDENCE`, treat this
as a feature to explain, not a failure to hide: "the system just told us honestly that this
particular pair didn't clear the bar, and told us why."

## 9. Show exports (20–30 s)
Open **Products & Export**, show the JSON/CSV/PNG package and download one.

## 10. Explain limitations honestly (30–45 s)
"This prototype has not yet been run through a full real-data validation campaign across all
three sensor pairs — that's the next step, not a finished claim. Everything you saw run today was
real code, real geometry, real thresholds — but 'the pipeline works' and 'we've validated
Chandrayaan-2 correspondence' are two different claims, and we're only making the first one right
now." See [`../docs/CLAIMS_MATRIX.md`](../docs/CLAIMS_MATRIX.md).

## 11. Explain future research direction (20–30 s)
Real three-pair validation campaign; a coarse-to-fine search specifically for the OHRC↔IIRS scale
gap; optional GPU acceleration kept strictly opt-in. See
[`../docs/18_LIMITATIONS_AND_FUTURE_WORK.md`](../docs/18_LIMITATIONS_AND_FUTURE_WORK.md).

## Closing line
"CHANDRABHAR-2 is not claiming to have solved Chandrayaan-2 correspondence — it's a disciplined,
inspectable attempt at it, built to be honest about exactly where it stands."
