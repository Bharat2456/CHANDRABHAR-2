"""Render the real UI components in both themes to static HTML (+ optional screenshots).

This is a DESIGN PREVIEW, not the Streamlit app: Streamlit's native widgets are not drawn.
All values come from a small synthetic fixture (same idea as app/selftest.py) and are
labelled as such — they are not Chandrayaan-2 results.

Usage:  python tools/ui_preview.py [out_dir] [--shots]
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.adapters import AdapterRegistry  # noqa: E402
from app.core.pipeline import Engine  # noqa: E402
from ui import components as C  # noqa: E402
from ui.logic import humanize_reason, gate_reasons  # noqa: E402
from ui.theme import build_css, logo_data_uri  # noqa: E402
from ui.tokens import palette  # noqa: E402


def fixture_result():
    rng = np.random.default_rng(7)
    base = np.zeros((1200, 1200), np.uint8)
    for _ in range(80):
        x, y = rng.integers(30, 1170, 2)
        cv2.circle(base, (int(x), int(y)), int(rng.integers(3, 25)), int(rng.integers(80, 255)), -1)
    M = cv2.getRotationMatrix2D((600, 600), 4.0, 1.0); M[:, 2] += [12, -9]
    warped = cv2.warpAffine(base, M, (1200, 1200), borderMode=cv2.BORDER_REFLECT)
    with tempfile.TemporaryDirectory() as td:
        a, b = Path(td) / "a.npy", Path(td) / "b.npy"
        np.save(a, base); np.save(b, warped)
        sa, sb = AdapterRegistry.inspect(a), AdapterRegistry.inspect(b)
        sa.gsd_m = sb.gsd_m = 0.25
        return Engine(levels=(1.0,)).register(sa, sb, "synthetic")


ROWS = {
    "OHRC": {"product_id": "FIXTURE_ohrc_product", "shape": "(12000, 3000)", "dtype": "uint8", "gsd_m": 0.27,
             "solar_elevation_deg": 31.4, "solar_azimuth_deg": 112.0, "acquisition_start": "fixture", "crs": None, "geometry_table": True},
    "TMC2": {"product_id": "FIXTURE_tmc2_product", "shape": "(9000, 4000)", "dtype": "uint8", "gsd_m": 5.0,
             "solar_elevation_deg": 44.9, "solar_azimuth_deg": 98.2, "acquisition_start": "fixture", "crs": None, "geometry_table": True},
    "IIRS": {"product_id": "FIXTURE_iirs_product", "shape": "(32, 800, 250)", "dtype": "float32", "gsd_m": None,
             "solar_elevation_deg": None, "solar_azimuth_deg": None, "acquisition_start": None, "crs": None, "geometry_table": False},
}


def page(theme: str, res) -> str:
    p = palette(theme)
    cols = "".join(f'<div>{C.source_panel_html(ROWS.get(s), s)}</div>' for s in ("OHRC", "TMC2", "IIRS"))
    tiles = "".join(f'<div>{C.tile_html(l, v, n, t)}</div>' for l, v, n, t in [
        ("Candidate matches", f"{res.tentative_matches:,}", "tentative", ""), ("Geometric inliers", f"{res.inliers:,}", "RANSAC", ""),
        ("Inlier ratio", f"{res.inlier_ratio*100:.1f}%", "inliers / matches", ""), ("Spatial coverage", f"{res.coverage*100:.1f}%", "4×4 grid", ""),
        ("RMSE", f"{res.rmse_px:.3f} px", "", ""), ("Elapsed", f"{res.diagnostics.get('elapsed_s', 0):.1f} s", "", "")])
    failing = type("R", (), {"diagnostics": {"status": "INSUFFICIENT_EVIDENCE", "gate_reasons": ["too_few_inliers", "low_spatial_coverage"],
                                             "elapsed_s": 41.0}, "homography": None})()
    reasons = "".join(f"<div style='margin:4px 0'>{C.chip_html('Not met','warn')} {C.e(humanize_reason(q))}</div>" for q in gate_reasons(failing))
    stages = C.stages_html({1, 2, 3, 4}, 5, running=True)
    err = C.stages_html({1, 2}, 6, errored=True)
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{build_css(theme)}
body{{margin:0;padding:18px 22px;background:{p['bg']};color:{p['text']};font-family:var(--cb-font-sans)}}
.grid3{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}} .grid6{{display:grid;grid-template-columns:repeat(6,1fr);gap:10px;margin:10px 0}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:14px}} h4{{margin:14px 0 6px;color:var(--cb-muted);font-size:.72rem;letter-spacing:.12em;text-transform:uppercase}}
@media (max-width:900px){{.grid3,.grid2{{grid-template-columns:1fr}}.grid6{{grid-template-columns:repeat(2,1fr)}}}}
</style></head><body>
{C.header_html(logo_data_uri(), 'fixture-folder', theme, ('info', 'Data scanned'))}
<div class="cb-fixture">UI FIXTURE — synthetic data for visual design only. Not Chandrayaan-2 results; not scientific validation.</div>
<div class="cb-title" style="margin-top:12px">Data Workspace</div><div class="cb-sub">Mission products discovered from PDS4 labels in your local folder.</div>
<div class="grid3">{cols}</div>
<h4>Evidence status (engine result on synthetic fixture)</h4>{C.claims_html(res)}<div class="grid6">{tiles}</div>
<div class="grid2"><div><h4>Failing gate example (fixture)</h4>{C.claims_html(failing)}{C.panel_html('Gate interpretation', reasons)}</div>
<div><h4>Pipeline — running</h4>{stages}<h4>Pipeline — failed stage</h4>{err}<h4>Empty state</h4>{C.empty_html('Registration needs scanned mission data', ['Enter the mission-data folder in the sidebar.','Click <b>Scan mission data</b>.'])}</div></div>
</body></html>"""


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    out = Path(args[0] if args else "ui_preview_out"); out.mkdir(parents=True, exist_ok=True)
    res = fixture_result()
    for theme in ("dark", "light"):
        (out / f"preview_{theme}.html").write_text(page(theme, res), encoding="utf-8")
    print("wrote", [p.name for p in out.glob("*.html")])
    if "--shots" in sys.argv:
        from playwright.sync_api import sync_playwright
        chrome = next(Path.home().glob(".cache/puppeteer/chrome/*/chrome-linux64/chrome"), None)
        with sync_playwright() as pw:
            b = pw.chromium.launch(executable_path=str(chrome) if chrome else None, args=["--no-sandbox"])
            for theme in ("dark", "light"):
                for name, w in (("desktop", 1440), ("narrow", 640)):
                    pg = b.new_page(viewport={"width": w, "height": 900})
                    pg.goto((out / f"preview_{theme}.html").resolve().as_uri())
                    pg.screenshot(path=str(out / f"{theme}_{name}.png"), full_page=True)
            b.close()


if __name__ == "__main__":
    main()
