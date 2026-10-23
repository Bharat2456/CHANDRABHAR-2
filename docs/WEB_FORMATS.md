# Supported formats and companion-file rules

Only formats implemented by the engine adapters are supported. Select **all** files of a product together (or the archive folder).

| Format | Primary | Required companions | Optional | Rules enforced |
|---|---|---|---|---|
| PDS4 | `*.xml` with `logical_identifier` | binary named by `<file_name>` (plain name; searched beside the label, in `data/calibrated/<date>/`, then anywhere in the selection) | geometry CSV `Scan,Pixel,Latitude,Longitude` (ISRO layout `…/geometry/calibrated/<date>/*.csv`, matched by product id) | data type ∈ supported PDS4 types; axes → shape; `file size == offset + product(shape) × itemsize`; GSD from `pixel_resolution`; solar elevation/azimuth |
| ENVI | `*.hdr` | binary with the same stem (`.qub`/`.img`/`.dat`/`.raw`/none) | — | BSQ/BIL/BIP; byte order; header offset; data types 1–5, 12–15; exact size check; GSD from `pixel size` |
| NumPy | `*.npy` | — | — | 2-D (lines, samples) or 3-D (bands, lines, samples) C-order; no object dtype; exact size; **GSD must be supplied manually** |
| Raw + sidecar | `*.raw` `*.bin` `*.dat` | `<file>.json` with `dtype`, `shape` | `offset`, `interleave` (required for 3-D), `sensor`, `product_id`, `gsd_m` | exact size check |

Without a geometry CSV the pair cannot use true swath intersection; the engine falls back to full-scene matching on a common GSD and the UI says so (the result then carries the warning `no_true_swath_intersection`).

Unsupported/unused files are listed with a reason (not a PDS4 label, binary without label, CSV not referenced, …). Only synthetic fixtures were available for testing; **real ISRO products were not tested** in this delivery (see `KNOWN_LIMITATIONS`).
