# plugins/ — Codex interim symlink (비정본)

`plugins/atp` 는 repo root 로의 상향 symlink 다. Codex marketplace
(`.agents/plugins/marketplace.json`)의 `atp` source.path(`./plugins/atp`)가
가리키는 대상이다. **비정본**: 공식 제약("source.path 는 marketplace root 내부
유지")을 우회한다(symlink 타깃 = repo root, marketplace root 밖). install 은
통과하나 정본 패턴 아님.

- 정본 재배치(자산을 `plugins/atp/` 실디렉토리로 이동)는 백로그 F-3PLAT-5.
- **Windows 취약성**: git symlink 는 `core.symlinks=false` 환경(일부 Windows)에서
  일반 텍스트 파일(`..`)로 체크아웃되어 깨진다. Codex on Windows 사용 시
  F-3PLAT-5 정본 subdir 재배치 선행 필요.
- atp-graphify 는 symlink 불요 — `./addons/graphify` 실디렉토리 직접 source.
