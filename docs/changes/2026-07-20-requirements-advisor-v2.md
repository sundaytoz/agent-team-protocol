---
kind: changes
title: requirements-advisor v2 — AC·우선순위·추적성·위장 해결책 판별 + 프로토콜 §2.10
description: requirements-advisor 조작화 갭 4건 흡수 + doc-저술 advisor 트리거 명문화. 2.5.0→2.6.0.
date: 2026-07-20
owner: template-maintainer
stability: living
last_reviewed: 2026-07-20
---

# requirements-advisor v2 + 프로토콜 §2.10 (2.5.0 → 2.6.0)

## 배경

세션 `20260720-115736` 에서 요구사항 분석 방법론 고찰 문서([docs/development/requirements-analysis-methodology.md](../development/requirements-analysis-methodology.md))를 저술하고, 그 §8 에서 이 레포의 `requirements-advisor` 를 적용 렌즈로 자기비평해 **조작화 갭 4건**을 식별했다. 본 변경은 그 갭을 에이전트 계약에 흡수하고, 같은 세션이 dogfood 한 "doc-저술 advisor 트리거" 판단을 프로토콜에 명문화한다.

## 변경 내용

### 1. `plugins/atp/agents/requirements-advisor.md` (version 1 → 2)

방법론 문서 §4·§3·§1.2 를 요구 단계 게이트로 흡수:

- **acceptance 게이트** — 각 FR 에 통과/실패 판정 가능한 수용 기준 1줄을 요구 단계에서 부여. "AC 를 못 쓰는 FR 은 아직 요구가 아니다" → 오픈질문/가정으로 이관. (검증가능성을 verification 단계로 미루지 않고 요구 단계에서 조기 검출)
- **우선순위(MoSCoW)** — FR 에 `priority: must|should|could|wont` 태깅. `wont` 로 스코프 명시 제외를 문서화.
- **추적성** — FR 에 `traces_to`(상위 필요/비즈니스 목표) 부여. 추적 안 되는 FR = 위장 해결책·잉여 신호.
- **위장 해결책 판별** — 신규 구조적 소절. "왜 원하는가"로 상위 목적 환원 여부를 능동 점검하여 요청에 전제된 해결책을 요구로 굳히지 않음. 생명주기 gap-hunt·복수 이벤트 대칭 점검과 동급 의무.
- 출력 스키마 `agent_version: 2`, 자가 검증 항목 4번(FR 3필드 부여 점검) 추가.

### 2. `plugins/atp/docs/development/agent-team-protocol.md` (신규 §2.10)

**doc-저술 시 advisor 트리거 — 분량이 아니라 성격.** 신규 코드/설계·외부 조사가 없고 도메인 지식을 orchestrator 가 보유한 합성 essay 는 큰 doc(수백 줄)이라도 advisor 전수 skip + 직접 저술이 우위일 수 있음. 단 (1) skip 근거를 Advisor Invocation Decision Log 에 기록, (2) documentation-advisor 규율(카테고리·index·frontmatter·링크)을 self-verification 으로 흡수. §7 impl-advisor 직접 실행 임계값과 동형의 축소 방향 재량.

### 3. 버전 bump

base atp manifest 4곳 2.5.0 → 2.6.0 (`plugins/atp/.claude-plugin/plugin.json`, `plugins/atp/.codex-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.codex-plugin/marketplace.json`).

## 영향

- 소비 프로젝트에서 `/atp:task` 진입 시 requirements-advisor 산출물(`requirements.md`)의 FR 이 priority·acceptance·traces_to 를 포함하는 형태로 바뀐다. 하위 호환: 기존 산출물 파서가 없으므로 스키마 확장은 가산적이며 파괴적이지 않음.
- ADR 미작성 — 가산적·가역적 스펙 진화로 판단.

## 검증

- release-checklist §4 버전 invariant: base 4곳 2.6.0 일치
- release-checklist §8 끊긴 §N 0: §2.10 은 하위 소절 추가로 top-level §N 재배열 없음
- release-checklist §1 링크 / §6 신규 doc 등록
