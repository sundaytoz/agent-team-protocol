---
kind: docs-index
title: Agent Team Protocol 문서 인덱스
description: 레포 문서의 docs-first 진입점.
owner: template-maintainer
stability: living
last_reviewed: 2026-06-10
---

<p align="center">
  <a href="index.md">한국어</a> ·
  <a href="index.en.md">English</a>
</p>

# 문서 인덱스

이 파일은 agent-team-protocol 레포의 docs-first 진입점이다. 작업을 시작할 때는 여기서 관련 카테고리를 고른 뒤, 해당 카테고리의 `index.md` 를 거쳐 구체 문서를 확인한다.

## 카테고리

| 카테고리 | 오디언스 | 인덱스 |
|---|---|---|
| Usage | 플러그인을 설치하고 소비 프로젝트에 적용하는 사용자 | [docs/usage/index.md](./usage/index.md) |
| Development | ATP 프로토콜, 에이전트, 스킬을 유지보수하는 기여자 | [docs/development/index.md](./development/index.md) |
| Architecture | 레포 구조와 런타임 산출물 경계를 확인하는 기여자 | [docs/architecture/index.md](./architecture/index.md) |
| ADR | 되돌리기 어려운 기술·운영 결정을 추적하는 유지보수자 | [docs/adr/index.md](./adr/index.md) |
| Changes | 실제 구현 변경 이력(런타임 동작·설치 경로 변화)을 확인하는 유지보수자 | [docs/changes/index.md](./changes/index.md) |

## 경계

이 레포의 `docs/` 는 사람(기여자·사용자)용 문서다 — 플러그인 번들에는 포함되지 않는다. 에이전트가 `${CLAUDE_PLUGIN_ROOT}/docs/...` 로 읽는 런타임 레퍼런스는 [plugins/atp/docs/](../plugins/atp/docs/index.md) 에 둔다. `/atp:init` 이 소비 프로젝트에 생성하는 편집형 문서의 원본은 [plugins/atp/templates/](../plugins/atp/templates/) 에서 스캐폴딩한다.

## Add-on

graphify 기능은 옵트인 add-on 이다. 설치·운영·그래프 갱신 규칙은 [plugins/atp-graphify/docs/graphify-usage.md](../plugins/atp-graphify/docs/graphify-usage.md) 를 본다.

## 빠른 진입

- 설치와 초기화: [docs/usage/setup-checklist.md](./usage/setup-checklist.md)
- 문제 해결: [docs/usage/faq.md](./usage/faq.md)
- 팀 운영 프로토콜: [plugins/atp/docs/development/agent-team-protocol.md](../plugins/atp/docs/development/agent-team-protocol.md)
- 에이전트 카탈로그: [plugins/atp/docs/development/agent-catalog.md](../plugins/atp/docs/development/agent-catalog.md)
- 파일 맵: [docs/architecture/file-map.md](./architecture/file-map.md)
- 세션 산출물 `.atp/work-session/` (플러그인 기본=추적 / 이 레포는 opt-out): [docs/architecture/file-map.md#3-런타임-디렉토리](./architecture/file-map.md#3-런타임-디렉토리)
- 결정 이력: [docs/adr/index.md](./adr/index.md)
- 코드 지식 그래프: [docs/graph/index.md](./graph/index.md)
- 릴리스·배포 트리거 (`plugins/atp/` 번들 변경 시 필수): [docs/development/release-checklist.md](./development/release-checklist.md) — **§0 (배포 완결 의무) 먼저**
