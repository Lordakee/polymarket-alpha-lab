"""Pure Phase 1 crypto exchange reserve drain market research reducer."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from types import MappingProxyType
from typing import Any


DEFAULT_MARKET_RESEARCH_CRYPTO_EXCHANGE_RESERVE_DRAIN_DIGEST_CONFIG_VERSION = (
    "market-research-crypto-exchange-reserve-drain-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

READY_REASON = "market_research_crypto_exchange_reserve_drain_digest_ready"
NO_INPUTS_REASON = "market_research_crypto_exchange_reserve_drain_digest_no_inputs"
RESERVE_DROP_REASON = (
    "market_research_crypto_exchange_reserve_drain_digest_reserve_drop"
)
NET_OUTFLOW_REASON = (
    "market_research_crypto_exchange_reserve_drain_digest_net_outflow"
)
SOURCE_GAP_REASON = "market_research_crypto_exchange_reserve_drain_digest_source_gap"
STALE_SNAPSHOT_REASON = (
    "market_research_crypto_exchange_reserve_drain_digest_stale_snapshot"
)
CONFIDENCE_GAP_REASON = (
    "market_research_crypto_exchange_reserve_drain_digest_confidence_gap"
)

REASON_CODE_SEQUENCE = (
    RESERVE_DROP_REASON,
    NET_OUTFLOW_REASON,
    SOURCE_GAP_REASON,
    STALE_SNAPSHOT_REASON,
    CONFIDENCE_GAP_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    RESERVE_DROP_REASON,
    NET_OUTFLOW_REASON,
    SOURCE_GAP_REASON,
    STALE_SNAPSHOT_REASON,
    CONFIDENCE_GAP_REASON,
    READY_REASON,
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")

__all__ = (
    "DEFAULT_MARKET_RESEARCH_CRYPTO_EXCHANGE_RESERVE_DRAIN_DIGEST_CONFIG_VERSION",
    "MarketResearchCryptoExchangeReserveDrainDigestConfig",
    "MarketResearchCryptoExchangeReserveDrainDigestReasonCodeCount",
    "MarketResearchCryptoExchangeReserveDrainDigestReport",
    "MarketResearchCryptoExchangeReserveDrainDigestRow",
    "MarketResearchCryptoExchangeReserveDrainSnapshot",
    "build_market_research_crypto_exchange_reserve_drain_digest",
    "market_research_crypto_exchange_reserve_drain_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchCryptoExchangeReserveDrainDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_CRYPTO_EXCHANGE_RESERVE_DRAIN_DIGEST_CONFIG_VERSION
    )
    max_snapshot_age_seconds: Decimal = Decimal("1800.000000")
    max_reserve_drop_ratio: Decimal = Decimal("0.120000")
    max_net_outflow_ratio: Decimal = Decimal("0.080000")
    min_source_count: Decimal = Decimal("3.000000")
    min_confidence: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoExchangeReserveDrainDigestConfig:
            raise TypeError(
                "MarketResearchCryptoExchangeReserveDrainDigestConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoExchangeReserveDrainDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchCryptoExchangeReserveDrainDigestConfig",
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_CRYPTO_EXCHANGE_RESERVE_DRAIN_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "max_snapshot_age_seconds",
            _require_positive_decimal(
                "max_snapshot_age_seconds",
                self.max_snapshot_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "min_source_count",
            _require_positive_count_decimal("min_source_count", self.min_source_count),
        )
        for field_name in (
            "max_reserve_drop_ratio",
            "max_net_outflow_ratio",
            "min_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchCryptoExchangeReserveDrainSnapshot:
    condition_id: str
    reserve_key: str
    asset_symbol: str
    source_timestamp: datetime
    source_count: Decimal
    reserve_balance: Decimal
    previous_reserve_balance: Decimal
    net_outflow: Decimal
    confidence: Decimal
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoExchangeReserveDrainSnapshot:
            raise TypeError(
                "MarketResearchCryptoExchangeReserveDrainSnapshot does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoExchangeReserveDrainSnapshot:
            raise ValueError(
                "snapshot must be exactly MarketResearchCryptoExchangeReserveDrainSnapshot",
            )
        for field_name in (
            "condition_id",
            "reserve_key",
            "asset_symbol",
            "source_config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "source_timestamp",
            _as_utc("source_timestamp", self.source_timestamp),
        )
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_count_decimal("source_count", self.source_count),
        )
        for field_name in (
            "reserve_balance",
            "previous_reserve_balance",
            "net_outflow",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "confidence",
            _require_ratio_decimal("confidence", self.confidence),
        )
        _require_hard_flags("snapshot", self)


@dataclass(frozen=True)
class MarketResearchCryptoExchangeReserveDrainDigestRow:
    condition_id: str
    reserve_key: str
    asset_symbol: str
    digest_status: str
    source_timestamp: datetime
    snapshot_age_seconds: Decimal
    source_count: Decimal
    reserve_balance: Decimal
    previous_reserve_balance: Decimal
    reserve_drop_ratio: Decimal
    net_outflow: Decimal
    net_outflow_ratio: Decimal
    confidence: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoExchangeReserveDrainDigestRow:
            raise TypeError(
                "MarketResearchCryptoExchangeReserveDrainDigestRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoExchangeReserveDrainDigestRow:
            raise ValueError(
                "row must be exactly MarketResearchCryptoExchangeReserveDrainDigestRow",
            )
        for field_name in ("condition_id", "reserve_key", "asset_symbol"):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_status("digest_status", self.digest_status)
        object.__setattr__(
            self,
            "source_timestamp",
            _as_utc("source_timestamp", self.source_timestamp),
        )
        object.__setattr__(
            self,
            "snapshot_age_seconds",
            _require_nonnegative_decimal(
                "snapshot_age_seconds",
                self.snapshot_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_count_decimal("source_count", self.source_count),
        )
        for field_name in (
            "reserve_balance",
            "previous_reserve_balance",
            "net_outflow",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("reserve_drop_ratio", "net_outflow_ratio", "confidence"):
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
class MarketResearchCryptoExchangeReserveDrainDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    snapshot_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoExchangeReserveDrainDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchCryptoExchangeReserveDrainDigestReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoExchangeReserveDrainDigestReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "MarketResearchCryptoExchangeReserveDrainDigestReasonCodeCount",
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
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchCryptoExchangeReserveDrainDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    snapshot_count: Decimal
    ready_snapshot_count: Decimal
    watch_snapshot_count: Decimal
    blocked_snapshot_count: Decimal
    reserve_drop_snapshot_count: Decimal
    net_outflow_snapshot_count: Decimal
    source_gap_snapshot_count: Decimal
    stale_snapshot_count: Decimal
    confidence_gap_snapshot_count: Decimal
    average_reserve_drop_ratio: Decimal
    average_net_outflow_ratio: Decimal
    max_snapshot_age_seconds: Decimal
    max_allowed_snapshot_age_seconds: Decimal
    max_allowed_reserve_drop_ratio: Decimal
    max_allowed_net_outflow_ratio: Decimal
    min_source_count: Decimal
    min_confidence: Decimal
    rows: tuple[MarketResearchCryptoExchangeReserveDrainDigestRow, ...]
    source_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchCryptoExchangeReserveDrainDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoExchangeReserveDrainDigestReport:
            raise TypeError(
                "MarketResearchCryptoExchangeReserveDrainDigestReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoExchangeReserveDrainDigestReport:
            raise ValueError(
                "report must be exactly MarketResearchCryptoExchangeReserveDrainDigestReport",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_CRYPTO_EXCHANGE_RESERVE_DRAIN_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "snapshot_count",
            "ready_snapshot_count",
            "watch_snapshot_count",
            "blocked_snapshot_count",
            "reserve_drop_snapshot_count",
            "net_outflow_snapshot_count",
            "source_gap_snapshot_count",
            "stale_snapshot_count",
            "confidence_gap_snapshot_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_snapshot_age_seconds", "max_allowed_snapshot_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_reserve_drop_ratio",
            "average_net_outflow_ratio",
            "max_allowed_reserve_drop_ratio",
            "max_allowed_net_outflow_ratio",
            "min_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_source_count",
            _require_nonnegative_count_decimal("min_source_count", self.min_source_count),
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
    MarketResearchCryptoExchangeReserveDrainDigestConfig,
    MarketResearchCryptoExchangeReserveDrainSnapshot,
    MarketResearchCryptoExchangeReserveDrainDigestRow,
    MarketResearchCryptoExchangeReserveDrainDigestReasonCodeCount,
    MarketResearchCryptoExchangeReserveDrainDigestReport,
)


def build_market_research_crypto_exchange_reserve_drain_digest(
    snapshots: tuple[MarketResearchCryptoExchangeReserveDrainSnapshot, ...],
    *,
    config: MarketResearchCryptoExchangeReserveDrainDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchCryptoExchangeReserveDrainDigestReport:
    cfg = config or MarketResearchCryptoExchangeReserveDrainDigestConfig()
    if type(cfg) is not MarketResearchCryptoExchangeReserveDrainDigestConfig:
        raise ValueError(
            "config must be exactly "
            "MarketResearchCryptoExchangeReserveDrainDigestConfig",
        )
    cfg = _revalidate_config(cfg)
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
                row.reserve_key,
                row.condition_id,
            ),
        ),
    )
    reason_codes = _summary_reason_codes(sorted_rows)
    report_status = _report_status(sorted_rows)
    return MarketResearchCryptoExchangeReserveDrainDigestReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        digest_status=report_status,
        recommended_next_step=_recommended_next_step(report_status),
        snapshot_count=_decimal_count(len(sorted_rows)),
        ready_snapshot_count=_status_count(sorted_rows, STATUS_READY),
        watch_snapshot_count=_status_count(sorted_rows, STATUS_WATCH),
        blocked_snapshot_count=_status_count(sorted_rows, STATUS_BLOCKED),
        reserve_drop_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            RESERVE_DROP_REASON,
        ),
        net_outflow_snapshot_count=_reason_snapshot_count(sorted_rows, NET_OUTFLOW_REASON),
        source_gap_snapshot_count=_reason_snapshot_count(sorted_rows, SOURCE_GAP_REASON),
        stale_snapshot_count=_reason_snapshot_count(sorted_rows, STALE_SNAPSHOT_REASON),
        confidence_gap_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            CONFIDENCE_GAP_REASON,
        ),
        average_reserve_drop_ratio=_ratio(
            _decimal_sum(row.reserve_drop_ratio for row in sorted_rows),
            _decimal_count(len(sorted_rows)),
        ),
        average_net_outflow_ratio=_ratio(
            _decimal_sum(row.net_outflow_ratio for row in sorted_rows),
            _decimal_count(len(sorted_rows)),
        ),
        max_snapshot_age_seconds=max(
            (row.snapshot_age_seconds for row in sorted_rows),
            default=ZERO,
        ),
        max_allowed_snapshot_age_seconds=cfg.max_snapshot_age_seconds,
        max_allowed_reserve_drop_ratio=cfg.max_reserve_drop_ratio,
        max_allowed_net_outflow_ratio=cfg.max_net_outflow_ratio,
        min_source_count=cfg.min_source_count,
        min_confidence=cfg.min_confidence,
        rows=sorted_rows,
        source_config_versions=tuple(
            sorted(
                (snapshot.reserve_key, snapshot.source_config_version)
                for snapshot in normalized_snapshots
            ),
        ),
        reason_code_counts=_reason_code_counts(sorted_rows, reason_codes),
        reason_codes=reason_codes,
    )


def market_research_crypto_exchange_reserve_drain_digest_payload(
    report: MarketResearchCryptoExchangeReserveDrainDigestReport,
) -> MappingProxyType:
    if type(report) is not MarketResearchCryptoExchangeReserveDrainDigestReport:
        raise ValueError(
            "report must be exactly MarketResearchCryptoExchangeReserveDrainDigestReport",
        )
    _validate_payload_dataclass(report)
    return _freeze(_json_ready(report))


def _row_for_snapshot(
    snapshot: MarketResearchCryptoExchangeReserveDrainSnapshot,
    *,
    config: MarketResearchCryptoExchangeReserveDrainDigestConfig,
    generated_at: datetime,
) -> MarketResearchCryptoExchangeReserveDrainDigestRow:
    if snapshot.source_timestamp > generated_at:
        raise ValueError("source_timestamp must not be in the future")
    snapshot_age_seconds = _age_seconds(generated_at, snapshot.source_timestamp)
    reserve_drop_ratio = _reserve_drop_ratio(
        snapshot.reserve_balance,
        snapshot.previous_reserve_balance,
    )
    net_outflow_ratio = _net_outflow_ratio(
        snapshot.net_outflow,
        snapshot.previous_reserve_balance,
    )
    reason_codes = _row_reason_codes(
        snapshot=snapshot,
        config=config,
        snapshot_age_seconds=snapshot_age_seconds,
        reserve_drop_ratio=reserve_drop_ratio,
        net_outflow_ratio=net_outflow_ratio,
    )
    return MarketResearchCryptoExchangeReserveDrainDigestRow(
        condition_id=snapshot.condition_id,
        reserve_key=snapshot.reserve_key,
        asset_symbol=snapshot.asset_symbol,
        digest_status=_row_status(reason_codes),
        source_timestamp=snapshot.source_timestamp,
        snapshot_age_seconds=snapshot_age_seconds,
        source_count=snapshot.source_count,
        reserve_balance=snapshot.reserve_balance,
        previous_reserve_balance=snapshot.previous_reserve_balance,
        reserve_drop_ratio=reserve_drop_ratio,
        net_outflow=snapshot.net_outflow,
        net_outflow_ratio=net_outflow_ratio,
        confidence=snapshot.confidence,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    snapshot: MarketResearchCryptoExchangeReserveDrainSnapshot,
    config: MarketResearchCryptoExchangeReserveDrainDigestConfig,
    snapshot_age_seconds: Decimal,
    reserve_drop_ratio: Decimal,
    net_outflow_ratio: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if reserve_drop_ratio > config.max_reserve_drop_ratio:
        reasons.append(RESERVE_DROP_REASON)
    if net_outflow_ratio > config.max_net_outflow_ratio:
        reasons.append(NET_OUTFLOW_REASON)
    if snapshot.source_count < config.min_source_count:
        reasons.append(SOURCE_GAP_REASON)
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
            RESERVE_DROP_REASON,
            NET_OUTFLOW_REASON,
            STALE_SNAPSHOT_REASON,
            CONFIDENCE_GAP_REASON,
        )
    ):
        return STATUS_BLOCKED
    return STATUS_WATCH


def _row_sort_value(
    row: MarketResearchCryptoExchangeReserveDrainDigestRow,
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


def _report_status(rows: tuple[MarketResearchCryptoExchangeReserveDrainDigestRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_READY


def _recommended_next_step(status: str) -> str:
    if status == STATUS_BLOCKED:
        return "block_report_only_market_research_crypto_exchange_reserve_drain_digest"
    if status == STATUS_WATCH:
        return "review_report_only_market_research_crypto_exchange_reserve_drain_digest"
    return "allow_report_only_market_research_crypto_exchange_reserve_drain_digest"


def _status_count(
    rows: tuple[MarketResearchCryptoExchangeReserveDrainDigestRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.digest_status == status))


def _reason_snapshot_count(
    rows: tuple[MarketResearchCryptoExchangeReserveDrainDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _reason_code_counts(
    rows: tuple[MarketResearchCryptoExchangeReserveDrainDigestRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[MarketResearchCryptoExchangeReserveDrainDigestReasonCodeCount, ...]:
    snapshot_count = _decimal_count(len(rows))
    if reason_codes == (NO_INPUTS_REASON,):
        return (
            MarketResearchCryptoExchangeReserveDrainDigestReasonCodeCount(
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
        MarketResearchCryptoExchangeReserveDrainDigestReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
            snapshot_ratio=_ratio(_decimal_count(counts[reason_code]), snapshot_count),
        )
        for reason_code in reason_codes
        if reason_code in counts
    )


def _summary_reason_codes(
    rows: tuple[MarketResearchCryptoExchangeReserveDrainDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    seen: set[str] = set()
    for row in rows:
        seen.update(row.reason_codes)
    if len(seen) > 1 and READY_REASON in seen:
        seen.remove(READY_REASON)
    return tuple(reason for reason in REASON_CODE_SEQUENCE if reason in seen)


def _validate_row(row: MarketResearchCryptoExchangeReserveDrainDigestRow) -> None:
    if row.reserve_drop_ratio != _reserve_drop_ratio(
        row.reserve_balance,
        row.previous_reserve_balance,
    ):
        raise ValueError("reserve_drop_ratio does not match reserve balances")
    if row.net_outflow_ratio != _net_outflow_ratio(
        row.net_outflow,
        row.previous_reserve_balance,
    ):
        raise ValueError("net_outflow_ratio does not match reserve balances")
    if row.digest_status != _row_status(row.reason_codes):
        raise ValueError("digest_status does not match reason_codes")


def _validate_report(report: MarketResearchCryptoExchangeReserveDrainDigestReport) -> None:
    if report.snapshot_count != _decimal_count(len(report.rows)):
        raise ValueError("snapshot_count does not match rows")
    if report.ready_snapshot_count != _status_count(report.rows, STATUS_READY):
        raise ValueError("ready_snapshot_count does not match rows")
    if report.watch_snapshot_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_snapshot_count does not match rows")
    if report.blocked_snapshot_count != _status_count(report.rows, STATUS_BLOCKED):
        raise ValueError("blocked_snapshot_count does not match rows")
    expected_reason_counts = (
        (RESERVE_DROP_REASON, report.reserve_drop_snapshot_count),
        (NET_OUTFLOW_REASON, report.net_outflow_snapshot_count),
        (SOURCE_GAP_REASON, report.source_gap_snapshot_count),
        (STALE_SNAPSHOT_REASON, report.stale_snapshot_count),
        (CONFIDENCE_GAP_REASON, report.confidence_gap_snapshot_count),
    )
    for reason_code, actual_count in expected_reason_counts:
        if actual_count != _reason_snapshot_count(report.rows, reason_code):
            raise ValueError(f"{reason_code} count does not match rows")
    if report.average_reserve_drop_ratio != _ratio(
        _decimal_sum(row.reserve_drop_ratio for row in report.rows),
        report.snapshot_count,
    ):
        raise ValueError("average_reserve_drop_ratio does not match rows")
    if report.average_net_outflow_ratio != _ratio(
        _decimal_sum(row.net_outflow_ratio for row in report.rows),
        report.snapshot_count,
    ):
        raise ValueError("average_net_outflow_ratio does not match rows")
    if report.max_snapshot_age_seconds != max(
        (row.snapshot_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_snapshot_age_seconds does not match rows")
    if report.digest_status != _report_status(report.rows):
        raise ValueError("digest_status does not match rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step does not match digest_status")
    expected_rows = tuple(
        sorted(
            report.rows,
            key=lambda row: (
                _row_sort_value(row),
                row.reserve_key,
                row.condition_id,
            ),
        ),
    )
    if report.rows != expected_rows:
        raise ValueError("rows must be deterministically sorted")
    expected_source_config_keys = tuple(sorted(row.reserve_key for row in report.rows))
    actual_source_config_keys = tuple(
        reserve_key for reserve_key, _source_config_version in report.source_config_versions
    )
    if actual_source_config_keys != expected_source_config_keys:
        raise ValueError("source_config_versions do not match rows")
    if report.source_config_versions != tuple(sorted(report.source_config_versions)):
        raise ValueError("source_config_versions must be deterministically sorted")
    expected_reason_codes = _summary_reason_codes(report.rows)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes do not match rows")
    expected_reason_code_counts = _reason_code_counts(report.rows, report.reason_codes)
    if report.reason_code_counts != expected_reason_code_counts:
        raise ValueError("reason_code_counts do not match rows")


def _normalize_snapshots(
    snapshots: tuple[MarketResearchCryptoExchangeReserveDrainSnapshot, ...],
) -> tuple[MarketResearchCryptoExchangeReserveDrainSnapshot, ...]:
    if type(snapshots) is not tuple:
        raise ValueError("snapshots must be a tuple")
    reserve_keys: set[str] = set()
    for snapshot in snapshots:
        if type(snapshot) is not MarketResearchCryptoExchangeReserveDrainSnapshot:
            raise ValueError(
                "snapshots must contain exactly "
                "MarketResearchCryptoExchangeReserveDrainSnapshot records",
            )
        revalidated = _revalidate_snapshot(snapshot)
        _require_hard_flags("snapshot", revalidated)
        if revalidated.reserve_key in reserve_keys:
            raise ValueError("reserve_key values must be unique")
        reserve_keys.add(revalidated.reserve_key)
    return tuple(_revalidate_snapshot(snapshot) for snapshot in snapshots)


def _normalize_rows(
    rows: tuple[MarketResearchCryptoExchangeReserveDrainDigestRow, ...],
) -> tuple[MarketResearchCryptoExchangeReserveDrainDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not MarketResearchCryptoExchangeReserveDrainDigestRow:
            raise ValueError(
                "rows must contain exactly "
                "MarketResearchCryptoExchangeReserveDrainDigestRow records",
            )
        _revalidate_row(row)
        _require_hard_flags("row", row)
    return rows


def _normalize_source_config_versions(value: tuple[tuple[str, str], ...]) -> tuple[tuple[str, str], ...]:
    if type(value) is not tuple:
        raise ValueError("source_config_versions must be a tuple")
    normalized: list[tuple[str, str]] = []
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("source_config_versions must contain string pairs")
        reserve_key, source_config_version = item
        _require_canonical_string("source_config_versions reserve_key", reserve_key)
        _require_canonical_string(
            "source_config_versions source_config_version",
            source_config_version,
        )
        normalized.append((reserve_key, source_config_version))
    if len({reserve_key for reserve_key, _source_config_version in normalized}) != len(
        normalized,
    ):
        raise ValueError("source_config_versions must be unique")
    return tuple(normalized)


def _normalize_reason_code_counts(
    value: tuple[MarketResearchCryptoExchangeReserveDrainDigestReasonCodeCount, ...],
) -> tuple[MarketResearchCryptoExchangeReserveDrainDigestReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    seen: set[str] = set()
    for item in value:
        if type(item) is not MarketResearchCryptoExchangeReserveDrainDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain exactly "
                "MarketResearchCryptoExchangeReserveDrainDigestReasonCodeCount records",
            )
        _revalidate_reason_code_count(item)
        _require_hard_flags("reason_code_count", item)
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        seen.add(item.reason_code)
    canonical = tuple(
        sorted(
            value,
            key=lambda item: REASON_CODE_SEQUENCE.index(item.reason_code),
        ),
    )
    if value != canonical:
        raise ValueError("reason_code_counts must be deterministically sorted")
    return value


def _revalidate_config(
    config: MarketResearchCryptoExchangeReserveDrainDigestConfig,
) -> MarketResearchCryptoExchangeReserveDrainDigestConfig:
    return MarketResearchCryptoExchangeReserveDrainDigestConfig(
        **{
            field.name: getattr(config, field.name)
            for field in fields(MarketResearchCryptoExchangeReserveDrainDigestConfig)
        },
    )


def _revalidate_snapshot(
    snapshot: MarketResearchCryptoExchangeReserveDrainSnapshot,
) -> MarketResearchCryptoExchangeReserveDrainSnapshot:
    return MarketResearchCryptoExchangeReserveDrainSnapshot(
        **{
            field.name: getattr(snapshot, field.name)
            for field in fields(MarketResearchCryptoExchangeReserveDrainSnapshot)
        },
    )


def _revalidate_row(
    row: MarketResearchCryptoExchangeReserveDrainDigestRow,
) -> MarketResearchCryptoExchangeReserveDrainDigestRow:
    return MarketResearchCryptoExchangeReserveDrainDigestRow(
        **{
            field.name: getattr(row, field.name)
            for field in fields(MarketResearchCryptoExchangeReserveDrainDigestRow)
        },
    )


def _revalidate_reason_code_count(
    item: MarketResearchCryptoExchangeReserveDrainDigestReasonCodeCount,
) -> MarketResearchCryptoExchangeReserveDrainDigestReasonCodeCount:
    return MarketResearchCryptoExchangeReserveDrainDigestReasonCodeCount(
        **{
            field.name: getattr(item, field.name)
            for field in fields(MarketResearchCryptoExchangeReserveDrainDigestReasonCodeCount)
        },
    )


def _normalize_reason_codes(
    value: tuple[str, ...],
    *,
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not value:
        raise ValueError("reason_codes must contain at least one value")
    if len(set(value)) != len(value):
        raise ValueError("reason_codes must not contain duplicates")
    for reason_code in value:
        _require_reason_code("reason_codes", reason_code)
        if reason_code not in sequence:
            raise ValueError("reason_codes contain an invalid value for this record")
    canonical = tuple(reason for reason in sequence if reason in value)
    if value != canonical:
        raise ValueError("reason_codes must be deterministically sorted")
    return value


def _reserve_drop_ratio(reserve_balance: Decimal, previous_reserve_balance: Decimal) -> Decimal:
    if previous_reserve_balance <= ZERO:
        return ZERO
    reserve_drop = previous_reserve_balance - reserve_balance
    if reserve_drop <= ZERO:
        return ZERO
    return min(_ratio(reserve_drop, previous_reserve_balance), ONE)


def _net_outflow_ratio(net_outflow: Decimal, previous_reserve_balance: Decimal) -> Decimal:
    if previous_reserve_balance <= ZERO or net_outflow <= ZERO:
        return ZERO
    return min(_ratio(net_outflow, previous_reserve_balance), ONE)


def _age_seconds(generated_at: datetime, source_timestamp: datetime) -> Decimal:
    elapsed = generated_at - source_timestamp
    microseconds = Decimal(
        elapsed.days * 24 * 60 * 60 * 1000000
        + elapsed.seconds * 1000000
        + elapsed.microseconds,
    )
    return _quantize(microseconds / MICROSECONDS_PER_SECOND)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _decimal_sum(values: Any) -> Decimal:
    total = ZERO
    for value in values:
        total = _quantize(total + value)
    return total


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_utc_payload_datetime(field_name: str, value: object) -> None:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is not UTC:
        raise ValueError(f"{field_name} must be UTC for payload")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a supported reason code")


def _require_six_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != -6:
        raise ValueError(f"{field_name} must be an exact six-decimal Decimal")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must be canonical")
    return value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_six_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-number Decimal")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be no greater than one")
    return normalized


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _validate_payload_dataclass(value: object) -> None:
    if not is_dataclass(value) or type(value) not in PUBLIC_PAYLOAD_DATACLASS_TYPES:
        raise ValueError("payload value must be a supported public dataclass")
    _require_hard_flags(type(value).__name__, value)
    for field in fields(value):
        _validate_payload_value(field.name, getattr(value, field.name))
    value.__post_init__()  # type: ignore[attr-defined]


def _validate_payload_value(field_name: str, value: object) -> None:
    if is_dataclass(value):
        _validate_payload_dataclass(value)
        return
    if type(value) is Decimal:
        _require_six_decimal(field_name, value)
        return
    if type(value) is datetime:
        _require_utc_payload_datetime(field_name, value)
        return
    if type(value) is tuple:
        for item in value:
            _validate_payload_value(field_name, item)
        return
    if type(value) in (str, bool) or value is None:
        return
    raise ValueError("payload value must be immutable and public")


def _json_ready(value: object) -> Any:
    if is_dataclass(value):
        _validate_payload_dataclass(value)
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if type(value) is Decimal:
        _require_six_decimal("payload decimal", value)
        return format(value, "f")
    if type(value) is datetime:
        _require_utc_payload_datetime("payload datetime", value)
        return value.isoformat()
    if type(value) is tuple:
        return tuple(_json_ready(item) for item in value)
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError("payload value must be immutable and public")


def _freeze(value: Any) -> Any:
    if type(value) is dict:
        return MappingProxyType({key: _freeze(child) for key, child in value.items()})
    if type(value) is tuple:
        return tuple(_freeze(child) for child in value)
    return value
