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
| [ADR-0006](./ADR-0006-three-platform-support.md) | v1.4.0 — 3-플랫폼 지원 (Claude Code / Codex / Gemini): capability tier + single-read 경로 마이그레이션 | accepted (capability matrix·판정표 SSoT 지위는 ADR-0009 가 번들 한정 부분 supersede) | 2026-06-09 |
| [ADR-0007](./ADR-0007-plugin-root-subdirectory.md) | v2.0.0 — 플러그인 루트 서브디렉토리 전환 (plugins/atp/, plugins/atp-graphify/) + Gemini manifest 위치 확정 | accepted | 2026-06-10 |
| [ADR-0008](./ADR-0008-platform-neutral-model-policy.md) | 모델 선택 정책 플랫폼 중립화 (tier S/M/L + effort 직교 노브) + orchestrator cap 규칙 + report 스키마 v2 | accepted | 2026-06-10 |
| [ADR-0009](./ADR-0009-bundle-runtime-platform-neutralization.md) | 번들 런타임 플랫폼 중립화 (capability 자가판정) + 3사 capability 데이터 동결 보존 (ADR-0006 부분 supersede) | accepted | 2026-06-11 |
| [ADR-0010](./ADR-0010-work-session-git-tracking.md) | work-session 추적 분할 정책 — 플러그인 기본=추적, 레포별 opt-out 허용, 이 소스 레포는 public+발화인용+내부비판 노출로 opt-out (ADR-0006 L34 부분 supersede) | accepted | 2026-06-16 |
| [ADR-0011](./ADR-0011-research-axis-completeness-prevention.md) | v2.2.0 — research 단계 축-완결성 예방 게이트 §4.8 신설 (독립 분류체계 ≥2 교차참조 + 폐쇄-신뢰도 마커 + 전수열거 주장 금지 + §9 사후승격) + research-advisor 자가검증 강화(동명이인 disambiguation·JS-SPA 출처 흡수) | accepted | 2026-06-17 |
| [ADR-0012](./ADR-0012-backport-self-leak-grep-gate.md) | backport 출처 식별자 self-grep 게이트 — 일반화 게이트 선언(ADR-0004/0005)을 release-checklist §7 + documentation/design-advisor 자가검증으로 실행 경로화 | accepted | 2026-06-17 |
| [ADR-0013](./ADR-0013-protocol-core-section-on-demand-routing.md) | protocol.md 진입 강제로드 토큰 감축 — 파일내 코어 구획(C1~C7) + on-demand 라우팅 (물리분할 회피, §N 불변·끊긴 인용 0, ~94% 감축) | accepted | 2026-06-18 |
| [ADR-0014](./ADR-0014-opencode-host-adapter-strategy.md) | opencode 호스트 어댑터 전략 (4번째 Layer-2) — generator 기반 CLI installer + Tier A-flat(PoC 실측) + 모델 슬러그 생략·상속 (빌드는 D7 후속) | accepted | 2026-06-24 |
| [ADR-0015](./ADR-0015-antigravity-host-verification.md) | Antigravity IDE 호스트 검증 (5번째 Layer-2) — GEMINI.md 지침파일 + `/atp-task` 하이픈 문법 + Tier A-flat 확정 + F-3PLAT-4 resolved-not-needed | accepted | 2026-06-30 |
| [ADR-0016](./ADR-0016-remove-feedback-inbox-system.md) | feedback inbox 시스템 제거 — "feedback" 3갈래 중 inbox 카테고리만 폐기(14→13), protocol_feedback·memory type:feedback 존치 | accepted | 2026-07-06 |
| [ADR-0017](./ADR-0017-subagent-lifecycle-recovery.md) | subagent silent-start lifecycle recovery — 사용자 승인 기반 독립 invocation 재시도, ownership·late completion 격리, 유한 phase 종단 | accepted | 2026-07-20 |
| [ADR-0018](./ADR-0018-research-falsification-corroboration-harvest.md) | v2.9.0 — research 불확실성 게이트 3종(반증 패스·단건 독립확증 single-source 플래그·수확 점검 1회 재분해, §4.8 적층) + add-on v2.2.0 graphify-out misplaced-output 방어·prior_lookup handoff + §8 research-lite 프로파일 | accepted | 2026-07-21 |
