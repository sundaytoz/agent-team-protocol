---
kind: adr
adr_number: "0009"
title: 번들 런타임 플랫폼 중립화 (capability 자가판정) + 3사 capability 데이터 동결 보존
status: accepted
date: 2026-06-11
deciders:
  - template-maintainer
  - stzjungsoo
supersedes: []
related_commits:
  - 45af003
---

# ADR-0009: 번들 런타임 플랫폼 중립화 (capability 자가판정) + 3사 capability 데이터 동결 보존

## 상태

**Accepted** — 2026-06-11. 세션 20260611-093639. ADR-0006(3-플랫폼 지원)·ADR-0008(모델 정책 중립화) 위에 적층.

**부분 supersede**: ADR-0006 이 부여한 "`platform-adapters.md` = capability matrix·플랫폼 Tier 판정표의 권위 SSoT" 지위(결정 1 의 매트릭스 보존 위치, 결정 2 의 판정표 위치)를 **번들 런타임 한정으로** 본 ADR 이 대체한다 — 동결 SSoT 는 본 ADR 의 부록으로 이전된다. ADR-0006 의 나머지 결정(마커 체계 자체, Tier 정의, A-flat 채택 논리, single-read 마이그레이션)과 사람용 설치 문서의 3사 병기는 supersede 대상이 아니다.

---

## 맥락

ATP 스킬은 **워크플로우(phase 척추·게이트·report 스키마)를 강제하는 도구이지, 특정 호스트 CLI 의 도구 사용을 강제하는 도구가 아니다.** 그러나 번들 런타임 문서(`plugins/atp/`)는 특정 3사 플랫폼을 이름으로 열거하고, 각 플랫폼의 Tier 판정·호출 문법·env 변수·배포 단위·모델 슬러그를 활성 규칙으로 하드코딩하고 있었다.

이 구조의 문제:

1. **미열거 호스트 배제**: 열거되지 않은 호스트 CLI 에서 ATP 를 사용하려는 에이전트가 "지원 목록에 없음"을 차단 신호로 오독할 수 있다. 에이전트는 자기 호스트 위에서 실행 중이므로 호스트의 호출 문법·지침파일 규약·모델 라인업을 스스로 알며, 자율 적용이 가능하다.
2. **신선도 부채**: 타 벤더의 슬러그·namespace·문법은 변동 시마다 번들 갱신을 요구한다. ADR-0008 이 모델 슬러그에서 이미 지적한 누수 패턴의 잔존이다.
3. **철학 불일치**: ADR-0008 은 모델 정책을 "플랫폼 이름 판정 → 중립 등급 판정 + 호스트 해석"으로 옮겼다. capability tier·호출 문법·env 레이어는 같은 전환이 미적용 상태였다.

사용자 확정 결정(세션 20260611-093639): ① 적용 범위는 번들 런타임만 — 사람이 따라 치는 설치 문서(README·docs/usage)의 3사 병기는 실용적이므로 유지. ② 실측 capability 데이터는 source-confidence 4단계 마커(ADR-0006 결정 1)를 전수 보존한 채 본 ADR 부록으로 동결 이관.

---

## 결정

### 결정 1 — 번들 런타임 활성 규칙에서 플랫폼 열거 제거 → capability 자가판정으로 치환

번들 4파일(`docs/development/platform-adapters.md`, `docs/development/agent-team-protocol.md`, `skills/task/SKILL.md`, `skills/init/SKILL.md`)의 활성 규칙에서 타 벤더 플랫폼명 열거를 제거한다.

- **Tier A / A-flat / B 정의는 유지** — 이미 capability 조건("subagent spawn 가능한가", "spawn 된 subagent 가 다시 spawn 할 수 있는가")으로 기술되어 플랫폼 독립이다.
- "어느 플랫폼 = 어느 Tier" 판정표, 플랫폼별 호출 문법·env·배포 단위 표는 제거하고, **호스트 capability 자가판정 절차**(Q1 spawn 가능? → Q2 재귀 가능? → Tier 결정, 판정 불가 시 Tier B / parent 상속 안전 폴백)로 치환한다.
- 호스트 고유 사항(호출 토큰·지침파일 규약·모델 슬러그·env 변수)은 **그 호스트 위에서 실행 중인 에이전트가 자율 적용**한다.

**기각 대안**: (a) `platform-adapters.md` 삭제 — 번들·루트 docs·ADR 의 12개+ 링크 붕괴. (b) 파일 개명 — ADR-0007 의 번들 필수 5건 등재 목록(불변 이력)과 충돌. → **파일명·경로 유지 + 내용 중립 재작성** 채택.

### 결정 2 — 3사 capability 데이터를 본 ADR 부록으로 동결 보존

6축 capability matrix·플랫폼 Tier 판정표·토폴로지 해소표·per-platform 어댑터 표·명령/환경변수/명명 대응표·미해결 마커 목록·실증 이력을 **표 셀·마커·박스 문구까지 글자 그대로** 부록 A~F 로 이관한다.

- source-confidence 4단계 마커(ADR-0006 결정 1)는 **개수 단위로 전수 보존**한다 (요약·재서술 금지).
- 부록은 **동결 이력**이다 — 향후 갱신 의무 없음. 새 실측이 생기면 신규 ADR 로 발행한다.
- 번들에서는 해당 데이터를 제거한다. 번들의 중립 재작성본이 부록을 "동결 이력 포인터" 1줄로 역참조한다.

**기각 대안**: (a) 마커 채로 번들 잔류 — 중립화 목적 미달, 신선도 부채 잔존. (b) 마커 제거 후 이관 — ADR-0006 결정 1(마커 전수 보존) 위반. (c) 루트 docs 의 살아있는 참고문서로 이동 — 유지보수 의무가 남아 결국 다시 낡는다(동결 이력이 정직).

### 결정 3 — 모델 tier 매핑(구 §1.6)·spawn=invocation 의무는 번들 유지

- ADR-0008 결정 5 가 구 §1.6 을 자사(Claude Code) 슬러그 매핑 정본으로 지정했으므로, 중립 재작성본의 **§6 "모델 Tier 매핑"** 으로 승계한다 — 자사 확정 슬러그 1셀 + 중립 등급 의미만 잔류, 타 벤더 행은 부록 F 로 동결. 프로토콜 §5 의 매핑 포인터는 `§1.6` → `§6` 으로 절번호만 갱신.
- spawn = invocation 기록 의무(report §8)는 이미 호스트 중립 규율 — 유지. 명문화 계기였던 특정 호스트 전사 사례는 배경 서술로서 부록 F 에 원문 보존하고, 번들은 호스트명 없이 사건만 기술한다.

### 결정 4 — init/task SKILL 지침파일 처리 중립화 + 기능 회귀 0

- 지침파일 3종 고정 열거를 "**자기 호스트 규약 파일 1순위 + 알려진 호환 후보 집합 ls 검사**"로 일반화한다. 호환 후보 집합(파일명 목록)은 레거시 감지용으로 잔존을 허용한다 — 파일명은 활성 강제 규칙이 아니라 감지 입력이다.
- `render_block` 은 호스트 이름 분기(3-케이스 heredoc) 대신 **호출 토큰 주입형 단일 템플릿**으로 전환한다 — 에이전트는 자신이 이번 세션에서 호출된 토큰을 안다.
- **기능 회귀 0 보장**: 마커 기반 멱등 upsert, `atp:migrate` 블록 로직, `$` 토큰의 perl 변수 보간 회피(`BLOCK` env var 경유)는 그대로 보존한다.

---

## 영향

- 번들: `platform-adapters.md` 중립 재작성(제목 "Capability Tier 와 호스트 자가판정"), `agent-team-protocol.md` §2.8/§5 포인터/§8 예시 1줄/관련문서 description 부분 수정, `skills/task/SKILL.md` §0.5·§6 중립화, `skills/init/SKILL.md` §2·§4 중립화.
- 사람용: README·docs/usage 의 3사 병기 유지(범위 밖). `docs/development/index.md`·`docs/development/release-checklist.md`·README 의 platform-adapters 관련 description·기대값만 본 ADR 기준으로 정합.
- 허용 잔존(역사적 명칭·자사 정본) 구역: ADR/TEMPLATE_DEV(이력 문서), platform-adapters §0 배경 1줄, 프로토콜의 과거 세션 배경 서술, §6 자사 Claude Code 슬러그(ADR-0008 정본), init/task SKILL 의 호환 후보 파일명 목록.
- 구 §1.6 절번호가 §6 으로 바뀌므로 활성 문서의 포인터를 일괄 갱신한다. ADR-0008 본문의 "§1.6" 표기는 이력이므로 수정하지 않는다(결정 시점 기준 표기 — 현행 위치는 본 ADR 이 기록).

## 검증

세션 design.md 의 AC-1~AC-15 를 실행 검증으로 통과해야 한다. 핵심:

- 번들 활성 규칙의 타 벤더 플랫폼명 열거 0건 (전수 grep + 허용 구역 수동 분류).
- 신뢰도 마커 전수 보존 — 이관 전 `platform-adapters.md` 의 마커 개수(이관 직전 실측: verified-seed 13 / verified-empirical 16 / cited 33 / TODO:실측 25 / needs_user_verification 6)와 본 ADR 의 마커 개수가 일치하고, 중립 재작성본의 마커 0.
- init 멱등 3회 스모크 + `$` 토큰 보존, migrate 블록 로직 잔존.

---

## 부록 — 동결 보존 데이터 (2026-06-11 이관, 이후 갱신 없음)

> 아래 부록 A~F 는 중립화 직전의 `plugins/atp/docs/development/platform-adapters.md` 에서 글자 그대로 이관한 동결 스냅샷이다. 분류 마커·표 셀·박스 문구를 원문 그대로 보존한다.

## 부록 A — 6축 Capability Matrix (구 §1.1)

연구 결과(source: `capability-research.md`)를 권위 문서로 승격한다. **셀의 분류 마커는 절대 제거하지 않는다.**

분류 범례: `verified-seed`(사전 검증) · `cited`(1차 공식문서 인용) · `TODO:실측`(문서 조각·미게시) · `needs_user_verification`(실제 install/하드웨어에서만 확인)

### 축 1 — 서브에이전트 spawn

| 플랫폼 | 값 | 분류 |
| --- | --- | --- |
| Claude Code | 가능 (Agent 툴) | verified-seed |
| Codex CLI | 가능 (명시 요청 시 spawn, `spawn_agents_on_csv` batch) | **verified-empirical (2026-06-10)** |
| Gemini CLI | 가능 (subagent=동명 tool 위임). **단 subagent→subagent 호출 불가(recursion protection)** | cited |

### 축 2 — per-call model override

| 플랫폼 | 값 | 분류 |
| --- | --- | --- |
| Claude Code | 가능 (Agent per-call override) | verified-seed |
| Codex CLI | 가능 (agent 파일 `model`/`model_reasoning_effort`, 생략 시 parent inherit) | cited |
| Gemini CLI | 가능 (frontmatter `model`, default `inherit`; settings.json override) | cited |

### 축 3 — skill/command 호출 문법

| 플랫폼 | 값 | 분류 |
| --- | --- | --- |
| Claude Code | `/atp:task` (콜론 namespace). `@`=설치 구분자 전용 | verified-seed |
| Codex CLI (번들 skill namespace) | `atp:task` / `atp:init` (`plugin:skill` 콜론 namespace) | verified-empirical (2026-06-10) |
| Codex CLI (호출 토큰) | `$atp:task [요청]` — 단축형 `$task` 도 동일 skill 로 해석 (`$` = skill 멘션 접두; `/skills` 로 목록) | verified-empirical (2026-06-10 사용자 대화형 전사 — 전체형·단축형 모두 명시 호출 인식·본문 로드·버전 보고) + cited (공식 skills docs) |
| Gemini CLI (custom command) | `/cmd` 또는 `/ns:cmd` (콜론 namespace), 충돌 시 `/ext.cmd` (닷) | cited |
| Gemini CLI (subagent 호출) | `@<agent_name>` (프롬프트 앞) | cited |

### 축 4 — 지침파일 규약

| 플랫폼 | 값 | 분류 |
| --- | --- | --- |
| Claude Code | `CLAUDE.md` | verified-seed |
| Codex CLI | `AGENTS.md` | verified-seed |
| Gemini CLI | `GEMINI.md` (기본; manifest `contextFileName` 으로 변경 가능) | cited |

### 축 5 — 확장 배포 단위

| 플랫폼 | 값 | 분류 |
| --- | --- | --- |
| Claude Code | 플러그인 (`.claude-plugin/plugin.json` + marketplace) | verified-seed |
| Codex CLI | 플러그인 (`.codex-plugin/plugin.json` = plugin manifest; marketplace 는 `<repo-root>/.agents/plugins/marketplace.json` 객체형 source) | cited |
| Gemini CLI | extension (`gemini-extension.json`; commands/·skills/·agents/·hooks/) | cited |

### 축 6 — 환경·경로 변수

| 플랫폼 | 값 | 분류 |
| --- | --- | --- |
| Claude Code | `${CLAUDE_PROJECT_DIR}`, `${CLAUDE_PLUGIN_ROOT}` | verified-seed |
| Codex CLI | `PLUGIN_ROOT`/`PLUGIN_DATA`; 호환용 `CLAUDE_PLUGIN_ROOT`/`CLAUDE_PLUGIN_DATA` | cited (hook 한정) / **TODO:실측** (skill 본문 가용성·workspace root) |
| Gemini CLI | `${extensionPath}`, `${workspacePath}`, `${/}` | cited (manifest/hooks 한정) / **TODO:실측** (skill 본문) |

### 미해결 마커 목록

- [verified-empirical 2026-06-10 · codex-cli 0.138.0] Codex subagent spawn 실증 — 세션 20260610-154723 사용자 대화형 전사에서 Codex 가 subagent **2개 spawn 확인**. 축1 Codex 셀 cited → verified-empirical 격상 근거. (spawn 실증 ≠ install 스모크 전부 완료 — 아래 needs_user_verification "세 플랫폼 install 후 task/init 스모크" 항목과 구분 유지.)
- [verified-empirical 2026-06-10] Codex 번들 skill = `atp:task`/`atp:init` (`plugin:skill` 콜론 namespace, codex exec 런타임 레지스트리). 호출 = **`$atp:task`** (전체형) 및 **`$task`** (단축형) — 둘 다 사용자 대화형 전사로 확인: 명시 호출 인식 + SKILL 본문·plugin.json Read + 설치 버전 정확 보고. 공식 docs `$` skill 멘션 접두 cited. `skills:"./skills/"` 선언 후 재설치 시 skill 노출 확인.
- [교훈 — 판정 오류 정정 이력] 한때 호출 토큰을 `/task` 로 단정했으나(codex exec 런타임 self-report 근거) 이는 모델 추측이었다. **런타임 self-report 는 컨텍스트에 주입되는 값(skill id 등)에만 유효하고, UI 입력 토큰의 근거가 될 수 없다.** UI 토큰은 공식 docs cited 또는 대화형 실측만 인정.
- [verified-empirical 2026-06-09 · codex-cli 0.138.0] Codex 설치 CLI 정본 확인 — `codex plugin {add,list,remove,marketplace}` 실제 서브명령. `atp@agent-team-protocol` 1.4.0 / `atp-graphify` 1.2.0 = installed+enabled, marketplace=`.agents/plugins/marketplace.json`, cache=`~/.codex/plugins/cache/agent-team-protocol/atp/1.4.0`(local 아닌 버전드). 공식 OpenAI 마켓플레이스도 전부 `.agents/plugins/marketplace.json`+`plugins/<name>` 실서브디렉토리 사용 → F-3PLAT-5 정본 방향 corroborate.
- [TODO:실측] `.codex-plugin/plugin.json` 의 `skills` 선언이 skill 노출 충분조건인지 (필요조건=정본 스키마 정합은 확인).
- [TODO:실측] Codex `PLUGIN_ROOT`/`CLAUDE_PLUGIN_ROOT` 의 skill·agent 본문(hook 외) 가용성.
- [TODO:실측] Gemini `${extensionPath}`/`${workspacePath}` 의 skill/agent 본문 가용성.
- [needs_user_verification] 세 플랫폼 실제 install 후 `task`/`init` 스모크.

## 부록 B — 플랫폼 Tier 판정표 (구 §1.3)

| 플랫폼 | Tier 잠정 판정 | 근거 | 확정 여부 |
| --- | --- | --- | --- |
| Claude Code | **Tier A (확정)** | Agent 툴 spawn — verified-seed | 확정 |
| Codex CLI | **Tier A (spawn verified-empirical 2026-06-10, install-smoke 보류)** | subagent 2개 spawn 실증(사용자 대화형 전사) + agent별 model 설정 — cited | needs_user_verification |
| Gemini CLI | **Tier A-flat (doc-cited, install-smoke 보류)** | subagent 시스템 존재 + recursion protection 제약 → 평탄 구조 채택 — cited | needs_user_verification |

> `needs_user_verification`: 실제 install + spawn 스모크 전까지 잠정 판정. 실패 시 해당 플랫폼은 Tier B 로 자동 격하(구 1.5 Tier B 격하 트리거 참조).

## 부록 C — Gemini Tier A-flat 토폴로지 해소표 (구 §1.4)

Gemini 의 recursion protection(subagent→subagent 호출 불가)은 ATP 의 2단 위임 체인(L1→L2→L3)의 L2→L3 간선을 막는다. 이를 Tier A-flat 평탄화로 해소한다.

| 항목 | Claude/Codex (Tier A) | Gemini (Tier A-flat) | Tier B (폴백) |
| --- | --- | --- | --- |
| spawn | advisor 가 worker spawn | orchestrator 가 worker 직접 spawn | spawn 없음 |
| 위임 깊이 | 2단 (L1→L2→L3) | 1단 평탄 (L1→L2, L1→L3) | 0단 (단일 agent) |
| worker 병렬 | advisor 내부 병렬 | orchestrator fan-out 병렬 | 순차 self-check |
| advisor 역할 | 계획+spawn+취합 | 계획 반환 → orchestrator 가 spawn → advisor 취합 | orchestrator self-check |
| 게이트 | 유지 | 유지 | 유지 |
| report 스키마(§8) | 유지 | 유지 | 유지 |
| 검증규율 | 유지 | 유지 | 유지 |
| 격하 대상 | 없음 | L2→L3 간선만 평탄화 | 병렬 → 순차 self-check |

**근거**: (1) recursion 제약은 capability 부재가 아니라 토폴로지 제약이므로 Tier B 격하는 과하다. (2) flat fan-out 은 spawn 능력을 그대로 활용하면서 재귀만 회피한다. (3) report 스키마·게이트는 호출 토폴로지와 독립이므로 평탄화해도 무손실. (4) advisor 가 "spawn 주체"에서 "계획 산출 주체"로 역할만 이동 — 산출물 계약(보고서 스키마 §8) 불변.

## 부록 D — Per-Platform 어댑터 (구 §2.1~2.3)

### Claude Code 어댑터

| 항목 | 값 |
| --- | --- |
| 호출 | `/atp:task <요청>`, `/atp:init` (콜론 namespace) |
| 지침파일 | `CLAUDE.md` |
| 프로젝트 루트 env | `${CLAUDE_PROJECT_DIR}` |
| 플러그인 루트 env | `${CLAUDE_PLUGIN_ROOT}` |
| 배포 단위 | `.claude-plugin/plugin.json` + marketplace |
| Model tier 매핑 | small=`haiku` / medium=`sonnet` / large=`opus` (구 §1.6, as-of 2026-06); effort 미지원(no-op) |
| Tier | A (확정) |

### Codex CLI 어댑터

| 항목 | 값 |
| --- | --- |
| 호출 | `$atp:task [요청]` (`$` skill 멘션 접두 — verified-empirical 2026-06-10 사용자 대화형 전사 + cited); skill id `atp:task` (`plugin:skill` 콜론, verified-empirical) |
| 지침파일 | `AGENTS.md` |
| 플러그인 루트 env | `PLUGIN_ROOT` (+ 호환 `CLAUDE_PLUGIN_ROOT`, hook 한정) |
| 쓰기 데이터 env | `PLUGIN_DATA` (+ 호환 `CLAUDE_PLUGIN_DATA`) |
| 배포 단위 | plugin manifest `.codex-plugin/plugin.json` (+ `skills:"./skills/"` 선언); marketplace 정본 `.agents/plugins/marketplace.json` (객체형 source) |
| Model tier 매핑 | 경량/표준/최상위 등급 (구 §1.6 — 구체 슬러그 미기재); effort=`model_reasoning_effort` (cited) |
| Tier | A (spawn verified-empirical 2026-06-10, install-smoke 보류) |

> **Codex 번들 skill namespace — verified-empirical (2026-06-10, codex-cli 0.138.0)**
>
> 번들 skill = `atp:task`/`atp:init` (`plugin:skill` 콜론 namespace — 런타임 레지스트리 직접 확인). 호출 **`$atp:task [요청]`** (사용자 대화형 전사 2026-06-10 — 명시 호출 인식·SKILL 본문 로드·설치 버전 정확 보고. 공식 docs `$` 접두 cited). `skills:"./skills/"` 선언 후 재설치 시 skill 노출 확인됨(충분조건 충족).
> 단축형 `$task` 도 동일 skill 로 해석됨(전사 확인 2026-06-10). 잔여 TODO:실측: env var `PLUGIN_ROOT`/`CLAUDE_PLUGIN_ROOT` 의 skill·agent 본문(hook 외) 가용성.
> marketplace 정본은 `.agents/plugins/marketplace.json`. `.codex-plugin/marketplace.json` 은 Claude 미러로 Codex 가 읽지 않음.
> env var `PLUGIN_ROOT`/`CLAUDE_PLUGIN_ROOT` 의 skill·agent 본문(hook 외) 가용성도 TODO:실측.

### Gemini CLI 어댑터

| 항목 | 값 |
| --- | --- |
| 호출 (command) | `/atp:task <요청>`, `/atp:init` (콜론 namespace) |
| subagent 명시 호출 | `@<agent_name>` (프롬프트 앞 — subagent 위임, 명령 호출 아님) |
| 지침파일 | `GEMINI.md` (기본; `contextFileName` 으로 변경 가능) |
| 확장 루트 env | `${extensionPath}` (manifest/hooks 한정) |
| 프로젝트 루트 env | `${workspacePath}` (manifest/hooks 한정) |
| 배포 단위 | `gemini-extension.json` (extension) |
| Model tier 매핑 | 경량/표준/최상위 등급 (구 §1.6 — 구체 슬러그 미기재); effort TODO:실측 |
| Tier | A-flat (doc-cited, install-smoke 보류) |

> **Gemini 배포형 — TODO:실측 박스**
>
> Gemini 명령 배포 형태(custom command `.toml` vs skill SKILL.md)와 정확한 namespace 표기는 install 스모크 전 미확정. 현재 설계 기준: "custom command 우선 + skill 폴백".
>
> `${extensionPath}`/`${workspacePath}` 의 skill/agent 본문(manifest·hooks 외) 가용성도 TODO:실측.

## 부록 E — 명령 매핑표 / 파일·디렉토리 명명표 / 환경변수 대응표 (구 §2.4 외)

### 명령 매핑표 (구 §2.4)

| 공통 식별자 | Claude Code | Codex (※번들 namespace 실측 TODO) | Gemini (※배포형 실측 TODO) |
| --- | --- | --- | --- |
| `task` | `/atp:task <요청>` | `$atp:task <요청>` (verified-empirical 2026-06-10) | `/atp:task <요청>` `TODO:실측` |
| `init` | `/atp:init` | `$atp:init` | `/atp:init` `TODO:실측` |

> `/task` 는 ATP 의 공식 사용자 입력명이 아니다. legacy 표기가 남아 있다면 플랫폼별 실제 입력명으로 교정한다.

### 파일과 디렉토리 명명

ATP 프로토콜 자체의 산출물 경로:

| 개념 | 현재 권위 경로 | Claude legacy | 비고 |
| --- | --- | --- | --- |
| 세션 공유 상태 | `.atp/work-session/<sid>/` | `.claude/work-session/<sid>/` (자동 이관 대상 — legacy) | F-3PLAT-3 single-read 전환 완료 |
| 프로젝트 지침 | 플랫폼별 파일 | `CLAUDE.md` | Codex: `AGENTS.md`, Gemini: `GEMINI.md` |
| 플러그인 매니페스트 | 플랫폼별 디렉토리 | `.claude-plugin/` | Codex: `.codex-plugin/plugin.json`(manifest) + marketplace 정본 `.agents/plugins/marketplace.json` |

### 환경 변수 — 플랫폼별 대응표

| 논리 변수 | Claude Code | Codex CLI | Gemini CLI |
| --- | --- | --- | --- |
| `${ATP_PROJECT_DIR}` | `${CLAUDE_PROJECT_DIR}` | workspace root (TODO:실측) | `${workspacePath}` (manifest/hooks 한정, TODO:실측) |
| `${ATP_PLUGIN_ROOT}` | `${CLAUDE_PLUGIN_ROOT}` | `PLUGIN_ROOT` (+ 호환 `CLAUDE_PLUGIN_ROOT`) | `${extensionPath}` (manifest/hooks 한정, TODO:실측) |

## 부록 F — 잔여 플랫폼 고유 구획 (구 §0.4 / §1.6 / 문서 작성 규칙 / 변경 우선순위 / 구 검증 체크리스트 / spawn 기록 의무 계기 원문)

### `@` 오용 경고 (구 §0.4)

> **`@` 주의 — 플랫폼별로 의미가 다르다**:
>
> - Claude Code: `@` 는 마켓플레이스 설치 구분자(`/plugin install atp@agent-team-protocol`) 전용. 명령 호출 문법 아님.
> - Codex: `@` 는 config 식별자(`plugin@marketplace`) 전용. skill 명시 호출 토큰은 **`$`** (skill 멘션 접두 — cited 공식 docs "type `$` to mention a skill"). 번들 skill 은 `plugin:skill` 콜론 namespace 로 노출되어 **`$atp:task`** 로 호출(verified-empirical 2026-06-10: 사용자 대화형 전사 — Codex 가 "explicitly invoked" 인식 + SKILL 본문 로드).
> - Gemini: `@<agent_name>` 은 subagent 명시 위임 문법(`@codebase_investigator ...`) — 명령 호출이 아닌 서브에이전트 호출.
>
> Claude 에서 `/atp@task` 표기는 설치 구분자와 호출을 혼동한 것이므로 쓰지 않는다.

### Model Tier 매핑 (구 §1.6)

ATP 모델 정책(프로토콜 §5)은 플랫폼 중립 tier(`small`/`medium`/`large`)로 판단하고, 각 플랫폼이 자기 모델 라인업으로 해석한다. **자사 플랫폼(Claude Code)만 구체 슬러그를 확정 기재**하고, 타 플랫폼은 등급 의미 + 신뢰도 마커로 기술한다 — 타 벤더 구체 슬러그 하드코딩은 모델명 누수의 역방향이므로 금지.

| tier | 의미(등급) | Claude Code (확정 슬러그, as-of 2026-06) | Codex CLI | Gemini CLI |
| --- | --- | --- | --- | --- |
| small | 라인업 경량 등급 | `haiku` | 경량 등급 모델 (cited) | 경량 등급 모델 (cited) |
| medium | 라인업 표준 등급 | `sonnet` | 표준 등급 모델 (cited) | 표준 등급 모델 (cited) |
| large | 라인업 최상위 등급 | `opus` | 최상위 등급 모델 (cited) | 최상위 등급 모델 (cited) |

| 항목 | Claude Code | Codex CLI | Gemini CLI |
| --- | --- | --- | --- |
| per-call override 문법 | Agent 툴 `model` 파라미터 (verified-seed) | agent 파일 `model` (생략 시 parent inherit, cited) | frontmatter `model` (default inherit, cited) |
| effort 노브 (프로토콜 §5.5) | 미지원 — effort=no-op (verified-seed) | `model_reasoning_effort` (low/medium/high; cited) | TODO:실측 |
| 자기 모델 가시성 (§5.6 cap 판정용) | 런타임 self-report — 컨텍스트 주입 (verified-seed) | TODO:실측 | TODO:실측 |

> **신선도(staleness) 취급**: 구체 슬러그(haiku/sonnet/opus)는 모델 라인업 변동 시 `as-of <date>` 스탬프를 갱신한다. tier→등급 의미·매핑 원칙은 라인업 변동과 무관하게 안정. Codex/Gemini 는 슬러그를 미기재하므로 신선도 관리 대상이 슬러그 1셀(Claude Code)로 국소화된다. 자기 모델 가시성이 TODO:실측인 플랫폼에서 cap 자기 tier 판정이 불가하면 프로토콜 §5.6 의 안전 폴백(override 미지정·parent 상속, `resolved_model: inherit`)을 적용한다.

### 문서 작성 규칙 (구 — 공통 프로토콜 문서 / 사용자 설치 문서 / 지침 삽입 블록)

공통 프로토콜 문서(`docs/development/agent-team-protocol.md`, advisor 정의, skill 본문처럼 3개 플랫폼이 함께 읽는 문서) 규칙:

- 제목과 본문 기본 표기는 `task 명령`, `init 명령`, `ATP task`, `ATP init` 처럼 플랫폼 중립적으로 쓴다.
- 실제 입력 예시가 필요하면 반드시 Claude Code / Codex / Gemini 를 나누어 표기한다.
- 3사 중 어느 하나만 단독 권위 표기로 쓰지 않는다.
- `/task` 는 새 문서에 쓰지 않는다.

사용자 설치/사용 문서(README, `docs/usage/faq.md`, `docs/usage/setup-checklist.md`)는 3사를 모두 병기한다. 예:

```md
ATP task smoke test:

- Claude Code: `/atp:task 안녕, 에이전트 팀이 로드됐는지 확인만 해줘`
- Codex: `$atp:task 안녕, 에이전트 팀이 로드됐는지 확인만 해줘` (verified-empirical 2026-06-10)
- Gemini: `/atp:task 안녕, 에이전트 팀이 로드됐는지 확인만 해줘` (TODO:실측 — 배포형 확정 전)
```

`init` 이 소비 프로젝트에 삽입하는 안내 블록은 대상 플랫폼에 맞는 실제 입력명을 사용한다:

| 대상 파일 | 입력 예시 |
| --- | --- |
| `CLAUDE.md` | `/atp:task [요청]` |
| `AGENTS.md` | `$atp:task [요청]` (verified-empirical) |
| `GEMINI.md` | `/atp:task [요청]` (TODO:실측 caveat 포함) |

### 변경 우선순위 (구 — 이관 시점 상태)

1. `skills/init/SKILL.md` 의 CLAUDE.md 단독 생성 → 3-지침파일 감지+옵트인 생성으로 확장.
2. README/faq/setup-checklist 의 smoke test 예시를 2사 → 3사(+Gemini TODO:실측) 병기로 확장.
3. `.claude/work-session/` → `.atp/work-session/` 경로 이전: **완료 (F-3PLAT-3)** — single-read 전환 + `atp:migrate` 자기삭제 블록으로 소비 프로젝트 1회성 자동 이관.
4. Gemini 실제 배포 산출물(extension.json, commands/*.toml) 생성: **이월(배포 패키징 후속)**.
5. `.claude-plugin/` / `.codex-plugin/` 매니페스트 `description` 에 Gemini 추가: **이월(배포 패키징 후속)**.

### 구 검증 체크리스트 (이관 시점 상태)

- [ ] `/task` 가 공식 사용자 입력명처럼 보이는 문서가 남아 있지 않은가?
- [ ] Claude Code 안내에는 `/atp:task` (콜론), Codex 안내에는 `$atp:task` 가 쓰였는가? (`/task` 단독·`$task` 주 표기 단정·`@`-멘션 가설 표기 잔존 0 — 실측 검증된 `$task` 단축형 **별칭 병기**는 허용)
- [ ] Codex marketplace 정본이 `.agents/plugins/marketplace.json` 으로 기술되고, `.codex-plugin/marketplace.json` 이 Codex 정본처럼 표기되지 않았는가?
- [ ] `@` 를 명령 호출 문법으로 쓴 표기(`/atp@task`)가 남아 있지 않은가?
- [ ] 공통 문서에서 특정 플랫폼 명령 문법 하나만 권위 표기로 쓰지 않았는가?
- [ ] capability matrix 의 TODO:실측 마커가 검증 없이 제거되지 않았는가?
- [ ] Gemini Tier A-flat 토폴로지 해소표가 존재하는가?
- [ ] `.atp/work-session/` 이 권위 경로로 기술되고, `.claude/work-session/` 이 legacy 라벨(자동 이관 대상) 외에서 권위로 남아있지 않은가?

### spawn = invocation 기록 의무 — 명문화 계기 원문 (구 §1.2 박스)

> **spawn = invocation 기록 의무**: spawn 된 subagent 는 capability tier 와 무관하게 report 스키마(프로토콜 §8) invocation 으로 기록한다 — layer + parent_invocation_id 필수. Codex 전사(20260610-154723)에서 subagent 2개 spawn 이 report Invocations 에 누락된 사례가 본 의무 명문화의 계기다(§8 위반).

---

## 관련 문서

- [ADR-0006](./ADR-0006-three-platform-support.md) — 3-플랫폼 지원 (본 ADR 이 SSoT 위치를 부분 supersede 하는 원본)
- [ADR-0007](./ADR-0007-plugin-root-subdirectory.md) — 번들 필수 5건 등재 (platform-adapters 파일명 유지 근거)
- [ADR-0008](./ADR-0008-platform-neutral-model-policy.md) — 모델 정책 중립화 (동일 철학의 선행 적용)
- [platform-adapters.md](../../plugins/atp/docs/development/platform-adapters.md) — 중립 재작성본 (capability 자가판정 권위)
