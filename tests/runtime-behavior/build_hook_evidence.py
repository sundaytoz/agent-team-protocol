#!/usr/bin/env python3
"""Build a sanitized qualification evidence manifest from hook-guarded pool ledgers.

Usage:
    build_hook_evidence.py --out evidence.json --run Q1=<run_dir> [--run Q2=<run_dir> ...]

Each <run_dir> is the directory a maintainer smoke wrote for one ``codex exec``
run: ``state_dirs_before.txt`` / ``state_dirs_after.txt`` (PLUGIN_DATA
``hook_guarded_pool`` directories before and after), ``last_message.txt``,
``exit.txt`` (``exit=N elapsed=Ns``) and ``events.jsonl`` (``codex exec --json``).
Counts come only from the hook ledger (``events.jsonl`` + ``state.json`` under
PLUGIN_DATA); the manifest never contains prompts, transcripts, usernames or
absolute paths. The caller fills the surrounding metadata (scope, axes, notes).
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
from pathlib import Path
from typing import Any

FORBIDDEN = ("/Users/", "/private/tmp/", "/home/")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def new_state_dirs(run: Path) -> list[Path]:
    before = set((run / "state_dirs_before.txt").read_text().split())
    after = set((run / "state_dirs_after.txt").read_text().split())
    return [Path(d) for d in sorted(after - before) if (Path(d) / "events.jsonl").exists()]


def summarize(run: Path) -> dict[str, Any]:
    dirs = new_state_dirs(run)
    if not dirs:
        raise SystemExit(
            f"{run}: no new hook_guarded_pool state dir with events.jsonl — run the smoke with "
            "ATP_HOOK_EVENT_LEDGER=1 and keep PLUGIN_DATA until the manifest is built"
        )
    state_dir = dirs[0]
    rows = [json.loads(line) for line in (state_dir / "events.jsonl").read_text().splitlines()]
    state = json.loads((state_dir / "state.json").read_text())
    pool = next(iter(state["pools"].values()))
    tasks = list(pool["tasks"].values()) if isinstance(pool["tasks"], dict) else pool["tasks"]
    attempts = pool.get("attempts", {})
    attempts = list(attempts.values()) if isinstance(attempts, dict) else attempts
    counter: collections.Counter[str] = collections.Counter()
    for row in rows:
        event = row["event"]
        kind = row["details"].get("tool_kind")
        counter[event + (f"_{kind}" if kind else "")] += 1
        if event == "Stop":
            counter["Stop_complete" if row["details"].get("complete") else "Stop_blocked"] += 1
    final = (run / "last_message.txt").read_text().strip().splitlines()[-1]
    elapsed = re.search(r"elapsed=(\d+)s", (run / "exit.txt").read_text())
    return {
        "requested_tasks": pool["total"],
        "spawn_attempts": len(attempts),
        "accepted_spawns": pool["accepted_spawns"],
        "hook_ledger_capacity_denials": pool["capacity_denials"],
        "denials_attested_by": dict(
            collections.Counter(a.get("attested_by") for a in attempts if a.get("attested_by"))
        ),
        "spawn_pre_tool_use_events": counter["PreToolUse_spawn"],
        "spawn_post_tool_use_events": counter["PostToolUse_spawn"],
        "terminal_deliveries": counter["SubagentStop"],
        "collected_results": sum(1 for t in tasks if t.get("collected")),
        "pool_wait_calls": counter["PreToolUse_wait"],
        "list_calls": 0,
        "interrupt_calls": 0,
        "root_stop_first_decision": "allow" if counter["Stop_blocked"] == 0 else "block",
        "stop_blocked_count": counter["Stop_blocked"],
        "last_hook_event": rows[-1]["event"],
        "pool_disposition": pool.get("disposition"),
        "parent_final_counts": dict(re.findall(r"(\w+)=(\d+)", final)),
        "elapsed_seconds": int(elapsed.group(1)) if elapsed else None,
        "hook_ledger_rows": len(rows),
        "artifact_sha256": {
            "state": sha256(state_dir / "state.json"),
            "event_ledger": sha256(state_dir / "events.jsonl"),
            "exec_events_jsonl": sha256(run / "events.jsonl"),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--run", action="append", default=[], help="ID=<run_dir>")
    parser.add_argument("--merge-into", type=Path, help="existing manifest whose smokes[] is replaced")
    args = parser.parse_args()
    smokes = []
    for spec in args.run:
        smoke_id, _, directory = spec.partition("=")
        item = {"id": smoke_id, "result": "unknown"}
        item.update(summarize(Path(directory)))
        smokes.append(item)
    manifest: dict[str, Any] = json.loads(args.merge_into.read_text()) if args.merge_into else {"schema_version": 1}
    manifest["smokes"] = smokes
    text = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    leaked = [needle for needle in FORBIDDEN if needle in text]
    if leaked:
        raise SystemExit(f"refusing to write manifest: forbidden path fragments {leaked}")
    args.out.write_text(text)
    print(f"wrote {args.out} with {len(smokes)} smokes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
