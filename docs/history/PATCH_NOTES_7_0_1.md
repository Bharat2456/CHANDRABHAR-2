# LunaMatch 7.0.1

## Hotfix

Fixes a real-data boundary failure in the physical-resolution overview path where the final streamed tile could be shorter than the requested output slice and trigger a NumPy broadcast error.

## Scientific/architectural correction

The previous v7 overview implementation could apply a computational stride after physical resampling while still reporting the nominal target GSD. 7.0.1 removes that hidden stride. Large scenes are now assembled from physical-resolution tiles, so computational tiling affects memory usage only and does not silently change the physical sampling represented to the matcher.

## Verification

- 6 pytest tests passed
- synthetic self-test passed
- release validation passed
- boundary regression passed
- >25M-pixel tiled-path regression passed
