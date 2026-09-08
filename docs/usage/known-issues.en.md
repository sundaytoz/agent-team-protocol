---
kind: usage
title: Known Issues
description: Confirmed ATP platform limitations, user impact, workarounds, and exit criteria.
owner: template-maintainer
stability: living
last_reviewed: 2026-08-26
---

<p align="center">
  <a href="known-issues.md">한국어</a> ·
  <a href="known-issues.en.md">English</a>
</p>

# Known Issues

This document tracks confirmed limitations that affect current user behavior. Design rationale belongs in ADRs, implemented changes in Changes, and unaccepted host-capability proposals in Backlog.

| ID | Surface | Status | User impact |
|---|---|---|---|
| ATP-KI-001 | Codex CLI 0.149.1 | Resolved within declared scope (2026-09-08) | Sessions with the `atp-codex-hooks` add-on installed and trusted run team execution through the hook-guarded bounded pool; without the add-on, on Windows, or in App/IDE the Tier B behavior remains |
| ATP-KI-002 | Codex App/IDE | Verification gap | Managed orchestration support is `unknown` because the same maintainer smoke has not been run |
| ATP-KI-003 | Codex formal wait/wakeup | Upstream capability gap | A timeout-free targeted subscription cannot be used as ATP's formal scheduling mode |

## ATP-KI-001 — Codex CLI managed all-results barrier failure

> **Status update 2026-09-08 (ADR-0025)**: the built-in barrier failure stands, but the hook-guarded bounded pool shipped in the opt-in add-on `atp-codex-hooks` passed qualification as the all-results barrier provider, so this issue is **resolved within the declared scope**. A Unix/`python3` session with the add-on installed and hook trust granted in the TUI runs with `host_managed_subagent_orchestration: supported` and `team_execution_enabled: true`. Sessions without the add-on, with untrusted hooks, on Windows, or in App/IDE have no marker and keep the Tier B / blocked behavior described below. Read the symptom, impact, and workaround sections as describing **out-of-scope sessions**.

### Symptom and scope

In the isolated Codex CLI 0.149.1 smoke, the terminal-only one-agent case and the delayed terminal after a nonterminal `MESSAGE` passed. The staggered two-agent case with `fork_turns: none` failed with `spawn_calls=2` and `terminal_deliveries=1`: only the fast child result was delivered before the parent turn ended. The queue→wait→refill bounded-pool candidate also passed the terminal-only flat, nested, denial-refill, and source/install parity checks, but failed the saturated nonterminal barrier, active-wait steering, approval same-identity continuation, and cancellation checks. The deployed tested-CLI profile therefore remains `formal_adapter_enabled: false`, `manual_wait_polling_supported: false`, `host_managed_subagent_orchestration: unsupported`, `team_execution_enabled: false`. No separate bounded-pool capability axis or execution mode was added.

The [official OpenAI Subagents documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents) describes local Codex subagent workflows. This issue does not claim that the official feature is absent. It records an empirical gap between that product description and ATP's multi-child all-results correctness contract, reproduced on CLI 0.149.1.

### User impact

- A general `$atp:task` request automatically degrades to `tier_b_sequential` and discloses that mode in one line. Its result is not presented as an independent advisor or subagent opinion.
- When actual independent subagent execution is part of the deliverable, ATP stops at `blocked_explicit_independence` and offers rerunning on a supported host, explicitly converting to non-independent Tier B, or cancelling.
- ATP does not hide this limitation with manual wait/list polling or automatic retry, interrupt, or fallback.

### Workarounds

- Continue with Tier B sequential self-checks when independence is not required.
- When independence is required, rerun on a host where the orchestration contract is verified. Codex App/IDE are not treated as supported workarounds because ATP has not run the same smoke there.

### Bounded-pool candidate qualification

- The saturated A rerun kept running 3/pending 2 at `MESSAGE`, performed zero message-triggered slot releases/refills, and later received the same child's terminal. It nevertheless stopped at requested 5, attempts/accepted 3/3, terminal 3, collected 1, wait 2, with no parent final. The first unsaturated run was superseded and is not a PASS.
- B accepted one steering queue request during an active wait but did not deliver it to the scheduler. It ended at requested/accepted 5/5, terminal/collected 4/4, wait 5, send/follow-up/list/interrupt 0, and no parent final.
- C relayed an actual interactive approval overlay and one reject decision, but the target child ended as `turn_aborted`, without same-identity continuation or a target terminal. The companion delivered one terminal, wait count was 2, no parent final was emitted, and the harmless marker was absent.
- D accepted a cancellation queue request at running 3/pending 2 but did not deliver it to the scheduler, which then spawned both pending tasks. It ended at accepted 5, terminal/collected 4/4, wait 4, interrupt 0, and no parent final. External smoke cleanup is not scheduler cancellation.
- Source/install skill byte hash parity at `bcfbdd0f0f7d066233155faebdec9aadb78de73fc2bfa057b3c7aec740eee146` and the installed flat/nested/denial-refill regressions passed, but cannot offset the failures above.

Although the official OpenAI documentation describes interactive approval overlays and queued control behavior, actual ATP qualification is authoritative. The bounded pool is not yet a supported workaround, and the built-in all-results P0 remains open.

### Exit criteria

On the same Codex surface and version, the release maintainer's terminal-only one-agent, delayed nonterminal-plus-terminal one-agent, and staggered-terminal two-agent smokes must all pass. Requested, spawned, terminal, and collected counts must match, with zero manual wait/list/interrupt/recovery actions.

Bounded-pool promotion is judged along the four independent axes defined in [the hook-guarded bounded pool backlog](../backlog/codex-cli-hook-guarded-bounded-pool.md) §Phase 3. The required axes are A (all-results barrier: consume every already-delivered terminal, refill only after a terminal, record capacity denials durably, and open the root Stop barrier only once every result is collected) and D (the declared packaging and runner scope). When A and D pass, the profile is promoted within the declared scope. B (steering and cancellation delivery into an active wait) and C (same-identity continuation after an approval decision) are independent axes recorded with their own values; an unknown or unsupported value on either does not block promotion of A and D. Instead, only requests that require those axes take the blocked or user-decision path.

Current axis state (2026-09-08): A passed on the 2026-08-31 rerun, C is supported, B is unknown (not yet measured on an interactive PTY), and D was resolved by moving the candidate hook into the opt-in add-on `atp-codex-hooks`. A Codex consumer who installs only the base `atp` plugin receives no hook, so the "Hooks need review" trust prompt never appears; when the add-on is absent, `$atp:task` records `skip: no-codex-hooks` and continues. The deployed profile did not change with this split. See the [add-on guide](../../plugins/atp-codex-hooks/docs/codex-hooks-usage.md) (Korean-first).

Evidence: the [official OpenAI Subagents documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents), [upstream issue draft](../backlog/codex-cli-collaboration-await-v1.md), [ADR-0024](../adr/ADR-0024-host-managed-subagent-orchestration.md), and the [0.149.1 sanitized evidence manifest](../../tests/runtime-behavior/evidence/codex-cli-0.149.1-20260826.json).

## ATP-KI-002 — Codex App/IDE capability status unknown

There is an official product description but no ATP release smoke for these surfaces. ATP therefore keeps the status `unknown` instead of inferring `supported` or `unsupported`. The deployed profile and task preflight determine user behavior. Maintainers can update the status after preserving evidence from the same three isolated smokes.

## ATP-KI-003 — Formal timeout-free wait/wakeup unavailable

The tested Codex collaboration surface does not provide the complete ATP formal-mode contract: timeout-free suspend, targeted wait-any/all, stable event identity, deduplication, completion coalescing, compact deltas, and await cancellation. ATP does not promote bounded waits or repeated polling to a formal adapter.

This limitation is separate from host-managed orchestration. The formal improvement proposal and acceptance criteria are tracked in the [Codex CLI collaboration await v1 backlog](../backlog/codex-cli-collaboration-await-v1.md).

## Reporting policy

New entries include the reproduction surface and version, user impact, a safe workaround, exit criteria, and evidence links. Public docs do not include raw user conversations, authentication material, actual session transcripts, or local absolute paths.
