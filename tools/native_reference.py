"""Native-Python reference run used as the parity oracle for the WebAssembly engine.
Usage: python tools/native_reference.py <fixture_dir>  -> JSON on stdout"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app.web.bridge as b
from app.synthetic import build_archive, build_misc

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
print(json.dumps(out))
