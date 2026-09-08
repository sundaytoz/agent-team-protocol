---
kind: adr
adr_number: "0025"
title: Codex team execution을 atp-codex-hooks add-on marker에 gate된 hook-guarded bounded pool로 승격
status: accepted
date: 2026-09-08
deciders:
  - template-maintainer
  - stzjungsoo
extends:
  - ADR-0024
---

# ADR-0025: Codex scope-gated team execution (hook-guarded bounded pool)

## 상태

**Accepted** — 2026-09-08. ADR-0024의 execution mode·authority 경계·release-time evidence 원칙을 유지하고, tested Codex CLI profile을 `unsupported`/`team_execution_enabled: false`에서 **선언된 scope 안의 `supported`/`true`**로 전환한다. ADR-0024를 supersede하지 않고 확장한다.

## 맥락

ADR-0024는 Codex built-in all-results barrier가 staggered 2-agent에서 실패한 사실(`spawn_calls=2`, `terminal_deliveries=1`)을 근거로 team execution을 닫았다. 이후 plugin-bundled hook이 spawn/wait/SubagentStop/root Stop을 관측해 durable ledger와 completion barrier를 제공하는 hook-guarded bounded pool candidate가 backlog §Phase 3의 4개 독립 축으로 qualification됐다.

- A(all-results barrier) PASS — 2026-08-31 T7/T9 재실행, 2026-09-08 add-on 빌드 재확인
- B(in-flight control) unknown — interactive PTY 미측정. ATP 정상 흐름은 mid-flight steering을 요구하지 않는다
- C(approval continuation) supported — 2026-08-28 T5
- D(packaging scope) — hook trust는 command 문자열에만 묶여 이후 runner 변경을 무확인 실행하므로 base 번들 배포는 부당했다. candidate hook을 옵트인 add-on `atp-codex-hooks`로 분리(2.17.0)해 기능을 켜는 사람만 그 동의를 진다

## 결정

### 1. Profile은 scope-gated로 전환한다

```yaml
formal_adapter_enabled: false
manual_wait_polling_supported: false
host_managed_subagent_orchestration: supported
team_execution_enabled: true
execution_scope: hook_guarded_bounded_pool
scope_gate: atp_hook_guard_ready_marker
```

`supported`/`true`는 `codex-team` §1의 exact `ATP_HOOK_GUARD_READY` marker가 root context에 있는 세션에만 적용된다. Marker는 add-on `atp-codex-hooks`의 `SessionStart` hook만 만들며, 설치본 `hooks/hooks.json`·`hooks/codex_pool_hook.py`의 SHA-256에 묶인다.

### 2. Scope 판정은 marker 하나로만 한다

Marker 부재(add-on 미설치, hook untrusted/disabled/policy-excluded, Windows `py -3` 미검증, source/install mismatch)는 오류가 아니라 기본 소비자 상태다. 그 세션은 `unsupported`로 동작하고 `$atp:task`는 `skip: no-codex-hooks`를 기록한 뒤 `general_task`는 `tier_b_sequential`, `explicit_subagent_required`는 `blocked_explicit_independence`로 차단 없이 계속한다. 시간·관측·probe로 scope 안팎을 재추론하거나 marker를 prompt에 합성하지 않는다.

### 3. All-results barrier의 제공자는 bounded pool이다

Codex built-in wait가 아니라 `codex-team` §2~§6의 queue→wait→refill scheduler + hook ledger(`ATP_POOL_BIND`/`ATP_POOL_RESULT`/`ATP_POOL_DENIED`/`ATP_POOL_TERMINAL_DELTA`) + root `Stop` barrier가 barrier를 구성한다. Capacity denial은 failure/retry가 아니라 pending 복귀이며, parent가 authoritative하게 관측한 error를 `update_plan` marker로 ledger에 재진술한다.

### 4. B축 unknown의 의미를 한정한다

실행 중 steering/취소 delivery를 **요구하는** 요청만 blocked/user-decision 경로로 보낸다. 사용자 취소는 host 인터럽트가 상위 계층에서 전체를 끊으므로 ATP 불변식(terminal confirmation 없는 합성 금지)은 유지된다.

### 5. 승격 근거는 add-on 빌드의 격리 qualification이다

`tests/runtime-behavior/evidence/codex-cli-0.149.1-hook-guarded-20260908.json` — terminal-only 1-agent, delayed terminal 1-agent, staggered 2-agent, capacity-denial refill 5-agent(attempts 9 / accepted 5 / denials 4 전건 parent_marker / terminal·collected 5) 전부 pass, list/interrupt 0, root Stop은 전원 collected 뒤에만 allow. `allow_managed_hooks_only`는 사용자 config에서 바인딩되지 않는 managed 계층 키로 확인돼 fail-closed로 커버한다.

## 결과

- Codex CLI 0.149.1에서 add-on을 설치·신뢰한 사용자는 `$atp:task`로 실제 advisor/worker team execution을 얻는다. 설치하지 않은 사용자의 동작은 2.17.0과 동일(Tier B)하다.
- base `atp` 번들은 hook을 포함하지 않으므로 신뢰 요청은 add-on 경계 안에서만 발생한다.
- Known Issue ATP-KI-001은 "선언 scope 안에서 해소"로 상태를 바꾸고, scope 밖(add-on 미설치·Windows·App/IDE)의 제한만 남긴다.
- validator/fixture: routing appendix 배포 block이 fixture block과 네 축 값이 일치하며, lifecycle-contract gate는 `scope_gate`와 `skip: no-codex-hooks` 어휘를 요구한다.

## 기각한 대안

- **전역 boolean `true`**: add-on 미설치 세션에서 marker 없이 spawn을 시도하게 되어 fail-closed 불변식과 D축 동의 경계를 깨뜨린다.
- **B축 측정 전 보류**: B는 A를 무효화하지 않는 독립 축이며 정상 흐름이 요구하지 않는 능력이다. 보류는 검증된 barrier를 불필요하게 포기한다.
- **base 번들에 hook 재포함**: D축 결론과 모순.

## 검증

- `tests/runtime-behavior/test_codex_hook_guard.py` 21건, `test_codex_managed_contract.py`(승격 evidence 대조 포함), `tests/lifecycle-contract/validate.py`
- 격리 qualification evidence 2026-09-08 (§5)

## 관련 문서

- [ADR-0024](./ADR-0024-host-managed-subagent-orchestration.md)
- [Codex orchestration skill](../../plugins/atp/skills/codex-team/SKILL.md) §1·§7
- [Codex lifecycle appendix](../../plugins/atp/docs/development/codex-lifecycle-routing.md) §1·§8.6
- [Backlog — qualification handoff](../backlog/codex-cli-hook-guarded-bounded-pool.md) §Phase 3
- [atp-codex-hooks 사용 가이드](../../plugins/atp-codex-hooks/docs/codex-hooks-usage.md)
