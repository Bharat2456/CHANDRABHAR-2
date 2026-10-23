import type { WorkspaceFile, Inspection, PairCheck, RunPayload, ProgressEvent, EngineInfo, MemoryPreset } from '../lib/types'

export type EngineStatus = 'idle' | 'loading' | 'ready' | 'busy' | 'error'
export interface BootInfo { info: EngineInfo; bundle: { engineVersion: string; platformVersion: string; sha256: string; fileCount: number } }
export class CancelledError extends Error { constructor() { super('Run cancelled'); this.name = 'CancelledError' } }
export class EngineError extends Error { detail?: string; constructor(m: string, d?: string) { super(m); this.name = 'EngineError'; this.detail = d } }

interface Pending { resolve: (v: any) => void; reject: (e: Error) => void } // eslint-disable-line @typescript-eslint/no-explicit-any
const base = (import.meta as unknown as { env: { BASE_URL: string } }).env.BASE_URL

/** Owns the worker: request/response correlation, progress fan-out, hard-cancel (terminate + respawn) and crash recovery. */
export class EngineClient {
  private worker: Worker | null = null
  private pending = new Map<number, Pending>()
  private seq = 1
  private progress = new Set<(runId: string, e: ProgressEvent) => void>()
  private bootStage = new Set<(s: string) => void>()
  private crash = new Set<(msg: string) => void>()
  private mounted: { files: WorkspaceFile[] } = { files: [] }
  private limits: MemoryPreset | null = null
  private demoActive = false
  private booting: Promise<BootInfo> | null = null
  info: BootInfo | null = null

  onProgress(cb: (runId: string, e: ProgressEvent) => void) { this.progress.add(cb); return () => this.progress.delete(cb) }
  onBootStage(cb: (s: string) => void) { this.bootStage.add(cb); return () => this.bootStage.delete(cb) }
  onCrash(cb: (msg: string) => void) { this.crash.add(cb); return () => this.crash.delete(cb) }

  private spawn() {
    const w = new Worker(new URL('./engine.worker.ts', import.meta.url), { type: 'module' })
    w.onmessage = (ev: MessageEvent) => {
      const m = ev.data
      if (m.event === 'boot') this.bootStage.forEach((f) => f(m.stage))
      else if (m.event === 'progress') this.progress.forEach((f) => f(m.runId, m.data))
      else if (typeof m.id === 'number') {
        const p = this.pending.get(m.id); if (!p) return; this.pending.delete(m.id)
        if (m.ok) p.resolve(m.result); else p.reject(new EngineError(m.error?.message ?? 'Engine error', m.error?.detail))
      }
    }
    const fail = (msg: string) => { this.rejectAll(new EngineError(msg)); this.worker = null; this.info = null; this.booting = null; this.crash.forEach((f) => f(msg)) }
    w.onerror = (e) => fail(`The engine worker stopped unexpectedly (${e.message || 'no message'}). This usually means the browser ran out of memory.`)
    w.onmessageerror = () => fail('The engine worker returned an unreadable message.')
    this.worker = w
  }
  private rejectAll(e: Error) { for (const p of this.pending.values()) p.reject(e); this.pending.clear() }

  call<T>(type: string, payload?: unknown, transfer: Transferable[] = []): Promise<T> {
    if (!this.worker) return Promise.reject(new EngineError('Engine is not running'))
    const id = this.seq++
    return new Promise<T>((resolve, reject) => { this.pending.set(id, { resolve, reject }); this.worker!.postMessage({ id, type, payload }, transfer) })
  }

  boot(): Promise<BootInfo> {
    if (this.booting) return this.booting
    if (!this.worker) this.spawn()
    const abs = (p: string) => new URL(base + p, location.href).href
    this.booting = this.call<BootInfo>('boot', { indexURL: abs('pyodide/'), pyodideURL: abs('pyodide/pyodide.mjs'), bundleURL: abs('engine/engine-bundle.json') })
      .then((i) => { this.info = i; return i }).catch((e) => { this.booting = null; throw e })
    return this.booting
  }

  async setLimits(l: MemoryPreset) { this.limits = l; if (this.info) await this.call('setLimits', l) }
  async mount(files: WorkspaceFile[]) { this.mounted = { files }; await this.call('mount', { files: files.map((f) => ({ path: f.path, blob: f.file })) }) }
  inspect() { return this.call<Inspection>('inspect') }
  pairCheck(ref: string, src: string) { return this.call<PairCheck>('pairCheck', { ref, src }) }
  override(key: string, value: { gsd_m?: number; sensor?: string }) { return this.call('override', { key, value }) }
  hashes(keys: string[]) { return this.call<Record<string, Record<string, string>>>('hashes', { keys }) }
  preview(key: string, maxDim?: number) { return this.call<{ meta: { shape: number[]; row_step: number; col_step: number; stats: Record<string, number>; note: string; bands_used: number[] }; png: Uint8Array }>('preview', { key, maxDim }) }
  async demo(action: 'make' | 'clear') { this.demoActive = action === 'make'; await this.call('demo', { action }) }
  selftest() { return this.call<Record<string, unknown>>('selftest') }
  register(ref: string, src: string, cfg: object, runId: string) { return this.call<{ payload: RunPayload; images: Record<string, Uint8Array> }>('register', { ref, src, cfg, runId }) }

  /** Hard cancel: terminate the worker (the only way to interrupt compiled code), then restore a clean engine in the background. */
  async cancelAndRestart(): Promise<void> {
    this.rejectAll(new CancelledError()); this.worker?.terminate(); this.worker = null; this.info = null; this.booting = null
    await this.recover()
  }
  /** Rebuild worker state after cancel/crash: boot, restore limits, remount the same File objects, regenerate demo data if active. */
  async recover(): Promise<void> {
    await this.boot()
    if (this.limits) await this.call('setLimits', this.limits)
    if (this.mounted.files.length) await this.call('mount', { files: this.mounted.files.map((f) => ({ path: f.path, blob: f.file })) })
    if (this.demoActive) await this.call('demo', { action: 'make' })
  }
  dispose() { this.rejectAll(new CancelledError()); this.worker?.terminate(); this.worker = null; this.booting = null; this.info = null }
}
