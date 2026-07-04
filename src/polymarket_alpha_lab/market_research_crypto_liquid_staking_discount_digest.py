"""Pure report-only digest for crypto liquid staking discount research."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from typing import Any


DEFAULT_MARKET_RESEARCH_CRYPTO_LIQUID_STAKING_DISCOUNT_DIGEST_CONFIG_VERSION = (
    "market-research-crypto-liquid-staking-discount-digest-v0"
)

_DECIMAL_CONTEXT = Context(prec=64)
_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_MICROSECONDS_PER_SECOND = Decimal("1000000")
_MICROSECONDS_PER_HOUR = Decimal("3600000000")
_REDACTED_SOURCE_REF = "<redacted-source-ref>"

_DIGEST_STATUSES = ("blocked", "watch", "clear")
_STATUS_WEIGHTS = {"blocked": 0, "watch": 1, "clear": 2}
_EMPTY_REASON = "crypto_liquid_staking_discount_inventory_empty"
_CLEAR_REASON = "crypto_liquid_staking_discount_clear"
_RATIO_BLOCKED_REASON = "crypto_liquid_staking_discount_ratio_blocked"
_RATIO_WATCH_REASON = "crypto_liquid_staking_discount_ratio_watch"
_SOURCE_AGE_BLOCKED_REASON = "crypto_liquid_staking_discount_source_age_blocked"
_SOURCE_AGE_WATCH_REASON = "crypto_liquid_staking_discount_source_age_watch"
_REASON_RANK = {
    _RATIO_BLOCKED_REASON: 0,
    _SOURCE_AGE_BLOCKED_REASON: 1,
    _RATIO_WATCH_REASON: 2,
    _SOURCE_AGE_WATCH_REASON: 3,
    _CLEAR_REASON: 4,
    _EMPTY_REASON: 5,
}
_NEXT_STEPS = {
    "blocked": "block_report_only_crypto_liquid_staking_discount_research",
    "watch": "refresh_report_only_crypto_liquid_staking_discount_research",
    "clear": "allow_report_only_crypto_liquid_staking_discount_research",
}


__all__ = (
    "DEFAULT_MARKET_RESEARCH_CRYPTO_LIQUID_STAKING_DISCOUNT_DIGEST_CONFIG_VERSION",
    "MarketResearchCryptoLiquidStakingDiscountDigestConfig",
    "MarketResearchCryptoLiquidStakingDiscountDigestReport",
    "MarketResearchCryptoLiquidStakingDiscountDigestRow",
    "MarketResearchCryptoLiquidStakingDiscountObservation",
    "build_market_research_crypto_liquid_staking_discount_digest",
    "market_research_crypto_liquid_staking_discount_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchCryptoLiquidStakingDiscountDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_CRYPTO_LIQUID_STAKING_DISCOUNT_DIGEST_CONFIG_VERSION
    )
    watch_discount_ratio: Decimal = Decimal("0.010000")
    blocked_discount_ratio: Decimal = Decimal("0.030000")
    watch_source_age_hours: Decimal = Decimal("12.000000")
    blocked_source_age_hours: Decimal = Decimal("48.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            MarketResearchCryptoLiquidStakingDiscountDigestConfig,
        )
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "watch_discount_ratio",
            _normalize_ratio("watch_discount_ratio", self.watch_discount_ratio),
        )
        object.__setattr__(
            self,
            "blocked_discount_ratio",
            _normalize_ratio("blocked_discount_ratio", self.blocked_discount_ratio),
        )
        if self.watch_discount_ratio > self.blocked_discount_ratio:
            raise ValueError("watch_discount_ratio must be at most blocked_discount_ratio")
        object.__setattr__(
            self,
            "watch_source_age_hours",
            _normalize_nonnegative_decimal(
                "watch_source_age_hours",
                self.watch_source_age_hours,
            ),
        )
        object.__setattr__(
            self,
            "blocked_source_age_hours",
            _normalize_nonnegative_decimal(
                "blocked_source_age_hours",
                self.blocked_source_age_hours,
            ),
        )
        if self.watch_source_age_hours > self.blocked_source_age_hours:
            raise ValueError("watch_source_age_hours must be at most blocked_source_age_hours")
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketResearchCryptoLiquidStakingDiscountObservation:
    asset_slug: str
    observation_id: str
    derivative_asset_slug: str
    protocol_slug: str
    chain_slug: str
    observed_at: datetime
    derivative_price: Decimal
    backing_asset_price: Decimal
    source_ref: str = _REDACTED_SOURCE_REF
    source_config_version: str = (
        DEFAULT_MARKET_RESEARCH_CRYPTO_LIQUID_STAKING_DISCOUNT_DIGEST_CONFIG_VERSION
    )
    reason_codes: tuple[str, ...] = ("liquid_staking_discount_observed",)
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "observation",
            self,
            MarketResearchCryptoLiquidStakingDiscountObservation,
        )
        _require_canonical_string("asset_slug", self.asset_slug)
        _require_canonical_string("observation_id", self.observation_id)
        _require_canonical_string("derivative_asset_slug", self.derivative_asset_slug)
        _require_canonical_string("protocol_slug", self.protocol_slug)
        _require_canonical_string("chain_slug", self.chain_slug)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "derivative_price",
            _normalize_positive_decimal("derivative_price", self.derivative_price),
        )
        object.__setattr__(
            self,
            "backing_asset_price",
            _normalize_positive_decimal("backing_asset_price", self.backing_asset_price),
        )
        _require_canonical_string("source_ref", self.source_ref)
        object.__setattr__(self, "source_ref", _REDACTED_SOURCE_REF)
        _require_canonical_string("source_config_version", self.source_config_version)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes_preserving_sequence(self.reason_codes),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketResearchCryptoLiquidStakingDiscountDigestRow:
    asset_slug: str
    observation_id: str
    derivative_asset_slug: str
    protocol_slug: str
    chain_slug: str
    observed_at: datetime
    derivative_price: Decimal
    backing_asset_price: Decimal
    discount_ratio: Decimal
    source_age_hours: Decimal
    source_ref: str
    digest_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "row",
            self,
            MarketResearchCryptoLiquidStakingDiscountDigestRow,
        )
        _require_canonical_string("asset_slug", self.asset_slug)
        _require_canonical_string("observation_id", self.observation_id)
        _require_canonical_string("derivative_asset_slug", self.derivative_asset_slug)
        _require_canonical_string("protocol_slug", self.protocol_slug)
        _require_canonical_string("chain_slug", self.chain_slug)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "derivative_price",
            _normalize_positive_decimal("derivative_price", self.derivative_price),
        )
        object.__setattr__(
            self,
            "backing_asset_price",
            _normalize_positive_decimal("backing_asset_price", self.backing_asset_price),
        )
        for field_name in ("discount_ratio", "source_age_hours"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.discount_ratio > _ONE:
            raise ValueError("discount_ratio must be between 0 and 1")
        _require_canonical_string("source_ref", self.source_ref)
        object.__setattr__(self, "source_ref", _REDACTED_SOURCE_REF)
        _require_digest_status("digest_status", self.digest_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes_preserving_sequence(self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketResearchCryptoLiquidStakingDiscountDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    observation_count: Decimal
    clear_observation_count: Decimal
    watch_observation_count: Decimal
    blocked_observation_count: Decimal
    max_discount_ratio: Decimal
    max_source_age_hours: Decimal
    reason_codes: tuple[str, ...]
    source_config_versions: tuple[tuple[str, str, str], ...]
    rows: tuple[MarketResearchCryptoLiquidStakingDiscountDigestRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "report",
            self,
            MarketResearchCryptoLiquidStakingDiscountDigestReport,
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_digest_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "observation_count",
            "clear_observation_count",
            "watch_observation_count",
            "blocked_observation_count",
            "max_discount_ratio",
            "max_source_age_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.max_discount_ratio > _ONE:
            raise ValueError("max_discount_ratio must be between 0 and 1")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes_preserving_sequence(self.reason_codes),
        )
        object.__setattr__(
            self,
            "source_config_versions",
            _normalize_source_config_versions(self.source_config_versions),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_hard_flags(self)


def build_market_research_crypto_liquid_staking_discount_digest(
    observations: Iterable[MarketResearchCryptoLiquidStakingDiscountObservation],
    *,
    config: MarketResearchCryptoLiquidStakingDiscountDigestConfig,
    generated_at: datetime,
) -> MarketResearchCryptoLiquidStakingDiscountDigestReport:
    if type(config) is not MarketResearchCryptoLiquidStakingDiscountDigestConfig:
        raise ValueError(
            "config must be a MarketResearchCryptoLiquidStakingDiscountDigestConfig",
        )
    _require_hard_flags(config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    rows = tuple(
        sorted(
            (
                _row_from_observation(
                    item,
                    config=config,
                    generated_at=generated_at,
                )
                for item in normalized_observations
            ),
            key=_row_sort_key,
        ),
    )
    digest_status = _report_status(rows)
    return MarketResearchCryptoLiquidStakingDiscountDigestReport(
        generated_at=generated_at,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=_NEXT_STEPS[digest_status],
        observation_count=_count_decimal(rows),
        clear_observation_count=_count_decimal(
            row for row in rows if row.digest_status == "clear"
        ),
        watch_observation_count=_count_decimal(
            row for row in rows if row.digest_status == "watch"
        ),
        blocked_observation_count=_count_decimal(
            row for row in rows if row.digest_status == "blocked"
        ),
        max_discount_ratio=_max_decimal(row.discount_ratio for row in rows),
        max_source_age_hours=_max_decimal(row.source_age_hours for row in rows),
        reason_codes=_report_reason_codes(rows),
        source_config_versions=_source_config_versions(normalized_observations),
        rows=rows,
    )


def market_research_crypto_liquid_staking_discount_digest_payload(
    report: MarketResearchCryptoLiquidStakingDiscountDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchCryptoLiquidStakingDiscountDigestReport:
        raise ValueError(
            "report must be a MarketResearchCryptoLiquidStakingDiscountDigestReport",
        )
    _require_hard_flags(report)
    return _payload_value(report)


def _row_from_observation(
    item: MarketResearchCryptoLiquidStakingDiscountObservation,
    *,
    config: MarketResearchCryptoLiquidStakingDiscountDigestConfig,
    generated_at: datetime,
) -> MarketResearchCryptoLiquidStakingDiscountDigestRow:
    discount_ratio = _discount_ratio(item.derivative_price, item.backing_asset_price)
    source_age_hours = _past_elapsed_hours(item.observed_at, generated_at)
    reason_codes = _row_reason_codes(
        item,
        discount_ratio=discount_ratio,
        source_age_hours=source_age_hours,
        config=config,
    )
    return MarketResearchCryptoLiquidStakingDiscountDigestRow(
        asset_slug=item.asset_slug,
        observation_id=item.observation_id,
        derivative_asset_slug=item.derivative_asset_slug,
        protocol_slug=item.protocol_slug,
        chain_slug=item.chain_slug,
        observed_at=item.observed_at,
        derivative_price=item.derivative_price,
        backing_asset_price=item.backing_asset_price,
        discount_ratio=discount_ratio,
        source_age_hours=source_age_hours,
        source_ref=item.source_ref,
        digest_status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    item: MarketResearchCryptoLiquidStakingDiscountObservation,
    *,
    discount_ratio: Decimal,
    source_age_hours: Decimal,
    config: MarketResearchCryptoLiquidStakingDiscountDigestConfig,
) -> tuple[str, ...]:
    codes = list(item.reason_codes)
    if discount_ratio >= config.blocked_discount_ratio:
        codes.append(_RATIO_BLOCKED_REASON)
    elif discount_ratio >= config.watch_discount_ratio:
        codes.append(_RATIO_WATCH_REASON)
    if source_age_hours >= config.blocked_source_age_hours:
        codes.append(_SOURCE_AGE_BLOCKED_REASON)
    elif source_age_hours >= config.watch_source_age_hours:
        codes.append(_SOURCE_AGE_WATCH_REASON)
    if codes == list(item.reason_codes):
        codes.append(_CLEAR_REASON)
    return _normalize_reason_codes(tuple(codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_blocked") for reason_code in reason_codes):
        return "blocked"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "clear"


def _report_status(
    rows: tuple[MarketResearchCryptoLiquidStakingDiscountDigestRow, ...],
) -> str:
    if not rows:
        return "blocked"
    if any(row.digest_status == "blocked" for row in rows):
        return "blocked"
    if any(row.digest_status == "watch" for row in rows):
        return "watch"
    return "clear"


def _report_reason_codes(
    rows: tuple[MarketResearchCryptoLiquidStakingDiscountDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (_EMPTY_REASON,)
    report_codes = tuple(
        reason_code
        for reason_code in _REASON_RANK
        if reason_code != _EMPTY_REASON
        and reason_code != _CLEAR_REASON
        and any(reason_code in row.reason_codes for row in rows)
    )
    if report_codes:
        return report_codes
    return (_CLEAR_REASON,)


def _normalize_observations(
    values: Iterable[MarketResearchCryptoLiquidStakingDiscountObservation],
) -> tuple[MarketResearchCryptoLiquidStakingDiscountObservation, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    seen_keys: set[tuple[str, str]] = set()
    for value in normalized:
        if type(value) is not MarketResearchCryptoLiquidStakingDiscountObservation:
            raise ValueError(
                "observations must contain "
                "MarketResearchCryptoLiquidStakingDiscountObservation values",
            )
        _require_hard_flags(value)
        key = (value.asset_slug, value.observation_id)
        if key in seen_keys:
            raise ValueError("observations must not contain duplicate asset/observation pairs")
        seen_keys.add(key)
    return normalized


def _normalize_rows(
    values: Iterable[MarketResearchCryptoLiquidStakingDiscountDigestRow],
) -> tuple[MarketResearchCryptoLiquidStakingDiscountDigestRow, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(
            "rows must contain MarketResearchCryptoLiquidStakingDiscountDigestRow values",
        )
    try:
        rows = tuple(values)
    except TypeError as exc:
        raise ValueError(
            "rows must contain MarketResearchCryptoLiquidStakingDiscountDigestRow values",
        ) from exc
    for row in rows:
        if type(row) is not MarketResearchCryptoLiquidStakingDiscountDigestRow:
            raise ValueError(
                "rows must contain MarketResearchCryptoLiquidStakingDiscountDigestRow values",
            )
        _require_hard_flags(row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic liquid staking discount sort")
    return rows


def _validate_row_consistency(
    row: MarketResearchCryptoLiquidStakingDiscountDigestRow,
) -> None:
    if row.discount_ratio != _discount_ratio(row.derivative_price, row.backing_asset_price):
        raise ValueError("discount_ratio must match derivative and backing prices")
    if row.digest_status != _row_status(row.reason_codes):
        raise ValueError("digest_status must match reason_codes")


def _validate_report_consistency(
    report: MarketResearchCryptoLiquidStakingDiscountDigestReport,
) -> None:
    if report.observation_count != _count_decimal(report.rows):
        raise ValueError("observation_count must match rows")
    if report.clear_observation_count != _count_decimal(
        row for row in report.rows if row.digest_status == "clear"
    ):
        raise ValueError("clear_observation_count must match rows")
    if report.watch_observation_count != _count_decimal(
        row for row in report.rows if row.digest_status == "watch"
    ):
        raise ValueError("watch_observation_count must match rows")
    if report.blocked_observation_count != _count_decimal(
        row for row in report.rows if row.digest_status == "blocked"
    ):
        raise ValueError("blocked_observation_count must match rows")
    if report.observation_count != (
        report.clear_observation_count
        + report.watch_observation_count
        + report.blocked_observation_count
    ):
        raise ValueError("observation_count must match digest status counts")
    if report.max_discount_ratio != _max_decimal(row.discount_ratio for row in report.rows):
        raise ValueError("max_discount_ratio must match rows")
    if report.max_source_age_hours != _max_decimal(
        row.source_age_hours for row in report.rows
    ):
        raise ValueError("max_source_age_hours must match rows")
    if report.digest_status != _report_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.recommended_next_step != _NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")


def _row_sort_key(
    row: MarketResearchCryptoLiquidStakingDiscountDigestRow,
) -> tuple[int, Decimal, Decimal, str, str]:
    return (
        _STATUS_WEIGHTS[row.digest_status],
        -row.discount_ratio,
        -row.source_age_hours,
        row.asset_slug,
        row.observation_id,
    )


def _source_config_versions(
    values: tuple[MarketResearchCryptoLiquidStakingDiscountObservation, ...],
) -> tuple[tuple[str, str, str], ...]:
    return tuple(
        sorted(
            (
                value.asset_slug,
                value.observation_id,
                value.source_config_version,
            )
            for value in values
        ),
    )


def _normalize_source_config_versions(
    values: Iterable[tuple[str, str, str]],
) -> tuple[tuple[str, str, str], ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("source_config_versions must be an iterable")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError("source_config_versions must be an iterable") from exc
    for item in normalized:
        if type(item) is not tuple or len(item) != 3:
            raise ValueError("source_config_versions must contain 3-item tuples")
        for value in item:
            _require_canonical_string("source_config_versions", value)
    if normalized != tuple(sorted(normalized)):
        raise ValueError("source_config_versions must be sorted")
    return normalized


def _past_elapsed_hours(start: datetime, end: datetime) -> Decimal:
    if end <= start:
        return _ZERO
    return _elapsed_hours(start, end)


def _elapsed_hours(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    whole_seconds = Decimal(delta.days) * Decimal("86400") + Decimal(delta.seconds)
    microseconds = whole_seconds * _MICROSECONDS_PER_SECOND + Decimal(delta.microseconds)
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(microseconds / _MICROSECONDS_PER_HOUR)


def _count_decimal(values: Iterable[object]) -> Decimal:
    return _quantize(Decimal(sum(1 for _ in values)))


def _discount_ratio(derivative_price: Decimal, backing_asset_price: Decimal) -> Decimal:
    if derivative_price >= backing_asset_price:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize((backing_asset_price - derivative_price) / backing_asset_price)


def _max_decimal(values: Iterable[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return _ZERO
    return max(normalized)


def _normalize_reason_codes(value: Iterable[str]) -> tuple[str, ...]:
    normalized = _normalize_reason_codes_preserving_sequence(value)
    return tuple(sorted(normalized, key=lambda item: (_REASON_RANK.get(item, 1000), item)))


def _normalize_reason_codes_preserving_sequence(value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        normalized = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    if not normalized:
        raise ValueError("reason_codes must contain at least one value")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must not contain duplicates")
    for reason_code in normalized:
        _require_canonical_string("reason_codes", reason_code)
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANTUM)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_digest_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be blocked, watch, or clear")


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_exact_type(label: str, value: object, expected_type: type) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _payload_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return _decimal_payload(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    return value


def _decimal_payload(value: Decimal) -> str:
    return format(value, "f")
