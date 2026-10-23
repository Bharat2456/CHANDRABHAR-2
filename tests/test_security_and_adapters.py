import json, numpy as np, pytest
from pathlib import Path
from app.adapters import AdapterRegistry
from app.io.reader import SceneReader
from app.safepath import clean_name, UnsafePathError, parse_xml_safe
from app.synthetic import build_archive, build_misc

def test_npy_regression_pixels_exact(tmp_path):
    """Audit finding: header bytes used to be read as pixel data."""
    a=(np.arange(100*100)%251).astype(np.uint8).reshape(100,100); p=tmp_path/'t.npy'; np.save(p,a)
    s=AdapterRegistry.inspect(p)
    assert s.array.offset>0 and np.array_equal(SceneReader(s).read_native(0,100,0,100),a)

def test_npy_truncated_and_fortran_rejected(tmp_path):
    a=np.zeros((10,10),np.float32); p=tmp_path/'t.npy'; np.save(p,a); p.write_bytes(p.read_bytes()[:-8])
    with pytest.raises(ValueError, match='mismatch'): AdapterRegistry.inspect(p)
    q=tmp_path/'f.npy'; np.save(q,np.asfortranarray(np.zeros((4,5)))); 
    with pytest.raises(ValueError): AdapterRegistry.inspect(q)

@pytest.mark.parametrize('bad',['../x.img','/etc/passwd','a/b.img','..','c:\\x.img','x\x00.img'])
def test_clean_name_blocks_traversal(bad):
    with pytest.raises(UnsafePathError): clean_name(bad)

def _mut_label(root, repl):
    xml=next(Path(root).rglob('ch2_ohr*.xml')); xml.write_text(xml.read_text().replace(*repl)); return xml

def test_pds4_label_traversal_rejected(tmp_path):
    build_archive(tmp_path); xml=_mut_label(tmp_path,('ch2_ohr_ncp_synth_20210101t0000000000_d_img_d18.img','../../../../../etc/passwd</file_name><x>'))
    with pytest.raises(ValueError): AdapterRegistry.inspect(xml,root=tmp_path)

def test_pds4_truncated_binary_detected(tmp_path):
    build_archive(tmp_path); img=next(Path(tmp_path).rglob('*ohr*.img')); img.write_bytes(img.read_bytes()[:-2])
    xml=next(Path(tmp_path).rglob('ch2_ohr*.xml'))
    with pytest.raises(ValueError, match='size mismatch'): AdapterRegistry.inspect(xml,root=tmp_path)

def test_pds4_missing_data_file(tmp_path):
    build_archive(tmp_path); next(Path(tmp_path).rglob('*ohr*.img')).unlink(); xml=next(Path(tmp_path).rglob('ch2_ohr*.xml'))
    with pytest.raises(ValueError, match='not found'): AdapterRegistry.inspect(xml,root=tmp_path)

def test_pds4_unsupported_dtype_and_bad_dims(tmp_path):
    build_archive(tmp_path); xml=_mut_label(tmp_path,('UnsignedLSB2','ComplexLSB16'))
    with pytest.raises(ValueError, match='Unsupported PDS4'): AdapterRegistry.inspect(xml,root=tmp_path)
    xml.write_text(xml.read_text().replace('ComplexLSB16','UnsignedLSB2').replace('<elements>520</elements>','<elements>-5</elements>',1))
    with pytest.raises(ValueError): AdapterRegistry.inspect(xml,root=tmp_path)

def test_xml_entity_bomb_refused(tmp_path):
    p=tmp_path/'bomb.xml'; p.write_text('<?xml version="1.0"?><!DOCTYPE l [<!ENTITY a "aaaa"><!ENTITY b "&a;&a;&a;">]><l>&b;</l>')
    with pytest.raises(ValueError, match='DTD'): parse_xml_safe(p)

def test_workspace_root_confines_search(tmp_path):
    """A label inside the workspace must never trigger a search above the workspace root."""
    ws=tmp_path/'ws'; build_archive(ws); (tmp_path/'secret.img').write_bytes(b'x')
    xml=next(ws.rglob('ch2_tmc*.xml')); s=AdapterRegistry.inspect(xml,root=ws)
    assert ws in Path(s.array.path).parents and ws in Path(s.metadata['geometry_csv']).parents

def test_all_formats_roundtrip(tmp_path):
    ref=build_misc(tmp_path)
    s=AdapterRegistry.inspect(tmp_path/'plain.npy'); assert np.array_equal(SceneReader(s).read_native(0,90,0,120),ref['npy'])
    e=AdapterRegistry.inspect(tmp_path/'cube.hdr'); assert e.gsd_m==12.5 and e.array.interleave=='bil'
    for b in range(6): assert np.array_equal(SceneReader(e).read_native(5,20,3,30,b), ref['bil'][5:20,b,3:30])
    r=AdapterRegistry.inspect(tmp_path/'bip.raw'); assert r.sensor=='IIRS'
    for b in range(5): assert np.array_equal(SceneReader(r).read_native(0,30,0,40,b), ref['bip'][:,:,b])

def test_raw_sidecar_size_mismatch(tmp_path):
    (tmp_path/'a.raw').write_bytes(bytes(10)); (tmp_path/'a.raw.json').write_text(json.dumps({'dtype':'<f4','shape':[100,100]}))
    with pytest.raises(ValueError, match='mismatch'): AdapterRegistry.inspect(tmp_path/'a.raw')
