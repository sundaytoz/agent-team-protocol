---
kind: backlog
title: Codex CLI 0.149.1 hook-guarded bounded pool qualification handoff
status: proposal
date: 2026-08-27
owner: template-maintainer
last_reviewed: 2026-09-08
---

# Codex CLI 0.149.1 hook-guarded bounded pool qualification handoff

## Summary

Codex CLI나 runtime 변경을 기다리지 않고 ATP가 Codex CLI 0.149.1의 실제 동작에
맞추는 후속 후보를 기록한다. Candidate 이름은 아직 정식 vocabulary가 아니지만 이
문서에서는 `hook_guarded_bounded_pool_orchestration`으로 부른다.

핵심 전환은 `wait_agent` delivery만 terminal 정본으로 삼지 않고 plugin-bundled hook이
spawn, wait, subagent lifecycle과 root stop을 관측해 `${PLUGIN_DATA}`에 durable ledger를
유지하는 것이다. Hook ledger는 누락된 terminal delivery 보충과 parent completion
barrier를 제공하고, skill의 pending/running/terminal queue가 bounded refill을 수행한다.

이 문서는 채택된 ADR이나 배포 계약이 아니다. 아래 **확인된 사실**은 다음 작업의
출발점으로 사용할 수 있지만, **가설**은 격리 runtime smoke 전까지 supported capability로
표현하면 안 된다.

## Scope and invariants

- Codex CLI는 `0.149.1`로 고정한다. CLI/runtime 수정이나 업그레이드를 해결책으로 두지 않는다.
- 저장소 source skill과 source plugin을 정본으로 사용한다. 설치된 사용자 plugin cache는
  정본이 아니며 사용자 전역 cache/settings/hooks를 변경하지 않는다.
- 임시 `CODEX_HOME`, 임시 workspace와 fresh source install만 사용한다.
- Raw hook event, JSONL transcript, 사용자 대화, 인증 정보, 로컬 사용자명과 절대 경로는
  커밋하지 않는다. 공개 evidence에는 sanitized label, count, ordering과 SHA-256만 둔다.
- Fixed sleep, 반복 `list_agents`, shell status polling은 scheduler correctness primitive가 아니다.
- Promotion 판정은 §Phase 3의 4개 독립 축으로 한다. 필수 축(A)이 실패하면 profile과 version/release metadata를 올리지 않는다. 선택 축(B/C)의 실패·unknown은 그 축의 값으로만 기록하고 다른 축의 판정을 낮추지 않는다.

## Confirmed facts

### 1. Existing Codex 0.149.1 bounded-pool baseline

Source-skill candidate에서 이미 다음 case가 통과했다.

| case | observed | result |
|---|---|---|
| flat root pool | tasks/accepted/terminal/collected `5/5/5/5`, width 3, pool wait 2, list/interrupt 0 | pass |
| nested owner pool | workers/accepted/terminal/collected `5/5/5/5`, worker width 2, root wait 1, owner wait 4, list/interrupt 0 | pass |
| capacity-denial refill | logical tasks 5, spawn attempts 6, accepted 5, denial 1, terminal/collected `5/5`; denied task는 pending 복귀 후 새 identity로 실행 | pass |

Fresh source install도 byte parity와 flat/nested/denial-refill 최소 회귀를 통과했다.
Source/installed `codex-team/SKILL.md` SHA-256는
`bcfbdd0f0f7d066233155faebdec9aadb78de73fc2bfa057b3c7aec740eee146`다.

### 2. Existing nonterminal/control qualification failures

현재 공개 evidence는
[Codex CLI 0.149.1 manifest](../../tests/runtime-behavior/evidence/codex-cli-0.149.1-20260826.json)다.

| case | confirmed ordering and counts | result |
|---|---|---|
| saturated nonterminal → terminal | requested 5, attempts/accepted 3/3, running/pending 3/2에서 nonterminal 1, MESSAGE release/refill 0/0, 같은 worker terminal 확인, terminal/collected 3/1, waits 2; 두 번째 wait가 반환하지 않아 refill/final 없음 | fail |
| active-wait steering | requested/attempted/accepted `5/5/5`, steering queued/acknowledged/delivered `1/1/0`, terminal/collected `4/4`, waits 5; root send/follow-up/list/interrupt 0, parent final 없음 | fail |
| approval continuation | requested/attempted/accepted `2/2/2`, approval required/relayed/decided `1/1/1`, reject 뒤 target `turn_aborted`, target terminal 0, companion terminal/collected 1/1, same-identity continuation 미확인 | fail |
| cancellation | requested/attempted/accepted `5/5/5`, queue accepted 1이나 active wait delivery 0, queue 뒤 추가 spawn 2, terminal/collected `4/4`, waits 4, scheduler interrupt 0, parent final 없음 | fail |

Cancellation run에서 사용한 `codex queue`는 message enqueue surface다. Queue message에
`cancel`이라는 문자열을 넣은 사실만으로 actual turn/agent interrupt를 증명하지 않는다.
다음 qualification은 TUI/background-agent stop, actual `interrupt_agent`, 또는 동등한
authoritative cancellation event를 사용해야 한다.

### 3. Official hook surface available in Codex 0.149.1

[공식 OpenAI Hooks 문서](https://learn.chatgpt.com/docs/hooks)는 다음을 명시한다.

- Enabled plugin은 기본 `hooks/hooks.json` 또는 `.codex-plugin/plugin.json`의 `hooks`
  entry로 lifecycle hooks를 번들할 수 있다.
- Plugin hook command에는 `PLUGIN_ROOT`, `PLUGIN_DATA`와 호환 env가 제공된다.
- `PreToolUse`와 `PostToolUse`는 대부분의 local function tool을 관측하며
  `spawn_agent`는 `Agent` alias에도 match한다.
- `SubagentStart`는 `agent_id`, `agent_type`, `turn_id`를 제공한다.
- `SubagentStop`은 `agent_id`, `agent_transcript_path`, `stop_hook_active`,
  `last_assistant_message`를 제공한다.
- `SubagentStop`의 `decision: block`은 subagent flow를 continuation한다.
- Root `Stop`의 `decision: block`은 새 continuation prompt를 만들고 root turn을 계속한다.
- Plugin hook은 설치만으로 trust되지 않는다. 사용자가 현재 hook definition을 review/trust하지
  않았거나 hooks가 policy/config로 disabled면 실행되지 않을 수 있다.
- Background hook completion은 스스로 새 turn을 시작하지 않는다. Specialized tool path는
  default hook path에서 opt out할 수 있으므로 hook을 완전한 enforcement boundary로 가정하면 안 된다.

[공식 OpenAI Subagents 문서](https://learn.chatgpt.com/docs/agent-configuration/subagents)는
interactive CLI에서 inactive subagent의 approval overlay가 source thread를 표시하며,
사용자가 running subagent를 steer/stop하도록 Codex에 요청할 수 있다고 설명한다.

### 4. Isolated hook coverage probe on actual Codex 0.149.1

2026-08-26/27 임시 `CODEX_HOME`과 임시 git workspace에서 project-local hook을
`--dangerously-bypass-hook-trust`로 명시 승인해 black-box probe를 수행했다. 이 flag는
격리된 maintainer probe에서만 사용했으며 배포 trust UX를 통과했다는 뜻이 아니다.

#### Coverage probe

한 root가 child 하나를 spawn하고 wait한 run에서 다음 hook input을 실제 관측했다.

| order | event | confirmed fields |
|---:|---|---|
| 1 | `PreToolUse` | `tool_name=collaborationspawn_agent`, `tool_use_id`, visible `task_name`; delegated `message`는 encrypted payload |
| 2 | `PostToolUse` | 같은 tool identity와 canonical task response |
| 3 | `SubagentStart` | stable `agent_id`, `agent_type=default`, child `turn_id` |
| 4 | `PreToolUse` | `tool_name=collaborationwait_agent`, `timeout_ms` |
| 5 | `SubagentStop` | 같은 `agent_id`, `stop_hook_active=false`, `last_assistant_message=HOOK_CHILD_DONE` |
| 6 | `PostToolUse` | wait completed response |
| 7 | `Stop` | root `turn_id`, `stop_hook_active=false`, `last_assistant_message=HOOK_ROOT_DONE` |

Counts는 spawn pre/post 1/1, subagent start/stop 1/1, wait pre/post 1/1,
root stop 1이다.

#### Same-identity continuation probe

별도 run에서 `SubagentStop`과 root `Stop`이 처음 호출될 때 hook이 `decision: block`을
반환했다.

- `SubagentStop` 2회가 동일 `agent_id`와 동일 child `turn_id`에서 발생했다.
- Ordering은 `stop_hook_active=false`, `HOOK_CHILD_INITIAL` →
  `stop_hook_active=true`, `HOOK_CHILD_CONTINUED`였다.
- Root `Stop` 2회도 동일 root `turn_id`에서 발생했다.
- Ordering은 `stop_hook_active=false`, `HOOK_ROOT_INITIAL` →
  `stop_hook_active=true`, `HOOK_ROOT_CONTINUED`였다.
- 새 environment identity, retry 또는 fallback은 생성되지 않았다.

Raw probe logs는 커밋하지 않았다. Local artifacts의 SHA-256만 기록한다.

| sanitized artifact | lines | SHA-256 |
|---|---:|---|
| hook coverage events | 12 | `1faa0e6275652a77f4aa3d08412f2a768ab904287c498de6a945d79d56ce3bcd` |
| hook continuation events | 4 | `ffbf93f966654e3ea2c4c475b7e8b0a7b3e3e59fdce6d62d0202e3ff404fdf74` |

## Hypotheses requiring qualification

아래 항목은 설계 가설이다. Runtime evidence 없이 `pass`, `supported`, `integrated`로
표현하지 않는다.

### H1. Hook ledger can close the missing-terminal gap

`SubagentStop`이 parent `wait_agent` delivery와 독립적으로 terminal identity/result를
제공하므로 `${PLUGIN_DATA}` ledger를 terminal 정본 보조 채널로 사용할 수 있다는 가설이다.

- `PostToolUse(collaborationwait_agent)`가 같은 session의 아직 model에 수집되지 않은
  `SubagentStop` rows를 `additionalContext`로 전달한다.
- 이미 hook ledger에서 terminal인 running set에 다시 wait하려 하면 `PreToolUse`가 그
  wait를 block하고 terminal delta를 feedback으로 반환한다.
- 이 동작이 saturated A의 terminal 3 / collected 1 gap을 없애고 terminal 뒤 refill을
  재개할 수 있어야 한다.

### H2. Root Stop can be an all-results completion barrier

Root `Stop` hook이 pool manifest의 requested/pending/running/terminal/collected count를
검사하고 incomplete이면 `decision: block`으로 같은 root turn을 계속할 수 있다는 가설이다.

- `Stop`은 terminal을 합성하지 않는다.
- 모든 requested logical result가 collected되기 전 final을 차단한다.
- `stop_hook_active=true`는 무조건 통과시키는 bypass가 아니다. Ledger가 complete일 때만
  allow하고, continuation loop는 bounded/event-driven이어야 한다.

### H3. Visible task name can carry stable logical identity

Spawn hook input의 delegated `message`는 encrypted라 hook이 logical metadata를 읽을 수
없다. 반면 `task_name`은 보인다. `task_name`에 pool id, logical task id와 `i_of_n`을
closed format으로 넣어 requested task manifest를 복원할 수 있다는 가설이다.

검증 전에는 spawn ordering만으로 `SubagentStart.agent_id`를 logical task에 결합하지 않는다.
Concurrent starts는 reorder될 수 있다. Candidate는 child `SubagentStart` additional context,
child result contract 또는 별도 correlation token으로 stable mapping을 증명해야 한다.

### H4. Terminal-boundary continuation can deliver steering before refill

`codex queue`가 active `wait_agent`를 즉시 깨우지 못하더라도 terminal wake 뒤 root
continuation safe point에서 queued user prompt가 적용되고, scheduler가 그 steering을
refill보다 먼저 처리할 수 있다는 가설이다.

`UserPromptSubmit`은 실제 prompt delivery를 관측할 뿐 queue acceptance 자체를 관측하는
event가 아니다. 다음 ordering이 원본 event로 확인돼야 한다.

```text
pool wait active
→ steering queued/acknowledged
→ terminal or hook continuation wake
→ UserPromptSubmit/steering delivered to existing root turn
→ running child에 send/follow-up exactly once
→ pending refill decision
```

이 ordering이 불가능하면 direct `/agent` steering 또는 별도 supported control surface로
contract를 재정의해야 한다. 단순 queue acceptance를 PASS로 세지 않는다.

### H5. Actual interrupt can implement pool cancellation

Actual root/agent interruption을 hook과 collaboration lifecycle이 관측하면 scheduler가
pending dispatch를 중단하고, running identities의 authoritative terminal/interrupted
confirmation만 수집할 수 있다는 가설이다.

- Cancellation 문자열을 queue하는 것은 actual interrupt가 아니다.
- 취소 뒤 spawn, retry, fallback, authority/ownership mutation은 0이어야 한다.
- Root turn abort가 `Stop`을 건너뛰는지, `SubagentStop`이 어떤 terminal detail을 주는지,
  child interrupt가 전체 pool cancellation intent와 어떻게 결합되는지 실측해야 한다.

### H6. Approval allow path preserves child identity

Interactive approval overlay에서 harmless action을 approve하면 같은 child `agent_id`가
continuation되고 terminal `SubagentStop`까지 도달한다는 가설이다. `PermissionRequest`
hook은 request/decision ordering을 기록할 수 있지만 ATP plugin이 arbitrary user action을
자동 승인해서는 안 된다.

Reject가 계속 `turn_aborted`로 끝난다면 approve path PASS와 reject path의 authoritative
aborted disposition을 별도로 문서화한다. 둘을 same-identity success로 합성하지 않는다.

### H7. Hook trust marker can fail closed at preflight

Plugin hook이 untrusted/disabled/policy-excluded일 때 team execution을 열지 않기 위해
`SessionStart` hook이 model-visible versioned capability marker를 주입하고 source skill이
첫 spawn 전에 그 marker를 요구할 수 있다는 가설이다.

- Marker가 없거나 version/hash가 다르면 spawn 0으로 blocked/Tier B decision path를 따른다.
- `--dangerously-bypass-hook-trust`는 maintainer smoke 전용이며 사용자 배포 preflight를
  대신하지 않는다.
- `allow_managed_hooks_only=true`, `[features].hooks=false`, changed hook hash와 trust review
  UX를 포함해 fail-closed를 검증해야 한다.

### H8. Hook runner can be distributed without undeclared host dependencies

Maintainer probe는 `python3` command hook을 사용했다. Python availability는 모든 지원
Codex 환경의 확인된 배포 계약이 아니다. 다음 중 하나를 선택하고 source/install smoke로
증명해야 한다.

- 명시적으로 지원 범위를 제한하고 Python 3 dependency를 preflight한다.
- Windows `commandWindows`를 포함한 portable command runner를 제공한다.
- Plugin-bundled MCP server 또는 self-contained executable로 ledger를 구현한다.

Dependency가 unknown이면 release profile을 올리지 않는다.

## Candidate architecture to prototype

최소 prototype은 다음 역할을 분리한다.

| component | responsibility |
|---|---|
| source `codex-team` skill | pending/running/terminal state, bounded width, capacity-denial pending 복귀, terminal-triggered refill, control ordering |
| `PreToolUse`/`PostToolUse` | spawn attempt/accepted/denial, wait call/result, send/follow-up/interrupt measurement, missing terminal delta delivery |
| `SubagentStart` | environment identity and child context correlation |
| `SubagentStop` | terminal identity, same-identity continuation signal, last assistant result capture |
| `PermissionRequest` | approval request/decision audit without unauthorized auto-approval |
| `UserPromptSubmit` | delivered steering/control audit; queue acceptance와 구분 |
| root `Stop` | requested all-results completion barrier |
| `${PLUGIN_DATA}` state | session-isolated, concurrency-safe pool manifest and append-only event ledger |

Ledger는 concurrent hook processes에 안전해야 한다. Partial writes, duplicate event,
reordered start/stop, hook retry와 root continuation loop를 처리하고 stable event id 또는
dedupe key를 가져야 한다. Unknown telemetry는 `null`로 기록한다.

## Qualification plan

### Phase 0 — preflight and packaging

1. 현재 `git status --short`와 `git diff`를 확인하고 기존 사용자 변경을 보존한다.
2. Source skill과 이 문서를 정본으로 읽는다.
3. 임시 `CODEX_HOME`과 workspace에 source plugin을 fresh install한다.
4. Plugin-bundled hook discovery, trust marker, `${PLUGIN_ROOT}`/`${PLUGIN_DATA}`와 runner
   dependency를 검증한다.
5. Hook disabled/untrusted/mismatched 상태에서 child spawn 0인 fail-closed case를 검증한다.

### Phase 1 — deterministic contract fixtures

- Exact hook tool-name vocabulary와 event schema fixture
- Spawn attempt/accepted/capacity-denied 구분
- `SubagentStart`/`SubagentStop` identity correlation과 dedupe
- Nonterminal은 running 유지, terminal만 slot release
- `Stop` incomplete block / complete allow
- Hook missing/error/timeout에서 synthetic terminal이나 supported promotion 금지
- Pending count와 requested manifest가 final barrier에 포함됨

### Phase 2 — isolated runtime smoke

각 smoke는 raw hook event와 Codex JSONL을 local temp에 보존하고 공개 manifest에는 sanitized
count/order/hash만 기록한다.

| id | required runtime result |
|---|---|
| T1 hook coverage | plugin-installed Pre/Post spawn/wait, SubagentStart/Stop, root Stop event 전수 관측 |
| T2 saturated nonterminal | running 3/pending 2에서 MESSAGE release/refill 0; terminal hook delta 전부 collected; requested/terminal/collected 5/5/5; terminal 뒤 FIFO refill |
| T3 premature root stop | delayed workers가 남은 동안 Stop hook이 final 차단; 마지막 result collected 뒤에만 allow |
| T4 steering | active wait에 actual steering; accepted와 delivered 분리; same root/child identity; retry 0; steering 적용이 refill보다 앞섬 |
| T5 approval | actual interactive approve 또는 reject; request/relay/decision/hook ordering; approve이면 same child identity terminal continuation |
| T6 cancellation | actual interrupt/stop; pending dispatch 중단; terminal confirmation 없는 completed/failed 합성 0; 취소 뒤 spawn/retry/fallback 0 |
| T7 capacity denial | tasks 5, attempts 6, accepted 5, denial 1; denied task pending 복귀; terminal 뒤 새 identity |
| T8 nested owner | owner/worker identity와 hook ledger isolation; workers 전부 collected; root final last |
| T9 source/install parity | source/installed hook config, runner와 skill hash parity; installed T1/T2/T7 최소 회귀 |

모든 normal completion case에서 requested logical tasks, spawn attempts, accepted spawns,
capacity denials, nonterminal/terminal deliveries, hook terminal rows, collected results,
pool wait, list/interrupt/follow-up/send calls, max running, refill order와 parent completion order를
기록한다.

### Phase 3 — promotion gate (축 직교 판정)

초판 gate는 T1–T9를 단일 boolean으로 접어 하나라도 fail이면 전 축을 disabled로 유지했다.
이는 ATP 자신의 설계와 모순된다. `platform-adapters.md` §3.2는 "Formal capability gap은
scheduling 최적화 unavailable이지 lifecycle failure가 아니다"로 축 직교성을 명시하고, §3.3의
execution mode 표도 formal adapter 결손과 managed orchestration 지원을 분리한다. 같은 논리로
**control-surface gap은 all-results barrier 실패가 아니다.** 따라서 promotion 판정을 다음
4개 독립 축으로 분해한다. 각 축은 자기 smoke 집합이 전부 PASS일 때만 해당 축을 올린다.

| 축 | smoke | 대응 요건 | 축이 fail일 때의 결과 |
|---|---|---|---|
| A. all-results barrier | T1, T2, T3, T7, T8, T9 | §3.3 요건 1~3 (child 생성·identity 연결, host routing/terminal delivery, 전원 terminal 뒤 barrier) | `host_managed_subagent_orchestration: unsupported`, team execution 불가 |
| B. in-flight control delivery | T4, T6 | §3.3 요건 4 중 user steering delivery | 축만 `unsupported`; mid-flight steering/취소에 의존하는 요청만 blocked/user-decision |
| C. approval continuation | T5 | §3.3 요건 4 중 host control 보존 | 축만 `unsupported`; approval 경유 작업만 blocked |
| D. packaging and runner scope | H7, H8 | 배포 가능 범위 | 선언된 scope 밖 host에서만 spawn 0 fail-closed |

**A는 필수 축이다.** A가 fail이면 B/C/D와 무관하게 team execution을 열지 않는다.
B와 C는 서로 독립이며 어느 쪽도 A를 무효화하지 않는다. §3.3 요건 4는
"user steering **또는** host control을 보존한다"는 선언적 OR이므로 B와 C 중 하나가
supported면 요건 4는 충족된다.

D는 boolean이 아니라 **선언된 배포 scope**다. H8이 이미 명시한 첫 번째 선택지
("명시적으로 지원 범위를 제한하고 Python 3 dependency를 preflight한다")를 채택하면
Windows 미검증은 축 fail이 아니라 scope 밖이다. 선언 scope 밖 host에서는 marker가
생성되지 않아 기존 fail-closed 경로가 그대로 spawn 0을 보장한다.

승격 시 갱신 대상(정식 execution mode name, capability axis, ADR, skill/task routing, ledger
vocabulary, validator, Known Issues, Changes, version, release metadata)은 **올린 축에 한정**한다.
축이 unsupported인 기능을 supported로 표현하지 않는다.

#### 축별 재판정

2026-08-28 evidence를 위 분해로 다시 읽으면 다음과 같다.

| 축 | 2026-08-28 상태 | 판정 근거 |
|---|---|---|
| A | T7/T9 blocked, 나머지 PASS | T7은 pool 기능 실패가 아니다. Evidence 자체가 `requested/attempts/accepted/terminal/collected = 5/6/5/5/5`, `parent_observed_capacity_denials: 1`이다. denial 감지 → pending 복귀 → refill → 전원 수집까지 정상 동작했고, hook ledger 라벨만 `attempted`로 남았다. T9는 설치본 T7 회귀 파생이다. |
| B | unsupported (비대화형), unknown (대화형) | T4/T6 artifact는 `root_jsonl` = `codex exec --json` 비대화형 run이다. 반면 PASS한 T5는 `tui_rollout` = interactive PTY다. 공식 Subagents 문서와 자체 research `P2-codex-cli-controls.md`가 모두 live steer/stop을 interactive CLI 경로로 설명한다. 즉 B는 **통과 가능한 surface에서 아직 측정되지 않았다.** |
| C | supported | T5 PASS — 실제 interactive decision 뒤 같은 child identity가 continuation돼 terminal까지 도달했다(H6 확인). |
| D | Unix scope 내 supported, Windows scope 밖 | Unix `python3` runner PASS, untrusted hook과 `features.hooks=false`에서 spawn 0. `allow_managed_hooks_only`는 미측정. |

#### A축 blocker 해소 (2026-08-31)

T7의 원인은 host 제약이 아니라 candidate 구현 갭이었다. Codex CLI 0.149.1이 실패한 local
function tool에 `PostToolUse`를 내보내지 않는 것은 사실이지만, **parent는 그 error를
`spawn_agent`의 반환값으로 이미 authoritative하게 관측한다.** ADR-0020의
environment-authoritative 원칙에서 tool 반환 error는 environment의 권위 응답이다. 여기에
hook ledger의 독립 attestation을 추가로 요구한 것은 이 candidate가 만든 제약이지 ATP
불변식이 아니다.

해법은 이 레포에 이미 존재했다. `hooks/hooks.json`의 `PreToolUse` matcher에 `update_plan`이
이미 포함돼 있고, `handle_pre_bind()`가 `ATP_POOL_BIND` marker로 parent-visible 사실을 durable
ledger에 기록하는 패턴을 T1에서 이미 PASS시켰다. 같은 채널에
`ATP_POOL_DENIED <pool> <index>/<total> <token>`을 추가하면 새 host capability 없이 denial이
ledger에 기록된다.

Hook은 다음 조건이 전부 성립할 때만 marker를 수용하므로 synthetic denial 경로가 생기지 않는다.

- pool/total/token이 durable manifest와 일치
- 해당 task에 `accepted_identity`가 없고 status가 `pending`
- 그 index에 아직 미해소인 `attempted` spawn attempt가 실제로 존재

세 조건 중 하나라도 어긋나면 `permission_deny`로 닫는다. 중복 marker는 소비할 `attempted`
entry가 없어 자동으로 거부된다. `PostToolUse`를 내보내는 host에서는 기존
`handle_post_spawn()` 경로가 그대로 동작하고, 이미 기록된 attempt는 재계수하지 않는다.

따라서 A축 재판정에 필요한 것은 새 host surface가 아니라 **T7/T9 재실행 1회**다.

#### A축 재실행 결과 (2026-08-31) — PASS

임시 `CODEX_HOME`, 임시 git workspace, fresh source install로 재실행했다. 공개 evidence는
[`codex-cli-0.149.1-hook-guarded-20260831.json`](../../tests/runtime-behavior/evidence/codex-cli-0.149.1-hook-guarded-20260831.json)이다.

| 항목 | 2026-08-28 | 2026-08-31 |
|---|---|---|
| requested / attempts / accepted / terminal / collected | 5 / 6 / 5 / 5 / 5 | 5 / 6 / 5 / 5 / 5 |
| `hook_ledger_capacity_denials` | **0** | **1** |
| denial attestation | 없음 | `attested_by: parent_marker` |
| `list_calls` / `interrupt_calls` | 0 / 0 | 0 / 0 |
| source/install byte parity | pass | pass |
| 판정 | fail | **pass** |

Ledger가 원인과 해소를 함께 보여준다. 실패한 `spawn_agent`의 `PreToolUse`는 있고
`PostToolUse`는 없다(spawn Pre 6 / Post 5 — 결손 1건). 그 지점에서 scheduler가
`ATP_POOL_DENIED`를 기록해 attempt가 `capacity_denied` / `attested_by: parent_marker`로
확정됐고, denied task는 pending 복귀 후 새 identity로 refill돼 전원 수집됐다. 마지막 hook
event는 전원 collected 뒤의 `Stop`이었다.

Host 실제 오류 원문은 `collab spawn failed: agent thread limit reached`다.

같은 run들에서 H1/H2/H3/H6이 실동작으로 재확인됐다. H2는 task 하나가 running이고 하나가
pending인 상태에서 root `Stop`을 실제로 차단하고 같은 root turn을 wait로 continuation했다.

재현 조건 두 가지를 기록한다.

- 기본 동시성 한계는 고정 상수가 아니다. 기본 설정 run에서 spawn 4건이 모두 accepted됐다.
  §Confirmed facts의 "primary 포함 총 4 active threads"는 관측 조건에 의존한다.
- Denial을 결정론적으로 재현하려면 `agents.max_concurrent_threads_per_session`을 명시
  설정하고 **child가 slot을 붙잡고 있는 동안** 초과 spawn을 시도해야 한다. Trivial child는
  다음 spawn 전에 slot을 반납해 denial이 발생하지 않는다.

#### 남은 승격 조건

```text
A축: PASS (2026-08-31 재실행)
B축: interactive PTY에서 T4/T6 재측정 필요 (비대화형 결과는 판정 근거 아님)
C축: PASS
D축: Unix/python3 scope 선언 + allow_managed_hooks_only 측정 + packaging 부수효과 결정
```

D축의 packaging 부수효과가 새로 확인됐다. `codex plugin add`만으로 `hooks/hooks.json`과
runner가 설치본에 실렸고, manifest에 `hooks` 필드가 없어도 기본 discovery 경로로 실행됐다.
도구를 전혀 쓰지 않는 프롬프트에서도 `PLUGIN_DATA`에 state와 ledger row가 기록됐다.

다만 이 비용은 **hook trust가 부여된 세션에만** 발생한다. 같은 임시 환경에서
`--dangerously-bypass-hook-trust` 없이 실행하면 marker가 도달하지 않고(`MARKER_ABSENT`)
새 `PLUGIN_DATA` state도 생성되지 않았다. 비대화형 `codex exec`는 trust 프롬프트나 경고를
출력하지 않고 조용히 hook을 실행하지 않는다. 즉 exec 경로에서는 신뢰 부여 전 비용이 0이고,
H7의 fail-closed도 이 경로에서 다시 확인된다.

`features.hooks`는 명시 설정 없이도 기본 활성이다. Fresh 임시 home에서 `config.toml`에
`[features]` 항목을 만들지 않은 상태로 측정했다.

| 조건 | marker |
|---|---|
| 기본 config, bypass 없음 | `MARKER_ABSENT` |
| 기본 config, `--dangerously-bypass-hook-trust` | 정상 출력 |

즉 번들 hook은 설치 직후 **활성 상태로 trust만 기다린다**. Feature flag가 아니라 hook trust
하나가 유일한 관문이다.

Non-interactive `codex exec`에는 승인 UI가 없어 조용히 건너뛰므로, 사람이 trust를 부여할 수
있는 경로는 TUI뿐이다.

#### Interactive TUI 최초 대면 동작 (2026-09-08 측정)

Fresh 임시 home에서 plugin 설치 후 TUI를 처음 켰을 때 다음 화면이 나타났다.

```text
Hooks need review
8 hooks are new or changed.
Hooks can run outside the sandbox after you trust them.

1. Review hooks
2. Trust all and continue
3. Continue without trusting (hooks won't run)
```

`8 hooks`는 이 candidate의 `hooks/hooks.json` 항목 수와 정확히 일치한다
(`SessionStart`, `PreToolUse`, `PostToolUse`, `SubagentStart`, `SubagentStop`,
`PermissionRequest`, `UserPromptSubmit`, `Stop` 각 1개).

`2. Trust all and continue`를 선택한 뒤 재시작하면 프롬프트가 다시 나오지 않았다. Trust는
`config.toml`에 hook 항목 단위로 영구 저장된다.

```toml
[hooks.state."atp@agent-team-protocol:hooks/hooks.json:session_start:0:0"]
trusted_hash = "sha256:..."
```

#### Trust는 command 문자열에 묶이고 runner 내용에는 묶이지 않는다

Trust 부여 뒤 격리 설치본을 직접 변형해 `codex exec`(bypass 없음)로 marker 도달 여부를
측정했다.

| 변형 | marker | 해석 |
|---|---|---|
| 변형 없음 | 도달 | 기준선 |
| `hooks/codex_pool_hook.py` 내용 변경 | **도달** | runner 코드가 바뀌어도 trust 유지 — 변경된 코드가 그대로 실행됨 |
| 해당 event의 `command` 문자열 변경 | **미도달** | trust 무효화 |

즉 Codex는 실행할 **명령줄**을 신뢰하고 그 명령이 실행하는 **코드**는 신뢰 범위에 넣지 않는다.
Consumer가 한 번 `Trust all`을 선택하면 이후 릴리스에서 runner 코드를 바꿔도 추가 확인 없이
sandbox 밖에서 실행된다.

#### D축 결론

성능 비용은 §소비자 비용 제거로 해소했지만, 동의 범위 문제가 남는다. 번들에 포함해 배포하면
`team_execution_enabled: false`인 모든 Codex consumer가 다음을 받는다.

- 얻을 기능이 없는 상태에서 "hooks can run outside the sandbox" 신뢰 요청 1회
- `Trust all`을 선택했다면, 이후 모든 atp 릴리스의 runner 코드 변경에 대한 무확인 실행 권한

따라서 candidate hook을 base 번들로 배포하지 않는다. 이 기능을 실제로 켜는 사람만 sandbox 밖
실행 동의를 요구받아야 하므로, `atp-graphify`와 같은 **옵트인 add-on 분리**를 D축 결정으로
채택한다. 옵트인 경계 안에서는 Unix/`python3` scope 선언과 `allow_managed_hooks_only` 측정만
남는다.

#### D축 add-on 분리 완료 (2026-09-08)

Candidate hook 두 파일을 base `plugins/atp/hooks/`에서 새 옵트인 add-on
`plugins/atp-codex-hooks/hooks/`로 옮겼다(`git mv`, runner byte 무수정 —
`runner_sha256` `22b93853…`은 2026-08-31 evidence와 동일). base 번들에는 hook이 남지 않는다.

- add-on manifest 2곳(`.claude-plugin`/`.codex-plugin`, version `1.0.0`, `dependencies: ["atp"]`)과
  marketplace 정본 3곳에 `atp-codex-hooks`를 등재했다.
- `hooks.json`은 description만 add-on 표기로 바뀌어 `hooks_sha256`이 `d7005171…`로 재생성됐고,
  `codex-team/SKILL.md` §1 marker를 새 해시로 갱신했다. add-on 미설치면 marker가 없어 기존
  fail-closed(spawn 0)가 그대로 동작하며, `$atp:task`는 `skip: no-codex-hooks`로 기록하고 차단 없이
  계속한다.
- 회귀 2건 추가 — `test_base_bundle_ships_no_hooks`,
  `test_addon_manifests_and_marketplaces_are_consistent`. 기존 19건은 add-on 경로로 상수만 바꿔
  전부 통과.
- 배포 profile은 변경하지 않았다(`team_execution_enabled: false` 유지). base는 hook 미배포라는
  소비자 가시 변경으로 `2.16.0 → 2.17.0`.

남은 D축 항목은 옵트인 경계 안의 `allow_managed_hooks_only` 측정과 Windows `py -3` runner
scope 결정이다. 사용자 가이드는 `plugins/atp-codex-hooks/docs/codex-hooks-usage.md`.

#### 소비자 비용 제거 (2026-09-01)

Trust가 부여된 세션에서 측정된 per-tool 비용은 candidate 설계 결함이었고, 배포 형태와
무관하게 고쳤다. 소비자는 ATP가 동작하기만 하면 되고 진단 산출물을 부담할 이유가 없다.

| 항목 | 이전 | 이후 |
|---|---|---|
| `Bash` / `apply_patch` 호출 | hook 실행 56ms + state 재작성 + ledger 1줄 | matcher에서 제거 — runner 미호출 |
| pool 없는 세션의 매칭 도구 | 56ms + 파일 3개 생성 | 49ms, **파일시스템 접근 0** |
| `events.jsonl` | 항상 기록, 이벤트마다 `fsync` | `ATP_HOOK_EVENT_LEDGER=1`일 때만 |

세 가지 변경이다.

1. **matcher 축소** — `PostToolUse`에서 `Bash|apply_patch`를 제거했다. 두 도구는 ATP pool과
   무관하며 approval action 관측이라는 부가 telemetry에만 쓰였다. T5의 판정 근거인
   `same_identity_terminal`은 `SubagentStop`에서 오므로 축 판정은 영향받지 않는다.
2. **filesystem fast path** — durable state가 없고 이 event가 pool을 열 수 없으면
   디렉토리 생성·lock 획득·state 읽기 전에 즉시 반환한다. Pool을 열 수 있는 event는
   `SessionStart`와 `task_name`이 pool task 형식인 spawn뿐이다.
3. **event ledger opt-in** — `events.jsonl`은 runner가 읽지 않는 maintainer 진단이므로 기본
   비활성이다. Pool 동작에 필요한 `state.json`은 그대로 유지한다. Hook은 event마다 별도
   프로세스라 durable state 없이는 barrier·terminal delta·refill이 성립하지 않는다.

남은 49ms는 Python 인터프리터 시동과 stdlib import(47ms)이고 실제 처리는 약 2ms다. 이제
`update_plan`과 collaboration 도구에만 걸리므로 team execution이 꺼진 소비자에게는 세션당
`update_plan` 몇 회에 그친다.

A와 D가 충족되면 `host_managed_subagent_orchestration: supported`와
`team_execution_enabled: true`를 **선언된 scope 안에서** 전환할 수 있다. B는 그때도
독립적으로 `unsupported | unknown`으로 남을 수 있으며, 이는 mid-flight steering/취소를
요구하는 요청에서만 blocked/user-decision 경로를 의미한다. 전환 전까지는 다음을 유지한다.

```yaml
formal_adapter_enabled: false
manual_wait_polling_supported: false
host_managed_subagent_orchestration: unsupported
team_execution_enabled: false
```

## 2026-08-28 qualification result

Fresh source install의 bundled hook 후보는 T1/T2/T3/T5/T8을 통과했지만 T4/T6/T7/T9가
실패했고 H8은 unknown이다. 따라서 이 문서의 proposal 상태, 현재 four-axis disabled
profile, `team_execution_enabled=false`와 plugin version은 유지한다.

| smoke | 핵심 count/order | 결과 |
|---|---|---|
| T1 | requested/accepted/terminal/collected `1/1/1/1`; SessionStart → spawn pre/post → bind → SubagentStop → wait delta → complete Stop | pass |
| T2 | `5/5/5/5`; running 3/pending 2의 nonterminal send 1, first terminal 전 refill 0, terminal 뒤 worker 4/5 refill | pass |
| T3 | 첫 Stop `pending/running/terminal/collected=0/1/0/0`에서 block, 같은 root turn continuation 뒤 `1/1` terminal/collected | pass |
| T4 | active wait 중 steering queue accepted 1, `UserPromptSubmit` delivery 0, send/follow-up 0 | fail |
| T5 | PermissionRequest 1, 일회성 human allow 1, 같은 child identity terminal 1 | pass |
| T6 | active wait 중 cancellation queue accepted 1, delivered/cancel-ledger/interrupt `0/0/0`, synthetic terminal 0 | fail |
| T7 | tasks/attempts/accepted/terminal/collected `5/6/5/5/5`; parent denial 1, hook ledger denial 0 | fail |
| T8 | root owner `1/1/1/1`, nested workers `3/3/3/3`; worker terminals 뒤 owner terminal | pass |
| T9 | source/install config·runner·skill byte parity, 설치본 T1/T2 pass, 설치본 T7 fail | fail |

T7에서 Codex CLI 0.149.1은 실패한 `spawn_agent` 호출에 `PostToolUse`를 내보내지 않았다.
재시도 Pre event만 보고 이전 attempt를 denial로 합성하지 않는다. T4/T6의 `codex queue`도
접수 UUID는 반환했지만 active wait에 prompt를 전달하지 않았다. 반면 T5 approve path는
실제 TUI decision 뒤 같은 identity로 계속돼 H6을 확인했다. Untrusted hook과
`features.hooks=false`는 exact marker 부재로 spawn 0이었지만, Windows `py -3`와
`allow_managed_hooks_only`는 아직 unknown이다.

공개 가능한 sanitized manifest는
[`codex-cli-0.149.1-hook-guarded-20260828.json`](../../tests/runtime-behavior/evidence/codex-cli-0.149.1-hook-guarded-20260828.json)이다.
이 절은 2026-08-28 시점의 원본 관측 기록이다. 같은 evidence를 §Phase 3의 축 분해로 다시 읽은
결과와 A축 blocker 해소 내용은 §Phase 3의 "축별 재판정"과 "A축 blocker 해소(2026-08-31)"를
따른다. 요약하면 T7/T9는 host 제약이 아니라 denial ledger writer 갭이었고(해소 완료, 재실행
대기), T4/T6은 통과 가능한 interactive surface에서 아직 측정되지 않았다.

## New-conversation continuation prompt

> **2026-09-08 — 아래 add-on 분리 프롬프트는 실행 완료됐다** (§D축 add-on 분리 완료). 다음 작업
> 후보는 B축 T4(interactive PTY steering) 재측정, `allow_managed_hooks_only` 측정, Windows runner
> scope 결정이다. 아래 원문은 실행 기록으로 보존한다.

이 절은 다음 작업 세션의 첫 요청 정본이었다. 이전 판(2026-08-28 재검증용)은 A축 PASS와
D축 결정으로 대체됐고, 이 판은 **candidate hook의 옵트인 add-on 분리**를 지시했다.

권장 host는 Claude Code다. 이 레포의 배포 profile에서 Codex CLI는
`team_execution_enabled: false`이므로 Codex에서 `$atp:task`를 부르면 `tier_b_sequential`로
격하되어 advisor 병렬 실행이 없다. 또한 이 레포는 사용자 Codex의 local marketplace source로
등록돼 있어, Codex에서 작업하면 방금 커밋된 `plugins/atp/hooks/`가 전역 설치본으로 들어와
"Hooks need review" 신뢰 다이얼로그를 반복해 밟게 된다. Codex CLI 자체는 Claude Code에서
`codex plugin` / `codex exec`로 도구처럼 구동해 검증할 수 있다 — 2026-08-31 A축 재실행이
그 방식으로 수행됐다. Interactive TUI 확인만 사람이 직접 해야 한다.

```text
/atp:task agent-team-protocol 레포에서 Codex hook-guarded bounded pool candidate 를
base 번들에서 분리해 옵트인 add-on 으로 만들어줘. D축 결정은 이미 끝났고 근거도 커밋돼 있다.
설계와 구현 계획을 먼저 보여준 뒤 진행해.

## 시작 전 필수 확인

1. `git log --oneline -3` — HEAD 가 `feat(atp): decompose Codex hook-guarded qualification
   into orthogonal axes` 인지 확인. 브랜치는 `feat/claude-code-managed-orchestration`.
2. `git status --short` — 미추적 `docs/changes/2026-08-18-pre-spawn-capability-gate.md` 는
   사용자 파일이다. 읽기·수정·이동·삭제·stage 하지 않는다.
3. `docs/index.md` → `docs/backlog/index.md` →
   `docs/backlog/codex-cli-hook-guarded-bounded-pool.md` 전문을 읽는다.
   §Phase 3 의 4축 gate, "축별 재판정", "A축 blocker 해소", "소비자 비용 제거",
   "Interactive TUI 최초 대면 동작", "D축 결론" 절이 이 작업의 전제다.
4. 함께 읽는다: `plugins/atp/docs/development/codex-lifecycle-routing.md` §8.2~§8.4,
   `plugins/atp/skills/codex-team/SKILL.md`, `plugins/atp/docs/development/platform-adapters.md`
   §3.2~§3.3, `docs/adr/ADR-0024-host-managed-subagent-orchestration.md`,
   `docs/development/release-checklist.md` §0 와 §4,
   `tests/runtime-behavior/README.md`, `tests/runtime-behavior/test_codex_hook_guard.py`.
5. add-on 선례를 읽는다: `plugins/atp-graphify/` 전체 구조와
   `plugins/atp/skills/task/SKILL.md` 의 graphify 옵트인 분기(§9 종료조건 4항의
   "skip: no-graphify" 처리).

## 확정된 사실 — 다시 검증하지 않는다

아래는 실측 완료 사항이다. 재측정하거나 fail 로 재도출하지 않는다.

- **A축 PASS.** codex-cli 0.149.1 격리 재실행에서
  requested/attempts/accepted/terminal/collected `5/6/5/5/5`,
  spawn PreToolUse 6 / PostToolUse 5(실패 spawn 에 Post 미발생),
  hook ledger capacity denial 1건 `attested_by: parent_marker`,
  list/interrupt 0, 마지막 hook event `Stop`. source/install byte parity 일치.
  evidence: `tests/runtime-behavior/evidence/codex-cli-0.149.1-hook-guarded-20260831.json`
- **C축 PASS** (2026-08-28 T5, interactive approval same-identity continuation).
- **B축은 T4(steering) 하나만 남는다.** T6(cancellation) 은 범위 밖 재분류 대상이다 —
  CLI 에 target-child cancel command 가 없고 호스트 인터럽트가 상위 계층에서 전체를 끊으므로
  ATP 가 지킬 불변식(terminal confirmation 없는 합성 금지)은 이미 충족된다.
  T4/T6 의 기존 FAIL 은 비대화형 `codex exec` + `codex queue` 에서 측정된 것이고,
  통과 가능한 surface 는 interactive PTY 다. 비대화형 결과를 판정 근거로 재사용하지 않는다.
- **hooks feature 는 기본 ON.** `config.toml` 에 `[features]` 없이도 bypass 만 주면
  marker 가 뜬다. 유일한 관문은 hook trust 다.
- **TUI 최초 대면**: "Hooks need review / 8 hooks are new or changed / Hooks can run outside
  the sandbox after you trust them" + 선택지 3개(Review / Trust all and continue /
  Continue without trusting). `Trust all` 후 재시작 시 재확인 없음.
  trust 는 `config.toml` 의 `[hooks.state."<plugin>:hooks/hooks.json:<event>:0:0"]`
  `trusted_hash` 로 항목 단위 영구 저장.
- **trust 는 command 문자열에만 묶인다.** runner `.py` 내용을 바꿔도 trust 가 유지되어
  바뀐 코드가 sandbox 밖에서 그대로 실행된다. 해당 event 의 `command` 문자열을 바꿀 때만
  무효화된다. 이것이 add-on 분리의 결정적 근거다.
- **소비자 per-tool 비용은 제거 완료.** `Bash|apply_patch` matcher 제거, filesystem fast
  path, `ATP_HOOK_EVENT_LEDGER=1` opt-in ledger. pool 없는 세션의 매칭 도구는 49ms
  (python 시동 28 + stdlib import 19 + 처리 2), 파일시스템 접근 0.
  회귀 3건이 이를 고정한다 — `test_consumer_session_without_a_pool_writes_nothing`,
  `test_event_ledger_is_off_unless_explicitly_enabled`,
  `test_unrelated_tools_are_not_matched_by_the_hook_config`.

## 이번 작업 범위

candidate hook 을 base `plugins/atp/` 에서 옵트인 add-on 으로 옮긴다.

1. **add-on 플러그인 신설** — 이름은 `atp-graphify` 패턴을 따라 정한다(예: `atp-codex-hooks`).
   `plugins/<addon>/.claude-plugin/plugin.json` 과 `.codex-plugin/plugin.json`,
   `hooks/hooks.json`, `hooks/codex_pool_hook.py` 를 둔다.
   marketplace 정본 3곳(`.claude-plugin/marketplace.json`, `.codex-plugin/marketplace.json`,
   `.agents/plugins/marketplace.json`)에 등재한다.
2. **base 에서 제거** — `plugins/atp/hooks/` 를 옮기고, base 번들에 hook 이 남지 않게 한다.
   base 만 설치한 Codex 소비자에게 "Hooks need review" 가 뜨지 않아야 한다.
3. **경로·marker 재정합** — `hooks.json` 의 `$PLUGIN_ROOT` 는 add-on 루트를 가리키게 된다.
   `codex-team/SKILL.md` §1 의 `ATP_HOOK_GUARD_READY` marker 해시를 새 파일 위치 기준으로
   재생성하고, add-on 미설치 시 marker 가 없어 spawn 0 으로 닫히는 기존 fail-closed 를 유지한다.
4. **skill 분기** — `codex-team/SKILL.md` 와 `plugins/atp/skills/task/SKILL.md` 에
   add-on 미설치 시의 처리를 명시한다. graphify 의 "skip: no-graphify" 와 같이
   차단 없이 계속 진행하는 형태를 따른다.
5. **테스트 경로 갱신** — `tests/runtime-behavior/test_codex_hook_guard.py` 의
   `PLUGIN` / `RUNNER` / `HOOKS` / `SKILL` 상수를 새 위치로 맞추고 19건 전부 통과시킨다.
6. **문서 갱신** — backlog §Phase 3 D축 절에 분리 완료를 기록하고,
   `codex-lifecycle-routing.md`, `known-issues.md`/`.en.md` 를 정합화한다.
   `tests/runtime-behavior/README.md` 의 `ATP_HOOK_EVENT_LEDGER=1` 안내 경로도 확인한다.
7. **release-checklist §4 invariant** — add-on 을 새로 만들면 그 manifest 버전과 등재 4곳을
   점검한다. base atp 버전 bump 이 필요한지 §0 기준으로 판단한다.

## 제약

- `team_execution_enabled` 를 이 작업에서 true 로 바꾸지 않는다. add-on 분리는 배포 형태
  변경이고, 승격은 별도 결정이다.
- 사용자 전역 `~/.codex`, 사용자 plugin cache, 실제 소비 프로젝트 설정을 변경하지 않는다.
  격리 검증이 필요하면 임시 `CODEX_HOME` + 임시 workspace + fresh source install 만 쓴다.
- raw hook event, JSONL transcript, 인증 정보, 로컬 사용자명, 절대 경로를 커밋하지 않는다.
  공개 evidence 에는 sanitized count / ordering / SHA-256 만 둔다.
- 기존 evidence manifest(08-19, 08-26, 08-28, 08-31)는 원본 관측 기록이므로 수정하지 않는다.
  재해석은 backlog / routing 문서에만 쓴다.

## 격리 검증이 필요할 때의 함정

- `codex exec` 는 stdin 을 읽으려 블록한다. `< /dev/null` 없으면 10분 넘게 이벤트 0건으로 멈춘다.
- PATH 의 `codex` 는 cmux shim 이라 자체 hook set 을 주입한다. maintainer smoke 는
  `~/.local/bin/codex` 를 직접 호출한다.
- capacity denial 을 재현하려면 `agents.max_concurrent_threads_per_session=1` 설정 +
  "연속 spawn" 명시가 둘 다 필요하다. trivial child 는 다음 spawn 전에 slot 을 반납한다.
- fresh 임시 `CODEX_HOME` 은 `auth.json` 이 없어 TUI 첫 대면이 **로그인 화면**이다(hook 신뢰 프롬프트는
  로그인·디렉토리 신뢰 뒤에 온다). 로그인 flow 를 밟지 말고 `ln -s ~/.codex/auth.json "$CODEX_HOME/auth.json"`
  으로만 잠깐 연결하고 smoke 종료 시 링크를 제거한다. 복사·커밋 금지. (2026-09-08 실증)
- cmux surface 에 TUI 가 포그라운드인 상태로 셸 텍스트를 보내면 문자열이 TUI 메뉴 입력으로 흡수된다
  (`clear; codex` 가 로그인 메뉴에서 device-code 항목을 선택한 실증). 텍스트를 보내기 전 `read-screen` 으로
  셸 프롬프트인지 확인하고, TUI 면 `/quit`+Enter 또는 해당 PID 만 종료한 뒤 보낸다. `ctrl-c` 는 로그인 화면을
  닫지 않는다.

## 완료 응답에 포함할 것

변경 파일, base 설치본에 hook 이 남지 않았음을 보인 검증, add-on 설치 시 marker 정합,
테스트 결과(19 + 15 + 6 + lifecycle-contract), marketplace 등재 4곳,
version/release metadata 변경 여부와 근거, 남은 blocker(B축 T4, Windows runner,
`allow_managed_hooks_only`).
```

## References

- [Codex CLI collaboration await P0/P1 backlog](./codex-cli-collaboration-await-v1.md)
- [ADR-0022 pre-spawn wait/wakeup gate](../adr/ADR-0022-pre-spawn-wait-wakeup-capability-gate.md)
- [ADR-0024 host-managed subagent orchestration](../adr/ADR-0024-host-managed-subagent-orchestration.md)
- [Codex lifecycle routing](../../plugins/atp/docs/development/codex-lifecycle-routing.md)
- [Runtime behavior tests](../../tests/runtime-behavior/README.md)
- [OpenAI Hooks](https://learn.chatgpt.com/docs/hooks)
- [OpenAI Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)
