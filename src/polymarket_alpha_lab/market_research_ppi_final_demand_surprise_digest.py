"""Pure Phase 1 PPI final demand surprise research reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_PPI_FINAL_DEMAND_SURPRISE_DIGEST_CONFIG_VERSION = (
    "market-research-ppi-final-demand-surprise-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

REASON_PREFIX = "market_research_ppi_final_demand_surprise_digest_"
MATERIAL_SURPRISE_REASON = f"{REASON_PREFIX}material_surprise"
CONFIRMATION_GAP_REASON = f"{REASON_PREFIX}confirmation_gap"
STALE_RELEASE_REASON = f"{REASON_PREFIX}stale_release"
THIN_SOURCES_REASON = f"{REASON_PREFIX}thin_sources"
HIGH_REVISION_REASON = f"{REASON_PREFIX}high_revision"
READY_REASON = f"{REASON_PREFIX}ready"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"

ROW_REASON_CODE_SEQUENCE = (
    MATERIAL_SURPRISE_REASON,
    CONFIRMATION_GAP_REASON,
    STALE_RELEASE_REASON,
    THIN_SOURCES_REASON,
    HIGH_REVISION_REASON,
    READY_REASON,
)
REPORT_REASON_CODE_SEQUENCE = (
    MATERIAL_SURPRISE_REASON,
    CONFIRMATION_GAP_REASON,
    STALE_RELEASE_REASON,
    THIN_SOURCES_REASON,
    HIGH_REVISION_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)

NEXT_STEPS = {
    STATUS_READY: "allow_report_only_market_research_ppi_final_demand_surprise_digest",
    STATUS_WATCH: "watch_report_only_market_research_ppi_final_demand_surprise_digest",
    STATUS_BLOCKED: "block_report_only_market_research_ppi_final_demand_surprise_digest",
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")

__all__ = (
    "DEFAULT_MARKET_RESEARCH_PPI_FINAL_DEMAND_SURPRISE_DIGEST_CONFIG_VERSION",
    "MarketResearchPpiFinalDemandSurpriseDigestConfig",
    "MarketResearchPpiFinalDemandSurpriseDigestReasonCodeCount",
    "MarketResearchPpiFinalDemandSurpriseDigestReport",
    "MarketResearchPpiFinalDemandSurpriseDigestRow",
    "MarketResearchPpiFinalDemandSurpriseDigestSignal",
    "build_market_research_ppi_final_demand_surprise_digest",
    "market_research_ppi_final_demand_surprise_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchPpiFinalDemandSurpriseDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_PPI_FINAL_DEMAND_SURPRISE_DIGEST_CONFIG_VERSION
    )
    max_release_age_seconds: Decimal = Decimal("7200.000000")
    min_source_count: Decimal = Decimal("2.000000")
    material_surprise_threshold: Decimal = Decimal("0.100000")
    high_revision_threshold: Decimal = Decimal("0.080000")
    min_confirmation_ratio: Decimal = Decimal("0.650000")
    watch_confidence_threshold: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchPpiFinalDemandSurpriseDigestConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPpiFinalDemandSurpriseDigestConfig:
            raise TypeError(
                "MarketResearchPpiFinalDemandSurpriseDigestConfig does not support subclassing",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_PPI_FINAL_DEMAND_SURPRISE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "max_release_age_seconds",
            _require_positive_decimal(
                "max_release_age_seconds",
                self.max_release_age_seconds,
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
        object.__setattr__(
            self,
            "high_revision_threshold",
            _require_ratio_decimal(
                "high_revision_threshold",
                self.high_revision_threshold,
            ),
        )
        object.__setattr__(
            self,
            "min_confirmation_ratio",
            _require_ratio_decimal("min_confirmation_ratio", self.min_confirmation_ratio),
        )
        object.__setattr__(
            self,
            "watch_confidence_threshold",
            _require_ratio_decimal(
                "watch_confidence_threshold",
                self.watch_confidence_threshold,
            ),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchPpiFinalDemandSurpriseDigestSignal:
    condition_id: str
    research_id: str
    release_id: str
    ppi_series_id: str
    public_source_reference: str
    observed_at: datetime
    expected_final_demand_ppi: Decimal
    actual_final_demand_ppi: Decimal
    prior_final_demand_ppi: Decimal
    source_count: Decimal
    revision_ratio: Decimal
    confirmation_ratio: Decimal
    base_confidence: Decimal
    signal_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchPpiFinalDemandSurpriseDigestSignal does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPpiFinalDemandSurpriseDigestSignal:
            raise TypeError(
                "MarketResearchPpiFinalDemandSurpriseDigestSignal does not support subclassing",
            )
        for field_name in (
            "condition_id",
            "research_id",
            "release_id",
            "ppi_series_id",
            "public_source_reference",
            "signal_config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "public_source_reference",
            _masked_reference(self.public_source_reference),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "expected_final_demand_ppi",
            "actual_final_demand_ppi",
            "prior_final_demand_ppi",
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
        for field_name in ("revision_ratio", "confirmation_ratio", "base_confidence"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("signal", self)


@dataclass(frozen=True)
class MarketResearchPpiFinalDemandSurpriseDigestRow:
    condition_id: str
    research_id: str
    release_id: str
    ppi_series_id: str
    digest_status: str
    observed_at: datetime
    release_age_seconds: Decimal
    expected_final_demand_ppi: Decimal
    actual_final_demand_ppi: Decimal
    prior_final_demand_ppi: Decimal
    surprise_delta: Decimal
    abs_surprise_delta: Decimal
    prior_revision_delta: Decimal
    source_count: Decimal
    revision_ratio: Decimal
    confirmation_ratio: Decimal
    base_confidence: Decimal
    confidence_decay_factor: Decimal
    final_confidence: Decimal
    redacted_public_source_reference: str
    signal_config_version: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchPpiFinalDemandSurpriseDigestRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPpiFinalDemandSurpriseDigestRow:
            raise TypeError(
                "MarketResearchPpiFinalDemandSurpriseDigestRow does not support subclassing",
            )
        for field_name in (
            "condition_id",
            "research_id",
            "release_id",
            "ppi_series_id",
            "redacted_public_source_reference",
            "signal_config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_status("digest_status", self.digest_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "release_age_seconds",
            _require_nonnegative_decimal("release_age_seconds", self.release_age_seconds),
        )
        for field_name in (
            "expected_final_demand_ppi",
            "actual_final_demand_ppi",
            "prior_final_demand_ppi",
            "surprise_delta",
            "prior_revision_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "abs_surprise_delta",
            _require_nonnegative_decimal("abs_surprise_delta", self.abs_surprise_delta),
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
            _normalize_reason_codes(
                self.reason_codes,
                sequence=ROW_REASON_CODE_SEQUENCE,
            ),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchPpiFinalDemandSurpriseDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    signal_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchPpiFinalDemandSurpriseDigestReasonCodeCount does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPpiFinalDemandSurpriseDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchPpiFinalDemandSurpriseDigestReasonCodeCount does not support subclassing",
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
class MarketResearchPpiFinalDemandSurpriseDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    signal_count: Decimal
    ready_signal_count: Decimal
    watch_signal_count: Decimal
    blocked_signal_count: Decimal
    material_surprise_count: Decimal
    stale_release_count: Decimal
    thin_source_count: Decimal
    high_revision_count: Decimal
    confirmation_gap_count: Decimal
    average_abs_surprise_delta: Decimal
    max_abs_surprise_delta: Decimal
    max_observed_release_age_seconds: Decimal
    rows: tuple[MarketResearchPpiFinalDemandSurpriseDigestRow, ...]
    reason_code_counts: tuple[MarketResearchPpiFinalDemandSurpriseDigestReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchPpiFinalDemandSurpriseDigestReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPpiFinalDemandSurpriseDigestReport:
            raise TypeError(
                "MarketResearchPpiFinalDemandSurpriseDigestReport does not support subclassing",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_PPI_FINAL_DEMAND_SURPRISE_DIGEST_CONFIG_VERSION
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
            "stale_release_count",
            "thin_source_count",
            "high_revision_count",
            "confirmation_gap_count",
            "average_abs_surprise_delta",
            "max_abs_surprise_delta",
            "max_observed_release_age_seconds",
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
            _normalize_reason_codes(
                self.reason_codes,
                sequence=REPORT_REASON_CODE_SEQUENCE,
            ),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_ppi_final_demand_surprise_digest(
    signals: tuple[MarketResearchPpiFinalDemandSurpriseDigestSignal, ...]
    | list[MarketResearchPpiFinalDemandSurpriseDigestSignal],
    *,
    config: MarketResearchPpiFinalDemandSurpriseDigestConfig,
    generated_at: datetime,
) -> MarketResearchPpiFinalDemandSurpriseDigestReport:
    if type(config) is not MarketResearchPpiFinalDemandSurpriseDigestConfig:
        raise ValueError(
            "config must be a MarketResearchPpiFinalDemandSurpriseDigestConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_signals = _normalize_signals(signals)
    rows = tuple(
        sorted(
            (
                _build_row(signal, config=config, generated_at=generated_at_utc)
                for signal in normalized_signals
            ),
            key=_row_sort_key,
        ),
    )
    signal_count = _decimal_count(len(rows))
    reason_code_counts = (
        _reason_code_counts(rows)
        if rows
        else (
            MarketResearchPpiFinalDemandSurpriseDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                signal_ratio=ZERO,
            ),
        )
    )
    reason_codes = tuple(item.reason_code for item in reason_code_counts)
    digest_status = _report_status(rows)
    return MarketResearchPpiFinalDemandSurpriseDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        signal_count=signal_count,
        ready_signal_count=_status_count(rows, STATUS_READY),
        watch_signal_count=_status_count(rows, STATUS_WATCH),
        blocked_signal_count=_status_count(rows, STATUS_BLOCKED),
        material_surprise_count=_reason_count(rows, MATERIAL_SURPRISE_REASON),
        stale_release_count=_reason_count(rows, STALE_RELEASE_REASON),
        thin_source_count=_reason_count(rows, THIN_SOURCES_REASON),
        high_revision_count=_reason_count(rows, HIGH_REVISION_REASON),
        confirmation_gap_count=_reason_count(rows, CONFIRMATION_GAP_REASON),
        average_abs_surprise_delta=_average_decimal(
            row.abs_surprise_delta for row in rows
        ),
        max_abs_surprise_delta=_max_decimal(row.abs_surprise_delta for row in rows),
        max_observed_release_age_seconds=_max_decimal(
            row.release_age_seconds for row in rows
        ),
        rows=rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_ppi_final_demand_surprise_digest_payload(
    report: MarketResearchPpiFinalDemandSurpriseDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchPpiFinalDemandSurpriseDigestReport:
        raise ValueError(
            "report must be a MarketResearchPpiFinalDemandSurpriseDigestReport",
        )
    _require_hard_flags("report", report)
    payload = _payload_value(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a dict")
    return payload


def _normalize_signals(
    signals: tuple[MarketResearchPpiFinalDemandSurpriseDigestSignal, ...]
    | list[MarketResearchPpiFinalDemandSurpriseDigestSignal],
) -> tuple[MarketResearchPpiFinalDemandSurpriseDigestSignal, ...]:
    if type(signals) not in (list, tuple):
        raise ValueError("signals must be a list or tuple")
    normalized = tuple(signals)
    seen_release_ids: set[str] = set()
    for signal in normalized:
        if type(signal) is not MarketResearchPpiFinalDemandSurpriseDigestSignal:
            raise ValueError(
                "signals must contain MarketResearchPpiFinalDemandSurpriseDigestSignal",
            )
        _require_hard_flags("signal", signal)
        if signal.release_id in seen_release_ids:
            raise ValueError("release_id values must be unique")
        seen_release_ids.add(signal.release_id)
    return normalized


def _build_row(
    signal: MarketResearchPpiFinalDemandSurpriseDigestSignal,
    *,
    config: MarketResearchPpiFinalDemandSurpriseDigestConfig,
    generated_at: datetime,
) -> MarketResearchPpiFinalDemandSurpriseDigestRow:
    release_age_seconds = _age_seconds(generated_at, signal.observed_at)
    surprise_delta = _six(
        signal.actual_final_demand_ppi - signal.expected_final_demand_ppi,
    )
    prior_revision_delta = _six(
        signal.actual_final_demand_ppi - signal.prior_final_demand_ppi,
    )
    reason_codes = _row_reason_codes(
        signal,
        release_age_seconds,
        surprise_delta,
        config=config,
    )
    confidence_decay_factor = _confidence_decay_factor(reason_codes)
    return MarketResearchPpiFinalDemandSurpriseDigestRow(
        condition_id=signal.condition_id,
        research_id=signal.research_id,
        release_id=signal.release_id,
        ppi_series_id=signal.ppi_series_id,
        digest_status=_row_status(reason_codes),
        observed_at=signal.observed_at,
        release_age_seconds=release_age_seconds,
        expected_final_demand_ppi=signal.expected_final_demand_ppi,
        actual_final_demand_ppi=signal.actual_final_demand_ppi,
        prior_final_demand_ppi=signal.prior_final_demand_ppi,
        surprise_delta=surprise_delta,
        abs_surprise_delta=_six(abs(surprise_delta)),
        prior_revision_delta=prior_revision_delta,
        source_count=signal.source_count,
        revision_ratio=signal.revision_ratio,
        confirmation_ratio=signal.confirmation_ratio,
        base_confidence=signal.base_confidence,
        confidence_decay_factor=confidence_decay_factor,
        final_confidence=_final_confidence(
            signal.base_confidence,
            confidence_decay_factor,
        ),
        redacted_public_source_reference=signal.public_source_reference,
        signal_config_version=signal.signal_config_version,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    signal: MarketResearchPpiFinalDemandSurpriseDigestSignal,
    release_age_seconds: Decimal,
    surprise_delta: Decimal,
    *,
    config: MarketResearchPpiFinalDemandSurpriseDigestConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if abs(surprise_delta) >= config.material_surprise_threshold:
        reason_codes.append(MATERIAL_SURPRISE_REASON)
    if signal.confirmation_ratio < config.min_confirmation_ratio:
        reason_codes.append(CONFIRMATION_GAP_REASON)
    if release_age_seconds > config.max_release_age_seconds:
        reason_codes.append(STALE_RELEASE_REASON)
    if signal.source_count < config.min_source_count:
        reason_codes.append(THIN_SOURCES_REASON)
    if signal.revision_ratio > config.high_revision_threshold:
        reason_codes.append(HIGH_REVISION_REASON)
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
        STALE_RELEASE_REASON in reason_codes
        or THIN_SOURCES_REASON in reason_codes
        or HIGH_REVISION_REASON in reason_codes
    ):
        return STATUS_BLOCKED
    return STATUS_WATCH


def _report_status(
    rows: tuple[MarketResearchPpiFinalDemandSurpriseDigestRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_READY


def _confidence_decay_factor(reason_codes: tuple[str, ...]) -> Decimal:
    penalty = ZERO
    if MATERIAL_SURPRISE_REASON in reason_codes:
        penalty += Decimal("0.100000")
    if CONFIRMATION_GAP_REASON in reason_codes:
        penalty += Decimal("0.100000")
    if STALE_RELEASE_REASON in reason_codes:
        penalty += Decimal("0.200000")
    if THIN_SOURCES_REASON in reason_codes:
        penalty += Decimal("0.100000")
    if HIGH_REVISION_REASON in reason_codes:
        penalty += Decimal("0.100000")
    factor = ONE - penalty
    if factor < ZERO:
        return ZERO
    return _six(factor)


def _final_confidence(base_confidence: Decimal, confidence_decay_factor: Decimal) -> Decimal:
    return _require_ratio_decimal(
        "final_confidence",
        base_confidence * confidence_decay_factor,
    )


def _reason_code_counts(
    rows: tuple[MarketResearchPpiFinalDemandSurpriseDigestRow, ...],
) -> tuple[MarketResearchPpiFinalDemandSurpriseDigestReasonCodeCount, ...]:
    signal_count = _decimal_count(len(rows))
    counts: list[MarketResearchPpiFinalDemandSurpriseDigestReasonCodeCount] = []
    for reason_code in REPORT_REASON_CODE_SEQUENCE:
        count = _reason_count(rows, reason_code)
        if count == ZERO:
            continue
        counts.append(
            MarketResearchPpiFinalDemandSurpriseDigestReasonCodeCount(
                reason_code=reason_code,
                count=count,
                signal_ratio=_ratio(count, signal_count),
            ),
        )
    return tuple(counts)


def _status_count(
    rows: tuple[MarketResearchPpiFinalDemandSurpriseDigestRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.digest_status == status))


def _reason_count(
    rows: tuple[MarketResearchPpiFinalDemandSurpriseDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _average_decimal(values: Any) -> Decimal:
    rows = tuple(values)
    if not rows:
        return ZERO
    return _six(sum(rows, ZERO) / _decimal_count(len(rows)))


def _max_decimal(values: Any) -> Decimal:
    rows = tuple(values)
    if not rows:
        return ZERO
    return _six(max(rows))


def _row_sort_key(
    row: MarketResearchPpiFinalDemandSurpriseDigestRow,
) -> tuple[int, Decimal, Decimal, str, str]:
    return (
        _status_rank(row.digest_status),
        -row.abs_surprise_delta,
        -row.release_age_seconds,
        row.release_id,
        row.condition_id,
    )


def _status_rank(status: str) -> int:
    return {
        STATUS_BLOCKED: 0,
        STATUS_WATCH: 1,
        STATUS_READY: 2,
    }[status]


def _normalize_rows(
    rows: tuple[MarketResearchPpiFinalDemandSurpriseDigestRow, ...],
) -> tuple[MarketResearchPpiFinalDemandSurpriseDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen_release_ids: set[str] = set()
    for row in rows:
        if type(row) is not MarketResearchPpiFinalDemandSurpriseDigestRow:
            raise ValueError(
                "rows must contain MarketResearchPpiFinalDemandSurpriseDigestRow",
            )
        _require_hard_flags("row", row)
        if row.release_id in seen_release_ids:
            raise ValueError("rows must contain unique release_id values")
        seen_release_ids.add(row.release_id)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be canonical")
    return rows


def _normalize_reason_code_counts(
    reason_code_counts: tuple[
        MarketResearchPpiFinalDemandSurpriseDigestReasonCodeCount,
        ...,
    ],
) -> tuple[MarketResearchPpiFinalDemandSurpriseDigestReasonCodeCount, ...]:
    if type(reason_code_counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    seen_reason_codes: set[str] = set()
    for count in reason_code_counts:
        if type(count) is not MarketResearchPpiFinalDemandSurpriseDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchPpiFinalDemandSurpriseDigestReasonCodeCount",
            )
        _require_hard_flags("reason code count", count)
        if count.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts must contain unique reason codes")
        seen_reason_codes.add(count.reason_code)
    canonical = tuple(
        sorted(
            reason_code_counts,
            key=lambda item: REPORT_REASON_CODE_SEQUENCE.index(item.reason_code),
        ),
    )
    if reason_code_counts != canonical:
        raise ValueError("reason_code_counts must be canonical")
    return reason_code_counts


def _normalize_reason_codes(
    reason_codes: tuple[str, ...],
    *,
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    seen_reason_codes: set[str] = set()
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
        if reason_code not in sequence:
            raise ValueError("reason_codes contain a value outside this sequence")
        if reason_code in seen_reason_codes:
            raise ValueError("reason_codes must be unique")
        seen_reason_codes.add(reason_code)
    if (
        sequence == ROW_REASON_CODE_SEQUENCE
        and READY_REASON in seen_reason_codes
        and len(seen_reason_codes) != 1
    ):
        raise ValueError("reason_codes must use ready by itself")
    if NO_INPUTS_REASON in seen_reason_codes and len(seen_reason_codes) != 1:
        raise ValueError("reason_codes must use no_inputs by itself")
    canonical = tuple(reason_code for reason_code in sequence if reason_code in reason_codes)
    if reason_codes != canonical:
        raise ValueError("reason_codes must be canonical")
    return reason_codes


def _validate_row(row: MarketResearchPpiFinalDemandSurpriseDigestRow) -> None:
    if row.surprise_delta != _six(
        row.actual_final_demand_ppi - row.expected_final_demand_ppi,
    ):
        raise ValueError("surprise_delta must match actual less expected")
    if row.abs_surprise_delta != _six(abs(row.surprise_delta)):
        raise ValueError("abs_surprise_delta must match surprise_delta")
    if row.prior_revision_delta != _six(
        row.actual_final_demand_ppi - row.prior_final_demand_ppi,
    ):
        raise ValueError("prior_revision_delta must match actual less prior")
    if row.digest_status != _row_status(row.reason_codes):
        raise ValueError("digest_status must match reason_codes")
    if row.confidence_decay_factor != _confidence_decay_factor(row.reason_codes):
        raise ValueError("confidence_decay_factor must match reason_codes")
    if row.final_confidence != _final_confidence(
        row.base_confidence,
        row.confidence_decay_factor,
    ):
        raise ValueError("final_confidence must match confidence_decay_factor")


def _validate_report(report: MarketResearchPpiFinalDemandSurpriseDigestReport) -> None:
    rows = report.rows
    signal_count = _decimal_count(len(rows))
    if report.signal_count != signal_count:
        raise ValueError("signal_count must match rows")
    expected_values = (
        ("ready_signal_count", _status_count(rows, STATUS_READY)),
        ("watch_signal_count", _status_count(rows, STATUS_WATCH)),
        ("blocked_signal_count", _status_count(rows, STATUS_BLOCKED)),
        ("material_surprise_count", _reason_count(rows, MATERIAL_SURPRISE_REASON)),
        ("stale_release_count", _reason_count(rows, STALE_RELEASE_REASON)),
        ("thin_source_count", _reason_count(rows, THIN_SOURCES_REASON)),
        ("high_revision_count", _reason_count(rows, HIGH_REVISION_REASON)),
        ("confirmation_gap_count", _reason_count(rows, CONFIRMATION_GAP_REASON)),
        ("average_abs_surprise_delta", _average_decimal(row.abs_surprise_delta for row in rows)),
        ("max_abs_surprise_delta", _max_decimal(row.abs_surprise_delta for row in rows)),
        (
            "max_observed_release_age_seconds",
            _max_decimal(row.release_age_seconds for row in rows),
        ),
    )
    for field_name, expected in expected_values:
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    expected_reason_code_counts = (
        _reason_code_counts(rows)
        if rows
        else (
            MarketResearchPpiFinalDemandSurpriseDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                signal_ratio=ZERO,
            ),
        )
    )
    if report.reason_code_counts != expected_reason_code_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")
    if report.digest_status != _report_status(rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    microseconds = Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    value = seconds + microseconds
    if value < ZERO:
        raise ValueError("observed_at must not be in the future")
    return _six(value)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _require_ratio_decimal("signal_ratio", numerator / denominator)


def _decimal_count(value: int) -> Decimal:
    return _six(Decimal(value))


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_status(field_name: str, value: str) -> None:
    if type(value) is not str or value not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")


def _require_reason_code(field_name: str, value: str) -> None:
    if type(value) is not str or value not in REPORT_REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a supported reason code")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise TypeError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _six(value)


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _require_nonnegative_count_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-count Decimal")
    return decimal_value


def _require_positive_count_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_nonnegative_count_decimal(field_name, value)
    if decimal_value == ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _six(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _masked_reference(value: str) -> str:
    if not _must_mask(value):
        return value
    return "sha256:" + sha256(value.encode("utf-8")).hexdigest()[:12]


def _must_mask(value: str) -> bool:
    lowered = value.lower()
    fragments = (
        "://",
        "?",
        "=",
        *(
            "".join(chr(code) for code in codes)
            for codes in (
                (97, 117, 116, 104),
                (112, 114, 105, 118, 97, 116, 101),
                (115, 101, 99, 114, 101, 116),
                (116, 111, 107, 101, 110),
                (119, 97, 108, 108, 101, 116),
            )
        ),
    )
    return any(fragment in lowered for fragment in fragments)


def _payload_value(value: Any) -> Any:
    if type(value) is Decimal:
        return format(_six(value), "f")
    if isinstance(value, Decimal):
        raise TypeError("payload numeric values must be Decimal")
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if isinstance(value, datetime):
        raise ValueError("payload datetime must be exactly datetime")
    if type(value) in (str, bool) or value is None:
        return value
    if type(value) is int:
        raise TypeError("payload numeric values must be Decimal")
    if type(value) in (tuple, list):
        return [_payload_value(item) for item in value]
    if type(value) is dict:
        payload: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload field names must be strings")
            payload[key] = _payload_value(item)
        return payload
    raise ValueError(f"unsupported payload value: {type(value).__name__}")
