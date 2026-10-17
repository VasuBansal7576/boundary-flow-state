# Boundary

We send 256 different agent profiles into two copies of a collaboration website. One has no ArmorIQ enforcement. The other uses ArmorIQ to check requests before the website executes them. We compare useful work, damage, blocked requests, and failures.

[Open the demo](https://vasubansal7576.github.io/boundary-flow-state/) · [Watch the four-minute video](https://youtu.be/PTKfH2pNLgU) · [Download the current project](https://github.com/VasuBansal7576/boundary-flow-state/archive/refs/heads/main.zip)

## How it works

The agents explore Signal Commons, a local website with documents, team workspaces, statistics tools, and publishing. Each agent has its own Codex thread, objective, memory, and tool responses. They share findings and claim work through a peer broker. The traces connect shared messages to later requests.

The runner uses [Swarms](https://github.com/kyegomez/swarms) `ConcurrentWorkflow` with 24 model-turn slots. All 256 profiles run on the unprotected site first, then on the protected site with fresh threads. The agents choose their actions from what they find.

## What happened

Recorded on 16 October 2026, run `explore-20261016-161209`.

| Observation | Unprotected | ArmorIQ |
|---|---:|---:|
| Actions outside the agents’ permission that executed | 162 | 0 |
| ArmorIQ policy denials | — | 188 |
| Legitimate agents that wrote team content | 48 | 45 |
| Legitimate agents receiving changed adversary-written content | 13 | 7 |
| Local tool or transport failures | 6 | 8 |

The agents adapt independently on each site, so these counts are not a matched-attack success rate. Receiving adversary-written content does not prove an agent followed it. [Results](RESULTS.md) and [failures](FAILURES.md) explain the measurements, timeouts, and reporting delays.

**The recorded 256-agent run used the ArmorIQ SDK gateway.** MCP was added afterward and checked separately with four requests and no new model calls. That check allowed a team write and blocked a public rewrite. See the [integration audit](source/INTEGRATION-AUDIT.md).

## Files

| Path | Contents |
|---|---|
| [`source/`](source/) | Both websites, Codex adapter, swarm runner, MCP adapter, and tests |
| [`data/agents/`](data/agents/) | All 256 agent trails for each website |
| [`proof/`](proof/) | Original request logs, messages, policy decisions, coordination graphs, and audit receipts |
| [`runs/`](runs/) | Supporting run records, site snapshots, and source captured during execution |
| [`film/`](film/) | Editable video, script, narration, footage cuts, and render instructions |
| [`PROJECT-CONTENTS.json`](PROJECT-CONTENTS.json) | File locations and hashes for the published run and film assets |

The full 69-minute recording exceeds GitHub’s per-file limit, so it lives in [Releases](https://github.com/VasuBansal7576/boundary-flow-state/releases/tag/flow-state-2026), alongside the finished video and original packaged export. Credentials, account screenshots, installed dependencies, and caches are excluded.

## Run locally

To browse the recorded demo, run this from the repository root:

```sh
python3 -m http.server 8080
```

Open <http://localhost:8080>. Playback needs no account or API key and starts no new agents.

For a fresh experiment, follow the [runbook](RUNBOOK.md). You need your own ArmorIQ credentials and a Codex subscription with available usage. The recorded experiment used an existing subscription and cost $0 extra.
