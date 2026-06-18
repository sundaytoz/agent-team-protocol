---
kind: development
title: Capability Tier 와 호스트 자가판정
description: ATP 가 호스트 CLI 의 subagent capability 를 자가판정해 위임 토폴로지(Tier A / A-flat / B)를 결정하는 규칙. 호스트 고유 문법·모델 슬러그는 호스트 위에서 실행 중인 에이전트가 자율 적용한다.
owner: template-maintainer
stability: draft
last_reviewed: 2026-06-11
---

# Capability Tier 와 호스트 자가판정

## 0. 원리 — 워크플로우 강제 ≠ 도구 강제

ATP 는 **워크플로우**(phase 척추 · 파괴적 조작 게이트 · report 스키마 · 검증규율)를 강제하는 프로토콜이지, 특정 호스트 CLI 의 도구 사용을 강제하는 프로토콜이 아니다. 따라서 본 문서는 호스트 플랫폼을 이름으로 열거하지 않는다.

- 에이전트는 자기 호스트 CLI 위에서 실행 중이므로 호스트의 **호출 문법 · 지침파일 규약 · 모델 라인업 · env/경로 변수 · 배포 단위를 스스로 안다.** 이들은 에이전트가 자율 적용한다.
- 프로토콜이 판정해야 하는 것은 단 하나 — **호스트의 subagent capability** 다. 이것이 위임 토폴로지(Tier)를 결정한다 (§3 자가판정).
- 어떤 호스트에서든 게이트 · report 스키마(프로토콜 §8) · 검증규율은 동일하게 적용된다 — 이들은 호출 토폴로지와 독립이다.

> 배경: ATP 는 Claude Code 에서 출발한 프로토콜이며, 한때 특정 3사 CLI 의 capability 를 본 문서에 열거했다. 그 실측 데이터는 ADR-0009 부록에 동결 보존되어 있다 (§8).

## 1. 논리 추상 (호스트 중립)

### 1.1 공통 명령 식별자

ATP 내부의 공통 명령 식별자는 `task`, `init` 이다. 스킬 파일명·프로토콜 설명·내부 설계 문서는 이 중립 이름을 사용한다. 실제 사용자 입력 문법(접두 토큰·namespace 표기)은 호스트 플랫폼이 결정하며, 에이전트는 자신이 이번 세션에서 호출된 토큰을 그대로 안내에 사용한다.

### 1.2 공통 산출물 경로

> **현재 권위 경로**: `.atp/work-session/<sid>/`
>
> 새 세션·문서·구현 모두 이 경로를 기본값으로 사용한다. (F-3PLAT-3 single-read 전환 완료)

> **legacy**: `.claude/work-session/` 은 이전 버전의 산출물 경로다. `init` 의 `atp:migrate` 블록으로 자동 이관된다. 신규 프로젝트는 이 경로를 사용하지 않는다.

### 1.3 논리 환경 변수

공통 문서에서는 논리 변수명을 사용한다. 호스트 실변수는 에이전트가 자기 호스트의 변수로 해석한다.

| 논리 변수 | 의미 | 호스트 해석 |
| --- | --- | --- |
| `${ATP_PROJECT_DIR}` | 소비 프로젝트 루트 | 호스트의 프로젝트 루트 변수/경로 자율 적용 |
| `${ATP_PLUGIN_ROOT}` | 설치된 ATP 플러그인 루트 | 호스트의 플러그인/확장 루트 변수 자율 적용 |

## 2. Capability Tier 정의 (capability 기반 — 호스트 독립)

- **Tier A** = 서브에이전트 spawn 가능 + spawn 된 subagent 의 재-spawn 가능 → ATP 3-tier 팀(orchestrator + advisor + worker) 완전 동작. 2단 위임 체인(orchestrator→advisor→worker) 지원.
- **Tier A-flat** = spawn 은 되나 subagent→subagent 재귀 금지인 호스트용 변형. orchestrator 가 advisor 와 worker 를 **모두 직접** 호출하는 평탄 구조(1단 fan-out). 게이트·report 스키마(§8)·검증규율 전량 유지.
- **Tier B** = 단일 agent (spawn 불가/미확인) → orchestrator 가 protocol phase 를 순차 self-checklist 로 수행. 병렬 advisor·worker 만 격하, 나머지 규율 유지. **spawn 자가판정 불가/실측 실패 시 안전 폴백.**

> **spawn = invocation 기록 의무**: spawn 된 subagent 는 capability tier 와 무관하게 report 스키마(프로토콜 §8) invocation 으로 기록한다 — layer + parent_invocation_id 필수. 한 호스트 CLI 의 운영 전사(20260610-154723)에서 subagent 2개 spawn 이 report Invocations 에 누락된 사례가 본 의무 명문화의 계기다(§8 위반 — 원문은 ADR-0009 부록 F).

## 3. Capability 자가판정 절차

orchestrator(메인 에이전트)는 ATP task 진입 시 자기 호스트의 capability 를 1회 자가판정한다. 플랫폼 이름이 아니라 **capability 질문**으로 판정한다 — 목록에 없는 호스트도 자연 커버된다.

```
[진입] orchestrator 가 자기 호스트 capability 를 자가판정
  │
  ├─ Q1. 내 호스트가 subagent 를 spawn 할 수 있는가?
  │     ├─ 모름/불가 ──────────────► Tier B (단일 agent 순차 self-checklist — §5)
  │     └─ 가능 ─┐
  │             │
  │   Q2. spawn 된 subagent 가 다시 subagent 를 spawn 할 수 있는가? (재귀)
  │             ├─ 불가(재귀 금지) ──► Tier A-flat (orchestrator 직접 fan-out — §4)
  │             └─ 가능 ────────────► Tier A (2단 위임: L1→L2→L3)
  │
  ├─ [고지] 비-A tier 면 1줄 고지
  │        ("Tier A-flat 평탄 위임 모드" / "Tier B 격하 모드 — 순차 self-checklist")
  │
  └─ [불변] 어느 tier 든: 파괴적 조작 게이트(프로토콜 §6) · report 스키마(§8) ·
            phase 완료 아티팩트 기준(§13) · forward phase-gate(§2.7) · 집합 전수 AC(§4.3) 유지.
```

판정 근거는 에이전트 자신의 런타임 지식(자기 도구 목록·호스트 문서·과거 동작)으로 충분하다. **확신이 없으면 안전 폴백** — spawn 여부 불확실 → Tier B, 재귀 여부 불확실 → Tier A-flat.

## 4. Tier A-flat 평탄화 규약 (재귀 금지 호스트의 토폴로지 해소)

subagent→subagent 재귀 금지는 ATP 의 2단 위임 체인(L1→L2→L3)에서 L2→L3 간선만 막는다. 이는 capability 부재가 아니라 **토폴로지 제약**이므로 Tier B 격하는 과하다 — 평탄화로 해소한다.

| 항목 | Tier A | Tier A-flat | Tier B (폴백) |
| --- | --- | --- | --- |
| spawn | advisor 가 worker spawn | orchestrator 가 worker 직접 spawn | spawn 없음 |
| 위임 깊이 | 2단 (L1→L2→L3) | 1단 평탄 (L1→L2, L1→L3) | 0단 (단일 agent) |
| worker 병렬 | advisor 내부 병렬 | orchestrator fan-out 병렬 | 순차 self-check |
| advisor 역할 | 계획+spawn+취합 | 계획 반환 → orchestrator 가 spawn → advisor 취합 | orchestrator self-check |
| 게이트 | 유지 | 유지 | 유지 |
| report 스키마(§8) | 유지 | 유지 | 유지 |
| 검증규율 | 유지 | 유지 | 유지 |
| 격하 대상 | 없음 | L2→L3 간선만 평탄화 | 병렬 → 순차 self-check |

**근거**: (1) flat fan-out 은 spawn 능력을 그대로 활용하면서 재귀만 회피한다. (2) report 스키마·게이트는 호출 토폴로지와 독립이므로 평탄화해도 무손실. (3) advisor 가 "spawn 주체"에서 "계획 산출 주체"로 역할만 이동 — 산출물 계약(보고서 스키마 §8) 불변.

## 5. Tier B 실행 규칙 (격하 시 적용)

spawn 미지원/자가판정 불가/실측 실패 호스트에서 **단일 agent 가 ATP 를 순차로 도는** 규율이다.

### 원칙

- **유지(불변)**: 파괴적 조작 게이트(프로토콜 §6), 보고서 스키마(§8), 검증규율(§13 phase 완료 아티팩트 기준), forward phase-gate(§2.7), 집합 전수 체크 AC(§4.3).
- **격하(변형)**: 병렬 advisor → 단일 agent 의 **순차 self-checklist**. worker fan-out → 단계별 self-수행. advisor 간 충돌 조정 → 단일 agent 가 phase 전환 시 직전 산출물 자기검토.
- **금지**: phase 척추(요구 → 조사 → 설계 → 구현 → 검증) 우회. 게이트 생략. report 스키마 누락.

### phase 순차 self-checklist

단일 agent 는 각 phase 진입 시 아래를 자기 점검하고, phase 종료 시 해당 phase 의 report(§8) 산출물을 `.atp/work-session/<sid>/` 에 기록한 뒤 다음 phase 로만 전진한다.

```
[Phase 0 — 요구사항 구체화]
  □ 요청을 FR/NFR 로 분해했는가
  □ 모호점은 AskUserQuestion 으로 닫았는가 (오픈 질문 0)
  □ requirements 산출물 기록 (report §8)

[Phase 1 — 조사 (research-advisor 역할 self-수행)]
  □ docs-first: index.md → 카테고리 index → 구체 문서 순 탐색했는가
  □ 외부 스펙은 source_confidence 마커(verified-seed/cited/TODO:실측)로 분류했는가
  □ (병렬 worker 불가) 조사 항목을 순차 처리하고 누락 없이 취합했는가
  □ research 산출물 기록 (report §8, concerns 포함)

[Phase 2 — 설계 (design-advisor 역할 self-수행)]
  □ 오픈 질문 0 — 미결은 concerns 로 에스컬레이션했는가
  □ 집합 포함 요구에 전수 체크 AC 1줄을 넣었는가 (§4.3)
  □ 시그니처 inflate 점검 (각 인자 사용 목적 인라인)
  □ design 산출물 기록 (report §8)

[Phase 3 — 구현 (implementation-advisor 역할 self-수행)]
  □ 설계도 파일 영향 맵을 따랐는가
  □ (병렬 worker 불가) 파일 단위 순차 수정 + 단계별 self-diff 검토
  □ unused/dead parameter 진단 게이트 통과 (§11.2)
  □ 파괴적 조작은 게이트 2단계 분리 통과 (§6)

[Phase 4 — 검증 (verification-advisor 역할 self-수행)]
  □ design 의 검증 포인트(AC) 전수 점검 — 집합 AC 는 grep -c 수치 일치 확인
  □ phase 완료 아티팩트 기준 충족 (§13)
  □ verification 산출물 기록 (report §8, PASS/FAIL)

[Phase 5 — 문서화 (documentation-advisor 역할 self-수행)]
  □ changes/ADR 등 카테고리 분류 기준 준수
  □ 회고 → MEMORY 반영 (§12)
```

### Tier B 진입 트리거

- §3 자가판정에서 spawn 불가/불확실 판정 시.
- 호스트 install 스모크에서 spawn 실패 확인 시.
- 또는 사용자가 명시적으로 단일-agent 모드 요청 시.
- 진입 시 orchestrator 는 "Tier B 격하 모드 — 병렬 advisor 미사용, 순차 self-checklist 수행" 을 1줄 고지한다.

## 6. 모델 Tier 매핑

ATP 모델 정책(프로토콜 §5)은 플랫폼 중립 tier(`small`/`medium`/`large`)로 판단하고, **호스트가 자기 모델 라인업으로 해석**한다.

| tier | 의미(등급) | 호스트 해석 |
| --- | --- | --- |
| small | 라인업 경량 등급 | 호스트 라인업의 경량 모델 |
| medium | 라인업 표준 등급 | 호스트 라인업의 표준 모델 |
| large | 라인업 최상위 등급 | 호스트 라인업의 최상위 모델 |

- **자사 확정 매핑** — reference 구현인 Claude Code 의 정본 슬러그 (as-of 2026-06): small=`haiku` / medium=`sonnet` / large=`opus`. ADR-0008 결정 5 가 본 절을 자사 슬러그 매핑 SSoT 로 지정한다. 라인업 변동 시 `as-of` 스탬프를 갱신한다.
- **타 호스트 구체 슬러그 하드코딩 금지** — 모델명 누수의 역방향이므로 금지(ADR-0008 결정 5). 각 호스트의 에이전트가 자기 라인업의 경량/표준/최상위 등급으로 해석한다.
- **per-call override**: 호스트가 제공하는 per-call override 문법(subagent 호출 파라미터, agent 정의 메타데이터 등)을 자율 사용한다. 생략 시 parent 상속.
- **effort 노브** (프로토콜 §5.5): 호스트가 노출하면 사용, 미노출이면 no-op — 동일 model_choice 블록을 모든 호스트가 공통 작성한다.
- **자기 모델 가시성** (프로토콜 §5.6 cap 판정): 자기 실행 모델을 tier 로 해석할 수 없으면 안전 폴백 — override 미지정(parent 상속), `resolved_model: inherit`.

## 7. 호스트 고유 적용 (자율 — 열거하지 않음)

다음은 호스트마다 다르지만 ATP 가 규정하지 않는다. 에이전트가 자기 호스트 규약을 자율 적용한다.

| 항목 | 적용 원칙 |
| --- | --- |
| skill/command 호출 문법 | 호스트가 노출하는 호출 토큰을 그대로 사용. 사용자 안내에는 자신이 이번 세션에서 호출된 토큰을 사용 |
| 지침파일 규약 | 호스트 자신의 지침파일 규약을 따른다 — 감지·생성 절차는 init SKILL §2 위임 |
| env/경로 변수 | 호스트의 프로젝트 루트·플러그인 루트 변수 자율 사용 (§1.3 논리 변수의 호스트 해석) |
| 배포 단위 | 호스트의 플러그인/확장 패키징 규약 자율 적용 |
| 모델 슬러그 | §6 — 중립 tier 를 자기 라인업으로 해석 |

## 8. 동결 이력 포인터

과거 특정 3사 CLI 에 대해 실측한 capability matrix(6축) · 플랫폼 Tier 판정표 · 토폴로지 해소표 · per-platform 어댑터 표 · 명령/환경변수/명명 대응표 · 실증 마커 목록은 소스 레포 `docs/adr/ADR-0009-bundle-runtime-platform-neutralization.md` **부록 A~F 에 동결 보존**되어 있다.

- 동결 이력이므로 **향후 갱신 의무 없음.** 새 호스트 실측이 생기면 신규 ADR 로 발행한다.
- 번들 런타임은 부록 데이터에 의존하지 않는다 — §3 자가판정만으로 동작한다.

## 검증 체크리스트

- [ ] 본 문서의 활성 규칙에 특정 타 벤더 플랫폼명·모델 슬러그가 열거되어 있지 않은가? (허용 잔존: §0 배경 1줄, §6 자사 정본 슬러그)
- [ ] Tier A / A-flat / B 정의가 capability 조건("spawn 가능한가" / "재귀 가능한가")만으로 기술되어 있는가?
- [ ] 자가판정 절차(§3)에 안전 폴백(불확실 → Tier B / parent 상속)이 포함되어 있는가?
- [ ] 동결 이력 포인터(§8 → ADR-0009 부록)가 존재하는가?
- [ ] 게이트·report 스키마·검증규율의 tier 독립성("어느 tier 든 유지")이 명시되어 있는가?
