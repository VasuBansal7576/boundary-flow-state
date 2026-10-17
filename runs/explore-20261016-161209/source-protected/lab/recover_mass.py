"""Continue unfinished work in existing model threads after a free-backend cooldown."""
import collections,json,threading,time,shutil
from urllib.parse import urlsplit
from concurrent.futures import ThreadPoolExecutor
import httpx
from swarms.structs.concurrent_workflow import ConcurrentWorkflow
from .codex_pool import CodexPool
from .mass_swarm import Room,ConcurrentPeer,Activity,INSTRUCTIONS
from .state import DATA,snapshot
from .swarm import write_json


def recover(run_id,participants=8,extra_rounds=3):
    folder=DATA/'mass_runs'/run_id;report=json.loads((folder/'report.json').read_text())
    if report['phase']!='complete':raise RuntimeError('Only continue after the original run has stopped cleanly')
    write_json(folder/'initial-six-round-report.json',report)
    base_round=report['round'];new_budget=base_round+extra_rounds
    report['initial_completed_at']=report['completed_at'];report['round_budget']=new_budget
    report.setdefault('continuations',[]).append({'at':time.time(),'reason':'Recover only unfinished work after real429s; reuse original thread IDs, no replacement agents','remote_request_interval_seconds':.8})
    def save(phase,number):
        report.update(phase=phase,round=number)
        write_json(folder/'report.json',report);write_json(DATA/'active-mass.json',{'run_id':run_id,'phase':phase})
    rooms={};old_events={};selected={}
    for arm in ['baseline','protected']:
        room=Room(arm,run_id);rooms[arm]=room
        events=[json.loads(v) for v in (folder/f'{arm}.jsonl').read_text().splitlines()];old_events[arm]=events
        for e in events:
            if e['kind']=='work_claimed':room.board.reserve(e['peer'],e['proposal'],e['round'])
            elif e['kind']=='observation':
                room.records[e['id']]=e;room.board.observe(e)
                room.coverage[e['proposal']['method']+' '+urlsplit(e['proposal']['path']).path]+=1
                room.conversation.add(role=e['peer'],content=json.dumps(e))
        reopened=[];latest=0
        for key,c in room.board.claims.items():
            if c['status']!='exhausted':continue
            detail=c.get('response',{}).get('body',{})
            inner=detail.get('detail',{}) if isinstance(detail,dict) else {}
            backend=inner.get('backend',{}) if isinstance(inner,dict) else {}
            if c['status']=='exhausted' and backend.get('http_status')==429:
                prior=room.records[c['result_id']];latest=max(latest,prior['at']);reopened.append(key)
        # Never retry a policy denial, application rejection or completed effect.
        if latest and time.time()-latest<65:
            raise RuntimeError('The65second backend cooldown has not elapsed; wait before continuation')
        for key in reopened:
            c=room.board.claims[key];c['status']='retryable'
            room.log('retry_reopened_after_cooldown',work_key=key,prior_result_id=c['result_id'],reason='Only real backend429 failure; one paced recovery continuation')
        if latest and time.time()-latest<65:
            raise RuntimeError('The65second backend cooldown has not elapsed; wait before continuation')
        if not room.board.candidates(0):selected[arm]=[];continue
        owners=[room.board.claims[k]['peer'] for k in reopened]
        names=list(dict.fromkeys(owners+[p['peer'] for p in report['arms'][arm]['peers']]))[:participants]
        selected[arm]=names
    if not any(selected.values()):print('No unfinished work to recover');return report
    save('recovery_preparing',base_round)
    pool=CodexPool(run_id+'-recovery',2,8);activity=Activity();clients={};peers={};workflows={}
    try:
        report['continuations'][-1]['budget_before']=pool.servers[0].budget()
        for arm,names in selected.items():
            clients[arm]=httpx.Client(trust_env=False,follow_redirects=False,limits=httpx.Limits(max_connections=20,max_keepalive_connections=20))
            peers[arm]=[]
            lookup={p['peer']:p for p in report['arms'][arm]['peers']}
            for name in names:
                old=lookup[name];index=report['roster'][arm].index(name)
                peer=ConcurrentPeer(name,arm,index,pool,rooms[arm],clients[arm],activity,new_budget)
                peer.thread_id=peer.server.resume_thread(old['thread_id'],peer.worker.scratch,INSTRUCTIONS+'\nThis is an explicitly logged recovery continuation after backend rate-limit failures. Keep completed work closed. Select only currently available unfinished work and reuse actual peer evidence. Same identity and same permissions.')
                peer.errors=list(old['errors']);peer.requests=old['http_responses'];peer.worker.calls=old['http_responses'];peer.worker.max_calls=new_budget
                peer.decisions=old['model_decisions'];peer.model_turns=old.get('actual_model_turns',peer.decisions)
                peer.own_delivered=set(old['own_response_ids_delivered']);peer.claim_conflicts=old['claim_conflicts']
                for e in old_events[arm]:
                    if e.get('peer')==name and e['kind']=='thinking':peer.seen.update(e.get('visible_peer_ids',[]))
                rooms[arm].log('thread_resumed',peer=name,thread_id=peer.thread_id,reason='Continue same participant; no new model identity')
                peers[arm].append(peer)
            if names:workflows[arm]=ConcurrentWorkflow(agents=peers[arm],max_workers=len(names),autosave=False,auto_save=False,on_error='raise',output_type='dict')
        with ThreadPoolExecutor(max_workers=2) as outer:
            for number in range(base_round+1,new_budget+1):
                pool.check_limits()
                for phase in ['decide','execute']:
                    if phase=='decide':
                        for r in rooms.values():r.intentions.clear()
                    else:
                        barrier=threading.Barrier(sum(len(v) for v in peers.values()))
                        for group in peers.values():
                            for p in group:p.barrier=barrier
                    save('recovery_'+phase,number)
                    print(f'{run_id} recovery round{number}/{new_budget}: {phase}; original model threads only',flush=True)
                    for f in [outer.submit(w.run,f'{phase}:{number}') for w in workflows.values()]:f.result()
                if all(not r.board.candidates(0) for r in rooms.values()):break
        for arm,group in peers.items():
            lookup={p['peer']:p for p in report['arms'][arm]['peers']}
            for p in group:
                lookup[p.agent_name].update(model_decisions=p.decisions,http_responses=p.requests,errors=p.errors,finished=p.finished,actual_model_turns=p.model_turns,own_response_ids_delivered=sorted(p.own_delivered),claim_conflicts=p.claim_conflicts)
            report['arms'][arm]['state']=snapshot(arm)
        report['budget_after']=pool.servers[0].budget();report['continuations'][-1]['budget_after']=report['budget_after']
        report['completed_at']=time.time();report['backend_request_pacing_seconds']=.8
        save('complete',number);print(run_id+': recovery complete',flush=True)
        return report
    except BaseException as e:
        report['error']=type(e).__name__+': '+str(e);save('failed',report.get('round',base_round));raise
    finally:
        pool.close()
        for c in clients.values():c.close()

if __name__=='__main__':
    import sys
    recover(sys.argv[1])
