---
name: init
description: atp 플러그인을 소비 프로젝트에 초기화. docs 골격·편집형 검증전략·CLAUDE.md 안내 블록을 멱등 생성. 플러그인 설치 후 프로젝트에서 한 번 실행.
disable-model-invocation: true
---

# /atp:init

atp 플러그인을 **소비 프로젝트** 에 초기화한다. 플러그인 캐시에 둘 수 없는 편집형 docs 골격을 `${CLAUDE_PROJECT_DIR}` 로 생성하고, CLAUDE.md 에 docs-first + `/atp:task` 안내 블록을 멱등 append 한다.

## 사용법

```
/atp:init           # 멱등 — 이미 있는 파일은 skip
/atp:init --force    # 기존 파일도 templates/ 원본으로 덮어쓰기
```

## 동작 (순서 고정)

복사 소스는 항상 `${CLAUDE_PLUGIN_ROOT}/templates/...`(플러그인 번들), 생성 대상은 항상 `${CLAUDE_PROJECT_DIR}/...`(소비 프로젝트 루트)다.

### 1. docs 골격 생성 (각 파일: 존재하면 skip — `--force` 시에만 덮어쓰기)

대상 → 소스:

- `${CLAUDE_PROJECT_DIR}/docs/index.md` ← `${CLAUDE_PLUGIN_ROOT}/templates/docs-index.md`
- `${CLAUDE_PROJECT_DIR}/docs/development/verification-strategies.md` ← `${CLAUDE_PLUGIN_ROOT}/templates/verification-strategies.md`
- `${CLAUDE_PROJECT_DIR}/docs/development/document-category-classification.md` ← `${CLAUDE_PLUGIN_ROOT}/templates/document-category-classification.md`
- `${CLAUDE_PROJECT_DIR}/docs/development/index.md` ← `${CLAUDE_PLUGIN_ROOT}/templates/category-index/development.md`
- 카테고리 index 14개 — 각 `<cat>` 에 대해 `${CLAUDE_PROJECT_DIR}/docs/<cat>/index.md` ← `${CLAUDE_PLUGIN_ROOT}/templates/category-index/<cat>.md`. 카테고리 목록: `adr analysis architecture backlog changes contracts development domain issues maintenance security usage work-log feedback` (development 는 위 항목과 동일 — 한 번만 생성).
- `${CLAUDE_PROJECT_DIR}/docs/graph/index.md` ← `${CLAUDE_PLUGIN_ROOT}/templates/graph/index.md`
- `${CLAUDE_PROJECT_DIR}/docs/graph/.gitignore` ← `${CLAUDE_PLUGIN_ROOT}/templates/graph/.gitignore`

Bash 구현 가이드 (멱등):

```bash
PR="${CLAUDE_PROJECT_DIR}"; PL="${CLAUDE_PLUGIN_ROOT}"; FORCE=0   # --force 인자면 FORCE=1
copy_idem() { # $1=src $2=dest
  if [ -f "$2" ] && [ "$FORCE" -ne 1 ]; then echo "skip: $2"; return; fi
  mkdir -p "$(dirname "$2")"; cp "$1" "$2"; echo "write: $2"
}
copy_idem "$PL/templates/docs-index.md" "$PR/docs/index.md"
copy_idem "$PL/templates/verification-strategies.md" "$PR/docs/development/verification-strategies.md"
copy_idem "$PL/templates/document-category-classification.md" "$PR/docs/development/document-category-classification.md"
for c in adr analysis architecture backlog changes contracts development domain issues maintenance security usage work-log feedback; do
  copy_idem "$PL/templates/category-index/$c.md" "$PR/docs/$c/index.md"
done
copy_idem "$PL/templates/graph/index.md" "$PR/docs/graph/index.md"
copy_idem "$PL/templates/graph/.gitignore" "$PR/docs/graph/.gitignore"
```

### 2. CLAUDE.md 안내 블록 append (마커 기반, 멱등)

`${CLAUDE_PROJECT_DIR}/CLAUDE.md` 처리:

- 파일 없음 → 마커 블록만 담아 신규 생성.
- 파일 있고 `<!-- atp:begin -->` 존재 → 마커 사이 내용을 **교체** (반복 실행 시 블록 1개만 유지).
- 파일 있고 마커 없음 → 파일 끝에 마커 블록 **append**.

블록 내용 (고정):

```
<!-- atp:begin -->
## 문서화 정책 (docs-first)
작업 시작 전 `docs/index.md` → 카테고리 `index.md` → 구체 문서 순으로 읽는다.
## 에이전트 팀 운영
`/atp:task [요청]` 으로 Orchestrator+Advisor+Worker 3-tier 모드 진입(명시 호출 전용).
권위 레퍼런스: atp 플러그인 번들 `docs/development/agent-team-protocol.md`.
<!-- atp:end -->
```

### 3. .gitignore 라인 보장

`${CLAUDE_PROJECT_DIR}/.gitignore` 에 `.claude/work-session/` 라인이 정확히 1줄 있도록 보장한다(grep 후 없을 때만 append — 중복 방지).

```bash
GI="$PR/.gitignore"
grep -qxF '.claude/work-session/' "$GI" 2>/dev/null || echo '.claude/work-session/' >> "$GI"
```

### 4. 사용자 안내 출력

- 생성/skip 파일 수 요약.
- 채워야 할 placeholder: `docs/development/verification-strategies.md` 의 `cmd`(프로젝트 검증 명령), `docs/development/document-category-classification.md` 의 불필요 카테고리 정리.
- 스모크: `/atp:task 안녕, 에이전트 팀 로드 확인` 안내.

## 멱등성 규약

- 모든 docs 파일: 존재 시 skip(덮어쓰기는 `--force` 만).
- CLAUDE.md: 마커 기반 교체 → 반복 실행해도 블록 정확히 1개.
- `.gitignore`: 라인 중복 방지(grep 검사).
