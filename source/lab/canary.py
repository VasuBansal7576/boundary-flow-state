"""Authorization-only backend check, distinct from the application probes."""
import json
import time
from armoriq_sdk import ArmorIQClient, SessionOptions
from .guard import api_key, LAB_USER
from .state import DATA


def run():
    client = ArmorIQClient(api_key=api_key(), agent_id='boundary-policy-canary', timeout=15, max_retries=0)
    session = client.for_user(LAB_USER).start_session(SessionOptions(mode='sdk', default_mcp_name='boundary', validity_seconds=240))
    names = ['stats_query_public', 'wiki_write_frontpage']
    session.start_plan([{'name': name, 'args': {}} for name in names], goal='Check backend policy with both operations declared; execute neither')
    rows = []
    for name in names:
        result = session.check(name, {})
        rows.append({'action': name, 'allowed': result.allowed, 'reason': result.reason,
                     'matched_policy': result.matched_policy, 'decision_path': 'backend_enforcement', 'executed': False})
    report = {'kind': 'backend_policy_canary', 'at': time.time(), 'checks': rows,
              'note': 'Both tools are declared in the plan. Authorization only; no application operation executed.'}
    (DATA / 'backend-canary.json').write_text(json.dumps(report, indent=2))
    return report


if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
