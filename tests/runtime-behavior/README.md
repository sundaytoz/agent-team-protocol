# Codex runtime behavioral regression

`validate_codex_session.py`는 실제 Codex JSONL의 collaboration event와 report/ledger를 검사한다. Internal rollout JSONL과 `codex exec --json` public event를 읽고 attempted/denied/executed를 분리한다.

## Host-managed contract fixture profile

```bash
python3 tests/runtime-behavior/validate_codex_session.py \
  --profile host-managed \
  --session-jsonl /path/to/codex-exec.jsonl \
  --ledger /path/to/.atp/work-session/SID/artifacts/wait-wakeup-events.jsonl \
  --report /path/to/.atp/work-session/SID/report.md \
  --appendix plugins/atp/docs/development/codex-lifecycle-routing.md
```

이 profile은 future supported implementation의 contract fixture를 검증하며 deployed capability 판정을 단독으로 만들지 않는다. 검증 항목은 다음과 같다.

- 첫 collaboration action 전에 `codex-team` skill이 선택·로드됨
- requested agents, executed spawn, terminal deliveries, collected results가 일치함
- manual wait/list/정상 interrupt와 semantic recovery가 0건임
- nonterminal update는 계속 running이고 terminal 전 결과 통합·report/session completion·parent final이 없음
- 여러 agent면 전원의 terminal result 뒤에만 barrier가 열림
- report/environment identity mapping과 concrete source reference가 실제 event에 연결됨
- 미래 `ended_at`을 terminal 전에 serialize하지 않음
- report 최종 read-only validation이 completion 기록 뒤, parent final 전에 있음
- 알 수 없는 telemetry가 `null`임

체크인된 fixture 3종은 terminal-only 1-agent, delayed nonterminal+terminal 1-agent, staggered terminal 2-agent를 다룬다.

```bash
python3 -m unittest tests/runtime-behavior/test_codex_managed_contract.py
```

## Historical regression

```bash
python3 tests/runtime-behavior/validate_codex_session.py \
  --profile historical-regression \
  --session-jsonl /path/to/rollout.jsonl
```

고정 관측값은 executed spawn 1, wait 13, list 2와 wait timeout 11이다. `native-cooperative` parser/fixture도 2.14.0 historical decision을 재현하기 위해 남아 있지만 정상 success profile이나 release capability 근거가 아니다. 새 release는 `host-managed`와 실제 격리 maintainer smoke만 사용한다.

## Maintainer smoke

Release maintainer는 임시 Codex home/workspace에서 실제 smoke 3종을 실행하고 JSONL·report·ledger를 보존한다. 소비 프로젝트의 각 task는 이 validator, capability child, timeout/wait/list probe, source/install parity 검사를 실행하지 않는다. 실제 evidence manifest에는 Codex surface/version, artifact path/hash, requested/spawn/nonterminal/terminal/collected/manual-wait/list/interrupt/recovery와 completion ordering을 기록한다.

2026-08-19 Codex CLI 0.147.0 evidence는 `evidence/codex-cli-0.147.0-20260819.json`에 있다. Terminal-only는 통과했지만 delayed nonterminal과 staggered two-agent는 all-results 전 parent가 종료돼 deployed CLI profile은 `unsupported`, team execution disabled다. App/IDE는 empirical `unknown`이다.
