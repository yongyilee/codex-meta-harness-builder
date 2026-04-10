# Codex Skill Writing Guide

Generated skills should be portable and immediately understandable by another Codex agent.

## Frontmatter

- Always include only `name` and `description`.
- Put trigger language in `description`, not in the body.
- Make the description self-contained.

## Body structure

- Title
- Purpose
- Trigger cues
- Inputs
- Workflow
- Outputs
- Constraints

## Constraints to keep

- Mention single-agent fallback.
- Mention file-backed shared state.
- Mention that installation/activation is separate from generation.
