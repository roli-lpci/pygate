from __future__ import annotations

from pathlib import Path

from pygate.config import load_config
from pygate.constants import DEFAULT_POLICY


class TestLoadConfig:
    def test_defaults_when_no_config(self, tmp_path: Path):
        config = load_config(tmp_path)
        assert config["source"] == "defaults"
        assert config["policy"]["max_attempts"] == DEFAULT_POLICY["max_attempts"]
        assert config["commands"] == {}

    def test_pygate_toml_takes_priority(self, tmp_path: Path):
        (tmp_path / "pygate.toml").write_text('[policy]\nmax_attempts = 5\n[commands]\nlint = "custom-ruff"\n')
        (tmp_path / "pyproject.toml").write_text("[tool.pygate.policy]\nmax_attempts = 10\n")
        config = load_config(tmp_path)
        assert config["policy"]["max_attempts"] == 5
        assert config["commands"]["lint"] == "custom-ruff"
        assert "pygate.toml" in config["source"]

    def test_pyproject_toml_fallback(self, tmp_path: Path):
        (tmp_path / "pyproject.toml").write_text("[tool.pygate.policy]\nmax_attempts = 7\n")
        config = load_config(tmp_path)
        assert config["policy"]["max_attempts"] == 7
        assert "pyproject.toml" in config["source"]

    def test_pyproject_without_pygate_section_returns_defaults(self, tmp_path: Path):
        (tmp_path / "pyproject.toml").write_text("[tool.ruff]\nline-length = 80\n")
        config = load_config(tmp_path)
        assert config["source"] == "defaults"

    def test_merge_preserves_unset_defaults(self, tmp_path: Path):
        (tmp_path / "pygate.toml").write_text("[policy]\nmax_attempts = 5\n")
        config = load_config(tmp_path)
        # max_attempts overridden, but other defaults preserved
        assert config["policy"]["max_attempts"] == 5
        assert config["policy"]["max_patch_lines"] == DEFAULT_POLICY["max_patch_lines"]
