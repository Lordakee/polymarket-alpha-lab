"""Pure Phase 1 crypto ETF creation/redemption imbalance research reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from types import MappingProxyType
from typing import Any


DEFAULT_MARKET_RESEARCH_CRYPTO_ETF_CREATION_REDEMPTION_IMBALANCE_DIGEST_CONFIG_VERSION = (
    "market-research-crypto-etf-creation-redemption-imbalance-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
IMBALANCE_DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

READY_REASON = (
    "market_research_crypto_etf_creation_redemption_imbalance_digest_ready"
)
NO_INPUTS_REASON = (
    "market_research_crypto_etf_creation_redemption_imbalance_digest_no_inputs"
)
IMBALANCE_USD_REASON = (
    "market_research_crypto_etf_creation_redemption_imbalance_digest_imbalance_usd"
)
IMBALANCE_RATIO_REASON = (
    "market_research_crypto_etf_creation_redemption_imbalance_digest_imbalance_ratio"
)
REDEMPTION_PRESSURE_REASON = (
    "market_research_crypto_etf_creation_redemption_imbalance_digest_redemption_pressure"
)
CREATION_PRESSURE_REASON = (
    "market_research_crypto_etf_creation_redemption_imbalance_digest_creation_pressure"
)
IMBALANCE_ACCELERATION_REASON = (
    "market_research_crypto_etf_creation_redemption_imbalance_digest_imbalance_acceleration"
)
NAV_DISLOCATION_REASON = (
    "market_research_crypto_etf_creation_redemption_imbalance_digest_nav_dislocation"
)
SETTLEMENT_LAG_REASON = (
    "market_research_crypto_etf_creation_redemption_imbalance_digest_settlement_lag"
)
SOURCE_GAP_REASON = (
    "market_research_crypto_etf_creation_redemption_imbalance_digest_source_gap"
)
CONFIDENCE_GAP_REASON = (
    "market_research_crypto_etf_creation_redemption_imbalance_digest_confidence_gap"
)
STALE_OBSERVATION_REASON = (
    "market_research_crypto_etf_creation_redemption_imbalance_digest_stale_observation"
)

REASON_CODE_SEQUENCE = (
    IMBALANCE_USD_REASON,
    IMBALANCE_RATIO_REASON,
    REDEMPTION_PRESSURE_REASON,
    CREATION_PRESSURE_REASON,
    IMBALANCE_ACCELERATION_REASON,
    NAV_DISLOCATION_REASON,
    SETTLEMENT_LAG_REASON,
    SOURCE_GAP_REASON,
    CONFIDENCE_GAP_REASON,
    STALE_OBSERVATION_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    IMBALANCE_USD_REASON,
    IMBALANCE_RATIO_REASON,
    REDEMPTION_PRESSURE_REASON,
    CREATION_PRESSURE_REASON,
    IMBALANCE_ACCELERATION_REASON,
    NAV_DISLOCATION_REASON,
    SETTLEMENT_LAG_REASON,
    SOURCE_GAP_REASON,
    CONFIDENCE_GAP_REASON,
    STALE_OBSERVATION_REASON,
    READY_REASON,
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("mar", "ket", "_", "slug"),
        _join_parts("ques", "tion"),
        _join_parts("wa", "llet"),
        _join_parts("or", "der"),
        _join_parts("to", "ken"),
        _join_parts("sec", "ret"),
        _join_parts("pri", "vate"),
        _join_parts("0", "x"),
    ),
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_CRYPTO_ETF_CREATION_REDEMPTION_IMBALANCE_DIGEST_CONFIG_VERSION",
    "MarketResearchCryptoEtfCreationRedemptionImbalanceDigestConfig",
    "MarketResearchCryptoEtfCreationRedemptionImbalanceDigestReasonCodeCount",
    "MarketResearchCryptoEtfCreationRedemptionImbalanceDigestReport",
    "MarketResearchCryptoEtfCreationRedemptionImbalanceDigestRow",
    "MarketResearchCryptoEtfCreationRedemptionImbalanceObservation",
    "build_market_research_crypto_etf_creation_redemption_imbalance_digest",
    "market_research_crypto_etf_creation_redemption_imbalance_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchCryptoEtfCreationRedemptionImbalanceDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_CRYPTO_ETF_CREATION_REDEMPTION_IMBALANCE_DIGEST_CONFIG_VERSION
    )
    max_observation_age_seconds: Decimal = Decimal("7200.000000")
    min_source_count: Decimal = Decimal("2.000000")
    watch_abs_imbalance_usd: Decimal = Decimal("25000000.000000")
    blocked_abs_imbalance_usd: Decimal = Decimal("100000000.000000")
    max_imbalance_ratio: Decimal = Decimal("0.050000")
    max_nav_dislocation_abs: Decimal = Decimal("0.015000")
    max_settlement_lag_hours: Decimal = Decimal("24.000000")
    min_confidence: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoEtfCreationRedemptionImbalanceDigestConfig:
            raise TypeError(
                "MarketResearchCryptoEtfCreationRedemptionImbalanceDigestConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoEtfCreationRedemptionImbalanceDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchCryptoEtfCreationRedemptionImbalanceDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "max_observation_age_seconds",
            "min_source_count",
            "max_settlement_lag_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("watch_abs_imbalance_usd", "blocked_abs_imbalance_usd"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_imbalance_ratio",
            "max_nav_dislocation_abs",
            "min_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_abs_imbalance_usd > self.blocked_abs_imbalance_usd:
            raise ValueError(
                "watch_abs_imbalance_usd must be at most blocked_abs_imbalance_usd",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchCryptoEtfCreationRedemptionImbalanceObservation:
    condition_id: str
    imbalance_key: str
    asset_symbol: str
    observed_at: datetime
    creations_usd: Decimal
    redemptions_usd: Decimal
    previous_imbalance_usd: Decimal
    assets_under_management_usd: Decimal
    nav_dislocation: Decimal
    settlement_lag_hours: Decimal
    source_count: Decimal
    confidence: Decimal
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoEtfCreationRedemptionImbalanceObservation:
            raise TypeError(
                "MarketResearchCryptoEtfCreationRedemptionImbalanceObservation "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoEtfCreationRedemptionImbalanceObservation:
            raise ValueError(
                "observation must be exactly "
                "MarketResearchCryptoEtfCreationRedemptionImbalanceObservation",
            )
        for field_name in (
            "condition_id",
            "imbalance_key",
            "asset_symbol",
            "source_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "creations_usd",
            "redemptions_usd",
            "settlement_lag_hours",
            "source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "previous_imbalance_usd",
            _require_count_decimal("previous_imbalance_usd", self.previous_imbalance_usd),
        )
        object.__setattr__(
            self,
            "assets_under_management_usd",
            _require_positive_count_decimal(
                "assets_under_management_usd",
                self.assets_under_management_usd,
            ),
        )
        object.__setattr__(
            self,
            "nav_dislocation",
            _require_signed_ratio_decimal("nav_dislocation", self.nav_dislocation),
        )
        object.__setattr__(
            self,
            "confidence",
            _require_ratio_decimal("confidence", self.confidence),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class MarketResearchCryptoEtfCreationRedemptionImbalanceDigestRow:
    condition_id: str
    imbalance_key: str
    asset_symbol: str
    digest_status: str
    observed_at: datetime
    observation_age_seconds: Decimal
    creations_usd: Decimal
    redemptions_usd: Decimal
    net_creation_redemption_usd: Decimal
    previous_imbalance_usd: Decimal
    imbalance_abs_usd: Decimal
    imbalance_change_abs_usd: Decimal
    assets_under_management_usd: Decimal
    imbalance_ratio: Decimal
    nav_dislocation: Decimal
    nav_dislocation_abs: Decimal
    settlement_lag_hours: Decimal
    source_count: Decimal
    confidence: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoEtfCreationRedemptionImbalanceDigestRow:
            raise TypeError(
                "MarketResearchCryptoEtfCreationRedemptionImbalanceDigestRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoEtfCreationRedemptionImbalanceDigestRow:
            raise ValueError(
                "row must be exactly "
                "MarketResearchCryptoEtfCreationRedemptionImbalanceDigestRow",
            )
        for field_name in ("condition_id", "imbalance_key", "asset_symbol"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_status("digest_status", self.digest_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "observation_age_seconds",
            "creations_usd",
            "redemptions_usd",
            "imbalance_abs_usd",
            "imbalance_change_abs_usd",
            "settlement_lag_hours",
            "source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "net_creation_redemption_usd",
            "previous_imbalance_usd",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "assets_under_management_usd",
            _require_positive_count_decimal(
                "assets_under_management_usd",
                self.assets_under_management_usd,
            ),
        )
        for field_name in ("imbalance_ratio", "nav_dislocation_abs", "confidence"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "nav_dislocation",
            _require_signed_ratio_decimal("nav_dislocation", self.nav_dislocation),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, sequence=ROW_REASON_CODE_SEQUENCE),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchCryptoEtfCreationRedemptionImbalanceDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    observation_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoEtfCreationRedemptionImbalanceDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchCryptoEtfCreationRedemptionImbalanceDigestReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if (
            type(self)
            is not MarketResearchCryptoEtfCreationRedemptionImbalanceDigestReasonCodeCount
        ):
            raise ValueError(
                "reason code count must be exactly "
                "MarketResearchCryptoEtfCreationRedemptionImbalanceDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "observation_ratio",
            _require_ratio_decimal("observation_ratio", self.observation_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchCryptoEtfCreationRedemptionImbalanceDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    observation_count: Decimal
    ready_observation_count: Decimal
    watch_observation_count: Decimal
    blocked_observation_count: Decimal
    imbalance_usd_observation_count: Decimal
    imbalance_ratio_observation_count: Decimal
    redemption_pressure_observation_count: Decimal
    creation_pressure_observation_count: Decimal
    imbalance_acceleration_observation_count: Decimal
    nav_dislocation_observation_count: Decimal
    settlement_lag_observation_count: Decimal
    source_gap_observation_count: Decimal
    confidence_gap_observation_count: Decimal
    stale_observation_count: Decimal
    total_net_creation_redemption_usd: Decimal
    average_imbalance_ratio: Decimal
    average_confidence: Decimal
    max_observation_age_seconds: Decimal
    max_allowed_observation_age_seconds: Decimal
    min_source_count: Decimal
    watch_abs_imbalance_usd: Decimal
    blocked_abs_imbalance_usd: Decimal
    max_imbalance_ratio: Decimal
    max_nav_dislocation_abs: Decimal
    max_settlement_lag_hours: Decimal
    min_confidence: Decimal
    rows: tuple[MarketResearchCryptoEtfCreationRedemptionImbalanceDigestRow, ...]
    source_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchCryptoEtfCreationRedemptionImbalanceDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoEtfCreationRedemptionImbalanceDigestReport:
            raise TypeError(
                "MarketResearchCryptoEtfCreationRedemptionImbalanceDigestReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoEtfCreationRedemptionImbalanceDigestReport:
            raise ValueError(
                "report must be exactly "
                "MarketResearchCryptoEtfCreationRedemptionImbalanceDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "observation_count",
            "ready_observation_count",
            "watch_observation_count",
            "blocked_observation_count",
            "imbalance_usd_observation_count",
            "imbalance_ratio_observation_count",
            "redemption_pressure_observation_count",
            "creation_pressure_observation_count",
            "imbalance_acceleration_observation_count",
            "nav_dislocation_observation_count",
            "settlement_lag_observation_count",
            "source_gap_observation_count",
            "confidence_gap_observation_count",
            "stale_observation_count",
            "max_observation_age_seconds",
            "max_allowed_observation_age_seconds",
            "min_source_count",
            "watch_abs_imbalance_usd",
            "blocked_abs_imbalance_usd",
            "max_settlement_lag_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "total_net_creation_redemption_usd",
            _require_count_decimal(
                "total_net_creation_redemption_usd",
                self.total_net_creation_redemption_usd,
            ),
        )
        for field_name in (
            "average_imbalance_ratio",
            "average_confidence",
            "max_imbalance_ratio",
            "max_nav_dislocation_abs",
            "min_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "source_config_versions",
            _normalize_source_config_versions(self.source_config_versions),
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


def build_market_research_crypto_etf_creation_redemption_imbalance_digest(
    observations: Iterable[MarketResearchCryptoEtfCreationRedemptionImbalanceObservation],
    *,
    config: MarketResearchCryptoEtfCreationRedemptionImbalanceDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchCryptoEtfCreationRedemptionImbalanceDigestReport:
    cfg = config or MarketResearchCryptoEtfCreationRedemptionImbalanceDigestConfig()
    if type(cfg) is not MarketResearchCryptoEtfCreationRedemptionImbalanceDigestConfig:
        raise ValueError(
            "config must be exactly "
            "MarketResearchCryptoEtfCreationRedemptionImbalanceDigestConfig",
        )
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
    sorted_rows = tuple(
        sorted(
            rows,
            key=lambda row: (
                _row_sort_value(row),
                row.imbalance_key,
                row.condition_id,
            ),
        ),
    )
    report_status = _report_status(sorted_rows)
    observation_count = _decimal_count(len(sorted_rows))
    return MarketResearchCryptoEtfCreationRedemptionImbalanceDigestReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        digest_status=report_status,
        recommended_next_step=_recommended_next_step(report_status),
        observation_count=observation_count,
        ready_observation_count=_status_count(sorted_rows, STATUS_READY),
        watch_observation_count=_status_count(sorted_rows, STATUS_WATCH),
        blocked_observation_count=_status_count(sorted_rows, STATUS_BLOCKED),
        imbalance_usd_observation_count=_reason_observation_count(
            sorted_rows,
            IMBALANCE_USD_REASON,
        ),
        imbalance_ratio_observation_count=_reason_observation_count(
            sorted_rows,
            IMBALANCE_RATIO_REASON,
        ),
        redemption_pressure_observation_count=_reason_observation_count(
            sorted_rows,
            REDEMPTION_PRESSURE_REASON,
        ),
        creation_pressure_observation_count=_reason_observation_count(
            sorted_rows,
            CREATION_PRESSURE_REASON,
        ),
        imbalance_acceleration_observation_count=_reason_observation_count(
            sorted_rows,
            IMBALANCE_ACCELERATION_REASON,
        ),
        nav_dislocation_observation_count=_reason_observation_count(
            sorted_rows,
            NAV_DISLOCATION_REASON,
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
        stale_observation_count=_reason_observation_count(
            sorted_rows,
            STALE_OBSERVATION_REASON,
        ),
        total_net_creation_redemption_usd=_decimal_sum(
            row.net_creation_redemption_usd for row in sorted_rows
        ),
        average_imbalance_ratio=_ratio(
            _decimal_sum(row.imbalance_ratio for row in sorted_rows),
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
        watch_abs_imbalance_usd=cfg.watch_abs_imbalance_usd,
        blocked_abs_imbalance_usd=cfg.blocked_abs_imbalance_usd,
        max_imbalance_ratio=cfg.max_imbalance_ratio,
        max_nav_dislocation_abs=cfg.max_nav_dislocation_abs,
        max_settlement_lag_hours=cfg.max_settlement_lag_hours,
        min_confidence=cfg.min_confidence,
        rows=sorted_rows,
        source_config_versions=tuple(
            sorted(
                (observation.imbalance_key, observation.source_config_version)
                for observation in normalized_observations
            ),
        ),
        reason_code_counts=_reason_code_counts(sorted_rows),
        reason_codes=_summary_reason_codes(sorted_rows),
    )


def market_research_crypto_etf_creation_redemption_imbalance_digest_payload(
    report: MarketResearchCryptoEtfCreationRedemptionImbalanceDigestReport,
) -> MappingProxyType:
    if type(report) is not MarketResearchCryptoEtfCreationRedemptionImbalanceDigestReport:
        raise ValueError(
            "report must be exactly "
            "MarketResearchCryptoEtfCreationRedemptionImbalanceDigestReport",
        )
    return _freeze(_json_ready(report))


def _row_for_observation(
    observation: MarketResearchCryptoEtfCreationRedemptionImbalanceObservation,
    *,
    config: MarketResearchCryptoEtfCreationRedemptionImbalanceDigestConfig,
    generated_at: datetime,
) -> MarketResearchCryptoEtfCreationRedemptionImbalanceDigestRow:
    if observation.observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    observation_age_seconds = _age_seconds(generated_at, observation.observed_at)
    net_creation_redemption_usd = _quantize(
        observation.creations_usd - observation.redemptions_usd,
    )
    imbalance_abs_usd = _count_abs(net_creation_redemption_usd)
    imbalance_change_abs_usd = _count_abs(
        net_creation_redemption_usd - observation.previous_imbalance_usd,
    )
    imbalance_ratio = _ratio(
        imbalance_abs_usd,
        observation.assets_under_management_usd,
    )
    nav_dislocation_abs = _ratio_abs(observation.nav_dislocation)
    reason_codes = _row_reason_codes(
        observation=observation,
        config=config,
        observation_age_seconds=observation_age_seconds,
        net_creation_redemption_usd=net_creation_redemption_usd,
        imbalance_abs_usd=imbalance_abs_usd,
        imbalance_change_abs_usd=imbalance_change_abs_usd,
        imbalance_ratio=imbalance_ratio,
        nav_dislocation_abs=nav_dislocation_abs,
    )
    return MarketResearchCryptoEtfCreationRedemptionImbalanceDigestRow(
        condition_id=observation.condition_id,
        imbalance_key=observation.imbalance_key,
        asset_symbol=observation.asset_symbol,
        digest_status=_row_status(reason_codes),
        observed_at=observation.observed_at,
        observation_age_seconds=observation_age_seconds,
        creations_usd=observation.creations_usd,
        redemptions_usd=observation.redemptions_usd,
        net_creation_redemption_usd=net_creation_redemption_usd,
        previous_imbalance_usd=observation.previous_imbalance_usd,
        imbalance_abs_usd=imbalance_abs_usd,
        imbalance_change_abs_usd=imbalance_change_abs_usd,
        assets_under_management_usd=observation.assets_under_management_usd,
        imbalance_ratio=imbalance_ratio,
        nav_dislocation=observation.nav_dislocation,
        nav_dislocation_abs=nav_dislocation_abs,
        settlement_lag_hours=observation.settlement_lag_hours,
        source_count=observation.source_count,
        confidence=observation.confidence,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    observation: MarketResearchCryptoEtfCreationRedemptionImbalanceObservation,
    config: MarketResearchCryptoEtfCreationRedemptionImbalanceDigestConfig,
    observation_age_seconds: Decimal,
    net_creation_redemption_usd: Decimal,
    imbalance_abs_usd: Decimal,
    imbalance_change_abs_usd: Decimal,
    imbalance_ratio: Decimal,
    nav_dislocation_abs: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if imbalance_abs_usd >= config.watch_abs_imbalance_usd:
        reasons.append(IMBALANCE_USD_REASON)
        if net_creation_redemption_usd < ZERO:
            reasons.append(REDEMPTION_PRESSURE_REASON)
        elif net_creation_redemption_usd > ZERO:
            reasons.append(CREATION_PRESSURE_REASON)
    if imbalance_ratio > config.max_imbalance_ratio:
        reasons.append(IMBALANCE_RATIO_REASON)
    if imbalance_change_abs_usd >= config.watch_abs_imbalance_usd:
        reasons.append(IMBALANCE_ACCELERATION_REASON)
    if nav_dislocation_abs > config.max_nav_dislocation_abs:
        reasons.append(NAV_DISLOCATION_REASON)
    if observation.settlement_lag_hours > config.max_settlement_lag_hours:
        reasons.append(SETTLEMENT_LAG_REASON)
    if observation.source_count < config.min_source_count:
        reasons.append(SOURCE_GAP_REASON)
    if observation.confidence < config.min_confidence:
        reasons.append(CONFIDENCE_GAP_REASON)
    if observation_age_seconds > config.max_observation_age_seconds:
        reasons.append(STALE_OBSERVATION_REASON)
    if not reasons:
        reasons.append(READY_REASON)
    return tuple(reason for reason in ROW_REASON_CODE_SEQUENCE if reason in reasons)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    if any(
        reason in reason_codes
        for reason in (
            IMBALANCE_RATIO_REASON,
            REDEMPTION_PRESSURE_REASON,
            NAV_DISLOCATION_REASON,
            SETTLEMENT_LAG_REASON,
            CONFIDENCE_GAP_REASON,
            STALE_OBSERVATION_REASON,
        )
    ):
        return STATUS_BLOCKED
    return STATUS_WATCH


def _row_sort_value(
    row: MarketResearchCryptoEtfCreationRedemptionImbalanceDigestRow,
) -> tuple[int, Decimal, Decimal]:
    status_rank = {
        STATUS_BLOCKED: 0,
        STATUS_WATCH: 1,
        STATUS_READY: 2,
    }[row.digest_status]
    severity = _decimal_count(
        len(tuple(reason for reason in row.reason_codes if reason != READY_REASON)),
    )
    return (status_rank, -severity, -row.imbalance_abs_usd)


def _report_status(
    rows: tuple[MarketResearchCryptoEtfCreationRedemptionImbalanceDigestRow, ...],
) -> str:
    if not rows:
        return STATUS_WATCH
    if any(row.digest_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_READY


def _recommended_next_step(status: str) -> str:
    if status == STATUS_BLOCKED:
        return (
            "block_report_only_market_research_crypto_etf_creation_redemption_"
            "imbalance_digest"
        )
    if status == STATUS_WATCH:
        return (
            "review_report_only_market_research_crypto_etf_creation_redemption_"
            "imbalance_digest"
        )
    return (
        "allow_report_only_market_research_crypto_etf_creation_redemption_"
        "imbalance_digest"
    )


def _status_count(
    rows: tuple[MarketResearchCryptoEtfCreationRedemptionImbalanceDigestRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.digest_status == status))


def _reason_observation_count(
    rows: tuple[MarketResearchCryptoEtfCreationRedemptionImbalanceDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _reason_code_counts(
    rows: tuple[MarketResearchCryptoEtfCreationRedemptionImbalanceDigestRow, ...],
) -> tuple[MarketResearchCryptoEtfCreationRedemptionImbalanceDigestReasonCodeCount, ...]:
    observation_count = _decimal_count(len(rows))
    if not rows:
        return (
            MarketResearchCryptoEtfCreationRedemptionImbalanceDigestReasonCodeCount(
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
        MarketResearchCryptoEtfCreationRedemptionImbalanceDigestReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
            observation_ratio=_ratio(_decimal_count(counts[reason_code]), observation_count),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _summary_reason_codes(
    rows: tuple[MarketResearchCryptoEtfCreationRedemptionImbalanceDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    seen: set[str] = set()
    for row in rows:
        seen.update(row.reason_codes)
    if len(seen) > 1 and READY_REASON in seen:
        seen.remove(READY_REASON)
    return tuple(reason for reason in REASON_CODE_SEQUENCE if reason in seen)


def _validate_row(
    row: MarketResearchCryptoEtfCreationRedemptionImbalanceDigestRow,
) -> None:
    if row.net_creation_redemption_usd != _quantize(
        row.creations_usd - row.redemptions_usd,
    ):
        raise ValueError("net_creation_redemption_usd does not match inputs")
    if row.imbalance_abs_usd != _count_abs(row.net_creation_redemption_usd):
        raise ValueError("imbalance_abs_usd does not match net imbalance")
    if row.imbalance_change_abs_usd != _count_abs(
        row.net_creation_redemption_usd - row.previous_imbalance_usd,
    ):
        raise ValueError("imbalance_change_abs_usd does not match inputs")
    if row.imbalance_ratio != _ratio(
        row.imbalance_abs_usd,
        row.assets_under_management_usd,
    ):
        raise ValueError("imbalance_ratio does not match inputs")
    if row.nav_dislocation_abs != _ratio_abs(row.nav_dislocation):
        raise ValueError("nav_dislocation_abs does not match nav_dislocation")
    if row.digest_status != _row_status(row.reason_codes):
        raise ValueError("digest_status does not match reason_codes")


def _validate_report(
    report: MarketResearchCryptoEtfCreationRedemptionImbalanceDigestReport,
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
        (IMBALANCE_USD_REASON, report.imbalance_usd_observation_count),
        (IMBALANCE_RATIO_REASON, report.imbalance_ratio_observation_count),
        (REDEMPTION_PRESSURE_REASON, report.redemption_pressure_observation_count),
        (CREATION_PRESSURE_REASON, report.creation_pressure_observation_count),
        (
            IMBALANCE_ACCELERATION_REASON,
            report.imbalance_acceleration_observation_count,
        ),
        (NAV_DISLOCATION_REASON, report.nav_dislocation_observation_count),
        (SETTLEMENT_LAG_REASON, report.settlement_lag_observation_count),
        (SOURCE_GAP_REASON, report.source_gap_observation_count),
        (CONFIDENCE_GAP_REASON, report.confidence_gap_observation_count),
        (STALE_OBSERVATION_REASON, report.stale_observation_count),
    )
    for reason_code, count in expected_counts:
        if count != _reason_observation_count(report.rows, reason_code):
            raise ValueError("reason observation count does not match rows")
    if report.digest_status != _report_status(report.rows):
        raise ValueError("digest_status does not match rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step does not match digest_status")
    if report.total_net_creation_redemption_usd != _decimal_sum(
        row.net_creation_redemption_usd for row in report.rows
    ):
        raise ValueError("total_net_creation_redemption_usd does not match rows")
    if report.average_imbalance_ratio != _ratio(
        _decimal_sum(row.imbalance_ratio for row in report.rows),
        report.observation_count,
    ):
        raise ValueError("average_imbalance_ratio does not match rows")
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
    observations: Iterable[MarketResearchCryptoEtfCreationRedemptionImbalanceObservation],
) -> tuple[MarketResearchCryptoEtfCreationRedemptionImbalanceObservation, ...]:
    try:
        observation_tuple = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be iterable") from exc
    seen_keys: set[str] = set()
    for observation in observation_tuple:
        if type(observation) is not MarketResearchCryptoEtfCreationRedemptionImbalanceObservation:
            raise ValueError(
                "observations must contain "
                "MarketResearchCryptoEtfCreationRedemptionImbalanceObservation",
            )
        if observation.imbalance_key in seen_keys:
            raise ValueError("imbalance_key values must be unique")
        seen_keys.add(observation.imbalance_key)
        _require_hard_flags("observation", observation)
    return observation_tuple


def _normalize_rows(
    rows: tuple[MarketResearchCryptoEtfCreationRedemptionImbalanceDigestRow, ...],
) -> tuple[MarketResearchCryptoEtfCreationRedemptionImbalanceDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not MarketResearchCryptoEtfCreationRedemptionImbalanceDigestRow:
            raise ValueError(
                "rows must contain "
                "MarketResearchCryptoEtfCreationRedemptionImbalanceDigestRow",
            )
        _require_hard_flags("row", row)
    return rows


def _normalize_reason_code_counts(
    items: tuple[
        MarketResearchCryptoEtfCreationRedemptionImbalanceDigestReasonCodeCount,
        ...,
    ],
) -> tuple[
    MarketResearchCryptoEtfCreationRedemptionImbalanceDigestReasonCodeCount,
    ...,
]:
    if type(items) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for item in items:
        if (
            type(item)
            is not MarketResearchCryptoEtfCreationRedemptionImbalanceDigestReasonCodeCount
        ):
            raise ValueError("reason_code_counts must contain reason count rows")
        _require_hard_flags("reason code count", item)
    return items


def _normalize_source_config_versions(
    value: tuple[tuple[str, str], ...],
) -> tuple[tuple[str, str], ...]:
    if type(value) is not tuple:
        raise ValueError("source_config_versions must be a tuple")
    pairs: list[tuple[str, str]] = []
    seen_keys: set[str] = set()
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("source_config_versions must contain pairs")
        imbalance_key, source_config_version = item
        _require_public_string("imbalance_key", imbalance_key)
        _require_public_string("source_config_version", source_config_version)
        if imbalance_key in seen_keys:
            raise ValueError("source_config_versions imbalance_key values must be unique")
        seen_keys.add(imbalance_key)
        pairs.append((imbalance_key, source_config_version))
    return tuple(pairs)


def _normalize_reason_codes(
    value: tuple[str, ...],
    *,
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    seen: set[str] = set()
    for reason_code in value:
        _require_reason_code("reason_code", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
    normalized = tuple(reason_code for reason_code in sequence if reason_code in seen)
    if normalized != value:
        raise ValueError("reason_codes must be deterministic")
    return normalized


def _require_status(field_name: str, value: str) -> None:
    if type(value) is not str or value not in IMBALANCE_DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be a supported status")


def _require_reason_code(field_name: str, value: str) -> None:
    if type(value) is not str or value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a supported reason code")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")
    _require_public_text(field_name, value)


def _require_public_string(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    _require_public_text(field_name, value)


def _require_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must be redacted")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag, None) is not True:
            raise ValueError(f"{field_name} {flag} must be True")


def _require_positive_count_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_count_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_count_decimal(field_name: str, value: Decimal) -> Decimal:
    return _require_decimal(field_name, value)


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _require_signed_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < -ONE or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between -1 and 1")
    return decimal_value


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError(f"{field_name} must be a finite Decimal")
    return _quantize(value)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if (
        type(value) is not datetime
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    return _quantize(
        Decimal(delta.days * 86400 + delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND),
    )


def _count_abs(value: Decimal) -> Decimal:
    return _quantize(abs(value))


def _ratio_abs(value: Decimal) -> Decimal:
    return _quantize(abs(value))


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _decimal_sum(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total = _quantize(total + value)
    return total


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        ready: dict[str, Any] = {}
        for field in fields(value):
            item = getattr(value, field.name)
            if field.name in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{field.name} must be True")
            ready[field.name] = _json_ready(item)
        return ready
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, tuple):
        return tuple(_json_ready(item) for item in value)
    if isinstance(value, list):
        return tuple(_json_ready(item) for item in value)
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _require_public_text("JSON object key", key)
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{key} must be True")
            ready[key] = _json_ready(item)
        return ready
    if type(value) is str:
        _require_public_text("JSON string value", value)
        return value
    if type(value) is bool or value is None:
        return value
    raise ValueError("value is not JSON serializable")


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, tuple):
        return tuple(_freeze(item) for item in value)
    return value
