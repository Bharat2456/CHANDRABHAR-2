"""Measures how the installed OpenCV resamples with cv2.remap(INTER_LINEAR) versus an exact float64 bilinear reference.
Output is JSON; run it under each OpenCV version to compare (see docs/WEB_PARITY_ANALYSIS.md).
Usage: python tools/opencv_resampling_analysis.py"""
import json,numpy as np,cv2
rng=np.random.default_rng(3); H,W=200,240
# smooth-ish content so a sub-pixel shift is measurable, plus the random-noise case used before
yy0,xx0=np.mgrid[0:H,0:W]
cases={'noise_f32':(rng.random((H,W))*250).astype(np.float32),'smooth_f32':(120+60*np.sin(xx0/11.0)+50*np.cos(yy0/7.0)).astype(np.float32)}
yy,xx=np.mgrid[0:150,0:170].astype(np.float32)
qx=(xx*1.2+3.37+0.3*np.sin(yy/9)).astype(np.float32); qy=(yy*1.1-2.21+0.2*np.cos(xx/7)).astype(np.float32)
def bil(src,qx,qy):
    x0=np.floor(qx).astype(int); y0=np.floor(qy).astype(int); fx=(qx-x0).astype(np.float64); fy=(qy-y0).astype(np.float64)
    g=lambda y,x: src[y,x].astype(np.float64)
    return g(y0,x0)*(1-fx)*(1-fy)+g(y0,x0+1)*fx*(1-fy)+g(y0+1,x0)*(1-fx)*fy+g(y0+1,x0+1)*fx*fy
inner=(qx>2)&(qx<W-3)&(qy>2)&(qy<H-3)
res={'cv2':cv2.__version__}
for k,src in cases.items():
    ref=bil(src,qx,qy); r=cv2.remap(src,qx,qy,cv2.INTER_LINEAR).astype(np.float64)
    e=(r-ref)[inner]; res[k]={'max_abs_err_vs_exact':round(float(np.abs(e).max()),5),'rms_err':round(float(np.sqrt((e**2).mean())),5)}
    # estimate an apparent coordinate offset: best (dx,dy) such that exact bilinear at (qx+dx,qy+dy) matches cv2 output
    best=min(((float(np.sqrt(((bil(src,np.clip(qx+dx,0,W-2),np.clip(qy+dy,0,H-2))-r)[inner]**2).mean())),dx,dy) for dx in np.arange(-0.6,0.61,0.1) for dy in np.arange(-0.6,0.61,0.1)))
    res[k]['best_apparent_offset(dx,dy)']=[round(best[1],2),round(best[2],2)]; res[k]['rms_at_best']=round(best[0],5)
print(json.dumps(res))
