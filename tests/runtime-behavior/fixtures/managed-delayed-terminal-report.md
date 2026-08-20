---
schema_version: 2
session_id: fixture-managed-delayed-terminal
started_at: 2026-08-19T12:10:00+09:00
ended_at: 2026-08-19T12:10:41+09:00
user_request: delayed terminal managed fixture
---

# Summary

The nonterminal update stayed running until the delayed terminal result.

# Invocations

- id: inv-verification
  layer: advisor
  name: verification-advisor
  environment_invocation_id: env-delayed-1
  started_at: 2026-08-19T12:10:01+09:00
  ended_at: 2026-08-19T12:10:40+09:00
  output_digest: 'terminal result'
  termination: completed

# Decisions

- All-results barrier satisfied after the terminal result.
