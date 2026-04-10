from __future__ import annotations

from dataclasses import asdict, dataclass, field
import re


SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
ROLE_KINDS = {"coordinator", "specialist", "executor", "validator"}
AGENT_TYPES = {"default", "explorer", "worker"}
REASONING_LEVELS = {"low", "medium", "high", "xhigh"}
EXECUTION_PATTERNS = {"sequential", "fanout-fanin", "router", "review-loop"}
RUNTIME_MODES = {"single", "delegated", "hybrid"}
DELEGATION_POLICIES = {"on-user-request", "always-if-allowed", "disabled"}
OWNER_MODES = {"repo-local", "generated", "user-home"}
BASELINE_MODES = {"no-harness", "single-agent", "manual"}
POINTER_MODES = {"patch", "append", "replace-section"}


class ManifestValidationError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ManifestValidationError(message)


def _validate_slug(value: str, label: str) -> None:
    _require(bool(SLUG_RE.match(value)), f"{label} must be lowercase hyphen-case: {value!r}")


def _validate_string_list(values: list[str], label: str) -> None:
    _require(isinstance(values, list), f"{label} must be a list of strings.")
    for item in values:
        _require(isinstance(item, str) and item.strip(), f"{label} contains an empty item.")


@dataclass(slots=True)
class HandoffSpec:
    can_spawn: list[str] = field(default_factory=list)
    can_message: list[str] = field(default_factory=list)

    def validate(self) -> None:
        _validate_string_list(self.can_spawn, "handoff.can_spawn")
        _validate_string_list(self.can_message, "handoff.can_message")


@dataclass(slots=True)
class HarnessSpec:
    name: str
    display_name: str
    description: str
    domain: str
    owner_mode: str = "generated"
    generated_at: str | None = None

    def validate(self) -> None:
        _validate_slug(self.name, "harness.name")
        _require(self.display_name.strip(), "harness.display_name is required.")
        _require(self.description.strip(), "harness.description is required.")
        _require(self.domain.strip(), "harness.domain is required.")
        _require(self.owner_mode in OWNER_MODES, f"owner_mode must be one of {sorted(OWNER_MODES)}.")


@dataclass(slots=True)
class ExecutionSpec:
    pattern: str = "sequential"
    runtime_mode: str = "single"
    delegation_policy: str = "on-user-request"
    task_ledger_path: str = "workspace/tasks.json"
    artifact_root: str = "workspace/artifacts"

    def validate(self) -> None:
        _require(self.pattern in EXECUTION_PATTERNS, f"pattern must be one of {sorted(EXECUTION_PATTERNS)}.")
        _require(self.runtime_mode in RUNTIME_MODES, f"runtime_mode must be one of {sorted(RUNTIME_MODES)}.")
        _require(
            self.delegation_policy in DELEGATION_POLICIES,
            f"delegation_policy must be one of {sorted(DELEGATION_POLICIES)}.",
        )
        _require(self.task_ledger_path.strip(), "task_ledger_path is required.")
        _require(self.artifact_root.strip(), "artifact_root is required.")


@dataclass(slots=True)
class ContextSpec:
    target_paths: list[str]
    readme_paths: list[str] = field(default_factory=list)
    instruction_files: list[str] = field(default_factory=list)

    def validate(self) -> None:
        _validate_string_list(self.target_paths, "context.target_paths")
        _require(bool(self.target_paths), "context.target_paths must not be empty.")
        _validate_string_list(self.readme_paths, "context.readme_paths")
        _validate_string_list(self.instruction_files, "context.instruction_files")


@dataclass(slots=True)
class RoleSpec:
    id: str
    title: str
    kind: str
    agent_type: str
    model: str
    reasoning_effort: str
    inputs: list[str]
    outputs: list[str]
    responsibilities: list[str]
    mission: str | None = None
    handoff: HandoffSpec | None = None

    def validate(self, known_roles: set[str]) -> None:
        _validate_slug(self.id, "role.id")
        _require(self.title.strip(), f"role.title is required for {self.id}.")
        _require(self.kind in ROLE_KINDS, f"role.kind must be one of {sorted(ROLE_KINDS)}.")
        _require(self.agent_type in AGENT_TYPES, f"role.agent_type must be one of {sorted(AGENT_TYPES)}.")
        _require(self.model.strip(), f"role.model is required for {self.id}.")
        _require(
            self.reasoning_effort in REASONING_LEVELS,
            f"role.reasoning_effort must be one of {sorted(REASONING_LEVELS)}.",
        )
        _validate_string_list(self.inputs, f"role[{self.id}].inputs")
        _validate_string_list(self.outputs, f"role[{self.id}].outputs")
        _require(bool(self.outputs), f"role[{self.id}] must declare at least one output.")
        _validate_string_list(self.responsibilities, f"role[{self.id}].responsibilities")
        for output in self.outputs:
            _require(
                output.startswith("workspace/artifacts/"),
                f"role[{self.id}] output must live under workspace/artifacts/: {output}",
            )
        if self.handoff is not None:
            self.handoff.validate()
            for target in self.handoff.can_spawn + self.handoff.can_message:
                _require(target in known_roles, f"role[{self.id}] references unknown handoff target {target!r}.")


@dataclass(slots=True)
class SkillSpec:
    id: str
    path: str
    purpose: str
    description: str | None = None
    display_name: str | None = None
    trigger_keywords: list[str] = field(default_factory=list)
    inputs: list[str] = field(default_factory=list)
    workflow: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)

    def validate(self) -> None:
        _validate_slug(self.id, "skill.id")
        _require(self.path.startswith("skills/") and self.path.endswith("/SKILL.md"), f"invalid skill path: {self.path}")
        _require(self.purpose.strip(), f"skill[{self.id}].purpose is required.")
        _validate_string_list(self.trigger_keywords, f"skill[{self.id}].trigger_keywords")
        _validate_string_list(self.inputs, f"skill[{self.id}].inputs")
        _validate_string_list(self.workflow, f"skill[{self.id}].workflow")
        _validate_string_list(self.outputs, f"skill[{self.id}].outputs")
        _validate_string_list(self.constraints, f"skill[{self.id}].constraints")


@dataclass(slots=True)
class TriggerChecks:
    should_trigger_min: int
    should_not_trigger_min: int

    def validate(self) -> None:
        _require(self.should_trigger_min >= 0, "should_trigger_min must be >= 0.")
        _require(self.should_not_trigger_min >= 0, "should_not_trigger_min must be >= 0.")


@dataclass(slots=True)
class EvalSpec:
    enabled: bool
    baseline_mode: str
    trigger_checks: TriggerChecks | None = None
    iterations_dir: str | None = None

    def validate(self) -> None:
        _require(self.baseline_mode in BASELINE_MODES, f"baseline_mode must be one of {sorted(BASELINE_MODES)}.")
        if self.trigger_checks is not None:
            self.trigger_checks.validate()
        if self.iterations_dir is not None:
            _require(self.iterations_dir.strip(), "iterations_dir must not be empty when provided.")


@dataclass(slots=True)
class AgentsPointerSpec:
    target_file: str
    section_title: str
    update_mode: str = "patch"
    append_history: bool = True

    def validate(self) -> None:
        _require(self.target_file == "AGENTS.md", "agents_pointer.target_file must be AGENTS.md.")
        _require(self.section_title.strip(), "agents_pointer.section_title is required.")
        _require(self.update_mode in POINTER_MODES, f"update_mode must be one of {sorted(POINTER_MODES)}.")


@dataclass(slots=True)
class HarnessManifest:
    version: str
    harness: HarnessSpec
    execution: ExecutionSpec
    context: ContextSpec
    roles: list[RoleSpec]
    skills: list[SkillSpec]
    eval: EvalSpec
    agents_pointer: AgentsPointerSpec

    def validate(self) -> None:
        _require(self.version.strip(), "version is required.")
        self.harness.validate()
        self.execution.validate()
        self.context.validate()
        _require(bool(self.roles), "roles must not be empty.")
        _require(bool(self.skills), "skills must not be empty.")

        role_ids = [role.id for role in self.roles]
        skill_ids = [skill.id for skill in self.skills]
        _require(len(role_ids) == len(set(role_ids)), "role ids must be unique.")
        _require(len(skill_ids) == len(set(skill_ids)), "skill ids must be unique.")

        known_roles = set(role_ids)
        for role in self.roles:
            role.validate(known_roles)
        for skill in self.skills:
            skill.validate()
        self.eval.validate()
        self.agents_pointer.validate()

    def to_dict(self) -> dict:
        return asdict(self)
