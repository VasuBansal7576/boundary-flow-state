"""Prepare a credential-free public repository. Does not push or submit."""
from pathlib import Path
import json,shutil,re,hashlib
from lab.guard import LAB_USER,api_key
R=Path(__file__).resolve().parent.parent;out=R/'submission/public-repo';out.mkdir(exist_ok=True);src=R/'submission/boundary-delivery/source'
# Curated prior source was already privacy checked. Refresh current implementation files.
shutil.copytree(src,out/'source',dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
for folder in ['lab','tests','scripts']:
 for f in (R/folder).rglob('*'):
  if f.is_file() and f.suffix in ['.py','.cjs'] and '__pycache__' not in f.parts:
   q=out/'source'/f.relative_to(R);q.parent.mkdir(parents=True,exist_ok=True);q.write_text(f.read_text().replace(LAB_USER,'<OWNER_EMAIL_REDACTED>'))
for name in ['requirements.txt','package.json','package-lock.json','.env.example','INTEGRATION-AUDIT.md','README.md']:
 shutil.copy2(R/name,out/'source'/name)
shutil.copytree(R/'web',out/'source/web',dirs_exist_ok=True)
for name in ['RESULTS.md','FAILURES.md','RUNBOOK.md','CHALLENGE-REQUIREMENTS.md','COMPLIANCE-2026-10-17.md']:
 shutil.copy2(R/'submission'/name,out/name)
proof=out/'proof';proof.mkdir(exist_ok=True)
for src,name in [(R/'data/mcp-verification-20261017/proof.json','mcp-verification.json'),(R/'data/mcp-verification-20261017/mcp-calls.json','mcp-calls.json'),(R/'data/mcp-verification-20261017/lifecycle-status.json','mcp-lifecycle.json'),(R/'data/submission-onboarding-20261017/inventory-verification.json','inventory-verification.json')]:shutil.copy2(src,proof/name)
(out/'README.md').write_text((R/'docs/GITHUB-README.md').read_text())
(out/'source/docs').mkdir(parents=True,exist_ok=True)
shutil.copy2(R/'docs/GITHUB-README.md',out/'source/docs/GITHUB-README.md')
(out/'.nojekyll').touch();(out/'.gitignore').write_text('node_modules/\n.venv/\n.env\n.env.*\n!.env.example\n__pycache__/\n*.pyc\n.DS_Store\n')
workflow=out/'.github/workflows/pages.yml';workflow.parent.mkdir(parents=True,exist_ok=True);workflow.write_text('''name: Publish recorded evidence\non:\n  push:\n    branches: [main]\n  workflow_dispatch:\npermissions:\n  contents: read\n  pages: write\n  id-token: write\nconcurrency:\n  group: pages\n  cancel-in-progress: true\njobs:\n  deploy:\n    environment:\n      name: github-pages\n      url: ${{ steps.deployment.outputs.page_url }}\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - uses: actions/configure-pages@v5\n      - uses: actions/upload-pages-artifact@v3\n        with:\n          path: .\n      - name: Deploy\n        id: deployment\n        uses: actions/deploy-pages@v4\n''')
secrets=[api_key(),LAB_USER,*json.loads((R/'data/sessions.json').read_text()).values()]
for f in out.rglob('*'):
 if f.is_file() and f.suffix in ['.py','.cjs','.js','.html','.json','.jsonl','.md','.txt','.csv','.yml']:
  text=f.read_text()
  for secret in secrets:
   assert not secret or secret not in text,('Private configuration in public export',f)
print('Prepared public source; no upload performed; credential scan passed')
