import { useRef, useState } from 'react'
import { store, useStore } from '../state/store'
import { Icon, Badge, PageHead, Notice, Confirm, Stat } from '../components/ui'
import type { RouteId } from '../components/Shell'
import { fromFileList, fromDataTransfer, fromDirectoryPicker, supportsDirectoryPicker } from '../lib/ingest'
import { fmtBytes, fmtNum, fmtInt, sensorKey, sensorLabel } from '../lib/format'
import { PROBLEM_TEXT, IGNORED_TEXT, WARNING_TEXT } from '../lib/copy'
import type { ProductInfo } from '../lib/types'

function ProductCard({ p }: { p: ProductInfo }) {
  const prev = useStore((s) => s.previews[p.key]); const [gsd, setGsd] = useState(''); const [sensor, setSensor] = useState('')
  const [open, setOpen] = useState(false)
  return (
    <article className="productcard" aria-label={`Product ${p.product_id}`}>
      <div className="row between"><div className="row"><span className="chip" data-sensor={sensorKey(p.sensor)}>{sensorLabel(p.sensor)}</span><b className="small mono" style={{ overflowWrap: 'anywhere' }}>{p.product_id}</b></div>
        <div className="row">{p.synthetic && <Badge tone="info" icon={false}>synthetic</Badge>}<Badge tone="mute" icon={false}>{p.adapter}</Badge></div></div>
      <div className="grid g3">
        <Stat k="Size" v={`${fmtInt(p.samples)}×${fmtInt(p.lines)}`} u={p.bands > 1 ? `× ${p.bands} bands` : 'px'} /><Stat k="GSD" v={p.gsd_m ? fmtNum(p.gsd_m, 3) : '—'} u="m/px" /><Stat k="Data type" v={p.dtype} />
      </div>
      <dl className="kv"><dt>Interleave</dt><dd>{p.interleave}</dd><dt>Binary</dt><dd>{p.data_file} · {fmtBytes(p.data_bytes)}</dd><dt>Geometry</dt><dd>{p.geometry_csv ? `${p.geometry_csv} · ${fmtBytes(p.geometry_csv_bytes)}` : 'none found'}</dd>
        {p.solar_elevation_deg != null && <><dt>Solar elev./az.</dt><dd>{fmtNum(p.solar_elevation_deg, 1)}° / {fmtNum(p.solar_azimuth_deg, 1)}°</dd></>}{p.acquisition_start && <><dt>Acquired</dt><dd>{p.acquisition_start}</dd></>}</dl>
      {p.warnings.length > 0 && <div className="row">{p.warnings.map((w) => <Badge key={w} tone="warn">{WARNING_TEXT[w] ?? w}</Badge>)}</div>}
      {(p.warnings.includes('gsd_missing') || p.warnings.includes('sensor_unknown')) && (
        <fieldset style={{ border: '1px solid var(--border)', borderRadius: 8, padding: 12 }}><legend className="small"><b>Supply missing metadata</b> <span className="faint">(recorded in the run manifest as a user override)</span></legend>
          <div className="grid g2">
            <label className="field"><span>GSD (m/px)</span><input type="number" min="0" step="any" value={gsd} onChange={(e) => setGsd(e.target.value)} placeholder="e.g. 5.0" /></label>
            <label className="field"><span>Sensor</span><select value={sensor} onChange={(e) => setSensor(e.target.value)}><option value="">keep ({p.sensor})</option><option>OHRC</option><option>TMC2</option><option>IIRS</option></select></label></div>
          <button className="btn small" style={{ marginTop: 8 }} onClick={() => store.setOverride(p.key, { ...(gsd ? { gsd_m: Number(gsd) } : {}), ...(sensor ? { sensor } : {}) })} disabled={!gsd && !sensor}>Apply override</button></fieldset>)}
      <div className="row"><button className="btn small" onClick={() => store.loadPreview(p.key)} disabled={prev === 'loading'}><Icon n="eye" spin={prev === 'loading'} />{prev === 'loading' ? 'Reading…' : prev ? 'Refresh preview' : 'Preview'}</button>
        <button className="btn small ghost" onClick={() => setOpen(!open)} aria-expanded={open}>{open ? 'Hide' : 'Show'} metadata</button></div>
      {prev === 'error' && <p className="small crit-bad">Preview failed.</p>}
      {prev && typeof prev === 'object' && <figure style={{ margin: 0 }}><img className="preview-img" src={prev.url} alt={`Decimated preview of ${p.product_id}`} /><figcaption className="xs faint">{prev.note} Sampled min/max: {fmtNum(prev.stats.min, 1)} / {fmtNum(prev.stats.max, 1)}.</figcaption></figure>}
      {open && <dl className="kv">{Object.entries(p.metadata).slice(0, 40).map(([k, v]) => <><dt key={k + 'k'}>{k}</dt><dd key={k + 'v'}>{typeof v === 'object' ? JSON.stringify(v) : String(v)}</dd></>)}</dl>}
    </article>
  )
}

export function Workspace({ go }: { go: (r: RouteId) => void }) {
  const s = useStore((x) => x); const [over, setOver] = useState(false); const [confirm, setConfirm] = useState(false)
  const fileIn = useRef<HTMLInputElement>(null); const dirIn = useRef<HTMLInputElement>(null)
  const ins = s.inspection
  const onDrop = async (e: React.DragEvent) => { e.preventDefault(); setOver(false); try { store.addRaw(await fromDataTransfer(e.dataTransfer)) } catch (err) { store.toast('bad', `Could not read dropped items: ${(err as Error).message}`) } }
  const pickDir = async () => { try { store.addRaw(await fromDirectoryPicker()) } catch (e) { if ((e as Error).name !== 'AbortError') store.toast('bad', (e as Error).message) } }
  const kindLabel: Record<string, string> = { pds4_label_candidate: 'XML', envi_header: 'ENVI hdr', numpy: 'npy', raw_binary: 'raw', sidecar_json: 'json', geometry_csv: 'csv', binary_data: 'binary', other: 'other' }
  const issuesBy = new Map(s.preflight.map((p) => [p.file.id, p.issues]))
  const bad = s.preflight.flatMap((p) => p.issues.filter((i) => i.tone === 'bad').map((i) => ({ f: p.file.path, i })))
  return (
    <>
      <PageHead kicker="Step 1" title="Data workspace"><p>Select mission products from this device. Files are read in place, in small slices — they are not uploaded and large binaries are not loaded into memory.</p></PageHead>
      <div className={`drop`} data-over={over} onDragOver={(e) => { e.preventDefault(); setOver(true) }} onDragLeave={() => setOver(false)} onDrop={onDrop} role="group" aria-label="File drop area">
        <Icon n="upload" className="faint" /><h2>Drop files or a folder here</h2>
        <p className="small muted">Include each product’s label <i>and</i> its binary, plus the geometry CSV for true geographic overlap. Selecting the whole archive folder is easiest.</p>
        <div className="row">
          <button className="btn primary" onClick={() => fileIn.current?.click()}><Icon n="file" />Select files</button>
          <button className="btn" onClick={() => (supportsDirectoryPicker() ? pickDir() : dirIn.current?.click())} disabled={!s.caps.directoryInput && !supportsDirectoryPicker()}><Icon n="folder" />Select folder</button>
          <button className="btn ghost" onClick={() => store.useDemo()}><Icon n="play" />Use synthetic demo</button>
        </div>
        {!s.caps.directoryInput && !supportsDirectoryPicker() && <p className="xs faint" style={{ marginTop: 10 }}>Folder selection is not supported by this browser; select the files together instead.</p>}
        <input ref={fileIn} type="file" multiple hidden data-testid="file-input" onChange={(e) => { if (e.target.files) store.addRaw(fromFileList(e.target.files)); e.target.value = '' }} />
        <input ref={dirIn} type="file" multiple hidden data-testid="dir-input" {...({ webkitdirectory: '', directory: '' } as object)} onChange={(e) => { if (e.target.files) store.addRaw(fromFileList(e.target.files)); e.target.value = '' }} />
      </div>

      {s.engine.status === 'error' && <div style={{ marginTop: 16 }}><Notice tone="bad" title="Engine could not start">{s.engine.error}<p><button className="btn small" onClick={() => store.recoverEngine()}>Retry</button></p></Notice></div>}
      {s.engine.status === 'loading' && <div style={{ marginTop: 16 }}><Notice tone="info" title="Loading the scientific engine">The Python engine (NumPy, SciPy, OpenCV, Shapely as WebAssembly, ~43 MB) is downloaded once and cached by your browser; it does not receive your files.</Notice></div>}

      {(s.files.length > 0 || s.demoActive) && (
        <div className="grid g-main" style={{ marginTop: 'var(--s-4)' }}>
          <section className="panel" aria-labelledby="files-h">
            <header><h2 id="files-h">Selected files</h2><div className="row"><span className="small muted">{s.files.length} · {fmtBytes(s.files.reduce((a, f) => a + f.size, 0))}</span><button className="btn small danger" onClick={() => setConfirm(true)}><Icon n="trash" />Reset workspace</button></div></header>
            {s.files.length === 0 ? <p className="small muted">Only the synthetic demo is loaded.</p> :
              <div className="filelist" role="list">{s.files.map((f) => { const iss = issuesBy.get(f.id) ?? []; return (
                <div className="item" role="listitem" key={f.id}><span className="p" title={f.path}>{f.path}</span><span className="chip">{kindLabel[s.preflight.find((p) => p.file.id === f.id)?.kind ?? 'other']}</span>
                  <span className="mono xs muted">{fmtBytes(f.size)}</span><span className="row" style={{ gap: 6 }}>{iss.map((i) => <Badge key={i.code} tone={i.tone}>{PROBLEM_TEXT[i.code]?.title ?? i.code}</Badge>)}<button className="btn small ghost" aria-label={`Remove ${f.name}`} onClick={() => store.removeFile(f.id)}><Icon n="x" /></button></span></div>) })}</div>}
            {bad.length > 0 && <div style={{ marginTop: 12 }}><Notice tone="warn" title="Quick checks found problems">{bad.slice(0, 4).map((b, i) => <p key={i}><code>{b.f}</code> — {PROBLEM_TEXT[b.i.code]?.fix ?? b.i.code}{b.i.detail ? ` (${b.i.detail})` : ''}</p>)}</Notice></div>}
            {s.skipped.length > 0 && <details style={{ marginTop: 12 }}><summary className="small muted">{s.skipped.length} skipped</summary><ul className="small">{s.skipped.slice(0, 30).map((k, i) => <li key={i}><code>{k.path}</code> — {k.reason}</li>)}</ul></details>}
          </section>
          <section className="panel" aria-labelledby="sum-h"><header><h2 id="sum-h">Inspection</h2>{s.inspecting ? <Badge tone="info" icon={false}><Icon n="loader" spin />Inspecting</Badge> : ins ? <Badge tone={ins.products.length ? 'ok' : 'warn'}>{ins.products.length} product{ins.products.length === 1 ? '' : 's'}</Badge> : <Badge tone="mute">Waiting for engine</Badge>}</header>
            <p className="small muted">Authoritative parsing uses the same adapters as the desktop engine, after safe-path and size checks.</p>
            {s.inspectError && <Notice tone="bad" title="Inspection failed">{s.inspectError}</Notice>}
            {ins && ins.ignored.length > 0 && <details><summary className="small">{ins.ignored.length} file(s) not used</summary><ul className="small">{ins.ignored.slice(0, 40).map((i) => <li key={i.file}><code>{i.file.replace(/^(user|demo):/, '')}</code> — {IGNORED_TEXT[i.reason] ?? i.reason}</li>)}</ul></details>}
            {ins && ins.products.length >= 2 && <p style={{ marginTop: 12 }}><button className="btn primary" onClick={() => go('registration')}>Continue to registration<Icon n="chev" /></button></p>}
          </section>
        </div>)}

      {ins && ins.problems.length > 0 && <section className="panel" style={{ marginTop: 'var(--s-4)' }} aria-labelledby="prob-h"><header><h2 id="prob-h">Products that could not be read</h2><Badge tone="bad">{ins.problems.length}</Badge></header>
        <div className="stack">{ins.problems.map((p) => <Notice key={p.file} tone="bad" title={`${PROBLEM_TEXT[p.code]?.title ?? 'Problem'} — ${p.file.replace(/^(user|demo):/, '')}`}><p>{PROBLEM_TEXT[p.code]?.fix}</p><p className="mono xs muted">{p.message}</p></Notice>)}</div></section>}

      {ins && ins.products.length > 0 && <section style={{ marginTop: 'var(--s-4)' }} aria-labelledby="prod-h"><h2 id="prod-h" style={{ marginBottom: 12 }}>Products</h2><div className="grid g2">{ins.products.map((p) => <ProductCard key={p.key} p={p} />)}</div></section>}
      {!s.files.length && !s.demoActive && <div className="empty" style={{ marginTop: 16 }}><h3>No files selected</h3><p className="small">Nothing leaves your device. See <a href="#/settings">Settings &amp; About</a> for supported formats and companion-file rules.</p></div>}

      <Confirm open={confirm} title="Reset workspace?" body={<p>This removes all selected files and detected products from this tab. Your original files on disk are not touched. Session results are kept.</p>} confirmLabel="Reset workspace" onCancel={() => setConfirm(false)} onConfirm={() => { setConfirm(false); store.resetWorkspace() }} />
    </>
  )
}
