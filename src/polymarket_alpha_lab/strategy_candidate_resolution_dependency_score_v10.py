"""Pure report-only dependency scoring for candidate resolution checks."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import Any


DEPENDENCY_STATUSES = ("pass", "watch", "blocked")
RULE_CHANGE_STATUSES = ("stable", "pending_review", "unacknowledged_change")

REQUIRED_FOLLOWUPS = (
    "confirm_critical_external_dependency",
    "refresh_official_resolution_source",
    "reduce_source_dependency_penalty",
    "complete_resolution_check_before_close",
    "review_resolution_rule_change_status",
)

REASON_CODES = (
    "dependency_clear",
    "external_dependency_present",
    "critical_dependency_present",
    "official_source_gap",
    "source_dependency_penalty_high",
    "near_resolution_window",
    "resolution_imminent",
    "resolution_rule_change_pending_review",
    "resolution_rule_change_unacknowledged",
)

SCORE_QUANT = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")


@dataclass(frozen=True)
class StrategyCandidateResolutionDependencyScoreV10Input:
    market_id: str
    dependency_count: Decimal
    critical_dependency_count: Decimal
    official_source_score: Decimal
    source_dependency_penalty: Decimal
    time_to_resolution_minutes: Decimal
    rule_change_status: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateResolutionDependencyScoreV10Input:
            raise ValueError("input must be a StrategyCandidateResolutionDependencyScoreV10Input")
        _require_canonical_string("market_id", self.market_id)
        _require_whole_decimal_count("dependency_count", self.dependency_count)
        _require_whole_decimal_count(
            "critical_dependency_count",
            self.critical_dependency_count,
        )
        _require_ratio_decimal("official_source_score", self.official_source_score)
        _require_ratio_decimal(
            "source_dependency_penalty",
            self.source_dependency_penalty,
        )
        _require_nonnegative_decimal(
            "time_to_resolution_minutes",
            self.time_to_resolution_minutes,
        )
        _require_member("rule_change_status", self.rule_change_status, RULE_CHANGE_STATUSES)
        if self.critical_dependency_count > self.dependency_count:
            raise ValueError("critical_dependency_count must not exceed dependency_count")
        _require_hard_flags(self)


@dataclass(frozen=True)
class StrategyCandidateResolutionDependencyScoreV10Report:
    market_id: str
    dependency_count: Decimal
    critical_dependency_count: Decimal
    official_source_score: Decimal
    source_dependency_penalty: Decimal
    time_to_resolution_minutes: Decimal
    rule_change_status: str
    dependency_status: str
    dependency_score: Decimal
    required_followups: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateResolutionDependencyScoreV10Report:
            raise ValueError("report must be a StrategyCandidateResolutionDependencyScoreV10Report")
        _require_canonical_string("market_id", self.market_id)
        _require_whole_decimal_count("dependency_count", self.dependency_count)
        _require_whole_decimal_count(
            "critical_dependency_count",
            self.critical_dependency_count,
        )
        _require_ratio_decimal("official_source_score", self.official_source_score)
        _require_ratio_decimal(
            "source_dependency_penalty",
            self.source_dependency_penalty,
        )
        _require_nonnegative_decimal(
            "time_to_resolution_minutes",
            self.time_to_resolution_minutes,
        )
        _require_member("rule_change_status", self.rule_change_status, RULE_CHANGE_STATUSES)
        _require_member("dependency_status", self.dependency_status, DEPENDENCY_STATUSES)
        _require_ratio_decimal("dependency_score", self.dependency_score)
        object.__setattr__(
            self,
            "required_followups",
            _normalize_string_tuple(
                "required_followups",
                self.required_followups,
                REQUIRED_FOLLOWUPS,
                allow_empty=True,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_string_tuple(
                "reason_codes",
                self.reason_codes,
                REASON_CODES,
                allow_empty=False,
            ),
        )
        if self.critical_dependency_count > self.dependency_count:
            raise ValueError("critical_dependency_count must not exceed dependency_count")

        expected_score = _dependency_score(
            dependency_count=self.dependency_count,
            critical_dependency_count=self.critical_dependency_count,
            official_source_score=self.official_source_score,
            source_dependency_penalty=self.source_dependency_penalty,
            time_to_resolution_minutes=self.time_to_resolution_minutes,
            rule_change_status=self.rule_change_status,
        )
        if self.dependency_score != expected_score:
            raise ValueError("dependency_score must match dependency inputs")

        expected_status = _dependency_status(
            dependency_score=self.dependency_score,
            critical_dependency_count=self.critical_dependency_count,
            rule_change_status=self.rule_change_status,
        )
        if self.dependency_status != expected_status:
            raise ValueError("dependency_status must match dependency inputs")

        expected_followups = _required_followups(
            critical_dependency_count=self.critical_dependency_count,
            official_source_score=self.official_source_score,
            source_dependency_penalty=self.source_dependency_penalty,
            time_to_resolution_minutes=self.time_to_resolution_minutes,
            rule_change_status=self.rule_change_status,
        )
        if self.required_followups != expected_followups:
            raise ValueError("required_followups must match dependency inputs")

        expected_reason_codes = _reason_codes(
            dependency_count=self.dependency_count,
            critical_dependency_count=self.critical_dependency_count,
            official_source_score=self.official_source_score,
            source_dependency_penalty=self.source_dependency_penalty,
            time_to_resolution_minutes=self.time_to_resolution_minutes,
            rule_change_status=self.rule_change_status,
        )
        if self.reason_codes != expected_reason_codes:
            raise ValueError("reason_codes must match dependency inputs")
        _require_hard_flags(self)

    @property
    def payload(self) -> dict[str, Any]:
        return _payload_value(asdict(self))


def build_strategy_candidate_resolution_dependency_score_v10_report(
    *,
    market_id: str,
    dependency_count: Decimal,
    critical_dependency_count: Decimal,
    official_source_score: Decimal,
    source_dependency_penalty: Decimal,
    time_to_resolution_minutes: Decimal,
    rule_change_status: str,
) -> StrategyCandidateResolutionDependencyScoreV10Report:
    input_row = StrategyCandidateResolutionDependencyScoreV10Input(
        market_id=market_id,
        dependency_count=dependency_count,
        critical_dependency_count=critical_dependency_count,
        official_source_score=official_source_score,
        source_dependency_penalty=source_dependency_penalty,
        time_to_resolution_minutes=time_to_resolution_minutes,
        rule_change_status=rule_change_status,
    )
    score = _dependency_score(
        dependency_count=input_row.dependency_count,
        critical_dependency_count=input_row.critical_dependency_count,
        official_source_score=input_row.official_source_score,
        source_dependency_penalty=input_row.source_dependency_penalty,
        time_to_resolution_minutes=input_row.time_to_resolution_minutes,
        rule_change_status=input_row.rule_change_status,
    )

    return StrategyCandidateResolutionDependencyScoreV10Report(
        market_id=input_row.market_id,
        dependency_count=input_row.dependency_count,
        critical_dependency_count=input_row.critical_dependency_count,
        official_source_score=input_row.official_source_score,
        source_dependency_penalty=input_row.source_dependency_penalty,
        time_to_resolution_minutes=input_row.time_to_resolution_minutes,
        rule_change_status=input_row.rule_change_status,
        dependency_status=_dependency_status(
            dependency_score=score,
            critical_dependency_count=input_row.critical_dependency_count,
            rule_change_status=input_row.rule_change_status,
        ),
        dependency_score=score,
        required_followups=_required_followups(
            critical_dependency_count=input_row.critical_dependency_count,
            official_source_score=input_row.official_source_score,
            source_dependency_penalty=input_row.source_dependency_penalty,
            time_to_resolution_minutes=input_row.time_to_resolution_minutes,
            rule_change_status=input_row.rule_change_status,
        ),
        reason_codes=_reason_codes(
            dependency_count=input_row.dependency_count,
            critical_dependency_count=input_row.critical_dependency_count,
            official_source_score=input_row.official_source_score,
            source_dependency_penalty=input_row.source_dependency_penalty,
            time_to_resolution_minutes=input_row.time_to_resolution_minutes,
            rule_change_status=input_row.rule_change_status,
        ),
    )


def strategy_candidate_resolution_dependency_score_v10_payload(
    report: StrategyCandidateResolutionDependencyScoreV10Report,
) -> dict[str, Any]:
    if type(report) is not StrategyCandidateResolutionDependencyScoreV10Report:
        raise ValueError("report must be a StrategyCandidateResolutionDependencyScoreV10Report")
    _require_hard_flags(report)
    return report.payload


def _dependency_score(
    *,
    dependency_count: Decimal,
    critical_dependency_count: Decimal,
    official_source_score: Decimal,
    source_dependency_penalty: Decimal,
    time_to_resolution_minutes: Decimal,
    rule_change_status: str,
) -> Decimal:
    score = (
        min(dependency_count, Decimal("5")) * Decimal("0.040000")
        + min(critical_dependency_count, Decimal("3")) * Decimal("0.165000")
        + (ONE - official_source_score) * Decimal("0.200000")
        + source_dependency_penalty * Decimal("0.250000")
        + _time_window_score(time_to_resolution_minutes)
        + _rule_change_score(rule_change_status)
    )
    return min(max(score, ZERO), ONE).quantize(SCORE_QUANT)


def _dependency_status(
    *,
    dependency_score: Decimal,
    critical_dependency_count: Decimal,
    rule_change_status: str,
) -> str:
    if critical_dependency_count > ZERO:
        return "blocked"
    if rule_change_status == "unacknowledged_change":
        return "blocked"
    if dependency_score >= Decimal("0.700000"):
        return "blocked"
    if dependency_score > ZERO:
        return "watch"
    return "pass"


def _required_followups(
    *,
    critical_dependency_count: Decimal,
    official_source_score: Decimal,
    source_dependency_penalty: Decimal,
    time_to_resolution_minutes: Decimal,
    rule_change_status: str,
) -> tuple[str, ...]:
    values: list[str] = []
    if critical_dependency_count > ZERO:
        values.append("confirm_critical_external_dependency")
    if official_source_score < Decimal("0.750000"):
        values.append("refresh_official_resolution_source")
    if source_dependency_penalty >= Decimal("0.750000"):
        values.append("reduce_source_dependency_penalty")
    if time_to_resolution_minutes <= Decimal("180"):
        values.append("complete_resolution_check_before_close")
    if rule_change_status != "stable":
        values.append("review_resolution_rule_change_status")
    return tuple(values)


def _reason_codes(
    *,
    dependency_count: Decimal,
    critical_dependency_count: Decimal,
    official_source_score: Decimal,
    source_dependency_penalty: Decimal,
    time_to_resolution_minutes: Decimal,
    rule_change_status: str,
) -> tuple[str, ...]:
    values: list[str] = []
    if dependency_count > ZERO:
        values.append("external_dependency_present")
    if critical_dependency_count > ZERO:
        values.append("critical_dependency_present")
    if official_source_score < Decimal("0.750000"):
        values.append("official_source_gap")
    if source_dependency_penalty >= Decimal("0.750000"):
        values.append("source_dependency_penalty_high")
    if time_to_resolution_minutes <= Decimal("60"):
        values.append("resolution_imminent")
    elif time_to_resolution_minutes <= Decimal("180"):
        values.append("near_resolution_window")
    if rule_change_status == "pending_review":
        values.append("resolution_rule_change_pending_review")
    elif rule_change_status == "unacknowledged_change":
        values.append("resolution_rule_change_unacknowledged")
    if not values:
        values.append("dependency_clear")
    return tuple(values)


def _time_window_score(time_to_resolution_minutes: Decimal) -> Decimal:
    if time_to_resolution_minutes <= Decimal("60"):
        return Decimal("0.150000")
    if time_to_resolution_minutes <= Decimal("180"):
        return Decimal("0.100000")
    return ZERO


def _rule_change_score(rule_change_status: str) -> Decimal:
    if rule_change_status == "pending_review":
        return Decimal("0.060000")
    if rule_change_status == "unacknowledged_change":
        return Decimal("0.250000")
    return ZERO


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_whole_decimal_count(field_name: str, value: Decimal) -> None:
    _require_nonnegative_decimal(field_name, value)
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")


def _require_ratio_decimal(field_name: str, value: Decimal) -> None:
    _require_nonnegative_decimal(field_name, value)
    if value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")


def _require_member(field_name: str, value: str, values: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in values:
        raise ValueError(f"{field_name} must be known")


def _normalize_string_tuple(
    field_name: str,
    values: tuple[str, ...],
    allowed_values: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not allow_empty and not values:
        raise ValueError(f"{field_name} must contain at least one value")
    if len(set(values)) != len(values):
        raise ValueError(f"{field_name} must not contain duplicates")
    for value in values:
        _require_member(field_name, value, allowed_values)
    return values


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _payload_value(value: Any) -> Any:
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    return value


__all__ = (
    "DEPENDENCY_STATUSES",
    "REASON_CODES",
    "REQUIRED_FOLLOWUPS",
    "RULE_CHANGE_STATUSES",
    "StrategyCandidateResolutionDependencyScoreV10Input",
    "StrategyCandidateResolutionDependencyScoreV10Report",
    "build_strategy_candidate_resolution_dependency_score_v10_report",
    "strategy_candidate_resolution_dependency_score_v10_payload",
)
