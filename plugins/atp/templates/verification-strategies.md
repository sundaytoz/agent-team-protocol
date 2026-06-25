# Verification Strategies Registry

`verification-advisor` 가 읽는 단일 레지스트리. 이 파일에 등록된 전략만 검증 대상이 된다. 전략 추가/수정 시 이 파일만 변경하면 에이전트 구조(tier) 는 건드릴 필요 없다.

## 검증 사다리 (L1 / L2 / L3)

프로젝트의 검증은 3단으로 나뉜다. 코드 변경의 성격에 따라 **적용할 최소 L 레벨** 이 결정된다.

| 레벨 | 대상 | 신뢰 범위 |
|---|---|---|
| **L1** | 단위·회귀 (타입체크 + 단위/회귀 테스트) | "내가 고친 라인이 깨지지 않음" + "과거 버그가 재발하지 않음" |
| **L2** | 원격/외부 의존 계약 (live contract 테스트) | "외부 서비스 스키마·필드가 우리 기대와 정합" |
| **L3** | End-to-end (실제 런타임·DB·외부 서비스 전부 도는 시나리오) | "사용자 시나리오가 실제 스택에서 끝까지 동작" |

### 버그 범주 → 적용 L 레벨 (예시 · 프로젝트 맞춤)

프로젝트 특성에 맞게 아래 표를 채운다.

| 버그/변경 범주 | 의무 레벨 |
|---|---|
| 외부 API 스키마/응답 파싱 수정 | L1 + L2 |
| 외부 서비스 설정 상수 변경 | L1 + L2 |
| 인증/인가/롤 플로우 수정 | L1 + L2 + L3 |
| 순수 도메인 로직 (외부 의존 없음) | L1 |
| 인프라 설정 (container/env/compose) | L1 + 수동 스모크 |

**회귀 테스트 의무**: 버그 수정 커밋은 해당 버그를 재현하는 테스트를 같이 포함한다. revert 시 테스트가 실패하고, 수정 후엔 통과해야 한다.

### 실행 수단

프로젝트 루트에 통합 검증 스크립트를 둘 것을 권장한다 (예: `scripts/verify.sh`, `make verify`, `cargo xtask verify`). 스크립트는 L1 → L2 → 로그 스캔 순차 실행을 담당.

- L2 를 조건부로 비활성화하는 환경 변수를 제공 (원격 꺼진 CI 대비). 예: `SKIP_LIVE_CONTRACT=1`.
- 원격 테스트의 seed/live URL 미지정 시 L2 는 자동 skip 처리되도록 구성.

## 사용 규약

- `verification-advisor` 는 호출 시 변경 scope 를 받아 매칭되는 전략만 실행한다.
- 전략 개수에 따라 tier 가 자동 결정된다:
  - 1개 → advisor 가 직접 실행 (tier 2)
  - 2개 이상 → `worker:` 필드가 있는 전략은 해당 worker spawn (tier 3), 나머지는 advisor 순차 실행
- 신규 worker 도입은 [agent-team-protocol.md §9](./agent-team-protocol.md) 의 확장 트리거 참조.

### 집합 전수 AC 실행 지침

design.md 의 "검증 포인트" 에 다음 형식의 AC 가 있으면 "집합 전수 체크" 유형으로 분류한다.

```
AC-N: <집합명> 전수 N건 ... (grep -c ... == N)
```

실행 방법:

1. AC 에 명시된 `grep -c` 명령을 그대로 실행한다.
2. 반환값이 AC 에 명시된 기대 수와 다르면 **blocker FAIL** 로 판정한다.
3. 실패 시 출력: 실제 매치 수 + 누락된 항목을 diff 또는 목록으로 제시.

집합 전수 AC 는 특성상 "부분 통과"가 없다 — 기대 수에서 1 이라도 어긋나면 전체 FAIL. 규약 근거는 프로토콜 §4.3 + `design-advisor.md` "집합 전수 체크 AC 패턴" 섹션.

## 전략 (템플릿)

아래는 YAML 스켈레톤이다. 프로젝트 기술 스택에 맞게 `cmd` 를 교체한다 (`pnpm` / `yarn` / `npm` / `cargo` / `go test` / `pytest` / `mvn test` 등).

```yaml
strategies:
  # ── L1 ────────────────────────────────────────
  - id: typecheck
    cmd: <프로젝트 타입체크 명령>       # e.g. pnpm typecheck / cargo check / mypy .
    scope: all
    timeout_s: 180
    failure_severity: blocker

  - id: unit
    cmd: <프로젝트 단위 테스트 명령>    # e.g. pnpm test / cargo test / pytest
    scope: <src glob>                   # e.g. src/**
    timeout_s: 600
    failure_severity: blocker

  # ── L2 ────────────────────────────────────────
  - id: contract-<external>
    cmd: <계약 테스트 명령>
    scope:
      - <외부 의존이 집중된 경로>
    timeout_s: 60
    failure_severity: blocker
    preconditions:
      - "<외부 서비스 기동 확인 방법>"
      - "<필요 환경 변수>"
    note: |
      원격 미기동 또는 seed 미지정 시 runtime 에서 skip 처리.
      blocker 로 두는 이유는 "원격이 떠 있는데 계약 위반" 이 사용자 장애로 직결되기 때문.

  # ── 통합 ──────────────────────────────────────
  - id: verify-all
    cmd: <통합 검증 스크립트>           # e.g. pnpm verify / make verify
    scope: all
    timeout_s: 900
    failure_severity: blocker
    note: "L1 + L2 + 로그 스캔 통합. ATP task 세션 종료 전 의무."
```

## 필드 정의

| 필드 | 의미 |
|---|---|
| `id` | 전략 식별자 (unique) |
| `cmd` | 실행 명령 |
| `scope` | glob. 이 패턴에 변경이 걸칠 때만 실행 |
| `timeout_s` | 초 단위 타임아웃 |
| `failure_severity` | `blocker` (실패 시 전체 검증 실패) \| `warning` (기록만) |
| `worker` (optional) | spawn 할 worker 이름. 미지정 시 advisor 직접 실행 |

## 호스트 어댑터 스모크 패턴 (재사용형)

신규 호스트 어댑터 추가 시 적용하는 검증 패턴. opencode 어댑터 정식 스모크(2026-06-24, L1 15/15 + L2 7/7 PASS)를 예시로 등록한다.

### 격리 가드

실제 전역 설정이 오염되지 않도록 **HOME-override 격리**를 반드시 적용한다.

```bash
T_HOME=$(mktemp -d)   # 임시 HOME — 실제 ~/.config/opencode 무수정
T_DIR=$(mktemp -d)    # 설치 대상 임시 디렉토리
```

전역 스코프 테스트: `HOME=$T_HOME node cli.js install --global`.
프로젝트 스코프 테스트: `cd $T_DIR && node cli.js install --project`.
종료 시 `rm -rf $T_HOME $T_DIR`.

### L1 — generator 단위 / 정적 검증

| 검증 항목 | 명령 / 기대 |
|---|---|
| 에이전트 개수 동등 | `ls agents/atp-*.md \| wc -l` vs source 파일 수 — 동등 |
| `--with-graphify` 개수 동등 | base(10) + graphify(3) = 13 |
| mode: subagent 전수 | `grep -L '^mode: subagent' agents/atp-*.md` → 빈 목록 |
| task: deny 전수 | `grep -L 'task: deny' agents/atp-*.md` → 빈 목록 |
| bash:deny 정확 4파일 | `grep -l 'bash:.*deny' agents/atp-*.md` → 4개(design/documentation/code-writer/retrospective) |
| 경로변수 잔류 0 | `grep -rl 'CLAUDE_PLUGIN_ROOT\|CLAUDE_PROJECT_DIR' agents/ commands/` → 빈 목록 |
| write 키 양키 | atp-code-writer 및 atp-migration-writer frontmatter에 `edit: allow` + `write: allow` 동시 존재 |
| 기본 모델 bake 0 | `grep -rl '^model:' agents/` → 빈 목록(기본 install) |
| provider bake 존재 | `--provider <name>` install 후 `grep -rl '^model:' agents/` → 비어있지 않음 |
| uninstall 잔여 0 | uninstall 후 `ls agents/ commands/ atp/` → 모두 없음 / exit 0 |
| 멱등 재install | 2회 install 후 md5 비교 동일 |

### L2 — 호스트 런타임 검증 (opencode 예시)

| 검증 항목 | 명령 / 기대 |
|---|---|
| command 로드·ProviderModelNotFoundError 0 | `opencode run --command atp-task "로드 확인만..."` → exit 0, 오류 없음 |
| agent list 파싱 | `opencode agent list` → atp-* 10개, 에러 0 |
| fan-out + 재귀차단 | design-advisor spawn 성공 + design-advisor 내부 재-spawn 없음(task:deny 집행) |
| worker write 실동작 | atp-code-writer spawn → 파일 write 성공(프로젝트 디렉토리 내) |
| worker bash 거부 | atp-code-writer bash 실행 시도 → "bash 도구 없음" 거부 |
| @ref 경로 read | `@.opencode/atp/docs/development/agent-team-protocol.md` Read → `# Agent Team Protocol` H1 |
| 양 scope(global+project) | HOME-override 전역 install + `opencode agent list` 10개 + smoke exit 0 |

### YAML 전략 등록 예시

```yaml
strategies:
  # ── 호스트 어댑터 L1 ────────────────────────────────────────
  - id: host-adapter-static
    cmd: node adapters/<host>/bin/cli.js install --project && <검증 명령 모음>
    scope: adapters/<host>/**
    timeout_s: 120
    failure_severity: blocker
    note: |
      generator 단위 정적 검증. 호스트 CLI 불요.
      개수동등·permission grep·uninstall 잔여0 포함.

  # ── 호스트 어댑터 L2 ────────────────────────────────────────
  - id: host-adapter-runtime
    cmd: <호스트 runtime smoke 명령>
    scope: adapters/<host>/**
    timeout_s: 300
    failure_severity: blocker
    preconditions:
      - "<호스트 CLI 설치 확인>"
      - "HOME-override 격리 변수 설정"
    note: |
      호스트 런타임 실동작 검증(command load, agent list, fan-out, bash 거부, @ref read, 양 scope).
      HOME-override 격리 필수 — 실제 전역 설정 무수정 보장.
      신규 호스트 게이트: 이 L2 전건 PASS 전 platform-adapters.md 활성 규칙 등재 금지.
```

## 확장 시

- 새 전략 추가: 위 YAML 블록에 항목 추가.
- Worker 분리가 필요한 수준에 도달 (브라우저 테스트, 장시간 E2E 등): `worker:` 필드 붙이고 해당 worker 파일 신설 + `verification-advisor.md` 의 tools 에 `Agent` 추가.
- 기준은 [agent-team-protocol.md §9 확장 트리거 레지스트리](./agent-team-protocol.md#9-확장-트리거-레지스트리).
