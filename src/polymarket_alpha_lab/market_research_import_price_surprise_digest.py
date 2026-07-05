"""Pure Phase 1 import price surprise research reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_IMPORT_PRICE_SURPRISE_DIGEST_CONFIG_VERSION = (
    "market-research-import-price-surprise-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

STALE_PRICE_SIGNAL_REASON = (
    "market_research_import_price_surprise_digest_stale_price_signal"
)
LOW_PROBABILITY_DELTA_REASON = (
    "market_research_import_price_surprise_digest_low_probability_delta"
)
LOW_SURPRISE_REASON = "market_research_import_price_surprise_digest_low_surprise"
SOURCE_FAMILY_GAP_REASON = (
    "market_research_import_price_surprise_digest_source_family_gap"
)
CONFIRMATION_GAP_REASON = (
    "market_research_import_price_surprise_digest_confirmation_gap"
)
READY_REASON = "market_research_import_price_surprise_digest_ready"
NO_INPUTS_REASON = "market_research_import_price_surprise_digest_no_inputs"

ROW_REASON_CODE_SEQUENCE = (
    STALE_PRICE_SIGNAL_REASON,
    LOW_PROBABILITY_DELTA_REASON,
    LOW_SURPRISE_REASON,
    SOURCE_FAMILY_GAP_REASON,
    CONFIRMATION_GAP_REASON,
    READY_REASON,
)
REASON_CODE_SEQUENCE = (
    CONFIRMATION_GAP_REASON,
    LOW_PROBABILITY_DELTA_REASON,
    LOW_SURPRISE_REASON,
    STALE_PRICE_SIGNAL_REASON,
    SOURCE_FAMILY_GAP_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)

NEXT_STEPS = {
    STATUS_READY: "use_report_only_market_research_import_price_surprise_digest",
    STATUS_WATCH: "watch_report_only_market_research_import_price_surprise_digest",
    STATUS_BLOCKED: "block_report_only_market_research_import_price_surprise_digest",
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")


__all__ = (
    "DEFAULT_MARKET_RESEARCH_IMPORT_PRICE_SURPRISE_DIGEST_CONFIG_VERSION",
    "MarketResearchImportPriceSurpriseDigestConfig",
    "MarketResearchImportPriceSurpriseDigestReasonCodeCount",
    "MarketResearchImportPriceSurpriseDigestReport",
    "MarketResearchImportPriceSurpriseDigestRow",
    "MarketResearchImportPriceSurpriseDigestSignal",
    "build_market_research_import_price_surprise_digest",
    "market_research_import_price_surprise_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchImportPriceSurpriseDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_IMPORT_PRICE_SURPRISE_DIGEST_CONFIG_VERSION
    )
    max_price_signal_age_seconds: Decimal = Decimal("7200.000000")
    min_abs_import_price_surprise: Decimal = Decimal("0.200000")
    min_market_probability_delta: Decimal = Decimal("0.030000")
    min_source_family_count: Decimal = Decimal("3.000000")
    min_confirmation_ratio: Decimal = Decimal("0.650000")
    confidence_decay_per_gap: Decimal = Decimal("0.100000")
    watch_confidence_threshold: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchImportPriceSurpriseDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchImportPriceSurpriseDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "max_price_signal_age_seconds",
            "min_abs_import_price_surprise",
            "min_source_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_market_probability_delta",
            "min_confirmation_ratio",
            "confidence_decay_per_gap",
            "watch_confidence_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchImportPriceSurpriseDigestSignal:
    condition_id: str
    import_price_key: str
    country_code: str
    release_key: str
    public_signal_reference: str
    observed_at: datetime
    actual_import_price_change: Decimal
    consensus_import_price_change: Decimal
    market_probability_delta: Decimal
    source_family_count: Decimal
    confirmation_ratio: Decimal
    base_confidence: Decimal
    signal_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchImportPriceSurpriseDigestSignal:
            raise ValueError(
                "signal must be exactly "
                "MarketResearchImportPriceSurpriseDigestSignal",
            )
        for field_name in (
            "condition_id",
            "import_price_key",
            "country_code",
            "release_key",
            "signal_config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_public_string("public_signal_reference", self.public_signal_reference)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "actual_import_price_change",
            "consensus_import_price_change",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "market_probability_delta",
            _require_ratio_decimal(
                "market_probability_delta",
                self.market_probability_delta,
            ),
        )
        object.__setattr__(
            self,
            "source_family_count",
            _require_nonnegative_decimal("source_family_count", self.source_family_count),
        )
        for field_name in ("confirmation_ratio", "base_confidence"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("signal", self)


@dataclass(frozen=True)
class MarketResearchImportPriceSurpriseDigestRow:
    condition_id: str
    import_price_key: str
    country_code: str
    release_key: str
    digest_status: str
    observed_at: datetime
    signal_age_seconds: Decimal
    actual_import_price_change: Decimal
    consensus_import_price_change: Decimal
    import_price_surprise: Decimal
    abs_import_price_surprise: Decimal
    market_probability_delta: Decimal
    source_family_count: Decimal
    confirmation_ratio: Decimal
    base_confidence: Decimal
    confidence_decay_factor: Decimal
    final_confidence: Decimal
    redacted_public_signal_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchImportPriceSurpriseDigestRow:
            raise ValueError(
                "row must be exactly MarketResearchImportPriceSurpriseDigestRow",
            )
        for field_name in (
            "condition_id",
            "import_price_key",
            "country_code",
            "release_key",
            "redacted_public_signal_reference",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_digest_status("digest_status", self.digest_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "signal_age_seconds",
            "abs_import_price_surprise",
            "source_family_count",
            "confidence_decay_factor",
            "final_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "actual_import_price_change",
            "consensus_import_price_change",
            "import_price_surprise",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "market_probability_delta",
            "confirmation_ratio",
            "base_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchImportPriceSurpriseDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    signal_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchImportPriceSurpriseDigestReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "MarketResearchImportPriceSurpriseDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "signal_ratio",
            _require_ratio_decimal("signal_ratio", self.signal_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchImportPriceSurpriseDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    signal_count: Decimal
    ready_signal_count: Decimal
    watch_signal_count: Decimal
    blocked_signal_count: Decimal
    stale_price_signal_count: Decimal
    low_surprise_signal_count: Decimal
    low_probability_delta_signal_count: Decimal
    source_family_gap_signal_count: Decimal
    confirmation_gap_signal_count: Decimal
    total_confidence_decay: Decimal
    average_final_confidence: Decimal
    average_abs_import_price_surprise: Decimal
    average_market_probability_delta: Decimal
    average_confirmation_ratio: Decimal
    max_observed_signal_age_seconds: Decimal
    rows: tuple[MarketResearchImportPriceSurpriseDigestRow, ...]
    reason_code_counts: tuple[MarketResearchImportPriceSurpriseDigestReasonCodeCount, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchImportPriceSurpriseDigestReport:
            raise ValueError(
                "report must be exactly MarketResearchImportPriceSurpriseDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_digest_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "signal_count",
            "ready_signal_count",
            "watch_signal_count",
            "blocked_signal_count",
            "stale_price_signal_count",
            "low_surprise_signal_count",
            "low_probability_delta_signal_count",
            "source_family_gap_signal_count",
            "confirmation_gap_signal_count",
            "total_confidence_decay",
            "average_final_confidence",
            "average_abs_import_price_surprise",
            "average_market_probability_delta",
            "average_confirmation_ratio",
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
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_import_price_surprise_digest(
    signals: list[MarketResearchImportPriceSurpriseDigestSignal]
    | tuple[MarketResearchImportPriceSurpriseDigestSignal, ...],
    *,
    config: MarketResearchImportPriceSurpriseDigestConfig,
    generated_at: datetime,
) -> MarketResearchImportPriceSurpriseDigestReport:
    if type(config) is not MarketResearchImportPriceSurpriseDigestConfig:
        raise ValueError("config must be a MarketResearchImportPriceSurpriseDigestConfig")
    _require_hard_flags("config", config)

    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (
                _row_from_signal(signal, config, generated_at_utc)
                for signal in _normalize_signals(signals)
            ),
            key=_row_sort_key,
        ),
    )
    reason_code_counts = _reason_code_counts(rows)
    digest_status = _digest_status(rows)
    return MarketResearchImportPriceSurpriseDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        signal_count=_count(len(rows)),
        ready_signal_count=_status_count(rows, STATUS_READY),
        watch_signal_count=_status_count(rows, STATUS_WATCH),
        blocked_signal_count=_status_count(rows, STATUS_BLOCKED),
        stale_price_signal_count=_reason_count(rows, STALE_PRICE_SIGNAL_REASON),
        low_surprise_signal_count=_reason_count(rows, LOW_SURPRISE_REASON),
        low_probability_delta_signal_count=_reason_count(
            rows,
            LOW_PROBABILITY_DELTA_REASON,
        ),
        source_family_gap_signal_count=_reason_count(rows, SOURCE_FAMILY_GAP_REASON),
        confirmation_gap_signal_count=_reason_count(rows, CONFIRMATION_GAP_REASON),
        total_confidence_decay=_sum_decimal(rows, "confidence_decay_factor"),
        average_final_confidence=_average(rows, "final_confidence"),
        average_abs_import_price_surprise=_average(
            rows,
            "abs_import_price_surprise",
        ),
        average_market_probability_delta=_average(rows, "market_probability_delta"),
        average_confirmation_ratio=_average(rows, "confirmation_ratio"),
        max_observed_signal_age_seconds=_max_decimal(rows, "signal_age_seconds"),
        rows=rows,
        reason_code_counts=reason_code_counts,
    )


def market_research_import_price_surprise_digest_payload(
    report: MarketResearchImportPriceSurpriseDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchImportPriceSurpriseDigestReport:
        raise ValueError("report must be a MarketResearchImportPriceSurpriseDigestReport")
    _require_hard_flags("report", report)
    return _json_ready(report)


def _normalize_signals(
    signals: list[MarketResearchImportPriceSurpriseDigestSignal]
    | tuple[MarketResearchImportPriceSurpriseDigestSignal, ...],
) -> tuple[MarketResearchImportPriceSurpriseDigestSignal, ...]:
    if type(signals) not in (list, tuple):
        raise ValueError("signals must be a list or tuple")
    normalized = tuple(signals)
    seen_condition_ids: set[str] = set()
    for signal in normalized:
        if type(signal) is not MarketResearchImportPriceSurpriseDigestSignal:
            raise ValueError(
                "signals must contain MarketResearchImportPriceSurpriseDigestSignal "
                "values",
            )
        _require_hard_flags("signal", signal)
        if signal.condition_id in seen_condition_ids:
            raise ValueError("signals must not contain duplicate condition_id values")
        seen_condition_ids.add(signal.condition_id)
    return normalized


def _row_from_signal(
    signal: MarketResearchImportPriceSurpriseDigestSignal,
    config: MarketResearchImportPriceSurpriseDigestConfig,
    generated_at: datetime,
) -> MarketResearchImportPriceSurpriseDigestRow:
    signal_age_seconds = _datetime_delta_seconds(generated_at, signal.observed_at)
    import_price_surprise = _quantize(
        signal.actual_import_price_change - signal.consensus_import_price_change,
    )
    abs_import_price_surprise = _quantize(abs(import_price_surprise))
    reason_codes = _row_reason_codes(
        signal_age_seconds=signal_age_seconds,
        abs_import_price_surprise=abs_import_price_surprise,
        signal=signal,
        config=config,
    )
    confidence_decay_factor = _confidence_decay_factor(reason_codes, config)
    final_confidence = _quantize(
        max(ZERO, signal.base_confidence - confidence_decay_factor),
    )
    digest_status = _row_status(reason_codes, final_confidence, config)
    return MarketResearchImportPriceSurpriseDigestRow(
        condition_id=signal.condition_id,
        import_price_key=signal.import_price_key,
        country_code=signal.country_code,
        release_key=signal.release_key,
        digest_status=digest_status,
        observed_at=signal.observed_at,
        signal_age_seconds=signal_age_seconds,
        actual_import_price_change=signal.actual_import_price_change,
        consensus_import_price_change=signal.consensus_import_price_change,
        import_price_surprise=import_price_surprise,
        abs_import_price_surprise=abs_import_price_surprise,
        market_probability_delta=signal.market_probability_delta,
        source_family_count=signal.source_family_count,
        confirmation_ratio=signal.confirmation_ratio,
        base_confidence=signal.base_confidence,
        confidence_decay_factor=confidence_decay_factor,
        final_confidence=final_confidence,
        redacted_public_signal_reference=_redacted_reference(
            signal.public_signal_reference,
        ),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    signal_age_seconds: Decimal,
    abs_import_price_surprise: Decimal,
    signal: MarketResearchImportPriceSurpriseDigestSignal,
    config: MarketResearchImportPriceSurpriseDigestConfig,
) -> tuple[str, ...]:
    candidates: list[str] = []
    if signal_age_seconds > config.max_price_signal_age_seconds:
        candidates.append(STALE_PRICE_SIGNAL_REASON)
    if signal.market_probability_delta < config.min_market_probability_delta:
        candidates.append(LOW_PROBABILITY_DELTA_REASON)
    if abs_import_price_surprise < config.min_abs_import_price_surprise:
        candidates.append(LOW_SURPRISE_REASON)
    if signal.source_family_count < config.min_source_family_count:
        candidates.append(SOURCE_FAMILY_GAP_REASON)
    if signal.confirmation_ratio < config.min_confirmation_ratio:
        candidates.append(CONFIRMATION_GAP_REASON)
    if not candidates:
        candidates.append(READY_REASON)
    return tuple(code for code in ROW_REASON_CODE_SEQUENCE if code in candidates)


def _row_status(
    reason_codes: tuple[str, ...],
    final_confidence: Decimal,
    config: MarketResearchImportPriceSurpriseDigestConfig,
) -> str:
    if STALE_PRICE_SIGNAL_REASON in reason_codes or SOURCE_FAMILY_GAP_REASON in reason_codes:
        return STATUS_BLOCKED
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    if final_confidence < config.watch_confidence_threshold:
        return STATUS_WATCH
    return STATUS_WATCH


def _digest_status(rows: tuple[MarketResearchImportPriceSurpriseDigestRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_READY


def _reason_code_counts(
    rows: tuple[MarketResearchImportPriceSurpriseDigestRow, ...],
) -> tuple[MarketResearchImportPriceSurpriseDigestReasonCodeCount, ...]:
    if not rows:
        return (
            MarketResearchImportPriceSurpriseDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ZERO,
                signal_ratio=ZERO,
            ),
        )
    signal_count = _count(len(rows))
    counts = [
        (reason_code, _reason_count(rows, reason_code))
        for reason_code in REASON_CODE_SEQUENCE
    ]
    return tuple(
        MarketResearchImportPriceSurpriseDigestReasonCodeCount(
            reason_code=reason_code,
            count=count,
            signal_ratio=_ratio(count, signal_count),
        )
        for reason_code, count in counts
        if count > ZERO
    )


def _row_sort_key(
    row: MarketResearchImportPriceSurpriseDigestRow,
) -> tuple[int, Decimal, Decimal, str]:
    status_rank = {STATUS_BLOCKED: 0, STATUS_WATCH: 1, STATUS_READY: 2}
    return (
        status_rank[row.digest_status],
        -row.signal_age_seconds,
        -row.abs_import_price_surprise,
        row.condition_id,
    )


def _redacted_reference(public_signal_reference: str) -> str:
    lowered = public_signal_reference.lower()
    if "://" in lowered or "?" in public_signal_reference or "=" in public_signal_reference:
        digest = sha256(public_signal_reference.encode("utf-8")).hexdigest()[:12]
        return f"sha256:{digest}"
    return public_signal_reference


def _validate_row(row: MarketResearchImportPriceSurpriseDigestRow) -> None:
    expected_surprise = _quantize(
        row.actual_import_price_change - row.consensus_import_price_change,
    )
    if row.import_price_surprise != expected_surprise:
        raise ValueError("import_price_surprise must match actual less consensus")
    if row.abs_import_price_surprise != _quantize(abs(row.import_price_surprise)):
        raise ValueError("abs_import_price_surprise must match import_price_surprise")
    if row.reason_codes == (READY_REASON,):
        expected_status = STATUS_READY
    elif (
        STALE_PRICE_SIGNAL_REASON in row.reason_codes
        or SOURCE_FAMILY_GAP_REASON in row.reason_codes
    ):
        expected_status = STATUS_BLOCKED
    else:
        expected_status = STATUS_WATCH
    if row.digest_status != expected_status:
        raise ValueError("digest_status must match reason_codes")
    if READY_REASON in row.reason_codes and row.reason_codes != (READY_REASON,):
        raise ValueError("reason_codes must not mix ready with gap reasons")
    if row.reason_codes == (READY_REASON,) and row.confidence_decay_factor != ZERO:
        raise ValueError("confidence_decay_factor must match reason_codes")
    expected_final_confidence = _quantize(
        max(ZERO, row.base_confidence - row.confidence_decay_factor),
    )
    if row.final_confidence != expected_final_confidence:
        raise ValueError("final_confidence must match base confidence less decay")


def _validate_report(report: MarketResearchImportPriceSurpriseDigestReport) -> None:
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic ordering")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if report.signal_count != _count(len(report.rows)):
        raise ValueError("signal_count must match rows")
    for field_name, status in (
        ("ready_signal_count", STATUS_READY),
        ("watch_signal_count", STATUS_WATCH),
        ("blocked_signal_count", STATUS_BLOCKED),
    ):
        if getattr(report, field_name) != _status_count(report.rows, status):
            raise ValueError(f"{field_name} must match rows")
    for field_name, reason_code in (
        ("stale_price_signal_count", STALE_PRICE_SIGNAL_REASON),
        ("low_surprise_signal_count", LOW_SURPRISE_REASON),
        ("low_probability_delta_signal_count", LOW_PROBABILITY_DELTA_REASON),
        ("source_family_gap_signal_count", SOURCE_FAMILY_GAP_REASON),
        ("confirmation_gap_signal_count", CONFIRMATION_GAP_REASON),
    ):
        if getattr(report, field_name) != _reason_count(report.rows, reason_code):
            raise ValueError(f"{field_name} must match rows")
    for field_name in (
        "total_confidence_decay",
        "average_final_confidence",
        "average_abs_import_price_surprise",
        "average_market_probability_delta",
        "average_confirmation_ratio",
        "max_observed_signal_age_seconds",
    ):
        expected = _report_decimal_stat(report.rows, field_name)
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _report_decimal_stat(
    rows: tuple[MarketResearchImportPriceSurpriseDigestRow, ...],
    field_name: str,
) -> Decimal:
    if field_name == "total_confidence_decay":
        return _sum_decimal(rows, "confidence_decay_factor")
    if field_name == "average_final_confidence":
        return _average(rows, "final_confidence")
    if field_name == "average_abs_import_price_surprise":
        return _average(rows, "abs_import_price_surprise")
    if field_name == "average_market_probability_delta":
        return _average(rows, "market_probability_delta")
    if field_name == "average_confirmation_ratio":
        return _average(rows, "confirmation_ratio")
    if field_name == "max_observed_signal_age_seconds":
        return _max_decimal(rows, "signal_age_seconds")
    raise ValueError(f"unsupported report decimal stat {field_name}")


def _datetime_delta_seconds(newer: datetime, older: datetime) -> Decimal:
    delta = newer - older
    microseconds = Decimal(delta.days * 86400 * 1000000)
    microseconds += Decimal(delta.seconds * 1000000)
    microseconds += Decimal(delta.microseconds)
    seconds = microseconds / MICROSECONDS_PER_SECOND
    if seconds < ZERO:
        raise ValueError("observed_at must be at or before generated_at")
    return _quantize(seconds)


def _status_count(
    rows: tuple[MarketResearchImportPriceSurpriseDigestRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.digest_status == status))


def _reason_count(
    rows: tuple[MarketResearchImportPriceSurpriseDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _sum_decimal(
    rows: tuple[MarketResearchImportPriceSurpriseDigestRow, ...],
    field_name: str,
) -> Decimal:
    return _quantize(sum((getattr(row, field_name) for row in rows), ZERO))


def _average(
    rows: tuple[MarketResearchImportPriceSurpriseDigestRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return _ratio(_sum_decimal(rows, field_name), _count(len(rows)))


def _max_decimal(
    rows: tuple[MarketResearchImportPriceSurpriseDigestRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return _quantize(max(getattr(row, field_name) for row in rows))


def _confidence_decay_factor(
    reason_codes: tuple[str, ...],
    config: MarketResearchImportPriceSurpriseDigestConfig,
) -> Decimal:
    gap_count = _count(sum(1 for code in reason_codes if code != READY_REASON))
    return _quantize(config.confidence_decay_per_gap * gap_count)


def _normalize_rows(
    rows: tuple[MarketResearchImportPriceSurpriseDigestRow, ...],
) -> tuple[MarketResearchImportPriceSurpriseDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not MarketResearchImportPriceSurpriseDigestRow:
            raise ValueError("rows must contain MarketResearchImportPriceSurpriseDigestRow")
        _require_hard_flags("row", row)
    return rows


def _normalize_reason_code_counts(
    rows: tuple[MarketResearchImportPriceSurpriseDigestReasonCodeCount, ...],
) -> tuple[MarketResearchImportPriceSurpriseDigestReasonCodeCount, ...]:
    if type(rows) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for row in rows:
        if type(row) is not MarketResearchImportPriceSurpriseDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchImportPriceSurpriseDigestReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", row)
    return rows


def _normalize_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in ROW_REASON_CODE_SEQUENCE:
            raise ValueError(f"{field_name} must be a known row reason code")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    ordered_codes = tuple(code for code in ROW_REASON_CODE_SEQUENCE if code in reason_codes)
    if ordered_codes != reason_codes:
        raise ValueError(f"{field_name} must be deterministic")
    return reason_codes


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str or value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a known reason code")
    return value


def _require_digest_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be a known digest status")
    return value


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")
    return value


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a public string")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    return _quantize(value)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be a ratio")
    return decimal_value


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} {flag_name} must be True")


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _json_ready(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return _json_ready(asdict(value))
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [_json_ready(item) for item in value]
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    return value
