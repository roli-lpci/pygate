from __future__ import annotations

from pathlib import Path

from pygate.exec import run_command
from pygate.gates.pyright import parse_pyright_output, resolve_pyright_command
from pygate.gates.pytest_gate import parse_pytest_output, resolve_pytest_command
from pygate.gates.ruff import parse_ruff_output, resolve_ruff_command
from pygate.models import (
    CommandTrace,
    Finding,
    GateName,
    GateResult,
    GateStatus,
    RunMode,
    Severity,
)


def _finding_for_exit_code(gate: GateName, trace: CommandTrace) -> Finding:
    return Finding(
        id=f"{gate.value}_exit_{trace.exit_code}",
        gate=gate,
        severity=Severity.HIGH,
        summary=f"{gate.value} command failed with exit code {trace.exit_code}",
        actual=trace.exit_code,
        threshold=0,
        raw={
            "command": trace.command,
            "stderr_excerpt": "\n".join(trace.stderr.splitlines()[:30]),
            "stdout_excerpt": "\n".join(trace.stdout.splitlines()[:30]),
        },
    )


def run_deterministic_gates(
    *,
    mode: RunMode,
    cwd: Path,
    config: dict,
    changed_files: list[str],
) -> tuple[list[GateResult], list[Finding], list[CommandTrace]]:
    gates_config = config.get("gates", {})
    commands_config = config.get("commands", {})
    test_in_canary = gates_config.get("test_in_canary", False)

    gate_plan = [
        (GateName.LINT, True),
        (GateName.TYPECHECK, True),
        (GateName.TEST, mode == RunMode.FULL or test_in_canary),
    ]

    gate_results: list[GateResult] = []
    all_findings: list[Finding] = []
    all_traces: list[CommandTrace] = []

    for gate_name, enabled in gate_plan:
        if not enabled:
            gate_results.append(GateResult(name=gate_name, status=GateStatus.SKIPPED, duration_ms=0))
            continue

        cmd = _resolve_command(gate_name, commands_config, cwd)
        trace = run_command(cmd, cwd=cwd)
        all_traces.append(trace)

        if trace.exit_code != 0:
            findings = _parse_gate_output(gate_name, trace, cwd)
            if not findings:
                findings = [_finding_for_exit_code(gate_name, trace)]
            all_findings.extend(findings)
            gate_results.append(GateResult(name=gate_name, status=GateStatus.FAIL, duration_ms=trace.duration_ms))
        else:
            gate_results.append(GateResult(name=gate_name, status=GateStatus.PASS, duration_ms=trace.duration_ms))

    return gate_results, all_findings, all_traces


def _resolve_command(gate: GateName, commands_config: dict, cwd: Path) -> str:
    if gate.value in commands_config:
        return commands_config[gate.value]

    match gate:
        case GateName.LINT:
            return resolve_ruff_command(commands_config)
        case GateName.TYPECHECK:
            return resolve_pyright_command(commands_config)
        case GateName.TEST:
            return resolve_pytest_command(commands_config, cwd)
        case _:
            raise ValueError(f"Unknown gate: {gate}")


def _parse_gate_output(gate: GateName, trace: CommandTrace, cwd: Path) -> list[Finding]:
    match gate:
        case GateName.LINT:
            return parse_ruff_output(trace.stdout, trace.stderr, trace.exit_code, cwd)
        case GateName.TYPECHECK:
            return parse_pyright_output(trace.stdout, trace.stderr, trace.exit_code, cwd)
        case GateName.TEST:
            report_path = cwd / ".pygate" / "pytest-report.json"
            return parse_pytest_output(trace.stdout, trace.stderr, trace.exit_code, report_path, cwd)
        case _:
            return []
