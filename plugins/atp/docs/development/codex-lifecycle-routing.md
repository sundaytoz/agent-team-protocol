---
kind: development
title: Codex managed subagent orchestration and lifecycle routing appendix
description: ATP의 host-neutral lifecycle과 result barrier를 Codex built-in managed subagent workflow에 매핑하는 조건부 appendix.
owner: template-maintainer
stability: draft
host_scope: codex
last_reviewed: 2026-09-08
---

# Codex managed subagent orchestration and lifecycle routing appendix

이 문서는 Codex host에서만 읽는 조건부 appendix다. 공통 lifecycle·result integration·report authority는 `agent-team-protocol.md` §2.5, host-neutral capability 판정은 `platform-adapters.md` §3.1~§3.3, 실제 실행 절차는 `../../skills/codex-team/SKILL.md`가 정본이다. Codex-specific 도구명과 event spelling은 이 appendix, 전용 skill, maintainer runtime validator에만 둔다.

## 1. Current Codex orchestration capability

<a id="current-codex-orchestration-capability"></a>

<!-- codex:orchestration-capability:begin -->
```yaml
formal_adapter_enabled: false
manual_wait_polling_supported: false
host_managed_subagent_orchestration: unsupported
team_execution_enabled: false
```
<!-- codex:orchestration-capability:end -->

공식 OpenAI 문서는 Codex app/CLI/IDE에서 직접 요청 또는 적용 가능한 `AGENTS.md`/skill instruction으로 delegation을 시작할 수 있고, Codex가 spawn, follow-up routing, 결과 대기와 thread lifecycle을 관리하는 product workflow를 설명한다. 그러나 이 설명만으로 ATP의 예상 밖 nonterminal update와 staggered multi-agent all-results barrier를 versioned correctness primitive로 확정하지 않는다.

- 공식 계약: <https://learn.chatgpt.com/docs/agent-configuration/subagents>
- Skill loading 계약: <https://learn.chatgpt.com/docs/build-skills> — name/description으로 선택한 뒤 전체 `SKILL.md`를 읽는다.
- ChatGPT Work는 eligible-account hosted surface이며 이 local Codex profile과 분리한다.

공식 문서는 low-level event schema, failure/approval taxonomy, latency SLA, stable event identity를 보장하지 않는다. 2026-08-26 Codex CLI 0.149.1 격리 smoke는 terminal-only 1-agent와 nonterminal 뒤 delayed terminal 1-agent가 통과했지만, staggered 2-agent에서는 두 spawn 중 fast terminal 하나만 전달된 뒤 parent turn이 종료됐다. 최소 child context(`fork_turns: none`)에서도 동일했다. 따라서 tested CLI profile은 `unsupported`, app/IDE empirical status는 `unknown`이다. 공식 보장과 empirical 관측을 서로 대체하지 않는다.

<a id="managed-orchestration-contract-fixture"></a>

<!-- codex:managed-contract-fixture:begin -->
```yaml
formal_adapter_enabled: false
manual_wait_polling_supported: false
host_managed_subagent_orchestration: supported
team_execution_enabled: true
```
<!-- codex:managed-contract-fixture:end -->

위 block은 future supported implementation이 충족해야 할 deterministic contract fixture이며 배포 capability 판정이 아니다.

## 2. Formal subscription profile

Codex built-in managed workflow 지원은 formal `environment_subscription` 지원을 뜻하지 않는다. Validator와 ledger가 대조하는 formal capability 정본은 다음 12개다.

<!-- codex:formal-capabilities:begin -->
```yaml
formal_capabilities:
  timeout_free_suspend: unsupported
  targeted_wait_any: unsupported
  targeted_wait_all: unsupported
  terminal_event_subscription: unknown
  approval_event_subscription: unknown
  user_steering_preemption: supported
  await_cancellation: unsupported
  compact_changed_invocation_delta: unsupported
  stable_event_identity: unsupported
  environment_deduplication: unsupported
  completion_coalescing: unknown
  internal_keepalive_no_model_wake: unsupported
```
<!-- codex:formal-capabilities:end -->

따라서 `formal_adapter_enabled: false`다. ATP는 timer, bounded `wait_agent`, 반복 `list_agents`로 빈 formal capability를 합성하지 않는다. Formal subscription과 product-managed all-results barrier는 별도 capability다.

## 3. Managed orchestration contract

첫 collaboration action 전에 `codex-team` skill을 선택하고 전체 내용을 읽는다. 소비 프로젝트의 매 task에서는 capability 확인용 child, timeout/wait/list probe, runtime validator, source/install parity 검사를 실행하지 않는다. 배포된 profile을 사용하고 실행 중 임의 추론으로 덮어쓰지 않는다. 현재 tested CLI profile에서는 first collaboration action을 실행하지 않고 explicit blocked/user-decision으로 반환한다.

정상 dispatch는 다음 계약을 갖는다.

1. `spawn_agent`로 bounded child task를 요청한다. Child prompt에는 정상 경로에서 intermediate `MESSAGE`를 보내지 않고 terminal result 한 건만 반환하도록 명시한다.
2. 요청한 여러 child가 있으면 모두 dispatch하고 Codex built-in workflow가 결과 대기와 follow-up routing을 관리하도록 둔다.
3. ATP orchestrator는 `wait_agent` polling loop와 `list_agents` polling을 운영하지 않는다.
4. 예상 밖 `Message Type: MESSAGE`가 전달돼도 invocation은 `running`이다. `Message Type: FINAL_ANSWER` 또는 environment의 명시적 terminal delivery만 terminal 후보다.
5. 모든 요청 child의 terminal delivery를 받고 result contract를 검증·취합하기 전에는 report invocation/session completion, `ended_at`, parent final response를 만들지 않는다.

Host는 child execution, follow-up routing, all-results wait와 terminal delivery를 소유한다. ATP는 logical task/DAG, preallocated report identity, result validation/integration, recovery 승인, result acceptance, write ownership, report/session lifecycle을 소유한다.

## 4. Identity mapping

표시명 정규화만으로 identity를 추론하지 않는다. Dispatch 전에 `report_invocation_id`를 할당하고 다음을 연결한다.

- spawn call identity
- spawn output의 environment identity: `agent_id`가 있으면 그 값, 없고 canonical `task_name`이 있으면 그 값
- requested task name
- preallocated `report_invocation_id`

Report invocation은 exact field `environment_invocation_id`를 사용하며 alias를 허용하지 않는다. 예를 들어 environment가 `/root/research_advisor`를 반환하고 report가 `research-advisor`를 표시하더라도 위 dispatch mapping이 있을 때만 같은 invocation으로 검증한다. Retry는 새 environment identity와 `retry_of`를 가져야 하며 same-invocation `followup_task`는 clean retry가 아니다.

## 5. Ledger and measurement

Ledger row는 정확히 `recorded_at`, `await_id`, `owner_report_invocation_id`, `event`, concrete `source_ref`, `details`의 six-field envelope을 유지한다. Managed mode의 `await_id`는 `null`이다.

정상 완료 뒤 aggregate `measurement`는 다음을 기록한다.

- `requested_agents`
- `requested_report_invocation_ids`
- `spawn_calls`
- `nonterminal_updates`
- `terminal_deliveries`
- `collected_results`
- `manual_wait_calls`
- `list_calls`
- `interrupt_calls`
- `semantic_recovery_actions`

Capability row는 profile의 네 축과 exact `selected_mode: host_managed_subagent_orchestration`을 생략 없이 기록한다. Measurement의 `mode`도 같은 exact value이며 축약 alias를 허용하지 않는다.

정상 fixture는 `requested_agents == spawn_calls == terminal_deliveries == collected_results`, `manual_wait_calls: 0`, `list_calls: 0`, `interrupt_calls: 0`, `semantic_recovery_actions: 0`이다. 관측하지 못한 token/latency telemetry는 `null`이며 0으로 합성하지 않는다.

모델은 미래 transcript ordinal을 예측해 쓰지 않는다. 실행 중에는 session/report/environment identity와 monotonic event identity를 사용해 `session:<session_id>:report:<report_invocation_id>:environment:<environment_id>:event:terminal-NNNN` 형태로 기록한다. Maintainer validator가 보존 JSONL의 실제 spawn mapping, terminal delivery 순서와 timestamp에 사후 연결한다. 연결되지 않는 `source_ref`는 실패다.

## 6. Lifecycle and recovery

실제 capability error가 관측되면 manual polling, automatic retry/interrupt/fallback, authority mutation 또는 automatic Tier B 전환으로 보상하지 않는다. 마지막 environment-authoritative state, result acceptance authority와 write ownership을 보존하고 요청 의도에 맞는 blocked/user-decision 경로를 사용한다.

`list_agents`는 정상 scheduling이나 capability probe에 사용하지 않는다. 기존 invocation의 명시적 terminal failure/interruption 뒤 사용자가 recovery를 승인했고 completion race 재확인이 필요할 때만 기존 lifecycle 계약에 따른 단발 authoritative 조회가 허용된다. `interrupt_agent`, 새 `spawn_agent`, fallback과 authority mutation도 같은 terminal evidence와 승인 계약 뒤에만 가능하다.

Late completion, read-only result quarantine, write isolation/ownership, partial write 분류, retry cap과 mandatory verification은 공통 protocol §2.5를 그대로 따른다. 공식 문서가 보장하지 않는 approval/failure detail은 `unknown`으로 유지한다.

### 6.1 Codex tool and lifecycle mapping

Codex의 `spawn_agent`는 새 child environment identity를 만들고, `followup_task`는 같은 environment identity의 continuation을 routing한다. `fork_turns`는 child에 전달할 대화 범위를 정할 뿐 lifecycle state나 retry attempt를 만들지 않는다. `send_message`는 실행 중 steering이며 terminal delivery가 아니다. `interrupt_agent`는 승인된 recovery에서만 사용하고, 반환된 environment event가 명시적 `interrupted`일 때만 termination으로 기록한다. `list_agents`와 `wait_agent`는 정상 managed scheduling에 사용하지 않는다.

Environment가 전달한 nonterminal update는 `running`으로 유지한다. 명시적 terminal delivery만 `completed`로 매핑한다. Status 자체가 unavailable/error이거나 의미가 불명확하면 `environment_state_unknown`이며 silence나 시간으로 `failed`를 합성하지 않는다.

### 6.2 Approval relay and continuation

관측된 `approval_required`와 이를 parent/user에게 relay하거나 같은 environment identity로 continuation할 capability는 별도 축이다. Relay가 unsupported/unavailable이어도 관측 state를 `environment_state_unknown`으로 낮추지 않는다. 반대로 status unavailable/error인 경우만 `environment_state_unknown`이다.

Approval relay/control이 unavailable이면 child `ended_at`과 `termination`을 비워 둔 채 phase control만 `blocked`로 반환한다. Environment provenance와 concrete `source_ref`, capability ref를 concern과 ledger에 남기고 retry, interrupt, fallback, result-acceptance/write-ownership mutation은 0건이다. Relay가 복구되어 같은 environment identity를 continuation하면 attempt와 retry accounting을 바꾸지 않는다.

## 7. Completion order

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

Validator는 timestamp scalar만 비교하지 않는다. Report completion 또는 termination을 실제로 serialize한 transcript event가 마지막 요청 child terminal delivery 뒤에 있는지 검사한다. 미래 `ended_at`을 terminal 전에 미리 쓰면 실패다.

## 8. Maintainer evidence

`supported` 판정은 deterministic fixture만으로 만들지 않는다. Release 전 격리된 temporary `CODEX_HOME`/workspace에서 다음 실제 smoke를 실행하고 JSONL·report·ledger를 보존한다.

1. agent 1개, terminal result만 반환
2. agent 1개, nonterminal update 뒤 지연 terminal result
3. agent 2개, 서로 다른 시각에 terminal result 반환

세 smoke는 manual `wait_agent` 0, `list_agents` 0, 요청 전원 terminal/result 수신, parent final과 report completion이 마지막 terminal 뒤, timeout/polling semantic action 0을 충족해야 한다. 실제 사용자 plugin cache, settings, hooks와 소비 프로젝트 설정은 변경하지 않는다.

2026-08-26 isolated Codex CLI 0.149.1 결과:

| smoke | product/result | 판정 |
|---|---|---|
| terminal-only 1-agent | spawn 1, terminal/collected 1, manual wait/list/interrupt 0, terminal 뒤 completion/final | pass |
| nonterminal 뒤 delayed terminal 1-agent | nonterminal `MESSAGE`는 running 유지, 뒤이은 terminal/collected 1, manual wait/list/interrupt/recovery 0 | pass |
| staggered terminal 2-agent | `fork_turns: none`; spawn 2 뒤 fast terminal 1개만 전달되고 slow terminal 없이 parent turn 종료 | fail |

따라서 single-agent 두 case가 green이어도 필수 multi-agent barrier가 실패하므로 deployed CLI profile은 `unsupported`, `team_execution_enabled: false`다. App/IDE는 같은 smoke 미수행으로 `unknown`이다. 공개 가능한 count·ordering·artifact hash는 `tests/runtime-behavior/evidence/codex-cli-0.149.1-20260826.json`에 기록하고 raw transcript는 커밋하지 않는다. 0.147.0 결과는 `tests/runtime-behavior/evidence/codex-cli-0.147.0-20260819.json`에 historical evidence로 보존한다.

### 8.1 Supplemental topology and capacity probes

0.149.1의 별도 maintainer probe는 result barrier와 독립된 다음 사실을 확인했다.

| probe | 관측 |
|---|---|
| nested spawn | `root → child → grandchild` 실제 spawn과 terminal 완료 |
| cumulative child fan-out | 한 child에서 short-lived grandchild 5개 모두 spawn 승인; 누적 상한 미확정 |
| saturated child fan-out | root + child가 active일 때 grandchild 2개 승인, 다음 3개는 `agent thread limit reached` |
| active capacity | limit 시 primary 포함 총 4 active threads |
| depth under saturation | root 아래 descendant 3단계 승인, 4단계 spawn은 같은 limit 오류 |

공식 OpenAI 문서의 `agents.max_concurrent_threads_per_session`은 primary를 제외한 concurrently open spawned-agent threads를 제한하며 unset이면 Codex가 default를 선택한다. Probe의 격리 설정은 unset이었다. 따라서 위 숫자는 0.149.1 default의 경험적 관측이지 모든 사용자 설정의 고정 상수가 아니다.

이 관측으로 bounded pool candidate를 설계한다. Scheduler는 pending queue와 running identity map을 유지하고, slot exhaustion을 task failure나 retry attempt로 세지 않으며, terminal delivery로 slot이 해제된 뒤 pending task를 refill한다. Fixed sleep, 반복 `list_agents`, 무변화 snapshot polling은 정상 scheduler primitive가 아니다. 이 candidate는 release-qualified execution mode가 아니며, 모든 nonterminal/control qualification이 통과하기 전 deployed profile은 위 §1의 `unsupported`를 유지한다.

첫 source-skill candidate smoke 결과는 다음과 같다.

| candidate | requested/accepted/terminal/collected | pool wait | max running | 판정 |
|---|---|---:|---:|---|
| root-owned flat pool | 5/5/5/5 | 2 | 3 | pass |
| nested pool owner의 worker queue | 5/5/5/5 | root 1 + owner 4 | workers 2 | pass |
| capacity denial 뒤 refill | tasks 5 / attempts 6 / accepted 5 / terminal 5 / collected 5 | 2 | 3 | pass |

세 candidate 모두 `list_agents`와 `interrupt_agent` 0회였다. Capacity denial은 failure/retry로 세지 않고 pending으로 복귀했으며 terminal 뒤 새 environment identity로 실제 refill됐다. Candidate source/install byte parity도 SHA-256 `bcfbdd0f0f7d066233155faebdec9aadb78de73fc2bfa057b3c7aec740eee146`로 일치했고 설치본 flat/nested/denial-refill 최소 회귀가 통과했다.

후속 nonterminal/control qualification은 다음처럼 실패했다.

| candidate | 핵심 관측 | 판정 |
|---|---|---|
| saturated nonterminal → terminal | 최초 비포화 run은 superseded. Rerun은 `MESSAGE`에서 running 3/pending 2, release/refill 0, 같은 child terminal까지 관측했으나 requested 5, attempts/accepted 3/3, terminal 3, collected 1, wait 2에서 두 번째 join이 멈춤; parent final 0 | fail |
| wait 중 user steering | queue accepted 1, scheduler control delivery와 send/follow-up 0; requested/accepted 5/5, terminal/collected 4/4, wait 5, list/interrupt 0; parent final 0 | fail |
| approval relay/continuation | interactive overlay가 child를 식별하고 reject decision 1을 relay; target은 `turn_aborted`, same-identity continuation과 target terminal 0; companion terminal 1, wait 2, parent final 0 | fail |
| cancellation | running 3/pending 2에서 queue accepted 1이나 scheduler delivery 0; 이후 pending 두 task가 spawn돼 accepted 5, terminal/collected 4/4, wait 4, interrupt 0; parent final 0 | fail |

A의 explicit-failed initial child는 실제 terminal 3건에 포함하지만 scheduler는 그 wake에서 result 하나만 collected했다. C의 harmless marker는 생성되지 않았다. D smoke를 종료하기 위한 harness 외부 정리는 scheduler cancellation/terminal confirmation으로 세지 않는다. 공식 OpenAI 문서가 interactive approval overlay와 queued control 동작을 설명하더라도 ATP의 capability 판정은 실제 active-wait delivery, identity continuation과 completion ordering을 우선한다.

Qualification이 all-PASS가 아니므로 `bounded_pool_orchestration` capability 축과 execution mode를 배포 계약에 추가하지 않았고, version/release metadata도 전환하지 않았다. §1의 four-axis profile과 `team_execution_enabled: false`가 그대로 정본이며 built-in all-results P0도 open이다. 재검증은 (1) A에서 이미 배달된 terminal 전부를 소비한 뒤 terminal-triggered refill로 5/5를 수집하고, (2) active join에 steering/cancellation을 실제 전달해 pending dispatch를 닫으며, (3) approval reject 뒤 동일 child identity를 continuation해 terminalize해야 한다. 전체 sanitized count, ordering과 artifact hash는 `tests/runtime-behavior/evidence/codex-cli-0.149.1-20260826.json`을 따른다.

### 8.2 Hook-guarded candidate qualification

2026-08-28 fresh source install에 bundled `hooks/hooks.json`, standard-library Python runner와
exact-hash `SessionStart` marker를 추가한 격리 후보를 검증했다. T1 hook coverage, T2 saturated
nonterminal terminal-triggered refill, T3 incomplete root Stop barrier, T5 interactive approve
same-identity continuation과 T8 nested owner isolation은 pass였다. Untrusted hook과
`features.hooks=false`에서도 marker가 없어 child spawn 0으로 닫혔다.

전체 qualification은 fail이다.

| smoke | 관측 | 판정 |
|---|---|---|
| T4 steering | active wait 중 queue accepted 1, `UserPromptSubmit` delivery와 send/follow-up 0 | fail |
| T6 cancellation | active wait 중 queue accepted 1, cancel ledger/actual interrupt 0, synthetic terminal 0 | fail |
| T7 capacity denial | logical tasks/attempts/accepted/terminal/collected `5/6/5/5/5`; parent denial 1, hook ledger denial 0 | fail |
| T9 parity | source/install byte parity와 설치본 T1/T2는 pass, 필수 설치본 T7은 fail | fail |

T7의 failed `spawn_agent` 호출에는 `PostToolUse`가 발생하지 않았다. 두 번째 Pre spawn만으로
이전 attempt를 capacity denial로 추정하는 방식은 missing event를 synthetic PASS로 바꾸므로
채택하지 않는다. Unix `python3` runner는 pass였지만 Windows `py -3`와
`allow_managed_hooks_only`는 unknown이다. 공개 count/order/hash는
`tests/runtime-behavior/evidence/codex-cli-0.149.1-hook-guarded-20260828.json`을 따른다.

### 8.3 2026-08-31 축별 재판정과 A축 blocker 해소

2026-08-28 판정은 이질적인 smoke 9개를 단일 promotion boolean으로 접었다. §3.2의 축 직교
원칙에 맞춰 backlog Phase 3를 all-results barrier(A) / in-flight control delivery(B) /
approval continuation(C) / packaging scope(D) 네 축으로 분해했다. 축 정의와 smoke 매핑은
`docs/backlog/codex-cli-hook-guarded-bounded-pool.md` §Phase 3가 정본이다.

축별 재판정에서 두 가지가 드러났다.

**T7/T9(A축)는 host 제약이 아니라 candidate 구현 갭이었다.** Evidence 자체가
`requested/attempts/accepted/terminal/collected = 5/6/5/5/5`와
`parent_observed_capacity_denials: 1`을 기록한다. pool은 denial 감지, pending 복귀, refill,
전원 수집까지 정상 동작했고 hook ledger 라벨만 `attempted`로 남았다. Parent는 그 error를
`spawn_agent` 반환값으로 이미 authoritative하게 관측하므로(ADR-0020), scheduler가
`update_plan`의 `ATP_POOL_DENIED <pool> <index>/<total> <token>` marker로 그 사실을 durable
ledger에 재진술한다. `handle_pre_bind()`가 `ATP_POOL_BIND`로 이미 증명한 채널이며 새 host
capability를 요구하지 않는다. Hook은 manifest 일치, `accepted_identity` 부재, 미해소
`attempted` attempt 존재를 모두 검사한 뒤에만 수용하므로 synthetic denial 경로가 없다.
`PostToolUse`를 내보내는 host에서는 기존 경로가 동작하고 이미 기록된 attempt는 재계수하지 않는다.

**T4/T6(B축)은 통과 가능한 surface에서 측정되지 않았다.** 두 smoke의 artifact는 `root_jsonl`
= 비대화형 `codex exec --json` run이다. PASS한 T5만 `tui_rollout` = interactive PTY다. 공식
Subagents 문서와 `P2-codex-cli-controls.md`가 모두 running subagent의 live steer/stop을
interactive CLI 경로로 설명하므로, 비대화형 `codex queue` 결과는 B축의 판정 근거가 아니다.
B축은 `unsupported`가 아니라 `unknown`으로 기록한다.

### 8.4 2026-08-31 A축 재실행 결과 — PASS

같은 0.149.1에서 임시 `CODEX_HOME`, 임시 git workspace와 fresh source install로 A축을 재실행했다.
공개 count/order/hash는 `tests/runtime-behavior/evidence/codex-cli-0.149.1-hook-guarded-20260831.json`이다.

| 항목 | 2026-08-28 | 2026-08-31 |
|---|---|---|
| requested / attempts / accepted / terminal / collected | 5 / 6 / 5 / 5 / 5 | 5 / 6 / 5 / 5 / 5 |
| `hook_ledger_capacity_denials` | **0** | **1** |
| denial attestation | 없음 | `attested_by: parent_marker` |
| `list_calls` / `interrupt_calls` | 0 / 0 | 0 / 0 |
| 마지막 hook event | — | `Stop` (전원 collected 뒤) |
| source/install byte parity | pass | pass |
| 판정 | fail | **pass** |

Ledger가 원인과 해소를 동시에 보여준다. 실패한 `spawn_agent`의 `PreToolUse`는 있고
`PostToolUse`는 없다(spawn Pre 6 / Post 5). 그 결손 지점에서 scheduler가
`update_plan`으로 `ATP_POOL_DENIED`를 기록해 durable ledger의 attempt가
`capacity_denied` / `attested_by: parent_marker`로 확정됐고, denied task는 pending 복귀 후
새 identity로 refill돼 전원 수집됐다.

Host 실제 오류 원문은 `collab spawn failed: agent thread limit reached`로
`CAPACITY_TEXT` 부분일치를 확인했다.

부수적으로 같은 run들에서 H1(중복 wait 차단 + terminal delta 반환), H2(incomplete root
Stop 차단 후 같은 turn continuation), H3(task_name/bind identity), H6(invalid terminal의
same-identity continuation)이 실동작으로 재확인됐다.

두 가지 관측을 함께 기록한다.

- **기본 동시성 한계는 고정 상수가 아니다.** 기본 설정 run에서 spawn 4건이 모두 accepted됐다.
  §8.1의 "primary 포함 총 4 active threads"는 관측 조건에 의존한다. Denial을 결정론적으로
  재현하려면 `agents.max_concurrent_threads_per_session`을 명시 설정하고, child가 slot을
  붙잡고 있는 동안 초과 spawn을 시도해야 한다. 짧은 child는 다음 spawn 전에 slot을 반납한다.
- **`hooks/hooks.json`은 설치만으로 활성화된다.** manifest에 `hooks` 필드가 없어도 기본
  discovery 경로로 번들 hook이 실행됐고, 도구를 쓰지 않는 프롬프트에서도 `PLUGIN_DATA`에
  state/ledger row가 기록됐다. 이 packaging 부수효과는 §8.5의 add-on 분리로 base 번들에서 제거됐다.

따라서 A축은 PASS다. §1 four-axis profile과 `team_execution_enabled: false`는 D축 scope
선언과 위 packaging 결정이 끝날 때까지 유지한다. B축 결과는 그 결정과 독립이다.

### 8.5 2026-09-08 D축 — candidate hook의 옵트인 add-on 분리

TUI 최초 대면 측정(2026-09-08)에서 설치 직후 "Hooks need review / 8 hooks are new or changed /
Hooks can run outside the sandbox after you trust them"가 뜨고, trust는 `config.toml`의
`[hooks.state."<plugin>:hooks/hooks.json:<event>:0:0"] trusted_hash`로 항목 단위 영구 저장됨을
확인했다. Trust는 **command 문자열에만** 묶여 runner `.py` 내용을 바꿔도 유지된다 — 즉
`Trust all` 한 번이 이후 모든 릴리스의 runner 변경을 sandbox 밖에서 무확인 실행하는 동의가 된다.

`team_execution_enabled: false`인 base 소비자가 얻을 기능 없이 이 동의를 요구받는 것은 부당하므로
candidate hook을 base에서 빼 옵트인 add-on **`atp-codex-hooks`**(`plugins/atp-codex-hooks/`)로
분리했다. Runner는 byte 무수정이고 `hooks.json`은 description만 바뀌어 `hooks_sha256`이 재생성됐다.
`codex-team` §1 marker는 add-on 설치본 해시 기준이며, add-on 미설치 시 marker 부재 →
spawn 0 fail-closed는 그대로다. `$atp:task`는 이를 `skip: no-codex-hooks`로 기록하고 배포 profile의
mode로 차단 없이 계속한다. 이 분리는 packaging 형태 변경이며 §1 profile을 바꾸지 않는다.

남은 D축: 옵트인 경계 안 `allow_managed_hooks_only` 측정, Windows `py -3` runner scope 결정.
B축 T4는 interactive PTY 재측정 대기로 독립이다. 사용자 가이드는 add-on의
`docs/codex-hooks-usage.md`.

## 9. 실행 체크리스트

- [ ] 첫 collaboration action 전에 `codex-team` skill 전체를 읽었는가?
- [ ] 모든 요청 child에 terminal-only 정상 반환과 all-results integration 계약을 전달했는가?
- [ ] 정상 경로 manual wait/list/interrupt가 0인가?
- [ ] nonterminal update를 running으로 유지했는가?
- [ ] dispatch identity mapping과 report invocation identity가 one-to-one인가?
- [ ] terminal delivery와 collected result가 요청 agent 전원과 일치하는가? 불일치하면 supported 판정을 거부했는가?
- [ ] unknown telemetry를 `null`로 보존했는가?
- [ ] completion serialization과 parent final이 마지막 terminal 뒤인가?
- [ ] capability error를 automatic Tier B/retry/interrupt/fallback으로 숨기지 않았는가?
