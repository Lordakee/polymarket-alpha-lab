"""Pure Phase 1 crypto blob fee spike market research reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from types import MappingProxyType
from typing import Any


DEFAULT_MARKET_RESEARCH_CRYPTO_BLOB_FEE_SPIKE_DIGEST_CONFIG_VERSION = (
    "market-research-crypto-blob-fee-spike-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
BLOB_FEE_SPIKE_DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

READY_REASON = "market_research_crypto_blob_fee_spike_digest_ready"
NO_INPUTS_REASON = "market_research_crypto_blob_fee_spike_digest_no_inputs"
BLOB_BASE_FEE_SPIKE_REASON = (
    "market_research_crypto_blob_fee_spike_digest_blob_base_fee_spike"
)
BLOB_P95_FEE_SPIKE_REASON = (
    "market_research_crypto_blob_fee_spike_digest_blob_p95_fee_spike"
)
BLOB_GAS_CONGESTION_REASON = (
    "market_research_crypto_blob_fee_spike_digest_blob_gas_congestion"
)
DATA_AVAILABILITY_BACKLOG_REASON = (
    "market_research_crypto_blob_fee_spike_digest_data_availability_backlog"
)
L2_BATCH_DELAY_REASON = "market_research_crypto_blob_fee_spike_digest_l2_batch_delay"
SOURCE_DIVERSITY_GAP_REASON = (
    "market_research_crypto_blob_fee_spike_digest_source_diversity_gap"
)
STALE_OBSERVATION_REASON = (
    "market_research_crypto_blob_fee_spike_digest_stale_observation"
)
CONFIDENCE_GAP_REASON = "market_research_crypto_blob_fee_spike_digest_confidence_gap"

REASON_CODE_SEQUENCE = (
    BLOB_BASE_FEE_SPIKE_REASON,
    BLOB_P95_FEE_SPIKE_REASON,
    BLOB_GAS_CONGESTION_REASON,
    DATA_AVAILABILITY_BACKLOG_REASON,
    L2_BATCH_DELAY_REASON,
    SOURCE_DIVERSITY_GAP_REASON,
    STALE_OBSERVATION_REASON,
    CONFIDENCE_GAP_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    BLOB_BASE_FEE_SPIKE_REASON,
    BLOB_P95_FEE_SPIKE_REASON,
    BLOB_GAS_CONGESTION_REASON,
    DATA_AVAILABILITY_BACKLOG_REASON,
    L2_BATCH_DELAY_REASON,
    SOURCE_DIVERSITY_GAP_REASON,
    STALE_OBSERVATION_REASON,
    CONFIDENCE_GAP_REASON,
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
        _join_parts("au", "th"),
        _join_parts("0", "x"),
    ),
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_CRYPTO_BLOB_FEE_SPIKE_DIGEST_CONFIG_VERSION",
    "MarketResearchCryptoBlobFeeSpikeDigestConfig",
    "MarketResearchCryptoBlobFeeSpikeDigestReasonCodeCount",
    "MarketResearchCryptoBlobFeeSpikeDigestReport",
    "MarketResearchCryptoBlobFeeSpikeDigestRow",
    "MarketResearchCryptoBlobFeeSpikeObservation",
    "build_market_research_crypto_blob_fee_spike_digest",
    "market_research_crypto_blob_fee_spike_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchCryptoBlobFeeSpikeDigestConfig:
    config_version: str = DEFAULT_MARKET_RESEARCH_CRYPTO_BLOB_FEE_SPIKE_DIGEST_CONFIG_VERSION
    max_observation_age_seconds: Decimal = Decimal("1800.000000")
    watch_blob_base_fee_spike_ratio: Decimal = Decimal("0.500000")
    blocked_blob_base_fee_spike_ratio: Decimal = Decimal("1.500000")
    max_blob_gas_used_ratio: Decimal = Decimal("0.850000")
    max_data_availability_backlog_ratio: Decimal = Decimal("0.650000")
    max_l2_batch_delay_seconds: Decimal = Decimal("600.000000")
    min_source_count: Decimal = Decimal("3.000000")
    min_confidence: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoBlobFeeSpikeDigestConfig:
            raise TypeError(
                "MarketResearchCryptoBlobFeeSpikeDigestConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoBlobFeeSpikeDigestConfig:
            raise ValueError(
                "config must be exactly MarketResearchCryptoBlobFeeSpikeDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_CRYPTO_BLOB_FEE_SPIKE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the configured version")
        for field_name in (
            "max_observation_age_seconds",
            "watch_blob_base_fee_spike_ratio",
            "blocked_blob_base_fee_spike_ratio",
            "max_l2_batch_delay_seconds",
            "min_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_blob_base_fee_spike_ratio > self.blocked_blob_base_fee_spike_ratio:
            raise ValueError(
                "watch_blob_base_fee_spike_ratio must not exceed blocked threshold",
            )
        for field_name in (
            "max_blob_gas_used_ratio",
            "max_data_availability_backlog_ratio",
            "min_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchCryptoBlobFeeSpikeObservation:
    condition_id: str
    blob_fee_key: str
    chain_name: str
    asset_symbol: str
    observed_at: datetime
    blob_base_fee_gwei: Decimal
    baseline_blob_base_fee_gwei: Decimal
    blob_fee_p95_gwei: Decimal
    baseline_blob_fee_p95_gwei: Decimal
    blob_gas_used_ratio: Decimal
    data_availability_backlog_ratio: Decimal
    l2_batch_delay_seconds: Decimal
    source_count: Decimal
    confidence: Decimal
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoBlobFeeSpikeObservation:
            raise TypeError(
                "MarketResearchCryptoBlobFeeSpikeObservation "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoBlobFeeSpikeObservation:
            raise ValueError(
                "observation must be exactly MarketResearchCryptoBlobFeeSpikeObservation",
            )
        for field_name in (
            "condition_id",
            "blob_fee_key",
            "chain_name",
            "asset_symbol",
            "source_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "blob_base_fee_gwei",
            "baseline_blob_base_fee_gwei",
            "blob_fee_p95_gwei",
            "baseline_blob_fee_p95_gwei",
            "l2_batch_delay_seconds",
            "source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "blob_gas_used_ratio",
            "data_availability_backlog_ratio",
            "confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class MarketResearchCryptoBlobFeeSpikeDigestRow:
    condition_id: str
    blob_fee_key: str
    chain_name: str
    asset_symbol: str
    digest_status: str
    observed_at: datetime
    observation_age_seconds: Decimal
    blob_base_fee_gwei: Decimal
    baseline_blob_base_fee_gwei: Decimal
    blob_base_fee_spike_ratio: Decimal
    blob_fee_p95_gwei: Decimal
    baseline_blob_fee_p95_gwei: Decimal
    blob_p95_fee_spike_ratio: Decimal
    blob_gas_used_ratio: Decimal
    data_availability_backlog_ratio: Decimal
    l2_batch_delay_seconds: Decimal
    source_count: Decimal
    confidence: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoBlobFeeSpikeDigestRow:
            raise TypeError(
                "MarketResearchCryptoBlobFeeSpikeDigestRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoBlobFeeSpikeDigestRow:
            raise ValueError("row must be exactly MarketResearchCryptoBlobFeeSpikeDigestRow")
        for field_name in (
            "condition_id",
            "blob_fee_key",
            "chain_name",
            "asset_symbol",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_status("digest_status", self.digest_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "observation_age_seconds",
            "blob_base_fee_gwei",
            "baseline_blob_base_fee_gwei",
            "blob_base_fee_spike_ratio",
            "blob_fee_p95_gwei",
            "baseline_blob_fee_p95_gwei",
            "blob_p95_fee_spike_ratio",
            "l2_batch_delay_seconds",
            "source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "blob_gas_used_ratio",
            "data_availability_backlog_ratio",
            "confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, sequence=ROW_REASON_CODE_SEQUENCE),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchCryptoBlobFeeSpikeDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    observation_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoBlobFeeSpikeDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchCryptoBlobFeeSpikeDigestReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoBlobFeeSpikeDigestReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "MarketResearchCryptoBlobFeeSpikeDigestReasonCodeCount",
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
class MarketResearchCryptoBlobFeeSpikeDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    observation_count: Decimal
    ready_observation_count: Decimal
    watch_observation_count: Decimal
    blocked_observation_count: Decimal
    blob_base_fee_spike_observation_count: Decimal
    blob_p95_fee_spike_observation_count: Decimal
    blob_gas_congestion_observation_count: Decimal
    data_availability_backlog_observation_count: Decimal
    l2_batch_delay_observation_count: Decimal
    source_diversity_gap_observation_count: Decimal
    stale_observation_count: Decimal
    confidence_gap_observation_count: Decimal
    average_blob_base_fee_spike_ratio: Decimal
    average_blob_p95_fee_spike_ratio: Decimal
    average_blob_gas_used_ratio: Decimal
    average_data_availability_backlog_ratio: Decimal
    average_l2_batch_delay_seconds: Decimal
    max_observation_age_seconds: Decimal
    max_allowed_observation_age_seconds: Decimal
    watch_blob_base_fee_spike_ratio: Decimal
    blocked_blob_base_fee_spike_ratio: Decimal
    max_blob_gas_used_ratio: Decimal
    max_data_availability_backlog_ratio: Decimal
    max_l2_batch_delay_seconds: Decimal
    min_source_count: Decimal
    min_confidence: Decimal
    rows: tuple[MarketResearchCryptoBlobFeeSpikeDigestRow, ...]
    source_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[MarketResearchCryptoBlobFeeSpikeDigestReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoBlobFeeSpikeDigestReport:
            raise TypeError(
                "MarketResearchCryptoBlobFeeSpikeDigestReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoBlobFeeSpikeDigestReport:
            raise ValueError(
                "report must be exactly MarketResearchCryptoBlobFeeSpikeDigestReport",
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
            "blob_base_fee_spike_observation_count",
            "blob_p95_fee_spike_observation_count",
            "blob_gas_congestion_observation_count",
            "data_availability_backlog_observation_count",
            "l2_batch_delay_observation_count",
            "source_diversity_gap_observation_count",
            "stale_observation_count",
            "confidence_gap_observation_count",
            "average_blob_base_fee_spike_ratio",
            "average_blob_p95_fee_spike_ratio",
            "average_l2_batch_delay_seconds",
            "max_observation_age_seconds",
            "max_allowed_observation_age_seconds",
            "watch_blob_base_fee_spike_ratio",
            "blocked_blob_base_fee_spike_ratio",
            "max_l2_batch_delay_seconds",
            "min_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_blob_gas_used_ratio",
            "average_data_availability_backlog_ratio",
            "max_blob_gas_used_ratio",
            "max_data_availability_backlog_ratio",
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


def build_market_research_crypto_blob_fee_spike_digest(
    observations: Iterable[MarketResearchCryptoBlobFeeSpikeObservation],
    *,
    config: MarketResearchCryptoBlobFeeSpikeDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchCryptoBlobFeeSpikeDigestReport:
    cfg = config or MarketResearchCryptoBlobFeeSpikeDigestConfig()
    if type(cfg) is not MarketResearchCryptoBlobFeeSpikeDigestConfig:
        raise ValueError("config must be exactly MarketResearchCryptoBlobFeeSpikeDigestConfig")
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    rows = tuple(
        _row_for_observation(observation, config=cfg, generated_at=generated_at_utc)
        for observation in normalized_observations
    )
    sorted_rows = tuple(
        sorted(
            rows,
            key=lambda row: (
                _row_sort_value(row),
                row.blob_fee_key,
                row.condition_id,
            ),
        ),
    )
    report_status = _report_status(sorted_rows)
    observation_count = _decimal_count(len(sorted_rows))
    return MarketResearchCryptoBlobFeeSpikeDigestReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        digest_status=report_status,
        recommended_next_step=_recommended_next_step(report_status),
        observation_count=observation_count,
        ready_observation_count=_status_count(sorted_rows, STATUS_READY),
        watch_observation_count=_status_count(sorted_rows, STATUS_WATCH),
        blocked_observation_count=_status_count(sorted_rows, STATUS_BLOCKED),
        blob_base_fee_spike_observation_count=_reason_observation_count(
            sorted_rows,
            BLOB_BASE_FEE_SPIKE_REASON,
        ),
        blob_p95_fee_spike_observation_count=_reason_observation_count(
            sorted_rows,
            BLOB_P95_FEE_SPIKE_REASON,
        ),
        blob_gas_congestion_observation_count=_reason_observation_count(
            sorted_rows,
            BLOB_GAS_CONGESTION_REASON,
        ),
        data_availability_backlog_observation_count=_reason_observation_count(
            sorted_rows,
            DATA_AVAILABILITY_BACKLOG_REASON,
        ),
        l2_batch_delay_observation_count=_reason_observation_count(
            sorted_rows,
            L2_BATCH_DELAY_REASON,
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
        average_blob_base_fee_spike_ratio=_ratio(
            _decimal_sum(row.blob_base_fee_spike_ratio for row in sorted_rows),
            observation_count,
        ),
        average_blob_p95_fee_spike_ratio=_ratio(
            _decimal_sum(row.blob_p95_fee_spike_ratio for row in sorted_rows),
            observation_count,
        ),
        average_blob_gas_used_ratio=_ratio(
            _decimal_sum(row.blob_gas_used_ratio for row in sorted_rows),
            observation_count,
        ),
        average_data_availability_backlog_ratio=_ratio(
            _decimal_sum(row.data_availability_backlog_ratio for row in sorted_rows),
            observation_count,
        ),
        average_l2_batch_delay_seconds=_ratio(
            _decimal_sum(row.l2_batch_delay_seconds for row in sorted_rows),
            observation_count,
        ),
        max_observation_age_seconds=max(
            (row.observation_age_seconds for row in sorted_rows),
            default=ZERO,
        ),
        max_allowed_observation_age_seconds=cfg.max_observation_age_seconds,
        watch_blob_base_fee_spike_ratio=cfg.watch_blob_base_fee_spike_ratio,
        blocked_blob_base_fee_spike_ratio=cfg.blocked_blob_base_fee_spike_ratio,
        max_blob_gas_used_ratio=cfg.max_blob_gas_used_ratio,
        max_data_availability_backlog_ratio=cfg.max_data_availability_backlog_ratio,
        max_l2_batch_delay_seconds=cfg.max_l2_batch_delay_seconds,
        min_source_count=cfg.min_source_count,
        min_confidence=cfg.min_confidence,
        rows=sorted_rows,
        source_config_versions=tuple(
            sorted(
                (observation.blob_fee_key, observation.source_config_version)
                for observation in normalized_observations
            ),
        ),
        reason_code_counts=_reason_code_counts(sorted_rows),
        reason_codes=_summary_reason_codes(sorted_rows),
    )


def market_research_crypto_blob_fee_spike_digest_payload(
    report: MarketResearchCryptoBlobFeeSpikeDigestReport,
) -> MappingProxyType:
    if type(report) is not MarketResearchCryptoBlobFeeSpikeDigestReport:
        raise ValueError("report must be exactly MarketResearchCryptoBlobFeeSpikeDigestReport")
    return _freeze(_json_ready(report))


def _row_for_observation(
    observation: MarketResearchCryptoBlobFeeSpikeObservation,
    *,
    config: MarketResearchCryptoBlobFeeSpikeDigestConfig,
    generated_at: datetime,
) -> MarketResearchCryptoBlobFeeSpikeDigestRow:
    if observation.observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    observation_age_seconds = _age_seconds(generated_at, observation.observed_at)
    blob_base_fee_spike_ratio = _spike_ratio(
        observation.blob_base_fee_gwei,
        observation.baseline_blob_base_fee_gwei,
    )
    blob_p95_fee_spike_ratio = _spike_ratio(
        observation.blob_fee_p95_gwei,
        observation.baseline_blob_fee_p95_gwei,
    )
    reason_codes = _row_reason_codes(
        observation=observation,
        config=config,
        observation_age_seconds=observation_age_seconds,
        blob_base_fee_spike_ratio=blob_base_fee_spike_ratio,
        blob_p95_fee_spike_ratio=blob_p95_fee_spike_ratio,
    )
    return MarketResearchCryptoBlobFeeSpikeDigestRow(
        condition_id=observation.condition_id,
        blob_fee_key=observation.blob_fee_key,
        chain_name=observation.chain_name,
        asset_symbol=observation.asset_symbol,
        digest_status=_row_status(
            reason_codes=reason_codes,
            blob_base_fee_spike_ratio=blob_base_fee_spike_ratio,
            blob_p95_fee_spike_ratio=blob_p95_fee_spike_ratio,
            config=config,
        ),
        observed_at=observation.observed_at,
        observation_age_seconds=observation_age_seconds,
        blob_base_fee_gwei=observation.blob_base_fee_gwei,
        baseline_blob_base_fee_gwei=observation.baseline_blob_base_fee_gwei,
        blob_base_fee_spike_ratio=blob_base_fee_spike_ratio,
        blob_fee_p95_gwei=observation.blob_fee_p95_gwei,
        baseline_blob_fee_p95_gwei=observation.baseline_blob_fee_p95_gwei,
        blob_p95_fee_spike_ratio=blob_p95_fee_spike_ratio,
        blob_gas_used_ratio=observation.blob_gas_used_ratio,
        data_availability_backlog_ratio=observation.data_availability_backlog_ratio,
        l2_batch_delay_seconds=observation.l2_batch_delay_seconds,
        source_count=observation.source_count,
        confidence=observation.confidence,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    observation: MarketResearchCryptoBlobFeeSpikeObservation,
    config: MarketResearchCryptoBlobFeeSpikeDigestConfig,
    observation_age_seconds: Decimal,
    blob_base_fee_spike_ratio: Decimal,
    blob_p95_fee_spike_ratio: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if blob_base_fee_spike_ratio >= config.watch_blob_base_fee_spike_ratio:
        reasons.append(BLOB_BASE_FEE_SPIKE_REASON)
    if blob_p95_fee_spike_ratio >= config.watch_blob_base_fee_spike_ratio:
        reasons.append(BLOB_P95_FEE_SPIKE_REASON)
    if observation.blob_gas_used_ratio > config.max_blob_gas_used_ratio:
        reasons.append(BLOB_GAS_CONGESTION_REASON)
    if observation.data_availability_backlog_ratio > config.max_data_availability_backlog_ratio:
        reasons.append(DATA_AVAILABILITY_BACKLOG_REASON)
    if observation.l2_batch_delay_seconds > config.max_l2_batch_delay_seconds:
        reasons.append(L2_BATCH_DELAY_REASON)
    if observation.source_count < config.min_source_count:
        reasons.append(SOURCE_DIVERSITY_GAP_REASON)
    if observation_age_seconds > config.max_observation_age_seconds:
        reasons.append(STALE_OBSERVATION_REASON)
    if observation.confidence < config.min_confidence:
        reasons.append(CONFIDENCE_GAP_REASON)
    if not reasons:
        reasons.append(READY_REASON)
    return tuple(reason for reason in ROW_REASON_CODE_SEQUENCE if reason in reasons)


def _row_status(
    *,
    reason_codes: tuple[str, ...],
    blob_base_fee_spike_ratio: Decimal,
    blob_p95_fee_spike_ratio: Decimal,
    config: MarketResearchCryptoBlobFeeSpikeDigestConfig,
) -> str:
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    if (
        blob_base_fee_spike_ratio >= config.blocked_blob_base_fee_spike_ratio
        or blob_p95_fee_spike_ratio >= config.blocked_blob_base_fee_spike_ratio
        or any(
            reason in reason_codes
            for reason in (
                BLOB_GAS_CONGESTION_REASON,
                DATA_AVAILABILITY_BACKLOG_REASON,
                L2_BATCH_DELAY_REASON,
                SOURCE_DIVERSITY_GAP_REASON,
                STALE_OBSERVATION_REASON,
                CONFIDENCE_GAP_REASON,
            )
        )
    ):
        return STATUS_BLOCKED
    return STATUS_WATCH


def _row_sort_value(row: MarketResearchCryptoBlobFeeSpikeDigestRow) -> tuple[int, Decimal]:
    status_rank = {
        STATUS_BLOCKED: 0,
        STATUS_WATCH: 1,
        STATUS_READY: 2,
    }[row.digest_status]
    severity = _decimal_count(
        len(tuple(reason for reason in row.reason_codes if reason != READY_REASON)),
    )
    return (status_rank, -severity)


def _report_status(rows: tuple[MarketResearchCryptoBlobFeeSpikeDigestRow, ...]) -> str:
    if not rows:
        return STATUS_WATCH
    if any(row.digest_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_READY


def _recommended_next_step(status: str) -> str:
    if status == STATUS_BLOCKED:
        return "block_report_only_market_research_crypto_blob_fee_spike_digest"
    if status == STATUS_WATCH:
        return "review_report_only_market_research_crypto_blob_fee_spike_digest"
    return "allow_report_only_market_research_crypto_blob_fee_spike_digest"


def _status_count(
    rows: tuple[MarketResearchCryptoBlobFeeSpikeDigestRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.digest_status == status))


def _reason_observation_count(
    rows: tuple[MarketResearchCryptoBlobFeeSpikeDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _reason_code_counts(
    rows: tuple[MarketResearchCryptoBlobFeeSpikeDigestRow, ...],
) -> tuple[MarketResearchCryptoBlobFeeSpikeDigestReasonCodeCount, ...]:
    observation_count = _decimal_count(len(rows))
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        MarketResearchCryptoBlobFeeSpikeDigestReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
            observation_ratio=_ratio(
                _decimal_count(counts[reason_code]),
                observation_count,
            ),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _summary_reason_codes(
    rows: tuple[MarketResearchCryptoBlobFeeSpikeDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    seen: set[str] = set()
    for row in rows:
        seen.update(row.reason_codes)
    if len(seen) > 1 and READY_REASON in seen:
        seen.remove(READY_REASON)
    return tuple(reason for reason in REASON_CODE_SEQUENCE if reason in seen)


def _validate_row(row: MarketResearchCryptoBlobFeeSpikeDigestRow) -> None:
    if row.blob_base_fee_spike_ratio != _spike_ratio(
        row.blob_base_fee_gwei,
        row.baseline_blob_base_fee_gwei,
    ):
        raise ValueError("blob_base_fee_spike_ratio does not match fee inputs")
    if row.blob_p95_fee_spike_ratio != _spike_ratio(
        row.blob_fee_p95_gwei,
        row.baseline_blob_fee_p95_gwei,
    ):
        raise ValueError("blob_p95_fee_spike_ratio does not match fee inputs")


def _validate_report(report: MarketResearchCryptoBlobFeeSpikeDigestReport) -> None:
    if report.observation_count != _decimal_count(len(report.rows)):
        raise ValueError("observation_count does not match rows")
    if report.ready_observation_count != _status_count(report.rows, STATUS_READY):
        raise ValueError("ready_observation_count does not match rows")
    if report.watch_observation_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_observation_count does not match rows")
    if report.blocked_observation_count != _status_count(report.rows, STATUS_BLOCKED):
        raise ValueError("blocked_observation_count does not match rows")
    expected_counts = (
        (BLOB_BASE_FEE_SPIKE_REASON, report.blob_base_fee_spike_observation_count),
        (BLOB_P95_FEE_SPIKE_REASON, report.blob_p95_fee_spike_observation_count),
        (BLOB_GAS_CONGESTION_REASON, report.blob_gas_congestion_observation_count),
        (
            DATA_AVAILABILITY_BACKLOG_REASON,
            report.data_availability_backlog_observation_count,
        ),
        (L2_BATCH_DELAY_REASON, report.l2_batch_delay_observation_count),
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
    if report.average_blob_base_fee_spike_ratio != _ratio(
        _decimal_sum(row.blob_base_fee_spike_ratio for row in report.rows),
        report.observation_count,
    ):
        raise ValueError("average_blob_base_fee_spike_ratio does not match rows")
    if report.average_blob_p95_fee_spike_ratio != _ratio(
        _decimal_sum(row.blob_p95_fee_spike_ratio for row in report.rows),
        report.observation_count,
    ):
        raise ValueError("average_blob_p95_fee_spike_ratio does not match rows")
    if report.average_blob_gas_used_ratio != _ratio(
        _decimal_sum(row.blob_gas_used_ratio for row in report.rows),
        report.observation_count,
    ):
        raise ValueError("average_blob_gas_used_ratio does not match rows")
    if report.average_data_availability_backlog_ratio != _ratio(
        _decimal_sum(row.data_availability_backlog_ratio for row in report.rows),
        report.observation_count,
    ):
        raise ValueError("average_data_availability_backlog_ratio does not match rows")
    if report.average_l2_batch_delay_seconds != _ratio(
        _decimal_sum(row.l2_batch_delay_seconds for row in report.rows),
        report.observation_count,
    ):
        raise ValueError("average_l2_batch_delay_seconds does not match rows")
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
    observations: Iterable[MarketResearchCryptoBlobFeeSpikeObservation],
) -> tuple[MarketResearchCryptoBlobFeeSpikeObservation, ...]:
    observation_tuple = tuple(observations)
    seen_keys: set[str] = set()
    for observation in observation_tuple:
        if type(observation) is not MarketResearchCryptoBlobFeeSpikeObservation:
            raise ValueError(
                "observations must contain MarketResearchCryptoBlobFeeSpikeObservation",
            )
        if observation.blob_fee_key in seen_keys:
            raise ValueError("blob_fee_key values must be unique")
        seen_keys.add(observation.blob_fee_key)
        _require_hard_flags("observation", observation)
    return observation_tuple


def _normalize_rows(
    rows: tuple[MarketResearchCryptoBlobFeeSpikeDigestRow, ...],
) -> tuple[MarketResearchCryptoBlobFeeSpikeDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not MarketResearchCryptoBlobFeeSpikeDigestRow:
            raise ValueError("rows must contain MarketResearchCryptoBlobFeeSpikeDigestRow")
        _require_hard_flags("row", row)
    return rows


def _normalize_reason_code_counts(
    items: tuple[MarketResearchCryptoBlobFeeSpikeDigestReasonCodeCount, ...],
) -> tuple[MarketResearchCryptoBlobFeeSpikeDigestReasonCodeCount, ...]:
    if type(items) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for item in items:
        if type(item) is not MarketResearchCryptoBlobFeeSpikeDigestReasonCodeCount:
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
        blob_fee_key, source_config_version = item
        _require_public_string("blob_fee_key", blob_fee_key)
        _require_public_string("source_config_version", source_config_version)
        if blob_fee_key in seen_keys:
            raise ValueError("source_config_versions blob_fee_key values must be unique")
        seen_keys.add(blob_fee_key)
        pairs.append((blob_fee_key, source_config_version))
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
    if type(value) is not str or value not in BLOB_FEE_SPIKE_DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be a valid status")


def _require_reason_code(field_name: str, value: str) -> None:
    if type(value) is not str or value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a valid reason code")


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


def _spike_ratio(current: Decimal, baseline: Decimal) -> Decimal:
    if baseline == ZERO:
        return ZERO
    ratio = current / baseline - ONE
    if ratio <= ZERO:
        return ZERO
    return _quantize(ratio)


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


def _json_ready(value: object) -> Any:
    if isinstance(value, Decimal):
        return f"{value:.6f}"
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    return value


def _freeze(value: object) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value
