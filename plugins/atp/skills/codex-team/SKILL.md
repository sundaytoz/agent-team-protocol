---
name: codex-team
description: Codex에서 ATP가 subagent를 spawn, delegate, steer, collect하기 전에 사용하는 orchestration skill. 배포 capability gate를 적용하고, atp-codex-hooks add-on의 exact hook marker가 있는 세션에서는 제한된 동시 슬롯을 queue→wait→refill하는 hook-guarded bounded pool로 team execution을 실행한다.
---

# Codex team orchestration

이 skill은 Codex host 전용이다. ATP가 한 명 이상의 subagent를 사용하려면 첫 collaboration action 전에 전체 `SKILL.md`를 읽는다. 공통 lifecycle·report authority는 `../../docs/development/agent-team-protocol.md`를 따르되, Codex scheduling 절차는 이 skill만으로 실행한다. Runtime task가 scheduling 방법을 알아내기 위해 evidence나 maintainer appendix를 다시 읽거나 capability probe를 만들지 않는다.

## 1. 실행 gate

1. 아래 §7의 배포 profile을 먼저 적용한다. Profile은 **선언된 scope 안에서** `team_execution_enabled: true`이며, scope 안에 있는지는 오직 아래 exact hook marker의 존재로 판정한다.
2. Hook은 base `atp` 번들에 없다. 옵트인 add-on **`atp-codex-hooks`**(`plugins/atp-codex-hooks/hooks/hooks.json` + `hooks/codex_pool_hook.py`)를 설치하고 TUI에서 hook trust를 부여한 세션에서만 `SessionStart` hook이 marker를 root context에 넣는다.
3. **Marker가 현재 root context에 있으면** 이 세션은 scope 안이다. `host_managed_subagent_orchestration: supported`, `selected_mode: host_managed_subagent_orchestration`으로 §2~§6의 hook-guarded bounded pool을 실행한다. 이것이 Codex의 정상 team execution 경로다.
4. **Marker가 없거나 schema/hash가 다르면** scope 밖이다 — add-on 미설치, hook untrusted, disabled, policy-excluded, dependency-missing(예: Windows `py -3` 미검증), source/install mismatch 중 어느 것이든 같게 취급한다. child spawn은 0이며 `$atp:task`는 `skip: no-codex-hooks`를 기록하고 `general_task`는 `tier_b_sequential`, `explicit_subagent_required`는 `blocked_explicit_independence`로 차단 없이 계속한다(graphify add-on의 `skip: no-graphify`와 같은 형태). Marker 부재는 오류가 아니라 기본 소비자 상태다.
5. 어느 경로에서도 사용자 전역 설정, 설치된 사용자 plugin cache, hooks와 소비 프로젝트를 변경하지 않으며, marker를 prompt에 복사·합성해 scope 안으로 위장하지 않는다.

```text
ATP_HOOK_GUARD_READY schema=1 hooks_sha256=d7005171cb3d60c911d9310733b9db445f184b40024e57e870a64d2a62fa8bd7 runner_sha256=22b938537cce01251fc00d3c4e358018dbf2a656e2edd4ceded59b9d7ac621b0
```

Marker는 add-on `atp-codex-hooks`가 번들한 `SessionStart` hook만 만든다. 해시는 add-on 설치본의 `hooks/hooks.json`과 `hooks/codex_pool_hook.py` 바이트에 대한 SHA-256이다. Prompt에 복사되거나 hook trust 우회 없이 합성된 문자열은 marker가 아니다. 선언 scope는 Unix + `python3` on PATH + add-on 설치 + hook trust다. Windows `py -3`는 미검증이라 scope 밖이며, 그 surface에서는 marker가 생성되지 않아 같은 fail-closed 경로로 닫힌다.

## 2. Bounded pool 상태

한 scheduler만 다음 상태를 소유한다.

- `pending`: 아직 spawn되지 않은 logical task의 FIFO queue
- `running`: environment identity → logical task/report invocation identity map
- `terminal`: 검증 가능한 terminal result map
- `rejected_capacity`: capacity 때문에 아직 실행되지 못한 task; failure나 retry가 아니라 `pending`으로 되돌릴 대상
- `requested`: 최초 logical task 집합; 실행 중 추가하거나 삭제하지 않는다

Root가 전체 queue owner인 flat pool을 기본으로 한다. Subagent가 다시 subagent를 호출해야 하면 그 subagent를 유일한 nested pool owner로 지정하고 root는 같은 시각에 별도 sibling fan-out을 만들지 않는다. Pool ownership을 받지 않은 child는 다시 spawn하지 않는다.

## 3. Slot budget와 dispatch

- 사용자 설정을 변경하거나 정상 task에서 limit probe를 실행하지 않는다.
- Host가 concrete concurrency budget을 제공하면 primary와 이미 active인 ancestor/child를 제외한 free slots만 사용한다.
- Budget을 알 수 없는 0.149.1-default candidate에서는 root direct pool은 최대 3 spawned threads, `root → pool-owner child → workers` 구조는 worker 최대 2개로 시작한다.
- Pending task를 bounded result contract로 만들고 report identity를 spawn 전에 할당한다. Nested pool owner에는 자신의 worker queue, 최대 active worker 수와 terminal-only 반환 계약을 명시한다.
- Root pool은 시작 전에 stable pool id, requested task total과 logical task별 random token을 확정한다. `task_name`은 `atp_pool_<pool>_<index>of<total>_<token>` 형식만 사용한다. `<pool>`은 6~16자의 소문자 영숫자, `<token>`은 8~32자의 소문자 hex다.
- 각 child prompt는 작업 시작 전 `update_plan`을 한 번 호출해 완료 step을 `ATP_POOL_BIND <pool> <index>/<total> <token>`으로 기록하고, terminal 첫 줄에 `ATP_POOL_RESULT <pool> <index>/<total> <token>`을 쓴 뒤 bounded result를 반환하도록 요구한다. Bind hook은 `SubagentStart.agent_id`와 token을 approval 전에 연결하고, terminal hook은 result token과 spawn response identity를 다시 교차 검증한다.
- Free slot 수만큼 `spawn_agent`를 호출해 `running`을 채운다. `fork_turns: "all"`은 pool owner가 원 요청과 authority context 전체를 실제로 필요로 할 때만 사용하고, leaf worker는 기본 `fork_turns: "none"`을 사용한다.
- Host가 `agent thread limit reached`를 반환하면 해당 task는 spawn된 것이 아니다. `spawn_calls`에는 attempted/denied를 분리해 기록하고 logical task를 `pending` 선두로 되돌린 뒤 pool을 saturated로 표시한다. 이를 task failure, clean retry, recovery action으로 세지 않는다.
- Codex CLI 0.149.1은 실패한 local function tool 호출에 `PostToolUse`를 내보내지 않는다. 따라서 denial을 관측한 scheduler는 즉시 `update_plan`을 한 번 호출해 완료 step을 `ATP_POOL_DENIED <pool> <index>/<total> <token>`으로 기록한다. Hook은 durable manifest와 미해소 spawn attempt가 실제로 있을 때만 이 marker를 수용하고, 이미 accepted/terminal인 task의 denial 주장은 거부한다. 이 marker는 parent가 tool 반환값에서 이미 관측한 authoritative error를 hook ledger로 재진술하는 채널이며, 관측하지 못한 denial을 합성하는 수단이 아니다.
- Capacity 외 spawn 오류는 합성하지 않는다. 실제 environment error를 보존하고 §6의 blocked/user-decision 경로로 간다.

## 4. Queue → wait → refill loop

다음 loop를 `pending`과 `running`이 모두 빌 때까지 반복한다.

1. Free slot이 있고 `pending`이 있으면 §3에 따라 pool을 채운다.
2. `running`이 있으면 `wait_agent`를 한 번 호출해 mailbox event를 기다린다. `list_agents` polling, fixed sleep, shell polling과 no-op keepalive를 사용하지 않는다. Hook이 wait 전후 또는 root Stop continuation에 `ATP_POOL_TERMINAL_DELTA`를 전달하면 같은 iteration의 terminal delivery 후보로 함께 검증한다.
3. 전달된 event와 hook delta를 preallocated logical identity에 연결한다.
   - `MESSAGE` 또는 progress: 해당 invocation은 `running`이다. terminal/result로 세지 않고 다시 wait한다.
   - `FINAL_ANSWER`, 명시적 completed terminal 또는 token/hash가 맞는 hook terminal delta: result contract를 검증한 뒤 `running`에서 제거하고 `terminal`에 한 번만 넣는다.
   - 명시적 failed/interrupted/approval-required/cancellation: §6으로 전달한다. Silence나 wait timeout은 이 상태를 합성하지 않는다.
4. 하나 이상의 terminal로 slot이 해제되면 즉시 §3으로 돌아가 `pending`을 refill한다.
5. Wake에 terminal이 없으면 spawn이나 completion을 만들지 않고 `running` 대상에 다시 wait한다.
6. `running`이 비었는데 `pending`이 남고 모든 spawn이 capacity error라면 기다릴 owner가 없으므로 무한 loop를 만들지 않는다. 실제 capacity state와 pending task를 보존해 blocked로 반환한다.

Wait 호출은 pool이 비지 않은 동안 terminal/progress/control event를 받기 위한 join이다. 짧은 timeout을 반복하거나 상태가 바뀌지 않았는데 `list_agents`로 재확인하는 polling loop로 바꾸지 않는다.

Root가 final을 시도할 때 bundled `Stop` hook은 durable manifest의 requested/pending/running/terminal/collected를 검사한다. Incomplete이면 `ATP_POOL_CONTINUE`로 같은 root turn을 continuation하고, complete일 때만 allow한다. 같은 ledger revision에서 event-driven progress가 반복해서 없으면 supported completion을 합성하지 않고 explicit blocked disposition으로 끝낸다.

## 5. Completion barrier와 계측

Scheduler completion 조건은 다음 두 식을 동시에 만족하는 경우뿐이다.

```text
pending == 0 && running == 0
requested_tasks == accepted_spawns == terminal_deliveries == collected_results
```

Capacity-denied attempt는 `accepted_spawns`에 포함하지 않는다. 같은 logical task가 나중에 slot을 얻어 spawn되면 environment identity는 한 개만 결과 집합에 연결한다. Duplicate terminal은 한 번만 소비한다.

Report에는 최소한 다음을 구분해 기록한다.

- requested logical tasks
- spawn attempts / accepted spawns / capacity denials
- maximum observed running set
- nonterminal updates / terminal deliveries / collected results
- pool wait calls / list calls / interrupt calls
- pending refill 횟수와 최종 미실행 task

모든 요청 agent/result를 검증·취합하기 전 report/session completion, `ended_at`, 사용자 final을 만들지 않는다. 미래 transcript ordinal이나 관측하지 못한 telemetry를 예측하지 않으며 unknown은 `null`로 둔다.

## 6. Steering, approval, cancellation과 recovery

- User steering은 현재 queue와 running identity에 적용하고 새 logical task를 암묵적으로 추가하지 않는다.
- Maintainer steering/cancellation smoke는 각각 `ATP_POOL_STEER <pool> <index>`와 `ATP_POOL_CANCEL <pool>` marker를 사용한다. Queue acceptance가 아니라 `UserPromptSubmit`의 `ATP_POOL_CONTROL_DELIVERED`가 있어야 delivered로 센다. Delivered control을 existing identity에 `send_message`/`followup_task` 또는 `interrupt_agent`로 적용하기 전에는 pending refill을 하지 않는다.
- Approval-required는 해당 invocation과 write ownership을 유지한 채 사용자 결정으로 전달한다. 다른 slot의 terminal/result는 계속 보존한다.
- `PermissionRequest` hook은 audit만 하고 임의 승인·거부하지 않는다. Approval PASS는 실제 interactive decision 뒤 같은 child identity의 terminal `SubagentStop`이 있어야 한다.
- User cancellation은 pending dispatch를 중단하고 host가 제공한 actual cancellation/interrupt 계약을 따른다. Queue에 cancel 문자열을 넣은 것만으로 PASS하지 않으며, terminal confirmation 없이 running을 completed/failed로 합성하지 않는다.
- Capacity backpressure는 recovery가 아니다. Automatic retry counter, fallback과 authority mutation을 만들지 않는다.
- 실제 failed/interrupted 뒤의 retry, interrupt, fallback, result-acceptance 또는 write-ownership 변경은 공통 lifecycle의 사용자 승인 계약을 따른다.

## 7. 배포된 capability profile

현재 배포 판정은 다음과 같다(2026-09-08, ADR-0025).

```yaml
formal_adapter_enabled: false
manual_wait_polling_supported: false
host_managed_subagent_orchestration: supported
team_execution_enabled: true
execution_scope: hook_guarded_bounded_pool
scope_gate: atp_hook_guard_ready_marker
```

`supported`/`true`는 **scope-gated**다 — §1의 exact marker가 있는 세션에만 적용되고, marker가 없는 세션은 `unsupported`/`false`로 동작한다. Codex built-in의 staggered 2-agent barrier는 `spawn_calls=2`, `terminal_deliveries=1`로 실패했으므로(2026-08-26) all-results barrier는 built-in wait가 아니라 §2~§6의 hook-guarded bounded pool이 제공한다. 승격 근거는 add-on 빌드에서 재실행한 2026-09-08 qualification(`tests/runtime-behavior/evidence/codex-cli-0.149.1-hook-guarded-20260908.json`)이다: terminal-only 1-agent, delayed terminal 1-agent(wait 2회, 합성 completion 0), staggered 2-agent all-results, capacity-denial refill 5-agent(attempts 9 / accepted 5 / denials 4 전건 `parent_marker` attested / terminal·collected 5) 전부 pass, list/interrupt 0, root Stop은 전원 collected 뒤에만 allow.

### 7.1 Candidate 축별 상태

Qualification 판정은 단일 boolean이 아니라 서로 독립인 4개 축이다. 축 정의와 smoke 매핑은
`../../../../docs/backlog/codex-cli-hook-guarded-bounded-pool.md` §Phase 3가 정본이다.
`../../docs/development/platform-adapters.md` §3.2가 명시하듯 capability gap은 축별로 판정하며,
control-surface gap을 all-results barrier 실패로 확대 해석하지 않는다.

| 축 | 현재 값 | 근거 |
|---|---|---|
| A. all-results barrier | PASS | 2026-08-31 재실행에서 requested/attempts/accepted/terminal/collected `5/6/5/5/5`, hook ledger capacity denial 1건(`attested_by: parent_marker`), list/interrupt 0, source/install parity 일치 |
| B. in-flight control delivery | unknown | T4/T6는 비대화형 `codex exec`에서만 측정됨 — 통과 가능한 interactive surface 미측정 |
| C. approval continuation | supported | T5 PASS — 실제 interactive decision 뒤 같은 child identity가 terminal까지 continuation |
| D. packaging and runner scope | 선언 완료 — 옵트인 add-on `atp-codex-hooks`, Unix `python3`, hook trust (2026-09-08) | 번들 hook은 TUI에서 1회 "hooks can run outside the sandbox" 신뢰를 요구하고, trust는 command 문자열에만 묶여 이후 runner 변경을 무확인 실행한다. 기능을 켜는 사람만 그 동의를 지도록 base 번들에서 제거하고 add-on으로 옮겼다. Windows `py -3`는 scope 밖(marker 미생성 → fail-closed). `allow_managed_hooks_only` 측정 결과는 appendix §8.6 |

A는 필수 축이고 B/C/D는 서로 독립이다. A와 D가 충족돼 선언된 scope 안에서 team execution을
열었다(ADR-0025). B는 `unknown`으로 남으며, 이는 **실행 중 steering/취소를 요구하는 요청만**
blocked/user-decision 경로로 보낸다는 뜻이다 — ATP 정상 흐름(spawn → wait → collect)은 mid-flight
steering을 요구하지 않고, 사용자 취소는 host 인터럽트가 상위 계층에서 처리한다.

일반 소비 task는 이 profile을 실행 중 임의로 올리거나 내리지 않는다. scope 판정은 marker 존재
하나로만 한다. B와 C는 그 결정과 독립적으로 각자의 축 값으로 기록한다.
