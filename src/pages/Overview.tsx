import { store, useStore } from '../state/store'
import { Icon, Badge, PageHead, Stat } from '../components/ui'
import type { RouteId } from '../components/Shell'
import { SUBTITLE, PRIVACY_STATEMENT, LIMITATION_STATEMENT } from '../lib/copy'
import { fmtBytes, fmtNum, sensorKey, sensorLabel } from '../lib/format'

const STEPS = [
  ['Parse products', 'PDS4 labels, ENVI headers, NumPy arrays, raw + sidecar.'], ['Geographic overlap', 'True swath-polygon intersection, not a bounding box.'],
  ['Common physical grid', 'Shared lunar grid at a physically meaningful GSD.'], ['Normalise representations', 'Sensor- and illumination-aware.'],
  ['Match features', 'SIFT → phase correlation → ECC cascade.'], ['Verify geometry', 'RANSAC homography with outlier rejection.'],
  ['Evidence gate', 'Explicit thresholds; failure reasons kept.'], ['Export', 'JSON, CSV, PNG and a run manifest.'],
]

export function Overview({ go }: { go: (r: RouteId) => void }) {
  const s = useStore((x) => x)
  const products = s.inspection?.products.length ?? 0
  const recent = [...s.results, ...s.savedRuns]
  return (
    <>
      <PageHead kicker="Mission overview" title="Lunar image registration workspace"><p>{SUBTITLE}.</p></PageHead>
      <div className="grid g-main">
        <section className="panel" aria-labelledby="start-h">
          <header><h2 id="start-h">Start here</h2></header>
          <p>Select Chandrayaan-2 products from your device, choose a reference and a source, and run the registration pipeline. Everything runs in this tab — the scientific engine is the project’s own Python code, compiled to WebAssembly.</p>
          <div className="row">
            <button className="btn primary" onClick={() => go('workspace')}><Icon n="folder" />Open data workspace</button>
            <button className="btn" onClick={async () => { await store.useDemo(); go('registration') }}><Icon n="play" />Try the synthetic demo</button>
          </div>
          <p className="xs faint" style={{ marginTop: 12 }}>The demo generates synthetic imagery with known geometry. It exercises the full pipeline but is <b>not</b> mission data and says nothing about mission accuracy.</p>
        </section>
        <section className="panel" aria-labelledby="ws-h">
          <header><h2 id="ws-h">Workspace status</h2><Badge tone={s.engine.status === 'ready' ? 'ok' : s.engine.status === 'error' ? 'bad' : 'mute'}>{s.engine.status === 'ready' ? 'Engine ready' : s.engine.status === 'loading' ? 'Engine loading' : s.engine.status === 'error' ? 'Engine error' : 'Engine not started'}</Badge></header>
          <div className="grid g2"><Stat k="Files selected" v={s.files.length} /><Stat k="Products found" v={products} /><Stat k="Size on device" v={fmtBytes(s.files.reduce((a, f) => a + f.size, 0))} /><Stat k="Session results" v={s.results.length} /></div>
          {s.engine.error && <p className="small crit-bad" style={{ marginTop: 8 }}>{s.engine.error}</p>}
        </section>
      </div>

      <section className="panel" style={{ marginTop: 'var(--s-4)' }} aria-labelledby="wf-h"><header><h2 id="wf-h">Scientific workflow</h2><span className="xs faint">executed by the real engine, in this order</span></header>
        <ol className="pipeline">{STEPS.map(([t, d]) => <li key={t}><b>{t}</b><span>{d}</span></li>)}</ol></section>

      <div className="grid g2" style={{ marginTop: 'var(--s-4)' }}>
        <section className="panel" aria-labelledby="sup-h"><header><h2 id="sup-h">Supported sensors &amp; formats</h2></header>
          <div className="tablewrap"><table><thead><tr><th>Sensor</th><th>Role</th><th className="num">Typical GSD</th></tr></thead><tbody>
            <tr><td><span className="chip" data-sensor="ohrc">OHRC</span></td><td>Optical high-resolution camera</td><td className="num">≈ 0.25 m</td></tr>
            <tr><td><span className="chip" data-sensor="tmc2">TMC-2</span></td><td>Terrain mapping camera</td><td className="num">≈ 5 m</td></tr>
            <tr><td><span className="chip" data-sensor="iirs">IIRS</span></td><td>Imaging infrared spectrometer</td><td className="num">≈ 60–90 m</td></tr></tbody></table></div>
          <p className="small muted" style={{ marginTop: 12 }}>Formats: PDS4 XML + binary (+ ISRO geometry CSV), ENVI header + binary, NumPy <code>.npy</code>, raw binary with JSON sidecar. GSD is read from labels; it is never guessed.</p></section>
        <section className="panel" aria-labelledby="rec-h"><header><h2 id="rec-h">Recent results</h2></header>
          {recent.length === 0 ? <div className="empty"><h3>No results yet</h3><p className="small">Results from this browser session appear here. They are kept in memory only unless you opt in to local saving in Settings.</p></div> :
            <div className="stack">{recent.slice(0, 5).map((r) => (
              <button key={r.id} className="btn ghost" style={{ justifyContent: 'space-between' }} onClick={() => { store.setActive(r.id); go('evidence') }}>
                <span className="row"><span className="chip" data-sensor={sensorKey(r.payload.ref.sensor)}>{sensorLabel(r.payload.ref.sensor)}</span>→<span className="chip" data-sensor={sensorKey(r.payload.src.sensor)}>{sensorLabel(r.payload.src.sensor)}</span>{r.payload.ref.synthetic && <Badge tone="info" icon={false}>synthetic</Badge>}</span>
                <span className="row"><Badge tone={r.payload.status === 'VALIDATED' ? 'ok' : 'warn'}>{r.payload.status === 'VALIDATED' ? 'Gate passed' : 'Gate not passed'}</Badge><span className="mono xs">{fmtNum(r.payload.metrics.rmse_px, 2, 'px')}</span></span>
              </button>))}</div>}
        </section>
      </div>

      <div className="grid g2" style={{ marginTop: 'var(--s-4)' }}>
        <div className="notice info"><Icon n="lock" /><div><p><b>Privacy by design</b></p><p>{PRIVACY_STATEMENT}</p></div></div>
        <div className="notice warn"><Icon n="warn" /><div><p><b>Scientific scope</b></p><p>{LIMITATION_STATEMENT}</p></div></div>
      </div>
    </>
  )
}
