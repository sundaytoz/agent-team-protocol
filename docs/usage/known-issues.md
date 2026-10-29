---
kind: usage
title: Known Issues
description: 현재 확인된 ATP 플랫폼 제한과 사용자 영향, 우회책, 해소 조건.
owner: template-maintainer
stability: living
last_reviewed: 2026-10-29
---

<p align="center">
  <a href="known-issues.md">한국어</a> ·
  <a href="known-issues.en.md">English</a>
</p>

# Known Issues

이 문서는 현재 사용자 동작에 영향을 주는 확인된 제한만 추적한다. 설계 배경은 ADR, 구현 변경은 Changes, 아직 채택되지 않은 host capability 제안은 Backlog에 둔다.

| ID | Surface | 상태 | 사용자 영향 |
|---|---|---|---|
| ATP-KI-001 | Codex CLI 0.149.1 | 0.165.0에서 미재현 (2026-10-29) | Codex 내장 subagent로 team execution 동작. 결과 취합은 Codex 내장 동작에 위임하며 시차 결과 일부가 누락된 관측이 있다 |
| ATP-KI-002 | Codex App/IDE | Verification gap | 동일한 maintainer smoke 미수행으로 managed orchestration 지원 여부 `unknown` |
| ATP-KI-003 | Codex formal wait/wakeup | Upstream capability gap | timeout-free targeted subscription을 formal scheduling mode로 사용할 수 없음 |
| ATP-KI-004 | Codex 연결 스모크 (surface·버전 미측정) | Obsolete (2.19.0) | child에 `update_plan` 미노출 관측. 2.19.0에서 bind 단계가 없어져 사용자 영향 없음 |

## ATP-KI-001 — Codex CLI managed all-results barrier 실패

> **2026-10-29 상태 갱신 (2.19.0, [ADR-0026](../adr/ADR-0026-codex-builtin-subagents-without-marker.md))**: Codex에서 `codex-team`은 marker·add-on 없이 Codex 내장 subagent를 사용한다(spawn → 대기·follow-up은 Codex 내장 workflow → 전체 terminal 결과 취합). 배포 profile은 `formal_adapter_enabled: false`, `manual_wait_polling_supported: false`, `host_managed_subagent_orchestration: supported`, `team_execution_enabled: true`다. 결과 취합은 Codex 내장 동작에 위임하며, 아래 2026-08-26 관측처럼 내장 barrier가 시차 결과 2건 중 1건만 전달한 사례가 있다. 이 caveat은 gate가 아니다. 아래 과거 기록은 보존된 이력이다.

> **2026-10-29 재확인 (Codex CLI 0.165.0)**: 2.19.0 설치본으로 `$atp:task` 2-agent 병렬 조사를 실행해 2개 모두 완료·취합됐다. 실행 중 "Waiting for agents"·"No agents completed yet" 표시는 Codex 내장 대기 기능의 중간 표시이며 실패 신호가 아니다. ATP는 이를 제한·해석하지 않는다.

### 과거 증상과 범위 (2026-08-26)

Codex CLI 0.149.1 격리 smoke에서 terminal-only 1-agent와 nonterminal `MESSAGE` 뒤 delayed terminal 1-agent는 통과했지만, `fork_turns: none`을 사용한 staggered 2-agent는 `spawn_calls=2`, `terminal_deliveries=1`로 실패했다. Fast child 결과만 전달된 뒤 slow child terminal 없이 parent turn이 종료됐다. Queue→wait→refill bounded-pool candidate도 terminal-only flat/nested/denial-refill과 source/install parity는 통과했지만, saturated nonterminal barrier, active-wait steering, approval same-identity continuation과 cancellation이 실패했다. 따라서 당시 ATP 2.15.0 tested CLI profile은 `formal_adapter_enabled: false`, `manual_wait_polling_supported: false`, `host_managed_subagent_orchestration: unsupported`, `team_execution_enabled: false`였다. 별도 bounded-pool capability 축이나 execution mode는 당시 추가하지 않았다.

[공식 OpenAI Subagents 문서](https://learn.chatgpt.com/docs/agent-configuration/subagents)는 local Codex subagent workflow를 설명한다. 이 이슈는 공식 기능 부재 주장이 아니라, 해당 제품 설명과 ATP가 요구하는 multi-child all-results correctness 계약 사이에서 CLI 0.149.1로 재현된 empirical gap이다.

### 현재 사용자 영향

- `$atp:task`는 Codex 내장 subagent로 advisor/worker를 spawn한다. 추가 add-on, hook trust, 실행 환경 scope 조건이 없다.
- 결과 취합은 Codex 내장 동작에 위임한다. 내장 barrier가 일부 결과를 전달하지 않으면 그 결과는 누락될 수 있으며, ATP는 manual wait/list polling, automatic retry·interrupt·fallback으로 이를 보상하지 않는다.
- 2.18.0까지의 marker gate와 `atp-codex-hooks` add-on은 2.19.0에서 제거됐다. 설치돼 있다면 `codex plugin remove atp-codex-hooks`로 삭제할 수 있다.

### 과거 기록 (2.18.0 이전)

2026-08-26 이후 queue→wait→refill 후보와 그 hook 기반 변형을 거쳐 2.18.0에서 marker로 범위를 제한해 팀 실행을 켰지만(ADR-0025), 2.19.0에서 이 gate를 제거하고 Codex 내장 동작으로 단순화했다. 결정 근거는 [ADR-0026](../adr/ADR-0026-codex-builtin-subagents-without-marker.md), 이전 판단은 [ADR-0024](../adr/ADR-0024-host-managed-subagent-orchestration.md)를 본다.

### Built-in 해소 조건

동일 Codex surface와 버전에서 release maintainer의 terminal-only 1-agent, delayed nonterminal+terminal 1-agent, staggered terminal 2-agent smoke가 모두 통과하고, requested/spawn/terminal/collected 수가 일치하며 manual wait/list/interrupt/recovery가 0이면 이 caveat을 닫는다.

근거: [공식 OpenAI Subagents 문서](https://learn.chatgpt.com/docs/agent-configuration/subagents), [upstream issue draft](../backlog/codex-cli-collaboration-await-v1.md), [ADR-0024](../adr/ADR-0024-host-managed-subagent-orchestration.md), [0.149.1 sanitized evidence manifest](../../tests/runtime-behavior/evidence/codex-cli-0.149.1-20260826.json).

## ATP-KI-002 — Codex App/IDE capability 상태 미확인

공식 제품 설명만 있고 ATP release smoke가 없다. 따라서 `supported`나 `unsupported`를 추론하지 않고 `unknown`으로 둔다. 사용자 동작은 실제 배포 profile과 task preflight가 정하며, maintainer가 같은 3종 smoke를 격리 실행해 근거를 보존하면 상태를 갱신한다.

## ATP-KI-003 — Formal timeout-free wait/wakeup 미지원

Codex의 tested collaboration surface는 ATP formal mode가 요구하는 timeout-free suspend, targeted wait-any/all, stable event identity, deduplication, completion coalescing, compact delta와 await cancellation 계약을 전부 제공하지 않는다. ATP는 bounded wait나 반복 polling을 formal adapter로 승격하지 않는다.

이 제한은 host-managed orchestration과 별도 축이다. Formal 개선 제안과 acceptance criteria는 [Codex CLI collaboration await v1 backlog](../backlog/codex-cli-collaboration-await-v1.md)에서 추적한다.

## ATP-KI-004 — 연결 스모크 child의 `update_plan` 미노출

2026-09-08 [실제 1-agent 연결 스모크](./codex-connection-smoke.md)에서 child는 `update_plan`을 사용할 수 없다고 보고해 당시 profile이 요구하던 bind plan 호출을 실행하지 못했다. 실제 spawn 응답과 `FINAL_ANSWER`로 `requested=accepted=terminal=collected=1`을 확인했고, child가 연결 상태·프로젝트와 일치하는 cwd·mutation 0을 보고했다. 이 관측의 UI surface와 버전은 독립 측정하지 않았다.

2.19.0에서 bind 단계가 제거돼 이 관측은 더 이상 사용자 동작에 영향을 주지 않는다. 이력으로만 보존한다.

## 보고 원칙

새 이슈를 추가할 때는 재현 surface·버전, 사용자 영향, 안전한 우회책, 해소 조건과 근거 링크를 함께 기록한다. 원본 사용자 대화, 인증 정보, 실제 session transcript와 로컬 절대 경로는 공개 문서에 포함하지 않는다.
