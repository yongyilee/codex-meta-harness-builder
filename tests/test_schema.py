from pathlib import Path

import pytest


yaml = pytest.importorskip("yaml")
jsonschema = pytest.importorskip("jsonschema")


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _validator(schema: dict):
    return jsonschema.Draft202012Validator(schema)


def test_schema_json_is_parseable(schema: dict):
    assert schema["title"] == "Meta Harness Manifest"


def test_minimal_valid_manifest_passes_validation(fixtures_root, schema):
    payload = _load_yaml(fixtures_root / "manifests" / "minimal-valid.yaml")
    errors = sorted(_validator(schema).iter_errors(payload), key=lambda err: list(err.path))
    assert errors == []


def test_missing_context_manifest_fails_validation(fixtures_root, schema):
    payload = _load_yaml(fixtures_root / "manifests" / "minimal-invalid-missing-context.yaml")
    errors = sorted(_validator(schema).iter_errors(payload), key=lambda err: list(err.path))
    assert errors
    assert any("context" in err.message for err in errors)


def test_empty_roles_manifest_fails_validation(fixtures_root, schema):
    payload = _load_yaml(fixtures_root / "manifests" / "minimal-invalid-empty-roles.yaml")
    errors = sorted(_validator(schema).iter_errors(payload), key=lambda err: list(err.path))
    assert errors
    assert any(list(err.path) == ["roles"] for err in errors)
