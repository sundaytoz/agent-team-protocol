---
kind: usage
title: Known Issues
description: 현재 확인된 ATP 플랫폼 제한과 사용자 영향, 우회책, 해소 조건.
owner: template-maintainer
stability: living
last_reviewed: 2026-08-20
---

<p align="center">
  <a href="known-issues.md">한국어</a> ·
  <a href="known-issues.en.md">English</a>
</p>

# Known Issues

이 문서는 현재 사용자 동작에 영향을 주는 확인된 제한만 추적한다. 설계 배경은 ADR, 구현 변경은 Changes, 아직 채택되지 않은 host capability 제안은 Backlog에 둔다.

| ID | Surface | 상태 | 사용자 영향 |
|---|---|---|---|
| ATP-KI-001 | Codex CLI 0.147.0 | Open | tested CLI에서 독립 subagent team execution disabled |
| ATP-KI-002 | Codex App/IDE | Verification gap | 동일한 maintainer smoke 미수행으로 managed orchestration 지원 여부 `unknown` |
| ATP-KI-003 | Codex formal wait/wakeup | Upstream capability gap | timeout-free targeted subscription을 formal scheduling mode로 사용할 수 없음 |

## ATP-KI-001 — Codex CLI managed all-results barrier 미검증

### 증상과 범위

ATP 2.15.0의 격리 Codex CLI 0.147.0 smoke에서 terminal-only 1-agent는 통과했지만, nonterminal 뒤 delayed terminal 1-agent와 staggered 2-agent는 모든 terminal result가 전달되기 전에 parent가 종료됐다. 따라서 배포된 tested CLI profile은 `host_managed_subagent_orchestration: unsupported`, `team_execution_enabled: false`다.

[공식 OpenAI Subagents 문서](https://learn.chatgpt.com/docs/agent-configuration/subagents)는 local Codex가 subagent workflow를 제공하고 main thread가 요청된 결과를 취합한다고 설명한다. 이 이슈는 공식 기능 부재 주장이 아니라, 해당 제품 설명과 ATP 2.15.0이 요구하는 all-results correctness 계약을 CLI 0.147.0 격리 smoke에서 끝까지 확인하지 못한 empirical gap이다.

### 사용자 영향

- 일반 `$atp:task` 요청은 `tier_b_sequential`로 자동 격하되 이 사실을 1줄 고지한다. 결과를 advisor/subagent 독립 의견으로 표현하지 않는다.
- 실제 독립 subagent 수행이 산출 요구사항이면 `blocked_explicit_independence`로 멈추고 지원 host 재실행, 독립성 없는 Tier B 명시 전환 또는 취소를 제시한다.
- ATP는 manual wait/list polling, automatic retry·interrupt·fallback으로 이 제한을 숨기지 않는다.

### 우회책

- 독립성이 필요 없는 작업은 Tier B 순차 self-check로 계속한다.
- 독립 실행이 필수라면 해당 orchestration 계약이 검증된 host에서 재실행한다. Codex App/IDE는 ATP의 동일 smoke를 거치지 않았으므로 지원되는 우회 surface로 간주하지 않는다.

### 해소 조건

동일 Codex surface와 버전에서 release maintainer의 terminal-only 1-agent, delayed nonterminal+terminal 1-agent, staggered terminal 2-agent smoke가 모두 통과하고, requested/spawn/terminal/collected 수가 일치하며 manual wait/list/interrupt/recovery가 0이어야 한다.

근거: [공식 OpenAI Subagents 문서](https://learn.chatgpt.com/docs/agent-configuration/subagents), [2.15.0 Changes](../changes/2026-08-19-codex-managed-subagent-orchestration.md), [ADR-0024](../adr/ADR-0024-host-managed-subagent-orchestration.md), [sanitized evidence manifest](../../tests/runtime-behavior/evidence/codex-cli-0.147.0-20260819.json).

## ATP-KI-002 — Codex App/IDE capability 상태 미확인

공식 제품 설명만 있고 ATP release smoke가 없다. 따라서 `supported`나 `unsupported`를 추론하지 않고 `unknown`으로 둔다. 사용자 동작은 실제 배포 profile과 task preflight가 정하며, maintainer가 같은 3종 smoke를 격리 실행해 근거를 보존하면 상태를 갱신한다.

## ATP-KI-003 — Formal timeout-free wait/wakeup 미지원

Codex의 tested collaboration surface는 ATP formal mode가 요구하는 timeout-free suspend, targeted wait-any/all, stable event identity, deduplication, completion coalescing, compact delta와 await cancellation 계약을 전부 제공하지 않는다. ATP는 bounded wait나 반복 polling을 formal adapter로 승격하지 않는다.

이 제한은 host-managed orchestration과 별도 축이다. Formal 개선 제안과 acceptance criteria는 [Codex CLI collaboration await v1 backlog](../backlog/codex-cli-collaboration-await-v1.md)에서 추적한다.

## 보고 원칙

새 이슈를 추가할 때는 재현 surface·버전, 사용자 영향, 안전한 우회책, 해소 조건과 근거 링크를 함께 기록한다. 원본 사용자 대화, 인증 정보, 실제 session transcript와 로컬 절대 경로는 공개 문서에 포함하지 않는다.
