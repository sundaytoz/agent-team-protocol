# TEMPLATE_DEV — 템플릿 리포지토리 기여자·메타 문서

> **복사 제외**. 이 파일은 **템플릿 리포지토리 자체의 개선 이력·백로그** 만 담는다. `cp -R <template>/...` 로 새 프로젝트에 이식할 때 **복사하지 않는다** (README §4.1 참조). 사용자 프로젝트에는 섞이면 안 된다.

---

## 1. 이 파일의 목적

이 파일은 `sundaytoz/agent-team-protocol` 템플릿 **자체의** 품질 관리용 메타 문서다. 역할 분리:

| 파일 | 독자 | 성격 | 복사 대상 |
|---|---|---|---|
| `README.md` | 템플릿 사용자 (이식자) | 설치·사용 가이드 | 아니오 (§4.1) |
| `CLAUDE.md` | 이식된 프로젝트의 Claude Code | 프로젝트 루트 진입점 | 예 (병합) |
| `docs/`, `.claude/` | 이식된 프로젝트의 Claude Code | 운영 규약·에이전트 정의 | 예 |
| **`TEMPLATE_DEV.md`** | **템플릿 기여자** | **개선 백로그·이력** | **아니오** |

`docs/` 하위에 이 내용을 두면 이식된 신규 프로젝트에 섞여 잡음이 되므로 **루트 단일 파일** 로 유지한다.

---

## 2. 평가 결과 스냅샷 (2026-05-06)

첫 번째 공식 평가 세션: `session 20260506-170447` (research-advisor 4축 + orchestrator 종합).

**종합 등급**: 중 (구조 완성도 높음, 이식 첫날 실행력 결함 3건).

| 축 | blocker | warn | nit |
|---|---|---|---|
| 1 — 이식성 | 2 | 4 | 3 |
| 2 — 에이전트 정의 | 0 | 7 | 3 |
| 3 — SKILL/프로토콜 | 2 | 6 | 2 |
| 4 — 문서·진입 동선 | 1 | 4 | 3 |
| **합계** | **3 (중복 1 제거 후 3)** | **21** | **11** |

Top 5 이슈 (혼합 심각도):

1. **[P0]** docs 카테고리 `index.md` 12개 부재 — docs-first 원칙 작동 불가 (Axis 1 & 4 중복).
2. **[P0]** 보고서 스키마 3-way drift — 프로토콜 §8 / SKILL §9 / README §9.1 필드 불일치 (Axis 3).
3. **[P0]** `CLAUDE.md` placeholder 이식 가이드 부재 — 첫날 필수 채움 목록 공백 (Axis 1 & 4).
4. **[P0]** "advisor 전체 스킵 vs verification 의무" 경계 모호 (Axis 3).
5. **[P1]** 에이전트 권한 격리가 규범적 금기에만 의존 — verification-advisor Read 전권, migration-writer Bash 전권, graphify-update-advisor `rm -rf` 게이트 미결합 (Axis 2 누적).

### 원본 자료 접근 전략

평가 세션 산출물은 `.claude/work-session/20260506-170447/` 에 있으나 이 디렉토리는 `.gitignore` 대상 (세션 임시 산출물 규약). 즉 **영구 링크 불가**. 따라서:

- **요지·결론**은 본 문서 §2 와 §3 에 **임베드**한다 (위 표 + 아래 백로그).
- **원문** 이 필요할 경우 세션을 보존한 기여자에게 요청하거나, 재조사 세션을 돌려 재생성한다. 재조사는 `/task 템플릿 이식성 재평가` 로 가능.
- 향후 공식 평가 세션 결과는 본 문서에 요약 임베드 + **ADR 수준의 중요 결정**은 `docs/adr/` (도입 후) 에 영구 보존.

---

## 3. 개선 백로그

### 3.1 우선순위 정의

- **P0 (blocker)**: 이식 첫날 실행 차단. 다음 마이너 릴리스 전 해결 의무.
- **P1 (warn)**: 운영 리스크. 누적 시 장기 품질 저하. 분기별 정리.
- **P2 (nit)**: 품질 다듬기. 관련 영역 수정 시 동시 처리.

### 3.2 분류 태그

- **[self]** 템플릿 자기 개선 (README·TEMPLATE_DEV·`.gitignore` 등 이식되지 않거나 이식 절차에 영향 주는 것).
- **[propagated]** 템플릿이 **전파**할 일반 개선 (`docs/`·`.claude/`·`CLAUDE.md` 등 복사 대상).

### 3.3 P0 묶음

| ID | 제목 | 태그 | 연관 이슈 | 의존 | 예상 세션 |
|---|---|---|---|---|---|
| **G-P0-1** | docs 카테고리 `index.md` 12개 스텁 포함 | [propagated] | Axis 1 #1, Axis 4 #1 | 없음 | 세션 1 |
| **G-P0-2** | 보고서 스키마 SSoT 통합 (프로토콜 §8 권위화) | [propagated] | Axis 3 #1 | 없음 (독립) | 세션 2 |
| **G-P0-3** | `CLAUDE.md` 이식 체크리스트 + placeholder 표기법 통일 | [propagated] | Axis 1 #2, Axis 1 #6, Axis 4 #2 | 없음 | 세션 3 |
| **G-P0-4** | SKILL §5 "advisor 전체 스킵 vs verification 의무" 문구 정정 | [propagated] | Axis 3 #2 | G-P0-2 이후 권장 | 세션 2 또는 4 |

### 3.4 P1 묶음

| ID | 제목 | 태그 | 연관 이슈 | 예상 세션 |
|---|---|---|---|---|
| **G-P1-A** | 에이전트 권한 규범적 금기 강화 (verification Read / migration Bash / graphify rm -rf) | [propagated] | Axis 2 #1, #4, #5 | 세션 4 |
| **G-P1-B** | 선택 파일 제거 절차를 FAQ → §5 "프로젝트 적응" 으로 승격 | [propagated] | Axis 1 #4 | 세션 5 |
| **G-P1-C** | `verification-strategies.md` §5 / `search-tool-matrix.md` §5 placeholder 경고 박스 | [propagated] | Axis 1 #5, Axis 4 #3 | 세션 5 |
| **G-P1-D** | research-advisor ↔ parallel-explorer WebSearch 비대칭 해소 | [propagated] | Axis 2 #2 | 세션 4 |
| **G-P1-E** | documentation-advisor description — in-progress vs final 호출 시점 변별 | [propagated] | Axis 2 #3 | 세션 4 |
| **G-P1-F** | graphify-lookup-advisor heuristic 과 graph-refresh-checker 경계 문서화 | [propagated] | Axis 2 #6 | 세션 4 |
| **G-P1-G** | `<template>` 치환 모호 + 런타임 디렉토리 혼입 경고 (README §4.1) | [self] | Axis 1 #3 | 세션 0 (이번) |
| **G-P1-H** | FAQ §15 의 "graphify 미도입 시 에이전트 파일 제거" 를 §5.4 로 승격 | [propagated] | Axis 1 #4 일부 | 세션 5 |
| **G-P1-I** | 프로토콜 §12 "추가/수정" vs `docs_sync_target` 자동 편집 범위 문서화 | [propagated] | Axis 3 #3 | 세션 5 |
| **G-P1-J** | "첫 호출 판단 기준" 명시 (요구 명확함 척도·메타 요청·feedback slug 판별) | [propagated] | Axis 3 #4 | 세션 5 |
| **G-P1-K** | §13 실행 가능 상태 체크를 SKILL §9 종료 조건에 반영 | [propagated] | Axis 3 #5 | 세션 2 |
| **G-P1-L** | AskUserQuestion 툴 권한이 orchestrator 에 있다는 전제를 SKILL 에 명시 | [propagated] | Axis 3 #6 | 세션 5 |
| **G-P1-M** | graphify 도입 여부 판별 규약 명문화 (`source_commit != null`) | [propagated] | Axis 3 #7, Axis 4 #4 | 세션 5 |
| **G-P1-N** | §3.1 graphify 최초 생성 유예 조건을 SKILL §9(4) 에 반영 | [propagated] | Axis 3 #8 | 세션 5 |
| **G-P1-O** | `docs/index.md` 빠른 참조에 graph-refresh-checker 선행 의무 명시 | [propagated] | Axis 4 #6 일부 → nit 승격 여부 재검토 | 세션 5 |

### 3.5 P2 묶음 (일괄 "Polish Pass")

| ID | 제목 | 연관 이슈 |
|---|---|---|
| **G-P2-POLISH** | 다음을 한 번에 처리: description 길이 정규화 / retrospective-advisor 초기 헤더 / parallel-explorer Bash 경고 / `.gitignore` 이미 포함 안내 / README 최소 읽기 경로 / SKILL 9단계 vs 프로토콜 §2 관점 통합 주석 / `protocol_feedback` retrospective 단계 언급 / documentation-guidelines graphify 선택 표기 / document-category-classification 예시 확대 / docs/index.md graph-refresh 선행 | Axis 2 #8-10, Axis 3 #9-10, Axis 1 #7-9, Axis 4 #6-8 |

### 3.6 의존 그래프 (요약)

```
G-P0-1 ─┐
G-P0-2 ─┼─ 독립 (병렬 가능)
G-P0-3 ─┘
             │
             └── G-P0-4 (권장: G-P0-2 후, 스키마 용어 확정된 상태에서)
                 │
                 └── P1 묶음 (스키마·명명 안정화 후)
                     │
                     └── G-P2-POLISH (최종 정리)
```

---

## 4. 백로그 항목 상세 (파일 영향 맵 + 변경 요지 + 검증)

### G-P0-1: docs 카테고리 `index.md` 12개 스텁

**파일 영향 맵**

| 변경 유형 | 경로 | 역할 |
|---|---|---|
| 신규 | `docs/adr/index.md` | ADR 카테고리 허브 |
| 신규 | `docs/analysis/index.md` | 분석 보고 허브 |
| 신규 | `docs/architecture/index.md` | 아키텍처 문서 허브 |
| 신규 | `docs/backlog/index.md` | 백로그 허브 |
| 신규 | `docs/changes/index.md` | 변경 기록 허브 |
| 신규 | `docs/contracts/index.md` | 계약/스키마 허브 |
| 신규 | `docs/domain/index.md` | 도메인 규칙 허브 |
| 신규 | `docs/issues/index.md` | 이슈 기록 허브 |
| 신규 | `docs/maintenance/index.md` | 유지보수 허브 |
| 신규 | `docs/security/index.md` | 보안 허브 |
| 신규 | `docs/work-log/index.md` | 작업 로그 허브 |
| 신규 | `docs/feedback/index.md` | 피드백 inbox 허브 (선택 의존) |
| 수정 | `docs/index.md` | 12개 링크가 실존 인식되도록 필요 시 각주 추가 |

**변경 요지**

각 `index.md` 는 3-5 라인 스텁:

```markdown
# <카테고리명> — <용도 한 줄>

> 분류 기준: [../development/document-category-classification.md](../development/document-category-classification.md)

## 문서 목록

_(아직 문서 없음)_
```

`feedback/index.md` 는 "feedback 스킬이 도입된 프로젝트에서만 사용" 경고를 추가. 카테고리가 프로젝트에 맞지 않으면 이식자가 디렉토리 전체를 삭제하도록 README §5.2 에 안내 (해당 항목은 §5.2 기존 규정으로 충분 — 별도 수정 불필요).

**검증**

- `ls docs/*/index.md | wc -l` = 14 (development + graph + 12 신규).
- `docs/index.md` 에서 링크 클릭 시 모두 존재 파일로 이동.
- documentation-advisor 가 "기존 index.md Edit" 규약을 최초 ADR 작성 시 실제로 실행 가능한지 드라이런.

### G-P0-2: 보고서 스키마 SSoT 통합

**파일 영향 맵**

| 변경 유형 | 경로 | 역할 |
|---|---|---|
| 수정 (확장) | `docs/development/agent-team-protocol.md` §8 | 스키마 v1 권위 YAML 에 누락 섹션 병합 |
| 수정 (축약) | `.claude/skills/task/SKILL.md` §9 | "프로토콜 §8 참조" 로 축약, 자체 섹션명 제거 |
| 수정 (축약) | `README.md` §9.1 | 동일하게 축약 + 프로토콜 링크 |

**변경 요지**

프로토콜 §8 YAML 에 다음을 **병합**하여 단일 권위 버전으로 승격:

- `verified_by_me` 섹션 (자동 검증 결과 집계)
- `needs_user_verification` 섹션 (수동 검증 필요)
- `graph_refresh` 섹션 (graph-refresh-checker 판정·후속)
- `user_signals.negative[*].structural: bool`
- `retrospective.memory_candidates[*].signal_source` / `docs_sync_target`
- `retrospective.protocol_feedback[]`

후방 호환 (v1 유지, schema bump 없음). SKILL.md / README 는 **필드 열거 대신 링크**.

**검증**

- 세 문서에서 섹션 이름을 `grep` 해 일치 확인.
- 실제 세션의 `report.md` 가 세 문서 중 어느 하나만 읽고도 완전한 스키마를 재현할 수 있는지 드라이런.

### G-P0-3: CLAUDE.md 이식 체크리스트 + placeholder 통일

**파일 영향 맵**

| 변경 유형 | 경로 | 역할 |
|---|---|---|
| 수정 (상단 주석 추가) | `CLAUDE.md` | 이식 체크리스트 (HTML 주석) |
| 수정 | `README.md` §4 또는 §5 | "이식 첫날 최소 채움 목록" 박스 |
| 수정 | `CLAUDE.md` + `docs/development/verification-strategies.md` + `docs/development/search-tool-matrix.md` | placeholder 표기법 `{...}` 통일 (기존 `<...>` 치환) |

**변경 요지**

CLAUDE.md 1행 위에:

```markdown
<!--
이식 체크리스트 (첫날 필수):
- [ ] {PROJECT_NAME}
- [ ] 기술 스택 표 런타임·언어·패키지 매니저·테스트
- [ ] 주요 명령어 {install} {dev} {build} {test} {typecheck}
  ↳ {install}/{test}/{typecheck} 는 docs/development/verification-strategies.md 의 L1 cmd 로 전파
선택 (추후):
- [ ] 코딩 규칙 열거
- [ ] 기술 스택 상세 주석
설치 완료 후 이 주석 블록은 삭제하세요.
-->
```

placeholder 표기는 **`{...}` 로 통일**. `verification-strategies.md` / `search-tool-matrix.md` 의 `<프로젝트 ...>` 를 `{project_...}` 로 치환. 사용자는 `grep -rn '{' CLAUDE.md docs/ | grep -v graph/` 로 채움 지점 일괄 확인.

**검증**

- `grep -rn '<[가-힣]' docs/ CLAUDE.md` 결과 0줄.
- `grep -rn '{[가-힣a-z_]*}' CLAUDE.md docs/development/` 가 체크리스트에 적힌 항목과 일치.

### G-P0-4: SKILL §5 advisor 스킵 규칙 정정

**파일 영향 맵**

| 변경 유형 | 경로 | 역할 |
|---|---|---|
| 수정 | `.claude/skills/task/SKILL.md` §5 | "전체" → "verification-advisor 와 통합 검증 제외 전체" |
| 수정 | `README.md` §6.3 (동일 문구) | 동기 유지 |
| 수정 (보강) | 동 위치 | "코드 변경" 정의 명시 |

**변경 요지**

```markdown
- 마이크로 편집(한 파일 몇 줄) 은 **verification-advisor 와 통합 검증을 제외한** advisor 전체 스킵 + orchestrator 직접 수행 허용.
- "코드 변경" 정의: 런타임에 평가되는 파일의 수정 (`.py`/`.ts`/`.rs`/`.go`/마이그레이션/schema DSL 등). 제외: `docs/**`, `*.md`, 주석 전용 변경.
- 설정 파일(`.env`, `.yaml`) 수정은 변경 성격에 따라 orchestrator 가 판단 — 실행 흐름에 영향 있으면 코드 변경 취급.
```

**검증**

- SKILL §5 와 README §6.3 이 축자 일치.
- 프로토콜 §13 실행 가능 상태 체크와 상호 참조 링크 추가.

### G-P1-G: README §4.1 `<template>` 치환 모호 해소 + 복사 제외 확장 (이번 세션에 포함)

§5 (README §4.1 diff) 참조.

---

## 5. 실행 순서 로드맵

| 세션 | 범위 | 사전 조건 | 예상 변경 파일 수 | 리스크 |
|---|---|---|---|---|
| **세션 0 (이번)** | TEMPLATE_DEV.md 신규 + README §4.1 업데이트 + `.gitignore` 확인 | 없음 | 2 (TEMPLATE_DEV 신규, README 수정) | 낮음 — 복사 제외 규약 실수만 주의 |
| **세션 1** | G-P0-1 (카테고리 index 12개 스텁) | 없음 | 12 신규 + 1 수정 (`docs/index.md`) | 낮음. 스텁 파일만 추가 |
| **세션 2** | G-P0-2 (스키마 SSoT) + G-P1-K (§13 체크) | 없음 (독립) | 3 수정 (프로토콜/SKILL/README) | 중 — 기존 세션 report.md 호환성 확인 필요 |
| **세션 3** | G-P0-3 (CLAUDE.md 체크리스트 + placeholder 통일) | 없음 | CLAUDE.md + 2-3 docs | 중 — placeholder 치환 실수 주의 (grep 사전 검증) |
| **세션 4** | G-P0-4 + G-P1-A/D/E/F (advisor 권한 강화 + 스킵 규칙) | G-P0-2 완료 (용어 안정) | SKILL + README + 5-7 agents | 중 — advisor 프롬프트 변경은 즉시 행동 변화 |
| **세션 5** | G-P1-B/C/H/I/J/L/M/N/O (운영 규약 잔여) | G-P0 전체 완료 | 5-8 docs | 낮음 |
| **세션 6** | G-P2-POLISH (nit 일괄) | P0·P1 안정화 | 10-13 파일 소폭 | 낮음 |

각 세션은 독립 브랜치에서 PR 로 병합. 세션 종료마다 `TEMPLATE_DEV.md` §6 Changelog 한 줄 추가.

### 이번 세션(세션 0) 에서 배포(커밋)하는 것

1. 루트에 `TEMPLATE_DEV.md` 생성 (본 파일).
2. `README.md` §4.1 에 복사 제외 목록 확장 + `<template>` 치환 안내 보강.
3. `.gitignore` 확인 — 이미 `.claude/work-session/` 포함. `TEMPLATE_DEV.md` 는 커밋 대상이므로 ignore 불필요.

**이번 세션에서는 P0-1~P0-4 의 실제 해결은 하지 않는다.** 백로그 등재만.

---

## 6. Changelog (이력 누적)

세션 단위로 본 문서를 갱신하고 한 줄씩 추가.

| 날짜 | 세션 ID | 변경 | 비고 |
|---|---|---|---|
| 2026-05-06 | 20260506-170447 | 첫 공식 평가 (4축, blocker 3 / warn 21 / nit 11) | summary.md 원본은 gitignore 세션에 보존 |
| 2026-05-06 | 20260506-172731 | TEMPLATE_DEV.md 신규, README §4.1 복사 제외 확장 | 세션 0 — 백로그 체계화 |

### 향후 확장 규약

- 세션 수가 ≥10 누적되거나 본 문서 길이가 ≥600 라인을 넘으면 `.meta/` 디렉토리로 분할 이관 검토. 그 시점 전까지는 단일 파일 유지.
- 공식 평가 세션은 재생성 가능 (`/task 템플릿 이식성 재평가`) 하므로 `.claude/work-session/` 보존 불필요.
- 중요한 구조적 결정 (예: 스키마 v2 bump) 은 도입 후 `docs/adr/` 에 영구 기록.
