---
kind: development
title: Codex subagent lifecycle routing appendix
description: Agent Team Protocol §2.5의 host-neutral lifecycle 의미를 Codex collaboration 도구에 매핑하는 조건부 appendix.
owner: template-maintainer
stability: draft
last_reviewed: 2026-07-20
---

# Codex subagent lifecycle routing appendix

이 문서는 Codex host에서만 읽는 조건부 appendix다. 상태·승인·clean retry·phase 종단의 정본은 `agent-team-protocol.md` §2.5이고 capability 판정 정본은 `platform-adapters.md` §3.1이다. 여기서는 Codex 도구 매핑과 calibration만 정의한다. 모델 선택 fallback은 §5.7과 `codex-spark-routing.md`의 별도 관심사다.

## 1. 도구 매핑

| 공통 의미 | Codex mapping | 제약 |
|---|---|---|
| event-driven wait / mailbox wake-up | `wait_agent` | timeout은 wake-up일 뿐 activity 또는 failure 증거가 아니다 |
| 제한적 authoritative status 재확인 | `list_agents` | 상태 snapshot만 사용한다. 같은 snapshot의 반복 조회를 새 증거로 세지 않는다 |
| 기존 invocation 종결 요청 | `interrupt_agent` | 사용자 승인 후에만 호출하며, 반환 상태와 후속 status로 termination/isolation을 확인한다 |
| clean retry | `spawn_agent` | 반환된 새 agent/invocation identity가 기존 대상과 다를 때만 새 `attempt`로 센다 |
| same-invocation continuation/diagnostic | `followup_task` | clean retry가 아니며 `attempt`를 증가시키지 않는다. silent-start 대상에는 종결 전 새 작업을 보내지 않는다 |
| retry context 범위 | `spawn_agent.fork_turns` + 명시 payload | 고정 turn 수를 정책으로 두지 않는다. 최소 권위 payload가 정본이고 fork 범위는 host/config·민감도에 맞춘다 |

task name suffix나 표시명은 가독성 보조일 뿐 identity 정본이 아니다. `spawn_agent`가 돌려준 새 invocation identity를 report의 새 `id`와 연결하고 `retry_of`에는 직전 report invocation ID를 기록한다.

## 2. first observable activity 판정

Codex에서 공통 activity로 인정하는 것은 orchestrator에게 전달된 subagent output, 명시적 progress/message, tool call start/result, 그리고 `list_agents` 또는 mailbox가 드러낸 terminal/blocked 상태다. UI에만 보이는 애니메이션, reasoning/token 내부 이벤트, timeout 종료 자체는 인정하지 않는다.

`wait_agent`가 새 mailbox update를 알리면 해당 update를 확인해 실제 activity 종류를 분류한다. update 없이 timeout되면 configured budget과 capability profile을 대조하고, 필요할 때 `list_agents`로 authoritative status를 configured finite `unchanged_check_budget` 안에서만 재확인한다. 확인 횟수와 간격은 calibration 대상이며 같은 snapshot의 반복은 새 증거로 세지 않는다. queued/blocked/tool-start가 관측되면 silent-start 의심을 해제하거나 해당 상태 규칙으로 이동한다.

progress 노출 여부가 불명확하고 `list_agents` snapshot도 실행 상태 이상을 보장하지 못하면 `progress_unobservable`로 보고한다. 이때 silent stall을 확정하거나 자동 `interrupt_agent`를 호출하지 않는다.

## 3. 승인 후 종결과 clean retry

1. 승인 직후 `list_agents` 또는 새 mailbox update로 race를 재확인한다. old invocation이 이미 완료됐으면 retry를 취소하고 기존 결과를 검토한다.
2. 여전히 실행 중이면 `interrupt_agent`를 호출한다. read-only scope는 이후 결과 수용권을 철회하고, write-capable scope는 status·ownership·disk diff로 termination/isolation을 확인한다.
3. write-capable invocation은 old ownership 회수와 partial write 분류가 끝나기 전 `spawn_agent`를 호출하지 않는다. Codex가 termination/isolation을 확인할 수 없으면 동일 write scope의 새 spawn은 금지한다.
4. `spawn_agent`에는 목표, 권위 파일, 확정 계약, write scope, 보존할 partial, 필수 산출물, 검증·반환 형식을 명시한다. `fork_turns`는 필요한 최소 범위를 선택하되 transcript 상속에 의존해 권위 계약을 생략하지 않는다.
5. 새 identity를 확인한 뒤에만 `attempt`를 증가시키고 `retry_of`를 연결한다. `followup_task`는 이 단계를 대체하지 않는다.

## 4. late completion과 ownership

`interrupt_agent` 및 ownership revoke 뒤 old invocation의 결과가 도착하면 report에서 `termination: late_completion`으로 격리한다. 자동 merge나 성공 판정을 하지 않는다. old invocation의 늦은 disk write가 보이면 새 invocation에 추가 작업을 보내기 전에 중단하고 diff와 ownership 충돌을 판정한다.

read-only 결과는 비충돌 참고자료로만 보존할 수 있다. write scope가 겹치거나 isolation을 확인할 수 없으면 새 owner의 동일 scope 작업을 진행하지 않고 protocol §2.5의 Tier B 직접 수행 또는 blocked 종단을 적용한다.

## 5. 유한 budget과 calibration

다음 값은 Codex/ATP config에서 유한하게 설정하고 CLI 버전·실행 환경별로 calibration한다.

- invocation accepted부터 첫 observable activity까지의 silence budget
- 변화 없는 status를 재확인할 수 있는 횟수와 확인 간격
- logical task별 clean retry 상한
- retry payload에 포함할 fork 범위 또는 fork 비사용 기준

기본값을 문서 상수로 고정하지 않는다. 관측 표본에는 CLI/runtime 버전, phase와 workload 유형, accepted 시각, first observable activity 시각, activity 종류, queued/blocked 여부를 남기고 충분한 표본의 지연 분포와 오탐 사례로 config를 조정한다. 표본이 부족하면 보수적인 사용자 결정 경로를 우선한다.

budget 소진 후에는 polling이나 동일 target follow-up을 반복하지 않는다. optional advisor, required artifact, implementation, verification, destructive action, closing docs/retro 각각 protocol §2.5의 종단표로 이동한다. 특히 code 변경 검증은 Tier B 직접 실행 또는 blocked이며 skip할 수 없다.

## 6. Codex 실행 체크리스트

- [ ] activity로 센 신호가 정상 collaboration API에서 실제 관측됐는가?
- [ ] timeout을 단독 실패 증거로 사용하지 않았는가?
- [ ] 승인 전 `interrupt_agent`, `spawn_agent`, phase fallback 실행이 0건인가?
- [ ] `followup_task`를 clean retry로 세거나 `attempt`를 올리지 않았는가?
- [ ] write retry 전 termination/isolation, partial diff, ownership 회수를 확인했는가?
- [ ] late completion을 자동 merge·성공 판정하지 않았는가?
- [ ] 상태 확인·retry budget 소진 뒤 phase별 종단으로 수렴했는가?
