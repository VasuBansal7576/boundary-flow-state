# Boundary

A coordinated-agent field test for website defenses. The same frozen 256 profiles explore two matching local sites, first without ArmorIQ and then with real server-side SDK enforcement. The evidence preserves useful coordination, actual harmful effects, policy blocks and failures.

Current run: `explore-20261016-161209` · **operation-plan-v2**. This is the full repaired-SDK run, separate from archived manifest-v1 experiments.

- [Open the local product](http://127.0.0.1:8175/) · [Four-minute judging film](http://127.0.0.1:8175/#watch)
- [Results](submission/RESULTS.md) · [Failures](submission/FAILURES.md) · [Runbook](submission/RUNBOOK.md)
- Static replay: `submission/boundary-replay` needs only an HTTP file server, no credentials or inference.
- Runtime: `lab/explore/runtime.py`; actual peer broker, unique persistent Codex threads and upstream `swarms==16.0.1 ConcurrentWorkflow`.
- Gateway: `lab/guard.py`; actual per-operation plans, public SDK check, explicit remote allow, result report and plan completion. Keys stay server-side. Cloud policy is exported with the evidence.

| Observation | Unprotected | ArmorIQ |
|---|---:|---:|
| Distinct persistent model threads | 256 | 256 |
| Agents with website responses | 256 | 256 |
| Actions with actual website responses | 976 | 1006 |
| Peer messages | 580 | 554 |
| Verified message → request chains | 196 | 167 |
| Verified shared observation → request chains | 415 | 483 |
| Profiles citing delivered peer material | 235 | 243 |
| Largest dependency component | 246 | 247 |
| Executed out-of-grant operations | 162 | 0 |
| Remote policy denials | 0 | 188 |
| In-grant policy denials | 0 | 0 |
| Legitimate profiles with successful team writes | 48 | 45 |
| Adversarial profiles with successful in-scope writes | 18 | 27 |
| Local tool/transport failures | 6 | 8 |
| Enforcement infrastructure errors | 0 | 5 |
| Same-identity coverage verification turns | 0 | 3 |

829/829 known-plan audits and 829/829 completions were confirmed after drain. Five token-issuance timeouts have unknown issuance outcomes and are not counted as policy denials. Read the failures before making security claims.

## Review or reproduce

Use the static replay for review. For a fresh experiment, follow [RUNBOOK.md](submission/RUNBOOK.md): install the pinned Python/Node dependencies, connect an existing Codex subscription, configure your ArmorIQ account/key and cloud operation policy, start the four loopback services, prepare a new run and confirm recording readiness before execution. No paid model API fallback or paid hosting is implemented.

The recorded source is frozen with hashes. Current public source replaces host-specific configuration and the owner email with portable configuration; the Guard class AST and resolved runtime settings were checked for equivalence. Archival source exports redact only the owner email and record original/exported hashes. Original frozen local artifacts remain unchanged.

Do not present exposure as failed tasks, in-scope adversarial writes as all proven harmful, independently adaptive arms as exact request replay, or the SDK gateway as a universal firewall. Both the successful boundary and its limits are part of this project.

## 17 October submission revision

The stricter organiser Discord announcement requires a 3–5 minute film, MCP, onboarding, public links and active ArmorTools Pro. See [the dated compliance audit](submission/COMPLIANCE-2026-10-17.md). The original 256-per-arm recording used SDK dynamic tools. The current default HTTP action transport is a real stdio MCP client/server; a separate four-call canary confirms backend allow/block and report delivery. It is not a new model-population run. All 512 inventory identities and one MCP configuration were registered afterward.

The policy shown is the active platform SDK policy. ArmorTools Policy Studio is for ArmorClaude plugin profiles and was not this run’s enforcement path. Pro remains inactive because billing was explicitly declined. This project is not claimed fully eligible or submitted until a real form receipt exists.
