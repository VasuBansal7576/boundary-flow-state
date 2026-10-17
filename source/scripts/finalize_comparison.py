from pathlib import Path
import json,time,subprocess,sys
from lab.explore.runtime import BASE
from lab.explore.verify import verify
from lab.explore.compare import compare
from lab.explore.submission import build
rid=json.loads(Path('data/rerun-current.json').read_text())['run_id'];f=BASE/rid
while not (f/'protected-lifecycle.jsonl').exists():time.sleep(10)
for arm in ['baseline','protected']:verify(rid,arm)
comparison=compare(rid);audit=build(rid)
assert comparison['separate_fresh_model_threads'] and all(comparison['same_source'].values()) and comparison['initial_fixtures_identical']
assert all(v['included_credit_balance_unchanged'] for v in comparison['arms'].values()),'Credit balance changed; investigate before any zero-cost claim'
subprocess.run([sys.executable,'scripts/curate_submission_run.py',rid],check=True)
print('Evidence analysis completed. Curated semantic claims still require inspection.',flush=True)
