---
kind: graph-index
title: ATP 코드 지식 그래프 인덱스
description: graphify 산출 코드 그래프의 정본 위치·scope·메타.
last_generated_at: 2026-06-25T11:13:20+09:00
source_commit: 7ab4a6cb646af4b06144d3db22550d2bc3b7f9aa
scopes:
  - path: adapters/opencode
    generated_at: 2026-06-25T11:13:20+09:00
    source_commit: 7ab4a6cb646af4b06144d3db22550d2bc3b7f9aa
    nodes: 162
    edges: 297
    communities: 9
---

# 코드 지식 그래프

graphify 로 생성한 코드 구조·관계 그래프 + 커뮤니티 탐지 결과의 **정본 위치**다. `graph-refresh-checker` 는 이 파일의 frontmatter(`source_commit`·`scopes`)로 staleness 를 판정한다.

## Scopes

| scope | nodes | edges | communities | generated | source_commit |
|---|---|---|---|---|---|
| `adapters/opencode` | 162 | 297 | 9 | 2026-06-25 | `7ab4a6c` |

## 산출물

> graph.html·graph.json·GRAPH_REPORT.md 는 재생성 가능한 빌드 산출물이라 **gitignore** 대상이다(documentation-guidelines §graphify). 원격 저장소엔 없으며, 클론 후 `/graphify adapters/opencode` 로 로컬 생성한다 — 아래 링크는 로컬 생성 후 유효. 이 `index.md`(메타)만 추적된다.

- [graph.html](./graph.html) — 인터랙티브 그래프 (브라우저에서 열기, 서버 불필요)
- [graph.json](./graph.json) — GraphRAG-ready raw 그래프 데이터
- [GRAPH_REPORT.md](./GRAPH_REPORT.md) — 감사 리포트 (god nodes·surprising connections·communities·99% EXTRACTED)

## 핵심 구조 (요약)

- **God nodes** (최다 연결 = 핵심 추상): `runInstall()`, `transformAgent()`, `buildPlan()`, `runUninstall()`
- **Hyperedges**: Transform Pipeline(parse→rewrite→serialize) · Install Flow(plan→prune→mkdir→write→manifest) · Canonical Source Resolution(vendor 번들 vs 레포 폴백)
- 9 communities: Install·Plan 실행 코어 / Agent 변환 개념·매핑 / Vendor 번들·패키징 / Install·Transform 테스트 / Tool·Tier 매핑 / Frontmatter 직렬화 / Canonical 번들 스크립트 / 참조 재작성

## 갱신

- 변경분만: `/graphify adapters/opencode --update`
- 신규 scope 추가: `/graphify <경로>` → 이 표에 행 추가 + frontmatter `scopes` 갱신
- `graphify-out/` 은 빌드 작업폴더(`.gitignore`) — 정본은 이 `docs/graph/` 디렉토리다.
