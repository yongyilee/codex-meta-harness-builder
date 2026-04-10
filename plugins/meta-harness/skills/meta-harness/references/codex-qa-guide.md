# Codex QA Guide

The QA role should validate boundaries, not just presence.

## What to inspect

- Does the manifest match the generated files?
- Do role handoffs reference existing roles?
- Do output paths stay under `workspace/artifacts/`?
- Are trigger examples specific enough to differentiate harness work from one-off tasks?

## Good QA output

- Call out structural mismatches first.
- Flag missing eval coverage second.
- Recommend the smallest viable fix.
