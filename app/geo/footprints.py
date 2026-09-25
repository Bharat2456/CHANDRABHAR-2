from pathlib import Path
import json

def load_geojson(path):
 d=json.loads(Path(path).read_text())
 if d.get('type')=='FeatureCollection': return [f['geometry'] for f in d.get('features',[]) if f.get('geometry')]
 if d.get('type')=='Feature': return [d['geometry']]
 return [d]
def bbox_geom(g):
 def pts(x):
  if isinstance(x[0],(int,float)): yield x
  else:
   for y in x: yield from pts(y)
 p=list(pts(g['coordinates'])); xs=[q[0] for q in p]; ys=[q[1] for q in p]; return min(xs),min(ys),max(xs),max(ys)
def intersect_bbox(a,b):
 ax0,ay0,ax1,ay1=a; bx0,by0,bx1,by1=b; x0=max(ax0,bx0); y0=max(ay0,by0); x1=min(ax1,bx1); y1=min(ay1,by1); return None if x1<=x0 or y1<=y0 else (x0,y0,x1,y1)
