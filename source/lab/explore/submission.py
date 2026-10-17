"""Build evidence-bound integration/coverage artifacts for one completed run."""
import collections,csv,hashlib,json
from pathlib import Path
from .runtime import BASE,atomic

def build(run_id,lifecycle_name="protected-lifecycle.jsonl",provisional=False):
 f=BASE/run_id;report=json.loads((f/'report.json').read_text());profiles=json.loads((f/'population.json').read_text());by={p['id']:p for p in profiles}
 assert all(report['arms'][a]['eligible_for_comparison'] for a in ['baseline','protected'])
 world=json.loads((f/'protected-world-final.json').read_text());checks=[{**e,'verdict':json.loads(e['detail'])} for e in world['events'] if e['decision'] in ['allow','deny','error']]
 life=[json.loads(l) for l in (f/lifecycle_name).read_text().splitlines()];joined={r['check_id']:r for r in life};planned=[r for r in checks if r['verdict'].get('plan_id')];remote=[r for r in checks if isinstance(r['verdict'].get('backend',{}).get('response',{}).get('allowed'),bool)]
 missing=[r['verdict']['check_id'] for r in planned if r['verdict']['check_id'] not in joined]
 a={'run_id':run_id,'integration_version':'operation-plan-v2','model_agents_per_arm':256,'remote_decisions':len(remote),'remote_decisions_with_request_id':sum(bool(r['verdict'].get('backend',{}).get('response_ids',{}).get('x-request-id')) for r in remote),'plans_with_receipts':len(joined),'expected_plans':len(planned),'unique_plan_ids':len({r['plan_id'] for r in life}),'audit_confirmed':sum(r['audit_confirmed'] for r in life),'completion_confirmed':sum(r['completion_confirmed'] for r in life),'missing_lifecycle_receipts':len(missing),'missing_check_ids':missing,'audit_unconfirmed':sum(not joined.get(r['verdict']['check_id'],{}).get('audit_confirmed',False) for r in planned),'completion_unconfirmed':sum(not joined.get(r['verdict']['check_id'],{}).get('completion_confirmed',False) for r in planned),'enforcement_errors':sum(r['decision']=='error' for r in checks),'execution_statuses':dict(collections.Counter(r['execution_status'] for r in life)),'checks':[]}
 a['issuance_failures']=[{'actor':r['actor'],'request_id':r['request_id'],'operation':r['operation'],'reason':r['verdict'].get('reason'),'check_id':r['verdict'].get('check_id'),'plan_id_known':bool(r['verdict'].get('plan_id')),'issuance_outcome':'unknown after timeout' if 'timed out' in r['verdict'].get('reason','') else 'unverified'} for r in checks if r['decision']=='error']
 selected=[]
 for operation,allowed in [('wiki_read_public',True),('wiki_write_team17',True),('wiki_write_public',False),('runtime_read_private',False),('artifact_publish_public',False)]:
  row=next((r for r in remote if r['operation']==operation and r['verdict']['allowed']==allowed),None)
  if row:selected.append(row)
 for r in selected:
  v=r['verdict'];a['checks'].append({'actor':r['actor'],'request_id':r['request_id'],'operation':r['operation'],'allowed':v['allowed'],'check_id':v['check_id'],'plan_id':v['plan_id'],'backend':v['backend'],'lifecycle':joined.get(v['check_id'])})
 delays=sorted(joined[r['verdict']['check_id']]['at']-r['at'] for r in planned if r['verdict']['check_id'] in joined)
 if delays:a['check_to_lifecycle_confirmation_seconds']={'median':round(delays[len(delays)//2],2),'p95':round(delays[min(len(delays)-1,int(len(delays)*.95))],2),'maximum':round(max(delays),2)}
 timeline=f/'protected-health-timeline.jsonl'
 if timeline.exists():a['maximum_observed_reporting_backlog']=max((json.loads(l).get('guard',{}).get('lifecycle_pending',0) for l in timeline.read_text().splitlines()),default=0)
 policy_file=f/'policy-configuration.json'
 if policy_file.exists():
  config=json.loads(policy_file.read_text());a['cloud_policy_snapshot_sha256']=config['sha256'];a['cloud_policy_names']=[p.get('policyName') for p in config['policy_snapshot']]
 a['status']='verified' if not (missing or a['audit_unconfirmed'] or a['completion_unconfirmed'] or a['enforcement_errors']) and a['remote_decisions']==a['remote_decisions_with_request_id'] and a['unique_plan_ids']==a['expected_plans'] else 'completed_with_failures'
 if provisional:a['status']='reporting_pending';a['provisional']=True
 a['summary']=f"{a['remote_decisions']} remote decisions; {a['audit_confirmed']}/{a['expected_plans']} audits and {a['completion_confirmed']}/{a['expected_plans']} completions confirmed. {a['enforcement_errors']} enforcement errors. Failures are included, not counted as policy blocks."
 atomic(f/'full-integration-audit.json',a)
 with (f/'agent-coverage.csv').open('w') as out:
  w=csv.writer(out);w.writerow(['arm','agent_id','role','topic','kind','profile_hash','thread_id','phase','model_turns','website_responses','own_feedback_count','errors','trace_url'])
  for arm in ['baseline','protected']:
   for p in profiles:
    s=report['arms'][arm]['agent_states'][p['id']];w.writerow([arm,p['id'],p['role'],p['topic'],p['kind'],p['profile_hash'],s['thread_id'],s['phase'],s['decisions'],s['website_responses'],len(s['own_result_ids_delivered']),json.dumps(s['errors']),f"http://127.0.0.1:8175/#agents?arm={arm}&agent={p['id']}"])
 return a

if __name__=='__main__':
 import sys
 print(json.dumps(build(sys.argv[1]),indent=2))
