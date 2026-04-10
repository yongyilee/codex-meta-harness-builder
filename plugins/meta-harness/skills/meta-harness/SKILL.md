---
name: meta-harness
description: Generate or update a reusable Codex harness bundle from a user prompt, domain brief, or workflow specification. Use when Codex needs to turn a request into structured role specs, generated skills, eval scaffolding, and an AGENTS.md pointer that another Codex agent can run or extend.
---

# Meta Harness

Generate portable harness bundles. Keep the bundle self-contained, but keep the implementation source of truth in `src/meta_harness`.

## Quick Start

1. Normalize the request into a JSON brief.
2. Run `scripts/scaffold_harness.py` with that brief.
3. Inspect the generated `harness.yaml`, `roles/`, `skills/`, `evals/`, and `AGENTS.pointer.md`.
4. Patch `AGENTS.md` only when the user explicitly wants the target repository wired up.

## Workflow

1. Read the user request and extract:
   - harness name
   - domain
   - summary
   - focus areas or explicit roles
   - target paths
   - should-trigger / should-not-trigger examples
2. Create a brief JSON file if one does not exist yet.
3. Run:

```powershell
python plugins/meta-harness/skills/meta-harness/scripts/scaffold_harness.py `
  --brief-file <brief.json> `
  --output-dir generated `
  [--patch-agents] `
  [--agents-file <path-to-AGENTS.md>]
```

4. Validate the result with:

```powershell
python plugins/meta-harness/skills/meta-harness/scripts/run_eval.py --harness-dir generated/<harness-name>
python plugins/meta-harness/skills/meta-harness/scripts/check_trigger_fit.py --harness-dir generated/<harness-name>
```

## Reading Order

- Read `references/codex-agent-patterns.md` when deciding role decomposition and execution mode.
- Read `references/codex-orchestrator-template.md` when you need to refine role contracts.
- Read `references/codex-skill-writing-guide.md` when generated skills need better frontmatter or trigger descriptions.
- Read `references/codex-validation-guide.md` when eval thresholds or trigger cases are weak.
- Read `references/codex-qa-guide.md` when designing the final validation role.

## Constraints

- Treat `src/meta_harness` as the implementation source of truth.
- Treat `plugins/meta-harness/...` as the Codex-facing distribution surface.
- Do not assume generated role files are native Codex agents; they are internal role specs.
- Keep delegated execution optional. Generated bundles must still make sense in single-agent mode.
- Use file-backed state such as `workspace/tasks.json` and `workspace/runtime/agents.json`.
