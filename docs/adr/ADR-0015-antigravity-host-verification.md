---
kind: adr
id: ADR-0015
title: Antigravity IDE 호스트 검증 — 5번째 Layer-2 어댑터 (Tier A-flat, GEMINI.md, /atp-task)
status: accepted
date: 2026-06-30
deciders: [stzjungsoo]
relates_to: [ADR-0006, ADR-0007, ADR-0009, ADR-0014]
---

# ADR-0015: Antigravity IDE 호스트 검증 — 5번째 Layer-2 어댑터

## 배경

ADR-0006 이 "Gemini CLI" 로 계획한 Google AI 코딩 호스트는 실측 전까지 `TODO:실측` 상태였다. 2026-06-30, **Antigravity IDE** (© 2026 Google, Version 2.2.1, macOS 15.5 Build SDK)에서 최초 실증 검증이 완료됐다. 본 ADR 은 그 실측 데이터를 영구 기록하고, ADR-0006/0007 의 미확정 항목(F-3PLAT-4, 호출 문법)을 해소한다.

## 실증 데이터

- **앱**: `/Applications/Antigravity.app` (Version 2.2.1, Build SDK macOS 15.5, © 2026 Google)
- **테스트 일시**: 2026-06-30
- **프로젝트**: `/Users/wemadeplay/workspace/stz/antigravity` (클린 프로젝트, GEMINI.md 존재)
- **호출**: `/atp-task 실수 a, b입력하면 pow 연산하는 파이썬 코드 작성 후 임의의 값 10개씩 대입해서 결과 보고서 작성해줘`
- **결과**: work-session `20260630-153344` 생성, advisor 체인 전수(requirements→design→implementation→verification→documentation), TC 10/10 PASS
- **모델**: Gemini 3.5 Flash (Medium) — 호스트 자체 라인업

## 핵심결론

| 항목 | ADR-0006 계획/추정 | 실측 결과 |
|---|---|---|
| 제품명 | Gemini CLI | Antigravity IDE |
| task 호출 | `/ns:cmd` (콜론 추정) | `/atp-task` (하이픈) |
| init 호출 | 미확인 | `/atp-init` (하이픈) |
| 지침파일 | `gemini-extension.json` + `commands/*.toml` (F-3PLAT-4 이월) | `GEMINI.md` 직접 읽기 |
| 설치 방식 | `/plugin install` 가정 | Skills 수동 복사 → `~/.gemini/config/skills/` |
| config 루트 | 미확인 | `~/.gemini/config/` (Gemini CLI 동일) |
| Tier | A-flat (doc-cited, smoke 보류) | A-flat 확정 |
| 검증 상태 | TODO:실측 | verified-empirical 2026-06-30 |

## 결정

### 결정 1 — Antigravity IDE = 5번째 Layer-2 어댑터 (Tier A-flat)

Antigravity IDE(© 2026 Google, Version 2.2.1)를 ATP 의 5번째 공식 지원 호스트로 확정한다.

- **Tier**: A-flat. subagent quota 소진 → orchestrator §2.5 직접 대행 fallback 동작 확인.
- **근거**: 실무 task 전 advisor 체인 완주 + TC 10/10 PASS — 단순 로드 확인을 초과하는 포괄적 검증.

### 결정 2 — F-3PLAT-4 해소 (gemini-extension.json 불필요, Antigravity IDE 한정)

ADR-0007 결정 4 가 이월한 F-3PLAT-4(`gemini-extension.json`, `commands/*.toml`)는 Antigravity IDE 에서 **불필요**임이 확인됐다.

Antigravity IDE 는 `GEMINI.md` 를 지침파일로 직접 읽는다 — `/atp-init` 으로 생성된 GEMINI.md 만으로 동작. F-3PLAT-4 상태: **resolved-not-needed (Antigravity IDE 한정)**. Gemini CLI(별도 제품)에 대한 F-3PLAT-4 의존성이 있다면 해당 제품 실측 시 별도 ADR 로 다룬다.

### 결정 3 — 호출 문법 확정: 하이픈 패턴 (`/atp-task`, `/atp-init`)

ADR-0006 §핵심결론 추정 `/ns:cmd`(콜론)는 틀렸음이 확인됐다. Antigravity IDE 는 **하이픈 패턴**을 사용한다:

- task: `/atp-task`
- init: `/atp-init`

Claude Code 의 콜론 네임스페이스(`/atp:task`, `/atp:init`)와 대비.

### 결정 4 — 설치 아키텍처 확인 (Skills + Rules, /plugin 없음)

Antigravity IDE 는 **Claude Code의 `/plugin` 마켓플레이스 시스템이 없다**. 대신 Skills + Rules 시스템을 사용한다.

| 항목 | Claude Code | Antigravity IDE |
|---|---|---|
| 설치 방식 | `/plugin marketplace add` + `/plugin install` | `plugins/atp/skills/` → `~/.gemini/config/skills/` 수동 복사 |
| 범위 | 프로젝트별 | 글로벌(`~/.gemini/config/skills/`) 또는 워크스페이스별 |
| config 루트 | `~/.claude/` | `~/.gemini/config/` (Gemini CLI 동일) |

**실증 설치 경로**:
```bash
# Global skills root 에 복사
cp -r plugins/atp/skills/init ~/.gemini/config/skills/atp-init
cp -r plugins/atp/skills/task ~/.gemini/config/skills/atp-task
# (agents 경로는 별도 확인 필요)
```

- **init**: `/atp-init` (verified-empirical 2026-06-30)
- **지침파일**: GEMINI.md — `~/.gemini/config/` 가 config 루트 (Gemini CLI와 동일)

**부작용 발견**: `/atp-init` 실행 시 생성된 GEMINI.md 의 `atp:begin` 블록 call_token 이 `/atp:task`(콜론)로 기록됨 — 실제 `/atp-task`(하이픈)와 불일치. init SKILL.md `render_block(call_token)` 자가판정 버그. 기능 영향: prose 지침이라 실제 동작은 무해하나, 사용자 안내로서 부정확 — 별도 수정 필요.

## 영향

- `docs/usage/setup-checklist.md/.en.md` — Gemini(TODO) → Antigravity IDE(verified-empirical)
- `docs/usage/faq.md/.en.md` — Gemini TODO 항목 → Antigravity 실측값 갱신
- `plugins/atp/docs/development/platform-adapters.md` §8 — Antigravity 포인터 추가
- `docs/adr/ADR-0006-three-platform-support.md` — 실측 노트 append

## 관련

- [ADR-0006](./ADR-0006-three-platform-support.md) — 3-플랫폼 계획 원문 (Gemini CLI 가정)
- [ADR-0007](./ADR-0007-plugin-root-subdirectory.md) — F-3PLAT-4(gemini-extension.json) 이월 — 본 ADR 결정 2 로 해소(Antigravity IDE 한정)
- [ADR-0009](./ADR-0009-bundle-runtime-platform-neutralization.md) — 번들 중립화, 3사 capability 데이터 동결
- [ADR-0014](./ADR-0014-opencode-host-adapter-strategy.md) — 4번째 호스트(opencode) 실측 선례
