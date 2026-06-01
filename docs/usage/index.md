---
kind: usage
title: Usage 카테고리 인덱스
description: plugin 설치·초기화·운영 관련 사용 가이드 인덱스.
owner: template-maintainer
stability: living
last_reviewed: 2026-06-01
---

# Usage — 사용 가이드

이 카테고리는 `atp` / `atp-graphify` 플러그인을 **설치하고 운영하는 사용자 관점**의 문서를 모은다. 내부 구조 설명은 `architecture/`, 개발 규칙은 `development/` 로 분리.

## 목록

- [setup-checklist.md](./setup-checklist.md) — plugin 설치 후 `/atp:init` → placeholder 채우기 → `/atp:task` 스모크 3단계 설정 체크리스트
- [faq.md](./faq.md) — 설치 실패·명령 미인식·graphify skip·init 재실행 등 문제 해결 FAQ

## 설치 순서

1. 마켓플레이스 등록

   ```
   /plugin marketplace add sundaytoz/agent-team-protocol
   ```

2. base 플러그인 설치 (필수)

   ```
   /plugin install atp@agent-team-protocol
   ```

3. graphify add-on 설치 (옵트인)

   ```
   /plugin install atp-graphify@agent-team-protocol
   ```

4. 초기화 — 프로젝트에 docs 골격 + CLAUDE.md 안내 블록 생성

   ```
   /atp:init
   ```

5. placeholder 채우기 → `/atp:task` 스모크 → 완료

상세는 [setup-checklist.md](./setup-checklist.md) 참조.

## 먼저 읽을 순서

1. [setup-checklist.md](./setup-checklist.md) — 설치 직후 설정 (3단계)
2. 문제 발생 시 [faq.md](./faq.md)
3. 에이전트 구성 확인 — [`../development/agent-catalog.md`](../development/agent-catalog.md)
