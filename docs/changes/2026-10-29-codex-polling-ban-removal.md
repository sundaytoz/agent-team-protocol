---
kind: changes
title: 2.19.1 — Codex wait_agent·list_agents polling 금지 제거
description: Codex appendix 와 host-managed validator 에서 wait_agent·list_agents 호출 금지를 제거하고 호출 수를 관측값으로만 기록.
owner: template-maintainer
stability: stable
last_reviewed: 2026-10-29
---

# 2.19.1 — Codex polling 금지 제거

## 변경

- **`codex-lifecycle-routing.md`** — `wait_agent`·`list_agents` 호출 금지 서술과 `manual_wait_calls: 0`·`list_calls: 0` fixture 기대값 제거. 두 값은 관측 호출 수로만 기록한다. capability error 보상 금지 목록에서 manual polling 제거.
- **`tests/runtime-behavior/validate_codex_session.py`** — host-managed 검사에서 `wait_agent`·`list_agents` 실행을 실패로 보던 규칙 제거, `semantic_recovery_actions` 집계에서 `list_agents` 제외. 정상 경로 `interrupt_agent` 금지는 유지.
- **테스트** — `test_builtin_wait_and_list_calls_are_allowed` 회귀 추가(수정 전 validator 에서 실패 확인). `validate.py` appendix 검사 갱신.
- **범위** — Codex 전용. Claude Code skill·공통 프로토콜·`manual_wait_polling_supported` 축은 변경하지 않음.
- **버전** — base `2.19.0 → 2.19.1`.
