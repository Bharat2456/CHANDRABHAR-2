# 04 — Data and Sensors

## Source

Chandrayaan-2 mission products are distributed by ISRO through the PRADAN archive
(ISSDC): https://pradan.issdc.gov.in/ch2/ — this is an external reference; verify current terms
there before use. See [`LEGAL/ISRO_DATA_ATTRIBUTION.md`](../LEGAL/ISRO_DATA_ATTRIBUTION.md).

This repository does **not** include or redistribute any Chandrayaan-2 mission data. The
dashboard and CLI read a local folder you point them at.

## Sensors

### OHRC — Orbiter High Resolution Camera
- Panchromatic, ~0.3 m native GSD.
- Supplied as generic binary raster products plus a PDS4 XML label.

### TMC-2 — Terrain Mapping Camera-2
- Panchromatic, ~5 m native GSD.
- Supplied as generic binary raster products (PDS4 XML label), with derived GeoTIFF products
  also available from the archive for some passes.

### IIRS — Imaging Infrared Spectrometer
- Hyperspectral, ~80 m native GSD.
- Supplied as a generic binary raster product (PDS4 XML label) with many spectral bands; this
  project's representation stage (`app/core/representation.py`) reduces a sampled subset of
  bands to a robust spectral median/IQR/shape representation rather than matching on raw bands.

## Product discovery

`app/adapters/AdapterRegistry.inspect()` classifies a product by inspecting its label file
(`.xml` for PDS4, `.hdr` for ENVI) and extracts: sensor name, product ID, array shape/dtype, GSD
(if stated in the label), solar elevation/azimuth (if present), and acquisition start time. The
dashboard's Mission Overview page scans a folder for filenames matching the `ch2_ohr`, `ch2_tmc`,
`ch2_iir` naming convention and calls this inspector on each.

## Metadata actually shown

The dashboard and CLI display only values the adapter actually extracted from the product's own
label — GSD, sun angle, acquisition timestamp, shape, dtype, product ID. Where a field is not
present in the source label, it is shown as unavailable rather than filled with a placeholder or
assumed value (per the project's no-fabrication rule, see
[`docs/CLAIMS_MATRIX.md`](CLAIMS_MATRIX.md)).

## What makes this pairing hard

See [`docs/02_PROBLEM_STATEMENT.md`](02_PROBLEM_STATEMENT.md) for the scale/modality/illumination
comparison table.
