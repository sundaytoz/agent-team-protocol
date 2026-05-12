---
kind: architecture
title: 구성 파일 맵
description: 템플릿의 디렉토리·파일별 역할과 cp-R 복사 여부를 한 장으로 정리.
owner: template-maintainer
stability: stable
last_reviewed: 2026-05-07
---

# 구성 파일 맵

본 템플릿 리포의 파일 구조. 이식자(cp-R 복사 사용자) 는 복사 후 자기 프로젝트 상황에 맞게 루트를 갱신한다. 복사 제외 목록은 `../../README.md` §3(설치) 을 단일 권위로 참조한다.

## 트리

```
agent-team-protocol/
├── README.md                                 ← 이식자 진입점 (cp-R 복사 제외)
├── CLAUDE.md                                 ← 프로젝트 루트 진입점 템플릿
├── TEMPLATE_DEV.md                           ← 템플릿 자체 백로그 (cp-R 복사 제외)
├── SECURITY.md                               ← 템플릿 리포 보안 채널 (cp-R 복사 제외)
├── AUTHORS                                   ← 원작자 표기 (cp-R 복사 제외)
├── LICENSE                                   ← MIT (cp-R 복사 제외)
│
├── .claude/
│   ├── skills/task/
│   │   └── SKILL.md                          ← /task 명령 진입점
│   └── agents/                               ← 에이전트 정의 13개
│       ├── requirements-advisor.md           │ Tier 2
│       ├── research-advisor.md               │ Tier 3 — parallel-explorer worker 호출
│       ├── parallel-explorer.md              │ Worker (research 소속)
│       ├── design-advisor.md                 │ Tier 2
│       ├── implementation-advisor.md         │ Tier 3 — code-writer / migration-writer 호출
│       ├── code-writer.md                    │ Worker (impl 소속)
│       ├── migration-writer.md               │ Worker (impl 소속)
│       ├── verification-advisor.md           │ Tier 2 — 의도적으로 컨텍스트 제한
│       ├── documentation-advisor.md          │ Tier 2
│       ├── retrospective-advisor.md          │ Tier 2 — 세션 종료 직전
│       ├── graphify-lookup-advisor.md        │ Tier 2 — graph 있을 때만
│       ├── graphify-update-advisor.md        │ Tier 2
│       └── graph-refresh-checker.md          │ staleness 판정 전용
│
└── docs/
    ├── index.md                              ← docs-first 허브 (모든 작업 시작 전 필독)
    ├── adr/                                  ← 되돌리기 어려운 결정 (번호제, 불변)
    ├── analysis/
    ├── architecture/
    │   ├── index.md
    │   └── file-map.md                       ← 이 문서
    ├── backlog/
    ├── changes/
    ├── contracts/
    ├── development/
    │   ├── index.md
    │   ├── agent-team-protocol.md            ← 권위 레퍼런스 (§1~§14)
    │   ├── agent-catalog.md                  ← 에이전트 정의 요약 카탈로그
    │   ├── verification-strategies.md        ← L1/L2/L3 전략 레지스트리
    │   ├── graphify-usage.md                 ← /graphify 설치·통합
    │   ├── search-tool-matrix.md             ← 탐색 도구(LSP/graphify/Grep 등) 선택 매트릭스
    │   ├── documentation-guidelines.md
    │   └── document-category-classification.md
    ├── domain/
    ├── feedback/                             ← 검토·수정 요청 inbox (선택)
    ├── graph/
    │   ├── index.md                          ← graphify 메타 (커밋 대상)
    │   └── .gitignore                        ← 본체(HTML/JSON) 무시
    ├── issues/
    ├── maintenance/
    ├── security/
    ├── usage/
    │   ├── index.md
    │   ├── faq.md                            ← 이식자 FAQ + 이식자 실수 카탈로그
    │   └── setup-checklist.md                ← 이식 후 30분 설정 체크리스트
    └── work-log/
```

## 런타임에만 생기는 디렉토리 (템플릿에 없음, `/task` 가 생성)

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

이 디렉토리는 `.gitignore` 대상이다 (README §3 설치 절의 `.gitignore` 갱신 안내 참조).

## 파일별 역할 요약

| 파일 | 역할 | 권위 문서 |
|---|---|---|
| `README.md` | 이식자 진입점 (5분 랜딩) | 이 리포 루트 |
| `CLAUDE.md` | 프로젝트 루트 진입점 — Claude Code 가 세션 시작 시 자동 로드 | 루트 |
| `.claude/skills/task/SKILL.md` | `/task` 명령 진입 스킬. orchestrator 9단계 트리거 | 해당 SKILL.md |
| `.claude/agents/*.md` | 13개 에이전트 정의 (Tier 2/3/Worker) | 각 파일 + `../development/agent-catalog.md` |
| `docs/development/agent-team-protocol.md` | 3-tier 운영 권위 레퍼런스 (§1~§14) | 해당 파일 |
| `docs/development/verification-strategies.md` | L1/L2/L3 검증 전략 레지스트리 | 해당 파일 |
| `docs/development/graphify-usage.md` | /graphify 설치·통합 규약 | 해당 파일 |

## 관련 문서

- [../../README.md](../../README.md) §3 — 설치 절차 및 복사 제외 목록 (cp-R 권위)
- [../development/agent-catalog.md](../development/agent-catalog.md) — 에이전트 13개 상세
- [../development/agent-team-protocol.md](../development/agent-team-protocol.md) — 운영 프로토콜 전문
