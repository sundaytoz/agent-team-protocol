---
kind: changes
title: environment-authoritative subagent lifecycle — wait/progress 추론 제거와 host event 권위화
description: timeout·경과 시간·progress/heartbeat 부재·동일 snapshot을 lifecycle 전이에서 제외하고 명시적 environment event만 취합·복구 근거로 사용한다.
date: 2026-08-12
owner: template-maintainer
stability: living
last_reviewed: 2026-08-13
implementation_status: implemented
verification_status: verified
---

# Environment-authoritative subagent lifecycle

## 변경 내용

- `agent-team-protocol.md` §2.5의 silent-start 관측 추론을 environment-authoritative 상태/event 계약으로 교체했다. `running`, `completed`, `failed`, `interrupted`, `approval_required`는 host가 실제 제공한 경우에만 정규화하고, 상태를 확인할 수 없으면 비종결 `environment_state_unknown`으로 둔다.
- wait timeout, 경과 시간, progress/output/tool event와 그 부재, heartbeat 부재, 동일 snapshot 반복은 lifecycle 전이·retry/fallback 권한·retry budget 소비를 만들지 않는다.
- `platform-adapters.md`에 lifecycle provenance capability와 unknown 폴백을 추가하고, `codex-lifecycle-routing.md`를 실제 collaboration snapshot/notification/control 결과의 mapping으로 갱신했다. Codex가 구조화해 보장하지 않는 approval/failure detail은 지원한다고 추정하지 않는다.
- task skill과 research/implementation advisor의 nested invocation 규칙을 같은 계약으로 맞췄다.
- lifecycle fixture를 environment event sequence 기반 10개 authority case와 ADR-0017 safety case로 재구성하고, validator가 비권위 관측 무전이와 schema v2 호환을 함께 검사하도록 갱신했다.
- research worker의 `model_choice.phase`를 protocol §5.8 routing enum `analyze`로 맞췄다. `research/index.md`의 artifact frontmatter `phase: research`는 별도 namespace로 유지한다.
- host-neutral invocation authority를 read-only `result acceptance authority`와 write-capable `write ownership`으로 구분했다. 사용자 retry 승인과 completion race 재확인 뒤에만 해당 authority를 철회·격리하며, 같은 old identity의 선행 authority anchor가 있어야 후속 environment completion을 `late_completion`으로 disposition한다.
- read-only late result와 late disk write가 없는 write-capable late result는 quarantine-only로 처리한다. 자동 merge·취합·성공 판정은 하지 않으며, 실제 late disk write가 확인된 경우에만 affected scope와 dependency closure를 persisted `paused`로 만든다.
- 명시적으로 관측된 `approval_required`는 relay/control capability가 없어도 child lifecycle에서 그대로 보존한다. relay 가능한 ancestor에는 control을 반환하며, root까지 불가능할 때의 phase 진행 불가만 report `Summary`/`Open Items`/`concerns` narrative에 `blocked`로 기록한다. child는 `ended_at: null`, `termination` 생략 상태이고 mutation·attempt/retry 증가는 0건이다. `environment_state_unknown`은 environment status API 자체가 unavailable/error이거나 의미 불명일 때만 생산한다.
- 카탈로그 research producer가 이름 붙은 모든 axis와 item 각각에 `확인됨 | 추정 | 미확인` marker 하나를 요구하도록 보정했다. 별도 aggregate `source_confidence: high | mixed | low`는 전체 marker multiset에서 결정론적으로 도출하며, worker와 advisor가 marker coverage와 aggregate derivation을 모두 self-check한다.
- 신규 abnormal `failed`/`interrupted`/`late_completion` producer는 `lifecycle_fallback_reason`에 concrete cause source, 현재 recovery disposition, rationale를 기록한다. disposition은 `awaiting_user_decision`, `approved_clean_retry`, `phase_fallback`, `blocked`, `late_completion_quarantined` 다섯 값이며, 중간 invocation도 retry exhaustion을 기다리지 않고 현재 값을 기록한다.

## 보존된 안전 계약과 호환성

- interrupt/retry/fallback 전 사용자 승인, clean retry의 새 invocation identity, retry 직전 completion race, termination/isolation 확인은 유지된다.
- write ownership 회수와 partial write 검사 전 동일 scope 재시도 금지, ownership 회수 뒤 `late_completion` 격리와 자동 merge 금지도 유지된다.
- read-only result acceptance 철회는 environment terminal을 추론하지 않으며 write isolation을 대신하지 않는다. 철회 전 completion은 completion race의 정상 결과 후보로 처리하고 retry를 취소한다.
- code 변경 verification은 advisor lifecycle 실패를 이유로 skip하지 않고 Tier B 동일 검증 또는 blocked로 끝난다.
- `schema_version: 2`와 optional lifecycle 필드 `attempt`, `termination`, `retry_of`, `lifecycle_fallback_reason`은 유지된다. 과거 `termination: silent_stall`은 reader 호환용으로만 허용하고 신규 producer는 생성하지 않는다.
- `authority_kind`, `authority_ref`, `result_acceptance_revoked`는 phase-local ledger 전용이며 report field를 추가하지 않는다.
- phase narrative의 `blocked`와 child invocation의 `approval_required`는 별도 namespace다. relay capability 한계는 lifecycle terminal이나 `environment_state_unknown`을 합성하지 않는다.
- abnormal disposition은 기존 `lifecycle_fallback_reason` string 내부의 신규 producer form일 뿐 새 report field나 termination enum이 아니다. 기존 v2 free-text와 missing optional field reader 호환, completed/nonterminal nullability도 유지된다.
- add-on 계약과 모델 routing의 `model_choice.fallback_reason` 의미는 변경하지 않는다.

## 영향 경로

- 공통 계약: `plugins/atp/docs/development/agent-team-protocol.md`, `plugins/atp/docs/development/platform-adapters.md`
- Host appendix: `plugins/atp/docs/development/codex-lifecycle-routing.md`, `plugins/atp/docs/development/index.md`
- 실행 주체: `plugins/atp/skills/task/SKILL.md`, `plugins/atp/agents/research-advisor.md`, `plugins/atp/agents/parallel-explorer.md`, `plugins/atp/agents/implementation-advisor.md`
- 실행 가능 계약: `tests/lifecycle-contract/fixtures/lifecycle-cases.json`, `tests/lifecycle-contract/fixtures/report-v2-environment.json`, `tests/lifecycle-contract/validate.py`
- 사용자·기여자 문서: FAQ 한·영, ADR-0020, 아키텍처 설계, release checklist §10과 각 카테고리 index

## 검증 상태

| 항목 | 상태 | 근거/다음 단계 |
|---|---|---|
| Fixture-first RED | pass | 새 fixture만 반영한 시점의 `python3 tests/lifecycle-contract/validate.py`가 exit 1. 첫 관련 실패는 구 validator의 `KeyError: 'observable_activity'`였다. 이는 이 좁은 RED 단계만 통과했다는 뜻이다. |
| Addendum 4 fixture/source/validator | pass | approval capability 직교성, axis/item marker와 aggregate derivation, abnormal current disposition case와 source invariant를 반영했고 최종 validator가 함께 검증했다. |
| 최종 lifecycle contract GREEN | pass | 2026-08-13 독립 invocation에서 `python3 tests/lifecycle-contract/validate.py`를 정확히 1회 실행해 exit 0과 `PASS: environment-authoritative lifecycle contract and compatibility fixtures`를 확인했다. |
| 새 구현 경로 direct probe | pass | 별도 read-only invocation `/root/final_environment_lifecycle_probe`가 environment `running` 뒤 `completed`로 종결됐다. 결과 계약을 충족했고 interrupt·retry·fallback·write는 0건이었다. wait timeout은 발생하지 않았으며 이는 실패 조건이 아니다. |
| Release checklist/metadata | pass (local) | base 4개 manifest를 2.12.0으로 동기화했다. add-on 2.3.0과 versionless Codex marketplace를 보존했고 상대 링크·index·§N·JSON·agent catalog·`git diff --check`를 통과했다. main 도달과 소비자 `/plugin update`는 merge 이후 사용자 확인 항목이다. |

설계 단계의 2026-08-12 14:58 probe는 progress 없는 정상 `running`이 wait timeout 두 번 뒤 `completed`될 수 있다는 반증 근거다. 2026-08-13의 별도 acceptance probe는 변경된 계약의 source/runtime 경로를 확인한 최종 증거로 구분한다.

## 관련 문서

- [ADR-0020](../adr/ADR-0020-environment-authoritative-subagent-lifecycle.md)
- [환경 권위 subagent lifecycle 아키텍처](../architecture/environment-authoritative-subagent-lifecycle-design.md)
- [ADR-0017](../adr/ADR-0017-subagent-lifecycle-recovery.md)
