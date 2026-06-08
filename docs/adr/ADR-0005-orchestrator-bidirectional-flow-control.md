---
kind: adr
adr_number: "0005"
title: v1.3.0 — orchestrator 양방향 흐름 제어 (backward 회귀 재디스패치 · forward 트랙 설계 게이트) + 시그널 세탁 방지 + 조사 출처 신뢰도 게이팅
status: accepted
date: 2026-06-08
deciders:
  - template-maintainer
  - stzjungsoo
supersedes: []
---

# ADR-0005: v1.3.0 — orchestrator 양방향 흐름 제어 + 시그널 세탁 방지 + 조사 출처 신뢰도 게이팅

## 상태

**Accepted** — 2026-06-08. ADR-0004(v1.2.0) 위에 적층. supersede 아님.

---

## 맥락

운영 세션 메타분석에서 orchestrator 의 흐름 제어가 **단방향(forward-only)** 이라는 구조적 공백이 드러났다. 관측된 실패 사슬:

1. 조사 단계가 1차 출처 차단(403/404/요청 실패)으로 추정 데이터를 산출하면서도 `concerns: []` 로 반환 — 불확실성이 산출물에 보존되지 않음.
2. orchestrator 가 그 산출을 상위 보고서로 격상하며 "추정" 을 "실제 기반" 으로 서술 — 계층 간 **불확실성 세탁(uncertainty laundering)**.
3. 사용자가 다항목 산출물 중 **한 항목의 사실 오류를 지적** — 이를 "사용자가 도메인 지식이 좋다" 류 **positive 시그널로 오분류**.
4. positive 분류 탓에 사용자 지적 3단계 판단(§2.3) 진입 자체가 차단 → 동일 출처·동일 생성방식으로 만든 나머지 항목 재검 없이 **지적된 항목만 국소 패치**.
5. 별개로, 한 요청을 복수 트랙으로 분해할 때 **"기능적 독립"** 만으로 한 트랙을 다른 트랙의 조사·설계 완료 전에 구현 선행 — 두 트랙이 동일 상태 전이를 공유(결합)했음에도. forward 척추(설계 완료 후 구현)를 트랙 병렬화가 우회.

핵심 진단: orchestrator 의 역할이 forward 디스패치에 치우쳐, (a) 결함 표면화 시 **어느 단계로 회귀할지** 판정하는 backward 제어와 (b) 트랙 분할 시 **설계 게이트를 언제 공유할지** 판정하는 forward 규율이 모두 규정 공백이었다. 조율·지휘 담당자라면 양방향 흐름 제어가 본분이다.

핵심 제약은 ADR-0003/0004 과 동일한 **일반화 게이트**다 — 동기가 된 소비 프로젝트 세션의 도메인 식별자(기능명·엔티티명·외부 API)를 본문·메타문서·파일명 어디에도 남기지 않는다. 본 ADR 과 신설 섹션의 배경 서술은 추상 패턴(다항목 사실 카탈로그·공유 상태 전이)으로만 기술한다.

## 결정

v1.3.0 으로 다음을 추가한다. 모두 신규 섹션 또는 순번 append 라 기존 섹션 하향 재번호가 없다.

1. **§2.6 결함 표면화 시 회귀 단계 판정 (backward re-dispatch)** — `agent-team-protocol.md` 신규 섹션. (a) 발원 단계 진단(표면화 위치 ≠ 발원), (b) 발원 단계 advisor 재호출로 산출물 전체 재검 — 국소 패치는 발원=현재 위치일 때만, (c) 하류 재실행, (d) `report.md` `regression` 기록. **다항목 산출물의 단일 항목 교정 → 동일 출처/생성방식 전수 재검 동반** + **계층 간 불확실성 보존(격상 시 hedge 유지)** 포함.
2. **§2.7 분할 트랙의 설계 게이트 규율 (forward phase-gate)** — `agent-team-protocol.md` 신규 섹션. 독립성을 **공유 자원(DB 엔티티·상태 전이·UX 플로우·계약) 수준**에서 판정. 결합 트랙은 설계 게이트 공유, 독립 확인 시 병렬 허용, 결합인데 선출시 필요 시 재작업 리스크 명시해 `AskUserQuestion` 위임. 구현 진입 전 자가 점검 2항.
3. **§2.3 시그널 세탁 금지** — "자주 저지르는 오류" 목록 append. 사용자의 사실·데이터 오류 지적은 산출 단계 품질의 negative 시그널이며 positive 로 재프레이밍 금지(positive 세탁이 §2.6 전수 재검·개선 경로를 무력화).
4. **§8 `regression` 보고서 필드** — 옵셔널(backward-compatible, schema_version 유지). 발원/표면 단계·전수 재검 여부·하류 재실행 범위 기록.
5. **research-advisor 출처 신뢰도 게이팅** (v1→v2) — 사실 항목별 신뢰도 마커(`확인됨`/`추정`/`미확인`), frontmatter `source_confidence: high|mixed|low`, 1차 출처 차단 fallback 시 `concerns: []` 반환 금지, 추정·미확인의 "확정/실제" 격상 금지. 자가검증 4번 신설.
6. **retrospective-advisor 시그널 세탁 경계** (v1→v2) — 회고에서 사실 오류 지적의 positive 오분류를 negative(structural 후보)로 재분류.

일반화 게이트는 추가 라인 + 신규 파일명에 적용하며 식별자 residual 0 을 commit 전 확인한다.

### 범위 밖 (이번에 하지 않음)

- **연구/시드 데이터 사실성 검증 게이트(F4)** — 코드 검증(L1/L2)과 별개로 외부 사실 데이터가 권위 시드가 될 때의 사실성 AC. 소비 프로젝트 `verification-strategies.md` 편집형 영역이라 본체에는 §2.6 불확실성 보존 원칙만 두고 구체 게이트는 후속.
- **forward 파이프라인 자동화 강제** — §2.7 은 판정 규율이지 단계 자동 차단이 아니다. 게이트 강제 메커니즘은 별도 검토.

## 검토한 대안

- **§2.6/§2.7 을 §2.3 안에 흡수** — §2.3 은 발화 분류, 신설 두 절은 흐름 제어(회귀·게이트)로 책임 축이 달라 별 섹션으로 분리. §2.3 에는 세탁 금지 1줄만 연결.
- **research 신뢰도를 프로토콜 본체에 박제** — advisor 산출 계약은 agent 파일 책임이라 마커·게이팅은 research-advisor.md 에 두고, 본체에는 §2.6 불확실성 보존 원칙으로만 연결.
- **schema_version 상향** — `regression` 은 옵셔널 추가라 §8 진화 규칙상 schema_version 유지(backward-compatible).

## 결과

- 본체 v1.2.0 → v1.3.0. `atp` plugin + marketplace bump. graphify add-on 무변경(미관여)이라 `atp-graphify` bump 없음.
- research-advisor / retrospective-advisor agent_version 1 → 2.
- ADR-0002 / 0003 / 0004 불변.
- 소비 프로젝트는 plugin 업데이트로 반영(본체 단독 릴리즈).

## 관련 문서

- [ADR-0004](./ADR-0004-consuming-project-generalization-backport-followup.md) — v1.2.0 후속 역이식
- [agent-team-protocol.md](../development/agent-team-protocol.md) — §2.3, §2.6, §2.7, §8
- [research-advisor.md](../../agents/research-advisor.md) — 출처 신뢰도 게이팅
- [retrospective-advisor.md](../../agents/retrospective-advisor.md) — 시그널 세탁 경계
