---
kind: adr
adr_number: "0008"
title: 모델 선택 정책 플랫폼 중립화 (tier S/M/L + effort 직교 노브) + orchestrator cap 규칙 + report 스키마 v2
status: accepted
date: 2026-06-10
deciders:
  - template-maintainer
  - stzjungsoo
supersedes: []
related_commits:
  - 719aa11
---

# ADR-0008: 모델 선택 정책 플랫폼 중립화 + cap 규칙 + report 스키마 v2

## 상태

**Accepted** — 2026-06-10. 세션 20260610-173353. ADR-0006(3-플랫폼 지원)·ADR-0007(플러그인 서브디렉토리) 위에 적층. supersede 아님.

---

## 맥락

프로토콜 §5 모델 선택 정책이 Claude 전용 모델명(haiku/sonnet/opus)을 하드코딩하고 있었다. Codex 세션 전사(2026-06-10, codex-cli 0.138.0)에서 사용자가 사용 모델을 묻자 Codex 가 ATP 문서의 타 벤더 모델명을 그대로 노출했다 — platform-adapters 의 3층 플랫폼 추상화(ADR-0006)가 모델 정책 레이어에는 적용되지 않았던 구조적 공백이다. 같은 전사에서 (a) Codex 가 subagent 2개를 실제 spawn 했음에도 report.md Invocations 에 orchestrator 만 기록된 §8 의무 위반, (b) Codex spawn capability 의 실증 증거가 함께 확인됐다.

또한 사용자 요구로, orchestrator 가 자신에게 할당된 모델보다 높은 등급을 subagent 에 지정하는 것을 금지하는 상한(cap) 규칙이 추가됐다 — 세션 모델 선택은 사용자가 표명한 비용/능력 상한이라는 해석이다.

## 결정

### 결정 1 — 플랫폼 중립 tier 어휘: `small` / `medium` / `large`

§5 전체를 tier 어휘로 재작성. tier 는 "그 호출 안에 남은 미결 판단의 수" = **판단 천장**을 표현하는 논리 등급이며, 구체 모델 슬러그는 각 플랫폼이 platform-adapters §1.6 매핑으로 해석한다. §5.4 는 판단축 4개(판단 밀도 / 결정론적 검증 가능성 / 오류의 침묵성 / 컨텍스트 폭)로 정교화 — phase 이름보다 작업 성격이 우선한다.

- 기각 대안 1: haiku/sonnet/opus 를 "논리 등급명"으로 재선언 — 여전히 특정 벤더 명칭이라 누수 동일.
- 기각 대안 2: 숫자형 tier-1/2/3 — §2 advisor Tier-2/3, platform-adapters capability Tier A/B 와 세 번째 "Tier" 축 충돌.
- 부수 결정: §5.3 디스패치 크기 라벨을 `s-batch`/`m-batch`/`l-batch` 로 개명 — small/medium/large 를 tier 가 점유하므로 직교 축 어휘 분리.

### 결정 2 — effort 직교 노브 (low/medium/high) + no-op 규칙

tier 가 판단 천장이라면 effort 는 "한 판단을 얼마나 깊게". 반박·검증·root-cause 는 high, 추출·포맷 변환은 low. 판단 천장 부족은 effort 로 보충 불가(tier 를 올린다). effort 노브 미지원 플랫폼에서는 기록만 하고 런타임 무시(no-op) — 미지원이 호출 실패를 유발하지 않아 동일 model_choice 블록을 3사가 공통 작성한다.

### 결정 3 — cap 규칙: orchestrator tier 상한 집행 (§5.6 신설)

orchestrator 는 자기 할당 모델의 tier 를 초과하는 tier 를 subagent 에 지정할 수 없다. 초과 산출 시 자동 clamp + `model_choice.capped`/`capped_from` 기록 + 세션 최종 보고 노출. 자기 tier 판정 불가 플랫폼은 override 미지정·parent 상속 안전 폴백(상속은 정의상 cap 초과 불가). cap clamp 는 사용자가 세션 모델 선택으로 표명한 상한의 집행이므로 silent downgrade 금지(§5.7)와 충돌하지 않는다.

### 결정 4 — report 스키마 v2

`model_choice.model: <haiku|sonnet|opus>` enum 제거 → `tier` / `effort` / `resolved_model` / `capped` / `capped_from` 도입. 필드 의미 변경·제거이므로 §8 진화 규칙에 따라 `schema_version: 2`. additive(model 유지) 기각 — 두 진실원(model vs tier) drift. 기존 v1 보고서는 소급 수정하지 않으며 v1/v2 혼재 읽기를 허용한다. `tier`(중립 의사결정값)와 `resolved_model`(실제 슬러그 사후 기록) 분리는 플랫폼 간 비교·retro 보정 루프에 필요.

### 결정 5 — 매핑 레이어: platform-adapters §1.6 + 역방향 누수 금지

tier→슬러그 매핑은 platform-adapters Layer 1 §1.6 에 신설. **자사 플랫폼(Claude Code)만 구체 슬러그 확정 기재**(small=haiku / medium=sonnet / large=opus, `as-of` 신선도 스탬프). Codex/Gemini 는 "라인업 경량/표준/최상위 등급" 의미 기술 + 신뢰도 마커만 — 타 벤더 슬러그 하드코딩은 모델명 누수의 역방향이므로 금지(AC 회귀 가드 포함). effort 지원 여부·자기 모델 가시성(cap 판정용)도 §1.6 에서 플랫폼별 관리.

### 결정 6 — spawn = invocation 기록 의무 명문화

spawn 된 모든 subagent 는 capability tier·플랫폼 불문 layer + parent_invocation_id 를 갖는 invocation 으로 기록한다(§8 주석 + platform-adapters §1.2 교차). Codex 전사의 subagent 2건 누락 사례가 직접 계기. 같은 전사를 근거로 축1 Codex spawn 마커를 cited → verified-empirical 로 격상(install 스모크 needs_user_verification 은 별개 유지).

## 영향

- 번들: `plugins/atp/docs/development/agent-team-protocol.md`(§2.5/§5/§8), `platform-adapters.md`(§1.1/§1.2/§1.3/§1.6 신설/§2.1~2.3), `skills/task/SKILL.md`(§1/§3/§6).
- 사람용: `README.md`, `docs/usage/faq.md`/`faq.en.md`, 본 ADR, `TEMPLATE_DEV.md`.
- 소비 프로젝트: 신규 세션부터 report v2 발행. 과거 v1 보고서와 혼재 허용 — 마이그레이션 불요.
- Claude 모델명의 허용 잔존 구역: platform-adapters §1.6(자사 매핑 정본), ADR/TEMPLATE_DEV(이력), 프로토콜 §2.1·§4.6 배경 서술 2줄(역사적 사실).

## 검증

설계 AC 14개(세션 20260610-173353 design.md §4) — 핵심: 모델명 누수 0건 전수 grep(AC-1), 역방향 누수 0건 회귀 가드(AC-10), cap 4조문(AC-3), 스키마 신규 필드 5개(AC-4). 모든 grep 은 self-exclusion character-class 로 자기매치 방지, 실제 실행으로만 통과 판정(§4.6).
