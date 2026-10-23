import json, pytest
from pathlib import Path
import app.web.bridge as b
from app.synthetic import build_archive, build_misc

@pytest.fixture()
def ws(tmp_path):
    old=dict(b.ROOTS); b.ROOTS['user']=str(tmp_path/'ws'); b.ROOTS['demo']=str(tmp_path/'demo')
    build_archive(tmp_path/'ws'); build_misc(tmp_path/'ws'/'misc'); (tmp_path/'ws'/'notes.txt').write_text('x'); (tmp_path/'ws'/'orphan.qub').write_bytes(b'1')
    yield tmp_path; b.ROOTS.update(old)

def test_inspect_classifies_everything(ws):
    r=json.loads(b.inspect_workspace()); kinds={p['adapter'] for p in r['products']}
    assert kinds=={'pds4','envi','numpy','raw_sidecar'}
    reasons={i['file']:i['reason'] for i in r['ignored']}
    assert reasons['user:notes.txt']=='unsupported_format' and reasons['user:orphan.qub']=='binary_without_label'
    pds=[p for p in r['products'] if p['adapter']=='pds4']
    assert all(p['geometry_csv'] and not p['warnings'] for p in pds)      # geometry companions found, no warnings
    assert not any(i['reason']=='csv_not_referenced' for i in r['ignored']) # geometry CSVs are consumed

def test_registration_payload_and_blobs(ws):
    r=json.loads(b.inspect_workspace()); k=[p['key'] for p in r['products'] if p['adapter']=='pds4']
    ev=[]; out=json.loads(b.run_registration(k[0],k[1],json.dumps({'levels':[1.0]}),ev.append))
    assert out['status']=='VALIDATED' and out['claims']['ground_truth_validation']=='NOT_ESTABLISHED'
    assert out['points']['total']==len(out['points']['inlier']) or out['points']['shown']==len(out['points']['inlier'])
    assert sum(out['points']['inlier'])==out['metrics']['inliers']
    for n in out['images'].values(): assert b.get_blob(n)[:8]==b'\x89PNG\r\n\x1a\n'
    assert out['engine_config']['rng_seed']==12345 and out['grid']['mode']=='geographic_warp'
    types={json.loads(e)['type'] for e in ev}; assert {'stage','level','tile'}<=types

def test_pair_check_rejects_same_and_missing_gsd(ws):
    r=json.loads(b.inspect_workspace()); npy=[p['key'] for p in r['products'] if p['adapter']=='numpy'][0]
    pc=json.loads(b.pair_check(npy,npy)); codes={m['code'] for m in pc['messages']}; assert {'same_product','gsd_missing'}<=codes
    with pytest.raises(ValueError): b.run_registration(npy,npy,'{}',lambda s:None)
    json.loads(b.set_override(npy,json.dumps({'gsd_m':3.0}))); assert not any(m['code']=='gsd_missing' for m in json.loads(b.pair_check(npy,npy))['messages'] if m.get('role')=='reference')

def test_preview_and_decompose(ws):
    r=json.loads(b.inspect_workspace()); k=r['products'][0]['key']; p=json.loads(b.product_preview(k,64))
    assert b.get_blob(p['blob'])[:4]==b'\x89PNG' and max(p['shape'])<=64
    d=b.decompose_h([[1,0,3],[0,1,-2],[0,0,1]]); assert d['tx_px']==3 and abs(d['rotation_deg'])<1e-9 and d['scale_x']==1
