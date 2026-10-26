"""Derivation of the native-vs-WASM transform-equivalence tolerance (reproducible, deterministic).

A homography is a *fitted* quantity: its coefficients have very different physical sensitivity (a 0.002 change in a
linear coefficient moves points by 0.002 x grid-size pixels) and the RANSAC fit itself has sampling uncertainty.  This
script measures, on the synthetic parity fixture:
  1. what a given coefficient error means as a worst-case displacement over the common grid, and
  2. the estimator's own uncertainty, by bootstrapping the engine's real correspondences.
Usage: python tools/parity_estimator_uncertainty.py [fixture_dir]
"""
import json, sys, tempfile
from pathlib import Path
import numpy as np, cv2
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.synthetic import build_archive
from app.adapters import AdapterRegistry
from app.core.pipeline import Engine

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(tempfile.mkdtemp(prefix='cb2-unc-'))
if not any(root.rglob('ch2_ohr*.xml')): build_archive(root)
a = AdapterRegistry.inspect(next(root.rglob('ch2_ohr*.xml')), root=root); b = AdapterRegistry.inspect(next(root.rglob('ch2_tmc*.xml')), root=root)
res = Engine(levels=(1.0,)).register(a, b, 'unc'); gh, gw = res.diagnostics['physical_grid_shape']
ps, pr = np.asarray(res.points_src, np.float32), np.asarray(res.points_ref, np.float32)
fit = lambda s, r: (lambda H: H / H[2, 2])(cv2.findHomography(s, r, cv2.RANSAC, 3.0, maxIters=10000, confidence=.995)[0])
H0 = fit(ps, pr)
C = np.array([[0, 0], [gw, 0], [0, gh], [gw, gh], [gw / 2, gh / 2]], np.float32).reshape(-1, 1, 2)
disp = lambda A, B: float(np.linalg.norm(cv2.perspectiveTransform(C, A) - cv2.perspectiveTransform(C, B), axis=2).max())
out = {'opencv': cv2.__version__, 'grid_hw': [gh, gw], 'n_correspondences': int(len(ps)), 'coefficient_error_to_displacement_px': {}}
for i, j in [(0, 0), (0, 1), (1, 0), (1, 1)]:
    B = H0.copy(); B[i, j] += 0.002; out['coefficient_error_to_displacement_px'][f'dA[{i}][{j}]=0.002'] = round(disp(H0, B), 3)
rng = np.random.default_rng(1); D, dA = [], []
for _ in range(500):
    idx = rng.integers(0, len(ps), len(ps))
    try: H = fit(ps[idx], pr[idx])
    except Exception: continue
    D.append(disp(H0, H)); dA.append(np.abs(H[:2, :2] - H0[:2, :2]).max())
D, dA = np.array(D), np.array(dA)
out['bootstrap_500'] = {'displacement_px': {'median': round(float(np.median(D)), 3), 'p95': round(float(np.percentile(D, 95)), 3)},
                        'max_abs_dA': {'median': float(np.median(dA)), 'p95': float(np.percentile(dA, 95))}, 'fraction_dA_ge_0.002': round(float(np.mean(dA >= 0.002)), 3)}
print(json.dumps(out, indent=2))
