from __future__ import annotations

import json
from pathlib import Path


def check_trigger_fit(harness_dir: str | Path) -> dict:
    root = Path(harness_dir)
    payload = json.loads((root / "evals" / "evals.json").read_text(encoding="utf-8"))
    should_trigger = payload["trigger_evals"]["should_trigger"]
    should_not_trigger = payload["trigger_evals"]["should_not_trigger"]
    thresholds = payload["trigger_thresholds"]
    return {
        "target_harness": payload["target_harness"],
        "should_trigger_count": len(should_trigger),
        "should_not_trigger_count": len(should_not_trigger),
        "should_trigger_min": thresholds["should_trigger_min"],
        "should_not_trigger_min": thresholds["should_not_trigger_min"],
        "passed": len(should_trigger) >= thresholds["should_trigger_min"]
        and len(should_not_trigger) >= thresholds["should_not_trigger_min"],
    }


def run_eval(harness_dir: str | Path) -> dict:
    root = Path(harness_dir)
    summary = check_trigger_fit(root)
    summary_path = root / "evals" / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return summary
