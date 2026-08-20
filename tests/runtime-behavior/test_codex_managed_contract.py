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
    / "tests/runtime-behavior/evidence/codex-cli-0.147.0-20260819.json"
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
        evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
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
        self.assertTrue(any(item["result"] == "fail" for item in evidence["smokes"]))
        self.assertEqual("unsupported", deployed["host_managed_subagent_orchestration"])
        self.assertFalse(deployed["team_execution_enabled"])

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
