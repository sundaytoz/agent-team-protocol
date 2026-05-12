<!-- cp-R 복사 제외. 이식자는 자기 프로젝트의 SECURITY.md 를 독자 작성. -->

# Security Policy

## Scope

본 리포지토리는 **실행 가능한 애플리케이션 코드를 포함하지 않는 문서·템플릿 저장소**다.
보안 취약점 대상은 다음에 한정한다.

- `.claude/agents/**` — 에이전트 정의에서 권한 격리 위반, 파괴적 조작 게이트 우회 경로
- `.claude/skills/**` — 스킬 정의에서 비밀 값·자격 증명이 프롬프트로 삽입될 수 있는 경로
- MCP 도구 노출 범위가 문서화된 원칙과 일치하지 않는 사례
- 문서에 포함된 예시 명령이 이식자 환경에서 파괴적으로 동작할 수 있는 지점

버전 개념은 없다. 리포지토리의 최신 `main` 브랜치만 지원 대상이다.

## Reporting a Vulnerability

주 채널: **GitHub Security Advisory (GHSA)** — https://github.com/sundaytoz/agent-team-protocol/security/advisories/new
보조 채널: stzjungsoo@users.noreply.github.com (GHSA 사용이 어려운 경우에만)

보고 시 다음을 포함해 주시기 바랍니다.

- 영향 받는 파일 경로
- 재현 시나리오 (에이전트 호출 순서·입력 포함)
- 예상 영향 범위 (권한 상승·정보 누출·파괴적 조작 등)

## Response SLA

| 단계 | 목표 |
|---|---|
| Initial response | 72시간 이내 |
| Triage (심각도 판정·수용 여부) | 14일 이내 |
| Resolution (수정 반영 또는 수용 불가 명시) | 90일 이내 |

## Disclosure Policy

조율된 공개(coordinated disclosure) 를 따른다.
수정 반영 또는 완화책 공지 후 GHSA 를 공개 전환한다.
