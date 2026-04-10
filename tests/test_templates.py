import json
from pathlib import Path

import pytest


jinja2 = pytest.importorskip("jinja2")
yaml = pytest.importorskip("yaml")
jsonschema = pytest.importorskip("jsonschema")


def _render(template_path: Path, **context) -> str:
    template = jinja2.Environment(
        undefined=jinja2.StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    ).from_string(template_path.read_text(encoding="utf-8"))
    return template.render(**context)


def test_harness_manifest_template_renders_valid_manifest(template_context, schema, repo_root):
    template_path = repo_root / "plugins" / "meta-harness" / "skills" / "meta-harness" / "templates" / "harness_manifest.yaml.j2"
    rendered = _render(template_path, **template_context)
    payload = yaml.safe_load(rendered)
    errors = sorted(jsonschema.Draft202012Validator(schema).iter_errors(payload), key=lambda err: list(err.path))
    assert errors == []


def test_role_template_renders_handoff_block(template_context, repo_root):
    template_path = repo_root / "plugins" / "meta-harness" / "skills" / "meta-harness" / "templates" / "role.md.j2"
    rendered = _render(template_path, role=template_context["roles"][0])
    assert "# Review Orchestrator" in rendered
    assert "Allowed spawn targets:" in rendered
    assert "`architecture-reviewer`" in rendered


def test_evals_template_renders_valid_json(template_context, repo_root):
    template_path = repo_root / "plugins" / "meta-harness" / "skills" / "meta-harness" / "templates" / "evals.json.j2"
    rendered = _render(template_path, **template_context)
    payload = json.loads(rendered)
    assert payload["target_harness"] == "code-review-harness"
    assert payload["trigger_thresholds"]["should_trigger_min"] == 1
    assert payload["trigger_evals"]["should_not_trigger"]


def test_agents_pointer_template_renders_expected_section(template_context, repo_root):
    template_path = repo_root / "plugins" / "meta-harness" / "skills" / "meta-harness" / "templates" / "AGENTS.pointer.md.j2"
    rendered = _render(template_path, **template_context)
    assert "## Meta Harness: Code Review Harness" in rendered
    assert "generated/code-review-harness/harness.yaml" in rendered


def test_generated_skill_template_includes_yaml_frontmatter(template_context, repo_root):
    template_path = repo_root / "plugins" / "meta-harness" / "skills" / "meta-harness" / "templates" / "skill_SKILL.md.j2"
    rendered = _render(template_path, harness=template_context["harness"], skill=template_context["skills"][0])
    assert rendered.lstrip().startswith("---\n")
    assert "name:" in rendered
    assert "description:" in rendered
