---
kind: development
title: Release Checklist
description: ATP 릴리즈 전 문서·매니페스트 동기화 점검 목록.
owner: template-maintainer
stability: living
last_reviewed: 2026-08-18
---

# Release Checklist

릴리즈 직전에는 아래 항목을 확인한다. 이 체크리스트는 2026-06-10 문서 감사에서 실제로 발견된 결함 유형을 기준으로 한다.

## 0. 릴리즈 트리거 (진입 조건)

> 이 레포 기여자의 진입 동선: 루트 `CLAUDE.md` 의 **"릴리스 — 배포 완결 의무"** 섹션이 docs-first 로 이 §0 를 가리킨다. `plugins/atp/` 번들을 변경하는 작업은 시작·완료 시 본 절을 확인한다.

§1~§10 은 **bump 이 일어난다는 전제** 의 사후 invariant 점검이다. bump 자체가 트리거되지 않으면 점검도 누락된다. 본 절은 릴리즈를 **언제** 시작해야 하는지의 진입 조건이다.

- **트리거 — feat 머지 = release 완결 의무**: user-facing feat(소비자 동작·인터페이스에 영향을 주는 변경)가 `main` 에 머지되면, 같은 작업 단위 안에서 manifest version bump + `/plugin update` 도달까지를 release 완결 조건으로 본다. `/plugin update` 는 manifest version 차이로만 갱신을 감지하므로, feat 가 main 에 들어가도 bump 이 main 에 도달하지 않으면 소비자에게 무증상으로 미도달한다.
- **번들 변경은 같은 작업 단위에서 완결**: `plugins/atp/`의 소비자-visible 동작·계약을 변경한 작업은 base manifest/marketplace version, changes·index, 관련 appendix/index, 본 체크리스트의 적용 gate를 같은 작업 단위에서 동기화한다. 검증과 소비자 추적 ref 도달 경로가 확인되기 전에는 구현만 완료됐다고 종료하지 않는다. 실제 push/update가 현재 권한·환경 밖이면 명령과 확인 항목을 `needs_user_verification`에 남기고 프로젝트 gate 미수행 상태를 명시한다.
- **이월 금지 — 메모는 트리거가 아니다**: bump 을 후속 release 로 미룰 때 평문 메모(TEMPLATE_DEV "잔여" 등)로 남기면 잊힌다(2026-06-09 → 2026-06-16 약 1주 방치 실증). 이월 시 추적 가능한 Open Item 으로 격리하고 `release-pending` 태그를 붙여 다음 세션 진입 시 우선 확인한다.
- **bump 대상 브랜치 = 소비자 추적 ref**: bump/release 커밋은 소비자가 추적하는 ref(보통 `main`) 기반 release 브랜치에서 수행한다. 커밋 직전 현재 HEAD 와 `origin/main` 의 관계(ahead/behind/diverged)·내용 동일성을 진단한다. **진단 결과를 두 케이스로 분기한다 — 한쪽 처방을 다른 쪽에 적용하면 안 된다**:
  - **(A) stale 머지-완료 브랜치** — HEAD 의 커밋들이 이미 `origin/main` 에 있다(내용 중복). 여기에 bump 하면 PR 머지 후에도 update 미도달이 반복된다. → **`origin/main` 기반으로 새 release 브랜치를 만든다.**
  - **(B) 미머지 릴리스 위 스택** — HEAD 가 `origin/main` 에 없는 **직전 bump 커밋**을 포함하고, 이번 작업이 그 커밋의 *내용* 에 의존한다(예: 직전 릴리스가 도입한 가드의 구멍을 이번 작업이 닫는다). 이 경우 스택이 **정당하며 `main` 기반 분기는 오히려 틀리다** — 직전 버전의 내용이 `main` 에 없으므로 그 위 버전만 올리면 **버전만 뛰고 내용이 비는** 상태가 된다. → **스택을 유지하고 PR 이 두 릴리스를 함께 머지함을 `open_items` 에 명시**한다. 버전 연속성(N-1 → N)은 PR 머지로 함께 확보된다.
  - 분기 기준은 "HEAD 가 main 보다 앞서 있는가" 가 아니라 **"직전 bump 커밋이 `origin/main` 에 있는가"** 다. (A) 는 있고 (B) 는 없다.
  - **진단 전 `git fetch origin main` 필수** — 로컬 `origin/main` ref 는 세션 중에도 stale 해진다(다른 PR 이 머지되면). fetch 없이 판정하면 (B) 로 오진하고, 그 오진이 `open_items`·사용자 보고까지 전파된다. 2026-07-30 세션 실증: fetch 전 "미머지 스택(B)" 으로 진단·보고했으나 fetch 후 직전 릴리스가 이미 머지돼 있어 (A) 였다.

검증 명령:

```bash
git fetch origin main -q
last_bump=$(git log -1 --format=%h -G'"version": *"2\.' origin/main -- plugins/atp/.claude-plugin/plugin.json)
git log --oneline ${last_bump}..origin/main --grep='^feat' --grep='!:'
```

> **명령 형태 주의 (2026-07-30 실행으로 발견한 결함 2건 — 둘 다 조용히 틀린 커밋을 집는다)**:
> - **`-S` 대신 `-G`** 를 쓴다. `-S` 는 문자열 **출현 횟수** 변화를 찾으므로 `2.9.0 → 2.10.0` 같은 bump 은 `"version": "2.` 의 횟수를 바꾸지 않아 **매치되지 않는다**. 실측: `-S` 는 2.0.0 시절 커밋(`bb75f21`)을 집었다.
> - **revision 은 `--` 앞에** 둔다. `-- <path> origin/main` 처럼 `--` 뒤에 두면 revision 이 아니라 **pathspec** 으로 해석돼 대상 브랜치 한정이 무효가 된다.
>
> 두 결함이 겹치면 명령은 에러 없이 무관한 커밋을 반환하므로 텍스트 리뷰로는 보이지 않는다(§4.6 "검증 명령은 실행으로만 통과 판정" 의 실제 사례).

기대값: 출력이 **비어있으면** 마지막 version bump 이후 user-facing feat 머지가 없으므로 release 불요. 출력이 **비어있지 않으면** 미릴리즈 feat 가 존재하므로 §4 버전 invariant 점검 **전에** version bump 이 선행되어야 하고, 그 bump 커밋이 `origin/main` 에 도달하는 경로(PR base=main)인지 확인한다.

브랜치 케이스 (A)/(B) 분기 진단:

```bash
git fetch origin main -q          # 필수 — stale ref 로 판정하면 (B) 로 오진한다
# 직전 bump 커밋(현 브랜치 기준)이 origin/main 에 있는가
prev_bump=$(git log -1 --format=%H -G'"version": *"2\.' HEAD~1 -- plugins/atp/.claude-plugin/plugin.json)
git merge-base --is-ancestor "$prev_bump" origin/main \
  && echo "case A (stale) — origin/main 기반 재분기" \
  || echo "case B (미머지 릴리스 위 스택) — 스택 유지 + open_items 명시"
```

`HEAD~1` 기준인 이유: 이번 세션이 방금 만든 bump 커밋 자신은 당연히 `origin/main` 에 없으므로 판정에서 제외해야 한다. 아직 bump 하지 않은 시점에 진단하면 `HEAD` 로 바꿔 쓴다.

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

### 4.1 Codex manifest와 skill invocation policy

형식 migration은 다음 세 계약을 분리해 판정한다.

- **공식 제품 계약**: [Build plugins](https://learn.chatgpt.com/docs/build-plugins)의 skills-only 최소 예시는 `.codex-plugin/plugin.json`에 `name`, `version`, `description`, `skills`를 둔다. [Package your plugin](https://developers.openai.com/plugins/build/plugins)은 `interface`를 install-surface metadata로 설명하며 manifest entry point 외 필드는 optional이라고 명시한다.
- **공식 skill 정책**: [Build skills](https://learn.chatgpt.com/docs/build-skills)은 implicit invocation 차단을 `skills/<name>/agents/openai.yaml`의 `policy.allow_implicit_invocation: false`로 선언한다. 이 값은 명시적 `$skill` invocation을 막지 않는다.
- **로컬 publishing/scaffold validator**: 최신 `plugin-creator` validator는 공식 최소 ingestion 예시보다 엄격하게 `author.name`과 `interface.displayName`, `shortDescription`, `longDescription`, `developerName`, `category`, `capabilities`, `defaultPrompt`를 요구한다. `skill-creator` quick validator는 `SKILL.md` frontmatter를 허용된 authoring 필드로 제한한다.

공식 문서는 legacy `disable-model-invocation`의 deprecated 여부를 명시하지 않는다. 따라서 해당 frontmatter 제거는 deprecated 사실의 인용이 아니라, 공식 대체 정책 위치와 최신 validator 거부를 함께 적용한 migration 추론으로 기록한다. CLI, Codex app, ChatGPT Chat/Work는 같은 배포 형식을 공유해도 discovery·UI·invocation behavior가 surface별로 다를 수 있으므로, 실제 설치 smoke의 surface와 버전을 반드시 함께 남긴다.

검증 명령:

```bash
uv run --with pyyaml python \
  ~/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py plugins/atp
uv run --with pyyaml python \
  ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py plugins/atp/skills/init
```

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

## 7. 역이식(backport) 산출물 출처 식별자 잔류 0

이 절은 **ATP 소스 레포 자체의 backport** — self-dogfooding 으로 얻은 소비 프로젝트(세션·도메인 사례·코드 심볼) 경험을 ADR·런타임 정본(`agent-team-protocol.md`)·`TEMPLATE_DEV.md`·`agents/*.md` 등 범용 자산에 역이식하는 변경 — 에만 발동한다. 소비 프로젝트가 자기 식별자를 쓰는 것은 정상이며 이 게이트 대상이 아니다.

ADR-0004·ADR-0005 가 "소비 프로젝트 식별자를 본문·메타·파일명 어디에도 남기지 않고 commit 전 residual 0 을 확인한다"는 **일반화 게이트를 선언**한 SSoT 정의처다. 본 절은 그 선언의 **집행 경로**다 — 선언만으로는 dead gate 가 되어 선언한 문서군 자신이 위반한 실증(2026-06-17, 코드 심볼·소비 프로젝트 slug·도메인 동반어 6건 누출)이 있다.

**발동 조건**: 이번 변경이 (a) backport(출처 인용 동반)인가, 또는 (b) **scrub/중립화 대상 토큰(소비 프로젝트 식별자·서비스명 등)을 본문 또는 메타 산출물(changelog·커밋 메시지·ADR 산문)에서 *언급*하는가**? 둘 중 하나라도 YES 면 §7 을 수행한다. 순수 내부 규약·플랫폼 스펙 변경에는 걸지 않는다.

> (b) 주의 — scrub/중립화 작업은 "무엇을 무엇으로 바꿨다"를 서술하면서 대상 토큰을 메타 산출물에 **재유입**하기 쉽다(작업 본문이 깨끗해도 changelog·커밋 메시지가 누출원이 될 수 있음). 따라서 backport 가 아닌 scrub *후속* 일반 patch 라도 메타 산출물이 대상 토큰을 언급하면 §7 을 발동한다. 메타 산출물에서는 원본 토큰을 직접 적지 말고 중립 placeholder("소비 프로젝트 서비스명", `examp[l]e_slug`)로 서술한다. (실증: 2026-06-18 세션 — TEMPLATE_DEV changelog 가 scrub 대상 서비스명을 재유입했고 commit 전 self-grep 이 검출.)

**절차 (commit 전)**:

1. **후보 토큰 수집** — 이번 작업이 인용한 출처 식별자를 목록화한다(고정 리스트가 아니라 *이번 작업이 실제로 끌어온* 토큰): 소비 프로젝트 slug(레포명·앱/게임 IP·봇명) + 도메인 동반어(플랫폼 고유 기능·엔티티명) + 코드 심볼(env 키·필드명·외부 API명). 출처는 이번 세션의 research 산출(누출 감사 카탈로그가 있으면 그것) / 인용 원본 세션 report / 작업자 인지다. 토큰이 0개면(=출처 인용이 전혀 없으면) 이 변경은 backport 가 아니므로 §7 미발동.

2. **self-grep 실행** — 수집한 토큰을 OR-패턴으로 묶어 **diff 추가 라인 + 신규 파일명**(scrub/중립화 변경이면 **이번 커밋 메시지**도 포함 — 발동 조건 (b))에 대해 실행한다. 패턴에는 character-class self-exclusion(예: 토큰 `example_slug` 면 `examp[l]e_slug`)을 적용해 이 체크리스트·게이트 명령 줄 자신이 매치되는 것을 막는다.

   ```bash
   # 단계 1 에서 수집한 토큰을 OR-패턴으로 묶되, 각 토큰에 character-class self-exclusion 을 적용해
   # 이 명령 줄 자신이 매치되지 않게 한다. 아래 example_* 는 형태 예시다(실제로는 수집한 토큰명 사용):
   git grep -niE 'examp[l]e_slug|examp[l]e_bot|examp[l]e_sym' -- ':!docs/development/release-checklist.md'
   ```

   기대값: **출력 없음 + exit 1**(매치 0). git grep 은 매치 0 일 때 exit 1 을 반환하므로 `; echo "exit=$?"` 로 확인한다. 1 hit 이상(exit 0)이면 잔류이므로 처리 후 재실행한다.

3. **잔류 처리** — 단순 토큰은 도메인 중립 placeholder 로 치환(예: 코드 심볼 → `field_key` 류 일반 명칭). 프로젝트명·도메인·기능이 한 줄에 응집된 강결합 서술은 단순 치환으로 식별성이 잔존하므로 본문 재작성으로 일반 규약만 추출하되(ADR-0004 패턴), hedge·갭 구조 등 교훈 골격은 보존한다(ADR-0011 §검증 모범). 본 레포 자체 dogfood 세션ID(타임스탬프)는 ATP evidence record 관행이라 유지한다(ADR-0010, 외부 누출 아님).

검증 명령(이 게이트 자체의 실행 가능성 — §4.6):

```bash
# 위 git grep 이 self-exclusion 으로 자기 명령 줄을 매치하지 않는지 1회 실행 확인.
# 누출이 이미 제거된 청정 레포에서는 어떤 backport 토큰 패턴이든 0 hit(exit 1)이어야 한다.
git grep -niE 'examp[l]e_slug|examp[l]e_bot|examp[l]e_sym' -- ':!docs/development/release-checklist.md'; echo "exit=$?"
```

기대값: 출력 없음 + `exit=1`. (토큰 리스트는 작업마다 다르므로 고정이 아니다 — 위는 2026-06-17 backport 의 예시 토큰이며, 그 시점 레포에서 0 hit 으로 실증됐다.)

## 9. opencode 어댑터 릴리즈

opencode 어댑터(`adapters/opencode/`)를 변경하거나 신규 호스트 어댑터를 추가할 때 적용한다.

### (a) adapters/opencode/package.json version 동기 점검

어댑터 기능 변경 시 `adapters/opencode/package.json` 의 `version` 을 bump 하고, CHANGELOG(있는 경우)와 동기되는지 확인한다.

```bash
grep '"version"' adapters/opencode/package.json
```

기대값: 이번 변경 의도와 일치하는 버전 번호.

### (b) 신규 호스트 게이트

신규 호스트 어댑터는 정식 스모크(opencode AC L1+L2 전건 PASS) 통과 전 **platform-adapters.md 활성 규칙 등재 금지** — 중립화 유지. platform-adapters.md §8 동결이력 포인터 1줄만 추가한다(ADR-0009 결정2·ADR-0014 D7 SSoT 정정 준거).

### (c) tier→slug as-of staleness 점검

`--provider` 옵션으로 bake 된 tier→slug 매핑이 해당 provider 의 현재 라인업과 여전히 정합하는지 확인한다. 라인업 변동 시 generator 매핑 업데이트 + `as-of` 스탬프 갱신.

```bash
grep -r 'as-of\|asOf\|haiku\|sonnet\|opus' adapters/opencode/
```

기대값: 매핑 날짜 스탬프가 최신 라인업 확인 시점을 반영.

### (d) opencode 스모크 절차 요약

```bash
# 임시 디렉토리에서 실행
T=$(mktemp -d)
cd "$T"
node <repo>/adapters/opencode/bin/cli.js install --project

# L1 정적 확인 (generator 단위)
ls .opencode/agents/atp-*.md | wc -l          # 개수 = source 와 동등
grep -L '^mode: subagent' .opencode/agents/atp-*.md   # 출력 없음 기대
grep -L 'task: deny' .opencode/agents/atp-*.md        # 출력 없음 기대
node <repo>/adapters/opencode/bin/cli.js uninstall --project
ls .opencode/agents/ 2>/dev/null | wc -l       # 0 기대 (잔여 0)

# L2 런타임 확인 (opencode 필요)
node <repo>/adapters/opencode/bin/cli.js install --project
opencode agent list                             # atp-* 10개, 에러 0 기대
opencode run --command atp-task "로드 확인만 — 한 줄로 답하고 종료"
# exit 0 + ProviderModelNotFoundError 0 기대
node <repo>/adapters/opencode/bin/cli.js uninstall --project

cd / && rm -rf "$T"
```

기대값: 각 단계 exit 0, L1 전건 PASS, L2 전건 PASS, 잔여 0.

## 8. 끊긴 §N 인용 0 (protocol 섹션 인용 무결성)

`agent-team-protocol.md` 는 ADR·`agents/*.md`·docs 가 §N 번호로 인용하는 사실상의 공개 앵커다. 섹션 추가/재배열로 인용된 §N 이 본문 헤더에서 사라지면 모든 인용이 무성증상으로 끊긴다(코어 구획은 `<!-- -->` 마커라 `#` 헤더 카운트에 안 잡혀 §N 번호에 영향 0). 본 절은 그 끊긴 인용을 0으로 강제한다.

검증 명령:

```bash
PROTO=plugins/atp/docs/development/agent-team-protocol.md
comm -23 \
  <(grep -rhoE --exclude='release-checklist.md' '§[1-9][0-9]?' docs plugins | tr -d '§' | sort -un) \
  <(grep -oE '^#{2,4} [0-9]+' "$PROTO" | grep -oE '[0-9]+' | sort -un)
```

기대값: **출력 없음**(끊긴 §N 인용 0). 좌변은 `docs`·`plugins` 전체에서 인용된 정수 §N 집합, 우변은 protocol 본문 §헤더 번호 집합이며, 좌변에만 있는 번호(=인용됐으나 본문에 없는 §N)가 끊긴 인용이다. `--exclude='release-checklist.md'` 로 이 체크리스트 자신의 §N 산문(self-match)을 검사 대상에서 빼 자기매치를 차단한다(§4.6 실행 통과 판정 — 2026-06-18 레포에서 출력 0 으로 실증). 신규 섹션은 §14 다음 정수로만 추가하고 기존 번호를 재배열하지 않는다(코어 구획 C7 규칙).

## 10. Environment-authoritative subagent lifecycle 계약

이 gate는 lifecycle뿐 아니라 2.15.0의 formal/host-managed scheduling과 adaptive execution-mode 계약도 함께 다룬다.

`agent-team-protocol.md` §2.5의 lifecycle correctness, timeout-free environment-owned formal scheduling, host-managed all-results barrier, host appendix 경계와 report schema v2 호환성을 함께 검사한다. 한 문서만 갱신하거나 manual wait를 correctness primitive로 승격해 공통 의미와 실행 mapping이 drift한 상태로 릴리즈하지 않는다.

### (a) Lifecycle + scheduling fixture와 schema v2 역호환

```bash
python3 tests/lifecycle-contract/validate.py
```

기대값: `PASS: environment-authoritative lifecycle contract and compatibility fixtures`, exit 0.

- 권위 event vocabulary와 10개 authority case가 전수 존재해야 한다. environment의 `running`/`completed`/`failed`/`interrupted`/`approval_required`와 상태 미확정 `environment_state_unknown`의 의미를 검사한다.
- `wait_timeout`, 경과 시간, progress/output/tool event 또는 그 부재, heartbeat 부재, 동일 snapshot은 상태 전이·retry/fallback 권한·retry budget 소비를 만들지 않아야 한다.
- lifecycle 필드가 없는 legacy v2, 과거 `termination: silent_stall` v2, 신규 environment terminal v2가 모두 유효해야 한다. 신규 producer는 `silent_stall`을 생성하지 않고 optional 4필드(`attempt`, `termination`, `retry_of`, `lifecycle_fallback_reason`)만 additive하게 사용한다.
- same-invocation follow-up attempt 불변, 승인 전 mutation 0건, completion race, termination/isolation, write ownership handoff, `late_completion` 격리, verification의 Tier B 실행 또는 blocked 종단을 확인한다.
- 명시적으로 관측된 `approval_required`는 relay/control unavailable이어도 child lifecycle에서 보존돼야 한다. child는 `ended_at: null`, `termination` 생략이고 mutation·attempt/retry 증가는 0건이며, phase 진행 불가만 report narrative에 `blocked`로 기록한다. `environment_state_unknown`은 environment status unavailable/error/semantic unknown에서만 생산한다.
- 이름 붙은 모든 research axis/item에 marker가 정확히 하나인지, aggregate `source_confidence`가 전체 marker multiset에서 `high|mixed|low` truth table로 재계산되는지, worker/advisor가 marker coverage와 aggregate derivation을 모두 self-check하는지 확인한다.
- 신규 abnormal `failed|interrupted|late_completion` reason이 concrete cause source, non-empty rationale와 닫힌 disposition 5종(`awaiting_user_decision`, `approved_clean_retry`, `phase_fallback`, `blocked`, `late_completion_quarantined`) 중 현재 값을 가지는지 확인한다. 중간 invocation의 non-null reason을 retry exhaustion 뒤로 미루면 실패해야 한다.
- `tests/lifecycle-contract/fixtures/wait-wakeup-cases.json`의 required capability, wake event와 ledger vocabulary가 closed set인지 검사한다. Formal mode에는 root-visible timeout event가 없어야 한다.
- Unchanged `running`/internal keepalive N회에 lifecycle transition, root model resume, semantic action, retry/list가 모두 0이어야 한다.
- Single completion은 wake 1회, 인접 completion 여러 개는 coalesced wake 1회, duplicate event는 delta/result acceptance 1회여야 한다.
- `approval_required`와 user steering은 barrier를 단락하되 state/authority/ownership을 보존해야 한다. Explicit `failed|interrupted`만 기존 사용자 승인형 recovery를 열어야 한다.
- Required formal capability 하나라도 `unsupported|unknown`이면 formal adapter만 disabled여야 하며 managed capability가 `supported`인 host는 `host_managed_subagent_orchestration`으로 spawn/result collection을 유지해야 한다.
- Formal/managed orchestration이 모두 없으면 general task는 `tier_b_sequential`로 진입하고, explicit subagent request는 silent Tier B 대체 없이 `blocked_explicit_independence`와 options를 제공해야 한다.
- 사용자 승인형 recovery나 completion-race 확인의 단발 authoritative list는 허용하되, existing invocation과 approval ref 없이 실행되거나 polling 목적으로 반복되면 실패해야 한다.
- Current Codex managed candidate는 requested/spawn/terminal/collected가 일치하고 manual wait/list와 정상 경로 interrupt가 0이며 terminal 전 completion serialization이 없을 때만 supported다. 하나라도 실패하면 tested surface profile은 `unsupported`, team execution은 disabled여야 한다.
- Non-Codex formal subscription과 Tier A-flat fixture가 기존 mode/topology를 유지해야 한다.

### (b) 공통 정본 host-neutrality와 appendix 연결

위 validator는 공통 §2.5·task·agent에 Codex collaboration 도구명과 event spelling이 0건인지, `codex-lifecycle-routing.md`와 전용 skill에는 실제 Codex mapping이 있는지 함께 검사한다. Active lifecycle 범위에는 `suspected_silent_stall`, observation budget 또는 heartbeat deadline 기반 전이가 없어야 한다. Codex 정상 경로의 manual wait/list polling은 0이어야 한다.

신규 host mapping을 추가하면 공통 §2.5가 아니라 해당 host appendix와 orchestration skill에 배치한다. `platform-adapters.md`에는 host-neutral lifecycle provenance, formal capability와 managed orchestration 판정만 추가한다. 모든 required scheduling capability가 `supported`일 때만 formal adapter를 enable하며 partial support를 `environment_subscription`으로 위장하지 않는다. Managed mode를 쓰려면 all-results barrier와 적용 surface/version 근거를 appendix에 명시한다. Environment가 노출하지 않는 lifecycle event는 추정하지 않는다.

### (c) Capability matrix와 release-time maintainer smoke

현재 tool schema와 host appendix의 capability identity를 양방향 대조한다. Timeout-free await identity, target wait-any/all, terminal/approval/steering/cancel subscription, compact delta, stable event ID, deduplication, coalescing과 internal keepalive no-model-wake 중 하나라도 `unsupported|unknown`이면 formal adapter는 disabled여야 한다.

Codex managed capability는 deterministic fixture만으로 `supported`를 확정하지 않는다. 임시 Codex home/workspace에서 terminal-only 1-agent, delayed nonterminal+terminal 1-agent, staggered terminal 2-agent smoke를 실행한다. ATP manual wait/list 0, 요청 전원 결과, 마지막 terminal 뒤 parent final/report completion, timeout/polling semantic action 0을 transcript로 확인한다. 소비 프로젝트의 각 task에서는 capability child, timeout/wait/list probe, runtime validator, source/install parity를 실행하지 않는다.

### (d) 실제 설치본·session JSONL behavioral regression

문자열 존재만으로 통과시키지 않는다. Historical regression은 2.13.0 관측 JSONL을 직접 parse해 기존 회귀가 실제 executed call로 재현되는지 확인한다.

```bash
python3 tests/runtime-behavior/validate_codex_session.py \
  --profile historical-regression \
  --session-jsonl "$ATP_HISTORICAL_JSONL"
```

기대값: executed `spawn_agent: 1`, `wait_agent: 13`, `list_agents: 2`, wait timeout 11과 `PASS: Codex runtime behavioral regression`.

격리 base bundle에서는 실제 managed orchestration smoke 3종의 `codex exec --json`, scheduling ledger와 report를 아래 profile에 전달한다.

```bash
python3 tests/runtime-behavior/validate_codex_session.py \
  --profile host-managed \
  --session-jsonl "$ATP_RUNTIME_JSONL" \
  --ledger "$ATP_WAIT_WAKE_LEDGER" \
  --report "$ATP_RUNTIME_REPORT" \
  --appendix plugins/atp/docs/development/codex-lifecycle-routing.md
```

각 smoke는 requested/spawn/terminal/collected가 정확히 일치하고 manual wait/list/정상 interrupt/semantic recovery 0이어야 한다. Nonterminal update는 invocation을 `running`으로 유지한다. Ledger의 six-field envelope과 concrete source는 실제 JSONL event에 연결돼야 한다. Report invocation/session completion serialization과 parent final은 마지막 terminal 뒤여야 하고 report 최종 read-only 검증은 parent final 전이어야 한다. 격리 실행은 사용자 전역 plugin cache/settings/hooks와 소비 프로젝트 설정을 변경하지 않는다.

### (e) 링크·index·§N·릴리스 메타데이터 전수 확인

- 신규 appendix는 `plugins/atp/docs/development/index.md`와 `docs/development/index.md` 양쪽에 등록한다.
- 신규 ADR/changes는 각각 `docs/adr/index.md`, `docs/changes/index.md`에 등록한다.
- §8의 끊긴 protocol 인용 검사를 재실행한다. 기존 §N을 재배열하지 않는다.
- §4의 base manifest 4곳 version invariant를 확인하고 add-on version과 `.agents/plugins/marketplace.json`의 versionless 계약을 변경하지 않는다.
- 2.15.0 release에서는 base manifest 4곳의 semantic version이 모두 `2.15.0`, add-on은 기존 버전, `.agents/plugins/marketplace.json`은 versionless인지 확인한다.
- user-facing FAQ는 한국어/영어에서 current tested CLI formal/managed contract unsupported + team disabled, manual wait/list 0, explicit blocker UX, app/IDE unknown, report v2 의미가 동등한지 대조한다.
- 카탈로그 confidence FAQ 한·영 모두에서 every axis/every item marker, `high|mixed|low` 결정 규칙, marker coverage와 aggregate derivation 두 self-check가 동등한지 대조한다.
- ADR-0021·ADR-0022·ADR-0023·ADR-0024와 공개 릴리스인 2026-08-13·2026-08-19 change가 각각 자기 index에 정확히 한 번 등록되고 architecture/change/ADR 사이 교차 링크가 유효한지 확인한다. 미출시 2.14 중간 구현은 ADR-0023의 superseded history로만 보존하고 Changes index에 싣지 않는다.
- Verification이 pending인 동안 architecture/change 문서가 current Codex end-to-end event-driven wake나 전체 validator PASS를 주장하지 않는지 확인한다. 실제 GREEN 후에만 상태를 갱신한다.
