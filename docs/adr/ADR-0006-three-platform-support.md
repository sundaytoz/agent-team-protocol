---
kind: adr
adr_number: "0006"
title: v1.4.0 — 3-플랫폼 지원 (Claude Code / Codex / Gemini): capability tier + single-read 경로 마이그레이션
status: accepted
date: 2026-06-09
deciders:
  - template-maintainer
  - stzjungsoo
supersedes: []
related_commits:
  - 4e9d9ea
  - 3472883
  - 3eb0bf2
  - f853c33
  - 5b5a909
  - ce30125
---

# ADR-0006: v1.4.0 — 3-플랫폼 지원 (Claude Code / Codex / Gemini): capability tier + single-read 경로 마이그레이션

## 상태

**Accepted** — 2026-06-09. ADR-0005(v1.3.0) 위에 적층. supersede 아님. ADR-0002(plugin-only) 의 플랫폼 범위를 Claude Code 단독에서 3사로 확장하는 후속이다.

---

## 맥락

### 배경

ATP 는 Claude Code 를 기준으로 설계됐다. v1.4.0 개발 세션(20260609-125316)에서 **Codex CLI 와 Gemini CLI 로 공식 지원 범위를 확장**하는 결정이 내려졌다. 이 ADR 은 그 세션에서 이루어진 되돌리기 어려운 결정 5개를 영구 기록한다.

> **이 문서가 유일한 영구 기록이다.** 근거 소스가 된 설계 문서들(`design.md`, `design-f3plat3.md`, `design-f3plat12.md`)과 조사 보고서(`capability-research.md`, `plugin-update-propagation.md`)는 work-session 산출물로 gitignore 대상이라 세션 종료 후 소실된다.

### 배경 제약 — source-confidence 4단계 마커 도입 계기

이전 세션 분석에서 외부 플랫폼 스펙을 조사할 때 미검증 정보가 추정 없이 단정 서술되어 하류 설계의 사실 오류로 이어지는 패턴이 관측됐다(ADR-0005 §맥락 참조). 3-플랫폼 조사는 Claude Code 외의 두 플랫폼(Codex CLI / Gemini CLI)의 공식 문서를 1차 출처로 삼아야 했는데, 이 출처들은 접근 가능하나 미게시 항목이 존재한다. 이에 **source-confidence 4단계 분류 마커**를 조사 표준으로 채택했다:

| 마커 | 의미 |
|---|---|
| `verified-seed` | 사전 검증된 시드 — 재조사 금지 |
| `cited` | 1차 공식문서 인용 |
| `TODO:실측` | 문서 미게시·조각 존재 — install 스모크 필요 |
| `needs_user_verification` | 실제 install/하드웨어에서만 확인 가능 |

이 마커들은 조사 보고서에서 `platform-adapters.md` 까지 전파되어 **capability matrix 의 모든 미확정 셀에 보존**된다. 검증 전 "확정" 격상을 구조적으로 차단한다.

### 조사 결과 요약 (6축 capability matrix)

세션 조사 결과 **3개 CLI 모두 서브에이전트 spawn + per-call model override 를 지원**함이 문서 근거 수준에서 확인됐다. 단, 두 가지 차이가 설계 제약으로 확인됐다:

1. **호출 문법 3사 3색**: Claude Code `/atp:task`(콜론 namespace) / Codex `$skill-name`($ 접두, 플러그인 namespace 표기는 TODO:실측) / Gemini `/ns:cmd`(콜론 namespace) 또는 `@agent_name`(subagent 직접 위임).
2. **Gemini subagent recursion 제약**: Gemini 는 subagent 가 다른 subagent 를 호출하는 것이 플랫폼 수준에서 금지된다(`cited` — github.com/google-gemini/gemini-cli docs/core/subagents.md). 이는 ATP 의 orchestrator→advisor→worker **2단 위임 체인의 L2→L3 간선**과 충돌한다.

미확정 항목(install 스모크 전):
- ~~[TODO:실측] Codex 플러그인 번들 skill 호출 namespace~~ → **해소 (2026-06-10)**: skill id `atp:task`(`plugin:skill` 콜론, 런타임 레지스트리), 호출 `$atp:task`(사용자 대화형 전사 — 명시 호출 인식·본문 로드·버전 보고. 공식 docs `$` 접두 cited). 단축형 `$task` 수용 여부만 잔여 TODO:실측.
- [TODO:실측] Codex `PLUGIN_ROOT`/`CLAUDE_PLUGIN_ROOT` 의 skill·agent 본문(hook 외) 가용성.
- [TODO:실측] Gemini `${extensionPath}`/`${workspacePath}` 의 skill/agent 본문 가용성.
- [needs_user_verification] 세 플랫폼 실제 install 후 `task`/`init` 스모크.

6축 capability matrix 전문은 `docs/development/platform-adapters.md` §1.1 이 권위 SSoT 이다.

---

## 결정

### 결정 1 — source-confidence 4단계 마커 표준화 (ADR-0005 §5 확장)

**결정**: ADR-0005 에서 research-advisor 에 도입한 신뢰도 마커를 **`verified-seed`/`cited`/`TODO:실측`/`needs_user_verification`** 4단계로 명명 표준화하고, 이 마커를 capability matrix 의 모든 미확정 셀에 **전수 보존**한다. 조사 산출 → 권위 문서로 승격 시 마커를 "확정"으로 격상하는 것을 금지한다.

**배경**: ADR-0005 의 마커 체계(`확인됨`/`추정`/`미확인`)를 외부 플랫폼 스펙 조사에 맞게 구체화했다. `verified-seed` 는 재조사 비용 절감, `cited` 는 1차 출처 있음 but 실측 미완, `TODO:실측` 은 install 스모크 전 단정 금지, `needs_user_verification` 은 자동화 불가 영역 명시로 각각 용도가 구분된다.

### 결정 2 — 플랫폼 capability tier (A / A-flat / B) 도입

**결정**: 플랫폼을 ATP 3-tier 위임 체인에서 할 수 있는 것에 따라 3등급으로 분류하는 **capability tier** 체계를 채택한다. 권위 정의는 `platform-adapters.md` Layer 1 이며, 코어 프로토콜(`agent-team-protocol.md`)에는 요약 + 포인터만 둔다(§2.8).

| Tier | 조건 | 위임 구조 |
|---|---|---|
| **Tier A** | spawn 가능 | 2단 위임 (orchestrator→advisor→worker) |
| **Tier A-flat** | spawn 가능, subagent→subagent 재귀 금지 | 1단 평탄 fan-out (orchestrator→{advisor,worker}) |
| **Tier B** | spawn 불가 또는 실측 실패 | 단일 agent 순차 self-checklist |

**중요**: 이 "플랫폼 capability tier(A/A-flat/B)"는 기존 코어 프로토콜의 "역할 tier(Tier-2/Tier-3 advisor)"와 **직교하는 별개 축**이다. 두 축의 이름 충돌은 코어 §2.8 의 용어 구분 박스로 명시한다.

현재 판정: Claude Code=**Tier A (확정)**, Codex CLI=**Tier A (doc-cited, smoke 보류)**, Gemini CLI=**Tier A-flat (doc-cited, smoke 보류)**. 실측 실패 시 해당 플랫폼은 Tier B 로 자동 격하된다.

### 결정 3 — Gemini recursion 제약 → Tier A-flat 채택 (Tier B 격하 기각)

**결정**: Gemini 의 subagent recursion 금지를 Tier B(단일 agent) 격하로 처리하지 않고, **Tier A-flat** 이라는 새로운 변형 tier 로 수용한다.

**Tier A-flat 토폴로지**: 역할 Tier-3 advisor 의 "advisor-내부-spawn"을 "orchestrator-직접-fan-out" 으로 평탄화한다. advisor 는 계획 산출 주체로 역할이 이동하고, orchestrator 가 계획에 따라 worker 를 직접 spawn 한 뒤 결과를 advisor 에 취합 위임한다.

| 항목 | Tier A (Claude/Codex) | Tier A-flat (Gemini) | Tier B (폴백) |
|---|---|---|---|
| spawn 주체 | advisor 가 worker spawn | orchestrator 가 worker 직접 spawn | spawn 없음 |
| 위임 깊이 | 2단 (L1→L2→L3) | 1단 평탄 (L1→L2, L1→L3) | 0단 (단일 agent) |
| worker 병렬 | advisor 내부 병렬 | orchestrator fan-out 병렬 | 순차 self-check |
| advisor 역할 | 계획+spawn+취합 | 계획 반환 → orchestrator spawn → advisor 취합 | orchestrator self-check |
| 게이트(§6) | 유지 | 유지 | 유지 |
| report 스키마 v1(§8) | 유지 | 유지 | 유지 |
| 검증규율(§13) | 유지 | 유지 | 유지 |

**기각한 대안**: Tier B 격하(dual downgrade). Gemini 가 spawn capability 를 갖고 있음에도 토폴로지 제약만으로 단일-agent 모드로 격하하면 capability 손실이 발생한다. Tier A-flat 은 spawn 능력을 그대로 활용하면서 재귀만 회피하는 최소 평탄화다. 또한 게이트·보고서 스키마·검증규율이 호출 토폴로지와 독립임이 확인됐으므로 평탄화해도 규율이 무손실이다.

### 결정 4 — single-read `.atp/work-session` 채택 + orchestrator 실행형 자기삭제 마이그레이션 블록

**결정**: 산출물 경로를 `.claude/work-session/` 에서 `.atp/work-session/` 으로 **single-read 전환**한다. 이미 초기화된 소비 프로젝트의 경로 이관은 **orchestrator 실행형 자기삭제 마이그레이션 블록**(`atp:migrate`)으로 처리한다.

**전파 제약 — 3사 공통**: 플랫폼 업데이트는 plugin cache 만 스왑하고 소비 프로젝트 파일을 건드리지 않는다(`cited` — Claude Code plugins-reference, Codex/Gemini install copy 모델 동일). 또한 install/update lifecycle 훅이 **세 플랫폼 모두 부재**함이 확인됐다(`cited` 전수):
- Claude Code: 훅 이벤트는 SessionStart/PreToolUse 등 런타임 전용. install/update 시점 훅 없음.
- Codex CLI: 런타임 이벤트만(SessionStart/SubagentStart/PreToolUse/...). install/update 전용 이벤트 없음.
- Gemini CLI: hooks.json 의 일반 CLI 동작 훅. install/update lifecycle 훅 미게시.

따라서 소비 프로젝트 파일 변경은 **사용자 액션을 경유하거나** orchestrator 의 런타임 실행으로만 가능하다.

**마이그레이션 블록 설계**:
- `init` 이 소비 프로젝트 지침파일(CLAUDE.md/AGENTS.md/GEMINI.md)에 `atp:migrate:begin` / `atp:migrate:end` 마커 블록을 삽입한다.
- 다음 `/atp:task` 또는 `/atp:init` 진입 시 orchestrator(메인 에이전트)가 1회 실행: (1) `.claude/work-session/` → `.atp/work-session/` `git mv`(비파괴 이동, 삭제 아님), (2) `.gitignore` 신라인 보장, (3) 블록 자체를 지침파일에서 제거(자기삭제).
- 블록은 안내 블록(`atp:begin`/`atp:end`)과 **별도 마커**로 분리된다.
- 3사 공통 문안(플랫폼 분기 불필요 — orchestrator 자연어 지시문이므로).
- 멱등: 이미 이관 완료 시 1~2 no-op, 3(블록 삭제)만 수행.

**기각한 대안**:
- **(a) 플러그인 업데이트 자동**: 플러그인 업데이트는 소비 프로젝트 `.gitignore` 와 구 디렉토리를 건드리지 않는다. 경로 혼재 위험.
- **(b) init 재실행 단독**: `.gitignore` 신라인 추가의 idiomatic vehicle 이나, 마이그레이션 블록 없이는 디렉토리 이관 vehicle 이 없다. 본 결정은 (b) 보강으로 간주.
- **(c) post-update 훅**: install/update lifecycle 훅이 3사 모두 부재 — 정공법 불가(cited 전수). SessionStart 훅 우회는 매 세션 침습적.
- **(d) dual-read backward-compat**: 영구적인 이경로 유지보수 부채를 남긴다. 사용자가 single-read 를 명시적으로 확정했으므로 기각.

### 결정 5 — 비목표·이월 항목 명시

다음 항목은 이번 결정의 범위 밖이다:

- **F-3PLAT-4 Gemini 배포 산출물**: `gemini-extension.json`, `commands/*.toml`, Gemini 전용 에이전트 파일 생성 — 배포형(command vs skill)이 `TODO:실측` 에 의존. 설계는 "custom command(.toml) 우선 + skill 폴백"으로 결정했으나 실제 파일 생성은 이월.
- **install 스모크**: 세 플랫폼 실제 설치 후 `task`/`init` 호출·env 치환·subagent spawn 실동작 확인은 `needs_user_verification` — 자동화 불가.
- **Codex skill namespace 확정**: ~~install 스모크 전까지 `TODO:실측`~~ → **해소 (2026-06-10)**: 호출 `$atp:task`, skill id `atp:task`. 경위: 한때 codex exec 런타임 self-report 로 `/task` 단정(오류) → 사용자 대화형 전사 + 공식 docs 로 `$atp:task` 확정. 교훈은 platform-adapters.md §1.1 미해결 마커 목록 참조.

---

## 검토한 대안

### D2 대안 — Tier B 격하 (dual downgrade)

Gemini subagent recursion 을 단순히 "spawn 체인이 막힘" 으로 보고 Tier B(단일 agent) 격하하는 방안. **기각 이유**: Gemini 는 spawn capability 자체를 보유한다. capability 없는 경우와 토폴로지 제약만 있는 경우를 같은 tier 로 처리하면 기능 손실이 발생한다. 실제로 orchestrator-직접-fan-out 이 설계상 가능하므로 Tier A-flat 이 더 정확하다(피드백 메모리 `topology-constraint-new-tier-vs-capability-downgrade` 참조).

### D4 대안 — dual-read backward-compat

`.claude/work-session/` 을 계속 읽고 신규 세션만 `.atp/work-session/` 에 쓰는 방안. research 조사(`plugin-update-propagation.md`)는 이를 "가장 비파괴·점진적"이라 평가했으나, 사용자가 단일 진실(single-read)을 선택했고, 영구적인 이중 경로 유지보수 부채를 회피하기 위해 기각됐다.

### D4 대안 — SessionStart 훅 자동 패치

Claude Code `SessionStart` 훅 + diff-and-act 관용구로 `.gitignore` 자동 패치. **기각 이유**: install/update lifecycle 훅 3사 부재(cited 전수). SessionStart 우회는 매 세션 소비 프로젝트 파일을 자동 수정하는 침습적 패턴이며, Codex 는 신뢰 게이트 필요, Gemini 는 동작 범위 미게시.

---

## 결과

- `platform-adapters.md` 가 3층 구조(Layer 0 protocol core / Layer 1 capability tier / Layer 2 per-platform adapter)로 재작성됐다. capability tier 정의(Tier A/A-flat/B)와 6축 capability matrix(source-confidence 마커 보존)의 권위 SSoT.
- `agent-team-protocol.md` 에 §2.8(플랫폼 capability tier 와 위임 토폴로지)이 추가됐다. 코어는 platform-adapters 포인터만 두며 정의를 복제하지 않는다.
- 코어 §2.7(forward phase-gate)에 "research 가 세션 초반 가정을 뒤집으면 설계 진입 전 plan 게이트" 트리거가 추가됐다.
- `skills/init/SKILL.md` 가 CLAUDE.md/AGENTS.md/GEMINI.md 3-파일 감지·옵트인 생성으로 확장됐다.
- `skills/init/SKILL.md` 에 `atp:migrate` 블록 upsert 로직이 추가됐다.
- `skills/task/SKILL.md` §0 에 orchestrator 마이그레이션 실행·자기삭제 로직이 추가됐다.
- 플러그인 본문 전 surface 의 산출물 경로 참조가 `.claude/work-session` → `.atp/work-session` 으로 단일 전환됐다.
- ADR-0002(plugin-only) / ADR-0003/0004/0005 불변. 본 ADR 은 ADR-0002 의 플랫폼 범위를 확장하며, ADR-0005 의 source-confidence 마커 체계를 4단계 명명으로 구체화한다.
- 커밋: 4e9d9ea(3-platform support 초기), 3472883(init block upsert fix), 3eb0bf2(single-read path + self-deleting migration block), f853c33(F-3PLAT-3 done 표시), 5b5a909(코어 §2.8 capability tier + §2.7 research-반전 트리거 = F-3PLAT-1/2), ce30125(atp 1.3.0→1.4.0 version bump).

---

## 관련 문서

- [ADR-0002](./ADR-0002-plugin-only-migration.md) — plugin-only 전환 (플랫폼 범위 확장의 전제)
- [ADR-0005](./ADR-0005-orchestrator-bidirectional-flow-control.md) — v1.3.0 source-confidence 마커 체계 도입
- [platform-adapters.md](../development/platform-adapters.md) — capability tier 권위 SSoT (Layer 0~2 전체)
- [agent-team-protocol.md](../development/agent-team-protocol.md) — §2.7(research 반전 트리거), §2.8(플랫폼 tier 연결 절)
