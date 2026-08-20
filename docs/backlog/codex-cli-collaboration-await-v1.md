---
kind: backlog
title: Codex CLI upstream issue draft — collaboration await v1
status: proposal
date: 2026-08-18
owner: template-maintainer
last_reviewed: 2026-08-20
---

# Codex CLI upstream issue draft: timeout-free collaboration await

## Summary

Codex collaboration에 두 capability를 단계적으로 추가하는 제안이다. P0는 product-managed workflow가 요청된 모든 child의 terminal result를 전달하기 전 parent를 종료하지 않는 all-results barrier다. P1은 target-aware timeout-free `collaboration.await.v1`로 root-visible timeout과 수동 polling 없이 명시적 scheduling을 제공한다.

## Reproduction

- Codex CLI: 0.147.0
- ATP 2.13.0 historical session: `spawn_agent` 1, `wait_agent` 13, timeout 11, `list_agents` 2. Empty timeout은 lifecycle event가 아니지만 root model을 재개해 같은 판단을 반복시켰다.
- ATP 2.15.0 isolated maintainer smoke: terminal-only 1-agent는 통과했지만 nonterminal 뒤 delayed terminal 1-agent와 staggered 2-agent는 모든 terminal result 전에 parent가 종료됐다.
- ATP 2.15.0은 manual wait/list polling을 제거하고 tested CLI의 `host_managed_subagent_orchestration`을 `unsupported`, team execution을 disabled로 배포한다. 일반 요청은 Tier B, 독립 subagent 필수 요청은 blocker로 수렴한다.

## P0: product-managed all-results barrier 보장

Built-in subagent workflow는 요청된 모든 child가 terminal result를 전달할 때까지 parent final을 허용하지 않는다. Nonterminal progress는 child를 `running`으로 유지하며 terminal delivery나 collected result로 세지 않는다.

이 요구는 [공식 OpenAI Subagents 문서](https://learn.chatgpt.com/docs/agent-configuration/subagents)가 설명하는 orchestration·all-results 취합 동작을 ATP가 검증 가능한 release contract로 고정하려는 것이다.

- requested child와 environment identity를 안정적으로 연결한다.
- `completed | failed | interrupted` terminal과 `approval_required`, user steering/cancellation을 구분한다.
- Parent가 여러 child를 요청하면 빠른 child 하나의 terminal만으로 barrier를 열지 않는다.
- Connection loss나 capability error는 synthetic success/failure를 만들지 않고 마지막 권위 상태와 control을 보존한다.

ATP 같은 caller가 별도 wait/list polling을 추가하지 않아도 이 계약이 성립해야 한다.

### P0 acceptance criteria

- Terminal-only 1-agent, nonterminal 뒤 delayed terminal 1-agent, staggered terminal 2-agent가 모두 parent 조기 종료 없이 통과한다.
- `requested_agents == spawn_calls == terminal_deliveries == collected_results`다.
- Nonterminal update 뒤에도 invocation은 `running`이고 terminal result가 별도로 전달된다.
- 정상 경로의 caller manual wait/list/interrupt/recovery action은 0이다.
- User steering, approval와 cancellation은 barrier 때문에 유실되거나 무기한 지연되지 않는다.

## P1: `collaboration.await.v1`

Timeout 인자가 없는 명시적 API를 추가한다.

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
- 모든 tool call을 durable message bus로 바꾸는 것
- P1 전에 cross-process exactly-once를 약속하는 것

## Related ATP evidence

- [Known Issues](../usage/known-issues.md)
- [Official OpenAI Subagents documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents)
- [ADR-0024 host-managed subagent orchestration](../adr/ADR-0024-host-managed-subagent-orchestration.md)
- [ADR-0023 historical host-native cooperative execution](../adr/ADR-0023-host-native-cooperative-execution.md)
- [ADR-0021 environment-owned wait/wakeup scheduling](../adr/ADR-0021-environment-owned-wait-wakeup-scheduling.md)
- [2.15.0 change](../changes/2026-08-19-codex-managed-subagent-orchestration.md)
- [Sanitized Codex CLI evidence manifest](../../tests/runtime-behavior/evidence/codex-cli-0.147.0-20260819.json)
