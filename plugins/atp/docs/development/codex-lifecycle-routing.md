---
kind: development
title: Codex managed subagent orchestration and lifecycle routing appendix
description: ATP의 host-neutral lifecycle과 result barrier를 Codex built-in subagent orchestration(marker gate 없음, ADR-0026)에 매핑하는 조건부 appendix.
owner: template-maintainer
stability: draft
host_scope: codex
last_reviewed: 2026-10-29
---

# Codex managed subagent orchestration and lifecycle routing appendix

이 문서는 Codex host에서만 읽는 조건부 appendix다. 공통 lifecycle·result integration·report authority는 `agent-team-protocol.md` §2.5, host-neutral capability 판정은 `platform-adapters.md` §3.1~§3.3, 실제 실행 절차는 `../../skills/codex-team/SKILL.md`가 정본이다. Codex-specific 도구명과 event spelling은 이 appendix, 전용 skill, maintainer runtime validator에만 둔다.

## 1. Current Codex orchestration capability

<a id="current-codex-orchestration-capability"></a>

<!-- codex:orchestration-capability:begin -->
```yaml
formal_adapter_enabled: false
manual_wait_polling_supported: false
host_managed_subagent_orchestration: supported
team_execution_enabled: true
execution_scope: codex_builtin_subagents
```
<!-- codex:orchestration-capability:end -->

**Built-in 판정(2026-10-29, ADR-0026).** 별도 add-on, hook trust, 세션 marker 없이 Codex의 기본 subagent 기능으로 team execution을 연다. 이전의 marker gate(ADR-0025)는 기본 subagent 사용을 오히려 막아 제거했다. 아래 §8의 2026-08-26 staggered 2-agent 관측(결과 1건만 전달)은 알려진 한계로 기록하며 실행 gate로 쓰지 않는다.

공식 OpenAI 문서는 Codex app/CLI/IDE에서 직접 요청 또는 적용 가능한 `AGENTS.md`/skill instruction으로 delegation을 시작할 수 있고, Codex가 spawn, follow-up routing, 결과 대기와 thread lifecycle을 관리하는 product workflow를 설명한다. 그러나 이 설명만으로 ATP의 예상 밖 nonterminal update와 staggered multi-agent all-results barrier를 versioned correctness primitive로 확정하지 않는다.

- 공식 계약: <https://learn.chatgpt.com/docs/agent-configuration/subagents>
- Skill loading 계약: <https://learn.chatgpt.com/docs/build-skills> — name/description으로 선택한 뒤 전체 `SKILL.md`를 읽는다.
- ChatGPT Work는 eligible-account hosted surface이며 이 local Codex profile과 분리한다.

공식 문서는 low-level event schema, failure/approval taxonomy, latency SLA, stable event identity를 보장하지 않는다. 2026-08-26 Codex CLI 0.149.1 격리 smoke는 terminal-only 1-agent와 nonterminal 뒤 delayed terminal 1-agent가 통과했지만, staggered 2-agent에서는 두 spawn 중 fast terminal 하나만 전달된 뒤 parent turn이 종료됐다. 이 관측은 §8 이력으로 보존하며, 현재 profile은 이를 gate로 쓰지 않는다(ADR-0026).

<a id="managed-orchestration-contract-fixture"></a>

<!-- codex:managed-contract-fixture:begin -->
```yaml
formal_adapter_enabled: false
manual_wait_polling_supported: false
host_managed_subagent_orchestration: supported
team_execution_enabled: true
```
<!-- codex:managed-contract-fixture:end -->

위 block은 deterministic contract fixture다(validator `--profile host-managed`가 대조). 배포 profile의 네 축과 값이 일치하지만 fixture block은 계약 정본, 배포 block은 배포 판정으로 역할이 다르다.

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

첫 collaboration action 전에 `codex-team` skill을 선택하고 전체 내용을 읽는다. 소비 프로젝트의 매 task에서는 capability 확인용 child, timeout/wait/list probe, runtime validator, source/install parity 검사를 실행하지 않는다. 배포된 profile을 사용하고 실행 중 임의 추론으로 덮어쓰지 않는다.

정상 dispatch는 다음 계약을 갖는다.

1. `spawn_agent`로 child task를 요청하고 child prompt에 결과 계약을 명시한다.
2. 요청한 여러 child가 있으면 모두 dispatch한다.
3. 예상 밖 `Message Type: MESSAGE`가 전달돼도 invocation은 `running`이다. `Message Type: FINAL_ANSWER` 또는 environment의 명시적 terminal delivery만 terminal 후보다.
4. 모든 요청 child의 terminal delivery를 받고 result contract를 검증·취합하기 전에는 report invocation/session completion, `ended_at`, parent final response를 만들지 않는다.

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

Measurement는 관측값을 그대로 기록할 뿐 runtime 제약이 아니다. 아래 0 값은 maintainer contract fixture의 기대값이다. 정상 fixture는 `requested_agents == spawn_calls == terminal_deliveries == collected_results`, `manual_wait_calls: 0`, `list_calls: 0`, `interrupt_calls: 0`, `semantic_recovery_actions: 0`이다. 관측하지 못한 token/latency telemetry는 `null`이며 0으로 합성하지 않는다.

모델은 미래 transcript ordinal을 예측해 쓰지 않는다. 실행 중에는 session/report/environment identity와 monotonic event identity를 사용해 `session:<session_id>:report:<report_invocation_id>:environment:<environment_id>:event:terminal-NNNN` 형태로 기록한다. Maintainer validator가 보존 JSONL의 실제 spawn mapping, terminal delivery 순서와 timestamp에 사후 연결한다. 연결되지 않는 `source_ref`는 실패다.

## 6. Lifecycle and recovery

실제 capability error가 관측되면 manual polling, automatic retry/interrupt/fallback, authority mutation 또는 automatic Tier B 전환으로 보상하지 않는다. 마지막 environment-authoritative state, result acceptance authority와 write ownership을 보존하고 요청 의도에 맞는 blocked/user-decision 경로를 사용한다.

명시적 terminal failure/interruption 뒤의 retry, fallback과 authority mutation은 공통 사용자 승인 계약을 따른다.

Late completion, read-only result quarantine, write isolation/ownership, partial write 분류, retry cap과 mandatory verification은 공통 protocol §2.5를 그대로 따른다. 공식 문서가 보장하지 않는 approval/failure detail은 `unknown`으로 유지한다.

### 6.1 Codex tool and lifecycle mapping

Codex의 `spawn_agent`는 새 child environment identity를 만들고, `followup_task`는 같은 environment identity의 continuation을 routing한다. `fork_turns`는 child에 전달할 대화 범위를 정할 뿐 lifecycle state나 retry attempt를 만들지 않는다. `send_message`는 실행 중 steering이며 terminal delivery가 아니다. `interrupt_agent`는 반환된 environment event가 명시적 `interrupted`일 때만 termination으로 기록한다.

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

따라서 single-agent 두 case가 green이어도 필수 multi-agent barrier가 실패해 당시 deployed CLI profile은 `unsupported`, `team_execution_enabled: false`였다(현재 profile은 §1, ADR-0026). App/IDE는 같은 smoke 미수행으로 `unknown`이다. 공개 가능한 count·ordering·artifact hash는 `tests/runtime-behavior/evidence/codex-cli-0.149.1-20260826.json`에 기록하고 raw transcript는 커밋하지 않는다. 0.147.0 결과는 `tests/runtime-behavior/evidence/codex-cli-0.147.0-20260819.json`에 historical evidence로 보존한다.

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

### 8.2 Hook-guarded bounded pool 이력 (2026-08-28 ~ 2026-09-08, 제거됨)

Built-in barrier 실패를 보완하려고 `SessionStart` exact marker로 gate한 hook-guarded bounded pool을 검증했고, 2026-09-08 옵트인 add-on `atp-codex-hooks`로 분리해 선언 scope 안 `supported`로 승격했다(ADR-0025). 공개 count/order/hash는 `tests/runtime-behavior/evidence/codex-cli-0.149.1-hook-guarded-20260828.json`·`-20260831.json`·`-20260908.json`에 historical evidence로 보존한다. 이 경로는 §8.3에서 제거했다.

### 8.3 2026-10-29 marker gate 제거 (ADR-0026)

§8.2의 hook-guarded bounded pool과 `atp-codex-hooks` add-on은 제거했다. Exact marker 요구가 Codex 기본 subagent 사용을 막아 대부분의 소비자 세션이 Tier B로 떨어졌기 때문이다. 현재 profile은 marker 없이 `codex_builtin_subagents`로 team execution을 연다. §8.1~§8.2와 관련 evidence JSON은 historical record로만 보존한다.

## 9. 실행 체크리스트

- [ ] 첫 collaboration action 전에 `codex-team` skill 전체를 읽었는가?
- [ ] 모든 요청 child에 결과 계약을 전달하고 전원 결과를 취합했는가?
- [ ] nonterminal update를 running으로 유지했는가?
- [ ] dispatch identity mapping과 report invocation identity가 one-to-one인가?
- [ ] terminal delivery와 collected result가 요청 agent 전원과 일치하는가? 불일치하면 supported 판정을 거부했는가?
- [ ] unknown telemetry를 `null`로 보존했는가?
- [ ] completion serialization과 parent final이 마지막 terminal 뒤인가?
- [ ] capability error를 automatic Tier B/retry/interrupt/fallback으로 숨기지 않았는가?
