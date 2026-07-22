---
kind: adr
adr_number: "0018"
title: research 불확실성 게이트 3종 확장 — 반증 패스 + 단건 사실 독립확증 + 수확 점검(1회 재분해) (§4.8 인접, ADR-0011 적층)
status: accepted
date: 2026-07-21
deciders:
  - template-maintainer
  - stzjungsoo
supersedes: []
related_commits:
  - (feat/research-falsification-gates 브랜치 — PR→main 머지 시 SHA 확정)
---

# ADR-0018: research 불확실성 게이트 3종 확장 — 반증 패스 · 단건 독립확증 · 수확 점검

## 상태

**Accepted** — 2026-07-21. 세션 20260721-165857(원론 진단 조사) → 20260721-171300(2축 상호 리뷰) → 20260721-173741(본 구현). ADR-0005(출처 신뢰도 게이팅)·ADR-0011(§4.8 축-완결성) 위에 적층. supersede 아님 — §4.8 의 "독립 ≥2 교차확증" 원리를 카탈로그 *축* 에서 **단건 사실**로 확장하고, 같은 축에 반증·수확 장치 2개를 인접 배치한다.

base atp 매니페스트 4개 `2.8.0` → `2.9.0` (minor). add-on atp-graphify 2개 `2.1.0` → `2.2.0` (동반 — graphify-out 방어, 본 ADR 의 부수 결정 4).

---

## 맥락

자료조사 방법론 원론(triangulation·Admiralty 2D·exploration/exploitation·premature stopping·adversarial verification)을 잣대로 ATP 조사 서브시스템을 진단한 조사(세션 20260721-165857, 4포인트 fan-out + 후속 1건)와, 그 산출물을 동일 스펙 서브에이전트 2축(프로토콜 로드/미로드)이 상호 리뷰한 검증(세션 20260721-171300)이 다음 갭에 수렴했다:

1. **반증(adversarial) 게이트 전무** — `반증·disconfirm·red-team·대안가설` 이 프로토콜·research-advisor·parallel-explorer 전체에서 0-hit (양 리뷰 축이 독립 grep 으로 재현). 기존 규율은 전부 "확인 경로" 방향이라, 확증편향의 직접 해독제가 없다. 취합자 자신의 오판(arXiv 실재 논문을 위조로 의심 → 반증 검증으로 교정)이 세션 내 살아있는 증거.
2. **단일출처 → 권위 승격 경로 열림** — 독립 ≥2 교차확증 의무가 §4.8 카탈로그 *축* 에만 있고, 하류(design/AC)를 실제로 흔드는 **단건 사실**(버전·수치·정책값·seed 가정)에는 없다. 저질 출처라도 1차 확인만 하면 `확인됨`→`high`→권위 전제로 승격 가능.
3. **조사 종료판정 부재** — 조사 깊이가 착수 시 분해로 확정되는 단일 패스 fan-out. saturation/무수확 정지 규칙 0-hit. 착수 분해가 얕으면 과소조사를 감지할 장치가 없다(premature stopping 사각). 단, "K회 연속 무수확" 류 원안은 라운드 개념이 없는 단일 패스 구조에 그대로 적용 불가(2축 리뷰 공통 판정) — 재정식화 필요.
4. **(부수) 깔때기 무결성 구멍 실증** — `/graphify` 기본 출력(`graphify-out/`)을 `docs/graph/` 로 미이동 시, lookup·checker 가 같은 경로만 봐 동일 사각을 공유한 채 no-graph 오판 → 그래프가 있는데도 research 전체 낭비(세션 20260721-165857 실증).

---

## 결정

### 결정 1 — 반증 패스 (load-bearing 격상 전 1회)

research-advisor 게이팅에 추가: **load-bearing 사실**(design/AC/보고서의 권위 전제로 승격되는 사실)을 `확인됨` 으로 격상하기 직전, **반대 증거 탐색 1회** 수행 + 결과 기록("반증 시도: 발견 없음" 도 명시 — 시도 사실이 기록 대상). 자가검증 6번 항목으로 집행.

- **발동 조건**: load-bearing 격상 시에만. **오버헤드 상한**: 항목당 1회. **미발동**: 비승격 참고 항목·내부 repo 사실.
- 기각 대안 — 전 항목 반증 의무: 조사 비용 배증, 저위험 항목엔 정보이득 없음. 발동 조건·상한이 §11 게이트 명문화 관례(부수 결정 5)의 첫 적용례.

### 결정 2 — 단건 사실 독립확증 (`single-source` 플래그)

§4.8 의 독립 ≥2 교차확증을 **권위 승격 대상 단건 사실**(외부·시변: 버전·수치·정책값·seed 가정)로 확장. 독립 출처 미확보 시 `확인됨` 이어도 `single-source: true` 플래그 기본 부착 — 플래그 항목은 검증 전 권위 승격 금지. 신규 tier·enum 없이 기존 마커 체계에 플래그 1개만 추가(ADR-0011 결정 1 의 어휘 재사용 원칙 유지).

- **미발동**: 내부 repo 사실(경로:line 직접 검증 가능).

### 결정 3 — 수확 점검 (1회 한정 재분해)

"K회 연속 무수확 정지" 원안을 기각하고(단일 패스 구조에 라운드 부재 — 범주 오류), **"취합 시 load-bearing 갭 잔존 → §4.8 절차 1 '보강 조사' 로 1회 한정 재분해"** 로 재정식화해 채택. 자가검증 7번 항목으로 집행. 조사 종료를 worker-lifecycle/budget 이 아닌 **수확 기준으로 1회 보정**하는 최소 장치다.

- **발동 조건**: 고위험/열거형 조사만. **상한**: 재분해 1회 — 반복 루프 금지(그래도 남으면 "미해결"+`concerns` 로 반환). 실행 모델(단일 패스)을 바꾸지 않고 §4.8 기존 어휘에 접속한다.

### 결정 4 — (부수, add-on) graphify-out 미이동 방어 + prior_lookup handoff

- `graphify-lookup-advisor`·`graph-refresh-checker` 의 no-graph 판정 직전에 `graphify-out/` 존재 **Glob 1회** 확인 → 존재 시 **no-graph (misplaced-output)** 로 반환하고 후속을 research 가 아닌 배치(mv)+메타 갱신으로 권고. lookup 의 "graph 외부 읽기 금지" 금기에는 **존재 Glob 만 허용하는 carve-out** 을 같은 커밋에 명시(에이전트 정의 자기모순 방지 — 2축 리뷰 A 축 지적). peer 대칭(§11.1) 준수 — 두 에이전트에 동일 분기.
- lookup miss/stale-suspected 반환에 `prior_lookup`(checked_scopes·queries·miss_reason) 블록 추가 → orchestrator 가 research dispatch 에 **§2.9 출처 명시 규율**로 전달, 동일 scope 중복 재탐색 방지. 탐색 이력이지 검증 사실이 아니므로 권위 전제 사용 금지.

### 결정 5 — (부수, 프로토콜 하우스키핑)

- **§8 경량 프로파일 `research-lite`**: 조사·고찰 전용(코드 변경 0) 세션의 옵셔널 축약 스키마. 준수 갭(보고서 자체 누락)의 구조 요인이 "규범 부적합" 이라는 2축 리뷰 진단의 처방 — 소급 채점이 아니라 규범을 상황에 맞춘다. dispatch 프롬프트 요지의 `input_digest` 기록을 필수로 유지해 "독립 수렴" 주장의 사후 검증 가능성을 확보. 사후 재구성 기록은 `retroactive: true` 라벨 의무.
- **§11 게이트 명문화 관례**: 게이트 신설·개정 시 발동 조건과 **미발동 조건을 같은 절에 명기**(§4.3·§4.8·§2.10 기존 관행의 명문화 1줄 — 신규 관례 아님).
- **§7 sid 접미사 허용 명문화**: `YYYYMMDD-HHMMSS` 뒤 kebab-case 슬러그 접미사 허용(운영 관행 명문화).

---

## 근거 요약 (2축 리뷰 수렴)

- 제안 기각 0건 — 프로토콜 로드 축(A)·최소 컨텍스트 축(B) 리뷰와 상호 크로스 비평 4산출물이 전 제안을 타당/조건부 타당으로 수렴. 조건(발동·상한·carve-out·§2.9 명기)은 전부 본 ADR 결정에 편입.
- 배포 순서: 결정 4(add-on, 유일한 실증 결함, 행동 리스크 0)와 결정 1~3(base, ADR 필요)은 릴리스 단위가 다르나 같은 PR 로 동시 진행(사용자 지시 — 무중단 일괄).
- 증거 파일: `.atp/work-session/20260721-171300-dual-axis-review/artifacts/dual-axis-synthesis.md` (레포 opt-out 정책상 git 미추적 — ADR-0010, 로컬 보존).

## 영향

| 파일 | 변경 |
|---|---|
| `plugins/atp/agents/research-advisor.md` | v2→v3: 입력 `prior_lookup` + 게이팅 2종(단건 독립확증·반증 패스) + 자가검증 6·7 |
| `plugins/atp-graphify/agents/graphify-lookup-advisor.md` | v1→v2: misplaced-output 분기 + carve-out + `prior_lookup` 반환 블록 |
| `plugins/atp-graphify/agents/graph-refresh-checker.md` | v1→v2: misplaced-output 분기 (peer 대칭) |
| `plugins/atp/docs/development/agent-team-protocol.md` | §4.8 단건 확장 문단, §7 sid 접미사, §8 research-lite, §11 게이트 관례 |
| `plugins/atp/skills/task/SKILL.md` | §3 research-lite 연결 1줄 |
| `plugins/atp-graphify/docs/graphify-usage.md` | §4.1 misplaced-output 감지 안내 1줄 |
