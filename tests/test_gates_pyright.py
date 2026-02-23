from __future__ import annotations

import json
from pathlib import Path

from pygate.gates.pyright import parse_pyright_output, resolve_pyright_command
from pygate.models import GateName, Severity


class TestResolvePyrightCommand:
    def test_default(self):
        assert resolve_pyright_command({}) == "pyright --outputjson ."

    def test_custom(self):
        assert resolve_pyright_command({"typecheck": "pyright src/"}) == "pyright src/"


class TestParsePyrightOutput:
    def test_parse_fixture(self, pyright_output: dict):
        stdout = json.dumps(pyright_output)
        cwd = Path("/tmp/project")
        findings = parse_pyright_output(stdout, "", 1, cwd)

        # Fixture has 4 diagnostics; 1 "information" is filtered out -> 2 errors + 1 warning = 3 findings
        assert len(findings) == 3

        # First error
        f0 = findings[0]
        assert f0.gate == GateName.TYPECHECK
        assert f0.severity == Severity.HIGH
        assert f0.rule == "reportAttributeAccessIssue"
        assert f0.files == ["src/foo.py"]
        assert f0.line == 11  # 0-indexed 10 + 1

        # Warning
        f2 = findings[2]
        assert f2.severity == Severity.MEDIUM

    def test_empty_output(self):
        findings = parse_pyright_output("", "", 0, Path("/tmp"))
        assert findings == []

    def test_invalid_json(self):
        findings = parse_pyright_output("not json", "", 1, Path("/tmp"))
        assert findings == []

    def test_no_diagnostics(self):
        data = {"version": "1.0", "generalDiagnostics": [], "summary": {"errorCount": 0}}
        findings = parse_pyright_output(json.dumps(data), "", 0, Path("/tmp"))
        assert findings == []
