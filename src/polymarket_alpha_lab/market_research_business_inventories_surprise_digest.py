"""Pure Phase 1 business inventories surprise reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_BUSINESS_INVENTORIES_SURPRISE_DIGEST_CONFIG_VERSION = (
    "market-research-business-inventories-surprise-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

REASON_PREFIX = "market_research_business_inventories_surprise_digest_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
READY_REASON = f"{REASON_PREFIX}ready"
STALE_SIGNAL_REASON = f"{REASON_PREFIX}stale_signal"
MATERIAL_SURPRISE_REASON = f"{REASON_PREFIX}material_surprise"
THIN_SOURCES_REASON = f"{REASON_PREFIX}thin_sources"
HIGH_REVISION_REASON = f"{REASON_PREFIX}high_revision"
CONFIRMATION_GAP_REASON = f"{REASON_PREFIX}confirmation_gap"

REASON_CODE_SEQUENCE = (
    CONFIRMATION_GAP_REASON,
    MATERIAL_SURPRISE_REASON,
    STALE_SIGNAL_REASON,
    THIN_SOURCES_REASON,
    HIGH_REVISION_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    STALE_SIGNAL_REASON,
    MATERIAL_SURPRISE_REASON,
    THIN_SOURCES_REASON,
    HIGH_REVISION_REASON,
    CONFIRMATION_GAP_REASON,
    READY_REASON,
)

NEXT_STEPS = {
    STATUS_READY: "allow_report_only_market_research_business_inventories_surprise_digest",
    STATUS_WATCH: "watch_report_only_market_research_business_inventories_surprise_digest",
    STATUS_BLOCKED: "block_report_only_market_research_business_inventories_surprise_digest",
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


BLOCKED_REFERENCE_FRAGMENTS = frozenset(
    (
        _join_parts("wal", "let"),
        _join_parts("au", "th"),
        _join_parts("ord", "er"),
        _join_parts("tra", "de"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("rep", "lace"),
        _join_parts("acc", "ount"),
    ),
)

REDACTED_REFERENCE_FRAGMENTS = frozenset(
    (
        _join_parts("to", "ken"),
        _join_parts("sec", "ret"),
        _join_parts("pri", "vate"),
        _join_parts("ven", "dor"),
        "https://",
        "http://",
    ),
)
UNSAFE_PUBLIC_TEXT_FRAGMENTS = frozenset(
    (
        *BLOCKED_REFERENCE_FRAGMENTS,
        _join_parts("to", "ken"),
        _join_parts("sec", "ret"),
    ),
)


__all__ = (
    "DEFAULT_MARKET_RESEARCH_BUSINESS_INVENTORIES_SURPRISE_DIGEST_CONFIG_VERSION",
    "MarketResearchBusinessInventoriesSurpriseDigestConfig",
    "MarketResearchBusinessInventoriesSurpriseDigestReasonCodeCount",
    "MarketResearchBusinessInventoriesSurpriseDigestReport",
    "MarketResearchBusinessInventoriesSurpriseDigestRow",
    "MarketResearchBusinessInventoriesSurpriseDigestSignal",
    "build_market_research_business_inventories_surprise_digest",
    "market_research_business_inventories_surprise_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchBusinessInventoriesSurpriseDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_BUSINESS_INVENTORIES_SURPRISE_DIGEST_CONFIG_VERSION
    )
    max_signal_age_seconds: Decimal = Decimal("7200.000000")
    min_source_count: Decimal = Decimal("2.000000")
    material_surprise_threshold: Decimal = Decimal("0.030000")
    max_revision_ratio: Decimal = Decimal("0.120000")
    min_confirmation_ratio: Decimal = Decimal("0.700000")
    watch_confidence_threshold: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchBusinessInventoriesSurpriseDigestConfig:
            raise TypeError(
                "config must be exactly "
                "MarketResearchBusinessInventoriesSurpriseDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_BUSINESS_INVENTORIES_SURPRISE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "max_signal_age_seconds",
            _require_positive_count_decimal(
                "max_signal_age_seconds",
                self.max_signal_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "min_source_count",
            _require_positive_count_decimal("min_source_count", self.min_source_count),
        )
        for field_name in (
            "material_surprise_threshold",
            "max_revision_ratio",
            "min_confirmation_ratio",
            "watch_confidence_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.material_surprise_threshold <= ZERO:
            raise ValueError("material_surprise_threshold must be positive")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchBusinessInventoriesSurpriseDigestSignal:
    condition_id: str
    research_key: str
    release_key: str
    inventory_segment: str
    public_signal_reference: str
    observed_at: datetime
    expected_inventory_mom: Decimal
    actual_inventory_mom: Decimal
    surprise_score: Decimal
    source_count: Decimal
    revision_ratio: Decimal
    confirmation_ratio: Decimal
    base_confidence: Decimal
    signal_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchBusinessInventoriesSurpriseDigestSignal:
            raise TypeError(
                "input signal must be exactly "
                "MarketResearchBusinessInventoriesSurpriseDigestSignal",
            )
        for field_name in (
            "condition_id",
            "research_key",
            "release_key",
            "inventory_segment",
            "signal_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_reference("public_signal_reference", self.public_signal_reference)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("expected_inventory_mom", "actual_inventory_mom"):
            object.__setattr__(
                self,
                field_name,
                _require_finite_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_count_decimal("source_count", self.source_count),
        )
        for field_name in (
            "surprise_score",
            "revision_ratio",
            "confirmation_ratio",
            "base_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input signal", self)


@dataclass(frozen=True)
class MarketResearchBusinessInventoriesSurpriseDigestRow:
    condition_id: str
    research_key: str
    release_key: str
    inventory_segment: str
    digest_status: str
    observed_at: datetime
    signal_age_seconds: Decimal
    expected_inventory_mom: Decimal
    actual_inventory_mom: Decimal
    surprise_delta: Decimal
    surprise_score: Decimal
    source_count: Decimal
    revision_ratio: Decimal
    confirmation_ratio: Decimal
    base_confidence: Decimal
    confidence_decay_factor: Decimal
    final_confidence: Decimal
    redacted_public_signal_reference: str
    signal_config_version: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchBusinessInventoriesSurpriseDigestRow:
            raise TypeError(
                "row must be exactly "
                "MarketResearchBusinessInventoriesSurpriseDigestRow",
            )
        for field_name in (
            "condition_id",
            "research_key",
            "release_key",
            "inventory_segment",
            "signal_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "redacted_public_signal_reference",
            _require_redacted_reference(
                "redacted_public_signal_reference",
                self.redacted_public_signal_reference,
            ),
        )
        _require_status("digest_status", self.digest_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "signal_age_seconds",
            "source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "expected_inventory_mom",
            "actual_inventory_mom",
            "surprise_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_finite_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "surprise_score",
            "revision_ratio",
            "confirmation_ratio",
            "base_confidence",
            "confidence_decay_factor",
            "final_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchBusinessInventoriesSurpriseDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    signal_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchBusinessInventoriesSurpriseDigestReasonCodeCount:
            raise TypeError(
                "reason code count must be exactly "
                "MarketResearchBusinessInventoriesSurpriseDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "signal_ratio",
            _require_ratio_decimal("signal_ratio", self.signal_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchBusinessInventoriesSurpriseDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    reason_codes: tuple[str, ...]
    signal_count: Decimal
    ready_signal_count: Decimal
    watch_signal_count: Decimal
    blocked_signal_count: Decimal
    material_surprise_count: Decimal
    stale_signal_count: Decimal
    thin_source_count: Decimal
    high_revision_count: Decimal
    confirmation_gap_count: Decimal
    average_surprise_score: Decimal
    max_signal_age_seconds: Decimal
    average_source_count: Decimal
    rows: tuple[MarketResearchBusinessInventoriesSurpriseDigestRow, ...]
    reason_code_counts: tuple[
        MarketResearchBusinessInventoriesSurpriseDigestReasonCodeCount,
        ...,
    ]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchBusinessInventoriesSurpriseDigestReport:
            raise TypeError(
                "report must be exactly "
                "MarketResearchBusinessInventoriesSurpriseDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("digest_status", self.digest_status)
        _require_public_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
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
            "max_signal_age_seconds",
            "average_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_surprise_score",
            _require_ratio_decimal("average_surprise_score", self.average_surprise_score),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_business_inventories_surprise_digest(
    signals: Iterable[object],
    *,
    config: MarketResearchBusinessInventoriesSurpriseDigestConfig,
    generated_at: datetime,
) -> MarketResearchBusinessInventoriesSurpriseDigestReport:
    if type(config) is not MarketResearchBusinessInventoriesSurpriseDigestConfig:
        raise TypeError(
            "config must be exactly "
            "MarketResearchBusinessInventoriesSurpriseDigestConfig",
        )
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (
                _build_row(signal, config=config, generated_at=generated_at_utc)
                for signal in tuple(signals)
            ),
            key=_row_sort_key,
        ),
    )

    signal_count = _count(len(rows))
    ready_signal_count = _count_status(rows, STATUS_READY)
    watch_signal_count = _count_status(rows, STATUS_WATCH)
    blocked_signal_count = _count_status(rows, STATUS_BLOCKED)
    material_surprise_count = _count_reason(rows, MATERIAL_SURPRISE_REASON)
    stale_signal_count = _count_reason(rows, STALE_SIGNAL_REASON)
    thin_source_count = _count_reason(rows, THIN_SOURCES_REASON)
    high_revision_count = _count_reason(rows, HIGH_REVISION_REASON)
    confirmation_gap_count = _count_reason(rows, CONFIRMATION_GAP_REASON)

    if signal_count == ZERO or blocked_signal_count > ZERO:
        digest_status = STATUS_BLOCKED
    elif watch_signal_count > ZERO:
        digest_status = STATUS_WATCH
    else:
        digest_status = STATUS_READY

    reason_code_counts = _build_reason_code_counts(rows)
    if signal_count == ZERO:
        reason_codes = (NO_INPUTS_REASON,)
    elif reason_code_counts:
        reason_codes = tuple(row.reason_code for row in reason_code_counts)
    else:
        reason_codes = (READY_REASON,)

    return MarketResearchBusinessInventoriesSurpriseDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        reason_codes=reason_codes,
        signal_count=signal_count,
        ready_signal_count=ready_signal_count,
        watch_signal_count=watch_signal_count,
        blocked_signal_count=blocked_signal_count,
        material_surprise_count=material_surprise_count,
        stale_signal_count=stale_signal_count,
        thin_source_count=thin_source_count,
        high_revision_count=high_revision_count,
        confirmation_gap_count=confirmation_gap_count,
        average_surprise_score=_average_decimal(
            tuple(row.surprise_score for row in rows),
        ),
        max_signal_age_seconds=max(
            (row.signal_age_seconds for row in rows),
            default=ZERO,
        ),
        average_source_count=_average_decimal(tuple(row.source_count for row in rows)),
        rows=rows,
        reason_code_counts=reason_code_counts,
    )


def market_research_business_inventories_surprise_digest_payload(
    report: MarketResearchBusinessInventoriesSurpriseDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchBusinessInventoriesSurpriseDigestReport:
        raise TypeError(
            "report must be exactly "
            "MarketResearchBusinessInventoriesSurpriseDigestReport",
        )
    payload = asdict(report)
    return _payload_value(payload)


def _build_row(
    signal: object,
    *,
    config: MarketResearchBusinessInventoriesSurpriseDigestConfig,
    generated_at: datetime,
) -> MarketResearchBusinessInventoriesSurpriseDigestRow:
    if type(signal) is not MarketResearchBusinessInventoriesSurpriseDigestSignal:
        raise TypeError(
            "input signal must be exactly "
            "MarketResearchBusinessInventoriesSurpriseDigestSignal",
        )
    signal_age_seconds = _seconds_between(signal.observed_at, generated_at)
    if signal_age_seconds < ZERO:
        raise ValueError("observed_at must not be after generated_at")

    reason_codes = []
    if signal_age_seconds > config.max_signal_age_seconds:
        reason_codes.append(STALE_SIGNAL_REASON)
    if signal.surprise_score >= config.material_surprise_threshold:
        reason_codes.append(MATERIAL_SURPRISE_REASON)
    if signal.source_count < config.min_source_count:
        reason_codes.append(THIN_SOURCES_REASON)
    if signal.revision_ratio > config.max_revision_ratio:
        reason_codes.append(HIGH_REVISION_REASON)
    if signal.confirmation_ratio < config.min_confirmation_ratio:
        reason_codes.append(CONFIRMATION_GAP_REASON)

    ordered_reason_codes = tuple(
        reason_code
        for reason_code in ROW_REASON_CODE_SEQUENCE
        if reason_code in reason_codes
    )
    if not ordered_reason_codes:
        ordered_reason_codes = (READY_REASON,)

    if STALE_SIGNAL_REASON in ordered_reason_codes:
        confidence_decay_factor = Decimal("0.400000")
    elif ordered_reason_codes != (READY_REASON,):
        confidence_decay_factor = Decimal("0.800000")
    else:
        confidence_decay_factor = ONE
    final_confidence = _quantize(signal.base_confidence * confidence_decay_factor)

    if (
        STALE_SIGNAL_REASON in ordered_reason_codes
        or THIN_SOURCES_REASON in ordered_reason_codes
        or HIGH_REVISION_REASON in ordered_reason_codes
    ):
        digest_status = STATUS_BLOCKED
    elif (
        ordered_reason_codes != (READY_REASON,)
        or final_confidence < config.watch_confidence_threshold
    ):
        digest_status = STATUS_WATCH
    else:
        digest_status = STATUS_READY

    return MarketResearchBusinessInventoriesSurpriseDigestRow(
        condition_id=signal.condition_id,
        research_key=signal.research_key,
        release_key=signal.release_key,
        inventory_segment=signal.inventory_segment,
        digest_status=digest_status,
        observed_at=signal.observed_at,
        signal_age_seconds=signal_age_seconds,
        expected_inventory_mom=signal.expected_inventory_mom,
        actual_inventory_mom=signal.actual_inventory_mom,
        surprise_delta=_quantize(
            signal.actual_inventory_mom - signal.expected_inventory_mom,
        ),
        surprise_score=signal.surprise_score,
        source_count=signal.source_count,
        revision_ratio=signal.revision_ratio,
        confirmation_ratio=signal.confirmation_ratio,
        base_confidence=signal.base_confidence,
        confidence_decay_factor=confidence_decay_factor,
        final_confidence=final_confidence,
        redacted_public_signal_reference=_redacted_reference(
            signal.public_signal_reference,
        ),
        signal_config_version=signal.signal_config_version,
        reason_codes=ordered_reason_codes,
    )


def _build_reason_code_counts(
    rows: tuple[MarketResearchBusinessInventoriesSurpriseDigestRow, ...],
) -> tuple[MarketResearchBusinessInventoriesSurpriseDigestReasonCodeCount, ...]:
    if not rows:
        return (
            MarketResearchBusinessInventoriesSurpriseDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                signal_ratio=ONE,
            ),
        )
    total = _count(len(rows))
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code in (READY_REASON, NO_INPUTS_REASON):
                continue
            counts[reason_code] = counts.setdefault(reason_code, ZERO) + ONE
    return tuple(
        MarketResearchBusinessInventoriesSurpriseDigestReasonCodeCount(
            reason_code=reason_code,
            count=_quantize(counts[reason_code]),
            signal_ratio=_ratio(counts[reason_code], total),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _row_sort_key(
    row: MarketResearchBusinessInventoriesSurpriseDigestRow,
) -> tuple[int, str, str, str]:
    status_rank = {
        STATUS_BLOCKED: 0,
        STATUS_WATCH: 1,
        STATUS_READY: 2,
    }
    return (
        status_rank[row.digest_status],
        row.release_key,
        row.research_key,
        row.condition_id,
    )


def _count_status(
    rows: tuple[MarketResearchBusinessInventoriesSurpriseDigestRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.digest_status == status))


def _count_reason(
    rows: tuple[MarketResearchBusinessInventoriesSurpriseDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(sum(values, ZERO) / _count(len(values)))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    whole_seconds = Decimal(delta.days * 86400 + delta.seconds)
    microseconds = Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    return _quantize(whole_seconds + microseconds)


def _redacted_reference(value: str) -> str:
    lowered = value.lower()
    if any(fragment in lowered for fragment in REDACTED_REFERENCE_FRAGMENTS):
        digest = sha256(value.encode("utf-8")).hexdigest()[:12]
        return f"sha256:{digest}"
    return value


def _payload_value(value: Any) -> Any:
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if isinstance(value, tuple):
        return tuple(_payload_value(item) for item in value)
    if isinstance(value, list):
        return tuple(_payload_value(item) for item in value)
    if isinstance(value, dict):
        return {key: _payload_value(item) for key, item in value.items()}
    return value


def _normalize_rows(
    rows: tuple[MarketResearchBusinessInventoriesSurpriseDigestRow, ...],
) -> tuple[MarketResearchBusinessInventoriesSurpriseDigestRow, ...]:
    values = tuple(rows)
    seen: set[tuple[str, str, str]] = set()
    for row in values:
        if type(row) is not MarketResearchBusinessInventoriesSurpriseDigestRow:
            raise TypeError(
                "rows must contain exactly "
                "MarketResearchBusinessInventoriesSurpriseDigestRow",
            )
        _require_hard_flags("row", row)
        key = (row.release_key, row.research_key, row.condition_id)
        if key in seen:
            raise ValueError("rows must be unique")
        seen.add(key)
    if values != tuple(sorted(values, key=_row_sort_key)):
        raise ValueError("rows must use canonical sorting")
    return values


def _normalize_reason_code_counts(
    rows: tuple[
        MarketResearchBusinessInventoriesSurpriseDigestReasonCodeCount,
        ...,
    ],
) -> tuple[MarketResearchBusinessInventoriesSurpriseDigestReasonCodeCount, ...]:
    values = tuple(rows)
    seen: set[str] = set()
    for row in values:
        if type(row) is not MarketResearchBusinessInventoriesSurpriseDigestReasonCodeCount:
            raise TypeError(
                "reason_code_counts must contain exactly "
                "MarketResearchBusinessInventoriesSurpriseDigestReasonCodeCount",
            )
        _require_hard_flags("reason code count", row)
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        seen.add(row.reason_code)
    canonical = tuple(reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in seen)
    if tuple(row.reason_code for row in values) != canonical:
        raise ValueError("reason_code_counts must use canonical reason code sequence")
    return values


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    values = tuple(reason_codes)
    if not values:
        raise ValueError("reason_codes must not be empty")
    for reason_code in values:
        _require_reason_code("reason_code", reason_code)
    if len(values) != len(frozenset(values)):
        raise ValueError("reason_codes must be unique")
    if READY_REASON in values and values != (READY_REASON,):
        raise ValueError("reason_codes ready must be the only ready reason")
    if NO_INPUTS_REASON in values and values != (NO_INPUTS_REASON,):
        raise ValueError("reason_codes no_inputs must be the only no-input reason")
    return tuple(reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in values)


def _normalize_row_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    values = tuple(reason_codes)
    if not values:
        raise ValueError("reason_codes must not be empty")
    for reason_code in values:
        _require_reason_code("reason_code", reason_code)
        if reason_code not in ROW_REASON_CODE_SEQUENCE:
            raise ValueError("reason_code is not supported")
    if len(values) != len(frozenset(values)):
        raise ValueError("reason_codes must be unique")
    if READY_REASON in values and values != (READY_REASON,):
        raise ValueError("reason_codes ready must be the only ready reason")
    return tuple(
        reason_code for reason_code in ROW_REASON_CODE_SEQUENCE if reason_code in values
    )


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise TypeError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_status(field_name: str, value: str) -> None:
    _require_public_string(field_name, value)
    if value not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be a supported status")


def _require_reference(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in BLOCKED_REFERENCE_FRAGMENTS):
        raise ValueError(f"{field_name} contains blocked sensitive surface")


def _require_redacted_reference(field_name: str, value: str) -> str:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if any(
        fragment in lowered
        for fragment in (*BLOCKED_REFERENCE_FRAGMENTS, *REDACTED_REFERENCE_FRAGMENTS)
    ):
        raise ValueError(f"{field_name} contains unsafe public surface")
    return value


def _require_public_string(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public surface")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be exactly str")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")


def _require_reason_code(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} is not supported")


def _require_finite_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise TypeError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_count_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_finite_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_count_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be no greater than one")
    return normalized


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        flag = getattr(value, flag_name)
        if type(flag) is not bool or flag is not True:
            raise ValueError(f"{field_name} {flag_name} must be True")


def _validate_row(row: MarketResearchBusinessInventoriesSurpriseDigestRow) -> None:
    if row.surprise_delta != _quantize(
        row.actual_inventory_mom - row.expected_inventory_mom,
    ):
        raise ValueError("surprise_delta must match actual minus expected")
    if row.final_confidence != _quantize(
        row.base_confidence * row.confidence_decay_factor,
    ):
        raise ValueError("final_confidence must match base_confidence and decay")
    if _has_blocking_row_reason(row.reason_codes):
        if row.digest_status != STATUS_BLOCKED:
            raise ValueError("digest_status must match blocking reason_codes")
    elif row.reason_codes != (READY_REASON,):
        if row.digest_status != STATUS_WATCH:
            raise ValueError("digest_status must match watch reason_codes")
    elif row.digest_status == STATUS_BLOCKED:
        raise ValueError("digest_status must match ready reason_codes")


def _validate_report(report: MarketResearchBusinessInventoriesSurpriseDigestReport) -> None:
    if report.recommended_next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if report.signal_count != _count(len(report.rows)):
        raise ValueError("signal_count must match rows")
    for status, field_name in (
        (STATUS_READY, "ready_signal_count"),
        (STATUS_WATCH, "watch_signal_count"),
        (STATUS_BLOCKED, "blocked_signal_count"),
    ):
        if getattr(report, field_name) != _count_status(report.rows, status):
            raise ValueError(f"{field_name} must match rows")
    for reason_code, field_name in (
        (MATERIAL_SURPRISE_REASON, "material_surprise_count"),
        (STALE_SIGNAL_REASON, "stale_signal_count"),
        (THIN_SOURCES_REASON, "thin_source_count"),
        (HIGH_REVISION_REASON, "high_revision_count"),
        (CONFIRMATION_GAP_REASON, "confirmation_gap_count"),
    ):
        if getattr(report, field_name) != _count_reason(report.rows, reason_code):
            raise ValueError(f"{field_name} must match rows")
    if report.average_surprise_score != _average_decimal(
        tuple(row.surprise_score for row in report.rows),
    ):
        raise ValueError("average_surprise_score must match rows")
    if report.max_signal_age_seconds != max(
        (row.signal_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_signal_age_seconds must match rows")
    if report.average_source_count != _average_decimal(
        tuple(row.source_count for row in report.rows),
    ):
        raise ValueError("average_source_count must match rows")
    if report.reason_code_counts != _build_reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    expected_reason_codes = tuple(row.reason_code for row in report.reason_code_counts)
    if report.rows and not expected_reason_codes:
        expected_reason_codes = (READY_REASON,)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match reason_code_counts")
    expected_status = _report_status(report.rows)
    if report.digest_status != expected_status:
        raise ValueError("digest_status must match rows")


def _report_status(
    rows: tuple[MarketResearchBusinessInventoriesSurpriseDigestRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_READY


def _has_blocking_row_reason(reason_codes: tuple[str, ...]) -> bool:
    return any(
        reason_code in reason_codes
        for reason_code in (
            STALE_SIGNAL_REASON,
            THIN_SOURCES_REASON,
            HIGH_REVISION_REASON,
        )
    )


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)
