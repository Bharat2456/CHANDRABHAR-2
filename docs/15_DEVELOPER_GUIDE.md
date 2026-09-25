# 15 — Developer Guide

## Setting up

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt -r requirements-dev.txt
python -m pytest -q
```

## Project layout

See [`docs/03_SYSTEM_ARCHITECTURE.md`](03_SYSTEM_ARCHITECTURE.md) for the full component map.

## Adding a new adapter (new product format)

Adapters live in `app/adapters/`. Each implements two entry points against a `Path`:
- `can_open(path)` — cheap check (extension/signature) that this adapter should handle the file.
- `inspect(path)` — parse the label/metadata and return a canonical `SceneSpec` (sensor,
  product_id, array, gsd_m, solar_elevation_deg, solar_azimuth_deg, acquisition_start, metadata
  dict including `geometry_csv` path if available).

Register the new adapter with `AdapterRegistry` (see `app/adapters/__init__.py`) so
`AdapterRegistry.inspect()` can dispatch to it automatically. Existing adapters to use as a
template: `pds4.py` (PDS4 XML label), `envi.py` (ENVI `.hdr`), `raw_sidecar.py` (raw binary +
JSON/text sidecar), `numpy_adapter.py` (`.npy`).

## Modifying the scientific core

**Do not modify `app/core/*.py` casually.** Any change that affects matching behavior,
thresholds, or reported metrics must be:
1. Documented in [`CHANGELOG.md`](../CHANGELOG.md) as a scientific-behavior change, not a
   UI-only change.
2. Covered by a test in `tests/` (see below).
3. Re-validated against the self-test (`python run.py`) and, ideally, real data before being
   described as working in any documentation.

UI-only changes (dashboard styling, layout, copy, documentation, branding) do not require this
process, but should still not alter what values are computed or displayed.

## Tests

```powershell
python -m pytest -q       # 18 tests as of this delivery
python run.py              # synthetic end-to-end self-test
python -m app.cli.main self-test   # same self-test via the CLI
```

See `tests/` for the current suite and
[`docs/TEST_AND_VALIDATION_REPORT.md`](TEST_AND_VALIDATION_REPORT.md) for what each test
actually covers.

## Release checklist

`release_validate.py` runs pytest + the self-test + a checklist of required files and writes
`RELEASE_VALIDATION.json`:

```powershell
python release_validate.py
```

## Coding conventions

The existing codebase favors compact, dependency-light, CPU-first Python (no async, no ORM, no
web framework beyond Streamlit for the UI). New code should match this style rather than
introducing new frameworks — see [`docs/18_LIMITATIONS_AND_FUTURE_WORK.md`](18_LIMITATIONS_AND_FUTURE_WORK.md)
for the project's explicit "do not overengineer" stance.

## Dashboard development

`dashboard.py` is a single-file Streamlit app. The four tabs are independent render functions
called from `main()`; state is persisted to `CHANDRABHAR-2_Platform_Outputs/workflow_state.json`
so Mission Overview can reflect the latest completed run without re-executing anything. Styling
tokens are defined once at the top of the file (`:root { --lm-* }`, matching
[`branding/color_palette.md`](../branding/color_palette.md)) — change the CSS variables there
rather than hardcoding colors in individual `st.markdown` calls.
