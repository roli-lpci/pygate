from __future__ import annotations

import json
from pathlib import Path

from pygate.models import Finding, GateName, Severity


def resolve_pyright_command(commands_config: dict) -> str:
    return commands_config.get("typecheck", "pyright --outputjson .")


def _map_severity(pyright_severity: str) -> Severity:
    match pyright_severity:
        case "error":
            return Severity.HIGH
        case "warning":
            return Severity.MEDIUM
        case "information":
            return Severity.LOW
        case _:
            return Severity.MEDIUM


def parse_pyright_output(stdout: str, stderr: str, exit_code: int, cwd: Path) -> list[Finding]:
    try:
        data = json.loads(stdout)
    except (json.JSONDecodeError, ValueError):
        return []

    if not isinstance(data, dict):
        return []

    diagnostics = data.get("generalDiagnostics", [])

    findings: list[Finding] = []
    for d in diagnostics:
        sev = d.get("severity", "error")
        if sev == "information":
            continue

        file_path = d.get("file", "")
        message = d.get("message", "")
        rule = d.get("rule", "")
        range_info = d.get("range", {})
        start = range_info.get("start", {})
        line = start.get("line", 0) + 1  # pyright is 0-indexed
        col = start.get("character", 0) + 1  # pyright is 0-indexed

        try:
            rel_path = str(Path(file_path).relative_to(cwd))
        except ValueError:
            rel_path = file_path

        finding_id = f"pyright_{rule}_{rel_path}_{line}" if rule else f"pyright_{rel_path}_{line}"

        findings.append(
            Finding(
                id=finding_id,
                gate=GateName.TYPECHECK,
                severity=_map_severity(sev),
                summary=f"{rule}: {message}" if rule else message,
                files=[rel_path],
                rule=rule or None,
                line=line,
                column=col,
                actual=1,
                threshold=0,
                raw={
                    "pyright_severity": sev,
                    "range": range_info,
                },
            )
        )

    return findings
