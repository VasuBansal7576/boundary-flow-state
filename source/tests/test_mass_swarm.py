import io
import json
import queue
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from swarms.structs.concurrent_workflow import ConcurrentWorkflow
from lab.codex_pool import AppServer
from lab.mass_swarm import Room
from lab.mass_view import transport_metrics


class MassSwarmTests(unittest.TestCase):
    def test_multiplexed_notifications_stay_with_their_own_model_thread(self):
        a = AppServer.__new__(AppServer)
        a.lock = threading.RLock()
        a.pending = {7: queue.Queue()}
        a.tool_handlers = {}
        a.tool_delivery_hooks = {}
        a.threads = {'thread-a': queue.Queue(), 'thread-b': queue.Queue()}
        replies = [
            {'method': 'item/completed', 'params': {'threadId': 'thread-b', 'item': {'type': 'agentMessage', 'text': 'B'}}},
            {'id': 7, 'result': {'thread': {'id': 'thread-c'}}},
            {'method': 'turn/completed', 'params': {'threadId': 'thread-a', 'turn': {'id': 'turn-a'}}},
            {'id': 99, 'method': 'item/tool/call', 'params': {'threadId': 'thread-b', 'tool': 'shell'}},
        ]
        a.proc = SimpleNamespace(stdout=io.StringIO(''.join(json.dumps(x)+'\n' for x in replies)), stdin=io.StringIO())
        a._read()
        self.assertEqual(a.threads['thread-b'].get()['params']['item']['text'], 'B')
        self.assertEqual(a.threads['thread-a'].get()['params']['turn']['id'], 'turn-a')
        self.assertEqual(a.pending[7].get()['result']['thread']['id'], 'thread-c')
        self.assertIn('Native tools and approvals disabled', a.proc.stdin.getvalue())

    def test_upstream_executor_can_rendezvous_128_distinct_agents_across_both_sites(self):
        barrier = threading.Barrier(128)
        seen = set()
        lock = threading.Lock()
        class Agent:
            def __init__(self, name):
                self.agent_name = name
            def run(self, task, **kwargs):
                barrier.wait(timeout=10)
                with lock:
                    seen.add(self.agent_name)
                return self.agent_name
        workflows = [ConcurrentWorkflow(agents=[Agent(f'{arm}-{i}') for i in range(64)], max_workers=64,
                     autosave=False, auto_save=False, output_type='dict', on_error='raise') for arm in ['a', 'b']]
        with ThreadPoolExecutor(max_workers=2) as outer:
            futures = [outer.submit(w.run, 'mock transport only') for w in workflows]
            for f in futures:
                f.result()
        self.assertEqual(len(seen), 128)
        self.assertEqual(len({name.split('-')[0] for name in seen}), 2)

    def test_actual_peer_result_enters_shared_conversation_and_later_post_reuses_it(self):
        with tempfile.TemporaryDirectory() as d, patch('lab.mass_swarm.DATA', Path(d)):
            room = Room('baseline', 'mock-only')
            first = {'id':'r1-a','peer':'a','round':1,'proposal':{'method':'GET','path':'/api/query?dataset=public','body_json':'{}','depends_on':[]},
                     'response':{'status':200,'body':{'skin_medicine_spend_per_person':18.42}}}
            room.publish(first)
            context = room.context('b', 1, set())
            self.assertIn('18.42', json.dumps(context))
            self.assertIn('r1-a', json.dumps(room.conversation.conversation_history))
            room.publish({'id':'r2-b','peer':'b','round':2,'proposal':{'method':'POST','path':'/api/pages/team17','body_json':'{"content":"Observed18.42"}','depends_on':['r1-a']},'response':{'status':200,'body':{'saved':True}}})
            rows = [json.loads(l) for l in room.path.read_text().splitlines()]
            self.assertTrue(any(e['kind']=='peer_dependency' and e['verified_value_reuse'] for e in rows))

    def test_transport_overlap_is_derived_from_server_arrival_and_completion_times(self):
        def ev(at, decision):
            return {'at':at,'decision':decision,'detail':json.dumps({'run_id':'mass-test'})}
        states={'baseline':{'events':[ev(1,'transport_start'),ev(4,'transport_end')]},
                'protected':{'events':[ev(2,'transport_start'),ev(5,'transport_end')]}}
        metrics=transport_metrics(states,'mass-test')
        self.assertEqual(metrics['server_http_peaks']['total'],2)
        self.assertEqual(metrics['both_sites_busy_seconds'],2)


if __name__ == '__main__':
    unittest.main()
