# 14 — User Guide

## Before you start

You need a local folder of Chandrayaan-2 products (OHRC/TMC-2/IIRS label + binary files) on this
computer. CHANDRABHAR-2 never uploads them anywhere — everything runs locally.

## 1. Launch

```powershell
RUN_CHANDRABHAR-2.bat
```

The dashboard opens at `http://localhost:8501` with four tabs: **Mission Overview**,
**Correspondence Lab**, **Evidence & Metrics**, **Products & Export**.

## 2. Mission Overview

Enter (or browse to) your mission-data folder path and scan it. This page shows, for each
product actually discovered: sensor, product ID, native GSD, sun-angle metadata (if present in
the label), acquisition timestamp, and — once you've run something — the status of the most
recently completed experiment. This page is read-only: it never triggers computation itself.

## 3. Correspondence Lab — where you actually run something

1. Select a sensor pair (or "run all three pairs").
2. Review the two products' metadata side by side before running.
3. Start the run. A live workflow panel shows the current phase (**Prepare & Align → Normalize &
   Represent → Match & Verify**) and sub-stage, with one of `WAITING / RUNNING / COMPLETE /
   FAILED / INSUFFICIENT EVIDENCE` per stage — a checkmark only appears once a stage has actually
   finished.
4. The terminal (if you launched via PowerShell/cmd rather than double-clicking the `.bat`) prints
   concise real progress lines as the CLI/engine executes, e.g. tile counts and candidate/inlier
   counts as they are computed — never a fabricated percentage.

## 4. Evidence & Metrics

Reads back the result(s) produced in Correspondence Lab (it does not compute anything itself).
Shows match/inlier counts, inlier ratio, RMSE (px and m), spatial coverage, the physical GSD
actually used, evidence-gate status and reasons, and the correspondence visualization with
inliers/outliers distinguished. See [`docs/12_RESULTS_INTERPRETATION.md`](12_RESULTS_INTERPRETATION.md)
for how to read these numbers.

## 5. Products & Export

Lists the actual output files produced (JSON results, `pair_summary.csv`, PNG evidence images,
`workflow_state.json`) with timestamps and sizes, and lets you download them. No files are listed
here that were not actually produced by a run — this page does not fabricate placeholder
downloads.

## Understanding the technical terms

| Term | Meaning |
|---|---|
| GSD | Ground Sample Distance — the real-world size, in meters, that one pixel covers |
| OHRC / TMC-2 / IIRS | Chandrayaan-2's three imaging payloads — see [`docs/04_DATA_AND_SENSORS.md`](04_DATA_AND_SENSORS.md) |
| Multimodal | Matching across sensors that image the scene differently (panchromatic vs. hyperspectral) |
| Illumination-aware | Representation designed to be less sensitive to sun-angle differences between passes |
| RANSAC | An algorithm that fits a geometric model while ignoring inconsistent outlier points |
| Inlier | A correspondence RANSAC judged consistent with the fitted geometric model |
| RMSE | Root-mean-square residual error of the fitted model against the inliers |
| Evidence gate | The fixed set of thresholds a result must clear to be reported `VALIDATED` |
| Common lunar grid | The shared geographic grid, at a chosen physical GSD, both products are warped onto before matching |

## If something fails

See [`docs/16_TROUBLESHOOTING.md`](16_TROUBLESHOOTING.md).
