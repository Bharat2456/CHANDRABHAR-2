import cv2,numpy as np
from app.model import MatchResult

def _single(rep):
 if rep.ndim==3:
  chans=[]
  for i in range(rep.shape[2]):
   x=rep[...,i].astype(np.float32)
   lo,hi=np.nanpercentile(x[np.isfinite(x)],[2,98]) if np.isfinite(x).any() else (0,1)
   x=np.clip((x-lo)/max(float(hi-lo),1e-6),0,1).astype(np.float32)
   gx=cv2.Sobel(x,cv2.CV_32F,1,0,ksize=3); gy=cv2.Sobel(x,cv2.CV_32F,0,1,ksize=3)
   chans.append(cv2.magnitude(gx,gy))
  # Average modality-normalized structural evidence; avoids letting one IIRS band-statistic dominate.
  return np.mean(chans,axis=0).astype(np.float32)
 return rep.astype(np.float32)

def _norm8(x):
 x=np.asarray(x,np.float32); finite=np.isfinite(x)
 if not finite.any(): return np.zeros(x.shape,np.uint8)
 lo,hi=np.nanpercentile(x[finite],[2,98]); y=np.clip((x-lo)/max(float(hi-lo),1e-6),0,1); return np.uint8(y*255)

def _grid_coverage(points,h,w):
 if len(points)==0:return 0.0
 grid=np.zeros((4,4),bool); p=np.asarray(points); gx=np.clip((p[:,0]/max(w,1)*4).astype(int),0,3); gy=np.clip((p[:,1]/max(h,1)*4).astype(int),0,3); grid[gy,gx]=True; return float(grid.mean())

def _result_from_points(pr,ps,kr=0,ks=0,method='MULTIMODAL'):
 pr=np.asarray(pr,np.float32); ps=np.asarray(ps,np.float32)
 if len(pr)<3:return MatchResult(method,kr,ks,len(pr),0,0.0,None,None,None,0.0,None,pr,ps,{'status':'INSUFFICIENT_EVIDENCE','reason':'too_few_correspondences'})
 H,mask=cv2.findHomography(ps,pr,cv2.RANSAC,3.0,maxIters=10000,confidence=.995)
 if H is None:return MatchResult(method,kr,ks,len(pr),0,0.0,None,None,None,0.0,None,pr,ps,{'status':'INSUFFICIENT_EVIDENCE','reason':'ransac_failed'})
 m=mask.ravel().astype(bool); pred=cv2.perspectiveTransform(ps.reshape(-1,1,2),H).reshape(-1,2); err=np.linalg.norm(pred-pr,axis=1)[m]
 h=int(max(pr[:,1].max(),1)+1); w=int(max(pr[:,0].max(),1)+1); inl=int(m.sum()); ratio=inl/max(len(pr),1); cov=_grid_coverage(pr[m],h,w); rm=float(np.sqrt(np.mean(err**2))) if inl else None
 status='VALIDATED' if inl>=12 and ratio>=0.35 and cov>=0.35 and rm is not None and rm<=2.5 else 'INSUFFICIENT_EVIDENCE'
 return MatchResult(method,kr,ks,len(pr),inl,ratio,rm,float(np.median(err)) if inl else None,float(np.percentile(err,95)) if inl else None,cov,H,pr,ps,{'status':status,'grid_coverage':cov})

def _subpixel_refine(img, points):
 # Local image evidence only: refine observed feature locations, never generate
 # new correspondences. This is intentionally conservative and can be audited.
 if points is None or len(points) == 0: return points, 0
 pts=np.asarray(points,np.float32).reshape(-1,1,2).copy()
 h,w=img.shape[:2]
 keep=(pts[:,0,0]>=3)&(pts[:,0,0]<w-3)&(pts[:,0,1]>=3)&(pts[:,0,1]<h-3)
 before=pts.copy()
 try:
  cv2.cornerSubPix(img.astype(np.float32),pts,(3,3),(-1,-1),(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,20,0.01))
 except Exception:
  return points,0
 pts[~keep]=before[~keep]
 delta=np.linalg.norm((pts-before).reshape(-1,2),axis=1)
 changed=int(np.count_nonzero((delta>1e-4)&keep))
 return pts.reshape(-1,2),changed

def _sift(ref,src,ratio=0.82):
 r8=_norm8(_single(ref)); s8=_norm8(_single(src))
 sift=cv2.SIFT_create(nfeatures=4000,contrastThreshold=0.008,edgeThreshold=12,sigma=1.2)
 kr,dr=sift.detectAndCompute(r8,None); ks,ds=sift.detectAndCompute(s8,None)
 if dr is None or ds is None:return None,len(kr),len(ks),0,0
 knn=cv2.BFMatcher(cv2.NORM_L2).knnMatch(dr,ds,k=2); good=[m for m,n in knn if m.distance < ratio*n.distance]
 if len(good)<6:return None,len(kr),len(ks),len(good),0
 pr=np.float32([kr[m.queryIdx].pt for m in good]); ps=np.float32([ks[m.trainIdx].pt for m in good])
 pr,nr=_subpixel_refine(r8,pr); ps,ns=_subpixel_refine(s8,ps)
 return (pr,ps),len(kr),len(ks),len(good),int(nr+ns)

def _phase_translation(ref,src):
 r=_norm8(_single(ref)).astype(np.float32)/255.; s=_norm8(_single(src)).astype(np.float32)/255.
 h=min(r.shape[0],s.shape[0]); w=min(r.shape[1],s.shape[1]); r=r[:h,:w]; s=s[:h,:w]
 if min(h,w)<32:return None
 r=cv2.GaussianBlur(r,(0,0),1.0); s=cv2.GaussianBlur(s,(0,0),1.0)
 r=r-r.mean(); s=s-s.mean();
 try: shift,response=cv2.phaseCorrelate(r,s)
 except Exception:return None
 if not np.isfinite(response) or response<0.12:return None
 dx,dy=shift; yy,xx=np.mgrid[16:h-16:32j,16:w-16:32j]
 pr=np.column_stack((xx.ravel(),yy.ravel())).astype(np.float32); ps=pr+np.array([dx,dy],np.float32)
 keep=(ps[:,0]>=0)&(ps[:,0]<w)&(ps[:,1]>=0)&(ps[:,1]<h)
 return pr[keep],ps[keep],float(response),[float(dx),float(dy)]

def _ecc_affine(ref,src):
 r=_norm8(_single(ref)).astype(np.float32)/255.; s=_norm8(_single(src)).astype(np.float32)/255.
 h=min(r.shape[0],s.shape[0]); w=min(r.shape[1],s.shape[1]);
 if min(h,w)<64:return None
 r=r[:h,:w]; s=s[:h,:w]
 r=cv2.GaussianBlur(r,(0,0),1.0); s=cv2.GaussianBlur(s,(0,0),1.0)
 # Dense ECC points are model-generated, not independent feature matches.
 # Require real image texture and a strong ECC correlation before exposing
 # the transform as supporting evidence. It is never sufficient by itself
 # for the final VALIDATED gate.
 if float(np.std(r))<0.02 or float(np.std(s))<0.02:return None
 warp=np.eye(2,3,dtype=np.float32)
 try:
  corr,warp=cv2.findTransformECC(r,s,warp,cv2.MOTION_AFFINE,(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,100,1e-5),None,1)
 except Exception:return None
 if not np.isfinite(corr) or float(corr)<0.70:return None
 yy,xx=np.mgrid[16:h-16:24j,16:w-16:24j]; pr=np.column_stack((xx.ravel(),yy.ravel())).astype(np.float32)
 ps=(pr @ warp[:,:2].T + warp[:,2]).astype(np.float32); keep=(ps[:,0]>=0)&(ps[:,0]<w)&(ps[:,1]>=0)&(ps[:,1]<h)
 return pr[keep],ps[keep],float(corr)

def match_representations(ref_rep,src_rep,ratio=0.78):
 a=_sift(ref_rep,src_rep,ratio)
 if a is not None and a[0] is not None:
  pts,kr,ks,good,subpix=a; res=_result_from_points(pts[0],pts[1],kr,ks,'SIFT+SUBPIXEL+RANSAC'); res.diagnostics.update({'matcher_path':'sift','subpixel_refined_count':int(subpix),'independent_correspondence_evidence':True}); return res
 if a is not None: _,kr,ks,good,subpix=a
 else: kr=ks=good=subpix=0
 ph=_phase_translation(ref_rep,src_rep)
 if ph is not None:
  pr,ps,response,shift=ph; res=_result_from_points(pr,ps,kr,ks,'PHASE+RANSAC'); res.diagnostics.update({'matcher_path':'phase_correlation','phase_response':response,'translation_px':shift,'dense_model_generated':True,'independent_correspondence_evidence':False}); res.diagnostics['status']='INSUFFICIENT_EVIDENCE'; res.diagnostics['reason']='dense_phase_model_generated_correspondences_not_independent'; return res
 ec=_ecc_affine(ref_rep,src_rep)
 if ec is not None:
  pr,ps,score=ec; res=_result_from_points(pr,ps,kr,ks,'ECC-AFFINE+RANSAC'); res.diagnostics.update({'matcher_path':'ecc_affine','ecc_correlation':score,'dense_model_generated':True}); res.diagnostics['status']='INSUFFICIENT_EVIDENCE'; res.diagnostics['reason']='dense_ecc_model_generated_correspondences_not_independent'; return res
 return MatchResult('MULTIMODAL-CASCADE',kr,ks,good,0,0.0,None,None,None,0.0,None,diagnostics={'status':'INSUFFICIENT_EVIDENCE','reason':'no_descriptors_or_direct_registration','matcher_path':'none'})
