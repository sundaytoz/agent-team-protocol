---
name: claude-code-team
description: Claude Code에서 ATP가 subagent를 spawn, steer, collect하기 전에 반드시 사용하는 orchestration skill. 검증된 Claude Code capability profile을 적용하고, turn-end await(spawn → 툴 호출 없이 턴 종료 → task-notification 재기동)를 all-results barrier로 사용하며 no-op 틱·transcript 폴링 등 manual liveness polling을 금지한다.
---

# Claude Code team orchestration

이 skill은 Claude Code host 전용이다. ATP task가 Claude Code에서 한 명 이상의 subagent를 호출하려면 첫 collaboration action 전에 이 전체 `SKILL.md`를 읽고 아래 계약을 적용한다. 공통 lifecycle·report authority는 `${CLAUDE_PLUGIN_ROOT}/docs/development/agent-team-protocol.md`, 검증된 Claude Code capability profile과 event mapping은 `${CLAUDE_PLUGIN_ROOT}/docs/development/claude-code-lifecycle-routing.md`가 정본이다.

## 1. 적용 시점

- ATP가 Claude Code에서 subagent를 spawn, steer, collect하려는 모든 실행에 적용한다 — top-level orchestrator와 nested advisor(worker를 spawn하는 research/implementation advisor) 모두.
- Skill 선택과 전문 로드는 첫 `Agent` 호출, `SendMessage` steering, `TaskStop`, 결과 취합보다 먼저 끝낸다.
- Nested advisor는 `Skill` 툴이 없다 — orchestrator는 worker를 spawn할 advisor의 입력 payload에 이 skill의 경로 `${CLAUDE_PLUGIN_ROOT}/skills/claude-code-team/SKILL.md`를 명시 주입하고, advisor는 첫 worker spawn 전에 그 경로를 `Read`로 전문 로드한다. 경로 주입이 누락됐어도 advisor는 `platform-adapters.md` §7.1 → Claude Code appendix 경유로 같은 파일을 찾아 읽는다.
- 소비 프로젝트의 매 task에서는 capability 확인용 child, timeout probe, liveness probe, source/install parity 검사를 실행하지 않는다. 릴리스에 포함된 capability profile을 사용한다.

## 2. 정상 dispatch 계약 — turn-end await

Claude Code의 `Agent` 툴은 async다. Spawn 호출은 `Async agent launched` ack와 `agentId`를 즉시 반환하고, child의 terminal result는 harness가 `<task-notification>`(inline `<result>` + `status`)으로 자동 주입한다. Harness는 **live background children을 가진 agent의 턴 종료를 완료로 처리하지 않고 모델 호출 0으로 suspend했다가 child terminal마다 재기동**한다. 이것이 managed all-results barrier이며, nested advisor에도 동일하게 적용된다.

1. 배치의 child 전원을 **한 assistant 메시지의 병렬 `Agent` 호출**로 dispatch한다(advisor 호출당 worker 동시 상한 등 공통 호출 불변은 protocol §2 그대로). 각 child prompt에는 다음을 명시한다.
   - 정상 경로에서 intermediate message를 보내지 않는다.
   - 완료 시 결과 계약을 충족한 terminal result 한 건을 최종 텍스트로 반환한다.
2. Spawn ack 수신 후 실제 준비 작업(ledger 기록, 다음 배치 준비 등)이 남았으면 수행한다. 대기만 남았으면 **짧은 상태 텍스트 한 줄로 턴을 종료**한다. 대기 목적의 툴 호출은 0건이다.
3. `<task-notification>` wake마다: 해당 `task-id`의 `status`/`<result>`를 수집해 dispatch mapping의 `report_invocation_id`에 연결하고, 수집 가능한 incremental 처리를 수행한다. 미수집 child가 남았고 실행할 준비 작업이 없으면 다시 짧은 상태 텍스트로 턴을 종료한다.
4. 같은 `task-id`의 재통지는 collected set으로 dedup해 한 번만 수집한다. 전달된 nonterminal update는 `running`일 뿐 terminal delivery나 completion authority가 아니다.
5. **Terminal delivery의 정의**: notification의 명시적 terminal disposition — `completed | failed | interrupted` — 전부가 terminal delivery이며 barrier 계수에 포함된다(승인된 recovery로 `TaskStop`된 child의 `interrupted` 포함). 그중 `completed` + inline `<result>`만 정상 수집 결과다. `failed`가 전달돼도 남은 live child의 대기·수집을 계속하고, recovery 검토는 전건 terminal 후 반환된 곳(orchestrator/사용자)에서 시작한다 — batch 반환 전에 retry/interrupt/fallback을 시작하지 않는다.
6. 모든 요청 child의 terminal delivery를 수신하고 결과 계약을 검증·취합하기 전에는 report invocation/session completion, `ended_at`, 사용자/parent 최종 응답을 만들지 않는다. 일부 child가 `failed`로 끝났다면 barrier는 열린 것이며, 최종 산출에 실패 건의 §2.5 disposition(`awaiting_user_decision` 등)을 포함해 반환한다 — 교착이 아니다.

**Turn-end 의미 경계**: live child가 0인 상태의 턴 종료는 그 agent의 최종 반환이다. 대기용 턴 종료 텍스트는 `WAITING <수집수>/<요청수>` 형태처럼 최종 산출로 오인될 수 없는 표식을 갖고, 최종 보고·구조화 반환 payload를 담지 않는다. 마지막 child 수집 뒤에는 반드시 반환 계약(구조화 payload 포함)을 완성한 뒤 종료한다 — 종료 직전 self-check: live child 0 + 전건 terminal + payload 완성. 모든 child가 이미 terminal인데 미수집 통지가 남은 race는 큐에 보존된 notification이 재기동시키므로 유실되지 않는다.

**Wake가 오지 않는 경우**: 대체 행동은 없음이 정답이다. Suspend는 모델 호출 0의 무비용 상태라 폴링과 달리 해악이 없고, 경과 시간·무소식은 상태 전이나 자가 회복(polling/probe/interrupt)의 근거가 아니다(protocol §2.5). Hang 의심의 처분 권한은 사용자에게 있다 — 사용자 steering/interrupt가 suspend를 언제든 선점한다.

## 3. 금지 — manual liveness polling

다음은 정상 경로에서 0건이어야 한다. 하나라도 발생하면 managed 계약 위반이다.

- 대기 목적의 no-op 도구 호출: `echo`/`sleep` 틱, 의미 없는 Read/Bash keepalive
- `~/.claude/projects/**`의 세션/subagent transcript(jsonl) 읽기, `tasks/*.output` 읽기 — notification이 `output_file` 경로를 광고하더라도 읽지 않는다. Inline `<result>`가 잘려 전문이 필요하면 같은 `agentId`에 `SendMessage`로 재전송을 요청한다(continuation — retry 아님). `SendMessage`가 툴셋에 없는 nested advisor는 재요청하지 않고 부분 결과 + `truncated_result` concern으로 반환한다 — 전문 획득은 `SendMessage`를 가진 상위(orchestrator) 몫
- Child transcript의 파일 크기·라인 수·mtime을 liveness/완료 신호로 폴링, 동일 snapshot 반복을 완료로 해석
- `ListAgents`·`/tasks` 조회를 정상 경로 scheduling에 사용 — 횟수 무관 0건이 fixture다. 유일한 예외는 승인된 recovery의 completion race 재확인 단발 조회이며 그 경우에도 `list_calls`에 계수한다
- `TaskOutput` 의존 — nested subagent 툴셋에 존재하지 않는다
- Pending child 결과의 예측·합성 — notification 없이는 결과를 모른다

## 4. 결과 barrier와 계측

- Dispatch마다 spawn ack의 `agentId`를 report invocation의 exact field `environment_invocation_id`에 기록한다. 표시명 alias로 대체하지 않는다. Child의 `report_invocation_id`는 protocol §2.5·task SKILL 규칙대로 spawn 전에 호출 주체가 할당해 입력에 주입한다.
- 요청한 agent 전원의 terminal delivery(정상+비정상)가 있어야 barrier가 열린다. 전건 `completed`인 정상 fixture는 `terminal_deliveries == collected_results == requested_agents == spawn_calls`. `failed`가 있으면 `terminal_deliveries == requested_agents == spawn_calls`는 유지하되 `collected_results`는 `completed` 수이며, 차이 사유를 `details`에 기록한다.
- 정상 managed 경로에서 `manual_wait_calls: 0`(대기 목적 도구 호출 수 — no-op 틱·transcript 폴링·liveness 조회 포함), `list_calls: 0`, `interrupt_calls: 0`, `semantic_recovery_actions: 0`이어야 한다.
- **Managed mode의 scheduling ledger는 두 종류 row만 기록한다**: preflight의 `await_capability_checked` 1회 + 종료 시 aggregate `measurement`. Per-wake row는 만들지 않는다 — `await_registered`/`wake_batch`는 formal `environment_subscription` 전용이다. Wake·terminal 사건별 기록은 lifecycle ledger(protocol §2.5)의 몫이다. Row envelope은 `recorded_at`, `await_id`(managed에서 `null`), `owner_report_invocation_id`, `event`, concrete `source_ref`, `details`의 six-field를 유지한다.
- Capability row의 `details`에는 exact keys와 values `formal_adapter_enabled: false`, `manual_wait_polling_supported: false`, `host_managed_subagent_orchestration: supported`, `team_execution_enabled: true`, `selected_mode: host_managed_subagent_orchestration`을 모두 기록하고 `profile_ref`는 exact string `claude-code-lifecycle-routing.md#current-claude-code-orchestration-capability`로 남긴다.
- 알 수 없는 telemetry는 `null`로 기록하고 0으로 합성하지 않는다.

## 5. lifecycle과 recovery

- Notification의 명시적 terminal disposition(`completed | failed | interrupted`)이 terminal delivery다. `completed` + inline `<result>`만 정상 수집 결과다. `failed`가 관측되면 lifecycle ledger에 기록하고 남은 child 수집을 계속하며, recovery(사용자 승인·독립 invocation identity·retry cap — protocol §2.5)는 batch 반환 후 approval authority가 있는 곳(orchestrator→사용자)에서 시작한다. Nested advisor는 사용자에게 직접 묻지 않는다 — disposition `awaiting_user_decision`으로 반환한다.
- `SendMessage`로 같은 agent에 보내는 follow-up은 steering/continuation이며 clean retry가 아니다(`SendMessage` 보유 주체에 한함). Retry는 새 `agentId`와 `retry_of`를 가진다.
- `TaskStop`은 승인된 recovery에서만 사용하고, 명시적으로 확인된 경우에만 `interrupted`로 기록한다.
- Capability error가 실제 관측되면 automatic polling, retry, interrupt, fallback 또는 automatic Tier B 전환으로 보상하지 않는다. 마지막 environment-authoritative state와 authority를 보존하고 요청 의도에 맞는 blocked/user-decision 경로를 사용한다.

## 6. authority 경계와 종료 순서

Claude Code host는 child execution, notification routing, suspend/wake scheduling과 terminal delivery를 소유한다. ATP는 logical task/DAG, result contract validation과 integration, approval/recovery decision, result acceptance, write ownership, report와 session lifecycle을 소유한다.

종료 순서는 공통 11단계다: 모든 요청 subagent terminal result 수신 → 결과 계약 검증·통합 → verification → retrospective → report 반영 → report 재스테이징 → staged 재검증 → 요청 범위 mutation/commit/push/remote verification → session `ended_at` → report 최종 read-only 검증 → 사용자 최종 응답. 미래 `ended_at`을 terminal 전에 미리 쓰지 않는다.

## 7. 배포된 capability profile

현재 배포 판정은 `formal_adapter_enabled: false`, `manual_wait_polling_supported: false`, `host_managed_subagent_orchestration: supported`, `team_execution_enabled: true`다. 검증 버전·smoke 근거(terminal-only 1-agent, delayed terminal 재-suspend, staggered 2-agent all-results — 2026-08-25 Claude Code 2.1.243 전부 pass)는 Claude Code appendix `claude-code-lifecycle-routing.md` §8에서만 관리한다. 실행 중 임의 추론으로 이 profile이나 result collection 계약을 덮어쓰지 않는다.
