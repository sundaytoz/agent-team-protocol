---
kind: backlog
title: Backlog — 외부·후속 구현 제안
description: 현재 레포 범위 밖이거나 선행 capability가 필요한 검토 가능한 제안서.
owner: template-maintainer
stability: living
last_reviewed: 2026-08-27
---

# Backlog — 외부·후속 구현 제안

이 카테고리는 ATP source에서 직접 구현할 수 없는 upstream 변경과 아직 채택되지 않은 후속 제안을 둔다. 현재 동작 계약이나 완료된 변경 이력은 ADR·Changes에 둔다.

## 목록

- [Codex CLI collaboration await v1 제안](./codex-cli-collaboration-await-v1.md) — product-managed all-results barrier(P0), timeout-free atomic await API(P1), durable plane 보류(P2)
- [Codex CLI 0.149.1 hook-guarded bounded pool qualification handoff](./codex-cli-hook-guarded-bounded-pool.md) — ATP-side hook ledger/barrier 후보, 2026-08-28 T1–T9 결과와 이를 4개 독립 축(all-results barrier / in-flight control / approval continuation / packaging scope)으로 분해한 promotion gate, A축 blocker 해소와 남은 재검증 조건
