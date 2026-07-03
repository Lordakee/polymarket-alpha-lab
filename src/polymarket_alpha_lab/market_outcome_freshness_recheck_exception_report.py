from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
from types import MappingProxyType
from typing import Any


EXCEPTION_TYPES = (
    "stale_outcome_timestamp",
    "missing_official_source",
    "unacknowledged_queue",
    "unresolved_category_freshness_gap",
    "repeated_overdue_recheck",
)
CRITICAL_EXCEPTION_TYPES = frozenset(
    (
        "missing_official_source",
        "unacknowledged_queue",
        "repeated_overdue_recheck",
    ),
)
SEVERITIES = ("none", "warning", "critical")
RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")


@dataclass(frozen=True)
class MarketOutcomeFreshnessRecheckExceptionConfig:
    config_version: str
    stale_outcome_after_seconds: Decimal
    category_gap_after_seconds: Decimal
    overdue_recheck_after_seconds: Decimal
    repeated_overdue_recheck_count: Decimal
    warning_exception_count: Decimal
    critical_exception_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "stale_outcome_after_seconds",
            "category_gap_after_seconds",
            "overdue_recheck_after_seconds",
            "repeated_overdue_recheck_count",
            "warning_exception_count",
            "critical_exception_count",
        ):
            _require_nonnegative_decimal(field_name, getattr(self, field_name))
        if self.warning_exception_count > self.critical_exception_count:
            raise ValueError(
                "warning_exception_count must not exceed critical_exception_count",
            )
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketOutcomeFreshnessRecheckExceptionInput:
    condition_id: str
    market_slug: str
    category: str
    outcome_timestamp: datetime | None
    official_source_url: str | None
    queue_acknowledged_at: datetime | None
    category_freshness_checked_at: datetime | None
    latest_recheck_due_at: datetime | None
    recheck_completed_at: datetime | None
    overdue_recheck_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("condition_id", self.condition_id)
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("category", self.category)
        if self.official_source_url is not None:
            _require_canonical_string(
                "official_source_url",
                self.official_source_url,
            )
        object.__setattr__(
            self,
            "outcome_timestamp",
            _as_optional_utc("outcome_timestamp", self.outcome_timestamp),
        )
        object.__setattr__(
            self,
            "queue_acknowledged_at",
            _as_optional_utc("queue_acknowledged_at", self.queue_acknowledged_at),
        )
        object.__setattr__(
            self,
            "category_freshness_checked_at",
            _as_optional_utc(
                "category_freshness_checked_at",
                self.category_freshness_checked_at,
            ),
        )
        object.__setattr__(
            self,
            "latest_recheck_due_at",
            _as_optional_utc("latest_recheck_due_at", self.latest_recheck_due_at),
        )
        object.__setattr__(
            self,
            "recheck_completed_at",
            _as_optional_utc("recheck_completed_at", self.recheck_completed_at),
        )
        _require_nonnegative_decimal(
            "overdue_recheck_count",
            self.overdue_recheck_count,
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketOutcomeFreshnessRecheckExceptionRow:
    condition_id: str
    market_slug: str
    category: str
    outcome_timestamp: datetime | None
    official_source_url: str | None
    queue_acknowledged_at: datetime | None
    category_freshness_checked_at: datetime | None
    latest_recheck_due_at: datetime | None
    recheck_completed_at: datetime | None
    outcome_age_seconds: Decimal | None
    category_freshness_gap_seconds: Decimal | None
    recheck_overdue_seconds: Decimal | None
    overdue_recheck_count: Decimal
    exception_types: tuple[str, ...]
    exception_count: Decimal
    severity: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("condition_id", self.condition_id)
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("category", self.category)
        if self.official_source_url is not None:
            _require_canonical_string(
                "official_source_url",
                self.official_source_url,
            )
        for field_name in (
            "outcome_timestamp",
            "queue_acknowledged_at",
            "category_freshness_checked_at",
            "latest_recheck_due_at",
            "recheck_completed_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _as_optional_utc(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "outcome_age_seconds",
            "category_freshness_gap_seconds",
            "recheck_overdue_seconds",
        ):
            value = getattr(self, field_name)
            if value is not None:
                _require_nonnegative_decimal(field_name, value)
        _require_nonnegative_decimal(
            "overdue_recheck_count",
            self.overdue_recheck_count,
        )
        object.__setattr__(
            self,
            "exception_types",
            _normalize_exception_types(self.exception_types),
        )
        _require_nonnegative_decimal("exception_count", self.exception_count)
        if self.exception_count != Decimal(len(self.exception_types)):
            raise ValueError("exception_count must match exception_types")
        if self.severity not in SEVERITIES:
            raise ValueError("severity must be a known severity")
        if self.exception_count == ZERO and self.severity != "none":
            raise ValueError("severity must be none without exceptions")
        if self.exception_count > ZERO and self.severity == "none":
            raise ValueError("severity must reflect exceptions")
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketOutcomeFreshnessRecheckExceptionReport:
    generated_at: datetime
    config_version: str
    market_count: Decimal
    exception_market_count: Decimal
    clean_market_count: Decimal
    exception_market_ratio: Decimal | None
    highest_severity: str
    severity_counts: MappingProxyType[str, Decimal]
    exception_type_counts: MappingProxyType[str, Decimal]
    rows: tuple[MarketOutcomeFreshnessRecheckExceptionRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "market_count",
            "exception_market_count",
            "clean_market_count",
        ):
            _require_nonnegative_decimal(field_name, getattr(self, field_name))
        if self.exception_market_ratio is not None:
            _require_probability_decimal(
                "exception_market_ratio",
                self.exception_market_ratio,
            )
        if self.highest_severity not in SEVERITIES:
            raise ValueError("highest_severity must be a known severity")
        object.__setattr__(
            self,
            "severity_counts",
            _normalize_decimal_mapping(
                "severity_counts",
                self.severity_counts,
                SEVERITIES,
            ),
        )
        object.__setattr__(
            self,
            "exception_type_counts",
            _normalize_decimal_mapping(
                "exception_type_counts",
                self.exception_type_counts,
                EXCEPTION_TYPES,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_hard_flags(self)


def build_market_outcome_freshness_recheck_exception_report(
    observations: (
        list[MarketOutcomeFreshnessRecheckExceptionInput]
        | tuple[MarketOutcomeFreshnessRecheckExceptionInput, ...]
    ),
    *,
    config: MarketOutcomeFreshnessRecheckExceptionConfig,
    generated_at: datetime,
) -> MarketOutcomeFreshnessRecheckExceptionReport:
    if type(config) is not MarketOutcomeFreshnessRecheckExceptionConfig:
        raise ValueError(
            "config must be a MarketOutcomeFreshnessRecheckExceptionConfig",
        )
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (
                _build_row(
                    observation,
                    config=config,
                    generated_at_utc=generated_at_utc,
                )
                for observation in _normalize_observations(observations)
            ),
            key=lambda row: (row.market_slug, row.condition_id),
        ),
    )
    market_count = Decimal(len(rows))
    exception_market_count = Decimal(
        sum(1 for row in rows if row.exception_count > ZERO),
    )
    severity_counts = {
        severity: Decimal(sum(1 for row in rows if row.severity == severity))
        for severity in SEVERITIES
    }
    exception_type_counts = {
        exception_type: Decimal(
            sum(1 for row in rows if exception_type in row.exception_types),
        )
        for exception_type in EXCEPTION_TYPES
    }
    return MarketOutcomeFreshnessRecheckExceptionReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        market_count=market_count,
        exception_market_count=exception_market_count,
        clean_market_count=market_count - exception_market_count,
        exception_market_ratio=_ratio(exception_market_count, market_count),
        highest_severity=_highest_severity(rows),
        severity_counts=MappingProxyType(severity_counts),
        exception_type_counts=MappingProxyType(exception_type_counts),
        rows=rows,
    )


def market_outcome_freshness_recheck_exception_report_json_payload(
    report: MarketOutcomeFreshnessRecheckExceptionReport,
) -> dict[str, Any]:
    if type(report) is not MarketOutcomeFreshnessRecheckExceptionReport:
        raise ValueError(
            "report must be a MarketOutcomeFreshnessRecheckExceptionReport",
        )
    return _json_ready(report)


def _build_row(
    observation: MarketOutcomeFreshnessRecheckExceptionInput,
    *,
    config: MarketOutcomeFreshnessRecheckExceptionConfig,
    generated_at_utc: datetime,
) -> MarketOutcomeFreshnessRecheckExceptionRow:
    outcome_age_seconds = _age_seconds(
        "outcome_age_seconds",
        generated_at_utc,
        observation.outcome_timestamp,
    )
    category_gap_seconds = _age_seconds(
        "category_freshness_gap_seconds",
        generated_at_utc,
        observation.category_freshness_checked_at,
    )
    recheck_overdue_seconds = _recheck_overdue_seconds(
        generated_at_utc=generated_at_utc,
        due_at=observation.latest_recheck_due_at,
        completed_at=observation.recheck_completed_at,
    )
    exception_types = _exception_types(
        observation,
        config=config,
        outcome_age_seconds=outcome_age_seconds,
        category_gap_seconds=category_gap_seconds,
        recheck_overdue_seconds=recheck_overdue_seconds,
    )
    return MarketOutcomeFreshnessRecheckExceptionRow(
        condition_id=observation.condition_id,
        market_slug=observation.market_slug,
        category=observation.category,
        outcome_timestamp=observation.outcome_timestamp,
        official_source_url=observation.official_source_url,
        queue_acknowledged_at=observation.queue_acknowledged_at,
        category_freshness_checked_at=observation.category_freshness_checked_at,
        latest_recheck_due_at=observation.latest_recheck_due_at,
        recheck_completed_at=observation.recheck_completed_at,
        outcome_age_seconds=outcome_age_seconds,
        category_freshness_gap_seconds=category_gap_seconds,
        recheck_overdue_seconds=recheck_overdue_seconds,
        overdue_recheck_count=observation.overdue_recheck_count,
        exception_types=exception_types,
        exception_count=Decimal(len(exception_types)),
        severity=_severity_for_exceptions(
            exception_types,
            Decimal(len(exception_types)),
            config=config,
        ),
    )


def _exception_types(
    observation: MarketOutcomeFreshnessRecheckExceptionInput,
    *,
    config: MarketOutcomeFreshnessRecheckExceptionConfig,
    outcome_age_seconds: Decimal | None,
    category_gap_seconds: Decimal | None,
    recheck_overdue_seconds: Decimal | None,
) -> tuple[str, ...]:
    exceptions: list[str] = []
    if (
        outcome_age_seconds is None
        or outcome_age_seconds > config.stale_outcome_after_seconds
    ):
        exceptions.append("stale_outcome_timestamp")
    if observation.official_source_url is None:
        exceptions.append("missing_official_source")
    if observation.queue_acknowledged_at is None:
        exceptions.append("unacknowledged_queue")
    if (
        category_gap_seconds is None
        or category_gap_seconds > config.category_gap_after_seconds
    ):
        exceptions.append("unresolved_category_freshness_gap")
    if (
        recheck_overdue_seconds is not None
        and recheck_overdue_seconds > config.overdue_recheck_after_seconds
        and observation.overdue_recheck_count >= config.repeated_overdue_recheck_count
    ):
        exceptions.append("repeated_overdue_recheck")
    return tuple(exceptions)


def _recheck_overdue_seconds(
    *,
    generated_at_utc: datetime,
    due_at: datetime | None,
    completed_at: datetime | None,
) -> Decimal | None:
    if due_at is None:
        return None
    normalized_due_at = _as_utc("latest_recheck_due_at", due_at)
    if completed_at is not None:
        completed_at_utc = _as_utc("recheck_completed_at", completed_at)
        if completed_at_utc < normalized_due_at:
            raise ValueError("recheck_completed_delta_seconds must be nonnegative")
        return None
    return _seconds_between(
        "recheck_overdue_seconds",
        generated_at_utc,
        normalized_due_at,
    )


def _normalize_observations(
    observations: (
        list[MarketOutcomeFreshnessRecheckExceptionInput]
        | tuple[MarketOutcomeFreshnessRecheckExceptionInput, ...]
    ),
) -> tuple[MarketOutcomeFreshnessRecheckExceptionInput, ...]:
    if type(observations) not in (list, tuple):
        raise ValueError(
            "observations must be a list or tuple of "
            "MarketOutcomeFreshnessRecheckExceptionInput values",
        )
    normalized = tuple(observations)
    for observation in normalized:
        if type(observation) is not MarketOutcomeFreshnessRecheckExceptionInput:
            raise ValueError(
                "observations must contain "
                "MarketOutcomeFreshnessRecheckExceptionInput values",
            )
    return normalized


def _normalize_rows(
    rows: tuple[MarketOutcomeFreshnessRecheckExceptionRow, ...],
) -> tuple[MarketOutcomeFreshnessRecheckExceptionRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not MarketOutcomeFreshnessRecheckExceptionRow:
            raise ValueError(
                "rows must contain MarketOutcomeFreshnessRecheckExceptionRow values",
            )
    return normalized


def _require_hard_flags(value: Any) -> None:
    if value.paper_only is not True:
        raise ValueError("paper_only must be True")
    if value.report_only is not True:
        raise ValueError("report_only must be True")
    if value.readonly is not True:
        raise ValueError("readonly must be True")


def _normalize_exception_types(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("exception_types must be a tuple")
    if len(set(value)) != len(value):
        raise ValueError("exception_types must be unique")
    for exception_type in value:
        if exception_type not in EXCEPTION_TYPES:
            raise ValueError("exception_types must be known exception types")
    expected_order = tuple(
        exception_type for exception_type in EXCEPTION_TYPES if exception_type in value
    )
    if value != expected_order:
        raise ValueError("exception_types must follow deterministic order")
    return value


def _normalize_decimal_mapping(
    field_name: str,
    mapping: Any,
    expected_keys: tuple[str, ...],
) -> MappingProxyType[str, Decimal]:
    if not isinstance(mapping, dict) and type(mapping) is not MappingProxyType:
        raise ValueError(f"{field_name} must be a mapping")
    normalized = dict(mapping)
    if tuple(normalized) != expected_keys:
        raise ValueError(f"{field_name} must use deterministic keys")
    for key, value in normalized.items():
        if key not in expected_keys:
            raise ValueError(f"{field_name} must use known keys")
        _require_nonnegative_decimal(f"{field_name}.{key}", value)
    return MappingProxyType(normalized)


def _validate_report_consistency(
    report: MarketOutcomeFreshnessRecheckExceptionReport,
) -> None:
    if report.market_count != Decimal(len(report.rows)):
        raise ValueError("market_count must match rows")
    if report.exception_market_count != Decimal(
        sum(1 for row in report.rows if row.exception_count > ZERO),
    ):
        raise ValueError("exception_market_count must match rows")
    if report.clean_market_count != report.market_count - report.exception_market_count:
        raise ValueError("clean_market_count must match market_count")
    if report.exception_market_ratio != _ratio(
        report.exception_market_count,
        report.market_count,
    ):
        raise ValueError("exception_market_ratio must match market counts")
    expected_severity_counts = {
        severity: Decimal(sum(1 for row in report.rows if row.severity == severity))
        for severity in SEVERITIES
    }
    if dict(report.severity_counts) != expected_severity_counts:
        raise ValueError("severity_counts must match rows")
    expected_exception_type_counts = {
        exception_type: Decimal(
            sum(1 for row in report.rows if exception_type in row.exception_types),
        )
        for exception_type in EXCEPTION_TYPES
    }
    if dict(report.exception_type_counts) != expected_exception_type_counts:
        raise ValueError("exception_type_counts must match rows")
    if report.highest_severity != _highest_severity(report.rows):
        raise ValueError("highest_severity must match rows")


def _severity_for_exceptions(
    exception_types: tuple[str, ...],
    exception_count: Decimal,
    *,
    config: MarketOutcomeFreshnessRecheckExceptionConfig,
) -> str:
    if (
        any(exception_type in CRITICAL_EXCEPTION_TYPES for exception_type in exception_types)
        or exception_count >= config.critical_exception_count
    ):
        return "critical"
    if exception_count >= config.warning_exception_count:
        return "warning"
    return "none"


def _highest_severity(
    rows: tuple[MarketOutcomeFreshnessRecheckExceptionRow, ...],
) -> str:
    if any(row.severity == "critical" for row in rows):
        return "critical"
    if any(row.severity == "warning" for row in rows):
        return "warning"
    return "none"


def _age_seconds(
    field_name: str,
    generated_at_utc: datetime,
    observed_at: datetime | None,
) -> Decimal | None:
    if observed_at is None:
        return None
    return _seconds_between(field_name, generated_at_utc, observed_at)


def _seconds_between(
    field_name: str,
    later: datetime,
    earlier: datetime,
) -> Decimal:
    later_utc = _as_utc("generated_at", later)
    earlier_utc = _as_utc(field_name, earlier)
    seconds = Decimal(str((later_utc - earlier_utc).total_seconds()))
    if seconds < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return seconds.quantize(Decimal("1"), rounding=ROUND_HALF_EVEN)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal | None:
    if denominator == ZERO:
        return None
    return (numerator / denominator).quantize(
        RATIO_QUANTUM,
        rounding=ROUND_HALF_EVEN,
    )


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: datetime | None) -> datetime | None:
    return None if value is None else _as_utc(field_name, value)


def _require_canonical_string(field_name: str, value: Any) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_decimal(field_name: str, value: Any) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_probability_decimal(field_name: str, value: Decimal) -> None:
    _require_nonnegative_decimal(field_name, value)
    if value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    if value != value.quantize(RATIO_QUANTUM, rounding=ROUND_HALF_EVEN):
        raise ValueError(f"{field_name} must use 0.000001 precision")


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if isinstance(value, MappingProxyType):
        return {key: _json_ready(child) for key, child in value.items()}
    if isinstance(value, tuple):
        return [_json_ready(child) for child in value]
    if isinstance(value, list):
        return [_json_ready(child) for child in value]
    if hasattr(value, "__dataclass_fields__"):
        return {
            field_name: _json_ready(getattr(value, field_name))
            for field_name in value.__dataclass_fields__
        }
    return value
