"""Diagnostic probe (native CPython OR Pyodide): full-precision registration internals for parity analysis.
Usage: python tools/parity_probe.py <fixture_dir> [--build]   -> JSON on stdout (or returned as PROBE_JSON in Pyodide)"""
import hashlib, json, sys
from pathlib import Path
import numpy as np, cv2, scipy, shapely
try: sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # native run from a checkout
except NameError: pass                                               # Pyodide exec(): /engine is already on sys.path

def _remap_mode():
    """Which cv2.remap(INTER_LINEAR) behaviour this OpenCV has: 'fixed-point-1/32px' (<= 4.13) or 'exact-float-bilinear' (>= 5.0)."""
    H, W = 200, 240; yy0, xx0 = np.mgrid[0:H, 0:W]; sm = (120 + 60 * np.sin(xx0 / 11.0) + 50 * np.cos(yy0 / 7.0)).astype(np.float32)
    yy, xx = np.mgrid[0:150, 0:170].astype(np.float32); qx = (xx * 1.2 + 3.37 + 0.3 * np.sin(yy / 9)).astype(np.float32); qy = (yy * 1.1 - 2.21 + 0.2 * np.cos(xx / 7)).astype(np.float32)
    o = cv2.remap(sm, qx, qy, cv2.INTER_LINEAR).astype(np.float64); x0 = np.floor(qx).astype(int); y0 = np.floor(qy).astype(int); fx = qx - x0; fy = qy - y0
    g = lambda y, x: sm[y, x].astype(np.float64); ex = g(y0, x0) * (1 - fx) * (1 - fy) + g(y0, x0 + 1) * fx * (1 - fy) + g(y0 + 1, x0) * (1 - fx) * fy + g(y0 + 1, x0 + 1) * fx * fy
    m = (qx > 2) & (qx < W - 3) & (qy > 2) & (qy < H - 3); e = float(np.abs(o - ex)[m].max())
    return 'exact-float-bilinear' if e < 1e-3 else 'fixed-point-1/32px'
root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('/ws')
from app.synthetic import build_archive
from app.adapters import AdapterRegistry
from app.core.pipeline import Engine
if '--build' in sys.argv: build_archive(root)
f = {'OHRC': next(root.rglob('ch2_ohr*.xml')), 'TMC2': next(root.rglob('ch2_tmc*.xml'))}
a = AdapterRegistry.inspect(f['OHRC'], root=root); b = AdapterRegistry.inspect(f['TMC2'], root=root)
res = Engine(levels=(1.0,)).register(a, b, 'probe')
pr, ps = np.asarray(res.points_ref, np.float64), np.asarray(res.points_src, np.float64)
H = res.homography
# Re-fit with the SAME correspondences, to separate "different points" from "different fit"
H2, m2 = cv2.findHomography(ps.astype(np.float32), pr.astype(np.float32), cv2.RANSAC, 3.0, maxIters=10000, confidence=.995)
out = {'versions': {'numpy': np.__version__, 'cv2': cv2.__version__, 'scipy': scipy.__version__, 'shapely': shapely.__version__, 'py': sys.version.split()[0], 'platform': sys.platform},
       'opencv_remap_mode': _remap_mode(), 'cv_build_simd': [l.strip() for l in cv2.getBuildInformation().splitlines() if 'CPU/HW features' in l or 'Baseline' in l or 'Dispatched' in l][:3],
       'n_points': int(len(pr)), 'inliers': int(res.inliers), 'tentative': int(res.tentative_matches), 'rmse': res.rmse_px, 'ratio': res.inlier_ratio,
       'H': H.tolist(), 'H_refit_same_points': H2.tolist(), 'inlier_mask': np.asarray(res.inlier_mask, int).tolist(),
       'pts_ref': pr.tolist(), 'pts_src': ps.tolist(), 'kp': [int(res.keypoints_ref), int(res.keypoints_src)],
       'pts_sha256': hashlib.sha256(np.round(np.vstack([pr, ps]), 3).tobytes()).hexdigest(), 'grid': res.diagnostics.get('physical_grid_shape')}
PROBE_JSON = json.dumps(out)
if __name__ == '__main__': print(PROBE_JSON)
