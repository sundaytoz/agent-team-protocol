---
kind: usage
title: Codex 단일 서브에이전트 연결 스모크
description: 실제 child 실행·결과 수신 확인 절차와 2026-09-08 관측 범위.
owner: template-maintainer
stability: living
last_reviewed: 2026-10-29
---

<p align="center">
  <a href="codex-connection-smoke.md">한국어</a> ·
  <a href="codex-connection-smoke.en.md">English</a>
</p>

# Codex 단일 서브에이전트 연결 스모크

이 스모크는 설치·skill 로드 확인 이후 실제 child의 spawn 수락부터 terminal 결과 취합까지 확인한다. 지원 범위의 정본은 [배포 capability profile](../../plugins/atp/skills/codex-team/SKILL.md)과 [ADR-0026](../adr/ADR-0026-codex-builtin-subagents-without-marker.md)이다.

## 실행 절차

1. [설치 체크리스트](./setup-checklist.md)에 따라 base를 설치하고 새 세션을 연다. 2.19.0부터 추가 add-on·hook trust는 필요 없다.
2. 세션에서 다음을 요청한다.

   ```text
   $atp:task 서브에이전트 1명을 실제로 가동해 연결 상태를 확인해줘
   ```

3. Preflight의 선택 mode가 `host_managed_subagent_orchestration`인지 확인한다. 배포 profile은 Codex에서 조건 없이 `team_execution_enabled: true`다.
4. 실제 spawn 수락 identity, child terminal 결과, report invocation identity가 대응하는지 확인한다. 대기·follow-up은 Codex 내장 workflow가 관리하며, 결과를 모두 수신하기 전에 성공으로 마감하지 않는다.
5. 세션 보고서에 요청·수락·terminal·취합 각각 1건, 최종 pending/running 0건을 기록한다. 사용 불가 도구·미검증 단계는 별도 concern으로 남긴다.

## 2026-09-08 연결 관측

아래는 2.18.0 profile 아래에서 수행한 저장소 작업 세션의 실제 spawn 응답과 `FINAL_ANSWER`를 바탕으로 공개용으로 요약한 기록이다. 원본 대화·로컬 절대 경로·사용자 식별자는 포함하지 않는다. 과거 보고서를 변경하거나 새로운 release qualification으로 재분류한 기록이 아니다.

| 항목 | 관측 |
|---|---|
| 요청 / spawn 시도 / 수락 | 1 / 1 / 1 |
| Terminal / 취합 | 1 / 1; 같은 child 결과는 중복 집계하지 않음 |
| 결과 대응 | 기대한 `report_invocation_id` 일치 |
| Child 반환 | `status=connected`; cwd가 요청 프로젝트와 일치; `mutations=0` 보고 |
| list / interrupt | 0 / 0 |
| `update_plan` | child에 제공되지 않음 (당시 profile의 bind 단계 미수행; 2.19.0에서 해당 단계 제거) |
| Surface·버전 | 해당 실행의 CLI/App/IDE 구분과 host 버전은 별도 측정하지 않음 |

결론은 **이 세션에서 단일 child 실행과 결과 전달·취합이 성공했다**는 것이다.

단일 결과로 다중 child 결과 취합, 승인 후 same-identity continuation, 실행 중 steering·취소, App/IDE 지원을 추가로 검증했다고 해석하지 않는다. 결과 취합은 Codex 내장 동작에 위임하며, 2026-08-26 Codex CLI 0.149.1 스모크에서는 내장 barrier가 시차 결과 2건 중 1건만 전달했다. 이 caveat은 [Known Issues](./known-issues.md)에서 추적한다.
