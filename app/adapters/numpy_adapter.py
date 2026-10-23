from pathlib import Path
import numpy as np
from numpy.lib import format as npfmt
from app.model import SceneSpec,ArraySpec
from app.safepath import checked_shape
class NumpyAdapter:
 name='numpy'
 @classmethod
 def can_open(cls,path): return path.suffix.lower()=='.npy'
 @classmethod
 def inspect(cls,path,root=None):
  path=Path(path)
  with path.open('rb') as f:
   ver=npfmt.read_magic(f)
   shape,fortran,dt=(npfmt.read_array_header_1_0(f) if ver==(1,0) else npfmt.read_array_header_2_0(f))
   offset=f.tell()
  if dt.hasobject: raise ValueError('object arrays are not supported')
  if fortran: raise ValueError('Fortran-ordered .npy arrays are not supported')
  shape=checked_shape(shape) if len(shape)>0 else (_ for _ in ()).throw(ValueError('0-d array'))
  if len(shape) not in (2,3): raise ValueError(f'expected a 2-D or 3-D array, got {len(shape)}-D')
  expected=offset+int(np.prod(shape,dtype=object))*dt.itemsize
  if expected!=path.stat().st_size: raise ValueError(f'NPY size mismatch: expected {expected}, actual {path.stat().st_size}')
  # 3-D arrays are interpreted band-sequential (bands, lines, samples).
  inter='bsq' if len(shape)==3 else 'native'
  return SceneSpec('NUMPY',path.stem,path,ArraySpec(path,shape,dt,offset,inter),metadata={'numpy':True,'npy_header_offset':offset})
