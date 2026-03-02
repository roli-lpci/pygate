# AGENTS.md

## Commands

- `pip install -e ".[dev]"` -- Install with dev dependencies
- `pytest` -- Run all 140 tests
- `pytest tests/test_run_command.py -v` -- Single test module
- `ruff check src/pygate/` -- Lint
- `ruff check src/pygate/ --fix` -- Lint with auto-fix
- `pyright src/pygate/` -- Type check (basic mode)
- `python -m build` -- Build wheel and sdist
- `pygate run` -- Run all quality gates
- `pygate repair --max-attempts 3` -- Auto-repair lint failures
- `pygate summarize` -- Generate agent-readable brief

## Testing

- Framework: `pytest` (config in `pyproject.toml` under `[tool.pytest.ini_options]`)
- Test location: `tests/`, one file per source module
- Fixtures: `tests/conftest.py` + JSON fixtures in `tests/fixtures/`
- All tests run offline — no subprocess execution, all gate outputs are mocked
- Run single test: `pytest tests/test_gates_ruff.py::test_ruff_parse -v`

## Project Structure

```
src/pygate/
  cli.py               # Argument parsing, subcommand dispatch
  run_command.py        # `pygate run` — orchestrates gate execution
  repair_command.py     # `pygate repair` — bounded auto-fix loop (ruff --fix)
  summarize_command.py  # `pygate summarize` — agent brief from JSON artifacts
  gates/               # Individual gate implementations
    ruff.py            # Ruff lint gate (JSON output parsing)
    pyright.py         # Pyright type-check gate
    pytest_gate.py     # Pytest gate (--json-report parsing)
  models.py            # Pydantic models (GateResult, Failure, Escalation, etc.)
  config.py            # pygate.toml / pyproject.toml config loading
  constants.py         # Exit codes, default paths
  exec.py              # Subprocess execution wrapper
  env.py               # Environment detection (CI, tool availability)
  fs.py                # File operations (artifact writes)
  deterministic_fix.py # Safe ruff --fix wrapper with rollback
schemas/               # JSON schemas for all artifact types
demo/artifacts/        # Example output from each command
```

## Code Style

- Python 3.10+ required (`from __future__ import annotations` in all modules)
- Pydantic v2 `BaseModel` for all structured data (not dataclasses)
- `str(Enum)` for status values (`GateStatus.PASS`, `RunMode.CANARY`, etc.)
- Ruff line length: 120, rules: `E, F, W, I, UP, B, SIM`
- Pyright basic mode
- Build system: hatchling

Good:
```python
from pydantic import BaseModel, Field

class GateResult(BaseModel):
    gate: str
    status: GateStatus
    failures: list[Failure] = Field(default_factory=list)
    duration_ms: int = 0
```

Bad:
```python
# Don't use raw dicts for gate results
result = {"gate": "ruff", "status": "pass", "failures": []}

# Don't use dataclasses — this project uses Pydantic
@dataclass
class GateResult:
    gate: str
```

## Git Workflow

- Branch from `main`
- Conventional commits: `feat:`, `fix:`, `test:`, `docs:`, `chore:`
- Run `pytest` and `ruff check` before pushing
- JSON schemas in `schemas/` must stay in sync with Pydantic models in `models.py`

## Boundaries

**Always:**
- Run `pytest` after modifying source files
- Keep Pydantic v2 as the modeling library
- Maintain Python 3.10+ compatibility
- Update JSON schemas when changing Pydantic models
- Use `from __future__ import annotations` in every module

**Ask first:**
- Adding new runtime dependencies (currently only pydantic + tomli)
- Adding new gate types (ruff/pyright/pytest are the current three)
- Changing exit codes in `constants.py`
- Modifying the repair loop bounds or retry logic
- Changing artifact output format (breaks downstream consumers)

**Never:**
- Execute subprocess commands in tests (all gate outputs are mocked)
- Use dataclasses instead of Pydantic models
- Remove or weaken the bounded repair loop (max-attempts is a safety constraint)
- Commit real project output to `demo/artifacts/` (use synthetic examples)
- Break JSON schema backward compatibility without a version bump
