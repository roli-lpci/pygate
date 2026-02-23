from __future__ import annotations

import json
from pathlib import Path

from pygate.fs import ensure_dir, load_changed_files, now_iso, read_json, write_json, write_text


class TestEnsureDir:
    def test_creates_nested_dirs(self, tmp_path: Path):
        target = tmp_path / "a" / "b" / "c"
        ensure_dir(target)
        assert target.is_dir()

    def test_idempotent(self, tmp_path: Path):
        target = tmp_path / "d"
        ensure_dir(target)
        ensure_dir(target)  # should not raise
        assert target.is_dir()


class TestWriteAndReadJson:
    def test_roundtrip(self, tmp_path: Path):
        data = {"key": "value", "nested": [1, 2, 3]}
        path = tmp_path / "test.json"
        write_json(path, data)
        result = read_json(path)
        assert result == data

    def test_creates_parent_dirs(self, tmp_path: Path):
        path = tmp_path / "sub" / "dir" / "data.json"
        write_json(path, {"ok": True})
        assert path.exists()
        assert read_json(path) == {"ok": True}


class TestWriteText:
    def test_writes_text(self, tmp_path: Path):
        path = tmp_path / "out.txt"
        write_text(path, "hello world")
        assert path.read_text() == "hello world"

    def test_creates_parent_dirs(self, tmp_path: Path):
        path = tmp_path / "nested" / "out.txt"
        write_text(path, "content")
        assert path.read_text() == "content"


class TestLoadChangedFiles:
    def test_newline_delimited(self, tmp_path: Path):
        path = tmp_path / "changed.txt"
        path.write_text("src/a.py\nsrc/b.py\n")
        assert load_changed_files(path) == ["src/a.py", "src/b.py"]

    def test_json_array(self, tmp_path: Path):
        path = tmp_path / "changed.json"
        path.write_text(json.dumps(["src/a.py", "src/b.py"]))
        assert load_changed_files(path) == ["src/a.py", "src/b.py"]

    def test_empty_file(self, tmp_path: Path):
        path = tmp_path / "empty.txt"
        path.write_text("")
        assert load_changed_files(path) == []

    def test_blank_lines_filtered(self, tmp_path: Path):
        path = tmp_path / "changed.txt"
        path.write_text("src/a.py\n\n  \nsrc/b.py\n")
        assert load_changed_files(path) == ["src/a.py", "src/b.py"]


class TestNowIso:
    def test_returns_iso_string(self):
        result = now_iso()
        assert "T" in result
        assert result.endswith("+00:00")
