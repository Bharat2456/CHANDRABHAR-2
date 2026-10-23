import { useState } from 'react'
import { store, useStore } from '../state/store'
import { Icon, PageHead, Notice } from '../components/ui'
import type { RouteId } from '../components/Shell'
import { metricsJson, summaryCsv, correspondencesCsv, manifestJson, download, baseName, buildZip } from '../lib/exporters'
import { renderEvidencePng } from '../lib/evidenceRender'
import { CANVAS_THEME, useBitmaps } from './Lab'
import { useMemo } from 'react'

export function Reports({ go }: { go: (r: RouteId) => void }) {
  const id = useStore((s) => s.activeResultId); const results = useStore((s) => s.results); const saved = useStore((s) => s.savedRuns)
  const r = useMemo(() => [...results, ...saved].find((x) => x.id === id) ?? results[0] ?? null, [id, results, saved])
  const panels = useBitmaps(r); const [busy, setBusy] = useState(false)
  if (!r) return (<><PageHead kicker="Step 5" title="Reports & export" /><div className="empty"><h3>Nothing to export yet</h3><p className="small">Complete a registration first. Exports are created on your device; nothing is sent anywhere.</p><p><button className="btn primary" onClick={() => go('registration')}>Go to registration</button></p></div></>)
  const b = baseName(r); const png = async () => renderEvidencePng(r.payload, panels, CANVAS_THEME, `CHANDRABHAR-2 · ${r.payload.ref.sensor} → ${r.payload.src.sensor}`)
  const guard = async (f: () => Promise<void> | void) => { setBusy(true); try { await f() } catch (e) { store.toast('bad', `Export failed: ${(e as Error).message}`) } finally { setBusy(false) } }
  const items = [
    { t: 'Metrics (JSON)', d: 'All metrics, gate outcome, diagnostics, levels, correspondences and engine versions.', f: () => download(`${b}_metrics.json`, metricsJson(r), 'application/json') },
    { t: 'Summary (CSV)', d: 'One row per quantity with unit, threshold and whether each criterion was met.', f: () => download(`${b}_summary.csv`, summaryCsv(r), 'text/csv') },
    { t: 'Correspondences (CSV)', d: 'Every displayed correspondence in common-grid pixels with inlier flag and residual.', f: () => download(`${b}_correspondences.csv`, correspondencesCsv(r), 'text/csv') },
    { t: 'Evidence image (PNG)', d: 'Side-by-side correspondence view with a text legend. Status is shown by shape and text, not colour alone.', f: async () => download(`${b}_evidence.png`, await png()) },
    { t: 'Run manifest (JSON)', d: 'Inputs (names, sizes, SHA-256 of labels and geometry), parameters, software versions, warnings.', f: () => download(`${b}_manifest.json`, manifestJson(r), 'application/json') },
  ]
  return (
    <>
      <PageHead kicker="Step 5" title="Reports & export"><p>Downloads are generated in this browser and saved directly to your device. No account is required.</p></PageHead>
      <div className="grid g-main">
        <section className="panel" aria-labelledby="ex-h"><header><h2 id="ex-h">Individual files</h2></header>
          <div className="stack">{items.map((i) => <div key={i.t} className="row between" style={{ borderBottom: '1px solid var(--border)', paddingBottom: 12 }}><div style={{ flex: '1 1 260px', minWidth: 0 }}><b>{i.t}</b><p className="small muted" style={{ margin: 0 }}>{i.d}</p></div><button className="btn" disabled={busy} onClick={() => guard(i.f)}><Icon n="download" />Download</button></div>)}</div>
          <div style={{ marginTop: 16 }}><button className="btn primary" disabled={busy} onClick={() => guard(async () => download(`${b}.zip`, new Blob([(await buildZip(r, await png())) as BlobPart], { type: 'application/zip' })))}><Icon n="download" />Download everything (.zip)</button></div></section>
        <aside className="stack"><section className="panel"><header><h2>Manifest preview</h2></header><pre className="mono xs" style={{ maxHeight: 360, overflow: 'auto', margin: 0, whiteSpace: 'pre-wrap' }}>{manifestJson(r).slice(0, 2600)}…</pre></section>
          <Notice tone="warn">Every export states that the evidence gate is an internal consistency test and that independent ground-truth validation is not established.</Notice>
          {r.payload.ref.synthetic && <Notice tone="info">This result came from synthetic demo imagery and is labelled as such in the exports.</Notice>}</aside>
      </div>
    </>
  )
}
