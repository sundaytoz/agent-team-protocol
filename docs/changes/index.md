---
kind: changes
title: Changes 카테고리 인덱스
description: 실제 구현 변경 이력(changelog). 런타임 동작·설치 경로·외부 인터페이스가 바뀐 경우.
owner: template-maintainer
stability: living
last_reviewed: 2026-06-24
---

# Changes — 런타임 동작 변경 이력

이 카테고리는 **실제 구현이 반영된 변경의 이력**을 모은다. 읽는 목적: "언제 어떤 구현 변화가 들어갔는지" 확인.

- 코드 또는 코드가 소비하는 설정/정적 데이터가 바뀌어 **실제 동작이 달라진** 경우에만 작성.
- 문서 동기화만 한 경우, 구조 분석만 한 경우, 운영 절차만 정리한 경우는 대상이 아님 → 각 해당 카테고리(`development/`, `analysis/`, `maintenance/`).
- 기술 선택·아키텍처 결정의 불변 레코드는 `../adr/`.

## 목록

| 파일 | 내용 | 날짜 |
|---|---|---|
| [2026-06-24-opencode-adapter.md](./2026-06-24-opencode-adapter.md) | opencode 4번째 Layer-2 어댑터 — generator + npm bin CLI 추가 (L1 15/15 + L2 7/7 PASS) | 2026-06-24 |
| [2026-06-25-opencode-adapter-npm-publish.md](./2026-06-25-opencode-adapter-npm-publish.md) | @atp-opencode/opencode npm publish 가능화 — vendor 번들 + prepack (AC 7/7 PASS) | 2026-06-25 |
| [2026-07-06-remove-feedback-inbox.md](./2026-07-06-remove-feedback-inbox.md) | feedback inbox 시스템 제거 (14→13 카테고리) — 2.3.2→2.4.0, protocol_feedback·memory type 존치 | 2026-07-06 |
| [2026-07-07-codex-spark-routing.md](./2026-07-07-codex-spark-routing.md) | Codex Spark 조건부 라우팅 appendix — 2.4.0→2.5.0, 미지원 시 기존 tier 매핑 fallback | 2026-07-07 |

## 관련 카테고리

- 기술/운영 결정의 **불변 레코드** → `../adr/`
- 오래 유지될 구조 설명 → `../architecture/`
- 재사용 가능한 개발 규칙 → `../development/`
