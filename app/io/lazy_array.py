"""Lazy, window-addressed access to raw binary rasters.

Two interchangeable backends share one contract (``read`` returns a copy of a window):

* ``memmap``  – NumPy memory map (fast on desktop operating systems).
* ``stream``  – explicit ``seek``/``readinto`` of only the bytes a window needs.  This is
  the backend used in the browser, where the file lives in a WORKERFS mount that cannot be
  memory-mapped, and it keeps peak memory proportional to the requested window.

Both backends are tested for bit-exact agreement (tests/test_lazy_array.py).
"""
from __future__ import annotations

import os
from pathlib import Path
import numpy as np

_STREAM_WHEN_NARROW = 0.5   # read per-row segments if window is narrower than this fraction


class LazyArray:
    def __init__(self, path, shape, dtype, offset=0, interleave='native', order='C', backend=None):
        self.path = Path(path); self.shape = tuple(int(s) for s in shape); self.dtype = np.dtype(dtype)
        self.offset = int(offset); self.interleave = interleave.lower(); self.order = order; self._mm = None
        if order != 'C':
            raise ValueError("only C-ordered rasters are supported")
        env = os.environ.get('CHANDRABHAR_IO', '').lower()
        self.backend = (backend or env or 'auto').lower()
        if self.backend == 'auto':
            self.backend = 'stream' if _in_wasm() else 'memmap'
        if self.backend not in {'memmap', 'stream'}:
            raise ValueError('unknown backend ' + self.backend)
        self._f = None

    # ---- geometry ---------------------------------------------------------------------
    def spatial_shape(self):
        if len(self.shape) == 2: return self.shape
        if self.interleave == 'bsq': return self.shape[1], self.shape[2]
        if self.interleave == 'bil': return self.shape[0], self.shape[2]
        if self.interleave == 'bip': return self.shape[0], self.shape[1]
        raise ValueError('unsupported interleave ' + self.interleave)

    def band_count(self):
        if len(self.shape) == 2: return 1
        if self.interleave == 'bsq': return self.shape[0]
        if self.interleave == 'bil': return self.shape[1]
        if self.interleave == 'bip': return self.shape[2]
        raise ValueError('unsupported interleave ' + self.interleave)

    # ---- backends ---------------------------------------------------------------------
    def _open(self):
        if self._mm is None:
            self._mm = np.memmap(self.path, mode='r', dtype=self.dtype, offset=self.offset, shape=self.shape, order=self.order)
        return self._mm

    def close(self):
        if self._f is not None:
            self._f.close(); self._f = None
        self._mm = None

    def _file(self):
        if self._f is None:
            self._f = open(self.path, 'rb')
        return self._f

    def _read_elems(self, elem_start: int, count: int) -> np.ndarray:
        isz = self.dtype.itemsize
        js_read = _js_reader()
        if js_read is not None:
            # Browser: Python's seek() is limited to 2 GiB (32-bit C long in wasm32). The host reads through
            # the Emscripten FS API with 64-bit-safe positions; only the requested bytes are materialised.
            need = count * isz
            arr = js_read(str(self.path), self.offset + elem_start * isz, need)
            raw = bytes(arr.to_py())
            if len(raw) != need: raise EOFError(f'{self.path.name}: truncated raster (wanted {need} bytes at element {elem_start})')
            return np.frombuffer(raw, dtype=self.dtype, count=count)
        f = self._file(); f.seek(self.offset + elem_start * isz)
        buf = np.empty(count, self.dtype)
        mv = memoryview(buf).cast('B'); need = count * isz; got = 0
        while got < need:
            n = f.readinto(mv[got:])
            if not n: raise EOFError(f'{self.path.name}: truncated raster (wanted {need} bytes at element {elem_start})')
            got += n
        return buf

    def _stream_plane(self, plane_elem0: int, nrows: int, ncols: int, r0, r1, c0, c1) -> np.ndarray:
        """Read rows r0:r1, cols c0:c1 from a row-major plane of shape (nrows, ncols)."""
        h, w = r1 - r0, c1 - c0
        if h <= 0 or w <= 0: return np.empty((max(h, 0), max(w, 0)), self.dtype)
        if w >= ncols * _STREAM_WHEN_NARROW:
            blk = self._read_elems(plane_elem0 + r0 * ncols, h * ncols).reshape(h, ncols)
            return blk[:, c0:c1].copy()
        out = np.empty((h, w), self.dtype)
        for i in range(h):
            out[i] = self._read_elems(plane_elem0 + (r0 + i) * ncols + c0, w)
        return out

    def _check(self, r0, r1, c0, c1, band):
        H, W = self.spatial_shape()
        if not (0 <= r0 <= r1 <= H and 0 <= c0 <= c1 <= W):
            raise IndexError(f'window ({r0}:{r1}, {c0}:{c1}) outside raster {H}x{W}')
        if not (0 <= band < self.band_count()):
            raise IndexError(f'band {band} outside 0..{self.band_count()-1}')

    # ---- public -----------------------------------------------------------------------
    def read(self, r0, r1, c0, c1, band=0):
        r0, r1, c0, c1, band = int(r0), int(r1), int(c0), int(c1), int(band)
        if self.backend == 'memmap':
            a = self._open()
            if a.ndim == 2: return np.asarray(a[r0:r1, c0:c1])
            if self.interleave == 'bsq': return np.asarray(a[band, r0:r1, c0:c1])
            if self.interleave == 'bil': return np.asarray(a[r0:r1, band, c0:c1])
            if self.interleave == 'bip': return np.asarray(a[r0:r1, c0:c1, band])
            raise ValueError('unsupported interleave ' + self.interleave)
        self._check(r0, r1, c0, c1, band)
        if len(self.shape) == 2:
            H, W = self.shape
            return self._stream_plane(0, H, W, r0, r1, c0, c1)
        if self.interleave == 'bsq':
            B, H, W = self.shape
            return self._stream_plane(band * H * W, H, W, r0, r1, c0, c1)
        if self.interleave == 'bil':
            H, B, W = self.shape
            h, w = r1 - r0, c1 - c0
            out = np.empty((h, w), self.dtype)
            for i in range(h):
                out[i] = self._read_elems(((r0 + i) * B + band) * W + c0, w)
            return out
        if self.interleave == 'bip':
            H, W, B = self.shape
            h, w = r1 - r0, c1 - c0
            out = np.empty((h, w), self.dtype)
            for i in range(h):
                seg = self._read_elems(((r0 + i) * W + c0) * B, w * B).reshape(w, B)
                out[i] = seg[:, band]
            return out
        raise ValueError('unsupported interleave ' + self.interleave)


def _in_wasm() -> bool:
    import sys
    return sys.platform in {'emscripten', 'wasi'}


def _js_reader():
    """Host-provided slice reader (set by the web worker); None on desktop."""
    if not _in_wasm(): return None
    try:
        import js
        return getattr(js, 'cb2ReadSlice', None)
    except Exception:
        return None
