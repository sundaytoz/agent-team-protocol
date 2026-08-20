---
name: task
description: 에이전트 팀(Orchestrator + Advisor + Worker) 모드로 진입해 요청을 처리. 자동 적용되지 않고 사용자가 명시적으로 `/task [요청]` 으로 호출해야 진입한다.
trigger: /task
---

# /task

이 명령이 호출되면 메인 에이전트는 **Orchestrator** 역할로 전환된다. 이 역할 규약은 `${CLAUDE_PLUGIN_ROOT}/docs/development/agent-team-protocol.md` 를 권위 레퍼런스로 한다.

## 사용법

```
/task                  # 인자 없음 — 사용자 요청 본문을 이 세션의 직전 메시지에서 수렴
/task <요청 본문>      # 인자로 작업 요청을 바로 전달
```

## Orchestrator 진입 절차

### 0. init 가드 (비차단)

`${CLAUDE_PROJECT_DIR}/docs/development/verification-strategies.md` 존재를 확인한다. 없으면 "먼저 `/atp:init` 실행을 권장합니다(아직 docs 골격이 없습니다)." 1줄을 안내하고 **계속 진행**한다 — 차단하지 않는다.

### 0.25 host orchestration skill과 execution mode preflight

이 단계는 §0 init 가드 직후 실행한다. Host-specific agent 기능을 사용하기 전에 적용 가능한 host orchestration skill을 선택하고 **전체 지침**을 읽는다. 이어서 `platform-adapters.md` §3.2~§3.3과 선택한 skill의 배포된 capability profile로 topology와 execution mode를 확정한다. 이 판정을 위해 소비 프로젝트 task마다 임시 child, 시간 기반 진단, 반복 상태 조회, maintainer validation 또는 source/install 비교를 실행하지 않는다.

선택한 host orchestration skill의 capability profile과 result collection 계약을 실행 중 관측의 임의 추론으로 덮어쓰지 않는다. Host-specific skill이 제공하는 managed orchestration을 generic polling보다 우선한다. **첫 advisor를 포함해 어떤 child도 spawn하기 전에** skill 전문 로드와 mode 선택을 끝낸다.

동시에 요청을 다음 두 intent 중 하나로 분류한다.

- `general_task`: `$atp:task`로 팀 작업을 요청했지만 실제 독립 subagent/advisor 의견 자체가 필수 산출물은 아님
- `explicit_subagent_required`: "실제 subagent 의견", "advisor에게 물어봐", "Blue/Red 독립 검토"처럼 child가 수행했다는 사실과 독립성이 요구사항임

다음 우선순위로 mode를 고른 뒤 §0.5부터 계속한다.

1. formal capability 12개가 전부 `supported` → `environment_subscription`. 기존 Tier A/A-flat 경로와 timeout-free scheduling을 그대로 사용한다.
2. formal adapter가 불완전하지만 선택한 host skill이 `host_managed_subagent_orchestration: supported`를 보장 → `host_managed_subagent_orchestration`. Child spawn을 허용하고 §5.3의 managed result barrier를 사용한다.
3. 두 orchestration mode가 모두 불가이고 `general_task` → `tier_b_sequential`. 사용자 선택을 기다리지 않고 자동 격하하며 "Tier B 격하 모드 — 병렬 advisor 미사용, 순차 self-checklist 수행"을 1줄 고지한다.
4. 두 orchestration mode가 모두 불가이고 `explicit_subagent_required` → `blocked_explicit_independence`. §0.5~§3의 세션 기록까지만 만든 뒤 child identity·authority·write ownership·spawn 0건으로 `지원 host에서 재실행 | 독립성 없는 Tier B로 명시 전환 | 취소`를 제공한다.

선택 결과는 공유 상태 생성 뒤 `wait-wakeup-events.jsonl`의 `await_capability_checked`에 `formal_adapter_enabled`, `host_managed_subagent_orchestration`, `selected_mode`, capability profile ref를 기록한다. 두 orchestration mode가 모두 unavailable일 때만 `wait_wakeup_capability_unavailable`을 정확히 1회 추가한다. `tier_b_sequential` 결과를 advisor/subagent 의견으로 표현하지 않는다.

### 0.5 1회성 마이그레이션 체크 (atp:migrate 블록 실행)

`§0.25 execution mode preflight`가 mode를 선택한 뒤, `§1 프로토콜 로드` 진입 전에 아래를 1회 수행한다.

프로젝트 루트의 지침파일(자기 호스트의 규약 파일을 1순위로, 호환 후보 집합은 init SKILL §2 `detect_guidance_files` 와 동일 — 존재하는 것)을 확인해 `<!-- atp:migrate:begin -->` 마커가 있으면:

1. **디렉토리 이관 (비파괴)**: `.claude/work-session` 이 존재하고 `.atp/work-session` 이 없으면 `mkdir -p .atp && git mv .claude/work-session .atp/work-session`(git 미추적 환경이면 `mv .claude/work-session .atp/work-session`). 둘 다 존재하면(부분 이관) `.claude/work-session/` 내 각 sid 를 `.atp/work-session/` 로 mv 병합(동명 sid 는 덮어쓰지 않음). 구 디렉토리 미존재면 no-op. **삭제 아님 — 이동.**
2. **`.gitignore` 추적 보장**: `.atp/work-session/` 라인이 **있으면 1줄 제거**(없으면 no-op) — work-session 은 git 추적이 기본(ADR-0010). 구경로 `.claude/work-session/` 라인은 유지.
3. **블록 자기삭제**: 위 1~2 가 모두 성공(또는 no-op)한 경우에만, 존재하는 각 지침파일에서 `<!-- atp:migrate:begin -->` ~ `<!-- atp:migrate:end -->` 구간을 in-place 삭제한다. 1~2 중 mv 실패 시 블록을 남기고 1줄 경고만 출력.
4. **고지 (조건부)**: **실제 디렉토리 이관이 1건 이상 발생한 경우에만** "ATP 경로 마이그레이션 1회 완료 — `.claude/work-session/` → `.atp/work-session/` 이관 + atp:migrate 블록 제거됨" 을 1줄 출력한다. 이관 0건(이미 이관됨 / 구 디렉토리 미존재)으로 **블록 삭제만 수행**한 경우 고지 없이 조용히 진행한다 (이미 마이그레이션된 환경에서 매 세션 노이즈 회피).

마커가 없으면 이 절 전체를 즉시 skip 하고 §1 로 진행한다.

> 이 작업은 멱등하다. 이미 이관됐고 블록만 남았다면 1~2 는 no-op, 3(블록 삭제)만 수행하며 고지 없이 조용히 진행한다(점4).
> 비파괴: 모든 디렉토리 조작은 mv/이동. 삭제 0건.

### 1. 프로토콜 로드

진입 시 다음 문서의 **코어 구획만** Read 하여 세션 컨텍스트에 상주시킨다:

- `${CLAUDE_PLUGIN_ROOT}/docs/development/agent-team-protocol.md`
  의 `<!-- atp:core:begin -->` ~ `<!-- atp:core:end -->` 구획
  (역할정의·호출불변·§6 파괴적 게이트 압축형·항상적용 체크리스트·라우팅 인덱스)

전문(全文)은 로드하지 않는다. 코어 구획의 **라우팅 인덱스 표**가 작업
성격별로 추가 Read 할 §섹션을 가리킨다. orchestrator 는 작업을 분류한 뒤
해당 트리거 행의 **대상 §헤더를 `grep` 으로 위치 확정한 후 그 지점부터 Read**
한다 (표의 offset 힌트는 편의값이며 본문 편집 시 드리프트할 수 있으므로
§헤더가 정본). 마이크로 편집은 코어만으로 진행 — 전문 로드 0.

게이트(§6)·세션 종료조건(아래 §9)·호출 불변규약은 코어에 상주하므로
"안 불러와서 누락" 되지 않는다.

그 외 참조가 필요할 수 있는 문서 (Read 는 필요 시):

- `${CLAUDE_PROJECT_DIR}/docs/development/verification-strategies.md`
- `${CLAUDE_PROJECT_DIR}/docs/index.md` (docs-first)

### 2. 공유 상태 디렉토리 생성

```
${CLAUDE_PROJECT_DIR}/.atp/work-session/<sid>/
```

`sid` = `YYYYMMDD-HHMMSS` (프로젝트 타임존 기준). Orchestrator 가 Bash 로 디렉토리를 멱등 생성:

```bash
mkdir -p ${CLAUDE_PROJECT_DIR}/.atp/work-session/<sid>/{research,implementation,artifacts}
```

**재개 규약**: 동일 sid 디렉토리가 이미 존재하면 이어쓰지 않고 새 sid 로 시작하되 `report.md` 에 `resumed_from: <이전 sid>` 필드를 기록한다. 이전 보고서의 미완료 섹션은 링크만 남기고 이번 세션에서 재수행.

### 3. report.md 초기화

해당 디렉토리에 `report.md` 를 프로토콜 §8 스키마(현행 `schema_version`)로 생성. 최초엔 헤더 + `user_request` + `Invocations: []` 만. 조사·고찰 전용(코드 변경 0 예상) 세션은 §8 경량 프로파일(`profile: research-lite`)로 시작할 수 있다 — 코드 변경이 1줄이라도 생기면 풀 스키마로 승격.

생성 직후 **Advisor Invocation Decision Log** 섹션을 함께 둔다:

```yaml
# Advisor Invocation Decision Log
# 각 advisor 호출/스킵 판단 즉시 1줄 append
```

이후 각 advisor 의 호출/스킵을 결정하는 **시점에 즉시** 다음 형식으로 append 한다 (회고 시점까지 미루지 않는다):

```yaml
- advisor: <name>
  decision: call | skip
  rationale: '<판단 근거 1줄>'
  checked_at: <iso>
```

skip 판단도 반드시 기록한다 — 어떤 advisor 를 왜 거치지 않았는지가 세션 추적·회고의 입력이 된다.

### 4. 요청 해석

- §0.25에서 수렴한 `user_request`, `general_task | explicit_subagent_required` intent와 `selected_mode`를 그대로 사용한다.
- `tier_b_sequential`이면 자동 격하와 고지 사실을 `Decisions`에 기록하고 advisor 호출은 만들지 않는다. 사용자가 명시 전환한 경우에는 concrete message ref도 함께 기록한다.
- `blocked_explicit_independence`이면 세션 기록 뒤 advisor 호출 계획으로 진행하지 않고 사용자 선택을 기다린다.

### 5. Advisor 호출 계획 수립

#### 5.0 계획 가시성 의무 (skip 기준에 우선) — 코드 작성 전 절대 단계

`/task` 진입 = "계획을 보여주고 동의받은 뒤 구현해 달라" 는 의도. 아래 skip 기준이 모두 충족되더라도 **첫 코드 변경 전에** 다음 중 하나로 사용자 동의를 받는다:

- (a) `ExitPlanMode` — 계획서(problem framing + 접근 + 영향 파일 + 검증 전략) 작성 후 승인
- (b) `AskUserQuestion` — 결정 축이 단일·이산이면 짧은 framing + Recommended 옵션 + 탈출구
- (c) inline 요약 + "이대로 진행할까요?" — 옵션 분기 없는 가장 가벼운 형태

**면제**: 사용자 명시 skip 지시("그냥 해", "advisor 없이", "간단히") 가 동일/직전 발화에 포함되거나, 1줄 마이크로 편집(신규 로직 0줄)인 경우.

requirements/design-advisor 산출물은 파일로만 존재 — 사용자는 자동으로 보지 못한다. orchestrator 가 핵심 결정을 전달할 책임을 진다. **옵션 공간이 닫혀있다는 orchestrator 사전 판단은 면제 사유가 아니다** (옵션 공간은 design 산출 이후에만 평가 — 프로토콜 §1). 이 절은 §5.1 정량 skip 기준보다 우선한다. 상세는 프로토콜 §1. **research 가 세션 초반 가정을 뒤집으면 설계 진입 전 plan 게이트를 1회 추가한다**(반전 요약 + 옵션 + Recommended + 근거 — 프로토콜 §2.7).

#### 5.1 Advisor 호출 흐름

§0.25에서 `tier_b_sequential`이 선택됐다면 이 절의 advisor 호출 계획과 모든 advisor `call` 결정을 실행하지 않는다. 각 phase를 `platform-adapters.md` §5 순차 self-check로 수행하고, "advisor가 검토했다" 또는 "독립 의견"으로 표현하지 않는다.

원 요청을 훑고 어떤 advisor 를 어떤 순서로 호출할지 결정한다. 일반적 흐름 (생략 가능):

```
requirements-advisor
  → graphify-lookup-advisor → (miss 시) research-advisor
  → design-advisor
  → implementation-advisor
  → verification-advisor
  → documentation-advisor
  → (대규모 구조 변경 시) graph-refresh-checker → graphify-update-advisor
  → retrospective-advisor
```

**스킵 기준**:

- 요구가 명확하면 requirements 스킵
- 기존 문서로 충분하면 research 스킵
- 마이크로 편집(한 파일 몇 줄) 은 **advisor 전체 스킵 + orchestrator 직접 수행** 허용 (프로토콜 예외 조항)
- 설계 산출물이 **파일 영향 맵 + 계약 + 시퀀스** 까지 확정적이면 `implementation-advisor` 스킵 + orchestrator 직접 구현 허용

**스킵 불가 (항상 실행)**:

- **verification-advisor / 통합 검증 스크립트** — 코드 변경이 1줄이라도 있으면 반드시 세션 종료 전에 통과해야 한다. 마이크로 편집이라도 예외 없음.
- **버그 수정 시 회귀 테스트** — 수정 전에는 실패하고 수정 후엔 통과하는 테스트를 같은 커밋에 포함. `verification-strategies.md` 의 "버그 범주 → 적용 L 레벨" 표 준수.

**Worker 계층**: 파일 단위 분할·동시 수정 방지·파일 소유권 맵은 `implementation-advisor` 책임. 상세는 프로토콜 §7. SKILL 본문에서 반복하지 않음.

**병렬 호출**: 독립 advisor (예: `research-advisor` 내부 `parallel-explorer`) 는 병렬 실행이 기본. orchestrator 가 상위 advisor 여러 개를 동시 호출하는 것은 컨텍스트 오염 리스크로 기본 금지. 자세한 규약은 프로토콜 §2.

#### 5.2 환경 권위 호출 lifecycle과 유한 복구

모든 advisor/worker invocation 을 만들 때 프로토콜 §2.5의 lifecycle 기록을 함께 초기화한다. 최소한 logical task, invocation identity, `attempt`, 시작 시각, host의 status/approval/termination/isolation capability와 clean-retry 상한을 `report.md` 또는 연결된 진단 artifact에 기록한다. lifecycle 상태는 host environment가 명시적으로 제공한 상태와 이벤트만 정규화한다.

Advisor spawn 전 orchestrator는 해당 advisor의 report-domain `report_invocation_id`를 미리 할당해 advisor 입력에 주입한다. 입력에 없으면 orchestrator가 새 unique value를 할당한 뒤에만 spawn하며, advisor는 이 exact value를 자기 scheduling row의 `owner_report_invocation_id`와 nested worker payload의 `parent_invocation_id`로 사용한다. Environment invocation identity로 대체하거나 advisor가 report에서 current row를 추정하게 하지 않는다.

- environment가 `queued` 또는 `running`을 보고하는 동안 ATP도 그 상태를 유지한다. wait timeout, 경과 시간, 동일 snapshot 반복, output/progress/tool event의 존재나 부재는 상태 전이·failure·retry/fallback 권한을 만들지 않는다.
- `completed`는 result 계약 검증·취합, `failed`는 원인 보고 후 recovery 검토, `interrupted`는 partial write와 ownership 확인으로 연결한다. environment의 `approval_required`는 retry/fallback 승인으로 간주하지 않는다. observed state와 relay/continuation capability는 별도 축이므로 relay/control 미지원이어도 child는 `approval_required`로 보존한다. environment provenance·두 identity·concrete `source_ref`·concern/capability evidence·ledger를 반환하고 child는 `ended_at: null`, termination 생략으로 두며 mutation은 0건이다. relay 가능한 ancestor에 control을 반환하고 root까지 불가하면 report의 `Summary` / `Open Items` / `concerns` narrative에만 phase `blocked`를 남긴다. capability 복구 뒤 같은 environment invocation/identity를 continuation하며 `attempt`와 retry accounting은 그대로 유지한다. 후속 status API unavailable/error event가 실제 관측된 경우에만 `environment_state_unknown`으로 전이한다.
- environment status API가 unavailable/error이거나 의미가 불명해 authoritative status를 얻을 수 없을 때만 `environment_state_unknown`으로 기록한다. 이를 stall/failure로 재분류하거나 자동 interrupt, retry, fallback의 근거로 사용하지 않는다.
- 명시적 terminal failure, interruption, environment blocker 또는 사용자 취소가 recovery 검토를 열어도 **사용자 확인 전 interrupt, retry, fallback 실행은 0건이어야 한다.**
- read-only invocation은 `result acceptance authority`를, write-capable invocation은 `write ownership`을 가진다. 사용자 retry 승인과 completion race 재확인 전에는 어느 authority도 철회하지 않는다.
- 사용자가 clean retry를 승인하면 completion race를 먼저 재확인한다. 기존 invocation이 완료됐으면 재시도를 취소하고 기존 결과를 정상 후보로 검토하며 authority 철회와 `late_completion`을 만들지 않는다.
- read-only recovery가 계속되면 host termination control을 먼저 사용한다. termination control이 없더라도 read-only 성질과 old identity를 확인할 수 있으면 11개 공통 ledger 필드와 `scope`/`rationale`/`source_ref`를 가진 advisor event `result_acceptance_revoked`로 future result acceptance만 ATP-local하게 격리한다. 이 event 뒤에만 **새 invocation identity**를 호출하며 environment terminal은 추론하지 않는다.
- write-capable recovery는 termination/write isolation, partial write 분류, ownership 회수를 확인한 뒤에만 새 identity로 handoff한다. read-only result quarantine은 write isolation을 대체하지 않는다. 같은 invocation에 보내는 follow-up은 진단/상태 확인일 뿐 clean retry가 아니며 `attempt`를 증가시키지 않는다.
- environment의 old `completed`는 권위 event로 별도 기록한다. 같은 old identity의 result acceptance authority 또는 write ownership이 먼저 철회·격리된 경우에만 `authority_kind`/`authority_ref`를 phase ledger에 둔 advisor `late_completion` disposition으로 격리한다. read-only와 write/no-disk late result는 quarantine-only이며 자동 merge·취합·성공 판정·ownership pause가 0건이다. 실제 late disk write만 affected scope와 dependency closure를 persisted `paused`로 만든다.
- 승인된 clean retry가 명시적 terminal failure로 끝나고 retry 상한에 도달하면 반복 재호출을 멈추고 §2.5 phase criticality에 따라 skip, Tier B self-check/direct 수행, 사용자 결정 또는 blocked 중 하나로 종결한다. write-capable·destructive scope는 termination/isolation을 확인할 수 없으면 같은 scope를 재호출하지 않는다.

`attempt`, `termination`, `retry_of`, `lifecycle_fallback_reason`은 §8의 optional lifecycle 필드에 기록한다. lifecycle 복구 사유는 모델 라우팅용 `model_choice.fallback_reason`과 분리하며, lifecycle 장애를 이유로 §5.7 모델 선택 의미를 변경하지 않는다.
신규 abnormal producer의 `lifecycle_fallback_reason`은 첫 serialization(`failed|interrupted|late_completion`)부터 `cause=<failed|interrupted|late_completion>@<concrete source_ref>; disposition=<awaiting_user_decision|approved_clean_retry|phase_fallback|blocked|late_completion_quarantined>; rationale=<non-empty summary>`를 기록한다. failed/interrupted 중간 invocation도 retry 소진을 기다리지 않고 현재 recovery disposition을 쓰며, decision이 바뀌면 같은 row의 disposition을 갱신하고 provenance history는 phase ledger에 보존한다. `completed`는 reason null/생략 가능하고 nonterminal은 `ended_at: null`, termination 생략, reason null/생략이다. 이는 기존 string 필드의 producer form이며 report v2 optional lifecycle 필드 네 개를 늘리지 않는다.

**verification 불변식**: code 변경이 있으면 verification advisor의 명시적 실패나 interruption도 skip 사유가 아니다. Tier B로 동일 통합 검증을 직접 실행하거나 요구되는 검증을 수행할 수 없어 `blocked`로 끝내며, 기존 L2 허용 규칙 밖의 `needs_user_verification`으로 대체하지 않는다.

#### 5.3 negotiated result collection

§0.25의 `selected_mode`에 따라 대기 방식을 분기한다. Lifecycle 판정은 어느 mode에서도 §5.2의 environment-authoritative 규칙을 그대로 따른다.

- `environment_subscription`: 프로토콜 §2.5의 `await_invocations`를 사용한다. 관심 identity, `condition: any | all`, 정확한 `wake_on` 집합을 등록하고 timeout-free suspend·deduplication·coalescing·compact delta 계약을 유지한다. 등록 직전 formal capability 12개를 재확인한다.
- `host_managed_subagent_orchestration`: 선택한 host orchestration skill의 managed result barrier를 사용한다. 요청한 모든 child의 terminal result가 도착한 뒤에만 검증·취합하며 generic polling을 추가하지 않는다. 실제 nonterminal update가 전달되면 invocation을 `running`으로 유지하고 completion, retry/fallback 또는 authority·ownership mutation을 만들지 않는다.
- `tier_b_sequential`: child가 없으므로 join을 호출하지 않고 §5 순차 self-check를 계속한다.
- `blocked_explicit_independence`: child와 join을 만들지 않고 사용자 선택을 기다린다.

실행 중 선택된 orchestration capability가 실제 unavailable/error로 바뀌면 child의 마지막 environment-authoritative state, result acceptance authority와 write ownership을 보존하고 추가 spawn·automatic retry/interrupt/fallback을 0건으로 둔 채 phase를 blocked로 반환한다. Automatic Tier B 전환으로 독립 실행 요구를 숨기지 않는다. Status API unavailable/error가 별도로 관측되지 않았다면 `environment_state_unknown`이나 `lifecycle_fallback_reason`을 합성하지 않는다.

Scheduling ledger의 허용 event vocabulary는 정확히 `await_capability_checked | await_registered | wake_batch | wait_wakeup_capability_unavailable | external_continuation_selected | measurement` 여섯 개다. `await_capability_checked`에는 `formal_adapter_enabled`, `host_managed_subagent_orchestration`, `selected_mode`를 기록한다. `await_registered`/`wake_batch`는 formal `environment_subscription`에만 사용한다. Managed `measurement`는 `requested_agents`, `spawn_calls`, `nonterminal_updates`, `terminal_deliveries`, `collected_results`, generic wait/list/interrupt와 semantic recovery action의 실제 관측값을 기록하며 알 수 없는 telemetry는 `null`로 둔다. `wait_wakeup_capability_unavailable`은 두 orchestration mode가 모두 불가하거나 선택된 mode가 runtime에서 사라진 경우에만 phase당 정확히 1회 기록한다. 명시적 `failed | interrupted` 뒤의 사용자 승인형 recovery, completion race, retry identity, result acceptance, write ownership, late completion 규칙은 §5.2 그대로다.

### 6. 각 호출에 모델 override

프로토콜 §5 루브릭으로 판단 천장(tier: `small` / `medium` / `large`)을 평가한 뒤 호스트 CLI 의 per-call override 문법으로 지정한다(tier→슬러그 매핑 원칙: platform-adapters §6 — 호스트가 자기 라인업·자기 override 문법으로 해석한다. 생략 시 parent 상속).

- **effort** (§5.5): 직교 노브 — 미지원 플랫폼은 no-op.
- **cap** (§5.6): orchestrator 자기 tier 를 초과하는 지정 금지 — 초과 산출 시 자동 clamp + `capped`/`capped_from` 기록. 자기 tier 판정 불가 시 override 미지정(parent 상속).
- **host 전용 optional route**: platform-adapters §7.1 appendix 는 해당 host 일 때만 Read. route 불가/미지원/실패 시 기존 tier 매핑으로 fallback 하고 `fallback_reason` 기록.

근거 한 줄을 `report.md` 의 `invocations[].model_choice.rationale` 에 기록 (스키마 전체: 프로토콜 §5.8).

### 7. 충돌 중재

advisor 산출물의 `concerns` 필드 교차 검사. 프로토콜 §4 절차 준수. 1라운드 실패 시 사용자에게 `AskUserQuestion`.

### 8. 파괴적 조작 게이트

프로토콜 §6 에 해당하는 조작은 orchestrator 가 사용자 확인 후에만 실행. Advisor/Worker 가 직접 수행 금지.

**게이트 통과 후 검증 실패 시 롤백**: 파괴적 조작이 사용자 승인 후 실행되었고 후속 검증이 실패하면 orchestrator 가 **즉시** 되돌리기를 시도한다 — `git revert`, 파일 복원, migration down 등. 자동 복원이 불가능한 영역(외부 서비스 상태 변경·공개 게시 등) 이면 `needs_user_verification` 에 수동 복구 단계를 명시하고 세션을 닫지 않는다.

### 9. 세션 종료

**종료 조건 (의무)**:

1. **통합 검증 스크립트 통과** — L1 pass, L2 는 pass 또는 skip(원격/seed 미지정). L2 실패 상태에서 세션 종료 금지.
2. 보고서의 "verified_by_me" 섹션에 실제로 통과한 단계를 나열:
   - `L1: typecheck / unit+regression`
   - `L2: contract-<외부 의존> (pass | skipped:<reason>)`
   - 로그 스캔: `clean | warn:<n>건`
3. 보고서의 "needs_user_verification" 섹션에 사용자 손으로 해야 할 것 명시 (실제 사용자 환경 스모크 1회 등). 없으면 "(없음)".
4. **`graph-refresh-checker` 호출 + 판정 기반 처리** — 코드 변경이 1줄이라도 있으면 예외 없이 실행. **판정 결과는 본 세션 또는 commit 시점에 처리하며 다음 세션으로 이월하지 않는다**(no-defer 정책 — 상세 경로·처리 표는 add-on 의 `graphify-usage.md`). **단 이 graphify 단계 전체는 옵트인 `atp-graphify` add-on 이 enable 된 경우에만 실행**한다. add-on 미설치면 graphify 에이전트 이름이 해소되지 않으므로 이 단계를 "skip: no-graphify" 로 기록하고 차단 없이 계속 진행한다. 판정별 필수 후속:
   - `fresh` → 후속 없음. 보고서 "graph_refresh" 섹션에 `fresh` 기록.
   - `partial-stale` → 해당 scope 만 `/graphify <대상경로>` 재생성. `${CLAUDE_PROJECT_DIR}/docs/graph/index.md` frontmatter + Scopes 표 갱신.
   - `fully-stale` → 영향 scope 전체 `/graphify` 재생성. 메타 갱신.
   - `no-graph` → 코드베이스가 비어있지 않다면 **세션 내에서 최초 생성**. `/graphify <주요 경로>` 실행 + 메타 작성.
   판정 결과와 수행한 처리는 보고서 "graph_refresh" 섹션에 한 줄 기록 (예: `partial-stale → src scope 재생성 완료`). graphify 가 도입되지 않은 프로젝트에선 이 단계 전체를 "skip: no-graphify" 로 기록.
5. **`git status` 확인** — 미커밋 잔여(tracked 변경·untracked 파일) 가 있으면 (1) 이번 작업 단위에 속하면 프로젝트의 커밋 정책(CLAUDE.md) 에 따라 커밋/push, (2) 속하지 않으면 `report.md` 의 `open_items` 에 파일 경로·상태를 명시. 커밋되지 않은 잔여를 남긴 채 retrospective 로 넘어가지 않는다.
6. **프로젝트 정의 종료/배포 게이트 hook** — 프로젝트가 `${CLAUDE_PROJECT_DIR}/docs/development/verification-strategies.md`(또는 `CLAUDE.md`) 에 추가 종료 게이트(예: 런타임/배포 후 동작 확인)나 프로젝트 전용 advisor(예: 배포 판정 advisor) 를 정의했으면 orchestrator 가 세션 종료 전 실행한다. 코드 단위 검증(L1/L2) 통과와 **별개로** 동작한다. 정의가 없으면 보고서에 "skip: no-project-gate" 로 기록. 자동 실행이 불가능한 환경(CI·원격 호스트·sandbox) 이면 `needs_user_verification` 에 명시 단계(명령 + 확인 항목) 를 적고 "프로젝트 게이트 미수행" 사유를 보고한다. 게이트 통과 후 검증 실패가 push 이후 단계면 §8 롤백 절차를 따른다.

그 외:
- **retro 호출 전 orchestrator 가 `user_signals` 기록**: 세션 중 사용자 발화에서 감지한 부정 시그널("왜 안 했어?", "또야?", "틀렸어") 과 긍정 시그널("좋더라", "그거 맞아", 한 번 만에 수락) 을 `report.md` 의 `user_signals.{positive|negative}` 에 한 줄씩 인용·요약. 구조적 허점이면 `negative[*].structural: true`. 한쪽이 없으면 빈 리스트.
- 모든 advisor 산출이 수렴 + verification pass 면 retrospective-advisor 호출 (기록된 `user_signals` 를 입력으로). **호출 전 전제**: `report.md` 의 `Summary` / `Invocations` / `Decisions` 세 섹션이 최소 1줄 이상 채워져 있어야 함. 빈 Summary 로 회고를 돌리면 입력 품질이 무너진다. **회고 산출 sink 는 `report.md` 의 `Retrospective` 섹션이다 — 별 파일(`retrospective.md` 등) 산출을 요구하지 않는다**(advisor 의 `Write` 미보유는 프로토콜 §12 "권고만" 설계의 의도된 제약). 산출물 유무는 그 섹션으로만 판정한다.
- 회고 결과의 `memory_candidates`(교훈 후보) 검토 후 orchestrator 가 수용 여부 결정. **docs-first**: 수용한 교훈은 `docs_sync_target` 경로(`CLAUDE.md` / `docs/development/*.md` / ADR 등) 에 **같은 커밋으로 기재하는 것을 기본**으로 한다. **memory 기록은 사용자의 memory 설정을 존중** — 사용자가 memory 를 활성화한 경우(`memory_optional: true` 후보)에만 보조로 갱신하고, 비활성/미설정이면 docs 단독으로 마감하며 memory 기록을 강제하지 않는다. `signal_source: negative` 뿐 아니라 `positive` 후보도 동등하게 검토 (비자명한 판단이 검증된 경우).
- **종료 serialization 순서**: 모든 요청 child terminal result 수신 → 결과 계약 검증·통합 → verification → retrospective → retrospective 결과를 report에 반영 → report 재스테이징 → staged 상태 재검증 → 요청 범위 mutation/commit/push/remote verification 완료 → session `ended_at` 기록 → report 형식 최종 read-only 검증 → 사용자 최종 응답. 미래 `ended_at`을 앞선 단계에서 미리 쓰지 않는다.
- 커밋/push 는 프로젝트 커밋 정책과 위 순서에 따라 작업 단위 끝에서 진행

## system-reminder 수신 시 행동 원칙

- `system-reminder` 수신 시 진행 중인 툴 호출·응답 준비를 완료한 뒤 reminder 내용을 반영한다. 상세 규약: `agent-team-protocol.md` §2.4.
- reminder 가 작업 전제 자체를 뒤집는 경우에만 `AskUserQuestion` 으로 사용자에게 명시적으로 알리고 합의 후 방향을 전환한다.

## 명시적 비활성 경로

사용자가 세션 도중 "팀 거치지 말고 직접 해", "advisor 없이", "간단히" 같은 지시를 내리면 orchestrator 는 advisor 호출을 스킵하고 직접 처리한다. `/task` 로 진입했더라도 예외 모드로 전환 가능.

## 금지

- `/task` 를 부르지 않았는데 팀 모드로 진입하는 것 (자동 적용 아님)
- 프로토콜 문서를 읽지 않고 팀 작업 시작
- `${CLAUDE_PROJECT_DIR}/.atp/work-session/` 디렉토리 없이 보고서 누적

## 관련

- `${CLAUDE_PLUGIN_ROOT}/docs/development/agent-team-protocol.md` (atp 플러그인 번들 레퍼런스)
- `${CLAUDE_PROJECT_DIR}/docs/development/verification-strategies.md` (소비 프로젝트 — `/atp:init` 이 생성)
