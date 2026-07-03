"""Pure reducer for market settlement preparedness summaries."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal


__all__ = (
    "DEFAULT_MARKET_RESOLUTION_READINESS_CONFIG_VERSION",
    "MarketResolutionObservation",
    "MarketResolutionReadinessConfig",
    "MarketResolutionReadinessReport",
    "MarketResolutionReadinessRow",
    "build_market_resolution_readiness_report",
)


DEFAULT_MARKET_RESOLUTION_READINESS_CONFIG_VERSION = "market-resolution-readiness-v1"
READINESS_STATUSES = ("blocked", "watch", "pass")
SEVERITY_WEIGHT = {"blocked": 0, "watch": 1, "pass": 2}
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")


@dataclass(frozen=True)
class MarketResolutionReadinessConfig:
    config_version: str = DEFAULT_MARKET_RESOLUTION_READINESS_CONFIG_VERSION
    min_ready_resolution_share: Decimal = ONE
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "min_ready_resolution_share",
            _normalize_probability(
                "min_ready_resolution_share",
                self.min_ready_resolution_share,
            ),
        )
        _require_safety_flags(self)


@dataclass(frozen=True)
class MarketResolutionObservation:
    condition_id: str
    closed: bool
    active: bool
    pending: bool
    outcome_observed: bool
    outcome_value: Decimal | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("condition_id", self.condition_id)
        for field_name in ("closed", "active", "pending", "outcome_observed"):
            if type(getattr(self, field_name)) is not bool:
                raise ValueError(f"{field_name} must be a bool")
        if self.closed and self.active:
            raise ValueError("closed markets must not be active")
        if self.pending and self.outcome_observed:
            raise ValueError("pending markets must not have outcome observations")
        if self.pending and self.outcome_value is not None:
            raise ValueError("pending markets must not have outcome values")
        if self.outcome_observed and self.outcome_value is None:
            raise ValueError("observed outcomes must include outcome_value")
        if not self.outcome_observed and self.outcome_value is not None:
            raise ValueError("unobserved outcomes must not include outcome_value")
        if self.outcome_value is not None:
            object.__setattr__(
                self,
                "outcome_value",
                _normalize_probability("outcome_value", self.outcome_value),
            )
        _require_safety_flags(self)


@dataclass(frozen=True)
class MarketResolutionReadinessRow:
    condition_id: str
    closed: bool
    active: bool
    pending: bool
    outcome_observed: bool
    outcome_value: Decimal | None
    resolution_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("condition_id", self.condition_id)
        for field_name in ("closed", "active", "pending", "outcome_observed"):
            if type(getattr(self, field_name)) is not bool:
                raise ValueError(f"{field_name} must be a bool")
        if self.outcome_value is not None:
            object.__setattr__(
                self,
                "outcome_value",
                _normalize_probability("outcome_value", self.outcome_value),
            )
        _require_status("resolution_status", self.resolution_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_safety_flags(self)


@dataclass(frozen=True)
class MarketResolutionReadinessReport:
    generated_at: datetime
    config_version: str
    min_ready_resolution_share: Decimal
    total_market_count: int
    closed_market_count: int
    active_market_count: int
    pending_market_count: int
    outcome_observed_count: int
    ready_resolution_count: int
    ready_resolution_share: Decimal
    resolution_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[MarketResolutionReadinessRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "min_ready_resolution_share",
            _normalize_probability(
                "min_ready_resolution_share",
                self.min_ready_resolution_share,
            ),
        )
        for field_name in (
            "total_market_count",
            "closed_market_count",
            "active_market_count",
            "pending_market_count",
            "outcome_observed_count",
            "ready_resolution_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "ready_resolution_share",
            _normalize_probability(
                "ready_resolution_share",
                self.ready_resolution_share,
            ),
        )
        _require_status("resolution_status", self.resolution_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_safety_flags(self)


def build_market_resolution_readiness_report(
    observations: tuple[MarketResolutionObservation, ...]
    | list[MarketResolutionObservation],
    *,
    config: MarketResolutionReadinessConfig,
    generated_at: datetime,
) -> MarketResolutionReadinessReport:
    if type(config) is not MarketResolutionReadinessConfig:
        raise ValueError("config must be a MarketResolutionReadinessConfig")
    generated_at_utc = _as_utc(generated_at)
    normalized = _normalize_observations(observations)
    rows = tuple(
        sorted(
            (_row_from_observation(observation) for observation in normalized),
            key=lambda row: (SEVERITY_WEIGHT[row.resolution_status], row.condition_id),
        ),
    )
    total_market_count = len(rows)
    closed_market_count = sum(1 for row in rows if row.closed)
    active_market_count = sum(1 for row in rows if row.active)
    pending_market_count = sum(1 for row in rows if row.pending)
    outcome_observed_count = sum(1 for row in rows if row.outcome_observed)
    ready_resolution_count = sum(
        1 for row in rows if row.resolution_status == "pass"
    )
    ready_resolution_share = _ratio(ready_resolution_count, total_market_count)
    resolution_status = _report_status(
        total_market_count=total_market_count,
        pending_market_count=pending_market_count,
        ready_resolution_share=ready_resolution_share,
        min_ready_resolution_share=config.min_ready_resolution_share,
    )

    return MarketResolutionReadinessReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        min_ready_resolution_share=config.min_ready_resolution_share,
        total_market_count=total_market_count,
        closed_market_count=closed_market_count,
        active_market_count=active_market_count,
        pending_market_count=pending_market_count,
        outcome_observed_count=outcome_observed_count,
        ready_resolution_count=ready_resolution_count,
        ready_resolution_share=ready_resolution_share,
        resolution_status=resolution_status,
        reason_codes=_report_reason_codes(resolution_status),
        rows=rows,
    )


def _row_from_observation(
    observation: MarketResolutionObservation,
) -> MarketResolutionReadinessRow:
    resolution_status, reason_codes = _row_status_and_reasons(observation)
    return MarketResolutionReadinessRow(
        condition_id=observation.condition_id,
        closed=observation.closed,
        active=observation.active,
        pending=observation.pending,
        outcome_observed=observation.outcome_observed,
        outcome_value=observation.outcome_value,
        resolution_status=resolution_status,
        reason_codes=reason_codes,
    )


def _row_status_and_reasons(
    observation: MarketResolutionObservation,
) -> tuple[str, tuple[str, ...]]:
    if observation.pending or not observation.closed:
        return "blocked", ("market_resolution_still_pending",)
    if not observation.outcome_observed:
        return "watch", ("closed_market_missing_outcome_observation",)
    return "pass", ("closed_market_outcome_observed",)


def _report_status(
    *,
    total_market_count: int,
    pending_market_count: int,
    ready_resolution_share: Decimal,
    min_ready_resolution_share: Decimal,
) -> str:
    if total_market_count == 0 or pending_market_count == total_market_count:
        return "blocked"
    if ready_resolution_share < min_ready_resolution_share:
        return "watch"
    return "pass"


def _report_reason_codes(status: str) -> tuple[str, ...]:
    if status == "pass":
        return ("market_resolution_ready",)
    if status == "watch":
        return ("resolution_observation_below_ready_threshold",)
    return ("no_markets_to_assess",)


def _ratio(numerator: int, denominator: int) -> Decimal:
    if denominator == 0:
        return ZERO
    return (Decimal(numerator) / Decimal(denominator)).quantize(QUANTUM)


def _normalize_observations(
    observations: tuple[MarketResolutionObservation, ...]
    | list[MarketResolutionObservation],
) -> tuple[MarketResolutionObservation, ...]:
    if type(observations) not in (list, tuple):
        raise ValueError(
            "observations must be a list or tuple of MarketResolutionObservation",
        )
    normalized = tuple(observations)
    for observation in normalized:
        if type(observation) is not MarketResolutionObservation:
            raise ValueError(
                "observations must contain MarketResolutionObservation values",
            )
    return normalized


def _normalize_rows(
    rows: tuple[MarketResolutionReadinessRow, ...],
) -> tuple[MarketResolutionReadinessRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not MarketResolutionReadinessRow:
            raise ValueError("rows must contain MarketResolutionReadinessRow values")
    if normalized != tuple(
        sorted(
            normalized,
            key=lambda row: (SEVERITY_WEIGHT[row.resolution_status], row.condition_id),
        ),
    ):
        raise ValueError("rows must use deterministic readiness sort")
    return normalized


def _validate_report_consistency(report: MarketResolutionReadinessReport) -> None:
    if report.total_market_count != len(report.rows):
        raise ValueError("total_market_count must match rows")
    if report.closed_market_count != sum(1 for row in report.rows if row.closed):
        raise ValueError("closed_market_count must match rows")
    if report.active_market_count != sum(1 for row in report.rows if row.active):
        raise ValueError("active_market_count must match rows")
    if report.pending_market_count != sum(1 for row in report.rows if row.pending):
        raise ValueError("pending_market_count must match rows")
    if report.outcome_observed_count != sum(
        1 for row in report.rows if row.outcome_observed
    ):
        raise ValueError("outcome_observed_count must match rows")
    if report.ready_resolution_count != sum(
        1 for row in report.rows if row.resolution_status == "pass"
    ):
        raise ValueError("ready_resolution_count must match pass rows")
    if report.ready_resolution_share != _ratio(
        report.ready_resolution_count,
        report.total_market_count,
    ):
        raise ValueError("ready_resolution_share must match ready count ratio")
    if report.resolution_status != _report_status(
        total_market_count=report.total_market_count,
        pending_market_count=report.pending_market_count,
        ready_resolution_share=report.ready_resolution_share,
        min_ready_resolution_share=report.min_ready_resolution_share,
    ):
        raise ValueError("resolution_status must match report state")
    if report.reason_codes != _report_reason_codes(report.resolution_status):
        raise ValueError("reason_codes must match resolution_status")


def _normalize_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        reason_codes = tuple(values)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not reason_codes:
        raise ValueError("reason_codes must include at least one code")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must not contain duplicates")
    for reason_code in reason_codes:
        _require_canonical_string("reason_codes", reason_code)
    return reason_codes


def _normalize_probability(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal or None")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return value.quantize(QUANTUM)


def _require_status(field_name: str, value: str) -> None:
    if type(value) is not str or value not in READINESS_STATUSES:
        raise ValueError(f"{field_name} must be one of {READINESS_STATUSES!r}")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value != value.strip() or not value:
        raise ValueError(f"{field_name} must be a non-empty stripped string")


def _require_nonnegative_int(field_name: str, value: int) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field_name} must be a non-negative int")


def _require_safety_flags(value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only") is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly") is not True:
        raise ValueError("readonly must be True")


def _as_utc(value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
