import { useEffect, useState } from 'react'
import { store, useStore } from '../state/store'
import { Icon, Badge, PageHead, Notice, Confirm } from '../components/ui'
import { storageEstimate } from '../lib/storage'
import { fmtBytes, fmtInt } from '../lib/format'
import { PRESETS } from '../lib/capabilities'
import { LIMITATION_STATEMENT, PRIVACY_STATEMENT } from '../lib/copy'
import { APP_VERSION, ENGINE_VERSION } from '../lib/version'

export function Settings() {
  const s = useStore((x) => x); const [confirm, setConfirm] = useState(false); const [est, setEst] = useState<{ usage: number; quota: number } | null>(null)
  useEffect(() => { void storageEstimate().then(setEst) }, [s.savedRuns.length])
  const c = s.caps; const boot = s.engine.boot
  const cap = (ok: boolean, yes: string, no: string) => ok ? <Badge tone="ok">{yes}</Badge> : <Badge tone="warn">{no}</Badge>
  return (
    <>
      <PageHead kicker="System" title="Settings & about"><p>Preferences, memory limits, local data controls, supported formats and scientific limitations.</p></PageHead>
      <div className="grid g2">
        <section className="panel" aria-labelledby="app-h"><header><h2 id="app-h">Appearance & accessibility</h2></header>
          <div className="stack">
            <label className="field"><span>Theme</span><select value={s.prefs.theme} onChange={(e) => store.setPrefs({ theme: e.target.value as 'system' })}><option value="system">Follow system</option><option value="dark">Dark (Orbital Night)</option><option value="light">Light (Lunar Daylight)</option></select></label>
            <label className="field"><span>Motion</span><select value={s.prefs.motion} onChange={(e) => store.setPrefs({ motion: e.target.value as 'system' })}><option value="system">Follow system setting</option><option value="reduce">Reduce motion</option></select></label>
            <p className="xs faint">Keyboard: Tab / Shift+Tab to move, Enter/Space to activate. In the Lab canvas use arrow keys to pan, + / − to zoom, 0 to fit.</p></div></section>
        <section className="panel" aria-labelledby="mem-h"><header><h2 id="mem-h">Processing & memory</h2><Badge tone="info" icon={false}>active: {s.preset.name}</Badge></header>
          <label className="field"><span>Memory preset</span><select value={s.prefs.memory} onChange={(e) => store.setPrefs({ memory: e.target.value as 'auto' })}><option value="auto">Automatic (from device capabilities)</option><option value="conservative">Conservative</option><option value="standard">Standard</option><option value="extended">Extended (may crash low-memory tabs)</option></select></label>
          <div className="tablewrap" style={{ marginTop: 12 }}><table><thead><tr><th>Preset</th><th className="num">Max grid px</th><th className="num">Geometry CSV</th><th className="num">Preview</th></tr></thead><tbody>{Object.values(PRESETS).map((p) => <tr key={p.name}><td>{p.name}</td><td className="num">{fmtInt(p.max_grid_pixels)}</td><td className="num">{p.max_geometry_csv_mb} MB</td><td className="num">{p.max_preview_dim}px</td></tr>)}</tbody></table></div>
          <p className="xs faint" style={{ marginTop: 8 }}>Input rasters are read in slices and are not limited by RAM. Limits apply to the in-memory common grid, geometry tables and previews. WebAssembly in a browser tab is limited to roughly 2–4 GB. Larger products are processed by tiling, but the common grid is capped; if it is, the engine reports it rather than crashing.</p></section>
      </div>

      <section className="panel" style={{ marginTop: 'var(--s-4)' }} aria-labelledby="loc-h"><header><h2 id="loc-h">Local data</h2></header>
        <div className="grid g2"><div className="stack">
          <label className="check"><input type="checkbox" checked={s.prefs.persistResults} onChange={(e) => store.setPrefs({ persistResults: e.target.checked })} /><span><b>Save results in this browser (IndexedDB)</b><br /><span className="muted">Off by default. Stores result metrics and evidence images only — never your mission files. Not synced across devices; cleared if you clear site data or use private browsing.</span></span></label>
          <p className="small">Saved runs: <b>{s.savedRuns.length}</b>{est && <> · site storage {fmtBytes(est.usage)} of ~{fmtBytes(est.quota)}</>}</p>
          <div className="row"><button className="btn danger" onClick={() => setConfirm(true)}><Icon n="trash" />Clear all local data</button></div></div>
          <Notice tone="info" title="What this site can store"><p><code>localStorage</code>: theme, memory preset, save-results opt-in. <code>IndexedDB</code>: saved results (opt-in). Nothing else. Selected files are held only as references in this tab until you close or reset it.</p></Notice></div></section>

      <div className="grid g2" style={{ marginTop: 'var(--s-4)' }}>
        <section className="panel" aria-labelledby="cap-h"><header><h2 id="cap-h">This browser</h2></header>
          <dl className="kv"><dt>Web Workers</dt><dd>{cap(c.worker, 'Available', 'Missing')}</dd><dt>WebAssembly</dt><dd>{cap(c.wasm, 'Available', 'Missing')}</dd><dt>Folder selection</dt><dd>{cap(c.directoryInput || c.fileSystemAccess, c.fileSystemAccess ? 'Directory picker' : 'webkitdirectory', 'Select files instead')}</dd><dt>IndexedDB</dt><dd>{cap(c.indexedDB, 'Available', 'Unavailable')}</dd><dt>Device memory</dt><dd>{c.deviceMemoryGB ? `${c.deviceMemoryGB} GB (coarse)` : 'not reported'}</dd><dt>CPU threads</dt><dd>{c.cores ?? 'not reported'}</dd><dt>WebGPU</dt><dd>{c.webgpu ? 'present, not used' : 'absent'} <span className="faint">— the engine is CPU/WASM; no benchmark has justified GPU use</span></dd></dl></section>
        <section className="panel" aria-labelledby="eng-h"><header><h2 id="eng-h">Scientific engine</h2></header>
          {boot ? <dl className="kv"><dt>Engine</dt><dd>{boot.bundle.engineVersion}</dd><dt>Platform</dt><dd>{boot.bundle.platformVersion}</dd><dt>Python</dt><dd>{boot.info.python} ({boot.info.platform})</dd><dt>NumPy / SciPy</dt><dd>{boot.info.numpy} / {boot.info.scipy}</dd><dt>OpenCV</dt><dd>{boot.info.opencv}</dd><dt>Shapely</dt><dd>{boot.info.shapely}</dd><dt>I/O backend</dt><dd>{boot.info.io_backend}</dd><dt>Bundle SHA-256</dt><dd>{boot.bundle.sha256.slice(0, 16)}…</dd></dl> : <p className="small muted">The engine has not been started. It loads on first use.</p>}
          <div className="row" style={{ marginTop: 12 }}><button className="btn" onClick={() => store.runSelftest()} disabled={s.selftest.running}><Icon n="play" spin={s.selftest.running} />Run engine self-test</button></div>
          {s.selftest.result && <div style={{ marginTop: 8 }}><Notice tone={s.selftest.result.passed ? 'ok' : 'bad'} title={s.selftest.result.passed ? 'Self-test passed' : 'Self-test failed'}><p className="mono xs">known-transform error {Number(s.selftest.result.known_transform_error_px).toFixed(3)} px · {String(s.selftest.result.inliers)} inliers · {Number(s.selftest.result.elapsed_s).toFixed(1)} s</p><p className="xs">Synthetic check against a known transform. Not mission validation.</p></Notice></div>}
          {s.selftest.error && <Notice tone="bad">{s.selftest.error}</Notice>}</section>
      </div>

      <section className="panel" style={{ marginTop: 'var(--s-4)' }} aria-labelledby="fmt-h"><header><h2 id="fmt-h">Supported formats & companion files</h2></header>
        <div className="tablewrap"><table><thead><tr><th>Format</th><th>Select together</th><th>Notes</th></tr></thead><tbody>
          <tr><td>PDS4</td><td><code>*.xml</code> label + the binary named by <code>file_name</code> + (optional) geometry <code>*.csv</code></td><td>Axes, data type, byte order, offset, GSD and solar geometry are read from the label. The binary size must equal the label-implied size. Geometry CSV (Scan, Pixel, Latitude, Longitude) enables true swath intersection; without it the engine falls back to full-scene matching and says so.</td></tr>
          <tr><td>ENVI</td><td><code>*.hdr</code> + binary (<code>.img</code>/<code>.qub</code>/<code>.dat</code>/<code>.raw</code>/no extension)</td><td>BSQ/BIL/BIP, byte order, header offset; GSD from <code>pixel size</code> if present.</td></tr>
          <tr><td>NumPy</td><td><code>*.npy</code></td><td>2-D or 3-D (bands, lines, samples), C-order, non-object dtypes. GSD must be supplied manually.</td></tr>
          <tr><td>Raw + sidecar</td><td><code>*.raw|.bin|.dat</code> + <code>&lt;file&gt;.json</code></td><td>Sidecar keys: dtype, shape, offset, interleave, sensor, product_id, gsd_m.</td></tr></tbody></table></div>
        <p className="small muted" style={{ marginTop: 8 }}>Labels are untrusted: file references must be plain names inside your selection, DTD/entity XML is refused, and declared sizes must match the actual files.</p></section>

      <div className="grid g2" style={{ marginTop: 'var(--s-4)' }}>
        <section className="panel" aria-labelledby="lim-h"><header><h2 id="lim-h">Scientific limitations</h2></header>
          <ul className="small" style={{ margin: 0, paddingLeft: 20, display: 'grid', gap: 6 }}>
            <li>{LIMITATION_STATEMENT}</li><li>The engine is classical computer vision (SIFT, phase correlation, ECC, RANSAC). It contains no trained model and does not learn from your files.</li>
            <li>Accuracy depends on label geometry quality; geometry errors in the swath tables propagate into the common grid.</li><li>Browser speed is typically several times slower than native and single-threaded. Very large swaths are bounded by the grid cap of the memory preset.</li><li>Only the products and formats documented above were tested; other mission products are unverified.</li></ul></section>
        <section className="panel" aria-labelledby="priv-h"><header><h2 id="priv-h">Privacy</h2></header><p className="small">{PRIVACY_STATEMENT}</p><p className="small muted">No analytics, session replay, telemetry, third-party scripts, remote fonts or external AI services are used. This is enforced by a Content-Security-Policy that restricts connections to this site. It cannot protect against a compromised device or malicious browser extensions.</p></section>
      </div>
      <section className="panel" style={{ marginTop: 'var(--s-4)' }} aria-labelledby="about-h"><header><h2 id="about-h">About</h2></header>
        <p className="small"><b>CHANDRABHAR-2</b> · web {APP_VERSION} · engine {ENGINE_VERSION}. Developed for Smart India Hackathon 2025. Chandrayaan-2 is an ISRO mission; mission data remain subject to ISRO/ISSDC terms. This project is not affiliated with or endorsed by ISRO. Third-party components (Pyodide, NumPy, SciPy, OpenCV, Shapely, React) are listed with licences in <code>docs/DEPENDENCIES.md</code>; original legal notices are in <code>LEGAL/</code>.</p></section>

      <Confirm open={confirm} title="Clear all local data?" body={<p>This deletes saved results, preferences and session results held by this site in your browser. Exported files on your device are unaffected.</p>} confirmLabel="Clear everything" onCancel={() => setConfirm(false)} onConfirm={() => { setConfirm(false); void store.clearLocalData() }} />
    </>
  )
}
