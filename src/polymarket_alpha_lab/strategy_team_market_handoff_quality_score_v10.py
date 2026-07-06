"""Pure paper/report/readonly team market handoff quality score v10 evaluator."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


__all__ = (
    "CONFIG_VERSION",
    "HANDOFF_STATUSES",
    "HANDOFF_QUALITY_STATUSES",
    "REPAIR_ACTIONS",
    "StrategyTeamMarketHandoffQualityScoreV10Input",
    "StrategyTeamMarketHandoffQualityScoreV10Report",
    "strategy_team_market_handoff_quality_score_v10",
    "strategy_team_market_handoff_quality_score_v10_payload",
)


CONFIG_VERSION = "strategy-team-market-handoff-quality-score-v10"

DECIMAL_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECTION_EVIDENCE_BASE = Decimal("8.000000")
URGENT_DEADLINE_MINUTES = Decimal("30.000000")
COMPRESSED_DEADLINE_MINUTES = Decimal("60.000000")
OPEN_DEADLINE_MINUTES = Decimal("120.000000")
HIGH_EVIDENCE_GAP_COUNT = Decimal("3.000000")

SECTION_WEIGHT = Decimal("0.900000")
EVIDENCE_WEIGHT = Decimal("0.016667")
DEADLINE_WEIGHT = Decimal("0.041666")
STATUS_WEIGHT = Decimal("0.041667")

COMPLETE_SCORE_FLOOR = Decimal("0.850000")
REPAIR_SCORE_FLOOR = Decimal("0.500000")

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

HANDOFF_STATUSES = ("ready", "in_review", "blocked")
HANDOFF_QUALITY_STATUSES = ("complete", "repair", "blocked")
REPAIR_ACTIONS = (
    "accept_handoff",
    "finish_handoff_review",
    "complete_required_sections",
    "close_evidence_gaps",
    "expedite_deadline_review",
    "block_handoff_until_repaired",
)
SENSITIVE_MARKERS = (
    "secret",
    "password",
    "passwd",
    "api_key",
    "apikey",
    "private_key",
    "access_key",
    "access_token",
    "bearer ",
    "://",
    "@",
)


@dataclass(frozen=True)
class StrategyTeamMarketHandoffQualityScoreV10Input:
    market_id: str
    from_team: str
    to_team: str
    handoff_status: str
    required_section_count: Decimal
    completed_section_count: Decimal
    evidence_gap_count: Decimal
    deadline_minutes: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_id", self.market_id)
        _require_canonical_string("from_team", self.from_team)
        _require_canonical_string("to_team", self.to_team)
        if self.from_team == self.to_team:
            raise ValueError("from_team and to_team must differ")
        object.__setattr__(
            self,
            "handoff_status",
            _require_member("handoff_status", self.handoff_status, HANDOFF_STATUSES),
        )
        object.__setattr__(
            self,
            "required_section_count",
            _normalize_positive_whole_decimal(
                "required_section_count",
                self.required_section_count,
            ),
        )
        for field_name in (
            "completed_section_count",
            "evidence_gap_count",
            "deadline_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        if self.completed_section_count > self.required_section_count:
            raise ValueError(
                "completed_section_count must not exceed required_section_count",
            )
        _require_safety_flags("input", self)


@dataclass(frozen=True)
class StrategyTeamMarketHandoffQualityScoreV10Report:
    market_id: str
    from_team: str
    to_team: str
    handoff_status: str
    required_section_count: Decimal
    completed_section_count: Decimal
    evidence_gap_count: Decimal
    deadline_minutes: Decimal
    handoff_quality_status: str
    handoff_quality_score: Decimal
    repair_actions: tuple[str, ...]
    reason_codes: tuple[str, ...]
    config_version: str = CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_id", self.market_id)
        _require_canonical_string("from_team", self.from_team)
        _require_canonical_string("to_team", self.to_team)
        if self.from_team == self.to_team:
            raise ValueError("from_team and to_team must differ")
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "handoff_status",
            _require_member("handoff_status", self.handoff_status, HANDOFF_STATUSES),
        )
        object.__setattr__(
            self,
            "required_section_count",
            _normalize_positive_whole_decimal(
                "required_section_count",
                self.required_section_count,
            ),
        )
        for field_name in (
            "completed_section_count",
            "evidence_gap_count",
            "deadline_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        if self.completed_section_count > self.required_section_count:
            raise ValueError(
                "completed_section_count must not exceed required_section_count",
            )
        object.__setattr__(
            self,
            "handoff_quality_status",
            _require_member(
                "handoff_quality_status",
                self.handoff_quality_status,
                HANDOFF_QUALITY_STATUSES,
            ),
        )
        object.__setattr__(
            self,
            "handoff_quality_score",
            _normalize_probability_decimal(
                "handoff_quality_score",
                self.handoff_quality_score,
            ),
        )
        object.__setattr__(
            self,
            "repair_actions",
            _normalize_known_strings("repair_actions", self.repair_actions, REPAIR_ACTIONS),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        _require_safety_flags("report", self)

    @property
    def payload(self) -> dict[str, Any]:
        return strategy_team_market_handoff_quality_score_v10_payload(self)


def strategy_team_market_handoff_quality_score_v10(
    handoff: StrategyTeamMarketHandoffQualityScoreV10Input,
) -> StrategyTeamMarketHandoffQualityScoreV10Report:
    if type(handoff) is not StrategyTeamMarketHandoffQualityScoreV10Input:
        raise ValueError(
            "handoff must be a StrategyTeamMarketHandoffQualityScoreV10Input",
        )
    _require_safety_flags("handoff", handoff)
    quality_score = _handoff_quality_score(handoff)
    quality_status = _handoff_quality_status(handoff, quality_score)
    return StrategyTeamMarketHandoffQualityScoreV10Report(
        market_id=handoff.market_id,
        from_team=handoff.from_team,
        to_team=handoff.to_team,
        handoff_status=handoff.handoff_status,
        required_section_count=handoff.required_section_count,
        completed_section_count=handoff.completed_section_count,
        evidence_gap_count=handoff.evidence_gap_count,
        deadline_minutes=handoff.deadline_minutes,
        handoff_quality_status=quality_status,
        handoff_quality_score=quality_score,
        repair_actions=_repair_actions(handoff, quality_status),
        reason_codes=_reason_codes(handoff),
    )


def strategy_team_market_handoff_quality_score_v10_payload(
    report: StrategyTeamMarketHandoffQualityScoreV10Report,
) -> dict[str, Any]:
    if type(report) is not StrategyTeamMarketHandoffQualityScoreV10Report:
        raise ValueError("report must be a StrategyTeamMarketHandoffQualityScoreV10Report")
    _require_safety_flags("report", report)
    return {
        "config_version": report.config_version,
        "market_id": report.market_id,
        "from_team": report.from_team,
        "to_team": report.to_team,
        "handoff_status": report.handoff_status,
        "required_section_count": _decimal_payload(report.required_section_count),
        "completed_section_count": _decimal_payload(report.completed_section_count),
        "evidence_gap_count": _decimal_payload(report.evidence_gap_count),
        "deadline_minutes": _decimal_payload(report.deadline_minutes),
        "handoff_quality_status": report.handoff_quality_status,
        "handoff_quality_score": _decimal_payload(report.handoff_quality_score),
        "repair_actions": list(report.repair_actions),
        "reason_codes": list(report.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _handoff_quality_score(
    handoff: StrategyTeamMarketHandoffQualityScoreV10Input,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        total = (
            _section_completion_score(handoff) * SECTION_WEIGHT
            + _evidence_gap_score(handoff.evidence_gap_count) * EVIDENCE_WEIGHT
            + _deadline_score(handoff.deadline_minutes) * DEADLINE_WEIGHT
            + _handoff_status_score(handoff.handoff_status) * STATUS_WEIGHT
        )
        if total > ONE:
            return ONE
        if total < ZERO:
            return ZERO
        return total.quantize(DECIMAL_QUANTUM)


def _handoff_quality_status(
    handoff: StrategyTeamMarketHandoffQualityScoreV10Input,
    quality_score: Decimal,
) -> str:
    if handoff.handoff_status == "blocked":
        return "blocked"
    if (
        quality_score >= COMPLETE_SCORE_FLOOR
        and handoff.completed_section_count == handoff.required_section_count
        and handoff.evidence_gap_count == ZERO
    ):
        return "complete"
    if quality_score >= REPAIR_SCORE_FLOOR:
        return "repair"
    return "blocked"


def _repair_actions(
    handoff: StrategyTeamMarketHandoffQualityScoreV10Input,
    quality_status: str,
) -> tuple[str, ...]:
    actions: list[str] = []
    if quality_status == "blocked":
        actions.append("block_handoff_until_repaired")
    if handoff.completed_section_count < handoff.required_section_count:
        actions.append("complete_required_sections")
    if handoff.evidence_gap_count > ZERO:
        actions.append("close_evidence_gaps")
    if handoff.deadline_minutes <= COMPRESSED_DEADLINE_MINUTES:
        actions.append("expedite_deadline_review")
    if not actions:
        if handoff.handoff_status == "in_review":
            actions.append("finish_handoff_review")
        else:
            actions.append("accept_handoff")
    return _normalize_known_strings("repair_actions", tuple(actions), REPAIR_ACTIONS)


def _reason_codes(
    handoff: StrategyTeamMarketHandoffQualityScoreV10Input,
) -> tuple[str, ...]:
    return _normalize_reason_codes(
        (
            f"sections_{_section_bucket(handoff)}",
            f"evidence_gap_{_evidence_gap_bucket(handoff.evidence_gap_count)}",
            f"deadline_window_{_deadline_bucket(handoff.deadline_minutes)}",
            f"handoff_{handoff.handoff_status}",
        ),
    )


def _section_completion_score(
    handoff: StrategyTeamMarketHandoffQualityScoreV10Input,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _capped_probability(
            handoff.completed_section_count / handoff.required_section_count,
        )


def _evidence_gap_score(evidence_gap_count: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = ONE - (evidence_gap_count / SECTION_EVIDENCE_BASE)
        return _capped_probability(score)


def _deadline_score(deadline_minutes: Decimal) -> Decimal:
    if deadline_minutes <= URGENT_DEADLINE_MINUTES:
        return Decimal("0.250000")
    if deadline_minutes <= COMPRESSED_DEADLINE_MINUTES:
        return Decimal("0.750000")
    if deadline_minutes < OPEN_DEADLINE_MINUTES:
        return Decimal("0.875000")
    return ONE


def _handoff_status_score(handoff_status: str) -> Decimal:
    if handoff_status == "ready":
        return ONE
    if handoff_status == "in_review":
        return Decimal("0.750000")
    return Decimal("0.250000")


def _section_bucket(handoff: StrategyTeamMarketHandoffQualityScoreV10Input) -> str:
    if handoff.completed_section_count == handoff.required_section_count:
        return "complete"
    if handoff.completed_section_count == ZERO:
        return "missing"
    return "partial"


def _evidence_gap_bucket(evidence_gap_count: Decimal) -> str:
    if evidence_gap_count == ZERO:
        return "none"
    if evidence_gap_count >= HIGH_EVIDENCE_GAP_COUNT:
        return "high"
    return "present"


def _deadline_bucket(deadline_minutes: Decimal) -> str:
    if deadline_minutes <= URGENT_DEADLINE_MINUTES:
        return "urgent"
    if deadline_minutes <= COMPRESSED_DEADLINE_MINUTES:
        return "compressed"
    return "open"


def _validate_report(report: StrategyTeamMarketHandoffQualityScoreV10Report) -> None:
    handoff = StrategyTeamMarketHandoffQualityScoreV10Input(
        market_id=report.market_id,
        from_team=report.from_team,
        to_team=report.to_team,
        handoff_status=report.handoff_status,
        required_section_count=report.required_section_count,
        completed_section_count=report.completed_section_count,
        evidence_gap_count=report.evidence_gap_count,
        deadline_minutes=report.deadline_minutes,
    )
    expected_score = _handoff_quality_score(handoff)
    expected_status = _handoff_quality_status(handoff, expected_score)
    if report.handoff_quality_score != expected_score:
        raise ValueError("handoff_quality_score must match input fields")
    if report.handoff_quality_status != expected_status:
        raise ValueError("handoff_quality_status must match input fields")
    if report.repair_actions != _repair_actions(handoff, expected_status):
        raise ValueError("repair_actions must match input fields")
    if report.reason_codes != _reason_codes(handoff):
        raise ValueError("reason_codes must match input fields")


def _normalize_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_whole_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value().quantize(DECIMAL_QUANTUM):
        raise ValueError(f"{field_name} must be whole")
    return decimal_value


def _normalize_probability_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    decimal_value = value.quantize(DECIMAL_QUANTUM)
    if decimal_value != value:
        raise ValueError(f"{field_name} must use the required decimal precision")
    return decimal_value


def _capped_probability(value: Decimal) -> Decimal:
    if value > ONE:
        return ONE
    if value < ZERO:
        return ZERO
    return value.quantize(DECIMAL_QUANTUM)


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> str:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a known value")
    return value


def _normalize_known_strings(
    field_name: str,
    values: object,
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not values:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    normalized: list[str] = []
    for item in values:
        _require_member(field_name, item, allowed_values)
        if item in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(item)
        normalized.append(item)
    return tuple(normalized)


def _normalize_reason_codes(values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not values:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    normalized: list[str] = []
    for reason_code in values:
        _require_canonical_string("reason_codes", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
        normalized.append(reason_code)
    return tuple(normalized)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _reject_unsafe_text(value)


def _require_safety_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if not hasattr(value, field_name):
            raise ValueError(f"{label} must expose {field_name}")
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _reject_unsafe_text(value: str) -> None:
    lowered = value.lower()
    if any(marker in lowered for marker in SENSITIVE_MARKERS):
        raise ValueError("must not contain sensitive material")


def _decimal_payload(value: Decimal) -> str:
    if type(value) is not Decimal:
        raise ValueError("payload decimal must be a Decimal")
    return format(value, "f")
