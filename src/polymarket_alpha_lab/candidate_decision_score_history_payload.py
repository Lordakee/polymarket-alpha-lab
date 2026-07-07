"""JSON-ready aggregate payload for candidate decision score history reports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from polymarket_alpha_lab.candidate_decision_score_history import (
    CandidateDecisionScoreHistoryActionCount,
    CandidateDecisionScoreHistoryReasonCodeCount,
    CandidateDecisionScoreHistoryReport,
    CandidateDecisionScoreHistoryTeamCount,
)


def candidate_decision_score_history_payload(
    report: CandidateDecisionScoreHistoryReport,
) -> dict[str, Any]:
    if type(report) is not CandidateDecisionScoreHistoryReport:
        raise ValueError("report must be a CandidateDecisionScoreHistoryReport")
    _require_hard_flags("history_report", report)

    payload: dict[str, Any] = {
        "generated_at": _json_value(report.generated_at),
        "status": report.status,
        "report_count": _json_value(report.report_count),
        "latest_generated_at": _json_value(report.latest_generated_at),
        "action_counts": [_action_count_payload(row) for row in report.action_counts],
        "reason_counts": [_reason_count_payload(row) for row in report.reason_counts],
        "primary_team_counts": [
            _team_count_payload(row) for row in report.primary_team_counts
        ],
        "source_report_count": _json_value(report.source_report_count),
        "candidate_count": _json_value(report.candidate_count),
        "action_reject_count": _json_value(report.action_reject_count),
        "action_watch_count": _json_value(report.action_watch_count),
        "action_research_more_count": _json_value(report.action_research_more_count),
        "action_paper_recommend_count": _json_value(
            report.action_paper_recommend_count,
        ),
        "hard_blocked_count": _json_value(report.hard_blocked_count),
        "blocked_total": _json_value(report.blocked_total),
        "watch_total": _json_value(report.watch_total),
        "paper_recommend_total": _json_value(report.paper_recommend_total),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    _require_hard_flags("payload", _DictFlags(payload))
    return payload


def _action_count_payload(
    row: CandidateDecisionScoreHistoryActionCount,
) -> dict[str, str]:
    if type(row) is not CandidateDecisionScoreHistoryActionCount:
        raise ValueError("action_counts must contain history action count rows")
    _require_hard_flags("action_count", row)
    return {
        "action": row.action,
        "count": _json_decimal(row.count),
    }


def _reason_count_payload(
    row: CandidateDecisionScoreHistoryReasonCodeCount,
) -> dict[str, str]:
    if type(row) is not CandidateDecisionScoreHistoryReasonCodeCount:
        raise ValueError("reason_counts must contain history reason count rows")
    _require_hard_flags("reason_count", row)
    return {
        "reason_code": row.reason_code,
        "count": _json_decimal(row.count),
    }


def _team_count_payload(row: CandidateDecisionScoreHistoryTeamCount) -> dict[str, str]:
    if type(row) is not CandidateDecisionScoreHistoryTeamCount:
        raise ValueError("primary_team_counts must contain history team count rows")
    _require_hard_flags("team_count", row)
    return {
        "team_id": row.team_id,
        "count": _json_decimal(row.count),
    }


def _json_value(value: object) -> object:
    if value is None:
        return None
    if type(value) is datetime:
        return value.isoformat()
    if type(value) is Decimal:
        return _json_decimal(value)
    if type(value) in (str, bool):
        return value
    raise ValueError("payload value must be aggregate JSON-ready")


def _json_decimal(value: Decimal) -> str:
    if type(value) is not Decimal:
        raise ValueError("payload decimal must be a Decimal")
    if not value.is_finite():
        raise ValueError("payload decimal must be finite")
    return format(value, "f")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} must be {flag_name}")


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


__all__ = ("candidate_decision_score_history_payload",)
