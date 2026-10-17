from pathlib import Path
import json,time,httpx
rid=json.loads(Path('data/rerun-current.json').read_text())['run_id'];f=Path('data/exploration')/rid
with httpx.Client(trust_env=False,timeout=20) as client:
 while True:
  try:
   h=client.get('http://127.0.0.1:8174/health').json();row={'at':time.time(),**h}
   with (f/'protected-health-timeline.jsonl').open('a') as out:out.write(json.dumps(row)+'\n')
   if (f/'protected-lifecycle.jsonl').exists() and h['guard']['lifecycle_pending']==0:break
  except Exception as e:
   with (f/'protected-health-timeline.jsonl').open('a') as out:out.write(json.dumps({'at':time.time(),'error':str(e)})+'\n')
  time.sleep(15)
