---
kind: usage
title: Known Issues
description: Confirmed ATP platform limitations, user impact, workarounds, and exit criteria.
owner: template-maintainer
stability: living
last_reviewed: 2026-08-20
---

<p align="center">
  <a href="known-issues.md">한국어</a> ·
  <a href="known-issues.en.md">English</a>
</p>

# Known Issues

This document tracks confirmed limitations that affect current user behavior. Design rationale belongs in ADRs, implemented changes in Changes, and unaccepted host-capability proposals in Backlog.

| ID | Surface | Status | User impact |
|---|---|---|---|
| ATP-KI-001 | Codex CLI 0.147.0 | Open | Independent subagent team execution is disabled for the tested CLI |
| ATP-KI-002 | Codex App/IDE | Verification gap | Managed orchestration support is `unknown` because the same maintainer smoke has not been run |
| ATP-KI-003 | Codex formal wait/wakeup | Upstream capability gap | A timeout-free targeted subscription cannot be used as ATP's formal scheduling mode |

## ATP-KI-001 — Codex CLI managed all-results barrier not verified

### Symptom and scope

In the isolated ATP 2.15.0 smoke on Codex CLI 0.147.0, the terminal-only one-agent case passed, but the delayed terminal after a nonterminal update and the staggered two-agent case ended the parent before all terminal results were delivered. The deployed tested-CLI profile is therefore `host_managed_subagent_orchestration: unsupported`, `team_execution_enabled: false`.

The [official OpenAI Subagents documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents) describes local Codex subagent workflows and says that the main thread collects requested results. This issue does not claim that the official feature is absent. It records an empirical gap between that product description and the full all-results correctness contract ATP 2.15.0 could verify in the isolated CLI 0.147.0 smoke.

### User impact

- A general `$atp:task` request automatically degrades to `tier_b_sequential` and discloses that mode in one line. Its result is not presented as an independent advisor or subagent opinion.
- When actual independent subagent execution is part of the deliverable, ATP stops at `blocked_explicit_independence` and offers rerunning on a supported host, explicitly converting to non-independent Tier B, or cancelling.
- ATP does not hide this limitation with manual wait/list polling or automatic retry, interrupt, or fallback.

### Workarounds

- Continue with Tier B sequential self-checks when independence is not required.
- When independence is required, rerun on a host where the orchestration contract is verified. Codex App/IDE are not treated as supported workarounds because ATP has not run the same smoke there.

### Exit criteria

On the same Codex surface and version, the release maintainer's terminal-only one-agent, delayed nonterminal-plus-terminal one-agent, and staggered-terminal two-agent smokes must all pass. Requested, spawned, terminal, and collected counts must match, with zero manual wait/list/interrupt/recovery actions.

Evidence: the [official OpenAI Subagents documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents), [2.15.0 Changes](../changes/2026-08-19-codex-managed-subagent-orchestration.md), [ADR-0024](../adr/ADR-0024-host-managed-subagent-orchestration.md), and the [sanitized evidence manifest](../../tests/runtime-behavior/evidence/codex-cli-0.147.0-20260819.json).

## ATP-KI-002 — Codex App/IDE capability status unknown

There is an official product description but no ATP release smoke for these surfaces. ATP therefore keeps the status `unknown` instead of inferring `supported` or `unsupported`. The deployed profile and task preflight determine user behavior. Maintainers can update the status after preserving evidence from the same three isolated smokes.

## ATP-KI-003 — Formal timeout-free wait/wakeup unavailable

The tested Codex collaboration surface does not provide the complete ATP formal-mode contract: timeout-free suspend, targeted wait-any/all, stable event identity, deduplication, completion coalescing, compact deltas, and await cancellation. ATP does not promote bounded waits or repeated polling to a formal adapter.

This limitation is separate from host-managed orchestration. The formal improvement proposal and acceptance criteria are tracked in the [Codex CLI collaboration await v1 backlog](../backlog/codex-cli-collaboration-await-v1.md).

## Reporting policy

New entries include the reproduction surface and version, user impact, a safe workaround, exit criteria, and evidence links. Public docs do not include raw user conversations, authentication material, actual session transcripts, or local absolute paths.
