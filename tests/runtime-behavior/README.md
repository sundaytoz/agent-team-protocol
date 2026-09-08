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

> **Candidate hook은 옵트인 add-on `atp-codex-hooks`에만 있다.** Smoke 전 임시 `CODEX_HOME`에
> base `atp`와 함께 `plugins/atp-codex-hooks`를 fresh install한다. `test_codex_hook_guard.py`의
> `RUNNER`/`HOOKS` 상수도 `plugins/atp-codex-hooks/hooks/`를 가리킨다. base만 설치한 세션은 hook이
> 없어 marker 부재 → spawn 0이 정상이다.
>
> TUI 격리 smoke의 환경 함정(stdin 블록, cmux shim, capacity denial 재현, fresh home의 로그인 화면,
> TUI 포그라운드 입력 흡수)은 `docs/backlog/codex-cli-hook-guarded-bounded-pool.md` §"격리 검증이
> 필요할 때의 함정"을 따른다.
>
> **Evidence manifest는 생성기로만 만든다.** 각 `codex exec` run 디렉토리(`state_dirs_before/after.txt`, `last_message.txt`,
> `exit.txt`, `events.jsonl`)를 `python3 tests/runtime-behavior/build_hook_evidence.py --out <manifest> --run Q1=<dir> …
> [--merge-into <기존 manifest>]` 에 넘기면 hook ledger에서 count/ordering/SHA-256만 뽑아 `smokes[]`를 채우고, 사용자명·절대 경로
> 조각이 있으면 쓰기를 거부한다. scope·axes·deployed_profile 등 메타는 호출자가 채운다. 2026-09-08 승격 evidence가 이 스키마다.
>
> **Event ledger는 opt-in이다.** `PLUGIN_DATA/hook_guarded_pool/v1/<session>/events.jsonl`은 runner가 한 번도 읽지 않는 maintainer
> 진단 산출물이므로 기본 비활성이다. Smoke evidence의 count/ordering을 수집하려면 실행 환경에
> `ATP_HOOK_EVENT_LEDGER=1`을 설정한다. 설정하지 않으면 pool은 정상 동작하지만
> `events.jsonl`이 생성되지 않아 ledger 기반 판정을 만들 수 없다. 소비자 환경에서는 설정하지
> 않는다.


Release maintainer는 임시 Codex home/workspace에서 실제 smoke 3종을 실행하고 JSONL·report·ledger를 보존한다. 소비 프로젝트의 각 task는 이 validator, capability child, timeout/wait/list probe, source/install parity 검사를 실행하지 않는다. 공개 evidence manifest에는 Codex surface/version, sanitized artifact label/hash, requested/spawn/nonterminal/terminal/collected/manual-wait/list/interrupt/recovery와 completion ordering을 기록한다. Raw transcript, 사용자 대화, 인증 정보, 로컬 사용자명과 절대 경로는 커밋하지 않는다.

최신 2026-08-26 Codex CLI 0.149.1 evidence는 `evidence/codex-cli-0.149.1-20260826.json`에 있다. Terminal-only와 delayed nonterminal-to-terminal 1-agent는 통과했지만 staggered two-agent가 `spawn_calls=2`, `terminal_deliveries=1`로 실패해 deployed CLI profile은 계속 `unsupported`, team execution disabled다. 0.147.0 historical evidence는 `evidence/codex-cli-0.147.0-20260819.json`에 보존한다. App/IDE는 empirical `unknown`이다.

같은 0.149.1 manifest의 `topology_and_capacity_probes`는 nested spawn, cumulative fan-out, saturated fan-out과 depth-chain 관측을 별도로 보존한다. Fixed-delay harness가 포함된 capacity probe는 all-results barrier qualification이 아니며, bounded queue→wait→refill scheduler 후보의 입력으로만 사용한다.

`bounded_pool_candidate_smokes`는 source skill을 직접 읽은 격리 run의 flat width-3 pool, nested width-2 worker pool, capacity-denial refill과 후속 qualification 결과를 기록한다. 세 terminal-only queue baseline은 pending refill과 5/5 result collection에 통과했고 실제 thread-limit denial도 terminal 뒤 새 environment identity로 재투입했다. Candidate source/install byte parity와 설치본 flat/nested/denial-refill 최소 회귀도 통과했다.

후속 qualification은 overall FAIL이다. 최초 A run은 saturation을 만들지 못해 superseded됐고 PASS로 세지 않는다. Saturated A rerun은 `MESSAGE` 시점 running 3/pending 2를 유지하고 message-triggered slot release/refill 0을 지켰으며 같은 identity의 terminal도 받았지만, requested 5 중 attempt/accepted 3/3, terminal 3, collected 1, pool wait 2에서 두 번째 join이 멈춰 parent final이 없었다. B는 active wait 중 steering queue 1건을 accepted했지만 scheduler에 전달하지 않아 requested/accepted 5/5, terminal/collected 4/4, wait 5, send/follow-up/list/interrupt 0, parent final 0이었다. C는 interactive approval overlay와 reject decision을 relay했지만 target child가 `turn_aborted`로 끝나 same-identity continuation과 target terminal이 없었다; companion terminal 1, pool wait 2, parent final 0이며 harmless marker는 생성되지 않았다. D는 running 3/pending 2에서 cancellation queue를 accepted했지만 scheduler에 전달하지 않았고 queued cancellation 뒤 pending 두 task를 추가 spawn했다; accepted 5, terminal/collected 4/4, wait 4, interrupt 0, parent final 0이었다. Harness의 외부 cleanup은 scheduler cancellation으로 집계하지 않는다.

따라서 deployed profile은 다음 네 값을 유지하며 별도 bounded-pool capability 축이나 execution mode를 추가하지 않는다.

```yaml
formal_adapter_enabled: false
manual_wait_polling_supported: false
host_managed_subagent_orchestration: unsupported
team_execution_enabled: false
```

> **2026-09-08 갱신**: 위 네 값은 2026-08-26 built-in barrier 판정의 기록이다. 이후 hook-guarded bounded pool이
> 4축 qualification을 통과해 배포 profile은 **scope-gated** `host_managed_subagent_orchestration: supported`,
> `team_execution_enabled: true`(`execution_scope: hook_guarded_bounded_pool`, `scope_gate: atp_hook_guard_ready_marker`)다.
> 승격 evidence는 `evidence/codex-cli-0.149.1-hook-guarded-20260908.json`(Q1 terminal-only / Q2 delayed / Q3 staggered /
> Q4 capacity-denial refill 전부 pass). add-on `atp-codex-hooks` marker가 없는 세션은 여전히 위 네 값으로 동작한다.
> 상세: `plugins/atp/docs/development/codex-lifecycle-routing.md` §8.6, ADR-0025.

재검증하려면 A에서 한 wake에 이미 전달된 terminal을 모두 소비하고 terminal 뒤에만 refill해야 한다. B/D는 queued control을 active pool join에 실제 전달하는 host surface가 필요하고, C는 approval decision 뒤 같은 child identity가 continuation돼 terminal result를 내야 한다. 세 조건과 기존 baseline·source/install parity가 한 qualification에서 모두 PASS하기 전에는 candidate를 supported로 표현하지 않는다.

2026-08-28 hook-guarded 후보의 후속 결과는
`evidence/codex-cli-0.149.1-hook-guarded-20260828.json`에 있다. 설치본 T1/T2/T3,
interactive approval T5와 nested owner T8은 통과했다. 그러나 active wait의 steering/cancellation은
`codex queue` 접수 뒤 `UserPromptSubmit` delivery 0이었고, 포화 `spawn_agent` 오류는
`PostToolUse`가 발생하지 않아 parent가 본 denial 1건이 hook ledger에는 0건으로 남았다.
Windows `py -3` dependency와 `allow_managed_hooks_only`도 미검증이다. 따라서 T4/T6/T7/T9가
실패하고 H8이 unknown인 이 후보는 release qualification이 아니며 위 disabled profile과
plugin version을 그대로 유지한다.
