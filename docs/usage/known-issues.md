---
kind: usage
title: Known Issues
description: 현재 확인된 ATP 플랫폼 제한과 사용자 영향, 우회책, 해소 조건.
owner: template-maintainer
stability: living
last_reviewed: 2026-09-08
---

<p align="center">
  <a href="known-issues.md">한국어</a> ·
  <a href="known-issues.en.md">English</a>
</p>

# Known Issues

이 문서는 현재 사용자 동작에 영향을 주는 확인된 제한만 추적한다. 설계 배경은 ADR, 구현 변경은 Changes, 아직 채택되지 않은 host capability 제안은 Backlog에 둔다.

| ID | Surface | 상태 | 사용자 영향 |
|---|---|---|---|
| ATP-KI-001 | Codex CLI 0.149.1 | Resolved within declared scope (2026-09-08) | 선언 scope의 exact hook marker가 있으면 team execution 가능. Marker 부재·불일치는 일반 요청 Tier B / 독립성 필수 요청 blocked |
| ATP-KI-002 | Codex App/IDE | Verification gap | 동일한 maintainer smoke 미수행으로 managed orchestration 지원 여부 `unknown` |
| ATP-KI-003 | Codex formal wait/wakeup | Upstream capability gap | timeout-free targeted subscription을 formal scheduling mode로 사용할 수 없음 |
| ATP-KI-004 | Codex 연결 스모크 (surface·버전 미측정) | Observed tool gap (2026-09-08) | child에 `update_plan` 미노출로 bind-plan 미실행; terminal 수집과 별개로 기록 |

## ATP-KI-001 — Codex CLI managed all-results barrier 실패

> **2026-09-08 상태 갱신 (ADR-0025)**: built-in barrier 실패는 그대로지만, 옵트인 add-on `atp-codex-hooks`의 hook-guarded bounded pool이 all-results barrier qualification을 통과해 **선언 scope 안에서 해소**됐다. 검증 범위는 Codex CLI 0.149.1, Unix, PATH의 `python3`, add-on 설치와 TUI hook trust이며, 현재 root context의 exact hook marker로 scope를 판정한다. Marker가 있으면 `host_managed_subagent_orchestration: supported`, `team_execution_enabled: true`; 없거나 schema/hash가 다르면 spawn 0과 `skip: no-codex-hooks`, 일반 요청 Tier B / 독립성 필수 요청 blocked다. Windows·App/IDE는 선언 scope 밖이다. 아래 과거 실패 기록은 보존된 이력이며 현재 hook-guarded profile을 부정하지 않는다.

### 과거 증상과 범위 (2026-08-26)

Codex CLI 0.149.1 격리 smoke에서 terminal-only 1-agent와 nonterminal `MESSAGE` 뒤 delayed terminal 1-agent는 통과했지만, `fork_turns: none`을 사용한 staggered 2-agent는 `spawn_calls=2`, `terminal_deliveries=1`로 실패했다. Fast child 결과만 전달된 뒤 slow child terminal 없이 parent turn이 종료됐다. Queue→wait→refill bounded-pool candidate도 terminal-only flat/nested/denial-refill과 source/install parity는 통과했지만, saturated nonterminal barrier, active-wait steering, approval same-identity continuation과 cancellation이 실패했다. 따라서 당시 ATP 2.15.0 tested CLI profile은 `formal_adapter_enabled: false`, `manual_wait_polling_supported: false`, `host_managed_subagent_orchestration: unsupported`, `team_execution_enabled: false`였다. 별도 bounded-pool capability 축이나 execution mode는 당시 추가하지 않았다.

[공식 OpenAI Subagents 문서](https://learn.chatgpt.com/docs/agent-configuration/subagents)는 local Codex subagent workflow를 설명한다. 이 이슈는 공식 기능 부재 주장이 아니라, 해당 제품 설명과 ATP가 요구하는 multi-child all-results correctness 계약 사이에서 CLI 0.149.1로 재현된 empirical gap이다.

### 현재 marker 부재·불일치 세션의 사용자 영향

- 일반 `$atp:task` 요청은 `tier_b_sequential`로 자동 격하되 이 사실을 1줄 고지한다. 결과를 advisor/subagent 독립 의견으로 표현하지 않는다.
- 실제 독립 subagent 수행이 산출 요구사항이면 `blocked_explicit_independence`로 멈추고 지원 host 재실행, 독립성 없는 Tier B 명시 전환 또는 취소를 제시한다.
- ATP는 manual wait/list polling, automatic retry·interrupt·fallback으로 이 제한을 숨기지 않는다.

### 현재 선택지

- 독립성이 필요 없는 작업은 Tier B 순차 self-check로 계속한다.
- 선언된 CLI scope에서 실제 팀 실행이 필요하면 [add-on 가이드](../../plugins/atp-codex-hooks/docs/codex-hooks-usage.md)에 따라 설치·trust 후 hook이 생성한 exact marker를 확인한다.
- 독립 실행이 필수라면 해당 orchestration 계약이 검증된 host에서 재실행한다. Codex App/IDE는 ATP의 동일 smoke를 거치지 않았으므로 지원되는 우회 surface로 간주하지 않는다.

### 과거 Bounded-pool candidate qualification (승격 전 실패 기록)

- Saturated A rerun은 `MESSAGE`에서 running 3/pending 2와 slot release/refill 0을 지키고 같은 child terminal도 받았지만, requested 5, attempts/accepted 3/3, terminal 3, collected 1, wait 2에서 멈췄고 parent final은 없었다. 최초 비포화 run은 superseded됐으며 PASS가 아니다.
- B는 active wait 중 steering queue를 한 번 accepted했지만 scheduler에 전달하지 않았다. Requested/accepted 5/5, terminal/collected 4/4, wait 5, send/follow-up/list/interrupt 0, parent final 0이었다.
- C는 interactive approval overlay와 reject decision을 실제 relay했지만 target child가 `turn_aborted`로 끝나 같은 identity continuation과 target terminal이 없었다. Companion terminal 1, wait 2, parent final 0이며 harmless marker도 없었다.
- D는 running 3/pending 2에서 cancellation queue를 accepted했지만 scheduler에 전달하지 않았고 pending 두 task를 추가 spawn했다. Accepted 5, terminal/collected 4/4, wait 4, interrupt 0, parent final 0이었다. 외부 smoke 정리는 scheduler cancellation이 아니다.
- Source/install skill byte hash `bcfbdd0f0f7d066233155faebdec9aadb78de73fc2bfa057b3c7aec740eee146`와 설치본 flat/nested/denial-refill 회귀는 PASS지만 위 실패를 상쇄하지 않는다.

공식 OpenAI 문서가 interactive approval overlay와 queued control 동작을 설명하더라도 실제 ATP qualification이 우선한다. 이 실패 당시 bounded-pool은 지원되는 우회책이 아니었다. 이후 hook-guarded 방식은 선언 scope에서 승격됐지만 built-in all-results P0는 계속 open이다.

### Built-in 해소 조건과 현재 hook-guarded 판정

동일 Codex surface와 버전에서 release maintainer의 terminal-only 1-agent, delayed nonterminal+terminal 1-agent, staggered terminal 2-agent smoke가 모두 통과하고, requested/spawn/terminal/collected 수가 일치하며 manual wait/list/interrupt/recovery가 0이어야 한다.

Bounded-pool 승격 판정은 [hook-guarded bounded pool backlog](../backlog/codex-cli-hook-guarded-bounded-pool.md) §Phase 3의 4개 독립 축을 따른다. 필수 축은 A(all-results barrier: 이미 전달된 terminal 전부 소비, terminal 뒤에만 refill, capacity denial의 durable 기록, 전원 수집 뒤 root Stop 개방)와 D(선언된 packaging/runner scope)다. A와 D가 PASS하면 선언 scope 안에서 profile을 승격한다. B(active wait의 steering/cancellation delivery)와 C(approval decision 뒤 same-identity continuation)는 독립 축으로 각자 값을 기록하며, 이 두 축의 unknown/unsupported가 A·D 승격을 막지 않는다. 대신 해당 축을 요구하는 요청만 blocked/user-decision 경로로 보낸다.

현재 축 상태(2026-09-08): A PASS(2026-08-31 및 2026-09-08 add-on qualification), C supported, B unknown(interactive PTY 미측정), D는 옵트인 add-on `atp-codex-hooks`의 scope 선언 완료다. A·D 충족으로 선언 scope에서 team execution을 지원하며 B를 요구하는 요청만 blocked/user-decision 경로로 보낸다. Base만 설치하면 hook이 배포되지 않아 `skip: no-codex-hooks`와 Tier B/blocked가 적용된다. 정본은 [codex-team §7](../../plugins/atp/skills/codex-team/SKILL.md#7-배포된-capability-profile), [add-on 가이드](../../plugins/atp-codex-hooks/docs/codex-hooks-usage.md), [2026-09-08 qualification evidence](../../tests/runtime-behavior/evidence/codex-cli-0.149.1-hook-guarded-20260908.json)다.

근거: [공식 OpenAI Subagents 문서](https://learn.chatgpt.com/docs/agent-configuration/subagents), [upstream issue draft](../backlog/codex-cli-collaboration-await-v1.md), [ADR-0024](../adr/ADR-0024-host-managed-subagent-orchestration.md), [0.149.1 sanitized evidence manifest](../../tests/runtime-behavior/evidence/codex-cli-0.149.1-20260826.json).

## ATP-KI-002 — Codex App/IDE capability 상태 미확인

공식 제품 설명만 있고 ATP release smoke가 없다. 따라서 `supported`나 `unsupported`를 추론하지 않고 `unknown`으로 둔다. 사용자 동작은 실제 배포 profile과 task preflight가 정하며, maintainer가 같은 3종 smoke를 격리 실행해 근거를 보존하면 상태를 갱신한다.

## ATP-KI-003 — Formal timeout-free wait/wakeup 미지원

Codex의 tested collaboration surface는 ATP formal mode가 요구하는 timeout-free suspend, targeted wait-any/all, stable event identity, deduplication, completion coalescing, compact delta와 await cancellation 계약을 전부 제공하지 않는다. ATP는 bounded wait나 반복 polling을 formal adapter로 승격하지 않는다.

이 제한은 host-managed orchestration과 별도 축이다. Formal 개선 제안과 acceptance criteria는 [Codex CLI collaboration await v1 backlog](../backlog/codex-cli-collaboration-await-v1.md)에서 추적한다.

## ATP-KI-004 — 연결 스모크 child의 `update_plan` 미노출

2026-09-08 [실제 1-agent 연결 스모크](./codex-connection-smoke.md)에서 child는 `update_plan`을 사용할 수 없다고 보고해 `ATP_POOL_BIND` plan 호출을 실행하지 못했다. 실제 spawn 응답, `FINAL_ANSWER`와 hook terminal delta로 `requested=accepted=terminal=collected=1`을 확인했고, child가 연결 상태·프로젝트와 일치하는 cwd·mutation 0을 보고했다. 결과 전달이 bind 실행을 증명하지는 않는다. 이 관측의 UI surface와 버전은 독립 측정하지 않았으며 App 또는 특정 CLI 버전의 qualification으로 분류하지 않는다.

도구 미노출은 concern으로 기록하고 bind 성공을 합성하지 않는다. Bind·approval·denial·전체 pool qualification이 필요한 경우 해당 도구와 절차를 실제로 실행한 별도 근거가 필요하다. 이 스모크만으로 배포 profile을 올리거나 내리지 않는다.

## 보고 원칙

새 이슈를 추가할 때는 재현 surface·버전, 사용자 영향, 안전한 우회책, 해소 조건과 근거 링크를 함께 기록한다. 원본 사용자 대화, 인증 정보, 실제 session transcript와 로컬 절대 경로는 공개 문서에 포함하지 않는다.
