# LunaMatch 8.0

## Correspondence upgrade

The major remaining weakness after v7.0.6 was not file I/O but the fact that physical-GSD resampling still left each sensor in its own native image geometry. v8.0 adds a geographic common-grid stage using the actual ISRO GRD Scan/Pixel samples.

Each pair now follows:

1. sampled GRD swath reconstruction
2. true polygon intersection
3. common lunar metric grid at target GSD
4. inverse geographic mapping into each native image
5. modality-specific structural/spectral representation
6. SIFT / phase-correlation / ECC fallback
7. global geometric consensus and evidence gate

This is designed to address curved polar geometry and severe modality/resolution differences without claiming that a weak correspondence is validated.
