"""Native-Python reference run used as the parity oracle for the WebAssembly engine.
Usage: python tools/native_reference.py <fixture_dir>  -> JSON on stdout"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app.web.bridge as b
import numpy, numpy as np, cv2, scipy, shapely, platform
from app.synthetic import build_archive, build_misc


def _remap_mode():
    """Which cv2.remap(INTER_LINEAR) behaviour this OpenCV has: 'fixed-point-1/32px' (<= 4.13) or 'exact-float-bilinear' (>= 5.0)."""
    H, W = 200, 240; yy0, xx0 = np.mgrid[0:H, 0:W]; sm = (120 + 60 * np.sin(xx0 / 11.0) + 50 * np.cos(yy0 / 7.0)).astype(np.float32)
    yy, xx = np.mgrid[0:150, 0:170].astype(np.float32); qx = (xx * 1.2 + 3.37 + 0.3 * np.sin(yy / 9)).astype(np.float32); qy = (yy * 1.1 - 2.21 + 0.2 * np.cos(xx / 7)).astype(np.float32)
    o = cv2.remap(sm, qx, qy, cv2.INTER_LINEAR).astype(np.float64); x0 = np.floor(qx).astype(int); y0 = np.floor(qy).astype(int); fx = qx - x0; fy = qy - y0
    g = lambda y, x: sm[y, x].astype(np.float64); ex = g(y0, x0) * (1 - fx) * (1 - fy) + g(y0, x0 + 1) * fx * (1 - fy) + g(y0 + 1, x0) * (1 - fx) * fy + g(y0 + 1, x0 + 1) * fx * fy
    m = (qx > 2) & (qx < W - 3) & (qy > 2) & (qy < H - 3); e = float(np.abs(o - ex)[m].max())
    return 'exact-float-bilinear' if e < 1e-3 else 'fixed-point-1/32px'

root = Path(sys.argv[1]); root.mkdir(parents=True, exist_ok=True)
build_archive(root); build_misc(root / 'misc')
b.ROOTS['user'] = str(root); b.ROOTS['demo'] = str(root / '__none__')
ins = json.loads(b.inspect_workspace())
out = {'products': {p['key']: {k: p[k] for k in ('sensor', 'gsd_m', 'shape', 'dtype', 'interleave', 'adapter', 'geometry_csv', 'lines', 'samples')} for p in ins['products']}, 'hashes': {}}
for p in ins['products']:
    H, W = p['lines'], p['samples']
    out['hashes'][p['key']] = [b.window_sha256(p['key'], 0, min(H, 40), 0, min(W, 50), 0), b.window_sha256(p['key'], H // 3, min(H, H // 3 + 17), W // 5, min(W, W // 5 + 29), 0)]
pds = sorted([p['key'] for p in ins['products'] if p['adapter'] == 'pds4'])
ohrc = [k for k in pds if '/ohrc/' in k or k.startswith('user:ohrc')][0]; tmc = [k for k in pds if 'tmc2' in k][0]
r = json.loads(b.run_registration(ohrc, tmc, json.dumps({'levels': [1.0]}), lambda s: None))
out['ref_key'], out['src_key'] = ohrc, tmc
out['registration'] = {'status': r['status'], 'metrics': r['metrics'], 'homography': r['homography']['matrix'], 'grid': r['grid'], 'geometry_status': r['pair_geometry']['status'], 'area_km2': r['pair_geometry']['area_km2']}
out['selftest'] = json.loads(b.run_selftest())
out['env'] = {'python': platform.python_version(), 'numpy': numpy.__version__, 'opencv': cv2.__version__, 'opencv_remap_mode': _remap_mode(), 'scipy': scipy.__version__, 'shapely': shapely.__version__, 'platform': platform.platform(),
              'opencv_cpu_features': [l.strip() for l in cv2.getBuildInformation().splitlines() if 'Baseline' in l or 'Dispatched' in l][:2]}
print(json.dumps(out))
