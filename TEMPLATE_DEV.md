# TEMPLATE_DEV — 플러그인 리포지토리 기여자·메타 문서

> 이 파일은 **`agent-team-protocol` 플러그인 레포 자체의 개선 이력·백로그** 만 담는다. 플러그인 배포(`atp@agent-team-protocol`)를 통해 소비 프로젝트로 전달되지 않는다 (커밋 대상이나 배포 산출물 아님). 사용자 프로젝트에는 포함되지 않는다.

---

## 1. 이 파일의 목적

이 파일은 `sundaytoz/agent-team-protocol` 플러그인 **자체의** 품질 관리용 메타 문서다. 역할 분리:

| 파일 | 독자 | 성격 | 소비 프로젝트 전달 |
|---|---|---|---|
| `README.md` | 플러그인 사용자 | 설치·사용 가이드 | 아니오 |
| `CLAUDE.md` | 이 레포 기여자 | 레포 개발 가이드 (self-dogfooding) | 아니오 |
| `docs/` (번들 레퍼런스) | 에이전트 런타임 (Read) | 운영 규약·에이전트 정의 | 플러그인 캐시 번들 (읽기전용) |
| `templates/` | `/atp:init` 스킬 | 스캐폴딩 원본 | init 이 소비 프로젝트로 복사 |
| **`TEMPLATE_DEV.md`** | **플러그인 기여자** | **개선 백로그·이력** | **아니오** |

`docs/` 하위에 이 내용을 두면 번들 레퍼런스와 섞여 에이전트가 읽는 레퍼런스 목록에 잡음이 되므로 **루트 단일 파일** 로 유지한다.

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

평가 세션 산출물은 `.atp/work-session/20260506-170447/` 에 있으나(1차 마이그레이션으로 `.claude/` 에서 이관), 이 레포는 work-session 을 **opt-out(gitignore)** 하므로(public + 발화 인용 노출 회피 — ADR-0010) 공개 커밋엔 없다. 즉 **영구 링크 불가**. 따라서:

- **요지·결론**은 본 문서 §2 와 §3 에 **임베드**한다 (위 표 + 아래 백로그).
- **원문**은 세션을 보존한 로컬(이 레포의 gitignore 된 `.atp/work-session/`)에서 열람하거나, `/atp:task 템플릿 이식성 재평가` 로 재생성한다.
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
| **G-P0-3** | ~~`CLAUDE.md` 이식 체크리스트 + placeholder 표기법 통일~~ ✅ 완료(plugin-only 전환으로 해소 — CLAUDE.md 복사 폐기, /atp:init 이 안내 블록 멱등 생성, 세션 20260601-115424) | [propagated] | Axis 1 #2, Axis 1 #6, Axis 4 #2 | 없음 | ~~세션 3~~ |
| **G-P0-4** | SKILL §5 "advisor 전체 스킵 vs verification 의무" 문구 정정 | [propagated] | Axis 3 #2 | G-P0-2 이후 권장 | 세션 2 또는 4 |

### 3.4 P1 묶음

| ID | 제목 | 태그 | 연관 이슈 | 예상 세션 |
|---|---|---|---|---|
| **G-P1-A** | 에이전트 권한 규범적 금기 강화 (verification Read / migration Bash / graphify rm -rf) | [propagated] | Axis 2 #1, #4, #5 | 세션 4 |
| **G-P1-B** | ~~선택 파일 제거 절차를 FAQ → §5 "프로젝트 적응" 으로 승격~~ ✅ 완료(plugin-only 전환으로 해소, 세션 20260601-115424) | [propagated] | Axis 1 #4 | ~~세션 5~~ |
| **G-P1-C** | `verification-strategies.md` §5 / `search-tool-matrix.md` §5 placeholder 경고 박스 | [propagated] | Axis 1 #5, Axis 4 #3 | 세션 5 |
| **G-P1-D** | research-advisor ↔ parallel-explorer WebSearch 비대칭 해소 | [propagated] | Axis 2 #2 | 세션 4 |
| **G-P1-E** | documentation-advisor description — in-progress vs final 호출 시점 변별 | [propagated] | Axis 2 #3 | 세션 4 |
| **G-P1-F** | graphify-lookup-advisor heuristic 과 graph-refresh-checker 경계 문서화 | [propagated] | Axis 2 #6 | 세션 4 |
| **G-P1-G** | ~~`<template>` 치환 모호 + 런타임 디렉토리 혼입 경고 (README §4.1)~~ ✅ 완료(plugin-only 전환으로 해소, 세션 20260601-115424) | [self] | Axis 1 #3 | ~~세션 0~~ |
| **G-P1-H** | ~~FAQ §15 의 "graphify 미도입 시 에이전트 파일 제거" 를 §5.4 로 승격~~ ✅ 완료(plugin-only 전환으로 해소 — graphify 는 옵트인 add-on 으로 분리, 세션 20260601-115424) | [propagated] | Axis 1 #4 일부 | ~~세션 5~~ |
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

> 분류 기준: [plugins/atp/templates/document-category-classification.md](plugins/atp/templates/document-category-classification.md)

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

### G-P1-G: README §4.1 `<template>` 치환 모호 해소 + 복사 제외 확장

✅ 완료 (plugin-only 전환으로 해소, 세션 20260601-115424). cp-R 복사 개념 자체가 폐기됨 — README 는 플러그인 설치 흐름으로 전면 재작성되어 이 항목이 대상으로 삼았던 "복사 제외"·"`<template>` 치환" 개념이 모두 소멸했다.

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
| 2026-06-01 | 20260601-115424 | plugin-only 전환 (cp-R 폐기, 2-플러그인 atp+atp-graphify) | README/CLAUDE.md/TEMPLATE_DEV.md 재작성, G-P0-3·G-P1-B/G/H 완료 마킹 |
| 2026-06-09 | 20260609-125316 | 3-플랫폼 지원(Claude/Codex/Gemini): platform-adapters 3층, capability matrix, Tier A/A-flat/B, init 3-지침파일, AGENTS.md 교정, init `$task` upsert 버그 fix | 커밋 4e9d9ea·3472883. 후속 §7 등재 |
| 2026-06-09 | 20260609-125316 | F-3PLAT-3: single-read `.atp/work-session` 전환(본문 14건 치환) + 자기삭제 마이그레이션 블록(init 삽입·task §0.5 실행) + platform-adapters 권위 반전 | 커밋 3eb0bf2. 12/12 AC + 동적 스모크 PASS. ~~잔여: version bump(release)~~ → 20260616-104333 에서 2.1.0 release 로 해소 |
| 2026-06-09 | 20260609-125316 | F-3PLAT-1/2: 코어 protocol §2.8 capability tier 동기화(역할tier↔capability tier 직교) + §2.7 research-반전 plan게이트 트리거 | 커밋 5b5a909. 9/9 AC PASS. 3-1 release-ready |
| 2026-06-09 | 20260609-173743 | Codex 구조 정정(interim): `.agents/plugins/marketplace.json` 정본 커밋 + `plugins/atp` symlink(비정본 명시) + `.codex-plugin/plugin.json` skills 선언 + platform-adapters 호출문법 `@`-반전(정확토큰 TODO:실측 보존) + README/CLAUDE/AGENTS/file-map `.codex-plugin` 설명 정정 + init AGENTS 블록 `@` 교정 | F-3PLAT-5/6 후속 등재. 정본 subdir 재배치는 백로그 |
| 2026-06-10 | 20260610-173353 | 모델 정책 플랫폼 중립화: §5 tier(small/medium/large)+effort 직교 노브+cap 규칙(§5.6)+report 스키마 v2, platform-adapters §1.6 모델 tier 매핑 신설, 축1 Codex spawn verified-empirical 격상, spawn=invocation 기록 의무 명문화, SKILL/FAQ/README 동기화 | ADR-0008. a976e98 feedback inbox 는 원격 브랜치 삭제로 제거(내용은 본 세션이 정식 처리) |
| 2026-06-10 | 20260610-093314 | Codex 호출 토큰 정정: `/task`(런타임 self-report 오판) → **`$task`**(사용자 대화형 실측 + 공식 docs `$` skill 멘션 접두). 7파일 전수 정정 + init upsert 동적 스모크(3회 멱등, `$task` 보존) PASS | 교훈: 런타임 self-report 는 UI 토큰 근거 불가 — platform-adapters §1.1 마커 목록에 명문화 |
| 2026-06-10 | 20260610-093314 | Codex 대화형 전사 확보: `$atp:task` 명시 호출 인식 + SKILL 본문 로드 + 버전 정확 보고 → 호출 표기 `$atp:task` 로 최종 통일(단축형 `$task` 는 TODO 격하). README 지원 플랫폼 표 + Codex 테스트 완료 체크리스트 신설(내부 경로 sanitize) | F-3PLAT-6 추가 해소. 잔여: `$task` 단축형·E2E spawn |
| 2026-06-11 | 20260611-093639 | 번들 런타임 플랫폼 중립화: platform-adapters 를 "capability 자가판정" 문서로 재작성(3사 matrix·판정표·어댑터 제거), 실측 데이터는 ADR-0009 부록 A~F 동결 이관(마커 13/16/33/25/6 전수 보존), init render_block 토큰 주입형 단일 템플릿 전환, task/init 지침파일 3종 열거 중립화, 프로토콜 §1.6→§6 포인터 갱신 | ADR-0009 (ADR-0006 부분 supersede). 15/15 AC + init 동적 스모크 PASS. 사람용 문서 3사 병기는 유지 |
| 2026-06-16 | 20260616-094150 | work-session 추적 정책: **플러그인 기본=추적 + 레포별 opt-out**. init/task scaffolding 추적 기본(소비 레포 전파), 프로토콜 §7 추적정책+opt-out 명문, §4.7 AC 정식화 self-audit 게이트 신설. **이 소스 레포는 public + user_signals 발화인용 노출로 opt-out(gitignore 유지, 미추적)**. docs 동기화 | ADR-0010 (ADR-0006 L34 supersede). 1차안(소스도 추적)을 사용자 정정으로 split — PR #7 재작성/force-push |
| 2026-06-16 | 20260616-104333 | **release: 2.0.0 → 2.1.0** (minor). bb75f21 이후 머지된 feat 3건(work-session 추적·bundle-runtime 중립화·platform-neutral 모델 정책)이 manifest 버전 미bump 로 `/plugin update` 미도달이던 것 해소. manifest 6곳(marketplace claude/codex + atp·atp-graphify plugin.json claude/codex) + 현재버전 서술 문서(CLAUDE/AGENTS/file-map) 동기화. F-3PLAT-3 잔여 version bump 항목 클로즈 | breaking 0건 → minor. `.agents/plugins/marketplace.json` 은 version 필드 없어 제외. 역사 기록(ADR-0007 등) 보존 |
| 2026-06-17 | 20260617-165603 | **release: 2.1.0 → 2.2.0** (minor). research 단계 축-완결성 예방 **§4.8 신설**(완결성-예방 클러스터 §4.3/§4.6/§4.7 합류, 삼각 상호참조 §4.8↔§4.3↔§2.6) + research-advisor (A)축-완결성 자가검증5 (B)동명이인 disambiguation (C)JS-SPA→source_confidence 흡수, §2.6 (B)전수재검 위생규칙. base manifest 4개 bump. ADR-0011. 검증 10/10 PASS. origin/main 기반 release 브랜치(§0 stale 회피, PR#11) | 타 소비프로젝트 audit 구조적 protocol_feedback. add-on atp-graphify 미변경. 잔여: §8 G-RELCHK-1(이월) |
| 2026-06-18 | 20260618-103431 | **진입 강제로드 토큰 감축** (progressive disclosure) + **release: 2.2.0 → 2.2.1** (patch). protocol.md 선두에 코어 구획(52줄, C1~C7 + `atp:core:item` 앵커 7) + §헤더 기준 on-demand 라우팅 인덱스 삽입, SKILL §1 "전문 읽기"→"코어 Read + 라우팅 인덱스가 가리키는 §섹션만 grep 위치확정 후 on-demand". 본문 §1~§14 무수정(§N 불변, 물리분할 0). release-checklist §8 "끊긴 §N 인용 0" 점검 신설(Q4=A). base manifest 4 bump(marketplace claude/codex + atp plugin.json claude/codex; atp-graphify 2.1.0 무관) | ADR-0013. ~94% 감축(853줄→코어 52), 끊긴 §N 인용 0, 게이트 코어상주(R1 차단), SKILL §N 무단절. verification 6/6 PASS. 동일 PR 에 bump 포함 → 병합+`/plugin update` 시 신규 SKILL 동작 도달 |
| 2026-06-18 | 20260618-121634 | **회고 memory→docs-first 정책 전환** + **마이그레이션 무이관 시 조용히 스킵** + **잔존 식별자 예시 중립화** + **release: 2.2.1 → 2.2.2** (patch). (1) retrospective-advisor·SKILL §9·protocol §12/§2.3표/§8스키마: 교훈 기본 sink=docs(docs-first), memory 는 사용자 설정 존중 보조(강제 제거, `memory_optional` 필드 추가). (2) SKILL §0.5 점4 고지 조건부화 — 실제 이관 ≥1건일 때만 출력, 0건이면 무고지(이미 마이그레이션된 환경 매세션 노이즈 제거). (3) release-checklist §7 self-exclusion 예시를 중립 토큰(`examp[l]e_slug`)으로 교체 — 사람이 읽어도 소비 프로젝트 서비스명이 드러나지 않게(서비스명 리터럴은 PR #11 scrub 으로 이미 0). base manifest 4 bump | 사용자 patch 요청 3건. 소비 프로젝트 식별자 self-grep 0 재확인(ADR-0012 게이트). 스키마 키 `memory_candidates` 보존(리플 회피), `memory_optional` 가산. ADR 없음(정책 전환은 §12 본문+changelog 로 추적) |
| 2026-06-25 | 20260625-161950 | **release: 2.2.2 → 2.3.0** (minor). `cc1f3a3`(2.2.2) 이후 머지된 번들 feat 가 manifest 미bump 로 `/plugin update` 미도달이던 것 해소 — dispatch §2.9 fact-injection(`4992ea5`) + opencode 번들 통합분(verification-strategies +86·platform-adapters §8 포인터·protocol 일부) + 식별자 grep 규율(`6517028`) + design-advisor. **재발 방지(레포 docs-first 동선 강화)**: 루트 `CLAUDE.md` "릴리스 — 배포 완결 의무" 신규 섹션 + `docs/index`(한·영) 빠른진입 release 동선 + `docs/development/index` §0 트리거 성격 노출 + release-checklist §0↔CLAUDE cross-ref. base manifest 4 bump | opencode 어댑터 본체(`adapters/opencode`)는 npm 별도(범위 밖). atp-graphify 2.1.0 무관. 번들·프로토콜 §N **0 변경**(동선은 레포 docs 한정 — 소비 프로젝트 미전파). `2.1.0`·`2.2.0` 에 이은 동일 미bump 이월 패턴 3회째 → docs-first 동선으로 구조적 차단 |
| 2026-07-06 | 20260706-090617 | **release: 2.3.2 → 2.4.0** (minor). **feedback inbox 시스템 제거** — "feedback" 3갈래(① `protocol_feedback[]` 자기교정 ② inbox 카테고리 ③ memory `type:feedback`) 중 **②만 폐기**(채택 실적 0, 이름 3중 오버로딩 혼선). 카테고리 14→13. base+opencode 어댑터 미러 동시 편집(15 편집 + 템플릿 2 삭제 + manifest 참조 1줄). ①③·§4.3 과거사례(dated fact) 존치. base manifest 4 bump. ADR-0016 + changes 기록 | 경계보존 위해 orchestrator-direct(위임 시 존치 대상 오삭제 리스크). 어댑터 미러는 생성 산출물이나 사용자 지시로 동시 편집. §4.3 인용은 라이브 참조 아닌 회고 사실이라 유지 |
| 2026-07-07 | 20260707-095025 | **release: 2.4.0 → 2.5.0** (minor). Codex 전용 `codex-spark-routing.md` appendix 추가 — Spark 는 `host_scope: codex-only` 문서에서만 구체화하고 공통 §5 는 host appendix 링크+fallback 규칙만 보강. `task/SKILL.md` §6 에 host 전용 optional route Read 규칙 추가. base manifest 4 bump + changes 기록 | ADR-0008 tier/effort/cap/report v2 유지. 새 schema field 0, Spark 미지원·미확인·실패 시 기존 tier 매핑 fallback. atp-graphify 변경 없음 |
| 2026-08-13 | — | **release: 2.12.0 → 2.13.0** (minor). Lifecycle correctness와 wait/wakeup scheduling을 분리하고 timeout-free environment subscription만 formal 경로로 채택. 필수 capability gap은 unavailable 1회·automatic wait/list/recovery 0·authority/ownership 보존 뒤 blocked 또는 explicit event-only continuation으로 수렴. Deterministic scheduling fixture와 validator 추가 | ADR-0021. 독립 validator·report v2·정적 release gate PASS(L2 skipped: 외부 의존 없음). Current Codex formal adapter는 unsupported이며 runtime timed-wait probe와 longer/repeated timed wait fallback 없음 |

### G-DESIGN-INVARIANT-1 — fallback 제안 전 최상위 불변식 모순 gate (P1) `release-pending`

**문제**: 초기 wait/wakeup 설계가 current Codex 완화책으로 bounded timeout fallback을 제안했지만, 이는 사용자의 최상위 불변식 “관심 상태 변화가 없으면 root model 호출 0”과 정면 충돌했다. 사용자 교정 후 strict environment-subscription gate로 전수 재설계했다.
**제안**: `design-advisor` 계획 gate에 invariant×option 대조를 추가한다. fallback·degradation 후보 각각이 명시적 최상위 불변식을 위반하면 후보에서 제거하고, 호스트 gap으로 분리한다.
- 태그: [self] · P1 · 번들 · signal_source: negative · `structural_class: structural-latent`
- docs_sync_target: `plugins/atp/agents/design-advisor.md` + `agent-team-protocol.md` 계획 gate

### G-SOURCESPEC-GATE-1 — agent/skill 실행 계약은 documentation 전 source-spec dry-run (P1) `release-pending`

**문제**: agent/skill 정의를 수정한 뒤 project 종료 gate에서 source-spec dry-run을 처음 수행해 mode scalar, Write allowlist, scheduling return, orchestrator-preallocated report identity 결함 C1∼C4를 늦게 발견했다. 수정 후 implementation→documentation→verification을 재실행했다.
**제안**: agent/skill 실행 계약 변경 시 documentation 진입 전 source-spec dry-run을 필수화한다. 최소 검사 축은 requested/effective mode, tool/Write allowlist, 반환 schema, orchestrator-preallocated identity, closed vocabulary다.
- 태그: [self] · P1 · 번들 · `release-pending`
- docs_sync_target: `plugins/atp/skills/task/SKILL.md` project gate + `plugins/atp/agents/implementation-advisor.md`

### 향후 확장 규약

- 세션 수가 ≥10 누적되거나 본 문서 길이가 ≥600 라인을 넘으면 `.meta/` 디렉토리로 분할 이관 검토. 그 시점 전까지는 단일 파일 유지.
- 공식 평가 세션은 재생성 가능 (`/task 템플릿 이식성 재평가`) 하므로 `.claude/work-session/` 보존 불필요.
- 중요한 구조적 결정 (예: 스키마 v2 bump) 은 도입 후 `docs/adr/` 에 영구 기록.

---

## 7. 3-플랫폼 후속 백로그 (세션 20260609-125316 발생)

본 세션은 문서·tier 체계·init 규칙까지 완료. 아래는 scope 확장이라 이월된 후속.

### F-3PLAT-1 — Tier A-flat 를 코어 `agent-team-protocol.md` 에 동기화 (3-1a) ✅ 완료 (커밋 5b5a909)
> §2.8 신설(capability tier 요약+포인터, 역할tier↔capability tier 직교 박스) + platform-adapters cross-ref. SSoT 는 platform-adapters Layer 1 유지. 9/9 AC PASS.
- 현재 Tier A-flat 는 `docs/development/platform-adapters.md` Layer 1 에만 존재. 코어 프로토콜 §1~§2 는 spawn 가능 전제의 3-tier 위임만 기술.
- **이름 충돌 주의**: 코어의 "Tier-2/Tier-3 advisor"(역할 tier) vs 신규 "Tier A/B/A-flat"(플랫폼 capability tier) = 직교 두 축. 동기화 시 명시 구분 필수.
- 우선순위 P1. 영향: 코어 1문서 + agent-catalog 정합 점검. blast 작음.

### F-3PLAT-2 — plan 게이트 "research 반전" 트리거 명문화 (3-1b) ✅ 완료 (커밋 5b5a909)
> §2.7 항목5 + 자가점검 bullet + 배경, §1·SKILL §5.0 포인터. 9/9 AC PASS.
- §5.0 / §2.7 에 "research 가 세션 초반 가정과 상충하면 설계 진입 전 plan 게이트 질문 필수" 한 줄.
- 근거 memory: `research-seed-reversal-plan-gate-delegation`. 우선순위 P2.

### F-3PLAT-3 — `.claude/work-session` → `.atp/work-session` 경로 이전 전파 ✅ 완료 (커밋 3eb0bf2)
> **채택**: single-read + orchestrator 실행형 자기삭제 마이그레이션 블록(사용자 결정으로 dual-read 대신 single-read). 설계 `design-f3plat3.md`, 검증 12/12 AC + 로컬 동적 스모크 PASS. ~~**잔여**: 플러그인 version bump(소비 프로젝트 갱신 도달 조건) 는 release 작업에서.~~ → **해소**: 20260616-104333 세션에서 2.0.0 → 2.1.0 release bump.

<details><summary>원래 조사 결론(이력)</summary>
- 조사: `.claude/work-session/20260609-125316/research/plugin-update-propagation.md`.
- **결론**: 플러그인 업데이트는 plugin 내부 경로참조만 갱신, **소비 프로젝트의 `.gitignore`·기존 디렉토리는 불가침**(3사 공통). install/update lifecycle 훅 **3사 모두 부재**(cited). → 소비측 변경은 사용자 액션(init 재실행) 경유 불가피.
- **권장안(조사 우열)**: **(d) dual-read backward-compat + (b) init 재실행 보강** + (a) 플러그인 업데이트(내부 참조 갱신 필수 동반재).
  - (d): 플러그인이 신(`.atp`)·구(`.claude`) 경로 양쪽 읽기 → 하드 이동의 추적누락·leftover 리스크 제거.
  - (b): 남는 단 하나 소비측 surface 인 `.gitignore` 신라인 → init §3 에 신라인 grep-append 추가가 전제.
- blast radius: 경로 참조 13파일(base agent 7 + skill 2 + docs 4)·~20건. dual-read 채택 시 "신경로 쓰기 + 양쪽 읽기" 로 한 커밋 전수.
- 우선순위 P1. **design phase 필요**(dual-read 구현 형태·init §3 패치 형태).
</details>

### F-3PLAT-4 — Gemini 실제 배포 산출물 생성
- `gemini-extension.json` + `commands/*.toml`(또는 skills/) + 에이전트 미러 = **신규 파일, 순수 additive**. 기존 agents/skills 무수정.
- 선행: F-3PLAT-1(Tier A-flat 코어동기화)·F-3PLAT-3(경로) 정합 후 미러가 정합 소스 복제. 우선순위 P2.

### needs_user_verification (install 스모크 — 마커 승격 게이트)
- Codex per-plugin 업데이트 명령·auto-update·version 트리거 존재 여부.
- Codex/Gemini 훅의 소비 프로젝트 파일 수정 권한.
- ~~Codex 번들 skill namespace~~(해소: `$atp:task` — 2026-06-10), Gemini 배포형·`${workspacePath}` 본문 가용성.
- 3사 install→update 후 신버전 본문 경로참조 실제 전환 스모크.

### F-3PLAT-5 — Codex 정본 subdir 재배치 (interim symlink 해소) ✅ 해소 (2026-06-10, ADR-0007)
- 현 interim: `.agents/plugins/marketplace.json`(정본 위치) + `plugins/atp -> ..` 상향 symlink(base source, 비정본·root 우회). atp-graphify 는 `./plugins/atp-graphify` 실디렉토리 직접 source.
- **비정본 사유(cited)**: 공식 제약 "source.path 는 marketplace root 내부 유지". symlink 타깃이 repo root(marketplace root 밖) → 우회. install 스모크는 통과하나 정본 아님.
- **정본 목표**: base 자산(agents/·skills/·docs/·templates/·`.codex-plugin/plugin.json`)을 `plugins/atp/` **실디렉토리**로 격리, marketplace source.path 가 root 내부 실서브트리를 가리키게. symlink 제거.
- **블로커**: Claude 라이브 레이아웃(`.claude-plugin/`+root `agents/`/`skills/`)이 root 자산 의존 → 재배치 시 Claude 경로 동시 정합 필요(대규모). 라이브 세션 안전 게이트 필요.
- **Windows 게이트**: git symlink 는 `core.symlinks=false`(일부 Windows)에서 깨짐. Codex on Windows 지원 전 F-3PLAT-5 선행.
- 우선순위 P2(scope 큼). 선행: 라이브 플러그인 레이아웃 분리 전략 설계.
- **해소 (2026-06-10)**: base 자산을 `plugins/atp/`, add-on 을 `plugins/atp-graphify/` 실디렉토리로 격리 완료. symlink·`plugins/README.md` 제거, 전 marketplace source 가 root 내부 실서브트리 지목. 인간 전용 문서(README 류·.en.md·ADR·TEMPLATE_DEV 등)는 루트 잔류로 번들 제외(~51% 페이로드 축소). atp/atp-graphify 모두 2.0.0. 결정 기록: [docs/adr/ADR-0007-plugin-root-subdirectory.md](docs/adr/ADR-0007-plugin-root-subdirectory.md). 잔여: 3-플랫폼 install 스모크(사용자 실측 — AC-9~12).

### F-3PLAT-6 — `.codex-plugin/plugin.json` skills 선언 충분성 실측 ✅ 대부분 해소 (2026-06-10, codex exec 0.138.0)
- **해소**: `skills:"./skills/"` 선언 후 재설치(`codex plugin add`) → `codex exec -s read-only` 런타임 레지스트리에 `atp:task`/`atp:init` **노출 확인**(충분조건 충족). 번들 skill namespace = `plugin:skill` 콜론(`atp:task`). 호출 = **`$atp:task`** (사용자 대화형 전사 2026-06-10 — 명시 호출 인식·SKILL 본문/plugin.json Read·설치 버전 1.4.0 정확 보고. 공식 docs `$` skill 멘션 접두 cited). `codex plugin {add,list,remove,marketplace}` CLI 정본·cache 1.4.0·marketplace `.agents/plugins/` 도 확인.
- **정정 이력**: 호출 토큰을 codex exec 런타임 self-report 근거로 `/task` 단정했던 것은 오류 — self-report 는 컨텍스트 주입값(skill id)에만 유효, UI 입력 토큰 근거 불가. 사용자 대화형 전사로 `$atp:task` 확정 후 전 문서 정정.
- **추가 해소 (2026-06-10)**: 단축형 `$task` 도 동일 skill 로 해석 — 사용자 전사 확인. 호출 토큰 완전 확정 (`$atp:task` 전체형 + `$task` 단축형).
- **잔여(소)**: env var `PLUGIN_ROOT`/`CLAUDE_PLUGIN_ROOT` 의 skill·agent 본문(hook 외) 가용성. 3-tier 팀 모드 E2E(subagent spawn 실동작).
- 마커: platform-adapters 의 Codex 호출문법·namespace 셀 verified-empirical 유지(근거 교체: 런타임 self-report → 사용자 실측+cited).

---

## 8. 후속 백로그 (세션 20260617-165603 발생)

§4.8 축-완결성 세션에서 retrospective 가 표면화한 구조적 protocol_feedback. 사용자 결정(D-B)으로 본 세션 스코프(§4.8) 밖 이월. report(gitignored) rot 방지 위해 추적 가능 백로그로 등재.

### G-RELCHK-1 — release-checklist §0 "세션 진입 시 브랜치 사전 진단" 보강 (P1, 이월)

**문제 (구조적)**: 현 release-checklist §0 은 "릴리즈 직전" 트리거 + "bump 대상 브랜치 = 소비자 추적 ref(커밋 직전 진단)" 만 규정하고, bump 이 예상되는 작업의 **세션 진입 시 사전 브랜치-적합성 진단** 규약이 없다. 세션 20260617-165603 에서 작업 브랜치(`feat/community-health-files`)가 origin/main 대비 stale(behind 1·이미 PR#10 머지)이고 origin/main 에 미릴리즈 feat 가 누적된 상태가 §0 게이트(세션 후반)에서야 드러나, 브랜치 조정 제안이 늦어졌다(모든 변경 가역이라 손실 0, release 브랜치로 회수). 동일 staleness 진단 누락이 직전 세션(20260616-104333)에 이어 형태를 달리해 재발 → (b)+(c) 결합, 주(主)는 (c).

**제안**: `docs/development/release-checklist.md` §0 에 "0.x 세션 진입 시 사전 진단(bump 예상 작업 한정)" 절 추가 또는 §0 첫 불릿 보강 — 작업 *착수 전* `git fetch` 후 HEAD↔origin/main 토폴로지(ahead/behind/diverged) + origin/main 미릴리즈 feat 누적을 1회 진단. stale/누적이면 "현 브랜치는 bump 도달 경로 아님 — origin/main 기반 release 브랜치 권장" 을 착수 전 사용자에게 정보 제공(제약 무시 아님 → 재결정). 동시에 `agent-team-protocol.md` 세션 셋업 절에서 bump-likely 작업 진입 시 이 진단을 트리거하는 1줄 연결.

**근거 교훈(report memory_candidate body_draft)**: `branch-fitness-pre-diagnosis-at-session-entry-when-bump-likely` — 기존 `bump-target-branch-consumer-tracked-ref`(커밋 직전)·`feat-merge-triggers-version-bump-release`(트리거 조건)의 **시점 선행 보강**(비중복). 상세 본문은 세션 20260617-165603 report.md `retrospective.memory_candidates` 참조(gitignored 로컬).

- 태그: [propagated] · 우선순위 P1 · 예상: 독립 세션 1
- docs_sync_target: `docs/development/release-checklist.md` (+ 선택 `agent-team-protocol.md` 세션 진입 절)

### (메타·낮은 우선) 프로토콜-개선 세션 흐름 템플릿화

"소비 프로젝트 audit→확정 prompt(진단·A/B/C·제약·증거)→신규 규약 자기적용 검증→삼각 상호참조 정합" 흐름이 효과적이었으나 1~2회 관측. **3회 이상 같은 흐름 반복 시** 프로토콜-개선 세션 템플릿(또는 §9 사후승격 인접 문서) 명문화 검토. 지금 규약화는 과잉 — 조건부 후보로만 기록.

---

## 9. 후속 백로그 (세션 20260618-103431 발생 — ADR-0013 진입로드 감축)

코어 구획+on-demand 로딩 세션에서 retrospective 가 표면화한 protocol_feedback 2건. 사용자 확정 스코프(Q5=A, "로딩 전용·규약 내용 변경 금지") 밖이라 본 세션 미반영, report(gitignored) rot 방지 위해 등재. 두 교훈은 MEMORY 기록됨(`atp/verification-baseline-compare-keep-tree-consistent`, `atp/citation-anchor-public-api-loading-over-split`).

### G-ACTREE-1 — AC baseline 대조 시 git tree 일관성 1줄 명문화 (P1)

**문제**: orchestrator 가 검증 AC 에 "개선 전후 대조" 를 추가할 때 cross-tree 혼용(working-소스 ↔ `git show HEAD:`-헤더)이 거짓양성을 주입한다. ADR-0013 세션 AC-3 에서 발생(verification-advisor 가 same-tree 정규화로 자가교정, 의미기준 PASS). design 원본 AC 는 정상이었고 결함은 orchestrator 프롬프트 확장부 한정.
**제안**: `agent-team-protocol.md` 검증 규약(§4.6/§4.7 인접)에 "baseline 대조 AC 는 양변을 동일 tree(HEAD↔HEAD 또는 working↔working)에 두고, 각 tree 내부 불변식(끊긴 인용 0 등)이 전후 동일한지 비교" 1줄 추가.
- 태그: [self] · P1 · docs_sync_target: `agent-team-protocol.md` (§4.x 검증 규약)

### G-CITEAPI-1 — "인용 광범위 = 공개 API" 설계 휴리스틱 등재 (P2)

**문제/기회**: `§N`·앵커 인용이 코드베이스 전반에 산재하면 사실상 공개 API. 무게/구조 개선 시 물리 재배치 전에 인용망을 실측하고 로딩전략 변경(코어상주+on-demand)을 분할보다 우선해야 끊긴 인용·이력문서 사후수정을 0 으로 만든다. ADR-0013 에서 실증(Q2=B).
**제안**: `documentation-guidelines.md` 또는 design 휴리스틱 절에 1줄 등재.
- 태그: [self] · P2 · docs_sync_target: `documentation-guidelines.md`

---

## 10. 후속 백로그 (세션 20260729-172132 발생 — 상류 graphify 스킬 구조 재편 대응)

retrospective 가 승격 판정한 후보 8건 중 **번들(`plugins/`) 변경을 요구하는 6건**을 이월한다. 사용자 승인 스코프("graphify 반영 15건")를 넘는 별개 작업 단위이고, base manifest 4곳 동기 bump + `docs/changes` 1건이 같은 작업 단위로 따라오기 때문이다.

**`release-pending`** — 다음 세션 진입 시 우선 확인(루트 `CLAUDE.md` §릴리스 이월 규약 / `release-checklist.md` §0 "메모는 트리거가 아니다"). 세션 report 는 `.atp/work-session/` opt-out(ADR-0010)으로 미추적이라 이 등재가 유일한 생존 경로다.

같은 회고의 후보 2건은 **본 세션에서 반영 완료**(번들 밖이라 bump 불요): release-checklist §0 브랜치 케이스 분기 + bump 탐지 명령 결함 2건 수정(`894950e`), 루트 `CLAUDE.md` §self-dogfooding 에 "편집한 에이전트 실호출" 1줄.

### G-ACTYPE1-1 — AC self-audit 3번째 축: 판별력(Type I) (P1) `release-pending`

**문제**: 이 세션에서 AC 정식화 결함 3건이 나왔고 **전부 "불변식이 정상 상태를 위반으로 판정"**(Type I)이었다. 메커니즘은 서로 달랐다 — S4=판별 키 부족(파일별 `__dirname` 을 중복 노드로 오판) / S5=외부 도구 동작 전제 오류(상류가 의도한 캐시 위치를 미배치로 오판) / AC-S4=검사 pathspec 범위(자기 이력 문서가 개명 사실을 기술하는 것을 위반으로 오판). §4.7 의 2축은 메커니즘(시점 드리프트·리터럴 grep 의존)으로 정의돼 있어 **셋 다 통과한다**. design 이 2축을 실제로 수행하고 통과 판정한 것이 노력 문제가 아니라 축 부재라는 직접 증거다.
**제안**: `agent-team-protocol.md` §4.7 에 3번째 축 신설 — "**판별력**: 이 불변식이 *정상* 상태를 위반으로 판정할 경우가 있는가? 위반으로 잡힐 대상을 3개 열거해보고 그중 정상인 것이 있으면 판별 키를 좁힌다(예: label → (label, 정의파일)). 검사 범위가 산출물 표면을 넘어 이력·메타 문서까지 가는지도 확인한다." `design-advisor.md` 의 self-audit 절 제목도 (시점·표현·**판별력**) 3축으로 갱신.
- 태그: [self] · P1 · 번들 → base manifest 4곳 bump + changes 1건
- docs_sync_target: `plugins/atp/docs/development/agent-team-protocol.md` §4.7 + `plugins/atp/agents/design-advisor.md`
- 재현성 근거: 동일 세션 n=3, 메커니즘 상이, 축 직교성 논증 확보. **+2 (2026-09-08 세션 20260908-152238, n=5)**: AC7 — `git grep 'plugins/atp/hooks'` 가 "base 에 hooks 없음" 을 단언하는 테스트의 assertion 메시지(부정 단언의 자기언급)를 매치 / AC9 — `/Users/` 광역 패턴이 redaction placeholder `/Users/example` fixture 를 매치. 둘 다 orchestrator 가 design 스킵 후 직접 저술한 AC 이며 §4.7 게이트 실행 주체 공백이 함께 드러났다(같은 세션에 task SKILL §5.1 + §4.7 서두에 "저술 주체 무관 적용" 1줄씩 반영). 판별력 열거의 기본 false-positive 후보 2종 명시 권장: (a) 금지 대상을 이름으로 단언하는 테스트·이력 문서, (b) 의도적 placeholder/redaction fixture. 해소는 산출물 재문구보다 pathspec/패턴 협소화 우선.

### G-UNIVCLAIM-1 — 전칭 부정 주장의 확증 표면 병기 (P1) `release-pending`

**문제**: research 가 "**경로 규약은 불변 — 전부 `graphify-out/` = cwd 기준**" 이라고 `확인됨` 으로 단정했으나 캐시에 대해서는 거짓이었다(상류가 `cache_root` ≠ `root` 를 명시적으로 구분). design 이 이를 불변식 전제로 승격해 S5 AC 가 오작동했고, verification 실행에서야 드러났다. ADR-0018 반증 패스가 통과한 이유는 그 사실이 §3.2 load-bearing 목록에 **없었기 때문** — research 가 자기분류하지 않았는데 design 은 전제로 썼다. 추가 진단: `확인됨` 에는 hedge 가 없어 §2.6 불확실성 보존이 발동하지 않는다 → **범위 한정은 hedge 와 독립된 승계 대상**인데 규율이 hedge 에만 걸려 있다.
**같은 세션 A/B 대조가 처방을 지목**: 범위를 한정한 CLI 축 주장("문서 표면 기준으로만 닫혔다")은 개방성이 하류로 전달돼 `.graphifyignore` 발견으로 이어졌고, 한정하지 않은 경로 규약 주장은 AC 전제로 무조건 승격됐다.
**제안**: (a) 전칭/부정 주장("전부 X 다", "Y 는 없다", "규약은 불변이다")에는 **확증 표면을 병기**한다 — "무엇을 근거로 전수라 하는가"(문서 표면 / 실행 표면 / 소스 표면). (b) **경로·기준(base) 규약은 load-bearing 기본 편입** — 기본 반례로 "한 시스템에 base 가 복수 공존"을 반드시 시도한다.
- 태그: [self] · P1 · 번들
- docs_sync_target: `agent-team-protocol.md` §4.8(ADR-0018 확장 문단) + `plugins/atp/agents/research-advisor.md` 자가검증 + `design-advisor.md`(전제 승계)
- 재현성 근거: 동일 세션 A/B 대조

### G-DESTPREM-1 — 파괴적 조작 전제는 게이트 전 read-only 실측으로 닫는다 (P1) `release-pending`

**문제/기회**: design 이 DO-1(3,477파일 61MB 격리)을 `미확정:` 으로 정직하게 표시하고 "보수적으로" 요구했으나, orchestrator 의 read-only 실측(`detect()` 직접 호출, write 0)이 전제를 반증해 **ignore 1줄로 대체**했다. 파괴적 조작 5건 → 2건, 삭제 0건. §6 에 전제 폐쇄를 요구하는 조항이 0 이라 이번엔 orchestrator 재량으로 성립했다.
**제안**: §6 에 소절 1개 — 파괴적 조작을 설계에 넣을 때 **그 필요성의 전제를 신뢰도와 함께 표기**하고(design 측), 게이트 제시 **직전에 read-only 로 전제를 재확인**한다(orchestrator 측). 양면 계약으로 명문화. 기존 "게이트 2단계 분리"는 시간축 뒷단이라 상보.
- 태그: [self] · P1 · 번들 · n=1 이나 비용 비대칭 큼(불필요한 61MB·3,477파일 이동) + 조항 0 = structural-latent
- docs_sync_target: `agent-team-protocol.md` §6 + `plugins/atp/agents/design-advisor.md`

### G-VERIFINDEP-1 — verification 은 기록 감사가 아니라 독립 재실행 (P1) `release-pending`

**문제**: 이 세션에서 verification 이 orchestrator 판정표를 **감사하지 않고 독립 재실행**해 S5 를 반증했다(orchestrator 는 레포 루트만 관측했고 실제 빌드 cwd 를 놓쳤다). 결과: AC 재정식화 + 소비자 문안 3곳 정정 + misplaced-output 판정 키 정밀화. 반대로 기록만 감사하는 verification(rubber-stamp)은 **조용히 실패**하므로 사후 관측이 불가능하다 — 이 성질 때문에 규약화 가치가 있다.
**제안**: `verification-advisor.md` 입력·실행 절차 뒤에 소절 — "orchestrator 가 제공한 판정 기록은 **입력이지 근거가 아니다**. 판정 가능한 항목은 반드시 재실행하고, 기록과 어긋나면 기록이 아니라 실행 결과를 채택한다. 재실행 불가 항목(사용자 확인 이력 등)만 기록에 의존하고 그 사실을 명시한다."
- 태그: [self] · P1 · 번들
- docs_sync_target: `plugins/atp/agents/verification-advisor.md` + `agent-team-protocol.md` §4.7 인접 1줄

### G-CONSTRSURF-1 — 제약 집행 AC 의 검사 표면이 제약 문안보다 좁으면 안 된다 (P2) `release-pending`

**문제** (Type I 의 역방향 = Type II): design 이 R-1("상류 버전 번호 0건")을 부과하고 AC-22 로 집행했는데, 본문은 0 hit 통과인 반면 **산출 파일명** `2026-07-30-graphify-0.9x-adaptation.md` 가 정규식(`0\.(7|8|9)\.[0-9]+`)을 우회했다. 게다가 그 파일명은 dispatch·design §5 가 지정한 것 — **제약 작성 단계와 경로 지시 단계가 갈리면 제약이 경로 지시에 적용되지 않는다.** 본 세션은 리네임으로 해소(참조 4사이트 동반 수정).
**제안**: 제약(R-n)을 부과하는 design 은 그 제약의 **검사 표면을 열거**한다 — 본문 / 파일명·경로 / frontmatter / 커밋 메시지 / index 링크. 그리고 자기가 지정하는 산출 경로 자신을 그 표면에 넣어 1회 대조한다.
- 태그: [self] · P2 · 번들
- docs_sync_target: `plugins/atp/agents/design-advisor.md`(제약 작성 소절) + `agent-team-protocol.md` §2.6 불확실성 보존 1줄

### G-GATEAXIS-1 — plan-gate 축이 코드베이스 사실로 판정 가능한지 먼저 자문 (P3) `release-pending`

**문제**: §2.7 plan-gate 발동은 정당했으나(H5 반전 + 범위 확장), 얹은 2번째 축(배치 규약 flat vs `<scope>/`)이 **"판단 보류 — design 위임"** 으로 돌아왔고 design 이 코드베이스 사실("flat 은 scope ≥ 2 에서 파일명 충돌로 성립 불가")로 단독 결정했다. 물어볼 필요가 없던 축을 얹었을 가능성.
**제안**: `§4.4` 자가 점검에 1줄 — "이 축이 **코드베이스 사실로 판정 가능한가**? 가능하면 묻지 말고 그 사실을 근거로 결정하고 결과를 보고한다. 선호·우선순위·비용 감수 의사만 사용자 축이다."
**반영 전제 (필수 병기)**: 이 점검은 **위임 축소 방향으로 쓰면 안 된다.** 안 물어봐서 틀린 방향으로 구현하는 비용이, 물어봐서 위임받는 비용보다 훨씬 크다(비대칭). 애매하면 묻는다.
- 태그: [self] · P3 · 번들 · signal_source: negative(약한 신호 — 명시적 지적 아님)
- docs_sync_target: `agent-team-protocol.md` §4.4 자가 점검

### (조건부) 통합 검증 게이트가 이 레포에서 상시 N/A

`/atp:init` 미실행으로 `docs/development/verification-strategies.md` 가 없어 이번에도 통합 검증을 AC 직접 실행으로 대체했다(반복 관측). 템플릿 `verification-strategies.md` 에 **문서·매니페스트 전용 전략 블록**(JSON 유효성 / 매니페스트 버전 invariant / 상대 링크 유효성 / 카테고리 index 등록)이 있으면 코드 없는 레포에서도 게이트를 정식으로 켤 수 있다. `/atp:init` 실행 + 템플릿 보강을 함께 검토.
- 태그: [self] · P2 · 번들(템플릿) · docs_sync_target: `plugins/atp/templates/verification-strategies.md`

---

## 11. 후속 백로그 (세션 20260804-120432 발생 — 세션 병목 분석 보고서 검토 + 교정 조치 3건)

세션 성격: 외부 세션 병목 분석 보고서의 타당성 2층 검증(Phase 1) → 검토가 도출한 교정 조치 3건 번들 반영(Phase 2, PR #27 / 2.11.0). 아래는 그 PR 스코프 **밖**으로 남은 항목이다.

**`release-pending`** — 다음 세션 진입 시 우선 확인. 세션 report 는 `.atp/work-session/` opt-out(ADR-0010)으로 미추적이라 이 등재가 유일한 생존 경로다.

> **역할 분리 (이번 회고가 지목한 규율)**: `report.md` 의 `open_items` 는 **동일 로컬·동일 작업자의 다음 세션 재진입 인터페이스**로만 유효하다. gitignore 되므로 durable·cross-contributor 기록이 아니다. 검토/평가형 세션이 "후속 작업 단위 후보" 를 산출하면 종료 전 이 파일에 최소 스텁(ID·제목·태그·연관 sid)을 등재한다 — §2 "원본 자료 접근 전략"(2026-05-06)이 이미 선언한 선례의 집행 경로다. 이번 세션은 초기에 `open_items` 에만 남겨 이 선례를 어겼고, 본 §11 등재로 해소했다.

### G-ADVPARA-1 — orchestrator 상위 advisor 동시 호출 금지 완화 검토 (ADR급) `release-pending`

**문제/기회**: 검토 대상 보고서가 최우선 조치로 "독립 advisor 3종 동시 dispatch(-32min)" 를 제시했으나, 이는 코어 구획 **C2** 와 §2 L103 의 명시 금지("컨텍스트 오염 리스크로 기본 금지")와 정면 충돌한다. 보고서는 그 규약의 존재를 언급하지 않아 조치로선 부적격 판정.
**그러나 개정 논거는 실측으로 존재한다**: 같은 보고서의 §7.1(subagent 1.45M tok 중 메인 진입 1.2%)·§3.1(advisor 보고서는 최종 컨텍스트의 5.8%)이 곧 금지 사유("컨텍스트 오염")의 반증 데이터다. 즉 금지의 근거가 실측으로 약화된 상태다.
**정정된 기대효과**: 보고서의 -32min 은 직렬 합계를 회수량으로 오독한 산술 오류. 순수 산술 **-15.5min**, 단계 의존성(documentation ← fix, retrospective ← verification·documentation) 반영 시 **-9.7min**.
**제안**: 금지를 유지/완화 어느 쪽이든 **ADR 로 판정**한다. 완화 시 코어 C2 + §2 L103 동시 개정 + 동시 호출 상한·산출 격리 조건 명시가 따라온다.
- 태그: [self] · P2 · 번들 → 코어 구획 개정이므로 base manifest 4곳 bump + changes + ADR
- docs_sync_target: `agent-team-protocol.md` 코어 C2 + §2 + `docs/adr/`
- 재현성 근거: 실측 데이터 있음(n=1 세션). 단 금지 완화의 리스크(동시 알림 처리·중재 복잡도)는 미측정

### G-RETROSPLIT-1 — retrospective 별 세션 분리 (보류 판정, 재검토 조건 명시) `release-pending`

**문제**: 검토 대상 보고서가 "retro 를 세션 종료 후 별 세션으로 분리(-17min, -162k tok, 난이도 낮음)" 를 제시. 검증 결과 **보류** — 끊기는 사슬 3개: §2 단계표의 "세션 종료 직전" 위치 / SKILL §9 의 `user_signals` 선기록 의무 + `report.md` 충족 전제 / §12 의 `memory_candidates` → docs 같은 커밋 반영. 게다가 이 레포 `CLAUDE.md` 가 "이월 금지" 를 실증 2건과 함께 명문화하고 있어, 조치 자체가 이월 패턴이다. 난이도 "낮음" 은 오판.
**재검토 조건**: 이월 추적 장치(추적 가능 항목 격리 + `release-pending` 류 표식)가 retro 에도 적용되도록 설계되면 재평가 가능.
- 태그: [self] · P3 · 번들
- docs_sync_target: `agent-team-protocol.md` §12 + `plugins/atp/skills/task/SKILL.md` §9

### G-SKILLTRIM-1 — `atp:task` SKILL 본문 축약 `release-pending`

**문제**: 검토 대상 보고서가 "스킬 본문 21KB 인라인 → 세션당 -6k tok" 을 제시했고 근거로 "내용 대부분이 1회성 마이그레이션 절차" 를 들었다. **정량 반증**: `SKILL.md` 19,873 B 중 §0.5 마이그레이션 블록은 **2,185 B = 11.0%**(최대 섹션은 §5, 30.95%). 마커 정리 실효는 ≈600 tok 이고 "-6k tok" 은 본문 **전체 축약**을 전제해야 성립한다 — 보고서가 두 규모를 한 조치로 묶었다. 부수로 "6k × 60턴 = 360k tok 재청구" 도 `cache_read` 10% 요율을 무시한 10배 과장(비용 등가 ≈36k).
**제안**: 축약은 여전히 유효한 방향이나 **§0.5 정리와 본문 축약을 분리**해 다룬다. 본문 축약은 절차 전문 인라인 대신 `agent-team-protocol.md` 참조로 대체하는 형태이며, 코어 구획 로드 규약(§1 프로토콜 로드)과의 정합을 함께 봐야 한다.
- 태그: [self] · P2 · 번들
- docs_sync_target: `plugins/atp/skills/task/SKILL.md`

### G-TOOLGRANT-1 — 새 tool/권한 상향 전 대칭성 자가점검 (P1) `release-pending`

**문제/기회**: 이 세션에서 orchestrator 가 `parallel-explorer` 에 `Write` 를 부여하려던 원안을, 같은 세션에서 `retrospective-advisor` 에 `Write` 부여를 "가드레일 제거" 로 기각한 논리와 **동일 구조**임을 구현 착수 시점에 포착해 폐기하고 read-only 유지 대안으로 교체했다(§2.5 `late_completion` 격리가 read-only 에 의존).
**그러나 절차로 보장되지 않는다**: 포착이 가능했던 것은 (a) 기각 논리가 같은 세션 Decisions 로그에 텍스트로 남아 접근 가능했고 (b) read-only ↔ 격리 근거가 프로토콜 본문에 이미 명문화돼 있었기 때문이다. `design-advisor.md`/`implementation-advisor.md` 자가검증 목록을 대조했으나 이를 강제하는 항목은 **없다**. 세션이 분리됐다면 재현 근거가 약하다.
**제안**: 자가검증 항목 신설 — "agent 의 tools 에 새 권한(`Write`/`Bash`/`Agent` 등)을 추가하기 전, 같은 세션 Decisions 로그 또는 `agent-team-protocol.md` 의 명시 invariant(§2.5 `late_completion`, §12 "권고만" 등)에서 **동일 구조의 권한 상향을 이미 거부한 판단**이 있는지 대조한다."
- 태그: [self] · P1 · 번들 · `structural_class: structural-latent`(구조가 허용, n=1)
- docs_sync_target: `plugins/atp/agents/design-advisor.md` + `plugins/atp/agents/implementation-advisor.md`

### G-RECOPURPOSE-1 — `AskUserQuestion` Recommended 는 사용자 지시 목적을 축으로 (P1) `release-pending`

**문제**: 이 세션에서 orchestrator 가 "검토 소견 문서만(release 의무 없음)" 을 Recommended 로 제시했으나 사용자는 "교정 조치만"(실제 번들 수정)을 택했다. Recommended 근거가 **안전/저비용** 축이었고 "사용자가 방금 이 검토를 시킨 목적(결함을 찾으면 고친다)" 축이 아니었다.
**§4.4 원문 대조**: 자가점검 7항목 중 3번("Recommended 근거 명시")은 근거의 **명시성**만 요구하고 근거의 **소스**를 규정하지 않는다 — 정확히 이 공백에서 발생.
**재발 판정**: 동일 뿌리 패턴이 별도 세션 2건에 이미 기록돼 있어 **n=3** (`standing-goal-check-before-deferral` 2026-06-10 / `confirm-top-goal-before-branching-questions` 2026-06-01). 세 건 모두 "orchestrator 의 안전측 판단이 사용자의 실제 우선순위보다 기본값으로 앞선다" 는 같은 구조.
**제안**: §4.4 자가점검에 항목 추가 — "Recommended 근거가 '안전/저비용' 뿐인가, 아니면 '사용자가 이 작업을 지시한 목적' 과 먼저 정합하는가. 후자를 우선 축으로 삼고 안전측 대안은 trade-off 병기해 옵션으로만 제시한다." 기존 standing-goal 계열 항목과의 통합도 함께 검토.
- 태그: [self] · P1 · 번들 · `structural_class: structural-frequent`(n=3, 별도 세션)
- docs_sync_target: `agent-team-protocol.md` §4.4 자가 점검
- 주의: 위 `G-GATEAXIS-1` 의 "반영 전제"(위임 축소 방향으로 쓰지 말 것)와 같은 §4.4 를 건드린다 — 두 항목을 함께 반영해 상충 없는지 대조

### (참고) 검토 대상 보고서 조치 중 기각·이관 결론 — 백로그 대상 아님

- **조치 4 (graph-refresh-checker 를 research 와 동시 실행)**: 기각. §9 종료 게이트이므로 판정 대상이 *변경 후* 코드베이스 — research 시점 실행은 판정 자체가 무효. 추가로 보고서의 실행 위치 서술(06:34)이 실제(08:00:42)와 다른 사실 오류.
- **조치 5 (worker notification 전파 범위 제한)**: ATP 스코프 이탈. 프로토콜 전문에 `notification`/`enqueue` 레버 0건 — 하네스 동작이며 env 보고서 소관.
