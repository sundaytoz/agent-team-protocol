---
schema_version: 2
session_id: fixture-managed-two-agents
started_at: 2026-08-19T12:20:00+09:00
ended_at: 2026-08-19T12:20:21+09:00
user_request: two-agent managed fixture
---

# Summary

Both requested terminal results were collected before completion.

# Invocations

- id: inv-research
  layer: advisor
  name: research-advisor
  environment_invocation_id: env-two-1
  started_at: 2026-08-19T12:20:01+09:00
  ended_at: 2026-08-19T12:20:05+09:00
  output_digest: 'first terminal'
  termination: completed
- id: inv-design
  layer: advisor
  name: design-advisor
  environment_invocation_id: env-two-2
  started_at: 2026-08-19T12:20:02+09:00
  ended_at: 2026-08-19T12:20:20+09:00
  output_digest: 'second terminal'
  termination: completed

# Decisions

- All-results barrier satisfied after the second terminal result.
