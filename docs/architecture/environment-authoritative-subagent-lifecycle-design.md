---
kind: architecture
title: 환경 권위 subagent lifecycle과 host-managed orchestration 설계
status: implemented
implementation_status: implemented
verification_status: l1-verified-l2-pending
date: 2026-08-19
owner: template-maintainer
stability: living
relates_to: [ADR-0017, ADR-0020, ADR-0021, ADR-0022, ADR-0023, ADR-0024]
supersedes_draft: codex-lifecycle-evidence-epoch-design.md
---

# 환경 권위 subagent lifecycle과 host-managed orchestration 설계

## 문서 상태

이 문서는 lifecycle correctness와 orchestration scheduling, 두 개의 독립 계약층을 다룬다. [ADR-0020](../adr/ADR-0020-environment-authoritative-subagent-lifecycle.md)은 lifecycle 권위, [ADR-0021](../adr/ADR-0021-environment-owned-wait-wakeup-scheduling.md)은 formal timeout-free subscription, [ADR-0022](../adr/ADR-0022-pre-spawn-wait-wakeup-capability-gate.md)는 pre-spawn ordering을 결정했다. [ADR-0024](../adr/ADR-0024-host-managed-subagent-orchestration.md)는 ADR-0023의 model-driven bounded-wait 재진입을 supersede하고 product-managed all-results barrier와 release-time capability evidence를 채택했다. 이 결정들은 ADR-0020의 lifecycle 권위를 유지한다.

전체 문서의 현재 상태는 **implemented, deterministic L1 verified, isolated maintainer smoke capability rejected**다. `python3 tests/lifecycle-contract/validate.py`는 environment-authoritative lifecycle, formal/managed mode negotiation, approval/steering/dedup, explicit recovery와 legacy/current report schema v2 compatibility를 통과했다. Checked-in managed fixture 3종은 future supported implementation의 skill-first, all-results terminal barrier, manual wait/list/interrupt 0과 completion serialization 순서를 검사한다.

2026-08-18 strict preflight 초안은 Codex CLI 0.147.0 격리 환경에서 collaboration call 0과 unavailable event 1을 확인했지만, formal scheduling 최적화 부재를 team 실행 불가로 오해했다. ADR-0023은 이 초안을 교정했다. Historical 관측 JSONL의 spawn 1, wait 13, list 2, timeout 11은 짧은 wait/list 반복의 비용 반증 자료로 보존한다.

Current Codex 제품은 managed subagent workflow를 제공하지만 CLI 0.147.0 smoke에서 ATP의 full all-results correctness contract를 충족하지 못했다. 2.15.0은 formal adapter와 manual polling을 모두 unsupported로 유지하고 tested CLI의 `host_managed_subagent_orchestration`을 `unsupported`, team execution을 disabled로 판정한다. Deterministic runtime fixture는 future supported implementation이 충족해야 할 계약이며 capability evidence를 대신하지 않는다.

2026-08-19 기존 실제 세션은 wait가 nonterminal update를 반환한 뒤 모델이 재대기하지 않아 terminal 전에 report completion을 기록했다. 새 isolated smoke도 product-managed 경로가 delayed/staggered terminal을 보장하지 않음을 확인했다. 2.15.0은 첫 collaboration action 전에 Codex 전용 skill을 읽고, unsupported profile이면 spawn이나 manual polling 대신 blocked/user-decision으로 수렴한다.

Source-spec 검증은 requested/effective mode 분리, advisor scheduling ledger, 반환 disposition, preallocated report identity를 유지한다. ADR-0024 이후에는 formal mode 보존, Codex host-managed mode, general Tier B, explicit independence blocker와 non-Codex Tier A-flat 불변을 함께 검사한다.

이 설계는 폐기된 `codex-lifecycle-evidence-epoch-design.md` 초안을 대체한다. 시간, wait 횟수, progress/heartbeat 유무로 ATP가 subagent의 생존 상태를 추론하지 않고, host environment가 제공하는 lifecycle 상태와 이벤트를 권위 정보로 사용한다.

## 결론

Subagent lifecycle과 wait/wakeup scheduling은 서로 다른 계약층이며 둘 다 environment 권위를 침범하지 않는다.

- Formal mode의 environment는 invocation identity와 실행 상태뿐 아니라 timeout-free suspend, 관심 event 구독, internal keepalive, wake scheduling, deduplication, coalescing, compact delta, steering/cancellation 전달을 소유한다. Managed mode에서는 host가 spawn, routing, all-results wait와 terminal delivery를 소유한다.
- ATP는 task/DAG, 관심 invocation과 `any|all` 조건, 결과 계약 검증·취합, approval relay 정책, 명시적 failure 뒤 retry/fallback 판단, result acceptance authority, write ownership과 late completion 격리를 소유한다.
- `wait` timeout은 lifecycle event가 아니다. Formal scheduling 수단이나 managed correctness primitive로 승격하지 않으며 ATP orchestrator는 manual wait/list polling loop를 만들지 않는다.
- progress/heartbeat는 사용자 경험과 작업 설명을 위한 선택 신호다. correctness 또는 liveness 판정 입력으로 사용하지 않는다.
- environment가 `running`을 보고하는 동안 ATP는 시간이 얼마나 지났든 `running`으로 취급한다.
- environment가 상태를 제공하지 못하면 `environment_state_unknown`으로 표현한다. 이를 stall이나 failure로 바꾸어 추론하지 않는다.
- Formal capability가 불완전해도 release-verified host-managed orchestration이 있으면 team execution을 유지한다. Formal/managed orchestration이 모두 없을 때만 일반 작업은 Tier B, 실제 독립성 요구는 blocker/options로 수렴한다. Runtime capability error가 관측되면 자동 전환하지 않고 기존 child state·authority·ownership을 보존한다.

## 배경과 반증 근거

### 반복 wait 관측

Codex 세션 `019ff34b-fbf9-7b10-a5f8-584334af1b0a`를 2026-08-12 11:21 KST에 집계한 결과다.

| 항목 | 횟수 |
|---|---:|
| `wait_agent` | 211 |
| 30초 wait | 195 |
| timeout | 171 |
| completed wait | 39 |

`Waiting for agents / Finished waiting / No agents completed yet`는 wait timeout이 UI에 노출된 결과다. 이 메시지만으로 subagent 실패나 ATP 장애를 의미하지 않는다. 문제는 timeout을 lifecycle 판단 재료로 삼아 동일한 관측을 반복하는 orchestration 정책이었다.

### 직접 lifecycle probe (설계 근거, 구현 전)

2026-08-12에 `/root/direct_lifecycle_probe`를 다음 조건으로 직접 실행했다.

- 별도 subagent thread
- progress message 금지
- read-only 작업
- final result만 반환

| 시점/관측 | 결과 |
|---|---|
| 시작 | 14:58:01 KST, `running` |
| 첫 60초 wait | timeout, 계속 `running` |
| 둘째 60초 wait | timeout, 계속 `running` |
| 완료 | 15:00:43 KST, 정상 final 반환 |
| 총 실행 시간 | 2분 42초 |
| filesystem 변경 | 없음 |
| probe 판정 | `runtime-path-normal` |

즉, 정상 invocation도 progress 없이 2분 이상 `running`일 수 있고 wait timeout이 두 번 발생한 뒤 정상 완료될 수 있다. 같은 세션의 설계·문서 advisor도 긴 무진행 구간 뒤 정상 완료했다. 따라서 다음 신호는 failure나 stall의 충분조건이 아니다.

이 probe는 environment-authoritative 방향을 선택한 **사전 반증 근거**다. 변경된 runtime 계약의 최종 acceptance probe는 2026-08-13에 별도 read-only invocation으로 수행했으며, environment의 `running`과 `completed`만 상태 전이 근거로 사용해 통과했다.

- 첫 progress가 일정 시간 안에 없음
- heartbeat가 일정 횟수 누락됨
- 동일한 `running` snapshot이 반복됨
- `wait`가 일정 횟수 timeout됨
- parent가 subagent 내부 tool/output을 관측하지 못함

### Token-efficiency 원인과 baseline

Lifecycle correctness가 해결돼도 timed wait가 반환될 때마다 root model이 재개되면 누적 context가 다시 입력된다. 원인은 대기 시간 자체가 아니라 다음 반복이다.

```text
timed wait 반환
  -> root model 재개와 누적 context 재입력
  -> 상태 변화가 없어도 새 wait/list 판단
  -> 반복
```

2026-08-12 root JSONL의 재현 가능한 집계는 `wait_agent` 209회, timeout 148회, root 직접 spawn 34회, root token 60,582,015, compaction 1회(최종 root 누적량의 93.06% 시점)다. Wait 결과 뒤 model usage를 event ordering으로 연결한 proxy는 input 34,471,967, cached input 34,161,408, output 21,579다. Nested child 15개, 전체 invocation 50개, tree token 102,214,528은 사용자 제공 historical 수치이지만 단일 root JSONL만으로 독립 검증할 수 없어 검증된 root 수치와 구분한다.

별도 작은 probe의 timed wait 두 번은 input 212,698, cached input 210,432, output 71을 사용했다. 첫 10초 timeout과 다음 completion 모두 root model을 재개했다. 이 관측은 “timeout을 길게 하자”가 아니라 root-visible timeout 자체를 formal path에서 제거해야 한다는 근거다.

ATP 2.12.0 source와 설치 cache의 지정 9개 lifecycle/runtime 파일은 변경 전 byte parity를 확인했다. 두 위치 모두 lifecycle 무전이는 구현했지만 root resume 억제, target `any|all`, event identity/deduplication, coalescing, compact delta 계약은 없었다. 설치 cache는 immutable evidence로 유지하며 2.13.0 source 변경을 cache에 직접 역적용하지 않는다.

### 결정론적 비교 workload

고비용 historical session을 재실행하지 않고, target 두 개가 `running`, unchanged/internal keepalive 세 번, 인접 completion 두 번을 내는 동일 trace를 fixture로 고정한다.

| mode | root model resume | wait/subscription call | list call | 결과 |
|---|---:|---:|---:|---|
| historical short polling | 5 | timed wait 5 | 3 | 비용 baseline 전용 |
| current tested Codex CLI ATP | release smoke에서 일부 terminal만 전달 | ATP manual wait 0 | 0 | full barrier unsupported, team execution disabled |
| logical environment subscription | 1 | logical await 1 | 0 | completion 두 개를 compact batch 하나로 전달 |

Current Codex 행은 formal subscription의 event schema나 full all-results correctness를 주장하지 않는다. ATP의 manual wait/list polling은 제거하며 tested CLI team execution은 disabled다. App/IDE와 정확한 scheduler 내부 wake/token 절감은 empirical evidence가 없으므로 `unknown`이다.

## 책임 경계

| 계약 | Environment가 소유 | ATP가 소유 |
|---|---|---|
| lifecycle | invocation 생성·identity, queued/running/terminal/approval 관측, interrupt/cancel 실제 결과 | logical task와 invocation 계보, result validation, approval relay 정책, explicit failure 뒤 recovery 판단 |
| wait/wakeup | persistent await identity, timeout-free suspend, internal keepalive, terminal/approval/steering/cancel event delivery | 관심 target, `condition: any|all`, 기본 wake set, DAG barrier와 batch 결과 취합 |
| event delivery | stable event ID, deduplication, completion coalescing, changed-invocation compact delta | result/detail artifact 저장과 report의 compact reference |
| effect authority | host termination/write-isolation 결과 | read-only result acceptance authority, write ownership, completion race와 late completion disposition |

Environment는 timeout/keepalive를 root-visible 반환으로 만들지 않는다. ATP는 environment scheduler를 timer, timed wait 또는 반복 status query로 대체하지 않는다. 실행 상한·watchdog·steering responsiveness·await cancellation은 host가 맡고, ATP가 이 gap을 polling으로 보상하지 않는다.

## Timeout-free `await_invocations` 계약

Formal scheduling mode는 다음 host-neutral 논리 API 하나다.

```text
await_invocations({
  targets,   // 중복 없는 environment invocation identity 집합
  condition, // any | all
  wake_on    // completed | failed | interrupted | approval_required | user_steering
})
```

Environment는 persistent `await_id`를 만들고 관심 event 전까지 root model turn을 suspend한다. `any`는 첫 관심 event와 resume dispatch 전 인접 event를 하나의 batch로 모은다. `all`은 target 전부의 terminal event를 누적하되 approval, steering, explicit await cancellation, backend capability error는 즉시 barrier를 단락한다. Timeout·keepalive interval·coalescing window·watchdog은 ATP 인자가 아니며 root-visible timeout event가 없다.

반환은 `await_id`, `batch_id`, `wake_reason`, changed invocation만 담은 `deltas[]`, `control_delta`로 구성한다. 각 delta에는 stable `event_id`, `environment_invocation_id`, state, concrete `source_ref`, optional `detail_ref`가 있어야 한다. 같은 event ID는 한 batch에만 들어가고, retry는 새 environment invocation identity를 사용한다. 전체 agent snapshot과 상세 결과 원문은 root context에 복제하지 않고 artifact/ref로 분리한다.

필수 capability는 `timeout_free_suspend`, targeted wait-any/all, terminal/approval subscription, steering preemption, await cancellation, compact delta, stable event identity, environment deduplication, completion coalescing, internal keepalive no-model-wake다. 하나라도 `unsupported|unknown`이면 formal adapter는 비활성이다.

## Execution mode 협상과 capability gap 수렴

첫 child spawn 전 formal capability와 배포된 host-managed profile을 별도 판정한다.

1. Formal capability 12개가 모두 supported면 `environment_subscription`을 사용한다.
2. Formal adapter가 불완전해도 managed orchestration이 supported면 `host_managed_subagent_orchestration`으로 child identity·authority·ownership과 spawn을 정상 생성한다.
3. 두 orchestration mode가 모두 없고 일반 작업이면 `tier_b_sequential`을 적용한다.
4. 두 mode가 모두 없고 실제 독립 child가 필수면 `blocked_explicit_independence`로 선택지를 제공한다.

Managed mode는 ATP manual wait/list polling, synthetic terminal, automatic retry/interrupt/fallback과 authority mutation을 만들지 않는다. Spawn 뒤 capability가 실제 unavailable/error가 되면 child의 마지막 state, result acceptance authority와 write ownership을 보존하고 blocked/user-decision 경로를 사용한다. Child가 뒤늦게 완료되면 선행 authority 철회가 없는 한 정상 completion 후보로 검토한다.

## 권위 상태 모델

아래 이름은 host별 native 상태를 ATP 의미로 정규화하기 위한 개념 모델이다. host adapter는 실제 environment가 명시적으로 제공한 이벤트만 매핑한다.

```text
spawn_requested
  -> accepted | queued | running

accepted | queued | running
  -> approval_required
  -> completed
  -> failed
  -> interrupted

approval_required
  -> queued | running
  -> failed | interrupted

상태를 확인할 수 없음
  -> environment_state_unknown
```

`blocked`는 두 종류를 구분한다.

1. environment가 권위 상태로 제공하는 `blocked`: environment state로 매핑한다.
2. agent final/result가 작업상 blocker를 보고하는 `blocked`: terminal result 의미로 검토한다.

문자열이나 reasoning 내용만 보고 실행 중 invocation을 임의로 terminal 처리하지 않는다.

## 이벤트 해석 규칙

| 관측 | lifecycle 전이 | ATP 동작 |
|---|---|---|
| spawn accepted/thread identity | environment 상태대로 전이 | invocation 계보 기록 |
| `queued` | `queued` 유지 | terminal event 대기 |
| `running` | `running` 유지 | terminal/approval event 대기 |
| progress/output/tool event | 전이 없음 | UX·진행 설명에만 사용 |
| host gap evidence에서 관측된 `wait` timeout | 전이 없음 | lifecycle 입력으로 쓰지 않음; ATP formal scheduling path에서는 timed wait 자체를 시작하지 않음 |
| 동일 상태 snapshot | 전이 없음 | 상태를 그대로 유지 |
| `approval_required` | 권위 상태 전이 | 사용자 승인 흐름 연결 |
| `completed` | terminal | result 계약 검증 후 취합 |
| `failed` | terminal | 원인 보고 후 recovery 판단 |
| `interrupted` | terminal | ownership과 partial write 확인 |
| 명시적 environment `blocked` | environment 의미대로 처리 | 사용자 결정 또는 host 지침 적용 |
| 상태 API 부재/오류 | `environment_state_unknown` | 실패 추론 없이 capability 한계 보고 |

핵심 불변식은 다음과 같다.

1. timeout 개수와 경과 시간은 lifecycle state를 변경하지 않는다.
2. progress/heartbeat 부재는 lifecycle state를 변경하지 않는다.
3. environment가 `running`인 동안 ATP 상태도 `running`이다.
4. retry/fallback 검토는 명시적 terminal failure, interruption, environment blocker, 사용자 취소처럼 권위 있는 사건에서만 시작한다.
5. interrupt/retry/fallback 같은 mutation은 기존 사용자 승인 게이트를 유지한다.

## Approval state와 relay/control capability

Environment가 관측시킨 lifecycle state와 ATP가 사용자에게 relay하거나 같은 invocation을 continuation할 capability는 독립된 축이다.

| environment status 관측 | relay/control capability | child invocation 정본 상태 | 처리 |
|---|---|---|---|
| `approval_required` | supported | `approval_required` | environment provenance와 concrete `source_ref`를 ledger에 기록하고 사용자에게 relay; same identity continuation의 attempt/retry 불변 |
| `approval_required` | unavailable/unknown | `approval_required` | 아래 safe return 적용; lifecycle 재분류와 mutation 0건 |
| status API unavailable/error 또는 의미 불명 | 임의 | `environment_state_unknown` | nonterminal unknown으로 기록하고 approval/failure를 추정하지 않음 |

relay/control이 불가능한 advisor는 child ledger의 environment state와 identity를 보존하고, capability evidence와 affected logical task를 `concerns`에 기록한다. child payload는 `ended_at: null`이고 `termination`을 생략하며 `lifecycle_fallback_reason`은 null 또는 생략한다. interrupt/cancel, 승인 합성, retry/fallback, invocation authority/ownership mutation, attempt/retry 증가는 모두 0건이다.

relay 가능한 ancestor가 있으면 final artifact를 완료로 주장하지 않고 control을 반환한다. root까지 경로가 없으면 phase 진행 불가만 report의 `Summary`, `Open Items`, `concerns` narrative에 `blocked`로 기록한다. 이 값은 child lifecycle state나 report termination enum이 아니다. `phase_control_disposition` 같은 report field도 추가하지 않는다. 이후 capability가 복구되면 same identity continuation을 사용하며, environment status 확인 자체가 새로 unavailable/error가 된 경우에만 `environment_state_unknown`을 생산한다.

## Research catalog confidence producer

열거형·카탈로그 research는 개별 marker와 aggregate confidence를 별도 namespace로 다룬다.

- 이름 붙은 모든 axis와 모든 item은 각각 정확히 하나의 `확인됨 | 추정 | 미확인` marker를 가진다. axis marker 상속이나 aggregate 값 대체는 허용하지 않는다.
- axis set 전체에는 정확히 하나의 `source_confidence: high | mixed | low` aggregate를 둔다.
- 모든 marker가 `확인됨`이면 `high`, `미확인`이 strict majority이면 `low`, 그 밖의 모든 조합은 `mixed`다. 전부 `추정`, 확인·추정 혼합, non-majority 미확인 포함도 `mixed`다.
- 여러 axis set을 가진 artifact의 전체 aggregate는 모든 set의 marker multiset을 합쳐 같은 mapping으로 계산한다.

research worker와 advisor는 반환 전 marker coverage와 aggregate derivation을 각각 self-check한다. 첫 검사는 이름 붙은 axis/item identity 집합과 marker-bearing identity 집합이 같고 identity마다 marker가 하나인지 확인한다. 둘째 검사는 실제 marker multiset으로 aggregate를 다시 계산해 worker/axis-set 및 artifact의 emitted `source_confidence`와 비교한다. advisor는 누락 marker를 추정해 채우거나 불일치 결과를 권위 전제로 승격하지 않는다.

## Abnormal lifecycle reason producer

신규 producer의 `termination: failed | interrupted | late_completion` row는 최초 abnormal serialization부터 non-null `lifecycle_fallback_reason`에 termination cause의 concrete `source_ref`, 현재 recovery disposition, non-empty rationale를 함께 기록한다. canonical string 안의 disposition은 다음 다섯 값으로 닫힌다.

| disposition | 의미 |
|---|---|
| `awaiting_user_decision` | abnormal terminal은 기록됐지만 별도 사용자 recovery 결정은 아직 없음 |
| `approved_clean_retry` | 사용자가 clean retry를 선택했고 race·authority·cap 계약에 따라 준비 또는 수행 중 |
| `phase_fallback` | 허용된 구체적 Tier B/skip/direct fallback이 선택됨 |
| `blocked` | capability, authority isolation, 필수 근거 또는 사용자 선택 때문에 recovery 진행 불가 |
| `late_completion_quarantined` | 선행 authority 철회 뒤 old completion을 quarantine |

중간 `failed`/`interrupted` invocation도 retry cap 소진을 기다리지 않는다. 사용자 결정 전에는 `awaiting_user_decision`, 승인 뒤에는 `approved_clean_retry`처럼 현재 상태를 기록하고, phase report 최종화 전에 명시적 결정이 달라지면 같은 row의 disposition을 갱신한다. 결정 순서와 provenance는 phase-local ledger에 보존한다. `late_completion`은 항상 `late_completion_quarantined`이고 선행 authority reference와 no-auto-merge 계약을 유지한다.

이 canonical form은 기존 string field의 신규 producer 규약이다. report `schema_version: 2`, optional lifecycle field 네 개, 기존 free-text reader compatibility를 바꾸지 않는다. `completed`는 reason null/생략, nonterminal은 `termination` 생략과 reason null/생략을 유지하며 lifecycle reason은 `model_choice.fallback_reason`과 별개다.

## Routing phase와 invocation authority

### Phase namespace

research 산출물과 §8 routing payload는 서로 다른 `phase` namespace를 쓴다.

| 위치 | 값 | 의미 |
|---|---|---|
| `research/index.md` frontmatter | `phase: research` | artifact/pipeline 산출 종류 |
| `Invocations[].model_choice.phase` | `phase: analyze` | protocol §5.8의 모델 routing enum |

research-advisor와 research worker가 사실을 조사·분석하므로 routing 값은 기존 닫힌 enum의 `analyze`다. artifact 값 `research`를 routing enum에 추가하거나 두 값을 같게 만들지 않는다. 이는 기존 report field의 값 보정이며 schema migration이 아니다.

### Host-neutral authority 종류

Lifecycle 상태의 environment 권위와 별개로 ATP는 invocation이 낳는 효과를 받아들일 권한을 관리한다.

| authority kind | 적용 대상 | 명시적 철회·격리 효과 | 정본 |
|---|---|---|---|
| `result_acceptance` (`result acceptance authority`) | read-only invocation | old identity의 future result를 취합·성공 판정 입력에서 제외 | phase-local lifecycle ledger |
| `write_ownership` | write-capable invocation | 선언된 scope의 변경 권한을 회수하고 old/new 동시 owner를 금지 | implementation ownership map + phase-local lifecycle ledger |

`result acceptance authority`의 ATP-local 철회는 host process termination이나 environment terminal 상태를 뜻하지 않는다. termination control이 있으면 먼저 사용해 environment event를 기록하지만, read-only 성질이 확인된 호출은 host termination control이 없어도 future result acceptance만 격리할 수 있다. 이 방식은 write isolation을 대체하지 않는다. write-capable invocation은 termination/write isolation과 partial write 분류가 확인되지 않으면 같은 scope를 handoff하거나 retry하지 않는다.

### 승인, completion race, 철회 순서

1. environment `failed`/`interrupted` 또는 명시적 blocker가 recovery 검토를 연다.
2. 사용자가 clean retry를 명시적으로 승인한다. 이 승인 전 authority mutation은 0건이다.
3. old invocation의 completion race를 같은 identity로 다시 확인한다. 이미 `completed`면 retry를 취소하고 정상 결과 후보로 검토하며 authority를 철회하지 않는다.
4. read-only면 termination 또는 read-only 성질을 확인하고 old report/environment identity의 `result_acceptance_revoked`를 ledger에 기록한다. write-capable이면 termination/write isolation·partial write를 확인하고 ownership을 회수한다.
5. retry cap을 확인한 뒤에만 새 report/environment identity를 생성한다.

`late_completion`은 4번의 선행 authority 기록 뒤 같은 old identity에 대해 environment `completed` 또는 result arrival이 명시된 경우에만 advisor가 기록하는 disposition이다. `authority_ref`는 같은 `report_invocation_id`와 `environment_invocation_id`의 선행 `result_acceptance_revoked` 또는 ownership 회수 anchor를 가리킨다. 철회 전 completion, 선행 record 부재, identity 불일치에서는 신규 producer가 `late_completion`을 만들지 않는다.

후속 처리도 authority와 disk mutation으로 분리한다.

- read-only `result_acceptance` late result: quarantine-only. 자동 merge·취합·성공 판정, ownership row, pause는 모두 0건이다.
- `write_ownership` 회수 뒤 late disk write가 없는 old result: quarantine-only. 새 owner와 ownership state를 바꾸지 않는다.
- 회수된 write scope의 late disk write: 겹치는 scope와 dependency transitive closure만 persisted `paused`로 전환해 중재한다. 독립 scope는 `active`를 유지한다.

따라서 write pause는 `late_completion` 자체가 아니라 late disk write에서만 열린다. `result_acceptance_revoked`, `authority_kind`, `authority_ref`는 phase-local ledger에만 저장한다. report는 계속 `schema_version: 2`이며 lifecycle optional field는 `attempt`, `termination`, `retry_of`, `lifecycle_fallback_reason` 네 개뿐이다.

## 폐기할 관측 정책

다음 관측 정책은 구현하지 않았으며 ADR-0020 적용과 함께 active lifecycle 규약에서 제거했다.

- `evidence_epoch`를 lifecycle decision engine으로 사용
- `start_silence_wait_limit`
- `unchanged_status_check_limit`
- `missed_heartbeat_limit`
- 60초 wait 2회 같은 fallback seed
- heartbeat deadline을 이용한 stall 판정
- `suspected_silent_stall`, `suspected_progress_stall` 자동 진입
- `progress_unobservable`을 retry/fallback의 recovery trigger로 사용
- `.atp/lifecycle.json`에 관측 횟수·시간 budget 저장
- `.atp/work-session/<sid>/artifacts/lifecycle-observation.json`에 추론 counter 저장
- timeout 수에 따라 사용자 결정 상태로 수렴하는 동적 테스트

`evidence_epoch`가 필요하다면 telemetry deduplication이나 UI event 정리에만 제한할 수 있다. lifecycle state와 action 권한에는 영향을 주지 않아야 한다.

## ADR-0017과의 관계

[ADR-0017](../adr/ADR-0017-subagent-lifecycle-recovery.md)은 append-only 규칙에 따라 결정 본문을 바꾸지 않았다. [ADR-0020](../adr/ADR-0020-environment-authoritative-subagent-lifecycle.md)이 다음 범위만 부분 supersede하고 나머지 recovery safety 결정을 계승한다.

### ADR-0020이 supersede한 부분

- 결정 1의 `suspected_silent_stall` 자동 감지 흐름과 first observable activity 기반 판정
- 결정 2의 stall 후보 감지 자동화 부분
- 결정 4의 first-activity 대기, unchanged 상태 확인 budget 및 budget 소진 기반 수렴

### 그대로 보존한 부분

- mutation 전 사용자 보고·선택·승인
- clean retry는 반드시 새 invocation identity 사용
- retry 직전 completion race 재확인
- 기존 invocation termination/isolation 확인 후 retry
- write ownership 회수와 partial write 검사
- 동일 write scope old/new invocation 동시 실행 금지
- late completion 격리와 ownership 충돌 중재
- mandatory verification non-skip
- report schema v2의 additive lifecycle 계보 필드

ADR-0020은 ADR-0017 전체를 폐기하지 않는다. 위 감지/관측 부분만 supersede하며 승인, 독립 retry identity, completion race, termination/isolation, ownership, late completion, verification non-skip과 schema v2 additive 필드를 유지한다.

## Host adapter 계약

각 host adapter는 다음 계약을 충족해야 한다.

1. environment-native lifecycle 상태와 terminal event의 출처를 문서화한다.
2. ATP 개념 상태로의 매핑은 명시적 environment 신호에만 근거한다.
3. 지원하지 않는 상태는 추정하지 않고 `environment_state_unknown`으로 둔다.
4. progress 전달 capability와 lifecycle status capability를 분리한다.
5. Wait/wakeup 필수 capability를 각각 `supported|unsupported|unknown`으로 판정하고 formal all-required gate 결과와 `host_managed_subagent_orchestration`, `manual_wait_polling_supported`를 별도 기록한다.
6. Formal mode에서는 timeout-free subscription만 사용한다. Managed mode는 적용 가능한 host orchestration skill의 all-results barrier를 사용하고 generic polling을 추가하지 않는다.
7. Environment deadline/watchdog가 있으면 설정·취소·terminal 의미를 host appendix에 기록하되 keepalive/watchdog를 root wake나 lifecycle transition으로 노출하지 않는다.
8. Execution mode는 첫 child spawn 전에 판정한다. Formal/managed mode가 모두 없을 때만 child identity·authority·ownership을 만들지 않으며, managed runtime gap은 기존 값을 보존한다.

Codex appendix는 collaboration runtime이 실제 보장하는 상태와 control만 매핑한다. 특정 버전에서 제공하지 않거나 공개 계약이 보장하지 않는 event는 제공되는 것처럼 가정하지 않는다.

### Current Codex capability 판정

| capability | 판정 | 의미 |
|---|---|---|
| product-managed spawn, follow-up routing, all-results wait | supported | 공식 app/CLI/IDE 계약과 release maintainer CLI smoke로 team execution 판정 |
| ATP manual wait/list polling | unsupported | correctness primitive로 사용하지 않음 |
| timeout-free suspend, internal rewait, targeted wait-any/all | unsupported | formal subscription 불가 |
| await cancellation handle, compact delta, stable event ID, native dedup | unsupported | identity·payload 계약 불충족 |
| approval subscription, failure/interruption detail, coalescing | unknown | 공개 API가 structured guarantee를 제공하지 않음 |
| scheduler/watchdog registration | unsupported | event-only resume와 health/cancel 계약 없음 |

따라서 tested Codex CLI profile은 `formal_adapter_enabled: false`, `manual_wait_polling_supported: false`, `host_managed_subagent_orchestration: unsupported`, `team_execution_enabled: false`다. ATP는 첫 collaboration action 전에 Codex orchestration skill을 전문 로드하고 unsupported이면 explicit blocked/user-decision 경로를 사용한다. App/IDE는 `unknown`이다. 적용 surface/version과 공식·경험적 근거는 Codex appendix와 release evidence manifest에 한정한다.

## 구현 파일 영향 맵

| 경로 | 반영 상태 |
|---|---|
| `docs/adr/ADR-0020-environment-authoritative-subagent-lifecycle.md`, `docs/adr/index.md` | ADR-0017의 감지/관측 부분만 부분 supersede하고 새 권위 경계를 기록 |
| `docs/adr/ADR-0021-environment-owned-wait-wakeup-scheduling.md`, `docs/adr/index.md` | timeout-free environment subscription만 formal scheduling으로 인정하고 strict capability-gap 수렴을 결정 |
| `docs/adr/ADR-0022-pre-spawn-wait-wakeup-capability-gate.md`, `docs/adr/index.md` | current Codex capability 판정을 첫 child spawn 전 preflight로 이동한 이력을 기록. zero-child/blocked 수렴은 ADR-0023이 부분 supersede |
| `docs/adr/ADR-0023-host-native-cooperative-execution.md`, `docs/adr/index.md` | formal scheduling과 team execution을 분리하고 ADR-0021/0022의 zero-child 결정을 부분 supersede |
| `docs/adr/ADR-0024-host-managed-subagent-orchestration.md`, `docs/adr/index.md` | ADR-0023의 bounded-wait correctness를 supersede하고 managed all-results barrier를 결정 |
| `plugins/atp/docs/development/agent-team-protocol.md` §2.5 | environment-authoritative lifecycle 위에 `await_invocations`, no-timeout/no-polling gate와 phase-local ledger를 정의 |
| `plugins/atp/docs/development/platform-adapters.md` | formal capability와 host-managed profile을 별도 판정하고 네 execution mode를 협상 |
| `plugins/atp/docs/development/codex-lifecycle-routing.md` | Codex lifecycle mapping, formal adapter false와 release-verified managed team profile을 기록 |
| `plugins/atp/skills/codex-team/SKILL.md` | 첫 collaboration action 전 전문 로드와 no-polling all-results barrier를 실행화 |
| `plugins/atp/skills/task/SKILL.md` | terminal event 기반 취합·복구와 top-level scheduling capability gate를 실행화 |
| `plugins/atp/agents/research-advisor.md` | 기존 lifecycle/result acceptance 계약과 nested read-only worker scheduling gate를 연결 |
| `plugins/atp/agents/parallel-explorer.md` | 모든 axis/item marker와 결정론적 aggregate 및 두 self-check를 반환 계약으로 연결 |
| `plugins/atp/agents/implementation-advisor.md` | 기존 lifecycle/write ownership 계약과 nested write-capable worker scheduling gate를 연결 |
| `tests/lifecycle-contract/fixtures/lifecycle-cases.json` | timeout 비전이, progress 비권위, explicit terminal event, approval capability 직교성, confidence derivation, abnormal recovery disposition과 authority isolation case를 반영 |
| `tests/lifecycle-contract/fixtures/report-v2-environment.json` | 신규 producer의 명시적 environment terminal fixture를 추가 |
| `tests/lifecycle-contract/fixtures/wait-wakeup-cases.json` | logical subscription, host-managed mode, Tier B, non-Codex topology 불변을 추가 |
| `tests/lifecycle-contract/validate.py` | 기존 lifecycle/authority/report-v2 검증과 scheduling closed-set, dedup/coalescing, zero-auto-action gate를 함께 검사 |
| `tests/runtime-behavior/validate_codex_session.py` | 실제 Codex JSONL의 skill-first spawn, all-results terminal barrier, manual wait/list 0과 completion ordering을 검사 |
| `docs/usage/faq.md`, `docs/usage/faq.en.md` | environment 권위와 보존 safety 의미를 동등하게 설명 |
| `docs/changes/2026-08-19-codex-managed-subagent-orchestration.md` | managed orchestration 2.15.0 변경을 기록 |
| manifest/version/release metadata | base 2.15.0 ×4, add-on 2.3.0 ×2, `.agents` versionless 유지 |

## 테스트 설계와 acceptance criteria

### Wait/wakeup scheduling fixture

| case | 입력 | 기대 |
|---|---|---|
| unchanged running/internal keepalive N회 | 관심 event 없음 | lifecycle transition, root resume, semantic action, retry/list 모두 0 |
| completed event 1회 | stable event ID 1개 | compact delta와 root wake 각각 1 |
| 인접 completion 여러 개 | resume dispatch 전 queue | coalesced batch와 root wake 각각 1 |
| `approval_required` | barrier 진행 중 | 즉시 relay, child state/authority/ownership 보존, recovery 0 |
| user steering | subscription suspend 중 | host가 control 즉시 반환; ATP timer 보상 0 |
| duplicate event | 같은 event ID 두 번 | batch/delta/result acceptance 각각 1 |
| explicit failed/interrupted | 권위 terminal event | 기존 사용자 승인형 recovery만 열림 |
| completion race/late completion | old/new identity와 authority anchor | 철회 전 completion은 정상 후보, 철회 뒤 old result만 quarantine |
| formal capability unsupported/unknown + managed orchestration supported | formal gate 실패, managed 가능 | `host_managed_subagent_orchestration`, spawn/result collection 유지, manual wait/list 0 |
| formal/managed mode 모두 없음, general task | safe orchestration 없음 | `tier_b_sequential` |
| formal/managed mode 모두 없음, explicit subagent request | 실제 독립 child가 필수 | `blocked_explicit_independence`, 지원 host/Tier B 명시 전환/취소 |
| non-Codex recursion 제한 | scheduling과 독립인 topology 제약 | 기존 Tier A-flat 유지 |
| report reader compatibility | legacy/silent-stall/environment v2 | schema v2와 optional lifecycle field 네 개 유지 |

정식 event vocabulary에는 root-visible timeout event가 없다. Fixture와 validator는 logical subscription의 correctness와 current-host managed 실행을 함께 확인하며, product-managed workflow를 formal subscription event schema로 오인하지 않는다.

### 동적 event sequence

| case | 입력 | 기대 |
|---|---|---|
| `timeouts_do_not_change_running` | `running` 뒤 timeout N회 | 계속 `running`, retry/fallback 0 |
| `no_progress_then_completed` | progress 없이 timeout 반복 후 `completed` | 정상 result 검증·취합 |
| `progress_does_not_grant_liveness` | progress 여러 번 뒤 environment `failed` | `failed`를 권위 terminal로 처리 |
| `same_snapshot_is_no_transition` | 동일 `running` snapshot 반복 | 전이·counter·mutation 0 |
| `explicit_failed_opens_recovery` | environment `failed` | 사용자 보고와 recovery 선택지로 진입 |
| `approval_is_propagated` | `approval_required` | 자동 retry 없이 사용자 승인 흐름 연결 |
| `approval_relay_unavailable_preserves_state` | 명시적 `approval_required`, relay/control unavailable | child는 nonterminal `approval_required`, phase narrative만 blocked, mutation 0 |
| `status_unavailable_is_unknown` | status API unavailable/error | `environment_state_unknown`; approval/failure 합성 0 |
| `interrupted_checks_ownership` | write-capable invocation `interrupted` | partial write·ownership 확인 전 retry 0 |
| `unknown_is_not_failure` | status capability 없음 | `environment_state_unknown`, failure/retry 0 |
| `read_only_completion_before_acceptance_revocation` | 승인 뒤 race 확인에서 old `completed` | retry·authority 철회·`late_completion` 0, 정상 후보 검토 |
| `read_only_late_completion_after_acceptance_revocation` | old identity의 `result_acceptance_revoked` 뒤 old `completed` | 같은 identity/ref 확인, quarantine-only, merge·success·pause 0 |
| `write_late_completion_without_disk_write` | ownership 회수 뒤 old completion, disk write 0 | quarantine-only, pause·ownership mutation 0 |
| `write_late_disk_write_pauses_dependency_closure` | ownership 회수 뒤 old completion과 late disk diff | overlap + dependency closure만 persisted `paused`, 독립 scope `active` |
| `late_completion_without_prior_authority_revocation_is_invalid` | 선행 철회가 없거나 identity/ref 불일치 | `late_completion` producer 거부 |
| `verification_is_not_skipped` | verification invocation explicit failure | Tier B 검증 또는 blocked |

### Catalog confidence와 recovery disposition

| case | 입력 | 기대 |
|---|---|---|
| `all_confirmed_is_high` | 모든 axis/item marker `확인됨` | aggregate `high` |
| `all_estimated_is_mixed` | 모든 marker `추정` | aggregate `mixed` |
| `non_majority_unverified_is_mixed` | 확인/추정과 non-majority 미확인 혼합 | aggregate `mixed` |
| `majority_unverified_is_low` | 미확인이 strict majority | aggregate `low` |
| `missing_or_duplicate_marker_is_invalid` | axis/item marker 누락 또는 중복 | producer/validator 거부 |
| `failed_awaiting_user` | `failed`, retry exhaustion false, 결정 전 | non-null reason, `awaiting_user_decision` |
| `interrupted_approved_retry` | `interrupted`, retry exhaustion false, 사용자 retry 승인 | non-null reason, `approved_clean_retry` |
| `late_completion_reason` | 선행 authority 철회 뒤 old completion | `late_completion_quarantined`, authority ref, auto-success 0 |

### 정적 invariant

- formal wait/wakeup은 timeout-free environment subscription 하나뿐이며 timed/long/repeated wait fallback이 없다.
- required scheduling capability 하나라도 `unsupported|unknown`이면 unavailable event가 정확히 1회이고 automatic wait/list/retry/interrupt/fallback은 모두 0이다.
- unchanged running과 internal keepalive는 root model resume와 semantic action을 만들지 않는다.
- wake payload는 changed invocation delta를 우선하고 stable event ID로 dedup하며 인접 completion을 한 batch로 coalesce한다.
- steering과 await cancellation responsiveness는 host 소유이며 ATP가 timeout이나 polling으로 보상하지 않는다.
- lifecycle decision 코드·문서에 timeout 횟수, first-activity deadline, missed heartbeat 기반 stall 전이가 없다.
- progress contract는 UX/result 설명용이며 lifecycle 권한을 만들지 않는다고 명시한다.
- environment terminal/approval/blocker 이벤트만 recovery 또는 사용자 결정 흐름을 연다.
- observed `approval_required`는 relay/control unavailable이어도 보존하며 phase narrative blocked와 invocation state를 분리한다.
- `environment_state_unknown`은 environment status unavailable/error/semantic unknown에서만 생산한다.
- 공통 규약에는 host 도구명과 고정 시간값이 없다.
- host appendix는 native state 출처와 ATP 상태 매핑을 명시한다.
- 사용자 승인 전 interrupt, retry spawn, phase fallback은 0건이다.
- clean retry identity, termination/isolation, ownership, late completion, verification non-skip 회귀 fixture를 보존한다.
- 사용자 승인과 completion race 재확인 전 result acceptance authority와 write ownership mutation은 0건이다.
- 모든 신규 `late_completion`은 같은 old identity의 선행 authority 철회·격리를 참조한다.
- read-only/no-disk late result는 quarantine-only이며 write pause는 late disk write에서만 열린다.
- report v2 lifecycle optional field는 `attempt`, `termination`, `retry_of`, `lifecycle_fallback_reason` 네 개로 유지한다.
- 모든 이름 붙은 axis/item은 정확히 하나의 marker를 가지며 aggregate는 전체 marker multiset에서 결정론적으로 재계산된다.
- marker coverage와 aggregate derivation을 worker와 advisor가 모두 self-check한다.
- abnormal 신규 producer reason은 concrete cause, 다섯 disposition 중 현재 값, non-empty rationale를 가지며 retry exhaustion을 기다리지 않는다.
- 한국어·영어 FAQ 의미가 동등하다.

### 완료 조건

1. timeout N회가 `running`을 다른 상태로 바꾸지 않는다.
2. progress가 전혀 없는 정상 completion을 성공 후보로 취합한다.
3. explicit `failed`만 failure recovery를 연다.
4. environment state unknown을 silent stall로 재분류하지 않는다.
5. 환경 상태와 ATP 정규화 상태의 매핑이 host별로 추적 가능하다.
6. ADR-0017의 recovery safety invariant가 모두 통과한다.
7. routing payload의 `model_choice.phase: analyze`와 research artifact의 `phase: research`가 각 namespace에서 검증된다.
8. read-only/write authority 선행조건과 quarantine/pause 분기가 deterministic fixture로 검증된다.
9. approval state/capability 직교성, confidence full coverage/aggregate mapping, abnormal current disposition이 deterministic fixture로 검증된다.
10. `python3 tests/lifecycle-contract/validate.py`가 event-authoritative fixture와 기존 안전 fixture를 모두 통과한다.
11. Scheduling fixture가 unchanged/keepalive 무재개, single/coalesced wake, approval/steering, duplicate dedup, failure recovery, race/late completion, capability gap 수렴과 report v2 호환을 모두 통과한다.
12. Current Codex CLI는 formal adapter/manual polling/host-managed full contract unsupported를 기록하고, 공식 제품 설명과 CLI empirical evidence를 분리한다.
13. Maintainer smoke 3종이 모두 requested/spawn/terminal/collected 일치, manual wait/list/정상 interrupt 0과 last-terminal 이후 completion을 만족할 때만 profile을 supported로 승격한다.
14. Non-Codex formal subscription과 Tier A-flat fixture가 기존 mode/topology를 유지한다.

## 구현·검증 진행 상태

1. [x] ADR-0020에서 ADR-0017의 부분 supersede 범위와 보존 불변식을 확정했다.
2. [x] lifecycle fixture를 environment event 중심으로 바꾸고 구 validator의 `KeyError: 'observable_activity'`, exit 1을 fixture-first RED로 기록했다.
3. [x] 공통 protocol, platform adapter, Codex appendix, task skill과 advisor 실행 경로를 environment-authoritative 계약으로 변경했다.
4. [x] validator와 schema v2 environment fixture를 새 계약에 맞게 변경했다.
5. [x] approval state/capability 직교성, catalog confidence derivation, abnormal current disposition을 source·fixture·validator에 반영했다.
6. [x] FAQ 한·영, ADR, architecture, changes, release checklist와 category index를 동기화했다.
7. [x] `python3 tests/lifecycle-contract/validate.py`의 최종 GREEN을 확인했다.
8. [x] 별도 read-only subagent direct probe로 새 invocation identity, environment `running`, 최종 `completed`와 결과 취합을 확인했다. wait timeout은 발생하지 않았으며 이를 실패로 보지 않았다.
9. [x] release checklist와 manifest/version metadata를 완료하고 링크·§N·버전 invariant를 검증했다.
10. [x] timeout-free `await_invocations` formal gate와 host-managed mode를 runtime/skill/advisor에 구현했다.
11. [x] scheduling fixture와 validator, current Codex capability matrix, report-v2 분리 ledger를 구현했다.
12. [x] base manifest 4곳을 2.13.0으로 동기화했다.
13. [x] verification-advisor가 전체 lifecycle+scheduling validator와 release checklist §10을 독립 실행해 PASS했다.
14. [x] 신규 change 문서와 이 문서의 verification 상태를 실제 결과에 맞게 갱신했다.
15. [x] Source-spec dry-run이 C1~C4를 검출했고, requested/effective mode·research write allowlist·scheduling return fields·preallocated report identity 보정 뒤 재실행 PASS했다.
16. [x] Execution mode 협상을 first advisor spawn 전에 두고 general 자동 Tier B와 explicit independence blocker를 분리했다.
17. [x] Historical 결함과 host-managed Codex JSONL을 검사하는 runtime behavioral validator를 추가했다.
18. [x] Checked-in managed fixture 3종으로 skill-first, spawn 1/1/2, manual wait/list/interrupt 0과 all-results barrier를 검증했다.
19. [x] 격리된 Codex CLI maintainer smoke 3종을 실행했고 terminal-only만 통과해 capability를 unsupported로 판정했다. Evidence manifest를 보존한다.

## 완료 체크리스트

- [x] `docs/index.md` → category index → 관련 문서 순서로 docs-first 탐색
- [x] `docs/adr/index.md`에서 ADR-0020 번호 확인
- [x] ADR-0017 결정 1, 2, 4의 부분 supersede와 결정 3, 5, 6 및 안전 불변식 보존 확인
- [x] host runtime이 실제 제공하는 lifecycle 상태/event와 미지원 한계를 appendix에 기록
- [x] fixture-first RED와 implementation diff 반영
- [x] FAQ 한·영 및 구현 문서 동기화
- [x] 직접 lifecycle probe
- [x] lifecycle contract validator 최종 GREEN
- [x] release metadata와 release checklist 최종 검증
- [x] lifecycle correctness와 wait/wakeup token-efficiency 계약 분리
- [x] timeout-free formal contract와 current Codex managed orchestration mapping 문서화
- [x] ATP manual wait/list polling 제거와 no-lifecycle-mutation 수렴 구현
- [x] scheduling fixture와 historical/current/logical comparison 구현
- [x] 2.13.0 독립 validator·정적 release gate 최종 GREEN(L2 skipped: 외부 의존 없음)
- [x] 2.14.0 adaptive execution-mode contract와 runtime validator 구현
- [x] Isolated 2.15.0 managed maintainer smoke 3종 실행 — 1/3 통과, capability unsupported

## 대안과 기각 이유

- **Evidence epoch와 유한 observation budget**: 동일 관측의 무한 반복은 줄이지만 정상 장기 실행을 stall로 오탐한다.
- **필수 heartbeat contract**: host가 progress delivery를 보장하지 않고 agent가 정상 작업 중 메시지를 보내지 않을 수 있어 correctness 신호가 될 수 없다.
- **고정 deadline 뒤 자동 interrupt**: environment의 정상 `running`을 ATP가 덮어쓰며 write-capable task에서 중복 실행 위험을 만든다.
- **동일 snapshot status check 횟수 제한**: UI 소음을 줄일 수는 있으나 lifecycle 판정 근거가 되지 않는다. UI throttling이 필요하면 별도 UX 정책으로 다룬다.
- **가장 긴 단일 timed wait를 correctness primitive로 사용**: nonterminal 반환 뒤 모델이 다시 기다려야 하므로 formal/managed 경로 모두에서 기각했다.
- **상태 list polling fallback**: 관심 event 없이 model을 깨우고 lifecycle 추론 압력을 만들므로 native mode에서도 기각했다.
- **현행 유지**: timeout 기반 관측 반복과 정상 실행 오탐 가능성을 그대로 남긴다.

## Rollback

구현 후 host event mapping에 결함이 발견되면 추론형 정책으로 되돌리지 않는다. 해당 host adapter를 `environment_state_unknown`으로 낮추고 mutation을 중단한 뒤 mapping을 수정한다. 이미 발행한 ADR을 되돌려야 하면 append-only 규칙에 따라 새 superseding ADR을 발행한다.

## 관련 문서

- [ADR-0020: environment-authoritative subagent lifecycle](../adr/ADR-0020-environment-authoritative-subagent-lifecycle.md)
- [ADR-0021: environment-owned wait/wakeup scheduling](../adr/ADR-0021-environment-owned-wait-wakeup-scheduling.md)
- [ADR-0022: pre-spawn wait/wakeup capability gate](../adr/ADR-0022-pre-spawn-wait-wakeup-capability-gate.md)
- [ADR-0023: host-native cooperative execution](../adr/ADR-0023-host-native-cooperative-execution.md)
- [ADR-0024: host-managed subagent orchestration](../adr/ADR-0024-host-managed-subagent-orchestration.md)
- [환경 권위 lifecycle 변경 기록](../changes/2026-08-12-environment-authoritative-subagent-lifecycle.md)
- [환경 주도 subagent wakeup 변경 기록](../changes/2026-08-13-environment-driven-subagent-wakeup.md)
- [2.15.0 Codex managed orchestration 변경 기록](../changes/2026-08-19-codex-managed-subagent-orchestration.md)
- [ADR-0017: subagent lifecycle recovery](../adr/ADR-0017-subagent-lifecycle-recovery.md)
- [subagent lifecycle recovery 변경 기록](../changes/2026-07-20-subagent-lifecycle-recovery.md)
- [Codex lifecycle routing appendix](../../plugins/atp/docs/development/codex-lifecycle-routing.md)
- [ATP 공통 lifecycle 규약](../../plugins/atp/docs/development/agent-team-protocol.md)
- [platform adapters](../../plugins/atp/docs/development/platform-adapters.md)
