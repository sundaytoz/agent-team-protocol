---
kind: adr
id: ADR-0016
title: feedback inbox 시스템 제거 — "feedback" 3갈래 중 inbox 카테고리만 폐기 (protocol_feedback·memory type:feedback 존치)
status: accepted
date: 2026-07-06
deciders: [stzjungsoo]
relates_to: [ADR-0003, ADR-0004]
---

# ADR-0016: feedback inbox 시스템 제거

## 배경

프로토콜 전반에서 "feedback" 라는 단어가 **의미가 다른 3개 축**을 관통해 사용돼 왔다:

1. **`protocol_feedback[]`** — `report.md` 스키마 필드. 프로토콜/에이전트 규약의 **구조적 허점**을 세션 중 캡처하고, `structural: true` 항목을 번들 소스 레포 이슈/PR 로 cross-session 승격하는 **자기교정 채널** (protocol §11 라우팅표 (c)행, §12.6).
2. **feedback inbox 카테고리** — `docs/feedback/` 디렉토리. `/task <feedback slug>` 로 inbox 항목을 작업 시작점으로 삼고 완료 시 `archive/` 로 이동하는 **검토·수정 요청 워크플로** (옵트인).
3. **memory `type: feedback`** — retrospective-advisor `memory_candidates` 의 타입 4종 중 하나. "작업 방식 교정/확인" 교훈을 담는 **회고 교훈 타입**.

세 축 모두 `user_signals`(positive/negative) → retrospective → docs-first 반영이라는 공통 상류를 공유하지만, **축 2(inbox)만이 실사용 실적이 없었다** — 템플릿 `category-index/feedback.md` 는 "_(아직 문서 없음)_" 상태로 남았고, 라이브 `docs/feedback/` 디렉토리는 이 레포에 생성된 적이 없다. init 이 14개 카테고리를 스캐폴딩하지만 inbox 플로우는 소비 프로젝트에서 채택되지 않았다.

## 결정

**축 2(feedback inbox 시스템)만 제거한다.** 축 1(`protocol_feedback[]`)·축 3(memory `type: feedback`)·§4.3 과거 사례 기록(dated fact)은 **존치**한다.

경계 근거: 축 1·3 은 프로토콜의 살아있는 자기교정/회고 메커니즘이고 실사용 중이다. 축 2 는 옵트인 스캐폴딩이었으나 채택 실적이 0 이며, "feedback" 이라는 이름의 3중 오버로딩이 프로토콜 독해 시 혼선을 유발했다. inbox 제거로 카테고리 세트가 14 → 13 으로 정리되고 이름 충돌 표면이 줄어든다.

## 영향 (파일 영향 맵)

**삭제:**
- `plugins/atp/templates/category-index/feedback.md` (템플릿 원본)
- `adapters/opencode/.opencode/atp/templates/category-index/feedback.md` (어댑터 미러) + manifest 참조 1줄

**inbox 참조 제거 (base):**
- `plugins/atp/skills/task/SKILL.md` — slug 사용법·§1 참조·§4 해석·§9 종료 4곳
- `plugins/atp/skills/init/SKILL.md` — 카테고리 리스트 + for-loop 에서 `feedback` 제거, 14개 → 13개
- `plugins/atp/templates/docs-index.md` — feedback row
- `plugins/atp/docs/development/search-tool-matrix.md` — 피드백·인박스 row
- `plugins/atp/agents/documentation-advisor.md` — feedback/ 금기 항목
- `docs/architecture/file-map.md` — feedback/index.md 노드 + 14종 → 13종
- `docs/usage/faq.md` — 14개 → 13개

**어댑터 미러 동시 반영:** 위 base 편집을 `adapters/opencode/.opencode/` 대응 파일(atp-task/atp-init/docs-index/search-tool-matrix/atp-documentation-advisor)에 동일 적용.

**존치 (건드리지 않음):**
- `protocol_feedback[]` 전 참조 (protocol §11/§12, report 스키마, retrospective-advisor)
- retro memory `type: feedback`
- `agent-team-protocol.md` §4.3 + `design-advisor.md` 의 `docs/feedback/archive/` 과거 사례 인용 — 2026-05-07 세션의 dated 회고 사실이지 라이브 참조가 아님

## 릴리스

옵트인 기능 제거 — 기존 설치 파손 없음(inbox 미채택). base atp manifest 4곳 동기 bump: **2.3.2 → 2.4.0** (minor). release-checklist §4 invariant 준수.
