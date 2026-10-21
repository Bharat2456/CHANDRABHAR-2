"""Pair execution with real progress + persisted state (flow preserved from the original dashboard).

Only ``Engine.register`` does scientific work; this module wraps it with state saving and UI feedback.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import streamlit as st

from app.adapters import AdapterRegistry
from app.core.pipeline import Engine
from ui.evidence_image import evidence_image
from ui.logic import explain_error
from ui.state import load_workflow_state, output_dir, reset_workflow_state, save_workflow_state  # noqa: F401


def run_pair(ref_path: str, src_path: str, name: str):
    ref = AdapterRegistry.inspect(Path(ref_path))
    src = AdapterRegistry.inspect(Path(src_path))
    engine = Engine()
    return engine.register(ref, src, name), ref, src


def store_result(result, name, ref, src, out_dir, ref_spec, src_spec):
    json_path = out_dir / f"{name}.json"
    Engine().save(result, json_path)
    png_path = evidence_image(result, out_dir / f"{name}_correspondence_evidence.png", name.replace("_", " ↔ "))
    st.session_state["last_result"] = {
        "result": result, "name": name, "ref": ref, "src": src, "out_dir": str(out_dir),
        "ref_spec": ref_spec, "src_spec": src_spec, "json_path": str(json_path), "evidence_path": str(png_path),
    }
    return json_path, png_path


def mission_jobs(ids: dict[str, dict[str, Any]]) -> list[tuple[str, str]]:
    by_sensor = {v["sensor"]: k for k, v in ids.items()}
    pairs = [("OHRC", "TMC2"), ("OHRC", "IIRS"), ("TMC2", "IIRS")]
    return [(by_sensor[a], by_sensor[b]) for a, b in pairs if a in by_sensor and b in by_sensor]


def write_summary_csv(batch_results, out_dir: Path) -> Path | None:
    if not batch_results:
        return None
    lines = ["pair,status,matches,inliers,inlier_ratio,coverage,rmse_m"]
    for name, res, _, _ in batch_results:
        vals = [name, res.diagnostics.get("status"), res.tentative_matches, res.inliers,
                f"{res.inlier_ratio:.6f}", f"{res.coverage:.6f}", res.diagnostics.get("rmse_m")]
        lines.append(",".join("" if v is None else str(v) for v in vals))
    p = out_dir / "mission_experiment_summary.csv"
    p.write_text("\n".join(lines), encoding="utf-8")
    return p


def execute_jobs(ids: dict[str, dict[str, Any]], jobs: list[tuple[str, str]], root: Path):
    out_dir = output_dir(root)
    out_dir.mkdir(parents=True, exist_ok=True)
    results = []
    total = len(jobs)
    save_workflow_state(
        root, execution="running", current_stage=3,
        current_stage_label="Build geographic overlap and common lunar grid", completed_stages=[1, 2],
        started_at=time.strftime("%Y-%m-%d %H:%M:%S"),
        workflow_summary=f"Running {total} sensor pair{'s' if total != 1 else ''}",
    )
    progress = st.progress(0, text="Preparing experiment…")
    for idx, (rid, sid) in enumerate(jobs, start=1):
        rr = ids[rid]; ss = ids[sid]
        name = f"{rr['sensor']}_{ss['sensor']}"
        progress.progress((idx - 1) / total, text=f"Running {name} ({idx}/{total})…")
        with st.status(f"Running {name} ({idx}/{total})…", expanded=True) as status:
            st.write("Engine running: geographic overlap → physical GSD grid → representation → matching → gate.")
            st.caption("The engine reports no per-stage progress, so no stage percentages are shown.")
            save_workflow_state(root, execution="running", current_stage=3, current_stage_label=f"{name}: running", completed_stages=[1, 2])
            started = time.time()
            try:
                result, ref_spec, src_spec = run_pair(rr["path"], ss["path"], name)
                elapsed = time.time() - started
                json_path, png_path = store_result(result, name, rr, ss, out_dir, ref_spec, src_spec)
                st.write(f"Finished in {elapsed:.1f} s · evidence gate: {result.diagnostics.get('status', 'UNKNOWN')}")
                st.write(f"Saved metrics: {json_path.name}")
                st.write(f"Saved visual evidence: {png_path.name}")
                status.update(label=f"{name} complete", state="complete")
                results.append((name, result, json_path, png_path))
                save_workflow_state(
                    root, execution="running", current_stage=3 if idx < total else 7,
                    current_stage_label=(f"Starting next pair ({idx + 1}/{total})" if idx < total else "Apply evidence gate and export results"),
                    completed_stages=[1, 2, 3, 4, 5, 6, 7], last_pair=name,
                    last_pair_status=result.diagnostics.get("status", "UNKNOWN"),
                    last_pair_json=str(json_path), last_pair_evidence=str(png_path),
                )
            except Exception as exc:
                status.update(label=f"{name} failed", state="error")
                save_workflow_state(root, execution="error", current_stage=6, current_stage_label=f"{name}: failed",
                                    completed_stages=[1, 2], workflow_summary=f"{name} failed: {type(exc).__name__}")
                summary, action = explain_error(exc)
                st.error(f"{name}: {summary} {action}")
                with st.expander("Technical details"):
                    st.code(f"{type(exc).__name__}: {exc}")
    progress.progress(1.0, text="Experiment finished")
    if results:
        name, result, json_path, png_path = results[-1]
        existing = st.session_state.get("last_result", {}).copy()
        existing.update({"result": result, "name": name, "json_path": str(json_path), "evidence_path": str(png_path),
                         "batch_results": results, "last_batch": len(results), "completed_at": time.strftime("%Y-%m-%d %H:%M:%S")})
        st.session_state["last_result"] = existing
        is_full = len(results) == 3 and total == 3
        save_workflow_state(
            root, execution="complete", current_stage=7, current_stage_label="Apply evidence gate and export results",
            completed_stages=[1, 2, 3, 4, 5, 6, 7], completed_at=existing["completed_at"],
            workflow_summary=("Full three-pair mission experiment completed" if is_full else f"{name} completed"),
            last_pair=name, last_pair_status=result.diagnostics.get("status", "UNKNOWN"),
            last_pair_json=str(json_path), last_pair_evidence=str(png_path),
            batch_summary=[{"pair": n, "status": r.diagnostics.get("status"), "matches": r.tentative_matches, "inliers": r.inliers,
                            "inlier_ratio": r.inlier_ratio, "coverage": r.coverage, "rmse_m": r.diagnostics.get("rmse_m")}
                           for n, r, _, _ in results],
        )
    return results
