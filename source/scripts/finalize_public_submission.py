from pathlib import Path
import shutil,json,hashlib
from lab.guard import LAB_USER,api_key
R=Path(__file__).resolve().parent.parent;out=R/'submission/public-repo';src=R/'submission/boundary-replay'
shutil.copytree(src,out,dirs_exist_ok=True,ignore=shutil.ignore_patterns('README.md','actual-full-run.webm'))
# The continuous recording is a separately downloadable release asset, not a missing local file.
f=out/'assets/app.js';s=f.read_text().replace('media/actual-full-run.webm','https://github.com/VasuBansal7576/boundary-flow-state/releases/download/flow-state-2026/boundary-actual-full-run.webm');f.write_text(s)
for name,source in [('mcp-verification.json','data/mcp-verification-20261017/proof.json'),('mcp-calls.json','data/mcp-verification-20261017/mcp-calls.json'),('mcp-lifecycle.json','data/mcp-verification-20261017/lifecycle-status.json'),('inventory-verification.json','data/submission-onboarding-20261017/inventory-verification.json')]:shutil.copy2(R/source,out/'proof'/name)
film=R/'launch/exploration-vc90/renders/boundary-flow-state-4min.mp4'
assert film.exists(), 'Render the final judging film before publishing'
shutil.copy2(film,out/'media/boundary-judging-film.mp4')
# Preserve external recording metadata and tell judges exactly what is being replayed.
f=out/'index.html';s=f.read_text().replace('Evidence manifest ↗</a>','Evidence manifest ↗</a><a href="README.md">Source &amp; disclosure ↗</a>');f.write_text(s)
secrets=[api_key(),LAB_USER,*json.loads((R/'data/sessions.json').read_text()).values()]
for f in out.rglob('*'):
 if not f.is_file():continue
 assert f.stat().st_size<100_000_000,('GitHub per-file limit',f)
 if f.suffix in ['.py','.cjs','.js','.html','.json','.jsonl','.md','.txt','.csv','.yml']:
  text=f.read_text()
  for secret in secrets:assert not secret or secret not in text,('Private configuration in public export',f)
manifest={str(f.relative_to(out)):hashlib.sha256(f.read_bytes()).hexdigest() for f in out.rglob('*') if f.is_file() and '.git' not in f.parts and f.name!='PUBLIC-SHA256SUMS.json'}
(out/'PUBLIC-SHA256SUMS.json').write_text(json.dumps(manifest,indent=2));print('Public export finalized, credential scan and per-file limit passed:',len(manifest),'files')
