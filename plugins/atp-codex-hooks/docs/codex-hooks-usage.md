---
kind: usage
title: atp-codex-hooks add-on — 설치·신뢰·범위
description: Codex CLI 전용 hook-guarded bounded-pool candidate runner 를 옵트인으로 설치하는 사용자 가이드. hook trust 의 의미, 지원 scope, 제거 방법.
owner: template-maintainer
stability: candidate
last_reviewed: 2026-09-08
---

# atp-codex-hooks add-on

`atp-codex-hooks` 는 Codex CLI 전용 **옵트인 add-on** 이다. base `atp` 플러그인이 정의하는
`codex-team` skill 의 hook-guarded bounded-pool candidate 가 필요로 하는 hook 두 파일을 번들한다.

```text
plugins/atp-codex-hooks/
├── .claude-plugin/plugin.json   (name: atp-codex-hooks, dependencies: ["atp"])
├── .codex-plugin/plugin.json    (동일 정의)
├── hooks/hooks.json             (SessionStart / PreToolUse / PostToolUse / SubagentStart /
│                                 SubagentStop / PermissionRequest / UserPromptSubmit / Stop — 8 항목)
├── hooks/codex_pool_hook.py     (표준 라이브러리만 쓰는 Python 3 runner)
└── docs/codex-hooks-usage.md    (이 문서)
```

base `atp` 번들에는 hook 이 **없다**. base 만 설치한 Codex 소비자는 "Hooks need review" 신뢰
프롬프트를 보지 않으며, hook 이 없으므로 `codex-team` §1 의 `ATP_HOOK_GUARD_READY` marker 도
생성되지 않아 candidate bounded pool 은 spawn 0 으로 닫힌다(fail-closed). 이것은 오류가 아니라
기본 상태다 — `$atp:task` 는 `skip: no-codex-hooks` 를 기록하고 배포 profile 이 정한 mode 로 계속한다.

## 1. 누가 설치하나

- **release maintainer** — 격리된 `CODEX_HOME` 에서 candidate qualification smoke 를 돌릴 때.
- **candidate 를 직접 실험하려는 사용자** — 아래 §3 의 신뢰 범위를 이해하고 동의하는 경우에만.

일반 소비 프로젝트는 설치할 이유가 없다. 배포 profile 은 add-on 을 설치해도 바뀌지 않는다
(`team_execution_enabled: false` 유지 — `codex-team` §7). Add-on 은 실행 가능성을 열 뿐,
승격은 별도 배포 결정이다.

## 2. 설치

```bash
codex plugin marketplace add sundaytoz/agent-team-protocol   # 이미 등록했으면 생략
codex plugin add atp@agent-team-protocol                     # base 선행 (dependency)
codex plugin add atp-codex-hooks@agent-team-protocol
```

Claude Code 에서 이 add-on 을 설치할 이유는 없다. hook 은 Codex 의 `PLUGIN_ROOT` / `PLUGIN_DATA`
환경과 Codex hook event 이름을 전제로 작성됐다.

## 3. hook trust — 무엇에 동의하는가

설치 후 Codex TUI 를 처음 열면 다음이 뜬다.

```text
Hooks need review
8 hooks are new or changed.
Hooks can run outside the sandbox after you trust them.
```

- **Trust all and continue** 를 고르면 `config.toml` 에 hook 항목 단위로
  `[hooks.state."atp-codex-hooks@agent-team-protocol:hooks/hooks.json:<event>:0:0"] trusted_hash`
  가 영구 저장되고 재확인은 없다.
- trust 는 **명령 문자열** (`python3 "$PLUGIN_ROOT/hooks/codex_pool_hook.py"`) 에 묶인다.
  runner `.py` 내용이 바뀌어도 trust 가 유지돼 바뀐 코드가 sandbox 밖에서 그대로 실행된다.
  즉 `Trust all` 은 이 add-on 의 **이후 릴리스 runner 코드 변경까지** 무확인 실행에 동의하는 것이다.
  이 동의 범위가 base 번들에서 분리한 이유다.
- **Continue without trusting** 을 고르면 hook 은 실행되지 않고 marker 도 없다 → spawn 0.
- 비대화형 `codex exec` 는 신뢰 프롬프트를 띄우지 않고 조용히 hook 을 건너뛴다.
  `--dangerously-bypass-hook-trust` 는 격리 smoke 전용이며 소비 환경에서 쓰지 않는다.

## 4. 지원 scope

| 항목 | 상태 |
|---|---|
| Codex CLI 0.149.1, Unix, `python3` on PATH | 검증됨 (A축 PASS 2026-08-31) |
| Windows `py -3` | 미검증 — scope 밖. marker 가 생성되지 않으면 fail-closed |
| `allow_managed_hooks_only` policy | 미측정 |
| Codex App / IDE | `unknown` |

## 5. 비용

hook 은 `update_plan` 과 collaboration 도구(`spawn_agent` 등)에만 matcher 가 걸린다.
`Bash` / `apply_patch` 는 runner 를 호출하지 않는다. pool 이 없는 세션에서 매칭 도구 1회당
약 49ms(Python 시동 + stdlib import) 이고 파일시스템 접근은 0 이다.

`events.jsonl` 진단 ledger 는 기본 비활성이다. maintainer smoke 에서만
`ATP_HOOK_EVENT_LEDGER=1` 을 설정한다. pool 동작에 필요한 `state.json` 은 `PLUGIN_DATA` 아래
세션 단위로만 기록되며 레포나 사용자 설정을 쓰지 않는다.

## 6. 제거

```bash
codex plugin remove atp-codex-hooks
```

`config.toml` 의 `[hooks.state."atp-codex-hooks@..."]` 항목은 Codex 가 관리한다. 남아 있어도
hook 파일이 없으면 실행되지 않는다.

## 관련

- `plugins/atp/skills/codex-team/SKILL.md` §1 실행 gate, §7.1 축별 상태
- `plugins/atp/docs/development/codex-lifecycle-routing.md` §8
- `docs/backlog/codex-cli-hook-guarded-bounded-pool.md` §Phase 3 (D축 결론)
- `tests/runtime-behavior/test_codex_hook_guard.py`
