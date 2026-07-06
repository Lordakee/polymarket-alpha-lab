"""Pure Phase 1 crypto ETF creation/redemption stress reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from types import MappingProxyType
from typing import Any


DEFAULT_MARKET_RESEARCH_CRYPTO_ETF_CREATION_REDEMPTION_STRESS_DIGEST_CONFIG_VERSION = (
    "market-research-crypto-etf-creation-redemption-stress-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

BASE_REASON = "market_research_crypto_etf_creation_redemption_stress_digest_"
READY_REASON = BASE_REASON + "ready"
NO_INPUTS_REASON = BASE_REASON + "no_inputs"
REDEMPTION_PRESSURE_USD_REASON = BASE_REASON + "redemption_pressure_usd"
REDEMPTION_PRESSURE_RATIO_REASON = BASE_REASON + "redemption_pressure_ratio"
FLOW_STRESS_RATIO_REASON = BASE_REASON + "flow_stress_ratio"
CASH_BUFFER_GAP_REASON = BASE_REASON + "cash_buffer_gap"
SETTLEMENT_LAG_REASON = BASE_REASON + "settlement_lag"
SOURCE_GAP_REASON = BASE_REASON + "source_gap"
CONFIDENCE_GAP_REASON = BASE_REASON + "confidence_gap"
STALE_SOURCE_REASON = BASE_REASON + "stale_source"

REASON_CODE_SEQUENCE = (
    REDEMPTION_PRESSURE_USD_REASON,
    REDEMPTION_PRESSURE_RATIO_REASON,
    FLOW_STRESS_RATIO_REASON,
    CASH_BUFFER_GAP_REASON,
    SETTLEMENT_LAG_REASON,
    SOURCE_GAP_REASON,
    CONFIDENCE_GAP_REASON,
    STALE_SOURCE_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    REDEMPTION_PRESSURE_USD_REASON,
    REDEMPTION_PRESSURE_RATIO_REASON,
    FLOW_STRESS_RATIO_REASON,
    CASH_BUFFER_GAP_REASON,
    SETTLEMENT_LAG_REASON,
    SOURCE_GAP_REASON,
    CONFIDENCE_GAP_REASON,
    STALE_SOURCE_REASON,
    READY_REASON,
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000.000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT = frozenset(
    (
        _join_parts("mar", "ket", "_", "slug"),
        _join_parts("ques", "tion"),
        _join_parts("payload", "_", "json"),
        _join_parts("wa", "llet"),
        _join_parts("or", "der"),
        _join_parts("au", "th"),
        _join_parts("pri", "vate"),
        _join_parts("k", "ey"),
    ),
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_CRYPTO_ETF_CREATION_REDEMPTION_STRESS_DIGEST_CONFIG_VERSION",
    "MarketResearchCryptoEtfCreationRedemptionStressDigestConfig",
    "MarketResearchCryptoEtfCreationRedemptionStressDigestReasonCodeCount",
    "MarketResearchCryptoEtfCreationRedemptionStressDigestReport",
    "MarketResearchCryptoEtfCreationRedemptionStressDigestRow",
    "MarketResearchCryptoEtfCreationRedemptionStressObservation",
    "build_market_research_crypto_etf_creation_redemption_stress_digest",
    "market_research_crypto_etf_creation_redemption_stress_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchCryptoEtfCreationRedemptionStressDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_CRYPTO_ETF_CREATION_REDEMPTION_STRESS_DIGEST_CONFIG_VERSION
    )
    max_observation_age_seconds: Decimal = Decimal("7200.000000")
    min_source_count: Decimal = Decimal("2.000000")
    watch_redemption_pressure_usd: Decimal = Decimal("25000000.000000")
    blocked_redemption_pressure_usd: Decimal = Decimal("100000000.000000")
    max_redemption_pressure_ratio: Decimal = Decimal("0.050000")
    watch_flow_stress_ratio: Decimal = Decimal("0.025000")
    min_cash_buffer_ratio: Decimal = Decimal("0.250000")
    max_settlement_lag_hours: Decimal = Decimal("24.000000")
    min_confidence: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchCryptoEtfCreationRedemptionStressDigestConfig "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            MarketResearchCryptoEtfCreationRedemptionStressDigestConfig,
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_CRYPTO_ETF_CREATION_REDEMPTION_STRESS_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in ("max_observation_age_seconds", "max_settlement_lag_hours"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_source_count",
            _require_positive_integral_decimal(
                "min_source_count",
                self.min_source_count,
            ),
        )
        for field_name in (
            "watch_redemption_pressure_usd",
            "blocked_redemption_pressure_usd",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_redemption_pressure_ratio",
            "watch_flow_stress_ratio",
            "min_cash_buffer_ratio",
            "min_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_redemption_pressure_usd > self.blocked_redemption_pressure_usd:
            raise ValueError(
                "watch_redemption_pressure_usd must be at most "
                "blocked_redemption_pressure_usd",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchCryptoEtfCreationRedemptionStressObservation:
    fund_id: str
    stress_id: str
    asset_symbol: str
    observed_at: datetime
    creations_usd: Decimal
    redemptions_usd: Decimal
    available_cash_usd: Decimal
    underlying_liquidity_usd: Decimal
    settlement_lag_hours: Decimal
    source_count: Decimal
    confidence: Decimal
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchCryptoEtfCreationRedemptionStressObservation "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "observation",
            self,
            MarketResearchCryptoEtfCreationRedemptionStressObservation,
        )
        for field_name in (
            "fund_id",
            "stress_id",
            "asset_symbol",
            "source_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "creations_usd",
            "redemptions_usd",
            "available_cash_usd",
            "settlement_lag_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "underlying_liquidity_usd",
            _require_positive_decimal(
                "underlying_liquidity_usd",
                self.underlying_liquidity_usd,
            ),
        )
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_integral_decimal("source_count", self.source_count),
        )
        object.__setattr__(
            self,
            "confidence",
            _require_ratio_decimal("confidence", self.confidence),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class MarketResearchCryptoEtfCreationRedemptionStressDigestRow:
    fund_id: str
    stress_id: str
    asset_symbol: str
    digest_status: str
    observed_at: datetime
    observation_age_seconds: Decimal
    creations_usd: Decimal
    redemptions_usd: Decimal
    net_creation_redemption_usd: Decimal
    redemption_pressure_usd: Decimal
    blocked_redemption_pressure_usd: Decimal
    available_cash_usd: Decimal
    underlying_liquidity_usd: Decimal
    redemption_pressure_ratio: Decimal
    flow_stress_ratio: Decimal
    cash_buffer_ratio: Decimal
    settlement_lag_hours: Decimal
    source_count: Decimal
    confidence: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchCryptoEtfCreationRedemptionStressDigestRow "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "row",
            self,
            MarketResearchCryptoEtfCreationRedemptionStressDigestRow,
        )
        _revalidate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchCryptoEtfCreationRedemptionStressDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    observation_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchCryptoEtfCreationRedemptionStressDigestReasonCodeCount "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "reason code count",
            self,
            MarketResearchCryptoEtfCreationRedemptionStressDigestReasonCodeCount,
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_integral_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "observation_ratio",
            _require_ratio_decimal("observation_ratio", self.observation_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchCryptoEtfCreationRedemptionStressDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    observation_count: Decimal
    ready_observation_count: Decimal
    watch_observation_count: Decimal
    blocked_observation_count: Decimal
    redemption_pressure_usd_observation_count: Decimal
    redemption_pressure_ratio_observation_count: Decimal
    flow_stress_ratio_observation_count: Decimal
    cash_buffer_gap_observation_count: Decimal
    settlement_lag_observation_count: Decimal
    source_gap_observation_count: Decimal
    confidence_gap_observation_count: Decimal
    stale_source_observation_count: Decimal
    total_redemption_pressure_usd: Decimal
    average_redemption_pressure_ratio: Decimal
    average_flow_stress_ratio: Decimal
    average_confidence: Decimal
    max_observation_age_seconds: Decimal
    max_allowed_observation_age_seconds: Decimal
    min_source_count: Decimal
    watch_redemption_pressure_usd: Decimal
    blocked_redemption_pressure_usd: Decimal
    max_redemption_pressure_ratio: Decimal
    watch_flow_stress_ratio: Decimal
    min_cash_buffer_ratio: Decimal
    max_settlement_lag_hours: Decimal
    min_confidence: Decimal
    rows: tuple[MarketResearchCryptoEtfCreationRedemptionStressDigestRow, ...]
    source_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchCryptoEtfCreationRedemptionStressDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchCryptoEtfCreationRedemptionStressDigestReport "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "report",
            self,
            MarketResearchCryptoEtfCreationRedemptionStressDigestReport,
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_CRYPTO_ETF_CREATION_REDEMPTION_STRESS_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        _require_status("digest_status", self.digest_status)
        _require_public_string("recommended_next_step", self.recommended_next_step)
        _revalidate_report_fields(self, strict_utc=False)
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_crypto_etf_creation_redemption_stress_digest(
    observations: Iterable[MarketResearchCryptoEtfCreationRedemptionStressObservation],
    *,
    config: MarketResearchCryptoEtfCreationRedemptionStressDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchCryptoEtfCreationRedemptionStressDigestReport:
    cfg = config or MarketResearchCryptoEtfCreationRedemptionStressDigestConfig()
    if type(cfg) is not MarketResearchCryptoEtfCreationRedemptionStressDigestConfig:
        raise ValueError(
            "config must be exactly "
            "MarketResearchCryptoEtfCreationRedemptionStressDigestConfig",
        )
    _require_hard_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    rows = tuple(
        _row_for_observation(
            observation,
            config=cfg,
            generated_at=generated_at_utc,
        )
        for observation in normalized_observations
    )
    sorted_rows = _sort_rows(rows)
    report_status = _report_status(sorted_rows)
    observation_count = _decimal_count(len(sorted_rows))
    return MarketResearchCryptoEtfCreationRedemptionStressDigestReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        digest_status=report_status,
        recommended_next_step=_recommended_next_step(report_status),
        observation_count=observation_count,
        ready_observation_count=_status_count(sorted_rows, STATUS_READY),
        watch_observation_count=_status_count(sorted_rows, STATUS_WATCH),
        blocked_observation_count=_status_count(sorted_rows, STATUS_BLOCKED),
        redemption_pressure_usd_observation_count=_reason_observation_count(
            sorted_rows,
            REDEMPTION_PRESSURE_USD_REASON,
        ),
        redemption_pressure_ratio_observation_count=_reason_observation_count(
            sorted_rows,
            REDEMPTION_PRESSURE_RATIO_REASON,
        ),
        flow_stress_ratio_observation_count=_reason_observation_count(
            sorted_rows,
            FLOW_STRESS_RATIO_REASON,
        ),
        cash_buffer_gap_observation_count=_reason_observation_count(
            sorted_rows,
            CASH_BUFFER_GAP_REASON,
        ),
        settlement_lag_observation_count=_reason_observation_count(
            sorted_rows,
            SETTLEMENT_LAG_REASON,
        ),
        source_gap_observation_count=_reason_observation_count(
            sorted_rows,
            SOURCE_GAP_REASON,
        ),
        confidence_gap_observation_count=_reason_observation_count(
            sorted_rows,
            CONFIDENCE_GAP_REASON,
        ),
        stale_source_observation_count=_reason_observation_count(
            sorted_rows,
            STALE_SOURCE_REASON,
        ),
        total_redemption_pressure_usd=_decimal_sum(
            row.redemption_pressure_usd for row in sorted_rows
        ),
        average_redemption_pressure_ratio=_ratio(
            _decimal_sum(row.redemption_pressure_ratio for row in sorted_rows),
            observation_count,
        ),
        average_flow_stress_ratio=_ratio(
            _decimal_sum(row.flow_stress_ratio for row in sorted_rows),
            observation_count,
        ),
        average_confidence=_ratio(
            _decimal_sum(row.confidence for row in sorted_rows),
            observation_count,
        ),
        max_observation_age_seconds=max(
            (row.observation_age_seconds for row in sorted_rows),
            default=ZERO,
        ),
        max_allowed_observation_age_seconds=cfg.max_observation_age_seconds,
        min_source_count=cfg.min_source_count,
        watch_redemption_pressure_usd=cfg.watch_redemption_pressure_usd,
        blocked_redemption_pressure_usd=cfg.blocked_redemption_pressure_usd,
        max_redemption_pressure_ratio=cfg.max_redemption_pressure_ratio,
        watch_flow_stress_ratio=cfg.watch_flow_stress_ratio,
        min_cash_buffer_ratio=cfg.min_cash_buffer_ratio,
        max_settlement_lag_hours=cfg.max_settlement_lag_hours,
        min_confidence=cfg.min_confidence,
        rows=sorted_rows,
        source_config_versions=tuple(
            sorted(
                (observation.stress_id, observation.source_config_version)
                for observation in normalized_observations
            ),
        ),
        reason_code_counts=_reason_code_counts(sorted_rows),
        reason_codes=_summary_reason_codes(sorted_rows),
    )


def market_research_crypto_etf_creation_redemption_stress_digest_payload(
    report: MarketResearchCryptoEtfCreationRedemptionStressDigestReport,
) -> MappingProxyType:
    if type(report) is not MarketResearchCryptoEtfCreationRedemptionStressDigestReport:
        raise ValueError(
            "report must be exactly "
            "MarketResearchCryptoEtfCreationRedemptionStressDigestReport",
        )
    _revalidate_public_dataclass(report)
    return _freeze(_payload_value(report))


def _row_for_observation(
    observation: MarketResearchCryptoEtfCreationRedemptionStressObservation,
    *,
    config: MarketResearchCryptoEtfCreationRedemptionStressDigestConfig,
    generated_at: datetime,
) -> MarketResearchCryptoEtfCreationRedemptionStressDigestRow:
    if observation.observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    observation_age_seconds = _age_seconds(generated_at, observation.observed_at)
    net_creation_redemption_usd = _quantize(
        observation.creations_usd - observation.redemptions_usd,
    )
    redemption_pressure_usd = _redemption_pressure(
        creations_usd=observation.creations_usd,
        redemptions_usd=observation.redemptions_usd,
        available_cash_usd=observation.available_cash_usd,
    )
    redemption_pressure_ratio = _ratio(
        redemption_pressure_usd,
        observation.underlying_liquidity_usd,
    )
    flow_stress_ratio = _ratio(
        _decimal_abs(net_creation_redemption_usd),
        observation.underlying_liquidity_usd,
    )
    cash_buffer_ratio = _cash_buffer_ratio(
        observation.available_cash_usd,
        observation.redemptions_usd,
    )
    reason_codes = _row_reason_codes(
        observation=observation,
        config=config,
        observation_age_seconds=observation_age_seconds,
        redemption_pressure_usd=redemption_pressure_usd,
        redemption_pressure_ratio=redemption_pressure_ratio,
        flow_stress_ratio=flow_stress_ratio,
        cash_buffer_ratio=cash_buffer_ratio,
    )
    return MarketResearchCryptoEtfCreationRedemptionStressDigestRow(
        fund_id=observation.fund_id,
        stress_id=observation.stress_id,
        asset_symbol=observation.asset_symbol,
        digest_status=_row_status(
            reason_codes,
            redemption_pressure_usd=redemption_pressure_usd,
            config=config,
        ),
        observed_at=observation.observed_at,
        observation_age_seconds=observation_age_seconds,
        creations_usd=observation.creations_usd,
        redemptions_usd=observation.redemptions_usd,
        net_creation_redemption_usd=net_creation_redemption_usd,
        redemption_pressure_usd=redemption_pressure_usd,
        blocked_redemption_pressure_usd=config.blocked_redemption_pressure_usd,
        available_cash_usd=observation.available_cash_usd,
        underlying_liquidity_usd=observation.underlying_liquidity_usd,
        redemption_pressure_ratio=redemption_pressure_ratio,
        flow_stress_ratio=flow_stress_ratio,
        cash_buffer_ratio=cash_buffer_ratio,
        settlement_lag_hours=observation.settlement_lag_hours,
        source_count=observation.source_count,
        confidence=observation.confidence,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    observation: MarketResearchCryptoEtfCreationRedemptionStressObservation,
    config: MarketResearchCryptoEtfCreationRedemptionStressDigestConfig,
    observation_age_seconds: Decimal,
    redemption_pressure_usd: Decimal,
    redemption_pressure_ratio: Decimal,
    flow_stress_ratio: Decimal,
    cash_buffer_ratio: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if redemption_pressure_usd >= config.watch_redemption_pressure_usd:
        reasons.append(REDEMPTION_PRESSURE_USD_REASON)
    if redemption_pressure_ratio > config.max_redemption_pressure_ratio:
        reasons.append(REDEMPTION_PRESSURE_RATIO_REASON)
    if flow_stress_ratio > config.watch_flow_stress_ratio:
        reasons.append(FLOW_STRESS_RATIO_REASON)
    if cash_buffer_ratio < config.min_cash_buffer_ratio:
        reasons.append(CASH_BUFFER_GAP_REASON)
    if observation.settlement_lag_hours > config.max_settlement_lag_hours:
        reasons.append(SETTLEMENT_LAG_REASON)
    if observation.source_count < config.min_source_count:
        reasons.append(SOURCE_GAP_REASON)
    if observation.confidence < config.min_confidence:
        reasons.append(CONFIDENCE_GAP_REASON)
    if observation_age_seconds > config.max_observation_age_seconds:
        reasons.append(STALE_SOURCE_REASON)
    if not reasons:
        reasons.append(READY_REASON)
    return tuple(reason for reason in ROW_REASON_CODE_SEQUENCE if reason in reasons)


def _row_status(
    reason_codes: tuple[str, ...],
    *,
    redemption_pressure_usd: Decimal,
    config: MarketResearchCryptoEtfCreationRedemptionStressDigestConfig,
) -> str:
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    if redemption_pressure_usd >= config.blocked_redemption_pressure_usd:
        return STATUS_BLOCKED
    if any(
        reason in reason_codes
        for reason in (
            REDEMPTION_PRESSURE_RATIO_REASON,
            CASH_BUFFER_GAP_REASON,
            SETTLEMENT_LAG_REASON,
            CONFIDENCE_GAP_REASON,
            STALE_SOURCE_REASON,
        )
    ):
        return STATUS_BLOCKED
    return STATUS_WATCH


def _row_status_from_row(
    row: MarketResearchCryptoEtfCreationRedemptionStressDigestRow,
) -> str:
    if row.reason_codes == (READY_REASON,):
        return STATUS_READY
    if row.redemption_pressure_usd >= row.blocked_redemption_pressure_usd:
        return STATUS_BLOCKED
    if any(
        reason in row.reason_codes
        for reason in (
            REDEMPTION_PRESSURE_RATIO_REASON,
            CASH_BUFFER_GAP_REASON,
            SETTLEMENT_LAG_REASON,
            CONFIDENCE_GAP_REASON,
            STALE_SOURCE_REASON,
        )
    ):
        return STATUS_BLOCKED
    return STATUS_WATCH


def _row_sort_tuple(
    row: MarketResearchCryptoEtfCreationRedemptionStressDigestRow,
) -> tuple[int, Decimal, Decimal]:
    status_rank = {
        STATUS_BLOCKED: 0,
        STATUS_WATCH: 1,
        STATUS_READY: 2,
    }[row.digest_status]
    severity = _decimal_count(
        sum(1 for reason in row.reason_codes if reason != READY_REASON),
    )
    return (status_rank, -severity, -row.redemption_pressure_usd)


def _sort_rows(
    rows: tuple[MarketResearchCryptoEtfCreationRedemptionStressDigestRow, ...],
) -> tuple[MarketResearchCryptoEtfCreationRedemptionStressDigestRow, ...]:
    decorated_rows = tuple(
        ((_row_sort_tuple(row), row.stress_id, row.fund_id), row)
        for row in rows
    )
    return tuple(row for _, row in sorted(decorated_rows))


def _report_status(
    rows: tuple[MarketResearchCryptoEtfCreationRedemptionStressDigestRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_READY


def _recommended_next_step(status: str) -> str:
    if status == STATUS_BLOCKED:
        return (
            "block_report_only_market_research_crypto_etf_creation_redemption_"
            "stress_digest"
        )
    if status == STATUS_WATCH:
        return (
            "review_report_only_market_research_crypto_etf_creation_redemption_"
            "stress_digest"
        )
    return (
        "allow_report_only_market_research_crypto_etf_creation_redemption_"
        "stress_digest"
    )


def _status_count(
    rows: tuple[MarketResearchCryptoEtfCreationRedemptionStressDigestRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.digest_status == status))


def _reason_observation_count(
    rows: tuple[MarketResearchCryptoEtfCreationRedemptionStressDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _reason_code_counts(
    rows: tuple[MarketResearchCryptoEtfCreationRedemptionStressDigestRow, ...],
) -> tuple[MarketResearchCryptoEtfCreationRedemptionStressDigestReasonCodeCount, ...]:
    observation_count = _decimal_count(len(rows))
    if not rows:
        return (
            MarketResearchCryptoEtfCreationRedemptionStressDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                observation_ratio=ZERO,
            ),
        )
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        MarketResearchCryptoEtfCreationRedemptionStressDigestReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
            observation_ratio=_ratio(_decimal_count(counts[reason_code]), observation_count),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _summary_reason_codes(
    rows: tuple[MarketResearchCryptoEtfCreationRedemptionStressDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    seen: set[str] = set()
    for row in rows:
        seen.update(row.reason_codes)
    if len(seen) > 1 and READY_REASON in seen:
        seen.remove(READY_REASON)
    return tuple(reason for reason in REASON_CODE_SEQUENCE if reason in seen)


def _revalidate_row(
    row: MarketResearchCryptoEtfCreationRedemptionStressDigestRow,
) -> None:
    for field_name in ("fund_id", "stress_id", "asset_symbol"):
        _require_public_string(field_name, getattr(row, field_name))
    _require_status("digest_status", row.digest_status)
    object.__setattr__(row, "observed_at", _as_utc("observed_at", row.observed_at))
    for field_name in (
        "observation_age_seconds",
        "creations_usd",
        "redemptions_usd",
        "redemption_pressure_usd",
        "blocked_redemption_pressure_usd",
        "available_cash_usd",
        "settlement_lag_hours",
    ):
        object.__setattr__(
            row,
            field_name,
            _require_nonnegative_decimal(field_name, getattr(row, field_name)),
        )
    object.__setattr__(
        row,
        "underlying_liquidity_usd",
        _require_positive_decimal(
            "underlying_liquidity_usd",
            row.underlying_liquidity_usd,
        ),
    )
    object.__setattr__(
        row,
        "source_count",
        _require_nonnegative_integral_decimal("source_count", row.source_count),
    )
    object.__setattr__(
        row,
        "net_creation_redemption_usd",
        _require_decimal(
            "net_creation_redemption_usd",
            row.net_creation_redemption_usd,
        ),
    )
    for field_name in (
        "redemption_pressure_ratio",
        "flow_stress_ratio",
        "cash_buffer_ratio",
        "confidence",
    ):
        object.__setattr__(
            row,
            field_name,
            _require_ratio_decimal(field_name, getattr(row, field_name)),
        )
    object.__setattr__(
        row,
        "reason_codes",
        _normalize_reason_codes(
            "reason_codes",
            row.reason_codes,
            ROW_REASON_CODE_SEQUENCE,
        ),
    )
    _validate_row(row)


def _validate_row(
    row: MarketResearchCryptoEtfCreationRedemptionStressDigestRow,
) -> None:
    if row.net_creation_redemption_usd != _quantize(
        row.creations_usd - row.redemptions_usd,
    ):
        raise ValueError("net_creation_redemption_usd does not match inputs")
    if row.redemption_pressure_usd != _redemption_pressure(
        creations_usd=row.creations_usd,
        redemptions_usd=row.redemptions_usd,
        available_cash_usd=row.available_cash_usd,
    ):
        raise ValueError("redemption_pressure_usd does not match inputs")
    if row.redemption_pressure_ratio != _ratio(
        row.redemption_pressure_usd,
        row.underlying_liquidity_usd,
    ):
        raise ValueError("redemption_pressure_ratio does not match inputs")
    if row.flow_stress_ratio != _ratio(
        _decimal_abs(row.net_creation_redemption_usd),
        row.underlying_liquidity_usd,
    ):
        raise ValueError("flow_stress_ratio does not match inputs")
    if row.cash_buffer_ratio != _cash_buffer_ratio(
        row.available_cash_usd,
        row.redemptions_usd,
    ):
        raise ValueError("cash_buffer_ratio does not match inputs")
    if row.digest_status != _row_status_from_row(row):
        raise ValueError("digest_status does not match reason_codes")


def _revalidate_report_fields(
    report: MarketResearchCryptoEtfCreationRedemptionStressDigestReport,
    *,
    strict_utc: bool,
) -> None:
    if strict_utc:
        _require_utc_datetime("generated_at", report.generated_at)
    for field_name in (
        "observation_count",
        "ready_observation_count",
        "watch_observation_count",
        "blocked_observation_count",
        "redemption_pressure_usd_observation_count",
        "redemption_pressure_ratio_observation_count",
        "flow_stress_ratio_observation_count",
        "cash_buffer_gap_observation_count",
        "settlement_lag_observation_count",
        "source_gap_observation_count",
        "confidence_gap_observation_count",
        "stale_source_observation_count",
    ):
        object.__setattr__(
            report,
            field_name,
            _require_nonnegative_integral_decimal(field_name, getattr(report, field_name)),
        )
    for field_name in (
        "total_redemption_pressure_usd",
        "max_observation_age_seconds",
        "max_allowed_observation_age_seconds",
        "watch_redemption_pressure_usd",
        "blocked_redemption_pressure_usd",
        "max_settlement_lag_hours",
    ):
        object.__setattr__(
            report,
            field_name,
            _require_nonnegative_decimal(field_name, getattr(report, field_name)),
        )
    object.__setattr__(
        report,
        "min_source_count",
        _require_positive_integral_decimal("min_source_count", report.min_source_count),
    )
    for field_name in (
        "average_redemption_pressure_ratio",
        "average_flow_stress_ratio",
        "average_confidence",
        "max_redemption_pressure_ratio",
        "watch_flow_stress_ratio",
        "min_cash_buffer_ratio",
        "min_confidence",
    ):
        object.__setattr__(
            report,
            field_name,
            _require_ratio_decimal(field_name, getattr(report, field_name)),
        )
    object.__setattr__(report, "rows", _normalize_rows(report.rows))
    object.__setattr__(
        report,
        "source_config_versions",
        _normalize_source_config_versions(report.source_config_versions),
    )
    object.__setattr__(
        report,
        "reason_code_counts",
        _normalize_reason_code_counts(report.reason_code_counts),
    )
    object.__setattr__(
        report,
        "reason_codes",
        _normalize_reason_codes(
            "reason_codes",
            report.reason_codes,
            REASON_CODE_SEQUENCE,
        ),
    )


def _validate_report(
    report: MarketResearchCryptoEtfCreationRedemptionStressDigestReport,
) -> None:
    if report.observation_count != _decimal_count(len(report.rows)):
        raise ValueError("observation_count does not match rows")
    if report.ready_observation_count != _status_count(report.rows, STATUS_READY):
        raise ValueError("ready_observation_count does not match rows")
    if report.watch_observation_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_observation_count does not match rows")
    if report.blocked_observation_count != _status_count(report.rows, STATUS_BLOCKED):
        raise ValueError("blocked_observation_count does not match rows")
    expected_counts = (
        (
            REDEMPTION_PRESSURE_USD_REASON,
            report.redemption_pressure_usd_observation_count,
        ),
        (
            REDEMPTION_PRESSURE_RATIO_REASON,
            report.redemption_pressure_ratio_observation_count,
        ),
        (FLOW_STRESS_RATIO_REASON, report.flow_stress_ratio_observation_count),
        (CASH_BUFFER_GAP_REASON, report.cash_buffer_gap_observation_count),
        (SETTLEMENT_LAG_REASON, report.settlement_lag_observation_count),
        (SOURCE_GAP_REASON, report.source_gap_observation_count),
        (CONFIDENCE_GAP_REASON, report.confidence_gap_observation_count),
        (STALE_SOURCE_REASON, report.stale_source_observation_count),
    )
    for reason_code, count in expected_counts:
        if count != _reason_observation_count(report.rows, reason_code):
            raise ValueError("reason observation count does not match rows")
    if report.digest_status != _report_status(report.rows):
        raise ValueError("digest_status does not match rows")
    if any(
        row.blocked_redemption_pressure_usd != report.blocked_redemption_pressure_usd
        for row in report.rows
    ):
        raise ValueError("row blocked_redemption_pressure_usd does not match report")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step does not match digest_status")
    if report.total_redemption_pressure_usd != _decimal_sum(
        row.redemption_pressure_usd for row in report.rows
    ):
        raise ValueError("total_redemption_pressure_usd does not match rows")
    if report.average_redemption_pressure_ratio != _ratio(
        _decimal_sum(row.redemption_pressure_ratio for row in report.rows),
        report.observation_count,
    ):
        raise ValueError("average_redemption_pressure_ratio does not match rows")
    if report.average_flow_stress_ratio != _ratio(
        _decimal_sum(row.flow_stress_ratio for row in report.rows),
        report.observation_count,
    ):
        raise ValueError("average_flow_stress_ratio does not match rows")
    if report.average_confidence != _ratio(
        _decimal_sum(row.confidence for row in report.rows),
        report.observation_count,
    ):
        raise ValueError("average_confidence does not match rows")
    if report.max_observation_age_seconds != max(
        (row.observation_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_observation_age_seconds does not match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts do not match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes do not match rows")


def _normalize_observations(
    observations: Iterable[MarketResearchCryptoEtfCreationRedemptionStressObservation],
) -> tuple[MarketResearchCryptoEtfCreationRedemptionStressObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be iterable")
    try:
        observation_tuple = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be iterable") from exc
    seen_ids: set[str] = set()
    for observation in observation_tuple:
        if type(observation) is not MarketResearchCryptoEtfCreationRedemptionStressObservation:
            raise ValueError(
                "observations must contain "
                "MarketResearchCryptoEtfCreationRedemptionStressObservation",
            )
        if observation.stress_id in seen_ids:
            raise ValueError("stress_id values must be unique")
        seen_ids.add(observation.stress_id)
        _require_hard_flags("observation", observation)
    return observation_tuple


def _normalize_rows(
    rows: tuple[MarketResearchCryptoEtfCreationRedemptionStressDigestRow, ...],
) -> tuple[MarketResearchCryptoEtfCreationRedemptionStressDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen_ids: set[str] = set()
    for row in rows:
        if type(row) is not MarketResearchCryptoEtfCreationRedemptionStressDigestRow:
            raise ValueError(
                "rows must contain MarketResearchCryptoEtfCreationRedemptionStressDigestRow",
            )
        if row.stress_id in seen_ids:
            raise ValueError("rows must not contain duplicate stress_id values")
        seen_ids.add(row.stress_id)
        _revalidate_row(row)
        _require_hard_flags("row", row)
    canonical = _sort_rows(rows)
    if rows != canonical:
        raise ValueError("rows must use canonical sequence")
    return rows


def _normalize_source_config_versions(
    values: tuple[tuple[str, str], ...],
) -> tuple[tuple[str, str], ...]:
    if type(values) is not tuple:
        raise ValueError("source_config_versions must be a tuple")
    normalized: list[tuple[str, str]] = []
    seen_ids: set[str] = set()
    for value in values:
        if type(value) is not tuple or len(value) != 2:
            raise ValueError("source_config_versions must contain string pairs")
        stress_id, source_config_version = value
        _require_public_string("stress_id", stress_id)
        _require_public_string("source_config_version", source_config_version)
        if stress_id in seen_ids:
            raise ValueError("source_config_versions must not contain duplicates")
        seen_ids.add(stress_id)
        normalized.append((stress_id, source_config_version))
    canonical = tuple(sorted(normalized))
    if values != canonical:
        raise ValueError("source_config_versions must use canonical sequence")
    return values


def _normalize_reason_code_counts(
    values: tuple[
        MarketResearchCryptoEtfCreationRedemptionStressDigestReasonCodeCount,
        ...,
    ],
) -> tuple[MarketResearchCryptoEtfCreationRedemptionStressDigestReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    seen_reasons: set[str] = set()
    for value in values:
        if (
            type(value)
            is not MarketResearchCryptoEtfCreationRedemptionStressDigestReasonCodeCount
        ):
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchCryptoEtfCreationRedemptionStressDigestReasonCodeCount",
            )
        if value.reason_code in seen_reasons:
            raise ValueError("reason_code_counts must not contain duplicates")
        seen_reasons.add(value.reason_code)
        _require_hard_flags("reason code count", value)
    canonical = tuple(
        value
        for reason_code in REASON_CODE_SEQUENCE
        for value in values
        if value.reason_code == reason_code
    )
    if values != canonical:
        raise ValueError("reason_code_counts must use canonical sequence")
    return values


def _normalize_reason_codes(
    field_name: str,
    values: tuple[str, ...],
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not values:
        raise ValueError(f"{field_name} must contain at least one value")
    if len(set(values)) != len(values):
        raise ValueError(f"{field_name} must not contain duplicates")
    for value in values:
        _require_reason_code("reason_code", value)
        if value not in sequence:
            raise ValueError(f"{field_name} contains unsupported value")
    canonical = tuple(reason for reason in sequence if reason in values)
    if values != canonical:
        raise ValueError(f"{field_name} must use canonical sequence")
    return values


def _redemption_pressure(
    *,
    creations_usd: Decimal,
    redemptions_usd: Decimal,
    available_cash_usd: Decimal,
) -> Decimal:
    pressure = redemptions_usd - creations_usd - available_cash_usd
    if pressure <= ZERO:
        return ZERO
    return _quantize(pressure)


def _cash_buffer_ratio(available_cash_usd: Decimal, redemptions_usd: Decimal) -> Decimal:
    if redemptions_usd == ZERO:
        return ONE
    capped_cash = min(available_cash_usd, redemptions_usd)
    return _ratio(capped_cash, redemptions_usd)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    microseconds = Decimal(
        delta.days * 86400000000 + delta.seconds * 1000000 + delta.microseconds,
    )
    return _quantize(microseconds / MICROSECONDS_PER_SECOND)


def _decimal_sum(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("values must be Decimals")
        total += value
    return _quantize(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _decimal_abs(value: Decimal) -> Decimal:
    return _quantize(abs(value))


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_positive_integral_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_positive_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return decimal_value


def _require_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
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
    if value.as_tuple().exponent != -6:
        raise ValueError(f"{field_name} must use six-decimal precision")
    if value != _quantize(value):
        raise ValueError(f"{field_name} must use six-decimal precision")
    return value


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_utc_datetime(field_name: str, value: object) -> None:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is not UTC or value.utcoffset() != ZERO_TIME_OFFSET:
        raise ValueError(f"{field_name} must be UTC")


ZERO_TIME_OFFSET = datetime(2026, 1, 1, tzinfo=UTC).utcoffset()


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be supported")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    lowered = value.lower()
    if any(term in lowered for term in UNSAFE_TEXT):
        raise ValueError(f"{field_name} must be redacted")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _require_exact_type(label: str, value: object, expected_type: type) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _revalidate_public_dataclass(value: object) -> None:
    if type(value) is MarketResearchCryptoEtfCreationRedemptionStressDigestReport:
        _require_utc_datetime("generated_at", value.generated_at)
        _require_status("digest_status", value.digest_status)
        _require_public_string("recommended_next_step", value.recommended_next_step)
        _revalidate_report_fields(value, strict_utc=True)
        _validate_report(value)
        _require_hard_flags("report", value)
        return
    if type(value) is MarketResearchCryptoEtfCreationRedemptionStressDigestRow:
        _require_utc_datetime("observed_at", value.observed_at)
        _revalidate_row(value)
        _require_hard_flags("row", value)
        return
    if type(value) is MarketResearchCryptoEtfCreationRedemptionStressDigestReasonCodeCount:
        _require_reason_code("reason_code", value.reason_code)
        _require_positive_integral_decimal("count", value.count)
        _require_ratio_decimal("observation_ratio", value.observation_ratio)
        _require_hard_flags("reason code count", value)
        return
    if type(value) is MarketResearchCryptoEtfCreationRedemptionStressDigestConfig:
        _require_hard_flags("config", value)
        return
    if type(value) is MarketResearchCryptoEtfCreationRedemptionStressObservation:
        _require_utc_datetime("observed_at", value.observed_at)
        _require_hard_flags("observation", value)
        return
    raise ValueError("payload contains unsupported dataclass")


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        _require_decimal("payload numeric value", value)
        return format(value, "f")
    if type(value) is datetime:
        _require_utc_datetime("payload datetime value", value)
        return value.isoformat()
    if isinstance(value, float):
        raise ValueError("payload value must not be a float")
    if is_dataclass(value) and not isinstance(value, type):
        _revalidate_public_dataclass(value)
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is tuple:
        return tuple(_payload_value(item) for item in value)
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError("payload value must be public")


def _freeze(value: Any) -> Any:
    if type(value) is dict:
        return MappingProxyType({name: _freeze(item) for name, item in value.items()})
    if type(value) is tuple:
        return tuple(_freeze(item) for item in value)
    return value
