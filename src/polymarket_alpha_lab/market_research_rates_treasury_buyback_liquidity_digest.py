"""Pure Phase 1 rates Treasury buyback liquidity research reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_RATES_TREASURY_BUYBACK_LIQUIDITY_DIGEST_CONFIG_VERSION = (
    "market-research-rates-treasury-buyback-liquidity-digest-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
DIGEST_STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCKED)

NO_INPUTS_REASON = (
    "market_research_rates_treasury_buyback_liquidity_digest_no_inputs"
)
PASS_REASON = "market_research_rates_treasury_buyback_liquidity_digest_pass"
STALE_SIGNAL_REASON = (
    "market_research_rates_treasury_buyback_liquidity_digest_stale_signal"
)
LOW_ACCEPTED_AMOUNT_REASON = (
    "market_research_rates_treasury_buyback_liquidity_digest_low_accepted_amount"
)
ACCEPTED_GAP_REASON = (
    "market_research_rates_treasury_buyback_liquidity_digest_accepted_gap"
)
OFFER_PRESSURE_BLOCKED_REASON = (
    "market_research_rates_treasury_buyback_liquidity_digest_offer_pressure_blocked"
)
PRICE_CONCESSION_BLOCKED_REASON = (
    "market_research_rates_treasury_buyback_liquidity_digest_price_concession_blocked"
)
LIQUIDITY_STRESS_BLOCKED_REASON = (
    "market_research_rates_treasury_buyback_liquidity_digest_liquidity_stress_blocked"
)
SOURCE_FAMILY_GAP_REASON = (
    "market_research_rates_treasury_buyback_liquidity_digest_source_family_gap"
)
STALE_SOURCE_RATIO_REASON = (
    "market_research_rates_treasury_buyback_liquidity_digest_stale_source_ratio"
)
CONFIRMATION_GAP_REASON = (
    "market_research_rates_treasury_buyback_liquidity_digest_confirmation_gap"
)
OFFER_PRESSURE_WATCH_REASON = (
    "market_research_rates_treasury_buyback_liquidity_digest_offer_pressure_watch"
)
PRICE_CONCESSION_WATCH_REASON = (
    "market_research_rates_treasury_buyback_liquidity_digest_price_concession_watch"
)
LIQUIDITY_STRESS_WATCH_REASON = (
    "market_research_rates_treasury_buyback_liquidity_digest_liquidity_stress_watch"
)

REASON_CODE_SEQUENCE = (
    STALE_SIGNAL_REASON,
    LOW_ACCEPTED_AMOUNT_REASON,
    ACCEPTED_GAP_REASON,
    OFFER_PRESSURE_BLOCKED_REASON,
    PRICE_CONCESSION_BLOCKED_REASON,
    LIQUIDITY_STRESS_BLOCKED_REASON,
    SOURCE_FAMILY_GAP_REASON,
    STALE_SOURCE_RATIO_REASON,
    CONFIRMATION_GAP_REASON,
    OFFER_PRESSURE_WATCH_REASON,
    PRICE_CONCESSION_WATCH_REASON,
    LIQUIDITY_STRESS_WATCH_REASON,
    PASS_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    STALE_SIGNAL_REASON,
    LOW_ACCEPTED_AMOUNT_REASON,
    ACCEPTED_GAP_REASON,
    OFFER_PRESSURE_BLOCKED_REASON,
    PRICE_CONCESSION_BLOCKED_REASON,
    LIQUIDITY_STRESS_BLOCKED_REASON,
    SOURCE_FAMILY_GAP_REASON,
    STALE_SOURCE_RATIO_REASON,
    OFFER_PRESSURE_WATCH_REASON,
    PRICE_CONCESSION_WATCH_REASON,
    LIQUIDITY_STRESS_WATCH_REASON,
    CONFIRMATION_GAP_REASON,
    PASS_REASON,
)
BLOCKING_REASONS = frozenset(
    (
        STALE_SIGNAL_REASON,
        LOW_ACCEPTED_AMOUNT_REASON,
        ACCEPTED_GAP_REASON,
        OFFER_PRESSURE_BLOCKED_REASON,
        PRICE_CONCESSION_BLOCKED_REASON,
        LIQUIDITY_STRESS_BLOCKED_REASON,
        SOURCE_FAMILY_GAP_REASON,
        STALE_SOURCE_RATIO_REASON,
    ),
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")

UNSAFE_REFERENCE_FRAGMENTS = frozenset(
    (
        "bear" "er",
        "cred" "ential",
        "api" "_" "key",
        "private" "_" "key",
        "sec" "ret",
        "tok" "en",
        "wall" "et",
    ),
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_RATES_TREASURY_BUYBACK_LIQUIDITY_DIGEST_CONFIG_VERSION",
    "MarketResearchRatesTreasuryBuybackLiquidityDigestConfig",
    "MarketResearchRatesTreasuryBuybackLiquidityDigestReasonCodeCount",
    "MarketResearchRatesTreasuryBuybackLiquidityDigestReport",
    "MarketResearchRatesTreasuryBuybackLiquidityDigestRow",
    "MarketResearchRatesTreasuryBuybackLiquidityDigestSignal",
    "build_market_research_rates_treasury_buyback_liquidity_digest",
    "market_research_rates_treasury_buyback_liquidity_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchRatesTreasuryBuybackLiquidityDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_RATES_TREASURY_BUYBACK_LIQUIDITY_DIGEST_CONFIG_VERSION
    )
    max_signal_age_seconds: Decimal = Decimal("7200.000000")
    min_accepted_amount_billion: Decimal = Decimal("5.000000")
    max_accepted_gap_billion: Decimal = Decimal("5.000000")
    watch_offer_to_accept_ratio: Decimal = Decimal("2.500000")
    blocked_offer_to_accept_ratio: Decimal = Decimal("4.000000")
    watch_price_concession_bp: Decimal = Decimal("3.000000")
    blocked_price_concession_bp: Decimal = Decimal("8.000000")
    watch_liquidity_stress_score: Decimal = Decimal("0.450000")
    blocked_liquidity_stress_score: Decimal = Decimal("0.750000")
    min_source_family_count: Decimal = Decimal("3.000000")
    max_stale_source_ratio: Decimal = Decimal("0.250000")
    min_confirmation_ratio: Decimal = Decimal("0.650000")
    confidence_decay_per_reason: Decimal = Decimal("0.050000")
    watch_confidence_threshold: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchRatesTreasuryBuybackLiquidityDigestConfig:
            raise TypeError(
                "MarketResearchRatesTreasuryBuybackLiquidityDigestConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchRatesTreasuryBuybackLiquidityDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchRatesTreasuryBuybackLiquidityDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_RATES_TREASURY_BUYBACK_LIQUIDITY_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_signal_age_seconds",
            "min_accepted_amount_billion",
            "max_accepted_gap_billion",
            "watch_offer_to_accept_ratio",
            "blocked_offer_to_accept_ratio",
            "watch_price_concession_bp",
            "blocked_price_concession_bp",
            "min_source_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_liquidity_stress_score",
            "blocked_liquidity_stress_score",
            "max_stale_source_ratio",
            "min_confirmation_ratio",
            "confidence_decay_per_reason",
            "watch_confidence_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.blocked_offer_to_accept_ratio <= self.watch_offer_to_accept_ratio:
            raise ValueError(
                "blocked_offer_to_accept_ratio must exceed "
                "watch_offer_to_accept_ratio",
            )
        if self.blocked_price_concession_bp <= self.watch_price_concession_bp:
            raise ValueError(
                "blocked_price_concession_bp must exceed "
                "watch_price_concession_bp",
            )
        if self.blocked_liquidity_stress_score <= self.watch_liquidity_stress_score:
            raise ValueError(
                "blocked_liquidity_stress_score must exceed "
                "watch_liquidity_stress_score",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchRatesTreasuryBuybackLiquidityDigestSignal:
    condition_id: str
    operation_window_key: str
    tenor_bucket: str
    public_signal_reference: str
    observed_at: datetime
    signal_age_seconds: Decimal
    accepted_amount_billion: Decimal
    offered_amount_billion: Decimal
    scheduled_amount_billion: Decimal
    offer_to_accept_ratio: Decimal
    average_price_concession_bp: Decimal
    liquidity_stress_score: Decimal
    source_family_count: Decimal
    stale_source_ratio: Decimal
    confirmation_ratio: Decimal
    base_confidence: Decimal
    signal_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchRatesTreasuryBuybackLiquidityDigestSignal:
            raise TypeError(
                "MarketResearchRatesTreasuryBuybackLiquidityDigestSignal "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchRatesTreasuryBuybackLiquidityDigestSignal:
            raise ValueError(
                "signal must be exactly "
                "MarketResearchRatesTreasuryBuybackLiquidityDigestSignal",
            )
        for field_name in (
            "condition_id",
            "operation_window_key",
            "tenor_bucket",
            "signal_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_canonical_string("public_signal_reference", self.public_signal_reference)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "signal_age_seconds",
            _require_nonnegative_decimal("signal_age_seconds", self.signal_age_seconds),
        )
        object.__setattr__(
            self,
            "accepted_amount_billion",
            _require_positive_decimal(
                "accepted_amount_billion",
                self.accepted_amount_billion,
            ),
        )
        object.__setattr__(
            self,
            "scheduled_amount_billion",
            _require_positive_decimal(
                "scheduled_amount_billion",
                self.scheduled_amount_billion,
            ),
        )
        for field_name in (
            "offered_amount_billion",
            "average_price_concession_bp",
            "source_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "offer_to_accept_ratio",
            _require_positive_decimal(
                "offer_to_accept_ratio",
                self.offer_to_accept_ratio,
            ),
        )
        for field_name in (
            "liquidity_stress_score",
            "stale_source_ratio",
            "confirmation_ratio",
            "base_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.offer_to_accept_ratio != _ratio(
            self.offered_amount_billion,
            self.accepted_amount_billion,
        ):
            raise ValueError("offer_to_accept_ratio must match offered and accepted")
        _require_hard_flags("signal", self)


@dataclass(frozen=True)
class MarketResearchRatesTreasuryBuybackLiquidityDigestRow:
    condition_id: str
    operation_window_key: str
    tenor_bucket: str
    observed_at: datetime
    signal_age_seconds: Decimal
    accepted_amount_billion: Decimal
    offered_amount_billion: Decimal
    scheduled_amount_billion: Decimal
    accepted_gap_billion: Decimal
    unaccepted_offer_billion: Decimal
    offer_to_accept_ratio: Decimal
    average_price_concession_bp: Decimal
    liquidity_stress_score: Decimal
    source_family_count: Decimal
    stale_source_ratio: Decimal
    confirmation_ratio: Decimal
    base_confidence: Decimal
    confidence_decay_factor: Decimal
    final_confidence: Decimal
    digest_status: str
    redacted_public_signal_reference: str
    signal_config_version: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchRatesTreasuryBuybackLiquidityDigestRow:
            raise TypeError(
                "MarketResearchRatesTreasuryBuybackLiquidityDigestRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchRatesTreasuryBuybackLiquidityDigestRow:
            raise ValueError(
                "row must be exactly MarketResearchRatesTreasuryBuybackLiquidityDigestRow",
            )
        for field_name in (
            "condition_id",
            "operation_window_key",
            "tenor_bucket",
            "signal_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "accepted_amount_billion",
            "scheduled_amount_billion",
            "offer_to_accept_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "signal_age_seconds",
            "offered_amount_billion",
            "accepted_gap_billion",
            "unaccepted_offer_billion",
            "average_price_concession_bp",
            "source_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "liquidity_stress_score",
            "stale_source_ratio",
            "confirmation_ratio",
            "base_confidence",
            "confidence_decay_factor",
            "final_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("digest_status", self.digest_status)
        _require_redacted_reference(
            "redacted_public_signal_reference",
            self.redacted_public_signal_reference,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, sequence=ROW_REASON_CODE_SEQUENCE),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchRatesTreasuryBuybackLiquidityDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    signal_ratio: Decimal = ZERO
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchRatesTreasuryBuybackLiquidityDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchRatesTreasuryBuybackLiquidityDigestReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchRatesTreasuryBuybackLiquidityDigestReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "MarketResearchRatesTreasuryBuybackLiquidityDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "signal_ratio",
            _require_ratio_decimal("signal_ratio", self.signal_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchRatesTreasuryBuybackLiquidityDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    signal_count: Decimal
    pass_signal_count: Decimal
    watch_signal_count: Decimal
    blocked_signal_count: Decimal
    stale_signal_count: Decimal
    low_accepted_amount_signal_count: Decimal
    accepted_gap_signal_count: Decimal
    blocked_offer_pressure_signal_count: Decimal
    watch_offer_pressure_signal_count: Decimal
    blocked_price_concession_signal_count: Decimal
    watch_price_concession_signal_count: Decimal
    blocked_liquidity_stress_signal_count: Decimal
    watch_liquidity_stress_signal_count: Decimal
    source_family_gap_signal_count: Decimal
    stale_source_signal_count: Decimal
    confirmation_gap_signal_count: Decimal
    total_confidence_decay: Decimal
    average_final_confidence: Decimal
    average_accepted_gap_billion: Decimal
    average_unaccepted_offer_billion: Decimal
    average_liquidity_stress_score: Decimal
    max_signal_age_seconds: Decimal
    min_accepted_amount_billion: Decimal
    max_accepted_gap_billion: Decimal
    watch_offer_to_accept_ratio: Decimal
    blocked_offer_to_accept_ratio: Decimal
    watch_price_concession_bp: Decimal
    blocked_price_concession_bp: Decimal
    watch_liquidity_stress_score: Decimal
    blocked_liquidity_stress_score: Decimal
    min_source_family_count: Decimal
    max_stale_source_ratio: Decimal
    min_confirmation_ratio: Decimal
    max_observed_signal_age_seconds: Decimal
    rows: tuple[MarketResearchRatesTreasuryBuybackLiquidityDigestRow, ...]
    signal_config_versions: tuple[tuple[str, str], ...] = ()
    reason_code_counts: tuple[
        MarketResearchRatesTreasuryBuybackLiquidityDigestReasonCodeCount,
        ...,
    ] = ()
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchRatesTreasuryBuybackLiquidityDigestReport:
            raise TypeError(
                "MarketResearchRatesTreasuryBuybackLiquidityDigestReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchRatesTreasuryBuybackLiquidityDigestReport:
            raise ValueError(
                "report must be exactly "
                "MarketResearchRatesTreasuryBuybackLiquidityDigestReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        _require_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "signal_count",
            "pass_signal_count",
            "watch_signal_count",
            "blocked_signal_count",
            "stale_signal_count",
            "low_accepted_amount_signal_count",
            "accepted_gap_signal_count",
            "blocked_offer_pressure_signal_count",
            "watch_offer_pressure_signal_count",
            "blocked_price_concession_signal_count",
            "watch_price_concession_signal_count",
            "blocked_liquidity_stress_signal_count",
            "watch_liquidity_stress_signal_count",
            "source_family_gap_signal_count",
            "stale_source_signal_count",
            "confirmation_gap_signal_count",
            "total_confidence_decay",
            "average_accepted_gap_billion",
            "average_unaccepted_offer_billion",
            "max_signal_age_seconds",
            "min_accepted_amount_billion",
            "max_accepted_gap_billion",
            "watch_offer_to_accept_ratio",
            "blocked_offer_to_accept_ratio",
            "watch_price_concession_bp",
            "blocked_price_concession_bp",
            "min_source_family_count",
            "max_observed_signal_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_final_confidence",
            "average_liquidity_stress_score",
            "watch_liquidity_stress_score",
            "blocked_liquidity_stress_score",
            "max_stale_source_ratio",
            "min_confirmation_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "signal_config_versions",
            _normalize_signal_config_versions(self.signal_config_versions),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, sequence=REASON_CODE_SEQUENCE),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_rates_treasury_buyback_liquidity_digest(
    signals: Iterable[MarketResearchRatesTreasuryBuybackLiquidityDigestSignal],
    *,
    config: MarketResearchRatesTreasuryBuybackLiquidityDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchRatesTreasuryBuybackLiquidityDigestReport:
    cfg = config or MarketResearchRatesTreasuryBuybackLiquidityDigestConfig()
    if type(cfg) is not MarketResearchRatesTreasuryBuybackLiquidityDigestConfig:
        raise ValueError(
            "config must be exactly "
            "MarketResearchRatesTreasuryBuybackLiquidityDigestConfig",
        )
    _require_hard_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_signals = _normalize_signals(signals)
    rows = tuple(
        _row_for_signal(signal, config=cfg, generated_at=generated_at_utc)
        for signal in normalized_signals
    )
    sorted_rows = tuple(
        sorted(
            rows,
            key=lambda row: (
                _row_sort_value(row),
                row.operation_window_key,
                row.condition_id,
            ),
        ),
    )
    report_status = _report_status(sorted_rows)
    signal_count = _decimal_count(len(sorted_rows))
    return MarketResearchRatesTreasuryBuybackLiquidityDigestReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        digest_status=report_status,
        recommended_next_step=_recommended_next_step(report_status),
        signal_count=signal_count,
        pass_signal_count=_status_count(sorted_rows, STATUS_PASS),
        watch_signal_count=_status_count(sorted_rows, STATUS_WATCH),
        blocked_signal_count=_status_count(sorted_rows, STATUS_BLOCKED),
        stale_signal_count=_reason_signal_count(sorted_rows, STALE_SIGNAL_REASON),
        low_accepted_amount_signal_count=_reason_signal_count(
            sorted_rows,
            LOW_ACCEPTED_AMOUNT_REASON,
        ),
        accepted_gap_signal_count=_reason_signal_count(
            sorted_rows,
            ACCEPTED_GAP_REASON,
        ),
        blocked_offer_pressure_signal_count=_reason_signal_count(
            sorted_rows,
            OFFER_PRESSURE_BLOCKED_REASON,
        ),
        watch_offer_pressure_signal_count=_reason_signal_count(
            sorted_rows,
            OFFER_PRESSURE_WATCH_REASON,
        ),
        blocked_price_concession_signal_count=_reason_signal_count(
            sorted_rows,
            PRICE_CONCESSION_BLOCKED_REASON,
        ),
        watch_price_concession_signal_count=_reason_signal_count(
            sorted_rows,
            PRICE_CONCESSION_WATCH_REASON,
        ),
        blocked_liquidity_stress_signal_count=_reason_signal_count(
            sorted_rows,
            LIQUIDITY_STRESS_BLOCKED_REASON,
        ),
        watch_liquidity_stress_signal_count=_reason_signal_count(
            sorted_rows,
            LIQUIDITY_STRESS_WATCH_REASON,
        ),
        source_family_gap_signal_count=_reason_signal_count(
            sorted_rows,
            SOURCE_FAMILY_GAP_REASON,
        ),
        stale_source_signal_count=_reason_signal_count(
            sorted_rows,
            STALE_SOURCE_RATIO_REASON,
        ),
        confirmation_gap_signal_count=_reason_signal_count(
            sorted_rows,
            CONFIRMATION_GAP_REASON,
        ),
        total_confidence_decay=_decimal_sum(
            row.confidence_decay_factor for row in sorted_rows
        ),
        average_final_confidence=_ratio(
            _decimal_sum(row.final_confidence for row in sorted_rows),
            signal_count,
        ),
        average_accepted_gap_billion=_ratio(
            _decimal_sum(row.accepted_gap_billion for row in sorted_rows),
            signal_count,
        ),
        average_unaccepted_offer_billion=_ratio(
            _decimal_sum(row.unaccepted_offer_billion for row in sorted_rows),
            signal_count,
        ),
        average_liquidity_stress_score=_ratio(
            _decimal_sum(row.liquidity_stress_score for row in sorted_rows),
            signal_count,
        ),
        max_signal_age_seconds=cfg.max_signal_age_seconds,
        min_accepted_amount_billion=cfg.min_accepted_amount_billion,
        max_accepted_gap_billion=cfg.max_accepted_gap_billion,
        watch_offer_to_accept_ratio=cfg.watch_offer_to_accept_ratio,
        blocked_offer_to_accept_ratio=cfg.blocked_offer_to_accept_ratio,
        watch_price_concession_bp=cfg.watch_price_concession_bp,
        blocked_price_concession_bp=cfg.blocked_price_concession_bp,
        watch_liquidity_stress_score=cfg.watch_liquidity_stress_score,
        blocked_liquidity_stress_score=cfg.blocked_liquidity_stress_score,
        min_source_family_count=cfg.min_source_family_count,
        max_stale_source_ratio=cfg.max_stale_source_ratio,
        min_confirmation_ratio=cfg.min_confirmation_ratio,
        max_observed_signal_age_seconds=max(
            (row.signal_age_seconds for row in sorted_rows),
            default=ZERO,
        ),
        rows=sorted_rows,
        signal_config_versions=tuple(
            sorted(
                (
                    signal.operation_window_key,
                    signal.signal_config_version,
                )
                for signal in normalized_signals
            ),
        ),
        reason_code_counts=_reason_code_counts(sorted_rows),
        reason_codes=_summary_reason_codes(sorted_rows),
    )


def market_research_rates_treasury_buyback_liquidity_digest_payload(
    report: MarketResearchRatesTreasuryBuybackLiquidityDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchRatesTreasuryBuybackLiquidityDigestReport:
        raise ValueError(
            "report must be exactly "
            "MarketResearchRatesTreasuryBuybackLiquidityDigestReport",
        )
    _require_hard_flags("report", report)
    ready = _json_ready(asdict(report))
    if type(ready) is not dict:
        raise ValueError("report payload must be a JSON object")
    return ready


def _row_for_signal(
    signal: MarketResearchRatesTreasuryBuybackLiquidityDigestSignal,
    *,
    config: MarketResearchRatesTreasuryBuybackLiquidityDigestConfig,
    generated_at: datetime,
) -> MarketResearchRatesTreasuryBuybackLiquidityDigestRow:
    if signal.observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    if signal.signal_age_seconds != _age_seconds(generated_at, signal.observed_at):
        raise ValueError("signal_age_seconds must match observed_at and generated_at")
    accepted_gap_billion = _absolute_decimal_difference(
        signal.accepted_amount_billion,
        signal.scheduled_amount_billion,
    )
    unaccepted_offer_billion = _nonnegative_decimal_difference(
        signal.offered_amount_billion,
        signal.accepted_amount_billion,
    )
    reason_codes = _row_reason_codes(
        signal=signal,
        accepted_gap_billion=accepted_gap_billion,
        config=config,
    )
    confidence_decay_factor = _confidence_decay_factor(reason_codes, config=config)
    final_confidence = _final_confidence(signal.base_confidence, confidence_decay_factor)
    return MarketResearchRatesTreasuryBuybackLiquidityDigestRow(
        condition_id=signal.condition_id,
        operation_window_key=signal.operation_window_key,
        tenor_bucket=signal.tenor_bucket,
        observed_at=signal.observed_at,
        signal_age_seconds=signal.signal_age_seconds,
        accepted_amount_billion=signal.accepted_amount_billion,
        offered_amount_billion=signal.offered_amount_billion,
        scheduled_amount_billion=signal.scheduled_amount_billion,
        accepted_gap_billion=accepted_gap_billion,
        unaccepted_offer_billion=unaccepted_offer_billion,
        offer_to_accept_ratio=signal.offer_to_accept_ratio,
        average_price_concession_bp=signal.average_price_concession_bp,
        liquidity_stress_score=signal.liquidity_stress_score,
        source_family_count=signal.source_family_count,
        stale_source_ratio=signal.stale_source_ratio,
        confirmation_ratio=signal.confirmation_ratio,
        base_confidence=signal.base_confidence,
        confidence_decay_factor=confidence_decay_factor,
        final_confidence=final_confidence,
        digest_status=_row_status(
            reason_codes,
            final_confidence=final_confidence,
            watch_confidence_threshold=config.watch_confidence_threshold,
        ),
        redacted_public_signal_reference=_redacted_reference(
            signal.public_signal_reference,
        ),
        signal_config_version=signal.signal_config_version,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    signal: MarketResearchRatesTreasuryBuybackLiquidityDigestSignal,
    accepted_gap_billion: Decimal,
    config: MarketResearchRatesTreasuryBuybackLiquidityDigestConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if signal.signal_age_seconds > config.max_signal_age_seconds:
        reasons.append(STALE_SIGNAL_REASON)
    if signal.accepted_amount_billion < config.min_accepted_amount_billion:
        reasons.append(LOW_ACCEPTED_AMOUNT_REASON)
    if accepted_gap_billion > config.max_accepted_gap_billion:
        reasons.append(ACCEPTED_GAP_REASON)
    if signal.offer_to_accept_ratio >= config.blocked_offer_to_accept_ratio:
        reasons.append(OFFER_PRESSURE_BLOCKED_REASON)
    elif signal.offer_to_accept_ratio >= config.watch_offer_to_accept_ratio:
        reasons.append(OFFER_PRESSURE_WATCH_REASON)
    if signal.average_price_concession_bp >= config.blocked_price_concession_bp:
        reasons.append(PRICE_CONCESSION_BLOCKED_REASON)
    elif signal.average_price_concession_bp >= config.watch_price_concession_bp:
        reasons.append(PRICE_CONCESSION_WATCH_REASON)
    if signal.liquidity_stress_score >= config.blocked_liquidity_stress_score:
        reasons.append(LIQUIDITY_STRESS_BLOCKED_REASON)
    elif signal.liquidity_stress_score >= config.watch_liquidity_stress_score:
        reasons.append(LIQUIDITY_STRESS_WATCH_REASON)
    if signal.source_family_count < config.min_source_family_count:
        reasons.append(SOURCE_FAMILY_GAP_REASON)
    if signal.stale_source_ratio > config.max_stale_source_ratio:
        reasons.append(STALE_SOURCE_RATIO_REASON)
    if signal.confirmation_ratio < config.min_confirmation_ratio:
        reasons.append(CONFIRMATION_GAP_REASON)
    if not reasons:
        reasons.append(PASS_REASON)
    return tuple(reason for reason in ROW_REASON_CODE_SEQUENCE if reason in reasons)


def _confidence_decay_factor(
    reason_codes: tuple[str, ...],
    *,
    config: MarketResearchRatesTreasuryBuybackLiquidityDigestConfig,
) -> Decimal:
    gap_count = sum(1 for reason in reason_codes if reason != PASS_REASON)
    return _quantize(config.confidence_decay_per_reason * _decimal_count(gap_count))


def _final_confidence(
    base_confidence: Decimal,
    confidence_decay_factor: Decimal,
) -> Decimal:
    return max(ZERO, _quantize(base_confidence - confidence_decay_factor))


def _row_status(
    reason_codes: tuple[str, ...],
    *,
    final_confidence: Decimal,
    watch_confidence_threshold: Decimal,
) -> str:
    if any(reason in BLOCKING_REASONS for reason in reason_codes):
        return STATUS_BLOCKED
    if reason_codes != (PASS_REASON,) or final_confidence < watch_confidence_threshold:
        return STATUS_WATCH
    return STATUS_PASS


def _report_status(
    rows: tuple[MarketResearchRatesTreasuryBuybackLiquidityDigestRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _recommended_next_step(status: str) -> str:
    if status == STATUS_PASS:
        return "allow_report_only_market_research_rates_treasury_buyback_liquidity_digest"
    if status == STATUS_WATCH:
        return "monitor_report_only_market_research_rates_treasury_buyback_liquidity_digest"
    return "block_report_only_market_research_rates_treasury_buyback_liquidity_digest"


def _summary_reason_codes(
    rows: tuple[MarketResearchRatesTreasuryBuybackLiquidityDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    seen = {reason for row in rows for reason in row.reason_codes}
    if PASS_REASON in seen and len(seen) > 1:
        seen.remove(PASS_REASON)
    return tuple(reason for reason in REASON_CODE_SEQUENCE if reason in seen)


def _reason_code_counts(
    rows: tuple[MarketResearchRatesTreasuryBuybackLiquidityDigestRow, ...],
) -> tuple[MarketResearchRatesTreasuryBuybackLiquidityDigestReasonCodeCount, ...]:
    if not rows:
        return ()
    total = _decimal_count(len(rows))
    counts: list[MarketResearchRatesTreasuryBuybackLiquidityDigestReasonCodeCount] = []
    for reason_code in REASON_CODE_SEQUENCE:
        count = _reason_signal_count(rows, reason_code)
        if count > ZERO and reason_code != PASS_REASON:
            counts.append(
                MarketResearchRatesTreasuryBuybackLiquidityDigestReasonCodeCount(
                    reason_code=reason_code,
                    count=count,
                    signal_ratio=_ratio(count, total),
                ),
            )
    return tuple(counts)


def _reason_signal_count(
    rows: tuple[MarketResearchRatesTreasuryBuybackLiquidityDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _status_count(
    rows: tuple[MarketResearchRatesTreasuryBuybackLiquidityDigestRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.digest_status == status))


def _validate_row(row: MarketResearchRatesTreasuryBuybackLiquidityDigestRow) -> None:
    if row.accepted_gap_billion != _absolute_decimal_difference(
        row.accepted_amount_billion,
        row.scheduled_amount_billion,
    ):
        raise ValueError("accepted_gap_billion must match accepted and scheduled")
    if row.unaccepted_offer_billion != _nonnegative_decimal_difference(
        row.offered_amount_billion,
        row.accepted_amount_billion,
    ):
        raise ValueError("unaccepted_offer_billion must match offered and accepted")
    if row.offer_to_accept_ratio != _ratio(
        row.offered_amount_billion,
        row.accepted_amount_billion,
    ):
        raise ValueError("offer_to_accept_ratio must match offered and accepted")
    if row.final_confidence != _final_confidence(
        row.base_confidence,
        row.confidence_decay_factor,
    ):
        raise ValueError("final_confidence must match confidence decay")
    if row.reason_codes == (PASS_REASON,) and row.confidence_decay_factor != ZERO:
        raise ValueError("pass rows must not have confidence decay")
    if row.digest_status == STATUS_PASS and row.reason_codes != (PASS_REASON,):
        raise ValueError("digest_status must match reason_codes")


def _validate_report(
    report: MarketResearchRatesTreasuryBuybackLiquidityDigestReport,
) -> None:
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step must match digest_status")
    if report.signal_count != _decimal_count(len(report.rows)):
        raise ValueError("signal_count must match rows")
    if report.pass_signal_count != _status_count(report.rows, STATUS_PASS):
        raise ValueError("pass_signal_count must match rows")
    if report.watch_signal_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_signal_count must match rows")
    if report.blocked_signal_count != _status_count(report.rows, STATUS_BLOCKED):
        raise ValueError("blocked_signal_count must match rows")
    if report.digest_status != _report_status(report.rows):
        raise ValueError("digest_status must match rows")
    reason_checks = (
        ("stale_signal_count", STALE_SIGNAL_REASON),
        ("low_accepted_amount_signal_count", LOW_ACCEPTED_AMOUNT_REASON),
        ("accepted_gap_signal_count", ACCEPTED_GAP_REASON),
        ("blocked_offer_pressure_signal_count", OFFER_PRESSURE_BLOCKED_REASON),
        ("watch_offer_pressure_signal_count", OFFER_PRESSURE_WATCH_REASON),
        (
            "blocked_price_concession_signal_count",
            PRICE_CONCESSION_BLOCKED_REASON,
        ),
        ("watch_price_concession_signal_count", PRICE_CONCESSION_WATCH_REASON),
        (
            "blocked_liquidity_stress_signal_count",
            LIQUIDITY_STRESS_BLOCKED_REASON,
        ),
        ("watch_liquidity_stress_signal_count", LIQUIDITY_STRESS_WATCH_REASON),
        ("source_family_gap_signal_count", SOURCE_FAMILY_GAP_REASON),
        ("stale_source_signal_count", STALE_SOURCE_RATIO_REASON),
        ("confirmation_gap_signal_count", CONFIRMATION_GAP_REASON),
    )
    for field_name, reason_code in reason_checks:
        if getattr(report, field_name) != _reason_signal_count(report.rows, reason_code):
            raise ValueError(f"{field_name} must match rows")
    if report.total_confidence_decay != _decimal_sum(
        row.confidence_decay_factor for row in report.rows
    ):
        raise ValueError("total_confidence_decay must match rows")
    if report.average_final_confidence != _ratio(
        _decimal_sum(row.final_confidence for row in report.rows),
        report.signal_count,
    ):
        raise ValueError("average_final_confidence must match rows")
    if report.average_accepted_gap_billion != _ratio(
        _decimal_sum(row.accepted_gap_billion for row in report.rows),
        report.signal_count,
    ):
        raise ValueError("average_accepted_gap_billion must match rows")
    if report.average_unaccepted_offer_billion != _ratio(
        _decimal_sum(row.unaccepted_offer_billion for row in report.rows),
        report.signal_count,
    ):
        raise ValueError("average_unaccepted_offer_billion must match rows")
    if report.average_liquidity_stress_score != _ratio(
        _decimal_sum(row.liquidity_stress_score for row in report.rows),
        report.signal_count,
    ):
        raise ValueError("average_liquidity_stress_score must match rows")
    if report.max_observed_signal_age_seconds != max(
        (row.signal_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_observed_signal_age_seconds must match rows")
    if report.signal_config_versions and len(report.signal_config_versions) != len(
        report.rows,
    ):
        raise ValueError("signal_config_versions must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_signals(
    signals: Iterable[MarketResearchRatesTreasuryBuybackLiquidityDigestSignal],
) -> tuple[MarketResearchRatesTreasuryBuybackLiquidityDigestSignal, ...]:
    if isinstance(signals, (str, bytes)):
        raise ValueError("signals must contain Treasury buyback liquidity signals")
    try:
        normalized = tuple(signals)
    except TypeError as exc:
        raise ValueError("signals must contain Treasury buyback liquidity signals") from exc
    seen_window_keys: set[str] = set()
    seen_condition_ids: set[str] = set()
    for signal in normalized:
        if type(signal) is not MarketResearchRatesTreasuryBuybackLiquidityDigestSignal:
            raise ValueError(
                "signals must contain "
                "MarketResearchRatesTreasuryBuybackLiquidityDigestSignal",
            )
        _require_hard_flags("signals", signal)
        if signal.operation_window_key in seen_window_keys:
            raise ValueError("operation_window_key values must be unique")
        if signal.condition_id in seen_condition_ids:
            raise ValueError("condition_id values must be unique")
        seen_window_keys.add(signal.operation_window_key)
        seen_condition_ids.add(signal.condition_id)
    return normalized


def _normalize_rows(
    rows: object,
) -> tuple[MarketResearchRatesTreasuryBuybackLiquidityDigestRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must contain Treasury buyback liquidity digest rows")
    try:
        normalized = tuple(rows)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must contain Treasury buyback liquidity digest rows") from exc
    for row in normalized:
        if type(row) is not MarketResearchRatesTreasuryBuybackLiquidityDigestRow:
            raise ValueError(
                "rows must contain MarketResearchRatesTreasuryBuybackLiquidityDigestRow",
            )
        _require_hard_flags("rows", row)
    if normalized != tuple(
        sorted(
            normalized,
            key=lambda row: (
                _row_sort_value(row),
                row.operation_window_key,
                row.condition_id,
            ),
        ),
    ):
        raise ValueError("rows must be sorted deterministically")
    if len({row.operation_window_key for row in normalized}) != len(normalized):
        raise ValueError("rows operation_window_key values must be unique")
    return normalized


def _normalize_signal_config_versions(value: object) -> tuple[tuple[str, str], ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("signal_config_versions must contain pairs")
    try:
        normalized = tuple(tuple(item) for item in value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("signal_config_versions must contain pairs") from exc
    seen: set[str] = set()
    for item in normalized:
        if len(item) != 2:
            raise ValueError("signal_config_versions must contain pairs")
        signal_key, config_version = item
        _require_public_string("signal_config_versions signal_key", signal_key)
        _require_canonical_string(
            "signal_config_versions config_version",
            config_version,
        )
        if signal_key in seen:
            raise ValueError("signal_config_versions signal keys must be unique")
        seen.add(signal_key)
    if normalized != tuple(sorted(normalized)):
        raise ValueError("signal_config_versions must be sorted")
    return normalized


def _normalize_reason_code_counts(
    value: object,
) -> tuple[MarketResearchRatesTreasuryBuybackLiquidityDigestReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must contain reason code counts")
    try:
        normalized = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_code_counts must contain reason code counts") from exc
    for item in normalized:
        if (
            type(item)
            is not MarketResearchRatesTreasuryBuybackLiquidityDigestReasonCodeCount
        ):
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchRatesTreasuryBuybackLiquidityDigestReasonCodeCount",
            )
        _require_hard_flags("reason_code_counts", item)
    if normalized != tuple(
        sorted(normalized, key=lambda item: REASON_CODE_SEQUENCE.index(item.reason_code)),
    ):
        raise ValueError("reason_code_counts must be sorted by reason code sequence")
    return normalized


def _normalize_reason_codes(
    value: object,
    *,
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must contain reason code strings")
    try:
        normalized = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_codes must contain reason code strings") from exc
    for reason_code in normalized:
        _require_reason_code("reason_code", reason_code)
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    sequence_index = {reason_code: index for index, reason_code in enumerate(sequence)}
    if normalized and normalized != tuple(
        sorted(normalized, key=lambda reason_code: sequence_index[reason_code]),
    ):
        raise ValueError("reason_codes must be sorted")
    return normalized


def _age_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    with localcontext(DECIMAL_CONTEXT):
        seconds = Decimal(delta.days * 86400 + delta.seconds)
        micros = Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
        return _quantize(seconds + micros)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _decimal_sum(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("values must be Decimals")
        if not value.is_finite():
            raise ValueError("values must be finite")
        total += value
    return _quantize(total)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _absolute_decimal_difference(left: Decimal, right: Decimal) -> Decimal:
    return _quantize(abs(left - right))


def _nonnegative_decimal_difference(left: Decimal, right: Decimal) -> Decimal:
    return max(ZERO, _quantize(left - right))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _row_sort_value(row: MarketResearchRatesTreasuryBuybackLiquidityDigestRow) -> int:
    if row.digest_status == STATUS_BLOCKED:
        return 0
    if row.digest_status == STATUS_WATCH:
        return 1
    return 2


def _redacted_reference(value: str) -> str:
    if _is_text_safe(value):
        return value
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()[:12]}"


def _is_text_safe(value: str) -> bool:
    lowered = value.lower()
    return not any(fragment in lowered for fragment in UNSAFE_REFERENCE_FRAGMENTS)


def _json_ready(value: object) -> Any:
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exact")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return format(value, "f")
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be exact")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, object] = {}
        for item_key, item in value.items():
            if type(item_key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[item_key] = _json_ready(item)
        return ready
    if isinstance(value, (str, bool)) or value is None:
        return value
    raise ValueError("value is not JSON serializable")


def _require_redacted_reference(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value.startswith("sha256:"):
        digest = value.removeprefix("sha256:")
        if len(digest) != 12 or not all(
            character in "0123456789abcdef" for character in digest
        ):
            raise ValueError(f"{field_name} must be a redacted reference")
        return
    if not _is_text_safe(value):
        raise ValueError(f"{field_name} must be redacted")


def _require_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must contain a known digest status")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must contain a known reason code")


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if not _is_text_safe(value):
        raise ValueError(f"{field_name} must be public safe")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")
