"""Pure typed resolution ambiguity escalation v5 report reducer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_STRATEGY_RESOLUTION_AMBIGUITY_ESCALATION_V5_CONFIG_VERSION = (
    "strategy-resolution-ambiguity-escalation-v5"
)
DECIMAL_CONTEXT = Context(prec=64)
RATIO_QUANTUM = Decimal("0.000001")
SECONDS_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
ZERO_SECONDS = Decimal("0.000000")
ZERO_COUNT = Decimal("0")

SOURCE_HIERARCHY_LEVELS = (
    "primary_resolution_source",
    "secondary_resolution_source",
    "tertiary_resolution_source",
    "missing_resolution_source",
)
ESCALATION_STATUSES = ("clear", "watch", "escalate")
OWNER_TEAMS = (
    "strategy_research_team",
    "resolution_policy_team",
    "resolution_operations_team",
)
NEXT_ACTIONS = (
    "continue_paper_monitoring",
    "schedule_resolution_review",
    "escalate_for_manual_resolution_review",
)
REASON_CODES = (
    "no_resolution_ambiguity_signals_supplied",
    "question_specificity_critically_low",
    "question_specificity_low",
    "resolution_rules_critically_unclear",
    "resolution_rules_unclear",
    "source_hierarchy_missing",
    "source_hierarchy_secondary_only",
    "source_hierarchy_tertiary_only",
    "close_time_imminent",
    "close_time_inside_review_window",
    "dispute_indicators_elevated",
    "dispute_indicators_present",
    "team_confidence_critically_low",
    "team_confidence_low",
    "resolution_ambiguity_clear",
)
CRITICAL_REASON_CODES = frozenset(
    (
        "question_specificity_critically_low",
        "resolution_rules_critically_unclear",
        "source_hierarchy_missing",
        "close_time_imminent",
        "dispute_indicators_elevated",
        "team_confidence_critically_low",
    ),
)

__all__ = (
    "DEFAULT_STRATEGY_RESOLUTION_AMBIGUITY_ESCALATION_V5_CONFIG_VERSION",
    "StrategyResolutionAmbiguityEscalationV5Config",
    "StrategyResolutionAmbiguityEscalationV5Report",
    "StrategyResolutionAmbiguityEscalationV5Row",
    "StrategyResolutionAmbiguityEscalationV5Signal",
    "build_strategy_resolution_ambiguity_escalation_v5_report",
    "strategy_resolution_ambiguity_escalation_v5_payload",
)


@dataclass(frozen=True)
class StrategyResolutionAmbiguityEscalationV5Config:
    config_version: str = DEFAULT_STRATEGY_RESOLUTION_AMBIGUITY_ESCALATION_V5_CONFIG_VERSION
    question_specificity_watch_threshold: Decimal = Decimal("0.750000")
    question_specificity_escalate_threshold: Decimal = Decimal("0.500000")
    rules_clarity_watch_threshold: Decimal = Decimal("0.800000")
    rules_clarity_escalate_threshold: Decimal = Decimal("0.600000")
    close_time_watch_seconds: Decimal = Decimal("86400.000000")
    close_time_escalate_seconds: Decimal = Decimal("3600.000000")
    dispute_watch_threshold: Decimal = Decimal("1")
    dispute_escalate_threshold: Decimal = Decimal("2")
    team_confidence_watch_threshold: Decimal = Decimal("0.700000")
    team_confidence_escalate_threshold: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "question_specificity_watch_threshold",
            "question_specificity_escalate_threshold",
            "rules_clarity_watch_threshold",
            "rules_clarity_escalate_threshold",
            "team_confidence_watch_threshold",
            "team_confidence_escalate_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("close_time_watch_seconds", "close_time_escalate_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_seconds(field_name, getattr(self, field_name)),
            )
        for field_name in ("dispute_watch_threshold", "dispute_escalate_threshold"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.question_specificity_escalate_threshold > self.question_specificity_watch_threshold:
            raise ValueError("question specificity escalation threshold must not exceed watch threshold")
        if self.rules_clarity_escalate_threshold > self.rules_clarity_watch_threshold:
            raise ValueError("rules clarity escalation threshold must not exceed watch threshold")
        if self.team_confidence_escalate_threshold > self.team_confidence_watch_threshold:
            raise ValueError("team confidence escalation threshold must not exceed watch threshold")
        if self.close_time_escalate_seconds > self.close_time_watch_seconds:
            raise ValueError("close time escalation threshold must not exceed watch threshold")
        if self.dispute_escalate_threshold < self.dispute_watch_threshold:
            raise ValueError("dispute escalation threshold must not be below watch threshold")
        require_paper_only_flags("StrategyResolutionAmbiguityEscalationV5Config", self)
        reject_unsafe_surface_fields("strategy resolution ambiguity escalation v5 config", self)


@dataclass(frozen=True)
class StrategyResolutionAmbiguityEscalationV5Signal:
    case_id: str
    question_specificity_score: Decimal
    rules_clarity_score: Decimal
    source_hierarchy_level: str
    seconds_until_close: Decimal
    dispute_indicator_count: Decimal
    team_confidence_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("case_id", self.case_id)
        object.__setattr__(
            self,
            "question_specificity_score",
            _normalize_ratio("question_specificity_score", self.question_specificity_score),
        )
        object.__setattr__(
            self,
            "rules_clarity_score",
            _normalize_ratio("rules_clarity_score", self.rules_clarity_score),
        )
        _require_member(
            "source_hierarchy_level",
            self.source_hierarchy_level,
            SOURCE_HIERARCHY_LEVELS,
        )
        object.__setattr__(
            self,
            "seconds_until_close",
            _normalize_nonnegative_seconds("seconds_until_close", self.seconds_until_close),
        )
        object.__setattr__(
            self,
            "dispute_indicator_count",
            _normalize_nonnegative_count("dispute_indicator_count", self.dispute_indicator_count),
        )
        object.__setattr__(
            self,
            "team_confidence_score",
            _normalize_ratio("team_confidence_score", self.team_confidence_score),
        )
        require_paper_only_flags("StrategyResolutionAmbiguityEscalationV5Signal", self)
        reject_unsafe_surface_fields("strategy resolution ambiguity escalation v5 signal", self)


@dataclass(frozen=True)
class StrategyResolutionAmbiguityEscalationV5Row:
    case_id: str
    escalation_status: str
    owner_team: str
    next_action: str
    question_specificity_score: Decimal
    rules_clarity_score: Decimal
    source_hierarchy_level: str
    seconds_until_close: Decimal
    dispute_indicator_count: Decimal
    team_confidence_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("case_id", self.case_id)
        _require_member("escalation_status", self.escalation_status, ESCALATION_STATUSES)
        _require_member("owner_team", self.owner_team, OWNER_TEAMS)
        _require_member("next_action", self.next_action, NEXT_ACTIONS)
        object.__setattr__(
            self,
            "question_specificity_score",
            _normalize_ratio("question_specificity_score", self.question_specificity_score),
        )
        object.__setattr__(
            self,
            "rules_clarity_score",
            _normalize_ratio("rules_clarity_score", self.rules_clarity_score),
        )
        _require_member(
            "source_hierarchy_level",
            self.source_hierarchy_level,
            SOURCE_HIERARCHY_LEVELS,
        )
        object.__setattr__(
            self,
            "seconds_until_close",
            _normalize_nonnegative_seconds("seconds_until_close", self.seconds_until_close),
        )
        object.__setattr__(
            self,
            "dispute_indicator_count",
            _normalize_nonnegative_count("dispute_indicator_count", self.dispute_indicator_count),
        )
        object.__setattr__(
            self,
            "team_confidence_score",
            _normalize_ratio("team_confidence_score", self.team_confidence_score),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        if self.owner_team != _owner_team_for_status(self.escalation_status):
            raise ValueError("owner_team must match escalation_status")
        if self.next_action != _next_action_for_status(self.escalation_status):
            raise ValueError("next_action must match escalation_status")
        require_paper_only_flags("StrategyResolutionAmbiguityEscalationV5Row", self)
        reject_unsafe_surface_fields("strategy resolution ambiguity escalation v5 row", self)


@dataclass(frozen=True)
class StrategyResolutionAmbiguityEscalationV5Report:
    generated_at: datetime
    config_version: str
    escalation_status: str
    owner_team: str
    next_action: str
    signal_count: Decimal
    clear_count: Decimal
    watch_count: Decimal
    escalate_count: Decimal
    rows: tuple[StrategyResolutionAmbiguityEscalationV5Row, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_member("escalation_status", self.escalation_status, ESCALATION_STATUSES)
        _require_member("owner_team", self.owner_team, OWNER_TEAMS)
        _require_member("next_action", self.next_action, NEXT_ACTIONS)
        for field_name in ("signal_count", "clear_count", "watch_count", "escalate_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        if self.owner_team != _owner_team_for_status(self.escalation_status):
            raise ValueError("owner_team must match escalation_status")
        if self.next_action != _next_action_for_status(self.escalation_status):
            raise ValueError("next_action must match escalation_status")
        if self.signal_count != self.clear_count + self.watch_count + self.escalate_count:
            raise ValueError("status counts must sum to signal_count")
        if self.signal_count != _count(len(self.rows)):
            raise ValueError("signal_count must match rows")
        require_paper_only_flags("StrategyResolutionAmbiguityEscalationV5Report", self)


def build_strategy_resolution_ambiguity_escalation_v5_report(
    signals: tuple[StrategyResolutionAmbiguityEscalationV5Signal, ...],
    *,
    config: StrategyResolutionAmbiguityEscalationV5Config | None = None,
    generated_at: datetime,
) -> StrategyResolutionAmbiguityEscalationV5Report:
    active_config = config if config is not None else StrategyResolutionAmbiguityEscalationV5Config()
    if type(active_config) is not StrategyResolutionAmbiguityEscalationV5Config:
        raise ValueError("config must be a StrategyResolutionAmbiguityEscalationV5Config")
    generated_at = _as_utc("generated_at", generated_at)
    normalized_signals = _normalize_signals(signals)
    rows = tuple(
        sorted(
            (_row_for_signal(signal, active_config) for signal in normalized_signals),
            key=_row_sort_key,
        ),
    )
    clear_count = _count(sum(row.escalation_status == "clear" for row in rows))
    watch_count = _count(sum(row.escalation_status == "watch" for row in rows))
    escalate_count = _count(sum(row.escalation_status == "escalate" for row in rows))
    report_status = _report_status(clear_count, watch_count, escalate_count)
    return StrategyResolutionAmbiguityEscalationV5Report(
        generated_at=generated_at,
        config_version=active_config.config_version,
        escalation_status=report_status,
        owner_team=_owner_team_for_status(report_status),
        next_action=_next_action_for_status(report_status),
        signal_count=_count(len(rows)),
        clear_count=clear_count,
        watch_count=watch_count,
        escalate_count=escalate_count,
        rows=rows,
        reason_codes=_report_reason_codes(rows),
    )


def strategy_resolution_ambiguity_escalation_v5_payload(
    report: StrategyResolutionAmbiguityEscalationV5Report,
) -> dict[str, Any]:
    if type(report) is not StrategyResolutionAmbiguityEscalationV5Report:
        raise ValueError("report must be a StrategyResolutionAmbiguityEscalationV5Report")
    require_paper_only_flags("StrategyResolutionAmbiguityEscalationV5Report", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _row_for_signal(
    signal: StrategyResolutionAmbiguityEscalationV5Signal,
    config: StrategyResolutionAmbiguityEscalationV5Config,
) -> StrategyResolutionAmbiguityEscalationV5Row:
    reason_codes = _reason_codes_for_signal(signal, config)
    status = _status_for_reason_codes(reason_codes)
    return StrategyResolutionAmbiguityEscalationV5Row(
        case_id=signal.case_id,
        escalation_status=status,
        owner_team=_owner_team_for_status(status),
        next_action=_next_action_for_status(status),
        question_specificity_score=signal.question_specificity_score,
        rules_clarity_score=signal.rules_clarity_score,
        source_hierarchy_level=signal.source_hierarchy_level,
        seconds_until_close=signal.seconds_until_close,
        dispute_indicator_count=signal.dispute_indicator_count,
        team_confidence_score=signal.team_confidence_score,
        reason_codes=reason_codes,
    )


def _reason_codes_for_signal(
    signal: StrategyResolutionAmbiguityEscalationV5Signal,
    config: StrategyResolutionAmbiguityEscalationV5Config,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if signal.question_specificity_score <= config.question_specificity_escalate_threshold:
        reason_codes.append("question_specificity_critically_low")
    elif signal.question_specificity_score < config.question_specificity_watch_threshold:
        reason_codes.append("question_specificity_low")

    if signal.rules_clarity_score <= config.rules_clarity_escalate_threshold:
        reason_codes.append("resolution_rules_critically_unclear")
    elif signal.rules_clarity_score < config.rules_clarity_watch_threshold:
        reason_codes.append("resolution_rules_unclear")

    if signal.source_hierarchy_level == "missing_resolution_source":
        reason_codes.append("source_hierarchy_missing")
    elif signal.source_hierarchy_level == "secondary_resolution_source":
        reason_codes.append("source_hierarchy_secondary_only")
    elif signal.source_hierarchy_level == "tertiary_resolution_source":
        reason_codes.append("source_hierarchy_tertiary_only")

    if signal.seconds_until_close <= config.close_time_escalate_seconds:
        reason_codes.append("close_time_imminent")
    elif signal.seconds_until_close <= config.close_time_watch_seconds:
        reason_codes.append("close_time_inside_review_window")

    if signal.dispute_indicator_count >= config.dispute_escalate_threshold:
        reason_codes.append("dispute_indicators_elevated")
    elif signal.dispute_indicator_count >= config.dispute_watch_threshold:
        reason_codes.append("dispute_indicators_present")

    if signal.team_confidence_score <= config.team_confidence_escalate_threshold:
        reason_codes.append("team_confidence_critically_low")
    elif signal.team_confidence_score < config.team_confidence_watch_threshold:
        reason_codes.append("team_confidence_low")

    if not reason_codes:
        return ("resolution_ambiguity_clear",)
    return tuple(reason_codes)


def _status_for_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in CRITICAL_REASON_CODES for reason_code in reason_codes):
        return "escalate"
    if reason_codes == ("resolution_ambiguity_clear",):
        return "clear"
    return "watch"


def _report_status(
    clear_count: Decimal,
    watch_count: Decimal,
    escalate_count: Decimal,
) -> str:
    del clear_count
    if escalate_count > ZERO_COUNT:
        return "escalate"
    if watch_count > ZERO_COUNT:
        return "watch"
    return "clear"


def _report_reason_codes(
    rows: tuple[StrategyResolutionAmbiguityEscalationV5Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_resolution_ambiguity_signals_supplied",)
    reason_codes: list[str] = []
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code == "resolution_ambiguity_clear":
                continue
            if reason_code not in reason_codes:
                reason_codes.append(reason_code)
    if not reason_codes:
        return ("resolution_ambiguity_clear",)
    return tuple(reason_codes)


def _row_sort_key(row: StrategyResolutionAmbiguityEscalationV5Row) -> tuple[int, str]:
    priority = {"escalate": 0, "watch": 1, "clear": 2}[row.escalation_status]
    return (priority, row.case_id)


def _owner_team_for_status(status: str) -> str:
    if status == "escalate":
        return "resolution_operations_team"
    if status == "watch":
        return "resolution_policy_team"
    return "strategy_research_team"


def _next_action_for_status(status: str) -> str:
    if status == "escalate":
        return "escalate_for_manual_resolution_review"
    if status == "watch":
        return "schedule_resolution_review"
    return "continue_paper_monitoring"


def _normalize_signals(
    signals: tuple[StrategyResolutionAmbiguityEscalationV5Signal, ...],
) -> tuple[StrategyResolutionAmbiguityEscalationV5Signal, ...]:
    if type(signals) is not tuple:
        raise ValueError("signals must be a tuple")
    case_ids: list[str] = []
    for signal in signals:
        if type(signal) is not StrategyResolutionAmbiguityEscalationV5Signal:
            raise ValueError("signals must contain StrategyResolutionAmbiguityEscalationV5Signal values")
        require_paper_only_flags("StrategyResolutionAmbiguityEscalationV5Signal", signal)
        case_ids.append(signal.case_id)
    if len(set(case_ids)) != len(case_ids):
        raise ValueError("case_id values must be unique")
    return signals


def _normalize_rows(
    rows: tuple[StrategyResolutionAmbiguityEscalationV5Row, ...],
) -> tuple[StrategyResolutionAmbiguityEscalationV5Row, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    case_ids: list[str] = []
    for row in rows:
        if type(row) is not StrategyResolutionAmbiguityEscalationV5Row:
            raise ValueError("rows must contain StrategyResolutionAmbiguityEscalationV5Row values")
        require_paper_only_flags("StrategyResolutionAmbiguityEscalationV5Row", row)
        case_ids.append(row.case_id)
    if len(set(case_ids)) != len(case_ids):
        raise ValueError("row case_id values must be unique")
    return rows


def _normalize_reason_codes(
    field_name: str,
    values: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not values and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    normalized: list[str] = []
    for value in values:
        _require_member(field_name, value, REASON_CODES)
        if value in normalized:
            raise ValueError(f"{field_name} must not contain duplicates")
        normalized.append(value)
    return tuple(normalized)


def _require_member(field_name: str, value: str, allowed_values: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be a known {field_name.replace('_', ' ')}")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _normalize_ratio(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value, RATIO_QUANTUM)
    if normalized < ZERO_RATIO or normalized > ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_nonnegative_seconds(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value, SECONDS_QUANTUM)
    if normalized < ZERO_SECONDS:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value, COUNT_QUANTUM)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != value:
        raise ValueError(f"{field_name} must be integral")
    return normalized


def _normalize_decimal(field_name: str, value: Decimal, quantum: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(quantum)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)
