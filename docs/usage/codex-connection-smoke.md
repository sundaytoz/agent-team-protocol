---
kind: usage
title: Codex 단일 서브에이전트 연결 스모크
description: 실제 child 실행·결과 수신 확인 절차와 2026-09-08 관측 범위.
owner: template-maintainer
stability: living
last_reviewed: 2026-09-08
---

<p align="center">
  <a href="codex-connection-smoke.md">한국어</a> ·
  <a href="codex-connection-smoke.en.md">English</a>
</p>

# Codex 단일 서브에이전트 연결 스모크

이 스모크는 설치·skill 로드 확인 이후 실제 child의 spawn 수락부터 terminal 결과 취합까지 확인한다. 전체 지원 범위의 정본은 [add-on 가이드](../../plugins/atp-codex-hooks/docs/codex-hooks-usage.md)와 [배포 capability profile](../../plugins/atp/skills/codex-team/SKILL.md)이다.

## 실행 절차

1. [설치 체크리스트](./setup-checklist.md)에 따라 base를 설치한다. Codex CLI에서 실제 팀 실행을 사용하려면 `atp-codex-hooks`를 설치하고 add-on 가이드의 trust 범위를 확인해 신뢰를 부여한 뒤 새 세션을 연다.
2. 세션에서 다음을 요청한다.

   ```text
   $atp:task 서브에이전트 1명을 실제로 가동해 연결 상태를 확인해줘
   ```

3. Preflight의 선택 mode를 확인한다. 현재 배포 profile은 exact hook marker가 있는 세션에 `host_managed_subagent_orchestration`을 적용한다. Marker가 없으면 이 요청은 독립 실행 필수이므로 `blocked_explicit_independence`, spawn 0으로 기록된다. Marker를 프롬프트에 붙여 scope를 위장하지 않는다.
4. 실제 spawn 수락 identity, child terminal 결과, pool token, report invocation identity가 대응하는지 확인한다. 결과를 모두 수신하기 전에 성공으로 마감하지 않는다.
5. 세션 보고서와 scheduling ledger에 요청·수락·terminal·취합 각각 1건, 최종 pending/running 0건을 기록한다. Pool wait는 event 수신을 위한 정상 join이며 반복 list 조회와 구분한다. 사용 불가 도구·미검증 단계는 별도 concern으로 남긴다.

## 2026-09-08 연결 관측

아래는 저장소 작업 세션의 실제 spawn 응답, `FINAL_ANSWER`, `ATP_POOL_TERMINAL_DELTA`를 바탕으로 공개용으로 요약한 기록이다. 원본 대화·로컬 절대 경로·사용자 식별자는 포함하지 않는다. 과거 보고서를 변경하거나 새로운 release qualification으로 재분류한 기록이 아니다.

| 항목 | 관측 |
|---|---|
| 실행 전제 | root context의 exact hook marker가 당시 로드한 profile과 일치 |
| 요청 / spawn 시도 / 수락 | 1 / 1 / 1 |
| Terminal / 취합 | 1 / 1; final과 hook delta는 같은 child 결과이므로 중복 집계하지 않음 |
| 결과 대응 | 기대한 pool token과 `report_invocation_id` 일치 |
| Child 반환 | `status=connected`; cwd가 요청 프로젝트와 일치; `mutations=0` 보고 |
| 대기 / list / interrupt | pool wait 1 / list 0 / interrupt 0 |
| Bind 단계 | child에 `update_plan`이 제공되지 않아 `ATP_POOL_BIND` 호출 미수행 |
| Surface·버전 | 해당 실행의 CLI/App/IDE 구분과 host 버전은 별도 측정하지 않음 |

결론은 **이 세션에서 단일 child 실행과 결과 전달·취합이 성공했다**는 것이다. `update_plan` 미제공으로 bind-plan 절차까지 완전히 준수했다고 할 수 없다. Hook terminal delta에 identity와 result hash가 포함됐다는 관측만으로 bind hook 내부 검증 전체를 입증하지 않는다.

단일 결과로 다중 child all-results barrier, capacity denial/refill, 승인 후 same-identity continuation, 실행 중 steering·취소, App/IDE 지원을 추가로 검증했다고 해석하지 않는다. 별도 [CLI 0.149.1 release qualification 근거](../../tests/runtime-behavior/evidence/codex-cli-0.149.1-hook-guarded-20260908.json)는 선언 scope의 기존 지원 근거이며 이번 관측과 구분한다. 새 관측은 [Known Issues](./known-issues.md)의 기존 축별 판정을 변경하지 않는다.

## `update_plan`이 없는 경우

도구 미제공 사실과 bind 미수행을 보고서에 남긴다. Terminal을 실제 수신했다면 연결 결과는 보존하되 전체 hook 절차 PASS로 확대하지 않는다. Bind 또는 capacity-denial attestation이 필요한 작업의 미수행 단계를 문서만으로 정상화하거나 다른 marker로 대체하지 않는다. 설치 cache·사용자 설정 수정은 이 연결 스모크의 일부가 아니다.
