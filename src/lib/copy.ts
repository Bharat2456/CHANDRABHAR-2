/** User-facing wording. Follows branding/brand_guidelines.md: no hype; software correctness is never conflated with scientific validation. */
export const GATE_REASON_TEXT: Record<string, string> = {
  too_few_tentative_matches: 'Fewer than the required number of tentative feature matches were found.',
  too_few_inliers: 'Fewer independent geometric inliers than required survived RANSAC.',
  low_inlier_ratio: 'The inlier ratio is below the configured threshold.',
  low_spatial_coverage: 'Inliers do not cover enough of the 4×4 spatial grid.',
  high_or_missing_rmse: 'Residual error is above the threshold, or no residual could be computed.',
}
export const ENGINE_REASON_TEXT: Record<string, string> = {
  too_few_correspondences: 'Fewer than three correspondences were available, so no transform could be estimated.',
  ransac_failed: 'RANSAC could not find a consistent homography.',
  no_tile_correspondences: 'No tile produced independent correspondences.',
  no_geo_tile_correspondences: 'No geographic-warp tile produced independent correspondences.',
  global_ransac_failed: 'Global RANSAC over all tile correspondences failed.',
  no_descriptors_or_direct_registration: 'No usable descriptors or direct registration were found (low texture or unrelated content).',
  dense_phase_model_generated_correspondences_not_independent: 'Only phase-correlation was possible; its correspondences are model-generated and are not independent evidence.',
  dense_ecc_model_generated_correspondences_not_independent: 'Only ECC refinement was possible; its correspondences are model-generated and are not independent evidence.',
}
export const PROBLEM_TEXT: Record<string, { title: string; fix: string }> = {
  size_mismatch_truncated_or_wrong_dims: { title: 'Binary size does not match the label', fix: 'The data file is truncated, from a different product, or the label dimensions are wrong. Re-copy the data file from its source.' },
  companion_missing: { title: 'Companion file missing', fix: 'Add the data file referenced by the label (select the whole product folder, or the label and its binary together).' },
  unsupported_datatype: { title: 'Unsupported data type', fix: 'The label declares a numeric type this engine does not implement.' },
  unsafe_xml: { title: 'Unsafe XML refused', fix: 'The label declares a DTD or entities. These are refused to prevent entity-expansion attacks.' },
  unsafe_path: { title: 'Unsafe file reference refused', fix: 'The label refers to a path outside its own folder. Only plain file names are accepted.' },
  invalid_dimensions: { title: 'Invalid dimensions', fix: 'The declared array shape is not a valid 2-D or 3-D raster.' },
  no_adapter: { title: 'No adapter recognised this file', fix: 'Supported inputs are PDS4 labels, ENVI headers, NumPy .npy and raw+JSON sidecar.' },
  invalid_metadata: { title: 'Invalid or incomplete metadata', fix: 'The label could not be interpreted. See the technical message below.' },
  empty_file: { title: 'Empty file', fix: 'The file has zero bytes; re-copy it.' },
  label_too_large: { title: 'Label too large', fix: 'Labels above 20 MB are refused.' },
  raw_without_sidecar: { title: 'Raw binary without JSON sidecar', fix: 'Add <name>.json describing dtype, shape, offset, interleave and gsd_m.' },
  unreadable: { title: 'File could not be read', fix: 'The browser could not read this file; check permissions.' },
}
export const IGNORED_TEXT: Record<string, string> = {
  xml_not_pds4: 'XML file is not a PDS4 label', binary_without_label: 'Binary file with no label or sidecar', csv_not_referenced: 'CSV not referenced by any product',
  json_not_sidecar: 'JSON file is not a raw-data sidecar', unsupported_format: 'Unsupported format',
}
export const PAIR_TEXT: Record<string, string> = {
  same_product: 'Choose two different products.', gsd_missing: 'Ground sample distance (GSD) is missing; enter it in the Data Workspace.',
  sensor_unknown: 'Sensor could not be identified; sensor-specific preprocessing will use generic handling.',
  grid_capped: 'The common grid was coarsened to respect the memory preset, so the matching GSD is larger than the cascade level requested.',
  large_gsd_ratio: 'Very large GSD ratio: the common grid is set by the coarser sensor, so fine detail of the finer sensor is not used.',
  no_pair_geometry: 'No geometry tables for this pair: the engine falls back to full-scene matching on a common GSD (no true geographic overlap).',
  geometry_unreadable: 'Geometry table could not be read.', no_overlap: 'The two footprints do not overlap.',
}
export const WARNING_TEXT: Record<string, string> = {
  sensor_unknown: 'Sensor not identified', gsd_missing: 'GSD missing', no_geometry_csv: 'No geometry table found', geometry_too_large: 'Geometry table exceeds the memory preset',
}
export const STAGE_TEXT: Record<string, string> = {
  start: 'Starting', geometry_intersection: 'Computing true swath intersection', matching_level: 'Common-grid matching', evidence_gate: 'Applying evidence gate', packaging_evidence: 'Packaging evidence',
}
export const CLAIM_LABELS = {
  processing: 'Processing completed', transform: 'Transformation estimated', gate: 'Evidence gate (configured thresholds)', truth: 'Independent ground-truth validation',
}
export const LIMITATION_STATEMENT = 'A passed evidence gate is an internal geometric-consistency test. It is not independent ground-truth validation, and no mission validation is claimed by this software.'
export const PRIVACY_STATEMENT = 'Your mission files are read and processed in this browser tab. They are not uploaded, and no analytics or telemetry is used. Static application files are downloaded from the host once; after that, processing makes no network requests.'
export const SUBTITLE = 'Multi-modal, illumination-aware and scale-aware image correspondence for Chandrayaan-2 OHRC, TMC-2 and IIRS imagery'
