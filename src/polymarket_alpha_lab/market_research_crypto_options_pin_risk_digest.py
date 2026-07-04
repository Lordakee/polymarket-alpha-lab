"""Pure Phase 1 crypto options expiry pin risk market research reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from types import MappingProxyType
from typing import Any


DEFAULT_MARKET_RESEARCH_CRYPTO_OPTIONS_PIN_RISK_DIGEST_CONFIG_VERSION = (
    "market-research-crypto-options-pin-risk-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
PIN_RISK_DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

READY_REASON = "market_research_crypto_options_pin_risk_digest_ready"
NO_INPUTS_REASON = "market_research_crypto_options_pin_risk_digest_no_inputs"
PIN_CLUSTER_REASON = "market_research_crypto_options_pin_risk_digest_pin_cluster"
MAX_PAIN_ALIGNMENT_REASON = (
    "market_research_crypto_options_pin_risk_digest_max_pain_alignment"
)
EXPIRY_WINDOW_REASON = "market_research_crypto_options_pin_risk_digest_expiry_window"
NOTIONAL_GAP_REASON = "market_research_crypto_options_pin_risk_digest_notional_gap"
STALE_SNAPSHOT_REASON = "market_research_crypto_options_pin_risk_digest_stale_snapshot"
CONFIDENCE_GAP_REASON = (
    "market_research_crypto_options_pin_risk_digest_confidence_gap"
)

REASON_CODE_SEQUENCE = (
    PIN_CLUSTER_REASON,
    MAX_PAIN_ALIGNMENT_REASON,
    EXPIRY_WINDOW_REASON,
    NOTIONAL_GAP_REASON,
    STALE_SNAPSHOT_REASON,
    CONFIDENCE_GAP_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    PIN_CLUSTER_REASON,
    MAX_PAIN_ALIGNMENT_REASON,
    EXPIRY_WINDOW_REASON,
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
        _join_parts("au", "th"),
        _join_parts("ac", "count"),
        _join_parts("0", "x"),
    ),
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_CRYPTO_OPTIONS_PIN_RISK_DIGEST_CONFIG_VERSION",
    "MarketResearchCryptoOptionsPinRiskDigestConfig",
    "MarketResearchCryptoOptionsPinRiskDigestReasonCodeCount",
    "MarketResearchCryptoOptionsPinRiskDigestReport",
    "MarketResearchCryptoOptionsPinRiskDigestRow",
    "MarketResearchCryptoOptionsPinRiskSnapshot",
    "build_market_research_crypto_options_pin_risk_digest",
    "market_research_crypto_options_pin_risk_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchCryptoOptionsPinRiskDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_CRYPTO_OPTIONS_PIN_RISK_DIGEST_CONFIG_VERSION
    )
    max_snapshot_age_seconds: Decimal = Decimal("3600.000000")
    max_hours_to_expiry: Decimal = Decimal("24.000000")
    max_strike_distance_ratio: Decimal = Decimal("0.010000")
    max_max_pain_distance_ratio: Decimal = Decimal("0.015000")
    min_near_strike_open_interest_ratio: Decimal = Decimal("0.300000")
    min_gamma_concentration_ratio: Decimal = Decimal("0.350000")
    min_expiry_notional_usd: Decimal = Decimal("10000000.000000")
    min_confidence: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoOptionsPinRiskDigestConfig:
            raise TypeError(
                "MarketResearchCryptoOptionsPinRiskDigestConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoOptionsPinRiskDigestConfig:
            raise ValueError(
                "config must be exactly MarketResearchCryptoOptionsPinRiskDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("max_snapshot_age_seconds", "max_hours_to_expiry"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_strike_distance_ratio",
            "max_max_pain_distance_ratio",
            "min_near_strike_open_interest_ratio",
            "min_gamma_concentration_ratio",
            "min_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_expiry_notional_usd",
            _require_nonnegative_count_decimal(
                "min_expiry_notional_usd",
                self.min_expiry_notional_usd,
            ),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchCryptoOptionsPinRiskSnapshot:
    condition_id: str
    pin_risk_key: str
    asset_symbol: str
    expiry_bucket: str
    observed_at: datetime
    spot_price: Decimal
    nearest_strike_price: Decimal
    max_pain_price: Decimal
    expiry_notional_usd: Decimal
    near_strike_open_interest_ratio: Decimal
    gamma_concentration_ratio: Decimal
    hours_to_expiry: Decimal
    confidence: Decimal
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoOptionsPinRiskSnapshot:
            raise TypeError(
                "MarketResearchCryptoOptionsPinRiskSnapshot does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoOptionsPinRiskSnapshot:
            raise ValueError(
                "snapshot must be exactly MarketResearchCryptoOptionsPinRiskSnapshot",
            )
        for field_name in (
            "condition_id",
            "pin_risk_key",
            "asset_symbol",
            "expiry_bucket",
            "source_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("spot_price", "nearest_strike_price", "max_pain_price"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "expiry_notional_usd",
            _require_nonnegative_count_decimal(
                "expiry_notional_usd",
                self.expiry_notional_usd,
            ),
        )
        for field_name in (
            "near_strike_open_interest_ratio",
            "gamma_concentration_ratio",
            "confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "hours_to_expiry",
            _require_nonnegative_count_decimal("hours_to_expiry", self.hours_to_expiry),
        )
        _require_hard_flags("snapshot", self)


@dataclass(frozen=True)
class MarketResearchCryptoOptionsPinRiskDigestRow:
    condition_id: str
    pin_risk_key: str
    asset_symbol: str
    expiry_bucket: str
    digest_status: str
    observed_at: datetime
    snapshot_age_seconds: Decimal
    spot_price: Decimal
    nearest_strike_price: Decimal
    max_pain_price: Decimal
    strike_distance_ratio: Decimal
    max_pain_distance_ratio: Decimal
    expiry_notional_usd: Decimal
    near_strike_open_interest_ratio: Decimal
    gamma_concentration_ratio: Decimal
    hours_to_expiry: Decimal
    confidence: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoOptionsPinRiskDigestRow:
            raise TypeError(
                "MarketResearchCryptoOptionsPinRiskDigestRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoOptionsPinRiskDigestRow:
            raise ValueError(
                "row must be exactly MarketResearchCryptoOptionsPinRiskDigestRow",
            )
        for field_name in (
            "condition_id",
            "pin_risk_key",
            "asset_symbol",
            "expiry_bucket",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_status("digest_status", self.digest_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "snapshot_age_seconds",
            "expiry_notional_usd",
            "hours_to_expiry",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("spot_price", "nearest_strike_price", "max_pain_price"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "strike_distance_ratio",
            "max_pain_distance_ratio",
            "near_strike_open_interest_ratio",
            "gamma_concentration_ratio",
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
class MarketResearchCryptoOptionsPinRiskDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    snapshot_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoOptionsPinRiskDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchCryptoOptionsPinRiskDigestReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoOptionsPinRiskDigestReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "MarketResearchCryptoOptionsPinRiskDigestReasonCodeCount",
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
class MarketResearchCryptoOptionsPinRiskDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    snapshot_count: Decimal
    ready_snapshot_count: Decimal
    watch_snapshot_count: Decimal
    blocked_snapshot_count: Decimal
    pin_cluster_snapshot_count: Decimal
    max_pain_alignment_snapshot_count: Decimal
    expiry_window_snapshot_count: Decimal
    notional_gap_snapshot_count: Decimal
    stale_snapshot_count: Decimal
    confidence_gap_snapshot_count: Decimal
    average_strike_distance_ratio: Decimal
    average_max_pain_distance_ratio: Decimal
    average_near_strike_open_interest_ratio: Decimal
    average_gamma_concentration_ratio: Decimal
    average_hours_to_expiry: Decimal
    max_snapshot_age_seconds: Decimal
    max_allowed_snapshot_age_seconds: Decimal
    max_allowed_hours_to_expiry: Decimal
    max_allowed_strike_distance_ratio: Decimal
    max_allowed_max_pain_distance_ratio: Decimal
    min_near_strike_open_interest_ratio: Decimal
    min_gamma_concentration_ratio: Decimal
    min_expiry_notional_usd: Decimal
    min_confidence: Decimal
    pin_cluster_snapshot_ratio: Decimal
    rows: tuple[MarketResearchCryptoOptionsPinRiskDigestRow, ...]
    source_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[MarketResearchCryptoOptionsPinRiskDigestReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCryptoOptionsPinRiskDigestReport:
            raise TypeError(
                "MarketResearchCryptoOptionsPinRiskDigestReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCryptoOptionsPinRiskDigestReport:
            raise ValueError(
                "report must be exactly MarketResearchCryptoOptionsPinRiskDigestReport",
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
            "pin_cluster_snapshot_count",
            "max_pain_alignment_snapshot_count",
            "expiry_window_snapshot_count",
            "notional_gap_snapshot_count",
            "stale_snapshot_count",
            "confidence_gap_snapshot_count",
            "average_hours_to_expiry",
            "max_snapshot_age_seconds",
            "max_allowed_snapshot_age_seconds",
            "max_allowed_hours_to_expiry",
            "min_expiry_notional_usd",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_strike_distance_ratio",
            "average_max_pain_distance_ratio",
            "average_near_strike_open_interest_ratio",
            "average_gamma_concentration_ratio",
            "max_allowed_strike_distance_ratio",
            "max_allowed_max_pain_distance_ratio",
            "min_near_strike_open_interest_ratio",
            "min_gamma_concentration_ratio",
            "min_confidence",
            "pin_cluster_snapshot_ratio",
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


def build_market_research_crypto_options_pin_risk_digest(
    snapshots: Iterable[MarketResearchCryptoOptionsPinRiskSnapshot],
    *,
    config: MarketResearchCryptoOptionsPinRiskDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchCryptoOptionsPinRiskDigestReport:
    cfg = config or MarketResearchCryptoOptionsPinRiskDigestConfig()
    if type(cfg) is not MarketResearchCryptoOptionsPinRiskDigestConfig:
        raise ValueError(
            "config must be exactly MarketResearchCryptoOptionsPinRiskDigestConfig",
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
                row.pin_risk_key,
                row.condition_id,
            ),
        ),
    )
    snapshot_count = _decimal_count(len(sorted_rows))
    report_status = _report_status(sorted_rows)
    return MarketResearchCryptoOptionsPinRiskDigestReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        digest_status=report_status,
        recommended_next_step=_recommended_next_step(report_status),
        snapshot_count=snapshot_count,
        ready_snapshot_count=_status_count(sorted_rows, STATUS_READY),
        watch_snapshot_count=_status_count(sorted_rows, STATUS_WATCH),
        blocked_snapshot_count=_status_count(sorted_rows, STATUS_BLOCKED),
        pin_cluster_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            PIN_CLUSTER_REASON,
        ),
        max_pain_alignment_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            MAX_PAIN_ALIGNMENT_REASON,
        ),
        expiry_window_snapshot_count=_reason_snapshot_count(
            sorted_rows,
            EXPIRY_WINDOW_REASON,
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
        average_strike_distance_ratio=_average_decimal(
            row.strike_distance_ratio for row in sorted_rows
        ),
        average_max_pain_distance_ratio=_average_decimal(
            row.max_pain_distance_ratio for row in sorted_rows
        ),
        average_near_strike_open_interest_ratio=_average_decimal(
            row.near_strike_open_interest_ratio for row in sorted_rows
        ),
        average_gamma_concentration_ratio=_average_decimal(
            row.gamma_concentration_ratio for row in sorted_rows
        ),
        average_hours_to_expiry=_average_decimal(
            row.hours_to_expiry for row in sorted_rows
        ),
        max_snapshot_age_seconds=max(
            (row.snapshot_age_seconds for row in sorted_rows),
            default=ZERO,
        ),
        max_allowed_snapshot_age_seconds=cfg.max_snapshot_age_seconds,
        max_allowed_hours_to_expiry=cfg.max_hours_to_expiry,
        max_allowed_strike_distance_ratio=cfg.max_strike_distance_ratio,
        max_allowed_max_pain_distance_ratio=cfg.max_max_pain_distance_ratio,
        min_near_strike_open_interest_ratio=cfg.min_near_strike_open_interest_ratio,
        min_gamma_concentration_ratio=cfg.min_gamma_concentration_ratio,
        min_expiry_notional_usd=cfg.min_expiry_notional_usd,
        min_confidence=cfg.min_confidence,
        pin_cluster_snapshot_ratio=_ratio(
            _reason_snapshot_count(sorted_rows, PIN_CLUSTER_REASON),
            snapshot_count,
        ),
        rows=sorted_rows,
        source_config_versions=tuple(
            sorted(
                (snapshot.pin_risk_key, snapshot.source_config_version)
                for snapshot in normalized_snapshots
            ),
        ),
        reason_code_counts=_reason_code_counts(sorted_rows),
        reason_codes=_summary_reason_codes(sorted_rows),
    )


def market_research_crypto_options_pin_risk_digest_payload(
    report: MarketResearchCryptoOptionsPinRiskDigestReport,
) -> MappingProxyType:
    if type(report) is not MarketResearchCryptoOptionsPinRiskDigestReport:
        raise ValueError(
            "report must be exactly MarketResearchCryptoOptionsPinRiskDigestReport",
        )
    return _freeze(_json_ready(report))


def _row_for_snapshot(
    snapshot: MarketResearchCryptoOptionsPinRiskSnapshot,
    *,
    config: MarketResearchCryptoOptionsPinRiskDigestConfig,
    generated_at: datetime,
) -> MarketResearchCryptoOptionsPinRiskDigestRow:
    if snapshot.observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    snapshot_age_seconds = _age_seconds(generated_at, snapshot.observed_at)
    strike_distance_ratio = _price_distance_ratio(
        snapshot.spot_price,
        snapshot.nearest_strike_price,
    )
    max_pain_distance_ratio = _price_distance_ratio(
        snapshot.spot_price,
        snapshot.max_pain_price,
    )
    reason_codes = _row_reason_codes(
        snapshot=snapshot,
        config=config,
        snapshot_age_seconds=snapshot_age_seconds,
        strike_distance_ratio=strike_distance_ratio,
        max_pain_distance_ratio=max_pain_distance_ratio,
    )
    return MarketResearchCryptoOptionsPinRiskDigestRow(
        condition_id=snapshot.condition_id,
        pin_risk_key=snapshot.pin_risk_key,
        asset_symbol=snapshot.asset_symbol,
        expiry_bucket=snapshot.expiry_bucket,
        digest_status=_row_status(reason_codes),
        observed_at=snapshot.observed_at,
        snapshot_age_seconds=snapshot_age_seconds,
        spot_price=snapshot.spot_price,
        nearest_strike_price=snapshot.nearest_strike_price,
        max_pain_price=snapshot.max_pain_price,
        strike_distance_ratio=strike_distance_ratio,
        max_pain_distance_ratio=max_pain_distance_ratio,
        expiry_notional_usd=snapshot.expiry_notional_usd,
        near_strike_open_interest_ratio=snapshot.near_strike_open_interest_ratio,
        gamma_concentration_ratio=snapshot.gamma_concentration_ratio,
        hours_to_expiry=snapshot.hours_to_expiry,
        confidence=snapshot.confidence,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    snapshot: MarketResearchCryptoOptionsPinRiskSnapshot,
    config: MarketResearchCryptoOptionsPinRiskDigestConfig,
    snapshot_age_seconds: Decimal,
    strike_distance_ratio: Decimal,
    max_pain_distance_ratio: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    in_expiry_window = snapshot.hours_to_expiry <= config.max_hours_to_expiry
    has_reference_notional = snapshot.expiry_notional_usd >= config.min_expiry_notional_usd
    if (
        strike_distance_ratio <= config.max_strike_distance_ratio
        and snapshot.near_strike_open_interest_ratio
        >= config.min_near_strike_open_interest_ratio
        and snapshot.gamma_concentration_ratio >= config.min_gamma_concentration_ratio
        and in_expiry_window
        and has_reference_notional
    ):
        reasons.append(PIN_CLUSTER_REASON)
    if max_pain_distance_ratio <= config.max_max_pain_distance_ratio:
        reasons.append(MAX_PAIN_ALIGNMENT_REASON)
    if in_expiry_window:
        reasons.append(EXPIRY_WINDOW_REASON)
    if not has_reference_notional:
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
            PIN_CLUSTER_REASON,
            STALE_SNAPSHOT_REASON,
            CONFIDENCE_GAP_REASON,
        )
    ):
        return STATUS_BLOCKED
    return STATUS_WATCH


def _row_sort_value(
    row: MarketResearchCryptoOptionsPinRiskDigestRow,
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
    rows: tuple[MarketResearchCryptoOptionsPinRiskDigestRow, ...],
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
        return "block_report_only_market_research_crypto_options_pin_risk_digest"
    if status == STATUS_WATCH:
        return "review_report_only_market_research_crypto_options_pin_risk_digest"
    return "allow_report_only_market_research_crypto_options_pin_risk_digest"


def _status_count(
    rows: tuple[MarketResearchCryptoOptionsPinRiskDigestRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.digest_status == status))


def _reason_snapshot_count(
    rows: tuple[MarketResearchCryptoOptionsPinRiskDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _reason_code_counts(
    rows: tuple[MarketResearchCryptoOptionsPinRiskDigestRow, ...],
) -> tuple[MarketResearchCryptoOptionsPinRiskDigestReasonCodeCount, ...]:
    snapshot_count = _decimal_count(len(rows))
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        MarketResearchCryptoOptionsPinRiskDigestReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
            snapshot_ratio=_ratio(_decimal_count(counts[reason_code]), snapshot_count),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _summary_reason_codes(
    rows: tuple[MarketResearchCryptoOptionsPinRiskDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    seen: set[str] = set()
    for row in rows:
        seen.update(row.reason_codes)
    if len(seen) > 1 and READY_REASON in seen:
        seen.remove(READY_REASON)
    return tuple(reason for reason in REASON_CODE_SEQUENCE if reason in seen)


def _validate_row(row: MarketResearchCryptoOptionsPinRiskDigestRow) -> None:
    if row.strike_distance_ratio != _price_distance_ratio(
        row.spot_price,
        row.nearest_strike_price,
    ):
        raise ValueError("strike_distance_ratio does not match prices")
    if row.max_pain_distance_ratio != _price_distance_ratio(
        row.spot_price,
        row.max_pain_price,
    ):
        raise ValueError("max_pain_distance_ratio does not match prices")
    if row.digest_status != _row_status(row.reason_codes):
        raise ValueError("digest_status does not match reason_codes")


def _validate_report(report: MarketResearchCryptoOptionsPinRiskDigestReport) -> None:
    if report.snapshot_count != _decimal_count(len(report.rows)):
        raise ValueError("snapshot_count does not match rows")
    if report.ready_snapshot_count != _status_count(report.rows, STATUS_READY):
        raise ValueError("ready_snapshot_count does not match rows")
    if report.watch_snapshot_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_snapshot_count does not match rows")
    if report.blocked_snapshot_count != _status_count(report.rows, STATUS_BLOCKED):
        raise ValueError("blocked_snapshot_count does not match rows")
    expected_counts = (
        (PIN_CLUSTER_REASON, report.pin_cluster_snapshot_count),
        (MAX_PAIN_ALIGNMENT_REASON, report.max_pain_alignment_snapshot_count),
        (EXPIRY_WINDOW_REASON, report.expiry_window_snapshot_count),
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
    if report.average_strike_distance_ratio != _average_decimal(
        row.strike_distance_ratio for row in report.rows
    ):
        raise ValueError("average_strike_distance_ratio does not match rows")
    if report.average_max_pain_distance_ratio != _average_decimal(
        row.max_pain_distance_ratio for row in report.rows
    ):
        raise ValueError("average_max_pain_distance_ratio does not match rows")
    if report.average_near_strike_open_interest_ratio != _average_decimal(
        row.near_strike_open_interest_ratio for row in report.rows
    ):
        raise ValueError(
            "average_near_strike_open_interest_ratio does not match rows",
        )
    if report.average_gamma_concentration_ratio != _average_decimal(
        row.gamma_concentration_ratio for row in report.rows
    ):
        raise ValueError("average_gamma_concentration_ratio does not match rows")
    if report.average_hours_to_expiry != _average_decimal(
        row.hours_to_expiry for row in report.rows
    ):
        raise ValueError("average_hours_to_expiry does not match rows")
    if report.max_snapshot_age_seconds != max(
        (row.snapshot_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_snapshot_age_seconds does not match rows")
    if report.pin_cluster_snapshot_ratio != _ratio(
        report.pin_cluster_snapshot_count,
        report.snapshot_count,
    ):
        raise ValueError("pin_cluster_snapshot_ratio does not match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts do not match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes do not match rows")


def _normalize_snapshots(
    snapshots: Iterable[MarketResearchCryptoOptionsPinRiskSnapshot],
) -> tuple[MarketResearchCryptoOptionsPinRiskSnapshot, ...]:
    snapshot_tuple = tuple(snapshots)
    seen_keys: set[str] = set()
    for snapshot in snapshot_tuple:
        if type(snapshot) is not MarketResearchCryptoOptionsPinRiskSnapshot:
            raise ValueError(
                "snapshots must contain MarketResearchCryptoOptionsPinRiskSnapshot",
            )
        if snapshot.pin_risk_key in seen_keys:
            raise ValueError("pin_risk_key values must be unique")
        seen_keys.add(snapshot.pin_risk_key)
        _require_hard_flags("snapshot", snapshot)
    return snapshot_tuple


def _normalize_rows(
    rows: tuple[MarketResearchCryptoOptionsPinRiskDigestRow, ...],
) -> tuple[MarketResearchCryptoOptionsPinRiskDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not MarketResearchCryptoOptionsPinRiskDigestRow:
            raise ValueError(
                "rows must contain MarketResearchCryptoOptionsPinRiskDigestRow",
            )
        _require_hard_flags("row", row)
    return rows


def _normalize_reason_code_counts(
    items: tuple[MarketResearchCryptoOptionsPinRiskDigestReasonCodeCount, ...],
) -> tuple[MarketResearchCryptoOptionsPinRiskDigestReasonCodeCount, ...]:
    if type(items) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for item in items:
        if type(item) is not MarketResearchCryptoOptionsPinRiskDigestReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count rows")
        _require_hard_flags("reason_code_count", item)
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
        pin_risk_key, source_config_version = item
        _require_public_string("pin_risk_key", pin_risk_key)
        _require_public_string("source_config_version", source_config_version)
        if pin_risk_key in seen_keys:
            raise ValueError("source_config_versions pin_risk_key values must be unique")
        seen_keys.add(pin_risk_key)
        pairs.append((pin_risk_key, source_config_version))
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
    if type(value) is not str or value not in PIN_RISK_DIGEST_STATUSES:
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


def _price_distance_ratio(reference_price: Decimal, comparison_price: Decimal) -> Decimal:
    return _ratio(_quantize(abs(reference_price - comparison_price)), reference_price)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _decimal_sum(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total = _quantize(total + value)
    return total


def _average_decimal(values: Iterable[Decimal]) -> Decimal:
    value_tuple = tuple(values)
    if not value_tuple:
        return ZERO
    return _ratio(_decimal_sum(value_tuple), _decimal_count(len(value_tuple)))


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
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, tuple):
        return tuple(_freeze(item) for item in value)
    return value
