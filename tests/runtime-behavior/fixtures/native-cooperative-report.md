---
schema_version: 2
session_id: fixture-native-cooperative
started_at: 2026-08-18T00:00:00+09:00
ended_at: 2026-08-18T00:00:31+09:00
user_request: |
  native cooperative lifecycle fixture
---

# Summary

Native cooperative lifecycle completed after the terminal advisor result and all requested mutations.

# Invocations

- id: inv-fixture-advisor
  layer: advisor
  name: retrospective-advisor
  started_at: 2026-08-18T00:00:01+09:00
  ended_at: 2026-08-18T00:00:11+09:00
  termination: completed

# Decisions

- by: orchestrator
  at: 2026-08-18T00:00:12+09:00
  decision: 'Apply retrospective, restage the report, revalidate, then commit and push.'

# Retrospective

- signals: { positive: [], negative: [] }
  what_went_well: []
  what_to_improve: []
  memory_candidates: []
  protocol_feedback: []
  applied_changes: []
