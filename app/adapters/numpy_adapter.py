from pathlib import Path
import numpy as np
from app.model import SceneSpec,ArraySpec
class NumpyAdapter:
 name='numpy'
 @classmethod
 def can_open(cls,path): return path.suffix.lower()=='.npy'
 @classmethod
 def inspect(cls,path):
  a=np.load(path,mmap_mode='r'); return SceneSpec('NUMPY',path.stem,path,ArraySpec(path,a.shape,a.dtype),metadata={'numpy':True})
