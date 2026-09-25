import numpy as np
from pathlib import Path
from app.core.pipeline import Engine
from app.model import SceneSpec, ArraySpec

def test_physical_overview_boundary_no_broadcast(tmp_path):
    p=tmp_path/'x.bin'
    a=np.arange(155*97,dtype=np.uint8).reshape(155,97)
    p.write_bytes(a.tobytes())
    spec=SceneSpec('TEST','boundary',p,ArraySpec(p,a.shape,a.dtype),gsd_m=4.0)
    out,gsd,diag=Engine(tile_px=32)._overview(__import__('app.io.reader',fromlist=['SceneReader']).SceneReader(spec),4.58,window=(0,155,0,97))
    assert out.shape==(135,85)
    assert gsd==4.58
    assert diag['computational_stride']==1
    assert diag['physical_gsd_preserved'] is True

def test_large_overview_tiled_path_preserves_gsd(tmp_path):
    p=tmp_path/'large.bin'
    # 5001x5001 bytes: deliberately above the 25M direct-read threshold.
    shape=(5001,5001)
    with p.open('wb') as f:
        row=np.arange(shape[1],dtype=np.uint8)
        for _ in range(shape[0]): f.write(row.tobytes())
    spec=SceneSpec('TEST','large',p,ArraySpec(p,shape,np.dtype('uint8')),gsd_m=10.0)
    from app.io.reader import SceneReader
    out,gsd,diag=Engine(tile_px=256)._overview(SceneReader(spec),20.0,window=(0,5001,0,5001))
    assert out.shape==(2500,2500)
    assert gsd==20.0
    assert diag['computational_stride']==1
    assert diag['physical_gsd_preserved'] is True


def test_iirs_representation_is_tile_bounded(tmp_path):
    # BSQ fixture: 12 bands, enough pixels to expose accidental full-AOI rereads.
    shape=(12,64,80); p=tmp_path/'iirs.bin'
    arr=np.arange(np.prod(shape),dtype=np.float32).reshape(shape)
    arr.tofile(p)
    from app.io.reader import SceneReader
    spec=SceneSpec('IIRS','fixture',p,ArraySpec(p,shape,np.dtype('float32'),interleave='bsq'),gsd_m=89.91)
    r=SceneReader(spec)
    base=np.zeros((32,40),np.float32)
    rep=Engine(tile_px=32)._iirs_rep(r,(8,40,12,52),base,89.91)
    assert rep.shape==(32,40,2)
    assert np.isfinite(rep).all()


def test_iirs_tile_native_window_respects_parent_offset(tmp_path):
    p=tmp_path/'iirs_offset.bin'
    shape=(12,200,300)
    np.zeros(shape,dtype=np.float32).tofile(p)
    from app.io.reader import SceneReader
    spec=SceneSpec('IIRS','offset',p,ArraySpec(p,shape,np.dtype('float32'),interleave='bsq'),gsd_m=89.91)
    r=SceneReader(spec)
    e=Engine(tile_px=64)
    w=e._tile_native_window(r,(100,180,120,260),89.91,16,64,24,64)
    assert w==(115,165,143,185)
    assert w[0] >= 100 and w[1] <= 180 and w[2] >= 120 and w[3] <= 260


def test_iirs_rep_rejects_empty_window_without_opencv_resize(tmp_path):
    p=tmp_path/'iirs_empty.bin'
    shape=(12,32,40)
    np.zeros(shape,dtype=np.float32).tofile(p)
    from app.io.reader import SceneReader
    spec=SceneSpec('IIRS','empty',p,ArraySpec(p,shape,np.dtype('float32'),interleave='bsq'),gsd_m=89.91)
    r=SceneReader(spec)
    base=np.zeros((32,40),np.float32)
    rep=Engine()._iirs_rep(r,(20,20,5,10),base,89.91)
    assert rep.shape == base.shape
