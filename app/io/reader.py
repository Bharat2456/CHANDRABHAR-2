from __future__ import annotations
import numpy as np
from app.model import SceneSpec
from app.io.lazy_array import LazyArray
class SceneReader:
 def __init__(self,spec): self.spec=spec; self.a=LazyArray(spec.array.path,spec.array.shape,spec.array.dtype,spec.array.offset,spec.array.interleave,spec.array.order)
 @property
 def spatial_shape(self): return self.a.spatial_shape()
 def read_native(self,r0,r1,c0,c1,band=0): return self.a.read(r0,r1,c0,c1,band)
 def read_resampled(self,r0,r1,c0,c1,target_gsd,band=0,method='area'):
  import cv2
  src_gsd=float(self.spec.gsd_m or target_gsd); factor=float(target_gsd)/src_gsd
  if factor<=1.000001:
   return self.read_native(r0,r1,c0,c1,band).astype(np.float32,copy=False), src_gsd
  arr=self.read_native(r0,r1,c0,c1,band).astype(np.float32,copy=False)
  oh=max(1,int(round(arr.shape[0]/factor))); ow=max(1,int(round(arr.shape[1]/factor)))
  out=cv2.resize(arr,(ow,oh),interpolation=cv2.INTER_AREA)
  return out,float(src_gsd*arr.shape[0]/max(oh,1))
 def read_block_mean(self,r0,r1,c0,c1,fy,fx,band=0):
  # Exact streaming block mean; avoids allocating the complete high-resolution window.
  h=(r1-r0+fy-1)//fy; w=(c1-c0+fx-1)//fx
  out=np.empty((h,w),np.float32)
  for i,rr in enumerate(range(r0,r1,fy)):
   rr1=min(r1,rr+fy); row=self.read_native(rr,rr1,c0,c1,band).astype(np.float32,copy=False)
   # weighted area pooling for final partial blocks
   for j,cc in enumerate(range(c0,c1,fx)):
    out[i,j]=np.nanmean(row[:,cc-c0:min(cc-c0+fx,row.shape[1])])
  return out
 def read_iirs_rep(self,r0,r1,c0,c1,band_indices=None):
  if len(self.spec.array.shape)!=3: return self.read_native(r0,r1,c0,c1,0).astype(np.float32)
  bands=self.spec.array.shape[0] if self.spec.array.interleave=='bsq' else self.spec.array.shape[-1]
  ids=band_indices or np.linspace(0,bands-1,min(12,bands),dtype=int).tolist()
  stack=[self.read_native(r0,r1,c0,c1,int(b)).astype(np.float32) for b in ids]
  x=np.stack(stack,axis=0); med=np.nanmedian(x,axis=0)
  invalid=~np.isfinite(x)
  if invalid.any(): x=np.where(invalid,med[None,...],x)
  x=np.sort(x,axis=0)
  q1=x[max(0,len(ids)//4-1)]; q3=x[min(len(ids)-1,(3*len(ids))//4)]
  spread=q3-q1
  med=np.nan_to_num(med,nan=0.0,posinf=0.0,neginf=0.0); spread=np.nan_to_num(spread,nan=0.0,posinf=0.0,neginf=0.0)
  return np.stack([med,spread],axis=-1)
