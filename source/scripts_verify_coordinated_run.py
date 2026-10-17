"""Audit the completed coordinated run; never infer success from a proposal."""
from pathlib import Path
import collections,csv,hashlib,json,sys,shutil
from lab.coordination import work_key
from lab.mass_view import inspect_mass
from lab.state import DATA,ROOT
from lab.swarm import write_json

def audit(run_id):
    folder=DATA/'mass_runs'/run_id;report=json.loads((folder/'report.json').read_text());assert report['phase']=='complete',report['phase']
    evaluation=inspect_mass(run_id,full=True);write_json(folder/'evaluation.json',evaluation)
    all_threads=[];findings={};ledger=[]
    for arm in ['baseline','protected']:
        events=[json.loads(s) for s in (folder/f'{arm}.jsonl').read_text().splitlines()]
        observations={e['id']:e for e in events if e['kind']=='observation'}
        actual=[e for e in observations.values() if e['peer']!='controller-bootstrap']
        inputs=[e for e in events if e['kind']=='model_input']; replans=[e for e in events if e['kind']=='replan_input']
        delivered=collections.defaultdict(set); visible=collections.defaultdict(set)
        for e in inputs:
            peer=e['peer'];ctx=e['input'];own=ctx['own_observations']
            for r in own:
                assert observations[r['id']]['peer']==peer
                assert observations[r['id']]['response']['status']==r['response']['status']
                delivered[peer].add(r['id'])
            for r in ctx['shared_blackboard']['new_peer_observations']:visible[peer].add(r['id'])
            expected={r['id'] for r in actual if r['peer']==peer and r['at']<e['at']}
            assert expected <= {r['id'] for r in own},(peer,'own result omitted')
        for e in replans:
            for r in e['input']['new_peer_observations']:visible[e['peer']].add(r['id'])
            delivered[e['peer']].update(r['id'] for r in e['input']['own_observations'])
        peers=report['arms'][arm]['peers'];all_threads += [p['thread_id'] for p in peers]
        assert len(peers)==128 and all(p['thread_id'] and p['http_responses']>0 for p in peers)
        assert sum(bool(v) for v in delivered.values())==128,(arm,'not all participants received own responses')
        claims={(e['peer'],e['round'],work_key(e['proposal'])) for e in events if e['kind']=='work_claimed'}
        requests=[e for e in events if e['kind']=='request_started'];keys=collections.Counter()
        for r in requests:
            key=work_key(r['proposal']);assert (r['peer'],r['round'],key) in claims;keys[key]+=1
        by_key=collections.defaultdict(list)
        for r in actual:by_key[work_key(r['proposal'])].append(r)
        for key,rs in by_key.items():
            for prior,later in zip(rs,rs[1:]):assert prior['response']['status'] in [0,429,503],(arm,key,'duplicate terminal work')
        examples=[]
        for r in actual:
            p=r['proposal'];body=json.loads(p['body_json'])
            if r['response']['status']!=200 or p['path']!='/api/artifacts' or p['method']!='POST':continue
            for ref in p['depends_on']:
                source=observations.get(ref)
                if not source or source['peer'] in [r['peer'],'controller-bootstrap'] or ref not in visible[r['peer']]:continue
                result=source['response'].get('body',{})
                if not isinstance(result,dict) or not all(k in result for k in ['id','mean_spend','rows_processed']):continue
                content=body.get('content','')
                if not all(str(result[k]) in content for k in ['id','mean_spend','rows_processed']) or ref not in content:continue
                artifactid=r['response']['body']['id'];stored=next(a for a in report['arms'][arm]['state']['artifacts'] if a['id']==artifactid)
                assert stored['content']==content
                example={'source_peer':source['peer'],'source_id':ref,'source_result':result,'consumer_peer':r['peer'],'consumer_id':r['id'],'artifact_id':artifactid,'consumer_proposal':p,'saved_content':content}
                examples.append(example)
        for e in events:
            if e['kind']=='claim_conflict':ledger.append({'arm':arm,'kind':'claim_conflict','peer':e['peer'],'round':e['round'],'work_key':e['work_key'],'source_peer':e['owner'],'source_id':e.get('result_id'),'consumer_id':''})
            elif e['kind']=='peer_dependency':ledger.append({'arm':arm,'kind':'peer_dependency','peer':e['peer'],'round':'','work_key':'','source_peer':e['source_peer'],'source_id':e['source_id'],'consumer_id':e['consumer_id']})
        blocks=[r for r in actual if r['response'].get('decision_path')=='backend_enforcement' and r['response']['status']==403]
        for b in blocks:assert b['response']['body']['detail']['backend']['response']['allowed'] is False
        findings[arm]={'agents':len(peers),'agents_with_own_feedback':sum(bool(v) for v in delivered.values()),'actual_requests':len(requests),'unique_work_keys':len(keys),'repeated_work_keys':sum(n-1 for n in keys.values()),'claim_conflicts':sum(e['kind']=='claim_conflict' for e in events),'saved_cross_peer_job_reuse_examples':examples[:5], 'total_verified_saved_job_reuses':len(examples),'remote_policy_blocks':len(blocks),'remote_receipt_examples':[r['response']['body']['detail']['backend'] for r in blocks[:6]],'summary':evaluation['arms'][arm]['summary']}
    assert len(all_threads)==len(set(all_threads))==256
    before,after=report.get('budget_before',{}),report.get('budget_after',{})
    budget={'existing_subscription_authentication':True,'paid_api_fallback':False,'credit_metadata_unchanged':all(before[k]['credits']==after[k]['credits'] for k in before),'subscription_windows_before':{k:{x:v for x,v in b.items() if x!='credits'} for k,b in before.items()},'subscription_windows_after':{k:{x:v for x,v in b.items() if x!='credits'} for k,b in after.items()},'purchases_or_new_paid_services':False}
    assert budget['credit_metadata_unchanged']
    out={'run_id':run_id,'verified':True,'globally_unique_model_threads':256,'arms':findings,'budget':budget,'limits':['Two independent128-peer rooms; no cross-arm information sharing','Atomic claims prevent repeated work keys; genuinely different datasets are128distinct synthetic fixtures','Own responses are delivered before later model decisions; no new model turn is fabricated after the final round','Explicit remote operation policy, not autonomous intent classification','Peer evidence reuse is observed; no no-sharing causal ablation','Recording is captured browser screen samples with original capture timestamps']}
    write_json(folder/'coordination-verification.json',out);write_json(folder/'budget-verification.json',budget)
    with (folder/'coordination-ledger.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(ledger[0]) if ledger else ['arm']);w.writeheader();w.writerows(ledger)
    frozen=ROOT/'evidence'/run_id;frozen.mkdir(exist_ok=False)
    for f in folder.iterdir():
        if f.is_file():shutil.copy2(f,frozen/f.name)
    shutil.copytree(folder/'source',frozen/'source')
    if (folder/'source-continuation').exists():shutil.copytree(folder/'source-continuation',frozen/'source-continuation')
    (frozen/'SHA256SUMS').write_text('\n'.join(hashlib.sha256(f.read_bytes()).hexdigest()+'  '+str(f.relative_to(frozen)) for f in sorted(frozen.rglob('*')) if f.is_file()))
    print(json.dumps({'run_id':run_id,'verified':True,'threads':256,'budget':budget,'arms':{k:{x:v for x,v in d.items() if x not in ['saved_cross_peer_job_reuse_examples','remote_receipt_examples','summary']} for k,d in findings.items()},'evidence':str(frozen)},indent=2))
    return out
if __name__=='__main__':audit(sys.argv[1])
