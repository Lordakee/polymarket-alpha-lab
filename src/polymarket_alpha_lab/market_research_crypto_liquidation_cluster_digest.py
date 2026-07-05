"""Pure Phase 1 crypto liquidation cluster market research reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from types import MappingProxyType
from typing import Any


DEFAULT_MARKET_RESEARCH_CRYPTO_LIQUIDATION_CLUSTER_DIGEST_CONFIG_VERSION = (
    "market-research-crypto-liquidation-cluster-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
LIQUIDATION_CLUSTER_DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

READY_REASON = "market_research_crypto_liquidation_cluster_digest_ready"
NO_INPUTS_REASON = "market_research_crypto_liquidation_cluster_digest_no_inputs"
LONG_CLUSTER_REASON = "market_research_crypto_liquidation_cluster_digest_long_cluster"
SHORT_CLUSTER_REASON = "market_research_crypto_liquidation_cluster_digest_short_cluster"
NOTIONAL_SURGE_REASON = (
    "market_research_crypto_liquidation_cluster_digest_notional_surge"
)
SOURCE_DIVERSITY_GAP_REASON = (
    "market_research_crypto_liquidation_cluster_digest_source_diversity_gap"
)
NOTIONAL_GAP_REASON = "market_research_crypto_liquidation_cluster_digest_notional_gap"
STALE_SNAPSHOT_REASON = (
    "market_research_crypto_liquidation_cluster_digest_stale_snapshot"
)
CONFIDENCE_GAP_REASON = (
    "market_research_crypto_liquidation_cluster_digest_confidence_gap"
)

REASON_CODE_SEQUENCE = (
    LONG_CLUSTER_REASON,
    SHORT_CLUSTER_REASON,
    NOTIONAL_SURGE_REASON,
    SOURCE_DIVERSITY_GAP_REASON,
    NOTIONAL_GAP_REASON,
    STALE_SNAPSHOT_REASON,
    CONFIDENCE_GAP_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    LONG_CLUSTER_REASON,
    SHORT_CLUSTER_REASON,
    NOTIONAL_SURGE_REASON,
    SOURCE_DIVERSITY_GAP_REASON,
    NOTIONAL_GAP_REASON,
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
    "DEFAULT_MARKET_RESEARCH_CRYPTO_LIQUIDATION_CLUSTER_DIGEST_CONFIG_VERSION",
    "MarketResearchCryptoLiquidationClusterDigestConfig",
    "MarketResearchCryptoLiquidationClusterDigestReasonCodeCount",
    "MarketResearchCryptoLiquidationClusterDigestReport",
    "MarketResearchCryptoLiquidationClusterDigestRow",
    "MarketResearchCryptoLiquidationClusterSnapshot",
    "build_market_research_crypto_liquidation_cluster_digest",
    "market_research_crypto_liquidation_cluster_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchCryptoLiquidationClusterDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_CRYPTO_LIQUIDATION_CLUSTER_DIGEST_CONFIG_VERSION
    )
    max_snapshot_age_seconds: Decimal = Decimal("900.000000")
    max_long_liquidation_ratio: Decimal = Decimal("0.650000")
    max_short_liquidation_ratio: Decimal = Decimal("0.650000")
    max_notional_change_ratio: Decimal = Decimal("0.750000")
    min_liquidation_notional_usd: Decimal = Decimal("10000000.000000")
    min_venue_source_count: Decimal = Decimal("3.000000")
    min_confidence: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoLiquidationClusterDigestConfig:
            raise TypeError(
                "MarketResearchCryptoLiquidationClusterDigestConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoLiquidationClusterDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchCryptoLiquidationClusterDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("max_snapshot_age_seconds", "min_venue_source_count"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_long_liquidation_ratio",
            "max_short_liquidation_ratio",
            "min_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_notional_change_ratio",
            "min_liquidation_notional_usd",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchCryptoLiquidationClusterSnapshot:
    condition_id: str
    cluster_key: str
    asset_symbol: str
    observed_at: datetime
    long_liquidation_usd: Decimal
    short_liquidation_usd: Decimal
    previous_total_liquidation_usd: Decimal
    venue_source_count: Decimal
    confidence: Decimal
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoLiquidationClusterSnapshot:
            raise TypeError(
                "MarketResearchCryptoLiquidationClusterSnapshot does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoLiquidationClusterSnapshot:
            raise ValueError(
                "snapshot must be exactly "
                "MarketResearchCryptoLiquidationClusterSnapshot",
            )
        for field_name in (
            "condition_id",
            "cluster_key",
            "asset_symbol",
            "source_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "long_liquidation_usd",
            "short_liquidation_usd",
            "previous_total_liquidation_usd",
            "venue_source_count",
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
        _require_hard_flags("snapshot", self)


@dataclass(frozen=True)
class MarketResearchCryptoLiquidationClusterDigestRow:
    condition_id: str
    cluster_key: str
    asset_symbol: str
    digest_status: str
    observed_at: datetime
    snapshot_age_seconds: Decimal
    long_liquidation_usd: Decimal
    short_liquidation_usd: Decimal
    total_liquidation_usd: Decimal
    previous_total_liquidation_usd: Decimal
    dominant_liquidation_ratio: Decimal
    notional_change_ratio: Decimal
    venue_source_count: Decimal
    confidence: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoLiquidationClusterDigestRow:
            raise TypeError(
                "MarketResearchCryptoLiquidationClusterDigestRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoLiquidationClusterDigestRow:
            raise ValueError(
                "row must be exactly MarketResearchCryptoLiquidationClusterDigestRow",
            )
        for field_name in ("condition_id", "cluster_key", "asset_symbol"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_status("digest_status", self.digest_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "snapshot_age_seconds",
            "long_liquidation_usd",
            "short_liquidation_usd",
            "total_liquidation_usd",
            "previous_total_liquidation_usd",
            "notional_change_ratio",
            "venue_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("dominant_liquidation_ratio", "confidence"):
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
class MarketResearchCryptoLiquidationClusterDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    snapshot_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoLiquidationClusterDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchCryptoLiquidationClusterDigestReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoLiquidationClusterDigestReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "MarketResearchCryptoLiquidationClusterDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "snapshot_ratio",
            _require_ratio_decimal("snapshot_ratio", self.snapshot_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchCryptoLiquidationClusterDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    snapshot_count: Decimal
    ready_snapshot_count: Decimal
    watch_snapshot_count: Decimal
    blocked_snapshot_count: Decimal
    long_cluster_snapshot_count: Decimal
    short_cluster_snapshot_count: Decimal
    notional_surge_snapshot_count: Decimal
    source_diversity_gap_snapshot_count: Decimal
    notional_gap_snapshot_count: Decimal
    stale_snapshot_count: Decimal
    confidence_gap_snapshot_count: Decimal
    average_total_liquidation_usd: Decimal
    average_dominant_liquidation_ratio: Decimal
    average_notional_change_ratio: Decimal
    max_snapshot_age_seconds: Decimal
    max_allowed_snapshot_age_seconds: Decimal
    max_allowed_long_liquidation_ratio: Decimal
    max_allowed_short_liquidation_ratio: Decimal
    max_allowed_notional_change_ratio: Decimal
    min_liquidation_notional_usd: Decimal
    min_venue_source_count: Decimal
    min_confidence: Decimal
    rows: tuple[MarketResearchCryptoLiquidationClusterDigestRow, ...]
    source_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchCryptoLiquidationClusterDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoLiquidationClusterDigestReport:
            raise TypeError(
                "MarketResearchCryptoLiquidationClusterDigestReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoLiquidationClusterDigestReport:
            raise ValueError(
                "report must be exactly MarketResearchCryptoLiquidationClusterDigestReport",
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
            "long_cluster_snapshot_count",
            "short_cluster_snapshot_count",
            "notional_surge_snapshot_count",
            "source_diversity_gap_snapshot_count",
            "notional_gap_snapshot_count",
            "stale_snapshot_count",
            "confidence_gap_snapshot_count",
            "average_total_liquidation_usd",
            "average_notional_change_ratio",
            "max_snapshot_age_seconds",
            "max_allowed_snapshot_age_seconds",
            "max_allowed_notional_change_ratio",
            "min_liquidation_notional_usd",
            "min_venue_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_dominant_liquidation_ratio",
            "max_allowed_long_liquidation_ratio",
            "max_allowed_short_liquidation_ratio",
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


_PUBLIC_DATACLASS_TYPES = (
    MarketResearchCryptoLiquidationClusterDigestConfig,
    MarketResearchCryptoLiquidationClusterDigestReasonCodeCount,
    MarketResearchCryptoLiquidationClusterDigestReport,
    MarketResearchCryptoLiquidationClusterDigestRow,
    MarketResearchCryptoLiquidationClusterSnapshot,
)


def build_market_research_crypto_liquidation_cluster_digest(
    snapshots: Iterable[MarketResearchCryptoLiquidationClusterSnapshot],
    *,
    config: MarketResearchCryptoLiquidationClusterDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchCryptoLiquidationClusterDigestReport:
    cfg = (
        MarketResearchCryptoLiquidationClusterDigestConfig()
        if config is None
        else config
    )
    if type(cfg) is not MarketResearchCryptoLiquidationClusterDigestConfig:
        raise ValueError(
            "config must be exactly "
            "MarketResearchCryptoLiquidationClusterDigestConfig",
        )
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_snapshots = _normalize_snapshots(snapshots)
    rows = tuple(
        _row_for_snapshot(snapshot, config=cfg, generated_at=generated_at_utc)
        for snapshot in normalized_snapshots
    )
    sorted_rows = _canonical_rows(rows)
    report_status = _report_status(sorted_rows)
    return MarketResearchCryptoLiquidationClusterDigestReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        digest_status=report_status,
        recommended_next_step=_recommended_next_step(report_status),
        snapshot_count=_decimal_count(len(sorted_rows)),
        ready_snapshot_count=_status_count(sorted_rows, STATUS_READY),
        watch_snapshot_count=_status_count(sorted_rows, STATUS_WATCH),
        blocked_snapshot_count=_status_count(sorted_rows, STATUS_BLOCKED),
        long_cluster_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            LONG_CLUSTER_REASON,
        ),
        short_cluster_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            SHORT_CLUSTER_REASON,
        ),
        notional_surge_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            NOTIONAL_SURGE_REASON,
        ),
        source_diversity_gap_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            SOURCE_DIVERSITY_GAP_REASON,
        ),
        notional_gap_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            NOTIONAL_GAP_REASON,
        ),
        stale_snapshot_count=_reason_snapshot_count(sorted_rows, STALE_SNAPSHOT_REASON),
        confidence_gap_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            CONFIDENCE_GAP_REASON,
        ),
        average_total_liquidation_usd=_ratio(
            _decimal_sum(row.total_liquidation_usd for row in sorted_rows),
            _decimal_count(len(sorted_rows)),
        ),
        average_dominant_liquidation_ratio=_ratio(
            _decimal_sum(row.dominant_liquidation_ratio for row in sorted_rows),
            _decimal_count(len(sorted_rows)),
        ),
        average_notional_change_ratio=_ratio(
            _decimal_sum(row.notional_change_ratio for row in sorted_rows),
            _decimal_count(len(sorted_rows)),
        ),
        max_snapshot_age_seconds=max(
            (row.snapshot_age_seconds for row in sorted_rows),
            default=ZERO,
        ),
        max_allowed_snapshot_age_seconds=cfg.max_snapshot_age_seconds,
        max_allowed_long_liquidation_ratio=cfg.max_long_liquidation_ratio,
        max_allowed_short_liquidation_ratio=cfg.max_short_liquidation_ratio,
        max_allowed_notional_change_ratio=cfg.max_notional_change_ratio,
        min_liquidation_notional_usd=cfg.min_liquidation_notional_usd,
        min_venue_source_count=cfg.min_venue_source_count,
        min_confidence=cfg.min_confidence,
        rows=sorted_rows,
        source_config_versions=tuple(
            sorted(
                (snapshot.cluster_key, snapshot.source_config_version)
                for snapshot in normalized_snapshots
            ),
        ),
        reason_code_counts=_reason_code_counts(sorted_rows),
        reason_codes=_summary_reason_codes(sorted_rows),
    )


def market_research_crypto_liquidation_cluster_digest_payload(
    report: MarketResearchCryptoLiquidationClusterDigestReport,
) -> MappingProxyType:
    if type(report) is not MarketResearchCryptoLiquidationClusterDigestReport:
        raise ValueError(
            "report must be exactly MarketResearchCryptoLiquidationClusterDigestReport",
        )
    _require_payload_safe_value("report", report)
    return _freeze(_json_ready(report))


def _row_for_snapshot(
    snapshot: MarketResearchCryptoLiquidationClusterSnapshot,
    *,
    config: MarketResearchCryptoLiquidationClusterDigestConfig,
    generated_at: datetime,
) -> MarketResearchCryptoLiquidationClusterDigestRow:
    if snapshot.observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    snapshot_age_seconds = _age_seconds(generated_at, snapshot.observed_at)
    total_liquidation_usd = _total_liquidation_usd(
        snapshot.long_liquidation_usd,
        snapshot.short_liquidation_usd,
    )
    dominant_liquidation_ratio = _dominant_liquidation_ratio(
        snapshot.long_liquidation_usd,
        snapshot.short_liquidation_usd,
    )
    notional_change_ratio = _notional_change_ratio(
        total_liquidation_usd,
        snapshot.previous_total_liquidation_usd,
    )
    reason_codes = _row_reason_codes(
        snapshot=snapshot,
        config=config,
        snapshot_age_seconds=snapshot_age_seconds,
        total_liquidation_usd=total_liquidation_usd,
        dominant_liquidation_ratio=dominant_liquidation_ratio,
        notional_change_ratio=notional_change_ratio,
    )
    return MarketResearchCryptoLiquidationClusterDigestRow(
        condition_id=snapshot.condition_id,
        cluster_key=snapshot.cluster_key,
        asset_symbol=snapshot.asset_symbol,
        digest_status=_row_status(reason_codes),
        observed_at=snapshot.observed_at,
        snapshot_age_seconds=snapshot_age_seconds,
        long_liquidation_usd=snapshot.long_liquidation_usd,
        short_liquidation_usd=snapshot.short_liquidation_usd,
        total_liquidation_usd=total_liquidation_usd,
        previous_total_liquidation_usd=snapshot.previous_total_liquidation_usd,
        dominant_liquidation_ratio=dominant_liquidation_ratio,
        notional_change_ratio=notional_change_ratio,
        venue_source_count=snapshot.venue_source_count,
        confidence=snapshot.confidence,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    snapshot: MarketResearchCryptoLiquidationClusterSnapshot,
    config: MarketResearchCryptoLiquidationClusterDigestConfig,
    snapshot_age_seconds: Decimal,
    total_liquidation_usd: Decimal,
    dominant_liquidation_ratio: Decimal,
    notional_change_ratio: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if (
        snapshot.long_liquidation_usd >= snapshot.short_liquidation_usd
        and dominant_liquidation_ratio > config.max_long_liquidation_ratio
    ):
        reasons.append(LONG_CLUSTER_REASON)
    if (
        snapshot.short_liquidation_usd > snapshot.long_liquidation_usd
        and dominant_liquidation_ratio > config.max_short_liquidation_ratio
    ):
        reasons.append(SHORT_CLUSTER_REASON)
    if notional_change_ratio > config.max_notional_change_ratio:
        reasons.append(NOTIONAL_SURGE_REASON)
    if snapshot.venue_source_count < config.min_venue_source_count:
        reasons.append(SOURCE_DIVERSITY_GAP_REASON)
    if total_liquidation_usd < config.min_liquidation_notional_usd:
        reasons.append(NOTIONAL_GAP_REASON)
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
            LONG_CLUSTER_REASON,
            SHORT_CLUSTER_REASON,
            NOTIONAL_SURGE_REASON,
            NOTIONAL_GAP_REASON,
            STALE_SNAPSHOT_REASON,
            CONFIDENCE_GAP_REASON,
        )
    ):
        return STATUS_BLOCKED
    return STATUS_WATCH


def _row_sort_value(
    row: MarketResearchCryptoLiquidationClusterDigestRow,
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


def _canonical_rows(
    rows: tuple[MarketResearchCryptoLiquidationClusterDigestRow, ...],
) -> tuple[MarketResearchCryptoLiquidationClusterDigestRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                _row_sort_value(row),
                -row.total_liquidation_usd,
                row.cluster_key,
                row.condition_id,
            ),
        ),
    )


def _report_status(
    rows: tuple[MarketResearchCryptoLiquidationClusterDigestRow, ...],
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
        return "block_report_only_market_research_crypto_liquidation_cluster_digest"
    if status == STATUS_WATCH:
        return "review_report_only_market_research_crypto_liquidation_cluster_digest"
    return "allow_report_only_market_research_crypto_liquidation_cluster_digest"


def _status_count(
    rows: tuple[MarketResearchCryptoLiquidationClusterDigestRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.digest_status == status))


def _reason_snapshot_count(
    rows: tuple[MarketResearchCryptoLiquidationClusterDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _reason_code_counts(
    rows: tuple[MarketResearchCryptoLiquidationClusterDigestRow, ...],
) -> tuple[MarketResearchCryptoLiquidationClusterDigestReasonCodeCount, ...]:
    snapshot_count = _decimal_count(len(rows))
    if not rows:
        return (
            MarketResearchCryptoLiquidationClusterDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                snapshot_ratio=ZERO,
            ),
        )
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        MarketResearchCryptoLiquidationClusterDigestReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
            snapshot_ratio=_ratio(_decimal_count(counts[reason_code]), snapshot_count),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _summary_reason_codes(
    rows: tuple[MarketResearchCryptoLiquidationClusterDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    seen: set[str] = set()
    for row in rows:
        seen.update(row.reason_codes)
    if len(seen) > 1 and READY_REASON in seen:
        seen.remove(READY_REASON)
    return tuple(reason for reason in REASON_CODE_SEQUENCE if reason in seen)


def _validate_row(row: MarketResearchCryptoLiquidationClusterDigestRow) -> None:
    if row.total_liquidation_usd != _total_liquidation_usd(
        row.long_liquidation_usd,
        row.short_liquidation_usd,
    ):
        raise ValueError("total_liquidation_usd does not match side inputs")
    if row.dominant_liquidation_ratio != _dominant_liquidation_ratio(
        row.long_liquidation_usd,
        row.short_liquidation_usd,
    ):
        raise ValueError("dominant_liquidation_ratio does not match side inputs")
    if row.notional_change_ratio != _notional_change_ratio(
        row.total_liquidation_usd,
        row.previous_total_liquidation_usd,
    ):
        raise ValueError("notional_change_ratio does not match notional inputs")
    if row.digest_status != _row_status(row.reason_codes):
        raise ValueError("digest_status does not match reason_codes")


def _validate_report(report: MarketResearchCryptoLiquidationClusterDigestReport) -> None:
    if report.snapshot_count != _decimal_count(len(report.rows)):
        raise ValueError("snapshot_count does not match rows")
    if report.ready_snapshot_count != _status_count(report.rows, STATUS_READY):
        raise ValueError("ready_snapshot_count does not match rows")
    if report.watch_snapshot_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_snapshot_count does not match rows")
    if report.blocked_snapshot_count != _status_count(report.rows, STATUS_BLOCKED):
        raise ValueError("blocked_snapshot_count does not match rows")
    expected_counts = (
        (LONG_CLUSTER_REASON, report.long_cluster_snapshot_count),
        (SHORT_CLUSTER_REASON, report.short_cluster_snapshot_count),
        (NOTIONAL_SURGE_REASON, report.notional_surge_snapshot_count),
        (SOURCE_DIVERSITY_GAP_REASON, report.source_diversity_gap_snapshot_count),
        (NOTIONAL_GAP_REASON, report.notional_gap_snapshot_count),
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
    if report.average_total_liquidation_usd != _ratio(
        _decimal_sum(row.total_liquidation_usd for row in report.rows),
        report.snapshot_count,
    ):
        raise ValueError("average_total_liquidation_usd does not match rows")
    if report.average_dominant_liquidation_ratio != _ratio(
        _decimal_sum(row.dominant_liquidation_ratio for row in report.rows),
        report.snapshot_count,
    ):
        raise ValueError("average_dominant_liquidation_ratio does not match rows")
    if report.average_notional_change_ratio != _ratio(
        _decimal_sum(row.notional_change_ratio for row in report.rows),
        report.snapshot_count,
    ):
        raise ValueError("average_notional_change_ratio does not match rows")
    if report.max_snapshot_age_seconds != max(
        (row.snapshot_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_snapshot_age_seconds does not match rows")
    if report.rows != _canonical_rows(report.rows):
        raise ValueError("rows must be deterministic")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts do not match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes do not match rows")


def _normalize_snapshots(
    snapshots: Iterable[MarketResearchCryptoLiquidationClusterSnapshot],
) -> tuple[MarketResearchCryptoLiquidationClusterSnapshot, ...]:
    snapshot_tuple = tuple(snapshots)
    seen_keys: set[str] = set()
    for snapshot in snapshot_tuple:
        if type(snapshot) is not MarketResearchCryptoLiquidationClusterSnapshot:
            raise ValueError(
                "snapshots must contain MarketResearchCryptoLiquidationClusterSnapshot",
            )
        if snapshot.cluster_key in seen_keys:
            raise ValueError("cluster_key values must be unique")
        seen_keys.add(snapshot.cluster_key)
        _require_hard_flags("snapshot", snapshot)
    return snapshot_tuple


def _normalize_rows(
    rows: tuple[MarketResearchCryptoLiquidationClusterDigestRow, ...],
) -> tuple[MarketResearchCryptoLiquidationClusterDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not MarketResearchCryptoLiquidationClusterDigestRow:
            raise ValueError(
                "rows must contain MarketResearchCryptoLiquidationClusterDigestRow",
            )
        _require_hard_flags("row", row)
    return rows


def _normalize_reason_code_counts(
    items: tuple[MarketResearchCryptoLiquidationClusterDigestReasonCodeCount, ...],
) -> tuple[MarketResearchCryptoLiquidationClusterDigestReasonCodeCount, ...]:
    if type(items) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for item in items:
        if type(item) is not MarketResearchCryptoLiquidationClusterDigestReasonCodeCount:
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
        cluster_key, source_config_version = item
        _require_public_string("cluster_key", cluster_key)
        _require_public_string("source_config_version", source_config_version)
        if cluster_key in seen_keys:
            raise ValueError("source_config_versions cluster_key values must be unique")
        seen_keys.add(cluster_key)
        pairs.append((cluster_key, source_config_version))
    normalized = tuple(pairs)
    if normalized != tuple(sorted(normalized)):
        raise ValueError("source_config_versions must be deterministic")
    return normalized


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
    if type(value) is not str or value not in LIQUIDATION_CLUSTER_DIGEST_STATUSES:
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


def _total_liquidation_usd(long_liquidation_usd: Decimal, short_liquidation_usd: Decimal) -> Decimal:
    return _quantize(long_liquidation_usd + short_liquidation_usd)


def _dominant_liquidation_ratio(
    long_liquidation_usd: Decimal,
    short_liquidation_usd: Decimal,
) -> Decimal:
    total_liquidation_usd = _total_liquidation_usd(
        long_liquidation_usd,
        short_liquidation_usd,
    )
    return _ratio(max(long_liquidation_usd, short_liquidation_usd), total_liquidation_usd)


def _notional_change_ratio(
    total_liquidation_usd: Decimal,
    previous_total_liquidation_usd: Decimal,
) -> Decimal:
    if previous_total_liquidation_usd == ZERO:
        return ZERO
    return _quantize(
        abs(total_liquidation_usd - previous_total_liquidation_usd)
        / previous_total_liquidation_usd,
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


def _require_payload_safe_value(field_name: str, value: object) -> None:
    if type(value) is Decimal:
        decimal_value = _require_decimal(field_name, value)
        if decimal_value != value or not value.same_quantum(QUANT):
            raise ValueError(f"{field_name} must be quantized to six decimals")
        return
    if type(value) is datetime:
        _as_utc(field_name, value)
        if value.tzinfo is not UTC:
            raise ValueError(f"{field_name} must be normalized to UTC")
        return
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{field_name} must be a supported public dataclass")
        _require_hard_flags(field_name, value)
        for field in fields(value):
            _require_payload_safe_value(
                f"{field_name}.{field.name}",
                getattr(value, field.name),
            )
        _rebuild_public_dataclass(field_name, value)
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            _require_payload_safe_value(f"{field_name}[{index}]", item)
        return
    if type(value) in (str, bool) or value is None:
        return
    if type(value) in (list, dict, set):
        raise ValueError(f"{field_name} must remain constructor-normalized")
    raise ValueError(f"{field_name} must be safe for serialization")


def _rebuild_public_dataclass(field_name: str, value: object) -> None:
    type_ = type(value)
    try:
        type_(**{field.name: getattr(value, field.name) for field in fields(value)})
    except (ArithmeticError, TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must remain constructor-valid") from exc


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError("value must be a supported public dataclass")
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("value must be exactly datetime")
        return value.isoformat()
    if type(value) is Decimal:
        return f"{value:.6f}"
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
