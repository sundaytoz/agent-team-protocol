---
kind: changes
title: 2.15.0 — Codex managed subagent orchestration
description: Codex host-managed all-results 계약과 release profile을 도입하고 검증되지 않은 tested CLI team execution을 안전하게 비활성화.
owner: template-maintainer
stability: stable
last_reviewed: 2026-08-20
---

# 2.15.0 — Codex managed subagent orchestration

## 원인

실제 Codex parent JSONL에서 단 한 번의 manual wait가 nonterminal update로 반환된 뒤 재대기가 없었고, terminal result 전에 report completion과 미래 `ended_at`이 기록됐다. ADR-0023의 native cooperative correctness는 모델이 재대기를 선택해야만 성립했다.

## 변경

- Codex 전용 `codex-team` skill을 추가하고 첫 collaboration action 전 전문 로드를 의무화했다.
- `host_managed_subagent_orchestration` candidate mode와 release-verified capability profile을 도입했다. Codex CLI 0.147.0 smoke는 3종 중 terminal-only 1종만 통과해 tested CLI를 `unsupported`, team execution disabled로 판정했다.
- 정상 Codex 경로의 manual wait/list polling과 소비 프로젝트 per-task smoke/probe/validator/parity 검사를 제거했다.
- managed session validator는 requested/spawn/nonterminal/terminal/collected와 manual wait/list/interrupt/recovery를 실제 transcript 순서로 대조한다.
- report/session completion serialization과 parent final이 마지막 terminal result 뒤인지 검증한다.
- 공통 task/protocol/agent는 host-neutral skill selection과 managed result barrier만 표현한다.

## 호환성

Formal `environment_subscription`, non-Codex Tier A-flat, 일반 Tier B, explicit-independence blocker, approval/steering/retry/ownership 계약은 유지한다. 2.14.0 native cooperative fixture는 historical defect regression으로만 남는다.

## 사용자 영향

- Codex plugin 설치, `$atp:init`/`$atp:task` skill 노출과 Tier B 순차 workflow는 계속 사용할 수 있다.
- Tested Codex CLI에서 일반 `$atp:task`는 `tier_b_sequential`로 진행하며 mode를 1줄 고지한다.
- 실제 독립 subagent 수행이 산출 요구사항이면 조용히 self-review로 대체하지 않고 `blocked_explicit_independence`에서 지원 host 재실행, 독립성 없는 Tier B 명시 전환 또는 취소를 제시한다.
- Codex App/IDE는 같은 smoke를 수행하지 않았으므로 `unknown`이다.

현재 사용자 제한과 우회책은 [Known Issues](../usage/known-issues.md), host에 필요한 후속 capability 제안은 [Backlog](../backlog/codex-cli-collaboration-await-v1.md)에서 분리해 추적한다.

## 검증

Deterministic managed fixture 3종, lifecycle contract, runtime unit/regression, pyright, JSON/JSONL parsing, host-neutrality scan과 격리 Codex CLI maintainer smoke 3종을 release gate로 사용한다. Deterministic fixture는 capability를 확정하지 않는다. 실제 smoke version과 artifact hash는 evidence manifest에 기록하며 세 smoke 전부가 통과하기 전 supported로 승격하지 않는다.

공개 저장소에는 validator, synthetic fixture와 비식별화된 evidence manifest만 둔다. 원본 사용자 대화, 실제 session transcript, 인증 정보와 로컬 절대 경로는 공개하지 않는다.
