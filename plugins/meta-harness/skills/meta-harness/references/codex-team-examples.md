# Codex Team Examples

## Code Review Harness

- Pattern: `fanout-fanin`
- Roles: orchestrator, architecture, security, performance, testing, quality-gate
- Good when the user wants a reusable review workflow

## Migration Harness

- Pattern: `review-loop`
- Roles: orchestrator, analyzer, implementer, verifier, quality-gate
- Good when repeated fix-and-verify cycles are needed

## Documentation Harness

- Pattern: `sequential`
- Roles: orchestrator, researcher, writer, reviewer
- Good when a stable content pipeline is more important than parallelism
