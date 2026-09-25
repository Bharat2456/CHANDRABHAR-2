from __future__ import annotations
from pathlib import Path
import re, xml.etree.ElementTree as ET
import numpy as np
from app.model import SceneSpec, ArraySpec
_DTYPE={"UnsignedByte":np.dtype("u1"),"UnsignedLSB2":np.dtype("<u2"),"UnsignedMSB2":np.dtype(">u2"),"SignedLSB2":np.dtype("<i2"),"SignedMSB2":np.dtype(">i2"),"UnsignedLSB4":np.dtype("<u4"),"UnsignedMSB4":np.dtype(">u4"),"SignedLSB4":np.dtype("<i4"),"SignedMSB4":np.dtype(">i4"),"IEEE754LSBSingle":np.dtype("<f4"),"IEEE754MSBSingle":np.dtype(">f4"),"IEEE754LSBDouble":np.dtype("<f8"),"IEEE754MSBDouble":np.dtype(">f8")}
def local(t): return t.rsplit('}',1)[-1]
def text(root,name,default=None):
    for e in root.iter():
        if local(e.tag)==name and e.text and e.text.strip(): return e.text.strip()
    return default
def alln(root,name): return [e for e in root.iter() if local(e.tag)==name]
def num(root,name):
    v=text(root,name)
    if v is None: return None
    try: return float(v)
    except: return None
def axes(root):
    out=[]
    for a in alln(root,'Axis_Array'):
        n=text(a,'axis_name'); e=text(a,'elements')
        if n and e: out.append((n,int(float(e))))
    return out
def sensor(path,root):
    s=(path.name+' '+(text(root,'title','') or '')).lower()
    for tok,name in [('iir','IIRS'),('ohr','OHRC'),('tmc','TMC2')]:
        if tok in s:return name
    return 'UNKNOWN'
def footprint(root):
    # Preserve labels when present; many CH-2 products expose four corner latitude/longitude values.
    vals={}
    for key in ('upper_left_latitude','upper_left_longitude','upper_right_latitude','upper_right_longitude','lower_left_latitude','lower_left_longitude','lower_right_latitude','lower_right_longitude'):
        v=num(root,key)
        if v is not None: vals[key]=v
    return vals or None
class PDS4Adapter:
    name='pds4'
    @classmethod
    def can_open(cls,path): return path.suffix.lower()=='.xml' and 'logical_identifier' in path.read_text(errors='ignore')[:200000]
    @classmethod
    def inspect(cls,path):
        path=Path(path); root=ET.parse(path).getroot(); logical=text(root,'logical_identifier',path.stem)
        product_id=logical.split(':')[-1]; fn=text(root,'file_name')
        if not fn: raise ValueError('PDS4 label has no file_name')
        candidates=[path.parent/fn,path.parent.parent.parent.parent/'data'/'calibrated'/path.parent.name/fn]
        data=next((p for p in candidates if p.exists()),None)
        if data is None:
            hits=list(path.parent.rglob(fn)); data=hits[0] if hits else None
        if data is None: raise FileNotFoundError(f'Data file {fn} not found for {path}')
        dtname=text(root,'data_type'); dt=_DTYPE.get(dtname)
        if dt is None: raise ValueError(f'Unsupported PDS4 data_type: {dtname}')
        ax=axes(root); shape=tuple(x[1] for x in ax)
        offset=int(float(text(root,'offset',0) or 0)); expected=offset+int(np.prod(shape))*dt.itemsize
        actual=data.stat().st_size
        if expected!=actual: raise ValueError(f'PDS4 binary size mismatch: expected {expected}, actual {actual}')
        meta={'logical_identifier':logical,'declared_file_size':int(float(text(root,'file_size',actual) or actual)),'data_type_name':dtname,'axis_names':[x[0] for x in ax],'footprint':footprint(root)}
        # Discover the sibling ISRO GRD geometry product.  The geometry file is
        # normally under <sensor>/geometry/calibrated/<date>/ and uses the same
        # acquisition stem with _g_grd_ in place of _d_img_.  Fall back to a
        # recursive search so the adapter remains usable after archive re-layout.
        archive_root=path.parent.parent.parent.parent if len(path.parents)>=4 else path.parent
        geos=[]
        if archive_root.exists():
            geo_dir=archive_root/'geometry'/'calibrated'/path.parent.name
            if geo_dir.exists():
                geos=list(geo_dir.glob(product_id+'*.csv'))
                if not geos:
                    stem=Path(fn).stem
                    prefix=stem.split('_d_img_')[0] if '_d_img_' in stem else stem
                    geos=list(geo_dir.glob(prefix+'*.csv'))
            if not geos:
                geos=list(archive_root.rglob(product_id+'*.csv'))
        if geos:
            meta['geometry_csv']=str(sorted(geos,key=lambda p: (('_g_grd_' not in p.name),len(p.name)))[0])
        for k in ('start_date_time','stop_date_time','solar_elevation','solar_azimuth','pixel_resolution','processing_level'):
            v=text(root,k)
            if v is not None: meta[k]=v
        gsd=num(root,'pixel_resolution')
        if gsd is None:
            # Some labels use a named resolution element; accept common aliases.
            for k in ('pixel_resolution_m','ground_sampling_distance','spatial_resolution'):
                gsd=num(root,k)
                if gsd is not None: break
        se=num(root,'solar_elevation'); sa=num(root,'solar_azimuth')
        inter='native'
        names=[x[0].lower() for x in ax]
        if len(shape)==3:
            if names[0] in {'band','bands'}: inter='bsq'
            elif names[-1] in {'band','bands'}: inter='bip'
            elif len(names)>1 and names[1] in {'band','bands'}: inter='bil'
        arr=ArraySpec(data,shape,dt,offset,inter,tuple(x[0] for x in ax),'C',metadata=meta)
        return SceneSpec(sensor(path,root),product_id,path,arr,gsd_m=gsd,acquisition_start=text(root,'start_date_time'),acquisition_end=text(root,'stop_date_time'),solar_elevation_deg=se,solar_azimuth_deg=sa,footprint=meta['footprint'],metadata=meta)
