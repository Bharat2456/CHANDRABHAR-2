from pathlib import Path
import tempfile,json,numpy as np,cv2
from app.adapters import AdapterRegistry
from app.core.pipeline import Engine
from app.model import SceneSpec,ArraySpec
def run():
 """Synthetic end-to-end engine check against a KNOWN transform (not mission validation).

 base -> warped is M (4 deg rotation + (12,-9) px shift), so the engine's source->reference
 homography must equal M^-1.  Pass = enough independent inliers, spatial coverage, and a
 recovered transform within 1.5 px (mean over a 5x5 lattice) of the known one.  The gate
 inlier-ratio is reported but is not a self-test criterion (it is RANSAC/scene dependent).
 """
 rng=np.random.default_rng(7); base=np.zeros((1200,1200),np.uint8)
 for _ in range(80):
  x,y=rng.integers(30,1170,2); r=int(rng.integers(3,25)); cv2.circle(base,(int(x),int(y)),r,int(rng.integers(80,255)),-1)
 for _ in range(30):
  x,y=rng.integers(50,1150,2); cv2.line(base,(int(x),int(y)),(int(x+rng.integers(-80,80)),int(y+rng.integers(-80,80))),int(rng.integers(80,220)),2)
 M=cv2.getRotationMatrix2D((600,600),4.0,1.0); M[:,2]+=[12,-9]; warped=cv2.warpAffine(base,M,(1200,1200),borderMode=cv2.BORDER_REFLECT)
 with tempfile.TemporaryDirectory() as td:
  a=Path(td)/'a.npy'; b=Path(td)/'b.npy'; np.save(a,base); np.save(b,warped)
  sa=AdapterRegistry.inspect(a); sb=AdapterRegistry.inspect(b); sa.gsd_m=0.25; sb.gsd_m=0.25
  res=Engine(levels=(1.0,)).register(sa,sb,'synthetic')
 err=None
 if res.homography is not None:
  Minv=np.linalg.inv(np.vstack([M,[0,0,1]])); g=np.array([[x,y] for x in np.linspace(100,1100,5) for y in np.linspace(100,1100,5)],np.float32).reshape(-1,1,2)
  err=float(np.mean(np.linalg.norm(cv2.perspectiveTransform(g,res.homography)-cv2.perspectiveTransform(g,Minv),axis=2)))
 ok=res.inliers>=12 and res.coverage>=0.35 and err is not None and err<=1.5
 return {'passed':bool(ok),'inliers':res.inliers,'ratio':res.inlier_ratio,'coverage':res.coverage,'rmse_px':res.rmse_px,'known_transform_error_px':err,'gate_status':res.diagnostics.get('status')}
