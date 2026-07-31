---
kind: graphify-meta
last_generated_at: null
source_commit: null
scopes: []
---

# Graph — graphify 산출물 메타

이 디렉토리는 `/graphify` 가 생성하는 지식 그래프 산출물의 **메타 정보만** 커밋한다. HTML/JSON/GRAPH_REPORT.md 본체는 `.gitignore` 대상이며 재생성 가능하다.

> 설치·적용 가이드는 `atp-graphify` add-on 번들의 `graphify-usage.md` 참조.

## 엔트리포인트 사용법

- 구조 탐색이 필요한 작업 전에 이 파일의 `last_generated_at` 과 `source_commit` 을 확인한다.
- 메인 브랜치 기준 마지막 소스 커밋보다 뒤쳐져 있다면 `graph-refresh-checker` 서브에이전트를 호출해 staleness 판정을 받는다.
- 판정 결과가 `partial-stale` / `fully-stale` 이면 메인 에이전트가 `/graphify` 를 호출해 재생성하고, 이 파일을 갱신한다.
- 더 이상 관련 없는 scope (제거된 모듈 등) 의 산출물은 재생성 전 **삭제** 한다.

## 산출물 레이아웃

```
docs/graph/
├── index.md               # 이 파일 — 메타, 커밋 대상
├── .gitignore             # 본체 무시 (allowlist — 커밋 대상)
└── <scope>/               # scope 별 산출물 디렉토리 (무시됨)
    ├── graph.html
    ├── graph.json
    ├── GRAPH_REPORT.md
    └── manifest.json, cache/, .graphify_* …   # 증분 갱신 상태 (배치 시 함께 이동)
```

scope 예시: `src`, `src-features`, `docs`, `full` 등. 한 번에 여러 scope 를 운용할 수 있다.

### scope 항목 스키마

```yaml
scopes:
  - name: src                  # 디렉토리명 = docs/graph/<name>/ — 파일시스템 안전(경로의 `/` 는 `-` 로 치환)
    target: src/**             # 그래프 대상 경로(사람이 읽는 설명)
    source_file_base: src      # graph.json 노드의 source_file 을 해석하는 기준 = /graphify 에 넘긴 경로
    generated_at: <iso>
    source_commit: <sha>
```

노드의 실제 파일 위치 = `<repo>/<source_file_base>/<source_file>` 이다. `source_file_base` 를 적지 않으면 상대경로를 해석할 수 없다. scope 대상 경로가 `adapters/opencode` 처럼 여러 세그먼트면 `name` 은 `adapters-opencode` 로 쓴다.

## Scopes

_현재 생성된 그래프 없음._

| scope | 마지막 생성 | 소스 커밋 | 대상 경로 | source_file_base | 요약 |
| --- | --- | --- | --- | --- | --- |

## 갱신 시 체크리스트

- [ ] frontmatter 의 `last_generated_at`, `source_commit`, `scopes` 갱신
- [ ] 아래 "Scopes" 표에 한 줄 추가/갱신
- [ ] scope 항목에 `source_file_base` 기록 (= `/graphify` 에 넘긴 경로)
- [ ] 폐기된 scope 가 있다면 해당 디렉토리 `rm -rf` + 표에서 제거
