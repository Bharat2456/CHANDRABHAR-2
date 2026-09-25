# Changelog

This project's identity was renamed from **LunaMatch** to **CHANDRABHAR-2**. This changelog
preserves that provenance rather than erasing it — full original patch notes for every prior
release are kept at [`docs/history/`](docs/history/).

Two version lines exist and are tracked separately, exactly as they were before the rename:

- **Engine version** (`VERSION.txt`) — the scientific core (`app/core`, `app/geo`,
  `app/adapters`). Unchanged by the CHANDRABHAR-2 productization pass.
- **Platform version** (`PLATFORM_VERSION.txt`) — the dashboard/UI/docs/packaging layer.

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
