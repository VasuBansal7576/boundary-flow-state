# ArmorIQ integration audit — full repaired run

Run `explore-20261016-161209` executed all 256 profiles on each site using the repaired operation-plan-v2 gateway. [Full results](submission/RESULTS.md) and [failure disclosures](submission/FAILURES.md) separate this evidence from the archived manifest-v1 run.

The website derives operation, principal and scope. A distinct SDK client/session captures each real operation and its actual arguments, calls public `session.check()` in SDK mode, and executes only after a verifiable remote explicit allow. Each check owns its immutable plan/session; actual execution or failure is reported against that plan and `complete_plan()` is called. Response hooks retain sanitized enforcement IDs and observed audit/status HTTP receipts, not JWTs or keys. A successful SDK return alone is not treated as proof of report delivery.

The run recorded 829 real remote decisions, 188 policy denials with request IDs, 829/829 confirmed known-plan audits, and 829/829 confirmed known-plan completions. Five token-issuance timeouts failed closed; issuance outcome is unknown and no client plan ID was available. They are infrastructure failures, outside known-plan completion denominators. Reporting was asynchronous and its queue was explicitly drained before capture and evidence finalization.

The organization policy `Boundary — local approved operations` defaults to block and explicitly allows eight named operation categories. `policy-configuration.json` contains the token-free policy snapshot. This is a custom website operation gateway supported by SDK mode, not an MCP proxy or verification of an external agent’s private reasoning. The application supplies resource-category mappings. General arbitrary-argument binding, token forgery/replay coverage and universal semantic safety were not demonstrated. All profiles share the same simulated team17 grant; production anonymous-user IAM is outside this controlled benchmark.

Actual SDK integration sources checked: [Sessions](https://docs.armoriq.ai/sdk/sessions), [Python SDK](https://docs.armoriq.ai/platform/sdk-cli/python-sdk), [Security model](https://docs.armoriq.ai/sdk/concepts/security-model), [ADK cookbook](https://docs.armoriq.ai/cookbook/adk-agent). The installed SDK is pinned at 0.6.10. Local execution after an SDK check is supported; public hosting is unnecessary.

Evidence: `data/exploration/explore-20261016-161209/full-integration-audit.json`, `protected-lifecycle.jsonl`, original event logs, world snapshots, source hashes and controller-finalization sidecars. All actual returned website responses have tool-delivery records. One terminal read timed out after its model ended; its client failure and server receipt are retained rather than relabeled as a delivered response.

## Separate real MCP revision — 17 October

`lab/mcp_server.py` exposes site_http over the official mcp 2.3.0 stdio protocol. Identity and localhost arm are supplied by the trusted launcher; model-controlled inputs cannot select a principal, grant or external origin. `lab/mcp_client.py` initializes a real ClientSession, discovers the tool and invokes it. The website remains the enforcement boundary and uses the actual ArmorIQ SDK backend, with no local role verdict substituted.

`data/mcp-verification-20261017/proof.json` records an isolated integration canary: unprotected public write 200, protected team write 200, protected public rewrite 403, real remote request ID, two confirmed audits and two completions. Zero new model calls. The 16 October population is not relabeled as MCP; 17 October inventory onboarding also postdates it. Cloud registry health is Unknown, and its generated detail link returned not found; local protocol verification succeeded.

The platform policy and ArmorTools ArmorClaude Policy Studio are separate products/configuration surfaces. No local plugin policy activation is claimed.
