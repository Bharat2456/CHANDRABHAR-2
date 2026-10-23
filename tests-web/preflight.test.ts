import { describe, it, expect } from 'vitest'
import { classify, preflight, sniffPds4FileName } from '../src/lib/preflight'
import { buildWorkspaceFiles } from '../src/lib/ingest'

const mk = (entries: [string, string | Uint8Array][]) => buildWorkspaceFiles(entries.map(([p, c]) => ({ path: p, file: new File([c as BlobPart], p.split('/').pop()!) }))).files
const label = (fn: string) => `<?xml version="1.0"?><Product_Observational xmlns="x"><Identification_Area><logical_identifier>urn:x:y</logical_identifier></Identification_Area><File_Area_Observational><File><file_name>${fn}</file_name></File></File_Area_Observational></Product_Observational>`

describe('classification', () => {
  it.each([['a.xml', 'pds4_label_candidate'], ['a.hdr', 'envi_header'], ['a.npy', 'numpy'], ['a.csv', 'geometry_csv'], ['a.json', 'sidecar_json'], ['a.qub', 'binary_data'], ['a.raw', 'raw_binary'], ['a.txt', 'other']])('%s -> %s', (p, k) => expect(classify(p)).toBe(k))
  it('sniffs PDS4 file_name with and without namespace prefix', () => { expect(sniffPds4FileName(label('p.img'))).toBe('p.img'); expect(sniffPds4FileName('<pds:file_name> q.img </pds:file_name> logical_identifier')).toBe('q.img'); expect(sniffPds4FileName('<a/>')).toBeNull() })
})
describe('preflight companion detection', () => {
  it('flags a missing PDS4 data file', async () => { const r = await preflight(mk([['p/x.xml', label('x.img')]])); expect(r[0].issues.map((i) => i.code)).toContain('companion_missing') })
  it('accepts label + data present', async () => { const r = await preflight(mk([['p/x.xml', label('x.img')], ['p/x.img', new Uint8Array(4)]])); expect(r.find((e) => e.kind === 'pds4_label_candidate')!.issues).toEqual([]) })
  it('flags path traversal in a label', async () => { const r = await preflight(mk([['x.xml', label('../../etc/passwd')]])); expect(r[0].issues.map((i) => i.code)).toContain('unsafe_path') })
  it('refuses DTD entity declarations', async () => { const r = await preflight(mk([['b.xml', '<?xml version="1.0"?><!DOCTYPE l [<!ENTITY a "x">]><logical_identifier>&a;</logical_identifier>']])); expect(r[0].issues.map((i) => i.code)).toContain('unsafe_xml') })
  it('flags ENVI header without binary and raw without sidecar, and empty files', async () => {
    const r = await preflight(mk([['c.hdr', 'ENVI'], ['r.raw', new Uint8Array(8)], ['e.npy', new Uint8Array(0)]]))
    const by = Object.fromEntries(r.map((e) => [e.file.name, e.issues.map((i) => i.code)])); expect(by['c.hdr']).toContain('companion_missing'); expect(by['r.raw']).toContain('raw_without_sidecar'); expect(by['e.npy']).toContain('empty_file')
  })
})
