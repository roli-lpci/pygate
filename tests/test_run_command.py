from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from pygate.models import CommandTrace, RunMode
from pygate.run_command import execute_run


def _make_trace(exit_code: int = 0, stdout: str = "", stderr: str = "") -> CommandTrace:
    return CommandTrace(
        command="test",
        cwd="/tmp",
        started_at="2025-01-01T00:00:00Z",
        duration_ms=100,
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
    )


class TestExecuteRun:
    @patch("pygate.gates.run_command")
    def test_all_gates_pass(self, mock_run, tmp_path: Path):
        # ruff returns 0 with empty array
        # pyright returns 0 with empty diagnostics
        mock_run.side_effect = [
            _make_trace(0, "[]"),  # ruff
            _make_trace(0, json.dumps({"generalDiagnostics": [], "summary": {"errorCount": 0}})),  # pyright
        ]

        result = execute_run(mode=RunMode.CANARY, changed_files=["src/foo.py"], cwd=tmp_path)

        assert result["status"] == "pass"
        assert Path(result["failures_path"]).exists()
        assert Path(result["metadata_path"]).exists()

        failures = json.loads(Path(result["failures_path"]).read_text())
        assert failures["status"] == "pass"
        assert len(failures["findings"]) == 0

    @patch("pygate.gates.run_command")
    def test_lint_gate_fails(self, mock_run, tmp_path: Path):
        ruff_output = [
            {
                "code": "F401",
                "filename": str(tmp_path / "src/foo.py"),
                "location": {"row": 1, "column": 1},
                "end_location": {"row": 1, "column": 10},
                "message": "unused import",
                "fix": None,
            }
        ]
        mock_run.side_effect = [
            _make_trace(1, json.dumps(ruff_output)),  # ruff fails
            _make_trace(0, json.dumps({"generalDiagnostics": [], "summary": {"errorCount": 0}})),  # pyright pass
        ]

        result = execute_run(mode=RunMode.CANARY, changed_files=["src/foo.py"], cwd=tmp_path)

        assert result["status"] == "fail"
        failures = json.loads(Path(result["failures_path"]).read_text())
        assert len(failures["findings"]) == 1
        assert failures["findings"][0]["gate"] == "lint"

    @patch("pygate.gates.run_command")
    def test_test_gate_skipped_in_canary(self, mock_run, tmp_path: Path):
        mock_run.side_effect = [
            _make_trace(0, "[]"),
            _make_trace(0, json.dumps({"generalDiagnostics": [], "summary": {"errorCount": 0}})),
        ]

        result = execute_run(mode=RunMode.CANARY, changed_files=[], cwd=tmp_path)
        failures = json.loads(Path(result["failures_path"]).read_text())

        gate_names = {g["name"] for g in failures["gates"]}
        assert "test" in gate_names
        test_gate = next(g for g in failures["gates"] if g["name"] == "test")
        assert test_gate["status"] == "skipped"

    def test_run_id_generated(self, tmp_path: Path):
        with patch("pygate.gates.run_command") as mock_run:
            mock_run.side_effect = [
                _make_trace(0, "[]"),
                _make_trace(0, json.dumps({"generalDiagnostics": [], "summary": {"errorCount": 0}})),
            ]
            result = execute_run(mode=RunMode.CANARY, changed_files=[], cwd=tmp_path)
            assert result["run_id"].startswith("run_")
