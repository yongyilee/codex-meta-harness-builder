# Codex Agent Patterns

Use these patterns when converting a prompt into a harness design.

## Default stance

- Prefer a harness that still works in single-agent mode.
- Add delegation only when the user explicitly wants parallel work or when the generated bundle is clearly meant for repeated multi-role execution.
- Persist shared state in files, not in `update_plan`.

## Patterns

### Sequential

- Good for deterministic build pipelines.
- Orchestrator hands off to one role at a time.
- Lowest coordination overhead.

### Fanout-Fanin

- Good for review, research, and audit tasks.
- Orchestrator fans out to specialists, then merges outputs.
- Default choice for review-style harnesses.

### Router

- Good when only one branch should run.
- Use when the request needs classification before execution.

### Review Loop

- Good for build -> validate -> revise cycles.
- Keep the loop count explicit in the generated instructions.

## Role defaults

- `coordinator` -> `agent_type: default`, `model: gpt-5.4-mini`, `reasoning_effort: high`
- `specialist` -> `agent_type: explorer`, `model: gpt-5.4-mini`, `reasoning_effort: medium`
- `executor` -> `agent_type: worker`, `model: gpt-5.4-mini`, `reasoning_effort: medium`
- `validator` -> `agent_type: explorer`, `model: gpt-5.4-mini`, `reasoning_effort: medium`
