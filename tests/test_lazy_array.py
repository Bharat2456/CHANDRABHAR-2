import numpy as np, pytest
from app.io.lazy_array import LazyArray

@pytest.mark.parametrize('inter,shape', [('native',(37,53)),('bsq',(5,37,53)),('bil',(37,5,53)),('bip',(37,53,5))])
@pytest.mark.parametrize('dt', ['<u2','>i2','<f4','>f8','u1'])
def test_stream_equals_memmap(tmp_path, inter, shape, dt):
    rng=np.random.default_rng(1); a=(rng.random(shape)*200).astype(dt); p=tmp_path/'x.bin'
    p.write_bytes(b'\x01'*24+a.tobytes())
    m=LazyArray(p,shape,dt,24,inter,backend='memmap'); s=LazyArray(p,shape,dt,24,inter,backend='stream')
    nb=m.band_count()
    for (r0,r1,c0,c1) in [(0,37,0,53),(3,11,5,9),(30,37,40,53),(0,1,0,1),(10,10,3,3)]:
        for b in range(nb):
            assert np.array_equal(m.read(r0,r1,c0,c1,b), s.read(r0,r1,c0,c1,b))
    s.close()

def test_stream_rejects_out_of_range_and_truncation(tmp_path):
    p=tmp_path/'t.bin'; p.write_bytes(bytes(100))
    s=LazyArray(p,(20,20),'u1',0,backend='stream')
    with pytest.raises(IndexError): s.read(0,21,0,5)
    with pytest.raises(EOFError): s.read(0,20,0,20)   # file shorter than declared


def test_js_reader_path_used_in_wasm(tmp_path, monkeypatch):
    """In the browser reads go through a host callback (64-bit-safe). Simulate it and require bit-exact results."""
    import sys, types
    import app.io.lazy_array as la
    shape = (60, 80); a = (np.random.default_rng(3).random(shape) * 999).astype('<u2'); p = tmp_path / 'x.bin'; p.write_bytes(b'\x07' * 10 + a.tobytes())
    calls = []
    class Arr:
        def __init__(self, b): self.b = b
        def to_py(self): return memoryview(self.b)
    def cb(path, pos, n):
        calls.append((pos, n)); d = open(path, 'rb').read(); return Arr(d[pos:pos + n])
    monkeypatch.setitem(sys.modules, 'js', types.SimpleNamespace(cb2ReadSlice=cb)); monkeypatch.setattr(la, '_in_wasm', lambda: True)
    s = la.LazyArray(p, shape, '<u2', 10, backend='stream')
    assert np.array_equal(s.read(5, 20, 7, 31), a[5:20, 7:31]) and calls
    with pytest.raises(EOFError):
        la.LazyArray(p, (60, 80), '<u2', 10 + 5000, backend='stream').read(50, 60, 0, 80)
