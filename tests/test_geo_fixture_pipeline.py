"""Geographic-warp registration against a SYNTHETIC surface with exactly known geometry."""
import json, numpy as np, pytest
from app.adapters import AdapterRegistry
from app.core.pipeline import Engine
from app.core.hooks import Hooks
from app.core.evidence import gate, GATE_THRESHOLDS
from app.synthetic import build_archive

@pytest.fixture(scope='module')
def pair(tmp_path_factory):
    root=tmp_path_factory.mktemp('arch'); f=build_archive(root)
    return AdapterRegistry.inspect(f['OHRC'],root=root), AdapterRegistry.inspect(f['TMC2'],root=root)

def test_geo_warp_recovers_known_geometry(pair):
    a,b=pair; res=Engine(levels=(1.0,)).register(a,b,'fx'); d=res.diagnostics
    assert d['pair_aoi_method']['status']=='TRUE_SWATH_INTERSECTION' and d['status']=='VALIDATED' and d['geographic_warp'] is True
    H=res.homography/res.homography[2,2]
    assert abs(H[0,2])<1.0 and abs(H[1,2])<1.0                                   # < 1 grid px (5 m)
    assert np.allclose(H[:2,:2],np.eye(2),atol=0.01)                              # no residual rotation/scale
    assert res.inlier_mask is not None and int(res.inlier_mask.sum())==res.inliers

def test_runs_are_reproducible(pair):
    a,b=pair; r1=Engine(levels=(1.0,)).register(a,b,'x'); r2=Engine(levels=(1.0,)).register(a,b,'x')
    assert r1.inliers==r2.inliers and np.allclose(r1.homography,r2.homography)

def test_hooks_report_real_progress(pair):
    a,b=pair; ev=[]
    class H(Hooks):
        def stage(self,n,**k): ev.append(('stage',n))
        def tile(self,i,n,**k): ev.append(('tile',i,n))
        def capture(self,*x): ev.append(('cap',))
    Engine(levels=(1.0,),hooks=H()).register(a,b,'x')
    tiles=[e for e in ev if e[0]=='tile']; assert tiles and all(1<=t[1]<=t[2] for t in tiles)
    assert ('stage','evidence_gate') in ev and any(e[0]=='cap' for e in ev)

def test_gate_thresholds_single_source():
    from app.core import evidence
    class R: tentative_matches=100; inliers=11; inlier_ratio=.9; coverage=1; rmse_px=1; diagnostics={}
    assert gate(R)['reasons']==['too_few_inliers']
    assert GATE_THRESHOLDS['min_inliers']==12 and GATE_THRESHOLDS['max_rmse_px']==2.5

def test_no_overlap_is_reported_not_faked(tmp_path):
    from app.synthetic import _surface_params,_write_sensor
    P=_surface_params(); a=_write_sensor(tmp_path,'ohrc','ohr_ncp',200,200,2.0,0,-700,-650,P); b=_write_sensor(tmp_path,'tmc2','tmc_ncf',100,100,5.0,0,5000,5000,P)
    A=AdapterRegistry.inspect(a,root=tmp_path); B=AdapterRegistry.inspect(b,root=tmp_path)
    from app.geo.mapper import GeometryMapper
    assert GeometryMapper(A.metadata['geometry_csv']).intersection_polygon(GeometryMapper(B.metadata['geometry_csv']))==[]

def test_low_texture_and_noise_do_not_validate():
    from app.core.matcher import match_representations
    rng=np.random.default_rng(0); flat=np.full((300,300),0.5,np.float32)
    assert match_representations(flat,flat.copy()).diagnostics['status']=='INSUFFICIENT_EVIDENCE'   # no texture at all
    n1=rng.random((300,300)).astype(np.float32); n2=rng.random((300,300)).astype(np.float32)
    assert match_representations(n1,n2).diagnostics['status']=='INSUFFICIENT_EVIDENCE'             # unrelated noise
    f1=0.5+rng.normal(0,.001,(300,300)).astype(np.float32); f2=0.5+rng.normal(0,.001,(300,300)).astype(np.float32)
    assert match_representations(f1,f2).diagnostics['status']=='INSUFFICIENT_EVIDENCE'             # independent faint noise

def test_documented_limit_identical_copy_passes_gate():
    """The gate measures internal geometric consistency, NOT ground truth: an image trivially
    matches its own copy. Passing the gate is therefore never reported as validation."""
    from app.core.matcher import match_representations
    rng=np.random.default_rng(0); n=rng.random((300,300)).astype(np.float32)
    assert match_representations(n,n.copy()).diagnostics['status']=='VALIDATED'
