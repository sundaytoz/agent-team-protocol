# 문서 인덱스

**docs-first 워크플로우**: 어떤 작업을 시작하기 전이든 이 파일을 먼저 읽고, 해당 카테고리의 `index.md` 를 거쳐 관련 문서를 확인한 뒤 구현에 착수한다.

> 작성/갱신 규칙과 카테고리 분류 기준은 `development/documentation-guidelines.md` + `development/document-category-classification.md` 를 따른다.

## 카테고리

| 경로 | 용도 | 인덱스 |
| --- | --- | --- |
| [adr/](./adr/index.md) | 되돌리기 어려운 아키텍처/기술 결정 (불변, 번호제) | adr/index.md |
| [analysis/](./analysis/index.md) | 코드/흐름/성능/리스크 분석 | analysis/index.md |
| [architecture/](./architecture/index.md) | 시스템 경계, 레이어 규칙, 저장 구조 | architecture/index.md |
| [backlog/](./backlog/index.md) | 미채택 아이디어, 재검토 트리거 | backlog/index.md |
| [changes/](./changes/index.md) | 실제 동작이 바뀐 구현 변경 이력 | changes/index.md |
| [contracts/](./contracts/index.md) | 외부/내부 계약 스펙 | contracts/index.md |
| [development/](./development/index.md) | 재사용 가능한 개발 규칙/절차/툴 운영 | development/index.md |
| [domain/](./domain/index.md) | 도메인 지식 (프로젝트가 다루는 업무 영역의 규칙·개념) | domain/index.md |
| [issues/](./issues/index.md) | 운영 장애/이슈 대응 기록 | issues/index.md |
| [maintenance/](./maintenance/index.md) | 수동 운영 절차 (마이그레이션/복구/배치) | maintenance/index.md |
| [security/](./security/index.md) | 인증/인가, 입력 검증, 비밀 값 관리 | security/index.md |
| [usage/](./usage/index.md) | 이식자용 사용 가이드·FAQ·체크리스트 | usage/index.md |
| [work-log/](./work-log/index.md) | 세션 간 handoff, 시점성 있는 작업 메모 | work-log/index.md |
| [feedback/](./feedback/index.md) | 검토·수정 요청 캡처 inbox (선택) | feedback/index.md |
| [graph/](./graph/index.md) | **자동 생성** — graphify 산출물 메타 | graph/index.md |

> 프로젝트 성격에 따라 불필요한 카테고리는 제거하거나 새 카테고리를 추가한다. 기준은 `development/document-category-classification.md`.

## 빠른 참조

- **아키텍처 / 구조 파악**: `architecture/` → 부족하면 `graph/index.md` 확인 후 필요 시 `/graphify` 호출
- **이식 후 설정**: `usage/setup-checklist.md` → 문제 발생 시 `usage/faq.md`
- **기술 선택 근거**: `adr/`
- **외부/내부 계약 스펙**: `contracts/`
- **도메인 규칙**: `domain/`
- **장애 이력**: `issues/`

## 작업 시작 체크리스트

- [ ] 이 인덱스에서 관련 카테고리를 식별했는가?
- [ ] 해당 카테고리 `index.md` 를 읽었는가?
- [ ] 구조 탐색이 필요한 작업이라면 `graph/index.md` 의 `last_generated_at` 이 최근인지 확인했는가?
- [ ] 작업 결과로 새 문서가 필요한가? (분류 기준은 `development/document-category-classification.md`)
