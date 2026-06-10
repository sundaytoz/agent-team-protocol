# Agent Team Protocol

Claude Code / Codex / Gemini CLI 세션을 **Orchestrator + Advisor + Worker 3-tier 에이전트 팀** 으로 운영하기 위한 플러그인. `/atp:task` 로 명시 호출할 때만 팀 모드에 진입하고, 작은 작업은 메인 에이전트가 직접 처리한다.

## 지원 플랫폼

| 플랫폼 | 상태 | 호출 | 지침파일 | 검증 수준 |
|---|---|---|---|---|
| Claude Code | ✅ 지원 | `/atp:task` | `CLAUDE.md` | reference 구현 — 상시 사용 검증 |
| Codex CLI | ✅ 지원 | `$atp:task` (단축형 `$task`) | `AGENTS.md` | 설치·skill 노출·호출·본문 로드 실측 (2026-06-10, codex-cli 0.138.0). subagent spawn 은 공식 문서 근거(cited) — 팀 모드 E2E 스모크 권장 |
| Gemini CLI | 🚧 계획 | `/atp:task` (예정, TODO:실측) | `GEMINI.md` | 문서 근거 설계 완료(Tier A-flat) — 배포 산출물 미생성 |

플랫폼 capability tier, 미실측 마커, 호출 문법의 정본은 [docs/development/platform-adapters.md](docs/development/platform-adapters.md) 다.

---

## 1. 왜 이 플러그인인가

Claude Code / Codex / Gemini CLI 를 단일 에이전트로 모든 작업을 시키면 세 가지 문제가 발생한다.

- **컨텍스트 오염**: 구현 다음 검증까지 같은 세션에서 하면, 에이전트가 자기가 쓴 코드에 합리화해 판정이 편향된다.
- **모델 비용 불균형**: 단순 조사에도 최상위 모델이 돌아가거나, 설계 단계에 작은 모델이 쓰여 품질이 무너진다.
- **파일 경합**: 병렬화하면 같은 파일을 두 번 쓰거나 의존 순서를 깨뜨린다.

이 플러그인은 위를 구조로 해결한다.

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

## 3. 설치

자세한 초기화 절차와 스모크 테스트는 [docs/usage/setup-checklist.md](docs/usage/setup-checklist.md) 를 따른다. 핵심 명령만 요약하면 다음과 같다.

```bash
/plugin marketplace add sundaytoz/agent-team-protocol
/plugin install atp@agent-team-protocol
/atp:init
```

Codex CLI 에서는 `codex plugin marketplace add <repo>` 와 `codex plugin add atp@agent-team-protocol` 을 사용한다.

graphify 지식 그래프 기능은 옵트인 add-on 이다.

```bash
/plugin install atp-graphify@agent-team-protocol
```

---

## 4. 레이아웃

상세 파일 맵과 런타임 산출물 경계는 [docs/architecture/file-map.md](docs/architecture/file-map.md) 가 정본이다.

```
agent-team-protocol/                      (레포 = 마켓플레이스 agent-team-protocol = base 플러그인 atp)
├── .claude-plugin/                       (Claude Code manifest)
├── .codex-plugin/                        (Codex plugin manifest; marketplace 정본은 .agents/plugins/)
├── .agents/plugins/marketplace.json      (Codex marketplace 정본 — 객체형 source: atp→./plugins/atp, atp-graphify→./addons/graphify)
├── plugins/atp -> ..                     (interim symlink — Codex base source. 비정본·root 우회. plugins/README.md 경고 참조)
├── agents/                               (base 에이전트 10개)
├── skills/                               (/atp:task, /atp:init)
├── docs/                                 (번들 레퍼런스 — agent 가 ${CLAUDE_PLUGIN_ROOT}/docs/... 로 Read)
│   ├── index.md
│   ├── usage/
│   ├── development/
│   ├── architecture/
│   └── adr/
├── templates/                            (/atp:init 스캐폴딩 원본)
└── addons/graphify/                      (옵트인 add-on 플러그인 atp-graphify)
```

---

## 5. self-dogfooding (이 레포 자체에서 `task` 스킬 사용)

이 레포 자체에서 작업할 때는 먼저 로컬 플러그인을 enable 해야 한다. 플랫폼별 self-dogfooding 명령은 [AGENTS.md](AGENTS.md) 와 [CLAUDE.md](CLAUDE.md) 의 "에이전트 팀 운영" 절을 따른다.

---

## 6. 더 읽기

| 주제 | 문서 | 참조 섹션 |
|---|---|---|
| 운영 프로토콜 권위 레퍼런스 | [docs/development/agent-team-protocol.md](docs/development/agent-team-protocol.md) | §1 역할 · §2 호출 모델 · §4 충돌 조정 · §5 모델 선택 · §6 파괴적 조작 게이트 · §7 재개 규약 · §8 보고서 스키마 · §9 확장 트리거 · §11 peer_agents · §12 회고 |
| 에이전트 카탈로그 (base 10 + add-on 3) | [docs/development/agent-catalog.md](docs/development/agent-catalog.md) | Tier 2 / Tier 3 / Worker |
| 구성 파일 맵 (트리) | [docs/architecture/file-map.md](docs/architecture/file-map.md) | 런타임 생성 디렉토리 포함 |
| 탐색 도구 선택 매트릭스 | [docs/development/search-tool-matrix.md](docs/development/search-tool-matrix.md) | LSP/graphify/Grep/Glob/Read/WebFetch |
| graphify add-on 설치·통합 | [addons/graphify/docs/graphify-usage.md](addons/graphify/docs/graphify-usage.md) | 설치·에이전트 동작 |
| 초기화 스킬 | [skills/init/SKILL.md](skills/init/SKILL.md) | 멱등 생성 계약 |
| 작업 진입 스킬 | [skills/task/SKILL.md](skills/task/SKILL.md) | 호출 방식 |
| 문제 해결 / FAQ | [docs/usage/faq.md](docs/usage/faq.md) | 설치·init·graphify 트러블슈팅 |

---

## 7. Credits

Originally created by 이정수 (WEMADE PLAY, DevOps). See [AUTHORS](AUTHORS) for details.

## 8. Security

보안 보고 채널은 [SECURITY.md](SECURITY.md) 참조.

## 9. License

Released under the MIT License — see [LICENSE](LICENSE).

## 10. 변경 / 백로그 / 기여

템플릿 자체의 개선 백로그·이력은 [TEMPLATE_DEV.md](TEMPLATE_DEV.md). 되돌리기 어려운 결정은 [docs/adr/](docs/adr/index.md).
