"""Browser bridge: the only module the web worker talks to.

Everything here is a thin orchestration layer over the unchanged scientific engine
(adapters -> geometry -> engine -> evidence gate).  It never computes a scientific value
itself except presentation-only summaries (homography decomposition, previews), and it
never opens a network connection.  All functions return JSON strings or PNG bytes.
"""
from __future__ import annotations
import hashlib, json, math, os, sys, time, traceback
from pathlib import Path
import numpy as np
import cv2

from app.adapters import AdapterRegistry
from app.core.pipeline import Engine
from app.core.hooks import Hooks
from app.core.evidence import GATE_THRESHOLDS, gate
from app.io.reader import SceneReader
from app.geo.mapper import GeometryMapper
from app.safepath import read_text_limited

ROOTS = {'user': '/ws', 'demo': '/demo'}
LABEL_EXT = {'.xml', '.hdr', '.npy'}
RAW_EXT = {'.raw', '.bin', '.dat'}
DEFAULT_LIMITS = {'max_geometry_csv_mb': 256, 'max_grid_pixels': 12_000_000, 'max_preview_dim': 768}
_S = {'specs': {}, 'infos': {}, 'blobs': {}, 'overrides': {}, 'limits': dict(DEFAULT_LIMITS), 'maps': {}}


# ------------------------------------------------------------------ helpers
def clean(o):
    if isinstance(o, dict): return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)): return [clean(v) for v in o]
    if isinstance(o, np.ndarray): return clean(o.tolist())
    if isinstance(o, (np.floating, float)):
        v = float(o); return v if math.isfinite(v) else None
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, (np.bool_,)): return bool(o)
    if isinstance(o, Path): return str(o)
    if isinstance(o, np.dtype): return str(o)
    return o

def dumps(o): return json.dumps(clean(o), allow_nan=False)

def _rel(p, root):
    try: return Path(p).relative_to(root).as_posix()
    except Exception: return Path(p).name

def _png(arr_u8_or_bgra):
    ok, buf = cv2.imencode('.png', arr_u8_or_bgra)
    if not ok: raise RuntimeError('png encode failed')
    return buf.tobytes()

def put_blob(name, data): _S['blobs'][name] = data; return name
def get_blob(name): return _S['blobs'][name]
def clear_blobs(prefix=''):
    for k in [k for k in _S['blobs'] if k.startswith(prefix)]: del _S['blobs'][k]

def set_limits(js): _S['limits'].update(json.loads(js)); return dumps(_S['limits'])

def engine_info():
    import scipy, shapely
    ver = ''
    for cand in ('VERSION.txt', '../VERSION.txt'):
        pass
    return dumps({'python': sys.version.split()[0], 'platform': sys.platform, 'numpy': np.__version__, 'opencv': cv2.__version__,
                  'scipy': scipy.__version__, 'shapely': shapely.__version__, 'gate': GATE_THRESHOLDS,
                  'io_backend': 'stream' if sys.platform == 'emscripten' else 'memmap'})


# ------------------------------------------------------------------ workspace scan / inspect
def _walk(root):
    out = []
    if not os.path.isdir(root): return out
    for dp, dn, fn in os.walk(root):
        dn.sort()
        for f in sorted(fn):
            p = Path(dp)/f
            try: out.append((p, p.stat().st_size))
            except OSError: pass
    return out

def _adapter_name(p):
    for a in AdapterRegistry._adapters:
        try:
            if a.can_open(p): return a.name
        except Exception: pass
    return None

def _spec_info(key, spec, root, adapter, label):
    a = spec.array; md = spec.metadata or {}
    bands = 1
    if len(a.shape) == 3:
        bands = a.shape[0] if a.interleave == 'bsq' else (a.shape[1] if a.interleave == 'bil' else a.shape[2])
    H, W = SceneReader(spec).spatial_shape
    gcsv = md.get('geometry_csv')
    warnings = []
    if spec.sensor == 'UNKNOWN': warnings.append('sensor_unknown')
    if not spec.gsd_m: warnings.append('gsd_missing')
    if not gcsv: warnings.append('no_geometry_csv')
    mdsafe = {}
    for k, v in md.items():
        if isinstance(v, (str, int, float, bool)) or v is None: s = v
        elif isinstance(v, dict): s = {str(kk): (vv if isinstance(vv, (int, float, str, bool)) or vv is None else str(vv)) for kk, vv in v.items()}
        else: s = str(v)
        if isinstance(s, str): s = s.replace(str(root), '') if str(root) in s else s; s = s[:400]
        mdsafe[str(k)] = s
    return {'key': key, 'label': label, 'adapter': adapter, 'sensor': spec.sensor, 'product_id': spec.product_id,
            'shape': list(a.shape), 'dtype': str(a.dtype), 'offset': a.offset, 'interleave': a.interleave, 'bands': bands,
            'lines': int(H), 'samples': int(W), 'gsd_m': spec.gsd_m, 'data_file': _rel(a.path, root), 'data_bytes': int(Path(a.path).stat().st_size),
            'geometry_csv': _rel(gcsv, root) if gcsv else None, 'geometry_csv_bytes': int(Path(gcsv).stat().st_size) if gcsv and Path(gcsv).exists() else None,
            'solar_elevation_deg': spec.solar_elevation_deg, 'solar_azimuth_deg': spec.solar_azimuth_deg,
            'acquisition_start': spec.acquisition_start, 'acquisition_end': spec.acquisition_end,
            'metadata': mdsafe, 'warnings': warnings, 'synthetic': 'synth' in str(spec.product_id).lower() or 'demo' in key.split(':')[0]}

def inspect_workspace():
    """Inspect every mounted root with the real adapters.  Returns products, errors and unused files."""
    _S['specs'].clear(); _S['infos'].clear(); _S['maps'].clear()
    products, problems, ignored, used = [], [], [], set()
    files = {}
    for rname, root in ROOTS.items():
        rp = Path(root)
        for p, sz in _walk(root): files[(rname, p)] = sz
    for (rname, p), sz in files.items():
        rp = Path(ROOTS[rname]); rel = _rel(p, rp); key = f'{rname}:{rel}'; ext = p.suffix.lower()
        is_label = ext in LABEL_EXT or (ext in RAW_EXT and p.with_suffix(p.suffix+'.json').exists())
        if not is_label: continue
        adapter = _adapter_name(p)
        if adapter is None:
            if ext == '.xml': ignored.append({'file': key, 'reason': 'xml_not_pds4'})
            continue
        try:
            spec = AdapterRegistry.inspect(p, root=rp)
        except Exception as e:
            problems.append({'file': key, 'adapter': adapter, 'code': _classify_error(e), 'message': str(e)[:500]}); continue
        info = _spec_info(key, spec, rp, adapter, rel)
        gb = info['geometry_csv_bytes']
        if gb and gb > _S['limits']['max_geometry_csv_mb']*1024*1024:
            info['warnings'].append('geometry_too_large'); spec.metadata.pop('geometry_csv', None); info['geometry_csv'] = None
        _S['specs'][key] = spec; _S['infos'][key] = info; products.append(info)
        used.add((rname, p)); used.add((rname, Path(spec.array.path)))
        g = (spec.metadata or {}).get('geometry_csv')
        if g: used.add((rname, Path(g)))
        if adapter == 'raw_sidecar': used.add((rname, p.with_suffix(p.suffix+'.json')))
    for (rname, p), sz in sorted(files.items(), key=lambda kv: str(kv[0][1])):
        if (rname, p) in used: continue
        rel = f'{rname}:{_rel(p, Path(ROOTS[rname]))}'; ext = p.suffix.lower()
        if any(i['file'] == rel for i in ignored): continue
        if any(pr['file'] == rel for pr in problems): continue
        if ext in {'.img', '.qub', '.dat', '.raw', '.bin'}: reason = 'binary_without_label'
        elif ext == '.csv': reason = 'csv_not_referenced'
        elif ext == '.json': reason = 'json_not_sidecar'
        else: reason = 'unsupported_format'
        ignored.append({'file': rel, 'reason': reason, 'bytes': sz})
    products.sort(key=lambda i: i['key'])
    return dumps({'products': products, 'problems': problems, 'ignored': ignored, 'file_count': len(files), 'total_bytes': sum(files.values())})

def _classify_error(e):
    m = str(e).lower()
    if 'size mismatch' in m: return 'size_mismatch_truncated_or_wrong_dims'
    if 'not found' in m: return 'companion_missing'
    if 'unsupported pds4 data_type' in m or 'unsupported envi' in m: return 'unsupported_datatype'
    if 'dtd' in m or 'entit' in m: return 'unsafe_xml'
    if 'file name' in m or 'outside the workspace' in m: return 'unsafe_path'
    if 'invalid dimension' in m or 'expected a 2-d' in m: return 'invalid_dimensions'
    if 'no adapter' in m: return 'no_adapter'
    return 'invalid_metadata'

def set_override(key, js):
    """User-supplied GSD / sensor correction (recorded in the manifest, never silent)."""
    o = json.loads(js); spec = _S['specs'][key]; info = _S['infos'][key]; applied = {}
    if o.get('gsd_m') is not None:
        g = float(o['gsd_m'])
        if not (0 < g < 1e6): raise ValueError('GSD must be a positive number of metres')
        spec.gsd_m = g; info['gsd_m'] = g; applied['gsd_m'] = g
        if 'gsd_missing' in info['warnings']: info['warnings'].remove('gsd_missing')
    if o.get('sensor'):
        s = str(o['sensor']).upper()[:12]; spec.sensor = s; info['sensor'] = s; applied['sensor'] = s
        if 'sensor_unknown' in info['warnings']: info['warnings'].remove('sensor_unknown')
    info['overrides'] = {**info.get('overrides', {}), **applied}
    return dumps(info)

def file_hashes(rel_keys_json):
    """SHA-256 of small text companions (label/geometry/sidecar). Large binaries are identified by size only."""
    out = {}
    for key in json.loads(rel_keys_json):
        info = _S['infos'].get(key)
        if not info: continue
        rname = key.split(':', 1)[0]; root = Path(ROOTS[rname]); h = {}
        for f in filter(None, (info['label'], info['geometry_csv'])):
            p = root/f
            try:
                if p.stat().st_size <= 64*1024*1024:
                    d = hashlib.sha256()
                    with p.open('rb') as fh:
                        for chunk in iter(lambda: fh.read(1 << 20), b''): d.update(chunk)
                    h[f] = d.hexdigest()
            except OSError: pass
        out[key] = h
    return dumps(out)


# ------------------------------------------------------------------ previews
def product_preview(key, max_dim=None):
    spec = _S['specs'][key]; r = SceneReader(spec)
    md = int(max_dim or _S['limits']['max_preview_dim']); H, W = r.spatial_shape
    sr = max(1, math.ceil(H/md)); sc = max(1, math.ceil(W/md))
    bands = _S['infos'][key]['bands']
    use = [bands//2] if bands < 3 else sorted({bands//4, bands//2, (3*bands)//4})
    rows = list(range(0, H, sr)); ow = math.ceil(W/sc)
    out = np.full((len(rows), ow), np.nan, np.float32)
    for i, rw in enumerate(rows):
        acc = None
        for b in use:
            row = r.read_native(rw, rw+1, 0, W, b).astype(np.float32)[0]
            acc = row if acc is None else acc+row
        row = acc/len(use)
        pad = ow*sc-W
        if pad: row = np.concatenate([row, np.full(pad, np.nan, np.float32)])
        v = row.reshape(ow, sc)
        with np.errstate(all='ignore'):
            ok = np.isfinite(v); cnt = ok.sum(1); s = np.where(ok, v, 0).sum(1)
        out[i] = np.where(cnt > 0, s/np.maximum(cnt, 1), np.nan)
    fin = np.isfinite(out)
    stats = {'sampled_pixels': int(fin.sum()), 'finite_fraction': float(fin.mean()) if out.size else 0.0}
    if fin.any():
        lo, hi = np.percentile(out[fin], [2, 98]); stats.update(min=float(out[fin].min()), max=float(out[fin].max()), mean=float(out[fin].mean()), p2=float(lo), p98=float(hi))
        img = np.clip((out-lo)/max(hi-lo, 1e-9), 0, 1); img = np.where(fin, img, 0)
        a = np.where(fin, 255, 0).astype(np.uint8); g = (img*255).astype(np.uint8)
        png = _png(cv2.merge([g, g, g, a]))
    else:
        png = _png(np.zeros((8, 8, 4), np.uint8))
    name = put_blob(f'preview:{key}', png)
    return dumps({'blob': name, 'shape': [len(rows), ow], 'row_step': sr, 'col_step': sc, 'bands_used': use, 'stats': stats,
                  'note': 'Decimated preview: every %dth line, columns block-averaged by %d. Not used by the engine.' % (sr, sc)})


# ------------------------------------------------------------------ geometry / pair checks
def _poly_area_km2(poly, lat0):
    if not poly or len(poly) < 3: return 0.0
    R = 1737.4; k = math.cos(math.radians(lat0))
    xy = [(math.radians(x)*R*k, math.radians(y)*R) for x, y in poly]
    a = 0.0
    for i in range(len(xy)):
        x1, y1 = xy[i]; x2, y2 = xy[(i+1) % len(xy)]; a += x1*y2-x2*y1
    return abs(a)/2

def _mapper(key):
    if key not in _S['maps']:
        g = (_S['specs'][key].metadata or {}).get('geometry_csv')
        _S['maps'][key] = GeometryMapper(g) if g and Path(g).exists() else None
    return _S['maps'][key]

def pair_check(ref_key, src_key):
    r, s = _S['infos'][ref_key], _S['infos'][src_key]; msgs = []
    if ref_key == src_key: msgs.append({'tone': 'bad', 'code': 'same_product'})
    for role, i in (('reference', r), ('source', s)):
        if not i['gsd_m']: msgs.append({'tone': 'bad', 'code': 'gsd_missing', 'role': role})
        if i['sensor'] == 'UNKNOWN': msgs.append({'tone': 'warn', 'code': 'sensor_unknown', 'role': role})
    out = {'messages': msgs, 'geometry': None, 'gsd_ratio': None}
    if r['gsd_m'] and s['gsd_m']:
        hi, lo = max(r['gsd_m'], s['gsd_m']), min(r['gsd_m'], s['gsd_m']); out['gsd_ratio'] = hi/lo
        out['common_gsd_base_m'] = hi
        if hi/lo > 20: msgs.append({'tone': 'warn', 'code': 'large_gsd_ratio', 'ratio': hi/lo})
    mr, ms = _mapper(ref_key), _mapper(src_key)
    if mr is None or ms is None:
        msgs.append({'tone': 'warn', 'code': 'no_pair_geometry'})
        out['geometry'] = {'status': 'NO_GEOMETRY_FULL_SCENE_FALLBACK'}
    elif not (mr.ok and ms.ok):
        msgs.append({'tone': 'bad', 'code': 'geometry_unreadable', 'detail': getattr(mr, 'error', None) or getattr(ms, 'error', None)})
        out['geometry'] = {'status': 'GEOMETRY_UNAVAILABLE'}
    else:
        poly = mr.intersection_polygon(ms)
        if not poly:
            msgs.append({'tone': 'bad', 'code': 'no_overlap'}); out['geometry'] = {'status': 'NO_GEOMETRY_INTERSECTION'}
        else:
            lat0 = float(np.mean([p[1] for p in poly])); area = _poly_area_km2(poly, lat0)
            out['geometry'] = {'status': 'TRUE_SWATH_INTERSECTION', 'vertices': len(poly), 'area_km2': area, 'polygon': poly,
                               'ref_polygon': mr.footprint_polygon(), 'src_polygon': ms.footprint_polygon(),
                               'ref_fit_rms': mr.rms, 'src_fit_rms': ms.rms, 'ref_method': mr.footprint_method, 'src_method': ms.footprint_method}
            if area < 1e-6: msgs.append({'tone': 'bad', 'code': 'no_overlap'})
            base = out.get('common_gsd_base_m')
            if base:
                out['grid_estimates'] = [{'gsd_m': base*x, 'pixels': int(area*1e6/((base*x)**2))} for x in Engine().levels]
    return dumps(out)


# ------------------------------------------------------------------ registration
def decompose_h(H):
    H = np.asarray(H, float); H = H/H[2, 2]; A = H[:2, :2]
    sx = math.hypot(A[0, 0], A[1, 0]); rot = math.degrees(math.atan2(A[1, 0], A[0, 0]))
    det = float(np.linalg.det(A)); sy = det/sx if sx else float('nan')
    shear = float((A[0, 0]*A[0, 1]+A[1, 0]*A[1, 1])/sx/sx) if sx else float('nan')
    return {'matrix': H.tolist(), 'tx_px': float(H[0, 2]), 'ty_px': float(H[1, 2]), 'rotation_deg': rot, 'scale_x': sx, 'scale_y': sy,
            'shear': shear, 'det_affine': det, 'perspective_h31': float(H[2, 0]), 'perspective_h32': float(H[2, 1]),
            'cond_affine': float(np.linalg.cond(A))}

class WebHooks(Hooks):
    def __init__(self, emit, cfg):
        self.emit = emit; self.cfg = cfg; self.levels = {}; self.cur = None; self.t0 = time.time(); self.level_summ = []
        self.path_counts = {}; self.plan_gsd = None
    def _e(self, **k):
        k['t'] = round(time.time()-self.t0, 2)
        try: self.emit(dumps(k))
        except Exception: pass
    def stage(self, name, **info):
        if name == 'matching_level': self.plan_gsd = info.get('target_gsd_m')
        self._e(type='stage', stage=name, **info)
    def level_begin(self, index, total, target_gsd_m, grid_h, grid_w, mode):
        s = max(1.0, max(grid_h, grid_w)/self.cfg.get('canvas_px', 1400)); cw = max(1, math.ceil(grid_w/s)); ch = max(1, math.ceil(grid_h/s))
        capped = bool(self.plan_gsd and abs(target_gsd_m-self.plan_gsd)/self.plan_gsd > 1e-6)
        self.cur = {'capped': capped, 'planned_gsd': self.plan_gsd, 'index': index, 'gsd': target_gsd_m, 'h': grid_h, 'w': grid_w, 'mode': mode, 's': s, 'cw': cw, 'ch': ch,
                    'ref': np.zeros((ch, cw), np.float32), 'src': np.zeros((ch, cw), np.float32), 'rv': np.zeros((ch, cw), bool), 'sv': np.zeros((ch, cw), bool)}
        self.levels[index] = self.cur
        self._e(type='level', level=index+1, levels=total, target_gsd_m=target_gsd_m, grid=[grid_h, grid_w], mode=mode)
    def tile(self, index, total, **info):
        self._e(type='tile', tile=index, tiles=total, **info)
        mp = info.get('matcher_path') or 'none'; self.path_counts[mp] = self.path_counts.get(mp, 0)+1
    def capture(self, oi, oj, ref, src, mask=None):
        c = self.cur
        if c is None: return
        s = c['s']; ref = np.asarray(ref); src = np.asarray(src)
        ref = ref[..., 0] if ref.ndim == 3 else ref; src = src[..., 0] if src.ndim == 3 else src
        h, w = ref.shape; y0, x0 = int(round(oi/s)), int(round(oj/s)); y1, x1 = int(round((oi+h)/s)), int(round((oj+w)/s))
        y1 = min(y1, c['ch']); x1 = min(x1, c['cw'])
        if y1 <= y0 or x1 <= x0: return
        for name, a, vname in (('ref', ref, 'rv'), ('src', src, 'sv')):
            a = np.nan_to_num(a.astype(np.float32), nan=0.0, posinf=0.0, neginf=0.0)
            small = cv2.resize(a, (x1-x0, y1-y0), interpolation=cv2.INTER_AREA)
            valid = np.ones(a.shape, np.uint8) if mask is None else mask.astype(np.uint8)
            valid = np.minimum(valid, (a != 0).astype(np.uint8)) if mask is not None else valid
            vs = cv2.resize(valid, (x1-x0, y1-y0), interpolation=cv2.INTER_AREA) > 0
            c[name][y0:y1, x0:x1] = np.where(vs, small, c[name][y0:y1, x0:x1]); c[vname][y0:y1, x0:x1] |= vs
    def level_end(self, index, res):
        d = res.diagnostics
        gs = gate(res)
        self.level_summ.append({'index': index, 'target_gsd_m': d.get('target_gsd_m'), 'status': gs['status'], 'reasons': gs['reasons'], 'method': res.method,
                                'keypoints_ref': res.keypoints_ref, 'keypoints_src': res.keypoints_src, 'tentative': res.tentative_matches,
                                'inliers': res.inliers, 'inlier_ratio': res.inlier_ratio, 'coverage': res.coverage, 'rmse_px': res.rmse_px,
                                'rmse_m': d.get('rmse_m'), 'grid': d.get('physical_grid_shape'), 'geographic_warp': bool(d.get('geographic_warp')),
                                'tiles': len(d.get('tiles') or []), 'reason': d.get('reason')})
        self.levels[index]['result'] = res

def _to_u8(c, valid):
    v = c[valid]
    if v.size == 0: return np.zeros(c.shape, np.uint8), valid
    lo, hi = np.percentile(v, [2, 98]); g = np.clip((c-lo)/max(hi-lo, 1e-9), 0, 1); return (g*255).astype(np.uint8), valid

def _rgba(g, valid):
    a = np.where(valid, 255, 0).astype(np.uint8); g = np.where(valid, g, 0).astype(np.uint8); return cv2.merge([g, g, g, a])

def run_registration(ref_key, src_key, cfg_json, emit):
    cfg = json.loads(cfg_json or '{}'); t0 = time.time(); lim = _S['limits']
    levels = tuple(float(x) for x in cfg.get('levels', Engine().levels))
    hooks = WebHooks(emit, cfg)
    eng = Engine(levels=levels, tile_px=int(cfg.get('tile_px', 512)), overlap=float(cfg.get('overlap', 0.2)), ratio=float(cfg.get('sift_ratio', 0.78)),
                 max_grid_pixels=int(min(cfg.get('max_grid_pixels', lim['max_grid_pixels']), lim['max_grid_pixels'])), seed=int(cfg.get('seed', 12345)), hooks=hooks)
    rs, ss = _S['specs'][ref_key], _S['specs'][src_key]
    pc = json.loads(pair_check(ref_key, src_key))
    if any(m['tone'] == 'bad' for m in pc['messages']): raise ValueError('Pair rejected: ' + ', '.join(m['code'] for m in pc['messages'] if m['tone'] == 'bad'))
    hooks.stage('start')
    res = eng.register(rs, ss, f'{_S["infos"][ref_key]["product_id"]}__{_S["infos"][src_key]["product_id"]}')
    hooks.stage('packaging_evidence')
    d = res.diagnostics; best = next((lv for lv in hooks.levels.values() if lv.get('result') is res), None)
    pts_r, pts_s = np.asarray(res.points_ref, float).reshape(-1, 2), np.asarray(res.points_src, float).reshape(-1, 2)
    mask = np.asarray(res.inlier_mask, bool).ravel() if res.inlier_mask is not None else np.zeros(len(pts_r), bool)
    resid = np.empty(0)
    if res.homography is not None and len(pts_r):
        pred = cv2.perspectiveTransform(pts_s.reshape(-1, 1, 2).astype(np.float32), res.homography).reshape(-1, 2); resid = np.linalg.norm(pred-pts_r, axis=1)
    cap = 30000; idx = np.arange(len(pts_r))
    if len(idx) > cap: idx = np.linspace(0, len(idx)-1, cap).astype(int)
    out_imgs = {}; grid = None
    if best is not None:
        s = best['s']; rg, rv = _to_u8(best['ref'], best['rv']); sg, sv = _to_u8(best['src'], best['sv'])
        out_imgs['ref'] = put_blob('run:ref', _png(_rgba(rg, rv))); out_imgs['src'] = put_blob('run:src', _png(_rgba(sg, sv)))
        if res.homography is not None:
            D = np.diag([1/s, 1/s, 1.0]); Dinv = np.diag([s, s, 1.0]); Hc = D @ res.homography @ Dinv
            wg = cv2.warpPerspective(sg, Hc, (best['cw'], best['ch']), flags=cv2.INTER_LINEAR)
            wv = cv2.warpPerspective(sv.astype(np.uint8)*255, Hc, (best['cw'], best['ch']), flags=cv2.INTER_NEAREST) > 0
            out_imgs['src_aligned'] = put_blob('run:src_aligned', _png(_rgba(wg, wv)))
        grid = {'h': best['h'], 'w': best['w'], 'target_gsd_m': best['gsd'], 'mode': best['mode'], 'preview_scale': s, 'preview_w': best['cw'], 'preview_h': best['ch']}
    tiles = d.get('tiles') or []; paths = {}
    for t in tiles: paths[t.get('matcher_path') or 'sift'] = paths.get(t.get('matcher_path') or 'sift', 0)+1
    g = gate(res); ggeo = d.get('pair_aoi_method') or {}
    ggeo = {k: v for k, v in ggeo.items() if k != 'intersection_polygon'} if isinstance(ggeo, dict) else ggeo
    payload = {
        'ref': _S['infos'][ref_key], 'src': _S['infos'][src_key], 'status': g['status'], 'gate_reasons': g['reasons'],
        'gate_thresholds': GATE_THRESHOLDS,
        'claims': {'processing_completed': True, 'transformation_estimated': res.homography is not None, 'evidence_gate': g['status'], 'ground_truth_validation': 'NOT_ESTABLISHED'},
        'metrics': {'method': res.method, 'keypoints_ref': res.keypoints_ref, 'keypoints_src': res.keypoints_src, 'tentative_matches': res.tentative_matches,
                    'inliers': res.inliers, 'inlier_ratio': res.inlier_ratio, 'coverage': res.coverage, 'rmse_px': res.rmse_px,
                    'median_error_px': res.median_error_px, 'p95_error_px': res.p95_error_px, 'rmse_m': d.get('rmse_m'), 'target_gsd_m': d.get('target_gsd_m')},
        'homography': decompose_h(res.homography) if res.homography is not None else None,
        'levels': hooks.level_summ, 'matcher_paths': paths, 'geometry': ggeo, 'pair_geometry': pc['geometry'] and {k: v for k, v in pc['geometry'].items() if k in ('status', 'area_km2', 'vertices', 'polygon', 'ref_polygon', 'src_polygon')},
        'grid': grid, 'images': out_imgs, 'reason': d.get('reason'),
        'points': {'ref': pts_r[idx], 'src': pts_s[idx], 'inlier': mask[idx].astype(int) if len(mask) == len(pts_r) else [0]*len(idx), 'residual_px': resid[idx] if len(resid) else [],
                   'total': int(len(pts_r)), 'shown': int(len(idx))},
        'elapsed_s': time.time()-t0, 'engine_config': eng.config(), 'engine': json.loads(engine_info()),
        'warnings': _warnings(res, d, pc) + ([{'code': 'grid_capped', 'detail': f"requested {best['planned_gsd']:.3f} m, used {best['gsd']:.3f} m (memory preset max_grid_pixels={eng.max_grid_pixels})"}] if best and best.get('capped') else []), 'finished_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
    }
    return dumps(payload)

def _warnings(res, d, pc):
    w = []
    if d.get('reason'): w.append({'code': 'engine_reason', 'detail': str(d['reason'])})
    if (d.get('pair_aoi_method') or {}).get('status') not in ('TRUE_SWATH_INTERSECTION',): w.append({'code': 'no_true_swath_intersection', 'detail': str((d.get('pair_aoi_method') or {}).get('status'))})
    if pc.get('gsd_ratio') and pc['gsd_ratio'] > 20: w.append({'code': 'large_gsd_ratio', 'detail': f"{pc['gsd_ratio']:.1f}"})
    return w


# ------------------------------------------------------------------ demo + selftest
def make_demo():
    from app.synthetic import build_archive
    import shutil
    root = Path(ROOTS['demo'])
    if root.exists(): shutil.rmtree(root)
    root.mkdir(parents=True)
    build_archive(root)
    return 'ok'

def clear_demo():
    import shutil
    if os.path.isdir(ROOTS['demo']): shutil.rmtree(ROOTS['demo'])
    return 'ok'

def run_selftest():
    from app.selftest import run
    t = time.time(); r = run(); r['elapsed_s'] = time.time()-t; r['note'] = 'Synthetic engine self-test; not mission validation.'
    return dumps(r)


def window_sha256(key, r0, r1, c0, c1, band=0):
    """Diagnostic: SHA-256 of a native-dtype pixel window (used by cross-implementation parity tests)."""
    a = SceneReader(_S['specs'][key]).read_native(int(r0), int(r1), int(c0), int(c1), int(band))
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
