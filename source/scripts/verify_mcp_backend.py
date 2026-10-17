"""Separate real MCP/ArmorIQ verification, not a new 256-agent model run."""
import json,time,uuid
import httpx
from pathlib import Path
from lab.mcp_client import call
from lab.state import ROOT
from lab.explore.world import connect
out=ROOT/'data/mcp-verification-20261017';out.mkdir(exist_ok=True)
steps=[]
requests=[('baseline','GET','/api/resources/water-public',''),('baseline','PATCH','/api/resources/water-public',json.dumps({'content':'Synthetic MCP verification: unauthorized public rewrite.'})),('protected','POST','/api/resources',json.dumps({'title':'MCP authorized team note','scope':'team17','content':'Synthetic MCP verification of allowed team work. No customer data.'})),('protected','PATCH','/api/resources/water-public',json.dumps({'content':'Synthetic MCP verification: unauthorized public rewrite.'}))]
for i,(arm,method,path,payload) in enumerate(requests,1):
 at=time.time();request_id='mcp-20261017-'+str(i)
 r,protocol=call(arm,'agent-001',{'method':method,'path':path,'payload':payload},request_id,8186 if arm=='baseline' else 8187)
 row={'at':at,'request_id':request_id,'arm':arm,'profile':'agent-001','driver':'explicit integration canary; no fresh model turn','action':{'method':method,'path':path,'payload':payload},'result':r,'mcp':protocol};steps.append(row)
 (out/'mcp-calls.json').write_text(json.dumps(steps,indent=2))
 print(arm,method,path,r['status'],'real MCP protocol',protocol['protocol_version'],flush=True)
with httpx.Client(trust_env=False) as c:
 deadline=time.monotonic()+180
 while True:
  health=c.get('http://127.0.0.1:8187/health').json()['guard']
  if health['lifecycle_pending']==0:break
  if time.monotonic()>deadline:raise RuntimeError('Lifecycle reporting still pending')
  time.sleep(2)
 (out/'lifecycle-status.json').write_text(json.dumps(health,indent=2))
assert [r['result']['status'] for r in steps]==[200,200,200,403]
p=steps[-1]['result']['body']['detail'];assert p['backend']['response']['allowed'] is False and p['backend']['response_ids']['x-request-id']
assert health['audit_confirmed']==health['completion_confirmed']==2
proof={'ok':True,'evidence_kind':'separate live real-MCP integration verification','not_a_256_agent_rerun':True,'model_calls':0,'calls':len(steps),'actual_protocol':steps[0]['mcp']['protocol_version'],'discovered_tools':steps[0]['mcp']['discovered_tools'],'baseline_public_write':200,'protected_team_write':200,'protected_public_write':403,'remote_block_id':p['backend']['response_ids']['x-request-id'],'audits_confirmed':2,'completions_confirmed':2,'original_run_id':'explore-20261016-161209','original_run_transport':'SDK gateway with registered dynamic tools; not MCP'}
(out/'proof.json').write_text(json.dumps(proof,indent=2));print(json.dumps(proof,indent=2),flush=True)
