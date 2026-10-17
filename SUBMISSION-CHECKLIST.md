# Submission check — 17 October 2026

Checked at 17:30 IST against the signed-in Discord announcements, problem statement, general and help channels, the current Google Form, and the account’s plan screen.

**ArmorTools Pro is now verified active.** A published build post is still missing, and the MCP/ArmorTools demonstration needs to meet the explicit submission requirements before the entry can be called complete.

Pro update: 17 October 2026, 18:51 IST. The owner completed checkout; the existing dashboard visibly shows Pro. Earlier Free-plan and stalled-checkout notes describe the previous state.

## Current instructions

- [13 October submission announcement](https://discord.com/channels/1450796662334423135/1554827636646088714/1559618286000410625): deadline **17 October 2026, 11:59 PM IST**. Keep the demo available **17–21 October**. Main video: **3–5 minutes**, hosted on YouTube, Loom or Vimeo. Every team member must have active ArmorTools Pro; entries without it will not be judged.
- [10 October problem statement](https://discord.com/channels/1450796662334423135/1558334610507567174): an agent, at least one real MCP server, real ArmorIQ allows and blocks, platform-issued credentials, registered agents/MCPs, sandbox effects, and disclosure of existing libraries and AI assistance.
- [Current submission form](https://forms.gle/fxkXnY8xgeyZ3QQX6): team details; ArmorTools emails and Pro status; project, GitHub, demo and video links; how ArmorIQ was used; ElevenLabs usage; an X/LinkedIn build post and confirmation of `#FlowStateHackathon`. Optional feedback, ambassador interest and coding-agent choices follow.

The later announcement and current form specify 3–5 minutes, replacing the older 90-second instruction. The public landing page still says MCP is optional; the released Discord rules require it. Both video versions are retained, and the current implementation includes real MCP transport.

The organiser confirmed in the help channel on 17 October at 10:01 IST that submissions use the announced Google Form, rather than Hackbriven’s submission round. No later waiver of the Pro or post requirements was found in the channels checked.

## What is ready

| Requirement | Evidence and status |
|---|---|
| Active ArmorTools Pro | Verified on the existing dashboard on 17 October 2026, 18:51 IST |
| Public source and setup | [Repository](https://github.com/VasuBansal7576/boundary-flow-state), plain README, pinned dependencies, local runbook |
| Available demo | [Interactive recorded experiment](https://vasubansal7576.github.io/boundary-flow-state/); no credentials required |
| Main judging video | [Unlisted four-minute film](https://youtu.be/PTKfH2pNLgU); verified playback and 4:00 duration |
| Agent population | 256 frozen profiles per arm, 512 distinct model threads, all 512 trails available |
| Coordination proof | Agent 084 creates a report; 060 relays its returned ID; 204 cites the delivered message and requests that report |
| Real enforcement | 188 recorded remote denials; explicit remote allow required before protected execution; 829 known-plan audits and completions confirmed |
| Failures | Accepted in-scope malicious content, exposure, local failures, five issuance timeouts and reporting delays are retained |
| MCP | Real stdio adapter, discovery and calls. A fresh separate four-request check passed on 17 October at 17:21 IST, including backend allow/block and two confirmed audit/completion pairs |
| Inventory | 512 agent registrations and one MCP registration verified earlier on 17 October. Cloud MCP health was Unknown; local protocol calls passed |
| Tests | All 37 tests passed in both the working project and exported runtime source |
| ElevenLabs | Not used; narration and media were produced locally. Answer No |
| Other tools | Codex subscription, Swarms ConcurrentWorkflow, custom peer broker, ArmorIQ SDK, MCP, HyperFrames and local Kokoro are disclosed |
| Recording and downloads | [Release assets](https://github.com/VasuBansal7576/boundary-flow-state/releases/tag/flow-state-2026), including full recording and checksums |

## What remains

1. **The build post.** No X/LinkedIn post has been published. A prepared post is available locally. The form requires a real post link and hashtag confirmation; neither can be truthfully supplied yet.
2. **Complete the policy demonstration.** The recorded population used server-side SDK policies through `platform.armoriq.ai`. The later announcement asks to show `tools.armoriq.ai` and ArmorTools Policy Studio. No plugin profile enforced this experiment. Another participant asked the same SDK-versus-Policy-Studio question in general on 17 October; no organiser answer was visible in the checked discussion. The current film discloses the distinction.
3. **Final review and submission.** The team and project fields are prepared in a saved form draft. The saved form originally marked Pro as No; it must be changed to Yes before final review, now that Pro is verified. Navigation stopped at the required social confirmation. No final submission or receipt exists.

## Limits judges should see

The hosted product is an interactive replay of a real experiment. It does not let visitors launch paid models or exercise the ArmorIQ backend. The code and runbook support local fresh runs with the visitor’s own credentials and included subscription usage. Whether a replay satisfies the judges’ live-demo expectation is not established by the form.

The original 16 October population used dynamic tools into the SDK gateway. MCP was added and checked separately on 17 October with **zero new model calls**. Registration also happened afterward. Neither the film nor this checklist claims a new 256-agent MCP run. The model threads, event logs, and captured website effects remain unchanged.

No eligibility claim, build post or form submission has been made. Additional spend remains $0.
