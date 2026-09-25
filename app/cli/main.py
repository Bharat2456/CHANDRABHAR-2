import argparse,json
from pathlib import Path
from app.adapters import AdapterRegistry
from app.core.pipeline import Engine
def main():
 p=argparse.ArgumentParser(); sub=p.add_subparsers(dest='cmd',required=True)
 i=sub.add_parser('inspect'); i.add_argument('product')
 r=sub.add_parser('register'); r.add_argument('reference'); r.add_argument('source'); r.add_argument('--out',default='outputs/result.json')
 a=sub.add_parser('inventory'); a.add_argument('root')
 m=sub.add_parser('mission'); m.add_argument('--root',required=True); m.add_argument('--out',default='outputs/mission_validation')
 g=sub.add_parser('geometry-audit'); g.add_argument('--root',required=True)
 s=sub.add_parser('self-test')
 args=p.parse_args()
 if args.cmd=='inspect':
  x=AdapterRegistry.inspect(args.product); print(json.dumps({'sensor':x.sensor,'product_id':x.product_id,'shape':x.array.shape,'dtype':str(x.array.dtype),'gsd_m':x.gsd_m,'source':str(x.array.path),'metadata':x.metadata},indent=2,default=str)); return
 if args.cmd=='inventory':
  root=Path(args.root); hits=[]
  for pth in root.rglob('*'):
   if pth.suffix.lower() in {'.xml','.hdr','.npy'}:
    try:
     x=AdapterRegistry.inspect(pth); hits.append({'sensor':x.sensor,'product_id':x.product_id,'shape':x.array.shape,'gsd_m':x.gsd_m,'source':str(x.source)})
    except Exception: pass
  print(json.dumps({'count':len(hits),'products':hits},indent=2,default=str)); return
 if args.cmd=='geometry-audit':
  root=Path(args.root); ids={'OHRC':'ch2_ohr_ncp_20260103t1005176450_d_img_d18.xml','TMC2':'ch2_tmc_ncf_20231101t1708581528_d_img_d18.xml','IIRS':'ch2_iir_nci_20210622t1850441449_d_img_d32.xml'}
  found={k:AdapterRegistry.inspect(next(root.rglob(v))) for k,v in ids.items()}
  from app.geo.mapper import GeometryMapper
  out={}
  for k,spec in found.items():
   gp=(spec.metadata or {}).get('geometry_csv'); gm=GeometryMapper(gp) if gp else None
   out[k]={'geometry_csv':gp,'geometry_ok':bool(gm and gm.ok),'rows':int(len(gm.samples)) if gm else 0,'scan_range':[gm.scan_min,gm.scan_max] if gm and gm.ok else None,'pixel_range':[gm.pixel_min,gm.pixel_max] if gm and gm.ok else None,'latlon_bbox':list(gm.footprint_bbox) if gm and gm.ok else None,'fit_rms':gm.rms if gm and gm.ok else None,'footprint_method':gm.footprint_method if gm and gm.ok else None,'shapely_available':bool(getattr(__import__('app.geo.mapper',fromlist=['_HAS_SHAPELY']),'_HAS_SHAPELY',False))}
  pairs={}
  for a,b in [('OHRC','TMC2'),('OHRC','IIRS'),('TMC2','IIRS')]:
   ga=GeometryMapper(out[a]['geometry_csv']); gb=GeometryMapper(out[b]['geometry_csv']); pairs[f'{a}_{b}']={'bbox':ga.intersection_bbox(gb),'vertices':len(ga.intersection_polygon(gb)),'method':'sampled_swath_perimeter'}
  print(json.dumps({'status':'GEOMETRY_AUDIT_COMPLETE','products':out,'pair_intersections':pairs},indent=2,default=str)); return
 if args.cmd=='mission':
  root=Path(args.root); out=Path(args.out); e=Engine(); ids={'OHRC':'ch2_ohr_ncp_20260103t1005176450_d_img_d18.xml','TMC2':'ch2_tmc_ncf_20231101t1708581528_d_img_d18.xml','IIRS':'ch2_iir_nci_20210622t1850441449_d_img_d32.xml'}
  found={}
  for sensor,name in ids.items():
   hits=list(root.rglob(name));
   if not hits: raise FileNotFoundError(f'{sensor} label not found: {name}')
   found[sensor]=AdapterRegistry.inspect(hits[0])
  summary={'status':'COMPLETE','pairs':{},'project_verdict':'NOT_VALIDATED','products':{k:{'sensor':v.sensor,'product_id':v.product_id,'shape':v.array.shape,'dtype':str(v.array.dtype),'gsd_m':v.gsd_m} for k,v in found.items()}}
  pairs=[('OHRC_TMC2','OHRC','TMC2'),('OHRC_IIRS','OHRC','IIRS'),('TMC2_IIRS','TMC2','IIRS')]
  out.mkdir(parents=True,exist_ok=True)
  for name,a,b in pairs:
   print(f'[CHANDRABHAR-2] starting {name}: {a} <-> {b}',flush=True)
   try:
    res=e.register(found[a],found[b],name)
    e.save(res,out/f'{name}.json')
    summary['pairs'][name]={'status':res.diagnostics['status'],'matches':res.tentative_matches,'inliers':res.inliers,'inlier_ratio':res.inlier_ratio,'coverage':res.coverage,'rmse_px':res.rmse_px,'rmse_m':res.diagnostics.get('rmse_m'),'scale_cascade':res.diagnostics.get('scale_cascade')}
    print(f'[CHANDRABHAR-2] finished {name}: status={res.diagnostics["status"]} matches={res.tentative_matches} inliers={res.inliers} ratio={res.inlier_ratio:.3f}',flush=True)
   except Exception as exc:
    err={'status':'ERROR','error_type':type(exc).__name__,'error':str(exc)}
    (out/f'{name}.json').write_text(json.dumps(err,indent=2))
    summary['pairs'][name]=err
    print(f'[CHANDRABHAR-2] finished {name}: status=ERROR error={type(exc).__name__}: {exc}',flush=True)
  if all(v['status']=='VALIDATED' for v in summary['pairs'].values()): summary['project_verdict']='EVIDENCE_SUFFICIENT_FOR_THREE_SENSOR'
  else: summary['project_verdict']='NOT_VALIDATED'
  out.mkdir(parents=True,exist_ok=True); (out/'summary.json').write_text(json.dumps(summary,indent=2)); print(json.dumps(summary,indent=2)); return
 if args.cmd=='register':
  e=Engine(); a=AdapterRegistry.inspect(args.reference); b=AdapterRegistry.inspect(args.source); res=e.register(a,b,Path(args.out).stem); e.save(res,args.out); print(json.dumps({'status':res.diagnostics['status'],'matches':res.tentative_matches,'inliers':res.inliers,'ratio':res.inlier_ratio,'rmse_px':res.rmse_px,'coverage':res.coverage,'out':args.out},indent=2)); return
 if args.cmd=='self-test':
  from app.selftest import run; print(json.dumps(run(),indent=2));
if __name__=='__main__': main()
