# PyGate Agent Brief — run_20260223140000_a1b2c3d4

**Mode:** canary
**Status:** fail
**Summary:** 3 deterministic finding(s) require repair.

## Findings & Actions

### `ruff_F401_src/auth.py_3_0`
- **Action:** Apply targeted ruff fixes and re-run lint deterministically.
- **Scope:** single_file
- **Files:** src/auth.py
- **Rationale:** lint failed deterministically. Address this before any inferred optimizations.

### `ruff_E501_src/middleware.py_47_1`
- **Action:** Apply targeted ruff fixes and re-run lint deterministically.
- **Scope:** single_file
- **Files:** src/middleware.py
- **Rationale:** lint failed deterministically. Address this before any inferred optimizations.

### `pyright_reportAttributeAccessIssue_src/auth.py_22`
- **Action:** Resolve Pyright type errors for impacted files and re-run typecheck.
- **Scope:** single_file
- **Files:** src/auth.py
- **Rationale:** typecheck failed deterministically. Address this before any inferred optimizations.

## Retry Policy

- Max attempts: 3
- Max patch lines: 150
- Abort on no improvement: 2 consecutive attempts

## Escalation

- Required: True
- Reason: UNRESOLVED_DETERMINISTIC_FAILURES
- Message: Escalate with evidence packet if bounded repair loop cannot clear deterministic failures.
