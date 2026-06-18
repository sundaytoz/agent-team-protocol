---
kind: adr
adr_number: "0012"
title: backport 출처 식별자 self-grep 게이트 — 일반화 게이트 선언(ADR-0004/0005)을 실행 경로로 회수
status: accepted
date: 2026-06-17
deciders:
  - template-maintainer
  - stzjungsoo
supersedes: []
---

# ADR-0012: backport 출처 식별자 self-grep 게이트

## 상태

**Accepted** — 2026-06-17. 세션 20260617-174819. ADR-0004(일반화 게이트 선언)·ADR-0005(동) 위에 적층 — supersede 아님. 두 ADR 이 선언(WHAT)한 게이트를 실행 경로(WHO/WHEN/HOW)로 회수한다.

## 맥락

ATP 는 self-dogfooding 으로 소비 프로젝트 운영 경험을 ADR·런타임 정본·TEMPLATE_DEV 에 역이식(backport)하는 것이 상시 워크플로우다(ADR-0003→0004→0005). 그 과정에서 출처 프로젝트 식별자(slug·도메인 동반어·코드 심볼)가 산출물에 따라 들어온다.

ADR-0004:38·ADR-0005:46 은 "소비 프로젝트 식별자를 본문·메타·파일명 어디에도 남기지 않고 commit 전 residual 0 을 확인한다"는 일반화 게이트를 **본문에 선언**했다. 그러나 그 확인이 release-checklist(§0~§6)·documentation-advisor·design-advisor 어디에도 실행 가능한 항목(self-grep AC)으로 회수되지 않았다 — 정의(WHAT)와 집행(WHO/WHEN/HOW)의 분리. 결과적으로 같은 문서군(ADR-0008/0009/0011·TEMPLATE_DEV·런타임 정본 §4.2)이 코드 심볼·소비 프로젝트 slug·도메인 동반어 6건을 누출했고(세션 20260617-174819 누출 감사), 검출은 ADR-0011 이 비판한 바로 그 "우발적 사용자 지목" 으로만 일어났다. 자기 ADR 의 메타 교훈(우발 검출을 설계된 보장으로 대체)이 자기 게이트에 미적용된 자기참조적 결함이다.

backport 는 ATP 의 일회성이 아닌 반복 작업유형이므로(ADR-0003→0004→0005 세 번 모두 동일 누락 패턴), 출처 식별자 동반은 본질적 부작용이고 게이트 부재는 (b) 재발 패턴 + (c) 프로토콜 허점이다.

## 결정

일반화 게이트 선언을 다음 실행 경로로 회수한다(신규 §4.x 본문 신설 없이 기존 인프라에 집행 지점만 추가 — 신규 어휘 도입 0):

1. **release-checklist.md 신규 §7 "역이식(backport) 산출물 출처 식별자 잔류 0"** — backport 변경에 한해 commit 전: (1) 이번 작업이 인용한 출처 토큰을 수집(고정 리스트 아님), (2) diff 추가 라인 + 신규 파일명에 character-class self-exclusion 을 적용한 `git grep -niE` 실행, 0 hit(exit 1) 기대, (3) 잔류 시 placeholder 치환 또는 본문 재작성(hedge·교훈 골격 보존). §0~§6 의 "검증 명령 + 기대값" 형식 답습.
2. **documentation-advisor 자가검증 4번(backport 한정)** — backport 문서화 시 출처 식별자 잔류 self-grep 확인. 절차는 §7 링크.
3. **design-advisor 자가검증 4번(일반화·backport 설계 한정)** — 일반화 배경 서술 설계 시 식별자 익명화 책임 명시. 절차는 §7 링크.
4. **ADR-0004:38·ADR-0005:46 에 집행 링크** — 두 선언처가 "집행 경로: release-checklist §7 + 본 ADR-0012" 로 forward 링크. 선언처→집행처 화살표 완성.

**§4.6/§4.7 자기적용**: §7 의 self-grep 명령은 (a) 현재 레포에서 실제 실행해 0 hit/exit 1 을 확인하고(§4.6), (b) 고정 토큰 리스트가 아니라 "이번 작업이 인용한 토큰 수집" 동적 절차로 시점 안정성을 확보하며(§4.7-1), (c) self-exclusion 으로 명령 줄 자기매치를 차단한다(표현 견고성 — §4.7-2 의 양방향 계약 변형).

- **기각 대안 — 신규 프로토콜 §4.9 본문 신설**: 게이트는 §4.6(검증수단)·§4.7(AC정식화) 클러스터의 *적용 사례*이지 새 완결성 축이 아니다. release-checklist(release 시점)·agent 자가검증(작성 시점)이 자연 거주지다. 본문 신설은 §4 클러스터에 중복 거주지를 만든다.
- **기각 대안 — 고정 토큰 블랙리스트 grep**: 다음 backport 의 새 출처 토큰을 놓친다(§4.7 표현 견고성 위반). "이번 작업이 인용한 토큰 수집" 동적 절차가 시점 독립적.
- **기각 대안 — 소비 프로젝트로 전파**: 소비 프로젝트는 자기 식별자 사용이 정상. 게이트는 ATP 소스 레포 backport 에만 scope.

## 영향

| 파일 | 변경 내용 | 비고 |
|---|---|---|
| `docs/development/release-checklist.md` §7 | 신규 절(backport 출처 식별자 잔류 0) | 순번 append, §0~§6 무변경 |
| `plugins/atp/agents/documentation-advisor.md` | 자가검증 4번(backport 한정) append | 자가검증 항목 추가는 계약 호환 |
| `plugins/atp/agents/design-advisor.md` | 자가검증 4번(일반화·backport 설계 한정) append | 동 |
| `docs/adr/ADR-0004-*.md` | "집행 경로" 링크 1줄 적층 | append-only 보강(supersede 아님) |
| `docs/adr/ADR-0005-*.md` | "집행 경로" 링크 1줄 적층 | 동 |
| `docs/adr/ADR-0012-*.md`(본 문서) | 신규 ADR | — |
| `docs/adr/index.md` | ADR-0012 행 추가 | — |
| MEMORY(레포 전용) | `backport-self-leak-grep-gate` 신규 항목 + 인덱스 | §12 절차 |

manifest version: 본 변경이 번들 런타임(`agent-team-protocol.md`)을 바꾸지 않고 루트 release-checklist + agent 자가검증만 바꾼다. agent 자가검증 변경은 번들 `plugins/atp/agents/` 소비 = user-facing 이므로 release-checklist §0~§6 + §4(version invariant) 게이트를 통과시키고 base atp 매니페스트 bump 여부를 release 시점에 판단한다(documentation-advisor 가 backport 시 분기 수행 = 소비자 동작 변화).

## 검증

세션 20260617-174819 design2.md §검증 포인트 AC-G1~G7 — verification-advisor 독립 재실행. 핵심: self-grep 명령 현재 레포 실제 실행 0 hit/exit 1(AC-G1), 게이트 텍스트의 §4.6/§4.7 자기적용 self-audit(AC-G3), 집행 지점 전수 존재(AC-G4), ADR-0012 index 등록(AC-G5).

## 관련 문서

- [ADR-0004](./ADR-0004-consuming-project-generalization-backport-followup.md) — 일반화 게이트 선언처(본 ADR 이 그 집행 경로)
- [ADR-0005](./ADR-0005-orchestrator-bidirectional-flow-control.md) — 일반화 게이트 선언처 + 불확실성 보존 원칙(hedge 골격 보존 근거)
- [ADR-0011](./ADR-0011-research-axis-completeness-prevention.md) — "우발 검출 → 설계된 보장 대체" 메타 교훈(본 ADR 이 그 교훈의 backport 특화 적용) + §검증 self-grep AC 모범
- [release-checklist.md](../development/release-checklist.md) — §7 집행 절 본문
- [agent-team-protocol.md](../../plugins/atp/docs/development/agent-team-protocol.md) — §4.6 검증수단 실행 / §4.7 AC 정식화(게이트 self-grep 이 만족) / §12 회고→MEMORY
