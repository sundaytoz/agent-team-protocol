---
kind: graph-index
title: ATP 코드 지식 그래프 인덱스
description: graphify 산출 코드 그래프의 정본 위치·scope·메타.
last_generated_at: 2026-07-30T09:38:00+09:00
source_commit: c01f5735173f3ea00effac318ffad3be6f9bbff7
scopes:
  - name: adapters-opencode
    path: adapters/opencode
    source_file_base: adapters/opencode
    generated_at: 2026-07-30T09:38:00+09:00
    source_commit: c01f5735173f3ea00effac318ffad3be6f9bbff7
    nodes: 133
    edges: 247
    hyperedges: 3
    communities: 10
---

# 코드 지식 그래프

graphify 로 생성한 코드 구조·관계 그래프 + 커뮤니티 탐지 결과의 **정본 위치**다. `graph-refresh-checker` 는 이 파일의 frontmatter(`source_commit`·`scopes`)로 staleness 를 판정한다.

산출물은 scope 별 서브디렉토리(`docs/graph/<scope>/`)에 둔다 — scope 를 여러 개 운용할 때 `graph.json` 파일명이 충돌하지 않게 하는 정본 레이아웃이다. scope 명은 대상 경로의 `/` 를 `-` 로 치환한 slug 이며, 노드 경로 해석 기준은 `source_file_base` 에 적는다. 이 레이아웃 결정의 근거·대안·되돌리기 경로는 [ADR-0019](../adr/ADR-0019-graph-artifact-scope-directory-layout.md) 에 있다 — flat 레이아웃으로 되돌리기 전에 반드시 읽을 것.

## Scopes

| scope | 대상 경로 | source_file_base | nodes | edges | communities | generated | source_commit |
|---|---|---|---|---|---|---|---|
| `adapters-opencode` | `adapters/opencode` | `adapters/opencode` | 133 | 247 | 10 | 2026-07-30 | `c01f573` |

노드의 실제 파일 위치 = `<repo>/<source_file_base>/<source_file>` 이다. 그래프의 `source_file` 은 scope 대상 경로에 상대적이므로 이 base 없이는 해석할 수 없다.

## 산출물

> graph.html·graph.json·GRAPH_REPORT.md 와 증분 갱신 상태(manifest 등)는 재생성 가능한 빌드 산출물이라 **gitignore** 대상이다(documentation-guidelines §graphify). 원격 저장소엔 없으며, 클론 후 `/graphify adapters/opencode` 로 로컬 생성한 뒤 `docs/graph/adapters-opencode/` 로 배치한다 — 아래 링크는 배치 후 유효. 이 `index.md`(메타)만 추적된다.

- [graph.html](./adapters-opencode/graph.html) — 인터랙티브 그래프 (브라우저에서 열기, 서버 불필요)
- [graph.json](./adapters-opencode/graph.json) — GraphRAG-ready raw 그래프 데이터
- [GRAPH_REPORT.md](./adapters-opencode/GRAPH_REPORT.md) — 감사 리포트 (god nodes·surprising connections·communities)

## 핵심 구조 (요약)

재생성 실측 기준(2026-07-30). 코퍼스 16파일 / ~7,700 words — code 14 + docs 2.

- **God nodes** (최다 연결 = 핵심 추상): `runInstall()` 11 · `buildPlan()` 10 · `runUninstall()` 10 · `transformAgent()` 9 · `parseFrontmatter()` 8
- **Hyperedges** (3): `atp-opencode install` 플래그 표면·실패 계약(7노드) · publish 시점 canonical 번들링 흐름(5노드) · canonical agent frontmatter 충실도 계약(6노드)
- **10 communities**: Frontmatter Transform Pipeline / Adapter Contract Documentation / Package Manifest Metadata / Install Test Suite / Canonical Source Planning / Path Resolution and Uninstall / Canonical Vendor Bundling / Plugins Root Resolution / Install Execution Flow / CLI Entry Point
- **추출 신뢰도**: 94% EXTRACTED · 6% INFERRED(14 엣지, 평균 confidence 0.84) · 1% AMBIGUOUS
- **알려진 품질 경고**: graph health 진단이 dangling-endpoint 엣지 29건을 보고했다(raw 276 → valid 247). 읽기 전용 진단이며 빌드를 중단시키지 않는다 — 그래프는 사용 가능하되 일부 엣지의 한쪽 끝이 노드로 해소되지 않는다. edge collapse·self-loop·중복 엣지는 0건.

## 갱신

- 변경분만: `/graphify adapters/opencode --update` — **런북이 cwd 의 `graphify-out/` 을 읽으므로 실행 전 배치를 역방향으로 되돌린다**(add-on `graphify-usage.md` §4.2 절차).
- 전량 재생성: `/graphify adapters/opencode` → 산출물을 `docs/graph/adapters-opencode/` 로 배치 + 빈 `graphify-out/` 제거
- 신규 scope 추가: `/graphify <경로>` → 이 표에 행 추가 + frontmatter `scopes` 갱신(`name`·`path`·`source_file_base` 필수)
- `graphify-out/` 은 빌드 작업폴더(`.gitignore`) — 정본은 이 `docs/graph/` 디렉토리다. 질의 전 잔존 여부를 확인한다: 남아 있으면 `/graphify` 가 정본 대신 그 사본으로 즉답한다.
