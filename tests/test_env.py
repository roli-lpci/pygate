from __future__ import annotations

from unittest.mock import patch

from pygate.env import capture_environment, check_environment, command_exists


class TestCommandExists:
    def test_known_command(self):
        # python3 should always exist in test environment
        assert command_exists("python3") is True

    def test_unknown_command(self):
        assert command_exists("definitely-not-a-real-command-xyz") is False


class TestCheckEnvironment:
    @patch("pygate.env.command_exists", return_value=True)
    def test_no_warnings_when_all_present(self, mock_exists):
        warnings = check_environment(command="run")
        assert warnings == []

    @patch("pygate.env.command_exists", return_value=False)
    def test_warns_for_missing_tools(self, mock_exists):
        warnings = check_environment(command="run")
        assert any("git" in w for w in warnings)
        assert any("ruff" in w for w in warnings)
        assert any("pyright" in w for w in warnings)

    @patch("pygate.env.command_exists", return_value=False)
    def test_non_run_command_skips_tool_checks(self, mock_exists):
        warnings = check_environment(command="summarize")
        assert any("git" in w for w in warnings)
        assert not any("ruff" in w for w in warnings)


class TestCaptureEnvironment:
    def test_returns_environment_info(self):
        env = capture_environment()
        assert env.python_version  # non-empty
        assert env.platform  # non-empty
        assert isinstance(env.installed_packages, dict)
