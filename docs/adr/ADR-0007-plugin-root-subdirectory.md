---
kind: adr
adr_number: "0007"
title: v2.0.0 — 플러그인 루트 서브디렉토리 전환 (plugins/atp/, plugins/atp-graphify/) + Gemini manifest 위치 확정
status: accepted
date: 2026-06-10
deciders:
  - template-maintainer
  - stzjungsoo
supersedes: []
related_commits:
  - 1e6fc79
  - feae019
  - bb75f21
  - 1b4a708
---

# ADR-0007: v2.0.0 — 플러그인 루트 서브디렉토리 전환 + Gemini manifest 위치 확정

## 상태

**Accepted** — 2026-06-10. ADR-0006(3-플랫폼 지원) 위에 적층. supersede 아님. repo 루트 = 플러그인 루트 구조에서 plugins/ 서브디렉토리 분리로 전환하는 구조 결정이다.

---

## 맥락

### 배경

ATP base 플러그인은 repo 루트가 곧 plugin root 였다 (`source: "./"` — Claude Code, Codex 에서 `plugins/atp -> ..` symlink 우회). 이 구조로 인해 install 시 인간 전용 문서(README 류, .en.md 4건, TEMPLATE_DEV.md, AUTHORS, SECURITY, ADR 문서 등 ~118KB, 번들의 약 51%)가 소비자 캐시로 복사됐다. 또한 `plugins/atp -> ..` symlink 는 Codex 정본 제약("source.path 는 marketplace root 내부")을 위반하고 Windows `core.symlinks=false` 환경에서 취약했다.

add-on `atp-graphify` 는 `addons/graphify/` 실디렉토리로 source 되어 symlink 문제는 없으나, base 와 위치 형식이 불일치했다.

### 사전 조사 결과 (research/summary.md)

- **P1**: Codex 서브디렉토리 source 는 symlink 없이 동작하며, claude-plugins-official 미러 다수가 `path:"plugins/<name>"` 패턴을 실등록. 현 symlink 는 타깃이 marketplace root 밖이라 비정본.
- **P3**: 런타임 직접필수 docs 는 `agent-team-protocol.md` 포함 `development/` 6건이 전부. 비-A docs 133KB(전체의 71%)는 즉시 제외 후보.
- **P4**: Gemini extension manifest 위치는 성문화 미비 — 서브디렉토리 전환 시 동시 확정 필요.

### 사용자 확정 결정 (OQ-1~OQ-5)

| ID | 결정 | 확정자 |
|---|---|---|
| OQ-1 | addons/graphify → plugins/atp-graphify/ 형제 이동 | 사용자 |
| OQ-2 | 버전 major 2.0.0 ("번들 파일 집합·캐시 레이아웃 변경 = breaking") | 사용자 |
| OQ-4 | Gemini extension manifest 위치: plugins/atp/ 하위로 성문화 | 사용자 |
| OQ-5 | 카테고리 index 4건 루트 잔류 + 번들 전용 경량 허브 2건 신규 (제3안) | design-advisor |

---

## 결정

### 결정 1 — 플러그인 루트를 서브디렉토리로 분리

**결정**: base 플러그인 `atp` 의 루트를 `plugins/atp/` 실디렉토리로, add-on `atp-graphify` 를 `plugins/atp-graphify/` 로 이동한다. repo 루트의 marketplace 매니페스트(`source`)만 새 경로를 가리키도록 수정한다. 인간 전용 문서는 repo 루트에 잔류한다.

```diff
# .claude-plugin/marketplace.json (동일 패턴을 .codex-plugin/marketplace.json 에 미러)
-  "version": "1.4.0",
+  "version": "2.0.0",
   { "name": "atp",
-    "source": "./",
+    "source": "./plugins/atp",
   { "name": "atp-graphify",
-    "source": "./addons/graphify"
+    "source": "./plugins/atp-graphify"
```

`plugins/atp -> ..` interim symlink 는 삭제한다. `.agents/plugins/marketplace.json`(Codex 정본)의 atp-graphify `path` 도 `./plugins/atp-graphify` 로 갱신한다. atp 의 Codex path 는 값이 불변(`./plugins/atp`)이었으므로 symlink 실디렉토리 전환만으로 정본화된다.

**동기**: (a) 인간 전용 문서 ~118KB(번들의 51%)가 소비자 캐시에서 제거됨. (b) symlink 비정본·Windows 취약성 해소. (c) TEMPLATE_DEV.md F-3PLAT-5 기등록 백로그 실현.

### 결정 2 — 번들 경계: docs 분할 (제3안)

**결정**: `plugins/atp/docs/` 에는 런타임 필수 development 5건(`agent-team-protocol.md`, `platform-adapters.md`, `agent-catalog.md`, `search-tool-matrix.md`, `documentation-guidelines.md`)과 번들 전용 경량 허브 2건(`docs/index.md`, `docs/development/index.md` 신규)만 포함한다. 루트 `docs/` 의 카테고리 index(usage/architecture/adr/development 풀본) 및 docs-first 허브는 전원 루트에 잔류한다.

번들 경량 허브는 development 6건만 가리키며 usage/architecture/adr/graphify 링크를 포함하지 않는다(캐시 자기완결). 번들 내 상대링크는 `plugins/atp/` 서브트리 밖을 참조하지 않는다.

**기각 대안**:
- **(가)** usage/architecture/adr index 번들 이동 + 가지치기: 루트 docs/index.md 카테고리 표 4링크 dangling, .en.md 선택자 파손.
- **(나)** docs/index.md 만 이동: README `docs/index.md` 링크·.en.md `./index.md` 선택자 dangling. 회피 시 루트 신규 = 제3안으로 수렴하면서 수정 파일 더 多.

### 결정 3 — 버전 2.0.0 (major) 정책

**결정**: atp 1.4.0 → 2.0.0, atp-graphify 1.2.0 → 2.0.0. major 의 의미는 "기능 파괴"가 아닌 "번들 파일 집합·캐시 레이아웃 구조 전환 시그널"이다.

atp 기존 설치 사용자는 `marketplace update` + `install` 재실행으로 새 캐시 레이아웃 수령. atp-graphify 기존 설치 사용자는 캐시 루트가 `addons/graphify` → `plugins/atp-graphify` 로 변경되므로 재설치 필요.

### 결정 4 — Gemini extension manifest 위치 성문화

**결정**: Gemini extension manifest(`gemini-extension.json` 예정)는 `plugins/atp/` 하위에 위치한다. 위치만 성문화한다. 파일명·내용·호출 문법·배포형(command vs skill)은 F-3PLAT-4 실측 대상(`TODO:실측` 마커 보존)이며 본 ADR 범위 밖이다.

### 결정 5 — ADR 본문 구 경로 링크 보존 원칙 확정

**결정**: ADR-0002~0006 본문의 구 경로 상대링크(`../development/*`, `addons/graphify` 등)는 수정하지 않는다. ADR 본문은 결정 당시 레퍼런스 스냅샷이며, GitHub 트리에서 해당 링크가 깨짐을 의도적으로 감수한다. 이 결정을 본 ADR 에 명기함으로써 "미수정 = 누락"이 아님을 성문화한다.

### 결정 6 — 롤백 경로

**결정**: `git revert` 로 커밋 단위 원복한다. marketplace source 를 구 경로로 되돌리면 구 캐시 레이아웃과의 정합이 복원된다.

---

## 검토한 대안

| 안 | 요약 | 기각 이유 |
|---|---|---|
| A1: 전 자산 plugins/atp/ 이동, 루트엔 README 류만 | docs 분할 불필요 | ADR·file-map·usage 133KB 가 캐시에 포함 → 번들 절감 약화 |
| A3: docs 전체 루트 잔류 + `${CLAUDE_PROJECT_DIR}` 전환 | 캐시 docs 0 | `${CLAUDE_PLUGIN_ROOT}` 추상화 파괴, ADR-0002 위배 |
| graphify addons/ 유지 | 이동 없음 | plugins/ 형제 구조 불일치, Codex 정본 경로 비일관 |

---

## 결과

- `plugins/atp/` 에 base 플러그인 자산(agents 10개, skills 2개, templates, plugin.json, docs/development 6건, 번들 경량 허브 2건) 이동 완료.
- `plugins/atp-graphify/` 에 add-on 자산(agents 3개, plugin.json, docs/graphify-usage.md) 이동 완료.
- `addons/` 디렉토리 삭제. `plugins/atp -> ..` symlink 삭제.
- 4개 marketplace 매니페스트 source + version 2.0.0 갱신 완료.
- 루트 docs/index.md 및 카테고리 index 4건 루트 잔류 확인. 번들 경량 허브 2건 신규 작성.
- 루트 잔류 문서 9건의 development/ 6건 cross-link 를 `plugins/atp/docs/development/` 프리픽스로 정정 완료(R10). ADR 5건 본문은 무수정(결정 5).
- addons/graphify 참조 22건을 plugins/atp-graphify 경로로 수정 완료(R-GF1~R-GF23 중 무수정 2건 제외).
- 커밋: 1e6fc79, feae019, bb75f21, 1b4a708.
- ADR-0002(plugin-only) / ADR-0003~0006 불변. 본 ADR 은 ADR-0002 의 플러그인 source 경로를 구체화하며 ADR-0006 의 3-플랫폼 구조 위에서 번들 경계를 확정한다.

---

## 관련 문서

- [ADR-0002](./ADR-0002-plugin-only-migration.md) — plugin-only 전환 (플러그인 source 경로의 전제)
- [ADR-0006](./ADR-0006-three-platform-support.md) — 3-플랫폼 지원 (Gemini manifest F-3PLAT-4 이월 근거)
- [platform-adapters.md](../../plugins/atp/docs/development/platform-adapters.md) — capability tier 권위 SSoT (번들 포함 이동 후 경로)
- [agent-team-protocol.md](../../plugins/atp/docs/development/agent-team-protocol.md) — 코어 프로토콜 (번들 포함 이동 후 경로)
