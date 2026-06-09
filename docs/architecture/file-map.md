---
kind: architecture
title: 구성 파일 맵
description: 플러그인 레이아웃(레포 루트), init 이 소비 프로젝트에 생성하는 산출물, 런타임 디렉토리를 한 장으로 정리.
owner: template-maintainer
stability: stable
last_reviewed: 2026-06-01
---

# 구성 파일 맵

레포 루트가 곧 **base 플러그인 `atp` 의 루트이자 마켓플레이스 `agent-team-protocol`** 이다. 이 문서는 세 가지 트리를 설명한다.

1. [레포(플러그인 소스) 트리](#1-레포플러그인-소스-트리)
2. [init 산출물 트리](#2-init-산출물-트리--소비-프로젝트)
3. [런타임 디렉토리](#3-런타임-디렉토리)

경로 경계 규칙은 [§4 경계 요약](#4-plugin-root-vs-project-dir-경계-요약) 참조.

---

## 1. 레포(플러그인 소스) 트리

```
agent-team-protocol/                      (레포 루트 = 마켓플레이스 = base 플러그인 atp)
│
├── .claude-plugin/                       ← Claude Code manifest
│   ├── plugin.json                       ← base 플러그인 정의 (name: atp)
│   └── marketplace.json                  ← 마켓플레이스 정의 (name: agent-team-protocol, plugins: [atp, atp-graphify])
│
├── .codex-plugin/                        ← Codex manifest mirror
│   ├── plugin.json                       ← base 플러그인 정의 (name: atp)
│   └── marketplace.json                  ← 동일 마켓플레이스 정의
│
├── agents/                               ← base atp 에이전트 10개 (graphify 3종 제외)
│   ├── requirements-advisor.md
│   ├── research-advisor.md
│   ├── parallel-explorer.md
│   ├── design-advisor.md
│   ├── implementation-advisor.md
│   ├── code-writer.md
│   ├── migration-writer.md
│   ├── verification-advisor.md
│   ├── documentation-advisor.md
│   └── retrospective-advisor.md
│
├── skills/
│   ├── task/
│   │   └── SKILL.md                      ← /atp:task 명령 진입점
│   └── init/
│       └── SKILL.md                      ← /atp:init 명령 진입점
│
├── docs/                                 ← 번들 레퍼런스 (읽기전용, ${CLAUDE_PLUGIN_ROOT} 로 Read)
│   ├── index.md                          ← docs-first 허브
│   ├── adr/
│   ├── analysis/
│   ├── architecture/
│   │   ├── index.md
│   │   └── file-map.md                   ← 이 문서
│   ├── backlog/
│   ├── changes/
│   ├── contracts/
│   ├── development/
│   │   ├── index.md
│   │   ├── agent-team-protocol.md        ← 3-tier 운영 권위 레퍼런스 (§1~§14)
│   │   ├── agent-catalog.md              ← 에이전트 카탈로그 (base 10 + add-on 3)
│   │   ├── verification-strategies.md    ← L1/L2/L3 전략 레지스트리 (templates/ 에도 스캐폴딩 원본)
│   │   ├── documentation-guidelines.md
│   │   ├── document-category-classification.md
│   │   └── search-tool-matrix.md
│   ├── domain/
│   ├── graph/
│   │   ├── index.md
│   │   └── .gitignore
│   ├── issues/
│   ├── maintenance/
│   ├── security/
│   ├── usage/
│   │   ├── index.md
│   │   ├── faq.md
│   │   └── setup-checklist.md
│   └── work-log/
│
├── templates/                            ← init 스캐폴딩 원본 (init 이 소비 프로젝트로 복사)
│   ├── docs/
│   │   ├── index.md
│   │   ├── development/
│   │   │   ├── verification-strategies.md    ← placeholder 포함 (cmd 교체 필요)
│   │   │   └── document-category-classification.md
│   │   └── graph/
│   │       ├── index.md
│   │       └── .gitignore
│   └── CLAUDE.md.snippet                 ← <!-- atp:begin --> 블록 원본
│
└── addons/
    └── graphify/                         ← add-on 플러그인 atp-graphify 루트
        ├── .claude-plugin/              ← Claude Code add-on manifest
        │   └── plugin.json               ← add-on 정의 (name: atp-graphify, dependencies: ["atp"])
        ├── .codex-plugin/               ← Codex add-on manifest mirror
        │   └── plugin.json               ← 동일 add-on 정의
        ├── agents/                       ← graphify 에이전트 3개
        │   ├── graph-refresh-checker.md
        │   ├── graphify-lookup-advisor.md
        │   └── graphify-update-advisor.md
        └── docs/
            └── graphify-usage.md         ← graphify add-on 설치·통합 가이드
```

---

## 2. init 산출물 트리 — 소비 프로젝트

`/atp:init` 실행 시 `${CLAUDE_PROJECT_DIR}` 기준으로 아래 항목을 생성한다. 이미 존재하는 파일은 덮어쓰지 않는다(멱등).

```
<소비 프로젝트 루트>/
│
├── CLAUDE.md                             ← 기존 파일 하단에 <!-- atp:begin --> 블록 멱등 append
│                                             (docs-first 정책 + /atp:task 진입 안내 포함)
├── .gitignore                            ← .claude/work-session/ 라인 추가 (없는 경우)
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

`/atp:task` 실행 시 세션마다 생성된다. `.gitignore` 로 커밋 제외.

```
.claude/work-session/<sid>/         ← 세션 공유 상태. sid = YYYYMMDD-HHMMSS
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

- [../development/agent-catalog.md](../development/agent-catalog.md) — base atp 10개 + add-on atp-graphify 3개 에이전트 상세
- [../development/agent-team-protocol.md](../development/agent-team-protocol.md) — 운영 프로토콜 전문
- [../usage/setup-checklist.md](../usage/setup-checklist.md) — init 후 설정 체크리스트
- [docs/adr/ADR-0002-plugin-only-migration.md](../adr/ADR-0002-plugin-only-migration.md) — cp-R 폐기·plugin-only 전환 결정 기록
