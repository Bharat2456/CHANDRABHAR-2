import { MAX_FILES, cleanRelativePath, isJunk, dedupe, basename } from './paths'
import type { WorkspaceFile } from './types'

let counter = 0
const mkId = () => `f${Date.now().toString(36)}${(counter++).toString(36)}`

export interface RawEntry { path: string; file: File }
export interface IngestResult { files: WorkspaceFile[]; skipped: { path: string; reason: string }[] }

/** Turn raw (path, File) pairs into validated workspace files. Never reads file contents. */
export function buildWorkspaceFiles(raw: RawEntry[], existing: WorkspaceFile[] = []): IngestResult {
  const skipped: { path: string; reason: string }[] = []; const ok: { path: string; file: File; renamed: boolean }[] = []
  const have = new Set(existing.map((f) => f.path + '|' + f.size))
  for (const r of raw) {
    try {
      const c = cleanRelativePath(r.path)
      if (isJunk(c.path)) { skipped.push({ path: r.path, reason: 'system_file' }); continue }
      ok.push({ path: c.path, file: r.file, renamed: c.renamed })
    } catch (e) { skipped.push({ path: String(r.path).slice(0, 200), reason: (e as Error).message }) }
  }
  const room = Math.max(0, MAX_FILES - existing.length)
  if (ok.length > room) { for (const x of ok.splice(room)) skipped.push({ path: x.path, reason: `file_limit_${MAX_FILES}` }) }
  const all = [...existing.map((f) => f.path), ...ok.map((o) => o.path)]
  const unique = dedupe(all).slice(existing.length)
  const files: WorkspaceFile[] = []
  ok.forEach((o, i) => {
    if (have.has(o.path + '|' + o.file.size) && unique[i] !== o.path) { skipped.push({ path: o.path, reason: 'duplicate' }); return }
    files.push({ id: mkId(), path: unique[i], name: basename(unique[i]), size: o.file.size, file: o.file, renamed: o.renamed || unique[i] !== o.path })
  })
  return { files, skipped }
}

/** From <input type=file> (multiple or webkitdirectory). */
export function fromFileList(list: FileList | File[]): RawEntry[] {
  return Array.from(list).map((f) => ({ path: (f as File & { webkitRelativePath?: string }).webkitRelativePath || f.name, file: f }))
}

// ---- drag & drop (supports folders through the FileSystem entries API) --------------------------------
type FsEntry = { isFile: boolean; isDirectory: boolean; name: string; fullPath: string; file?: (cb: (f: File) => void, err: (e: unknown) => void) => void; createReader?: () => { readEntries: (cb: (e: FsEntry[]) => void, err: (e: unknown) => void) => void } }

const readAll = (reader: NonNullable<ReturnType<NonNullable<FsEntry['createReader']>>>) =>
  new Promise<FsEntry[]>((resolve, reject) => {
    const acc: FsEntry[] = []
    const next = () => reader.readEntries((batch) => { if (!batch.length) resolve(acc); else { acc.push(...batch); next() } }, reject)
    next()
  })

async function walkEntry(e: FsEntry, out: RawEntry[], budget: { n: number }): Promise<void> {
  if (budget.n <= 0) return
  if (e.isFile && e.file) {
    const f = await new Promise<File>((res, rej) => e.file!(res, rej)); budget.n--
    out.push({ path: e.fullPath.replace(/^\//, ''), file: f })
  } else if (e.isDirectory && e.createReader) {
    for (const c of await readAll(e.createReader())) await walkEntry(c, out, budget)
  }
}

export async function fromDataTransfer(dt: DataTransfer): Promise<RawEntry[]> {
  const out: RawEntry[] = []
  // Entries must be captured synchronously, before any await.
  const entries: FsEntry[] = []
  for (const item of Array.from(dt.items ?? [])) {
    const get = (item as DataTransferItem & { webkitGetAsEntry?: () => FsEntry | null }).webkitGetAsEntry
    const ent = get ? get.call(item) : null
    if (ent) entries.push(ent)
  }
  const fallback = Array.from(dt.files ?? [])
  if (entries.length) { const budget = { n: MAX_FILES }; for (const e of entries) await walkEntry(e, out, budget); return out }
  return fallback.map((f) => ({ path: f.name, file: f }))
}

// ---- File System Access API (Chromium) ---------------------------------------------------------------
export const supportsDirectoryPicker = () => typeof (window as unknown as { showDirectoryPicker?: unknown }).showDirectoryPicker === 'function'
interface DirHandle { name: string; values: () => AsyncIterable<{ kind: 'file' | 'directory'; name: string; getFile?: () => Promise<File> } & DirHandle> }
export async function fromDirectoryPicker(): Promise<RawEntry[]> {
  const pick = (window as unknown as { showDirectoryPicker: (o?: unknown) => Promise<DirHandle> }).showDirectoryPicker
  const root = await pick({ mode: 'read' }); const out: RawEntry[] = []; const budget = { n: MAX_FILES }
  const walk = async (h: DirHandle, prefix: string) => {
    for await (const e of h.values()) {
      if (budget.n <= 0) return
      if (e.kind === 'file' && e.getFile) { out.push({ path: `${prefix}${e.name}`, file: await e.getFile() }); budget.n-- }
      else if (e.kind === 'directory') await walk(e as unknown as DirHandle, `${prefix}${e.name}/`)
    }
  }
  await walk(root, `${root.name}/`)
  return out
}
