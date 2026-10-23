import { extname, basename, stem, dirname } from './paths'
import type { WorkspaceFile } from './types'

export type FileKind = 'pds4_label_candidate' | 'envi_header' | 'numpy' | 'raw_binary' | 'sidecar_json' | 'geometry_csv' | 'binary_data' | 'other'
export interface PreflightEntry { file: WorkspaceFile; kind: FileKind; issues: { tone: 'bad' | 'warn'; code: string; detail?: string }[] }

const BINARY = new Set(['.img', '.qub', '.dat', '.raw', '.bin'])
const MAX_LABEL = 20 * 1024 * 1024

export function classify(path: string): FileKind {
  const e = extname(path)
  if (e === '.xml') return 'pds4_label_candidate'
  if (e === '.hdr') return 'envi_header'
  if (e === '.npy') return 'numpy'
  if (e === '.csv') return 'geometry_csv'
  if (e === '.json') return 'sidecar_json'
  if (BINARY.has(e)) return e === '.raw' || e === '.bin' || e === '.dat' ? 'raw_binary' : 'binary_data'
  return 'other'
}

/** Tiny, safe extraction of PDS4 <file_name> from the head of a label (regex; the engine does the real parse). */
export function sniffPds4FileName(text: string): string | null {
  if (!/logical_identifier/.test(text)) return null
  const m = /<(?:\w+:)?file_name>\s*([^<]+?)\s*<\/(?:\w+:)?file_name>/.exec(text)
  return m ? m[1] : null
}
const hasEntityDecl = (t: string) => /<!ENTITY/i.test(t)

/** Fast, engine-independent hints shown immediately after selection. The Python adapters remain authoritative. */
export async function preflight(files: WorkspaceFile[]): Promise<PreflightEntry[]> {
  const byBase = new Map<string, WorkspaceFile[]>(); const byDir = new Map<string, Set<string>>()
  for (const f of files) {
    const b = basename(f.path); (byBase.get(b) ?? byBase.set(b, []).get(b)!).push(f)
    const d = dirname(f.path); (byDir.get(d) ?? byDir.set(d, new Set()).get(d)!).add(b)
  }
  const out: PreflightEntry[] = []
  for (const f of files) {
    const kind = classify(f.path); const issues: PreflightEntry['issues'] = []
    if (f.size === 0) issues.push({ tone: 'bad', code: 'empty_file' })
    if (kind === 'pds4_label_candidate') {
      if (f.size > MAX_LABEL) issues.push({ tone: 'bad', code: 'label_too_large' })
      else {
        try {
          const head = await f.file.slice(0, 200_000).text()
          if (hasEntityDecl(head)) issues.push({ tone: 'bad', code: 'unsafe_xml' })
          const fn = sniffPds4FileName(head)
          if (fn) {
            if (/[\\/]|^\.\.?$/.test(fn)) issues.push({ tone: 'bad', code: 'unsafe_path', detail: fn })
            else if (!byBase.has(fn)) issues.push({ tone: 'bad', code: 'companion_missing', detail: fn })
          }
        } catch { issues.push({ tone: 'warn', code: 'unreadable' }) }
      }
    }
    if (kind === 'envi_header') {
      const s = stem(f.path); const d = dirname(f.path); const sibs = byDir.get(d) ?? new Set()
      if (!['.qub', '.img', '.dat', '.raw', ''].some((x) => sibs.has(s + x) && s + x !== basename(f.path))) issues.push({ tone: 'bad', code: 'companion_missing', detail: `${s}.img/.qub/.dat` })
    }
    if (kind === 'raw_binary') {
      const sibs = byDir.get(dirname(f.path)) ?? new Set()
      if (!sibs.has(basename(f.path) + '.json')) issues.push({ tone: 'warn', code: 'raw_without_sidecar' })
    }
    out.push({ file: f, kind, issues })
  }
  return out
}
