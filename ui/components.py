"""Reusable HTML components. ``*_html`` functions are pure (testable, previewable); thin
``st`` wrappers render them. All dynamic text is escaped."""
from __future__ import annotations

from html import escape as e
from typing import Any, Iterable

from ui.logic import (TONE_SYMBOL, evidence_claims, fmt_num, readiness, sensor_label,
                      gate_status_tone, fmt_pct)
from ui.tokens import SENSOR_KEYS

STAGES = [
    (1, "Connect to local mission-data folder"),
    (2, "Read Chandrayaan-2 sensor metadata"),
    (3, "Build geographic overlap and common lunar grid"),
    (4, "Normalize by physical GSD"),
    (5, "Build illumination-aware representations"),
    (6, "Find correspondences and verify geometry"),
    (7, "Apply evidence gate and export results"),
]


def chip_html(label: str, tone: str = "mute") -> str:
    tone = tone if tone in TONE_SYMBOL else "mute"
    return f'<span class="cb-chip {tone}"><span aria-hidden="true">{TONE_SYMBOL[tone]}</span>{e(label)}</span>'


def tile_html(label: str, value: str, note: str = "", tone: str = "") -> str:
    cls = f" t-{tone}" if tone else ""
    return (f'<div class="cb-tile{cls}"><div class="cb-tile-l">{e(label)}</div>'
            f'<div class="cb-tile-v">{e(value)}</div><div class="cb-tile-n">{e(note)}</div></div>')


def panel_html(title: str, body_html: str, right_html: str = "", extra_cls: str = "", title_cls: str = "") -> str:
    return (f'<section class="cb-panel {extra_cls}"><div class="cb-panel-h"><span class="cb-panel-t {title_cls}">{e(title)}</span>'
            f'{right_html}</div><div class="cb-panel-b">{body_html}</div></section>')


def kv_html(pairs: Iterable[tuple[str, Any]]) -> str:
    items = "".join(f"<dt>{e(str(k))}</dt><dd>{e('—' if v is None else str(v))}</dd>" for k, v in pairs)
    return f'<dl class="cb-kv">{items}</dl>'


def header_html(logo_uri: str, context: str, theme: str, app_state: tuple[str, str]) -> str:
    img = f'<img src="{logo_uri}" alt="CHANDRABHAR-2 logo">' if logo_uri else ""
    tone, label = app_state
    return (f'<header class="cb-header">{img}<div><div class="cb-brand">CHANDRABHAR<b>-2</b></div>'
            f'<div class="cb-descriptor">LUNAR INTELLIGENCE INTERFACE · Chandrayaan-2 OHRC · TMC-2 · IIRS correspondence</div>'
            f'<div class="cb-tricolour"></div></div><div class="cb-spacer"></div>'
            f'<div class="cb-ctx"><div>Workspace: <span class="cb-mono">{e(context)}</span></div>'
            f'<div>Theme: <span class="cb-mono">{e(theme.title())}</span> · change via ⋮ ▸ Settings ▸ Theme</div></div>'
            f'<div>{chip_html(label, tone)}</div></header>')


def source_panel_html(row: dict[str, Any] | None, sensor: str) -> str:
    key = SENSOR_KEYS.get(sensor.upper(), "ohrc")
    label = sensor_label(sensor)
    if not row:
        body = '<span class="cb-note">No product for this sensor was found in the scanned folder.</span>'
        return panel_html(label, body, chip_html("Not found", "mute"), f"cb-src s-{key}", "cb-sensor")
    tone, rlabel, note = readiness(row)
    sun = (f"{fmt_num(row.get('solar_elevation_deg'), 2)}° elev · {fmt_num(row.get('solar_azimuth_deg'), 2)}° az"
           if row.get("solar_elevation_deg") is not None else "—")
    body = kv_html([
        ("Product", row.get("product_id")), ("Dimensions", row.get("shape")), ("Data type", row.get("dtype")),
        ("GSD", fmt_num(row.get("gsd_m"), 2, "m")), ("Sun angles", sun),
        ("Acquired", row.get("acquisition_start")), ("CRS", row.get("crs") or "—"),
        ("Geometry table", "present" if row.get("geometry_table") else "not referenced"),
    ]) + f'<div class="cb-note" style="margin-top:8px">{e(note)}</div>'
    return panel_html(label, body, chip_html(rlabel, tone), f"cb-src s-{key}", "cb-sensor")


def claims_html(result: Any) -> str:
    rows = "".join(
        f'<div class="cb-claim"><div class="cb-claim-q">{e(c["q"])}</div><div>{chip_html(c["label"], c["tone"])}</div>'
        f'<div class="cb-claim-d">{e(c["detail"])}</div></div>' for c in evidence_claims(result))
    return panel_html("Evidence status — four separate claims", f'<div style="margin:-10px -12px">{rows}</div>')


def stages_html(completed: set[int], current: int = 0, running: bool = False, errored: bool = False) -> str:
    out = []
    for n, label in STAGES:
        if n in completed:
            cls, txt = "done", "done"
        elif errored and n == current:
            cls, txt = "err", "failed"
        elif running and n == current:
            cls, txt = "run", "running"
        else:
            cls, txt = "", "waiting"
        out.append(f'<div class="cb-stage {cls}"><span><b class="cb-mono">{n:02d}</b>&nbsp;&nbsp;{e(label)}</span>'
                   f'<span class="st">{txt}</span></div>')
    return "".join(out)


def empty_html(title: str, steps: list[str]) -> str:
    li = "".join(f"<li>{s}</li>" for s in steps)
    return f'<div class="cb-empty"><b>{e(title)}</b><ol style="margin:8px 0 0 18px;padding:0">{li}</ol></div>'


# ---- Streamlit wrappers ----------------------------------------------------------------
def md(html: str) -> None:
    import streamlit as st

    st.markdown(html, unsafe_allow_html=True)


def page_title(title: str, sub: str) -> None:
    md(f'<div class="cb-title">{e(title)}</div><div class="cb-sub">{e(sub)}</div>')


def tile(label: str, value: str, note: str = "", tone: str = "") -> None:
    md(tile_html(label, value, note, tone))


def result_tiles(result: Any) -> None:
    import streamlit as st

    d = result.diagnostics or {}
    tone, _ = gate_status_tone(d.get("status"))
    cols = st.columns(6)
    data = [
        ("Candidate matches", f"{result.tentative_matches:,}", "tentative", ""),
        ("Geometric inliers", f"{result.inliers:,}", "RANSAC", ""),
        ("Inlier ratio", fmt_pct(result.inlier_ratio), "inliers / matches", ""),
        ("Spatial coverage", fmt_pct(result.coverage), "4×4 grid", ""),
        ("RMSE", fmt_num(result.rmse_px, 3, "px"), f"{d.get('rmse_m', '—') if d.get('rmse_m') is not None else '—'} m", ""),
        ("Elapsed", fmt_num(d.get("elapsed_s"), 1, "s"), f"target GSD {fmt_num(d.get('target_gsd_m'), 2, 'm')}", ""),
    ]
    for c, (l, v, n, t) in zip(cols, data):
        with c:
            tile(l, v, n, t)
