# 17 — Reproducibility

## Target environment (as designed)

- **OS:** Windows 10/11 (primary target; the launch scripts are `.bat`/`.ps1`). Linux/macOS work
  with the equivalent `python -m ...` commands.
- **Python:** 3.10 or newer, 64-bit.
- **Hardware:** CPU-only laptop-class hardware. No GPU required or used. See
  [`docs/18_LIMITATIONS_AND_FUTURE_WORK.md`](18_LIMITATIONS_AND_FUTURE_WORK.md) for the memory
  assumptions behind the tiling design.

## Environment this delivery was actually verified in

For this productization pass, compilation, the unit-test suite, and the synthetic self-test were
run and verified in a **Linux, Python 3.12.3** sandbox (as a cross-platform sanity check, since
the primary Windows target could not be exercised in this environment) — see
[`docs/TEST_AND_VALIDATION_REPORT.md`](TEST_AND_VALIDATION_REPORT.md) for the exact results.
This does not replace verification on the primary Windows/Python 3.10 target, which should still
be done before a live demo.

## Dependencies

Exact version ranges: `requirements.txt`, `requirements-optional.txt`, `requirements-dev.txt`.
Full third-party list with the versions actually resolved during this verification pass:
[`LEGAL/THIRD_PARTY_NOTICES.md`](../LEGAL/THIRD_PARTY_NOTICES.md).

## Configuration

Sensor-pair product-ID mapping used by `python -m app.cli.main mission` and `geometry-audit` is
defined inline in `app/cli/main.py` (see that file) and in `configs/chandrayaan2_real.json`.
Update these to point at your own downloaded product filenames.

## Reproducing an experiment

1. Record the exact product IDs used (shown in Mission Overview / `inspect` command output).
2. Record the code version: engine `VERSION.txt`, platform `PLATFORM_VERSION.txt`, and — if
   using git — the commit hash.
3. Run `python -m app.cli.main mission --root <path> --out outputs\mission_validation`.
4. The output `summary.json`, per-pair JSON files, and `pair_summary.csv` together with the
   recorded product IDs and code version are sufficient for a second researcher to reproduce the
   same experiment against the same source products.

## Reproducing the test/self-test results in this document set

```powershell
python -m pytest -q
python run.py
python release_validate.py
```

`release_validate.py` regenerates `RELEASE_VALIDATION.json` with the current pytest/self-test
output and a required-file checklist.
