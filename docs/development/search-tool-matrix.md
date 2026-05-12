---
title: 탐색 도구 선택 매트릭스
category: development
status: active
updated_at: 2026-05-06
related:
  - agent-team-protocol.md
  - graphify-usage.md
---

# 탐색 도구 선택 매트릭스

에이전트 팀이 탐색/검색 작업에서 어떤 도구를 언제 쓸지 결정하는 기준을 정의한다.

---

## §1 도구 분류 및 특성 (중립)

### LSP (Language Server Protocol)

**강점**
- 심볼 정의/타입/참조를 정확한 구문 분석 기반으로 조회
- Rename, Go-to-definition, Find-all-references 등 정밀 심볼 네비게이션
- 언어 서버가 지원하는 모든 언어에서 동일한 인터페이스

**한계**
- 모듈 간 거시적 군집·연관 관계 시각화는 제공하지 않음
- 프로젝트 전체 아키텍처 관점 파악에는 부적합
- 언어 서버가 설치·구동되어 있어야 함

### graphify (지식 그래프)

**강점**
- 모듈/파일/심볼 간 연관 관계를 군집·엣지로 시각화
- god node, 순환 의존, 계층 위반 등 구조적 냄새 탐지
- 거시적 "무엇이 무엇을 쓰는가" 패턴 파악에 최적

**한계**
- 정확한 심볼 단위 조회보다 코스트가 높고 신선도 관리 필요
- 코드 변경 후 stale 상태면 잘못된 관계 반환 가능
- 그래프가 없거나 낡으면 재생성 비용 발생

### Grep (텍스트 패턴)

**강점**
- 파일 타입/경로 무관하게 정규식으로 패턴 검색
- 빠르고 별도 인덱스 불필요
- 코드·문서·설정 파일 모두 동일하게 탐색

**한계**
- 심볼 경계를 모름 — 같은 이름이 다른 맥락에 있어도 모두 히트
- 구조적 의미 해석 불가 (그냥 문자열 매칭)

### Glob (경로 패턴)

**강점**
- 파일 존재 확인, 경로 목록 수집에 최적
- 확장자·디렉토리 구조 기반 필터링

**한계**
- 파일 내용을 보지 않음
- 심볼/의미 정보 없음

### Read (직접 읽기)

**강점**
- 특정 파일의 내용을 그대로 읽어 해석
- 타임라인·로드맵·Phase 정보처럼 구조화된 문서를 직접 소비할 때 최적

**한계**
- 목표 파일 경로를 미리 알아야 함
- 여러 파일에 걸친 패턴 탐색에는 부적합

### WebFetch / WebSearch (외부 자료)

**강점**
- 외부 라이브러리 API, 공식 문서, 릴리스 노트 조회
- 프로젝트 외부 정보

**한계**
- 프로젝트 내부 코드 탐색 불가
- 네트워크 의존, 최신성 불확실

---

## §2 목적별 1차 도구 매트릭스 (중립)

| 목적 | 1차 도구 | 보조 도구 | 스킵 가능 조건 | 선택 근거 |
|---|---|---|---|---|
| 심볼 정의 점프 (함수/클래스/변수 위치 확인) | LSP | Grep | 파일 경로가 이미 확실할 때 Read | 구문 분석 기반 정확도 > 텍스트 매칭 |
| 참조·호출처 전수 조회 | LSP | Grep | - | LSP find-all-references 는 rename-safe 수준 정확도 |
| 모듈 연관·군집 파악 | graphify | Grep | 그래프 fresh 판정이 없으면 skip 불가 | 엣지 시각화가 핵심 목적 |
| god node·순환 의존 탐지 | graphify | Grep | - | audit.md 가 자동 집계 |
| 키워드·패턴 검색 (코드/문서 혼재) | Grep | Glob | - | 파일 타입 무관 동일 인터페이스 |
| 파일·경로 목록 수집 | Glob | Grep | 경로가 확실하면 Read | 내용 불필요 시 Glob 이 빠름 |
| 로드맵·Phase 정보 조회 | Read (docs 직접) | Grep | - | 구조화 문서는 직접 읽기가 정확 |
| 장애·변경 이력 조회 | Read (work-log/changes 직접) | Grep | - | 시간축 조회는 파일 직접 읽기 |
| 외부 라이브러리 API 조회 | WebFetch / WebSearch | - | 이미 로컬 docs 에 있으면 Read | 외부 최신 정보는 웹 직접 조회 |
| graphify stale 판정 | graph-refresh-checker | - | source_commit == HEAD 이면 fresh 자동 | 판정 전용 에이전트로 일관성 유지 |

**표 사용법**: 목적 행을 찾아 1차 도구를 기본 선택. 스킵 가능 조건에 해당하면 보조 도구 또는 Read 로 대체.

---

## §3 graphify stale 판정 기준 (중립)

stale 판정은 `graph-refresh-checker` 가 전담한다. 에이전트가 직접 판정하지 않는다.

### 핵심 원칙: scope 대상 경로 내 변경이 없으면 fresh

```
git diff <source_commit>..HEAD -- <scope 대상 경로>
```

이 명령의 출력이 **비어있으면 자동 fresh**. scope 밖(docs/, .claude/, *.md 등)에만 커밋이 쌓여 있어도 해당 scope 는 fresh 로 판정한다.

### 판정 레벨

| 레벨 | 조건 |
|---|---|
| **fresh** | `source_commit == HEAD` OR scope 내 변경 파일 0건 |
| **partial-stale** | scope 내 변경 있으나 구조적 시그널 미미 (주석·docstring·타입 힌트 조정만), 또는 일부 scope 만 변경 |
| **fully-stale** | 여러 scope 에 걸쳐 구조적 시그널 다수 (import/export 경로 변경, 함수 시그너처 변경, 파일 A/D 10건 이상) |
| **no-graph** | `docs/graph/index.md` 없거나 `source_commit: null` |

### 문서 전용 커밋 오판 방지

scope 대상 경로가 `src/**` 처럼 코드만 포함하면, `docs/` 나 `.claude/` 의 커밋은 stale 판정에 영향을 주지 않는다. 이 동작이 의도적임을 명시하여 "왜 fresh 인가?" 오해를 방지한다.

### 구조적 시그널 예시 (Python 프로젝트)

- `import <module>` / `from <module> import` 추가·제거·경로 변경
- `def `, `class `, `async def ` 시그너처 변경
- `__all__` 목록 변경
- Alembic 마이그레이션 파일 추가 (DB 스키마 구조 변경)

---

## §4 LSP vs graphify vs Grep 결정 트리 (중립)

```
탐색 목적을 정의했는가?
│
├─ 심볼 이름/타입/정의 위치가 정확히 필요한가?
│   └─ YES → LSP (find-definition / find-references)
│
├─ 모듈 간 연관·군집·아키텍처 패턴이 필요한가?
│   ├─ YES → graphify 조회 (graph-refresh-checker 선행)
│   │         └─ stale/no-graph 이면 graphify-update-advisor 경유 후 재시도
│   └─ NO → 다음 분기로
│
├─ 특정 파일 경로를 이미 알고 있거나 타임라인/로드맵 문서인가?
│   └─ YES → Read (직접 읽기)
│
├─ 파일 존재·목록이 필요한가? (내용 불필요)
│   └─ YES → Glob
│
├─ 키워드·패턴이 어떤 파일에 있는지 모르는가?
│   └─ YES → Grep
│
└─ 외부 라이브러리·공개 API 정보인가?
    └─ YES → WebFetch / WebSearch
```

**결정 트리 우선순위 원칙**: 정확도(LSP) → 거시 구조(graphify) → 직접 경로(Read) → 경로 목록(Glob) → 패턴 검색(Grep) → 외부(Web). 비용이 낮은 도구부터 시도하되, 목적이 명확하면 바로 1차 도구로 진입.

---

## §5 프로젝트 적응 가이드 (템플릿)

프로젝트에 템플릿을 적용할 때 §5 를 해당 프로젝트 고유 섹션으로 채운다. 아래는 작성 형식 예시다.

### 프로젝트 탐색 진입점 (작성 예시)

| 탐색 목적 | 진입점 경로 | 도구 |
|---|---|---|
| 로드맵·Phase 계획 | `<프로젝트 설계 문서 경로>` | Read |
| 작업 로그·완료 항목 | `docs/work-log/` | Read |
| 미완료·backlog | `docs/backlog/<...>` | Read |
| API/이벤트 계약 | `docs/contracts/` | Read + Grep |
| 모듈 구조 그래프 | `docs/graph/<scope>/` (graph-refresh-checker 선행) | graphify |
| 심볼 정의·참조 | LSP 또는 Grep | LSP / Grep |
| 피드백·인박스 | `docs/feedback/inbox/` | Read |

### 프로젝트 scope 경로 기준 (graph-refresh-checker 용, 작성 예시)

| Scope | 대상 경로 | stale 영향 대상 |
|---|---|---|
| `src` | `src/<package>/**` | 소스 파일의 import/정의/시그너처 변경 |

문서·설정 전용 커밋 (`docs/`, `.claude/`, `*.md` 등) 은 코드 scope 의 stale 판정에 영향을 주지 않는다.

### 관련 문서

- [agent-team-protocol.md](./agent-team-protocol.md) — 에이전트 팀 운영 규약
- [graphify-usage.md](./graphify-usage.md) — graphify 설치·운용 및 갱신 트리거
- [documentation-guidelines.md](./documentation-guidelines.md) — 문서 작성 규칙
