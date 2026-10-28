"""Canary for OpenCV's resampling behaviour, which the geographic warp (cv2.remap, INTER_LINEAR) depends on.

Known behaviours (measured, see docs/WEB_PARITY_ANALYSIS.md):
  * OpenCV <= 4.13 (incl. the 4.11 build inside the WebAssembly runtime): sampling coordinates are quantised to 1/32 px
    (fixed-point INTER_BITS = 5) -> small, bounded deviations from the exact bilinear value.
  * OpenCV >= 5.0: exact float bilinear (error ~ float32 rounding).
What must NEVER change silently is the sub-pixel *convention* (a half-pixel or whole-pixel offset would misregister every
product). This test fails on any behaviour other than the two known ones, and reports which one is installed.
"""
import numpy as np
import cv2


def _exact_bilinear(src, qx, qy):
    x0 = np.floor(qx).astype(int); y0 = np.floor(qy).astype(int); fx = qx - x0; fy = qy - y0
    g = lambda y, x: src[y, x].astype(np.float64)
    return g(y0, x0) * (1 - fx) * (1 - fy) + g(y0, x0 + 1) * fx * (1 - fy) + g(y0 + 1, x0) * (1 - fx) * fy + g(y0 + 1, x0 + 1) * fx * fy


def _measure():
    H, W = 200, 240; yy0, xx0 = np.mgrid[0:H, 0:W]
    smooth = (120 + 60 * np.sin(xx0 / 11.0) + 50 * np.cos(yy0 / 7.0)).astype(np.float32)
    yy, xx = np.mgrid[0:150, 0:170].astype(np.float32)
    qx = (xx * 1.2 + 3.37 + 0.3 * np.sin(yy / 9)).astype(np.float32); qy = (yy * 1.1 - 2.21 + 0.2 * np.cos(xx / 7)).astype(np.float32)
    out = cv2.remap(smooth, qx, qy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT).astype(np.float64)
    inner = (qx > 2) & (qx < W - 3) & (qy > 2) & (qy < H - 3)
    return float(np.abs(out - _exact_bilinear(smooth, qx, qy))[inner].max())


def test_remap_subpixel_convention_is_one_of_the_two_known_behaviours(record_property):
    err = _measure()
    mode = 'exact-float-bilinear' if err < 1e-3 else 'fixed-point-1/32px'
    record_property('opencv_remap_mode', f'{cv2.__version__}: {mode} (max err {err:.3g} gray levels)')
    # smooth test image: fixed-point quantisation (<= 1/32 px x gradient ~0.2) is the largest legitimate deviation.
    # A half-pixel/whole-pixel offset would give errors of tens of gray levels.
    assert err < 0.25, f"OpenCV {cv2.__version__} remap deviates {err:.3g} from exact bilinear: sub-pixel convention may have changed"
