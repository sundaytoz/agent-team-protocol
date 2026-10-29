---
kind: adr
adr_number: "0026"
title: Codex team execution에서 hook marker gate와 atp-codex-hooks add-on을 제거하고 built-in subagent를 기본 경로로
status: accepted
date: 2026-10-29
deciders:
  - stzjungsoo
supersedes:
  - ADR-0025
---

# ADR-0026: Codex built-in subagent를 marker gate 없이 사용

## 상태

**Accepted** — 2026-10-29. ADR-0025(scope-gated hook-guarded bounded pool)를 supersede한다. ADR-0024의 execution mode·authority 경계는 유지한다.

## 맥락

ADR-0025는 Codex team execution을 옵트인 add-on `atp-codex-hooks`의 `SessionStart` hook이 넣는 exact `ATP_HOOK_GUARD_READY` marker에 gate했다. Marker가 없으면 child spawn 0으로 닫혀 `general_task`는 Tier B로 격하됐다. 실제 사용에서는 Codex 기본 subagent 기능만으로 child를 쓸 수 있는데도 add-on 설치·hook trust·Unix/`python3` 조건을 만족하지 못한 대부분의 세션이 subagent를 쓰지 못했다. Gate가 안전장치가 아니라 사용 차단 요인이 됐다. `codex-team` skill도 pool token(`ATP_POOL_BIND/RESULT/DENIED`), slot budget, hook ledger, 4축 qualification 표 등 hook 전용 제약으로 복잡해졌다.

## 결정

1. `codex-team` skill에서 marker gate와 hook 전용 절차를 제거한다. Codex에서는 항상 `host_managed_subagent_orchestration`으로 진행하며 `spawn_agent`로 dispatch하고 요청한 모든 결과를 검증·취합한다. skill에는 프로토콜 기본 계약만 둔다.
2. 배포 profile:

   ```yaml
   formal_adapter_enabled: false
   manual_wait_polling_supported: false
   host_managed_subagent_orchestration: supported
   team_execution_enabled: true
   execution_scope: codex_builtin_subagents
   ```

3. `atp-codex-hooks` add-on(`plugins/atp-codex-hooks/`), marketplace 등재, hook 회귀 테스트와 evidence 생성기를 삭제한다. `skip: no-codex-hooks` 경로와 host skill의 scope gate 서술을 task SKILL·platform-adapters에서 제거한다.
4. nonterminal은 `running`, 사용자 승인형 recovery 등 공통 lifecycle 계약은 그대로다.

## 결과

- Codex 소비자는 base `atp`만 설치해도 `$atp:task`에서 advisor/worker subagent를 사용한다.
- 알려진 한계: 2026-08-26 Codex CLI 0.149.1 격리 smoke에서 built-in barrier가 staggered 2-agent 중 결과 1건만 전달하고 parent turn을 끝낸 기록이 있다(`tests/runtime-behavior/evidence/codex-cli-0.149.1-20260826.json`). 이를 실행 gate로 쓰지 않는다. 결과 누락이 재현되면 별도 ADR로 다룬다. 2026-10-29 Codex CLI 0.165.0에서 2.19.0 설치본으로 2-agent 병렬 `$atp:task`를 실행해 2개 모두 완료·취합됐다(미재현).
- 기존에 add-on을 설치한 사용자는 `codex plugin remove atp-codex-hooks`로 제거할 수 있다.
- hook-guarded evidence JSON과 routing appendix §8 이력은 historical record로 보존한다.

## 관련

- [ADR-0024](./ADR-0024-host-managed-subagent-orchestration.md)
- [ADR-0025](./ADR-0025-codex-scope-gated-team-execution.md) (superseded)
- [codex-team skill](../../plugins/atp/skills/codex-team/SKILL.md)
- [Codex lifecycle routing appendix](../../plugins/atp/docs/development/codex-lifecycle-routing.md)
