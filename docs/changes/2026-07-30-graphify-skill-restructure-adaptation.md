---
kind: changes
title: 상류 graphify 스킬 구조 재편 대응 — 거짓 안내 제거 + 산출물 레이아웃 정본화
date: 2026-07-30
related_adr: ADR-0019
versions:
  base: 2.9.0 → 2.10.0
  addon: 2.2.0 → 2.3.0
---

# 상류 graphify 스킬 구조 재편 대응 (base 2.10.0 / add-on 2.3.0)

세션 20260729-172132(조사 → 설계 → 구현). 배치 규약 결정 근거: [ADR-0019](../adr/ADR-0019-graph-artifact-scope-directory-layout.md).

> 이 문서는 **상류 graphify 릴리스 번호를 인용하지 않는다.** 릴리스별 기능 귀속의 유일한 출처가 상류 CHANGELOG 이고(독립 확증 미확보), 번호를 박으면 다음 업그레이드에 즉시 stale 된다. 설치된 버전은 `graphify --version` 으로 확인한다.

## 무엇이 왜 바뀌었나

상류 graphify 스킬이 **코어 `SKILL.md` + 조건부 로딩 `references/` sidecar 구조로 재편**되고 **데이터 오염 방어 가드가 대폭 늘어난** 방향으로 크게 바뀌었다. 그 결과 우리 add-on 문서·에이전트 정의에 **"따라하면 실패하는" 거짓 안내**가 생겼다 — 설치 절차(단일 파일 수동 배치), 버전 확인 명령(실행 실패 실측), "고급 옵션 상세는 `SKILL.md` 참조"(상세가 sidecar 로 이동).

조사 과정에서 업그레이드와 **무관하게 선행하던 드리프트 2건**도 함께 드러났다:

- 산출물명 — 우리 문서 일부가 `audit.md` 를 쓰는데 실제 산출물명은 `GRAPH_REPORT.md` 다. 같은 문서 안에서 두 이름이 동시에 쓰이는 자기모순 상태였다.
- 배치 레이아웃 — 규약은 `docs/graph/<scope>/`, 실물은 flat. `graphify-lookup-advisor` 의 Read 타겟이 존재하지 않는 경로였다. → [ADR-0019](../adr/ADR-0019-graph-artifact-scope-directory-layout.md) 로 규약 쪽 확정.

따라서 작업 성격은 "업그레이드 대응" 이 아니라 **"거짓 안내 제거 + 규약-실물 정합"** 이다.

## 반영 항목 15건

### P0 — 거짓 안내 제거 (5건, "따라하면 실패" 성격)

| # | 변경 |
|---|---|
| P0-1 | **설치 절차를 `graphify install` 위임으로 전면 교체**. `SKILL.md` 한 파일만 수동 복사하면 코어의 조건부 포인터가 전부 끊기고, 추출 프롬프트 파일의 **경로가 시맨틱 캐시 키**라 캐시 귀속까지 깨진다(업그레이드 후에도 낡은 프롬프트 결과가 재생). 확인은 `ls ~/.claude/skills/graphify/SKILL.md .../references/`, 비어 있으면 재실행(자기복구) |
| P0-2 | **설치 방법 권장 순서 반전** — `uv tool install graphifyy` 1순위, `pip` 은 경고 동반 대안으로 강등(상류 README 가 Mac/Windows 에서 pip 회피를 권고한다). 스킬이 실행 시 작업 디렉토리에 기록된 인터프리터 경로로 Python 을 해석하므로 pip 환경과 어긋나면 import 자체가 실패한다 |
| P0-3 | **버전 확인 명령 교체** → `graphify --version`. 구 명령(`python3 -c "import graphify; print(graphify.__version__)"`)은 배포에 그 속성이 없어 실행 실패한다(실측). 출력 예시는 `<버전>` 플레이스홀더 |
| P0-4 | **§9 고급 옵션을 sidecar 라우팅 표로 교체** — `--update`/`--cluster-only` → `references/update.md`, `query`/`path`/`explain` → `references/query.md`, export 계열 → `references/exports.md`. 나머지는 `ls .../references/` 로 위임(목록 하드코딩 최소화). "CLI 실제 표면은 스킬 문서보다 넓다 → 전수는 `graphify --help`" 를 명시 |
| P0-5 | **`audit.md` → `GRAPH_REPORT.md` 전수 통일 — 10사이트 / 6파일.** 조사가 지목한 3사이트를 실측 전수로 확장했고, 이 확장이 base 번들 2파일(`search-tool-matrix.md`·`documentation-guidelines.md`)을 영향 범위로 끌어들여 **base 매니페스트 동기 bump 를 확정**시켰다 |

### P1 — 신 상호작용 방어 (5건)

| # | 변경 |
|---|---|
| P1-1 | **misplaced-output 확인을 `source_commit` 조건에서 분리**해 판정 종류와 무관하게 무조건 1회 실행. 직전 릴리스의 방어는 발동 전제가 "index.md 부재 또는 `source_commit: null`" 이라, index.md 가 정상인 레포(= 이 레포)에서는 잔존 `graphify-out/` 을 **영구히 못 봤다**. 두 peer(`graphify-lookup-advisor`·`graph-refresh-checker`)가 동일 필드명 `graphify_out_present` 를 근거에 기록한다(§11.1 대칭) |
| P1-2 | **질의 전 `graphify-out/` 잔존 정리 의무화**. 스킬은 호출 시점 cwd 에 `graphify-out/graph.json` 이 있으면 탐지·코퍼스 점검을 건너뛰고 그 파일로 즉답한다 — 정본이 `docs/graph/<scope>/` 인 상태에서는 **오류 메시지 없는 조용한 오답**이다. `rm -rf` 가 아니라 배치(park) 후 빈 디렉토리 `rmdir` |
| P1-3 | **배치 절차를 payload 통째 이동으로 재작성** — 개별 파일 열거 금지. 증분 갱신 상태(`manifest.json`·`cache/`·사이드카)가 같은 디렉토리에 있고 버전마다 새 사이드카가 추가되므로 열거 목록은 조용히 stale 되며, 특히 `manifest.json` 누락은 **증분 갱신을 매번 전량 재추출로 퇴화**시킨다. 날짜 백업 서브디렉토리는 park 하지 않고 버린다. 되돌리기(`--update` 전 역방향 이동) 절차 동반 |
| P1-4 | **`graphify-update-advisor` 의 배치(park)·메타 책임 명문화**. lookup 이 이 advisor 를 실행 주체로 지목하는데 정의에 그 책임이 없어 **peer 계약이 끊겨** 있었다. Bash 사용 범위도 (a) 폐기 scope 정리 (b) park 용 `mkdir`/`mv` (c) 빈 `graphify-out/` `rmdir` 로 한정 |
| P1-5 | **base 중립 정본 `search-tool-matrix.md` 의 `no-graph` 기준에 misplaced-output 분기 반영** — add-on 이 앞서가고 중립 정본이 뒤처진 드리프트 해소 |

### P2 — 신 신호 활용 / 정합 (5건)

| # | 변경 |
|---|---|
| P2-1 | **재생성 성공 판정 = 차단 신호 부재 ∧ 산출물 실재의 논리곱**. 빈 그래프·축소 거부 두 가드는 write 이전에 중단하므로 이것이 hard fail 이고(`hard_fail: none \| empty-graph \| shrink-rejected`), `GRAPH HEALTH WARNING` 배너는 **읽기 전용 진단이라 판정자가 아니다** → `quality_warnings` 로 분리 기록. 금기에 "경고를 실패로 격상 / 차단 신호를 경고로 격하" 2줄 추가 |
| P2-2 | **index.md 스키마에 `source_file_base` 추가** (템플릿 + 이 레포 실물, 동일 명칭). 노드의 `source_file` 이 스캔 루트 상대이므로 base 없이는 실제 파일 위치를 해석할 수 없다. ADR-0019 결정 2(slug)의 **필수 전제** |
| P2-3 | **`graph-refresh-checker` 의 보조 신호로 `manifest.json` 편입 — 단 필수 의존 금지.** 빌드 상태 파일은 gitignore 대상이라 클론 직후엔 없다 → "부재가 정상", 판정 로직은 이 파일에 의존하지 않는다, 관측하지 않은 필드로 분기하지 않는다 |
| P2-4 | **이 레포 `docs/graph/` 전량 재생성** (아래 §재생성 결과). 노드 ID 규칙 반전 + base 혼재 오염으로 증분 갱신이 불가능했다 |
| P2-5 | `docs/graph/.gitignore` 서술을 **이중 경로 명시**로 정정(스캐폴딩이 allowlist 로 생성 / 루트 `.gitignore` 에 직접 둔 프로젝트는 부재 — 둘 중 한 곳이면 충분) + `--no-viz` 문제표 행의 **증상 방향 반전 수정**(HTML 을 건너뛰는 옵션이므로 "`graph.json` 은 있고 `graph.html` 이 없음" 이 맞다) |

## 파생 변경 (D1~D7)

| # | 변경 |
|---|---|
| D1 | 루트 `.gitignore` += `docs/graph/*/` — scope 서브디렉토리 전체 무시(ADR-0019 귀결). 기존 flat 3줄은 잔존 산출물 오작동 방어로 유지, 주석 갱신 |
| D2 | add-on usage §3.2 에 scope slug 명명 규칙 1줄 + 예시 표 1행(`adapters-opencode` / `adapters/opencode`) |
| D3 | 템플릿 `graph/index.md` 에 동일 명명 규칙 + `### scope 항목 스키마` 절 신설 + Scopes 표 5열 → 6열 |
| D4 | 이 레포 `docs/graph/index.md` 산출물 링크를 `./adapters-opencode/…` 로 갱신 |
| D5 | `graphify-lookup-advisor` 에 Read 실패 시 `docs/graph/*/graph.json` Glob 방어 1줄 (index.md scope 명과 실제 디렉토리 어긋남 대비) |
| D6 | 루트 `.gitignore` += `.opencode/` — adapter installer 설치본 사본을 무시. **코퍼스 오염 차단이 목적이고 파일 이동은 하지 않았다**: 실측으로 그래프 코퍼스 53파일 중 37파일(70%)이 이 트리 하위의 우리 플러그인 번들 설치본 사본이었다. 부수 효과로 61MB untracked 트리가 `git status` 를 오염시키던 문제도 해소 |
| D7 | add-on usage **§3.3 "그래프 코퍼스에서 제외하기" 신설** — `.gitignore` 는 조상 디렉토리 체인까지 자동 존중되고, `.graphifyignore` 는 그 뒤에 병합돼 **더 제외만 가능**(재포함 불가)하다는 규칙 + 선택 기준 표. 원칙 1줄: "scope 는 무엇을 그래프화할지, ignore 규칙은 그 안에서 무엇을 뺄지를 정한다 — 코퍼스 오염은 scope 를 쪼개서 피하지 않는다" |

## 이 레포 `docs/graph/` 재생성 결과

`/graphify adapters/opencode` → `docs/graph/adapters-opencode/` 배치. scope 명 `adapters-opencode`, `source_file_base: adapters/opencode`.

| 항목 | 값 |
|---|---|
| 규모 | **133 nodes / 247 edges / 3 hyperedges / 10 communities** (구 162 nodes / 297 edges / 9 communities) |
| 코퍼스 | 16파일(code 14 + doc 2) — D6 적용 후. 적용 전 53파일 |
| 추출 신뢰도 | 94% EXTRACTED · 6% INFERRED(14엣지, 평균 confidence 0.84) · 1% AMBIGUOUS |
| 오염 해소 | `source_file` **단일 base**(구: scope-root 111 / repo-root 51 혼재) · `runInstall` **1노드**(구: `src_install_runinstall` + `install_runInstall` 2노드로 분열) |

**노드 감소는 정상이다** — 중복 노드 제거 + 설치본 사본 배제의 결과이므로 감소 폭에 하한을 두지 않았다. 오히려 구 값(162)에 근접하면 필터가 안 먹었다는 의심 신호로 읽는다.

**알려진 품질 경고**: graph health 진단이 dangling-endpoint 엣지 **29건**을 보고했다(raw 276 → valid 247). **읽기 전용 진단이며 빌드를 중단시키지 않는다** — 그래프는 사용 가능하되 일부 엣지의 한쪽 끝이 노드로 해소되지 않는다. edge collapse·self-loop·중복 엣지는 0건. P2-1 규약대로 성공/실패 판정에는 쓰지 않고 품질 항목으로만 기록한다.

파괴적 조작은 전부 `rm` 없이 scratchpad 백업 `mv` 로 수행했다(구 flat 산출물 3파일 + 이전 `graphify-out/` payload). 두 대상 모두 gitignore 대상이라 git 으로 복구할 수 없기 때문이다. 삭제성 조작은 빈 디렉토리 `rmdir` 1건뿐이다.

## 릴리스

| 대상 | 버전 | 근거 |
|---|---|---|
| add-on atp-graphify 매니페스트 2곳 | 2.2.0 → **2.3.0** | 설치 절차 전면 교체 · 에이전트 판정 게이팅 변경 · 반환 스키마 필드 3종 추가 = user-facing feat → minor |
| base atp 매니페스트 4곳 | 2.9.0 → **2.10.0** | 번들 3파일 변경 — 템플릿 스키마 필드 추가(소비자 대면 계약) · `search-tool-matrix` 판정 기준 변경 · `documentation-guidelines` 산출물명 정정. 오타 수정이 아니라 계약 추가이므로 patch 부족 |

**major 가 아닌 근거**: slug 규칙이 기존 문서 예시(`src`, `src-features`, `docs`, `full`)에서 항등 변환이므로 그 규약을 따른 소비자의 `docs/graph/src/` 는 그대로 유효하다(파괴 0 — ADR-0019 §영향). 루트 `.gitignore`·`docs/graph/index.md` 편집은 번들 밖이라 버전 영향 0.

## 소비자 영향

`/plugin update` 로 base 2.10.0 + add-on 2.3.0 수신 시:

- graphify 설치 안내가 `uv tool install graphifyy` → `graphify install` 로 바뀐다. **기존 안내대로 `SKILL.md` 만 수동 배치한 환경은 `graphify install` 1회 실행으로 복구**된다.
- `docs/graph/` 산출물 위치가 `docs/graph/<scope>/` 로 명문화된다. 단일 세그먼트 scope 를 쓰던 프로젝트는 변경 불필요.
- `docs/graph/index.md` scope 항목에 `source_file_base` 기록이 요구된다(신규 필드 — 미기록 시 노드 경로 단정 금지).
- 그래프 조회·staleness 판정이 `graphify-out/` 잔존을 무조건 확인하므로, 미배치 상태에서 "그래프 없음" 오판 대신 배치 권고가 나온다.

## 잔여 / 후속

- **index.md 스키마 이원화 미해소** — 템플릿(`kind: graphify-meta`, `name`/`target`)과 이 레포 실물(`kind: graph-index`, `path`)이 서로 다른 스키마다. 이번 변경은 `source_file_base` 만 양쪽 동일 명칭으로 추가했다.
- **`source_file_base` 소비자 서술 보강** — 이 필드를 쓰는 주체(update-advisor)와 해석 규칙(템플릿 산문)은 있으나, 정작 상대경로를 해석해야 할 `graphify-lookup-advisor` 정의의 base 해석 의무는 구현 취합 단계에서 보정으로 추가됐다. 후속 세션에서 실사용 경로를 1회 확인할 대상.
- add-on usage §4 절차 예시가 이 레포 고유 scope 를 쓰는지 vs 일반 예시(`src`)로 통일할지는 구현 취합에서 `src` 로 정리했으나, 같은 문서 내 예시 일관성은 재점검 여지가 있다.
