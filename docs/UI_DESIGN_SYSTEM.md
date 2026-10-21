# CHANDRABHAR-2 | Lunar Intelligence Interface — UI design system

Presentation-only layer. `app/` (the scientific engine, v8.0.2) is untouched.

## Layout of the UI code
| Path | Role |
|---|---|
| `dashboard.py` | Thin shell: page config, sidebar workspace, mission header, `st.navigation` |
| `ui/tokens.py` | **Design tokens** — dark (Orbital Night) and light (Lunar Daylight) palettes, fonts |
| `ui/theme.py` | CSS generated from tokens, active-theme detection, embedded logo |
| `ui/components.py` | Reusable components (`*_html` are pure; thin `st` wrappers) |
| `ui/logic.py` | Pure logic: formatting, evidence-claim classification, pre-run validation, error wording |
| `ui/pages.py` | Overview, Data Workspace, Image Registration, Evidence & Results, Reports & Export |
| `ui/runner.py` | Pair execution + persisted state (flow unchanged; calls `Engine.register`) |
| `ui/evidence_image.py` | Evidence PNG renderer, moved verbatim from the old dashboard |
| `.streamlit/config.toml` | Native-widget theme for both modes (kept in sync with tokens by a test) |
| `tools/ui_preview.py` | Static design preview of both themes (synthetic fixture only) |

## Themes
Streamlit applies `[theme.dark]` / `[theme.light]` from `.streamlit/config.toml` to native widgets and follows the OS
by default. Switch via **⋮ ▸ Settings ▸ Theme** (Dark / Light / System); the choice is persisted by Streamlit in the
browser. Custom components read the active theme through `st.context.theme` and use CSS variables (`--cb-*`).
Limitation: Streamlit cannot restyle its native widgets from an in-app custom switch without brittle DOM selectors,
so the built-in switcher is used deliberately. To change a colour, edit `ui/tokens.py` **and** `.streamlit/config.toml`
(`tests/test_ui_logic.py` fails if they drift or if contrast drops below 4.5:1).

## Evidence language (never conflated)
1. *Processing completed* — the engine returned (blue, informational).
2. *Transformation estimated* — a homography exists (blue / amber).
3. *Evidence gate* — Passed (green, only when status is `VALIDATED`) or Insufficient evidence (amber), with reasons.
4. *Independent ground-truth validation* — always **Not established**; this software never produces it.

## Run / test
```
python -m streamlit run dashboard.py
python tools/ui_preview.py ui_preview_out --shots     # needs playwright; optional
python -m pytest tests                                 # includes tests/test_ui_logic.py
```
