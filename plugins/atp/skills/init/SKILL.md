---
name: init
description: atp 플러그인을 소비 프로젝트에 초기화. docs 골격·편집형 검증전략·호스트 지침파일 안내 블록을 멱등 생성. 플러그인 설치 후 프로젝트에서 한 번 실행.
disable-model-invocation: true
---

# /atp:init

atp 플러그인을 **소비 프로젝트** 에 초기화한다. 플러그인 캐시에 둘 수 없는 편집형 docs 골격을 `${CLAUDE_PROJECT_DIR}` 로 생성하고, 호스트 지침파일(자기 호스트의 규약 파일 — 감지 로직은 §2)에 docs-first + 호출 안내 블록을 멱등 append 한다.

## 사용법

```
/atp:init              # 멱등 — 이미 있는 파일은 skip
/atp:init --force      # 기존 파일도 templates/ 원본으로 덮어쓰기
/atp:init --all        # 알려진 지침파일 호환 후보 전부 생성
/atp:init --platforms=claude,codex,gemini   # 생성할 지침파일을 명시 (레거시 호환 플래그)
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
- `project_dir`(소비 프로젝트 루트) 아래에 **자기 호스트의 지침파일 규약 파일**(에이전트가 자기 호스트 규약을 안다)과 **알려진 호환 후보 집합**(레거시 감지용 — bash 구현의 후보 목록)이 존재하는지 ls 검사.
- 반환: 존재하는 파일명 집합 — 이 집합이 블록 삽입 대상 결정 입력으로 쓰인다.

**감지 결과에 따른 분기**:
1. 하나라도 존재 → 존재하는 파일에만 안내 블록을 멱등 삽입. 없는 파일은 생성하지 않음.
2. 하나도 없음 → 기본값: **자기 호스트의 규약 지침파일 1개만 생성**(호스트 자가판정 — 다른 호스트용 파일은 만들지 않음). 추가 파일은 `--all` 또는 `--platforms=...` 플래그 명시 시에만 생성.
3. `--all` 플래그 → 알려진 호환 후보 전부 생성(없으면 신규, 있으면 블록만 삽입).
4. `--platforms=claude,codex,gemini` → 명시된 것만 처리 — 레거시 호환 플래그 (`claude`=CLAUDE.md, `codex`=AGENTS.md, `gemini`=GEMINI.md).

`render_block(call_token)` 으로 블록 문자열을 생성한다:
- `call_token` = 그 지침파일의 호스트에서 ATP task 를 호출하는 토큰. 자기 호스트 대상이면 **이번 세션에서 자신이 호출된 토큰**을 그대로 쓴다. 호스트 이름 분기 없음 — 단일 템플릿에 토큰만 치환.
- 반환: 마커 포함 블록 문자열.

**각 파일 처리 규칙** (모든 지침파일 공통):
- 파일 없음 → 마커 블록만 담아 신규 생성.
- 파일 있고 `<!-- atp:begin/end -->` 마커 존재 → 마커 사이 내용을 **교체** (반복 실행 시 블록 1개만 유지).
- 파일 있고 마커 없음 → 파일 끝에 마커 블록 **append**.

Bash 구현 가이드:

```bash
# detect_guidance_files: project_dir 아래 존재하는 지침파일 감지
# $1=project_dir — ls 검사 대상 경로 (반환값: 존재 파일 목록)
# 아래 후보 목록은 활성 강제 규칙이 아니라 **레거시 호환 감지 입력**이다. 목록에 없는
# 호스트의 규약 파일은 에이전트가 자기 호스트 지식으로 후보에 추가해 검사한다.
detect_guidance_files() {
  local project_dir="$1"
  local found=()
  for f in CLAUDE.md AGENTS.md GEMINI.md; do   # 알려진 호환 후보 (+ 자기 호스트 규약 파일)
    [ -f "$project_dir/$f" ] && found+=("$f")
  done
  echo "${found[@]}"
}

# render_block: 안내 블록 반환 — 호스트 이름 분기 없음, 단일 템플릿
# $1=call_token — 그 지침파일의 호스트에서 ATP task 를 호출하는 토큰
#   (자기 호스트 대상이면 이번 세션에서 자신이 호출된 토큰 그대로).
#   토큰에 `$` 등 특수문자가 포함될 수 있으므로 eval/재확장 없이 bash 치환만 사용한다.
render_block() {
  local call_token="$1"
  local tpl
  tpl="$(cat <<'EOF'
<!-- atp:begin -->
## 문서화 정책 (docs-first)
작업 시작 전 `docs/index.md` → 카테고리 `index.md` → 구체 문서 순으로 읽는다.
## 에이전트 팀 운영
`__ATP_CALL__ [요청]` 으로 Orchestrator+Advisor+Worker 팀 모드 진입(명시 호출 전용).
위임 토폴로지는 호스트 capability 자가판정(Tier A/A-flat/B)을 따른다 — 번들 `docs/development/platform-adapters.md`.
권위 레퍼런스: atp 플러그인 번들 `docs/development/agent-team-protocol.md`.
<!-- atp:end -->
EOF
)"
  printf '%s\n' "${tpl//__ATP_CALL__/$call_token}"
}

# 블록 멱등 삽입 함수
# $1=target_file $2=call_token
upsert_block() {
  local target="$1"
  local call_token="$2"
  local block
  block="$(render_block "$call_token")"
  if [ ! -f "$target" ]; then
    echo "$block" > "$target"; echo "create: $target"; return
  fi
  MARKER_BEGIN="<!-- atp:""begin -->"
  if grep -q "$MARKER_BEGIN" "$target"; then
    # 마커 사이 교체. block 은 반드시 env var 로 넘겨 perl replacement 의 변수 보간을
    # 회피한다 — 호출 토큰에 `$` 가 포함되는 호스트에서 블록 본문의 `$task` 류 토큰을
    # 직접 박으면 perl 이 변수로 해석해 삭제해 버린다(과거 `$task` 소실 회귀 방지).
    BLOCK="$block" perl -i -0pe 's|<!--\s*atp:begin\s*-->.*?<!--\s*atp:end\s*-->|$ENV{BLOCK}|s' "$target"
    echo "update: $target"
  else
    echo "" >> "$target"; echo "$block" >> "$target"
    echo "append: $target"
  fi
}
```

블록 내용은 위 `render_block` 의 단일 템플릿을 권위 원본으로 한다 — 호스트 차이는 `call_token` 치환 1개뿐이다. 타 호스트용 지침파일을 생성할 때(`--all`/`--platforms`)의 토큰은 과거 실측 기록(소스 레포 ADR-0009 부록)을 참고하거나, 모르면 중립 식별자 `task` 를 쓰고 해당 호스트에서의 정확한 토큰 확인을 사용자 안내에 남긴다.

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
2. `.gitignore` 추적 보장: `.atp/work-session/` 라인이 **있으면 1줄 제거**(없으면 skip) — work-session 은 git 추적이 기본(ADR-0010). 구경로 `.claude/work-session/` 라인은 유지.
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

### 3. .gitignore 추적 보장

`.atp/work-session/` 은 durable session history 로 **git 추적이 기본**이다 — `.gitignore` 에 추가하지 않는다. 과거 init/migrate 가 추가했을 수 있는 leftover 라인을 제거한다(ADR-0010).

```bash
GI="$PR/.gitignore"
# 신경로(.atp/work-session/) ignore 라인이 있으면 제거 — 추적 기본 (비파괴: 라인 1개만 삭제)
[ -f "$GI" ] && grep -qxF '.atp/work-session/' "$GI" 2>/dev/null \
  && grep -vxF '.atp/work-session/' "$GI" > "$GI.tmp" && mv "$GI.tmp" "$GI" \
  && echo "untrack-removed: .atp/work-session/ in $GI"
# 구경로 라인(.claude/work-session/)은 leftover ignore 목적으로 유지 — 제거하지 않음.
# (구경로 산출물은 deprecated 이므로 추적하지 않는다)
```

### 4. 사용자 안내 출력

- 생성/skip 파일 수 요약.
- 생성/갱신된 지침파일 목록 + 이 호스트의 task 호출 문법 1줄 — 에이전트가 자신이 이번 세션에서 호출된 토큰으로 안내한다. 타 호스트용 파일을 함께 생성한 경우(`--all`/`--platforms`) 해당 토큰은 확정 표기하지 않고 "그 호스트에서 노출되는 task 호출 토큰 확인 필요" 1줄을 덧붙인다.
- 채워야 할 placeholder: `docs/development/verification-strategies.md` 의 `cmd`(프로젝트 검증 명령), `docs/development/document-category-classification.md` 의 불필요 카테고리 정리.
- 스모크: 이 호스트의 호출 토큰으로 `task 안녕, 에이전트 팀 로드 확인` 1회 실행 안내.
- 마이그레이션 블록이 삽입된 경우: "기존 `.claude/work-session/` 산출물이 있으면 다음 `/atp:task` 진입 시 `.atp/work-session/` 로 자동 이관됩니다 (1회성)."

## 멱등성 규약

- 모든 docs 파일: 존재 시 skip(덮어쓰기는 `--force` 만).
- 지침파일: 마커 기반 교체 → 반복 실행해도 블록 정확히 1개.
- `.gitignore`: 라인 중복 방지(grep 검사).
- `atp:migrate` 블록: 마커 기반 교체 → 반복 init 해도 1개. 단 orchestrator 가 이관 후 삭제하므로, 이관 완료된 프로젝트에서 init 재실행 시 블록이 재삽입될 수 있음(재삽입돼도 1~2 가 no-op 이므로 무해, 3 으로 다시 자기삭제).
