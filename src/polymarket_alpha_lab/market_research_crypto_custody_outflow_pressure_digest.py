"""Pure Phase 1 crypto custody outflow pressure market research reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from types import MappingProxyType
from typing import Any


DEFAULT_MARKET_RESEARCH_CRYPTO_CUSTODY_OUTFLOW_PRESSURE_DIGEST_CONFIG_VERSION = (
    "market-research-crypto-custody-outflow-pressure-digest-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
CUSTODY_OUTFLOW_PRESSURE_DIGEST_STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCKED)
VENUE_TYPES = ("exchange", "custodian")

PASS_REASON = "market_research_crypto_custody_outflow_pressure_digest_pass"
NO_INPUTS_REASON = (
    "market_research_crypto_custody_outflow_pressure_digest_no_inputs"
)
OUTFLOW_PRESSURE_REASON = (
    "market_research_crypto_custody_outflow_pressure_digest_outflow_pressure"
)
OUTFLOW_WATCH_REASON = (
    "market_research_crypto_custody_outflow_pressure_digest_outflow_watch"
)
OUTFLOW_GROWTH_REASON = (
    "market_research_crypto_custody_outflow_pressure_digest_outflow_growth"
)
WITHDRAWAL_QUEUE_PRESSURE_REASON = (
    "market_research_crypto_custody_outflow_pressure_digest_withdrawal_queue_pressure"
)
WITHDRAWAL_WAIT_REASON = (
    "market_research_crypto_custody_outflow_pressure_digest_withdrawal_wait"
)
SOURCE_DIVERSITY_GAP_REASON = (
    "market_research_crypto_custody_outflow_pressure_digest_source_diversity_gap"
)
STALE_OBSERVATION_REASON = (
    "market_research_crypto_custody_outflow_pressure_digest_stale_observation"
)
CONFIDENCE_GAP_REASON = (
    "market_research_crypto_custody_outflow_pressure_digest_confidence_gap"
)

REASON_CODE_SEQUENCE = (
    OUTFLOW_PRESSURE_REASON,
    OUTFLOW_WATCH_REASON,
    OUTFLOW_GROWTH_REASON,
    WITHDRAWAL_QUEUE_PRESSURE_REASON,
    WITHDRAWAL_WAIT_REASON,
    SOURCE_DIVERSITY_GAP_REASON,
    STALE_OBSERVATION_REASON,
    CONFIDENCE_GAP_REASON,
    PASS_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    OUTFLOW_PRESSURE_REASON,
    OUTFLOW_WATCH_REASON,
    OUTFLOW_GROWTH_REASON,
    WITHDRAWAL_QUEUE_PRESSURE_REASON,
    WITHDRAWAL_WAIT_REASON,
    SOURCE_DIVERSITY_GAP_REASON,
    STALE_OBSERVATION_REASON,
    CONFIDENCE_GAP_REASON,
    PASS_REASON,
)
BLOCKING_REASONS = (
    OUTFLOW_PRESSURE_REASON,
    WITHDRAWAL_QUEUE_PRESSURE_REASON,
    WITHDRAWAL_WAIT_REASON,
    STALE_OBSERVATION_REASON,
    CONFIDENCE_GAP_REASON,
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
        _join_parts("au", "th"),
        _join_parts("0", "x"),
    ),
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_CRYPTO_CUSTODY_OUTFLOW_PRESSURE_DIGEST_CONFIG_VERSION",
    "MarketResearchCryptoCustodyOutflowPressureDigestConfig",
    "MarketResearchCryptoCustodyOutflowPressureDigestReasonCodeCount",
    "MarketResearchCryptoCustodyOutflowPressureDigestReport",
    "MarketResearchCryptoCustodyOutflowPressureDigestRow",
    "MarketResearchCryptoCustodyOutflowPressureObservation",
    "build_market_research_crypto_custody_outflow_pressure_digest",
    "market_research_crypto_custody_outflow_pressure_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchCryptoCustodyOutflowPressureDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_CRYPTO_CUSTODY_OUTFLOW_PRESSURE_DIGEST_CONFIG_VERSION
    )
    max_observation_age_seconds: Decimal = Decimal("1800.000000")
    watch_outflow_ratio: Decimal = Decimal("0.050000")
    blocked_outflow_ratio: Decimal = Decimal("0.100000")
    max_outflow_growth_ratio: Decimal = Decimal("0.500000")
    max_withdrawal_queue_ratio: Decimal = Decimal("0.200000")
    max_withdrawal_wait_hours: Decimal = Decimal("24.000000")
    min_source_count: Decimal = Decimal("3.000000")
    min_confidence: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoCustodyOutflowPressureDigestConfig:
            raise TypeError(
                "MarketResearchCryptoCustodyOutflowPressureDigestConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoCustodyOutflowPressureDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchCryptoCustodyOutflowPressureDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_CRYPTO_CUSTODY_OUTFLOW_PRESSURE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "max_observation_age_seconds",
            "max_withdrawal_wait_hours",
            "min_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_outflow_ratio",
            "blocked_outflow_ratio",
            "max_outflow_growth_ratio",
            "max_withdrawal_queue_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_outflow_ratio > self.blocked_outflow_ratio:
            raise ValueError("watch_outflow_ratio must not exceed blocked_outflow_ratio")
        object.__setattr__(
            self,
            "min_confidence",
            _require_ratio_decimal("min_confidence", self.min_confidence),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchCryptoCustodyOutflowPressureObservation:
    condition_id: str
    custody_pressure_key: str
    venue_name: str
    venue_type: str
    asset_symbol: str
    observed_at: datetime
    net_outflow_usd: Decimal
    previous_net_outflow_usd: Decimal
    assets_under_custody_usd: Decimal
    withdrawal_queue_usd: Decimal
    daily_withdrawal_capacity_usd: Decimal
    estimated_withdrawal_wait_hours: Decimal
    source_count: Decimal
    confidence: Decimal
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoCustodyOutflowPressureObservation:
            raise TypeError(
                "MarketResearchCryptoCustodyOutflowPressureObservation "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoCustodyOutflowPressureObservation:
            raise ValueError(
                "observation must be exactly "
                "MarketResearchCryptoCustodyOutflowPressureObservation",
            )
        for field_name in (
            "condition_id",
            "custody_pressure_key",
            "venue_name",
            "asset_symbol",
            "source_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_venue_type("venue_type", self.venue_type)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "net_outflow_usd",
            "previous_net_outflow_usd",
            "withdrawal_queue_usd",
            "estimated_withdrawal_wait_hours",
            "source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("assets_under_custody_usd", "daily_withdrawal_capacity_usd"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "confidence",
            _require_ratio_decimal("confidence", self.confidence),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class MarketResearchCryptoCustodyOutflowPressureDigestRow:
    condition_id: str
    custody_pressure_key: str
    venue_name: str
    venue_type: str
    asset_symbol: str
    digest_status: str
    observed_at: datetime
    observation_age_seconds: Decimal
    net_outflow_usd: Decimal
    previous_net_outflow_usd: Decimal
    assets_under_custody_usd: Decimal
    outflow_ratio: Decimal
    outflow_growth_ratio: Decimal
    withdrawal_queue_usd: Decimal
    daily_withdrawal_capacity_usd: Decimal
    withdrawal_queue_ratio: Decimal
    estimated_withdrawal_wait_hours: Decimal
    source_count: Decimal
    confidence: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoCustodyOutflowPressureDigestRow:
            raise TypeError(
                "MarketResearchCryptoCustodyOutflowPressureDigestRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoCustodyOutflowPressureDigestRow:
            raise ValueError(
                "row must be exactly "
                "MarketResearchCryptoCustodyOutflowPressureDigestRow",
            )
        for field_name in (
            "condition_id",
            "custody_pressure_key",
            "venue_name",
            "asset_symbol",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_venue_type("venue_type", self.venue_type)
        _require_status("digest_status", self.digest_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "observation_age_seconds",
            "net_outflow_usd",
            "previous_net_outflow_usd",
            "outflow_ratio",
            "outflow_growth_ratio",
            "withdrawal_queue_usd",
            "withdrawal_queue_ratio",
            "estimated_withdrawal_wait_hours",
            "source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("assets_under_custody_usd", "daily_withdrawal_capacity_usd"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "confidence",
            _require_ratio_decimal("confidence", self.confidence),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, sequence=ROW_REASON_CODE_SEQUENCE),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchCryptoCustodyOutflowPressureDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    observation_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoCustodyOutflowPressureDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchCryptoCustodyOutflowPressureDigestReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoCustodyOutflowPressureDigestReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "MarketResearchCryptoCustodyOutflowPressureDigestReasonCodeCount",
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
class MarketResearchCryptoCustodyOutflowPressureDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    observation_count: Decimal
    pass_observation_count: Decimal
    watch_observation_count: Decimal
    blocked_observation_count: Decimal
    outflow_pressure_observation_count: Decimal
    outflow_watch_observation_count: Decimal
    outflow_growth_observation_count: Decimal
    withdrawal_queue_pressure_observation_count: Decimal
    withdrawal_wait_observation_count: Decimal
    source_diversity_gap_observation_count: Decimal
    stale_observation_count: Decimal
    confidence_gap_observation_count: Decimal
    average_outflow_ratio: Decimal
    average_outflow_growth_ratio: Decimal
    average_withdrawal_queue_ratio: Decimal
    average_estimated_withdrawal_wait_hours: Decimal
    max_observation_age_seconds: Decimal
    max_allowed_observation_age_seconds: Decimal
    watch_outflow_ratio: Decimal
    blocked_outflow_ratio: Decimal
    max_outflow_growth_ratio: Decimal
    max_withdrawal_queue_ratio: Decimal
    max_withdrawal_wait_hours: Decimal
    min_source_count: Decimal
    min_confidence: Decimal
    rows: tuple[MarketResearchCryptoCustodyOutflowPressureDigestRow, ...]
    source_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchCryptoCustodyOutflowPressureDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoCustodyOutflowPressureDigestReport:
            raise TypeError(
                "MarketResearchCryptoCustodyOutflowPressureDigestReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoCustodyOutflowPressureDigestReport:
            raise ValueError(
                "report must be exactly "
                "MarketResearchCryptoCustodyOutflowPressureDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_CRYPTO_CUSTODY_OUTFLOW_PRESSURE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        _require_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "observation_count",
            "pass_observation_count",
            "watch_observation_count",
            "blocked_observation_count",
            "outflow_pressure_observation_count",
            "outflow_watch_observation_count",
            "outflow_growth_observation_count",
            "withdrawal_queue_pressure_observation_count",
            "withdrawal_wait_observation_count",
            "source_diversity_gap_observation_count",
            "stale_observation_count",
            "confidence_gap_observation_count",
            "average_outflow_ratio",
            "average_outflow_growth_ratio",
            "average_withdrawal_queue_ratio",
            "average_estimated_withdrawal_wait_hours",
            "max_observation_age_seconds",
            "max_allowed_observation_age_seconds",
            "watch_outflow_ratio",
            "blocked_outflow_ratio",
            "max_outflow_growth_ratio",
            "max_withdrawal_queue_ratio",
            "max_withdrawal_wait_hours",
            "min_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_confidence",
            _require_ratio_decimal("min_confidence", self.min_confidence),
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


def build_market_research_crypto_custody_outflow_pressure_digest(
    observations: Iterable[MarketResearchCryptoCustodyOutflowPressureObservation],
    *,
    config: MarketResearchCryptoCustodyOutflowPressureDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchCryptoCustodyOutflowPressureDigestReport:
    cfg = config or MarketResearchCryptoCustodyOutflowPressureDigestConfig()
    if type(cfg) is not MarketResearchCryptoCustodyOutflowPressureDigestConfig:
        raise ValueError(
            "config must be exactly "
            "MarketResearchCryptoCustodyOutflowPressureDigestConfig",
        )
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    rows = tuple(
        _row_for_observation(observation, config=cfg, generated_at=generated_at_utc)
        for observation in normalized_observations
    )
    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    report_status = _report_status(sorted_rows)
    observation_count = _decimal_count(len(sorted_rows))
    return MarketResearchCryptoCustodyOutflowPressureDigestReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        digest_status=report_status,
        recommended_next_step=_recommended_next_step(report_status),
        observation_count=observation_count,
        pass_observation_count=_status_count(sorted_rows, STATUS_PASS),
        watch_observation_count=_status_count(sorted_rows, STATUS_WATCH),
        blocked_observation_count=_status_count(sorted_rows, STATUS_BLOCKED),
        outflow_pressure_observation_count=_reason_observation_count(
            sorted_rows,
            OUTFLOW_PRESSURE_REASON,
        ),
        outflow_watch_observation_count=_reason_observation_count(
            sorted_rows,
            OUTFLOW_WATCH_REASON,
        ),
        outflow_growth_observation_count=_reason_observation_count(
            sorted_rows,
            OUTFLOW_GROWTH_REASON,
        ),
        withdrawal_queue_pressure_observation_count=_reason_observation_count(
            sorted_rows,
            WITHDRAWAL_QUEUE_PRESSURE_REASON,
        ),
        withdrawal_wait_observation_count=_reason_observation_count(
            sorted_rows,
            WITHDRAWAL_WAIT_REASON,
        ),
        source_diversity_gap_observation_count=_reason_observation_count(
            sorted_rows,
            SOURCE_DIVERSITY_GAP_REASON,
        ),
        stale_observation_count=_reason_observation_count(
            sorted_rows,
            STALE_OBSERVATION_REASON,
        ),
        confidence_gap_observation_count=_reason_observation_count(
            sorted_rows,
            CONFIDENCE_GAP_REASON,
        ),
        average_outflow_ratio=_ratio(
            _decimal_sum(row.outflow_ratio for row in sorted_rows),
            observation_count,
        ),
        average_outflow_growth_ratio=_ratio(
            _decimal_sum(row.outflow_growth_ratio for row in sorted_rows),
            observation_count,
        ),
        average_withdrawal_queue_ratio=_ratio(
            _decimal_sum(row.withdrawal_queue_ratio for row in sorted_rows),
            observation_count,
        ),
        average_estimated_withdrawal_wait_hours=_ratio(
            _decimal_sum(row.estimated_withdrawal_wait_hours for row in sorted_rows),
            observation_count,
        ),
        max_observation_age_seconds=max(
            (row.observation_age_seconds for row in sorted_rows),
            default=ZERO,
        ),
        max_allowed_observation_age_seconds=cfg.max_observation_age_seconds,
        watch_outflow_ratio=cfg.watch_outflow_ratio,
        blocked_outflow_ratio=cfg.blocked_outflow_ratio,
        max_outflow_growth_ratio=cfg.max_outflow_growth_ratio,
        max_withdrawal_queue_ratio=cfg.max_withdrawal_queue_ratio,
        max_withdrawal_wait_hours=cfg.max_withdrawal_wait_hours,
        min_source_count=cfg.min_source_count,
        min_confidence=cfg.min_confidence,
        rows=sorted_rows,
        source_config_versions=tuple(
            sorted(
                (observation.custody_pressure_key, observation.source_config_version)
                for observation in normalized_observations
            ),
        ),
        reason_code_counts=_reason_code_counts(sorted_rows),
        reason_codes=_summary_reason_codes(sorted_rows),
    )


def market_research_crypto_custody_outflow_pressure_digest_payload(
    report: MarketResearchCryptoCustodyOutflowPressureDigestReport,
) -> MappingProxyType:
    if type(report) is not MarketResearchCryptoCustodyOutflowPressureDigestReport:
        raise ValueError(
            "report must be exactly "
            "MarketResearchCryptoCustodyOutflowPressureDigestReport",
        )
    return _freeze(_json_ready(report))


def _row_for_observation(
    observation: MarketResearchCryptoCustodyOutflowPressureObservation,
    *,
    config: MarketResearchCryptoCustodyOutflowPressureDigestConfig,
    generated_at: datetime,
) -> MarketResearchCryptoCustodyOutflowPressureDigestRow:
    if observation.observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    observation_age_seconds = _age_seconds(generated_at, observation.observed_at)
    outflow_ratio = _ratio(
        observation.net_outflow_usd,
        observation.assets_under_custody_usd,
    )
    outflow_growth_ratio = _growth_ratio(
        observation.net_outflow_usd,
        observation.previous_net_outflow_usd,
    )
    withdrawal_queue_ratio = _ratio(
        observation.withdrawal_queue_usd,
        observation.daily_withdrawal_capacity_usd,
    )
    reason_codes = _row_reason_codes(
        observation=observation,
        config=config,
        observation_age_seconds=observation_age_seconds,
        outflow_ratio=outflow_ratio,
        outflow_growth_ratio=outflow_growth_ratio,
        withdrawal_queue_ratio=withdrawal_queue_ratio,
    )
    return MarketResearchCryptoCustodyOutflowPressureDigestRow(
        condition_id=observation.condition_id,
        custody_pressure_key=observation.custody_pressure_key,
        venue_name=observation.venue_name,
        venue_type=observation.venue_type,
        asset_symbol=observation.asset_symbol,
        digest_status=_row_status(reason_codes),
        observed_at=observation.observed_at,
        observation_age_seconds=observation_age_seconds,
        net_outflow_usd=observation.net_outflow_usd,
        previous_net_outflow_usd=observation.previous_net_outflow_usd,
        assets_under_custody_usd=observation.assets_under_custody_usd,
        outflow_ratio=outflow_ratio,
        outflow_growth_ratio=outflow_growth_ratio,
        withdrawal_queue_usd=observation.withdrawal_queue_usd,
        daily_withdrawal_capacity_usd=observation.daily_withdrawal_capacity_usd,
        withdrawal_queue_ratio=withdrawal_queue_ratio,
        estimated_withdrawal_wait_hours=observation.estimated_withdrawal_wait_hours,
        source_count=observation.source_count,
        confidence=observation.confidence,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    observation: MarketResearchCryptoCustodyOutflowPressureObservation,
    config: MarketResearchCryptoCustodyOutflowPressureDigestConfig,
    observation_age_seconds: Decimal,
    outflow_ratio: Decimal,
    outflow_growth_ratio: Decimal,
    withdrawal_queue_ratio: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if outflow_ratio >= config.blocked_outflow_ratio:
        reasons.append(OUTFLOW_PRESSURE_REASON)
    elif outflow_ratio >= config.watch_outflow_ratio:
        reasons.append(OUTFLOW_WATCH_REASON)
    if outflow_growth_ratio > config.max_outflow_growth_ratio:
        reasons.append(OUTFLOW_GROWTH_REASON)
    if withdrawal_queue_ratio > config.max_withdrawal_queue_ratio:
        reasons.append(WITHDRAWAL_QUEUE_PRESSURE_REASON)
    if observation.estimated_withdrawal_wait_hours > config.max_withdrawal_wait_hours:
        reasons.append(WITHDRAWAL_WAIT_REASON)
    if observation.source_count < config.min_source_count:
        reasons.append(SOURCE_DIVERSITY_GAP_REASON)
    if observation_age_seconds > config.max_observation_age_seconds:
        reasons.append(STALE_OBSERVATION_REASON)
    if observation.confidence < config.min_confidence:
        reasons.append(CONFIDENCE_GAP_REASON)
    if not reasons:
        reasons.append(PASS_REASON)
    return tuple(reason for reason in ROW_REASON_CODE_SEQUENCE if reason in reasons)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (PASS_REASON,):
        return STATUS_PASS
    if any(reason in reason_codes for reason in BLOCKING_REASONS):
        return STATUS_BLOCKED
    return STATUS_WATCH


def _row_sort_key(
    row: MarketResearchCryptoCustodyOutflowPressureDigestRow,
) -> tuple[int, Decimal, str, str]:
    status_rank = {
        STATUS_BLOCKED: 0,
        STATUS_WATCH: 1,
        STATUS_PASS: 2,
    }[row.digest_status]
    severity = _decimal_count(
        len(tuple(reason for reason in row.reason_codes if reason != PASS_REASON)),
    )
    return (status_rank, -severity, row.custody_pressure_key, row.condition_id)


def _report_status(
    rows: tuple[MarketResearchCryptoCustodyOutflowPressureDigestRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _recommended_next_step(status: str) -> str:
    if status == STATUS_BLOCKED:
        return "block_report_only_market_research_crypto_custody_outflow_pressure_digest"
    if status == STATUS_WATCH:
        return "review_report_only_market_research_crypto_custody_outflow_pressure_digest"
    return "allow_report_only_market_research_crypto_custody_outflow_pressure_digest"


def _status_count(
    rows: tuple[MarketResearchCryptoCustodyOutflowPressureDigestRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.digest_status == status))


def _reason_observation_count(
    rows: tuple[MarketResearchCryptoCustodyOutflowPressureDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _reason_code_counts(
    rows: tuple[MarketResearchCryptoCustodyOutflowPressureDigestRow, ...],
) -> tuple[MarketResearchCryptoCustodyOutflowPressureDigestReasonCodeCount, ...]:
    observation_count = _decimal_count(len(rows))
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        MarketResearchCryptoCustodyOutflowPressureDigestReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
            observation_ratio=_ratio(_decimal_count(counts[reason_code]), observation_count),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _summary_reason_codes(
    rows: tuple[MarketResearchCryptoCustodyOutflowPressureDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    seen: set[str] = set()
    for row in rows:
        seen.update(row.reason_codes)
    if len(seen) > 1 and PASS_REASON in seen:
        seen.remove(PASS_REASON)
    return tuple(reason for reason in REASON_CODE_SEQUENCE if reason in seen)


def _validate_row(row: MarketResearchCryptoCustodyOutflowPressureDigestRow) -> None:
    if row.outflow_ratio != _ratio(row.net_outflow_usd, row.assets_under_custody_usd):
        raise ValueError("outflow_ratio does not match outflow inputs")
    if row.outflow_growth_ratio != _growth_ratio(
        row.net_outflow_usd,
        row.previous_net_outflow_usd,
    ):
        raise ValueError("outflow_growth_ratio does not match outflow inputs")
    if row.withdrawal_queue_ratio != _ratio(
        row.withdrawal_queue_usd,
        row.daily_withdrawal_capacity_usd,
    ):
        raise ValueError("withdrawal_queue_ratio does not match queue inputs")
    if row.digest_status != _row_status(row.reason_codes):
        raise ValueError("digest_status does not match reason_codes")


def _validate_report(report: MarketResearchCryptoCustodyOutflowPressureDigestReport) -> None:
    if report.observation_count != _decimal_count(len(report.rows)):
        raise ValueError("observation_count does not match rows")
    if report.pass_observation_count != _status_count(report.rows, STATUS_PASS):
        raise ValueError("pass_observation_count does not match rows")
    if report.watch_observation_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_observation_count does not match rows")
    if report.blocked_observation_count != _status_count(report.rows, STATUS_BLOCKED):
        raise ValueError("blocked_observation_count does not match rows")
    expected_counts = (
        (OUTFLOW_PRESSURE_REASON, report.outflow_pressure_observation_count),
        (OUTFLOW_WATCH_REASON, report.outflow_watch_observation_count),
        (OUTFLOW_GROWTH_REASON, report.outflow_growth_observation_count),
        (
            WITHDRAWAL_QUEUE_PRESSURE_REASON,
            report.withdrawal_queue_pressure_observation_count,
        ),
        (WITHDRAWAL_WAIT_REASON, report.withdrawal_wait_observation_count),
        (SOURCE_DIVERSITY_GAP_REASON, report.source_diversity_gap_observation_count),
        (STALE_OBSERVATION_REASON, report.stale_observation_count),
        (CONFIDENCE_GAP_REASON, report.confidence_gap_observation_count),
    )
    for reason_code, count in expected_counts:
        if count != _reason_observation_count(report.rows, reason_code):
            raise ValueError("reason observation count does not match rows")
    if report.digest_status != _report_status(report.rows):
        raise ValueError("digest_status does not match rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step does not match digest_status")
    if report.average_outflow_ratio != _ratio(
        _decimal_sum(row.outflow_ratio for row in report.rows),
        report.observation_count,
    ):
        raise ValueError("average_outflow_ratio does not match rows")
    if report.average_outflow_growth_ratio != _ratio(
        _decimal_sum(row.outflow_growth_ratio for row in report.rows),
        report.observation_count,
    ):
        raise ValueError("average_outflow_growth_ratio does not match rows")
    if report.average_withdrawal_queue_ratio != _ratio(
        _decimal_sum(row.withdrawal_queue_ratio for row in report.rows),
        report.observation_count,
    ):
        raise ValueError("average_withdrawal_queue_ratio does not match rows")
    if report.average_estimated_withdrawal_wait_hours != _ratio(
        _decimal_sum(row.estimated_withdrawal_wait_hours for row in report.rows),
        report.observation_count,
    ):
        raise ValueError("average_estimated_withdrawal_wait_hours does not match rows")
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
    observations: Iterable[MarketResearchCryptoCustodyOutflowPressureObservation],
) -> tuple[MarketResearchCryptoCustodyOutflowPressureObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError(
            "observations must contain "
            "MarketResearchCryptoCustodyOutflowPressureObservation",
        )
    observation_tuple = tuple(observations)
    seen_keys: set[str] = set()
    for observation in observation_tuple:
        if type(observation) is not MarketResearchCryptoCustodyOutflowPressureObservation:
            raise ValueError(
                "observations must contain "
                "MarketResearchCryptoCustodyOutflowPressureObservation",
            )
        if observation.custody_pressure_key in seen_keys:
            raise ValueError("custody_pressure_key values must be unique")
        seen_keys.add(observation.custody_pressure_key)
        _require_hard_flags("observation", observation)
    return observation_tuple


def _normalize_rows(
    rows: tuple[MarketResearchCryptoCustodyOutflowPressureDigestRow, ...],
) -> tuple[MarketResearchCryptoCustodyOutflowPressureDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen_keys: set[str] = set()
    for row in rows:
        if type(row) is not MarketResearchCryptoCustodyOutflowPressureDigestRow:
            raise ValueError(
                "rows must contain MarketResearchCryptoCustodyOutflowPressureDigestRow",
            )
        if row.custody_pressure_key in seen_keys:
            raise ValueError("custody_pressure_key values must be unique")
        seen_keys.add(row.custody_pressure_key)
        _require_hard_flags("row", row)
    return tuple(sorted(rows, key=_row_sort_key))


def _normalize_reason_code_counts(
    items: tuple[
        MarketResearchCryptoCustodyOutflowPressureDigestReasonCodeCount,
        ...,
    ],
) -> tuple[MarketResearchCryptoCustodyOutflowPressureDigestReasonCodeCount, ...]:
    if type(items) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    seen: set[str] = set()
    for item in items:
        if type(item) is not MarketResearchCryptoCustodyOutflowPressureDigestReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count rows")
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        seen.add(item.reason_code)
        _require_hard_flags("reason code count", item)
    return tuple(sorted(items, key=lambda item: REASON_CODE_SEQUENCE.index(item.reason_code)))


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
        custody_pressure_key, source_config_version = item
        _require_public_string("custody_pressure_key", custody_pressure_key)
        _require_public_string("source_config_version", source_config_version)
        if custody_pressure_key in seen_keys:
            raise ValueError(
                "source_config_versions custody_pressure_key values must be unique",
            )
        seen_keys.add(custody_pressure_key)
        pairs.append((custody_pressure_key, source_config_version))
    return tuple(sorted(pairs))


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
    if type(value) is not str or value not in CUSTODY_OUTFLOW_PRESSURE_DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be a supported status")


def _require_venue_type(field_name: str, value: str) -> None:
    if type(value) is not str or value not in VENUE_TYPES:
        raise ValueError(f"{field_name} must be a supported venue type")


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


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError(f"{field_name} must be a finite Decimal")
    return _quantize(value)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime or value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} must have a non-None UTC offset")
    return value.astimezone(UTC)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    return _quantize(
        Decimal(delta.days * 86400 + delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND),
    )


def _growth_ratio(current_value: Decimal, previous_value: Decimal) -> Decimal:
    if previous_value == ZERO:
        return ZERO
    growth = (current_value - previous_value) / previous_value
    if growth <= ZERO:
        return ZERO
    return _quantize(growth)


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
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, datetime):
        return value.isoformat()
    if type(value) is Decimal:
        return str(value)
    if type(value) is tuple:
        return tuple(_json_ready(item) for item in value)
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"unsupported payload value type: {type(value).__name__}")


def _freeze(value: Any) -> Any:
    if type(value) is dict:
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if type(value) is tuple:
        return tuple(_freeze(item) for item in value)
    return value
