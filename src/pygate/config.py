from __future__ import annotations

import sys
from pathlib import Path

from pygate.constants import DEFAULT_POLICY

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None  # type: ignore[assignment]


def load_config(cwd: Path | None = None) -> dict:
    cwd = cwd or Path.cwd()

    # Try pygate.toml first
    pygate_toml = cwd / "pygate.toml"
    if pygate_toml.exists():
        return _merge_config(_load_toml(pygate_toml), source=str(pygate_toml))

    # Try pyproject.toml [tool.pygate]
    pyproject = cwd / "pyproject.toml"
    if pyproject.exists():
        full = _load_toml(pyproject)
        user_config = full.get("tool", {}).get("pygate", {})
        if user_config:
            return _merge_config(user_config, source=str(pyproject))

    return _defaults()


def _load_toml(path: Path) -> dict:
    if tomllib is None:
        raise ImportError(
            f"Cannot parse {path}: tomli package required on Python < 3.11. Install it with: pip install tomli"
        )
    with open(path, "rb") as f:
        return tomllib.load(f)


def _defaults() -> dict:
    return {
        "policy": dict(DEFAULT_POLICY),
        "commands": {},
        "gates": {},
        "source": "defaults",
    }


def _merge_config(user: dict, *, source: str) -> dict:
    defaults = _defaults()
    policy = {**defaults["policy"], **user.get("policy", {})}
    commands = user.get("commands", {})
    gates = {**defaults["gates"], **user.get("gates", {})}
    return {
        "policy": policy,
        "commands": commands,
        "gates": gates,
        "source": source,
    }
