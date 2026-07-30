# Graphify 설치 및 적용

> **2.0.0 재설치 안내**: atp-graphify 2.0.0 부터 add-on 소스가 1.x 의 `addons/` 하위에서 `plugins/atp-graphify` 로 이동해 설치 캐시 루트가 바뀐다. 1.x 설치 사용자는 marketplace update 후 `atp-graphify` 를 재설치해야 한다.

`/graphify` 는 임의의 디렉토리(코드·문서·PDF·이미지 혼재 가능) 를 지식 그래프로 변환하는 Claude Code 스킬이다. 본 템플릿의 에이전트 팀은 graphify 산출물을 1차 탐색 경로로 사용하므로, 프로젝트 구조가 커지면 설치·정례 갱신을 권장한다.

## 1. 사전 조건

- Python 3.x — 설치 도구는 `uv` 권장(§2.2). 전역 `pip` 설치는 비권장
- Node.js (Claude Code 환경)
- 프로젝트 루트에 `.claude/` 쓰기 권한

## 2. 설치

### 2.1 graphify 설치 (패키지 + 스킬)

```bash
uv tool install graphifyy   # 설치 방법 선택 근거는 §2.2
graphify install            # ~/.claude/skills/graphify/ 에 스킬 일습을 원자적으로 배치
```

`graphify install` 은 코어 `SKILL.md` 와 **조건부 로딩용 `references/` sidecar 를 함께** 배치한다. `SKILL.md` 한 파일만 수동 복사하면 안 된다 — 코어의 조건부 포인터가 전부 끊기고, 추출 프롬프트 파일의 경로가 시맨틱 캐시 키로 쓰이므로 캐시 귀속까지 깨진다(업그레이드 후에도 낡은 프롬프트 결과가 재생된다).

배치 확인:

```bash
ls ~/.claude/skills/graphify/SKILL.md ~/.claude/skills/graphify/references/
```

`references/` 가 비어 있거나 없으면 `graphify install` 을 다시 실행한다(자기복구). Claude Code 대상이면 추가 옵션 없이 이 명령으로 충분하다 — 다른 호스트 대상 옵션은 `graphify install --help` 로 확인한다.

스킬은 **사용자 전역**(`~/.claude/skills/`)에 두면 모든 프로젝트에서 `/graphify` 로 호출 가능하다. 프로젝트 단독으로 쓸 거면 `.claude/skills/graphify/` 에 둔다(이 경우도 `references/` 를 함께 둔다).

### 2.2 Python 패키지 설치 방법

배포명은 **`graphifyy`**(y 2개)다. import 명·CLI 명은 `graphify` 다 — `pip install graphify`(y 1개)는 다른 패키지를 가리킨다.

| 방법 | 권장도 | 비고 |
|---|---|---|
| `uv tool install graphifyy` | **1순위** | 격리 환경 + 스킬의 런타임 인터프리터 해석과 정합 |
| `pipx install graphifyy` | 대안 | 격리는 되지만 상류 정본 절차는 uv |
| `pip install graphifyy` | **비권장 (Mac/Windows)** | 상류 문서가 회피를 권고한다. 스킬은 실행 시 작업 디렉토리에 기록된 인터프리터 경로로 Python 을 해석하므로, pip 이 설치한 환경과 어긋나면 `ModuleNotFoundError` 가 난다 |

`/graphify` 스킬은 미설치 시 실행 중 자동 설치를 시도하지만, 위 방법으로 미리 깔아두면 첫 실행이 빨라지고 인터프리터 불일치를 피한다.

패키지 설치 확인:

```bash
graphify --version
```

`graphify <버전>` 1줄이 출력되면 성공이다. 실패하면 콘솔 스크립트가 PATH 에 없다는 뜻이므로 §2.2 방법으로 재설치한다.

> `python3 -c "import graphify; print(graphify.__version__)"` 형태는 쓰지 않는다 — 배포에 그 속성이 없고, 시스템 `python3` 는 패키지가 설치된 환경과 다를 수 있다.

### 2.3 스킬 로드 확인

새 Claude Code 세션에서 `/graphify --help` 호출. 스킬이 로드되고 usage 가 출력되면 성공.

## 3. 프로젝트 초기 세팅

### 3.1 디렉토리 레이아웃

```
docs/graph/
├── index.md           # 메타 (커밋 대상)
├── .gitignore         # 본체 무시 (커밋 대상)
└── <scope>/           # 각 scope 별 산출물 (gitignore)
    ├── graph.html
    ├── graph.json
    ├── GRAPH_REPORT.md
    └── manifest.json, .graphify_* …   # 증분 갱신 상태 (배치 시 함께 이동)
                                       # 추출 캐시는 여기가 아니라 스캔 루트에 남는다 — §4.2 참조
```

`docs/graph/index.md` 와 `.gitignore` 는 본 템플릿에 포함돼 있다. 그대로 커밋한다.

### 3.2 Scope 설계 원칙

한 프로젝트에 여러 scope 를 병행 운용할 수 있다. 일반적 분할:

| Scope 예시 | 대상 | 언제 유용 |
|---|---|---|
| `src` | `src/**` 전체 | 코드베이스 전체 구조 파악 |
| `src-features` | `src/features/**` | 도메인 로직만 집중 |
| `docs` | `docs/**` | 문서 간 참조 네트워크 |
| `full` | 레포 전체 | 코드+문서 교차 관점 (비용 큼) |
| `adapters-opencode` | `adapters/opencode` | 단일 어댑터 트리 (경로에 `/` 가 있어 slug 로 치환한 예) |

**시작 권장**: `src` 단일 scope 로 시작. 모듈이 커져 탐색 비용이 올라가면 scope 를 쪼갠다.

scope 명은 디렉토리명이 되므로 파일시스템 안전해야 한다 — 대상 경로에 `/` 가 있으면 `-` 로 치환한다(`adapters/opencode` → `adapters-opencode`). 대상 경로 자체는 index.md 의 `target`·`source_file_base` 에 적는다.

### 3.3 그래프 코퍼스에서 제외하기

scope 는 *무엇을 그래프화할지* 를 정하고, ignore 규칙은 *그 안에서 무엇을 뺄지* 를 정한다. 코퍼스가 원치 않는 파일로 채워질 때는 scope 를 쪼개지 말고 ignore 규칙으로 해결한다.

- **`.gitignore` 는 자동으로 존중된다.** graphify 는 대상 경로의 조상 디렉토리 체인까지 올라가며 ignore 파일을 수집하므로, 레포 루트 `.gitignore` 가 서브디렉토리 scope 빌드에도 적용된다. git 이 무시하는 재생성 산출물은 별도 설정 없이 그래프에서도 빠진다.
- **`.graphifyignore` 는 그래프에서만 추가로 뺄 때 쓴다.** `.gitignore` 를 먼저 읽고 `.graphifyignore` 를 나중에 병합하는 순서이며, **더 제외할 수만 있고 재포함(re-include)은 불가능**하다 — `.gitignore` 로 빠진 것을 그래프에만 되살릴 수는 없다.
- 의존성 디렉토리 같은 대표적 노이즈 트리는 별도 설정 없이도 스캔에서 잘린다.

선택 기준:

| 상황 | 어디에 쓰나 |
|---|---|
| git 에서도 무시해야 할 재생성 산출물 (설치본·빌드 출력) | `.gitignore` |
| git 은 추적해야 하지만 그래프에서만 빼고 싶은 트리 (대용량 픽스처·벤더 사본·생성 코드) | `.graphifyignore` |

제외가 반영됐는지는 생성 직후 `GRAPH_REPORT.md` 의 파일·노드 규모로 확인한다 — 예상보다 크면 의도하지 않은 트리가 섞였다는 신호다.

## 4. 실행

### 4.1 기본 호출

```
/graphify src
```

산출물은 **호출 시점 cwd 의 `graphify-out/`** 에 생성된다. 스킬 런북은 출력 경로를 바꾸는 환경변수를 존중하지 않으므로(런북이 경로를 직접 넘긴다) **실행 후 이동(§4.2)이 유일한 배치 경로**다. 배치를 잊어도 `graphify-lookup-advisor`/`graph-refresh-checker` 가 `graphify-out/` 잔존을 Glob 으로 감지해 **no-graph (misplaced-output)** 사유로 반환한다 — 오판(그래프가 있는데 research 낭비)은 막아주지만, 배치·메타 갱신 자체는 `graphify-update-advisor` 의 책임이다(§5.3).

### 4.2 산출물 배치 (park)

```bash
# 1) 생성 (레포 루트에서)
/graphify src

# 2) scope 디렉토리로 payload 통째 이동 (scope 명은 §3.2 slug 규칙)
mkdir -p docs/graph/src
mv graphify-out/* graphify-out/.[!.]* docs/graph/src/ 2>/dev/null

# 3) 빈 작업 디렉토리 제거 (§4.4 — 잔존 graph.json 이 이후 질의를 가로채는 것을 막는다)
rmdir graphify-out
```

**개별 파일을 열거하지 않는다.** `graph.json`·`graph.html`·`GRAPH_REPORT.md` 외에 증분 갱신 상태(`manifest.json`, `.graphify_*` 사이드카)가 같은 디렉토리에 있고, graphify 버전에 따라 새 사이드카가 추가된다 — 열거 목록은 조용히 stale 되고 그 대가는 `--update` 의 전량 재추출이다. 특히 **`manifest.json` 을 빼먹으면 증분 갱신이 매번 전체 재추출로 퇴화**한다.

> **추출 캐시는 예외 — 옮기지 않는다.** 산출물은 호출 시점 cwd 에 쓰이지만 **추출 캐시는 그래프 대상 경로(스캔 루트) 기준**으로 따로 관리된다. 두 위치는 `/graphify .` 처럼 cwd 와 대상 경로가 같을 때만 일치하고, `/graphify <서브경로>` 에서는 갈린다 — 이때 캐시는 `<대상경로>/graphify-out/cache/` 에 생기며 **거기 있어야 다음 실행이 찾는다**. 정본 디렉토리로 옮기면 캐시 재사용이 깨져 매번 다시 추출한다. 이 캐시 전용 디렉토리는 `graph.json` 을 담지 않으므로 §4.4 의 질의 가로채기 대상도 아니다. 정리하려면 옮기지 말고 그냥 두거나 삭제한다(삭제하면 다음 실행이 재생성한다).

예외 1건: 날짜 서브디렉토리(`graphify-out/<YYYY-MM-DD>/`)는 graphify 가 보호된 그래프를 덮어쓸 때 만드는 자체 백업이다. park 하지 않고 버린다(정본 사본은 방금 옮긴 것).

**증분 갱신(`--update`)은 역방향으로 되돌린 뒤 실행한다** — 런북이 cwd 의 `graphify-out/` 을 읽는다:

```bash
mkdir -p graphify-out
mv docs/graph/src/* docs/graph/src/.[!.]* graphify-out/ 2>/dev/null
/graphify src --update
# 끝나면 위 2)~3) 반복
```

### 4.3 메타 갱신

`docs/graph/index.md` frontmatter 와 Scopes 표를 갱신한다 (템플릿의 "갱신 시 체크리스트" 참조):

```yaml
---
kind: graphify-meta
last_generated_at: 2026-04-30T10:00:00+09:00
source_commit: <current HEAD sha>
scopes:
  - name: src
    target: src/**
    generated_at: 2026-04-30T10:00:00+09:00
---
```

### 4.4 질의 전 필수 점검 — `graphify-out/` 잔존 정리

스킬은 호출 시점 cwd 에 `graphify-out/graph.json` 이 있으면 **탐지·코퍼스 점검을 전부 건너뛰고 그 파일로 즉답**한다. 정본은 `docs/graph/<scope>/` 이므로, 잔존 사본이 있으면 질의가 정본이 아니라 낡은 사본을 근거로 답한다 — 오류 메시지 없는 조용한 오답이다.

```bash
ls graphify-out/graph.json 2>/dev/null   # 출력이 있으면 질의 전에 §4.2 배치를 완료한다
```

`rm -rf graphify-out` 으로 해결하지 않는다 — 증분 갱신 상태까지 날려 다음 `--update` 가 전량 재추출이 된다. §4.2 의 배치(park)로 옮긴 뒤 빈 디렉토리만 `rmdir` 한다.

## 5. 에이전트 팀과의 통합

본 템플릿은 graphify 산출물을 3 지점에서 참조한다:

### 5.1 `graphify-lookup-advisor` — 1차 탐색 진입점

모든 조사 요청의 첫 관문. `docs/graph/index.md` + `graph.json` 을 뒤져 히트 여부를 판정하고, miss 시 `research-advisor` 로 에스컬레이션한다.

### 5.2 `graph-refresh-checker` — staleness 판정

- `docs/graph/index.md` 의 `source_commit` 과 현재 HEAD 를 비교
- scope 별 변경 라인·구조적 시그널(export/route/schema 정의 변경) 집계
- 판정: `fresh` / `partial-stale` / `fully-stale` / `no-graph`
- **판정만** 수행. 재생성은 다음 단계가 담당.

### 5.3 `graphify-update-advisor` — 재생성 지휘

- `graph-refresh-checker` 판정 수신 후 재생성 대상 scope 확정
- 폐기된 scope 디렉토리 `rm -rf`
- orchestrator 에게 `/graphify` 재호출 요청
- 산출물 배치(park, §4.2) — `graphify-out/` payload 를 `docs/graph/<scope>/` 로 이동
- 재생성 완료 후 `docs/graph/index.md` 메타 갱신

## 6. 갱신 트리거

다음 시점에 `graph-refresh-checker` 를 선제 호출해 판정을 받는다:

- **첫 작업 진입 시** 그래프가 없고 코드베이스가 비어있지 않을 때
- **대규모 리팩터링 직후** (10개 이상 파일 이동/삭제, 모듈 신설)
- **아키텍처/전체 구조 질문 수신 시**
- **커밋/PR 직전 구조 변경을 동반한 경우**

판정이 `partial-stale` / `fully-stale` / `no-graph` 이면 `/graphify` 재호출.

## 7. 커밋 정책

- `docs/graph/index.md` — **커밋 대상** (메타 정보)
- `docs/graph/.gitignore` — **커밋 대상**. `/atp:init` 스캐폴딩이 allowlist 형태(`*` / `!index.md` / `!.gitignore`)로 생성한다. 무시 규칙을 루트 `.gitignore` 에 직접 둔 프로젝트는 이 파일이 없을 수 있다 — **둘 중 한 곳에만 있으면 된다**(양쪽에 두면 중복이지 오류는 아니다)
- `docs/graph/<scope>/` 전체 — **gitignore** (`graph.html`·`graph.json`·`GRAPH_REPORT.md` + 증분 상태. 재생성 가능, 저장소 비대화 방지)

## 8. 자주 겪는 문제

| 증상 | 원인 | 조치 |
|---|---|---|
| `/graphify` 호출 시 "skill not found" | 스킬 미배치 | `~/.claude/skills/graphify/SKILL.md` 및 `references/` 존재 확인 → 없으면 `graphify install` |
| `ModuleNotFoundError: graphify` | Python 패키지 미설치 | `uv tool install graphifyy` 수동 실행 |
| `graph.json` 은 생겼는데 `graph.html` 이 없음 | `--no-viz` 로 시각화 생성을 건너뜀 | 옵션 없이 재실행 (`--no-viz` 는 HTML 만 생략한다 — JSON 이 정본이다) |
| 큰 레포에서 토큰 급증 | scope 가 너무 넓음 | scope 를 하위 디렉토리 단위로 쪼갬 (`src-features`, `src-infra` 등) |
| `graph-refresh-checker` 가 항상 `fully-stale` 반환 | scope 의 `target` 경로가 잘못됨 | `docs/graph/index.md` 의 scope 표에서 대상 경로 수정 |

## 9. 고급 옵션 (상세는 단일 `SKILL.md` 가 아니다)

graphify 스킬은 **코어 `SKILL.md` + 조건부 로딩 `references/` sidecar** 구조다. 고급 옵션의 실제 절차는 코어가 아니라 sidecar 에 있고, 코어에는 조건부 포인터만 남아 있다.

| 알고 싶은 것 | 문서 (`~/.claude/skills/graphify/` 기준) |
|---|---|
| `--update` / `--cluster-only` 증분·클러스터 절차 | `references/update.md` |
| `query` / `path` / `explain` 질의 | `references/query.md` |
| export 계열(Obsidian·그래프 DB·GraphML·SVG·MCP 등) | `references/exports.md` |

그 외 주제(GitHub 클론·다중 경로 병합·미디어 전사·커밋 훅·서브에이전트 추출 스펙)는 `ls ~/.claude/skills/graphify/references/` 로 파일명을 확인해 해당 파일을 읽는다. **CLI 실제 표면은 스킬 문서가 다루는 범위보다 넓다** — 옵션 전수 확인은 `graphify --help` 를 쓴다.

- `--mode deep` — 추론 엣지(INFERRED) 를 풍부하게. 토큰·시간 증가
- `--update` — 변경된 파일만 증분 갱신 (선행 조건: §4.2 의 되돌리기 절차)
- `--cluster-only` — 기존 graph 에 클러스터링만 재실행. **후속 절차는 `references/update.md` 지시를 따른다**(전체 단계를 다시 돌리면 실패한다)
- `--watch` — 파일 변경 감시 + 자동 재생성 (LLM 없이 구조적 변경만)
- `--no-viz` — HTML 시각화 생성을 건너뛴다(JSON 은 그대로 생성)
- `/graphify query "<question>"` — 생성된 graph 에 질의. `references/query.md` 가 요구하는 **선행 단계(어휘 확장)를 건너뛰지 않는다**

## 10. graph 갱신 이월 금지(no-defer) 정책

**핵심 원칙: graph 갱신을 다음 세션으로 미루지 않는다.** `graph-refresh-checker` 가 `partial-stale` / `fully-stale` / `no-graph` 판정을 내리면 **본 세션 또는 commit 시점**에 처리한다. 이월(deferral) 옵션 자체를 두지 않는다.

### 10.1 처리 경로

#### (A) 자동 처리 — 코드 전용 변경

프로젝트가 post-commit hook 을 구성한 경우, 코드 디렉토리의 구조 변경은 commit 직후 hook 이 background 로 AST 만 재생성한다(LLM 불필요, commit 자체를 차단하지 않음). orchestrator 는 별도 행동 없이 보고서에 `graph_refresh.handled_by: post-commit-hook` 만 기록한다. hook 구현·트리거 경로·재생성 로그 위치는 **프로젝트별로 정의**한다(소비 프로젝트 hook). 세션 종료 직전 hook 재생성 로그를 1회 확인해 실패가 있으면 사용자에게 보고한다.

#### (B) 즉시 또는 background 분리 — 문서/이미지 포함 변경

문서·이미지 변경은 LLM semantic 추출이 필요해 AST hook 이 처리할 수 없다. 다음 두 경로 중 하나로 처리한다 — **이월(다음 세션) 금지**.

- **(B-1) 인스턴스 내 즉시 처리**: 변경 규모가 작거나(파일 ≤ 5개) 사용자 대기가 수용 가능하면 본 세션에서 `/graphify <scope>` 를 직접 호출한다.
- **(B-2) background subagent 분리**: 변경 규모가 크거나(파일 > 5개) 풀 scope 빌드면 `general-purpose` subagent 를 `run_in_background: true` 로 호출해 graphify 실행을 별도 컨텍스트로 분리한다. 본 세션은 사용자에게 한 줄 고지 후 종료 가능하다. 이월 금지 정책이므로 (A)/(B) 처리 경로를 사용자에게 묻지 않는다.

### 10.2 의사결정 표

| 변경 유형 | 처리 경로 | 사용자 인터럽트 |
|---|---|---|
| 코드 전용 | (A) hook | 없음 (자동) |
| 문서/이미지 ≤ 5 파일 | (B-1) | 한 줄 고지 |
| 문서/이미지 > 5 또는 풀 scope | (B-2) | 한 줄 고지 |
| 코드 + 문서 혼합 | (A) + (B) | 한 줄 고지 |
| `no-graph` (최초 생성) | (B-2) | 한 줄 고지 |

### 10.3 금지 항목 (구 규약 — 폐기됨)

- ❌ Open Items 에 "다음 세션 시작 시 자동 실행" 태그로 이월
- ❌ deviation(이월) 옵션
- ❌ `consecutive_defers` 카운터
- ❌ `AskUserQuestion` 으로 (A)/(B) 처리 경로 결정을 사용자에게 위임 (이월 자체가 없으므로 묻지 않는다)

### 10.4 보고서 기록

`report.md` 의 `graph_refresh` 섹션에 판정과 처리를 기록한다:

```yaml
graph_refresh:
  decision: handled_inline | handled_background | handled_by_hook | fresh | no-op
  judgment: fresh | partial-stale | fully-stale | no-graph
  scopes_processed: [...]
  background_subagent_id: <id>   # (B-2) 의 경우만
  reason: <한 줄>
```

**배경**: 운영 중 graph 갱신이 여러 세션에 걸쳐 반복 이월되는 것을 관찰하고 명시적 정정을 거친 결과, 이월 옵션 자체를 규약에서 제거했다.

## 관련 문서

- `agent-team-protocol.md` (base atp 번들 — `${CLAUDE_PLUGIN_ROOT}/docs/development/`) — §9 확장 트리거 레지스트리 (graph scope ≥ 5 시 lookup 병렬 worker 승격)
- `documentation-guidelines.md` (base atp 번들 — `${CLAUDE_PLUGIN_ROOT}/docs/development/`) — graphify 산출물 관리 규칙
