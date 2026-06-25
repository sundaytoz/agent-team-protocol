---
kind: changes
title: opencode 4번째 Layer-2 어댑터 — generator + npm bin CLI 추가
date: 2026-06-24
related_adr: ADR-0014
---

# opencode 어댑터 추가 (2026-06-24)

## 변경 요약

`adapters/opencode/` 신규 추가 — generator 기반 능동 변환 + npm `bin` CLI installer. opencode 를 ATP 의 4번째 Layer-2 호스트로 지원한다.

## 변경 내용

| 항목 | 내용 |
|---|---|
| 추가 | `adapters/opencode/` — generator + `bin/cli.js` + `package.json` |
| 기능 | `install`/`uninstall`, `--global`(~/.config/opencode/) / `--project`(.opencode/), `--with-graphify`, `--provider` |
| 변환 | tools→opencode permission(per-tool), `mode: subagent` 전수, description 보존, 경로치환(`${CLAUDE_PLUGIN_ROOT}/docs/...` → `@<설치경로>/atp/docs/...`) |
| 토폴로지 | Tier A-flat(primary fan-out, subagent `task:deny` 재귀차단) |
| 모델 | 기본 `model:` 생략(상속, ProviderModelNotFoundError 0 실증). `--provider` 시만 bake |

## 검증 결과

정식 스모크 전건 PASS (`.atp/work-session/20260624-172721/verification/results.md`):

- **L1 — generator 단위/정적**: 15/15 PASS (골든 단위 24 tests + AC-01~AC-15)
- **L2 — opencode 런타임**: 7/7 PASS (AC-08,10,11,09b,16,17,18)
- FAIL/skip: 0

## 관련 결정

- [ADR-0014](../adr/ADR-0014-opencode-host-adapter-strategy.md) — 이식 전략 결정(accepted 2026-06-24) + 구현 완료 기록(D7 후속 섹션)
- [ADR-0009](../adr/ADR-0009-bundle-runtime-platform-neutralization.md) — 번들 런타임 중립화. platform-adapters.md 에 opencode host 행을 추가하지 않는 근거(중립화 유지, §8 포인터만)
