"""Pure Phase 1 crypto perp open-interest flush digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import re
from typing import Any


DEFAULT_MARKET_RESEARCH_CRYPTO_PERP_OPEN_INTEREST_FLUSH_DIGEST_CONFIG_VERSION = (
    "market-research-crypto-perp-open-interest-flush-digest-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

ROW_STATUSES = ("high_risk", "watch", "clear")
REPORT_STATUSES = ("blocked", "high_risk", "watch", "clear")
LIQUIDATION_SIDES = ("balanced", "long", "short")
ROW_REASON_CODES = (
    "open_interest_drop_high",
    "open_interest_drop_watch",
    "price_move_confirms_flush",
    "liquidation_pressure_high",
    "funding_extreme",
    "source_stale",
    "open_interest_flush_clear",
)
REPORT_REASON_CODES = (
    "crypto_perp_open_interest_flush_clear",
    "crypto_perp_open_interest_flush_digest_empty",
    "crypto_perp_open_interest_flush_high_risk_present",
    "crypto_perp_open_interest_flush_stale_source_present",
    "crypto_perp_open_interest_flush_watch_present",
)
ROW_STATUS_RANK = {
    "high_risk": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "clear": Decimal("2.000000"),
}
_CANONICAL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")


__all__ = (
    "DEFAULT_MARKET_RESEARCH_CRYPTO_PERP_OPEN_INTEREST_FLUSH_DIGEST_CONFIG_VERSION",
    "MarketResearchCryptoPerpOpenInterestFlushDigestConfig",
    "CryptoPerpOpenInterestFlushObservation",
    "CryptoPerpOpenInterestFlushDigestRow",
    "CryptoPerpOpenInterestFlushReasonCodeCount",
    "CryptoPerpOpenInterestFlushDigestReport",
    "build_market_research_crypto_perp_open_interest_flush_digest",
    "market_research_crypto_perp_open_interest_flush_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchCryptoPerpOpenInterestFlushDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_CRYPTO_PERP_OPEN_INTEREST_FLUSH_DIGEST_CONFIG_VERSION
    )
    watch_open_interest_drop_ratio: Decimal = Decimal("0.060000")
    high_open_interest_drop_ratio: Decimal = Decimal("0.120000")
    min_abs_price_move_ratio: Decimal = Decimal("0.020000")
    high_liquidation_to_volume_ratio: Decimal = Decimal("0.080000")
    high_abs_funding_rate_8h: Decimal = Decimal("0.000800")
    stale_source_after_seconds: Decimal = Decimal("900.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoPerpOpenInterestFlushDigestConfig:
            raise TypeError(
                "MarketResearchCryptoPerpOpenInterestFlushDigestConfig"
                " does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchCryptoPerpOpenInterestFlushDigestConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_CRYPTO_PERP_OPEN_INTEREST_FLUSH_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_open_interest_drop_ratio",
            "high_open_interest_drop_ratio",
            "min_abs_price_move_ratio",
            "high_liquidation_to_volume_ratio",
            "high_abs_funding_rate_8h",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "stale_source_after_seconds",
            _normalize_positive_decimal(
                "stale_source_after_seconds",
                self.stale_source_after_seconds,
            ),
        )
        if self.high_open_interest_drop_ratio < self.watch_open_interest_drop_ratio:
            raise ValueError(
                "high_open_interest_drop_ratio must be at least"
                " watch_open_interest_drop_ratio",
            )
        _require_hard_flags(self)


@dataclass(frozen=True)
class CryptoPerpOpenInterestFlushObservation:
    source_id: str
    market_slug: str
    base_asset: str
    venue_id: str
    current_open_interest_usd: Decimal
    previous_open_interest_usd: Decimal
    current_mark_price: Decimal
    previous_mark_price: Decimal
    funding_rate_8h: Decimal
    long_liquidations_usd: Decimal
    short_liquidations_usd: Decimal
    volume_24h_usd: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CryptoPerpOpenInterestFlushObservation:
            raise TypeError(
                "CryptoPerpOpenInterestFlushObservation does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, CryptoPerpOpenInterestFlushObservation, "observation")
        for field_name in ("source_id", "market_slug", "base_asset", "venue_id"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "current_open_interest_usd",
            "long_liquidations_usd",
            "short_liquidations_usd",
            "volume_24h_usd",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "previous_open_interest_usd",
            "current_mark_price",
            "previous_mark_price",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "funding_rate_8h",
            _normalize_decimal("funding_rate_8h", self.funding_rate_8h),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags(self)


@dataclass(frozen=True)
class CryptoPerpOpenInterestFlushDigestRow:
    source_id: str
    market_slug: str
    base_asset: str
    venue_id: str
    current_open_interest_usd: Decimal
    previous_open_interest_usd: Decimal
    open_interest_change_ratio: Decimal
    open_interest_drop_ratio: Decimal
    current_mark_price: Decimal
    previous_mark_price: Decimal
    mark_price_change_ratio: Decimal
    abs_price_move_ratio: Decimal
    funding_rate_8h: Decimal
    long_liquidations_usd: Decimal
    short_liquidations_usd: Decimal
    volume_24h_usd: Decimal
    liquidation_to_volume_ratio: Decimal
    dominant_liquidation_side: str
    source_age_seconds: Decimal
    observed_at: datetime
    flush_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CryptoPerpOpenInterestFlushDigestRow:
            raise TypeError(
                "CryptoPerpOpenInterestFlushDigestRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, CryptoPerpOpenInterestFlushDigestRow, "row")
        for field_name in ("source_id", "market_slug", "base_asset", "venue_id"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "current_open_interest_usd",
            "long_liquidations_usd",
            "short_liquidations_usd",
            "volume_24h_usd",
            "open_interest_drop_ratio",
            "abs_price_move_ratio",
            "liquidation_to_volume_ratio",
            "source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "previous_open_interest_usd",
            "current_mark_price",
            "previous_mark_price",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "open_interest_change_ratio",
            "mark_price_change_ratio",
            "funding_rate_8h",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        _require_member(
            "dominant_liquidation_side",
            self.dominant_liquidation_side,
            LIQUIDATION_SIDES,
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_member("flush_status", self.flush_status, ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row_consistency(self)
        _require_hard_flags(self)


@dataclass(frozen=True)
class CryptoPerpOpenInterestFlushReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CryptoPerpOpenInterestFlushReasonCodeCount:
            raise TypeError(
                "CryptoPerpOpenInterestFlushReasonCodeCount"
                " does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, CryptoPerpOpenInterestFlushReasonCodeCount, "count")
        _require_member("reason_code", self.reason_code, REPORT_REASON_CODES)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _normalize_probability("row_ratio", self.row_ratio),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class CryptoPerpOpenInterestFlushDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    high_risk_count: Decimal
    watch_count: Decimal
    clear_count: Decimal
    stale_source_count: Decimal
    max_open_interest_drop_ratio: Decimal
    max_abs_price_move_ratio: Decimal
    max_liquidation_to_volume_ratio: Decimal
    digest_status: str
    recommended_next_step: str
    rows: tuple[CryptoPerpOpenInterestFlushDigestRow, ...]
    reason_code_counts: tuple[CryptoPerpOpenInterestFlushReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CryptoPerpOpenInterestFlushDigestReport:
            raise TypeError(
                "CryptoPerpOpenInterestFlushDigestReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, CryptoPerpOpenInterestFlushDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_CRYPTO_PERP_OPEN_INTEREST_FLUSH_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "high_risk_count",
            "watch_count",
            "clear_count",
            "stale_source_count",
            "max_open_interest_drop_ratio",
            "max_abs_price_move_ratio",
            "max_liquidation_to_volume_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("digest_status", self.digest_status, REPORT_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        _validate_report_consistency(self)
        _require_hard_flags(self)


def build_market_research_crypto_perp_open_interest_flush_digest(
    observations: Iterable[CryptoPerpOpenInterestFlushObservation],
    *,
    config: MarketResearchCryptoPerpOpenInterestFlushDigestConfig,
    generated_at: datetime,
) -> CryptoPerpOpenInterestFlushDigestReport:
    _require_exact_type(
        config,
        MarketResearchCryptoPerpOpenInterestFlushDigestConfig,
        "config",
    )
    generated_at = _as_utc("generated_at", generated_at)
    _require_hard_flags(config)
    normalized = _normalize_observations(observations)
    rows = tuple(
        sorted(
            (
                _row_from_observation(
                    observation,
                    config=config,
                    generated_at=generated_at,
                )
                for observation in normalized
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    return CryptoPerpOpenInterestFlushDigestReport(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized)),
        row_count=_count_decimal(len(rows)),
        high_risk_count=_status_count(rows, "high_risk"),
        watch_count=_status_count(rows, "watch"),
        clear_count=_status_count(rows, "clear"),
        stale_source_count=_row_reason_count(rows, "source_stale"),
        max_open_interest_drop_ratio=_max_row_decimal(
            rows,
            "open_interest_drop_ratio",
        ),
        max_abs_price_move_ratio=_max_row_decimal(rows, "abs_price_move_ratio"),
        max_liquidation_to_volume_ratio=_max_row_decimal(
            rows,
            "liquidation_to_volume_ratio",
        ),
        digest_status=_digest_status(rows),
        recommended_next_step=_recommended_next_step(_digest_status(rows)),
        rows=rows,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
        reason_codes=reason_codes,
    )


def market_research_crypto_perp_open_interest_flush_digest_payload(
    report: CryptoPerpOpenInterestFlushDigestReport,
) -> dict[str, Any]:
    _require_exact_type(report, CryptoPerpOpenInterestFlushDigestReport, "report")
    return _payload_value(report)


def _row_from_observation(
    observation: CryptoPerpOpenInterestFlushObservation,
    *,
    config: MarketResearchCryptoPerpOpenInterestFlushDigestConfig,
    generated_at: datetime,
) -> CryptoPerpOpenInterestFlushDigestRow:
    open_interest_change_ratio = _ratio(
        observation.current_open_interest_usd - observation.previous_open_interest_usd,
        observation.previous_open_interest_usd,
    )
    open_interest_drop_ratio = _quantize_decimal(max(ZERO, -open_interest_change_ratio))
    mark_price_change_ratio = _ratio(
        observation.current_mark_price - observation.previous_mark_price,
        observation.previous_mark_price,
    )
    abs_price_move_ratio = _quantize_decimal(abs(mark_price_change_ratio))
    liquidation_to_volume_ratio = _ratio(
        observation.long_liquidations_usd + observation.short_liquidations_usd,
        observation.volume_24h_usd,
    )
    source_age_seconds = _seconds_between(generated_at, observation.observed_at)
    reason_codes = _row_reason_codes(
        open_interest_drop_ratio=open_interest_drop_ratio,
        abs_price_move_ratio=abs_price_move_ratio,
        liquidation_to_volume_ratio=liquidation_to_volume_ratio,
        funding_rate_8h=observation.funding_rate_8h,
        source_age_seconds=source_age_seconds,
        config=config,
    )
    flush_status = _row_flush_status(reason_codes)
    return CryptoPerpOpenInterestFlushDigestRow(
        source_id=observation.source_id,
        market_slug=observation.market_slug,
        base_asset=observation.base_asset,
        venue_id=observation.venue_id,
        current_open_interest_usd=observation.current_open_interest_usd,
        previous_open_interest_usd=observation.previous_open_interest_usd,
        open_interest_change_ratio=open_interest_change_ratio,
        open_interest_drop_ratio=open_interest_drop_ratio,
        current_mark_price=observation.current_mark_price,
        previous_mark_price=observation.previous_mark_price,
        mark_price_change_ratio=mark_price_change_ratio,
        abs_price_move_ratio=abs_price_move_ratio,
        funding_rate_8h=observation.funding_rate_8h,
        long_liquidations_usd=observation.long_liquidations_usd,
        short_liquidations_usd=observation.short_liquidations_usd,
        volume_24h_usd=observation.volume_24h_usd,
        liquidation_to_volume_ratio=liquidation_to_volume_ratio,
        dominant_liquidation_side=_dominant_liquidation_side(
            observation.long_liquidations_usd,
            observation.short_liquidations_usd,
        ),
        source_age_seconds=source_age_seconds,
        observed_at=observation.observed_at,
        flush_status=flush_status,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    open_interest_drop_ratio: Decimal,
    abs_price_move_ratio: Decimal,
    liquidation_to_volume_ratio: Decimal,
    funding_rate_8h: Decimal,
    source_age_seconds: Decimal,
    config: MarketResearchCryptoPerpOpenInterestFlushDigestConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if open_interest_drop_ratio >= config.high_open_interest_drop_ratio:
        reason_codes.append("open_interest_drop_high")
    elif open_interest_drop_ratio >= config.watch_open_interest_drop_ratio:
        reason_codes.append("open_interest_drop_watch")
    if (
        open_interest_drop_ratio >= config.watch_open_interest_drop_ratio
        and abs_price_move_ratio >= config.min_abs_price_move_ratio
    ):
        reason_codes.append("price_move_confirms_flush")
    if liquidation_to_volume_ratio >= config.high_liquidation_to_volume_ratio:
        reason_codes.append("liquidation_pressure_high")
    if abs(funding_rate_8h) >= config.high_abs_funding_rate_8h:
        reason_codes.append("funding_extreme")
    if source_age_seconds > config.stale_source_after_seconds:
        reason_codes.append("source_stale")
    if not reason_codes:
        reason_codes.append("open_interest_flush_clear")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), ROW_REASON_CODES)


def _row_flush_status(reason_codes: tuple[str, ...]) -> str:
    if "open_interest_drop_high" in reason_codes and (
        "price_move_confirms_flush" in reason_codes
        or "liquidation_pressure_high" in reason_codes
        or "funding_extreme" in reason_codes
    ):
        return "high_risk"
    if "open_interest_drop_high" in reason_codes and "source_stale" not in reason_codes:
        return "high_risk"
    if reason_codes == ("open_interest_flush_clear",):
        return "clear"
    return "watch"


def _report_reason_codes(
    rows: tuple[CryptoPerpOpenInterestFlushDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("crypto_perp_open_interest_flush_digest_empty",)
    reason_codes: list[str] = []
    if any(row.flush_status == "high_risk" for row in rows):
        reason_codes.append("crypto_perp_open_interest_flush_high_risk_present")
    if any(row.flush_status == "watch" for row in rows):
        reason_codes.append("crypto_perp_open_interest_flush_watch_present")
    if any("source_stale" in row.reason_codes for row in rows):
        reason_codes.append("crypto_perp_open_interest_flush_stale_source_present")
    if all(row.flush_status == "clear" for row in rows):
        reason_codes.append("crypto_perp_open_interest_flush_clear")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), REPORT_REASON_CODES)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[CryptoPerpOpenInterestFlushDigestRow, ...],
) -> tuple[CryptoPerpOpenInterestFlushReasonCodeCount, ...]:
    if reason_codes == ("crypto_perp_open_interest_flush_digest_empty",):
        return (
            CryptoPerpOpenInterestFlushReasonCodeCount(
                reason_code="crypto_perp_open_interest_flush_digest_empty",
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    row_count = _count_decimal(len(rows))
    return tuple(
        CryptoPerpOpenInterestFlushReasonCodeCount(
            reason_code=reason_code,
            count=_report_reason_count(reason_code, rows),
            row_ratio=_ratio(_report_reason_count(reason_code, rows), row_count),
        )
        for reason_code in reason_codes
    )


def _report_reason_count(
    reason_code: str,
    rows: tuple[CryptoPerpOpenInterestFlushDigestRow, ...],
) -> Decimal:
    if reason_code == "crypto_perp_open_interest_flush_high_risk_present":
        return _status_count(rows, "high_risk")
    if reason_code == "crypto_perp_open_interest_flush_watch_present":
        return _status_count(rows, "watch")
    if reason_code == "crypto_perp_open_interest_flush_stale_source_present":
        return _row_reason_count(rows, "source_stale")
    if reason_code == "crypto_perp_open_interest_flush_clear":
        return _status_count(rows, "clear")
    if reason_code == "crypto_perp_open_interest_flush_digest_empty":
        return ONE
    raise ValueError("reason_code must be supported")


def _digest_status(rows: tuple[CryptoPerpOpenInterestFlushDigestRow, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.flush_status == "high_risk" for row in rows):
        return "high_risk"
    if any(row.flush_status == "watch" for row in rows):
        return "watch"
    return "clear"


def _recommended_next_step(status: str) -> str:
    if status == "clear":
        return "allow_report_only_crypto_perp_open_interest_flush_digest"
    if status == "watch":
        return "monitor_report_only_crypto_perp_open_interest_flush_digest"
    return "block_report_only_crypto_perp_open_interest_flush_digest"


def _validate_row_consistency(row: CryptoPerpOpenInterestFlushDigestRow) -> None:
    expected_change = _ratio(
        row.current_open_interest_usd - row.previous_open_interest_usd,
        row.previous_open_interest_usd,
    )
    if row.open_interest_change_ratio != expected_change:
        raise ValueError("open_interest_change_ratio must match open interest values")
    if row.open_interest_drop_ratio != _quantize_decimal(max(ZERO, -expected_change)):
        raise ValueError("open_interest_drop_ratio must match open interest values")
    expected_price_change = _ratio(
        row.current_mark_price - row.previous_mark_price,
        row.previous_mark_price,
    )
    if row.mark_price_change_ratio != expected_price_change:
        raise ValueError("mark_price_change_ratio must match mark prices")
    if row.abs_price_move_ratio != _quantize_decimal(abs(row.mark_price_change_ratio)):
        raise ValueError("abs_price_move_ratio must match mark_price_change_ratio")
    expected_liquidation_ratio = _ratio(
        row.long_liquidations_usd + row.short_liquidations_usd,
        row.volume_24h_usd,
    )
    if row.liquidation_to_volume_ratio != expected_liquidation_ratio:
        raise ValueError("liquidation_to_volume_ratio must match liquidation values")
    if row.dominant_liquidation_side != _dominant_liquidation_side(
        row.long_liquidations_usd,
        row.short_liquidations_usd,
    ):
        raise ValueError("dominant_liquidation_side must match liquidation values")
    if row.flush_status != _row_flush_status(row.reason_codes):
        raise ValueError("reason_codes must match row metrics")
    if row.flush_status == "clear" and row.reason_codes != ("open_interest_flush_clear",):
        raise ValueError("reason_codes must match row metrics")
    if row.flush_status != "clear" and "open_interest_flush_clear" in row.reason_codes:
        raise ValueError("reason_codes must match row metrics")


def _validate_report_consistency(report: CryptoPerpOpenInterestFlushDigestReport) -> None:
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.input_count != report.row_count:
        raise ValueError("input_count must match rows")
    if report.high_risk_count != _status_count(report.rows, "high_risk"):
        raise ValueError("high_risk_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.clear_count != _status_count(report.rows, "clear"):
        raise ValueError("clear_count must match rows")
    if report.high_risk_count + report.watch_count + report.clear_count != report.row_count:
        raise ValueError("status counts must match row_count")
    if report.stale_source_count != _row_reason_count(report.rows, "source_stale"):
        raise ValueError("stale_source_count must match rows")
    if report.max_open_interest_drop_ratio != _max_row_decimal(
        report.rows,
        "open_interest_drop_ratio",
    ):
        raise ValueError("max_open_interest_drop_ratio must match rows")
    if report.max_abs_price_move_ratio != _max_row_decimal(
        report.rows,
        "abs_price_move_ratio",
    ):
        raise ValueError("max_abs_price_move_ratio must match rows")
    if report.max_liquidation_to_volume_ratio != _max_row_decimal(
        report.rows,
        "liquidation_to_volume_ratio",
    ):
        raise ValueError("max_liquidation_to_volume_ratio must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step must match digest_status")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, report.rows):
        raise ValueError("reason_code_counts must match reason_codes")


def _normalize_observations(
    observations: Iterable[CryptoPerpOpenInterestFlushObservation],
) -> tuple[CryptoPerpOpenInterestFlushObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must be an iterable")
    normalized = tuple(observations)
    seen: set[str] = set()
    for observation in normalized:
        if type(observation) is not CryptoPerpOpenInterestFlushObservation:
            raise ValueError(
                "observations must contain CryptoPerpOpenInterestFlushObservation",
            )
        _require_hard_flags(observation)
        if observation.source_id in seen:
            raise ValueError("observations must not contain duplicate source_id values")
        seen.add(observation.source_id)
    return normalized


def _normalize_rows(
    rows: Iterable[CryptoPerpOpenInterestFlushDigestRow],
) -> tuple[CryptoPerpOpenInterestFlushDigestRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not CryptoPerpOpenInterestFlushDigestRow:
            raise ValueError("rows must contain CryptoPerpOpenInterestFlushDigestRow")
        _require_hard_flags(row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    if len({row.source_id for row in normalized}) != len(normalized):
        raise ValueError("rows must not contain duplicate source_id values")
    return normalized


def _normalize_reason_code_counts(
    counts: Iterable[CryptoPerpOpenInterestFlushReasonCodeCount],
) -> tuple[CryptoPerpOpenInterestFlushReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)) or not isinstance(counts, Iterable):
        raise ValueError("reason_code_counts must be an iterable")
    normalized = tuple(counts)
    for count in normalized:
        if type(count) is not CryptoPerpOpenInterestFlushReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain"
                " CryptoPerpOpenInterestFlushReasonCodeCount",
            )
        _require_hard_flags(count)
    if normalized != tuple(sorted(normalized, key=_reason_code_count_sort_key)):
        raise ValueError("reason_code_counts must be sorted deterministically")
    return normalized


def _normalize_reason_codes(
    field_name: str,
    reason_codes: Iterable[str],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Iterable):
        raise ValueError(f"{field_name} must be an iterable")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_member("reason_code", reason_code, allowed)
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(sorted(normalized, key=allowed.index))


def _row_sort_key(row: CryptoPerpOpenInterestFlushDigestRow) -> tuple[Decimal, Decimal, str, str]:
    return (
        ROW_STATUS_RANK[row.flush_status],
        -row.open_interest_drop_ratio,
        row.market_slug,
        row.source_id,
    )


def _reason_code_count_sort_key(
    count: CryptoPerpOpenInterestFlushReasonCodeCount,
) -> Decimal:
    return _count_decimal(REPORT_REASON_CODES.index(count.reason_code))


def _dominant_liquidation_side(long_value: Decimal, short_value: Decimal) -> str:
    if long_value > short_value:
        return "long"
    if short_value > long_value:
        return "short"
    return "balanced"


def _status_count(
    rows: tuple[CryptoPerpOpenInterestFlushDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.flush_status == status))


def _row_reason_count(
    rows: tuple[CryptoPerpOpenInterestFlushDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_row_decimal(
    rows: tuple[CryptoPerpOpenInterestFlushDigestRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    if delta.days < 0:
        raise ValueError("observed_at must not be after generated_at")
    whole_seconds = Decimal(delta.days * 86400 + delta.seconds)
    fractional_seconds = Decimal(delta.microseconds) / Decimal("1000000")
    return _quantize_decimal(whole_seconds + fractional_seconds)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(numerator / denominator)


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_positive_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_probability(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
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


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must be supported")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value or _CANONICAL_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_exact_type(value: object, type_: type[object], label: str) -> None:
    if type(value) is not type_:
        raise ValueError(f"{label} must be exactly {type_.__name__}")


def _payload_value(value: object) -> Any:
    if isinstance(value, Decimal):
        return f"{value:.6f}"
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    return value
