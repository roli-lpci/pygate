from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

from pygate.fs import now_iso
from pygate.models import CommandTrace


def run_command(
    command: str,
    *,
    cwd: Path | str | None = None,
    timeout_seconds: int | None = None,
    env: dict[str, str] | None = None,
) -> CommandTrace:
    work_dir = str(cwd) if cwd else os.getcwd()
    merged_env = {**os.environ, **(env or {})}
    started_at = now_iso()
    start = time.monotonic()
    timed_out = False

    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            env=merged_env,
        )
        exit_code = result.returncode
        stdout = result.stdout or ""
        stderr = result.stderr or ""
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        exit_code = 1
        stdout = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")

    duration_ms = int((time.monotonic() - start) * 1000)

    return CommandTrace(
        command=command,
        cwd=work_dir,
        started_at=started_at,
        duration_ms=duration_ms,
        exit_code=exit_code,
        timed_out=timed_out,
        stdout=stdout,
        stderr=stderr,
    )
