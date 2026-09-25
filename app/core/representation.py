import cv2,numpy as np

def robust_norm(x):
 x=np.asarray(x,np.float32); finite=np.isfinite(x)
 if not finite.any(): return np.zeros_like(x)
 lo,hi=np.nanpercentile(x[finite],[2,98]); y=np.clip((x-lo)/max(hi-lo,1e-6),0,1); return y.astype(np.float32)

def structural(x):
 x=robust_norm(x); gx=cv2.Sobel(x,cv2.CV_32F,1,0,ksize=3); gy=cv2.Sobel(x,cv2.CV_32F,0,1,ksize=3); mag=cv2.magnitude(gx,gy); return robust_norm(mag)

def illumination_invariant(x,solar_elev=None,solar_az=None):
 x=robust_norm(x); log=np.log1p(8*x)/np.log(9); hp=x-cv2.GaussianBlur(x,(0,0),2); st=structural(x)
 gx=cv2.Sobel(x,cv2.CV_32F,1,0,ksize=3); gy=cv2.Sobel(x,cv2.CV_32F,0,1,ksize=3)
 if solar_az is not None:
  a=np.deg2rad(float(solar_az)); directional=np.cos(a)*gx+np.sin(a)*gy; directional=robust_norm(np.abs(directional))
 else: directional=robust_norm(np.abs(gx)+np.abs(gy))
 return np.stack([log,robust_norm(hp),st,directional],axis=-1)

def modality_rep(x,solar_elev=None,solar_az=None):
 if x.ndim==3 and x.shape[-1]>=2:
  base=robust_norm(x[...,0]); spread=robust_norm(x[...,1]); channels=[base,spread,structural(base)]
  if x.shape[-1]>=3: channels.append(robust_norm(x[...,2]))
  return np.stack(channels,axis=-1)
 return illumination_invariant(x,solar_elev,solar_az)
