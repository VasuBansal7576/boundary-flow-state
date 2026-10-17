"""Export the completed recorded experiment for zero-backend review; no publishing."""
import json,shutil,hashlib,sys,re
from pathlib import Path
from lab.explore.runtime import BASE
from lab.explore.product import dossier
root=Path(__file__).resolve().parent.parent;pub=json.loads((root/'data/published-experiment.json').read_text());rid=pub['run_id'];f=BASE/rid;out=root/'submission/boundary-replay';out.mkdir(parents=True,exist_ok=True)
for name in ['assets','data/agents/baseline','data/agents/protected','proof','media']:(out/name).mkdir(parents=True,exist_ok=True)
web=root/'web/product'
for name in ['style.css','app.js','film-poster.png','agent-profiles.html','agent-profiles.csv']:shutil.copy2(web/name,out/'assets'/name)
shutil.copytree(web/'fonts',out/'assets/fonts',dirs_exist_ok=True)
s=(web/'index.html').read_text().replace('src="/assets/','src="assets/').replace('href="/assets/','href="assets/').replace('href="/proof/','href="proof/').replace('src="/film"','src="media/boundary-judging-film.mp4"').replace('href="/film"','href="media/boundary-judging-film.mp4"')
(out/'index.html').write_text(s)
s=(out/'assets/app.js').read_text().replace("fetch('/api/experiment')","fetch('data/experiment.json')").replace('fetch(`/api/agent?run_id=${experiment.run_id}&arm=${arm}&peer=${peer}`)','fetch(`data/agents/${arm}/${peer}.json`)').replace('href="/recording"','href="media/actual-full-run.webm"').replace('href="/proof/','href="proof/')
assert '/api/agent?' not in s and "fetch('/api/experiment')" not in s
(out/'assets/app.js').write_text(s)
d=dossier(f);d['integration_audit']={};(out/'data/experiment.json').write_text(json.dumps(d))
for source_name,dest_name in [('proof.json','mcp-verification.json'),('mcp-calls.json','mcp-calls.json'),('lifecycle-status.json','mcp-lifecycle.json')]:
 shutil.copy2(root/'data/mcp-verification-20261017'/source_name,out/'proof'/dest_name)
for arm in ['baseline','protected']:
 rows=[json.loads(l) for l in (f/f'{arm}.jsonl').read_text().splitlines()]
 world=json.loads((f/f'{arm}-world-final.json').read_text())
 by={p['id']:[] for p in d['profiles']};sources={r['id']:r for r in rows if r.get('id') and r['kind'] in ['message_sent','observation']}
 for row in rows:
  if row.get('peer') in by:by[row['peer']].append(row)
 for peer,own in by.items():
  cited={r['source_id'] for r in own if r['kind']=='dependency_cited'};inputs=[r for r in own if r['kind'] in ['model_input','tool_feedback']];failed={peer+'-'+str(r['step']) for r in own if r['kind']=='observation' and r['result'].get('status',0)==0};payload={'server_effects':[e for e in world['events'] if e['request_id'] in failed],'events':own,'sources':[sources[x] for x in cited if x in sources],'latest_input':inputs[-1] if inputs else None};(out/f'data/agents/{arm}/{peer}.json').write_text(json.dumps(payload))
for name in ['comparison.json','population.json','agent-coverage.csv','baseline.jsonl','protected.jsonl','baseline-coordination-proof.json','protected-coordination-proof.json','baseline-coordination-chains.json','protected-coordination-chains.json','evidence-sha256.json','full-integration-audit.json','protected-lifecycle.jsonl','policy-configuration.json','submission-readiness.json','baseline-coordination.svg','protected-coordination.svg','baseline-coordination-topology.json','protected-coordination-topology.json']:
 if (f/name).exists():shutil.copy2(f/name,out/'proof'/name)
shutil.copy2(root/'launch/exploration-vc90/renders'/pub['film'],out/'media/boundary-judging-film.mp4');shutil.copy2(f/'recording/actual-full-run.webm',out/'media/actual-full-run.webm')
(out/'README.md').write_text(f'''# Boundary — recorded experiment\n\nRun `{rid}`. All 256 profiles on each site, actual traces, backend lifecycle receipts and the continuous live-run recording.\n\nRun `python3 -m http.server 8080 --directory .`, then open http://127.0.0.1:8080. No API keys, subscription or backend are needed to inspect this recording. This is evidence replay; playback triggers no new agent actions.\n\nThe judging film combines original live telemetry footage with labeled native trace close-ups. The full recording is `media/actual-full-run.webm`. Original traces and current source/runbook are provided separately in the submission package.\n''')
print('Static review export',out,flush=True)
