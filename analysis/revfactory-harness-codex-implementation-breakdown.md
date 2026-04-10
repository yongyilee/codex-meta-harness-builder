# revfactory/harness -> Codex 구현작업 분해

작성일: 2026-04-10

## 문서 목적

`analysis/revfactory-harness-codex-strategy.md`를 실제 구현 가능한 작업 단위로 분해한다. 이 문서는 다른 에이전트가 곧바로 작업을 시작할 수 있도록 **작업 패키지, 선후관계, 산출물, 완료 기준**을 명확히 정의하는 데 목적이 있다.

## 대상 독자

- meta-harness를 실제 구현할 Codex 에이전트
- 구현 순서와 범위를 통제할 설계자
- 작업 배정과 검수를 맡을 리뷰어

## 미해결 질문

1. 구현 위치를 현재 저장소 루트 기준으로 할지, `plugins/meta-harness/` 하위로 제한할지 결정이 필요하다.
2. 초기 버전에서 실제 `spawn_agent` 실행까지 포함할지, 우선 scaffold 생성까지만 포함할지 범위를 확정해야 한다.
3. 샘플 하네스 1종을 어떤 도메인으로 잡을지 결정이 필요하다.

---

## 1. 구현 목표

이번 1차 구현의 목표는 다음이다.

- Codex에서 설치 가능한 최소 meta-harness plugin 구조를 만든다.
- meta-harness skill이 프로젝트 분석 후 하네스 스펙을 생성할 수 있게 한다.
- 스캐폴더가 역할 스펙, generated skills, eval skeleton을 생성하게 한다.
- `AGENTS.md`에 최소 포인터를 증분 반영할 수 있게 한다.
- 샘플 하네스 1종에 대해 end-to-end로 생성 결과를 검증할 수 있게 한다.

즉 이번 단계의 성공 기준은 "하네스 개념을 설명하는 문서"가 아니라, **실제로 생성 가능한 Codex 하네스 골격을 확보하는 것**이다.

---

## 2. 작업 분해 원칙

작업은 아래 원칙으로 나눈다.

- 구조를 먼저 고정하고 문서를 덧붙인다.
- 문서보다 스키마와 템플릿을 먼저 만든다.
- 수작업 생성보다 scaffold 자동화를 우선한다.
- Claude 용어 치환은 문서만이 아니라 파일 구조와 스크립트에도 반영한다.
- 검증 자산은 후순위가 아니라 MVP 일부로 포함한다.

---

## 3. 상위 워크패키지

### WP1. 제품 골격 스캐폴딩

목적:

- Codex plugin/skill 제품의 물리적 구조를 만든다.

주요 작업:

- `plugins/meta-harness/.codex-plugin/plugin.json` 생성
- `plugins/meta-harness/skills/meta-harness/` 기본 디렉터리 생성
- `plugins/meta-harness/skills/meta-harness/references/`, `scripts/`, `templates/`, `schemas/` 폴더 생성
- 최소 `agents/openai.yaml` 골격 생성

산출물:

- plugin root 구조
- 비어 있지 않은 최소 manifest

선행 조건:

- 없음

완료 기준:

- Codex plugin/skill 기본 구조가 디스크에 존재
- 각 디렉터리의 역할이 README 없이도 구조상 구분 가능

### WP2. 하네스 스펙 정의

목적:

- "무엇을 생성할지"를 schema 레벨에서 먼저 고정한다.

주요 작업:

- `harness.schema.json` 설계
- `harness.yaml` 초안 설계
- role spec 포맷 정의
- eval spec 포맷 정의

산출물:

- `schemas/harness.schema.json`
- `templates/harness_manifest.yaml.j2`
- role/eval 샘플 스펙

선행 조건:

- WP1

완료 기준:

- 하네스 생성 결과를 schema로 검증 가능한 상태
- 역할, skill, eval, 포인터 정보가 빠짐없이 표현 가능

### WP3. 템플릿 시스템 구축

목적:

- 하네스 산출물을 일관된 포맷으로 생성할 수 있게 한다.

주요 작업:

- `role.md.j2`
- `skill_SKILL.md.j2`
- `AGENTS.pointer.md.j2`
- 필요 시 `evals.json.j2`

산출물:

- 생성용 템플릿 세트

선행 조건:

- WP2

완료 기준:

- schema 입력만으로 주요 산출물 텍스트가 렌더링 가능
- 수작업 후처리가 최소화됨

### WP4. 스캐폴더 구현

목적:

- 하네스 정의를 입력받아 generated 패키지를 실제로 생성한다.

주요 작업:

- `scripts/scaffold_harness.py` 작성
- 입력 검증
- 디렉터리 생성
- 템플릿 렌더링
- generated outputs 저장

산출물:

- 실행 가능한 scaffold script

선행 조건:

- WP2
- WP3

완료 기준:

- `harness.yaml` 또는 equivalent input을 받아 generated tree 생성 가능
- 동일 입력에 대해 재현 가능한 출력 생성

### WP5. meta-harness skill 작성

목적:

- Codex가 meta-harness를 적절한 상황에서 트리거하고, 스캐폴더를 호출하도록 만든다.

주요 작업:

- `skills/meta-harness/SKILL.md` 작성
- description 최적화
- Phase 0~7을 Codex 용어로 포팅
- scaffold script 호출 절차 기술

산출물:

- 오케스트레이터 skill 본문

선행 조건:

- WP1
- WP2

완료 기준:

- skill이 "언제 쓰는지"와 "무엇을 하는지"를 모두 설명
- 생성 엔진과 문서가 분리되어 있음
- delegation이 불가능한 상황에서 single-agent 폴백 또는 generated-output-only 모드를 설명함

### WP6. reference 포팅

목적:

- `revfactory/harness`의 핵심 설계 문서를 Codex 용어로 치환해 재사용한다.

주요 작업:

- `agent-design-patterns.md` 포팅
- `orchestrator-template.md` 포팅
- `skill-writing-guide.md` 포팅
- `skill-testing-guide.md` 포팅
- `qa-agent-guide.md` 포팅

산출물:

- Codex 전용 reference 문서 세트

선행 조건:

- WP1

완료 기준:

- Claude 전용 표면이 문서에서 제거됨
- `spawn_agent`, `send_input`, `AGENTS.md`, task ledger 개념 반영

### WP7. `AGENTS.md` 연동

목적:

- 생성된 하네스를 repo instruction 체계와 연결한다.

주요 작업:

- `AGENTS.md` 포인터 섹션 포맷 정의
- 기존 `AGENTS.md` patch 전략 정의
- 변경 이력 행 생성 규칙 정의

산출물:

- 포인터 템플릿
- patch/update 로직

선행 조건:

- WP3
- WP4

완료 기준:

- 기존 `AGENTS.md`를 파괴하지 않고 meta-harness 섹션 추가 가능
- 포인터 전략이 `revfactory/harness` 1.2.0 방향성과 일치

### WP8. 검증 골격 구축

목적:

- 생성된 하네스의 품질을 반복 측정할 기반을 만든다.

주요 작업:

- `scripts/run_eval.py` 골격 작성
- `scripts/check_trigger_fit.py` 골격 작성
- `evals/evals.json` 포맷 정의
- with-harness / baseline 디렉터리 규약 정의

산출물:

- 최소 검증 러너와 eval skeleton

선행 조건:

- WP2
- WP4

완료 기준:

- eval 디렉터리 구조 자동 생성 가능
- should-trigger / should-NOT-trigger 시나리오를 저장하고 읽을 수 있음
- runtime state 파일(`workspace/runtime/agents.json`) 구조를 함께 정의함

### WP9. 샘플 하네스 1종 적용

목적:

- 설계가 실제 생성 흐름에서 성립하는지 검증한다.

주요 작업:

- 샘플 도메인 선택
- `harness.yaml` 샘플 작성
- scaffold 실행
- 생성 결과 검토
- 누락 필드/템플릿/포인터 전략 보정

산출물:

- generated sample harness

선행 조건:

- WP4
- WP5
- WP8

완료 기준:

- 샘플 하네스 한 개가 generated tree를 끝까지 생성
- 역할 스펙, generated skill, eval skeleton, `AGENTS.md` 포인터가 모두 생성됨

---

## 4. 권장 구현 순서

아래 순서대로 진행하는 것이 가장 안전하다.

1. WP1 제품 골격 스캐폴딩
2. WP2 하네스 스펙 정의
3. WP3 템플릿 시스템 구축
4. WP4 스캐폴더 구현
5. WP5 meta-harness skill 작성
6. WP6 reference 포팅
7. WP7 `AGENTS.md` 연동
8. WP8 검증 골격 구축
9. WP9 샘플 하네스 적용

이 순서를 추천하는 이유는:

- 생성 엔진 없는 문서 더미 상태를 피할 수 있다.
- schema와 template가 먼저 있어야 문서와 구현이 어긋나지 않는다.
- `AGENTS.md` 연동과 eval은 generated output이 나온 뒤에 붙이는 게 안정적이다.
- `spawn_agent` 실행은 사용자 요청/권한 제약을 받으므로, 실행 엔진보다 generated harness 산출물을 먼저 완성하는 편이 안전하다.

---

## 5. 작업 단위별 파일 터치 범위

| 워크패키지 | 주 파일 | 비고 |
|---|---|---|
| WP1 | `.codex-plugin/plugin.json` | plugin 메타데이터 |
| WP1 | `skills/meta-harness/agents/openai.yaml` | UI metadata |
| WP2 | `schemas/harness.schema.json` | 핵심 계약 |
| WP2 | `templates/harness_manifest.yaml.j2` | generated spec |
| WP3 | `templates/role.md.j2` | 역할 스펙 |
| WP3 | `templates/skill_SKILL.md.j2` | generated skill |
| WP3 | `templates/evals.json.j2` | eval skeleton |
| WP3 | `templates/AGENTS.pointer.md.j2` | 포인터 |
| WP4 | `scripts/scaffold_harness.py` | 생성 엔진 |
| WP5 | `skills/meta-harness/SKILL.md` | 메인 skill |
| WP6 | `references/*.md` | Codex 포팅 문서 |
| WP7 | `scripts/scaffold_harness.py` 또는 별도 patch helper | AGENTS 반영 |
| WP8 | `scripts/run_eval.py` | eval runner |
| WP8 | `scripts/check_trigger_fit.py` | trigger validator |
| WP9 | `generated/<sample>/...` | 샘플 출력 |

---

## 6. 각 워크패키지의 완료 기준

### 최소 완료 기준

- WP1~WP4 완료 시:
  - "하네스를 생성할 수 있는 엔진"이 존재해야 한다.

- WP5~WP7 완료 시:
  - "Codex가 meta-harness를 이해하고 repo 지침과 연결할 수 있는 구조"가 있어야 한다.

- WP8~WP9 완료 시:
  - "생성된 하네스가 유효한지 반복 측정할 수 있는 루프"가 있어야 한다.

### 실패로 간주할 상태

- skill 문서만 있고 scaffold script가 없는 상태
- schema 없이 템플릿만 존재하는 상태
- generated output은 생기지만 `AGENTS.md` 연동이 없는 상태
- eval 구조가 없어 품질 회귀를 잡을 수 없는 상태

---

## 7. 에이전트 배정 권장안

병렬 작업이 가능하다면 아래처럼 나누는 것이 좋다.

### 담당 A. 스펙/템플릿 축

담당 범위:

- WP2
- WP3

적합한 역할:

- schema 설계형
- 문서/템플릿 정합성 검토형

### 담당 B. 스캐폴더/검증 축

담당 범위:

- WP4
- WP8

적합한 역할:

- Python 스크립트 구현형
- 생성/검증 자동화형

### 담당 C. skill/reference 축

담당 범위:

- WP5
- WP6
- WP7

적합한 역할:

- skill authoring
- Codex instruction 체계 이해

### 담당 D. 샘플 하네스 적용 축

담당 범위:

- WP9

적합한 역할:

- end-to-end 검증형
- 산출물 품질 검토형

---

## 8. 구현 시 주의점

- `AGENTS.md`는 절대 전체 재작성하지 않는다.
- role spec 파일을 Codex 네이티브 설정으로 오해하지 않는다.
- `update_plan`을 공유 작업 보드로 설계하지 않는다.
- generated skill과 meta-harness 자기 자신의 skill을 섞지 않는다.
- generated skill은 우선 portable output으로 보고, 설치/활성화는 별도 단계로 분리한다.
- template와 generated output 사이의 경계를 명확히 둔다.
- eval은 나중에 붙이는 부가 기능이 아니라 최소 제품 일부로 본다.

---

## 9. 바로 다음 액션

이 문서를 기준으로 바로 구현에 들어간다면 첫 작업은 아래 셋 중 하나여야 한다.

1. `schemas/harness.schema.json` 초안 작성
2. `templates/harness_manifest.yaml.j2`와 `templates/role.md.j2` 초안 작성
3. `scripts/scaffold_harness.py`의 입력/출력 계약부터 고정

가장 추천하는 시작점은 1번이다. 스키마가 고정되어야 이후 문서, 템플릿, 스크립트가 흔들리지 않는다.
