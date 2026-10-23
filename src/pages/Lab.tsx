import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { store, useStore } from '../state/store'
import { Icon, PageHead, Stat, Badge } from '../components/ui'
import type { RouteId } from '../components/Shell'
import { renderEvidence, type Panels, type RenderOpts } from '../lib/evidenceRender'
import { fmtNum, fmtPct } from '../lib/format'
import type { RunResult } from '../lib/types'

export const CANVAS_THEME = { bg: '#05070a', text: '#e8edf4', muted: '#98a3b5', border: '#3a475a', ok: '#3fb950', bad: '#f85149', accent: '#f5a524' }

export function useBitmaps(r: RunResult | null) {
  const [p, setP] = useState<Panels>({ ref: null, src: null, aligned: null })
  useEffect(() => {
    let dead = false; setP({ ref: null, src: null, aligned: null }); if (!r) return
    ;(async () => { const get = async (k: string) => (r.images[k] ? createImageBitmap(r.images[k]) : null); const [ref, src, aligned] = await Promise.all([get('ref'), get('src'), get('src_aligned')]); if (!dead) setP({ ref, src, aligned }) })().catch(() => {})
    return () => { dead = true }
  }, [r])
  return p
}

export function Lab({ go }: { go: (r: RouteId) => void }) {
  const id = useStore((s) => s.activeResultId); const results = useStore((s) => s.results); const saved = useStore((s) => s.savedRuns)
  const r = useMemo(() => [...results, ...saved].find((x) => x.id === id) ?? results[0] ?? null, [id, results, saved])
  const panels = useBitmaps(r); const wrap = useRef<HTMLDivElement>(null); const cv = useRef<HTMLCanvasElement>(null)
  const [mode, setMode] = useState<'side' | 'overlay'>('side'); const [src, setSrc] = useState<'before' | 'after'>('after'); const [alpha, setAlpha] = useState(0.5)
  const [inl, setInl] = useState(true); const [out, setOut] = useState(true); const [lines, setLines] = useState(true)
  const [view, setView] = useState({ scale: 1, ox: 0, oy: 0 }); const [size, setSize] = useState({ w: 800, h: 480 }); const fitted = useRef<string>('')
  const g = r?.payload.grid

  const fit = useCallback(() => {
    if (!g) return; const panelW = mode === 'side' ? (size.w - 12) / 2 : size.w; const sc = Math.min(panelW / g.preview_w, size.h / g.preview_h)
    setView({ scale: sc, ox: (panelW - g.preview_w * sc) / 2, oy: (size.h - g.preview_h * sc) / 2 })
  }, [g, mode, size])
  useEffect(() => { const key = `${r?.id}|${mode}|${Math.round(size.w / 40)}`; if (fitted.current !== key) { fitted.current = key; fit() } }, [r?.id, mode, size, fit])
  useEffect(() => { const el = wrap.current; if (!el) return; const ro = new ResizeObserver(() => { const w = el.clientWidth; setSize({ w, h: Math.max(320, Math.min(640, Math.round(w * (window.innerWidth < 700 ? 0.9 : 0.56)))) }) }); ro.observe(el); return () => ro.disconnect() }, [])

  useEffect(() => {
    const c = cv.current; if (!c || !r) return; const dpr = Math.min(2, window.devicePixelRatio || 1); c.width = Math.round(size.w * dpr); c.height = Math.round(size.h * dpr)
    const ctx = c.getContext('2d')!; ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    const o: RenderOpts = { showInliers: inl, showOutliers: out, showLines: lines, scale: view.scale, ox: view.ox, oy: view.oy, mode, overlayAlpha: alpha, overlaySource: src, theme: CANVAS_THEME }
    renderEvidence(ctx, size.w, size.h, r.payload, panels, o)
  }, [r, panels, view, size, mode, src, alpha, inl, out, lines])

  // interactions: pointer pan, wheel zoom about the cursor, pinch, keyboard
  const ptrs = useRef(new Map<number, { x: number; y: number }>()); const pinch = useRef<number | null>(null)
  const zoomAt = (cx: number, cy: number, f: number) => setView((v) => { const panelW = mode === 'side' ? (size.w - 12) / 2 : size.w; const x = cx > panelW + 12 && mode === 'side' ? cx - panelW - 12 : cx; const ns = Math.max(0.05, Math.min(60, v.scale * f)); const k = ns / v.scale; return { scale: ns, ox: x - (x - v.ox) * k, oy: cy - (cy - v.oy) * k } })
  const rect = () => cv.current!.getBoundingClientRect()
  if (!r || !g) return (<><PageHead kicker="Step 3" title="Correspondence lab" /><div className="empty"><h3>No registration result yet</h3><p className="small">Run a registration to inspect correspondences here.</p><p><button className="btn primary" onClick={() => go('registration')}>Go to registration</button></p></div></>)
  const p = r.payload; const nIn = p.points.inlier.reduce((a, b) => a + b, 0); const nOut = p.points.ref.length - nIn
  const resid = p.points.residual_px.filter((_, i) => p.points.inlier[i] === 1); const maxR = Math.max(3, ...resid); const bins = Array.from({ length: 16 }, () => 0); resid.forEach((v) => { bins[Math.min(15, Math.floor((v / maxR) * 16))]++ }); const bmax = Math.max(1, ...bins)
  return (
    <>
      <PageHead kicker="Step 3" title="Correspondence lab"><p>Inspect what the matcher saw on the common grid. Panels pan and zoom together. Shapes differ so status never depends on colour: <b>ring = inlier</b>, <b>cross = outlier</b>.</p></PageHead>
      <div className="lab">
        <div className="stack">
          <div className="row between">
            <div className="row"><div className="seg" role="group" aria-label="View mode"><button aria-pressed={mode === 'side'} onClick={() => setMode('side')}>Side by side</button><button aria-pressed={mode === 'overlay'} onClick={() => setMode('overlay')}>Overlay</button></div>
              {mode === 'overlay' && <div className="seg" role="group" aria-label="Alignment"><button aria-pressed={src === 'before'} onClick={() => setSrc('before')}>Before alignment</button><button aria-pressed={src === 'after'} onClick={() => setSrc('after')} disabled={!panels.aligned}>After alignment</button></div>}</div>
            <div className="row"><button className="btn small" onClick={() => zoomAt(size.w / 4, size.h / 2, 1.25)} aria-label="Zoom in">+</button><button className="btn small" onClick={() => zoomAt(size.w / 4, size.h / 2, 0.8)} aria-label="Zoom out">−</button><button className="btn small" onClick={fit}>Fit</button></div></div>
          <div className="canvas-wrap" ref={wrap} style={{ height: size.h }}>
            <canvas ref={cv} tabIndex={0} role="img" aria-label={`Correspondence view: ${nIn} inliers and ${nOut} outliers between reference and source on the common grid. Arrow keys pan, plus and minus zoom, 0 resets.`} style={{ width: size.w, height: size.h }}
              onPointerDown={(e) => { (e.target as HTMLElement).setPointerCapture(e.pointerId); ptrs.current.set(e.pointerId, { x: e.clientX, y: e.clientY }) }}
              onPointerMove={(e) => { const m = ptrs.current.get(e.pointerId); if (!m) return; const dx = e.clientX - m.x, dy = e.clientY - m.y; m.x = e.clientX; m.y = e.clientY
                if (ptrs.current.size === 2) { const [a, b] = [...ptrs.current.values()]; const d = Math.hypot(a.x - b.x, a.y - b.y); if (pinch.current) { const rc = rect(); zoomAt((a.x + b.x) / 2 - rc.left, (a.y + b.y) / 2 - rc.top, d / pinch.current) } pinch.current = d }
                else setView((v) => ({ ...v, ox: v.ox + dx, oy: v.oy + dy })) }}
              onPointerUp={(e) => { ptrs.current.delete(e.pointerId); pinch.current = null }} onPointerCancel={(e) => { ptrs.current.delete(e.pointerId); pinch.current = null }}
              onWheel={(e) => { e.preventDefault(); const rc = rect(); zoomAt(e.clientX - rc.left, e.clientY - rc.top, e.deltaY < 0 ? 1.15 : 1 / 1.15) }}
              onKeyDown={(e) => { const st = 40; if (e.key === 'ArrowLeft') setView((v) => ({ ...v, ox: v.ox + st })); else if (e.key === 'ArrowRight') setView((v) => ({ ...v, ox: v.ox - st })); else if (e.key === 'ArrowUp') setView((v) => ({ ...v, oy: v.oy + st })); else if (e.key === 'ArrowDown') setView((v) => ({ ...v, oy: v.oy - st })); else if (e.key === '+' || e.key === '=') zoomAt(size.w / 4, size.h / 2, 1.25); else if (e.key === '-') zoomAt(size.w / 4, size.h / 2, 0.8); else if (e.key === '0') fit(); else return; e.preventDefault() }} />
            <span className="hint">drag · wheel · pinch · arrows</span></div>
          <div className="row between"><div className="legend"><span><svg width="14" height="14" aria-hidden="true"><circle cx="7" cy="7" r="5" fill="none" stroke="#3fb950" strokeWidth="2" /></svg>Inlier ({nIn})</span><span><svg width="14" height="14" aria-hidden="true"><path d="M2 2l10 10M12 2L2 12" stroke="#f85149" strokeWidth="2" /></svg>Outlier ({nOut})</span><span>solid line = inlier · dashed = outlier</span></div>
            <div className="row"><label className="check"><input type="checkbox" checked={inl} onChange={(e) => setInl(e.target.checked)} />Inliers</label><label className="check"><input type="checkbox" checked={out} onChange={(e) => setOut(e.target.checked)} />Outliers</label>{mode === 'side' && <label className="check"><input type="checkbox" checked={lines} onChange={(e) => setLines(e.target.checked)} />Lines</label>}</div></div>
          {mode === 'overlay' && <label className="field"><span>Source opacity: {Math.round(alpha * 100)}%</span><input type="range" min="0" max="1" step="0.05" value={alpha} onChange={(e) => setAlpha(Number(e.target.value))} /></label>}
          {p.points.total > p.points.shown && <p className="xs faint">Showing {p.points.shown} of {p.points.total} correspondences (evenly subsampled for display).</p>}
          <p className="xs faint">These panels show the engine’s normalised common-grid representation (percentile-stretched), not raw detector counts. Transparent areas are outside the swath intersection.</p>
        </div>
        <aside className="stack" aria-label="Diagnostics">
          <section className="panel"><header><h2>Alignment</h2><Badge tone={p.status === 'VALIDATED' ? 'ok' : 'warn'}>{p.status === 'VALIDATED' ? 'Gate passed' : 'Gate not passed'}</Badge></header>
            <div className="grid g2"><Stat k="Inliers" v={p.metrics.inliers} /><Stat k="Inlier ratio" v={fmtPct(p.metrics.inlier_ratio)} /><Stat k="RMSE" v={fmtNum(p.metrics.rmse_px, 2)} u="px" /><Stat k="Coverage" v={fmtPct(p.metrics.coverage, 0)} /></div>
            {p.homography && <dl className="kv" style={{ marginTop: 12 }}><dt>Shift</dt><dd>{fmtNum(p.homography.tx_px, 2)}, {fmtNum(p.homography.ty_px, 2)} px</dd><dt>Rotation</dt><dd>{fmtNum(p.homography.rotation_deg, 3)}°</dd><dt>Scale</dt><dd>{fmtNum(p.homography.scale_x, 4)} / {fmtNum(p.homography.scale_y, 4)}</dd></dl>}</section>
          <section className="panel"><header><h2>Inlier residuals</h2><span className="xs faint">0 – {maxR.toFixed(1)} px</span></header>
            {resid.length ? <div className="hist" role="img" aria-label={`Residual histogram of ${resid.length} inliers, maximum ${maxR.toFixed(2)} pixels`}>{bins.map((b, i) => <i key={i} style={{ height: `${(b / bmax) * 100}%` }} title={`${b}`} />)}</div> : <p className="small muted">No inliers.</p>}
            <p className="xs faint" style={{ marginTop: 6 }}>Residuals in common-grid pixels (1 px = {fmtNum(p.metrics.target_gsd_m, 2)} m).</p></section>
          <button className="btn" onClick={() => go('evidence')}>Open evidence summary<Icon n="chev" /></button>
        </aside>
      </div>
    </>
  )
}
