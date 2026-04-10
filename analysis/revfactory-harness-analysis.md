# revfactory/harness 분석

작성일: 2026-04-10

## 한줄 요약

`revfactory/harness`는 "Claude에서 하네스를 자동 생성해주는 코드 생성기"라기보다, **Claude Code가 새로운 에이전트 팀과 스킬 묶음을 설계하도록 유도하는 메타 스킬 패키지**다. 핵심 구현은 프로그램 코드가 아니라 `SKILL.md`와 여러 reference 문서에 들어 있는 **설계 규칙, 템플릿, 검증 절차**다.

즉, 이 저장소의 본질은:

- 런타임 엔진 구현체가 아니다.
- Claude 전용 하네스 설계 방법론과 프롬프트 자산 모음이다.
- 산출물도 실행 바이너리나 라이브러리가 아니라 `.claude/agents/`, `.claude/skills/`, `CLAUDE.md` 같은 **설정성 Markdown 파일**이다.

---

## 1. 저장소 구조 요약

핵심 파일은 많지 않다.

```text
harness/
├── .claude-plugin/plugin.json
├── skills/harness/SKILL.md
├── skills/harness/references/
│   ├── agent-design-patterns.md
│   ├── orchestrator-template.md
│   ├── team-examples.md
│   ├── skill-writing-guide.md
│   ├── skill-testing-guide.md
│   └── qa-agent-guide.md
├── README.md
├── CHANGELOG.md
├── index.html
└── privacy.html
```

실질적인 "제품 로직"은 거의 전부 `skills/harness/` 아래에 몰려 있다.

---

## 2. 핵심 구성요소별 역할

### 2.1 `.claude-plugin/plugin.json`

플러그인 메타데이터만 담는다.

- 이름: `harness`
- 버전: `1.2.0`
- 설명: Agent Team & Skill Architect

여기에는 생성 로직이 없다. 설치/식별용 매니페스트다.

### 2.2 `skills/harness/SKILL.md`

이 저장소의 실제 중심이다.

이 문서는 Claude에게 다음을 하라고 지시한다.

1. 현재 프로젝트의 하네스 상태를 감사한다.
2. 필요한 팀 아키텍처를 선택한다.
3. 에이전트 정의 파일을 만든다.
4. 에이전트가 쓸 스킬을 만든다.
5. 오케스트레이터 스킬과 `CLAUDE.md` 포인터를 만든다.
6. 생성 결과를 테스트하고 반복 개선한다.

즉, `SKILL.md` 자체가 "하네스를 만드는 오케스트레이터 프롬프트"다.

### 2.3 `references/*.md`

이 파일들은 생성 규칙의 상세 매뉴얼이다.

- `agent-design-patterns.md`
  - 팀 vs 서브에이전트 vs 하이브리드 실행 모드
  - 6개 아키텍처 패턴
  - 에이전트 분리 기준
- `orchestrator-template.md`
  - 오케스트레이터 스킬 템플릿
  - 팀 모드/서브에이전트 모드/하이브리드 모드 예시
- `team-examples.md`
  - 리서치, 소설, 웹툰, 코드리뷰, 마이그레이션 팀 예시
- `skill-writing-guide.md`
  - 스킬 description 작성법
  - Progressive Disclosure 설계
  - output schema 규칙
- `skill-testing-guide.md`
  - with-skill vs baseline 비교
  - assertion 기반 채점
  - trigger 검증
- `qa-agent-guide.md`
  - QA 에이전트를 어떻게 설계해야 하는지
  - 특히 "경계면 불일치" 검증을 강조

### 2.4 `README.md`, `CHANGELOG.md`

문서와 릴리즈 기록이다.

특히 `CHANGELOG.md`는 이 프로젝트가 단순 정적 템플릿이 아니라 **하네스 운영 모델 자체를 빠르게 진화**시키고 있다는 점을 보여준다.

### 2.5 `index.html`

랜딩 페이지다. 설치/홍보용 프론트엔드이며, 하네스 생성 메커니즘의 핵심은 아니다.

---

## 3. 이 저장소가 실제로 "자동 생성"하는 방식

이 프로젝트의 자동화는 전통적인 의미의 코드 자동화가 아니다.

### 작동 방식

1. 사용자가 Claude에게 "Build a harness for this project" 같은 요청을 한다.
2. Claude가 `harness` 스킬을 트리거한다.
3. `SKILL.md`의 단계별 지시에 따라 프로젝트를 분석한다.
4. Claude가 직접 `.claude/agents/*`, `.claude/skills/*`, `CLAUDE.md`를 작성한다.

즉, 저장소 자체가 파일을 생성하는 스크립트를 실행하는 게 아니라:

- Claude가 이 문서를 읽고
- 문서에 적힌 규칙을 따라
- 대상 프로젝트 안에 파일들을 생성하는 구조다.

따라서 이 저장소는 **생성기(generator)** 보다는 **생성 지침(specification + prompt package)** 에 가깝다.

---

## 4. 핵심 워크플로우

`SKILL.md` 기준 워크플로우는 현재 7단계다.

### Phase 0: 현황 감사

- 기존 `.claude/agents/`, `.claude/skills/`, `CLAUDE.md`를 읽음
- 신규 구축 / 기존 확장 / 운영·유지보수로 분기
- drift(실제 파일과 문서 간 불일치) 탐지

이 단계가 있다는 점이 중요하다. 이 프로젝트는 처음 생성만 다루지 않고 **이미 존재하는 하네스를 증분 수정**하는 흐름도 다룬다.

### Phase 1: 도메인 분석

- 사용자 요청에서 도메인 파악
- 작업 유형 식별
- 기존 에이전트/스킬과 충돌 여부 검토
- 코드베이스 탐색
- 사용자 숙련도 추정

### Phase 2: 팀 아키텍처 설계

- Agent Teams를 기본 모드로 간주
- 필요 시 Sub-agents 또는 Hybrid 선택
- 6가지 패턴 중 적합한 구조 선택

### Phase 3: 에이전트 정의 생성

- 모든 에이전트를 `.claude/agents/{name}.md` 파일로 생성
- 역할, 원칙, 입력/출력 프로토콜, 에러 핸들링, 협업 규칙 명시
- 팀 모드일 경우 팀 통신 프로토콜까지 작성

### Phase 4: 스킬 생성

- 각 에이전트가 사용할 `.claude/skills/{name}/SKILL.md` 생성
- 필요 시 `references/`, `scripts/`, `assets/` 구조도 함께 설계
- description을 "pushy"하게 써서 트리거 확률을 높이도록 유도

### Phase 5: 통합 및 오케스트레이션

- 오케스트레이터 스킬 작성
- 에이전트 간 데이터 흐름과 에러 처리 규칙 정의
- `CLAUDE.md`에는 상세 설정이 아니라 **포인터와 변경 이력만** 남김

### Phase 6: 검증 및 테스트

- 구조 검증
- 실행 모드 검증
- with-skill vs without-skill 비교
- should-trigger / should-NOT-trigger 테스트
- dry run 테스트

### Phase 7: 하네스 진화

- 사용자 피드백 수집
- 피드백 유형별 수정 대상 결정
- 변경 이력 기록
- 반복 실패 패턴이 보이면 하네스 자체를 진화시킴

---

## 5. 실행 모델 분석

이 저장소는 Claude의 협업 메커니즘을 전제로 설계되어 있다.

### 5.1 기본 모드: Agent Teams

문서상 기본값은 Agent Teams다.

주요 전제:

- `TeamCreate`
- `SendMessage`
- `TaskCreate` / `TaskUpdate`

이 조합을 통해 팀원 간 직접 통신과 공유 작업 보드를 활용한다.

핵심 철학은:

- 2명 이상이 협업하면 팀이 기본이다.
- 팀원 간 직접 메시지 교환이 품질을 높인다.
- 리더를 거치지 않는 상호 검증이 중요하다.

### 5.2 대안 모드: Sub-agents

서브에이전트는 다음 상황에서만 권장된다.

- 팀 통신이 구조적으로 불필요
- 결과만 메인에 반환하면 충분
- 오버헤드를 줄이는 게 더 중요

즉 이 저장소는 **서브에이전트를 기본값으로 놓지 않는다**.

### 5.3 하이브리드 모드

최근 버전에서 강화된 영역이다.

예:

- 자료 수집은 병렬 서브에이전트
- 통합은 팀 모드
- 최종 QA는 단일 서브에이전트

이 점은 Codex용 meta-harness를 만들 때도 그대로 가져갈 가치가 높다.

---

## 6. 설계 철학

### 6.1 에이전트와 스킬의 분리

이 저장소는 다음 분리를 강하게 밀고 있다.

- 에이전트 = "누가 할 것인가"
- 스킬 = "어떻게 할 것인가"

그래서 모든 에이전트를 파일로 정의하게 하고, 스킬은 재사용 가능한 절차 지식으로 설계한다.

### 6.2 Progressive Disclosure

컨텍스트 최적화를 매우 중요하게 본다.

3단계 로딩 모델:

- metadata: 항상 로드
- `SKILL.md`: 스킬 트리거 시 로드
- `references/`: 필요할 때만 로드

즉, 하네스를 "작게 유지하고 필요할 때만 확장"하는 구조다.

### 6.3 검증 중심 설계

하네스 생성 자체보다, 생성된 하네스가 실제로 유용한지 검증하는 절차가 강하다.

특히:

- baseline 대비 improvement 측정
- trigger precision/recall 검증
- 반복 개선 루프

이 부분은 단순 프롬프트 템플릿 저장소와 가장 큰 차이점이다.

---

## 7. QA 가이드가 특히 중요한 이유

`qa-agent-guide.md`는 단순 QA 체크리스트가 아니다. 이 저장소가 어떤 버그를 중요하게 보는지 드러낸다.

핵심 메시지:

- QA는 "존재 확인"보다 "경계면 비교"를 해야 한다.
- API와 프론트, 상태전이 맵과 실제 업데이트 코드, 파일 경로와 링크 경로를 동시에 읽어야 한다.
- 정적 타입 통과만으로는 충분하지 않다.

이는 Codex용 meta-harness에서도 그대로 중요한 원칙이다.

특히 코드 생성/검증 하네스에서는:

- 모듈 단독 정합성보다 인터페이스 정합성이 더 위험하다.
- QA 에이전트는 읽기 전용 탐색자가 아니라 교차 검증 가능한 작업자여야 한다.

---

## 8. 변경 이력에서 읽히는 방향성

`CHANGELOG.md`를 보면 최근 변화 방향이 분명하다.

### 8.1 초기 1.0.x

- 6단계 기반 하네스 생성
- 팀 패턴, 스킬 작성, 테스트 방법론 정립

### 8.2 1.1.0

- Phase 0 감사 도입
- 기존 하네스 확장/운영 시나리오 도입
- `CLAUDE.md`와의 동기화 강화
- 하네스를 "운영 가능한 시스템"으로 보기 시작

### 8.3 1.2.0

- `CLAUDE.md`를 상세 문서가 아니라 포인터로 축소
- 하이브리드 실행 모드 강화
- 중복 제거 및 구조 단순화

즉 프로젝트는 점점:

- 상세한 중앙 문서화보다
- 실제 파일 구조를 진실의 원천으로 두고
- 오케스트레이터는 최소 포인터만 남기는 방향으로 진화 중이다.

이 방향은 Codex에서도 유효하다.

---

## 9. Codex용 meta-harness 관점에서 재사용 가능한 부분

### 거의 그대로 가져갈 수 있는 것

- Phase 0~7의 상위 워크플로우
- 에이전트/스킬 분리 원칙
- Progressive Disclosure
- 6개 아키텍처 패턴
- 하네스 진화 루프
- trigger 검증 / baseline 비교 아이디어
- QA의 경계면 검증 철학

### Codex에 맞게 치환해야 하는 것

- `.claude/agents/`, `.claude/skills/`, `CLAUDE.md`
- `TeamCreate`, `SendMessage`, `TaskCreate`
- Claude의 skill trigger 메커니즘
- `model: "opus"` 전제
- Claude 플러그인/마켓플레이스 설치 구조

즉 재사용 단위는 "코드"가 아니라 **아키텍처와 생성 프로세스**다.

---

## 10. Codex용 meta-harness 관점에서 한계

이 저장소를 그대로 옮겨서는 Codex용 자동 하네스가 되지 않는다.

### 한계 1. 실행 엔진이 없다

실제 스캐폴딩 스크립트나 AST 기반 생성기가 없다. Claude가 문서를 읽고 수동으로 파일을 쓰는 모델이다.

### 한계 2. Claude 고유 개념에 깊게 묶여 있다

- agent teams
- team messaging
- task board
- CLAUDE.md pointer
- Claude skill description trigger

이 부분은 Codex 환경에 맞는 다른 추상화가 필요하다.

### 한계 3. 산출물이 Markdown 중심이다

실행 가능한 코드 자산보다 에이전트 정의와 절차 문서가 중심이다.

즉 Codex에서 "자동 구성"을 더 강하게 하려면 다음이 추가되어야 한다.

- 템플릿 파일 세트
- 스캐폴딩 로직
- 환경별 매핑 규칙
- 검증 스크립트

---

## 11. meta-harness 설계에 대한 시사점

`revfactory/harness`를 분석하고 나면, Codex용 meta-harness는 아래 두 층으로 나누는 게 합리적이다.

### 1층: 방법론 레이어

이 저장소에서 거의 그대로 차용 가능하다.

- 요구 분석
- 팀 구조 선택
- 에이전트/스킬 역할 설계
- 오케스트레이션 규칙
- 검증 루프

### 2층: Codex 실행 레이어

새로 만들어야 한다.

- Codex용 하네스 디렉터리 규약
- 에이전트 정의 파일 형식
- 스캐폴딩 스크립트
- 템플릿 렌더링
- Codex 도구 체계와의 연결

즉 이 저장소는 Codex meta-harness의 "정답 코드"라기보다는, **설계 철학과 생성 프로세스의 좋은 레퍼런스**다.

---

## 12. 결론

`revfactory/harness`의 강점은 실제 실행 코드가 아니라 **LLM이 스스로 전문 에이전트 팀을 설계하고, 파일 단위 하네스를 생성하고, 다시 검증하고, 진화시키게 만드는 운영 모델**에 있다.

Codex용 meta-harness를 만들 때 가장 가치 있는 자산은 다음 세 가지다.

1. 하네스를 한 번 만드는 산출물이 아니라 지속 운영·개선되는 시스템으로 본다.
2. 에이전트, 스킬, 오케스트레이터, QA를 분리된 계층으로 설계한다.
3. 생성보다 검증과 진화 루프를 더 강하게 설계한다.

반대로 그대로 재사용하기 어려운 영역은 Claude 전용 인터페이스와 파일 규약이다. 따라서 Codex용 구현에서는 이 저장소를 **프롬프트 패키지로 복제**하기보다, **아키텍처 청사진으로 번역**하는 접근이 맞다.

---

## 참고한 원본 파일

- `https://github.com/revfactory/harness`
- `https://github.com/revfactory/harness/blob/main/.claude-plugin/plugin.json`
- `https://github.com/revfactory/harness/blob/main/skills/harness/SKILL.md`
- `https://github.com/revfactory/harness/blob/main/skills/harness/references/agent-design-patterns.md`
- `https://github.com/revfactory/harness/blob/main/skills/harness/references/orchestrator-template.md`
- `https://github.com/revfactory/harness/blob/main/skills/harness/references/team-examples.md`
- `https://github.com/revfactory/harness/blob/main/skills/harness/references/skill-writing-guide.md`
- `https://github.com/revfactory/harness/blob/main/skills/harness/references/skill-testing-guide.md`
- `https://github.com/revfactory/harness/blob/main/skills/harness/references/qa-agent-guide.md`
- `https://github.com/revfactory/harness/blob/main/CHANGELOG.md`
