---
kind: adr
adr_number: "0013"
title: protocol.md 진입 강제로드 토큰 감축 — 파일내 코어 구획 + on-demand 라우팅 (물리분할 회피)
status: accepted
date: 2026-06-18
deciders:
  - template-maintainer
  - stzjungsoo
supersedes: []
---

# ADR-0013: protocol.md 진입 강제로드 토큰 감축 — 파일내 코어 구획 + on-demand 라우팅 (물리분할 회피)

## 상태

**Accepted** — 2026-06-18. 세션 20260618-103431. supersede 아님 — `agent-team-protocol.md` 의 §1~§14 본문·번호·텍스트를 무수정으로 유지하고 **로딩 전략만** 바꾼다. ADR-0003·ADR-0009 가 확립한 "§N 번호 = 사실상 공개 계약" 원칙(재번호 이력) 위에 적층한다.

## 맥락

`/atp:task` 진입 시 SKILL §1 이 `agent-team-protocol.md`(853줄/~31K 토큰)를 **매번 전문(全文) 강제로드** 한다. 마이크로 편집(1파일 수정 등) 같은 핫패스조차 31K 를 선지불하는 구조였다. 사용자 원 요청: *"플러그인 원본 자체가 너무 무거워. 필요할 때 연관 내용을 불러올 수 있도록 구조를 개선하고 싶어"* — progressive disclosure(필요 시 로드)로의 전환 요구다.

요구사항 단계(requirements.md)가 "무거움"을 4축으로 분해한 결과 지배적 비용은 **D1 런타임 컨텍스트 토큰(진입 강제로드)** 으로 확정됐고(Q1=A, Q5=A), agents 중복(D2)·디스크(D3)·인지부담(D4)은 후순위로 분리됐다.

핵심 제약은 **§N 앵커가 사실상 공개 API** 라는 점이다. §N 인용이 16파일 164건에 산재하며 — ADR 12건 전부 + agents 13파일 + docs 다수 — 특히 ADR-0008/0009 는 재번호된 **옛 절번호(§1.1~§1.6)** 까지 인용한다. 물리 분할은 이 인용망을 광범위하게 단절시켜 결정이력 문서(ADR)의 사후수정을 강제한다 — append-only 원칙과 정면 충돌하는 민감 비용.

또 다른 제약은 **게이트 강제력 보존(R1)** 이다. §6 파괴적 조작 게이트·SKILL §9 종료조건·§2.6 회귀판정처럼 "안 불러오면 위반을 못 잡는" 규칙을 지연로드 대상으로 두면, orchestrator 가 happy-path 만 로드하고 게이트를 누락해 게이트가 사실상 옵션이 되는 실패모드가 생긴다.

## 결정

**Q2=B(로딩 전략만 변경) + Q3=A(필수 상주 코어 명시) + Q4=A(slug↔§N 매핑 + 회귀게이트)** 를 채택한다. 물리분할·신규파일·git mv 는 **0건**.

1. **물리분할 회피, 단일파일 유지** — `agent-team-protocol.md` 는 단일 파일로, 본문 §1~§14 번호·텍스트를 **무수정** 유지한다.
2. **파일 선두 코어 구획 삽입** — `## 1.` 직전(인트로 다음)에 `<!-- atp:core:begin -->` ~ `<!-- atp:core:end -->` 구획(52줄)을 삽입한다. HTML 주석 마커라 `#` 헤더·§N 번호 카운트에 영향 0. 코어는 **원문 인용·포인터만** 두고 규약 내용을 재서술하지 않는다. 7개 항목(`<!-- atp:core:item N -->` 앵커):
   - **C1 역할정의 요약**(상세 §1) — Orchestrator 직접작업 금지 등.
   - **C2 호출모델 불변**(상세 §2) — Tier-3 만 Agent 보유·worker 재귀금지·상위 advisor 동시호출 금지.
   - **C3 §6 파괴적 게이트 압축형** — 게이트 6항목 + "advisor/worker 직접수행 금지, orchestrator 사용자 확인 후만" + 2단계 분리 포인터.
   - **C4 게이트 통과 후 롤백 원칙**(상세 §6).
   - **C5 항상적용 체크리스트** — 세션 종료조건(SKILL §9)·회귀판정(§2.6)·plan-gate(§2.7) "트리거 무관 항상 적용" 명시.
   - **C6 라우팅 인덱스 표** — 트리거 → 대상 §헤더 + offset 힌트.
   - **C7 slug↔§N 매핑 + 신규 섹션 규칙**.
3. **SKILL §1 재작성** — "전문 읽기" → "코어 구획만 Read + 라우팅 인덱스가 가리키는 §섹션만 §헤더 grep 위치확정 후 on-demand Read". 마이크로 편집은 코어만으로 진행(전문 로드 0).
4. **라우팅은 §헤더 기준, offset 은 힌트** — 본문 편집 시 offset 이 드리프트하므로 라우팅 인덱스는 `## N.` §헤더 grep 으로 위치를 확정하고 offset 은 편의 힌트로만 둔다(드리프트 내성).
5. **회귀방지(Q4=A)** — 코어 C7 에 slug↔§N 매핑(번호=slug, 신규 섹션은 §14 다음 정수로만 추가·재배열 금지) + `docs/development/release-checklist.md` §8 "끊긴 §N 인용 0" 점검 절 신설.

**근거 — 왜 물리분할을 안 했나(핵심)**: §N 앵커가 공개 API 이므로 물리분할은 16파일 164건 인용을 광범위 단절시키고 ADR 사후수정을 강제한다. B 안은 §N 불변으로 **끊긴 인용 0 + ADR 수정 0 + 신규파일 0** 으로 동일 토큰 목표를 달성한다.

**Q3=A 보강**: 게이트(§6)·종료조건(SKILL §9)·호출불변·회귀판정을 트리거 무관 "항상 상주 코어"로 강제해, 지연로드 누락으로 게이트가 무력화되는 실패모드(R1)를 **구조적으로 차단**한다.

## 영향

| 파일 | 변경 내용 | 비고 |
|---|---|---|
| `plugins/atp/docs/development/agent-team-protocol.md` | 선두에 코어 구획 52줄(+53, C1~C7 + item 앵커 7개) 삽입 | 본문 §1~§14 무수정. 853→906줄 |
| `plugins/atp/skills/task/SKILL.md` | §1 "전문 읽기"→"코어+on-demand" 재작성 | +15/-2. SKILL 내부 §N 인용 전부 보존(§N 불변) |
| `docs/development/release-checklist.md` | §8 "끊긴 §N 인용 0" 점검 절 신설 | +15. 회귀 게이트 |
| `docs/architecture/file-map.md` | protocol.md 설명에 코어 구획(진입 로딩 구조) 한 줄 보강 | 구조 설명 동기화 (이력 아님) |
| `docs/adr/ADR-0013-*.md`(본 문서) | 신규 ADR | — |
| `docs/adr/index.md` | ADR-0013 행 추가 | — |

manifest version: 본 변경은 번들 런타임(`agent-team-protocol.md`)과 번들 SKILL(`task/SKILL.md`) 의 **로딩 동작**을 바꾼다 = user-facing(소비자 동작 변화). 역호환: 기존 설치 번들은 옛 SKILL(전문 읽기)로 동작 — 무해(더 많이 읽을 뿐). §N 번호 불변이라 기존 work-session 보고서·ADR 인용 전부 유효. base atp 매니페스트 bump 여부는 release-checklist §0~§6 게이트 + §4(version invariant)를 통과시키고 release 시점에 판단한다.

## 검증

세션 20260618-103431 design.md §검증 포인트 AC-1~AC-6 + release-checklist §8 추가 점검 — verification-advisor 독립 재실행, overall PASS. 핵심:

- **AC-1**(코어 집합 전수): `grep -c 'atp:core:item' agent-team-protocol.md` == **7**(item 1~7 전수). PASS.
- **AC-2**(헤더 무변경): `diff <(git show HEAD:...|grep -E '^#{2,4} [0-9]') <(grep -E ...)` 출력 0 — 본문 §1~§14 헤더 텍스트 집합 완전 동일. PASS.
- **AC-3**(끊긴 §N 인용 0, FR-4): 동일트리 정규화 재실행으로 개선 전·후 모두 끊긴 인용 0. PASS. (orchestrator 제시 원문을 좌변 working↔우변 HEAD 혼용 시 1..14 거짓양성 — §4.7 AC 정식화 결함으로 verification concerns 분리 기록.)
- **AC-4**(토큰 감축, FR-1/NFR): 코어 **52줄**(전문 906줄의 5.7%, ~2.6K 토큰 추정) — 853줄/~31K 전문 대비 **약 94% 감축**(목표 ≥70% 충족).
- **AC-5**(게이트 보존, FR-3/R1): C3 §6 게이트 6항목 + "직접수행 금지+사용자확인" + C5 SKILL §9 종료조건 포인터가 트리거 무관 "항상 적용"으로 코어 상주. PASS.
- **AC-6**(SKILL §N 무단절, R3): SKILL §N 인용 전부 본문 헤더에 실존(§0 만 SKILL-로컬 가드). 끊김 0. PASS.

verification concerns(이번 변경의 결함 아님 — 인프라 갭): 통합 verify 스크립트 부재 + `verification-strategies.md` 경로 불일치는 orchestrator 반환.

## 기각 대안

- **A 물리 분할(§섹션군별 파일)**: §N 인용 16파일 164건 광범위 단절, ADR 사후수정 강제(민감), 신규파일/git mv 다수. B 가 0 분할로 동일 토큰 목표를 달성하므로 기각.
- **C 하이브리드(콜드섹션만 분리)**: §8/§11 인용(ADR-0003/0005/0006/0008/0009 등)이 신파일로 이동 → 인용 일부 갱신·ADR 터치 발생. 차선이나 ADR 무수정 이점을 잃어 기각.
- **Q3-B on-demand 게이트(게이트도 조건부 Read)**: "파괴조작 직전 §6 Read" 를 orchestrator 가 누락하면 게이트 무력화(R1 발동). 기각.
- **Q4-B 일괄 sweep 갱신 / Q4-C 리다이렉트 맵**: B 안에서 §N 번호 불변이라 불필요. 기각.

## 관련 문서

- [ADR-0003](./ADR-0003-consuming-project-generalization-backport.md) — §N 재번호(섹션번호 충돌 회피) 이력 → "§N = 공개 계약" 전제의 출처
- [ADR-0009](./ADR-0009-bundle-runtime-platform-neutralization.md) — §1.1~§1.6 옛 절번호 인용 보유 → 물리분할 회피 근거(인용망 단절 대상)
- [release-checklist.md](../development/release-checklist.md) — §8 "끊긴 §N 인용 0" 회귀 게이트 본문
- [agent-team-protocol.md](../../plugins/atp/docs/development/agent-team-protocol.md) — 코어 구획(`atp:core:begin`~`end`, C1~C7) + 본문 §1~§14
- [file-map.md](../architecture/file-map.md) — protocol.md 코어 구획 진입 로딩 구조 설명
- 세션 산출: `.atp/work-session/20260618-103431/{requirements,design,verification}.md`
