from __future__ import annotations

from pathlib import Path

from pygate.summarize_command import execute_summarize


class TestExecuteSummarize:
    def test_generates_brief_for_failures(self, tmp_path: Path, seed_failures):
        failures_path = seed_failures(findings_count=2)
        result = execute_summarize(input_path=str(failures_path), cwd=tmp_path)

        assert result["status"] == "fail"
        assert Path(result["brief_json_path"]).exists()
        assert Path(result["brief_md_path"]).exists()

    def test_generates_brief_for_pass(self, tmp_path: Path, seed_failures):
        failures_path = seed_failures(findings_count=0)
        result = execute_summarize(input_path=str(failures_path), cwd=tmp_path)

        assert result["status"] == "pass"

    def test_markdown_contains_findings(self, tmp_path: Path, seed_failures):
        failures_path = seed_failures(findings_count=2)
        execute_summarize(input_path=str(failures_path), cwd=tmp_path)

        md_path = tmp_path / ".pygate" / "agent-brief.md"
        md = md_path.read_text()
        assert "ruff_F401" in md
        assert "lint" in md.lower()
        assert "Retry Policy" in md

    def test_json_brief_has_priority_actions(self, tmp_path: Path, seed_failures):
        failures_path = seed_failures(findings_count=2)
        execute_summarize(input_path=str(failures_path), cwd=tmp_path)

        from pygate.fs import read_json

        brief = read_json(tmp_path / ".pygate" / "agent-brief.json")
        assert len(brief["priority_actions"]) == 2
        assert brief["retry_policy"]["max_attempts"] == 3
