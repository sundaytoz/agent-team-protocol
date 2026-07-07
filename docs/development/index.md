# Development — 개발 규칙 / 절차 / 툴 운영

반복해서 재사용할 규칙/워크플로우/툴 사용법을 둔다.

## 목록

> 런타임 레퍼런스(에이전트가 `${CLAUDE_PLUGIN_ROOT}/docs/development/...` 로 Read 하는 문서)는 [plugins/atp/docs/development/](../../plugins/atp/docs/development/index.md) 로 이동했다 — 번들에는 그 서브트리만 포함된다. 이 디렉토리에는 **기여자용 문서**(릴리즈 절차 등)만 남는다. 프로젝트별 **편집형** 문서(`verification-strategies.md`, `document-category-classification.md`)는 `/atp:init` 이 소비 프로젝트 `docs/development/` 에 생성한다 (원본 템플릿은 `plugins/atp/templates/`).

런타임 레퍼런스 (번들 — `plugins/atp/docs/development/`):
- [agent-team-protocol.md](../../plugins/atp/docs/development/agent-team-protocol.md) — Orchestrator + Advisor + Worker 3-tier 에이전트 팀 운영 규약 (호출 모델, 충돌 조정, 모델 선택, 보고서 스키마, 확장 트리거)
- [agent-catalog.md](../../plugins/atp/docs/development/agent-catalog.md) — 에이전트 정의 요약 카탈로그 (base `atp` 10개 + 옵트인 `atp-graphify` 3개. 권위 원본은 `plugins/atp/agents/*.md` 및 `plugins/atp-graphify/agents/*.md`)
- [documentation-guidelines.md](../../plugins/atp/docs/development/documentation-guidelines.md) — 문서 작성 가이드라인
- [platform-adapters.md](../../plugins/atp/docs/development/platform-adapters.md) — 호스트 capability tier 정의와 자가판정 절차. 호스트 고유 문법·슬러그는 에이전트가 자율 적용 (과거 3사 실측 데이터는 [ADR-0009](../adr/ADR-0009-bundle-runtime-platform-neutralization.md) 부록에 동결)
- [search-tool-matrix.md](../../plugins/atp/docs/development/search-tool-matrix.md) — 탐색/검색 도구 선택 매트릭스 (LSP, graphify, Grep, Glob, Read, WebFetch 목적별 기준)
- [codex-spark-routing.md](../../plugins/atp/docs/development/codex-spark-routing.md) — Codex host 전용 Spark 조건부 라우팅 appendix

기여자용 문서 (이 디렉토리 — 번들 제외):
- [release-checklist.md](./release-checklist.md) — **§0 = 언제 릴리즈를 시작하나** (user-facing feat 머지 = release 완결 의무, 진입 조건) / §1~§9 = bump 전제 사후 invariant 점검(문서 링크·TODO 마커·manifest·agent catalog·끊긴 §N 인용 동기화). `plugins/atp/` 번들을 건드리는 작업은 **§0 를 먼저** 본다(루트 `CLAUDE.md` "릴리스 — 배포 완결 의무" 가 docs-first 로 이 §0 를 가리킨다).

편집형(프로젝트 생성) 문서:
- `verification-strategies.md` — `verification-advisor` 가 읽는 검증 전략 레지스트리. `/atp:init` 이 생성, 프로젝트가 `cmd` 를 채운다.
- `document-category-classification.md` — 카테고리 분류 기준. `/atp:init` 이 생성, 프로젝트가 조정한다.
