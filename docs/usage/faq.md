---
kind: usage
title: 문제 해결 / FAQ
description: plugin 설치·init·사용 중 흔한 문제와 대응.
owner: template-maintainer
stability: living
last_reviewed: 2026-08-20
---

# 문제 해결 / FAQ

plugin 설치·초기화·일상 사용 중 자주 마주치는 질문을 모았다. 초기 설정 절차는 [setup-checklist.md](./setup-checklist.md) 를 먼저 참고한다.

---

## 설치 / 마켓플레이스

### Q. `/plugin marketplace add sundaytoz/agent-team-protocol` 이 실패한다.

A. 다음을 순서대로 점검한다.

1. 네트워크 연결 및 GitHub 접근 가능 여부 확인.
2. `sundaytoz/agent-team-protocol` 레포가 public 인지 확인.
3. Claude Code 버전이 플러그인 마켓플레이스를 지원하는 버전인지 확인.

마켓플레이스 add 가 성공하면 이후 `atp@agent-team-protocol` 으로 install 한다.

### Q. `atp` 플러그인과 `atp-graphify` 플러그인을 각각 install 해야 하나?

A. 예. 두 플러그인은 별개 컴포넌트다.

- `/plugin install atp@agent-team-protocol` — **base (필수)**. agents 10개 + skills(task, init) 번들.
- `/plugin install atp-graphify@agent-team-protocol` — **graphify add-on (옵트인)**. graphify agents 3개 + graphify-usage.md 번들. base atp 설치 후 선택적으로 추가.

---

## /atp:task · 네임스페이스

### Q. `/atp:task` 명령이 안 보인다 / 인식되지 않는다.

A. 다음을 확인한다.

1. **마켓플레이스 add** 가 완료됐는가? (`/plugin marketplace add sundaytoz/agent-team-protocol`)
2. **plugin install** 이 완료됐는가? (`/plugin install atp@agent-team-protocol`)
3. 새 Claude Code 세션을 시작했는가? (install 후 세션 재시작 필요)
4. plugin 이 **enable** 상태인가? (`/plugin list` 로 `atp` 상태 확인)

### Q. `/task` 로 입력해도 되는가? 네임스페이스가 혼동된다.

A. `/atp:task` 를 사용해야 한다. 플러그인은 `atp:` 네임스페이스로 노출된다. `/task` 는 다른 플러그인 또는 직접 정의된 커맨드가 없는 한 작동하지 않는다.

---

## /atp:init · 초기화

### Q. `/atp:init` 을 실행했는데 `docs/` 디렉토리가 생성되지 않았다.

A. init 은 `${CLAUDE_PROJECT_DIR}` 기준으로 아래 항목을 생성한다.

- `docs/index.md` + 카테고리 index 13개
- `docs/development/verification-strategies.md`
- `docs/development/document-category-classification.md`
- `docs/graph/` 골격

init 실패의 주요 원인:

1. `atp` plugin 이 제대로 install·enable 되지 않은 상태에서 `/atp:init` 호출.
2. 프로젝트 디렉토리 쓰기 권한 부재.
3. 세션을 새로 시작하지 않고 install 직후 바로 호출.

### Q. `/atp:init` 을 재실행해도 괜찮은가?

A. 예, 멱등하다. 이미 존재하는 파일은 덮어쓰지 않고, CLAUDE.md 의 `<!-- atp:begin -->` 블록도 중복 삽입하지 않는다. 초기화 후 placeholder 를 채운 상태에서 재실행해도 변경 내용이 유지된다.

---

## graphify add-on

### Q. graphify 단계가 "skip: no-graphify" 로 기록되고 넘어간다. 오류인가?

A. 정상 동작이다. `atp-graphify` add-on 이 설치되지 않은 환경에서 base atp 는 graphify 단계를 건너뛰고 `skip: no-graphify` 로 세션 보고서에 기록한다. graphify 기능이 필요하면 `/plugin install atp-graphify@agent-team-protocol` 로 add-on 을 추가하고 새 세션을 시작한다. 상세는 `../../plugins/atp-graphify/docs/graphify-usage.md`.

### Q. graphify add-on 을 설치했는데 graphify 에이전트가 여전히 작동하지 않는다.

A. `atp` base 가 먼저 설치돼 있어야 한다. `atp-graphify` 는 `atp` 를 dependency 로 선언하므로, base 미설치 상태에서는 add-on 이 활성화되지 않는다. install 순서: base atp → atp-graphify.

---

## Codex hooks add-on

### Q. Codex 에서 atp 를 설치했는데 "Hooks need review" 가 뜬다 / 안 뜬다.

A. base `atp` 2.17.0 이후에는 hook 이 번들되지 않으므로 base 만 설치하면 뜨지 않는 것이 정상이다. 뜬다면 옵트인 add-on `atp-codex-hooks` 를 함께 설치한 경우다. 그 프롬프트는 add-on 의 8개 hook 이 trust 뒤 sandbox 밖에서 실행됨을 알리는 것이며, trust 는 명령 문자열에 묶여 이후 runner 코드 변경에도 유지된다. maintainer smoke 나 candidate 실험이 아니면 `codex plugin remove atp-codex-hooks` 로 제거한다. 상세는 [`../../plugins/atp-codex-hooks/docs/codex-hooks-usage.md`](../../plugins/atp-codex-hooks/docs/codex-hooks-usage.md).

### Q. `codex-team` 이 `skip: no-codex-hooks` 를 기록하고 spawn 0 으로 진행한다. 오류인가?

A. 정상이다. add-on 미설치면 `ATP_HOOK_GUARD_READY` marker 가 없어 candidate bounded pool 이 fail-closed 로 닫히고, `$atp:task` 는 배포 profile 이 정한 mode(현재 `tier_b_sequential`) 로 차단 없이 계속한다. add-on 을 설치해도 배포 profile(`team_execution_enabled: false`) 은 바뀌지 않는다.

## 에이전트 팀 운영

### Q. `verification-advisor` 가 통합 검증 스크립트 없다고 실패한다.

A. `/atp:init` 이 생성한 `docs/development/verification-strategies.md` 의 `cmd` 필드를 프로젝트 실제 명령으로 교체했는지 확인한다. 통합 `verify-all` 스크립트가 없다면 L1/L2 개별 `cmd` 만 유지해도 된다.

### Q. Advisor 가 서로 모순된 결정을 내린다.

A. `../../plugins/atp/docs/development/agent-team-protocol.md` §4 충돌 조정 절 참조. 각 advisor 산출물의 `concerns` 필드가 교차점. orchestrator 가 1라운드 재검토 요청 → 실패 시 사용자에게 `AskUserQuestion`.

### Q. Worker 가 담당 파일 외부를 수정하려고 한다.

A. `implementation-advisor` 의 파일 소유권 맵을 확인. 한 파일에 2개 worker 가 할당되지 않았는지 검사. Worker 가 "한계" 로 반환했다면 advisor 가 재할당한다.

### Q. 모델이 항상 large tier 만 써서 비용이 크다.

A. `report.md` 의 `invocations[].model_choice` 를 확인. `phase` / `escalation_reason` / `dispatch_size` / `capped` 가 `../../plugins/atp/docs/development/agent-team-protocol.md` §5 정책과 일치하는지 점검. `escalation_reason: null` 인데 `tier: large` 가 반복되면 orchestrator 프롬프트에 "기본 medium, §5.2 트리거 적중 시에만 large 상승" 을 명시적으로 상기시킨다. tier 는 플랫폼 중립(small/medium/large) — 실제 모델 슬러그는 `resolved_model` 로 확인한다(tier→슬러그 매핑 원칙: platform-adapters §6).

### Q. 세션이 중간에 끊겼다. 이어서 하려면?

A. 같은 `sid` 디렉토리가 이미 있어도 이어쓰지 않는다. 새 sid 로 시작하며 `report.md` 에 `resumed_from: <이전 sid>` 를 기록한다. 이전 `report.md` 에서 어느 phase 까지 끝났는지 확인하고 거기서부터 재개한다 (`../../plugins/atp/docs/development/agent-team-protocol.md` §7 재개 규약).

### Q. graphify 없이도 팀이 동작하는가?

A. 예. `graphify-lookup-advisor` 가 `no-graph` 반환하면 `research-advisor` 로 자동 에스컬레이션. 세션 종료 시 graph-refresh 단계는 "skip: no-graphify" 로 기록하고 넘어간다. 상세는 `../../plugins/atp-graphify/docs/graphify-usage.md`.

### Q. 내 프로젝트에 DB 가 없는데 `migration-writer` 가 필요한가?

A. 필요 없다. init 후 생성된 프로젝트의 에이전트 설정에서 migration-writer 관련 언급을 제거한다. tier 구조에는 영향 없음.

### Q. 테스트 명령이 여러 개인데 `verify-all` 하나로 통합하기 어렵다.

A. 통합 스크립트를 만들지 말고 `verification-strategies.md` (소비 프로젝트 `docs/development/`) 에 전략을 여러 개 등록한다. `verification-advisor` 가 변경 scope 에 매칭되는 것만 순차 실행한다.

### Q. ATP가 subagent 완료를 기다릴 때 긴 timeout이나 반복 polling을 사용하는가?

A. Formal scheduling은 timeout-free subscription만 인정한다. Formal capability 12개를 모두 제공하는 host에서는 관심 event까지 root model을 suspend하고 event deduplication, completion coalescing, compact delta, user steering과 cancellation 전달을 environment가 소유한다.

ATP는 formal capability 부족이나 managed orchestration 오류를 manual wait/list polling, automatic retry·interrupt·fallback으로 보상하지 않는다. Tested Codex CLI의 현재 상태, 일반 Tier B와 독립 subagent blocker 동작, App/IDE의 `unknown` 판정과 해소 조건은 [Known Issues](./known-issues.md)에 분리해 추적한다. 공통 lifecycle 의미는 [`agent-team-protocol.md` §2.5](../../plugins/atp/docs/development/agent-team-protocol.md), Codex mapping은 [`codex-lifecycle-routing.md`](../../plugins/atp/docs/development/codex-lifecycle-routing.md)를 본다.

### Q. Advisor가 오류 없이 `running` 상태에서 첫 활동을 보이지 않는다.

A. ATP는 host environment가 정상 API로 명시한 상태와 terminal event만 lifecycle 권위로 사용한다. environment가 `running`을 반환하는 동안 ATP도 `running`으로 유지한다. wait timeout, 경과 시간, output/progress/tool event 또는 그 부재, heartbeat 부재, 동일 snapshot 반복은 lifecycle 전이·retry/fallback 권한을 만들지 않는다. 상태를 확인할 수 없으면 비종결 `environment_state_unknown`으로 남기며 failure로 추론하지 않는다.

명시적 environment `failed`/`interrupted`/blocker 또는 사용자 취소가 발생해 orchestrator가 상태와 원인을 보고하면 다음 중 하나를 선택한다.

1. 기존 invocation 종결·격리 후 **clean retry** — 새 invocation ID로 독립 실행한다. 같은 thread에 follow-up을 보내는 것은 clean retry가 아니다.
2. environment 상태를 유지한다. 자동 timed wait는 시작하지 않으며, host가 지원하고 사용자가 명시 선택한 event-only external continuation이 있을 때만 그 event를 기다린다.
3. phase에 허용된 fallback을 수행한다.
4. 해당 phase 또는 세션을 blocked로 끝낸다.

environment의 `approval_required`는 해당 승인 흐름으로 전달하지만 clean retry/fallback 승인으로 대신하지 않는다. interrupt, retry, fallback은 별도 사용자 승인 전에 실행되지 않는다. retry 승인 직전에 completion race를 다시 확인하며, 기존 invocation이 완료됐다면 retry를 취소하고 정상 결과 후보로 검토한다. 이 확인 전에는 결과 수용 권한이나 write ownership을 철회하지 않는다.

명시적으로 관측된 `approval_required`는 relay/control capability가 없어도 그대로 유지한다. relay 가능한 상위 agent에는 control을 반환하고, root까지 relay할 수 없으면 phase 진행 불가만 report narrative에 `blocked`로 기록한다. 이는 child lifecycle terminal이 아니며 child는 `ended_at: null`, `termination` 생략 상태다. relay 불가를 이유로 `environment_state_unknown`이나 failure로 바꾸지 않는다. `environment_state_unknown`은 environment status 자체가 unavailable/error이거나 의미를 확인할 수 없을 때만 사용한다. capability가 복구되어 same identity continuation이 가능하면 attempt와 retry 수를 늘리지 않는다.

read-only 호출에서는 old identity의 `result acceptance authority`를 명시적으로 철회한 뒤에만 새 identity를 시작한다. 이는 이후 도착한 old result를 ATP가 수용하지 않는 host-neutral 격리이며 environment terminal 상태를 추론하지 않는다. 같은 old identity의 철회 기록 뒤 도착한 결과만 `late_completion`으로 분류해 quarantine하며 자동 merge·취합·성공 판정 또는 ownership pause에 사용하지 않는다.

write-capable 호출에서는 기존 termination/write isolation, ownership 회수, partial write를 확인하기 전 같은 scope를 재시도하지 않는다. ownership 회수 뒤 old result가 도착해도 late disk write가 없으면 quarantine-only다. 실제 late disk write가 확인된 경우에만 겹치는 scope와 dependency closure를 persisted `paused`로 만들며 독립 scope는 계속 `active`다. 따라서 `late_completion` 자체는 pause 조건이 아니다. 특히 code 변경의 verification은 advisor 장애를 이유로 skip할 수 없고 Tier B 직접 검증 또는 blocked로 끝난다.

신규 producer의 abnormal `failed`/`interrupted`/`late_completion`에는 `lifecycle_fallback_reason`으로 concrete cause source, 현재 recovery disposition, rationale를 함께 기록한다. disposition은 `awaiting_user_decision`, `approved_clean_retry`, `phase_fallback`, `blocked`, `late_completion_quarantined` 다섯 가지다. 이는 retry 소진 뒤에만 쓰는 최종 사유가 아니다. 중간 invocation도 즉시 현재 disposition을 기록하고, 후속 명시적 결정에 맞춰 갱신한다. report schema는 계속 v2이고 lifecycle optional field도 기존 네 개뿐이다. 상세 의미는 [`agent-team-protocol.md` §2.5](../../plugins/atp/docs/development/agent-team-protocol.md), Codex 도구 mapping은 [`codex-lifecycle-routing.md`](../../plugins/atp/docs/development/codex-lifecycle-routing.md)를 참고한다.

### Q. 카탈로그 조사에서 개별 신뢰도와 `source_confidence`를 어떻게 기록하는가?

A. 이름 붙은 **모든 axis와 모든 item 각각**에 정확히 하나의 `확인됨 | 추정 | 미확인` marker를 기록한다. axis marker를 하위 item에 상속하거나 aggregate 값으로 대신할 수 없다. axis set 전체에는 별도 namespace인 `source_confidence: high | mixed | low`를 정확히 하나 둔다.

aggregate는 전체 marker multiset에서 결정론적으로 계산한다. 전부 `확인됨`이면 `high`, `미확인`이 strict majority이면 `low`, 그 밖의 모든 조합은 `mixed`다. 따라서 전부 `추정`, 확인·추정 혼합, non-majority 미확인 포함은 모두 `mixed`다. 여러 axis set이 있는 artifact의 전체 aggregate도 모든 set의 marker를 합쳐 같은 규칙으로 계산한다.

research worker와 advisor는 반환 전에 두 항목을 모두 self-check한다. 첫째, **마커 커버리지(marker coverage)**는 이름 붙은 axis/item 집합과 marker-bearing identity 집합이 같고 각 identity의 marker가 정확히 하나인지 검사한다. 둘째, **집계 도출(aggregate derivation)**은 실제 marker multiset에서 aggregate를 재계산해 emitted `source_confidence`와 일치하는지 검사한다. 누락 marker를 advisor가 추정해 채우거나 불일치 결과를 권위 전제로 승격하지 않는다.

---

## self-dogfooding (이 레포에서 개발)

### Q. 이 레포 자체에서 `/atp:task` (또는 Codex/Antigravity 동등 명령) 를 쓰고 싶다.

A. 로컬 플러그인 enable 이 필요하다.

**Claude Code:**
```
/plugin marketplace add ./
/plugin install atp@agent-team-protocol
```

**Codex (verified-empirical 2026-06-10, codex-cli 0.138.0):**
```
codex plugin marketplace add .
codex plugin add atp@agent-team-protocol
```

**Antigravity IDE (verified-empirical 2026-06-30, Antigravity 2.2.1):**
```
# Antigravity 는 /plugin 개념 없음 — Skills + Rules 시스템 사용.
# 설치: plugins/atp/skills/ → ~/.gemini/config/skills/ 수동 복사 (global skills root)
# init: /atp-init
# task: /atp-task
# 지침파일: GEMINI.md (상세: ADR-0015)
```

**opencode (verified-empirical 2026-06-24, opencode 1.17.9):**
```
# opencode 는 별도 npm 어댑터. @atp-opencode/opencode 패키지로 발행돼 있다.
npx @atp-opencode/opencode install
```

graphify add-on 도 사용하려면 (Claude Code):

```
/plugin install atp-graphify@agent-team-protocol
```

이후 새 세션에서 `/atp:task` (Claude Code) / `$atp:task` (Codex, verified-empirical 2026-06-10, codex-cli 0.138.0) / `/atp-task` (Antigravity IDE, verified-empirical 2026-06-30, Antigravity 2.2.1) / `opencode run --command atp-task "..."` (opencode, verified-empirical 2026-06-24, opencode 1.17.9) 가 활성화된다. 자세한 내용은 `../../README.md` §5 (self-dogfooding) 참조.

---

## 관련 문서

- [setup-checklist.md](./setup-checklist.md) — plugin 설치 후 설정 체크리스트
- [`../../plugins/atp/docs/development/agent-team-protocol.md`](../../plugins/atp/docs/development/agent-team-protocol.md) — 운영 프로토콜 전문 (§4 충돌 조정, §5 모델 선택, §7 재개 규약)
- `verification-strategies.md` — 검증 전략 레지스트리 (소비 프로젝트 `docs/development/`, `/atp:init` 생성)
- [`../../plugins/atp-graphify/docs/graphify-usage.md`](../../plugins/atp-graphify/docs/graphify-usage.md) — atp-graphify add-on 설치·통합
- [`../../plugins/atp/docs/development/agent-catalog.md`](../../plugins/atp/docs/development/agent-catalog.md) — base atp 10개 + add-on atp-graphify 3개 에이전트 목록
