from __future__ import annotations
from pathlib import Path
import csv
import numpy as np

try:
    from scipy.interpolate import LinearNDInterpolator
    _HAS_SCIPY = True
except Exception:
    LinearNDInterpolator = None
    _HAS_SCIPY = False

try:
    from shapely.geometry import Polygon, Point
    from shapely.ops import unary_union
    _HAS_SHAPELY = True
except Exception:
    Polygon = Point = None
    _HAS_SHAPELY = False


def _norm(s):
    return ''.join(ch for ch in str(s).strip().lower() if ch.isalnum())


def _convex_hull(points):
    pts=sorted(set((float(x),float(y)) for x,y in points))
    if len(pts)<=1: return pts
    def cross(o,a,b): return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    lo=[]
    for p in pts:
        while len(lo)>=2 and cross(lo[-2],lo[-1],p)<=0: lo.pop()
        lo.append(p)
    hi=[]
    for p in reversed(pts):
        while len(hi)>=2 and cross(hi[-2],hi[-1],p)<=0: hi.pop()
        hi.append(p)
    return lo[:-1]+hi[:-1]


def _grid_boundary(arr):
    """Trace the perimeter of the sampled Scan x Pixel geometry grid."""
    # arr columns: scan, pixel, lat, lon
    if len(arr) < 4:
        return []
    by_scan = {}
    by_pixel = {}
    for scan, pix, lat, lon in arr:
        by_scan.setdefault(float(scan), []).append((float(pix), float(lon), float(lat)))
        by_pixel.setdefault(float(pix), []).append((float(scan), float(lon), float(lat)))
    scans = sorted(by_scan); pixels = sorted(by_pixel)
    if len(scans) < 2 or len(pixels) < 2:
        return []
    def edge_for_scan(scan, reverse=False):
        row = sorted(by_scan[scan], key=lambda x:x[0])
        pts=[(x[1],x[2]) for x in row]
        return list(reversed(pts)) if reverse else pts
    def edge_for_pixel(pix, reverse=False):
        col = sorted(by_pixel[pix], key=lambda x:x[0])
        pts=[(x[1],x[2]) for x in col]
        return list(reversed(pts)) if reverse else pts
    top = edge_for_scan(scans[0], False)
    right = edge_for_pixel(pixels[-1], False)[1:]
    bottom = edge_for_scan(scans[-1], True)[1:]
    left = edge_for_pixel(pixels[0], True)[1:]
    ring = top + right + bottom + left
    if ring and ring[0] != ring[-1]: ring.append(ring[0])
    return ring


class GeometryMapper:
    """Read ISRO CH-2 GRD geometry samples and map Scan/Pixel <-> lon/lat.

    For native ISRO GRD files, the sampled Scan x Pixel grid is used to trace
    the actual swath perimeter. Shapely is preferred for non-convex polygon
    intersection; a point-in-footprint fallback remains available.
    """
    def __init__(self,csv_path,max_samples=200000):
        self.csv_path=Path(csv_path); self.max_samples=int(max_samples)
        self.ok=False; self.columns=[]; self.samples=np.empty((0,4),float); self.rms=None
        self._fit()

    def _fit(self):
        with self.csv_path.open('r',errors='ignore',newline='') as f:
            rd=csv.DictReader(f)
            raw=[c for c in (rd.fieldnames or []) if c is not None]
            self.columns=[_norm(c) for c in raw]
            idx={_norm(c):c for c in raw}
            def pick(*names):
                for n in names:
                    if _norm(n) in idx: return idx[_norm(n)]
                return None
            lc=pick('Scan','Line','Row'); sc=pick('Pixel','Sample','Column','Col')
            lat=pick('Latitude','Lat'); lon=pick('Longitude','Lon')
            if not (lc and sc and lat and lon):
                self.error=f'Unsupported geometry columns: {raw}'; return
            rows=[]
            for row in rd:
                try: rows.append((float(row[lc]),float(row[sc]),float(row[lat]),float(row[lon])))
                except Exception: continue
            if not rows:
                self.error='No numeric geometry rows'; return
            arr=np.asarray(rows,float)
            if len(arr)>self.max_samples:
                idxs=np.linspace(0,len(arr)-1,self.max_samples,dtype=int); arr=arr[idxs]
            self.samples=arr
            self.scan_col,self.pixel_col,self.lat_col,self.lon_col=lc,sc,lat,lon
            self.scan_min=float(arr[:,0].min()); self.scan_max=float(arr[:,0].max())
            self.pixel_min=float(arr[:,1].min()); self.pixel_max=float(arr[:,1].max())
            self.lat_min=float(arr[:,2].min()); self.lat_max=float(arr[:,2].max())
            self.lon_min=float(arr[:,3].min()); self.lon_max=float(arr[:,3].max())
            self.hull=_convex_hull(list(zip(arr[:,3],arr[:,2])))
            self.boundary=_grid_boundary(arr)
            self.footprint_method='sampled_swath_perimeter' if len(self.boundary)>=4 else 'convex_hull_fallback'
            self._poly = None
            if _HAS_SHAPELY and len(self.boundary)>=4:
                try:
                    p=Polygon(self.boundary)
                    if not p.is_valid: p=p.buffer(0)
                    if not p.is_empty: self._poly=p
                except Exception: self._poly=None
            A=np.c_[arr[:,0],arr[:,1],np.ones(len(arr))]
            self.coef_lat=np.linalg.lstsq(A,arr[:,2],rcond=None)[0]
            self.coef_lon=np.linalg.lstsq(A,arr[:,3],rcond=None)[0]
            pred=A@np.c_[self.coef_lat,self.coef_lon]
            self.rms=float(np.sqrt(np.mean((pred-arr[:,2:4])**2)))
            self.ok=True; self.error=None

    @property
    def footprint_bbox(self):
        return (self.lat_min,self.lon_min,self.lat_max,self.lon_max) if self.ok else None

    def footprint_hull(self): return list(self.hull) if self.ok else []
    def footprint_polygon(self): return list(self.boundary) if self.ok and len(self.boundary)>=4 else self.footprint_hull()

    def intersection_polygon(self,other):
        if not self.ok or not other.ok: return []
        if _HAS_SHAPELY and self._poly is not None and other._poly is not None:
            try:
                inter=self._poly.intersection(other._poly)
                if inter.is_empty: return []
                if inter.geom_type=='Polygon': return [(float(x),float(y)) for x,y in inter.exterior.coords]
                if inter.geom_type=='MultiPolygon':
                    p=max(inter.geoms,key=lambda g:g.area)
                    return [(float(x),float(y)) for x,y in p.exterior.coords]
            except Exception:
                pass
        # Fallback: retain only sampled points lying in the other footprint.
        if other._poly is not None:
            pts=[(float(x),float(y)) for _,_,y,x in self.samples if other._poly.covers(Point(float(x),float(y)))]
            if len(pts)>=3: return _convex_hull(pts)
        return self._convex_intersection(other)

    def _convex_intersection(self,other):
        def inside(p,a,b): return (b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0]) >= -1e-12
        def clip(subject,clip_poly):
            out=list(subject)
            for i,a in enumerate(clip_poly):
                b=clip_poly[(i+1)%len(clip_poly)]; inp=out; out=[]
                if not inp: break
                s=inp[-1]
                for e in inp:
                    se=inside(s,a,b); ee=inside(e,a,b)
                    if ee != se:
                        dx=e[0]-s[0]; dy=e[1]-s[1]; ex=b[0]-a[0]; ey=b[1]-a[1]
                        den=dx*ey-dy*ex
                        if abs(den)>1e-15:
                            t=((a[0]-s[0])*ey-(a[1]-s[1])*ex)/den; out.append((s[0]+t*dx,s[1]+t*dy))
                    if ee: out.append(e)
                    s=e
            return out
        return clip(self.hull,other.hull)


    def inverse_interpolators(self, bbox=None, max_points=9000):
        """Build local geographic(lon,lat)->(scan,pixel) interpolators.

        CH-2 GRD samples are a regular Scan x Pixel sampling of a curved swath.
        A global affine inverse is not valid for strongly curved polar TMC-2 geometry,
        so the registration path uses a local piecewise-linear geographic inverse.
        """
        if not self.ok or not _HAS_SCIPY:
            return None
        a=self.samples
        if bbox is not None:
            lat0,lon0,lat1,lon1=map(float,bbox)
            pad_lat=max(0.02,abs(lat1-lat0)*0.08); pad_lon=max(0.02,abs(lon1-lon0)*0.08)
            mask=(a[:,2]>=min(lat0,lat1)-pad_lat)&(a[:,2]<=max(lat0,lat1)+pad_lat)&(a[:,3]>=min(lon0,lon1)-pad_lon)&(a[:,3]<=max(lon0,lon1)+pad_lon)
            q=a[mask]
            if len(q)>=16: a=q
        if len(a)>max_points:
            idx=np.linspace(0,len(a)-1,max_points,dtype=int); a=a[idx]
        pts=np.c_[a[:,3],a[:,2]]
        try:
            fi=LinearNDInterpolator(pts,a[:,0],fill_value=np.nan)
            fj=LinearNDInterpolator(pts,a[:,1],fill_value=np.nan)
            return fi,fj
        except Exception:
            return None

    def native_grid_from_lonlat(self, lon_grid, lat_grid, bbox=None):
        inv=self.inverse_interpolators(bbox=bbox)
        if inv is None: return None,None
        fi,fj=inv
        scan=fi(lon_grid,lat_grid).astype(np.float32)
        pix=fj(lon_grid,lat_grid).astype(np.float32)
        return scan,pix

    def intersection_bbox(self,other):
        poly=self.intersection_polygon(other)
        if not poly: return None
        xs=[p[0] for p in poly]; ys=[p[1] for p in poly]
        return (min(ys),min(xs),max(ys),max(xs))

    def pixel_window_for_polygon(self,poly,pad=0.03):
        if not self.ok or not poly: return None
        if _HAS_SHAPELY:
            try:
                shp=Polygon(poly)
                q=[]
                for scan,pix,lat,lon in self.samples:
                    if shp.covers(Point(float(lon),float(lat))): q.append((scan,pix))
                if q:
                    q=np.asarray(q,float); r0,r1=q[:,0].min(),q[:,0].max(); c0,c1=q[:,1].min(),q[:,1].max()
                    dr=max(2.0,(r1-r0)*pad); dc=max(2.0,(c1-c0)*pad)
                    return (r0-dr,r1+dr,c0-dc,c1+dc)
            except Exception: pass
        xs=[p[0] for p in poly]; ys=[p[1] for p in poly]
        return self.pixel_window_for_bbox((min(ys),min(xs),max(ys),max(xs)),pad=pad)

    def pixel_window_for_bbox(self,bbox,pad=0.03):
        if not self.ok: return None
        lat0,lon0,lat1,lon1=map(float,bbox)
        if lat1<lat0: lat0,lat1=lat1,lat0
        if lon1<lon0: lon0,lon1=lon1,lon0
        a=self.samples; mask=(a[:,2]>=lat0)&(a[:,2]<=lat1)&(a[:,3]>=lon0)&(a[:,3]<=lon1)
        if np.any(mask):
            q=a[mask]; r0,r1=q[:,0].min(),q[:,0].max(); c0,c1=q[:,1].min(),q[:,1].max()
        else:
            M=np.array([[self.coef_lat[0],self.coef_lat[1]],[self.coef_lon[0],self.coef_lon[1]]],float); b=np.array([self.coef_lat[2],self.coef_lon[2]])
            if abs(np.linalg.det(M))<1e-12: return None
            pts=[np.linalg.solve(M,np.array([lat,lon])-b) for lat,lon in [(lat0,lon0),(lat0,lon1),(lat1,lon0),(lat1,lon1)]]; pts=np.asarray(pts); r0,r1=pts[:,0].min(),pts[:,0].max(); c0,c1=pts[:,1].min(),pts[:,1].max()
        dr=max(2.0,(r1-r0)*pad); dc=max(2.0,(c1-c0)*pad); return (r0-dr,r1+dr,c0-dc,c1+dc)
