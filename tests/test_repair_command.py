from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from pygate.repair_command import execute_repair


class TestExecuteRepair:
    def test_escalates_when_no_improvement(self, tmp_path: Path, seed_failures):
        failures_path = seed_failures(findings_count=2)

        # Mock execute_run to always return failures
        with (
            patch("pygate.repair_command.execute_run") as mock_run,
            patch("pygate.repair_command.run_deterministic_prefix") as mock_fix,
        ):
            mock_fix.return_value = []

            # Each re-run returns same failures (no improvement)
            def side_effect(**kwargs):
                # Write a failures.json that mirrors the seed
                pygate_dir = tmp_path / ".pygate"
                f_data = json.loads(failures_path.read_text())
                (pygate_dir / "failures.json").write_text(json.dumps(f_data))
                return {"status": "fail", "failures_path": str(pygate_dir / "failures.json"), "run_id": "re_run"}

            mock_run.side_effect = side_effect

            result = execute_repair(input_path=str(failures_path), max_attempts=3, cwd=tmp_path)

        assert result["status"] == "escalated"
        assert result["reason_code"] == "NO_IMPROVEMENT"

    def test_returns_pass_when_gates_clear(self, tmp_path: Path, seed_failures):
        failures_path = seed_failures(findings_count=1)

        with (
            patch("pygate.repair_command.execute_run") as mock_run,
            patch("pygate.repair_command.run_deterministic_prefix") as mock_fix,
        ):
            mock_fix.return_value = [{"rule_id": "RUFF_AUTOFIX", "accepted": True}]

            # Re-run returns pass
            def side_effect(**kwargs):
                pygate_dir = tmp_path / ".pygate"
                pass_data = {
                    "version": "1.0.0",
                    "run_id": "re_run",
                    "mode": "canary",
                    "status": "pass",
                    "timestamp": "2025-01-01T00:00:00Z",
                    "changed_files": [],
                    "gates": [{"name": "lint", "status": "pass", "duration_ms": 50}],
                    "findings": [],
                    "inferred_hints": [],
                }
                (pygate_dir / "failures.json").write_text(json.dumps(pass_data))
                return {"status": "pass", "failures_path": str(pygate_dir / "failures.json"), "run_id": "re_run"}

            mock_run.side_effect = side_effect

            result = execute_repair(input_path=str(failures_path), max_attempts=3, cwd=tmp_path)

        assert result["status"] == "pass"
        report_path = tmp_path / ".pygate" / "repair-report.json"
        assert report_path.exists()

    def test_escalates_on_attempts_exhausted(self, tmp_path: Path, seed_failures):
        failures_path = seed_failures(findings_count=2)

        with (
            patch("pygate.repair_command.execute_run") as mock_run,
            patch("pygate.repair_command.run_deterministic_prefix") as mock_fix,
        ):
            mock_fix.return_value = []
            call_count = 0

            def side_effect(**kwargs):
                nonlocal call_count
                call_count += 1
                pygate_dir = tmp_path / ".pygate"
                # Alternate between 2 and 1 findings to avoid NO_IMPROVEMENT trigger
                count = 2 if call_count % 2 == 0 else 1
                f_data = {
                    "version": "1.0.0",
                    "run_id": f"re_{call_count}",
                    "mode": "canary",
                    "status": "fail",
                    "timestamp": "2025-01-01T00:00:00Z",
                    "changed_files": ["src/foo.py"],
                    "gates": [{"name": "lint", "status": "fail", "duration_ms": 50}],
                    "findings": [
                        {
                            "id": f"f{i}",
                            "gate": "lint",
                            "severity": "high",
                            "summary": f"issue {i}",
                            "actual": 1,
                            "threshold": 0,
                        }
                        for i in range(count)
                    ],
                    "inferred_hints": [],
                }
                (pygate_dir / "failures.json").write_text(json.dumps(f_data))
                return {
                    "status": "fail",
                    "failures_path": str(pygate_dir / "failures.json"),
                    "run_id": f"re_{call_count}",
                }

            mock_run.side_effect = side_effect

            result = execute_repair(input_path=str(failures_path), max_attempts=2, cwd=tmp_path)

        assert result["status"] == "escalated"
        assert result["reason_code"] in ("NO_IMPROVEMENT", "UNKNOWN_BLOCKER")
