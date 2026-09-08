---
kind: changes
title: 2.18.0 — Codex team execution 승격 (scope-gated, atp-codex-hooks marker)
description: hook-guarded bounded pool 을 add-on 빌드에서 4-smoke qualification PASS 시켜 codex-team 배포 profile 을 host_managed_subagent_orchestration supported / team_execution_enabled true 로 전환. marker 없는 세션은 Tier B 유지.
owner: template-maintainer
stability: stable
last_reviewed: 2026-09-08
---

# 2.18.0 — Codex team execution 승격 (scope-gated)

## 원인

2.17.0 에서 candidate hook 을 옵트인 add-on `atp-codex-hooks` 로 분리했지만 배포 profile 은 `team_execution_enabled: false` 였다. backlog §Phase 3 규칙(A·D 충족 → 선언 scope 안 승격)에서 남은 것은 D축 scope 선언과 `allow_managed_hooks_only` 측정, 그리고 add-on 빌드(hooks hash 변경) 기준 qualification 재실행이었다.

## 변경

- **배포 profile** (`codex-team` §7, routing appendix §1): `host_managed_subagent_orchestration: supported`, `team_execution_enabled: true`, `execution_scope: hook_guarded_bounded_pool`, `scope_gate: atp_hook_guard_ready_marker`. 값은 **scope-gated** — `ATP_HOOK_GUARD_READY` marker 가 있는 세션(add-on 설치 + hook trust, Unix `python3`)에만 적용.
- **`codex-team` §1 gate**: "격리 maintainer smoke 명시 요청" 전제 제거. marker 존재 = scope 안 = bounded pool 로 정상 team execution. marker 부재 = `skip: no-codex-hooks` → `tier_b_sequential` / `blocked_explicit_independence`, 오류 아님.
- **`task` SKILL §0.25**, **platform-adapters §3.3**: host skill 의 `supported` 가 scope-gated 일 수 있음과 marker 단일 신호 판정 명시.
- **ADR-0025** 신설(ADR-0024 확장). known-issues KI-001 → "Resolved within declared scope". backlog §승격, routing §8.6, tests README, add-on 가이드·faq·README·index 정합.
- **evidence** `tests/runtime-behavior/evidence/codex-cli-0.149.1-hook-guarded-20260908.json`; `test_codex_managed_contract.py` 가 배포 block 을 이 evidence 와 대조(전 smoke pass, Q4 attempts−accepted == denials == parent_marker attested). `tests/lifecycle-contract/validate.py` 가 appendix 의 `supported/true` + `scope_gate` + `skip: no-codex-hooks` 어휘를 요구.
- **버전** base `2.17.0 → 2.18.0`(manifest 4곳). add-on 1.0.0 불변(hook byte 무변경 — marker 동일).

## 검증

격리 qualification(임시 `CODEX_HOME`, base 2.17.0 + add-on 1.0.0 fresh install, TUI `Trust all` 임시 home 한정, `codex exec --json` workspace-write / approval never, `ATP_HOOK_EVENT_LEDGER=1`, codex-cli 0.149.1):

| smoke | attempts / accepted / denials / terminal / collected | wait | 판정 |
|---|---|---|---|
| Q1 terminal-only 1-agent | 1 / 1 / 0 / 1 / 1 | 1 | pass |
| Q2 delayed terminal 1-agent (`sleep 35`) | 1 / 1 / 0 / 1 / 1 | 2 (첫 wait 무결과 → running 유지, 합성 0) | pass |
| Q3 staggered 2-agent (`sleep 30` + 즉시) | 2 / 2 / 0 / 2 / 2 | 2 | pass |
| Q4 capacity-denial refill 5-agent (limit 1) | 9 / 5 / 4 (전건 `parent_marker`) / 5 / 5 | 5 | pass |

전 run list/interrupt 0, 마지막 hook event `Stop`(complete). `allow_managed_hooks_only`: `-c` override·`$CODEX_HOME/requirements.toml` 모두 무효(managed 계층 키) → fail-closed 커버. 사용자 `~/.codex` 무변경.

정적: hook guard 21, managed contract 16, validate_codex 6, lifecycle-contract PASS, release-checklist §1/§4/§8.

## 잔여

- B축 T4 interactive PTY steering 재측정, Windows `py -3` runner — 둘 다 profile 변경 없이 축 값 갱신.
- 소비 Codex 환경에서 add-on 설치·trust 후 `$atp:task` 1회 실호출로 advisor spawn 확인 — needs_user_verification.
