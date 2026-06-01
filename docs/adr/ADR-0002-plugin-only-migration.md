---
kind: adr
adr_number: "0002"
title: cp-R 배포 폐기 및 plugin-only 2플러그인(atp + atp-graphify) 전환
status: accepted
date: 2026-06-01
deciders:
  - template-maintainer
  - stzjungsoo
supersedes: []
---

# ADR-0002: cp-R 배포 폐기 및 plugin-only 2플러그인(atp + atp-graphify) 전환

## 상태

**Accepted** — 2026-06-01. 세션 `20260601-115424`.

---

## 맥락

### 현황 (결정 이전)

`agent-team-protocol` 레포는 `cp -R .claude docs CLAUDE.md` 방식으로 소비 프로젝트에 이식되는 **cp-R 템플릿**으로 운영됐다. 이 구조는 다음 근본 한계를 가진다.

1. **CLAUDE.md 자동 주입 불가**: 소비 프로젝트에 이미 CLAUDE.md 가 있으면 덮어쓰기 충돌. 없으면 수동 병합 필요. 어느 쪽이든 이식자 실수 위험(M1~M5 카탈로그).
2. **편집형 docs 유지보수 불가**: `verification-strategies.md`, 카테고리 index 등 프로젝트마다 내용이 달라야 하는 파일을 cp-R 로 공유할 수 없다. 업스트림 변경이 이식 프로젝트에 자동 반영되지 않는다.
3. **복사 제외 목록 관리 부담**: README.md, TEMPLATE_DEV.md, AUTHORS, SECURITY.md, LICENSE, work-session 등을 이식 시 수작업으로 제외해야 한다. 실수 빈도 높음(M5).
4. **graphify 선택적 도입 불가**: 템플릿 자체에 graphify 에이전트 3종이 포함돼 있어, graphify 를 원하지 않는 프로젝트도 불필요한 파일을 보유한다.

Claude Code 플러그인 시스템(마켓플레이스, `${CLAUDE_PLUGIN_ROOT}` load-time 치환, `init` 스킬)이 위 한계를 구조적으로 해소할 수 있음이 research(`20260601-115424/research/plugin-spec-findings.md`) 단계에서 확인됐다.

---

## 결정

### 채택안: plugin-only 2플러그인 구조

cp-R 배포 워크플로우를 **완전 폐기**하고 레포를 **마켓플레이스 `agent-team-protocol`(레포명) + 플러그인 2개** 구조로 전환한다.

#### 플러그인 구성

| 플러그인 | install 명령 | 포함 내용 |
|---|---|---|
| `atp` (base, 필수) | `/plugin install atp@agent-team-protocol` | agents 10개(graphify 제외) + skills(task, init) + 번들 레퍼런스 docs + templates |
| `atp-graphify` (add-on, 옵트인) | `/plugin install atp-graphify@agent-team-protocol` | graphify agents 3개 + graphify-usage.md. `dependencies: ["atp"]` |

#### 레포 레이아웃

레포 루트 = base 플러그인 `atp` 의 루트 = 마켓플레이스 `agent-team-protocol`.

- `agents/` (루트 레벨, base 10개)
- `skills/{task,init}/`
- `docs/` (번들 레퍼런스, 읽기전용)
- `templates/` (init 스캐폴딩 원본)
- `addons/graphify/` (add-on 플러그인 루트, `source: "./addons/graphify"`)

상세 트리는 [`../architecture/file-map.md`](../architecture/file-map.md) 참조.

#### `${CLAUDE_PLUGIN_ROOT}` vs `${CLAUDE_PROJECT_DIR}` 경계

- **번들 레퍼런스** (`agent-team-protocol.md`, `agent-catalog.md` 등) → `${CLAUDE_PLUGIN_ROOT}/docs/...` (읽기전용, agent load-time 치환)
- **편집형 문서** (`verification-strategies.md`, 카테고리 index 등) → `init` 이 `${CLAUDE_PROJECT_DIR}/docs/...` 로 스캐폴딩
- **산출물** (`work-session/`, 소스 코드 등) → `${CLAUDE_PROJECT_DIR}/...`

#### `init` 스킬 역할

`/atp:init` 이 소비 프로젝트에:
1. `docs/` 골격 14 카테고리 index + `verification-strategies.md` + `document-category-classification.md` + `docs/graph/` 생성
2. 프로젝트 `CLAUDE.md` 에 `<!-- atp:begin --> ... <!-- atp:end -->` docs-first + `/atp:task` 안내 블록 **멱등 append**
3. `.gitignore` 에 `.claude/work-session/` 라인 추가

#### 진입점 네임스페이스

- `/atp:task` — 에이전트 팀 모드 진입
- `/atp:init` — 프로젝트 초기화

---

## 검토한 대안

### 대안 A: dual-mode (cp-R 유지 + plugin 선택 추가)

cp-R 을 유지하면서 plugin 경로를 병렬 제공하는 방안. **기각** 이유:

- 두 배포 경로를 동시에 문서화·테스트·유지보수해야 하는 복잡도 증가.
- cp-R 의 구조적 한계(CLAUDE.md 주입 불가, 복사 제외 관리) 가 해소되지 않는다.
- 장기적으로 cp-R 이 사실상 dead-path 가 될 것이 명확함.

### 대안 B: 구조 최소 (agent + skill 파일만 plugin, docs 제외)

plugin 에 agent/skill 만 번들하고 docs 는 소비자가 별도 관리하는 방안. **기각** 이유:

- `agent-team-protocol.md` 등 레퍼런스 docs 를 번들하지 않으면 agent 가 런타임에 프로토콜을 읽을 수 없다.
- `${CLAUDE_PLUGIN_ROOT}` 치환의 핵심 가치(읽기전용 레퍼런스 공유)를 포기하게 된다.

### 대안 C: graphify 를 base 에 포함 (분리 없음)

graphify 에이전트 3종을 base 에 유지하는 방안. **기각** 이유:

- graphify 스킬 자체(`~/.claude/skills/graphify/`)가 사용자 환경 소유이므로, base 에 포함해도 스킬 미설치 프로젝트에서 agent 가 작동하지 않는다.
- 불필요한 에이전트 3종이 base 에 노출돼 사용자 혼란을 야기.
- 옵트인 분리가 "graphify 미도입 시 skip" 기존 규약과 더 자연스럽게 정합.

---

## 결과

### 긍정적 결과

- **CLAUDE.md 자동 주입**: init 이 멱등 append 로 처리. 이식자 수작업 불요.
- **편집형 docs 격리**: 번들(읽기전용) vs 스캐폴딩(프로젝트 편집) 명확한 분리.
- **복사 제외 목록 소멸**: 더 이상 "복사 제외" 관리가 필요 없다.
- **graphify 옵트인**: 미도입 프로젝트는 add-on 없이 base 만으로 완전 동작.
- **네임스페이스 명확**: `/atp:task`, `/atp:init` 으로 플러그인 출처 명시.
- **업스트림 갱신**: plugin 업데이트 시 소비 프로젝트가 자동으로 최신 레퍼런스 docs 를 받는다.

### 부정적 결과 / 트레이드오프

- **self-dogfooding 마찰**: 이 레포 자체에서 개발 시 로컬 플러그인 enable(`/plugin marketplace add ./`) 이 필요하다. 미설치 상태에서는 `${CLAUDE_PLUGIN_ROOT}` 경로가 치환되지 않아 Read 경로가 깨진다. README §5 self-dogfooding 절에 안내 포함.
- **init 재실행 필요**: 기존 cp-R 이식 프로젝트는 신규 install 후 `/atp:init` 을 한 번 실행해야 한다.
- **런타임 검증 의존**: plugin.json / marketplace.json 유효성 및 네임스페이스 실호출은 실제 플러그인 install 환경에서만 완전 검증 가능.

---

## 관련 문서

- [`../architecture/file-map.md`](../architecture/file-map.md) — 플러그인 레이아웃 및 경계 규칙
- [`../development/agent-catalog.md`](../development/agent-catalog.md) — base atp 10개 + add-on atp-graphify 3개 에이전트 목록
- [`../usage/setup-checklist.md`](../usage/setup-checklist.md) — plugin 설치 후 설정 체크리스트
- `.claude/work-session/20260601-115424/design.md` — plugin-only 전환 설계 확정 문서 (v2, OQ-1/2/3 해소)
- `.claude/work-session/20260601-115424/research/plugin-spec-findings.md` — 플러그인 스펙 리서치 결과
