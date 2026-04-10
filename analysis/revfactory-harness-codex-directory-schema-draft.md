# revfactory/harness -> Codex 초기 디렉터리/스키마 초안

작성일: 2026-04-10

## 문서 목적

Codex용 meta-harness의 초기 디렉터리 구조와 핵심 스키마 초안을 정의한다. 이 문서는 실제 구현 전에 **폴더 구조, 파일 책임, 데이터 계약**을 먼저 고정하기 위한 설계 초안이다.

## 대상 독자

- meta-harness의 scaffold engine을 구현할 에이전트
- schema/template를 먼저 설계할 에이전트
- generated output의 구조를 검수할 리뷰어

## 미해결 질문

1. `plugins/meta-harness/`를 저장소 내부 표준 위치로 고정할지 결정이 필요하다.
2. generated 하네스를 저장소 내부 `generated/`에 둘지, 대상 프로젝트 루트에 직접 배치할지 정책 확정이 필요하다.
3. `harness.yaml`을 최종 진실의 원천으로 둘지, JSON schema 검증용 별도 manifest를 둘지 결정이 필요하다.

---

## 1. 디렉터리 설계 원칙

- meta-harness 제품 자체와 generated 하네스를 분리한다.
- 사람이 읽는 설계 문서와 기계가 읽는 스키마를 분리한다.
- 역할 스펙, generated skill, eval 자산은 각각 독립 디렉터리를 가진다.
- `AGENTS.md`에는 inventory를 넣지 않고 generated spec이 진실의 원천이 되게 한다.

---

## 2. 제품 루트 디렉터리 초안

권장 초기 구조는 아래와 같다.

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
│       │   ├── codex-validation-guide.md
│       │   └── codex-qa-guide.md
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

### 디렉터리별 책임

| 경로 | 책임 |
|---|---|
| `.codex-plugin/` | Codex plugin 메타데이터 |
| `skills/meta-harness/` | 오케스트레이터 skill 본체 |
| `references/` | 필요 시만 읽는 상세 설계 문서 |
| `scripts/` | 재현 가능한 생성/검증 엔진 |
| `templates/` | generated output 텍스트 원형 |
| `schemas/` | 기계 검증 가능한 데이터 계약 |
| `assets/` | 향후 공통 템플릿, 샘플 자산 |

---

## 3. generated 하네스 디렉터리 초안

generated 하네스는 아래처럼 분리하는 것을 권장한다.

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
│   ├── trigger/
│   ├── baseline/
│   └── iterations/
└── workspace/
    ├── tasks.json
    ├── artifacts/
    ├── logs/
    └── runtime/
        └── agents.json
```

### generated 구조의 의도

- `harness.yaml`
  - generated 하네스의 단일 진실 원천
- `roles/`
  - 내부 역할 정의
  - 실행 시 `spawn_agent` 프롬프트로 렌더링되는 원본
- `skills/`
  - 실제 Codex skill 포맷 산출물
- `evals/`
  - 하네스 품질 검증 자산
- `workspace/`
  - 실행 중 생성되는 중간 산출물과 작업 ledger

---

## 4. `harness.yaml` 초안

### 4.1 역할

`harness.yaml`은 generated 하네스 전체를 설명하는 중심 파일이다.

담아야 할 것:

- 하네스 메타데이터
- 도메인
- 패턴
- 역할 구성
- skill 구성
- eval 정책
- `AGENTS.md` 포인터 정책

### 4.2 초안 예시

```yaml
version: 0.1

harness:
  name: code-review-harness
  display_name: Code Review Harness
  description: >
    코드 리뷰 작업을 위해 아키텍처, 보안, 성능, 테스트 관점의 역할을
    조합해 결과를 통합하는 Codex 하네스
  domain: software-engineering
  owner_mode: repo-local
  generated_at: 2026-04-10

execution:
  pattern: fanout-fanin
  runtime_mode: single
  delegation_policy: on-user-request
  task_ledger_path: workspace/tasks.json
  artifact_root: workspace/artifacts

context:
  target_paths:
    - .
  readme_paths:
    - README.md
  instruction_files:
    - AGENTS.md

roles:
  - id: orchestrator
    title: Review Orchestrator
    kind: coordinator
    agent_type: default
    model: gpt-5.4
    reasoning_effort: high
    inputs:
      - user_request
      - repository_context
    outputs:
      - workspace/artifacts/final-review.md
    responsibilities:
      - 역할 배치
      - 결과 통합
      - 위험 우선순위 정렬
    handoff:
      can_spawn:
        - architecture-reviewer
        - security-reviewer
        - performance-reviewer
        - test-reviewer
      can_message:
        - architecture-reviewer
        - security-reviewer
        - performance-reviewer
        - test-reviewer

  - id: architecture-reviewer
    title: Architecture Reviewer
    kind: specialist
    agent_type: explorer
    model: gpt-5.4-mini
    reasoning_effort: medium
    inputs:
      - repository_context
      - selected_diff
    outputs:
      - workspace/artifacts/architecture-review.md
    responsibilities:
      - 구조적 리스크 식별
      - 설계 일관성 검토
    handoff:
      can_message:
        - orchestrator

skills:
  - id: orchestrate
    path: skills/orchestrate/SKILL.md
    purpose: 하네스 전체 실행
    trigger_keywords:
      - comprehensive code review
      - parallel review
      - review harness

  - id: analyze
    path: skills/analyze/SKILL.md
    purpose: 분석 역할 공통 절차

  - id: validate
    path: skills/validate/SKILL.md
    purpose: 결과 검증 및 요약

eval:
  enabled: true
  baseline_mode: no-harness
  trigger_checks:
    should_trigger_min: 8
    should_not_trigger_min: 8
  iterations_dir: evals/iterations

agents_pointer:
  target_file: AGENTS.md
  section_title: Meta Harness: code-review-harness
  update_mode: patch
  append_history: true
```

---

## 5. `harness.schema.json` 항목 초안

아래는 JSON Schema로 반드시 고정해야 할 최상위 필드다.

### 5.1 최상위 구조

```json
{
  "type": "object",
  "required": [
    "version",
    "harness",
    "execution",
    "context",
    "roles",
    "skills",
    "eval",
    "agents_pointer"
  ]
}
```

### 5.2 필드 정의 초안

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `version` | string | 필수 | manifest 버전 |
| `harness` | object | 필수 | 하네스 메타데이터 |
| `execution` | object | 필수 | 실행 패턴, 작업 ledger, artifact 경로 |
| `context` | object | 필수 | 분석 시 읽을 파일/경로 |
| `roles` | array | 필수 | 역할 정의 목록 |
| `skills` | array | 필수 | 생성할 skill 목록 |
| `eval` | object | 필수 | 평가 정책 |
| `agents_pointer` | object | 필수 | `AGENTS.md` 패치 전략 |

### 5.3 `harness` 오브젝트

```json
{
  "type": "object",
  "required": ["name", "display_name", "description", "domain", "owner_mode"],
  "properties": {
    "name": { "type": "string", "pattern": "^[a-z0-9-]+$" },
    "display_name": { "type": "string" },
    "description": { "type": "string" },
    "domain": { "type": "string" },
    "owner_mode": { "type": "string", "enum": ["repo-local", "generated", "user-home"] },
    "generated_at": { "type": "string", "format": "date" }
  }
}
```

### 5.4 `execution` 오브젝트

```json
{
  "type": "object",
  "required": ["pattern", "runtime_mode", "delegation_policy", "task_ledger_path", "artifact_root"],
  "properties": {
    "pattern": {
      "type": "string",
      "enum": [
        "sequential",
        "fanout-fanin",
        "router",
        "review-loop"
      ]
    },
    "runtime_mode": {
      "type": "string",
      "enum": ["single", "delegated", "hybrid"]
    },
    "delegation_policy": {
      "type": "string",
      "enum": ["on-user-request", "always-if-allowed", "disabled"]
    },
    "task_ledger_path": { "type": "string" },
    "artifact_root": { "type": "string" }
  }
}
```

### 5.5 `roles` 아이템

```json
{
  "type": "object",
  "required": [
    "id",
    "title",
    "kind",
    "agent_type",
    "model",
    "reasoning_effort",
    "inputs",
    "outputs",
    "responsibilities"
  ],
  "properties": {
    "id": { "type": "string", "pattern": "^[a-z0-9-]+$" },
    "title": { "type": "string" },
    "kind": { "type": "string", "enum": ["coordinator", "specialist", "executor", "validator"] },
    "agent_type": { "type": "string", "enum": ["default", "explorer", "worker"] },
    "model": { "type": "string" },
    "reasoning_effort": {
      "type": "string",
      "enum": ["low", "medium", "high", "xhigh"]
    },
    "inputs": {
      "type": "array",
      "items": { "type": "string" }
    },
    "outputs": {
      "type": "array",
      "items": { "type": "string" }
    },
    "responsibilities": {
      "type": "array",
      "items": { "type": "string" }
    },
    "handoff": {
      "type": "object",
      "properties": {
        "can_spawn": {
          "type": "array",
          "items": { "type": "string" }
        },
        "can_message": {
          "type": "array",
          "items": { "type": "string" }
        }
      }
    }
  }
}
```

### 5.6 `skills` 아이템

```json
{
  "type": "object",
  "required": ["id", "path", "purpose"],
  "properties": {
    "id": { "type": "string" },
    "path": { "type": "string" },
    "purpose": { "type": "string" },
    "trigger_keywords": {
      "type": "array",
      "items": { "type": "string" }
    }
  }
}
```

### 5.7 `eval` 오브젝트

```json
{
  "type": "object",
  "required": ["enabled", "baseline_mode"],
  "properties": {
    "enabled": { "type": "boolean" },
    "baseline_mode": { "type": "string" },
    "iterations_dir": { "type": "string" },
    "trigger_checks": {
      "type": "object",
      "required": ["should_trigger_min", "should_not_trigger_min"],
      "properties": {
        "should_trigger_min": { "type": "integer", "minimum": 0 },
        "should_not_trigger_min": { "type": "integer", "minimum": 0 }
      }
    }
  }
}
```

### 5.8 `agents_pointer` 오브젝트

```json
{
  "type": "object",
  "required": ["target_file", "section_title", "update_mode"],
  "properties": {
    "target_file": { "type": "string", "enum": ["AGENTS.md"] },
    "section_title": { "type": "string" },
    "update_mode": { "type": "string", "enum": ["patch", "append", "replace-section"] },
    "append_history": { "type": "boolean" }
  }
}
```

---

## 6. 역할 스펙 Markdown 초안

`roles/*.md`는 Codex 네이티브 agent 설정이 아니라 internal role spec이다. 아래 형태를 권장한다.

```markdown
---
id: architecture-reviewer
title: Architecture Reviewer
kind: specialist
agent_type: explorer
model: gpt-5.4-mini
reasoning_effort: medium
---

# Architecture Reviewer

## 목적
- 구조적 리스크 식별
- 설계 계층 불일치 탐지

## 입력
- repository_context
- selected_diff

## 출력
- workspace/artifacts/architecture-review.md

## 책임
- 모듈 경계 검토
- 의존성 방향 점검
- 변경 파급 범위 요약

## handoff
- orchestrator 에게 결과 전달
- 필요 시 security-reviewer 와 교차 검토 요청
```

---

## 7. generated skill 초안

generated skill은 일반 Codex skill 형식을 따른다.

```markdown
---
name: code-review-analyze
description: 코드 리뷰 하네스의 분석 역할에서 공통적으로 사용하는 절차. 변경 범위 파악, 파일 우선순위 정렬, 핵심 리스크 후보 정리를 수행한다.
---

# Code Review Analyze

## Quick Start

1. 변경 파일 목록을 수집한다.
2. 위험도가 높은 파일을 먼저 정렬한다.
3. 역할별 검토 포인트를 분리한다.

## 출력 규약

- 결과를 `workspace/artifacts/*.md`에 저장한다.
- 추정은 `가정 필요`로 표시한다.
```

즉 generated `SKILL.md`는 최소한 다음을 만족해야 한다.

- YAML frontmatter에 `name`, `description` 포함
- body에는 Quick Start 또는 Workflow, 출력 규약, 제약을 분리
- generated portable bundle이라는 점을 본문에 명시

---

## 8. `evals/evals.json` 초안

검증 자산은 최소 아래 구조를 가져야 한다.

```json
{
  "version": "0.1",
  "target_harness": "code-review-harness",
  "trigger_evals": {
    "should_trigger": [
      "이 저장소에 대해 병렬 코드 리뷰 하네스를 구성해줘",
      "보안, 성능, 테스트 관점으로 나눠서 리뷰하는 하네스가 필요해"
    ],
    "should_not_trigger": [
      "현재 브랜치 변경 파일만 간단히 요약해줘",
      "README 오타만 수정해줘"
    ]
  },
  "baseline": {
    "mode": "no-harness"
  }
}
```

---

## 9. `AGENTS.md` 포인터 초안

`AGENTS.md`는 아래처럼 최소 섹션만 추가하는 것을 권장한다.

```markdown
## Meta Harness: code-review-harness

목표: 병렬 코드 리뷰 하네스를 사용해 구조, 보안, 성능, 테스트 관점의 검토를 통합한다.

트리거: 포괄적 코드 리뷰 하네스 구성, 병렬 리뷰 하네스 생성, 역할 분해 기반 리뷰 요청 시 generated/code-review-harness 를 우선 참조한다.

변경 이력:
| 날짜 | 변경 내용 | 대상 | 사유 |
|---|---|---|---|
| 2026-04-10 | 초기 포인터 등록 | generated/code-review-harness | meta-harness 생성 |
```

---

## 10. 초기 구현 시 고정해야 할 규칙

- generated 루트 아래 파일은 모두 상대경로 기준으로 서로 연결한다.
- `AGENTS.md` 포인터는 항상 저장소 루트 기준으로 추가한다.
- role id와 skill id는 소문자 하이픈 케이스로 고정한다.
- 역할 출력 경로는 반드시 `workspace/artifacts/` 아래로 제한한다.
- eval 자산은 `evals/` 아래로만 생성한다.
- generated skill은 self-contained description을 가져야 한다.
- runtime agent id 매핑은 `workspace/runtime/agents.json`에 저장한다.
- `runtime_mode: delegated` 또는 `hybrid`는 실제 실행 시 사용자 요청/권한이 있을 때만 사용한다.
- generated skill은 우선 portable bundle이며, 자동 활성화는 별도 install 단계가 필요할 수 있다.

---

## 11. 바로 구현 가능한 최소 세트

지금 바로 코드로 옮긴다면 최소 아래 일곱 개를 먼저 고정하면 된다.

1. `schemas/harness.schema.json`
2. `templates/harness_manifest.yaml.j2`
3. `templates/role.md.j2`
4. `templates/skill_SKILL.md.j2`
5. `templates/evals.json.j2`
6. `templates/AGENTS.pointer.md.j2`
7. `scripts/scaffold_harness.py`

이 일곱 개가 있으면:

- 하네스 입력 계약이 생기고
- 역할 문서가 렌더링 가능하고
- generated skill/eval/pointer까지 한 번에 맞출 수 있고
- generated tree를 만들 수 있고
- 이후 skill/reference/eval 문서를 점진적으로 붙일 수 있다.
