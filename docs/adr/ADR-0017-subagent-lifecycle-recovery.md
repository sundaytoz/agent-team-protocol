---
kind: adr
id: ADR-0017
title: subagent silent-start lifecycle recovery — 사용자 승인 기반 독립 invocation 재시도와 유한 수렴
status: accepted
date: 2026-07-20
deciders: [stzjungsoo]
relates_to: [ADR-0004, ADR-0008, ADR-0009, ADR-0013]
---

# ADR-0017: subagent silent-start lifecycle recovery

## 배경

현행 호출 실패 규약은 API 오류·timeout·rate limit처럼 명시적으로 실패한 호출을 사용자에게 보고하고 승인 후 재시도하는 흐름을 제공했다. 그러나 invocation이 오류 없이 `running`으로 남고 첫 관측 가능 활동을 만들지 않는 silent-start 상황은 실패 처리 진입 조건이 아니었다. 같은 invocation에 추가 지시를 보내거나 상태를 계속 조회하는 현장 대응도 clean retry의 정체성과 유한한 종단을 보장하지 못했다.

한 Codex 운영 세션에서 이런 공백이 관측됐지만, UI 이벤트 누락이나 runtime scheduler를 근본 원인으로 확정할 증거는 없다. 따라서 이 결정은 특정 runtime 원인이나 고정 시간 추정에 의존하지 않고 ATP가 보장할 수 있는 lifecycle 의미와 안전 경계를 규정한다.

## 결정

### 1. 공통 정본은 host-neutral lifecycle 의미만 정의한다

`agent-team-protocol.md` §2.5를 명시적 호출 실패와 silent-start lifecycle 실패의 공통 정본으로 확장한다. 공통 상태 흐름은 다음과 같다.

```text
active
  → suspected_silent_stall
  → awaiting_user_decision
  → terminating
  → retrying | fallback | blocked
```

first observable activity는 orchestrator가 정상 API로 실제 관측할 수 있는 output, explicit progress, tool start/result, terminal 또는 explicit blocked 상태다. reasoning·token 내부 이벤트는 공통 판정 조건이 아니다. queueing, explicit blocked, 이미 시작된 long-running tool은 silent-start stall에서 제외한다. progress와 authoritative status capability가 불명확하면 stall로 단정하지 않고 `progress_unobservable` 사용자 결정 경로로 보낸다.

Codex의 구체적인 collaboration 도구·상태 조회·context fork 매핑은 별도 런타임 appendix인 `plugins/atp/docs/development/codex-lifecycle-routing.md`에 둔다. `platform-adapters.md`는 progress, termination, invocation identity, interrupt, write isolation 같은 capability 자가판정만 정의한다.

### 2. 감지와 복구 실행을 분리한다

stall 후보 감지는 자동화할 수 있다. 그러나 interrupt/cancel, retry invocation 생성, phase fallback 실행은 기존 §2.5의 순서인 **사용자 보고 → 옵션 제시 → 사용자 확인** 뒤에만 수행한다. 사용자 승인 전 이 세 종류의 action은 0건이어야 한다.

승인 직전 기존 invocation이 완료되면 retry를 취소하고 기존 결과를 정상 후보로 검토한다.

### 3. clean retry의 정본은 새 invocation ID다

clean retry는 실패 실행과 다른 invocation ID를 가진 독립 실행이다. 동일 thread/invocation에 follow-up을 보내는 행위는 continuation 또는 진단일 뿐 clean retry가 아니며 `attempt`를 증가시키지 않는다.

retry payload에는 목표, 권위 자료와 확정 계약, write scope, 보존할 partial, 필수 산출물, 검증·반환 형식을 명시한다. 전체 transcript 상속이나 특정 turn 수는 공통 요구가 아니다.

### 4. 상태 확인과 retry는 configurable한 유한 budget을 가진다

first-activity 대기, 변화 없는 상태 확인, clean retry 횟수는 host/config별 calibration 대상이며 모두 유한해야 한다. 특정 초·polling 간격·context turn 수를 공통 상수로 고정하지 않는다. timeout 자체는 새 증거나 실패 확정이 아니다.

budget 소진 후에는 같은 판단·재시도를 반복하지 않고 phase criticality에 따라 다음 중 하나로 수렴한다.

- optional advisory: 사용자 승인 하 skip 또는 기존 근거 요약
- required judgment/artifact: Tier B 순차 self-check, 사용자 결정 또는 blocked
- write-capable implementation: ownership이 안전하게 회수된 범위의 direct/self 수행, 독립 dispatch 또는 blocked
- mandatory verification: Tier B 직접 검증 또는 blocked; advisor 장애를 이유로 skip 금지
- destructive/external action: 자동 fallback 없이 사용자 승인·복구 가능성 확보까지 blocked
- closing documentation/retro: 필수 report 전제를 유지한 orchestrator self-check 또는 blocked

### 5. write ownership과 late completion을 격리한다

write-capable invocation은 clean retry 전에 기존 termination/isolation 확인, ownership 회수, partial write 검사를 완료해야 한다. 이를 확인할 수 없고 scope도 분리할 수 없으면 동일 write scope의 새 invocation을 시작하지 않는다.

ownership 회수 후 기존 invocation이 완료하면 `late_completion`으로 격리한다. 그 결과는 자동 merge하거나 성공으로 판정하지 않으며 새 owner의 scope를 수정할 권한도 없다. 늦은 disk write가 발견되면 새 owner를 일시 중지하고 diff와 ownership 충돌을 중재한다.

### 6. report schema v2를 additive하게 확장한다

`schema_version: 2`를 유지하고 `invocations[]`에 다음 네 필드만 optional로 추가한다.

- `attempt`
- `termination`
- `retry_of`
- `lifecycle_fallback_reason`

기존 v2 report는 네 필드 없이도 유효하고 새 reader는 필드 부재를 legacy/unknown으로 해석한다. `retry_of`는 host thread ID가 아니라 report 내부 invocation ID를 참조한다.

`lifecycle_fallback_reason`은 invocation lifecycle 복구 전용이다. §5.7과 `model_choice.fallback_reason`은 모델 slug/route/tier fallback 의미를 그대로 유지하며 lifecycle recovery와 혼합하지 않는다.

## 대안과 기각 이유

- **고정 deadline·polling 간격·context turn 수를 공통 규약에 둔다**: 단일 incident로 calibration할 수 없고 host/workload 차이에서 오탐을 만든다.
- **동일 invocation follow-up을 retry로 센다**: 실패 runtime 상태의 재사용 여부를 분리할 수 없고 attempt 계보가 모호해진다.
- **자동 interrupt와 retry를 수행한다**: 기존 사용자 승인 게이트를 우회하고 write scope에서 중복 실행 위험을 만든다.
- **schema v3와 host telemetry 필드를 일괄 도입한다**: host가 노출하지 않는 필드가 많고 기존 reader migration 비용이 불필요하다.
- **lifecycle fallback을 §5.7에 합친다**: 모델 routing과 invocation recovery라는 서로 다른 감사 축을 오염시킨다.

## 영향

- 공통 호출 실패 처리가 no-first-observable-activity 상태까지 확장된다.
- host-specific 실행자는 공통 정본과 자기 appendix/capability 판정을 함께 읽어야 한다.
- verification은 advisor lifecycle 장애가 있어도 Tier B 실행 또는 blocked로 끝나며 skip되지 않는다.
- v2 report producer는 네 lifecycle 필드를 필요할 때만 기록할 수 있고 기존 report/reader는 계속 유효하다.
- user-facing 동작 변경이므로 base atp를 2.7.0에서 2.8.0으로 minor bump한다.

## 검증

`tests/lifecycle-contract/validate.py`가 다음을 회귀 검증한다.

- legacy v2와 lifecycle optional 필드가 추가된 v2 fixture의 동시 유효성
- 승인 전 lifecycle action 0건, clean retry identity, same-invocation attempt 불변
- write ownership 회수 순서와 late completion 격리
- phase별 유한 종단 및 verification non-skip
- 공통 §2.5의 Codex 도구명·고정 시간값 부재와 Codex appendix mapping 존재
- task skill 및 호출 주체의 §2.5 연결

## 관련

- [ADR-0008](./ADR-0008-platform-neutral-model-policy.md) — report schema v2와 모델 routing 필드
- [ADR-0009](./ADR-0009-bundle-runtime-platform-neutralization.md) — 번들 런타임 플랫폼 중립화
- [`agent-team-protocol.md` §2.5](../../plugins/atp/docs/development/agent-team-protocol.md) — 공통 lifecycle 정본
- [`codex-lifecycle-routing.md`](../../plugins/atp/docs/development/codex-lifecycle-routing.md) — Codex host appendix
