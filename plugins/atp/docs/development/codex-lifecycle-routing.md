---
kind: development
title: Codex subagent lifecycle routing appendix
description: Agent Team Protocol §2.5의 host-neutral lifecycle 의미를 Codex collaboration 도구에 매핑하는 조건부 appendix.
owner: template-maintainer
stability: draft
host_scope: codex
last_reviewed: 2026-08-12
---

# Codex subagent lifecycle routing appendix

이 문서는 Codex host에서만 읽는 조건부 appendix다. 상태·승인·clean retry·phase 종단의 정본은 `agent-team-protocol.md` §2.5이고 capability 판정 정본은 `platform-adapters.md` §3.1이다. 여기서는 Codex collaboration environment가 실제 제공하는 snapshot·notification·control 결과만 매핑한다. 모델 선택 fallback은 §5.7과 `codex-spark-routing.md`의 별도 관심사다.

## 1. 도구 매핑

| 공통 의미 | Codex mapping | 제약 |
|---|---|---|
| event-driven wait / mailbox wake-up | `wait_agent` | timeout은 wake-up일 뿐 activity 또는 failure 증거가 아니다 |
| environment status snapshot | `list_agents` | 응답이 명시한 각 invocation 상태만 권위로 사용한다. `running` snapshot은 계속 `running`이며 같은 snapshot 반복은 전이 없음 |
| mailbox/final-status notification | `wait_agent`가 알린 update + 전달된 agent 결과 | environment가 명시한 final completion과 결과만 `completed`로 취합한다. timeout은 terminal notification이 아니다 |
| 기존 invocation 종결 요청·결과 | `interrupt_agent` | 사용자 승인 후에만 호출한다. environment가 반환한 실제 이전/중단 상태만 기록하며 write isolation은 ownership·disk 상태도 확인한다 |
| read-only result acceptance isolation | ATP-local ledger `result_acceptance_revoked` | 사용자 승인·completion race 뒤 old identity의 future result 수용만 철회한다. Codex terminal event나 write isolation을 합성하지 않는다 |
| clean retry | `spawn_agent` | 반환된 새 agent/invocation identity가 기존 대상과 다를 때만 새 `attempt`로 센다 |
| same-invocation continuation/diagnostic | `followup_task` | clean retry가 아니며 `attempt`를 증가시키지 않는다. 기존 invocation 종결 전 새 logical task를 보내 retry를 흉내 내지 않는다 |
| retry context 범위 | `spawn_agent.fork_turns` + 명시 payload | 고정 turn 수를 정책으로 두지 않는다. 최소 권위 payload가 정본이고 fork 범위는 host/config·민감도에 맞춘다 |

task name suffix나 표시명은 가독성 보조일 뿐 identity 정본이 아니다. `spawn_agent`가 돌려준 새 invocation identity를 report의 새 `id`와 연결하고 `retry_of`에는 직전 report invocation ID를 기록한다.

## 2. Codex 상태·event 정규화

현재 collaboration API에서 권위로 사용할 수 있는 것은 `list_agents`가 실제 반환한 invocation snapshot, `wait_agent`가 알린 mailbox/final-status update, 전달된 최종 agent 결과, `interrupt_agent`가 실제 반환한 중단 결과다. ATP는 응답에 포함된 상태 문자열과 notification 의미만 공통 상태로 정규화하며 존재하지 않는 세부 상태를 보간하지 않는다.

| Codex 관측 | ATP 정규화 |
|---|---|
| `list_agents`가 invocation을 `running`으로 반환 | `running` 유지 |
| `list_agents`가 그 밖의 상태를 명시 | 해당 상태가 공통 계약과 일치할 때만 그대로 정규화; 의미가 불명확하면 `environment_state_unknown` |
| final-status update와 최종 결과 전달 | terminal `completed`; 반환 계약 검증 후 취합 |
| `interrupt_agent`가 현재 turn 중단을 명시 | 해당 attempt의 `interrupted`; partial write·ownership 확인 |
| `wait_agent` timeout | 상태 전이 없음 |
| snapshot 부재, API 오류 또는 의미를 보장할 수 없는 상태 | `environment_state_unknown`; failure/terminal 아님 |

현재 collaboration API 계약은 subagent의 `approval_required` event와 모든 failure 원인·terminal detail을 별도 structured event로 보장하지 않는다. 따라서 appendix는 이를 supported로 선언하지 않는다. 그러나 실제 runtime 응답이 `approval_required`를 명시했다면 relay/control 미지원과 무관하게 그 state를 보존한다. relay 불가 child는 environment provenance·두 identity·concrete `source_ref`와 concern/capability evidence·ledger를 반환하고 `ended_at: null`, termination 생략, mutation 0을 유지하며 report의 `Summary` / `Open Items` / `concerns` narrative만 blocked다. capability가 복구돼 same environment identity continuation이 가능하면 `attempt`와 retry accounting을 바꾸지 않는다. `environment_state_unknown`은 snapshot/status API unavailable/error 또는 의미 불명일 때만 쓰며, observed approval 뒤에도 새 status unavailable/error event가 실제 있어야만 전이한다. agent output·무응답·경과 시간에서 상태를 합성하지 않으며 agent 결과 본문의 업무상 `blocked`도 environment-native blocker가 아니다.

progress/message/tool output은 사용자 진행 설명에 사용할 수 있지만 lifecycle 전이를 만들지 않는다. 반대로 progress/heartbeat가 없거나 같은 `running` snapshot이 반복되어도 stall·failed·interrupted로 바꾸지 않는다.

## 3. 승인 후 종결과 clean retry

1. 명시적 failure/interruption/environment blocker 뒤 사용자가 retry를 승인하면, 먼저 `list_agents` 또는 새 mailbox update로 completion race를 재확인한다. old invocation이 이미 완료됐으면 retry를 취소하고 기존 결과를 검토한다.
2. environment가 여전히 실행 중이고 termination control을 제공하면 `interrupt_agent`를 먼저 호출한다. environment가 반환한 event와 read/write 성질을 확인한다. termination control이 없더라도 read-only임이 확정된 old identity는 ATP-local result acceptance isolation을 사용할 수 있지만 write-capable scope에는 사용할 수 없다.
3. read-only recovery가 계속되면 같은 old report/environment identity의 11개 공통 필드와 `scope`/`rationale`/`source_ref`를 가진 `result_acceptance_revoked` advisor ledger event를 기록한다. 이 event 뒤에만 새 identity를 spawn한다.
4. write-capable invocation은 old ownership 회수와 partial write 분류가 끝나기 전 `spawn_agent`를 호출하지 않는다. Codex가 termination/isolation을 확인할 수 없으면 동일 write scope의 새 spawn은 금지한다.
5. `spawn_agent`에는 목표, 권위 파일, 확정 계약, write scope, 보존할 partial, 필수 산출물, 검증·반환 형식을 명시한다. `fork_turns`는 필요한 최소 범위를 선택하되 transcript 상속에 의존해 권위 계약을 생략하지 않는다.
6. 새 identity를 확인한 뒤에만 `attempt`를 증가시키고 `retry_of`를 연결한다. `followup_task`는 이 단계를 대체하지 않는다.

## 4. late completion과 invocation authority

Codex environment가 old invocation의 final completion/result를 전달하면 먼저 environment `completed`로 기록한다. 같은 old identity의 `result_acceptance_revoked` 또는 write ownership 회수가 선행한 경우에만 advisor가 `authority_kind`와 그 선행 anchor의 `authority_ref`를 phase ledger에 연결해 report `termination: late_completion` disposition을 기록한다. 선행 authority 철회가 없으면 정상 completion race 후보이며 `late_completion`으로 바꾸지 않는다.

read-only late result와 write ownership 회수 뒤 disk write가 없는 late result는 quarantine-only이며 자동 merge·취합·성공 판정·ownership pause를 하지 않는다. old invocation의 실제 late disk write가 보인 경우에만 affected scope와 dependency closure를 persisted pause하고 diff/ownership 충돌을 중재한다. write isolation을 확인할 수 없으면 새 owner의 동일 scope 작업을 진행하지 않고 protocol §2.5의 Tier B 직접 수행 또는 blocked 종단을 적용한다.

## 5. 유한 clean retry와 phase 종단

명시적 terminal failure 뒤 logical task별 clean retry 상한과 retry payload의 fork 범위는 host/config가 정할 수 있다. wait timeout, 경과 시간, progress 부재, 동일 snapshot 조회 횟수는 retry 한도를 소비하거나 phase fallback을 열지 않는다.

승인된 clean retry도 environment가 명시한 같은 terminal failure로 끝나거나 retry 상한이 소진되면 protocol §2.5의 phase별 종단으로 수렴한다. 특히 code 변경 검증은 Tier B 직접 실행 또는 blocked이며 lifecycle 장애를 이유로 skip할 수 없다.

## 6. Codex 실행 체크리스트

- [ ] 상태·terminal event가 collaboration environment의 실제 snapshot/notification에서 관측됐는가?
- [ ] `running`을 그대로 유지하고 timeout·경과 시간·progress/heartbeat 부재·동일 snapshot으로 전이시키지 않았는가?
- [ ] 미지원 approval/failure detail을 합성하지 않고 `environment_state_unknown`으로 남겼는가?
- [ ] 실제 관측된 `approval_required`는 relay/control 미지원이어도 보존하고, status unavailable/error와 구분했는가?
- [ ] 승인 전 `interrupt_agent`, `spawn_agent`, phase fallback 실행이 0건인가?
- [ ] `followup_task`를 clean retry로 세거나 `attempt`를 올리지 않았는가?
- [ ] read-only retry는 same-identity `result_acceptance_revoked`를 새 spawn 전에 기록했는가?
- [ ] write retry 전 termination/isolation, partial diff, ownership 회수를 확인했는가?
- [ ] late completion은 선행 authority 철회와 identity/ref가 일치하고, late disk write가 없으면 quarantine-only인가?
- [ ] 명시적 terminal failure 뒤 승인된 retry 상한 소진 시 phase별 종단으로 수렴했는가?
