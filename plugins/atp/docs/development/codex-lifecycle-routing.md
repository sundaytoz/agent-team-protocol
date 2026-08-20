---
kind: development
title: Codex managed subagent orchestration and lifecycle routing appendix
description: ATP의 host-neutral lifecycle과 result barrier를 Codex built-in managed subagent workflow에 매핑하는 조건부 appendix.
owner: template-maintainer
stability: draft
host_scope: codex
last_reviewed: 2026-08-19
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

공식 문서는 low-level event schema, failure/approval taxonomy, latency SLA, stable event identity를 보장하지 않는다. 2026-08-19 Codex CLI 0.147.0 격리 smoke는 terminal-only 1-agent만 통과했고, nonterminal 뒤 delayed terminal과 staggered 2-agent에서는 parent turn이 모든 terminal 전 종료됐다. `multi_agent_v2` opt-in도 delayed case를 보장하지 못했다. 따라서 tested CLI profile은 `unsupported`, app/IDE empirical status는 `unknown`이다. 공식 보장과 empirical 관측을 서로 대체하지 않는다.

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

2026-08-19 isolated Codex CLI 0.147.0 결과:

| smoke | product/result | 판정 |
|---|---|---|
| terminal-only 1-agent | spawn 1, terminal/collected 1, manual wait/list/interrupt 0, terminal 뒤 completion/final | pass |
| nonterminal 뒤 delayed terminal 1-agent | progress 뒤 parent가 terminal 전 final; child turn aborted. `multi_agent_v2` opt-in도 terminal 전 종료 | fail |
| staggered terminal 2-agent | spawn 2 뒤 fast terminal만 받은 상태에서 parent가 terminal 전 blocked final; slow child 미수집 | fail |

따라서 deterministic fixture는 모두 green이어도 deployed CLI profile은 `unsupported`, `team_execution_enabled: false`다. App/IDE는 같은 smoke 미수행으로 `unknown`이다. 보존 transcript와 hash는 `tests/runtime-behavior/evidence/codex-cli-0.147.0-20260819.json`에 기록한다.

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
