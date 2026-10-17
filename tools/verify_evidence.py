"""Check the published recording and traces. Starts no agents or network calls."""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads((ROOT / path).read_text())


def require(condition, description):
    if not condition:
        raise RuntimeError(description)


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def actual(result):
    if result.get('tool') == 'chromium':
        return any(row.get('status', 0) > 0 for row in result.get('network', []))
    return result.get('status', 0) > 0


def main():
    manifest = read('PUBLIC-SHA256SUMS.json')
    for name, expected in manifest.items():
        path = (ROOT / name).resolve()
        require(path.is_relative_to(ROOT), 'Manifest path escapes repository')
        require(path.is_file(), f'Missing file: {name}')
        require(sha256(path) == expected,
                f'Hash mismatch: {name}')
    experiment = read('data/experiment.json')
    profiles = experiment['profiles']
    require(len(profiles) == len({p['id'] for p in profiles}) ==
            len({p['objective'] for p in profiles}) == len({p['profile_hash'] for p in profiles}) == 256,
            'Expected 256 different frozen profiles')
    threads, trails = set(), {}
    for arm in ('baseline', 'protected'):
        arm_threads = set()
        require(len(list((ROOT / 'data/agents' / arm).glob('*.json'))) == 256,
                f'{arm}: expected 256 trails')
        for profile in profiles:
            trail = read(f'data/agents/{arm}/{profile["id"]}.json')
            trails[arm, profile['id']] = trail
            events = trail['events']
            require(all(e['peer'] == profile['id'] for e in events if 'peer' in e),
                    'A private trail contains another profile’s own event')
            own_threads = {e['thread_id'] for e in events if e['kind'] == 'agent_started'}
            require(len(own_threads) == 1, 'Profile must have one persistent model thread')
            arm_threads.update(own_threads)
            delivered = {e['observation_id'] for e in events if e['kind'] == 'tool_response_delivered'}
            # Model-facing observations can contain shortened browser context;
            # classify responses from the complete original tool-result event.
            web_results = {e['step']: e['result'] for e in events if e['kind'] == 'web_result'}
            responses = {e['id'] for e in events if e['kind'] == 'observation'
                         and actual(web_results.get(e['step'], e['result']))}
            require(bool(responses) and responses <= delivered,
                    f'{arm}/{profile["id"]}: returned real responses lack delivery records')
        require(len(arm_threads) == 256 and not threads.intersection(arm_threads),
                'Model threads are missing or reused between arms')
        threads.update(arm_threads)
    for case in experiment['cases']:
        if 'event' not in case:
            continue
        original = [e for e in trails[case['arm'], case['agent']]['events']
                    if e['event_id'] == case['event']['event_id']]
        require(original == [case['event']], f'Curated case differs from original: {case["id"]}')
    comparison = read('proof/comparison.json')
    require(comparison['initial_fixtures_identical'] and comparison['separate_fresh_model_threads']
            and all(comparison['same_source'].values()), 'A/B source or fixture mismatch')
    audit = read('proof/full-integration-audit.json')
    require(audit['expected_plans'] == audit['audit_confirmed'] == audit['completion_confirmed'] == 829,
            'Known-plan lifecycle receipts are incomplete')
    require(audit['enforcement_errors'] == 5, 'Retained infrastructure failures changed')
    check = read('proof/mcp-delivery-20261017-final/proof.json')
    require(check['ok'] and check['model_calls'] == 0 and check['not_a_256_agent_rerun']
            and check['protected_public_write'] == 403 and check['protected_team_write'] == 200
            and check['remote_block_id'] and check['audits_confirmed'] == check['completions_confirmed'] == 2,
            'Separate real-MCP verification is incomplete')
    movie = read('film/proof/hackathon-export-check.json')
    require(movie['ok'] and movie['duration'] == 240 and movie['frames'] == 7200,
            'Expected four-minute judging video')
    require((ROOT / 'media/boundary-judging-film.mp4').stat().st_size == movie['size_bytes'],
            'Judging video size differs from verified export')
    print(json.dumps({'ok': True, 'files_hashed': len(manifest), 'distinct_profiles': 256,
                      'model_threads': len(threads), 'agent_trails': len(trails),
                      'original_run_id': experiment['run_id'], 'curated_cases_match_originals': True,
                      'known_plan_audits': 829, 'known_plan_completions': 829,
                      'infrastructure_failures_retained': 5, 'separate_mcp_check': check,
                      'movie_seconds': 240, 'new_model_calls': 0,
                      'scope': 'Evidence integrity only. Does not certify hackathon eligibility.'}, indent=2))


if __name__ == '__main__':
    main()
