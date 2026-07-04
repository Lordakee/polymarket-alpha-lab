"""Pure Phase 1 crypto L2 blob fee spike digest reducer."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from types import MappingProxyType
from typing import Any


DEFAULT_MARKET_RESEARCH_CRYPTO_LAYER2_BLOB_FEE_SPIKE_DIGEST_CONFIG_VERSION = (
    "market-research-crypto-layer2-blob-fee-spike-digest-v0"
)

NUMERIC_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DEFAULT_MAX_OBSERVATION_AGE_SECONDS = Decimal("1800.000000")
DEFAULT_WATCH_BLOB_BASE_FEE_SPIKE_RATIO = Decimal("0.750000")
DEFAULT_BLOCKED_BLOB_BASE_FEE_SPIKE_RATIO = Decimal("2.000000")
DEFAULT_MAX_BLOB_GAS_USED_RATIO = Decimal("0.850000")
DEFAULT_MAX_DATA_AVAILABILITY_BACKLOG_RATIO = Decimal("0.600000")
DEFAULT_MAX_BATCH_SUBMISSION_DELAY_SECONDS = Decimal("600.000000")
DEFAULT_MIN_SOURCE_COUNT = Decimal("3.000000")
DEFAULT_MIN_CONFIDENCE = Decimal("0.700000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

DIGEST_STATUSES = ("ready", "watch", "blocked")
STATUS_WEIGHTS = {
    "blocked": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "ready": Decimal("0.000000"),
}

READY_REASON_CODE = "market_research_crypto_layer2_blob_fee_spike_digest_ready"
NO_INPUTS_REASON_CODE = "market_research_crypto_layer2_blob_fee_spike_digest_no_inputs"
BLOB_BASE_FEE_SPIKE_REASON_CODE = (
    "market_research_crypto_layer2_blob_fee_spike_digest_blob_base_fee_spike"
)
BLOB_GAS_CONGESTION_REASON_CODE = (
    "market_research_crypto_layer2_blob_fee_spike_digest_blob_gas_congestion"
)
DATA_AVAILABILITY_BACKLOG_REASON_CODE = (
    "market_research_crypto_layer2_blob_fee_spike_digest_data_availability_backlog"
)
BATCH_SUBMISSION_DELAY_REASON_CODE = (
    "market_research_crypto_layer2_blob_fee_spike_digest_batch_submission_delay"
)
SOURCE_DIVERSITY_GAP_REASON_CODE = (
    "market_research_crypto_layer2_blob_fee_spike_digest_source_diversity_gap"
)
STALE_OBSERVATION_REASON_CODE = (
    "market_research_crypto_layer2_blob_fee_spike_digest_stale_observation"
)
CONFIDENCE_GAP_REASON_CODE = (
    "market_research_crypto_layer2_blob_fee_spike_digest_confidence_gap"
)

REASON_CODES = (
    READY_REASON_CODE,
    NO_INPUTS_REASON_CODE,
    BLOB_BASE_FEE_SPIKE_REASON_CODE,
    BLOB_GAS_CONGESTION_REASON_CODE,
    DATA_AVAILABILITY_BACKLOG_REASON_CODE,
    BATCH_SUBMISSION_DELAY_REASON_CODE,
    SOURCE_DIVERSITY_GAP_REASON_CODE,
    STALE_OBSERVATION_REASON_CODE,
    CONFIDENCE_GAP_REASON_CODE,
)
ROW_REASON_CODES = (
    READY_REASON_CODE,
    BLOB_BASE_FEE_SPIKE_REASON_CODE,
    BLOB_GAS_CONGESTION_REASON_CODE,
    DATA_AVAILABILITY_BACKLOG_REASON_CODE,
    BATCH_SUBMISSION_DELAY_REASON_CODE,
    SOURCE_DIVERSITY_GAP_REASON_CODE,
    STALE_OBSERVATION_REASON_CODE,
    CONFIDENCE_GAP_REASON_CODE,
)
REPORT_REASON_CODES = REASON_CODES

REVIEW_NEXT_STEP = (
    "review_report_only_market_research_crypto_layer2_blob_fee_spike_digest"
)
BLOCK_NEXT_STEP = "block_report_only_market_research_crypto_layer2_blob_fee_spike_digest"
READY_NEXT_STEP = (
    "continue_report_only_market_research_crypto_layer2_blob_fee_spike_digest"
)

_REDACTED_TERMS = (
    "secret",
    "token",
    "credential",
    "auth",
    "key",
    "wall" "et",
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_CRYPTO_LAYER2_BLOB_FEE_SPIKE_DIGEST_CONFIG_VERSION",
    "MarketResearchCryptoLayer2BlobFeeSpikeDigestConfig",
    "MarketResearchCryptoLayer2BlobFeeSpikeObservation",
    "MarketResearchCryptoLayer2BlobFeeSpikeDigestRow",
    "MarketResearchCryptoLayer2BlobFeeSpikeDigestReasonCodeCount",
    "MarketResearchCryptoLayer2BlobFeeSpikeDigestReport",
    "build_market_research_crypto_layer2_blob_fee_spike_digest",
    "market_research_crypto_layer2_blob_fee_spike_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchCryptoLayer2BlobFeeSpikeDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_CRYPTO_LAYER2_BLOB_FEE_SPIKE_DIGEST_CONFIG_VERSION
    )
    max_observation_age_seconds: Decimal = DEFAULT_MAX_OBSERVATION_AGE_SECONDS
    watch_blob_base_fee_spike_ratio: Decimal = DEFAULT_WATCH_BLOB_BASE_FEE_SPIKE_RATIO
    blocked_blob_base_fee_spike_ratio: Decimal = (
        DEFAULT_BLOCKED_BLOB_BASE_FEE_SPIKE_RATIO
    )
    max_blob_gas_used_ratio: Decimal = DEFAULT_MAX_BLOB_GAS_USED_RATIO
    max_data_availability_backlog_ratio: Decimal = (
        DEFAULT_MAX_DATA_AVAILABILITY_BACKLOG_RATIO
    )
    max_batch_submission_delay_seconds: Decimal = (
        DEFAULT_MAX_BATCH_SUBMISSION_DELAY_SECONDS
    )
    min_source_count: Decimal = DEFAULT_MIN_SOURCE_COUNT
    min_confidence: Decimal = DEFAULT_MIN_CONFIDENCE
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoLayer2BlobFeeSpikeDigestConfig:
            raise TypeError(
                "MarketResearchCryptoLayer2BlobFeeSpikeDigestConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoLayer2BlobFeeSpikeDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchCryptoLayer2BlobFeeSpikeDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_CRYPTO_LAYER2_BLOB_FEE_SPIKE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "max_observation_age_seconds",
            _normalize_positive_decimal(
                "max_observation_age_seconds",
                self.max_observation_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "watch_blob_base_fee_spike_ratio",
            _normalize_positive_decimal(
                "watch_blob_base_fee_spike_ratio",
                self.watch_blob_base_fee_spike_ratio,
            ),
        )
        object.__setattr__(
            self,
            "blocked_blob_base_fee_spike_ratio",
            _normalize_positive_decimal(
                "blocked_blob_base_fee_spike_ratio",
                self.blocked_blob_base_fee_spike_ratio,
            ),
        )
        if self.blocked_blob_base_fee_spike_ratio < self.watch_blob_base_fee_spike_ratio:
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
                _normalize_unit_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_batch_submission_delay_seconds",
            _normalize_positive_decimal(
                "max_batch_submission_delay_seconds",
                self.max_batch_submission_delay_seconds,
            ),
        )
        object.__setattr__(
            self,
            "min_source_count",
            _normalize_positive_count("min_source_count", self.min_source_count),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchCryptoLayer2BlobFeeSpikeObservation:
    screening_key: str
    condition_id: str
    layer2_name: str
    rollup_family: str
    observed_at: datetime
    blob_base_fee_gwei: Decimal
    baseline_blob_base_fee_gwei: Decimal
    blob_gas_used_ratio: Decimal
    data_availability_backlog_ratio: Decimal
    batch_submission_delay_seconds: Decimal
    source_count: Decimal
    confidence: Decimal
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoLayer2BlobFeeSpikeObservation:
            raise TypeError(
                "MarketResearchCryptoLayer2BlobFeeSpikeObservation "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoLayer2BlobFeeSpikeObservation:
            raise ValueError(
                "observation must be exactly "
                "MarketResearchCryptoLayer2BlobFeeSpikeObservation",
            )
        for field_name in ("screening_key", "condition_id", "rollup_family"):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_public_string("layer2_name", self.layer2_name)
        _require_canonical_string("source_config_version", self.source_config_version)
        _reject_redacted_text("source_config_version", self.source_config_version)
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        object.__setattr__(
            self,
            "blob_base_fee_gwei",
            _normalize_nonnegative_decimal("blob_base_fee_gwei", self.blob_base_fee_gwei),
        )
        object.__setattr__(
            self,
            "baseline_blob_base_fee_gwei",
            _normalize_positive_decimal(
                "baseline_blob_base_fee_gwei",
                self.baseline_blob_base_fee_gwei,
            ),
        )
        for field_name in (
            "blob_gas_used_ratio",
            "data_availability_backlog_ratio",
            "confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "batch_submission_delay_seconds",
            _normalize_nonnegative_decimal(
                "batch_submission_delay_seconds",
                self.batch_submission_delay_seconds,
            ),
        )
        object.__setattr__(
            self,
            "source_count",
            _normalize_nonnegative_count("source_count", self.source_count),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class MarketResearchCryptoLayer2BlobFeeSpikeDigestRow:
    screening_key: str
    condition_id: str
    layer2_name: str
    rollup_family: str
    observed_at: datetime
    observation_age_seconds: Decimal
    blob_base_fee_gwei: Decimal
    baseline_blob_base_fee_gwei: Decimal
    blob_base_fee_spike_ratio: Decimal
    blob_gas_used_ratio: Decimal
    data_availability_backlog_ratio: Decimal
    batch_submission_delay_seconds: Decimal
    source_count: Decimal
    confidence: Decimal
    source_config_version: str
    digest_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoLayer2BlobFeeSpikeDigestRow:
            raise TypeError(
                "MarketResearchCryptoLayer2BlobFeeSpikeDigestRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoLayer2BlobFeeSpikeDigestRow:
            raise ValueError(
                "row must be exactly MarketResearchCryptoLayer2BlobFeeSpikeDigestRow",
            )
        for field_name in ("screening_key", "condition_id", "rollup_family"):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_public_string("layer2_name", self.layer2_name)
        _require_canonical_string("source_config_version", self.source_config_version)
        _reject_redacted_text("source_config_version", self.source_config_version)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "observation_age_seconds",
            "blob_base_fee_gwei",
            "batch_submission_delay_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "baseline_blob_base_fee_gwei",
            _normalize_positive_decimal(
                "baseline_blob_base_fee_gwei",
                self.baseline_blob_base_fee_gwei,
            ),
        )
        object.__setattr__(
            self,
            "blob_base_fee_spike_ratio",
            _normalize_signed_decimal(
                "blob_base_fee_spike_ratio",
                self.blob_base_fee_spike_ratio,
            ),
        )
        for field_name in (
            "blob_gas_used_ratio",
            "data_availability_backlog_ratio",
            "confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_count",
            _normalize_nonnegative_count("source_count", self.source_count),
        )
        _require_member("digest_status", self.digest_status, DIGEST_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchCryptoLayer2BlobFeeSpikeDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    observation_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoLayer2BlobFeeSpikeDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchCryptoLayer2BlobFeeSpikeDigestReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoLayer2BlobFeeSpikeDigestReasonCodeCount:
            raise ValueError(
                "reason_code_count must be exactly "
                "MarketResearchCryptoLayer2BlobFeeSpikeDigestReasonCodeCount",
            )
        _require_member("reason_code", self.reason_code, ROW_REASON_CODES)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_count("count", self.count),
        )
        object.__setattr__(
            self,
            "observation_ratio",
            _normalize_unit_ratio("observation_ratio", self.observation_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchCryptoLayer2BlobFeeSpikeDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    observation_count: Decimal
    ready_observation_count: Decimal
    watch_observation_count: Decimal
    blocked_observation_count: Decimal
    blob_base_fee_spike_observation_count: Decimal
    blob_gas_congestion_observation_count: Decimal
    data_availability_backlog_observation_count: Decimal
    batch_submission_delay_observation_count: Decimal
    source_diversity_gap_observation_count: Decimal
    stale_observation_count: Decimal
    confidence_gap_observation_count: Decimal
    average_blob_base_fee_spike_ratio: Decimal
    average_blob_gas_used_ratio: Decimal
    average_data_availability_backlog_ratio: Decimal
    average_batch_submission_delay_seconds: Decimal
    max_observation_age_seconds: Decimal
    watch_blob_base_fee_spike_ratio: Decimal
    blocked_blob_base_fee_spike_ratio: Decimal
    max_blob_gas_used_ratio: Decimal
    max_data_availability_backlog_ratio: Decimal
    max_batch_submission_delay_seconds: Decimal
    min_source_count: Decimal
    min_confidence: Decimal
    rows: tuple[MarketResearchCryptoLayer2BlobFeeSpikeDigestRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        MarketResearchCryptoLayer2BlobFeeSpikeDigestReasonCodeCount,
        ...,
    ]
    source_config_versions: tuple[tuple[str, str], ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoLayer2BlobFeeSpikeDigestReport:
            raise TypeError(
                "MarketResearchCryptoLayer2BlobFeeSpikeDigestReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoLayer2BlobFeeSpikeDigestReport:
            raise ValueError(
                "report must be exactly "
                "MarketResearchCryptoLayer2BlobFeeSpikeDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_member("digest_status", self.digest_status, DIGEST_STATUSES)
        _require_member(
            "recommended_next_step",
            self.recommended_next_step,
            (READY_NEXT_STEP, REVIEW_NEXT_STEP, BLOCK_NEXT_STEP),
        )
        for field_name in (
            "observation_count",
            "ready_observation_count",
            "watch_observation_count",
            "blocked_observation_count",
            "blob_base_fee_spike_observation_count",
            "blob_gas_congestion_observation_count",
            "data_availability_backlog_observation_count",
            "batch_submission_delay_observation_count",
            "source_diversity_gap_observation_count",
            "stale_observation_count",
            "confidence_gap_observation_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_blob_base_fee_spike_ratio",
            "average_blob_gas_used_ratio",
            "average_data_availability_backlog_ratio",
            "average_batch_submission_delay_seconds",
            "max_observation_age_seconds",
            "watch_blob_base_fee_spike_ratio",
            "blocked_blob_base_fee_spike_ratio",
            "max_blob_gas_used_ratio",
            "max_data_availability_backlog_ratio",
            "max_batch_submission_delay_seconds",
            "min_source_count",
            "min_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "source_config_versions",
            _normalize_source_config_versions(self.source_config_versions),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_crypto_layer2_blob_fee_spike_digest(
    observations: tuple[MarketResearchCryptoLayer2BlobFeeSpikeObservation, ...],
    *,
    config: MarketResearchCryptoLayer2BlobFeeSpikeDigestConfig | None = None,
    generated_at: datetime | None = None,
) -> MarketResearchCryptoLayer2BlobFeeSpikeDigestReport:
    cfg = config or MarketResearchCryptoLayer2BlobFeeSpikeDigestConfig()
    if type(cfg) is not MarketResearchCryptoLayer2BlobFeeSpikeDigestConfig:
        raise ValueError(
            "config must be exactly "
            "MarketResearchCryptoLayer2BlobFeeSpikeDigestConfig",
        )
    _require_hard_flags("config", cfg)
    generated = _as_utc("generated_at", generated_at or datetime.now(UTC))

    rows: list[MarketResearchCryptoLayer2BlobFeeSpikeDigestRow] = []
    seen_screening_keys: set[str] = set()
    for observation in observations:
        if type(observation) is not MarketResearchCryptoLayer2BlobFeeSpikeObservation:
            raise ValueError(
                "observations must contain "
                "MarketResearchCryptoLayer2BlobFeeSpikeObservation rows",
            )
        if observation.screening_key in seen_screening_keys:
            raise ValueError("screening_key values must be unique")
        seen_screening_keys.add(observation.screening_key)
        rows.append(_build_row(observation, cfg, generated))

    ordered_rows = tuple(sorted(rows, key=_row_sort_key))
    observation_count = _count_decimal(len(ordered_rows))
    digest_status = _digest_status(ordered_rows)
    reason_codes = _report_reason_codes(ordered_rows)
    reason_code_counts = _reason_code_counts(ordered_rows)

    return MarketResearchCryptoLayer2BlobFeeSpikeDigestReport(
        generated_at=generated,
        config_version=cfg.config_version,
        digest_status=digest_status,
        recommended_next_step=_recommended_next_step(digest_status),
        observation_count=observation_count,
        ready_observation_count=_status_count(ordered_rows, "ready"),
        watch_observation_count=_status_count(ordered_rows, "watch"),
        blocked_observation_count=_status_count(ordered_rows, "blocked"),
        blob_base_fee_spike_observation_count=_reason_count(
            ordered_rows,
            BLOB_BASE_FEE_SPIKE_REASON_CODE,
        ),
        blob_gas_congestion_observation_count=_reason_count(
            ordered_rows,
            BLOB_GAS_CONGESTION_REASON_CODE,
        ),
        data_availability_backlog_observation_count=_reason_count(
            ordered_rows,
            DATA_AVAILABILITY_BACKLOG_REASON_CODE,
        ),
        batch_submission_delay_observation_count=_reason_count(
            ordered_rows,
            BATCH_SUBMISSION_DELAY_REASON_CODE,
        ),
        source_diversity_gap_observation_count=_reason_count(
            ordered_rows,
            SOURCE_DIVERSITY_GAP_REASON_CODE,
        ),
        stale_observation_count=_reason_count(ordered_rows, STALE_OBSERVATION_REASON_CODE),
        confidence_gap_observation_count=_reason_count(
            ordered_rows,
            CONFIDENCE_GAP_REASON_CODE,
        ),
        average_blob_base_fee_spike_ratio=_average_decimal(
            tuple(row.blob_base_fee_spike_ratio for row in ordered_rows),
        ),
        average_blob_gas_used_ratio=_average_decimal(
            tuple(row.blob_gas_used_ratio for row in ordered_rows),
        ),
        average_data_availability_backlog_ratio=_average_decimal(
            tuple(row.data_availability_backlog_ratio for row in ordered_rows),
        ),
        average_batch_submission_delay_seconds=_average_decimal(
            tuple(row.batch_submission_delay_seconds for row in ordered_rows),
        ),
        max_observation_age_seconds=max(
            (row.observation_age_seconds for row in ordered_rows),
            default=ZERO,
        ).quantize(NUMERIC_QUANTUM),
        watch_blob_base_fee_spike_ratio=cfg.watch_blob_base_fee_spike_ratio,
        blocked_blob_base_fee_spike_ratio=cfg.blocked_blob_base_fee_spike_ratio,
        max_blob_gas_used_ratio=cfg.max_blob_gas_used_ratio,
        max_data_availability_backlog_ratio=cfg.max_data_availability_backlog_ratio,
        max_batch_submission_delay_seconds=cfg.max_batch_submission_delay_seconds,
        min_source_count=cfg.min_source_count,
        min_confidence=cfg.min_confidence,
        rows=ordered_rows,
        reason_codes=reason_codes,
        reason_code_counts=reason_code_counts,
        source_config_versions=_source_config_versions(ordered_rows),
    )


def market_research_crypto_layer2_blob_fee_spike_digest_payload(
    report: MarketResearchCryptoLayer2BlobFeeSpikeDigestReport,
) -> Mapping[str, Any]:
    if type(report) is not MarketResearchCryptoLayer2BlobFeeSpikeDigestReport:
        raise ValueError(
            "report must be exactly "
            "MarketResearchCryptoLayer2BlobFeeSpikeDigestReport",
        )
    payload = _json_ready(asdict(report))
    if not isinstance(payload, Mapping):
        raise ValueError("report payload must be a mapping")
    return payload


def _build_row(
    observation: MarketResearchCryptoLayer2BlobFeeSpikeObservation,
    config: MarketResearchCryptoLayer2BlobFeeSpikeDigestConfig,
    generated_at: datetime,
) -> MarketResearchCryptoLayer2BlobFeeSpikeDigestRow:
    if observation.observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    observation_age_seconds = _seconds_between(generated_at, observation.observed_at)
    spike_ratio = _blob_base_fee_spike_ratio(
        observation.blob_base_fee_gwei,
        observation.baseline_blob_base_fee_gwei,
    )
    reason_codes = _row_reason_codes(
        spike_ratio=spike_ratio,
        blob_gas_used_ratio=observation.blob_gas_used_ratio,
        data_availability_backlog_ratio=observation.data_availability_backlog_ratio,
        batch_submission_delay_seconds=observation.batch_submission_delay_seconds,
        source_count=observation.source_count,
        confidence=observation.confidence,
        observation_age_seconds=observation_age_seconds,
        config=config,
    )
    digest_status = _row_status(reason_codes, spike_ratio, config)
    return MarketResearchCryptoLayer2BlobFeeSpikeDigestRow(
        screening_key=observation.screening_key,
        condition_id=observation.condition_id,
        layer2_name=observation.layer2_name,
        rollup_family=observation.rollup_family,
        observed_at=observation.observed_at,
        observation_age_seconds=observation_age_seconds,
        blob_base_fee_gwei=observation.blob_base_fee_gwei,
        baseline_blob_base_fee_gwei=observation.baseline_blob_base_fee_gwei,
        blob_base_fee_spike_ratio=spike_ratio,
        blob_gas_used_ratio=observation.blob_gas_used_ratio,
        data_availability_backlog_ratio=observation.data_availability_backlog_ratio,
        batch_submission_delay_seconds=observation.batch_submission_delay_seconds,
        source_count=observation.source_count,
        confidence=observation.confidence,
        source_config_version=observation.source_config_version,
        digest_status=digest_status,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    spike_ratio: Decimal,
    blob_gas_used_ratio: Decimal,
    data_availability_backlog_ratio: Decimal,
    batch_submission_delay_seconds: Decimal,
    source_count: Decimal,
    confidence: Decimal,
    observation_age_seconds: Decimal,
    config: MarketResearchCryptoLayer2BlobFeeSpikeDigestConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if spike_ratio >= config.watch_blob_base_fee_spike_ratio:
        reasons.append(BLOB_BASE_FEE_SPIKE_REASON_CODE)
    if blob_gas_used_ratio > config.max_blob_gas_used_ratio:
        reasons.append(BLOB_GAS_CONGESTION_REASON_CODE)
    if data_availability_backlog_ratio > config.max_data_availability_backlog_ratio:
        reasons.append(DATA_AVAILABILITY_BACKLOG_REASON_CODE)
    if batch_submission_delay_seconds > config.max_batch_submission_delay_seconds:
        reasons.append(BATCH_SUBMISSION_DELAY_REASON_CODE)
    if source_count < config.min_source_count:
        reasons.append(SOURCE_DIVERSITY_GAP_REASON_CODE)
    if observation_age_seconds > config.max_observation_age_seconds:
        reasons.append(STALE_OBSERVATION_REASON_CODE)
    if confidence < config.min_confidence:
        reasons.append(CONFIDENCE_GAP_REASON_CODE)
    if not reasons:
        return (READY_REASON_CODE,)
    return tuple(reasons)


def _row_status(
    reason_codes: tuple[str, ...],
    spike_ratio: Decimal,
    config: MarketResearchCryptoLayer2BlobFeeSpikeDigestConfig,
) -> str:
    if reason_codes == (READY_REASON_CODE,):
        return "ready"
    if spike_ratio < config.blocked_blob_base_fee_spike_ratio and reason_codes == (
        BLOB_BASE_FEE_SPIKE_REASON_CODE,
    ):
        return "watch"
    return "blocked"


def _digest_status(
    rows: tuple[MarketResearchCryptoLayer2BlobFeeSpikeDigestRow, ...],
) -> str:
    if not rows:
        return "watch"
    if any(row.digest_status == "blocked" for row in rows):
        return "blocked"
    if any(row.digest_status == "watch" for row in rows):
        return "watch"
    return "ready"


def _recommended_next_step(digest_status: str) -> str:
    if digest_status == "blocked":
        return BLOCK_NEXT_STEP
    if digest_status == "watch":
        return REVIEW_NEXT_STEP
    return READY_NEXT_STEP


def _report_reason_codes(
    rows: tuple[MarketResearchCryptoLayer2BlobFeeSpikeDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON_CODE,)
    non_ready_reasons: set[str] = set()
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code != READY_REASON_CODE:
                non_ready_reasons.add(reason_code)
    if not non_ready_reasons:
        return (READY_REASON_CODE,)
    return tuple(
        reason_code
        for reason_code in ROW_REASON_CODES
        if reason_code != READY_REASON_CODE and reason_code in non_ready_reasons
    )


def _reason_code_counts(
    rows: tuple[MarketResearchCryptoLayer2BlobFeeSpikeDigestRow, ...],
) -> tuple[MarketResearchCryptoLayer2BlobFeeSpikeDigestReasonCodeCount, ...]:
    if not rows:
        return ()
    report_reasons = _report_reason_codes(rows)
    if report_reasons == (NO_INPUTS_REASON_CODE,):
        return ()
    counts: list[MarketResearchCryptoLayer2BlobFeeSpikeDigestReasonCodeCount] = []
    observation_count = _count_decimal(len(rows))
    for reason_code in report_reasons:
        count = _reason_count(rows, reason_code)
        if count > ZERO:
            counts.append(
                MarketResearchCryptoLayer2BlobFeeSpikeDigestReasonCodeCount(
                    reason_code=reason_code,
                    count=count,
                    observation_ratio=_safe_ratio(count, observation_count),
                ),
            )
    return tuple(counts)


def _status_count(
    rows: tuple[MarketResearchCryptoLayer2BlobFeeSpikeDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.digest_status == status))


def _reason_count(
    rows: tuple[MarketResearchCryptoLayer2BlobFeeSpikeDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _source_config_versions(
    rows: tuple[MarketResearchCryptoLayer2BlobFeeSpikeDigestRow, ...],
) -> tuple[tuple[str, str], ...]:
    return tuple(
        sorted(
            (
                (row.screening_key, row.source_config_version)
                for row in rows
            ),
            key=lambda item: item[0],
        ),
    )


def _row_sort_key(
    row: MarketResearchCryptoLayer2BlobFeeSpikeDigestRow,
) -> tuple[Decimal, Decimal, Decimal, Decimal, str, str, str]:
    non_ready_reason_count = _count_decimal(
        sum(1 for reason_code in row.reason_codes if reason_code != READY_REASON_CODE),
    )
    return (
        -STATUS_WEIGHTS[row.digest_status],
        -non_ready_reason_count,
        -row.blob_base_fee_spike_ratio,
        -row.observation_age_seconds,
        row.screening_key,
        row.condition_id,
        row.source_config_version,
    )


def _blob_base_fee_spike_ratio(
    blob_base_fee_gwei: Decimal,
    baseline_blob_base_fee_gwei: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (
            (blob_base_fee_gwei - baseline_blob_base_fee_gwei)
            / baseline_blob_base_fee_gwei
        ).quantize(NUMERIC_QUANTUM)


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    with localcontext(DECIMAL_CONTEXT):
        return (Decimal(delta.total_seconds()).quantize(NUMERIC_QUANTUM))


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (sum(values, ZERO) / Decimal(len(values))).quantize(NUMERIC_QUANTUM)


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(NUMERIC_QUANTUM)


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(NUMERIC_QUANTUM)


def _validate_row(row: MarketResearchCryptoLayer2BlobFeeSpikeDigestRow) -> None:
    expected_spike_ratio = _blob_base_fee_spike_ratio(
        row.blob_base_fee_gwei,
        row.baseline_blob_base_fee_gwei,
    )
    if row.blob_base_fee_spike_ratio != expected_spike_ratio:
        raise ValueError("blob_base_fee_spike_ratio must match blob fee inputs")
    if row.reason_codes == (READY_REASON_CODE,) and row.digest_status != "ready":
        raise ValueError("digest_status must match reason_codes")
    if row.digest_status == "ready" and row.reason_codes != (READY_REASON_CODE,):
        raise ValueError("reason_codes must match digest_status")


def _validate_report(report: MarketResearchCryptoLayer2BlobFeeSpikeDigestReport) -> None:
    if report.observation_count != _count_decimal(len(report.rows)):
        raise ValueError("observation_count must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step must match digest_status")
    if report.ready_observation_count != _status_count(report.rows, "ready"):
        raise ValueError("ready_observation_count must match rows")
    if report.watch_observation_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_observation_count must match rows")
    if report.blocked_observation_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_observation_count must match rows")
    reason_count_fields = (
        (
            "blob_base_fee_spike_observation_count",
            BLOB_BASE_FEE_SPIKE_REASON_CODE,
        ),
        (
            "blob_gas_congestion_observation_count",
            BLOB_GAS_CONGESTION_REASON_CODE,
        ),
        (
            "data_availability_backlog_observation_count",
            DATA_AVAILABILITY_BACKLOG_REASON_CODE,
        ),
        (
            "batch_submission_delay_observation_count",
            BATCH_SUBMISSION_DELAY_REASON_CODE,
        ),
        (
            "source_diversity_gap_observation_count",
            SOURCE_DIVERSITY_GAP_REASON_CODE,
        ),
        ("stale_observation_count", STALE_OBSERVATION_REASON_CODE),
        ("confidence_gap_observation_count", CONFIDENCE_GAP_REASON_CODE),
    )
    for field_name, reason_code in reason_count_fields:
        if getattr(report, field_name) != _reason_count(report.rows, reason_code):
            raise ValueError(f"{field_name} must match rows")
    if report.average_blob_base_fee_spike_ratio != _average_decimal(
        tuple(row.blob_base_fee_spike_ratio for row in report.rows),
    ):
        raise ValueError("average_blob_base_fee_spike_ratio must match rows")
    if report.average_blob_gas_used_ratio != _average_decimal(
        tuple(row.blob_gas_used_ratio for row in report.rows),
    ):
        raise ValueError("average_blob_gas_used_ratio must match rows")
    if report.average_data_availability_backlog_ratio != _average_decimal(
        tuple(row.data_availability_backlog_ratio for row in report.rows),
    ):
        raise ValueError("average_data_availability_backlog_ratio must match rows")
    if report.average_batch_submission_delay_seconds != _average_decimal(
        tuple(row.batch_submission_delay_seconds for row in report.rows),
    ):
        raise ValueError("average_batch_submission_delay_seconds must match rows")
    expected_max_age = max(
        (row.observation_age_seconds for row in report.rows),
        default=ZERO,
    ).quantize(NUMERIC_QUANTUM)
    if report.max_observation_age_seconds != expected_max_age:
        raise ValueError("max_observation_age_seconds must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.source_config_versions != _source_config_versions(report.rows):
        raise ValueError("source_config_versions must match rows")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(NUMERIC_QUANTUM)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_signed_decimal(field_name: str, value: Decimal) -> Decimal:
    return _require_decimal(field_name, value).quantize(NUMERIC_QUANTUM)


def _normalize_unit_ratio(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return normalized


def _normalize_positive_count(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be non-empty canonical text")
    if not _is_ascii_lower_digit(value[0]):
        raise ValueError(f"{field_name} must start with lowercase text or a digit")
    for character in value:
        if not _is_canonical_character(character):
            raise ValueError(f"{field_name} must be canonical lowercase text")


def _require_public_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be non-empty public text")
    for character in value:
        ordinal = ord(character)
        if ordinal < 32 or ordinal > 126:
            raise ValueError(f"{field_name} must contain visible ASCII text")
    _reject_redacted_text(field_name, value)


def _reject_redacted_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    for term in _REDACTED_TERMS:
        if term in lowered:
            raise ValueError(f"{field_name} contains redacted text")


def _is_ascii_lower_digit(character: str) -> bool:
    return ("a" <= character <= "z") or ("0" <= character <= "9")


def _is_canonical_character(character: str) -> bool:
    return _is_ascii_lower_digit(character) or character in ("_", "-", ".")


def _require_member(field_name: str, value: str, allowed: tuple[str, ...]) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _normalize_reason_codes(
    field_name: str,
    values: tuple[str, ...],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    for value in values:
        if type(value) is not str:
            raise ValueError(f"{field_name} must contain strings")
        if value not in allowed:
            raise ValueError(f"{field_name} contains unsupported reason code")
        if value in seen:
            raise ValueError(f"{field_name} must not contain duplicate reason codes")
        seen.add(value)
    return tuple(value for value in allowed if value in seen)


def _normalize_rows(
    rows: tuple[MarketResearchCryptoLayer2BlobFeeSpikeDigestRow, ...],
) -> tuple[MarketResearchCryptoLayer2BlobFeeSpikeDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen: set[str] = set()
    normalized: list[MarketResearchCryptoLayer2BlobFeeSpikeDigestRow] = []
    for row in rows:
        if type(row) is not MarketResearchCryptoLayer2BlobFeeSpikeDigestRow:
            raise ValueError("rows must contain digest rows")
        if row.screening_key in seen:
            raise ValueError("rows must contain unique screening_key values")
        seen.add(row.screening_key)
        normalized.append(row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    rows: tuple[MarketResearchCryptoLayer2BlobFeeSpikeDigestReasonCodeCount, ...],
) -> tuple[MarketResearchCryptoLayer2BlobFeeSpikeDigestReasonCodeCount, ...]:
    if type(rows) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    seen: set[str] = set()
    normalized: list[MarketResearchCryptoLayer2BlobFeeSpikeDigestReasonCodeCount] = []
    for row in rows:
        if type(row) is not MarketResearchCryptoLayer2BlobFeeSpikeDigestReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason code count rows")
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must contain unique reason_code values")
        seen.add(row.reason_code)
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda row: ROW_REASON_CODES.index(row.reason_code)))


def _normalize_source_config_versions(
    rows: tuple[tuple[str, str], ...],
) -> tuple[tuple[str, str], ...]:
    if type(rows) is not tuple:
        raise ValueError("source_config_versions must be a tuple")
    normalized: list[tuple[str, str]] = []
    seen: set[str] = set()
    for item in rows:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("source_config_versions must contain pairs")
        screening_key, source_config_version = item
        _require_canonical_string("screening_key", screening_key)
        _require_canonical_string("source_config_version", source_config_version)
        _reject_redacted_text("source_config_version", source_config_version)
        if screening_key in seen:
            raise ValueError("source_config_versions must contain unique screening_key values")
        seen.add(screening_key)
        normalized.append((screening_key, source_config_version))
    return tuple(sorted(normalized, key=lambda item: item[0]))


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        flag = getattr(value, field_name)
        if type(flag) is not bool:
            raise ValueError(f"{label} {field_name} must be a bool")
        if flag is not True:
            raise ValueError(f"{field_name} must be True")


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Mapping):
        return MappingProxyType({key: _json_ready(child) for key, child in value.items()})
    if isinstance(value, tuple):
        return tuple(_json_ready(child) for child in value)
    if isinstance(value, list):
        return tuple(_json_ready(child) for child in value)
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return value
    if isinstance(value, int):
        raise ValueError("payload contains a non-Decimal numeric value")
    return value
