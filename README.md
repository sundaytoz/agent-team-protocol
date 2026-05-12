# Claude Code Agent Team — Generic Template

Claude Code 세션을 **Orchestrator + Advisor + Worker 3-tier 에이전트 팀** 으로 운영하기 위한 프로젝트 중립 템플릿. `/task` 스킬로 명시 호출할 때만 팀 모드에 진입하고, 작은 작업은 메인 에이전트가 직접 처리한다.

---

## 1. 왜 이 템플릿인가

Claude Code 를 단일 에이전트로 모든 작업을 시키면 세 가지 문제가 발생한다.

- **컨텍스트 오염**: 구현 다음 검증까지 같은 세션에서 하면, 에이전트가 자기가 쓴 코드에 합리화해 판정이 편향된다.
- **모델 비용 불균형**: 단순 조사에도 최상위 모델이 돌아가거나, 설계 단계에 작은 모델이 쓰여 품질이 무너진다.
- **파일 경합**: 병렬화하면 같은 파일을 두 번 쓰거나 의존 순서를 깨뜨린다.

이 템플릿은 위를 구조로 해결한다.

| 문제 | 해법 |
|---|---|
| 컨텍스트 오염 | advisor 단위로 격리 — 특히 `verification-advisor` 는 **구현 코드·설계 문서 접근 금지** |
| 모델 비용 | orchestrator 가 호출 시점에 스케일 평가(`small`/`medium`/`large`) 후 `haiku`/`sonnet`/`opus` override |
| 파일 경합 | `implementation-advisor` 가 **파일 소유권 맵** 으로 1파일 1worker 보장 + 의존 있는 건 순차 |

---

## 2. 개념 — 3-tier 역할 분리

```
Orchestrator  ← 사용자 유일 창구. 직접 작업 금지. 위임·중재·보고만.
    │
    ├── Tier-2 Advisor   ← 단일 invocation 완결 (requirements / design / verification / documentation …)
    │
    └── Tier-3 Advisor   ← 내부에서 Worker 병렬 spawn (research / implementation)
          ├── Worker A ─┐
          ├── Worker B ─┼── advisor 가 취합 후 반환
          └── Worker C ─┘
```

**불변식** — Tier-3 advisor 만 `Agent` 툴을 보유(재귀 방지). Advisor 호출당 Worker 최대 6개 동시 spawn. Orchestrator 가 상위 advisor 여러 개를 동시 호출하는 것은 기본 금지. 상세는 [docs/development/agent-team-protocol.md](docs/development/agent-team-protocol.md) §1~§2.

---

## 3. 설치 (cp-R 5분)

### 3.1 복사

```bash
# 1) 템플릿 받기 (한 번만)
git clone git@github.com:sundaytoz/agent-team-protocol.git ~/work/agent-team-protocol
TEMPLATE=~/work/agent-team-protocol

# 2) 타깃 프로젝트로 이동
cd /path/to/your-project

# 3) 복사 — 아래 "복사 제외" 목록은 복사하지 않는다
cp -R "$TEMPLATE/.claude" .
cp -R "$TEMPLATE/docs" .
cp "$TEMPLATE/CLAUDE.md" .         # 이미 있다면 병합 (아래 §3.2)

# 4) 템플릿 레포의 세션 임시 산출물이 우발 복사됐다면 제거
#    (`.gitignore` 는 `cp -R` 중엔 존중되지 않는다)
rm -rf .claude/work-session
```

**복사 제외 (이식하지 않는다)** — 템플릿 리포 자체의 메타 파일. 신규 프로젝트에 섞이면 안 된다.

- `README.md` — 프로젝트 고유 README 를 덮지 않도록 제외.
- `TEMPLATE_DEV.md` — 템플릿 자체의 개선 백로그·이력. 사용자 프로젝트와 무관.
- `SECURITY.md` — 본 템플릿 리포의 보안 채널. 이식자는 자기 프로젝트의 보안 정책을 독자 작성.
- `AUTHORS` — 본 템플릿의 원작자 표기. 이식자는 자기 프로젝트의 AUTHORS 를 독자 작성.
- `LICENSE` — 본 템플릿의 라이선스. 이식자는 자기 프로젝트의 라이선스를 독자 결정·배치.
- `.claude/work-session/` — 템플릿 레포의 과거 세션 임시 산출물. 반드시 4) 단계로 제거.
- `docs/feedback/archive/` — 템플릿에서 해소된 feedback 이력. 이식자와 무관.

### 3.2 `CLAUDE.md` 병합

프로젝트에 이미 `CLAUDE.md` 가 있으면 본 템플릿의 "에이전트 팀 운영" 섹션 + "문서화 정책" 섹션만 추가한다. 기술 스택 표·커맨드 표는 프로젝트 고유 내용으로 채운다.

### 3.3 `.gitignore` 갱신

```gitignore
# Claude Code agent team session artifacts
.claude/work-session/
```

`docs/graph/.gitignore` 는 템플릿에 이미 포함 — 그래프 본체만 무시하고 `index.md` 는 커밋한다.

### 3.4 검증

새 Claude Code 세션에서 `/task 안녕, 에이전트 팀이 로드됐는지 확인만 해줘`. orchestrator 가 `docs/development/agent-team-protocol.md` 를 읽고 `.claude/work-session/<sid>/` 를 생성하면 성공.

---

## 4. 프로젝트 적응 (3군데)

템플릿은 언어·프레임워크 중립이다. 이식 후 **30분 내** 아래 3군데만 손보면 된다. 체크리스트는 [docs/usage/setup-checklist.md](docs/usage/setup-checklist.md).

| # | 대상 | 무엇을 |
|---|---|---|
| 1 | `docs/development/verification-strategies.md` | YAML `cmd` 를 프로젝트 실제 명령으로 교체 (L1 typecheck / L1 unit / L2 contract / verify-all) |
| 2 | `docs/development/document-category-classification.md` + `docs/index.md` | 해당 없는 카테고리 행 삭제, 필요한 카테고리 행 추가 (예: 웹 UI → `uiux-qa-report/`) |
| 3 | `.claude/agents/code-writer.md` / `migration-writer.md` | `code-writer` 는 `CLAUDE.md` 의 코딩 규칙 링크. `migration-writer` 는 프로젝트 ORM 명령(Drizzle/Alembic/EF/Flyway/Prisma)으로 절차 구체화 |

(선택) graphify 도입은 [docs/development/graphify-usage.md](docs/development/graphify-usage.md) 9 단계를 참조. 미도입 시 `graphify-*` 에이전트는 세션 종료 시 "skip: no-graphify" 로 기록되고 자동으로 건너뛴다.

---

## 5. 더 읽기

| 주제 | 문서 | 참조 섹션 |
|---|---|---|
| 운영 프로토콜 권위 레퍼런스 | [docs/development/agent-team-protocol.md](docs/development/agent-team-protocol.md) | §1 역할 · §2 호출 모델 · §4 충돌 조정 · §5 모델 선택 · §6 파괴적 조작 게이트 · §7 재개 규약 · §8 보고서 스키마 · §9 확장 트리거 · §11 peer_agents · §12 회고 |
| 에이전트 13개 카탈로그 | [docs/development/agent-catalog.md](docs/development/agent-catalog.md) | Tier 2 / Tier 3 / Worker |
| 구성 파일 맵 (트리) | [docs/architecture/file-map.md](docs/architecture/file-map.md) | 런타임 생성 디렉토리 포함 |
| 검증 전략 레지스트리 | [docs/development/verification-strategies.md](docs/development/verification-strategies.md) | L1/L2/L3 |
| graphify 설치·통합 | [docs/development/graphify-usage.md](docs/development/graphify-usage.md) | 9 단계 |
| 탐색 도구 선택 매트릭스 | [docs/development/search-tool-matrix.md](docs/development/search-tool-matrix.md) | LSP/graphify/Grep/Glob/Read/WebFetch |
| 이식 후 30분 설정 | [docs/usage/setup-checklist.md](docs/usage/setup-checklist.md) | 0~7 단계 |
| 문제 해결 / FAQ / 이식 실수 카탈로그 | [docs/usage/faq.md](docs/usage/faq.md) | FAQ + M1~M8 |
| `/task` 진입 스킬 | [.claude/skills/task/SKILL.md](.claude/skills/task/SKILL.md) | 호출 방식 |

---

## 6. Credits

Originally created by 이정수 (WEMADE PLAY, DevOps). Ported to `sundaytoz` organization — see [AUTHORS](AUTHORS) for details.

## 7. Security

본 템플릿 리포의 보안 보고 채널은 [SECURITY.md](SECURITY.md) 참조. 이식 프로젝트는 자기 보안 정책을 독자 작성한다 (cp-R 복사 제외).

## 8. License

Released under the MIT License — see [LICENSE](LICENSE).

## 9. 변경 / 백로그 / 기여

템플릿 자체의 개선 백로그·이력은 [TEMPLATE_DEV.md](TEMPLATE_DEV.md). 되돌리기 어려운 결정은 [docs/adr/](docs/adr/index.md).
