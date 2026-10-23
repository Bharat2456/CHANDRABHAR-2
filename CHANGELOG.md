# Changelog

This project's identity was renamed from **LunaMatch** to **CHANDRABHAR-2**. This changelog
preserves that provenance rather than erasing it — full original patch notes for every prior
release are kept at [`docs/history/`](docs/history/).

Two version lines exist and are tracked separately, exactly as they were before the rename:

- **Engine version** (`VERSION.txt`) — the scientific core (`app/core`, `app/geo`,
  `app/adapters`). Unchanged by the CHANDRABHAR-2 productization pass.
- **Platform version** (`PLATFORM_VERSION.txt`) — the dashboard/UI/docs/packaging layer.


## Platform 3.0.0-web / Engine 8.1.0 — browser-native release

**Platform.** CHANDRABHAR-2 now runs entirely in the browser (React + TypeScript SPA; the Python engine executes in a Web Worker as WebAssembly via Pyodide 0.29.5) and deploys from GitHub to Vercel as a static site. No backend, accounts or telemetry. The Streamlit app (`dashboard.py`, `ui/`) is retained unchanged as the local reference UI.

**Engine 8.1.0 (scientific core).**
- **Fixed (correctness):** the `.npy` adapter memory-mapped the file at offset 0, so the NumPy header bytes were read as pixel data (images were shifted by the header length). It now parses the header, uses the true data offset, validates size, and rejects Fortran-order/object arrays. Regression test: `tests/test_security_and_adapters.py::test_npy_regression_pixels_exact`. PDS4/ENVI/raw adapters were not affected.
- **Changed (self-test):** `app/selftest.py` now verifies the recovered transform against the known synthetic transform (≤ 1.5 px) instead of the gate inlier-ratio, which was only reaching its threshold because both test images were identically corrupted by the bug above. Evidence-gate thresholds are **unchanged**.
- **Added:** `app/safepath.py` (label-supplied names must be plain names inside the workspace; DTD/entity XML refused; size limits), size validation for raw/sidecar and `.npy`, `LazyArray` stream backend (bit-exact with memmap; required in the browser), host-side 64-bit slice reads (Python `seek` is 32-bit in wasm32), `app/core/hooks.py` (progress / evidence capture; no effect on results), `Engine.config()` recorded in every result, deterministic RANSAC seeding, inlier masks on `MatchResult`, `GATE_THRESHOLDS` as the single source of truth, `app/web/bridge.py`, `app/synthetic.py`.
- **Not changed:** matching cascade, representations, geowarp, geometry mapper, gate thresholds and their semantics.

See `docs/WEB_MIGRATION_PARITY.md` and `docs/WEB_TEST_REPORT.md`.

## Platform v2.1.0 — Lunar Intelligence Interface (UI/UX redesign)

Presentation layer only. **`app/` is byte-identical to v2.0.0; engine remains v8.0.2.**

### Changed
- `dashboard.py` is now a thin shell; UI split into `ui/` (tokens, theme, components, logic, pages, runner).
- Five pages via `st.navigation`: Mission Overview, Data Workspace, Image Registration, Evidence & Results, Reports & Export.
- Complete dark (Orbital Night) and light (Lunar Daylight) themes (`.streamlit/config.toml` + `ui/tokens.py`).
- Evidence shown as four separate claims; green is used only for a passed evidence gate.
- Removed the hard-coded "Problem-statement coverage" ✅ list (it did not reflect the result).
- Unreadable product labels are now listed with their error instead of silently skipped.
- Rescan asks for confirmation before resetting a recorded completed run's workflow state.
- Pre-run selection validation and plain-language error guidance (raw exception still shown).

### Added
- `tests/test_ui_logic.py`, `tools/ui_preview.py`, `docs/UI_DESIGN_SYSTEM.md`.

## Platform v2.0.0-chandrabhar2 — CHANDRABHAR-2 rebrand (this delivery)

Presentation, documentation, and packaging release. **No scientific-core file under `app/core`,
`app/geo`, or `app/adapters` was modified** — engine version remains v8.0.2.

### Changed (UI / branding only)
- Product renamed **LunaMatch → CHANDRABHAR-2** throughout the dashboard, README, CLI log
  prefixes, launch scripts, and output folder naming
  (`LunaMatch_Platform_Outputs` → `CHANDRABHAR-2_Platform_Outputs`).
- New color palette and CSS tokens derived from the official CHANDRABHAR-2 logo (see
  `branding/color_palette.md`); dashboard hero banner, status pills, and the evidence-visualization
  renderer (`evidence_image()` in `dashboard.py`) recolored to match.
- Launch scripts renamed and rewritten: `RUN_PLATFORM.bat` → `RUN_CHANDRABHAR-2.bat`,
  `run_platform.ps1` → `run_chandrabhar2.ps1`.
- `run.py` self-test banner and `app/cli/main.py` log prefixes updated from `[LunaMatch]` to
  `[CHANDRABHAR-2]`.

### Added
- Full 18-document `docs/` suite (`01_PROJECT_OVERVIEW.md` through
  `18_LIMITATIONS_AND_FUTURE_WORK.md`), plus `TECHNICAL_DESIGN_REPORT.md`,
  `TECHNICAL_DEMONSTRATION_REPORT.md`, `TECHNICAL_EXPERIMENT_REPORT.md`,
  `SOFTWARE_REQUIREMENTS_SPECIFICATION.md`, `TEST_AND_VALIDATION_REPORT.md`.
- `docs/assets/diagrams/` (Mermaid architecture, component, data-flow, experiment-workflow, and
  UI-workflow diagrams) and `docs/assets/screenshots/` (a real evidence image generated from the
  software's own synthetic self-test, honestly labeled as synthetic; real dashboard-tab
  screenshots left as a documented gap — see that folder's README).
- `LEGAL/` folder: `LICENSE.md` (status placeholder requiring author confirmation),
  `THIRD_PARTY_NOTICES.md`, `DATA_LICENSE_AND_USAGE.md`, `ISRO_DATA_ATTRIBUTION.md`,
  `SOFTWARE_DISCLAIMER.md`, `COPYRIGHT_NOTICE.md`, `CONTRIBUTING.md`.
- `SIH/` folder: project summary, technical approach, innovation points, demo script, evaluator
  guide, and an explicit limitations/next-steps document.
- `branding/` folder: logo assets (including a chroma-keyed transparent version and
  favicon/app-icon crops), `color_palette.md`, `typography.md`, `brand_guidelines.md`.
- New README rewritten to the full structure requested for this rebrand (problem statement,
  architecture, install, experiment workflow, validation status, licensing, disclaimer,
  citation).

### Preserved unchanged (scientific core)
- `app/core/pipeline.py`, `app/core/evidence.py`, `app/core/physical.py`,
  `app/core/representation.py`, `app/core/geowarp.py`, `app/core/matcher.py`,
  `app/core/tiles.py`, `app/geo/mapper.py`, all `app/adapters/*.py`.
- All 18 tests in `tests/` unchanged and still passing (18/18).
- The evidence-gate thresholds in `app/core/evidence.py` are byte-for-byte unchanged.

---

## Prior history (original "LunaMatch" identity)

Full original patch notes preserved at [`docs/history/`](docs/history/). Summary:

| Version | Summary |
|---|---|
| Platform 1.3.1 | Most recent pre-rebrand platform release (baseline for this delivery) |
| Platform 1.2.0 | Evidence & Metrics became an active verification workspace rather than a placeholder |
| Platform 1.1.1 | Fixed a Streamlit session-state ownership error; added a root `dashboard.py` launcher |
| Platform 1.1.0 | Interactive demo completion release around the (then-current) v8.0.2 engine; explicitly noted no change to scientific validation claims |
| Platform 1.0.1 | Early platform fix release |
| Engine 8.0.2 | **Evidence Integrity Patch** — phase-correlation dense-grid points explicitly marked model-generated/non-independent; global tiled RANSAC no longer pools phase/ECC model-generated points as independent correspondence evidence |
| Engine 8.0.1 | Fixed an OpenCV `cv2.remap` hard dimension limit for large native source windows |
| Engine 8.0 | Correspondence upgrade |
| Engine 7.0.6 | IIRS tile-window and mission-run resilience fix |
| Engine 7.0.5 | True swath geometry release |
| Engine 7.0.4 | Geometry correctness release |
| Engine 7.0.3 | Geographic AOI correctness patch — pair-specific AOI derived from true footprint intersection |
| Engine 7.0.2 | Real-mission IIRS performance correction |
| Engine 7.0.1 | Hotfix |

See [`docs/history/CHANGELOG_V7.md`](docs/history/CHANGELOG_V7.md) and
[`docs/history/RELEASE_NOTES.md`](docs/history/RELEASE_NOTES.md) for further detail on the v7
architecture transition, and [`docs/history/ADAPTER_SDK.md`](docs/history/ADAPTER_SDK.md) for the
original adapter-extension guide (superseded by
[`docs/15_DEVELOPER_GUIDE.md`](docs/15_DEVELOPER_GUIDE.md), which covers the same mechanism under
the current name).
