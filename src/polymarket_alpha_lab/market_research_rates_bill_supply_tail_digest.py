"""Pure Phase 1 rates bill supply tail research reducer."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, date, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_MARKET_RESEARCH_RATES_BILL_SUPPLY_TAIL_DIGEST_CONFIG_VERSION = (
    "market-research-rates-bill-supply-tail-digest-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
DIGEST_STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCKED)

NO_INPUTS_REASON = "market_research_rates_bill_supply_tail_digest_no_inputs"
PASS_REASON = "market_research_rates_bill_supply_tail_digest_pass"
STALE_SOURCE_REASON = "market_research_rates_bill_supply_tail_digest_stale_source"
LOW_SUPPLY_SURPRISE_REASON = (
    "market_research_rates_bill_supply_tail_digest_low_supply_surprise"
)
LOW_TAIL_REASON = "market_research_rates_bill_supply_tail_digest_low_tail"
BID_TO_COVER_GAP_REASON = (
    "market_research_rates_bill_supply_tail_digest_bid_to_cover_gap"
)
TAKEDOWN_SHIFT_GAP_REASON = (
    "market_research_rates_bill_supply_tail_digest_takedown_shift_gap"
)
TGA_PAYDOWN_GAP_REASON = (
    "market_research_rates_bill_supply_tail_digest_tga_paydown_gap"
)
REPO_SPECIALNESS_GAP_REASON = (
    "market_research_rates_bill_supply_tail_digest_repo_specialness_gap"
)
UPSTREAM_REASON_GAP_REASON = (
    "market_research_rates_bill_supply_tail_digest_upstream_reason_gap"
)

REASON_CODE_SEQUENCE = (
    STALE_SOURCE_REASON,
    LOW_SUPPLY_SURPRISE_REASON,
    LOW_TAIL_REASON,
    BID_TO_COVER_GAP_REASON,
    TAKEDOWN_SHIFT_GAP_REASON,
    TGA_PAYDOWN_GAP_REASON,
    REPO_SPECIALNESS_GAP_REASON,
    UPSTREAM_REASON_GAP_REASON,
    PASS_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    STALE_SOURCE_REASON,
    LOW_SUPPLY_SURPRISE_REASON,
    LOW_TAIL_REASON,
    BID_TO_COVER_GAP_REASON,
    TAKEDOWN_SHIFT_GAP_REASON,
    TGA_PAYDOWN_GAP_REASON,
    REPO_SPECIALNESS_GAP_REASON,
    UPSTREAM_REASON_GAP_REASON,
    PASS_REASON,
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")

__all__ = (
    "DEFAULT_MARKET_RESEARCH_RATES_BILL_SUPPLY_TAIL_DIGEST_CONFIG_VERSION",
    "MarketResearchRatesBillSupplyTailDigestConfig",
    "MarketResearchRatesBillSupplyTailDigestReasonCodeCount",
    "MarketResearchRatesBillSupplyTailDigestReport",
    "MarketResearchRatesBillSupplyTailDigestRow",
    "MarketResearchRatesBillSupplyTailDigestSignal",
    "build_market_research_rates_bill_supply_tail_digest",
    "market_research_rates_bill_supply_tail_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchRatesBillSupplyTailDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_RATES_BILL_SUPPLY_TAIL_DIGEST_CONFIG_VERSION
    )
    max_source_age_seconds: Decimal = Decimal("7200.000000")
    min_announced_supply_surprise_billion: Decimal = Decimal("10.000000")
    min_tail_bps: Decimal = Decimal("1.500000")
    max_bid_to_cover_delta: Decimal = Decimal("-0.050000")
    max_indirect_takedown_delta: Decimal = Decimal("-0.020000")
    min_direct_takedown_delta: Decimal = Decimal("0.020000")
    min_tga_paydown_pressure_billion: Decimal = Decimal("20.000000")
    min_repo_specialness_proxy_bps: Decimal = Decimal("5.000000")
    min_upstream_reason_code_count: Decimal = Decimal("2.000000")
    risk_penalty_per_gap: Decimal = Decimal("0.100000")
    blocked_risk_threshold: Decimal = Decimal("0.500000")
    watch_risk_threshold: Decimal = Decimal("0.650000")
    pass_risk_threshold: Decimal = Decimal("0.800000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchRatesBillSupplyTailDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchRatesBillSupplyTailDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "max_source_age_seconds",
            "min_upstream_reason_code_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.max_source_age_seconds <= ZERO:
            raise ValueError("max_source_age_seconds must be positive")
        if self.min_upstream_reason_code_count <= ZERO:
            raise ValueError("min_upstream_reason_code_count must be positive")
        for field_name in (
            "min_announced_supply_surprise_billion",
            "min_tail_bps",
            "max_bid_to_cover_delta",
            "max_indirect_takedown_delta",
            "min_direct_takedown_delta",
            "min_tga_paydown_pressure_billion",
            "min_repo_specialness_proxy_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_measure_decimal(field_name, getattr(self, field_name)),
            )
        if self.max_bid_to_cover_delta >= ZERO:
            raise ValueError("max_bid_to_cover_delta must be below zero")
        if self.max_indirect_takedown_delta >= ZERO:
            raise ValueError("max_indirect_takedown_delta must be below zero")
        for field_name in (
            "min_tail_bps",
            "min_direct_takedown_delta",
            "min_repo_specialness_proxy_bps",
        ):
            if getattr(self, field_name) <= ZERO:
                raise ValueError(f"{field_name} must be positive")
        for field_name in (
            "risk_penalty_per_gap",
            "blocked_risk_threshold",
            "watch_risk_threshold",
            "pass_risk_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if not (
            self.blocked_risk_threshold
            < self.watch_risk_threshold
            < self.pass_risk_threshold
        ):
            raise ValueError("risk thresholds must be ascending")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchRatesBillSupplyTailDigestSignal:
    condition_id: str
    market_slug: str
    tenor: str
    auction_date: date
    source_timestamp: datetime
    announced_supply_surprise_billion: Decimal
    tail_bps: Decimal
    bid_to_cover_delta: Decimal
    indirect_takedown_delta: Decimal
    direct_takedown_delta: Decimal
    tga_paydown_pressure_billion: Decimal
    repo_specialness_proxy_bps: Decimal
    base_risk_score: Decimal
    upstream_reason_codes: tuple[str, ...]
    signal_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchRatesBillSupplyTailDigestSignal:
            raise ValueError(
                "signal must be exactly "
                "MarketResearchRatesBillSupplyTailDigestSignal",
            )
        for field_name in (
            "condition_id",
            "market_slug",
            "tenor",
            "signal_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "auction_date",
            _as_date("auction_date", self.auction_date),
        )
        object.__setattr__(
            self,
            "source_timestamp",
            _as_utc("source_timestamp", self.source_timestamp),
        )
        for field_name in (
            "announced_supply_surprise_billion",
            "tail_bps",
            "bid_to_cover_delta",
            "indirect_takedown_delta",
            "direct_takedown_delta",
            "tga_paydown_pressure_billion",
            "repo_specialness_proxy_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_measure_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "tail_bps",
            "repo_specialness_proxy_bps",
        ):
            if getattr(self, field_name) < ZERO:
                raise ValueError(f"{field_name} must be nonnegative")
        object.__setattr__(
            self,
            "base_risk_score",
            _require_ratio_decimal("base_risk_score", self.base_risk_score),
        )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_public_strings(
                "upstream_reason_codes",
                self.upstream_reason_codes,
            ),
        )
        _require_hard_flags("signal", self)


@dataclass(frozen=True)
class MarketResearchRatesBillSupplyTailDigestRow:
    condition_id: str
    market_slug: str
    tenor: str
    auction_date: date
    source_timestamp: datetime
    source_age_seconds: Decimal
    announced_supply_surprise_billion: Decimal
    tail_bps: Decimal
    bid_to_cover_delta: Decimal
    indirect_takedown_delta: Decimal
    direct_takedown_delta: Decimal
    tga_paydown_pressure_billion: Decimal
    repo_specialness_proxy_bps: Decimal
    base_risk_score: Decimal
    gap_penalty_score: Decimal
    final_risk_score: Decimal
    digest_status: str
    upstream_reason_codes: tuple[str, ...]
    signal_config_version: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchRatesBillSupplyTailDigestRow:
            raise ValueError("row must be exactly MarketResearchRatesBillSupplyTailDigestRow")
        for field_name in (
            "condition_id",
            "market_slug",
            "tenor",
            "signal_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "auction_date",
            _as_date("auction_date", self.auction_date),
        )
        object.__setattr__(
            self,
            "source_timestamp",
            _as_utc("source_timestamp", self.source_timestamp),
        )
        object.__setattr__(
            self,
            "source_age_seconds",
            _require_nonnegative_count_decimal(
                "source_age_seconds",
                self.source_age_seconds,
            ),
        )
        for field_name in (
            "announced_supply_surprise_billion",
            "tail_bps",
            "bid_to_cover_delta",
            "indirect_takedown_delta",
            "direct_takedown_delta",
            "tga_paydown_pressure_billion",
            "repo_specialness_proxy_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_measure_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "base_risk_score",
            "gap_penalty_score",
            "final_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("digest_status", self.digest_status, DIGEST_STATUSES)
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_public_strings(
                "upstream_reason_codes",
                self.upstream_reason_codes,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                self.reason_codes,
                sequence=ROW_REASON_CODE_SEQUENCE,
            ),
        )
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchRatesBillSupplyTailDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    signal_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchRatesBillSupplyTailDigestReasonCodeCount:
            raise ValueError(
                "reason_code_count must be exactly "
                "MarketResearchRatesBillSupplyTailDigestReasonCodeCount",
            )
        _require_member("reason_code", self.reason_code, ROW_REASON_CODE_SEQUENCE)
        if self.reason_code == PASS_REASON:
            raise ValueError("reason_code must identify a gap")
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        if self.count <= ZERO:
            raise ValueError("count must be positive")
        object.__setattr__(
            self,
            "signal_ratio",
            _require_ratio_decimal("signal_ratio", self.signal_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchRatesBillSupplyTailDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    signal_count: Decimal
    pass_signal_count: Decimal
    watch_signal_count: Decimal
    blocked_signal_count: Decimal
    stale_source_signal_count: Decimal
    low_supply_surprise_signal_count: Decimal
    low_tail_signal_count: Decimal
    bid_to_cover_gap_signal_count: Decimal
    takedown_shift_gap_signal_count: Decimal
    tga_paydown_gap_signal_count: Decimal
    repo_specialness_gap_signal_count: Decimal
    upstream_reason_gap_signal_count: Decimal
    total_gap_penalty_score: Decimal
    average_final_risk_score: Decimal
    max_final_risk_score: Decimal
    risk_score: Decimal
    average_announced_supply_surprise_billion: Decimal
    average_tail_bps: Decimal
    average_bid_to_cover_delta: Decimal
    average_indirect_takedown_delta: Decimal
    average_direct_takedown_delta: Decimal
    average_tga_paydown_pressure_billion: Decimal
    average_repo_specialness_proxy_bps: Decimal
    max_source_age_seconds: Decimal
    min_announced_supply_surprise_billion: Decimal
    min_tail_bps: Decimal
    max_bid_to_cover_delta: Decimal
    max_indirect_takedown_delta: Decimal
    min_direct_takedown_delta: Decimal
    min_tga_paydown_pressure_billion: Decimal
    min_repo_specialness_proxy_bps: Decimal
    min_upstream_reason_code_count: Decimal
    blocked_risk_threshold: Decimal
    watch_risk_threshold: Decimal
    pass_risk_threshold: Decimal
    max_observed_source_age_seconds: Decimal
    rows: tuple[MarketResearchRatesBillSupplyTailDigestRow, ...]
    signal_config_versions: tuple[tuple[str, str], ...]
    upstream_reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        MarketResearchRatesBillSupplyTailDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchRatesBillSupplyTailDigestReport:
            raise ValueError(
                "report must be exactly MarketResearchRatesBillSupplyTailDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_member("digest_status", self.digest_status, DIGEST_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "signal_count",
            "pass_signal_count",
            "watch_signal_count",
            "blocked_signal_count",
            "stale_source_signal_count",
            "low_supply_surprise_signal_count",
            "low_tail_signal_count",
            "bid_to_cover_gap_signal_count",
            "takedown_shift_gap_signal_count",
            "tga_paydown_gap_signal_count",
            "repo_specialness_gap_signal_count",
            "upstream_reason_gap_signal_count",
            "max_source_age_seconds",
            "min_upstream_reason_code_count",
            "max_observed_source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "total_gap_penalty_score",
            "average_final_risk_score",
            "max_final_risk_score",
            "risk_score",
            "blocked_risk_threshold",
            "watch_risk_threshold",
            "pass_risk_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_announced_supply_surprise_billion",
            "average_tail_bps",
            "average_bid_to_cover_delta",
            "average_indirect_takedown_delta",
            "average_direct_takedown_delta",
            "average_tga_paydown_pressure_billion",
            "average_repo_specialness_proxy_bps",
            "min_announced_supply_surprise_billion",
            "min_tail_bps",
            "max_bid_to_cover_delta",
            "max_indirect_takedown_delta",
            "min_direct_takedown_delta",
            "min_tga_paydown_pressure_billion",
            "min_repo_specialness_proxy_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_measure_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "signal_config_versions",
            _normalize_signal_config_versions(self.signal_config_versions),
        )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_public_strings(
                "upstream_reason_codes",
                self.upstream_reason_codes,
            ),
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


def build_market_research_rates_bill_supply_tail_digest(
    signals: Iterable[MarketResearchRatesBillSupplyTailDigestSignal],
    *,
    config: MarketResearchRatesBillSupplyTailDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchRatesBillSupplyTailDigestReport:
    cfg = config or MarketResearchRatesBillSupplyTailDigestConfig()
    if type(cfg) is not MarketResearchRatesBillSupplyTailDigestConfig:
        raise ValueError(
            "config must be exactly MarketResearchRatesBillSupplyTailDigestConfig",
        )
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_signals = _normalize_signals(signals)
    rows = tuple(
        _row_for_signal(signal, config=cfg, generated_at=generated_at_utc)
        for signal in normalized_signals
    )
    sorted_rows = _sorted_rows(rows)
    report_status = _report_status(sorted_rows)
    row_count = _decimal_count(len(sorted_rows))
    return MarketResearchRatesBillSupplyTailDigestReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        digest_status=report_status,
        recommended_next_step=_recommended_next_step(report_status),
        signal_count=row_count,
        pass_signal_count=_status_count(sorted_rows, STATUS_PASS),
        watch_signal_count=_status_count(sorted_rows, STATUS_WATCH),
        blocked_signal_count=_status_count(sorted_rows, STATUS_BLOCKED),
        stale_source_signal_count=_reason_signal_count(sorted_rows, STALE_SOURCE_REASON),
        low_supply_surprise_signal_count=_reason_signal_count(
            sorted_rows,
            LOW_SUPPLY_SURPRISE_REASON,
        ),
        low_tail_signal_count=_reason_signal_count(sorted_rows, LOW_TAIL_REASON),
        bid_to_cover_gap_signal_count=_reason_signal_count(
            sorted_rows,
            BID_TO_COVER_GAP_REASON,
        ),
        takedown_shift_gap_signal_count=_reason_signal_count(
            sorted_rows,
            TAKEDOWN_SHIFT_GAP_REASON,
        ),
        tga_paydown_gap_signal_count=_reason_signal_count(
            sorted_rows,
            TGA_PAYDOWN_GAP_REASON,
        ),
        repo_specialness_gap_signal_count=_reason_signal_count(
            sorted_rows,
            REPO_SPECIALNESS_GAP_REASON,
        ),
        upstream_reason_gap_signal_count=_reason_signal_count(
            sorted_rows,
            UPSTREAM_REASON_GAP_REASON,
        ),
        total_gap_penalty_score=_decimal_sum(
            row.gap_penalty_score for row in sorted_rows
        ),
        average_final_risk_score=_ratio(
            _decimal_sum(row.final_risk_score for row in sorted_rows),
            row_count,
        ),
        max_final_risk_score=max(
            (row.final_risk_score for row in sorted_rows),
            default=ZERO,
        ),
        risk_score=max(
            (row.final_risk_score for row in sorted_rows),
            default=ZERO,
        ),
        average_announced_supply_surprise_billion=_ratio(
            _decimal_sum(
                row.announced_supply_surprise_billion for row in sorted_rows
            ),
            row_count,
        ),
        average_tail_bps=_ratio(
            _decimal_sum(row.tail_bps for row in sorted_rows),
            row_count,
        ),
        average_bid_to_cover_delta=_ratio(
            _decimal_sum(row.bid_to_cover_delta for row in sorted_rows),
            row_count,
        ),
        average_indirect_takedown_delta=_ratio(
            _decimal_sum(row.indirect_takedown_delta for row in sorted_rows),
            row_count,
        ),
        average_direct_takedown_delta=_ratio(
            _decimal_sum(row.direct_takedown_delta for row in sorted_rows),
            row_count,
        ),
        average_tga_paydown_pressure_billion=_ratio(
            _decimal_sum(row.tga_paydown_pressure_billion for row in sorted_rows),
            row_count,
        ),
        average_repo_specialness_proxy_bps=_ratio(
            _decimal_sum(row.repo_specialness_proxy_bps for row in sorted_rows),
            row_count,
        ),
        max_source_age_seconds=cfg.max_source_age_seconds,
        min_announced_supply_surprise_billion=cfg.min_announced_supply_surprise_billion,
        min_tail_bps=cfg.min_tail_bps,
        max_bid_to_cover_delta=cfg.max_bid_to_cover_delta,
        max_indirect_takedown_delta=cfg.max_indirect_takedown_delta,
        min_direct_takedown_delta=cfg.min_direct_takedown_delta,
        min_tga_paydown_pressure_billion=cfg.min_tga_paydown_pressure_billion,
        min_repo_specialness_proxy_bps=cfg.min_repo_specialness_proxy_bps,
        min_upstream_reason_code_count=cfg.min_upstream_reason_code_count,
        blocked_risk_threshold=cfg.blocked_risk_threshold,
        watch_risk_threshold=cfg.watch_risk_threshold,
        pass_risk_threshold=cfg.pass_risk_threshold,
        max_observed_source_age_seconds=max(
            (row.source_age_seconds for row in sorted_rows),
            default=ZERO,
        ),
        rows=sorted_rows,
        signal_config_versions=tuple(
            sorted(
                (
                    signal.market_slug,
                    signal.signal_config_version,
                )
                for signal in normalized_signals
            ),
        ),
        upstream_reason_codes=_upstream_reason_codes(sorted_rows),
        reason_code_counts=_reason_code_counts(sorted_rows),
        reason_codes=_summary_reason_codes(sorted_rows),
    )


def market_research_rates_bill_supply_tail_digest_payload(
    report: MarketResearchRatesBillSupplyTailDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchRatesBillSupplyTailDigestReport:
        raise ValueError(
            "report must be exactly MarketResearchRatesBillSupplyTailDigestReport",
        )
    return _json_ready(asdict(report))


def _row_for_signal(
    signal: MarketResearchRatesBillSupplyTailDigestSignal,
    *,
    config: MarketResearchRatesBillSupplyTailDigestConfig,
    generated_at: datetime,
) -> MarketResearchRatesBillSupplyTailDigestRow:
    if signal.source_timestamp > generated_at:
        raise ValueError("source_timestamp must not be in the future")
    source_age_seconds = _age_seconds(generated_at, signal.source_timestamp)
    reason_codes = _row_reason_codes(
        signal=signal,
        config=config,
        source_age_seconds=source_age_seconds,
    )
    gap_penalty_score = _gap_penalty_score(reason_codes, config=config)
    final_risk_score = _final_risk_score(signal.base_risk_score, gap_penalty_score)
    return MarketResearchRatesBillSupplyTailDigestRow(
        condition_id=signal.condition_id,
        market_slug=signal.market_slug,
        tenor=signal.tenor,
        auction_date=signal.auction_date,
        source_timestamp=signal.source_timestamp,
        source_age_seconds=source_age_seconds,
        announced_supply_surprise_billion=signal.announced_supply_surprise_billion,
        tail_bps=signal.tail_bps,
        bid_to_cover_delta=signal.bid_to_cover_delta,
        indirect_takedown_delta=signal.indirect_takedown_delta,
        direct_takedown_delta=signal.direct_takedown_delta,
        tga_paydown_pressure_billion=signal.tga_paydown_pressure_billion,
        repo_specialness_proxy_bps=signal.repo_specialness_proxy_bps,
        base_risk_score=signal.base_risk_score,
        gap_penalty_score=gap_penalty_score,
        final_risk_score=final_risk_score,
        digest_status=_row_status(
            reason_codes,
            final_risk_score=final_risk_score,
            config=config,
        ),
        upstream_reason_codes=signal.upstream_reason_codes,
        signal_config_version=signal.signal_config_version,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    signal: MarketResearchRatesBillSupplyTailDigestSignal,
    config: MarketResearchRatesBillSupplyTailDigestConfig,
    source_age_seconds: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if source_age_seconds > config.max_source_age_seconds:
        reasons.append(STALE_SOURCE_REASON)
    if (
        signal.announced_supply_surprise_billion
        < config.min_announced_supply_surprise_billion
    ):
        reasons.append(LOW_SUPPLY_SURPRISE_REASON)
    if signal.tail_bps < config.min_tail_bps:
        reasons.append(LOW_TAIL_REASON)
    if signal.bid_to_cover_delta > config.max_bid_to_cover_delta:
        reasons.append(BID_TO_COVER_GAP_REASON)
    if (
        signal.indirect_takedown_delta > config.max_indirect_takedown_delta
        or signal.direct_takedown_delta < config.min_direct_takedown_delta
    ):
        reasons.append(TAKEDOWN_SHIFT_GAP_REASON)
    if signal.tga_paydown_pressure_billion < config.min_tga_paydown_pressure_billion:
        reasons.append(TGA_PAYDOWN_GAP_REASON)
    if signal.repo_specialness_proxy_bps < config.min_repo_specialness_proxy_bps:
        reasons.append(REPO_SPECIALNESS_GAP_REASON)
    if (
        _decimal_count(len(signal.upstream_reason_codes))
        < config.min_upstream_reason_code_count
    ):
        reasons.append(UPSTREAM_REASON_GAP_REASON)
    if not reasons:
        reasons.append(PASS_REASON)
    return tuple(reason for reason in ROW_REASON_CODE_SEQUENCE if reason in reasons)


def _gap_penalty_score(
    reason_codes: tuple[str, ...],
    *,
    config: MarketResearchRatesBillSupplyTailDigestConfig,
) -> Decimal:
    gap_count = sum(1 for reason in reason_codes if reason != PASS_REASON)
    return min(
        ONE,
        _quantize(config.risk_penalty_per_gap * _decimal_count(gap_count)),
    )


def _final_risk_score(
    base_risk_score: Decimal,
    gap_penalty_score: Decimal,
) -> Decimal:
    return max(ZERO, _quantize(base_risk_score - gap_penalty_score))


def _row_status(
    reason_codes: tuple[str, ...],
    *,
    final_risk_score: Decimal,
    config: MarketResearchRatesBillSupplyTailDigestConfig,
) -> str:
    if reason_codes == (PASS_REASON,) and final_risk_score >= config.pass_risk_threshold:
        return STATUS_PASS
    if final_risk_score < config.blocked_risk_threshold:
        return STATUS_BLOCKED
    if final_risk_score >= config.watch_risk_threshold:
        return STATUS_WATCH
    return STATUS_BLOCKED


def _sorted_rows(
    rows: Iterable[MarketResearchRatesBillSupplyTailDigestRow],
) -> tuple[MarketResearchRatesBillSupplyTailDigestRow, ...]:
    status_weight = {STATUS_BLOCKED: 0, STATUS_WATCH: 1, STATUS_PASS: 2}
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                status_weight[row.digest_status],
                row.final_risk_score,
                row.market_slug,
                row.condition_id,
            ),
        ),
    )


def _report_status(rows: tuple[MarketResearchRatesBillSupplyTailDigestRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _recommended_next_step(status: str) -> str:
    if status == STATUS_PASS:
        return "allow_report_only_market_research_rates_bill_supply_tail_digest"
    if status == STATUS_WATCH:
        return "review_report_only_market_research_rates_bill_supply_tail_digest"
    return "block_report_only_market_research_rates_bill_supply_tail_digest"


def _summary_reason_codes(
    rows: tuple[MarketResearchRatesBillSupplyTailDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    reasons = {
        reason
        for row in rows
        for reason in row.reason_codes
        if reason != PASS_REASON
    }
    if not reasons:
        return (PASS_REASON,)
    return tuple(reason for reason in REASON_CODE_SEQUENCE if reason in reasons)


def _reason_code_counts(
    rows: tuple[MarketResearchRatesBillSupplyTailDigestRow, ...],
) -> tuple[MarketResearchRatesBillSupplyTailDigestReasonCodeCount, ...]:
    signal_count = _decimal_count(len(rows))
    counter: Counter[str] = Counter(
        reason
        for row in rows
        for reason in row.reason_codes
        if reason != PASS_REASON
    )
    return tuple(
        MarketResearchRatesBillSupplyTailDigestReasonCodeCount(
            reason_code=reason,
            count=_decimal_count(counter[reason]),
            signal_ratio=_ratio(_decimal_count(counter[reason]), signal_count),
        )
        for reason in REASON_CODE_SEQUENCE
        if reason in counter
    )


def _upstream_reason_codes(
    rows: tuple[MarketResearchRatesBillSupplyTailDigestRow, ...],
) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                reason
                for row in rows
                for reason in row.upstream_reason_codes
            },
        ),
    )


def _status_count(
    rows: tuple[MarketResearchRatesBillSupplyTailDigestRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.digest_status == status))


def _reason_signal_count(
    rows: tuple[MarketResearchRatesBillSupplyTailDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _normalize_signals(
    value: Iterable[MarketResearchRatesBillSupplyTailDigestSignal],
) -> tuple[MarketResearchRatesBillSupplyTailDigestSignal, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("signals must be an iterable")
    try:
        signals = tuple(value)
    except TypeError as exc:
        raise ValueError("signals must be an iterable") from exc
    seen: set[str] = set()
    for signal in signals:
        if type(signal) is not MarketResearchRatesBillSupplyTailDigestSignal:
            raise ValueError(
                "signals must contain "
                "MarketResearchRatesBillSupplyTailDigestSignal values",
            )
        _require_hard_flags("signals", signal)
        if signal.condition_id in seen:
            raise ValueError("signals condition_id values must be unique")
        seen.add(signal.condition_id)
    return signals


def _normalize_rows(
    value: tuple[MarketResearchRatesBillSupplyTailDigestRow, ...],
) -> tuple[MarketResearchRatesBillSupplyTailDigestRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not MarketResearchRatesBillSupplyTailDigestRow:
            raise ValueError(
                "rows must contain MarketResearchRatesBillSupplyTailDigestRow values",
            )
        _require_hard_flags("rows", row)
        if row.condition_id in seen:
            raise ValueError("rows condition_id values must be unique")
        seen.add(row.condition_id)
    if rows != _sorted_rows(rows):
        raise ValueError("rows must use deterministic sequence")
    return rows


def _normalize_signal_config_versions(
    value: tuple[tuple[str, str], ...],
) -> tuple[tuple[str, str], ...]:
    if type(value) not in (list, tuple):
        raise ValueError("signal_config_versions must be a list or tuple")
    pairs = tuple(value)
    seen: set[tuple[str, str]] = set()
    for pair in pairs:
        if type(pair) not in (list, tuple) or len(pair) != 2:
            raise ValueError("signal_config_versions must contain pairs")
        key, version = pair
        _require_public_string("signal_config_versions key", key)
        _require_public_string("signal_config_versions version", version)
        normalized_pair = (key, version)
        if normalized_pair in seen:
            raise ValueError("signal_config_versions values must be unique")
        seen.add(normalized_pair)
    if pairs != tuple(sorted(pairs)):
        raise ValueError("signal_config_versions must use canonical sequence")
    return tuple((key, version) for key, version in pairs)


def _normalize_reason_code_counts(
    value: tuple[MarketResearchRatesBillSupplyTailDigestReasonCodeCount, ...],
) -> tuple[MarketResearchRatesBillSupplyTailDigestReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(value)
    seen: set[str] = set()
    for item in counts:
        if type(item) is not MarketResearchRatesBillSupplyTailDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchRatesBillSupplyTailDigestReasonCodeCount values",
            )
        _require_hard_flags("reason_code_counts", item)
        if item.reason_code in seen:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen.add(item.reason_code)
    canonical = tuple(reason for reason in REASON_CODE_SEQUENCE if reason in seen)
    if tuple(item.reason_code for item in counts) != canonical:
        raise ValueError("reason_code_counts must use canonical sequence")
    return counts


def _normalize_reason_codes(
    value: tuple[str, ...],
    *,
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reasons = tuple(value)
    seen: set[str] = set()
    for reason in reasons:
        _require_member("reason_code", reason, sequence)
        if reason in seen:
            raise ValueError("reason_codes values must be unique")
        seen.add(reason)
    canonical = tuple(reason for reason in sequence if reason in seen)
    if reasons != canonical:
        raise ValueError("reason_codes must use canonical sequence")
    return reasons


def _normalize_public_strings(
    field_name: str,
    value: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    values = tuple(value)
    seen: set[str] = set()
    for item in values:
        _require_public_string(field_name, item)
        if item in seen:
            raise ValueError(f"{field_name} values must be unique")
        seen.add(item)
    canonical = tuple(sorted(values))
    if values != canonical:
        raise ValueError(f"{field_name} must use canonical sequence")
    return values


def _validate_report(report: MarketResearchRatesBillSupplyTailDigestReport) -> None:
    rows = report.rows
    if report.signal_count != _decimal_count(len(rows)):
        raise ValueError("signal_count must match rows")
    checks = (
        ("pass_signal_count", report.pass_signal_count, _status_count(rows, STATUS_PASS)),
        ("watch_signal_count", report.watch_signal_count, _status_count(rows, STATUS_WATCH)),
        (
            "blocked_signal_count",
            report.blocked_signal_count,
            _status_count(rows, STATUS_BLOCKED),
        ),
        (
            "stale_source_signal_count",
            report.stale_source_signal_count,
            _reason_signal_count(rows, STALE_SOURCE_REASON),
        ),
        (
            "low_supply_surprise_signal_count",
            report.low_supply_surprise_signal_count,
            _reason_signal_count(rows, LOW_SUPPLY_SURPRISE_REASON),
        ),
        (
            "low_tail_signal_count",
            report.low_tail_signal_count,
            _reason_signal_count(rows, LOW_TAIL_REASON),
        ),
        (
            "bid_to_cover_gap_signal_count",
            report.bid_to_cover_gap_signal_count,
            _reason_signal_count(rows, BID_TO_COVER_GAP_REASON),
        ),
        (
            "takedown_shift_gap_signal_count",
            report.takedown_shift_gap_signal_count,
            _reason_signal_count(rows, TAKEDOWN_SHIFT_GAP_REASON),
        ),
        (
            "tga_paydown_gap_signal_count",
            report.tga_paydown_gap_signal_count,
            _reason_signal_count(rows, TGA_PAYDOWN_GAP_REASON),
        ),
        (
            "repo_specialness_gap_signal_count",
            report.repo_specialness_gap_signal_count,
            _reason_signal_count(rows, REPO_SPECIALNESS_GAP_REASON),
        ),
        (
            "upstream_reason_gap_signal_count",
            report.upstream_reason_gap_signal_count,
            _reason_signal_count(rows, UPSTREAM_REASON_GAP_REASON),
        ),
    )
    for field_name, actual, expected in checks:
        if actual != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.total_gap_penalty_score != _decimal_sum(
        row.gap_penalty_score for row in rows
    ):
        raise ValueError("total_gap_penalty_score must match rows")
    row_count = _decimal_count(len(rows))
    if report.average_final_risk_score != _ratio(
        _decimal_sum(row.final_risk_score for row in rows),
        row_count,
    ):
        raise ValueError("average_final_risk_score must match rows")
    if report.max_final_risk_score != max(
        (row.final_risk_score for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_final_risk_score must match rows")
    if report.risk_score != report.max_final_risk_score:
        raise ValueError("risk_score must match rows")
    if report.average_announced_supply_surprise_billion != _ratio(
        _decimal_sum(row.announced_supply_surprise_billion for row in rows),
        row_count,
    ):
        raise ValueError("average_announced_supply_surprise_billion must match rows")
    if report.average_tail_bps != _ratio(
        _decimal_sum(row.tail_bps for row in rows),
        row_count,
    ):
        raise ValueError("average_tail_bps must match rows")
    if report.average_bid_to_cover_delta != _ratio(
        _decimal_sum(row.bid_to_cover_delta for row in rows),
        row_count,
    ):
        raise ValueError("average_bid_to_cover_delta must match rows")
    if report.average_indirect_takedown_delta != _ratio(
        _decimal_sum(row.indirect_takedown_delta for row in rows),
        row_count,
    ):
        raise ValueError("average_indirect_takedown_delta must match rows")
    if report.average_direct_takedown_delta != _ratio(
        _decimal_sum(row.direct_takedown_delta for row in rows),
        row_count,
    ):
        raise ValueError("average_direct_takedown_delta must match rows")
    if report.average_tga_paydown_pressure_billion != _ratio(
        _decimal_sum(row.tga_paydown_pressure_billion for row in rows),
        row_count,
    ):
        raise ValueError("average_tga_paydown_pressure_billion must match rows")
    if report.average_repo_specialness_proxy_bps != _ratio(
        _decimal_sum(row.repo_specialness_proxy_bps for row in rows),
        row_count,
    ):
        raise ValueError("average_repo_specialness_proxy_bps must match rows")
    if report.max_observed_source_age_seconds != max(
        (row.source_age_seconds for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_observed_source_age_seconds must match rows")
    if report.upstream_reason_codes != _upstream_reason_codes(rows):
        raise ValueError("upstream_reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != _summary_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.digest_status != _report_status(rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step must match digest_status")


def _age_seconds(generated_at: datetime, source_timestamp: datetime) -> Decimal:
    delta = generated_at - source_timestamp
    total_microseconds = (
        Decimal(delta.days * 86400 + delta.seconds) * MICROSECONDS_PER_SECOND
        + Decimal(delta.microseconds)
    )
    return _quantize(total_microseconds / MICROSECONDS_PER_SECOND)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_date(field_name: str, value: date) -> date:
    if type(value) is not date:
        raise ValueError(f"{field_name} must be a date")
    return value


def _require_public_string(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    if any(ord(character) < 32 for character in value):
        raise ValueError(f"{field_name} must be printable")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if value != value.strip():
        raise ValueError(f"{field_name} must be canonical")


def _require_member(field_name: str, value: str, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must be one of the canonical values")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} {flag_name} must be True")


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    return _quantize(value)


def _require_measure_decimal(field_name: str, value: Decimal) -> Decimal:
    return _require_decimal(field_name, value)


def _require_nonnegative_count_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _decimal_sum(values: Iterable[Decimal]) -> Decimal:
    return _quantize(sum(values, ZERO))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if type(value) is datetime:
        return value.isoformat()
    if type(value) is date:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    return value
