# Agent Team Protocol

Claude Code / Codex / Gemini CLI 세션을 **Orchestrator + Advisor + Worker 3-tier 에이전트 팀** 으로 운영하기 위한 플러그인. `/atp:task` 로 명시 호출할 때만 팀 모드에 진입하고, 작은 작업은 메인 에이전트가 직접 처리한다.

## 지원 플랫폼

| 플랫폼 | 상태 | 호출 | 지침파일 | 검증 수준 |
|---|---|---|---|---|
| Claude Code | ✅ 지원 | `/atp:task` | `CLAUDE.md` | reference 구현 — 상시 사용 검증 |
| Codex CLI | ✅ 지원 | `$atp:task` | `AGENTS.md` | 설치·skill 노출·호출·본문 로드 실측 (2026-06-10, codex-cli 0.138.0). subagent spawn 은 공식 문서 근거(cited) — 팀 모드 E2E 스모크 권장 |
| Gemini CLI | 🚧 계획 | `/atp:task` (예정, TODO:실측) | `GEMINI.md` | 문서 근거 설계 완료(Tier A-flat) — 배포 산출물 미생성 |

Codex 테스트 완료 항목 (2026-06-10, codex-cli 0.138.0):

- [x] 마켓플레이스 등록 (`codex plugin marketplace add <repo>`) — `.agents/plugins/marketplace.json` 인식
- [x] 플러그인 설치 (`codex plugin add atp@agent-team-protocol`) — 버전드 cache (`~/.codex/plugins/cache/<marketplace>/<plugin>/<version>/`) 에 설치·enable
- [x] 번들 skill 노출 — `atp:task`/`atp:init` (`plugin:skill` 콜론 namespace)
- [x] 명시 호출 — `$atp:task` 멘션 인식 (Codex 가 "explicitly invoked" 로 응답, 단축형 `$task` 수용 여부는 미확인)
- [x] skill 본문(SKILL.md)·plugin.json 메타데이터 Read 동작 — 설치 버전 정확 보고
- [ ] 3-tier 팀 모드 E2E (subagent spawn 실동작) — 미실시

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

### 3.1 마켓플레이스 등록 (한 번만)

```bash
/plugin marketplace add sundaytoz/agent-team-protocol
```

### 3.2 base 플러그인 설치

```bash
/plugin install atp@agent-team-protocol
```

`atp` 는 Orchestrator + 10개 Advisor/Worker 에이전트 + `/atp:task` · `/atp:init` 스킬을 포함하는 base 플러그인이다.

### 3.3 graphify add-on 설치 (옵트인)

graphify 지식 그래프 기능이 필요한 경우에만 추가 설치한다.

```bash
/plugin install atp-graphify@agent-team-protocol
```

`atp-graphify` 는 graphify 관련 에이전트 3개(`graph-refresh-checker`, `graphify-lookup-advisor`, `graphify-update-advisor`)와 번들 사용 가이드를 포함한다. `atp` 를 선요구한다. 미설치 시 base 는 `skip: no-graphify` 로 정상 동작한다.

### 3.4 프로젝트 초기화

소비 프로젝트 루트에서 한 번 실행한다.

```bash
/atp:init
```

다음을 멱등 생성한다.

- `docs/` 골격 (index.md, 카테고리 index 14개, verification-strategies, document-category-classification, graph 골격)
- 플랫폼 지침파일에 `docs-first` + 호출 안내 블록 append (`<!-- atp:begin -->` 마커, 멱등):
  - `CLAUDE.md` 존재 시: `/atp:task` 안내 블록 삽입
  - `AGENTS.md` 존재 시: `$atp:task` 안내 블록 삽입 (verified-empirical)
  - `GEMINI.md` 존재 시: `/atp:task` 안내 블록 삽입 (TODO:실측 caveat 포함)
  - 지침파일 없으면 `CLAUDE.md` 기본 생성. `--all` 또는 `--platforms=` 로 3개 생성 가능.
- `.gitignore` 에 `.atp/work-session/` 라인 보장

초기화 후 `docs/development/verification-strategies.md` 의 `cmd` 값을 프로젝트 실제 명령으로 교체하면 준비 완료다.

### 3.5 검증 (스모크)

플랫폼별 입력:

- Claude Code: `/atp:task 안녕, 에이전트 팀이 로드됐는지 확인만 해줘`
- Codex: `$atp:task 안녕, 에이전트 팀이 로드됐는지 확인만 해줘` (`$` = skill 멘션 접두 — verified-empirical 2026-06-10)
- Gemini: `/atp:task 안녕, 에이전트 팀이 로드됐는지 확인만 해줘` (TODO:실측 — 배포형 확정 전)

orchestrator 가 프로토콜을 읽고 `.atp/work-session/<sid>/` 를 생성하면 성공.

---

## 4. 레이아웃

```
agent-team-protocol/                      (레포 = 마켓플레이스 agent-team-protocol = base 플러그인 atp)
├── .claude-plugin/                       (Claude Code manifest)
│   ├── plugin.json                       (name: atp)
│   └── marketplace.json                  (name: agent-team-protocol, plugins: [atp, atp-graphify])
├── .codex-plugin/                        (Codex plugin manifest; marketplace 정본은 .agents/plugins/)
│   ├── plugin.json                       (name: atp; skills: "./skills/")
│   └── marketplace.json                  (Claude 미러 — Codex 는 읽지 않음)
├── .agents/plugins/marketplace.json      (Codex marketplace 정본 — 객체형 source: atp→./plugins/atp, atp-graphify→./addons/graphify)
├── plugins/atp -> ..                     (interim symlink — Codex base source. 비정본·root 우회. plugins/README.md 경고 참조)
├── agents/                               (base 에이전트 10개)
├── skills/
│   ├── task/SKILL.md                     (/atp:task — 작업 진입)
│   └── init/SKILL.md                     (/atp:init — 초기화)
├── docs/                                 (번들 레퍼런스 — agent 가 ${CLAUDE_PLUGIN_ROOT}/docs/... 로 Read)
│   └── development/
│       ├── agent-team-protocol.md        (운영 프로토콜 권위 레퍼런스)
│       ├── agent-catalog.md              (에이전트 카탈로그)
│       ├── documentation-guidelines.md
│       ├── search-tool-matrix.md
│       └── index.md
├── templates/                            (/atp:init 스캐폴딩 원본)
└── addons/
    └── graphify/                         (옵트인 add-on 플러그인 atp-graphify)
        ├── .claude-plugin/plugin.json    (Claude Code manifest; name: atp-graphify, dependencies: ["atp"])
        ├── .codex-plugin/plugin.json     (Codex manifest mirror)
        ├── agents/                       (graphify 에이전트 3개)
        └── docs/graphify-usage.md
```

---

## 5. self-dogfooding (이 레포 자체에서 /atp:task 사용)

이 레포 자체에서 `/atp:task` 개발 작업을 진행하려면 플러그인이 로컬에서 enable 되어 있어야 `${CLAUDE_PLUGIN_ROOT}` 가 올바른 절대경로로 치환된다. 미설치 상태에서는 경로가 깨져 에이전트가 레퍼런스 문서를 읽지 못한다.

```bash
# 로컬 마켓플레이스를 project scope 로 등록
/plugin marketplace add ./

# base 설치
/plugin install atp@agent-team-protocol

# graphify 에이전트까지 검증이 필요한 경우
/plugin install atp-graphify@agent-team-protocol
```

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
