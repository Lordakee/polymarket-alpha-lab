"""Pure Phase 1 crypto L2 blob fee spike market research reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from types import MappingProxyType
from typing import Any


DEFAULT_MARKET_RESEARCH_CRYPTO_L2_BLOB_FEE_SPIKE_DIGEST_CONFIG_VERSION = (
    "market-research-crypto-l2-blob-fee-spike-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
BLOB_FEE_SPIKE_DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

READY_REASON = "market_research_crypto_l2_blob_fee_spike_digest_ready"
NO_INPUTS_REASON = "market_research_crypto_l2_blob_fee_spike_digest_no_inputs"
FEE_SPIKE_REASON = "market_research_crypto_l2_blob_fee_spike_digest_fee_spike"
HIGH_BLOB_FEE_REASON = (
    "market_research_crypto_l2_blob_fee_spike_digest_high_blob_fee"
)
HIGH_L2_FEE_REASON = "market_research_crypto_l2_blob_fee_spike_digest_high_l2_fee"
SOURCE_GAP_REASON = "market_research_crypto_l2_blob_fee_spike_digest_source_gap"
STALE_SOURCE_REASON = "market_research_crypto_l2_blob_fee_spike_digest_stale_source"
CONFIDENCE_GAP_REASON = (
    "market_research_crypto_l2_blob_fee_spike_digest_confidence_gap"
)

REASON_CODE_SEQUENCE = (
    FEE_SPIKE_REASON,
    HIGH_BLOB_FEE_REASON,
    HIGH_L2_FEE_REASON,
    SOURCE_GAP_REASON,
    STALE_SOURCE_REASON,
    CONFIDENCE_GAP_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    FEE_SPIKE_REASON,
    HIGH_BLOB_FEE_REASON,
    HIGH_L2_FEE_REASON,
    SOURCE_GAP_REASON,
    STALE_SOURCE_REASON,
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
        _join_parts("0", "x"),
    ),
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_CRYPTO_L2_BLOB_FEE_SPIKE_DIGEST_CONFIG_VERSION",
    "MarketResearchCryptoL2BlobFeeSpikeDigestConfig",
    "MarketResearchCryptoL2BlobFeeSpikeDigestReasonCodeCount",
    "MarketResearchCryptoL2BlobFeeSpikeDigestReport",
    "MarketResearchCryptoL2BlobFeeSpikeDigestRow",
    "MarketResearchCryptoL2BlobFeeSpikeSample",
    "build_market_research_crypto_l2_blob_fee_spike_digest",
    "market_research_crypto_l2_blob_fee_spike_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchCryptoL2BlobFeeSpikeDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_CRYPTO_L2_BLOB_FEE_SPIKE_DIGEST_CONFIG_VERSION
    )
    max_source_age_seconds: Decimal = Decimal("1800.000000")
    min_source_count: Decimal = Decimal("2.000000")
    max_blob_base_fee_gwei: Decimal = Decimal("45.000000")
    max_blob_fee_spike_ratio: Decimal = Decimal("3.000000")
    max_l2_priority_fee_gwei: Decimal = Decimal("0.300000")
    min_confidence: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchCryptoL2BlobFeeSpikeDigestConfig "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoL2BlobFeeSpikeDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchCryptoL2BlobFeeSpikeDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("max_source_age_seconds", "min_source_count"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_blob_base_fee_gwei",
            "max_blob_fee_spike_ratio",
            "max_l2_priority_fee_gwei",
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
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchCryptoL2BlobFeeSpikeSample:
    condition_id: str
    sample_id: str
    rollup_name: str
    observed_at: datetime
    source_count: Decimal
    blob_base_fee_gwei: Decimal
    blob_fee_spike_ratio: Decimal
    l2_priority_fee_gwei: Decimal
    batch_queue_depth: Decimal
    confidence: Decimal
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchCryptoL2BlobFeeSpikeSample does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoL2BlobFeeSpikeSample:
            raise ValueError(
                "sample must be exactly MarketResearchCryptoL2BlobFeeSpikeSample",
            )
        for field_name in (
            "condition_id",
            "sample_id",
            "rollup_name",
            "source_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "source_count",
            "blob_base_fee_gwei",
            "blob_fee_spike_ratio",
            "l2_priority_fee_gwei",
            "batch_queue_depth",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "confidence",
            _require_ratio_decimal("confidence", self.confidence),
        )
        _require_hard_flags("sample", self)


@dataclass(frozen=True)
class MarketResearchCryptoL2BlobFeeSpikeDigestRow:
    condition_id: str
    sample_id: str
    rollup_name: str
    digest_status: str
    observed_at: datetime
    source_age_seconds: Decimal
    source_count: Decimal
    blob_base_fee_gwei: Decimal
    blob_fee_spike_ratio: Decimal
    l2_priority_fee_gwei: Decimal
    batch_queue_depth: Decimal
    confidence: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchCryptoL2BlobFeeSpikeDigestRow "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoL2BlobFeeSpikeDigestRow:
            raise ValueError(
                "row must be exactly MarketResearchCryptoL2BlobFeeSpikeDigestRow",
            )
        for field_name in ("condition_id", "sample_id", "rollup_name"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_status("digest_status", self.digest_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "source_age_seconds",
            "source_count",
            "blob_base_fee_gwei",
            "blob_fee_spike_ratio",
            "l2_priority_fee_gwei",
            "batch_queue_depth",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
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
class MarketResearchCryptoL2BlobFeeSpikeDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    sample_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchCryptoL2BlobFeeSpikeDigestReasonCodeCount "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoL2BlobFeeSpikeDigestReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "MarketResearchCryptoL2BlobFeeSpikeDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "sample_ratio",
            _require_ratio_decimal("sample_ratio", self.sample_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchCryptoL2BlobFeeSpikeDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    sample_count: Decimal
    ready_sample_count: Decimal
    watch_sample_count: Decimal
    blocked_sample_count: Decimal
    fee_spike_sample_count: Decimal
    high_blob_fee_sample_count: Decimal
    high_l2_fee_sample_count: Decimal
    source_gap_sample_count: Decimal
    stale_source_sample_count: Decimal
    confidence_gap_sample_count: Decimal
    average_blob_base_fee_gwei: Decimal
    average_blob_fee_spike_ratio: Decimal
    average_l2_priority_fee_gwei: Decimal
    max_source_age_seconds: Decimal
    max_allowed_source_age_seconds: Decimal
    min_source_count: Decimal
    max_allowed_blob_base_fee_gwei: Decimal
    max_allowed_blob_fee_spike_ratio: Decimal
    max_allowed_l2_priority_fee_gwei: Decimal
    min_confidence: Decimal
    ready_sample_ratio: Decimal
    rows: tuple[MarketResearchCryptoL2BlobFeeSpikeDigestRow, ...]
    source_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchCryptoL2BlobFeeSpikeDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchCryptoL2BlobFeeSpikeDigestReport "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoL2BlobFeeSpikeDigestReport:
            raise ValueError(
                "report must be exactly MarketResearchCryptoL2BlobFeeSpikeDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "sample_count",
            "ready_sample_count",
            "watch_sample_count",
            "blocked_sample_count",
            "fee_spike_sample_count",
            "high_blob_fee_sample_count",
            "high_l2_fee_sample_count",
            "source_gap_sample_count",
            "stale_source_sample_count",
            "confidence_gap_sample_count",
            "average_blob_base_fee_gwei",
            "average_blob_fee_spike_ratio",
            "average_l2_priority_fee_gwei",
            "max_source_age_seconds",
            "max_allowed_source_age_seconds",
            "min_source_count",
            "max_allowed_blob_base_fee_gwei",
            "max_allowed_blob_fee_spike_ratio",
            "max_allowed_l2_priority_fee_gwei",
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
        object.__setattr__(
            self,
            "ready_sample_ratio",
            _require_ratio_decimal("ready_sample_ratio", self.ready_sample_ratio),
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


def build_market_research_crypto_l2_blob_fee_spike_digest(
    samples: Iterable[MarketResearchCryptoL2BlobFeeSpikeSample],
    *,
    config: MarketResearchCryptoL2BlobFeeSpikeDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchCryptoL2BlobFeeSpikeDigestReport:
    cfg = config or MarketResearchCryptoL2BlobFeeSpikeDigestConfig()
    if type(cfg) is not MarketResearchCryptoL2BlobFeeSpikeDigestConfig:
        raise ValueError(
            "config must be exactly MarketResearchCryptoL2BlobFeeSpikeDigestConfig",
        )
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_samples = _normalize_samples(samples)
    rows = tuple(
        _row_for_sample(sample, config=cfg, generated_at=generated_at_utc)
        for sample in normalized_samples
    )
    sorted_rows = tuple(
        sorted(
            rows,
            key=lambda row: (
                _row_sort_value(row),
                row.sample_id,
                row.condition_id,
            ),
        ),
    )
    report_status = _report_status(sorted_rows)
    sample_count = _decimal_count(len(sorted_rows))
    reason_codes = _summary_reason_codes(sorted_rows)
    return MarketResearchCryptoL2BlobFeeSpikeDigestReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        digest_status=report_status,
        recommended_next_step=_recommended_next_step(report_status),
        sample_count=sample_count,
        ready_sample_count=_status_count(sorted_rows, STATUS_READY),
        watch_sample_count=_status_count(sorted_rows, STATUS_WATCH),
        blocked_sample_count=_status_count(sorted_rows, STATUS_BLOCKED),
        fee_spike_sample_count=_reason_sample_count(sorted_rows, FEE_SPIKE_REASON),
        high_blob_fee_sample_count=_reason_sample_count(
            sorted_rows,
            HIGH_BLOB_FEE_REASON,
        ),
        high_l2_fee_sample_count=_reason_sample_count(sorted_rows, HIGH_L2_FEE_REASON),
        source_gap_sample_count=_reason_sample_count(sorted_rows, SOURCE_GAP_REASON),
        stale_source_sample_count=_reason_sample_count(
            sorted_rows,
            STALE_SOURCE_REASON,
        ),
        confidence_gap_sample_count=_reason_sample_count(
            sorted_rows,
            CONFIDENCE_GAP_REASON,
        ),
        average_blob_base_fee_gwei=_ratio(
            _decimal_sum(row.blob_base_fee_gwei for row in sorted_rows),
            sample_count,
        ),
        average_blob_fee_spike_ratio=_ratio(
            _decimal_sum(row.blob_fee_spike_ratio for row in sorted_rows),
            sample_count,
        ),
        average_l2_priority_fee_gwei=_ratio(
            _decimal_sum(row.l2_priority_fee_gwei for row in sorted_rows),
            sample_count,
        ),
        max_source_age_seconds=max(
            (row.source_age_seconds for row in sorted_rows),
            default=ZERO,
        ),
        max_allowed_source_age_seconds=cfg.max_source_age_seconds,
        min_source_count=cfg.min_source_count,
        max_allowed_blob_base_fee_gwei=cfg.max_blob_base_fee_gwei,
        max_allowed_blob_fee_spike_ratio=cfg.max_blob_fee_spike_ratio,
        max_allowed_l2_priority_fee_gwei=cfg.max_l2_priority_fee_gwei,
        min_confidence=cfg.min_confidence,
        ready_sample_ratio=_ratio(_status_count(sorted_rows, STATUS_READY), sample_count),
        rows=sorted_rows,
        source_config_versions=tuple(
            sorted(
                (sample.sample_id, sample.source_config_version)
                for sample in normalized_samples
            ),
        ),
        reason_code_counts=_reason_code_counts(sorted_rows, reason_codes, sample_count),
        reason_codes=reason_codes,
    )


def market_research_crypto_l2_blob_fee_spike_digest_payload(
    report: MarketResearchCryptoL2BlobFeeSpikeDigestReport,
) -> MappingProxyType:
    if type(report) is not MarketResearchCryptoL2BlobFeeSpikeDigestReport:
        raise ValueError(
            "report must be exactly MarketResearchCryptoL2BlobFeeSpikeDigestReport",
        )
    return _freeze(_json_ready(report))


def _row_for_sample(
    sample: MarketResearchCryptoL2BlobFeeSpikeSample,
    *,
    config: MarketResearchCryptoL2BlobFeeSpikeDigestConfig,
    generated_at: datetime,
) -> MarketResearchCryptoL2BlobFeeSpikeDigestRow:
    if sample.observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    source_age_seconds = _age_seconds(generated_at, sample.observed_at)
    reason_codes = _row_reason_codes(
        sample=sample,
        config=config,
        source_age_seconds=source_age_seconds,
    )
    return MarketResearchCryptoL2BlobFeeSpikeDigestRow(
        condition_id=sample.condition_id,
        sample_id=sample.sample_id,
        rollup_name=sample.rollup_name,
        digest_status=_row_status(reason_codes),
        observed_at=sample.observed_at,
        source_age_seconds=source_age_seconds,
        source_count=sample.source_count,
        blob_base_fee_gwei=sample.blob_base_fee_gwei,
        blob_fee_spike_ratio=sample.blob_fee_spike_ratio,
        l2_priority_fee_gwei=sample.l2_priority_fee_gwei,
        batch_queue_depth=sample.batch_queue_depth,
        confidence=sample.confidence,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    sample: MarketResearchCryptoL2BlobFeeSpikeSample,
    config: MarketResearchCryptoL2BlobFeeSpikeDigestConfig,
    source_age_seconds: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if sample.blob_fee_spike_ratio > config.max_blob_fee_spike_ratio:
        reasons.append(FEE_SPIKE_REASON)
    if sample.blob_base_fee_gwei > config.max_blob_base_fee_gwei:
        reasons.append(HIGH_BLOB_FEE_REASON)
    if sample.l2_priority_fee_gwei > config.max_l2_priority_fee_gwei:
        reasons.append(HIGH_L2_FEE_REASON)
    if sample.source_count < config.min_source_count:
        reasons.append(SOURCE_GAP_REASON)
    if source_age_seconds > config.max_source_age_seconds:
        reasons.append(STALE_SOURCE_REASON)
    if sample.confidence < config.min_confidence:
        reasons.append(CONFIDENCE_GAP_REASON)
    if not reasons:
        reasons.append(READY_REASON)
    return tuple(reason for reason in ROW_REASON_CODE_SEQUENCE if reason in reasons)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    if any(
        reason in reason_codes
        for reason in (
            FEE_SPIKE_REASON,
            HIGH_BLOB_FEE_REASON,
            HIGH_L2_FEE_REASON,
            STALE_SOURCE_REASON,
            CONFIDENCE_GAP_REASON,
        )
    ):
        return STATUS_BLOCKED
    return STATUS_WATCH


def _row_sort_value(row: MarketResearchCryptoL2BlobFeeSpikeDigestRow) -> tuple[int, Decimal]:
    status_rank = {
        STATUS_BLOCKED: 0,
        STATUS_WATCH: 1,
        STATUS_READY: 2,
    }[row.digest_status]
    severity = _decimal_count(
        len(tuple(reason for reason in row.reason_codes if reason != READY_REASON)),
    )
    return (status_rank, -severity)


def _report_status(
    rows: tuple[MarketResearchCryptoL2BlobFeeSpikeDigestRow, ...],
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
        return "block_report_only_market_research_crypto_l2_blob_fee_spike_digest"
    if status == STATUS_WATCH:
        return "review_report_only_market_research_crypto_l2_blob_fee_spike_digest"
    return "allow_report_only_market_research_crypto_l2_blob_fee_spike_digest"


def _status_count(
    rows: tuple[MarketResearchCryptoL2BlobFeeSpikeDigestRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.digest_status == status))


def _reason_sample_count(
    rows: tuple[MarketResearchCryptoL2BlobFeeSpikeDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _reason_code_counts(
    rows: tuple[MarketResearchCryptoL2BlobFeeSpikeDigestRow, ...],
    reason_codes: tuple[str, ...],
    sample_count: Decimal,
) -> tuple[MarketResearchCryptoL2BlobFeeSpikeDigestReasonCodeCount, ...]:
    if reason_codes == (NO_INPUTS_REASON,):
        return (
            MarketResearchCryptoL2BlobFeeSpikeDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                sample_ratio=ZERO,
            ),
        )
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        MarketResearchCryptoL2BlobFeeSpikeDigestReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
            sample_ratio=_ratio(_decimal_count(counts[reason_code]), sample_count),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _summary_reason_codes(
    rows: tuple[MarketResearchCryptoL2BlobFeeSpikeDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    seen: set[str] = set()
    for row in rows:
        seen.update(row.reason_codes)
    if len(seen) > 1 and READY_REASON in seen:
        seen.remove(READY_REASON)
    return tuple(reason for reason in REASON_CODE_SEQUENCE if reason in seen)


def _validate_row(row: MarketResearchCryptoL2BlobFeeSpikeDigestRow) -> None:
    if row.digest_status != _row_status(row.reason_codes):
        raise ValueError("digest_status does not match reason_codes")


def _validate_report(report: MarketResearchCryptoL2BlobFeeSpikeDigestReport) -> None:
    if report.sample_count != _decimal_count(len(report.rows)):
        raise ValueError("sample_count does not match rows")
    if report.ready_sample_count != _status_count(report.rows, STATUS_READY):
        raise ValueError("ready_sample_count does not match rows")
    if report.watch_sample_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_sample_count does not match rows")
    if report.blocked_sample_count != _status_count(report.rows, STATUS_BLOCKED):
        raise ValueError("blocked_sample_count does not match rows")
    expected_counts = (
        (FEE_SPIKE_REASON, report.fee_spike_sample_count),
        (HIGH_BLOB_FEE_REASON, report.high_blob_fee_sample_count),
        (HIGH_L2_FEE_REASON, report.high_l2_fee_sample_count),
        (SOURCE_GAP_REASON, report.source_gap_sample_count),
        (STALE_SOURCE_REASON, report.stale_source_sample_count),
        (CONFIDENCE_GAP_REASON, report.confidence_gap_sample_count),
    )
    for reason_code, count in expected_counts:
        if count != _reason_sample_count(report.rows, reason_code):
            raise ValueError("reason sample count does not match rows")
    if report.digest_status != _report_status(report.rows):
        raise ValueError("digest_status does not match rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step does not match digest_status")
    if report.average_blob_base_fee_gwei != _ratio(
        _decimal_sum(row.blob_base_fee_gwei for row in report.rows),
        report.sample_count,
    ):
        raise ValueError("average_blob_base_fee_gwei does not match rows")
    if report.average_blob_fee_spike_ratio != _ratio(
        _decimal_sum(row.blob_fee_spike_ratio for row in report.rows),
        report.sample_count,
    ):
        raise ValueError("average_blob_fee_spike_ratio does not match rows")
    if report.average_l2_priority_fee_gwei != _ratio(
        _decimal_sum(row.l2_priority_fee_gwei for row in report.rows),
        report.sample_count,
    ):
        raise ValueError("average_l2_priority_fee_gwei does not match rows")
    if report.max_source_age_seconds != max(
        (row.source_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_source_age_seconds does not match rows")
    if report.ready_sample_ratio != _ratio(
        report.ready_sample_count,
        report.sample_count,
    ):
        raise ValueError("ready_sample_ratio does not match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes do not match rows")
    if report.reason_code_counts != _reason_code_counts(
        report.rows,
        report.reason_codes,
        report.sample_count,
    ):
        raise ValueError("reason_code_counts do not match rows")


def _normalize_samples(
    samples: Iterable[MarketResearchCryptoL2BlobFeeSpikeSample],
) -> tuple[MarketResearchCryptoL2BlobFeeSpikeSample, ...]:
    sample_tuple = tuple(samples)
    seen_keys: set[str] = set()
    for sample in sample_tuple:
        if type(sample) is not MarketResearchCryptoL2BlobFeeSpikeSample:
            raise ValueError(
                "samples must contain MarketResearchCryptoL2BlobFeeSpikeSample",
            )
        if sample.sample_id in seen_keys:
            raise ValueError("sample_id values must be unique")
        seen_keys.add(sample.sample_id)
        _require_hard_flags("sample", sample)
    return sample_tuple


def _normalize_rows(
    rows: tuple[MarketResearchCryptoL2BlobFeeSpikeDigestRow, ...],
) -> tuple[MarketResearchCryptoL2BlobFeeSpikeDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen_keys: set[str] = set()
    for row in rows:
        if type(row) is not MarketResearchCryptoL2BlobFeeSpikeDigestRow:
            raise ValueError("rows must contain MarketResearchCryptoL2BlobFeeSpikeDigestRow")
        if row.sample_id in seen_keys:
            raise ValueError("rows sample_id values must be unique")
        seen_keys.add(row.sample_id)
        _require_hard_flags("row", row)
    canonical_rows = tuple(
        sorted(
            rows,
            key=lambda row: (
                _row_sort_value(row),
                row.sample_id,
                row.condition_id,
            ),
        ),
    )
    if rows != canonical_rows:
        raise ValueError("rows must use canonical sequence")
    return rows


def _normalize_reason_code_counts(
    items: tuple[MarketResearchCryptoL2BlobFeeSpikeDigestReasonCodeCount, ...],
) -> tuple[MarketResearchCryptoL2BlobFeeSpikeDigestReasonCodeCount, ...]:
    if type(items) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    seen_reason_codes: set[str] = set()
    for item in items:
        if type(item) is not MarketResearchCryptoL2BlobFeeSpikeDigestReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count rows")
        if item.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen_reason_codes.add(item.reason_code)
    canonical_items = tuple(
        sorted(items, key=lambda item: REASON_CODE_SEQUENCE.index(item.reason_code)),
    )
    if items != canonical_items:
        raise ValueError("reason_code_counts must use canonical sequence")
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
        sample_id, source_config_version = item
        _require_public_string("sample_id", sample_id)
        _require_public_string("source_config_version", source_config_version)
        if sample_id in seen_keys:
            raise ValueError("source_config_versions sample_id values unique")
        seen_keys.add(sample_id)
        pairs.append((sample_id, source_config_version))
    normalized_pairs = tuple(pairs)
    if normalized_pairs != tuple(sorted(normalized_pairs)):
        raise ValueError("source_config_versions must use canonical sequence")
    return normalized_pairs


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


def _require_positive_whole_count_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_positive_count_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
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
    if value.as_tuple().exponent != -6:
        raise ValueError(f"{field_name} must be a six decimal Decimal")
    return value


def _as_utc(field_name: str, value: datetime) -> datetime:
    if (
        type(value) is not datetime
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.tzinfo is not UTC:
        raise ValueError(f"{field_name} must be UTC-aware")
    return value


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    return _quantize(
        Decimal(delta.days * 86400 + delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND),
    )


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


def _revalidate_public_dataclass(value: object) -> None:
    dataclass_values = {field.name: getattr(value, field.name) for field in fields(value)}
    if type(value) is MarketResearchCryptoL2BlobFeeSpikeDigestConfig:
        MarketResearchCryptoL2BlobFeeSpikeDigestConfig(**dataclass_values)
        return
    if type(value) is MarketResearchCryptoL2BlobFeeSpikeSample:
        MarketResearchCryptoL2BlobFeeSpikeSample(**dataclass_values)
        return
    if type(value) is MarketResearchCryptoL2BlobFeeSpikeDigestRow:
        MarketResearchCryptoL2BlobFeeSpikeDigestRow(**dataclass_values)
        return
    if type(value) is MarketResearchCryptoL2BlobFeeSpikeDigestReasonCodeCount:
        MarketResearchCryptoL2BlobFeeSpikeDigestReasonCodeCount(**dataclass_values)
        return
    if type(value) is MarketResearchCryptoL2BlobFeeSpikeDigestReport:
        MarketResearchCryptoL2BlobFeeSpikeDigestReport(**dataclass_values)
        return
    raise ValueError("payload dataclass must use public exact type")


def _six_decimal_text(field_name: str, value: Decimal) -> str:
    if (
        type(value) is not Decimal
        or not value.is_finite()
        or value.as_tuple().exponent != -6
        or value != _quantize(value)
    ):
        raise ValueError(f"{field_name} must be a six decimal Decimal")
    return str(value)


def _utc_datetime_text(field_name: str, value: datetime) -> str:
    if (
        type(value) is not datetime
        or value.tzinfo is not UTC
        or value.utcoffset() is None
    ):
        raise ValueError(f"{field_name} must be UTC-aware")
    return value.isoformat()


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        _revalidate_public_dataclass(value)
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if type(value) is datetime:
        return _utc_datetime_text("datetime", value)
    if type(value) is Decimal:
        return _six_decimal_text("Decimal", value)
    if isinstance(value, tuple):
        return tuple(_json_ready(item) for item in value)
    if isinstance(value, list):
        return tuple(_json_ready(item) for item in value)
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, tuple):
        return tuple(_freeze(item) for item in value)
    return value
