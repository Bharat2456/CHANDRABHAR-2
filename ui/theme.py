"""Stylesheet generation and theme resolution (CSS variables from tokens)."""
from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path

from ui.tokens import FONT_MONO, FONT_SANS, palette

ROOT = Path(__file__).resolve().parent.parent


def active_theme(default: str = "dark") -> str:
    """Return 'dark' or 'light' for the theme Streamlit is currently using."""
    try:
        import streamlit as st

        t = getattr(st.context, "theme", None)
        kind = getattr(t, "type", None) if t is not None else None
        if kind in ("dark", "light"):
            return kind
    except Exception:
        pass
    return default


def build_css(theme: str) -> str:
    p = palette(theme)
    var = "\n".join(f"  --cb-{k.replace('_', '-')}: {v};" for k, v in p.items())
    return f"""
:root {{
{var}
  --cb-font-sans: {FONT_SANS};
  --cb-font-mono: {FONT_MONO};
  --cb-radius: 4px;
}}
.block-container {{ padding-top: 1.1rem; max-width: 1560px; }}
[data-testid="stSidebar"] {{ border-right: 1px solid var(--cb-border); }}
.cb-mono {{ font-family: var(--cb-font-mono); font-variant-numeric: tabular-nums; }}

/* Mission header */
.cb-header {{ display:flex; align-items:center; gap:14px; padding:10px 14px; border:1px solid var(--cb-border);
  background: linear-gradient(90deg, var(--cb-surface), var(--cb-surface2)); border-radius: var(--cb-radius);
  box-shadow: var(--cb-shadow); margin-bottom: 14px; }}
.cb-header img {{ width:44px; height:44px; display:block; }}
.cb-brand {{ font-weight:800; letter-spacing:.08em; font-size:1.15rem; color:var(--cb-text); }}
.cb-brand b {{ color: var(--cb-accent); }}
.cb-descriptor {{ color:var(--cb-muted); font-size:.78rem; letter-spacing:.04em; }}
.cb-header .cb-spacer {{ flex:1; }}
.cb-tricolour {{ height:2px; width:46px; margin-top:4px; background:linear-gradient(90deg,#FF9933 0 33%,#FFFFFF 33% 66%,#138808 66%); }}
.cb-ctx {{ text-align:right; font-size:.74rem; color:var(--cb-muted); line-height:1.5; }}
.cb-ctx .cb-mono {{ color:var(--cb-text); }}

/* Panels */
.cb-panel {{ border:1px solid var(--cb-border); background:var(--cb-surface); border-radius:var(--cb-radius);
  box-shadow:var(--cb-shadow); margin:0 0 12px 0; }}
.cb-panel-h {{ display:flex; justify-content:space-between; align-items:center; gap:8px; padding:8px 12px;
  border-bottom:1px solid var(--cb-border); background:var(--cb-surface2); }}
.cb-panel-t {{ font-size:.72rem; font-weight:700; letter-spacing:.11em; text-transform:uppercase; color:var(--cb-muted); }}
.cb-panel-b {{ padding:10px 12px; color:var(--cb-text); font-size:.9rem; }}
.cb-note {{ color:var(--cb-muted); font-size:.8rem; }}

/* Metric tiles */
.cb-tile {{ border:1px solid var(--cb-border); background:var(--cb-surface); border-radius:var(--cb-radius);
  padding:10px 12px; min-height:92px; border-top:2px solid var(--cb-border); }}
.cb-tile.t-ok {{ border-top-color:var(--cb-ok); }} .cb-tile.t-warn {{ border-top-color:var(--cb-warn); }}
.cb-tile.t-bad {{ border-top-color:var(--cb-bad); }} .cb-tile.t-info {{ border-top-color:var(--cb-accent-info); }}
.cb-tile-l {{ font-size:.68rem; letter-spacing:.1em; text-transform:uppercase; color:var(--cb-muted); }}
.cb-tile-v {{ font-family:var(--cb-font-mono); font-size:1.4rem; font-weight:700; margin-top:4px; color:var(--cb-text); }}
.cb-tile-n {{ font-size:.75rem; color:var(--cb-muted); margin-top:2px; }}

/* Status chips (always icon + text, never colour alone) */
.cb-chip {{ display:inline-flex; align-items:center; gap:6px; padding:2px 9px; border-radius:2px; font-size:.72rem;
  font-weight:700; letter-spacing:.06em; text-transform:uppercase; border:1px solid; white-space:nowrap; }}
.cb-chip.ok   {{ color:var(--cb-ok);   background:var(--cb-ok-bg);   border-color:var(--cb-ok); }}
.cb-chip.warn {{ color:var(--cb-warn); background:var(--cb-warn-bg); border-color:var(--cb-warn); }}
.cb-chip.bad  {{ color:var(--cb-bad);  background:var(--cb-bad-bg);  border-color:var(--cb-bad); }}
.cb-chip.info {{ color:var(--cb-accent-info); background:var(--cb-info-bg); border-color:var(--cb-accent-info); }}
.cb-chip.mute {{ color:var(--cb-mute); background:var(--cb-mute-bg); border-color:var(--cb-border); }}

/* Key/value lists and claims */
.cb-kv {{ display:grid; grid-template-columns: 9.5rem 1fr; gap:4px 12px; font-size:.84rem; }}
.cb-kv dt {{ color:var(--cb-muted); }} .cb-kv dd {{ margin:0; font-family:var(--cb-font-mono); word-break:break-all; }}
.cb-claim {{ display:grid; grid-template-columns: minmax(10rem,14rem) max-content minmax(0,1fr); gap:10px; align-items:center; padding:8px 12px;
  border-bottom:1px solid var(--cb-border); font-size:.85rem; }}
.cb-claim:last-child {{ border-bottom:0; }}
.cb-claim-q {{ font-weight:600; }} .cb-claim-d {{ color:var(--cb-muted); }}

/* Source panels: sensor identity rule */
.cb-src {{ border-left:3px solid var(--cb-border); }}
.cb-src.s-ohrc {{ border-left-color:var(--cb-ohrc); }} .cb-src.s-tmc2 {{ border-left-color:var(--cb-tmc2); }}
.cb-src.s-iirs {{ border-left-color:var(--cb-iirs); }}
.cb-sensor {{ font-weight:800; letter-spacing:.1em; }}
.s-ohrc .cb-sensor {{ color:var(--cb-ohrc); }} .s-tmc2 .cb-sensor {{ color:var(--cb-tmc2); }} .s-iirs .cb-sensor {{ color:var(--cb-iirs); }}

/* Pipeline stages */
.cb-stage {{ display:flex; justify-content:space-between; gap:10px; padding:7px 12px; border-left:3px solid var(--cb-border);
  background:var(--cb-surface); margin:4px 0; font-size:.86rem; border-radius:2px; }}
.cb-stage.done {{ border-left-color:var(--cb-accent-info); }} .cb-stage.run {{ border-left-color:var(--cb-accent); }}
.cb-stage.err {{ border-left-color:var(--cb-bad); }}
.cb-stage .st {{ color:var(--cb-muted); font-size:.74rem; text-transform:uppercase; letter-spacing:.08em; }}

/* Empty states / journey */
.cb-empty {{ border:1px dashed var(--cb-border); padding:18px; border-radius:var(--cb-radius); color:var(--cb-muted); background:var(--cb-surface); }}
.cb-empty b {{ color:var(--cb-text); }}
.cb-title {{ font-size:1.45rem; font-weight:800; letter-spacing:.02em; margin:2px 0 2px; }}
.cb-sub {{ color:var(--cb-muted); font-size:.9rem; margin-bottom:12px; }}
.cb-fixture {{ border:1px solid var(--cb-warn); color:var(--cb-warn); padding:4px 10px; font-size:.75rem; letter-spacing:.06em; }}

@media (max-width: 900px) {{
  .cb-claim {{ grid-template-columns: 1fr; gap:4px; }}
  .cb-kv {{ grid-template-columns: 7.5rem 1fr; }}
  .cb-header {{ flex-wrap: wrap; }}
  .cb-ctx {{ text-align:left; }}
}}
@media (prefers-reduced-motion: no-preference) {{
  .cb-tile, .cb-panel, .cb-chip {{ transition: border-color .15s ease, background-color .15s ease; }}
}}
"""


@lru_cache(maxsize=1)
def logo_data_uri() -> str:
    """Official app-icon crop, embedded (resized only; never recoloured)."""
    try:
        import cv2

        im = cv2.imread(str(ROOT / "branding" / "app_icon.png"), cv2.IMREAD_UNCHANGED)
        if im is None:
            return ""
        im = cv2.resize(im, (96, 96), interpolation=cv2.INTER_AREA)
        ok, buf = cv2.imencode(".png", im)
        return "data:image/png;base64," + base64.b64encode(buf.tobytes()).decode() if ok else ""
    except Exception:
        return ""


def inject(theme: str | None = None) -> str:
    import streamlit as st

    theme = theme or active_theme()
    st.markdown(f"<style>{build_css(theme)}</style>", unsafe_allow_html=True)
    return theme
