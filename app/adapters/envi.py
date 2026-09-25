from pathlib import Path
import re,numpy as np
from app.model import SceneSpec,ArraySpec
DT={1:np.uint8,2:np.int16,3:np.int32,4:np.float32,5:np.float64,12:np.uint16,13:np.uint32,14:np.int64,15:np.uint64}
class ENVIAdapter:
 name='envi'
 @classmethod
 def can_open(cls,path): return path.suffix.lower()=='.hdr'
 @classmethod
 def inspect(cls,path):
  path=Path(path); txt=path.read_text(errors='ignore')
  def get(k,d=None):
   m=re.search(rf'^\s*{re.escape(k)}\s*=\s*([^\n]+)',txt,re.I|re.M); return m.group(1).strip() if m else d
  samples=int(get('samples')); lines=int(get('lines')); bands=int(get('bands',1)); off=int(get('header offset',0)); inter=get('interleave','bsq').lower(); bo=int(get('byte order',0)); code=int(get('data type'))
  dt=np.dtype(DT[code]).newbyteorder('<' if bo==0 else '>'); data=next((p for p in (path.with_suffix('.qub'),path.with_suffix('.img'),path.with_suffix('')) if p.exists()),None)
  if data is None: raise FileNotFoundError('ENVI binary beside header not found')
  shape=(lines,samples) if bands==1 else ((bands,lines,samples) if inter=='bsq' else ((lines,bands,samples) if inter=='bil' else (lines,samples,bands)))
  expected=off+int(np.prod(shape))*dt.itemsize
  if expected!=data.stat().st_size: raise ValueError(f'ENVI binary size mismatch: expected {expected}, actual {data.stat().st_size}')
  gsd=None
  m=re.search(r'pixel size\s*=\s*\{?([^,}]+)',txt,re.I)
  if m:
   try: gsd=float(m.group(1))
   except: pass
  return SceneSpec('ENVI',path.stem,path,ArraySpec(data,shape,dt,off,inter,(), 'C'),gsd_m=gsd,metadata={'envi_header':str(path)})
