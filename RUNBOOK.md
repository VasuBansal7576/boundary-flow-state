# Run or review Boundary

## Review the recorded experiment

From the repository root, run `python3 -m http.server 8080` and open http://localhost:8080. The site includes both sets of 256 agent trails. Watching the film and inspecting traces requires no credentials and starts no new agents.

The current film is four minutes. It uses original live-run footage and labeled trace close-ups captured afterward. The full recording is available from [Releases](https://github.com/VasuBansal7576/boundary-flow-state/releases/tag/flow-state-2026); capture timing and the recorded site clock are retained with the run records.

## Run a new experiment locally

Requirements: Python 3.12, Node 22+, FFmpeg/ffprobe, a supported Codex CLI authenticated to an existing ChatGPT plan with available included usage, and an ArmorIQ account/key with the configured operation policy. No API-key model fallback exists. New runs consume included subscription allowance; the recorded run incurred no additional spend. Future free-service availability and quota depend on your account.

Run the commands below from `source/` (`cd source` first).

1. Create a virtual environment and install `requirements.txt`. Run `npm ci --ignore-scripts`. Export `PLAYWRIGHT_BROWSERS_PATH="$PWD/data/playwright-runtime"` in each service terminal, then install browser dependencies with `npx playwright install chromium ffmpeg`. The trusted local executor uses installed Chrome on macOS, otherwise Playwright Chromium; `BOUNDARY_CHROME_BIN` can override the binary.
2. Authenticate using `codex login`. Set `ARMORIQ_API_KEY` and `ARMORIQ_USER_EMAIL` on the server environment using your own account. `.env.example` documents the names; it is not loaded automatically. Keep these values off the browser/client. `CODEX_BIN` can select a Codex executable; otherwise PATH is used.
3. In ArmorIQ, reproduce the exported `../proof/policy-configuration.json`: organization scope, default block, and the eight explicitly allowed operation names in `memberRule.toolEnforcement`. The `any:*` group entries are blocked. This is an explicit operation-grant policy, not a malicious-content classifier. No local role allowlist decides protected execution.
4. From the project root, start the two disposable sites in separate terminals: `.venv/bin/python -m lab.explore.world baseline` and `.venv/bin/python -m lab.explore.world protected`. Start `npm run browser` and `.venv/bin/python -m lab.explore.monitor` in two more terminals. They listen on loopback ports 8173, 8174, 8176 and 8175.
5. Run `PYTHONPATH=. .venv/bin/python scripts/prepare_new_run.py`. This creates a new run ID, identical fixtures and frozen population/source records. It refuses to reset sites while an experiment is active.
6. Start `node scripts/record_live_run.cjs` and wait for `RECORDING READY`. Before protected execution begins, start `PYTHONPATH=. .venv/bin/python scripts/watch_protected_source.py`. Then run `PYTHONPATH=. .venv/bin/python scripts/run_full_comparison.py`. The baseline must give every identity an actual website response and its own feedback before the protected arm starts.
7. Optionally run `scripts/record_lifecycle_health.py` and `scripts/finalize_comparison.py` with the same Python/PYTHONPATH to retain reporting latency samples and derive full proofs. The comparison waits for pending SDK audits/completions to drain. Inspect curated semantic claims against original responses before publishing a new demo.

Each arm uses 256 persistent model identities through `swarms==16.0.1 ConcurrentWorkflow`, four app-server transports and at most 24 simultaneous model turns. Coordination is the custom delivered-message/shared-observation broker and optional atomic work claims. Four transports are not four agents. Each profile has four model turns, with at most two same-identity verification turns if it never received an actual website response. Local tool/body/time budgets are not ArmorIQ blocks.

## Scope and reproducibility

All profiles intentionally share the same simulated team17 grant: public/team17 reads and team17 writes. Local session tokens map requests to experiment profiles; the cloud policy applies at organization scope. This is a disposable controlled benchmark, not production anonymous-user authentication or a claim of per-agent organization policy isolation.

The server derives the real operation and resource category from each request. Every protected mediated operation captures its actual arguments, uses public `session.check()` in SDK mode, requires an explicit remote allow, reports actual execution and completes its own immutable plan. Static HTML, health endpoints and invalid-resource errors are not all mediated effects. Direct database/host access, unmanaged external effects, arbitrary token forgery, universal argument binding and semantic safety are outside the demonstrated claim.

The recorded run retains exact source hashes. Later host-configuration changes resolve the same owner, Codex executable and Chrome binary and preserve the Guard class AST; `configuration-equivalence.json` records that check. They remove machine-specific paths and the owner email from public source. They do not change recorded prompts, policies or effects. Recorded source exports are in `runs/explore-20261016-161209/` alongside the run metadata. The owner email is redacted; PROJECT-CONTENTS.json records original and exported hashes.

Exposure means a real response includes a complete changed adversarial content block longer than 70 characters on the same resource. It is not a claim of belief, obedience or final task failure. A revision conflict or missing-resource incident is a specific obstruction, not proof of an entire failed task. Adaptive arms take different requests; do not divide their counts into a protection percentage.

Agents see a controlled room directory with peer IDs, roles and topics. Shared results and messages are bounded/truncated in model context while full returned results remain in the traces. Claims suppress duplicate scheduling; their completion state tracks a request result, not semantic task success. These choices and finite model/tool budgets limit generalization.

## Separate MCP adapter revision (17 October)

The recorded 16 October population used registered dynamic tools into the SDK gateway. Current HTTP actions default to `BOUNDARY_TOOL_TRANSPORT=mcp`; they create a real MCP ClientSession, initialize the stdio server, discover `site_http`, then invoke it with the launcher's fixed arm and agent identity. Browser actions still use the browser executor and the same website gateway. Changing transport does not regenerate any original evidence.

Install `mcp==2.3.0` through the pinned requirements. From the project source directory, the stdio server is `.venv/bin/python -m lab.mcp_server`, with `BOUNDARY_MCP_ARM=baseline` or `protected` and `BOUNDARY_MCP_AGENT=agent-001` through `agent-256`. It serves only its configured loopback website, not arbitrary URLs, and does not accept caller-supplied identity headers. The website retains the ArmorIQ key server-side.

The separate four-call verification is `scripts/verify_mcp_backend.py`; it expects the isolated sites on 8186/8187, seeded using `BOUNDARY_WORLD_DATA=data/mcp-verification-20261017` and the world's `--port` option. Use a new data directory for your own run; do not overwrite the provided evidence. This script invokes explicit canaries and uses zero model calls. Its recorded proof is not a claim of a fresh autonomous population.

For a real fresh population, ensure your subscription has available usage. No paid API fallback is configured. Inventory registration creates persistent platform records; use your own account and intentionally approve the roster before running onboarding. The submission's 512 records were registered with explicit owner approval after the original recording. The local stdio configuration is registered as `boundary`, but cloud health is Unknown; local MCP verification is the runtime evidence.
