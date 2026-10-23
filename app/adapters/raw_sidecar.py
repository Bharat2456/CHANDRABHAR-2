from pathlib import Path
import json,numpy as np
from app.model import SceneSpec,ArraySpec
from app.safepath import read_text_limited, checked_shape
class RawSidecarAdapter:
 name='raw_sidecar'
 @classmethod
 def can_open(cls,path): return path.suffix.lower() in {'.raw','.bin','.dat'} and path.with_suffix(path.suffix+'.json').exists()
 @classmethod
 def inspect(cls,path,root=None):
  path=Path(path)
  m=json.loads(read_text_limited(path.with_suffix(path.suffix+'.json')))
  if not isinstance(m,dict): raise ValueError('sidecar JSON must be an object')
  dt=np.dtype(m['dtype']); shape=checked_shape(m['shape']); off=int(m.get('offset',0)); inter=str(m.get('interleave','native'))
  if dt.hasobject: raise ValueError('object dtype is not supported')
  if off<0: raise ValueError('negative offset')
  if len(shape)==3 and inter.lower() not in {'bsq','bil','bip'}: raise ValueError('3-D rasters need interleave bsq|bil|bip')
  expected=off+int(np.prod(shape,dtype=object))*dt.itemsize
  if expected!=path.stat().st_size: raise ValueError(f'raw size mismatch: expected {expected}, actual {path.stat().st_size}')
  gsd=m.get('gsd_m'); gsd=float(gsd) if gsd is not None else None
  return SceneSpec(str(m.get('sensor','UNKNOWN')),str(m.get('product_id',path.stem)),path,ArraySpec(path,shape,dt,off,inter),gsd_m=gsd,metadata=m)
