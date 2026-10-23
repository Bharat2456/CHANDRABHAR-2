import type { RunResult } from './types'
import { makeZip } from './zip'
import { APP_VERSION } from './version'

const csvEsc = (v: unknown) => { const s = v == null ? '' : String(v); return /[",\n\r]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s }
const row = (a: unknown[]) => a.map(csvEsc).join(',')

export function metricsJson(r: RunResult): string {
  const { images: _i, ...rest } = r.payload as typeof r.payload & { images: unknown }
  return JSON.stringify({ schema: 'chandrabhar2.metrics/1', app_version: APP_VERSION, run_id: r.id, ...rest }, null, 2)
}

export function summaryCsv(r: RunResult): string {
  const p = r.payload; const m = p.metrics; const T = p.gate_thresholds; const lines = [row(['quantity', 'value', 'unit', 'threshold', 'criterion_met'])]
  const add = (q: string, v: unknown, u = '', th: unknown = '', ok: unknown = '') => lines.push(row([q, v, u, th, ok]))
  add('reference_product', p.ref.product_id); add('reference_sensor', p.ref.sensor); add('source_product', p.src.product_id); add('source_sensor', p.src.sensor)
  add('method', m.method); add('common_grid_gsd', m.target_gsd_m, 'm'); add('keypoints_reference', m.keypoints_ref); add('keypoints_source', m.keypoints_src)
  add('tentative_matches', m.tentative_matches, 'count', `>=${T.min_tentative_matches}`, m.tentative_matches >= T.min_tentative_matches)
  add('inliers', m.inliers, 'count', `>=${T.min_inliers}`, m.inliers >= T.min_inliers)
  add('inlier_ratio', m.inlier_ratio, 'fraction', `>=${T.min_inlier_ratio}`, m.inlier_ratio >= T.min_inlier_ratio)
  add('coverage_4x4', m.coverage, 'fraction', `>=${T.min_coverage}`, m.coverage >= T.min_coverage)
  add('rmse', m.rmse_px, 'px', `<=${T.max_rmse_px}`, m.rmse_px != null && m.rmse_px <= T.max_rmse_px); add('rmse', m.rmse_m, 'm'); add('median_error', m.median_error_px, 'px'); add('p95_error', m.p95_error_px, 'px')
  if (p.homography) { const h = p.homography; add('translation_x', h.tx_px, 'px'); add('translation_y', h.ty_px, 'px'); add('rotation', h.rotation_deg, 'deg'); add('scale_x', h.scale_x); add('scale_y', h.scale_y); add('shear', h.shear); add('perspective_h31', h.perspective_h31); add('perspective_h32', h.perspective_h32) }
  add('evidence_gate', p.status); add('gate_reasons', p.gate_reasons.join(';')); add('ground_truth_validation', p.claims.ground_truth_validation); add('elapsed', p.elapsed_s, 's')
  return lines.join('\n') + '\n'
}

export function correspondencesCsv(r: RunResult): string {
  const pt = r.payload.points; const lines = [row(['index', 'ref_x_gridpx', 'ref_y_gridpx', 'src_x_gridpx', 'src_y_gridpx', 'ransac_inlier', 'residual_gridpx'])]
  for (let i = 0; i < pt.ref.length; i++) lines.push(row([i, pt.ref[i][0], pt.ref[i][1], pt.src[i][0], pt.src[i][1], pt.inlier[i] === 1 ? 1 : 0, pt.residual_px[i] ?? '']))
  return lines.join('\n') + '\n'
}

/** Reproducible run manifest: every input identity, parameter and software version needed to repeat the run. */
export function manifestJson(r: RunResult): string {
  const p = r.payload
  const prod = (x: typeof p.ref) => ({ key: x.key, product_id: x.product_id, sensor: x.sensor, adapter: x.adapter, shape: x.shape, dtype: x.dtype, interleave: x.interleave, gsd_m: x.gsd_m, data_file: x.data_file, data_bytes: x.data_bytes, geometry_csv: x.geometry_csv, user_overrides: x.overrides ?? null, synthetic: x.synthetic, sha256_of_text_companions: r.hashes[x.key] ?? {} })
  return JSON.stringify({
    schema: 'chandrabhar2.manifest/1', app_version: APP_VERSION, run_id: r.id, finished_utc: p.finished_utc,
    software: { engine: p.engine, engine_bundle: 'see /engine/engine-bundle.json sha256 in application build', gate_thresholds: p.gate_thresholds },
    inputs: { reference: prod(p.ref), source: prod(p.src), selected_files: r.files },
    parameters: { user_config: r.config, engine_config: p.engine_config, memory_preset: r.limits },
    execution: { elapsed_s: p.elapsed_s, levels_attempted: p.levels.map((l) => ({ index: l.index, target_gsd_m: l.target_gsd_m, status: l.status, method: l.method, geographic_warp: l.geographic_warp })), matcher_paths: p.matcher_paths, geometry: p.geometry },
    outcome: { claims: p.claims, status: p.status, gate_reasons: p.gate_reasons, warnings: p.warnings, engine_reason: p.reason ?? null },
    statement: 'The evidence gate is an internal consistency test. Independent ground-truth validation is not established by this software.',
  }, null, 2)
}

export function download(name: string, data: Blob | string, mime = 'application/octet-stream') {
  const blob = typeof data === 'string' ? new Blob([data], { type: mime }) : data
  const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = name; a.rel = 'noopener'
  document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url), 30_000)
}

export const baseName = (r: RunResult) => `chandrabhar2_${r.payload.ref.sensor}-${r.payload.src.sensor}_${r.payload.finished_utc.replace(/[:]/g, '').slice(0, 15)}`

export async function buildZip(r: RunResult, evidencePng: Blob | null): Promise<Uint8Array> {
  const enc = new TextEncoder(); const b = baseName(r)
  const entries = [
    { name: `${b}/metrics.json`, data: enc.encode(metricsJson(r)) }, { name: `${b}/summary.csv`, data: enc.encode(summaryCsv(r)) },
    { name: `${b}/correspondences.csv`, data: enc.encode(correspondencesCsv(r)) }, { name: `${b}/manifest.json`, data: enc.encode(manifestJson(r)) },
  ]
  if (evidencePng) entries.push({ name: `${b}/evidence.png`, data: new Uint8Array(await evidencePng.arrayBuffer()) })
  return makeZip(entries)
}
