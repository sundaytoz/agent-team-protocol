---
kind: changes
title: Codex Spark 조건부 라우팅 appendix
date: 2026-07-07
relates_to: [ADR-0008]
---

# Codex Spark 조건부 라우팅 appendix

## 무엇이 바뀌었나

Codex host 에서만 읽는 `codex-spark-routing.md` 런타임 appendix 를 추가했다. Spark 관련 구체 스펙은 공통 ATP 모델 정책에 직접 섞지 않고, `host_scope: codex-only` 문서로 격리한다.

## 실동작 변경

- `/atp:task` 의 모델 override 단계에서 host 전용 optional route 를 확인할 수 있다.
- Codex host 는 Spark 가 사용 가능한 경우에만 저지연 `code-writer` 류 작업 후보로 고려한다.
- Spark 가 미지원, 미확인, 권한/plan/quota 제한, 호출 실패, 검증 품질 리스크 중 하나에 걸리면 기존 `small` / `medium` / `large` tier 매핑으로 fallback 한다.
- report schema v2 는 유지한다. 새 필드 없이 `resolved_model` 과 `fallback_reason` 으로 실제 라우팅을 기록한다.

## 릴리스

base atp manifest 4곳: 2.4.0 → 2.5.0 (minor). `atp-graphify` 는 변경 없음.

상세 스펙: [codex-spark-routing.md](../../plugins/atp/docs/development/codex-spark-routing.md).
