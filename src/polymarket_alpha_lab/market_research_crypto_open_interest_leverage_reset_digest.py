"""Pure Phase 1 crypto open-interest leverage reset digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import re
from typing import Any


DEFAULT_MARKET_RESEARCH_CRYPTO_OPEN_INTEREST_LEVERAGE_RESET_DIGEST_CONFIG_VERSION = (
    "market-research-crypto-open-interest-leverage-reset-digest-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

ROW_STATUSES = ("blocked", "watch", "pass")
REPORT_STATUSES = ("blocked", "watch", "pass")
LIQUIDATION_SIDES = ("balanced", "long", "short")
ROW_REASON_CODES = (
    "open_interest_drop_blocked",
    "open_interest_drop_watch",
    "leverage_drop_blocked",
    "leverage_drop_watch",
    "liquidation_confirms_reset",
    "funding_extreme",
    "source_stale",
    "open_interest_leverage_reset_inline",
)
REPORT_REASON_CODES = (
    "crypto_open_interest_leverage_reset_blocked_present",
    "crypto_open_interest_leverage_reset_watch_present",
    "crypto_open_interest_leverage_reset_stale_source_present",
    "crypto_open_interest_leverage_reset_clear",
    "crypto_open_interest_leverage_reset_digest_empty",
)
ROW_STATUS_RANK = {
    "blocked": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}
_CANONICAL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")


__all__ = (
    "DEFAULT_MARKET_RESEARCH_CRYPTO_OPEN_INTEREST_LEVERAGE_RESET_DIGEST_CONFIG_VERSION",
    "MarketResearchCryptoOpenInterestLeverageResetDigestConfig",
    "CryptoOpenInterestLeverageResetObservation",
    "CryptoOpenInterestLeverageResetDigestRow",
    "CryptoOpenInterestLeverageResetReasonCodeCount",
    "CryptoOpenInterestLeverageResetDigestReport",
    "build_market_research_crypto_open_interest_leverage_reset_digest",
    "market_research_crypto_open_interest_leverage_reset_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchCryptoOpenInterestLeverageResetDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_CRYPTO_OPEN_INTEREST_LEVERAGE_RESET_DIGEST_CONFIG_VERSION
    )
    watch_open_interest_drop_ratio: Decimal = Decimal("0.050000")
    blocked_open_interest_drop_ratio: Decimal = Decimal("0.120000")
    watch_leverage_drop_ratio: Decimal = Decimal("0.100000")
    blocked_leverage_drop_ratio: Decimal = Decimal("0.200000")
    min_liquidation_to_volume_ratio: Decimal = Decimal("0.040000")
    high_abs_funding_rate_8h: Decimal = Decimal("0.000800")
    stale_source_after_seconds: Decimal = Decimal("900.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoOpenInterestLeverageResetDigestConfig:
            raise TypeError(
                "MarketResearchCryptoOpenInterestLeverageResetDigestConfig"
                " does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchCryptoOpenInterestLeverageResetDigestConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_CRYPTO_OPEN_INTEREST_LEVERAGE_RESET_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_open_interest_drop_ratio",
            "blocked_open_interest_drop_ratio",
            "watch_leverage_drop_ratio",
            "blocked_leverage_drop_ratio",
            "min_liquidation_to_volume_ratio",
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
        if self.blocked_open_interest_drop_ratio < self.watch_open_interest_drop_ratio:
            raise ValueError(
                "blocked_open_interest_drop_ratio must be at least"
                " watch_open_interest_drop_ratio",
            )
        if self.blocked_leverage_drop_ratio < self.watch_leverage_drop_ratio:
            raise ValueError(
                "blocked_leverage_drop_ratio must be at least"
                " watch_leverage_drop_ratio",
            )
        _require_hard_flags(self)


@dataclass(frozen=True)
class CryptoOpenInterestLeverageResetObservation:
    source_id: str
    event_key: str
    base_asset: str
    venue_id: str
    current_open_interest_usd: Decimal
    previous_open_interest_usd: Decimal
    current_estimated_leverage_ratio: Decimal
    previous_estimated_leverage_ratio: Decimal
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
        if cls is not CryptoOpenInterestLeverageResetObservation:
            raise TypeError(
                "CryptoOpenInterestLeverageResetObservation does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, CryptoOpenInterestLeverageResetObservation, "observation")
        for field_name in ("source_id", "event_key", "base_asset", "venue_id"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "current_open_interest_usd",
            "current_estimated_leverage_ratio",
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
            "previous_estimated_leverage_ratio",
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
class CryptoOpenInterestLeverageResetDigestRow:
    source_id: str
    event_key: str
    base_asset: str
    venue_id: str
    current_open_interest_usd: Decimal
    previous_open_interest_usd: Decimal
    open_interest_change_ratio: Decimal
    open_interest_drop_ratio: Decimal
    current_estimated_leverage_ratio: Decimal
    previous_estimated_leverage_ratio: Decimal
    leverage_change_ratio: Decimal
    leverage_drop_ratio: Decimal
    funding_rate_8h: Decimal
    long_liquidations_usd: Decimal
    short_liquidations_usd: Decimal
    volume_24h_usd: Decimal
    liquidation_to_volume_ratio: Decimal
    dominant_liquidation_side: str
    source_age_seconds: Decimal
    observed_at: datetime
    reset_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CryptoOpenInterestLeverageResetDigestRow:
            raise TypeError(
                "CryptoOpenInterestLeverageResetDigestRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, CryptoOpenInterestLeverageResetDigestRow, "row")
        for field_name in ("source_id", "event_key", "base_asset", "venue_id"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "current_open_interest_usd",
            "current_estimated_leverage_ratio",
            "long_liquidations_usd",
            "short_liquidations_usd",
            "volume_24h_usd",
            "open_interest_drop_ratio",
            "leverage_drop_ratio",
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
            "previous_estimated_leverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "open_interest_change_ratio",
            "leverage_change_ratio",
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
        _require_member("reset_status", self.reset_status, ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row_consistency(self)
        _require_hard_flags(self)


@dataclass(frozen=True)
class CryptoOpenInterestLeverageResetReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CryptoOpenInterestLeverageResetReasonCodeCount:
            raise TypeError(
                "CryptoOpenInterestLeverageResetReasonCodeCount"
                " does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, CryptoOpenInterestLeverageResetReasonCodeCount, "count")
        _require_member("reason_code", self.reason_code, REPORT_REASON_CODES)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_decimal("count", self.count),
        )
        if self.count == ZERO:
            raise ValueError("count must be positive")
        object.__setattr__(
            self,
            "row_ratio",
            _normalize_probability("row_ratio", self.row_ratio),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class CryptoOpenInterestLeverageResetDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    stale_source_count: Decimal
    max_open_interest_drop_ratio: Decimal
    max_leverage_drop_ratio: Decimal
    max_liquidation_to_volume_ratio: Decimal
    digest_status: str
    recommended_next_step: str
    rows: tuple[CryptoOpenInterestLeverageResetDigestRow, ...]
    reason_code_counts: tuple[CryptoOpenInterestLeverageResetReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CryptoOpenInterestLeverageResetDigestReport:
            raise TypeError(
                "CryptoOpenInterestLeverageResetDigestReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, CryptoOpenInterestLeverageResetDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_CRYPTO_OPEN_INTEREST_LEVERAGE_RESET_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "blocked_count",
            "watch_count",
            "pass_count",
            "stale_source_count",
            "max_open_interest_drop_ratio",
            "max_leverage_drop_ratio",
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


def build_market_research_crypto_open_interest_leverage_reset_digest(
    observations: Iterable[CryptoOpenInterestLeverageResetObservation],
    *,
    config: MarketResearchCryptoOpenInterestLeverageResetDigestConfig,
    generated_at: datetime,
) -> CryptoOpenInterestLeverageResetDigestReport:
    _require_exact_type(
        config,
        MarketResearchCryptoOpenInterestLeverageResetDigestConfig,
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
    status = _digest_status(rows)
    return CryptoOpenInterestLeverageResetDigestReport(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized)),
        row_count=_count_decimal(len(rows)),
        blocked_count=_status_count(rows, "blocked"),
        watch_count=_status_count(rows, "watch"),
        pass_count=_status_count(rows, "pass"),
        stale_source_count=_row_reason_count(rows, "source_stale"),
        max_open_interest_drop_ratio=_max_row_decimal(
            rows,
            "open_interest_drop_ratio",
        ),
        max_leverage_drop_ratio=_max_row_decimal(rows, "leverage_drop_ratio"),
        max_liquidation_to_volume_ratio=_max_row_decimal(
            rows,
            "liquidation_to_volume_ratio",
        ),
        digest_status=status,
        recommended_next_step=_recommended_next_step(status),
        rows=rows,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
        reason_codes=reason_codes,
    )


def market_research_crypto_open_interest_leverage_reset_digest_payload(
    report: CryptoOpenInterestLeverageResetDigestReport,
) -> dict[str, Any]:
    _require_exact_type(report, CryptoOpenInterestLeverageResetDigestReport, "report")
    _revalidate_public_dataclass(report)
    return _payload_value(report)


def _row_from_observation(
    observation: CryptoOpenInterestLeverageResetObservation,
    *,
    config: MarketResearchCryptoOpenInterestLeverageResetDigestConfig,
    generated_at: datetime,
) -> CryptoOpenInterestLeverageResetDigestRow:
    open_interest_change_ratio = _ratio(
        observation.current_open_interest_usd - observation.previous_open_interest_usd,
        observation.previous_open_interest_usd,
    )
    open_interest_drop_ratio = _quantize_decimal(max(ZERO, -open_interest_change_ratio))
    leverage_change_ratio = _ratio(
        observation.current_estimated_leverage_ratio
        - observation.previous_estimated_leverage_ratio,
        observation.previous_estimated_leverage_ratio,
    )
    leverage_drop_ratio = _quantize_decimal(max(ZERO, -leverage_change_ratio))
    liquidation_to_volume_ratio = _ratio(
        observation.long_liquidations_usd + observation.short_liquidations_usd,
        observation.volume_24h_usd,
    )
    source_age_seconds = _seconds_between(generated_at, observation.observed_at)
    reason_codes = _row_reason_codes(
        open_interest_drop_ratio=open_interest_drop_ratio,
        leverage_drop_ratio=leverage_drop_ratio,
        liquidation_to_volume_ratio=liquidation_to_volume_ratio,
        funding_rate_8h=observation.funding_rate_8h,
        source_age_seconds=source_age_seconds,
        config=config,
    )
    reset_status = _row_reset_status(reason_codes)
    return CryptoOpenInterestLeverageResetDigestRow(
        source_id=observation.source_id,
        event_key=observation.event_key,
        base_asset=observation.base_asset,
        venue_id=observation.venue_id,
        current_open_interest_usd=observation.current_open_interest_usd,
        previous_open_interest_usd=observation.previous_open_interest_usd,
        open_interest_change_ratio=open_interest_change_ratio,
        open_interest_drop_ratio=open_interest_drop_ratio,
        current_estimated_leverage_ratio=observation.current_estimated_leverage_ratio,
        previous_estimated_leverage_ratio=observation.previous_estimated_leverage_ratio,
        leverage_change_ratio=leverage_change_ratio,
        leverage_drop_ratio=leverage_drop_ratio,
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
        reset_status=reset_status,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    open_interest_drop_ratio: Decimal,
    leverage_drop_ratio: Decimal,
    liquidation_to_volume_ratio: Decimal,
    funding_rate_8h: Decimal,
    source_age_seconds: Decimal,
    config: MarketResearchCryptoOpenInterestLeverageResetDigestConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if open_interest_drop_ratio >= config.blocked_open_interest_drop_ratio:
        reason_codes.append("open_interest_drop_blocked")
    elif open_interest_drop_ratio >= config.watch_open_interest_drop_ratio:
        reason_codes.append("open_interest_drop_watch")
    if leverage_drop_ratio >= config.blocked_leverage_drop_ratio:
        reason_codes.append("leverage_drop_blocked")
    elif leverage_drop_ratio >= config.watch_leverage_drop_ratio:
        reason_codes.append("leverage_drop_watch")
    if (
        liquidation_to_volume_ratio >= config.min_liquidation_to_volume_ratio
        and (
            open_interest_drop_ratio >= config.watch_open_interest_drop_ratio
            or leverage_drop_ratio >= config.watch_leverage_drop_ratio
        )
    ):
        reason_codes.append("liquidation_confirms_reset")
    if abs(funding_rate_8h) >= config.high_abs_funding_rate_8h:
        reason_codes.append("funding_extreme")
    if source_age_seconds > config.stale_source_after_seconds:
        reason_codes.append("source_stale")
    if not reason_codes:
        reason_codes.append("open_interest_leverage_reset_inline")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), ROW_REASON_CODES)


def _row_reset_status(reason_codes: tuple[str, ...]) -> str:
    if (
        "open_interest_drop_blocked" in reason_codes
        or "leverage_drop_blocked" in reason_codes
    ):
        return "blocked"
    if reason_codes == ("open_interest_leverage_reset_inline",):
        return "pass"
    return "watch"


def _report_reason_codes(
    rows: tuple[CryptoOpenInterestLeverageResetDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("crypto_open_interest_leverage_reset_digest_empty",)
    reason_codes: list[str] = []
    if any(row.reset_status == "blocked" for row in rows):
        reason_codes.append("crypto_open_interest_leverage_reset_blocked_present")
    if any(row.reset_status == "watch" for row in rows):
        reason_codes.append("crypto_open_interest_leverage_reset_watch_present")
    if any("source_stale" in row.reason_codes for row in rows):
        reason_codes.append("crypto_open_interest_leverage_reset_stale_source_present")
    if all(row.reset_status == "pass" for row in rows):
        reason_codes.append("crypto_open_interest_leverage_reset_clear")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), REPORT_REASON_CODES)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[CryptoOpenInterestLeverageResetDigestRow, ...],
) -> tuple[CryptoOpenInterestLeverageResetReasonCodeCount, ...]:
    if reason_codes == ("crypto_open_interest_leverage_reset_digest_empty",):
        return (
            CryptoOpenInterestLeverageResetReasonCodeCount(
                reason_code="crypto_open_interest_leverage_reset_digest_empty",
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    row_count = _count_decimal(len(rows))
    return tuple(
        CryptoOpenInterestLeverageResetReasonCodeCount(
            reason_code=reason_code,
            count=_report_reason_count(reason_code, rows),
            row_ratio=_ratio(_report_reason_count(reason_code, rows), row_count),
        )
        for reason_code in reason_codes
    )


def _report_reason_count(
    reason_code: str,
    rows: tuple[CryptoOpenInterestLeverageResetDigestRow, ...],
) -> Decimal:
    if reason_code == "crypto_open_interest_leverage_reset_blocked_present":
        return _status_count(rows, "blocked")
    if reason_code == "crypto_open_interest_leverage_reset_watch_present":
        return _status_count(rows, "watch")
    if reason_code == "crypto_open_interest_leverage_reset_stale_source_present":
        return _row_reason_count(rows, "source_stale")
    if reason_code == "crypto_open_interest_leverage_reset_clear":
        return _status_count(rows, "pass")
    if reason_code == "crypto_open_interest_leverage_reset_digest_empty":
        return ONE
    raise ValueError("reason_code must be supported")


def _digest_status(rows: tuple[CryptoOpenInterestLeverageResetDigestRow, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.reset_status == "blocked" for row in rows):
        return "blocked"
    if any(row.reset_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _recommended_next_step(status: str) -> str:
    if status == "pass":
        return "allow_report_only_crypto_open_interest_leverage_reset_digest"
    if status == "watch":
        return "monitor_report_only_crypto_open_interest_leverage_reset_digest"
    return "block_report_only_crypto_open_interest_leverage_reset_digest"


def _validate_row_consistency(row: CryptoOpenInterestLeverageResetDigestRow) -> None:
    expected_open_interest_change = _ratio(
        row.current_open_interest_usd - row.previous_open_interest_usd,
        row.previous_open_interest_usd,
    )
    if row.open_interest_change_ratio != expected_open_interest_change:
        raise ValueError("open_interest_change_ratio must match open interest values")
    if row.open_interest_drop_ratio != _quantize_decimal(
        max(ZERO, -expected_open_interest_change),
    ):
        raise ValueError("open_interest_drop_ratio must match open interest values")
    expected_leverage_change = _ratio(
        row.current_estimated_leverage_ratio - row.previous_estimated_leverage_ratio,
        row.previous_estimated_leverage_ratio,
    )
    if row.leverage_change_ratio != expected_leverage_change:
        raise ValueError("leverage_change_ratio must match leverage values")
    if row.leverage_drop_ratio != _quantize_decimal(max(ZERO, -expected_leverage_change)):
        raise ValueError("leverage_drop_ratio must match leverage values")
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
    if row.reset_status != _row_reset_status(row.reason_codes):
        raise ValueError("reset_status must match row metrics")
    if (
        row.reset_status == "pass"
        and row.reason_codes != ("open_interest_leverage_reset_inline",)
    ):
        raise ValueError("reason_codes must match row metrics")
    if (
        row.reset_status != "pass"
        and "open_interest_leverage_reset_inline" in row.reason_codes
    ):
        raise ValueError("reason_codes must match row metrics")


def _validate_report_consistency(report: CryptoOpenInterestLeverageResetDigestReport) -> None:
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.input_count != report.row_count:
        raise ValueError("input_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.blocked_count + report.watch_count + report.pass_count != report.row_count:
        raise ValueError("status counts must match row_count")
    if report.stale_source_count != _row_reason_count(report.rows, "source_stale"):
        raise ValueError("stale_source_count must match rows")
    if report.max_open_interest_drop_ratio != _max_row_decimal(
        report.rows,
        "open_interest_drop_ratio",
    ):
        raise ValueError("max_open_interest_drop_ratio must match rows")
    if report.max_leverage_drop_ratio != _max_row_decimal(
        report.rows,
        "leverage_drop_ratio",
    ):
        raise ValueError("max_leverage_drop_ratio must match rows")
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
    observations: Iterable[CryptoOpenInterestLeverageResetObservation],
) -> tuple[CryptoOpenInterestLeverageResetObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must be an iterable")
    normalized = tuple(observations)
    seen: set[str] = set()
    for observation in normalized:
        if type(observation) is not CryptoOpenInterestLeverageResetObservation:
            raise ValueError(
                "observations must contain CryptoOpenInterestLeverageResetObservation",
            )
        _require_hard_flags(observation)
        if observation.source_id in seen:
            raise ValueError("observations must not contain duplicate source_id values")
        seen.add(observation.source_id)
    return normalized


def _normalize_rows(
    rows: tuple[CryptoOpenInterestLeverageResetDigestRow, ...],
) -> tuple[CryptoOpenInterestLeverageResetDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a canonical tuple")
    for row in rows:
        if type(row) is not CryptoOpenInterestLeverageResetDigestRow:
            raise ValueError("rows must contain CryptoOpenInterestLeverageResetDigestRow")
        _require_hard_flags(row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    if len({row.source_id for row in rows}) != len(rows):
        raise ValueError("rows must not contain duplicate source_id values")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[CryptoOpenInterestLeverageResetReasonCodeCount, ...],
) -> tuple[CryptoOpenInterestLeverageResetReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a canonical tuple")
    for count in counts:
        if type(count) is not CryptoOpenInterestLeverageResetReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain"
                " CryptoOpenInterestLeverageResetReasonCodeCount",
            )
        _require_hard_flags(count)
    if counts != tuple(sorted(counts, key=_reason_code_count_sort_key)):
        raise ValueError("reason_code_counts must be sorted deterministically")
    return counts


def _normalize_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError(f"{field_name} must be a canonical tuple")
    for reason_code in reason_codes:
        _require_member("reason_code", reason_code, allowed)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be canonical without duplicates")
    if reason_codes != tuple(sorted(reason_codes, key=allowed.index)):
        raise ValueError(f"{field_name} must be canonical")
    return reason_codes


def _row_sort_key(
    row: CryptoOpenInterestLeverageResetDigestRow,
) -> tuple[Decimal, Decimal, Decimal, str, str]:
    return (
        ROW_STATUS_RANK[row.reset_status],
        -row.open_interest_drop_ratio,
        -row.leverage_drop_ratio,
        row.event_key,
        row.source_id,
    )


def _reason_code_count_sort_key(
    count: CryptoOpenInterestLeverageResetReasonCodeCount,
) -> Decimal:
    return _count_decimal(REPORT_REASON_CODES.index(count.reason_code))


def _dominant_liquidation_side(long_value: Decimal, short_value: Decimal) -> str:
    if long_value > short_value:
        return "long"
    if short_value > long_value:
        return "short"
    return "balanced"


def _status_count(
    rows: tuple[CryptoOpenInterestLeverageResetDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.reset_status == status))


def _row_reason_count(
    rows: tuple[CryptoOpenInterestLeverageResetDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_row_decimal(
    rows: tuple[CryptoOpenInterestLeverageResetDigestRow, ...],
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
    decimal_value = _quantize_decimal(value)
    if decimal_value != value or not value.same_quantum(QUANTUM):
        raise ValueError(f"{field_name} must be six-decimal")
    return value


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    return value.astimezone(UTC)


def _require_payload_utc(field_name: str, value: object) -> None:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is not UTC or value.utcoffset() != ZERO_TIME_OFFSET:
        raise ValueError(f"{field_name} must be UTC for payload serialization")


ZERO_TIME_OFFSET = UTC.utcoffset(None)


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


def _revalidate_public_dataclass(value: object) -> None:
    if type(value) is MarketResearchCryptoOpenInterestLeverageResetDigestConfig:
        MarketResearchCryptoOpenInterestLeverageResetDigestConfig(
            **_public_dataclass_values(value),
        )
        return
    if type(value) is CryptoOpenInterestLeverageResetObservation:
        _require_payload_utc("observed_at", value.observed_at)
        CryptoOpenInterestLeverageResetObservation(**_public_dataclass_values(value))
        return
    if type(value) is CryptoOpenInterestLeverageResetDigestRow:
        _require_payload_utc("observed_at", value.observed_at)
        CryptoOpenInterestLeverageResetDigestRow(**_public_dataclass_values(value))
        return
    if type(value) is CryptoOpenInterestLeverageResetReasonCodeCount:
        CryptoOpenInterestLeverageResetReasonCodeCount(**_public_dataclass_values(value))
        return
    if type(value) is CryptoOpenInterestLeverageResetDigestReport:
        _require_payload_utc("generated_at", value.generated_at)
        for row in value.rows:
            _revalidate_public_dataclass(row)
        for count in value.reason_code_counts:
            _revalidate_public_dataclass(count)
        CryptoOpenInterestLeverageResetDigestReport(**_public_dataclass_values(value))
        return
    raise ValueError("payload value must be a supported public dataclass")


def _public_dataclass_values(value: object) -> dict[str, object]:
    if not is_dataclass(value) or isinstance(value, type):
        raise ValueError("value must be a public dataclass")
    return {field.name: getattr(value, field.name) for field in fields(value)}


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        _normalize_decimal("payload decimal", value)
        return f"{value:.6f}"
    if isinstance(value, Decimal):
        raise ValueError("payload decimal must be an exact Decimal")
    if type(value) is datetime:
        _require_payload_utc("datetime", value)
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    return value
