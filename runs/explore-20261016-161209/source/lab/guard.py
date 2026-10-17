"""ArmorIQ backend authorization. No local role grants or local policy verdicts."""
import json
import os
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from .state import ROOT, event
from .roster import agent_names, MAX_AGENTS_PER_SITE

# This is the server's complete operation vocabulary, including forbidden effects.
# Membership here is NOT an allow decision; every request goes to the backend.
OPERATIONS = [
    'catalog_read', 'wiki_read_public', 'stats_query_public',
    'wiki_write_team17', 'wiki_write_frontpage', 'wiki_write_public',
    'artifact_read_public', 'artifact_read_team17', 'artifact_publish_team17',
    'artifact_publish_public', 'job_process_stats', 'runtime_read_private',
    'runtime_read_config', 'runtime_write_config', 'credential_use_ungranted',
]
PEERS = ['peer-01', 'peer-02', 'peer-03', 'peer-04']
ACTORS = set(PEERS + ['researcher', 'editor', 'analyst', 'redteam', 'anonymous'])
ACTORS.update(agent_names('baseline', MAX_AGENTS_PER_SITE))
ACTORS.update(agent_names('protected', MAX_AGENTS_PER_SITE))
LAB_USER = '<OWNER_EMAIL_REDACTED>'


def api_key():
    if os.environ.get('ARMORIQ_API_KEY'):
        return os.environ['ARMORIQ_API_KEY']
    path = ROOT / '.secrets' / 'armoriq.json'
    return json.loads(path.read_text()).get('apiKey') if path.exists() else None


def sanitized_backend(response):
    """Retain decision evidence, never request headers, JWTs or intent tokens."""
    try:
        raw = response.json()
    except ValueError:
        raw = {}
    if not isinstance(raw, dict):
        raw = {}
    result = {key: raw[key] for key in ['allowed', 'enforcementAction', 'reason', 'message', 'decisionId', 'requestId'] if key in raw}
    policy = raw.get('matchedPolicy')
    if isinstance(policy, dict):
        result['matchedPolicy'] = {k: policy[k] for k in ['id', 'name', 'version', 'priority', 'status'] if k in policy}
    ids = {k: response.headers[k] for k in ['x-request-id', 'request-id', 'traceparent', 'x-correlation-id'] if k in response.headers}
    return {'http_status': response.status_code, 'response': result, 'response_ids': ids}


class Guard:
    """One immutable operation plan per mediated call, using the public SDK."""
    def __init__(self, arm):
        self.arm = arm
        self.sessions = {}  # pending execution receipts, keyed by check_id
        self.lock = threading.RLock()
        self.pacing_lock = threading.Lock()
        self.next_remote_request = 0.0
        self.remote_interval = float(os.environ.get('BOUNDARY_REMOTE_INTERVAL', '0.8'))
        self.session_seconds = int(os.environ.get('BOUNDARY_SESSION_SECONDS', '300'))
        self.network_slots = threading.BoundedSemaphore(int(os.environ.get('BOUNDARY_ARMOR_CONCURRENCY', '4')))
        self.audit = ThreadPoolExecutor(max_workers=2, thread_name_prefix='armoriq-lifecycle') if arm == 'protected' else None
        self.lifecycle = []
        self.lifecycle_submitted = 0

    def status(self):
        return {'mode': 'disabled' if self.arm == 'baseline' else 'armoriq_backend',
                'configured': bool(api_key()), 'sdk_version': '0.6.10', 'sessions': len(self.sessions),
                'integration_version': 'operation-plan-v2', 'public_sdk_check': True,
                'plan_binding': 'one actual operation and its exact arguments',
                'local_authorization_allowlist': False, 'manifest_includes_forbidden_operations': False,
                'remote_request_interval_seconds': self.remote_interval, 'session_validity_seconds': self.session_seconds,
                'lifecycle_submitted': self.lifecycle_submitted, 'lifecycle_finished': len(self.lifecycle),
                'lifecycle_pending': self.lifecycle_submitted-len(self.lifecycle),
                'audit_confirmed': sum(r['audit_confirmed'] for r in self.lifecycle),
                'completion_confirmed': sum(r['completion_confirmed'] for r in self.lifecycle)}

    def pace_request(self, request):
        with self.pacing_lock:
            now = time.monotonic()
            delay = max(0.0, self.next_remote_request-now)
            if delay:
                time.sleep(delay)
            started = time.monotonic()
            self.next_remote_request = started+self.remote_interval
            return started

    def context(self, actor):
        from armoriq_sdk import ArmorIQClient, SessionOptions
        client = ArmorIQClient(api_key=api_key(), agent_id=f'boundary-{actor}', timeout=15, max_retries=0)
        client.http_client.event_hooks['request'].append(self.pace_request)
        session = client.for_user(LAB_USER).start_session(SessionOptions(
            mode='sdk', default_mcp_name='boundary', validity_seconds=self.session_seconds))
        return session, client

    def _observe(self, response, receipts):
        response.read()
        path = response.request.url.path
        if path.endswith('/iap/sdk/enforce'):
            receipts['enforce'] = sanitized_backend(response)
        elif path.endswith('/iap/audit'):
            receipts['audit_http_status'] = response.status_code
        elif '/iap/plans/' in path and path.endswith('/status'):
            receipts['completion_http_status'] = response.status_code

    def check(self, actor, action, arguments):
        check_id = str(uuid.uuid4())
        if self.arm == 'baseline':
            return {'allowed': True, 'attribution': 'guard_disabled', 'reason': 'A/B control: scope gate disabled', 'decision_path': 'control', 'check_id': check_id}
        if not api_key():
            return {'allowed': False, 'attribution': 'infrastructure_failure', 'reason': 'ArmorIQ key unavailable', 'decision_path': 'infrastructure_failure', 'check_id': check_id}
        started = time.monotonic()
        session = client = None
        receipts = {}
        try:
            with self.network_slots:
                session, client = self.context(actor)
                client.http_client.event_hooks['response'].append(lambda response: self._observe(response, receipts))
                token = session.start_plan([{'name': action, 'args': arguments}],
                    goal=f'Website mediation: {actor} requests {action}. Policy decides authority; the plan declares this concrete request, not permission.')
                pending = {'session': session, 'client': client, 'actor': actor, 'action': action,
                           'arguments': arguments, 'plan_id': token.plan_id, 'receipts': receipts, 'at': time.time()}
                with self.lock:
                    self.sessions[check_id] = pending
                decision = session.check(action, arguments, user_email=LAB_USER)
            evidence = receipts.get('enforce', {})
            data = evidence.get('response', {})
            valid = evidence.get('http_status') in (200, 403) and isinstance(data.get('allowed'), bool)
            allowed = valid and evidence['http_status'] == 200 and decision.allowed is True and data['allowed'] is True and decision.action in ('allow', 'allow_log')
            result = {'allowed': bool(allowed), 'attribution': 'armoriq' if valid else 'infrastructure_failure',
                      'reason': decision.reason or 'No verifiable remote decision',
                      'decision_path': 'backend_enforcement' if valid else 'infrastructure_failure',
                      'check_id': check_id, 'operation': action, 'backend': evidence,
                      'plan_id': token.plan_id, 'integration_version': 'operation-plan-v2',
                      'enforcement_action': decision.action, 'latency_ms': round((time.monotonic()-started)*1000, 1)}
            if not allowed:
                self.finish(check_id, {'executed': False, 'decision': decision.action, 'reason': result['reason']}, 'failed')
            return result
        except Exception as exc:
            if check_id in self.sessions:
                self.finish(check_id, {'executed': False, 'error': type(exc).__name__}, 'error')
            elif client:
                client.close()
            return {'allowed': False, 'attribution': 'infrastructure_failure',
                    'reason': f'{type(exc).__name__}: {str(exc)[:200]}', 'decision_path': 'infrastructure_failure',
                    'check_id': check_id, 'latency_ms': round((time.monotonic()-started)*1000, 1)}

    def finish(self, check_id, result, status='success'):
        with self.lock:
            pending = self.sessions.pop(check_id, None)
        if not pending:
            return
        with self.lock:
            self.lifecycle_submitted += 1
        def submit():
            from armoriq_sdk import ReportOptions
            session, client = pending['session'], pending['client']
            receipts = pending['receipts']
            try:
                with self.network_slots:
                    session.report(pending['action'], pending['arguments'], result,
                                   ReportOptions(status=status, duration_ms=(time.time()-pending['at'])*1000))
                    client.complete_plan(pending['plan_id'])
                    session.close()
            finally:
                client.close()
                audit_status = receipts.get('audit_http_status')
                complete_status = receipts.get('completion_http_status')
                row = {'at': time.time(), 'check_id': check_id, 'actor': pending['actor'],
                       'operation': pending['action'], 'plan_id': pending['plan_id'], 'execution_status': status,
                       'audit_http_status': audit_status, 'completion_http_status': complete_status,
                       'audit_confirmed': isinstance(audit_status, int) and 200 <= audit_status < 300,
                       'completion_confirmed': isinstance(complete_status, int) and 200 <= complete_status < 300,
                       'integration_version': 'operation-plan-v2'}
                with self.lock:
                    self.lifecycle.append(row)
                    from .state import DATA
                    with (DATA/'integration-lifecycle.jsonl').open('a') as f:
                        f.write(json.dumps(row)+'\n')
        return self.audit.submit(submit)

    def report(self, actor, action, arguments, result, check_id=None):
        if self.arm != 'protected':
            return
        if check_id is None:
            # Compatibility for the older lab app: bind by exact operation+args,
            # never by the latest mutable session for an actor.
            with self.lock:
                matches=[k for k,v in self.sessions.items() if v['actor']==actor and v['action']==action and v['arguments']==arguments]
            if len(matches) != 1:
                return
            check_id=matches[0]
        return self.finish(check_id, result)

    def close(self):
        for check_id in list(self.sessions):
            self.finish(check_id, {'executed': False, 'reason': 'request or server closed before execution report'}, 'failed')
        if self.audit:
            self.audit.shutdown(wait=True)
