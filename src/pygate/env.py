from __future__ import annotations

import json
import shutil
import sys

from pygate.exec import run_command
from pygate.models import EnvironmentInfo


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def check_environment(*, command: str) -> list[str]:
    warnings: list[str] = []
    if not command_exists("git"):
        warnings.append("git not found: repo metadata will be unavailable")
    if command == "run":
        if not command_exists("ruff"):
            warnings.append("ruff not found: lint gate will fail")
        if not command_exists("pyright"):
            warnings.append("pyright not found: typecheck gate will fail")
    return warnings


def capture_environment() -> EnvironmentInfo:
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    platform = sys.platform
    virtualenv = sys.prefix if sys.prefix != sys.base_prefix else None
    resolver = _detect_resolver()
    installed = _get_installed_packages()

    return EnvironmentInfo(
        python_version=python_version,
        platform=platform,
        virtualenv=virtualenv,
        resolver=resolver,
        installed_packages=installed,
    )


def _detect_resolver() -> str | None:
    if command_exists("uv"):
        return "uv"
    if command_exists("poetry"):
        return "poetry"
    if command_exists("pip"):
        return "pip"
    return None


def _get_installed_packages() -> dict[str, str]:
    for cmd in ["uv pip list --format json", "pip list --format json"]:
        exe = cmd.split()[0]
        if not command_exists(exe):
            continue
        trace = run_command(cmd, timeout_seconds=30)
        if trace.exit_code == 0 and trace.stdout.strip():
            try:
                pkgs = json.loads(trace.stdout)
                return {p["name"]: p["version"] for p in pkgs if isinstance(p, dict)}
            except (json.JSONDecodeError, KeyError):
                continue
    return {}
