from __future__ import annotations
import numpy as np
import cv2
from pathlib import Path
from app.geo.mapper import GeometryMapper, _HAS_SCIPY

LUNAR_RADIUS_M = 1737400.0

class GeoGrid:
    def __init__(self, polygon_lonlat, target_gsd_m, max_pixels=12_000_000):
        self.polygon=np.asarray(polygon_lonlat,dtype=np.float64)
        self.target_gsd=float(target_gsd_m)
        lat0=float(np.mean(self.polygon[:,1])); lon0=float(np.mean(self.polygon[:,0]))
        self.lat0=lat0; self.lon0=lon0
        c=np.cos(np.deg2rad(lat0))
        self.xy=np.column_stack(((self.polygon[:,0]-lon0)*np.pi/180*LUNAR_RADIUS_M*c,(self.polygon[:,1]-lat0)*np.pi/180*LUNAR_RADIUS_M))
        self.x0=float(self.xy[:,0].min()); self.y0=float(self.xy[:,1].min())
        self.x1=float(self.xy[:,0].max()); self.y1=float(self.xy[:,1].max())
        self.width=max(2,int(np.ceil((self.x1-self.x0)/self.target_gsd))+1)
        self.height=max(2,int(np.ceil((self.y1-self.y0)/self.target_gsd))+1)
        if self.width*self.height>max_pixels:
            scale=np.sqrt((self.width*self.height)/max_pixels)
            self.target_gsd*=float(scale)
            self.width=max(2,int(np.ceil((self.x1-self.x0)/self.target_gsd))+1)
            self.height=max(2,int(np.ceil((self.y1-self.y0)/self.target_gsd))+1)
    def lonlat_tile(self,r0,r1,c0,c1):
        xs=self.x0+(np.arange(c0,c1,dtype=np.float64)+0.5)*self.target_gsd
        ys=self.y0+(np.arange(r0,r1,dtype=np.float64)+0.5)*self.target_gsd
        X,Y=np.meshgrid(xs,ys)
        lon=self.lon0+X/(LUNAR_RADIUS_M*np.cos(np.deg2rad(self.lat0)))*180/np.pi
        lat=self.lat0+Y/LUNAR_RADIUS_M*180/np.pi
        return lon,lat
    def polygon_mask_tile(self,r0,r1,c0,c1):
        pts=np.round(np.column_stack(((self.polygon[:,0]-self.lon0)*np.pi/180*LUNAR_RADIUS_M*np.cos(np.deg2rad(self.lat0))-self.x0,
                                      (self.polygon[:,1]-self.lat0)*np.pi/180*LUNAR_RADIUS_M-self.y0))/self.target_gsd).astype(np.int32)
        pts[:,0]=np.clip(pts[:,0],-1000000,self.width+1000000); pts[:,1]=np.clip(pts[:,1],-1000000,self.height+1000000)
        mask=np.zeros((r1-r0,c1-c0),np.uint8)
        pts[:,1]-=r0; pts[:,0]-=c0
        cv2.fillPoly(mask,[pts],1)
        return mask.astype(bool)

def _bounded_remap(src_img, mx, my, max_dim=32760):
    """OpenCV-safe remap for native source windows larger than SHRT_MAX.

    The output tile is recursively partitioned until every source patch passed
    to cv2.remap is below OpenCV's 16-bit dimension limit.
    """
    mx=np.asarray(mx,np.float32); my=np.asarray(my,np.float32)
    oh,ow=mx.shape
    out=np.zeros((oh,ow),np.float32)
    def rec(r0,r1,c0,c1):
        sx=mx[r0:r1,c0:c1]; sy=my[r0:r1,c0:c1]
        good=np.isfinite(sx)&np.isfinite(sy)
        if not good.any(): return
        y0=int(np.floor(np.nanmin(sy[good])))-2; y1=int(np.ceil(np.nanmax(sy[good])))+3
        x0=int(np.floor(np.nanmin(sx[good])))-2; x1=int(np.ceil(np.nanmax(sx[good])))+3
        y0=max(0,y0); x0=max(0,x0); y1=min(src_img.shape[0],y1); x1=min(src_img.shape[1],x1)
        if y1<=y0 or x1<=x0: return
        if (y1-y0)<max_dim and (x1-x0)<max_dim:
            qx=(sx-x0).copy(); qy=(sy-y0).copy(); qx[~good]=0; qy[~good]=0
            patch=cv2.remap(src_img[y0:y1,x0:x1],qx,qy,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT)
            patch[~good]=0; out[r0:r1,c0:c1]=patch; return
        if (r1-r0)>= (c1-c0) and r1-r0>1:
            mid=r0+(r1-r0)//2; rec(r0,mid,c0,c1); rec(mid,r1,c0,c1)
        elif c1-c0>1:
            mid=c0+(c1-c0)//2; rec(r0,r1,c0,mid); rec(r0,r1,mid,c1)
    rec(0,oh,0,ow)
    return out

def warp_reader_to_grid(reader, mapper:GeometryMapper, grid:GeoGrid, r0,r1,c0,c1, band=0):
    lon,lat=grid.lonlat_tile(r0,r1,c0,c1)
    scan,pix=mapper.native_grid_from_lonlat(lon,lat,bbox=(float(lat.min()),float(lon.min()),float(lat.max()),float(lon.max())))
    if scan is None: return None
    finite=np.isfinite(scan)&np.isfinite(pix)
    if not finite.any(): return np.zeros((r1-r0,c1-c0),np.float32)
    s0=int(max(0,np.floor(np.nanmin(scan[finite]))-2)); s1=int(min(reader.spatial_shape[0],np.ceil(np.nanmax(scan[finite]))+3))
    p0=int(max(0,np.floor(np.nanmin(pix[finite]))-2)); p1=int(min(reader.spatial_shape[1],np.ceil(np.nanmax(pix[finite]))+3))
    if s1<=s0 or p1<=p0: return np.zeros((r1-r0,c1-c0),np.float32)
    src=reader.read_native(s0,s1,p0,p1,band).astype(np.float32,copy=False)
    mapx=(pix-p0).astype(np.float32); mapy=(scan-s0).astype(np.float32)
    mapx[~finite]=0; mapy[~finite]=0
    out=_bounded_remap(src,mapx,mapy)
    out[~finite]=0
    return out

def warp_iirs_rep_to_grid(reader, mapper, grid, r0,r1,c0,c1, bands=24):
    ids=np.linspace(0,reader.spec.array.shape[0]-1,min(bands,reader.spec.array.shape[0]),dtype=int)
    vals=[]
    for b in ids:
        v=warp_reader_to_grid(reader,mapper,grid,r0,r1,c0,c1,int(b))
        if v is None: return None
        vals.append(v)
    x=np.stack(vals,axis=0).astype(np.float32)
    finite=np.isfinite(x); med=np.nanmedian(np.where(finite,x,np.nan),axis=0)
    invalid=~np.isfinite(x); x=np.where(invalid,med[None,...],x)
    x=np.sort(x,axis=0)
    q1=x[max(0,len(ids)//4-1)]; q3=x[min(len(ids)-1,(3*len(ids))//4)]
    spread=q3-q1
    # Spectral-shape energy: robust measure of local band-to-band change.
    raw=np.diff(x,axis=0)
    slope=np.sqrt(np.mean(raw*raw,axis=0))
    med=np.nan_to_num(med); spread=np.nan_to_num(spread); slope=np.nan_to_num(slope)
    return np.stack([med,spread,slope],axis=-1)
