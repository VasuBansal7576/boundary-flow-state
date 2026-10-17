from pathlib import Path
import json,subprocess,concurrent.futures
P=Path(__file__).resolve().parent;A=P/'assets';m=json.loads((P/'proof/submission-story.json').read_text());a=m['comparison']['arms'];d=m['product_arms'];audit=m['audit'];h=m['handoff'];leak=m['leak'];b=m['block'];miss=m['plant']
beats=[(1,0,9,'Boundary tests how coordinated agents use and misuse websites. Two matching sites. Unprotected first, then Armor I Q. This time, we record the full execution.'),(2,9,10,f"Two hundred fifty-six profiles per site. Each has its own model thread. In the control arm, all received peer material; {a['baseline']['agents_citing_delivered_peer_material']} cited it in decisions. This is actual live footage."),(3,19,17,f"{h['creator_spoken']} creates a report. {h['producer_spoken']} relays its new identifier. {h['consumer_spoken']} receives it and verifies the report. Follow the recorded reference and request. Meanwhile, {leak['spoken']} {d['baseline']['adversarial_agents_with_out_of_grant_effects']} adversarial profiles crossed the grant."),(4,36,12,f"It reaches legitimate work. {d['baseline']['exposed_legitimate_agents']} legitimate profiles received changed adversarial content from the same resource. Open the actual write and subsequent response. Exposure is verified; a total final task-failure count is not established."),(5,48,16,f"Now the same profiles, with fresh memories, on Armor I Q. Watch the backend blocks arrive. This request gets four-oh-three with a remote decision identifier. {a['protected']['backend_policy_denials']} policy denials. {a['protected']['out_of_grant_executed_operations']} out-of-grant operations executed."),(6,64,13,f"But a granted operation accepts this adversarial instruction. {d['protected']['exposed_legitimate_agents']} legitimate profiles encountered adversary-authored content. {a['protected']['local_tool_or_transport_failures']} local tool or transport failures. {a['protected']['enforcement_errors']} enforcement errors. Permission is not content safety."),(7,77,13,f"Per-operation plans. Public SDK checks. Actual outcome reports. {audit['audit_confirmed']} audits and {audit['completion_confirmed']} completions confirmed. Both populations, all traces, and the continuous recording are inspectable. Existing Codex subscription. Zero additional spend.")]

(P/'submission-beats.json').write_text(json.dumps([dict(id=i,start=s,duration=d,text=t) for i,s,d,t in beats],indent=2))
def voice(b):
 i,s,d,t=b;f=A/f'submission-vo-{i:02}.wav';txt=A/f'submission-vo-{i:02}.txt';prior=txt.read_text() if txt.exists() else None;txt.write_text(t)
 if f.exists() and prior!=t:f.unlink()
 if not f.exists():
  r=subprocess.run(['npx','--yes','hyperframes@0.8.164','tts','--text-file',str(txt),'--voice','af_nova','--speed','1.08','--output',str(f)],capture_output=True,text=True);(P/'proof'/f'submission-tts-{i:02}.log').write_text(r.stdout+r.stderr)
  if r.returncode:raise RuntimeError(r.stdout+r.stderr)
 probe=lambda p:float(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(p)]))
 length=probe(f)
 if length>d-.4:
  tmp=A/f'submission-temp-{i}.wav';subprocess.run(['/opt/homebrew/bin/ffmpeg','-y','-v','error','-i',str(f),'-af',f'atempo={length/(d-.5)}',str(tmp)],check=True);tmp.replace(f);length=probe(f)
 print('voice',i,round(length,2),flush=True);return dict(id=i,start=s+.12,duration=length,text=t)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:meta=list(ex.map(voice,beats))
(P/'submission-audio-meta.json').write_text(json.dumps(meta,indent=2))
