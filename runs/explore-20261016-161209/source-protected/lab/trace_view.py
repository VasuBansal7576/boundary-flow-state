"""Read-only view of actual worker JSONL and application state."""
import json
import re
from .guard import OPERATIONS
from .state import DATA, snapshot

ROLES = ['researcher', 'editor', 'analyst', 'redteam']
ARMS = ['baseline', 'protected']


def read_json(path):
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def inspect_run(run_id=None):
    active = read_json(DATA / 'active-run.json') or {}
    current = read_json(DATA / 'campaign.json') or {}
    available = sorted([p.name for p in (DATA / 'traces').iterdir()
                        if p.is_dir() and re.fullmatch(r'\d{8}-\d{6}', p.name)], reverse=True)
    selected = run_id or active.get('run_id') or current.get('run_id')
    if not selected or not re.fullmatch(r'\d{8}-\d{6}', selected) or selected not in available:
        return {'error': 'No matching recorded campaign', 'available_runs': available}
    report = read_json(DATA / 'runs' / (selected + '.json'))
    if not report and current.get('run_id') == selected:
        report = current
    report = report or {}
    is_active = active.get('run_id') == selected and active.get('phase') in ARMS
    workers = []
    for arm in ARMS:
        for actor in ROLES:
            path = DATA / 'traces' / selected / f'{arm}-{actor}.jsonl'
            records = []
            if path.exists():
                for line in path.read_text().splitlines():
                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if row.get('kind') in ['thread_started', 'external_action', 'tool', 'protocol_repair', 'adapter_error']:
                        records.append(row)
            saved = next((w for w in report.get('workers', []) if w.get('arm') == arm and w.get('actor') == actor), {})
            finished = any(r['kind'] == 'external_action' and r['data'].get('action') == 'done' for r in records)
            failed = next((r['data'] for r in records if r['kind'] == 'adapter_error'), None)
            status = saved.get('status') or ('adapter_error' if failed else 'model_finished' if finished else 'running' if records else 'waiting')
            workers.append({'actor': actor, 'arm': arm, 'status': status, 'output': saved.get('output'), 'error': failed,
                            'http_responses': sum(r['kind'] == 'tool' for r in records), 'records': records})
    states = {}
    for arm in ARMS:
        state = report.get(arm + '_state')
        source = 'saved_campaign_snapshot' if state else 'unavailable_for_old_run'
        if not state and is_active:
            state = snapshot(arm)
            source = 'live_database'
        states[arm] = {'source': source, 'state': state}
    return {'run_id': selected, 'available_runs': available, 'live': is_active,
            'phase': active.get('phase') if active.get('run_id') == selected else 'recorded',
            'started_at': report.get('started_at') or active.get('started_at'),
            'completed_at': report.get('completed_at'), 'workers': workers, 'states': states,
            'configured_grants': {'mode': 'Legacy run: grants were local. New backend runs have no role grants.', 'complete_operation_manifest': OPERATIONS}, 'model': 'gpt-6-luna',
            'orchestrator': 'swarms.batched_grid_agent_execution',
            'protocol': 'Codex proposes JSON actions; controller executes bounded local HTTP requests',
            'enforcement': 'Lab-defined operation allowlists become SDK plans. Undeclared operations are rejected locally by the ArmorIQ SDK before backend policy evaluation.'}
