# Development — 개발 규칙 / 절차 / 툴 운영

반복해서 재사용할 규칙/워크플로우/툴 사용법을 둔다.

## 목록

> 이 디렉토리는 **플러그인 번들 레퍼런스**(읽기전용)다. 에이전트가 `${CLAUDE_PLUGIN_ROOT}/docs/development/...` 로 Read 한다. 프로젝트별 **편집형** 문서(`verification-strategies.md`, `document-category-classification.md`)는 여기 두지 않고 `/atp:init` 이 소비 프로젝트 `docs/development/` 에 생성한다 (원본 템플릿은 `templates/`).

- [agent-team-protocol.md](./agent-team-protocol.md) — Orchestrator + Advisor + Worker 3-tier 에이전트 팀 운영 규약 (호출 모델, 충돌 조정, 모델 선택, 보고서 스키마, 확장 트리거)
- [agent-catalog.md](./agent-catalog.md) — 에이전트 정의 요약 카탈로그 (base `atp` 10개 + 옵트인 `atp-graphify` 3개. 권위 원본은 `agents/*.md` 및 `addons/graphify/agents/*.md`)
- [documentation-guidelines.md](./documentation-guidelines.md) — 문서 작성 가이드라인
- [search-tool-matrix.md](./search-tool-matrix.md) — 탐색/검색 도구 선택 매트릭스 (LSP, graphify, Grep, Glob, Read, WebFetch 목적별 기준)

편집형(프로젝트 생성) 문서:
- `verification-strategies.md` — `verification-advisor` 가 읽는 검증 전략 레지스트리. `/atp:init` 이 생성, 프로젝트가 `cmd` 를 채운다.
- `document-category-classification.md` — 카테고리 분류 기준. `/atp:init` 이 생성, 프로젝트가 조정한다.
