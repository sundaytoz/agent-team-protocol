# agent-team-protocol (플러그인 소스 레포)

이 레포는 Claude Code / Codex 플러그인 **`atp`** (base) 와 **`atp-graphify`** (옵트인 add-on) 의 소스다. 마켓플레이스명은 레포명과 같은 `agent-team-protocol`.

> 소비 프로젝트의 AGENTS.md 에 삽입되는 안내 블록·placeholder 템플릿은 `templates/` 와 `skills/init/SKILL.md` 에 있다. 이 파일(레포 루트 AGENTS.md)은 **이 레포 자체를 개발하는 기여자용** 가이드다.

---

## 레포 구조

```
agent-team-protocol/
├── .claude-plugin/          (Claude Code base atp 매니페스트: plugin.json, marketplace.json)
├── .codex-plugin/           (Codex base atp 매니페스트 mirror: plugin.json, marketplace.json)
├── agents/                  (base 에이전트 10개)
├── skills/task/, skills/init/  (base 스킬)
├── docs/                    (번들 레퍼런스 — 에이전트가 ${CLAUDE_PLUGIN_ROOT}/docs/... 로 Read)
├── templates/               (/atp:init 스캐폴딩 원본)
└── addons/graphify/         (옵트인 add-on atp-graphify)
    ├── .claude-plugin/      (Claude Code add-on 매니페스트)
    ├── .codex-plugin/       (Codex add-on 매니페스트 mirror)
    ├── agents/              (graphify 에이전트 3개)
    └── docs/graphify-usage.md
```

---

## 문서화 정책 (docs-first)

어떤 작업이든 시작 전에 **`docs/index.md`** (번들 레퍼런스 허브) 를 먼저 읽고, 관련 카테고리의 `index.md` → 구체 문서 순으로 탐색한 뒤 구현에 착수한다.

- 문서 작성/갱신 규칙: `docs/development/documentation-guidelines.md`
- 카테고리 분류 기준: `docs/development/document-category-classification.md`

---

## 에이전트 팀 운영 (self-dogfooding)

이 레포 자체에서 Codex 로 작업하려면 **로컬 플러그인 enable 이 선행**되어야 한다. 미설치 상태에선 `${CLAUDE_PLUGIN_ROOT}` 가 치환되지 않아 에이전트가 레퍼런스 문서를 읽지 못한다.

```bash
# 이 레포 루트에서 한 번만 (Codex 설치 명령 — TODO:실측: namespace 확정 전)
$init

# graphify 에이전트 검증 시 추가
# (Codex 플러그인 번들 skill 의 정확한 호출 표기는 install 스모크로 확정 예정)
```

로컬 enable 후:

- 작업 진입: `$task [요청]` (TODO:실측 — `$task` vs `$atp-task` namespace 확정 전)
- 권위 레퍼런스: `docs/development/agent-team-protocol.md`
- 에이전트 정의: `agents/*.md` (base), `addons/graphify/agents/*.md` (add-on)

작은 작업은 메인 에이전트가 직접 처리한다. 3-tier 팀 모드는 `$task` 명시 호출 시에만 진입한다(TODO:실측).

---

## 코딩 규칙

- agent/skill body 의 레퍼런스 Read 경로는 `${CLAUDE_PLUGIN_ROOT}/docs/...`, 편집형 Read 는 `${CLAUDE_PROJECT_DIR}/docs/...`, 산출물 Write 는 `${CLAUDE_PROJECT_DIR}/.claude/work-session/...` 규칙을 따른다.
- docs/ 하위 번들 레퍼런스는 편집형 파일(verification-strategies 등)과 섞지 않는다. 편집형 원본은 `templates/` 에 둔다.
- TEMPLATE_DEV.md 는 이 레포 자체의 개선 백로그·이력 전용 메타 파일로, 커밋 대상이다.
