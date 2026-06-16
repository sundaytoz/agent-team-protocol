---
kind: development
title: Release Checklist
description: ATP 릴리즈 전 문서·매니페스트 동기화 점검 목록.
owner: template-maintainer
stability: living
last_reviewed: 2026-06-16
---

# Release Checklist

릴리즈 직전에는 아래 항목을 확인한다. 이 체크리스트는 2026-06-10 문서 감사에서 실제로 발견된 결함 유형을 기준으로 한다.

## 0. 릴리즈 트리거 (진입 조건)

§1~§6 은 **bump 이 일어난다는 전제** 의 사후 invariant 점검이다. bump 자체가 트리거되지 않으면 점검도 누락된다. 본 절은 릴리즈를 **언제** 시작해야 하는지의 진입 조건이다.

- **트리거 — feat 머지 = release 완결 의무**: user-facing feat(소비자 동작·인터페이스에 영향을 주는 변경)가 `main` 에 머지되면, 같은 작업 단위 안에서 manifest version bump + `/plugin update` 도달까지를 release 완결 조건으로 본다. `/plugin update` 는 manifest version 차이로만 갱신을 감지하므로, feat 가 main 에 들어가도 bump 이 main 에 도달하지 않으면 소비자에게 무증상으로 미도달한다.
- **이월 금지 — 메모는 트리거가 아니다**: bump 을 후속 release 로 미룰 때 평문 메모(TEMPLATE_DEV "잔여" 등)로 남기면 잊힌다(2026-06-09 → 2026-06-16 약 1주 방치 실증). 이월 시 추적 가능한 Open Item 으로 격리하고 `release-pending` 태그를 붙여 다음 세션 진입 시 우선 확인한다.
- **bump 대상 브랜치 = 소비자 추적 ref**: bump/release 커밋은 소비자가 추적하는 ref(보통 `main`) 기반 release 브랜치에서 수행한다. 커밋 직전 현재 HEAD 와 `origin/main` 의 관계(ahead/behind/diverged)·내용 동일성을 진단한다. 이미 머지 완료된 stale 로컬 feat 브랜치에 bump 하면 PR 머지 후에도 update 미도달이 반복된다.

검증 명령:

```bash
git fetch origin main -q
last_bump=$(git log -1 --format=%h -S'"version": "2.' -- plugins/atp/.claude-plugin/plugin.json origin/main)
git log --oneline ${last_bump}..origin/main --grep='^feat' --grep='!:'
```

기대값: 출력이 **비어있으면** 마지막 version bump 이후 user-facing feat 머지가 없으므로 release 불요. 출력이 **비어있지 않으면** 미릴리즈 feat 가 존재하므로 §4 버전 invariant 점검 **전에** version bump 이 선행되어야 하고, 그 bump 커밋이 `origin/main` 에 도달하는 경로(PR base=main)인지 확인한다.

## 1. 상대 링크 유효성

문서와 템플릿의 상대 링크가 실제 파일로 해소되는지 확인한다. 특히 add-on 문서는 `docs/development/` 아래에 있다고 가정하지 않는다.

검증 명령:

```bash
rg -n "development/graphi[f]y|\\./graphify-usage\\.md" $(git ls-files docs plugins README.md README.en.md)
```

기대값: 출력 없음. graphify add-on 문서 링크는 `plugins/atp-graphify/docs/graphify-usage.md` 를 가리켜야 하고, base 번들(`plugins/atp/docs/`) 내 문서는 번들 외 파일을 링크하지 않는다(텍스트 언급만 허용). `git ls-files` 로 tracked 파일만 검사한다 — self-dogfooding 으로 생성되는 untracked 산출물은 릴리즈 대상이 아니다. 패턴의 `[f]` 는 이 체크리스트 자신의 명령 줄이 매치되는 것을 막는 self-exclusion 이다.

## 2. `TODO:실측` 잔존

`TODO:실측` 은 실제 미실측 항목에만 남긴다. 이미 실측 완료된 Codex 호출 토큰·설치 명령 같은 항목에는 `verified-empirical` 과 날짜·버전을 병기한다.

검증 명령:

```bash
rg -n "TODO:실측|미실시|verified-empirical" README.md docs/usage docs/development docs/adr plugins/atp/docs/development
```

기대값: 플랫폼 실측 상태의 동결 SSoT 는 [ADR-0009](../adr/ADR-0009-bundle-runtime-platform-neutralization.md) 부록이다(갱신 의무 없음 — 새 실측은 신규 ADR). `TODO:실측` 은 (a) 사람용 문서(README·docs/usage)의 플랫폼 병기 항목, (b) ADR 이력 문서, (c) 번들 내 마커 체계 *설명* 줄(예: platform-adapters §5 self-checklist 의 분류 안내), (d) 이 체크리스트 자신의 명령·기대값 줄(self-match)에만 존재한다 — 번들 런타임의 플랫폼별 실측 표·어댑터에는 잔존 0.

## 3. README ↔ usage 명령어 일치

README 의 빠른 설치·호출 예시와 `docs/usage/` 의 체크리스트·FAQ가 같은 토큰을 사용해야 한다.

검증 명령:

```bash
rg -n "\\$task|\\$atp:task|/atp:task|codex plugin (marketplace add|add)" README.md docs/usage
```

기대값: Codex 기본 호출(주 표기)은 `$atp:task`. `$task` 는 실측 검증된(verified-empirical 2026-06-10) 단축형 별칭으로 병기만 허용하고, 주 표기로 단정하지 않는다 — [ADR-0009](../adr/ADR-0009-bundle-runtime-platform-neutralization.md) 부록 F(구 검증 체크리스트)와 동일 기준. 번들 런타임 문서는 플랫폼별 호출 토큰을 열거하지 않으므로 검사 대상에서 제외한다.

## 4. Marketplace manifest 동기화

Claude, Codex, marketplace 정본의 plugin 이름·버전·source 경로가 같은 릴리즈 의도를 가리키는지 확인한다.

검증 명령:

```bash
rg -n '"name"|"version"|"plugins"|"source"|atp-graphify|agent-team-protocol' .claude-plugin .codex-plugin .agents/plugins plugins/atp/.claude-plugin plugins/atp/.codex-plugin plugins/atp-graphify/.claude-plugin plugins/atp-graphify/.codex-plugin
```

기대값: `.agents/plugins/marketplace.json` 이 Codex marketplace 정본이고, `.claude-plugin/marketplace.json` / `.codex-plugin/marketplace.json` 은 그 의도와 충돌하지 않는다. 모든 marketplace 의 atp source 는 `./plugins/atp`, atp-graphify source 는 `./plugins/atp-graphify`.

버전 invariant: base atp 매니페스트 4개(`plugins/atp/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `plugins/atp/.codex-plugin/plugin.json`, `.codex-plugin/marketplace.json`)는 버전이 서로 같아야 하고, add-on atp-graphify 매니페스트 2개(`plugins/atp-graphify/.claude-plugin/plugin.json`, `plugins/atp-graphify/.codex-plugin/plugin.json`)도 서로 같아야 한다. base 와 add-on 은 독립 버저닝(불일치 정상). `.agents/plugins/marketplace.json` 에는 version 필드가 없는 것이 정상이다.

## 5. Agent catalog ↔ agents/ 목록 일치

`plugins/atp/docs/development/agent-catalog.md` 는 base `plugins/atp/agents/` 10개와 add-on `plugins/atp-graphify/agents/` 3개를 모두 포함해야 한다.

검증 명령:

```bash
find plugins/atp/agents plugins/atp-graphify/agents -maxdepth 1 -name '*.md' -exec basename {} .md \\; | sort && rg -o '`[a-z0-9-]+`' plugins/atp/docs/development/agent-catalog.md | tr -d '`' | sort -u
```

기대값: 파일 목록의 에이전트 이름이 카탈로그 표에 모두 등장한다.

## 6. 카테고리 index 신규 문서 등록

`docs/` 에 새 문서를 추가하면 해당 카테고리의 `index.md` 에 링크하고, 필요하면 `docs/index.md` 또는 README "더 읽기"에도 노출한다.

검증 명령:

```bash
find docs plugins/atp/docs -mindepth 2 -maxdepth 2 -name '*.md' ! -name index.md -print | sort && find docs plugins/atp/docs -maxdepth 2 -name index.md -print | sort
```

기대값: 새 문서가 속한 카테고리 index 에서 링크된다. 런타임 문서(`plugins/atp/docs/development/`)는 번들 경량본 [plugins/atp/docs/development/index.md](../../plugins/atp/docs/development/index.md) 와 루트 풀본 [docs/development/index.md](./index.md) 양쪽을 갱신한다. 번들 경량 허브 2건(`plugins/atp/docs/index.md`, `plugins/atp/docs/development/index.md`)은 번들 외 문서를 링크하지 않는다(텍스트 언급만 허용 — 루트 허브 ↔ 번들 허브 정합).
