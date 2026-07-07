---
kind: development
title: Codex Spark Routing
description: Codex host 에서만 읽는 GPT-5.3-Codex-Spark 조건부 라우팅 규칙.
owner: template-maintainer
stability: experimental
last_reviewed: 2026-07-07
host_scope: codex-only
---

# Codex Spark Routing

이 문서는 **Codex host 에서만** 읽는 선택적 스펙이다. Claude Code, Gemini, opencode 등 다른 host 는 이 문서를 읽지 않고 `platform-adapters.md` §6 의 기존 tier 매핑만 따른다.

## 목적

`gpt-5.3-codex-spark` 는 Codex 의 별도 모델 선택지이며, Fast mode 나 `effort` 값이 아니다. 따라서 ATP 공통 정책의 `small` / `medium` / `large` tier 를 대체하지 않는다. Spark 는 Codex 사용자가 해당 모델을 사용할 수 있는 환경에서만, 저지연 코드 작성 worker 후보로 제한적으로 사용한다.

## 적용 조건

Orchestrator 는 아래 조건을 모두 만족할 때만 Spark 라우팅을 고려한다.

- 현재 host 가 Codex 이고, host 의 모델 카탈로그 또는 모델 선택 UI 에서 `gpt-5.3-codex-spark` 사용 가능성이 확인됨.
- phase 가 `code-implementation` 이고, 대상이 `code-writer` 류의 텍스트 코드 편집이다.
- 설계가 이미 확정되어 worker 가 새 설계 판단, 원인 탐색, 충돌 중재를 하지 않는다.
- 변경 범위가 단일 파일 또는 작고 독립적인 파일 묶음이며, 검증이 lint/typecheck/unit test/grep 같은 결정론적 게이트로 잡힌다.
- 보안, 인증, 권한, 결제, 데이터 마이그레이션, 파괴적 조작, 공개 배포 판단이 포함되지 않는다.

## 제외 조건

다음 작업은 Spark 를 사용하지 않는다.

- analyze / design / planning / graphify-judgment / validation-runtime.
- root-cause 탐색, 다파일 아키텍처 판단, 의미 감사, 사용자-visible 회귀 판정.
- `migration-writer` 작업 또는 irreversible data path.
- Spark 사용 가능 여부가 불명확한 환경.

## Fallback

Spark 는 optional route 이다. 아래 상황에서는 기존 ATP 모델 정책으로 즉시 fallback 한다.

- host 가 Codex 가 아님.
- `gpt-5.3-codex-spark` 가 모델 카탈로그, allowlist, UI selector 에서 확인되지 않음.
- 호출 시 model unavailable, permission/plan 제한, quota/usage 제한, research-preview 미제공, 또는 기타 모델 선택 실패가 발생함.
- Spark 로 수행한 code worker 결과가 결정론적 검증에서 실패하고, 실패 원인이 단순 문법 수정이 아니라 판단 품질 리스크로 보임.

Fallback 은 `platform-adapters.md` §6 의 기존 tier 매핑을 사용한다. 즉 `tier` / `effort` / `cap` / `resolved_model` / `fallback_reason` 기록 규칙은 `agent-team-protocol.md` §5 그대로 유지한다.

## 기록 규칙

Spark 를 실제 사용한 invocation 은 기존 `model_choice` 스키마를 유지하고 다음처럼 기록한다.

```yaml
model_choice:
  phase: code
  dispatch_size: s-batch
  tier: medium
  effort: low | medium
  resolved_model: gpt-5.3-codex-spark
  capped: false
  capped_from: null
  escalation_reason: null
  fallback_reason: null
  rationale: 'Codex Spark route: 확정 스펙의 저지연 code-writer 작업'
```

Spark 를 고려했지만 쓰지 못한 경우:

```yaml
model_choice:
  phase: code
  dispatch_size: s-batch
  tier: medium
  effort: medium
  resolved_model: <기존 tier 매핑 결과|inherit>
  capped: false
  capped_from: null
  escalation_reason: null
  fallback_reason: 'Codex Spark unavailable: <확인된 사유>'
  rationale: 'Spark route 후보였으나 기존 tier 매핑으로 fallback'
```

새 필드는 추가하지 않는다. `resolved_model` 과 `fallback_reason` 만으로도 실제 라우팅과 fallback 을 재현할 수 있어 report schema v2 를 유지한다.

## 운영 원칙

- Spark 사용은 비용 사유의 silent downgrade 로 취급하지 않는다. 사용 목적은 저지연 반복이며, 적용 조건이 좁고 검증 게이트가 결정론적일 때만 허용된다.
- §5 판정 결과가 `large` 인 작업은 Spark 후보가 아니다. `large` 가 나온다는 것은 남은 판단 천장이 높다는 뜻이므로 저지연 모델로 보충하지 않는다.
- Spark 가 실패하면 같은 작업 단위를 좁혀 재시도하거나 기존 tier 매핑 모델로 1회 재시도한다. 반복 실패 시 implementation concern 으로 올리고 design/verification 단계로 되돌린다.

## 확인 방법

Codex host 는 자기 환경에서 제공되는 모델 선택 메커니즘으로 availability 를 확인한다. 예시:

```bash
codex debug models | jq -r '.models[].slug' | grep -x 'gpt-5.3-codex-spark'
```

이 명령은 Codex CLI 에서만 의미가 있다. 실패하거나 명령이 없으면 Spark 미확인으로 보고 기존 tier 매핑을 사용한다.
