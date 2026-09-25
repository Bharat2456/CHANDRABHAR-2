from app.core.physical import plan_common_gsd
def test_plan():
 p=plan_common_gsd(.25,4.58,levels=(1,2)); assert p[0].target_gsd_m==4.58; assert p[0].ref_factor>1; assert p[0].src_factor==1
