"""Pure Phase 1 crypto stablecoin redemption-queue market research reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from types import MappingProxyType
from typing import Any


DEFAULT_MARKET_RESEARCH_CRYPTO_STABLECOIN_REDEMPTION_QUEUE_DIGEST_CONFIG_VERSION = (
    "market-research-crypto-stablecoin-redemption-queue-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
REDEMPTION_QUEUE_DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

READY_REASON = "market_research_crypto_stablecoin_redemption_queue_digest_ready"
NO_INPUTS_REASON = "market_research_crypto_stablecoin_redemption_queue_digest_no_inputs"
QUEUE_SIZE_REASON = "market_research_crypto_stablecoin_redemption_queue_digest_queue_size"
QUEUE_RATIO_REASON = (
    "market_research_crypto_stablecoin_redemption_queue_digest_queue_ratio"
)
QUEUE_GROWTH_REASON = (
    "market_research_crypto_stablecoin_redemption_queue_digest_queue_growth"
)
WAIT_TIME_REASON = "market_research_crypto_stablecoin_redemption_queue_digest_wait_time"
RESERVE_GAP_REASON = (
    "market_research_crypto_stablecoin_redemption_queue_digest_reserve_gap"
)
SOURCE_DIVERSITY_GAP_REASON = (
    "market_research_crypto_stablecoin_redemption_queue_digest_source_diversity_gap"
)
STALE_SNAPSHOT_REASON = (
    "market_research_crypto_stablecoin_redemption_queue_digest_stale_snapshot"
)
CONFIDENCE_GAP_REASON = (
    "market_research_crypto_stablecoin_redemption_queue_digest_confidence_gap"
)

REASON_CODE_SEQUENCE = (
    QUEUE_SIZE_REASON,
    QUEUE_RATIO_REASON,
    QUEUE_GROWTH_REASON,
    WAIT_TIME_REASON,
    RESERVE_GAP_REASON,
    SOURCE_DIVERSITY_GAP_REASON,
    STALE_SNAPSHOT_REASON,
    CONFIDENCE_GAP_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    QUEUE_SIZE_REASON,
    QUEUE_RATIO_REASON,
    QUEUE_GROWTH_REASON,
    WAIT_TIME_REASON,
    RESERVE_GAP_REASON,
    SOURCE_DIVERSITY_GAP_REASON,
    STALE_SNAPSHOT_REASON,
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
    "DEFAULT_MARKET_RESEARCH_CRYPTO_STABLECOIN_REDEMPTION_QUEUE_DIGEST_CONFIG_VERSION",
    "MarketResearchCryptoStablecoinRedemptionQueueDigestConfig",
    "MarketResearchCryptoStablecoinRedemptionQueueDigestReasonCodeCount",
    "MarketResearchCryptoStablecoinRedemptionQueueDigestReport",
    "MarketResearchCryptoStablecoinRedemptionQueueDigestRow",
    "MarketResearchCryptoStablecoinRedemptionQueueSnapshot",
    "build_market_research_crypto_stablecoin_redemption_queue_digest",
    "market_research_crypto_stablecoin_redemption_queue_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchCryptoStablecoinRedemptionQueueDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_CRYPTO_STABLECOIN_REDEMPTION_QUEUE_DIGEST_CONFIG_VERSION
    )
    max_snapshot_age_seconds: Decimal = Decimal("1800.000000")
    max_redemption_queue_usd: Decimal = Decimal("750000000.000000")
    max_queue_ratio: Decimal = Decimal("0.120000")
    max_queue_growth_ratio: Decimal = Decimal("0.250000")
    max_estimated_wait_hours: Decimal = Decimal("24.000000")
    min_source_count: Decimal = Decimal("3.000000")
    min_reserve_coverage_ratio: Decimal = Decimal("1.000000")
    min_confidence: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoStablecoinRedemptionQueueDigestConfig:
            raise TypeError(
                "MarketResearchCryptoStablecoinRedemptionQueueDigestConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoStablecoinRedemptionQueueDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchCryptoStablecoinRedemptionQueueDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "max_snapshot_age_seconds",
            "max_estimated_wait_hours",
            "min_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_redemption_queue_usd",
            _require_nonnegative_count_decimal(
                "max_redemption_queue_usd",
                self.max_redemption_queue_usd,
            ),
        )
        for field_name in (
            "max_queue_ratio",
            "min_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_queue_growth_ratio",
            _require_nonnegative_count_decimal(
                "max_queue_growth_ratio",
                self.max_queue_growth_ratio,
            ),
        )
        object.__setattr__(
            self,
            "min_reserve_coverage_ratio",
            _require_nonnegative_count_decimal(
                "min_reserve_coverage_ratio",
                self.min_reserve_coverage_ratio,
            ),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchCryptoStablecoinRedemptionQueueSnapshot:
    condition_id: str
    redemption_queue_key: str
    stablecoin_symbol: str
    observed_at: datetime
    redemption_queue_usd: Decimal
    previous_redemption_queue_usd: Decimal
    circulating_supply_usd: Decimal
    reserve_coverage_ratio: Decimal
    estimated_wait_hours: Decimal
    source_count: Decimal
    confidence: Decimal
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoStablecoinRedemptionQueueSnapshot:
            raise TypeError(
                "MarketResearchCryptoStablecoinRedemptionQueueSnapshot "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoStablecoinRedemptionQueueSnapshot:
            raise ValueError(
                "snapshot must be exactly "
                "MarketResearchCryptoStablecoinRedemptionQueueSnapshot",
            )
        for field_name in (
            "condition_id",
            "redemption_queue_key",
            "stablecoin_symbol",
            "source_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "redemption_queue_usd",
            "previous_redemption_queue_usd",
            "circulating_supply_usd",
            "estimated_wait_hours",
            "source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reserve_coverage_ratio",
            _require_nonnegative_count_decimal(
                "reserve_coverage_ratio",
                self.reserve_coverage_ratio,
            ),
        )
        object.__setattr__(
            self,
            "confidence",
            _require_ratio_decimal("confidence", self.confidence),
        )
        _require_hard_flags("snapshot", self)


@dataclass(frozen=True)
class MarketResearchCryptoStablecoinRedemptionQueueDigestRow:
    condition_id: str
    redemption_queue_key: str
    stablecoin_symbol: str
    digest_status: str
    observed_at: datetime
    snapshot_age_seconds: Decimal
    redemption_queue_usd: Decimal
    previous_redemption_queue_usd: Decimal
    circulating_supply_usd: Decimal
    queue_ratio: Decimal
    queue_growth_ratio: Decimal
    reserve_coverage_ratio: Decimal
    estimated_wait_hours: Decimal
    source_count: Decimal
    confidence: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoStablecoinRedemptionQueueDigestRow:
            raise TypeError(
                "MarketResearchCryptoStablecoinRedemptionQueueDigestRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoStablecoinRedemptionQueueDigestRow:
            raise ValueError(
                "row must be exactly "
                "MarketResearchCryptoStablecoinRedemptionQueueDigestRow",
            )
        for field_name in (
            "condition_id",
            "redemption_queue_key",
            "stablecoin_symbol",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_status("digest_status", self.digest_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "snapshot_age_seconds",
            "redemption_queue_usd",
            "previous_redemption_queue_usd",
            "circulating_supply_usd",
            "estimated_wait_hours",
            "source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "queue_ratio",
            "confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "queue_growth_ratio",
            _require_nonnegative_count_decimal(
                "queue_growth_ratio",
                self.queue_growth_ratio,
            ),
        )
        object.__setattr__(
            self,
            "reserve_coverage_ratio",
            _require_nonnegative_count_decimal(
                "reserve_coverage_ratio",
                self.reserve_coverage_ratio,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, sequence=ROW_REASON_CODE_SEQUENCE),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchCryptoStablecoinRedemptionQueueDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    snapshot_ratio: Decimal

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoStablecoinRedemptionQueueDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchCryptoStablecoinRedemptionQueueDigestReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoStablecoinRedemptionQueueDigestReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "MarketResearchCryptoStablecoinRedemptionQueueDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "snapshot_ratio",
            _require_ratio_decimal("snapshot_ratio", self.snapshot_ratio),
        )


@dataclass(frozen=True)
class MarketResearchCryptoStablecoinRedemptionQueueDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    snapshot_count: Decimal
    ready_snapshot_count: Decimal
    watch_snapshot_count: Decimal
    blocked_snapshot_count: Decimal
    queue_size_snapshot_count: Decimal
    queue_ratio_snapshot_count: Decimal
    queue_growth_snapshot_count: Decimal
    wait_time_snapshot_count: Decimal
    reserve_gap_snapshot_count: Decimal
    source_diversity_gap_snapshot_count: Decimal
    stale_snapshot_count: Decimal
    confidence_gap_snapshot_count: Decimal
    average_queue_ratio: Decimal
    average_queue_growth_ratio: Decimal
    average_estimated_wait_hours: Decimal
    max_snapshot_age_seconds: Decimal
    max_allowed_snapshot_age_seconds: Decimal
    max_allowed_redemption_queue_usd: Decimal
    max_allowed_queue_ratio: Decimal
    max_allowed_queue_growth_ratio: Decimal
    max_allowed_estimated_wait_hours: Decimal
    min_source_count: Decimal
    min_reserve_coverage_ratio: Decimal
    min_confidence: Decimal
    rows: tuple[MarketResearchCryptoStablecoinRedemptionQueueDigestRow, ...]
    source_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchCryptoStablecoinRedemptionQueueDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoStablecoinRedemptionQueueDigestReport:
            raise TypeError(
                "MarketResearchCryptoStablecoinRedemptionQueueDigestReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoStablecoinRedemptionQueueDigestReport:
            raise ValueError(
                "report must be exactly "
                "MarketResearchCryptoStablecoinRedemptionQueueDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "snapshot_count",
            "ready_snapshot_count",
            "watch_snapshot_count",
            "blocked_snapshot_count",
            "queue_size_snapshot_count",
            "queue_ratio_snapshot_count",
            "queue_growth_snapshot_count",
            "wait_time_snapshot_count",
            "reserve_gap_snapshot_count",
            "source_diversity_gap_snapshot_count",
            "stale_snapshot_count",
            "confidence_gap_snapshot_count",
            "average_estimated_wait_hours",
            "max_snapshot_age_seconds",
            "max_allowed_snapshot_age_seconds",
            "max_allowed_redemption_queue_usd",
            "average_queue_growth_ratio",
            "max_allowed_queue_growth_ratio",
            "max_allowed_estimated_wait_hours",
            "min_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_queue_ratio",
            "max_allowed_queue_ratio",
            "min_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_reserve_coverage_ratio",
            _require_nonnegative_count_decimal(
                "min_reserve_coverage_ratio",
                self.min_reserve_coverage_ratio,
            ),
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


def build_market_research_crypto_stablecoin_redemption_queue_digest(
    snapshots: Iterable[MarketResearchCryptoStablecoinRedemptionQueueSnapshot],
    *,
    config: MarketResearchCryptoStablecoinRedemptionQueueDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchCryptoStablecoinRedemptionQueueDigestReport:
    cfg = config or MarketResearchCryptoStablecoinRedemptionQueueDigestConfig()
    if type(cfg) is not MarketResearchCryptoStablecoinRedemptionQueueDigestConfig:
        raise ValueError(
            "config must be exactly "
            "MarketResearchCryptoStablecoinRedemptionQueueDigestConfig",
        )
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_snapshots = _normalize_snapshots(snapshots)
    rows = tuple(
        _row_for_snapshot(snapshot, config=cfg, generated_at=generated_at_utc)
        for snapshot in normalized_snapshots
    )
    sorted_rows = tuple(
        sorted(
            rows,
            key=lambda row: (
                _row_sort_value(row),
                row.redemption_queue_key,
                row.condition_id,
            ),
        ),
    )
    report_status = _report_status(sorted_rows)
    return MarketResearchCryptoStablecoinRedemptionQueueDigestReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        digest_status=report_status,
        recommended_next_step=_recommended_next_step(report_status),
        snapshot_count=_decimal_count(len(sorted_rows)),
        ready_snapshot_count=_status_count(sorted_rows, STATUS_READY),
        watch_snapshot_count=_status_count(sorted_rows, STATUS_WATCH),
        blocked_snapshot_count=_status_count(sorted_rows, STATUS_BLOCKED),
        queue_size_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            QUEUE_SIZE_REASON,
        ),
        queue_ratio_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            QUEUE_RATIO_REASON,
        ),
        queue_growth_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            QUEUE_GROWTH_REASON,
        ),
        wait_time_snapshot_count=_reason_snapshot_count(sorted_rows, WAIT_TIME_REASON),
        reserve_gap_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            RESERVE_GAP_REASON,
        ),
        source_diversity_gap_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            SOURCE_DIVERSITY_GAP_REASON,
        ),
        stale_snapshot_count=_reason_snapshot_count(sorted_rows, STALE_SNAPSHOT_REASON),
        confidence_gap_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            CONFIDENCE_GAP_REASON,
        ),
        average_queue_ratio=_ratio(
            _decimal_sum(row.queue_ratio for row in sorted_rows),
            _decimal_count(len(sorted_rows)),
        ),
        average_queue_growth_ratio=_ratio(
            _decimal_sum(row.queue_growth_ratio for row in sorted_rows),
            _decimal_count(len(sorted_rows)),
        ),
        average_estimated_wait_hours=_ratio(
            _decimal_sum(row.estimated_wait_hours for row in sorted_rows),
            _decimal_count(len(sorted_rows)),
        ),
        max_snapshot_age_seconds=max(
            (row.snapshot_age_seconds for row in sorted_rows),
            default=ZERO,
        ),
        max_allowed_snapshot_age_seconds=cfg.max_snapshot_age_seconds,
        max_allowed_redemption_queue_usd=cfg.max_redemption_queue_usd,
        max_allowed_queue_ratio=cfg.max_queue_ratio,
        max_allowed_queue_growth_ratio=cfg.max_queue_growth_ratio,
        max_allowed_estimated_wait_hours=cfg.max_estimated_wait_hours,
        min_source_count=cfg.min_source_count,
        min_reserve_coverage_ratio=cfg.min_reserve_coverage_ratio,
        min_confidence=cfg.min_confidence,
        rows=sorted_rows,
        source_config_versions=tuple(
            sorted(
                (snapshot.redemption_queue_key, snapshot.source_config_version)
                for snapshot in normalized_snapshots
            ),
        ),
        reason_code_counts=_reason_code_counts(sorted_rows),
        reason_codes=_summary_reason_codes(sorted_rows),
    )


def market_research_crypto_stablecoin_redemption_queue_digest_payload(
    report: MarketResearchCryptoStablecoinRedemptionQueueDigestReport,
) -> MappingProxyType:
    if type(report) is not MarketResearchCryptoStablecoinRedemptionQueueDigestReport:
        raise ValueError(
            "report must be exactly "
            "MarketResearchCryptoStablecoinRedemptionQueueDigestReport",
        )
    return _freeze(_json_ready(report))


def _row_for_snapshot(
    snapshot: MarketResearchCryptoStablecoinRedemptionQueueSnapshot,
    *,
    config: MarketResearchCryptoStablecoinRedemptionQueueDigestConfig,
    generated_at: datetime,
) -> MarketResearchCryptoStablecoinRedemptionQueueDigestRow:
    if snapshot.observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    snapshot_age_seconds = _age_seconds(generated_at, snapshot.observed_at)
    queue_ratio = _ratio(snapshot.redemption_queue_usd, snapshot.circulating_supply_usd)
    queue_growth_ratio = _queue_growth_ratio(
        snapshot.redemption_queue_usd,
        snapshot.previous_redemption_queue_usd,
    )
    reason_codes = _row_reason_codes(
        snapshot=snapshot,
        config=config,
        snapshot_age_seconds=snapshot_age_seconds,
        queue_ratio=queue_ratio,
        queue_growth_ratio=queue_growth_ratio,
    )
    return MarketResearchCryptoStablecoinRedemptionQueueDigestRow(
        condition_id=snapshot.condition_id,
        redemption_queue_key=snapshot.redemption_queue_key,
        stablecoin_symbol=snapshot.stablecoin_symbol,
        digest_status=_row_status(reason_codes),
        observed_at=snapshot.observed_at,
        snapshot_age_seconds=snapshot_age_seconds,
        redemption_queue_usd=snapshot.redemption_queue_usd,
        previous_redemption_queue_usd=snapshot.previous_redemption_queue_usd,
        circulating_supply_usd=snapshot.circulating_supply_usd,
        queue_ratio=queue_ratio,
        queue_growth_ratio=queue_growth_ratio,
        reserve_coverage_ratio=snapshot.reserve_coverage_ratio,
        estimated_wait_hours=snapshot.estimated_wait_hours,
        source_count=snapshot.source_count,
        confidence=snapshot.confidence,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    snapshot: MarketResearchCryptoStablecoinRedemptionQueueSnapshot,
    config: MarketResearchCryptoStablecoinRedemptionQueueDigestConfig,
    snapshot_age_seconds: Decimal,
    queue_ratio: Decimal,
    queue_growth_ratio: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if snapshot.redemption_queue_usd > config.max_redemption_queue_usd:
        reasons.append(QUEUE_SIZE_REASON)
    if queue_ratio > config.max_queue_ratio:
        reasons.append(QUEUE_RATIO_REASON)
    if queue_growth_ratio > config.max_queue_growth_ratio:
        reasons.append(QUEUE_GROWTH_REASON)
    if snapshot.estimated_wait_hours > config.max_estimated_wait_hours:
        reasons.append(WAIT_TIME_REASON)
    if snapshot.reserve_coverage_ratio < config.min_reserve_coverage_ratio:
        reasons.append(RESERVE_GAP_REASON)
    if snapshot.source_count < config.min_source_count:
        reasons.append(SOURCE_DIVERSITY_GAP_REASON)
    if snapshot_age_seconds > config.max_snapshot_age_seconds:
        reasons.append(STALE_SNAPSHOT_REASON)
    if snapshot.confidence < config.min_confidence:
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
            QUEUE_SIZE_REASON,
            QUEUE_RATIO_REASON,
            QUEUE_GROWTH_REASON,
            WAIT_TIME_REASON,
            RESERVE_GAP_REASON,
            STALE_SNAPSHOT_REASON,
            CONFIDENCE_GAP_REASON,
        )
    ):
        return STATUS_BLOCKED
    return STATUS_WATCH


def _row_sort_value(
    row: MarketResearchCryptoStablecoinRedemptionQueueDigestRow,
) -> tuple[int, Decimal]:
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
    rows: tuple[MarketResearchCryptoStablecoinRedemptionQueueDigestRow, ...],
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
        return "block_report_only_market_research_crypto_stablecoin_redemption_queue_digest"
    if status == STATUS_WATCH:
        return "review_report_only_market_research_crypto_stablecoin_redemption_queue_digest"
    return "allow_report_only_market_research_crypto_stablecoin_redemption_queue_digest"


def _status_count(
    rows: tuple[MarketResearchCryptoStablecoinRedemptionQueueDigestRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.digest_status == status))


def _reason_snapshot_count(
    rows: tuple[MarketResearchCryptoStablecoinRedemptionQueueDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _reason_code_counts(
    rows: tuple[MarketResearchCryptoStablecoinRedemptionQueueDigestRow, ...],
) -> tuple[MarketResearchCryptoStablecoinRedemptionQueueDigestReasonCodeCount, ...]:
    snapshot_count = _decimal_count(len(rows))
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        MarketResearchCryptoStablecoinRedemptionQueueDigestReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
            snapshot_ratio=_ratio(_decimal_count(counts[reason_code]), snapshot_count),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _summary_reason_codes(
    rows: tuple[MarketResearchCryptoStablecoinRedemptionQueueDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    seen: set[str] = set()
    for row in rows:
        seen.update(row.reason_codes)
    if len(seen) > 1 and READY_REASON in seen:
        seen.remove(READY_REASON)
    return tuple(reason for reason in REASON_CODE_SEQUENCE if reason in seen)


def _validate_row(row: MarketResearchCryptoStablecoinRedemptionQueueDigestRow) -> None:
    if row.queue_ratio != _ratio(row.redemption_queue_usd, row.circulating_supply_usd):
        raise ValueError("queue_ratio does not match queue inputs")
    if row.queue_growth_ratio != _queue_growth_ratio(
        row.redemption_queue_usd,
        row.previous_redemption_queue_usd,
    ):
        raise ValueError("queue_growth_ratio does not match queue inputs")
    if row.digest_status != _row_status(row.reason_codes):
        raise ValueError("digest_status does not match reason_codes")


def _validate_report(
    report: MarketResearchCryptoStablecoinRedemptionQueueDigestReport,
) -> None:
    if report.snapshot_count != _decimal_count(len(report.rows)):
        raise ValueError("snapshot_count does not match rows")
    if report.ready_snapshot_count != _status_count(report.rows, STATUS_READY):
        raise ValueError("ready_snapshot_count does not match rows")
    if report.watch_snapshot_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_snapshot_count does not match rows")
    if report.blocked_snapshot_count != _status_count(report.rows, STATUS_BLOCKED):
        raise ValueError("blocked_snapshot_count does not match rows")
    expected_counts = (
        (QUEUE_SIZE_REASON, report.queue_size_snapshot_count),
        (QUEUE_RATIO_REASON, report.queue_ratio_snapshot_count),
        (QUEUE_GROWTH_REASON, report.queue_growth_snapshot_count),
        (WAIT_TIME_REASON, report.wait_time_snapshot_count),
        (RESERVE_GAP_REASON, report.reserve_gap_snapshot_count),
        (SOURCE_DIVERSITY_GAP_REASON, report.source_diversity_gap_snapshot_count),
        (STALE_SNAPSHOT_REASON, report.stale_snapshot_count),
        (CONFIDENCE_GAP_REASON, report.confidence_gap_snapshot_count),
    )
    for reason_code, count in expected_counts:
        if count != _reason_snapshot_count(report.rows, reason_code):
            raise ValueError("reason snapshot count does not match rows")
    if report.digest_status != _report_status(report.rows):
        raise ValueError("digest_status does not match rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step does not match digest_status")
    if report.average_queue_ratio != _ratio(
        _decimal_sum(row.queue_ratio for row in report.rows),
        report.snapshot_count,
    ):
        raise ValueError("average_queue_ratio does not match rows")
    if report.average_queue_growth_ratio != _ratio(
        _decimal_sum(row.queue_growth_ratio for row in report.rows),
        report.snapshot_count,
    ):
        raise ValueError("average_queue_growth_ratio does not match rows")
    if report.average_estimated_wait_hours != _ratio(
        _decimal_sum(row.estimated_wait_hours for row in report.rows),
        report.snapshot_count,
    ):
        raise ValueError("average_estimated_wait_hours does not match rows")
    if report.max_snapshot_age_seconds != max(
        (row.snapshot_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_snapshot_age_seconds does not match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts do not match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes do not match rows")


def _normalize_snapshots(
    snapshots: Iterable[MarketResearchCryptoStablecoinRedemptionQueueSnapshot],
) -> tuple[MarketResearchCryptoStablecoinRedemptionQueueSnapshot, ...]:
    snapshot_tuple = tuple(snapshots)
    seen_keys: set[str] = set()
    for snapshot in snapshot_tuple:
        if type(snapshot) is not MarketResearchCryptoStablecoinRedemptionQueueSnapshot:
            raise ValueError(
                "snapshots must contain "
                "MarketResearchCryptoStablecoinRedemptionQueueSnapshot",
            )
        if snapshot.redemption_queue_key in seen_keys:
            raise ValueError("redemption_queue_key values must be unique")
        seen_keys.add(snapshot.redemption_queue_key)
        _require_hard_flags("snapshot", snapshot)
    return snapshot_tuple


def _normalize_rows(
    rows: tuple[MarketResearchCryptoStablecoinRedemptionQueueDigestRow, ...],
) -> tuple[MarketResearchCryptoStablecoinRedemptionQueueDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not MarketResearchCryptoStablecoinRedemptionQueueDigestRow:
            raise ValueError(
                "rows must contain MarketResearchCryptoStablecoinRedemptionQueueDigestRow",
            )
        _require_hard_flags("row", row)
    return rows


def _normalize_reason_code_counts(
    items: tuple[
        MarketResearchCryptoStablecoinRedemptionQueueDigestReasonCodeCount,
        ...,
    ],
) -> tuple[MarketResearchCryptoStablecoinRedemptionQueueDigestReasonCodeCount, ...]:
    if type(items) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for item in items:
        if type(item) is not MarketResearchCryptoStablecoinRedemptionQueueDigestReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count rows")
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
        redemption_queue_key, source_config_version = item
        _require_public_string("redemption_queue_key", redemption_queue_key)
        _require_public_string("source_config_version", source_config_version)
        if redemption_queue_key in seen_keys:
            raise ValueError(
                "source_config_versions redemption_queue_key values must be unique",
            )
        seen_keys.add(redemption_queue_key)
        pairs.append((redemption_queue_key, source_config_version))
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
    if type(value) is not str or value not in REDEMPTION_QUEUE_DIGEST_STATUSES:
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


def _queue_growth_ratio(
    redemption_queue_usd: Decimal,
    previous_redemption_queue_usd: Decimal,
) -> Decimal:
    if previous_redemption_queue_usd == ZERO:
        return ZERO
    growth = (redemption_queue_usd - previous_redemption_queue_usd) / (
        previous_redemption_queue_usd
    )
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
