"""Pure report-only reducer for rates term-premium repricing digests."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_MARKET_RESEARCH_RATES_TERM_PREMIUM_REPRICING_DIGEST_CONFIG_VERSION = (
    "market-research-rates-term-premium-repricing-digest-v0"
)

QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCKED_STATUS = "blocked"
STATUSES = (PASS_STATUS, WATCH_STATUS, BLOCKED_STATUS)

TERM_PREMIUM_DELTA_REASON = "rates_term_premium_repricing_term_premium_delta"
REAL_YIELD_SHIFT_REASON = "rates_term_premium_repricing_real_yield_shift"
INFLATION_BREAKEVEN_SHIFT_REASON = (
    "rates_term_premium_repricing_inflation_breakeven_shift"
)
AUCTION_SUPPLY_PRESSURE_REASON = (
    "rates_term_premium_repricing_auction_supply_pressure"
)
VOL_BREAKOUT_REASON = "rates_term_premium_repricing_vol_breakout"
SOURCE_FRESHNESS_RISK_REASON = (
    "rates_term_premium_repricing_source_freshness_risk"
)
SOURCE_QUORUM_RISK_REASON = "rates_term_premium_repricing_source_quorum_risk"
WATCH_SCORE_REASON = "rates_term_premium_repricing_watch_score"
BLOCKED_SCORE_REASON = "rates_term_premium_repricing_blocked_score"
PASSED_REASON = "rates_term_premium_repricing_passed"
DIGEST_PASSED_REASON = "rates_term_premium_repricing_digest_passed"
DIGEST_EMPTY_REASON = "rates_term_premium_repricing_digest_empty"

ROW_REASON_CODES = (
    AUCTION_SUPPLY_PRESSURE_REASON,
    BLOCKED_SCORE_REASON,
    INFLATION_BREAKEVEN_SHIFT_REASON,
    PASSED_REASON,
    REAL_YIELD_SHIFT_REASON,
    SOURCE_FRESHNESS_RISK_REASON,
    SOURCE_QUORUM_RISK_REASON,
    TERM_PREMIUM_DELTA_REASON,
    VOL_BREAKOUT_REASON,
    WATCH_SCORE_REASON,
)
DIGEST_REASON_CODES = (
    AUCTION_SUPPLY_PRESSURE_REASON,
    BLOCKED_SCORE_REASON,
    DIGEST_EMPTY_REASON,
    DIGEST_PASSED_REASON,
    INFLATION_BREAKEVEN_SHIFT_REASON,
    REAL_YIELD_SHIFT_REASON,
    SOURCE_FRESHNESS_RISK_REASON,
    SOURCE_QUORUM_RISK_REASON,
    TERM_PREMIUM_DELTA_REASON,
    VOL_BREAKOUT_REASON,
    WATCH_SCORE_REASON,
)
KNOWN_REASON_CODES = tuple(dict.fromkeys((*ROW_REASON_CODES, *DIGEST_REASON_CODES)))
NEXT_STEP_BY_STATUS = {
    PASS_STATUS: "continue_rates_term_premium_monitoring",
    WATCH_STATUS: "review_rates_term_premium_repricing_digest",
    BLOCKED_STATUS: "review_rates_term_premium_repricing_digest",
}

__all__ = (
    "DEFAULT_MARKET_RESEARCH_RATES_TERM_PREMIUM_REPRICING_DIGEST_CONFIG_VERSION",
    "MarketResearchRatesTermPremiumRepricingDigestConfig",
    "MarketResearchRatesTermPremiumRepricingDigestReport",
    "MarketResearchRatesTermPremiumRepricingDigestRow",
    "MarketResearchRatesTermPremiumRepricingInput",
    "MarketResearchRatesTermPremiumRepricingReasonCodeCount",
    "build_market_research_rates_term_premium_repricing_digest",
    "market_research_rates_term_premium_repricing_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchRatesTermPremiumRepricingDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_RATES_TERM_PREMIUM_REPRICING_DIGEST_CONFIG_VERSION
    )
    watch_term_premium_delta_bps: Decimal = Decimal("10.000000")
    blocked_term_premium_delta_bps: Decimal = Decimal("25.000000")
    watch_real_yield_shift_bps: Decimal = Decimal("8.000000")
    watch_inflation_breakeven_shift_bps: Decimal = Decimal("6.000000")
    watch_auction_supply_pressure: Decimal = Decimal("0.600000")
    watch_vol_breakout: Decimal = Decimal("0.550000")
    source_freshness_watch_threshold: Decimal = Decimal("0.700000")
    source_quorum_watch_threshold: Decimal = Decimal("0.650000")
    risk_score_watch_threshold: Decimal = Decimal("0.500000")
    risk_score_blocked_threshold: Decimal = Decimal("0.800000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchRatesTermPremiumRepricingDigestConfig:
            raise TypeError(
                "MarketResearchRatesTermPremiumRepricingDigestConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchRatesTermPremiumRepricingDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchRatesTermPremiumRepricingDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "watch_term_premium_delta_bps",
            "blocked_term_premium_delta_bps",
            "watch_real_yield_shift_bps",
            "watch_inflation_breakeven_shift_bps",
            "watch_auction_supply_pressure",
            "watch_vol_breakout",
            "source_freshness_watch_threshold",
            "source_quorum_watch_threshold",
            "risk_score_watch_threshold",
            "risk_score_blocked_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_term_premium_delta_bps <= ZERO:
            raise ValueError("watch_term_premium_delta_bps must be positive")
        if self.blocked_term_premium_delta_bps <= self.watch_term_premium_delta_bps:
            raise ValueError(
                "blocked_term_premium_delta_bps must exceed "
                "watch_term_premium_delta_bps",
            )
        if self.risk_score_watch_threshold <= ZERO:
            raise ValueError("risk_score_watch_threshold must be positive")
        if self.risk_score_blocked_threshold <= self.risk_score_watch_threshold:
            raise ValueError(
                "risk_score_blocked_threshold must exceed risk_score_watch_threshold",
            )
        for field_name in (
            "watch_auction_supply_pressure",
            "watch_vol_breakout",
            "source_freshness_watch_threshold",
            "source_quorum_watch_threshold",
            "risk_score_watch_threshold",
            "risk_score_blocked_threshold",
        ):
            _require_probability(field_name, getattr(self, field_name))
        require_paper_only_flags(
            "MarketResearchRatesTermPremiumRepricingDigestConfig",
            self,
        )


@dataclass(frozen=True)
class MarketResearchRatesTermPremiumRepricingInput:
    market_slug: str
    tenor_bucket: str
    observed_at: datetime
    term_premium_delta_bps: Decimal
    real_yield_shift_bps: Decimal
    inflation_breakeven_shift_bps: Decimal
    auction_supply_pressure: Decimal
    vol_breakout_score: Decimal
    source_freshness_ratio: Decimal
    source_quorum_ratio: Decimal
    upstream_reason_codes: tuple[str, ...]
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchRatesTermPremiumRepricingInput:
            raise TypeError(
                "MarketResearchRatesTermPremiumRepricingInput does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchRatesTermPremiumRepricingInput:
            raise ValueError(
                "input must be exactly MarketResearchRatesTermPremiumRepricingInput",
            )
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("tenor_bucket", self.tenor_bucket)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "term_premium_delta_bps",
            "real_yield_shift_bps",
            "inflation_breakeven_shift_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "auction_supply_pressure",
            "vol_breakout_score",
            "source_freshness_ratio",
            "source_quorum_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_upstream_reason_codes(self.upstream_reason_codes),
        )
        _require_canonical_string("source_config_version", self.source_config_version)
        require_paper_only_flags(
            "MarketResearchRatesTermPremiumRepricingInput",
            self,
        )


@dataclass(frozen=True)
class MarketResearchRatesTermPremiumRepricingReasonCodeCount:
    reason_code: str
    market_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchRatesTermPremiumRepricingReasonCodeCount:
            raise TypeError(
                "MarketResearchRatesTermPremiumRepricingReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchRatesTermPremiumRepricingReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "MarketResearchRatesTermPremiumRepricingReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        if self.reason_code in (DIGEST_EMPTY_REASON, DIGEST_PASSED_REASON, PASSED_REASON):
            raise ValueError("reason_code must be a row risk reason")
        object.__setattr__(
            self,
            "market_count",
            _normalize_nonnegative_decimal("market_count", self.market_count),
        )
        if self.market_count <= ZERO:
            raise ValueError("market_count must be positive")
        require_paper_only_flags(
            "MarketResearchRatesTermPremiumRepricingReasonCodeCount",
            self,
        )


@dataclass(frozen=True)
class MarketResearchRatesTermPremiumRepricingDigestRow:
    market_slug: str
    tenor_bucket: str
    observed_at: datetime
    term_premium_delta_bps: Decimal
    term_premium_delta_abs_bps: Decimal
    real_yield_shift_bps: Decimal
    real_yield_shift_abs_bps: Decimal
    inflation_breakeven_shift_bps: Decimal
    inflation_breakeven_shift_abs_bps: Decimal
    auction_supply_pressure: Decimal
    vol_breakout_score: Decimal
    source_freshness_ratio: Decimal
    source_quorum_ratio: Decimal
    risk_score: Decimal
    digest_status: str
    source_config_version: str
    upstream_reason_codes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchRatesTermPremiumRepricingDigestRow:
            raise TypeError(
                "MarketResearchRatesTermPremiumRepricingDigestRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchRatesTermPremiumRepricingDigestRow:
            raise ValueError(
                "row must be exactly MarketResearchRatesTermPremiumRepricingDigestRow",
            )
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("tenor_bucket", self.tenor_bucket)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "term_premium_delta_bps",
            "term_premium_delta_abs_bps",
            "real_yield_shift_bps",
            "real_yield_shift_abs_bps",
            "inflation_breakeven_shift_bps",
            "inflation_breakeven_shift_abs_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "auction_supply_pressure",
            "vol_breakout_score",
            "source_freshness_ratio",
            "source_quorum_ratio",
            "risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_status("digest_status", self.digest_status)
        _require_canonical_string("source_config_version", self.source_config_version)
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_upstream_reason_codes(self.upstream_reason_codes),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        require_paper_only_flags(
            "MarketResearchRatesTermPremiumRepricingDigestRow",
            self,
        )


@dataclass(frozen=True)
class MarketResearchRatesTermPremiumRepricingDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    market_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    term_premium_repricing_count: Decimal
    real_yield_shift_count: Decimal
    inflation_breakeven_shift_count: Decimal
    auction_supply_pressure_count: Decimal
    vol_breakout_count: Decimal
    source_freshness_risk_count: Decimal
    source_quorum_risk_count: Decimal
    max_risk_score: Decimal | None
    average_risk_score: Decimal | None
    rows: tuple[MarketResearchRatesTermPremiumRepricingDigestRow, ...]
    reason_code_counts: tuple[
        MarketResearchRatesTermPremiumRepricingReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchRatesTermPremiumRepricingDigestReport:
            raise TypeError(
                "MarketResearchRatesTermPremiumRepricingDigestReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchRatesTermPremiumRepricingDigestReport:
            raise ValueError(
                "report must be exactly "
                "MarketResearchRatesTermPremiumRepricingDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "market_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "term_premium_repricing_count",
            "real_yield_shift_count",
            "inflation_breakeven_shift_count",
            "auction_supply_pressure_count",
            "vol_breakout_count",
            "source_freshness_risk_count",
            "source_quorum_risk_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_risk_score",
            _normalize_optional_probability("max_risk_score", self.max_risk_score),
        )
        object.__setattr__(
            self,
            "average_risk_score",
            _normalize_optional_probability(
                "average_risk_score",
                self.average_risk_score,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_digest_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        require_paper_only_flags(
            "MarketResearchRatesTermPremiumRepricingDigestReport",
            self,
        )


def build_market_research_rates_term_premium_repricing_digest(
    inputs: Iterable[MarketResearchRatesTermPremiumRepricingInput],
    *,
    config: MarketResearchRatesTermPremiumRepricingDigestConfig,
    generated_at: datetime,
) -> MarketResearchRatesTermPremiumRepricingDigestReport:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    if type(config) is not MarketResearchRatesTermPremiumRepricingDigestConfig:
        raise ValueError(
            "config must be a MarketResearchRatesTermPremiumRepricingDigestConfig",
        )
    require_paper_only_flags(
        "MarketResearchRatesTermPremiumRepricingDigestConfig",
        config,
    )
    generated_at_utc = _as_utc("generated_at", generated_at)
    try:
        input_items = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    _validate_inputs(input_items)

    rows = _build_rows(input_items, config=config, generated_at=generated_at_utc)
    digest_status = _digest_status(rows)
    reason_codes = _digest_reason_codes(rows)
    return MarketResearchRatesTermPremiumRepricingDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[digest_status],
        market_count=_count(len(rows)),
        pass_count=_status_count(rows, PASS_STATUS),
        watch_count=_status_count(rows, WATCH_STATUS),
        blocked_count=_status_count(rows, BLOCKED_STATUS),
        term_premium_repricing_count=_reason_row_count(
            rows,
            TERM_PREMIUM_DELTA_REASON,
        ),
        real_yield_shift_count=_reason_row_count(rows, REAL_YIELD_SHIFT_REASON),
        inflation_breakeven_shift_count=_reason_row_count(
            rows,
            INFLATION_BREAKEVEN_SHIFT_REASON,
        ),
        auction_supply_pressure_count=_reason_row_count(
            rows,
            AUCTION_SUPPLY_PRESSURE_REASON,
        ),
        vol_breakout_count=_reason_row_count(rows, VOL_BREAKOUT_REASON),
        source_freshness_risk_count=_reason_row_count(
            rows,
            SOURCE_FRESHNESS_RISK_REASON,
        ),
        source_quorum_risk_count=_reason_row_count(rows, SOURCE_QUORUM_RISK_REASON),
        max_risk_score=_max_risk_score(rows),
        average_risk_score=_average_risk_score(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
        reason_codes=reason_codes,
    )


def market_research_rates_term_premium_repricing_digest_payload(
    report: MarketResearchRatesTermPremiumRepricingDigestReport,
) -> dict[str, object]:
    if type(report) is not MarketResearchRatesTermPremiumRepricingDigestReport:
        raise ValueError(
            "report must be a MarketResearchRatesTermPremiumRepricingDigestReport",
        )
    require_paper_only_flags(
        "MarketResearchRatesTermPremiumRepricingDigestReport",
        report,
    )
    return {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "digest_status": report.digest_status,
        "recommended_next_step": report.recommended_next_step,
        "market_count": _decimal_string(report.market_count),
        "pass_count": _decimal_string(report.pass_count),
        "watch_count": _decimal_string(report.watch_count),
        "blocked_count": _decimal_string(report.blocked_count),
        "term_premium_repricing_count": _decimal_string(
            report.term_premium_repricing_count,
        ),
        "real_yield_shift_count": _decimal_string(report.real_yield_shift_count),
        "inflation_breakeven_shift_count": _decimal_string(
            report.inflation_breakeven_shift_count,
        ),
        "auction_supply_pressure_count": _decimal_string(
            report.auction_supply_pressure_count,
        ),
        "vol_breakout_count": _decimal_string(report.vol_breakout_count),
        "source_freshness_risk_count": _decimal_string(
            report.source_freshness_risk_count,
        ),
        "source_quorum_risk_count": _decimal_string(report.source_quorum_risk_count),
        "max_risk_score": _optional_decimal_string(report.max_risk_score),
        "average_risk_score": _optional_decimal_string(report.average_risk_score),
        "rows": [
            {
                "market_slug": row.market_slug,
                "tenor_bucket": row.tenor_bucket,
                "observed_at": row.observed_at.isoformat(),
                "term_premium_delta_bps": _decimal_string(
                    row.term_premium_delta_bps,
                ),
                "term_premium_delta_abs_bps": _decimal_string(
                    row.term_premium_delta_abs_bps,
                ),
                "real_yield_shift_bps": _decimal_string(row.real_yield_shift_bps),
                "real_yield_shift_abs_bps": _decimal_string(
                    row.real_yield_shift_abs_bps,
                ),
                "inflation_breakeven_shift_bps": _decimal_string(
                    row.inflation_breakeven_shift_bps,
                ),
                "inflation_breakeven_shift_abs_bps": _decimal_string(
                    row.inflation_breakeven_shift_abs_bps,
                ),
                "auction_supply_pressure": _decimal_string(
                    row.auction_supply_pressure,
                ),
                "vol_breakout_score": _decimal_string(row.vol_breakout_score),
                "source_freshness_ratio": _decimal_string(row.source_freshness_ratio),
                "source_quorum_ratio": _decimal_string(row.source_quorum_ratio),
                "risk_score": _decimal_string(row.risk_score),
                "digest_status": row.digest_status,
                "source_config_version": row.source_config_version,
                "upstream_reason_codes": list(row.upstream_reason_codes),
                "reason_codes": list(row.reason_codes),
                "paper_only": row.paper_only,
                "report_only": row.report_only,
                "readonly": row.readonly,
            }
            for row in report.rows
        ],
        "reason_code_counts": [
            {
                "reason_code": reason_count.reason_code,
                "market_count": _decimal_string(reason_count.market_count),
                "paper_only": reason_count.paper_only,
                "report_only": reason_count.report_only,
                "readonly": reason_count.readonly,
            }
            for reason_count in report.reason_code_counts
        ],
        "reason_codes": list(report.reason_codes),
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _validate_inputs(
    inputs: tuple[MarketResearchRatesTermPremiumRepricingInput, ...],
) -> None:
    seen: set[str] = set()
    for input_row in inputs:
        if type(input_row) is not MarketResearchRatesTermPremiumRepricingInput:
            raise ValueError(
                "inputs must contain "
                "MarketResearchRatesTermPremiumRepricingInput values",
            )
        require_paper_only_flags(
            "MarketResearchRatesTermPremiumRepricingInput",
            input_row,
        )
        if input_row.market_slug in seen:
            raise ValueError("inputs must use unique market_slug values")
        seen.add(input_row.market_slug)


def _build_rows(
    inputs: tuple[MarketResearchRatesTermPremiumRepricingInput, ...],
    *,
    config: MarketResearchRatesTermPremiumRepricingDigestConfig,
    generated_at: datetime,
) -> tuple[MarketResearchRatesTermPremiumRepricingDigestRow, ...]:
    rows: list[MarketResearchRatesTermPremiumRepricingDigestRow] = []
    for input_row in inputs:
        if input_row.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        term_abs = abs(input_row.term_premium_delta_bps).quantize(QUANT)
        real_abs = abs(input_row.real_yield_shift_bps).quantize(QUANT)
        breakeven_abs = abs(input_row.inflation_breakeven_shift_bps).quantize(QUANT)
        risk_score = _risk_score(
            term_premium_delta_abs_bps=term_abs,
            real_yield_shift_abs_bps=real_abs,
            inflation_breakeven_shift_abs_bps=breakeven_abs,
            auction_supply_pressure=input_row.auction_supply_pressure,
            vol_breakout_score=input_row.vol_breakout_score,
            source_freshness_ratio=input_row.source_freshness_ratio,
            source_quorum_ratio=input_row.source_quorum_ratio,
            config=config,
        )
        digest_status = _row_status(
            risk_score=risk_score,
            term_premium_delta_abs_bps=term_abs,
            real_yield_shift_abs_bps=real_abs,
            inflation_breakeven_shift_abs_bps=breakeven_abs,
            auction_supply_pressure=input_row.auction_supply_pressure,
            vol_breakout_score=input_row.vol_breakout_score,
            source_freshness_ratio=input_row.source_freshness_ratio,
            source_quorum_ratio=input_row.source_quorum_ratio,
            config=config,
        )
        rows.append(
            MarketResearchRatesTermPremiumRepricingDigestRow(
                market_slug=input_row.market_slug,
                tenor_bucket=input_row.tenor_bucket,
                observed_at=input_row.observed_at,
                term_premium_delta_bps=input_row.term_premium_delta_bps,
                term_premium_delta_abs_bps=term_abs,
                real_yield_shift_bps=input_row.real_yield_shift_bps,
                real_yield_shift_abs_bps=real_abs,
                inflation_breakeven_shift_bps=input_row.inflation_breakeven_shift_bps,
                inflation_breakeven_shift_abs_bps=breakeven_abs,
                auction_supply_pressure=input_row.auction_supply_pressure,
                vol_breakout_score=input_row.vol_breakout_score,
                source_freshness_ratio=input_row.source_freshness_ratio,
                source_quorum_ratio=input_row.source_quorum_ratio,
                risk_score=risk_score,
                digest_status=digest_status,
                source_config_version=input_row.source_config_version,
                upstream_reason_codes=input_row.upstream_reason_codes,
                reason_codes=_row_reason_codes(
                    term_premium_delta_abs_bps=term_abs,
                    real_yield_shift_abs_bps=real_abs,
                    inflation_breakeven_shift_abs_bps=breakeven_abs,
                    auction_supply_pressure=input_row.auction_supply_pressure,
                    vol_breakout_score=input_row.vol_breakout_score,
                    source_freshness_ratio=input_row.source_freshness_ratio,
                    source_quorum_ratio=input_row.source_quorum_ratio,
                    risk_score=risk_score,
                    config=config,
                ),
            ),
        )
    return _sorted_rows(tuple(rows))


def _row_reason_codes(
    *,
    term_premium_delta_abs_bps: Decimal,
    real_yield_shift_abs_bps: Decimal,
    inflation_breakeven_shift_abs_bps: Decimal,
    auction_supply_pressure: Decimal,
    vol_breakout_score: Decimal,
    source_freshness_ratio: Decimal,
    source_quorum_ratio: Decimal,
    risk_score: Decimal,
    config: MarketResearchRatesTermPremiumRepricingDigestConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if auction_supply_pressure >= config.watch_auction_supply_pressure:
        reason_codes.append(AUCTION_SUPPLY_PRESSURE_REASON)
    if risk_score >= config.risk_score_blocked_threshold:
        reason_codes.append(BLOCKED_SCORE_REASON)
    elif risk_score >= config.risk_score_watch_threshold:
        reason_codes.append(WATCH_SCORE_REASON)
    elif term_premium_delta_abs_bps >= config.watch_term_premium_delta_bps:
        reason_codes.append(WATCH_SCORE_REASON)
    if (
        inflation_breakeven_shift_abs_bps
        >= config.watch_inflation_breakeven_shift_bps
    ):
        reason_codes.append(INFLATION_BREAKEVEN_SHIFT_REASON)
    if real_yield_shift_abs_bps >= config.watch_real_yield_shift_bps:
        reason_codes.append(REAL_YIELD_SHIFT_REASON)
    if source_freshness_ratio < config.source_freshness_watch_threshold:
        reason_codes.append(SOURCE_FRESHNESS_RISK_REASON)
    if source_quorum_ratio < config.source_quorum_watch_threshold:
        reason_codes.append(SOURCE_QUORUM_RISK_REASON)
    if term_premium_delta_abs_bps >= config.watch_term_premium_delta_bps:
        reason_codes.append(TERM_PREMIUM_DELTA_REASON)
    if vol_breakout_score >= config.watch_vol_breakout:
        reason_codes.append(VOL_BREAKOUT_REASON)
    if not reason_codes:
        reason_codes.append(PASSED_REASON)
    return tuple(sorted(dict.fromkeys(reason_codes)))


def _risk_score(
    *,
    term_premium_delta_abs_bps: Decimal,
    real_yield_shift_abs_bps: Decimal,
    inflation_breakeven_shift_abs_bps: Decimal,
    auction_supply_pressure: Decimal,
    vol_breakout_score: Decimal,
    source_freshness_ratio: Decimal,
    source_quorum_ratio: Decimal,
    config: MarketResearchRatesTermPremiumRepricingDigestConfig,
) -> Decimal:
    if not (
        term_premium_delta_abs_bps >= config.watch_term_premium_delta_bps
        or real_yield_shift_abs_bps >= config.watch_real_yield_shift_bps
        or inflation_breakeven_shift_abs_bps
        >= config.watch_inflation_breakeven_shift_bps
        or auction_supply_pressure >= config.watch_auction_supply_pressure
        or vol_breakout_score >= config.watch_vol_breakout
        or source_freshness_ratio < config.source_freshness_watch_threshold
        or source_quorum_ratio < config.source_quorum_watch_threshold
    ):
        return ZERO
    score = max(
        _ratio(
            term_premium_delta_abs_bps,
            config.blocked_term_premium_delta_bps,
        ),
        _ratio(real_yield_shift_abs_bps, config.blocked_term_premium_delta_bps),
        _ratio(
            inflation_breakeven_shift_abs_bps,
            config.blocked_term_premium_delta_bps,
        ),
        auction_supply_pressure,
        vol_breakout_score,
        ONE - source_freshness_ratio,
        ONE - source_quorum_ratio,
    )
    if score > ONE:
        return ONE
    return score.quantize(QUANT, rounding=ROUND_HALF_UP)


def _row_status(
    *,
    risk_score: Decimal,
    term_premium_delta_abs_bps: Decimal,
    real_yield_shift_abs_bps: Decimal,
    inflation_breakeven_shift_abs_bps: Decimal,
    auction_supply_pressure: Decimal,
    vol_breakout_score: Decimal,
    source_freshness_ratio: Decimal,
    source_quorum_ratio: Decimal,
    config: MarketResearchRatesTermPremiumRepricingDigestConfig,
) -> str:
    if risk_score >= config.risk_score_blocked_threshold:
        return BLOCKED_STATUS
    if (
        risk_score >= config.risk_score_watch_threshold
        or term_premium_delta_abs_bps >= config.watch_term_premium_delta_bps
        or real_yield_shift_abs_bps >= config.watch_real_yield_shift_bps
        or inflation_breakeven_shift_abs_bps
        >= config.watch_inflation_breakeven_shift_bps
        or auction_supply_pressure >= config.watch_auction_supply_pressure
        or vol_breakout_score >= config.watch_vol_breakout
        or source_freshness_ratio < config.source_freshness_watch_threshold
        or source_quorum_ratio < config.source_quorum_watch_threshold
    ):
        return WATCH_STATUS
    return PASS_STATUS


def _digest_status(
    rows: tuple[MarketResearchRatesTermPremiumRepricingDigestRow, ...],
) -> str:
    if any(row.digest_status == BLOCKED_STATUS for row in rows):
        return BLOCKED_STATUS
    if any(row.digest_status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _digest_reason_codes(
    rows: tuple[MarketResearchRatesTermPremiumRepricingDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (DIGEST_EMPTY_REASON,)
    reason_codes = tuple(
        reason_code
        for reason_code in _unique_row_reason_codes(rows)
        if reason_code != PASSED_REASON
    )
    return reason_codes if reason_codes else (DIGEST_PASSED_REASON,)


def _unique_row_reason_codes(
    rows: tuple[MarketResearchRatesTermPremiumRepricingDigestRow, ...],
) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                reason_code
                for row in rows
                for reason_code in row.reason_codes
            },
        ),
    )


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[MarketResearchRatesTermPremiumRepricingDigestRow, ...],
) -> tuple[MarketResearchRatesTermPremiumRepricingReasonCodeCount, ...]:
    return tuple(
        MarketResearchRatesTermPremiumRepricingReasonCodeCount(
            reason_code=reason_code,
            market_count=_count(
                sum(1 for row in rows if reason_code in row.reason_codes),
            ),
        )
        for reason_code in reason_codes
        if reason_code not in (DIGEST_EMPTY_REASON, DIGEST_PASSED_REASON)
    )


def _sorted_rows(
    rows: tuple[MarketResearchRatesTermPremiumRepricingDigestRow, ...],
) -> tuple[MarketResearchRatesTermPremiumRepricingDigestRow, ...]:
    status_weight = {BLOCKED_STATUS: 0, WATCH_STATUS: 1, PASS_STATUS: 2}
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                status_weight[row.digest_status],
                row.tenor_bucket,
                row.market_slug,
                row.observed_at,
            ),
        ),
    )


def _status_count(
    rows: tuple[MarketResearchRatesTermPremiumRepricingDigestRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.digest_status == status))


def _reason_row_count(
    rows: tuple[MarketResearchRatesTermPremiumRepricingDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_risk_score(
    rows: tuple[MarketResearchRatesTermPremiumRepricingDigestRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return max(row.risk_score for row in rows).quantize(QUANT)


def _average_risk_score(
    rows: tuple[MarketResearchRatesTermPremiumRepricingDigestRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return (
        sum((row.risk_score for row in rows), ZERO) / _count(len(rows))
    ).quantize(QUANT, rounding=ROUND_HALF_UP)


def _validate_row(row: MarketResearchRatesTermPremiumRepricingDigestRow) -> None:
    if row.term_premium_delta_abs_bps != abs(row.term_premium_delta_bps).quantize(QUANT):
        raise ValueError("term_premium_delta_abs_bps must match absolute delta")
    if row.real_yield_shift_abs_bps != abs(row.real_yield_shift_bps).quantize(QUANT):
        raise ValueError("real_yield_shift_abs_bps must match absolute shift")
    if row.inflation_breakeven_shift_abs_bps != abs(
        row.inflation_breakeven_shift_bps,
    ).quantize(QUANT):
        raise ValueError(
            "inflation_breakeven_shift_abs_bps must match absolute shift",
        )
    if row.digest_status != PASS_STATUS and row.reason_codes == (PASSED_REASON,):
        raise ValueError("watch and blocked rows must include repricing reasons")
    if row.digest_status == PASS_STATUS and row.reason_codes != (PASSED_REASON,):
        raise ValueError("pass rows must use passed reason only")


def _validate_report(report: MarketResearchRatesTermPremiumRepricingDigestReport) -> None:
    rows = report.rows
    if report.market_count != _count(len(rows)):
        raise ValueError("market_count must match rows")
    if report.pass_count != _status_count(rows, PASS_STATUS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, WATCH_STATUS):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(rows, BLOCKED_STATUS):
        raise ValueError("blocked_count must match rows")
    if report.term_premium_repricing_count != _reason_row_count(
        rows,
        TERM_PREMIUM_DELTA_REASON,
    ):
        raise ValueError("term_premium_repricing_count must match rows")
    if report.real_yield_shift_count != _reason_row_count(rows, REAL_YIELD_SHIFT_REASON):
        raise ValueError("real_yield_shift_count must match rows")
    if report.inflation_breakeven_shift_count != _reason_row_count(
        rows,
        INFLATION_BREAKEVEN_SHIFT_REASON,
    ):
        raise ValueError("inflation_breakeven_shift_count must match rows")
    if report.auction_supply_pressure_count != _reason_row_count(
        rows,
        AUCTION_SUPPLY_PRESSURE_REASON,
    ):
        raise ValueError("auction_supply_pressure_count must match rows")
    if report.vol_breakout_count != _reason_row_count(rows, VOL_BREAKOUT_REASON):
        raise ValueError("vol_breakout_count must match rows")
    if report.source_freshness_risk_count != _reason_row_count(
        rows,
        SOURCE_FRESHNESS_RISK_REASON,
    ):
        raise ValueError("source_freshness_risk_count must match rows")
    if report.source_quorum_risk_count != _reason_row_count(
        rows,
        SOURCE_QUORUM_RISK_REASON,
    ):
        raise ValueError("source_quorum_risk_count must match rows")
    if report.max_risk_score != _max_risk_score(rows):
        raise ValueError("max_risk_score must match rows")
    if report.average_risk_score != _average_risk_score(rows):
        raise ValueError("average_risk_score must match rows")
    if report.rows != _sorted_rows(report.rows):
        raise ValueError("rows must use deterministic sequence")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, rows):
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != _digest_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.digest_status != _digest_status(rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != NEXT_STEP_BY_STATUS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest status")


def _normalize_rows(
    rows: tuple[MarketResearchRatesTermPremiumRepricingDigestRow, ...],
) -> tuple[MarketResearchRatesTermPremiumRepricingDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen: set[str] = set()
    for row in rows:
        if type(row) is not MarketResearchRatesTermPremiumRepricingDigestRow:
            raise ValueError(
                "rows must contain "
                "MarketResearchRatesTermPremiumRepricingDigestRow values",
            )
        require_paper_only_flags(
            "MarketResearchRatesTermPremiumRepricingDigestRow",
            row,
        )
        if row.market_slug in seen:
            raise ValueError("rows must use unique market_slug values")
        seen.add(row.market_slug)
    return rows


def _normalize_reason_code_counts(
    counts: tuple[MarketResearchRatesTermPremiumRepricingReasonCodeCount, ...],
) -> tuple[MarketResearchRatesTermPremiumRepricingReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    seen: set[str] = set()
    for count in counts:
        if type(count) is not MarketResearchRatesTermPremiumRepricingReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchRatesTermPremiumRepricingReasonCodeCount values",
            )
        require_paper_only_flags(
            "MarketResearchRatesTermPremiumRepricingReasonCodeCount",
            count,
        )
        if count.reason_code in seen:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen.add(count.reason_code)
    if tuple(count.reason_code for count in counts) != tuple(sorted(seen)):
        raise ValueError("reason_code_counts must use deterministic sequence")
    return counts


def _normalize_row_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    normalized = _normalize_reason_code_tuple("reason_codes", reason_codes)
    for reason_code in normalized:
        if reason_code not in ROW_REASON_CODES:
            raise ValueError("reason_codes must contain known row reason codes")
    if PASSED_REASON in normalized and normalized != (PASSED_REASON,):
        raise ValueError("passed reason must not be mixed with risk reasons")
    return normalized


def _normalize_digest_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    normalized = _normalize_reason_code_tuple("reason_codes", reason_codes)
    for reason_code in normalized:
        if reason_code not in DIGEST_REASON_CODES:
            raise ValueError("reason_codes must contain known digest reason codes")
    if DIGEST_EMPTY_REASON in normalized and normalized != (DIGEST_EMPTY_REASON,):
        raise ValueError("empty reason must not be mixed with risk reasons")
    if DIGEST_PASSED_REASON in normalized and normalized != (DIGEST_PASSED_REASON,):
        raise ValueError("passed reason must not be mixed with risk reasons")
    return normalized


def _normalize_reason_code_tuple(
    field_name: str,
    reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        _require_reason_code(field_name, reason_code)
    if tuple(sorted(set(reason_codes))) != reason_codes:
        raise ValueError(f"{field_name} must be unique and sorted")
    return reason_codes


def _normalize_upstream_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("upstream_reason_codes must be a tuple")
    if not reason_codes:
        raise ValueError("upstream_reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_canonical_string("upstream_reason_codes", reason_code)
    if tuple(sorted(set(reason_codes))) != reason_codes:
        raise ValueError("upstream_reason_codes must be unique and sorted")
    return reason_codes


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    _require_decimal(field_name, value)
    return value.quantize(QUANT)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    _require_probability(field_name, normalized)
    return normalized


def _normalize_optional_probability(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_probability(field_name, value)


def _require_probability(field_name: str, value: Decimal) -> None:
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("ratio denominator must be positive")
    return (numerator / denominator).quantize(QUANT, rounding=ROUND_HALF_UP)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in KNOWN_REASON_CODES:
        raise ValueError(f"{field_name} must contain known reason codes")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _decimal_string(value: Decimal) -> str:
    return str(value.quantize(QUANT))


def _optional_decimal_string(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return _decimal_string(value)
