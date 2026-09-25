import numpy as np
from app.core.representation import illumination_invariant
def test_rep():
 x=np.random.default_rng(2).random((100,120),dtype=np.float32); y=illumination_invariant(x,10,45); assert y.shape==(100,120,4) and np.isfinite(y).all()
