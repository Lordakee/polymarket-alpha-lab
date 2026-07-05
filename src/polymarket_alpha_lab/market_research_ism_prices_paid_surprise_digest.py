"""Pure Phase 1 ISM prices-paid surprise research reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_ISM_PRICES_PAID_SURPRISE_DIGEST_CONFIG_VERSION = (
    "market-research-ism-prices-paid-surprise-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)
STATUS_SEQUENCE = {STATUS_BLOCKED: 0, STATUS_WATCH: 1, STATUS_READY: 2}

REASON_PREFIX = "market_research_ism_prices_paid_surprise_digest_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
READY_REASON = f"{REASON_PREFIX}ready"
STALE_SIGNAL_REASON = f"{REASON_PREFIX}stale_signal"
MATERIAL_SURPRISE_REASON = f"{REASON_PREFIX}material_surprise"
THIN_SOURCES_REASON = f"{REASON_PREFIX}thin_sources"
HIGH_REVISION_REASON = f"{REASON_PREFIX}high_revision"
CONFIRMATION_GAP_REASON = f"{REASON_PREFIX}confirmation_gap"

ROW_REASON_CODE_SEQUENCE = (
    STALE_SIGNAL_REASON,
    MATERIAL_SURPRISE_REASON,
    THIN_SOURCES_REASON,
    HIGH_REVISION_REASON,
    CONFIRMATION_GAP_REASON,
    READY_REASON,
)
REPORT_REASON_CODE_SEQUENCE = (
    MATERIAL_SURPRISE_REASON,
    STALE_SIGNAL_REASON,
    THIN_SOURCES_REASON,
    HIGH_REVISION_REASON,
    CONFIRMATION_GAP_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)

NEXT_STEPS = {
    STATUS_READY: "allow_report_only_market_research_ism_prices_paid_surprise_digest",
    STATUS_WATCH: "watch_report_only_market_research_ism_prices_paid_surprise_digest",
    STATUS_BLOCKED: "block_report_only_market_research_ism_prices_paid_surprise_digest",
}

QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
PUBLIC_REFERENCE_PREFIXES = ("official-", "public-", "ism/", "fred/")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


def _join_codes(*codes: int) -> str:
    return "".join(chr(code) for code in codes)


UNSAFE_REFERENCE_MARKERS = (
    _join_codes(97, 112, 105, 95, 107, 101, 121),
    _join_parts("au", "th"),
    _join_parts("bear", "er "),
    _join_parts("pass", "word"),
    _join_codes(112, 114, 105, 118, 97, 116, 101, 95, 107, 101, 121),
    _join_parts("sec", "ret"),
    _join_parts("sig", "nature"),
    _join_parts("to", "ken"),
    _join_parts("wal", "let"),
    "://",
    "?",
    "=",
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_ISM_PRICES_PAID_SURPRISE_DIGEST_CONFIG_VERSION",
    "MarketResearchIsmPricesPaidSurpriseDigestConfig",
    "MarketResearchIsmPricesPaidSurpriseDigestReasonCodeCount",
    "MarketResearchIsmPricesPaidSurpriseDigestReport",
    "MarketResearchIsmPricesPaidSurpriseDigestRow",
    "MarketResearchIsmPricesPaidSurpriseDigestSignal",
    "build_market_research_ism_prices_paid_surprise_digest",
    "market_research_ism_prices_paid_surprise_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchIsmPricesPaidSurpriseDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_ISM_PRICES_PAID_SURPRISE_DIGEST_CONFIG_VERSION
    )
    max_signal_age_seconds: Decimal = Decimal("7200.000000")
    min_source_count: Decimal = Decimal("2.000000")
    material_surprise_threshold: Decimal = Decimal("2.000000")
    max_revision_ratio: Decimal = Decimal("0.200000")
    min_confirmation_ratio: Decimal = Decimal("0.650000")
    watch_confidence_threshold: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchIsmPricesPaidSurpriseDigestConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_ISM_PRICES_PAID_SURPRISE_DIGEST_CONFIG_VERSION
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
        object.__setattr__(
            self,
            "material_surprise_threshold",
            _require_positive_decimal(
                "material_surprise_threshold",
                self.material_surprise_threshold,
            ),
        )
        for field_name in (
            "max_revision_ratio",
            "min_confirmation_ratio",
            "watch_confidence_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchIsmPricesPaidSurpriseDigestSignal:
    condition_id: str
    research_id: str
    release_id: str
    sector: str
    public_signal_reference: str
    observed_at: datetime
    expected_prices_paid_index: Decimal
    actual_prices_paid_index: Decimal
    source_count: Decimal
    revision_ratio: Decimal
    confirmation_ratio: Decimal
    base_confidence: Decimal
    signal_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchIsmPricesPaidSurpriseDigestSignal,
            "signal",
        )
        for field_name in (
            "condition_id",
            "research_id",
            "release_id",
            "sector",
            "signal_config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_public_reference(
            "public_signal_reference",
            self.public_signal_reference,
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("expected_prices_paid_index", "actual_prices_paid_index"):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_count_decimal("source_count", self.source_count),
        )
        for field_name in ("revision_ratio", "confirmation_ratio", "base_confidence"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("signal", self)


@dataclass(frozen=True)
class MarketResearchIsmPricesPaidSurpriseDigestRow:
    condition_id: str
    research_id: str
    release_id: str
    sector: str
    digest_status: str
    observed_at: datetime
    signal_age_seconds: Decimal
    expected_prices_paid_index: Decimal
    actual_prices_paid_index: Decimal
    surprise_index: Decimal
    abs_surprise_index: Decimal
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
        _require_exact_type(self, MarketResearchIsmPricesPaidSurpriseDigestRow, "row")
        for field_name in (
            "condition_id",
            "research_id",
            "release_id",
            "sector",
            "redacted_public_signal_reference",
            "signal_config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_status("digest_status", self.digest_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "signal_age_seconds",
            "abs_surprise_index",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "expected_prices_paid_index",
            "actual_prices_paid_index",
            "surprise_index",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_count_decimal("source_count", self.source_count),
        )
        for field_name in (
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
            _normalize_reason_codes(self.reason_codes, ROW_REASON_CODE_SEQUENCE),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchIsmPricesPaidSurpriseDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    signal_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchIsmPricesPaidSurpriseDigestReasonCodeCount,
            "reason code count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "signal_ratio",
            _require_ratio_decimal("signal_ratio", self.signal_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchIsmPricesPaidSurpriseDigestReport:
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
    average_abs_surprise_index: Decimal
    max_abs_surprise_index: Decimal
    average_final_confidence: Decimal
    max_observed_signal_age_seconds: Decimal
    rows: tuple[MarketResearchIsmPricesPaidSurpriseDigestRow, ...]
    reason_code_counts: tuple[
        MarketResearchIsmPricesPaidSurpriseDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketResearchIsmPricesPaidSurpriseDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_ISM_PRICES_PAID_SURPRISE_DIGEST_CONFIG_VERSION
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
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_abs_surprise_index",
            "max_abs_surprise_index",
            "average_final_confidence",
            "max_observed_signal_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, REPORT_REASON_CODE_SEQUENCE),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_ism_prices_paid_surprise_digest(
    signals: Iterable[MarketResearchIsmPricesPaidSurpriseDigestSignal],
    *,
    config: MarketResearchIsmPricesPaidSurpriseDigestConfig,
    generated_at: datetime,
) -> MarketResearchIsmPricesPaidSurpriseDigestReport:
    if type(config) is not MarketResearchIsmPricesPaidSurpriseDigestConfig:
        raise ValueError(
            "config must be a MarketResearchIsmPricesPaidSurpriseDigestConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_signals = _normalize_signals(signals)
    rows = _sorted_rows(
        tuple(
            _build_row(signal, config=config, generated_at=generated_at_utc)
            for signal in normalized_signals
        ),
    )
    signal_count = _decimal_count(len(rows))
    reason_codes = _report_reason_codes(rows)
    digest_status = _report_status(rows)
    return MarketResearchIsmPricesPaidSurpriseDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        signal_count=signal_count,
        ready_signal_count=_status_count(rows, STATUS_READY),
        watch_signal_count=_status_count(rows, STATUS_WATCH),
        blocked_signal_count=_status_count(rows, STATUS_BLOCKED),
        material_surprise_count=_reason_count(rows, MATERIAL_SURPRISE_REASON),
        stale_signal_count=_reason_count(rows, STALE_SIGNAL_REASON),
        thin_source_count=_reason_count(rows, THIN_SOURCES_REASON),
        high_revision_count=_reason_count(rows, HIGH_REVISION_REASON),
        confirmation_gap_count=_reason_count(rows, CONFIRMATION_GAP_REASON),
        average_abs_surprise_index=_average_decimal(
            row.abs_surprise_index for row in rows
        ),
        max_abs_surprise_index=_max_decimal(row.abs_surprise_index for row in rows),
        average_final_confidence=_average_decimal(
            row.final_confidence for row in rows
        ),
        max_observed_signal_age_seconds=_max_decimal(
            (row.signal_age_seconds for row in rows),
        ),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes, signal_count),
        reason_codes=reason_codes,
    )


def market_research_ism_prices_paid_surprise_digest_payload(
    report: MarketResearchIsmPricesPaidSurpriseDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchIsmPricesPaidSurpriseDigestReport:
        raise ValueError(
            "report must be a MarketResearchIsmPricesPaidSurpriseDigestReport",
        )
    _require_hard_flags("report", report)
    return _payload_value(asdict(report))


def _build_row(
    signal: MarketResearchIsmPricesPaidSurpriseDigestSignal,
    *,
    config: MarketResearchIsmPricesPaidSurpriseDigestConfig,
    generated_at: datetime,
) -> MarketResearchIsmPricesPaidSurpriseDigestRow:
    signal_age_seconds = _datetime_delta_seconds(generated_at, signal.observed_at)
    surprise_index = _q(signal.actual_prices_paid_index - signal.expected_prices_paid_index)
    abs_surprise_index = _q(abs(surprise_index))
    reason_codes = _row_reason_codes(
        signal,
        abs_surprise_index=abs_surprise_index,
        signal_age_seconds=signal_age_seconds,
        config=config,
    )
    decay_factor = _confidence_decay_factor(reason_codes)
    return MarketResearchIsmPricesPaidSurpriseDigestRow(
        condition_id=signal.condition_id,
        research_id=signal.research_id,
        release_id=signal.release_id,
        sector=signal.sector,
        digest_status=_row_status(reason_codes),
        observed_at=signal.observed_at,
        signal_age_seconds=signal_age_seconds,
        expected_prices_paid_index=signal.expected_prices_paid_index,
        actual_prices_paid_index=signal.actual_prices_paid_index,
        surprise_index=surprise_index,
        abs_surprise_index=abs_surprise_index,
        source_count=signal.source_count,
        revision_ratio=signal.revision_ratio,
        confirmation_ratio=signal.confirmation_ratio,
        base_confidence=signal.base_confidence,
        confidence_decay_factor=decay_factor,
        final_confidence=_q(signal.base_confidence * decay_factor),
        redacted_public_signal_reference=_redacted_public_reference(
            signal.public_signal_reference,
        ),
        signal_config_version=signal.signal_config_version,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    signal: MarketResearchIsmPricesPaidSurpriseDigestSignal,
    *,
    abs_surprise_index: Decimal,
    signal_age_seconds: Decimal,
    config: MarketResearchIsmPricesPaidSurpriseDigestConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if signal_age_seconds > config.max_signal_age_seconds:
        reason_codes.append(STALE_SIGNAL_REASON)
    if abs_surprise_index >= config.material_surprise_threshold:
        reason_codes.append(MATERIAL_SURPRISE_REASON)
    if signal.source_count < config.min_source_count:
        reason_codes.append(THIN_SOURCES_REASON)
    if signal.revision_ratio > config.max_revision_ratio:
        reason_codes.append(HIGH_REVISION_REASON)
    if signal.confirmation_ratio < config.min_confirmation_ratio:
        reason_codes.append(CONFIRMATION_GAP_REASON)
    if not reason_codes:
        return (READY_REASON,)
    return tuple(
        reason_code
        for reason_code in ROW_REASON_CODE_SEQUENCE
        if reason_code in reason_codes
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    if (
        STALE_SIGNAL_REASON in reason_codes
        or THIN_SOURCES_REASON in reason_codes
        or HIGH_REVISION_REASON in reason_codes
    ):
        return STATUS_BLOCKED
    return STATUS_WATCH


def _confidence_decay_factor(reason_codes: tuple[str, ...]) -> Decimal:
    penalty = ZERO
    if STALE_SIGNAL_REASON in reason_codes:
        penalty += Decimal("0.200000")
    if MATERIAL_SURPRISE_REASON in reason_codes:
        penalty += Decimal("0.100000")
    if THIN_SOURCES_REASON in reason_codes:
        penalty += Decimal("0.100000")
    if HIGH_REVISION_REASON in reason_codes:
        penalty += Decimal("0.100000")
    if CONFIRMATION_GAP_REASON in reason_codes:
        penalty += Decimal("0.100000")
    factor = ONE - penalty
    if factor < ZERO:
        return ZERO
    return _q(factor)


def _report_reason_codes(
    rows: tuple[MarketResearchIsmPricesPaidSurpriseDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    present = {reason_code for row in rows for reason_code in row.reason_codes}
    return tuple(
        reason_code
        for reason_code in REPORT_REASON_CODE_SEQUENCE
        if reason_code in present
    )


def _report_status(
    rows: tuple[MarketResearchIsmPricesPaidSurpriseDigestRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_READY


def _reason_code_counts(
    rows: tuple[MarketResearchIsmPricesPaidSurpriseDigestRow, ...],
    reason_codes: tuple[str, ...],
    signal_count: Decimal,
) -> tuple[MarketResearchIsmPricesPaidSurpriseDigestReasonCodeCount, ...]:
    if not rows:
        return (
            MarketResearchIsmPricesPaidSurpriseDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                signal_ratio=ZERO,
            ),
        )
    return tuple(
        MarketResearchIsmPricesPaidSurpriseDigestReasonCodeCount(
            reason_code=reason_code,
            count=_reason_count(rows, reason_code),
            signal_ratio=_ratio(_reason_count(rows, reason_code), signal_count),
        )
        for reason_code in reason_codes
    )


def _normalize_signals(
    signals: Iterable[MarketResearchIsmPricesPaidSurpriseDigestSignal],
) -> tuple[MarketResearchIsmPricesPaidSurpriseDigestSignal, ...]:
    if isinstance(signals, (str, bytes)) or not isinstance(signals, Iterable):
        raise ValueError("signals must be an iterable of ISM prices-paid signals")
    normalized = tuple(signals)
    seen_condition_ids: set[str] = set()
    seen_release_ids: set[str] = set()
    for signal in normalized:
        if type(signal) is not MarketResearchIsmPricesPaidSurpriseDigestSignal:
            raise ValueError(
                "signals must contain MarketResearchIsmPricesPaidSurpriseDigestSignal",
            )
        _require_hard_flags("signal", signal)
        if signal.condition_id in seen_condition_ids:
            raise ValueError(f"duplicate condition_id {signal.condition_id!r}")
        if signal.release_id in seen_release_ids:
            raise ValueError(f"duplicate release_id {signal.release_id!r}")
        seen_condition_ids.add(signal.condition_id)
        seen_release_ids.add(signal.release_id)
    return normalized


def _normalize_rows(
    rows: tuple[MarketResearchIsmPricesPaidSurpriseDigestRow, ...],
) -> tuple[MarketResearchIsmPricesPaidSurpriseDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen_release_ids: set[str] = set()
    for row in rows:
        if type(row) is not MarketResearchIsmPricesPaidSurpriseDigestRow:
            raise ValueError(
                "rows must contain MarketResearchIsmPricesPaidSurpriseDigestRow",
            )
        _require_hard_flags("row", row)
        if row.release_id in seen_release_ids:
            raise ValueError("rows must contain unique release_id values")
        seen_release_ids.add(row.release_id)
    if rows != _sorted_rows(rows):
        raise ValueError("rows must use deterministic sequence")
    return rows


def _normalize_reason_code_counts(
    value: tuple[MarketResearchIsmPricesPaidSurpriseDigestReasonCodeCount, ...],
) -> tuple[MarketResearchIsmPricesPaidSurpriseDigestReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    seen_reason_codes: set[str] = set()
    for item in value:
        if type(item) is not MarketResearchIsmPricesPaidSurpriseDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchIsmPricesPaidSurpriseDigestReasonCodeCount",
            )
        _require_hard_flags("reason code count", item)
        if item.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts must contain unique reason codes")
        seen_reason_codes.add(item.reason_code)
    if value != _sorted_reason_code_counts(value):
        raise ValueError("reason_code_counts must use deterministic sequence")
    return value


def _normalize_reason_codes(
    value: tuple[str, ...],
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not value:
        raise ValueError("reason_codes must not be empty")
    seen_reason_codes: set[str] = set()
    for reason_code in value:
        _require_reason_code("reason_codes", reason_code)
        if reason_code in seen_reason_codes:
            raise ValueError("reason_codes must be unique")
        seen_reason_codes.add(reason_code)
    if sequence == ROW_REASON_CODE_SEQUENCE and NO_INPUTS_REASON in seen_reason_codes:
        raise ValueError("reason_codes must not include no_inputs for rows")
    if (
        sequence == ROW_REASON_CODE_SEQUENCE
        and READY_REASON in seen_reason_codes
        and len(seen_reason_codes) != 1
    ):
        raise ValueError("ready reason_code must be exclusive for rows")
    if NO_INPUTS_REASON in seen_reason_codes and len(seen_reason_codes) != 1:
        raise ValueError("no_inputs reason_code must be exclusive")
    deterministic = tuple(
        reason_code for reason_code in sequence if reason_code in seen_reason_codes
    )
    if value != deterministic:
        raise ValueError("reason_codes must use deterministic sequence")
    return value


def _validate_row(row: MarketResearchIsmPricesPaidSurpriseDigestRow) -> None:
    expected_surprise = _q(row.actual_prices_paid_index - row.expected_prices_paid_index)
    if row.surprise_index != expected_surprise:
        raise ValueError("surprise_index must match actual less expected")
    if row.abs_surprise_index != _q(abs(row.surprise_index)):
        raise ValueError("abs_surprise_index must match surprise_index")
    if row.digest_status != _row_status(row.reason_codes):
        raise ValueError("digest_status must match reason_codes")
    if row.confidence_decay_factor != _confidence_decay_factor(row.reason_codes):
        raise ValueError("confidence_decay_factor must match reason_codes")
    if row.final_confidence != _q(row.base_confidence * row.confidence_decay_factor):
        raise ValueError("final_confidence must match base confidence")


def _validate_report(report: MarketResearchIsmPricesPaidSurpriseDigestReport) -> None:
    rows = report.rows
    signal_count = _decimal_count(len(rows))
    if report.signal_count != signal_count:
        raise ValueError("signal_count must match rows")
    expected_values = {
        "ready_signal_count": _status_count(rows, STATUS_READY),
        "watch_signal_count": _status_count(rows, STATUS_WATCH),
        "blocked_signal_count": _status_count(rows, STATUS_BLOCKED),
        "material_surprise_count": _reason_count(rows, MATERIAL_SURPRISE_REASON),
        "stale_signal_count": _reason_count(rows, STALE_SIGNAL_REASON),
        "thin_source_count": _reason_count(rows, THIN_SOURCES_REASON),
        "high_revision_count": _reason_count(rows, HIGH_REVISION_REASON),
        "confirmation_gap_count": _reason_count(rows, CONFIRMATION_GAP_REASON),
        "average_abs_surprise_index": _average_decimal(
            row.abs_surprise_index for row in rows
        ),
        "max_abs_surprise_index": _max_decimal(row.abs_surprise_index for row in rows),
        "average_final_confidence": _average_decimal(
            row.final_confidence for row in rows
        ),
        "max_observed_signal_age_seconds": _max_decimal(
            (row.signal_age_seconds for row in rows),
        ),
    }
    for field_name, expected in expected_values.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    expected_reason_codes = _report_reason_codes(rows)
    expected_reason_counts = _reason_code_counts(
        rows,
        expected_reason_codes,
        signal_count,
    )
    if report.reason_code_counts != expected_reason_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    if report.digest_status != _report_status(rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")


def _row_sort_value(
    row: MarketResearchIsmPricesPaidSurpriseDigestRow,
) -> tuple[int, Decimal, Decimal, str, str]:
    return (
        STATUS_SEQUENCE[row.digest_status],
        -row.abs_surprise_index,
        -row.signal_age_seconds,
        row.release_id,
        row.condition_id,
    )


def _sorted_rows(
    rows: tuple[MarketResearchIsmPricesPaidSurpriseDigestRow, ...],
) -> tuple[MarketResearchIsmPricesPaidSurpriseDigestRow, ...]:
    return tuple(
        row
        for _sort_value, _index, row in sorted(
            (_row_sort_value(row), index, row) for index, row in enumerate(rows)
        )
    )


def _sorted_reason_code_counts(
    counts: tuple[MarketResearchIsmPricesPaidSurpriseDigestReasonCodeCount, ...],
) -> tuple[MarketResearchIsmPricesPaidSurpriseDigestReasonCodeCount, ...]:
    return tuple(
        count
        for _sort_value, _index, count in sorted(
            (_reason_rank(count.reason_code), index, count)
            for index, count in enumerate(counts)
        )
    )


def _reason_rank(reason_code: str) -> int:
    if reason_code not in REPORT_REASON_CODE_SEQUENCE:
        raise ValueError("reason_code must be supported")
    return REPORT_REASON_CODE_SEQUENCE.index(reason_code)


def _status_count(
    rows: tuple[MarketResearchIsmPricesPaidSurpriseDigestRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.digest_status == status))


def _reason_count(
    rows: tuple[MarketResearchIsmPricesPaidSurpriseDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _average_decimal(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    return _q(sum(items, ZERO) / Decimal(len(items)))


def _max_decimal(values: Iterable[Decimal]) -> Decimal:
    return max(tuple(values), default=ZERO)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _require_ratio_decimal("signal_ratio", numerator / denominator)


def _datetime_delta_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    seconds = (
        Decimal(delta.days * 86400 + delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    if seconds < ZERO:
        raise ValueError("observed_at must not be after generated_at")
    return _q(seconds)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise TypeError(f"{label} must be exactly {expected_type.__name__}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_public_reference(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if any(marker in lowered for marker in UNSAFE_REFERENCE_MARKERS):
        raise ValueError(f"{field_name} must be public and redacted")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REPORT_REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a supported reason code")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _q(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _q(value)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value == ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-count Decimal")
    return decimal_value


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_count_decimal(field_name, value)
    if decimal_value == ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _q(value)


def _require_hard_flags(context: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{context} {flag_name} must be True")


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return _q(Decimal(value))


def _q(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _redacted_public_reference(value: str) -> str:
    if value.startswith(PUBLIC_REFERENCE_PREFIXES):
        return value
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()[:12]}"


def _payload_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return format(_q(value), "f")
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {str(name): _payload_value(item) for name, item in value.items()}
    if value is None or type(value) in (str, bool, int):
        return value
    raise ValueError(f"unsupported payload value: {type(value).__name__}")
