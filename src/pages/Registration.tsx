import { useEffect, useState } from 'react'
import { store, useStore } from '../state/store'
import { Icon, Badge, PageHead, Notice, Progress, Stat } from '../components/ui'
import type { RouteId } from '../components/Shell'
import { fmtNum, fmtInt, fmtSec, sensorKey, sensorLabel } from '../lib/format'
import { PAIR_TEXT, STAGE_TEXT } from '../lib/copy'
import { DEFAULT_LEVELS, DEFAULT_CONFIG } from '../lib/types'

const LEVEL_PRESETS: Record<string, number[]> = { cascade: DEFAULT_LEVELS, fast: [1.0, 2.5], single: [1.0] }

function useElapsed(start: number | null, on: boolean) { const [n, setN] = useState(0); useEffect(() => { if (!on || !start) return; const t = setInterval(() => setN(Date.now() - start), 500); return () => clearInterval(t) }, [on, start]); return n / 1000 }

export function Registration({ go }: { go: (r: RouteId) => void }) {
  const s = useStore((x) => x); const ins = s.inspection; const products = ins?.products ?? []
  const ref = products.find((p) => p.key === s.refKey), src = products.find((p) => p.key === s.srcKey)
  const running = s.run.status === 'running'; const elapsed = useElapsed(s.run.startedAt, running)
  const msgs = s.pair?.messages ?? []; const blocked = msgs.some((m) => m.tone === 'bad') || !ref || !src || s.engine.status !== 'ready'
  const preset = Object.entries(LEVEL_PRESETS).find(([, v]) => JSON.stringify(v) === JSON.stringify(s.config.levels))?.[0] ?? 'custom'
  const geo = s.pair?.geometry
  const sel = (label: string, value: string | null, set: (k: string | null) => void, other: string | null) => (
    <label className="field"><span>{label}</span><select value={value ?? ''} onChange={(e) => set(e.target.value || null)} disabled={running}>
      <option value="">Select a product…</option>{products.map((p) => <option key={p.key} value={p.key} disabled={p.key === other}>{sensorLabel(p.sensor)} · {p.product_id.slice(-34)} · {p.gsd_m ? p.gsd_m + ' m' : 'GSD?'}</option>)}</select></label>)
  useEffect(() => { void store.ensureEngine() }, [])
  const tileFrac = s.run.tiles ? (s.run.tile ?? 0) / s.run.tiles : null
  return (
    <>
      <PageHead kicker="Step 2" title="Image registration"><p>Pick a reference and a source. The engine builds a common physical grid from true swath geometry, then matches and verifies on that grid.</p></PageHead>
      {products.length < 2 ? <div className="empty"><h3>Two products are needed</h3><p className="small">Add products in the Data Workspace, or use the synthetic demo.</p><p><button className="btn primary" onClick={() => go('workspace')}>Open data workspace</button> <button className="btn" onClick={() => store.useDemo()}>Use synthetic demo</button></p></div> : (
        <div className="grid g-main">
          <div className="stack">
            <section className="panel" aria-labelledby="sel-h"><header><h2 id="sel-h">Products</h2><button className="btn small ghost" disabled={running || !ref || !src} onClick={() => store.setPair(s.srcKey, s.refKey)}>Swap</button></header>
              <div className="grid g2">{sel('Reference (fixed frame)', s.refKey, (k) => store.setPair(k, s.srcKey), s.srcKey)}{sel('Source (registered to reference)', s.srcKey, (k) => store.setPair(s.refKey, k), s.refKey)}</div>
              {ref && src && <div className="grid g2" style={{ marginTop: 12 }}>{[ref, src].map((p, i) => <dl key={p.key} className="kv"><dt>{i ? 'Source' : 'Reference'}</dt><dd><span className="chip" data-sensor={sensorKey(p.sensor)}>{sensorLabel(p.sensor)}</span></dd><dt>GSD</dt><dd>{p.gsd_m ? `${fmtNum(p.gsd_m, 3)} m` : 'missing'}</dd><dt>Pixels</dt><dd>{fmtInt(p.samples)} × {fmtInt(p.lines)}{p.bands > 1 ? ` × ${p.bands}` : ''}</dd><dt>Geometry</dt><dd>{p.geometry_csv ? 'swath table' : 'none'}</dd></dl>)}</div>}
            </section>

            <section className="panel" aria-labelledby="comp-h"><header><h2 id="comp-h">Pair compatibility</h2>{s.pairLoading && <Icon n="loader" spin />}</header>
              {!ref || !src ? <p className="small muted">Select both products.</p> : <div className="stack">
                {msgs.map((m, i) => <Notice key={i} tone={m.tone === 'bad' ? 'bad' : m.tone === 'warn' ? 'warn' : 'info'}>{PAIR_TEXT[m.code] ?? m.code}{m.ratio ? ` (${m.ratio.toFixed(0)}×)` : ''}{m.detail ? ` — ${m.detail}` : ''}</Notice>)}
                <div className="grid g3"><Stat k="GSD ratio" v={s.pair?.gsd_ratio ? `${s.pair.gsd_ratio.toFixed(2)}×` : '—'} title="coarser / finer" /><Stat k="Common grid base" v={s.pair?.common_gsd_base_m ? fmtNum(s.pair.common_gsd_base_m, 2) : '—'} u="m (coarser sensor)" />
                  <Stat k="Overlap" v={geo?.area_km2 != null ? fmtNum(geo.area_km2, geo.area_km2 < 1 ? 3 : 1) : '—'} u={geo?.area_km2 != null ? 'km²' : ''} /></div>
                <p className="small"><b>Overlap method:</b> {geo?.status === 'TRUE_SWATH_INTERSECTION' ? <Badge tone="ok">True swath intersection ({geo.vertices} vertices)</Badge> : geo ? <Badge tone="warn">{geo.status}</Badge> : '—'}</p>
                {geo?.grid_estimates && <details><summary className="small">Estimated grid size per cascade level</summary><div className="tablewrap"><table><thead><tr><th className="num">GSD (m)</th><th className="num">Pixels</th></tr></thead><tbody>{geo.grid_estimates.map((g) => <tr key={g.gsd_m}><td className="num">{fmtNum(g.gsd_m, 2)}</td><td className="num">{fmtInt(g.pixels)}</td></tr>)}</tbody></table></div><p className="xs faint">Estimates from polygon area; the engine caps grids at {fmtInt(s.preset.max_grid_pixels)} px under the “{s.preset.name}” memory preset. Run time is not predicted.</p></details>}
              </div>}
            </section>

            <section className="panel" aria-labelledby="run-h"><header><h2 id="run-h">Run</h2>
              {running ? <button className="btn danger" onClick={() => store.cancelRun()}><Icon n="stop" />Cancel run</button> : <button className="btn primary" disabled={blocked} onClick={() => store.runRegistration()} data-testid="run"><Icon n="play" />Run registration</button>}</header>
              {s.engine.status !== 'ready' && !running && <Notice tone="info">The engine is {s.engine.status === 'loading' ? 'loading…' : 'not ready'}.</Notice>}
              {running && <div className="stack" role="status" aria-live="polite" data-testid="progress">
                <div className="row between"><b>{STAGE_TEXT[s.run.stage ?? ''] ?? s.run.stage}{s.run.stage === 'matching_level' || s.run.stageLevel ? ` · level ${s.run.stageLevel ?? '?'} of up to ${s.run.levels ?? '?'}` : ''}</b><span className="mono small">{fmtSec(elapsed)}</span></div>
                <Progress value={tileFrac} label="Tile matching progress" />
                <p className="small muted">{s.run.tiles ? `Tile ${s.run.tile} of ${s.run.tiles} at ${fmtNum(s.run.gsd, 2)} m/px (${s.run.mode?.replace('_', ' ')})` : 'Preparing the common grid — exact progress for this step is not measurable, so the bar is indeterminate.'}</p>
                <p className="xs faint">The cascade stops early once a level passes the evidence gate, so the number of levels is an upper bound. Cancelling restarts the engine cleanly (a few seconds); your files stay selected.</p>
                <details><summary className="xs">Event log</summary><pre className="mono xs" style={{ maxHeight: 160, overflow: 'auto', margin: 0 }}>{s.run.log.map((l) => `${l.t.toFixed(1)}s  ${l.text}`).join('\n')}</pre></details></div>}
              {s.run.status === 'error' && s.run.error && <Notice tone="bad" title="The run failed"><p>{s.run.error.message}</p>{s.run.error.detail && <details><summary className="xs">Technical detail</summary><pre className="mono xs" style={{ whiteSpace: 'pre-wrap', maxHeight: 200, overflow: 'auto' }}>{s.run.error.detail}</pre></details>}<p className="small">Try: Conservative memory preset (Settings), a single-level cascade, or a smaller tile size. <button className="btn small" onClick={() => store.dismissRunError()}>Dismiss</button> {s.engine.status === 'error' && <button className="btn small" onClick={() => store.recoverEngine()}>Restart engine</button>}</p></Notice>}
              {s.run.status === 'cancelled' && <Notice tone="info">Run cancelled. No partial result was kept.</Notice>}
              {s.run.status === 'done' && <Notice tone="ok" title="Processing completed"><p>Review the outcome in <a href="#/evidence">Evidence &amp; Results</a> or inspect correspondences in the <a href="#/lab">Lab</a>. Completion does not imply the evidence gate passed.</p></Notice>}
            </section>
          </div>

          <aside className="stack" aria-label="Parameters">
            <section className="panel"><header><h2>Parameters</h2><button className="btn small ghost" onClick={() => store.setConfig({ ...DEFAULT_CONFIG })} disabled={running}>Defaults</button></header>
              <div className="stack">
                <label className="field"><span>Scale cascade</span><select disabled={running} value={preset} onChange={(e) => store.setConfig({ levels: LEVEL_PRESETS[e.target.value] ?? s.config.levels })}><option value="cascade">Full cascade (1, 1.5, 2.5, 4, 6 × base)</option><option value="fast">Two levels (1, 2.5 ×)</option><option value="single">Single level (1 ×)</option>{preset === 'custom' && <option value="custom">Custom</option>}</select><small>Multiples of the coarser sensor’s GSD. Stops at the first level that passes the gate.</small></label>
                <label className="field"><span>Tile size (px)</span><select disabled={running} value={s.config.tile_px} onChange={(e) => store.setConfig({ tile_px: Number(e.target.value) })}>{[256, 384, 512, 768].map((v) => <option key={v}>{v}</option>)}</select><small>Smaller tiles use less memory.</small></label>
                <label className="field"><span>Tile overlap: {Math.round(s.config.overlap * 100)}%</span><input type="range" min="0.1" max="0.4" step="0.05" value={s.config.overlap} disabled={running} onChange={(e) => store.setConfig({ overlap: Number(e.target.value) })} /></label>
                <label className="field"><span>SIFT ratio-test: {s.config.sift_ratio.toFixed(2)}</span><input type="range" min="0.6" max="0.9" step="0.01" value={s.config.sift_ratio} disabled={running} onChange={(e) => store.setConfig({ sift_ratio: Number(e.target.value) })} /><small>Lower = stricter, fewer ambiguous matches.</small></label>
                <label className="field"><span>RNG seed (recorded)</span><input type="number" value={s.config.seed} disabled={running} onChange={(e) => store.setConfig({ seed: Number(e.target.value) || 0 })} /><small>Recorded in the manifest. OpenCV’s RANSAC uses a fixed internal generator, so identical input gives identical output whatever this value is.</small></label>
              </div></section>
            <section className="panel"><header><h2>Evidence-gate thresholds</h2><Badge tone="mute" icon={false}>fixed</Badge></header>
              <dl className="kv">{Object.entries(s.engine.boot?.info.gate ?? {}).map(([k, v]) => <><dt key={k}>{k.replace(/_/g, ' ')}</dt><dd key={k + 'v'}>{String(v)}</dd></>)}</dl>
              <p className="xs faint" style={{ marginTop: 8 }}>Thresholds are not user-adjustable, so a result cannot be made to pass by loosening the test.</p></section>
          </aside>
        </div>)}
    </>
  )
}
