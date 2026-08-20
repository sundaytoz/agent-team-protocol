#!/usr/bin/env python3
"""Regression tests for Codex native-cooperative lifecycle validation."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "tests/runtime-behavior/validate_codex_session.py"
FIXTURES = ROOT / "tests/runtime-behavior/fixtures"
APPENDIX = ROOT / "plugins/atp/docs/development/codex-lifecycle-routing.md"


class NativeCooperativeRegressionTests(unittest.TestCase):
    maxDiff = None

    def run_validator(
        self,
        *,
        session: Path,
        ledger: Path,
        report: Path,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                "python3",
                str(VALIDATOR),
                "--profile",
                "native-cooperative",
                "--session-jsonl",
                str(session),
                "--ledger",
                str(ledger),
                "--report",
                str(report),
                "--appendix",
                str(APPENDIX),
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

    def test_message_rejoins_until_final_and_measurement_matches(self) -> None:
        result = self.run_validator(
            session=FIXTURES / "native-cooperative-session.jsonl",
            ledger=FIXTURES / "native-cooperative-ledger.jsonl",
            report=FIXTURES / "native-cooperative-report.md",
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn('"wait_agent": 2', result.stdout)

    def test_message_only_cannot_complete_invocation_or_session(self) -> None:
        session_rows = [
            json.loads(line)
            for line in (FIXTURES / "native-cooperative-session.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        message_only = [row for row in session_rows if row.get("ordinal", 0) <= 5]
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            session = temp / "session.jsonl"
            session.write_text(
                "\n".join(json.dumps(row) for row in message_only) + "\n",
                encoding="utf-8",
            )
            result = self.run_validator(
                session=session,
                ledger=FIXTURES / "native-cooperative-ledger.jsonl",
                report=FIXTURES / "native-cooperative-report.md",
            )
        self.assertNotEqual(0, result.returncode)
        output = result.stdout + result.stderr
        self.assertIn("FINAL_ANSWER", output)
        self.assertIn("MESSAGE-only invocation cannot record ended_at", output)
        self.assertIn("MESSAGE-only session cannot record report ended_at", output)

    def test_final_answer_requires_completed_termination(self) -> None:
        report_text = (FIXTURES / "native-cooperative-report.md").read_text(
            encoding="utf-8"
        )
        report_text = report_text.replace(
            "termination: completed", "termination: failed", 1
        )
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "report.md"
            report.write_text(report_text, encoding="utf-8")
            result = self.run_validator(
                session=FIXTURES / "native-cooperative-session.jsonl",
                ledger=FIXTURES / "native-cooperative-ledger.jsonl",
                report=report,
            )
        self.assertNotEqual(0, result.returncode)
        self.assertIn(
            "FINAL_ANSWER requires report termination completed",
            result.stdout + result.stderr,
        )

    def test_explicit_environment_terminal_correlates_report_state(self) -> None:
        session_rows = [
            json.loads(line)
            for line in (FIXTURES / "native-cooperative-session.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        for row in session_rows:
            if row.get("ordinal") == 7:
                row["payload"]["output"] = json.dumps(
                    {
                        "message": "Wait completed.",
                        "timed_out": False,
                        "status": "failed",
                        "agent_id": "env-fixture-1",
                    }
                )
            elif row.get("ordinal") == 8:
                row["payload"] = {
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": "failure relayed"}],
                }
        report_text = (FIXTURES / "native-cooperative-report.md").read_text(
            encoding="utf-8"
        )
        report_text = report_text.replace(
            "termination: completed", "termination: failed", 1
        )
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            session = temp / "session.jsonl"
            session.write_text(
                "\n".join(json.dumps(row) for row in session_rows) + "\n",
                encoding="utf-8",
            )
            report = temp / "report.md"
            report.write_text(report_text, encoding="utf-8")
            result = self.run_validator(
                session=session,
                ledger=FIXTURES / "native-cooperative-ledger.jsonl",
                report=report,
            )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_ledger_envelope_capabilities_and_measurement_are_exact(self) -> None:
        ledger_rows = [
            json.loads(line)
            for line in (FIXTURES / "native-cooperative-ledger.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        mutations = {
            "missing-envelope": lambda rows: rows[0].pop("owner_report_invocation_id"),
            "capability-drift": lambda rows: rows[0]["details"][
                "formal_capabilities"
            ].__setitem__("stable_event_identity", "supported"),
            "measurement-drift": lambda rows: rows[-1]["details"].__setitem__(
                "wait_calls", 1
            ),
            "measurement-source-drift": lambda rows: rows[-1].__setitem__(
                "source_ref", "transcript:ordinal:8"
            ),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                rows = json.loads(json.dumps(ledger_rows))
                mutate(rows)
                ledger = Path(directory) / "ledger.jsonl"
                ledger.write_text(
                    "\n".join(json.dumps(row) for row in rows) + "\n",
                    encoding="utf-8",
                )
                result = self.run_validator(
                    session=FIXTURES / "native-cooperative-session.jsonl",
                    ledger=ledger,
                    report=FIXTURES / "native-cooperative-report.md",
                )
                self.assertNotEqual(0, result.returncode)
                self.assertIn(name.split("-")[0], (result.stdout + result.stderr).lower())

    def test_session_end_cannot_precede_last_requested_mutation(self) -> None:
        report_text = (FIXTURES / "native-cooperative-report.md").read_text(
            encoding="utf-8"
        )
        report_text = report_text.replace(
            "ended_at: 2026-08-18T00:00:31+09:00",
            "ended_at: 2026-08-18T00:00:19+09:00",
            1,
        )
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "report.md"
            report.write_text(report_text, encoding="utf-8")
            result = self.run_validator(
                session=FIXTURES / "native-cooperative-session.jsonl",
                ledger=FIXTURES / "native-cooperative-ledger.jsonl",
                report=report,
            )
        self.assertNotEqual(0, result.returncode)
        self.assertIn("ended_at", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
