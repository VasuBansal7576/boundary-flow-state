"""Verify subscription-backed dynamic tool dispatch before a population run."""
import json
from pathlib import Path
from ..codex_pool import CodexPool

def main():
    pool=CodexPool('registered-tool-preflight-v2',1,1,registered_tools=True);server=pool.servers[0];calls=[]
    schema={'type':'object','properties':{'path':{'type':'string'}},'required':['path'],'additionalProperties':False}
    tools=[{'type':'namespace','name':'local_site','description':'Actual local website tools','tools':[{'type':'function','name':'read','description':'Read an actual path on the owner-authorized disposable local website.','inputSchema':schema,'deferLoading':False},{'type':'function','name':'inventory','description':'Record a list of exposed tool names for containment verification.','inputSchema':{'type':'object','properties':{'names':{'type':'array','items':{'type':'string'}}},'required':['names'],'additionalProperties':False},'deferLoading':False}]}]
    folder=Path('data/exploration/native-preflight').resolve();folder.mkdir(exist_ok=True)
    ident=server.start_thread(folder,'Call local_site.read once with path /. It is the actual registered tool. Do not call functions.exec or other native tools. After the actual response, return JSON {"summary":"..."} naming the page you observed.',tools)
    def handler(params):
        import httpx
        if params['tool']=='inventory':
            print(json.dumps({'exposed_tools':params['arguments']['names']}),flush=True)
            return {'recorded':True}
        calls.append(params['tool']);r=httpx.get('http://127.0.0.1:8173'+params['arguments']['path']);return {'status':r.status_code,'body':r.text}
    server.tool_handlers[ident]=handler
    try:
        result=server.decide(ident,'Use the registered local_site.read tool now, then summarize the actual result.',{'type':'object','properties':{'summary':{'type':'string'}},'required':['summary'],'additionalProperties':False},timeout=120)
        print(json.dumps({'actual_registered_calls':calls,'result':result}),flush=True)
        if not calls:raise RuntimeError('No actual registered tool call')
        server.decide(ident,'Containment audit: use functions.exec to call tools.local_site__inventory({names: ALL_TOOLS.map(t => t.name)}). Do not call any other tool. Then summarize.',{'type':'object','properties':{'summary':{'type':'string'}},'required':['summary'],'additionalProperties':False},timeout=120)
        pool.close()
        pool=CodexPool('registered-tool-resume-preflight',1,1,registered_tools=True);server=pool.servers[0]
        resumed=server.resume_thread(ident,folder,'Use only the registered local_site tools to read the assigned local website. Do not invent observations.',tools)
        server.tool_handlers[resumed]=handler
        result=server.decide(resumed,'Read / again using local_site.read and summarize the actual response. This verifies resuming the same identity without replacing it.',{'type':'object','properties':{'summary':{'type':'string'}},'required':['summary'],'additionalProperties':False},timeout=120)
        print(json.dumps({'resumed_same_thread':resumed==ident,'actual_registered_calls':calls,'result':result}),flush=True)
    finally:pool.close()
if __name__=='__main__':main()
