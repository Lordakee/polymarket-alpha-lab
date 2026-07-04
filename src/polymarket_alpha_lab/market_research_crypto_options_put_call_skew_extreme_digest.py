"""Pure Phase 1 crypto options put-call skew extreme reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from types import MappingProxyType
from typing import Any


DEFAULT_MARKET_RESEARCH_CRYPTO_OPTIONS_PUT_CALL_SKEW_EXTREME_DIGEST_CONFIG_VERSION = (
    "market-research-crypto-options-put-call-skew-extreme-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
PUT_CALL_SKEW_EXTREME_DIGEST_STATUSES = (
    STATUS_READY,
    STATUS_WATCH,
    STATUS_BLOCKED,
)

READY_REASON = (
    "market_research_crypto_options_put_call_skew_extreme_digest_ready"
)
NO_INPUTS_REASON = (
    "market_research_crypto_options_put_call_skew_extreme_digest_no_inputs"
)
EXTREME_SKEW_REASON = (
    "market_research_crypto_options_put_call_skew_extreme_digest_extreme_skew"
)
PUT_IV_PREMIUM_REASON = (
    "market_research_crypto_options_put_call_skew_extreme_digest_put_iv_premium"
)
CALL_IV_PREMIUM_REASON = (
    "market_research_crypto_options_put_call_skew_extreme_digest_call_iv_premium"
)
PUT_CALL_VOLUME_IMBALANCE_REASON = (
    "market_research_crypto_options_put_call_skew_extreme_digest_"
    "put_call_volume_imbalance"
)
REFERENCE_GAP_REASON = (
    "market_research_crypto_options_put_call_skew_extreme_digest_reference_gap"
)
OPEN_INTEREST_GAP_REASON = (
    "market_research_crypto_options_put_call_skew_extreme_digest_open_interest_gap"
)
VOLUME_GAP_REASON = (
    "market_research_crypto_options_put_call_skew_extreme_digest_volume_gap"
)
STALE_SNAPSHOT_REASON = (
    "market_research_crypto_options_put_call_skew_extreme_digest_stale_snapshot"
)
CONFIDENCE_GAP_REASON = (
    "market_research_crypto_options_put_call_skew_extreme_digest_confidence_gap"
)

REASON_CODE_SEQUENCE = (
    EXTREME_SKEW_REASON,
    PUT_IV_PREMIUM_REASON,
    CALL_IV_PREMIUM_REASON,
    PUT_CALL_VOLUME_IMBALANCE_REASON,
    REFERENCE_GAP_REASON,
    OPEN_INTEREST_GAP_REASON,
    VOLUME_GAP_REASON,
    STALE_SNAPSHOT_REASON,
    CONFIDENCE_GAP_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    EXTREME_SKEW_REASON,
    PUT_IV_PREMIUM_REASON,
    CALL_IV_PREMIUM_REASON,
    PUT_CALL_VOLUME_IMBALANCE_REASON,
    REFERENCE_GAP_REASON,
    OPEN_INTEREST_GAP_REASON,
    VOLUME_GAP_REASON,
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
        _join_parts("au", "th"),
        _join_parts("ke", "y"),
        _join_parts("to", "ken"),
        _join_parts("sec", "ret"),
        _join_parts("pri", "vate"),
        _join_parts("acc", "ount"),
        _join_parts("can", "cel"),
        _join_parts("re", "place"),
        _join_parts("ex", "change"),
        _join_parts("tra", "de"),
        _join_parts("0", "x"),
    ),
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_CRYPTO_OPTIONS_PUT_CALL_SKEW_EXTREME_DIGEST_CONFIG_VERSION",
    "MarketResearchCryptoOptionsPutCallSkewExtremeDigestConfig",
    "MarketResearchCryptoOptionsPutCallSkewExtremeDigestReasonCodeCount",
    "MarketResearchCryptoOptionsPutCallSkewExtremeDigestReport",
    "MarketResearchCryptoOptionsPutCallSkewExtremeDigestRow",
    "MarketResearchCryptoOptionsPutCallSkewExtremeSnapshot",
    "build_market_research_crypto_options_put_call_skew_extreme_digest",
    "market_research_crypto_options_put_call_skew_extreme_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchCryptoOptionsPutCallSkewExtremeDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_CRYPTO_OPTIONS_PUT_CALL_SKEW_EXTREME_DIGEST_CONFIG_VERSION
    )
    max_snapshot_age_seconds: Decimal = Decimal("1800.000000")
    min_reference_count: Decimal = Decimal("2.000000")
    min_open_interest_usd: Decimal = Decimal("1000000.000000")
    min_volume_usd: Decimal = Decimal("250000.000000")
    max_put_call_skew_abs: Decimal = Decimal("0.250000")
    max_put_iv_premium_over_call: Decimal = Decimal("0.150000")
    max_call_iv_premium_over_put: Decimal = Decimal("0.150000")
    max_put_call_volume_ratio: Decimal = Decimal("2.500000")
    min_confidence: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoOptionsPutCallSkewExtremeDigestConfig:
            raise TypeError(
                "MarketResearchCryptoOptionsPutCallSkewExtremeDigestConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoOptionsPutCallSkewExtremeDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchCryptoOptionsPutCallSkewExtremeDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "max_snapshot_age_seconds",
            "min_reference_count",
            "max_put_call_volume_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("min_open_interest_usd", "min_volume_usd"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_put_call_skew_abs",
            "max_put_iv_premium_over_call",
            "max_call_iv_premium_over_put",
            "min_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchCryptoOptionsPutCallSkewExtremeSnapshot:
    condition_id: str
    signal_id: str
    asset_symbol: str
    expiry_bucket: str
    observed_at: datetime
    reference_count: Decimal
    open_interest_usd: Decimal
    volume_usd: Decimal
    put_call_skew: Decimal
    put_iv_25_delta: Decimal
    call_iv_25_delta: Decimal
    put_call_volume_ratio: Decimal
    confidence: Decimal
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoOptionsPutCallSkewExtremeSnapshot:
            raise TypeError(
                "MarketResearchCryptoOptionsPutCallSkewExtremeSnapshot "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoOptionsPutCallSkewExtremeSnapshot:
            raise ValueError(
                "snapshot must be exactly "
                "MarketResearchCryptoOptionsPutCallSkewExtremeSnapshot",
            )
        for field_name in (
            "condition_id",
            "signal_id",
            "asset_symbol",
            "expiry_bucket",
            "source_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("reference_count", "open_interest_usd", "volume_usd"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "put_call_skew",
            _require_signed_ratio_decimal("put_call_skew", self.put_call_skew),
        )
        for field_name in (
            "put_iv_25_delta",
            "call_iv_25_delta",
            "confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "put_call_volume_ratio",
            _require_nonnegative_count_decimal(
                "put_call_volume_ratio",
                self.put_call_volume_ratio,
            ),
        )
        _require_hard_flags("snapshot", self)


@dataclass(frozen=True)
class MarketResearchCryptoOptionsPutCallSkewExtremeDigestRow:
    condition_id: str
    signal_id: str
    asset_symbol: str
    expiry_bucket: str
    digest_status: str
    observed_at: datetime
    snapshot_age_seconds: Decimal
    reference_count: Decimal
    open_interest_usd: Decimal
    volume_usd: Decimal
    put_call_skew: Decimal
    put_iv_25_delta: Decimal
    call_iv_25_delta: Decimal
    put_call_skew_abs: Decimal
    put_iv_premium_over_call: Decimal
    call_iv_premium_over_put: Decimal
    put_call_volume_ratio: Decimal
    confidence: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoOptionsPutCallSkewExtremeDigestRow:
            raise TypeError(
                "MarketResearchCryptoOptionsPutCallSkewExtremeDigestRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoOptionsPutCallSkewExtremeDigestRow:
            raise ValueError(
                "row must be exactly "
                "MarketResearchCryptoOptionsPutCallSkewExtremeDigestRow",
            )
        for field_name in (
            "condition_id",
            "signal_id",
            "asset_symbol",
            "expiry_bucket",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_status("digest_status", self.digest_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "snapshot_age_seconds",
            "reference_count",
            "open_interest_usd",
            "volume_usd",
            "put_call_volume_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "put_call_skew",
            _require_signed_ratio_decimal("put_call_skew", self.put_call_skew),
        )
        for field_name in (
            "put_iv_25_delta",
            "call_iv_25_delta",
            "put_call_skew_abs",
            "put_iv_premium_over_call",
            "call_iv_premium_over_put",
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
class MarketResearchCryptoOptionsPutCallSkewExtremeDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    snapshot_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoOptionsPutCallSkewExtremeDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchCryptoOptionsPutCallSkewExtremeDigestReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoOptionsPutCallSkewExtremeDigestReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "MarketResearchCryptoOptionsPutCallSkewExtremeDigestReasonCodeCount",
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
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchCryptoOptionsPutCallSkewExtremeDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    snapshot_count: Decimal
    ready_snapshot_count: Decimal
    watch_snapshot_count: Decimal
    blocked_snapshot_count: Decimal
    extreme_skew_snapshot_count: Decimal
    put_iv_premium_snapshot_count: Decimal
    call_iv_premium_snapshot_count: Decimal
    put_call_volume_imbalance_snapshot_count: Decimal
    reference_gap_snapshot_count: Decimal
    open_interest_gap_snapshot_count: Decimal
    volume_gap_snapshot_count: Decimal
    stale_snapshot_count: Decimal
    confidence_gap_snapshot_count: Decimal
    average_put_call_skew: Decimal
    average_put_iv_25_delta: Decimal
    average_call_iv_25_delta: Decimal
    average_put_call_volume_ratio: Decimal
    max_snapshot_age_seconds: Decimal
    max_allowed_snapshot_age_seconds: Decimal
    min_reference_count: Decimal
    min_open_interest_usd: Decimal
    min_volume_usd: Decimal
    max_allowed_put_call_skew_abs: Decimal
    max_allowed_put_iv_premium_over_call: Decimal
    max_allowed_call_iv_premium_over_put: Decimal
    max_allowed_put_call_volume_ratio: Decimal
    min_confidence: Decimal
    ready_snapshot_ratio: Decimal
    rows: tuple[MarketResearchCryptoOptionsPutCallSkewExtremeDigestRow, ...]
    source_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchCryptoOptionsPutCallSkewExtremeDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoOptionsPutCallSkewExtremeDigestReport:
            raise TypeError(
                "MarketResearchCryptoOptionsPutCallSkewExtremeDigestReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoOptionsPutCallSkewExtremeDigestReport:
            raise ValueError(
                "report must be exactly "
                "MarketResearchCryptoOptionsPutCallSkewExtremeDigestReport",
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
            "extreme_skew_snapshot_count",
            "put_iv_premium_snapshot_count",
            "call_iv_premium_snapshot_count",
            "put_call_volume_imbalance_snapshot_count",
            "reference_gap_snapshot_count",
            "open_interest_gap_snapshot_count",
            "volume_gap_snapshot_count",
            "stale_snapshot_count",
            "confidence_gap_snapshot_count",
            "max_snapshot_age_seconds",
            "max_allowed_snapshot_age_seconds",
            "min_reference_count",
            "min_open_interest_usd",
            "min_volume_usd",
            "max_allowed_put_call_volume_ratio",
            "average_put_call_volume_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_put_call_skew",
            _require_signed_ratio_decimal(
                "average_put_call_skew",
                self.average_put_call_skew,
            ),
        )
        for field_name in (
            "average_put_iv_25_delta",
            "average_call_iv_25_delta",
            "max_allowed_put_call_skew_abs",
            "max_allowed_put_iv_premium_over_call",
            "max_allowed_call_iv_premium_over_put",
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


def build_market_research_crypto_options_put_call_skew_extreme_digest(
    snapshots: Iterable[MarketResearchCryptoOptionsPutCallSkewExtremeSnapshot],
    *,
    config: MarketResearchCryptoOptionsPutCallSkewExtremeDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchCryptoOptionsPutCallSkewExtremeDigestReport:
    cfg = config or MarketResearchCryptoOptionsPutCallSkewExtremeDigestConfig()
    if type(cfg) is not MarketResearchCryptoOptionsPutCallSkewExtremeDigestConfig:
        raise ValueError(
            "config must be exactly "
            "MarketResearchCryptoOptionsPutCallSkewExtremeDigestConfig",
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
                row.signal_id,
                row.condition_id,
            ),
        ),
    )
    report_status = _report_status(sorted_rows)
    snapshot_count = _decimal_count(len(sorted_rows))
    return MarketResearchCryptoOptionsPutCallSkewExtremeDigestReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        digest_status=report_status,
        recommended_next_step=_recommended_next_step(report_status),
        snapshot_count=snapshot_count,
        ready_snapshot_count=_status_count(sorted_rows, STATUS_READY),
        watch_snapshot_count=_status_count(sorted_rows, STATUS_WATCH),
        blocked_snapshot_count=_status_count(sorted_rows, STATUS_BLOCKED),
        extreme_skew_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            EXTREME_SKEW_REASON,
        ),
        put_iv_premium_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            PUT_IV_PREMIUM_REASON,
        ),
        call_iv_premium_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            CALL_IV_PREMIUM_REASON,
        ),
        put_call_volume_imbalance_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            PUT_CALL_VOLUME_IMBALANCE_REASON,
        ),
        reference_gap_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            REFERENCE_GAP_REASON,
        ),
        open_interest_gap_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            OPEN_INTEREST_GAP_REASON,
        ),
        volume_gap_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            VOLUME_GAP_REASON,
        ),
        stale_snapshot_count=_reason_snapshot_count(sorted_rows, STALE_SNAPSHOT_REASON),
        confidence_gap_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            CONFIDENCE_GAP_REASON,
        ),
        average_put_call_skew=_ratio(
            _decimal_sum(row.put_call_skew for row in sorted_rows),
            snapshot_count,
        ),
        average_put_iv_25_delta=_ratio(
            _decimal_sum(row.put_iv_25_delta for row in sorted_rows),
            snapshot_count,
        ),
        average_call_iv_25_delta=_ratio(
            _decimal_sum(row.call_iv_25_delta for row in sorted_rows),
            snapshot_count,
        ),
        average_put_call_volume_ratio=_ratio(
            _decimal_sum(row.put_call_volume_ratio for row in sorted_rows),
            snapshot_count,
        ),
        max_snapshot_age_seconds=max(
            (row.snapshot_age_seconds for row in sorted_rows),
            default=ZERO,
        ),
        max_allowed_snapshot_age_seconds=cfg.max_snapshot_age_seconds,
        min_reference_count=cfg.min_reference_count,
        min_open_interest_usd=cfg.min_open_interest_usd,
        min_volume_usd=cfg.min_volume_usd,
        max_allowed_put_call_skew_abs=cfg.max_put_call_skew_abs,
        max_allowed_put_iv_premium_over_call=cfg.max_put_iv_premium_over_call,
        max_allowed_call_iv_premium_over_put=cfg.max_call_iv_premium_over_put,
        max_allowed_put_call_volume_ratio=cfg.max_put_call_volume_ratio,
        min_confidence=cfg.min_confidence,
        ready_snapshot_ratio=_ratio(
            _status_count(sorted_rows, STATUS_READY),
            snapshot_count,
        ),
        rows=sorted_rows,
        source_config_versions=tuple(
            sorted(
                (snapshot.signal_id, snapshot.source_config_version)
                for snapshot in normalized_snapshots
            ),
        ),
        reason_code_counts=_reason_code_counts(sorted_rows),
        reason_codes=_summary_reason_codes(sorted_rows),
    )


def market_research_crypto_options_put_call_skew_extreme_digest_payload(
    report: MarketResearchCryptoOptionsPutCallSkewExtremeDigestReport,
) -> MappingProxyType:
    if type(report) is not MarketResearchCryptoOptionsPutCallSkewExtremeDigestReport:
        raise ValueError(
            "report must be exactly "
            "MarketResearchCryptoOptionsPutCallSkewExtremeDigestReport",
        )
    return _freeze(_json_ready(report))


def _row_for_snapshot(
    snapshot: MarketResearchCryptoOptionsPutCallSkewExtremeSnapshot,
    *,
    config: MarketResearchCryptoOptionsPutCallSkewExtremeDigestConfig,
    generated_at: datetime,
) -> MarketResearchCryptoOptionsPutCallSkewExtremeDigestRow:
    if snapshot.observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    snapshot_age_seconds = _age_seconds(generated_at, snapshot.observed_at)
    put_call_skew_abs = _ratio_abs(snapshot.put_call_skew)
    put_iv_premium_over_call = _positive_difference(
        snapshot.put_iv_25_delta,
        snapshot.call_iv_25_delta,
    )
    call_iv_premium_over_put = _positive_difference(
        snapshot.call_iv_25_delta,
        snapshot.put_iv_25_delta,
    )
    reason_codes = _row_reason_codes(
        snapshot=snapshot,
        config=config,
        snapshot_age_seconds=snapshot_age_seconds,
        put_call_skew_abs=put_call_skew_abs,
        put_iv_premium_over_call=put_iv_premium_over_call,
        call_iv_premium_over_put=call_iv_premium_over_put,
    )
    return MarketResearchCryptoOptionsPutCallSkewExtremeDigestRow(
        condition_id=snapshot.condition_id,
        signal_id=snapshot.signal_id,
        asset_symbol=snapshot.asset_symbol,
        expiry_bucket=snapshot.expiry_bucket,
        digest_status=_row_status(reason_codes),
        observed_at=snapshot.observed_at,
        snapshot_age_seconds=snapshot_age_seconds,
        reference_count=snapshot.reference_count,
        open_interest_usd=snapshot.open_interest_usd,
        volume_usd=snapshot.volume_usd,
        put_call_skew=snapshot.put_call_skew,
        put_iv_25_delta=snapshot.put_iv_25_delta,
        call_iv_25_delta=snapshot.call_iv_25_delta,
        put_call_skew_abs=put_call_skew_abs,
        put_iv_premium_over_call=put_iv_premium_over_call,
        call_iv_premium_over_put=call_iv_premium_over_put,
        put_call_volume_ratio=snapshot.put_call_volume_ratio,
        confidence=snapshot.confidence,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    snapshot: MarketResearchCryptoOptionsPutCallSkewExtremeSnapshot,
    config: MarketResearchCryptoOptionsPutCallSkewExtremeDigestConfig,
    snapshot_age_seconds: Decimal,
    put_call_skew_abs: Decimal,
    put_iv_premium_over_call: Decimal,
    call_iv_premium_over_put: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if put_call_skew_abs > config.max_put_call_skew_abs:
        reasons.append(EXTREME_SKEW_REASON)
    if put_iv_premium_over_call > config.max_put_iv_premium_over_call:
        reasons.append(PUT_IV_PREMIUM_REASON)
    if call_iv_premium_over_put > config.max_call_iv_premium_over_put:
        reasons.append(CALL_IV_PREMIUM_REASON)
    if snapshot.put_call_volume_ratio > config.max_put_call_volume_ratio:
        reasons.append(PUT_CALL_VOLUME_IMBALANCE_REASON)
    if snapshot.reference_count < config.min_reference_count:
        reasons.append(REFERENCE_GAP_REASON)
    if snapshot.open_interest_usd < config.min_open_interest_usd:
        reasons.append(OPEN_INTEREST_GAP_REASON)
    if snapshot.volume_usd < config.min_volume_usd:
        reasons.append(VOLUME_GAP_REASON)
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
            EXTREME_SKEW_REASON,
            PUT_IV_PREMIUM_REASON,
            CALL_IV_PREMIUM_REASON,
            PUT_CALL_VOLUME_IMBALANCE_REASON,
            OPEN_INTEREST_GAP_REASON,
            VOLUME_GAP_REASON,
            STALE_SNAPSHOT_REASON,
            CONFIDENCE_GAP_REASON,
        )
    ):
        return STATUS_BLOCKED
    return STATUS_WATCH


def _row_sort_value(
    row: MarketResearchCryptoOptionsPutCallSkewExtremeDigestRow,
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
    rows: tuple[MarketResearchCryptoOptionsPutCallSkewExtremeDigestRow, ...],
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
        return (
            "block_report_only_market_research_crypto_options_"
            "put_call_skew_extreme_digest"
        )
    if status == STATUS_WATCH:
        return (
            "review_report_only_market_research_crypto_options_"
            "put_call_skew_extreme_digest"
        )
    return (
        "allow_report_only_market_research_crypto_options_"
        "put_call_skew_extreme_digest"
    )


def _status_count(
    rows: tuple[MarketResearchCryptoOptionsPutCallSkewExtremeDigestRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.digest_status == status))


def _reason_snapshot_count(
    rows: tuple[MarketResearchCryptoOptionsPutCallSkewExtremeDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _reason_code_counts(
    rows: tuple[MarketResearchCryptoOptionsPutCallSkewExtremeDigestRow, ...],
) -> tuple[MarketResearchCryptoOptionsPutCallSkewExtremeDigestReasonCodeCount, ...]:
    snapshot_count = _decimal_count(len(rows))
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        MarketResearchCryptoOptionsPutCallSkewExtremeDigestReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
            snapshot_ratio=_ratio(_decimal_count(counts[reason_code]), snapshot_count),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _summary_reason_codes(
    rows: tuple[MarketResearchCryptoOptionsPutCallSkewExtremeDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    seen: set[str] = set()
    for row in rows:
        seen.update(row.reason_codes)
    if len(seen) > 1 and READY_REASON in seen:
        seen.remove(READY_REASON)
    return tuple(reason for reason in REASON_CODE_SEQUENCE if reason in seen)


def _validate_row(row: MarketResearchCryptoOptionsPutCallSkewExtremeDigestRow) -> None:
    if row.put_call_skew_abs != _ratio_abs(row.put_call_skew):
        raise ValueError("put_call_skew_abs does not match put_call_skew")
    if row.put_iv_premium_over_call != _positive_difference(
        row.put_iv_25_delta,
        row.call_iv_25_delta,
    ):
        raise ValueError("put_iv_premium_over_call does not match iv inputs")
    if row.call_iv_premium_over_put != _positive_difference(
        row.call_iv_25_delta,
        row.put_iv_25_delta,
    ):
        raise ValueError("call_iv_premium_over_put does not match iv inputs")
    if row.digest_status != _row_status(row.reason_codes):
        raise ValueError("digest_status does not match reason_codes")


def _validate_report(
    report: MarketResearchCryptoOptionsPutCallSkewExtremeDigestReport,
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
        (EXTREME_SKEW_REASON, report.extreme_skew_snapshot_count),
        (PUT_IV_PREMIUM_REASON, report.put_iv_premium_snapshot_count),
        (CALL_IV_PREMIUM_REASON, report.call_iv_premium_snapshot_count),
        (
            PUT_CALL_VOLUME_IMBALANCE_REASON,
            report.put_call_volume_imbalance_snapshot_count,
        ),
        (REFERENCE_GAP_REASON, report.reference_gap_snapshot_count),
        (OPEN_INTEREST_GAP_REASON, report.open_interest_gap_snapshot_count),
        (VOLUME_GAP_REASON, report.volume_gap_snapshot_count),
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
    if report.average_put_call_skew != _ratio(
        _decimal_sum(row.put_call_skew for row in report.rows),
        report.snapshot_count,
    ):
        raise ValueError("average_put_call_skew does not match rows")
    if report.average_put_iv_25_delta != _ratio(
        _decimal_sum(row.put_iv_25_delta for row in report.rows),
        report.snapshot_count,
    ):
        raise ValueError("average_put_iv_25_delta does not match rows")
    if report.average_call_iv_25_delta != _ratio(
        _decimal_sum(row.call_iv_25_delta for row in report.rows),
        report.snapshot_count,
    ):
        raise ValueError("average_call_iv_25_delta does not match rows")
    if report.average_put_call_volume_ratio != _ratio(
        _decimal_sum(row.put_call_volume_ratio for row in report.rows),
        report.snapshot_count,
    ):
        raise ValueError("average_put_call_volume_ratio does not match rows")
    if report.max_snapshot_age_seconds != max(
        (row.snapshot_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_snapshot_age_seconds does not match rows")
    if report.ready_snapshot_ratio != _ratio(
        report.ready_snapshot_count,
        report.snapshot_count,
    ):
        raise ValueError("ready_snapshot_ratio does not match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts do not match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes do not match rows")


def _normalize_snapshots(
    snapshots: Iterable[MarketResearchCryptoOptionsPutCallSkewExtremeSnapshot],
) -> tuple[MarketResearchCryptoOptionsPutCallSkewExtremeSnapshot, ...]:
    snapshot_tuple = tuple(snapshots)
    seen_ids: set[str] = set()
    for snapshot in snapshot_tuple:
        if type(snapshot) is not MarketResearchCryptoOptionsPutCallSkewExtremeSnapshot:
            raise ValueError(
                "snapshots must contain "
                "MarketResearchCryptoOptionsPutCallSkewExtremeSnapshot",
            )
        if snapshot.signal_id in seen_ids:
            raise ValueError("signal_id values must be unique")
        seen_ids.add(snapshot.signal_id)
        _require_hard_flags("snapshot", snapshot)
    return snapshot_tuple


def _normalize_rows(
    rows: tuple[MarketResearchCryptoOptionsPutCallSkewExtremeDigestRow, ...],
) -> tuple[MarketResearchCryptoOptionsPutCallSkewExtremeDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not MarketResearchCryptoOptionsPutCallSkewExtremeDigestRow:
            raise ValueError(
                "rows must contain "
                "MarketResearchCryptoOptionsPutCallSkewExtremeDigestRow",
            )
        _require_hard_flags("row", row)
    return rows


def _normalize_reason_code_counts(
    items: tuple[
        MarketResearchCryptoOptionsPutCallSkewExtremeDigestReasonCodeCount,
        ...,
    ],
) -> tuple[MarketResearchCryptoOptionsPutCallSkewExtremeDigestReasonCodeCount, ...]:
    if type(items) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for item in items:
        if type(item) is not MarketResearchCryptoOptionsPutCallSkewExtremeDigestReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count rows")
        _require_hard_flags("reason_code_count", item)
    return items


def _normalize_source_config_versions(
    value: tuple[tuple[str, str], ...],
) -> tuple[tuple[str, str], ...]:
    if type(value) is not tuple:
        raise ValueError("source_config_versions must be a tuple")
    pairs: list[tuple[str, str]] = []
    seen_ids: set[str] = set()
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("source_config_versions must contain pairs")
        signal_id, source_config_version = item
        _require_public_string("signal_id", signal_id)
        _require_public_string("source_config_version", source_config_version)
        if signal_id in seen_ids:
            raise ValueError("source_config_versions signal_id values unique")
        seen_ids.add(signal_id)
        pairs.append((signal_id, source_config_version))
    normalized = tuple(sorted(pairs))
    if normalized != value:
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
    if type(value) is not str or value not in PUT_CALL_SKEW_EXTREME_DIGEST_STATUSES:
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
    if type(value) is not datetime or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    return _quantize(
        Decimal(delta.days * 86400 + delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND),
    )


def _ratio_abs(value: Decimal) -> Decimal:
    return _quantize(abs(value))


def _positive_difference(left: Decimal, right: Decimal) -> Decimal:
    difference = _quantize(left - right)
    if difference < ZERO:
        return ZERO
    return difference


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
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, datetime):
        return value.isoformat()
    if type(value) is Decimal:
        return str(value)
    if isinstance(value, tuple):
        return tuple(_json_ready(item) for item in value)
    if isinstance(value, list):
        return tuple(_json_ready(item) for item in value)
    if isinstance(value, dict):
        return {str(name): _json_ready(item) for name, item in value.items()}
    return value


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({name: _freeze(item) for name, item in value.items()})
    if isinstance(value, tuple):
        return tuple(_freeze(item) for item in value)
    return value
