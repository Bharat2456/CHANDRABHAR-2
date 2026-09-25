from dataclasses import dataclass
from app.model import Tile
def make_tiles(h,w,tile=1024,overlap=0.2):
 step=max(1,int(tile*(1-overlap))); out=[]; r=0; idx=0
 while r<h:
  r1=min(h,r+tile); c=0
  while c<w:
   c1=min(w,c+tile); out.append(Tile(r,r1,c,c1,id=f't{idx:04d}')); idx+=1
   if c1==w: break
   c+=step
  if r1==h: break
  r+=step
 return out
