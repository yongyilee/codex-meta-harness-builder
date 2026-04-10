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
    raise RuntimeError("Unable to locate src/meta_harness from run_eval.py")


_bootstrap()

from meta_harness.cli import main as cli_main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(cli_main(["run-eval", *sys.argv[1:]]))
