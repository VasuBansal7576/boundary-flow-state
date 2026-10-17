from pathlib import Path
import json,hashlib,subprocess
R=Path(__file__).resolve().parent.parent;F=R/'launch/exploration-vc90';read=lambda p:json.loads(p.read_text())
export=read(F/'proof/hackathon-export-check.json');assert export['ok'] and export['duration']==240 and export['frames']==7200
s=(F/'proof/hackathon-check-final.json').read_text();check=json.loads(s[s.index('{'):]);assert check['ok'] and check['layout']['warningCount']==0
m=read(R/'data/mcp-verification-20261017/proof.json');assert m['ok'] and m['not_a_256_agent_rerun'] and m['model_calls']==0 and m['protected_public_write']==403 and m['audits_confirmed']==m['completions_confirmed']==2
reg=[json.loads(x) for x in (R/'data/submission-onboarding-20261017/registrations.jsonl').read_text().splitlines()];assert len(reg)==512 and all(x.get('ok') for x in reg)
verified=read(R/'data/submission-onboarding-20261017/inventory-verification.json');assert verified['console_agent_count']==512 and verified['console_mcp_count']==1
record=R/'data/exploration/explore-20261016-161209';population=read(record/'population.json');assert len(population)==256 and len({p['id'] for p in population})==256
prior=read(R/'submission/FINAL-LOCAL-VERIFICATION.json') if (R/'submission/FINAL-LOCAL-VERIFICATION.json').exists() else {}
out={**prior,'local_technical_checks_passed':True,'movie':export,'mcp_verification':m,'inventory':verified,'tests_rerun_by_this_script':False,'public_publishing_approval':prior.get('public_publishing_approval','not verified'),'video_upload_terms_approval':prior.get('video_upload_terms_approval','not verified'),'social_post':prior.get('social_post','not published; explicit authorization required'),'active_pro':prior.get('active_pro'),'billing':prior.get('billing','not verified'),'policy_surface':'platform SDK policy; not ArmorClaude Policy Studio','eligibility':prior.get('eligibility','not verified; see current checklist'),'form_receipt':prior.get('form_receipt'),'submitted':prior.get('submitted',False),'additional_spend_usd':0,'readiness_scope':'Local evidence checks; not a certification of eligibility','latest_requirements':'SUBMISSION-CHECKLIST.md'}
(R/'submission/FINAL-LOCAL-VERIFICATION.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
