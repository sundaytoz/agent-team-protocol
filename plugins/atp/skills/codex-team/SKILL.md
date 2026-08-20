---
name: codex-team
description: Codex에서 ATP가 subagent를 spawn, delegate, steer, collect하기 전에 반드시 사용하는 orchestration skill. 검증된 Codex capability profile을 적용하고, supported일 때만 built-in all-results workflow를 사용하며 manual wait/list polling을 금지한다.
---

# Codex team orchestration

이 skill은 Codex host 전용이다. ATP task가 Codex에서 한 명 이상의 subagent를 호출하려면 첫 collaboration action 전에 이 전체 `SKILL.md`를 읽고 아래 계약을 적용한다. 공통 lifecycle·report authority는 `../../docs/development/agent-team-protocol.md`, 검증된 Codex capability profile과 event mapping은 `../../docs/development/codex-lifecycle-routing.md`가 정본이다.

## 1. 적용 시점

- ATP가 Codex에서 subagent를 spawn, delegate, steer, collect하려는 모든 실행에 적용한다.
- Skill 선택과 전문 로드는 첫 `spawn_agent`, `followup_task`, `send_message`, `interrupt_agent`, 결과 취합보다 먼저 끝낸다.
- 소비 프로젝트의 매 task에서는 capability child, timeout probe, wait/list probe, runtime validator, source/install parity 검사를 실행하지 않는다. 릴리스에 포함된 capability profile을 사용한다.

## 2. 정상 dispatch 계약

이 절부터 §5까지는 배포 profile이 `host_managed_subagent_orchestration: supported`인 surface 또는 maintainer candidate smoke에만 적용한다. `unsupported | unknown`이면 §6의 no-spawn 경로를 사용한다.

1. Codex built-in subagent workflow를 사용한다.
2. 요청을 bounded child task로 나누고 필요한 agent 전원을 dispatch한다. 각 child prompt에는 다음을 명시한다.
   - 정상 경로에서 intermediate progress `MESSAGE`를 보내지 않는다.
   - 완료 시 결과 계약을 충족한 terminal result 한 건을 반환한다.
3. Parent orchestration 요청에는 요청한 모든 agent의 결과를 기다린 뒤 통합하도록 명시한다. Codex가 spawn, follow-up routing, 결과 대기와 thread lifecycle을 관리하도록 둔다. ATP orchestrator는 `wait_agent` polling loop나 `list_agents` polling을 만들지 않는다.
4. 모든 요청 agent/child의 terminal result가 도착할 때까지 invocation은 running이다. 전달된 nonterminal update는 progress일 뿐 terminal result나 completion authority가 아니다.
5. 요청한 모든 terminal result를 수신하고 결과 계약을 검증·취합하기 전에는 report invocation/session completion, `ended_at`, 사용자 최종 응답을 만들지 않는다.

## 3. 결과 barrier와 계측

- Dispatch마다 `requested_agents`와 반환된 environment identity를 report invocation identity에 명시적으로 연결한다. 표시명 변형은 identity 연결 규칙으로 정규화하되 environment identity를 대체하지 않는다.
- Report invocation은 exact field `environment_invocation_id`에 spawn이 반환한 identity를 기록한다. `environment_identity` 같은 alias로 바꾸거나 표시명만 기록하지 않는다.
- 요청한 agent 전원의 terminal delivery가 있어야 barrier가 열린다. `terminal_deliveries == collected_results == requested_agents == spawn_calls`를 검증한다.
- 정상 Codex managed orchestration에서 `manual_wait_calls: 0`, `list_calls: 0`, `interrupt_calls: 0`, `semantic_recovery_actions: 0`이어야 한다.
- 알 수 없는 telemetry는 `null`로 기록한다. 관측하지 못한 값을 0으로 합성하지 않는다.
- Scheduling ledger row는 `recorded_at`, `await_id`, `owner_report_invocation_id`, `event`, concrete `source_ref`, `details`의 six-field envelope을 유지한다. `owner_report_invocation_id`는 `null`이 아니라 spawn 전에 할당한 실제 report invocation ID여야 한다. Aggregate measurement는 `source_ref`가 가리키는 terminal result의 report invocation ID를 owner로 사용한다.
- Managed capability row의 `details`에는 exact keys와 values `formal_adapter_enabled: false`, `manual_wait_polling_supported: false`, `host_managed_subagent_orchestration: supported`, `team_execution_enabled: true`, `selected_mode: host_managed_subagent_orchestration`을 모두 기록한다. `managed` 같은 축약 mode나 key 생략을 허용하지 않는다.
- Measurement의 `mode`도 exact value `host_managed_subagent_orchestration`이다. `input_tokens`, `cached_input_tokens`, `output_tokens`, `latency_ms`, `steering_latency_ms`를 관측하지 못하면 key를 생략하지 않고 각각 `null`로 기록한다.
- 실행 중 알 수 없는 transcript ordinal을 모델이 예측해 쓰지 않는다. 실제 생성 가능한 session/report/environment identity와 monotonic event identity를 먼저 기록하고, maintainer validator가 보존된 transcript event와 사후 대조한다.

## 4. lifecycle과 recovery

- `MESSAGE` 같은 실제 nonterminal update가 전달돼도 invocation은 `running`을 유지한다. 그 update를 terminal delivery나 collected result로 세지 않는다.
- Retry, interrupt, fallback, result-acceptance authority mutation과 write-ownership mutation은 명시적 terminal failure/interruption이 관측되고 기존 사용자 승인 계약을 충족한 경우에만 수행한다.
- Capability error가 실제 관측되면 automatic wait/list polling, retry, interrupt, fallback 또는 automatic Tier B 전환으로 보상하지 않는다. 마지막 environment-authoritative state와 authority를 보존하고 현재 요청 의도에 맞는 blocked/user-decision 경로를 사용한다.
- 같은 invocation에 보내는 follow-up은 steering 또는 continuation이며 clean retry가 아니다.

## 5. authority 경계와 종료 순서

Codex host는 child execution, follow-up routing, all-results wait와 terminal delivery를 소유한다. ATP는 logical task/DAG, result contract validation과 integration, approval/recovery decision, result acceptance, write ownership, report와 session lifecycle을 소유한다.

종료 순서는 다음과 같다.

1. 모든 요청 subagent terminal result 수신
2. 결과 계약 검증 및 통합
3. verification
4. retrospective
5. retrospective 결과를 report에 반영
6. report 재스테이징
7. staged 상태 재검증
8. 요청 범위 mutation/commit/push/remote verification 완료
9. session `ended_at` 기록
10. report 형식 최종 read-only 검증
11. 사용자 최종 응답

미래 `ended_at`을 미리 serialize하거나 terminal delivery 이전 transcript event에서 invocation/session termination을 쓰지 않는다.

## 6. 배포된 capability profile

현재 배포 판정은 `formal_adapter_enabled: false`, `manual_wait_polling_supported: false`, `host_managed_subagent_orchestration: unsupported`, `team_execution_enabled: false`다. 적용 surface와 검증 버전·공식/경험적 근거는 Codex appendix에서만 관리한다. 실행 중 임의 추론으로 이 profile이나 result collection 계약을 덮어쓰지 않는다.

Codex CLI 0.147.0 maintainer smoke에서 terminal-only 1-agent는 통과했지만 nonterminal 뒤 terminal 1-agent와 staggered 2-agent all-results barrier가 실패했으므로 전체 ATP managed contract는 `unsupported`다. App/IDE surface는 공식 제품 설명과 별개로 동일 smoke를 수행하지 않아 `unknown`이다. 세 release smoke가 모두 통과하기 전 `supported`로 올리지 않는다.

이 profile에서는 정상 소비 task가 child를 spawn하지 않는다. Manual wait/list polling, automatic retry/interrupt/fallback 또는 automatic Tier B로 보상하지 말고, 실제 독립 subagent가 필요한 `$atp:task`를 명시적 blocked/user-decision 경로로 반환한다. 독립성이 필요 없는 Tier B 전환은 사용자가 명시적으로 선택한 경우에만 수행한다.
