---
kind: development
title: Codex subagent lifecycle and wait/wakeup routing appendix
description: Agent Team Protocol §2.5의 host-neutral lifecycle과 timeout-free wait/wakeup 계약을 Codex collaboration API에 매핑하는 조건부 appendix.
owner: template-maintainer
stability: draft
host_scope: codex
last_reviewed: 2026-08-13
---

# Codex subagent lifecycle and wait/wakeup routing appendix

이 문서는 Codex host에서만 읽는 조건부 appendix다. 상태·승인·clean retry·phase 종단과 논리 `await_invocations`의 정본은 `agent-team-protocol.md` §2.5이고 capability 판정 정본은 `platform-adapters.md` §3.1~§3.2다. 여기서는 Codex collaboration environment가 정상 API에서 실제 보장하는 의미만 매핑한다. 모델 선택 fallback은 protocol §5.7과 `codex-spark-routing.md`의 별도 관심사다.

## 1. Current-host 결론

```yaml
requested_mode: environment_subscription
effective_mode: unavailable
adapter_enabled: false
fallback: none
timed_fallback: false
disposition: wait_wakeup_capability_unavailable
```

현재 Codex collaboration API는 persistent timeout-free subscription identity, target별 `any | all`, compact delta/event identity/dedup/coalescing 계약을 제공하지 않는다. 따라서 formal wait/wakeup all-required gate를 통과하지 못한다. ATP는 이 host에서 timed wait를 scheduling adapter나 fallback으로 호출하지 않으며, 반복 상태 조회로 빈 capability를 합성하지 않는다.

호출 주체는 `wait_wakeup_capability_unavailable`을 phase-local `wait-wakeup-events.jsonl`에 정확히 1회 기록한다. Automatic wait/list/retry/interrupt/phase fallback은 각각 0건이다. Child의 마지막 environment-authoritative lifecycle state, result acceptance authority, write ownership을 보존하고 phase를 `blocked`로 반환한다. 사용자가 host-native event-only external continuation을 명시 선택했고 resume identity와 cancellation contract가 모두 있을 때만 그 continuation을 등록할 수 있다. 현재 normal collaboration API만으로는 이 경로도 제공되지 않는다.

이 판정은 scheduling capability gap이며 child failure, stall, interruption 또는 `environment_state_unknown`이 아니다. Status API unavailable/error가 별도로 실제 관측된 identity만 `environment_state_unknown`으로 정규화한다.

## 2. Wait/wakeup capability matrix

판정값은 `supported | unsupported | unknown`이다. `supported`인 부분 기능도 §2.5의 all-required gate를 단독 충족하거나 formal adapter 활성화를 의미하지 않는다.

| capability | 판정 | gate | API 근거와 처리 |
|---|---|---|---|
| `timeout_free_suspend` / subscription handle | unsupported | required | bounded `wait_agent`에는 persistent await identity가 없고 시간 경계 반환이 root turn을 재개하므로 gap evidence일 뿐 adapter가 아니다 |
| bounded global mailbox wait | supported | ineligible | `wait_agent`의 live-agent mailbox wait는 target/condition subscription이 아니며 ATP가 scheduling path로 사용하지 않는다 |
| environment-internal re-await without model wake | unsupported | required | root-visible 반환 뒤 environment 내부에서 같은 await를 이어갈 control이 없다 |
| `targeted_wait_any` | unsupported | required | 선택 target/filter 입력이 없다 |
| `targeted_wait_all` | unsupported | required | `targets`와 `condition: all` barrier가 없다 |
| `terminal_event_subscription` — completed | supported | required subset | final-status notification/result 전달은 있으나 전체 terminal 종류의 structured subscription은 아니다 |
| `terminal_event_subscription` — failed/interrupted detail | unknown | required | 공개 반환 계약이 두 종류와 원인/detail을 구조적으로 보장하지 않는다 |
| `approval_event_subscription` | unknown | required | `approval_required` structured subscription을 공개 계약이 보장하지 않는다 |
| `user_steering_preemption` | supported | required subset | active mailbox wait는 새 user input에 조기 control을 반환할 수 있으나 formal subscription은 없다 |
| user steering numeric latency SLA | unknown | advisory | 조기 반환 가능성 외 ms bound는 없다. ATP는 응답성 보상 timer를 만들지 않는다 |
| `await_cancellation` | unsupported | required | await identity나 subscription cancel token이 없다 |
| `compact_changed_invocation_delta` | unsupported | required | changed invocation만 담은 structured delta payload가 없다 |
| `stable_event_identity` | unsupported | required | stable `event_id`가 반환 계약에 없다 |
| `environment_deduplication` | unsupported | required | cursor/dedup token과 exactly-once batch 계약이 없다 |
| `completion_coalescing` | unknown | required | resume dispatch 전 인접 event를 하나의 causal batch로 묶는 보장이 없다 |
| `internal_keepalive_no_model_wake` | unsupported | required | keepalive/scheduler가 environment 내부에서 root resume 없이 동작하는 API가 없다 |
| scheduler/watchdog registration | unsupported | required host function | 등록·해제·health와 event-only resume 계약이 없다 |
| invocation current-turn cancellation | supported | separate | `interrupt_agent`는 child turn control이며 await subscription cancellation을 대체하지 않는다 |
| root token/live-context telemetry | unknown | advisory | collaboration API 표면에서 causal live usage를 보장하지 않는다 |
| explicit compaction control | unsupported | advisory | collaboration API 표면에 compaction trigger/control이 없다 |

결론은 `adapter_enabled: false`다. Current host에서 “관심 상태 변화가 없으면 root model 호출도 0건”인 end-to-end 진행을 ATP 문서나 호출 조합만으로 구현할 수 없다. Host가 protocol §2.5의 timeout-free handle, target condition, terminal/approval/steering/cancel subscription, stable event ID, compact delta, dedup/coalescing을 함께 제공해야 한다.

## 3. Lifecycle 도구 매핑

Scheduling adapter가 비활성이어도 lifecycle authority와 명시적 사용자 승인형 recovery는 유지한다.

| 공통 의미 | Codex mapping | 제약 |
|---|---|---|
| environment status snapshot | `list_agents` | completion race 재확인 등 lifecycle 계약이 명시적으로 요구할 때만 사용한다. Capability-gap 자동 보상이나 inertial polling에는 사용하지 않는다 |
| final-status/result delivery | collaboration environment가 전달한 final notification과 agent result | environment가 명시한 terminal 의미만 정규화하고 결과 계약 검증 뒤 취합한다 |
| 기존 invocation 종결 요청·결과 | `interrupt_agent` | explicit terminal recovery 또는 사용자 취소 뒤 사용자 승인 하에서만 호출한다. 반환된 실제 상태만 기록하고 write isolation은 ownership·disk 상태도 확인한다 |
| read-only result acceptance isolation | ATP-local ledger `result_acceptance_revoked` | 사용자 승인·completion race 뒤 old identity future result 수용만 철회한다. Codex terminal event나 write isolation을 합성하지 않는다 |
| clean retry | `spawn_agent` | 반환된 새 environment identity가 기존 대상과 다를 때만 새 `attempt`로 센다 |
| same-invocation continuation/diagnostic | `followup_task` | clean retry가 아니며 `attempt`를 증가시키지 않는다. 기존 invocation 종결 전 새 logical task를 보내 retry를 흉내 내지 않는다 |
| retry context 범위 | `spawn_agent.fork_turns` + 명시 payload | 고정 turn 수를 정책으로 두지 않는다. 최소 권위 payload가 정본이고 fork 범위는 host/config·민감도에 맞춘다 |

Task name suffix나 표시명은 가독성 보조일 뿐 identity 정본이 아니다. `spawn_agent`가 돌려준 새 environment identity를 report의 새 `id`와 연결하고 `retry_of`에는 직전 report invocation ID를 기록한다.

## 4. Codex 상태·event 정규화

ATP는 collaboration environment가 실제 반환하거나 전달한 상태 문자열과 notification 의미만 공통 상태로 정규화하며 존재하지 않는 세부 상태를 보간하지 않는다.

| Codex 관측 | ATP 정규화 |
|---|---|
| lifecycle 목적의 명시 조회가 invocation을 `running`으로 반환 | `running` 유지 |
| 명시 조회가 그 밖의 상태를 반환 | 공통 계약과 의미가 일치할 때만 그대로 정규화; 의미가 불명확하면 `environment_state_unknown` |
| final-status notification과 최종 결과 전달 | environment가 명시한 terminal state; `completed`는 반환 계약 검증 후 취합 |
| `interrupt_agent`가 현재 turn 중단을 명시 | 해당 attempt의 `interrupted`; partial write·ownership 확인 |
| snapshot/status API 부재·오류 또는 의미 불명 | `environment_state_unknown`; failure/terminal 아님 |

현재 공개 계약은 `approval_required`와 모든 failure 원인·terminal detail을 별도 structured event로 보장하지 않는다. 이를 supported로 선언하거나 output·silence·경과 시간에서 합성하지 않는다. 실제 runtime response가 `approval_required`를 명시했다면 relay/control 미지원과 무관하게 그 state를 보존한다. Relay 불가 child는 environment provenance·report/environment identity·concrete `source_ref`·concern/capability evidence·ledger를 반환하고 `ended_at: null`, termination 생략, mutation 0을 유지한다. Report의 `Summary` / `Open Items` / `concerns` narrative만 blocked다.

Capability가 복구돼 same environment identity continuation이 가능하면 `attempt`와 retry accounting을 바꾸지 않는다. 이후 status API unavailable/error가 실제 관측된 경우에만 그 identity를 `environment_state_unknown`으로 바꾼다. Progress/message/tool output과 그 부재, 같은 `running` snapshot, internal keepalive는 lifecycle transition이나 root wake 사유가 아니다.

## 5. 승인 후 종결과 clean retry

1. 명시적 failure/interruption/environment blocker 뒤 사용자가 retry를 승인하면, lifecycle 목적의 authoritative status 조회 또는 이미 전달된 새 environment event로 completion race를 재확인한다. Old invocation이 이미 `completed`면 retry를 취소하고 기존 결과를 검토한다.
2. Environment가 여전히 실행 중이고 termination control을 제공하면 `interrupt_agent`를 먼저 호출한다. Environment가 반환한 event와 read/write 성질을 확인한다. Termination control이 unsupported라도 read-only임이 확정된 old identity에는 ATP-local result acceptance isolation을 사용할 수 있으나 write-capable scope에는 사용할 수 없다.
3. Read-only recovery가 계속되면 같은 old report/environment identity의 11개 공통 field와 `scope`/`rationale`/`source_ref`를 가진 `result_acceptance_revoked` advisor ledger event를 기록한다. 이 event 뒤에만 새 identity를 spawn한다.
4. Write-capable invocation은 old ownership 회수와 partial write 분류가 끝나기 전 새 invocation을 만들지 않는다. Codex가 termination/isolation을 확인할 수 없으면 동일 write scope의 새 spawn은 금지한다.
5. 새 invocation payload에는 목표, 권위 파일, 확정 계약, write scope, 보존할 partial, 필수 산출물, 검증·반환 형식을 명시한다. Transcript 상속에 의존해 권위 계약을 생략하지 않는다.
6. 새 identity를 확인한 뒤에만 `attempt`를 증가시키고 `retry_of`를 연결한다. Same-invocation follow-up은 이 단계를 대체하지 않는다.

Scheduling capability gap만으로는 이 절을 열지 않는다. Gap path의 automatic status 조회, interrupt, retry, phase fallback은 모두 0건이다.

## 6. Late completion과 invocation authority

Codex environment가 old invocation의 final completion/result를 전달하면 먼저 environment `completed`로 기록한다. 같은 old identity의 `result_acceptance_revoked` 또는 write ownership 회수가 선행한 경우에만 advisor가 `authority_kind`와 그 선행 anchor의 `authority_ref`를 phase ledger에 연결해 report `termination: late_completion` disposition을 기록한다. 선행 authority 철회가 없으면 정상 completion race 후보이며 `late_completion`으로 바꾸지 않는다.

Read-only late result와 write ownership 회수 뒤 disk write가 없는 late result는 quarantine-only이며 자동 merge·취합·성공 판정·ownership pause를 하지 않는다. Old invocation의 실제 late disk write가 보인 경우에만 affected scope와 dependency closure를 persisted pause하고 diff/ownership 충돌을 중재한다. Write isolation을 확인할 수 없으면 새 owner의 동일 scope 작업을 진행하지 않고 protocol §2.5의 Tier B 직접 수행 또는 blocked 종단을 적용한다.

Capability-gap blocked 반환 뒤에도 authority/ownership이 보존되므로, 이후 전달된 completion은 정상 후보다. 별도 사용자 승인형 recovery로 authority가 먼저 철회된 identity만 late-completion quarantine 대상이다.

## 7. 유한 clean retry와 phase 종단

명시적 terminal failure 뒤 logical task별 clean retry 상한과 retry payload의 fork 범위는 host/config가 정할 수 있다. 경과 시간, progress 부재, 동일 snapshot 조회 횟수는 retry 한도를 소비하거나 phase fallback을 열지 않는다.

승인된 clean retry도 environment가 명시한 같은 terminal failure로 끝나거나 retry 상한이 소진되면 protocol §2.5의 phase별 종단으로 수렴한다. 특히 code 변경 검증은 Tier B 직접 실행 또는 blocked이며 lifecycle 장애를 이유로 skip할 수 없다.

Report schema는 v2를 유지한다. `attempt`, `termination`, `retry_of`, `lifecycle_fallback_reason` 네 optional lifecycle field의 의미를 바꾸거나 scheduling field를 `Invocations[]`에 추가하지 않는다. Wait/wakeup capability와 batch 측정은 별도 `wait-wakeup-events.jsonl`만 사용한다.

## 8. Codex 실행 체크리스트

- [ ] formal wait/wakeup profile이 `adapter_enabled: false`이고 timed scheduling fallback 실행이 0건인가?
- [ ] `wait_wakeup_capability_unavailable`을 phase-local scheduling ledger에 정확히 1회 기록했는가?
- [ ] gap 뒤 automatic wait/list/retry/interrupt/fallback이 각각 0건이고 child state·result acceptance·write ownership을 보존했는가?
- [ ] phase가 blocked 또는 사용자 선택 event-only external continuation으로만 수렴했는가?
- [ ] lifecycle state·terminal event는 collaboration environment의 실제 snapshot/notification에서만 관측했는가?
- [ ] `running`을 그대로 유지하고 경과 시간·progress/heartbeat 부재·동일 snapshot으로 전이시키지 않았는가?
- [ ] 미보장 approval/failure detail을 합성하지 않고, 실제 `approval_required`는 relay/control 미지원이어도 보존했는가?
- [ ] 명시적 recovery에서 사용자 승인 전 `interrupt_agent`, `spawn_agent`, phase fallback 실행이 0건인가?
- [ ] same-invocation follow-up을 clean retry로 세거나 `attempt`를 올리지 않았는가?
- [ ] read-only retry는 same-identity `result_acceptance_revoked`를 새 spawn 전에 기록했는가?
- [ ] write retry 전 termination/isolation, partial diff, ownership 회수를 확인했는가?
- [ ] late completion은 선행 authority 철회와 identity/ref가 일치하고, late disk write가 없으면 quarantine-only인가?
- [ ] report v2 optional lifecycle field 네 개를 유지하고 scheduling metadata는 별도 ledger에만 두었는가?
