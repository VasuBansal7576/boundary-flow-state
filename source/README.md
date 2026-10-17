# Runtime source

This folder contains the local websites, agent runner, Codex adapter, and ArmorIQ integration.

Follow the [runbook](../RUNBOOK.md) to set up a fresh experiment. The [main README](../README.md) links to the recorded demo and results.

| File | Purpose |
|---|---|
| [`lab/explore/world.py`](lab/explore/world.py) | Both copies of Signal Commons |
| [`lab/explore/runtime.py`](lab/explore/runtime.py) | Agent threads, shared messages, work claims, and tool feedback |
| [`lab/codex_pool.py`](lab/codex_pool.py) | Codex app-server connections |
| [`lab/guard.py`](lab/guard.py) | ArmorIQ backend checks and audit reporting |
| [`lab/mcp_server.py`](lab/mcp_server.py) | Local MCP tool server |
| [`lab/explore/browser.cjs`](lab/explore/browser.cjs) | Browser actions on the local sites |
| [`tests/`](tests/) | Integration-boundary and coordination tests |

Fresh runs need your own ArmorIQ credentials and available Codex subscription usage. Start the current experiment using the runbook. Older prototype modules, including `start.py`, are retained for reference.
