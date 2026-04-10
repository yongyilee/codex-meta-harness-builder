from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .briefs import init_brief, load_brief
from .evals import check_trigger_fit, run_eval
from .scaffold import generate_harness


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate Codex-oriented harness bundles.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_brief_parser = subparsers.add_parser("init-brief", help="Create a starter brief JSON file.")
    init_brief_parser.add_argument("--name", required=True)
    init_brief_parser.add_argument("--domain", required=True)
    init_brief_parser.add_argument("--summary", required=True)
    init_brief_parser.add_argument("--focus-area", action="append", default=[])
    init_brief_parser.add_argument("--output", required=True)

    generate_parser = subparsers.add_parser("generate", help="Generate a harness bundle from a brief JSON file.")
    generate_parser.add_argument("--brief-file", required=True)
    generate_parser.add_argument("--output-dir", default="generated")
    generate_parser.add_argument("--force", action="store_true")
    generate_parser.add_argument("--patch-agents", action="store_true")
    generate_parser.add_argument("--agents-file")

    validate_parser = subparsers.add_parser("validate", help="Validate that a brief can produce a manifest.")
    validate_parser.add_argument("--brief-file", required=True)

    eval_parser = subparsers.add_parser("run-eval", help="Summarize trigger coverage for a generated harness.")
    eval_parser.add_argument("--harness-dir", required=True)

    fit_parser = subparsers.add_parser("check-trigger-fit", help="Check trigger thresholds for a generated harness.")
    fit_parser.add_argument("--harness-dir", required=True)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "init-brief":
        payload = init_brief(args.name, args.domain, args.summary, args.focus_area)
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(output)
        return 0

    if args.command == "generate":
        brief = load_brief(args.brief_file)
        result = generate_harness(
            target_root=args.output_dir,
            brief=brief,
            force=args.force,
            patch_agents=args.patch_agents,
            agents_file=args.agents_file,
        )
        print(result)
        return 0

    if args.command == "validate":
        brief = load_brief(args.brief_file)
        from .briefs import build_manifest_from_brief

        manifest, _, _, _ = build_manifest_from_brief(brief)
        print(manifest.harness.name)
        return 0

    if args.command == "run-eval":
        print(json.dumps(run_eval(args.harness_dir), indent=2, ensure_ascii=False))
        return 0

    if args.command == "check-trigger-fit":
        result = check_trigger_fit(args.harness_dir)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result["passed"] else 1

    parser.print_help(sys.stderr)
    return 2
