/**
 * Explicit, local-only persistence.
 *  - localStorage 'cb2.prefs'  : theme, memory preset, persistence opt-in (no mission data)
 *  - IndexedDB 'cb2'/'runs'     : result JSON + evidence images, ONLY when the user opted in. Mission files are never stored.
 */
import type { RunResult } from './types'
export interface Prefs { theme: 'system' | 'dark' | 'light'; memory: 'auto' | 'conservative' | 'standard' | 'extended'; persistResults: boolean; motion: 'system' | 'reduce' }
export const DEFAULT_PREFS: Prefs = { theme: 'system', memory: 'auto', persistResults: false, motion: 'system' }
const PREF_KEY = 'cb2.prefs'

export function loadPrefs(): Prefs {
  try { const raw = localStorage.getItem(PREF_KEY); if (raw) return { ...DEFAULT_PREFS, ...JSON.parse(raw) } } catch { /* storage blocked */ }
  return { ...DEFAULT_PREFS }
}
export function savePrefs(p: Prefs): boolean { try { localStorage.setItem(PREF_KEY, JSON.stringify(p)); return true } catch { return false } }

const open = (): Promise<IDBDatabase> => new Promise((res, rej) => {
  if (typeof indexedDB === 'undefined') return rej(new Error('IndexedDB unavailable'))
  const r = indexedDB.open('cb2', 1)
  r.onupgradeneeded = () => { r.result.createObjectStore('runs', { keyPath: 'id' }) }
  r.onsuccess = () => res(r.result); r.onerror = () => rej(r.error ?? new Error('IndexedDB open failed'))
})
const tx = <T,>(mode: IDBTransactionMode, f: (s: IDBObjectStore) => IDBRequest<T>): Promise<T> => open().then((db) => new Promise<T>((res, rej) => {
  const t = db.transaction('runs', mode); const rq = f(t.objectStore('runs'))
  t.oncomplete = () => { db.close(); res(rq.result) }; t.onerror = () => { db.close(); rej(t.error) }; t.onabort = () => { db.close(); rej(t.error ?? new Error('aborted')) }
}))

export type SaveOutcome = { ok: true } | { ok: false; reason: 'quota' | 'unavailable' | 'error'; message: string }
export async function saveRun(r: RunResult): Promise<SaveOutcome> {
  try { await tx('readwrite', (s) => s.put({ ...r, savedAt: Date.now() })); return { ok: true } }
  catch (e) {
    const err = e as DOMException; const name = err?.name ?? ''
    if (name === 'QuotaExceededError') return { ok: false, reason: 'quota', message: 'Browser storage quota exceeded; the result was not saved. Export it instead.' }
    if (/unavailable/i.test(String(err?.message))) return { ok: false, reason: 'unavailable', message: 'Local storage is unavailable (private browsing?).' }
    return { ok: false, reason: 'error', message: String(err?.message ?? e) }
  }
}
export async function listRuns(): Promise<RunResult[]> { try { return (await tx('readonly', (s) => s.getAll())) as RunResult[] } catch { return [] } }
export async function deleteRun(id: string) { try { await tx('readwrite', (s) => s.delete(id)) } catch { /* ignore */ } }
export async function clearAllLocalData(): Promise<void> {
  try { localStorage.removeItem(PREF_KEY) } catch { /* ignore */ }
  try { sessionStorage.clear() } catch { /* ignore */ }
  await new Promise<void>((res) => { if (typeof indexedDB === 'undefined') return res(); const r = indexedDB.deleteDatabase('cb2'); r.onsuccess = () => res(); r.onerror = () => res(); r.onblocked = () => res() })
}
export async function storageEstimate() { try { const e = await navigator.storage?.estimate?.(); return e ? { usage: e.usage ?? 0, quota: e.quota ?? 0 } : null } catch { return null } }
