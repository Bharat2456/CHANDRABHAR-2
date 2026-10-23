import { describe, it, expect } from 'vitest'
import { cleanRelativePath, dedupe, isJunk, extname, stem } from '../src/lib/paths'
import { buildWorkspaceFiles } from '../src/lib/ingest'

describe('cleanRelativePath (untrusted browser paths)', () => {
  it('accepts normal relative paths and normalises backslashes', () => { expect(cleanRelativePath('a/b/c.xml').path).toBe('a/b/c.xml'); expect(cleanRelativePath('a\\b\\c.xml').path).toBe('a/b/c.xml') })
  it.each(['../x', 'a/../../x', '/etc/passwd', 'C:\\Windows\\x', 'a/./b', '', '///'])('rejects %j', (p) => { expect(() => cleanRelativePath(p)).toThrow() })
  it('replaces control characters and flags the rename', () => { const r = cleanRelativePath('a/b\u0000c.img'); expect(r.path).toBe('a/b_c.img'); expect(r.renamed).toBe(true) })
  it('rejects absurd depth and length', () => { expect(() => cleanRelativePath(Array(40).fill('d').join('/'))).toThrow(); expect(() => cleanRelativePath('x'.repeat(300))).toThrow() })
  it('detects junk files', () => { expect(isJunk('a/.DS_Store')).toBe(true); expect(isJunk('__MACOSX/a/b')).toBe(true); expect(isJunk('a/._b')).toBe(true); expect(isJunk('a/b.xml')).toBe(false) })
  it('dedupes colliding paths', () => { expect(dedupe(['a.img', 'a.img', 'b'])).toEqual(['a.img', 'a__dup1.img', 'b']) })
  it('ext/stem helpers', () => { expect(extname('x/Y.QUB')).toBe('.qub'); expect(stem('x/y.z.hdr')).toBe('y.z') })
})

describe('buildWorkspaceFiles', () => {
  const f = (n: string, size = 3) => new File([new Uint8Array(size)], n.split('/').pop()!)
  it('skips unsafe and junk entries without throwing, keeps the rest', () => {
    const r = buildWorkspaceFiles([{ path: 'ok/a.xml', file: f('a.xml') }, { path: '../evil', file: f('evil') }, { path: '.DS_Store', file: f('.DS_Store') }])
    expect(r.files.map((x) => x.path)).toEqual(['ok/a.xml']); expect(r.skipped.map((s) => s.reason)).toEqual(expect.arrayContaining(['path traversal is not allowed', 'system_file']))
  })
  it('never reads file contents (only size/name)', () => { const file = f('a.npy', 10); const r = buildWorkspaceFiles([{ path: 'a.npy', file }]); expect(r.files[0].size).toBe(10); expect(r.files[0].file).toBe(file) })
})
