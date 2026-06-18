---
kind: architecture
title: 구성 파일 맵
description: 플러그인 레이아웃(레포 루트), init 이 소비 프로젝트에 생성하는 산출물, 런타임 디렉토리를 한 장으로 정리.
owner: template-maintainer
stability: stable
last_reviewed: 2026-06-10
---

# 구성 파일 맵

레포 루트는 **마켓플레이스 `agent-team-protocol`** 이고, base 플러그인 `atp` 의 루트는 **`plugins/atp/`**, add-on `atp-graphify` 의 루트는 **`plugins/atp-graphify/`** 서브디렉토리다 (2.1.0 — 설치 시 해당 서브트리만 번들로 복사된다). 이 문서는 세 가지 트리를 설명한다.

1. [레포(플러그인 소스) 트리](#1-레포플러그인-소스-트리)
2. [init 산출물 트리](#2-init-산출물-트리--소비-프로젝트)
3. [런타임 디렉토리](#3-런타임-디렉토리)

경로 경계 규칙은 [§4 경계 요약](#4-plugin-root-vs-project-dir-경계-요약) 참조.

---

## 1. 레포(플러그인 소스) 트리

```
agent-team-protocol/                      (레포 루트 = 마켓플레이스 agent-team-protocol)
│
├── .claude-plugin/
│   └── marketplace.json                  ← Claude Code 마켓플레이스 정본 (plugins: [atp→./plugins/atp, atp-graphify→./plugins/atp-graphify])
│
├── .codex-plugin/
│   └── marketplace.json                  ← Claude 미러 (Codex 는 읽지 않음)
│
├── .agents/
│   └── plugins/
│       └── marketplace.json              ← Codex marketplace 정본 (객체형 source: atp→./plugins/atp, atp-graphify→./plugins/atp-graphify)
│
├── plugins/
│   ├── atp/                              ← base 플러그인 루트 (설치 시 이 서브트리만 캐시로 복사)
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json               ← base 플러그인 정의 (name: atp, version 2.1.0)
│   │   ├── .codex-plugin/
│   │   │   └── plugin.json               ← base 플러그인 정의 (skills: "./skills/")
│   │   ├── agents/                       ← base 에이전트 10개 (graphify 3종 제외)
│   │   │   ├── requirements-advisor.md
│   │   │   ├── research-advisor.md
│   │   │   ├── parallel-explorer.md
│   │   │   ├── design-advisor.md
│   │   │   ├── implementation-advisor.md
│   │   │   ├── code-writer.md
│   │   │   ├── migration-writer.md
│   │   │   ├── verification-advisor.md
│   │   │   ├── documentation-advisor.md
│   │   │   └── retrospective-advisor.md
│   │   ├── skills/
│   │   │   ├── task/SKILL.md             ← /atp:task 명령 진입점
│   │   │   └── init/SKILL.md             ← /atp:init 명령 진입점
│   │   ├── docs/                         ← 번들 런타임 레퍼런스 (읽기전용, ${CLAUDE_PLUGIN_ROOT} 로 Read)
│   │   │   ├── index.md                  ← 번들 전용 경량 허브
│   │   │   └── development/
│   │   │       ├── index.md              ← 번들 전용 경량본 (런타임 6건만)
│   │   │       ├── agent-team-protocol.md ← 3-tier 운영 권위 레퍼런스 (§1~§14 + 선두 코어 구획 atp:core)
│   │   │       ├── agent-catalog.md      ← 에이전트 카탈로그 (base 10 + add-on 3)
│   │   │       ├── platform-adapters.md  ← 호스트 capability tier 정의·자가판정 정본
│   │   │       ├── documentation-guidelines.md
│   │   │       └── search-tool-matrix.md
│   │   ├── templates/                    ← init 스캐폴딩 원본 (init 이 소비 프로젝트로 복사)
│   │   │   ├── category-index/*.md       ← 카테고리 index 14종
│   │   │   ├── docs-index.md
│   │   │   ├── verification-strategies.md    ← placeholder 포함 (cmd 교체 필요)
│   │   │   ├── document-category-classification.md
│   │   │   └── graph/ (index.md, .gitignore)
│   │   └── (gemini-extension manifest)   ← 위치 확정(ADR-0007), 산출물은 F-3PLAT-4 에서 생성 예정
│   │
│   └── atp-graphify/                     ← add-on 플러그인 루트 (add-on 설치 시 이 서브트리만 복사)
│       ├── .claude-plugin/plugin.json    ← add-on 정의 (name: atp-graphify, version 2.1.0, dependencies: ["atp"])
│       ├── .codex-plugin/plugin.json     ← 동일 add-on 정의
│       ├── agents/                       ← graphify 에이전트 3개
│       │   ├── graph-refresh-checker.md
│       │   ├── graphify-lookup-advisor.md
│       │   └── graphify-update-advisor.md
│       └── docs/
│           └── graphify-usage.md         ← graphify add-on 설치·통합 가이드
│
└── docs/                                 ← 사람용 문서 (번들 제외 — GitHub 독자·기여자 대상)
    ├── index.md (+ index.en.md)          ← docs-first 풀 허브 (한/영)
    ├── adr/                              ← ADR 5건 + index.md
    ├── architecture/
    │   ├── index.md
    │   └── file-map.md                   ← 이 문서
    ├── development/
    │   ├── index.md                      ← 루트 풀본 (런타임 6건은 plugins/atp/docs/ 로 링크)
    │   └── release-checklist.md          ← 기여자 릴리즈 절차
    └── usage/                            ← 설치·FAQ 가이드 (한/영 6건)
```

---

## 2. init 산출물 트리 — 소비 프로젝트

`/atp:init` 실행 시 `${CLAUDE_PROJECT_DIR}` 기준으로 아래 항목을 생성한다. 이미 존재하는 파일은 덮어쓰지 않는다(멱등).

```
<소비 프로젝트 루트>/
│
├── CLAUDE.md                             ← 기존 파일 하단에 <!-- atp:begin --> 블록 멱등 append
│                                             (docs-first 정책 + /atp:task 진입 안내 포함)
├── .gitignore                            ← .atp/work-session/ 라인 제거 (있는 경우) — 추적 기본
│
└── docs/
    ├── index.md                          ← docs-first 허브
    ├── adr/index.md
    ├── analysis/index.md
    ├── architecture/index.md
    ├── backlog/index.md
    ├── changes/index.md
    ├── contracts/index.md
    ├── development/
    │   ├── index.md
    │   ├── verification-strategies.md    ← placeholder 포함 — cmd 를 프로젝트 명령으로 교체 필요
    │   └── document-category-classification.md
    ├── domain/index.md
    ├── feedback/index.md
    ├── graph/
    │   ├── index.md
    │   └── .gitignore
    ├── issues/index.md
    ├── maintenance/index.md
    ├── security/index.md
    ├── usage/index.md
    └── work-log/index.md
```

init 후 설정 절차는 [../usage/setup-checklist.md](../usage/setup-checklist.md) 참조.

---

## 3. 런타임 디렉토리

`/atp:task` 실행 시 세션마다 생성된다. 권위 정의: [프로토콜 §7](../../plugins/atp/docs/development/agent-team-protocol.md#7-공유-상태-레이아웃).

**추적 정책 (ADR-0010)**: 플러그인 기본은 추적이다 — 소비 레포의 `/atp:init` 은 `.gitignore` 에서 `.atp/work-session/` 라인을 제거하여 추적을 활성화한다. 추적을 원치 않는 레포는 `.gitignore` 에 `.atp/work-session/` 1줄을 추가해 opt-out 할 수 있다. **이 소스 레포(`agent-team-protocol`)는 opt-out 을 행사한다** — public 레포이며 work-session report 에 유지자 발화(`user_signals`)와 retrospective 내부 비판이 기록되어 공개 노출이 부적절하기 때문이다. 따라서 이 레포에서는 `.atp/work-session/` 이 `.gitignore` 대상이며 커밋되지 않는다.

```
.atp/work-session/<sid>/            ← 세션 공유 상태. sid = YYYYMMDD-HHMMSS
                                        플러그인 기본=추적 / 레포별 opt-out 가능(.gitignore 1줄)
                                        이 소스 레포는 opt-out(미추적)
    ├── report.md                   ← 모든 의사결정·invocation·회고 누적
    ├── requirements.md
    ├── research/
    ├── design.md
    ├── implementation/
    │   ├── ownership.md            ← 파일 소유권 맵
    │   └── report.md
    ├── verification.md
    ├── documentation.md
    ├── conflicts.md
    └── artifacts/
```

---

## 4. ${CLAUDE_PLUGIN_ROOT} vs ${CLAUDE_PROJECT_DIR} 경계 요약

| 변수 | 가리키는 경로 | 용도 |
|---|---|---|
| `${CLAUDE_PLUGIN_ROOT}` | 플러그인 캐시 내 레포 루트 (읽기전용) | 번들 레퍼런스 문서 Read, agent/skill 본문 경로 참조 |
| `${CLAUDE_PROJECT_DIR}` | 소비 프로젝트 루트 (읽기/쓰기) | init 생성 파일, 세션 work-session, 프로젝트 소스 코드 |

규칙:
- **레퍼런스 Read** (`agent-team-protocol.md`, `agent-catalog.md` 등 번들 docs) → `${CLAUDE_PLUGIN_ROOT}/docs/...`
- **편집형 Read/Write** (프로젝트 `verification-strategies.md`, 카테고리 index 등) → `${CLAUDE_PROJECT_DIR}/docs/...`
- **산출물 Write** (`work-session/`, `report.md`, 소스 코드 등) → `${CLAUDE_PROJECT_DIR}/...`

---

## 관련 문서

- [../../plugins/atp/docs/development/agent-catalog.md](../../plugins/atp/docs/development/agent-catalog.md) — base atp 10개 + add-on atp-graphify 3개 에이전트 상세
- [../../plugins/atp/docs/development/agent-team-protocol.md](../../plugins/atp/docs/development/agent-team-protocol.md) — 운영 프로토콜 전문 (선두 코어 구획 + §1~§14)
- [docs/adr/ADR-0013-protocol-core-section-on-demand-routing.md](../adr/ADR-0013-protocol-core-section-on-demand-routing.md) — protocol.md 진입 로딩 구조: 코어 구획 상주 + on-demand §섹션 라우팅 결정
- [../usage/setup-checklist.md](../usage/setup-checklist.md) — init 후 설정 체크리스트
- [docs/adr/ADR-0002-plugin-only-migration.md](../adr/ADR-0002-plugin-only-migration.md) — cp-R 폐기·plugin-only 전환 결정 기록
