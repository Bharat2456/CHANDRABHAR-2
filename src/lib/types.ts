export interface WorkspaceFile { id: string; path: string; name: string; size: number; file: File; renamed?: boolean }

export interface ProductInfo {
  key: string; label: string; adapter: 'pds4' | 'envi' | 'numpy' | 'raw_sidecar'; sensor: string; product_id: string
  shape: number[]; dtype: string; offset: number; interleave: string; bands: number; lines: number; samples: number
  gsd_m: number | null; data_file: string; data_bytes: number; geometry_csv: string | null; geometry_csv_bytes: number | null
  solar_elevation_deg: number | null; solar_azimuth_deg: number | null; acquisition_start: string | null; acquisition_end: string | null
  metadata: Record<string, unknown>; warnings: string[]; synthetic: boolean; overrides?: { gsd_m?: number; sensor?: string }
}
export interface InspectProblem { file: string; adapter?: string; code: string; message: string }
export interface IgnoredFile { file: string; reason: string; bytes?: number }
export interface Inspection { products: ProductInfo[]; problems: InspectProblem[]; ignored: IgnoredFile[]; file_count: number; total_bytes: number }

export interface PairMessage { tone: 'bad' | 'warn' | 'info'; code: string; role?: string; ratio?: number; detail?: string }
export interface PairCheck {
  messages: PairMessage[]; gsd_ratio: number | null; common_gsd_base_m?: number
  geometry: null | { status: string; area_km2?: number; vertices?: number; polygon?: [number, number][]; ref_polygon?: [number, number][]; src_polygon?: [number, number][]; grid_estimates?: { gsd_m: number; pixels: number }[]; ref_fit_rms?: number; src_fit_rms?: number }
}

export interface RunConfig { levels: number[]; tile_px: number; overlap: number; sift_ratio: number; seed: number }
export const DEFAULT_LEVELS = [1.0, 1.5, 2.5, 4.0, 6.0]
export const DEFAULT_CONFIG: RunConfig = { levels: DEFAULT_LEVELS, tile_px: 512, overlap: 0.2, sift_ratio: 0.78, seed: 12345 }

export interface GateThresholds { min_tentative_matches: number; min_inliers: number; min_inlier_ratio: number; min_coverage: number; max_rmse_px: number; ransac_reproj_px: number }
export interface HomographyDiag { matrix: number[][]; tx_px: number; ty_px: number; rotation_deg: number; scale_x: number; scale_y: number; shear: number; det_affine: number; perspective_h31: number; perspective_h32: number; cond_affine: number }
export interface LevelSummary { index: number; target_gsd_m: number | null; status: string; reasons: string[]; method: string; keypoints_ref: number; keypoints_src: number; tentative: number; inliers: number; inlier_ratio: number; coverage: number; rmse_px: number | null; rmse_m: number | null; grid: number[] | null; geographic_warp: boolean; tiles: number; reason?: string | null }

export interface RunPayload {
  ref: ProductInfo; src: ProductInfo; status: 'VALIDATED' | 'INSUFFICIENT_EVIDENCE' | string; gate_reasons: string[]; gate_thresholds: GateThresholds
  claims: { processing_completed: boolean; transformation_estimated: boolean; evidence_gate: string; ground_truth_validation: string }
  metrics: { method: string; keypoints_ref: number; keypoints_src: number; tentative_matches: number; inliers: number; inlier_ratio: number; coverage: number; rmse_px: number | null; median_error_px: number | null; p95_error_px: number | null; rmse_m: number | null; target_gsd_m: number | null }
  homography: HomographyDiag | null; levels: LevelSummary[]; matcher_paths: Record<string, number>; geometry: Record<string, unknown>
  pair_geometry: null | { status: string; area_km2?: number; vertices?: number; polygon?: [number, number][]; ref_polygon?: [number, number][]; src_polygon?: [number, number][] }
  grid: null | { h: number; w: number; target_gsd_m: number; mode: string; preview_scale: number; preview_w: number; preview_h: number }
  images: Record<string, string>; reason?: string | null
  points: { ref: [number, number][]; src: [number, number][]; inlier: number[]; residual_px: number[]; total: number; shown: number }
  elapsed_s: number; engine_config: Record<string, unknown>; engine: EngineInfo
  warnings: { code: string; detail: string }[]; finished_utc: string
}
export interface RunResult { id: string; payload: RunPayload; images: Record<string, Blob>; savedLocally?: boolean; overrides: Record<string, unknown>; hashes: Record<string, Record<string, string>>; files: { path: string; size: number; lastModified: number }[]; config: RunConfig; limits: MemoryPreset; userNotes?: string }

export interface EngineInfo { python: string; platform: string; numpy: string; opencv: string; scipy: string; shapely: string; gate: GateThresholds; io_backend: string }
export type MemoryPreset = { name: 'conservative' | 'standard' | 'extended'; max_geometry_csv_mb: number; max_grid_pixels: number; max_preview_dim: number; canvas_px: number }

export interface ProgressEvent { type: 'stage' | 'level' | 'tile'; t: number; stage?: string; level?: number; levels?: number; target_gsd_m?: number; grid?: number[]; mode?: string; tile?: number; tiles?: number; matcher_path?: string; matches?: number }
