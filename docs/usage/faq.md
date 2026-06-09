---
kind: usage
title: 문제 해결 / FAQ
description: plugin 설치·init·사용 중 흔한 문제와 대응.
owner: template-maintainer
stability: living
last_reviewed: 2026-06-01
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

- `docs/index.md` + 카테고리 index 14개
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

A. 정상 동작이다. `atp-graphify` add-on 이 설치되지 않은 환경에서 base atp 는 graphify 단계를 건너뛰고 `skip: no-graphify` 로 세션 보고서에 기록한다. graphify 기능이 필요하면 `/plugin install atp-graphify@agent-team-protocol` 로 add-on 을 추가하고 새 세션을 시작한다. 상세는 `../../addons/graphify/docs/graphify-usage.md`.

### Q. graphify add-on 을 설치했는데 graphify 에이전트가 여전히 작동하지 않는다.

A. `atp` base 가 먼저 설치돼 있어야 한다. `atp-graphify` 는 `atp` 를 dependency 로 선언하므로, base 미설치 상태에서는 add-on 이 활성화되지 않는다. install 순서: base atp → atp-graphify.

---

## 에이전트 팀 운영

### Q. `verification-advisor` 가 통합 검증 스크립트 없다고 실패한다.

A. `/atp:init` 이 생성한 `docs/development/verification-strategies.md` 의 `cmd` 필드를 프로젝트 실제 명령으로 교체했는지 확인한다. 통합 `verify-all` 스크립트가 없다면 L1/L2 개별 `cmd` 만 유지해도 된다.

### Q. Advisor 가 서로 모순된 결정을 내린다.

A. `../development/agent-team-protocol.md` §4 충돌 조정 절 참조. 각 advisor 산출물의 `concerns` 필드가 교차점. orchestrator 가 1라운드 재검토 요청 → 실패 시 사용자에게 `AskUserQuestion`.

### Q. Worker 가 담당 파일 외부를 수정하려고 한다.

A. `implementation-advisor` 의 파일 소유권 맵을 확인. 한 파일에 2개 worker 가 할당되지 않았는지 검사. Worker 가 "한계" 로 반환했다면 advisor 가 재할당한다.

### Q. 모델이 항상 opus 만 써서 비용이 크다.

A. `report.md` 의 `invocations[].model_choice` 를 확인. `phase` / `escalation_reason` / `dispatch_size` 가 `../development/agent-team-protocol.md` §5 정책과 일치하는지 점검. `escalation_reason: null` 인데 `model: opus` 가 반복되면 orchestrator 프롬프트에 "기본 sonnet, §5.2 트리거 적중 시에만 opus 상승" 을 명시적으로 상기시킨다.

### Q. 세션이 중간에 끊겼다. 이어서 하려면?

A. 같은 `sid` 디렉토리가 이미 있어도 이어쓰지 않는다. 새 sid 로 시작하며 `report.md` 에 `resumed_from: <이전 sid>` 를 기록한다. 이전 `report.md` 에서 어느 phase 까지 끝났는지 확인하고 거기서부터 재개한다 (`../development/agent-team-protocol.md` §7 재개 규약).

### Q. graphify 없이도 팀이 동작하는가?

A. 예. `graphify-lookup-advisor` 가 `no-graph` 반환하면 `research-advisor` 로 자동 에스컬레이션. 세션 종료 시 graph-refresh 단계는 "skip: no-graphify" 로 기록하고 넘어간다. 상세는 `../../addons/graphify/docs/graphify-usage.md`.

### Q. 내 프로젝트에 DB 가 없는데 `migration-writer` 가 필요한가?

A. 필요 없다. init 후 생성된 프로젝트의 에이전트 설정에서 migration-writer 관련 언급을 제거한다. tier 구조에는 영향 없음.

### Q. 테스트 명령이 여러 개인데 `verify-all` 하나로 통합하기 어렵다.

A. 통합 스크립트를 만들지 말고 `../development/verification-strategies.md` 에 전략을 여러 개 등록한다. `verification-advisor` 가 변경 scope 에 매칭되는 것만 순차 실행한다.

---

## self-dogfooding (이 레포에서 개발)

### Q. 이 레포 자체에서 `/atp:task` (또는 Codex/Gemini 동등 명령) 를 쓰고 싶다.

A. 로컬 플러그인 enable 이 필요하다.

**Claude Code:**
```
/plugin marketplace add ./
/plugin install atp@agent-team-protocol
```

**Codex (TODO:실측 — namespace 확정 전):**
```
# Codex 플러그인 설치 명령 및 정확한 호출 표기는 install 스모크로 확정 예정.
```

**Gemini (TODO:실측 — extension 배포형·namespace 확정 전):**
```
# Gemini extension 설치 명령 및 정확한 호출 표기(/atp:task 콜론 추정)는 install 스모크로 확정 예정.
```

graphify add-on 도 사용하려면 (Claude Code):

```
/plugin install atp-graphify@agent-team-protocol
```

이후 새 세션에서 `/atp:task` (Claude Code) / `$task` (Codex, TODO:실측) / `/atp:task` (Gemini, TODO:실측) 가 활성화된다. 자세한 내용은 `../../README.md` §5 (self-dogfooding) 참조.

---

## 관련 문서

- [setup-checklist.md](./setup-checklist.md) — plugin 설치 후 설정 체크리스트
- [`../development/agent-team-protocol.md`](../development/agent-team-protocol.md) — 운영 프로토콜 전문 (§4 충돌 조정, §5 모델 선택, §7 재개 규약)
- `verification-strategies.md` — 검증 전략 레지스트리 (소비 프로젝트 `docs/development/`, `/atp:init` 생성)
- [`../../addons/graphify/docs/graphify-usage.md`](../../addons/graphify/docs/graphify-usage.md) — atp-graphify add-on 설치·통합
- [`../development/agent-catalog.md`](../development/agent-catalog.md) — base atp 10개 + add-on atp-graphify 3개 에이전트 목록
