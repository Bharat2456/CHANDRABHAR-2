# Claims Matrix

Claim-by-claim implementation/validation status, engine v8.0.2 (CHANDRABHAR-2 platform v2.0.0).
This table is the authoritative claim status referenced throughout `docs/` — if any other
document's wording ever conflicts with this table, this table is correct.

| Claim | v8 status |
|---|---|
| PDS4 / ENVI / TIFF / NumPy / raw-sidecar adapter architecture | Implemented |
| ISRO GRD Scan/Pixel geometry discovery | Implemented |
| Sampled swath perimeter intersection | Implemented |
| Common geographic metric grid | Implemented |
| Physical GSD invariant | Implemented and regression-tested |
| IIRS spectral representation | Implemented |
| Multimodal matcher cascade | Implemented |
| Real OHRC↔TMC-2 validation | Must be re-run on v8 real data |
| Real OHRC↔IIRS validation | Must be re-run on v8 real data |
| Real TMC-2↔IIRS validation | Must be re-run on v8 real data |
| Three-sensor scientific validation | Not claimed |
