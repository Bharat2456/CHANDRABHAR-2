"""Deterministic SYNTHETIC test fixtures (not Chandrayaan-2 data).

Two simulated sensors sample one procedural lunar-like surface through different,
rotated pixel->(lon,lat) geometries, and are written as PDS4 label+binary with ISRO-style
GRD geometry CSVs.  Because the surface is analytic, the true geographic relationship
between the two images is known exactly, so geo-warp registration can be checked.
"""
from __future__ import annotations
import json, math
from pathlib import Path
import numpy as np

R_MOON = 1737400.0
LON0, LAT0 = 23.4, -41.0

def _surface_params(seed=11, n=520, extent=2400.0):
    rng = np.random.default_rng(seed)
    return dict(
        x=rng.uniform(-extent/2, extent/2, n), y=rng.uniform(-extent/2, extent/2, n),
        r=np.exp(rng.uniform(math.log(14), math.log(110), n)), a=rng.uniform(.4, 1.0, n)*rng.choice([-1, 1], n),
        w=rng.uniform(.18, .35, n))

def surface(xm, ym, P):
    """Analytic albedo/topography proxy at local metric coords (east, north) in metres."""
    out = np.zeros_like(xm, dtype=np.float64)
    for x, y, r, a, w in zip(P['x'], P['y'], P['r'], P['a'], P['w']):
        d = np.hypot(xm-x, ym-y)
        out += a*np.exp(-((d-r)/(w*r+3.0))**2) - 0.35*a*np.exp(-(d/(0.8*r))**2)
    out += 0.25*np.sin(xm/37.0+1.3)*np.sin(ym/53.0-.4) + 0.12*np.sin((xm+ym)/19.0)
    return out

def _lonlat(x, y):
    lat = LAT0 + np.degrees(y/R_MOON)
    lon = LON0 + np.degrees(x/(R_MOON*math.cos(math.radians(LAT0))))
    return lon, lat

def _sensor_xy(rows, cols, gsd, theta_deg, ox, oy):
    t = math.radians(theta_deg); c, s = math.cos(t), math.sin(t)
    u = (np.asarray(cols, float)+0.5)*gsd; v = (np.asarray(rows, float)+0.5)*gsd
    return ox + c*u - s*v, oy + s*u + c*v

def render(h, w, gsd, theta, ox, oy, P, gamma=1.0, tilt=0.0, noise=0.0, seed=0):
    rr, cc = np.mgrid[0:h, 0:w]
    x, y = _sensor_xy(rr, cc, gsd, theta, ox, oy)
    f = surface(x, y, P)
    f = (f-np.percentile(f, 1))/(np.percentile(f, 99)-np.percentile(f, 1)+1e-9)
    f = np.clip(f, 0, 1)**gamma
    f = f*(1+tilt*(cc/w-.5))
    if noise: f = f+np.random.default_rng(seed).normal(0, noise, f.shape)
    return np.clip(f, 0, 1)

def _label(pid, title, fn, size, dtype_name, h, w, gsd, solar_el, solar_az, extra_axes=None):
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<Product_Observational xmlns="http://pds.nasa.gov/pds4/pds/v1">
 <Identification_Area><logical_identifier>urn:isro:isda:ch2_synth:data_calibrated:{pid}</logical_identifier><title>{title}</title></Identification_Area>
 <Observation_Area><Time_Coordinates><start_date_time>2021-01-01T00:00:00Z</start_date_time><stop_date_time>2021-01-01T00:00:10Z</stop_date_time></Time_Coordinates>
  <Discipline_Area><Imaging_Parameters><pixel_resolution>{gsd}</pixel_resolution><solar_elevation>{solar_el}</solar_elevation><solar_azimuth>{solar_az}</solar_azimuth></Imaging_Parameters></Discipline_Area></Observation_Area>
 <File_Area_Observational><File><file_name>{fn}</file_name><file_size>{size}</file_size></File>
  <Array_2D_Image><offset>0</offset><axes>2</axes><axis_index_order>Last Index Fastest</axis_index_order><Element_Array><data_type>{dtype_name}</data_type></Element_Array>
   <Axis_Array><axis_name>Line</axis_name><elements>{h}</elements><sequence_number>1</sequence_number></Axis_Array>
   <Axis_Array><axis_name>Sample</axis_name><elements>{w}</elements><sequence_number>2</sequence_number></Axis_Array>
  </Array_2D_Image></File_Area_Observational>
</Product_Observational>
'''

def _write_sensor(root: Path, key, token, h, w, gsd, theta, ox, oy, P, date='20210101', **rk):
    img = render(h, w, gsd, theta, ox, oy, P, **rk)
    dn = (img*4000).astype('<u2')
    stem = f'ch2_{token}_synth_{date}t0000000000_d_img_d18'
    d = root/key/'data'/'calibrated'/date; g = root/key/'geometry'/'calibrated'/date
    d.mkdir(parents=True, exist_ok=True); g.mkdir(parents=True, exist_ok=True)
    (d/f'{stem}.img').write_bytes(dn.tobytes())
    (d/f'{stem}.xml').write_text(_label(f'{stem}', f'Synthetic {key} {token}', f'{stem}.img', dn.nbytes, 'UnsignedLSB2', h, w, gsd, 35.0, 110.0))
    rows = sorted(set(list(range(0, h, 12))+[h-1])); cols = sorted(set(list(range(0, w, 12))+[w-1]))
    lines = ['Scan,Pixel,Latitude,Longitude']
    for r in rows:
        for c in cols:
            x, y = _sensor_xy(r, c, gsd, theta, ox, oy); lon, lat = _lonlat(x, y)
            lines.append(f'{r},{c},{float(lat):.9f},{float(lon):.9f}')
    (g/f'{stem.replace("_d_img_","_g_grd_")}.csv').write_text('\n'.join(lines)+'\n')
    return d/f'{stem}.xml'

def build_archive(root, seed=11):
    """OHRC-like (2 m) and TMC2-like (5 m, rotated, different radiometry) over one surface."""
    root = Path(root); P = _surface_params(seed)
    a = _write_sensor(root, 'ohrc', 'ohr_ncp', 520, 520, 2.0, 0.0, -700.0, -650.0, P)
    b = _write_sensor(root, 'tmc2', 'tmc_ncf', 260, 260, 5.0, 8.0, -520.0, -560.0, P, gamma=0.7, tilt=0.35, noise=0.01, seed=3)
    return {'OHRC': a, 'TMC2': b, 'truth': {'surface_seed': seed, 'lon0': LON0, 'lat0': LAT0}}

def build_misc(root):
    """One of every non-PDS4 format: npy, ENVI (BIL, big-endian), raw+sidecar (BIP)."""
    root = Path(root); root.mkdir(parents=True, exist_ok=True); rng = np.random.default_rng(5)
    a = (rng.random((90, 120))*1000).astype(np.float32); np.save(root/'plain.npy', a)
    bil = (rng.random((40, 6, 50))*500).astype('>i2')       # lines, bands, samples
    (root/'cube.img').write_bytes(bil.tobytes())
    (root/'cube.hdr').write_text('ENVI\nsamples = 50\nlines = 40\nbands = 6\nheader offset = 0\ndata type = 2\ninterleave = bil\nbyte order = 1\npixel size = {12.5, 12.5}\n')
    bip = (rng.random((30, 40, 5))*100).astype('<f4')
    (root/'bip.raw').write_bytes(b'\x00'*16+bip.tobytes())
    (root/'bip.raw.json').write_text(json.dumps({'dtype': '<f4', 'shape': [30, 40, 5], 'offset': 16, 'interleave': 'bip', 'sensor': 'IIRS', 'product_id': 'bip_fixture', 'gsd_m': 60.0}))
    return {'npy': a, 'bil': bil, 'bip': bip}

if __name__ == '__main__':
    import sys
    out = Path(sys.argv[1] if len(sys.argv) > 1 else 'tests/fixtures/synthetic_archive')
    print(build_archive(out)); build_misc(out/'misc'); print('written to', out)
