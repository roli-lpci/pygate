from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, data: Any) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(data, indent=2, default=str) + "\n", encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8")


def load_changed_files(path: Path) -> list[str]:
    content = path.read_text(encoding="utf-8").strip()
    if not content:
        return []
    if content.startswith("["):
        parsed = json.loads(content)
        if not isinstance(parsed, list):
            return []
        return [f for f in parsed if isinstance(f, str)]
    return [line.strip() for line in content.splitlines() if line.strip()]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
