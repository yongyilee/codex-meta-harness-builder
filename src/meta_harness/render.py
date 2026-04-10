from __future__ import annotations

import json

from .models import HarnessManifest, RoleSpec, SkillSpec
from .utils import titleize


def render_manifest_yaml(manifest: HarnessManifest) -> str:
    return dump_yaml(manifest.to_dict()) + "\n"


def render_role_markdown(role: RoleSpec) -> str:
    lines = [
        f"# {role.title}",
        "",
        f"Role ID: `{role.id}`",
        f"Kind: `{role.kind}`",
        f"Agent Type: `{role.agent_type}`",
        f"Model: `{role.model}`",
        f"Reasoning Effort: `{role.reasoning_effort}`",
        "",
        "## Mission",
        "",
        role.mission or role.title,
        "",
        "## Inputs",
        "",
    ]
    lines.extend(f"- `{item}`" for item in role.inputs)
    lines.extend(["", "## Outputs", ""])
    lines.extend(f"- `{item}`" for item in role.outputs)
    lines.extend(["", "## Responsibilities", ""])
    lines.extend(f"- {item}" for item in role.responsibilities)
    lines.extend(
        [
            "",
            "## Collaboration Rules",
            "",
            "- Persist shared execution state in files, not in transient plan state.",
            "- If delegated execution is not allowed, hand work back to the orchestrator for single-agent completion.",
            "- Do not assume this role is auto-installed as a native Codex agent.",
        ]
    )
    if role.handoff and role.handoff.can_spawn:
        lines.extend(["- Allowed spawn targets:"])
        lines.extend(f"  - `{item}`" for item in role.handoff.can_spawn)
    if role.handoff and role.handoff.can_message:
        lines.extend(["- Allowed message targets:"])
        lines.extend(f"  - `{item}`" for item in role.handoff.can_message)
    return "\n".join(lines) + "\n"


def render_skill_markdown(harness_name: str, skill: SkillSpec) -> str:
    skill_name = f"{harness_name}-{skill.id}"
    description = skill.description or skill.purpose
    title = skill.display_name or titleize(skill.id)
    lines = [
        "---",
        f"name: {json.dumps(skill_name, ensure_ascii=False)}",
        f"description: {json.dumps(description, ensure_ascii=False)}",
        "---",
        "",
        f"# {title}",
        "",
        skill.purpose,
        "",
        "## Trigger",
        "",
        "Use this generated skill when the request matches one or more of the following:",
        "",
    ]
    lines.extend(f"- {item}" for item in (skill.trigger_keywords or ["generated harness execution"]))
    lines.extend(["", "## Inputs", ""])
    lines.extend(f"- `{item}`" for item in (skill.inputs or ["harness_manifest"]))
    lines.extend(["", "## Workflow", ""])
    lines.extend(f"- {item}" for item in (skill.workflow or ["Read the manifest and produce the declared output."]))
    lines.extend(["", "## Outputs", ""])
    lines.extend(f"- `{item}`" for item in (skill.outputs or ["workspace/artifacts/output.md"]))
    lines.extend(["", "## Constraints", ""])
    constraints = skill.constraints or [
        "Prefer single-agent execution unless delegated mode is explicitly requested and allowed.",
        "Use file-backed ledgers for shared state.",
        "Treat this generated skill as a portable bundle. Installation is a separate step.",
    ]
    lines.extend(f"- {item}" for item in constraints)
    return "\n".join(lines) + "\n"


def render_evals_json(
    manifest: HarnessManifest,
    should_trigger: list[str],
    should_not_trigger: list[str],
) -> str:
    payload = {
        "version": manifest.version,
        "target_harness": manifest.harness.name,
        "baseline": {"mode": manifest.eval.baseline_mode},
        "trigger_thresholds": {
            "should_trigger_min": manifest.eval.trigger_checks.should_trigger_min if manifest.eval.trigger_checks else 0,
            "should_not_trigger_min": manifest.eval.trigger_checks.should_not_trigger_min if manifest.eval.trigger_checks else 0,
        },
        "trigger_evals": {
            "should_trigger": should_trigger,
            "should_not_trigger": should_not_trigger,
        },
        "artifacts": {
            "iterations_dir": manifest.eval.iterations_dir or "evals/iterations",
            "summary_file": "evals/summary.json",
        },
    }
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def render_agents_pointer(manifest: HarnessManifest, when_to_use: list[str]) -> str:
    lines = [
        f"## Meta Harness: {manifest.harness.display_name}",
        "",
        f"Goal: {manifest.harness.description}",
        "",
        "When to use:",
    ]
    lines.extend(f"- {item}" for item in when_to_use)
    lines.extend(
        [
            "",
            "Primary generated assets:",
            f"- `generated/{manifest.harness.name}/harness.yaml`",
            f"- `generated/{manifest.harness.name}/roles/`",
            f"- `generated/{manifest.harness.name}/skills/`",
            f"- `generated/{manifest.harness.name}/evals/`",
            "",
            "Change log:",
            "| Date | Change | Author | Reason |",
            "|---|---|---|---|",
            f"| {manifest.harness.generated_at} | Initial pointer generated | meta-harness | Bootstrap generated harness entry |",
        ]
    )
    return "\n".join(lines) + "\n"


def dump_yaml(value: object, indent: int = 0) -> str:
    lines = _dump_yaml_lines(value, indent)
    return "\n".join(lines)


def _dump_yaml_lines(value: object, indent: int) -> list[str]:
    prefix = " " * indent
    if isinstance(value, dict):
        if not value:
            return [prefix + "{}"]
        lines: list[str] = []
        for key, item in value.items():
            if _is_scalar(item):
                lines.append(f"{prefix}{key}: {_dump_scalar(item)}")
            else:
                lines.append(f"{prefix}{key}:")
                lines.extend(_dump_yaml_lines(item, indent + 2))
        return lines
    if isinstance(value, list):
        if not value:
            return [prefix + "[]"]
        lines = []
        for item in value:
            if _is_scalar(item):
                lines.append(f"{prefix}- {_dump_scalar(item)}")
            else:
                nested = _dump_yaml_lines(item, indent + 2)
                first = nested[0].lstrip()
                lines.append(f"{prefix}- {first}")
                for line in nested[1:]:
                    lines.append(line)
        return lines
    return [prefix + _dump_scalar(value)]


def _is_scalar(value: object) -> bool:
    return value is None or isinstance(value, (str, int, float, bool))


def _dump_scalar(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return json.dumps(str(value), ensure_ascii=False)
