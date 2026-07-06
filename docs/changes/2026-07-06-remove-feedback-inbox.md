---
kind: changes
title: feedback inbox 시스템 제거 (14 → 13 카테고리)
date: 2026-07-06
relates_to: [ADR-0016]
---

# feedback inbox 시스템 제거

## 무엇이 바뀌었나

"feedback" 3갈래 중 **inbox 카테고리 시스템만** 제거. init 스캐폴딩 카테고리가 14 → 13 개로 감소. `/task <feedback slug>` 진입 경로·`docs/feedback/` 카테고리·inbox/archive 워크플로 삭제.

**존치**: `protocol_feedback[]`(프로토콜 자기교정), retro memory `type: feedback`, §4.3 과거 사례 기록.

## 실동작 변경

- `/atp:init` 실행 시 `docs/feedback/` 를 더 이상 생성하지 않음 (13개 카테고리만).
- `/atp:task <slug>` 의 feedback slug 진입 분기 제거 — 인자는 요청 본문으로만 해석.
- opencode 어댑터 미러 동일 반영 (`atp-task`/`atp-init`/템플릿/search-tool-matrix/documentation-advisor).

## 릴리스

base atp manifest 4곳: 2.3.2 → 2.4.0 (minor). 옵트인 기능 제거 — 기존 설치 파손 없음.

상세 근거·파일 영향 맵: [ADR-0016](../adr/ADR-0016-remove-feedback-inbox-system.md).
