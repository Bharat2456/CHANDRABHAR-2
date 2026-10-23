import { describe, it, expect } from 'vitest'
import { makeZip, crc32 } from '../src/lib/zip'
import { summaryCsv, correspondencesCsv, manifestJson, metricsJson } from '../src/lib/exporters'
import type { RunResult } from '../src/lib/types'
import { execFileSync } from 'node:child_process'; import { writeFileSync, mkdtempSync } from 'node:fs'; import { tmpdir } from 'node:os'; import { join } from 'node:path'

const prod = (s: string) => ({ key: 'user:' + s, label: s, adapter: 'pds4', sensor: s, product_id: 'p_' + s, shape: [10, 10], dtype: 'uint16', offset: 0, interleave: 'native', bands: 1, lines: 10, samples: 10, gsd_m: 2, data_file: s + '.img', data_bytes: 200, geometry_csv: null, geometry_csv_bytes: null, solar_elevation_deg: null, solar_azimuth_deg: null, acquisition_start: null, acquisition_end: null, metadata: {}, warnings: [], synthetic: true })
const T = { min_tentative_matches: 8, min_inliers: 12, min_inlier_ratio: 0.35, min_coverage: 0.35, max_rmse_px: 2.5, ransac_reproj_px: 3 }
const result = (): RunResult => ({ id: 'r1', overrides: {}, hashes: { 'user:OHRC': { 'a.xml': 'ab' } }, files: [], config: { levels: [1], tile_px: 512, overlap: 0.2, sift_ratio: 0.78, seed: 1 }, limits: { name: 'standard', max_geometry_csv_mb: 1, max_grid_pixels: 1, max_preview_dim: 1, canvas_px: 1 }, images: {},
  payload: { ref: prod('OHRC'), src: prod('TMC2'), status: 'VALIDATED', gate_reasons: [], gate_thresholds: T, claims: { processing_completed: true, transformation_estimated: true, evidence_gate: 'VALIDATED', ground_truth_validation: 'NOT_ESTABLISHED' },
    metrics: { method: 'SIFT_RANSAC', keypoints_ref: 100, keypoints_src: 90, tentative_matches: 50, inliers: 40, inlier_ratio: 0.8, coverage: 0.9, rmse_px: 1.1, median_error_px: 0.9, p95_error_px: 2, rmse_m: 5.5, target_gsd_m: 5 },
    homography: { matrix: [[1, 0, 0], [0, 1, 0], [0, 0, 1]], tx_px: 0, ty_px: 0, rotation_deg: 0, scale_x: 1, scale_y: 1, shear: 0, det_affine: 1, perspective_h31: 0, perspective_h32: 0, cond_affine: 1 }, levels: [], matcher_paths: { sift: 3 }, geometry: {}, pair_geometry: null, grid: null, images: {}, points: { ref: [[1, 2], [3, 4]], src: [[1.5, 2.5], [9, 9]], inlier: [1, 0], residual_px: [0.2, 5], total: 2, shown: 2 }, elapsed_s: 1, engine_config: { rng_seed: 1 }, engine: { python: '3', platform: 'x', numpy: '2', opencv: '4', scipy: '1', shapely: '2', gate: T, io_backend: 'stream' }, warnings: [], finished_utc: '2026-01-01T00:00:00Z' } } as unknown as RunResult)

describe('exports', () => {
  it('summary CSV has stable header, gate rows and the not-established statement', () => { const c = summaryCsv(result()); expect(c.split('\n')[0]).toBe('quantity,value,unit,threshold,criterion_met'); expect(c).toContain('inliers,40,count,>=12,true'); expect(c).toContain('ground_truth_validation,NOT_ESTABLISHED') })
  it('CSV escaping', () => { const r = result(); r.payload.ref.product_id = 'a,"b"'; expect(summaryCsv(r)).toContain('"a,""b"""') })
  it('correspondences CSV flags inliers and residuals', () => { const l = correspondencesCsv(result()).trim().split('\n'); expect(l).toHaveLength(3); expect(l[1]).toBe('0,1,2,1.5,2.5,1,0.2'); expect(l[2].split(',')[5]).toBe('0') })
  it('manifest is valid JSON with versions, parameters, hashes and the statement', () => { const m = JSON.parse(manifestJson(result())); expect(m.parameters.engine_config.rng_seed).toBe(1); expect(m.inputs.reference.sha256_of_text_companions['a.xml']).toBe('ab'); expect(m.statement).toMatch(/not established/); expect(m.software.engine.opencv).toBe('4') })
  it('metrics JSON excludes image blobs but keeps claims', () => { const m = JSON.parse(metricsJson(result())); expect(m.images).toBeUndefined(); expect(m.claims.ground_truth_validation).toBe('NOT_ESTABLISHED') })
})
describe('zip writer', () => {
  it('crc32 matches the standard check value', () => expect(crc32(new TextEncoder().encode('123456789'))).toBe(0xcbf43926))
  it('produces an archive Python can verify and extract byte-exactly', () => {
    const z = makeZip([{ name: 'd/a.txt', data: new TextEncoder().encode('hello') }, { name: 'd/b.bin', data: new Uint8Array([0, 1, 2, 255]) }]); const f = join(mkdtempSync(join(tmpdir(), 'z-')), 't.zip'); writeFileSync(f, z)
    const out = execFileSync('python3', ['-c', "import zipfile,sys;z=zipfile.ZipFile(sys.argv[1]);assert z.testzip() is None;print(z.read('d/a.txt').decode(), list(z.read('d/b.bin')))", f]).toString().trim(); expect(out).toBe('hello [0, 1, 2, 255]')
  })
})
