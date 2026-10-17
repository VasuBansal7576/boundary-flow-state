"""Distinct registered identities for the concurrent experiment."""
MAX_AGENTS_PER_SITE = 256


def agent_names(arm, count=128):
    if arm not in ['baseline', 'protected'] or not 1 <= count <= MAX_AGENTS_PER_SITE:
        raise ValueError('Unsupported arm or agent count')
    return [f'{arm}-agent-{i:03}' for i in range(1, count + 1)]
