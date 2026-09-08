---
kind: development
title: Capability Tier 와 호스트 자가판정
description: ATP 가 호스트 CLI 의 subagent capability 를 자가판정해 위임 토폴로지(Tier A / A-flat / B)를 결정하는 규칙. 호스트 고유 문법·모델 슬러그는 호스트 위에서 실행 중인 에이전트가 자율 적용한다.
owner: template-maintainer
stability: draft
last_reviewed: 2026-08-18
---

# Capability Tier 와 호스트 자가판정

## 0. 원리 — 워크플로우 강제 ≠ 도구 강제

ATP 는 **워크플로우**(phase 척추 · 파괴적 조작 게이트 · report 스키마 · 검증규율)를 강제하는 프로토콜이지, 특정 호스트 CLI 의 도구 사용을 강제하는 프로토콜이 아니다. 따라서 본 문서는 호스트 플랫폼을 이름으로 열거하지 않는다.

- 에이전트는 자기 호스트 CLI 위에서 실행 중이므로 호스트의 **호출 문법 · 지침파일 규약 · 모델 라인업 · env/경로 변수 · 배포 단위를 스스로 안다.** 이들은 에이전트가 자율 적용한다.
- 프로토콜이 판정해야 하는 것은 단 하나 — **호스트의 subagent capability** 다. 이것이 위임 토폴로지(Tier)를 결정한다 (§3 자가판정).
- 어떤 호스트에서든 게이트 · report 스키마(프로토콜 §8) · 검증규율은 동일하게 적용된다 — 이들은 호출 토폴로지와 독립이다.

> 배경: ATP 는 Claude Code 에서 출발한 프로토콜이며, 한때 특정 3사 CLI 의 capability 를 본 문서에 열거했다. 그 실측 데이터는 ADR-0009 부록에 동결 보존되어 있다 (§8).

## 1. 논리 추상 (호스트 중립)

### 1.1 공통 명령 식별자

ATP 내부의 공통 명령 식별자는 `task`, `init` 이다. 스킬 파일명·프로토콜 설명·내부 설계 문서는 이 중립 이름을 사용한다. 실제 사용자 입력 문법(접두 토큰·namespace 표기)은 호스트 플랫폼이 결정하며, 에이전트는 자신이 이번 세션에서 호출된 토큰을 그대로 안내에 사용한다.

### 1.2 공통 산출물 경로

> **현재 권위 경로**: `.atp/work-session/<sid>/`
>
> 새 세션·문서·구현 모두 이 경로를 기본값으로 사용한다. (F-3PLAT-3 single-read 전환 완료)

> **legacy**: `.claude/work-session/` 은 이전 버전의 산출물 경로다. `init` 의 `atp:migrate` 블록으로 자동 이관된다. 신규 프로젝트는 이 경로를 사용하지 않는다.

### 1.3 논리 환경 변수

공통 문서에서는 논리 변수명을 사용한다. 호스트 실변수는 에이전트가 자기 호스트의 변수로 해석한다.

| 논리 변수 | 의미 | 호스트 해석 |
| --- | --- | --- |
| `${ATP_PROJECT_DIR}` | 소비 프로젝트 루트 | 호스트의 프로젝트 루트 변수/경로 자율 적용 |
| `${ATP_PLUGIN_ROOT}` | 설치된 ATP 플러그인 루트 | 호스트의 플러그인/확장 루트 변수 자율 적용 |

## 2. Capability Tier 정의 (capability 기반 — 호스트 독립)

- **Tier A** = 서브에이전트 spawn 가능 + spawn 된 subagent 의 재-spawn 가능 → ATP 3-tier 팀(orchestrator + advisor + worker) 완전 동작. 2단 위임 체인(orchestrator→advisor→worker) 지원.
- **Tier A-flat** = spawn 은 되나 subagent→subagent 재귀 금지인 호스트용 변형. orchestrator 가 advisor 와 worker 를 **모두 직접** 호출하는 평탄 구조(1단 fan-out). 게이트·report 스키마(§8)·검증규율 전량 유지.
- **Tier B** = 단일 agent (spawn 불가/미확인) → orchestrator 가 protocol phase 를 순차 self-checklist 로 수행. 병렬 advisor·worker 만 격하, 나머지 규율 유지. **spawn 자가판정 불가/실측 실패 시 안전 폴백.**

> **spawn = invocation 기록 의무**: spawn 된 subagent 는 capability tier 와 무관하게 report 스키마(프로토콜 §8) invocation 으로 기록한다 — layer + parent_invocation_id 필수. 한 호스트 CLI 의 운영 전사(20260610-154723)에서 subagent 2개 spawn 이 report Invocations 에 누락된 사례가 본 의무 명문화의 계기다(§8 위반 — 원문은 ADR-0009 부록 F).

## 3. Capability 자가판정 절차

orchestrator(메인 에이전트)는 ATP task 진입 시 적용 가능한 host orchestration skill을 먼저 선택해 전체 지침과 배포된 capability profile을 읽는다. 플랫폼 이름이 아니라 **capability 질문**으로 판정한다 — 목록에 없는 호스트도 자연 커버된다. 소비 프로젝트의 매 task에서 임시 child, 시간 기반 probe, 반복 상태 조회나 maintainer validator를 실행해 profile을 다시 만들지 않는다.

```
[진입] orchestrator 가 자기 호스트 capability 를 자가판정
  │
  ├─ Q1. 내 호스트가 subagent 를 spawn 할 수 있는가?
  │     ├─ 모름/불가 ──────────────► Tier B (단일 agent 순차 self-checklist — §5)
  │     └─ 가능 ─┐
  │             │
  │   Q2. spawn 된 subagent 가 다시 subagent 를 spawn 할 수 있는가? (재귀)
  │             ├─ 불가(재귀 금지) ──► Tier A-flat (orchestrator 직접 fan-out — §4)
  │             └─ 가능 ────────────► Tier A (2단 위임: L1→L2→L3)
  │
  ├─ [고지] 비-A tier 면 1줄 고지
  │        ("Tier A-flat 평탄 위임 모드" / "Tier B 격하 모드 — 순차 self-checklist")
  │
  └─ [불변] 어느 tier 든: 파괴적 조작 게이트(프로토콜 §6) · report 스키마(§8) ·
            phase 완료 아티팩트 기준(§13) · forward phase-gate(§2.7) · 집합 전수 AC(§4.3) 유지.
```

판정 근거는 선택한 host orchestration skill의 검증된 profile, 호스트 공식 문서와 정상 API다. 실행 중 임의 추론으로 profile과 result collection 계약을 덮어쓰지 않는다. Applicable skill/profile이 없고 확신할 근거도 없으면 안전 폴백한다 — spawn 여부 불확실 → Tier B, 재귀 여부 불확실 → Tier A-flat.

### 3.1 Invocation lifecycle capability profile

위임 topology 판정과 별도로, subagent를 호출하는 주체는 프로토콜 §2.5를 실행하기 전에 다음 capability를 `supported | unsupported | unknown`으로 자가판정한다. 플랫폼 이름이나 추정이 아니라 environment가 정상 API로 실제 노출하는 의미를 기준으로 한다.

| capability | 판정 질문 | `unsupported` / `unknown` 안전 폴백 |
|---|---|---|
| authoritative non-terminal state | accepted/queued/running을 environment state로 확인 가능한가 | 얻은 상태만 보존하고 미노출 상태는 `environment_state_unknown` |
| authoritative terminal event | completed/failed/interrupted를 서로 구분한 environment event로 받을 수 있는가 | 미지원 terminal 종류를 output·시간·silence로 합성하지 않고 `environment_state_unknown` |
| approval event | `approval_required`를 environment event로 받을 수 있는가 | 승인 필요 여부를 추정하지 않는다. host가 제공하는 별도 승인 흐름만 따른다 |
| approval relay capability | 관측된 `approval_required`를 parent/user에게 relay할 수 있는가 | 미지원이어도 관측된 state는 `approval_required`로 보존; concern·ledger를 반환하고 phase narrative만 blocked |
| approval continuation capability | 사용자 결정 후 같은 environment identity를 continuation할 수 있는가 | interrupt/retry/fallback·authority mutation 0; child `ended_at: null`, termination 생략 |
| native blocker provenance | environment 실행 blocker와 agent output의 업무상 `blocked`를 구분 가능한가 | 두 의미를 합치지 않고 출처 불명 상태를 `environment_state_unknown`으로 유지 |
| output/progress UX | output, explicit progress, tool start/result를 정상 API로 관측 가능한가 | 진행 설명을 생략할 수 있으나 lifecycle 상태에는 영향 없음 |
| termination control | 실행 중 invocation에 host-native 종결 요청을 보낼 수 있는가 | 지원 시 사용자 승인·completion race 뒤 먼저 사용; 반환 event만 terminal로 기록 |
| termination confirmation | 종결 또는 더 이상 write하지 않음을 확인 가능한가 | 동일 write scope handoff 금지; scope 분리, Tier B 직접 수행, user decision 또는 blocked |
| invocation identity | 새 실행과 기존 실행의 identity 차이를 확인 가능한가 | clean retry로 세지 않으며 Tier B 또는 blocked |
| context control | 새 invocation에 최소 권위 payload만 전달 가능한가 | 명시 payload로 권위 계약을 재진술하고 불필요한 이력 의존을 최소화 |
| result acceptance isolation | 확인된 read-only invocation의 old identity가 보낸 future result를 ATP-local하게 격리 가능한가 | 새 read-only retry를 만들지 않고 Tier B, user decision 또는 blocked |
| write isolation/ownership | old/new invocation의 write scope를 분리하고 ownership을 회수 가능한가 | 같은 scope 동시 실행 금지 |

Environment가 `running`을 반환하면 ATP도 `running`을 유지한다. wait timeout, 경과 시간, progress/heartbeat 부재, 동일 snapshot 반복은 wake-up 또는 UX 관측일 뿐 상태 전이·retry·fallback 권한이 아니다. 상태 API 부재·오류도 `environment_state_unknown`이며 terminal failure가 아니다.

Approval event observation과 relay/continuation capability는 별도 축이다. 명시적 `approval_required`를 relay 미지원 때문에 `environment_state_unknown`으로 낮추지 않는다. `environment_state_unknown`은 environment status 자체가 unavailable/error/semantically unknown일 때만 쓴다.

Relay/continuation capability가 복구되어 host가 same environment identity continuation을 제공하면 `attempt`와 retry accounting을 바꾸지 않는다. 이후 status API unavailable/error event가 실제 발생한 경우에만 그 새 관측을 `environment_state_unknown`으로 기록한다.

Host termination control과 ATP-local `result acceptance isolation`은 별도 capability다. 사용자 승인과 completion race 재확인 뒤 host termination을 먼저 시도하되, termination control이 unsupported라도 read-only 성질과 identity를 확인한 invocation은 `result_acceptance_revoked` ledger event로 future result 수용만 격리할 수 있다. 이 격리는 environment `failed`/`interrupted`를 합성하지 않는다. write-capable invocation의 `write_ownership`에는 적용할 수 없으며 termination/write isolation·partial write 분류를 대신하지 않는다.

명시적 failed/interrupted/environment blocker 뒤의 clean retry 횟수에는 유한한 안전 한도를 둘 수 있다. 그러나 관측 시간·poll 횟수는 그 한도를 소비하지 않는다. capability가 unknown이어도 사용자 보고 → 옵션 → 확인 순서를 생략하지 않으며, 승인 전 interrupt/retry/fallback은 0건이다.

### 3.2 Formal wait/wakeup scheduling capability profile

Lifecycle capability와 별도로, subagent를 호출하는 주체는 execution mode preflight와 protocol §2.5의 `await_invocations` 등록 직전에 다음 capability를 각각 `supported | unsupported | unknown`으로 판정한다. 이 profile은 host-neutral하며 모든 required capability가 `supported`인 경우에만 `formal_adapter_enabled: true`, `mode: environment_subscription`이다. 이 판정은 timeout-free scheduling 최적화 mode의 가용성을 결정하며 child spawn 가능성 자체는 §3.3이 별도로 판정한다.

| capability identity | 판정 질문 |
|---|---|
| `timeout_free_suspend` | 관심 event 전에는 root model invocation 없이 persistent await를 유지하는가 |
| `targeted_wait_any` | 지정한 target 집합 중 하나의 관심 event를 기다릴 수 있는가 |
| `targeted_wait_all` | 지정한 target 집합 전부의 terminal 조건을 누적할 수 있는가 |
| `terminal_event_subscription` | `completed | failed | interrupted`를 environment event로 구분해 구독하는가 |
| `approval_event_subscription` | `approval_required`를 structured environment event로 구독하는가 |
| `user_steering_preemption` | suspend 중 user steering이 wait를 선점해 control을 반환하는가 |
| `await_cancellation` | persistent await identity를 별도로 취소할 수 있는가 |
| `compact_changed_invocation_delta` | 전체 snapshot이 아니라 changed invocation delta만 전달하는가 |
| `stable_event_identity` | 재전달을 식별할 stable event ID가 있는가 |
| `environment_deduplication` | 동일 event ID를 한 batch에서만 전달하는가 |
| `completion_coalescing` | resume dispatch 전 인접 관심 event를 한 compact batch로 취합하는가 |
| `internal_keepalive_no_model_wake` | keepalive/watchdog을 environment 내부에서 처리하고 root를 깨우지 않는가 |

**Formal all-required gate**: 위 identity 하나라도 `unsupported | unknown`이면 `formal_adapter_enabled: false`다. ATP는 부분 capability를 조합해 `environment_subscription`이라고 주장하거나 root-visible 시간 신호·반복 상태 조회·polling으로 formal 계약의 빈 capability를 보충하지 않는다. 다만 formal adapter 부재는 곧바로 `spawn_allowed: false`를 뜻하지 않는다. 적용 가능한 host orchestration skill이 product-managed all-results barrier를 `supported`로 보장하면 §3.3의 `host_managed_subagent_orchestration`을 사용할 수 있다.

Formal capability gap은 scheduling 최적화 unavailable이지 lifecycle failure가 아니다. `host_managed_subagent_orchestration`에서는 host가 spawn·routing·all-results collection을 관리하고 ATP는 generic polling을 추가하지 않는다. Managed capability 자체가 runtime에서 unavailable/error로 바뀐 경우에만 마지막 child state·authority·ownership을 보존하고 추가 spawn·automatic recovery를 0건으로 둔 채 phase를 blocked로 반환한다. Formal subscription으로 위장한 timer/polling continuation은 계속 금지한다.

Scheduling 기록은 lifecycle ledger와 분리된 phase-local `wait-wakeup-events.jsonl`에 둔다. Event vocabulary는 정확히 다음 여섯 개의 닫힌 집합이며, host adapter가 다른 event 이름이나 root-visible timeout/keepalive event를 추가하지 않는다.

| scheduling event | 의미 |
|---|---|
| `await_capability_checked` | 필수 capability 12개 각각의 판정, `formal_adapter_enabled`, `host_managed_subagent_orchestration`, `selected_mode`와 profile 근거를 기록한다 |
| `await_registered` | all-required gate 통과 뒤 `targets`, `condition`, 정확한 `wake_on`, `mode: environment_subscription`, capability profile ref를 기록한다 |
| `wake_batch` | 하나의 root resume를 식별하는 batch identity, wake reason, changed-invocation compact delta와 deduplicated event identity를 기록한다 |
| `wait_wakeup_capability_unavailable` | formal adapter와 host-managed orchestration이 모두 unavailable일 때 정확히 1회 기록하고 preserved lifecycle state·authority·ownership, phase disposition, automatic action 0건을 보존한다 |
| `external_continuation_selected` | 사용자가 명시 선택한 event-only continuation identity와 wake/cancellation contract가 모두 있을 때만 기록한다 |
| `measurement` | 정상 API나 로그로 확인한 requested/spawn/nonterminal/terminal/collected/manual-wait/list/interrupt/recovery, token, latency 측정만 기록하며 알 수 없는 값은 `null`로 둔다 |

각 row의 envelope과 event별 closed details, adapter 논리 입출력, 정확한 wake set, compact delta·event ID·coalescing·steering/cancellation 불변식은 protocol §2.5가 정본이다. Scheduling metadata를 report v2 `Invocations[]`에 복사하지 않는다.

### 3.3 Execution mode negotiation

위임 topology(Tier A / A-flat / B)와 scheduling mode는 직교한다. Q1/Q2의 spawn·재귀 판정은 그대로 topology를 정하고, 별도 orchestration 판정이 child 결과의 all-results barrier를 고른다. Host-specific 기능을 사용하기 전에 적용 가능한 host orchestration skill을 선택해 전체 지침을 읽는다. 특정 host 전용 도구명과 event spelling은 공통 규약에 넣지 않고 §7.1의 조건부 appendix와 전용 skill이 해석한다.

`host_managed_subagent_orchestration`은 host와 적용 skill이 다음을 보장하는 capability 값 `supported | unknown | unsupported`다.

별도 축 `manual_wait_polling_supported`는 generic model-visible polling이 correctness primitive인지 나타내며, managed mode에서는 반드시 `false`다. 이 값은 formal adapter capability와 host-managed capability를 합성하지 않는다.

Host skill은 `supported`를 **선언된 scope에 gate**할 수 있다 — 예: 옵트인 add-on hook이 세션 시작 시 넣는 exact marker의 존재. 그 경우 scope 판정은 그 skill이 정한 단일 신호로만 하고, marker 부재는 오류가 아니라 `unsupported`로 취급해 `general_task`는 Tier B로 투명하게 계속한다. Runtime 관측·시간·probe로 scope 안팎을 재추론하지 않는다.

1. 요청된 child를 만들고 environment identity를 report identity에 연결할 수 있다.
2. Host가 follow-up routing, 결과 대기와 terminal delivery를 관리한다.
3. 요청한 모든 child terminal result가 준비된 뒤 parent result collection barrier를 연다.
4. ATP가 generic polling을 추가하지 않아도 user steering 또는 host control을 보존한다.

Execution mode의 닫힌 집합과 선택 우선순위는 다음과 같다.

| selected mode | 조건 | 처리 |
|---|---|---|
| `environment_subscription` | `formal_adapter_enabled: true` | 기존 timeout-free `await_invocations` 계약을 그대로 사용 |
| `host_managed_subagent_orchestration` | formal adapter는 불완전하지만 host profile이 `supported` | host-managed all-results barrier를 사용하고 generic polling을 추가하지 않음 |
| `tier_b_sequential` | 두 orchestration mode가 모두 불가이고 `request_intent: general_task` | 사용자 선택을 기다리지 않고 순차 self-check로 자동 격하하며 1줄 고지 |
| `blocked_explicit_independence` | 두 orchestration mode가 모두 불가이고 `request_intent: explicit_subagent_required` | `지원 host에서 재실행 | 독립성 없는 Tier B로 명시 전환 | 취소`를 제시하고 blocked |

Managed mode에서 실제 nonterminal update가 전달돼도 invocation은 `running`이다. 모든 요청 child terminal result를 수신·검증·취합하기 전 report/session completion과 parent final을 만들지 않는다. 정상 경로 measurement는 requested agent, spawn, nonterminal update, terminal delivery, collected result와 generic wait/list/interrupt/recovery action의 실제 횟수를 기록하고 알 수 없는 telemetry는 `null`로 둔다.

실행 중 managed capability가 unavailable/error로 바뀌면 automatic polling, retry, interrupt, fallback 또는 Tier B 전환으로 보상하지 않는다. Child의 마지막 authoritative state, result acceptance authority와 write ownership을 보존하고 요청 의도에 맞는 blocked/user-decision 경로를 사용한다. Formal capability가 나중에 추가되면 topology 변경 없이 scheduling mode만 `environment_subscription`으로 승격한다.

이 협상은 다른 host의 기존 판정을 바꾸지 않는다. Formal capability 12개를 이미 충족하는 host는 계속 `environment_subscription`을 사용하고, 재귀 spawn이 불가능한 host의 Tier A-flat topology도 그대로 유지된다.

## 4. Tier A-flat 평탄화 규약 (재귀 금지 호스트의 토폴로지 해소)

subagent→subagent 재귀 금지는 ATP 의 2단 위임 체인(L1→L2→L3)에서 L2→L3 간선만 막는다. 이는 capability 부재가 아니라 **토폴로지 제약**이므로 Tier B 격하는 과하다 — 평탄화로 해소한다.

| 항목 | Tier A | Tier A-flat | Tier B (폴백) |
| --- | --- | --- | --- |
| spawn | advisor 가 worker spawn | orchestrator 가 worker 직접 spawn | spawn 없음 |
| 위임 깊이 | 2단 (L1→L2→L3) | 1단 평탄 (L1→L2, L1→L3) | 0단 (단일 agent) |
| worker 병렬 | advisor 내부 병렬 | orchestrator fan-out 병렬 | 순차 self-check |
| advisor 역할 | 계획+spawn+취합 | 계획 반환 → orchestrator 가 spawn → advisor 취합 | orchestrator self-check |
| 게이트 | 유지 | 유지 | 유지 |
| report 스키마(§8) | 유지 | 유지 | 유지 |
| 검증규율 | 유지 | 유지 | 유지 |
| 격하 대상 | 없음 | L2→L3 간선만 평탄화 | 병렬 → 순차 self-check |

**근거**: (1) flat fan-out 은 spawn 능력을 그대로 활용하면서 재귀만 회피한다. (2) report 스키마·게이트는 호출 토폴로지와 독립이므로 평탄화해도 무손실. (3) advisor 가 "spawn 주체"에서 "계획 산출 주체"로 역할만 이동 — 산출물 계약(보고서 스키마 §8) 불변.

## 5. Tier B 실행 규칙 (격하 시 적용)

spawn 미지원/자가판정 불가/실측 실패 호스트에서 **단일 agent 가 ATP 를 순차로 도는** 규율이다.

### 원칙

- **유지(불변)**: 파괴적 조작 게이트(프로토콜 §6), 보고서 스키마(§8), 검증규율(§13 phase 완료 아티팩트 기준), forward phase-gate(§2.7), 집합 전수 체크 AC(§4.3).
- **격하(변형)**: 병렬 advisor → 단일 agent 의 **순차 self-checklist**. worker fan-out → 단계별 self-수행. advisor 간 충돌 조정 → 단일 agent 가 phase 전환 시 직전 산출물 자기검토.
- **금지**: phase 척추(요구 → 조사 → 설계 → 구현 → 검증) 우회. 게이트 생략. report 스키마 누락.

### phase 순차 self-checklist

단일 agent 는 각 phase 진입 시 아래를 자기 점검하고, phase 종료 시 해당 phase 의 report(§8) 산출물을 `.atp/work-session/<sid>/` 에 기록한 뒤 다음 phase 로만 전진한다.

```
[Phase 0 — 요구사항 구체화]
  □ 요청을 FR/NFR 로 분해했는가
  □ 모호점은 AskUserQuestion 으로 닫았는가 (오픈 질문 0)
  □ requirements 산출물 기록 (report §8)

[Phase 1 — 조사 (research-advisor 역할 self-수행)]
  □ docs-first: index.md → 카테고리 index → 구체 문서 순 탐색했는가
  □ 외부 스펙은 source_confidence 마커(verified-seed/cited/TODO:실측)로 분류했는가
  □ (병렬 worker 불가) 조사 항목을 순차 처리하고 누락 없이 취합했는가
  □ research 산출물 기록 (report §8, concerns 포함)

[Phase 2 — 설계 (design-advisor 역할 self-수행)]
  □ 오픈 질문 0 — 미결은 concerns 로 에스컬레이션했는가
  □ 집합 포함 요구에 전수 체크 AC 1줄을 넣었는가 (§4.3)
  □ 시그니처 inflate 점검 (각 인자 사용 목적 인라인)
  □ design 산출물 기록 (report §8)

[Phase 3 — 구현 (implementation-advisor 역할 self-수행)]
  □ 설계도 파일 영향 맵을 따랐는가
  □ (병렬 worker 불가) 파일 단위 순차 수정 + 단계별 self-diff 검토
  □ unused/dead parameter 진단 게이트 통과 (§11.2)
  □ 파괴적 조작은 게이트 2단계 분리 통과 (§6)

[Phase 4 — 검증 (verification-advisor 역할 self-수행)]
  □ design 의 검증 포인트(AC) 전수 점검 — 집합 AC 는 grep -c 수치 일치 확인
  □ phase 완료 아티팩트 기준 충족 (§13)
  □ verification 산출물 기록 (report §8, PASS/FAIL)

[Phase 5 — 문서화 (documentation-advisor 역할 self-수행)]
  □ changes/ADR 등 카테고리 분류 기준 준수
  □ 회고 → 교훈 반영 (docs-first; memory 는 사용자 설정 시 보조) (§12)
```

### Tier B 진입 트리거

- §3 자가판정에서 spawn 불가/불확실 판정 시.
- 배포된 host capability profile이 spawn 또는 orchestration을 `unsupported`로 명시한 경우.
- 또는 사용자가 명시적으로 단일-agent 모드 요청 시.
- 진입 시 orchestrator 는 "Tier B 격하 모드 — 병렬 advisor 미사용, 순차 self-checklist 수행" 을 1줄 고지한다.

## 6. 모델 Tier 매핑

ATP 모델 정책(프로토콜 §5)은 플랫폼 중립 tier(`small`/`medium`/`large`)로 판단하고, **호스트가 자기 모델 라인업으로 해석**한다.

| tier | 의미(등급) | 호스트 해석 |
| --- | --- | --- |
| small | 라인업 경량 등급 | 호스트 라인업의 경량 모델 |
| medium | 라인업 표준 등급 | 호스트 라인업의 표준 모델 |
| large | 라인업 최상위 등급 | 호스트 라인업의 최상위 모델 |

- **자사 확정 매핑** — reference 구현인 Claude Code 의 정본 슬러그 (as-of 2026-06): small=`haiku` / medium=`sonnet` / large=`opus`. ADR-0008 결정 5 가 본 절을 자사 슬러그 매핑 SSoT 로 지정한다. 라인업 변동 시 `as-of` 스탬프를 갱신한다.
- **타 호스트 구체 슬러그 하드코딩 금지** — 모델명 누수의 역방향이므로 금지(ADR-0008 결정 5). 각 호스트의 에이전트가 자기 라인업의 경량/표준/최상위 등급으로 해석한다.
- **per-call override**: 호스트가 제공하는 per-call override 문법(subagent 호출 파라미터, agent 정의 메타데이터 등)을 자율 사용한다. 생략 시 parent 상속.
- **effort 노브** (프로토콜 §5.5): 호스트가 노출하면 사용, 미노출이면 no-op — 동일 model_choice 블록을 모든 호스트가 공통 작성한다.
- **자기 모델 가시성** (프로토콜 §5.6 cap 판정): 자기 실행 모델을 tier 로 해석할 수 없으면 안전 폴백 — override 미지정(parent 상속), `resolved_model: inherit`.

## 7. 호스트 고유 적용 (자율 — 열거하지 않음)

다음은 호스트마다 다르지만 ATP 가 규정하지 않는다. 에이전트가 자기 호스트 규약을 자율 적용한다.

| 항목 | 적용 원칙 |
| --- | --- |
| skill/command 호출 문법 | 호스트가 노출하는 호출 토큰을 그대로 사용. 사용자 안내에는 자신이 이번 세션에서 호출된 토큰을 사용 |
| 지침파일 규약 | 호스트 자신의 지침파일 규약을 따른다 — 감지·생성 절차는 init SKILL §2 위임 |
| env/경로 변수 | 호스트의 프로젝트 루트·플러그인 루트 변수 자율 사용 (§1.3 논리 변수의 호스트 해석) |
| 배포 단위 | 호스트의 플러그인/확장 패키징 규약 자율 적용 |
| 모델 슬러그 | §6 — 중립 tier 를 자기 라인업으로 해석 |

### 7.1 조건부 host appendix

host 전용 모델 route 나 사용량 정책은 공통 §6 tier 매핑을 덮어쓰지 않는다. 해당 host 에서만 appendix 를 읽고, route 사용이 불가능하면 즉시 §6 의 기존 tier 매핑으로 fallback 한다.

- Codex host: [codex-spark-routing.md](./codex-spark-routing.md) — Spark 를 저지연 code-worker route 후보로만 사용하고, 미지원/미확인/실패 시 기존 tier 매핑으로 fallback.
- Codex host lifecycle/orchestration: [codex-lifecycle-routing.md](./codex-lifecycle-routing.md) — §2.5의 environment state·terminal event·종결·독립 invocation을 매핑하고, formal scheduling과 managed all-results capability를 분리한다. lifecycle fallback은 scheduling 및 모델 route와 독립.
- Claude Code host lifecycle/orchestration: [claude-code-lifecycle-routing.md](./claude-code-lifecycle-routing.md) — async `Agent` spawn과 task-notification terminal 전달을 §2.5 계약에 매핑. barrier 는 turn-end await(live children 보유 agent 를 완료 처리하지 않고 모델 호출 0으로 suspend)이며, no-op 틱·transcript 파일 폴링 등 manual liveness polling 을 금지한다. 실행 절차는 `claude-code-team` skill 이 정본.

## 8. 동결 이력 포인터

과거 특정 3사 CLI 에 대해 실측한 capability matrix(6축) · 플랫폼 Tier 판정표 · 토폴로지 해소표 · per-platform 어댑터 표 · 명령/환경변수/명명 대응표 · 실증 마커 목록은 소스 레포 `docs/adr/ADR-0009-bundle-runtime-platform-neutralization.md` **부록 A~F 에 동결 보존**되어 있다.

- 동결 이력이므로 **향후 갱신 의무 없음.** 새 호스트 실측이 생기면 신규 ADR 로 발행한다.
- 번들 런타임은 부록 데이터에 의존하지 않는다 — §3 자가판정만으로 동작한다.
- opencode(4번째 호스트) 실측 → `docs/adr/ADR-0014-opencode-host-adapter-strategy.md` (generator+CLI 어댑터, Tier A-flat, 스모크 PASS 2026-06-24).
- Antigravity IDE(5번째 호스트) 실측 → `docs/adr/ADR-0015-antigravity-host-verification.md` (GEMINI.md 지침파일, `/atp-task` 하이픈 문법, Tier A-flat, task PASS 2026-06-30, Antigravity 2.2.1).

## 검증 체크리스트

- [ ] 본 문서의 활성 규칙에 특정 타 벤더 플랫폼명·모델 슬러그가 열거되어 있지 않은가? (허용 잔존: §0 배경 1줄, §6 자사 정본 슬러그)
- [ ] Tier A / A-flat / B 정의가 capability 조건("spawn 가능한가" / "재귀 가능한가")만으로 기술되어 있는가?
- [ ] 자가판정 절차(§3)에 안전 폴백(불확실 → Tier B / parent 상속)이 포함되어 있는가?
- [ ] lifecycle capability(environment state·terminal/approval event·종결·identity·context·result acceptance isolation·write isolation)가 supported/unsupported/unknown으로 판정되고 `environment_state_unknown` 안전 폴백이 정의되어 있는가?
- [ ] wait/wakeup 필수 capability 12개가 전부 `supported`일 때만 `environment_subscription`이 활성화되는가?
- [ ] formal gap이 있어도 `host_managed_subagent_orchestration: supported`인 host는 managed all-results barrier로 팀 실행을 유지하는가?
- [ ] 두 orchestration mode가 모두 불가할 때 일반 작업은 투명한 `tier_b_sequential`, 실제 독립성 요구는 `blocked_explicit_independence`로 수렴하는가?
- [ ] Host 전용 managed mapping이 formal subscription 또는 다른 host의 Tier A/A-flat/B 판정을 변경하지 않는가?
- [ ] 동결 이력 포인터(§8 → ADR-0009 부록)가 존재하는가?
- [ ] 게이트·report 스키마·검증규율의 tier 독립성("어느 tier 든 유지")이 명시되어 있는가?
