---
kind: adr
adr_number: "0010"
title: work-session 추적 분할 정책 — 플러그인 기본=추적, 레포별 opt-out 허용, 이 소스 레포는 opt-out
status: accepted
date: 2026-06-16
deciders:
  - template-maintainer
  - stzjungsoo
supersedes:
  - ADR-0006 (L34 의 "gitignore 대상이라 세션 종료 후 소실된다" 단정을 무효화 — ADR-0006 본문은 불변)
related_commits:
  - 0aa5625 (work-session 추적 분할 정책 — 본 ADR 결정 구현)
---

# ADR-0010: work-session 추적 분할 정책 — 플러그인 기본=추적, 레포별 opt-out 허용, 이 소스 레포는 opt-out

## 상태

**Accepted** — 2026-06-16. 세션 20260616-094150 초안, 동일 날짜 분할 정책으로 확정.

**ADR-0006 부분 supersede**: ADR-0006 L34 의 "work-session 산출물은 gitignore 대상이라 세션 종료 후 소실된다" 단정을 본 ADR 이 무효화한다. 플러그인 기본이 추적이므로 해당 단정은 더 이상 유효하지 않다. 단, 이 소스 레포는 opt-out(gitignore)을 행사하므로 이 레포 자체에서는 work-session 이 추적되지 않는다. ADR-0006 본문은 불변 기록 — 직접 수정 금지.

---

## 맥락

ATP 프로토콜 문서는 과거 세션 ID 를 규정의 evidence record 로 인용한다("세션 20260609-125316 에서 …"). 이 인용 관행이 유효하려면 참조 대상 세션 산출물이 실제로 지속되어야 한다.

현행 `.gitignore` 는 `.atp/work-session/` 트리 전체를 ignore 하고 있어 세션 산출물이 세션 종료 후 소실된다 — evidence record 인용이 dangling reference 가 되는 구조다.

세션 20260616-094150 design.md §개요 에서 "위치는 `.atp/` 에 둔 채 un-gitignore + 트리 전체 git 추적으로 전환"을 최소 변경 + 최대 일관성 경로로 결정했다. 이후 사용자 검토에서 **이 소스 레포 고유의 맥락**이 추가로 식별되었다:

- **이 소스 레포는 PUBLIC**: 소비 레포 대부분이 private 인 것과 달리 이 레포는 공개되어 있다.
- **user_signals 발화 인용**: work-session report 의 `user_signals` 섹션에는 유지자(실제 사람)의 발화가 직접 인용된다.
- **retrospective 내부 비판**: retrospective-advisor 산출물에는 프로세스·결정에 대한 내부 비판이 기록된다.

이 세 축이 겹치면 세션 산출물이 공개 레포에 커밋되었을 때 의도치 않은 노출이 발생할 수 있다. 초안 결정(전면 추적 전환)은 이 축을 검토하지 않았고, 사용자가 이를 잡아 분할 정책으로 정정했다.

---

## 결정

### 결정 1 — 플러그인 기본: 추적 (소비 레포)

신규 소비 레포의 `/atp:init` scaffolding 기본값은 **추적**이다.

- `init/SKILL.md §3`: `.atp/work-session/` 를 `.gitignore` 에 append 하는 로직을 **"ignore 라인이 있으면 제거(추적 보장)"** 로직으로 반전한다.
- `task/SKILL.md §0.5 step 2` 및 `init` 의 `render_migrate_block` step 2 도 동일 정책으로 반전하여 1차/2차 migrate 간 정책 일관성 보장.

효과: 아직 1차 migrate 블록이 살아있는 소비 레포는 다음 `/atp:task` 또는 `/atp:init` 진입 시 경로 이관 + ignore 라인 제거를 한 번에 수행 → 새 추적 정책에 자동 수렴.

### 결정 2 — opt-out 제공

추적을 원치 않는 레포는 `.gitignore` 에 `.atp/work-session/` 1줄을 추가해 opt-out 할 수 있다. 플러그인은 이 라인의 존재를 존중하며 강제로 제거하지 않는다(ADR-0009 소비 `.gitignore` 불가침 원칙과 정합).

**opt-out 적합 시나리오 예시**:
- public 레포이고 work-session 에 내부 발화·비판이 기록되는 경우
- CI 환경에서 work-session 커밋이 노이즈로 작용하는 경우
- 레포 크기 정책상 자동 생성 파일 커밋을 금지하는 경우

### 결정 3 — 이 소스 레포(`agent-team-protocol`)는 opt-out

이 소스 레포는 아래 세 근거의 합산으로 opt-out 을 행사한다:

1. **Public 레포**: GitHub 에 공개되어 있어 커밋된 산출물이 누구에게나 노출된다.
2. **user_signals 발화 인용**: report.md 의 `user_signals` 섹션에는 유지자(실제 사람)의 발화가 인용된다. 이 발화는 내부 커뮤니케이션을 의도한 것으로, 공개 커밋 기록에 영구 보존되는 것은 부적절하다.
3. **retrospective 내부 비판**: retrospective-advisor 산출물에는 프로세스·결정·구현에 대한 솔직한 내부 비판이 담긴다. 이 역시 공개 노출이 부적절하다.

따라서 이 레포는 `.gitignore` 에 `.atp/work-session/` 라인을 유지한다. 이는 결정 1(플러그인 기본=추적)과 모순이 아니다 — 단일 분할 정책의 일관된 적용이다. `.atp/work-session/` 내 문서는 세션 중 에이전트가 로컬에서 생성·참조하지만 커밋되지 않는다.

### 결정 4 — OQ-E: 이미 1차 마이그레이션을 끝낸 소비 레포 = 수동 안내

이미 1차 `.claude→.atp` 마이그레이션을 완료해 migrate 블록이 자기삭제된 소비 레포에는 결정 1 의 반전이 자동 도달하지 않는다. 이에 대해 **문서 안내(수동)** 를 확정한다:

`setup-checklist.md` / `setup-checklist.en.md` 에 두 방향 안내를 추가한다:
- "기존 소비 레포는 `.gitignore` 에서 `.atp/work-session/` 라인 1줄을 직접 제거하면 추적이 활성화된다."
- "추적을 원치 않으면 `.gitignore` 에 `.atp/work-session/` 1줄을 추가해 opt-out 할 수 있다."

---

## 영향

| 파일 | 변경 내용 | 소유 |
|---|---|---|
| `.gitignore` | `.atp/work-session/` 라인 재추가(이 레포는 opt-out). `git rm --cached .atp/work-session/` 도 수행 | orchestrator |
| `plugins/atp/skills/init/SKILL.md` §3 | gitignore append → ignore 라인 제거 반전 | implementation |
| `plugins/atp/skills/init/SKILL.md` render_migrate_block step2 | append → 제거 반전 | implementation |
| `plugins/atp/skills/task/SKILL.md` §0.5 step 2 | append → 제거 보장 반전 | implementation |
| `plugins/atp/docs/development/agent-team-protocol.md` §7 | "플러그인 기본=추적, opt-out 가능" 1구 추가 | orchestrator |
| `docs/usage/setup-checklist.md` | 추적 기본 안내 유지 + opt-out 안내(1줄 추가) 추가 | documentation-advisor |
| `docs/usage/setup-checklist.en.md` | 영문 동기 + opt-out 안내 추가 | documentation-advisor |
| `docs/architecture/file-map.md` | 런타임 섹션에 "플러그인 기본=추적 / opt-out 가능 / 이 레포 opt-out" 명시 | documentation-advisor |
| `docs/index.md` | 빠른 진입 세션 산출물 포인터 "git 추적" 단정 → 분할 정책 정정 | documentation-advisor |
| `TEMPLATE_DEV.md` | 분할 정책 반영 | orchestrator |
| ADR-0006 본문 | **불변 — 직접 수정 금지**. 본 ADR 이 L34 단정을 supersede 로만 무효화 | — |

---

## 검증 포인트 (핵심)

### 소비 레포 (기본 추적)
- 신규 `/atp:init` 후 `.gitignore` 에 `.atp/work-session/` 라인 부재
- init/SKILL.md §3 에 `>> "$GI"` append 패턴 부재 + `grep -vxF '.atp/work-session/'` 패턴 존재

### 이 소스 레포 (opt-out)
- `.gitignore` 에 `.atp/work-session/` 라인 존재
- `git check-ignore .atp/work-session/20260616-094150/report.md` → ignore 됨(exit 0)
- setup-checklist 에 opt-out 1줄 추가 안내 존재
- file-map §3 에 분할 정책 + 이 레포 opt-out 명시

---

## 관련 문서

- [ADR-0006](./ADR-0006-three-platform-support.md) — L34 "gitignore 대상이라 세션 종료 후 소실된다" 원문 보존 (본 ADR 이 해당 단정을 supersede)
- [ADR-0009](./ADR-0009-bundle-runtime-platform-neutralization.md) — 플러그인 update 가 소비 `.gitignore` 불가침 원칙 (opt-out 정합성 근거)
- [docs/architecture/file-map.md](../architecture/file-map.md) — 런타임 디렉토리 구조 및 opt-out 캡션
- [plugins/atp/docs/development/agent-team-protocol.md](../../plugins/atp/docs/development/agent-team-protocol.md) — §7 공유 상태 레이아웃
