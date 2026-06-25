---
kind: changes
title: "@atp-opencode/opencode npm publish 가능화 — vendor 번들 + prepack"
date: 2026-06-25
related_adr: ADR-0014
related_changes: 2026-06-24-opencode-adapter.md
---

# @atp-opencode/opencode npm publish 가능화 (2026-06-25)

## 변경 요약

`adapters/opencode/`의 패키징 결함을 수정해 **실제 npm publish → `npx @atp-opencode/opencode install` 가 동작**하게 만들었다. 이전까지는 레포 clone 안에서만 로컬 실행 가능한 상태였다.

## 근본 원인

`src/plan.js`와 `src/install.js`가 canonical 소스(`plugins/**`)를 `REPO_ROOT = resolve(__dirname, '..', '..', '...')` 상대경로로 읽었다. `files: ["bin/", "src/"]`라 npm tarball에 `plugins/**`가 빠졌고, 설치 시 `__dirname`이 `node_modules/@atp-opencode/opencode/src`가 되어 `../../../`가 깨졌다(ENOENT).

## 변경 내용

| 파일 | 변경 내용 |
|---|---|
| `adapters/opencode/src/paths.js` | `resolveCanonicalPluginsRoot(fromDir)` 헬퍼 추가 — `vendor/plugins/atp/agents` 존재 시 번들 경로, 없으면 `../../../plugins` 레포 폴백. |
| `adapters/opencode/src/plan.js` | `REPO_ROOT` 제거 → `PLUGINS_ROOT = resolveCanonicalPluginsRoot(__dirname)` 경유로 6개 `CANONICAL_*` 상수 재정의. |
| `adapters/opencode/src/install.js` | 동일 폴백으로 `plugin.json`(manifest source_version) 경로 해석. |
| `adapters/opencode/package.json` | `files`에 `vendor/` 추가, `scripts.prepack: "node scripts/bundle-canonical.js"` 추가. |
| `adapters/opencode/scripts/bundle-canonical.js` (신규) | prepack 시 canonical 7개 경로를 `vendor/plugins/`로 복사. 누락 시 exit 1로 publish 차단. |
| `adapters/opencode/.gitignore` (신규) | `vendor/`, `*.tgz`, `node_modules/` 제외. |

## 설계 원칙 준수

- **ADR-0014 D3** (canonical 단일 소스, "4번째 수작업 사본 금지"): `vendor/`는 git-ignored 빌드 산출물로, 레포에는 `plugins/**` canonical만 커밋. prepack이 publish 시점에만 번들 생성.
- **self-dogfooding 유지**: `vendor/` 부재 시 레포 폴백 분기로 `node bin/cli.js install` 계속 동작.

## 검증 결과

전건 PASS (`.atp/work-session/20260625-100445/verification/results.md`):

| AC | 내용 | 결과 |
|---|---|---|
| AC-1 | bundle 스크립트 7/7 타겟 생성 | PASS |
| AC-2 | npm pack tarball에 vendor/ 43파일 포함 (prepack 자동 실행) | PASS |
| AC-3 | 기존 단위 테스트 회귀 0 (24/24) | PASS |
| AC-4 | vendor 부재 시 레포 폴백 동작 (agent 10개) | PASS |
| AC-5 | 레포 밖 임시 디렉토리에서 tarball 설치 후 `atp-opencode install` 정상 | PASS |
| AC-6 | vendor/ git 추적 제외 확인 | PASS |
| AC-7 | manifest source_version `2.2.2` | PASS |

## publish 절차 (사용자 직접 수행 필요 — credential·외부게시 게이트)

```bash
# 필요 시
npm org create atp

npm login
cd adapters/opencode
npm publish --access public
```

`prepack` 훅이 `npm publish` 전 자동으로 `vendor/` 번들을 생성한다. 레포에 `vendor/`를 커밋할 필요 없음.

## 관련 문서

- [2026-06-24-opencode-adapter.md](./2026-06-24-opencode-adapter.md) — 초기 generator + npm bin CLI 추가 이력
- [ADR-0014](../adr/ADR-0014-opencode-host-adapter-strategy.md) — 이식 전략 결정 + 구현 완료 기록(D7 후속). publish 가능화 사실 추가 노트 포함.
