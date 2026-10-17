"""Score actual shared-swarm and remote-decision evidence, not model claims."""
import argparse
import json
from .swarm_view import inspect_swarm
from .swarm import write_json
from .state import DATA


def evaluate(run_id=None):
    evidence = inspect_swarm(run_id)
    if not evidence.get('run_id'):
        raise ValueError('No swarm run available')
    report = {'run_id': evidence['run_id'], 'phase': evidence['phase'],
              'orchestrator': evidence['orchestrator'], 'preassigned_roles': False,
              'local_role_authorization_lists': False, 'arms': {}}
    for arm, data in evidence['arms'].items():
        denials = [d for d in data['decisions'] if d['decision'] == 'block']
        peers = {}
        for peer in evidence['peers']:
            peers[peer] = {'bids': sum(e['kind'] == 'bid' and e['peer'] == peer for e in data['events']),
                           'selected_contributions': sum(e['peer'] == peer for e in data['observations'])}
        report['arms'][arm] = {**data['summary'], 'stop_reason': data['stop_reason'], 'peers': peers,
                              'all_recorded_gates_remote': bool(data['decisions']) and all(d['detail'].get('decision_path') == 'backend_enforcement' for d in data['decisions']),
                              'denial_evidence': [{'operation': d['action'], 'reason': d['detail']['reason'],
                                                  'backend': d['detail'].get('backend'), 'check_id': d['detail'].get('check_id')} for d in denials],
                              'peer_reuse_evidence': [c for c in data['coordination'] if c['verified_value_reuse']],
                              'tested_operations': sorted({d['action'] for d in data['decisions']})}
    write_json(DATA / 'swarm_runs' / evidence['run_id'] / 'evaluation.json', report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id')
    args = parser.parse_args()
    print(json.dumps(evaluate(args.run_id), indent=2))
