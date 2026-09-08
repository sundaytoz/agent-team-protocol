# agent-team-protocol (플러그인 소스 레포)

이 레포는 Claude Code/Codex 플러그인 **`atp`** (base), **`atp-graphify`** (옵트인 add-on), **`atp-codex-hooks`** (Codex 팀 실행용 옵트인 add-on)의 소스다. 마켓플레이스명은 레포명과 같은 `agent-team-protocol`.

> 소비 프로젝트의 CLAUDE.md 에 삽입되는 안내 블록·placeholder 템플릿은 `plugins/atp/templates/` 와 `plugins/atp/skills/init/SKILL.md` 에 있다. 이 파일(레포 루트 CLAUDE.md)은 **이 레포 자체를 개발하는 기여자용** 가이드다.

---

## 레포 구조

```
agent-team-protocol/
├── .claude-plugin/marketplace.json   (Claude Code marketplace 정본)
├── .codex-plugin/marketplace.json    (Claude 미러 — Codex 는 읽지 않음)
├── .agents/plugins/marketplace.json  (Codex marketplace 정본 — 객체형 source)
├── plugins/atp/             (base 플러그인 루트 — 설치 시 이 서브트리만 번들로 복사)
│   ├── .claude-plugin/ .codex-plugin/  (plugin.json — 현재 버전은 manifest 참조)
│   ├── agents/              (base 에이전트 10개)
│   ├── skills/task/, skills/init/  (base 스킬)
│   ├── docs/development/    (런타임 레퍼런스 — 에이전트가 ${CLAUDE_PLUGIN_ROOT}/docs/... 로 Read)
│   └── templates/           (/atp:init 스캐폴딩 원본)
├── plugins/atp-graphify/    (옵트인 add-on — graphify 에이전트 3개 + docs/graphify-usage.md)
├── plugins/atp-codex-hooks/ (Codex 옵트인 add-on — hook runner + 설치·trust 가이드)
└── docs/                    (사람용 문서 — 번들 제외: usage / development / architecture / adr)
```

---

## 문서화 정책 (docs-first)

어떤 작업이든 시작 전에 **`docs/index.md`** (사람용 docs-first 허브) 를 먼저 읽고, 관련 카테고리의 `index.md` → 구체 문서 순으로 탐색한 뒤 구현에 착수한다. 번들 런타임 레퍼런스는 `plugins/atp/docs/` 에 있다.

- 문서 작성/갱신 규칙: `plugins/atp/docs/development/documentation-guidelines.md`
- 카테고리 분류 기준 원본: `plugins/atp/templates/document-category-classification.md`

---

## 에이전트 팀 운영 (self-dogfooding)

이 레포 자체에서 `/atp:task` 로 작업하려면 **로컬 플러그인 enable 이 선행**되어야 한다. 미설치 상태에선 `${CLAUDE_PLUGIN_ROOT}` 가 치환되지 않아 에이전트가 레퍼런스 문서를 읽지 못한다.

```bash
# 이 레포 루트에서 한 번만
/plugin marketplace add ./
/plugin install atp@agent-team-protocol

# graphify 에이전트 검증 시 추가
/plugin install atp-graphify@agent-team-protocol
```

로컬 enable 후:

- 작업 진입: `/atp:task [요청]`
- 권위 레퍼런스: `plugins/atp/docs/development/agent-team-protocol.md`
- 에이전트 정의: `plugins/atp/agents/*.md` (base), `plugins/atp-graphify/agents/*.md` (add-on)

작은 작업은 메인 에이전트가 직접 처리한다. 3-tier 팀 모드는 `/atp:task` 명시 호출 시에만 진입한다.

Codex의 실제 팀 실행은 별도 `atp-codex-hooks` 설치·hook trust와 exact marker가 필요하다. Claude Code에는 이 add-on을 설치하지 않는다. Codex 안내는 [AGENTS.md](AGENTS.md), [add-on 가이드](plugins/atp-codex-hooks/docs/codex-hooks-usage.md), [단일 연결 스모크](docs/usage/codex-connection-smoke.md)를 따른다.

**에이전트 정의를 편집했으면 세션 종료 전에 그 에이전트를 1회 실호출한다.** 정의 파일은 실행되지 않는 산문이라 자기모순·미해소 참조가 정적 검토를 통과한다 — 실호출만이 새 규약이 실제로 적용되는지 보여준다. 비용은 거의 0이고, 세션 종료 조건이 이미 요구하는 호출(예: `graph-refresh-checker`)로 갈음되는 경우도 많다. 실증: 2026-07-30 세션에서 `graph-refresh-checker` 의 판정 키를 바꾼 뒤 종료 조건 호출이 그 규약을 실제로 적용해 오탐을 피하는 것을 확인했다.

> **캐비트 — 설치 캐시가 stale 하면 실호출은 거짓 PASS 다.** 이 규약은 호출이 **편집한 정의**를 태운다고 가정한다. 그런데 로컬 enable 은 `~/.claude/plugins/cache/agent-team-protocol/atp/<version>/` 의 스냅샷을 쓰므로, 같은 세션에서 소스를 편집하고 bump 까지 한 상태(= 캐시 version < 소스 version)에서 `atp:<agent>` 를 호출하면 **편집 전 정의**가 실행된다. 검증했다는 기록만 남고 실제로는 무관한 스펙을 검증한다.
>
> 판정: 캐시 version 과 `plugins/atp/.claude-plugin/plugin.json` 의 version 을 비교한다. 불일치면 실호출로 갈음하지 말고 아래 둘을 함께 한다.
>
> 1. **dry-run 대리검증** — 신 spec 본문을 프롬프트에 주입해 범용 에이전트로 1회 수행시키고, 자기모순·미해소 참조·판단 불가 지점을 보고하게 한다. 실증: 2026-08-04 세션에서 `parallel-explorer`/`research-advisor` 개정안을 이 방식으로 태워 실행상 결함 3건(파일명 규칙 부재·frontmatter 리터럴/placeholder 모호·"관계만 재서술 금지" 의 무관계 사각)을 검출하고 같은 커밋에 반영했다.
> 2. **실환경 검증을 `needs_user_verification` 으로 이월** — `/plugin update` 도달 후 그 에이전트를 1회 호출해 확인할 항목을 명시한다. dry-run 은 대리이지 대체가 아니다.

---

## 릴리스 — 배포 완결 의무

소비자에게 영향을 주는 변경(`plugins/atp/` 번들 = 에이전트·스킬·런타임 레퍼런스·템플릿)을 `main` 에 머지하는 작업은 **머지로 끝이 아니다**. `/plugin update` 는 manifest 버전 차이로만 갱신을 감지하므로, 버전 bump 이 `main` 에 도달하지 않으면 변경은 소비자에게 **무증상 미도달**한다.

따라서 user-facing feat 를 다룰 때는 **배포 완결까지를 같은 작업 단위로** 본다:

1. **배포 트리거 확인** — `docs/development/release-checklist.md` §0 (feat 머지 = release 완결 의무). docs-first 동선(§문서화 정책)에서 작업 시작·완료 시 이 §0 를 본다.
2. **bump → PR → `/plugin update` 도달** 까지가 완결. base atp manifest 4곳(release-checklist §4 invariant)을 동기 bump 한다.
3. **이월 금지** — bump 을 후속으로 미룰 때 평문 메모(커밋 메시지·TEMPLATE_DEV "잔여")로 남기면 잊힌다. 실증: `2.0.0→2.1.0`·`2.2.2→2.3.0` 모두 미bump 이월이 뒤늦게 release 로 해소됐다. 이월 시 추적 가능한 항목으로 격리하고 `release-pending` 표식을 붙여 다음 세션 진입 시 우선 확인한다.

상세 절차·검증 명령은 `docs/development/release-checklist.md` 를 따른다.

---

## 코딩 규칙

- agent/skill body 의 레퍼런스 Read 경로는 `${CLAUDE_PLUGIN_ROOT}/docs/...`, 편집형 Read 는 `${CLAUDE_PROJECT_DIR}/docs/...`, 산출물 Write 는 `${CLAUDE_PROJECT_DIR}/.atp/work-session/...` 규칙을 따른다.
- 번들 런타임 레퍼런스는 `plugins/atp/docs/` 에, 사람용 문서는 루트 `docs/` 에 둔다 — 두 트리를 섞지 않는다. 편집형(소비 프로젝트 생성) 원본은 `plugins/atp/templates/` 에 둔다.
- TEMPLATE_DEV.md 는 이 레포 자체의 개선 백로그·이력 전용 메타 파일로, 커밋 대상이다.
