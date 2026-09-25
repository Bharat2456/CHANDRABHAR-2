# v8.0.1 patch notes

## Fixed
1. OpenCV `cv2.remap` hard dimension limit (`SHRT_MAX`) for large native source windows.
2. ECC return-order bug (`correlation, warp = findTransformECC(...)`).
3. Dense ECC correspondences were incorrectly able to pass the same RANSAC/evidence gate as independent SIFT matches.

## Scientific safety
ECC/phase correlation are fallback/support paths. A dense model-generated correspondence field is not treated as independent feature evidence for final validation.
