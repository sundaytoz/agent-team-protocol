---
kind: adr
id: ADR-0020
title: environment-authoritative subagent lifecycle — 관측 추론 폐기와 host event 권위화
status: accepted
date: 2026-08-12
deciders: [stzjungsoo]
partially_supersedes: [ADR-0017]
relates_to: [ADR-0008, ADR-0009, ADR-0013, ADR-0017]
---

# ADR-0020: environment-authoritative subagent lifecycle

## Context

[ADR-0017](./ADR-0017-subagent-lifecycle-recovery.md)은 첫 관측 가능 활동과 변화 없는 상태 확인에 유한 budget을 두고 `suspected_silent_stall`을 감지하는 정책을 도입했다. 이후 직접 관측에서는 progress 없이 장시간 `running`인 정상 invocation이 여러 번의 wait timeout 뒤 정상 완료했다. wait timeout, 경과 시간, progress/heartbeat 부재, 동일 snapshot 반복은 parent의 관측 상태만 설명하며 invocation의 실제 생존 상태를 증명하지 못한다.

ATP가 이 비권위 신호를 failure detector로 사용하면 host environment가 명시한 정상 `running`을 덮어쓰고, 특히 write-capable invocation에서 불필요한 interrupt나 중복 실행 위험을 연다. lifecycle 상태의 소유자와 orchestration 안전 정책의 소유자를 분리해야 한다.

## Decision

### 1. Host environment의 명시적 상태와 event만 lifecycle 권위로 사용한다

ATP는 host가 정상 API로 제공한 `accepted`, `queued`, `running`, `approval_required`, `completed`, `failed`, `interrupted`와 명시적 environment blocker만 공통 의미로 정규화한다. host가 상태를 제공하지 않거나 의미를 보장할 수 없으면 `environment_state_unknown`으로 남긴다. 이는 terminal이나 failure가 아니며 mutation 권한을 만들지 않는다.

`wait` timeout, 경과 시간, progress/output/tool event 또는 그 부재, heartbeat 부재, 동일 snapshot 반복은 lifecycle 전이를 만들지 않는다. environment가 `running`을 반환하는 동안 ATP도 `running`으로 유지한다. progress는 UX·설명 신호이지 liveness 증명이 아니다.

Host별 실제 상태 출처와 도구 mapping은 host appendix에 둔다. 공통 protocol은 특정 host 도구명이나 고정 시간값을 포함하지 않는다. 지원되지 않는 event는 추정하거나 합성하지 않는다.

### 2. Recovery 검토는 권위 있는 사건에서만 연다

명시적 `failed`, `interrupted`, environment-native blocker 또는 사용자 취소가 recovery 검토를 열 수 있다. `approval_required`는 environment 승인 흐름으로 전달하지만 clean retry나 fallback의 승인으로 간주하지 않는다. timeout, 무진행, 동일 snapshot은 recovery trigger도 retry budget 소비 사유도 아니다.

### 3. ADR-0017을 부분적으로만 supersede한다

이 ADR이 supersede하는 범위는 다음으로 한정한다.

- ADR-0017 결정 1·2의 `suspected_silent_stall`/first observable activity 기반 감지 부분
- ADR-0017 결정 4의 first-activity 대기 budget, unchanged 상태 확인 budget, 그 관측 budget 소진으로 phase 종단을 여는 부분

다음 ADR-0017 결정과 안전 불변식은 그대로 유효하다.

- interrupt, retry, fallback, ownership 변경 전 사용자 보고·선택·승인
- clean retry의 새 invocation identity와 same-invocation follow-up의 attempt 불변
- retry 승인 직전 completion race 재확인
- 기존 invocation termination/isolation 확인 뒤 retry
- write ownership 회수, partial write 검사, 동일 write scope의 old/new owner 동시 실행 금지
- ownership 회수 뒤 `late_completion` 격리와 자동 merge·성공 판정 금지
- mandatory verification non-skip: Tier B 동일 검증 또는 blocked
- report schema v2와 `attempt`, `termination`, `retry_of`, `lifecycle_fallback_reason` 네 additive optional 필드
- lifecycle fallback과 `model_choice.fallback_reason`의 의미 분리

과거 v2 report의 `termination: silent_stall`은 reader 호환용 역사 enum으로 유지한다. 신규 producer는 environment가 명시한 terminal event 또는 ownership 회수 뒤의 `late_completion`만 기록하며 `environment_state_unknown`으로 invocation을 종결하지 않는다.

## Consequences

- 정상 장기 실행은 progress가 없거나 wait timeout이 반복되어도 ATP에 의해 stall/failure로 재분류되지 않는다.
- event 노출이 제한된 host에서는 자동 recovery보다 `environment_state_unknown`과 사용자 판단이 늘어난다. 이는 거짓 failure보다 안전한 보수적 결과다.
- clean retry 횟수의 유한 안전 한도와 phase별 종단은 명시적 terminal failure 이후에만 적용된다.
- lifecycle fixture는 environment event sequence와 비권위 observation의 무전이를 분리해 검증한다.
- report schema version은 2로 유지되며 데이터 migration은 없다.

## Alternatives considered

- **Evidence epoch 또는 observation budget**: 반복 관측은 유한화하지만 정상 `running`을 오탐할 수 있어 기각했다.
- **필수 heartbeat**: delivery가 보장되지 않는 UX 신호를 correctness 조건으로 만들므로 기각했다.
- **고정 deadline 뒤 자동 interrupt**: environment 권위를 덮어쓰고 write 중복 위험을 만들므로 기각했다.
- **상태 API 부재를 failure로 간주**: capability 한계를 실행 실패로 오해하므로 기각했다.

## Implementation and verification status

Runtime protocol, host capability/appendix, task skill, advisor lifecycle, fixture와 validator 변경은 2026-08-12 worktree에 반영됐다. Fixture-first RED는 구 validator가 새 fixture에 없는 `observable_activity`를 읽어 `KeyError`로 exit 1 하는 것으로 확인했다.

최종 검증은 2026-08-13에 완료했다. 독립 lifecycle validator가 exit 0과 `PASS: environment-authoritative lifecycle contract and compatibility fixtures`를 반환했고, 별도 read-only direct probe가 environment의 `running` 뒤 `completed`를 권위 상태로 수용해 결과 계약을 충족했다. 자동 interrupt·retry·fallback은 0건이었다. base manifest 4개는 2.12.0으로 동기화했고, add-on 2.3.0과 versionless Codex marketplace를 보존한 채 release 정적 gate를 통과했다. main 도달과 소비자 `/plugin update`는 merge 이후 확인한다.

## References

- [환경 권위 subagent lifecycle 아키텍처](../architecture/environment-authoritative-subagent-lifecycle-design.md)
- [환경 권위 lifecycle 변경 기록](../changes/2026-08-12-environment-authoritative-subagent-lifecycle.md)
- [`agent-team-protocol.md` §2.5](../../plugins/atp/docs/development/agent-team-protocol.md)
- [Codex lifecycle routing appendix](../../plugins/atp/docs/development/codex-lifecycle-routing.md)
- [ADR-0017](./ADR-0017-subagent-lifecycle-recovery.md)

## Accepted clarification — invocation authority (2026-08-12)

이 보정은 ADR-0020의 accepted 결정과 ADR-0017 부분 supersede 범위를 바꾸지 않는다. 위 Decision 3의 “ownership 회수 뒤의 `late_completion`”과 “ownership 회수 뒤의 `late_completion`만 기록”이라는 표현은 아래 두 authority 중 같은 old identity의 해당 authority가 먼저 철회·격리된 경우를 뜻하는 것으로 명확화한다. lifecycle 상태는 계속 environment event가 권위이며, ATP가 관리하는 invocation effect authority는 host-neutral하게 다음 둘로 구분한다.

- read-only invocation의 `result acceptance authority`: 해당 identity의 future result를 현재 logical task의 취합·성공 판정 입력으로 받아들일 권한
- write-capable invocation의 `write ownership`: 선언된 write scope를 변경할 권한

사용자 retry 승인과 completion race 재확인 전에는 어느 authority도 철회하지 않는다. race 재확인에서 old invocation이 `completed`면 retry를 취소하고 정상 결과 후보로 검토한다. read-only recovery는 termination 또는 read-only 성질을 확인한 뒤 phase-local ledger에 old report/environment identity의 `result_acceptance_revoked`를 기록하고, write-capable recovery는 termination/write isolation과 partial write를 확인한 뒤 ownership을 회수한다. 그 선행 조치 뒤에만 새 identity를 spawn할 수 있다.

`late_completion`은 같은 old identity의 해당 authority가 먼저 명시적으로 철회·격리된 뒤 environment `completed` 또는 result arrival이 도착한 경우에만 기록하는 advisor disposition이다. 선행 authority record가 없거나 completion이 철회 전에 도착하면 `late_completion`으로 분류하지 않는다. read-only late result와 late disk write가 없는 write-capable late result는 quarantine-only이며 자동 merge·취합·성공 판정 또는 ownership pause를 만들지 않는다. 회수된 write scope에 실제 late disk write가 확인된 경우에만 겹치는 scope와 dependency closure를 persisted `paused`로 만든다.

`authority_kind`, `authority_ref`, `result_acceptance_revoked`는 phase-local ledger 계약이며 report field가 아니다. report는 계속 `schema_version: 2`이고 lifecycle optional field는 `attempt`, `termination`, `retry_of`, `lifecycle_fallback_reason` 네 개뿐이다. research worker의 `model_choice.phase: analyze`는 protocol §5.8 routing enum이고 research artifact frontmatter의 `phase: research`는 산출물 분류이므로 서로 다른 namespace다.

## Accepted clarification — approval capability와 recovery disposition (2026-08-12)

이 보정도 ADR-0020의 accepted 결정과 ADR-0017 부분 supersede 범위를 확장하지 않는다. environment가 명시한 lifecycle state와 ATP가 그 state를 사용자에게 relay하거나 같은 invocation을 continuation할 capability는 별도 축이다. 따라서 명시적으로 관측된 `approval_required`는 relay/control capability가 없거나 불명이어도 `approval_required`로 보존한다. 이 경우 child invocation은 environment provenance와 concrete `source_ref`를 ledger에 남기고, `ended_at: null`, `termination` 생략, `lifecycle_fallback_reason` null 또는 생략으로 반환한다. interrupt/cancel, 승인 합성, retry/fallback, authority/ownership mutation, attempt/retry 증가는 수행하지 않는다.

relay 가능한 ancestor에는 control을 반환한다. root까지 relay/continuation을 제공할 수 없으면 phase 진행 불가는 report의 `Summary`, `Open Items`, `concerns` narrative에 `blocked`로 기록한다. 이 phase control disposition은 child invocation의 lifecycle state나 `termination` enum이 아니며 report field를 추가하지 않는다. capability가 복구되고 environment가 same identity continuation을 지원하면 attempt/retry accounting을 바꾸지 않고 계속한다. `environment_state_unknown`은 relay capability가 아니라 environment status API 자체가 unavailable/error이거나 상태 의미를 확인할 수 없다는 새 관측이 있을 때만 생산한다.

신규 producer에서 `failed`, `interrupted`, `late_completion` termination의 `lifecycle_fallback_reason`은 최초 abnormal serialization부터 원인의 concrete source와 현재 recovery disposition, non-empty rationale를 함께 기록한다. canonical producer form의 disposition은 `awaiting_user_decision`, `approved_clean_retry`, `phase_fallback`, `blocked`, `late_completion_quarantined` 다섯 값으로 닫힌다. 중간 `failed`/`interrupted` invocation도 retry cap 소진을 기다리지 않으며, 명시적 사용자·advisor decision이 바뀌면 같은 row의 현재 disposition을 갱신하고 결정 순서와 provenance는 phase-local ledger에 보존한다. `late_completion`은 항상 `late_completion_quarantined`이고 선행 authority anchor와 no-auto-merge 계약을 유지한다.

이 형식은 기존 string field의 producer 규약일 뿐 schema migration이 아니다. 기존 v2 free-text와 optional field가 없는 report의 reader compatibility, `completed`의 reason null/생략, nonterminal의 `termination` 생략과 reason null/생략을 유지한다. report는 계속 `schema_version: 2`이고 optional lifecycle field는 기존 네 개뿐이며, lifecycle cause/recovery disposition은 `model_choice.fallback_reason`과 분리한다.
