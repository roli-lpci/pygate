from __future__ import annotations

import json
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture
def ruff_output() -> list:
    return json.loads((FIXTURES_DIR / "ruff_output.json").read_text())


@pytest.fixture
def pyright_output() -> dict:
    return json.loads((FIXTURES_DIR / "pyright_output.json").read_text())


@pytest.fixture
def sample_pytest_report() -> dict:
    return json.loads((FIXTURES_DIR / "pytest_report.json").read_text())


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Create a minimal temporary project directory."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "foo.py").write_text("import os\n\nx = 1\n")
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")
    return tmp_path


@pytest.fixture
def seed_failures(tmp_path: Path):
    """Write a failures.json to tmp_path/.pygate/ and return its path."""

    def _seed(findings_count: int = 2, mode: str = "canary") -> Path:
        pygate_dir = tmp_path / ".pygate"
        pygate_dir.mkdir(exist_ok=True)
        failures = {
            "version": "1.0.0",
            "run_id": "run_test_123",
            "mode": mode,
            "status": "fail" if findings_count > 0 else "pass",
            "timestamp": "2025-01-01T00:00:00+00:00",
            "changed_files": ["src/foo.py"],
            "gates": [
                {"name": "lint", "status": "fail" if findings_count > 0 else "pass", "duration_ms": 100},
                {"name": "typecheck", "status": "pass", "duration_ms": 200},
            ],
            "findings": [
                {
                    "id": f"ruff_F401_src/foo.py_{i}",
                    "gate": "lint",
                    "severity": "high",
                    "summary": f"F401: unused import {i}",
                    "files": ["src/foo.py"],
                    "rule": "F401",
                    "line": i,
                    "actual": 1,
                    "threshold": 0,
                }
                for i in range(1, findings_count + 1)
            ],
            "inferred_hints": [],
        }
        path = pygate_dir / "failures.json"
        path.write_text(json.dumps(failures, indent=2))
        return path

    return _seed
