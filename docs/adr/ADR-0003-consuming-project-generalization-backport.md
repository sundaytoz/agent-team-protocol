---
kind: adr
adr_number: "0003"
title: v1.1.0 — 소비 프로젝트 일반화 자산 역이식 (계획 가시화 · AskUserQuestion 옵션설계 · clarify 분기 · 산출물 자가검증 계약)
status: accepted
date: 2026-06-05
deciders:
  - template-maintainer
  - stzjungsoo
supersedes: []
---

# ADR-0003: v1.1.0 — 소비 프로젝트 일반화 자산 역이식

## 상태

**Accepted** — 2026-06-05.

---

## 맥락

소비 프로젝트는 ADR-0002(plugin-only 전환) **이전**의 cp-R fork 잔재를 보유했고, 그 fork 에서 운영 세션을 거치며 atp 본체에는 없는 일반화 가능한 규약이 누적됐다. 두 산출물(atp 본체 vs 소비 프로젝트 fork)이 **양방향 분기** 한 상태였다:

- **atp 가 앞선 영역**: deterministic model-selection(§5), 대형 호출 분할(§2.1), open_questions 경로(§2.2), 지적 3단계(§2.3), system-reminder 처리(§2.4), graphify 유예/조건(§3.1/3.2), 동결스펙(§4.1)·UI/UX(§4.2)·AC 전수체크(§4.3), 게이트 2단계(§6), peer_agents(§11.1), Phase 완료(§13), 탐색 도구(§14).
- **소비 프로젝트 fork 가 앞선 영역(일반화 가능)**: 계획 가시화 의무, AskUserQuestion 옵션 설계 규약, clarify 응대 분기, 옵션 단일수렴 skip 금지, advisor/worker 산출물 자가검증 계약, requirements 생명주기 gap-hunt, design 시그니처 inflate 방지, 구현 unused 진단 게이트.

소비 프로젝트 fork 의 일반화 가능 자산을 atp 본체로 역류시키지 않으면, plugin-only 로 마이그레이션할 때 해당 규약이 소실된다.

## 결정

소비 프로젝트 fork 의 **일반화 가능 규약만** atp 본체에 머지한다(프로젝트 특화·개인 메모리 slug 참조는 제외). 섹션 번호 충돌(fork §4.2=clarify vs atp §4.2=UI/UX, fork §12=자가검증 vs atp §12=회고)을 피해 의미 위치에 삽입·재번호했다.

### 반영 내역 (v1.1.0)

| 위치 | 추가 |
|---|---|
| protocol §1 | 계획 가시화 의무 · 옵션 공간 판정 권한 (단일수렴 skip 금지) |
| protocol §4.4 | AskUserQuestion 옵션 설계 규약 + 자가 점검 5항목 |
| protocol §4.5 | clarify 응대 분기 (내용 vs 범위/축→재설계) |
| protocol §11 항목 7 + §11.2 | advisor/worker 산출물 자가 검증 체크리스트 + self_verification 반환 계약 |
| SKILL §5.0 | 계획 가시성 의무 (skip 기준 우선) |
| SKILL §9 단계 6 | 프로젝트 정의 종료/배포 게이트 generic hook |
| agents/* (13) | `## 자가 검증` + `## 반환값` 계약, frontmatter concerns_checked 리마인더 |
| requirements-advisor | 생명주기 gap-hunt · 2차 단절 점검 · 복수 이벤트 대칭 점검 |
| design-advisor | 시그니처 inflate 방지 |
| implementation-advisor | unused 진단 별도 게이트 (자가검증 4번) |

### 프로젝트 특화는 generic hook 으로 흡수

소비 프로젝트의 "운영서버 확인 게이트"·배포 판정 advisor 같은 배포 특화 규약은 atp 에 박지 않고, SKILL §9 단계 6 의 **"프로젝트 정의 종료/배포 게이트 hook"** 으로 일반화했다. 특화 내용은 소비 프로젝트의 `verification-strategies.md` 와 프로젝트 전용 advisor 로 격리한다.

### 일반화 규칙

- MEMORY `feedback_*` slug 참조는 개인 메모리이므로 atp 본체에서 제외.
- 도구명은 일반화 (`package.json` → 의존성 매니페스트, `pnpm typecheck`/`eslint` → 통합 타입체크/프로젝트 린터, Discord embed → 사용자 노출 표현).

## 검토한 대안

- **fork 양쪽 유지**: 분기 누적으로 드리프트 심화. 기각.
- **소비 프로젝트 fork §5(model-selection) 까지 역이식**: fork 버전이 atp §5 보다 구버전(단일축 small/medium/large)이라 역이식 시 퇴행. 제외.

## 결과

- atp 1.0.0 → 1.1.0 (atp · atp-graphify · marketplace 동반 bump).
- 소비 프로젝트가 plugin-only 로 마이그레이션해도 일반화 규약이 본체에 보존됨.
- 향후 atp→소비 프로젝트 역방향 드리프트(예: design AC 전수체크가 소비 프로젝트에 미반영)는 별도 정리 대상으로 남김.

## 관련 문서

- [ADR-0002](./ADR-0002-plugin-only-migration.md) — plugin-only 전환 (본 ADR 의 전제)
- `docs/development/agent-team-protocol.md` §1·§4.4·§4.5·§11.2
- `skills/task/SKILL.md` §5.0·§9
