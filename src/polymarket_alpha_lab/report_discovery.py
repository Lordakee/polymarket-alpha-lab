"""Read-only CLI discovery registry for operator-facing report entrypoints."""

from __future__ import annotations

from dataclasses import dataclass


REPORT_DISCOVERY_CATEGORIES = (
    "readiness",
    "strategy-rollups",
    "manual-review",
)


@dataclass(frozen=True)
class ReportDiscoveryEntry:
    command: str
    description: str


@dataclass(frozen=True)
class ReportDiscoveryGroup:
    category: str
    title: str
    purpose: str
    entries: tuple[ReportDiscoveryEntry, ...]


REPORT_DISCOVERY_GROUPS = (
    ReportDiscoveryGroup(
        category="readiness",
        title="Phase 1 readiness reports",
        purpose=(
            "Read-only paper/report-only readiness gates and digests for "
            "operator go/no-go review."
        ),
        entries=(
            ReportDiscoveryEntry(
                command="paper-autonomous-readiness-digest",
                description="Phase 1 readiness digest across autonomous paper gates.",
            ),
            ReportDiscoveryEntry(
                command="team-memory-readiness-digest",
                description="Team memory readiness digest from diagnostics gate history.",
            ),
            ReportDiscoveryEntry(
                command="paper-autonomous-allocation-proposal-db-history-health-trend-gate",
                description="Allocation proposal health trend gate for readiness drift.",
            ),
        ),
    ),
    ReportDiscoveryGroup(
        category="strategy-rollups",
        title="Critical strategy rollups",
        purpose=(
            "Read-only paper/report-only rollups that summarize strategy "
            "selection, agreement, risk, and queue posture."
        ),
        entries=(
            ReportDiscoveryEntry(
                command="probability-selection-scorer-agreement-trend-gate",
                description="Probability selection and scorer agreement trend gate.",
            ),
            ReportDiscoveryEntry(
                command="paper-probability-selection-summary-history-trend-gate",
                description="Probability selection summary history trend gate.",
            ),
            ReportDiscoveryEntry(
                command="paper-recommendation-cycle-action-gate",
                description="Recommendation cycle action gate rollup.",
            ),
            ReportDiscoveryEntry(
                command="action-gated-queue-decision-support-trend",
                description="Action-gated queue decision-support trend rollup.",
            ),
        ),
    ),
    ReportDiscoveryGroup(
        category="manual-review",
        title="Manual review packet",
        purpose=(
            "Next-step read-only paper/report-only packet commands for "
            "operator manual review."
        ),
        entries=(
            ReportDiscoveryEntry(
                command="paper-research-packet-operator-flow",
                description="Operator flow packet that queues next manual review actions.",
            ),
            ReportDiscoveryEntry(
                command="paper-research-packet-quality",
                description="Research packet quality report for manual review triage.",
            ),
            ReportDiscoveryEntry(
                command="paper-research-packet-operator-flow-db-history-gate",
                description="Operator flow history gate for manual review readiness.",
            ),
        ),
    ),
)


def report_discovery_groups(
    category: str | None = None,
) -> tuple[ReportDiscoveryGroup, ...]:
    if category is None:
        return REPORT_DISCOVERY_GROUPS
    if category not in REPORT_DISCOVERY_CATEGORIES:
        raise ValueError(f"unknown report discovery category: {category}")
    return tuple(group for group in REPORT_DISCOVERY_GROUPS if group.category == category)


def format_report_discovery(
    *,
    category: str | None = None,
    output_format: str = "text",
) -> str:
    if output_format != "text":
        raise ValueError("report discovery output format must be text")

    lines = [
        "Report discovery: read-only paper/report-only operator entrypoints",
    ]
    for group in report_discovery_groups(category):
        lines.extend(("", group.title, f"  {group.purpose}"))
        for entry in group.entries:
            lines.append(f"  - {entry.command}: {entry.description}")
    return "\n".join(lines) + "\n"
