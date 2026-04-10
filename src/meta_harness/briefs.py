from __future__ import annotations

import json
from pathlib import Path

from .models import (
    AgentsPointerSpec,
    ContextSpec,
    EvalSpec,
    ExecutionSpec,
    HandoffSpec,
    HarnessManifest,
    HarnessSpec,
    RoleSpec,
    SkillSpec,
    TriggerChecks,
)
from .utils import ensure_list, slugify, titleize, today_iso


ROLE_DEFAULTS = {
    "coordinator": {"agent_type": "default", "model": "gpt-5.4", "reasoning_effort": "high"},
    "specialist": {"agent_type": "explorer", "model": "gpt-5.4-mini", "reasoning_effort": "medium"},
    "executor": {"agent_type": "worker", "model": "gpt-5.4", "reasoning_effort": "medium"},
    "validator": {"agent_type": "explorer", "model": "gpt-5.4-mini", "reasoning_effort": "medium"},
}


def _sentence_fragment(value: str) -> str:
    return value.strip().rstrip(".")


def load_brief(path: str | Path) -> dict:
    source = Path(path)
    return json.loads(source.read_text(encoding="utf-8"))


def default_brief(name: str) -> dict:
    return {
        "name": slugify(name),
        "domain": "general",
        "summary": f"Coordinate reusable Codex work for {titleize(slugify(name))}.",
        "focus_areas": ["analysis", "implementation"],
        "target_paths": ["."],
        "readme_paths": ["README.md"],
        "instruction_files": ["AGENTS.md"],
        "execution_pattern": "fanout-fanin",
        "runtime_mode": "single",
        "delegation_policy": "on-user-request",
    }


def init_brief(name: str, domain: str, summary: str, focus_areas: list[str]) -> dict:
    brief = default_brief(name)
    brief["domain"] = domain
    brief["summary"] = summary
    if focus_areas:
        brief["focus_areas"] = focus_areas
    return brief


def build_manifest_from_brief(brief: dict) -> tuple[HarnessManifest, list[str], list[str], list[str]]:
    name = slugify(brief["name"])
    display_name = brief.get("display_name") or titleize(name)
    summary = brief["summary"].strip()
    domain = brief["domain"].strip()
    generated_at = brief.get("generated_at") or today_iso()
    target_paths = ensure_list(brief.get("target_paths") or ["."])
    readme_paths = ensure_list(brief.get("readme_paths") or ["README.md"])
    instruction_files = ensure_list(brief.get("instruction_files") or ["AGENTS.md"])

    harness = HarnessSpec(
        name=name,
        display_name=display_name,
        description=summary,
        domain=domain,
        owner_mode=brief.get("owner_mode", "generated"),
        generated_at=generated_at,
    )
    execution = ExecutionSpec(
        pattern=brief.get("execution_pattern", "fanout-fanin"),
        runtime_mode=brief.get("runtime_mode", "single"),
        delegation_policy=brief.get("delegation_policy", "on-user-request"),
    )
    context = ContextSpec(
        target_paths=target_paths,
        readme_paths=readme_paths,
        instruction_files=instruction_files,
    )

    roles = _build_roles(summary, brief)
    skills = _build_skills(name, summary, roles, brief)
    trigger_cases = ensure_list(brief.get("should_trigger")) or [
        f"{display_name}를 위한 Codex 하네스를 만들어줘",
        f"{summary} 작업을 역할별로 나누는 하네스를 구성해줘",
    ]
    non_trigger_cases = ensure_list(brief.get("should_not_trigger")) or [
        "현재 파일 하나만 빠르게 수정해줘",
        "간단한 질문 하나에만 답해줘",
    ]
    pointer_lines = ensure_list(brief.get("agents_pointer_when_to_use")) or [
        f"{display_name}를 새로 생성하거나 갱신해야 할 때",
        "여러 역할로 분해해 반복 실행 가능한 Codex 하네스가 필요할 때",
    ]

    eval_spec = EvalSpec(
        enabled=bool(brief.get("eval_enabled", True)),
        baseline_mode=brief.get("baseline_mode", "no-harness"),
        trigger_checks=TriggerChecks(
            should_trigger_min=brief.get("should_trigger_min", max(1, len(trigger_cases))),
            should_not_trigger_min=brief.get("should_not_trigger_min", max(1, len(non_trigger_cases))),
        ),
        iterations_dir=brief.get("iterations_dir", "evals/iterations"),
    )
    agents_pointer = AgentsPointerSpec(
        target_file="AGENTS.md",
        section_title=brief.get("agents_pointer_section_title", f"Meta Harness: {display_name}"),
        update_mode=brief.get("agents_pointer_update_mode", "patch"),
        append_history=bool(brief.get("agents_pointer_append_history", True)),
    )
    manifest = HarnessManifest(
        version=str(brief.get("version", "0.2")),
        harness=harness,
        execution=execution,
        context=context,
        roles=roles,
        skills=skills,
        eval=eval_spec,
        agents_pointer=agents_pointer,
    )
    manifest.validate()
    return manifest, trigger_cases, non_trigger_cases, pointer_lines


def _build_roles(summary: str, brief: dict) -> list[RoleSpec]:
    raw_roles = list(brief.get("roles") or [])
    roles: list[RoleSpec] = []
    for raw in raw_roles:
        roles.append(_normalize_role(raw, summary))

    if not any(role.id == "orchestrator" for role in roles):
        roles.insert(0, _orchestrator_role(summary))

    if not raw_roles:
        focus_areas = ensure_list(brief.get("focus_areas")) or ["analysis", "implementation"]
        roles = [_orchestrator_role(summary)]
        for focus in focus_areas:
            roles.append(_role_from_focus(focus, summary))

    if not any(role.kind == "validator" for role in roles):
        roles.append(_quality_gate_role(summary))

    other_role_ids = [role.id for role in roles if role.id != "orchestrator"]
    roles[0].handoff = HandoffSpec(can_spawn=other_role_ids, can_message=other_role_ids)
    return roles


def _normalize_role(raw: dict, summary: str) -> RoleSpec:
    role_id = slugify(raw.get("id") or raw.get("focus") or raw["title"])
    kind = raw.get("kind") or _infer_kind(role_id)
    defaults = ROLE_DEFAULTS[kind]
    outputs = ensure_list(raw.get("outputs")) or [f"workspace/artifacts/{role_id}.md"]
    return RoleSpec(
        id=role_id,
        title=raw.get("title") or _default_role_title(role_id, kind),
        kind=kind,
        agent_type=raw.get("agent_type", defaults["agent_type"]),
        model=raw.get("model", defaults["model"]),
        reasoning_effort=raw.get("reasoning_effort", defaults["reasoning_effort"]),
        mission=raw.get("mission") or f"Own the {role_id} slice for {summary}",
        inputs=ensure_list(raw.get("inputs")) or ["user_request", "target_context"],
        outputs=outputs,
        responsibilities=ensure_list(raw.get("responsibilities"))
        or [
            f"Inspect the {role_id} workstream",
            f"Record findings for {role_id}",
        ],
        handoff=HandoffSpec(
            can_spawn=ensure_list((raw.get("handoff") or {}).get("can_spawn")),
            can_message=ensure_list((raw.get("handoff") or {}).get("can_message")) or ["orchestrator"],
        ),
    )


def _orchestrator_role(summary: str) -> RoleSpec:
    defaults = ROLE_DEFAULTS["coordinator"]
    return RoleSpec(
        id="orchestrator",
        title="Harness Orchestrator",
        kind="coordinator",
        agent_type=defaults["agent_type"],
        model=defaults["model"],
        reasoning_effort=defaults["reasoning_effort"],
        mission=f"Translate the request into a coordinated harness for: {summary}",
        inputs=["user_request", "repository_context", "harness_manifest"],
        outputs=["workspace/artifacts/final-report.md"],
        responsibilities=[
            "Decide which roles need to run",
            "Merge outputs into a stable final report",
            "Fallback to single-agent completion when delegation is unavailable",
        ],
    )


def _quality_gate_role(summary: str) -> RoleSpec:
    defaults = ROLE_DEFAULTS["validator"]
    return RoleSpec(
        id="quality-gate",
        title="Quality Gate",
        kind="validator",
        agent_type=defaults["agent_type"],
        model=defaults["model"],
        reasoning_effort=defaults["reasoning_effort"],
        mission=f"Validate the generated harness and its outputs for: {summary}",
        inputs=["harness_manifest", "workspace/artifacts"],
        outputs=["workspace/artifacts/quality-gate.md"],
        responsibilities=[
            "Check that artifacts satisfy the manifest contract",
            "Call out missing eval coverage or weak triggers",
        ],
        handoff=HandoffSpec(can_message=["orchestrator"]),
    )


def _role_from_focus(focus: str, summary: str) -> RoleSpec:
    role_id = slugify(focus)
    kind = _infer_kind(role_id)
    defaults = ROLE_DEFAULTS[kind]
    title = _default_role_title(role_id, kind)
    inputs = ["user_request", "repository_context"]
    if kind == "executor":
        inputs.append("implementation_plan")
    return RoleSpec(
        id=role_id,
        title=title,
        kind=kind,
        agent_type=defaults["agent_type"],
        model=defaults["model"],
        reasoning_effort=defaults["reasoning_effort"],
        mission=f"Own the {title.lower()} track for: {summary}",
        inputs=inputs,
        outputs=[f"workspace/artifacts/{role_id}.md"],
        responsibilities=[
            f"Inspect the request from the {title.lower()} angle",
            f"Summarize {title.lower()} risks and next actions",
        ],
        handoff=HandoffSpec(can_message=["orchestrator"]),
    )


def _infer_kind(role_id: str) -> str:
    if any(token in role_id for token in ("qa", "quality", "validate", "test")):
        return "validator"
    if any(token in role_id for token in ("build", "implement", "fix", "migrate")):
        return "executor"
    return "specialist"


def _default_role_title(role_id: str, kind: str) -> str:
    suffix = {
        "specialist": "Specialist",
        "executor": "Worker",
        "validator": "Validator",
        "coordinator": "Orchestrator",
    }[kind]
    return f"{titleize(role_id)} {suffix}"


def _build_skills(name: str, summary: str, roles: list[RoleSpec], brief: dict) -> list[SkillSpec]:
    summary_fragment = _sentence_fragment(summary)
    raw_skills = list(brief.get("skills") or [])
    if raw_skills:
        return [_normalize_skill(raw, summary_fragment) for raw in raw_skills]

    skills = [
        SkillSpec(
            id="orchestrate",
            path="skills/orchestrate/SKILL.md",
            display_name=f"{titleize(name)} Orchestrate",
            purpose="Coordinate the generated harness end-to-end.",
            description=f"Coordinate the generated harness for {summary_fragment}. Use when the full multi-role flow should run.",
            trigger_keywords=["generate harness", "refresh harness", titleize(name)],
            inputs=["user_request", "harness_manifest", "repository_context"],
            workflow=[
                "Read the manifest and pick the relevant roles",
                "Persist shared state in workspace files",
                "Merge role outputs into a single final artifact",
            ],
            outputs=["workspace/artifacts/final-report.md"],
            constraints=[
                "Fallback to single-agent mode when delegation is unavailable",
                "Do not treat update_plan as shared runtime state",
            ],
        )
    ]
    for role in roles:
        if role.id == "orchestrator":
            continue
        skills.append(
            SkillSpec(
                id=role.id,
                path=f"skills/{role.id}/SKILL.md",
                display_name=role.title,
                purpose=f"Run the {role.title.lower()} slice of the harness.",
                description=f"Execute the {role.title.lower()} role for {summary_fragment}.",
                trigger_keywords=[role.id, role.title.lower()],
                inputs=role.inputs,
                workflow=[
                    f"Read roles/{role.id}.md",
                    "Produce the role artifact in workspace/artifacts/",
                    "Return actionable output to the orchestrator",
                ],
                outputs=role.outputs,
                constraints=[
                    "Keep the role output aligned with harness.yaml",
                    "Escalate ambiguity back to the orchestrator instead of inventing state",
                ],
            )
        )
    return skills


def _normalize_skill(raw: dict, summary_fragment: str) -> SkillSpec:
    skill_id = slugify(raw.get("id") or raw["path"].split("/")[1])
    return SkillSpec(
        id=skill_id,
        path=raw.get("path") or f"skills/{skill_id}/SKILL.md",
        display_name=raw.get("display_name"),
        purpose=raw["purpose"],
        description=raw.get("description")
        or f"{raw['purpose']} Use when the harness needs the {skill_id} step for {summary_fragment}.",
        trigger_keywords=ensure_list(raw.get("trigger_keywords")),
        inputs=ensure_list(raw.get("inputs")),
        workflow=ensure_list(raw.get("workflow")),
        outputs=ensure_list(raw.get("outputs")),
        constraints=ensure_list(raw.get("constraints")),
    )
