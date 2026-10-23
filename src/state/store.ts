import { useSyncExternalStore } from 'react'
import { EngineClient, CancelledError, EngineError } from '../worker/client'
import type { BootInfo, EngineStatus } from '../worker/client'
import { buildWorkspaceFiles, type RawEntry } from '../lib/ingest'
import { preflight, type PreflightEntry } from '../lib/preflight'
import { DEFAULT_CONFIG, type Inspection, type PairCheck, type ProgressEvent, type RunConfig, type RunResult, type WorkspaceFile, type ProductInfo, type MemoryPreset } from '../lib/types'
import { detectCapabilities, resolvePreset, type Capabilities } from '../lib/capabilities'
import { loadPrefs, savePrefs, saveRun, listRuns, deleteRun, clearAllLocalData, type Prefs } from '../lib/storage'

export interface Toast { id: number; tone: 'ok' | 'warn' | 'bad' | 'info'; text: string }
export interface PreviewState { url: string; note: string; shape: number[]; stats: Record<string, number> }
export interface RunState {
  status: 'idle' | 'running' | 'done' | 'error' | 'cancelled'; runId: string | null; startedAt: number | null
  stage: string | null; stageLevel: number | null; levels: number | null; gsd: number | null; tile: number | null; tiles: number | null; mode: string | null
  log: { t: number; text: string }[]; error: { message: string; detail?: string } | null
}
export interface State {
  caps: Capabilities; prefs: Prefs; preset: MemoryPreset
  engine: { status: EngineStatus; stage: string | null; error: string | null; boot: BootInfo | null }
  files: WorkspaceFile[]; skipped: { path: string; reason: string }[]; preflight: PreflightEntry[]
  inspection: Inspection | null; inspecting: boolean; inspectError: string | null; demoActive: boolean
  previews: Record<string, PreviewState | 'loading' | 'error'>
  refKey: string | null; srcKey: string | null; pair: PairCheck | null; pairLoading: boolean
  config: RunConfig; run: RunState; results: RunResult[]; activeResultId: string | null; savedRuns: RunResult[]
  toasts: Toast[]; selftest: { running: boolean; result: Record<string, unknown> | null; error: string | null }
}

const idleRun: RunState = { status: 'idle', runId: null, startedAt: null, stage: null, stageLevel: null, levels: null, gsd: null, tile: null, tiles: null, mode: null, log: [], error: null }

class Store {
  private s: State; private subs = new Set<() => void>(); readonly engine = new EngineClient(); private toastN = 1; private inspectSeq = 0
  constructor() {
    const caps = detectCapabilities(); const prefs = loadPrefs()
    this.s = {
      caps, prefs, preset: resolvePreset(prefs.memory, caps),
      engine: { status: 'idle', stage: null, error: null, boot: null }, files: [], skipped: [], preflight: [], inspection: null, inspecting: false, inspectError: null, demoActive: false,
      previews: {}, refKey: null, srcKey: null, pair: null, pairLoading: false, config: { ...DEFAULT_CONFIG }, run: { ...idleRun }, results: [], activeResultId: null, savedRuns: [], toasts: [], selftest: { running: false, result: null, error: null },
    }
    this.engine.onBootStage((stage) => this.set({ engine: { ...this.s.engine, stage } }))
    this.engine.onProgress((runId, e) => this.onProgress(runId, e))
    this.engine.onCrash((msg) => { this.set({ engine: { ...this.s.engine, status: 'error', error: msg }, run: this.s.run.status === 'running' ? { ...this.s.run, status: 'error', error: { message: msg } } : this.s.run }); this.toast('bad', msg) })
    this.applyTheme()
    if (prefs.persistResults) void this.refreshSaved()
  }
  get = () => this.s
  subscribe = (f: () => void) => { this.subs.add(f); return () => this.subs.delete(f) }
  private set(p: Partial<State>) { this.s = { ...this.s, ...p }; this.subs.forEach((f) => f()) }

  // ---- toasts / prefs --------------------------------------------------------------------------------
  toast(tone: Toast['tone'], text: string) { const id = this.toastN++; this.set({ toasts: [...this.s.toasts.slice(-3), { id, tone, text }] }); setTimeout(() => this.dismissToast(id), tone === 'bad' ? 9000 : 5000) }
  dismissToast(id: number) { this.set({ toasts: this.s.toasts.filter((t) => t.id !== id) }) }
  applyTheme() {
    const r = document.documentElement; const t = this.s.prefs.theme
    if (t === 'system') r.removeAttribute('data-theme'); else r.setAttribute('data-theme', t)
    if (this.s.prefs.motion === 'reduce') r.setAttribute('data-motion', 'reduce'); else r.removeAttribute('data-motion')
  }
  setPrefs(p: Partial<Prefs>) {
    const prefs = { ...this.s.prefs, ...p }; const ok = savePrefs(prefs)
    const preset = resolvePreset(prefs.memory, this.s.caps); this.set({ prefs, preset }); this.applyTheme()
    if (!ok) this.toast('warn', 'Preferences could not be stored (browser storage is blocked); they apply to this session only.')
    if (p.memory !== undefined && this.engine.info) void this.engine.setLimits(preset)
    if (p.persistResults === true) void this.refreshSaved()
  }

  // ---- engine ---------------------------------------------------------------------------------------
  async ensureEngine(): Promise<void> {
    if (this.s.engine.status === 'ready' || this.s.engine.status === 'busy') return
    if (!this.s.caps.worker || !this.s.caps.wasm) { this.set({ engine: { ...this.s.engine, status: 'error', error: 'This browser lacks Web Workers or WebAssembly, which the scientific engine requires.' } }); return }
    this.set({ engine: { ...this.s.engine, status: 'loading', error: null, stage: 'runtime' } })
    try {
      const info = await this.engine.boot(); await this.engine.setLimits(this.s.preset)
      this.set({ engine: { status: 'ready', stage: 'ready', error: null, boot: info } })
      if (this.s.files.length || this.s.demoActive) await this.syncWorkspace()
    } catch (e) { this.set({ engine: { ...this.s.engine, status: 'error', error: (e as Error).message } }) }
  }

  // ---- workspace -----------------------------------------------------------------------------------
  async addRaw(raw: RawEntry[]) {
    const { files, skipped } = buildWorkspaceFiles(raw, this.s.files)
    const all = [...this.s.files, ...files]
    this.set({ files: all, skipped: [...this.s.skipped, ...skipped].slice(-200), preflight: await preflight(all) })
    if (skipped.length) this.toast('warn', `${skipped.length} file(s) were skipped (system files, duplicates or unsafe paths).`)
    if (files.length) this.toast('ok', `${files.length} file(s) added. Nothing was uploaded; files stay on this device.`)
    void this.ensureEngine().then(() => this.syncWorkspace())
  }
  async removeFile(id: string) { const all = this.s.files.filter((f) => f.id !== id); this.set({ files: all, preflight: await preflight(all) }); await this.syncWorkspace() }
  async resetWorkspace() {
    Object.values(this.s.previews).forEach((p) => typeof p === 'object' && URL.revokeObjectURL(p.url))
    this.set({ files: [], skipped: [], preflight: [], inspection: null, inspectError: null, previews: {}, refKey: null, srcKey: null, pair: null, demoActive: false })
    if (this.engine.info) { try { await this.engine.mount([]); await this.engine.demo('clear'); await this.engine.inspect() } catch { /* ignore */ } }
    this.toast('info', 'Workspace cleared. Session results are kept until you close the tab or clear them.')
  }
  async useDemo() {
    await this.ensureEngine(); if (this.s.engine.status !== 'ready') return
    try { await this.engine.demo('make'); this.set({ demoActive: true }); this.toast('info', 'Synthetic demo pair generated in memory (not mission data).'); await this.syncWorkspace() }
    catch (e) { this.toast('bad', `Demo generation failed: ${(e as Error).message}`) }
  }
  /** Mount current files and (re)inspect with the real adapters. */
  async syncWorkspace() {
    if (this.s.engine.status !== 'ready') return
    const seq = ++this.inspectSeq; this.set({ inspecting: true, inspectError: null })
    try {
      await this.engine.mount(this.s.files); const ins = await this.engine.inspect()
      if (seq !== this.inspectSeq) return
      const keys = new Set(ins.products.map((p) => p.key))
      let { refKey, srcKey } = this.s; if (refKey && !keys.has(refKey)) refKey = null; if (srcKey && !keys.has(srcKey)) srcKey = null
      const pds = ins.products.filter((p) => p.adapter === 'pds4' || p.synthetic)
      if (!refKey && !srcKey && pds.length >= 2) { const sorted = [...pds].sort((a, b) => (a.gsd_m ?? 1e9) - (b.gsd_m ?? 1e9)); refKey = sorted[0].key; srcKey = sorted[1].key }
      this.set({ inspection: ins, inspecting: false, refKey, srcKey, previews: {} }); void this.refreshPair()
    } catch (e) { if (seq === this.inspectSeq) this.set({ inspecting: false, inspectError: (e as Error).message }) }
  }
  async setOverride(key: string, v: { gsd_m?: number; sensor?: string }) {
    try { const info = (await this.engine.override(key, v)) as ProductInfo; const ins = this.s.inspection; if (ins) this.set({ inspection: { ...ins, products: ins.products.map((p) => (p.key === key ? info : p)) } }); void this.refreshPair() }
    catch (e) { this.toast('bad', (e as Error).message) }
  }
  async loadPreview(key: string) {
    if (this.s.previews[key] === 'loading') return
    this.set({ previews: { ...this.s.previews, [key]: 'loading' } })
    try {
      const { meta, png } = await this.engine.preview(key, this.s.preset.max_preview_dim)
      const url = URL.createObjectURL(new Blob([png as BlobPart], { type: 'image/png' }))
      this.set({ previews: { ...this.s.previews, [key]: { url, note: meta.note, shape: meta.shape, stats: meta.stats } } })
    } catch (e) { this.set({ previews: { ...this.s.previews, [key]: 'error' } }); this.toast('bad', `Preview failed: ${(e as Error).message}`) }
  }

  // ---- pair + run -------------------------------------------------------------------------------------
  setPair(ref: string | null, src: string | null) { this.set({ refKey: ref, srcKey: src, pair: null }); void this.refreshPair() }
  setConfig(p: Partial<RunConfig>) { this.set({ config: { ...this.s.config, ...p } }) }
  async refreshPair() {
    const { refKey, srcKey } = this.s; if (!refKey || !srcKey || this.s.engine.status !== 'ready' || this.s.run.status === 'running') { this.set({ pair: null }); return }
    this.set({ pairLoading: true })
    try { const pair = await this.engine.pairCheck(refKey, srcKey); if (refKey === this.s.refKey && srcKey === this.s.srcKey) this.set({ pair, pairLoading: false }) }
    catch (e) { this.set({ pairLoading: false, pair: { messages: [{ tone: 'bad', code: 'geometry_unreadable', detail: (e as Error).message }], gsd_ratio: null, geometry: null } }) }
  }
  private onProgress(runId: string, e: ProgressEvent) {
    const r = this.s.run; if (r.runId !== runId) return
    const log = [...r.log, { t: e.t, text: e.type === 'tile' ? `tile ${e.tile}/${e.tiles}${e.matcher_path ? ' · ' + e.matcher_path : ''}` : e.type === 'level' ? `level ${e.level}/${e.levels} · grid ${e.grid?.[1]}×${e.grid?.[0]} @ ${e.target_gsd_m?.toFixed(2)} m · ${e.mode}` : `stage: ${e.stage}`}].slice(-60)
    if (e.type === 'stage') this.set({ run: { ...r, stage: e.stage ?? null, stageLevel: e.level ?? r.stageLevel, levels: e.levels ?? r.levels, gsd: e.target_gsd_m ?? r.gsd, log } })
    else if (e.type === 'level') this.set({ run: { ...r, stageLevel: e.level ?? null, levels: e.levels ?? null, gsd: e.target_gsd_m ?? null, tile: 0, tiles: null, mode: e.mode ?? null, log } })
    else this.set({ run: { ...r, tile: e.tile ?? null, tiles: e.tiles ?? null, log } })
  }
  async runRegistration() {
    const { refKey, srcKey, config } = this.s; if (!refKey || !srcKey || this.s.run.status === 'running') return
    const runId = `r${Date.now().toString(36)}`
    this.set({ run: { ...idleRun, status: 'running', runId, startedAt: Date.now(), stage: 'start' } })
    try {
      const { payload, images } = await this.engine.register(refKey, srcKey, { ...config, max_grid_pixels: this.s.preset.max_grid_pixels, canvas_px: this.s.preset.canvas_px }, runId)
      const hashes = await this.engine.hashes([refKey, srcKey]).catch(() => ({}))
      const blobs: Record<string, Blob> = {}; for (const [k, v] of Object.entries(images)) blobs[k] = new Blob([v as BlobPart], { type: 'image/png' })
      const used = new Set([payload.ref.data_file, payload.src.data_file, payload.ref.label, payload.src.label, payload.ref.geometry_csv, payload.src.geometry_csv].filter(Boolean) as string[])
      const result: RunResult = { id: runId, payload, images: blobs, overrides: {}, hashes, config: { ...config }, limits: this.s.preset,
        files: this.s.files.filter((f) => [...used].some((u) => u.endsWith(f.path) || f.path.endsWith(u))).map((f) => ({ path: f.path, size: f.size, lastModified: f.file.lastModified })) }
      this.set({ results: [result, ...this.s.results], activeResultId: runId, run: { ...this.s.run, status: 'done' } })
      if (this.s.prefs.persistResults) { const o = await saveRun(result); if (!o.ok) this.toast('warn', o.message); else { result.savedLocally = true; void this.refreshSaved() } }
    } catch (e) {
      if (e instanceof CancelledError) { this.set({ run: { ...this.s.run, status: 'cancelled' } }); return }
      const err = e as EngineError; this.set({ run: { ...this.s.run, status: 'error', error: { message: err.message, detail: err.detail } } })
    }
  }
  async cancelRun() {
    if (this.s.run.status !== 'running') return
    this.set({ engine: { ...this.s.engine, status: 'loading', stage: 'restarting' }, run: { ...this.s.run, status: 'cancelled' } })
    try { await this.engine.cancelAndRestart(); this.set({ engine: { ...this.s.engine, status: 'ready', stage: 'ready', error: null } }); await this.syncWorkspace(); this.toast('info', 'Run cancelled. The engine was restarted cleanly and your files are still selected.') }
    catch (e) { this.set({ engine: { ...this.s.engine, status: 'error', error: (e as Error).message } }) }
  }
  async recoverEngine() {
    this.set({ engine: { ...this.s.engine, status: 'loading', stage: 'restarting', error: null } })
    try { await this.engine.recover(); this.set({ engine: { ...this.s.engine, status: 'ready', stage: 'ready', error: null, boot: this.engine.info } }); await this.syncWorkspace() }
    catch (e) { this.set({ engine: { ...this.s.engine, status: 'error', error: (e as Error).message } }) }
  }
  dismissRunError() { this.set({ run: { ...idleRun } }) }
  setActive(id: string) { this.set({ activeResultId: id }) }
  activeResult(): RunResult | null { return [...this.s.results, ...this.s.savedRuns].find((r) => r.id === this.s.activeResultId) ?? null }

  // ---- persistence ------------------------------------------------------------------------------------
  async refreshSaved() { const runs = await listRuns(); this.set({ savedRuns: runs.filter((r) => !this.s.results.some((x) => x.id === r.id)) }) }
  async deleteSaved(id: string) { await deleteRun(id); this.set({ savedRuns: this.s.savedRuns.filter((r) => r.id !== id) }) }
  async clearLocalData() {
    await clearAllLocalData(); this.set({ prefs: loadPrefs(), savedRuns: [], results: [], activeResultId: null }); this.set({ preset: resolvePreset(this.s.prefs.memory, this.s.caps) }); this.applyTheme()
    this.toast('ok', 'All locally stored preferences and saved results were deleted.')
  }
  async runSelftest() {
    await this.ensureEngine(); if (this.s.engine.status !== 'ready') return
    this.set({ selftest: { running: true, result: null, error: null } })
    try { this.set({ selftest: { running: false, result: await this.engine.selftest(), error: null } }) } catch (e) { this.set({ selftest: { running: false, result: null, error: (e as Error).message } }) }
  }
}

export const store = new Store()
export function useStore<T>(sel: (s: State) => T): T {
  return useSyncExternalStore(store.subscribe, () => sel(store.get()))
}
