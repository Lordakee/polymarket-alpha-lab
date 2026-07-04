"""Pure report-only digest for debt ceiling X-date policy risk."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from typing import Any


__all__ = (
    "DEFAULT_MARKET_RESEARCH_POLICY_DEBT_CEILING_X_DATE_DIGEST_CONFIG_VERSION",
    "MarketResearchPolicyDebtCeilingXDateDigestConfig",
    "DebtCeilingXDateSignal",
    "DebtCeilingXDateDigestRow",
    "DebtCeilingXDateDigestReport",
    "build_market_research_policy_debt_ceiling_x_date_digest",
    "market_research_policy_debt_ceiling_x_date_digest_payload",
)


DEFAULT_MARKET_RESEARCH_POLICY_DEBT_CEILING_X_DATE_DIGEST_CONFIG_VERSION = (
    "market-research-policy-debt-ceiling-x-date-digest-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
SECONDS_PER_HOUR = Decimal("3600")
MICROSECONDS_PER_SECOND = Decimal("1000000")
DECIMAL_CONTEXT = Context(prec=64)

RISK_STATUSES = ("high_risk", "watch", "low_risk")
DIGEST_STATUSES = ("blocked", "watch", "pass")
STATUS_WEIGHT = {
    "high_risk": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "low_risk": Decimal("2.000000"),
}

BLOCKED_ROW_REASONS = (
    "x_date_slippage_blocked",
    "days_to_x_date_blocked",
    "negotiation_stress_blocked",
)
WATCH_ROW_REASONS = (
    "x_date_slippage_watch",
    "days_to_x_date_watch",
    "negotiation_stress_watch",
    "policy_signal_stale",
)
REPORT_REASON_SEQUENCE = (
    "debt_ceiling_x_date_digest_empty",
    "debt_ceiling_x_date_high_risk_present",
    "debt_ceiling_x_date_watch_present",
    "debt_ceiling_x_date_low_risk_only",
    "debt_ceiling_x_date_stale_signal_present",
    "x_date_slippage_blocked_present",
    "x_date_slippage_watch_present",
    "days_to_x_date_blocked_present",
    "days_to_x_date_watch_present",
    "negotiation_stress_blocked_present",
    "negotiation_stress_watch_present",
)


@dataclass(frozen=True)
class MarketResearchPolicyDebtCeilingXDateDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_POLICY_DEBT_CEILING_X_DATE_DIGEST_CONFIG_VERSION
    )
    watch_days_to_x_date: Decimal = Decimal("14.000000")
    blocked_days_to_x_date: Decimal = Decimal("7.000000")
    watch_slippage_days: Decimal = Decimal("3.000000")
    blocked_slippage_days: Decimal = Decimal("7.000000")
    watch_negotiation_stress_ratio: Decimal = Decimal("0.400000")
    blocked_negotiation_stress_ratio: Decimal = Decimal("0.700000")
    max_signal_age_hours: Decimal = Decimal("48.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchPolicyDebtCeilingXDateDigestConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "watch_days_to_x_date",
            "blocked_days_to_x_date",
            "watch_slippage_days",
            "blocked_slippage_days",
            "max_signal_age_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_negotiation_stress_ratio",
            "blocked_negotiation_stress_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class DebtCeilingXDateSignal:
    signal_id: str
    market_slug: str
    source_label: str
    baseline_x_date: datetime
    latest_x_date: datetime
    observed_at: datetime
    negotiation_stress_ratio: Decimal
    probability_event_relevance: Decimal
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, DebtCeilingXDateSignal, "signal")
        for field_name in ("signal_id", "market_slug", "source_label"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in ("baseline_x_date", "latest_x_date", "observed_at"):
            object.__setattr__(
                self,
                field_name,
                _as_utc(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "negotiation_stress_ratio",
            "probability_event_relevance",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_reason_codes(self.upstream_reason_codes, require_nonempty=True),
        )
        _require_hard_flags("signal", self)


@dataclass(frozen=True)
class DebtCeilingXDateDigestRow:
    signal_id: str
    market_slug: str
    source_label: str
    baseline_x_date: datetime
    latest_x_date: datetime
    observed_at: datetime
    days_to_x_date: Decimal
    slippage_days: Decimal
    signal_age_hours: Decimal
    negotiation_stress_ratio: Decimal
    probability_event_relevance: Decimal
    risk_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, DebtCeilingXDateDigestRow, "row")
        for field_name in ("signal_id", "market_slug", "source_label"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in ("baseline_x_date", "latest_x_date", "observed_at"):
            object.__setattr__(
                self,
                field_name,
                _as_utc(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "days_to_x_date",
            "slippage_days",
            "signal_age_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "negotiation_stress_ratio",
            "probability_event_relevance",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member("risk_status", self.risk_status, RISK_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class DebtCeilingXDateDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    input_count: Decimal
    high_risk_count: Decimal
    watch_count: Decimal
    low_risk_count: Decimal
    stale_signal_count: Decimal
    max_slippage_days: Decimal
    min_days_to_x_date: Decimal
    max_negotiation_stress_ratio: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[DebtCeilingXDateDigestRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, DebtCeilingXDateDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_member("digest_status", self.digest_status, DIGEST_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "input_count",
            "high_risk_count",
            "watch_count",
            "low_risk_count",
            "stale_signal_count",
            "max_slippage_days",
            "min_days_to_x_date",
            "max_negotiation_stress_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_negotiation_stress_ratio",
            _normalize_probability(
                "max_negotiation_stress_ratio",
                self.max_negotiation_stress_ratio,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_policy_debt_ceiling_x_date_digest(
    signals: Iterable[DebtCeilingXDateSignal],
    *,
    config: MarketResearchPolicyDebtCeilingXDateDigestConfig,
    generated_at: datetime,
) -> DebtCeilingXDateDigestReport:
    if type(config) is not MarketResearchPolicyDebtCeilingXDateDigestConfig:
        raise ValueError(
            "config must be exactly MarketResearchPolicyDebtCeilingXDateDigestConfig",
        )
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized = _normalize_inputs(signals)
    rows = tuple(
        sorted(
            (
                _row_from_signal(value, config=config, generated_at=generated_at)
                for value in normalized
            ),
            key=_row_sort_key,
        ),
    )
    digest_status = _digest_status(rows)
    return DebtCeilingXDateDigestReport(
        generated_at=generated_at,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=_recommended_next_step(digest_status),
        input_count=_count_decimal(len(normalized)),
        high_risk_count=_status_count(rows, "high_risk"),
        watch_count=_status_count(rows, "watch"),
        low_risk_count=_status_count(rows, "low_risk"),
        stale_signal_count=_reason_count(rows, "policy_signal_stale"),
        max_slippage_days=_max_decimal(row.slippage_days for row in rows),
        min_days_to_x_date=_min_decimal(row.days_to_x_date for row in rows),
        max_negotiation_stress_ratio=_max_decimal(
            (row.negotiation_stress_ratio for row in rows),
        ),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def market_research_policy_debt_ceiling_x_date_digest_payload(
    report: DebtCeilingXDateDigestReport,
) -> dict[str, Any]:
    if type(report) is not DebtCeilingXDateDigestReport:
        raise ValueError("report must be exactly DebtCeilingXDateDigestReport")
    _require_hard_flags("report", report)
    return _payload_value(report)


def _row_from_signal(
    value: DebtCeilingXDateSignal,
    *,
    config: MarketResearchPolicyDebtCeilingXDateDigestConfig,
    generated_at: datetime,
) -> DebtCeilingXDateDigestRow:
    if value.observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    days_to_x_date = _nonnegative_elapsed_days(value.latest_x_date, generated_at)
    slippage_days = _nonnegative_elapsed_days(value.baseline_x_date, value.latest_x_date)
    signal_age_hours = _elapsed_hours(generated_at, value.observed_at)
    reason_codes = _row_reason_codes(
        value.upstream_reason_codes,
        days_to_x_date=days_to_x_date,
        slippage_days=slippage_days,
        signal_age_hours=signal_age_hours,
        negotiation_stress_ratio=value.negotiation_stress_ratio,
        config=config,
    )
    return DebtCeilingXDateDigestRow(
        signal_id=value.signal_id,
        market_slug=value.market_slug,
        source_label=value.source_label,
        baseline_x_date=value.baseline_x_date,
        latest_x_date=value.latest_x_date,
        observed_at=value.observed_at,
        days_to_x_date=days_to_x_date,
        slippage_days=slippage_days,
        signal_age_hours=signal_age_hours,
        negotiation_stress_ratio=value.negotiation_stress_ratio,
        probability_event_relevance=value.probability_event_relevance,
        risk_status=_risk_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    upstream_reason_codes: tuple[str, ...],
    *,
    days_to_x_date: Decimal,
    slippage_days: Decimal,
    signal_age_hours: Decimal,
    negotiation_stress_ratio: Decimal,
    config: MarketResearchPolicyDebtCeilingXDateDigestConfig,
) -> tuple[str, ...]:
    reason_codes = list(upstream_reason_codes)
    if slippage_days >= config.blocked_slippage_days:
        reason_codes.append("x_date_slippage_blocked")
    elif slippage_days >= config.watch_slippage_days:
        reason_codes.append("x_date_slippage_watch")
    if days_to_x_date <= config.blocked_days_to_x_date:
        reason_codes.append("days_to_x_date_blocked")
    elif days_to_x_date <= config.watch_days_to_x_date:
        reason_codes.append("days_to_x_date_watch")
    if negotiation_stress_ratio >= config.blocked_negotiation_stress_ratio:
        reason_codes.append("negotiation_stress_blocked")
    elif negotiation_stress_ratio >= config.watch_negotiation_stress_ratio:
        reason_codes.append("negotiation_stress_watch")
    if signal_age_hours > config.max_signal_age_hours:
        reason_codes.append("policy_signal_stale")
    return _normalize_reason_codes(reason_codes, require_nonempty=True)


def _risk_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in reason_codes for reason_code in BLOCKED_ROW_REASONS):
        return "high_risk"
    if any(reason_code in reason_codes for reason_code in WATCH_ROW_REASONS):
        return "watch"
    return "low_risk"


def _digest_status(rows: tuple[DebtCeilingXDateDigestRow, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.risk_status == "high_risk" for row in rows):
        return "blocked"
    if any(row.risk_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _recommended_next_step(digest_status: str) -> str:
    if digest_status == "pass":
        return "allow_report_only_market_research_policy_debt_ceiling_x_date_digest"
    if digest_status == "watch":
        return "monitor_report_only_market_research_policy_debt_ceiling_x_date_digest"
    return "block_report_only_market_research_policy_debt_ceiling_x_date_digest"


def _report_reason_codes(
    rows: tuple[DebtCeilingXDateDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("debt_ceiling_x_date_digest_empty",)
    row_reason_codes = tuple(reason_code for row in rows for reason_code in row.reason_codes)
    reason_codes: list[str] = []
    if any(row.risk_status == "high_risk" for row in rows):
        reason_codes.append("debt_ceiling_x_date_high_risk_present")
    if any(row.risk_status == "watch" for row in rows):
        reason_codes.append("debt_ceiling_x_date_watch_present")
    if all(row.risk_status == "low_risk" for row in rows):
        reason_codes.append("debt_ceiling_x_date_low_risk_only")
    if "policy_signal_stale" in row_reason_codes:
        reason_codes.append("debt_ceiling_x_date_stale_signal_present")
    mapping = (
        ("x_date_slippage_blocked", "x_date_slippage_blocked_present"),
        ("x_date_slippage_watch", "x_date_slippage_watch_present"),
        ("days_to_x_date_blocked", "days_to_x_date_blocked_present"),
        ("days_to_x_date_watch", "days_to_x_date_watch_present"),
        ("negotiation_stress_blocked", "negotiation_stress_blocked_present"),
        ("negotiation_stress_watch", "negotiation_stress_watch_present"),
    )
    for row_reason, report_reason in mapping:
        if row_reason in row_reason_codes:
            reason_codes.append(report_reason)
    return _normalize_report_reason_codes(reason_codes)


def _validate_config(
    config: MarketResearchPolicyDebtCeilingXDateDigestConfig,
) -> None:
    if config.watch_days_to_x_date < config.blocked_days_to_x_date:
        raise ValueError("watch_days_to_x_date must be at least blocked_days_to_x_date")
    if config.blocked_slippage_days < config.watch_slippage_days:
        raise ValueError("blocked_slippage_days must be at least watch_slippage_days")
    if config.blocked_negotiation_stress_ratio < config.watch_negotiation_stress_ratio:
        raise ValueError(
            "blocked_negotiation_stress_ratio must be at least watch threshold",
        )


def _validate_row(row: DebtCeilingXDateDigestRow) -> None:
    expected_slippage = _nonnegative_elapsed_days(row.baseline_x_date, row.latest_x_date)
    if row.slippage_days != expected_slippage:
        raise ValueError("slippage_days must match baseline_x_date and latest_x_date")
    if row.risk_status != _risk_status(row.reason_codes):
        raise ValueError("risk_status must match reason_codes")


def _validate_report(report: DebtCeilingXDateDigestReport) -> None:
    if report.input_count != _count_decimal(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.high_risk_count != _status_count(report.rows, "high_risk"):
        raise ValueError("high_risk_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.low_risk_count != _status_count(report.rows, "low_risk"):
        raise ValueError("low_risk_count must match rows")
    if report.input_count != report.high_risk_count + report.watch_count + report.low_risk_count:
        raise ValueError("input_count must match risk status counts")
    if report.stale_signal_count != _reason_count(report.rows, "policy_signal_stale"):
        raise ValueError("stale_signal_count must match rows")
    if report.max_slippage_days != _max_decimal(row.slippage_days for row in report.rows):
        raise ValueError("max_slippage_days must match rows")
    if report.min_days_to_x_date != _min_decimal(row.days_to_x_date for row in report.rows):
        raise ValueError("min_days_to_x_date must match rows")
    if report.max_negotiation_stress_ratio != _max_decimal(
        (row.negotiation_stress_ratio for row in report.rows),
    ):
        raise ValueError("max_negotiation_stress_ratio must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step must match digest_status")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_inputs(
    values: Iterable[DebtCeilingXDateSignal],
) -> tuple[DebtCeilingXDateSignal, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("inputs must contain DebtCeilingXDateSignal values")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError("inputs must contain DebtCeilingXDateSignal values") from exc
    seen: set[str] = set()
    for value in normalized:
        if type(value) is not DebtCeilingXDateSignal:
            raise ValueError("inputs must contain DebtCeilingXDateSignal values")
        _require_hard_flags("signal", value)
        if value.signal_id in seen:
            raise ValueError("inputs must not contain duplicate signal_id values")
        seen.add(value.signal_id)
    return normalized


def _normalize_rows(
    values: Iterable[DebtCeilingXDateDigestRow],
) -> tuple[DebtCeilingXDateDigestRow, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("rows must contain DebtCeilingXDateDigestRow values")
    try:
        rows = tuple(values)
    except TypeError as exc:
        raise ValueError("rows must contain DebtCeilingXDateDigestRow values") from exc
    for row in rows:
        if type(row) is not DebtCeilingXDateDigestRow:
            raise ValueError("rows must contain DebtCeilingXDateDigestRow values")
        _require_hard_flags("row", row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    return rows


def _normalize_reason_codes(
    values: Iterable[str],
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    if require_nonempty and not normalized:
        raise ValueError("reason_codes must contain at least one value")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must not contain duplicates")
    for reason_code in normalized:
        _require_canonical_string("reason_codes", reason_code)
    return tuple(sorted(normalized))


def _normalize_report_reason_codes(values: Iterable[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    if not normalized:
        raise ValueError("reason_codes must contain at least one value")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must not contain duplicates")
    for reason_code in normalized:
        _require_member("reason_codes", reason_code, REPORT_REASON_SEQUENCE)
    return tuple(
        reason_code
        for reason_code in REPORT_REASON_SEQUENCE
        if reason_code in normalized
    )


def _row_sort_key(
    row: DebtCeilingXDateDigestRow,
) -> tuple[Decimal, Decimal, Decimal, Decimal, Decimal, str, str]:
    return (
        STATUS_WEIGHT[row.risk_status],
        row.days_to_x_date,
        -row.slippage_days,
        -row.negotiation_stress_ratio,
        -row.probability_event_relevance,
        row.market_slug,
        row.signal_id,
    )


def _status_count(rows: tuple[DebtCeilingXDateDigestRow, ...], status: str) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.risk_status == status))


def _reason_count(rows: tuple[DebtCeilingXDateDigestRow, ...], reason_code: str) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _max_decimal(values: Iterable[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return ZERO
    return max(normalized)


def _min_decimal(values: Iterable[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return ZERO
    return min(normalized)


def _nonnegative_elapsed_days(later: datetime, earlier: datetime) -> Decimal:
    if later <= earlier:
        return ZERO
    return _quantize_decimal(_elapsed_seconds(later, earlier) / SECONDS_PER_DAY)


def _elapsed_hours(later: datetime, earlier: datetime) -> Decimal:
    if later < earlier:
        raise ValueError("later datetime must not be before earlier datetime")
    return _quantize_decimal(_elapsed_seconds(later, earlier) / SECONDS_PER_HOUR)


def _elapsed_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    whole_seconds = Decimal(delta.days) * SECONDS_PER_DAY + Decimal(delta.seconds)
    fractional_seconds = Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    return _quantize_decimal(whole_seconds + fractional_seconds)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must be supported")


def _require_exact_type(value: object, type_: type[object], label: str) -> None:
    if type(value) is not type_:
        raise ValueError(f"{label} must be exactly {type_.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _payload_value(value: object) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    return value
