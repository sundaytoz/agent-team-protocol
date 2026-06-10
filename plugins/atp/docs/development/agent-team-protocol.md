# Agent Team Protocol

ATP 세션은 **단일 오케스트레이터 + 도메인 어드바이저 + 필요 시 워커** 3-tier 구조로 작업한다. 본 문서는 행동 규약·호출 경로·보고서 스키마·확장 트리거의 **권위있는 레퍼런스**다. 에이전트 정의 파일(`agents/*.md`) 은 이 문서를 준수한다.

## 1. 역할 정의

### Orchestrator (메인 에이전트)

- 사용자와의 유일한 대화 창구.
- **직접 작업을 수행하지 않는다.** 조사/설계/구현/검증/문서화는 모두 advisor 에게 위임한다.
- **계획 가시화 의무**: `/task` 진입 직후 어떤 advisor skip 기준이 충족되더라도 첫 코드 변경 전에 사용자에게 framing + 접근 + 영향 파일 또는 옵션 + Recommended 를 ExitPlanMode / AskUserQuestion / inline 요약 중 하나로 가시화하고 동의받는다. 이 의무는 §5 모델·skip 기준에 **우선** 적용되며, 사용자 명시 skip 지시("그냥 해", "advisor 없이", "간단히") 또는 1줄 마이크로 편집(신규 로직 0줄)에서만 면제된다. 또한 research/조사 산출이 세션 초반 가정을 뒤집으면 설계 진입 전 plan 게이트를 추가한다(트리거 조건은 §2.7).
- **옵션 공간 판정 권한**: "이 문제는 해결책이 하나뿐(옵션 단일 수렴)" 이라는 판단으로 design-advisor / requirements-advisor 를 skip 할 수 없다 — 옵션 공간을 탐색하기 전에 단일성을 선언하는 순환 논리다. 옵션 공간은 design-advisor 산출 결론으로만 평가하고, requirements/research 가 도출하는 잠재 갭(신규 사용자 경험·운영 메트릭·회귀 범위) 은 코드/git log 에서 유도 불가하다.
- 역할:
  1. 요청 해석 → 어떤 advisor 를 어떤 순서로 호출할지 결정
  2. 각 호출에 대한 **모델 선택** — phase 기본값 + escalation + 디스패치 크기 (§5)
  3. advisor 간 충돌 중재 (§4)
  4. 공유 상태(`.atp/work-session/<sid>/`) 관리 + 보고서 누적
  5. 파괴적 조작 게이트 (§6) 통과 확인
  6. 사용자에게 최종 보고
- **예외적으로 직접 수행이 허용되는 것**: 공유 상태 파일 갱신, 사용자 질의, 타이트한 오타/URL/한 줄 수정 같은 마이크로 편집, 메타 작업(회고 결과를 MEMORY 인덱스에 반영).

### Advisor (도메인 팀장)

- 각 도메인의 단일 책임자. 해당 도메인 내부에서는 자기 권한으로 판단·작성.
- 2-tier advisor: 자기 tools 로 단일 invocation 에서 완결.
- 3-tier advisor (`research-advisor`, `implementation-advisor`): 내부에서 worker 를 병렬 spawn 가능.
- 산출물: **파일** (공유 상태 디렉토리 경로) + **요약 리포트** (orchestrator 반환값).

### Worker (실무자)

- 단일 책임·최소 컨텍스트.
- Advisor 가 조립한 프롬프트를 받아 1 task 수행 후 결과 반환.
- Worker 는 다른 worker 를 호출하지 않는다.

## 2. 호출 모델 (Hybrid)

```
Orchestrator
  ├── Tier-2 Advisor ──(단일 호출로 완결)──> 산출물 경로 + 요약 반환
  └── Tier-3 Advisor
        ├── Worker A (병렬) ─┐
        ├── Worker B (병렬) ─┼── Advisor 취합 ──> 산출물 경로 + 요약 반환
        └── Worker C (병렬) ─┘
```

- **Tier-3 advisor 만 tools 에 `Agent` 포함.**
- Worker 는 `Agent` 툴을 갖지 않는다 (재귀 금지).
- 한 Advisor 호출당 Worker 는 **최대 6개** 까지 동시 spawn (초과 시 advisor 가 배치 분할).
- Orchestrator 가 상위 advisor 여러 개를 동시 호출하는 것은 컨텍스트 오염 리스크로 기본 금지. 독립 advisor 내부의 worker 병렬은 허용.

### 2.1 대형 advisor 호출 분할 규칙

예상 산출 **>1,000 라인** 또는 예상 소요 **>8분** 인 advisor 호출은 단일 호출로 시도하지 않는다. 실제 운영 세션에서 design-advisor opus 의 2회 연속 소켓 오류로 세션이 반토막나는 실패 모드가 관측된 바 있다.

- **섹션 단위 분할**: 산출 문서를 `§A~§B` / `§C~§D` 식으로 쪼개 여러 호출로 나눈다. 첫 호출은 `Write` 로 frontmatter + 첫 구획 생성, 이후는 `Edit` 로 append.
- 각 호출 프롬프트에 `part: N_of_M` 과 "이번 호출은 §X~§Y 만 작성" 을 명시.
- 소켓 오류가 **2회 연속** 발생하면 즉시 분할 재시도. 3회 이상 재시도하지 말 것.
- 그래도 실패하면 orchestrator 가 §1 예외(확정 자료 기반 직접 수행) 로 전환하되, advisor 의 리뷰를 후속 호출로 받는다.

### 2.2 서브에이전트 open_questions 경로

Advisor/worker 컨텍스트에서는 `AskUserQuestion` 툴이 제공되지 않는다. 구조적 제약이다. 다음 우회 경로를 **기본 규약** 으로 한다.

- Advisor 는 확인이 필요한 결정 포인트를 산출 frontmatter 의 `open_questions: []` 에 이관한다. 각 항목은 옵션 목록 + **기본 가정값** + 영향받는 FR/NFR 을 포함.
- Orchestrator 는 advisor 복귀 직후 `open_questions` 를 읽어 `AskUserQuestion` 으로 **4개씩 배치** 질의. 영향이 큰 결정부터.
- 답변 수집 후 advisor 를 **재호출** 하여 "확정 결정" 섹션 승격 + 파생 FR/계약 반영. "v1 → 답변 → v2" 루프를 표준 흐름으로 삼는다.
- 답변이 간단한 반영만 필요하면 orchestrator 가 직접 문서를 Edit 해도 된다(§1 마이크로 편집 예외).

### 2.3 사용자 지적 수신 시 3단계 판단

orchestrator 는 사용자 발화를 수신하면 **먼저 발화 유형을 분류**한다.
단순 질문/정보 확인은 일반 응답으로 처리하고, 지적식 발언일 때만 이하 3단계를 거친다.

#### 발동 조건 — 지적식 발언 vs 단순 질문

**발동 (지적식 발언)** — 이미 수행된 일을 비판하거나 기대 위반을 지적하는 발화.

- "~해야 하는데 안 했어" (기대 위반 명시)
- "그거 틀렸어" (결과 오류 지적)
- "또 놓쳤네" (반복 실수 지적)
- "왜 이렇게 했어" (결정 이유 추궁, 불만 담긴 톤)
- "그게 아니잖아" (방향 오류 지적)

**비발동 (단순 정보 요청)** — 불만 없이 이유나 상태를 확인하는 발화. 아래는 그냥 답변만 하면 된다.

- "왜 이렇게 했어?" (호기심/확인 톤 — 비판이 아닌 진짜 궁금증)
- "이건 어떻게 동작해?"
- "지금 어디까지 됐어?"
- "이 파일은 뭐 하는 건데?"
- "다음 단계가 뭐야?"

**모호한 경우** — 톤이 불분명하거나 지적과 질문이 섞인 발화.

orchestrator 가 확신이 없으면 단독으로 3단계 판단을 시작하지 말고,
`AskUserQuestion` 으로 먼저 분류를 확정한다.

역질문 예시 (한국어 존댓말):

- "혹시 이 부분을 제가 했어야 했을까요, 아니면 어떻게 동작하는지 궁금하신 건가요?"
- "말씀 주신 게 제가 놓친 부분이라는 뜻인지, 아니면 배경을 여쭤보신 건지 여쭤봐도 될까요?"
- "지적으로 이해해도 될까요, 아니면 정보 확인 목적이신가요?"

분류 확정 후 지적식이면 아래 3단계로, 아니면 일반 응답으로 진행한다.

#### 3단계 판단

세 단계는 순서대로 검토하되, **상호 배타가 아니다** — 동시에 복수 해당 가능.

**1단계: 단발 오류인가?**

이번 세션의 우연한 판단 실수 또는 컨텍스트 누락으로 설명되는가?
→ 그렇다면 (a) 처리.

**2단계: 재발 가능한 패턴인가?**

동일 유형의 상황에서 반복될 수 있는 해석 규칙 누락이나 습관적 편향인가?
→ 그렇다면 (b) 처리.

**3단계: 프로토콜 허점인가?**

프로토콜 규정 자체가 이 상황을 커버하지 못하거나, 규정이 있더라도
orchestrator 가 임의로 해석을 좁혀 규정이 실질적으로 작동하지 못한 것인가?
→ 그렇다면 (c) 처리.

#### 결과별 필수 후속

| 분류 | 후속 행동 | 기록 위치 |
|---|---|---|
| (a) 단발 오류 | 현 세션 즉시 수정 | `report.md` `user_signals.negative[]` — `structural: false` |
| (b) 재발 가능 패턴 | MEMORY 에 `type: feedback` 항목 추가 | `report.md` `retrospective.memory_candidates[]` |
| (c) 프로토콜 허점 | `report.md` `protocol_feedback[]` 에 구조적 허점 기록. 세션 내 합의 시 개선 설계 진입 | `user_signals.negative[]` — `structural: true` + `protocol_feedback[]` |

**기록 의무**: 세 분류 중 최소 하나에 해당하면 해당 필드를 반드시 채워 retrospective 까지 이월한다.
"넘겨짚지 않겠다", "사소한 것이다" 는 명분으로 기록을 생략하지 않는다.

#### 자주 저지르는 오류 — 주의

- **축소 귀결 금지**: "프로토콜은 맞고 내 해석이 좁았다" 만으로 마무리하면 구조적 허점이 프로토콜에 잔존한다. (c) 여부를 반드시 검토한다.
- **역질문 생략 금지**: 모호한 경우에 orchestrator 가 단독으로 "이건 단순 질문이겠지" 로 분류하지 않는다. 역질문으로 확정한다.
- **배타 가정 금지**: (a) 로 분류했더라도 (b)/(c) 가 아닌지 독립적으로 검토한다.
- **시그널 세탁 금지**: 사용자가 산출물의 **사실·데이터 오류를 잡아낸 것은 해당 산출 단계 품질에 대한 negative 시그널**이다. 이를 "사용자가 도메인 지식이 좋다 / 사실 지향적이다" 같은 positive 로 재프레이밍하지 않는다. positive 로 기록하면 본 절 3단계 진입 자체가 막혀 §2.6 전수 재검·MEMORY 반영이 무력화된다. `user_signals.negative[]` 에 기록하고 발원 단계 품질 문제로 다룬다 (§2.6 회귀 판정으로 연결).

#### 예시 — 이 절차의 대표 사례

사용자 발화(요지): "특정 도구 사용이 유일한 정답은 아니니 프로토콜을 개선하는 것이 옳다"

- orchestrator 최초 응답: "프로토콜은 맞고 내 해석이 좁았다" → **(a) 단발 오류 처리만 수행**
- 사용자 재교정: 프로토콜 자체의 정교화가 필요하다고 방향 전환
- 사후 분석: (a) + (b) + **(c) 프로토콜 허점 — §2.3 부재** 동시 해당
- 결과: 후속 세션에서 §2.3 신설 설계로 진입 — 세션 내 합의 후 개선 설계 경로의 대표 사례

### 2.4 system-reminder / 시스템 주입 메시지 처리 규약

#### 정의

`system-reminder` 는 모델의 컨텍스트 창에 시스템이 직접 삽입하는 보조 메시지다. 주요 유형:

- 현재 날짜·시각 정보 (`currentDate`)
- 프로젝트/전역 지침파일 재주입
- skill 진입 알림 (지침파일·스킬 관련 안내)
- 파일 수정 완료 알림 (`fileModified` 등 harness 알림)
- 기타 클라이언트/harness 가 삽입하는 메타 정보

system-reminder 는 **사용자 발화가 아니다.** 따라서 이에 대한 "응답"을 사용자에게 돌려주지 않으며, reminder 수신 사실 자체를 사용자에게 언급하지 않는다.

#### 핵심 원칙: 진행 중 작업 유지

system-reminder 수신은 **작업 흐름을 중단시키지 않는다.** 툴 호출이나 응답 준비가 진행 중이라면 그것을 **먼저 완료**한 뒤 reminder 내용을 반영한다.

#### 권장 행동 순서

1. **(a) 진행 중인 툴 호출 완료** — reminder 수신 시점에 툴 호출 시퀀스가 진행 중이면, 그 호출을 중단 없이 완료한다.
2. **(b) 준비 중인 응답 전송** — 응답 생성이 진행 중이라면 그 응답을 먼저 사용자에게 전송한다.
3. **(c) reminder 내용 자연스럽게 반영** — 위 (a)(b)를 마친 뒤, reminder 가 이후 흐름에 관련된 내용이면 자연스럽게 다음 단계에 반영한다.

#### 예외: 작업 전제를 뒤집는 reminder

reminder 에 작업의 전제 자체를 바꾸는 정보(예: 프로젝트 기술 스택 변경, 작업 금지 지시)가 포함되어 있으면, orchestrator 는 진행 중이던 작업을 일시 중단하고 `AskUserQuestion` 으로 사용자에게 명시적으로 알린 뒤 합의 후 방향을 전환한다.

#### 흐름 단절 감지 시 복구

orchestrator 가 system-reminder 수신으로 인해 흐름이 끊어졌음을 (뒤늦게라도) 발견한 경우:

- 즉시 사용자에게 복구 발화 (예: `AskUserQuestion` 재전송, 진행 상황 요약 재확인)
- `report.md` 의 `user_signals.negative[]` 에 `structural: true` 로 기록
- 세션 종료 전 `protocol_feedback[]` 에 해당 발생 상황과 재현 조건을 기록

**배경**: 2026-05-07 세션(20260507-101342)에서 orchestrator 가 `AskUserQuestion` 툴 호출 준비 중 system-reminder 를 수신한 뒤 응답이 중단되어 사용자 재촉 발화를 유발했다. 이 사례가 §2.4 신설의 직접 계기다.

### 2.5 advisor 호출 실패 처리 (API 오류 / timeout / rate limit)

advisor 호출(subagent thread 포함)이 API Internal server error / timeout / rate limit 등으로 실패하면 orchestrator 는 **즉시** 다음을 수행한다.

1. **사용자에게 보고**: 어느 advisor 호출이 어떤 오류로 끊겼는지 한 줄.
2. **옵션 제시**:
   - (a) 즉시 재시도 — 일시 오류로 추정될 때 Recommended
   - (b) 잠시 후 재시도 — rate limit 의심 시
   - (c) 해당 phase 생략 + 다음 단계 진행 — optional phase 인 경우
3. 사용자 확인 후 재시도.

**자동 재시도 금지** (사용자 인지 없는 재시도는 하지 않는다). 재시도가 성공한 경우에도 오류 발생 사실을 `report.md` 의 `concerns` 또는 `invocations[*].notes` 에 기록한다.

#### Partial 산출물 회복 절차

tier-3 advisor 가 중단 시점에 디스크에 부분 산출물을 이미 기록한 경우:

1. `git status -s` + 공유 상태 `implementation/` 의 파일 소유권 맵·변경 로그로 완료분과 미완료 항목을 식별한다.
2. 위 옵션 (a)~(c) 외에 다음을 추가한다:
   - **(a') partial 활용 + 좁은 재호출** (Recommended): 잔여 범위만 명시한 새 프롬프트 + 모델 한 단계 다운그레이드(`opus` → `sonnet`, `sonnet` → `haiku`). 프롬프트 첫 줄에 "이미 완료(재작성 금지): …" 를 명시해 중복 작성을 막는다.
3. 다운그레이드는 좁은 잔여 범위에서만 적용한다. 충돌 중재·스키마 결정 같은 "잔여인데 큰 결정" 은 동일 모델을 유지한다.

§2.1 분할 호출 중 소켓 오류는 모델 다운그레이드가 아니라 분할 재시도로 처리한다(§5.5). 본 절의 다운그레이드는 **부분 산출물이 남은 중단**에 한정되며, 사용자 인지 하의 명시 다운그레이드이므로 §5.5 의 silent downgrade 금지와 충돌하지 않는다.

**배경**: 운영 세션에서 tier-2 advisor 호출이 API Internal server error 로 끊긴 사실을 orchestrator 가 사용자에게 즉시 보고하지 않아, 사용자가 직접 끊김을 인지하고 재지시하게 된 사례가 이 절 신설의 직접 계기다.

### 2.6 결함 표면화 시 회귀 단계 판정 (backward re-dispatch)

orchestrator 는 forward 파이프라인(요구사항 → 조사 → 설계 → 구현 → 검증 → 문서화)의 디스패처일 뿐 아니라, **결함이 표면화됐을 때 어느 단계로 되돌아가 바로잡을지 판정하는 역방향 제어의 책임자**다. 이 판정을 생략하고 결함이 드러난 위치에서 국소 패치만 하면, 같은 발원 단계가 만든 동류 결함이 잔존한다. 조율·지휘 담당자의 본분은 forward 디스패치와 backward 회귀 판정 **양방향**을 모두 포함한다.

#### 발동 조건

advisor 산출물 또는 그 하류 산출(report·design·구현)에서 결함이 드러났을 때 — 사용자 지적(§2.3)이든 자체 발견이든 — 아래 절차를 거친다.

#### 절차

1. **발원 단계 진단**: 결함이 *표면화된* 단계가 아니라 결함을 *처음 생성한* 단계를 식별한다. (예: report 의 잘못된 값이라도 발원은 그 값을 만든 조사·설계 단계일 수 있다.)
2. **회귀 + 재디스패치**: 발원 단계의 advisor 를 재호출해 산출물 **전체를 재검·재생성**한다. 결함이 드러난 단일 위치만 고치는 **국소 패치는 발원 단계 = 현재 위치일 때만** 허용한다.
3. **하류 재실행**: 발원 단계 산출이 바뀌면, 그것을 입력으로 삼은 하류 단계(설계·구현 등)를 영향분석 후 재실행하거나 재검한다.
4. **기록**: 진단한 발원 단계·회귀 결정·하류 재실행 범위를 `report.md` 의 `regression` 항목(§8)에 남긴다.

#### 다항목 산출물의 단일 항목 교정 — 전수 재검 동반

목록·표·카탈로그 등 **다항목 산출물에서 한 항목이 결함으로 지적·발견**되면, 그 항목만 제거/수정하고 끝내지 않는다. **동일 출처·동일 생성방식으로 만들어진 나머지 항목이 같은 결함 클래스를 공유하는지 발원 단계에서 전수 재검**한다. 한 항목의 결함은 거의 항상 생성 절차의 결함이며 같은 절차로 만든 다른 항목에 재현된다. (§4.3 집합 전수 체크 AC 가 design 시점의 예방이라면, 본 절은 결함 표면화 이후의 사후 전수 재검이다.)

#### 불확실성 보존 (계층 간 격상 금지)

orchestrator 가 하위 산출(조사 결과 등)을 상위 산출(report·design)로 격상할 때 원본의 hedge·신뢰도 마커를 **보존**한다. "추정/미확인" 을 "확정/실제" 로 바꾸는 격상(uncertainty laundering)은 금지한다 — 하류 단계가 미검증 정보를 권위 있는 전제로 오인해 결함이 증폭된다.

**배경**: 다항목 사실 카탈로그 산출 세션에서, 1차 출처가 차단돼 추정으로 채운 항목들이 상위 보고서에서 "실제 기반" 으로 격상됐고, 사용자가 그중 한 항목의 사실 오류를 지적했으나 동일 출처로 만든 나머지 항목은 재검 없이 해당 항목만 제거된 사례가 본 절 신설의 계기다. 발원 단계(조사) 회귀 대신 표면(목록)에서 국소 패치한 전형이다.

### 2.7 분할 트랙의 설계 게이트 규율 (forward phase-gate)

한 요청이 복수 기능/트랙으로 분해될 때, orchestrator 는 **"요구사항 구체화 → 사전 조사·기획 → 설계 완료 → 그 다음 구현 → 검증"** 척추를 트랙 병렬화로 우회하지 않는다. 핵심은 **독립성을 어느 수준에서 판정하는가**다.

1. **독립성은 공유 자원 수준에서 판정한다.** 기능 명칭이 다르다고 독립이 아니다. 두 트랙이 같은 DB 엔티티·상태 전이·UX 플로우·외부 계약을 건드리면 **결합(coupled)** 으로 간주한다.
2. **결합 트랙은 설계 게이트를 공유한다.** coupled 트랙 중 하나만 먼저 구현 단계로 보내지 않는다. requirements·조사·설계가 **결합 범위 전체**에서 수렴한 뒤 구현에 진입한다. 먼저 구현한 트랙이 건드린 공유 지점을 나중 트랙의 설계가 바꾸면 재작업이 발생한다.
3. **독립이 확인되면 병렬 가능.** 공유 자원이 없음을 실제로 확인했으면 트랙별 병렬 진행은 허용된다(§5.3 독립 영역 병렬과 정합).
4. **결합인데 일부를 먼저 출시해야 하면 사용자 결정.** orchestrator 단독으로 "기능이 독립적이니 먼저 구현" 판정 금지. 어떤 공유 자원이 나중 설계로 바뀔 수 있는지(재작업 리스크)를 명시해 `AskUserQuestion` 으로 위임한다.
5. **research 가 세션 초반 가정을 뒤집으면 설계 진입 전 plan 게이트.** research/조사 산출이 세션 초반 orchestrator 의 가정(seed assumption)을 공식문서 인용으로 뒤집으면, orchestrator 단독으로 반전을 단정·반영하지 않는다. 설계(design-advisor) 진입 **전에** `AskUserQuestion` plan 게이트를 1회 추가해 ① 반전 요약 1줄(가정 → 뒤집힌 결론) ② 옵션(반전 채택 vs 보수적 유지) ③ Recommended ④ 근거(인용 출처) 를 제시하고 사용자 확정을 받는다. seed 가정은 종종 설계 전체의 토대이므로, 검증 없이 자동 반영하면 하류 설계가 미확정 전제 위에 쌓인다.

#### 자가 점검 (트랙 분할 직후, 구현 진입 전)

- 이 트랙이 건드리는 DB 엔티티·상태 전이·플로우를, 아직 설계되지 않은 다른 트랙도 건드리는가? → 예이면 결합. 설계 게이트 공유.
- "독립이다" 판정의 근거가 **기능 명칭 차이**뿐인가? → 그렇다면 공유 자원 수준에서 재판정.
- 조사 산출이 세션 초반 가정과 상충하는가? → 예이면 설계 진입 전 plan 게이트(반전 요약 + 옵션 + Recommended + 근거) 필수. orchestrator 단독 반영 금지.

**배경**: 한 요청을 두 트랙으로 나눈 세션에서, 두 트랙이 동일 상태 전이(한 엔티티의 특정 상태 진입)를 공유하는데도 "기능적으로 독립" 으로 보고 한 트랙을 다른 트랙의 조사·설계 전에 구현 완료한 사례가 있다. 이후 트랙의 설계가 그 공유 전이의 의미를 바꿔 먼저 구현한 트랙이 재작업 대상이 됐다. forward 척추(설계 완료 후 구현)를 트랙 병렬화가 우회한 전형이다.

또한 2026-06-09 세션(20260609-125316)에서 플랫폼 capability 에 대한 seed 가정이 research 의 1차 출처 조사로 뒤집혔다. 이때 단정 대신 plan 게이트로 사용자에게 위임한 것이 항목 5 명문화의 직접 계기다.

### 2.8 플랫폼 capability tier 와 위임 토폴로지

§2 의 호출 모델은 호스트 CLI 의 subagent capability 에 따라 평탄화·격하될 수 있다. 플랫폼 capability tier, 플랫폼별 호출 문법, 격하 트리거의 **권위 정의는 `platform-adapters.md` Layer 1~2** 다.

본 문서에서 말하는 Tier-2/Tier-3 는 advisor 역할 tier 이며, `platform-adapters.md` 의 Tier A/A-flat/B 는 호스트 CLI capability tier 다. 두 축은 직교한다. 코어 프로토콜의 게이트·report 스키마·검증규율은 호출 토폴로지와 독립이므로 어느 capability tier 에서도 동일하게 적용된다.

## 3. 도메인 매핑

| 도메인 | 에이전트 | Tier | 호출 시점 |
|---|---|---|---|
| 요구사항 파악 | `requirements-advisor` | 2 | 세션 초반, 스코프 모호 시 |
| 그래프 검색 | `graphify-lookup-advisor` | 2 | **코드/모듈 구조 조사**의 1차 진입점. 시간축·로드맵·문서 조회는 `docs/` 직접 Read. 상세 선택 기준은 `search-tool-matrix.md` 참조 (graphify 산출물이 있는 프로젝트만) |
| 자료 검색 | `research-advisor` | 3 | graphify 에서 miss 또는 외부 자료 필요 시 |
| 설계 | `design-advisor` | 2 | 요구사항 확정 후, 구현 전 |
| 구현 | `implementation-advisor` | 3 | 설계 승인 후 |
| 검증 | `verification-advisor` | 2 | 구현 완료 후 (구현 경로·diff 접근 차단) |
| 문서화 | `documentation-advisor` | 2 | 작업 중/완료 시 |
| 그래프 갱신 | `graphify-update-advisor` | 2 | 대규모 변경 직후 (`graph-refresh-checker` 판정 수신) |
| 회고 | `retrospective-advisor` | 2 | 세션 종료 직전 |

`graph-refresh-checker` 는 staleness 판정 전용. `graphify-update-advisor` 가 선행 호출한다.

### 3.1 graphify 최초 생성 유예 조건

`graph-refresh-checker` 가 `no-graph` 판정을 내려도, src/ 파일이 존재하는 것만으로 즉시 생성할 필요는 없다. 실질적 판정 기준은 **모듈 간 의미 있는 import 엣지가 존재하는가** 다. 빈 `__init__.py` 만 있는 스캐폴딩 직후처럼 노드만 있고 엣지가 거의 없는 상태에서 graphify 를 실행하면 다음 Phase 에서 바로 재생성해야 하는 낭비가 발생한다.

- **즉시 생성**: src/ 에 비어있지 않은 `.py` 파일이 5개 이상이고, 그 중 최소 2개가 서로 import 관계를 갖는다.
- **유예 허용**: 스캐폴딩 Phase 등 대부분 파일이 빈 `__init__.py` 거나 상호 참조가 거의 없는 경우. 보고서 Open Items 에 "Phase N 진입 후 graphify" 로 이관하고 결정 사유를 Decisions 섹션에 기록한다.
- 이 유예 판정은 orchestrator 의 판단 영역이며, Phase 1 스캐폴딩 세션 유형이 첫 실증 사례.

### 3.2 graph-refresh-checker 호출 조건

`graph-refresh-checker` 는 **scope 대상 경로 내 변경이 있을 때만** 실질적 의미를 갖는다. 호출 전 아래 조건을 확인한다.

- **호출 필요**: `git diff <source_commit>..HEAD -- <scope 대상 경로>` 출력이 비어있지 않은 경우
- **호출 스킵**: 위 명령 출력이 비어있는 경우 → checker 결과를 `skip: no-scope-change` 로 보고서에 기록하고 fresh 취급
- **배경**: docs/, .claude/, *.md 전용 커밋은 코드 scope 의 그래프를 낡게 만들지 않는다. 불필요한 재생성을 줄이기 위해 scope 경로 기준으로 필터링한다.

## 4. 충돌 조정 프로토콜

1. 각 advisor 산출물 프론트매터에 `concerns: []` 필드를 둔다. 자기 도메인 바깥에 영향을 주는 결정은 반드시 여기 기록.
2. Orchestrator 는 모든 advisor 산출물을 수집한 뒤 `concerns` 을 교차해 충돌을 탐지한다.
3. 충돌 감지 시:
   - **2자 충돌**: 두 advisor 에게 서로의 `concerns` 블록만 전달해 1라운드 재검토 요청. 합의 → 종결. 실패 시 4로.
   - **N자 충돌 (3자 이상)**: orchestrator 가 공동 브리핑을 만들어 관련 advisor 들에게 동시에 전달, 1라운드. 실패 시 4로.
4. 1라운드 실패 시 orchestrator 가 근거·대립지점 요약 → **사용자에게 `AskUserQuestion`**. 판단 위임 후 확정.

### 4.1 동결 스펙 vs advisor concerns (후속 세션 파생 변경)

1차 세션에서 기능 스펙이 동결되고 2차(UI/UX·보안·성능 등) 설계 세션이 시작되면, advisor 가 동결 영역(기존 FR/NFR/contracts/DB schema)을 건드리는 신규 요구를 도출하는 경우가 있다. 이를 내부적으로 흡수하면 구현 단계에서 스펙 충돌이 드러나 재작업 비용이 커진다.

- 동결 영역을 건드리는 advisor `concerns` 는 즉시 **C-00X conflict 로 승격** 한다. C 번호는 이전 세션들에서 사용한 번호와 **이어서** 부여 (예: 1차 세션이 C-001~C-003 을 사용했다면 2차는 C-004~).
- `conflicts.md` frontmatter 의 `resolutions` 에 각 C-번호별로 `옵션 A/B/C + recommended + 영향 범위(건드릴 파일·연관 FR)` 를 기술.
- `AskUserQuestion` 헤더에 "동결 파일을 바꾸는 결정" 임을 명시 (예: "DB 스키마 확장") + recommended 를 첫 옵션.
- 해소 후 `conflicts.md` 의 `resolutions[<C-NNN>]` 에 `choice / resolved_at / follow_up[]` 기록. 관련 설계 문서의 frontmatter `concerns` 는 `[C-NNN resolved]` 로 인라인 갱신.
- 해소 결과로 필요한 docs/ 반영은 documentation 단계 또는 orchestrator 마이크로편집으로 처리 (§1 예외).

UI/UX 세션에서 멱등성 관련 C-번호 충돌(예: onboarding 멱등, 자동 기능 on 멱등) 처리가 이 패턴의 1차 실증 사례.

### 4.2 UI/UX 세션 고유 규약

UI/UX 가 포함된 세션(챗봇·CLI·웹 프런트 등 사용자 노출 표면을 설계) 에서는 다음 세 가지가 구조적 실패 지점으로 반복된다. 세션 초기 체크리스트와 선택지 제시 형식에 명시적으로 포함한다.

**4.2.1 형제 프로젝트 UX 벤치마크 (research 선행)**

- 세션 개시 시 orchestrator 는 프로젝트 `CLAUDE.md` 에서 "형제 프로젝트 / 참조 인프라 / 공유 스택" 힌트를 스캔한다. (예: 상위 디렉토리의 형제 프로젝트 경로 언급 등)
- 동일 작성자·동일 조직이 운영 중인 유사 플랫폼 프로젝트가 있으면 **UX/UI 관련 advisor 첫 호출 전** 에 research-advisor 로 해당 프로젝트의 정책(CLAUDE.md, ADR, 주요 UX 파일) 을 조사한다.
- 조사 체크포인트: 톤/어휘·컴포넌트 사용 규약·권한 정책·에러 응답·interaction 만료 대응.
- 기존 `research-first-spec` (외부 라이브러리 인터페이스 검증) 과 구별 — 이쪽은 "운영 중 UX 패턴의 선행 수집". UI/UX v3 설계 세션에서 형제 프로젝트 조사 누락이 1차 오판의 원인이 된 사례가 있다.

**4.2.2 톤 검토와 어휘 검토는 독립 두 축**

- requirements-advisor 또는 design-advisor 가 UI/UX 섹션 작성 시 다음 두 항목을 **분리** 체크:
  1. **톤 체크** — 존댓말/반말, 격식체/반격식체, 이모지 밀도
  2. **어휘 체크** — 사용자 노출 문자열(description, success/error, embed 필드, 자동완성 라벨) 에서
     - 기술 식별자 노출 여부 (`preset_key`, `voice_key`, `f0_method`, `pth_filename` 등)
     - 도메인 전문어·약어 노출 여부 (내부 기술 약어, 업무 전문어 등)
     - 영어 키워드 잔존 여부 (`timeout`, `preset`, `pitch` 등)
- 판정 기준: "이 봇을 처음 쓰는 커뮤니티 멤버" 페르소나. 어휘 치환 후보는 `현재 용어 | 사용 위치 | 권장 치환 | 근거` 표로 requirements 에 기록.

**4.2.3 추천 옵션 제시 시 사용자 편의 비용 대칭 병기**

- conflict 또는 design 선택지에서 "관리 비용 절감" 을 추천 근거로 쓸 때 사용자 편의 손실을 **대칭 항목** 으로 병기한다. 표 형식:

  | 관점 | 추천안 | 대안 |
  |---|---|---|
  | 구현/운영 비용 | 절감 근거 | 증가 근거 |
  | **사용자 편의** | **손실 명시** | **이득 명시** |

- `AskUserQuestion` option `description` 에도 사용자 관점 비용을 1구절 포함. 예: "관리 부담 ↓ / 매번 파라미터 3개 직접 타이핑 필요".
- "UX 단순화" vs "사용자 편의" 가 충돌하는 결정은 비개발자 시나리오 예시 1개를 필수 포함.
- UI/UX 세션의 "컴포넌트 미사용" 유형 오판이 이 원칙 누락의 직접 사례 — 후속 세션에서 C-번호 승격으로 뒤집힌 적이 있음.

### 4.3 Acceptance Criteria 집합 전수 체크 패턴

design-advisor 가 설계 문서의 "검증 포인트" 섹션을 작성할 때, 집합(목록·카테고리·다중 항목)이 포함된 요구사항에는 **개별 항목 AC 대신 전수 체크 AC 1줄**을 추가한다. 상세 규약 및 템플릿은 `agents/design-advisor.md` 의 "집합 전수 체크 AC 패턴" 섹션을 따른다.

**배경**: 2026-05-07 세션(20260507-124344)에서 복사 제외 목록 7건 중 `docs/feedback/archive/` 1건이 AC 에 명시되지 않아 implementation 이 누락해도 verification 에서 FAIL 로 잡히지 않았다. §4.3 은 이 재발 방지 규약이다.

### 4.4 AskUserQuestion 옵션 설계 규약

사용자에게 판단을 위임하는 `AskUserQuestion` 은 옵션 설계 품질이 마찰/라운드 수를 좌우한다. 다음 규약을 지킨다.

1. **결정 축 명시**: 옵션 열거 전에 해당 질문이 묻는 축(axis) 을 한 줄로 기술. 예: "신규 외부 의존성 도입 여부", "결과를 스트리밍 vs 단건 노출".
2. **축 커버 자기검증**: Option A/B/C 가 축의 양 극단과 중간을 덮는지 스스로 점검. 한쪽 편향이면 재설계 후 제시.
3. **의존성 선스캔**: 외부 라이브러리(native/binary/네트워크) 도입이 섞인 옵션을 제시하려면, 사전에 프로젝트의 **의존성 매니페스트**(package.json / pyproject.toml / go.mod 등)를 훑어 기존 대체재가 있는지 확인한다. 있으면 "신규 의존성 0 경로" 를 Recommended 또는 옵션에 포함.
4. **탈출구**: 마지막 옵션으로 "Other/직접 기술" 탈출구를 제공하거나, Recommended 이유를 명시해 사용자가 축을 무시하고 새 방향을 내도 되게 한다.

#### 자가 점검 항목 (제시 전)

1. **의존성 선스캔 완료 확인**: 외부 의존성 도입 옵션이면 매니페스트 스캔 결과를 옵션 설명에 인용.
2. **축 커버 검증 확인**: A/B/C 가 양극+중간을 덮는지 제시 전 점검.
3. **Recommended 근거 명시**: 사용자가 읽지 않아도 선택 가능한 수준의 한 줄 이유.
4. **사용자 명시 언급 자료 포함 확인**: 이번 대화에서 사용자가 직접 URL/라이브러리/도구를 언급했다면 그 선택지를 옵션에서 빼지 말고 동등 비교에 포함하거나 옵션 본문에 배제 근거 한 줄을 기술한다.
5. **표현·총량·인지부담 축 포함 확인**: 결함 후보 multiSelect 등에서 옵션이 모두 데이터/값/구조 축으로만 채워졌는지 점검. 가시성·UI·리포트류 도메인은 "표현 총량(출력 N개·총 라인 L)·스크롤·인지부담" 축이 핵심 결함일 가능성이 큰데 데이터 축에 시선이 쏠려 빠지기 쉽다. 사전 정량 분석에 표현 메트릭도 포함하고, 옵션에 이 축이 1개도 없으면 Other 탈출구 description 에 명시한다.
6. **인용 사실 신선도 확인**: 옵션 본문이 현행 코드/문서/설정 상태(의존성, 환경변수·설정 스키마, 아키텍처 경계 기술, 자동 로드 게이트 문구 등) 를 인용한다면, 옵션 제시 **직전에** Read 또는 grep 으로 실제 파일 상태와 대조한다. 비교형 옵션("현재 → 변경 후") 의 "현재" 부분이 stale 하면 사용자가 옵션 비교 모드 대신 정정 지시 모드로 전환되어 불필요한 라운드가 추가된다.
7. **인접 구현체 인용 완결성 확인**: 옵션이 캐시·스토리지·서비스·레이어 등 구현 계층을 언급한다면, 코드베이스에 동류 구현체가 이미 존재하는지 grep/Read 로 확인한다. 존재한다면 옵션 본문에 "기존 X 패턴을 확장" vs "신규 Y 도입" 을 명시하거나, 계층의 일부만 라벨에 들어간 경우 전체 스택을 한 줄로 인용한다(예: "메모리 + 외부 캐시 + 영속 저장소 다계층 적용"). 자가 점검: "이 옵션 텍스트만 읽은 사람이 코드베이스에 이미 있는 관련 구현체를 알 수 있는가?" — NO 이면 보완 후 제시한다. 6번이 인용된 사실의 정확성을, 7번이 인용 자체의 누락을 잡으므로 두 점검은 상호 보완이다.

### 4.5 clarify 요청 응대 분기

사용자의 clarify 요청은 두 갈래로 해석한다.

- **(a) 내용 clarify** ("A가 무슨 뜻?", "B는 어떤 동작?"): 옵션 의미를 재설명한다.
- **(b) 범위/축 clarify** ("옵션이 좁다", "다른 방향 없나", "이런 거 말고", "왜 X 를 뺐어"): 옵션 자체를 다시 설계해 `AskUserQuestion` 을 한 번 더 보낸다.

(b) 로 판정되면 "무엇을 더 설명할까?" 로 되묻지 않는다. 설계 부담은 orchestrator 가 진다. (b) 신호 어휘가 섞였는지 먼저 판단하고 분기하는 것이 기본값이다. 옵션 배제에 대한 반문("왜 X 를 안 썼어?")도 (b) 로 취급해 동등 비교로 옵션을 1회 재설계한다.

### 4.6 검증 명령·체크리스트는 실행으로만 통과 판정

문서에 포함된 검증 명령(체크리스트의 grep/rg, 스모크 스크립트 등)을 작성·수정·리뷰하는 모든 단계(design / implementation / verification / 외부 reviewer 디스패치)는 그 명령을 **현재 레포 상태에서 실제 실행**하고 기대값(출력 유무·exit code)과 대조한 결과를 산출물에 포함해야 통과 판정할 수 있다. 텍스트 리뷰만으로는 자기매치(패턴이 자신의 명령 줄을 매치), untracked 산출물 오염, glob/escape 차이, exit code 의미 같은 결함 클래스가 보이지 않는다. 자기매치 방지에는 `graphi[f]y` 식 character-class self-exclusion 을 표준 트릭으로 쓴다. (§4.3 이 design 시점 AC 의 전수성 예방이라면, 본 절은 검증 수단 자체의 실행 가능성 예방이다.)

**배경**: 2026-06-10 세션(20260610-103316)에서 release-checklist step-1 의 rg 명령이 자기매치 + untracked 오염으로 커밋 시점부터 기대값 충족이 불가능했으나, opus reviewer 의 문서 리뷰도 미탐지했고 orchestrator 의 실제 실행 검증에서야 발견됐다.

## 5. 모델 선택 정책

에이전트 frontmatter 의 `model:` 필드는 **비워둔다.** Orchestrator 가 호출 시점에 Agent 툴의 `model` 파라미터로 override 한다.

결정은 결정론적이어야 한다. 단계별 파이프라인:

```
phase 기본값 (§5.1) → escalation 트리거 (§5.2) → 디스패치 크기 보정 (§5.3)
                  → 탐색/기계적 성격 오버라이드 (§5.4) → 환경 fallback (§5.5) → 기록 (§5.6)
```

### 5.1 Phase × 기본 모델

| Phase | 기본 모델 | 비고 |
|---|---|---|
| analyze (사용자 발화 분류·근본 원인 탐색) | `opus` | 판단 비용 큼 |
| design / planning | `opus` | trade-off 빈번 |
| code-implementation (스펙 명확) | `sonnet` | 기계적 작성 |
| validation — 정적 체크·타입·테스트 | `sonnet` | rote |
| validation — 런타임·웹·시나리오 | `opus` | 주관적 회귀 판단 |
| docs-sync | `sonnet` | 형식 위주 |
| graphify 실행 | `sonnet` | 도구 실행 |
| graphify 필요성 판단 | `opus` | 메타 판단 |

### 5.2 Escalation 트리거 (1단 상승)

phase 기본값 위에 다음 중 **하나라도** 해당되면 1단 상승. `sonnet` → `opus`, `haiku` → `sonnet`. 상승 사유를 보고서 `escalation_reason` 에 기록.

- 스펙이 모호하거나 `open_questions` 미해소 상태로 진입.
- Phase 도중 **trade-off** 가 드러나는 결정점이 노출됨.
- 보안·인증·권한·결제·**되돌릴 수 없는 데이터 마이그레이션** 영역. §6 파괴적 게이트 발동 작업은 **자동 상승**.
- 검증자가 **주관적 회귀 리스크** 를 판정해야 함.
- Worker 가 고정 타깃을 따르지 않고 **무엇을 들여다볼지 스스로 결정** 해야 함 (탐색적).

### 5.3 디스패치 크기 임계

phase·escalation 결과 위에 크기로 보정. 기존 파일 수 단일축 루브릭(small/medium/large) 은 폐기하고, 파일 수는 보조 신호로만 본다.

| 디스패치 크기 | 처리 경로 | 모델 보정 |
|---|---|---|
| tool calls < 5 + 단일 파일 + 스펙 명확 | orchestrator 직접 (§1 마이크로 편집 예외) | n/a — orchestrator 본 모델로 처리 |
| 5–20 tool calls + 스펙 명확 | worker 디스패치 | `sonnet` 유지 |
| > 20 tool calls 또는 판단 사슬 다단 | worker 디스패치 | `opus` 로 상승 |
| 독립 영역 2–3개 병렬 | 영역별 worker 디스패치 | escalation 미발동 시 모두 `sonnet` |

### 5.4 탐색 vs 기계적 성격 (오버라이드)

Phase 이름만으로 결정하지 말 것. 본 항이 §5.1 과 충돌하면 **본 항 우선**.

- 탐색적·판단 집중·"다음에 무엇을 볼지" 결정형 → **`opus`**.
- 기계적·범위 고정·타깃 명시 → **`sonnet`** (또는 `haiku`).

### 5.5 환경 Fallback

- **확정되지 않은 모델 슬러그를 그대로 넘기지 않는다.** 호출 환경의 whitelist 에 슬러그가 없으면 **parent 모델 상속** 으로 fallback 하고 `fallback_reason` 에 사유 기록.
- **비용 사유로 `opus` → `sonnet` silent 다운그레이드 금지.** `opus` phase 가 환경 미지원이면 **사용자 확인 후** 명시 다운그레이드.
- §2.1 분할 호출 중 소켓 오류 fallback 은 모델 다운그레이드가 아니라 **분할 재시도** 로 처리한다.

### 5.6 기록

모든 호출은 보고서 `invocations[].model_choice` 에 다음을 남긴다:

```yaml
model_choice:
  phase: <analyze|design|code|validation-static|validation-runtime|docs|graphify-exec|graphify-judgment>
  dispatch_size: <direct|small|medium|large|parallel>
  model: <haiku|sonnet|opus>
  escalation_reason: <한 줄 | null>   # §5.2 트리거 적중 시
  fallback_reason: <한 줄 | null>     # §5.5 환경 fallback 시
  rationale: <한 줄>
```

**기본 지침**: 불확실하면 `sonnet` 에서 시작, §5.2 트리거 적중 즉시 `opus` 상승. 비용 하한선 유지하되 §5.5 silent downgrade 금지가 우선.

## 6. 파괴적 조작 게이트

다음 조작은 advisor/worker 가 **직접 수행 금지**. Orchestrator 가 사용자 확인 후에만 실행한다.

- `git push --force`, `git reset --hard`, 브랜치/태그 삭제
- DB drop, TRUNCATE, 마이그레이션 rollback 실행 (작성은 허용, 적용은 금지)
- 파일 대량 삭제 (≥5 파일 또는 디렉토리 통째)
- 외부 시스템으로의 쓰기 호출 (메시지 발송, 외부 API 쓰기, 공개 게시 등)
- `~/.claude/` 전역 설정 수정 (프로젝트 설정은 허용)
- 서드파티에 데이터 업로드 (gist, pastebin 등)

일반적인 `git commit && git push` 의 자동화 여부는 프로젝트 루트 `CLAUDE.md` 의 커밋 정책을 따른다.

### 게이트 통과 후 검증 실패 시 롤백

파괴적 조작이 사용자 승인 후 실행되었고 후속 검증이 실패하면 orchestrator 가 **즉시** 되돌리기를 시도한다 — `git revert`, 파일 복원, migration down 등. 자동 복원이 불가능한 영역(외부 서비스 상태 변경·공개 게시 등) 이면 보고서의 `needs_user_verification` 에 수동 복구 단계를 명시하고 세션을 닫지 않는다.

### 게이트 2단계 분리 원칙

"로컬 파괴"와 "외부 반영"이 시퀀스로 묶인 조작(git 이력 재작성 + force push, 마이그레이션 + 배포, 파일 대량 삭제 + push, 공개 게시 등)은 반드시 게이트를 두 단계로 분리한다.

- **1단계 — 로컬 실행 게이트**: 로컬 실행 결과 preview(변경 요약·커밋 해시·영향 파일) 와 사전 확보된 롤백 경로(백업 브랜치·down migration·파일 백업) 를 option description 에 포함한다.
- **중간 — 자동 검증**: verification-advisor 또는 AC 체크로 1단계 결과가 의도대로인지 확인. 실패하면 2단계 진입 금지 + 자동 롤백.
- **2단계 — 외부 반영 게이트**: 로컬 vs 원격 차이, 연결된 PR/fork 유무, 롤백 가능 여부를 명시한 preview.

단일 게이트로 묶으면 사용자가 복합 리스크를 한 번에 판단해야 하므로 승인률이 낮아지고 오판 가능성이 커진다. 2단계 분리 + 각 단계 preview 제공이 판단 비용을 낮춘다는 실전 사례는 ADR-0001 §5.3 T4(이력 재작성) + 후속 force push 시퀀스에서 검증됨.

> **실전 적용 사례**: ADR-0001 §4, §5.3 (비공개 이력 — 소스 레포 결정 기록) — git 이력 재작성(T4) 및 GitHub repo transfer(T7) 의 이중 파괴적 게이트 절차와 롤백 경로. 2026-05-07 세션(20260507-121142) 에서 T4 + force push 를 2단계 게이트로 분리 승인하여 실제 적용 완료.

## 7. 공유 상태 레이아웃

```
.atp/work-session/<sid>/
├── report.md              # §8 스키마
├── requirements.md        # requirements-advisor 산출
├── research/              # research-advisor 산출 (탐색 결과 묶음)
├── design.md              # design-advisor 산출
├── implementation/        # implementation-advisor 산출 (파일 소유권 맵 + 변경 로그)
├── verification.md        # verification-advisor 산출
├── documentation.md       # documentation-advisor 산출
├── conflicts.md           # advisor 간 충돌 기록
└── artifacts/             # worker 중간 산출물
```

`sid` = ISO 타임스탬프 `YYYYMMDD-HHMMSS` (프로젝트 타임존 기준). 세션 시작 시 orchestrator 가 디렉토리 생성.

### 재개 규약

동일 `sid` 디렉토리가 이미 존재하면 이어쓰지 않고 새 sid 로 시작하되 `report.md` 에 `resumed_from: <이전 sid>` 필드를 기록한다. 이전 보고서의 미완료 섹션은 링크만 남기고 이번 세션에서 재수행.

### 세션 핸드오프 (미래 확장 예약)

장기 세션이 컨텍스트를 초과할 경우 `.atp/work-session/<sid>/handoff.md` 에 다음 세션 인수인계 내용을 기록한다. 포맷:

```yaml
---
continued_from_sid: <prev-sid>
outstanding_decisions: []
pending_invocations: []
blocked_on: <기다리는 것>
---
```

현재는 포맷만 예약. 실제 사용은 필요 시.

## 8. 보고서 스키마 (v1)

```yaml
---
schema_version: 1
session_id: <sid>
resumed_from: <이전 sid | null>   # 동일 sid 디렉토리가 이미 있어 새 sid 로 시작한 경우
started_at: <iso>
ended_at: <iso | null>
user_request: |
  <원문>
---

# Summary
<1-3 문단>

# Invocations
# 시간순. orchestrator 도 자기 주요 판단을 invocation 으로 기록.
- id: inv-001
  layer: orchestrator | advisor | worker
  name: <agent name>
  agent_version: <frontmatter version>
  parent_invocation_id: <id | null>
  started_at / ended_at: <iso>
  input_digest: <요약 1줄>
  output_digest: <요약 1줄>
  artifacts: [path1, path2]
  concerns: []
  model_choice:                # §5.6 스키마
    phase: <...>
    dispatch_size: <direct|small|medium|large|parallel>
    model: <haiku|sonnet|opus>
    escalation_reason: <한 줄 | null>
    fallback_reason: <한 줄 | null>
    rationale: <...>
  token_usage:                 # 추정치 가능
    input: <n>
    output: <n>
  # ── tier-3 advisor 전용 (tier-2 / orchestrator / worker 는 생략 가능) ──
  planned_workers: <n>         # worker spawn 계획 수 (ownership.md 기준)
  actual_workers: <n>          # 실제 spawn 된 worker 수 (0 = advisor 직접 실행)

# Decisions
- by: <advisor name | user>
  at: <iso>
  decision: <...>
  rationale: <...>
  related_invocations: [inv-00X]

# Conflicts
- between: [advisor A, advisor B, ...]
  detected_at: <iso>
  resolved_by: mediation | orchestrator | user
  outcome: <...>

# Open Items
- <...>

# Regression (옵셔널 — §2.6 backward re-dispatch 발동 시)
# 결함이 표면화돼 발원 단계로 회귀한 경우 기록. 국소 패치로 끝낸 경우는 source_stage = surfaced_stage.
- surfaced_at_stage: <결함이 드러난 단계>
  source_stage: <결함을 처음 생성한 단계>
  defect: <한 줄>
  full_set_recheck: <다항목 산출물이면 전수 재검 여부 bool>
  downstream_rerun: [<재실행/재검한 하류 단계>]
  resolved_at: <iso>

# User Signals (옵셔널, 세션 중 orchestrator 가 누적)
# 사용자 발화에서 감지된 긍정/부정 시그널. retrospective-advisor 입력.
user_signals:
  positive:
    - quote_or_paraphrase: <사용자 발화 한 줄>
      about: <어떤 결정/행동에 대한 것인지>
  negative:
    - quote_or_paraphrase: <사용자 발화 한 줄>
      about: <어떤 결정/행동에 대한 것인지>
      structural: true | false

# Retrospective
- signals: { positive: [], negative: [] }   # retro 가 user_signals 를 구조화해 옮김
- what_went_well: []
- what_to_improve: []
- memory_candidates: []       # { name, type, description, body_draft, rationale_for_saving, signal_source, docs_sync_target }
                              # docs_sync_target: 운영·배포·검증 규약성이면 반영해야 할 docs 경로 또는 null
- protocol_feedback: []       # structural 부정 시그널 기반
- applied_changes: []         # MEMORY / SKILL / agent 수정 목록
```

### 진화 규칙

- 필드 추가는 backward-compatible 유지 (옵셔널로 시작).
- 필드 의미 변경·제거는 `schema_version` 올림.
- 기존 세션의 보고서는 소급 수정하지 않는다.

## 9. 확장 트리거 레지스트리

**사후 승격 원칙.** 아래 신호가 관측되면 해당 에이전트/워커를 추가한다. 예측만으로 미리 만들지 않는다.

| 트리거 | 추가 대상 | 행동 |
|---|---|---|
| 독립 테스트 스위트 ≥ 2 or 단일 스위트 런타임 > 수 분 or 산출물 무거움 | `verification-advisor` → tier 3 승격 + 필요 worker(`unit-test-runner` / `browser-test-runner` / `e2e-runner` / `a11y-auditor` 등) | 해당 worker 파일 추가 + advisor tools 에 `Agent` 추가 + `verification-strategies.md` 등록 |
| 설계 검수 요구 정례화 | `design-reviewer` worker | design-advisor tier 3 승격 |
| 문서 링크 깨짐 빈발 or 다중 카테고리 동시 작성 정례화 | `doc-linter` worker, `doc-writer` worker | documentation-advisor tier 3 승격 |
| graph scope ≥ 5 | lookup 병렬 worker | graphify-lookup-advisor tier 3 승격 |
| scope ≥ 3 재생성이 정례화 | `scope-regen` worker | graphify-update-advisor tier 3 승격 |
| 세션 ≥ 10 누적 후 장기 패턴 분석 요구 | `retro-aggregator` advisor 또는 worker | 별도 ADR 고려 |

## 10. MCP / 외부 도구 통합 규칙

- MCP 서버 추가는 호스트 CLI 의 harness 설정 사항이다.
- 새 MCP 툴이 등록되면 **관련 advisor 의 `tools:` 배열을 확장**한다. 구조(tier) 변경은 발생하지 않는다.
- Worker 는 MCP 툴을 원칙적으로 받지 않는다 (격리 유지). 예외는 ADR 로 기록.

## 11. Agent 파일 규약

모든 `agents/*.md` 는 다음 frontmatter 를 따른다:

```yaml
---
name: <kebab-case>
description: <orchestrator 가 호출 판단에 쓰는 한 줄>
tools: <쉼표 구분 목록>        # 필요한 것만 최소
version: 1
peer_agents:                   # 선택. 같은 도메인 로직을 공유하는 에이전트 파일명 목록 (확장자 제외)
  - <kebab-case-name>
  - ...
---
```

`model:` 필드는 넣지 않는다 (orchestrator 오버라이드). 프롬프트 본문에는 반드시 다음 섹션을 포함:

1. **역할** — 이 도메인에서 책임 범위
2. **입력** — orchestrator 가 무엇을 주는지
3. **도구 사용 규칙** — 어떤 도구를 어느 범위로 쓸지
4. **출력 스키마** — 반환값 형식 (파일 경로 + 요약 리포트)
5. **금기** — 인접 도메인 침범 금지 사항
6. **충돌 시** — `concerns` 필드 사용법
7. **자가 검증** — 반환 직전 체크리스트 (§11.2)

파일을 산출하는 advisor 의 frontmatter 에는 `# 산출물 frontmatter 에 반드시 concerns_checked: true 포함` 주석을 둔다 (산출물 frontmatter 와 agent 정의 frontmatter 혼동 방지용 리마인더).

### 11.1 peer_agents 규약

**의미**: `peer_agents` 에 열거된 파일들은 동일 도메인 로직(판정 기준, 입출력 포맷, 처리 흐름)을 공유한다. 한쪽을 수정하면 나머지도 정합성이 깨질 수 있다.

**수정 시 교차 점검 의무**: `peer_agents` 를 가진 파일을 수정할 때는 반드시 peer 파일 전체를 읽고 도메인 로직 정합성을 확인한 뒤 반영한다. 드리프트를 발견하면 **같은 커밋 내에서** 함께 수정한다.

**대칭성 원칙**: A 의 `peer_agents` 에 B 가 있으면 B 의 `peer_agents` 에도 A 가 있어야 한다. 단방향 선언은 정합성 위반. 기계 검증: `grep -l "peer_agents:" plugins/atp/agents/*.md plugins/atp-graphify/agents/*.md` 로 목록 추출 후 교차 확인.

**선택 필드**: `peer_agents` 가 없는 에이전트는 "독립" 으로 간주한다. 과도한 peer 선언은 수정 부담만 늘리므로, 실제 도메인 로직이 공유되는 관계에만 적용한다.

**하위끼리 생략 가능**: 상위-하위(advisor-worker) 관계에서 상위가 여러 하위를 거느릴 때, 상위 ↔ 각 하위는 대칭 선언하되 **하위끼리 직접 peer 선언은 생략 가능**하다. 하위끼리 직접적 도메인 로직 공유가 없고 상위를 경유하는 간접 연결로 충분하면 피어로 묶지 않는다. (예: `implementation-advisor` ↔ `code-writer` / `migration-writer` 는 대칭 선언하지만 `code-writer` ↔ `migration-writer` 는 직접 선언하지 않는다.)

**예시 — graphify 삼중**:

```yaml
# graph-refresh-checker.md
peer_agents:
  - graphify-lookup-advisor
  - graphify-update-advisor

# graphify-lookup-advisor.md
peer_agents:
  - graph-refresh-checker
  - graphify-update-advisor

# graphify-update-advisor.md
peer_agents:
  - graph-refresh-checker
  - graphify-lookup-advisor
```

**배경**: 과거 운영 세션에서 `graphify-lookup-advisor` 의 stale heuristic 이 `graph-refresh-checker` 의 판정 로직과 이원화된 채 방치된 드리프트가 발견됐다. 이 규약은 드리프트 재발 방지용이다.

### 11.2 Advisor / Worker 산출물 자가 검증

모든 advisor 는 산출물을 orchestrator 에 반환하기 **직전에** 다음 항목을 점검한다.

| # | 항목 | 실패 시 |
|---|---|---|
| 1 | 산출물 파일이 `${CLAUDE_PROJECT_DIR}/.atp/work-session/<sid>/` 에 존재 (텍스트 반환형 advisor 는 "반환 블록이 규정 스키마를 따르는가" 로 대체) | 즉시 작성/정정 후 재확인 |
| 2 | frontmatter 필수 필드 (phase, agent, agent_version, generated_at, concerns, concerns_checked) 포함 | 누락 필드 추가 |
| 3 | concerns 의도적 검토 완료 (비어있어도 OK — 검토 사실이 핵심) | `concerns_checked: true` 삽입 |

실패 시 자가 수정 1회 → 여전히 실패면 concerns 에 `self_verification_failed: <항목>` 기록 후 반환한다. 결과는 반환값의 `self_verification.checklist_passed: <bool>` 로 포함한다.

**Worker** 는 산출물을 advisor 에 반환하므로 기준이 다르다 — 2항목으로 축약: (1) 자신이 수정/생성한 파일 경로(read-only worker 는 인용)를 반환에 포함, (2) 담당 범위(파일 소유권·탐색 타겟) 밖을 건드리지 않음.

**구현 advisor 추가 항목 (4번)**: 통합 타입체크는 unused 변수/파라미터를 잡지 못하는 경우가 많으므로, LSP unused 진단 0 또는 프로젝트 린터(예: `eslint --max-warnings=0`, `ruff` 등) 통과를 타입체크와 **별도 게이트**로 점검한다. design 시그니처를 그대로 따른 구현에서 dead parameter 가 발생하기 쉽다(§11 design-advisor 시그니처 inflate 방지 항목과 연계).

## 12. 회고 → MEMORY 반영 절차

1. `retrospective-advisor` 가 세션 보고서를 읽고 `what_to_improve` / `applied_changes` 초안을 산출.
2. Orchestrator 가 그 중 **메모리에 남길 만한 항목** (재현성 있는 교훈) 만 선별.
3. 프로젝트 memory 저장소에 신규 파일 또는 기존 파일 갱신, `MEMORY.md` 인덱스 갱신.
4. 수용한 candidate 에 `docs_sync_target` 이 지정되어 있으면 해당 경로(프로젝트 지침파일 / `docs/development/*.md` / ADR 등) 에도 **같은 커밋에** 반영한다. 내부 작업 흐름 교훈만 MEMORY 단독 보관.
5. 사용자 확인 없이 진행 가능 — 단 파괴적 삭제가 아닌 **추가/수정** 만 허용.

## 13. Phase 완료 아티팩트 기준

세션 종료 조건 (SKILL.md §9) 을 충족해도, **사용자가 세션 직후 곧바로 다음 작업에 진입할 수 있는 실행 가능 상태** 가 아니면 Phase 를 완료로 표시하지 않는다.

- **실행 가능 상태** 의 정의: 엔트리포인트(`uv run python -m <pkg>` / `npm start` 등) 를 실행했을 때 (1) 필수 아티팩트 누락이 아닌 "값 채우세요" 식의 명확한 안내가 나오거나 (2) 기본 설정으로 성공 종료하거나 둘 중 하나.
- **실행 가능 상태가 아닌 예**: `.env.example` 만 있고 `.env` 는 없는 상태에서 프로젝트 엔트리포인트(예: `uv run python -m <pkg>` / `npm start`) 가 `FileNotFoundError` 또는 무안내 실패를 내는 경우. "사용자가 `cp .env.example .env` 후 편집하세요" 는 Phase 완료 기준을 충족하지 않는다 — 플레이스홀더 `.env` 를 orchestrator 가 만들어 두어야 한다.
- **`needs_user_verification` 규약**: 필수 아티팩트에는 "(선택)" 표기 금지. 필수(값을 채워야 실행됨) / 선택(기본값이 있거나 비필수) 를 명시적으로 구분.
- **레퍼런스 파일 vs 진입점 파일 분리**: `.env.example` 같은 레퍼런스는 커밋 대상, `.env` 같은 진입점은 gitignore 대상 + orchestrator 가 Phase 완료 시 생성.

과거 실증 사례: 스캐폴딩 세션이 `.env` 를 만들지 않고 "(선택) .env 채우기" 로 넘긴 것이 "환경 설정이 안 돼 있다" 는 부정 시그널을 유발한 적이 있다. 재세션에서 플레이스홀더 `.env` 를 생성하고 나서야 이 기준이 충족됐다.

## 14. 탐색 도구 선택

탐색/검색 작업에서 어떤 도구를 언제 쓸지는 **`docs/development/search-tool-matrix.md`** 를 따른다.

핵심 원칙:
- 심볼 정의/참조 → **LSP**
- 모듈 연관·군집·아키텍처 패턴 → **graphify** (graph-refresh-checker 선행)
- 로드맵·타임라인·Phase 문서 → **docs/ 직접 Read**
- 키워드·패턴 → **Grep**
- 파일 목록 → **Glob**
- 외부 API → **WebFetch / WebSearch**

각 agent 의 tools 배열은 매트릭스와 일관되게 유지한다. LSP 를 추가하면 해당 agent 가 심볼 정밀 탐색을 직접 수행할 수 있다.

## 관련 문서

- `verification-strategies.md` — verification-advisor 가 읽는 전략 레지스트리 (편집형 — 소비 프로젝트 `docs/development/`, `/atp:init` 생성)
- [documentation-guidelines.md](./documentation-guidelines.md) — 문서 작성 규칙 (번들 레퍼런스)
- [platform-adapters.md](./platform-adapters.md) — 플랫폼 capability tier 와 플랫폼별 명령 문법·경로 어댑터 (Tier 정의 SSoT — §2.8 에서 참조)
- `document-category-classification.md` — 카테고리 분류 기준 (편집형 — 소비 프로젝트 `docs/development/`, `/atp:init` 생성)
