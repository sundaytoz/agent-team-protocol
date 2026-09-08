---
kind: backlog
title: Codex CLI upstream issue draft — all-results barrier and collaboration await v1
status: proposal
date: 2026-08-18
owner: template-maintainer
last_reviewed: 2026-08-26
---

# Codex CLI upstream issue draft: all-results barrier and collaboration await v1

## Summary

Codex collaboration에 두 capability를 단계적으로 추가하는 제안이다. P0는 product-managed workflow가 요청된 모든 child의 terminal result를 전달하기 전 parent turn이나 final을 종료하지 않는 all-results barrier다. P1은 target-aware timeout-free `collaboration.await.v1`로 root-visible timeout과 수동 polling 없이 명시적 scheduling을 제공하는 후속 제안이다.

P0 통과에 P1 전체 구현은 필요하지 않다. Host가 기존 built-in workflow 내부에서 root를 suspend하고 모든 terminal result 뒤 자동 재개해도 P0를 충족한다.

## Latest reproduction

- Codex CLI: 0.149.1
- Candidate ATP plugin: `2.16.0+codex.20260825102518`
- Terminal-only 1-agent: PASS
- Nonterminal `MESSAGE` → delayed terminal 1-agent: PASS
- Staggered terminal 2-agent with `fork_turns: "none"`: FAIL
- 실패 관측값: `requested_agents=2`, `spawn_calls=2`, `terminal_deliveries=1`; `collected_results`는 실패 run에 ledger가 생성되지 않아 `null`
- Ordering: 두 child를 spawn한 뒤 fast child terminal만 전달됐고, slow child terminal 없이 parent turn이 종료됨
- Caller actions: manual wait/list/interrupt/recovery 0

최소 child context에서도 실패했으므로 full conversation fork 크기는 all-results barrier 실패의 설명이 아니다. Terminal-only 1-agent와 nonterminal-to-terminal 1-agent가 통과한 사실은 single-child lifecycle delivery가 동작함을 보이지만, multi-child all-results contract를 충족시키지 않는다.

Historical context: Codex CLI 0.147.0에서는 terminal-only 1-agent만 통과했고 nonterminal 뒤 delayed terminal 1-agent와 staggered 2-agent가 실패했다. 0.149.1은 single-agent nonterminal case를 개선했지만 필수 multi-agent barrier는 여전히 실패한다.

### Supplemental topology and capacity facts

같은 0.149.1 격리 환경에서 별도 topology/capacity probe를 수행했다. 이 probe는 고정 지연으로 thread를 열린 상태로 유지했으므로 P0 all-results barrier 합격 근거가 아니라 scheduler 설계 입력이다.

- `root → child → grandchild` 실제 nested spawn과 세 terminal result가 확인됐다.
- 한 child가 short-lived grandchild를 누적 5개까지 생성했다. 누적 생성 상한은 확인하지 않았다.
- Root와 fan-out child가 살아 있는 saturated probe에서는 grandchild 2개가 승인되고 이후 3개가 모두 `collab spawn failed: agent thread limit reached`로 거절됐다.
- 관측된 limit 시점의 활성 구성은 primary root + child + grandchild 2개, 총 4 threads였다.
- 깊이 체인은 root 아래 descendant 3단계까지 승인됐고 4단계 spawn은 같은 thread-limit 오류로 거절됐다. 별도 nesting-depth limit가 아니라 concurrent thread limit의 결과로 해석한다.
- `agents.max_concurrent_threads_per_session`은 격리 설정에서 unset이었다. 공식 문서상 이 값은 primary를 제외한 concurrently open spawned-agent thread cap이며, unset이면 Codex가 default를 선택한다.
- Capacity probe 내부의 manual `wait_agent`/`list_agents`/`interrupt_agent`는 0이었다. 고정 지연 harness는 결과 barrier를 보상하지 않고 active-thread overlap만 만들었다.

따라서 ATP 후속 후보는 한 번에 전체 DAG를 spawn하지 않는다. Pending queue와 bounded running set을 유지하고, capacity가 차면 terminal event를 기다린 뒤 해제된 slot에 다음 task를 넣는 pool scheduler로 검증한다. 이 후보는 P0 upstream 요구를 철회하거나 현재 deployed profile을 supported로 바꾸는 근거가 아니다.

Source skill candidate의 terminal-only queue baseline은 통과했다. Root-owned width-3 pool은 logical task 5개를 spawn/terminal/collected 5/5로 마쳤고 pool wait 2회, list/interrupt 0회였다. Nested owner smoke도 `root → pool-owner → workers` 구조에서 worker width 2를 유지하며 worker 5개를 전부 순환 처리했고 root wait 1회, owner wait 4회, list/interrupt 0회였다. 별도 capacity-denial smoke는 logical task 5개에 spawn attempt 6, accepted 5, denial 1, terminal/collected 5/5를 기록했고, 거절된 task가 terminal 뒤 새 environment identity로 refill됐다.

그러나 후속 release qualification은 실패했다. 최초 nonterminal run은 saturation 조건을 충족하지 않아 판정에서 제외했고, saturated rerun은 running 3/pending 2에서 `MESSAGE`만으로 slot release/refill을 하지 않고 같은 child의 terminal까지 받았지만 전체 barrier를 완성하지 못했다. Requested 5 중 spawn attempt/accepted 3/3, terminal delivery 3(초기 child 한 건의 explicit failure 포함), collected 1, pool wait 2였고 두 번째 wait가 반환하지 않아 parent final은 없었다. Active wait 중 steering queue는 한 번 accepted됐지만 scheduler turn에 전달되지 않아 send/follow-up 0, terminal/collected 4/4, wait 5에서 parent final 없이 중단됐다. Interactive approval overlay는 running child를 식별해 실제 relay됐지만 한 번의 reject 뒤 target이 `turn_aborted`로 끝나 같은 identity continuation과 terminal delivery가 없었다. Cancellation queue도 running 3/pending 2에서 accepted됐으나 active wait에 전달되지 않았고, scheduler는 뒤이어 pending 두 task를 spawn했다. 결과는 accepted 5, terminal/collected 4/4, wait 4, interrupt 0, parent final 0이었다. 외부 smoke 정리는 scheduler cancellation 증거로 세지 않는다.

Candidate source/install byte parity와 설치본 flat/nested/denial-refill 최소 회귀는 독립적으로 통과했다. Source와 installed `codex-team/SKILL.md` SHA-256는 `bcfbdd0f0f7d066233155faebdec9aadb78de73fc2bfa057b3c7aec740eee146`로 같았다. 이 부분 성공은 nonterminal barrier, steering, approval continuation, cancellation 실패를 상쇄하지 않는다. 따라서 정식 bounded-pool execution mode 통합, capability 축 추가, profile 승격과 release는 수행하지 않았고 upstream P0도 계속 open이다. Sanitized count, ordering과 artifact hash는 [0.149.1 evidence manifest](../../tests/runtime-behavior/evidence/codex-cli-0.149.1-20260826.json)에 보존한다.

다음 qualification은 (1) 이미 전달된 terminal 전부를 한 wake에서 소비하고 terminal 뒤에만 refill하는 saturated pool join, (2) active wait에 queued steering/cancellation을 실제 control delivery로 주입하는 host surface, (3) approval decision 뒤 같은 child identity를 재개해 terminalize하는 동작을 먼저 실증해야 한다. 공식 OpenAI 문서는 approval overlay와 queued control의 제품 동작을 설명하지만, ATP 지원 판정에는 이 empirical all-results/control-delivery 계약의 실제 PASS가 우선한다.

## P0: product-managed all-results barrier

Built-in subagent workflow는 요청된 모든 child가 terminal result를 전달할 때까지 parent turn과 final을 종료하지 않아야 한다. Nonterminal progress는 child를 `running`으로 유지하며 terminal delivery나 collected result로 세지 않는다.

이 요구는 [공식 OpenAI Subagents 문서](https://learn.chatgpt.com/docs/agent-configuration/subagents)가 설명하는 orchestration·결과 취합 동작을 ATP가 검증 가능한 release contract로 고정하려는 것이다.

- 요청된 child와 environment identity를 안정적으로 연결한다.
- `completed | failed | interrupted` terminal과 nonterminal `MESSAGE`를 구분한다.
- 빠른 child 하나의 terminal만으로 multi-child barrier를 열지 않는다.
- ATP caller의 wait/list polling 없이 host가 root를 suspend하고 자동 재개한다.
- User steering, approval와 cancellation은 barrier 대기 중에도 전달한다.
- `requested_agents == spawn_calls == terminal_deliveries == collected_results`를 보장한다.

### P0 acceptance criteria

- Terminal-only 1-agent, nonterminal 뒤 delayed terminal 1-agent, staggered terminal 2-agent가 모두 parent 조기 종료 없이 통과한다.
- `requested_agents == spawn_calls == terminal_deliveries == collected_results`다.
- Nonterminal update 뒤에도 invocation은 `running`이고 terminal result가 별도로 전달된다.
- 정상 경로의 caller manual wait/list/interrupt/recovery action은 0이다.
- User steering, approval와 cancellation은 barrier 때문에 유실되거나 무기한 지연되지 않는다.

## Copy/paste upstream issue body

Suggested title: `Codex CLI 0.149.1 ends the parent turn after only one of two staggered subagent results`

````markdown
### Environment

- Codex CLI: 0.149.1
- Candidate plugin: ATP `2.16.0+codex.20260825102518`
- Isolated temporary Codex home and git workspace
- Built-in subagent workflow; no caller `wait`, `list`, `interrupt`, or recovery calls

### Summary

The built-in subagent workflow does not consistently keep the parent turn alive until every requested child has delivered a terminal result.

Two one-agent controls pass on 0.149.1:

1. terminal-only child: pass
2. nonterminal `MESSAGE`, then delayed terminal result: pass

The required staggered two-agent case fails. The parent receives the fast child's terminal result and then ends before the slow child's terminal result is delivered. Using `fork_turns: "none"` for minimal child context does not change the failure.

Observed failing counts:

```text
requested_agents=2
spawn_calls=2
terminal_deliveries=1
collected_results=unknown (the run ended before a measurement ledger was produced)
manual_wait_calls=0
list_calls=0
interrupt_calls=0
semantic_recovery_actions=0
```

Observed order:

```text
spawn fast child
spawn slow child
fast child terminal delivered
parent turn completed
slow child terminal not delivered
```

### Minimal reproduction

1. Start Codex CLI 0.149.1 with subagents enabled.
2. Ask the parent to spawn two independent children with `fork_turns: "none"`.
3. Have the first child return a terminal result quickly and the second return later.
4. Tell the parent to use the built-in all-results workflow, make no explicit wait/list/interrupt/recovery calls, and finish only after both terminal results are received.
5. Observe that both spawn calls execute, but only the fast terminal result is delivered before the parent turn completes.

Control cases:

- A terminal-only one-agent run delivers 1/1 terminal result and passes.
- A one-agent run with a nonterminal `MESSAGE` followed by a delayed terminal result keeps the child running, later delivers the terminal result, and passes.

### Expected behavior (P0)

- The parent turn/final cannot complete until every requested child has delivered a terminal result.
- A nonterminal `MESSAGE` keeps that child running.
- One fast child's terminal result does not open a multi-child barrier.
- The host suspends the root and resumes it automatically; callers such as ATP do not need wait/list polling.
- User steering, approval, and cancellation remain deliverable while the barrier is pending.
- On a normal successful run:

```text
requested_agents == spawn_calls == terminal_deliveries == collected_results
```

### Actual behavior

In the staggered two-agent run:

```text
requested_agents=2
spawn_calls=2
terminal_deliveries=1
```

The fast child result is delivered, the slow child result is not delivered, and the parent turn ends. This is an all-results barrier failure, not a request for callers to add polling.

### Evidence and privacy

A sanitized evidence manifest contains only versions, observed counts/order, and SHA-256 hashes of the preserved local artifacts. It excludes authentication data, user conversation text, local usernames, absolute paths, and raw JSONL transcripts.

Repository evidence: `tests/runtime-behavior/evidence/codex-cli-0.149.1-20260826.json`

### Priority split

P0 is the product-managed all-results barrier above. It can be fixed without implementing a new public await API.

A target-aware, timeout-free `collaboration.await.v1` API would be useful as a separate P1 follow-up for explicit scheduling, stable event identity, cancellation, and compact changed-invocation deltas. P1 is not a prerequisite for accepting or fixing this P0 issue.
````

## P1 follow-up: `collaboration.await.v1`

P0가 안정된 뒤 timeout 인자가 없는 명시적 API를 별도 제안한다.

```json
{
  "targets": ["environment-invocation-id-a", "environment-invocation-id-b"],
  "condition": "any | all",
  "wake_on": [
    "completed",
    "failed",
    "interrupted",
    "approval_required",
    "user_steering"
  ]
}
```

필수 semantics:

- 등록 시점의 atomic snapshot + subscription으로 check/subscribe race를 없앤다.
- 각 await는 stable await identity를 가지며 명시적으로 cancel할 수 있다.
- 각 lifecycle event와 snapshot revision은 stable identity를 가져 duplicate delivery를 idempotently consume할 수 있다.
- 반환은 changed invocation만 담은 compact delta와 상세 result reference를 우선한다. 전체 agent snapshot을 반복 복제하지 않는다.
- `condition: any|all`을 target 집합에 대해 host가 평가한다.
- 인접 completion은 compact batch로 coalesce하되 approval, steering과 cancellation을 지연하지 않는다.
- Timed fallback이나 root-visible keepalive는 제공하지 않는다.

### P1 acceptance criteria

- Subscribe 직전 완료와 subscribe 직후 완료가 유실·중복 없이 한 번 소비된다.
- `any`는 첫 관심 사건에, `all`은 모든 target barrier 충족 또는 단락 event에 wake한다.
- 같은 event/revision 재전달은 semantic action을 한 번만 만든다.
- Cancellation은 await identity에 결합되고 stale completion이 취소된 await를 재개하지 않는다.
- Payload는 changed-only delta와 result refs이며 unchanged target 전체를 반복하지 않는다.

## P2: durable exactly-once event plane은 보류

CLI 재시작 뒤 await 복구나 원격 resume가 실제 요구사항으로 증명되기 전에는 durable exactly-once event plane을 만들지 않는다. P1의 process-lifetime stable identity, atomic subscription과 idempotent consumption으로 먼저 충분성을 검증한다. 재시작·원격 resume 요구가 생기면 persisted cursor, lease와 replay/ack protocol을 별도 설계한다.

## Non-goals

- ATP가 timeout 값을 조정하거나 polling loop를 제공하는 것
- Progress/heartbeat 부재를 lifecycle failure로 해석하는 것
- P0 통과에 P1 전체 구현을 요구하는 것
- 모든 tool call을 durable message bus로 바꾸는 것
- P1 전에 cross-process exactly-once를 약속하는 것

## Related ATP evidence

- [ATP hook-guarded bounded-pool qualification handoff](./codex-cli-hook-guarded-bounded-pool.md)
- [Known Issues](../usage/known-issues.md)
- [Official OpenAI Subagents documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents)
- [ADR-0024 host-managed subagent orchestration](../adr/ADR-0024-host-managed-subagent-orchestration.md)
- [ADR-0023 historical host-native cooperative execution](../adr/ADR-0023-host-native-cooperative-execution.md)
- [ADR-0021 environment-owned wait/wakeup scheduling](../adr/ADR-0021-environment-owned-wait-wakeup-scheduling.md)
- [2.15.0 change](../changes/2026-08-19-codex-managed-subagent-orchestration.md)
- [Codex CLI 0.149.1 sanitized evidence manifest](../../tests/runtime-behavior/evidence/codex-cli-0.149.1-20260826.json)
- [Codex CLI 0.147.0 historical evidence manifest](../../tests/runtime-behavior/evidence/codex-cli-0.147.0-20260819.json)
