---
kind: adr
id: ADR-0021
title: environment-owned wait/wakeup scheduling — timeout-free subscription과 strict capability-gap 수렴
status: accepted
date: 2026-08-13
deciders: [stzjungsoo]
relates_to: [ADR-0017, ADR-0020]
supersedes: []
---

# ADR-0021: environment-owned wait/wakeup scheduling

## Context

[ADR-0020](./ADR-0020-environment-authoritative-subagent-lifecycle.md)은 wait timeout, 경과 시간, progress/heartbeat 부재와 동일 `running` snapshot으로 lifecycle failure를 추론하지 않도록 고쳤다. 그러나 bounded wait가 timeout이나 mailbox update를 반환할 때마다 root model이 재개되고 큰 누적 context가 다시 입력되는 scheduling 비용은 남았다. Lifecycle correctness와 model wake-up 억제는 별개 문제다.

2026-08-12 root JSONL에서는 `wait_agent` 209회와 timeout 148회를 확인했다. Wait 결과 뒤 model usage의 event-order proxy는 input 34,471,967, cached input 34,161,408이었다. 별도 작은 timed-wait probe 두 번도 input 212,698, cached input 210,432를 다시 입력했다. Timeout 길이를 늘리면 재개 빈도만 바뀌며 “관심 있는 환경 상태 변화가 없으면 root model 호출도 0건”이라는 불변식을 보장하지 못한다.

ATP 2.12.0 source와 설치 cache의 지정 lifecycle/runtime 파일은 변경 전 byte-identical이었다. 둘 다 environment-authoritative lifecycle은 구현했지만 timeout-free suspension, selected-target wait-any/all, event ID, deduplication, coalescing, compact changed-invocation delta 계약은 없었다.

## Decision

### 1. Formal wait/wakeup은 timeout-free environment subscription 하나뿐이다

ATP의 논리 API는 다음 의미를 가진다.

```text
await_invocations({
  targets,
  condition: any | all,
  wake_on: [completed, failed, interrupted, approval_required, user_steering]
})
```

Environment는 persistent await identity를 만들고 관심 event 전까지 root model turn을 suspend한다. Unchanged `running`, keepalive, scheduler tick은 environment 내부 사건이며 root-visible timeout이나 model wake를 만들지 않는다. Formal mode에는 timeout 인자와 timed/long/repeated wait가 없다.

Environment가 소유하는 책임은 invocation identity와 실행 상태, terminal/approval event 관측, timeout-free wait와 wake scheduling, internal keepalive, event ID와 deduplication, completion coalescing, compact changed-invocation delta, user steering, await cancellation과 child cancellation 결과 전달이다.

ATP가 소유하는 책임은 logical task와 dependency/DAG, 관심 invocation과 `any|all` condition, result contract 검증·취합, approval relay 정책, 명시적 failure 뒤 사용자 승인형 retry/fallback 판단, completion race, retry identity, result acceptance authority, write ownership과 late completion 격리다.

### 2. Required capability는 all-or-nothing gate다

Adapter는 timeout-free suspend, targeted wait-any/all, terminal/approval subscription, steering preemption, await cancellation, compact delta, stable event identity, native deduplication, completion coalescing과 internal keepalive no-model-wake를 각각 `supported|unsupported|unknown`으로 판정한다.

모두 `supported`일 때만 `environment_subscription`을 등록한다. 하나라도 `unsupported|unknown`이면 ATP는 부분 capability, bounded wait, 긴 timeout, 반복 wait 또는 status polling을 조합해 formal 기능을 합성하지 않는다.

### 3. Capability gap은 정확히 한 번, 자동 동작 0건으로 수렴한다

Formal gate가 실패하면 호출 주체는 phase-local `wait-wakeup-events.jsonl`에 `wait_wakeup_capability_unavailable`을 정확히 한 번 기록한다. Automatic wait, list/status query, retry, interrupt와 phase fallback은 각각 0건이다.

Scheduling capability gap은 lifecycle failure, stall, interruption 또는 `environment_state_unknown`이 아니다. Status API unavailable/error가 실제 관측되지 않은 한 child의 마지막 environment-authoritative state를 보존한다. Result acceptance authority와 write ownership도 철회하거나 handoff하지 않는다. 따라서 scheduling gap 자체는 `lifecycle_fallback_reason` producer가 아니다.

Phase는 blocked narrative/Open Item으로 control을 반환한다. 유일한 대안은 사용자가 명시적으로 선택한 event-only external continuation이다. 이 continuation은 non-empty identity, 관심 environment event에서만 새 active turn을 여는 wake contract와 별도 cancellation contract가 모두 있어야 한다. Timer/polling continuation은 허용하지 않는다.

### 4. Wake payload는 compact delta이고 environment가 중복과 batch를 책임진다

Environment 반환에는 persistent `await_id`, 한 번의 resume를 식별하는 `batch_id`, `wake_reason`, changed invocation만 담은 `deltas[]`, optional control delta가 있어야 한다. 각 invocation delta는 stable `event_id`, `environment_invocation_id`, normalized state와 concrete provenance를 가진다.

같은 event ID는 정확히 한 batch에만 들어간다. Resume dispatch 전에 도착한 여러 completion은 하나의 compact batch로 coalesce한다. Approval, steering과 cancellation은 coalescing 때문에 지연하지 않는다. ATP는 전체 agent snapshot을 root context에 복제하지 않고 상세 result를 artifact/ref로 분리한다.

### 5. 기존 lifecycle·authority·report 계약을 보존한다

명시적 `failed|interrupted` event만 기존 사용자 승인형 recovery를 연다. Retry 직전 completion race, 새 invocation identity, read-only result acceptance revocation, write termination/isolation과 ownership 회수, late completion quarantine 및 late disk write dependency pause 규칙은 그대로다.

Scheduling event는 별도 phase-local ledger에 둔다. Report는 `schema_version: 2`를 유지하고 optional lifecycle field도 `attempt`, `termination`, `retry_of`, `lifecycle_fallback_reason` 네 개뿐이다.

## Current Codex host disposition

현재 정상 collaboration API는 최대 1시간 bounded global mailbox wait와 final-status/user-steering 조기 반환 일부를 제공한다. 그러나 timeout-free await identity, selected-target wait-any/all, internal rewait, await cancellation handle, stable event ID, compact delta, native deduplication과 scheduler 등록을 지원하지 않으며 approval/failure detail과 coalescing은 공개 계약상 unknown이다.

따라서 current Codex adapter는 `adapter_enabled: false`다. ATP 2.13.0은 `wait_agent`에 더 긴 timeout을 주거나 반복 호출하지 않는다. `wait_wakeup_capability_unavailable` 1회 뒤 blocked로 수렴하며, 현재 정상 API에는 formal event-only external continuation도 없다. 이는 host gap을 ATP 구현으로 위장하지 않는 의도된 결과다.

## Consequences

- 관심 event가 없는 동안 root model invocation을 만들지 않는 계약이 명확해진다.
- Partial host support를 polling으로 보상하지 않아 token 폭증과 상태 조회 관성을 막는다.
- Current Codex에서는 자동 subagent completion까지 진행하지 못하고 phase가 blocked될 수 있다. 이는 end-to-end event-driven 지원이 생기기 전의 명시적 capability boundary다.
- Child state와 effect authority가 보존되므로 뒤늦은 정상 completion을 거짓 late completion으로 격리하지 않는다.
- Report reader migration 없이 scheduling 측정과 감사를 별도 ledger에서 확장할 수 있다.
- Host는 subscription/dedup/coalescing/delta/steering/cancel을 구현해야 하고, ATP는 target/barrier/result/recovery/DAG 정책에 집중한다.

## Alternatives considered

- **가장 긴 bounded wait**: timeout 빈도만 낮추며 언젠가 root를 깨우고 target/event identity 계약을 제공하지 않아 기각했다.
- **유한 polling fallback**: 무한 반복은 막지만 관심 event 없는 model wake를 허용해 목표 불변식을 위반하므로 기각했다.
- **Timeout 뒤 자동 `list_agents`**: unchanged snapshot에 새 semantic 판단을 유도하고 lifecycle/scheduling 책임을 섞으므로 기각했다.
- **Scheduling gap을 failure/unknown으로 전환**: host capability 부족을 child 상태로 오인하고 authority 회수나 중복 실행을 열 수 있어 기각했다.
- **Report schema v3**: scheduling metadata를 invocation lifecycle row에 섞을 이유가 없고 v2 reader compatibility를 불필요하게 깨므로 기각했다.

## Implementation and verification status

Runtime protocol, platform adapter, Codex appendix, task skill, research/implementation advisor, deterministic fixture, validator와 base 2.13.0 manifest 변경은 worktree에 구현됐다. Current Codex formal adapter는 의도적으로 disabled다.

2026-08-13 독립 verification-advisor가 lifecycle+scheduling validator를 실행해 exit 0과 `PASS: environment-authoritative lifecycle contract and compatibility fixtures`를 확인했다. Report schema v2 legacy/current compatibility, JSON/diff/relative links/index/§N/catalog/manifest, active runtime no-timeout와 Codex gap scan도 PASS했다. L2는 외부 의존이 없어 skipped다.

검증을 위해 runtime timed-wait probe를 실행하지 않았다. Current Codex formal adapter가 unsupported/disabled이고 timed wait probe가 금지되므로 deterministic fixture와 정적 capability 계약이 권위 검증 경로다. 따라서 ADR 결정의 구현은 verified지만 current Codex end-to-end environment-driven wake는 계속 unsupported이며 향후 host capability 구현이 필요하다.

Final source-spec dry-run은 네 execution-spec gap을 먼저 검출했다. Current Codex의 `requested_mode`/`effective_mode` 분리(C1), research scheduling ledger Write/Edit allowlist(C2), 두 advisor의 별도 `wait_wakeup_ledger`와 닫힌 `wait_wakeup_disposition` 반환(C3), orchestrator가 spawn 전에 할당·주입하는 advisor `report_invocation_id`와 scheduling owner identity(C4)를 보정했다. 수정 후 dry-run은 C1~C4, current-host unavailable/blocked trace, hypothetical all-supported subscription trace와 기존 authority/race/late-completion 안전 계약을 모두 PASS했다. 이는 source-spec simulation이며 runtime host support 증거가 아니다.

## References

- [환경 권위 lifecycle과 wait/wakeup architecture](../architecture/environment-authoritative-subagent-lifecycle-design.md)
- [2.13.0 environment-driven wakeup change](../changes/2026-08-13-environment-driven-subagent-wakeup.md)
- [ADR-0020](./ADR-0020-environment-authoritative-subagent-lifecycle.md)
- [`agent-team-protocol.md` §2.5](../../plugins/atp/docs/development/agent-team-protocol.md)
- [platform adapter contract](../../plugins/atp/docs/development/platform-adapters.md)
- [Codex lifecycle/wait-wakeup appendix](../../plugins/atp/docs/development/codex-lifecycle-routing.md)
