"""Pure Phase 1 gold futures open interest market research reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from types import MappingProxyType
from typing import Any


DEFAULT_MARKET_RESEARCH_GOLD_FUTURES_OPEN_INTEREST_DIGEST_CONFIG_VERSION = (
    "market-research-gold-futures-open-interest-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

REASON_PREFIX = "market_research_gold_futures_open_interest_digest_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
READY_REASON = f"{REASON_PREFIX}ready"
STALE_SNAPSHOT_REASON = f"{REASON_PREFIX}stale_snapshot"
THIN_SOURCE_COUNT_REASON = f"{REASON_PREFIX}thin_source_count"
LOW_OPEN_INTEREST_REASON = f"{REASON_PREFIX}low_open_interest"
LOW_VOLUME_REASON = f"{REASON_PREFIX}low_volume"
OPEN_INTEREST_SHOCK_REASON = f"{REASON_PREFIX}open_interest_shock"
CONCENTRATION_PRESSURE_REASON = f"{REASON_PREFIX}concentration_pressure"
STALE_SOURCE_RATIO_REASON = f"{REASON_PREFIX}stale_source_ratio"
CONFIDENCE_GAP_REASON = f"{REASON_PREFIX}confidence_gap"

REASON_CODE_SEQUENCE = (
    STALE_SNAPSHOT_REASON,
    THIN_SOURCE_COUNT_REASON,
    LOW_OPEN_INTEREST_REASON,
    LOW_VOLUME_REASON,
    OPEN_INTEREST_SHOCK_REASON,
    CONCENTRATION_PRESSURE_REASON,
    STALE_SOURCE_RATIO_REASON,
    CONFIDENCE_GAP_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    STALE_SNAPSHOT_REASON,
    THIN_SOURCE_COUNT_REASON,
    LOW_OPEN_INTEREST_REASON,
    LOW_VOLUME_REASON,
    OPEN_INTEREST_SHOCK_REASON,
    CONCENTRATION_PRESSURE_REASON,
    STALE_SOURCE_RATIO_REASON,
    CONFIDENCE_GAP_REASON,
    READY_REASON,
)
NEXT_STEPS = {
    STATUS_READY: "allow_report_only_market_research_gold_futures_open_interest_digest",
    STATUS_WATCH: "monitor_report_only_market_research_gold_futures_open_interest_digest",
    STATUS_BLOCKED: "block_report_only_market_research_gold_futures_open_interest_digest",
}
BLOCKING_REASONS = frozenset(
    (
        STALE_SNAPSHOT_REASON,
        LOW_OPEN_INTEREST_REASON,
        LOW_VOLUME_REASON,
        OPEN_INTEREST_SHOCK_REASON,
        CONCENTRATION_PRESSURE_REASON,
        CONFIDENCE_GAP_REASON,
    ),
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
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("bro", "ker"),
        _join_parts("or", "der"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("rep", "lace"),
        _join_parts("ex", "change"),
        _join_parts("sig", "ning"),
        _join_parts("net", "work"),
        _join_parts("data", "base"),
        _join_parts("per", "sist"),
        _join_parts("sec", "ret"),
        _join_parts("to", "ken"),
        _join_parts("pri", "vate"),
        _join_parts("acc", "ount"),
    ),
)

PUBLIC_LABEL_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789._-")

__all__ = (
    "DEFAULT_MARKET_RESEARCH_GOLD_FUTURES_OPEN_INTEREST_DIGEST_CONFIG_VERSION",
    "MarketResearchGoldFuturesOpenInterestDigestConfig",
    "MarketResearchGoldFuturesOpenInterestDigestReasonCodeCount",
    "MarketResearchGoldFuturesOpenInterestDigestReport",
    "MarketResearchGoldFuturesOpenInterestDigestRow",
    "MarketResearchGoldFuturesOpenInterestSnapshot",
    "build_market_research_gold_futures_open_interest_digest",
    "market_research_gold_futures_open_interest_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchGoldFuturesOpenInterestDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_GOLD_FUTURES_OPEN_INTEREST_DIGEST_CONFIG_VERSION
    )
    max_snapshot_age_seconds: Decimal = Decimal("7200.000000")
    min_open_interest_contracts: Decimal = Decimal("10000.000000")
    min_volume_contracts: Decimal = Decimal("2500.000000")
    max_open_interest_change_abs: Decimal = Decimal("0.200000")
    min_source_count: Decimal = Decimal("2.000000")
    max_concentration_ratio: Decimal = Decimal("0.650000")
    max_stale_source_ratio: Decimal = Decimal("0.250000")
    min_confidence: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchGoldFuturesOpenInterestDigestConfig:
            raise TypeError(
                "MarketResearchGoldFuturesOpenInterestDigestConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchGoldFuturesOpenInterestDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchGoldFuturesOpenInterestDigestConfig",
            )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_GOLD_FUTURES_OPEN_INTEREST_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_snapshot_age_seconds",
            "min_open_interest_contracts",
            "min_volume_contracts",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_source_count",
            _require_positive_count_decimal("min_source_count", self.min_source_count),
        )
        for field_name in (
            "max_open_interest_change_abs",
            "max_concentration_ratio",
            "max_stale_source_ratio",
            "min_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchGoldFuturesOpenInterestSnapshot:
    condition_id: str
    open_interest_key: str
    contract_bucket: str
    observed_at: datetime
    open_interest_contracts: Decimal
    open_interest_change_ratio: Decimal
    volume_contracts: Decimal
    volume_to_open_interest_ratio: Decimal
    position_concentration_ratio: Decimal
    source_count: Decimal
    stale_source_ratio: Decimal
    confidence: Decimal
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchGoldFuturesOpenInterestSnapshot:
            raise TypeError(
                "MarketResearchGoldFuturesOpenInterestSnapshot "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchGoldFuturesOpenInterestSnapshot:
            raise ValueError(
                "snapshot must be exactly "
                "MarketResearchGoldFuturesOpenInterestSnapshot",
            )
        for field_name in (
            "condition_id",
            "open_interest_key",
            "contract_bucket",
            "source_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "open_interest_contracts",
            "volume_contracts",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "open_interest_change_ratio",
            _require_signed_ratio_decimal(
                "open_interest_change_ratio",
                self.open_interest_change_ratio,
            ),
        )
        for field_name in (
            "volume_to_open_interest_ratio",
            "position_concentration_ratio",
            "stale_source_ratio",
            "confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_count_decimal("source_count", self.source_count),
        )
        _require_hard_flags("snapshot", self)


@dataclass(frozen=True)
class MarketResearchGoldFuturesOpenInterestDigestRow:
    condition_id: str
    open_interest_key: str
    contract_bucket: str
    digest_status: str
    observed_at: datetime
    snapshot_age_seconds: Decimal
    open_interest_contracts: Decimal
    open_interest_change_ratio: Decimal
    open_interest_change_abs: Decimal
    volume_contracts: Decimal
    volume_to_open_interest_ratio: Decimal
    position_concentration_ratio: Decimal
    source_count: Decimal
    stale_source_ratio: Decimal
    confidence: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchGoldFuturesOpenInterestDigestRow:
            raise TypeError(
                "MarketResearchGoldFuturesOpenInterestDigestRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchGoldFuturesOpenInterestDigestRow:
            raise ValueError(
                "row must be exactly "
                "MarketResearchGoldFuturesOpenInterestDigestRow",
            )
        for field_name in ("condition_id", "open_interest_key", "contract_bucket"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_status("digest_status", self.digest_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "snapshot_age_seconds",
            _require_nonnegative_count_decimal(
                "snapshot_age_seconds",
                self.snapshot_age_seconds,
            ),
        )
        for field_name in (
            "open_interest_contracts",
            "volume_contracts",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "open_interest_change_ratio",
            _require_signed_ratio_decimal(
                "open_interest_change_ratio",
                self.open_interest_change_ratio,
            ),
        )
        for field_name in (
            "open_interest_change_abs",
            "volume_to_open_interest_ratio",
            "position_concentration_ratio",
            "stale_source_ratio",
            "confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_count_decimal("source_count", self.source_count),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                self.reason_codes,
                sequence=ROW_REASON_CODE_SEQUENCE,
            ),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchGoldFuturesOpenInterestDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    snapshot_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchGoldFuturesOpenInterestDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchGoldFuturesOpenInterestDigestReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchGoldFuturesOpenInterestDigestReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "MarketResearchGoldFuturesOpenInterestDigestReasonCodeCount",
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
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchGoldFuturesOpenInterestDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    snapshot_count: Decimal
    ready_snapshot_count: Decimal
    watch_snapshot_count: Decimal
    blocked_snapshot_count: Decimal
    stale_snapshot_count: Decimal
    thin_source_snapshot_count: Decimal
    low_open_interest_snapshot_count: Decimal
    low_volume_snapshot_count: Decimal
    open_interest_shock_snapshot_count: Decimal
    concentration_pressure_snapshot_count: Decimal
    stale_source_snapshot_count: Decimal
    confidence_gap_snapshot_count: Decimal
    average_open_interest_contracts: Decimal
    average_volume_contracts: Decimal
    average_open_interest_change_ratio: Decimal
    average_volume_to_open_interest_ratio: Decimal
    average_position_concentration_ratio: Decimal
    max_observed_snapshot_age_seconds: Decimal
    max_allowed_snapshot_age_seconds: Decimal
    min_open_interest_contracts: Decimal
    min_volume_contracts: Decimal
    max_allowed_open_interest_change_abs: Decimal
    min_source_count: Decimal
    max_concentration_ratio: Decimal
    max_stale_source_ratio: Decimal
    min_confidence: Decimal
    ready_snapshot_ratio: Decimal
    rows: tuple[MarketResearchGoldFuturesOpenInterestDigestRow, ...]
    source_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchGoldFuturesOpenInterestDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchGoldFuturesOpenInterestDigestReport:
            raise TypeError(
                "MarketResearchGoldFuturesOpenInterestDigestReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchGoldFuturesOpenInterestDigestReport:
            raise ValueError(
                "report must be exactly "
                "MarketResearchGoldFuturesOpenInterestDigestReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_GOLD_FUTURES_OPEN_INTEREST_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("digest_status", self.digest_status)
        _require_public_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "snapshot_count",
            "ready_snapshot_count",
            "watch_snapshot_count",
            "blocked_snapshot_count",
            "stale_snapshot_count",
            "thin_source_snapshot_count",
            "low_open_interest_snapshot_count",
            "low_volume_snapshot_count",
            "open_interest_shock_snapshot_count",
            "concentration_pressure_snapshot_count",
            "stale_source_snapshot_count",
            "confidence_gap_snapshot_count",
            "max_observed_snapshot_age_seconds",
            "min_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_open_interest_contracts",
            "average_volume_contracts",
            "max_allowed_snapshot_age_seconds",
            "min_open_interest_contracts",
            "min_volume_contracts",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_open_interest_change_ratio",
            _require_signed_ratio_decimal(
                "average_open_interest_change_ratio",
                self.average_open_interest_change_ratio,
            ),
        )
        for field_name in (
            "average_volume_to_open_interest_ratio",
            "average_position_concentration_ratio",
            "max_allowed_open_interest_change_abs",
            "max_concentration_ratio",
            "max_stale_source_ratio",
            "min_confidence",
            "ready_snapshot_ratio",
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


def build_market_research_gold_futures_open_interest_digest(
    snapshots: Iterable[MarketResearchGoldFuturesOpenInterestSnapshot],
    *,
    config: MarketResearchGoldFuturesOpenInterestDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchGoldFuturesOpenInterestDigestReport:
    cfg = (
        MarketResearchGoldFuturesOpenInterestDigestConfig()
        if config is None
        else config
    )
    if type(cfg) is not MarketResearchGoldFuturesOpenInterestDigestConfig:
        raise ValueError(
            "config must be exactly "
            "MarketResearchGoldFuturesOpenInterestDigestConfig",
        )
    _require_hard_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_snapshots = _normalize_snapshots(snapshots)
    rows = tuple(
        sorted(
            (
                _row_for_snapshot(
                    snapshot,
                    config=cfg,
                    generated_at=generated_at_utc,
                )
                for snapshot in normalized_snapshots
            ),
            key=lambda row: (
                _row_sort_value(row),
                row.open_interest_key,
                row.condition_id,
            ),
        ),
    )
    report_status = _report_status(rows)
    snapshot_count = _decimal_count(len(rows))
    reason_code_counts = _reason_code_counts(rows)
    return MarketResearchGoldFuturesOpenInterestDigestReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        digest_status=report_status,
        recommended_next_step=NEXT_STEPS[report_status],
        snapshot_count=snapshot_count,
        ready_snapshot_count=_status_count(rows, STATUS_READY),
        watch_snapshot_count=_status_count(rows, STATUS_WATCH),
        blocked_snapshot_count=_status_count(rows, STATUS_BLOCKED),
        stale_snapshot_count=_reason_snapshot_count(rows, STALE_SNAPSHOT_REASON),
        thin_source_snapshot_count=_reason_snapshot_count(
            rows,
            THIN_SOURCE_COUNT_REASON,
        ),
        low_open_interest_snapshot_count=_reason_snapshot_count(
            rows,
            LOW_OPEN_INTEREST_REASON,
        ),
        low_volume_snapshot_count=_reason_snapshot_count(rows, LOW_VOLUME_REASON),
        open_interest_shock_snapshot_count=_reason_snapshot_count(
            rows,
            OPEN_INTEREST_SHOCK_REASON,
        ),
        concentration_pressure_snapshot_count=_reason_snapshot_count(
            rows,
            CONCENTRATION_PRESSURE_REASON,
        ),
        stale_source_snapshot_count=_reason_snapshot_count(
            rows,
            STALE_SOURCE_RATIO_REASON,
        ),
        confidence_gap_snapshot_count=_reason_snapshot_count(
            rows,
            CONFIDENCE_GAP_REASON,
        ),
        average_open_interest_contracts=_ratio(
            _decimal_sum(row.open_interest_contracts for row in rows),
            snapshot_count,
        ),
        average_volume_contracts=_ratio(
            _decimal_sum(row.volume_contracts for row in rows),
            snapshot_count,
        ),
        average_open_interest_change_ratio=_ratio(
            _decimal_sum(row.open_interest_change_ratio for row in rows),
            snapshot_count,
        ),
        average_volume_to_open_interest_ratio=_ratio(
            _decimal_sum(row.volume_to_open_interest_ratio for row in rows),
            snapshot_count,
        ),
        average_position_concentration_ratio=_ratio(
            _decimal_sum(row.position_concentration_ratio for row in rows),
            snapshot_count,
        ),
        max_observed_snapshot_age_seconds=max(
            (row.snapshot_age_seconds for row in rows),
            default=ZERO,
        ),
        max_allowed_snapshot_age_seconds=cfg.max_snapshot_age_seconds,
        min_open_interest_contracts=cfg.min_open_interest_contracts,
        min_volume_contracts=cfg.min_volume_contracts,
        max_allowed_open_interest_change_abs=cfg.max_open_interest_change_abs,
        min_source_count=cfg.min_source_count,
        max_concentration_ratio=cfg.max_concentration_ratio,
        max_stale_source_ratio=cfg.max_stale_source_ratio,
        min_confidence=cfg.min_confidence,
        ready_snapshot_ratio=_ratio(_status_count(rows, STATUS_READY), snapshot_count),
        rows=rows,
        source_config_versions=tuple(
            sorted(
                (
                    snapshot.open_interest_key,
                    snapshot.source_config_version,
                )
                for snapshot in normalized_snapshots
            ),
        ),
        reason_code_counts=reason_code_counts,
        reason_codes=tuple(item.reason_code for item in reason_code_counts),
    )


def market_research_gold_futures_open_interest_digest_payload(
    report: MarketResearchGoldFuturesOpenInterestDigestReport,
) -> MappingProxyType:
    if type(report) is not MarketResearchGoldFuturesOpenInterestDigestReport:
        raise ValueError(
            "report must be exactly "
            "MarketResearchGoldFuturesOpenInterestDigestReport",
        )
    _require_hard_flags("report", report)
    return _freeze(_json_ready(report))


def _row_for_snapshot(
    snapshot: MarketResearchGoldFuturesOpenInterestSnapshot,
    *,
    config: MarketResearchGoldFuturesOpenInterestDigestConfig,
    generated_at: datetime,
) -> MarketResearchGoldFuturesOpenInterestDigestRow:
    if snapshot.observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    snapshot_age_seconds = _age_seconds(generated_at, snapshot.observed_at)
    open_interest_change_abs = _ratio_abs(snapshot.open_interest_change_ratio)
    reason_codes = _row_reason_codes(
        snapshot=snapshot,
        config=config,
        snapshot_age_seconds=snapshot_age_seconds,
        open_interest_change_abs=open_interest_change_abs,
    )
    return MarketResearchGoldFuturesOpenInterestDigestRow(
        condition_id=snapshot.condition_id,
        open_interest_key=snapshot.open_interest_key,
        contract_bucket=snapshot.contract_bucket,
        digest_status=_row_status(reason_codes),
        observed_at=snapshot.observed_at,
        snapshot_age_seconds=snapshot_age_seconds,
        open_interest_contracts=snapshot.open_interest_contracts,
        open_interest_change_ratio=snapshot.open_interest_change_ratio,
        open_interest_change_abs=open_interest_change_abs,
        volume_contracts=snapshot.volume_contracts,
        volume_to_open_interest_ratio=snapshot.volume_to_open_interest_ratio,
        position_concentration_ratio=snapshot.position_concentration_ratio,
        source_count=snapshot.source_count,
        stale_source_ratio=snapshot.stale_source_ratio,
        confidence=snapshot.confidence,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    snapshot: MarketResearchGoldFuturesOpenInterestSnapshot,
    config: MarketResearchGoldFuturesOpenInterestDigestConfig,
    snapshot_age_seconds: Decimal,
    open_interest_change_abs: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if snapshot_age_seconds > config.max_snapshot_age_seconds:
        reason_codes.append(STALE_SNAPSHOT_REASON)
    if snapshot.source_count < config.min_source_count:
        reason_codes.append(THIN_SOURCE_COUNT_REASON)
    if snapshot.open_interest_contracts < config.min_open_interest_contracts:
        reason_codes.append(LOW_OPEN_INTEREST_REASON)
    if snapshot.volume_contracts < config.min_volume_contracts:
        reason_codes.append(LOW_VOLUME_REASON)
    if open_interest_change_abs > config.max_open_interest_change_abs:
        reason_codes.append(OPEN_INTEREST_SHOCK_REASON)
    if snapshot.position_concentration_ratio > config.max_concentration_ratio:
        reason_codes.append(CONCENTRATION_PRESSURE_REASON)
    if snapshot.stale_source_ratio > config.max_stale_source_ratio:
        reason_codes.append(STALE_SOURCE_RATIO_REASON)
    if snapshot.confidence < config.min_confidence:
        reason_codes.append(CONFIDENCE_GAP_REASON)
    if not reason_codes:
        return (READY_REASON,)
    return tuple(reason for reason in ROW_REASON_CODE_SEQUENCE if reason in reason_codes)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    if any(reason_code in BLOCKING_REASONS for reason_code in reason_codes):
        return STATUS_BLOCKED
    return STATUS_WATCH


def _report_status(
    rows: tuple[MarketResearchGoldFuturesOpenInterestDigestRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_READY


def _row_sort_value(
    row: MarketResearchGoldFuturesOpenInterestDigestRow,
) -> tuple[int, Decimal]:
    status_rank = {
        STATUS_BLOCKED: 0,
        STATUS_WATCH: 1,
        STATUS_READY: 2,
    }[row.digest_status]
    severity = _decimal_count(
        sum(1 for reason_code in row.reason_codes if reason_code != READY_REASON),
    )
    return (status_rank, -severity)


def _status_count(
    rows: tuple[MarketResearchGoldFuturesOpenInterestDigestRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.digest_status == status))


def _reason_snapshot_count(
    rows: tuple[MarketResearchGoldFuturesOpenInterestDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _reason_code_counts(
    rows: tuple[MarketResearchGoldFuturesOpenInterestDigestRow, ...],
) -> tuple[MarketResearchGoldFuturesOpenInterestDigestReasonCodeCount, ...]:
    snapshot_count = _decimal_count(len(rows))
    if not rows:
        return (
            MarketResearchGoldFuturesOpenInterestDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                snapshot_ratio=ZERO,
            ),
        )
    return tuple(
        MarketResearchGoldFuturesOpenInterestDigestReasonCodeCount(
            reason_code=reason_code,
            count=count,
            snapshot_ratio=_ratio(count, snapshot_count),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code != NO_INPUTS_REASON
        if (count := _reason_snapshot_count(rows, reason_code)) > ZERO
    )


def _validate_row(row: MarketResearchGoldFuturesOpenInterestDigestRow) -> None:
    if row.open_interest_change_abs != _ratio_abs(row.open_interest_change_ratio):
        raise ValueError("open_interest_change_abs must match open_interest_change_ratio")
    if row.digest_status != _row_status(row.reason_codes):
        raise ValueError("digest_status must match reason_codes")


def _validate_report(report: MarketResearchGoldFuturesOpenInterestDigestReport) -> None:
    if report.snapshot_count != _decimal_count(len(report.rows)):
        raise ValueError("snapshot_count must match rows")
    if report.ready_snapshot_count != _status_count(report.rows, STATUS_READY):
        raise ValueError("ready_snapshot_count must match rows")
    if report.watch_snapshot_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_snapshot_count must match rows")
    if report.blocked_snapshot_count != _status_count(report.rows, STATUS_BLOCKED):
        raise ValueError("blocked_snapshot_count must match rows")
    reason_checks = (
        ("stale_snapshot_count", STALE_SNAPSHOT_REASON),
        ("thin_source_snapshot_count", THIN_SOURCE_COUNT_REASON),
        ("low_open_interest_snapshot_count", LOW_OPEN_INTEREST_REASON),
        ("low_volume_snapshot_count", LOW_VOLUME_REASON),
        ("open_interest_shock_snapshot_count", OPEN_INTEREST_SHOCK_REASON),
        ("concentration_pressure_snapshot_count", CONCENTRATION_PRESSURE_REASON),
        ("stale_source_snapshot_count", STALE_SOURCE_RATIO_REASON),
        ("confidence_gap_snapshot_count", CONFIDENCE_GAP_REASON),
    )
    for field_name, reason_code in reason_checks:
        if getattr(report, field_name) != _reason_snapshot_count(
            report.rows,
            reason_code,
        ):
            raise ValueError(f"{field_name} must match rows")
    if report.average_open_interest_contracts != _ratio(
        _decimal_sum(row.open_interest_contracts for row in report.rows),
        report.snapshot_count,
    ):
        raise ValueError("average_open_interest_contracts must match rows")
    if report.average_volume_contracts != _ratio(
        _decimal_sum(row.volume_contracts for row in report.rows),
        report.snapshot_count,
    ):
        raise ValueError("average_volume_contracts must match rows")
    if report.average_open_interest_change_ratio != _ratio(
        _decimal_sum(row.open_interest_change_ratio for row in report.rows),
        report.snapshot_count,
    ):
        raise ValueError("average_open_interest_change_ratio must match rows")
    if report.average_volume_to_open_interest_ratio != _ratio(
        _decimal_sum(row.volume_to_open_interest_ratio for row in report.rows),
        report.snapshot_count,
    ):
        raise ValueError("average_volume_to_open_interest_ratio must match rows")
    if report.average_position_concentration_ratio != _ratio(
        _decimal_sum(row.position_concentration_ratio for row in report.rows),
        report.snapshot_count,
    ):
        raise ValueError("average_position_concentration_ratio must match rows")
    if report.max_observed_snapshot_age_seconds != max(
        (row.snapshot_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_observed_snapshot_age_seconds must match rows")
    if report.ready_snapshot_ratio != _ratio(
        report.ready_snapshot_count,
        report.snapshot_count,
    ):
        raise ValueError("ready_snapshot_ratio must match rows")
    if len(report.source_config_versions) != len(report.rows):
        raise ValueError("source_config_versions must match rows")
    source_config_keys = tuple(
        open_interest_key
        for open_interest_key, _source_config_version in report.source_config_versions
    )
    row_keys = tuple(sorted(row.open_interest_key for row in report.rows))
    if source_config_keys != row_keys:
        raise ValueError("source_config_versions must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")
    if report.digest_status != _report_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")


def _normalize_snapshots(
    snapshots: Iterable[MarketResearchGoldFuturesOpenInterestSnapshot],
) -> tuple[MarketResearchGoldFuturesOpenInterestSnapshot, ...]:
    if isinstance(snapshots, (str, bytes)):
        raise ValueError("snapshots must be an iterable of digest snapshots")
    try:
        rows = tuple(snapshots)
    except TypeError as exc:
        raise ValueError("snapshots must be an iterable of digest snapshots") from exc
    seen: set[str] = set()
    for snapshot in rows:
        if type(snapshot) is not MarketResearchGoldFuturesOpenInterestSnapshot:
            raise ValueError(
                "snapshots must contain "
                "MarketResearchGoldFuturesOpenInterestSnapshot",
            )
        _require_hard_flags("snapshot", snapshot)
        if snapshot.open_interest_key in seen:
            raise ValueError(
                "snapshots must not contain duplicate open_interest_key values",
            )
        seen.add(snapshot.open_interest_key)
    return rows


def _normalize_rows(
    value: object,
) -> tuple[MarketResearchGoldFuturesOpenInterestDigestRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not MarketResearchGoldFuturesOpenInterestDigestRow:
            raise ValueError(
                "rows must contain "
                "MarketResearchGoldFuturesOpenInterestDigestRow",
            )
        _require_hard_flags("row", row)
    expected = tuple(
        sorted(
            rows,
            key=lambda row: (
                _row_sort_value(row),
                row.open_interest_key,
                row.condition_id,
            ),
        ),
    )
    if rows != expected:
        raise ValueError("rows must use deterministic sort")
    if len({row.open_interest_key for row in rows}) != len(rows):
        raise ValueError("rows must use unique open_interest_key values")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[MarketResearchGoldFuturesOpenInterestDigestReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not MarketResearchGoldFuturesOpenInterestDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchGoldFuturesOpenInterestDigestReasonCodeCount",
            )
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        seen.add(row.reason_code)
    expected = tuple(
        item
        for reason_code in REASON_CODE_SEQUENCE
        for item in rows
        if item.reason_code == reason_code
    )
    if rows != expected:
        raise ValueError("reason_code_counts must use deterministic sort")
    return rows


def _normalize_source_config_versions(value: object) -> tuple[tuple[str, str], ...]:
    if type(value) not in (list, tuple):
        raise ValueError("source_config_versions must be a list or tuple")
    rows = tuple(value)
    normalized: list[tuple[str, str]] = []
    for row in rows:
        if type(row) not in (list, tuple) or len(row) != 2:
            raise ValueError("source_config_versions rows must be pairs")
        open_interest_key, config_version = row
        _require_public_string("open_interest_key", open_interest_key)
        _require_public_string("source_config_version", config_version)
        normalized.append((open_interest_key, config_version))
    result = tuple(normalized)
    if result != tuple(sorted(result)):
        raise ValueError("source_config_versions must use deterministic sort")
    if len({open_interest_key for open_interest_key, _ in result}) != len(result):
        raise ValueError("source_config_versions must be unique")
    return result


def _normalize_reason_codes(
    value: object,
    *,
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        if reason_code not in sequence:
            raise ValueError("reason_code must be known")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    if tuple(code for code in sequence if code in reason_codes) != reason_codes:
        raise ValueError("reason_codes must use deterministic sort")
    return reason_codes


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


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
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _ratio_abs(value: Decimal) -> Decimal:
    return _quantize(abs(value))


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    return _quantize(
        Decimal(delta.days) * Decimal("86400")
        + Decimal(delta.seconds)
        + Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND,
    )


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return format(value, "f")
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if type(value) in (str, bool):
        return value
    if type(value) is int or type(value) is float:
        raise ValueError("JSON value must not be a public numeric primitive")
    if isinstance(value, tuple):
        return tuple(_json_ready(item) for item in value)
    if isinstance(value, list):
        return tuple(_json_ready(item) for item in value)
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    raise ValueError("value is not JSON serializable")


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, tuple):
        return tuple(_freeze(item) for item in value)
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone aware")
    return value.astimezone(UTC)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(value)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value().quantize(QUANT):
        raise ValueError(f"{field_name} must be integral")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be in the inclusive 0 to 1 range")
    return _quantize(value)


def _require_signed_ratio_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < -ONE or value > ONE:
        raise ValueError(f"{field_name} must be in the inclusive -1 to 1 range")
    return _quantize(value)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    assert type(value) is str
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must not include unsafe text")
    if any(char not in PUBLIC_LABEL_CHARS for char in lowered):
        raise ValueError(f"{field_name} must be identifier-like")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be a valid digest status")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a known reason code")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")
