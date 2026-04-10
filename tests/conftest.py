import importlib.util
import json
from pathlib import Path
import shutil
import sys
import uuid

import pytest


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
PLUGIN_ROOT = ROOT / "plugins" / "meta-harness"
SKILL_ROOT = PLUGIN_ROOT / "skills" / "meta-harness"
SCHEMA_PATH = SKILL_ROOT / "schemas" / "harness.schema.json"
SCAFFOLD_PATH = SKILL_ROOT / "scripts" / "scaffold_harness.py"
TEMPLATES_ROOT = SKILL_ROOT / "templates"
FIXTURES_ROOT = ROOT / "tests" / "fixtures"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


def load_python_module(module_path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return ROOT


@pytest.fixture(scope="session")
def fixtures_root() -> Path:
    return FIXTURES_ROOT


@pytest.fixture(scope="session")
def schema_path() -> Path:
    return SCHEMA_PATH


@pytest.fixture(scope="session")
def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def scaffold_module():
    return load_python_module(SCAFFOLD_PATH, "meta_harness_scaffold")


@pytest.fixture(scope="session")
def template_context(fixtures_root: Path) -> dict:
    path = fixtures_root / "render" / "minimal_context.json"
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture()
def workspace_tmp_path(repo_root: Path):
    root = repo_root / ".test-artifacts"
    root.mkdir(exist_ok=True)
    path = root / uuid.uuid4().hex
    path.mkdir()
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)
