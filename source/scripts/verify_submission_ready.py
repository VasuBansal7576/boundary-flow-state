"""Validate evidence identity, execution mediation, capture coverage and delivery."""
from pathlib import Path
import json,hashlib,csv,datetime,subprocess,collections
from lab.explore.runtime import BASE,atomic
from lab.explore.population import digest
from lab.explore.product import dossier,is_exposure
root=Path(__file__).resolve().parent.parent;rid=json.loads((root/'data/rerun-current.json').read_text())['run_id'];f=BASE/rid;report=json.loads((f/'report.json').read_text());profiles=json.loads((f/'population.json').read_text());assert len(profiles)==len({p['profile_hash'] for p in profiles})==len({p['objective'] for p in profiles})==256;assert digest(profiles)==report['population_hash'];checks={'distinct_frozen_profiles':256};allthreads=set();bookends=[];failure_counts={};recorded={}
for arm in ['baseline','protected']:
 a=report['arms'][arm];assert a['phase']=='complete' and a['eligible_for_comparison'];rows=[json.loads(l) for l in (f/f'{arm}.jsonl').read_text().splitlines()];recorded[arm]=rows;web={(r['peer'],r['step']):r for r in rows if r['kind']=='web_result'};fallback=[r for r in rows if r['kind']=='observation' and r['result'].get('status',0)==0 and (r['peer'],r['step']) not in web];web.update({(r['peer'],r['step']):r for r in fallback});dec={(r['peer'],r['step']):r for r in rows if r['kind']=='decision'};world=json.loads((f/f'{arm}-world-final.json').read_text());threads={r['thread_id'] for r in rows if r['kind']=='agent_started'};assert len(threads)==256 and not allthreads&threads;allthreads|=threads
 actual=lambda r:any(n.get('status',0)>0 for n in r.get('network',[])) if r.get('tool')=='chromium' else r.get('status',0)>0
 actual_peers={r['peer'] for r in web.values() if actual(r['result'])};assert len(actual_peers)==256
 obs={r['id']:r for r in rows if r['kind']=='observation'};feedback={r['peer'] for r in rows if r['kind']=='tool_response_delivered' and r.get('observation_id') in obs and actual(web[(obs[r['observation_id']]['peer'],obs[r['observation_id']]['step'])]['result'])};assert len(feedback)==256
 for e in world['events']:
  assert e['request_id'],'Non-population request contaminated world events'
  peer=e['actor'].removeprefix(arm+'-');step=int(e['request_id'].split('-')[-1]);d=dec[(peer,step)];w=web[(peer,step)];assert d['at']<=e['at']<=w['at']+.1,(arm,e['id'],'effect outside its original request window')
  if arm=='protected' and e['decision']=='executed':assert any(q['request_id']==e['request_id'] and q['operation']==e['operation'] and q['decision']=='allow' and q['at']<=e['at'] for q in world['events'])
 failure_counts[arm]={k:sum(r['kind']==k for r in rows) for k in ['agent_error','web_error','invalid_reference','claim_conflict','tool_budget_reached','coverage_continuation']}
 (f/f'{arm}-failure-ledger.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows if r['kind'] in failure_counts[arm] or (r['kind']=='observation' and r['result'].get('status',0)==0) or (r['kind']=='web_result' and r['result'].get('status',0)>=400)))
 finished={r['peer']:r['at'] for r in rows if r['kind']=='agent_finished'}
 delivered={r.get('observation_id') for r in rows if r['kind']=='tool_response_delivered'}
 positive={r['id'] for r in obs.values() if actual(web[(r['peer'],r['step'])]['result'])};assert positive<=delivered,'A real returned website response was not delivered'
 late=[{'observation_id':r['id'],'peer':r['peer'],'step':r['step'],'status':r['result'].get('status'),'seconds_after_model_finish':round(r['at']-finished[r['peer']],2),'delivered':r['id'] in delivered,'error':r['result'].get('error')} for r in obs.values() if r['at']>finished[r['peer']]]
 atomic(f/f'{arm}-controller-finalization.json',{'late_observations':late,'model_completion_report_counter_snapshot':a['counts'],'settled_event_counts':dict(collections.Counter(r['kind'] for r in rows)),'all_actual_returned_site_responses_delivered':True})
 checks[arm]={'unique_model_threads':len(threads),'profiles_with_actual_site_responses':len(actual_peers),'profiles_with_delivered_actual_site_feedback':len(feedback),'failure_events':failure_counts[arm]}
 bookends += [r['at'] for r in rows if r['kind'] in ['agent_started','agent_finished']]
import sys
if '--model-evidence-only' in sys.argv:
 print(json.dumps(checks,indent=2));raise SystemExit(0)
comparison=json.loads((f/'comparison.json').read_text());assert comparison['initial_fixtures_identical'] and comparison['separate_fresh_model_threads'] and all(comparison['same_source'].values());assert all(a['included_credit_balance_unchanged'] for a in comparison['arms'].values());checks['included_credit_balance_unchanged']=True
assert len(list(csv.DictReader((f/'agent-coverage.csv').open())))==512
capture=json.loads((f/'recording/capture-manifest.json').read_text());stamp=lambda s:datetime.datetime.fromisoformat(s.replace('Z','+00:00')).timestamp();assert stamp(capture['first_view_ready_at'])<min(bookends) and stamp(capture['last_frame_at'])>max(bookends);assert capture['errors']==[];life=[json.loads(l) for l in (f/'protected-lifecycle.jsonl').read_text().splitlines()];assert stamp(capture['last_frame_at'])>=max(r['at'] for r in life);checks['continuous_recording_covers_both_arms_and_lifecycle_drain']=True
raw=f/'recording/actual-full-run.webm';raw_meta=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-show_format','-show_streams','-of','json',str(raw)]));assert raw.stat().st_size>1_000_000;elapsed=stamp(capture['last_frame_at'])-stamp(capture['recording_page_created_at']);assert abs(float(raw_meta['format']['duration'])-elapsed)<7;atomic(f/'recording/ffprobe.json',raw_meta);checks['recording_duration_seconds']=float(raw_meta['format']['duration'])
product=dossier(f);worlds={a:json.loads((f/f'{a}-world-final.json').read_text()) for a in recorded}
for c in product['cases']:
 original=next(r for r in recorded[c['arm']] if r['event_id']==c['event']['event_id']);assert original==c['event']
for arm in recorded:
 world=worlds[arm];history={(h['resource'],h['revision']):h['content'] for h in world['history']};events={e['id']:e for e in world['events']};web={e['event_id']:e for e in recorded[arm] if e['kind']=='web_result'}
 for p in product['arms'][arm]['exposures']:
  m=events[p['mutation_event_id']];assert is_exposure(web[p['consumer_event_id']],m,json.loads(m['detail']),history)
story=json.loads((root/'launch/exploration-vc90/proof/submission-story.json').read_text());assert story['run_id']==rid and story['handoff']['identifier_verified_in_delivered_peer_material'] and not story['handoff']['identifier_in_prior_own_responses'];assert story['plant']['quote'] in story['plant']['full_content'];checks['curated_cases_and_all_exposure_pairs_match_original_events']=True
movie=root/'launch/exploration-vc90/renders/boundary-fixed-256-vc90.mp4';export=json.loads((root/'launch/exploration-vc90/proof/submission-export-check.json').read_text());assert export['ok'] and export['duration']==90 and export['frames']==2700;checks['movie']=export
for htmlfile in (root/'launch/exploration-vc90/compositions').rglob('*.html'):
 if htmlfile.parent.name not in ['frames','compositions']:continue
 if htmlfile.name not in ['rail.html','captions.html'] and htmlfile.parent.name!='frames':continue
 assert 'explore-20261016-134306' not in htmlfile.read_text() and 'manifest-v1' not in htmlfile.read_text()
audit=json.loads((f/'full-integration-audit.json').read_text());assert not audit.get('provisional');assert json.loads((f/'protected-lifecycle-status.json').read_text())['guard']['lifecycle_pending']==0;checks['integration']=audit;checks['status']='ready_with_disclosed_failures' if any(v['local_tool_or_transport_failures'] or v.get('agent_execution_errors') for v in comparison['arms'].values()) or audit['status']!='verified' else 'ready';checks['limitations']=['Controlled synthetic sites; explicit profiles and common team17 grant.','Adaptive arms differ; no matched-request efficacy percentage.','Exposures, conflicts and missing-resource incidents are not final task-failure counts.','Cloud policy controls operation categories, not malicious meaning.','Published event materials did not expose the exact submission form or closing hour.'];atomic(f/'submission-readiness.json',checks);print(json.dumps({k:v for k,v in checks.items() if k!='integration'},indent=2))
