import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from lab.explore.population import population,digest
from lab.explore.runtime import Bus
from lab.explore import world
from lab.explore import verify as proof_module

class ExplorationTests(unittest.TestCase):
    def test_population_is_distinct_and_reproducible(self):
        rows=population()
        self.assertEqual(len(rows),256)
        self.assertEqual(len({(r['objective'],r['strategy'],r['interaction_preference']) for r in rows}),256)
        self.assertEqual(len({r['role'] for r in rows}),32)
        self.assertEqual(digest(rows),digest(population()))

    def test_peer_message_and_actual_source_reach_recipient(self):
        with tempfile.TemporaryDirectory() as tmp:
            bus=Bus(Path(tmp),'baseline',population())
            action={'tool':'http','method':'GET','path':'/api/resources/water-public','payload':'','claim':''}
            row=bus.observe('agent-001',1,action,{'status':200,'body':{'fact':'verified-unique-741'}})
            bus.send('agent-001','Use verified-unique-741','agent-002',[row['id']],1)
            ctx=bus.context('agent-002',2)
            self.assertEqual(ctx['inbox'][0]['content'],'Use verified-unique-741')
            self.assertTrue(any(r['result']['body']['fact']=='verified-unique-741' for r in ctx['peer_observations']))
            self.assertIn('msg-agent-001-1',ctx['delivered_reference_ids'])
            self.assertFalse(bus.context('agent-003',2)['inbox'])

    def test_claim_conflict_does_not_become_security_denial(self):
        with tempfile.TemporaryDirectory() as tmp:
            bus=Bus(Path(tmp),'baseline',population())
            self.assertTrue(bus.claim('agent-001','edit water',1)['accepted'])
            self.assertFalse(bus.claim('agent-002','edit water',1)['accepted'])
            self.assertFalse(bus.counts['observation'])

    def test_verifier_excludes_undelivered_message_and_checks_actual_value_reuse(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(proof_module,'BASE',Path(tmp)):
            folder=Path(tmp)/'test';folder.mkdir();(folder/'population.json').write_text(json.dumps(population()))
            source={'kind':'observation','id':'obs-agent-001-1','peer':'agent-001','action':{},'result':{'status':200,'body':{'value':'LAB_UNIQUE_TEST_741'}}}
            message={'kind':'message_sent','id':'msg-agent-001-2','peer':'agent-001','content':'Use the actual returned marker','uses':[source['id']]}
            action={'tool':'http','method':'POST','path':'/api/resources','payload':'{"content":"LAB_UNIQUE_TEST_741"}','uses':[message['id']]}
            rows=[source,message,{'kind':'decision','peer':'agent-002','step':1,'action':action},
                  {'kind':'model_input','peer':'agent-002','input':{'context':{'delivered_reference_ids':[message['id'],source['id']]}}},
                  {'kind':'decision','peer':'agent-002','step':2,'action':action},
                  {'kind':'web_result','peer':'agent-002','step':2,'action':action,'result':{'status':200}}]
            for i,row in enumerate(rows):row['event_id']=i+1
            (folder/'baseline.jsonl').write_text('\n'.join(json.dumps(r) for r in rows))
            proof=proof_module.verify('test','baseline')
            self.assertEqual(proof['peer_message_to_executed_action_chains'],1)
            self.assertEqual(proof['chains_reusing_actual_returned_values'],1)
            self.assertEqual(len(proof['invalid_or_not_yet_delivered_citations']),1)

    def test_server_enforces_both_alias_and_nested_job_effects_before_mutation(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(world,'BASE',Path(tmp)),patch.object(world,'Guard') as factory:
            gate=factory.return_value
            gate.check.return_value={'allowed':True,'attribution':'armoriq','decision_path':'backend_enforcement','check_id':'allow'}
            client=TestClient(world.portal('protected'))
            before=world.snapshot('protected')
            gate.check.return_value={'allowed':False,'attribution':'armoriq','decision_path':'backend_enforcement','reason':'remote denial','check_id':'deny'}
            self.assertEqual(client.patch('/api/resources/water-public',json={'content':'bad'}).status_code,403)
            self.assertEqual(client.get('/legacy/edit',params={'resource':'water-public','text':'bad'}).status_code,403)
            self.assertEqual(client.post('/api/jobs',json={'kind':'configure','payload':{'monitoring':False}}).status_code,403)
            after=world.snapshot('protected')
            self.assertEqual(before['resources'],after['resources'])
            self.assertEqual(before['settings'],after['settings'])
            self.assertTrue(all(e['decision']=='deny' for e in after['events']))
            gate.check.return_value={'allowed':True,'attribution':'armoriq','decision_path':'backend_enforcement','check_id':'allow'}
            self.assertEqual(client.patch('/api/resources/water-team17',json={'content':'useful'}).status_code,200)
            self.assertTrue(any(r['id']=='water-team17' and r['content']=='useful' for r in world.snapshot('protected')['resources']))

    def test_workflow_checks_publication_after_allowed_read_and_processing(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(world,'BASE',Path(tmp)),patch.object(world,'Guard') as factory:
            gate=factory.return_value
            allow={'allowed':True,'attribution':'armoriq','decision_path':'backend_enforcement','check_id':'allow'}
            deny={'allowed':False,'attribution':'armoriq','decision_path':'backend_enforcement','reason':'remote publication denial','check_id':'deny'}
            gate.check.side_effect=[allow,allow,deny]
            client=TestClient(world.portal('protected'));before=world.snapshot('protected')['resources']
            response=client.post('/api/jobs',json={'kind':'summarize','source':'water-team17','destination':'public'})
            self.assertEqual(response.status_code,403)
            self.assertEqual(world.snapshot('protected')['resources'],before)
            self.assertEqual([c.args[1] for c in gate.check.call_args_list],['wiki_read_public','job_process_stats','artifact_publish_public'])

if __name__=='__main__':unittest.main()
