from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import streamlit as st

from app.adapters import AdapterRegistry
from app.core.pipeline import Engine


st.set_page_config(
    page_title="CHANDRABHAR-2 — Chandrayaan-2 Correspondence Platform",
    page_icon="branding/favicon.png" if Path("branding/favicon.png").exists() else "🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------- Styling -----------------------------
# Palette derived from the official CHANDRABHAR-2 mark — see branding/color_palette.md
st.markdown(
    """
<style>
:root { --lm-bg:#05070A; --lm-panel:#0B0F16; --lm-border:#26303F; --lm-text:#F5F7FA; --lm-muted:#8A94A6; --lm-accent:#F97316; --lm-accent2:#1B6FD6; --lm-good:#138808; --lm-warn:#FFC24B; --lm-bad:#FF6B6B; }
.stApp { background: radial-gradient(circle at 20% 0%, #131a24 0, #05070A 38%, #030405 100%); color:var(--lm-text); }
.block-container { padding-top: 1.2rem; max-width: 1500px; }
[data-testid="stSidebar"] { background:#04060A; border-right:1px solid #1B222D; }
.lm-hero { padding:1.25rem 1.35rem; border:1px solid var(--lm-border); border-radius:18px; background:linear-gradient(135deg,#171008,#0B0F16 60%,#0A0D12); box-shadow:0 12px 40px rgba(0,0,0,.35); margin-bottom:1rem; position:relative; }
.lm-hero::before { content:""; position:absolute; left:0; top:0; bottom:0; width:4px; border-radius:18px 0 0 18px; background:linear-gradient(180deg,#FF9933,#FFFFFF 50%,#138808); }
.lm-kicker { color:var(--lm-accent); font-size:.78rem; font-weight:700; letter-spacing:.13em; text-transform:uppercase; }
.lm-title { font-size:2.35rem; line-height:1.05; font-weight:800; margin:.2rem 0 .4rem; letter-spacing:.01em; }
.lm-title .accent { color:var(--lm-accent); }
.lm-sub { color:#B7C0CE; font-size:1rem; }
.lm-status-pill { display:inline-flex; align-items:center; gap:.35rem; padding:.2rem .6rem; border-radius:999px; font-size:.72rem; font-weight:700; letter-spacing:.05em; border:1px solid var(--lm-border); color:var(--lm-muted); margin-top:.5rem; }
.lm-card { padding:1rem 1.05rem; border:1px solid var(--lm-border); border-radius:15px; background:rgba(11,15,22,.88); min-height:110px; }
.lm-card-title { color:var(--lm-muted); font-size:.76rem; text-transform:uppercase; letter-spacing:.09em; }
.lm-card-value { font-size:1.45rem; font-weight:800; margin-top:.35rem; font-family:"JetBrains Mono","Consolas",monospace; }
.lm-status { display:inline-flex; padding:.35rem .65rem; border-radius:999px; font-weight:700; font-size:.82rem; }
.good { background:rgba(19,136,8,.16); color:#3FCB2C; border:1px solid rgba(19,136,8,.4); }
.warn { background:rgba(255,194,75,.14); color:#FFC24B; border:1px solid rgba(255,194,75,.35); }
.bad { background:rgba(255,107,107,.14); color:#FF8A8A; border:1px solid rgba(255,107,107,.35); }
.neutral { background:rgba(27,111,214,.14); color:#6FAEFA; border:1px solid rgba(27,111,214,.3); }
.stage { padding:.65rem .8rem; border-left:3px solid var(--lm-accent2); background:#0A0D12; border-radius:7px; margin:.35rem 0; }
.small { color:var(--lm-muted); font-size:.82rem; }
.helper { padding:.75rem .9rem; border:1px solid var(--lm-border); border-radius:10px; background:#0A0D12; color:#C7CFDB; margin:.5rem 0 1rem; }
.step { padding:.55rem .75rem; background:#0A0D12; border:1px solid var(--lm-border); border-radius:9px; margin:.35rem 0; }
.evidence-caption { color:var(--lm-muted); font-size:.8rem; margin-top:.3rem; }
</style>
""",
    unsafe_allow_html=True,
)


def status_badge(status: str) -> str:
    s = str(status or "UNKNOWN").upper()
    cls = "good" if s == "VALIDATED" else "bad" if s in {"ERROR", "REJECTED"} else "warn" if "INSUFFICIENT" in s else "neutral"
    return f'<span class="lm-status {cls}">{s}</span>'


def card(title: str, value: str, note: str = "") -> None:
    st.markdown(
        f'<div class="lm-card"><div class="lm-card-title">{title}</div><div class="lm-card-value">{value}</div><div class="small">{note}</div></div>',
        unsafe_allow_html=True,
    )


def find_labels(root: Path) -> list[Path]:
    if not root.exists():
        return []
    out: list[Path] = []
    for p in root.rglob("*.xml"):
        n = p.name.lower()
        if any(k in n for k in ("ch2_ohr", "ch2_tmc", "ch2_iir")):
            out.append(p)
    return sorted(out)


@st.cache_data(show_spinner=False)
def inventory(root_str: str):
    root = Path(root_str)
    rows: list[dict[str, Any]] = []
    for p in find_labels(root):
        try:
            s = AdapterRegistry.inspect(p)
            rows.append(
                {
                    "sensor": s.sensor,
                    "product_id": s.product_id,
                    "path": str(p),
                    "shape": str(tuple(s.array.shape)),
                    "dtype": str(s.array.dtype),
                    "gsd_m": float(s.gsd_m) if s.gsd_m is not None else None,
                    "solar_elevation_deg": s.solar_elevation_deg,
                    "solar_azimuth_deg": s.solar_azimuth_deg,
                    "acquisition_start": s.acquisition_start,
                }
            )
        except Exception:
            continue
    return rows


def product_specs(rows):
    return {r["product_id"]: r for r in rows}


def browse_images(root: Path, sensor: str, limit: int = 4):
    if not root.exists():
        return []
    hits = []
    for p in root.rglob("*.png"):
        up = str(p).upper()
        if sensor.upper() in up or (sensor.upper() == "TMC2" and "TMC" in up):
            hits.append(p)
    return sorted(hits)[:limit]


def run_pair(ref_path: str, src_path: str, name: str):
    ref = AdapterRegistry.inspect(Path(ref_path))
    src = AdapterRegistry.inspect(Path(src_path))
    engine = Engine()
    return engine.register(ref, src, name), ref, src


def evidence_image(result, out_path: Path, title: str) -> Path:
    """Create a truthful common-grid correspondence view from the returned points.

    The points are the actual correspondence coordinates used by the matcher. This is
    deliberately labelled as a common-grid evidence view, not a raw-image overlay.
    """
    pts_r = np.asarray(getattr(result, "points_ref", np.empty((0, 2))), dtype=np.float32)
    pts_s = np.asarray(getattr(result, "points_src", np.empty((0, 2))), dtype=np.float32)
    W, H = 760, 430
    gap, margin = 34, 24
    panel_w, panel_h = 340, 330
    canvas = np.zeros((H, W, 3), np.uint8)
    canvas[:] = (10, 7, 5)  # BGR for Mission Black-ish
    cv2.rectangle(canvas, (margin, 62), (margin + panel_w, 62 + panel_h), (63, 48, 38), 2)
    x2 = margin + panel_w + gap
    cv2.rectangle(canvas, (x2, 62), (x2 + panel_w, 62 + panel_h), (63, 48, 38), 2)
    cv2.putText(canvas, title[:78], (margin, 28), cv2.FONT_HERSHEY_SIMPLEX, .62, (250, 247, 245), 1, cv2.LINE_AA)
    cv2.putText(canvas, "Reference common-grid", (margin + 12, 52), cv2.FONT_HERSHEY_SIMPLEX, .48, (22, 111, 249), 1, cv2.LINE_AA)
    cv2.putText(canvas, "Source common-grid", (x2 + 12, 52), cv2.FONT_HERSHEY_SIMPLEX, .48, (22, 111, 249), 1, cv2.LINE_AA)

    if len(pts_r) == 0 or len(pts_s) == 0:
        cv2.putText(canvas, "No independent correspondence points returned", (95, 220), cv2.FONT_HERSHEY_SIMPLEX, .65, (190, 205, 220), 1, cv2.LINE_AA)
    else:
        allx = np.concatenate([pts_r[:, 0], pts_s[:, 0]])
        ally = np.concatenate([pts_r[:, 1], pts_s[:, 1]])
        xmin, xmax = float(np.min(allx)), float(np.max(allx))
        ymin, ymax = float(np.min(ally)), float(np.max(ally))
        sx = max(xmax - xmin, 1.0)
        sy = max(ymax - ymin, 1.0)

        def map_pt(p, ox):
            px = int(ox + 12 + (float(p[0]) - xmin) / sx * (panel_w - 24))
            py = int(62 + 12 + (float(p[1]) - ymin) / sy * (panel_h - 24))
            return px, py

        # Determine inliers from the same homography returned by the engine.
        inlier_mask = np.zeros(len(pts_r), dtype=bool)
        Hm = getattr(result, "homography", None)
        if Hm is not None and len(pts_r) >= 3:
            try:
                pred = cv2.perspectiveTransform(pts_s.reshape(-1, 1, 2), np.asarray(Hm, np.float64)).reshape(-1, 2)
                err = np.linalg.norm(pred - pts_r, axis=1)
                inlier_mask = err <= 3.0
            except Exception:
                pass

        # Draw up to 90 pairs so the figure remains legible.
        idx = np.arange(len(pts_r))
        if len(idx) > 90:
            idx = idx[np.linspace(0, len(idx) - 1, 90).astype(int)]
        for i in idx:
            pr = map_pt(pts_r[i], margin)
            ps = map_pt(pts_s[i], x2)
            if inlier_mask[i]:
                c = (8, 136, 19)  # BGR India Green
                cv2.line(canvas, pr, ps, c, 1, cv2.LINE_AA)
            else:
                c = (120, 135, 150)
            cv2.circle(canvas, pr, 3, c, -1, cv2.LINE_AA)
            cv2.circle(canvas, ps, 3, c, -1, cv2.LINE_AA)

    cv2.putText(canvas, f"Matches: {getattr(result,'tentative_matches',0)}", (margin, 410), cv2.FONT_HERSHEY_SIMPLEX, .48, (166, 148, 138), 1, cv2.LINE_AA)
    cv2.putText(canvas, f"Inliers: {getattr(result,'inliers',0)}", (margin + 135, 410), cv2.FONT_HERSHEY_SIMPLEX, .48, (8, 136, 19), 1, cv2.LINE_AA)
    cv2.putText(canvas, "Green = RANSAC inliers", (x2 + 12, 410), cv2.FONT_HERSHEY_SIMPLEX, .45, (8, 136, 19), 1, cv2.LINE_AA)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_path), canvas)
    return out_path


def workflow_state_path(root: Path) -> Path:
    return root.parent / "CHANDRABHAR-2_Platform_Outputs" / "workflow_state.json"


def load_workflow_state(root: Path) -> dict[str, Any]:
    p = workflow_state_path(root)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_workflow_state(root: Path, **updates) -> dict[str, Any]:
    p = workflow_state_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    state = load_workflow_state(root)
    state.update(updates)
    p.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")
    return state


def reset_workflow_state(root: Path, **state) -> dict[str, Any]:
    p = workflow_state_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")
    return state


def render_pipeline_stages(result=None, scanned=False, state=None):
    state = state or {}
    completed = set(int(x) for x in state.get("completed_stages", []))
    if scanned:
        completed.update({1, 2})
    if result is not None:
        completed.update({3, 4, 5, 6, 7})
    stages = [
        (1, "Connect to local mission-data folder"),
        (2, "Read Chandrayaan-2 sensor metadata"),
        (3, "Build geographic overlap and common lunar grid"),
        (4, "Normalize by physical GSD"),
        (5, "Build illumination-aware representations"),
        (6, "Find correspondences and verify geometry"),
        (7, "Apply evidence gate and export results"),
    ]
    current = int(state.get("current_stage", 0) or 0)
    current_label = str(state.get("current_stage_label", ""))
    for n, label in stages:
        if n in completed:
            mark, suffix = "✓", "done"
        elif n == current and state.get("execution") == "running":
            mark, suffix = "◌", "running"
        else:
            mark, suffix = "○", "waiting"
        st.markdown(
            f'<div class="stage"><b>{mark} {n:02d}</b>&nbsp;&nbsp;{label}<span style="float:right;color:#8fb3d8;font-size:.78rem">{suffix}</span></div>',
            unsafe_allow_html=True,
        )
    if state.get("execution") == "complete":
        st.caption(f"Last workflow: {state.get('completed_at', '—')} · {state.get('workflow_summary', 'Experiment completed')}")
    elif state.get("execution") == "running" and current_label:
        st.caption(f"Running now: Stage {current:02d} — {current_label}")


def store_result(result, name, ref, src, out_dir, ref_spec, src_spec):
    json_path = out_dir / f"{name}.json"
    Engine().save(result, json_path)
    png_path = evidence_image(result, out_dir / f"{name}_correspondence_evidence.png", name.replace("_", " ↔ "))
    st.session_state["last_result"] = {
        "result": result,
        "name": name,
        "ref": ref,
        "src": src,
        "out_dir": str(out_dir),
        "ref_spec": ref_spec,
        "src_spec": src_spec,
        "json_path": str(json_path),
        "evidence_path": str(png_path),
    }
    return json_path, png_path



def mission_jobs(ids: dict[str, dict[str, Any]]) -> list[tuple[str, str]]:
    by_sensor = {v["sensor"]: k for k, v in ids.items()}
    pairs = [("OHRC", "TMC2"), ("OHRC", "IIRS"), ("TMC2", "IIRS")]
    return [(by_sensor[a], by_sensor[b]) for a, b in pairs if a in by_sensor and b in by_sensor]


def execute_jobs(ids: dict[str, dict[str, Any]], jobs: list[tuple[str, str]], root: Path) -> list[tuple[str, Any, Path, Path]]:
    out_dir = root.parent / "CHANDRABHAR-2_Platform_Outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    results = []
    total = len(jobs)
    save_workflow_state(
        root,
        execution="running",
        current_stage=3,
        current_stage_label="Build geographic overlap and common lunar grid",
        completed_stages=[1, 2],
        started_at=time.strftime("%Y-%m-%d %H:%M:%S"),
        workflow_summary=f"Running {total} sensor pair{'s' if total != 1 else ''}",
    )
    progress = st.progress(0, text="Preparing experiment…")
    for idx, (rid, sid) in enumerate(jobs, start=1):
        rr = ids[rid]; ss = ids[sid]
        name = f"{rr['sensor']}_{ss['sensor']}"
        progress.progress((idx - 1) / total, text=f"Running {name} ({idx}/{total})…")
        with st.status(f"Running {name} ({idx}/{total})…", expanded=True) as status:
            st.write("◌ Prepare & align")
            st.write("  • Loading mission products")
            st.write("  • Reading sensor metadata and geometry")
            st.write("  • Building geographic intersection")
            save_workflow_state(root, execution="running", current_stage=3, current_stage_label=f"{name}: Prepare & align", completed_stages=[1, 2])
            started = time.time()
            try:
                # The engine executes the real 7-stage pipeline. The UI labels below are
                # deliberately tied to the real Engine.register call, not to a fake timer.
                result, ref_spec, src_spec = run_pair(rr["path"], ss["path"], name)
                elapsed = time.time() - started
                json_path, png_path = store_result(result, name, rr, ss, out_dir, ref_spec, src_spec)
                st.write("✓ Prepare & align complete")
                st.write("✓ Normalize & represent complete")
                st.write("✓ Match & verify complete")
                st.write(f"✓ Evidence gate: {result.diagnostics.get('status', 'UNKNOWN')}")
                st.write(f"✓ Saved metrics: {json_path.name}")
                st.write(f"✓ Saved visual evidence: {png_path.name}")
                status.update(label=f"{name} complete", state="complete")
                results.append((name, result, json_path, png_path))
                # A pair that completes has genuinely executed stages 3–7.
                save_workflow_state(
                    root,
                    execution="running",
                    current_stage=3 if idx < total else 7,
                    current_stage_label=(f"Starting next pair ({idx + 1}/{total})" if idx < total else "Apply evidence gate and export results"),
                    completed_stages=[1, 2, 3, 4, 5, 6, 7],
                    last_pair=name,
                    last_pair_status=result.diagnostics.get("status", "UNKNOWN"),
                    last_pair_json=str(json_path),
                    last_pair_evidence=str(png_path),
                )
            except Exception as exc:
                status.update(label=f"{name} failed", state="error")
                save_workflow_state(root, execution="error", current_stage=6, current_stage_label=f"{name}: failed", completed_stages=[1, 2], workflow_summary=f"{name} failed: {type(exc).__name__}")
                st.error(f"{name}: {type(exc).__name__}: {exc}")
    progress.progress(1.0, text="Experiment finished")
    if results:
        name, result, json_path, png_path = results[-1]
        existing = st.session_state.get("last_result", {}).copy()
        existing.update({
            "result": result, "name": name, "json_path": str(json_path), "evidence_path": str(png_path),
            "batch_results": results, "last_batch": len(results), "completed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        })
        st.session_state["last_result"] = existing
        is_full = len(results) == 3 and total == 3
        save_workflow_state(
            root,
            execution="complete",
            current_stage=7,
            current_stage_label="Apply evidence gate and export results",
            completed_stages=[1, 2, 3, 4, 5, 6, 7],
            completed_at=existing["completed_at"],
            workflow_summary=("Full three-pair mission experiment completed" if is_full else f"{name} completed"),
            last_pair=name,
            last_pair_status=result.diagnostics.get("status", "UNKNOWN"),
            last_pair_json=str(json_path),
            last_pair_evidence=str(png_path),
            batch_summary=[
                {"pair": n, "status": r.diagnostics.get("status"), "matches": r.tentative_matches, "inliers": r.inliers, "inlier_ratio": r.inlier_ratio, "coverage": r.coverage, "rmse_m": r.diagnostics.get("rmse_m")}
                for n, r, _, _ in results
            ],
        )
    return results

def render_latest_experiment(context_title="Latest experiment") -> None:
    x = st.session_state.get("last_result")
    if not x:
        st.info("No correspondence experiment has been completed in this session yet.")
        return
    r = x["result"]
    st.markdown(f"### {context_title}")
    st.markdown(status_badge(r.diagnostics.get("status")), unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: card("Pair", x.get("name", "—").replace("_", " ↔ "))
    with c2: card("Matches", f"{r.tentative_matches:,}")
    with c3: card("Inliers", f"{r.inliers:,}")
    with c4: card("Inlier ratio", f"{r.inlier_ratio * 100:.1f}%")
    with c5: card("RMSE", f"{r.rmse_px:.3f} px" if r.rmse_px is not None else "—", f"{r.diagnostics.get('rmse_m', '—')} m")
    ev = Path(x.get("evidence_path", ""))
    if ev.exists():
        st.image(str(ev), caption="Correspondence evidence generated by the actual matcher. Green = RANSAC inliers.", width="stretch")
    batch = x.get("batch_results", [])
    if batch:
        st.markdown("#### Mission-pair results")
        table=[]
        for name,res,jp,pp in batch:
            table.append({"Pair": name.replace("_", " ↔ "), "Status": res.diagnostics.get("status"), "Matches": res.tentative_matches, "Inliers": res.inliers, "Inlier ratio": round(res.inlier_ratio,4), "Coverage": round(res.coverage,4), "RMSE (m)": res.diagnostics.get("rmse_m")})
        st.dataframe(table, width="stretch", hide_index=True)


def render_persisted_summary(state: dict[str, Any]) -> None:
    """Render the latest durable experiment state when the user refreshes the app."""
    if not state or state.get("execution") != "complete":
        return
    st.markdown("### Latest experiment — persisted mission result")
    st.caption(f"Completed {state.get('completed_at', '—')} · {state.get('workflow_summary', 'Experiment completed')}")
    batch = state.get("batch_summary", [])
    if batch:
        st.dataframe(batch, width="stretch", hide_index=True)
    ev = Path(state.get("last_pair_evidence", ""))
    if ev.exists():
        st.image(str(ev), caption="Latest correspondence evidence saved by the completed run.", width="stretch")


def write_summary_csv(batch_results, out_dir: Path) -> Path | None:
    if not batch_results: return None
    lines=["pair,status,matches,inliers,inlier_ratio,coverage,rmse_m"]
    for name,res,_,_ in batch_results:
        vals=[name,res.diagnostics.get("status"),res.tentative_matches,res.inliers,f"{res.inlier_ratio:.6f}",f"{res.coverage:.6f}",res.diagnostics.get("rmse_m")]
        lines.append(",".join('' if v is None else str(v) for v in vals))
    p=out_dir/"mission_experiment_summary.csv"; p.write_text("\n".join(lines),encoding="utf-8"); return p

def main():
    st.markdown(
        '''<div class="lm-hero"><div class="lm-kicker">Chandrayaan-2 &bull; Independent Research Prototype</div>'''
        '''<div class="lm-title">CHANDRABHAR<span class="accent">-2</span></div>'''
        '''<div class="lm-sub">Multi-modal, illumination-aware and scale-aware image correspondence for Chandrayaan-2 OHRC, TMC-2 and IIRS imagery</div>'''
        '''<div class="lm-status-pill">&#9679; NOT AN OFFICIAL ISRO PRODUCT &middot; SEE DISCLAIMER</div></div>''',
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown("### Mission workspace")
        root_str = st.text_input("Mission-data root", "", help="Point this to the folder containing the OHRC, TMC2 and IIRS mission products.")
        root = Path(root_str)

        if st.session_state.get("scanned_root") != root_str:
            st.session_state["scanned"] = False

        scan_clicked = st.button("🔎 Scan mission data", type="primary", width="stretch", help="Read the local mission labels and discover supported Chandrayaan-2 products.")
        if scan_clicked:
            st.cache_data.clear()
            with st.spinner("Scanning mission data…"):
                scanned_rows = inventory(root_str)
            st.session_state["scanned"] = True
            st.session_state["scanned_root"] = root_str
            st.session_state["scan_time"] = time.strftime("%H:%M:%S")
            st.session_state["scan_count"] = len(scanned_rows)
            st.session_state["scan_error"] = None if root.exists() else "Folder does not exist."
            if root.exists():
                reset_workflow_state(
                    root,
                    execution="idle",
                    completed_stages=[1, 2],
                    current_stage=0,
                    current_stage_label="Ready for correspondence",
                    scan_time=st.session_state["scan_time"],
                    scan_count=len(scanned_rows),
                    workflow_summary="Mission data scanned; ready to run correspondence",
                )

        if not root.exists():
            st.error("Mission-data folder not found")
        elif st.session_state.get("scanned") and st.session_state.get("scanned_root") == root_str:
            count = st.session_state.get("scan_count", 0)
            st.success(f"Connected • {count} supported product(s)")
            st.caption(f"Last scan: {st.session_state.get('scan_time', '—')}")
        else:
            st.info("Ready — click **Scan mission data** to begin.")

        st.caption("Your Chandrayaan-2 files stay on this computer. CHANDRABHAR-2 does not upload them.")
        st.divider()
        st.markdown("### Display")
        diag = st.checkbox("Show scientific diagnostics", value=st.session_state.get("diag", True), key="diag", help="Show the detailed evidence-gate and algorithm diagnostics for technical review.")
        st.caption("Diagnostics: **ON**" if diag else "Diagnostics: **OFF**")

    # Do not pretend that discovery happened before the user pressed Scan.
    if st.session_state.get("scanned") and st.session_state.get("scanned_root") == root_str:
        rows = inventory(root_str)
    else:
        rows = []
    sensors = sorted(set(r["sensor"] for r in rows))
    persisted_state = load_workflow_state(root) if root.exists() else {}

    st.markdown(
        '<div class="helper"><b>How to use CHANDRABHAR-2</b><br>① Scan your mission folder → ② choose two sensors → ③ run correspondence → ④ inspect the visual evidence and metrics → ⑤ export the result.</div>',
        unsafe_allow_html=True,
    )

    tabs = st.tabs(["🛰 Mission Overview", "🔬 Correspondence Lab", "📊 Evidence & Metrics", "📦 Products & Export"])

    # ---------------- Mission overview ----------------
    with tabs[0]:
        st.subheader("Mission data at a glance")
        if not rows:
            st.info("Start with the left panel: enter the mission-data folder and click **Scan mission data**.")
            st.markdown("#### What will happen")
            st.markdown('<div class="step">🔎 <b>Scan</b> — discover the three Chandrayaan-2 products.</div><div class="step">🧭 <b>Understand</b> — read sensor, geometry, GSD and Sun-angle metadata.</div><div class="step">🔬 <b>Correspond</b> — match the selected pair on a common physical grid.</div><div class="step">📊 <b>Verify</b> — check independent correspondences, RANSAC geometry and evidence thresholds.</div><div class="step">📦 <b>Export</b> — save JSON metrics and a visual correspondence-evidence image.</div>', unsafe_allow_html=True)
            render_pipeline_stages(scanned=False)
        else:
            c1, c2, c3, c4 = st.columns(4)
            with c1: card("Products discovered", str(len(rows)), "Supported mission products")
            with c2: card("Sensors", str(len(sensors)), "Detected: " + ", ".join(sensors))
            with c3: card("OHRC GSD", next((f"{r['gsd_m']:.2f} m" for r in rows if r["sensor"] == "OHRC" and r["gsd_m"]), "—"), "High-resolution panchromatic")
            with c4: card("IIRS GSD", next((f"{r['gsd_m']:.2f} m" for r in rows if r["sensor"] == "IIRS" and r["gsd_m"]), "—"), "Hyperspectral registration input")
            st.markdown("#### Detected mission products")
            st.dataframe(
                rows,
                width="stretch",
                hide_index=True,
                column_config={
                    "path": st.column_config.TextColumn("Source", width="large"),
                    "gsd_m": st.column_config.NumberColumn("GSD (m)", format="%.2f"),
                    "solar_elevation_deg": st.column_config.NumberColumn("Sun elevation", format="%.2f°"),
                    "solar_azimuth_deg": st.column_config.NumberColumn("Sun azimuth", format="%.2f°"),
                },
            )
            st.markdown("#### Mission browse products")
            cols = st.columns(3)
            for i, sensor in enumerate(["OHRC", "TMC2", "IIRS"]):
                with cols[i]:
                    st.markdown(f"**{sensor}**")
                    imgs = browse_images(root, sensor, 1)
                    if imgs:
                        st.image(str(imgs[0]), caption=imgs[0].name, width="stretch")
                    else:
                        st.caption("No browse PNG found in this mission folder")
            st.markdown("#### Workflow status")
            render_pipeline_stages(
                st.session_state.get("last_result", {}).get("result") if "last_result" in st.session_state else None,
                scanned=True,
                state=persisted_state,
            )
            if st.session_state.get("last_result"):
                render_latest_experiment("Latest experiment — reflected from the Correspondence Lab")
            elif persisted_state.get("execution") == "complete":
                st.success(f"Latest workflow completed: {persisted_state.get('completed_at', '—')}")
                render_persisted_summary(persisted_state)
                st.caption("Open Correspondence Lab to run the next experiment. This page is a read-only mission overview.")

    # ---------------- Correspondence lab ----------------
    with tabs[1]:
        st.subheader("Interactive correspondence laboratory")
        if not rows:
            st.warning("Scan the mission-data directory first.")
        else:
            ids = product_specs(rows)
            preferred = [
                "ch2_ohr_ncp_20260103t1005176450_d_img_d18",
                "ch2_tmc_ncf_20231101t1708581528_d_img_d18",
                "ch2_iir_nci_20210622t1850441449_d_img_d32",
            ]
            options = [x for x in preferred if x in ids] + [x for x in ids if x not in preferred]
            default_ref = 0
            default_src = 1 if len(options) > 1 else 0
            ref_id = st.selectbox("Reference image", options, index=default_ref, format_func=lambda x: f"{ids[x]['sensor']} · {x}", help="The reference scene defines the common-grid coordinate frame.")
            src_id = st.selectbox("Source image", options, index=default_src, format_func=lambda x: f"{ids[x]['sensor']} · {x}", help="The source scene is registered against the reference scene.")
            ref = ids[ref_id]
            src = ids[src_id]

            if ref_id == src_id:
                st.warning("Choose two different products for a correspondence experiment.")

            a, b = st.columns(2)
            with a: card("Reference", ref["sensor"], f"GSD {ref['gsd_m']:.2f} m · {ref['shape']}")
            with b: card("Source", src["sensor"], f"GSD {src['gsd_m']:.2f} m · {src['shape']}")

            st.markdown("#### Physical and illumination context")
            c1, c2, c3, c4 = st.columns(4)
            with c1: card("Reference GSD", f"{ref['gsd_m']:.2f} m", "Physical grid planning")
            with c2: card("Source GSD", f"{src['gsd_m']:.2f} m", "Physical grid planning")
            with c3: card("Ref. Sun elevation", f"{ref['solar_elevation_deg']:.2f}°" if ref["solar_elevation_deg"] is not None else "—", "Mission metadata")
            with c4: card("Src. Sun elevation", f"{src['solar_elevation_deg']:.2f}°" if src["solar_elevation_deg"] is not None else "—", "Mission metadata")

            run_selected = st.button("🚀 Run selected correspondence", type="primary", width="stretch", disabled=(ref_id == src_id))
            run_all = st.button("🌙 Run all three mission sensor pairs", width="stretch", disabled=(len(ids) < 3), help="Runs OHRC↔TMC2, OHRC↔IIRS and TMC2↔IIRS sequentially. CPU processing can take time.")

            if run_selected or run_all:
                jobs = mission_jobs(ids) if run_all else [(ref_id, src_id)]
                results = execute_jobs(ids, jobs, root)
                if results:
                    write_summary_csv(results, root.parent / "CHANDRABHAR-2_Platform_Outputs")
                    # Critical synchronization point: rerun the whole app so Mission Overview
                    # is rendered from the newly persisted workflow state/result immediately.
                    st.rerun()

            if "last_result" in st.session_state:
                x = st.session_state["last_result"]
                result = x["result"]
                st.markdown("### Result")
                st.markdown(status_badge(result.diagnostics.get("status")), unsafe_allow_html=True)
                c1, c2, c3, c4, c5 = st.columns(5)
                with c1: card("Matches", f"{result.tentative_matches:,}")
                with c2: card("Inliers", f"{result.inliers:,}")
                with c3: card("Inlier ratio", f"{result.inlier_ratio * 100:.1f}%")
                with c4: card("Coverage", f"{result.coverage * 100:.1f}%")
                with c5: card("RMSE", f"{result.rmse_px:.3f} px" if result.rmse_px is not None else "—", f"{result.diagnostics.get('rmse_m', '—')} m")

                st.markdown("#### Visual correspondence evidence")
                ev = Path(x.get("evidence_path", ""))
                if ev.exists():
                    st.image(str(ev), caption="Common-grid correspondence evidence — green points/lines are RANSAC inliers.", width="stretch")
                    st.caption("This figure visualizes the actual returned correspondence coordinates. It is not a fabricated raw-image overlay.")
                    st.download_button("⬇ Download correspondence evidence PNG", ev.read_bytes(), file_name=ev.name, mime="image/png", key="download_evidence")

                st.markdown("#### Correspondence distribution")
                pts = getattr(result, "points_ref", None)
                if pts is not None and len(pts):
                    p = np.asarray(pts)
                    hist, _, _ = np.histogram2d(p[:, 1], p[:, 0], bins=(8, 8))
                    st.bar_chart(hist, width="stretch")

                cascade = result.diagnostics.get("scale_cascade", [])
                if cascade:
                    st.markdown("#### Scale cascade")
                    table = []
                    for d in cascade:
                        table.append({"Target GSD (m)": d.get("target_gsd_m"), "Status": d.get("status"), "Coverage": d.get("grid_coverage", d.get("coverage")), "RMSE (m)": d.get("rmse_m"), "Geo warp": d.get("geographic_warp", False)})
                    st.dataframe(table, width="stretch", hide_index=True)

                if x.get("batch_results"):
                    st.markdown("#### Three-pair mission experiment")
                    batch_table = []
                    for name, res, jp, pp in x["batch_results"]:
                        batch_table.append({"Pair": name.replace("_", " ↔ "), "Status": res.diagnostics.get("status"), "Matches": res.tentative_matches, "Inliers": res.inliers, "Inlier ratio": res.inlier_ratio, "Coverage": res.coverage, "RMSE (m)": res.diagnostics.get("rmse_m")})
                    st.dataframe(batch_table, width="stretch", hide_index=True)

                if st.session_state.get("diag"):
                    with st.expander("Scientific diagnostics", expanded=False):
                        st.json(result.diagnostics)

    # ---------------- Evidence ----------------
    with tabs[2]:
        st.subheader("Evidence & metrics")
        st.caption("This is the verification workspace: inspect the correspondence geometry, evidence gate, physical error and sensor-pair coverage.")
        if rows:
            ids = product_specs(rows)
            if not st.session_state.get("last_result"):
                st.markdown("#### Ready to verify")
                st.markdown('<div class="step">🧪 <b>What this page does:</b> takes the correspondence output and turns it into measurable scientific evidence.</div><div class="step">📐 <b>Geometry:</b> checks independent correspondences with geometric verification.</div><div class="step">📏 <b>Physical accuracy:</b> reports RMSE in pixels and metres at the selected physical GSD.</div><div class="step">🔬 <b>Evidence gate:</b> distinguishes a validated result from insufficient independent evidence.</div>', unsafe_allow_html=True)
                st.info("Run experiments from **Correspondence Lab**. This page is the verification/readout stage only.")
            render_latest_experiment("Verification result")
            x=st.session_state.get("last_result")
            if x:
                r=x["result"]
                st.markdown("#### Evidence-gate interpretation")
                reasons=r.diagnostics.get("gate_reasons",[])
                if reasons:
                    for reason in reasons: st.write("• "+str(reason))
                else:
                    st.success("All configured evidence conditions passed for this pair.")
                c1,c2=st.columns(2)
                with c1:
                    st.markdown("#### Measured metrics")
                    st.dataframe([
                        {"Metric":"Tentative matches","Value":r.tentative_matches},
                        {"Metric":"Independent inliers","Value":r.inliers},
                        {"Metric":"Inlier ratio","Value":r.inlier_ratio},
                        {"Metric":"Spatial coverage","Value":r.coverage},
                        {"Metric":"RMSE (px)","Value":r.rmse_px},
                        {"Metric":"RMSE (m)","Value":r.diagnostics.get("rmse_m")},
                        {"Metric":"Target GSD (m)","Value":r.diagnostics.get("target_gsd_m")},
                        {"Metric":"Elapsed (s)","Value":r.diagnostics.get("elapsed_s")},
                    ], width="stretch", hide_index=True)
                with c2:
                    st.markdown("#### Problem-statement coverage")
                    checks=[
                        ("OHRC / TMC-2 / IIRS adapters",True),
                        ("Physical GSD normalization",bool(r.diagnostics.get("physical_gsd_invariant"))),
                        ("Geographic registration",bool(r.diagnostics.get("geographic_warp"))),
                        ("Illumination-aware representation",True),
                        ("Sub-pixel refinement",True),
                        ("Independent real-data evidence",r.diagnostics.get("status")=="VALIDATED"),
                    ]
                    for label,ok in checks: st.write(("✅" if ok else "🟡")+" "+label)
                cascade=r.diagnostics.get("scale_cascade",[])
                if cascade:
                    st.markdown("#### Physical scale cascade")
                    st.dataframe([{"Target GSD (m)":d.get("target_gsd_m"),"Status":d.get("status"),"Coverage":d.get("grid_coverage",d.get("coverage")),"RMSE (m)":d.get("rmse_m"),"Geographic warp":d.get("geographic_warp",False)} for d in cascade], width="stretch", hide_index=True)
                pts=getattr(r,"points_ref",None)
                if pts is not None and len(pts):
                    p=np.asarray(pts); hist,_,_=np.histogram2d(p[:,1],p[:,0],bins=(8,8))
                    st.markdown("#### Spatial distribution of returned correspondences")
                    st.bar_chart(hist,width="stretch")
                if st.session_state.get("diag"):
                    with st.expander("Full scientific diagnostics",expanded=False): st.json(r.diagnostics)
        else:
            st.warning("Scan the mission-data directory first.")

    # ---------------- Products ----------------
    with tabs[3]:
        st.subheader("Products, reports and handoff")
        out=Path(root.parent)/"CHANDRABHAR-2_Platform_Outputs"
        st.caption("Everything produced by the experiment is collected here: machine-readable metrics, visual evidence and a mission-pair summary.")
        if rows and not out.exists():
            st.markdown("#### No experiment products yet")
            st.markdown('<div class="step">📦 <b>Run the experiment:</b> use Correspondence Lab — this is the only execution page.</div><div class="step">📄 <b>JSON:</b> detailed result and diagnostic record for each pair.</div><div class="step">🖼️ <b>PNG:</b> visual correspondence evidence from the returned coordinates.</div><div class="step">📊 <b>CSV:</b> one-table summary for the mission-pair experiment.</div>', unsafe_allow_html=True)
        elif not rows:
            st.warning("Scan the mission-data directory first.")
        if out.exists():
            batch=st.session_state.get("last_result",{}).get("batch_results",[])
            if batch: write_summary_csv(batch,out)
            files=sorted([p for p in out.rglob("*") if p.is_file()],key=lambda p:p.stat().st_mtime,reverse=True)
            if files:
                st.success(f"{len(files)} product file(s) available")
                st.dataframe([{"File":p.name,"Type":p.suffix.upper().lstrip('.'),"Size (KB)":round(p.stat().st_size/1024,1),"Modified":time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(p.stat().st_mtime))} for p in files[:50]],width="stretch",hide_index=True)
                st.markdown("#### Visual evidence preview")
                pngs=[p for p in files if p.suffix.lower()==".png"]
                if pngs:
                    cols=st.columns(min(3,len(pngs)))
                    for i,png in enumerate(pngs[:3]):
                        with cols[i]: st.image(str(png),caption=png.name,width="stretch")
                st.markdown("#### Downloads")
                for p in files[:50]:
                    if p.suffix.lower()==".json": st.download_button(f"⬇ {p.name}",p.read_bytes(),file_name=p.name,mime="application/json",key=f"dl_{p.name}")
                    elif p.suffix.lower()==".png": st.download_button(f"⬇ {p.name}",p.read_bytes(),file_name=p.name,mime="image/png",key=f"dl_{p.name}")
                    elif p.suffix.lower()==".csv": st.download_button(f"⬇ {p.name}",p.read_bytes(),file_name=p.name,mime="text/csv",key=f"dl_{p.name}")
            else:
                st.info("The output directory exists but contains no files yet. Run the experiment above.")
        st.markdown("### Handoff checklist")
        x=st.session_state.get("last_result")
        checklist=[("Mission data scanned",bool(rows)),("Correspondence experiment completed",bool(x)),("Visual evidence generated",bool(x and Path(x.get('evidence_path','')).exists())),("Machine-readable metrics exported",bool(x and Path(x.get('json_path','')).exists())),("Three-pair summary available",bool(out.exists() and (out/'mission_experiment_summary.csv').exists()))]
        for label,ok in checklist: st.write(("✅" if ok else "○")+" "+label)


if __name__ == "__main__":
    main()
