/**
 * Cross-implementation parity: the SAME Python engine, native CPython vs. WebAssembly (Pyodide), on identical synthetic fixtures.
 * Pixel reads must be bit-exact; registration results must agree within the tolerances stated below.
 */
import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { execFileSync } from 'node:child_process'
import { readFileSync, mkdtempSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { loadPyodide } from '../public/pyodide/pyodide.mjs'
import { bootEngine, type Py } from '../src/engine/boot'
import { maxDisplacement, coefficientDeltas } from './transformMetric'

/**
 * Two registrations of the same data are equivalent when the transforms they estimate move the common grid by less than this (grid px).
 * Derivation (tools/parity_estimator_uncertainty.py, synthetic fixture, 199x191 px grid): the former per-coefficient limit of 0.002
 * is 0.38-0.40 px of displacement; the estimator's own bootstrap sampling uncertainty is median 1.1 px / p95 2.5 px, so 0.5 px is
 * still well inside the resolution of the fit while being independent of grid size. The engine's own gate allows RMSE up to 2.5 px.
 */
const TRANSFORM_EQUIVALENCE_PX = 0.5

const ROOT = process.cwd()
let native: any; let py: Py; let bridge: Py; let wasm: any // eslint-disable-line @typescript-eslint/no-explicit-any
let ws: string

beforeAll(async () => {
  ws = mkdtempSync(join(tmpdir(), 'cb2-parity-'))
  native = JSON.parse(execFileSync(process.env.PYTHON ?? 'python3', ['tools/native_reference.py', ws], { cwd: ROOT, maxBuffer: 1 << 28 }).toString())
  const bundle = JSON.parse(readFileSync(join(ROOT, 'public/engine/engine-bundle.json'), 'utf8'))
  py = await bootEngine({ loadPyodide, indexURL: join(ROOT, 'public/pyodide') + '/', bundle })
  py.FS.mount(py.FS.filesystems.NODEFS, { root: ws }, '/ws')
  bridge = py.pyimport('app.web.bridge')
  const ins = JSON.parse(bridge.inspect_workspace())
  wasm = { ins }
  wasm.run = JSON.parse(bridge.run_registration(native.ref_key, native.src_key, JSON.stringify({ levels: [1.0] }), () => {}))
  wasm.self = JSON.parse(bridge.run_selftest())
})

afterAll(() => {
  // Evidence record of the measured comparison (committed as docs/evidence/parity.json by the maintainer when re-run).
  const a = wasm.run, b = native.registration
  writeFileSync(join(ROOT, 'tests-web', 'parity-result.json'), JSON.stringify({
    measured_utc: new Date().toISOString(), data: 'synthetic fixtures (app/synthetic.py), levels=[1.0]',
    native: { env: native.env, metrics: b.metrics, homography: b.homography, selftest: native.selftest },
    wasm: { engine: JSON.parse(bridge.engine_info()), metrics: a.metrics, homography: a.homography.matrix, selftest: wasm.self },
    pixel_windows_compared: Object.keys(native.hashes).length * 2,
    transform_displacement_px: maxDisplacement(a.homography.matrix, b.homography, a.grid.w, a.grid.h), coefficient_deltas: coefficientDeltas(a.homography.matrix, b.homography),
    deltas: { inliers: a.metrics.inliers - b.metrics.inliers, rmse_px: a.metrics.rmse_px - b.metrics.rmse_px, tx_px: a.homography.matrix[0][2] - b.homography[0][2], ty_px: a.homography.matrix[1][2] - b.homography[1][2] },
  }, null, 2))
})

describe('native CPython vs WebAssembly engine', () => {
  it('runs the same engine versions family (platform differs, API identical)', () => { const info = JSON.parse(bridge.engine_info()); expect(info.platform).toBe('emscripten'); expect(info.io_backend).toBe('stream'); expect(info.gate).toEqual({ min_tentative_matches: 8, min_inliers: 12, min_inlier_ratio: 0.35, min_coverage: 0.35, max_rmse_px: 2.5, ransac_reproj_px: 3 }) })
  it('detects identical products with identical metadata', () => {
    const got = Object.fromEntries(wasm.ins.products.map((p: any) => [p.key, { sensor: p.sensor, gsd_m: p.gsd_m, shape: p.shape, dtype: p.dtype, interleave: p.interleave, adapter: p.adapter, geometry_csv: p.geometry_csv, lines: p.lines, samples: p.samples }]))
    expect(got).toEqual(native.products)
  })
  it('reads bit-identical pixels for every format (pds4, envi BIL big-endian, npy, raw BIP)', () => {
    for (const [key, hs] of Object.entries<string[]>(native.hashes)) {
      const p = wasm.ins.products.find((x: any) => x.key === key); const H = p.lines, W = p.samples
      expect([bridge.window_sha256(key, 0, Math.min(H, 40), 0, Math.min(W, 50), 0), bridge.window_sha256(key, Math.floor(H / 3), Math.min(H, Math.floor(H / 3) + 17), Math.floor(W / 5), Math.min(W, Math.floor(W / 5) + 29), 0)]).toEqual(hs)
    }
  })
  it('geometry intersection agrees', () => { expect(wasm.run.pair_geometry.status).toBe(native.registration.geometry_status); expect(wasm.run.pair_geometry.area_km2).toBeCloseTo(native.registration.area_km2, 6) })
  it('common grid is identical', () => { expect(wasm.run.grid.h).toBe(native.registration.grid.h); expect(wasm.run.grid.w).toBe(native.registration.grid.w); expect(wasm.run.grid.target_gsd_m).toBeCloseTo(native.registration.grid.target_gsd_m, 9) })
  it('evidence-gate outcome is identical and ground truth stays not established', () => { expect(wasm.run.status).toBe(native.registration.status); expect(wasm.run.claims.ground_truth_validation).toBe('NOT_ESTABLISHED') })
  it('registration metrics agree within tolerance (OpenCV minor-version / FP differences)', () => {
    const a = wasm.run.metrics, b = native.registration.metrics
    expect(Math.abs(a.inliers - b.inliers) / b.inliers).toBeLessThan(0.15); expect(Math.abs(a.tentative_matches - b.tentative_matches) / b.tentative_matches).toBeLessThan(0.15)
    expect(Math.abs(a.rmse_px - b.rmse_px)).toBeLessThan(0.25); expect(Math.abs(a.coverage - b.coverage)).toBeLessThan(0.1)
  })
  it(`estimated transforms are equivalent: worst-case displacement over the common grid < ${TRANSFORM_EQUIVALENCE_PX} px`, () => {
    const A = wasm.run.homography.matrix, B = native.registration.homography
    const d = maxDisplacement(A, B, wasm.run.grid.w, wasm.run.grid.h)
    // Everything needed to diagnose a future failure from the CI log alone (no re-run required):
    const ctx = JSON.stringify({ displacement_px: d, grid_wh: [wasm.run.grid.w, wasm.run.grid.h], coefficient_deltas: coefficientDeltas(A, B), native_env: native.env,
      wasm_env: JSON.parse(bridge.engine_info()), inliers: [native.registration.metrics.inliers, wasm.run.metrics.inliers], tentative: [native.registration.metrics.tentative_matches, wasm.run.metrics.tentative_matches],
      keypoints: [[native.registration.metrics.keypoints_ref, native.registration.metrics.keypoints_src], [wasm.run.metrics.keypoints_ref, wasm.run.metrics.keypoints_src]], H_native: B, H_wasm: A }, null, 1)
    expect(d, ctx).toBeLessThan(TRANSFORM_EQUIVALENCE_PX)
  })
  it('recovers the known synthetic geometry (near-identity on the common grid)', () => { const m = wasm.run.homography; expect(Math.abs(m.tx_px)).toBeLessThan(1); expect(Math.abs(m.ty_px)).toBeLessThan(1); expect(Math.abs(m.rotation_deg)).toBeLessThan(0.5) })
  it('self-test (known-transform check) passes in WebAssembly and natively', () => { expect(wasm.self.passed).toBe(true); expect(native.selftest.passed).toBe(true); expect(wasm.self.known_transform_error_px).toBeLessThan(1.5); expect(Math.abs(wasm.self.known_transform_error_px - native.selftest.known_transform_error_px)).toBeLessThan(0.3) })
  it('repeat run on identical input => identical result in WebAssembly (reproducible)', () => {
    const again = JSON.parse(bridge.run_registration(native.ref_key, native.src_key, JSON.stringify({ levels: [1.0] }), () => {}))
    expect(again.metrics.inliers).toBe(wasm.run.metrics.inliers); expect(again.homography.matrix).toEqual(wasm.run.homography.matrix)
  })
  it('path traversal in a label cannot read outside the workspace (virtual FS)', () => {
    py.runPython(`
import os, pathlib
from app.adapters import AdapterRegistry
ws = pathlib.Path('/ws'); lab = next(ws.rglob('ch2_ohr*.xml'))
orig = lab.read_text()
os.makedirs('/tmp/x', exist_ok=True); open('/tmp/x/evil.xml','w').write(orig.replace('.img</file_name>', '../../../../etc/passwd</file_name>').replace('ch2_ohr_ncp_synth_20210101t0000000000_d_img_d18', '../../../../etc/passwd'))
try:
    AdapterRegistry.inspect(pathlib.Path('/tmp/x/evil.xml'), root=pathlib.Path('/tmp/x')); raise SystemExit('traversal was NOT blocked')
except ValueError: pass
`)
  })
})
