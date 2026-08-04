---
kind: changes
title: 비정상 종결 기록 의무 · 회고 산출 sink 명문화 · research worker 반환 규격화
description: lifecycle 실패의 silent absorption 금지 + retro 산출물 오지시 차단 + parallel-explorer 반환 계약 규격화로 취합 tail 축소. 2.10.0→2.11.0.
date: 2026-08-04
owner: template-maintainer
stability: living
last_reviewed: 2026-08-04
---

# 비정상 종결 기록 의무 · 회고 산출 sink · worker 반환 규격화 (2.10.0 → 2.11.0)

세션 병목 분석 보고서를 검토하는 과정에서 드러난 3건을 반영한다. 세 건 모두 **규약은 이미 존재했으나 집행 경로가 비어 있던** 유형이다.

## 변경 내용

### 1. 비정상 종결의 기록 의무 (§2.5 · §8)

- `agent-team-protocol.md` §2.5 에 **`실패의 기록 의무 (silent absorption 금지)`** 절을 신설했다. lifecycle 실패를 사용자 보고도 기록도 없이 orchestrator 직접 수행으로 흡수하고 세션을 진행하는 것을 금지한다. phase 종단 표의 Tier B self-check·fallback·skip 은 허용된 **종단**이지 보고·기록의 면제가 아님을 명시했다.
- §8 lifecycle 필드 규약에 **optional 의 예외**를 추가했다. `completed` 가 아닌 종결(`failed` / `interrupted` / `silent_stall` / `late_completion`)에는 `termination` 기록이 의무이며, 흡수한 경우에도 선택한 종단 사유를 `lifecycle_fallback_reason` 에 남긴다. 필드 부재가 유효한 범위는 정상 완료·legacy report 로 한정된다.

관측된 실패 모드: 운영 세션에서 문서화 단계 advisor 가 API 커넥션 오류로 종결됐는데 clean retry·사용자 보고 없이 orchestrator 직접 검증으로 마감되고 보고서에는 usage 0 행만 남았다. 이후 그 세션을 분석한 별도 보고서가 그 행을 실행 실패가 아닌 no-op 으로 읽어 실패 사실이 분석에서 소실됐다. §2.5 의 복구 규약은 그 시점에 이미 완비돼 있었으므로 결함은 규약 부재가 아니라 **기록 경로가 전건 optional 이라 무기록 흡수가 스키마상 합법**이었다는 점이다.

### 2. 회고 산출 sink 명문화 (§12 · SKILL §9)

- §12 절차 1 에 회고 산출 sink 가 `report.md` 의 `Retrospective` 섹션임을 명시하고, `retrospective-advisor` 의 `Write` 미보유가 절차 3~5("orchestrator 가 수용 판단 후 반영")를 지키는 **의도된 제약**임을 기록했다.
- orchestrator 가 회고 dispatch 에서 별 파일 산출을 요구하지 않도록 규정했다. 요구하면 advisor 가 규약대로 거부하고 섹션만 채우는데, 그 정상 동작이 "산출물 생성 실패" 로 오독되어 tools 부여 결함으로 잘못 진단된 관측이 있다.
- `skills/task/SKILL.md` §9 의 retro 항목에 같은 취지를 1줄 추가했다.

### 3. research worker 반환 규격화 — 취합 tail 축소 (agents 2건)

- `parallel-explorer` 출력 계약에 `결론`(1줄) · `source_confidence`(포인트 한정) · `concerns` 세 절을 추가했다. 세 절은 비어 있을 수 없으며, 판정 근거가 부족하면 그 사실을 `결론` 에 쓰고 `source_confidence: low` + 사유를 남긴다. 자가 검증 항목도 3개로 늘렸다.
- `research-advisor` 산출을 **결론 전용 `index.md` + 포인트별 근거 파일** 2층으로 분리하고 **취합 규약(재작성 금지)** 을 신설했다. 취합은 (1) worker 반환 본문을 그대로 포인트별 파일로 저장, (2) `결론`·`source_confidence` 를 `index.md` 결론 요약표로 발췌, (3) `concerns` 합집합 승계 — 3동작으로 끝난다. `index.md` 에 포인트별 요약 문단을 옮겨 적는 것을 금지했다.
- worker 의 **파일 쓰기 금지는 유지**했다. research worker 의 read-only 성질은 §2.5 의 `late_completion` 격리(수용권 회수 후 도착한 결과를 안전하게 폐기)가 성립하는 근거이며, worker 가 디스크에 쓰면 폐기한 결과의 산출물이 남는다.

관측된 병목: 조사 단계 대기 시간 중 절반 가까이가 worker 병렬 구간이 아니라 advisor 의 반환문 재작성·파일 저술이었다. 규격화는 그 직렬 tail 을 줄이고, 동시에 하류 advisor 가 `index.md` 만 읽어도 판단이 서게 해 하류 토큰도 함께 낮춘다.

**개정 규약 dry-run 에서 잡은 실행상 결함 3건을 같은 변경에 반영**했다(`CLAUDE.md` 의 "정의 편집 시 실호출 1회" 규약 집행):

- **포인트별 파일명 규칙 부재** — `<포인트>.md` 만 있어 번호인지 제목 slug 인지 판단 불가였다. `P<번호>-<제목-slug>.md` 로 확정했다(번호만 쓰면 내용 식별에 파일을 열어야 하고, slug 만 쓰면 정렬이 조사 순서와 어긋난다).
- **frontmatter `concerns: []` 의 리터럴/placeholder 모호성** — 실제 목록을 채우고, 승계·발견 concern 이 0건일 때만 `[]` 로 둠을 명시했다. `generated_at` 의 타임존 관례(`<sid>` 와 동일한 프로젝트 타임존, offset 포함)도 함께 못박았다.
- **`종합 판단` = "관계만, 재서술 금지" 의 사각** — 포인트 간 실질적 관계가 희박하면 관계를 쓰기 위해 각 포인트 결론을 다시 풀어써야 하므로, 재서술 금지를 지킬 수 없는 구조였다. "포인트 간 관계 없음(독립 조사 n건)" 으로 마감하는 예외를 추가하고, 관계를 억지로 구성하려 결론을 풀어쓰는 것이 재서술에 해당함을 명시했다.

worker 반환 규격 자체는 dry-run 에서 2개 worker 모두 6절을 순서대로 빠짐없이 채워 반환해 규격 이탈 보정 0건이었다.

## 호환성

- 기존 schema v2 report 는 수정 없이 유효하다. 새 기록 의무는 **이번 버전 이후 발생하는 비정상 종결**에만 적용되며, legacy report 의 종결 정보는 `unknown` 으로 남고 소급 기재 대상이 아니다(§8 진화 규칙 · `retroactive` 라벨 규약).
- lifecycle 필드 이름·상태 어휘·phase 종단 표는 변경하지 않았다. `attempt` / `termination` / `retry_of` / `lifecycle_fallback_reason` 4필드와 상태 흐름은 그대로다.
- `parallel-explorer` 의 tools·read-only 계약은 변경 없다. 반환 텍스트에 절이 추가될 뿐이므로 기존 프롬프트도 계속 동작하며, 규격을 벗어난 반환은 advisor 가 해당 항목만 보정하고 `concerns` 에 "규격 이탈 보정" 으로 남긴다.
- add-on `atp-graphify` 는 무변경(2.3.0 유지).

## 사용자에게 보이는 변화

- advisor 호출이 실패하면 보고서에 그 사실이 남는다. orchestrator 가 직접 수행으로 메꿨더라도 어느 phase 가 왜 대체 수행됐는지 `report.md` 에서 확인할 수 있다.
- 회고 단계에서 "파일을 만들 수 없다" 는 보고가 사라진다. 회고 산출물 유무는 `report.md` 의 `Retrospective` 섹션으로만 판정한다.
- 조사 단계 산출물이 `index.md`(결론) + 포인트별 파일(근거) 2층으로 분리된다. 하류 단계와 사용자 모두 결론을 먼저 보고 필요할 때 근거로 내려간다.

## 검증

- `python3 tests/lifecycle-contract/validate.py` — lifecycle fixture + 문서 invariant(§2.5 host-neutrality, 고정 시간값 0, 상태 어휘 전수, optional 4필드 존재)
- release-checklist §1 상대 링크 · §4 base manifest 4곳 2.11.0 동기 · §5 agent catalog · §6 카테고리 index · §7 소비 프로젝트 식별자 잔류 0 · §8 끊긴 §N 인용 0
- 편집한 agent 정의 실호출 1회 (`CLAUDE.md` 규약 — 정의 편집 시 세션 종료 전 실호출)
