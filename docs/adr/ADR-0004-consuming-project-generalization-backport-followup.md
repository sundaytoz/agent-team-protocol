---
kind: adr
adr_number: "0004"
title: v1.2.0 — 소비 프로젝트 일반화 자산 후속 역이식 (호출 실패 처리 · 자가점검 2종 · graph 이월금지 · Decision Log · analysis perspective)
status: accepted
date: 2026-06-05
deciders:
  - template-maintainer
  - stzjungsoo
supersedes: []
---

# ADR-0004: v1.2.0 — 소비 프로젝트 일반화 자산 후속 역이식

## 상태

**Accepted** — 2026-06-05. ADR-0003(v1.1.0) 위에 적층. supersede 아님.

---

## 맥락

ADR-0003 이 소비 프로젝트 fork 의 일반화 자산 일부(계획 가시화·AskUserQuestion 옵션설계·clarify 분기·산출물 자가검증 계약)를 v1.1.0 으로 흡수했으나, 그 이후 소비 프로젝트에서 여러 세션에 걸쳐 누적된 규약 개선이 본체에 반영되지 않은 채 남아 있었다. 분기 진단 결과 ADR-0003 이 흡수하지 못한 일반화 후보 6건이 식별됐고, 모두 도메인 무관 규약이거나 소비 프로젝트 식별자를 본문 재작성으로 제거할 수 있는 항목이다.

핵심 제약은 일반화 게이트다 — 소비 프로젝트 식별자(외부 API명·패키지·스택·env·hook 경로·개인 메모리 slug)를 본문·메타문서·파일명 어디에도 남기지 않는다. 식별자를 강하게 동반하는 후보는 단순 치환이 아니라 본문 재작성으로 일반 규약만 추출했다.

## 결정

다음 6건을 본체에 역이식한다(v1.2.0). 삽입은 모두 순번 append 또는 신규 섹션이라 기존 섹션의 하향 재번호가 발생하지 않는다.

1. **advisor 호출 실패 처리 + partial 산출물 회복** — `agent-team-protocol.md` 에 신규 §2.5 신설. API 오류/timeout/rate limit 시 즉시 사용자 보고 + 재시도 옵션 a/b/c + 자동 재시도 금지. tier-3 advisor 의 부분 산출물이 남은 중단은 좁은 재호출 + 모델 한 단계 다운그레이드로 회복하되, §5.5 의 silent downgrade 금지와 정합(사용자 인지 하 명시 다운그레이드).
2. **AskUserQuestion 자가점검: 인용 사실 신선도** — §4.4 자가점검 목록 6번 append. 비교형 옵션의 "현재" 인용이 stale 하지 않은지 제시 직전 재확인.
3. **AskUserQuestion 자가점검: 인접 구현체 인용 완결성** — §4.4 자가점검 목록 7번 append. 옵션이 언급한 구현 계층의 기존 동류 구현체 인용 누락 방지.
4. **graph 갱신 이월 금지(no-defer) 정책** — `skills/task/SKILL.md` 세션 종료 graph-refresh step 에 정책 한 줄 + `addons/graphify/docs/graphify-usage.md` 에 상세 섹션(처리 경로 A/B·의사결정 표·폐기된 구 규약·보고서 기록). hook 구현·트리거 경로는 소비 프로젝트 정의(placeholder)로 격리.
5. **Advisor Invocation Decision Log** — `skills/task/SKILL.md` §3(report.md 초기화) 본문 강화. 각 advisor 호출/스킵 판단을 시점에 즉시 1줄(call/skip/rationale/checked_at) append. 식별자 0 — 단순 이식.
6. **analysis 문서 perspective frontmatter 규약** — `documentation-guidelines.md` "카테고리 선택" 다음에 신규 섹션. 분석 관점을 frontmatter 에 명시(perspective / valid_starting_point_for / superseded_note)해 후속 세션의 잘못된 전제 채택을 방지. perspective enum 은 일반화(backward-compat / redesign / neutral).

일반화 게이트는 변경분(diff) 추가 라인 + 신규 파일명 slug 에 적용하며, 식별자 residual 0 을 commit 전 확인했다.

### 범위 밖 (역이식하지 않음)

- **코어 advisor `agents/*.md` 9종** — fork 측이 오히려 구버전(자가검증 섹션 포인터 stale, LSP·peer_agents 미보유). fork→본체 후보 0건. 본체→fork 역방향 드리프트 정리는 별도 작업.
- **모델 선택 단일축 루브릭** — fork 의 단일축 small/medium/large 는 구버전이며 ADR-0003 이 결정론 파이프라인(§5.1~5.6)으로 이미 대체하며 명시 제외한 퇴행 항목. **재제안하지 않는다.**
- **본체가 이미 앞선 영역** — 계획 가시화 의무·옵션 단일수렴 skip 금지·대형 호출 분할·open_questions 경로·파괴 게이트 2단계 분리·회고 docs_sync 등은 본체가 선행. 역이식하면 퇴행.

### 검토 후 보류

- **cache-write 3시점 회귀 의무** — 캐시 특화 패턴. 본체 검증 전략의 "회귀 테스트 의무" 한 줄로 의미가 이미 커버되어 중복. 보류.
- **정량 스킵 기준 표 + 탐색표현 스킵금지 어휘** — 본체 SKILL §5.1 산문 스킵 기준 + §5.0 계획 가시성 의무 + §4.5 clarify 분기가 동등 효력 제공. 중복 가능성으로 이번 릴리즈 보류.

## 검토한 대안

- **별도 브랜치 신설** — ADR-0003 의 소비 프로젝트 일반화 흐름과 동일 릴리즈 단위이므로 동일 브랜치 적층을 택했다.
- **단순 토큰 치환** — 식별자를 강하게 동반한 후보(호출 실패 처리·graph 이월금지)는 치환만으로 잔여가 남아 본문 재작성으로 처리했다.
- **graph 이월금지를 protocol 본체에 박제** — graphify 가 opt-in add-on 이므로 상세 정책은 add-on docs 에 두고 본체 SKILL 에는 정책 한 줄만 두어 결합도를 낮췄다.

## 결과

- 본체 v1.1.0 → v1.2.0. `atp` plugin + marketplace + `atp-graphify` plugin(후보 #4 가 add-on docs 를 건드림) 동반 bump.
- 소비 프로젝트는 이 후속 역이식의 영향을 받지 않는다(본체 단독 릴리즈).
- ADR-0002 / ADR-0003 불변.

## 관련 문서

- [ADR-0003](./ADR-0003-consuming-project-generalization-backport.md) — v1.1.0 1차 역이식
- [agent-team-protocol.md](../development/agent-team-protocol.md) — §2.5, §4.4
- [documentation-guidelines.md](../development/documentation-guidelines.md) — analysis perspective
