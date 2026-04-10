# meta-harness Code Review And Test Report

작성일: 2026-04-10

## 범위

- 기획 기준선
  - `analysis/revfactory-harness-codex-strategy.md`
  - `analysis/revfactory-harness-codex-directory-schema-draft.md`
  - `analysis/revfactory-harness-codex-review-test-plan.md`
- 구현 검토 대상
  - `src/meta_harness/*.py`
- 테스트 검토 대상
  - `tests/`
  - `plugins/meta-harness/skills/meta-harness/schemas/harness.schema.json`
  - `plugins/meta-harness/skills/meta-harness/templates/*.j2`

## 요약 판정

- 코드리뷰 판정: `fail`
- 테스트 판정: `fail`
- 현재 generation layer MVP는 "생성은 되지만 계약 일치성과 산출물 안정성에 구조적 결함이 남아 있는 상태"로 판단한다.

판정 근거:

1. `AGENTS.md` 포인터 계약이 manifest와 실제 생성/패치 로직 사이에서 일치하지 않는다.
2. custom role ordering에서 orchestrator가 delegation 권한을 잃을 수 있다.
3. `force` 재생성 시 stale role/skill 파일이 남아 generated bundle이 비결정적이 된다.
4. `skill.path` 계약과 실제 파일 생성 위치가 불일치할 수 있다.
5. 테스트는 최종 기준으로 `18`개 중 `15`개만 통과했고, schema fixture 3건이 실패한다.

## 주요 Findings

### 1. High - `agents_pointer` 계약이 실제 생성 경로에서 무시된다

관련 코드:

- `src/meta_harness/briefs.py:115-120`
- `src/meta_harness/render.py:115-139`
- `src/meta_harness/scaffold.py:74-97`

문제:

- manifest에는 `section_title`, `update_mode`, `append_history`가 들어간다.
- 하지만 `AGENTS.pointer.md` 렌더링은 `manifest.harness.display_name`과 `generated/<harness-name>/...` 경로를 하드코딩한다.
- `update_agents_file()`도 `display_name` 기반 정규식 치환만 수행한다.

영향:

- `agents_pointer.section_title`를 커스터마이즈해도 실제 포인터에 반영되지 않는다.
- `--output-dir`를 `generated` 외 다른 경로로 주면 포인터의 asset 경로가 실제 산출물과 어긋난다.
- `update_mode`, `append_history` 값은 현재 저장만 되고 동작으로 이어지지 않는다.

기획 대비:

- `analysis/revfactory-harness-codex-directory-schema-draft.md`는 `agents_pointer`를 생성 계약의 일부로 정의한다.
- `analysis/revfactory-harness-codex-review-test-plan.md` Gate A, Gate C 기준과 충돌한다.

### 2. High - custom role ordering에서 orchestrator가 delegation 소유권을 잃는다

관련 코드:

- `src/meta_harness/briefs.py:135-155`

문제:

- raw roles에 `orchestrator`가 포함되어 있지만 첫 번째가 아니면, 코드가 `roles[0]`에 전체 `can_spawn`/`can_message`를 덮어쓴다.
- 이 경우 첫 번째 specialist가 전체 역할을 spawn 가능한 조정자처럼 동작하고, 실제 orchestrator는 메시지 수신 대상 수준으로 내려간다.

영향:

- generated manifest와 role spec이 설계 의도와 다르게 만들어진다.
- 이후 runtime layer를 붙일 때 orchestration 권한 모델이 깨진 상태로 시작하게 된다.

기획 대비:

- 전략 문서에서 coordinator 역할이 delegation을 소유하는 구조를 전제로 한다.

### 3. High - `force=True` 재생성 시 stale 파일이 남아 generated bundle이 오염된다

관련 코드:

- `src/meta_harness/scaffold.py:41-46`
- `src/meta_harness/scaffold.py:63-75`

문제:

- non-empty target에 대해 `force=True`를 주면 기존 디렉터리를 비우지 않고 그대로 덮어쓴다.
- 현재 manifest에 없는 role/skill 파일은 삭제되지 않는다.

재현:

- 첫 실행에서 `security` role을 포함해 생성
- 두 번째 실행에서 `security` role 제거 + `force=True`
- `roles/security.md`, `skills/security/SKILL.md`가 그대로 남는다

영향:

- 디스크 상태가 `harness.yaml`과 불일치한다.
- generated bundle handoff 시 다음 에이전트가 stale 파일을 현재 계약으로 오해할 수 있다.

기획 대비:

- `analysis/revfactory-harness-codex-review-test-plan.md` Gate B의 "예측 가능한 force 동작" 요구를 만족하지 못한다.

### 4. High - `skill.path` 계약을 스캐폴더가 실제로 지키지 않는다

관련 코드:

- `src/meta_harness/models.py:149-157`
- `src/meta_harness/scaffold.py:66-72`

문제:

- validation은 `skills/.../SKILL.md` 패턴이면 통과시킨다.
- 실제 write 경로는 `skill.path.split("/")[1]`만 사용한다.
- 따라서 nested skill path가 들어오면 manifest와 실제 파일 위치가 달라진다.

재현:

- manifest path: `skills/orchestrate/custom/SKILL.md`
- 실제 생성 위치: `skills/orchestrate/SKILL.md`

영향:

- generated manifest가 가리키는 경로를 bundle이 충족하지 못한다.
- self-contained handoff bundle이라는 전제가 깨진다.

### 5. Medium - production renderer와 template 자산이 분리되어 드리프트 위험이 크다

관련 코드:

- `src/meta_harness/render.py`
- `src/meta_harness/scaffold.py:53-75`
- `plugins/meta-harness/skills/meta-harness/templates/*.j2`

문제:

- 테스트는 Jinja template를 검증한다.
- 실제 스캐폴더는 template를 사용하지 않고 Python 하드코딩 렌더러를 사용한다.

영향:

- template 테스트가 녹색이어도 실제 generated output이 동일하다는 보장이 없다.
- WP3/WP4에서 의도한 "template 중심 생성 계약"과 구현 축이 분리된다.

기획 대비:

- `analysis/revfactory-harness-codex-implementation-breakdown.md`는 schema -> template -> scaffold 순으로 계약을 고정하라고 명시한다.

## 테스트 실행 결과

### 실행 전 메모

- 개발 의존성이 설치되어 있지 않아 아래 패키지를 먼저 개별 설치했다.
  - `pytest`
  - `PyYAML`
  - `jsonschema`
  - `Jinja2`
- `requirements-dev.txt`는 pip가 requirements 파일로 해석하지 못했다. UTF-8/CP949 모두 디코딩 실패했고, 바이너리 손상 파일처럼 보였다.

### 실행 커맨드

1. `python -m pytest`
2. `python -m pytest --basetemp .pytest_tmp`

메모:

- 첫 번째 실행은 Windows temp 디렉터리 권한 문제로 scaffold 테스트 setup이 실패했다.
- 두 번째 실행은 `--basetemp .pytest_tmp`로 환경 문제를 제거한 기준 결과다.

### 최종 결과

- `18` collected
- `15 passed`
- `3 failed`
- `0 skipped`

실패 테스트:

- `tests/test_schema.py::test_minimal_valid_manifest_passes_validation`
- `tests/test_schema.py::test_missing_context_manifest_fails_validation`
- `tests/test_schema.py::test_empty_roles_manifest_fails_validation`

### 실패 원인

세 테스트 모두 schema 로직 자체 이전에 fixture YAML parse 단계에서 실패한다.

관련 fixture:

- `tests/fixtures/manifests/minimal-valid.yaml:57`
- `tests/fixtures/manifests/minimal-invalid-missing-context.yaml:43`
- `tests/fixtures/manifests/minimal-invalid-empty-roles.yaml:35`

문제 값:

```yaml
section_title: Meta Harness: code-review-harness
```

설명:

- `:`가 포함된 scalar를 따옴표 없이 써서 PyYAML이 `mapping values are not allowed here`로 파싱을 중단한다.
- 따라서 현재 schema fixture 3건은 "schema가 틀렸다"가 아니라 "fixture YAML이 문법상 invalid"인 상태다.

## 테스트 해석

좋은 점:

- scaffold flow 자체는 환경만 정리하면 현재 테스트 기준으로 모두 통과한다.
- plugin metadata, skill frontmatter, template 렌더링 테스트도 통과한다.

남은 문제:

- schema fixture 세트가 깨져 있어 schema gate를 신뢰할 수 없다.
- production renderer와 template가 분리되어 있으므로 template green만으로 생성 계약 green이라고 보기 어렵다.

## 다음 담당 에이전트를 위한 handoff

우선순위 제안:

1. schema fixture YAML 3건을 먼저 정상 파싱 가능하게 복구
2. `agents_pointer` 필드들이 실제 렌더링/패치 로직에 반영되도록 계약 정렬
3. orchestrator role 위치와 handoff 권한 부여 로직 수정
4. `force` 재실행 정책을 명시적으로 결정하고 stale 파일 처리 추가
5. `skill.path` 전체 경로를 실제 생성 위치에 반영
6. template와 production renderer 중 하나를 진실 원천으로 고정

검증 재실행 기준:

- `python -m pytest --basetemp .pytest_tmp`

## 결론

현재 저장소는 "하네스 생성 MVP의 뼈대"는 갖췄지만, analysis 문서가 정의한 계약을 코드가 완전히 보존하고 있지는 않다. 특히 `agents_pointer`, role orchestration ownership, force 재생성 안정성, skill path 보존은 다음 구현 에이전트가 우선적으로 바로잡아야 한다.

테스트 기준으로도 완전한 녹색 상태가 아니며, 실패 3건은 fixture 문법 오류라 빠르게 정리할 수 있다. 다만 fixture 수정만으로 제품 판정이 올라가지는 않고, 위 High 이슈들을 함께 해결해야 generation layer MVP를 안정적으로 handoff할 수 있다.
