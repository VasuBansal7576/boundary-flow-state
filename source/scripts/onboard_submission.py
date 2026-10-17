"""Real supported control-plane registration; does not claim a new swarm run.

Uses the already-authorized lab key. No new credential, deployment, policy
allowance, or paid API is requested. Policies are intentionally omitted so the
existing organization operation policy remains the source of authorization.
"""
import argparse, json, time, threading, concurrent.futures
from pathlib import Path
import httpx
from armoriq_sdk.cli import CONTROL_PLANE_REGISTER_ENDPOINT
from lab.guard import api_key, LAB_USER
from lab.state import ROOT

p=argparse.ArgumentParser();p.add_argument('--all',action='store_true');a=p.parse_args()
folder=ROOT/'data/submission-onboarding-20261017';folder.mkdir(exist_ok=True)
records=folder/'registrations.jsonl'
previous=[json.loads(s) for s in records.read_text().splitlines()] if records.exists() else []
completed={r['agent_id'] for r in previous if r['ok']}
identities=[f'boundary-{arm}-agent-{i:03}' for arm in ['baseline','protected'] for i in range(1,257)] if a.all else ['boundary-protected-agent-001']
lock=threading.Lock()
def register(agent):
 if agent in completed:return
 with httpx.Client(timeout=30,trust_env=False) as client:
  payload={'version':'v1','identity':{'api_key':'$ARMORIQ_API_KEY','user_id':LAB_USER,'agent_id':agent},'environment':'sandbox','mcp_servers':[]}
  r=client.post(CONTROL_PLANE_REGISTER_ENDPOINT,headers={'Authorization':'Bearer '+api_key()},json=payload)
  try:body=r.json()
  except ValueError:body={}
  # Retain only inventory metadata; never response credentials/certificates.
  safe={k:body[k] for k in ['agent_id','agentId','registered_at','environment','status','message','mcp_servers','registered_mcp_servers'] if k in body}
  row={'at':time.time(),'agent_id':agent,'http_status':r.status_code,'ok':r.is_success,'response':safe,'purpose':'inventory onboarding after recorded SDK run','new_model_execution':False,'policy_payload_omitted':True}
  with lock:
   with records.open('a') as f:f.write(json.dumps(row)+'\n')
  print(agent,r.status_code,'registered' if row['ok'] else 'not registered',flush=True)
  if not row['ok']:
   print('Safe error detail',json.dumps({k:body[k] for k in ['error','detail','message'] if k in body})[:800],flush=True)
   raise SystemExit(1)
  time.sleep(.2)

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
 list(executor.map(register, identities))
