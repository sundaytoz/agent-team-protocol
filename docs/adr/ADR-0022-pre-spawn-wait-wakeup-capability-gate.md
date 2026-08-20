---
kind: adr
id: ADR-0022
title: Codex wait/wakeup capability 판정을 advisor spawn 전 absolute preflight로 이동
status: accepted
date: 2026-08-18
deciders: [stzjungsoo]
relates_to: [ADR-0020, ADR-0021]
supersedes: []
---

# ADR-0022: pre-spawn wait/wakeup capability gate

## Context

ADR-0021과 ATP 2.13.0은 current Codex adapter가 formal wait/wakeup capability를 지원하지 않으면 timed wait나 polling으로 보충하지 않고 `wait_wakeup_capability_unavailable` 1회 뒤 blocked로 수렴하도록 정했다. 그러나 task 실행 순서가 capability gate보다 advisor spawn을 먼저 허용했다. 모델은 이미 생성된 child 결과를 회수해야 한다는 압력을 받았고, 실제 Codex CLI 0.147.0 세션에서 `spawn_agent` 1회 뒤 `wait_agent` 13회(그중 timeout 11회), `list_agents` 2회가 실행됐다.

관측 세션 직전 ATP source와 설치된 2.13.0 cache 전체는 byte parity였다. 따라서 stale cache가 아니라 gate ordering과 문자열 중심 정적 검증의 결함이다.

## Decision

### 1. Capability 판정은 첫 child spawn 전 absolute preflight다

Task skill은 init 존재 확인 직후, migration·report 초기화·advisor invocation identity·authority·write ownership 생성보다 먼저 적용 host의 required wait/wakeup capability를 판정한다. 모두 `supported`일 때만 child identity 생성과 spawn 계획으로 진행한다.

하나라도 `unsupported|unknown`이면 해당 세션에는 child를 만들지 않는다. Executed spawn, automatic wait, polling 목적 list, retry, interrupt와 fallback은 모두 0건이다. Child authority와 write ownership도 0건이고 제품·문서·외부 상태 mutation도 0건이다. 예외는 session-scoped preflight audit directory와 `wait-wakeup-events.jsonl` 한 파일뿐이다. Ledger owner는 `orchestrator-preflight:<sid>`이며 unavailable event는 정확히 한 번이다.

### 2. 사용자 intent를 보존한다

일반 `$atp:task` 요청은 capability 한계를 고지하고 사용자가 선택할 수 있는 Tier B 단일 에이전트 순차 수행을 제안한다. 선택 전에는 Tier B를 자동 실행하지 않는다.

사용자가 실제 subagent/advisor의 독립 의견을 명시적으로 요구했다면 child가 생성되지 않았다는 blocker와 `지원 host에서 재실행 | 독립성 없는 Tier B로 명시 전환 | 취소`를 제시한다. Tier B 결과를 subagent 의견으로 조용히 대체하지 않는다.

### 3. Post-spawn 보존 규칙은 동적 capability gap에만 적용한다

Preflight 당시 capability가 모두 supported였으나 spawn 뒤 host 오류로 새 scheduling gap이 생긴 경우에만 ADR-0021의 child state, result acceptance authority와 write ownership 보존 규칙을 적용한다. Disabled preflight 경로에는 보존할 child가 없다.

### 4. 행동 검증을 릴리스 gate에 추가한다

정적 fixture는 ordering, intent UX와 one-shot authoritative recovery list 허용을 검사한다. 별도 runtime validator는 실제 Codex JSONL에서 attempted/executed collaboration call을 구분하고, ledger exact-once, child artifact 부재, mutation scope와 source/설치본 parity를 검증한다. 2026-08-18 관측 JSONL의 기존 회귀 수치도 fixture가 아니라 실제 로그에서 재집계한다.

`list_agents`를 전면 금지하지 않는다. 기존 invocation이 있고 사용자가 승인한 recovery 또는 completion-race 확인에서만 단발 authoritative 조회를 허용한다. Unsupported preflight와 자동 polling 경로에서는 0건이다.

### 5. Codex hook은 이번 릴리스에 포함하지 않는다

Codex CLI 0.147.0을 격리한 container에서 plugin-bundled `UserPromptSubmit`과 `PreToolUse`를 black-box 측정했다. Plugin 배포와 ATP prompt scope 판정은 동작했지만 실제 `collaboration.spawn_agent`, `wait_agent`, `list_agents` 호출은 `PreToolUse`에 관측되지 않았다. 따라서 deny-before-mutation, ATP-only deny와 denial-loop 부재를 증명할 수 없다.

모든 조건이 GREEN일 때만 defense-in-depth hook을 추가한다는 기준에 따라 hook 구현을 제외한다. 사용자 전역 Codex hook 설정은 변경하지 않는다.

## Consequences

- Unsupported Codex에서 orphan child와 결과 회수 압력을 함께 제거한다.
- 일반 작업은 사용자가 Tier B로 전환할 수 있고, 독립 subagent 요구는 의미를 잃지 않은 채 blocker로 반환된다.
- Static contract와 실제 설치본/session 행동 사이의 회귀를 함께 검출한다.
- Hook 차단에 의존하지 않으므로 prompt contract가 primary control로 남는다. Host가 collaboration tool hook을 지원하면 격리 측정을 다시 수행할 수 있다.
- Timeout-free await 자체는 ATP가 구현할 수 없으며 Codex CLI upstream 과제로 남는다.

## Alternatives considered

- **Spawn 뒤 capability 판정 유지**: orphan child와 결과 회수 압력을 만들므로 기각했다.
- **Unsupported에서 Tier B 자동 대체**: 명시적 독립 의견 요구를 위장하고 사용자 선택을 생략하므로 기각했다.
- **`list_agents` 전면 금지**: 승인된 recovery의 completion race를 권위 있게 확인할 경로까지 없애므로 기각했다.
- **Hook hard gate 즉시 배포**: collaboration 도구가 `PreToolUse`에 관측되지 않아 실제 차단을 증명할 수 없으므로 기각했다.
- **Static string validator만 유지**: ATP 2.13.0 규약이 주입된 실제 세션의 회귀를 잡지 못했으므로 기각했다.

## References

- [ADR-0021](./ADR-0021-environment-owned-wait-wakeup-scheduling.md)
- [ADR-0023](./ADR-0023-host-native-cooperative-execution.md) — 이 결정의 zero-child/Tier B 부분을 후속 교정한 historical decision
- [ADR-0024](./ADR-0024-host-managed-subagent-orchestration.md) — 현행 host-managed orchestration 결정
- [Codex CLI collaboration await upstream proposal](../backlog/codex-cli-collaboration-await-v1.md)
- [Runtime behavior validator](../../tests/runtime-behavior/README.md)
- [Codex lifecycle appendix](../../plugins/atp/docs/development/codex-lifecycle-routing.md)
