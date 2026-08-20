---
kind: adr
adr_number: "0024"
title: Codex product-managed subagent orchestration과 release-time capability evidence
status: accepted
date: 2026-08-19
deciders:
  - template-maintainer
  - stzjungsoo
supersedes:
  - ADR-0023
---

# ADR-0024: host-managed subagent orchestration

## 상태

**Accepted** — 2026-08-19. ADR-0023의 `host_native_cooperative` mode, bounded wait 재진입, runtime probe와 정상 실행 검증 결정을 supersede한다. Formal `environment_subscription`, environment-authoritative lifecycle, approval/recovery/ownership 계약과 non-Codex topology 결정은 유지한다.

## 맥락

ADR-0023은 Codex의 bounded mailbox wait를 team correctness primitive로 사용했다. 2026-08-19 원본 parent session은 child spawn 1회 뒤 manual wait 1회만 수행했고, wait가 nonterminal update를 반환한 뒤 두 번째 wait 없이 report completion을 serialize했다. Terminal result는 약 37.9초 뒤 별도 event로 도착했다. 즉 correctness가 host가 아니라 모델의 재대기 판단에 의존했다.

공식 OpenAI subagent 문서는 Codex app/CLI/IDE의 built-in workflow가 spawn, follow-up routing, 결과 대기와 thread 종료를 관리하고 요청한 모든 subagent 결과가 준비된 뒤 통합하도록 요청할 수 있다고 설명한다. Skill 문서는 name/description으로 선택한 skill의 전체 `SKILL.md`를 실행 시 읽는 계약을 제공한다. 이 제품 계약을 ATP의 manual polling보다 우선해야 한다.

## 결정

### 1. Execution mode를 host-managed로 교체한다

정상 Codex team mode는 `host_managed_subagent_orchestration`이다. Profile 축은 `formal_adapter_enabled`, `manual_wait_polling_supported`, `host_managed_subagent_orchestration`, `team_execution_enabled`다. Formal adapter 부재와 managed orchestration 지원은 직교한다.

ATP orchestrator는 정상 경로에서 generic wait/list polling을 운영하지 않는다. Nonterminal update는 `running`이며 모든 요청 child의 terminal result가 수신·검증·취합되기 전 report/session completion이나 parent final을 만들지 않는다.

### 2. Host 전용 실행 계약은 전용 skill과 appendix에 격리한다

Codex에서 첫 subagent collaboration action 전에 `codex-team` skill을 선택하고 전체 지침을 읽는다. Codex 도구명, event spelling, capability profile과 transcript validator mapping은 전용 skill, Codex appendix, maintainer validator에만 둔다. 공통 task/protocol/agent에는 host-neutral skill selection과 managed result barrier 의미만 둔다.

### 3. Capability 검증은 release-time maintainer 책임이다

소비 프로젝트의 각 task는 capability child, timeout/wait/list probe, runtime validator, source/install parity 검사를 실행하지 않는다. Maintainer는 release 전 격리된 환경에서 terminal-only 1-agent, delayed nonterminal+terminal 1-agent, staggered terminal 2-agent smoke를 실행해 transcript/report/ledger를 보존한다. Deterministic fixture만으로 `supported`를 확정하지 않는다.

### 4. Failure와 telemetry를 합성하지 않는다

실제 capability error는 automatic polling, retry, interrupt, fallback 또는 Tier B 전환으로 숨기지 않는다. 마지막 environment-authoritative state와 authority/ownership을 보존하고 blocked/user-decision 경로를 사용한다. 알 수 없는 telemetry는 `null`이다. Ledger는 기존 six-field envelope을 유지하고 concrete session/report/environment/monotonic-event identity로 transcript event와 연결한다.

### 5. Completion serialization은 event ordering으로 검증한다

종료는 모든 terminal result, 통합, verification, retrospective, report 반영·재스테이징·재검증, 요청된 mutation/remote verification, session `ended_at`, report 최종 read-only 검증, parent final 순서다. Validator는 timestamp 값뿐 아니라 completion/termination을 쓴 transcript event가 마지막 terminal 뒤인지 검사한다. 미래 `ended_at` 선기록은 실패다.

## 결과

- Codex team execution candidate는 제품 관리형 all-results barrier를 우선하고 root-level manual polling을 제거한다.
- Formal subscription을 제공하는 host와 non-Codex Tier A-flat/Tier B/explicit-independence 경로는 유지된다.
- Release evidence가 없거나 제품 동작이 공식·경험적으로 확인되지 않은 surface는 `unknown`으로 남긴다.
- ADR-0023 fixture와 실제 결함 transcript는 historical regression evidence로만 보존한다.

2026-08-19 Codex CLI 0.147.0 maintainer smoke 결과 terminal-only 1-agent는 통과했으나 delayed nonterminal+terminal과 staggered 2-agent는 all-results 전 parent가 종료됐다. 따라서 tested CLI profile은 `unsupported`, team execution은 disabled다. App/IDE는 `unknown`이며 세 smoke가 모두 통과하는 새 evidence 전에는 supported로 승격하지 않는다.

## 기각한 대안

- **bounded wait를 반복해 correctness를 확보**: nonterminal 반환 뒤 모델이 재대기해야 하므로 닫힌 보장이 아니다.
- **매 task smoke/probe**: 소비자 비용·변이·권한 위험을 만들고 release capability 판정을 task마다 재추론한다.
- **Codex를 자동 Tier B로 격하**: 검증된 제품 수준 team orchestration을 불필요하게 포기한다.
- **공통 protocol에 Codex 도구/event를 복제**: host-neutral 경계를 깨뜨린다.

## 검증

- `tests/runtime-behavior/test_codex_managed_contract.py`와 managed fixture 3종
- `tests/runtime-behavior/validate_codex_session.py --profile host-managed`
- `tests/lifecycle-contract/validate.py`의 formal/non-Codex/Tier B/approval/recovery 불변 fixture
- release-time isolated Codex CLI smoke transcript와 evidence manifest

## 관련 문서

- [ADR-0023](./ADR-0023-host-native-cooperative-execution.md)
- [Codex orchestration skill](../../plugins/atp/skills/codex-team/SKILL.md)
- [Codex lifecycle appendix](../../plugins/atp/docs/development/codex-lifecycle-routing.md)
- [Runtime behavior validator](../../tests/runtime-behavior/README.md)
