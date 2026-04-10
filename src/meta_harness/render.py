from __future__ import annotations

import json
from pathlib import Path

from jinja2 import Environment, StrictUndefined

from .models import HarnessManifest, RoleSpec, SkillSpec


TEMPLATES_ROOT = (
    Path(__file__).resolve().parents[2]
    / "plugins"
    / "meta-harness"
    / "skills"
    / "meta-harness"
    / "templates"
)


def _create_environment() -> Environment:
    environment = Environment(
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    environment.filters["tojson"] = lambda value: json.dumps(value, ensure_ascii=False)
    return environment


ENVIRONMENT = _create_environment()


def _render_template(name: str, **context: object) -> str:
    template_path = TEMPLATES_ROOT / name
    template = ENVIRONMENT.from_string(template_path.read_text(encoding="utf-8"))
    return template.render(**context)


def render_manifest_yaml(manifest: HarnessManifest) -> str:
    context = manifest.to_dict()
    context["generated_at"] = manifest.harness.generated_at
    return _render_template("harness_manifest.yaml.j2", **context).rstrip() + "\n"


def render_role_markdown(role: RoleSpec) -> str:
    return _render_template("role.md.j2", role=role).rstrip() + "\n"


def render_skill_markdown(harness_name: str, skill: SkillSpec) -> str:
    return _render_template("skill_SKILL.md.j2", harness={"name": harness_name}, skill=skill).rstrip() + "\n"


def render_evals_json(
    manifest: HarnessManifest,
    should_trigger: list[str],
    should_not_trigger: list[str],
) -> str:
    context = manifest.to_dict()
    context["trigger_cases_json"] = json.dumps(should_trigger, ensure_ascii=False)
    context["baseline_cases_json"] = json.dumps(should_not_trigger, ensure_ascii=False)
    return _render_template("evals.json.j2", **context).rstrip() + "\n"


def render_agents_pointer(
    manifest: HarnessManifest,
    when_to_use: list[str],
    bundle_root: str,
) -> str:
    return _render_template(
        "AGENTS.pointer.md.j2",
        harness=manifest.harness,
        agents_pointer=manifest.agents_pointer,
        generated_at=manifest.harness.generated_at,
        pointer={"when_to_use": when_to_use},
        bundle_root=bundle_root,
    ).rstrip() + "\n"
