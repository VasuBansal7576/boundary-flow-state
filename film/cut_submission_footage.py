from pathlib import Path
import json,datetime,subprocess
P=Path(__file__).resolve().parent;ROOT=P.parent.parent;M=json.loads((P/'proof/submission-story.json').read_text());f=ROOT/'data/exploration'/M['run_id'];capture_file=f/'recording/capture-manifest.json';capture=json.loads((capture_file if capture_file.exists() else f/'recording/capture-start.json').read_text());source=f/'recording/actual-full-run.webm'
if not source.exists():source=next((f/'recording').glob('page@*.webm'));capture['status']='in_progress'
zero=datetime.datetime.fromisoformat(capture['recording_page_created_at'].replace('Z','+00:00')).timestamp();clips=[]
# Select original execution ranges containing real effects/blocks, at normal speed.
for arm,key in [('baseline','leak'),('protected','block')]:
 c=next(c for c in M['cases'] if c['id']==key);at=c['event']['at'];offset=max(0,at-zero-3);out=P/f'capture/submission-{arm}-live.mp4'
 subprocess.run(['/opt/homebrew/bin/ffmpeg','-y','-v','error','-ss',str(offset),'-i',str(source),'-t','10','-an','-r','30','-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(out)],check=True)
 subprocess.run(['/opt/homebrew/bin/ffmpeg','-y','-v','error','-ss','4','-i',str(out),'-frames:v','1',str(P/f'proof/{arm}-live-cut.png')],check=True)
 clips.append({'arm':arm,'file':str(out.relative_to(P)),'source':str(source.relative_to(ROOT)),'source_start_seconds':offset,'duration':10,'playback_rate':1,'target_event_id':c['event']['event_id'],'target_agent':c['agent'],'target_event_at':at,'timing_note':'Offset uses recorder page creation wall-clock; verify the captured onscreen UTC clock and receipt visually.'})
(P/'capture/submission-live-footage-manifest.json').write_text(json.dumps({'run_id':M['run_id'],'original_recording':capture,'clips':clips},indent=2));print('Cut actual continuous-run footage at normal speed')
