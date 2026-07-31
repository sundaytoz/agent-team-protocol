---
kind: adr
adr_number: "0019"
title: docs/graph 산출물 scope 서브디렉토리 레이아웃 확정 — 규약-실물 드리프트 정정 + scope slug 명명 규칙
status: accepted
date: 2026-07-30
deciders:
  - template-maintainer
  - stzjungsoo
supersedes: []
related_commits:
  - (세션 20260729-172132 구현 — PR→main 머지 시 SHA 확정)
---

# ADR-0019: `docs/graph/<scope>/` 산출물 레이아웃 확정 + scope slug 명명 규칙

## 상태

**Accepted** — 2026-07-30. 세션 20260729-172132(상류 graphify 스킬 구조 재편 대응: 조사 → 설계 → 구현)의 위임 결정 D-A·D-A' 를 정본화한다. supersede 아님 — 기존 ADR 은 이 레이아웃을 결정한 적이 없다. 규약은 add-on 문서·에이전트 정의·번들 정본·템플릿에 **산재**했을 뿐 결정 레코드가 없었고, 그래서 실물이 규약을 따르지 않아도 되돌릴 근거가 없었다.

동반 릴리스: base atp 매니페스트 4곳 `2.9.0` → `2.10.0`, add-on atp-graphify 2곳 `2.2.0` → `2.3.0`. 변경 이력은 [changes/2026-07-30-graphify-skill-restructure-adaptation.md](../changes/2026-07-30-graphify-skill-restructure-adaptation.md).

---

## 맥락

### 규약과 실물이 어긋나 있었다

graphify 산출물의 정본 위치를 **6개 산출물이 `docs/graph/<scope>/` 로 서술**하는데, 이 레포 디스크 실물은 **flat**(`docs/graph/{graph.json, graph.html, GRAPH_REPORT.md, index.md}`, scope 디렉토리 0개)이었다.

| 축 | 상태 (세션 실측) |
|---|---|
| `<scope>/` 를 주장하는 산출물 | `graphify-lookup-advisor.md`(Read 타겟) · `graphify-usage.md` 3곳 · `graph-refresh-checker.md` · `graphify-update-advisor.md` · `plugins/atp/templates/graph/index.md` · **`plugins/atp/docs/development/documentation-guidelines.md`(base 번들 정본)** |
| flat 을 주장하는 것 | 루트 `.gitignore` 의 flat 전용 3줄(`docs/graph/*.html`·`docs/graph/*.json`·`docs/graph/GRAPH_REPORT.md` — 어느 것도 `docs/graph/<scope>/graph.json` 을 매치하지 않는다) + 디스크 3파일 |

가장 무거운 귀결: **`graphify-lookup-advisor` 의 Read 타겟이 존재하지 않는 경로였다.** 그래프 조회 에이전트가 `docs/graph/<scope>/graph.json` 을 읽도록 정의돼 있는데 그 경로에 파일이 없다 — 즉 정본 조회 경로가 규약상 상시 miss 였다.

**이 드리프트는 graphify 업그레이드와 무관하게 선행했다.** 상류 스킬 구조 재편 대응을 조사하는 과정에서 발견된 것이지 그 재편이 만든 것이 아니다. 같은 성격의 선행 드리프트가 하나 더 있었다(산출물명 `audit.md` vs `GRAPH_REPORT.md` — changes 문서 참조).

### 규약-실물 불일치가 실제 데이터 오염으로 나타났다 (실증)

구 그래프(재생성 전, scratchpad 백업 대조)에서 다음이 관측됐다. 전부 이 레포 자신의 `docs/graph/graph.json` 실측이다.

| 증상 | 관측값 |
|---|---|
| 동일 함수가 2노드로 분열 | `runInstall` 이 `src_install_runinstall`(전체 경로 세그먼트 조인 = 신 ID 규칙) + `install_runInstall`(직상위 디렉토리 = 구 ID 규칙) **2노드**로 존재. `GRAPH_REPORT.md` god node 표에 중복 계상 |
| `source_file` 해석 기준(base) 2종 혼재 | scope-root 기준 **111노드**(`src/install.js`) / repo-root 기준 **51노드**(`adapters/opencode/src/install.js`). 전자 13종은 repo root 에서 실재하지 않는 경로 |
| 총 노드 | 162 |

두 ID 규칙과 두 base 가 한 파일에 섞여 있다는 것은, 서로 다른 규약으로 만든 산출물이 같은 위치에서 병합됐다는 뜻이다. 배치 위치가 규약과 어긋난 채로 운영되면 "어느 base 로 상대화된 산출물인지" 를 구분할 구조적 수단이 없다.

정정 후 전량 재생성 결과: **단일 base 133노드 / `runInstall` 1노드**. 규약 정합화가 데이터 정합성으로 직결됨을 같은 레포에서 확인했다.

---

## 결정

### 결정 1 — `docs/graph/<scope>/` 를 정본 레이아웃으로 확정한다

flat 실물을 규약 쪽으로 정정한다(반대 방향이 아니다). scope 별 산출물은 `docs/graph/<scope>/` 하위에 두고, `docs/graph/index.md`(메타)만 커밋 대상으로 남긴다.

### 결정 2 (D-A') — scope 명은 대상 경로의 파일시스템 안전 slug, 디렉토리 깊이 1 고정

scope 대상 경로에 `/` 가 있으면 **`-` 로 치환**한 이름을 scope 명(= 디렉토리명)으로 쓴다. 디렉토리 깊이는 항상 1이다.

- `adapters/opencode` → scope 명 `adapters-opencode` → `docs/graph/adapters-opencode/`
- 기존 문서의 `<scope>` 플레이스홀더 표기는 그대로 유효하다 — scope 는 *이름*, 대상 경로는 index.md 의 `target`/`path` 와 `source_file_base` 가 갖는다. `<scope>` → `<slug>` 류 일괄 치환은 하지 않는다.

---

## 근거

### 결정적 근거 2개

1. **flat 은 scope 가 2개 이상이면 성립 자체가 불가능하다.** `graph.json`·`graph.html`·`GRAPH_REPORT.md` 파일명이 scope 간에 충돌한다. 그런데 다중 scope 는 이미 여러 산출물에 걸친 **기존 설계 자산**이다 — add-on usage 의 scope 분할 표, `docs/graph/index.md` 의 `scopes` 배열, `graph-refresh-checker` 의 scope 별 staleness 판정, 프로토콜의 `graph scope ≥ 5` → lookup 병렬 worker 승격 규칙. flat 을 정본으로 택하면 이 자산을 전부 폐기해야 한다(비가역적 기능 축소).
2. **"디렉토리 1개 = 상대화 base 1개" 가 새 규약과 의미적으로 정합하다.** 상류 스킬이 노드의 `source_file` 을 **스캔 루트 기준으로 일관 상대화**하도록 바뀌었다. 즉 `/graphify <경로>` 산출물의 `source_file` 은 그 `<경로>` 에 상대적이다. scope 디렉토리가 곧 그 상대화 단위가 되므로 산출물 하나가 base 하나에 1:1 로 대응한다. flat 에서는 여러 base 산출물이 같은 위치를 공유하게 되고, 그것이 위 §맥락의 base 2종 혼재가 발생할 수 있는 구조다.

### slug(결정 2)를 택한 이유와 그 대가

깊이 1 slug 를 쓰면 세 가지 운영 연산이 **전부 1줄로 성립**한다:

| 연산 | slug (`docs/graph/adapters-opencode/`) | 경로 중첩 (`docs/graph/adapters/opencode/`) |
|---|---|---|
| 실재 scope 열거 | `docs/graph/*/graph.json` Glob 1회 | 깨짐 (깊이 가변) |
| gitignore | `docs/graph/*/` 1줄 | 깨짐 (깊이별 패턴 필요) |
| 폐기 scope 정리 | `rm -rf docs/graph/<scope>` | 깨짐 (빈 중간 디렉토리 잔존) |

**대가**: 디렉토리명이 base 경로와 문자열 동일하지 않다. 따라서 **`source_file_base` 명시 기록이 선택이 아니라 필수 전제가 된다** — 이 필드 없이는 `source_file` 상대경로를 실제 파일로 해석할 수 없다. 같은 세션에서 index.md 스키마에 이 필드를 추가해 대가를 지불했다(추가 비용 0 — 같은 편집 단위).

---

## 영향

| 영향 | 내용 |
|---|---|
| 루트 `.gitignore` | `docs/graph/*/` 1줄 추가. 기존 flat 3줄은 잔존 산출물 오작동 방어로 유지 |
| index.md 스키마 | `source_file_base` 필드 추가 — 템플릿(`plugins/atp/templates/graph/index.md`)과 이 레포 실물(`docs/graph/index.md`) 양쪽에 **동일 명칭**. 노드의 실제 위치 = `<repo>/<source_file_base>/<source_file>` |
| **소비자 파괴 0** | 기존 문서·템플릿의 scope 예시(`src`, `src-features`, `docs`, `full`)는 모두 단일 세그먼트라 slug 규칙이 **항등 변환**이다. 이미 `docs/graph/src/` 를 만든 소비자는 그대로 유효 → 릴리스는 major 가 아니라 minor |
| 이 레포 실물 | 전량 재생성으로 규약에 맞췄다 — 구 flat 162노드(오염) → `docs/graph/adapters-opencode/` 133노드(단일 base). 구 산출물은 삭제하지 않고 scratchpad 백업으로 격리(gitignore 대상 = git 복구 불가) |
| 조회 경로 | `graphify-lookup-advisor` 의 Read 타겟이 처음으로 실재하게 됐다. 추가로 index.md 의 scope 명과 실제 디렉토리가 어긋날 경우를 대비해 `docs/graph/*/graph.json` Glob 방어 1줄을 같은 세션에 넣었다 |
| 잔여 부채 | `index.md` 스키마 이원화(템플릿 `kind: graphify-meta`/`name`·`target` vs 이 레포 실물 `kind: graph-index`/`path`)는 **미해소**다. 이번 결정은 `source_file_base` 만 양쪽 동일 명칭으로 추가하고 이원화 자체는 건드리지 않았다 — 별도 작업 필요 |

---

## 검토한 대안

### (A) flat 으로 통일 — 기각

`<scope>` 개념을 위 §맥락 표의 **6파일 전역**(base 번들 정본 `documentation-guidelines.md` 포함)에서 제거하고 다중 scope 기능을 폐기하는 안. 기각 근거:

- 다중 scope 설계 자산 폐기가 **비가역적 기능 축소**다(근거 1).
- 템플릿·문서가 약속한 레이아웃을 철회하는 것이므로 **이미 `docs/graph/src/` 를 만든 소비자가 깨진다**. 채택안은 반대로 파괴 0이다.
- flat 을 지지하는 근거는 "현재 디스크가 그렇다" 뿐이고, 그 현재 상태 자체가 오염의 온상이었다(§맥락 실증).

### (B) scope 대상 경로를 그대로 중첩 — 기각

`docs/graph/adapters/opencode/`. Glob 열거·gitignore 1줄·scope 삭제가 **셋 다 깨진다**(위 표). 삭제 후 빈 중간 디렉토리도 남는다.

### (C) 재생성을 포기하고 규약만 문서로 정리 — 기각

규약-실물 불일치를 그대로 두면 다음 기여자가 flat 실물을 보고 규약을 되돌린다. 실제로 이 드리프트가 그렇게 발생했다. 결정을 ADR 로 올리는 이유도 같다 — 결정 기록이 세션 산출물 안에만 있으면(이 레포는 `.atp/work-session/` git opt-out — ADR-0010) 근거가 소실된다.

### flat 으로 되돌리는 마이그레이션 경로 (1줄)

`mv docs/graph/<scope>/* docs/graph/ && rmdir docs/graph/<scope>` → 루트 `.gitignore` 의 `docs/graph/*/` 삭제 → 위 (A) 의 6파일에서 `<scope>` 개념 제거(다중 scope 기능 폐기 동반).

---

## 관련 문서

- [changes/2026-07-30-graphify-skill-restructure-adaptation.md](../changes/2026-07-30-graphify-skill-restructure-adaptation.md) — 본 결정을 포함한 세션 변경 전량(반영 15건 + 파생 7건 + 재생성 결과)
- [ADR-0018](./ADR-0018-research-falsification-corroboration-harvest.md) — 직전 add-on 릴리스. `graphify-out/` 미배치 방어(misplaced-output)를 도입했고, 본 세션이 그 게이팅 구멍을 폐쇄했다
- [ADR-0010](./ADR-0010-work-session-git-tracking.md) — 이 레포의 work-session git opt-out (결정 근거를 ADR 로 올려야 하는 이유)
- `plugins/atp/docs/development/documentation-guidelines.md` §graphify 산출물 관리 규칙 — 번들 정본 (이 결정과 정합)
- `docs/graph/index.md` — 이 레포의 scope 메타 실물
