# agent-team-protocol (플러그인 소스 레포)

이 레포는 Claude Code / Codex 플러그인 **`atp`** (base) 와 **`atp-graphify`** (옵트인 add-on) 의 소스다. 마켓플레이스명은 레포명과 같은 `agent-team-protocol`.

> 소비 프로젝트의 AGENTS.md 에 삽입되는 안내 블록·placeholder 템플릿은 `plugins/atp/templates/` 와 `plugins/atp/skills/init/SKILL.md` 에 있다. 이 파일(레포 루트 AGENTS.md)은 **이 레포 자체를 개발하는 기여자용** 가이드다.

---

## 레포 구조

```
agent-team-protocol/
├── .claude-plugin/marketplace.json   (Claude Code marketplace 정본)
├── .codex-plugin/marketplace.json    (Claude 미러 — Codex 는 읽지 않음)
├── .agents/plugins/marketplace.json  (Codex marketplace 정본 — 객체형 source)
├── plugins/atp/             (base 플러그인 루트 — 설치 시 이 서브트리만 번들로 복사)
│   ├── .claude-plugin/ .codex-plugin/  (plugin.json — version 2.1.0)
│   ├── agents/              (base 에이전트 10개)
│   ├── skills/task/, skills/init/  (base 스킬)
│   ├── docs/development/    (런타임 레퍼런스 — 에이전트가 ${CLAUDE_PLUGIN_ROOT}/docs/... 로 Read)
│   └── templates/           (/atp:init 스캐폴딩 원본)
├── plugins/atp-graphify/    (옵트인 add-on — graphify 에이전트 3개 + docs/graphify-usage.md)
└── docs/                    (사람용 문서 — 번들 제외: usage / development / architecture / adr)
```

---

## 문서화 정책 (docs-first)

어떤 작업이든 시작 전에 **`docs/index.md`** (사람용 docs-first 허브) 를 먼저 읽고, 관련 카테고리의 `index.md` → 구체 문서 순으로 탐색한 뒤 구현에 착수한다. 번들 런타임 레퍼런스는 `plugins/atp/docs/` 에 있다.

- 문서 작성/갱신 규칙: `plugins/atp/docs/development/documentation-guidelines.md`
- 카테고리 분류 기준 원본: `plugins/atp/templates/document-category-classification.md`

---

## 에이전트 팀 운영 (self-dogfooding)

이 레포 자체에서 Codex 로 작업하려면 **로컬 플러그인 enable 이 선행**되어야 한다. 미설치 상태에선 `${CLAUDE_PLUGIN_ROOT}` 가 치환되지 않아 에이전트가 레퍼런스 문서를 읽지 못한다.

```bash
# 이 레포 루트에서 한 번만 (Codex, verified-empirical 2026-06-10 · codex-cli 0.138.0)
codex plugin marketplace add .
codex plugin add atp@agent-team-protocol

# graphify add-on 필요시
codex plugin add atp-graphify@agent-team-protocol
# 초기화는 세션에서 $init (skill id atp:init) 호출
```

로컬 enable 후:

- 작업 진입: `$atp:task [요청]` (`$` = Codex skill 멘션 접두, verified-empirical 2026-06-10)
- 권위 레퍼런스: `plugins/atp/docs/development/agent-team-protocol.md`
- 에이전트 정의: `plugins/atp/agents/*.md` (base), `plugins/atp-graphify/agents/*.md` (add-on)

작은 작업은 메인 에이전트가 직접 처리한다. 3-tier 팀 모드는 `$atp:task` 명시 호출 시에만 진입한다.

---

## 코딩 규칙

- agent/skill body 의 레퍼런스 Read 경로는 `${CLAUDE_PLUGIN_ROOT}/docs/...`, 편집형 Read 는 `${CLAUDE_PROJECT_DIR}/docs/...`, 산출물 Write 는 `${CLAUDE_PROJECT_DIR}/.atp/work-session/...` 규칙을 따른다.
- 번들 런타임 레퍼런스는 `plugins/atp/docs/` 에, 사람용 문서는 루트 `docs/` 에 둔다 — 두 트리를 섞지 않는다. 편집형(소비 프로젝트 생성) 원본은 `plugins/atp/templates/` 에 둔다.
- TEMPLATE_DEV.md 는 이 레포 자체의 개선 백로그·이력 전용 메타 파일로, 커밋 대상이다.
