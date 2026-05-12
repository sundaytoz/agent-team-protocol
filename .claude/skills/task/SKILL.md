---
name: task
description: 에이전트 팀(Orchestrator + Advisor + Worker) 모드로 진입해 요청을 처리. 자동 적용되지 않고 사용자가 명시적으로 `/task [요청]` 으로 호출해야 진입한다.
trigger: /task
---

# /task

이 명령이 호출되면 메인 에이전트는 **Orchestrator** 역할로 전환된다. 이 역할 규약은 `docs/development/agent-team-protocol.md` 를 권위 레퍼런스로 한다.

## 사용법

```
/task                  # 인자 없음 — 사용자 요청 본문을 이 세션의 직전 메시지에서 수렴
/task <요청 본문>      # 인자로 작업 요청을 바로 전달
/task <feedback slug>  # (feedback inbox 가 있는 프로젝트) inbox 특정 항목을 시작점으로
```

## Orchestrator 진입 절차

### 1. 프로토콜 로드

반드시 다음 문서를 **전문 읽기** 하여 세션 컨텍스트에 주입:

- `docs/development/agent-team-protocol.md` — 호출 모델 / 충돌 조정 / 스케일 루브릭 / 보고서 스키마 v1 / 파괴적 조작 게이트 / 확장 트리거

그 외 참조가 필요할 수 있는 문서 (Read 는 필요 시):

- `docs/development/verification-strategies.md`
- `docs/index.md` (docs-first)
- `docs/feedback/index.md` (feedback slug 입력 시, 해당 기능이 있는 프로젝트에 한함)

### 2. 공유 상태 디렉토리 생성

```
.claude/work-session/<sid>/
```

`sid` = `YYYYMMDD-HHMMSS` (프로젝트 타임존 기준). Orchestrator 가 Bash 로 생성:

```bash
mkdir -p .claude/work-session/<sid>/{research,implementation,artifacts}
```

**재개 규약**: 동일 sid 디렉토리가 이미 존재하면 이어쓰지 않고 새 sid 로 시작하되 `report.md` 에 `resumed_from: <이전 sid>` 필드를 기록한다. 이전 보고서의 미완료 섹션은 링크만 남기고 이번 세션에서 재수행.

### 3. report.md 초기화

해당 디렉토리에 `report.md` 를 프로토콜 §8 스키마 v1 로 생성. 최초엔 헤더 + `user_request` + `Invocations: []` 만.

### 4. 요청 해석

- 인자 있음 → 인자 텍스트를 `user_request` 로
- 인자 없음 → 사용자 직전 메시지 또는 명시 요청 수렴
- feedback slug → `docs/feedback/inbox/<slug>*.md` 탐색 → frontmatter `status: open` → `in_progress` 로 갱신 + 본문을 `user_request` 로 (프로젝트에 feedback 플로우가 있는 경우)

### 5. Advisor 호출 계획 수립

원 요청을 훑고 어떤 advisor 를 어떤 순서로 호출할지 결정한다. 일반적 흐름 (생략 가능):

```
requirements-advisor
  → graphify-lookup-advisor → (miss 시) research-advisor
  → design-advisor
  → implementation-advisor
  → verification-advisor
  → documentation-advisor
  → (대규모 구조 변경 시) graph-refresh-checker → graphify-update-advisor
  → retrospective-advisor
```

**스킵 기준**:

- 요구가 명확하면 requirements 스킵
- 기존 문서로 충분하면 research 스킵
- 마이크로 편집(한 파일 몇 줄) 은 **advisor 전체 스킵 + orchestrator 직접 수행** 허용 (프로토콜 예외 조항)
- 설계 산출물이 **파일 영향 맵 + 계약 + 시퀀스** 까지 확정적이면 `implementation-advisor` 스킵 + orchestrator 직접 구현 허용

**스킵 불가 (항상 실행)**:

- **verification-advisor / 통합 검증 스크립트** — 코드 변경이 1줄이라도 있으면 반드시 세션 종료 전에 통과해야 한다. 마이크로 편집이라도 예외 없음.
- **버그 수정 시 회귀 테스트** — 수정 전에는 실패하고 수정 후엔 통과하는 테스트를 같은 커밋에 포함. `verification-strategies.md` 의 "버그 범주 → 적용 L 레벨" 표 준수.

**Worker 계층**: 파일 단위 분할·동시 수정 방지·파일 소유권 맵은 `implementation-advisor` 책임. 상세는 프로토콜 §7. SKILL 본문에서 반복하지 않음.

**병렬 호출**: 독립 advisor (예: `research-advisor` 내부 `parallel-explorer`) 는 병렬 실행이 기본. orchestrator 가 상위 advisor 여러 개를 동시 호출하는 것은 컨텍스트 오염 리스크로 기본 금지. 자세한 규약은 프로토콜 §2.

### 6. 각 호출에 모델 override

프로토콜 §5 루브릭으로 스케일 평가 후 Agent 툴 `model` 파라미터로 `haiku` / `sonnet` / `opus` 지정. 근거 한 줄을 `report.md` 의 `invocations[].model_choice.rationale` 에 기록.

### 7. 충돌 중재

advisor 산출물의 `concerns` 필드 교차 검사. 프로토콜 §4 절차 준수. 1라운드 실패 시 사용자에게 `AskUserQuestion`.

### 8. 파괴적 조작 게이트

프로토콜 §6 에 해당하는 조작은 orchestrator 가 사용자 확인 후에만 실행. Advisor/Worker 가 직접 수행 금지.

**게이트 통과 후 검증 실패 시 롤백**: 파괴적 조작이 사용자 승인 후 실행되었고 후속 검증이 실패하면 orchestrator 가 **즉시** 되돌리기를 시도한다 — `git revert`, 파일 복원, migration down 등. 자동 복원이 불가능한 영역(외부 서비스 상태 변경·공개 게시 등) 이면 `needs_user_verification` 에 수동 복구 단계를 명시하고 세션을 닫지 않는다.

### 9. 세션 종료

**종료 조건 (의무)**:

1. **통합 검증 스크립트 통과** — L1 pass, L2 는 pass 또는 skip(원격/seed 미지정). L2 실패 상태에서 세션 종료 금지.
2. 보고서의 "verified_by_me" 섹션에 실제로 통과한 단계를 나열:
   - `L1: typecheck / unit+regression`
   - `L2: contract-<외부 의존> (pass | skipped:<reason>)`
   - 로그 스캔: `clean | warn:<n>건`
3. 보고서의 "needs_user_verification" 섹션에 사용자 손으로 해야 할 것 명시 (실제 사용자 환경 스모크 1회 등). 없으면 "(없음)".
4. **`graph-refresh-checker` 호출 + 판정 기반 처리** — 코드 변경이 1줄이라도 있으면 예외 없이 실행. 판정별 필수 후속:
   - `fresh` → 후속 없음. 보고서 "graph_refresh" 섹션에 `fresh` 기록.
   - `partial-stale` → 해당 scope 만 `/graphify <대상경로>` 재생성. `docs/graph/index.md` frontmatter + Scopes 표 갱신.
   - `fully-stale` → 영향 scope 전체 `/graphify` 재생성. 메타 갱신.
   - `no-graph` → 코드베이스가 비어있지 않다면 **세션 내에서 최초 생성**. `/graphify <주요 경로>` 실행 + 메타 작성.
   판정 결과와 수행한 처리는 보고서 "graph_refresh" 섹션에 한 줄 기록 (예: `partial-stale → src scope 재생성 완료`). graphify 가 도입되지 않은 프로젝트에선 이 단계 전체를 "skip: no-graphify" 로 기록.
5. **`git status` 확인** — 미커밋 잔여(tracked 변경·untracked 파일) 가 있으면 (1) 이번 작업 단위에 속하면 프로젝트의 커밋 정책(CLAUDE.md) 에 따라 커밋/push, (2) 속하지 않으면 `report.md` 의 `open_items` 에 파일 경로·상태를 명시. 커밋되지 않은 잔여를 남긴 채 retrospective 로 넘어가지 않는다.

그 외:
- **retro 호출 전 orchestrator 가 `user_signals` 기록**: 세션 중 사용자 발화에서 감지한 부정 시그널("왜 안 했어?", "또야?", "틀렸어") 과 긍정 시그널("좋더라", "그거 맞아", 한 번 만에 수락) 을 `report.md` 의 `user_signals.{positive|negative}` 에 한 줄씩 인용·요약. 구조적 허점이면 `negative[*].structural: true`. 한쪽이 없으면 빈 리스트.
- 모든 advisor 산출이 수렴 + verification pass 면 retrospective-advisor 호출 (기록된 `user_signals` 를 입력으로). **호출 전 전제**: `report.md` 의 `Summary` / `Invocations` / `Decisions` 세 섹션이 최소 1줄 이상 채워져 있어야 함. 빈 Summary 로 회고를 돌리면 입력 품질이 무너진다.
- 회고 결과의 `memory_candidates` 검토 후 orchestrator 가 수용 여부 결정 → 수용 시 memory 갱신. `signal_source: negative` 뿐 아니라 `positive` 후보도 동등하게 검토 (비자명한 판단이 검증된 경우). 수용한 candidate 에 `docs_sync_target` 이 지정되어 있으면 해당 경로(`CLAUDE.md` / `docs/development/*.md` / ADR 등) 에도 **같은 커밋에** 반영한다.
- `report.md` 에 `ended_at` 기록
- feedback slug 로 진입했다면 해당 항목을 `archive/` 로 이동 + frontmatter `status: done`, `resolved_at`, `resolved_commit`, `work_log` 갱신
- 커밋/push 는 프로젝트 커밋 정책에 따라 작업 단위 끝에서 진행

## system-reminder 수신 시 행동 원칙

- `system-reminder` 수신 시 진행 중인 툴 호출·응답 준비를 완료한 뒤 reminder 내용을 반영한다. 상세 규약: `agent-team-protocol.md` §2.4.
- reminder 가 작업 전제 자체를 뒤집는 경우에만 `AskUserQuestion` 으로 사용자에게 명시적으로 알리고 합의 후 방향을 전환한다.

## 명시적 비활성 경로

사용자가 세션 도중 "팀 거치지 말고 직접 해", "advisor 없이", "간단히" 같은 지시를 내리면 orchestrator 는 advisor 호출을 스킵하고 직접 처리한다. `/task` 로 진입했더라도 예외 모드로 전환 가능.

## 금지

- `/task` 를 부르지 않았는데 팀 모드로 진입하는 것 (자동 적용 아님)
- 프로토콜 문서를 읽지 않고 팀 작업 시작
- `.claude/work-session/` 디렉토리 없이 보고서 누적

## 관련

- [docs/development/agent-team-protocol.md](../../../docs/development/agent-team-protocol.md)
- [docs/development/verification-strategies.md](../../../docs/development/verification-strategies.md)
