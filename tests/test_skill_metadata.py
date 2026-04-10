import json

import pytest


yaml = pytest.importorskip("yaml")


def test_plugin_manifest_is_valid_json(repo_root):
    path = repo_root / "plugins" / "meta-harness" / ".codex-plugin" / "plugin.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["name"] == "meta-harness"
    assert payload["skills"] == "./skills/"


def test_meta_harness_skill_has_yaml_frontmatter(repo_root):
    path = repo_root / "plugins" / "meta-harness" / "skills" / "meta-harness" / "SKILL.md"
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    assert "name:" in text
    assert "description:" in text


def test_openai_yaml_exposes_skill_interface(repo_root):
    path = repo_root / "plugins" / "meta-harness" / "skills" / "meta-harness" / "agents" / "openai.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert payload["interface"]["display_name"] == "Meta Harness"
