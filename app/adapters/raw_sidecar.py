from pathlib import Path
import json,numpy as np
from app.model import SceneSpec,ArraySpec
class RawSidecarAdapter:
 name='raw_sidecar'
 @classmethod
 def can_open(cls,path): return path.suffix.lower() in {'.raw','.bin','.dat'} and path.with_suffix(path.suffix+'.json').exists()
 @classmethod
 def inspect(cls,path):
  m=json.loads(path.with_suffix(path.suffix+'.json').read_text()); dt=np.dtype(m['dtype']); return SceneSpec(m.get('sensor','UNKNOWN'),m.get('product_id',path.stem),path,ArraySpec(path,tuple(m['shape']),dt,int(m.get('offset',0)),m.get('interleave','native')),gsd_m=m.get('gsd_m'),metadata=m)
