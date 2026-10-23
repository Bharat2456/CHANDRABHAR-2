import { store, useStore } from '../state/store'
import { Icon, Badge, PageHead, Notice, Stat } from '../components/ui'
import type { RouteId } from '../components/Shell'
import { fmtNum, fmtInt, fmtPct, fmtSec, sensorKey, sensorLabel } from '../lib/format'
import { GATE_REASON_TEXT, ENGINE_REASON_TEXT, CLAIM_LABELS, LIMITATION_STATEMENT, WARNING_TEXT, PAIR_TEXT } from '../lib/copy'

export function Evidence({ go }: { go: (r: RouteId) => void }) {
  const id = useStore((s) => s.activeResultId); const results = useStore((s) => s.results); const saved = useStore((s) => s.savedRuns)
  const r = [...results, ...saved].find((x) => x.id === id) ?? results[0] ?? null
  if (!r) return (<><PageHead kicker="Step 4" title="Evidence & results" /><div className="empty"><h3>No results yet</h3><p className="small">Run a registration first.</p><p><button className="btn primary" onClick={() => go('registration')}>Go to registration</button></p></div></>)
  const p = r.payload; const m = p.metrics; const T = p.gate_thresholds; const h = p.homography; const pass = p.status === 'VALIDATED'
  const crit = [
    { k: 'Tentative matches', v: fmtInt(m.tentative_matches), t: `≥ ${T.min_tentative_matches}`, ok: m.tentative_matches >= T.min_tentative_matches },
    { k: 'RANSAC inliers', v: fmtInt(m.inliers), t: `≥ ${T.min_inliers}`, ok: m.inliers >= T.min_inliers },
    { k: 'Inlier ratio', v: fmtPct(m.inlier_ratio), t: `≥ ${fmtPct(T.min_inlier_ratio, 0)}`, ok: m.inlier_ratio >= T.min_inlier_ratio },
    { k: 'Spatial coverage (4×4 cells)', v: fmtPct(m.coverage, 0), t: `≥ ${fmtPct(T.min_coverage, 0)}`, ok: m.coverage >= T.min_coverage },
    { k: 'RMSE', v: m.rmse_px == null ? '—' : `${fmtNum(m.rmse_px, 3)} px${m.rmse_m != null ? ` (${fmtNum(m.rmse_m, 2)} m)` : ''}`, t: `≤ ${T.max_rmse_px} px`, ok: m.rmse_px != null && m.rmse_px <= T.max_rmse_px },
  ]
  const flags: string[] = []
  if (h) { if (Math.abs(h.scale_x - 1) > 0.05 || Math.abs(h.scale_y - 1) > 0.05) flags.push('Residual scale differs from 1 by more than 5% on a physically normalised grid; inspect the correspondences.'); if (Math.abs(h.rotation_deg) > 10) flags.push('Residual rotation above 10° after geographic warping is unusual.'); if (h.cond_affine > 1e3) flags.push('The affine part is ill-conditioned (near-degenerate transform).'); if (Math.abs(h.perspective_h31) > 1e-3 || Math.abs(h.perspective_h32) > 1e-3) flags.push('Non-trivial perspective terms were estimated.') }
  const paths = Object.entries(p.matcher_paths)
  return (
    <>
      <PageHead kicker="Step 4" title="Evidence & results"><p>What was computed, what the gate decided, and — separately — what has <i>not</i> been established.</p></PageHead>
      {results.length + saved.length > 1 && <label className="field" style={{ maxWidth: 420, marginBottom: 16 }}><span>Result</span><select value={r.id} onChange={(e) => store.setActive(e.target.value)}>{[...results, ...saved].map((x) => <option key={x.id} value={x.id}>{x.payload.ref.sensor} → {x.payload.src.sensor} · {x.payload.finished_utc}</option>)}</select></label>}
      <section className="panel" aria-labelledby="claims-h"><header><h2 id="claims-h">Four separate statements</h2><div className="row"><span className="chip" data-sensor={sensorKey(p.ref.sensor)}>{sensorLabel(p.ref.sensor)}</span>→<span className="chip" data-sensor={sensorKey(p.src.sensor)}>{sensorLabel(p.src.sensor)}</span>{p.ref.synthetic && <Badge tone="info" icon={false}>synthetic data</Badge>}</div></header>
        <div className="claims">
          <div className="claim"><span className="q">1 · {CLAIM_LABELS.processing}</span><Badge tone="ok">Yes</Badge><span className="d">The pipeline ran to completion in {fmtSec(p.elapsed_s)}.</span></div>
          <div className="claim"><span className="q">2 · {CLAIM_LABELS.transform}</span>{p.claims.transformation_estimated ? <Badge tone="ok">Estimated</Badge> : <Badge tone="bad">Not estimated</Badge>}<span className="d">{p.claims.transformation_estimated ? 'A homography was fitted to RANSAC inliers.' : (p.reason && ENGINE_REASON_TEXT[p.reason]) || 'No transform could be estimated.'}</span></div>
          <div className="claim"><span className="q">3 · {CLAIM_LABELS.gate}</span>{pass ? <Badge tone="ok">Passed</Badge> : <Badge tone="warn">Not passed · insufficient evidence</Badge>}<span className="d">{pass ? 'All configured criteria were met.' : `${p.gate_reasons.length} criterion/criteria not met.`}</span></div>
          <div className="claim"><span className="q">4 · {CLAIM_LABELS.truth}</span><Badge tone="mute">Not established</Badge><span className="d">Always reported as not established by this software.</span></div></div>
        <div style={{ marginTop: 12 }}><Notice tone="warn"><p>{LIMITATION_STATEMENT}</p>{p.ref.synthetic && <p><b>This run used synthetic demo imagery.</b> It demonstrates the pipeline on a known surface; it is not Chandrayaan-2 validation.</p>}</Notice></div></section>

      {!pass && <section className="panel" style={{ marginTop: 'var(--s-4)' }} aria-labelledby="why-h"><header><h2 id="why-h">Why the gate was not passed</h2></header><ul className="small" style={{ margin: 0, paddingLeft: 20 }}>{p.gate_reasons.map((c) => <li key={c}>{GATE_REASON_TEXT[c] ?? c}</li>)}{p.reason && <li>{ENGINE_REASON_TEXT[p.reason] ?? p.reason}</li>}</ul>
        <p className="small muted" style={{ marginTop: 8 }}>An insufficient-evidence result is a valid outcome: the data may be low-texture, poorly overlapping, or too different in modality for this method.</p></section>}

      <div className="grid g2" style={{ marginTop: 'var(--s-4)' }}>
        <section className="panel" aria-labelledby="gate-h"><header><h2 id="gate-h">Evidence-gate criteria</h2></header>
          <div className="tablewrap"><table><thead><tr><th>Criterion</th><th className="num">Measured</th><th className="num">Threshold</th><th>Result</th></tr></thead><tbody>{crit.map((c) => <tr key={c.k}><td>{c.k}</td><td className="num">{c.v}</td><td className="num">{c.t}</td><td>{c.ok ? <Badge tone="ok">Met</Badge> : <Badge tone="bad">Not met</Badge>}</td></tr>)}</tbody></table></div>
          <div className="grid g3" style={{ marginTop: 12 }}><Stat k="Keypoints ref" v={fmtInt(m.keypoints_ref)} /><Stat k="Keypoints src" v={fmtInt(m.keypoints_src)} /><Stat k="Median / P95" v={`${fmtNum(m.median_error_px, 2)} / ${fmtNum(m.p95_error_px, 2)}`} u="px" /></div></section>

        <section className="panel" aria-labelledby="tr-h"><header><h2 id="tr-h">Transformation diagnostics</h2></header>
          {h ? <><dl className="kv"><dt>Translation</dt><dd>{fmtNum(h.tx_px, 3)}, {fmtNum(h.ty_px, 3)} px ≈ {fmtNum(h.tx_px * (m.target_gsd_m ?? 0), 2)}, {fmtNum(h.ty_px * (m.target_gsd_m ?? 0), 2)} m</dd><dt>Rotation</dt><dd>{fmtNum(h.rotation_deg, 4)}°</dd><dt>Scale x / y</dt><dd>{fmtNum(h.scale_x, 5)} / {fmtNum(h.scale_y, 5)}</dd><dt>Shear</dt><dd>{fmtNum(h.shear, 5)}</dd><dt>Perspective h31/h32</dt><dd>{h.perspective_h31.toExponential(2)} / {h.perspective_h32.toExponential(2)}</dd><dt>det / cond (affine)</dt><dd>{fmtNum(h.det_affine, 5)} / {fmtNum(h.cond_affine, 2)}</dd></dl>
            <details style={{ marginTop: 8 }}><summary className="small">3×3 homography (source → reference, grid px)</summary><pre className="mono xs">{h.matrix.map((r) => r.map((v) => v.toFixed(6).padStart(12)).join(' ')).join('\n')}</pre></details>
            {flags.map((f) => <div key={f} style={{ marginTop: 8 }}><Notice tone="warn">{f}</Notice></div>)}
            <p className="xs faint" style={{ marginTop: 8 }}>On a correctly geographic-warped common grid, a faithful result is close to the identity; large values indicate residual misregistration (or a wrong match).</p></> : <p className="small muted">No transform was estimated.</p>}</section>
      </div>

      <div className="grid g2" style={{ marginTop: 'var(--s-4)' }}>
        <section className="panel" aria-labelledby="lv-h"><header><h2 id="lv-h">Scale cascade</h2></header>
          <div className="tablewrap"><table><thead><tr><th>Level</th><th className="num">GSD (m)</th><th className="num">Inliers/tent.</th><th className="num">RMSE px</th><th>Gate</th></tr></thead><tbody>{p.levels.map((l) => <tr key={l.index}><td>{l.index + 1}{l.geographic_warp ? ' · geo' : ''}</td><td className="num">{fmtNum(l.target_gsd_m, 2)}</td><td className="num">{l.inliers}/{l.tentative}</td><td className="num">{fmtNum(l.rmse_px, 2)}</td><td>{l.status === 'VALIDATED' ? <Badge tone="ok">Passed</Badge> : <Badge tone="warn">Not passed</Badge>}</td></tr>)}</tbody></table></div>
          <p className="xs faint" style={{ marginTop: 6 }}>The best level (by inlier ratio, inliers, coverage) is reported.</p></section>
        <section className="panel" aria-labelledby="mt-h"><header><h2 id="mt-h">Methods that actually ran</h2></header>
          <dl className="kv"><dt>Reported method</dt><dd>{m.method}</dd><dt>Overlap</dt><dd>{p.pair_geometry?.status ?? '—'}{p.pair_geometry?.area_km2 != null ? ` · ${fmtNum(p.pair_geometry.area_km2, 3)} km²` : ''}</dd><dt>Common grid</dt><dd>{p.grid ? `${p.grid.w}×${p.grid.h} px @ ${fmtNum(p.grid.target_gsd_m, 2)} m · ${p.grid.mode.replace('_', ' ')}` : '—'}</dd><dt>Tile matcher paths</dt><dd>{paths.length ? paths.map(([k, v]) => `${k}: ${v}`).join(', ') : '—'}</dd><dt>Engine</dt><dd>Python {p.engine.python} · NumPy {p.engine.numpy} · OpenCV {p.engine.opencv} · SciPy {p.engine.scipy} · Shapely {p.engine.shapely}</dd></dl>
          {p.warnings.length > 0 && <div className="stack" style={{ marginTop: 8 }}>{p.warnings.map((w) => <Notice key={w.code} tone="warn">{PAIR_TEXT[w.code] ?? WARNING_TEXT[w.code] ?? w.code}: <span className="mono xs">{w.detail}</span></Notice>)}</div>}</section>
      </div>
      <p style={{ marginTop: 16 }} className="row"><button className="btn" onClick={() => go('lab')}><Icon n="lab" />Open correspondence lab</button><button className="btn primary" onClick={() => go('reports')}><Icon n="download" />Export results</button></p>
    </>
  )
}
