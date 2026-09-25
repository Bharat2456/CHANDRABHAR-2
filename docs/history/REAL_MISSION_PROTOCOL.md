# Real-mission validation protocol

1. Inspect the XML/HDR labels and verify binary-size consistency.
2. Confirm native GSD and acquisition/illumination metadata.
3. Restrict processing to a documented geographic overlap/AOI when a trusted footprint is available.
4. Build representations at common physical GSD levels.
5. Keep computational tiling separate from physical GSD.
6. Estimate geometry with RANSAC and require spatially distributed inliers.
7. Report pairwise evidence independently for OHRC↔TMC-2, OHRC↔IIRS, and TMC-2↔IIRS.
8. Only then report a three-sensor correspondence experiment.
9. Preserve product IDs, labels, configuration, code version, and metrics in the output report.

## Development candidate audit
The v7 development audit also checks that the selected TMC-2 and IIRS product IDs exist in the official PRADAN South-Pole footprint archives supplied during project development. This confirms catalogue identity, not registration success.
