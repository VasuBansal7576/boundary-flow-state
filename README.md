# Boundary

A coordinated-agent field test for website defenses. The same 256 frozen profiles explore matching synthetic websites, first unprotected and then with real ArmorIQ SDK enforcement. Useful work, shared sources, harmful effects, backend blocks and failures remain inspectable.

The site at the repository root is a credential-free **recorded evidence replay**. Playback does not start fresh agent inference. Run a static HTTP server here to inspect it locally. Current implementation is in `source/`; follow `RUNBOOK.md` for your own sandbox run with available subscription usage and your own ArmorIQ credentials.

## What the evidence says

- 256 fresh model threads per arm, 32 objective families × 8 topics. Upstream `swarms==16.0.1 ConcurrentWorkflow` schedules participants; our peer broker supplies observations, messages, work claims and traceable dependencies. 24 model-turn slots; not 256 simultaneous model calls.
- Recorded run: `explore-20261016-161209`, 16 October 2026, operation-plan-v2. Unprotected: 162 out-of-grant operations execute. Protected: 188 real backend denials, zero observed out-of-grant executions. These independently adaptive request populations do not establish a matched-request protection rate.
- Legitimate profiles with team writes: 48 / 45. Profiles exposed to changed adversary-authored content: 13 / 7. Exposure does not prove belief, obedience or final task failure.
- All 829 known-plan audits and completions confirmed after drain. Five token-issuance timeouts have unknown outcomes and are outside the known-plan denominator. Local tool/transport failures: 6 / 8.
- Real stdio MCP added and verified separately on 17 October. Four explicit canary calls, zero new model calls: unprotected public write 200, protected team write 200, protected public write 403. Not a fresh 256-agent MCP run. Inventory registrations postdate the recording.

## Submission status and provenance

The organisers’ later announcement requires a 3–5 minute film, live demo, repository, hosted video, social post and active ArmorTools Pro. Billing was declined, so Pro is inactive. The active platform SDK policy is distinct from ArmorTools’ ArmorClaude Policy Studio. We do not claim full eligibility, that a plugin policy enforced the recording, or that this entry has been submitted without a real form receipt. See the dated compliance audit.

Built during the 10–17 October event week using AI coding assistants, existing Codex subscription, ArmorIQ Python SDK 0.6.10, MCP 2.3.0, upstream Swarms 16.0.1, Playwright and HyperFrames 0.8.167. Current post-recording MCP/runtime/restart fixes are disclosed separately; original trace files are preserved. The video uses original continuous live telemetry footage and labeled native evidence/console close-ups captured afterward. Local Kokoro narration and an original synthesized music bed; ElevenLabs was not used. Additional spend: $0.

## Review

Open the site, choose an agent and arm, inspect its objective and authority, follow a received source into the sender’s trace, then inspect its next request and actual response. `RESULTS.md` and `FAILURES.md` define the measurements and limits. `proof/` contains downloadable traces and receipts. Original continuous recording and full local package are distributed as release assets because the recording exceeds GitHub’s per-file limit. No secret key, session cookie or production data is needed.
