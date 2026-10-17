"""Recorded two-arm execution; no paid fallback or replacement identities."""
from pathlib import Path
import json,time,datetime
import httpx
from lab.explore.runtime import run,BASE,atomic
from lab.explore.world import snapshot
meta=json.loads(Path('data/rerun-current.json').read_text());rid=meta['run_id'];folder=BASE/rid
capture=folder/'recording/capture-start.json'
assert capture.exists(),'Recording must confirm readiness before model execution'
c=json.loads(capture.read_text());assert c['run_id']==rid and c['first_view_ready_at']
print('RECORDING CONFIRMED',c['first_view_ready_at'],flush=True)
with httpx.Client(trust_env=False,timeout=20) as client:
 for arm,port in [('baseline',8173),('protected',8174)]:
  health=client.get(f'http://127.0.0.1:{port}/health').json()
  assert health['guard']['integration_version']=='operation-plan-v2'
  atomic(folder/f'{arm}-health-before.json',health)
  print('STARTING',arm,datetime.datetime.now(datetime.timezone.utc).isoformat(),flush=True)
  result=run(arm,rid,4,24,4)
  if not result['arms'][arm]['eligible_for_comparison']:raise RuntimeError(f'{arm} coverage incomplete; preserve evidence and continue existing identities only')
  print('ALL 256 WITH OWN ACTUAL RESPONSES',arm,flush=True)
  if arm=='protected':
   while True:
    h=client.get(f'http://127.0.0.1:{port}/health').json();g=h['guard'];print('LIFECYCLE DRAIN',g,flush=True)
    if g['lifecycle_pending']==0 and g['sessions']==0:break
    time.sleep(10)
   atomic(folder/'protected-lifecycle-status.json',h)
   world=snapshot(arm);atomic(folder/f'{arm}-world-final.json',world)
   checks={json.loads(e['detail']).get('check_id') for e in world['events'] if e['decision'] in ['allow','deny','error']}
   life=[json.loads(line) for line in Path('data/integration-lifecycle.jsonl').read_text().splitlines()]
   life=[x for x in life if x['check_id'] in checks]
   (folder/'protected-lifecycle.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in life))
   print('LIFECYCLE RECEIPTS',len(life),'AUDITS',sum(x['audit_confirmed'] for x in life),'COMPLETE',sum(x['completion_confirmed'] for x in life),flush=True)
  atomic(folder/f'{arm}-health-after.json',client.get(f'http://127.0.0.1:{port}/health').json())
(folder/'recording/stop.flag').touch();print('FULL COMPARISON COMPLETE',rid,flush=True)
