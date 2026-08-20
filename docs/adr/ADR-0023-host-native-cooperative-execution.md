---
kind: adr
adr_number: "0023"
title: Formal scheduling과 team execution 분리 — host-native cooperative mode
status: accepted
date: 2026-08-18
deciders:
  - template-maintainer
  - stzjungsoo
supersedes:
  - ADR-0022 decisions 1-3 (partial)
  - ADR-0021 capability-gap blocked convergence (partial)
---

# ADR-0023: host-native cooperative execution

## 상태

**Accepted** — 2026-08-18. ADR-0021의 formal `environment_subscription` 계약과 ADR-0022의 pre-spawn 판정 필요성은 유지하되, formal wait/wakeup capability 부족을 child spawn 금지와 동일시한 결정을 부분 supersede한다.

## 맥락

ATP 2.14.0 초안은 timeout-free suspend, targeted any/all, stable event identity, deduplication, completion coalescing과 compact delta 등 formal scheduling capability 12개를 첫 child spawn의 all-required gate로 사용했다. Current Codex는 이 최적화 계약을 전부 제공하지 않으므로 실제로 제공하는 child spawn, stable invocation identity, mailbox wait, final-result delivery와 user steering까지 사용하지 못했다. 일반 작업도 audit ledger만 만든 뒤 Tier B 전환 허락을 기다렸다.

이 결합은 두 문제를 섞었다.

1. **Team correctness**: child를 만들고 결과·terminal event를 회수하며 lifecycle authority와 write ownership을 지킬 수 있는가.
2. **Scheduling efficiency**: 관심 event 전 root를 깨우지 않고 deduplicate/coalesce된 compact delta로 재개할 수 있는가.

ADR-0009의 플랫폼 중립 원칙은 ATP가 특정 도구의 완전한 복제를 요구하는 대신 phase 척추·게이트·report·검증을 보존하고, 각 host가 자기 capability로 실행하도록 한다. Formal scheduling의 부재만으로 team correctness까지 비활성화하면 이 원칙과 충돌한다.

## 결정

### 1. Formal adapter와 team execution을 직교 축으로 분리한다

Formal capability 12개는 `environment_subscription`의 all-required gate로만 유지한다. 하나라도 `unsupported | unknown`이면 `formal_adapter_enabled: false`지만 곧바로 `spawn_allowed: false`가 되지 않는다.

Host가 stable invocation identity, final result 또는 terminal notification을 회수하는 native join, wait 중 user steering/control 보존을 제공하면 `native_join_supported: true`다. 이 경우 `selected_mode: host_native_cooperative`로 team topology를 유지한다.

### 2. Execution mode는 닫힌 네 값으로 협상한다

우선순위는 다음과 같다.

1. `environment_subscription`: formal capability 12개가 모두 supported.
2. `host_native_cooperative`: formal adapter는 불완전하지만 safe native join이 supported.
3. `tier_b_sequential`: 두 join이 모두 불가인 일반 작업. 사용자 선택을 기다리지 않고 투명하게 자동 격하.
4. `blocked_explicit_independence`: 두 join이 모두 불가이며 실제 독립 child가 산출 요구사항. 지원 host, 명시적 Tier B 전환 또는 취소를 요청.

Topology의 Tier A/A-flat/B 판정은 scheduling mode와 독립이다. 재귀 spawn이 불가능한 host의 Tier A-flat과 formal subscription을 이미 제공하는 host의 기존 동작은 변경하지 않는다.

### 3. Codex는 native cooperative join을 사용한다

Codex appendix는 formal adapter를 계속 unsupported로 정직하게 기록한다. 동시에 child spawn identity와 mailbox wait/final notification/user steering을 native join 근거로 기록하고 team execution을 활성화한다.

Bounded mailbox wait의 시간 경계 반환은 lifecycle event, failure, stall, retry 또는 fallback 근거가 아니다. 가장 긴 실용 wait를 우선하고 terminal 결과가 없으면 같은 native join을 다시 걸 수 있다. Timeout 뒤 상태 열거 polling, synthetic terminal, automatic retry/interrupt/fallback과 authority·ownership mutation은 0건이다. 각 실제 wait·timeout·root resume는 measurement로 기록한다.

### 4. 기존 안전 불변식은 유지한다

Environment-authoritative lifecycle, approval relay, result acceptance isolation, write ownership, destructive action gate, user-approved recovery, independent retry identity, late completion quarantine와 mandatory verification은 변경하지 않는다.

Formal/native join이 runtime에서 모두 unavailable이 되면 기존 child state·authority·ownership을 보존하고 추가 spawn·automatic recovery 0건으로 blocked 반환한다. Status API 오류가 별도로 관측되지 않았다면 `environment_state_unknown`을 합성하지 않는다.

## 다른 플랫폼 영향 경계

- Formal capability 12개를 모두 지원하는 host는 기존 `environment_subscription` 경로를 그대로 사용한다.
- 재귀 spawn만 제한된 host는 기존 Tier A-flat topology를 그대로 사용한다.
- Spawn 자체가 불가능한 일반 host는 기존 Tier B phase 척추를 사용하되 사용자 확인 없이 투명하게 자동 진입한다.
- Codex tool 이름과 bounded wait 의미는 Codex appendix에만 둔다. 공통 protocol·task·agent 문서는 `host_native_cooperative`라는 논리 mode만 사용한다.
- Report schema v2와 scheduling event vocabulary 여섯 개는 변경하지 않는다.

## 기각한 대안

- **Formal capability 12개를 계속 spawn gate로 사용**: scheduling 효율과 team correctness를 결합해 host의 실제 기능을 버리므로 기각.
- **Codex를 항상 Tier B로 자동 격하**: 동작은 하지만 실제 subagent 독립성과 병렬성을 불필요하게 포기하므로 기각.
- **Codex bounded wait를 formal subscription으로 간주**: timeout-free·targeted·dedup/coalescing 계약을 충족하지 않아 의미를 왜곡하므로 기각.
- **다른 host 공통 규약에 Codex tool 이름을 추가**: 플랫폼 중립 경계를 깨뜨리므로 기각.

## 검증

- Lifecycle fixture는 formal mode 보존, Codex native cooperative spawn 허용, general 자동 Tier B, explicit independence blocker, non-Codex Tier A-flat 불변을 각각 검사한다.
- Runtime validator는 native Codex session에서 spawn/wait가 실행되고 polling list와 정상 경로 interrupt가 0건인지 검사한다.
- Codex ledger는 `formal_adapter_enabled: false`, `native_join_supported: true`, `selected_mode: host_native_cooperative`를 가져야 하며 formal gap만으로 unavailable event를 만들지 않는다.

## 관련 문서

- [ADR-0009](./ADR-0009-bundle-runtime-platform-neutralization.md)
- [ADR-0021](./ADR-0021-environment-owned-wait-wakeup-scheduling.md)
- [ADR-0022](./ADR-0022-pre-spawn-wait-wakeup-capability-gate.md)
- [Codex lifecycle appendix](../../plugins/atp/docs/development/codex-lifecycle-routing.md)
- [Runtime behavior validator](../../tests/runtime-behavior/README.md)

> Superseded by [ADR-0024](./ADR-0024-host-managed-subagent-orchestration.md) on 2026-08-19. 이 문서는 2.14.0 historical decision/evidence로만 보존한다.
