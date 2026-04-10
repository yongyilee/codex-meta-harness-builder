from __future__ import annotations

from pathlib import Path
import sys


def _bootstrap() -> None:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "src"
        if (candidate / "meta_harness").exists():
            if str(candidate) not in sys.path:
                sys.path.insert(0, str(candidate))
            return
    raise RuntimeError("Unable to locate src/meta_harness from scaffold_harness.py")


_bootstrap()

from meta_harness.cli import main as cli_main  # noqa: E402
from meta_harness.scaffold import generate_harness, scaffold, update_agents_file, write_json  # noqa: E402

__all__ = ["generate_harness", "scaffold", "update_agents_file", "write_json"]


if __name__ == "__main__":
    raise SystemExit(cli_main(["generate", *sys.argv[1:]]))
