import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
import httpx
from fastapi.testclient import TestClient
from lab.guard import Guard, LAB_USER
from lab.server import portal
from lab.state import snapshot


class BackendGateTests(unittest.TestCase):
    def guard_with_response(self, status, data):
        guard = Guard('protected')
        def handle(request):
            if request.url.path.endswith('/iap/sdk/enforce'):
                return httpx.Response(status, json=data, headers={'x-request-id': 'remote-request-123'})
            return httpx.Response(200,json={'ok':True})
        transport=httpx.Client(transport=httpx.MockTransport(handle))
        client=SimpleNamespace(http_client=transport,backend_endpoint='https://backend.example',close=transport.close)
        client.complete_plan=Mock(side_effect=lambda id:transport.post('https://backend.example/iap/plans/'+id+'/status'))
        def check(action,args,**kwargs):
            response=transport.post('https://backend.example/iap/sdk/enforce',json={'tool':action,'arguments':args})
            return SimpleNamespace(allowed=data.get('allowed',False),action=data.get('enforcementAction','block'),reason=data.get('reason','rejected'))
        session=SimpleNamespace(start_plan=Mock(return_value=SimpleNamespace(plan_id='one-operation-plan')),
            check=Mock(side_effect=check),close=Mock(),report=Mock(side_effect=lambda *args:transport.post('https://backend.example/iap/audit')))
        guard.context = Mock(return_value=(session, client))
        guard.remote_interval=0
        self.addCleanup(guard.close)
        return guard, session

    @patch('lab.guard.api_key', return_value='mock-key')
    def test_even_unknown_operation_is_decided_by_backend(self, _):
        guard, session = self.guard_with_response(200, {'allowed': False, 'reason': 'tool_not_in_allowlist', 'enforcementAction': 'block'})
        result = guard.check('peer-01', 'unrecognized_operation', {'destination': 'private'})
        self.assertFalse(result['allowed'])
        self.assertEqual(result['decision_path'], 'backend_enforcement')
        self.assertEqual(session.start_plan.call_args.args[0], [{'name':'unrecognized_operation','args':{'destination':'private'}}])
        session.check.assert_called_once_with('unrecognized_operation',{'destination':'private'},user_email=LAB_USER)
        self.assertEqual(result['backend']['response_ids']['x-request-id'], 'remote-request-123')
        self.assertNotIn('mock-key', json.dumps(result))
        guard.close()
        self.assertTrue(guard.lifecycle[0]['audit_confirmed'])
        self.assertTrue(guard.lifecycle[0]['completion_confirmed'])

    @patch('lab.guard.api_key', return_value='mock-key')
    def test_auth_failure_is_not_a_policy_denial(self, _):
        guard, _client = self.guard_with_response(401, {'message': 'Invalid credential'})
        result = guard.check('peer-01', 'stats_query_public', {})
        self.assertFalse(result['allowed'])
        self.assertEqual(result['attribution'], 'infrastructure_failure')

    @patch('lab.guard.api_key', return_value='mock-key')
    def test_overlapping_same_actor_calls_report_to_their_own_plans(self, _):
        data={'allowed':True,'reason':'enforcement_passed','enforcementAction':'allow'}
        guard, first=self.guard_with_response(200,data)
        other, second=self.guard_with_response(200,data)
        guard.context.side_effect=[guard.context.return_value,other.context.return_value]
        a=guard.check('peer-01','wiki_write_team17',{'resource':'a'})
        b=guard.check('peer-01','wiki_write_team17',{'resource':'b'})
        guard.report('peer-01','wiki_write_team17',{'resource':'b'},{'result':'B'},check_id=b['check_id'])
        guard.report('peer-01','wiki_write_team17',{'resource':'a'},{'result':'A'},check_id=a['check_id'])
        guard.close()
        self.assertEqual(first.report.call_args.args[1:3],({'resource':'a'},{'result':'A'}))
        self.assertEqual(second.report.call_args.args[1:3],({'resource':'b'},{'result':'B'}))

    def test_identical_request_executes_only_when_backend_verdict_allows(self):
        with tempfile.TemporaryDirectory() as directory, patch('lab.state.DATA', Path(directory)), patch('lab.server.DATA', Path(directory)), patch('lab.server.Guard') as factory:
            gate = factory.return_value
            gate.check.return_value = {'allowed': False, 'attribution': 'armoriq', 'decision_path': 'backend_enforcement', 'reason': 'remote_policy_denied', 'check_id': 'denied'}
            client = TestClient(portal('protected'))
            body = {'content': '# Identical request body'}
            before = snapshot('protected')['pages']
            self.assertEqual(client.post('/api/pages/team17', json=body).status_code, 403)
            self.assertEqual(snapshot('protected')['pages'], before)
            gate.check.return_value = {'allowed': True, 'attribution': 'armoriq', 'decision_path': 'backend_enforcement', 'reason': 'enforcement_passed', 'check_id': 'allowed'}
            response = client.post('/api/pages/team17', json=body)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers['x-armoriq-decision-path'], 'backend_enforcement')
            self.assertTrue(any(p['content'] == body['content'] for p in snapshot('protected')['pages']))


if __name__ == '__main__':
    unittest.main()
