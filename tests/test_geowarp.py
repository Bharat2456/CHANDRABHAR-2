import numpy as np, cv2
from pathlib import Path
from app.model import SceneSpec, ArraySpec
from app.core.pipeline import Engine

def _geom(path, n=256, step=32, scale=1e-4):
    rows=['Longitude,Latitude,Pixel,Scan']
    for scan in range(0,n,step):
        for pix in range(0,n,step):
            rows.append(f'{pix*scale},{scan*scale},{pix},{scan}')
    # include final boundary
    for scan in [n-1]:
        for pix in range(0,n,step): rows.append(f'{pix*scale},{scan*scale},{pix},{scan}')
    for pix in [n-1]:
        for scan in range(0,n,step): rows.append(f'{pix*scale},{scan*scale},{pix},{scan}')
    path.write_text('\n'.join(rows))

def test_geographic_warp_aligns_two_sensors(tmp_path):
    n=256; rng=np.random.default_rng(3)
    base=np.zeros((n,n),np.uint8)
    for _ in range(50):
        x,y=rng.integers(15,n-15,2); cv2.circle(base,(int(x),int(y)),int(rng.integers(3,10)),int(rng.integers(80,255)),-1)
    for _ in range(15):
        x,y=rng.integers(10,n-30,2); cv2.line(base,(int(x),int(y)),(int(x+rng.integers(10,35)),int(y+rng.integers(10,35))),200,2)
    src=cv2.GaussianBlur(base,(0,0),0.8)
    M=np.float32([[1,0,3],[0,1,-2]]); src=cv2.warpAffine(src,M,(n,n),borderMode=cv2.BORDER_REFLECT)
    pa=tmp_path/'a.bin'; pb=tmp_path/'b.bin'; ga=tmp_path/'a.csv'; gb=tmp_path/'b.csv'
    base.tofile(pa); src.tofile(pb); _geom(ga); _geom(gb)
    sa=SceneSpec('OHRC','a',pa,ArraySpec(pa,base.shape,base.dtype),gsd_m=1.0,metadata={'geometry_csv':str(ga)},footprint={'upper_left_latitude':0,'upper_left_longitude':0,'upper_right_latitude':0,'upper_right_longitude':255e-4,'lower_left_latitude':255e-4,'lower_left_longitude':0,'lower_right_latitude':255e-4,'lower_right_longitude':255e-4})
    sb=SceneSpec('TMC2','b',pb,ArraySpec(pb,src.shape,src.dtype),gsd_m=1.0,metadata={'geometry_csv':str(gb)},footprint=sa.footprint)
    r=Engine(levels=(1.0,),tile_px=128,overlap=.2).register(sa,sb,'geo_synth')
    assert r.diagnostics.get('geographic_warp') is True
    assert r.inliers >= 12 or r.tentative_matches >= 12


def test_iirs_geowarp_spectral_representation(tmp_path):
    n=128; bands=24
    rng=np.random.default_rng(8); base=rng.random((n,n),dtype=np.float32)
    arr=np.stack([base*(0.7+0.02*b) for b in range(bands)],axis=0).astype(np.float32)
    data=tmp_path/'iirs.bin'; arr.tofile(data); g=tmp_path/'iirs.csv'; _geom(g,n=n,step=16,scale=1e-4)
    from app.model import SceneSpec,ArraySpec
    from app.io.reader import SceneReader
    from app.geo.mapper import GeometryMapper
    from app.core.geowarp import GeoGrid,warp_iirs_rep_to_grid
    spec=SceneSpec('IIRS','i',data,ArraySpec(data,arr.shape,arr.dtype,interleave='bsq'),gsd_m=1.0,metadata={'geometry_csv':str(g)})
    mapper=GeometryMapper(g); poly=mapper.footprint_polygon(); grid=GeoGrid(poly,1.0,max_pixels=100000)
    rep=warp_iirs_rep_to_grid(SceneReader(spec),mapper,grid,0,min(64,grid.height),0,min(64,grid.width))
    assert rep is not None and rep.shape[2]==3 and np.isfinite(rep).all()


def test_safe_remap_handles_oversized_native_source(tmp_path):
    from app.core.geowarp import _bounded_remap
    import numpy as np
    src=np.arange(40000*8,dtype=np.float32).reshape(40000,8)
    y=np.repeat(np.linspace(100,39000,64,dtype=np.float32)[:,None],8,axis=1)
    x=np.tile(np.arange(8,dtype=np.float32),(64,1))
    out=_bounded_remap(src,x,y)
    assert out.shape==(64,8) and np.isfinite(out).all()
