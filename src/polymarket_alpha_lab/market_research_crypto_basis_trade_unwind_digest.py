"""Pure Phase 1 crypto basis trade unwind market research reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from types import MappingProxyType
from typing import Any


DEFAULT_MARKET_RESEARCH_CRYPTO_BASIS_TRADE_UNWIND_DIGEST_CONFIG_VERSION = (
    "market-research-crypto-basis-trade-unwind-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

REASON_PREFIX = "market_research_crypto_basis_trade_unwind_digest_"
READY_REASON = REASON_PREFIX + "ready"
NO_INPUTS_REASON = REASON_PREFIX + "no_inputs"
BASIS_COMPRESSION_REASON = REASON_PREFIX + "basis_compression"
FUNDING_COMPRESSION_REASON = REASON_PREFIX + "funding_compression"
OPEN_INTEREST_DROP_REASON = REASON_PREFIX + "open_interest_drop"
SPOT_DEPTH_DROP_REASON = REASON_PREFIX + "spot_depth_drop"
LIQUIDATION_PRESSURE_REASON = REASON_PREFIX + "liquidation_pressure"
UNWIND_RATIO_PRESSURE_REASON = REASON_PREFIX + "unwind_ratio_pressure"
SOURCE_DIVERSITY_GAP_REASON = REASON_PREFIX + "source_diversity_gap"
STALE_SNAPSHOT_REASON = REASON_PREFIX + "stale_snapshot"
CONFIDENCE_GAP_REASON = REASON_PREFIX + "confidence_gap"

REASON_CODE_SEQUENCE = (
    BASIS_COMPRESSION_REASON,
    FUNDING_COMPRESSION_REASON,
    OPEN_INTEREST_DROP_REASON,
    SPOT_DEPTH_DROP_REASON,
    LIQUIDATION_PRESSURE_REASON,
    UNWIND_RATIO_PRESSURE_REASON,
    SOURCE_DIVERSITY_GAP_REASON,
    STALE_SNAPSHOT_REASON,
    CONFIDENCE_GAP_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    BASIS_COMPRESSION_REASON,
    FUNDING_COMPRESSION_REASON,
    OPEN_INTEREST_DROP_REASON,
    SPOT_DEPTH_DROP_REASON,
    LIQUIDATION_PRESSURE_REASON,
    UNWIND_RATIO_PRESSURE_REASON,
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
        _join_parts("wal", "let"),
        _join_parts("or", "der"),
        _join_parts("can", "cel"),
        _join_parts("re", "place"),
        _join_parts("ex", "change"),
        _join_parts("api", "_", "key"),
        _join_parts("access", "_", "key"),
        _join_parts("sec", "ret", "_", "key"),
        _join_parts("bro", "ker"),
        _join_parts("sign", "ing"),
        _join_parts("acc", "ount"),
        _join_parts("to", "ken"),
        _join_parts("sec", "ret"),
        _join_parts("pri", "vate"),
        _join_parts("au", "th"),
        _join_parts("0", "x"),
    ),
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_CRYPTO_BASIS_TRADE_UNWIND_DIGEST_CONFIG_VERSION",
    "MarketResearchCryptoBasisTradeUnwindDigestConfig",
    "MarketResearchCryptoBasisTradeUnwindSnapshot",
    "MarketResearchCryptoBasisTradeUnwindDigestRow",
    "MarketResearchCryptoBasisTradeUnwindDigestReasonCodeCount",
    "MarketResearchCryptoBasisTradeUnwindDigestReport",
    "build_market_research_crypto_basis_trade_unwind_digest",
    "market_research_crypto_basis_trade_unwind_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchCryptoBasisTradeUnwindDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_CRYPTO_BASIS_TRADE_UNWIND_DIGEST_CONFIG_VERSION
    )
    max_snapshot_age_seconds: Decimal = Decimal("1800.000000")
    watch_basis_compression_abs: Decimal = Decimal("0.010000")
    blocked_basis_compression_abs: Decimal = Decimal("0.030000")
    watch_funding_compression_abs: Decimal = Decimal("0.003000")
    blocked_funding_compression_abs: Decimal = Decimal("0.008000")
    watch_open_interest_drop_ratio: Decimal = Decimal("0.100000")
    blocked_open_interest_drop_ratio: Decimal = Decimal("0.300000")
    watch_spot_depth_drop_ratio: Decimal = Decimal("0.150000")
    blocked_spot_depth_drop_ratio: Decimal = Decimal("0.400000")
    watch_liquidation_usd: Decimal = Decimal("500000.000000")
    blocked_liquidation_usd: Decimal = Decimal("1500000.000000")
    watch_unwind_ratio: Decimal = Decimal("0.100000")
    blocked_unwind_ratio: Decimal = Decimal("0.350000")
    min_venue_source_count: Decimal = Decimal("3.000000")
    min_confidence: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoBasisTradeUnwindDigestConfig:
            raise TypeError(
                "MarketResearchCryptoBasisTradeUnwindDigestConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoBasisTradeUnwindDigestConfig:
            raise ValueError(
                "config must be exactly MarketResearchCryptoBasisTradeUnwindDigestConfig",
            )
        _require_config_version(self.config_version)
        for field_name in ("max_snapshot_age_seconds", "min_venue_source_count"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_basis_compression_abs",
            "blocked_basis_compression_abs",
            "watch_funding_compression_abs",
            "blocked_funding_compression_abs",
            "watch_open_interest_drop_ratio",
            "blocked_open_interest_drop_ratio",
            "watch_spot_depth_drop_ratio",
            "blocked_spot_depth_drop_ratio",
            "watch_unwind_ratio",
            "blocked_unwind_ratio",
            "min_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("watch_liquidation_usd", "blocked_liquidation_usd"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        _require_ordered_thresholds(
            "basis_compression_abs",
            self.watch_basis_compression_abs,
            self.blocked_basis_compression_abs,
        )
        _require_ordered_thresholds(
            "funding_compression_abs",
            self.watch_funding_compression_abs,
            self.blocked_funding_compression_abs,
        )
        _require_ordered_thresholds(
            "open_interest_drop_ratio",
            self.watch_open_interest_drop_ratio,
            self.blocked_open_interest_drop_ratio,
        )
        _require_ordered_thresholds(
            "spot_depth_drop_ratio",
            self.watch_spot_depth_drop_ratio,
            self.blocked_spot_depth_drop_ratio,
        )
        _require_ordered_thresholds(
            "liquidation_usd",
            self.watch_liquidation_usd,
            self.blocked_liquidation_usd,
        )
        _require_ordered_thresholds(
            "unwind_ratio",
            self.watch_unwind_ratio,
            self.blocked_unwind_ratio,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchCryptoBasisTradeUnwindSnapshot:
    condition_id: str
    unwind_key: str
    asset_symbol: str
    observed_at: datetime
    venue_source_count: Decimal
    current_basis: Decimal
    previous_basis: Decimal
    current_funding_rate: Decimal
    previous_funding_rate: Decimal
    open_interest_usd: Decimal
    previous_open_interest_usd: Decimal
    spot_depth_usd: Decimal
    previous_spot_depth_usd: Decimal
    liquidation_usd: Decimal
    unwind_ratio: Decimal
    confidence: Decimal
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoBasisTradeUnwindSnapshot:
            raise TypeError(
                "MarketResearchCryptoBasisTradeUnwindSnapshot does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoBasisTradeUnwindSnapshot:
            raise ValueError(
                "snapshot must be exactly MarketResearchCryptoBasisTradeUnwindSnapshot",
            )
        for field_name in (
            "condition_id",
            "unwind_key",
            "asset_symbol",
            "source_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "venue_source_count",
            "open_interest_usd",
            "previous_open_interest_usd",
            "spot_depth_usd",
            "previous_spot_depth_usd",
            "liquidation_usd",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "current_basis",
            "previous_basis",
            "current_funding_rate",
            "previous_funding_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_signed_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("unwind_ratio", "confidence"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("snapshot", self)


@dataclass(frozen=True)
class MarketResearchCryptoBasisTradeUnwindDigestRow:
    condition_id: str
    unwind_key: str
    asset_symbol: str
    digest_status: str
    observed_at: datetime
    snapshot_age_seconds: Decimal
    venue_source_count: Decimal
    current_basis: Decimal
    previous_basis: Decimal
    basis_compression_abs: Decimal
    current_funding_rate: Decimal
    previous_funding_rate: Decimal
    funding_compression_abs: Decimal
    open_interest_usd: Decimal
    previous_open_interest_usd: Decimal
    open_interest_drop_ratio: Decimal
    spot_depth_usd: Decimal
    previous_spot_depth_usd: Decimal
    spot_depth_drop_ratio: Decimal
    liquidation_usd: Decimal
    unwind_ratio: Decimal
    confidence: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoBasisTradeUnwindDigestRow:
            raise TypeError(
                "MarketResearchCryptoBasisTradeUnwindDigestRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoBasisTradeUnwindDigestRow:
            raise ValueError(
                "row must be exactly MarketResearchCryptoBasisTradeUnwindDigestRow",
            )
        for field_name in ("condition_id", "unwind_key", "asset_symbol"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_status("digest_status", self.digest_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "snapshot_age_seconds",
            "venue_source_count",
            "open_interest_usd",
            "previous_open_interest_usd",
            "spot_depth_usd",
            "previous_spot_depth_usd",
            "liquidation_usd",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "current_basis",
            "previous_basis",
            "current_funding_rate",
            "previous_funding_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_signed_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "basis_compression_abs",
            "funding_compression_abs",
            "open_interest_drop_ratio",
            "spot_depth_drop_ratio",
            "unwind_ratio",
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
class MarketResearchCryptoBasisTradeUnwindDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    snapshot_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoBasisTradeUnwindDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchCryptoBasisTradeUnwindDigestReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoBasisTradeUnwindDigestReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "MarketResearchCryptoBasisTradeUnwindDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "snapshot_ratio",
            _require_ratio_decimal("snapshot_ratio", self.snapshot_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchCryptoBasisTradeUnwindDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    snapshot_count: Decimal
    ready_snapshot_count: Decimal
    watch_snapshot_count: Decimal
    blocked_snapshot_count: Decimal
    basis_compression_snapshot_count: Decimal
    funding_compression_snapshot_count: Decimal
    open_interest_drop_snapshot_count: Decimal
    spot_depth_drop_snapshot_count: Decimal
    liquidation_pressure_snapshot_count: Decimal
    unwind_ratio_pressure_snapshot_count: Decimal
    source_diversity_gap_snapshot_count: Decimal
    stale_snapshot_count: Decimal
    confidence_gap_snapshot_count: Decimal
    average_basis_compression_abs: Decimal
    average_funding_compression_abs: Decimal
    average_open_interest_drop_ratio: Decimal
    average_spot_depth_drop_ratio: Decimal
    total_liquidation_usd: Decimal
    average_unwind_ratio: Decimal
    average_confidence: Decimal
    max_snapshot_age_seconds: Decimal
    max_allowed_snapshot_age_seconds: Decimal
    watch_basis_compression_abs: Decimal
    blocked_basis_compression_abs: Decimal
    watch_funding_compression_abs: Decimal
    blocked_funding_compression_abs: Decimal
    watch_open_interest_drop_ratio: Decimal
    blocked_open_interest_drop_ratio: Decimal
    watch_spot_depth_drop_ratio: Decimal
    blocked_spot_depth_drop_ratio: Decimal
    watch_liquidation_usd: Decimal
    blocked_liquidation_usd: Decimal
    watch_unwind_ratio: Decimal
    blocked_unwind_ratio: Decimal
    min_venue_source_count: Decimal
    min_confidence: Decimal
    rows: tuple[MarketResearchCryptoBasisTradeUnwindDigestRow, ...]
    source_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchCryptoBasisTradeUnwindDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoBasisTradeUnwindDigestReport:
            raise TypeError(
                "MarketResearchCryptoBasisTradeUnwindDigestReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoBasisTradeUnwindDigestReport:
            raise ValueError(
                "report must be exactly MarketResearchCryptoBasisTradeUnwindDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_config_version(self.config_version)
        _require_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "snapshot_count",
            "ready_snapshot_count",
            "watch_snapshot_count",
            "blocked_snapshot_count",
            "basis_compression_snapshot_count",
            "funding_compression_snapshot_count",
            "open_interest_drop_snapshot_count",
            "spot_depth_drop_snapshot_count",
            "liquidation_pressure_snapshot_count",
            "unwind_ratio_pressure_snapshot_count",
            "source_diversity_gap_snapshot_count",
            "stale_snapshot_count",
            "confidence_gap_snapshot_count",
            "total_liquidation_usd",
            "max_snapshot_age_seconds",
            "max_allowed_snapshot_age_seconds",
            "watch_liquidation_usd",
            "blocked_liquidation_usd",
            "min_venue_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_basis_compression_abs",
            "average_funding_compression_abs",
            "average_open_interest_drop_ratio",
            "average_spot_depth_drop_ratio",
            "average_unwind_ratio",
            "average_confidence",
            "watch_basis_compression_abs",
            "blocked_basis_compression_abs",
            "watch_funding_compression_abs",
            "blocked_funding_compression_abs",
            "watch_open_interest_drop_ratio",
            "blocked_open_interest_drop_ratio",
            "watch_spot_depth_drop_ratio",
            "blocked_spot_depth_drop_ratio",
            "watch_unwind_ratio",
            "blocked_unwind_ratio",
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


PUBLIC_PAYLOAD_DATACLASS_TYPES = (
    MarketResearchCryptoBasisTradeUnwindDigestConfig,
    MarketResearchCryptoBasisTradeUnwindSnapshot,
    MarketResearchCryptoBasisTradeUnwindDigestRow,
    MarketResearchCryptoBasisTradeUnwindDigestReasonCodeCount,
    MarketResearchCryptoBasisTradeUnwindDigestReport,
)


def build_market_research_crypto_basis_trade_unwind_digest(
    snapshots: Iterable[MarketResearchCryptoBasisTradeUnwindSnapshot],
    *,
    config: MarketResearchCryptoBasisTradeUnwindDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchCryptoBasisTradeUnwindDigestReport:
    cfg = config or MarketResearchCryptoBasisTradeUnwindDigestConfig()
    if type(cfg) is not MarketResearchCryptoBasisTradeUnwindDigestConfig:
        raise ValueError(
            "config must be exactly MarketResearchCryptoBasisTradeUnwindDigestConfig",
        )
    _require_hard_flags("config", cfg)
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
                row.unwind_key,
                row.condition_id,
            ),
        ),
    )
    report_status = _report_status(sorted_rows)
    snapshot_count = _decimal_count(len(sorted_rows))
    return MarketResearchCryptoBasisTradeUnwindDigestReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        digest_status=report_status,
        recommended_next_step=_recommended_next_step(report_status),
        snapshot_count=snapshot_count,
        ready_snapshot_count=_status_count(sorted_rows, STATUS_READY),
        watch_snapshot_count=_status_count(sorted_rows, STATUS_WATCH),
        blocked_snapshot_count=_status_count(sorted_rows, STATUS_BLOCKED),
        basis_compression_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            BASIS_COMPRESSION_REASON,
        ),
        funding_compression_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            FUNDING_COMPRESSION_REASON,
        ),
        open_interest_drop_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            OPEN_INTEREST_DROP_REASON,
        ),
        spot_depth_drop_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            SPOT_DEPTH_DROP_REASON,
        ),
        liquidation_pressure_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            LIQUIDATION_PRESSURE_REASON,
        ),
        unwind_ratio_pressure_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            UNWIND_RATIO_PRESSURE_REASON,
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
        average_basis_compression_abs=_ratio(
            _decimal_sum(row.basis_compression_abs for row in sorted_rows),
            snapshot_count,
        ),
        average_funding_compression_abs=_ratio(
            _decimal_sum(row.funding_compression_abs for row in sorted_rows),
            snapshot_count,
        ),
        average_open_interest_drop_ratio=_ratio(
            _decimal_sum(row.open_interest_drop_ratio for row in sorted_rows),
            snapshot_count,
        ),
        average_spot_depth_drop_ratio=_ratio(
            _decimal_sum(row.spot_depth_drop_ratio for row in sorted_rows),
            snapshot_count,
        ),
        total_liquidation_usd=_decimal_sum(row.liquidation_usd for row in sorted_rows),
        average_unwind_ratio=_ratio(
            _decimal_sum(row.unwind_ratio for row in sorted_rows),
            snapshot_count,
        ),
        average_confidence=_ratio(
            _decimal_sum(row.confidence for row in sorted_rows),
            snapshot_count,
        ),
        max_snapshot_age_seconds=max(
            (row.snapshot_age_seconds for row in sorted_rows),
            default=ZERO,
        ),
        max_allowed_snapshot_age_seconds=cfg.max_snapshot_age_seconds,
        watch_basis_compression_abs=cfg.watch_basis_compression_abs,
        blocked_basis_compression_abs=cfg.blocked_basis_compression_abs,
        watch_funding_compression_abs=cfg.watch_funding_compression_abs,
        blocked_funding_compression_abs=cfg.blocked_funding_compression_abs,
        watch_open_interest_drop_ratio=cfg.watch_open_interest_drop_ratio,
        blocked_open_interest_drop_ratio=cfg.blocked_open_interest_drop_ratio,
        watch_spot_depth_drop_ratio=cfg.watch_spot_depth_drop_ratio,
        blocked_spot_depth_drop_ratio=cfg.blocked_spot_depth_drop_ratio,
        watch_liquidation_usd=cfg.watch_liquidation_usd,
        blocked_liquidation_usd=cfg.blocked_liquidation_usd,
        watch_unwind_ratio=cfg.watch_unwind_ratio,
        blocked_unwind_ratio=cfg.blocked_unwind_ratio,
        min_venue_source_count=cfg.min_venue_source_count,
        min_confidence=cfg.min_confidence,
        rows=sorted_rows,
        source_config_versions=tuple(
            sorted(
                (snapshot.unwind_key, snapshot.source_config_version)
                for snapshot in normalized_snapshots
            ),
        ),
        reason_code_counts=_reason_code_counts(sorted_rows),
        reason_codes=_summary_reason_codes(sorted_rows),
    )


def market_research_crypto_basis_trade_unwind_digest_payload(
    report: MarketResearchCryptoBasisTradeUnwindDigestReport,
) -> MappingProxyType:
    if type(report) is not MarketResearchCryptoBasisTradeUnwindDigestReport:
        raise ValueError(
            "report must be exactly MarketResearchCryptoBasisTradeUnwindDigestReport",
        )
    return _freeze(_json_ready(report))


def _row_for_snapshot(
    snapshot: MarketResearchCryptoBasisTradeUnwindSnapshot,
    *,
    config: MarketResearchCryptoBasisTradeUnwindDigestConfig,
    generated_at: datetime,
) -> MarketResearchCryptoBasisTradeUnwindDigestRow:
    if snapshot.observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    snapshot_age_seconds = _age_seconds(generated_at, snapshot.observed_at)
    basis_compression_abs = _compression_abs(snapshot.previous_basis, snapshot.current_basis)
    funding_compression_abs = _compression_abs(
        snapshot.previous_funding_rate,
        snapshot.current_funding_rate,
    )
    open_interest_drop_ratio = _drop_ratio(
        snapshot.open_interest_usd,
        snapshot.previous_open_interest_usd,
    )
    spot_depth_drop_ratio = _drop_ratio(
        snapshot.spot_depth_usd,
        snapshot.previous_spot_depth_usd,
    )
    reason_codes = _row_reason_codes(
        snapshot=snapshot,
        config=config,
        snapshot_age_seconds=snapshot_age_seconds,
        basis_compression_abs=basis_compression_abs,
        funding_compression_abs=funding_compression_abs,
        open_interest_drop_ratio=open_interest_drop_ratio,
        spot_depth_drop_ratio=spot_depth_drop_ratio,
    )
    return MarketResearchCryptoBasisTradeUnwindDigestRow(
        condition_id=snapshot.condition_id,
        unwind_key=snapshot.unwind_key,
        asset_symbol=snapshot.asset_symbol,
        digest_status=_row_status(
            reason_codes,
            config=config,
            basis_compression_abs=basis_compression_abs,
            funding_compression_abs=funding_compression_abs,
            open_interest_drop_ratio=open_interest_drop_ratio,
            spot_depth_drop_ratio=spot_depth_drop_ratio,
            liquidation_usd=snapshot.liquidation_usd,
            unwind_ratio=snapshot.unwind_ratio,
            snapshot_age_seconds=snapshot_age_seconds,
            confidence=snapshot.confidence,
        ),
        observed_at=snapshot.observed_at,
        snapshot_age_seconds=snapshot_age_seconds,
        venue_source_count=snapshot.venue_source_count,
        current_basis=snapshot.current_basis,
        previous_basis=snapshot.previous_basis,
        basis_compression_abs=basis_compression_abs,
        current_funding_rate=snapshot.current_funding_rate,
        previous_funding_rate=snapshot.previous_funding_rate,
        funding_compression_abs=funding_compression_abs,
        open_interest_usd=snapshot.open_interest_usd,
        previous_open_interest_usd=snapshot.previous_open_interest_usd,
        open_interest_drop_ratio=open_interest_drop_ratio,
        spot_depth_usd=snapshot.spot_depth_usd,
        previous_spot_depth_usd=snapshot.previous_spot_depth_usd,
        spot_depth_drop_ratio=spot_depth_drop_ratio,
        liquidation_usd=snapshot.liquidation_usd,
        unwind_ratio=snapshot.unwind_ratio,
        confidence=snapshot.confidence,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    snapshot: MarketResearchCryptoBasisTradeUnwindSnapshot,
    config: MarketResearchCryptoBasisTradeUnwindDigestConfig,
    snapshot_age_seconds: Decimal,
    basis_compression_abs: Decimal,
    funding_compression_abs: Decimal,
    open_interest_drop_ratio: Decimal,
    spot_depth_drop_ratio: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if basis_compression_abs >= config.watch_basis_compression_abs:
        reasons.append(BASIS_COMPRESSION_REASON)
    if funding_compression_abs >= config.watch_funding_compression_abs:
        reasons.append(FUNDING_COMPRESSION_REASON)
    if open_interest_drop_ratio >= config.watch_open_interest_drop_ratio:
        reasons.append(OPEN_INTEREST_DROP_REASON)
    if spot_depth_drop_ratio >= config.watch_spot_depth_drop_ratio:
        reasons.append(SPOT_DEPTH_DROP_REASON)
    if snapshot.liquidation_usd >= config.watch_liquidation_usd:
        reasons.append(LIQUIDATION_PRESSURE_REASON)
    if snapshot.unwind_ratio >= config.watch_unwind_ratio:
        reasons.append(UNWIND_RATIO_PRESSURE_REASON)
    if snapshot.venue_source_count < config.min_venue_source_count:
        reasons.append(SOURCE_DIVERSITY_GAP_REASON)
    if snapshot_age_seconds > config.max_snapshot_age_seconds:
        reasons.append(STALE_SNAPSHOT_REASON)
    if snapshot.confidence < config.min_confidence:
        reasons.append(CONFIDENCE_GAP_REASON)
    if not reasons:
        reasons.append(READY_REASON)
    return tuple(reason for reason in ROW_REASON_CODE_SEQUENCE if reason in reasons)


def _row_status(
    reason_codes: tuple[str, ...],
    *,
    config: MarketResearchCryptoBasisTradeUnwindDigestConfig,
    basis_compression_abs: Decimal,
    funding_compression_abs: Decimal,
    open_interest_drop_ratio: Decimal,
    spot_depth_drop_ratio: Decimal,
    liquidation_usd: Decimal,
    unwind_ratio: Decimal,
    snapshot_age_seconds: Decimal,
    confidence: Decimal,
) -> str:
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    if (
        basis_compression_abs >= config.blocked_basis_compression_abs
        or funding_compression_abs >= config.blocked_funding_compression_abs
        or open_interest_drop_ratio >= config.blocked_open_interest_drop_ratio
        or spot_depth_drop_ratio >= config.blocked_spot_depth_drop_ratio
        or liquidation_usd >= config.blocked_liquidation_usd
        or unwind_ratio >= config.blocked_unwind_ratio
        or snapshot_age_seconds > config.max_snapshot_age_seconds
        or confidence < config.min_confidence
    ):
        return STATUS_BLOCKED
    return STATUS_WATCH


def _row_sort_value(
    row: MarketResearchCryptoBasisTradeUnwindDigestRow,
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
    rows: tuple[MarketResearchCryptoBasisTradeUnwindDigestRow, ...],
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
        return "block_report_only_market_research_crypto_basis_trade_unwind_digest"
    if status == STATUS_WATCH:
        return "review_report_only_market_research_crypto_basis_trade_unwind_digest"
    return "allow_report_only_market_research_crypto_basis_trade_unwind_digest"


def _status_count(
    rows: tuple[MarketResearchCryptoBasisTradeUnwindDigestRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.digest_status == status))


def _reason_snapshot_count(
    rows: tuple[MarketResearchCryptoBasisTradeUnwindDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _reason_code_counts(
    rows: tuple[MarketResearchCryptoBasisTradeUnwindDigestRow, ...],
) -> tuple[MarketResearchCryptoBasisTradeUnwindDigestReasonCodeCount, ...]:
    if not rows:
        return (
            MarketResearchCryptoBasisTradeUnwindDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                snapshot_ratio=ZERO,
            ),
        )
    snapshot_count = _decimal_count(len(rows))
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    if len(counts) > 1 and READY_REASON in counts:
        del counts[READY_REASON]
    return tuple(
        MarketResearchCryptoBasisTradeUnwindDigestReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
            snapshot_ratio=_ratio(_decimal_count(counts[reason_code]), snapshot_count),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _summary_reason_codes(
    rows: tuple[MarketResearchCryptoBasisTradeUnwindDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    seen: set[str] = set()
    for row in rows:
        seen.update(row.reason_codes)
    if len(seen) > 1 and READY_REASON in seen:
        seen.remove(READY_REASON)
    return tuple(reason for reason in REASON_CODE_SEQUENCE if reason in seen)


def _validate_row(row: MarketResearchCryptoBasisTradeUnwindDigestRow) -> None:
    if row.basis_compression_abs != _compression_abs(row.previous_basis, row.current_basis):
        raise ValueError("basis_compression_abs does not match basis inputs")
    if row.funding_compression_abs != _compression_abs(
        row.previous_funding_rate,
        row.current_funding_rate,
    ):
        raise ValueError("funding_compression_abs does not match funding inputs")
    if row.open_interest_drop_ratio != _drop_ratio(
        row.open_interest_usd,
        row.previous_open_interest_usd,
    ):
        raise ValueError("open_interest_drop_ratio does not match inputs")
    if row.spot_depth_drop_ratio != _drop_ratio(
        row.spot_depth_usd,
        row.previous_spot_depth_usd,
    ):
        raise ValueError("spot_depth_drop_ratio does not match inputs")
    if row.digest_status == STATUS_READY and row.reason_codes != (READY_REASON,):
        raise ValueError("digest_status does not match reason_codes")
    if row.digest_status != STATUS_READY and row.reason_codes == (READY_REASON,):
        raise ValueError("digest_status does not match reason_codes")


def _validate_report(report: MarketResearchCryptoBasisTradeUnwindDigestReport) -> None:
    if report.snapshot_count != _decimal_count(len(report.rows)):
        raise ValueError("snapshot_count does not match rows")
    if report.ready_snapshot_count != _status_count(report.rows, STATUS_READY):
        raise ValueError("ready_snapshot_count does not match rows")
    if report.watch_snapshot_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_snapshot_count does not match rows")
    if report.blocked_snapshot_count != _status_count(report.rows, STATUS_BLOCKED):
        raise ValueError("blocked_snapshot_count does not match rows")
    expected_counts = (
        (BASIS_COMPRESSION_REASON, report.basis_compression_snapshot_count),
        (FUNDING_COMPRESSION_REASON, report.funding_compression_snapshot_count),
        (OPEN_INTEREST_DROP_REASON, report.open_interest_drop_snapshot_count),
        (SPOT_DEPTH_DROP_REASON, report.spot_depth_drop_snapshot_count),
        (LIQUIDATION_PRESSURE_REASON, report.liquidation_pressure_snapshot_count),
        (UNWIND_RATIO_PRESSURE_REASON, report.unwind_ratio_pressure_snapshot_count),
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
    if report.average_basis_compression_abs != _ratio(
        _decimal_sum(row.basis_compression_abs for row in report.rows),
        report.snapshot_count,
    ):
        raise ValueError("average_basis_compression_abs does not match rows")
    if report.average_funding_compression_abs != _ratio(
        _decimal_sum(row.funding_compression_abs for row in report.rows),
        report.snapshot_count,
    ):
        raise ValueError("average_funding_compression_abs does not match rows")
    if report.average_open_interest_drop_ratio != _ratio(
        _decimal_sum(row.open_interest_drop_ratio for row in report.rows),
        report.snapshot_count,
    ):
        raise ValueError("average_open_interest_drop_ratio does not match rows")
    if report.average_spot_depth_drop_ratio != _ratio(
        _decimal_sum(row.spot_depth_drop_ratio for row in report.rows),
        report.snapshot_count,
    ):
        raise ValueError("average_spot_depth_drop_ratio does not match rows")
    if report.total_liquidation_usd != _decimal_sum(
        row.liquidation_usd for row in report.rows
    ):
        raise ValueError("total_liquidation_usd does not match rows")
    if report.average_unwind_ratio != _ratio(
        _decimal_sum(row.unwind_ratio for row in report.rows),
        report.snapshot_count,
    ):
        raise ValueError("average_unwind_ratio does not match rows")
    if report.average_confidence != _ratio(
        _decimal_sum(row.confidence for row in report.rows),
        report.snapshot_count,
    ):
        raise ValueError("average_confidence does not match rows")
    if report.max_snapshot_age_seconds != max(
        (row.snapshot_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_snapshot_age_seconds does not match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts do not match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes do not match rows")
    if tuple(key for key, _ in report.source_config_versions) != tuple(
        sorted(row.unwind_key for row in report.rows),
    ):
        raise ValueError("source_config_versions do not match rows")
    if not report.rows and report.source_config_versions != ():
        raise ValueError("source_config_versions do not match rows")


def _normalize_snapshots(
    snapshots: Iterable[MarketResearchCryptoBasisTradeUnwindSnapshot],
) -> tuple[MarketResearchCryptoBasisTradeUnwindSnapshot, ...]:
    if isinstance(snapshots, (str, bytes)):
        raise ValueError(
            "snapshots must contain MarketResearchCryptoBasisTradeUnwindSnapshot",
        )
    try:
        snapshot_tuple = tuple(snapshots)
    except TypeError as exc:
        raise ValueError(
            "snapshots must contain MarketResearchCryptoBasisTradeUnwindSnapshot",
        ) from exc
    seen_keys: set[str] = set()
    for snapshot in snapshot_tuple:
        if type(snapshot) is not MarketResearchCryptoBasisTradeUnwindSnapshot:
            raise ValueError(
                "snapshots must contain MarketResearchCryptoBasisTradeUnwindSnapshot",
            )
        if snapshot.unwind_key in seen_keys:
            raise ValueError("unwind_key values must be unique")
        seen_keys.add(snapshot.unwind_key)
        _require_hard_flags("snapshot", snapshot)
    return snapshot_tuple


def _normalize_rows(
    rows: tuple[MarketResearchCryptoBasisTradeUnwindDigestRow, ...],
) -> tuple[MarketResearchCryptoBasisTradeUnwindDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not MarketResearchCryptoBasisTradeUnwindDigestRow:
            raise ValueError(
                "rows must contain MarketResearchCryptoBasisTradeUnwindDigestRow",
            )
        _require_hard_flags("row", row)
    if rows != tuple(
        sorted(
            rows,
            key=lambda row: (
                _row_sort_value(row),
                row.unwind_key,
                row.condition_id,
            ),
        ),
    ):
        raise ValueError("rows must be deterministic")
    return rows


def _normalize_reason_code_counts(
    items: tuple[MarketResearchCryptoBasisTradeUnwindDigestReasonCodeCount, ...],
) -> tuple[MarketResearchCryptoBasisTradeUnwindDigestReasonCodeCount, ...]:
    if type(items) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for item in items:
        if type(item) is not MarketResearchCryptoBasisTradeUnwindDigestReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count rows")
        _require_reason_code("reason_code", item.reason_code)
        _require_positive_whole_decimal("count", item.count)
        _require_ratio_decimal("snapshot_ratio", item.snapshot_ratio)
        _require_hard_flags("reason_code_count", item)
    if items != tuple(
        sorted(items, key=lambda item: REASON_CODE_SEQUENCE.index(item.reason_code)),
    ):
        raise ValueError("reason_code_counts must be deterministic")
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
        unwind_key, source_config_version = item
        _require_public_string("unwind_key", unwind_key)
        _require_public_string("source_config_version", source_config_version)
        if unwind_key in seen_keys:
            raise ValueError("source_config_versions unwind_key values must be unique")
        seen_keys.add(unwind_key)
        pairs.append((unwind_key, source_config_version))
    normalized = tuple(sorted(pairs))
    if normalized != value:
        raise ValueError("source_config_versions must be deterministic")
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


def _require_config_version(value: str) -> None:
    _require_canonical_string("config_version", value)
    if value != DEFAULT_MARKET_RESEARCH_CRYPTO_BASIS_TRADE_UNWIND_DIGEST_CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")


def _require_status(field_name: str, value: str) -> None:
    if type(value) is not str or value not in DIGEST_STATUSES:
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


def _require_ordered_thresholds(
    field_name: str,
    watch_value: Decimal,
    blocked_value: Decimal,
) -> None:
    if blocked_value < watch_value:
        raise ValueError(f"blocked_{field_name} must be at least watch_{field_name}")


def _require_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_positive_whole_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_positive_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole number")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


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
    if value.as_tuple().exponent != QUANT.as_tuple().exponent:
        raise ValueError(f"{field_name} must be a canonical six-decimal Decimal")
    return value


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime or value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} must have a non-None UTC offset")
    return value.astimezone(UTC)


def _require_payload_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is not UTC:
        raise ValueError(f"{field_name} must use UTC timezone")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} must have a non-None UTC offset")
    return value


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    return _quantize(
        Decimal(delta.days * 86400 + delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND),
    )


def _compression_abs(previous_value: Decimal, current_value: Decimal) -> Decimal:
    compression = abs(previous_value) - abs(current_value)
    if compression <= ZERO:
        return ZERO
    return _quantize(compression)


def _drop_ratio(current_value: Decimal, previous_value: Decimal) -> Decimal:
    if previous_value == ZERO or current_value >= previous_value:
        return ZERO
    return _ratio(previous_value - current_value, previous_value)


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


def _require_canonical_decimal_value(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError(f"{field_name} must be a finite Decimal")
    if value.as_tuple().exponent != QUANT.as_tuple().exponent:
        raise ValueError(f"{field_name} must be a canonical six-decimal Decimal")
    return value


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in PUBLIC_PAYLOAD_DATACLASS_TYPES:
            raise ValueError("payload contains unsupported dataclass value")
        _revalidate_payload_dataclass(value)
        _require_hard_flags(type(value).__name__, value)
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, MappingProxyType):
        raise ValueError("payload contains unsupported mapping value")
    if type(value) is datetime:
        return _require_payload_utc("datetime", value).isoformat()
    if type(value) is Decimal:
        return format(_require_canonical_decimal_value("Decimal", value), "f")
    if type(value) is tuple:
        return tuple(_json_ready(item) for item in value)
    if type(value) in {list, dict, set}:
        raise ValueError("payload contains unsupported collection value")
    if isinstance(value, bool) or value is None or type(value) is str:
        return value
    if type(value) in {float, int}:
        raise ValueError("payload contains a non-Decimal numeric value")
    raise ValueError("payload contains unsupported value")


def _revalidate_payload_dataclass(value: Any) -> None:
    value_type = type(value)
    if value_type is MarketResearchCryptoBasisTradeUnwindDigestConfig:
        _require_config_version(value.config_version)
        _require_positive_decimal(
            "max_snapshot_age_seconds",
            value.max_snapshot_age_seconds,
        )
        _require_positive_decimal("watch_liquidation_usd", value.watch_liquidation_usd)
        _require_positive_decimal(
            "blocked_liquidation_usd",
            value.blocked_liquidation_usd,
        )
        _require_positive_decimal(
            "min_venue_source_count",
            value.min_venue_source_count,
        )
        for field_name in (
            "watch_basis_compression_abs",
            "blocked_basis_compression_abs",
            "watch_funding_compression_abs",
            "blocked_funding_compression_abs",
            "watch_open_interest_drop_ratio",
            "blocked_open_interest_drop_ratio",
            "watch_spot_depth_drop_ratio",
            "blocked_spot_depth_drop_ratio",
            "watch_unwind_ratio",
            "blocked_unwind_ratio",
            "min_confidence",
        ):
            _require_ratio_decimal(field_name, getattr(value, field_name))
        _require_ordered_thresholds(
            "basis_compression_abs",
            value.watch_basis_compression_abs,
            value.blocked_basis_compression_abs,
        )
        _require_ordered_thresholds(
            "funding_compression_abs",
            value.watch_funding_compression_abs,
            value.blocked_funding_compression_abs,
        )
        _require_ordered_thresholds(
            "open_interest_drop_ratio",
            value.watch_open_interest_drop_ratio,
            value.blocked_open_interest_drop_ratio,
        )
        _require_ordered_thresholds(
            "spot_depth_drop_ratio",
            value.watch_spot_depth_drop_ratio,
            value.blocked_spot_depth_drop_ratio,
        )
        _require_ordered_thresholds(
            "liquidation_usd",
            value.watch_liquidation_usd,
            value.blocked_liquidation_usd,
        )
        _require_ordered_thresholds(
            "unwind_ratio",
            value.watch_unwind_ratio,
            value.blocked_unwind_ratio,
        )
        return
    if value_type is MarketResearchCryptoBasisTradeUnwindSnapshot:
        _require_payload_utc("observed_at", value.observed_at)
        return
    if value_type is MarketResearchCryptoBasisTradeUnwindDigestRow:
        _require_payload_utc("observed_at", value.observed_at)
        _normalize_reason_codes(value.reason_codes, sequence=ROW_REASON_CODE_SEQUENCE)
        return
    if value_type is MarketResearchCryptoBasisTradeUnwindDigestReasonCodeCount:
        _require_reason_code("reason_code", value.reason_code)
        _require_positive_whole_decimal("count", value.count)
        _require_ratio_decimal("snapshot_ratio", value.snapshot_ratio)
        return
    if value_type is MarketResearchCryptoBasisTradeUnwindDigestReport:
        _require_payload_utc("generated_at", value.generated_at)
        _normalize_rows(value.rows)
        _normalize_source_config_versions(value.source_config_versions)
        _normalize_reason_code_counts(value.reason_code_counts)
        _normalize_reason_codes(value.reason_codes, sequence=REASON_CODE_SEQUENCE)
        _validate_report(value)
        return


def _freeze(value: Any) -> Any:
    if type(value) is dict:
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if type(value) is tuple:
        return tuple(_freeze(item) for item in value)
    return value
