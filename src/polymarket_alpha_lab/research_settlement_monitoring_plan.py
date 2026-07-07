"""Readonly research settlement monitoring priority plan."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
import hashlib
import json
from typing import Any


DEFAULT_RESEARCH_SETTLEMENT_MONITORING_PLAN_CONFIG_VERSION = (
    "research-settlement-monitoring-plan-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
THREE = Decimal("3.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
SECONDS_PER_DAY = Decimal("86400")

PUBLIC_STATUSES = ("pass", "watch", "block")
STATUS_SORT_WEIGHT = {"block": 0, "watch": 1, "pass": 2}
STATUS_SCORE_COMPONENT = {
    "pass": ZERO,
    "watch": Decimal("0.250000"),
    "block": Decimal("0.750000"),
}

NO_CASES_REASON = "settlement_monitoring_no_cases"
CLEAR_REASON = "settlement_monitoring_clear"
WINDOW_WATCH_REASON = "settlement_monitoring_window_watch"
WINDOW_BLOCK_REASON = "settlement_monitoring_window_block"
RULE_RISK_WATCH_REASON = "settlement_monitoring_rule_risk_watch"
RULE_RISK_BLOCK_REASON = "settlement_monitoring_rule_risk_block"
REVIEW_READINESS_WATCH_REASON = "settlement_monitoring_review_readiness_watch"
REVIEW_READINESS_BLOCK_REASON = "settlement_monitoring_review_readiness_block"

ROW_REASON_CODES = (
    CLEAR_REASON,
    WINDOW_WATCH_REASON,
    WINDOW_BLOCK_REASON,
    RULE_RISK_WATCH_REASON,
    RULE_RISK_BLOCK_REASON,
    REVIEW_READINESS_WATCH_REASON,
    REVIEW_READINESS_BLOCK_REASON,
)
REPORT_REASON_CODES = (
    NO_CASES_REASON,
    CLEAR_REASON,
    WINDOW_BLOCK_REASON,
    RULE_RISK_BLOCK_REASON,
    REVIEW_READINESS_BLOCK_REASON,
    WINDOW_WATCH_REASON,
    RULE_RISK_WATCH_REASON,
    REVIEW_READINESS_WATCH_REASON,
)
TRIGGER_REASON_CODES = tuple(
    reason_code
    for reason_code in REPORT_REASON_CODES
    if reason_code not in (NO_CASES_REASON, CLEAR_REASON)
)

UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "auth",
        "buy",
        "candidate_id",
        "database",
        "dsn",
        "market_id",
        "market_slug",
        "order",
        "position",
        "question",
        "raw_candidate",
        "recommend",
        "recommendation",
        "sell",
        "slug",
        "source_ref",
        "source_text",
        "source_url",
        "table",
        "token",
        "trade",
        "url",
        "wallet",
    ),
)


__all__ = (
    "DEFAULT_RESEARCH_SETTLEMENT_MONITORING_PLAN_CONFIG_VERSION",
    "ResearchSettlementMonitoringConfig",
    "ResearchSettlementMonitoringCandidate",
    "ResearchSettlementMonitoringRow",
    "ResearchSettlementMonitoringPlan",
    "build_research_settlement_monitoring_plan",
    "research_settlement_monitoring_plan_payload",
    "validate_research_settlement_monitoring_public_payload",
)


@dataclass(frozen=True)
class ResearchSettlementMonitoringConfig:
    watch_within_seconds: Decimal = Decimal("3600.000000")
    block_within_seconds: Decimal = Decimal("900.000000")
    rule_risk_watch_threshold: Decimal = Decimal("0.500000")
    rule_risk_block_threshold: Decimal = Decimal("0.850000")
    review_readiness_watch_below: Decimal = Decimal("0.750000")
    review_readiness_block_below: Decimal = Decimal("0.400000")
    config_version: str = DEFAULT_RESEARCH_SETTLEMENT_MONITORING_PLAN_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("ResearchSettlementMonitoringConfig does not support subclassing")

    def __post_init__(self) -> None:
        for field_name in ("watch_within_seconds", "block_within_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_within_seconds >= self.watch_within_seconds:
            raise ValueError("block_within_seconds must be less than watch_within_seconds")
        for field_name in (
            "rule_risk_watch_threshold",
            "rule_risk_block_threshold",
            "review_readiness_watch_below",
            "review_readiness_block_below",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        if self.rule_risk_watch_threshold > self.rule_risk_block_threshold:
            raise ValueError(
                "rule_risk_watch_threshold must not exceed rule_risk_block_threshold",
            )
        if self.review_readiness_watch_below < self.review_readiness_block_below:
            raise ValueError(
                "review_readiness_watch_below must not be below "
                "review_readiness_block_below",
            )
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchSettlementMonitoringCandidate:
    anonymous_case_label: str
    anonymized_settlement_at: datetime
    rule_risk_score: Decimal
    review_readiness_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSettlementMonitoringCandidate does not support subclassing",
        )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "anonymous_case_label",
            _require_public_string("anonymous_case_label", self.anonymous_case_label),
        )
        object.__setattr__(
            self,
            "anonymized_settlement_at",
            _as_utc("anonymized_settlement_at", self.anonymized_settlement_at),
        )
        for field_name in ("rule_risk_score", "review_readiness_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("case", self)


@dataclass(frozen=True)
class ResearchSettlementMonitoringRow:
    anonymous_case_label: str
    anonymized_settlement_at: datetime
    seconds_to_settlement: Decimal
    rule_risk_score: Decimal
    review_readiness_score: Decimal
    priority_score: Decimal
    manual_monitoring_priority: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("ResearchSettlementMonitoringRow does not support subclassing")

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "anonymous_case_label",
            _require_public_string("anonymous_case_label", self.anonymous_case_label),
        )
        object.__setattr__(
            self,
            "anonymized_settlement_at",
            _as_utc("anonymized_settlement_at", self.anonymized_settlement_at),
        )
        for field_name in (
            "seconds_to_settlement",
            "priority_score",
            "manual_monitoring_priority",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("rule_risk_score", "review_readiness_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_known_value("status", self.status, PUBLIC_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        if self.status != _status_from_reason_codes(self.reason_codes):
            raise ValueError("status is inconsistent with reason_codes")
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchSettlementMonitoringPlan:
    generated_at: datetime
    config_version: str
    watch_within_seconds: Decimal
    block_within_seconds: Decimal
    rule_risk_watch_threshold: Decimal
    rule_risk_block_threshold: Decimal
    review_readiness_watch_below: Decimal
    review_readiness_block_below: Decimal
    case_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_priority_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchSettlementMonitoringRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("ResearchSettlementMonitoringPlan does not support subclassing")

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        for field_name in ("watch_within_seconds", "block_within_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "rule_risk_watch_threshold",
            "rule_risk_block_threshold",
            "review_readiness_watch_below",
            "review_readiness_block_below",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("case_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_priority_score",
            _require_nonnegative_decimal("max_priority_score", self.max_priority_score),
        )
        _require_known_value("status", self.status, PUBLIC_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("plan", self)
        _validate_plan_consistency(self)
        expected_digest = _derived_validation_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match plan payload")
        _require_digest("derived_validation_digest", self.derived_validation_digest)


def build_research_settlement_monitoring_plan(
    cases: list[ResearchSettlementMonitoringCandidate]
    | tuple[ResearchSettlementMonitoringCandidate, ...],
    *,
    config: ResearchSettlementMonitoringConfig,
    generated_at: datetime,
) -> ResearchSettlementMonitoringPlan:
    if type(config) is not ResearchSettlementMonitoringConfig:
        raise ValueError("config must be a ResearchSettlementMonitoringConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    provisional_rows = tuple(
        _row_from_case(value, config=config, generated_at=generated_at_utc)
        for value in _normalize_cases(cases)
    )
    sorted_rows = tuple(sorted(provisional_rows, key=_row_sort_key))
    rows = tuple(
        _row_with_priority(row, _count(index))
        for index, row in enumerate(sorted_rows, start=1)
    )
    return ResearchSettlementMonitoringPlan(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        watch_within_seconds=config.watch_within_seconds,
        block_within_seconds=config.block_within_seconds,
        rule_risk_watch_threshold=config.rule_risk_watch_threshold,
        rule_risk_block_threshold=config.rule_risk_block_threshold,
        review_readiness_watch_below=config.review_readiness_watch_below,
        review_readiness_block_below=config.review_readiness_block_below,
        case_count=_count(len(rows)),
        pass_count=_count(sum(1 for row in rows if row.status == "pass")),
        watch_count=_count(sum(1 for row in rows if row.status == "watch")),
        block_count=_count(sum(1 for row in rows if row.status == "block")),
        max_priority_score=_max_decimal(row.priority_score for row in rows),
        status=_plan_status(rows),
        reason_codes=_plan_reason_codes(rows),
        rows=rows,
    )


def research_settlement_monitoring_plan_payload(
    plan: ResearchSettlementMonitoringPlan,
) -> dict[str, Any]:
    if type(plan) is not ResearchSettlementMonitoringPlan:
        raise ValueError("plan must be a ResearchSettlementMonitoringPlan")
    _require_hard_flags("plan", plan)
    _reject_unsafe_public_surface("plan", plan)
    payload = _json_ready(plan)
    if type(payload) is not dict:
        raise ValueError("plan payload must be a JSON object")
    validate_research_settlement_monitoring_public_payload(payload)
    return payload


def validate_research_settlement_monitoring_public_payload(
    payload: dict[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_surface("public payload", payload)
    _reject_public_numerics(payload)
    _require_hard_flags("public payload", _PayloadFlags(payload))
    _validate_public_statuses(payload)
    digest = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", digest)
    without_digest = dict(payload)
    without_digest.pop("derived_validation_digest", None)
    expected_digest = _digest_payload(without_digest)
    if digest != expected_digest:
        raise ValueError("derived_validation_digest does not match public payload")


def _row_from_case(
    value: ResearchSettlementMonitoringCandidate,
    *,
    config: ResearchSettlementMonitoringConfig,
    generated_at: datetime,
) -> ResearchSettlementMonitoringRow:
    if type(value) is not ResearchSettlementMonitoringCandidate:
        raise ValueError("case must be a ResearchSettlementMonitoringCandidate")
    _require_hard_flags("case", value)
    seconds_to_settlement = _seconds_until(value.anonymized_settlement_at, generated_at)
    reason_codes = _row_reason_codes(
        seconds_to_settlement=seconds_to_settlement,
        rule_risk_score=value.rule_risk_score,
        review_readiness_score=value.review_readiness_score,
        config=config,
    )
    status = _status_from_reason_codes(reason_codes)
    priority_score = _priority_score(
        status=status,
        seconds_to_settlement=seconds_to_settlement,
        rule_risk_score=value.rule_risk_score,
        review_readiness_score=value.review_readiness_score,
        config=config,
    )
    return ResearchSettlementMonitoringRow(
        anonymous_case_label=value.anonymous_case_label,
        anonymized_settlement_at=value.anonymized_settlement_at,
        seconds_to_settlement=seconds_to_settlement,
        rule_risk_score=value.rule_risk_score,
        review_readiness_score=value.review_readiness_score,
        priority_score=priority_score,
        manual_monitoring_priority=ZERO,
        status=status,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    seconds_to_settlement: Decimal,
    rule_risk_score: Decimal,
    review_readiness_score: Decimal,
    config: ResearchSettlementMonitoringConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if seconds_to_settlement <= config.block_within_seconds:
        reason_codes.append(WINDOW_BLOCK_REASON)
    elif seconds_to_settlement <= config.watch_within_seconds:
        reason_codes.append(WINDOW_WATCH_REASON)

    if rule_risk_score >= config.rule_risk_block_threshold:
        reason_codes.append(RULE_RISK_BLOCK_REASON)
    elif rule_risk_score >= config.rule_risk_watch_threshold:
        reason_codes.append(RULE_RISK_WATCH_REASON)

    if review_readiness_score <= config.review_readiness_block_below:
        reason_codes.append(REVIEW_READINESS_BLOCK_REASON)
    elif review_readiness_score <= config.review_readiness_watch_below:
        reason_codes.append(REVIEW_READINESS_WATCH_REASON)

    if not reason_codes:
        return (CLEAR_REASON,)
    return tuple(reason_codes)


def _priority_score(
    *,
    status: str,
    seconds_to_settlement: Decimal,
    rule_risk_score: Decimal,
    review_readiness_score: Decimal,
    config: ResearchSettlementMonitoringConfig,
) -> Decimal:
    window_urgency = (
        ZERO
        if seconds_to_settlement >= config.watch_within_seconds
        else (ONE - (seconds_to_settlement / config.watch_within_seconds))
    )
    readiness_gap = (ONE - review_readiness_score) / THREE
    return _quantize(
        STATUS_SCORE_COMPONENT[status]
        + _quantize(window_urgency)
        + rule_risk_score
        + _quantize(readiness_gap),
    )


def _row_with_priority(
    row: ResearchSettlementMonitoringRow,
    manual_monitoring_priority: Decimal,
) -> ResearchSettlementMonitoringRow:
    return ResearchSettlementMonitoringRow(
        anonymous_case_label=row.anonymous_case_label,
        anonymized_settlement_at=row.anonymized_settlement_at,
        seconds_to_settlement=row.seconds_to_settlement,
        rule_risk_score=row.rule_risk_score,
        review_readiness_score=row.review_readiness_score,
        priority_score=row.priority_score,
        manual_monitoring_priority=manual_monitoring_priority,
        status=row.status,
        reason_codes=row.reason_codes,
    )


def _row_sort_key(row: ResearchSettlementMonitoringRow) -> tuple[int, Decimal, Decimal, str]:
    return (
        STATUS_SORT_WEIGHT[row.status],
        -row.priority_score,
        row.seconds_to_settlement,
        row.anonymous_case_label,
    )


def _plan_status(rows: tuple[ResearchSettlementMonitoringRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _plan_reason_codes(rows: tuple[ResearchSettlementMonitoringRow, ...]) -> tuple[str, ...]:
    if not rows:
        return (NO_CASES_REASON,)
    row_reasons = {reason_code for row in rows for reason_code in row.reason_codes}
    if row_reasons == {CLEAR_REASON}:
        return (CLEAR_REASON,)
    return tuple(
        reason_code
        for reason_code in TRIGGER_REASON_CODES
        if reason_code in row_reasons
    )


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _validate_plan_consistency(plan: ResearchSettlementMonitoringPlan) -> None:
    rows = plan.rows
    if plan.case_count != _count(len(rows)):
        raise ValueError("case_count is inconsistent with rows")
    if plan.pass_count != _count(sum(1 for row in rows if row.status == "pass")):
        raise ValueError("pass_count is inconsistent with rows")
    if plan.watch_count != _count(sum(1 for row in rows if row.status == "watch")):
        raise ValueError("watch_count is inconsistent with rows")
    if plan.block_count != _count(sum(1 for row in rows if row.status == "block")):
        raise ValueError("block_count is inconsistent with rows")
    if plan.max_priority_score != _max_decimal(row.priority_score for row in rows):
        raise ValueError("max_priority_score is inconsistent with rows")
    if plan.status != _plan_status(rows):
        raise ValueError("status is inconsistent with rows")
    if plan.reason_codes != _plan_reason_codes(rows):
        raise ValueError("reason_codes are inconsistent with rows")
    if tuple(sorted(rows, key=_row_sort_key)) != rows:
        raise ValueError("rows must be sorted by manual monitoring priority")
    for index, row in enumerate(rows, start=1):
        if row.manual_monitoring_priority != _count(index):
            raise ValueError("manual_monitoring_priority is inconsistent with row order")


def _normalize_cases(
    values: list[ResearchSettlementMonitoringCandidate]
    | tuple[ResearchSettlementMonitoringCandidate, ...],
) -> tuple[ResearchSettlementMonitoringCandidate, ...]:
    if not isinstance(values, (list, tuple)):
        raise ValueError("cases must be a list or tuple")
    normalized: list[ResearchSettlementMonitoringCandidate] = []
    for value in values:
        if type(value) is not ResearchSettlementMonitoringCandidate:
            raise ValueError("case must be a ResearchSettlementMonitoringCandidate")
        normalized.append(value)
    return tuple(normalized)


def _normalize_rows(values: object) -> tuple[ResearchSettlementMonitoringRow, ...]:
    if not isinstance(values, (list, tuple)):
        raise ValueError("rows must be a list or tuple")
    normalized: list[ResearchSettlementMonitoringRow] = []
    for value in values:
        if type(value) is not ResearchSettlementMonitoringRow:
            raise ValueError("row must be a ResearchSettlementMonitoringRow")
        normalized.append(value)
    return tuple(normalized)


def _normalize_reason_codes(
    field_name: str,
    values: object,
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if not isinstance(values, (list, tuple)):
        raise ValueError(f"{field_name} must be a list or tuple")
    normalized: list[str] = []
    for value in values:
        _require_known_value(field_name, value, allowed_values)
        if value not in normalized:
            normalized.append(value)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return tuple(normalized)


def _require_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value(rounding=ROUND_HALF_EVEN):
        raise ValueError(f"{field_name} must be an integral Decimal count")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be an exact Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _max_decimal(values: object) -> Decimal:
    maximum = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("max value must be an exact Decimal")
        if value > maximum:
            maximum = value
    return maximum


def _seconds_until(anonymized_settlement_at: datetime, generated_at: datetime) -> Decimal:
    seconds = _duration_seconds(generated_at, anonymized_settlement_at)
    if seconds < ZERO:
        return ZERO
    return seconds


def _duration_seconds(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    microseconds = (
        Decimal(delta.days) * SECONDS_PER_DAY * MICROSECONDS_PER_SECOND
        + Decimal(delta.seconds) * MICROSECONDS_PER_SECOND
        + Decimal(delta.microseconds)
    )
    return _quantize(microseconds / MICROSECONDS_PER_SECOND)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == "" or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")
    _reject_unsafe_public_text(field_name, value)
    return value


def _require_known_value(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


@dataclass(frozen=True)
class _PayloadFlags:
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


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be an exact Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float) or type(value) is int:
        raise ValueError("JSON value must use Decimal-derived strings")
    if type(value) is str or type(value) is bool:
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_surface(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_surface(label, asdict(value))
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_text(label, key)
            _reject_unsafe_public_surface(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_surface(label, item)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public value in {label}")


def _reject_public_numerics(value: object) -> None:
    if isinstance(value, float) or type(value) is int:
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numerics(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numerics(item)


def _validate_public_statuses(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "status":
                _require_known_value("status", item, PUBLIC_STATUSES)
            _validate_public_statuses(item)
        return
    if isinstance(value, list):
        for item in value:
            _validate_public_statuses(item)


def _derived_validation_digest(plan: ResearchSettlementMonitoringPlan) -> str:
    payload = asdict(plan)
    payload.pop("derived_validation_digest", None)
    return _digest_payload(_json_ready(payload))


def _digest_payload(payload: object) -> str:
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a sha256 hex digest") from exc
    return value
