---
kind: changes
title: 2.19.0 — Codex hook marker gate와 atp-codex-hooks add-on 제거
description: codex-team skill 이 marker 없이 Codex built-in subagent 로 team execution 을 연다. hook-guarded bounded pool 절차·add-on·hook 테스트 삭제.
owner: template-maintainer
stability: stable
last_reviewed: 2026-10-29
---

# 2.19.0 — Codex hook marker gate 제거 (ADR-0026)

## 원인

2.18.0 의 Codex team execution 은 옵트인 add-on `atp-codex-hooks` 가 넣는 exact `ATP_HOOK_GUARD_READY` marker 가 있어야 열렸다. Codex 기본 subagent 기능만으로도 child 를 쓸 수 있는데, add-on 설치·hook trust·Unix `python3` 조건을 갖추지 못한 세션은 전부 Tier B 로 격하돼 gate 가 오히려 subagent 사용을 막았다. `codex-team` skill 도 pool token·slot budget·hook ledger·축별 qualification 표로 복잡해졌다.

## 변경

- **`plugins/atp/skills/codex-team/SKILL.md`** — marker gate, `ATP_POOL_*` token, bounded pool/slot budget, hook ledger·root Stop barrier, 축별 표 제거. 프로토콜 기본 계약(identity 연결, 결과 계약, nonterminal=running, 전원 취합 후 완료, 승인형 recovery)만 남김. profile `execution_scope: codex_builtin_subagents`, `scope_gate` 삭제.
- **`plugins/atp/skills/task/SKILL.md` §0.25 / `platform-adapters.md` §3.3** — host skill scope gate·`skip: no-codex-hooks` 서술 제거.
- **`codex-lifecycle-routing.md`** — §1 배포 block·판정 문단 갱신, §3 marker 문장 제거, §8.2~§8.6 hook 이력을 §8.2 요약으로 압축, §8.3 제거 기록 추가.
- **add-on 삭제** — `plugins/atp-codex-hooks/`, marketplace 3곳 등재, `tests/runtime-behavior/test_codex_hook_guard.py`, `build_hook_evidence.py`. Hook evidence JSON 은 history 로 보존.
- **테스트** — `test_codex_managed_contract.py` 배포 profile 테스트를 marker 부재 계약으로 교체, `validate.py` appendix 검사를 `execution_scope: codex_builtin_subagents` + `scope_gate` 부재로 교체.
- **문서** — ADR-0026(ADR-0025 supersede), README/usage/index/file-map/CLAUDE.md/AGENTS.md/release-checklist 정리.
- **버전** — base `2.18.0 → 2.19.0`(manifest 4곳). `atp-graphify` 불변.

## 알려진 한계

2026-10-29 Codex CLI 0.165.0 재확인에서 2-agent 결과 2건 모두 취합(미재현).


2026-08-26 Codex CLI 0.149.1 smoke 에서 built-in barrier 가 staggered 2-agent 중 결과 1건만 전달한 기록이 있다.

## 소비자 조치

- `/plugin update` 또는 `codex plugin` 재설치로 2.19.0 수신.
- 기존 add-on 설치자는 `codex plugin remove atp-codex-hooks`.
