"""The five application pages. Each reads the shared workspace context set up in dashboard.py."""
from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import streamlit as st

from ui import components as C
from ui.data import browse_images
from ui.logic import (fmt_num, gate_status_tone, humanize_reason, gate_reasons, result_row, sensor_label,
                      validate_selection)
from ui.runner import execute_jobs, mission_jobs, write_summary_csv
from ui.state import load_workflow_state, output_dir

PREFERRED = [
    "ch2_ohr_ncp_20260103t1005176450_d_img_d18",
    "ch2_tmc_ncf_20231101t1708581528_d_img_d18",
    "ch2_iir_nci_20210622t1850441449_d_img_d32",
]


def ctx() -> dict:
    return st.session_state["_ctx"]


def _scan_needed(what: str) -> bool:
    c = ctx()
    if c["rows"]:
        return False
    C.md(C.empty_html(f"{what} needs scanned mission data", [
        "Enter the mission-data folder in the sidebar.",
        "Click <b>Scan mission data</b>.",
        "Return to this page.",
    ]))
    if c["errors"]:
        st.warning(f"{len(c['errors'])} product label(s) could not be read — see Data Workspace.")
    return True


def _scalar_result_block(x: dict) -> None:
    r = x["result"]
    C.md(C.claims_html(r))
    C.result_tiles(r)


# ------------------------------------------------------------------ Mission overview
def overview_page() -> None:
    c = ctx(); rows = c["rows"]; root: Path = c["root"]
    C.page_title("Mission Overview", "Where the experiment stands and what to do next.")
    state = load_workflow_state(root) if root.exists() else {}
    last = st.session_state.get("last_result")
    completed = set(int(v) for v in state.get("completed_stages", []))
    if c["scanned"]:
        completed.update({1, 2})
    if last is not None:
        completed.update({3, 4, 5, 6, 7})
    left, right = st.columns([5, 7], gap="large")
    with left:
        C.md(C.panel_html("Pipeline status", C.stages_html(
            completed, int(state.get("current_stage", 0) or 0), state.get("execution") == "running", state.get("execution") == "error")))
        if state.get("execution") == "complete":
            st.caption(f"Last workflow: {state.get('completed_at', '—')} · {state.get('workflow_summary', 'Experiment completed')}")
    with right:
        if not rows:
            C.md(C.empty_html("Start here", [
                "<b>Data Workspace</b> — point CHANDRABHAR-2 at your local mission folder and scan.",
                "<b>Registration</b> — choose a reference and a source product and run.",
                "<b>Evidence &amp; Results</b> — read the evidence gate and metrics.",
                "<b>Reports &amp; Export</b> — download JSON, PNG and CSV outputs.",
            ]))
            st.caption("Your Chandrayaan-2 files stay on this computer. CHANDRABHAR-2 does not upload them.")
        else:
            sensors = sorted(set(r["sensor"] for r in rows))
            a, b, d = st.columns(3)
            with a: C.tile("Products discovered", str(len(rows)), "supported mission products", "info")
            with b: C.tile("Sensors", str(len(sensors)), ", ".join(sensor_label(s) for s in sensors))
            with d: C.tile("Parse errors", str(len(c["errors"])), "see Data Workspace", "warn" if c["errors"] else "")
            if last is not None:
                C.md("<div style='height:10px'></div>")
                _scalar_result_block(last)
            elif state.get("execution") == "complete":
                C.md(C.panel_html("Persisted result", f"Completed {state.get('completed_at', '—')} · {state.get('workflow_summary', '')}"))
                if state.get("batch_summary"):
                    st.dataframe(state["batch_summary"], width="stretch", hide_index=True)
            else:
                st.info("Data scanned. Continue to **Registration** to run a pair.")


# ------------------------------------------------------------------ Data workspace
def data_page() -> None:
    c = ctx(); rows = c["rows"]; root: Path = c["root"]
    C.page_title("Data Workspace", "Mission products discovered from PDS4 labels in your local folder.")
    if _scan_needed("The data workspace"):
        return
    by_sensor: dict[str, dict] = {}
    for r in rows:
        by_sensor.setdefault(r["sensor"].upper(), r)
    cols = st.columns(3, gap="medium")
    for col, sensor in zip(cols, ["OHRC", "TMC2", "IIRS"]):
        with col:
            C.md(C.source_panel_html(by_sensor.get(sensor), sensor))
    if len(rows) > len(by_sensor):
        st.caption(f"{len(rows)} products found; the panels above show the first product per sensor. All are listed below.")
    st.markdown("##### All detected products")
    st.dataframe(rows, width="stretch", hide_index=True, column_config={
        "path": st.column_config.TextColumn("Source", width="large"),
        "gsd_m": st.column_config.NumberColumn("GSD (m)", format="%.2f"),
        "solar_elevation_deg": st.column_config.NumberColumn("Sun elevation", format="%.2f°"),
        "solar_azimuth_deg": st.column_config.NumberColumn("Sun azimuth", format="%.2f°"),
    })
    if c["errors"]:
        st.markdown("##### Labels that could not be read")
        C.md(C.chip_html(f"{len(c['errors'])} unreadable", "warn"))
        st.dataframe(c["errors"], width="stretch", hide_index=True)
    with st.expander("Mission browse products (PNG previews found in the folder)"):
        cols = st.columns(3)
        for i, sensor in enumerate(["OHRC", "TMC2", "IIRS"]):
            with cols[i]:
                st.markdown(f"**{sensor_label(sensor)}**")
                imgs = browse_images(root, sensor, 1)
                if imgs:
                    st.image(str(imgs[0]), caption=imgs[0].name, width="stretch")
                else:
                    st.caption("No browse PNG found in this mission folder")


# ------------------------------------------------------------------ Registration
def registration_page() -> None:
    c = ctx(); rows = c["rows"]; root: Path = c["root"]
    C.page_title("Image Registration", "Choose a sensor pair, check the context, then run the correspondence engine.")
    if _scan_needed("Registration"):
        return
    ids = {r["product_id"]: r for r in rows}
    options = [x for x in PREFERRED if x in ids] + [x for x in ids if x not in PREFERRED]
    left, right = st.columns([4, 8], gap="large")
    with left:
        ref_id = st.selectbox("Reference image", options, index=0, key="ref_sel",
                              format_func=lambda x: f"{sensor_label(ids[x]['sensor'])} · {x}",
                              help="The reference scene defines the common-grid coordinate frame.")
        src_id = st.selectbox("Source image", options, index=1 if len(options) > 1 else 0, key="src_sel",
                              format_func=lambda x: f"{sensor_label(ids[x]['sensor'])} · {x}",
                              help="The source scene is registered against the reference scene.")
        checks = validate_selection(ids, ref_id, src_id)
        for tone, msg in checks:
            (st.error if tone == "bad" else st.warning)(msg)
        blocked = any(t == "bad" for t, _ in checks)
        run_selected = st.button("Run selected correspondence", type="primary", width="stretch", disabled=blocked)
        run_all = st.button("Run all three mission sensor pairs", width="stretch", disabled=(len(ids) < 3),
                            help="Runs OHRC↔TMC2, OHRC↔IIRS and TMC2↔IIRS sequentially. CPU processing can take time.")
        st.caption("Runs use the engine's default scale cascade and evidence gate. No scientific parameter is changed here.")
    with right:
        a, b = st.columns(2)
        with a: C.md(C.source_panel_html(ids[ref_id], ids[ref_id]["sensor"]))
        with b: C.md(C.source_panel_html(ids[src_id], ids[src_id]["sensor"]))
    st.markdown("---")
    if run_selected or run_all:
        jobs = mission_jobs(ids) if run_all else [(ref_id, src_id)]
        results = execute_jobs(ids, jobs, root)
        if results:
            write_summary_csv(results, output_dir(root))
            st.rerun()
    last = st.session_state.get("last_result")
    if last:
        st.markdown(f"##### Latest result — {last.get('name', '').replace('_', ' ↔ ')}")
        _scalar_result_block(last)
        st.caption("Open **Evidence & Results** for the correspondence figure, gate interpretation and diagnostics.")


# ------------------------------------------------------------------ Evidence & results
def evidence_page() -> None:
    c = ctx(); root: Path = c["root"]
    C.page_title("Evidence & Results", "What the engine found, and whether that evidence clears the configured gate.")
    x = st.session_state.get("last_result")
    if not x:
        state = load_workflow_state(root) if root.exists() else {}
        if state.get("execution") == "complete" and state.get("batch_summary"):
            st.info(f"Showing persisted summary from {state.get('completed_at', '—')} (full result objects live only in the session that ran them).")
            st.dataframe(state["batch_summary"], width="stretch", hide_index=True)
            ev = Path(state.get("last_pair_evidence", ""))
            if ev.exists():
                st.image(str(ev), caption="Latest correspondence evidence saved by the completed run.", width="stretch")
        else:
            C.md(C.empty_html("No result to inspect yet", [
                "Run a pair from <b>Registration</b>.", "Results, gate reasons and figures appear here."]))
        return
    r = x["result"]; d = r.diagnostics or {}
    tone, label = gate_status_tone(d.get("status"))
    C.md(f"<div style='margin-bottom:8px'>{C.chip_html('Gate: ' + label, tone)} &nbsp; "
         f"<span class='cb-note'>Pair: {x.get('name', '—').replace('_', ' ↔ ')}</span></div>")
    _scalar_result_block(x)
    main, side = st.columns([8, 4], gap="large")
    with main:
        ev = Path(x.get("evidence_path", ""))
        if ev.exists():
            st.image(str(ev), caption="Common-grid correspondence view drawn from the matcher's returned points. "
                                      "Inliers are re-derived for display (reprojection error ≤ 3.0 px under the returned homography). "
                                      "This is not a raw-image overlay.", width="stretch")
            st.download_button("Download correspondence evidence PNG", ev.read_bytes(), file_name=ev.name, mime="image/png", key="download_evidence")
        pts = getattr(r, "points_ref", None)
        if pts is not None and len(pts):
            st.markdown("##### Spatial distribution of returned correspondences")
            p = np.asarray(pts)
            hist, _, _ = np.histogram2d(p[:, 1], p[:, 0], bins=(8, 8))
            st.bar_chart(hist, width="stretch")
    with side:
        reasons = gate_reasons(r)
        if reasons:
            body = "".join(f"<div style='margin:4px 0'>{C.chip_html('Not met', 'warn')} {C.e(humanize_reason(q))}</div>" for q in reasons)
        else:
            body = C.chip_html("All conditions met", "ok") + "<div class='cb-note' style='margin-top:6px'>This is the internal evidence gate, not independent validation.</div>"
        C.md(C.panel_html("Gate interpretation", body))
        C.md(C.panel_html("Measured values", C.kv_html([
            ("Tentative matches", r.tentative_matches), ("Independent inliers", r.inliers),
            ("Inlier ratio", fmt_num(r.inlier_ratio, 4)), ("Spatial coverage", fmt_num(r.coverage, 4)),
            ("RMSE (px)", fmt_num(r.rmse_px, 4)), ("RMSE (m)", fmt_num(d.get("rmse_m"), 4)),
            ("Target GSD (m)", d.get("target_gsd_m")), ("Elapsed (s)", fmt_num(d.get("elapsed_s"), 1)),
        ])))
        hm = getattr(r, "homography", None)
        if hm is not None:
            with st.expander("Estimated transformation (homography)"):
                st.code(np.array2string(np.asarray(hm), precision=6, suppress_small=True))
    cascade = d.get("scale_cascade", [])
    if cascade:
        st.markdown("##### Physical scale cascade")
        st.dataframe([{"Target GSD (m)": z.get("target_gsd_m"), "Status": z.get("status"),
                       "Coverage": z.get("grid_coverage", z.get("coverage")), "RMSE (m)": z.get("rmse_m"),
                       "Geographic warp": z.get("geographic_warp", False)} for z in cascade], width="stretch", hide_index=True)
    if x.get("batch_results"):
        st.markdown("##### Mission-pair results")
        st.dataframe([result_row(n, rs) for n, rs, _, _ in x["batch_results"]], width="stretch", hide_index=True)
    if c["diag"]:
        with st.expander("Full scientific diagnostics"):
            st.json(d)


# ------------------------------------------------------------------ Reports & export
def reports_page() -> None:
    c = ctx(); rows = c["rows"]; root: Path = c["root"]
    C.page_title("Reports & Reproducibility", "Everything produced by the experiment: metrics, evidence figures and the pair summary.")
    out = output_dir(root)
    x = st.session_state.get("last_result")
    if x:
        batch = x.get("batch_results", [])
        if batch and out.exists():
            write_summary_csv(batch, out)
    files = sorted([p for p in out.rglob("*") if p.is_file()], key=lambda p: p.stat().st_mtime, reverse=True) if out.exists() else []
    if not rows and not files:
        C.md(C.empty_html("No products yet", ["Scan mission data.", "Run a pair on <b>Registration</b>.",
                                               "JSON metrics, PNG evidence and a CSV summary appear here."]))
    if files:
        st.success(f"{len(files)} product file(s) available in {out}")
        st.dataframe([{"File": p.name, "Type": p.suffix.upper().lstrip("."), "Size (KB)": round(p.stat().st_size / 1024, 1),
                       "Modified": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(p.stat().st_mtime))} for p in files[:50]],
                     width="stretch", hide_index=True)
        pngs = [p for p in files if p.suffix.lower() == ".png"]
        if pngs:
            st.markdown("##### Visual evidence preview")
            cols = st.columns(min(3, len(pngs)))
            for i, png in enumerate(pngs[:3]):
                with cols[i]:
                    st.image(str(png), caption=png.name, width="stretch")
        st.markdown("##### Downloads")
        mime = {".json": "application/json", ".png": "image/png", ".csv": "text/csv"}
        for p in files[:50]:
            if p.suffix.lower() in mime:
                st.download_button(f"Download {p.name}", p.read_bytes(), file_name=p.name, mime=mime[p.suffix.lower()], key=f"dl_{p.name}")
    elif rows:
        st.info("The output folder has no files yet. Run an experiment on the Registration page.")
    st.markdown("##### Handoff checklist")
    items = [("Mission data scanned", bool(rows)), ("Correspondence experiment completed", bool(x)),
             ("Visual evidence generated", bool(x and Path(x.get("evidence_path", "")).exists())),
             ("Machine-readable metrics exported", bool(x and Path(x.get("json_path", "")).exists())),
             ("Three-pair summary available", bool(out.exists() and (out / "mission_experiment_summary.csv").exists()))]
    C.md("".join(f"<div style='margin:3px 0'>{C.chip_html('Done' if ok else 'Pending', 'info' if ok else 'mute')} &nbsp;{C.e(l)}</div>" for l, ok in items))
    st.caption("Reproducibility: the JSON per pair stores the full diagnostics, scale cascade and elapsed time. "
               "Engine v8.0.2 · Platform v2.0.0 (see VERSION.txt / PLATFORM_VERSION.txt).")
    C.md(C.panel_html("Scope of claims", "Software correctness (tests passing, code running) and scientific validation "
                      "(evidence gate on real mission data) are different things. This independent research prototype is "
                      "not an official ISRO product — see LEGAL/SOFTWARE_DISCLAIMER.md."))
