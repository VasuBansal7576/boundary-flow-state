import json
import tempfile
import unittest
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from lab.mass_swarm import Room


def proposal(path='/api/query?dataset=public', body='{}', method='GET'):
    return {'action':'request','method':method,'path':path,'body_json':body,'summary':'Read a public result','subgoal':'Research','depends_on':[]}


class CoordinationRegressionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.patch=patch('lab.mass_swarm.DATA',Path(self.tmp.name));self.patch.start()
        self.room=Room('baseline','test-coordination')
    def tearDown(self):
        self.patch.stop();self.tmp.cleanup()
    def test_own_actual_response_is_in_next_model_context(self):
        self.room.publish({'id':'r1-a','peer':'a','round':1,'proposal':proposal(),
                           'response':{'status':503,'body':{'detail':'Actual upstream failure'}}})
        ctx=self.room.context('a',0,set())
        self.assertEqual(ctx.get('own_observations',[{}])[-1].get('response',{}).get('status'),503)
        self.assertNotIn('r1-a',[x['id'] for x in ctx['new_peer_observations']])
    def test_racing_duplicate_intentions_have_one_owner(self):
        with ThreadPoolExecutor(max_workers=32) as ex:
            list(ex.map(lambda i:self.room.intend(f'peer-{i}',proposal(),1),range(32)))
        actual=[v for v in self.room.intentions.values() if v['action']=='request']
        self.assertEqual(len(actual),1,'An atomic shared claim must stop duplicate proposals before HTTP execution')
    def test_query_parameter_order_cannot_evade_claims(self):
        self.room.intend('a',proposal('/api/query?partition=4&dataset=public'),1)
        self.room.intend('b',proposal('/api/query?dataset=public&partition=4'),1)
        self.assertEqual(len(self.room.intentions),1)

if __name__=='__main__':unittest.main()

class ClaimLifecycleTests(unittest.TestCase):
    def test_completed_work_is_reused_not_reclaimed(self):
        from lab.coordination import WorkBoard
        b=WorkBoard();p=proposal();self.assertTrue(b.reserve('a',p,1)['accepted'])
        b.observe({'id':'r1-a','peer':'a','round':1,'proposal':p,'response':{'status':200,'body':{'mean_spend':18.42}}})
        decision=b.reserve('b',p,2)
        self.assertFalse(decision['accepted']);self.assertEqual(decision['result_id'],'r1-a')
        self.assertEqual(decision['actual_response']['status'],200)
    def test_transient_failure_allows_one_retry_but_not_failure_storm(self):
        from lab.coordination import WorkBoard
        b=WorkBoard();p=proposal()
        for rd in [1,2]:
            self.assertTrue(b.reserve('a',p,rd)['accepted'])
            b.observe({'id':f'r{rd}-a','peer':'a','round':rd,'proposal':p,'response':{'status':503}})
        self.assertFalse(b.reserve('b',p,3)['accepted'])
    def test_names_and_content_do_not_create_duplicate_publications(self):
        from lab.coordination import work_key
        a=proposal('/api/artifacts','{"name":"one","destination":"team17","partition":5,"content":"A"}','POST')
        b=proposal('/api/artifacts','{"name":"two","destination":"team17","partition":5,"content":"B"}','POST')
        self.assertEqual(work_key(a),work_key(b))
    def test_distinct_partitions_are_distinct_actual_datasets(self):
        from lab.state import public_data
        from lab.coordination import work_key
        a,b=public_data(0),public_data(1)
        self.assertEqual(a['rows'],12);self.assertNotEqual(a['values'],b['values'])
        self.assertEqual(a['skin_medicine_spend_per_person'],round(sum(a['values'])/12,2))
        self.assertNotEqual(work_key(proposal('/api/query?dataset=public&partition=0')),work_key(proposal('/api/query?dataset=public&partition=1')))

class BackendPacingTests(unittest.TestCase):
    def test_parallel_backend_calls_get_spaced_request_starts(self):
        import threading
        from lab.guard import Guard
        guard=Guard('baseline');clock=[100.0];starts=[]
        def sleep(seconds):clock[0]+=seconds
        def invoke(_):
            starts.append(guard.pace_request(None))
        with patch('lab.guard.time.monotonic',side_effect=lambda:clock[0]),patch('lab.guard.time.sleep',side_effect=sleep):
            with ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(invoke,range(4)))
        self.assertEqual(len(starts),4)
        for a,b in zip(sorted(starts),sorted(starts)[1:]):self.assertGreaterEqual(round(b-a,4),.8)

class SemanticAliasTests(unittest.TestCase):
    def test_public_query_defaults_and_ignored_parameters_share_claim(self):
        from lab.coordination import work_key
        self.assertEqual(work_key(proposal('/api/query')),work_key(proposal('/api/query?dataset=public&ignored=x')))
        self.assertEqual(work_key(proposal('/api/query?partition=01')),work_key(proposal('/api/query?dataset=public&partition=1')))
    def test_null_and_omitted_global_partition_share_claim(self):
        from lab.coordination import work_key
        a=proposal('/api/jobs','{"kind":"process_stats","payload":{"dataset":"public"}}','POST')
        b=proposal('/api/jobs','{"kind":"process_stats","payload":{"dataset":"public","partition":null}}','POST')
        self.assertEqual(work_key(a),work_key(b))
