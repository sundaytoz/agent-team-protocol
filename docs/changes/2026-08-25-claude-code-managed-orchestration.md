---
kind: changes
title: 2.16.0 — Claude Code managed orchestration (turn-end await)
description: Claude Code host 전용 orchestration skill과 lifecycle appendix를 신설해 async Agent 툴의 task-notification barrier를 정본화하고, advisor의 no-op 틱·transcript 폴링 improvisation을 제거.
owner: template-maintainer
stability: stable
last_reviewed: 2026-08-25
---

# 2.16.0 — Claude Code managed orchestration (turn-end await)

## 원인

소비 프로젝트 세션 `c9027225`(ATP 2.15.0, Claude Code 2.1.243)에서 research-advisor가 parallel-explorer 6개를 spawn한 뒤 no-op `echo idle` Bash 틱 233회+(~3–5초 간격)와 `~/.claude/projects/**` child transcript 파일 크기 폴링으로 대기를 improvise했다. 이미 완료된 worker를 5분 이상 계속 `wc -l` 폴링하는 구간도 관측됐다.

원인은 이중 공백이다.

1. 신버전 Claude Code의 `Agent` 툴이 동기(blocking)에서 async spawn + `<task-notification>` 전달로 바뀌어, 구버전에서 spawn 호출 자체가 수행하던 barrier가 사라졌다.
2. ATP 번들에는 host orchestration skill이 `codex-team` 하나뿐이라, Claude Code advisor는 "managed barrier 사용·polling 금지"라는 추상 계약만 받고 구체 메커니즘 없이 improvise했다(ledger의 `host_managed_subagent_orchestration: supported`도 보증 주체 없는 임의 판정이었다).

## 변경

- Claude Code 전용 `claude-code-team` skill을 추가하고 첫 collaboration action 전 전문 로드를 의무화했다.
- `claude-code-lifecycle-routing.md` appendix를 신설해 검증된 capability profile(`formal_adapter_enabled: false`, `manual_wait_polling_supported: false`, `host_managed_subagent_orchestration: supported`, `team_execution_enabled: true`)과 event mapping을 정본화했다.
- Barrier를 turn-end await로 확정했다: spawn(한 메시지 병렬) → 대기 목적 툴 호출 0으로 턴 종료 → harness가 live children 보유 agent를 완료 처리하지 않고 모델 호출 0으로 suspend → child terminal마다 `<task-notification>`(inline result) 재기동 → 전건 수집 후 최종 반환.
- 금지 목록을 명문화했다: no-op 틱(`echo`/`sleep`), `~/.claude/projects/**`·`tasks/*.output` transcript 읽기, 파일 크기/mtime liveness 폴링, `ListAgents` 반복 조회, `TaskOutput` 의존(nested 툴셋 미존재).
- `platform-adapters.md` §7.1에 Claude Code appendix 포인터를 추가했다.

Codex 경로는 무수정이다 — `codex-team` skill, `codex-lifecycle-routing.md`, 공통 protocol §2.5 본문, task SKILL 모두 변경 0. 신규 파일 2개 + additive 포인터 2줄 + manifest bump가 전부다.

## 검증

2026-08-25 Claude Code 2.1.243 격리 smoke 3건 실측(`tests/runtime-behavior/evidence/claude-code-2.1.243-20260825.json`):

- terminal-only 1-agent: 턴 종료 후 child terminal에 재기동, 최종 반환에 child 결과 포함 — pass
- nested `TaskOutput` 가용성: 툴 부재 확인 — barrier 후보 제외
- staggered 2-agent all-results: wakes=3, per-child delivery, +25s delayed terminal 수집, manual wait 0 — pass

관측 세션의 반증 증거: W2 worker 최종 산출 원문이 advisor 컨텍스트에 transcript 기록 없이 주입돼 재현됨(worker 종료 00:40:13 → advisor 산출 00:41:56, 유입 레코드 0) — task-notification 인라인 전달의 실증.

## 잔여

- 실환경(소비 프로젝트) `/plugin update` 후 `/atp:task`로 advisor→worker 경로 1회 실호출해 `manual_wait_calls: 0` 확인 — needs_user_verification.
- `failed | interrupted` notification의 event 구분 전달은 미관측(`unknown`) — 관측 시 appendix §2 갱신.
