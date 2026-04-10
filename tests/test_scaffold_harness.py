import pytest


yaml = pytest.importorskip("yaml")
jsonschema = pytest.importorskip("jsonschema")

def test_scaffold_creates_expected_tree(tmp_path, scaffold_module):
    output_root = scaffold_module.scaffold(tmp_path, "code-review-harness", force=False)
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


def test_scaffold_refuses_non_empty_target_without_force(tmp_path, scaffold_module):
    target = tmp_path / "code-review-harness"
    target.mkdir(parents=True, exist_ok=True)
    (target / "existing.txt").write_text("occupied\n", encoding="utf-8")

    with pytest.raises(FileExistsError):
        scaffold_module.scaffold(tmp_path, "code-review-harness", force=False)


def test_scaffold_allows_non_empty_target_with_force(tmp_path, scaffold_module):
    target = tmp_path / "code-review-harness"
    target.mkdir(parents=True, exist_ok=True)
    (target / "existing.txt").write_text("occupied\n", encoding="utf-8")

    output_root = scaffold_module.scaffold(tmp_path, "code-review-harness", force=True)
    assert output_root == target
    assert (target / "harness.yaml").exists()
    assert (target / "workspace" / "tasks.json").exists()
    assert (target / "workspace" / "runtime" / "agents.json").exists()


def test_scaffold_initial_json_files_have_expected_shape(tmp_path, scaffold_module):
    output_root = scaffold_module.scaffold(tmp_path, "code-review-harness", force=False)
    tasks = (output_root / "workspace" / "tasks.json").read_text(encoding="utf-8")
    agents = (output_root / "workspace" / "runtime" / "agents.json").read_text(encoding="utf-8")
    summary = (output_root / "evals" / "baseline" / "summary.json").read_text(encoding="utf-8")

    assert '"tasks": []' in tasks
    assert '"agents": []' in agents
    assert '"results": []' in summary


def test_scaffolded_manifest_immediately_validates_against_schema(tmp_path, scaffold_module, schema):
    output_root = scaffold_module.scaffold(tmp_path, "code-review-harness", force=False)
    payload = yaml.safe_load((output_root / "harness.yaml").read_text(encoding="utf-8"))
    errors = sorted(jsonschema.Draft202012Validator(schema).iter_errors(payload), key=lambda err: list(err.path))
    assert errors == []


def test_scaffold_can_patch_agents_file(tmp_path, scaffold_module, fixtures_root):
    output_root = scaffold_module.scaffold(tmp_path, "code-review-harness", force=False)
    agents_file = tmp_path / "AGENTS.md"
    agents_file.write_text((fixtures_root / "agents" / "AGENTS.base.md").read_text(encoding="utf-8"), encoding="utf-8")

    pointer = (output_root / "AGENTS.pointer.md").read_text(encoding="utf-8")
    scaffold_module.update_agents_file(agents_file, pointer, "Code Review Harness")

    updated = agents_file.read_text(encoding="utf-8")
    assert "## Meta Harness: Code Review Harness" in updated
    assert "generated/code-review-harness/harness.yaml" in updated
