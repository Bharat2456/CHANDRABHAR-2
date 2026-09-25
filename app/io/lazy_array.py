from pathlib import Path
import numpy as np
class LazyArray:
 def __init__(self,path,shape,dtype,offset=0,interleave='native',order='C'):
  self.path=Path(path); self.shape=tuple(shape); self.dtype=np.dtype(dtype); self.offset=int(offset); self.interleave=interleave.lower(); self.order=order; self._mm=None
 def _open(self):
  if self._mm is None:self._mm=np.memmap(self.path,mode='r',dtype=self.dtype,offset=self.offset,shape=self.shape,order=self.order)
  return self._mm
 def spatial_shape(self):
  if len(self.shape)==2:return self.shape
  if self.interleave=='bsq':return self.shape[1],self.shape[2]
  if self.interleave=='bil':return self.shape[0],self.shape[2]
  if self.interleave=='bip':return self.shape[0],self.shape[1]
  raise ValueError('unsupported interleave '+self.interleave)
 def read(self,r0,r1,c0,c1,band=0):
  a=self._open()
  if a.ndim==2:return np.asarray(a[r0:r1,c0:c1])
  if self.interleave=='bsq':return np.asarray(a[band,r0:r1,c0:c1])
  if self.interleave=='bil':return np.asarray(a[r0:r1,band,c0:c1])
  if self.interleave=='bip':return np.asarray(a[r0:r1,c0:c1,band])
  raise ValueError('unsupported interleave '+self.interleave)
