---
kind: development
title: 에이전트 카탈로그
description: `.claude/agents/*.md` 13 파일 개요와 tier·호출 시점 정리.
owner: template-maintainer
stability: stable
peer_docs:
  - docs/development/agent-team-protocol.md
last_reviewed: 2026-05-07
---

# 에이전트 카탈로그

본 템플릿에 포함된 13개 에이전트의 **요약 테이블**. 각 에이전트의 권위 정의는 `.claude/agents/<name>.md` (frontmatter + 본문) 에 있다. 이 카탈로그는 탐색·재검토·리뷰용 개요다.

운영 규약(호출 모델, 충돌 조정, 파괴적 조작 게이트, 보고서 스키마) 은 [`agent-team-protocol.md`](./agent-team-protocol.md) §1~§14 를 참조한다.

## Tier 2 (단일 invocation 완결)

Advisor 1회 호출로 산출물을 완결 보고한다. Worker 를 spawn 하지 않는다.

| 에이전트 | 도구 | 핵심 제약 |
|---|---|---|
| `requirements-advisor` | Read, Grep, Glob, Bash, AskUserQuestion | 설계·구현 금지. 오픈 질문은 `concerns` 로 에스컬레이션 |
| `design-advisor` | Read, Grep, Glob, Write, Edit | `design.md` 만 작성. **오픈 질문 금지** — 전부 결정 |
| `verification-advisor` | Read, Bash | **구현 코드·design.md 접근 금지.** acceptance criteria + 실행 결과만 본다 |
| `documentation-advisor` | Read, Grep, Glob, Write, Edit | 새 문서 생성 시 카테고리 `index.md` 링크 추가 의무 |
| `retrospective-advisor` | Read, Grep, Glob, Edit | 긍정/부정 시그널 양측 수집. MEMORY 직접 수정 금지 |
| `graphify-lookup-advisor` | Read, Grep, Glob, Bash | `docs/graph/` 밖 파일 읽기 금지. peer: graph-refresh-checker / graphify-update-advisor |
| `graphify-update-advisor` | Read, Grep, Glob, Write, Edit, Bash | `/graphify` 직접 호출 금지 (orchestrator 경유). peer: graph-refresh-checker / graphify-lookup-advisor |
| `graph-refresh-checker` | Bash, Read, Glob, Grep | staleness 판정만. 재생성 금지. peer: graphify-lookup-advisor / graphify-update-advisor |

## Tier 3 (Worker 병렬 spawn)

Advisor 가 내부적으로 Worker 를 최대 6개까지 동시 spawn 한다. Agent 툴은 **Tier 3 advisor 만** 보유한다 (재귀 방지).

| 에이전트 | Worker | 도구 |
|---|---|---|
| `research-advisor` | `parallel-explorer` | Read, Grep, Glob, Bash, WebFetch, WebSearch, Agent, LSP |
| `implementation-advisor` | `code-writer`, `migration-writer` | Read, Grep, Glob, Write, Edit, Bash, Agent, LSP |

## Worker (재귀 금지 — Agent 툴 없음)

| 워커 | 소속 | 도구 | 핵심 제약 |
|---|---|---|---|
| `parallel-explorer` | research | Read, Grep, Glob, Bash, WebFetch, LSP | read-only. 파일 쓰기 금지. 범위 밖 탐색 금지 |
| `code-writer` | implementation | Read, Write, Edit, Grep, Glob, LSP | **담당 파일에만** 쓰기 (Bash 없음) |
| `migration-writer` | implementation | Read, Write, Edit, Grep, Glob, Bash | 마이그레이션 **생성만**. DB 적용은 orchestrator 몫 |

## peer_agents 규약

동일 도메인 로직을 공유하는 에이전트 쌍/트리오는 각 에이전트 frontmatter 의 `peer_agents` 필드로 선언된다. 수정 시 peer 정합성 교차 점검이 의무. 상세는 [`agent-team-protocol.md`](./agent-team-protocol.md) §11.1.

대표 peer 그룹:

- **graphify 트리오**: `graphify-lookup-advisor` / `graphify-update-advisor` / `graph-refresh-checker`
- **implementation 트리오**: `implementation-advisor` / `code-writer` / `migration-writer`
- **research 페어**: `research-advisor` / `parallel-explorer`

## 확장 — Tier 3 로의 승격

관측된 신호가 누적되면 특정 advisor 를 Tier 3 로 승격하고 worker 를 추가한다. 트리거 레지스트리는 `agent-team-protocol.md` §9 (확장 트리거 레지스트리). 예측 기반으로 미리 worker 를 만들지 않는다 — **사후 승격 원칙**.

## 관련 문서

- [`agent-team-protocol.md`](./agent-team-protocol.md) — §1 역할 정의, §2 호출 모델, §6 파괴적 조작 게이트, §11 Agent 파일 규약 (peer_agents 포함)
- [`verification-strategies.md`](./verification-strategies.md) — verification-advisor 가 참조하는 전략 레지스트리
- [`graphify-usage.md`](./graphify-usage.md) — graphify 트리오의 외부 스킬 연동 설치·운용
- [`search-tool-matrix.md`](./search-tool-matrix.md) — 각 에이전트가 사용하는 탐색 도구의 목적별 선택 기준
- `.claude/agents/*.md` — 각 에이전트의 권위 정의 (frontmatter `tools:` / `peer_agents:` 포함)
