"""Pure Phase 1 crypto basis spread dislocation reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from types import MappingProxyType
from typing import Any


DEFAULT_MARKET_RESEARCH_CRYPTO_BASIS_SPREAD_DISLOCATION_DIGEST_CONFIG_VERSION = (
    "market-research-crypto-basis-spread-dislocation-digest-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
DIGEST_STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCKED)

PASS_REASON = (
    "market_research_crypto_basis_spread_dislocation_digest_spread_aligned"
)
NO_INPUTS_REASON = (
    "market_research_crypto_basis_spread_dislocation_digest_no_inputs"
)
BLOCKED_SPREAD_DISLOCATION_REASON = (
    "market_research_crypto_basis_spread_dislocation_digest_blocked_spread_dislocation"
)
WATCH_SPREAD_DISLOCATION_REASON = (
    "market_research_crypto_basis_spread_dislocation_digest_watch_spread_dislocation"
)
BLOCKED_SPREAD_CHANGE_REASON = (
    "market_research_crypto_basis_spread_dislocation_digest_blocked_spread_change"
)
WATCH_SPREAD_CHANGE_REASON = (
    "market_research_crypto_basis_spread_dislocation_digest_watch_spread_change"
)
SOURCE_GAP_REASON = (
    "market_research_crypto_basis_spread_dislocation_digest_source_gap"
)
LIQUIDITY_GAP_REASON = (
    "market_research_crypto_basis_spread_dislocation_digest_liquidity_gap"
)
STALE_SNAPSHOT_REASON = (
    "market_research_crypto_basis_spread_dislocation_digest_stale_snapshot"
)
CONFIDENCE_GAP_REASON = (
    "market_research_crypto_basis_spread_dislocation_digest_confidence_gap"
)

REASON_CODE_SEQUENCE = (
    BLOCKED_SPREAD_DISLOCATION_REASON,
    WATCH_SPREAD_DISLOCATION_REASON,
    BLOCKED_SPREAD_CHANGE_REASON,
    WATCH_SPREAD_CHANGE_REASON,
    SOURCE_GAP_REASON,
    LIQUIDITY_GAP_REASON,
    STALE_SNAPSHOT_REASON,
    CONFIDENCE_GAP_REASON,
    PASS_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    BLOCKED_SPREAD_DISLOCATION_REASON,
    WATCH_SPREAD_DISLOCATION_REASON,
    BLOCKED_SPREAD_CHANGE_REASON,
    WATCH_SPREAD_CHANGE_REASON,
    SOURCE_GAP_REASON,
    LIQUIDITY_GAP_REASON,
    STALE_SNAPSHOT_REASON,
    CONFIDENCE_GAP_REASON,
    PASS_REASON,
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000.000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("mar", "ket", "_", "slug"),
        _join_parts("ques", "tion"),
        _join_parts("wa", "llet"),
        _join_parts("or", "der"),
        _join_parts("can", "cel"),
        _join_parts("re", "place"),
        _join_parts("sub", "mit"),
        _join_parts("ex", "change"),
        _join_parts("api", "_", "key"),
        _join_parts("access", "_", "key"),
        _join_parts("sec", "ret", "_", "key"),
        _join_parts("tr", "ade"),
        _join_parts("tra", "ding"),
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
    "DEFAULT_MARKET_RESEARCH_CRYPTO_BASIS_SPREAD_DISLOCATION_DIGEST_CONFIG_VERSION",
    "MarketResearchCryptoBasisSpreadDislocationDigestConfig",
    "MarketResearchCryptoBasisSpreadDislocationDigestReasonCodeCount",
    "MarketResearchCryptoBasisSpreadDislocationDigestReport",
    "MarketResearchCryptoBasisSpreadDislocationDigestRow",
    "MarketResearchCryptoBasisSpreadDislocationSnapshot",
    "build_market_research_crypto_basis_spread_dislocation_digest",
    "market_research_crypto_basis_spread_dislocation_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchCryptoBasisSpreadDislocationDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_CRYPTO_BASIS_SPREAD_DISLOCATION_DIGEST_CONFIG_VERSION
    )
    max_snapshot_age_seconds: Decimal = Decimal("3600.000000")
    watch_spread_dislocation_abs: Decimal = Decimal("0.015000")
    blocked_spread_dislocation_abs: Decimal = Decimal("0.035000")
    watch_spread_change_abs: Decimal = Decimal("0.010000")
    blocked_spread_change_abs: Decimal = Decimal("0.025000")
    min_source_count: Decimal = Decimal("3.000000")
    min_liquidity_usd: Decimal = Decimal("1000000.000000")
    min_confidence: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoBasisSpreadDislocationDigestConfig:
            raise TypeError(
                "MarketResearchCryptoBasisSpreadDislocationDigestConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoBasisSpreadDislocationDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchCryptoBasisSpreadDislocationDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_CRYPTO_BASIS_SPREAD_DISLOCATION_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("max_snapshot_age_seconds", "min_source_count"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_liquidity_usd",
            _require_nonnegative_decimal("min_liquidity_usd", self.min_liquidity_usd),
        )
        for field_name in (
            "watch_spread_dislocation_abs",
            "blocked_spread_dislocation_abs",
            "watch_spread_change_abs",
            "blocked_spread_change_abs",
            "min_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.blocked_spread_dislocation_abs < self.watch_spread_dislocation_abs:
            raise ValueError(
                "blocked_spread_dislocation_abs must be at least watch threshold",
            )
        if self.blocked_spread_change_abs < self.watch_spread_change_abs:
            raise ValueError("blocked_spread_change_abs must be at least watch threshold")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchCryptoBasisSpreadDislocationSnapshot:
    condition_id: str
    spread_id: str
    asset_symbol: str
    basis_pair: str
    near_tenor: str
    far_tenor: str
    observed_at: datetime
    near_basis_pct: Decimal
    far_basis_pct: Decimal
    expected_spread_pct: Decimal
    observed_spread_pct: Decimal
    previous_spread_pct: Decimal
    source_count: Decimal
    liquidity_usd: Decimal
    confidence: Decimal
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoBasisSpreadDislocationSnapshot:
            raise TypeError(
                "MarketResearchCryptoBasisSpreadDislocationSnapshot "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoBasisSpreadDislocationSnapshot:
            raise ValueError(
                "snapshot must be exactly "
                "MarketResearchCryptoBasisSpreadDislocationSnapshot",
            )
        for field_name in (
            "condition_id",
            "spread_id",
            "asset_symbol",
            "basis_pair",
            "near_tenor",
            "far_tenor",
            "source_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("source_count", "liquidity_usd"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "near_basis_pct",
            "far_basis_pct",
            "expected_spread_pct",
            "observed_spread_pct",
            "previous_spread_pct",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_signed_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "confidence",
            _require_ratio_decimal("confidence", self.confidence),
        )
        _require_hard_flags("snapshot", self)


@dataclass(frozen=True)
class MarketResearchCryptoBasisSpreadDislocationDigestRow:
    condition_id: str
    spread_id: str
    asset_symbol: str
    basis_pair: str
    near_tenor: str
    far_tenor: str
    digest_status: str
    observed_at: datetime
    snapshot_age_seconds: Decimal
    near_basis_pct: Decimal
    far_basis_pct: Decimal
    expected_spread_pct: Decimal
    observed_spread_pct: Decimal
    previous_spread_pct: Decimal
    spread_dislocation_abs: Decimal
    spread_change_abs: Decimal
    source_count: Decimal
    liquidity_usd: Decimal
    confidence: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoBasisSpreadDislocationDigestRow:
            raise TypeError(
                "MarketResearchCryptoBasisSpreadDislocationDigestRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoBasisSpreadDislocationDigestRow:
            raise ValueError(
                "row must be exactly "
                "MarketResearchCryptoBasisSpreadDislocationDigestRow",
            )
        for field_name in (
            "condition_id",
            "spread_id",
            "asset_symbol",
            "basis_pair",
            "near_tenor",
            "far_tenor",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_status("digest_status", self.digest_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "snapshot_age_seconds",
            "spread_dislocation_abs",
            "spread_change_abs",
            "source_count",
            "liquidity_usd",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "near_basis_pct",
            "far_basis_pct",
            "expected_spread_pct",
            "observed_spread_pct",
            "previous_spread_pct",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_signed_ratio_decimal(field_name, getattr(self, field_name)),
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
class MarketResearchCryptoBasisSpreadDislocationDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    snapshot_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoBasisSpreadDislocationDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchCryptoBasisSpreadDislocationDigestReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if (
            type(self)
            is not MarketResearchCryptoBasisSpreadDislocationDigestReasonCodeCount
        ):
            raise ValueError(
                "reason code count must be exactly "
                "MarketResearchCryptoBasisSpreadDislocationDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        if self.count == ZERO:
            raise ValueError("count must be positive")
        object.__setattr__(
            self,
            "snapshot_ratio",
            _require_ratio_decimal("snapshot_ratio", self.snapshot_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchCryptoBasisSpreadDislocationDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    snapshot_count: Decimal
    pass_snapshot_count: Decimal
    watch_snapshot_count: Decimal
    blocked_snapshot_count: Decimal
    spread_dislocation_snapshot_count: Decimal
    spread_change_snapshot_count: Decimal
    source_gap_snapshot_count: Decimal
    liquidity_gap_snapshot_count: Decimal
    stale_snapshot_count: Decimal
    confidence_gap_snapshot_count: Decimal
    average_observed_spread_pct: Decimal
    average_spread_dislocation_abs: Decimal
    max_spread_dislocation_abs: Decimal
    max_snapshot_age_seconds: Decimal
    max_allowed_snapshot_age_seconds: Decimal
    watch_spread_dislocation_abs: Decimal
    blocked_spread_dislocation_abs: Decimal
    watch_spread_change_abs: Decimal
    blocked_spread_change_abs: Decimal
    min_source_count: Decimal
    min_liquidity_usd: Decimal
    min_confidence: Decimal
    rows: tuple[MarketResearchCryptoBasisSpreadDislocationDigestRow, ...]
    source_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchCryptoBasisSpreadDislocationDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoBasisSpreadDislocationDigestReport:
            raise TypeError(
                "MarketResearchCryptoBasisSpreadDislocationDigestReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoBasisSpreadDislocationDigestReport:
            raise ValueError(
                "report must be exactly "
                "MarketResearchCryptoBasisSpreadDislocationDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_CRYPTO_BASIS_SPREAD_DISLOCATION_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "snapshot_count",
            "pass_snapshot_count",
            "watch_snapshot_count",
            "blocked_snapshot_count",
            "spread_dislocation_snapshot_count",
            "spread_change_snapshot_count",
            "source_gap_snapshot_count",
            "liquidity_gap_snapshot_count",
            "stale_snapshot_count",
            "confidence_gap_snapshot_count",
            "average_spread_dislocation_abs",
            "max_spread_dislocation_abs",
            "max_snapshot_age_seconds",
            "max_allowed_snapshot_age_seconds",
            "watch_spread_dislocation_abs",
            "blocked_spread_dislocation_abs",
            "watch_spread_change_abs",
            "blocked_spread_change_abs",
            "min_source_count",
            "min_liquidity_usd",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_observed_spread_pct",
            _require_signed_ratio_decimal(
                "average_observed_spread_pct",
                self.average_observed_spread_pct,
            ),
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


def build_market_research_crypto_basis_spread_dislocation_digest(
    snapshots: Iterable[MarketResearchCryptoBasisSpreadDislocationSnapshot],
    *,
    config: MarketResearchCryptoBasisSpreadDislocationDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchCryptoBasisSpreadDislocationDigestReport:
    cfg = config or MarketResearchCryptoBasisSpreadDislocationDigestConfig()
    if type(cfg) is not MarketResearchCryptoBasisSpreadDislocationDigestConfig:
        raise ValueError(
            "config must be exactly "
            "MarketResearchCryptoBasisSpreadDislocationDigestConfig",
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
                row.spread_id,
                row.condition_id,
            ),
        ),
    )
    report_status = _report_status(sorted_rows)
    return MarketResearchCryptoBasisSpreadDislocationDigestReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        digest_status=report_status,
        recommended_next_step=_recommended_next_step(report_status),
        snapshot_count=_decimal_count(len(sorted_rows)),
        pass_snapshot_count=_status_count(sorted_rows, STATUS_PASS),
        watch_snapshot_count=_status_count(sorted_rows, STATUS_WATCH),
        blocked_snapshot_count=_status_count(sorted_rows, STATUS_BLOCKED),
        spread_dislocation_snapshot_count=_spread_dislocation_count(sorted_rows),
        spread_change_snapshot_count=_spread_change_count(sorted_rows),
        source_gap_snapshot_count=_reason_snapshot_count(sorted_rows, SOURCE_GAP_REASON),
        liquidity_gap_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            LIQUIDITY_GAP_REASON,
        ),
        stale_snapshot_count=_reason_snapshot_count(sorted_rows, STALE_SNAPSHOT_REASON),
        confidence_gap_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            CONFIDENCE_GAP_REASON,
        ),
        average_observed_spread_pct=_ratio(
            _decimal_sum(row.observed_spread_pct for row in sorted_rows),
            _decimal_count(len(sorted_rows)),
        ),
        average_spread_dislocation_abs=_ratio(
            _decimal_sum(row.spread_dislocation_abs for row in sorted_rows),
            _decimal_count(len(sorted_rows)),
        ),
        max_spread_dislocation_abs=max(
            (row.spread_dislocation_abs for row in sorted_rows),
            default=ZERO,
        ),
        max_snapshot_age_seconds=max(
            (row.snapshot_age_seconds for row in sorted_rows),
            default=ZERO,
        ),
        max_allowed_snapshot_age_seconds=cfg.max_snapshot_age_seconds,
        watch_spread_dislocation_abs=cfg.watch_spread_dislocation_abs,
        blocked_spread_dislocation_abs=cfg.blocked_spread_dislocation_abs,
        watch_spread_change_abs=cfg.watch_spread_change_abs,
        blocked_spread_change_abs=cfg.blocked_spread_change_abs,
        min_source_count=cfg.min_source_count,
        min_liquidity_usd=cfg.min_liquidity_usd,
        min_confidence=cfg.min_confidence,
        rows=sorted_rows,
        source_config_versions=tuple(
            sorted(
                (snapshot.spread_id, snapshot.source_config_version)
                for snapshot in normalized_snapshots
            ),
        ),
        reason_code_counts=_reason_code_counts(sorted_rows),
        reason_codes=_summary_reason_codes(sorted_rows),
    )


def market_research_crypto_basis_spread_dislocation_digest_payload(
    report: MarketResearchCryptoBasisSpreadDislocationDigestReport,
) -> MappingProxyType:
    if type(report) is not MarketResearchCryptoBasisSpreadDislocationDigestReport:
        raise ValueError(
            "report must be exactly "
            "MarketResearchCryptoBasisSpreadDislocationDigestReport",
        )
    _require_payload_datetimes_utc(report)
    revalidated_report = _revalidate_report(report)
    _require_hard_flags("report", revalidated_report)
    return _freeze(_json_ready(revalidated_report))


def _row_for_snapshot(
    snapshot: MarketResearchCryptoBasisSpreadDislocationSnapshot,
    *,
    config: MarketResearchCryptoBasisSpreadDislocationDigestConfig,
    generated_at: datetime,
) -> MarketResearchCryptoBasisSpreadDislocationDigestRow:
    if snapshot.observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    snapshot_age_seconds = _age_seconds(generated_at, snapshot.observed_at)
    spread_dislocation_abs = _ratio_abs(
        snapshot.observed_spread_pct - snapshot.expected_spread_pct,
    )
    spread_change_abs = _ratio_abs(
        snapshot.observed_spread_pct - snapshot.previous_spread_pct,
    )
    reason_codes = _row_reason_codes(
        snapshot=snapshot,
        config=config,
        snapshot_age_seconds=snapshot_age_seconds,
        spread_dislocation_abs=spread_dislocation_abs,
        spread_change_abs=spread_change_abs,
    )
    return MarketResearchCryptoBasisSpreadDislocationDigestRow(
        condition_id=snapshot.condition_id,
        spread_id=snapshot.spread_id,
        asset_symbol=snapshot.asset_symbol,
        basis_pair=snapshot.basis_pair,
        near_tenor=snapshot.near_tenor,
        far_tenor=snapshot.far_tenor,
        digest_status=_row_status(reason_codes),
        observed_at=snapshot.observed_at,
        snapshot_age_seconds=snapshot_age_seconds,
        near_basis_pct=snapshot.near_basis_pct,
        far_basis_pct=snapshot.far_basis_pct,
        expected_spread_pct=snapshot.expected_spread_pct,
        observed_spread_pct=snapshot.observed_spread_pct,
        previous_spread_pct=snapshot.previous_spread_pct,
        spread_dislocation_abs=spread_dislocation_abs,
        spread_change_abs=spread_change_abs,
        source_count=snapshot.source_count,
        liquidity_usd=snapshot.liquidity_usd,
        confidence=snapshot.confidence,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    snapshot: MarketResearchCryptoBasisSpreadDislocationSnapshot,
    config: MarketResearchCryptoBasisSpreadDislocationDigestConfig,
    snapshot_age_seconds: Decimal,
    spread_dislocation_abs: Decimal,
    spread_change_abs: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if spread_dislocation_abs >= config.blocked_spread_dislocation_abs:
        reasons.append(BLOCKED_SPREAD_DISLOCATION_REASON)
    elif spread_dislocation_abs >= config.watch_spread_dislocation_abs:
        reasons.append(WATCH_SPREAD_DISLOCATION_REASON)
    if spread_change_abs >= config.blocked_spread_change_abs:
        reasons.append(BLOCKED_SPREAD_CHANGE_REASON)
    elif spread_change_abs >= config.watch_spread_change_abs:
        reasons.append(WATCH_SPREAD_CHANGE_REASON)
    if snapshot.source_count < config.min_source_count:
        reasons.append(SOURCE_GAP_REASON)
    if snapshot.liquidity_usd < config.min_liquidity_usd:
        reasons.append(LIQUIDITY_GAP_REASON)
    if snapshot_age_seconds > config.max_snapshot_age_seconds:
        reasons.append(STALE_SNAPSHOT_REASON)
    if snapshot.confidence < config.min_confidence:
        reasons.append(CONFIDENCE_GAP_REASON)
    if not reasons:
        reasons.append(PASS_REASON)
    return tuple(reason for reason in ROW_REASON_CODE_SEQUENCE if reason in reasons)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (PASS_REASON,):
        return STATUS_PASS
    if any(
        reason in reason_codes
        for reason in (
            BLOCKED_SPREAD_DISLOCATION_REASON,
            BLOCKED_SPREAD_CHANGE_REASON,
            STALE_SNAPSHOT_REASON,
            CONFIDENCE_GAP_REASON,
        )
    ):
        return STATUS_BLOCKED
    return STATUS_WATCH


def _row_sort_value(
    row: MarketResearchCryptoBasisSpreadDislocationDigestRow,
) -> tuple[int, Decimal, Decimal, Decimal]:
    status_rank = {
        STATUS_BLOCKED: 0,
        STATUS_WATCH: 1,
        STATUS_PASS: 2,
    }[row.digest_status]
    severity = _decimal_count(
        len(tuple(reason for reason in row.reason_codes if reason != PASS_REASON)),
    )
    return (
        status_rank,
        -severity,
        -row.spread_dislocation_abs,
        -row.spread_change_abs,
    )


def _report_status(
    rows: tuple[MarketResearchCryptoBasisSpreadDislocationDigestRow, ...],
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
        return "block_report_only_market_research_crypto_basis_spread_dislocation_digest"
    if status == STATUS_WATCH:
        return "review_report_only_market_research_crypto_basis_spread_dislocation_digest"
    return "allow_report_only_market_research_crypto_basis_spread_dislocation_digest"


def _status_count(
    rows: tuple[MarketResearchCryptoBasisSpreadDislocationDigestRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.digest_status == status))


def _reason_snapshot_count(
    rows: tuple[MarketResearchCryptoBasisSpreadDislocationDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _spread_dislocation_count(
    rows: tuple[MarketResearchCryptoBasisSpreadDislocationDigestRow, ...],
) -> Decimal:
    return _decimal_count(
        sum(
            1
            for row in rows
            if BLOCKED_SPREAD_DISLOCATION_REASON in row.reason_codes
            or WATCH_SPREAD_DISLOCATION_REASON in row.reason_codes
        ),
    )


def _spread_change_count(
    rows: tuple[MarketResearchCryptoBasisSpreadDislocationDigestRow, ...],
) -> Decimal:
    return _decimal_count(
        sum(
            1
            for row in rows
            if BLOCKED_SPREAD_CHANGE_REASON in row.reason_codes
            or WATCH_SPREAD_CHANGE_REASON in row.reason_codes
        ),
    )


def _reason_code_counts(
    rows: tuple[MarketResearchCryptoBasisSpreadDislocationDigestRow, ...],
) -> tuple[MarketResearchCryptoBasisSpreadDislocationDigestReasonCodeCount, ...]:
    snapshot_count = _decimal_count(len(rows))
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        MarketResearchCryptoBasisSpreadDislocationDigestReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
            snapshot_ratio=_ratio(_decimal_count(counts[reason_code]), snapshot_count),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _summary_reason_codes(
    rows: tuple[MarketResearchCryptoBasisSpreadDislocationDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    seen: set[str] = set()
    for row in rows:
        seen.update(row.reason_codes)
    if len(seen) > 1 and PASS_REASON in seen:
        seen.remove(PASS_REASON)
    return tuple(reason for reason in REASON_CODE_SEQUENCE if reason in seen)


def _validate_row(
    row: MarketResearchCryptoBasisSpreadDislocationDigestRow,
) -> None:
    if row.spread_dislocation_abs != _ratio_abs(
        row.observed_spread_pct - row.expected_spread_pct,
    ):
        raise ValueError("spread_dislocation_abs does not match spread inputs")
    if row.spread_change_abs != _ratio_abs(
        row.observed_spread_pct - row.previous_spread_pct,
    ):
        raise ValueError("spread_change_abs does not match spread inputs")
    if row.digest_status != _row_status(row.reason_codes):
        raise ValueError("digest_status does not match reason_codes")


def _validate_report(
    report: MarketResearchCryptoBasisSpreadDislocationDigestReport,
) -> None:
    if report.snapshot_count != _decimal_count(len(report.rows)):
        raise ValueError("snapshot_count does not match rows")
    if report.pass_snapshot_count != _status_count(report.rows, STATUS_PASS):
        raise ValueError("pass_snapshot_count does not match rows")
    if report.watch_snapshot_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_snapshot_count does not match rows")
    if report.blocked_snapshot_count != _status_count(report.rows, STATUS_BLOCKED):
        raise ValueError("blocked_snapshot_count does not match rows")
    expected_counts = (
        (
            report.spread_dislocation_snapshot_count,
            _spread_dislocation_count(report.rows),
        ),
        (report.spread_change_snapshot_count, _spread_change_count(report.rows)),
        (
            report.source_gap_snapshot_count,
            _reason_snapshot_count(report.rows, SOURCE_GAP_REASON),
        ),
        (
            report.liquidity_gap_snapshot_count,
            _reason_snapshot_count(report.rows, LIQUIDITY_GAP_REASON),
        ),
        (
            report.stale_snapshot_count,
            _reason_snapshot_count(report.rows, STALE_SNAPSHOT_REASON),
        ),
        (
            report.confidence_gap_snapshot_count,
            _reason_snapshot_count(report.rows, CONFIDENCE_GAP_REASON),
        ),
    )
    for actual, expected in expected_counts:
        if actual != expected:
            raise ValueError("reason snapshot count does not match rows")
    if report.digest_status != _report_status(report.rows):
        raise ValueError("digest_status does not match rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step does not match digest_status")
    if report.average_observed_spread_pct != _ratio(
        _decimal_sum(row.observed_spread_pct for row in report.rows),
        report.snapshot_count,
    ):
        raise ValueError("average_observed_spread_pct does not match rows")
    if report.average_spread_dislocation_abs != _ratio(
        _decimal_sum(row.spread_dislocation_abs for row in report.rows),
        report.snapshot_count,
    ):
        raise ValueError("average_spread_dislocation_abs does not match rows")
    if report.max_spread_dislocation_abs != max(
        (row.spread_dislocation_abs for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_spread_dislocation_abs does not match rows")
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
    snapshots: Iterable[MarketResearchCryptoBasisSpreadDislocationSnapshot],
) -> tuple[MarketResearchCryptoBasisSpreadDislocationSnapshot, ...]:
    snapshot_tuple = tuple(snapshots)
    seen_spread_ids: set[str] = set()
    for snapshot in snapshot_tuple:
        if type(snapshot) is not MarketResearchCryptoBasisSpreadDislocationSnapshot:
            raise ValueError(
                "snapshots must contain "
                "MarketResearchCryptoBasisSpreadDislocationSnapshot",
            )
        revalidated_snapshot = _revalidate_snapshot(snapshot)
        if revalidated_snapshot.spread_id in seen_spread_ids:
            raise ValueError("spread_id values must be unique")
        seen_spread_ids.add(revalidated_snapshot.spread_id)
        _require_hard_flags("snapshot", revalidated_snapshot)
    return snapshot_tuple


def _normalize_rows(
    rows: tuple[MarketResearchCryptoBasisSpreadDislocationDigestRow, ...],
) -> tuple[MarketResearchCryptoBasisSpreadDislocationDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized_rows: list[MarketResearchCryptoBasisSpreadDislocationDigestRow] = []
    for row in rows:
        if type(row) is not MarketResearchCryptoBasisSpreadDislocationDigestRow:
            raise ValueError(
                "rows must contain "
                "MarketResearchCryptoBasisSpreadDislocationDigestRow",
            )
        normalized_row = _revalidate_row(row)
        _require_hard_flags("row", normalized_row)
        normalized_rows.append(normalized_row)
    row_tuple = tuple(normalized_rows)
    canonical_rows = tuple(
        sorted(
            row_tuple,
            key=lambda row: (
                _row_sort_value(row),
                row.spread_id,
                row.condition_id,
            ),
        ),
    )
    if row_tuple != canonical_rows:
        raise ValueError("rows must be deterministic")
    return row_tuple


def _normalize_reason_code_counts(
    items: tuple[
        MarketResearchCryptoBasisSpreadDislocationDigestReasonCodeCount,
        ...,
    ],
) -> tuple[MarketResearchCryptoBasisSpreadDislocationDigestReasonCodeCount, ...]:
    if type(items) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    normalized_items: list[MarketResearchCryptoBasisSpreadDislocationDigestReasonCodeCount] = []
    for item in items:
        if type(item) is not MarketResearchCryptoBasisSpreadDislocationDigestReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count rows")
        normalized_item = _revalidate_reason_code_count(item)
        _require_hard_flags("reason code count", normalized_item)
        normalized_items.append(normalized_item)
    return tuple(normalized_items)


def _normalize_source_config_versions(
    value: tuple[tuple[str, str], ...],
) -> tuple[tuple[str, str], ...]:
    if type(value) is not tuple:
        raise ValueError("source_config_versions must be a tuple")
    pairs: list[tuple[str, str]] = []
    seen_spread_ids: set[str] = set()
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("source_config_versions must contain pairs")
        spread_id, source_config_version = item
        _require_public_string("spread_id", spread_id)
        _require_public_string("source_config_version", source_config_version)
        if spread_id in seen_spread_ids:
            raise ValueError("source_config_versions spread_id values must be unique")
        seen_spread_ids.add(spread_id)
        pairs.append((spread_id, source_config_version))
    pair_tuple = tuple(pairs)
    if pair_tuple != tuple(sorted(pair_tuple)):
        raise ValueError("source_config_versions must be deterministic")
    return pair_tuple


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


def _revalidate_report(
    report: MarketResearchCryptoBasisSpreadDislocationDigestReport,
) -> MarketResearchCryptoBasisSpreadDislocationDigestReport:
    return MarketResearchCryptoBasisSpreadDislocationDigestReport(
        **{
            field.name: getattr(report, field.name)
            for field in fields(MarketResearchCryptoBasisSpreadDislocationDigestReport)
        },
    )


def _revalidate_snapshot(
    snapshot: MarketResearchCryptoBasisSpreadDislocationSnapshot,
) -> MarketResearchCryptoBasisSpreadDislocationSnapshot:
    return MarketResearchCryptoBasisSpreadDislocationSnapshot(
        **{
            field.name: getattr(snapshot, field.name)
            for field in fields(MarketResearchCryptoBasisSpreadDislocationSnapshot)
        },
    )


def _revalidate_row(
    row: MarketResearchCryptoBasisSpreadDislocationDigestRow,
) -> MarketResearchCryptoBasisSpreadDislocationDigestRow:
    return MarketResearchCryptoBasisSpreadDislocationDigestRow(
        **{
            field.name: getattr(row, field.name)
            for field in fields(MarketResearchCryptoBasisSpreadDislocationDigestRow)
        },
    )


def _revalidate_reason_code_count(
    item: MarketResearchCryptoBasisSpreadDislocationDigestReasonCodeCount,
) -> MarketResearchCryptoBasisSpreadDislocationDigestReasonCodeCount:
    return MarketResearchCryptoBasisSpreadDislocationDigestReasonCodeCount(
        **{
            field.name: getattr(item, field.name)
            for field in fields(
                MarketResearchCryptoBasisSpreadDislocationDigestReasonCodeCount,
            )
        },
    )


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


def _require_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
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
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must be a canonical six-place Decimal")
    quantized = _quantize(value)
    if value != quantized or value.as_tuple().exponent != QUANT.as_tuple().exponent:
        raise ValueError(f"{field_name} must be a canonical six-place Decimal")
    return value


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime or value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} must have a non-None UTC offset")
    return value.astimezone(UTC)


def _require_payload_datetimes_utc(value: Any) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _require_payload_datetimes_utc(getattr(value, field.name))
        return
    if isinstance(value, datetime):
        if type(value) is not datetime or value.tzinfo is not UTC:
            raise ValueError("payload datetimes must be UTC")
        return
    if isinstance(value, tuple):
        for item in value:
            _require_payload_datetimes_utc(item)
        return
    if isinstance(value, dict):
        for item in value.values():
            _require_payload_datetimes_utc(item)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    return _quantize(
        Decimal(delta.days * 86400 + delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND),
    )


def _ratio_abs(value: Decimal) -> Decimal:
    return _quantize(abs(value))


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _decimal_sum(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("values must be Decimals")
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
    if isinstance(value, Decimal):
        raise ValueError("JSON Decimal value must be exactly Decimal")
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, int) and not isinstance(value, bool):
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, tuple):
        return tuple(_json_ready(item) for item in value)
    if isinstance(value, list):
        return tuple(_json_ready(item) for item in value)
    if isinstance(value, dict):
        return {str(name): _json_ready(item) for name, item in value.items()}
    if value is None or isinstance(value, (str, bool)):
        return value
    raise ValueError("JSON serializable value expected")


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({name: _freeze(item) for name, item in value.items()})
    if isinstance(value, tuple):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value
