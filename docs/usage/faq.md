---
kind: usage
title: 문제 해결 / FAQ
description: 이식·사용 중 흔한 실수와 대응(ADR-0001 M1~M8 카탈로그 포함).
owner: template-maintainer
stability: living
last_reviewed: 2026-05-07
---

# 문제 해결 / FAQ

이식자가 자주 마주치는 문의와 이식 실수 카탈로그를 한 곳에 모았다. 사전 예방은 [setup-checklist.md](./setup-checklist.md) 를 우선 참고한다.

---

## FAQ

### Q. `/task` 호출해도 팀 모드로 진입 안 한다.

A. `.claude/skills/task/SKILL.md` 가 있는지 확인. 새 Claude Code 세션에서 시도. 첫 줄의 frontmatter(`trigger: /task`) 가 깨졌는지도 확인.

### Q. `verification-advisor` 가 통합 검증 스크립트 없다고 실패한다.

A. `../development/verification-strategies.md` 의 `verify-all` 블록 `cmd` 를 프로젝트 실제 명령으로 교체했는지 확인. 스크립트가 없다면 L1/L2 개별 `cmd` 만 써도 된다.

### Q. Advisor 가 서로 모순된 결정을 내린다.

A. `../development/agent-team-protocol.md` §4 충돌 조정. 각 advisor 산출물의 `concerns` 필드가 교차점. orchestrator 가 1라운드 재검토 요청 → 실패 시 사용자에게 `AskUserQuestion`.

### Q. Worker 가 담당 파일 외부를 수정하려고 한다.

A. `implementation-advisor` 의 파일 소유권 맵 확인. 한 파일에 2개 worker 할당되진 않았는지 검사. Worker 가 "한계" 로 표기해 반환했다면 advisor 가 다시 할당한다.

### Q. 모델이 항상 `opus` 만 써서 비용이 크다.

A. `report.md` 의 `invocations[].model_choice.rationale` 을 확인. 스케일 루브릭(`../development/agent-team-protocol.md` §5) 에 맞는지 점검. 단순 조사인데 `large` 판정이 계속 나오면 orchestrator 프롬프트에 "기본 sonnet, 재호출 시 upgrade" 를 명시적으로 상기시킨다.

### Q. 세션이 중간에 끊겼다. 이어서 하려면?

A. 같은 `sid` 디렉토리가 이미 있어도 이어쓰지 않는다. 새 sid 로 시작하며 `report.md` 에 `resumed_from: <이전 sid>` 를 기록한다. 이전 `report.md` 에서 어느 phase 까지 끝났는지 확인하고 거기서부터 재개한다 (`../development/agent-team-protocol.md` §7 재개 규약).

### Q. graphify 없이도 팀이 동작하는가?

A. 예. `graphify-lookup-advisor` 가 `no-graph` 반환하면 `research-advisor` 로 자동 에스컬레이션. 세션 종료 시 graph-refresh 단계는 "skip: no-graphify" 로 기록하고 넘어간다. 상세는 `../development/graphify-usage.md`.

### Q. 내 프로젝트는 DB 가 없는데 `migration-writer` 가 필요한가?

A. 필요 없다. `.claude/agents/migration-writer.md` 를 삭제하고 `implementation-advisor.md` 의 Worker 목록에서 migration-writer 언급을 제거한다. tier 구조에는 영향 없음.

### Q. 테스트 명령이 여러 개인데 `verify-all` 하나로 통합하기 어렵다.

A. 통합 스크립트를 만들지 말고 `../development/verification-strategies.md` 에 전략을 여러 개 등록한다. `verification-advisor` 가 변경 scope 에 매칭되는 것만 순차 실행. 전략이 2개 이상 + worker 분할이 필요해지면 `../development/agent-team-protocol.md` §9 (확장 트리거) 참조.

### Q. 라이선스를 `TBD` 로 써도 되는가?

A. 아니오. 본 템플릿은 MIT 지만 **`LICENSE` 는 cp-R 복사 제외** 다 (README §3). 이식자가 자기 프로젝트의 라이선스를 독자 결정·배치해야 한다. "라이선스 미결정" 상태로 공개 배포하면 기여자 권리관계가 모호해진다.

---

## 이식자 실수 카탈로그 (M1~M8)

ADR-0001 §8.2 에서 파생. 체크리스트로 사전 예방 가능한 항목은 [setup-checklist.md](./setup-checklist.md) 참조.

| # | 실수 유형 | 증상 | 핵심 대응 |
|---|---|---|---|
| **M1** | CLAUDE.md 플레이스홀더 방치 | 세션 시작 시 에이전트가 `{PROJECT_NAME}` · `{install}` 등을 그대로 인용 | `grep -nE "\{(PROJECT_NAME\|install\|dev\|build\|test\|typecheck or lint)\}" CLAUDE.md` 결과 0줄이 될 때까지 치환 |
| **M2** | docs 카테고리 오분류 | 분석 문서를 `changes/` 에 둠, 구조 문서를 `work-log/` 에 둠 | `../development/document-category-classification.md` 의 "빠른 결정 순서" 재확인 |
| **M3** | 에이전트 tools 필드 누락 | Worker 가 "도구 없음" 으로 spawn 실패 | 각 `.claude/agents/<name>.md` frontmatter 에 `tools:` 명시 (카탈로그 표의 도구 칼럼 참조) |
| **M4** | 세션 디렉토리 경로 불일치 | `report.md` 참조가 broken | 경로는 반드시 `.claude/work-session/<YYYYMMDD-HHMMSS>/` 고정. 타임존·하이픈 형식 준수 |
| **M5** | cp-R 복사 제외 위반 | 이식 프로젝트에 `README.md` · `TEMPLATE_DEV.md` · 원본 `LICENSE`/`AUTHORS`/`SECURITY.md` 가 섞임 | README §3 의 "복사 제외" 목록 재확인. `rm -rf .claude/work-session` 누락이 빈번 |
| **M6** | 세션 ID 충돌 오해 | "다른 프로젝트와 sid 가 겹치는가?" 혼동 | 세션 경로는 프로젝트 루트 기준 상대. 프로젝트 간 실제 충돌 없음 |
| **M7** | 라이선스를 `TBD` 로 유지 | 공개 배포 시 기여자 권리관계 모호 | 위 FAQ "라이선스를 `TBD` 로 써도 되는가?" 참조. `LICENSE` 를 독자 결정 |
| **M8** | `docs/feedback/inbox/` 경로 부재 | `/feedback` 스킬이 기록 대상 디렉토리 없다며 실패 | `mkdir -p docs/feedback/inbox` 실행. feedback 스킬 미도입이면 무시 가능 |

---

## 관련 문서

- [setup-checklist.md](./setup-checklist.md) — 이식 후 설정 체크리스트 (M1/M5 의 사전 예방)
- [`../development/agent-team-protocol.md`](../development/agent-team-protocol.md) — 운영 프로토콜 전문 (§4 충돌 조정, §5 모델 선택, §7 재개 규약)
- [`../development/verification-strategies.md`](../development/verification-strategies.md) — 검증 전략 레지스트리
- [`../development/graphify-usage.md`](../development/graphify-usage.md) — /graphify 설치·통합
- [`../../README.md`](../../README.md) §3 — 설치 및 복사 제외 목록 (cp-R 권위)
