---
kind: changes
title: 2.17.0 — Codex candidate hook을 옵트인 add-on atp-codex-hooks로 분리
description: hook-guarded bounded-pool candidate의 hooks.json·runner를 base 번들에서 제거하고 Codex CLI 전용 옵트인 add-on으로 옮겨, base만 설치한 소비자가 "Hooks need review" 신뢰 요청을 받지 않게 함. 배포 profile 무변경.
owner: template-maintainer
stability: stable
last_reviewed: 2026-09-08
---

# 2.17.0 — Codex candidate hook을 옵트인 add-on `atp-codex-hooks`로 분리

## 원인

`plugins/atp/hooks/`의 candidate hook은 `codex plugin add`만으로 설치본에 실려 기본 discovery 경로로 활성화됐다. Codex TUI는 첫 대면에 "Hooks need review / 8 hooks are new or changed / Hooks can run outside the sandbox after you trust them"을 띄우고, `Trust all`은 hook 항목 단위 `trusted_hash`로 영구 저장된다. 이 trust는 **command 문자열에만** 묶이므로 runner `.py` 내용이 바뀌어도 유지되어 이후 릴리스의 runner 변경이 sandbox 밖에서 무확인 실행된다.

`team_execution_enabled: false`인 base 소비자는 얻을 기능 없이 이 동의를 요구받았다. backlog §Phase 3 D축은 이를 근거로 `atp-graphify`와 같은 옵트인 add-on 분리를 결정했다.

## 변경

- **add-on 신설** `plugins/atp-codex-hooks/` — `.claude-plugin`/`.codex-plugin` manifest(version `1.0.0`, `dependencies: ["atp"]`), `hooks/hooks.json`, `hooks/codex_pool_hook.py`(`git mv`, byte 무수정), `docs/codex-hooks-usage.md`.
- **base 제거** — `plugins/atp/hooks/` 삭제. base 번들에 hook 0. base만 설치한 Codex 소비자에게 "Hooks need review"가 뜨지 않는다.
- **marketplace 3곳 등재** — `.claude-plugin/marketplace.json`, `.codex-plugin/marketplace.json`, `.agents/plugins/marketplace.json`.
- **marker 재정합** — `hooks.json` description만 add-on 표기로 변경돼 `hooks_sha256`이 `d7005171…`로 바뀌었다. `runner_sha256` `22b93853…`은 2026-08-31 A축 evidence와 동일. `codex-team/SKILL.md` §1 marker 갱신. add-on 미설치 시 marker 부재 → spawn 0 fail-closed 유지.
- **skill 분기** — `codex-team` §1에 add-on 전제와 `skip: no-codex-hooks`, `task` SKILL §0.25에 add-on 미설치 시 차단 없는 계속(`skip: no-graphify`와 동형) 명시.
- **테스트** — `test_codex_hook_guard.py` 상수를 add-on 경로로, 회귀 2건 추가(`test_base_bundle_ships_no_hooks`, `test_addon_manifests_and_marketplaces_are_consistent`) → 21건.
- **문서** — backlog D축 "분리 완료", routing appendix §8.5, known-issues ko/en, tests README, file-map, docs index ko/en, README ko/en, faq ko/en, release-checklist §4 invariant(add-on 2곳 + base `hooks/` 부재).
- **버전** — base `2.16.0 → 2.17.0`(manifest 4곳). add-on `atp-codex-hooks 1.0.0`. `atp-graphify 2.3.0` 불변.

배포 profile은 바뀌지 않았다 — `formal_adapter_enabled: false`, `manual_wait_polling_supported: false`, `host_managed_subagent_orchestration: unsupported`, `team_execution_enabled: false`. add-on 분리는 packaging 형태 변경이고 승격은 별도 결정이다.

## 검증

- `python3 -m unittest tests/runtime-behavior/test_codex_hook_guard.py` 21/21, `test_codex_managed_contract.py` 15/15, `test_validate_codex_session.py` 6/6, `tests/lifecycle-contract/validate.py` PASS.
- 격리 Codex 검증(임시 `CODEX_HOME` + 임시 git workspace + fresh source install, codex-cli 0.149.1 직접 호출, 사용자 `~/.codex` 무변경):
  - base `atp@agent-team-protocol`만 설치 → 설치본 트리 `agents docs skills templates`, `find … -iname 'hooks*'` 0건, `config.toml` `hooks.state` 0건. TUI 최초 대면은 디렉토리 신뢰 프롬프트 → 메인 화면. **"Hooks need review" 없음.**
  - `atp-codex-hooks@agent-team-protocol` 추가 설치 → 설치본 `hooks/hooks.json`·`hooks/codex_pool_hook.py` 존재, base 트리는 여전히 hook 0. 설치본↔소스 SHA-256 byte parity 일치(`d7005171…`, `22b93853…`). 설치본 runner에 `SessionStart` payload를 직접 넣어 얻은 marker가 `codex-team/SKILL.md` §1 문자열과 정확히 일치.
  - add-on 설치 후 TUI 최초 대면에 "Hooks need review / 8 hooks are new or changed / Hooks can run outside the sandbox after you trust them"가 나타남 — 신뢰 요청이 add-on 경계 안으로 이동했음을 확인. 검증에서는 `Continue without trusting`을 선택해 trust를 남기지 않았다.

## 잔여

- B축 T4(interactive PTY steering) 재측정, `allow_managed_hooks_only` 측정, Windows `py -3` runner scope 결정 — backlog §남은 승격 조건.
- `/plugin update` 도달 후 소비 Codex 환경에서 base 2.17.0 설치본에 `hooks/`가 없고 TUI 첫 대면에 신뢰 프롬프트가 없음을 1회 확인 — needs_user_verification.
