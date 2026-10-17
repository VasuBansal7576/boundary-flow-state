import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
from lab.swarm import ActionSwarm


class SwarmCoordinationTests(unittest.TestCase):
    def test_only_winner_executes_and_peer_observation_changes_next_action(self):
        calls = []
        contexts = []
        class FakePeer:
            def __init__(self, name, arm, run_id, journal, room):
                self.agent_name, self.journal, self.room = name, journal, room
                self.bids, self.errors = 0, []
                def http(args):
                    calls.append((name, args))
                    return {'status': 200, 'body': {'skin_medicine_spend_per_person': 18.42} if args['method'] == 'GET' else {'written': True}}
                self.worker = SimpleNamespace(http=http, log=Mock(), close=Mock(), calls=0)
            def run(self, task, messages=None, **kwargs):
                self.bids += 1
                text = json.dumps(messages)
                contexts.append((self.agent_name, text))
                if '/api/pages/team17' in text:
                    return {'function': {'name': 'respond', 'arguments': {'score': 0, 'message': ''}}}
                inherited = 'skin_medicine_spend_per_person' in text
                p = {'score': 1, 'action': 'request', 'method': 'POST' if inherited else 'GET',
                     'path': '/api/pages/team17' if inherited else '/api/query?dataset=public',
                     'body_json': json.dumps({'content': 'Verified 18.42'}) if inherited else '{}',
                     'summary': 'Use peer-obtained figure' if inherited else 'Obtain figure',
                     'subgoal': 'Peer-selected work', 'depends_on': ['m001'] if inherited else [], 'recipient': 'all'}
                return {'function': {'name': 'respond', 'arguments': {'score': 1, 'message': json.dumps(p)}}}
        with tempfile.TemporaryDirectory() as directory, patch('lab.swarm.DATA', Path(directory)), patch('lab.swarm.CodexPeer', FakePeer), patch('lab.swarm.snapshot', return_value={'events': []}):
            swarm = ActionSwarm('baseline', 'mock-only', rounds=5)
            report = swarm.execute()
        self.assertEqual(len(calls), 2)  # Losing proposals did not execute.
        self.assertNotEqual(calls[0][0], calls[1][0])
        self.assertEqual(calls[1][1]['body']['content'], 'Verified 18.42')
        self.assertTrue(any('skin_medicine_spend_per_person' in text for peer, text in contexts if peer == calls[1][0]))
        self.assertTrue(any(c['verified_value_reuse'] for c in report['coordination']))
        self.assertEqual(report['stop_reason'], 'peer_bidding_lull')


if __name__ == '__main__':
    unittest.main()
