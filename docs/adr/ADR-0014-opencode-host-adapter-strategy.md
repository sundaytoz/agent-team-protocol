---
kind: adr
adr_number: "0014"
title: opencode 호스트 어댑터 전략 (4번째 Layer-2) — generator 기반 CLI installer + 잠정 capability tier (구현 보류)
status: accepted
date: 2026-06-24
deciders:
  - stzjungsoo
supersedes: []
related_commits: []
---

# ADR-0014: opencode 호스트 어댑터 전략 (4번째 Layer-2) — generator 기반 CLI installer + 잠정 capability tier (구현 보류)

## 상태

**Accepted** — 2026-06-24. ADR-0006(3-플랫폼 지원) 의 호스트 범위를 **opencode(4번째)** 로 확장한다. 채택한 이식 전략을 **같은 날 수작업 PoC 로 실측 검증**했다(opencode 1.17.9, project-scoped `.opencode/`, 디렉토리 `~/workspace/atp-opencode-poc`). 핵심 메커니즘(command·agent 로드·Tier 스폰·permission 격리·경로치환)은 전부 동작 확인됐고, 미확정이던 `TODO:실측` 3건(재귀·모델·LSP)은 §검증에서 해소됐다.

**여전히 보류(D7)**: 실제 generator/installer 빌드 + `platform-adapters.md` SSoT 갱신 + 정식 install 스모크는 후속이다 — 결정(이식 방식)은 accepted, 실행만 미착수.

ADR-0008(모델정책 중립화)·ADR-0009(번들 런타임 중립화·capability 자가판정)·ADR-0013(§N 앵커 = 공개 계약) 위에 적층한다. supersede 아님.

---

## 맥락

### 요청

사용자 요청: *"opencode 라는 IDE 에 우리 플러그인을 설치 가능하게 하려면 어떻게 하는 게 좋을까?"* — atp 를 4번째 호스트(opencode)에 배포하는 방법 결정.

### opencode 프리미티브 조사 (cited — opencode.ai 공식문서)

| primitive | 위치 | 형식·제약 |
|---|---|---|
| agent | `.opencode/agents/`(프로젝트) · `~/.config/opencode/agents/`(전역) | md frontmatter: `mode`(primary/subagent/all)·`model`·`permission`{allow\|deny\|ask, 와일드카드}·`description`(필수). subagent 는 primary 가 **Task 툴로 호출** |
| command | `.opencode/commands/` · `~/.config/opencode/commands/` | md frontmatter: `description`·`agent`·`model`·`subtask`. body=프롬프트, `$ARGUMENTS`/`$1`·`` !`sh` ``·`@file` 지원 |
| plugin (JS/TS) | npm `"plugin":[...]` 또는 plugins 디렉토리 | hook 이벤트(40+) + custom tool **만**. agent/command 등록 불가, config-injection hook **부재** |
| 공유 문서 | opencode.json `instructions:[glob]` + `{file:path}` 치환 | 런타임 주입 |
| 전역 config | `~/.config/opencode/` | — |
| marketplace / plugin-root var | **없음** | `/plugin install name@mp` 대응물 없음, `${CLAUDE_PLUGIN_ROOT}` 대응 변수 없음 |

### 기존 아키텍처 (이 결정의 토대)

- `platform-adapters.md` 가 3-layer 구조(Layer0 protocol core / Layer1 capability tier / Layer2 per-platform adapter)의 권위 SSoT (ADR-0006·0009). Claude Code / Codex / Gemini 가 이미 Layer2 어댑터.
- capability tier: **Tier A**(spawn → 2단 위임) / **Tier A-flat**(spawn 가능, subagent 재귀 금지 → 1단 평탄 fan-out) / **Tier B**(spawn 불가 → 단일 agent self-checklist).
- 모델 정책 중립(ADR-0008): tier S/M/L → 호스트가 자기 라인업 slug 로 해석. effort 직교 노브(미지원 시 no-op).
- §N 앵커는 사실상 공개 계약(ADR-0013) — 호스트 무관 보존.

### 핵심 차이 — passive 어댑터 vs 능동 어댑터

기존 어댑터(claude/codex)는 **passive**: 호스트가 번들 md 를 plugin-root 변수 치환으로 **직접 read**, 별도 변환 없음. opencode 는 두 가지로 인해 **능동 변환**이 불가피하다:

1. **plugin-root 변수 부재** — agent/skill 본문의 `${CLAUDE_PLUGIN_ROOT}/docs/...` 참조를 해소할 호스트 변수가 없다.
2. **frontmatter 스키마 상이** — atp 의 `tools: Read, Write, ...` 리스트와 opencode 의 `permission`{allow/deny/ask} 객체 + `mode`/`model` 이 다르다.

추가로 **marketplace 부재** → 한 줄 설치 대응물이 없다.

### install-hook 부재 — 기각 패턴의 선례 일치

ADR-0006 결정4 가 install/update lifecycle 훅이 3사 전수 부재함을 확정했고, 소비 프로젝트 파일 변경은 **사용자 액션 또는 orchestrator 런타임 실행으로만** 가능하다고 기록했다. 본 세션 조사는 opencode plugin 도 agent/command 를 등록할 수 없음(hook+tool only, config hook 부재 — cited)을 확인해 이 선례와 일치한다. 따라서 "plugin 한 줄로 자동 등록" 류는 구조적으로 불가하며, 정공법은 **사용자 호출형 installer** 다.

### 미확정 항목 (PoC 로 해소 — 2026-06-24)

- ~~[TODO:실측] subagent→subagent 재귀~~ → **해소: 재귀 deny**(subagent 세션에 `task:deny` 주입) → **Tier A-flat 확정**.
- ~~[TODO:실측] per-call 모델 override~~ → **해소: per-agent 정적만**. 게다가 provider 슬러그 비호환(`anthropic/*` 미존재) → `model:` 생략(상속)이 정답.
- ~~[TODO:실측] LSP 툴 노출~~ → **해소: 기본 off**(`all LSPs are disabled`) → generator 가 LSP drop / grep 매핑.
- ~~[needs_user_verification] install 후 실동작~~ → **PoC 검증됨**(§검증). 단 정식 generator/installer 산출물 스모크는 D7 후속.

---

## 결정

### D1 — opencode = platform-adapters.md 의 4번째 Layer-2 어댑터

Layer0(protocol core)·canonical agents(13+3)·skills 를 **무수정** 유지하고, opencode 를 Layer2 per-platform adapter 로 추가한다. 기존 멀티호스트 모델의 의도된 확장점에 끼운다 — 신규 구조가 아니다.

### D2 — 배포 = 사용자 호출형 CLI installer (npm `bin`)

`npx <pkg> install [--global|--project]` 가 변환 산출물을 opencode config 디렉토리(`~/.config/opencode/` 또는 `.opencode/`)에 복사하고 `uninstall` 을 제공한다. **startup-sync plugin** 안과 **수동 복사** 안은 기각(아래 §기각 대안).

### D3 — generator 기반 능동 변환 (canonical 단일 소스 유지)

canonical(`plugins/atp/agents/*.md`, `plugins/atp/skills/*/SKILL.md`, atp-graphify 동일)을 **단일 진실로 유지**하고, generator 가 호스트별 산출물을 방출한다:

- frontmatter: `tools:` 리스트 → opencode `permission`{allow/deny/ask} 객체 변환, `mode: subagent` 부여(advisor/worker), `model` 부여(D4).
- 본문: `${CLAUDE_PLUGIN_ROOT}/docs/...` → opencode 배치 경로(예 `~/.config/opencode/atp/docs/...`)로 치환. 큰 프로토콜 문서는 전역 `instructions` 자동주입(컨텍스트 bloat) 대신 본문 내 `@file`/`{file:}` **온디맨드** 참조 선호.
- skills(`/atp:task`,`/atp:init`) → opencode commands(`$ARGUMENTS`).

**4번째 수작업 사본 금지** — 13+3 agent 를 손으로 복제하면 드리프트가 발생한다. generator 가 유일한 방출 경로.

### D4 — 모델: **provider 슬러그 하드코딩 금지, 기본 `model:` 생략(상속)** (PoC 실측)

tier S/M/L 정책(ADR-0008)은 유지하되 agent frontmatter 에 provider 슬러그를 **박지 않는다**. 실측: `model: anthropic/claude-sonnet-4-5` → `ProviderModelNotFoundError`(사용자 환경에 직접 `anthropic/` provider 없음; `opencode models` 상 Claude 는 `amazon-bedrock/anthropic.claude-*-v1:0` 등 provider 별 슬러그가 제각각). → **generator 기본 = `model:` 생략 → subagent 가 primary 모델 상속**(어느 provider든 동작). tier→구체 slug 는 `--provider` install 옵션일 때만. per-call override 부재·effort no-op 는 수용.

### D5 — capability tier = **A-flat 확정** (PoC 실측)

opencode 는 subagent+Task 스폰을 지원하나(Tier A 스폰 동작 확인), **subagent 세션에 `task:deny` 가 주입되어 subagent→subagent 재귀가 차단**된다(2026-06-24 실측). → **Tier A-flat** 확정(Gemini 와 동일). ATP 의 L2→L3(advisor→worker)는 orchestrator 직접 fan-out 으로 평탄화 — ADR-0006 의 Tier A-flat machinery 재사용. 게이트(§6)·보고서 스키마·검증 규율은 토폴로지 독립이라 무손실.

### D6 — 어댑터 코드 격리 배치

신규 어댑터 코드(`package.json` + `bin` + generator)는 신규 sibling 디렉토리(예 `adapters/opencode/`)에 **격리**한다. 레포 루트는 prose/markdown 유지 — 기존 `.claude-plugin`/`.codex-plugin`/`.agents/plugins` marketplace 와 `plugins/atp(-graphify)` 번들은 무영향.

### D7 — 구현 · SSoT 갱신 보류 (사용자 지시)

다음은 본 ADR 범위 밖이며 구현 착수 시 수행한다:

- 실제 generator/installer 빌드 + tool→permission 매핑표 + tier→slug 표 확정.
- `platform-adapters.md` capability matrix 에 opencode 행 추가 — **본 ADR 에서는 하지 않는다**(미검증 플랫폼을 SSoT 에 supported 로 올리지 않기 위함). 스모크 통과 시 갱신.
- install 스모크([needs_user_verification]).

---

## 검증 (수작업 PoC, 2026-06-24)

generator/installer 없이 agent 2개(design-advisor·code-writer)+command 1개를 손변환해 실제 opencode(1.17.9, project-scoped `.opencode/`)에서 실행·실측. verdict:

| 항목 | 결과 | 근거 |
|---|---|---|
| command 로드·실행 | ✅ | `command=atp-task` |
| agent frontmatter 로드 | ✅ | `opencode agent list` 파싱(각 25 rule) |
| Tier 스폰 (primary→subagent) | ✅ | `task` allow + child `parentID`=primary, `agent=atp-design-advisor` 구동 |
| worker 툴격리 (`tools`→`permission`) | ✅ | code-writer `bash:deny` + read/edit/write/grep/glob allow 파싱·적용 |
| 경로치환 (`${CLAUDE_PLUGIN_ROOT}/docs`→`@`) | ✅ | code-writer 가 `ATP-PATH-REWRITE-OK` 인용 |
| 재귀 | ❌(의도) → **A-flat** | subagent `task:deny` |
| 모델 `anthropic/*` 슬러그 | ❌ → 생략 상속으로 해결 | `ProviderModelNotFoundError` |
| LSP | off | `all LSPs are disabled` |

부수: `--agent <subagent>` 로 subagent 를 primary 호출 불가(build 폴백). **배포 블로커 0** (모델 슬러그 생략 조건).

## 영향

| 대상 | 영향 |
|---|---|
| Layer0 protocol core, canonical agents 13+3, skills | **무수정** |
| `.claude-plugin`/`.codex-plugin`/`.agents/plugins` marketplace, `plugins/atp(-graphify)` 번들 | **무영향** |
| 모델정책(ADR-0008), §N 인용망(ADR-0013), capability 자가판정(ADR-0009) | 재사용·보존 |
| 신규 `adapters/opencode/`(generator+bin+package.json) | **추가형(additive)** — 구현 시 |
| 본 ADR + `docs/adr/index.md` 행 | 추가 |

**구조 무손상 확인**: 본 결정은 전부 additive 다. 유일한 신규성은 "passive 어댑터 → 능동 generator + JS 툴체인 도입"이며, 루트에 `package.json` 이 없는 현 상태를 `adapters/opencode/` 격리로 보존한다. 이 능동 산출물 생성은 ADR-0006 결정5 가 이월한 **Gemini F-3PLAT-4**(gemini-extension.json·commands/*.toml 생성)와 동형 — 향후 범용 "adapter 산출물 generator" 로 일반화할 여지가 있다(별도 결정으로 다룸).

---

## 검토한 대안

### startup-sync JS plugin (opencode.json `"plugin"` 한 줄)

부팅 시 plugin 이 번들 md 를 agents 디렉토리에 write. **기각**: (1) opencode plugin 은 agent 등록 불가·config hook 부재(cited)라 파일 write 우회가 필요한데, 이는 ADR-0006 결정4 가 기각한 "install-hook 부재 → SessionStart 침습 우회"와 동형. (2) agent 탐색 vs plugin 로드 순서 race. (3) 매 부팅 사용자 config 디렉토리 침범.

### 수작업 4번째 사본 (`opencode/` 에 변환된 md 직접 커밋)

**기각**: canonical 단일소스 원칙 위반. 13+3 agent + skills 를 손으로 유지 → claude/codex/opencode 간 드리프트 불가피. generator(D3)가 이를 구조적으로 차단.

### plugin-only(JS) 자동 등록 기대

**기각(불가)**: opencode plugin 은 hook 이벤트 + custom tool 만 제공하고 agent/command 를 선언적으로 등록하는 메커니즘이 없다(cited).

---

## 관련 문서

- [ADR-0006](./ADR-0006-three-platform-support.md) — 3-플랫폼 지원·capability tier·결정4(install-hook 부재)·결정5(Gemini 산출물 이월). 본 ADR 의 직접 전제.
- [ADR-0008](./ADR-0008-platform-neutral-model-policy.md) — tier S/M/L 모델 중립화. D4 의 토대.
- [ADR-0009](./ADR-0009-bundle-runtime-platform-neutralization.md) — 번들 런타임 중립화·capability 자가판정.
- [ADR-0013](./ADR-0013-protocol-core-section-on-demand-routing.md) — §N 앵커 = 공개 계약(호스트 무관 보존).
- [platform-adapters.md](../development/platform-adapters.md) — capability tier·per-platform adapter SSoT (구현 시 opencode 행 추가 대상).
- opencode 공식문서 (cited): [plugins](https://opencode.ai/docs/plugins/) · [agents](https://opencode.ai/docs/agents/) · [commands](https://opencode.ai/docs/commands/) · [config](https://opencode.ai/docs/config/)
