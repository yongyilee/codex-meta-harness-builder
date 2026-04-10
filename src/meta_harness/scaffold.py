from __future__ import annotations

import json
from pathlib import Path
import re

from .briefs import build_manifest_from_brief, default_brief
from .evals import run_eval
from .render import render_agents_pointer, render_evals_json, render_manifest_yaml, render_role_markdown, render_skill_markdown


DEFAULT_DIRS = [
    "evals/baseline",
    "evals/iterations",
    "workspace/artifacts",
    "workspace/logs",
    "workspace/runtime",
]


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def scaffold(target_root: Path, harness_name: str, force: bool) -> Path:
    brief = default_brief(harness_name)
    return generate_harness(target_root=target_root, brief=brief, force=force, patch_agents=False)


def generate_harness(
    target_root: str | Path,
    brief: dict,
    force: bool = False,
    patch_agents: bool = False,
    agents_file: str | Path | None = None,
) -> Path:
    output_root = Path(target_root)
    manifest, should_trigger, should_not_trigger, pointer_lines = build_manifest_from_brief(brief)
    harness_root = output_root / manifest.harness.name

    if harness_root.exists() and any(harness_root.iterdir()) and not force:
        raise FileExistsError(f"Target already exists and is not empty: {harness_root}")

    harness_root.mkdir(parents=True, exist_ok=True)
    for relative in DEFAULT_DIRS:
        (harness_root / relative).mkdir(parents=True, exist_ok=True)

    roles_dir = harness_root / "roles"
    roles_dir.mkdir(exist_ok=True)
    skills_dir = harness_root / "skills"
    skills_dir.mkdir(exist_ok=True)

    (harness_root / "harness.yaml").write_text(render_manifest_yaml(manifest), encoding="utf-8")
    write_json(harness_root / "brief.json", brief)
    write_json(harness_root / "workspace" / "tasks.json", {"tasks": []})
    write_json(harness_root / "workspace" / "runtime" / "agents.json", {"agents": []})
    write_json(harness_root / "evals" / "baseline" / "summary.json", {"results": []})
    (harness_root / "evals" / "evals.json").write_text(
        render_evals_json(manifest, should_trigger, should_not_trigger),
        encoding="utf-8",
    )

    for role in manifest.roles:
        (roles_dir / f"{role.id}.md").write_text(render_role_markdown(role), encoding="utf-8")

    for skill in manifest.skills:
        skill_root = skills_dir / skill.path.split("/")[1]
        skill_root.mkdir(parents=True, exist_ok=True)
        (skill_root / "SKILL.md").write_text(
            render_skill_markdown(manifest.harness.name, skill),
            encoding="utf-8",
        )

    pointer = render_agents_pointer(manifest, pointer_lines)
    (harness_root / "AGENTS.pointer.md").write_text(pointer, encoding="utf-8")

    if patch_agents:
        target = Path(agents_file) if agents_file else Path("AGENTS.md")
        update_agents_file(target, pointer, manifest.harness.display_name)

    run_eval(harness_root)
    return harness_root


def update_agents_file(path: str | Path, section_text: str, display_name: str) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    existing = target.read_text(encoding="utf-8") if target.exists() else ""
    pattern = re.compile(rf"(?ms)^## Meta Harness: {re.escape(display_name)}\n.*?(?=^## |\Z)")
    if pattern.search(existing):
        updated = pattern.sub(section_text.rstrip() + "\n\n", existing)
    else:
        updated = existing.rstrip()
        if updated:
            updated += "\n\n"
        updated += section_text.rstrip() + "\n"
    target.write_text(updated, encoding="utf-8")
    return target
