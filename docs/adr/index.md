# ADR 인덱스

**카테고리 용도**: 기술 선택·아키텍처 원칙에 대한 되돌리기 어려운 결정. 불변(append-only). 결정을 뒤집을 때는 기존 ADR 을 수정하지 않고 새 ADR 을 발행하여 "supersedes ADR-NNNN" 명시.

파일명 규칙: `ADR-NNNN-kebab-case-title.md` (NNNN 은 0001 부터 순차 증가)

## 결정 목록

| ADR | 제목 | 상태 | 날짜 |
|---|---|---|---|
| ADR-0001 | (public repo 이전 계획 — 본 레포에 파일 미보존, 프로토콜 §6 에서 참조) | — | — |
| [ADR-0002](./ADR-0002-plugin-only-migration.md) | cp-R 배포 폐기 및 plugin-only 2플러그인(atp + atp-graphify) 전환 | accepted | 2026-06-01 |
| [ADR-0003](./ADR-0003-consuming-project-generalization-backport.md) | v1.1.0 — 소비 프로젝트 일반화 자산 역이식 (계획 가시화·옵션설계·자가검증 계약) | accepted | 2026-06-05 |
| [ADR-0004](./ADR-0004-consuming-project-generalization-backport-followup.md) | v1.2.0 — 소비 프로젝트 일반화 자산 후속 역이식 (호출 실패 처리·자가점검 2종·graph 이월금지·Decision Log·analysis perspective) | accepted | 2026-06-05 |
| [ADR-0005](./ADR-0005-orchestrator-bidirectional-flow-control.md) | v1.3.0 — orchestrator 양방향 흐름 제어 (backward 회귀 재디스패치·forward 트랙 설계 게이트) + 시그널 세탁 방지 + 조사 출처 신뢰도 게이팅 | accepted | 2026-06-08 |
| [ADR-0006](./ADR-0006-three-platform-support.md) | v1.4.0 — 3-플랫폼 지원 (Claude Code / Codex / Gemini): capability tier + single-read 경로 마이그레이션 | accepted | 2026-06-09 |
