---
name: codex-team
description: Codex에서 ATP가 subagent를 spawn, delegate, steer, collect하기 전에 사용하는 orchestration skill. Codex built-in subagent 기능으로 child를 dispatch하고, 결과 대기·follow-up routing은 Codex built-in workflow에 맡긴 뒤 요청한 모든 결과를 취합한다.
---

# Codex team orchestration

이 skill은 Codex host 전용이다. ATP가 한 명 이상의 subagent를 사용하려면 첫 collaboration action 전에 전체 `SKILL.md`를 읽는다. 공통 lifecycle·report authority는 `../../docs/development/agent-team-protocol.md`를 따르고, Codex 도구·event mapping은 `../../docs/development/codex-lifecycle-routing.md`를 참조한다. Runtime task가 scheduling 방법을 알아내기 위해 capability probe를 만들지 않는다.

## 1. 적용

- 별도 add-on, hook 설치·trust, 세션 marker 없이 Codex의 기본 subagent 기능을 그대로 사용한다.
- §4의 배포 profile을 적용해 `selected_mode: host_managed_subagent_orchestration`으로 진행한다.
- 사용자 전역 설정, 설치된 plugin cache와 소비 프로젝트 설정을 변경하지 않는다.

## 2. Dispatch와 결과 수집

1. Child마다 `report_invocation_id`를 spawn 전에 할당하고, spawn 결과의 environment identity(`agent_id` 또는 `task_name`)를 연결한다.
2. `spawn_agent`로 child task를 요청하고, child prompt에 반환할 결과 계약을 명시한다.
3. 결과 대기, follow-up routing과 진행 표시는 Codex 내장 기능이 하는 대로 둔다. `wait_agent`·`list_agents` 등 Codex 내장 도구 사용과 "Waiting for agents", "No agents completed yet" 같은 중간 표시는 ATP가 제한하거나 이상 신호로 보지 않는다.
4. 전달된 nonterminal update는 `running`이다. 명시적 terminal delivery만 결과로 검증·취합하고, 같은 child의 중복 terminal은 한 번만 소비한다.
5. 모든 요청 agent의 결과를 검증·취합하기 전에는 report/session completion, `ended_at`, 사용자 final을 만들지 않는다. Host가 concurrency limit 오류를 반환하면 그 task는 spawn되지 않은 것이며, 실행 중 child가 끝난 뒤 다시 dispatch한다.

## 3. Steering, approval과 recovery

- User steering은 실행 중인 child identity에 `send_message`/`followup_task`로 적용하며 새 logical task를 암묵적으로 추가하지 않는다.
- Approval-required는 해당 child와 write ownership을 유지한 채 사용자 결정으로 전달한다.
- 실제 failed/interrupted 뒤의 retry, interrupt, fallback, result-acceptance 또는 write-ownership 변경은 공통 lifecycle의 사용자 승인 계약을 따른다. Silence나 시간 경과로 상태를 합성하지 않는다.

## 4. 배포된 capability profile

현재 배포 판정은 다음과 같다(2026-10-29, ADR-0026).

```yaml
formal_adapter_enabled: false
manual_wait_polling_supported: false
host_managed_subagent_orchestration: supported
team_execution_enabled: true
execution_scope: codex_builtin_subagents
```

실행 중 이 profile을 임의로 올리거나 내리지 않는다. 검증 이력과 알려진 한계는 `codex-lifecycle-routing.md` §1·§8에서만 관리한다.
