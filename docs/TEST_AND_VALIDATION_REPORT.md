# CHANDRABHAR-2 — Test and Validation Report

## Software correctness vs. scientific validation

This report deliberately separates two different claims:

- **Software correctness** (this report, in full): does the code run correctly, do the unit
  tests pass, does the self-test recover a known synthetic transform?
- **Scientific validation** (not claimed complete by this report): does a real Chandrayaan-2
  sensor pair clear the evidence gate? See
  [`docs/10_VALIDATION_AND_EVIDENCE.md`](10_VALIDATION_AND_EVIDENCE.md) and
  [`docs/CLAIMS_MATRIX.md`](CLAIMS_MATRIX.md). **Passing every test in this report does not
  itself constitute scientific validation.**

## Unit / integration tests

Run: `python -m pytest -q`, in a Linux/Python 3.12.3 sandbox (see
[`docs/17_REPRODUCIBILITY.md`](17_REPRODUCIBILITY.md) for the environment note relative to the
primary Windows/Python 3.10 target).

**Result: 18 passed, 0 failed.**

| Test file | Tests | What it covers |
|---|---|---|
| `test_adapters.py` | `test_numpy` | NumPy adapter can inspect a `.npy` product |
| `test_geometry_isro.py` | `test_isro_grd_columns_and_intersection` | ISRO GRD geometry column parsing and footprint intersection |
| `test_geowarp.py` | `test_geographic_warp_aligns_two_sensors`, `test_iirs_geowarp_spectral_representation`, `test_safe_remap_handles_oversized_native_source` | Common-grid geographic warp correctness, IIRS spectral representation, safe handling of oversized native sources |
| `test_matcher.py` | `test_ecc_dense_fallback_never_validates_without_independent_matches`, `test_phase_dense_fallback_never_counts_as_independent_validation` | **Explicit regression tests that dense/fallback matcher stages cannot produce a false `VALIDATED` without genuine independent correspondence evidence** — i.e. the no-fabrication rule is unit-tested, not just documented |
| `test_physical.py` | `test_plan` | `plan_common_gsd()` cascade correctness |
| `test_pipeline_boundary.py` | 5 tests | Physical-overview tile boundary handling, GSD preservation on large/tiled paths, IIRS tile-bounded representation, parent-offset handling, empty-window edge case |
| `test_representation.py` | `test_rep` | Representation stage (`robust_norm`/`structural`/`illumination_invariant`/`modality_rep`) |
| `test_tiles.py` | 4 tests | Tiling geometry, geometry-mapper AOI sample handling, pair-AOI footprint-intersection requirement, `register()` using pair-footprint AOI |

The two `test_matcher.py` tests are worth calling out specifically: they exist to guarantee, at
the unit-test level, that a fallback matching stage (dense/phase-correlation) cannot be
misinterpreted by the pipeline as independent evidence strong enough to validate a result — this
is the automated test-level enforcement of the "no fabricated validation" rule in
[`docs/05_SCIENTIFIC_METHOD.md`](05_SCIENTIFIC_METHOD.md).

## Self-test (synthetic, known-answer regression)

Run: `python run.py`.

```
CHANDRABHAR-2 ENGINE SELF-TEST PASSED
{'passed': True, 'inliers': 327, 'ratio': 0.3605, 'coverage': 0.9375, 'rmse_px': 0.7986}
```

This end-to-end run applies a known 4° rotation + (12,−9) px translation to a synthetic scene and
confirms the full pipeline (adapters → geometry → GSD planning → representation → matcher →
RANSAC → evidence gate) recovers it above the gate's thresholds. See
[`docs/TECHNICAL_DEMONSTRATION_REPORT.md`](TECHNICAL_DEMONSTRATION_REPORT.md) for full detail and
the corresponding evidence image.

## Release validation

`release_validate.py` re-runs pytest + the self-test and checks for the presence of required
files (`README.md`, `VERSION.txt`, `app/core/pipeline.py`, `app/io/reader.py`,
`app/adapters/pds4.py`), writing the result to `RELEASE_VALIDATION.json`. Run as part of this
delivery; see that file for the current output.

## Expected vs. actual results

| Check | Expected | Actual (this delivery) |
|---|---|---|
| `pytest -q` | All tests pass | 18/18 passed |
| `python run.py` | Synthetic self-test passes its own gate | Passed (VALIDATED, see numbers above) |
| `python -m py_compile` on edited files | No syntax errors | Clean |
| Dashboard imports | No import errors | `dashboard.py` compiles cleanly; not launched with a live browser in this environment (see `docs/assets/screenshots/README.md`) |

## Reproducibility instructions

```powershell
python -m pip install -r requirements.txt -r requirements-dev.txt
python -m pytest -q
python run.py
python release_validate.py
```

## Known limitations of this test suite

- No test in this suite runs against real Chandrayaan-2 products — all are synthetic/unit-level.
  A real-data integration test (skipped by default, opt-in via a local data path) would be a
  reasonable future addition — see
  [`docs/18_LIMITATIONS_AND_FUTURE_WORK.md`](18_LIMITATIONS_AND_FUTURE_WORK.md).
- Coverage of the CLI (`app/cli/main.py`) commands themselves (as opposed to the underlying
  `app.core`/`app.geo`/`app.adapters` functions they call) is exercised manually in this report
  (`python run.py`, `pytest`) rather than via a dedicated CLI test file.
