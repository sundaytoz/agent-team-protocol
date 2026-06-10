---
name: init
description: atp 플러그인을 소비 프로젝트에 초기화. docs 골격·편집형 검증전략·플랫폼 지침파일(CLAUDE.md/AGENTS.md/GEMINI.md) 안내 블록을 멱등 생성. 플러그인 설치 후 프로젝트에서 한 번 실행.
disable-model-invocation: true
---

# /atp:init

atp 플러그인을 **소비 프로젝트** 에 초기화한다. 플러그인 캐시에 둘 수 없는 편집형 docs 골격을 `${CLAUDE_PROJECT_DIR}` 로 생성하고, 플랫폼 지침파일(CLAUDE.md / AGENTS.md / GEMINI.md)에 docs-first + 호출 안내 블록을 멱등 append 한다.

## 사용법

```
/atp:init              # 멱등 — 이미 있는 파일은 skip
/atp:init --force      # 기존 파일도 templates/ 원본으로 덮어쓰기
/atp:init --all        # CLAUDE.md + AGENTS.md + GEMINI.md 3개 모두 생성
/atp:init --platforms=claude,codex,gemini   # 생성할 플랫폼 명시
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

### 2. 지침파일 안내 블록 append (감지 + 옵트인, 마커 기반, 멱등)

#### 감지 로직

`detect_guidance_files(project_dir)` 를 수행한다:
- `project_dir`(소비 프로젝트 루트) 아래에 `CLAUDE.md` / `AGENTS.md` / `GEMINI.md` 가 존재하는지 ls 검사.
- 반환: 존재하는 파일명 집합 — 이 집합이 블록 삽입 대상 결정 입력으로 쓰인다.

**감지 결과에 따른 분기**:
1. 하나라도 존재 → 존재하는 파일에만 해당 플랫폼 블록을 멱등 삽입. 없는 파일은 생성하지 않음.
2. 하나도 없음 → 기본값: `CLAUDE.md` 만 생성(현행 동작 보존, 회귀 방지). `AGENTS.md` / `GEMINI.md` 는 `--all` 또는 `--platforms=...` 플래그 명시 시에만 생성.
3. `--all` 플래그 → `CLAUDE.md` / `AGENTS.md` / `GEMINI.md` 3개 모두 생성(없으면 신규, 있으면 블록만 삽입).
4. `--platforms=claude,codex,gemini` → 명시된 플랫폼만 처리 (`claude`=CLAUDE.md, `codex`=AGENTS.md, `gemini`=GEMINI.md).

`render_block(platform)` 으로 블록 문자열을 생성한다:
- `platform`("claude"|"codex"|"gemini") 이 어느 호출 문법 블록을 낼지 결정하는 분기 키로 쓰인다.
- 반환: 해당 플랫폼의 마커 포함 블록 문자열.

**각 파일 처리 규칙** (CLAUDE.md / AGENTS.md / GEMINI.md 공통):
- 파일 없음 → 마커 블록만 담아 신규 생성.
- 파일 있고 `<!-- atp:begin/end -->` 마커 존재 → 마커 사이 내용을 **교체** (반복 실행 시 블록 1개만 유지).
- 파일 있고 마커 없음 → 파일 끝에 마커 블록 **append**.

Bash 구현 가이드:

```bash
# detect_guidance_files: project_dir 아래 존재하는 지침파일 감지
# $1=project_dir — ls 검사 대상 경로 (반환값: 존재 파일 목록)
detect_guidance_files() {
  local project_dir="$1"
  local found=()
  for f in CLAUDE.md AGENTS.md GEMINI.md; do
    [ -f "$project_dir/$f" ] && found+=("$f")
  done
  echo "${found[@]}"
}

# render_block: platform 에 맞는 안내 블록 반환
# $1=platform ("claude"|"codex"|"gemini") — 호출 문법 분기 키 (이 값만으로 블록 결정)
render_block() {
  local platform="$1"
  case "$platform" in
    claude)
      cat <<'EOF'
<!-- atp:begin -->
## 문서화 정책 (docs-first)
작업 시작 전 `docs/index.md` → 카테고리 `index.md` → 구체 문서 순으로 읽는다.
## 에이전트 팀 운영
`/atp:task [요청]` 으로 Orchestrator+Advisor+Worker 3-tier 모드 진입(명시 호출 전용).
권위 레퍼런스: atp 플러그인 번들 `docs/development/agent-team-protocol.md`.
<!-- atp:end -->
EOF
      ;;
    codex)
      cat <<'EOF'
<!-- atp:begin -->
## 문서화 정책 (docs-first)
작업 시작 전 `docs/index.md` → 카테고리 `index.md` → 구체 문서 순으로 읽는다.
## 에이전트 팀 운영 (Codex)
`$atp:task [요청]` 으로 Orchestrator+Advisor+Worker 3-tier 모드 진입(명시 호출 전용).
※ Codex 는 skill 을 `$` 멘션 접두로 호출한다. 번들 skill 은 `plugin:skill` 콜론 namespace(`atp:task`/`atp:init`)로 노출 (verified-empirical 2026-06-10, codex-cli 0.138.0).
권위 레퍼런스: atp 플러그인 번들 `docs/development/agent-team-protocol.md`.
<!-- atp:end -->
EOF
      ;;
    gemini)
      cat <<'EOF'
<!-- atp:begin -->
## 문서화 정책 (docs-first)
작업 시작 전 `docs/index.md` → 카테고리 `index.md` → 구체 문서 순으로 읽는다.
## 에이전트 팀 운영 (Gemini)
`/atp:task [요청]` 으로 Orchestrator+Advisor+Worker 모드 진입(명시 호출 전용).
※ Gemini 는 namespaced custom command 를 콜론으로 노출한다(`/ns:cmd`). 배포형(command vs skill)·정확 namespace 는 install 스모크로 확정 예정 (TODO:실측).
※ Gemini 는 subagent→subagent 재귀가 금지되어 ATP 는 Tier A-flat(평탄 위임)로 동작한다.
권위 레퍼런스: atp 플러그인 번들 `docs/development/agent-team-protocol.md`.
<!-- atp:end -->
EOF
      ;;
  esac
}

# 블록 멱등 삽입 함수
# $1=target_file $2=platform
upsert_block() {
  local target="$1"
  local platform="$2"
  local block
  block="$(render_block "$platform")"
  if [ ! -f "$target" ]; then
    echo "$block" > "$target"; echo "create: $target"; return
  fi
  MARKER_BEGIN="<!-- atp:""begin -->"
  if grep -q "$MARKER_BEGIN" "$target"; then
    # 마커 사이 교체. block 은 반드시 env var 로 넘겨 perl replacement 의 변수 보간을
    # 회피한다 — 블록 본문에 `$task` 같은 `$` 토큰이 있으면 직접 박을 때 perl 이
    # 변수로 해석해 삭제해 버린다(Codex 블록의 `$task` 소실 회귀 방지).
    BLOCK="$block" perl -i -0pe 's|<!--\s*atp:begin\s*-->.*?<!--\s*atp:end\s*-->|$ENV{BLOCK}|s' "$target"
    echo "update: $target"
  else
    echo "" >> "$target"; echo "$block" >> "$target"
    echo "append: $target"
  fi
}
```

블록 내용은 위 `render_block` bash 구현의 각 heredoc 케이스를 권위 원본으로 한다(CLAUDE=`claude` 케이스, AGENTS=`codex` 케이스, GEMINI=`gemini` 케이스).

#### atp:migrate 블록 멱등 삽입

안내 블록(`atp:begin`/`atp:end`) upsert 직후, **동일 대상 파일 집합**에 `atp:migrate` 블록을 별도 멱등 삽입한다.

> **가드**: `.claude/work-session/` 디렉토리가 프로젝트에 존재할 때만 삽입한다. 신규 프로젝트는 이관 대상 디렉토리가 없으므로 migrate 블록이 불필요하다(노이즈 회피).

```bash
# render_migrate_block: atp:migrate 블록 문안 반환 (인자 없음 — 3사 공통 단일 문안)
render_migrate_block() {
  cat <<'EOF'
<!-- atp:migrate:begin -->
## [ATP 1회성 마이그레이션 — 완료 후 이 블록을 삭제하시오]

ATP 산출물 경로가 `.claude/work-session/` 에서 `.atp/work-session/` 로 이전되었습니다.
다음 `/atp:task` 또는 `/atp:init` 진입 시, 메인 에이전트(orchestrator)는 **작업 시작 전에**
아래를 순서대로 1회 수행한 뒤 이 블록(atp:migrate:begin~end)을 이 파일에서 제거한다:

1. 구 디렉토리 존재 검사: `[ -d .claude/work-session ]`.
   - 존재하고 `.atp/work-session` 이 없으면: `mkdir -p .atp && git mv .claude/work-session .atp/work-session`
     (git 미추적 환경이면 `mv .claude/work-session .atp/work-session`). **삭제 아님 — 이동.**
   - 둘 다 존재(부분 이관)하면: 구 디렉토리 내 세션들을 `.atp/work-session/` 로 mv 병합(동명 sid 덮어쓰지 않음).
   - 구 디렉토리 없으면: no-op.
2. `.gitignore` 보장: `.atp/work-session/` 라인이 없으면 1줄 append (있으면 skip).
3. 위 1~2 완료 후, **이 `atp:migrate:begin`~`atp:migrate:end` 블록 전체를 이 지침파일에서 삭제**한다
   (다음 세션 컨텍스트 비용 0). 삭제는 이 파일 1개에 대한 비파괴 in-place 편집이며 §6 게이트 대상 아님.

> 이 작업은 멱등하다. 이미 이관됐고 블록만 남았다면 1~2 는 no-op, 3(블록 삭제)만 수행한다.
<!-- atp:migrate:end -->
EOF
}

# upsert_migrate_block: atp:migrate 블록 멱등 삽입 (안내 블록과 별도 마커)
# $1=target_file — 삽입 대상 지침파일 (이미 §2 안내블록 upsert 로 존재 보장)
upsert_migrate_block() {
  local target="$1"
  local mb me block
  mb="<!-- atp:""migrate:begin -->"; me="<!-- atp:""migrate:end -->"
  block="$(render_migrate_block)"   # 위 문안 heredoc 반환 (인자 없음 — 플랫폼 무관)
  if grep -q "$mb" "$target"; then
    BLOCK="$block" perl -i -0pe \
      's|<!--\s*atp:migrate:begin\s*-->.*?<!--\s*atp:migrate:end\s*-->|$ENV{BLOCK}|s' "$target"
    echo "migrate-update: $target"
  else
    echo "" >> "$target"; echo "$block" >> "$target"
    echo "migrate-append: $target"
  fi
}
```

호출: §2 의 안내블록 upsert 루프와 동일 대상 집합에서, **`[ -d "$PR/.claude/work-session" ]` 가드** 통과 시 `upsert_migrate_block "$target"` 1줄 추가. 가드 실패(신규 프로젝트)면 migrate 블록 삽입 전체 skip.

### 3. .gitignore 라인 보장

`${CLAUDE_PROJECT_DIR}/.gitignore` 에 `.atp/work-session/` 라인이 정확히 1줄 있도록 보장한다(grep 후 없을 때만 append — 중복 방지).

```bash
GI="$PR/.gitignore"
# 신경로 보장 (없을 때만 append)
grep -qxF '.atp/work-session/' "$GI" 2>/dev/null || echo '.atp/work-session/' >> "$GI"
# 구경로 라인(.claude/work-session/)은 leftover ignore 목적으로 유지 — 제거하지 않음.
# (마이그레이션 미수행 프로젝트의 .claude/work-session/ 가 추적되지 않도록)
```

### 4. 사용자 안내 출력

- 생성/skip 파일 수 요약.
- 생성된 지침파일 목록 + 각 플랫폼 호출 문법 안내:
  - CLAUDE.md 생성/갱신 → "Claude Code: `/atp:task [요청]`"
  - AGENTS.md 생성/갱신 → "Codex: `$atp:task [요청]` (`$` skill 멘션 접두, verified-empirical 2026-06-10)"
  - GEMINI.md 생성/갱신 → "Gemini: `/atp:task [요청]` (TODO:실측 — 배포형 확정 전)"
- 채워야 할 placeholder: `docs/development/verification-strategies.md` 의 `cmd`(프로젝트 검증 명령), `docs/development/document-category-classification.md` 의 불필요 카테고리 정리.
- 스모크: Claude Code `/atp:task 안녕, 에이전트 팀 로드 확인` 안내.
- 마이그레이션 블록이 삽입된 경우: "기존 `.claude/work-session/` 산출물이 있으면 다음 `/atp:task` 진입 시 `.atp/work-session/` 로 자동 이관됩니다 (1회성)."

## 멱등성 규약

- 모든 docs 파일: 존재 시 skip(덮어쓰기는 `--force` 만).
- 지침파일(CLAUDE.md / AGENTS.md / GEMINI.md): 마커 기반 교체 → 반복 실행해도 블록 정확히 1개.
- `.gitignore`: 라인 중복 방지(grep 검사).
- `atp:migrate` 블록: 마커 기반 교체 → 반복 init 해도 1개. 단 orchestrator 가 이관 후 삭제하므로, 이관 완료된 프로젝트에서 init 재실행 시 블록이 재삽입될 수 있음(재삽입돼도 1~2 가 no-op 이므로 무해, 3 으로 다시 자기삭제).
