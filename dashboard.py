"""CHANDRABHAR-2 | LUNAR INTELLIGENCE INTERFACE — Streamlit entry point.

Thin application shell: theme, mission header, sidebar workspace controls and navigation.
Presentation lives in ``ui/``; the scientific engine in ``app/`` is untouched.
"""
from __future__ import annotations

import time
from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="CHANDRABHAR-2 — Lunar Intelligence Interface",
    page_icon="branding/favicon.png" if Path("branding/favicon.png").exists() else "🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

from ui import components as C  # noqa: E402
from ui import pages as P  # noqa: E402
from ui.data import scan_products  # noqa: E402
from ui.state import load_workflow_state, reset_workflow_state  # noqa: E402
from ui.theme import inject, logo_data_uri  # noqa: E402


@st.cache_data(show_spinner=False)
def inventory(root_str: str):
    return scan_products(root_str)


def _do_scan(root: Path, root_str: str) -> None:
    st.cache_data.clear()
    with st.spinner("Scanning mission data…"):
        rows, errors = inventory(root_str)
    st.session_state.update(scanned=True, scanned_root=root_str, scan_time=time.strftime("%H:%M:%S"),
                            scan_count=len(rows), scan_errors=len(errors))
    if root.exists():
        reset_workflow_state(root, execution="idle", completed_stages=[1, 2], current_stage=0,
                             current_stage_label="Ready for correspondence", scan_time=st.session_state["scan_time"],
                             scan_count=len(rows), workflow_summary="Mission data scanned; ready to run correspondence")


def main() -> None:
    theme = inject()

    with st.sidebar:
        st.markdown("### Mission workspace")
        root_str = st.text_input("Mission-data root", "", help="Folder containing the OHRC, TMC2 and IIRS mission products.")
        root = Path(root_str)
        if st.session_state.get("scanned_root") != root_str:
            st.session_state["scanned"] = False
        prior = load_workflow_state(root) if root.exists() and root_str else {}
        has_prior = prior.get("execution") == "complete"
        if st.button("Scan mission data", type="primary", width="stretch",
                     help="Read the local mission labels and discover supported Chandrayaan-2 products."):
            if has_prior and st.session_state.get("scanned"):
                st.session_state["confirm_rescan"] = True
            else:
                _do_scan(root, root_str)
        if st.session_state.get("confirm_rescan"):
            st.warning("A completed run is recorded for this folder. Rescanning resets its saved workflow state "
                       "(exported files are kept).")
            c1, c2 = st.columns(2)
            if c1.button("Rescan", width="stretch"):
                st.session_state["confirm_rescan"] = False
                _do_scan(root, root_str)
                st.rerun()
            if c2.button("Cancel", width="stretch"):
                st.session_state["confirm_rescan"] = False
                st.rerun()
        if not root_str:
            st.info("Enter a folder path to begin.")
        elif not root.exists():
            st.error("Mission-data folder not found")
        elif st.session_state.get("scanned") and st.session_state.get("scanned_root") == root_str:
            st.success(f"Connected • {st.session_state.get('scan_count', 0)} supported product(s)")
            if st.session_state.get("scan_errors"):
                st.warning(f"{st.session_state['scan_errors']} label(s) could not be read")
            st.caption(f"Last scan: {st.session_state.get('scan_time', '—')}")
        else:
            st.info("Ready — click **Scan mission data**.")
        st.caption("Your Chandrayaan-2 files stay on this computer. CHANDRABHAR-2 does not upload them.")
        st.divider()
        st.checkbox("Show scientific diagnostics", value=st.session_state.get("diag", True), key="diag",
                    help="Show the detailed evidence-gate and algorithm diagnostics for technical review.")

    scanned = bool(st.session_state.get("scanned") and st.session_state.get("scanned_root") == root_str and root_str)
    rows, errors = inventory(root_str) if scanned else ([], [])
    st.session_state["_ctx"] = {"root": root, "root_str": root_str, "rows": rows, "errors": errors,
                                "scanned": scanned, "diag": st.session_state.get("diag", True)}

    last = st.session_state.get("last_result")
    if last:
        app_state = {"ok": ("ok", "Gate passed"), "warn": ("warn", "Insufficient evidence")}.get(
            C.gate_status_tone(last["result"].diagnostics.get("status"))[0], ("mute", "Result ready"))
    elif scanned:
        app_state = ("info", "Data scanned")
    else:
        app_state = ("mute", "Idle")
    C.md(C.header_html(logo_data_uri(), root.name if root_str else "no folder selected", theme, app_state))

    nav = st.navigation([
        st.Page(P.overview_page, title="Mission Overview", icon=":material/public:", default=True, url_path="overview"),
        st.Page(P.data_page, title="Data Workspace", icon=":material/satellite_alt:", url_path="data"),
        st.Page(P.registration_page, title="Image Registration", icon=":material/compare:", url_path="registration"),
        st.Page(P.evidence_page, title="Evidence & Results", icon=":material/fact_check:", url_path="evidence"),
        st.Page(P.reports_page, title="Reports & Export", icon=":material/inventory_2:", url_path="reports"),
    ])
    nav.run()


main()
