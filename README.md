<p align="center">
  <a href="README.md">한국어</a> ·
  <a href="README.en.md">English</a>
</p>

# Agent Team Protocol

AI 코딩 작업을 역할 기반 에이전트 팀 흐름으로 운영하게 해주는 프로토콜/플러그인.

<p align="center">
  <a href="docs/usage/setup-checklist.md">설치</a> ·
  <a href="docs/index.md">문서</a> ·
  <a href="plugins/atp/docs/development/agent-team-protocol.md">프로토콜</a> ·
  <a href="docs/usage/faq.md">FAQ</a>
</p>

## 지원 플랫폼

| 플랫폼 | 상태 | 호출 | 지침파일 | 검증 수준 |
|---|---|---|---|---|
| Claude Code | ✅ 지원 | `/atp:task` | `CLAUDE.md` | reference 구현 — 상시 사용 검증 |
| Codex CLI | ✅ 지원 | `$atp:task` (단축형 `$task`) | `AGENTS.md` | 설치·skill 노출·호출·본문 로드 실측 (2026-06-10, codex-cli 0.138.0). subagent spawn 은 공식 문서 근거(cited) — 팀 모드 E2E 스모크 권장 |
| Gemini CLI | 🚧 계획 | `/atp:task` (예정, TODO:실측) | `GEMINI.md` | 문서 근거 설계 완료(Tier A-flat) — 배포 산출물 미생성 |

지원 플랫폼별 호출 문법, capability tier, 미실측 마커의 정본은 [plugins/atp/docs/development/platform-adapters.md](plugins/atp/docs/development/platform-adapters.md) 다.

---

## 1. 왜 이 플러그인인가

단일 에이전트에게 조사·설계·구현·검증을 모두 맡기면 세 가지 문제가 발생한다.

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

**불변식** — Tier-3 advisor 만 `Agent` 툴을 보유(재귀 방지). Advisor 호출당 Worker 최대 6개 동시 spawn. Orchestrator 가 상위 advisor 여러 개를 동시 호출하는 것은 기본 금지. 상세는 [plugins/atp/docs/development/agent-team-protocol.md](plugins/atp/docs/development/agent-team-protocol.md) §1~§2.

---

## 3. 설치

자세한 초기화 절차와 스모크 테스트는 [docs/usage/setup-checklist.md](docs/usage/setup-checklist.md) 를 따른다. 핵심 명령만 요약하면 다음과 같다.

```bash
/plugin marketplace add sundaytoz/agent-team-protocol
/plugin install atp@agent-team-protocol
/atp:init
```

플랫폼별 설치 명령과 호출 문법은 [지원 플랫폼](#지원-플랫폼) 표 및 [setup-checklist.md](docs/usage/setup-checklist.md) 를 따른다.

graphify 지식 그래프 기능은 옵트인 add-on 이다.

```bash
/plugin install atp-graphify@agent-team-protocol
```

---

## 4. 레이아웃

상세 파일 맵과 런타임 산출물 경계는 [docs/architecture/file-map.md](docs/architecture/file-map.md) 가 정본이다.

```
agent-team-protocol/                      (레포 = 마켓플레이스 agent-team-protocol)
├── .claude-plugin/marketplace.json       (Claude Code marketplace 정본)
├── .codex-plugin/marketplace.json        (Claude 미러)
├── .agents/plugins/marketplace.json      (Codex marketplace 정본)
├── plugins/
│   ├── atp/                              (base 플러그인 루트 — 설치 시 이 서브트리만 번들)
│   │   ├── .claude-plugin/ .codex-plugin/  (plugin manifest)
│   │   ├── agents/                       (base 에이전트 10개)
│   │   ├── skills/                       (/atp:task, /atp:init)
│   │   ├── docs/development/             (런타임 레퍼런스 — agent 가 ${CLAUDE_PLUGIN_ROOT}/docs/... 로 Read)
│   │   └── templates/                    (/atp:init 스캐폴딩 원본)
│   └── atp-graphify/                     (옵트인 add-on 플러그인)
└── docs/                                 (사람용 문서 — 번들 제외: usage / development / architecture / adr)
```

---

## 5. self-dogfooding (이 레포 자체에서 `task` 스킬 사용)

이 레포 자체에서 작업할 때는 먼저 로컬 플러그인을 enable 해야 한다. self-dogfooding 절차는 [AGENTS.md](AGENTS.md) 와 [CLAUDE.md](CLAUDE.md) 의 "에이전트 팀 운영" 절을 따른다.

---

## 6. 더 읽기

| 주제 | 문서 | 참조 섹션 |
|---|---|---|
| 운영 프로토콜 권위 레퍼런스 | [plugins/atp/docs/development/agent-team-protocol.md](plugins/atp/docs/development/agent-team-protocol.md) | §1 역할 · §2 호출 모델 · §4 충돌 조정 · §5 모델 선택 · §6 파괴적 조작 게이트 · §7 재개 규약 · §8 보고서 스키마 · §9 확장 트리거 · §11 peer_agents · §12 회고 |
| 에이전트 카탈로그 (base 10 + add-on 3) | [plugins/atp/docs/development/agent-catalog.md](plugins/atp/docs/development/agent-catalog.md) | Tier 2 / Tier 3 / Worker |
| 구성 파일 맵 (트리) | [docs/architecture/file-map.md](docs/architecture/file-map.md) | 런타임 생성 디렉토리 포함 |
| 탐색 도구 선택 매트릭스 | [plugins/atp/docs/development/search-tool-matrix.md](plugins/atp/docs/development/search-tool-matrix.md) | LSP/graphify/Grep/Glob/Read/WebFetch |
| graphify add-on 설치·통합 | [plugins/atp-graphify/docs/graphify-usage.md](plugins/atp-graphify/docs/graphify-usage.md) | 설치·에이전트 동작 |
| 초기화 스킬 | [plugins/atp/skills/init/SKILL.md](plugins/atp/skills/init/SKILL.md) | 멱등 생성 계약 |
| 작업 진입 스킬 | [plugins/atp/skills/task/SKILL.md](plugins/atp/skills/task/SKILL.md) | 호출 방식 |
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
