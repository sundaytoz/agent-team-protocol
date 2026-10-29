---
kind: changes
title: 2.14.0 — Adaptive execution mode와 Codex native cooperative team
date: 2026-08-18
version: 2.14.0
status: implemented-l1-verified
owner: template-maintainer
---

# 2.14.0 — Adaptive execution mode

## 요약

ATP는 첫 advisor spawn 전에 formal scheduling과 host-native team execution을 별도 축으로 판정한다. Current Codex formal wait/wakeup adapter는 계속 unsupported지만 `spawn_agent`와 mailbox `wait_agent`를 native cooperative join으로 사용해 실제 advisor/worker 팀 실행을 유지한다.

Formal/native join이 모두 없는 일반 host만 Tier B 순차 self-check로 투명하게 자동 격하한다. 사용자가 실제 독립 subagent 의견을 요구했는데 child 실행이 불가능한 경우에만 blocker와 선택지를 반환한다. 다른 host의 `environment_subscription`, Tier A-flat과 Tier B phase 척추는 변경하지 않는다.

## 원인 재확인

관측 세션에는 ATP 2.13.0과 no-polling 규약이 실제 주입됐지만 짧은 bounded wait와 상태 조회가 반복됐다. 실제 JSONL 재집계 결과는 `spawn_agent` 1, `wait_agent` 13, `list_agents` 2, wait timeout 11이다. 당시 source와 설치 cache 전체 parity도 확인돼 stale cache를 원인에서 제외했다.

초기 2.14.0 설계는 이를 막기 위해 formal capability 12개 전체를 spawn gate로 승격했지만, scheduling 효율과 team correctness를 결합해 Codex의 실제 spawn/result-collection 기능까지 비활성화했다. ADR-0023이 이 결합을 교정한다.

## 구현

- Task skill은 `environment_subscription | host_native_cooperative | tier_b_sequential | blocked_explicit_independence`를 첫 advisor spawn 전에 협상한다.
- Formal capability 12개는 `environment_subscription`의 all-required gate로만 유지한다.
- Codex appendix는 `formal_adapter_enabled: false`, `native_join_supported: true`, `team_execution_enabled: true`를 선언한다.
- Native bounded wait의 timeout은 lifecycle no-op이며 가장 긴 실용 wait를 우선한다. Timeout 뒤 polling list, synthetic terminal, automatic retry/interrupt/fallback과 authority mutation은 0건이다.
- Research/implementation advisor의 nested worker join도 같은 negotiated mode를 사용한다.
- Lifecycle fixture는 formal mode, Codex native mode, general 자동 Tier B, explicit independence blocker와 non-Codex Tier A-flat 불변을 각각 고정한다.
- Runtime validator는 실제/synthetic Codex JSONL의 `MESSAGE`와 `FINAL_ANSWER`를 별도 lifecycle 사건으로 읽고, nonterminal update 뒤 native rejoin, polling list 0, exact ledger envelope·measurement·appendix capability parity와 report/mutation 종료 순서를 검사한다.

## Hook black-box 결과

Codex CLI 0.147.0 container, 별도 Codex home, read-only auth와 throwaway plugin으로 측정했다. Plugin-bundled `UserPromptSubmit`은 ATP prompt를 관측했고 사용자 전역 `~/.codex/hooks.json` 변경 없이 배포됐다. 그러나 실제 `collaboration.spawn_agent`, `wait_agent`, `list_agents` 호출은 `PreToolUse`에 들어오지 않았다.

따라서 deny-before-state-change와 deny 후 반복 호출 부재를 검증할 수 없어 hook은 구현에서 제외했다. 이 릴리스는 사용자 전역 Codex 설정을 수정하지 않는다.

## 검증 상태

- Historical runtime JSONL 재집계 보존: spawn 1, wait 13, list 2, timeout 11.
- Lifecycle static validator: `PASS: environment-authoritative lifecycle contract and compatibility fixtures`.
- Checked-in native cooperative runtime fixture: `MESSAGE → running → rejoin → FINAL_ANSWER → completed`, spawn 1, wait 2, list 0, interrupt 0, timeout/semantic recovery 0.
- Fresh installed Codex end-to-end smoke와 source/cache parity는 release 전 사용자 환경에서 확인한다.

## 관련 문서

- [ADR-0022](../adr/ADR-0022-pre-spawn-wait-wakeup-capability-gate.md)
- [ADR-0023](../adr/ADR-0023-host-native-cooperative-execution.md)
- [Codex CLI upstream proposal](../backlog/codex-cli-collaboration-await-v1.md)
- [Runtime behavior validator](../../tests/runtime-behavior/README.md)
- [Release checklist §10](../development/release-checklist.md#10-environment-authoritative-subagent-lifecycle-계약)
