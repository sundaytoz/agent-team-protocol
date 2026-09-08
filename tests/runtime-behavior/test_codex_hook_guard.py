#!/usr/bin/env python3
"""Deterministic fixtures for the Codex hook-guarded pool candidate."""

from __future__ import annotations

import concurrent.futures
import hashlib
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
PLUGIN = ROOT / "plugins/atp"
ADDON = ROOT / "plugins/atp-codex-hooks"
RUNNER = ADDON / "hooks/codex_pool_hook.py"
HOOKS = ADDON / "hooks/hooks.json"
SKILL = PLUGIN / "skills/codex-team/SKILL.md"
MARKETPLACES = (
    ROOT / ".claude-plugin/marketplace.json",
    ROOT / ".codex-plugin/marketplace.json",
    ROOT / ".agents/plugins/marketplace.json",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class HookHarness:
    def __init__(
        self,
        root: Path,
        session: str = "fixture-hook-session",
        ledger_mode: str = "1",
    ) -> None:
        self.root = root
        self.session = session
        self.ledger_mode = ledger_mode

    def call(self, **payload: Any) -> dict[str, Any]:
        event = {"session_id": self.session, **payload}
        env = os.environ.copy()
        env["PLUGIN_DATA"] = str(self.root)
        env["PLUGIN_ROOT"] = str(ADDON)
        # The event ledger is maintainer diagnostics and ships disabled; the
        # fixtures assert on it, so they opt in the same way a smoke does.
        env.setdefault("ATP_HOOK_EVENT_LEDGER", self.ledger_mode)
        result = subprocess.run(
            ["python3", str(RUNNER)],
            input=json.dumps(event),
            text=True,
            capture_output=True,
            check=False,
            env=env,
            cwd=ROOT,
        )
        if result.returncode != 0 or result.stderr:
            raise AssertionError(result.stdout + result.stderr)
        return json.loads(result.stdout) if result.stdout.strip() else {}

    def state_dir(self) -> Path:
        session_hash = hashlib.sha256(self.session.encode()).hexdigest()[:24]
        return self.root / "hook_guarded_pool/v1" / session_hash

    def state(self) -> dict[str, Any]:
        return json.loads((self.state_dir() / "state.json").read_text())

    def ledger(self) -> list[dict[str, Any]]:
        return [
            json.loads(line)
            for line in (self.state_dir() / "events.jsonl").read_text().splitlines()
        ]

    @staticmethod
    def task(pool: str, index: int, total: int, token: str) -> str:
        return f"atp_pool_{pool}_{index}of{total}_{token}"

    def pre_spawn(
        self, task_name: str, tool_use_id: str, turn_id: str = "root-turn"
    ) -> dict[str, Any]:
        return self.call(
            hook_event_name="PreToolUse",
            turn_id=turn_id,
            tool_name="collaborationspawn_agent",
            tool_use_id=tool_use_id,
            tool_input={"task_name": task_name, "message": "encrypted"},
        )

    def post_spawn(
        self,
        task_name: str,
        tool_use_id: str,
        identity: str | None = None,
        response: Any | None = None,
    ) -> dict[str, Any]:
        return self.call(
            hook_event_name="PostToolUse",
            turn_id="root-turn",
            tool_name="collaborationspawn_agent",
            tool_use_id=tool_use_id,
            tool_input={"task_name": task_name, "message": "encrypted"},
            tool_response=response
            if response is not None
            else {"agent_id": identity, "canonical_task_name": task_name},
        )

    def plan_marker(self, step: str, turn_id: str = "root-turn") -> dict[str, Any]:
        self.plan_calls = getattr(self, "plan_calls", 0) + 1
        return self.call(
            hook_event_name="PreToolUse",
            turn_id=turn_id,
            tool_name="update_plan",
            tool_use_id=f"plan-{self.plan_calls}",
            tool_input={"plan": [{"status": "completed", "step": step}]},
        )

    def terminal(
        self,
        pool: str,
        index: int,
        total: int,
        token: str,
        identity: str,
        *,
        body: str = "done",
        stop_hook_active: bool = False,
    ) -> dict[str, Any]:
        return self.call(
            hook_event_name="SubagentStop",
            turn_id=f"child-turn-{index}",
            agent_id=identity,
            agent_type="default",
            stop_hook_active=stop_hook_active,
            last_assistant_message=(
                f"ATP_POOL_RESULT {pool} {index}/{total} {token}\n{body}"
            ),
        )


class CodexHookGuardTests(unittest.TestCase):
    maxDiff = None

    def test_session_marker_matches_exact_source_hashes_and_skill_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            harness = HookHarness(Path(directory))
            response = harness.call(
                hook_event_name="SessionStart",
                source="startup",
                permission_mode="default",
            )
        marker = response["hookSpecificOutput"]["additionalContext"]
        expected = (
            "ATP_HOOK_GUARD_READY schema=1 "
            f"hooks_sha256={digest(HOOKS)} runner_sha256={digest(RUNNER)}"
        )
        self.assertEqual(expected, marker)
        skill = SKILL.read_text(encoding="utf-8")
        self.assertIn(expected, skill)
        self.assertIn("child spawn은 0", skill)
        manifest = json.loads((PLUGIN / ".codex-plugin/plugin.json").read_text())
        self.assertNotIn("hooks", manifest)

    def test_base_bundle_ships_no_hooks(self) -> None:
        """Only the opt-in add-on may carry the hook; a base-only Codex install
        must never surface the "Hooks need review" trust prompt."""
        self.assertFalse(
            (PLUGIN / "hooks").exists(),
            "the base bundle must not contain a hooks/ directory (add-on only)",
        )
        for manifest_path in (
            PLUGIN / ".claude-plugin/plugin.json",
            PLUGIN / ".codex-plugin/plugin.json",
        ):
            manifest = json.loads(manifest_path.read_text())
            self.assertNotIn("hooks", manifest, manifest_path.name)
        self.assertTrue(HOOKS.is_file())
        self.assertTrue(RUNNER.is_file())
        self.assertIn("atp-codex-hooks", SKILL.read_text(encoding="utf-8"))

    def test_addon_manifests_and_marketplaces_are_consistent(self) -> None:
        claude = json.loads((ADDON / ".claude-plugin/plugin.json").read_text())
        codex = json.loads((ADDON / ".codex-plugin/plugin.json").read_text())
        self.assertEqual("atp-codex-hooks", claude["name"])
        self.assertEqual(claude["name"], codex["name"])
        self.assertEqual(claude["version"], codex["version"])
        self.assertEqual(["atp"], claude["dependencies"])
        self.assertEqual(["atp"], codex["dependencies"])
        for marketplace in MARKETPLACES:
            plugins = json.loads(marketplace.read_text())["plugins"]
            entry = next(
                (item for item in plugins if item["name"] == "atp-codex-hooks"), None
            )
            self.assertIsNotNone(entry, f"{marketplace} must list atp-codex-hooks")
            source = entry["source"]
            path = source["path"] if isinstance(source, dict) else source
            self.assertEqual("./plugins/atp-codex-hooks", path, str(marketplace))

    def test_terminal_delta_refills_and_root_stop_opens_only_when_complete(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            harness = HookHarness(Path(directory))
            pool, total = "abc123", 3
            names = [
                harness.task(pool, index, total, f"0000000{index}")
                for index in range(1, total + 1)
            ]
            self.assertEqual({}, harness.pre_spawn(names[0], "spawn-1"))
            harness.post_spawn(names[0], "spawn-1", "agent-1")
            blocked = harness.call(
                hook_event_name="Stop",
                turn_id="root-turn",
                stop_hook_active=False,
                last_assistant_message="early final",
            )
            self.assertEqual("block", blocked["decision"])
            self.assertIn('"pending":2', blocked["reason"])

            harness.terminal(pool, 1, total, "00000001", "agent-1")
            delta = harness.call(
                hook_event_name="PreToolUse",
                turn_id="root-turn",
                tool_name="collaborationwait_agent",
                tool_use_id="wait-1",
                tool_input={},
            )
            reason = delta["hookSpecificOutput"]["permissionDecisionReason"]
            self.assertIn("ATP_POOL_TERMINAL_DELTA", reason)
            self.assertIn("agent-1", reason)

            for index in (2, 3):
                self.assertEqual({}, harness.pre_spawn(names[index - 1], f"spawn-{index}"))
                harness.post_spawn(
                    names[index - 1], f"spawn-{index}", f"agent-{index}"
                )
                harness.terminal(
                    pool,
                    index,
                    total,
                    f"0000000{index}",
                    f"agent-{index}",
                )
            post_wait = harness.call(
                hook_event_name="PostToolUse",
                turn_id="root-turn",
                tool_name="collaborationwait_agent",
                tool_use_id="wait-2",
                tool_input={},
                tool_response={"status": "completed"},
            )
            self.assertIn(
                "ATP_POOL_TERMINAL_DELTA",
                post_wait["hookSpecificOutput"]["additionalContext"],
            )
            allowed = harness.call(
                hook_event_name="Stop",
                turn_id="root-turn",
                stop_hook_active=True,
                last_assistant_message="final after three",
            )
            self.assertEqual({}, allowed)
            state = harness.state()["pools"][pool]
            self.assertEqual("completed", state["disposition"])
            self.assertEqual(
                {"requested": 3, "pending": 0, "running": 0, "terminal": 3, "collected": 3, "cancelled_pending": 0},
                {
                    "requested": state["total"],
                    "pending": sum(t["status"] == "pending" for t in state["tasks"].values()),
                    "running": sum(t["status"] == "running" for t in state["tasks"].values()),
                    "terminal": sum(bool(t["terminal_disposition"]) for t in state["tasks"].values()),
                    "collected": sum(bool(t["collected"]) for t in state["tasks"].values()),
                    "cancelled_pending": sum(t["status"] == "cancelled_pending" for t in state["tasks"].values()),
                },
            )

    def test_nonterminal_wait_keeps_identity_running(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            harness = HookHarness(Path(directory))
            name = harness.task("abc123", 1, 1, "00000001")
            harness.pre_spawn(name, "spawn-1")
            harness.post_spawn(name, "spawn-1", "agent-1")
            response = harness.call(
                hook_event_name="PostToolUse",
                turn_id="root-turn",
                tool_name="collaborationwait_agent",
                tool_use_id="wait-message",
                tool_input={},
                tool_response={"message_type": "MESSAGE", "agent_id": "agent-1"},
            )
            self.assertEqual({}, response)
            task = harness.state()["pools"]["abc123"]["tasks"]["1"]
            self.assertEqual("running", task["status"])
            self.assertIsNone(task["terminal_disposition"])

    def test_capacity_denial_returns_task_to_pending_then_accepts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            harness = HookHarness(Path(directory))
            name = harness.task("abc123", 1, 1, "00000001")
            harness.pre_spawn(name, "spawn-denied")
            harness.post_spawn(
                name,
                "spawn-denied",
                response={"isError": True, "message": "agent thread limit reached"},
            )
            task = harness.state()["pools"]["abc123"]["tasks"]["1"]
            self.assertEqual("pending", task["status"])
            harness.pre_spawn(name, "spawn-accepted")
            harness.post_spawn(name, "spawn-accepted", "agent-new")
            pool = harness.state()["pools"]["abc123"]
            self.assertEqual(2, pool["tasks"]["1"]["spawn_attempts"])
            self.assertEqual(1, pool["capacity_denials"])
            self.assertEqual(1, pool["accepted_spawns"])
            self.assertEqual("agent-new", pool["tasks"]["1"]["accepted_identity"])

    def test_consumer_session_without_a_pool_writes_nothing(self) -> None:
        """A consumer with team execution disabled never opens a pool.

        The hook must not turn every matched tool call into a state rewrite and
        a ledger append for people who get no feature out of it.
        """
        with tempfile.TemporaryDirectory() as directory:
            harness = HookHarness(Path(directory))
            for i in range(5):
                harness.call(
                    hook_event_name="PostToolUse",
                    turn_id="root-turn",
                    tool_name="update_plan",
                    tool_use_id=f"unrelated-{i}",
                    tool_input={"plan": [{"status": "completed", "step": "unrelated work"}]},
                    tool_response="ok",
                )
                harness.call(
                    hook_event_name="PreToolUse",
                    turn_id="root-turn",
                    tool_name="collaborationwait_agent",
                    tool_use_id=f"unrelated-wait-{i}",
                    tool_input={"timeout_ms": 1000},
                )
            self.assertFalse(
                (harness.state_dir() / "state.json").exists(),
                "no pool existed, so no durable state should have been written",
            )
            self.assertFalse(
                (harness.state_dir() / "events.jsonl").exists(),
                "no pool existed, so no ledger rows should have been appended",
            )

    def test_event_ledger_is_off_unless_explicitly_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            harness = HookHarness(Path(directory), ledger_mode="")
            name = harness.task("abc123", 1, 1, "00000001")
            harness.pre_spawn(name, "spawn-1")
            harness.post_spawn(name, "spawn-1", "agent-1")
            # Functional state is still durable — the pool cannot work without it.
            pool = harness.state()["pools"]["abc123"]
            self.assertEqual(1, pool["accepted_spawns"])
            self.assertEqual("agent-1", pool["tasks"]["1"]["accepted_identity"])
            # Diagnostics are not.
            self.assertFalse(
                (harness.state_dir() / "events.jsonl").exists(),
                "the event ledger is maintainer diagnostics and must stay opt-in",
            )

    def test_unrelated_tools_are_not_matched_by_the_hook_config(self) -> None:
        config = json.loads(HOOKS.read_text())
        for event, entries in config["hooks"].items():
            for entry in entries:
                matcher = entry.get("matcher", "")
                for tool in ("Bash", "apply_patch"):
                    self.assertNotIn(
                        tool,
                        matcher,
                        f"{event} must not invoke the runner on unrelated {tool} calls",
                    )

    def test_parent_marker_records_denial_when_post_tool_use_is_missing(self) -> None:
        """Codex 0.149.1 emits no PostToolUse for a failed spawn_agent call."""
        with tempfile.TemporaryDirectory() as directory:
            harness = HookHarness(Path(directory))
            name = harness.task("abc123", 1, 1, "00000001")
            harness.pre_spawn(name, "spawn-denied")
            response = harness.plan_marker("ATP_POOL_DENIED abc123 1/1 00000001")
            context = response["hookSpecificOutput"]["additionalContext"]
            self.assertIn("ATP_POOL_DENIAL_RECORDED", context)
            pool = harness.state()["pools"]["abc123"]
            self.assertEqual(1, pool["capacity_denials"])
            self.assertEqual("pending", pool["tasks"]["1"]["status"])
            self.assertEqual(
                "capacity_denied", pool["attempts"]["spawn-denied"]["status"]
            )
            self.assertEqual(
                "parent_marker", pool["attempts"]["spawn-denied"]["attested_by"]
            )
            harness.pre_spawn(name, "spawn-accepted")
            harness.post_spawn(name, "spawn-accepted", "agent-new")
            pool = harness.state()["pools"]["abc123"]
            self.assertEqual(2, pool["tasks"]["1"]["spawn_attempts"])
            self.assertEqual(1, pool["capacity_denials"])
            self.assertEqual(1, pool["accepted_spawns"])

    def test_denial_marker_is_refused_for_accepted_or_unattempted_task(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            harness = HookHarness(Path(directory))
            name = harness.task("abc123", 1, 1, "00000001")
            # no spawn attempt at all
            harness.pre_spawn(name, "spawn-1")
            harness.post_spawn(name, "spawn-1", "agent-1")
            refused = harness.plan_marker("ATP_POOL_DENIED abc123 1/1 00000001")
            self.assertEqual(
                "deny",
                refused["hookSpecificOutput"]["permissionDecision"],
            )
            self.assertEqual(0, harness.state()["pools"]["abc123"]["capacity_denials"])

    def test_denial_marker_rejects_wrong_token_and_duplicate_claim(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            harness = HookHarness(Path(directory))
            name = harness.task("abc123", 1, 1, "00000001")
            harness.pre_spawn(name, "spawn-denied")
            wrong = harness.plan_marker("ATP_POOL_DENIED abc123 1/1 deadbeef")
            self.assertEqual("deny", wrong["hookSpecificOutput"]["permissionDecision"])
            self.assertEqual(0, harness.state()["pools"]["abc123"]["capacity_denials"])
            harness.plan_marker("ATP_POOL_DENIED abc123 1/1 00000001")
            self.assertEqual(1, harness.state()["pools"]["abc123"]["capacity_denials"])
            duplicate = harness.plan_marker("ATP_POOL_DENIED abc123 1/1 00000001")
            self.assertEqual(
                "deny", duplicate["hookSpecificOutput"]["permissionDecision"]
            )
            self.assertEqual(1, harness.state()["pools"]["abc123"]["capacity_denials"])

    def test_post_tool_use_does_not_double_count_marker_denial(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            harness = HookHarness(Path(directory))
            name = harness.task("abc123", 1, 1, "00000001")
            harness.pre_spawn(name, "spawn-denied")
            harness.plan_marker("ATP_POOL_DENIED abc123 1/1 00000001")
            harness.post_spawn(
                name,
                "spawn-denied",
                response={"isError": True, "message": "agent thread limit reached"},
            )
            pool = harness.state()["pools"]["abc123"]
            self.assertEqual(1, pool["capacity_denials"])
            self.assertEqual("pending", pool["tasks"]["1"]["status"])

    def test_capacity_denial_post_tool_agent_alias_is_counted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            harness = HookHarness(Path(directory))
            name = harness.task("abc123", 1, 1, "00000001")
            harness.pre_spawn(name, "spawn-alias")
            harness.call(
                hook_event_name="PostToolUse",
                turn_id="root-turn",
                tool_name="Agent",
                tool_use_id="spawn-alias",
                tool_input={"task_name": name, "message": "encrypted"},
                tool_response={"isError": True, "message": "agent thread limit reached"},
            )
            pool = harness.state()["pools"]["abc123"]
            self.assertEqual(1, pool["capacity_denials"])
            self.assertEqual("pending", pool["tasks"]["1"]["status"])

    def test_spawn_response_plain_text_uuid_is_a_stable_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            harness = HookHarness(Path(directory))
            name = harness.task("abc123", 1, 1, "00000001")
            harness.pre_spawn(name, "spawn-plain")
            identity = "01a04718-0a37-7280-9cf4-21a31d70e0c7"
            harness.post_spawn(
                name,
                "spawn-plain",
                response=f"Spawned {name} with agent id {identity}",
            )
            task = harness.state()["pools"]["abc123"]["tasks"]["1"]
            self.assertEqual(identity, task["accepted_identity"])
            self.assertEqual("running", task["status"])

    def test_invalid_terminal_continues_same_child_once(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            harness = HookHarness(Path(directory))
            name = harness.task("abc123", 1, 1, "00000001")
            harness.pre_spawn(name, "spawn-1")
            harness.post_spawn(name, "spawn-1", "agent-1")
            first = harness.call(
                hook_event_name="SubagentStop",
                turn_id="child-turn",
                agent_id="agent-1",
                agent_type="default",
                stop_hook_active=False,
                last_assistant_message="missing contract",
            )
            self.assertEqual("block", first["decision"])
            self.assertIn("ATP_POOL_RESULT abc123 1/1 00000001", first["reason"])
            second = harness.call(
                hook_event_name="SubagentStop",
                turn_id="child-turn",
                agent_id="agent-1",
                agent_type="default",
                stop_hook_active=True,
                last_assistant_message="still missing",
            )
            self.assertNotIn("decision", second)
            self.assertEqual("blocked", harness.state()["pools"]["abc123"]["disposition"])

    def test_delivered_steering_must_be_applied_before_refill(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            harness = HookHarness(Path(directory))
            first = harness.task("abc123", 1, 2, "00000001")
            second = harness.task("abc123", 2, 2, "00000002")
            harness.pre_spawn(first, "spawn-1")
            harness.post_spawn(first, "spawn-1", "agent-1")
            delivered = harness.call(
                hook_event_name="UserPromptSubmit",
                turn_id="root-turn",
                prompt="ATP_POOL_STEER abc123 1 use the revised boundary",
            )
            self.assertIn("type=steer", delivered["hookSpecificOutput"]["additionalContext"])
            denied = harness.pre_spawn(second, "spawn-2-before-control")
            self.assertEqual(
                "deny", denied["hookSpecificOutput"]["permissionDecision"]
            )
            harness.call(
                hook_event_name="PostToolUse",
                turn_id="root-turn",
                tool_name="collaborationsend_message",
                tool_use_id="send-1",
                tool_input={"target": "agent-1", "message": "encrypted"},
                tool_response={"ok": True},
            )
            self.assertEqual({}, harness.pre_spawn(second, "spawn-2-after-control"))

    def test_actual_interrupt_closes_cancelled_pool_without_refill(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            harness = HookHarness(Path(directory))
            first = harness.task("abc123", 1, 3, "00000001")
            second = harness.task("abc123", 2, 3, "00000002")
            harness.pre_spawn(first, "spawn-1")
            harness.post_spawn(first, "spawn-1", "agent-1")
            harness.call(
                hook_event_name="UserPromptSubmit",
                turn_id="root-turn",
                prompt="ATP_POOL_CANCEL abc123",
            )
            self.assertEqual(
                "deny",
                harness.pre_spawn(second, "spawn-after-cancel")["hookSpecificOutput"][
                    "permissionDecision"
                ],
            )
            harness.call(
                hook_event_name="PostToolUse",
                turn_id="root-turn",
                tool_name="collaborationinterrupt_agent",
                tool_use_id="interrupt-1",
                tool_input={"target": "agent-1"},
                tool_response={"status": "interrupted"},
            )
            harness.call(
                hook_event_name="SubagentStop",
                turn_id="child-turn-1",
                agent_id="agent-1",
                agent_type="default",
                stop_hook_active=False,
                last_assistant_message="interrupted by root",
            )
            harness.call(
                hook_event_name="PreToolUse",
                turn_id="root-turn",
                tool_name="collaborationwait_agent",
                tool_use_id="wait-cancel",
                tool_input={},
            )
            allowed = harness.call(
                hook_event_name="Stop",
                turn_id="root-turn",
                stop_hook_active=False,
                last_assistant_message="cancelled final",
            )
            self.assertEqual({}, allowed)
            pool = harness.state()["pools"]["abc123"]
            self.assertEqual("cancelled", pool["disposition"])
            self.assertEqual(1, pool["accepted_spawns"])
            self.assertEqual("interrupted", pool["tasks"]["1"]["terminal_disposition"])

    def test_permission_request_is_audited_without_automatic_decision(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            harness = HookHarness(Path(directory))
            name = harness.task("abc123", 1, 1, "00000001")
            harness.pre_spawn(name, "spawn-1")
            harness.post_spawn(
                name,
                "spawn-1",
                response="Spawned canonical task atp_pool_abc123_1of1_00000001",
            )
            harness.call(
                hook_event_name="SubagentStart",
                turn_id="child-turn",
                agent_id="agent-1",
                agent_type="default",
            )
            bound = harness.call(
                hook_event_name="PreToolUse",
                turn_id="child-turn",
                tool_name="update_plan",
                tool_use_id="bind-1",
                tool_input={
                    "plan": [
                        {
                            "step": "ATP_POOL_BIND abc123 1/1 00000001",
                            "status": "completed",
                        }
                    ]
                },
            )
            self.assertIn(
                "ATP_POOL_IDENTITY_BOUND",
                bound["hookSpecificOutput"]["additionalContext"],
            )
            response = harness.call(
                hook_event_name="PermissionRequest",
                turn_id="child-turn",
                tool_name="Bash",
                tool_input={"command": "touch harmless-marker"},
            )
            self.assertEqual({}, response)
            task = harness.state()["pools"]["abc123"]["tasks"]["1"]
            self.assertTrue(task["approval_required"])
            ledger = (harness.state_dir() / "events.jsonl").read_text()
            self.assertNotIn("touch harmless-marker", ledger)

    def test_duplicate_and_concurrent_events_are_deduplicated_and_atomic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            harness = HookHarness(root)
            names = [
                harness.task("abc123", index, 10, f"{index:08x}")
                for index in range(1, 11)
            ]

            def invoke(item: tuple[int, str]) -> dict[str, Any]:
                index, name = item
                return harness.pre_spawn(name, f"spawn-{index}")

            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                responses = list(executor.map(invoke, enumerate(names, 1)))
            self.assertTrue(all(response == {} for response in responses))
            duplicate = harness.pre_spawn(names[0], "spawn-1")
            self.assertEqual({}, duplicate)
            state = harness.state()
            self.assertEqual(10, len(state["pools"]["abc123"]["attempts"]))
            ledger = harness.ledger()
            pre_spawn_rows = [
                row
                for row in ledger
                if row["event"] == "PreToolUse"
                and row["details"].get("candidate")
            ]
            self.assertEqual(10, len(pre_spawn_rows))
            self.assertEqual(len(ledger), len({row["event_id"] for row in ledger}))

    def test_public_ledger_contains_hashes_not_raw_prompt_or_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            harness = HookHarness(Path(directory))
            name = harness.task("abc123", 1, 1, "00000001")
            harness.pre_spawn(name, "spawn-1")
            raw = "ATP_POOL_CANCEL abc123 /Users/example secret-user-prompt"
            harness.call(
                hook_event_name="UserPromptSubmit",
                turn_id="root-turn",
                prompt=raw,
                cwd="/Users/example/project",
                transcript_path="/Users/example/transcript.jsonl",
            )
            ledger = (harness.state_dir() / "events.jsonl").read_text()
            self.assertNotIn(raw, ledger)
            self.assertNotIn("/Users/", ledger)
            self.assertIn(hashlib.sha256(raw.encode()).hexdigest(), ledger)


if __name__ == "__main__":
    unittest.main()
