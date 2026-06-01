# Graphify 설치 및 적용

`/graphify` 는 임의의 디렉토리(코드·문서·PDF·이미지 혼재 가능) 를 지식 그래프로 변환하는 Claude Code 스킬이다. 본 템플릿의 에이전트 팀은 graphify 산출물을 1차 탐색 경로로 사용하므로, 프로젝트 구조가 커지면 설치·정례 갱신을 권장한다.

## 1. 사전 조건

- Python 3.x (pip 또는 pipx)
- Node.js (Claude Code 환경)
- 프로젝트 루트에 `.claude/` 쓰기 권한

## 2. 설치

### 2.1 graphify 스킬 배치 (사용자 전역)

```bash
mkdir -p ~/.claude/skills/graphify
# SKILL.md 를 graphify 배포처에서 받아 ~/.claude/skills/graphify/SKILL.md 로 배치
```

스킬은 **사용자 전역**(`~/.claude/skills/`) 에 두면 모든 프로젝트에서 `/graphify` 트리거로 호출 가능하다. 프로젝트 단독으로만 쓸 거면 `.claude/skills/graphify/` 에 둔다.

### 2.2 Python 패키지 설치

`/graphify` 스킬은 실행 시 자동으로 Python 패키지를 설치하려 시도한다:

```bash
pip install graphifyy
```

수동으로 미리 깔아두면 첫 실행이 빨라진다. pipx 사용을 권장:

```bash
pipx install graphifyy
```

설치 확인:

```bash
python3 -c "import graphify; print(graphify.__version__)"
```

### 2.3 설치 확인

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
    └── audit.md
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

**시작 권장**: `src` 단일 scope 로 시작. 모듈이 커져 탐색 비용이 올라가면 scope 를 쪼갠다.

## 4. 실행

### 4.1 기본 호출

```
/graphify src
```

default output 은 `graphify-out/` 이다. 본 템플릿 규약은 **scope 별 `docs/graph/<scope>/`** 이므로 실행 후 산출물을 이동하거나, 다음 절차대로 출력 경로를 지정한다.

### 4.2 Scope 경로로 산출물 배치

graphify CLI 옵션을 쓰거나, 실행 후 `mv` 로 옮긴다. 가장 단순한 방식:

```bash
# 생성
/graphify src

# scope 디렉토리로 이동
mkdir -p docs/graph/src
mv graphify-out/graph.html graphify-out/graph.json graphify-out/GRAPH_REPORT.md docs/graph/src/
# audit.md 가 있다면 함께 이동. 파일명은 graphify 버전에 따라 다를 수 있음.
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
- `docs/graph/.gitignore` — **커밋 대상**
- `docs/graph/<scope>/*.html`, `*.json`, `audit.md` — **gitignore** (재생성 가능, 저장소 비대화 방지)

## 8. 자주 겪는 문제

| 증상 | 원인 | 조치 |
|---|---|---|
| `/graphify` 호출 시 "skill not found" | 스킬 미배치 | `~/.claude/skills/graphify/SKILL.md` 존재 확인 |
| `ModuleNotFoundError: graphify` | Python 패키지 미설치 | `pip install graphifyy` 수동 실행 |
| 실행은 되는데 `graph.html` 만 있고 `graph.json` 없음 | `--no-viz` 또는 구버전 | 옵션 없이 재실행, graphify 버전 확인 |
| 큰 레포에서 토큰 급증 | scope 가 너무 넓음 | scope 를 하위 디렉토리 단위로 쪼갬 (`src-features`, `src-infra` 등) |
| `graph-refresh-checker` 가 항상 `fully-stale` 반환 | scope 의 `target` 경로가 잘못됨 | `docs/graph/index.md` 의 scope 표에서 대상 경로 수정 |

## 9. 고급 옵션 (상세는 `~/.claude/skills/graphify/SKILL.md` 참조)

- `--mode deep` — 추론 엣지(INFERRED) 를 풍부하게. 토큰·시간 증가
- `--update` — 변경된 파일만 증분 갱신
- `--cluster-only` — 기존 graph 에 클러스터링만 재실행
- `--watch` — 파일 변경 감시 + 자동 재생성 (LLM 없이 구조적 변경만)
- `/graphify query "<question>"` — 생성된 graph 에 질의 (BFS 탐색)

## 관련 문서

- [agent-team-protocol.md](./agent-team-protocol.md) — §9 확장 트리거 레지스트리 (graph scope ≥ 5 시 lookup 병렬 worker 승격)
- [documentation-guidelines.md](./documentation-guidelines.md) — graphify 산출물 관리 규칙
