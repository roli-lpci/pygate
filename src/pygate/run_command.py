from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from pygate.config import load_config
from pygate.constants import FAILURES_FILE, PYGATE_DIR, RUN_METADATA_FILE
from pygate.env import capture_environment
from pygate.exec import run_command
from pygate.fs import ensure_dir, now_iso, write_json
from pygate.gates import run_deterministic_gates
from pygate.models import (
    Confidence,
    FailuresPayload,
    InferredHint,
    RunMetadata,
    RunMode,
    RunStatus,
)


def _git_info(cwd: Path) -> dict[str, str | None]:
    from pygate.env import command_exists

    if not command_exists("git"):
        return {"repo": None, "branch": None}

    repo = None
    branch = None

    trace = run_command("git config --get remote.origin.url", cwd=cwd)
    if trace.exit_code == 0:
        repo = trace.stdout.strip() or None

    trace = run_command("git rev-parse --abbrev-ref HEAD", cwd=cwd)
    if trace.exit_code == 0:
        branch = trace.stdout.strip() or None

    return {"repo": repo, "branch": branch}


def _generate_run_id() -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    short_uuid = uuid.uuid4().hex[:8]
    return f"run_{ts}_{short_uuid}"


def execute_run(
    *,
    mode: RunMode,
    changed_files: list[str],
    cwd: Path | None = None,
) -> dict:
    cwd = cwd or Path.cwd()
    pygate_dir = cwd / PYGATE_DIR
    ensure_dir(pygate_dir)

    run_id = _generate_run_id()
    started_at = now_iso()
    start_ms = _monotonic_ms()

    config = load_config(cwd)
    environment = capture_environment()

    gate_results, findings, traces = run_deterministic_gates(
        mode=mode, cwd=cwd, config=config, changed_files=changed_files
    )

    status = RunStatus.FAIL if findings else RunStatus.PASS
    git = _git_info(cwd)

    inferred_hints = [
        InferredHint(
            finding_id=f.id,
            hint=f"Start with the deterministic gate failure in {f.gate.value}. "
            "Inspect command output in run-metadata traces.",
            confidence=Confidence.LOW,
        )
        for f in findings
    ]

    failures = FailuresPayload(
        run_id=run_id,
        mode=mode,
        status=status,
        timestamp=now_iso(),
        repo=git["repo"],
        branch=git["branch"],
        changed_files=changed_files,
        gates=gate_results,
        findings=findings,
        inferred_hints=inferred_hints,
    )

    metadata = RunMetadata(
        run_id=run_id,
        mode=mode,
        started_at=started_at,
        completed_at=now_iso(),
        duration_ms=_monotonic_ms() - start_ms,
        config_source=config.get("source", "defaults"),
        environment=environment,
        command_traces=traces,
    )

    failures_path = cwd / FAILURES_FILE
    metadata_path = cwd / RUN_METADATA_FILE

    write_json(failures_path, failures.model_dump(mode="json"))
    write_json(metadata_path, metadata.model_dump(mode="json"))

    return {
        "status": status.value,
        "failures_path": str(failures_path),
        "metadata_path": str(metadata_path),
        "run_id": run_id,
    }


def _monotonic_ms() -> int:
    return int(time.monotonic() * 1000)
