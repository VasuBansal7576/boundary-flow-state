import json,time,hashlib,shutil
from pathlib import Path
rid=json.loads(Path('data/rerun-current.json').read_text())['run_id'];f=Path('data/exploration')/rid
while 'protected' not in json.loads((f/'report.json').read_text())['arms']:time.sleep(1)
expected=json.loads((f/'source-sha256.json').read_text());actual={}
for name,h in expected.items():
 p=Path(name);actual[name]=hashlib.sha256(p.read_bytes()).hexdigest()
 if name in ['lab/guard.py','lab/explore/world.py','lab/explore/runtime.py','lab/explore/population.py','lab/explore/browser.cjs','lab/codex_pool.py']:assert actual[name]==h,(name,'changed between arms')
 dest=f/'source-protected'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
(f/'source-protected-sha256.json').write_text(json.dumps(actual,indent=2));print('Protected runtime, gateway, population and browser source match baseline snapshot',flush=True)
