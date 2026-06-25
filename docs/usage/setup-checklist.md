---
kind: usage
title: plugin 설치 후 설정 체크리스트
description: /plugin install 후 /atp:init 실행 → placeholder 채우기 → /atp:task 스모크까지 3단계 체크리스트.
owner: template-maintainer
stability: living
last_reviewed: 2026-06-01
---

# plugin 설치 후 설정 체크리스트

`/plugin install atp@agent-team-protocol` 완료 후 **`/atp:task` 가 정상 동작하는 상태** 로 만드는 3단계 체크리스트. 문제가 생기면 [faq.md](./faq.md) 를 참고한다.

---

## 0. 전제: plugin install 완료 확인

- [ ] `/plugin marketplace add sundaytoz/agent-team-protocol` 성공했는가?
- [ ] `/plugin install atp@agent-team-protocol` 성공했는가?
- [ ] (옵트인) graphify 기능이 필요하면 `/plugin install atp-graphify@agent-team-protocol` 도 완료했는가?
- [ ] `/plugin list` 에서 `atp` 상태가 enabled 인가?

---

## 1단계. `/atp:init` 실행

새 Claude Code 세션에서:

```
/atp:init
```

init 이 프로젝트에 아래 항목을 생성한다.

- `docs/index.md` — docs-first 허브
- `docs/<카테고리>/index.md` × 14 — 카테고리 인덱스
- `docs/development/verification-strategies.md` — L1/L2/L3 검증 전략 레지스트리 (placeholder 포함)
- `docs/development/document-category-classification.md` — 카테고리 분류 기준
- `docs/graph/` 골격 (`index.md` + `.gitignore`)
- `CLAUDE.md` 에 `<!-- atp:begin --> ... <!-- atp:end -->` docs-first + `/atp:task` 안내 블록 멱등 append
- `.gitignore` 에서 `.atp/work-session/` 라인 제거 (추적 기본 — 라인을 추가하지 않음)

### 확인

- [ ] `docs/index.md` 가 생성됐는가?
- [ ] `CLAUDE.md` 에 `<!-- atp:begin -->` 블록이 추가됐는가?
- [ ] `.gitignore` 에 `.atp/work-session/` 라인이 **없는가**? (추적 기본 — 라인이 없어야 정상)

> **기존(1차 마이그레이션 완료) 소비 레포**: `.gitignore` 에 `.atp/work-session/` 라인이 남아 있다면 해당 1줄을 직접 제거하면 추적이 활성화된다 (구경로 `.claude/work-session/` 라인은 유지).

> **opt-out**: 추적을 원치 않는 레포는 `.gitignore` 에 `.atp/work-session/` 1줄을 추가해 opt-out 할 수 있다. public 레포이거나 work-session 산출물에 내부 발화·비판이 기록되어 공개 노출이 부적절한 경우에 적합하다.

> init 은 멱등하다. 이미 존재하는 파일은 덮어쓰지 않으므로 재실행해도 안전하다.

---

## 2단계. placeholder 채우기

init 이 생성한 파일에는 프로젝트별로 채워야 할 placeholder 가 있다.

### 2-A. verification-strategies.md — 검증 명령 교체

`docs/development/verification-strategies.md` 의 YAML 블록 `cmd` 를 프로젝트 실제 명령으로 치환한다.

- [ ] **L1 typecheck** `cmd` → 예: `pnpm typecheck` / `tsc --noEmit` / `cargo check` / `mypy .` / `go vet ./...`
- [ ] **L1 unit** `cmd` → 예: `pnpm test` / `jest` / `cargo test` / `pytest` / `go test ./...`
- [ ] **L2 contract** `cmd` + preconditions → 외부 의존 테스트가 있을 때만. 없으면 해당 블록 삭제 가능.
- [ ] **verify-all** 통합 스크립트 → 단일 명령으로 L1 + L2 순차 실행. 필요 없으면 블록 삭제 후 개별 `cmd` 만 유지해도 된다.

### 2-B. document-category-classification.md — 카테고리 조정

`docs/development/document-category-classification.md` 의 카테고리 표를 프로젝트에 맞게 조정한다.

- [ ] 프로젝트와 무관한 카테고리 행 삭제 (예: 순수 라이브러리 → `maintenance/` 삭제 가능).
- [ ] 프로젝트 고유 카테고리 추가 (예: 웹 UI 프로젝트 → `uiux-qa-report/`).
- [ ] 변경 후 `docs/index.md` 카테고리 표와 동기화됐는가?

### 2-C. CLAUDE.md — 프로젝트 정보 채우기

init 이 append 한 atp 안내 블록 외에, CLAUDE.md 나머지 섹션(기술 스택, 주요 명령어, 코딩 규칙)도 프로젝트 실제 내용으로 채운다.

- [ ] "기술 스택" 표가 실제 런타임/언어/패키지 매니저/테스트 프레임워크로 채워졌는가?
- [ ] "주요 명령어" 코드 블록이 실제 `install` / `dev` / `build` / `test` 명령으로 채워졌는가?
- [ ] "코딩 규칙" 섹션에 프로젝트 고유 규칙이 기재됐는가?

---

## 3단계. 스모크 테스트

플랫폼별 입력:

- **Claude Code**: `/atp:task 안녕, 에이전트 팀이 로드됐는지 확인만 해줘`
- **Codex** (verified-empirical 2026-06-10, codex-cli 0.138.0): `$atp:task 안녕, 에이전트 팀이 로드됐는지 확인만 해줘`
- **Gemini** (TODO:실측 — 배포형 확정 전): `/atp:task 안녕, 에이전트 팀이 로드됐는지 확인만 해줘`
- **opencode** (verified-empirical 2026-06-24, opencode 1.17.9): `opencode run --command atp-task "안녕, 에이전트 팀이 로드됐는지 확인만 해줘"`

> opencode 는 마켓플레이스 plugin 이 아니라 npm 어댑터로 설치한다: `npx @atp-opencode/opencode install` (위 0단계의 marketplace/install 단계 불필요). 상세는 [faq.md](./faq.md) · [`../../adapters/opencode/README.md`](../../adapters/opencode/README.md).

- [ ] orchestrator 가 `docs/development/agent-team-protocol.md` 를 읽었는가?
- [ ] `.atp/work-session/<sid>/` 디렉토리가 생성됐는가?
- [ ] `report.md` 초기 스키마 v1 헤더가 기록됐는가?

세 가지 모두 YES 면 설정 완료.

---

## 관련 문서

- [faq.md](./faq.md) — 설치 실패·명령 미인식·graphify skip 등 문제 해결
- [`../../plugins/atp/docs/development/agent-team-protocol.md`](../../plugins/atp/docs/development/agent-team-protocol.md) — 3-tier 운영 프로토콜 전문
- `verification-strategies.md` — 검증 전략 레지스트리 (`/atp:init` 이 소비 프로젝트 `docs/development/` 에 생성, 2-A 에서 편집)
- `document-category-classification.md` — 카테고리 분류 기준 (`/atp:init` 이 생성, 2-B 에서 편집)
- [`../../plugins/atp-graphify/docs/graphify-usage.md`](../../plugins/atp-graphify/docs/graphify-usage.md) — atp-graphify add-on 설치·통합 (옵트인)
