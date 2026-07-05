"""Pure Phase 1 equity short-interest squeeze risk digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import re
from typing import Any


DEFAULT_MARKET_RESEARCH_EQUITY_SHORT_INTEREST_SQUEEZE_DIGEST_CONFIG_VERSION = (
    "market-research-equity-short-interest-squeeze-digest-v0"
)

SQUEEZE_STATUSES = ("pass", "watch", "blocked")
ROW_REASON_CODES = (
    "equity_short_interest_squeeze_extreme_short_interest",
    "equity_short_interest_squeeze_extreme_days_to_cover",
    "equity_short_interest_squeeze_extreme_borrow_fee",
    "equity_short_interest_squeeze_high_short_interest",
    "equity_short_interest_squeeze_high_days_to_cover",
    "equity_short_interest_squeeze_high_borrow_fee",
    "equity_short_interest_squeeze_price_rally",
    "equity_short_interest_squeeze_thin_sources",
    "equity_short_interest_squeeze_stale_observation",
    "equity_short_interest_squeeze_float_uncertainty",
    "equity_short_interest_squeeze_inline",
    "equity_short_interest_squeeze_blocked",
    "equity_short_interest_squeeze_watch",
)
REPORT_REASON_CODES = (
    "equity_short_interest_squeeze_blocked_present",
    "equity_short_interest_squeeze_crowded_short_present",
    "equity_short_interest_squeeze_days_to_cover_present",
    "equity_short_interest_squeeze_borrow_stress_present",
    "equity_short_interest_squeeze_price_rally_present",
    "equity_short_interest_squeeze_data_quality_present",
    "equity_short_interest_squeeze_digest_clear",
    "equity_short_interest_squeeze_digest_empty",
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
WATCH_RISK_SCORE = Decimal("0.500000")
DEFAULT_BLOCKED_SHORT_INTEREST_RATIO = Decimal("0.250000")
DEFAULT_BLOCKED_DAYS_TO_COVER = Decimal("7.000000")
DEFAULT_BLOCKED_BORROW_FEE_RATE = Decimal("0.500000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUS_RANK = {
    "blocked": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}
_CANONICAL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")


__all__ = (
    "DEFAULT_MARKET_RESEARCH_EQUITY_SHORT_INTEREST_SQUEEZE_DIGEST_CONFIG_VERSION",
    "MarketResearchEquityShortInterestSqueezeDigestConfig",
    "MarketResearchEquityShortInterestSqueezeDigestObservation",
    "MarketResearchEquityShortInterestSqueezeDigestRow",
    "MarketResearchEquityShortInterestSqueezeReasonCodeCount",
    "MarketResearchEquityShortInterestSqueezeDigestReport",
    "build_market_research_equity_short_interest_squeeze_digest",
    "market_research_equity_short_interest_squeeze_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchEquityShortInterestSqueezeDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_EQUITY_SHORT_INTEREST_SQUEEZE_DIGEST_CONFIG_VERSION
    )
    watch_short_interest_ratio: Decimal = Decimal("0.150000")
    blocked_short_interest_ratio: Decimal = DEFAULT_BLOCKED_SHORT_INTEREST_RATIO
    watch_days_to_cover: Decimal = Decimal("3.000000")
    blocked_days_to_cover: Decimal = DEFAULT_BLOCKED_DAYS_TO_COVER
    watch_borrow_fee_rate: Decimal = Decimal("0.200000")
    blocked_borrow_fee_rate: Decimal = DEFAULT_BLOCKED_BORROW_FEE_RATE
    rally_confirmation_pct: Decimal = Decimal("0.100000")
    min_source_count: Decimal = Decimal("2.000000")
    max_observation_age_seconds: Decimal = Decimal("86400.000000")
    max_float_uncertainty_ratio: Decimal = Decimal("0.050000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: Any) -> None:
        raise TypeError(
            "MarketResearchEquityShortInterestSqueezeDigestConfig "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchEquityShortInterestSqueezeDigestConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_EQUITY_SHORT_INTEREST_SQUEEZE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_short_interest_ratio",
            "blocked_short_interest_ratio",
            "watch_borrow_fee_rate",
            "blocked_borrow_fee_rate",
            "max_float_uncertainty_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_days_to_cover",
            "blocked_days_to_cover",
            "rally_confirmation_pct",
            "min_source_count",
            "max_observation_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_short_interest_ratio > self.blocked_short_interest_ratio:
            raise ValueError(
                "blocked_short_interest_ratio must be greater than or equal to "
                "watch_short_interest_ratio",
            )
        if self.watch_days_to_cover > self.blocked_days_to_cover:
            raise ValueError(
                "blocked_days_to_cover must be greater than or equal to "
                "watch_days_to_cover",
            )
        if self.watch_borrow_fee_rate > self.blocked_borrow_fee_rate:
            raise ValueError(
                "blocked_borrow_fee_rate must be greater than or equal to "
                "watch_borrow_fee_rate",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchEquityShortInterestSqueezeDigestObservation:
    source_id: str
    equity_symbol: str
    market_slug: str
    short_interest_ratio: Decimal
    days_to_cover: Decimal
    borrow_fee_rate: Decimal
    five_day_price_return_pct: Decimal
    float_uncertainty_ratio: Decimal
    source_count: Decimal
    data_timestamp: datetime
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: Any) -> None:
        raise TypeError(
            "MarketResearchEquityShortInterestSqueezeDigestObservation "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchEquityShortInterestSqueezeDigestObservation,
            "observation",
        )
        for field_name in ("source_id", "equity_symbol", "market_slug"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "short_interest_ratio",
            "borrow_fee_rate",
            "float_uncertainty_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "days_to_cover",
            _require_nonnegative_decimal("days_to_cover", self.days_to_cover),
        )
        object.__setattr__(
            self,
            "five_day_price_return_pct",
            _require_decimal(
                "five_day_price_return_pct",
                self.five_day_price_return_pct,
            ),
        )
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_decimal("source_count", self.source_count),
        )
        object.__setattr__(
            self,
            "data_timestamp",
            _as_utc("data_timestamp", self.data_timestamp),
        )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_upstream_reason_codes(
                "upstream_reason_codes",
                self.upstream_reason_codes,
            ),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class MarketResearchEquityShortInterestSqueezeDigestRow:
    source_id: str
    equity_symbol: str
    market_slug: str
    short_interest_ratio: Decimal
    short_interest_excess_ratio: Decimal
    days_to_cover: Decimal
    days_to_cover_excess: Decimal
    borrow_fee_rate: Decimal
    borrow_fee_excess_rate: Decimal
    five_day_price_return_pct: Decimal
    float_uncertainty_ratio: Decimal
    source_count: Decimal
    observation_age_seconds: Decimal
    data_timestamp: datetime
    squeeze_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: Any) -> None:
        raise TypeError(
            "MarketResearchEquityShortInterestSqueezeDigestRow "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchEquityShortInterestSqueezeDigestRow,
            "row",
        )
        for field_name in ("source_id", "equity_symbol", "market_slug"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "short_interest_ratio",
            "short_interest_excess_ratio",
            "borrow_fee_rate",
            "borrow_fee_excess_rate",
            "float_uncertainty_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "days_to_cover",
            "days_to_cover_excess",
            "source_count",
            "observation_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "five_day_price_return_pct",
            _require_decimal(
                "five_day_price_return_pct",
                self.five_day_price_return_pct,
            ),
        )
        object.__setattr__(
            self,
            "data_timestamp",
            _as_utc("data_timestamp", self.data_timestamp),
        )
        _require_member("squeeze_status", self.squeeze_status, SQUEEZE_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchEquityShortInterestSqueezeReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: Any) -> None:
        raise TypeError(
            "MarketResearchEquityShortInterestSqueezeReasonCodeCount "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchEquityShortInterestSqueezeReasonCodeCount,
            "reason code count",
        )
        _require_member("reason_code", self.reason_code, REPORT_REASON_CODES)
        object.__setattr__(self, "count", _require_positive_decimal("count", self.count))
        object.__setattr__(self, "row_ratio", _require_ratio("row_ratio", self.row_ratio))
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchEquityShortInterestSqueezeDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    high_short_interest_count: Decimal
    extreme_short_interest_count: Decimal
    high_days_to_cover_count: Decimal
    extreme_days_to_cover_count: Decimal
    high_borrow_fee_count: Decimal
    extreme_borrow_fee_count: Decimal
    rally_confirmation_count: Decimal
    thin_source_count: Decimal
    stale_observation_count: Decimal
    float_uncertainty_count: Decimal
    max_short_interest_ratio: Decimal
    average_short_interest_ratio: Decimal
    max_days_to_cover: Decimal
    average_days_to_cover: Decimal
    max_borrow_fee_rate: Decimal
    average_borrow_fee_rate: Decimal
    squeeze_risk_score: Decimal
    digest_status: str
    recommended_next_step: str
    rows: tuple[MarketResearchEquityShortInterestSqueezeDigestRow, ...]
    reason_code_counts: tuple[MarketResearchEquityShortInterestSqueezeReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: Any) -> None:
        raise TypeError(
            "MarketResearchEquityShortInterestSqueezeDigestReport "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchEquityShortInterestSqueezeDigestReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_EQUITY_SHORT_INTEREST_SQUEEZE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "blocked_count",
            "watch_count",
            "pass_count",
            "high_short_interest_count",
            "extreme_short_interest_count",
            "high_days_to_cover_count",
            "extreme_days_to_cover_count",
            "high_borrow_fee_count",
            "extreme_borrow_fee_count",
            "rally_confirmation_count",
            "thin_source_count",
            "stale_observation_count",
            "float_uncertainty_count",
            "max_short_interest_ratio",
            "average_short_interest_ratio",
            "max_days_to_cover",
            "average_days_to_cover",
            "max_borrow_fee_rate",
            "average_borrow_fee_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "squeeze_risk_score",
            _require_ratio("squeeze_risk_score", self.squeeze_risk_score),
        )
        _require_member("digest_status", self.digest_status, SQUEEZE_STATUSES)
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
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


_PUBLIC_DATACLASS_TYPES = (
    MarketResearchEquityShortInterestSqueezeDigestConfig,
    MarketResearchEquityShortInterestSqueezeDigestObservation,
    MarketResearchEquityShortInterestSqueezeDigestRow,
    MarketResearchEquityShortInterestSqueezeReasonCodeCount,
    MarketResearchEquityShortInterestSqueezeDigestReport,
)
_PUBLIC_DATACLASS_PAYLOAD_LABELS = {
    MarketResearchEquityShortInterestSqueezeDigestConfig: "config",
    MarketResearchEquityShortInterestSqueezeDigestObservation: "observation",
    MarketResearchEquityShortInterestSqueezeDigestRow: "row",
    MarketResearchEquityShortInterestSqueezeReasonCodeCount: "reason code count",
    MarketResearchEquityShortInterestSqueezeDigestReport: "report",
}


def build_market_research_equity_short_interest_squeeze_digest(
    observations: Iterable[MarketResearchEquityShortInterestSqueezeDigestObservation],
    *,
    config: MarketResearchEquityShortInterestSqueezeDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchEquityShortInterestSqueezeDigestReport:
    cfg = (
        MarketResearchEquityShortInterestSqueezeDigestConfig()
        if config is None
        else config
    )
    if type(cfg) is not MarketResearchEquityShortInterestSqueezeDigestConfig:
        raise ValueError(
            "config must be exactly "
            "MarketResearchEquityShortInterestSqueezeDigestConfig",
        )
    generated_at_utc = _as_utc("generated_at", generated_at)
    _require_hard_flags("config", cfg)
    normalized = _normalize_observations(observations)
    rows = tuple(
        sorted(
            (
                _row_from_observation(
                    observation,
                    config=cfg,
                    generated_at=generated_at_utc,
                )
                for observation in normalized
            ),
            key=_row_sort_key,
        ),
    )
    row_count = _count_decimal(len(rows))
    reason_codes = _report_reason_codes(rows)
    digest_status = _digest_status(rows)

    return MarketResearchEquityShortInterestSqueezeDigestReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        input_count=_count_decimal(len(normalized)),
        row_count=row_count,
        blocked_count=_status_count(rows, "blocked"),
        watch_count=_status_count(rows, "watch"),
        pass_count=_status_count(rows, "pass"),
        high_short_interest_count=_any_reason_count(
            rows,
            (
                "equity_short_interest_squeeze_high_short_interest",
                "equity_short_interest_squeeze_extreme_short_interest",
            ),
        ),
        extreme_short_interest_count=_reason_count(
            rows,
            "equity_short_interest_squeeze_extreme_short_interest",
        ),
        high_days_to_cover_count=_any_reason_count(
            rows,
            (
                "equity_short_interest_squeeze_high_days_to_cover",
                "equity_short_interest_squeeze_extreme_days_to_cover",
            ),
        ),
        extreme_days_to_cover_count=_reason_count(
            rows,
            "equity_short_interest_squeeze_extreme_days_to_cover",
        ),
        high_borrow_fee_count=_any_reason_count(
            rows,
            (
                "equity_short_interest_squeeze_high_borrow_fee",
                "equity_short_interest_squeeze_extreme_borrow_fee",
            ),
        ),
        extreme_borrow_fee_count=_reason_count(
            rows,
            "equity_short_interest_squeeze_extreme_borrow_fee",
        ),
        rally_confirmation_count=_reason_count(
            rows,
            "equity_short_interest_squeeze_price_rally",
        ),
        thin_source_count=_reason_count(rows, "equity_short_interest_squeeze_thin_sources"),
        stale_observation_count=_reason_count(
            rows,
            "equity_short_interest_squeeze_stale_observation",
        ),
        float_uncertainty_count=_reason_count(
            rows,
            "equity_short_interest_squeeze_float_uncertainty",
        ),
        max_short_interest_ratio=_max_row_decimal(rows, "short_interest_ratio"),
        average_short_interest_ratio=_ratio(
            _sum_decimal(row.short_interest_ratio for row in rows),
            row_count,
        ),
        max_days_to_cover=_max_row_decimal(rows, "days_to_cover"),
        average_days_to_cover=_ratio(
            _sum_decimal(row.days_to_cover for row in rows),
            row_count,
        ),
        max_borrow_fee_rate=_max_row_decimal(rows, "borrow_fee_rate"),
        average_borrow_fee_rate=_ratio(
            _sum_decimal(row.borrow_fee_rate for row in rows),
            row_count,
        ),
        squeeze_risk_score=_squeeze_risk_score(rows),
        digest_status=digest_status,
        recommended_next_step=_recommended_next_step(digest_status),
        rows=rows,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
        reason_codes=reason_codes,
    )


def market_research_equity_short_interest_squeeze_digest_payload(
    report: MarketResearchEquityShortInterestSqueezeDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchEquityShortInterestSqueezeDigestReport:
        raise ValueError(
            "report must be exactly "
            "MarketResearchEquityShortInterestSqueezeDigestReport",
        )
    _require_payload_safe_value("report", report)
    return _payload_value(report)


def _row_from_observation(
    observation: MarketResearchEquityShortInterestSqueezeDigestObservation,
    *,
    config: MarketResearchEquityShortInterestSqueezeDigestConfig,
    generated_at: datetime,
) -> MarketResearchEquityShortInterestSqueezeDigestRow:
    observation_age_seconds = _observation_age_seconds(
        observation.data_timestamp,
        generated_at,
    )
    squeeze_status = _squeeze_status(
        observation,
        observation_age_seconds=observation_age_seconds,
        config=config,
    )
    return MarketResearchEquityShortInterestSqueezeDigestRow(
        source_id=observation.source_id,
        equity_symbol=observation.equity_symbol,
        market_slug=observation.market_slug,
        short_interest_ratio=observation.short_interest_ratio,
        short_interest_excess_ratio=_positive_excess(
            observation.short_interest_ratio,
            DEFAULT_BLOCKED_SHORT_INTEREST_RATIO,
        ),
        days_to_cover=observation.days_to_cover,
        days_to_cover_excess=_positive_excess(
            observation.days_to_cover,
            DEFAULT_BLOCKED_DAYS_TO_COVER,
        ),
        borrow_fee_rate=observation.borrow_fee_rate,
        borrow_fee_excess_rate=_positive_excess(
            observation.borrow_fee_rate,
            DEFAULT_BLOCKED_BORROW_FEE_RATE,
        ),
        five_day_price_return_pct=observation.five_day_price_return_pct,
        float_uncertainty_ratio=observation.float_uncertainty_ratio,
        source_count=observation.source_count,
        observation_age_seconds=observation_age_seconds,
        data_timestamp=observation.data_timestamp,
        squeeze_status=squeeze_status,
        reason_codes=_row_reason_codes(
            observation,
            squeeze_status=squeeze_status,
            observation_age_seconds=observation_age_seconds,
            config=config,
        ),
    )


def _squeeze_status(
    observation: MarketResearchEquityShortInterestSqueezeDigestObservation,
    *,
    observation_age_seconds: Decimal,
    config: MarketResearchEquityShortInterestSqueezeDigestConfig,
) -> str:
    if (
        observation.short_interest_ratio >= config.blocked_short_interest_ratio
        or observation.days_to_cover >= config.blocked_days_to_cover
        or observation.borrow_fee_rate >= config.blocked_borrow_fee_rate
        or observation_age_seconds > config.max_observation_age_seconds
        or observation.float_uncertainty_ratio > config.max_float_uncertainty_ratio
    ):
        return "blocked"
    if (
        observation.short_interest_ratio >= config.watch_short_interest_ratio
        or observation.days_to_cover >= config.watch_days_to_cover
        or observation.borrow_fee_rate >= config.watch_borrow_fee_rate
        or observation.five_day_price_return_pct >= config.rally_confirmation_pct
        or observation.source_count < config.min_source_count
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    observation: MarketResearchEquityShortInterestSqueezeDigestObservation,
    *,
    squeeze_status: str,
    observation_age_seconds: Decimal,
    config: MarketResearchEquityShortInterestSqueezeDigestConfig,
) -> tuple[str, ...]:
    if squeeze_status == "blocked":
        reason_codes = ["equity_short_interest_squeeze_blocked"]
    elif squeeze_status == "watch":
        reason_codes = ["equity_short_interest_squeeze_watch"]
    else:
        reason_codes = ["equity_short_interest_squeeze_inline"]

    if squeeze_status != "pass":
        _append_threshold_reason(
            reason_codes,
            value=observation.short_interest_ratio,
            watch_threshold=config.watch_short_interest_ratio,
            blocked_threshold=config.blocked_short_interest_ratio,
            watch_reason="equity_short_interest_squeeze_high_short_interest",
            blocked_reason="equity_short_interest_squeeze_extreme_short_interest",
        )
        _append_threshold_reason(
            reason_codes,
            value=observation.days_to_cover,
            watch_threshold=config.watch_days_to_cover,
            blocked_threshold=config.blocked_days_to_cover,
            watch_reason="equity_short_interest_squeeze_high_days_to_cover",
            blocked_reason="equity_short_interest_squeeze_extreme_days_to_cover",
        )
        _append_threshold_reason(
            reason_codes,
            value=observation.borrow_fee_rate,
            watch_threshold=config.watch_borrow_fee_rate,
            blocked_threshold=config.blocked_borrow_fee_rate,
            watch_reason="equity_short_interest_squeeze_high_borrow_fee",
            blocked_reason="equity_short_interest_squeeze_extreme_borrow_fee",
        )
        if observation.five_day_price_return_pct >= config.rally_confirmation_pct:
            reason_codes.append("equity_short_interest_squeeze_price_rally")
        if observation.source_count < config.min_source_count:
            reason_codes.append("equity_short_interest_squeeze_thin_sources")
        if observation_age_seconds > config.max_observation_age_seconds:
            reason_codes.append("equity_short_interest_squeeze_stale_observation")
        if observation.float_uncertainty_ratio > config.max_float_uncertainty_ratio:
            reason_codes.append("equity_short_interest_squeeze_float_uncertainty")

    return _normalize_reason_codes(
        "reason_codes",
        tuple(sorted(reason_codes, key=ROW_REASON_CODES.index)),
        ROW_REASON_CODES,
    )


def _append_threshold_reason(
    reason_codes: list[str],
    *,
    value: Decimal,
    watch_threshold: Decimal,
    blocked_threshold: Decimal,
    watch_reason: str,
    blocked_reason: str,
) -> None:
    if value >= blocked_threshold:
        reason_codes.append(blocked_reason)
    elif value >= watch_threshold:
        reason_codes.append(watch_reason)


def _report_reason_codes(
    rows: tuple[MarketResearchEquityShortInterestSqueezeDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("equity_short_interest_squeeze_digest_empty",)
    reason_codes: list[str] = []
    if any(row.squeeze_status == "blocked" for row in rows):
        reason_codes.append("equity_short_interest_squeeze_blocked_present")
    if _any_reason_count(
        rows,
        (
            "equity_short_interest_squeeze_high_short_interest",
            "equity_short_interest_squeeze_extreme_short_interest",
        ),
    ) > ZERO:
        reason_codes.append("equity_short_interest_squeeze_crowded_short_present")
    if _any_reason_count(
        rows,
        (
            "equity_short_interest_squeeze_high_days_to_cover",
            "equity_short_interest_squeeze_extreme_days_to_cover",
        ),
    ) > ZERO:
        reason_codes.append("equity_short_interest_squeeze_days_to_cover_present")
    if _any_reason_count(
        rows,
        (
            "equity_short_interest_squeeze_high_borrow_fee",
            "equity_short_interest_squeeze_extreme_borrow_fee",
        ),
    ) > ZERO:
        reason_codes.append("equity_short_interest_squeeze_borrow_stress_present")
    if _reason_count(rows, "equity_short_interest_squeeze_price_rally") > ZERO:
        reason_codes.append("equity_short_interest_squeeze_price_rally_present")
    if _any_reason_count(
        rows,
        (
            "equity_short_interest_squeeze_thin_sources",
            "equity_short_interest_squeeze_stale_observation",
            "equity_short_interest_squeeze_float_uncertainty",
        ),
    ) > ZERO:
        reason_codes.append("equity_short_interest_squeeze_data_quality_present")
    if not reason_codes:
        reason_codes.append("equity_short_interest_squeeze_digest_clear")
    return tuple(reason for reason in REPORT_REASON_CODES if reason in reason_codes)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[MarketResearchEquityShortInterestSqueezeDigestRow, ...],
) -> tuple[MarketResearchEquityShortInterestSqueezeReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    if reason_codes == ("equity_short_interest_squeeze_digest_empty",):
        return (
            MarketResearchEquityShortInterestSqueezeReasonCodeCount(
                reason_code="equity_short_interest_squeeze_digest_empty",
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    return tuple(
        MarketResearchEquityShortInterestSqueezeReasonCodeCount(
            reason_code=reason_code,
            count=_report_reason_row_count(reason_code, rows),
            row_ratio=_ratio(_report_reason_row_count(reason_code, rows), row_count),
        )
        for reason_code in reason_codes
    )


def _report_reason_row_count(
    reason_code: str,
    rows: tuple[MarketResearchEquityShortInterestSqueezeDigestRow, ...],
) -> Decimal:
    if reason_code == "equity_short_interest_squeeze_blocked_present":
        return _status_count(rows, "blocked")
    if reason_code == "equity_short_interest_squeeze_crowded_short_present":
        return _any_reason_count(
            rows,
            (
                "equity_short_interest_squeeze_high_short_interest",
                "equity_short_interest_squeeze_extreme_short_interest",
            ),
        )
    if reason_code == "equity_short_interest_squeeze_days_to_cover_present":
        return _any_reason_count(
            rows,
            (
                "equity_short_interest_squeeze_high_days_to_cover",
                "equity_short_interest_squeeze_extreme_days_to_cover",
            ),
        )
    if reason_code == "equity_short_interest_squeeze_borrow_stress_present":
        return _any_reason_count(
            rows,
            (
                "equity_short_interest_squeeze_high_borrow_fee",
                "equity_short_interest_squeeze_extreme_borrow_fee",
            ),
        )
    if reason_code == "equity_short_interest_squeeze_price_rally_present":
        return _reason_count(rows, "equity_short_interest_squeeze_price_rally")
    if reason_code == "equity_short_interest_squeeze_data_quality_present":
        return _any_reason_count(
            rows,
            (
                "equity_short_interest_squeeze_thin_sources",
                "equity_short_interest_squeeze_stale_observation",
                "equity_short_interest_squeeze_float_uncertainty",
            ),
        )
    return _reason_count(rows, "equity_short_interest_squeeze_inline")


def _digest_status(
    rows: tuple[MarketResearchEquityShortInterestSqueezeDigestRow, ...],
) -> str:
    if not rows:
        return "blocked"
    if any(row.squeeze_status == "blocked" for row in rows):
        return "blocked"
    if any(row.squeeze_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _recommended_next_step(status: str) -> str:
    if status == "pass":
        return "allow_report_only_equity_short_interest_squeeze_screening"
    if status == "watch":
        return "monitor_report_only_equity_short_interest_squeeze_screening"
    return "block_report_only_equity_short_interest_squeeze_screening"


def _squeeze_risk_score(
    rows: tuple[MarketResearchEquityShortInterestSqueezeDigestRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    if _digest_status(rows) == "blocked":
        return ONE
    if _digest_status(rows) == "watch":
        return WATCH_RISK_SCORE
    return ZERO


def _observation_age_seconds(observed_at: datetime, generated_at: datetime) -> Decimal:
    age_seconds = _quantize_decimal(
        Decimal(str((generated_at - _as_utc("data_timestamp", observed_at)).total_seconds())),
    )
    if age_seconds < ZERO:
        raise ValueError("data_timestamp must not be future dated")
    return age_seconds


def _validate_row(row: MarketResearchEquityShortInterestSqueezeDigestRow) -> None:
    if row.short_interest_excess_ratio != _positive_excess(
        row.short_interest_ratio,
        DEFAULT_BLOCKED_SHORT_INTEREST_RATIO,
    ):
        raise ValueError("short_interest_excess_ratio must match short_interest_ratio")
    if row.days_to_cover_excess != _positive_excess(
        row.days_to_cover,
        DEFAULT_BLOCKED_DAYS_TO_COVER,
    ):
        raise ValueError("days_to_cover_excess must match days_to_cover")
    if row.borrow_fee_excess_rate != _positive_excess(
        row.borrow_fee_rate,
        DEFAULT_BLOCKED_BORROW_FEE_RATE,
    ):
        raise ValueError("borrow_fee_excess_rate must match borrow_fee_rate")
    if row.squeeze_status == "pass":
        if row.reason_codes != ("equity_short_interest_squeeze_inline",):
            raise ValueError("reason_codes must match squeeze_status")
        return
    if row.squeeze_status == "watch":
        if "equity_short_interest_squeeze_watch" not in row.reason_codes:
            raise ValueError("reason_codes must match squeeze_status")
        if "equity_short_interest_squeeze_blocked" in row.reason_codes:
            raise ValueError("reason_codes must match squeeze_status")
    if row.squeeze_status == "blocked":
        if "equity_short_interest_squeeze_blocked" not in row.reason_codes:
            raise ValueError("reason_codes must match squeeze_status")
        if "equity_short_interest_squeeze_watch" in row.reason_codes:
            raise ValueError("reason_codes must match squeeze_status")


def _validate_report(report: MarketResearchEquityShortInterestSqueezeDigestReport) -> None:
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
        raise ValueError("status counts must match rows")
    if report.high_short_interest_count != _any_reason_count(
        report.rows,
        (
            "equity_short_interest_squeeze_high_short_interest",
            "equity_short_interest_squeeze_extreme_short_interest",
        ),
    ):
        raise ValueError("high_short_interest_count must match rows")
    if report.extreme_short_interest_count != _reason_count(
        report.rows,
        "equity_short_interest_squeeze_extreme_short_interest",
    ):
        raise ValueError("extreme_short_interest_count must match rows")
    if report.high_days_to_cover_count != _any_reason_count(
        report.rows,
        (
            "equity_short_interest_squeeze_high_days_to_cover",
            "equity_short_interest_squeeze_extreme_days_to_cover",
        ),
    ):
        raise ValueError("high_days_to_cover_count must match rows")
    if report.extreme_days_to_cover_count != _reason_count(
        report.rows,
        "equity_short_interest_squeeze_extreme_days_to_cover",
    ):
        raise ValueError("extreme_days_to_cover_count must match rows")
    if report.high_borrow_fee_count != _any_reason_count(
        report.rows,
        (
            "equity_short_interest_squeeze_high_borrow_fee",
            "equity_short_interest_squeeze_extreme_borrow_fee",
        ),
    ):
        raise ValueError("high_borrow_fee_count must match rows")
    if report.extreme_borrow_fee_count != _reason_count(
        report.rows,
        "equity_short_interest_squeeze_extreme_borrow_fee",
    ):
        raise ValueError("extreme_borrow_fee_count must match rows")
    if report.rally_confirmation_count != _reason_count(
        report.rows,
        "equity_short_interest_squeeze_price_rally",
    ):
        raise ValueError("rally_confirmation_count must match rows")
    if report.thin_source_count != _reason_count(
        report.rows,
        "equity_short_interest_squeeze_thin_sources",
    ):
        raise ValueError("thin_source_count must match rows")
    if report.stale_observation_count != _reason_count(
        report.rows,
        "equity_short_interest_squeeze_stale_observation",
    ):
        raise ValueError("stale_observation_count must match rows")
    if report.float_uncertainty_count != _reason_count(
        report.rows,
        "equity_short_interest_squeeze_float_uncertainty",
    ):
        raise ValueError("float_uncertainty_count must match rows")
    if report.max_short_interest_ratio != _max_row_decimal(
        report.rows,
        "short_interest_ratio",
    ):
        raise ValueError("max_short_interest_ratio must match rows")
    if report.average_short_interest_ratio != _ratio(
        _sum_decimal(row.short_interest_ratio for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_short_interest_ratio must match rows")
    if report.max_days_to_cover != _max_row_decimal(report.rows, "days_to_cover"):
        raise ValueError("max_days_to_cover must match rows")
    if report.average_days_to_cover != _ratio(
        _sum_decimal(row.days_to_cover for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_days_to_cover must match rows")
    if report.max_borrow_fee_rate != _max_row_decimal(report.rows, "borrow_fee_rate"):
        raise ValueError("max_borrow_fee_rate must match rows")
    if report.average_borrow_fee_rate != _ratio(
        _sum_decimal(row.borrow_fee_rate for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_borrow_fee_rate must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.squeeze_risk_score != _squeeze_risk_score(report.rows):
        raise ValueError("squeeze_risk_score must match rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step must match digest_status")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, report.rows):
        raise ValueError("reason_code_counts must match reason_codes")


def _normalize_observations(
    observations: Iterable[MarketResearchEquityShortInterestSqueezeDigestObservation],
) -> tuple[MarketResearchEquityShortInterestSqueezeDigestObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError(
            "observations must contain "
            "MarketResearchEquityShortInterestSqueezeDigestObservation",
        )
    normalized = tuple(observations)
    seen_source_ids: set[str] = set()
    for observation in normalized:
        if type(observation) is not MarketResearchEquityShortInterestSqueezeDigestObservation:
            raise ValueError(
                "observations must contain "
                "MarketResearchEquityShortInterestSqueezeDigestObservation",
            )
        _require_hard_flags("observation", observation)
        if observation.source_id in seen_source_ids:
            raise ValueError("observations must not contain duplicate source_id values")
        seen_source_ids.add(observation.source_id)
    return normalized


def _normalize_rows(
    rows: Iterable[MarketResearchEquityShortInterestSqueezeDigestRow],
) -> tuple[MarketResearchEquityShortInterestSqueezeDigestRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError(
            "rows must contain MarketResearchEquityShortInterestSqueezeDigestRow",
        )
    normalized = tuple(rows)
    seen_source_ids: set[str] = set()
    for row in normalized:
        if type(row) is not MarketResearchEquityShortInterestSqueezeDigestRow:
            raise ValueError(
                "rows must contain MarketResearchEquityShortInterestSqueezeDigestRow",
            )
        _require_hard_flags("row", row)
        if row.source_id in seen_source_ids:
            raise ValueError("rows must not contain duplicate source_id values")
        seen_source_ids.add(row.source_id)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted")
    return normalized


def _normalize_reason_code_counts(
    values: Iterable[MarketResearchEquityShortInterestSqueezeReasonCodeCount],
) -> tuple[MarketResearchEquityShortInterestSqueezeReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError("reason_code_counts must contain reason code counts")
    normalized = tuple(values)
    seen_reason_codes: set[str] = set()
    for value in normalized:
        if type(value) is not MarketResearchEquityShortInterestSqueezeReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchEquityShortInterestSqueezeReasonCodeCount",
            )
        _require_hard_flags("reason code count", value)
        if value.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts must not contain duplicates")
        seen_reason_codes.add(value.reason_code)
    if normalized != tuple(
        sorted(normalized, key=lambda value: REPORT_REASON_CODES.index(value.reason_code)),
    ):
        raise ValueError("reason_code_counts must be sorted")
    return normalized


def _normalize_upstream_reason_codes(
    field_name: str,
    values: Iterable[str],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError(f"{field_name} must contain reason code strings")
    normalized = tuple(values)
    for value in normalized:
        _require_canonical_string("reason_code", value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    if normalized != tuple(sorted(normalized)):
        raise ValueError(f"{field_name} must be sorted")
    return normalized


def _normalize_reason_codes(
    field_name: str,
    values: Iterable[str],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError(f"{field_name} must contain reason code strings")
    normalized = tuple(values)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    for value in normalized:
        _require_member("reason_code", value, allowed)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    if normalized != tuple(sorted(normalized, key=lambda value: allowed.index(value))):
        raise ValueError(f"{field_name} must be sorted")
    return normalized


def _row_sort_key(
    row: MarketResearchEquityShortInterestSqueezeDigestRow,
) -> tuple[Decimal, Decimal, Decimal, str, str]:
    return (
        STATUS_RANK[row.squeeze_status],
        -row.short_interest_ratio,
        -row.days_to_cover,
        row.equity_symbol,
        row.source_id,
    )


def _status_count(
    rows: tuple[MarketResearchEquityShortInterestSqueezeDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.squeeze_status == status))


def _reason_count(
    rows: tuple[MarketResearchEquityShortInterestSqueezeDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _any_reason_count(
    rows: tuple[MarketResearchEquityShortInterestSqueezeDigestRow, ...],
    reason_codes: tuple[str, ...],
) -> Decimal:
    return _count_decimal(
        sum(1 for row in rows if any(reason in row.reason_codes for reason in reason_codes)),
    )


def _max_row_decimal(
    rows: tuple[MarketResearchEquityShortInterestSqueezeDigestRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("values must be Decimals")
        total += value
    return _quantize_decimal(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(numerator / denominator)


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _positive_excess(value: Decimal, threshold: Decimal) -> Decimal:
    excess = value - threshold
    if excess <= ZERO:
        return ZERO
    return _quantize_decimal(excess)


def _require_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
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


def _require_decimal(field_name: str, value: object) -> Decimal:
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


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must be supported")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value or _CANONICAL_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_payload_safe_value(field_name: str, value: object) -> None:
    if type(value) is Decimal:
        _require_six_decimal(field_name, value)
        return
    if isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be exactly Decimal")
    if type(value) is datetime:
        _as_utc(field_name, value)
        if value.tzinfo is not UTC:
            raise ValueError(f"{field_name} must be normalized to UTC")
        return
    if isinstance(value, datetime):
        raise ValueError(f"{field_name} must be exactly datetime")
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{field_name} must be a supported public dataclass")
        _require_hard_flags(_PUBLIC_DATACLASS_PAYLOAD_LABELS[type(value)], value)
        for field in fields(value):
            _require_payload_safe_value(
                f"{field_name}.{field.name}",
                getattr(value, field.name),
            )
        _reconstruct_public_dataclass(field_name, value)
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            _require_payload_safe_value(f"{field_name}[{index}]", item)
        return
    if type(value) in (str, bool) or value is None:
        return
    if type(value) in (list, dict, set):
        raise ValueError(f"{field_name} must remain constructor-normalized")
    raise ValueError(f"{field_name} must be safe for payload serialization")


def _require_six_decimal(field_name: str, value: Decimal) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != -6:
        raise ValueError(f"{field_name} must have exactly six decimal places")
    if _quantize_decimal(value) != value:
        raise ValueError(f"{field_name} must have exactly six decimal places")


def _reconstruct_public_dataclass(field_name: str, value: object) -> None:
    try:
        type(value)(**{field.name: getattr(value, field.name) for field in fields(value)})
    except (ArithmeticError, TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must remain constructor-valid") from exc


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        return f"{value:.6f}"
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    return value
