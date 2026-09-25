from app.core.tiles import make_tiles
def test_tiles(): assert len(make_tiles(2500,2300,1024,.2))>1

def test_geometry_mapper_uses_direct_aoi_samples(tmp_path):
    p=tmp_path/'g.csv'
    p.write_text('line,sample,latitude,longitude\n0,0,-85.0,20.0\n0,100,-85.0,21.0\n100,0,-84.0,20.0\n100,100,-84.0,21.0\n')
    from app.geo.mapper import GeometryMapper
    g=GeometryMapper(p)
    w=g.pixel_window_for_bbox((-84.9,20.1,-84.1,20.9),pad=0.0)
    assert w is not None
    assert 0 <= w[0] <= 100 and 0 <= w[1] <= 100

def test_pair_aoi_requires_footprint_intersection():
    from app.core.pipeline import Engine
    e=Engine()
    a={'upper_left_latitude':-85,'upper_left_longitude':20,'upper_right_latitude':-85,'upper_right_longitude':21,'lower_left_latitude':-84,'lower_left_longitude':20,'lower_right_latitude':-84,'lower_right_longitude':21}
    b={'upper_left_latitude':-85,'upper_left_longitude':20.5,'upper_right_latitude':-85,'upper_right_longitude':22,'lower_left_latitude':-84,'lower_left_longitude':20.5,'lower_right_latitude':-84,'lower_right_longitude':22}
    assert e._intersection_bbox(a,b)==(-85,20.5,-84,21)

def test_register_uses_pair_footprint_aoi(tmp_path, monkeypatch):
    import numpy as np
    from app.core.pipeline import Engine
    from app.model import SceneSpec, ArraySpec, MatchResult
    a=np.zeros((64,64),dtype=np.uint8); pa=tmp_path/'a.bin'; a.tofile(pa)
    b=np.zeros((64,64),dtype=np.uint8); pb=tmp_path/'b.bin'; b.tofile(pb)
    fp=lambda lo: {'upper_left_latitude':-85,'upper_left_longitude':lo,'upper_right_latitude':-85,'upper_right_longitude':lo+1,'lower_left_latitude':-84,'lower_left_longitude':lo,'lower_right_latitude':-84,'lower_right_longitude':lo+1}
    sa=SceneSpec('A','a',pa,ArraySpec(pa,a.shape,a.dtype),gsd_m=4.58,footprint=fp(20))
    sb=SceneSpec('B','b',pb,ArraySpec(pb,b.shape,b.dtype),gsd_m=4.58,footprint=fp(20.5))
    def fake(*args,**kwargs):
        return MatchResult('fixture',1,1,0,0,0.0,None,None,None,0.0,None,diagnostics={'status':'INSUFFICIENT_EVIDENCE','physical_grid_shape':[1,1]})
    monkeypatch.setattr(Engine,'_tile_match',fake)
    r=Engine(levels=(1.0,)).register(sa,sb,'a_b')
    assert r.diagnostics['pair_aoi_latlon']==(-85,20.5,-84,21)
