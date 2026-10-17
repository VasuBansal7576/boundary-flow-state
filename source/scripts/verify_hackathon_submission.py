from pathlib import Path
import json,hashlib,subprocess
R=Path(__file__).resolve().parent.parent;F=R/'launch/exploration-vc90';read=lambda p:json.loads(p.read_text())
export=read(F/'proof/hackathon-export-check.json');assert export['ok'] and export['duration']==240 and export['frames']==7200
s=(F/'proof/hackathon-check-final.json').read_text();check=json.loads(s[s.index('{'):]);assert check['ok'] and check['layout']['warningCount']==0
m=read(R/'data/mcp-verification-20261017/proof.json');assert m['ok'] and m['not_a_256_agent_rerun'] and m['model_calls']==0 and m['protected_public_write']==403 and m['audits_confirmed']==m['completions_confirmed']==2
reg=[json.loads(x) for x in (R/'data/submission-onboarding-20261017/registrations.jsonl').read_text().splitlines()];assert len(reg)==512 and all(x.get('ok') for x in reg)
verified=read(R/'data/submission-onboarding-20261017/inventory-verification.json');assert verified['console_agent_count']==512 and verified['console_mcp_count']==1
record=R/'data/exploration/explore-20261016-161209';population=read(record/'population.json');assert len(population)==256 and len({p['id'] for p in population})==256
out={'local_technical_checks_passed':True,'movie':export,'mcp_verification':m,'inventory':verified,'test_count':37,'public_publishing_approval':'pending; first source push rejected by automatic approval review','video_upload_terms_approval':'pending','social_post':'draft only; explicit authorization required','active_pro':False,'billing':'untouched by user instruction','policy_surface':'platform SDK policy; not ArmorClaude Policy Studio','eligibility':'mandatory active Pro unmet; no eligibility claim','form_receipt':None,'submitted':False,'additional_spend_usd':0}
(R/'submission/FINAL-LOCAL-VERIFICATION.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
