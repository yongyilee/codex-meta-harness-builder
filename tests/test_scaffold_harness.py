import pytest


yaml = pytest.importorskip("yaml")
jsonschema = pytest.importorskip("jsonschema")

def test_scaffold_creates_expected_tree(workspace_tmp_path, scaffold_module):
    output_root = scaffold_module.scaffold(workspace_tmp_path, "code-review-harness", force=False)
    expected_paths = [
        output_root / "harness.yaml",
        output_root / "brief.json",
        output_root / "roles" / "orchestrator.md",
        output_root / "skills" / "orchestrate" / "SKILL.md",
        output_root / "evals" / "evals.json",
        output_root / "evals" / "summary.json",
        output_root / "workspace" / "tasks.json",
        output_root / "workspace" / "runtime" / "agents.json",
        output_root / "AGENTS.pointer.md",
    ]
    for path in expected_paths:
        assert path.exists(), path


def test_scaffold_refuses_non_empty_target_without_force(workspace_tmp_path, scaffold_module):
    target = workspace_tmp_path / "code-review-harness"
    target.mkdir(parents=True, exist_ok=True)
    (target / "existing.txt").write_text("occupied\n", encoding="utf-8")

    with pytest.raises(FileExistsError):
        scaffold_module.scaffold(workspace_tmp_path, "code-review-harness", force=False)


def test_scaffold_allows_non_empty_target_with_force(workspace_tmp_path, scaffold_module):
    target = workspace_tmp_path / "code-review-harness"
    target.mkdir(parents=True, exist_ok=True)
    (target / "existing.txt").write_text("occupied\n", encoding="utf-8")

    output_root = scaffold_module.scaffold(workspace_tmp_path, "code-review-harness", force=True)
    assert output_root == target
    assert (target / "harness.yaml").exists()
    assert (target / "workspace" / "tasks.json").exists()
    assert (target / "workspace" / "runtime" / "agents.json").exists()


def test_scaffold_initial_json_files_have_expected_shape(workspace_tmp_path, scaffold_module):
    output_root = scaffold_module.scaffold(workspace_tmp_path, "code-review-harness", force=False)
    tasks = (output_root / "workspace" / "tasks.json").read_text(encoding="utf-8")
    agents = (output_root / "workspace" / "runtime" / "agents.json").read_text(encoding="utf-8")
    summary = (output_root / "evals" / "baseline" / "summary.json").read_text(encoding="utf-8")

    assert '"tasks": []' in tasks
    assert '"agents": []' in agents
    assert '"results": []' in summary


def test_scaffolded_manifest_immediately_validates_against_schema(workspace_tmp_path, scaffold_module, schema):
    output_root = scaffold_module.scaffold(workspace_tmp_path, "code-review-harness", force=False)
    payload = yaml.safe_load((output_root / "harness.yaml").read_text(encoding="utf-8"))
    errors = sorted(jsonschema.Draft202012Validator(schema).iter_errors(payload), key=lambda err: list(err.path))
    assert errors == []


def test_scaffold_can_patch_agents_file(workspace_tmp_path, scaffold_module, fixtures_root, repo_root):
    output_root = scaffold_module.scaffold(workspace_tmp_path, "code-review-harness", force=False)
    agents_file = workspace_tmp_path / "AGENTS.md"
    agents_file.write_text((fixtures_root / "agents" / "AGENTS.base.md").read_text(encoding="utf-8"), encoding="utf-8")

    pointer = (output_root / "AGENTS.pointer.md").read_text(encoding="utf-8")
    scaffold_module.update_agents_file(agents_file, pointer, "Meta Harness: Code Review Harness")

    updated = agents_file.read_text(encoding="utf-8")
    expected_bundle_root = output_root.relative_to(repo_root).as_posix()
    assert "## Meta Harness: Code Review Harness" in updated
    assert f"{expected_bundle_root}/harness.yaml" in updated


def test_force_regeneration_removes_stale_role_and_skill_files(workspace_tmp_path, scaffold_module):
    first_brief = {
        "name": "code-review-harness",
        "domain": "software-engineering",
        "summary": "First pass",
        "focus_areas": ["architecture", "security"],
        "target_paths": ["."],
    }
    second_brief = {
        "name": "code-review-harness",
        "domain": "software-engineering",
        "summary": "Second pass",
        "focus_areas": ["architecture"],
        "target_paths": ["."],
    }

    output_root = scaffold_module.generate_harness(workspace_tmp_path, first_brief, force=False)
    assert (output_root / "roles" / "security.md").exists()
    assert (output_root / "skills" / "security" / "SKILL.md").exists()

    output_root = scaffold_module.generate_harness(workspace_tmp_path, second_brief, force=True)
    assert not (output_root / "roles" / "security.md").exists()
    assert not (output_root / "skills" / "security" / "SKILL.md").exists()


def test_nested_skill_paths_are_preserved(workspace_tmp_path, scaffold_module):
    brief = {
        "name": "custom-harness",
        "domain": "software-engineering",
        "summary": "Custom nested skills",
        "target_paths": ["."],
        "roles": [
            {
                "id": "orchestrator",
                "title": "Custom Orchestrator",
                "kind": "coordinator",
                "agent_type": "default",
                "model": "gpt-5.4-mini",
                "reasoning_effort": "high",
                "inputs": ["user_request"],
                "outputs": ["workspace/artifacts/final-report.md"],
                "responsibilities": ["Coordinate the flow"],
            }
        ],
        "skills": [
            {
                "id": "orchestrate",
                "path": "skills/orchestrate/custom/SKILL.md",
                "purpose": "Run a nested skill path",
            }
        ],
    }

    output_root = scaffold_module.generate_harness(workspace_tmp_path, brief, force=False)
    assert (output_root / "skills" / "orchestrate" / "custom" / "SKILL.md").exists()


def test_orchestrator_keeps_handoff_when_not_first_in_custom_roles(workspace_tmp_path, scaffold_module):
    brief = {
        "name": "ordered-harness",
        "domain": "software-engineering",
        "summary": "Custom ordering",
        "target_paths": ["."],
        "roles": [
            {
                "id": "security",
                "title": "Security Specialist",
                "kind": "specialist",
                "agent_type": "explorer",
                "model": "gpt-5.4-mini",
                "reasoning_effort": "medium",
                "inputs": ["user_request"],
                "outputs": ["workspace/artifacts/security.md"],
                "responsibilities": ["Review security posture"],
            },
            {
                "id": "orchestrator",
                "title": "Harness Orchestrator",
                "kind": "coordinator",
                "agent_type": "default",
                "model": "gpt-5.4-mini",
                "reasoning_effort": "high",
                "inputs": ["user_request"],
                "outputs": ["workspace/artifacts/final-report.md"],
                "responsibilities": ["Coordinate the flow"],
            },
        ],
    }

    output_root = scaffold_module.generate_harness(workspace_tmp_path, brief, force=False)
    manifest = yaml.safe_load((output_root / "harness.yaml").read_text(encoding="utf-8"))
    orchestrator = next(role for role in manifest["roles"] if role["id"] == "orchestrator")
    security = next(role for role in manifest["roles"] if role["id"] == "security")

    assert orchestrator["handoff"]["can_spawn"] == ["security", "quality-gate"]
    assert security.get("handoff", {}).get("can_spawn") in (None, [])


def test_patch_agents_uses_section_title_output_path_and_history_policy(workspace_tmp_path, scaffold_module):
    brief = {
        "name": "code-review-harness",
        "domain": "software-engineering",
        "summary": "Pointer contract",
        "focus_areas": ["architecture"],
        "target_paths": ["."],
        "agents_pointer_section_title": "Meta Harness: Custom Review Bundle",
        "agents_pointer_append_history": False,
    }
    agents_file = workspace_tmp_path / "AGENTS.md"
    agents_file.write_text("# Repo Instructions\n", encoding="utf-8")

    output_root = scaffold_module.generate_harness(
        workspace_tmp_path / "bundles",
        brief,
        force=False,
        patch_agents=True,
        agents_file=agents_file,
    )
    updated = agents_file.read_text(encoding="utf-8")
    pointer = (output_root / "AGENTS.pointer.md").read_text(encoding="utf-8")

    assert "## Meta Harness: Custom Review Bundle" in updated
    assert "`bundles/code-review-harness/harness.yaml`" in updated
    assert "Change log:" not in updated
    assert pointer == updated.split("# Repo Instructions\n\n", 1)[1]


def test_append_mode_appends_duplicate_section(workspace_tmp_path, scaffold_module):
    agents_file = workspace_tmp_path / "AGENTS.md"
    agents_file.write_text("## Meta Harness: Duplicate\nold\n", encoding="utf-8")
    section_text = "## Meta Harness: Duplicate\nnew\n"

    scaffold_module.update_agents_file(agents_file, section_text, "Meta Harness: Duplicate", update_mode="append")

    updated = agents_file.read_text(encoding="utf-8")
    assert updated.count("## Meta Harness: Duplicate") == 2
