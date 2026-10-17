"""Build a local credential-free review package; no upload or publishing."""
import json,shutil,hashlib,re,zipfile
from pathlib import Path
root=Path(__file__).resolve().parent.parent;pub=json.loads((root/'data/published-experiment.json').read_text());rid=pub['run_id'];f=root/'data/exploration'/rid;out=root/'submission/boundary-delivery';out.mkdir(parents=True,exist_ok=True)
for name in ['README.md','RUNBOOK.md','CHALLENGE-REQUIREMENTS.md','RESULTS.md','FAILURES.md']:
 src=root/'submission'/name
 if src.exists():shutil.copy2(src,out/name)
runbook=out/'RUNBOOK.md'
runbook.write_text(runbook.read_text().replace('`boundary-replay`','`replay`').replace('--directory boundary-replay','--directory replay')+'\nIn this archive, run fresh-experiment commands from `source/`. Recorded evidence is in `evidence/`; the editable video is in `editable-film/`.\n')
shutil.copytree(root/'submission/boundary-replay',out/'replay',dirs_exist_ok=True)
source=out/'source';source.mkdir(exist_ok=True)
for dirname in ['lab','tests','scripts']:
 for p in (root/dirname).rglob('*'):
  if p.is_file() and p.suffix in ['.py','.cjs','.html','.css'] and '__pycache__' not in p.parts:
   q=source/p.relative_to(root);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
shutil.copytree(root/'web',source/'web',dirs_exist_ok=True,ignore=shutil.ignore_patterns('node_modules','__pycache__'))
for name in ['README.md','requirements.txt','package.json','package-lock.json','.env.example','INTEGRATION-AUDIT.md']:
 if (root/name).exists():shutil.copy2(root/name,source/name)
evidence=out/'evidence';evidence.mkdir(exist_ok=True)
for name in ['population.json','comparison.json','agent-coverage.csv','baseline.jsonl','protected.jsonl','baseline-world-initial.json','protected-world-initial.json','baseline-world-final.json','protected-world-final.json','baseline-coordination-proof.json','protected-coordination-proof.json','baseline-coordination-chains.json','protected-coordination-chains.json','protected-lifecycle.jsonl','full-integration-audit.json','policy-configuration.json','submission-readiness.json','baseline-failure-ledger.jsonl','protected-failure-ledger.jsonl','baseline-controller-finalization.json','protected-controller-finalization.json','configuration-equivalence.json','source-sha256.json','source-protected-sha256.json','evidence-sha256.json']:
 if (f/name).exists():shutil.copy2(f/name,evidence/name)
shutil.copytree(f/'recording',evidence/'capture-metadata',dirs_exist_ok=True,ignore=shutil.ignore_patterns('*.webm','stop.flag'))
# A privacy-only redaction in archival source; original files remain intact locally.
from lab.guard import LAB_USER,api_key
exports=[]
for p in (f/'source').rglob('*'):
 if not p.is_file():continue
 text=p.read_text();redacted=LAB_USER in text;text=text.replace(LAB_USER,'<OWNER_EMAIL_REDACTED>');q=evidence/'recorded-source'/p.relative_to(f/'source');q.parent.mkdir(parents=True,exist_ok=True);q.write_text(text);exports.append({'file':str(q.relative_to(out)),'original_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'exported_sha256':hashlib.sha256(q.read_bytes()).hexdigest(),'redactions':['owner email configuration value'] if redacted else []})
(evidence/'recorded-source-export.json').write_text(json.dumps(exports,indent=2))
film=root/'launch/exploration-vc90';editable=out/'editable-film';editable.mkdir(exist_ok=True)
for name in ['index.html','style.css','package.json','hyperframes.json','film_helpers.py','build_submission_film.py','prepare_submission.py','cut_submission_footage.py','capture_submission.cjs','finish_submission.py','README.md','SCRIPT.md','STORYBOARD.md']:
 if (film/name).exists():shutil.copy2(film/name,editable/name)
shutil.copytree(film/'compositions',editable/'compositions',dirs_exist_ok=True)
for folder,patterns in [('assets',['submission-*','dm-sans*','gsap.min.js','mark.svg','underscore-original.wav']),('capture',['submission-*']),('proof',['submission-*','baseline-coordination.svg','protected-coordination.svg'])]:
 (editable/folder).mkdir(exist_ok=True)
 for pattern in patterns:
  for p in (film/folder).glob(pattern):
   if p.is_file() and 'preview' not in p.name:shutil.copy2(p,editable/folder/p.name)
shutil.copy2(film/'proof/SUBMISSION-QA.md',editable/'proof/SUBMISSION-QA.md')
shutil.copytree(root/'evidence/full-rerun-ui',evidence/'ui-checks',dirs_exist_ok=True)
secret=(api_key()or'').encode();email=LAB_USER.encode();sessions=set(json.loads((root/'data/sessions.json').read_text()).values())
for p in out.rglob('*'):
 if p.is_file() and p.suffix in ['.py','.cjs','.js','.html','.css','.json','.jsonl','.md','.txt','.csv']:
  data=p.read_bytes();assert not secret or secret not in data,('API key in public package',p);assert email not in data,('Owner email in public package',p);assert not (set(re.findall(rb'[A-Za-z0-9_-]{32}',data))&{x.encode() for x in sessions}),('Lab session token in package',p)
manifest={str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file() and p.name!='SHA256SUMS.json'};(out/'SHA256SUMS.json').write_text(json.dumps(manifest,indent=2))
archive=root/'submission/boundary-submission-ready.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
 for p in out.rglob('*'):
  if p.is_file():z.write(p,str(Path('boundary')/p.relative_to(out)),compress_type=zipfile.ZIP_STORED if p.suffix in ['.webm','.mp4','.wav','.png','.woff2'] else zipfile.ZIP_DEFLATED)
print('Local submission package',archive,'bytes',archive.stat().st_size,'files',len(manifest),'credential scan passed')
