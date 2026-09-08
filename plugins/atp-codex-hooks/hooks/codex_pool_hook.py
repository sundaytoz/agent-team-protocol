#!/usr/bin/env python3
"""Codex hook runner for ATP's hook-guarded bounded-pool candidate.

The runner intentionally uses only the Python standard library. It writes
session-isolated state under PLUGIN_DATA, never the repository or user config.
Public evidence must be derived from the sanitized event ledger; state may hold
short-lived model result text so a hook can redeliver a missed terminal result.
"""

from __future__ import annotations

import contextlib
import datetime as dt
import hashlib
import json
import os
import re
import stat
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterator


SCHEMA_VERSION = 1
MAX_RESULT_CHARS = 24_000
MAX_CACHED_RESPONSES = 512
TASK_NAME_RE = re.compile(
    r"^atp_pool_(?P<pool>[a-z0-9]{6,16})_"
    r"(?P<index>[1-9][0-9]{0,2})of(?P<total>[1-9][0-9]{0,2})_"
    r"(?P<token>[a-f0-9]{8,32})$"
)
RESULT_RE = re.compile(
    r"(?:^|\n)ATP_POOL_RESULT\s+"
    r"(?P<pool>[a-z0-9]{6,16})\s+"
    r"(?P<index>[1-9][0-9]{0,2})/(?P<total>[1-9][0-9]{0,2})\s+"
    r"(?P<token>[a-f0-9]{8,32})(?:\s|$)"
)
BIND_RE = re.compile(
    r"\bATP_POOL_BIND\s+(?P<pool>[a-z0-9]{6,16})\s+"
    r"(?P<index>[1-9][0-9]{0,2})/(?P<total>[1-9][0-9]{0,2})\s+"
    r"(?P<token>[a-f0-9]{8,32})\b"
)
DENIED_RE = re.compile(
    r"\bATP_POOL_DENIED\s+(?P<pool>[a-z0-9]{6,16})\s+"
    r"(?P<index>[1-9][0-9]{0,2})/(?P<total>[1-9][0-9]{0,2})\s+"
    r"(?P<token>[a-f0-9]{8,32})\b"
)
STEER_RE = re.compile(
    r"\bATP_POOL_STEER\s+(?P<pool>[a-z0-9]{6,16})\s+"
    r"(?P<index>[1-9][0-9]{0,2})\b"
)
CANCEL_RE = re.compile(r"\bATP_POOL_CANCEL\s+(?P<pool>[a-z0-9]{6,16})\b")
CAPACITY_TEXT = "agent thread limit reached"
UUID_RE = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
)
TASK_NAME_SEARCH_RE = re.compile(
    r"\batp_pool_[a-z0-9]{6,16}_[1-9][0-9]{0,2}of"
    r"[1-9][0-9]{0,2}_[a-f0-9]{8,32}\b"
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8", errors="replace"))


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True)


def normalized_tool_name(value: object) -> str:
    return re.sub(r"[^a-z]", "", str(value or "").lower())


def tool_kind(value: object) -> str | None:
    normalized = normalized_tool_name(value)
    if normalized == "agent":
        return "spawn"
    for suffix, kind in (
        ("updateplan", "bind"),
        ("spawnagent", "spawn"),
        ("waitagent", "wait"),
        ("sendmessage", "send"),
        ("followuptask", "followup"),
        ("interruptagent", "interrupt"),
    ):
        if normalized.endswith(suffix):
            return kind
    return None


def all_strings(value: Any) -> Iterator[str]:
    if isinstance(value, str):
        yield value
        stripped = value.strip()
        if stripped.startswith(("{", "[")):
            try:
                parsed = json.loads(stripped)
            except json.JSONDecodeError:
                return
            yield from all_strings(parsed)
    elif isinstance(value, dict):
        for item in value.values():
            yield from all_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from all_strings(item)


def flattened_text(value: Any) -> str:
    return "\n".join(all_strings(value))


def find_key(value: Any, names: set[str]) -> str | None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in names and isinstance(item, (str, int)) and str(item):
                return str(item)
        for item in value.values():
            found = find_key(item, names)
            if found:
                return found
    elif isinstance(value, list):
        for item in value:
            found = find_key(item, names)
            if found:
                return found
    elif isinstance(value, str):
        stripped = value.strip()
        if stripped.startswith(("{", "[")):
            try:
                return find_key(json.loads(stripped), names)
            except json.JSONDecodeError:
                pass
        for name in names:
            match = re.search(
                rf"[\"']?{re.escape(name)}[\"']?\s*[:=]\s*[\"'](?P<id>[^\"']+)",
                value,
            )
            if match:
                return match.group("id")
    return None


def extract_environment_identity(response: Any) -> str | None:
    keyed = find_key(
        response,
        {
            "agent_id",
            "environment_invocation_id",
            "thread_id",
            "canonical_task_name",
        },
    )
    if keyed:
        return keyed
    text = flattened_text(response)
    uuid_match = UUID_RE.search(text)
    if uuid_match:
        return uuid_match.group(0)
    task_match = TASK_NAME_SEARCH_RE.search(text)
    if task_match:
        return task_match.group(0)
    return None


def safe_session_hash(session_id: str) -> str:
    return sha256_text(session_id)[:24]


def event_identity(payload: dict[str, Any]) -> str:
    event = str(payload.get("hook_event_name", "unknown"))
    turn_id = str(payload.get("turn_id", ""))
    tool_use_id = str(payload.get("tool_use_id", ""))
    agent_id = str(payload.get("agent_id", ""))
    stop_active = str(payload.get("stop_hook_active", ""))
    prompt_hash = sha256_text(str(payload.get("prompt", "")))[:16]
    message_hash = sha256_text(str(payload.get("last_assistant_message", "")))[:16]
    material = "|".join(
        (event, turn_id, tool_use_id, agent_id, stop_active, prompt_hash, message_hash)
    )
    return f"hook-{sha256_text(material)[:24]}"


def new_state(session_hash: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "session_hash": session_hash,
        "revision": 0,
        "pools": {},
        "turn_agents": {},
        "responses": {},
        "response_order": [],
    }


def new_task(index: int) -> dict[str, Any]:
    return {
        "index": index,
        "task_name": None,
        "token": None,
        "status": "pending",
        "spawn_attempts": 0,
        "accepted_identity": None,
        "terminal_disposition": None,
        "result_body": None,
        "result_sha256": None,
        "collected": False,
        "approval_required": False,
        "approval_action_observed": False,
        "interrupt_requested": False,
    }


def new_pool(pool_id: str, total: int) -> dict[str, Any]:
    return {
        "pool_id": pool_id,
        "total": total,
        "tasks": {str(index): new_task(index) for index in range(1, total + 1)},
        "attempts": {},
        "identity_to_index": {},
        "accepted_spawns": 0,
        "capacity_denials": 0,
        "cancel_requested": False,
        "controls": [],
        "disposition": "active",
        "progress_revision": 0,
        "last_stop_progress_revision": None,
        "no_progress_stops": 0,
    }


def mark_progress(pool: dict[str, Any]) -> None:
    pool["progress_revision"] = int(pool.get("progress_revision", 0)) + 1


def active_pools(state: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        pool
        for pool in state.get("pools", {}).values()
        if pool.get("disposition") in {"active", "cancelling", "blocked"}
    ]


def task_for_identity(
    state: dict[str, Any], identity: str
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    for pool in state.get("pools", {}).values():
        index = pool.get("identity_to_index", {}).get(identity)
        if index is not None:
            return pool, pool["tasks"][str(index)]
    return None


def task_for_turn(
    state: dict[str, Any], turn_id: str
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    identity = state.get("turn_agents", {}).get(turn_id)
    if not identity:
        return None
    return task_for_identity(state, identity)


def permission_deny(reason: str) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def additional_context(event: str, context: str) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": event,
            "additionalContext": context,
        }
    }


def terminal_delta(pool: dict[str, Any]) -> dict[str, Any] | None:
    results: list[dict[str, Any]] = []
    for raw_index in sorted(pool["tasks"], key=int):
        task = pool["tasks"][raw_index]
        if task.get("terminal_disposition") and not task.get("collected"):
            results.append(
                {
                    "index": task["index"],
                    "identity": task.get("accepted_identity"),
                    "disposition": task.get("terminal_disposition"),
                    "result": task.get("result_body"),
                    "result_sha256": task.get("result_sha256"),
                }
            )
            task["collected"] = True
    if not results:
        return None
    mark_progress(pool)
    return {"pool_id": pool["pool_id"], "results": results}


def pool_counts(pool: dict[str, Any]) -> dict[str, int]:
    tasks = list(pool["tasks"].values())
    return {
        "requested": int(pool["total"]),
        "pending": sum(task["status"] == "pending" for task in tasks),
        "running": sum(task["status"] == "running" for task in tasks),
        "terminal": sum(bool(task["terminal_disposition"]) for task in tasks),
        "collected": sum(bool(task["collected"]) for task in tasks),
        "cancelled_pending": sum(
            task["status"] == "cancelled_pending" for task in tasks
        ),
    }


def pool_complete(pool: dict[str, Any]) -> bool:
    counts = pool_counts(pool)
    if pool.get("cancel_requested"):
        return counts["running"] == 0 and counts["terminal"] == counts["collected"]
    return (
        counts["requested"]
        == counts["terminal"]
        == counts["collected"]
        and counts["pending"] == 0
        and counts["running"] == 0
    )


def event_details(
    payload: dict[str, Any], state: dict[str, Any], extra: dict[str, Any] | None = None
) -> dict[str, Any]:
    details: dict[str, Any] = {
        "hook_event_name": payload.get("hook_event_name"),
        "turn_id_hash": sha256_text(str(payload.get("turn_id", "")))[:16]
        if payload.get("turn_id")
        else None,
        "tool_kind": tool_kind(payload.get("tool_name")),
        "tool_name_normalized": normalized_tool_name(payload.get("tool_name"))
        or None,
        "active_pools": len(active_pools(state)),
    }
    if extra:
        details.update(extra)
    return details


@contextlib.contextmanager
def exclusive_lock(path: Path) -> Iterator[None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("a+b")
    try:
        if os.name == "nt":
            import msvcrt

            if path.stat().st_size == 0:
                handle.write(b"0")
                handle.flush()
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        yield
    finally:
        if os.name == "nt":
            import msvcrt

            handle.seek(0)
            with contextlib.suppress(OSError):
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            with contextlib.suppress(OSError):
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()


def read_state(path: Path, session_hash: str) -> dict[str, Any]:
    if not path.exists():
        return new_state(session_hash)
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return new_state(session_hash)
    if (
        state.get("schema_version") != SCHEMA_VERSION
        or state.get("session_hash") != session_hash
    ):
        return new_state(session_hash)
    return state


def atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(prefix=".state-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=True, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_name, stat.S_IRUSR | stat.S_IWUSR)
        os.replace(temp_name, path)
    finally:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(temp_name)


def event_ledger_enabled() -> bool:
    """The append-only event ledger is maintainer diagnostics, not a runtime input.

    Nothing in this runner reads ``events.jsonl``; it exists so a release
    maintainer can derive sanitized smoke evidence. Consumers only need the
    pool to work, so the ledger stays off unless it is explicitly requested.
    """
    return os.environ.get("ATP_HOOK_EVENT_LEDGER", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def append_ledger(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(
        path,
        os.O_APPEND | os.O_CREAT | os.O_WRONLY,
        stat.S_IRUSR | stat.S_IWUSR,
    )
    try:
        with os.fdopen(descriptor, "a", encoding="utf-8") as handle:
            handle.write(compact_json(row) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        with contextlib.suppress(OSError):
            os.close(descriptor)
        raise


def marker() -> str:
    runner = Path(__file__).resolve()
    hooks = runner.with_name("hooks.json")
    runner_hash = sha256_bytes(runner.read_bytes())
    hooks_hash = sha256_bytes(hooks.read_bytes())
    return (
        f"ATP_HOOK_GUARD_READY schema={SCHEMA_VERSION} "
        f"hooks_sha256={hooks_hash} runner_sha256={runner_hash}"
    )


def handle_session_start(
    payload: dict[str, Any], state: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    capability = marker()
    return additional_context("SessionStart", capability), {
        "marker_sha256": sha256_text(capability)
    }


def handle_pre_spawn(
    payload: dict[str, Any], state: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return {}, {"candidate": False}
    task_name = str(tool_input.get("task_name", ""))
    match = TASK_NAME_RE.fullmatch(task_name)
    if not match:
        return {}, {"candidate": False}
    pool_id = match.group("pool")
    index = int(match.group("index"))
    total = int(match.group("total"))
    token = match.group("token")
    if index > total:
        return permission_deny("ATP pool task index exceeds requested total."), {
            "candidate": True,
            "pool_id": pool_id,
            "index": index,
            "blocked": True,
        }
    pool = state["pools"].get(pool_id)
    if pool is None:
        pool = new_pool(pool_id, total)
        state["pools"][pool_id] = pool
    if int(pool["total"]) != total:
        return permission_deny("ATP pool total does not match the durable manifest."), {
            "candidate": True,
            "pool_id": pool_id,
            "index": index,
            "blocked": True,
        }
    task = pool["tasks"][str(index)]
    if task.get("token") not in {None, token}:
        return permission_deny("ATP pool task token changed for an existing logical task."), {
            "candidate": True,
            "pool_id": pool_id,
            "index": index,
            "blocked": True,
        }
    pending_controls = [
        control for control in pool["controls"] if not control.get("processed")
    ]
    if pool.get("cancel_requested"):
        return permission_deny("ATP pool cancellation is active; pending dispatch is closed."), {
            "candidate": True,
            "pool_id": pool_id,
            "index": index,
            "blocked": True,
        }
    if pending_controls:
        return permission_deny(
            "ATP pool control must be applied to existing identities before refill."
        ), {
            "candidate": True,
            "pool_id": pool_id,
            "index": index,
            "blocked": True,
        }
    if task["status"] not in {"pending"}:
        return permission_deny("ATP pool logical task is already running or terminal."), {
            "candidate": True,
            "pool_id": pool_id,
            "index": index,
            "blocked": True,
        }
    tool_use_id = str(payload.get("tool_use_id", ""))
    task["task_name"] = task_name
    task["token"] = token
    task["spawn_attempts"] += 1
    pool["attempts"][tool_use_id] = {"index": index, "status": "attempted"}
    mark_progress(pool)
    return {}, {
        "candidate": True,
        "pool_id": pool_id,
        "index": index,
        "attempt": task["spawn_attempts"],
        "blocked": False,
    }


def handle_post_spawn(
    payload: dict[str, Any], state: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    tool_use_id = str(payload.get("tool_use_id", ""))
    response = payload.get("tool_response")
    for pool in state["pools"].values():
        attempt = pool["attempts"].get(tool_use_id)
        if attempt is None:
            continue
        task = pool["tasks"][str(attempt["index"])]
        if attempt["status"] != "attempted":
            return {}, {
                "candidate": True,
                "pool_id": pool["pool_id"],
                "index": task["index"],
                "attempt_status": attempt["status"],
                "already_recorded": True,
            }
        text = flattened_text(response).lower()
        if CAPACITY_TEXT in text:
            attempt["status"] = "capacity_denied"
            pool["capacity_denials"] += 1
            task["status"] = "pending"
            mark_progress(pool)
            return {}, {
                "candidate": True,
                "pool_id": pool["pool_id"],
                "index": task["index"],
                "capacity_denied": True,
            }
        identity = extract_environment_identity(response)
        if not identity:
            attempt["status"] = "unmapped_error"
            pool["disposition"] = "blocked"
            mark_progress(pool)
            return additional_context(
                "PostToolUse",
                "ATP_POOL_BLOCKED spawn response lacked a stable environment identity.",
            ), {
                "candidate": True,
                "pool_id": pool["pool_id"],
                "index": task["index"],
                "identity_mapped": False,
            }
        attempt["status"] = "accepted"
        attempt["identity"] = identity
        task["status"] = "running"
        task["accepted_identity"] = identity
        pool["identity_to_index"][identity] = task["index"]
        pool["accepted_spawns"] += 1
        mark_progress(pool)
        return {}, {
            "candidate": True,
            "pool_id": pool["pool_id"],
            "index": task["index"],
            "identity_hash": sha256_text(identity)[:16],
            "identity_mapped": True,
        }
    return {}, {"candidate": False}


def handle_subagent_start(
    payload: dict[str, Any], state: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    identity = str(payload.get("agent_id", ""))
    turn_id = str(payload.get("turn_id", ""))
    if identity and turn_id:
        state["turn_agents"][turn_id] = identity
    matched = task_for_identity(state, identity) if identity else None
    return {}, {
        "candidate": bool(matched),
        "identity_hash": sha256_text(identity)[:16] if identity else None,
        "mapped": bool(matched),
    }


def latest_attempted_entry(
    pool: dict[str, Any], index: int
) -> dict[str, Any] | None:
    for attempt in reversed(list(pool["attempts"].values())):
        if int(attempt.get("index", -1)) == index and attempt.get("status") == "attempted":
            return attempt
    return None


def handle_pre_denial(
    payload: dict[str, Any], state: dict[str, Any], marker_match: re.Match[str]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Record a parent-observed capacity denial that emitted no PostToolUse.

    Codex CLI 0.149.1 does not emit ``PostToolUse`` for a failed local function
    tool, so ``handle_post_spawn`` never sees the ``agent thread limit reached``
    response. The scheduler already observes that error authoritatively as the
    tool return value, so it re-states the fact through a hook-visible
    ``update_plan`` marker. The hook still refuses to record a denial that
    contradicts durable state, so a denial can never be synthesized for a spawn
    that was actually accepted.
    """
    pool = state["pools"].get(marker_match.group("pool"))
    index = int(marker_match.group("index"))
    if (
        not pool
        or str(index) not in pool["tasks"]
        or int(marker_match.group("total")) != int(pool["total"])
    ):
        return permission_deny(
            "ATP pool denial marker does not match the durable manifest."
        ), {"candidate": True, "denial_recorded": False}
    task = pool["tasks"][str(index)]
    if marker_match.group("token") != task.get("token"):
        return permission_deny(
            "ATP pool denial token does not match the logical task."
        ), {
            "candidate": True,
            "pool_id": pool["pool_id"],
            "index": index,
            "denial_recorded": False,
        }
    if task.get("accepted_identity") or task["status"] != "pending":
        return permission_deny(
            "ATP pool denial cannot be claimed for an accepted or terminal task."
        ), {
            "candidate": True,
            "pool_id": pool["pool_id"],
            "index": index,
            "denial_recorded": False,
        }
    attempt = latest_attempted_entry(pool, index)
    if attempt is None:
        return permission_deny(
            "ATP pool denial has no unresolved spawn attempt to attribute."
        ), {
            "candidate": True,
            "pool_id": pool["pool_id"],
            "index": index,
            "denial_recorded": False,
        }
    attempt["status"] = "capacity_denied"
    attempt["attested_by"] = "parent_marker"
    pool["capacity_denials"] += 1
    mark_progress(pool)
    context = (
        f"ATP_POOL_DENIAL_RECORDED pool={pool['pool_id']} index={index} "
        f"capacity_denials={pool['capacity_denials']}"
    )
    return additional_context("PreToolUse", context), {
        "candidate": True,
        "pool_id": pool["pool_id"],
        "index": index,
        "capacity_denied": True,
        "attested_by": "parent_marker",
        "denial_recorded": True,
    }


def handle_pre_bind(
    payload: dict[str, Any], state: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    turn_id = str(payload.get("turn_id", ""))
    identity = state.get("turn_agents", {}).get(turn_id)
    marker_match = BIND_RE.search(compact_json(payload.get("tool_input")))
    if not identity or not marker_match:
        return {}, {"candidate": False}
    pool = state["pools"].get(marker_match.group("pool"))
    index = int(marker_match.group("index"))
    if (
        not pool
        or str(index) not in pool["tasks"]
        or int(marker_match.group("total")) != int(pool["total"])
    ):
        return permission_deny("ATP pool bind marker does not match the durable manifest."), {
            "candidate": True,
            "identity_bound": False,
        }
    task = pool["tasks"][str(index)]
    if marker_match.group("token") != task.get("token"):
        return permission_deny("ATP pool bind token does not match the logical task."), {
            "candidate": True,
            "pool_id": pool["pool_id"],
            "index": index,
            "identity_bound": False,
        }
    pool["identity_to_index"][identity] = index
    task["accepted_identity"] = identity
    mark_progress(pool)
    context = (
        f"ATP_POOL_IDENTITY_BOUND pool={pool['pool_id']} index={index} "
        f"identity_sha256={sha256_text(identity)}"
    )
    return additional_context("PreToolUse", context), {
        "candidate": True,
        "pool_id": pool["pool_id"],
        "index": index,
        "identity_hash": sha256_text(identity)[:16],
        "identity_bound": True,
    }


def handle_subagent_stop(
    payload: dict[str, Any], state: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    identity = str(payload.get("agent_id", ""))
    message = str(payload.get("last_assistant_message") or "")[:MAX_RESULT_CHARS]
    matched = task_for_identity(state, identity) if identity else None
    marker_match = RESULT_RE.search(message)
    if matched is None and marker_match:
        pool = state["pools"].get(marker_match.group("pool"))
        index = int(marker_match.group("index"))
        if pool and str(index) in pool["tasks"]:
            task = pool["tasks"][str(index)]
            if task.get("token") == marker_match.group("token"):
                matched = (pool, task)
                if identity:
                    pool["identity_to_index"][identity] = index
                    task["accepted_identity"] = identity
    if matched is None:
        return {}, {"candidate": False}
    pool, task = matched
    valid_result = bool(
        marker_match
        and marker_match.group("pool") == pool["pool_id"]
        and int(marker_match.group("index")) == task["index"]
        and int(marker_match.group("total")) == int(pool["total"])
        and marker_match.group("token") == task.get("token")
    )
    disposition: str | None = None
    if task.get("interrupt_requested"):
        disposition = "interrupted"
    elif valid_result:
        disposition = "completed"
    elif task.get("approval_required") and "turn_aborted" in message.lower():
        disposition = "approval_aborted"
    if disposition is None:
        if not bool(payload.get("stop_hook_active")):
            return {
                "decision": "block",
                "reason": (
                    "Return the required terminal contract exactly once: "
                    f"ATP_POOL_RESULT {pool['pool_id']} {task['index']}/{pool['total']} "
                    f"{task.get('token')} followed by the bounded result."
                ),
            }, {
                "candidate": True,
                "pool_id": pool["pool_id"],
                "index": task["index"],
                "terminal": False,
                "continued": True,
            }
        pool["disposition"] = "blocked"
        mark_progress(pool)
        return {"systemMessage": "ATP pool child stopped without a valid terminal contract."}, {
            "candidate": True,
            "pool_id": pool["pool_id"],
            "index": task["index"],
            "terminal": False,
            "continued": False,
        }
    task["status"] = "terminal"
    task["terminal_disposition"] = disposition
    task["result_body"] = message
    task["result_sha256"] = sha256_text(message)
    task["collected"] = False
    mark_progress(pool)
    return {}, {
        "candidate": True,
        "pool_id": pool["pool_id"],
        "index": task["index"],
        "terminal": True,
        "disposition": disposition,
        "result_sha256": task["result_sha256"],
    }


def collect_all_deltas(state: dict[str, Any]) -> list[dict[str, Any]]:
    deltas: list[dict[str, Any]] = []
    for pool in active_pools(state):
        delta = terminal_delta(pool)
        if delta:
            deltas.append(delta)
    return deltas


def handle_pre_wait(
    payload: dict[str, Any], state: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    deltas = collect_all_deltas(state)
    if not deltas:
        return {}, {"candidate": bool(active_pools(state)), "terminal_delta_count": 0}
    context = "ATP_POOL_TERMINAL_DELTA " + compact_json(deltas)
    return permission_deny(context), {
        "candidate": True,
        "terminal_delta_count": sum(len(delta["results"]) for delta in deltas),
        "wait_blocked_as_redundant": True,
    }


def handle_post_wait(
    payload: dict[str, Any], state: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    response_text = flattened_text(payload.get("tool_response"))
    for pool in active_pools(state):
        for identity, index in pool["identity_to_index"].items():
            task = pool["tasks"][str(index)]
            if (
                identity in response_text
                and task.get("terminal_disposition")
                and not task.get("collected")
            ):
                task["collected"] = True
                mark_progress(pool)
    deltas = collect_all_deltas(state)
    if not deltas:
        return {}, {"candidate": bool(active_pools(state)), "terminal_delta_count": 0}
    context = "ATP_POOL_TERMINAL_DELTA " + compact_json(deltas)
    return additional_context("PostToolUse", context), {
        "candidate": True,
        "terminal_delta_count": sum(len(delta["results"]) for delta in deltas),
    }


def handle_user_prompt(
    payload: dict[str, Any], state: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    prompt = str(payload.get("prompt") or "")
    prompt_hash = sha256_text(prompt)
    cancel = CANCEL_RE.search(prompt)
    steer = STEER_RE.search(prompt)
    if cancel:
        pool = state["pools"].get(cancel.group("pool"))
        if not pool:
            return {}, {"candidate": False, "prompt_sha256": prompt_hash}
        pool["cancel_requested"] = True
        pool["disposition"] = "cancelling"
        for task in pool["tasks"].values():
            if task["status"] == "pending":
                task["status"] = "cancelled_pending"
        pool["controls"].append(
            {"type": "cancel", "prompt_sha256": prompt_hash, "processed": False}
        )
        mark_progress(pool)
        context = (
            f"ATP_POOL_CONTROL_DELIVERED type=cancel pool={pool['pool_id']} "
            f"prompt_sha256={prompt_hash}. Stop pending dispatch and interrupt only "
            "the pool's current running identities; do not synthesize terminal state."
        )
        return additional_context("UserPromptSubmit", context), {
            "candidate": True,
            "pool_id": pool["pool_id"],
            "control": "cancel",
            "prompt_sha256": prompt_hash,
        }
    if steer:
        pool = state["pools"].get(steer.group("pool"))
        index = int(steer.group("index"))
        if not pool or str(index) not in pool["tasks"]:
            return {}, {"candidate": False, "prompt_sha256": prompt_hash}
        pool["controls"].append(
            {
                "type": "steer",
                "target_index": index,
                "prompt_sha256": prompt_hash,
                "processed": False,
            }
        )
        mark_progress(pool)
        context = (
            f"ATP_POOL_CONTROL_DELIVERED type=steer pool={pool['pool_id']} "
            f"target_index={index} prompt_sha256={prompt_hash}. Apply this control "
            "to the existing target identity before any pending refill."
        )
        return additional_context("UserPromptSubmit", context), {
            "candidate": True,
            "pool_id": pool["pool_id"],
            "control": "steer",
            "target_index": index,
            "prompt_sha256": prompt_hash,
        }
    return {}, {"candidate": bool(active_pools(state)), "prompt_sha256": prompt_hash}


def handle_permission_request(
    payload: dict[str, Any], state: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    turn_id = str(payload.get("turn_id", ""))
    matched = task_for_turn(state, turn_id)
    if not matched:
        return {}, {"candidate": False}
    pool, task = matched
    task["approval_required"] = True
    mark_progress(pool)
    return {}, {
        "candidate": True,
        "pool_id": pool["pool_id"],
        "index": task["index"],
        "approval_required": True,
        "tool_input_sha256": sha256_text(compact_json(payload.get("tool_input")))
        if payload.get("tool_input") is not None
        else None,
        "decision": None,
    }


def handle_pre_control(
    payload: dict[str, Any], state: dict[str, Any], kind: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    target = find_key(
        payload.get("tool_input"), {"target", "agent_id", "task_name", "environment_id"}
    )
    matched = task_for_identity(state, target) if target else None
    return {}, {
        "candidate": bool(matched or active_pools(state)),
        "control_tool": kind,
        "target_identity_hash": sha256_text(target)[:16] if target else None,
    }


def response_failed(response: Any) -> bool:
    if isinstance(response, dict) and response.get("isError") is True:
        return True
    text = flattened_text(response).lower()
    return any(marker in text for marker in ("error", "failed", "not found"))


def handle_post_control(
    payload: dict[str, Any], state: dict[str, Any], kind: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    target = find_key(
        payload.get("tool_input"), {"target", "agent_id", "task_name", "environment_id"}
    )
    matched = task_for_identity(state, target) if target else None
    success = not response_failed(payload.get("tool_response"))
    if kind in {"send", "followup"} and success:
        for pool in active_pools(state):
            for control in pool["controls"]:
                if control.get("type") != "steer" or control.get("processed"):
                    continue
                target_task = pool["tasks"][str(control["target_index"])]
                if target is None or target_task.get("accepted_identity") == target:
                    control["processed"] = True
                    control["applied_by"] = kind
                    mark_progress(pool)
                    break
    if kind == "interrupt" and success:
        if matched:
            pool, task = matched
            task["interrupt_requested"] = True
            mark_progress(pool)
        for pool in active_pools(state):
            running = [task for task in pool["tasks"].values() if task["status"] == "running"]
            if pool.get("cancel_requested") and running and all(
                task.get("interrupt_requested") for task in running
            ):
                for control in pool["controls"]:
                    if control.get("type") == "cancel" and not control.get("processed"):
                        control["processed"] = True
                        control["applied_by"] = "interrupt"
                mark_progress(pool)
    return {}, {
        "candidate": bool(matched or active_pools(state)),
        "control_tool": kind,
        "success": success,
        "target_identity_hash": sha256_text(target)[:16] if target else None,
    }


def handle_other_post_tool(
    payload: dict[str, Any], state: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    turn_id = str(payload.get("turn_id", ""))
    matched = task_for_turn(state, turn_id)
    if matched:
        pool, task = matched
        if task.get("approval_required"):
            task["approval_action_observed"] = True
            mark_progress(pool)
            return {}, {
                "candidate": True,
                "pool_id": pool["pool_id"],
                "index": task["index"],
                "approval_action_observed": True,
            }
    return {}, {"candidate": False}


def handle_stop(
    payload: dict[str, Any], state: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    pools = active_pools(state)
    if not pools:
        return {}, {"candidate": False}
    deltas = collect_all_deltas(state)
    incomplete: list[dict[str, Any]] = []
    for pool in pools:
        if pool_complete(pool):
            pool["disposition"] = "cancelled" if pool.get("cancel_requested") else "completed"
            mark_progress(pool)
            continue
        counts = pool_counts(pool)
        progress = int(pool.get("progress_revision", 0))
        if pool.get("last_stop_progress_revision") == progress:
            pool["no_progress_stops"] = int(pool.get("no_progress_stops", 0)) + 1
        else:
            pool["no_progress_stops"] = 0
            pool["last_stop_progress_revision"] = progress
        incomplete.append(
            {
                "pool_id": pool["pool_id"],
                "counts": counts,
                "cancel_requested": bool(pool.get("cancel_requested")),
                "unprocessed_controls": sum(
                    not control.get("processed") for control in pool["controls"]
                ),
                "no_progress_stops": pool["no_progress_stops"],
            }
        )
    if not incomplete:
        return {}, {
            "candidate": True,
            "complete": True,
            "terminal_delta_count": sum(len(delta["results"]) for delta in deltas),
        }
    if any(item["no_progress_stops"] >= 2 for item in incomplete):
        for item in incomplete:
            state["pools"][item["pool_id"]]["disposition"] = "blocked"
        reason = "ATP_POOL_BLOCKED no event-driven progress; supported completion is not claimed."
        return {
            "continue": False,
            "stopReason": reason,
            "systemMessage": reason,
        }, {
            "candidate": True,
            "complete": False,
            "bounded_block": True,
            "pools": incomplete,
        }
    reason_payload = {"pools": incomplete, "terminal_deltas": deltas}
    reason = (
        "ATP_POOL_CONTINUE "
        + compact_json(reason_payload)
        + " Apply delivered control before refill. Refill only after terminal release; "
        "if running remains, perform one pool wait. Do not finalize."
    )
    return {"decision": "block", "reason": reason}, {
        "candidate": True,
        "complete": False,
        "bounded_block": False,
        "pools": incomplete,
        "terminal_delta_count": sum(len(delta["results"]) for delta in deltas),
    }


def dispatch(
    payload: dict[str, Any], state: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    event = str(payload.get("hook_event_name", ""))
    kind = tool_kind(payload.get("tool_name"))
    if event == "SessionStart":
        return handle_session_start(payload, state)
    if event == "SubagentStart":
        return handle_subagent_start(payload, state)
    if event == "SubagentStop":
        return handle_subagent_stop(payload, state)
    if event == "UserPromptSubmit":
        return handle_user_prompt(payload, state)
    if event == "PermissionRequest":
        return handle_permission_request(payload, state)
    if event == "Stop":
        return handle_stop(payload, state)
    if event == "PreToolUse":
        if kind == "bind":
            denial = DENIED_RE.search(compact_json(payload.get("tool_input")))
            if denial:
                return handle_pre_denial(payload, state, denial)
            return handle_pre_bind(payload, state)
        if kind == "spawn":
            return handle_pre_spawn(payload, state)
        if kind == "wait":
            return handle_pre_wait(payload, state)
        if kind in {"send", "followup", "interrupt"}:
            return handle_pre_control(payload, state, kind)
        return {}, {"candidate": False}
    if event == "PostToolUse":
        if kind == "bind":
            return handle_other_post_tool(payload, state)
        if kind == "spawn":
            return handle_post_spawn(payload, state)
        if kind == "wait":
            return handle_post_wait(payload, state)
        if kind in {"send", "followup", "interrupt"}:
            return handle_post_control(payload, state, kind)
        return handle_other_post_tool(payload, state)
    return {}, {"candidate": False}


def may_open_pool_or_respond(payload: dict[str, Any]) -> bool:
    """Whether this event can matter when no durable state exists yet.

    Only `SessionStart` (which returns the capability marker) and a spawn whose
    `task_name` is a pool task can create the first state file. Everything else
    is a no-op in a session that never opened a pool, so it must not create
    directories, take a lock, or write anything.
    """
    event = str(payload.get("hook_event_name", ""))
    if event == "SessionStart":
        return True
    if event != "PreToolUse" or tool_kind(payload.get("tool_name")) != "spawn":
        return False
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return False
    return bool(TASK_NAME_RE.fullmatch(str(tool_input.get("task_name", ""))))


def process(payload: dict[str, Any], plugin_data: Path) -> dict[str, Any]:
    session_id = str(payload.get("session_id", ""))
    if not session_id:
        return {}
    session_hash = safe_session_hash(session_id)
    root = plugin_data / "hook_guarded_pool" / f"v{SCHEMA_VERSION}" / session_hash
    state_path = root / "state.json"
    ledger_path = root / "events.jsonl"
    lock_path = root / "state.lock"
    if not state_path.exists() and not may_open_pool_or_respond(payload):
        return {}
    event_id = event_identity(payload)
    with exclusive_lock(lock_path):
        state = read_state(state_path, session_hash)
        cached = state.get("responses", {}).get(event_id)
        if isinstance(cached, dict):
            return cached
        had_pools = bool(state.get("pools"))
        response, extra = dispatch(payload, state)
        if not response and not had_pools and not state.get("pools"):
            # No ATP pool has ever existed in this session and this event did
            # not start one, so there is nothing to persist. Consumers running
            # with team execution disabled never open a pool, which keeps the
            # hook free of disk writes on unrelated tool calls.
            return {}
        state["revision"] = int(state.get("revision", 0)) + 1
        state.setdefault("responses", {})[event_id] = response
        order = state.setdefault("response_order", [])
        order.append(event_id)
        while len(order) > MAX_CACHED_RESPONSES:
            expired = order.pop(0)
            state["responses"].pop(expired, None)
        atomic_write_json(state_path, state)
        if not event_ledger_enabled():
            return response
        append_ledger(
            ledger_path,
            {
                "event_id": event_id,
                "recorded_at": utc_now(),
                "session_hash": session_hash,
                "event": str(payload.get("hook_event_name", "unknown")),
                "details": event_details(payload, state, extra),
            },
        )
        return response


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return 0
    if not isinstance(payload, dict):
        return 0
    plugin_data_raw = os.environ.get("PLUGIN_DATA") or os.environ.get(
        "CLAUDE_PLUGIN_DATA"
    )
    if not plugin_data_raw:
        return 0
    try:
        plugin_data = Path(plugin_data_raw).expanduser().resolve()
        plugin_data.mkdir(parents=True, exist_ok=True)
        response = process(payload, plugin_data)
    except Exception as exc:  # Fail closed through marker absence, not hook crashes.
        print(f"ATP hook candidate unavailable: {type(exc).__name__}", file=sys.stderr)
        return 0
    if response:
        sys.stdout.write(compact_json(response))
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
