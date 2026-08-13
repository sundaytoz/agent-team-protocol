---
kind: changes
title: 2.13.0 — environment-driven subagent wakeup 계약과 no-timeout capability gate
date: 2026-08-13
version: 2.13.0
status: implemented-verified
owner: template-maintainer
---

# 2.13.0 — environment-driven subagent wakeup

## 요약

ATP 2.12.0의 environment-authoritative lifecycle correctness는 유지하면서, root model 재개 비용을 다루는 wait/wakeup scheduling 계약을 별도 층으로 추가했다. Formal scheduling은 timeout-free environment subscription만 허용한다. Host 필수 capability 하나라도 `unsupported|unknown`이면 timed wait나 polling으로 보상하지 않고 `wait_wakeup_capability_unavailable`을 정확히 한 번 기록한 뒤 blocked로 수렴한다.

구현과 독립 verification-advisor 검증이 완료됐다. Lifecycle+scheduling validator는 정확한 PASS 문구 `PASS: environment-authoritative lifecycle contract and compatibility fixtures`를 반환했고 report schema v2 legacy/current compatibility를 함께 통과했다. 현재 Codex host는 formal subscription을 지원하지 않으므로 이 verified 상태가 end-to-end event-driven wake 달성을 뜻하지는 않는다.

## 원인과 책임 경계

2.12.0은 timeout, 경과 시간, heartbeat/progress 부재와 동일 `running` snapshot을 lifecycle failure로 오판하지 않는다. 그러나 bounded wait 반환은 여전히 root model을 재개하고 큰 누적 context를 다시 입력한다. 따라서 lifecycle correctness와 token-efficiency는 별도 문제다.

- Environment 소유: invocation identity/state, timeout-free suspend, terminal/approval subscription, internal keepalive, event ID/deduplication, completion coalescing, compact changed-invocation delta, user steering, await cancellation과 child cancellation 결과.
- ATP 소유: logical task/DAG, target과 wait-any/all 조건, result contract 검증·취합, approval relay 정책, explicit failure 뒤 recovery 판단, completion race, retry identity, result acceptance authority, write ownership과 late completion 격리.

정본 결정은 [ADR-0021](../adr/ADR-0021-environment-owned-wait-wakeup-scheduling.md), 장기 구조는 [architecture 문서](../architecture/environment-authoritative-subagent-lifecycle-design.md)다. ADR-0021은 lifecycle 정본인 [ADR-0020](../adr/ADR-0020-environment-authoritative-subagent-lifecycle.md)을 supersede하지 않는다.

## 구현 내용

- `plugins/atp/docs/development/agent-team-protocol.md` §2.5에 host-neutral `await_invocations({targets, condition, wake_on})`, compact wake batch, phase-local scheduling ledger와 strict gap convergence를 추가했다.
- `plugins/atp/docs/development/platform-adapters.md`에 wait/wakeup required capability 12개와 all-required gate를 추가했다.
- `plugins/atp/docs/development/codex-lifecycle-routing.md`에 current Codex `adapter_enabled: false`와 capability 근거를 격리했다.
- `plugins/atp/skills/task/SKILL.md`, `plugins/atp/agents/research-advisor.md`, `plugins/atp/agents/implementation-advisor.md`에 top-level/nested scheduling gate를 실행화했다.
- Current Codex appendix는 `requested_mode: environment_subscription`과 `effective_mode: unavailable`을 분리하고 `adapter_enabled: false`와 일치시켰다.
- Research advisor의 Write/Edit allowlist에 owned `research/wait-wakeup-events.jsonl`을 추가했다. 두 advisor는 report-v2 `Invocations[]`와 분리된 `wait_wakeup_ledger` 및 닫힌 `wait_wakeup_disposition`을 반환한다.
- Orchestrator는 advisor spawn 전에 advisor 자체 report-domain `report_invocation_id`를 할당·주입한다. Scheduling row의 `owner_report_invocation_id`와 nested worker의 `parent_invocation_id`는 이 값을 사용하며 environment identity로 대체하지 않는다.
- Capability gap에서는 `wait_wakeup_capability_unavailable` 1회, automatic wait/list/retry/interrupt/fallback 각 0건, child lifecycle/result acceptance/write ownership 보존을 강제한다.
- Phase 종결은 blocked 또는 사용자가 명시 선택한 event-only external continuation뿐이다. Timer/polling continuation과 longer/repeated timed wait는 허용하지 않는다.
- Scheduling metadata는 phase-local `wait-wakeup-events.jsonl`에 두고 report `schema_version: 2`와 optional lifecycle field 네 개를 보존한다.
- `tests/lifecycle-contract/fixtures/wait-wakeup-cases.json`과 `tests/lifecycle-contract/validate.py`에 unchanged/keepalive 무재개, single/coalesced completion, approval, steering, duplicate deduplication, explicit recovery, completion race/late completion, capability gap, report-v2 compatibility와 comparison workload를 추가했다.
- Base manifest 4곳을 2.13.0으로 동기화했다. Add-on 2.3.0과 versionless `.agents/plugins/marketplace.json`은 변경하지 않았다.

## Current Codex support와 host gap

| capability | 판정 | 2.13.0 처리 |
|---|---|---|
| bounded global mailbox wait, 최대 1시간 | supported but ineligible | timeout이 root를 깨우므로 formal/fallback adapter에 사용하지 않음 |
| completed final-status와 user steering 조기 반환 | supported subset | 단독으로 gate 통과 불가 |
| timeout-free suspend와 persistent await identity | unsupported | adapter disabled |
| timeout 뒤 environment 내부 재대기 | unsupported | timed fallback 없음 |
| selected-target wait-any / wait-all | unsupported | adapter disabled |
| approval subscription, failure/interruption detail | unknown | 지원으로 추정하지 않음 |
| await cancellation handle | unsupported | host 변경 필요 |
| compact changed-invocation delta | unsupported | host 변경 필요 |
| stable event ID와 environment deduplication | unsupported | host 변경 필요 |
| completion coalescing | unknown | 보장으로 추정하지 않음 |
| scheduler/watchdog registration과 internal keepalive no-model-wake | unsupported | host 변경 필요 |

User steering과 cancellation responsiveness는 host 책임이다. ATP는 timeout이나 polling으로 이를 보상하지 않는다. 현재 normal Codex collaboration API에는 formal event-only external continuation도 없어 capability gap 뒤 phase는 blocked다.

## 2.12.0 source/cache parity

변경 전 source repo와 설치된 2.12.0 cache의 지정 9개 파일(`agent-team-protocol.md`, Codex appendix, platform adapter, task skill, research/implementation/parallel advisor, base manifest 2개)은 `cmp -s`와 SHA-256 비교에서 byte-identical이었다. 이는 scheduling gap이 stale cache 때문이 아니라 2.12.0 계약 자체의 빈 표면이었음을 보여준다.

2.13.0 source 구현 뒤 설치 cache 2.12.0과의 drift는 의도적이다. Cache는 evidence로 유지하고 직접 편집하지 않는다. 배포·설치 갱신 뒤 새 bundle parity는 별도 release 확인 대상이다.

## Before/after evidence

### Historical evidence

2026-08-12 root JSONL에서 독립 확인 가능한 수치는 다음과 같다.

| 항목 | 값 |
|---|---:|
| root token | 60,582,015 |
| root `wait_agent` call | 209 |
| timeout | 148 |
| root direct spawn | 34 |
| compaction | 1회, 최종 root 누적량의 93.06% 시점 |
| wait-resume event-order proxy input | 34,471,967 |
| wait-resume event-order proxy cached input | 34,161,408 |
| wait-resume event-order proxy output | 21,579 |

Nested child 15개, 전체 invocation 50개, tree token 102,214,528은 사용자 제공 historical 수치이며 단일 root JSONL로는 독립 검증할 수 없다. Resume usage도 causal ID가 없는 event-order proxy이므로 그 한계를 유지한다.

작은 timed-wait probe 두 번은 input 212,698, cached input 210,432, output 71이었다. 첫 10초 timeout과 다음 completion이 각각 root model을 재개했다.

### Deterministic comparison workload

Target 두 개, unchanged/internal keepalive 세 번, 인접 completion 두 번인 같은 trace를 고정했다.

| mode | root resumes | wait/subscription calls | list calls | disposition |
|---|---:|---:|---:|---|
| historical short polling | 5 | timed wait 5 | 3 | baseline evidence only |
| current Codex capability-gated ATP | 0 | 0 | 0 | unavailable 1회 뒤 blocked |
| logical environment subscription | 1 | logical await 1 | 0 | completion 두 개를 batch 하나로 전달 |

Current Codex의 0회는 workload 완료나 실제 latency/token 개선 측정이 아니다. Unsupported adapter가 forbidden polling을 시작하지 않았다는 correctness assertion이다. Logical mode의 token/latency와 steering latency는 host 미구현이므로 `null`이며, 임의 수치로 채우지 않는다.

## 호환성과 보존 규칙

- Report schema는 v2 그대로이며 optional lifecycle field는 기존 네 개다.
- Scheduling capability gap은 `environment_state_unknown`, failure, interruption, retry/fallback 또는 authority revocation을 합성하지 않는다.
- Explicit `failed|interrupted` 뒤 사용자 승인형 recovery, completion race, clean retry identity와 cap을 보존한다.
- Read-only result acceptance와 write ownership은 gap에서 보존된다. 선행 철회 없는 뒤늦은 completion은 정상 후보이며 late completion이 아니다.
- 실제 authority 철회 뒤 old completion만 quarantine하고, write scope의 실제 late disk write만 dependency closure를 pause한다.
- `approval_required`는 state를 보존하고 사용자 relay로 연결하며 자동 recovery를 열지 않는다.

## 검증 상태

| 항목 | 상태 | 비고 |
|---|---|---|
| 구현 worker 정적 점검 | pass | `git diff --check`, Python reference-count 점검, `pyright tests/lifecycle-contract/validate.py` 0 errors/warnings |
| Scheduling fixture/validator 구현 | pass | 독립 verification-advisor 실행 완료 |
| 전체 lifecycle contract validator | pass | exit 0, `PASS: environment-authoritative lifecycle contract and compatibility fixtures` |
| Report v2 compatibility gate | pass | legacy/current fixture와 optional lifecycle field 정확히 네 개를 전체 validator가 확인 |
| JSON/diff/relative links/index/§N/catalog/manifest | pass | base 4×2.13.0, add-on 2×2.3.0, `.agents` versionless 포함 |
| Active runtime no-timeout/Codex gap scan | pass | active scope에 `wait_agent`/`timeout_ms` 0; appendix는 disabled와 no timed fallback 유지 |
| Source agent-spec dry-run | pass after fixes | 초기 C1~C4 검출 후 requested/effective mode, research write allowlist, scheduling return fields, preallocated report identity를 보정하고 재실행 PASS |
| L2 external contract | skipped | 외부 의존 없음; disabled adapter의 runtime timed-wait probe는 금지 |
| Current Codex end-to-end event-driven wake | unsupported | host capability gap; ATP 검증 항목으로 PASS 처리하지 않음 |

독립 검증의 overall 판정은 pass이고 rollback signal은 없다. Runtime host probe는 수행하지 않았다. Current Codex formal adapter가 unsupported/disabled이며 timed wait probe가 금지되므로, 정적 capability 계약과 결정론적 fixture가 권위 검증 경로다.

후속 source-spec dry-run도 agent spawn과 wait/list/status API 없이 현재 source definition을 simulation했다. 수정 후 current Codex unsupported path와 hypothetical all-supported path, report v2 분리, approval/failure/completion-race/late-completion 계약이 모두 PASS했다. Installed cache 2.12.0은 stale하므로 2.13.0 installed-agent smoke 결과로 사용하지 않았다.

## 관련 문서

- [ADR-0021](../adr/ADR-0021-environment-owned-wait-wakeup-scheduling.md)
- [환경 권위 lifecycle과 wait/wakeup architecture](../architecture/environment-authoritative-subagent-lifecycle-design.md)
- [2.12.0 lifecycle change](./2026-08-12-environment-authoritative-subagent-lifecycle.md)
- [release checklist §10](../development/release-checklist.md#10-environment-authoritative-subagent-lifecycle-계약)
