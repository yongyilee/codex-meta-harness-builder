# Codex Orchestrator Template

Use this as the baseline contract for orchestrator roles.

## Required responsibilities

- Read `harness.yaml` before dispatching work.
- Decide whether the request can stay single-agent.
- Persist shared state to `workspace/tasks.json` and `workspace/runtime/agents.json`.
- Merge role outputs into a final artifact under `workspace/artifacts/`.

## Required inputs

- `user_request`
- `repository_context`
- `harness_manifest`

## Required outputs

- `workspace/artifacts/final-report.md`

## Handoff rules

- `can_spawn` should list only known role ids.
- `can_message` should usually mirror `can_spawn`.
- If delegation is unavailable, the orchestrator owns completion instead of failing.
