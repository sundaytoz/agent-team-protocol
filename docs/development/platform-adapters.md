---
kind: development
title: Platform Adapters
description: Claude Code / Codex / Gemini 3개 플랫폼을 지원할 때 ATP 공통 개념과 플랫폼별 명령 문법·tier 를 분리하는 규칙.
owner: template-maintainer
stability: draft
last_reviewed: 2026-06-09
---

# Platform Adapters

ATP 는 Claude Code 에서 시작된 프로토콜이지만, 3개 CLI(Claude Code / Codex CLI / Gemini CLI) 를 함께 지원한다. 이 문서는 **공통 프로토콜 코어**, **capability tier 분류**, **플랫폼별 어댑터** 를 3층으로 분리하여 플랫폼 차이가 프로토콜 본체에 섞이지 않도록 한다.

---

## Layer 0 — Protocol Core (플랫폼 중립)

### 0.1 공통 명령 식별자

ATP 내부의 공통 명령 식별자는 `task`, `init` 이다. 스킬 파일명·프로토콜 설명·내부 설계 문서는 이 중립 이름을 사용한다. 실제 사용자 입력 문법은 호스트 플랫폼이 결정한다(Layer 2 per-platform adapter 참조).

### 0.2 공통 산출물 경로

> **현재 권위 경로**: `.atp/work-session/<sid>/`
>
> 새 세션·문서·구현 모두 이 경로를 기본값으로 사용한다. (F-3PLAT-3 single-read 전환 완료)

> **legacy**: `.claude/work-session/` 은 이전 버전의 산출물 경로다. `init` 의 `atp:migrate` 블록으로 자동 이관된다. 신규 프로젝트는 이 경로를 사용하지 않는다.

### 0.3 논리 환경 변수

공통 문서에서는 논리 변수명을 사용하고, 플랫폼별 실제 변수는 Layer 2 에서만 기재한다.

| 논리 변수 | 의미 | 플랫폼별 대응 |
| --- | --- | --- |
| `${ATP_PROJECT_DIR}` | 소비 프로젝트 루트 | Layer 2 각 어댑터 참조 |
| `${ATP_PLUGIN_ROOT}` | 설치된 ATP 플러그인 루트 | Layer 2 각 어댑터 참조 |

### 0.4 `@` 오용 경고

> **`@` 주의 — 플랫폼별로 의미가 다르다**:
>
> - Claude Code: `@` 는 마켓플레이스 설치 구분자(`/plugin install atp@agent-team-protocol`) 전용. 명령 호출 문법 아님.
> - Codex: `@` 는 (1) config 식별자(`plugin@marketplace`)이자 (2) **설치된 플러그인/번들 skill 멘션 호출 접두**("Type `@` to invoke a specific plugin or one of its bundled skills" — cited). 정확 토큰(`@atp`/`@task`/`/task`)은 TODO:실측.
> - Gemini: `@<agent_name>` 은 subagent 명시 위임 문법(`@codebase_investigator ...`) — 명령 호출이 아닌 서브에이전트 호출.
>
> Claude 에서 `/atp@task` 표기는 설치 구분자와 호출을 혼동한 것이므로 쓰지 않는다.

---

## Layer 1 — Capability Tier

### 1.1 Capability Matrix (분류 마커 보존)

연구 결과(source: `capability-research.md`)를 권위 문서로 승격한다. **셀의 분류 마커는 절대 제거하지 않는다.**

분류 범례: `verified-seed`(사전 검증) · `cited`(1차 공식문서 인용) · `TODO:실측`(문서 조각·미게시) · `needs_user_verification`(실제 install/하드웨어에서만 확인)

### 축 1 — 서브에이전트 spawn

| 플랫폼 | 값 | 분류 |
| --- | --- | --- |
| Claude Code | 가능 (Agent 툴) | verified-seed |
| Codex CLI | 가능 (명시 요청 시 spawn, `spawn_agents_on_csv` batch) | cited |
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
| Codex CLI (플러그인/번들 skill 멘션) | `@` 접두 (`@`+plugin/skill kebab-name) | cited |
| Codex CLI (정확 호출 토큰) | **미확정** (`@atp` vs `@task` vs `/task`) | **TODO:실측** |
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

#### 미해결 마커 목록

- [TODO:실측] Codex 플러그인 번들 skill 정확 호출 토큰 (`@atp` vs `@task` vs `/task`; `@` prefix 자체는 cited).
- [verified-empirical 2026-06-09 · codex-cli 0.138.0] Codex 설치 CLI 정본 확인 — `codex plugin {add,list,remove,marketplace}` 실제 서브명령. `atp@agent-team-protocol` 1.4.0 / `atp-graphify` 1.2.0 = installed+enabled, marketplace=`.agents/plugins/marketplace.json`, cache=`~/.codex/plugins/cache/agent-team-protocol/atp/1.4.0`(local 아닌 버전드). 공식 OpenAI 마켓플레이스도 전부 `.agents/plugins/marketplace.json`+`plugins/<name>` 실서브디렉토리 사용 → F-3PLAT-5 정본 방향 corroborate.
- [TODO:실측] `.codex-plugin/plugin.json` 의 `skills` 선언이 skill 노출 충분조건인지 (필요조건=정본 스키마 정합은 확인).
- [TODO:실측] Codex `PLUGIN_ROOT`/`CLAUDE_PLUGIN_ROOT` 의 skill·agent 본문(hook 외) 가용성.
- [TODO:실측] Gemini `${extensionPath}`/`${workspacePath}` 의 skill/agent 본문 가용성.
- [needs_user_verification] 세 플랫폼 실제 install 후 `task`/`init` 스모크.

---

### 1.2 Tier 정의

- **Tier A** = 서브에이전트 spawn 가능 → ATP 3-tier 팀(orchestrator + advisor + worker) 완전 동작. 2단 위임 체인(orchestrator→advisor→worker) 지원.
- **Tier A-flat** (Gemini 전용 변형) = spawn 은 되나 subagent→subagent 재귀 금지. orchestrator 가 advisor 와 worker 를 **모두 직접** 호출하는 평탄 구조(1단 fan-out). 게이트·report v1·검증규율 전량 유지.
- **Tier B** = 단일 agent (spawn 불가/미확인) → orchestrator 가 protocol phase 를 순차 self-checklist 로 수행. 병렬 advisor·worker 만 격하, 나머지 규율 유지. **spawn 실측 실패 시 안전 폴백.**

---

### 1.3 플랫폼 Tier 판정표

| 플랫폼 | Tier 잠정 판정 | 근거 | 확정 여부 |
| --- | --- | --- | --- |
| Claude Code | **Tier A (확정)** | Agent 툴 spawn — verified-seed | 확정 |
| Codex CLI | **Tier A (doc-cited, install-smoke 보류)** | subagents 명시 spawn + agent별 model 설정 — cited | needs_user_verification |
| Gemini CLI | **Tier A-flat (doc-cited, install-smoke 보류)** | subagent 시스템 존재 + recursion protection 제약 → 평탄 구조 채택 — cited | needs_user_verification |

> `needs_user_verification`: 실제 install + spawn 스모크 전까지 잠정 판정. 실패 시 해당 플랫폼은 Tier B 로 자동 격하(1.5 Tier B 격하 트리거 참조).

---

### 1.4 Gemini Tier A-flat 토폴로지 해소표

Gemini 의 recursion protection(subagent→subagent 호출 불가)은 ATP 의 2단 위임 체인(L1→L2→L3)의 L2→L3 간선을 막는다. 이를 Tier A-flat 평탄화로 해소한다.

| 항목 | Claude/Codex (Tier A) | Gemini (Tier A-flat) | Tier B (폴백) |
| --- | --- | --- | --- |
| spawn | advisor 가 worker spawn | orchestrator 가 worker 직접 spawn | spawn 없음 |
| 위임 깊이 | 2단 (L1→L2→L3) | 1단 평탄 (L1→L2, L1→L3) | 0단 (단일 agent) |
| worker 병렬 | advisor 내부 병렬 | orchestrator fan-out 병렬 | 순차 self-check |
| advisor 역할 | 계획+spawn+취합 | 계획 반환 → orchestrator 가 spawn → advisor 취합 | orchestrator self-check |
| 게이트 | 유지 | 유지 | 유지 |
| report 스키마 v1 | 유지 | 유지 | 유지 |
| 검증규율 | 유지 | 유지 | 유지 |
| 격하 대상 | 없음 | L2→L3 간선만 평탄화 | 병렬 → 순차 self-check |

**근거**: (1) recursion 제약은 capability 부재가 아니라 토폴로지 제약이므로 Tier B 격하는 과하다. (2) flat fan-out 은 spawn 능력을 그대로 활용하면서 재귀만 회피한다. (3) report 스키마·게이트는 호출 토폴로지와 독립이므로 평탄화해도 무손실. (4) advisor 가 "spawn 주체"에서 "계획 산출 주체"로 역할만 이동 — 산출물 계약(보고서 v1) 불변.

---

### 1.5 Tier B 실행 규칙 (격하 시 적용)

spawn 미지원/실측 실패 플랫폼에서 **단일 agent 가 ATP 를 순차로 도는** 규율이다.

#### 원칙

- **유지(불변)**: 파괴적 조작 게이트(프로토콜 §6), 보고서 스키마 v1(§8), 검증규율(§13 phase 완료 아티팩트 기준), forward phase-gate(§2.7), 집합 전수 체크 AC(§4.3).
- **격하(변형)**: 병렬 advisor → 단일 agent 의 **순차 self-checklist**. worker fan-out → 단계별 self-수행. advisor 간 충돌 조정 → 단일 agent 가 phase 전환 시 직전 산출물 자기검토.
- **금지**: phase 척추(요구 → 조사 → 설계 → 구현 → 검증) 우회. 게이트 생략. report 스키마 누락.

#### phase 순차 self-checklist

단일 agent 는 각 phase 진입 시 아래를 자기 점검하고, phase 종료 시 해당 phase 의 report v1 산출물을 `.atp/work-session/<sid>/` 에 기록한 뒤 다음 phase 로만 전진한다.

```
[Phase 0 — 요구사항 구체화]
  □ 요청을 FR/NFR 로 분해했는가
  □ 모호점은 AskUserQuestion 으로 닫았는가 (오픈 질문 0)
  □ requirements 산출물 기록 (report v1)

[Phase 1 — 조사 (research-advisor 역할 self-수행)]
  □ docs-first: index.md → 카테고리 index → 구체 문서 순 탐색했는가
  □ 외부 스펙은 source_confidence 마커(verified-seed/cited/TODO:실측)로 분류했는가
  □ (병렬 worker 불가) 조사 항목을 순차 처리하고 누락 없이 취합했는가
  □ research 산출물 기록 (report v1, concerns 포함)

[Phase 2 — 설계 (design-advisor 역할 self-수행)]
  □ 오픈 질문 0 — 미결은 concerns 로 에스컬레이션했는가
  □ 집합 포함 요구에 전수 체크 AC 1줄을 넣었는가 (§4.3)
  □ 시그니처 inflate 점검 (각 인자 사용 목적 인라인)
  □ design 산출물 기록 (report v1)

[Phase 3 — 구현 (implementation-advisor 역할 self-수행)]
  □ 설계도 파일 영향 맵을 따랐는가
  □ (병렬 worker 불가) 파일 단위 순차 수정 + 단계별 self-diff 검토
  □ unused/dead parameter 진단 게이트 통과 (§11.2)
  □ 파괴적 조작은 게이트 2단계 분리 통과 (§6)

[Phase 4 — 검증 (verification-advisor 역할 self-수행)]
  □ design 의 검증 포인트(AC) 전수 점검 — 집합 AC 는 grep -c 수치 일치 확인
  □ phase 완료 아티팩트 기준 충족 (§13)
  □ verification 산출물 기록 (report v1, PASS/FAIL)

[Phase 5 — 문서화 (documentation-advisor 역할 self-수행)]
  □ changes/ADR 등 카테고리 분류 기준 준수
  □ 회고 → MEMORY 반영 (§12)
```

#### Tier B 진입 트리거

- 플랫폼 install 스모크에서 spawn 실패 확인 시.
- 또는 사용자가 명시적으로 단일-agent 모드 요청 시.
- 진입 시 orchestrator 는 "Tier B 격하 모드 — 병렬 advisor 미사용, 순차 self-checklist 수행" 을 1줄 고지한다.

---

## Layer 2 — Per-Platform Adapter

### 2.1 Claude Code 어댑터

| 항목 | 값 |
| --- | --- |
| 호출 | `/atp:task <요청>`, `/atp:init` (콜론 namespace) |
| 지침파일 | `CLAUDE.md` |
| 프로젝트 루트 env | `${CLAUDE_PROJECT_DIR}` |
| 플러그인 루트 env | `${CLAUDE_PLUGIN_ROOT}` |
| 배포 단위 | `.claude-plugin/plugin.json` + marketplace |
| Tier | A (확정) |

### 2.2 Codex CLI 어댑터

| 항목 | 값 |
| --- | --- |
| 호출 | `@`-멘션 (정확 토큰 `@atp`/`@task`/`/task` 는 TODO:실측; `@` prefix 는 cited) |
| 지침파일 | `AGENTS.md` |
| 플러그인 루트 env | `PLUGIN_ROOT` (+ 호환 `CLAUDE_PLUGIN_ROOT`, hook 한정) |
| 쓰기 데이터 env | `PLUGIN_DATA` (+ 호환 `CLAUDE_PLUGIN_DATA`) |
| 배포 단위 | plugin manifest `.codex-plugin/plugin.json` (+ `skills:"./skills/"` 선언); marketplace 정본 `.agents/plugins/marketplace.json` (객체형 source) |
| Tier | A (doc-cited, install-smoke 보류) |

> **Codex 번들 skill namespace — TODO:실측 박스**
>
> 정확 호출 토큰(`@atp` vs `@task` vs `/task`)은 공식 문서가 토큰 단위 확정 안 함(`@` prefix·kebab namespace 만 cited). install 스모크 1회 후 확정.
> `.codex-plugin/plugin.json` `skills:"./skills/"` 선언이 skill 노출 충분조건인지도 install 스모크 게이트(필요조건=정본 스키마 정합은 확인됨).
> marketplace 정본은 `.agents/plugins/marketplace.json`. `.codex-plugin/marketplace.json` 은 Claude 미러로 Codex 가 읽지 않음.
> env var `PLUGIN_ROOT`/`CLAUDE_PLUGIN_ROOT` 의 skill·agent 본문(hook 외) 가용성도 TODO:실측.

### 2.3 Gemini CLI 어댑터

| 항목 | 값 |
| --- | --- |
| 호출 (command) | `/atp:task <요청>`, `/atp:init` (콜론 namespace) |
| subagent 명시 호출 | `@<agent_name>` (프롬프트 앞 — subagent 위임, 명령 호출 아님) |
| 지침파일 | `GEMINI.md` (기본; `contextFileName` 으로 변경 가능) |
| 확장 루트 env | `${extensionPath}` (manifest/hooks 한정) |
| 프로젝트 루트 env | `${workspacePath}` (manifest/hooks 한정) |
| 배포 단위 | `gemini-extension.json` (extension) |
| Tier | A-flat (doc-cited, install-smoke 보류) |

> **Gemini 배포형 — TODO:실측 박스**
>
> Gemini 명령 배포 형태(custom command `.toml` vs skill SKILL.md)와 정확한 namespace 표기는 install 스모크 전 미확정. 현재 설계 기준: "custom command 우선 + skill 폴백".
>
> `${extensionPath}`/`${workspacePath}` 의 skill/agent 본문(manifest·hooks 외) 가용성도 TODO:실측.

### 2.4 명령 매핑표

| 공통 식별자 | Claude Code | Codex (※번들 namespace 실측 TODO) | Gemini (※배포형 실측 TODO) |
| --- | --- | --- | --- |
| `task` | `/atp:task <요청>` | `@`-멘션 `TODO:실측` (`@atp`/`@task`/`/task`) | `/atp:task <요청>` `TODO:실측` |
| `init` | `/atp:init` | `@`-멘션 `TODO:실측` | `/atp:init` `TODO:실측` |

> `/task` 는 ATP 의 공식 사용자 입력명이 아니다. legacy 표기가 남아 있다면 플랫폼별 실제 입력명으로 교정한다.

---

## 문서 작성 규칙

### 공통 프로토콜 문서

`docs/development/agent-team-protocol.md`, advisor 정의, skill 본문처럼 3개 플랫폼이 함께 읽는 문서는 다음 규칙을 따른다.

- 제목과 본문 기본 표기는 `task 명령`, `init 명령`, `ATP task`, `ATP init` 처럼 플랫폼 중립적으로 쓴다.
- 실제 입력 예시가 필요하면 반드시 Claude Code / Codex / Gemini 를 나누어 표기한다.
- 3사 중 어느 하나만 단독 권위 표기로 쓰지 않는다.
- `/task` 는 새 문서에 쓰지 않는다.

### 사용자 설치/사용 문서

README, `docs/usage/faq.md`, `docs/usage/setup-checklist.md` 처럼 사용자가 따라 치는 문서는 3사를 모두 병기한다.

예:

```md
ATP task smoke test:

- Claude Code: `/atp:task 안녕, 에이전트 팀이 로드됐는지 확인만 해줘`
- Codex: `@task 안녕, 에이전트 팀이 로드됐는지 확인만 해줘` (TODO:실측 — `@` prefix 는 cited, 정확 토큰 확정 전)
- Gemini: `/atp:task 안녕, 에이전트 팀이 로드됐는지 확인만 해줘` (TODO:실측 — 배포형 확정 전)
```

### 프로젝트 지침 삽입 블록

`init` 이 소비 프로젝트에 삽입하는 안내 블록은 대상 플랫폼에 맞는 실제 입력명을 사용한다. 3-파일 감지+옵트인 생성 규칙은 `skills/init/SKILL.md` §2 에 위임한다.

| 대상 파일 | 입력 예시 |
| --- | --- |
| `CLAUDE.md` | `/atp:task [요청]` |
| `AGENTS.md` | `@task [요청]` (TODO:실측 caveat — `@` prefix cited, 토큰 미확정) |
| `GEMINI.md` | `/atp:task [요청]` (TODO:실측 caveat 포함) |

---

## 파일과 디렉토리 명명

ATP 프로토콜 자체의 산출물 경로:

| 개념 | 현재 권위 경로 | Claude legacy | 비고 |
| --- | --- | --- | --- |
| 세션 공유 상태 | `.atp/work-session/<sid>/` | `.claude/work-session/<sid>/` (자동 이관 대상 — legacy) | F-3PLAT-3 single-read 전환 완료 |
| 프로젝트 지침 | 플랫폼별 파일 | `CLAUDE.md` | Codex: `AGENTS.md`, Gemini: `GEMINI.md` |
| 플러그인 매니페스트 | 플랫폼별 디렉토리 | `.claude-plugin/` | Codex: `.codex-plugin/plugin.json`(manifest) + marketplace 정본 `.agents/plugins/marketplace.json` |

---

## 환경 변수 — 플랫폼별 대응표

| 논리 변수 | Claude Code | Codex CLI | Gemini CLI |
| --- | --- | --- | --- |
| `${ATP_PROJECT_DIR}` | `${CLAUDE_PROJECT_DIR}` | workspace root (TODO:실측) | `${workspacePath}` (manifest/hooks 한정, TODO:실측) |
| `${ATP_PLUGIN_ROOT}` | `${CLAUDE_PLUGIN_ROOT}` | `PLUGIN_ROOT` (+ 호환 `CLAUDE_PLUGIN_ROOT`) | `${extensionPath}` (manifest/hooks 한정, TODO:실측) |

---

## 변경 우선순위

1. `skills/init/SKILL.md` 의 CLAUDE.md 단독 생성 → 3-지침파일 감지+옵트인 생성으로 확장.
2. README/faq/setup-checklist 의 smoke test 예시를 2사 → 3사(+Gemini TODO:실측) 병기로 확장.
3. `.claude/work-session/` → `.atp/work-session/` 경로 이전: **완료 (F-3PLAT-3)** — single-read 전환 + `atp:migrate` 자기삭제 블록으로 소비 프로젝트 1회성 자동 이관.
4. Gemini 실제 배포 산출물(extension.json, commands/*.toml) 생성: **이월(배포 패키징 후속)**.
5. `.claude-plugin/` / `.codex-plugin/` 매니페스트 `description` 에 Gemini 추가: **이월(배포 패키징 후속)**.

---

## 검증 체크리스트

- [ ] `/task` 가 공식 사용자 입력명처럼 보이는 문서가 남아 있지 않은가?
- [ ] Claude Code 안내에는 `/atp:task` (콜론), Codex 안내에는 `@`-멘션(정확 토큰 TODO:실측) 이 쓰였는가? (`$`-접두 가설 표기 잔존 0)
- [ ] Codex marketplace 정본이 `.agents/plugins/marketplace.json` 으로 기술되고, `.codex-plugin/marketplace.json` 이 Codex 정본처럼 표기되지 않았는가?
- [ ] `@` 를 명령 호출 문법으로 쓴 표기(`/atp@task`)가 남아 있지 않은가?
- [ ] 공통 문서에서 특정 플랫폼 명령 문법 하나만 권위 표기로 쓰지 않았는가?
- [ ] capability matrix 의 TODO:실측 마커가 검증 없이 제거되지 않았는가?
- [ ] Gemini Tier A-flat 토폴로지 해소표가 존재하는가?
- [ ] `.atp/work-session/` 이 권위 경로로 기술되고, `.claude/work-session/` 이 legacy 라벨(자동 이관 대상) 외에서 권위로 남아있지 않은가?
