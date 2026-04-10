import json
from pathlib import Path

import pytest


jinja2 = pytest.importorskip("jinja2")
yaml = pytest.importorskip("yaml")
jsonschema = pytest.importorskip("jsonschema")

from meta_harness.briefs import build_manifest_from_brief
from meta_harness.render import render_agents_pointer, render_manifest_yaml


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


def test_production_manifest_renderer_matches_template_contract(schema):
    brief = {
        "name": "code-review-harness",
        "domain": "software-engineering",
        "summary": "Rendered fixture for template tests.",
        "display_name": "Code Review Harness",
        "target_paths": ["."],
        "readme_paths": ["README.md"],
        "instruction_files": ["AGENTS.md"],
        "roles": [
            {
                "id": "orchestrator",
                "title": "Review Orchestrator",
                "kind": "coordinator",
                "agent_type": "default",
                "model": "gpt-5.4-mini",
                "reasoning_effort": "high",
                "mission": "Coordinate the generated harness.",
                "inputs": ["user_request", "repository_context"],
                "outputs": ["workspace/artifacts/final-review.md"],
                "responsibilities": ["Coordinate review flow", "Merge specialist outputs"],
                "handoff": {
                    "can_spawn": ["architecture-reviewer"],
                    "can_message": ["architecture-reviewer"],
                },
            }
        ],
        "skills": [
            {
                "id": "orchestrate",
                "display_name": "Code Review Orchestrate",
                "path": "skills/orchestrate/SKILL.md",
                "purpose": "Run the harness",
                "description": "Run the code review harness end-to-end.",
                "trigger_keywords": ["review harness", "parallel review"],
                "inputs": ["user_request", "repository_context"],
                "workflow": ["Read the manifest", "Assign role responsibilities", "Persist artifacts"],
                "outputs": ["workspace/artifacts/final-review.md"],
                "constraints": ["Fallback to single-agent mode when delegation is unavailable."],
            }
        ],
        "should_trigger": ["Build a code review harness"],
        "should_not_trigger": ["Summarize the diff only"],
        "agents_pointer_section_title": "Meta Harness: Code Review Harness",
    }
    manifest, _, _, _ = build_manifest_from_brief(brief)

    payload = yaml.safe_load(render_manifest_yaml(manifest))
    errors = sorted(jsonschema.Draft202012Validator(schema).iter_errors(payload), key=lambda err: list(err.path))
    assert payload["harness"]["name"] == "code-review-harness"
    assert payload["agents_pointer"]["section_title"] == "Meta Harness: Code Review Harness"
    assert errors == []


def test_production_agents_pointer_renderer_honors_section_title_and_bundle_root():
    brief = {
        "name": "code-review-harness",
        "domain": "software-engineering",
        "summary": "Rendered fixture for template tests.",
        "target_paths": ["."],
        "focus_areas": ["architecture"],
        "agents_pointer_section_title": "Meta Harness: Custom Review Bundle",
        "agents_pointer_append_history": False,
    }
    manifest, _, _, pointer_lines = build_manifest_from_brief(brief)
    rendered = render_agents_pointer(manifest, pointer_lines, "bundles/code-review-harness")
    assert "## Meta Harness: Custom Review Bundle" in rendered
    assert "`bundles/code-review-harness/harness.yaml`" in rendered
    assert "Change log:" not in rendered
