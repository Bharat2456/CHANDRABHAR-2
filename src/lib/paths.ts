/** Defensive handling of untrusted file names/paths coming from the browser or from labels. */
export const MAX_FILES = 20000
export const MAX_DEPTH = 32
const JUNK = new Set(['.ds_store', 'thumbs.db', 'desktop.ini'])
const CONTROL = /[\u0000-\u001f\u007f]/g

export interface CleanPath { path: string; renamed: boolean }

/** Normalise a browser-provided relative path. Throws for traversal / absolute paths. */
export function cleanRelativePath(raw: string): CleanPath {
  if (typeof raw !== 'string' || raw.length === 0) throw new Error('empty path')
  let renamed = false
  const unified = raw.replace(/\\/g, '/')
  if (unified.startsWith('/') || /^[a-zA-Z]:\//.test(unified)) throw new Error('absolute paths are not allowed')
  const parts = unified.split('/').filter((p) => p.length > 0)
  if (parts.length === 0) throw new Error('empty path')
  if (parts.length > MAX_DEPTH) throw new Error('path too deep')
  const out = parts.map((p) => {
    if (p === '.' || p === '..') throw new Error('path traversal is not allowed')
    const c = p.replace(CONTROL, '_')
    if (c !== p) renamed = true
    if (c.length > 255) throw new Error('file name too long')
    return c
  })
  const path = out.join('/')
  if (path.length > 1024) throw new Error('path too long')
  return { path, renamed }
}

export const isJunk = (path: string) => {
  const parts = path.split('/')
  const base = parts[parts.length - 1].toLowerCase()
  return JUNK.has(base) || parts.includes('__MACOSX') || base.startsWith('._')
}

export const basename = (p: string) => p.slice(p.lastIndexOf('/') + 1)
export const extname = (p: string) => { const b = basename(p); const i = b.lastIndexOf('.'); return i <= 0 ? '' : b.slice(i).toLowerCase() }
export const stem = (p: string) => { const b = basename(p); const i = b.lastIndexOf('.'); return i <= 0 ? b : b.slice(0, i) }
export const dirname = (p: string) => (p.includes('/') ? p.slice(0, p.lastIndexOf('/')) : '')

/** Make every path unique (case-sensitive) by suffixing duplicates; returns mapping info. */
export function dedupe(paths: string[]): string[] {
  const seen = new Map<string, number>(); const out: string[] = []
  for (const p of paths) {
    const n = seen.get(p) ?? 0; seen.set(p, n + 1)
    if (n === 0) out.push(p)
    else { const e = extname(p); const base = e ? p.slice(0, -e.length) : p; out.push(`${base}__dup${n}${e}`) }
  }
  return out
}
