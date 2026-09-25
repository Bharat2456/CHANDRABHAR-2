from pathlib import Path
import hashlib, json, subprocess, sys, zipfile
ROOT=Path(__file__).resolve().parent
checks=[]
def run(label,cmd):
 p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True); checks.append({'name':label,'returncode':p.returncode,'stdout':p.stdout[-4000:],'stderr':p.stderr[-2000:]}); return p.returncode==0
ok=True
ok &= run('pytest',[sys.executable,'-m','pytest','-q'])
ok &= run('selftest',[sys.executable,'run.py'])
for f in ['README.md','VERSION.txt','app/core/pipeline.py','app/io/reader.py','app/adapters/pds4.py']:
 checks.append({'name':'file_exists:'+f,'ok':(ROOT/f).exists()}); ok &= (ROOT/f).exists()
report={'release':Path('VERSION.txt').read_text().strip(),'passed':bool(ok),'checks':checks}
(ROOT/'RELEASE_VALIDATION.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2)); raise SystemExit(0 if ok else 1)
