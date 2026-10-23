/// <reference lib="webworker" />
/**
 * Dedicated Web Worker hosting the Python scientific engine (Pyodide / WebAssembly).
 * All mission-file access happens here through WORKERFS (lazy, slice-based reads of the user's File objects).
 * This worker never issues network requests for mission data; it only fetches the static engine assets once at boot.
 */
import { bootEngine, type EngineBundle, type Py } from '../engine/boot'

let py: Py = null
let bridge: Py = null
const ctx = self as unknown as DedicatedWorkerGlobalScope

interface Req { id: number; type: string; payload?: any } // eslint-disable-line @typescript-eslint/no-explicit-any

const pyErr = (e: unknown) => {
  const msg = String((e as Error)?.message ?? e)
  const lines = msg.split('\n').map((l) => l.trim()).filter(Boolean)
  const last = [...lines].reverse().find((l) => /^[A-Za-z_.]*(Error|Exception)\b|^ValueError|^FileNotFoundError|^MemoryError/.test(l)) ?? lines[lines.length - 1] ?? msg
  return { message: last, detail: msg.length < 6000 ? msg : msg.slice(-6000), name: (e as Error)?.name ?? 'Error' }
}

function takeBlob(name: string): Uint8Array {
  const proxy = bridge.get_blob(name)
  try { return proxy.toJs() as Uint8Array } finally { proxy.destroy?.() }
}

function remount(files: { path: string; blob: Blob }[]) {
  ;(ctx as unknown as { cb2CloseSlices?: () => void }).cb2CloseSlices?.() // drop cached read handles of the previous mount
  try { py.FS.unmount('/ws') } catch { /* not mounted */ }
  py.FS.mount(py.FS.filesystems.WORKERFS, { blobs: files.map((f) => ({ name: f.path, data: f.blob })) }, '/ws')
}

const handlers: Record<string, (p: any) => Promise<{ result: unknown; transfer?: Transferable[] }> | { result: unknown; transfer?: Transferable[] }> = { // eslint-disable-line @typescript-eslint/no-explicit-any
  async boot(p: { indexURL: string; bundleURL: string; pyodideURL: string }) {
    const [bundle, mod] = await Promise.all([
      fetch(p.bundleURL).then((r) => { if (!r.ok) throw new Error(`engine bundle HTTP ${r.status}`); return r.json() as Promise<EngineBundle> }),
      import(/* @vite-ignore */ p.pyodideURL),
    ])
    py = await bootEngine({ loadPyodide: mod.loadPyodide, indexURL: p.indexURL, bundle, onStage: (s) => ctx.postMessage({ event: 'boot', stage: s }) })
    bridge = py.pyimport('app.web.bridge')
    return { result: { info: JSON.parse(bridge.engine_info()), bundle: { engineVersion: bundle.engineVersion, platformVersion: bundle.platformVersion, sha256: bundle.sha256, fileCount: bundle.fileCount } } }
  },
  mount(p: { files: { path: string; blob: Blob }[] }) { remount(p.files); return { result: true } },
  setLimits(p: object) { return { result: JSON.parse(bridge.set_limits(JSON.stringify(p))) } },
  inspect() { return { result: JSON.parse(bridge.inspect_workspace()) } },
  pairCheck(p: { ref: string; src: string }) { return { result: JSON.parse(bridge.pair_check(p.ref, p.src)) } },
  override(p: { key: string; value: object }) { return { result: JSON.parse(bridge.set_override(p.key, JSON.stringify(p.value))) } },
  hashes(p: { keys: string[] }) { return { result: JSON.parse(bridge.file_hashes(JSON.stringify(p.keys))) } },
  preview(p: { key: string; maxDim?: number }) {
    const meta = JSON.parse(bridge.product_preview(p.key, p.maxDim ?? null)); const png = takeBlob(meta.blob)
    return { result: { meta, png }, transfer: [png.buffer] }
  },
  register(p: { ref: string; src: string; cfg: object; runId: string }) {
    const emit = (s: string) => { try { ctx.postMessage({ event: 'progress', runId: p.runId, data: JSON.parse(s) }) } catch { /* ignore */ } }
    const payload = JSON.parse(bridge.run_registration(p.ref, p.src, JSON.stringify(p.cfg), emit))
    const images: Record<string, Uint8Array> = {}; const transfer: Transferable[] = []
    for (const [k, name] of Object.entries(payload.images as Record<string, string>)) { const b = takeBlob(name); images[k] = b; transfer.push(b.buffer) }
    py.runPython("import app.web.bridge as _b, gc; _b.clear_blobs('run:'); gc.collect()")
    return { result: { payload, images }, transfer }
  },
  demo(p: { action: 'make' | 'clear' }) { if (p.action === 'make') bridge.make_demo(); else bridge.clear_demo(); return { result: true } },
  selftest() { return { result: JSON.parse(bridge.run_selftest()) } },
}

ctx.onmessage = async (ev: MessageEvent<Req>) => {
  const { id, type, payload } = ev.data
  try {
    if (type !== 'boot' && !py) throw new Error('engine not booted')
    const h = handlers[type]; if (!h) throw new Error(`unknown request ${type}`)
    const { result, transfer } = await h(payload)
    ctx.postMessage({ id, ok: true, result }, transfer ?? [])
  } catch (e) { ctx.postMessage({ id, ok: false, error: pyErr(e) }) }
}
