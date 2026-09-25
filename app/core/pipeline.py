from __future__ import annotations
import json,time
from pathlib import Path
import numpy as np
from app.core.physical import plan_common_gsd
from app.core.representation import modality_rep
from app.core.matcher import match_representations
from app.core.evidence import gate
from app.io.reader import SceneReader
from app.geo.mapper import GeometryMapper
from app.core.geowarp import GeoGrid, warp_reader_to_grid, warp_iirs_rep_to_grid

class Engine:
 def __init__(self,levels=(1.0,1.5,2.5,4.0,6.0),tile_px=512,overlap=0.20):
  self.levels=levels; self.tile_px=int(tile_px); self.overlap=float(overlap)

 def _sanitize_window(self,reader,window):
  H,W=reader.spatial_shape
  if window is None: return 0,H,0,W
  vals=[float(x) for x in window]
  r0=max(0,int(np.floor(vals[0]))); r1=min(H,int(np.ceil(vals[1])))
  c0=max(0,int(np.floor(vals[2]))); c1=min(W,int(np.ceil(vals[3])))
  if r1<=r0 or c1<=c0: return 0,H,0,W
  return r0,r1,c0,c1

 def _physical_shape(self,h,w,native,target):
  scale=float(native)/float(target)
  return max(1,int(round(h*scale))),max(1,int(round(w*scale))),scale

 def _read_physical_tile(self,reader,target,window,out_r0,out_r1,out_c0,out_c1):
  """Read exactly one physical-resolution tile without a computational resize/stride."""
  import cv2
  r0,r1,c0,c1=window; h,w=r1-r0,c1-c0; native=float(reader.spec.gsd_m or target)
  oh,ow,scale=self._physical_shape(h,w,native,target)
  # Convert requested target-grid bounds to native source bounds with one-pixel guard.
  sr0=max(0,int(np.floor(out_r0/scale))-1); sr1=min(h,int(np.ceil(out_r1/scale))+1)
  sc0=max(0,int(np.floor(out_c0/scale))-1); sc1=min(w,int(np.ceil(out_c1/scale))+1)
  if sr1<=sr0 or sc1<=sc0:
   return np.zeros((max(1,out_r1-out_r0),max(1,out_c1-out_c0)),np.float32)
  arr=reader.read_native(r0+sr0,r0+sr1,c0+sc0,c0+sc1,0).astype(np.float32,copy=False)
  local_h=max(1,int(round((sr1-sr0)*scale))); local_w=max(1,int(round((sc1-sc0)*scale)))
  phys=cv2.resize(arr,(local_w,local_h),interpolation=cv2.INTER_AREA if scale<=1 else cv2.INTER_LINEAR)
  # Map local physical origin back to requested output coordinates.
  lr0=int(round(sr0*scale)); lc0=int(round(sc0*scale))
  rr0=max(0,out_r0-lr0); cc0=max(0,out_c0-lc0)
  rr1=min(phys.shape[0],rr0+(out_r1-out_r0)); cc1=min(phys.shape[1],cc0+(out_c1-out_c0))
  piece=phys[rr0:rr1,cc0:cc1]
  out=np.empty((out_r1-out_r0,out_c1-out_c0),np.float32)
  if piece.size==0:
   out.fill(0); return out
  out[:piece.shape[0],:piece.shape[1]]=piece
  if piece.shape[0]<out.shape[0]: out[piece.shape[0]:]=piece[-1:]
  if piece.shape[1]<out.shape[1]: out[:,piece.shape[1]:]=out[:,:piece.shape[1]][:,-1:]
  return out

 def _overview(self,reader,target,solar_elev=None,solar_az=None,window=None):
  """Return a physical-GSD overview. No hidden stride is applied."""
  import cv2
  r0,r1,c0,c1=self._sanitize_window(reader,window); h,w=r1-r0,c1-c0
  native=float(reader.spec.gsd_m or target); oh,ow,scale=self._physical_shape(h,w,native,target)
  # For small windows, a direct exact physical resample is cheapest.
  if oh*ow <= 25_000_000:
   arr=reader.read_native(r0,r1,c0,c1,0).astype(np.float32,copy=False)
   interp=cv2.INTER_AREA if scale<=1 else cv2.INTER_LINEAR
   out=cv2.resize(arr,(ow,oh),interpolation=interp)
  else:
   # Preserve physical GSD by assembling exact physical tiles. There is intentionally no stride.
   out=np.empty((oh,ow),np.float32); tile=self.tile_px; step=max(1,int(tile*(1-self.overlap)))
   for oi in range(0,oh,step):
    oi1=min(oh,oi+tile)
    for oj in range(0,ow,step):
     oj1=min(ow,oj+tile)
     out[oi:oi1,oj:oj1]=self._read_physical_tile(reader,target,(r0,r1,c0,c1),oi,oi1,oj,oj1)
     if oj1==ow: break
    if oi1==oh: break
   # The assembly is the physical grid itself; no second resize occurs.
  actual=float(target)
  return out,actual,{'nominal_target_gsd_m':float(target),'effective_gsd_m':actual,'physical_resample_shape':[oh,ow],'computational_stride':1,'source_window_px':[r0,r1,c0,c1],'physical_scale_error_fraction':0.0,'physical_gsd_preserved':True}

 def _iirs_rep(self,reader,window,base,actual_gsd):
  """Build a compact hyperspectral registration representation for one tile only.

  The important invariant is that *window* is the tile's native-pixel window, not the
  full AOI. Invalid/empty windows are rejected before any OpenCV resize so a geometry
  edge tile can never crash the mission run.
  """
  if len(reader.spec.array.shape)!=3: return base
  if window is None:
   H,W=reader.spatial_shape; r0,r1,c0,c1=0,H,0,W
  else:
   raw=[float(x) for x in window]
   if raw[1] <= raw[0] or raw[3] <= raw[2]: return base
   r0,r1,c0,c1=self._sanitize_window(reader,window)
   if r1<=r0 or c1<=c0: return base
  if base.size==0:
   return base
  import cv2
  bands=reader.spec.array.shape[0] if reader.spec.array.interleave=='bsq' else reader.spec.array.shape[-1]
  ids=np.linspace(0,bands-1,min(12,bands),dtype=int)
  vals=[reader.read_native(r0,r1,c0,c1,int(b)).astype(np.float32,copy=False) for b in ids]
  x=np.stack(vals,axis=0)
  # Avoid np.nanpercentile over a huge 3-D tile. With 12 sampled bands,
  # median-impute invalid samples and use order statistics for a fast robust IQR proxy.
  med=np.nanmedian(x,axis=0)
  invalid=~np.isfinite(x)
  if invalid.any(): x=np.where(invalid,med[None,...],x)
  x=np.sort(x,axis=0)
  q1=x[max(0,len(ids)//4-1)]
  q3=x[min(len(ids)-1,(3*len(ids))//4)]
  spread=q3-q1
  med=np.nan_to_num(med); spread=np.nan_to_num(spread)
  out_h,out_w=base.shape[:2]
  if med.shape != (out_h,out_w):
   med=cv2.resize(med,(out_w,out_h),interpolation=cv2.INTER_AREA); spread=cv2.resize(spread,(out_w,out_h),interpolation=cv2.INTER_AREA)
  return np.stack([med,spread],axis=-1)

 def _tile_native_window(self,reader,parent_window,target,oi,oi1,oj,oj1):
  """Map local physical tile coordinates into absolute native coordinates.

  ``oi:oi1, oj:oj1`` are local coordinates within *parent_window*. The previous
  implementation compared those local coordinates directly with absolute ``r0/c0``
  offsets, which could create reversed/empty IIRS windows near an offset AOI boundary.
  """
  raw=[float(x) for x in parent_window] if parent_window is not None else None
  if raw is not None and (raw[1] <= raw[0] or raw[3] <= raw[2]):
   H,W=reader.spatial_shape; return (0,0,0,0)
  r0,r1,c0,c1=self._sanitize_window(reader,parent_window); native=float(reader.spec.gsd_m or target)
  scale=native/float(target)
  if r1<=r0 or c1<=c0 or oi1<=oi or oj1<=oj:
   return (r0,r0,c0,c0)
  lr0=max(0,int(np.floor(oi/scale))-1); lr1=min(r1-r0,int(np.ceil(oi1/scale))+1)
  lc0=max(0,int(np.floor(oj/scale))-1); lc1=min(c1-c0,int(np.ceil(oj1/scale))+1)
  if lr1<=lr0 or lc1<=lc0:
   return (r0,r0,c0,c0)
  return (r0+lr0,r0+lr1,c0+lc0,c0+lc1)

 def _auto_window(self,spec,aoi,polygon=None):
  # Pair-specific geographic intersection is supplied by register().
  gp=(spec.metadata or {}).get('geometry_csv')
  if gp and Path(gp).exists():
   try:
    gm=GeometryMapper(gp); w=gm.pixel_window_for_polygon(polygon) if polygon else gm.pixel_window_for_bbox(aoi)
    if w: return w, {'source':'geometry_csv_direct_or_affine','fit_rms_coordinate_units':gm.rms,'aoi_latlon':aoi}
   except Exception as e: return None, {'source':'geometry_csv_failed','error':str(e)}
  return None, {'source':'full_scene','aoi_latlon':aoi}

 def _tile_match(self,rr,sr,plan,rw,sw,ref_spec,src_spec):
  """Match corresponding physical tiles and re-estimate one global transform from all tile correspondences."""
  import cv2
  r0,r1,c0,c1=self._sanitize_window(rr,rw); s0,s1,d0,d1=self._sanitize_window(sr,sw)
  rh,rwpx,_=self._physical_shape(r1-r0,c1-c0,float(rr.spec.gsd_m or plan.target_gsd_m),plan.target_gsd_m)
  sh,swpx,_=self._physical_shape(s1-s0,d1-d0,float(sr.spec.gsd_m or plan.target_gsd_m),plan.target_gsd_m)
  H=min(rh,sh); W=min(rwpx,swpx)
  step=max(1,int(self.tile_px*(1-self.overlap))); tile=self.tile_px
  all_pr=[]; all_ps=[]; kp_r=kp_s=tent=0; tile_diags=[]
  for oi in range(0,H,step):
   oi1=min(H,oi+tile)
   for oj in range(0,W,step):
    oj1=min(W,oj+tile)
    ref=self._read_physical_tile(rr,plan.target_gsd_m,(r0,r1,c0,c1),oi,oi1,oj,oj1)
    src=self._read_physical_tile(sr,plan.target_gsd_m,(s0,s1,d0,d1),oi,oi1,oj,oj1)
    if ref.shape[0]<64 or ref.shape[1]<64 or src.shape[0]<64 or src.shape[1]<64:
     if oj1==W: break
     continue
    if ref_spec.sensor.upper()=='IIRS':
     ref=self._iirs_rep(rr,self._tile_native_window(rr,(r0,r1,c0,c1),plan.target_gsd_m,oi,oi1,oj,oj1),ref,plan.target_gsd_m)
    if src_spec.sensor.upper()=='IIRS':
     src=self._iirs_rep(sr,self._tile_native_window(sr,(s0,s1,d0,d1),plan.target_gsd_m,oi,oi1,oj,oj1),src,plan.target_gsd_m)
    res=match_representations(modality_rep(ref,ref_spec.solar_elevation_deg,ref_spec.solar_azimuth_deg),modality_rep(src,src_spec.solar_elevation_deg,src_spec.solar_azimuth_deg))
    kp_r+=res.keypoints_ref; kp_s+=res.keypoints_src; tent+=res.tentative_matches
    if res.points_ref.size and res.points_src.size and res.diagnostics.get('independent_correspondence_evidence', True):
     all_pr.append(res.points_ref+np.array([oj,oi],np.float32)); all_ps.append(res.points_src+np.array([oj,oi],np.float32))
    tile_diags.append({'id':f'{oi}:{oj}','shape':[oi1-oi,oj1-oj],'matches':res.tentative_matches,'inliers':res.inliers,'ratio':res.inlier_ratio,'coverage':res.coverage,'rmse_px':res.rmse_px})
    if oj1==W: break
   if oi1==H: break
  if not all_pr:
   from app.model import MatchResult
   return MatchResult('TILED-SIFT+RANSAC',kp_r,kp_s,tent,0,0.0,None,None,None,0.0,None,diagnostics={'status':'INSUFFICIENT_EVIDENCE','reason':'no_tile_correspondences','tiles':tile_diags,'physical_grid_shape':[H,W]})
  pr=np.vstack(all_pr).astype(np.float32); ps=np.vstack(all_ps).astype(np.float32)
  Hm,mask=cv2.findHomography(ps,pr,cv2.RANSAC,3.0,maxIters=10000,confidence=.995)
  if Hm is None:
   from app.model import MatchResult
   return MatchResult('TILED-SIFT+RANSAC',kp_r,kp_s,len(pr),0,0.0,None,None,None,0.0,None,pr,ps,{'status':'INSUFFICIENT_EVIDENCE','reason':'global_ransac_failed','tiles':tile_diags,'physical_grid_shape':[H,W]})
  m=mask.ravel().astype(bool); pred=cv2.perspectiveTransform(ps.reshape(-1,1,2),Hm).reshape(-1,2); err=np.linalg.norm(pred-pr,axis=1)[m]
  grid=np.zeros((4,4),bool); pts=pr[m]; gx=np.clip((pts[:,0]/max(W,1)*4).astype(int),0,3); gy=np.clip((pts[:,1]/max(H,1)*4).astype(int),0,3); grid[gy,gx]=True
  inl=int(m.sum()); ratio=float(inl/max(len(pr),1)); cov=float(grid.mean()); rm=float(np.sqrt(np.mean(err**2))) if inl else None
  status='VALIDATED' if inl>=12 and ratio>=0.35 and cov>=0.35 and rm is not None and rm<=2.5 else 'INSUFFICIENT_EVIDENCE'
  from app.model import MatchResult
  return MatchResult('TILED-SIFT+RANSAC',kp_r,kp_s,len(pr),inl,ratio,rm,float(np.median(err)) if inl else None,float(np.percentile(err,95)) if inl else None,cov,Hm,pr,ps,{'status':status,'grid_coverage':cov,'tiles':tile_diags,'physical_grid_shape':[H,W]})

 def _intersection_bbox(self,fp_a,fp_b):
  def bounds(fp):
   if not isinstance(fp,dict) or not fp: return None
   lats=[v for k,v in fp.items() if k.endswith('_latitude') and v is not None]
   lons=[v for k,v in fp.items() if k.endswith('_longitude') and v is not None]
   if len(lats)<2 or len(lons)<2: return None
   return min(lats),min(lons),max(lats),max(lons)
  a=bounds(fp_a); b=bounds(fp_b)
  if not a or not b: return None
  lat0=max(a[0],b[0]); lon0=max(a[1],b[1]); lat1=min(a[2],b[2]); lon1=min(a[3],b[3])
  if lat1<=lat0 or lon1<=lon0: return None
  return (lat0,lon0,lat1,lon1)

 def _geometry_intersection_bbox(self,ref_spec,src_spec):
  rg=(ref_spec.metadata or {}).get('geometry_csv'); sg=(src_spec.metadata or {}).get('geometry_csv')
  if not (rg and sg and Path(rg).exists() and Path(sg).exists()): return None, None
  try:
   r=GeometryMapper(rg); s=GeometryMapper(sg)
   if not (r.ok and s.ok): return None, {'status':'GEOMETRY_UNAVAILABLE','reference_error':getattr(r,'error',None),'source_error':getattr(s,'error',None)}
   poly=r.intersection_polygon(s)
   if not poly: return None, {'status':'NO_GEOMETRY_INTERSECTION'}
   xs=[p[0] for p in poly]; ys=[p[1] for p in poly]; aoi=(min(ys),min(xs),max(ys),max(xs))
   return aoi, {'status':'TRUE_SWATH_INTERSECTION','reference_geometry':str(r.csv_path),'source_geometry':str(s.csv_path),'reference_geometry_rms':r.rms,'source_geometry_rms':s.rms,'reference_footprint_method':r.footprint_method,'source_footprint_method':s.footprint_method,'intersection_vertices':len(poly),'intersection_polygon':poly}
  except Exception as e:
   return None, {'status':'GEOMETRY_INTERSECTION_FAILED','error':str(e)}

 def _geo_tile_match(self,rr,sr,plan,ref_spec,src_spec,polygon):
  """Register two sensors after true geographic warping onto the same metric grid.

  This is the key cross-modal correction: a common GSD alone is insufficient because
  each CH-2 sensor has a different curved Scan/Pixel-to-ground mapping. Both images are
  first sampled onto the same lunar geographic grid, then matched.
  """
  rg=(ref_spec.metadata or {}).get('geometry_csv'); sg=(src_spec.metadata or {}).get('geometry_csv')
  if not (rg and sg and Path(rg).exists() and Path(sg).exists() and polygon): return None
  rmap=GeometryMapper(rg); smap=GeometryMapper(sg)
  if not (rmap.ok and smap.ok): return None
  grid=GeoGrid(polygon,plan.target_gsd_m,max_pixels=12_000_000)
  step=max(1,int(self.tile_px*(1-self.overlap))); all_pr=[]; all_ps=[]; tent=kp_r=kp_s=0; tiles=[]
  for oi in range(0,grid.height,step):
   oi1=min(grid.height,oi+self.tile_px)
   for oj in range(0,grid.width,step):
    oj1=min(grid.width,oj+self.tile_px)
    mask=grid.polygon_mask_tile(oi,oi1,oj,oj1)
    if int(mask.sum())<64*64:
     if oj1==grid.width: break
     continue
    if ref_spec.sensor.upper()=='IIRS': ref=warp_iirs_rep_to_grid(rr,rmap,grid,oi,oi1,oj,oj1)
    else: ref=warp_reader_to_grid(rr,rmap,grid,oi,oi1,oj,oj1,0)
    if src_spec.sensor.upper()=='IIRS': src=warp_iirs_rep_to_grid(sr,smap,grid,oi,oi1,oj,oj1)
    else: src=warp_reader_to_grid(sr,smap,grid,oi,oi1,oj,oj1,0)
    if ref is None or src is None: continue
    ref=np.asarray(ref,np.float32); src=np.asarray(src,np.float32); ref[~mask]=0; src[~mask]=0
    if min(ref.shape[:2])<64 or min(src.shape[:2])<64: continue
    res=match_representations(modality_rep(ref,ref_spec.solar_elevation_deg,ref_spec.solar_azimuth_deg),modality_rep(src,src_spec.solar_elevation_deg,src_spec.solar_azimuth_deg))
    kp_r+=res.keypoints_ref; kp_s+=res.keypoints_src; tent+=res.tentative_matches
    if res.points_ref.size and res.points_src.size and res.diagnostics.get('independent_correspondence_evidence', True):
     all_pr.append(res.points_ref+np.array([oj,oi],np.float32)); all_ps.append(res.points_src+np.array([oj,oi],np.float32))
    tiles.append({'id':f'{oi}:{oj}','shape':[oi1-oi,oj1-oj],'matches':res.tentative_matches,'inliers':res.inliers,'ratio':res.inlier_ratio,'coverage':res.coverage,'rmse_px':res.rmse_px,'matcher_path':res.diagnostics.get('matcher_path')})
    if oj1==grid.width: break
   if oi1==grid.height: break
  if not all_pr:
   from app.model import MatchResult
   return MatchResult('GEO-WARP-MULTIMODAL',kp_r,kp_s,tent,0,0.0,None,None,None,0.0,None,diagnostics={'status':'INSUFFICIENT_EVIDENCE','reason':'no_geo_tile_correspondences','tiles':tiles,'physical_grid_shape':[grid.height,grid.width],'geographic_warp':True,'target_gsd_m':grid.target_gsd})
  pr=np.vstack(all_pr).astype(np.float32); ps=np.vstack(all_ps).astype(np.float32)
  from app.core.matcher import _result_from_points
  res=_result_from_points(pr,ps,kp_r,kp_s,'GEO-WARP-MULTIMODAL+RANSAC')
  res.diagnostics.update({'geographic_warp':True,'target_gsd_m':grid.target_gsd,'physical_grid_shape':[grid.height,grid.width],'tiles':tiles})
  return res

 def register(self,ref_spec,src_spec,name='pair'):
  t=time.time(); rr=SceneReader(ref_spec); sr=SceneReader(src_spec); levels=[]
  aoi,gd=self._geometry_intersection_bbox(ref_spec,src_spec)
  intersection_polygon=(gd or {}).get('intersection_polygon') if isinstance(gd,dict) else None
  if aoi is None:
   aoi=self._intersection_bbox(ref_spec.footprint,src_spec.footprint)
   gd=gd or {'status':'XML_FOOTPRINT_INTERSECTION'}
  if aoi is None:
   # Generic formats may legitimately lack footprint metadata; keep full-scene behavior
   # for such non-mission inputs, while the CH-2 PDS4 adapters provide footprints and
   # therefore take the pair-specific geographic intersection path.
   rw,rd0=None,{'source':'full_scene_no_pair_footprint'}; sw,sd0=None,{'source':'full_scene_no_pair_footprint'}
  else:
   rw,rd0=self._auto_window(ref_spec,aoi,intersection_polygon); sw,sd0=self._auto_window(src_spec,aoi,intersection_polygon)
  for plan in plan_common_gsd(ref_spec.gsd_m,src_spec.gsd_m,levels=self.levels):
   res=self._geo_tile_match(rr,sr,plan,ref_spec,src_spec,intersection_polygon) if intersection_polygon else None
   if res is None:
    res=self._tile_match(rr,sr,plan,rw,sw,ref_spec,src_spec)
   res.diagnostics.update({'target_gsd_m':plan.target_gsd_m,'actual_ref_gsd_m':float(plan.target_gsd_m),'actual_src_gsd_m':float(plan.target_gsd_m),'rmse_m':(res.rmse_px*float(plan.target_gsd_m) if res.rmse_px is not None else None),'physical_scale_error_fraction_ref':0.0,'physical_scale_error_fraction_src':0.0})
   levels.append(res)
   if res.diagnostics.get('status')=='VALIDATED': break
  best=max(levels,key=lambda x:(x.inlier_ratio,x.inliers,x.coverage))
  cascade=[dict(x.diagnostics) for x in levels]
  best.diagnostics.update({'experiment':name,'elapsed_s':time.time()-t,'pair_aoi_latlon':aoi,'pair_aoi_method':gd,'scale_cascade':cascade,'physical_gsd_invariant':True,'auto_aoi_reference':rd0,'auto_aoi_source':sd0,'status':gate(best)['status'],'gate_reasons':gate(best)['reasons'],'note':'Physical GSD is preserved during matching. Computational tiling changes memory footprint only; no post-resize stride is used to disguise a coarser effective GSD.'})
  return best

 def save(self,result,path):
  path=Path(path); path.parent.mkdir(parents=True,exist_ok=True); d={k:v for k,v in result.__dict__.items() if k not in ('homography','points_ref','points_src')}; d['homography']=result.homography.tolist() if result.homography is not None else None; path.write_text(json.dumps(d,indent=2,default=str))
