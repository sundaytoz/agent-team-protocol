---
kind: development
title: Release Checklist
description: ATP 릴리즈 전 문서·매니페스트 동기화 점검 목록.
owner: template-maintainer
stability: living
last_reviewed: 2026-06-10
---

# Release Checklist

릴리즈 직전에는 아래 항목을 확인한다. 이 체크리스트는 2026-06-10 문서 감사에서 실제로 발견된 결함 유형을 기준으로 한다.

## 1. 상대 링크 유효성

문서와 템플릿의 상대 링크가 실제 파일로 해소되는지 확인한다. 특히 add-on 문서는 `docs/development/` 아래에 있다고 가정하지 않는다.

검증 명령:

```bash
rg -n "development/graphify|\\./graphify-usage\\.md" docs templates README.md
```

기대값: 출력 없음. graphify add-on 문서는 `addons/graphify/docs/graphify-usage.md` 를 가리켜야 한다.

## 2. `TODO:실측` 잔존

`TODO:실측` 은 실제 미실측 항목에만 남긴다. 이미 실측 완료된 Codex 호출 토큰·설치 명령 같은 항목에는 `verified-empirical` 과 날짜·버전을 병기한다.

검증 명령:

```bash
rg -n "TODO:실측|미실시|verified-empirical" README.md docs/usage docs/development docs/adr
```

기대값: 남은 `TODO:실측` 이 `docs/development/platform-adapters.md` 의 SSoT 상태와 일치한다.

## 3. README ↔ usage 명령어 일치

README 의 빠른 설치·호출 예시와 `docs/usage/` 의 체크리스트·FAQ가 같은 토큰을 사용해야 한다.

검증 명령:

```bash
rg -n "\\$task|\\$atp:task|/atp:task|codex plugin (marketplace add|add)" README.md docs/usage docs/development/platform-adapters.md
```

기대값: Codex 기본 호출은 `$atp:task` 이고, `$task` 는 단축형으로만 설명된다.

## 4. Marketplace manifest 동기화

Claude, Codex, marketplace 정본의 plugin 이름·버전·source 경로가 같은 릴리즈 의도를 가리키는지 확인한다.

검증 명령:

```bash
rg -n '"name"|"version"|"plugins"|"source"|atp-graphify|agent-team-protocol' .claude-plugin .codex-plugin .agents/plugins
```

기대값: `.agents/plugins/marketplace.json` 이 Codex marketplace 정본이고, `.claude-plugin/marketplace.json` / `.codex-plugin/marketplace.json` 은 그 의도와 충돌하지 않는다.

## 5. Agent catalog ↔ agents/ 목록 일치

`docs/development/agent-catalog.md` 는 base `agents/` 10개와 add-on `addons/graphify/agents/` 3개를 모두 포함해야 한다.

검증 명령:

```bash
find agents addons/graphify/agents -maxdepth 1 -name '*.md' -exec basename {} .md \\; | sort && rg -o '`[a-z0-9-]+`' docs/development/agent-catalog.md | tr -d '`' | sort -u
```

기대값: 파일 목록의 에이전트 이름이 카탈로그 표에 모두 등장한다.

## 6. 카테고리 index 신규 문서 등록

`docs/` 에 새 문서를 추가하면 해당 카테고리의 `index.md` 에 링크하고, 필요하면 `docs/index.md` 또는 README "더 읽기"에도 노출한다.

검증 명령:

```bash
find docs -mindepth 2 -maxdepth 2 -name '*.md' ! -name index.md -print | sort && find docs -maxdepth 2 -name index.md -print | sort
```

기대값: 새 문서가 속한 카테고리 index 에서 링크된다. `docs/development/` 문서는 [docs/development/index.md](./index.md) 목록도 함께 갱신한다.
