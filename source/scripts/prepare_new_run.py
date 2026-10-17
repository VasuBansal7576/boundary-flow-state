"""Prepare a fresh dataset after local servers are started; never replace a run."""
from pathlib import Path
import time,json,hashlib,shutil
from lab.explore.population import population,digest
from lab.explore.world import seed
p=Path(__file__).resolve().parent.parent;base=p/'data/exploration';base.mkdir(parents=True,exist_ok=True)
if (base/'active.json').exists():
 active=json.loads((base/'active.json').read_text());r=base/active['run_id']/'report.json'
 if r.exists() and any(a.get('phase') in ['running','preparing','continuing_incomplete_participants'] for a in json.loads(r.read_text()).get('arms',{}).values()):raise SystemExit('An experiment is still active. Finish it before resetting these disposable websites.')
rid='explore-'+time.strftime('%Y%m%d-%H%M%S');f=base/rid;f.mkdir();files=list((p/'lab').rglob('*.py'))+list((p/'lab/explore').glob('*.cjs'))+[p/'requirements.txt',p/'package.json',p/'package-lock.json',p/'web/product/live-run.html',p/'scripts/record_live_run.cjs'];manifest={}
for src in files:
 if src.exists():
  rel=src.relative_to(p);dest=f/'source'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest);manifest[str(rel)]=hashlib.sha256(src.read_bytes()).hexdigest()
(f/'source-sha256.json').write_text(json.dumps(manifest,indent=2));profiles=population();(f/'population.json').write_text(json.dumps(profiles));(f/'report.json').write_text(json.dumps({'run_id':rid,'created_at':time.time(),'population_hash':digest(profiles),'profiles':256,'arms':{}}));(p/'data/rerun-current.json').write_text(json.dumps({'run_id':rid,'integration_version':'operation-plan-v2','steps':4,'model_slots':24,'recording_required':True}));(base/'active.json').write_text(json.dumps({'run_id':rid,'arm':'baseline'}));seed('baseline',True);seed('protected',True);print('Prepared',rid);print('Start scripts/record_live_run.cjs; wait for RECORDING READY, then run scripts/run_full_comparison.py. Start scripts/watch_protected_source.py before the protected arm begins.')
