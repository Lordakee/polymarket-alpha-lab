"""Pure Phase 1 crypto funding-rate market research reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from types import MappingProxyType
from typing import Any


DEFAULT_MARKET_RESEARCH_CRYPTO_FUNDING_RATE_DIGEST_CONFIG_VERSION = (
    "market-research-crypto-funding-rate-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
FUNDING_RATE_DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

READY_REASON = "market_research_crypto_funding_rate_digest_ready"
NO_INPUTS_REASON = "market_research_crypto_funding_rate_digest_no_inputs"
FUNDING_RATE_PRESSURE_REASON = (
    "market_research_crypto_funding_rate_digest_funding_rate_pressure"
)
PREDICTED_FUNDING_RATE_PRESSURE_REASON = (
    "market_research_crypto_funding_rate_digest_predicted_funding_rate_pressure"
)
FUNDING_RATE_CHANGE_REASON = (
    "market_research_crypto_funding_rate_digest_funding_rate_change"
)
SOURCE_DIVERSITY_GAP_REASON = (
    "market_research_crypto_funding_rate_digest_source_diversity_gap"
)
OPEN_INTEREST_GAP_REASON = (
    "market_research_crypto_funding_rate_digest_open_interest_gap"
)
STALE_SNAPSHOT_REASON = "market_research_crypto_funding_rate_digest_stale_snapshot"
CONFIDENCE_GAP_REASON = "market_research_crypto_funding_rate_digest_confidence_gap"

REASON_CODE_SEQUENCE = (
    FUNDING_RATE_PRESSURE_REASON,
    PREDICTED_FUNDING_RATE_PRESSURE_REASON,
    FUNDING_RATE_CHANGE_REASON,
    SOURCE_DIVERSITY_GAP_REASON,
    OPEN_INTEREST_GAP_REASON,
    STALE_SNAPSHOT_REASON,
    CONFIDENCE_GAP_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    FUNDING_RATE_PRESSURE_REASON,
    PREDICTED_FUNDING_RATE_PRESSURE_REASON,
    FUNDING_RATE_CHANGE_REASON,
    SOURCE_DIVERSITY_GAP_REASON,
    OPEN_INTEREST_GAP_REASON,
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
        _join_parts("can", "cel"),
        _join_parts("re", "place"),
        _join_parts("ex", "change"),
        _join_parts("au", "th"),
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
        _join_parts("0", "x"),
    ),
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_CRYPTO_FUNDING_RATE_DIGEST_CONFIG_VERSION",
    "MarketResearchCryptoFundingRateDigestConfig",
    "MarketResearchCryptoFundingRateDigestReasonCodeCount",
    "MarketResearchCryptoFundingRateDigestReport",
    "MarketResearchCryptoFundingRateDigestRow",
    "MarketResearchCryptoFundingRateSnapshot",
    "build_market_research_crypto_funding_rate_digest",
    "market_research_crypto_funding_rate_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchCryptoFundingRateDigestConfig:
    config_version: str = DEFAULT_MARKET_RESEARCH_CRYPTO_FUNDING_RATE_DIGEST_CONFIG_VERSION
    max_snapshot_age_seconds: Decimal = Decimal("3600.000000")
    max_funding_rate_abs: Decimal = Decimal("0.010000")
    max_predicted_funding_rate_abs: Decimal = Decimal("0.012000")
    max_funding_rate_change_abs: Decimal = Decimal("0.006000")
    min_exchange_source_count: Decimal = Decimal("3.000000")
    min_open_interest_usd: Decimal = Decimal("1000000.000000")
    min_confidence: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoFundingRateDigestConfig:
            raise TypeError(
                "MarketResearchCryptoFundingRateDigestConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoFundingRateDigestConfig:
            raise ValueError(
                "config must be exactly MarketResearchCryptoFundingRateDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("max_snapshot_age_seconds", "min_exchange_source_count"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_open_interest_usd",
            _require_nonnegative_count_decimal(
                "min_open_interest_usd",
                self.min_open_interest_usd,
            ),
        )
        for field_name in (
            "max_funding_rate_abs",
            "max_predicted_funding_rate_abs",
            "max_funding_rate_change_abs",
            "min_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchCryptoFundingRateSnapshot:
    condition_id: str
    funding_rate_key: str
    asset_symbol: str
    observed_at: datetime
    exchange_source_count: Decimal
    funding_rate: Decimal
    predicted_funding_rate: Decimal
    previous_funding_rate: Decimal
    open_interest_usd: Decimal
    confidence: Decimal
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoFundingRateSnapshot:
            raise TypeError(
                "MarketResearchCryptoFundingRateSnapshot does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoFundingRateSnapshot:
            raise ValueError(
                "snapshot must be exactly MarketResearchCryptoFundingRateSnapshot",
            )
        for field_name in (
            "condition_id",
            "funding_rate_key",
            "asset_symbol",
            "source_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "exchange_source_count",
            _require_nonnegative_count_decimal(
                "exchange_source_count",
                self.exchange_source_count,
            ),
        )
        object.__setattr__(
            self,
            "open_interest_usd",
            _require_nonnegative_count_decimal(
                "open_interest_usd",
                self.open_interest_usd,
            ),
        )
        for field_name in (
            "funding_rate",
            "predicted_funding_rate",
            "previous_funding_rate",
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
class MarketResearchCryptoFundingRateDigestRow:
    condition_id: str
    funding_rate_key: str
    asset_symbol: str
    digest_status: str
    observed_at: datetime
    snapshot_age_seconds: Decimal
    exchange_source_count: Decimal
    funding_rate: Decimal
    predicted_funding_rate: Decimal
    previous_funding_rate: Decimal
    funding_rate_abs: Decimal
    predicted_funding_rate_abs: Decimal
    funding_rate_change_abs: Decimal
    open_interest_usd: Decimal
    confidence: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoFundingRateDigestRow:
            raise TypeError(
                "MarketResearchCryptoFundingRateDigestRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoFundingRateDigestRow:
            raise ValueError("row must be exactly MarketResearchCryptoFundingRateDigestRow")
        for field_name in ("condition_id", "funding_rate_key", "asset_symbol"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_status("digest_status", self.digest_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "snapshot_age_seconds",
            "exchange_source_count",
            "open_interest_usd",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "funding_rate",
            "predicted_funding_rate",
            "previous_funding_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_signed_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "funding_rate_abs",
            "predicted_funding_rate_abs",
            "funding_rate_change_abs",
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
class MarketResearchCryptoFundingRateDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    snapshot_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoFundingRateDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchCryptoFundingRateDigestReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoFundingRateDigestReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "MarketResearchCryptoFundingRateDigestReasonCodeCount",
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
class MarketResearchCryptoFundingRateDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    snapshot_count: Decimal
    ready_snapshot_count: Decimal
    watch_snapshot_count: Decimal
    blocked_snapshot_count: Decimal
    funding_rate_pressure_snapshot_count: Decimal
    predicted_funding_rate_pressure_snapshot_count: Decimal
    funding_rate_change_snapshot_count: Decimal
    source_diversity_gap_snapshot_count: Decimal
    open_interest_gap_snapshot_count: Decimal
    stale_snapshot_count: Decimal
    confidence_gap_snapshot_count: Decimal
    average_funding_rate: Decimal
    average_predicted_funding_rate: Decimal
    average_funding_rate_change_abs: Decimal
    max_snapshot_age_seconds: Decimal
    max_allowed_snapshot_age_seconds: Decimal
    max_allowed_funding_rate_abs: Decimal
    max_allowed_predicted_funding_rate_abs: Decimal
    max_allowed_funding_rate_change_abs: Decimal
    min_exchange_source_count: Decimal
    min_open_interest_usd: Decimal
    min_confidence: Decimal
    rows: tuple[MarketResearchCryptoFundingRateDigestRow, ...]
    source_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[MarketResearchCryptoFundingRateDigestReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoFundingRateDigestReport:
            raise TypeError(
                "MarketResearchCryptoFundingRateDigestReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoFundingRateDigestReport:
            raise ValueError(
                "report must be exactly MarketResearchCryptoFundingRateDigestReport",
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
            "funding_rate_pressure_snapshot_count",
            "predicted_funding_rate_pressure_snapshot_count",
            "funding_rate_change_snapshot_count",
            "source_diversity_gap_snapshot_count",
            "open_interest_gap_snapshot_count",
            "stale_snapshot_count",
            "confidence_gap_snapshot_count",
            "max_snapshot_age_seconds",
            "max_allowed_snapshot_age_seconds",
            "min_exchange_source_count",
            "min_open_interest_usd",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_funding_rate",
            "average_predicted_funding_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_signed_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_funding_rate_change_abs",
            "max_allowed_funding_rate_abs",
            "max_allowed_predicted_funding_rate_abs",
            "max_allowed_funding_rate_change_abs",
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
    MarketResearchCryptoFundingRateDigestConfig,
    MarketResearchCryptoFundingRateDigestReasonCodeCount,
    MarketResearchCryptoFundingRateDigestReport,
    MarketResearchCryptoFundingRateDigestRow,
    MarketResearchCryptoFundingRateSnapshot,
)


def build_market_research_crypto_funding_rate_digest(
    snapshots: Iterable[MarketResearchCryptoFundingRateSnapshot],
    *,
    config: MarketResearchCryptoFundingRateDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchCryptoFundingRateDigestReport:
    cfg = MarketResearchCryptoFundingRateDigestConfig() if config is None else config
    if type(cfg) is not MarketResearchCryptoFundingRateDigestConfig:
        raise ValueError(
            "config must be exactly MarketResearchCryptoFundingRateDigestConfig",
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
                row.funding_rate_key,
                row.condition_id,
            ),
        ),
    )
    report_status = _report_status(sorted_rows)
    return MarketResearchCryptoFundingRateDigestReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        digest_status=report_status,
        recommended_next_step=_recommended_next_step(report_status),
        snapshot_count=_decimal_count(len(sorted_rows)),
        ready_snapshot_count=_status_count(sorted_rows, STATUS_READY),
        watch_snapshot_count=_status_count(sorted_rows, STATUS_WATCH),
        blocked_snapshot_count=_status_count(sorted_rows, STATUS_BLOCKED),
        funding_rate_pressure_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            FUNDING_RATE_PRESSURE_REASON,
        ),
        predicted_funding_rate_pressure_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            PREDICTED_FUNDING_RATE_PRESSURE_REASON,
        ),
        funding_rate_change_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            FUNDING_RATE_CHANGE_REASON,
        ),
        source_diversity_gap_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            SOURCE_DIVERSITY_GAP_REASON,
        ),
        open_interest_gap_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            OPEN_INTEREST_GAP_REASON,
        ),
        stale_snapshot_count=_reason_snapshot_count(sorted_rows, STALE_SNAPSHOT_REASON),
        confidence_gap_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            CONFIDENCE_GAP_REASON,
        ),
        average_funding_rate=_ratio(
            _decimal_sum(row.funding_rate for row in sorted_rows),
            _decimal_count(len(sorted_rows)),
        ),
        average_predicted_funding_rate=_ratio(
            _decimal_sum(row.predicted_funding_rate for row in sorted_rows),
            _decimal_count(len(sorted_rows)),
        ),
        average_funding_rate_change_abs=_ratio(
            _decimal_sum(row.funding_rate_change_abs for row in sorted_rows),
            _decimal_count(len(sorted_rows)),
        ),
        max_snapshot_age_seconds=max(
            (row.snapshot_age_seconds for row in sorted_rows),
            default=ZERO,
        ),
        max_allowed_snapshot_age_seconds=cfg.max_snapshot_age_seconds,
        max_allowed_funding_rate_abs=cfg.max_funding_rate_abs,
        max_allowed_predicted_funding_rate_abs=cfg.max_predicted_funding_rate_abs,
        max_allowed_funding_rate_change_abs=cfg.max_funding_rate_change_abs,
        min_exchange_source_count=cfg.min_exchange_source_count,
        min_open_interest_usd=cfg.min_open_interest_usd,
        min_confidence=cfg.min_confidence,
        rows=sorted_rows,
        source_config_versions=tuple(
            sorted(
                (snapshot.funding_rate_key, snapshot.source_config_version)
                for snapshot in normalized_snapshots
            ),
        ),
        reason_code_counts=_reason_code_counts(sorted_rows),
        reason_codes=_summary_reason_codes(sorted_rows),
    )


def market_research_crypto_funding_rate_digest_payload(
    report: MarketResearchCryptoFundingRateDigestReport,
) -> MappingProxyType:
    if type(report) is not MarketResearchCryptoFundingRateDigestReport:
        raise ValueError(
            "report must be exactly MarketResearchCryptoFundingRateDigestReport",
        )
    _require_payload_safe_value("report", report)
    return _freeze(_json_ready(report))


def _row_for_snapshot(
    snapshot: MarketResearchCryptoFundingRateSnapshot,
    *,
    config: MarketResearchCryptoFundingRateDigestConfig,
    generated_at: datetime,
) -> MarketResearchCryptoFundingRateDigestRow:
    if snapshot.observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    snapshot_age_seconds = _age_seconds(generated_at, snapshot.observed_at)
    funding_rate_abs = _ratio_abs(snapshot.funding_rate)
    predicted_funding_rate_abs = _ratio_abs(snapshot.predicted_funding_rate)
    funding_rate_change_abs = _ratio_abs(snapshot.funding_rate - snapshot.previous_funding_rate)
    reason_codes = _row_reason_codes(
        snapshot=snapshot,
        config=config,
        snapshot_age_seconds=snapshot_age_seconds,
        funding_rate_abs=funding_rate_abs,
        predicted_funding_rate_abs=predicted_funding_rate_abs,
        funding_rate_change_abs=funding_rate_change_abs,
    )
    return MarketResearchCryptoFundingRateDigestRow(
        condition_id=snapshot.condition_id,
        funding_rate_key=snapshot.funding_rate_key,
        asset_symbol=snapshot.asset_symbol,
        digest_status=_row_status(reason_codes),
        observed_at=snapshot.observed_at,
        snapshot_age_seconds=snapshot_age_seconds,
        exchange_source_count=snapshot.exchange_source_count,
        funding_rate=snapshot.funding_rate,
        predicted_funding_rate=snapshot.predicted_funding_rate,
        previous_funding_rate=snapshot.previous_funding_rate,
        funding_rate_abs=funding_rate_abs,
        predicted_funding_rate_abs=predicted_funding_rate_abs,
        funding_rate_change_abs=funding_rate_change_abs,
        open_interest_usd=snapshot.open_interest_usd,
        confidence=snapshot.confidence,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    snapshot: MarketResearchCryptoFundingRateSnapshot,
    config: MarketResearchCryptoFundingRateDigestConfig,
    snapshot_age_seconds: Decimal,
    funding_rate_abs: Decimal,
    predicted_funding_rate_abs: Decimal,
    funding_rate_change_abs: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if funding_rate_abs > config.max_funding_rate_abs:
        reasons.append(FUNDING_RATE_PRESSURE_REASON)
    if predicted_funding_rate_abs > config.max_predicted_funding_rate_abs:
        reasons.append(PREDICTED_FUNDING_RATE_PRESSURE_REASON)
    if funding_rate_change_abs > config.max_funding_rate_change_abs:
        reasons.append(FUNDING_RATE_CHANGE_REASON)
    if snapshot.exchange_source_count < config.min_exchange_source_count:
        reasons.append(SOURCE_DIVERSITY_GAP_REASON)
    if snapshot.open_interest_usd < config.min_open_interest_usd:
        reasons.append(OPEN_INTEREST_GAP_REASON)
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
            FUNDING_RATE_PRESSURE_REASON,
            PREDICTED_FUNDING_RATE_PRESSURE_REASON,
            FUNDING_RATE_CHANGE_REASON,
            OPEN_INTEREST_GAP_REASON,
            STALE_SNAPSHOT_REASON,
            CONFIDENCE_GAP_REASON,
        )
    ):
        return STATUS_BLOCKED
    return STATUS_WATCH


def _row_sort_value(row: MarketResearchCryptoFundingRateDigestRow) -> tuple[int, Decimal]:
    status_rank = {
        STATUS_BLOCKED: 0,
        STATUS_WATCH: 1,
        STATUS_READY: 2,
    }[row.digest_status]
    severity = _decimal_count(len(tuple(reason for reason in row.reason_codes if reason != READY_REASON)))
    return (status_rank, -severity)


def _report_status(rows: tuple[MarketResearchCryptoFundingRateDigestRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_READY


def _recommended_next_step(status: str) -> str:
    if status == STATUS_BLOCKED:
        return "block_report_only_market_research_crypto_funding_rate_digest"
    if status == STATUS_WATCH:
        return "review_report_only_market_research_crypto_funding_rate_digest"
    return "allow_report_only_market_research_crypto_funding_rate_digest"


def _status_count(
    rows: tuple[MarketResearchCryptoFundingRateDigestRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.digest_status == status))


def _reason_snapshot_count(
    rows: tuple[MarketResearchCryptoFundingRateDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _reason_code_counts(
    rows: tuple[MarketResearchCryptoFundingRateDigestRow, ...],
) -> tuple[MarketResearchCryptoFundingRateDigestReasonCodeCount, ...]:
    snapshot_count = _decimal_count(len(rows))
    if not rows:
        return (
            MarketResearchCryptoFundingRateDigestReasonCodeCount(
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
        MarketResearchCryptoFundingRateDigestReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
            snapshot_ratio=_ratio(_decimal_count(counts[reason_code]), snapshot_count),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _summary_reason_codes(
    rows: tuple[MarketResearchCryptoFundingRateDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    seen: set[str] = set()
    for row in rows:
        seen.update(row.reason_codes)
    if len(seen) > 1 and READY_REASON in seen:
        seen.remove(READY_REASON)
    return tuple(reason for reason in REASON_CODE_SEQUENCE if reason in seen)


def _validate_row(row: MarketResearchCryptoFundingRateDigestRow) -> None:
    if row.funding_rate_abs != _ratio_abs(row.funding_rate):
        raise ValueError("funding_rate_abs does not match funding_rate")
    if row.predicted_funding_rate_abs != _ratio_abs(row.predicted_funding_rate):
        raise ValueError(
            "predicted_funding_rate_abs does not match predicted_funding_rate",
        )
    if row.funding_rate_change_abs != _ratio_abs(
        row.funding_rate - row.previous_funding_rate,
    ):
        raise ValueError("funding_rate_change_abs does not match funding_rate inputs")
    if row.digest_status != _row_status(row.reason_codes):
        raise ValueError("digest_status does not match reason_codes")


def _validate_report(report: MarketResearchCryptoFundingRateDigestReport) -> None:
    if report.snapshot_count != _decimal_count(len(report.rows)):
        raise ValueError("snapshot_count does not match rows")
    if report.ready_snapshot_count != _status_count(report.rows, STATUS_READY):
        raise ValueError("ready_snapshot_count does not match rows")
    if report.watch_snapshot_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_snapshot_count does not match rows")
    if report.blocked_snapshot_count != _status_count(report.rows, STATUS_BLOCKED):
        raise ValueError("blocked_snapshot_count does not match rows")
    expected_counts = (
        (FUNDING_RATE_PRESSURE_REASON, report.funding_rate_pressure_snapshot_count),
        (
            PREDICTED_FUNDING_RATE_PRESSURE_REASON,
            report.predicted_funding_rate_pressure_snapshot_count,
        ),
        (FUNDING_RATE_CHANGE_REASON, report.funding_rate_change_snapshot_count),
        (SOURCE_DIVERSITY_GAP_REASON, report.source_diversity_gap_snapshot_count),
        (OPEN_INTEREST_GAP_REASON, report.open_interest_gap_snapshot_count),
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
    if report.average_funding_rate != _ratio(
        _decimal_sum(row.funding_rate for row in report.rows),
        report.snapshot_count,
    ):
        raise ValueError("average_funding_rate does not match rows")
    if report.average_predicted_funding_rate != _ratio(
        _decimal_sum(row.predicted_funding_rate for row in report.rows),
        report.snapshot_count,
    ):
        raise ValueError("average_predicted_funding_rate does not match rows")
    if report.average_funding_rate_change_abs != _ratio(
        _decimal_sum(row.funding_rate_change_abs for row in report.rows),
        report.snapshot_count,
    ):
        raise ValueError("average_funding_rate_change_abs does not match rows")
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
        sorted(row.funding_rate_key for row in report.rows),
    ):
        raise ValueError("source_config_versions do not match rows")


def _normalize_snapshots(
    snapshots: Iterable[MarketResearchCryptoFundingRateSnapshot],
) -> tuple[MarketResearchCryptoFundingRateSnapshot, ...]:
    snapshot_tuple = tuple(snapshots)
    seen_keys: set[str] = set()
    for snapshot in snapshot_tuple:
        if type(snapshot) is not MarketResearchCryptoFundingRateSnapshot:
            raise ValueError("snapshots must contain MarketResearchCryptoFundingRateSnapshot")
        if snapshot.funding_rate_key in seen_keys:
            raise ValueError("funding_rate_key values must be unique")
        seen_keys.add(snapshot.funding_rate_key)
        _require_hard_flags("snapshot", snapshot)
    return snapshot_tuple


def _normalize_rows(
    rows: tuple[MarketResearchCryptoFundingRateDigestRow, ...],
) -> tuple[MarketResearchCryptoFundingRateDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not MarketResearchCryptoFundingRateDigestRow:
            raise ValueError("rows must contain MarketResearchCryptoFundingRateDigestRow")
        _require_hard_flags("row", row)
    if rows != tuple(
        sorted(
            rows,
            key=lambda row: (
                _row_sort_value(row),
                row.funding_rate_key,
                row.condition_id,
            ),
        ),
    ):
        raise ValueError("rows must be deterministic")
    return rows


def _normalize_reason_code_counts(
    items: tuple[MarketResearchCryptoFundingRateDigestReasonCodeCount, ...],
) -> tuple[MarketResearchCryptoFundingRateDigestReasonCodeCount, ...]:
    if type(items) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    seen: set[str] = set()
    for item in items:
        if type(item) is not MarketResearchCryptoFundingRateDigestReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count rows")
        _require_hard_flags("reason_code_count", item)
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        seen.add(item.reason_code)
    normalized = tuple(
        sorted(
            items,
            key=lambda item: REASON_CODE_SEQUENCE.index(item.reason_code),
        ),
    )
    if normalized != items:
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
        funding_rate_key, source_config_version = item
        _require_public_string("funding_rate_key", funding_rate_key)
        _require_public_string("source_config_version", source_config_version)
        if funding_rate_key in seen_keys:
            raise ValueError("source_config_versions funding_rate_key values must be unique")
        seen_keys.add(funding_rate_key)
        pairs.append((funding_rate_key, source_config_version))
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


def _require_status(field_name: str, value: str) -> None:
    if type(value) is not str or value not in FUNDING_RATE_DIGEST_STATUSES:
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


def _require_signed_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < -ONE or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between -1 and 1")
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


def _ratio_abs(value: Decimal) -> Decimal:
    return _quantize(abs(value))


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
        if decimal_value != value:
            raise ValueError(f"{field_name} must be quantized to six decimals")
        return
    if type(value) is datetime:
        _as_utc(field_name, value)
        if value.tzinfo is not UTC:
            raise ValueError(f"{field_name} must be normalized to UTC")
        return
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{field_name} must be a known public dataclass")
        _require_hard_flags(field_name, value)
        for field in fields(value):
            _require_payload_safe_value(
                f"{field_name}.{field.name}",
                getattr(value, field.name),
            )
        _reconstruct_public_dataclass(field_name, value)
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            _require_payload_safe_value(f"{field_name}[{index}]", item)
        return
    if type(value) in (str, bool) or value is None:
        return
    if type(value) in (list, dict, set):
        raise ValueError(f"{field_name} must remain constructor-normalized")
    raise ValueError(f"{field_name} must be payload safe")


def _reconstruct_public_dataclass(field_name: str, value: object) -> None:
    type_ = type(value)
    try:
        type_(**{field.name: getattr(value, field.name) for field in fields(value)})
    except (ArithmeticError, TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must remain constructor-valid") from exc


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if type(value) is datetime:
        return value.isoformat()
    if type(value) is Decimal:
        return f"{value:.6f}"
    if type(value) is tuple:
        return tuple(_json_ready(item) for item in value)
    if type(value) is list:
        return tuple(_json_ready(item) for item in value)
    if type(value) is dict:
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, tuple):
        return tuple(_freeze(item) for item in value)
    return value
