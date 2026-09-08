#!/usr/bin/env python3
"""Regression tests for Codex host-managed subagent orchestration."""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "tests/runtime-behavior/validate_codex_session.py"
CODEX_TEAM_SKILL = ROOT / "plugins/atp/skills/codex-team/SKILL.md"
TASK_SKILL = ROOT / "plugins/atp/skills/task/SKILL.md"
PROTOCOL = ROOT / "plugins/atp/docs/development/agent-team-protocol.md"
AGENT_DIR = ROOT / "plugins/atp/agents"
FIXTURES = ROOT / "tests/runtime-behavior/fixtures"
EVIDENCE = (
    ROOT
    / "tests/runtime-behavior/evidence/codex-cli-0.149.1-20260826.json"
)
PROMOTION_EVIDENCE = (
    ROOT
    / "tests/runtime-behavior/evidence/codex-cli-0.149.1-hook-guarded-20260908.json"
)


class CodexManagedContractTests(unittest.TestCase):
    maxDiff = None

    def run_validator(
        self,
        stem: str,
        *,
        session: Path | None = None,
        ledger: Path | None = None,
        report: Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                "python3",
                str(VALIDATOR),
                "--profile",
                "host-managed",
                "--session-jsonl",
                str(session or FIXTURES / f"{stem}-session.jsonl"),
                "--ledger",
                str(ledger or FIXTURES / f"{stem}-ledger.jsonl"),
                "--report",
                str(report or FIXTURES / f"{stem}-report.md"),
                "--appendix",
                str(
                    ROOT
                    / "plugins/atp/docs/development/codex-lifecycle-routing.md"
                ),
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

    def test_codex_team_skill_is_mandatory_before_delegation(self) -> None:
        self.assertTrue(CODEX_TEAM_SKILL.is_file(), "Codex team skill is missing")
        skill = CODEX_TEAM_SKILL.read_text(encoding="utf-8")
        task = TASK_SKILL.read_text(encoding="utf-8")
        for term in (
            "Codex",
            "subagent",
            "spawn",
            "delegate",
            "steer",
            "collect",
            "전체 `SKILL.md`",
            "모든 요청 agent",
        ):
            self.assertIn(term, skill)
        self.assertIn("host orchestration skill", task)
        self.assertIn("전체 지침", task)

    def test_validator_exposes_host_managed_profile(self) -> None:
        result = subprocess.run(
            ["python3", str(VALIDATOR), "--help"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("host-managed", result.stdout)

    def test_three_managed_orchestration_fixtures_pass(self) -> None:
        for stem in (
            "managed-terminal-only",
            "managed-delayed-terminal",
            "managed-two-agents",
        ):
            with self.subTest(stem=stem):
                result = self.run_validator(stem)
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)
                summary = json.loads(result.stdout.split("\nPASS:", 1)[0])
                self.assertEqual(0, summary["executed"].get("wait_agent", 0))
                self.assertEqual(0, summary["executed"].get("list_agents", 0))
                self.assertEqual(0, summary["executed"].get("interrupt_agent", 0))

    def test_message_only_cannot_integrate_or_complete(self) -> None:
        rows = [
            json.loads(line)
            for line in (FIXTURES / "managed-delayed-terminal-session.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        rows = [row for row in rows if row["ordinal"] <= 4]
        rows.append(
            {
                "timestamp": "2026-08-19T03:10:03Z",
                "ordinal": 5,
                "type": "event_msg",
                "payload": {
                    "type": "item_completed",
                    "item": {
                        "type": "FileChange",
                        "changes": {
                            ".atp/work-session/fixture-managed-delayed-terminal/report.md": {
                                "type": "update",
                                "unified_diff": "@@\n-ended_at: null\n+ended_at: 2026-08-19T12:10:41+09:00\n+  termination: completed\n",
                            }
                        },
                    },
                },
            }
        )
        with tempfile.TemporaryDirectory() as directory:
            session = Path(directory) / "session.jsonl"
            session.write_text(
                "\n".join(json.dumps(row) for row in rows) + "\n",
                encoding="utf-8",
            )
            result = self.run_validator(
                "managed-delayed-terminal", session=session
            )
        self.assertNotEqual(0, result.returncode)
        output = result.stdout + result.stderr
        self.assertIn("nonterminal", output.lower())
        self.assertIn("completion serialization", output.lower())

    def test_two_agents_require_every_terminal_before_parent_final(self) -> None:
        rows = [
            json.loads(line)
            for line in (FIXTURES / "managed-two-agents-session.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        for row in rows:
            if row["ordinal"] == 10:
                row["ordinal"] = 7
                row["timestamp"] = "2026-08-19T03:20:06Z"
            elif row["ordinal"] == 7:
                row["ordinal"] = 8
            elif row["ordinal"] == 8:
                row["ordinal"] = 9
            elif row["ordinal"] == 9:
                row["ordinal"] = 10
        rows.sort(key=lambda row: row["ordinal"])
        with tempfile.TemporaryDirectory() as directory:
            session = Path(directory) / "session.jsonl"
            session.write_text(
                "\n".join(json.dumps(row) for row in rows) + "\n",
                encoding="utf-8",
            )
            result = self.run_validator("managed-two-agents", session=session)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("parent final", (result.stdout + result.stderr).lower())

    def test_future_ended_at_serialized_before_terminal_fails(self) -> None:
        rows = [
            json.loads(line)
            for line in (FIXTURES / "managed-delayed-terminal-session.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        completion = next(row for row in rows if row["ordinal"] == 6)
        completion["ordinal"] = 5
        completion["timestamp"] = "2026-08-19T03:10:03Z"
        terminal = next(row for row in rows if row["ordinal"] == 5)
        terminal["ordinal"] = 6
        rows.sort(key=lambda row: row["ordinal"])
        with tempfile.TemporaryDirectory() as directory:
            session = Path(directory) / "session.jsonl"
            session.write_text(
                "\n".join(json.dumps(row) for row in rows) + "\n",
                encoding="utf-8",
            )
            result = self.run_validator(
                "managed-delayed-terminal", session=session
            )
        self.assertNotEqual(0, result.returncode)
        self.assertIn("completion serialization", (result.stdout + result.stderr).lower())

    def test_identity_and_source_ref_must_resolve(self) -> None:
        report_text = (FIXTURES / "managed-terminal-only-report.md").read_text(
            encoding="utf-8"
        )
        ledger_rows = [
            json.loads(line)
            for line in (FIXTURES / "managed-terminal-only-ledger.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        cases = {
            "identity": (
                report_text.replace("env-terminal-1", "env-does-not-exist"),
                ledger_rows,
            ),
            "source_ref": (
                report_text,
                [
                    ledger_rows[0],
                    {
                        **ledger_rows[1],
                        "source_ref": "session:fixture-managed-terminal-only:event:terminal-9999",
                    },
                ],
            ),
        }
        for label, (candidate_report, candidate_ledger) in cases.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                temp = Path(directory)
                report = temp / "report.md"
                report.write_text(candidate_report, encoding="utf-8")
                ledger = temp / "ledger.jsonl"
                ledger.write_text(
                    "\n".join(json.dumps(row) for row in candidate_ledger) + "\n",
                    encoding="utf-8",
                )
                result = self.run_validator(
                    "managed-terminal-only", ledger=ledger, report=report
                )
            self.assertNotEqual(0, result.returncode)
            self.assertIn(label, (result.stdout + result.stderr).lower())

    def test_measurements_match_requested_spawn_terminal_and_collection(self) -> None:
        rows = [
            json.loads(line)
            for line in (FIXTURES / "managed-two-agents-ledger.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        mutations = {
            "requested_agents": 1,
            "spawn_calls": 1,
            "terminal_deliveries": 1,
            "collected_results": 1,
            "manual_wait_calls": 1,
            "list_calls": 1,
            "interrupt_calls": 1,
        }
        for field, value in mutations.items():
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                candidate = json.loads(json.dumps(rows))
                candidate[-1]["details"][field] = value
                ledger = Path(directory) / "ledger.jsonl"
                ledger.write_text(
                    "\n".join(json.dumps(row) for row in candidate) + "\n",
                    encoding="utf-8",
                )
                result = self.run_validator(
                    "managed-two-agents", ledger=ledger
                )
            self.assertNotEqual(0, result.returncode)
            self.assertIn(field, result.stdout + result.stderr)

    def test_unknown_telemetry_stays_null(self) -> None:
        rows = [
            json.loads(line)
            for line in (FIXTURES / "managed-terminal-only-ledger.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        rows[-1]["details"]["latency_ms"] = 0
        with tempfile.TemporaryDirectory() as directory:
            ledger = Path(directory) / "ledger.jsonl"
            ledger.write_text(
                "\n".join(json.dumps(row) for row in rows) + "\n",
                encoding="utf-8",
            )
            result = self.run_validator(
                "managed-terminal-only", ledger=ledger
            )
        self.assertNotEqual(0, result.returncode)
        self.assertIn("unknown telemetry", (result.stdout + result.stderr).lower())

    def test_unknown_telemetry_key_cannot_be_omitted(self) -> None:
        rows = [
            json.loads(line)
            for line in (FIXTURES / "managed-terminal-only-ledger.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        del rows[-1]["details"]["steering_latency_ms"]
        with tempfile.TemporaryDirectory() as directory:
            ledger = Path(directory) / "ledger.jsonl"
            ledger.write_text(
                "\n".join(json.dumps(row) for row in rows) + "\n",
                encoding="utf-8",
            )
            result = self.run_validator("managed-terminal-only", ledger=ledger)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("unknown telemetry", (result.stdout + result.stderr).lower())

    def test_deployed_profile_matches_empirical_smoke_outcome(self) -> None:
        """The deployed block must equal the promotion evidence profile, and that
        evidence must show every qualification smoke passing on the add-on build."""
        evidence = json.loads(PROMOTION_EVIDENCE.read_text(encoding="utf-8"))
        appendix = (
            ROOT / "plugins/atp/docs/development/codex-lifecycle-routing.md"
        ).read_text(encoding="utf-8")
        block = re.search(
            r"<!-- codex:orchestration-capability:begin -->\s*```yaml\s*"
            r"(?P<body>.*?)```\s*"
            r"<!-- codex:orchestration-capability:end -->",
            appendix,
            re.DOTALL,
        )
        self.assertIsNotNone(block)
        deployed: dict[str, bool | str] = {}
        assert block is not None
        for raw in block.group("body").splitlines():
            key, value = raw.split(":", 1)
            value = value.strip()
            deployed[key] = (
                True if value == "true" else False if value == "false" else value
            )
        self.assertEqual(evidence["deployed_profile"], deployed)
        self.assertTrue(all(item["result"] == "pass" for item in evidence["smokes"]))
        self.assertEqual("supported", deployed["host_managed_subagent_orchestration"])
        self.assertTrue(deployed["team_execution_enabled"])
        self.assertEqual("hook_guarded_bounded_pool", deployed["execution_scope"])
        self.assertEqual("atp_hook_guard_ready_marker", deployed["scope_gate"])
        ids = {item["id"] for item in evidence["smokes"]}
        self.assertTrue({"Q1-terminal-only-1-agent", "Q2-delayed-terminal-1-agent",
                         "Q3-staggered-2-agent-all-results",
                         "Q4-capacity-denial-refill-5-agent"} <= ids)
        denial = next(i for i in evidence["smokes"] if i["id"].startswith("Q4"))
        self.assertEqual(denial["spawn_attempts"] - denial["accepted_spawns"],
                         denial["hook_ledger_capacity_denials"])
        self.assertEqual({"parent_marker": denial["hook_ledger_capacity_denials"]},
                         denial["denials_attested_by"])
        for item in evidence["smokes"]:
            self.assertEqual(item["requested_tasks"], item["accepted_spawns"])
            self.assertEqual(item["requested_tasks"], item["terminal_deliveries"])
            self.assertEqual(item["requested_tasks"], item["collected_results"])
            self.assertEqual(0, item["list_calls"])
            self.assertEqual(0, item["interrupt_calls"])
            self.assertEqual("Stop", item["last_hook_event"])
        # the 2026-08-26 built-in barrier evidence is unchanged history: it still fails
        built_in = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        self.assertTrue(any(item["result"] == "fail" for item in built_in["smokes"]))
        self.assertFalse(built_in["deployed_profile"]["team_execution_enabled"])

    def test_promotion_evidence_is_sanitized(self) -> None:
        text = PROMOTION_EVIDENCE.read_text(encoding="utf-8")
        for needle in ("/Users/", "/private/tmp/", "wemadeplay"):
            self.assertNotIn(needle, text)
        evidence = json.loads(text)
        for item in evidence["smokes"]:
            for value in item["artifact_sha256"].values():
                self.assertRegex(value, r"^[0-9a-f]{64}$")

    def test_bounded_pool_candidate_evidence_is_not_promoted(self) -> None:
        evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        self.assertEqual(
            "2.16.0+codex.20260825102518",
            evidence["candidate_plugin_version"],
        )
        topology = evidence["topology_and_capacity_probes"]
        self.assertEqual("pass", topology["nested_spawn"]["result"])
        self.assertEqual(
            5, topology["short_lived_nested_fanout"]["accepted_spawns"]
        )
        saturated = topology["saturated_nested_fanout"]
        self.assertEqual(2, saturated["accepted_spawns"])
        self.assertEqual(3, saturated["rejected_spawns"])
        self.assertEqual(4, saturated["observed_active_threads_at_limit"])

        candidate = evidence["bounded_pool_candidate_smokes"]
        for key in ("flat_root_pool", "nested_owner_pool"):
            self.assertEqual("pass", candidate[key]["result"])
        self.assertEqual(5, candidate["flat_root_pool"]["collected_results"])
        self.assertEqual(
            5, candidate["nested_owner_pool"]["worker_collected_results"]
        )
        denial = candidate["capacity_denial_refill"]
        self.assertEqual(6, denial["spawn_attempts"])
        self.assertEqual(5, denial["accepted_spawns"])
        self.assertEqual(1, denial["capacity_denials"])
        self.assertEqual(5, denial["collected_results"])

        saturated = candidate["saturated_nonterminal_then_terminal"]
        self.assertEqual("fail", saturated["result"])
        self.assertEqual(3, saturated["nonterminal_observed_running"])
        self.assertEqual(2, saturated["nonterminal_observed_pending"])
        self.assertEqual(0, saturated["nonterminal_slot_releases"])
        self.assertEqual(0, saturated["nonterminal_triggered_refills"])
        self.assertEqual(3, saturated["terminal_deliveries"])
        self.assertEqual(1, saturated["collected_results"])
        self.assertTrue(saturated["identity_continuity"])
        self.assertFalse(saturated["parent_turn_completed"])

        steering = candidate["steering_while_pool_wait_active"]
        self.assertEqual("fail", steering["result"])
        self.assertEqual(1, steering["external_steering_queued"])
        self.assertEqual(1, steering["external_steering_acknowledged"])
        self.assertEqual(0, steering["external_steering_delivered_to_root"])
        self.assertEqual(4, steering["terminal_deliveries"])
        self.assertEqual(4, steering["collected_results"])
        self.assertEqual(5, steering["pool_wait_calls"])

        approval = candidate["approval_relay_and_continuation"]
        self.assertEqual("fail", approval["result"])
        self.assertEqual(1, approval["approval_required_events"])
        self.assertEqual(1, approval["approval_relays"])
        self.assertEqual("rejected", approval["approval_decision"])
        self.assertTrue(approval["approval_target_turn_aborted_after_decision"])
        self.assertEqual(0, approval["approval_target_terminal_deliveries"])
        self.assertIsNone(approval["approval_environment_identity_continued"])
        self.assertFalse(approval["approval_side_effect_marker_present"])

        cancellation = candidate["cancellation_with_running_and_pending"]
        self.assertEqual("fail", cancellation["result"])
        self.assertEqual(1, cancellation["external_cancellation_queued"])
        self.assertEqual(1, cancellation["external_cancellation_acknowledged"])
        self.assertEqual(0, cancellation["external_cancellation_delivered_to_root"])
        self.assertEqual(2, cancellation["spawns_after_external_cancellation_queued"])
        self.assertEqual(0, cancellation["scheduler_interrupt_calls"])
        self.assertFalse(
            cancellation["outer_cleanup_sigterm_is_scheduler_interrupt"]
        )

        parity = candidate["source_install_parity"]
        self.assertEqual("pass", parity["result"])
        self.assertTrue(parity["byte_equal"])
        self.assertEqual(
            parity["source_skill_sha256"], parity["installed_skill_sha256"]
        )
        installed = candidate["fresh_installed_regression"]
        self.assertEqual("pass", installed["result"])
        for key in ("flat_root_pool", "nested_owner_pool", "capacity_denial_refill"):
            self.assertEqual("pass", installed[key]["result"])
        installed_denial = installed["capacity_denial_refill"]
        self.assertEqual(6, installed_denial["spawn_attempts"])
        self.assertEqual(1, installed_denial["capacity_denials"])
        self.assertEqual(0, installed_denial["denied_task_retry_count"])

        gate = candidate["qualification_gate"]
        self.assertEqual("blocked", gate["decision"])
        self.assertFalse(gate["promotion_allowed"])
        self.assertFalse(gate["bounded_pool_execution_mode_integrated"])
        self.assertFalse(gate["version_bumped"])
        self.assertFalse(gate["release_metadata_changed"])
        self.assertFalse(candidate["release_qualification_complete"])
        self.assertFalse(evidence["deployed_profile"]["team_execution_enabled"])

    def test_codex_evidence_is_sanitized_and_hashes_are_well_formed(self) -> None:
        evidence_text = EVIDENCE.read_text(encoding="utf-8")
        self.assertNotIn("/Users/", evidence_text)
        self.assertNotIn("/private/tmp/", evidence_text)
        self.assertNotIn("wemadeplay", evidence_text)
        evidence = json.loads(evidence_text)

        def visit(value: object, key: str = "") -> None:
            if isinstance(value, dict):
                for child_key, child_value in value.items():
                    visit(child_value, child_key)
            elif isinstance(value, list):
                for child_value in value:
                    visit(child_value, key)
            elif key.endswith("sha256") or key in {
                "parent_jsonl",
                "root_jsonl",
                "child_jsonl",
                "grandchild_jsonl",
                "pool_owner_jsonl",
                "report",
                "ledger",
                "validator_output",
                "public_jsonl",
                "internal_rollout",
                "root_rollout",
                "approval_target_rollout",
                "companion_rollout",
                "root_internal_rollout",
                "depth_1_jsonl",
                "depth_2_jsonl",
                "depth_3_jsonl",
            }:
                self.assertIsInstance(value, str)
                assert isinstance(value, str)
                self.assertRegex(value, r"^[0-9a-f]{64}$")

        visit(evidence)

    def test_consumer_task_has_no_runtime_smoke_or_probe(self) -> None:
        task = TASK_SKILL.read_text(encoding="utf-8")
        forbidden = (
            "test child",
            "timeout probe",
            "wait/list probe",
            "runtime validator 실행",
            "source/install parity",
            "사용자에게 smoke",
        )
        for term in forbidden:
            self.assertNotIn(term, task)

    def test_common_sources_remain_codex_neutral(self) -> None:
        common_paths = [TASK_SKILL, PROTOCOL, *sorted(AGENT_DIR.glob("*.md"))]
        forbidden = (
            "spawn_agent",
            "wait_agent",
            "list_agents",
            "interrupt_agent",
            "Message Type:",
            "FINAL_ANSWER",
        )
        for path in common_paths:
            text = path.read_text(encoding="utf-8")
            for term in forbidden:
                self.assertNotIn(term, text, f"{term!r} leaked into {path}")


if __name__ == "__main__":
    unittest.main()
