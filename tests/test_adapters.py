from pathlib import Path
from app.adapters import AdapterRegistry
import numpy as np

def test_numpy(tmp_path):
 p=tmp_path/'x.npy'; np.save(p,np.zeros((8,9),np.uint8)); s=AdapterRegistry.inspect(p); assert s.array.shape==(8,9)
