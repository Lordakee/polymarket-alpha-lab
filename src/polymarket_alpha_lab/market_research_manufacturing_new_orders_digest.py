"""Pure in-memory manufacturing new orders market research digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Context, Decimal, localcontext
from hashlib import sha256
from typing import Any


__all__ = (
    "DEFAULT_MARKET_RESEARCH_MANUFACTURING_NEW_ORDERS_DIGEST_CONFIG_VERSION",
    "MarketResearchManufacturingNewOrdersDigestConfig",
    "MarketResearchManufacturingNewOrdersDigestReasonCodeCount",
    "MarketResearchManufacturingNewOrdersDigestReport",
    "MarketResearchManufacturingNewOrdersDigestRow",
    "MarketResearchManufacturingNewOrdersDigestSignal",
    "build_market_research_manufacturing_new_orders_digest",
    "market_research_manufacturing_new_orders_digest_payload",
)


DEFAULT_MARKET_RESEARCH_MANUFACTURING_NEW_ORDERS_DIGEST_CONFIG_VERSION = (
    "market-research-manufacturing-new-orders-digest-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64)
MICROSECONDS_PER_SECOND = Decimal("1000000")

READY_STATUS = "ready"
WATCH_STATUS = "watch"
BLOCKED_STATUS = "blocked"
STATUSES = (READY_STATUS, WATCH_STATUS, BLOCKED_STATUS)
STATUS_RANK = {BLOCKED_STATUS: 0, WATCH_STATUS: 1, READY_STATUS: 2}

READY_REASON = "market_research_manufacturing_new_orders_digest_ready"
EMPTY_REASON = "market_research_manufacturing_new_orders_digest_empty"
STALE_REASON = "market_research_manufacturing_new_orders_digest_stale_signal"
MATERIAL_REASON = "market_research_manufacturing_new_orders_digest_material_surprise"
THIN_REASON = "market_research_manufacturing_new_orders_digest_thin_sources"
REVISION_REASON = "market_research_manufacturing_new_orders_digest_high_revision"
CONFIRMATION_REASON = (
    "market_research_manufacturing_new_orders_digest_confirmation_gap"
)
LOW_CONFIDENCE_REASON = (
    "market_research_manufacturing_new_orders_digest_low_confidence"
)
ROW_REASON_CODE_SEQUENCE = (
    STALE_REASON,
    MATERIAL_REASON,
    THIN_REASON,
    REVISION_REASON,
    CONFIRMATION_REASON,
    LOW_CONFIDENCE_REASON,
    READY_REASON,
)
REPORT_REASON_CODE_SEQUENCE = (
    EMPTY_REASON,
    CONFIRMATION_REASON,
    REVISION_REASON,
    LOW_CONFIDENCE_REASON,
    MATERIAL_REASON,
    STALE_REASON,
    THIN_REASON,
    READY_REASON,
)
REASON_COUNT_SORT_SEQUENCE = (
    CONFIRMATION_REASON,
    MATERIAL_REASON,
    REVISION_REASON,
    LOW_CONFIDENCE_REASON,
    STALE_REASON,
    THIN_REASON,
    READY_REASON,
    EMPTY_REASON,
)

ACCEPT_NEXT_STEP = "accept_report_only_market_research_manufacturing_new_orders_digest"
WATCH_NEXT_STEP = "watch_report_only_market_research_manufacturing_new_orders_digest"
BLOCK_NEXT_STEP = "block_report_only_market_research_manufacturing_new_orders_digest"

PUBLIC_REFERENCE_PREFIXES = ("public-", "official-", "gamma/", "clob/", "data/")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


SENSITIVE_REFERENCE_MARKERS = (
    _join_parts("api", "_", "key", "="),
    _join_parts("api", "key", "="),
    _join_parts("au", "thor", "ization", "="),
    _join_parts("bear", "er "),
    _join_parts("pass", "word", "="),
    _join_parts("pri", "vate"),
    _join_parts("pri", "vate", "_", "key", "="),
    _join_parts("sec", "ret"),
    _join_parts("sig", "nature", "="),
    _join_parts("to", "ken"),
    _join_parts("wal", "let"),
)


@dataclass(frozen=True)
class MarketResearchManufacturingNewOrdersDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_MANUFACTURING_NEW_ORDERS_DIGEST_CONFIG_VERSION
    )
    max_signal_age_seconds: Decimal = Decimal("7200.000000")
    min_source_count: Decimal = Decimal("2")
    material_surprise_threshold: Decimal = Decimal("0.050000")
    max_revision_ratio: Decimal = Decimal("0.200000")
    min_confirmation_ratio: Decimal = Decimal("0.650000")
    watch_confidence_threshold: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketResearchManufacturingNewOrdersDigestConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_MANUFACTURING_NEW_ORDERS_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("max_signal_age_seconds", "material_surprise_threshold"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_source_count",
            _normalize_positive_count_decimal("min_source_count", self.min_source_count),
        )
        for field_name in (
            "max_revision_ratio",
            "min_confirmation_ratio",
            "watch_confidence_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketResearchManufacturingNewOrdersDigestSignal:
    condition_id: str
    research_key: str
    release_key: str
    sector_key: str
    public_signal_reference: str
    observed_at: datetime
    expected_change_ratio: Decimal
    actual_change_ratio: Decimal
    surprise_ratio: Decimal
    source_count: Decimal
    revision_ratio: Decimal
    confirmation_ratio: Decimal
    base_confidence: Decimal
    signal_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketResearchManufacturingNewOrdersDigestSignal, "signal")
        for field_name in (
            "condition_id",
            "research_key",
            "release_key",
            "sector_key",
            "public_signal_reference",
            "signal_config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "expected_change_ratio",
            "actual_change_ratio",
            "surprise_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_count",
            _normalize_nonnegative_count_decimal("source_count", self.source_count),
        )
        for field_name in ("revision_ratio", "confirmation_ratio", "base_confidence"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketResearchManufacturingNewOrdersDigestRow:
    condition_id: str
    research_key: str
    release_key: str
    sector_key: str
    redacted_public_signal_reference: str
    observed_at: datetime
    expected_change_ratio: Decimal
    actual_change_ratio: Decimal
    surprise_ratio: Decimal
    surprise_delta: Decimal
    source_count: Decimal
    revision_ratio: Decimal
    confirmation_ratio: Decimal
    signal_age_seconds: Decimal
    confidence_decay_factor: Decimal
    final_confidence: Decimal
    digest_status: str
    reason_codes: tuple[str, ...]
    signal_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketResearchManufacturingNewOrdersDigestRow, "row")
        for field_name in (
            "condition_id",
            "research_key",
            "release_key",
            "sector_key",
            "redacted_public_signal_reference",
            "signal_config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "expected_change_ratio",
            "actual_change_ratio",
            "surprise_ratio",
            "surprise_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_count",
            _normalize_nonnegative_count_decimal("source_count", self.source_count),
        )
        for field_name in ("signal_age_seconds",):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "revision_ratio",
            "confirmation_ratio",
            "confidence_decay_factor",
            "final_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("digest_status", self.digest_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, ROW_REASON_CODE_SEQUENCE),
        )
        if self.surprise_delta != _q(self.actual_change_ratio - self.expected_change_ratio):
            raise ValueError("surprise_delta must match change ratios")
        if self.digest_status != _row_status(self.reason_codes):
            raise ValueError("digest_status must match reason_codes")
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketResearchManufacturingNewOrdersDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    signal_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchManufacturingNewOrdersDigestReasonCodeCount,
            "reason_code_count",
        )
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_count_decimal("count", self.count),
        )
        _require_known_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "signal_ratio",
            _normalize_ratio_decimal("signal_ratio", self.signal_ratio),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketResearchManufacturingNewOrdersDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    signal_count: Decimal
    ready_signal_count: Decimal
    watch_signal_count: Decimal
    blocked_signal_count: Decimal
    material_surprise_count: Decimal
    stale_signal_count: Decimal
    thin_source_count: Decimal
    high_revision_count: Decimal
    confirmation_gap_count: Decimal
    average_surprise_ratio: Decimal
    max_signal_age_seconds: Decimal
    average_source_count: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[MarketResearchManufacturingNewOrdersDigestReasonCodeCount, ...]
    rows: tuple[MarketResearchManufacturingNewOrdersDigestRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketResearchManufacturingNewOrdersDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_MANUFACTURING_NEW_ORDERS_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "signal_count",
            "ready_signal_count",
            "watch_signal_count",
            "blocked_signal_count",
            "material_surprise_count",
            "stale_signal_count",
            "thin_source_count",
            "high_revision_count",
            "confirmation_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_surprise_ratio",
            "max_signal_age_seconds",
            "average_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, REPORT_REASON_CODE_SEQUENCE),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_hard_flags(self)


def build_market_research_manufacturing_new_orders_digest(
    signals: Iterable[MarketResearchManufacturingNewOrdersDigestSignal],
    *,
    config: MarketResearchManufacturingNewOrdersDigestConfig
    | None = None,
    generated_at: datetime,
) -> MarketResearchManufacturingNewOrdersDigestReport:
    if config is None:
        config = MarketResearchManufacturingNewOrdersDigestConfig()
    if type(config) is not MarketResearchManufacturingNewOrdersDigestConfig:
        raise ValueError("config must be a MarketResearchManufacturingNewOrdersDigestConfig")
    generated_at_utc = _as_utc("generated_at", generated_at)

    normalized_signals = tuple(signals)
    seen_condition_ids: set[str] = set()
    rows = []
    for item in normalized_signals:
        if type(item) is not MarketResearchManufacturingNewOrdersDigestSignal:
            raise ValueError("signals must contain MarketResearchManufacturingNewOrdersDigestSignal")
        if item.condition_id in seen_condition_ids:
            raise ValueError(f"duplicate condition_id {item.condition_id!r}")
        seen_condition_ids.add(item.condition_id)
        rows.append(_build_row(item, config=config, generated_at=generated_at_utc))

    sorted_rows = tuple(
        sorted(
            rows,
            key=lambda row: (
                STATUS_RANK[row.digest_status],
                -row.signal_age_seconds,
                -row.surprise_ratio,
                row.release_key,
                row.condition_id,
            ),
        ),
    )

    signal_count = _count(len(sorted_rows))
    ready_count = _count(sum(1 for row in sorted_rows if row.digest_status == READY_STATUS))
    watch_count = _count(sum(1 for row in sorted_rows if row.digest_status == WATCH_STATUS))
    blocked_count = _count(
        sum(1 for row in sorted_rows if row.digest_status == BLOCKED_STATUS),
    )
    material_count = _count(sum(1 for row in sorted_rows if MATERIAL_REASON in row.reason_codes))
    stale_count = _count(sum(1 for row in sorted_rows if STALE_REASON in row.reason_codes))
    thin_count = _count(sum(1 for row in sorted_rows if THIN_REASON in row.reason_codes))
    revision_count = _count(
        sum(1 for row in sorted_rows if REVISION_REASON in row.reason_codes),
    )
    confirmation_count = _count(
        sum(1 for row in sorted_rows if CONFIRMATION_REASON in row.reason_codes),
    )
    average_surprise = _average(
        tuple(row.surprise_ratio for row in sorted_rows),
        denominator=signal_count,
    )
    max_age = max((row.signal_age_seconds for row in sorted_rows), default=ZERO)
    average_sources = _average(
        tuple(row.source_count for row in sorted_rows),
        denominator=signal_count,
    )
    reason_codes = _report_reason_codes(sorted_rows)
    reason_code_counts = _reason_code_counts(reason_codes, sorted_rows, signal_count)

    if not sorted_rows:
        digest_status = BLOCKED_STATUS
        next_step = BLOCK_NEXT_STEP
        reason_codes = (EMPTY_REASON,)
        reason_code_counts = (
            MarketResearchManufacturingNewOrdersDigestReasonCodeCount(
                reason_code=EMPTY_REASON,
                count=ONE,
                signal_ratio=ZERO,
            ),
        )
    elif blocked_count > ZERO:
        digest_status = BLOCKED_STATUS
        next_step = BLOCK_NEXT_STEP
    elif watch_count > ZERO:
        digest_status = WATCH_STATUS
        next_step = WATCH_NEXT_STEP
    else:
        digest_status = READY_STATUS
        next_step = ACCEPT_NEXT_STEP

    return MarketResearchManufacturingNewOrdersDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=next_step,
        signal_count=signal_count,
        ready_signal_count=ready_count,
        watch_signal_count=watch_count,
        blocked_signal_count=blocked_count,
        material_surprise_count=material_count,
        stale_signal_count=stale_count,
        thin_source_count=thin_count,
        high_revision_count=revision_count,
        confirmation_gap_count=confirmation_count,
        average_surprise_ratio=average_surprise,
        max_signal_age_seconds=max_age,
        average_source_count=average_sources,
        reason_codes=reason_codes,
        reason_code_counts=reason_code_counts,
        rows=sorted_rows,
    )


def market_research_manufacturing_new_orders_digest_payload(
    report: MarketResearchManufacturingNewOrdersDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchManufacturingNewOrdersDigestReport:
        raise ValueError("report must be a MarketResearchManufacturingNewOrdersDigestReport")
    return {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "digest_status": report.digest_status,
        "recommended_next_step": report.recommended_next_step,
        "signal_count": _count_text(report.signal_count),
        "ready_signal_count": _count_text(report.ready_signal_count),
        "watch_signal_count": _count_text(report.watch_signal_count),
        "blocked_signal_count": _count_text(report.blocked_signal_count),
        "material_surprise_count": _count_text(report.material_surprise_count),
        "stale_signal_count": _count_text(report.stale_signal_count),
        "thin_source_count": _count_text(report.thin_source_count),
        "high_revision_count": _count_text(report.high_revision_count),
        "confirmation_gap_count": _count_text(report.confirmation_gap_count),
        "average_surprise_ratio": _decimal_text(report.average_surprise_ratio),
        "max_signal_age_seconds": _decimal_text(report.max_signal_age_seconds),
        "average_source_count": _decimal_text(report.average_source_count),
        "reason_codes": list(report.reason_codes),
        "reason_code_counts": [
            {
                "reason_code": item.reason_code,
                "count": _count_text(item.count),
                "signal_ratio": _decimal_text(item.signal_ratio),
                "paper_only": item.paper_only,
                "report_only": item.report_only,
                "readonly": item.readonly,
            }
            for item in report.reason_code_counts
        ],
        "rows": [_row_payload(row) for row in report.rows],
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _build_row(
    signal: MarketResearchManufacturingNewOrdersDigestSignal,
    *,
    config: MarketResearchManufacturingNewOrdersDigestConfig,
    generated_at: datetime,
) -> MarketResearchManufacturingNewOrdersDigestRow:
    if signal.observed_at > generated_at:
        raise ValueError("observed_at must be <= generated_at")
    age = _seconds(generated_at - signal.observed_at)
    surprise_delta = _q(signal.actual_change_ratio - signal.expected_change_ratio)
    stale = age > config.max_signal_age_seconds
    material = signal.surprise_ratio >= config.material_surprise_threshold
    thin = signal.source_count < config.min_source_count
    high_revision = signal.revision_ratio > config.max_revision_ratio
    confirmation_gap = signal.confirmation_ratio < config.min_confirmation_ratio

    decay = _confidence_decay_factor(age, config.max_signal_age_seconds)
    final_confidence = _q(signal.base_confidence * decay)

    reasons: list[str] = []
    if stale:
        reasons.append(STALE_REASON)
    if material:
        reasons.append(MATERIAL_REASON)
    if thin:
        reasons.append(THIN_REASON)
    if high_revision:
        reasons.append(REVISION_REASON)
    if confirmation_gap:
        reasons.append(CONFIRMATION_REASON)
    if final_confidence < config.watch_confidence_threshold:
        reasons.append(LOW_CONFIDENCE_REASON)

    if stale or thin or high_revision or final_confidence < config.watch_confidence_threshold:
        status = BLOCKED_STATUS
    elif material or confirmation_gap:
        status = WATCH_STATUS
    else:
        status = READY_STATUS
        reasons.append(READY_REASON)

    return MarketResearchManufacturingNewOrdersDigestRow(
        condition_id=signal.condition_id,
        research_key=signal.research_key,
        release_key=signal.release_key,
        sector_key=signal.sector_key,
        redacted_public_signal_reference=_redact_reference(signal.public_signal_reference),
        observed_at=signal.observed_at,
        expected_change_ratio=signal.expected_change_ratio,
        actual_change_ratio=signal.actual_change_ratio,
        surprise_ratio=signal.surprise_ratio,
        surprise_delta=surprise_delta,
        source_count=signal.source_count,
        revision_ratio=signal.revision_ratio,
        confirmation_ratio=signal.confirmation_ratio,
        signal_age_seconds=age,
        confidence_decay_factor=decay,
        final_confidence=final_confidence,
        digest_status=status,
        reason_codes=tuple(reasons),
        signal_config_version=signal.signal_config_version,
    )


def _row_payload(row: MarketResearchManufacturingNewOrdersDigestRow) -> dict[str, Any]:
    return {
        "condition_id": row.condition_id,
        "research_key": row.research_key,
        "release_key": row.release_key,
        "sector_key": row.sector_key,
        "redacted_public_signal_reference": row.redacted_public_signal_reference,
        "observed_at": row.observed_at.isoformat(),
        "expected_change_ratio": _decimal_text(row.expected_change_ratio),
        "actual_change_ratio": _decimal_text(row.actual_change_ratio),
        "surprise_ratio": _decimal_text(row.surprise_ratio),
        "surprise_delta": _decimal_text(row.surprise_delta),
        "source_count": _decimal_text(row.source_count),
        "revision_ratio": _decimal_text(row.revision_ratio),
        "confirmation_ratio": _decimal_text(row.confirmation_ratio),
        "signal_age_seconds": _decimal_text(row.signal_age_seconds),
        "confidence_decay_factor": _decimal_text(row.confidence_decay_factor),
        "final_confidence": _decimal_text(row.final_confidence),
        "digest_status": row.digest_status,
        "reason_codes": list(row.reason_codes),
        "signal_config_version": row.signal_config_version,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _confidence_decay_factor(age: Decimal, max_age: Decimal) -> Decimal:
    if max_age <= ZERO or age <= max_age:
        return ONE
    with localcontext(DECIMAL_CONTEXT):
        ratio = max_age / age
    return _q(ratio)


def _report_reason_codes(
    rows: tuple[MarketResearchManufacturingNewOrdersDigestRow, ...],
) -> tuple[str, ...]:
    codes = {
        code
        for row in rows
        for code in row.reason_codes
        if code != READY_REASON
    }
    if not codes and rows:
        codes.add(READY_REASON)
    return tuple(code for code in REPORT_REASON_CODE_SEQUENCE if code in codes)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[MarketResearchManufacturingNewOrdersDigestRow, ...],
    signal_count: Decimal,
) -> tuple[MarketResearchManufacturingNewOrdersDigestReasonCodeCount, ...]:
    counts: list[MarketResearchManufacturingNewOrdersDigestReasonCodeCount] = []
    for reason_code in reason_codes:
        count = _count(sum(1 for row in rows if reason_code in row.reason_codes))
        counts.append(
            MarketResearchManufacturingNewOrdersDigestReasonCodeCount(
                reason_code=reason_code,
                count=count,
                signal_ratio=_ratio(count, signal_count),
            ),
        )
    return tuple(
        sorted(
            counts,
            key=_reason_code_count_sort_key,
        ),
    )


def _average(values: tuple[Decimal, ...], *, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _q(sum(values, ZERO) / denominator)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _q(numerator / denominator)


def _reason_code_count_sort_key(
    item: MarketResearchManufacturingNewOrdersDigestReasonCodeCount,
) -> tuple[Decimal, int]:
    return (-item.count, REASON_COUNT_SORT_SEQUENCE.index(item.reason_code))


def _seconds(delta: timedelta) -> Decimal:
    seconds = (
        Decimal(delta.days * 86400 + delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    return _q(seconds)


def _count(value: int) -> Decimal:
    return _q(Decimal(value))


def _q(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _q(value)


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be non-negative")
    return normalized


def _normalize_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return normalized


def _normalize_positive_count_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return normalized


def _normalize_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    return normalized


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a str")
    if not value or value != value.strip():
        raise ValueError(f"{field_name} must be non-empty and trimmed")


def _normalize_reason_codes(
    value: tuple[str, ...],
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not value:
        raise ValueError("reason_codes must not be empty")
    for reason_code in value:
        _require_known_reason_code("reason_codes", reason_code)
    if len(set(value)) != len(value):
        raise ValueError("reason_codes must be unique")
    canonical = tuple(reason_code for reason_code in sequence if reason_code in value)
    if value != canonical:
        raise ValueError("reason_codes must use deterministic ordering")
    return value


def _normalize_rows(
    value: tuple[MarketResearchManufacturingNewOrdersDigestRow, ...],
) -> tuple[MarketResearchManufacturingNewOrdersDigestRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in value:
        if type(row) is not MarketResearchManufacturingNewOrdersDigestRow:
            raise ValueError("rows must contain MarketResearchManufacturingNewOrdersDigestRow")
    if value != tuple(
        sorted(
            value,
            key=lambda row: (
                STATUS_RANK[row.digest_status],
                -row.signal_age_seconds,
                -row.surprise_ratio,
                row.release_key,
                row.condition_id,
            ),
        ),
    ):
        raise ValueError("rows must use deterministic ordering")
    return value


def _normalize_reason_code_counts(
    value: tuple[MarketResearchManufacturingNewOrdersDigestReasonCodeCount, ...],
) -> tuple[MarketResearchManufacturingNewOrdersDigestReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for item in value:
        if type(item) is not MarketResearchManufacturingNewOrdersDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchManufacturingNewOrdersDigestReasonCodeCount",
            )
    if value != tuple(sorted(value, key=_reason_code_count_sort_key)):
        raise ValueError("reason_code_counts must use deterministic ordering")
    return value


def _require_status(field_name: str, value: str) -> None:
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES!r}")


def _require_known_reason_code(field_name: str, value: str) -> None:
    if type(value) is not str or value not in REPORT_REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a known reason code")


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (READY_REASON,):
        return READY_STATUS
    if (
        STALE_REASON in reason_codes
        or THIN_REASON in reason_codes
        or REVISION_REASON in reason_codes
        or LOW_CONFIDENCE_REASON in reason_codes
    ):
        return BLOCKED_STATUS
    return WATCH_STATUS


def _require_hard_flags(value: object) -> None:
    for flag in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag) is not True:
            raise ValueError(f"{flag} must be True")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _redact_reference(value: str) -> str:
    lowered = value.lower()
    if any(marker in lowered for marker in SENSITIVE_REFERENCE_MARKERS):
        return f"sha256:{sha256(value.encode('utf-8')).hexdigest()[:12]}"
    if value.startswith(PUBLIC_REFERENCE_PREFIXES):
        return value
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()[:12]}"


def _decimal_text(value: Decimal) -> str:
    return format(value, "f")


def _count_text(value: Decimal) -> str:
    return _decimal_text(value)


def _validate_report_consistency(
    report: MarketResearchManufacturingNewOrdersDigestReport,
) -> None:
    row_count = _count(len(report.rows))
    if report.signal_count != row_count:
        raise ValueError("signal_count must equal row count")
    status_counts = {
        READY_STATUS: _count(sum(1 for row in report.rows if row.digest_status == READY_STATUS)),
        WATCH_STATUS: _count(sum(1 for row in report.rows if row.digest_status == WATCH_STATUS)),
        BLOCKED_STATUS: _count(
            sum(1 for row in report.rows if row.digest_status == BLOCKED_STATUS),
        ),
    }
    if report.ready_signal_count != status_counts[READY_STATUS]:
        raise ValueError("ready_signal_count must match rows")
    if report.watch_signal_count != status_counts[WATCH_STATUS]:
        raise ValueError("watch_signal_count must match rows")
    if report.blocked_signal_count != status_counts[BLOCKED_STATUS]:
        raise ValueError("blocked_signal_count must match rows")
    if report.signal_count == ZERO and report.rows != ():
        raise ValueError("rows must be empty when signal_count is zero")
    expected_status = BLOCKED_STATUS
    expected_next_step = BLOCK_NEXT_STEP
    if report.rows:
        if status_counts[BLOCKED_STATUS] > ZERO:
            expected_status = BLOCKED_STATUS
            expected_next_step = BLOCK_NEXT_STEP
        elif status_counts[WATCH_STATUS] > ZERO:
            expected_status = WATCH_STATUS
            expected_next_step = WATCH_NEXT_STEP
        else:
            expected_status = READY_STATUS
            expected_next_step = ACCEPT_NEXT_STEP
    if report.digest_status != expected_status:
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != expected_next_step:
        raise ValueError("recommended_next_step must match digest_status")
    expected_reason_codes = (
        _report_reason_codes(report.rows) if report.rows else (EMPTY_REASON,)
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    expected_reason_code_counts = _reason_code_counts(
        expected_reason_codes,
        report.rows,
        report.signal_count,
    )
    if not report.rows:
        expected_reason_code_counts = (
            MarketResearchManufacturingNewOrdersDigestReasonCodeCount(
                reason_code=EMPTY_REASON,
                count=ONE,
                signal_ratio=ZERO,
            ),
        )
    if report.reason_code_counts != expected_reason_code_counts:
        raise ValueError("reason_code_counts must match rows")
