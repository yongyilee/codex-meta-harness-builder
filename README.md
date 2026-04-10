# meta-harness

`meta-harness`는 사용자 프롬프트나 구조화된 brief를 받아 Codex용 하네스 번들을 생성하는 프로젝트다. `revfactory/harness`의 설계 철학과 이 저장소의 [`analysis`](./analysis) 문서를 바탕으로, Claude 전용 개념을 Codex 환경에 맞는 `plugin + skill + scaffold CLI + eval skeleton`으로 번역하는 데 초점을 맞춘다.

## 목표

- 프롬프트를 하네스 스펙으로 정규화한다.
- 역할 스펙, generated skill, eval skeleton, `AGENTS.md` 포인터를 재현 가능하게 생성한다.
- Codex skill로 등록 가능한 plugin 구조를 유지하되, 실제 로직은 `src/` 아래 패키지로 관리한다.

## 현재 범위

- `src/meta_harness/`
  - brief 정규화
  - manifest 모델/검증
  - YAML/Markdown/JSON 렌더링
  - 하네스 스캐폴딩
  - trigger-fit / eval summary 생성
- `plugins/meta-harness/`
  - Codex plugin manifest
  - `SKILL.md`
  - wrapper scripts
  - schema / template / reference docs
- `tests/`
  - schema, template, scaffold, skill metadata 검증

## 빠른 시작

```powershell
python -m pip install -e .
python -m pip install -r requirements-dev.txt
python plugins/meta-harness/skills/meta-harness/scripts/scaffold_harness.py `
  --brief-file examples/code-review-brief.json `
  --output-dir generated `
  --patch-agents
```

생성 결과는 기본적으로 `generated/<harness-name>/` 아래에 놓인다.

## brief 예시

샘플 입력은 [`examples/code-review-brief.json`](./examples/code-review-brief.json) 에 있다. 핵심 필드는 다음과 같다.

- `name`
- `domain`
- `summary`
- `focus_areas` 또는 `roles`
- `target_paths`
- `should_trigger`
- `should_not_trigger`

역할을 모두 직접 쓰지 않아도 `focus_areas`만 주면 orchestrator, specialist/worker, quality gate를 자동으로 파생한다.

## Codex skill 등록 관점

이 저장소는 plugin/skill을 바로 배치할 수 있게 유지한다.

- plugin root: [`plugins/meta-harness`](./plugins/meta-harness)
- skill entry: [`plugins/meta-harness/skills/meta-harness/SKILL.md`](./plugins/meta-harness/skills/meta-harness/SKILL.md)
- 실제 구현: [`src/meta_harness`](./src/meta_harness)

즉, skill bundle은 Codex가 읽기 좋은 형태를 유지하고, 구현 변경은 `src`에서 진행한 뒤 wrapper를 통해 노출한다.

## 검증

```powershell
pytest
python plugins/meta-harness/skills/meta-harness/scripts/run_eval.py --harness-dir generated/code-review-harness
python plugins/meta-harness/skills/meta-harness/scripts/check_trigger_fit.py --harness-dir generated/code-review-harness
```

## 참고 자료

- 원본 아이디어: `https://github.com/revfactory/harness`
- 로컬 분석 문서:
  - [`analysis/revfactory-harness-analysis.md`](./analysis/revfactory-harness-analysis.md)
  - [`analysis/revfactory-harness-codex-strategy.md`](./analysis/revfactory-harness-codex-strategy.md)
  - [`analysis/revfactory-harness-codex-directory-schema-draft.md`](./analysis/revfactory-harness-codex-directory-schema-draft.md)
  - [`analysis/revfactory-harness-codex-implementation-breakdown.md`](./analysis/revfactory-harness-codex-implementation-breakdown.md)
