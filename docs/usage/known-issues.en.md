---
kind: usage
title: Known Issues
description: Confirmed ATP platform limitations, user impact, workarounds, and exit criteria.
owner: template-maintainer
stability: living
last_reviewed: 2026-10-29
---

<p align="center">
  <a href="known-issues.md">한국어</a> ·
  <a href="known-issues.en.md">English</a>
</p>

# Known Issues

This document tracks confirmed limitations that affect current user behavior. Design rationale belongs in ADRs, implemented changes in Changes, and unaccepted host-capability proposals in Backlog.

| ID | Surface | Status | User impact |
|---|---|---|---|
| ATP-KI-001 | Codex CLI 0.149.1 | Not reproduced on 0.165.0 (2026-10-29) | Team execution runs through Codex built-in subagents. some staggered results were missing on 0.149.1; not reproduced on 0.165.0 |
| ATP-KI-002 | Codex App/IDE | Verification gap | Managed orchestration support is `unknown` because the same maintainer smoke has not been run |
| ATP-KI-003 | Codex formal wait/wakeup | Upstream capability gap | A timeout-free targeted subscription cannot be used as ATP's formal scheduling mode |
| ATP-KI-004 | Codex connection smoke (surface/version unmeasured) | Obsolete (2.19.0) | Child lacked `update_plan`; 2.19.0 removed the bind step, so there is no user impact |

## ATP-KI-001 — Codex CLI managed all-results barrier failure

> **Status update 2026-10-29 (2.19.0, [ADR-0026](../adr/ADR-0026-codex-builtin-subagents-without-marker.md))**: on Codex, `codex-team` uses Codex built-in subagents without any marker or add-on. The deployed profile is `formal_adapter_enabled: false`, `manual_wait_polling_supported: false`, `host_managed_subagent_orchestration: supported`, `team_execution_enabled: true`. As in the 2026-08-26 observation below, the built-in barrier once delivered only 1 of 2 staggered results. This caveat is not a gate. The records below are preserved history.

> **Recheck 2026-10-29 (Codex CLI 0.165.0)**: running a two-agent parallel `$atp:task` on the 2.19.0 install, both agents completed and were collected.

### Historical symptom and scope (2026-08-26)

In the isolated Codex CLI 0.149.1 smoke, the terminal-only one-agent case and the delayed terminal after a nonterminal `MESSAGE` passed. The staggered two-agent case with `fork_turns: none` failed with `spawn_calls=2` and `terminal_deliveries=1`: only the fast child result was delivered before the parent turn ended. The queue→wait→refill bounded-pool candidate also passed the terminal-only flat, nested, denial-refill, and source/install parity checks, but failed the saturated nonterminal barrier, active-wait steering, approval same-identity continuation, and cancellation checks. The ATP 2.15.0 tested-CLI profile at that time was therefore `formal_adapter_enabled: false`, `manual_wait_polling_supported: false`, `host_managed_subagent_orchestration: unsupported`, `team_execution_enabled: false`. No separate bounded-pool capability axis or execution mode was added at that time.

The [official OpenAI Subagents documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents) describes local Codex subagent workflows. This issue does not claim that the official feature is absent. It records an empirical gap between that product description and ATP's multi-child all-results correctness contract, reproduced on CLI 0.149.1.

### Current user impact

- `$atp:task` spawns advisors and workers through Codex built-in subagents. There is no extra add-on, hook trust, or execution-environment scope requirement.
- Mark completion only after every requested child result is verified and collected.
- The marker gate and the `atp-codex-hooks` add-on used through 2.18.0 were removed in 2.19.0. If installed, uninstall with `codex plugin remove atp-codex-hooks`.

### History (before 2.19.0)

After 2026-08-26, ATP went through a queue→wait→refill candidate and a hook-based variant, and in 2.18.0 enabled team execution limited by a marker (ADR-0025). 2.19.0 removed that gate and simplified to Codex's built-in behavior. See [ADR-0026](../adr/ADR-0026-codex-builtin-subagents-without-marker.md) for the rationale and [ADR-0024](../adr/ADR-0024-host-managed-subagent-orchestration.md) for the earlier decision.

### Built-in exit criteria

This caveat closes when, on the same Codex surface and version, the release maintainer's terminal-only one-agent, delayed nonterminal-plus-terminal one-agent, and staggered-terminal two-agent smokes all pass, requested, spawned, terminal, and collected counts match, and manual wait/list/interrupt/recovery actions are zero.

Evidence: the [official OpenAI Subagents documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents), [upstream issue draft](../backlog/codex-cli-collaboration-await-v1.md), [ADR-0024](../adr/ADR-0024-host-managed-subagent-orchestration.md), and the [0.149.1 sanitized evidence manifest](../../tests/runtime-behavior/evidence/codex-cli-0.149.1-20260826.json).

## ATP-KI-002 — Codex App/IDE capability status unknown

There is an official product description but no ATP release smoke for these surfaces. ATP therefore keeps the status `unknown` instead of inferring `supported` or `unsupported`. The deployed profile and task preflight determine user behavior. Maintainers can update the status after preserving evidence from the same three isolated smokes.

## ATP-KI-003 — Formal timeout-free wait/wakeup unavailable

The tested Codex collaboration surface does not provide the complete ATP formal-mode contract: timeout-free suspend, targeted wait-any/all, stable event identity, deduplication, completion coalescing, compact deltas, and await cancellation. ATP does not promote bounded waits or repeated polling to a formal adapter.

This limitation is separate from host-managed orchestration. The formal improvement proposal and acceptance criteria are tracked in the [Codex CLI collaboration await v1 backlog](../backlog/codex-cli-collaboration-await-v1.md).

## ATP-KI-004 — `update_plan` unavailable to a connection-smoke child

In the [actual one-agent connection smoke](./codex-connection-smoke.en.md) on 2026-09-08, the child reported that `update_plan` was unavailable, so the bind plan call required by the profile at that time did not run. The actual spawn response and `FINAL_ANSWER` established `requested=accepted=terminal=collected=1`; the child reported connected status, a cwd matching the project, and zero mutations. The UI surface and version were not independently measured.

2.19.0 removed the bind step, so this observation no longer affects user behavior. It is kept as history only.

## Reporting policy

New entries include the reproduction surface and version, user impact, a safe workaround, exit criteria, and evidence links. Public docs do not include raw user conversations, authentication material, actual session transcripts, or local absolute paths.
