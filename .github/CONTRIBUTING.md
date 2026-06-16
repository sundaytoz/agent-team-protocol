<p align="center"><a href="CONTRIBUTING.md">한국어</a> · <a href="CONTRIBUTING.en.md">English</a></p>

# 기여 가이드 (Contributing)

이 문서는 루트 [`CLAUDE.md`](../CLAUDE.md) · [`AGENTS.md`](../AGENTS.md) 의 보완 가이드다. 전체 규약을 중복 서술하지 않고, 각 항목의 요지와 정본 문서 링크만 제공한다.

## 시작하기 전에 (Before you start)

docs-first 원칙: 어떤 작업이든 [`docs/index.md`](../docs/index.md) 를 먼저 읽고 → 관련 카테고리 `index.md` → 구체 문서 순으로 탐색한 뒤 착수한다.

## 레포 구조 / 3-tree 분리

`plugins/atp/docs/`(번들 런타임 레퍼런스) · 루트 `docs/`(사람용 문서) · `plugins/atp/templates/`(편집형 원본) 세 트리는 섞지 않는다. 자세한 구조는 [`CLAUDE.md`](../CLAUDE.md) 참조.

## 개발 / 검증 진입

작은 작업은 메인 에이전트가 직접 처리하고, 3-tier 팀 모드는 `/atp:task`(Claude Code) 또는 `$atp:task`(Codex) 를 명시 호출할 때만 진입한다. 이 레포에서 self-dogfooding 하려면 로컬 플러그인 enable 이 선행되어야 한다([`CLAUDE.md`](../CLAUDE.md) · [`AGENTS.md`](../AGENTS.md)).

## 커밋 규약

Conventional Commits prefix(`feat` / `fix` / `docs` / `refactor` / `chore`; breaking change 는 `!` 표기)를 사용한다. 모든 AI 협업 커밋에는 `Co-Authored-By` 트레일러를 의무로 남긴다. 메시지 본문은 한/영 혼용을 허용한다.

## PR 절차

main 브랜치에 직접 push 하지 않는다. fork 또는 feature branch 에서 작업하고 PR 기반으로 머지한다.

## ADR 규칙

되돌리기 어려운 결정은 `docs/adr/ADR-NNNN-kebab.md` 로 기록한다. ADR 은 append-only 이며, 결정을 뒤집을 때는 기존 문서를 수정하지 않고 새 ADR 을 만들어 supersedes 로 연결한다. 섹션 구조는 Context / Decision / Consequences / Alternatives 다([`docs/adr/index.md`](../docs/adr/index.md)).

## 릴리즈 트리거 게이트

user-facing `feat` 가 `plugins/` 번들에서 main 에 머지되면, 같은 작업 단위 안에서 manifest version bump → `/plugin update` 도달까지 release 를 완결한다([`docs/development/release-checklist.md`](../docs/development/release-checklist.md)).

## 문서 언어 정책

한국어가 정본이며 `*.en.md` 영문 미러를 함께 둔다. 도메인 용어는 원어를 보존한다.

## 행동 강령 / 보안 / 지원

[`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) · [`SECURITY.md`](../SECURITY.md) · [`SUPPORT.md`](SUPPORT.md) 를 참조한다.

---

이 community 파일들(`.github/` 산하)은 **이 레포 자체용**이며 `/atp:init` 소비 프로젝트로 복사되지 않는다.
