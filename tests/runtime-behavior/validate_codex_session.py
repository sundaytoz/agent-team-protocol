#!/usr/bin/env python3
"""Validate actual Codex JSONL behavior for ATP orchestration profiles."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


COLLAB_NAMES = {
    "spawn_agent",
    "wait_agent",
    "list_agents",
    "interrupt_agent",
    "followup_task",
    "send_message",
}
PUBLIC_COLLAB_NAMES = {
    "spawn": "spawn_agent",
    "wait": "wait_agent",
    "list": "list_agents",
    "close": "interrupt_agent",
    "resume": "followup_task",
    "send_input": "send_message",
}
DENIAL_MARKERS = (
    "blocked by pretooluse hook",
    "command blocked by pretooluse hook",
    "tool call blocked by pretooluse hook",
    'permissiondecision":"deny',
)
LEDGER_FIELDS = {
    "recorded_at",
    "await_id",
    "owner_report_invocation_id",
    "event",
    "source_ref",
    "details",
}
LEDGER_EVENTS = {
    "await_capability_checked",
    "await_registered",
    "wake_batch",
    "wait_wakeup_capability_unavailable",
    "external_continuation_selected",
    "measurement",
}
MEASUREMENT_FIELDS = {
    "spawn_calls": "spawn_agent",
    "wait_calls": "wait_agent",
    "list_calls": "list_agents",
}
TERMINAL_STATES = {"completed", "failed", "interrupted"}
CAPABILITY_VALUES = {"supported", "unsupported", "unknown"}
MESSAGE_TYPE = re.compile(r"(?m)^Message Type: (MESSAGE|FINAL_ANSWER)\s*$")
ORDINAL_REF = re.compile(r"(?:transcript|session-jsonl):ordinal:(\d+)$")
MANAGED_EVENT_REF = re.compile(
    r"session:(?P<session>[^:]+):report:(?P<report>[^:]+):"
    r"environment:(?P<environment>.+):event:terminal-(?P<index>\d{4})$"
)
PLACEHOLDER = re.compile(r"<[^>]+>|\b(?:todo|tbd|unknown-ref)\b", re.IGNORECASE)
UNKNOWN_TELEMETRY_FIELDS = {
    "input_tokens",
    "cached_input_tokens",
    "output_tokens",
    "latency_ms",
    "steering_latency_ms",
}


def fail(message: str, failures: list[str]) -> None:
    failures.append(message)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
        if isinstance(value, dict):
            value.setdefault("_line", line_number)
            rows.append(value)
    return rows


def normalize_output(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def is_denied(value: Any) -> bool:
    text = json.dumps(normalize_output(value), ensure_ascii=False).lower()
    return any(marker in text for marker in DENIAL_MARKERS)


def parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value or value == "null":
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def row_ordinal(row: dict[str, Any]) -> int:
    value = row.get("ordinal", row.get("_line", 0))
    return value if isinstance(value, int) else 0


def content_text(content: Any) -> str:
    if not isinstance(content, list):
        return ""
    return "\n".join(
        str(item.get("text"))
        for item in content
        if isinstance(item, dict) and isinstance(item.get("text"), str)
    )


def author_key(value: Any) -> str:
    return str(value or "").rsplit("/", 1)[-1]


def normalized_agent_name(value: Any) -> str:
    return author_key(value).replace("_", "-")


def command_text(item: dict[str, Any]) -> str:
    command = item.get("command")
    if isinstance(command, list):
        return " ".join(str(part) for part in command)
    return str(command or "")


def is_mutation_event(event: dict[str, Any]) -> bool:
    if event["kind"] == "file_change":
        return True
    command = event.get("command", "")
    mutation_patterns = (
        r"\bgit\s+add\b",
        r"\bgit\s+commit\b",
        r"\bgit\s+push\b",
        r"\bgit\s+(?:switch|checkout|branch|mv)\b",
    )
    return any(re.search(pattern, command) for pattern in mutation_patterns)


def collect_behavior(rows: list[dict[str, Any]]) -> dict[str, Any]:
    calls: dict[str, dict[str, Any]] = {}
    custom_calls: dict[str, dict[str, Any]] = {}
    agent_names: dict[str, str] = {}
    public_completed = Counter()
    assistant_messages: list[str] = []
    wait_timeouts = 0
    executed_events: list[dict[str, Any]] = []
    lifecycle_events: list[dict[str, Any]] = []
    session_events: list[dict[str, Any]] = []
    parent_final_events: list[dict[str, Any]] = []
    skill_load_events: list[dict[str, Any]] = []

    for row in rows:
        ordinal = row_ordinal(row)
        timestamp = row.get("timestamp")
        if row.get("type") == "response_item":
            payload = row.get("payload")
            if not isinstance(payload, dict):
                continue
            payload_type = payload.get("type")
            if payload_type == "custom_tool_call":
                call_id = payload.get("call_id")
                if isinstance(call_id, str):
                    custom_calls[call_id] = {
                        "name": payload.get("name"),
                        "input": str(payload.get("input") or ""),
                        "call_ordinal": ordinal,
                        "call_timestamp": timestamp,
                    }
            elif payload_type == "custom_tool_call_output":
                call_id = payload.get("call_id")
                call = custom_calls.get(call_id) if isinstance(call_id, str) else None
                if call is not None:
                    source = call["input"]
                    successful = not is_denied(payload.get("output"))
                    if "tools.apply_patch" in source:
                        normalized_patch = source.replace("\\n", "\n")
                        paths = re.findall(
                            r"^\*\*\* (?:Add|Update|Delete) File: (.+)$",
                            normalized_patch,
                            re.MULTILINE,
                        )
                        session_events.append(
                            {
                                "kind": "file_change",
                                "ordinal": ordinal,
                                "timestamp": timestamp,
                                "paths": sorted(paths),
                                "command": "",
                                "diff": normalized_patch,
                                "successful": successful,
                            }
                        )
                    elif call.get("name") == "exec":
                        session_events.append(
                            {
                                "kind": "command",
                                "ordinal": ordinal,
                                "timestamp": timestamp,
                                "paths": [],
                                "command": source,
                                "successful": successful,
                            }
                        )
                        if successful and "codex-team/SKILL.md" in source:
                            skill_load_events.append(
                                {"ordinal": ordinal, "timestamp": timestamp}
                            )
            elif payload_type == "function_call":
                name = payload.get("name")
                call_id = payload.get("call_id")
                if name in COLLAB_NAMES and isinstance(call_id, str):
                    calls[call_id] = {
                        "name": name,
                        "arguments": payload.get("arguments"),
                        "call_ordinal": ordinal,
                        "call_timestamp": timestamp,
                    }
            elif payload_type == "function_call_output":
                call_id = payload.get("call_id")
                call = calls.get(call_id) if isinstance(call_id, str) else None
                if call is not None:
                    output = normalize_output(payload.get("output"))
                    call["output"] = output
                    call["output_ordinal"] = ordinal
                    call["output_timestamp"] = timestamp
                    if not is_denied(output):
                        task_name: Any = None
                        if call["name"] == "spawn_agent" and isinstance(output, dict):
                            arguments = normalize_output(call.get("arguments"))
                            agent_id = output.get("agent_id") or output.get("task_name")
                            task_name = (
                                arguments.get("task_name")
                                if isinstance(arguments, dict)
                                else None
                            )
                            canonical_task_name = output.get("task_name") or task_name
                            if isinstance(agent_id, str) and isinstance(
                                canonical_task_name, str
                            ):
                                agent_names[agent_id] = canonical_task_name
                        timed_out = bool(
                            call["name"] == "wait_agent"
                            and isinstance(output, dict)
                            and output.get("timed_out") is True
                        )
                        if timed_out:
                            wait_timeouts += 1
                        executed_events.append(
                            {
                                "name": call["name"],
                                "call_ordinal": call["call_ordinal"],
                                "ordinal": ordinal,
                                "timestamp": timestamp,
                                "timed_out": timed_out,
                                "agent_id": (
                                    output.get("agent_id") or output.get("task_name")
                                )
                                if isinstance(output, dict)
                                else None,
                                "task_name": (
                                    output.get("task_name") or task_name
                                )
                                if call["name"] == "spawn_agent"
                                and isinstance(output, dict)
                                else None,
                            }
                        )
                        if isinstance(output, dict):
                            state = output.get("status") or output.get("state")
                            if state in TERMINAL_STATES:
                                agent_id = output.get("agent_id")
                                lifecycle_events.append(
                                    {
                                        "type": "ENVIRONMENT_TERMINAL",
                                        "state": state,
                                        "author": output.get("task_name")
                                        or agent_names.get(str(agent_id))
                                        or output.get("agent_id"),
                                        "ordinal": ordinal,
                                        "timestamp": timestamp,
                                        "text": json.dumps(output, ensure_ascii=False),
                                    }
                                )
            elif payload_type == "agent_message":
                text = content_text(payload.get("content"))
                match = MESSAGE_TYPE.search(text)
                if match:
                    lifecycle_events.append(
                        {
                            "type": match.group(1),
                            "state": "completed"
                            if match.group(1) == "FINAL_ANSWER"
                            else "running",
                            "author": str(payload.get("author") or ""),
                            "ordinal": ordinal,
                            "timestamp": timestamp,
                            "text": text,
                        }
                    )
            elif payload_type == "message" and payload.get("role") == "assistant":
                text = content_text(payload.get("content"))
                if text:
                    assistant_messages.append(text)
                if payload.get("phase") == "final_answer":
                    parent_final_events.append(
                        {
                            "ordinal": ordinal,
                            "timestamp": timestamp,
                            "text": text,
                        }
                    )

        if row.get("type") == "item.completed":
            item = row.get("item")
            if not isinstance(item, dict):
                continue
            if item.get("type") == "collab_tool_call":
                normalized = PUBLIC_COLLAB_NAMES.get(str(item.get("tool")))
                if normalized:
                    public_completed[normalized] += 1
                    executed_events.append(
                        {
                            "name": normalized,
                            "call_ordinal": ordinal,
                            "ordinal": ordinal,
                            "timestamp": timestamp,
                            "timed_out": False,
                        }
                    )
            elif item.get("type") == "agent_message" and item.get("text"):
                text = str(item["text"])
                assistant_messages.append(text)
                match = MESSAGE_TYPE.search(text)
                if match:
                    lifecycle_events.append(
                        {
                            "type": match.group(1),
                            "state": "completed"
                            if match.group(1) == "FINAL_ANSWER"
                            else "running",
                            "author": str(item.get("author") or ""),
                            "ordinal": ordinal,
                            "timestamp": timestamp,
                            "text": text,
                        }
                    )

        if row.get("type") == "event_msg":
            payload = row.get("payload")
            item = payload.get("item") if isinstance(payload, dict) else None
            if (
                isinstance(payload, dict)
                and payload.get("type") == "item_completed"
                and isinstance(item, dict)
            ):
                if item.get("type") == "FileChange":
                    changes = item.get("changes") or {}
                    session_events.append(
                        {
                            "kind": "file_change",
                            "ordinal": ordinal,
                            "timestamp": timestamp,
                            "paths": sorted(changes.keys()),
                            "command": "",
                            "diff": "\n".join(
                                str(change.get("unified_diff") or "")
                                for change in changes.values()
                                if isinstance(change, dict)
                            ),
                        }
                    )
                elif item.get("type") == "CommandExecution":
                    command = command_text(item)
                    session_events.append(
                        {
                            "kind": "command",
                            "ordinal": ordinal,
                            "timestamp": timestamp,
                            "paths": [],
                            "command": command,
                            "successful": item.get("status") == "completed"
                            and item.get("exit_code") in (0, None),
                        }
                    )
                    if (
                        item.get("status") == "completed"
                        and item.get("exit_code") in (0, None)
                        and "codex-team/SKILL.md" in command
                    ):
                        skill_load_events.append(
                            {"ordinal": ordinal, "timestamp": timestamp}
                        )

    attempted = Counter(call["name"] for call in calls.values())
    denied = Counter()
    executed = Counter(public_completed)
    for call in calls.values():
        if "output" not in call:
            continue
        if is_denied(call["output"]):
            denied[call["name"]] += 1
        else:
            executed[call["name"]] += 1

    return {
        "attempted": dict(attempted),
        "denied": dict(denied),
        "executed": dict(executed),
        "executed_events": sorted(executed_events, key=lambda event: event["ordinal"]),
        "wait_timeouts": wait_timeouts,
        "assistant_text": "\n".join(assistant_messages),
        "lifecycle_events": sorted(
            lifecycle_events, key=lambda event: event["ordinal"]
        ),
        "session_events": sorted(session_events, key=lambda event: event["ordinal"]),
        "row_timestamps": {
            row_ordinal(row): row.get("timestamp") for row in rows
        },
        "agent_names": agent_names,
        "parent_final_events": sorted(
            parent_final_events, key=lambda event: event["ordinal"]
        ),
        "skill_load_events": sorted(
            skill_load_events, key=lambda event: event["ordinal"]
        ),
    }


def compare_trees(source: Path, installed: Path, failures: list[str]) -> None:
    source_files = {
        path.relative_to(source): path for path in source.rglob("*") if path.is_file()
    }
    installed_files = {
        path.relative_to(installed): path
        for path in installed.rglob("*")
        if path.is_file()
    }
    if set(source_files) != set(installed_files):
        missing = sorted(str(path) for path in set(source_files) - set(installed_files))
        extra = sorted(str(path) for path in set(installed_files) - set(source_files))
        fail(f"installed tree differs: missing={missing}, extra={extra}", failures)
        return
    for relative in sorted(source_files):
        if source_files[relative].read_bytes() != installed_files[relative].read_bytes():
            fail(f"installed file differs from source: {relative}", failures)


def load_appendix_capabilities(path: Path, failures: list[str]) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    match = re.search(
        r"<!-- codex:formal-capabilities:begin -->\s*```yaml\s*"
        r"formal_capabilities:\s*\n(?P<body>.*?)```\s*"
        r"<!-- codex:formal-capabilities:end -->",
        text,
        re.DOTALL,
    )
    if not match:
        fail("appendix formal capability matrix block is missing", failures)
        return {}
    capabilities: dict[str, str] = {}
    for raw in match.group("body").splitlines():
        item = re.fullmatch(r"\s{2}([a-z_]+):\s*(supported|unsupported|unknown)\s*", raw)
        if item:
            capabilities[item.group(1)] = item.group(2)
    if len(capabilities) != 12 or set(capabilities.values()) - CAPABILITY_VALUES:
        fail(
            "appendix capability matrix must contain exactly 12 formal judgments",
            failures,
        )
    return capabilities


def load_appendix_managed_profile(
    path: Path, failures: list[str]
) -> dict[str, bool | str]:
    text = path.read_text(encoding="utf-8")
    match = re.search(
        r"<!-- codex:managed-contract-fixture:begin -->\s*```yaml\s*"
        r"(?P<body>.*?)```\s*"
        r"<!-- codex:managed-contract-fixture:end -->",
        text,
        re.DOTALL,
    )
    if not match:
        fail("appendix managed contract fixture block is missing", failures)
        return {}
    profile: dict[str, bool | str] = {}
    for raw in match.group("body").splitlines():
        item = re.fullmatch(r"([a-z_]+):\s*(true|false|supported|unknown|unsupported)\s*", raw)
        if not item:
            continue
        value: bool | str
        if item.group(2) == "true":
            value = True
        elif item.group(2) == "false":
            value = False
        else:
            value = item.group(2)
        profile[item.group(1)] = value
    expected = {
        "formal_adapter_enabled": False,
        "manual_wait_polling_supported": False,
        "host_managed_subagent_orchestration": "supported",
        "team_execution_enabled": True,
    }
    if profile != expected:
        fail(
            f"appendix managed orchestration profile drift: expected {expected}, "
            f"observed {profile}",
            failures,
        )
    return profile


def parse_report(path: Path, failures: list[str]) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    frontmatter = re.match(r"\A---\s*\n(?P<body>.*?)\n---\s*\n", text, re.DOTALL)
    if not frontmatter:
        fail("report frontmatter is missing", failures)
        body = ""
    else:
        body = frontmatter.group("body")

    def scalar(name: str) -> str | None:
        match = re.search(rf"(?m)^{re.escape(name)}:\s*(.*?)\s*$", body)
        return match.group(1).strip("'\"") if match else None

    invocation_section = re.search(
        r"(?ms)^# Invocations\s*\n(?P<body>.*?)(?=^# |\Z)", text
    )
    invocations: list[dict[str, str | None]] = []
    if invocation_section:
        chunks = re.split(r"(?m)^- id:\s*", invocation_section.group("body"))[1:]
        for chunk in chunks:
            lines = chunk.splitlines()
            invocation: dict[str, str | None] = {"id": lines[0].strip()}
            for key in (
                "name",
                "environment_invocation_id",
                "started_at",
                "ended_at",
                "output_digest",
                "termination",
            ):
                match = re.search(rf"(?m)^  {key}:\s*(.*?)\s*$", chunk)
                invocation[key] = match.group(1).strip("'\"") if match else None
            invocations.append(invocation)
    return {
        "text": text,
        "session_id": scalar("session_id"),
        "ended_at": scalar("ended_at"),
        "invocations": invocations,
    }


def validate_lifecycle(
    behavior: dict[str, Any], report: dict[str, Any], failures: list[str]
) -> None:
    lifecycle = behavior["lifecycle_events"]
    messages = [event for event in lifecycle if event["type"] == "MESSAGE"]
    finals = [event for event in lifecycle if event["type"] == "FINAL_ANSWER"]
    terminal = [
        event
        for event in lifecycle
        if event["type"] in {"FINAL_ANSWER", "ENVIRONMENT_TERMINAL"}
    ]
    if not terminal:
        fail(
            "native cooperative transcript contains no FINAL_ANSWER or explicit "
            "environment terminal event",
            failures,
        )
    wait_events = [
        event for event in behavior["executed_events"] if event["name"] == "wait_agent"
    ]

    for message in messages:
        same_author = [
            event
            for event in terminal
            if event["ordinal"] > message["ordinal"]
            and (
                not event.get("author")
                or not message.get("author")
                or author_key(event.get("author"))
                == author_key(message.get("author"))
            )
        ]
        final_ordinal = same_author[0]["ordinal"] if same_author else sys.maxsize
        rejoins = [
            event
            for event in wait_events
            if event["call_ordinal"] > message["ordinal"]
            and event["call_ordinal"] < final_ordinal
        ]
        if not rejoins:
            fail(
                "MESSAGE is nonterminal and requires another native wait_agent join "
                "before FINAL_ANSWER or an explicit environment terminal event",
                failures,
            )

        semantic_events = [
            event
            for event in behavior["session_events"]
            if message["ordinal"] < event["ordinal"] < final_ordinal
            and is_mutation_event(event)
        ]
        semantic_calls = [
            event
            for event in behavior["executed_events"]
            if message["ordinal"] < event["call_ordinal"] < final_ordinal
            and event["name"] != "wait_agent"
        ]
        if semantic_events or semantic_calls:
            fail(
                "MESSAGE must keep lifecycle running with zero semantic actions "
                "until the next native join reaches a terminal event",
                failures,
            )

        if not same_author:
            fail(
                f"MESSAGE from {message.get('author') or 'unknown child'} has no "
                "FINAL_ANSWER or explicit environment terminal event",
                failures,
            )
            matching_name = author_key(message.get("author"))
            for invocation in report["invocations"]:
                name = str(invocation.get("name") or "")
                if name in {matching_name, f"{matching_name}-advisor"} and (
                    invocation.get("ended_at") not in (None, "null")
                    or invocation.get("termination") in TERMINAL_STATES
                ):
                    fail(
                        "MESSAGE-only invocation cannot record ended_at or terminal "
                        f"termination ({invocation.get('id')})",
                        failures,
                    )
            if report.get("ended_at") not in (None, "null"):
                fail("MESSAGE-only session cannot record report ended_at", failures)

    for terminal_event in terminal:
        matching_name = author_key(terminal_event.get("author"))
        matching_invocations = [
            invocation
            for invocation in report["invocations"]
            if str(invocation.get("name") or "")
            in {matching_name, f"{matching_name}-advisor"}
        ]
        if not matching_invocations:
            fail(
                f"{terminal_event['type']} from {terminal_event.get('author')!r} "
                "has no matching report invocation",
                failures,
            )
            continue
        terminal_time = parse_time(terminal_event.get("timestamp"))
        expected_termination = (
            "completed"
            if terminal_event["type"] == "FINAL_ANSWER"
            else terminal_event["state"]
        )
        for invocation in matching_invocations:
            ended_at = parse_time(invocation.get("ended_at"))
            if ended_at is None:
                fail(
                    f"terminal invocation {invocation.get('id')} is missing ended_at",
                    failures,
                )
            elif terminal_time is not None and ended_at < terminal_time:
                fail(
                    f"report invocation ended_at for {invocation.get('id')} precedes "
                    f"its matching {terminal_event['type']}",
                    failures,
                )
            if invocation.get("termination") != expected_termination:
                label = (
                    "FINAL_ANSWER requires report termination completed"
                    if terminal_event["type"] == "FINAL_ANSWER"
                    else f"ENVIRONMENT_TERMINAL requires report termination {expected_termination}"
                )
                fail(
                    f"{label} for invocation {invocation.get('id')}",
                    failures,
                )

    for timeout in (
        event
        for event in wait_events
        if event.get("timed_out") is True
    ):
        later_waits = [
            event
            for event in wait_events
            if event["call_ordinal"] > timeout["ordinal"]
        ]
        boundary = later_waits[0]["call_ordinal"] if later_waits else sys.maxsize
        semantic_events = [
            event
            for event in behavior["session_events"]
            if timeout["ordinal"] < event["ordinal"] < boundary
            and is_mutation_event(event)
        ]
        semantic_calls = [
            event
            for event in behavior["executed_events"]
            if timeout["ordinal"] < event["call_ordinal"] < boundary
            and event["name"] != "wait_agent"
        ]
        if semantic_events or semantic_calls:
            fail(
                "native wait timeout must have zero semantic recovery actions before rejoin",
                failures,
            )


def validate_report_timing(
    behavior: dict[str, Any], report: dict[str, Any], failures: list[str]
) -> None:
    ended_at = parse_time(report.get("ended_at"))
    if ended_at is None:
        fail("native-cooperative report ended_at is missing or invalid", failures)
        return

    lifecycle_times = [
        parse_time(event.get("timestamp"))
        for event in behavior["lifecycle_events"]
        if event["type"] in {"FINAL_ANSWER", "ENVIRONMENT_TERMINAL"}
    ]
    mutation_events = [
        event
        for event in behavior["session_events"]
        if event.get("successful", True) and is_mutation_event(event)
    ]
    boundary_events = mutation_events + [
        event
        for event in behavior["session_events"]
        if event.get("successful", True)
        and re.search(r"\bgit\s+(?:ls-remote|rev-parse)\b", event.get("command", ""))
    ]
    boundary_times = lifecycle_times + [
        parse_time(event.get("timestamp")) for event in boundary_events
    ]
    for boundary in (value for value in boundary_times if value is not None):
        if ended_at < boundary:
            fail(
                "session ended_at precedes FINAL_ANSWER, a requested-scope mutation, "
                "commit/push, or requested remote verification",
                failures,
            )
            break

    pushes = [
        event
        for event in behavior["session_events"]
        if event.get("successful", True)
        and re.search(r"\bgit\s+push\b", event.get("command", ""))
    ]
    remote_checks = [
        event
        for event in behavior["session_events"]
        if event.get("successful", True)
        and re.search(r"\bgit\s+ls-remote\b", event.get("command", ""))
    ]
    for push in pushes:
        if not any(event["ordinal"] >= push["ordinal"] for event in remote_checks):
            fail("git push lacks requested remote SHA verification via git ls-remote", failures)


def validate_host_managed_report_timing(
    behavior: dict[str, Any], report: dict[str, Any], failures: list[str]
) -> None:
    """Validate scalar time and serialization order without time-travel assumptions."""
    ended_at = parse_time(report.get("ended_at"))
    if ended_at is None:
        fail("host-managed report ended_at is missing or invalid", failures)
        return
    terminal_times = [
        parse_time(event.get("timestamp"))
        for event in behavior["lifecycle_events"]
        if event["type"] in {"FINAL_ANSWER", "ENVIRONMENT_TERMINAL"}
    ]
    for terminal_at in (value for value in terminal_times if value is not None):
        if ended_at < terminal_at:
            fail("host-managed session ended_at precedes a requested terminal delivery", failures)
            break

    completion_events = [
        event
        for event in behavior["session_events"]
        if event.get("successful", True) and is_report_completion_serialization(event)
    ]
    if not completion_events:
        fail("host-managed transcript has no report completion serialization event", failures)
        return
    first_completion = completion_events[0]
    completion_at = parse_time(first_completion.get("timestamp"))
    if completion_at is not None and ended_at > completion_at:
        fail("report serialized a future ended_at before that instant occurred", failures)

    prior_boundaries = [
        event
        for event in behavior["session_events"]
        if event.get("successful", True)
        and event["ordinal"] < first_completion["ordinal"]
        and (
            is_mutation_event(event)
            or re.search(
                r"\bgit\s+(?:ls-remote|rev-parse)\b", event.get("command", "")
            )
        )
    ]
    for boundary in prior_boundaries:
        boundary_at = parse_time(boundary.get("timestamp"))
        if boundary_at is not None and ended_at < boundary_at:
            fail(
                "host-managed session ended_at precedes a prior requested-scope "
                "mutation or remote verification",
                failures,
            )
            break

    pushes = [
        event
        for event in behavior["session_events"]
        if event.get("successful", True)
        and re.search(r"\bgit\s+push\b", event.get("command", ""))
    ]
    remote_checks = [
        event
        for event in behavior["session_events"]
        if event.get("successful", True)
        and re.search(r"\bgit\s+ls-remote\b", event.get("command", ""))
    ]
    for push in pushes:
        if not any(event["ordinal"] >= push["ordinal"] for event in remote_checks):
            fail("git push lacks requested remote SHA verification via git ls-remote", failures)


def validate_retrospective_order(
    behavior: dict[str, Any], report: dict[str, Any], failures: list[str]
) -> None:
    retro_finals = [
        event
        for event in behavior["lifecycle_events"]
        if event["type"] == "FINAL_ANSWER"
        and "retrospective" in str(event.get("author") or "")
    ]
    if not retro_finals:
        return
    final = retro_finals[-1]
    later_commands = [
        event
        for event in behavior["session_events"]
        if event["kind"] == "command"
        and event.get("successful", True)
        and event["ordinal"] > final["ordinal"]
    ]
    commits_or_pushes = [
        event
        for event in later_commands
        if re.search(r"\bgit\s+(?:commit|push)\b", event["command"])
    ]
    report_restage = [
        event
        for event in later_commands
        if re.search(r"\bgit\s+add\b[^\n]*report\.md", event["command"])
    ]
    if not commits_or_pushes and not report_restage:
        return

    report_changes = [
        event
        for event in behavior["session_events"]
        if event["kind"] == "file_change"
        and event["ordinal"] > final["ordinal"]
        and any(path.endswith("report.md") for path in event["paths"])
    ]
    apply_ordinal = report_changes[-1]["ordinal"] if report_changes else final["ordinal"]
    stages = [event for event in report_restage if event["ordinal"] > apply_ordinal]
    if not stages:
        fail(
            "retrospective application must be followed by report restaging before commit/push",
            failures,
        )
        return
    stage = stages[0]
    validations = [
        event
        for event in later_commands
        if event["ordinal"] > stage["ordinal"]
        and (
            "validate_codex_session.py" in event["command"]
            or "git diff --cached --check" in event["command"]
        )
    ]
    same_command_validation = (
        "git diff --cached --check" in stage["command"]
        and stage["command"].find("git add")
        < stage["command"].find("git diff --cached --check")
    )
    if not validations and not same_command_validation:
        fail(
            "report restaging must be followed by report/staged revalidation",
            failures,
        )
        return
    validation_ordinal = validations[0]["ordinal"] if validations else stage["ordinal"]
    out_of_order = any(
        event["ordinal"] < validation_ordinal for event in commits_or_pushes
    )
    for event in commits_or_pushes:
        if event["ordinal"] != validation_ordinal:
            continue
        command = event["command"]
        validation_positions = [
            position
            for marker in ("validate_codex_session.py", "git diff --cached --check")
            if (position := command.find(marker)) >= 0
        ]
        terminal_positions = [
            position
            for marker in ("git commit", "git push")
            if (position := command.find(marker)) >= 0
        ]
        if not validation_positions or (
            terminal_positions and min(terminal_positions) < min(validation_positions)
        ):
            out_of_order = True
    if out_of_order:
        fail(
            "commit/push occurred before retrospective apply -> report restage -> "
            "revalidation completed",
            failures,
        )


def validate_native_ledger(
    path: Path,
    behavior: dict[str, Any],
    report: dict[str, Any],
    appendix_capabilities: dict[str, str],
    failures: list[str],
) -> None:
    rows = load_jsonl(path)
    for index, row in enumerate(rows, 1):
        actual_fields = set(row) - {"_line"}
        if actual_fields != LEDGER_FIELDS:
            fail(
                f"ledger envelope row {index} must contain exactly six fields; "
                f"missing={sorted(LEDGER_FIELDS - actual_fields)}, "
                f"extra={sorted(actual_fields - LEDGER_FIELDS)}",
                failures,
            )
        if row.get("event") not in LEDGER_EVENTS:
            fail(f"ledger event vocabulary drift at row {index}", failures)
        if parse_time(row.get("recorded_at")) is None:
            fail(f"ledger recorded_at is invalid at row {index}", failures)
        owner = row.get("owner_report_invocation_id")
        if not isinstance(owner, str) or not owner:
            fail(f"ledger owner_report_invocation_id is missing at row {index}", failures)
        elif owner not in {item.get("id") for item in report["invocations"]}:
            fail(f"ledger owner {owner!r} is absent from report Invocations", failures)
        source_ref = row.get("source_ref")
        if (
            not isinstance(source_ref, str)
            or not source_ref.strip()
            or PLACEHOLDER.search(source_ref)
        ):
            fail(f"ledger source_ref is not concrete at row {index}: {source_ref!r}", failures)
        if not isinstance(row.get("details"), dict):
            fail(f"ledger details are missing at row {index}", failures)
        if row.get("await_id") is not None:
            fail(f"native cooperative ledger await_id must be null at row {index}", failures)

    unavailable = [
        row for row in rows if row.get("event") == "wait_wakeup_capability_unavailable"
    ]
    if unavailable:
        fail(
            "formal capability gap incorrectly emitted "
            f"wait_wakeup_capability_unavailable ({len(unavailable)} rows)",
            failures,
        )
    checked = [row for row in rows if row.get("event") == "await_capability_checked"]
    if len(checked) != 1:
        fail(
            "await_capability_checked must occur exactly once "
            f"(observed {len(checked)})",
            failures,
        )
    else:
        details = checked[0].get("details")
        if isinstance(details, dict):
            if details.get("formal_capabilities") != appendix_capabilities:
                fail("capability matrix drift from Codex appendix", failures)
            if details.get("formal_adapter_enabled") is not False:
                fail("Codex native mode must preserve formal_adapter_enabled=false", failures)
            if details.get("native_join_supported") is not True:
                fail("Codex native mode did not record native_join_supported=true", failures)
            if details.get("selected_mode") != "host_native_cooperative":
                fail(
                    "Codex native mode ledger selected_mode is not host_native_cooperative",
                    failures,
                )

    measurements = [row for row in rows if row.get("event") == "measurement"]
    waits = behavior["executed"].get("wait_agent", 0)
    if len(measurements) != waits:
        fail(
            f"measurement rows must record every native wait (expected {waits}, "
            f"observed {len(measurements)})",
            failures,
        )
    previous_waits = 0
    wait_output_ordinals = {
        event["ordinal"]
        for event in behavior["executed_events"]
        if event["name"] == "wait_agent"
    }
    for index, row in enumerate(measurements, 1):
        source_ref = row.get("source_ref")
        match = ORDINAL_REF.fullmatch(source_ref) if isinstance(source_ref, str) else None
        if not match:
            fail(f"measurement source_ref is not a concrete transcript ordinal: {source_ref!r}", failures)
            continue
        ordinal = int(match.group(1))
        if ordinal not in behavior["row_timestamps"]:
            fail(
                f"measurement source_ref does not resolve to a transcript row: {source_ref!r}",
                failures,
            )
            continue
        if ordinal not in wait_output_ordinals:
            fail(
                "measurement source_ref must resolve to the corresponding native "
                f"wait return: {source_ref!r}",
                failures,
            )
            continue
        prefix = [
            event
            for event in behavior["executed_events"]
            if event["ordinal"] <= ordinal
        ]
        counts = Counter(event["name"] for event in prefix)
        timeout_count = sum(event["timed_out"] for event in prefix)
        details = row.get("details")
        if not isinstance(details, dict):
            continue
        expected_values = {
            field: counts.get(tool, 0) for field, tool in MEASUREMENT_FIELDS.items()
        }
        expected_values.update(
            {
                "root_model_resumes": counts.get("wait_agent", 0),
                "wait_timeouts": timeout_count,
                "semantic_recovery_actions": max(counts.get("spawn_agent", 0) - 1, 0)
                + counts.get("list_agents", 0)
                + counts.get("interrupt_agent", 0)
                + counts.get("followup_task", 0)
                + counts.get("send_message", 0),
            }
        )
        for field, expected in expected_values.items():
            if details.get(field) != expected:
                fail(
                    f"measurement {field} drift at row {index}: expected {expected}, "
                    f"observed {details.get(field)!r}",
                    failures,
                )
        if details.get("wait_calls") != previous_waits + 1:
            fail("measurement wait_calls must be cumulative one row per native wait", failures)
        previous_waits = int(details.get("wait_calls", previous_waits))
        recorded_at = parse_time(row.get("recorded_at"))
        event_time = parse_time(behavior["row_timestamps"].get(ordinal))
        if recorded_at is not None and event_time is not None and recorded_at != event_time:
            fail("measurement recorded_at does not match source_ref timestamp", failures)


def validate_native_cooperative(behavior: dict[str, Any], failures: list[str]) -> None:
    executed = behavior["executed"]
    if executed.get("spawn_agent", 0) != 1:
        fail(
            f"native cooperative regression expects exactly one spawn_agent "
            f"(observed {executed.get('spawn_agent', 0)})",
            failures,
        )
    if executed.get("wait_agent", 0) < 2:
        fail("native cooperative MESSAGE path requires at least two wait_agent joins", failures)
    if executed.get("list_agents", 0) != 0:
        fail("native cooperative session used list_agents polling", failures)
    if executed.get("interrupt_agent", 0) != 0:
        fail("normal native cooperative session executed interrupt_agent", failures)
    if "blocked_awaiting_user_choice" in behavior["assistant_text"]:
        fail("formal capability gap still blocked the native cooperative session", failures)


def is_report_completion_serialization(event: dict[str, Any]) -> bool:
    if event.get("kind") != "file_change" or not any(
        path.endswith("report.md") for path in event.get("paths", [])
    ):
        return False
    added = [
        line[1:].strip()
        for line in str(event.get("diff") or "").splitlines()
        if line.startswith("+") and not line.startswith("+++")
    ]
    return any(
        re.fullmatch(r"ended_at:\s*(?!null\s*$).+", line)
        or re.fullmatch(r"termination:\s*(?:completed|failed|interrupted|late_completion)", line)
        for line in added
    )


def validate_host_managed_behavior(
    behavior: dict[str, Any], report: dict[str, Any], failures: list[str]
) -> None:
    executed = behavior["executed"]
    spawn_events = [
        event
        for event in behavior["executed_events"]
        if event["name"] == "spawn_agent"
    ]
    if not spawn_events:
        fail("host-managed regression requires at least one requested spawn_agent", failures)
        return

    first_spawn = min(event["call_ordinal"] for event in spawn_events)
    if not any(
        event["ordinal"] < first_spawn for event in behavior["skill_load_events"]
    ):
        fail(
            "Codex team skill must be selected and fully loaded before delegation",
            failures,
        )

    for tool, label in (
        ("wait_agent", "manual wait_agent"),
        ("list_agents", "list_agents polling"),
        ("interrupt_agent", "normal-path interrupt_agent"),
    ):
        if executed.get(tool, 0) != 0:
            fail(f"host-managed orchestration executed forbidden {label}", failures)

    messages = [
        event for event in behavior["lifecycle_events"] if event["type"] == "MESSAGE"
    ]
    terminals = [
        event
        for event in behavior["lifecycle_events"]
        if event["type"] in {"FINAL_ANSWER", "ENVIRONMENT_TERMINAL"}
    ]
    completion_events = [
        event
        for event in behavior["session_events"]
        if is_report_completion_serialization(event)
    ]

    for message in messages:
        matching = [
            event
            for event in terminals
            if event["ordinal"] > message["ordinal"]
            and (
                not event.get("author")
                or not message.get("author")
                or normalized_agent_name(event.get("author"))
                == normalized_agent_name(message.get("author"))
            )
        ]
        if not matching:
            fail(
                "nonterminal update has no later terminal delivery; invocation must remain running",
                failures,
            )
            boundary = sys.maxsize
        else:
            boundary = matching[0]["ordinal"]
        if any(
            message["ordinal"] < event["ordinal"] < boundary
            for event in completion_events
        ):
            fail(
                "report/session completion serialization occurred after a nonterminal "
                "update but before its terminal delivery",
                failures,
            )
        if any(
            message["ordinal"] < event["ordinal"] < boundary
            for event in behavior["parent_final_events"]
        ):
            fail(
                "parent final response occurred while a nonterminal child was still running",
                failures,
            )

    if len(terminals) != len(spawn_events):
        fail(
            f"all-results barrier mismatch: spawn_calls={len(spawn_events)}, "
            f"terminal_deliveries={len(terminals)}",
            failures,
        )
    if terminals:
        last_terminal_ordinal = max(event["ordinal"] for event in terminals)
        if any(event["ordinal"] < last_terminal_ordinal for event in completion_events):
            fail(
                "report/session completion serialization precedes all requested terminal deliveries",
                failures,
            )
        if not behavior["parent_final_events"]:
            fail("host-managed transcript is missing the parent final response", failures)
        elif any(
            event["ordinal"] <= last_terminal_ordinal
            for event in behavior["parent_final_events"]
        ):
            fail(
                "parent final response precedes all requested terminal deliveries",
                failures,
            )
        final_report_validations = [
            event
            for event in behavior["session_events"]
            if event.get("kind") == "command"
            and event.get("successful", True)
            and "report.md" in event.get("command", "")
            and "read_text" in event.get("command", "")
            and "assert" in event.get("command", "")
        ]
        last_completion = max(
            (event["ordinal"] for event in completion_events),
            default=last_terminal_ordinal,
        )
        first_parent_final = min(
            (
                event["ordinal"]
                for event in behavior["parent_final_events"]
                if event["ordinal"] > last_terminal_ordinal
            ),
            default=sys.maxsize,
        )
        if not any(
            last_completion < event["ordinal"] < first_parent_final
            for event in final_report_validations
        ):
            fail(
                "final read-only report validation is missing after completion "
                "serialization and before parent final",
                failures,
            )

    spawn_by_environment = {
        str(event.get("agent_id")): event
        for event in spawn_events
        if event.get("agent_id")
    }
    report_by_environment = {
        str(invocation.get("environment_invocation_id")): invocation
        for invocation in report["invocations"]
        if invocation.get("environment_invocation_id")
    }
    if not set(spawn_by_environment).issubset(report_by_environment):
        fail(
            "environment/report identity mapping does not match spawned identities",
            failures,
        )
    for environment_id, spawn in spawn_by_environment.items():
        invocation = report_by_environment.get(environment_id)
        if invocation is None:
            continue
        if normalized_agent_name(invocation.get("name")) != normalized_agent_name(
            spawn.get("task_name")
        ):
            fail(
                f"environment/report identity name mismatch for {environment_id}",
                failures,
            )
        matching_terminals = [
            event
            for event in terminals
            if normalized_agent_name(event.get("author"))
            == normalized_agent_name(spawn.get("task_name"))
        ]
        if len(matching_terminals) != 1:
            fail(
                f"environment/report identity {environment_id} does not resolve to "
                "exactly one terminal delivery",
                failures,
            )
            continue
        terminal_time = parse_time(matching_terminals[0].get("timestamp"))
        ended_at = parse_time(invocation.get("ended_at"))
        if ended_at is None or (
            terminal_time is not None and ended_at < terminal_time
        ):
            fail(
                f"report invocation {invocation.get('id')} ended before its terminal delivery",
                failures,
            )
        if invocation.get("termination") != "completed":
            fail(
                f"collected result {invocation.get('id')} is not completed",
                failures,
            )
        if not str(invocation.get("output_digest") or "").strip():
            fail(
                f"collected result {invocation.get('id')} lacks output_digest",
                failures,
            )


def validate_host_managed_ledger(
    path: Path,
    behavior: dict[str, Any],
    report: dict[str, Any],
    appendix_profile: dict[str, bool | str],
    failures: list[str],
) -> None:
    rows = load_jsonl(path)
    report_ids = {str(item.get("id")) for item in report["invocations"]}
    for index, row in enumerate(rows, 1):
        actual_fields = set(row) - {"_line"}
        if actual_fields != LEDGER_FIELDS:
            fail(
                f"ledger envelope row {index} must contain exactly six fields; "
                f"missing={sorted(LEDGER_FIELDS - actual_fields)}, "
                f"extra={sorted(actual_fields - LEDGER_FIELDS)}",
                failures,
            )
        if row.get("event") not in LEDGER_EVENTS:
            fail(f"ledger event vocabulary drift at row {index}", failures)
        if parse_time(row.get("recorded_at")) is None:
            fail(f"ledger recorded_at is invalid at row {index}", failures)
        if row.get("await_id") is not None:
            fail(f"host-managed ledger await_id must be null at row {index}", failures)
        owner = row.get("owner_report_invocation_id")
        if owner not in report_ids:
            fail(f"ledger owner {owner!r} is absent from report Invocations", failures)
        source_ref = row.get("source_ref")
        if (
            not isinstance(source_ref, str)
            or not source_ref.strip()
            or PLACEHOLDER.search(source_ref)
        ):
            fail(f"ledger source_ref is not concrete at row {index}: {source_ref!r}", failures)
        if not isinstance(row.get("details"), dict):
            fail(f"ledger details are missing at row {index}", failures)

    checked = [row for row in rows if row.get("event") == "await_capability_checked"]
    if len(checked) != 1:
        fail("await_capability_checked must occur exactly once", failures)
    else:
        details = checked[0].get("details", {})
        for key, value in appendix_profile.items():
            if details.get(key) != value:
                fail(f"capability profile drift for {key}", failures)
        if details.get("selected_mode") != "host_managed_subagent_orchestration":
            fail("managed ledger selected_mode drift", failures)

    measurements = [row for row in rows if row.get("event") == "measurement"]
    if len(measurements) != 1:
        fail("host-managed ledger requires one aggregate measurement", failures)
        return
    measurement = measurements[0]
    details = measurement.get("details", {})
    requested_ids = details.get("requested_report_invocation_ids")
    if not isinstance(requested_ids, list) or not requested_ids:
        fail("requested_report_invocation_ids are missing", failures)
        requested_id_set: set[str] = set()
    else:
        requested_id_set = {str(value) for value in requested_ids}
    spawned_report_ids = {
        str(invocation.get("id"))
        for invocation in report["invocations"]
        if str(invocation.get("environment_invocation_id"))
        in {
            str(event.get("agent_id"))
            for event in behavior["executed_events"]
            if event["name"] == "spawn_agent" and event.get("agent_id")
        }
    }
    if requested_id_set != spawned_report_ids:
        fail("requested_report_invocation_ids do not match spawned report identities", failures)
    spawn_count = behavior["executed"].get("spawn_agent", 0)
    nonterminal_count = sum(
        event["type"] == "MESSAGE" for event in behavior["lifecycle_events"]
    )
    terminal_events = [
        event
        for event in behavior["lifecycle_events"]
        if event["type"] in {"FINAL_ANSWER", "ENVIRONMENT_TERMINAL"}
    ]
    collected = sum(
        str(invocation.get("id")) in requested_id_set
        and
        invocation.get("termination") == "completed"
        and bool(str(invocation.get("output_digest") or "").strip())
        for invocation in report["invocations"]
    )
    expected = {
        "requested_agents": len(requested_id_set),
        "spawn_calls": spawn_count,
        "nonterminal_updates": nonterminal_count,
        "terminal_deliveries": len(terminal_events),
        "collected_results": collected,
        "manual_wait_calls": behavior["executed"].get("wait_agent", 0),
        "list_calls": behavior["executed"].get("list_agents", 0),
        "interrupt_calls": behavior["executed"].get("interrupt_agent", 0),
        "semantic_recovery_actions": sum(
            behavior["executed"].get(name, 0)
            for name in ("list_agents", "interrupt_agent", "followup_task", "send_message")
        ),
    }
    for field, value in expected.items():
        if details.get(field) != value:
            fail(
                f"measurement {field} drift: expected {value}, "
                f"observed {details.get(field)!r}",
                failures,
            )
    if not requested_id_set.issubset(report_ids):
        fail("requested_report_invocation_ids are absent from report identities", failures)
    for field in UNKNOWN_TELEMETRY_FIELDS:
        if field not in details or details.get(field) is not None:
            fail(f"unknown telemetry {field} must remain null", failures)

    source_ref = measurement.get("source_ref")
    match = MANAGED_EVENT_REF.fullmatch(source_ref) if isinstance(source_ref, str) else None
    if not match or match.group("session") != report.get("session_id"):
        fail("measurement source_ref does not resolve to the report session", failures)
    else:
        index = int(match.group("index"))
        if index < 1 or index > len(terminal_events):
            fail("measurement source_ref does not resolve to an actual terminal event", failures)
        else:
            terminal = terminal_events[index - 1]
            referenced_report = next(
                (
                    invocation
                    for invocation in report["invocations"]
                    if invocation.get("id") == match.group("report")
                ),
                None,
            )
            if (
                referenced_report is None
                or match.group("report") not in requested_id_set
                or str(referenced_report.get("environment_invocation_id"))
                != match.group("environment")
            ):
                fail(
                    "measurement source_ref report/environment identity mismatch",
                    failures,
                )
            elif normalized_agent_name(referenced_report.get("name")) != normalized_agent_name(
                terminal.get("author")
            ):
                fail(
                    "measurement source_ref does not identify its terminal author",
                    failures,
                )
            recorded_at = parse_time(measurement.get("recorded_at"))
            terminal_at = parse_time(terminal.get("timestamp"))
            if recorded_at is None or terminal_at is None or recorded_at < terminal_at:
                fail(
                    "measurement source_ref terminal event timestamp mismatch",
                    failures,
                )


def validate_historical(behavior: dict[str, Any], failures: list[str]) -> None:
    expected = {"spawn_agent": 1, "wait_agent": 13, "list_agents": 2}
    for name, count in expected.items():
        if behavior["executed"].get(name, 0) != count:
            fail(
                f"historical {name}: expected {count}, "
                f"observed {behavior['executed'].get(name, 0)}",
                failures,
            )
    if behavior["wait_timeouts"] != 11:
        fail(
            f"historical wait timeouts: expected 11, "
            f"observed {behavior['wait_timeouts']}",
            failures,
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--session-jsonl", required=True, type=Path)
    parser.add_argument(
        "--profile",
        required=True,
        choices=("historical-regression", "native-cooperative", "host-managed"),
    )
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--appendix", type=Path)
    parser.add_argument("--source-plugin-root", type=Path)
    parser.add_argument("--installed-plugin-root", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    failures: list[str] = []
    behavior = collect_behavior(load_jsonl(args.session_jsonl))

    if bool(args.source_plugin_root) != bool(args.installed_plugin_root):
        fail("source and installed plugin roots must be provided together", failures)
    elif args.source_plugin_root and args.installed_plugin_root:
        compare_trees(args.source_plugin_root, args.installed_plugin_root, failures)

    if args.profile == "historical-regression":
        validate_historical(behavior, failures)
    elif args.profile == "native-cooperative":
        if not args.ledger:
            fail("native-cooperative requires --ledger", failures)
        if not args.report:
            fail("native-cooperative requires --report", failures)
        if not args.appendix:
            fail("native-cooperative requires --appendix", failures)
        if args.ledger and args.report and args.appendix:
            report = parse_report(args.report, failures)
            capabilities = load_appendix_capabilities(args.appendix, failures)
            validate_native_cooperative(behavior, failures)
            validate_lifecycle(behavior, report, failures)
            validate_report_timing(behavior, report, failures)
            validate_retrospective_order(behavior, report, failures)
            validate_native_ledger(
                args.ledger, behavior, report, capabilities, failures
            )
    else:
        report: dict[str, Any] | None = None
        profile: dict[str, bool | str] | None = None
        if not args.ledger:
            fail("host-managed requires --ledger", failures)
        elif not args.ledger.is_file():
            fail(f"host-managed ledger is missing: {args.ledger}", failures)
        if not args.report:
            fail("host-managed requires --report", failures)
        elif not args.report.is_file():
            fail(f"host-managed report is missing: {args.report}", failures)
        if not args.appendix:
            fail("host-managed requires --appendix", failures)
        elif not args.appendix.is_file():
            fail(f"host-managed appendix is missing: {args.appendix}", failures)
        if args.report and args.report.is_file():
            report = parse_report(args.report, failures)
            validate_host_managed_behavior(behavior, report, failures)
            validate_host_managed_report_timing(behavior, report, failures)
            validate_retrospective_order(behavior, report, failures)
        if args.appendix and args.appendix.is_file():
            profile = load_appendix_managed_profile(args.appendix, failures)
        if args.ledger and args.ledger.is_file() and report is not None and profile is not None:
            validate_host_managed_ledger(
                args.ledger, behavior, report, profile, failures
            )

    summary = {
        "profile": args.profile,
        "session_jsonl": str(args.session_jsonl),
        "attempted": behavior["attempted"],
        "denied": behavior["denied"],
        "executed": behavior["executed"],
        "wait_timeouts": behavior["wait_timeouts"],
        "lifecycle_events": [
            {
                "type": event["type"],
                "state": event["state"],
                "author": event.get("author"),
                "timestamp": event.get("timestamp"),
                "ordinal": event["ordinal"],
            }
            for event in behavior["lifecycle_events"]
        ],
        "failures": failures,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if failures:
        print("FAIL: Codex runtime behavioral regression", file=sys.stderr)
        return 1
    print("PASS: Codex runtime behavioral regression")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
