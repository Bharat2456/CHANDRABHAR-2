# 16 — Troubleshooting

The dashboard presents errors in three layers: **what happened**, **why it may have happened**,
**what you can do** — with full technical detail (Python traceback) available behind an
expandable diagnostics section rather than shown inline by default.

## Common issues

### "No products found" when scanning a mission folder
- Confirm the folder actually contains files matching the `ch2_ohr`, `ch2_tmc`, or `ch2_iir`
  naming pattern with an `.xml` (PDS4) or `.hdr` (ENVI) label.
- Confirm you pointed the dashboard at the parent folder, not a specific product file.

### `geometry_csv` missing / geometry audit reports `geometry_ok: false`
- The product's label did not reference a geometry table, or the referenced file was not found
  next to it. Without it, footprint intersection falls back to whatever bounding information is
  available in the label, if any — see [`docs/07_GEOMETRIC_MODEL.md`](07_GEOMETRIC_MODEL.md).

### A pair always reports `INSUFFICIENT_EVIDENCE`
- This is a valid scientific result, not necessarily a bug. See
  [`docs/12_RESULTS_INTERPRETATION.md`](12_RESULTS_INTERPRETATION.md) for how to read the
  specific `reasons` and what they imply.
- Confirm the two products actually have real geographic overlap (`geometry-audit` command).

### `pytest` fails after a local code change
- Run `python -m pytest -q -x` to stop at the first failure and read the traceback.
- If the failure is in `tests/test_evidence.py` or similar scientific-core tests, do not adjust
  the test to make it pass — see [`docs/15_DEVELOPER_GUIDE.md`](15_DEVELOPER_GUIDE.md)'s policy
  on modifying the scientific core.

### `ModuleNotFoundError` (e.g. `shapely`, `scipy`)
- Re-run `python -m pip install -r requirements.txt`. These are direct requirements, not
  optional, in this codebase.

### Streamlit shows a blank page / widget-state error
- Stop the process, clear `.streamlit/` cache if present, and relaunch. This platform version
  has already been checked for `use_container_width` and legacy widget-state incompatibilities
  (see [`CHANGELOG.md`](../CHANGELOG.md) and `docs/history/PATCH_NOTES_PLATFORM_1_3_1.md`).

### The app is slow on a large product
- This is expected for a CPU-first, memory-conscious design — see
  [`docs/18_LIMITATIONS_AND_FUTURE_WORK.md`](18_LIMITATIONS_AND_FUTURE_WORK.md). Large products
  are memory-mapped and tiled rather than fully loaded into RAM.

## Where to look next

- [`docs/12_RESULTS_INTERPRETATION.md`](12_RESULTS_INTERPRETATION.md) for reading a result.
- [`docs/17_REPRODUCIBILITY.md`](17_REPRODUCIBILITY.md) for environment-related issues.
- `docs/history/` for prior patch notes that may already describe a fix for an issue you're
  seeing.
