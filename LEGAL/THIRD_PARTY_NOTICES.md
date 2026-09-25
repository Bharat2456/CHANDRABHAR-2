# Third-Party Notices

CHANDRABHAR-2 depends on the following open-source packages. Versions below (where marked
"resolved") are what was actually installed and verified when this documentation was prepared;
constraints are from `requirements.txt` / `requirements-optional.txt` / `requirements-dev.txt` in
this repository. Confirm exact versions and current license text against each project's own
repository/PyPI page before distribution — this table is a good-faith summary, not a substitute
for each project's own license file.

## Direct requirements (`requirements.txt`)

| Package | Constraint | Resolved version | License | Purpose in CHANDRABHAR-2 |
|---|---|---|---|---|
| NumPy | `>=1.24,<3` | 2.4.4 | BSD 3-Clause | Core array operations throughout `app/core` |
| opencv-python | `>=4.8,<5` | 4.13.0.92 | Apache 2.0 | Image warping, Sobel/gradient ops, SIFT/ECC matching, evidence-image rendering |
| Shapely | `>=2.0,<3` | 2.1.2 | BSD 3-Clause | Exact footprint polygon intersection (`app/geo/mapper.py`) |
| SciPy | `>=1.10,<2` | 1.17.1 | BSD 3-Clause | `LinearNDInterpolator` for Scan/Pixel↔Lat/Lon geometry fitting |
| Streamlit | `>=1.49,<2` | 1.64.0 | Apache 2.0 | Dashboard UI framework (`dashboard.py`) |

## Optional (`requirements-optional.txt`)

| Package | Constraint | License | Purpose |
|---|---|---|---|
| pyshp | `>=2.3` | MIT | Additional shapefile format support |
| rasterio | `>=1.3` | BSD 3-Clause | Additional raster/GeoTIFF format support |
| pyproj | `>=3.6` | MIT | Additional coordinate-reference-system support |

Not installed/resolved in the environment used to prepare this documentation; confirm current
version and license on PyPI before use.

## Development (`requirements-dev.txt`)

| Package | Constraint | Resolved version | License | Purpose |
|---|---|---|---|---|
| pytest | `>=8` | 9.1.1 | MIT | Test runner for `tests/` |

## Transitive dependencies worth noting

Streamlit itself brings in Pillow, pandas, and pyarrow as its own dependencies (used by
Streamlit's UI widgets, e.g. image display and dataframe rendering) — CHANDRABHAR-2's own code
does not import them directly.

| Package | Resolved version | License |
|---|---|---|
| Pillow | 12.1.1 | HPND (historical "PIL Software License", permissive) |
| pandas | 3.0.2 | BSD 3-Clause |
| pyarrow | 25.0.1 | Apache 2.0 |

## No modification of third-party source

CHANDRABHAR-2 uses these packages as installed dependencies via `pip`; no third-party source code
is vendored or modified in this repository. Each package's own license governs its use and
redistribution and is not superseded by CHANDRABHAR-2's own license status (see
[`LICENSE.md`](LICENSE.md)).
