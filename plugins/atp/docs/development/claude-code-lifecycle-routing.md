---
kind: development
title: Claude Code managed subagent orchestration and lifecycle routing appendix
description: ATP의 host-neutral lifecycle과 result barrier를 Claude Code async Agent 툴 + task-notification workflow에 매핑하는 조건부 appendix.
owner: template-maintainer
stability: stable
host_scope: claude-code
last_reviewed: 2026-08-25
---

# Claude Code managed subagent orchestration and lifecycle routing appendix

이 문서는 Claude Code host에서만 읽는 조건부 appendix다. 공통 lifecycle·result integration·report authority는 `agent-team-protocol.md` §2.5, host-neutral capability 판정은 `platform-adapters.md` §3.1~§3.3, 실제 실행 절차는 `${CLAUDE_PLUGIN_ROOT}/skills/claude-code-team/SKILL.md`(레포 기준 `plugins/atp/skills/claude-code-team/SKILL.md`)가 정본이다. Claude Code-specific 도구명과 event spelling은 이 appendix와 전용 skill에만 둔다.

## 1. Current Claude Code orchestration capability

<a id="current-claude-code-orchestration-capability"></a>

<!-- claude-code:orchestration-capability:begin -->
```yaml
formal_adapter_enabled: false
manual_wait_polling_supported: false
host_managed_subagent_orchestration: supported
team_execution_enabled: true
```
<!-- claude-code:orchestration-capability:end -->

Claude Code의 `Agent` 툴은 async spawn이다. Spawn 호출은 즉시 `Async agent launched` ack와 environment identity(`agentId`)를 반환하며, 이 ack는 결과가 아니다. Child의 terminal result는 harness가 `<task-notification>` event로 parent 대화에 자동 주입한다(inline `<result>` + `status`). 구버전 Claude Code의 동기(blocking) `Agent`/`Task` 툴과 달리 spawn 호출 자체가 barrier가 아니므로, barrier는 아래 §3의 turn-end await다.

- Terminal delivery: `<task-notification>` — `task-id`, `status`, inline `<result>`, `output_file` 경로 포함. `output_file`은 subagent transcript라 읽기 금지 대상이다(§3) — `<result>`가 잘려 전문이 필요하면 같은 `agentId`에 `SendMessage`로 재전송을 요청한다(continuation). `SendMessage`가 없는 nested advisor는 부분 결과 + `truncated_result` concern으로 반환하고 전문 획득은 상위에 맡긴다.
- 완료 판정의 harness 규칙: agent가 **live background children 없이** 정지할 때만 그 agent를 완료로 처리한다. Live children을 가진 채 툴 호출 없이 턴을 끝내면 agent는 종료되지 않고 **모델 호출 0으로 suspend**되며, child terminal마다 재기동된다. 이 규칙은 nested agent(advisor가 worker를 spawn한 경우)에도 동일하게 적용된다(2026-08-25 smoke E1/E3 실측).
- `TaskOutput` 툴은 nested subagent 툴셋에 존재하지 않는다(smoke E2). Blocking wait 프리미티브 후보로 사용하지 않는다.

## 2. Formal subscription profile

Task-notification 기반 managed delivery는 formal `environment_subscription` 지원을 뜻하지 않는다. Formal capability 12개 판정은 다음과 같다.

<!-- claude-code:formal-capabilities:begin -->
```yaml
formal_capabilities:
  timeout_free_suspend: supported
  targeted_wait_any: unsupported
  targeted_wait_all: unsupported
  terminal_event_subscription: unknown
  approval_event_subscription: unknown
  user_steering_preemption: supported
  await_cancellation: unsupported
  compact_changed_invocation_delta: supported
  stable_event_identity: unsupported
  environment_deduplication: unknown
  completion_coalescing: unknown
  internal_keepalive_no_model_wake: supported
```
<!-- claude-code:formal-capabilities:end -->

- `targeted_wait_any`/`targeted_wait_all`: 관심 target 집합·`wake_on` 등록 API가 없다. 모든 live child의 terminal이 wake를 만든다.
- `terminal_event_subscription`: `status: completed`는 실측됐으나 `failed | interrupted`의 event 구분 전달은 미관측 — `unknown`.
- `stable_event_identity`: `task-id`는 agent identity이지 event identity가 아니다. 같은 task-id가 재통지될 수 있다(resume된 agent가 다시 정지하는 경우) — 재전달 식별용 event ID 부재.
- `await_cancellation`: persistent await identity 개념이 없어 별도 취소 불가. `TaskStop`은 child 종료 control이지 await 취소가 아니다.

따라서 `formal_adapter_enabled: false`다. ATP는 timer, no-op 도구 호출, 반복 상태 조회로 빈 formal capability를 합성하지 않는다. Formal subscription과 host-managed all-results barrier는 별도 capability이며, Claude Code는 후자가 `supported`다.

## 3. Managed orchestration contract — turn-end await

첫 collaboration action 전에 `claude-code-team` skill을 선택하고 전체 내용을 읽는다. 소비 프로젝트의 매 task에서는 capability 확인용 child, timeout probe, liveness probe, source/install parity 검사를 실행하지 않는다. 배포된 profile을 사용하고 실행 중 임의 추론으로 덮어쓰지 않는다.

정상 dispatch는 다음 계약을 갖는다.

1. 배치의 child 전원을 **한 assistant 메시지의 병렬 `Agent` 호출**로 dispatch한다. Child prompt에는 정상 경로에서 intermediate message를 보내지 않고 terminal result 한 건만 반환하도록 명시한다.
2. Spawn ack 수신 후 실제 준비 작업(ledger 기록 등)이 남았으면 수행하고, 대기만 남았으면 **짧은 상태 텍스트로 턴을 종료**한다. 대기 목적의 툴 호출은 0건이다.
3. `<task-notification>` wake마다 해당 child의 `status`/`<result>`를 수집하고 dispatch mapping의 report invocation identity에 연결한다. 미수집 child가 남았고 실행할 준비 작업이 없으면 다시 턴을 종료한다.
4. 전달된 nonterminal update(steering 회신 등)는 `running`일 뿐 terminal delivery가 아니다.
5. Terminal delivery = notification의 명시적 terminal disposition(`completed | failed | interrupted`) 전부이며 barrier 계수에 포함된다(승인된 recovery로 `TaskStop`된 child의 `interrupted` 포함). `completed`만 정상 수집 결과다. `failed`가 전달돼도 남은 live child 수집을 계속하고, recovery 검토는 전건 terminal 후 batch 반환된 곳에서 시작한다 — batch 반환 전 retry/interrupt/fallback 0건.
6. 모든 요청 child의 terminal delivery를 받고 result contract를 검증·취합하기 전에는 report invocation/session completion, `ended_at`, parent final response를 만들지 않는다. 일부 `failed`여도 전건 terminal이면 barrier는 열린다 — 실패 건은 §2.5 disposition과 함께 반환하며 교착이 아니다.
7. Wake가 오지 않는 동안의 대체 행동은 없음이 정답이다. Suspend는 모델 호출 0의 무비용 상태이고, 경과 시간·무소식은 상태 전이·자가 회복의 근거가 아니다. Hang 의심의 처분은 사용자 몫이며 사용자 steering/interrupt가 suspend를 언제든 선점한다.

**Turn-end 의미 경계**: live child가 하나도 없는 상태의 턴 종료는 harness가 그 agent의 최종 반환으로 처리한다. 따라서 (a) 대기용 턴 종료 텍스트에 최종 보고를 쓰지 않고, (b) 마지막 child 수집 뒤에는 반드시 최종 산출을 완성한 뒤 종료한다. 모든 child가 이미 terminal인데 미수집 통지가 남은 race는 큐에 보존된 notification이 재기동시키므로 유실되지 않는다(smoke E1: spawn ack 직후 턴 종료 → 이후 notification 도착 → 재기동 실측).

**금지 목록** (관측된 실패 사례 — 2026-08-25 소비 세션 `c9027225`에서 advisor가 no-op `echo` 틱 233회+와 child transcript 파일 폴링으로 개선 전 abstract 계약을 improvise):

- 대기 목적의 no-op 도구 호출(`echo`, `sleep`, 기타 keepalive 틱)
- `~/.claude/projects/**`의 세션/subagent transcript 파일 읽기, `tasks/*.output` 파일 읽기(잘린 결과 전문은 `SendMessage` continuation으로 획득)
- Child transcript의 파일 크기·라인 수·mtime liveness 폴링, 동일 snapshot 반복을 완료로 해석
- `ListAgents`/`/tasks` 조회를 정상 경로 scheduling에 사용 — 횟수 무관 0건이 fixture. 예외는 승인된 recovery의 completion race 재확인 단발 조회뿐이며 `list_calls`에 계수
- `TaskOutput` 의존(nested 툴셋에 미존재)
- Pending child 결과의 예측·합성

Host는 child execution, notification routing, suspend/wake scheduling과 terminal delivery를 소유한다. ATP는 logical task/DAG, preallocated report identity, result validation/integration, recovery 승인, result acceptance, write ownership, report/session lifecycle을 소유한다.

## 4. Identity mapping

Dispatch 전에 `report_invocation_id`를 할당하고(발급 주체·형식은 protocol §2.5와 task SKILL의 기존 규칙 — 호출 주체가 unique value를 만들어 child 입력에 주입) 다음을 연결한다.

- spawn call identity (`tool_use_id`)
- spawn ack의 environment identity: `agentId`
- notification의 `task-id` (= `agentId`)
- preallocated `report_invocation_id`

Report invocation은 exact field `environment_invocation_id`에 `agentId`를 기록하며 alias나 표시명 대체를 허용하지 않는다. 같은 `task-id`의 재통지는 collected set으로 dedup해 한 번만 수집한다. `SendMessage`로 같은 agent에 보내는 follow-up은 steering/continuation이며 clean retry가 아니다. Retry는 새 `agentId`와 `retry_of`를 가져야 한다.

## 5. Ledger and measurement

Ledger row는 정확히 `recorded_at`, `await_id`, `owner_report_invocation_id`, `event`, concrete `source_ref`, `details`의 six-field envelope을 유지한다. Managed mode의 `await_id`는 `null`이다.

Managed mode의 scheduling ledger는 두 종류 row만 갖는다: preflight의 `await_capability_checked` 1회 + 종료 시 aggregate `measurement`. Per-wake/per-terminal scheduling row는 만들지 않는다 — `await_registered`/`wake_batch`는 formal `environment_subscription` 전용 vocabulary다. Wake·terminal 사건별 기록은 lifecycle ledger(protocol §2.5)가 담당한다.

Capability row의 `details`에는 exact keys와 values `formal_adapter_enabled: false`, `manual_wait_polling_supported: false`, `host_managed_subagent_orchestration: supported`, `team_execution_enabled: true`, `selected_mode: host_managed_subagent_orchestration`을 모두 기록하고 `profile_ref`는 exact string `claude-code-lifecycle-routing.md#current-claude-code-orchestration-capability`다.

Measurement 필드 집합은 protocol §2.5의 managed `measurement` 규정을 따른다: `requested_agents`, `requested_report_invocation_ids`, `spawn_calls`, `nonterminal_updates`, `terminal_deliveries`, `collected_results`, `manual_wait_calls`, `list_calls`, `interrupt_calls`, `semantic_recovery_actions`. 전건 `completed`인 정상 fixture는 `requested_agents == spawn_calls == terminal_deliveries == collected_results`. `failed`가 있으면 `terminal_deliveries == requested_agents == spawn_calls`는 유지되고 `collected_results`는 `completed` 수이며 차이 사유를 `details`에 남긴다. `manual_wait_calls: 0`(대기 목적 도구 호출 수 — no-op 틱·transcript 폴링·liveness 조회 포함), `list_calls: 0`, `interrupt_calls: 0`, `semantic_recovery_actions: 0`이다. 관측하지 못한 token/latency telemetry는 `null`이며 0으로 합성하지 않는다.

## 6. Lifecycle and recovery

- Notification의 명시적 terminal disposition(`completed | failed | interrupted`)이 terminal delivery이며, `completed` + inline `<result>`만 정상 수집 결과다. `failed`/error가 관측되면 lifecycle ledger에 기록하고 남은 child 수집을 계속하며, §2.5의 사용자 승인·독립 invocation·retry cap 계약은 batch 반환 후 approval authority가 있는 곳(orchestrator→사용자)에서 적용한다. Nested advisor는 disposition `awaiting_user_decision`으로 반환할 뿐 직접 recovery를 시작하지 않는다.
- 실제 capability error(예: spawn 거부, notification 채널 오류)가 관측되면 manual polling, automatic retry/interrupt/fallback, authority mutation 또는 automatic Tier B 전환으로 보상하지 않는다. 마지막 environment-authoritative state와 authority를 보존하고 blocked/user-decision 경로를 사용한다.
- `TaskStop`은 승인된 recovery에서만 사용하고, 그 결과가 명시적으로 확인될 때만 `interrupted`로 기록한다.
- Child 승인 프롬프트는 사용자 permission 흐름으로 표면화되며 parent에 structured `approval_required` event로 전달되지 않는다(`unknown`). 관측 불가 축은 합성하지 않는다.
- Late completion, read-only result quarantine, write isolation/ownership, partial write 분류는 공통 protocol §2.5를 그대로 따른다.

## 7. Completion order

종료 순서는 codex appendix와 동일한 공통 11단계다: 모든 요청 subagent terminal result 수신 → 결과 계약 검증·통합 → verification → retrospective → report 반영 → report 재스테이징 → staged 재검증 → 요청 범위 mutation/commit/push/remote verification → session `ended_at` → report 최종 read-only 검증 → 사용자 최종 응답. 미래 `ended_at`을 terminal 전에 미리 쓰면 실패다.

## 8. Maintainer evidence

2026-08-25 Claude Code 2.1.243 (darwin) 격리 smoke — general-purpose parent + Explore children, 폴링·대기용 툴 호출 금지 지시:

| smoke | product/result | 판정 |
|---|---|---|
| E1: terminal-only 1-agent | spawn 후 툴 호출 없이 턴 종료 → child terminal에 재기동 → 최종 `RESUMED: <child 결과>` 반환. 대기 중 모델 호출 0 | pass |
| E2: nested `TaskOutput` 가용성 | 툴 자체가 subagent 툴셋에 부재 — barrier 후보 아님 | 확인 |
| E3: staggered 2-agent all-results barrier | fast/slow(+25s) 동시 spawn, wakes=3, per-child delivery(`batched=no`), 전건 수집, manual wait 0 | pass |

Codex smoke 2(nonterminal 뒤 delayed terminal)의 실패 축 — parent가 terminal 전에 final을 만드는 조기 종료 — 는 Claude Code에서는 harness가 live children 보유 agent를 완료 처리하지 않으므로 구조적으로 부재하며, E3의 첫 wake 후 재-suspend → +25s delayed terminal 수집이 같은 축을 커버한다. 보존 결과는 소스 레포 전용 경로 `tests/runtime-behavior/evidence/claude-code-2.1.243-20260825.json`에 기록한다(번들 미포함 — 설치 환경에서 해소되지 않는 maintainer 근거 경로).

반증 사례(개선 동기): 같은 날 소비 프로젝트 세션 `c9027225`(ATP 2.15.0, Claude Code 용 host skill 부재)에서 research-advisor가 worker 6개 spawn 후 no-op `echo idle` 틱 233회+·child transcript 파일 크기 폴링으로 대기를 improvise — 기능은 수렴했으나 wake당 전체 컨텍스트 재추론 비용이 발생했다. 이 appendix와 `claude-code-team` skill이 그 gap을 닫는다.

## 9. 실행 체크리스트

- [ ] 첫 collaboration action 전에 `claude-code-team` skill 전체를 읽었는가?
- [ ] 배치 child 전원을 한 메시지의 병렬 `Agent` 호출로 dispatch했는가?
- [ ] 모든 child prompt에 terminal-only 반환 계약을 전달했는가?
- [ ] 대기 목적 툴 호출(no-op 틱·transcript 폴링·liveness 조회)이 0인가?
- [ ] 대기가 필요한 시점마다 턴을 종료해 harness suspend에 맡겼는가?
- [ ] 같은 task-id 재통지를 dedup했는가?
- [ ] terminal delivery와 collected result가 요청 agent 전원과 일치하는가?
- [ ] 최종 산출은 마지막 child 수집 뒤에만 완성했는가?
- [ ] capability error를 automatic Tier B/retry/interrupt/fallback으로 숨기지 않았는가?
