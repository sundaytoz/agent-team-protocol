---
kind: usage
title: 이식 후 설정 체크리스트
description: cp-R 이식 직후 30분 이내 `/task` 진입 상태로 만드는 체크리스트.
owner: template-maintainer
stability: living
last_reviewed: 2026-05-07
---

# 이식 후 설정 체크리스트

cp-R 로 템플릿을 복사한 직후 **30분 내 완료** 를 목표로 한다. 한 번만 수행하면 이후 `/task` 가 정상 동작한다. 각 항목은 이식자 실수 카탈로그(`faq.md` M1~M8) 와 연동된다.

복사 절차 자체는 `../../README.md` §3 참조. 이 문서는 그 **이후** 의 프로젝트 맞춤화 단계다.

---

## 0. 복사 제외 재확인 (2분) — M5 예방

- [ ] `README.md` 가 본 템플릿의 것이 아니라 **내 프로젝트의 README** 인가? (덮어썼다면 복구)
- [ ] `TEMPLATE_DEV.md` 가 프로젝트 루트에 **없어야** 한다. 있다면 삭제.
- [ ] `SECURITY.md` · `AUTHORS` · `LICENSE` 는 **내 프로젝트 것** 이어야 한다. 원본 템플릿 버전이 복사됐다면 삭제 후 독자 작성.
- [ ] `.claude/work-session/` 이 비어있는가? 템플릿 레포의 과거 세션이 함께 끌려왔다면 `rm -rf .claude/work-session` 실행.

권위 위치: `../../README.md` §3 (설치) 의 "복사 제외" 블록.

---

## 1. CLAUDE.md 병합 (5분) — M1 예방

- [ ] 프로젝트 루트에 `CLAUDE.md` 가 있는가? 없으면 템플릿의 것을 가져오되 내용은 프로젝트 고유로 교체.
- [ ] 플레이스홀더 잔존 여부 확인:

  ```bash
  grep -nE "\{(PROJECT_NAME|install|dev|build|test|typecheck or lint)\}" CLAUDE.md
  ```

  출력이 0줄이 될 때까지 각 자리를 실제 값으로 치환.
- [ ] "에이전트 팀 운영" 섹션 + "문서화 정책" 섹션이 보존됐는가? (템플릿 핵심 진입점)
- [ ] "주요 명령어" 표가 내 프로젝트의 실제 명령으로 채워졌는가?

---

## 2. 검증 명령 교체 (10분)

`docs/development/verification-strategies.md` 의 YAML 블록 `cmd` 를 프로젝트 실제 명령으로 치환.

- [ ] **L1 typecheck** `cmd` → 예: `pnpm typecheck` / `tsc --noEmit` / `cargo check` / `mypy .` / `go vet ./...`
- [ ] **L1 unit** `cmd` → 예: `pnpm test` / `jest` / `cargo test` / `pytest` / `go test ./...`
- [ ] **L2 contract** `cmd` + preconditions → 외부 의존 테스트가 있을 때만. 없으면 해당 블록 삭제 가능.
- [ ] **verify-all** 통합 스크립트 → 단일 명령으로 L1 + L2 를 순차 실행. 스크립트를 만들지 않는 경우 이 블록을 삭제하고 개별 `cmd` 만 유지해도 된다(`faq.md` 관련 항목 참조).

---

## 3. 카테고리 조정 (5분) — M2 예방

`docs/development/document-category-classification.md` 의 카테고리 표 점검.

- [ ] 프로젝트와 **무관한 카테고리** 는 행 삭제 (예: 순수 라이브러리 → `maintenance/` · `operations/` 삭제 가능).
- [ ] 프로젝트 고유 카테고리 **추가** (예: 웹 UI 프로젝트 → `uiux-qa-report/`).
- [ ] 변경 후 `docs/index.md` 카테고리 표에 반영했는가? (두 파일은 동기화 유지)

---

## 4. 에이전트 기술 스택 주석 (5분)

`.claude/agents/code-writer.md` / `migration-writer.md` 에서 프로젝트 맞춤 부분 확인.

- [ ] `code-writer.md` 의 "작성 규칙" 섹션을 프로젝트 `CLAUDE.md` 의 코딩 규칙과 **링크** 로 연결 (권위는 CLAUDE.md).
- [ ] DB 가 없는 프로젝트라면 `migration-writer.md` 삭제 + `implementation-advisor.md` 의 Worker 목록에서 migration-writer 언급 제거(`faq.md` 관련 항목 참조).
- [ ] 특정 ORM/마이그레이션 도구가 있으면 `migration-writer.md` 의 "절차 3단계" 를 구체화 (Drizzle / Alembic / EF Core / Flyway / Prisma 등).

---

## 5. graphify 도입 여부 결정 (선택, 3분)

- [ ] 프로젝트 크기가 작고 구조 탐색 비용이 낮으면 **생략** 가능 — 이 경우 `graphify-*` 에이전트 3종은 세션 종료 시 "skip: no-graphify" 로 기록되고 아무 동작도 하지 않는다.
- [ ] 도입하는 경우 `docs/development/graphify-usage.md` 의 9 단계를 따른다.

---

## 6. `.gitignore` 확인

- [ ] `.gitignore` 에 다음 한 줄이 있는가?

  ```gitignore
  .claude/work-session/
  ```

  `docs/graph/.gitignore` 는 템플릿에 이미 포함 — 그래프 본체만 무시하고 `index.md` 는 커밋된다.

---

## 7. 스모크 테스트

새 Claude Code 세션에서:

```
/task 안녕, 에이전트 팀이 로드됐는지 확인만 해줘
```

- [ ] orchestrator 가 `docs/development/agent-team-protocol.md` 를 읽었는가?
- [ ] `.claude/work-session/<sid>/` 디렉토리가 생성됐는가?
- [ ] `report.md` 초기 스키마 v1 헤더가 기록됐는가?

세 가지 모두 YES 면 이식 완료.

---

## 관련 문서

- [`../../README.md`](../../README.md) §3 — 설치 절차 및 복사 제외 목록 (cp-R 권위)
- [faq.md](./faq.md) — 문제 해결 + 이식자 실수 카탈로그
- [`../development/agent-team-protocol.md`](../development/agent-team-protocol.md) — 3-tier 운영 프로토콜 전문
- [`../development/verification-strategies.md`](../development/verification-strategies.md) — 검증 전략 레지스트리
- [`../development/document-category-classification.md`](../development/document-category-classification.md) — 카테고리 분류 기준
- [`../development/graphify-usage.md`](../development/graphify-usage.md) — graphify 설치·통합 (선택)
