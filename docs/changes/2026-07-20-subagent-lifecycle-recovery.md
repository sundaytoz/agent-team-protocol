---
kind: changes
title: subagent silent-start lifecycle recovery — 승인 기반 독립 재시도와 유한 수렴
description: 첫 관측 가능 활동 없는 running invocation의 안전한 감지·격리·독립 재시도 규약. 2.7.0→2.8.0.
date: 2026-07-20
owner: template-maintainer
stability: living
last_reviewed: 2026-07-20
---

# subagent silent-start lifecycle recovery (2.7.0 → 2.8.0)

## 변경 내용

- 명시적 오류 없이 실행 중이지만 first observable activity가 없는 호출을 `suspected_silent_stall`로 분류하는 공통 의미 계약을 `agent-team-protocol.md` §2.5에 추가했다.
- 감지는 자동화할 수 있으나 interrupt, retry, fallback은 사용자 보고와 옵션 제시 후 승인받아 실행하도록 기존 안전 게이트를 유지했다.
- clean retry를 새 invocation ID로 정의했다. 동일 invocation follow-up은 retry/attempt로 세지 않는다.
- 상태 확인과 retry에 host/config별 유한 budget을 요구하고, optional advisor부터 mandatory verification·destructive action·closing docs/retro까지 phase별 종단을 명시했다.
- write-capable 호출은 termination/isolation 확인, ownership 회수, partial write 분류 후에만 동일 scope의 새 실행을 허용한다. 회수 후 도착한 결과는 `late_completion`으로 격리하며 자동 merge·성공 판정을 금지한다.
- `schema_version: 2`를 유지하면서 `attempt`, `termination`, `retry_of`, `lifecycle_fallback_reason` 네 필드를 optional로 추가했다. lifecycle fallback은 §5.7의 모델 routing fallback과 분리된다.
- Codex collaboration 도구 mapping과 calibration 지침을 `codex-lifecycle-routing.md` appendix로 분리했다. 공통 protocol에는 host 도구명이나 고정 시간값을 두지 않는다.

## 호환성

기존 schema v2 report는 수정 없이 유효하다. 새 필드 부재는 legacy/unknown으로 해석하며, 기존 reader는 optional 필드를 무시할 수 있다. 다른 host는 lifecycle appendix 없이도 capability-unknown 경로와 Tier B/self-check/blocked 종단을 적용할 수 있다.

## 사용자에게 보이는 변화

advisor가 첫 활동 없이 `running`에 머물면 ATP는 무한 polling이나 자동 retry 대신 상태와 관측 한계를 보고한다. 사용자는 clean retry, 추가 대기, phase에 허용된 fallback, 중단 중에서 선택한다. code 변경의 verification은 advisor 장애를 이유로 skip되지 않는다.

## 검증

- lifecycle 상태·예외·phase fallback fixture
- legacy/new schema v2 compatibility fixture
- 승인 전 action 0건, invocation identity, ownership handoff, late completion quarantine
- 공통 정본 host-neutrality와 Codex appendix mapping
- 문서 링크·§N 인용·index·base manifest 4곳 2.8.0 동기화

결정 배경과 불변식은 [ADR-0017](../adr/ADR-0017-subagent-lifecycle-recovery.md)을 따른다.
