---
kind: changes
title: research 불확실성 게이트 3종 + graphify-out 방어 + prior_lookup handoff
date: 2026-07-21
related_adr: ADR-0018
versions:
  base: 2.8.0 → 2.9.0
  addon: 2.1.0 → 2.2.0
---

# research 불확실성 게이트 3종 + graphify 깔때기 방어 (2.9.0 / add-on 2.2.0)

자료조사 방법론 원론 진단(세션 20260721-165857) → 2축 상호 리뷰 검증(20260721-171300) → 본 구현(20260721-173741). 결정 근거: [ADR-0018](../adr/ADR-0018-research-falsification-corroboration-harvest.md).

## base atp (2.8.0 → 2.9.0)

- **research-advisor v2→v3**
  - 게이팅 추가 2종: **단건 사실 독립확증**(권위 승격 대상 외부·시변 사실에 독립 출처 ≥2 미확보 시 `single-source: true` 플래그 + 승격 금지), **반증 패스**(load-bearing `확인됨` 격상 직전 반대 증거 탐색 1회 기록 의무, 항목당 1회 상한).
  - 자가검증 5→7 항목: 6(반증 패스 기록·single-source 플래그), 7(수확 점검 — 취합 시 load-bearing 갭 잔존이면 §4.8 보강 조사로 **1회 한정 재분해**, 고위험/열거형 한정).
  - 입력에 optional `prior_lookup`(graphify-lookup miss handoff — §2.9 출처 명시 수용, 중복 재탐색 방지).
- **protocol.md**: §4.8 단건 확장 문단(ADR-0018), §7 sid 접미사 허용 명문화, §8 경량 프로파일 `research-lite`(조사·고찰 전용 세션, `retroactive: true` 라벨 의무 포함), §11 게이트 명문화 관례(발동+미발동 조건 동시 명기).
- **SKILL.md §3**: research-lite 진입 연결 1줄.

## add-on atp-graphify (2.1.0 → 2.2.0)

- **graphify-lookup-advisor v1→v2**: no-graph 판정 전 `graphify-out/` 존재 Glob 1회 → 존재 시 **no-graph (misplaced-output)** 반환 + 권고를 research 아닌 배치(graphify-update-advisor)로. 금기에 "존재 Glob 만 허용" carve-out 동시 명시. miss/stale-suspected 반환에 `prior_lookup` 블록 추가.
- **graph-refresh-checker v1→v2**: 동일 misplaced-output 분기 (peer 대칭 §11.1).
- **graphify-usage.md §4.1**: 감지 동작 안내 1줄.

## 소비자 영향

- `/plugin update` 로 base 2.9.0 + add-on 2.2.0 수신 시: research 산출물에 `single-source` 플래그·반증 기록이 추가로 나타나고, graphify 산출물 미배치 상태에서 research 낭비가 차단된다. 기존 세션 보고서·산출물 소급 영향 없음(옵셔널·additive).
