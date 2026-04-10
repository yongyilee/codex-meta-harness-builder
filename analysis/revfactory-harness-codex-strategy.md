# revfactory/harness -> Codex 변환 전략

작성일: 2026-04-10

## 문서 목적

`analysis/revfactory-harness-analysis.md`의 분석 결과를 바탕으로, Claude 전용 메타 스킬 패키지인 `revfactory/harness`를 **Codex에서 동작하는 meta-harness 제품**으로 전환하기 위한 설계 전략을 정리한다.

## 대상 독자

- 이 저장소에서 실제 구현을 맡을 Codex 에이전트
- meta-harness의 구조와 우선순위를 결정할 설계자
- 하네스 생성 워크플로우를 Codex 환경에 맞게 옮기려는 유지보수 담당자

## 미해결 질문

1. 생성된 Codex 하네스를 repo-local plugin으로 둘지, home-local skill/plugin으로 둘지 기본 정책을 정할 필요가 있다.
2. 생성 결과를 실제 Codex skill로 즉시 활성화할지, 우선 중간 스펙 파일만 생성할지 결정이 필요하다.
3. 여러 프로젝트에서 공통 재사용할 "기본 레퍼런스 묶음"을 어느 수준까지 내장할지 범위를 정해야 한다.

---

## 한줄 전략

`revfactory/harness`를 그대로 포팅하지 말고, **설계 방법론은 유지하고 Claude 전용 런타임 표면만 Codex 네이티브 구성요소로 치환**해야 한다. 결과물은 "프롬프트 패키지"가 아니라, **Codex skill + plugin + scaffold script + 역할 스펙 + 검증 자산**으로 재구성하는 것이 맞다.

---

## 1. 변환 원칙

### 1.1 유지할 것

- Phase 0~7의 상위 워크플로우
- 에이전트/스킬/오케스트레이터/QA의 계층 분리
- 6개 아키텍처 패턴
- Progressive Disclosure
- with-harness vs baseline 검증 방식
- trigger 검증과 반복 개선 루프

### 1.2 교체할 것

- Claude plugin 구조
- `.claude/agents/`, `.claude/skills/`, `CLAUDE.md`
- `TeamCreate`, `SendMessage`, `TaskCreate`
- Claude 전용 skill trigger와 모델 전제

### 1.3 새로 추가할 것

- Codex용 스캐폴딩 스크립트
- Codex 하네스 스펙 파일
- 역할 프롬프트 렌더러
- 검증 실행 스크립트
- `AGENTS.md` 연동 정책

---

## 2. Claude -> Codex 대응표

| Claude 측 개념 | Codex 변환 대상 | 전략 |
|---|---|---|
| `.claude-plugin/plugin.json` | `.codex-plugin/plugin.json` | Codex plugin 구조로 재작성 |
| `skills/harness/SKILL.md` | `skills/meta-harness/SKILL.md` | 메인 오케스트레이터 skill로 포팅 |
| `references/*.md` | `skills/meta-harness/references/*.md` | 거의 그대로 이식하되 Codex 용어로 수정 |
| `.claude/agents/{name}.md` | `generated/<harness>/roles/{name}.md` | Codex 네이티브 agent 파일이 아니라 meta-harness 내부 역할 스펙으로 관리 |
| `.claude/skills/{name}/SKILL.md` | `generated/<harness>/skills/{name}/SKILL.md` | Codex skill 형식으로 생성 |
| `CLAUDE.md` 포인터 | `AGENTS.md` 포인터 | repo 루트 지침 파일에 최소 포인터만 추가 |
| `TeamCreate` | `spawn_agent` | Codex 내장 sub-agent 스폰으로 치환하되, 사용자 요청/권한이 없으면 single-agent로 폴백 |
| `SendMessage` | `send_input` | 명시적 agent-to-agent 메시지 전달 |
| `TaskCreate/TaskUpdate` | 작업 ledger 파일 + runtime state 파일 + 메시지 프로토콜 | 공유 작업 보드는 파일/프로토콜로 구현 |
| `model: "opus"` | 역할별 모델 정책 | 모델/추론 강도를 하드코딩하지 않고 설정화 |

핵심은 `.claude/agents/*.md` 대응물을 "Codex가 자동으로 읽는 파일"로 가정하지 않는 것이다. Codex에는 현재 **사용자 정의 에이전트 파일을 자동 로딩하는 표준**이 보이지 않으므로, 역할 스펙은 meta-harness가 읽어서 `spawn_agent` 호출 프롬프트로 변환해야 한다.

---

## 3. 목표 아키텍처

Codex용 meta-harness는 아래 3층으로 나누는 것이 가장 안정적이다.

### 3.1 설계 레이어

역할:

- 프로젝트 분석
- 도메인 분해
- 팀 구조 선택
- 역할 정의
- skill 초안 설계

구현 형태:

- `skills/meta-harness/SKILL.md`
- `references/*.md`
- 템플릿 렌더링 규칙

### 3.2 생성 레이어

역할:

- 하네스 스펙 파일 생성
- 역할 카드 생성
- Codex skills 생성
- 포인터 파일 갱신

구현 형태:

- `scripts/scaffold_harness.py`
- `templates/`
- `schemas/harness.schema.json`

### 3.3 실행/검증 레이어

역할:

- 생성된 역할 스펙을 바탕으로 agent 스폰
- 단계별 산출물 관리
- baseline 비교
- trigger 평가

구현 형태:

- `scripts/run_eval.py`
- `scripts/check_trigger_fit.py`
- `generated/<harness>/evals/`

---

## 4. 제안 파일 구조

### 4.1 meta-harness 제품 자체

```text
plugins/meta-harness/
├── .codex-plugin/
│   └── plugin.json
├── skills/
│   └── meta-harness/
│       ├── SKILL.md
│       ├── agents/
│       │   └── openai.yaml
│       ├── references/
│       │   ├── codex-agent-patterns.md
│       │   ├── codex-orchestrator-template.md
│       │   ├── codex-team-examples.md
│       │   ├── codex-skill-writing-guide.md
│       │   └── codex-validation-guide.md
│       ├── scripts/
│       │   ├── scaffold_harness.py
│       │   ├── render_role_prompt.py
│       │   ├── run_eval.py
│       │   └── check_trigger_fit.py
│       ├── templates/
│       │   ├── harness_manifest.yaml.j2
│       │   ├── role.md.j2
│       │   ├── skill_SKILL.md.j2
│       │   ├── evals.json.j2
│       │   └── AGENTS.pointer.md.j2
│       └── schemas/
│           └── harness.schema.json
└── assets/
```

### 4.2 생성된 하네스 산출물

```text
generated/<harness-name>/
├── harness.yaml
├── roles/
│   ├── orchestrator.md
│   ├── analyst.md
│   ├── builder.md
│   └── qa.md
├── skills/
│   ├── orchestrate/
│   │   └── SKILL.md
│   ├── analyze/
│   │   └── SKILL.md
│   ├── build/
│   │   └── SKILL.md
│   └── validate/
│       └── SKILL.md
├── evals/
│   ├── evals.json
│   └── baseline/
└── workspace/
    ├── tasks.json
    └── runtime/
        └── agents.json
```

이 구조의 장점은:

- 생성된 결과가 "Codex가 쓸 수 있는 파일"과 "meta-harness가 관리하는 내부 파일"로 분리된다.
- 다른 에이전트가 생성 결과를 바로 읽고 후속 구현을 할 수 있다.
- 검증 자산까지 하네스 패키지에 포함시킬 수 있다.

---

## 5. 핵심 설계 결정

### 5.1 `CLAUDE.md`는 `AGENTS.md`로 치환한다

Codex는 repo 단위 지침 파일로 `AGENTS.md`를 해석하는 관례가 있으므로, Claude의 `CLAUDE.md` 포인터 역할은 `AGENTS.md`가 맡는 것이 맞다.

다만 `revfactory/harness` 1.2.0의 방향성을 유지해야 한다.

- `AGENTS.md`에는 상세 inventory를 넣지 않는다.
- 최소 포인터와 변경 이력만 남긴다.
- 기존 `AGENTS.md` 전체를 재작성하지 않는다.
- meta-harness 전용 섹션만 증분 수정한다.

권장 섹션 예시:

```markdown
## Meta Harness: <domain>

목표: <한 줄 요약>

트리거: <어떤 요청에서 어떤 skill 또는 harness spec을 우선 사용할지>

변경 이력:
| 날짜 | 변경 내용 | 대상 | 사유 |
|---|---|---|---|
```

### 5.2 `.claude/agents/*.md`는 "역할 스펙"으로 바꾼다

Codex에서 커스텀 에이전트 파일을 네이티브하게 로딩한다고 가정하면 설계가 불안정해진다. 따라서 역할 파일은 다음 목적의 **내부 스펙**으로 정의한다.

- 어떤 역할인지
- 어떤 agent_type을 쓸지
- 어떤 모델/추론 강도를 쓸지
- 어떤 산출물을 남길지
- 어떤 상황에서 다른 agent에 메시지를 보낼지

그리고 실행 시 meta-harness가 이 파일을 읽어 `spawn_agent`/`send_input` 호출로 변환한다.

### 5.3 Team 작업 보드는 파일 기반 ledger로 치환한다

Claude의 `TaskCreate/TaskUpdate`는 Codex에 그대로 없다. 따라서 아래 3가지를 조합한다.

- `harness.yaml` 내 작업 정의
- `workspace/tasks.json` 같은 실행 ledger
- `workspace/runtime/agents.json` 같은 runtime state 파일
- `send_input`을 통한 상태 전달

즉 "공유 작업 보드"는 네이티브 기능이 아니라 **명시적 데이터 파일 + 메시지 규약**으로 구현한다.

`update_plan`은 오케스트레이터가 사용자에게 진행 상태를 보여주기 위한 보조 도구일 뿐, 하네스 내부의 공유 상태 저장소로 쓰면 안 된다.

### 5.4 모델 정책은 하드코딩하지 않는다

Claude판의 `model: "opus"`는 Codex에서 그대로 유지할 필요가 없다.

권장 정책:

- 오케스트레이터: 상위 모델 + 중~고 추론
- 탐색형 역할: `explorer` 또는 경량 모델
- 코드 수정형 역할: `worker` + codex 계열 모델
- 검증형 역할: 탐색형 또는 worker, 작업 성격에 따라 선택

이를 `harness.yaml`이나 role spec에 설정 가능한 정책으로 둔다.

### 5.5 skill trigger는 유지하되, 실행 스크립트 중심으로 보강한다

Codex skills도 `name`과 `description` 기반 트리거 구조를 갖지만, 실제 재현성과 자동성을 높이려면 스크립트가 필요하다.

즉:

- "언제 skill이 트리거되는가"는 description으로 제어
- "실제로 무엇이 생성되는가"는 script/template로 제어
- generated `SKILL.md`는 YAML frontmatter를 포함해야 한다
- frontmatter에는 최소 `name`, `description`을 넣고, body에는 workflow, output contract, constraints를 분리한다

이 이중 구조가 필요하다.

### 5.6 Codex 실행 제약을 전제로 설계한다

현재 Codex 환경에서는 `spawn_agent` 사용이 항상 자유로운 것이 아니다. 따라서 meta-harness는 아래 두 층을 분리해야 한다.

- **하네스 설계/생성 층**
  - 언제나 실행 가능해야 한다.
  - 역할 정의, skill 생성, eval skeleton 생성, `AGENTS.md` 포인터 생성까지 담당한다.
- **하네스 실행 층**
  - 사용자 요청이 명시적으로 delegation/sub-agent/team 실행을 포함할 때만 `spawn_agent` 경로를 사용한다.
  - 그렇지 않으면 single-agent 폴백 모드로 동작하거나, 실행 대신 generated harness만 남긴다.

즉 meta-harness의 기본 성공 조건은 "항상 멀티에이전트를 실행한다"가 아니라, **항상 하네스를 생성할 수 있고, 실행 가능할 때만 delegation을 붙인다**여야 한다.

---

## 6. 구현 단계

### 단계 1. 스펙 우선 정리

가장 먼저 해야 할 일은 "무엇을 생성할지"를 YAML/JSON schema로 고정하는 것이다.

필수 스키마 항목:

- harness 메타데이터
- 도메인 설명
- 실행 패턴
- 역할 목록
- 역할별 agent_type / model policy / outputs
- 생성할 skills 목록
- eval 시나리오
- `AGENTS.md` 포인터 정보

권장 산출물:

- `schemas/harness.schema.json`
- `templates/harness_manifest.yaml.j2`

### 단계 2. 레퍼런스 문서 Codex 용어로 포팅

`revfactory/harness`의 reference 문서 중 재사용 가치가 높은 것을 먼저 옮긴다.

우선순위:

1. `agent-design-patterns.md`
2. `orchestrator-template.md`
3. `skill-writing-guide.md`
4. `skill-testing-guide.md`
5. `qa-agent-guide.md`

이 단계에서는 Claude 용어를 아래처럼 모두 치환한다.

- Claude Code Plugin -> Codex plugin
- TeamCreate -> spawn strategy
- SendMessage -> agent message handoff
- TaskCreate -> task ledger protocol
- CLAUDE.md -> AGENTS.md

### 단계 3. 스캐폴딩 엔진 구현

스캐폴더는 최소한 아래를 생성해야 한다.

- `generated/<harness-name>/harness.yaml`
- `roles/*.md`
- `skills/*/SKILL.md`
- `evals/evals.json`
- 필요 시 `AGENTS.pointer.md` 초안

여기서 중요한 점:

- 첫 버전은 템플릿 렌더링만 해도 충분하다.
- Codex 실제 실행 로직은 다음 단계에서 붙인다.
- 즉 MVP는 "생성 가능한 하네스 패키지"다.
- generated `skills/*/SKILL.md`는 우선 **portable skill bundle**로 생성한다.
- 즉시 auto-discovery 되는 설치형 skill인지, 단순 generated artifact인지는 별도 install 단계에서 결정한다.

### 단계 4. 오케스트레이터 skill 구현

`skills/meta-harness/SKILL.md`는 다음 일을 하게 해야 한다.

1. 프로젝트 감사
2. 기존 하네스 여부 판별
3. 도메인 분석
4. 실행 패턴 선택
5. 스키마 채우기
6. scaffold script 호출
7. 결과 검토

즉 Codex skill은 직접 모든 파일을 손으로 쓰는 게 아니라, **분석과 의사결정**을 맡고, 파일 생성은 스캐폴더가 맡는 구조가 바람직하다.

### 단계 5. 실행 및 검증 루프 구현

이 단계에서 "정말 하네스처럼 동작하는가"를 붙인다.

최소 검증 항목:

- generated skill frontmatter 검증
- role spec 누락 검증
- baseline 대비 개선 실험 구조 생성
- should-trigger / should-NOT-trigger 시나리오 생성
- role prompt 렌더링 테스트

### 단계 6. 샘플 하네스 1종으로 끝까지 검증

문서만 포팅하고 끝내면 실패한다. 반드시 하나의 도메인으로 끝까지 검증해야 한다.

권장 샘플:

- 코드 리뷰 하네스
- 문서 생성 하네스
- 리서치 하네스

이 셋 중 하나를 택해:

- spec 생성
- scaffold 생성
- `AGENTS.md` 포인터 생성
- eval 자산 생성

까지 완료해야 전략이 실제 제품으로 내려앉는다.

---

## 7. MVP 범위

첫 구현은 아래 범위로 제한하는 것이 좋다.

### MVP에 포함

- Codex plugin 1개
- meta-harness skill 1개
- 핵심 reference 4~5개
- scaffold script 1개
- `harness.yaml` schema 1개
- 기본 템플릿 묶음
  - `harness_manifest.yaml.j2`
  - `role.md.j2`
  - `skill_SKILL.md.j2`
  - `evals.json.j2`
  - `AGENTS.pointer.md.j2`
- eval skeleton 생성
- `AGENTS.md` 포인터 업데이트 로직

### MVP에서 제외

- 랜딩 페이지 이식
- Marketplace 노출
- 고급 자동 최적화 루프
- 다중 도메인 전용 템플릿 과도한 내장
- 복잡한 GUI

즉 첫 버전은 "잘 생성되는가"에 집중하고, "예쁘게 배포되는가"는 미룬다.

---

## 8. 리스크와 대응

### 리스크 1. Codex에 커스텀 에이전트 개념이 없어서 설계가 흔들릴 수 있다

대응:

- 역할 파일을 네이티브 설정이 아닌 내부 스펙으로 정의
- 모든 실행은 `spawn_agent` 호출 시점에 렌더링

### 리스크 2. `AGENTS.md`를 과도하게 오염시킬 수 있다

대응:

- 포인터 섹션만 유지
- inventory는 `generated/<harness>/harness.yaml`이 진실의 원천
- 기존 `AGENTS.md`는 patch 방식으로만 수정

### 리스크 3. 문서만 많고 자동성은 약한 상태로 끝날 수 있다

대응:

- 반드시 scaffold script를 MVP에 포함
- 수작업 생성 비중을 낮춤

### 리스크 4. trigger 품질이 낮아 실제로 skill이 잘 안 불릴 수 있다

대응:

- should-trigger / should-NOT-trigger eval을 초기에 포함
- description 문구를 문서가 아니라 실험 데이터로 조정

### 리스크 5. 멀티에이전트 협업이 task board 없이 불안정할 수 있다

대응:

- 파일 기반 ledger 도입
- 역할별 산출물 경로를 강제
- handoff 프로토콜을 role spec에 명시

---

## 9. 추천 구현 순서

다른 에이전트가 구현한다면 아래 순서를 권장한다.

1. `plugins/meta-harness/.codex-plugin/plugin.json` 스캐폴딩
2. `skills/meta-harness/SKILL.md` 초안 작성
3. `schemas/harness.schema.json` 정의
4. `templates/*.j2` 작성
5. `scripts/scaffold_harness.py` 구현
6. reference 문서 Codex 포팅
7. `AGENTS.md` 포인터 패치 로직 구현
8. `scripts/run_eval.py` 골격 구현
9. 샘플 하네스 1종 생성 및 검증

이 순서의 장점은:

- 문서만 있고 엔진이 없는 상태를 빨리 벗어난다.
- 생성 산출물 포맷을 먼저 고정할 수 있다.
- 이후 skill과 validation이 산출물 중심으로 정리된다.

---

## 10. 완료 기준

다음 조건을 만족하면 "revfactory/harness의 Codex 변환 1차 성공"으로 볼 수 있다.

- Codex plugin으로 설치 가능한 최소 구조가 있다.
- meta-harness skill이 프로젝트 분석 후 scaffold script를 호출할 수 있다.
- 생성 결과로 `harness.yaml`, `roles/*.md`, `skills/*/SKILL.md`, `evals/`가 나온다.
- `AGENTS.md`에 최소 포인터를 증분 반영할 수 있다.
- 샘플 하네스 1종이 baseline 대비 비교 가능한 eval 골격을 만든다.
- 역할 스펙이 실제 `spawn_agent` 호출 프롬프트로 변환 가능하다.

---

## 11. 최종 제안

이 프로젝트는 "Claude용 하네스를 Codex 문법으로 번역"하는 작업이 아니라, **Claude의 하네스 설계 철학을 Codex의 실행 모델 위에 재구현**하는 작업으로 정의해야 한다.

따라서 구현 방향은 아래처럼 잡는 것이 맞다.

- 문서 포팅만 하지 말고 스캐폴더를 함께 만든다.
- `.claude/agents`의 개념은 Codex 내부 역할 스펙으로 재정의한다.
- `CLAUDE.md`는 `AGENTS.md` 포인터 전략으로 대체한다.
- 멀티에이전트 협업은 `spawn_agent` + `send_input` + task ledger 프로토콜로 재구성한다.
- MVP는 "잘 생성되는 하네스 패키지"에 집중하고, 고급 자동화는 2차로 미룬다.

이 전략을 따르면 `revfactory/harness`의 가장 큰 장점인 **설계 방법론, 검증 루프, 진화 가능한 구조**를 잃지 않으면서도, Codex 환경에 맞는 실체를 만들 수 있다.
