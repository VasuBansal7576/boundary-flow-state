"""Read-only live evidence browser. It never supplies agent decisions."""
import json
import os
import re
import threading
from pathlib import Path
from fastapi import FastAPI,HTTPException,Request
from fastapi.responses import HTMLResponse,FileResponse,RedirectResponse
from fastapi.staticfiles import StaticFiles
from ..state import ROOT
from .runtime import BASE
from .world import snapshot

app=FastAPI(title='Boundary exploration live proof')
app.mount('/assets',StaticFiles(directory=ROOT/'web/product'),name='product-assets')
cache={};lock=threading.RLock()
def read_events(folder,arm):
    file=folder/f'{arm}.jsonl'
    if not file.exists():return []
    key=str(file)
    with lock:
        data=cache.setdefault(key,{'offset':0,'events':[]})
        with file.open() as f:
            f.seek(data['offset'])
            while True:
                pos=f.tell();line=f.readline()
                if not line:break
                try:row=json.loads(line)
                except ValueError:f.seek(pos);break
                data['events'].append(row)
            data['offset']=f.tell()
        return data['events']
def folder_for(run_id):
    if not re.fullmatch(r'explore-\d{8}-\d{6}',run_id):raise HTTPException(400,'Invalid run ID')
    folder=BASE/run_id
    if not folder.exists():raise HTTPException(404,'Run not found')
    return folder
@app.get('/',response_class=HTMLResponse)
def home(request:Request):
    if request.query_params.get('run_id') or request.query_params.get('agent'):
        return RedirectResponse('/inspect?'+str(request.query_params))
    return HTMLResponse((ROOT/'web/product/index.html').read_text())
@app.get('/live-run',response_class=HTMLResponse)
def live_run():return HTMLResponse((ROOT/'web/product/live-run.html').read_text())
@app.get('/inspect',response_class=HTMLResponse)
def inspect_original():return (ROOT/'web/explore/live.html').read_text()
def published():
    f=Path(os.environ.get('BOUNDARY_EXPERIMENT_MANIFEST',str(ROOT/'data/published-experiment.json')))
    return json.loads(f.read_text()) if f.exists() else {'run_id':'explore-20261016-134306'}
@app.get('/api/experiment')
def experiment(run_id:str|None=None):
    run_id=run_id or published()['run_id']
    from .product import dossier
    result=dict(dossier(folder_for(run_id)))
    proof=ROOT/'data/integration-audit.json'
    result['integration_audit']=json.loads(proof.read_text()) if proof.exists() else {'status':'checking','historical_run_revalidated':False}
    return result
@app.get('/film')
def film():
    folder=ROOT/'launch/exploration-vc90/renders'
    revised=folder/published().get('film','boundary-product-demo-90s.mp4')
    return FileResponse(revised if revised.exists() else folder/'boundary-256-vc-pitch-90s.mp4',media_type='video/mp4')
@app.get('/recording')
def continuous_recording():return FileResponse(folder_for(published()['run_id'])/'recording/actual-full-run.webm',media_type='video/webm',filename='boundary-actual-full-run.webm')
@app.get('/integration-audit.json')
def integration_receipts():return FileResponse(ROOT/'data/integration-audit.json',media_type='application/json')
@app.get('/proof/{name}')
def proof_download(name:str,run_id:str|None=None):
    allowed={'comparison.json','population.json','agent-coverage.csv','baseline-coordination-proof.json','protected-coordination-proof.json','evidence-sha256.json','baseline.jsonl','protected.jsonl','full-integration-audit.json','protected-lifecycle.jsonl','source-sha256.json','submission-readiness.json'}
    if name not in allowed:raise HTTPException(404,'Unknown evidence file')
    return FileResponse(folder_for(run_id or published()['run_id'])/name,filename=name)
@app.get('/api/live')
def live(run_id:str|None=None,arm:str|None=None):
    active=json.loads((BASE/'active.json').read_text()) if (BASE/'active.json').exists() else {}
    run_id=run_id or active.get('run_id')
    if not run_id:return {'waiting':True}
    folder=folder_for(run_id);report=json.loads((folder/'report.json').read_text());arm=arm or active.get('arm','baseline')
    if arm not in ['baseline','protected']:raise HTTPException(400,'Unknown arm')
    rows=read_events(folder,arm);profiles=json.loads((folder/'population.json').read_text())
    decisions={};observations={};deliveries={};started=set();errors=[];states=report['arms'].get(arm,{}).get('agent_states',{})
    for r in rows:
        peer=r.get('peer')
        if r['kind']=='agent_started':started.add(peer)
        if r['kind']=='decision':decisions[peer]=r
        if r['kind']=='observation':observations[peer]=r
        if r['kind']=='message_delivered' and r['message_ids']:deliveries[peer]=r
        if r['kind'] in ['agent_error','web_error','subscription_paused']:errors.append(r)
    final_state=folder/f'{arm}-world-final.json'
    ws=json.loads(final_state.read_text()) if report['arms'].get(arm,{}).get('phase')=='complete' and final_state.exists() else snapshot(arm)
    effects=ws['events']
    msgs=[r for r in rows if r['kind']=='message_sent']
    citations=[r for r in rows if r['kind']=='dependency_cited']
    profiles=[{**p,'state':states.get(p['id'],{}),'decision':decisions.get(p['id']),'observation':observations.get(p['id']),'delivery':deliveries.get(p['id'])} for p in profiles]
    proof_file=folder/f'{arm}-coordination-proof.json'
    proof=json.loads(proof_file.read_text()) if proof_file.exists() else {}
    handoffs=[]
    for chain in (proof.get('strongest_chains',[])+proof.get('strongest_observation_chains',[])):
        result=chain.get('actual_response') or {}
        handoffs.append({k:chain.get(k) for k in ['producer','consumer','message_id','source_observation_id','source_observation_ids','message','value_reuse','action']}|{'status':result.get('status')})
    return {'run_id':run_id,'arm':arm,'handoffs':handoffs[:8],'report':{k:v for k,v in report.items() if k!='arms'},'arm_report':{k:v for k,v in report['arms'].get(arm,{}).items() if k!='agent_states'},
            'profiles':profiles,'summary':{'started':len(started),'responded':len({r['peer'] for r in rows if r['kind']=='observation' and r['result'].get('status',0)>0}),'decisions':sum(r['kind']=='decision' for r in rows),
            'messages':len(msgs),'delivered':sum(len(r['message_ids']) for r in rows if r['kind']=='message_delivered'),
            'cited_peer_messages':sum(r['source_id'].startswith('msg-') and not r['source_id'].startswith('msg-'+r['peer']+'-') for r in citations),
            'outside_grant_effects':sum(r['outside_grant'] and r['decision']=='executed' for r in effects),'backend_denials':sum(r['decision']=='deny' for r in effects),
            'infrastructure_errors':sum(r['decision']=='error' for r in effects),'http_methods':sorted({r['action']['method'] for r in rows if r['kind']=='web_result' and r['action']['tool']=='http'}),
            'browser_actions':sum(r['kind']=='web_result' and r['action']['tool']!='http' for r in rows)},
            'feed':[{k:v for k,v in r.items() if k!='input'} for r in rows if r['kind'] in ['message_sent','dependency_cited','web_result','claim_conflict','agent_error']][-45:],
            'recent_effects':effects[-30:],'backend_denials':[e for e in effects if e['decision']=='deny'][-8:],'errors':errors[-10:]}
@app.get('/api/agent')
def agent(run_id:str,arm:str,peer:str):
    if arm not in ['baseline','protected'] or not re.fullmatch(r'agent-\d{3}',peer):raise HTTPException(400,'Invalid selection')
    rows=read_events(folder_for(run_id),arm);own=[r for r in rows if r.get('peer')==peer]
    inputs=[r for r in own if r['kind'] in ['model_input','tool_feedback']]
    cited={r['source_id'] for r in own if r['kind']=='dependency_cited'}
    sources=[r for r in rows if r.get('id') in cited and r['kind'] in ['message_sent','observation']]
    return {'events':own,'sources':sources,'latest_input':inputs[-1] if inputs else None}
if __name__=='__main__':
    import uvicorn
    uvicorn.run(app,host='127.0.0.1',port=8175,log_level='warning')
