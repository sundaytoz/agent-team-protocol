---
kind: changes
title: requirements-advisor v3 — 명확성 게이트 + 착수·종료 판정(되돌리기 비용)
description: 방법론 2차 교차검사로 도출한 핵심 품질 게이트 2건(§4 명확성 / §6.3+§7 종료판정) 흡수. 2.6.0→2.7.0.
date: 2026-07-20
owner: template-maintainer
stability: living
last_reviewed: 2026-07-20
---

# requirements-advisor v3 — 명확성 게이트 + 착수·종료 판정 (2.6.0 → 2.7.0)

## 배경

v2 는 요구사항 분석 방법론([docs/development/requirements-analysis-methodology.md](../development/requirements-analysis-methodology.md)) §8 이 자기비평으로 지목한 조작화 갭 4건(acceptance·MoSCoW·traces_to·위장 해결책 판별)을 흡수했다. 본 변경은 그 §8 이 **다루지 않은** §1~§7 전 원칙을 v2 에이전트와 재교차검사(2차)해 잔여 갭 후보 G1~G8 을 도출하고, 그중 방법론이 **핵심 품질 게이트로 규정**했으나 유일하게 미조작화였던 두 건을 계약에 흡수한다.

세션 `20260720-124023`.

## 변경 내용

### 1. `plugins/atp/agents/requirements-advisor.md` (version 2 → 3)

방법론 §4·§6.3·§7 을 요구 단계 게이트로 흡수:

- **명확성 게이트 (G1, §4 unambiguous)** — 신규 구조적 소절. FR 서술에 정량화·예시로 고정되지 않은 형용사/부사("빠르게", "적절히", "일부", "대부분")가 남으면 요구가 아니라 **미정 자리표시자**로 규정. (1) acceptance 에 수치/예시로 정량 고정, 또는 (2) 오픈질문/가정 이관 — 둘 중 하나로 해소하고 FR 본문에 모호어를 남기지 않는다. acceptance 필드의 **사전 조건**으로 위치(모호어가 살아있으면 acceptance 는 형식만 채워질 뿐 판정 불가).
- **착수·종료 판정 (G2, §6.3 분석 마비 + §7 착수 판정)** — 신규 소절. 종료 조건을 "오픈 질문 0" 이 아니라 **"남은 모호성이 전부 되돌리기 싼 결정에만 닿는 상태"**로 명문화. 미해결 항목을 되돌리기 비쌈(스키마·공개 계약·마이그레이션·외부 인터페이스·권한 경계 → 붙든다) vs 쌈(지역 로직·문구·내부 배치 → 가정 명시 후 진행)으로 분류. 기존 "추측 가능하면 넘긴다"(도구 규칙)의 판정축을 **되돌리기 비용**으로 고정 — 분석 마비 ↔ 조기 종료 양방향 방지.
- 역할 요약에 두 게이트 반영, `AskUserQuestion` 규칙에 판정축 포인터 추가.
- 출력 스키마 `agent_version: 3`, 자가 검증 항목 5번(명확성 게이트)·6번(종료 판정) 추가.

### 2. `docs/development/requirements-analysis-methodology.md` §8

"이미 조작화된 것" 표에 §4 명확성·§6.3+§7 착수·종료 판정 행 추가. "2차 교차검사(2026-07-20, v3)" 노트로 G1~G8 도출 결과와 흡수(G1/G2)·보류(G3~G8) 근거 기록.

### 3. 버전 bump

base atp manifest 4곳 2.6.0 → 2.7.0 (`plugins/atp/.claude-plugin/plugin.json`, `plugins/atp/.codex-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.codex-plugin/marketplace.json`).

## 보류 (한계효용 낮음)

- **G3 Kano 당연요구 능동 사냥 (§3.3)** — gap-hunt 가 순차 전이 단절은 사냥하나 "말해지지 않은 당연요구 캐기"로 명명 안 됨. gap-hunt 에 부분 흡수돼 별도 명문화 한계효용 낮음.
- **G4 FR 간 일관성 (§4 consistent)** — self-verification 에 상호 모순 점검 항목 부재. 저빈도.
- **G5~G8** — INVEST(§3.4, Testable 은 acceptance 로 커버)·금도금 명시신호(§6.2, traces_to 가 탐지 도구)·확증편향 자문(§6.4)·가정→FR 의존추적(§7, 프로토콜 §2.7 plan-gate 로 세션 레벨 커버).

## 영향

- 소비 프로젝트에서 `requirements.md` 산출물의 `agent_version` 이 3 으로 스탬프된다. FR 스키마 필드(priority·acceptance·traces_to)는 v2 와 동일 — 신규 게이트는 *행동/자가검증* 규율이라 스키마 shape 불변. 하위 호환 가산적.
- ADR 미작성 — 가산적·가역적 규율 진화로 판단(v2 와 동형).

## 검증

- release-checklist §4 버전 invariant: base 4곳 2.7.0 일치
- release-checklist §5 agent catalog: agents/ 목록 불변(신규 에이전트 없음)
- release-checklist §8 끊긴 §N 0: 방법론 문서 top-level §N 재배열 없음
- release-checklist §1 링크 / §6 신규 doc 등록(changes/index.md)
