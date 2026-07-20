#!/usr/bin/env python3
"""Validate ATP silent-start lifecycle documentation and compatibility fixtures."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent / "fixtures"
OPTIONAL_FIELDS = {
    "attempt",
    "termination",
    "retry_of",
    "lifecycle_fallback_reason",
}
TERMINATIONS = {
    "completed",
    "failed",
    "interrupted",
    "silent_stall",
    "late_completion",
}
COMMON_FORBIDDEN = {
    "wait_agent",
    "list_agents",
    "followup_task",
    "interrupt_agent",
    "spawn_agent",
    "fork_turns",
}


def load(name: str) -> dict:
    with (FIXTURES / name).open(encoding="utf-8") as handle:
        return json.load(handle)


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def section(text: str, start: str, end: str) -> str:
    return text.split(start, 1)[1].split(end, 1)[0]


def main() -> int:
    failures: list[str] = []
    legacy = load("report-v2-legacy.json")
    current = load("report-v2-lifecycle.json")
    cases_doc = load("lifecycle-cases.json")

    require(legacy["schema_version"] == 2, "legacy report is not schema v2", failures)
    require(current["schema_version"] == 2, "lifecycle report is not schema v2", failures)
    legacy_keys = set(legacy["invocations"][0])
    current_invocation = current["invocations"][0]
    require(set(current_invocation) - legacy_keys == OPTIONAL_FIELDS,
            "new v2 fixture does not add exactly the four lifecycle fields", failures)
    require(current_invocation["termination"] in TERMINATIONS,
            "unknown lifecycle termination", failures)
    require(current_invocation["retry_of"] != current_invocation["id"],
            "clean retry must use a new invocation identity", failures)
    require(current_invocation["model_choice"]["fallback_reason"] is None,
            "lifecycle recovery altered model routing fallback", failures)

    cases = {case["name"]: case for case in cases_doc["cases"]}
    require(set(cases_doc["observable_activity"]) == {
        "output", "explicit_progress", "tool_start", "tool_result", "terminal_or_blocked"
    }, "observable activity contract drift", failures)
    for name in ("long_running_tool_started", "queued", "explicit_blocked", "terminal"):
        require(cases[name].get("state") != "suspected_silent_stall",
                f"excluded case classified as silent stall: {name}", failures)
    for case in cases.values():
        require(case.get("actions_before_approval", []) == [],
                f"mutation before user approval: {case['name']}", failures)

    suspected_path = cases["no_activity_budget_elapsed"]["state_path"]
    require(suspected_path == ["active", "suspected_silent_stall", "awaiting_user_decision"],
            "silent-start pre-approval state path drift", failures)
    require(cases["unknown_observability"]["state"] == "progress_unobservable",
            "unknown progress capability asserted a stall", failures)
    same = cases["same_invocation_followup"]
    require(not same["clean_retry"] and same["attempt_before"] == same["attempt_after"],
            "same-invocation follow-up changed attempt", failures)

    write_retry = cases["approved_clean_retry_write_scope"]
    write_actions = write_retry["actions"]
    require(write_retry["old_invocation_id"] != write_retry["new_invocation_id"],
            "clean retry reused invocation identity", failures)
    require(
        write_actions.index("confirm_termination")
        < write_actions.index("inspect_partial_write")
        < write_actions.index("revoke_ownership")
        < write_actions.index("spawn_new_invocation"),
        "new write invocation started before termination/partial inspection/ownership handoff",
        failures,
    )
    late = cases["late_old_completion"]
    require(late["termination"] == "late_completion" and not late["auto_merge"] and not late["counts_as_success"],
            "late completion was not quarantined", failures)
    require(cases["write_scope_isolation_unknown"]["state"] == "blocked",
            "unisolated write retry did not block", failures)

    fallback = cases_doc["retry_exhausted"]
    require(set(fallback) == {
        "optional_advisory", "required_artifact", "implementation", "verification",
        "destructive_action", "closing_docs_retro"
    }, "phase fallback matrix is incomplete", failures)
    require("skip" not in " ".join(fallback["verification"]),
            "verification fallback permits skip", failures)
    require(set(fallback["verification"]) == {"tier_b_execute", "blocked"},
            "verification must end in Tier B execution or blocked", failures)

    protocol_path = ROOT / "plugins/atp/docs/development/agent-team-protocol.md"
    protocol = protocol_path.read_text(encoding="utf-8")
    lifecycle = section(protocol, "### 2.5", "### 2.6")
    forbidden_hits = sorted(name for name in COMMON_FORBIDDEN if name in lifecycle)
    require(not forbidden_hits,
            f"common lifecycle contract contains Codex tool names: {forbidden_hits}", failures)
    require(not re.search(r"\b\d+\s*(?:초|seconds?|minutes?|분)\b", lifecycle, re.IGNORECASE),
            "common lifecycle contract contains a fixed time value", failures)
    for state in ("active", "suspected_silent_stall", "awaiting_user_decision", "terminating", "retrying", "fallback", "blocked"):
        require(state in lifecycle, f"missing lifecycle state in common protocol: {state}", failures)
    for field in OPTIONAL_FIELDS:
        require(field in protocol, f"missing optional report field: {field}", failures)

    appendix_path = ROOT / "plugins/atp/docs/development/codex-lifecycle-routing.md"
    require(appendix_path.exists(), "Codex lifecycle appendix is missing", failures)
    if appendix_path.exists():
        appendix = appendix_path.read_text(encoding="utf-8")
        for name in COMMON_FORBIDDEN:
            require(name in appendix, f"Codex appendix lacks mapping for {name}", failures)
        require("calibrat" in appendix.lower() or "보정" in appendix,
                "Codex appendix lacks calibration guidance", failures)

    for path in (
        ROOT / "plugins/atp/skills/task/SKILL.md",
        ROOT / "plugins/atp/agents/research-advisor.md",
        ROOT / "plugins/atp/agents/implementation-advisor.md",
    ):
        body = path.read_text(encoding="utf-8")
        require("§2.5" in body, f"execution subject does not reference §2.5: {path}", failures)

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("PASS: lifecycle contract fixtures and documentation invariants")
    return 0


if __name__ == "__main__":
    sys.exit(main())
