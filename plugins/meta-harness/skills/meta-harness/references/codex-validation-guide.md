# Codex Validation Guide

Use validation as part of the product, not as a later add-on.

## Minimum checks

- `harness.yaml` validates against the schema.
- `roles/` exists and each role has at least one output artifact.
- generated skills contain YAML frontmatter.
- `evals/evals.json` has both `should_trigger` and `should_not_trigger`.
- `AGENTS.pointer.md` matches the generated harness name.

## Runtime checks

- Run `scripts/run_eval.py` to emit `evals/summary.json`.
- Run `scripts/check_trigger_fit.py` to fail fast when the bundle has weak trigger coverage.
