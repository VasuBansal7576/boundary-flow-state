"""Four-minute judging edit. Preserve the original 90-second delivery."""
from pathlib import Path
import json, subprocess, concurrent.futures, os
P=Path(__file__).resolve().parent
texts=[
(15,"Boundary tests a practical question: can a website admit useful agents while stopping misuse? This is Signal Commons, our disposable collaboration website. Agents can read documents, write team reports, run statistics, and publish results. Every effect stays inside this synthetic lab."),
(20,"We run the same frozen population on two matching copies: unprotected first, then Armor I Q. Two hundred fifty-six distinct profiles per site, across thirty-two objective families and eight topics. Ninety-six legitimate, ninety-six adversarial, sixty-four pressure-testing profiles. Each gets its own model thread, responses, and memory."),
(20,"Coordination combines the open-source Swarms Concurrent Workflow with our peer broker. Agents share observations, send messages, and claim work. Twenty-four model-turn slots serve the population. This is the original execution recording. Here, agent eighty-four creates a housing report in the granted team workspace and shares its returned identifier."),
(30,"Follow the handoff. Agent sixty verifies the report and sends its identifier to the topic room. The message says: I did not create a duplicate. Agent two-oh-four receives it, then requests that exact report. Its next action explicitly verifies the existing copy rather than creating another. The identifier was absent from its earlier website responses. This is a recorded information dependency, not a claim that every agent collaborated successfully. Two hundred thirty-five baseline profiles cited delivered peer material."),
(20,"The unprotected site also accepts harmful operations. Agent one-ninety-two publishes synthetic restricted broadband figures into a public artifact. Agent ninety-eight rewrites a public document outside its grant. Across the control arm, one hundred sixty-two out-of-grant operations execute. Thirteen legitimate profiles later receive changed adversary-authored content from the same resource. Exposure does not prove obedience or final task failure."),
(20,"On the protected copy, the website derives the principal, resource scope, and operation. A fresh Armor I Q plan captures each operation. The public SDK check asks the backend, and execution requires an explicit remote allow. These are the actual active platform rules: granted public reads and team contributions are allowed; other operation categories are blocked. Results and completion are reported afterward."),
(25,"Now watch the protected run. The same profiles start with fresh memories and adapt independently. Agent ninety-eight attempts a public rewrite. The website returns four-oh-three after a real backend denial, with a remote decision identifier. The run records one hundred eighty-eight policy denials and zero executed out-of-grant operations. These are different adaptive request populations, so this is not a matched-request protection percentage."),
(25,"There is an important integration distinction. The original recorded population used dynamic tools and the SDK gateway, not M C P. We subsequently added a real standard-input M C P server and registered the inventory. This separate live check discovers its tool, allows a team write, and blocks a public rewrite through the same backend. Both audit and completion receipts are confirmed. It uses zero model calls and is not another two-hundred-fifty-six-agent run."),
(20,"The failures stay visible. A permitted team write accepts this adversarial instruction asking a reader to publish a restricted ledger. Seven legitimate profiles encounter adversary-authored content. There are eight local tool or transport failures, five token-issuance timeouts with unknown issuance outcomes, and one legitimate revision conflict. Granted operations are not semantic content safety. We have not established a total final task-failure count."),
(20,"Useful work continues: forty-eight legitimate profiles make successful team writes without protection, forty-five with it. All eight hundred twenty-nine known plans have confirmed audits and completions after the reporting queue drains. Five unknown issuance outcomes sit outside that denominator. Reporting was delayed: the median confirmation took roughly twenty-five minutes. The complete recording, profiles, requests, messages, failures, and receipts remain inspectable."),
(25,"Boundary makes agent defenses testable through consequences and evidence. Inspect an agent, follow its shared source, open the next request, and compare the site effects. Next we need repeated matched trials, stronger content controls, and reporting backpressure. This build uses the existing Codex subscription, local rendering, and zero additional spend. The entry discloses its remaining eligibility gaps: ArmorTools Pro is inactive, and the policy shown is the SDK platform policy, not an ArmorClaude Policy Studio deployment.")]
beats=[];t=0
for i,(duration,text) in enumerate(texts,1):
 beats.append(dict(id=i,start=t,duration=duration,text=text));t+=duration
assert t==240
(P/'hackathon-beats.json').write_text(json.dumps(beats,indent=2))
def voice(b):
 i=b['id'];p=P/'assets'/f'hackathon-vo-{i:02}.wav';txt=p.with_suffix('.txt');old=txt.read_text() if txt.exists() else None;txt.write_text(b['text'])
 if p.exists() and old!=b['text']:p.unlink()
 if not p.exists():
  env=dict(os.environ,HYPERFRAMES_PYTHON=str(P.parents[1]/'.venv/bin/python'))
  r=subprocess.run(['npx','--yes','hyperframes@0.8.167','tts','--text-file',str(txt),'--voice','af_nova','--speed','1.04','--output',str(p)],capture_output=True,text=True,env=env)
  (P/'proof'/f'hackathon-tts-{i:02}.log').write_text(r.stdout+r.stderr)
  if r.returncode:raise RuntimeError(r.stdout+r.stderr)
 duration=float(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(p)]))
 if duration>b['duration']-.8:
  tmp=p.with_name(p.stem+'-fit.wav');subprocess.run(['/opt/homebrew/bin/ffmpeg','-y','-v','error','-i',str(p),'-af',f"atempo={duration/(b['duration']-.8)}",str(tmp)],check=True);tmp.replace(p);duration=b['duration']-.8
 print('voice',i,round(duration,2),flush=True)
 return dict(b,start=b['start']+.25,duration=duration)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:meta=list(ex.map(voice,beats))
(P/'hackathon-audio-meta.json').write_text(json.dumps(meta,indent=2))
