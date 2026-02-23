from __future__ import annotations

from pathlib import Path

from pygate.config import load_config
from pygate.constants import AGENT_BRIEF_JSON_FILE, AGENT_BRIEF_MD_FILE, PYGATE_DIR, EscalationCode
from pygate.fs import ensure_dir, read_json, write_json, write_text
from pygate.models import (
    ActionScope,
    AgentBrief,
    EscalationInfo,
    FailuresPayload,
    PriorityAction,
    RetryPolicy,
    RunStatus,
)

_GATE_ACTIONS: dict[str, str] = {
    "lint": "Apply targeted ruff fixes and re-run lint deterministically.",
    "typecheck": "Resolve Pyright type errors for impacted files and re-run typecheck.",
    "test": "Fix failing tests and ensure pytest passes.",
}


def _scope_for_finding(finding_files: list[str]) -> ActionScope:
    if len(finding_files) == 1:
        return ActionScope.SINGLE_FILE
    if len(finding_files) <= 3:
        return ActionScope.MULTI_FILE
    return ActionScope.CROSS_MODULE


def execute_summarize(*, input_path: str, cwd: Path | None = None) -> dict:
    cwd = cwd or Path.cwd()
    pygate_dir = cwd / PYGATE_DIR
    ensure_dir(pygate_dir)

    config = load_config(cwd)
    policy = config.get("policy", {})

    failures_data = read_json(Path(input_path))
    failures = FailuresPayload(**failures_data)

    priority_actions = [
        PriorityAction(
            finding_id=f.id,
            action=_GATE_ACTIONS.get(f.gate.value, f"Address {f.gate.value} failure."),
            scope=_scope_for_finding(f.files),
            target_files=f.files,
            rationale=f"{f.gate.value} failed deterministically. Address this before any inferred optimizations.",
        )
        for f in failures.findings
    ]

    count = len(failures.findings)
    summary = (
        "All deterministic gates passed."
        if failures.status == RunStatus.PASS
        else f"{count} deterministic finding(s) require repair."
    )

    escalation = (
        EscalationInfo(required=False)
        if failures.status == RunStatus.PASS
        else EscalationInfo(
            required=True,
            reason_code=EscalationCode.UNRESOLVED_DETERMINISTIC_FAILURES,
            message="Escalate with evidence packet if bounded repair loop cannot clear deterministic failures.",
        )
    )

    brief = AgentBrief(
        run_id=failures.run_id,
        mode=failures.mode,
        status=failures.status,
        summary=summary,
        priority_actions=priority_actions,
        retry_policy=RetryPolicy(
            max_attempts=policy.get("max_attempts", 3),
            max_patch_lines=policy.get("max_patch_lines", 150),
            abort_on_no_improvement=policy.get("abort_on_no_improvement", 2),
        ),
        escalation=escalation,
    )

    brief_json_path = cwd / AGENT_BRIEF_JSON_FILE
    brief_md_path = cwd / AGENT_BRIEF_MD_FILE

    write_json(brief_json_path, brief.model_dump(mode="json"))
    write_text(brief_md_path, _generate_markdown(brief, failures))

    return {
        "brief_json_path": str(brief_json_path),
        "brief_md_path": str(brief_md_path),
        "status": brief.status.value,
    }


def _generate_markdown(brief: AgentBrief, failures: FailuresPayload) -> str:
    lines = [
        f"# PyGate Agent Brief — {brief.run_id}",
        "",
        f"**Mode:** {brief.mode.value}  ",
        f"**Status:** {brief.status.value}  ",
        f"**Summary:** {brief.summary}",
        "",
    ]

    if brief.priority_actions:
        lines.append("## Findings & Actions")
        lines.append("")
        for action in brief.priority_actions:
            lines.append(f"### `{action.finding_id}`")
            lines.append(f"- **Action:** {action.action}")
            lines.append(f"- **Scope:** {action.scope.value}")
            if action.target_files:
                lines.append(f"- **Files:** {', '.join(action.target_files)}")
            lines.append(f"- **Rationale:** {action.rationale}")
            lines.append("")

    lines.append("## Retry Policy")
    lines.append("")
    lines.append(f"- Max attempts: {brief.retry_policy.max_attempts}")
    lines.append(f"- Max patch lines: {brief.retry_policy.max_patch_lines}")
    lines.append(f"- Abort on no improvement: {brief.retry_policy.abort_on_no_improvement} consecutive attempts")
    lines.append("")

    if brief.escalation:
        lines.append("## Escalation")
        lines.append("")
        lines.append(f"- Required: {brief.escalation.required}")
        if brief.escalation.reason_code:
            lines.append(f"- Reason: {brief.escalation.reason_code}")
        if brief.escalation.message:
            lines.append(f"- Message: {brief.escalation.message}")
        lines.append("")

    return "\n".join(lines)
