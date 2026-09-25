from dataclasses import dataclass
import math
@dataclass
class PhysicalPlan:
 target_gsd_m: float
 ref_factor: float
 src_factor: float
 strategy: str
 def as_dict(self): return self.__dict__.copy()
def plan_common_gsd(ref_gsd,src_gsd,mode='native_coarse',levels=(1.0,1.5,2.5,4.0,6.0)):
 r=float(ref_gsd); s=float(src_gsd); base=max(r,s)
 if mode=='native_coarse': targets=[base*x for x in levels]
 elif mode=='finest_common': targets=[base]
 else: targets=[base*x for x in levels]
 return [PhysicalPlan(float(t),float(t/r),float(t/s),'physical_common_gsd') for t in targets]
