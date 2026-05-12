# {PROJECT_NAME}

{프로젝트 한두 문장 설명을 여기에.}

## 기술 스택

| 구분 | 선택 |
| --- | --- |
| 런타임 | {e.g. Node.js 22 LTS} |
| 언어 | {e.g. TypeScript (ESM)} |
| 패키지 매니저 | {e.g. pnpm / yarn / npm / cargo / go mod} |
| 테스트 | {e.g. vitest / jest / pytest / go test} |

## 주요 명령어

```bash
{install}
{dev}
{build}
{test}
{typecheck or lint}
```

## 문서화 정책 (docs-first)

어떤 작업이든 시작 전에 **`docs/index.md`** 를 먼저 읽고, 관련 카테고리의 `index.md` → 구체 문서 순으로 탐색한 뒤 구현에 착수한다.

- 문서 작성/갱신 규칙: `docs/development/documentation-guidelines.md`
- 카테고리 분류 기준: `docs/development/document-category-classification.md`

## 에이전트 팀 운영 (명령어 진입)

이 프로젝트는 **`/task` 스킬로 명시 호출** 할 때만 Orchestrator + Advisor + Worker 3-tier 에이전트 팀 모드에 진입한다. 자동 적용되지 않는다. 작은 작업은 메인 에이전트가 종전처럼 직접 처리.

- 명령: `/task [요청]` — `.claude/skills/task/SKILL.md`
- 권위 레퍼런스: [docs/development/agent-team-protocol.md](./docs/development/agent-team-protocol.md)
- 에이전트 정의: `.claude/agents/*.md`

## 코딩 규칙

- {프로젝트 고유 규칙을 여기에 열거}
- 커밋 전 타입체크/테스트 통과 확인
