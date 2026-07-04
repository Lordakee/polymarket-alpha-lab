"""Read-only Phase 1 profile for market category probability volatility."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)
from polymarket_alpha_lab.team_taxonomy import require_team_category_pair


DEFAULT_MARKET_CATEGORY_VOLATILITY_PROFILE_CONFIG_VERSION = (
    "market-category-volatility-profile-v0"
)
RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
STABILITY_BUCKETS = (
    "insufficient_history",
    "stable",
    "watch",
    "volatile",
)
REPORT_STATUSES = (
    "empty_snapshot_set",
    "insufficient_history",
    "stable",
    "watch",
    "volatile",
)
REASON_CODE_SEQUENCE = (
    "missing_snapshot_history",
    "missing_team_coverage",
    "category_volatility_high",
    "range_expansion_high",
    "category_volatility_watch",
    "category_stable",
)


@dataclass(frozen=True)
class MarketCategoryVolatilityProfileConfig:
    config_version: str = DEFAULT_MARKET_CATEGORY_VOLATILITY_PROFILE_CONFIG_VERSION
    min_snapshot_count: Decimal = Decimal("2.000000")
    min_team_count: Decimal = Decimal("1.000000")
    stable_volatility_threshold: Decimal = Decimal("0.050000")
    high_volatility_threshold: Decimal = Decimal("0.250000")
    range_expansion_threshold: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "min_snapshot_count",
            _normalize_positive_count("min_snapshot_count", self.min_snapshot_count),
        )
        object.__setattr__(
            self,
            "min_team_count",
            _normalize_positive_count("min_team_count", self.min_team_count),
        )
        for field_name in (
            "stable_volatility_threshold",
            "high_volatility_threshold",
            "range_expansion_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.high_volatility_threshold <= self.stable_volatility_threshold:
            raise ValueError(
                "high_volatility_threshold must exceed stable_volatility_threshold",
            )
        require_paper_only_flags("MarketCategoryVolatilityProfileConfig", self)


@dataclass(frozen=True)
class MarketCategoryProbabilitySnapshot:
    snapshot_id: str
    category_id: str
    team_id: str
    forecast_probability: Decimal
    generated_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("snapshot_id", self.snapshot_id)
        team_id, category_id = require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        object.__setattr__(self, "team_id", team_id)
        object.__setattr__(self, "category_id", category_id)
        object.__setattr__(
            self,
            "forecast_probability",
            _normalize_probability("forecast_probability", self.forecast_probability),
        )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        require_paper_only_flags("MarketCategoryProbabilitySnapshot", self)


@dataclass(frozen=True)
class MarketCategoryVolatilityProfileRow:
    category_id: str
    snapshot_count: Decimal
    team_count: Decimal
    first_snapshot_at: datetime
    latest_snapshot_at: datetime
    min_probability: Decimal
    max_probability: Decimal
    average_probability: Decimal
    category_volatility: Decimal
    first_probability_range: Decimal
    latest_probability_range: Decimal
    range_expansion: Decimal
    stability_bucket: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_category_id("category_id", self.category_id)
        object.__setattr__(
            self,
            "snapshot_count",
            _normalize_positive_count("snapshot_count", self.snapshot_count),
        )
        object.__setattr__(
            self,
            "team_count",
            _normalize_positive_count("team_count", self.team_count),
        )
        object.__setattr__(
            self,
            "first_snapshot_at",
            _as_utc("first_snapshot_at", self.first_snapshot_at),
        )
        object.__setattr__(
            self,
            "latest_snapshot_at",
            _as_utc("latest_snapshot_at", self.latest_snapshot_at),
        )
        if self.latest_snapshot_at < self.first_snapshot_at:
            raise ValueError("latest_snapshot_at must not precede first_snapshot_at")
        for field_name in (
            "min_probability",
            "max_probability",
            "average_probability",
            "category_volatility",
            "first_probability_range",
            "latest_probability_range",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "range_expansion",
            _normalize_signed_ratio("range_expansion", self.range_expansion),
        )
        if self.max_probability < self.min_probability:
            raise ValueError("max_probability must be at least min_probability")
        if self.category_volatility != _quantize_ratio(
            self.max_probability - self.min_probability,
        ):
            raise ValueError("category_volatility must match probability bounds")
        if self.range_expansion != _quantize_signed_ratio(
            self.latest_probability_range - self.first_probability_range,
        ):
            raise ValueError("range_expansion must match probability ranges")
        if self.stability_bucket not in STABILITY_BUCKETS:
            raise ValueError("stability_bucket must be a known bucket")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_reason_codes(self)
        require_paper_only_flags("MarketCategoryVolatilityProfileRow", self)


@dataclass(frozen=True)
class MarketCategoryVolatilityProfileReport:
    generated_at: datetime
    config_version: str
    snapshot_count: Decimal
    category_count: Decimal
    volatile_category_count: Decimal
    watch_category_count: Decimal
    stable_category_count: Decimal
    insufficient_history_category_count: Decimal
    max_category_volatility: Decimal | None
    max_range_expansion: Decimal | None
    status: str
    rows: tuple[MarketCategoryVolatilityProfileRow, ...]
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
            "snapshot_count",
            "category_count",
            "volatile_category_count",
            "watch_category_count",
            "stable_category_count",
            "insufficient_history_category_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_category_volatility",
            _normalize_optional_probability(
                "max_category_volatility",
                self.max_category_volatility,
            ),
        )
        object.__setattr__(
            self,
            "max_range_expansion",
            _normalize_optional_signed_ratio(
                "max_range_expansion",
                self.max_range_expansion,
            ),
        )
        if self.status not in REPORT_STATUSES:
            raise ValueError("status must be a known volatility profile report status")
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        require_paper_only_flags("MarketCategoryVolatilityProfileReport", self)


def build_market_category_volatility_profile_report(
    snapshots: Iterable[MarketCategoryProbabilitySnapshot],
    *,
    config: MarketCategoryVolatilityProfileConfig,
    generated_at: datetime,
) -> MarketCategoryVolatilityProfileReport:
    if isinstance(snapshots, (str, bytes)):
        raise ValueError("snapshots must be an iterable")
    if type(config) is not MarketCategoryVolatilityProfileConfig:
        raise ValueError("config must be a MarketCategoryVolatilityProfileConfig")
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be exactly datetime")
    require_paper_only_flags("MarketCategoryVolatilityProfileConfig", config)

    try:
        snapshot_items = tuple(snapshots)
    except TypeError as exc:
        raise ValueError("snapshots must be an iterable") from exc
    _validate_snapshots(snapshot_items)

    rows = _build_rows(snapshot_items, config)
    return MarketCategoryVolatilityProfileReport(
        generated_at=generated_at,
        config_version=config.config_version,
        snapshot_count=_decimal_count(len(snapshot_items)),
        category_count=_decimal_count(len(rows)),
        volatile_category_count=_bucket_count(rows, "volatile"),
        watch_category_count=_bucket_count(rows, "watch"),
        stable_category_count=_bucket_count(rows, "stable"),
        insufficient_history_category_count=_bucket_count(rows, "insufficient_history"),
        max_category_volatility=_max_category_volatility(rows),
        max_range_expansion=_max_range_expansion(rows),
        status=_report_status(rows),
        rows=rows,
    )


def market_category_volatility_profile_payload(
    report: MarketCategoryVolatilityProfileReport,
) -> dict[str, Any]:
    if type(report) is not MarketCategoryVolatilityProfileReport:
        raise ValueError("report must be a MarketCategoryVolatilityProfileReport")
    require_paper_only_flags("MarketCategoryVolatilityProfileReport", report)
    reject_unsafe_surface_fields("market category volatility profile report", report)
    _reject_public_int_float_values(
        "market category volatility profile report",
        report,
    )
    payload = json_ready_no_floats(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    reject_unsafe_surface_fields("market category volatility profile payload", payload)
    _reject_public_int_float_values(
        "market category volatility profile payload",
        payload,
    )
    return payload


def _validate_snapshots(
    snapshots: tuple[MarketCategoryProbabilitySnapshot, ...],
) -> None:
    seen_ids: set[str] = set()
    for snapshot in snapshots:
        if type(snapshot) is not MarketCategoryProbabilitySnapshot:
            raise ValueError(
                "snapshots must contain MarketCategoryProbabilitySnapshot values",
            )
        try:
            require_paper_only_flags("MarketCategoryProbabilitySnapshot", snapshot)
        except ValueError as exc:
            raise ValueError("snapshots must be paper-only") from exc
        if snapshot.snapshot_id in seen_ids:
            raise ValueError("snapshots must use unique snapshot_id values")
        seen_ids.add(snapshot.snapshot_id)


def _build_rows(
    snapshots: tuple[MarketCategoryProbabilitySnapshot, ...],
    config: MarketCategoryVolatilityProfileConfig,
) -> tuple[MarketCategoryVolatilityProfileRow, ...]:
    grouped: dict[str, list[MarketCategoryProbabilitySnapshot]] = {}
    for snapshot in snapshots:
        grouped.setdefault(snapshot.category_id, []).append(snapshot)

    rows: list[MarketCategoryVolatilityProfileRow] = []
    for category_id, category_snapshots in sorted(grouped.items()):
        timeline = tuple(sorted(category_snapshots, key=_snapshot_rank))
        snapshot_count = _decimal_count(len(timeline))
        team_count = _decimal_count(len({snapshot.team_id for snapshot in timeline}))
        probabilities = tuple(snapshot.forecast_probability for snapshot in timeline)
        first_at = timeline[0].generated_at
        latest_at = timeline[-1].generated_at
        first_range = _probability_range(
            tuple(
                snapshot.forecast_probability
                for snapshot in timeline
                if snapshot.generated_at == first_at
            ),
        )
        latest_range = _probability_range(
            tuple(
                snapshot.forecast_probability
                for snapshot in timeline
                if snapshot.generated_at == latest_at
            ),
        )
        category_volatility = _probability_range(probabilities)
        range_expansion = _quantize_signed_ratio(latest_range - first_range)
        stability_bucket, reason_codes = _stability_bucket(
            snapshot_count=snapshot_count,
            team_count=team_count,
            category_volatility=category_volatility,
            range_expansion=range_expansion,
            config=config,
        )
        rows.append(
            MarketCategoryVolatilityProfileRow(
                category_id=category_id,
                snapshot_count=snapshot_count,
                team_count=team_count,
                first_snapshot_at=first_at,
                latest_snapshot_at=latest_at,
                min_probability=min(probabilities),
                max_probability=max(probabilities),
                average_probability=_mean(probabilities),
                category_volatility=category_volatility,
                first_probability_range=first_range,
                latest_probability_range=latest_range,
                range_expansion=range_expansion,
                stability_bucket=stability_bucket,
                reason_codes=reason_codes,
            ),
        )
    return tuple(rows)


def _snapshot_rank(
    snapshot: MarketCategoryProbabilitySnapshot,
) -> tuple[datetime, str, str]:
    return snapshot.generated_at, snapshot.team_id, snapshot.snapshot_id


def _stability_bucket(
    *,
    snapshot_count: Decimal,
    team_count: Decimal,
    category_volatility: Decimal,
    range_expansion: Decimal,
    config: MarketCategoryVolatilityProfileConfig,
) -> tuple[str, tuple[str, ...]]:
    reason_codes: list[str] = []
    if snapshot_count < config.min_snapshot_count:
        reason_codes.append("missing_snapshot_history")
    if team_count < config.min_team_count:
        reason_codes.append("missing_team_coverage")
    if reason_codes:
        return "insufficient_history", tuple(reason_codes)
    if category_volatility >= config.high_volatility_threshold:
        reason_codes.append("category_volatility_high")
    if range_expansion >= config.range_expansion_threshold:
        reason_codes.append("range_expansion_high")
    if reason_codes:
        return "volatile", tuple(reason_codes)
    if category_volatility <= config.stable_volatility_threshold:
        return "stable", ("category_stable",)
    return "watch", ("category_volatility_watch",)


def _report_status(rows: tuple[MarketCategoryVolatilityProfileRow, ...]) -> str:
    if not rows:
        return "empty_snapshot_set"
    if any(row.stability_bucket == "volatile" for row in rows):
        return "volatile"
    if any(row.stability_bucket == "watch" for row in rows):
        return "watch"
    if any(row.stability_bucket == "insufficient_history" for row in rows):
        return "insufficient_history"
    return "stable"


def _bucket_count(
    rows: tuple[MarketCategoryVolatilityProfileRow, ...],
    bucket: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.stability_bucket == bucket))


def _probability_range(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        raise ValueError("probability values must not be empty")
    return _quantize_ratio(max(values) - min(values))


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        raise ValueError("probability values must not be empty")
    return _quantize_ratio(sum(values, ZERO) / Decimal(len(values)))


def _max_category_volatility(
    rows: tuple[MarketCategoryVolatilityProfileRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize_ratio(max(row.category_volatility for row in rows))


def _max_range_expansion(
    rows: tuple[MarketCategoryVolatilityProfileRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize_signed_ratio(max(row.range_expansion for row in rows))


def _validate_report(report: MarketCategoryVolatilityProfileReport) -> None:
    if report.category_count != _decimal_count(len(report.rows)):
        raise ValueError("rows must match category_count")
    if report.volatile_category_count != _bucket_count(report.rows, "volatile"):
        raise ValueError("volatile_category_count must match rows")
    if report.watch_category_count != _bucket_count(report.rows, "watch"):
        raise ValueError("watch_category_count must match rows")
    if report.stable_category_count != _bucket_count(report.rows, "stable"):
        raise ValueError("stable_category_count must match rows")
    if report.insufficient_history_category_count != _bucket_count(
        report.rows,
        "insufficient_history",
    ):
        raise ValueError("insufficient_history_category_count must match rows")
    if report.snapshot_count < sum(
        (row.snapshot_count for row in report.rows),
        ZERO,
    ):
        raise ValueError("snapshot_count must cover row snapshots")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if not report.rows:
        if report.snapshot_count != ZERO:
            raise ValueError("snapshot_count must be zero without rows")
        if report.max_category_volatility is not None:
            raise ValueError("max_category_volatility must be absent without rows")
        if report.max_range_expansion is not None:
            raise ValueError("max_range_expansion must be absent without rows")
    else:
        if report.max_category_volatility != _max_category_volatility(report.rows):
            raise ValueError("max_category_volatility must match rows")
        if report.max_range_expansion != _max_range_expansion(report.rows):
            raise ValueError("max_range_expansion must match rows")


def _normalize_rows(value: object) -> tuple[MarketCategoryVolatilityProfileRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in rows:
        if type(row) is not MarketCategoryVolatilityProfileRow:
            raise ValueError("rows must contain MarketCategoryVolatilityProfileRow values")
        require_paper_only_flags("MarketCategoryVolatilityProfileRow", row)
    if tuple(sorted(rows, key=lambda row: row.category_id)) != rows:
        raise ValueError("rows must be sorted by category_id")
    if len({row.category_id for row in rows}) != len(rows):
        raise ValueError("rows must use unique category_id values")
    return rows


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        reason_codes = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in REASON_CODE_SEQUENCE:
            raise ValueError("reason_codes must contain known reason codes")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    if tuple(code for code in REASON_CODE_SEQUENCE if code in reason_codes) != reason_codes:
        raise ValueError("reason_codes must be deterministic")
    return reason_codes


def _validate_row_reason_codes(row: MarketCategoryVolatilityProfileRow) -> None:
    if row.stability_bucket == "insufficient_history":
        allowed = {"missing_snapshot_history", "missing_team_coverage"}
    elif row.stability_bucket == "volatile":
        allowed = {"category_volatility_high", "range_expansion_high"}
    elif row.stability_bucket == "watch":
        allowed = {"category_volatility_watch"}
    else:
        allowed = {"category_stable"}
    if set(row.reason_codes) - allowed:
        raise ValueError("reason_codes must match stability_bucket")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    normalized = value.astimezone(UTC)
    return datetime(
        normalized.year,
        normalized.month,
        normalized.day,
        normalized.hour,
        normalized.minute,
        normalized.second,
        normalized.microsecond,
        tzinfo=UTC,
        fold=normalized.fold,
    )


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_category_id(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    _require_canonical_string(field_name, value)


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    count = _normalize_count(field_name, value)
    if count < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return count


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    count = _normalize_count(field_name, value)
    if count <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return count


def _normalize_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return value.quantize(RATIO_QUANTUM)


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(RATIO_QUANTUM)


def _normalize_optional_probability(
    field_name: str,
    value: Decimal | None,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_probability(field_name, value)


def _normalize_optional_signed_ratio(
    field_name: str,
    value: Decimal | None,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_signed_ratio(field_name, value)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize_ratio(value)


def _normalize_signed_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < -ONE or value > ONE:
        raise ValueError(f"{field_name} must be between -1 and 1")
    return _quantize_signed_ratio(value)


def _quantize_ratio(value: Decimal) -> Decimal:
    if not value.is_finite():
        raise ValueError("ratio must be finite")
    return value.quantize(RATIO_QUANTUM)


def _quantize_signed_ratio(value: Decimal) -> Decimal:
    if not value.is_finite():
        raise ValueError("ratio must be finite")
    return value.quantize(RATIO_QUANTUM)


def _reject_public_int_float_values(label: str, value: object) -> None:
    _reject_public_int_float_values_at(label, "value", value)


def _reject_public_int_float_values_at(
    label: str,
    field_name: str,
    value: object,
) -> None:
    if type(value) is int:
        raise ValueError(f"{field_name} public numeric value must be a Decimal in {label}")
    if type(value) is float:
        raise ValueError(f"{field_name} public numeric value must be a Decimal in {label}")
    if isinstance(value, (Decimal, datetime, str, bool)) or value is None:
        return
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_public_int_float_values_at(
                label,
                field.name,
                getattr(value, field.name),
            )
        return
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_public_int_float_values_at(label, "payload_key", key)
            _reject_public_int_float_values_at(label, str(key), item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_int_float_values_at(label, field_name, item)


__all__ = (
    "DEFAULT_MARKET_CATEGORY_VOLATILITY_PROFILE_CONFIG_VERSION",
    "MarketCategoryProbabilitySnapshot",
    "MarketCategoryVolatilityProfileConfig",
    "MarketCategoryVolatilityProfileReport",
    "MarketCategoryVolatilityProfileRow",
    "build_market_category_volatility_profile_report",
    "market_category_volatility_profile_payload",
)
