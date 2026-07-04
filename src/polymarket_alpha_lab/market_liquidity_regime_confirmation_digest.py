"""Pure report-only market liquidity regime confirmation digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from typing import Any


__all__ = (
    "DEFAULT_MARKET_LIQUIDITY_REGIME_CONFIRMATION_DIGEST_CONFIG_VERSION",
    "MarketLiquidityRegimeConfirmationDigestConfig",
    "MarketLiquidityRegimeConfirmationDigestInput",
    "MarketLiquidityRegimeConfirmationDigestReport",
    "MarketLiquidityRegimeConfirmationDigestRow",
    "build_market_liquidity_regime_confirmation_digest",
    "market_liquidity_regime_confirmation_digest_payload",
)


DEFAULT_MARKET_LIQUIDITY_REGIME_CONFIRMATION_DIGEST_CONFIG_VERSION = (
    "market-liquidity-regime-confirmation-digest-v0"
)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64)

CONFIRMED_STATUS = "confirmed"
PARTIAL_STATUS = "partial"
UNCONFIRMED_STATUS = "unconfirmed"
CONFIRMATION_STATUSES = (
    CONFIRMED_STATUS,
    PARTIAL_STATUS,
    UNCONFIRMED_STATUS,
)
STATUS_RANK = {
    CONFIRMED_STATUS: 0,
    PARTIAL_STATUS: 1,
    UNCONFIRMED_STATUS: 2,
}
SENSITIVE_REFERENCE_MARKERS = (
    "api" + "_key=",
    "api" + "key=",
    "au" + "thor" + "ization=",
    "bearer ",
    "pass" + "word=",
    "private" + "_key=",
    "se" + "cret=",
    "sig" + "nature=",
    "to" + "ken=",
    "wal" + "let=",
)


@dataclass(frozen=True)
class MarketLiquidityRegimeConfirmationDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_LIQUIDITY_REGIME_CONFIRMATION_DIGEST_CONFIG_VERSION
    )
    min_probability_move: Decimal = Decimal("0.030000")
    min_depth_change_ratio: Decimal = Decimal("0.150000")
    min_spread_change_ratio: Decimal = Decimal("0.120000")
    max_source_age_seconds: Decimal = Decimal("300.000000")
    min_volume_proxy: Decimal = Decimal("50.000000")
    stale_confidence_cap: Decimal = Decimal("0.300000")
    thin_volume_confidence_cap: Decimal = Decimal("0.500000")
    unconfirmed_confidence_cap: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketLiquidityRegimeConfirmationDigestConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "min_probability_move",
            "min_depth_change_ratio",
            "min_spread_change_ratio",
            "stale_confidence_cap",
            "thin_volume_confidence_cap",
            "unconfirmed_confidence_cap",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_source_age_seconds", "min_volume_proxy"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketLiquidityRegimeConfirmationDigestInput:
    market_slug: str
    outcome_name: str
    probability_before: Decimal
    probability_after: Decimal
    depth_before: Decimal
    depth_after: Decimal
    spread_before: Decimal
    spread_after: Decimal
    source_observed_at: datetime
    volume_proxy: Decimal
    base_confidence: Decimal
    source_reference: str
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketLiquidityRegimeConfirmationDigestInput, "input")
        for field_name in ("market_slug", "outcome_name", "source_reference"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in ("probability_before", "probability_after", "base_confidence"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "depth_before",
            "depth_after",
            "spread_before",
            "spread_after",
            "volume_proxy",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_observed_at",
            _as_utc("source_observed_at", self.source_observed_at),
        )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_reason_codes(self.upstream_reason_codes),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketLiquidityRegimeConfirmationDigestRow:
    market_slug: str
    outcome_name: str
    probability_before: Decimal
    probability_after: Decimal
    probability_move: Decimal
    depth_before: Decimal
    depth_after: Decimal
    depth_change_ratio: Decimal
    spread_before: Decimal
    spread_after: Decimal
    spread_change_ratio: Decimal
    source_observed_at: datetime
    source_age_seconds: Decimal
    volume_proxy: Decimal
    confirmation_score: Decimal
    confidence_cap: Decimal
    capped_confidence: Decimal
    confirmation_status: str
    source_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketLiquidityRegimeConfirmationDigestRow, "row")
        for field_name in ("market_slug", "outcome_name", "source_reference"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "probability_before",
            "probability_after",
            "probability_move",
            "depth_change_ratio",
            "spread_change_ratio",
            "confirmation_score",
            "confidence_cap",
            "capped_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "depth_before",
            "depth_after",
            "spread_before",
            "spread_after",
            "source_age_seconds",
            "volume_proxy",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_observed_at",
            _as_utc("source_observed_at", self.source_observed_at),
        )
        _require_confirmation_status("confirmation_status", self.confirmation_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketLiquidityRegimeConfirmationDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    confirmed_count: Decimal
    partial_count: Decimal
    unconfirmed_count: Decimal
    stale_source_count: Decimal
    thin_volume_count: Decimal
    max_probability_move: Decimal
    max_confirmation_score: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[MarketLiquidityRegimeConfirmationDigestRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketLiquidityRegimeConfirmationDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "input_count",
            "row_count",
            "confirmed_count",
            "partial_count",
            "unconfirmed_count",
            "stale_source_count",
            "thin_volume_count",
            "max_probability_move",
            "max_confirmation_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_hard_flags(self)


def build_market_liquidity_regime_confirmation_digest(
    inputs: Iterable[MarketLiquidityRegimeConfirmationDigestInput],
    *,
    config: MarketLiquidityRegimeConfirmationDigestConfig,
    generated_at: datetime,
) -> MarketLiquidityRegimeConfirmationDigestReport:
    if type(config) is not MarketLiquidityRegimeConfirmationDigestConfig:
        raise ValueError(
            "config must be a MarketLiquidityRegimeConfirmationDigestConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    _require_hard_flags(config)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (
                _row_from_input(value, config=config, generated_at=generated_at)
                for value in normalized_inputs
            ),
            key=_row_sort_key,
        ),
    )
    return MarketLiquidityRegimeConfirmationDigestReport(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized_inputs)),
        row_count=_count_decimal(len(rows)),
        confirmed_count=_status_count(rows, CONFIRMED_STATUS),
        partial_count=_status_count(rows, PARTIAL_STATUS),
        unconfirmed_count=_status_count(rows, UNCONFIRMED_STATUS),
        stale_source_count=_count_decimal(
            sum(1 for row in rows if "source_stale" in row.reason_codes),
        ),
        thin_volume_count=_count_decimal(
            sum(1 for row in rows if "volume_proxy_thin" in row.reason_codes),
        ),
        max_probability_move=_max_row_decimal(rows, "probability_move"),
        max_confirmation_score=_max_row_decimal(rows, "confirmation_score"),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def market_liquidity_regime_confirmation_digest_payload(
    report: MarketLiquidityRegimeConfirmationDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketLiquidityRegimeConfirmationDigestReport:
        raise ValueError(
            "report must be a MarketLiquidityRegimeConfirmationDigestReport",
        )
    return _payload_value(report)


def _row_from_input(
    value: MarketLiquidityRegimeConfirmationDigestInput,
    *,
    config: MarketLiquidityRegimeConfirmationDigestConfig,
    generated_at: datetime,
) -> MarketLiquidityRegimeConfirmationDigestRow:
    probability_move = _absolute_change(value.probability_before, value.probability_after)
    depth_change_ratio = _change_ratio(value.depth_before, value.depth_after)
    spread_change_ratio = _change_ratio(value.spread_before, value.spread_after)
    source_age_seconds = _seconds_between(generated_at, value.source_observed_at)
    has_probability_move = probability_move >= config.min_probability_move
    depth_changed = depth_change_ratio >= config.min_depth_change_ratio
    spread_changed = spread_change_ratio >= config.min_spread_change_ratio
    source_fresh = source_age_seconds <= config.max_source_age_seconds
    volume_sufficient = value.volume_proxy >= config.min_volume_proxy
    confirmation_score = _confirmation_score(
        has_probability_move=has_probability_move,
        depth_changed=depth_changed,
        spread_changed=spread_changed,
        source_fresh=source_fresh,
        volume_sufficient=volume_sufficient,
    )
    status = _confirmation_status(
        has_probability_move=has_probability_move,
        depth_changed=depth_changed,
        spread_changed=spread_changed,
        source_fresh=source_fresh,
        volume_sufficient=volume_sufficient,
    )
    confidence_cap = _confidence_cap(
        status=status,
        source_fresh=source_fresh,
        volume_sufficient=volume_sufficient,
        config=config,
    )
    reason_codes = _row_reason_codes(
        value.upstream_reason_codes,
        status=status,
        has_probability_move=has_probability_move,
        depth_changed=depth_changed,
        spread_changed=spread_changed,
        source_fresh=source_fresh,
        volume_sufficient=volume_sufficient,
    )
    return MarketLiquidityRegimeConfirmationDigestRow(
        market_slug=value.market_slug,
        outcome_name=value.outcome_name,
        probability_before=value.probability_before,
        probability_after=value.probability_after,
        probability_move=probability_move,
        depth_before=value.depth_before,
        depth_after=value.depth_after,
        depth_change_ratio=depth_change_ratio,
        spread_before=value.spread_before,
        spread_after=value.spread_after,
        spread_change_ratio=spread_change_ratio,
        source_observed_at=value.source_observed_at,
        source_age_seconds=source_age_seconds,
        volume_proxy=value.volume_proxy,
        confirmation_score=confirmation_score,
        confidence_cap=confidence_cap,
        capped_confidence=min(value.base_confidence, confidence_cap),
        confirmation_status=status,
        source_reference=_redact_reference(value.source_reference),
        reason_codes=reason_codes,
    )


def _confirmation_score(
    *,
    has_probability_move: bool,
    depth_changed: bool,
    spread_changed: bool,
    source_fresh: bool,
    volume_sufficient: bool,
) -> Decimal:
    if not has_probability_move:
        return _quantize_decimal(ZERO)
    score = ZERO
    if depth_changed:
        score += Decimal("0.400000")
    if spread_changed:
        score += Decimal("0.400000")
    return _normalize_probability("confirmation_score", score)


def _confirmation_status(
    *,
    has_probability_move: bool,
    depth_changed: bool,
    spread_changed: bool,
    source_fresh: bool,
    volume_sufficient: bool,
) -> str:
    if not has_probability_move:
        return UNCONFIRMED_STATUS
    if not source_fresh or not volume_sufficient:
        return UNCONFIRMED_STATUS
    liquidity_signal_count = int(depth_changed) + int(spread_changed)
    if liquidity_signal_count == 2:
        return CONFIRMED_STATUS
    if liquidity_signal_count == 1:
        return PARTIAL_STATUS
    return UNCONFIRMED_STATUS


def _confidence_cap(
    *,
    status: str,
    source_fresh: bool,
    volume_sufficient: bool,
    config: MarketLiquidityRegimeConfirmationDigestConfig,
) -> Decimal:
    caps = [ONE]
    if not source_fresh:
        caps.append(config.stale_confidence_cap)
    if not volume_sufficient:
        caps.append(config.thin_volume_confidence_cap)
    if status != CONFIRMED_STATUS:
        caps.append(config.unconfirmed_confidence_cap)
    return _quantize_decimal(min(caps))


def _row_reason_codes(
    upstream_reason_codes: tuple[str, ...],
    *,
    status: str,
    has_probability_move: bool,
    depth_changed: bool,
    spread_changed: bool,
    source_fresh: bool,
    volume_sufficient: bool,
) -> tuple[str, ...]:
    reason_codes = list(upstream_reason_codes)
    if not has_probability_move:
        reason_codes.append("probability_move_below_threshold")
    reason_codes.append(
        "depth_regime_changed" if depth_changed else "depth_regime_unchanged",
    )
    reason_codes.append(
        "spread_regime_changed" if spread_changed else "spread_regime_unchanged",
    )
    reason_codes.append("source_fresh" if source_fresh else "source_stale")
    reason_codes.append(
        "volume_proxy_sufficient" if volume_sufficient else "volume_proxy_thin",
    )
    if status == CONFIRMED_STATUS:
        reason_codes.append("liquidity_regime_confirmed")
    elif status == PARTIAL_STATUS:
        reason_codes.append("liquidity_regime_partially_confirmed")
    else:
        reason_codes.append("liquidity_regime_unconfirmed")
    return _normalize_reason_codes(tuple(reason_codes))


def _normalize_inputs(
    inputs: Iterable[MarketLiquidityRegimeConfirmationDigestInput],
) -> tuple[MarketLiquidityRegimeConfirmationDigestInput, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Iterable):
        raise ValueError("inputs must be an iterable")
    normalized = tuple(inputs)
    for value in normalized:
        if type(value) is not MarketLiquidityRegimeConfirmationDigestInput:
            raise ValueError(
                "inputs must contain MarketLiquidityRegimeConfirmationDigestInput",
            )
        _require_hard_flags(value)
    return normalized


def _normalize_rows(
    rows: Iterable[MarketLiquidityRegimeConfirmationDigestRow],
) -> tuple[MarketLiquidityRegimeConfirmationDigestRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not MarketLiquidityRegimeConfirmationDigestRow:
            raise ValueError("rows must contain MarketLiquidityRegimeConfirmationDigestRow")
        _require_hard_flags(row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _validate_row_consistency(row: MarketLiquidityRegimeConfirmationDigestRow) -> None:
    expected_probability_move = _absolute_change(
        row.probability_before,
        row.probability_after,
    )
    if row.probability_move != expected_probability_move:
        raise ValueError("probability_move must match probability values")
    if row.depth_change_ratio != _change_ratio(row.depth_before, row.depth_after):
        raise ValueError("depth_change_ratio must match depth values")
    if row.spread_change_ratio != _change_ratio(row.spread_before, row.spread_after):
        raise ValueError("spread_change_ratio must match spread values")
    if row.capped_confidence > row.confidence_cap:
        raise ValueError("capped_confidence must not exceed confidence_cap")
    expected_status_reason = {
        CONFIRMED_STATUS: "liquidity_regime_confirmed",
        PARTIAL_STATUS: "liquidity_regime_partially_confirmed",
        UNCONFIRMED_STATUS: "liquidity_regime_unconfirmed",
    }[row.confirmation_status]
    if expected_status_reason not in row.reason_codes:
        raise ValueError("confirmation_status must match reason_codes")


def _validate_report_consistency(
    report: MarketLiquidityRegimeConfirmationDigestReport,
) -> None:
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.confirmed_count + report.partial_count + report.unconfirmed_count != (
        report.row_count
    ):
        raise ValueError("status counts must match row_count")
    if report.stale_source_count != _count_decimal(
        sum(1 for row in report.rows if "source_stale" in row.reason_codes),
    ):
        raise ValueError("stale_source_count must match rows")
    if report.thin_volume_count != _count_decimal(
        sum(1 for row in report.rows if "volume_proxy_thin" in row.reason_codes),
    ):
        raise ValueError("thin_volume_count must match rows")
    if report.max_probability_move != _max_row_decimal(report.rows, "probability_move"):
        raise ValueError("max_probability_move must match rows")
    if report.max_confirmation_score != _max_row_decimal(
        report.rows,
        "confirmation_score",
    ):
        raise ValueError("max_confirmation_score must match rows")


def _report_reason_codes(
    rows: tuple[MarketLiquidityRegimeConfirmationDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("liquidity_regime_confirmation_digest_empty",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _status_count(
    rows: tuple[MarketLiquidityRegimeConfirmationDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.confirmation_status == status))


def _max_row_decimal(
    rows: tuple[MarketLiquidityRegimeConfirmationDigestRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return _quantize_decimal(ZERO)
    return max(getattr(row, field_name) for row in rows)


def _absolute_change(before: Decimal, after: Decimal) -> Decimal:
    return _quantize_decimal(abs(after - before))


def _change_ratio(before: Decimal, after: Decimal) -> Decimal:
    if before == ZERO:
        if after == ZERO:
            return _quantize_decimal(ZERO)
        return _quantize_decimal(ONE)
    return _normalize_probability("change_ratio", abs(after - before) / before)


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    if delta.days < 0:
        raise ValueError("source_observed_at must not be after generated_at")
    whole_seconds = Decimal(delta.days * 86400 + delta.seconds)
    fractional_seconds = Decimal(delta.microseconds) / Decimal("1000000")
    return _quantize_decimal(whole_seconds + fractional_seconds)


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


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
        raise ValueError(f"{field_name} must be UTC-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_confirmation_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in CONFIRMATION_STATUSES:
        raise ValueError(f"{field_name} must be confirmed, partial, or unconfirmed")


def _normalize_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Iterable):
        raise ValueError("reason_codes must be an iterable")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_canonical_string("reason_code", reason_code)
        if _contains_sensitive_text(reason_code):
            raise ValueError("reason_code must not contain sensitive text")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(sorted(normalized))


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_exact_type(value: object, type_: type[object], label: str) -> None:
    if type(value) is not type_:
        raise ValueError(f"{label} must be exactly {type_.__name__}")


def _row_sort_key(
    row: MarketLiquidityRegimeConfirmationDigestRow,
) -> tuple[int, Decimal, str, str, datetime, str]:
    return (
        STATUS_RANK[row.confirmation_status],
        -row.confirmation_score,
        row.market_slug,
        row.outcome_name,
        row.source_observed_at,
        row.source_reference,
    )


def _contains_sensitive_text(value: str) -> bool:
    return any(marker in value.lower() for marker in SENSITIVE_REFERENCE_MARKERS)


def _redact_reference(reference: str) -> str:
    if "?" in reference and _contains_sensitive_text(reference):
        return reference.split("?", 1)[0] + "?<redacted>"
    if _contains_sensitive_text(reference):
        return "<redacted>"
    return reference


def _payload_value(value: object) -> Any:
    if isinstance(value, Decimal):
        return f"{value:.6f}"
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    return value
