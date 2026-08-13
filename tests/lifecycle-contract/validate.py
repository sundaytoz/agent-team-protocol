#!/usr/bin/env python3
"""Validate ATP's environment-authoritative subagent lifecycle contract."""

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
EXPECTED_OPTIONAL_FIELDS = {
    "attempt",
    "termination",
    "retry_of",
    "lifecycle_fallback_reason",
}
LEDGER_FIELDS = {
    "recorded_at",
    "logical_task",
    "report_invocation_id",
    "environment_invocation_id",
    "attempt",
    "event",
    "provenance",
    "source_ref",
    "clean_retry_limit",
    "clean_retry_limit_source",
    "retries_spawned",
}
LEDGER_PROVENANCE = {"environment", "user", "advisor"}
ENVIRONMENT_LEDGER_EVENTS = {
    "accepted",
    "queued",
    "running",
    "approval_required",
    "completed",
    "failed",
    "interrupted",
}
RETRY_DECISION_EVENTS = {"retry_approved", "retry_denied"}
IMPLEMENTATION_LEDGER_EVENTS = {
    *ENVIRONMENT_LEDGER_EVENTS,
    *RETRY_DECISION_EVENTS,
    "late_completion",
    "environment_state_unknown",
    "ownership_pending",
    "ownership_active",
    "ownership_paused",
    "ownership_resumed",
}
RESEARCH_LEDGER_EVENTS = {
    *ENVIRONMENT_LEDGER_EVENTS,
    *RETRY_DECISION_EVENTS,
    "result_acceptance_revoked",
    "late_completion",
    "environment_state_unknown",
}
AUTHORITY_LEDGER_FIELDS = {"authority_kind", "authority_ref"}
AUTHORITY_KINDS = {"result_acceptance", "write_ownership"}
WORKER_INVOCATION_FIELDS = {
    "id",
    "layer",
    "name",
    "agent_version",
    "parent_invocation_id",
    "started_at",
    "ended_at",
    "input_digest",
    "output_digest",
    "artifacts",
    "concerns",
    "model_choice",
    "token_usage",
    "attempt",
    "termination",
    "retry_of",
    "lifecycle_fallback_reason",
}
MODEL_CHOICE_FIELDS = {
    "phase",
    "dispatch_size",
    "tier",
    "effort",
    "resolved_model",
    "capped",
    "capped_from",
    "escalation_reason",
    "fallback_reason",
    "rationale",
}
MODEL_ROUTING_PHASES = {
    "analyze",
    "design",
    "code",
    "validation-static",
    "validation-runtime",
    "docs",
    "graphify-exec",
    "graphify-judgment",
}
TOKEN_USAGE_FIELDS = {"input", "output"}
OWNERSHIP_RECORD_FIELDS = {
    "scope_id",
    "scope_kind",
    "scope_paths",
    "state",
    "owner_report_invocation_id",
    "owner_environment_invocation_id",
    "revoked_from_report_invocation_id",
    "revoked_from_environment_invocation_id",
    "handoff_to_report_invocation_id",
    "handoff_to_environment_invocation_id",
    "handoff_at",
    "dependencies",
    "reservation",
    "generated_paths",
    "pause",
}
RESERVATION_FIELDS = {"directory", "namespace", "namespace_key", "schema_files"}
PAUSE_FIELDS = {
    "reason",
    "source_ref",
    "caused_by_report_invocation_id",
    "caused_by_environment_invocation_id",
}
OWNERSHIP_STATES = {"reserved", "active", "pending_handoff", "paused", "released"}
REQUIRED_RESEARCH_TOOLS = {
    "Read",
    "Grep",
    "Glob",
    "Write",
    "Edit",
    "Bash",
    "WebFetch",
    "WebSearch",
    "Agent",
    "LSP",
}
AUTHORITATIVE_EVENTS = {
    "accepted",
    "queued",
    "running",
    "approval_required",
    "completed",
    "failed",
    "interrupted",
    "blocked",
    "environment_state_unknown",
}
REQUIRED_AUTHORITY_CASES = {
    "timeouts_do_not_change_running",
    "no_progress_then_completed",
    "progress_does_not_grant_liveness",
    "same_snapshot_is_no_transition",
    "explicit_failed_opens_recovery",
    "approval_is_propagated",
    "interrupted_checks_ownership",
    "unknown_is_not_failure",
    "late_completion_is_quarantined",
    "verification_is_not_skipped",
}
NON_AUTHORITATIVE_OBSERVATIONS = {
    "wait_timeout",
    "progress",
    "output",
    "tool_start",
    "tool_result",
    "same_snapshot",
    "no_progress",
}
SAFETY_CASES = {
    "same_invocation_followup",
    "approved_clean_retry_read_only",
    "approved_clean_retry_write_scope",
    "completion_before_retry_approval",
    "write_scope_isolation_unknown",
}
AUTHORITY_ISOLATION_CASES = {
    "read_only_completion_before_acceptance_revocation",
    "read_only_late_completion_after_acceptance_revocation",
    "write_late_completion_without_disk_write",
    "write_late_disk_write_pauses_dependency_closure",
    "late_completion_without_prior_authority_revocation_is_invalid",
}
APPROVAL_CAPABILITY_CASES = {
    "observed_approval_relay_supported",
    "observed_approval_relay_unavailable",
    "status_unavailable_is_unknown",
    "status_error_is_unknown",
    "observed_approval_downgraded_to_unknown_is_invalid",
}
CONFIDENCE_DERIVATION_CASES = {
    "all_confirmed_is_high",
    "all_estimated_is_mixed",
    "nonmajority_unverified_is_mixed",
    "strict_majority_unverified_is_low",
    "multiple_axis_sets_derive_artifact_aggregate",
    "missing_marker_is_invalid",
    "duplicate_identity_is_invalid",
    "duplicate_marker_is_invalid",
    "item_aggregate_namespace_is_invalid",
    "aggregate_item_namespace_is_invalid",
    "aggregate_mismatch_is_invalid",
}
LIFECYCLE_REASON_CASES = {
    "failed_awaiting_user",
    "interrupted_approved_retry",
    "failed_phase_fallback",
    "interrupted_blocked",
    "late_completion_reason",
    "completed_reason_null",
    "approval_nonterminal_reason_null",
    "abnormal_reason_missing_is_invalid",
    "unknown_disposition_is_invalid",
    "empty_rationale_is_invalid",
    "late_completion_wrong_disposition_is_invalid",
}
ITEM_CONFIDENCE_MARKERS = {"확인됨", "추정", "미확인"}
AGGREGATE_CONFIDENCE = {"high", "mixed", "low"}
RECOVERY_DISPOSITIONS = {
    "awaiting_user_decision",
    "approved_clean_retry",
    "phase_fallback",
    "blocked",
    "late_completion_quarantined",
}
ABNORMAL_TERMINATIONS = {"failed", "interrupted", "late_completion"}
REASON_PATTERN = re.compile(
    r"^cause=(failed|interrupted|late_completion)@([^;]+); "
    r"disposition=([a-z_]+); rationale=(.+)$"
)
NEW_PRODUCER_TERMINATIONS = {
    "completed",
    "failed",
    "interrupted",
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
DEPRECATED_ACTIVE_TERMS = {
    "suspected_silent_stall",
    "start_silence_budget",
    "unchanged_check_budget",
}


def load(name: str) -> dict:
    with (FIXTURES / name).open(encoding="utf-8") as handle:
        return json.load(handle)


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def between(text: str, start: str, end: str) -> str:
    if start not in text or end not in text.split(start, 1)[1]:
        raise ValueError(f"section boundary missing: {start!r} .. {end!r}")
    return text.split(start, 1)[1].split(end, 1)[0]


def active_scope(path: Path, start: str, end: str, failures: list[str]) -> str:
    try:
        return between(path.read_text(encoding="utf-8"), start, end)
    except (OSError, ValueError) as exc:
        failures.append(f"cannot read active lifecycle scope in {path}: {exc}")
        return ""


def require_terms(
    body: str, terms: set[str], label: str, failures: list[str]
) -> None:
    missing = sorted(term for term in terms if term not in body)
    require(not missing, f"{label} lacks required terms: {missing}", failures)


def require_ordered(
    body: str, anchors: list[str], label: str, failures: list[str]
) -> None:
    positions: list[int] = []
    cursor = 0
    for anchor in anchors:
        position = body.find(anchor, cursor)
        positions.append(position)
        if position >= 0:
            cursor = position + len(anchor)
    require(
        all(position >= 0 for position in positions),
        f"{label} lacks required ordering: {anchors}",
        failures,
    )


def require_ordered_sequence(
    sequence: list[str], anchors: list[str], label: str, failures: list[str]
) -> None:
    cursor = 0
    positions: list[int] = []
    for anchor in anchors:
        try:
            position = sequence.index(anchor, cursor)
        except ValueError:
            position = -1
        positions.append(position)
        if position >= 0:
            cursor = position + 1
    require(
        all(position >= 0 for position in positions),
        f"{label} lacks required ordering: {anchors}",
        failures,
    )


def row_identity(row: dict) -> tuple[object, object]:
    return row.get("report_invocation_id"), row.get("environment_invocation_id")


def collect_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        keys = set(value)
        for nested in value.values():
            keys.update(collect_keys(nested))
        return keys
    if isinstance(value, list):
        keys: set[str] = set()
        for nested in value:
            keys.update(collect_keys(nested))
        return keys
    return set()


def fenced_blocks(body: str, language: str) -> list[str]:
    return re.findall(
        rf"```{re.escape(language)}\s*\n(.*?)\n```",
        body,
        re.DOTALL,
    )


def ledger_example(body: str) -> dict:
    for block in fenced_blocks(body, "json"):
        try:
            value = json.loads(block)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and "event" in value and "provenance" in value:
            return value
    return {}


def yaml_keys_at_indent(block: str, spaces: int) -> set[str]:
    prefix = " " * spaces
    return set(
        re.findall(rf"^{re.escape(prefix)}(?:- )?([a-z_]+):", block, re.MULTILINE)
    )


def yaml_record_keys(block: str) -> set[str]:
    return yaml_keys_at_indent(block, 4) | set(
        re.findall(r"^ {2}- ([a-z_]+):", block, re.MULTILINE)
    )


def yaml_child_block(block: str, key: str, indent: int) -> str:
    lines = block.splitlines()
    marker = f"{' ' * indent}{key}:"
    for index, line in enumerate(lines):
        if line == marker or line.startswith(f"{marker} "):
            children: list[str] = []
            for candidate in lines[index + 1 :]:
                if candidate.strip() and len(candidate) - len(candidate.lstrip()) <= indent:
                    break
                children.append(candidate)
            return "\n".join(children)
    return ""


def source_example(body: str, root_key: str) -> str:
    for block in fenced_blocks(body, "yaml"):
        if re.search(rf"^{re.escape(root_key)}:", block, re.MULTILINE):
            return block
    return ""


def require_cooccurring_terms(
    body: str, terms: set[str], label: str, failures: list[str]
) -> None:
    paragraphs = re.split(r"\n\s*\n", body)
    require(
        any(all(term in paragraph for term in terms) for paragraph in paragraphs),
        f"{label} lacks one coherent semantic anchor containing: {sorted(terms)}",
        failures,
    )


def normalized_semantic_text(body: str) -> str:
    """Normalize presentation-only Markdown differences for prose contracts."""
    return re.sub(
        r"\s+",
        " ",
        body.lower()
        .replace("`", "")
        .replace("**", "")
        .replace("‐", "-")
        .replace("‑", "-")
        .replace("–", "-")
        .replace("—", "-"),
    ).strip()


def semantic_paragraph(
    body: str, term_groups: tuple[tuple[str, ...], ...]
) -> str:
    """Return one paragraph containing at least one normalized term per group."""
    for paragraph in re.split(r"\n\s*\n", body):
        normalized = normalized_semantic_text(paragraph)
        if all(
            any(normalized_semantic_text(term) in normalized for term in alternatives)
            for alternatives in term_groups
        ):
            return paragraph
    return ""


def has_item_marker_vocabulary(body: str) -> bool:
    normalized = normalized_semantic_text(body)
    korean = all(marker in normalized for marker in ITEM_CONFIDENCE_MARKERS)
    english = all(
        marker in normalized for marker in {"confirmed", "estimated", "unverified"}
    )
    return korean or english


def confidence_mapping_anchor(body: str) -> str:
    """Find a coherent item/aggregate namespace and truth-table prose block."""
    paragraphs = [
        paragraph for paragraph in re.split(r"\n\s*\n", body) if paragraph.strip()
    ]
    for start in range(len(paragraphs)):
        for width in range(1, min(3, len(paragraphs) - start) + 1):
            paragraph = "\n\n".join(paragraphs[start : start + width])
            normalized = normalized_semantic_text(paragraph)
            if not (
                has_item_marker_vocabulary(paragraph)
                and all(term in normalized for term in AGGREGATE_CONFIDENCE)
                and "source_confidence" in normalized
                and "namespace" in normalized
                and "strict majority" in normalized
            ):
                continue
            all_confirmed_is_high = (
                re.search(
                    r"(?:전\s*(?:항목|axis/item)|전부|모든[^,.]{0,30})\s*확인됨"
                    r"[^,.]{0,50}high",
                    normalized,
                )
                is not None
                or re.search(
                    r"high[^,.]{0,50}(?:all|every)[^,.]{0,30}confirmed",
                    normalized,
                )
                is not None
            )
            strict_majority_unverified_is_low = (
                re.search(r"미확인[^,.]{0,60}low", normalized) is not None
                or re.search(r"low[^,.]{0,60}미확인", normalized) is not None
                or re.search(
                    r"unverified[^,.]{0,60}strict majority[^,.]{0,60}low",
                    normalized,
                )
                is not None
                or re.search(
                    r"low[^,.]{0,60}unverified[^,.]{0,60}strict majority",
                    normalized,
                )
                is not None
            )
            otherwise_is_mixed = (
                re.search(r"(?:나머지|그 밖)[^,.]{0,50}mixed", normalized)
                is not None
                or re.search(
                    r"mixed[^,.]{0,50}(?:every other|otherwise)", normalized
                )
                is not None
            )
            if (
                all_confirmed_is_high
                and strict_majority_unverified_is_low
                and otherwise_is_mixed
            ):
                return paragraph
    return ""


def has_confidence_self_checks(body: str) -> bool:
    """Accept canonical or localized labels while retaining both check semantics."""
    normalized = normalized_semantic_text(body)
    marker_coverage_label = any(
        term in normalized
        for term in (
            "marker coverage",
            "마커 커버리지",
            "마커 전수성",
            "마커 적용 범위",
        )
    )
    aggregate_derivation_label = any(
        term in normalized
        for term in (
            "aggregate derivation",
            "집계 도출",
            "집계값 도출",
            "집계값 유도",
        )
    )
    coverage_semantics = (
        ("marker" in normalized or "마커" in normalized)
        and ("identity" in normalized or "식별" in normalized)
        and ("정확히 하나" in normalized or "exactly one" in normalized)
        and ("같" in normalized or "equal" in normalized)
    )
    derivation_semantics = (
        "source_confidence" in normalized
        and ("재계산" in normalized or "recompute" in normalized)
        and ("일치" in normalized or "compare" in normalized or "match" in normalized)
    )
    return (
        (marker_coverage_label or coverage_semantics)
        and (aggregate_derivation_label or derivation_semantics)
        and coverage_semantics
        and derivation_semantics
    )


def has_same_environment_continuation_accounting(body: str) -> bool:
    """Recognize equivalent same-invocation/identity continuation wording."""
    identity_terms = (
        "same identity",
        "same invocation",
        "same environment identity",
        "same environment invocation",
        "같은 environment identity",
        "같은 environment invocation",
        "동일 thread/invocation",
    )
    no_change_terms = (
        "바꾸지 않",
        "그대로 유지",
        "증가시키지 않",
        "증가는 모두 0건",
        "불변",
        "do not change",
        "does not change",
        "remain unchanged",
    )
    paragraphs = [
        paragraph for paragraph in re.split(r"\n\s*\n", body) if paragraph.strip()
    ]
    for start in range(len(paragraphs)):
        for width in range(1, min(2, len(paragraphs) - start) + 1):
            normalized = normalized_semantic_text(
                "\n\n".join(paragraphs[start : start + width])
            )
            if (
                any(term in normalized for term in identity_terms)
                and "attempt" in normalized
                and "retry" in normalized
                and any(term in normalized for term in no_change_terms)
            ):
                return True
    return False


def has_immediate_intermediate_reason(body: str) -> bool:
    """Require abnormal reason serialization before retry exhaustion."""
    normalized = normalized_semantic_text(body)
    first_serialization = (
        "첫 serialization" in normalized
        or "첫 abnormal serialization" in normalized
        or "first serialization" in normalized
    )
    intermediate = (
        "중간 invocation" in normalized
        or "intermediate invocation" in normalized
        or (
            "awaiting_user_decision" in normalized
            and ("decision 전" in normalized or "before the decision" in normalized)
        )
    )
    no_exhaustion_wait = (
        re.search(
            r"retry[^.]{0,50}(?:exhaust|소진|cap)[^.]{0,50}기다리지",
            normalized,
        )
        is not None
        or re.search(
            r"(?:not|never)[^.]{0,50}(?:defer|wait)[^.]{0,80}retr(?:y|ies)"
            r"[^.]{0,50}exhaust",
            normalized,
        )
        is not None
    )
    return first_serialization and intermediate and no_exhaustion_wait


def derived_confidence(markers: list[str]) -> str | None:
    if not markers or any(marker not in ITEM_CONFIDENCE_MARKERS for marker in markers):
        return None
    if all(marker == "확인됨" for marker in markers):
        return "high"
    if sum(marker == "미확인" for marker in markers) > len(markers) / 2:
        return "low"
    return "mixed"


def parsed_lifecycle_reason(value: object) -> tuple[str, str, str, str] | None:
    if not isinstance(value, str):
        return None
    match = REASON_PATTERN.fullmatch(value)
    if not match:
        return None
    cause, source_ref, disposition, rationale = match.groups()
    if not source_ref.strip() or not rationale.strip():
        return None
    return cause, source_ref, disposition, rationale


def validate_reports(failures: list[str]) -> None:
    legacy = load("report-v2-legacy.json")
    old_lifecycle = load("report-v2-lifecycle.json")
    environment = load("report-v2-environment.json")

    reports = {
        "legacy": legacy,
        "old lifecycle": old_lifecycle,
        "environment": environment,
    }
    require(
        OPTIONAL_FIELDS == EXPECTED_OPTIONAL_FIELDS,
        "report schema v2 optional lifecycle field contract is not exactly four fields",
        failures,
    )
    ledger_only_fields = (LEDGER_FIELDS - {"attempt"}) | AUTHORITY_LEDGER_FIELDS
    require(
        OPTIONAL_FIELDS.isdisjoint(ledger_only_fields),
        "phase-local lifecycle ledger fields leaked into report optional fields",
        failures,
    )
    for label, report in reports.items():
        require(report["schema_version"] == 2, f"{label} report is not schema v2", failures)
        require(len(report["invocations"]) == 1, f"{label} fixture must contain one invocation", failures)
        require(
            set(report["invocations"][0]).isdisjoint(ledger_only_fields),
            f"{label} report contains phase-local lifecycle ledger fields",
            failures,
        )

    legacy_keys = set(legacy["invocations"][0])
    for label, report in (("old lifecycle", old_lifecycle), ("environment", environment)):
        invocation = report["invocations"][0]
        require(
            set(invocation) - legacy_keys == OPTIONAL_FIELDS,
            f"{label} v2 fixture does not add exactly the four lifecycle fields",
            failures,
        )
        require(
            invocation["model_choice"]["fallback_reason"] is None,
            f"{label} lifecycle state altered model routing fallback",
            failures,
        )

    old_invocation = old_lifecycle["invocations"][0]
    require(
        old_invocation["termination"] == "silent_stall",
        "old lifecycle fixture no longer proves silent_stall reader compatibility",
        failures,
    )
    require(
        old_invocation["retry_of"] != old_invocation["id"],
        "legacy clean retry reused its invocation identity",
        failures,
    )
    require(
        isinstance(old_invocation.get("lifecycle_fallback_reason"), str)
        and bool(old_invocation["lifecycle_fallback_reason"].strip()),
        "legacy v2 free-text lifecycle fallback reason is no longer readable",
        failures,
    )

    environment_invocation = environment["invocations"][0]
    require(
        environment_invocation["termination"] in NEW_PRODUCER_TERMINATIONS,
        "environment producer lacks an explicit environment terminal event",
        failures,
    )
    require(
        environment_invocation["termination"] != "silent_stall",
        "new environment producer emitted legacy-only silent_stall",
        failures,
    )
    retry_of = environment_invocation["retry_of"]
    require(
        retry_of is None or retry_of != environment_invocation["id"],
        "environment producer reused its invocation identity",
        failures,
    )


def validate_cases(failures: list[str]) -> None:
    cases_doc = load("lifecycle-cases.json")
    require(
        set(cases_doc["authoritative_events"]) == AUTHORITATIVE_EVENTS,
        "authoritative environment event vocabulary drift",
        failures,
    )
    require(
        set(cases_doc["non_authoritative_observations"])
        == NON_AUTHORITATIVE_OBSERVATIONS,
        "non-authoritative observation vocabulary drift",
        failures,
    )

    cases = {case["name"]: case for case in cases_doc["cases"]}
    require(set(cases) == REQUIRED_AUTHORITY_CASES, "authority case set is not the required ten", failures)
    for case in cases.values():
        require(
            set(case.get("events", [])) <= AUTHORITATIVE_EVENTS,
            f"unknown authority event in case: {case['name']}",
            failures,
        )
        require(
            set(case.get("observations", [])) <= NON_AUTHORITATIVE_OBSERVATIONS,
            f"unknown non-authoritative observation in case: {case['name']}",
            failures,
        )
        require(
            case.get("actions_before_approval", []) == [],
            f"mutation before user approval: {case['name']}",
            failures,
        )
        require(
            case.get("retry_or_fallback") is False,
            f"observation or unapproved event opened retry/fallback: {case['name']}",
            failures,
        )

    timeouts = cases["timeouts_do_not_change_running"]
    require(
        timeouts["expected_state"] == "running"
        and set(timeouts["observations"]) == {"wait_timeout"},
        "wait timeout changed authoritative running state",
        failures,
    )
    no_progress = cases["no_progress_then_completed"]
    require(
        no_progress["expected_state_path"] == ["accepted", "running", "completed"]
        and no_progress["result_disposition"] == "validate_and_collect",
        "no-progress path did not preserve environment completion",
        failures,
    )
    progress = cases["progress_does_not_grant_liveness"]
    require(
        progress["expected_state_path"] == ["accepted", "running", "failed"]
        and progress["recovery_trigger"] == "explicit_environment_failed",
        "progress observation overrode explicit environment failure",
        failures,
    )
    same_snapshot = cases["same_snapshot_is_no_transition"]
    require(
        same_snapshot["expected_state"] == "running"
        and same_snapshot["transition_count_from_observations"] == 0,
        "same snapshot produced a lifecycle transition",
        failures,
    )
    failed = cases["explicit_failed_opens_recovery"]
    require(
        failed["expected_state"] == "failed" and failed["recovery_review"] == "open",
        "explicit environment failure did not open recovery review",
        failures,
    )
    approval = cases["approval_is_propagated"]
    require(
        approval["expected_state"] == "approval_required"
        and approval["approval_flow"] == "propagate_to_user"
        and approval["approval_grants_retry_or_fallback"] is False,
        "environment approval event was treated as recovery approval",
        failures,
    )
    interrupted = cases["interrupted_checks_ownership"]
    require(
        interrupted["expected_state"] == "interrupted"
        and interrupted["write_capable"] is True
        and interrupted["actions"] == ["inspect_partial_write", "confirm_ownership_recovery"]
        and interrupted["spawn_before_ownership_recovery"] is False,
        "interrupted write invocation bypassed ownership recovery",
        failures,
    )
    unknown = cases["unknown_is_not_failure"]
    require(
        unknown["expected_state"] == "environment_state_unknown"
        and unknown["terminal"] is False,
        "unknown environment state was classified as terminal failure",
        failures,
    )
    late = cases["late_completion_is_quarantined"]
    require(
        late["termination"] == "late_completion"
        and late["ownership_revoked_before_completion"] is True
        and late["actions"] == ["quarantine_old_result"]
        and late["auto_merge"] is False
        and late["counts_as_success"] is False,
        "late completion was not quarantined",
        failures,
    )
    verification = cases["verification_is_not_skipped"]
    require(
        verification["phase"] == "mandatory_verification"
        and set(verification["allowed_terminal_actions"]) == {"tier_b_execute", "blocked"}
        and verification["skip_allowed"] is False,
        "verification failure permits skip",
        failures,
    )

    safety = {case["name"]: case for case in cases_doc["safety_cases"]}
    require(set(safety) == SAFETY_CASES, "ADR-0017 safety case set is incomplete", failures)
    same = safety["same_invocation_followup"]
    require(
        not same["clean_retry"] and same["attempt_before"] == same["attempt_after"],
        "same-invocation follow-up changed attempt",
        failures,
    )
    read_retry = safety["approved_clean_retry_read_only"]
    require(
        read_retry["approved"] is True
        and read_retry["old_invocation_id"] != read_retry["new_invocation_id"]
        and read_retry["retry_of"] == read_retry["old_invocation_id"]
        and read_retry["actions"].index("confirm_termination")
        < read_retry["actions"].index("spawn_new_invocation"),
        "read-only clean retry violated approval, identity, or termination ordering",
        failures,
    )
    write_retry = safety["approved_clean_retry_write_scope"]
    require(
        write_retry["approved"] is True
        and write_retry["old_invocation_id"] != write_retry["new_invocation_id"]
        and write_retry["retry_of"] == write_retry["old_invocation_id"],
        "write clean retry violated approval or identity",
        failures,
    )
    write_actions = write_retry["actions"]
    require(
        write_actions.index("confirm_termination")
        < write_actions.index("inspect_partial_write")
        < write_actions.index("revoke_ownership")
        < write_actions.index("spawn_new_invocation"),
        "write retry bypassed termination, partial-write inspection, or ownership handoff",
        failures,
    )
    completion_race = safety["completion_before_retry_approval"]
    require(
        completion_race["approved"] is False
        and completion_race["old_completion"] == "before_approval"
        and completion_race["actions"] == ["review_old_result", "cancel_retry"]
        and completion_race["auto_merge"] is False,
        "completion-before-approval race did not cancel retry",
        failures,
    )
    isolation = safety["write_scope_isolation_unknown"]
    require(
        isolation["expected_state"] == "blocked"
        and isolation["termination_confirmed"] is False
        and isolation["isolation_confirmed"] is False
        and isolation["actions"] == [],
        "unisolated write retry did not block",
        failures,
    )

    # AC-R28 through AC-R31 and AC-R34: deterministic authority-isolation
    # traces preserve approval/race/revocation order, join late dispositions to
    # the same old identity, and keep read/no-disk effects disjoint from writes.
    authority_case_list = cases_doc.get("authority_isolation_cases", [])
    authority_cases = {case["name"]: case for case in authority_case_list}
    require(
        len(authority_cases) == len(authority_case_list)
        and set(authority_cases) == AUTHORITY_ISOLATION_CASES,
        "authority isolation case set is not the required deterministic five",
        failures,
    )

    for name, case in authority_cases.items():
        ledger = case.get("ledger", [])
        for index, row in enumerate(ledger):
            require(
                LEDGER_FIELDS <= set(row),
                f"authority ledger row lacks common fields: {name}[{index}]",
                failures,
            )
            require(
                bool(row.get("source_ref")),
                f"authority ledger row has an empty source_ref: {name}[{index}]",
                failures,
            )
            event = row.get("event")
            expected_provenance = (
                "environment"
                if event in ENVIRONMENT_LEDGER_EVENTS
                else "user"
                if event in RETRY_DECISION_EVENTS
                else "advisor"
            )
            require(
                row.get("provenance") == expected_provenance,
                f"authority ledger event provenance mismatch: {name}[{index}]",
                failures,
            )
            if event in RETRY_DECISION_EVENTS or event in {
                "result_acceptance_revoked",
                "late_completion",
                "ownership_pending",
                "ownership_active",
                "ownership_paused",
            }:
                require(
                    bool(row.get("scope")) and bool(row.get("rationale")),
                    f"authority event lacks scope/rationale: {name}[{index}]",
                    failures,
                )
            if event == "late_completion":
                require(
                    row.get("authority_kind") in AUTHORITY_KINDS
                    and bool(row.get("authority_ref")),
                    f"accepted late disposition lacks authority kind/ref: {name}[{index}]",
                    failures,
                )
            if event in {"result_acceptance_revoked", "late_completion", "ownership_pending"}:
                require(
                    all(row_identity(row)),
                    f"authority event lacks its report/environment identity pair: {name}[{index}]",
                    failures,
                )
        retry_limits = {row.get("clean_retry_limit") for row in ledger}
        retry_sources = {row.get("clean_retry_limit_source") for row in ledger}
        retry_counts = [row.get("retries_spawned") for row in ledger]
        require(
            len(retry_limits) == 1
            and len(retry_sources) == 1
            and None not in retry_limits
            and None not in retry_sources
            and retry_counts == sorted(retry_counts)
            and all(count <= next(iter(retry_limits)) for count in retry_counts),
            f"authority trace changed immutable retry configuration: {name}",
            failures,
        )

    completion_race = authority_cases.get(
        "read_only_completion_before_acceptance_revocation", {}
    )
    race_ledger = completion_race.get("ledger", [])
    require_ordered_sequence(
        completion_race.get("sequence", []),
        ["interrupted", "retry_approved", "completion_race_rechecked", "completed"],
        "read-only completion-before-revocation race",
        failures,
    )
    race_events = [row.get("event") for row in race_ledger]
    race_expected = completion_race.get("expected", {})
    require(
        "result_acceptance_revoked" not in race_events
        and "late_completion" not in race_events
        and race_expected
        == {
            "result_disposition": "normal_candidate",
            "retry_spawns": 0,
            "result_acceptance_revocations": 0,
            "late_completion_dispositions": 0,
        },
        "completion before authority revocation did not remain a normal candidate",
        failures,
    )

    read_late = authority_cases.get(
        "read_only_late_completion_after_acceptance_revocation", {}
    )
    read_sequence = read_late.get("sequence", [])
    read_ledger = read_late.get("ledger", [])
    require_ordered_sequence(
        read_sequence,
        [
            "interrupted",
            "retry_approved",
            "completion_race_rechecked",
            "result_acceptance_revoked",
            "new_identity_issued",
            "completed",
            "late_completion",
        ],
        "read-only authority revocation and late disposition",
        failures,
    )
    read_revocations = [
        row for row in read_ledger if row.get("event") == "result_acceptance_revoked"
    ]
    read_accepts = [row for row in read_ledger if row.get("event") == "accepted"]
    read_completions = [row for row in read_ledger if row.get("event") == "completed"]
    read_late_rows = [row for row in read_ledger if row.get("event") == "late_completion"]
    require(
        len(read_revocations) == len(read_accepts) == len(read_completions) == len(read_late_rows) == 1,
        "read-only late trace must have one revocation, retry identity, completion, and disposition",
        failures,
    )
    if read_revocations and read_accepts and read_completions and read_late_rows:
        revoked = read_revocations[0]
        accepted = read_accepts[0]
        completed = read_completions[0]
        late = read_late_rows[0]
        require(
            row_identity(revoked) == row_identity(completed) == row_identity(late)
            and row_identity(accepted) != row_identity(revoked)
            and late.get("authority_kind") == "result_acceptance"
            and late.get("authority_ref") == revoked.get("source_ref")
            and late.get("source_ref") == completed.get("source_ref")
            and read_ledger.index(revoked) < read_ledger.index(accepted)
            < read_ledger.index(completed) < read_ledger.index(late),
            "read-only late disposition lacks same-identity revocation/reference ordering",
            failures,
        )
    require(
        read_late.get("expected", {})
        == {
            "result_disposition": "quarantine_only",
            "retry_spawns": 1,
            "auto_merge": False,
            "counts_as_success": False,
            "ownership_pause_scopes": [],
            "ownership_mutations_after_late_completion": 0,
        },
        "read-only late completion is not quarantine-only",
        failures,
    )

    def validate_write_late_anchor(case: dict, label: str) -> tuple[dict, dict]:
        sequence = case.get("sequence", [])
        ledger = case.get("ledger", [])
        require_ordered_sequence(
            sequence,
            [
                "interrupted",
                "retry_approved",
                "completion_race_rechecked",
                "ownership_pending",
                "new_identity_issued",
                "ownership_active",
                "completed",
                "late_completion",
            ],
            label,
            failures,
        )
        pending = [row for row in ledger if row.get("event") == "ownership_pending"]
        active = [row for row in ledger if row.get("event") == "ownership_active"]
        completed = [row for row in ledger if row.get("event") == "completed"]
        late = [row for row in ledger if row.get("event") == "late_completion"]
        require(
            len(pending) == len(active) == len(completed) == len(late) == 1,
            f"{label} must contain one ownership anchor, new owner, completion, and disposition",
            failures,
        )
        if not (pending and active and completed and late):
            return {}, {}
        require(
            row_identity(pending[0]) == row_identity(completed[0]) == row_identity(late[0])
            and row_identity(active[0]) != row_identity(pending[0])
            and late[0].get("authority_kind") == "write_ownership"
            and late[0].get("authority_ref") == pending[0].get("source_ref")
            and late[0].get("source_ref") == completed[0].get("source_ref")
            and ledger.index(pending[0]) < ledger.index(active[0])
            < ledger.index(completed[0]) < ledger.index(late[0]),
            f"{label} lacks same-identity write authority/reference ordering",
            failures,
        )
        return pending[0], late[0]

    write_safe = authority_cases.get("write_late_completion_without_disk_write", {})
    validate_write_late_anchor(write_safe, "write late completion without disk mutation")
    require(
        write_safe.get("disk_writes_after_revocation") == []
        and write_safe.get("expected", {})
        == {
            "result_disposition": "quarantine_only",
            "auto_merge": False,
            "counts_as_success": False,
            "ownership_pause_scopes": [],
            "ownership_mutations_after_late_completion": 0,
        },
        "write late result without disk mutation changed ownership or success",
        failures,
    )

    write_disk = authority_cases.get(
        "write_late_disk_write_pauses_dependency_closure", {}
    )
    _, write_disk_late = validate_write_late_anchor(
        write_disk, "write late disk mutation"
    )
    require_ordered_sequence(
        write_disk.get("sequence", []),
        ["late_completion", "late_disk_write_detected", "ownership_paused"],
        "late disk write pause ordering",
        failures,
    )
    ownership_graph = write_disk.get("ownership_graph", [])
    dependencies = {
        record.get("scope_id"): set(record.get("dependencies", []))
        for record in ownership_graph
    }
    affected = set(write_disk_late.get("scope", []))
    changed = True
    while changed:
        changed = False
        for scope_id, scope_dependencies in dependencies.items():
            if scope_id not in affected and scope_dependencies & affected:
                affected.add(scope_id)
                changed = True
    disk_expected = write_disk.get("expected", {})
    pause_rows = [
        row for row in write_disk.get("ledger", []) if row.get("event") == "ownership_paused"
    ]
    require(
        bool(write_disk.get("disk_writes_after_revocation"))
        and len(pause_rows) == 1
        and set(pause_rows[0].get("scope", [])) == affected
        and set(disk_expected.get("persisted_paused_scopes", [])) == affected
        and set(disk_expected.get("active_scopes", [])) == set(dependencies) - affected
        and disk_expected.get("auto_merge") is False
        and disk_expected.get("counts_as_success") is False,
        "late disk write did not persist exactly the affected dependency closure",
        failures,
    )

    invalid = authority_cases.get(
        "late_completion_without_prior_authority_revocation_is_invalid", {}
    )
    invalid_ledger = invalid.get("ledger", [])
    invalid_candidates = invalid.get("candidate_late_completions", [])
    completed_rows = [row for row in invalid_ledger if row.get("event") == "completed"]
    authority_rows = [
        row
        for row in invalid_ledger
        if row.get("event") in {"result_acceptance_revoked", "ownership_pending"}
    ]
    for index, candidate in enumerate(invalid_candidates):
        require(
            LEDGER_FIELDS <= set(candidate)
            and candidate.get("event") == "late_completion"
            and candidate.get("provenance") == "advisor",
            f"invalid late candidate lacks the common ledger contract: candidate {index}",
            failures,
        )
    matching_authority = {
        row.get("source_ref")
        for row in authority_rows
        if completed_rows and row_identity(row) == row_identity(completed_rows[0])
    }
    accepted_candidates = [
        candidate
        for candidate in invalid_candidates
        if candidate.get("authority_ref") in matching_authority
    ]
    require(
        len(completed_rows) == 1
        and not matching_authority
        and len(invalid_candidates) == 2
        and "authority_ref" not in invalid_candidates[0]
        and invalid_candidates[1].get("authority_ref")
        == "ledger:unrelated-result-acceptance-revoked"
        and row_identity(invalid_candidates[1]) != row_identity(authority_rows[0])
        and accepted_candidates == []
        and invalid.get("expected", {}).get("accepted_late_completions") == 0
        and set(invalid.get("expected", {}).get("rejection_reasons", []))
        == {"missing_authority_ref", "authority_identity_mismatch"},
        "missing or mismatched authority references were accepted as late completion",
        failures,
    )

    # AC-R35 through AC-R38: status observation and approval control
    # capability remain orthogonal, including the safe relay-unavailable return.
    approval_case_list = cases_doc.get("approval_capability_cases", [])
    approval_cases = {case.get("name"): case for case in approval_case_list}
    require(
        len(approval_cases) == len(approval_case_list)
        and set(approval_cases) == APPROVAL_CAPABILITY_CASES,
        "approval capability case set is incomplete or duplicated",
        failures,
    )
    for name, case in approval_cases.items():
        observation = case.get("status_observation", {})
        observation_result = observation.get("result")
        observed_state = observation.get("state")
        expected_state = case.get("expected_state")
        payload = case.get("worker_payload", {})
        mutations = case.get("mutations", {})
        derived_state = (
            "approval_required"
            if observation_result == "available" and observed_state == "approval_required"
            else "environment_state_unknown"
            if observation_result in {"unavailable", "error"}
            else None
        )
        structurally_valid = (
            derived_state is not None
            and expected_state == derived_state
            and payload.get("ended_at") is None
            and "termination" not in payload
            and payload.get("lifecycle_fallback_reason") is None
            and bool(case.get("ledger_path"))
            and case.get("attempt_before") == case.get("attempt_after")
            and case.get("retries_spawned_before")
            == case.get("retries_spawned_after")
            and case.get("approval_events_synthesized") == 0
            and mutations
            == {
                "interrupt_or_cancel": 0,
                "retry_or_fallback": 0,
                "authority_or_ownership": 0,
            }
        )
        if observed_state == "approval_required":
            structurally_valid = structurally_valid and (
                observation.get("provenance") == "environment"
                and bool(observation.get("source_ref"))
                and bool(case.get("report_invocation_id"))
                and bool(case.get("environment_invocation_id"))
            )
        require(
            structurally_valid is case.get("valid"),
            f"approval capability fixture validity mismatch: {name}",
            failures,
        )

    supported_approval = approval_cases.get("observed_approval_relay_supported", {})
    require(
        supported_approval.get("approval_relay_capability") == "supported"
        and supported_approval.get("approval_continuation_capability") == "supported"
        and supported_approval.get("environment_invocation_id")
        == supported_approval.get("continuation_environment_invocation_id"),
        "supported approval continuation changed environment identity",
        failures,
    )
    unavailable_approval = approval_cases.get(
        "observed_approval_relay_unavailable", {}
    )
    unavailable_payload = unavailable_approval.get("worker_payload", {})
    unavailable_concerns = " ".join(unavailable_payload.get("concerns", []))
    require(
        unavailable_approval.get("approval_relay_capability") == "unavailable"
        and unavailable_approval.get("approval_continuation_capability")
        == "unavailable"
        and unavailable_approval.get("phase_control_disposition") == "blocked"
        and set(unavailable_approval.get("phase_control_sink", []))
        == {"Summary", "Open Items", "concerns"}
        and "approval relay/control unavailable" in unavailable_concerns
        and "capability_ref=" in unavailable_concerns
        and "logical_task=" in unavailable_concerns
        and "approval_required; relay/control unavailable"
        in unavailable_payload.get("output_digest", ""),
        "relay-unavailable approval did not produce the safe phase-blocked return",
        failures,
    )
    unknown_cases = [
        case
        for case in approval_cases.values()
        if case.get("valid") and case.get("expected_state") == "environment_state_unknown"
    ]
    require(
        {case.get("status_observation", {}).get("result") for case in unknown_cases}
        == {"unavailable", "error"}
        and all(
            case.get("status_observation", {}).get("state") is None
            for case in unknown_cases
        ),
        "environment_state_unknown was not limited to status unavailable/error",
        failures,
    )
    invalid_approval = approval_cases.get(
        "observed_approval_downgraded_to_unknown_is_invalid", {}
    )
    require(
        invalid_approval.get("valid") is False
        and invalid_approval.get("rejection_reason")
        == "observed_approval_state_must_be_preserved",
        "observed approval downgrade is not an explicit invalid fixture",
        failures,
    )

    # AC-R39 through AC-R41: every axis/item owns exactly one Korean marker,
    # while each emitted aggregate is recomputed from its complete multiset.
    confidence_case_list = cases_doc.get("confidence_derivation_cases", [])
    confidence_cases = {case.get("name"): case for case in confidence_case_list}
    require(
        len(confidence_cases) == len(confidence_case_list)
        and set(confidence_cases) == CONFIDENCE_DERIVATION_CASES,
        "confidence derivation case set is incomplete or duplicated",
        failures,
    )
    valid_derived_aggregates: set[str] = set()
    for name, case in confidence_cases.items():
        errors: set[str] = set()
        axis_sets = case.get("axis_sets", [])
        axis_names: list[object] = []
        artifact_markers: list[str] = []
        if not isinstance(axis_sets, list) or not axis_sets:
            errors.add("marker_coverage_mismatch")
            axis_sets = []
        for axis in axis_sets:
            axis_name = axis.get("name")
            axis_names.append(axis_name)
            axis_marker = axis.get("marker")
            items = axis.get("items", [])
            item_names = [item.get("name") for item in items]
            if not isinstance(axis_name, str) or not axis_name:
                errors.add("marker_coverage_mismatch")
            if len(item_names) != len(set(item_names)):
                errors.add("duplicate_axis_item_identity")
            if axis_marker not in ITEM_CONFIDENCE_MARKERS:
                errors.add("item_marker_namespace_invalid")
            else:
                artifact_markers.append(axis_marker)
            set_markers: list[str] = []
            if axis_marker in ITEM_CONFIDENCE_MARKERS:
                set_markers.append(axis_marker)
            for item in items:
                item_name = item.get("name")
                marker = item.get("marker")
                if not isinstance(item_name, str) or not item_name or "marker" not in item:
                    errors.add("marker_coverage_mismatch")
                if not isinstance(marker, str):
                    errors.add("marker_must_be_exactly_one")
                elif marker not in ITEM_CONFIDENCE_MARKERS:
                    errors.add("item_marker_namespace_invalid")
                else:
                    set_markers.append(marker)
                    artifact_markers.append(marker)
            emitted_set_aggregate = axis.get("source_confidence")
            if emitted_set_aggregate not in AGGREGATE_CONFIDENCE:
                errors.add("aggregate_namespace_invalid")
            expected_set_aggregate = derived_confidence(set_markers)
            if (
                expected_set_aggregate is not None
                and emitted_set_aggregate in AGGREGATE_CONFIDENCE
                and emitted_set_aggregate != expected_set_aggregate
            ):
                errors.add("aggregate_derivation_mismatch")
        if len(axis_names) != len(set(axis_names)):
            errors.add("duplicate_axis_item_identity")
        emitted_artifact_aggregate = case.get("source_confidence")
        if emitted_artifact_aggregate not in AGGREGATE_CONFIDENCE:
            errors.add("aggregate_namespace_invalid")
        expected_artifact_aggregate = derived_confidence(artifact_markers)
        if (
            expected_artifact_aggregate is not None
            and emitted_artifact_aggregate in AGGREGATE_CONFIDENCE
            and emitted_artifact_aggregate != expected_artifact_aggregate
        ):
            errors.add("aggregate_derivation_mismatch")
        computed_valid = not errors
        require(
            computed_valid is case.get("valid"),
            f"confidence fixture validity mismatch: {name}; errors={sorted(errors)}",
            failures,
        )
        if computed_valid and expected_artifact_aggregate:
            valid_derived_aggregates.add(expected_artifact_aggregate)
        if not case.get("valid"):
            require(
                case.get("rejection_reason") in errors,
                f"confidence fixture rejection reason was not derived: {name}",
                failures,
            )
    require(
        valid_derived_aggregates == AGGREGATE_CONFIDENCE,
        "confidence fixtures do not cover the complete high/mixed/low truth table",
        failures,
    )

    # AC-R42 through AC-R45: abnormal reasons encode cause, source,
    # disposition, and rationale without waiting for retry exhaustion.
    reason_case_list = cases_doc.get("lifecycle_reason_cases", [])
    reason_cases = {case.get("name"): case for case in reason_case_list}
    require(
        len(reason_cases) == len(reason_case_list)
        and set(reason_cases) == LIFECYCLE_REASON_CASES,
        "lifecycle reason case set is incomplete or duplicated",
        failures,
    )
    valid_dispositions: set[str] = set()
    for name, case in reason_cases.items():
        termination = case.get("termination")
        reason = case.get("lifecycle_fallback_reason")
        parsed = parsed_lifecycle_reason(reason)
        if termination in ABNORMAL_TERMINATIONS:
            computed_valid = (
                parsed is not None
                and parsed[0] == termination
                and parsed[2] in RECOVERY_DISPOSITIONS
                and parsed[2] == case.get("expected_disposition")
            )
            if termination == "late_completion":
                computed_valid = computed_valid and (
                    parsed is not None
                    and parsed[2] == "late_completion_quarantined"
                    and bool(case.get("authority_ref"))
                    and case.get("authority_ref") in parsed[3]
                    and case.get("auto_merge") is False
                    and case.get("counts_as_success") is False
                )
            if computed_valid and parsed:
                valid_dispositions.add(parsed[2])
        elif termination == "completed":
            computed_valid = reason is None
        else:
            computed_valid = (
                "termination" not in case
                and case.get("observed_state")
                in {"running", "approval_required", "environment_state_unknown"}
                and case.get("ended_at") is None
                and reason is None
            )
        require(
            computed_valid is case.get("valid"),
            f"lifecycle reason fixture validity mismatch: {name}",
            failures,
        )
    require(
        valid_dispositions == RECOVERY_DISPOSITIONS,
        "lifecycle reason fixtures do not cover the exact five dispositions",
        failures,
    )
    require(
        reason_cases.get("failed_awaiting_user", {}).get("retry_exhausted") is False
        and reason_cases.get("interrupted_approved_retry", {}).get("retry_exhausted")
        is False,
        "intermediate abnormal reason incorrectly requires retry exhaustion",
        failures,
    )

    fallback = cases_doc["retry_exhausted"]
    require(
        set(fallback)
        == {
            "optional_advisory",
            "required_artifact",
            "implementation",
            "verification",
            "destructive_action",
            "closing_docs_retro",
        },
        "phase fallback matrix is incomplete",
        failures,
    )
    require(
        set(fallback["verification"]) == {"tier_b_execute", "blocked"},
        "verification must end in Tier B execution or blocked",
        failures,
    )


def validate_agent_source_specs(failures: list[str]) -> None:
    protocol_path = ROOT / "plugins/atp/docs/development/agent-team-protocol.md"
    platform_path = ROOT / "plugins/atp/docs/development/platform-adapters.md"
    catalog_path = ROOT / "plugins/atp/docs/development/agent-catalog.md"
    task_path = ROOT / "plugins/atp/skills/task/SKILL.md"
    research_path = ROOT / "plugins/atp/agents/research-advisor.md"
    implementation_path = ROOT / "plugins/atp/agents/implementation-advisor.md"

    research = research_path.read_text(encoding="utf-8")
    implementation = implementation_path.read_text(encoding="utf-8")
    catalog = catalog_path.read_text(encoding="utf-8")
    protocol_lifecycle = active_scope(protocol_path, "### 2.5", "### 2.6", failures)
    protocol_regression = active_scope(
        protocol_path,
        "\n### 2.6 결함 표면화 시 회귀 단계 판정",
        "\n### 2.7 분할 트랙의 설계 게이트 규율",
        failures,
    )
    protocol_research_confidence = active_scope(
        protocol_path, "### 4.8", "\n## 5.", failures
    )
    platform_lifecycle = active_scope(platform_path, "### 3.1", "\n## 4.", failures)
    task_lifecycle = active_scope(task_path, "#### 5.2", "\n### 6.", failures)
    research_lifecycle = active_scope(
        research_path, "## Worker lifecycle", "\n## 출력", failures
    )
    implementation_lifecycle = active_scope(
        implementation_path, "## Worker lifecycle", "\n## 출력", failures
    )
    research_output = active_scope(research_path, "## 출력", "\n## 금기", failures)
    research_confidence = active_scope(
        research_path, "### 출처 신뢰도 게이팅", "\nOrchestrator 에게", failures
    )
    ownership_template = active_scope(
        implementation_path, "## 파일 소유권 맵", "\n## Worker 호출", failures
    )
    implementation_output = active_scope(
        implementation_path, "## 출력", "\n## Worker 계획", failures
    )
    implementation_return = active_scope(
        implementation_path, "## 반환값", "\n## 자가 검증", failures
    )

    # AC-R1/R2: research can write only its phase-local artifacts, and its
    # downstream template always carries explicit concern review state.
    research_frontmatter = between(research, "---\n", "\n---")
    tools_match = re.search(r"^tools:\s*(.+)$", research_frontmatter, re.MULTILINE)
    research_tools = set(tools_match.group(1).split(", ")) if tools_match else set()
    catalog_match = re.search(
        r"^\| `research-advisor` \| `parallel-explorer` \| ([^|]+) \|$",
        catalog,
        re.MULTILINE,
    )
    catalog_tools = (
        {tool.strip() for tool in catalog_match.group(1).split(",")}
        if catalog_match
        else set()
    )
    require(
        research_tools == REQUIRED_RESEARCH_TOOLS,
        "research-advisor source tool set differs from the required v4 tool set",
        failures,
    )
    require(
        catalog_tools == research_tools,
        "research-advisor catalog tool set differs from its source frontmatter",
        failures,
    )
    lsp_rules = [
        line for line in research.splitlines() if line.startswith("- `LSP`")
    ]
    require(
        len(lsp_rules) == 1,
        "research-advisor LSP tool-use rule is missing or duplicated",
        failures,
    )
    require_terms(
        lsp_rules[0] if lsp_rules else "",
        {"symbol", "definition/reference", "navigation", "코드 수정·실행에는 사용하지 않는다"},
        "research-advisor LSP navigation scope",
        failures,
    )
    require_terms(
        research,
        {
            "${CLAUDE_PROJECT_DIR}/.atp/work-session/<sid>/research/**",
            "프로젝트 제품 파일에는 쓰지 않는다",
            "research/**` 밖의 파일 Write/Edit",
        },
        "research-advisor scoped write contract",
        failures,
    )
    require_terms(
        research_output,
        {"concerns: []", "concerns_checked: true"},
        "research output frontmatter template",
        failures,
    )

    # The item marker and aggregate/axis confidence enums are different
    # namespaces with one explicit strict-majority mapping in both sources.
    for label, body in (
        ("protocol §4.8 confidence schema", protocol_research_confidence),
        ("research-advisor confidence schema", research_confidence),
    ):
        anchor = confidence_mapping_anchor(body)
        require(
            bool(anchor),
            f"{label} lacks a coherent item/aggregate namespace with "
            "all-confirmed high, strict-majority-unverified low, and otherwise mixed",
            failures,
        )
        require_terms(
            normalized_semantic_text(anchor),
            {"item-level marker enum", "aggregate", "source_confidence"},
            label,
            failures,
        )
    confidence_procedure = between(
        protocol_research_confidence, "**절차**:", "**맹점과"
    )
    confidence_item_two = next(
        (
            line
            for line in confidence_procedure.splitlines()
            if re.match(r"^2\.\s+", line) and "축 집합" in line
        ),
        "",
    )
    require(
        bool(confidence_mapping_anchor(confidence_item_two)),
        "protocol §4.8 confidence procedure item 2 lacks the complete "
        "item/aggregate namespace and strict-majority truth table",
        failures,
    )
    require_terms(
        normalized_semantic_text(confidence_item_two),
        {
            "axis/item",
            "item-level marker enum",
            "aggregate source_confidence",
            "marker coverage",
            "aggregate derivation",
        },
        "protocol §4.8 confidence procedure item 2",
        failures,
    )
    require(
        "`source_confidence` 3-tier(`확인됨`/`추정`/`미확인`)"
        not in confidence_procedure,
        "protocol §4.8 procedure conflates item markers with source_confidence",
        failures,
    )

    # Report schema stays optional, but every abnormal producer termination
    # carries cause + one of the five dispositions + rationale immediately.
    fallback_contract = semantic_paragraph(
        research_lifecycle,
        (
            ("lifecycle_fallback_reason",),
            ("cause=<failed|interrupted|late_completion>",),
            ("disposition=<",),
            ("rationale=<",),
            ("non-null",),
        ),
    )
    require(
        bool(fallback_contract),
        "research abnormal lifecycle fallback reason lacks one canonical "
        "cause/disposition/rationale producer anchor",
        failures,
    )
    require_terms(
        fallback_contract,
        {"failed", "interrupted", "late_completion", *RECOVERY_DISPOSITIONS},
        "research abnormal lifecycle fallback reason",
        failures,
    )
    require_ordered(
        normalized_semantic_text(fallback_contract),
        ["cause=<", "@<concrete source_ref>", "disposition=<", "rationale=<"],
        "research abnormal lifecycle fallback reason",
        failures,
    )
    require(
        has_immediate_intermediate_reason(fallback_contract),
        "research abnormal lifecycle fallback reason is not serialized for an "
        "intermediate invocation before retry exhaustion",
        failures,
    )
    normalized_fallback = normalized_semantic_text(fallback_contract)
    require(
        re.search(
            r"completed[^.]*lifecycle_fallback_reason[^.]*null[^.]*생략",
            normalized_fallback,
        )
        is not None
        and re.search(
            r"non-terminal[^.]*ended_at: null[^.]*lifecycle_fallback_reason"
            r"[^.]*null[^.]*생략[^.]*termination[^.]*key[^.]*생략",
            normalized_fallback,
        )
        is not None,
        "research lifecycle fallback reason nullability contract is incomplete",
        failures,
    )

    # AC-R3: nested approval is relayed to the sole user-facing authority and
    # same-invocation continuation neither increments attempt nor mutates retry.
    for label, body in (
        ("research-advisor nested approval", research_lifecycle),
        ("implementation-advisor nested approval", implementation_lifecycle),
    ):
        approval_lines = [
            line
            for line in body.splitlines()
            if "nested worker" in line and "approval_required" in line
        ]
        require(len(approval_lines) == 1, f"{label} contract is not singular", failures)
        approval_line = approval_lines[0] if approval_lines else ""
        require_terms(
            approval_line,
            {"ledger", "orchestrator", "사용자", "attempt", "retry/fallback"},
            label,
            failures,
        )
        require(
            has_same_environment_continuation_accounting(approval_line),
            f"{label} lacks same-environment invocation/identity continuation accounting",
            failures,
        )
        require_ordered(
            approval_line,
            ["approval_required", "ledger", "orchestrator", "사용자"],
            label,
            failures,
        )
        require(
            "environment_state_unknown" in body
            and "relay" in body
            and "mutation" in body,
            f"{label} lacks mutation-free unknown-state relay fallback",
            failures,
        )
    # AC-R4/R5: the two source specs must agree on the top-level orchestrator
    # setter/root ledger and each nested spawner's phase-local ledger.
    root_ledger_path = ".atp/work-session/<sid>/artifacts/lifecycle-events.jsonl"
    for label, body in (
        ("research-advisor common recording", research_lifecycle),
        ("implementation-advisor common recording", implementation_lifecycle),
    ):
        require_terms(
            body,
            {
                "orchestrator",
                "top-level advisor logical task",
                "dispatch하기 전에",
                "clean_retry_limit",
                root_ledger_path,
                "유일한 writer",
            },
            label,
            failures,
        )
    ledger_contracts = (
        (
            "research lifecycle ledger",
            research_lifecycle,
            ".atp/work-session/<sid>/research/lifecycle-events.jsonl",
        ),
        (
            "implementation lifecycle ledger",
            implementation_lifecycle,
            ".atp/work-session/<sid>/implementation/lifecycle-events.jsonl",
        ),
    )
    for label, body, path in ledger_contracts:
        require(path in body, f"{label} path is missing", failures)
        require(
            re.search(r"(?:유일한|단일|독점).*writer|writer.*(?:유일한|단일|독점)", body)
            is not None,
            f"{label} lacks a single-writer contract",
            failures,
        )
        require_terms(body, LEDGER_FIELDS, f"{label} row contract", failures)
        require(
            "최초 dispatch" in body
            and "clean_retry_limit_source" in body
            and "immutable" in body,
            f"{label} does not set an immutable retry limit and source before dispatch",
            failures,
        )
        require(
            "새 environment identity" in body.replace("`", "")
            and "발급된 뒤에만" in body
            and "retries_spawned" in body,
            f"{label} does not increment retry accounting only after identity issuance",
            failures,
        )
    for label, body in (
        ("research-advisor", research_lifecycle),
        ("implementation-advisor", implementation_lifecycle),
    ):
        explicit_nested_setter = re.search(
            rf"{re.escape(label)}는[^\n]*nested(?: worker)? logical task[^\n]*setter",
            body,
        )
        require(
            explicit_nested_setter is not None
            and "최초 dispatch" in body
            and "clean_retry_limit" in body,
            f"{label} is not the explicit nested clean_retry_limit setter",
            failures,
        )

    # AC-R6: the append-only ledger preserves interruption before a quarantined
    # late completion, while report termination remains one final scalar value.
    for label, body in (
        ("research-advisor", research_lifecycle),
        ("implementation-advisor", implementation_lifecycle),
    ):
        require_ordered(
            body,
            ["`interrupted`", "`late_completion`"],
            f"{label} interrupted-to-late-completion ledger",
            failures,
        )
        require(
            "termination" in body
            and "late_completion" in body
            and (
                "최종 disposition" in body
                or "`late_completion`으로 기록" in body
            ),
            f"{label} does not retain late_completion as final scalar termination",
            failures,
        )

    # AC-R7/R8: write ownership passes through an ownerless pending state, and
    # late-write pausing is restricted to the dependent closure.
    handoff = between(
        implementation_lifecycle,
        "clean retry와 ownership mutation 순서는 다음으로 고정한다.",
        "### Late completion 처리",
    )
    require_ordered(
        handoff,
        [
            "retry_approved",
            "completion race",
            "termination",
            "retries_spawned < clean_retry_limit",
            "pending_handoff",
            "새 identity로 spawn",
            "environment_invocation_id",
            "active",
        ],
        "implementation two-stage ownership handoff",
        failures,
    )
    require_terms(
        implementation_lifecycle,
        {
            "state: paused",
            "dependencies",
            "transitive closure",
            "독립 scope는 `active`",
        },
        "implementation dependency-scoped late-write pause",
        failures,
    )

    # AC-R9: both implementation templates expose concern review, and the
    # advisor returns exactly the two canonical artifact objects.
    for label, body in (
        ("implementation ownership template", ownership_template),
        ("implementation report template", implementation_output),
    ):
        require_terms(body, {"concerns: []", "concerns_checked: true"}, label, failures)
    require(
        "정확히 두 객체" in implementation_return
        and implementation_return.count("path:") == 2
        and "implementation/report.md" in implementation_return
        and "implementation/ownership.md" in implementation_return,
        "implementation return does not contain exactly two per-file artifact objects",
        failures,
    )
    require(
        "세 번째 artifact 객체로 추가하지 않고" in implementation_return,
        "implementation lifecycle ledger leaked into returned artifact objects",
        failures,
    )

    # AC-R10: a migration owns a reservable namespace before generation, then
    # expands to all generated paths; an unreservable namespace is serialized.
    require_ordered(
        ownership_template,
        ["scope_kind", "migration_namespace", "reservation:", "generated_paths"],
        "migration namespace reservation",
        failures,
    )
    require_terms(
        ownership_template,
        {
            "같은 `namespace_key`는 반드시 직렬화",
            "generated_paths",
            "downstream worker의 scope/dependency에 반영한 뒤에만",
            "병렬 spawn은 0건",
            "하나씩 직렬 실행",
        },
        "migration reservation and serial fallback",
        failures,
    )

    # AC-R11: derive the documented report optional block, rather than merely
    # trusting this validator's constant, and keep phase-ledger fields local.
    report_schema = active_scope(protocol_path, "## 8. 보고서 스키마", "\n## 9.", failures)
    optional_block = between(
        report_schema,
        "# ── lifecycle 전용 optional 필드",
        "# ── tier-3 advisor 전용",
    )
    documented_optional_fields = set(
        re.findall(r"^\s{2}([a-z_]+):", optional_block, re.MULTILINE)
    )
    require(
        documented_optional_fields == EXPECTED_OPTIONAL_FIELDS,
        "protocol report schema does not document exactly four lifecycle optional fields",
        failures,
    )
    require(
        documented_optional_fields.isdisjoint(LEDGER_FIELDS - {"attempt"}),
        "protocol report optional fields include a phase-local ledger key",
        failures,
    )

    # AC-R12: active specs and fixture keys may discuss observations only to
    # deny authority; they must not introduce absence counters or transitions.
    absence_counter = re.compile(
        r"(?:wait[_ -]?timeout|no[_ -]?progress|heartbeat(?:[_ -]?(?:absence|miss))?"
        r"|타임아웃|진행\s*부재|하트비트\s*부재)\s*[_ -]?"
        r"(?:count(?:er)?|budget|limit|횟수|카운터|예산)",
        re.IGNORECASE,
    )
    source_scopes = {
        "protocol §2.5": protocol_lifecycle,
        "platform §3.1": platform_lifecycle,
        "task §5.2": task_lifecycle,
        "research-advisor lifecycle": research_lifecycle,
        "implementation-advisor lifecycle": implementation_lifecycle,
    }
    for label, body in source_scopes.items():
        require(
            absence_counter.search(body) is None,
            f"absence-based lifecycle counter remains in {label}",
            failures,
        )
        require(
            any(
                phrase in body
                for phrase in (
                    "상태를 전이시키지 않는다",
                    "상태 전이·retry·fallback 권한이 아니다",
                    "상태 전이·failure·retry/fallback 권한을 만들지 않는다",
                    "failure나 retry/fallback 근거가 아니다",
                )
            ),
            f"{label} does not explicitly deny observation-driven transitions",
            failures,
        )
    cases_doc = load("lifecycle-cases.json")
    fixture_keys = collect_keys(cases_doc)
    forbidden_fixture_keys = sorted(
        key for key in fixture_keys if absence_counter.fullmatch(key.replace("_", " "))
    )
    require(
        not forbidden_fixture_keys,
        f"fixture contains absence-counter keys: {forbidden_fixture_keys}",
        failures,
    )
    for case in cases_doc["cases"]:
        if set(case.get("observations", [])) & {"wait_timeout", "no_progress"}:
            require(
                case.get("retry_or_fallback") is False
                and case.get("actions_before_approval") == [],
                f"absence observation caused transition or mutation: {case['name']}",
                failures,
            )

    # AC-R13: each phase documents the complete ledger row, its event
    # vocabulary, and the closed provenance domain structurally.
    ledger_examples = {
        "research-advisor": (
            ledger_example(research_lifecycle),
            RESEARCH_LEDGER_EVENTS,
        ),
        "implementation-advisor": (
            ledger_example(implementation_lifecycle),
            IMPLEMENTATION_LEDGER_EVENTS,
        ),
    }
    for label, (example, expected_events) in ledger_examples.items():
        require(bool(example), f"{label} has no parseable ledger JSON example", failures)
        require(
            set(example) == LEDGER_FIELDS,
            f"{label} ledger example does not have exactly the eleven common fields",
            failures,
        )
        events = set(str(example.get("event", "")).split("|"))
        provenance = set(str(example.get("provenance", "")).split("|"))
        require(events == expected_events, f"{label} ledger event vocabulary drift", failures)
        require(
            provenance == LEDGER_PROVENANCE,
            f"{label} ledger provenance is not environment|user|advisor",
            failures,
        )
        require(
            not re.search(r"provenance\s*:\s*`?orchestrator", research_lifecycle + implementation_lifecycle),
            "source spec introduces orchestrator as a fourth provenance value",
            failures,
        )
        require_cooccurring_terms(
            research_lifecycle if label == "research-advisor" else implementation_lifecycle,
            {*ENVIRONMENT_LEDGER_EVENTS, "provenance: environment", "source_ref", "합성하지 않는다"},
            f"{label} environment provenance mapping",
            failures,
        )

    # AC-R14: retry accounting is immutable, derived-only, monotonic, and
    # checked before a spawn; counters advance only after identity issuance.
    for label, body in (
        ("research-advisor", research_lifecycle),
        ("implementation-advisor", implementation_lifecycle),
    ):
        require_cooccurring_terms(
            body,
            {
                "최초 dispatch",
                "clean_retry_limit",
                "clean_retry_limit_source",
                "immutable",
                "retries_spawned",
                "단조 증가",
                "clean_retries_remaining",
                "저장하지 않고",
                "clean_retry_limit - retries_spawned",
            },
            f"{label} immutable retry accounting",
            failures,
        )
        normalized_body = body.replace("`", "")
        require_ordered(
            normalized_body,
            [
                "각 clean retry spawn 직전",
                "retries_spawned < clean_retry_limit",
                "새 environment_invocation_id가 발급된 뒤에만",
                "retries_spawned와 attempt를 증가",
            ],
            f"{label} pre-spawn cap and post-identity accounting",
            failures,
        )
        require(
            not re.search(r"(?:저장|persist)[^\n]{0,40}clean_retries_remaining", body),
            f"{label} stores the derived retry remainder",
            failures,
        )

    # AC-R15/AC-R16: user retry decisions are distinct from environment
    # approval and write recovery cannot mutate ownership before approval.
    for label, body in (
        ("research-advisor", research_lifecycle),
        ("implementation-advisor", implementation_lifecycle),
    ):
        require_cooccurring_terms(
            body,
            {
                "retry_approved",
                "retry_denied",
                "provenance: user",
                "scope",
                "rationale",
                "source_ref",
                "approval_required",
                "합성하지 않는다",
            },
            f"{label} explicit retry decision event",
            failures,
        )
    implementation_recovery = between(
        implementation_lifecycle,
        "clean retry와 ownership mutation 순서는 다음으로 고정한다.",
        "### Late completion 처리",
    )
    require_ordered(
        implementation_recovery,
        [
            "failed`/`interrupted",
            "사용자 retry 승인 전",
            "retry_approved",
            "completion race",
            "termination",
            "retries_spawned < clean_retry_limit",
            "pending_handoff",
            "새 identity로 spawn",
            "environment_invocation_id",
            "active",
        ],
        "implementation approval-before-mutation recovery",
        failures,
    )
    require_cooccurring_terms(
        implementation_lifecycle,
        {"사용자 retry 승인 전", "ownership row", "mutation", "0건"},
        "implementation preapproval ownership immutability",
        failures,
    )
    require_cooccurring_terms(
        implementation_lifecycle,
        {"retry_denied", "ownership mutation", "spawn", "0건"},
        "implementation denied-retry immutability",
        failures,
    )

    # AC-R17: advisor returns contain one complete report-v2 invocation object
    # per real worker, including routing, usage, lifecycle, and identity joins.
    for label, body in (
        ("research-advisor", research_lifecycle),
        ("implementation-advisor", implementation_lifecycle),
    ):
        worker_example = source_example(body, "worker_invocations")
        require(bool(worker_example), f"{label} has no worker_invocations YAML example", failures)
        require(
            yaml_record_keys(worker_example) == WORKER_INVOCATION_FIELDS,
            f"{label} worker invocation example field set drift",
            failures,
        )
        model_choice = yaml_child_block(worker_example, "model_choice", 4)
        token_usage = yaml_child_block(worker_example, "token_usage", 4)
        require(
            yaml_keys_at_indent(model_choice, 6) == MODEL_CHOICE_FIELDS,
            f"{label} model_choice does not have the ten required fields",
            failures,
        )
        require(
            yaml_keys_at_indent(token_usage, 6) == TOKEN_USAGE_FIELDS,
            f"{label} token_usage does not have input and output",
            failures,
        )
        require_terms(
            body,
            {
                "실제 spawn된",
                "worker_invocations",
                "aggregate worker",
                "report_invocation_id",
                "environment_invocation_id",
                "orchestrator",
                "report에 append",
                "중복하지 않고",
            },
            f"{label} per-worker return and report join",
            failures,
        )
        require_cooccurring_terms(
            body,
            {"attempt", "retry_of", "lifecycle_fallback_reason", "항상 반환"},
            f"{label} lifecycle producer fields",
            failures,
        )
        termination_contract = semantic_paragraph(
            body,
            (
                ("termination",),
                ("authoritative terminal", "environment terminal"),
                ("non-terminal", "nonterminal"),
                ("ended_at: null",),
                ("key를 생략", "omits the termination key"),
            ),
        )
        require(
            bool(termination_contract),
            f"{label} conditional termination producer rule does not tie the "
            "termination key to an authoritative terminal/disposition and omit it "
            "for an ended_at-null nonterminal payload",
            failures,
        )

    # AC-R18 is enforced both by validate_reports and AC-R11; repeat the
    # cross-schema disjointness here so worker/ownership expansion cannot leak.
    non_report_fields = (
        (LEDGER_FIELDS - {"attempt"})
        | OWNERSHIP_RECORD_FIELDS
        | RESERVATION_FIELDS
        | PAUSE_FIELDS
        | AUTHORITY_LEDGER_FIELDS
        | (WORKER_INVOCATION_FIELDS - OPTIONAL_FIELDS)
        | {"worker_invocations", "environment_invocation_id"}
    )
    require(
        OPTIONAL_FIELDS == EXPECTED_OPTIONAL_FIELDS
        and OPTIONAL_FIELDS.isdisjoint(non_report_fields),
        "report v2 lifecycle optional fields expanded beyond the exact four",
        failures,
    )

    # AC-R19/AC-R20: parse the ownership template as a fixed, fully explicit
    # record and verify its persisted state and identity transitions.
    ownership_example = source_example(ownership_template, "ownership_records")
    require(bool(ownership_example), "ownership template has no parseable YAML example", failures)
    require(
        'lifecycle_ledger: "./lifecycle-events.jsonl"' in ownership_example,
        "ownership frontmatter does not link the phase lifecycle ledger",
        failures,
    )
    ownership_keys = yaml_record_keys(ownership_example)
    require(
        ownership_keys == OWNERSHIP_RECORD_FIELDS,
        "ownership record does not have exactly the fixed top-level keys",
        failures,
    )
    reservation = yaml_child_block(ownership_example, "reservation", 4)
    pause = yaml_child_block(ownership_example, "pause", 4)
    require(
        yaml_keys_at_indent(reservation, 6) == RESERVATION_FIELDS,
        "ownership reservation does not have the fixed key set",
        failures,
    )
    require(
        yaml_keys_at_indent(pause, 6) == PAUSE_FIELDS,
        "ownership pause does not have the fixed key set",
        failures,
    )
    state_match = re.search(r"^ {4}state:\s*(.+)$", ownership_example, re.MULTILINE)
    documented_states = (
        {part.strip() for part in state_match.group(1).split("|")} if state_match else set()
    )
    require(
        documented_states == OWNERSHIP_STATES,
        "ownership state vocabulary drift",
        failures,
    )
    require(
        {"owner", "revoked_from", "handoff_to", "worker"}.isdisjoint(ownership_keys),
        "ownership template contains an identity-domain-free key",
        failures,
    )
    require_terms(
        ownership_template,
        {
            "report_invocation_id",
            "environment_invocation_id",
            "report domain",
            "host domain",
            "domain 없는",
            "두 identity 중 하나만 채운 active row는 invalid",
            "적용되지 않는 scalar/object는 `null`, list는 `[]`",
        },
        "ownership identity and nullable-key contract",
        failures,
    )
    ownership_transitions = between(
        ownership_template, "identity와 state는 다음처럼 해석한다.", "**불변식**"
    )
    require_ordered(
        ownership_transitions,
        ["state: reserved", "environment identity가 발급된 뒤", "active`로 persist"],
        "ownership initial reserved-to-active transition",
        failures,
    )
    require_ordered(
        implementation_recovery,
        ["pending_handoff", "새 identity로 spawn", "row를 `active`로 persist"],
        "ownership approved handoff transition",
        failures,
    )
    require_cooccurring_terms(
        ownership_template,
        {"paused", "persisted", "ownership_resumed", "state: active", "null"},
        "ownership persisted pause and resume transition",
        failures,
    )

    # AC-R21: harmless late results and late disk writes have disjoint effects;
    # only the dependency closure is persistently paused and explicitly resumed.
    require_cooccurring_terms(
        implementation_lifecycle,
        {"harmless late completion", "disk write가 0건", "quarantine-only", "mutate하지 않는다"},
        "harmless late completion branch",
        failures,
    )
    require_cooccurring_terms(
        implementation_lifecycle,
        {
            "late disk write",
            "dependencies",
            "transitive closure",
            "state: paused",
            "persist",
            "독립 scope",
            "active",
        },
        "late disk write dependency-closure pause",
        failures,
    )
    pause_resume_lines = [
        line
        for line in implementation_lifecycle.splitlines()
        if "state: paused" in line and "ownership_resumed" in line
    ]
    require(
        len(pause_resume_lines) == 1,
        "persisted pause mediation and resume contract is not singular",
        failures,
    )
    pause_resume_line = pause_resume_lines[0] if pause_resume_lines else ""
    require_terms(
        pause_resume_line,
        {"persisted", "orchestrator", "중재", "state: active", "ledger", "기록"},
        "persisted pause mediation and resume",
        failures,
    )
    require_ordered(
        pause_resume_line,
        ["state: paused", "persisted", "orchestrator", "중재", "state: active", "persisted", "ownership_resumed", "ledger", "기록"],
        "persisted pause mediation and resume",
        failures,
    )
    late_completion_section = between(
        implementation_lifecycle,
        "### Late completion 처리",
        "### Worker invocation 반환 계약",
    )
    late_completion_scalar = semantic_paragraph(
        late_completion_section,
        (
            ("late_completion",),
            ("최종 scalar", "final scalar"),
            ("최종 disposition", "final disposition"),
            ("자동 merge", "automatically merge"),
            ("성공 판정하지 않", "does not count as success"),
        ),
    )
    require(
        bool(late_completion_scalar),
        "late completion scalar disposition does not preserve the final scalar "
        "while forbidding automatic merge and success",
        failures,
    )
    require_ordered(
        normalized_semantic_text(late_completion_scalar),
        ["같은 old report/environment identity", "최종 scalar termination", "late_completion"],
        "late completion final scalar identity binding",
        failures,
    )

    # AC-R22: migration reservation determines safe concurrency and generated
    # paths become owned dependencies before downstream dispatch.
    require_terms(
        ownership_template,
        {
            "서로 다른 non-null `namespace_key`",
            "disjoint migration으로 병렬 실행",
            "같은 `namespace_key`는 반드시 직렬화",
            "unknown/null",
            "병렬 spawn은 0건",
            "generated_paths",
            "downstream worker의 scope/dependency에 반영한 뒤에만",
            "shared_generated_artifact",
        },
        "migration namespace concurrency and generated ownership",
        failures,
    )
    migration_contract = between(
        ownership_template, "**불변식**", "\ndisjoint namespace_key는"
    )
    require_ordered(
        migration_contract,
        ["namespace_key", "reserved`로 persist", "generated_paths", "downstream"],
        "migration reservation before generation and dispatch",
        failures,
    )

    # AC-R23: research uses the common producer/decision/payload contract but
    # read-only late results never create implementation ownership state.
    require_terms(
        research_lifecycle,
        {
            "accepted",
            "queued",
            "provenance: environment",
            "clean_retry_limit_source",
            "retry_approved",
            "retry_denied",
            "worker_invocations",
            "quarantine-only",
            "implementation ownership이나 pause artifact를 만들지 않는다",
        },
        "research lifecycle parity",
        failures,
    )

    # AC-R24: absence observations remain fixtures, but no active producer
    # schema may persist a time/progress/heartbeat absence counter.
    forbidden_counter_key = re.compile(
        r"(?:wait|timeout|elapsed|silence|unchanged|snapshot|progress|output|tool|heartbeat)"
        r".*(?:count|counter|budget|limit)$",
        re.IGNORECASE,
    )
    schema_keys = (
        LEDGER_FIELDS
        | WORKER_INVOCATION_FIELDS
        | MODEL_CHOICE_FIELDS
        | TOKEN_USAGE_FIELDS
        | OWNERSHIP_RECORD_FIELDS
        | RESERVATION_FIELDS
        | PAUSE_FIELDS
        | AUTHORITY_LEDGER_FIELDS
    )
    require(
        not sorted(key for key in schema_keys if forbidden_counter_key.fullmatch(key)),
        "active source schema contains an absence-derived lifecycle counter",
        failures,
    )
    forbidden_fixture_counters = sorted(
        key for key in fixture_keys if forbidden_counter_key.fullmatch(key)
    )
    require(
        not forbidden_fixture_counters,
        f"fixture contains forbidden absence counters: {forbidden_fixture_counters}",
        failures,
    )
    forbidden_source_identifier = re.compile(
        r"\b(?:wait|timeout|elapsed|silence|unchanged|snapshot|progress|output|tool|heartbeat)"
        r"[_-](?:count|counter|budget|limit)s?\b",
        re.IGNORECASE,
    )
    for label, body in (
        ("research-advisor", research_lifecycle),
        ("implementation-advisor", implementation_lifecycle),
    ):
        require(
            forbidden_source_identifier.search(body) is None,
            f"{label} introduces an absence-derived producer counter",
            failures,
        )

    # AC-R25: canonical expectations are checked as semantic co-occurrence and
    # ordering, while the examples above provide structural schema coherence.
    common_semantic_anchors = (
        {
            "clean_retry_limit",
            "clean_retry_limit_source",
            "logical task",
            "immutable",
            "clean_retries_remaining",
            "저장하지 않고",
            "clean_retry_limit - retries_spawned",
        },
        {
            "clean retry spawn 직전",
            "retries_spawned < clean_retry_limit",
            "environment_invocation_id",
            "발급된 뒤에만",
            "attempt",
        },
        {
            "retry_approved",
            "retry_denied",
            "provenance: user",
            "scope",
            "rationale",
            "source_ref",
        },
        {
            *ENVIRONMENT_LEDGER_EVENTS,
            "environment provenance",
            "관측 부재",
            "합성하지 않는다",
        },
        {"worker_invocations", "실제 spawn된 worker별", "§8 Invocations payload", "대체하지 않는다"},
    )
    for label, body in (
        ("research-advisor", research_lifecycle),
        ("implementation-advisor", implementation_lifecycle),
    ):
        for index, terms in enumerate(common_semantic_anchors, start=1):
            require_cooccurring_terms(
                body,
                terms,
                f"{label} canonical semantic anchor {index}",
                failures,
            )
    implementation_anchors = (
        {"사용자 retry 승인 전", "ownership row", "mutation", "0건"},
        {
            "report_invocation_id",
            "environment_invocation_id",
            "domain을 분리",
            "pending_handoff",
            "handoff_to 두 ID가 모두 null",
            "active",
            "두 ID가 모두 확정",
        },
        {
            "disk write 없는 late_completion",
            "quarantine-only",
            "ownership을 mutate하지 않으며",
            "late disk write",
            "dependency transitive closure",
            "persisted paused",
        },
        {"disjoint namespace_key", "병렬 가능", "같은 namespace_key", "직렬 실행"},
        {"implementation/ownership.md", "lifecycle_ledger", "./lifecycle-events.jsonl"},
    )
    for index, terms in enumerate(implementation_anchors, start=6):
        require_cooccurring_terms(
            ownership_template + "\n\n" + implementation_lifecycle,
            terms,
            f"implementation canonical semantic anchor {index}",
            failures,
        )

    # AC-R26: the report routing phase and research artifact phase are
    # intentionally different namespaces. Derive the closed routing enum from
    # protocol §5.8 and parse both source examples independently.
    protocol_routing = active_scope(protocol_path, "### 5.8", "\n## 6.", failures)
    phase_enum_match = re.search(r"^\s*phase:\s*<([^>]+)>", protocol_routing, re.MULTILINE)
    parsed_routing_phases = (
        {part.strip() for part in phase_enum_match.group(1).split("|")}
        if phase_enum_match
        else set()
    )
    research_worker_example = source_example(research_lifecycle, "worker_invocations")
    research_model_choice = yaml_child_block(
        research_worker_example, "model_choice", 4
    )
    worker_phase_match = re.search(
        r"^ {6}phase:\s*([^\s#]+)", research_model_choice, re.MULTILINE
    )
    worker_phase = worker_phase_match.group(1) if worker_phase_match else None
    artifact_examples = [
        block
        for block in fenced_blocks(research_output, "yaml")
        if block.startswith("---\n")
    ]
    artifact_phase_match = (
        re.search(r"^phase:\s*([^\s#]+)", artifact_examples[0], re.MULTILINE)
        if artifact_examples
        else None
    )
    artifact_phase = artifact_phase_match.group(1) if artifact_phase_match else None
    require(
        parsed_routing_phases == MODEL_ROUTING_PHASES
        and worker_phase == "analyze"
        and worker_phase in parsed_routing_phases
        and artifact_phase == "research"
        and artifact_phase not in parsed_routing_phases
        and worker_phase != artifact_phase,
        "research routing phase and artifact phase namespaces were conflated",
        failures,
    )

    # AC-R27: every execution layer distinguishes result acceptance from write
    # ownership, and read-only ATP-local isolation cannot stand in for write
    # termination/isolation and partial-write classification.
    for label, body in (
        ("protocol §2.5 authority taxonomy", protocol_lifecycle),
        ("platform §3.1 authority taxonomy", platform_lifecycle),
        ("task §5.2 authority taxonomy", task_lifecycle),
        ("research authority taxonomy", research_lifecycle),
    ):
        normalized_authority_body = body.replace("_", " ").replace("`", "")
        require_terms(
            normalized_authority_body,
            {"read-only", "write-capable", "result acceptance", "write ownership"},
            label,
            failures,
        )
    for label, body in (
        ("protocol read isolation boundary", protocol_lifecycle),
        ("platform read isolation boundary", platform_lifecycle),
        ("research read isolation boundary", research_lifecycle),
    ):
        normalized_authority_body = body.replace("_", " ").replace("`", "")
        paragraphs = re.split(r"\n\s*\n", normalized_authority_body)
        require(
            any(
                "result acceptance" in paragraph
                and "write isolation" in paragraph
                and (
                    "대체하지 않는다" in paragraph
                    or "대신하지 않는다" in paragraph
                )
                for paragraph in paragraphs
            ),
            f"{label} does not keep read-only isolation separate from write isolation",
            failures,
        )

    # AC-R28/AC-R29: source producers and parsed fixtures use the same
    # approval -> completion-race -> authority-isolation -> new-identity order.
    require_ordered(
        research_lifecycle,
        ["retry_approved", "completion race", "result_acceptance_revoked", "새 identity로 spawn"],
        "research approved authority isolation",
        failures,
    )
    require_ordered(
        task_lifecycle,
        ["retry를 승인", "completion race", "result_acceptance_revoked", "새 invocation identity"],
        "task approved authority isolation",
        failures,
    )
    require_ordered(
        protocol_lifecycle,
        ["retry를 승인", "completion race", "result_acceptance_revoked", "새 identity를 spawn"],
        "protocol approved authority isolation",
        failures,
    )
    require_terms(
        research_lifecycle,
        {
            "result_acceptance_revoked",
            "11개 공통 필드",
            "report_invocation_id",
            "environment_invocation_id",
            "scope",
            "rationale",
            "source_ref",
            "provenance: advisor",
        },
        "research result acceptance revocation producer",
        failures,
    )

    # AC-R30/AC-R31: source semantics match the fixture's same-identity
    # authority_ref join and its three mutually exclusive effect branches.
    for label, body in (
        ("protocol late-completion precondition", protocol_lifecycle),
        ("research late-completion precondition", research_lifecycle),
    ):
        require_terms(
            body,
            {"late_completion", "old", "authority_ref", "completed"},
            label,
            failures,
        )
    require_cooccurring_terms(
        research_lifecycle,
        {
            "result_acceptance",
            "quarantine-only",
            "자동 취합",
            "성공 판정",
            "ownership",
            "pause",
        },
        "read-only late result isolation",
        failures,
    )
    require_terms(
        implementation_lifecycle,
        {
            "ownership",
            "late_completion",
            "late disk write",
            "quarantine-only",
            "dependency",
            "persisted paused",
        },
        "write late result branch isolation",
        failures,
    )

    # AC-R32: runtime contract, accepted ADR clarification, and Korean/English
    # FAQ all retain the two authority kinds and the late-write-only pause rule.
    adr_path = ROOT / "docs/adr/ADR-0020-environment-authoritative-subagent-lifecycle.md"
    faq_ko_path = ROOT / "docs/usage/faq.md"
    faq_en_path = ROOT / "docs/usage/faq.en.md"
    adr = adr_path.read_text(encoding="utf-8")
    faq_ko = faq_ko_path.read_text(encoding="utf-8")
    faq_en = faq_en_path.read_text(encoding="utf-8")
    for label, body in (
        ("protocol authority parity", protocol_lifecycle),
        ("task authority parity", task_lifecycle),
        ("ADR-0020 authority parity", adr),
    ):
        normalized_authority_body = body.replace("_", " ").replace("`", "")
        require_terms(
            normalized_authority_body,
            {
                "result acceptance",
                "write ownership",
                "late completion",
                "quarantine",
                "late disk write",
            },
            label,
            failures,
        )
    require_terms(
        research_lifecycle.replace("_", " ").replace("`", ""),
        {
            "result acceptance",
            "late completion",
            "quarantine",
            "자동 취합",
            "성공 판정",
            "ownership",
            "pause",
        },
        "research read-authority parity",
        failures,
    )
    require_terms(
        implementation_lifecycle.replace("_", " ").replace("`", ""),
        {
            "ownership",
            "late completion",
            "quarantine",
            "late disk write",
            "persisted paused",
        },
        "implementation write-authority parity",
        failures,
    )
    require_terms(
        faq_ko,
        {
            "result acceptance authority",
            "write ownership",
            "late_completion",
            "quarantine",
            "late disk write",
            "persisted `paused`",
        },
        "Korean FAQ authority parity",
        failures,
    )
    require_terms(
        faq_en,
        {
            "result acceptance authority",
            "write ownership",
            "late_completion",
            "quarantine",
            "late disk write",
            "persistently pauses",
        },
        "English FAQ authority parity",
        failures,
    )
    adr_frontmatter = between(adr, "---\n", "\n---")
    adr_partial_scope = active_scope(
        adr_path,
        "### 3. ADR-0017을 부분적으로만 supersede한다",
        "\n## Consequences",
        failures,
    )
    require(
        "partially_supersedes: [ADR-0017]" in adr_frontmatter
        and re.search(r"^supersedes:", adr_frontmatter, re.MULTILINE) is None,
        "ADR-0020 no longer records a partial-only supersede of ADR-0017",
        failures,
    )
    require_terms(
        adr_partial_scope,
        {
            "suspected_silent_stall",
            "first observable activity",
            "first-activity",
            "unchanged",
            "사용자",
            "clean retry",
            "write ownership",
            "verification non-skip",
        },
        "ADR-0020 partial supersede boundary",
        failures,
    )

    # AC-R33: authority metadata remains phase-ledger-only while the existing
    # report v2 and §5.8 routing schemas remain unchanged.
    require(
        OPTIONAL_FIELDS == EXPECTED_OPTIONAL_FIELDS
        and OPTIONAL_FIELDS.isdisjoint(AUTHORITY_LEDGER_FIELDS),
        "authority metadata expanded the report v2 lifecycle optional fields",
        failures,
    )
    require_cooccurring_terms(
        report_schema,
        {
            "authority_kind",
            "authority_ref",
            "result_acceptance_revoked",
            "phase ledger",
            "report field로 추가하지 않는다",
        },
        "report v2 authority field locality",
        failures,
    )

    # AC-R34: source and fixture keep environment completion separate from the
    # later advisor disposition; AC-R12/R24 still reject absence-based counters.
    authority_cases = {
        case["name"]: case
        for case in cases_doc.get("authority_isolation_cases", [])
    }
    for case_name in (
        "read_only_late_completion_after_acceptance_revocation",
        "write_late_completion_without_disk_write",
        "write_late_disk_write_pauses_dependency_closure",
    ):
        case = authority_cases[case_name]
        ledger = case["ledger"]
        completed_positions = [
            index for index, row in enumerate(ledger) if row.get("event") == "completed"
        ]
        late_positions = [
            index for index, row in enumerate(ledger) if row.get("event") == "late_completion"
        ]
        require(
            len(completed_positions) == len(late_positions) == 1
            and completed_positions[0] < late_positions[0]
            and ledger[completed_positions[0]].get("provenance") == "environment"
            and ledger[late_positions[0]].get("provenance") == "advisor",
            f"environment completion and advisor disposition were collapsed: {case_name}",
            failures,
        )

    # The research pointer must resolve to an exact subheading inside §2.6.
    uncertainty_heading = "#### 불확실성 보존 (계층 간 격상 금지)"
    require(
        uncertainty_heading in protocol_regression,
        "exact uncertainty-preservation subheading is missing inside protocol §2.6",
        failures,
    )
    require(
        "§2.6의 하위 제목 `#### 불확실성 보존 (계층 간 격상 금지)`" in research,
        "research-advisor does not point to the exact protocol §2.6 subheading",
        failures,
    )


def validate_documentation(failures: list[str]) -> None:
    protocol_path = ROOT / "plugins/atp/docs/development/agent-team-protocol.md"
    platform_path = ROOT / "plugins/atp/docs/development/platform-adapters.md"
    appendix_path = ROOT / "plugins/atp/docs/development/codex-lifecycle-routing.md"
    task_path = ROOT / "plugins/atp/skills/task/SKILL.md"
    research_path = ROOT / "plugins/atp/agents/research-advisor.md"
    implementation_path = ROOT / "plugins/atp/agents/implementation-advisor.md"
    faq_ko_path = ROOT / "docs/usage/faq.md"
    faq_en_path = ROOT / "docs/usage/faq.en.md"

    protocol = protocol_path.read_text(encoding="utf-8")
    lifecycle = active_scope(protocol_path, "### 2.5", "### 2.6", failures)
    platform = active_scope(platform_path, "### 3.1", "\n## 4.", failures)
    appendix = appendix_path.read_text(encoding="utf-8") if appendix_path.exists() else ""
    task = active_scope(task_path, "#### 5.2", "\n### 6.", failures)
    research = active_scope(research_path, "## Worker lifecycle", "\n## 출력", failures)
    implementation = active_scope(
        implementation_path, "## Worker lifecycle", "\n## 출력", failures
    )
    faq_ko = active_scope(
        faq_ko_path,
        "### Q. Advisor가 오류 없이 `running` 상태에서 첫 활동을 보이지 않는다.",
        "\n---",
        failures,
    )
    faq_en = active_scope(
        faq_en_path,
        "### Q. An advisor stays `running` without an error or any first activity.",
        "\n---",
        failures,
    )
    active_scopes = {
        "protocol §2.5": lifecycle,
        "platform §3.1": platform,
        "Codex appendix": appendix,
        "task §5.2": task,
        "research-advisor lifecycle": research,
        "implementation-advisor lifecycle": implementation,
        "FAQ ko lifecycle": faq_ko,
        "FAQ en lifecycle": faq_en,
    }

    for label, body in active_scopes.items():
        deprecated_hits = sorted(term for term in DEPRECATED_ACTIVE_TERMS if term in body)
        require(not deprecated_hits, f"deprecated detection terms in {label}: {deprecated_hits}", failures)
        heartbeat_transition = re.search(
            r"\bheartbeat[_ -](?:deadline|budget)\b|heartbeat\s*(?:기한|예산)",
            body,
            re.IGNORECASE,
        )
        require(not heartbeat_transition, f"heartbeat deadline transition remains in {label}", failures)

    forbidden_hits = sorted(name for name in COMMON_FORBIDDEN if name in lifecycle)
    require(
        not forbidden_hits,
        f"common lifecycle contract contains Codex tool names: {forbidden_hits}",
        failures,
    )
    require(
        not re.search(r"\b\d+\s*(?:초|seconds?|minutes?|분)\b", lifecycle, re.IGNORECASE),
        "common lifecycle contract contains a fixed time value",
        failures,
    )
    for state in (
        "running",
        "completed",
        "failed",
        "interrupted",
        "approval_required",
        "environment_state_unknown",
    ):
        require(state in lifecycle, f"missing environment state in common protocol: {state}", failures)
        require(state in platform, f"missing environment state in capability profile: {state}", failures)
    for field in OPTIONAL_FIELDS:
        require(field in protocol, f"missing optional report field: {field}", failures)

    report_schema = active_scope(protocol_path, "## 8. 보고서 스키마", "\n## 9.", failures)
    require("silent_stall" in report_schema, "report reader no longer documents legacy silent_stall", failures)
    require(
        "legacy" in report_schema.lower() or "과거" in report_schema,
        "silent_stall is not marked as reader-only legacy compatibility",
        failures,
    )

    require(appendix_path.exists(), "Codex lifecycle appendix is missing", failures)
    if appendix:
        for name in COMMON_FORBIDDEN:
            require(name in appendix, f"Codex appendix lacks mapping for {name}", failures)
        for state in ("running", "completed", "environment_state_unknown"):
            require(state in appendix, f"Codex appendix lacks environment mapping for {state}", failures)
        require("unsupported" in appendix.lower() or "미지원" in appendix,
                "Codex appendix does not disclose unsupported lifecycle events", failures)

    for label, body in (
        ("task §5.2", task),
        ("research-advisor lifecycle", research),
        ("implementation-advisor lifecycle", implementation),
    ):
        require("§2.5" in body, f"execution subject does not reference §2.5: {label}", failures)
        require(
            "environment_state_unknown" in body,
            f"execution subject lacks unknown-state safety fallback: {label}",
            failures,
        )

    for label, body, approval_word in (
        ("FAQ ko lifecycle", faq_ko, "승인"),
        ("FAQ en lifecycle", faq_en, "approval"),
    ):
        for term in ("running", "clean retry", "late_completion", "verification"):
            require(term.lower() in body.lower(), f"{label} lacks lifecycle invariant: {term}", failures)
        require(approval_word in body.lower(), f"{label} lacks user approval invariant", failures)


def validate_addendum4_source_parity(failures: list[str]) -> None:
    protocol_path = ROOT / "plugins/atp/docs/development/agent-team-protocol.md"
    platform_path = ROOT / "plugins/atp/docs/development/platform-adapters.md"
    appendix_path = ROOT / "plugins/atp/docs/development/codex-lifecycle-routing.md"
    task_path = ROOT / "plugins/atp/skills/task/SKILL.md"
    research_path = ROOT / "plugins/atp/agents/research-advisor.md"
    explorer_path = ROOT / "plugins/atp/agents/parallel-explorer.md"
    implementation_path = ROOT / "plugins/atp/agents/implementation-advisor.md"
    adr_path = ROOT / "docs/adr/ADR-0020-environment-authoritative-subagent-lifecycle.md"
    faq_ko_path = ROOT / "docs/usage/faq.md"
    faq_en_path = ROOT / "docs/usage/faq.en.md"
    architecture_path = (
        ROOT / "docs/architecture/environment-authoritative-subagent-lifecycle-design.md"
    )
    changes_path = (
        ROOT / "docs/changes/2026-08-12-environment-authoritative-subagent-lifecycle.md"
    )
    release_path = ROOT / "docs/development/release-checklist.md"

    protocol_lifecycle = active_scope(
        protocol_path, "### 2.5", "### 2.6", failures
    )
    protocol_confidence = active_scope(
        protocol_path, "### 4.8", "\n## 5.", failures
    )
    protocol_report = active_scope(
        protocol_path, "## 8. 보고서 스키마", "\n## 9.", failures
    )
    platform_lifecycle = active_scope(
        platform_path, "### 3.1", "\n## 4.", failures
    )
    task_lifecycle = active_scope(task_path, "#### 5.2", "\n### 6.", failures)
    research = research_path.read_text(encoding="utf-8")
    research_lifecycle = between(research, "## Worker lifecycle", "\n## 출력")
    implementation = implementation_path.read_text(encoding="utf-8")
    implementation_lifecycle = between(
        implementation, "## Worker lifecycle", "\n## 출력"
    )
    explorer = explorer_path.read_text(encoding="utf-8")
    appendix = appendix_path.read_text(encoding="utf-8")
    adr = adr_path.read_text(encoding="utf-8")
    require(
        "## Accepted clarification — approval capability와 recovery disposition"
        in adr,
        "ADR-0020 approval/recovery clarification is missing",
        failures,
    )
    adr_clarification = adr.split(
        "## Accepted clarification — approval capability와 recovery disposition", 1
    )[-1]
    faq_ko = faq_ko_path.read_text(encoding="utf-8")
    faq_en = faq_en_path.read_text(encoding="utf-8")
    architecture = architecture_path.read_text(encoding="utf-8")
    changes = changes_path.read_text(encoding="utf-8")
    release_document = release_path.read_text(encoding="utf-8")
    require(
        "## 10. Environment-authoritative subagent lifecycle 계약"
        in release_document,
        "release checklist lifecycle gate is missing",
        failures,
    )
    release = release_document.split(
        "## 10. Environment-authoritative subagent lifecycle 계약", 1
    )[-1]

    # AC-R35/AC-R37: all execution and user-facing layers preserve the
    # observed approval state and keep workflow blocking in a separate sink.
    approval_scopes = {
        "protocol §2.5": protocol_lifecycle,
        "platform §3.1": platform_lifecycle,
        "Codex appendix": appendix,
        "task §5.2": task_lifecycle,
        "research-advisor": research_lifecycle,
        "implementation-advisor": implementation_lifecycle,
        "ADR-0020 clarification": adr_clarification,
        "FAQ ko": faq_ko,
        "FAQ en": faq_en,
        "architecture": architecture,
        "changes": changes,
        "release checklist": release,
    }
    for label, body in approval_scopes.items():
        require_terms(
            body,
            {"approval_required", "relay", "environment_state_unknown", "blocked"},
            f"{label} approval state/capability parity",
            failures,
        )
        require(
            re.search(r"unavailable|unsupported|미지원|불가", body, re.IGNORECASE)
            is not None
            and re.search(r"status[^\n]*(?:error|오류)|error[^\n]*status", body, re.IGNORECASE)
            is not None,
            f"{label} does not distinguish relay limits from status unavailable/error",
            failures,
        )

    # AC-R36/AC-R38: concrete producer/adapter paths expose the safe payload,
    # zero mutations, and same-identity accounting semantics.
    for label, body in (
        ("protocol §2.5", protocol_lifecycle),
        ("Codex appendix", appendix),
        ("task §5.2", task_lifecycle),
        ("research-advisor", research_lifecycle),
        ("implementation-advisor", implementation_lifecycle),
        ("ADR-0020 clarification", adr_clarification),
        ("architecture", architecture),
    ):
        require_terms(
            body,
            {
                "ended_at",
                "termination",
                "provenance",
                "source_ref",
                "concern",
                "ledger",
                "mutation",
            },
            f"{label} relay-unavailable safe return",
            failures,
        )
        require(
            "0" in body or "수행하지 않는다" in body,
            f"{label} lacks the zero-action relay-unavailable boundary",
            failures,
        )
        require(
            has_same_environment_continuation_accounting(body),
            f"{label} lacks same-identity continuation accounting",
            failures,
        )

    # AC-R39 through AC-R41: runtime, both producers, FAQs, architecture, and
    # release evidence agree on marker coverage and aggregate derivation.
    confidence_scopes = {
        "protocol §4.8": protocol_confidence,
        "research-advisor": research,
        "parallel-explorer": explorer,
        "FAQ ko": faq_ko,
        "FAQ en": faq_en,
        "architecture": architecture,
        "changes": changes,
    }
    faq_confidence_labels = {"FAQ ko", "FAQ en"}
    for label, body in confidence_scopes.items():
        normalized = normalized_semantic_text(body)
        marker_terms = (
            {"source_confidence", "high", "mixed", "low"}
            if label in faq_confidence_labels
            else {
                "확인됨",
                "추정",
                "미확인",
                "source_confidence",
                "high",
                "mixed",
                "low",
                "marker coverage",
                "aggregate derivation",
            }
        )
        require_terms(
            normalized,
            marker_terms,
            f"{label} confidence derivation parity",
            failures,
        )
        if label in faq_confidence_labels:
            require(
                has_item_marker_vocabulary(body)
                and bool(confidence_mapping_anchor(body))
                and has_confidence_self_checks(body),
                f"{label} confidence derivation parity lacks localized marker "
                "coverage or aggregate derivation semantics",
                failures,
            )
    require_terms(
        release.lower().replace("`", ""),
        {
            "axis/item",
            "marker",
            "source_confidence",
            "high|mixed|low",
            "marker coverage",
            "aggregate derivation",
        },
        "release checklist confidence gate",
        failures,
    )
    for label, body in (
        ("protocol §4.8", protocol_confidence),
        ("research-advisor", research),
        ("parallel-explorer", explorer),
        ("architecture", architecture),
    ):
        require(
            "namespace" in body.lower()
            and "strict majority" in body.lower()
            and "mixed" in body.lower(),
            f"{label} lacks the confidence namespace/truth-table boundary",
            failures,
        )
    for label, body in (("FAQ ko", faq_ko), ("FAQ en", faq_en)):
        require(
            bool(confidence_mapping_anchor(body)),
            f"{label} lacks the confidence namespace/strict-majority truth-table boundary",
            failures,
        )
    for label, body in (
        ("research-advisor", research),
        ("parallel-explorer", explorer),
    ):
        self_check = body.split("## 자가 검증", 1)[-1]
        require_terms(
            self_check,
            {"marker coverage", "aggregate derivation", "identity", "source_confidence"},
            f"{label} confidence self-check pair",
            failures,
        )
    require(
        re.search(r"누락[^\n]*(?:추정|재작성|합성)", research) is not None,
        "research-advisor permits missing-marker authority promotion",
        failures,
    )
    require_terms(
        explorer,
        {"이름 붙은 모든 axis", "이름 붙은 모든 item", "정확히 하나", "직접 붙인다"},
        "parallel-explorer per-identity marker producer",
        failures,
    )
    explorer_frontmatter = between(explorer, "---\n", "\n---")
    require(
        re.search(r"^version:\s*2$", explorer_frontmatter, re.MULTILINE) is not None,
        "parallel-explorer output-contract version is not 2",
        failures,
    )

    # AC-R42/AC-R43/AC-R45: producer and user-facing layers share the exact
    # closed disposition vocabulary while report v2 remains additive/legacy-safe.
    reason_scopes = {
        "protocol §8": protocol_report,
        "task §5.2": task_lifecycle,
        "research-advisor": research_lifecycle,
        "implementation-advisor": implementation_lifecycle,
        "ADR-0020 clarification": adr_clarification,
        "FAQ ko": faq_ko,
        "FAQ en": faq_en,
        "architecture": architecture,
        "changes": changes,
        "release checklist": release,
    }
    for label, body in reason_scopes.items():
        require_terms(
            body,
            {
                "lifecycle_fallback_reason",
                "failed",
                "interrupted",
                "late_completion",
                *RECOVERY_DISPOSITIONS,
            },
            f"{label} recovery disposition parity",
            failures,
        )
    for label, body in (
        ("protocol §8", protocol_report),
        ("task §5.2", task_lifecycle),
        ("research-advisor", research_lifecycle),
        ("implementation-advisor", implementation_lifecycle),
    ):
        require_terms(
            body,
            {"cause=<", "@<concrete source_ref>", "disposition=<", "rationale=<"},
            f"{label} canonical reason producer form",
            failures,
        )
        require(
            has_immediate_intermediate_reason(body),
            f"{label} does not serialize the intermediate abnormal reason before "
            "retry exhaustion",
            failures,
        )
    for label, body in reason_scopes.items():
        normalized = body.lower().replace("_", " ").replace("-", " ")
        require(
            "cause" in normalized
            and "rationale" in normalized
            and "retry" in normalized
            and ("exhaust" in normalized or "소진" in normalized or "cap" in normalized),
            f"{label} lacks current abnormal reason semantics",
            failures,
        )
    require_terms(
        protocol_report,
        {
            "schema_version: 2",
            "optional lifecycle 필드",
            "legacy",
            "기존 string 필드",
            "silent_stall",
        },
        "protocol report v2 legacy compatibility",
        failures,
    )
    require(
        "phase_control_disposition" not in protocol_report
        and "disposition:" not in protocol_report
        and re.search(
            r"^\s+termination:\s+completed \| failed \| interrupted \| late_completion$",
            protocol_report,
            re.MULTILINE,
        )
        is not None,
        "recovery disposition leaked into report fields or termination enum",
        failures,
    )

    # AC-R44: source producers retain completed/nonterminal nullability and
    # quarantined late completion with authority/no-auto-success boundaries.
    require_terms(
        protocol_report,
        {"completed", "정상 완료", "필드 부재", "lifecycle_fallback_reason"},
        "protocol §8 completed reason nullability",
        failures,
    )
    for label, body in (
        ("research-advisor", research_lifecycle),
        ("implementation-advisor", implementation_lifecycle),
    ):
        require_terms(
            body,
            {"completed", "null", "non-terminal", "termination", "생략"},
            f"{label} lifecycle nullability preservation",
            failures,
        )
    for label, body in (
        ("protocol §2.5", protocol_lifecycle),
        ("research-advisor", research_lifecycle),
        ("implementation-advisor", implementation_lifecycle),
        ("ADR-0020", adr),
        ("architecture", architecture),
    ):
        require_terms(
            body,
            {"late_completion", "authority", "quarantine", "자동", "성공"},
            f"{label} late-completion quarantine parity",
            failures,
        )

    # AC-R46: the accepted ADR remains a partial supersede of observation and
    # detection only; Addendum 4 does not widen the environment authority.
    require_terms(
        adr,
        {
            "partially_supersedes: [ADR-0017]",
            "부분적으로만 supersede",
            "감지 부분",
            "관측 budget",
            "확장하지 않는다",
            "environment가 명시",
        },
        "ADR-0020 partial-supersede boundary",
        failures,
    )

    # AC-R47: the new fixture domains add no absence-derived producer counter.
    cases_doc = load("lifecycle-cases.json")
    addendum4_fixture_keys = collect_keys(
        {
            "approval_capability_cases": cases_doc.get("approval_capability_cases"),
            "confidence_derivation_cases": cases_doc.get("confidence_derivation_cases"),
            "lifecycle_reason_cases": cases_doc.get("lifecycle_reason_cases"),
        }
    )
    absence_counter = re.compile(
        r"(?:wait|timeout|elapsed|silence|unchanged|snapshot|progress|output|tool|heartbeat)"
        r".*(?:count|counter|budget|limit)$",
        re.IGNORECASE,
    )
    require(
        not sorted(
            key for key in addendum4_fixture_keys if absence_counter.fullmatch(key)
        ),
        "Addendum 4 fixture contains an absence-derived producer counter",
        failures,
    )


def main() -> int:
    failures: list[str] = []
    validate_reports(failures)
    validate_cases(failures)
    validate_agent_source_specs(failures)
    validate_documentation(failures)
    validate_addendum4_source_parity(failures)

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("PASS: environment-authoritative lifecycle contract and compatibility fixtures")
    return 0


if __name__ == "__main__":
    sys.exit(main())
