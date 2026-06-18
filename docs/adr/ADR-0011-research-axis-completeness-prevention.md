---
kind: adr
adr_number: "0011"
title: research 단계 축-완결성(axis-completeness) 예방 게이트 신설 (§4.8) + research-advisor 자가검증 강화 (동명이인 disambiguation·JS-SPA 출처 흡수)
status: accepted
date: 2026-06-17
deciders:
  - template-maintainer
  - stzjungsoo
supersedes: []
related_commits:
  - (release/v2.2.0 브랜치 — origin/main 기반 신규 브랜치 커밋, PR→main 머지 시 SHA 확정)
---

# ADR-0011: research 단계 축-완결성 예방 게이트 (§4.8) + research-advisor 자가검증 강화

## 상태

**Accepted** — 2026-06-17. 세션 20260617-165603. ADR-0005(조사 출처 신뢰도 게이팅)·ADR-0008(report 스키마 v2 의 신뢰도 마커) 위에 적층. supersede 아님 — 기존 완결성-예방 클러스터(§4.3 design 시점 집합 전수 / §4.6 검증수단 / §4.7 AC 정식화)에 research 시점 꼭짓점 1개를 **추가**한다.

base atp 매니페스트 4개 `2.1.0` → `2.2.0` (minor). add-on atp-graphify 미변경(독립 버저닝).

---

## 맥락

ATP 의 완결성-예방 규약은 두 시점에 존재했으나 그 사이에 구조적 빈칸이 있었다:

- **§4.3 (집합 전수 체크 AC, design 시점)**: *요구에 명시된* 집합의 전수성을 design 시점에 예방한다. 그러나 어떤 카테고리 **축**이 애초에 요구에 잡히지 않으면 그 축에 대한 AC 자체가 생성되지 않는다.
- **§2.6 (다항목 산출물 전수 재검, 사후 시점)**: 결함이 *표면화된 후* 항목 지향으로 전수 재검을 발동한다. 그러나 축이 통째로 부재하면 재검할 항목이 0이라(결함 항목 자체가 없음) 발동되지 않는다.

따라서 "**카테고리 축 집합 자체의 완결성**" — research 시점에 *요구에 아직 잡히지 않은 축까지* 의 완결성 — 을 강제하는 규약이 ATP 에 없었다. 축 부재 → 항목 0 → §4.3·§2.6 어느 쪽도 미발동이라는 사각이 구조적으로 열려 있었다.

**촉발 증거 (hedge 보존)**: 타 소비 프로젝트의 다항목 카탈로그 audit 에서 한 카테고리 축이 통째로 누락(담당 worker 0)됐고, 사용자 의심이 우발적으로 전수 재검을 유발할 때까지 묻혀 있었다고 **보고됐다**. 이 누락·수치는 해당 프로젝트 보고자의 진술 기반이며 본 레포에서 직접 검증하지 않았다(§2.6 불확실성 보존 원칙 — uncertainty laundering 금지). 따라서 본 ADR 은 그 사고(事故) 수치를 사실로 단정하지 않는다. 단, **갭의 구조**(축 부재 → 항목 0 → 어느 규약도 미발동)는 보고자 진술과 독립적으로 위 §4.3/§2.6 분석만으로 식별 가능하며, 본 결정은 이 구조적 갭을 근거로 한다. §2.6 이 그 사례에서 미스를 잡은 것은 설계된 메커니즘이 아니라 사용자 의심 덕의 사고였다는 점이 핵심 동기 — 우발에 의존하던 검출을 설계된 보장으로 대체한다.

---

## 결정

### 결정 1 — 검출 방식: research-advisor 자가검증 항목 (전용 spawn·하이브리드 대비)

축-완결성 패스를 **research-advisor 의 취합 단계 자가검증 항목**으로 구현한다(`research-advisor.md` "자가 검증" 리스트의 5번 항목). 핵심 규율 3가지:

1. **독립 분류체계 ≥2개 교차참조(multi-modal sweep)**: 축을 단일 출처의 분류로 받지 않고, 서로 독립적인 분류체계 둘 이상(예: 공식 문서 모듈 분류 + 커뮤니티/생태계 토픽 택소노미)으로 축을 각각 도출해 교차참조한다. 한쪽 체계에만 있는 축 = 미완결 신호 → 보강 조사.
2. **축 집합 폐쇄-신뢰도 마커**: 축 *목록 자체* 에 기존 `source_confidence` 3-tier(`확인됨`/`추정`/`미확인`)를 재사용해 "이 축 목록이 닫혔다고 주장하지 않음" 을 산출에 명시한다. 신규 필드·신규 enum·4-tier 도입 없음.
3. **전수 열거 주장 금지**: "전수 열거했다"는 주장은 쓰지 않는다 — 개방 집합에서 그 주장은 누락을 부른 바로 그 과신을 재현한다. *결과*(완전한 목록)가 아니라 *방법*(독립 분류체계 ≥2개 교차참조)을 강제하고, 완결성의 *주장* 대신 도출 *방법* 을 산출에 박는다.

**고위험 카탈로그**: 정본성이 높거나 누락 비용이 큰 카탈로그는 분류체계별 sweep 을 `parallel-explorer` 로 병렬 수행할 수 있다 — **권장이지 강제 아님**. 전담 worker 를 신설하지 않는다.

**맹점의 명시 보존 + §9 사후승격 경로**: "축을 놓친 모델은 같은 축을 다시 놓칠 수 있다"는 맹점은 ≥2 독립 분류체계 교차참조로 *완화*되지만 *완전 제거되지는 않는다*. 이 맹점을 숨기지 않고 §4.8 본문에 명시 보존한다. 동일 유형 축 누락이 사후에 **재발**하면 §9 확장 트리거 레지스트리의 사후 승격 원칙에 따라 축-sweep 전담 worker 승격을 검토한다(예측 선제작이 아니라 관측 후 격상).

- **기각 대안 — 전용 spawn(축-sweep 전담 worker 즉시 신설)**: 비용 최고. 단일 관측(미검증 타 프로젝트 사고 1건)을 근거로 영구 인프라를 선제작하는 것은 §9 "예측 선제작 금지, 관측 후 격상" 원칙에 반한다. 재발이 실증되면 §9 경로로 승격할 여지를 남기는 편이 정합.
- **기각 대안 — 하이브리드(자가검증 + 조건부 전용 spawn 자동 트리거)**: 자동 트리거 조건을 지금 고정하면 그 조건 자체가 또 다른 누락 축이 된다(메타 과신). 자가검증으로 시작하고 §9 사후승격을 수동 판단 게이트로 두는 편이 더 보수적.
- **채택 사유**: (A) 자가검증이 비용 최저이고, (B) ≥2 교차분류 규율로 맹점을 실질 완화하며, (C) §9 사후승격으로 재발 시 격상 경로를 보존한다. 맹점을 제거됐다고 주장하지 않고 명시 보존하는 점이 본 결정의 정직성 핵심이다.

### 결정 2 — 배치 위치: 신규 §4.8 (완결성-예방 클러스터 합류)

축-완결성 규약을 프로토콜 신규 **§4.8 "카탈로그/열거형 축-완결성 예방 (research 시점)"** 로 둔다. 기존 완결성-예방 클러스터(§4.3 집합 전수 / §4.6 검증수단 / §4.7 AC 정식화)에 합류시키고, **삼각 상호참조 §4.8 ↔ §4.3 ↔ §2.6** 를 건다 — 셋이 완결성 예방을 시점·계기·대상 축에서 분담한다:

| 절 | 시점 | 계기 | 대상 |
|---|---|---|---|
| §4.3 | design | 사전 | 요구에 *명시된* 집합 |
| §4.8 | research | 사전 | 요구에 *아직 안 잡힌* 축 |
| §2.6 | 결함 표면화 후 | 사후 | 항목 |

**게이팅**: §4.8 은 열거형/카탈로그 산출(2개 이상 이름 붙은 항목을 축·카테고리로 나열)일 때만 발동한다(§4.3 와 동일 발동 조건). 라이브러리 API 조사·단건 사실 확인 같은 비열거 research 에는 걸지 않는다.

- **기각 대안 — §2.x(advisor 운영 규약) 배치**: §4.8 은 완결성 *예방 방법론* 이지 advisor 호출 판단 규약이 아니다. §4.3/§4.6/§4.7 과 같은 클러스터에 둬야 "완결성 규칙은 §4 에서 발견" 이라는 단일 거주지가 유지된다(§4.3 이 이미 §2.6 과 짝).

### 결정 3 — 부수 규칙 2건: 기존 인프라 흡수 (신규 어휘 도입 금지)

`research-advisor.md` 에 저위험 부수 규칙 2건을 기존 인프라에 흡수한다:

- **(B) 동명이인(homonym) disambiguation**: 같은 이름의 서로 다른 엔티티(동명 라이브러리·동명 repo·동명 도구)는 분류 전에 식별자(도메인/repo URL/패키지 ID)로 먼저 구분한 뒤 분류한다. 사전 분류규칙(research-advisor)과 §2.6 사후 전수 재검 위생 규칙(재검 worker 가 동명이인을 한 엔티티로 병합/혼동해 새 결함을 주입하지 않도록) 양쪽에 배치.
- **(C) JS-SPA 출처 치유 → `source_confidence` 게이트 흡수**: WebFetch 는 JS 를 실행하지 않고 parallel-explorer 도 브라우저 자동화를 보유하지 않으므로, 클라이언트 렌더로만 내용이 드러나는 SPA 출처는 표준 도구로 확인 불가다. 호스트가 브라우저 자동화를 보유하면 선택적으로 시도하되, 아니면 해당 항목을 기존 `미확인` 마커로 처리하고 `concerns` 에 사유를 남긴다.

- **기각 대안 — (C) 에 신규 검증 어휘(`needs_user_verification`) 도입**: 기존 `미확인` 마커로 충분하다. 신규 어휘는 source_confidence 3-tier 와 중복되는 두 번째 신뢰도 축을 만들어 drift 를 부른다. 기존 게이트 1줄 흡수로 처리.

### 결정 4 — 지금 minor bump + release-checklist 게이트

본 변경은 에이전트가 `${CLAUDE_PLUGIN_ROOT}/docs/development/agent-team-protocol.md` 로 Read 하는 **권위 런타임 레퍼런스**(§4.8)와 research-advisor 자가검증을 바꾸므로 소비자 동작에 영향 = **user-facing**. 따라서 base atp 매니페스트 4개를 `2.1.0` → `2.2.0` (minor) 으로 올리고, release-checklist §0–§6 게이트를 커밋 전에 통과시킨다.

- **기각 대안 — bump 생략(평문 메모로 이월)**: release-checklist §0 의 "이월 금지" 원칙에 정면 반한다(2026-06-09 → 2026-06-16 약 1주 방치 실증). `/plugin update` 는 manifest version 차이로만 갱신을 감지하므로, bump 이 소비자 추적 ref 에 도달하지 않으면 §4.8 이 무증상으로 미도달한다. 이월 시에도 추적 가능한 `release-pending` Open Item 으로만 격리한다.

---

## 영향

| 파일 | 변경 내용 | 비고 |
|---|---|---|
| `plugins/atp/docs/development/agent-team-protocol.md` §4.8 | 신규 절(축-완결성 예방 게이트) | 본 ADR 결정 1·2 의 구현 — **이미 구현됨** |
| `plugins/atp/docs/development/agent-team-protocol.md` §4.3 | §4.8 삼각 상호참조 1줄 | 이미 구현됨 |
| `plugins/atp/docs/development/agent-team-protocol.md` §2.6 | §4.8 cross-ref 확장 + (B) 동명이인 전수재검 위생 규칙 1줄 | 이미 구현됨 |
| `plugins/atp/agents/research-advisor.md` | (A) 축-완결성 자가검증 5번 항목 + (C) JS-SPA 흡수 1줄 + (B) 동명이인 분류규칙 1줄 + "3개→5개" prose 카운트 정정 | 이미 구현됨 |
| `plugins/atp/agents/parallel-explorer.md` | **무변경**(peer 드리프트 부재) | 결정 1 이 worker 책임을 확대하지 않음 — §11.1 교차 점검으로 무변경 확인 |
| base atp 매니페스트 4개 | `2.1.0` → `2.2.0` | `plugins/atp/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `plugins/atp/.codex-plugin/plugin.json`, `.codex-plugin/marketplace.json` |
| `docs/adr/ADR-0011-*.md` (본 문서) | 신규 ADR | documentation-advisor |
| `docs/adr/index.md` | ADR-0011 행 추가 | documentation-advisor |
| add-on atp-graphify 매니페스트 2개 | 무변경(독립 버저닝) | — |

소비 프로젝트 영향: 신규 세션부터 research-advisor 가 열거형/카탈로그 산출 시 축-완결성 패스를 수행한다. 과거 research 산출은 소급 재검 대상이 아니다(§4.8 은 새 게이트지 기존 산출을 무효화하지 않음). `source_confidence` 3-tier 불변이라 기존 산출 frontmatter 호환 — 마이그레이션 불요.

---

## 검증

설계 AC 10개(세션 20260617-165603 design.md §검증 포인트) — verification-advisor 독립 재실행 결과 **PASS 10/10, 양가 판정 0**. 핵심:

- **삼각 상호참조 4방향 링크**(§4.8→§4.3, §4.8→§2.6, §4.3→§4.8, §2.6→§4.8) 모두 존재 — 절 본문 범위를 `awk` 로 한정해 다른 절의 동일 토큰 오매치 배제(AC-1) + 의미 무결성 수동 판정(AC-2).
- **base 매니페스트 4개 version 상호 동일 불변식 == `2.2.0`** — `jq -r .version | sort -u` 가 1줄(AC-3).
- **"전수 열거" 금칙어 부재 + "닫혔다고 주장하지 않음" 긍정형 앵커 존재** — AC-4(금칙어 부재)↔AC-5(양방향 계약 앵커)로 동의 표현을 의미 차원에서 차단.
- **research-advisor 자가검증 5항목** + 5번이 §4.8 게이팅 어휘 포함(AC-6).
- **peer 대칭 불변식**(research-advisor ↔ parallel-explorer 양방향 선언, AC-7) + **parallel-explorer 무변경**(`git diff --name-only` 빈 출력, AC-8).
- **(B)(C) 흡수 — 신규 어휘 `needs_user_verification` 부재**(== 0, AC-9) + **게이팅 명시**(비열거 미발동, AC-10).

모든 AC 는 자기 work-session 트리 카운트에 의존하지 않는 tracked 파일 대상 또는 불변식으로 정식화돼 §4.7 시점-드리프트 함정을 사전 차단했다.

> **release-routing 확정**: 커밋 게이트는 `release/v2.2.0`(origin/main 기반 신규 브랜치)로 확정됐다(세션 20260617-165603 plan 게이트). 현 로컬 `feat/community-health-files` 가 origin/main 대비 stale(behind 1·이미 PR#10 머지)이라 §0 상 stale 브랜치 단독 bump 는 `/plugin update` 미도달을 재현하므로 회피한다. 2.2.0 bump 은 PR→main 으로 소비자 추적 ref 에 도달한다.

---

## 관련 문서

- [ADR-0005](./ADR-0005-orchestrator-bidirectional-flow-control.md) — 조사 출처 신뢰도 게이팅 도입(본 ADR 의 (C) JS-SPA 흡수가 그 게이트 위에 1줄 적층)
- [ADR-0008](./ADR-0008-platform-neutral-model-policy.md) — report 스키마 v2 의 신뢰도 마커 체계(§4.8 축 폐쇄-신뢰도 마커가 같은 `source_confidence` 3-tier 재사용)
- [plugins/atp/docs/development/agent-team-protocol.md](../../plugins/atp/docs/development/agent-team-protocol.md) — §4.8 본문(축-완결성 예방), §4.3/§2.6 삼각 상호참조, §9 사후승격 원칙
- [docs/development/release-checklist.md](../development/release-checklist.md) — §0 릴리즈 트리거(결정 4 bump 의무의 근거), §6 카테고리 index 등록
