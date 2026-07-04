"""Pure Phase 1 bank stress credit research reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_BANK_STRESS_CREDIT_DIGEST_CONFIG_VERSION = (
    "market-research-bank-stress-credit-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

REASON_PREFIX = "market_research_bank_stress_credit_digest_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
READY_REASON = f"{REASON_PREFIX}ready"
STALE_SIGNAL_REASON = f"{REASON_PREFIX}stale_signal"
DEPOSIT_FLIGHT_REASON = f"{REASON_PREFIX}deposit_flight"
CREDIT_STRESS_REASON = f"{REASON_PREFIX}credit_stress"
CAPITAL_BUFFER_THIN_REASON = f"{REASON_PREFIX}capital_buffer_thin"
FUNDING_PRESSURE_REASON = f"{REASON_PREFIX}funding_pressure"
THIN_SOURCES_REASON = f"{REASON_PREFIX}thin_sources"

REASON_CODE_SEQUENCE = (
    DEPOSIT_FLIGHT_REASON,
    CREDIT_STRESS_REASON,
    CAPITAL_BUFFER_THIN_REASON,
    FUNDING_PRESSURE_REASON,
    STALE_SIGNAL_REASON,
    THIN_SOURCES_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    DEPOSIT_FLIGHT_REASON,
    CREDIT_STRESS_REASON,
    CAPITAL_BUFFER_THIN_REASON,
    FUNDING_PRESSURE_REASON,
    STALE_SIGNAL_REASON,
    THIN_SOURCES_REASON,
    READY_REASON,
)
BLOCKING_REASONS = (
    DEPOSIT_FLIGHT_REASON,
    CREDIT_STRESS_REASON,
    CAPITAL_BUFFER_THIN_REASON,
    FUNDING_PRESSURE_REASON,
    STALE_SIGNAL_REASON,
)

NEXT_STEPS = {
    STATUS_READY: "allow_report_only_market_research_bank_stress_credit_digest",
    STATUS_WATCH: "watch_report_only_market_research_bank_stress_credit_digest",
    STATUS_BLOCKED: "block_report_only_market_research_bank_stress_credit_digest",
}

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
        _join_parts("acc", "ount"),
        _join_parts("ord", "er"),
        _join_parts("can", "cel"),
        _join_parts("re", "place"),
        _join_parts("ex", "change"),
        _join_parts("mut", "ation"),
        _join_parts("data", "base"),
        _join_parts("net", "work"),
        _join_parts("sec", "ret"),
        _join_parts("to", "ken"),
        _join_parts("pri", "vate"),
        _join_parts("tra", "de"),
        _join_parts("dsn"),
        "://",
        "?",
    ),
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_BANK_STRESS_CREDIT_DIGEST_CONFIG_VERSION",
    "MarketResearchBankStressCreditDigestConfig",
    "MarketResearchBankStressCreditDigestReasonCodeCount",
    "MarketResearchBankStressCreditDigestReport",
    "MarketResearchBankStressCreditDigestRow",
    "MarketResearchBankStressCreditDigestSignal",
    "build_market_research_bank_stress_credit_digest",
    "market_research_bank_stress_credit_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchBankStressCreditDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_BANK_STRESS_CREDIT_DIGEST_CONFIG_VERSION
    )
    max_signal_age_seconds: Decimal = Decimal("7200.000000")
    deposit_outflow_watch_ratio: Decimal = Decimal("0.030000")
    deposit_outflow_block_ratio: Decimal = Decimal("0.080000")
    credit_spread_watch_bps: Decimal = Decimal("50.000000")
    credit_spread_block_bps: Decimal = Decimal("125.000000")
    min_capital_buffer_ratio: Decimal = Decimal("0.070000")
    funding_pressure_watch_ratio: Decimal = Decimal("0.650000")
    min_source_count: Decimal = Decimal("2.000000")
    confidence_decay_per_reason: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchBankStressCreditDigestConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchBankStressCreditDigestConfig:
            raise TypeError(
                "config must be exactly MarketResearchBankStressCreditDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_BANK_STRESS_CREDIT_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "max_signal_age_seconds",
            _require_positive_decimal(
                "max_signal_age_seconds",
                self.max_signal_age_seconds,
            ),
        )
        for field_name in (
            "deposit_outflow_watch_ratio",
            "deposit_outflow_block_ratio",
            "min_capital_buffer_ratio",
            "funding_pressure_watch_ratio",
            "confidence_decay_per_reason",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("credit_spread_watch_bps", "credit_spread_block_bps"):
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
        if self.deposit_outflow_block_ratio <= self.deposit_outflow_watch_ratio:
            raise ValueError(
                "deposit_outflow_block_ratio must exceed deposit_outflow_watch_ratio",
            )
        if self.credit_spread_block_bps <= self.credit_spread_watch_bps:
            raise ValueError("credit_spread_block_bps must exceed credit_spread_watch_bps")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchBankStressCreditDigestSignal:
    condition_id: str
    research_key: str
    bank_segment: str
    public_signal_reference: str
    observed_at: datetime
    deposit_outflow_ratio: Decimal
    credit_spread_widening_bps: Decimal
    capital_buffer_ratio: Decimal
    funding_pressure_ratio: Decimal
    source_count: Decimal
    base_confidence: Decimal
    signal_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchBankStressCreditDigestSignal does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchBankStressCreditDigestSignal:
            raise TypeError(
                "signal must be exactly MarketResearchBankStressCreditDigestSignal",
            )
        for field_name in (
            "condition_id",
            "research_key",
            "bank_segment",
            "signal_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_public_reference(
            "public_signal_reference",
            self.public_signal_reference,
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "deposit_outflow_ratio",
            "capital_buffer_ratio",
            "funding_pressure_ratio",
            "base_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "credit_spread_widening_bps",
            _require_decimal(
                "credit_spread_widening_bps",
                self.credit_spread_widening_bps,
            ),
        )
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_count_decimal("source_count", self.source_count),
        )
        _require_hard_flags("signal", self)


@dataclass(frozen=True)
class MarketResearchBankStressCreditDigestRow:
    condition_id: str
    research_key: str
    bank_segment: str
    digest_status: str
    observed_at: datetime
    signal_age_seconds: Decimal
    deposit_outflow_ratio: Decimal
    credit_spread_widening_bps: Decimal
    capital_buffer_ratio: Decimal
    funding_pressure_ratio: Decimal
    source_count: Decimal
    base_confidence: Decimal
    confidence_decay_factor: Decimal
    final_confidence: Decimal
    redacted_public_signal_reference: str
    signal_config_version: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchBankStressCreditDigestRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchBankStressCreditDigestRow:
            raise TypeError("row must be exactly MarketResearchBankStressCreditDigestRow")
        for field_name in (
            "condition_id",
            "research_key",
            "bank_segment",
            "redacted_public_signal_reference",
            "signal_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_status("digest_status", self.digest_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "signal_age_seconds",
            "source_count",
            "confidence_decay_factor",
            "final_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "deposit_outflow_ratio",
            "capital_buffer_ratio",
            "funding_pressure_ratio",
            "base_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "credit_spread_widening_bps",
            _require_decimal(
                "credit_spread_widening_bps",
                self.credit_spread_widening_bps,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, ROW_REASON_CODE_SEQUENCE),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchBankStressCreditDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    signal_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchBankStressCreditDigestReasonCodeCount does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchBankStressCreditDigestReasonCodeCount:
            raise TypeError(
                "reason count must be exactly "
                "MarketResearchBankStressCreditDigestReasonCodeCount",
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
        _require_hard_flags("reason count", self)


@dataclass(frozen=True)
class MarketResearchBankStressCreditDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    signal_count: Decimal
    ready_signal_count: Decimal
    watch_signal_count: Decimal
    blocked_signal_count: Decimal
    deposit_flight_signal_count: Decimal
    credit_stress_signal_count: Decimal
    capital_buffer_thin_signal_count: Decimal
    funding_pressure_signal_count: Decimal
    stale_signal_count: Decimal
    thin_source_signal_count: Decimal
    average_deposit_outflow_ratio: Decimal | None
    average_credit_spread_widening_bps: Decimal | None
    min_capital_buffer_ratio: Decimal | None
    max_funding_pressure_ratio: Decimal | None
    average_final_confidence: Decimal | None
    max_signal_age_seconds: Decimal | None
    rows: tuple[MarketResearchBankStressCreditDigestRow, ...]
    reason_code_counts: tuple[MarketResearchBankStressCreditDigestReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchBankStressCreditDigestReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchBankStressCreditDigestReport:
            raise TypeError(
                "report must be exactly MarketResearchBankStressCreditDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "signal_count",
            "ready_signal_count",
            "watch_signal_count",
            "blocked_signal_count",
            "deposit_flight_signal_count",
            "credit_stress_signal_count",
            "capital_buffer_thin_signal_count",
            "funding_pressure_signal_count",
            "stale_signal_count",
            "thin_source_signal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_deposit_outflow_ratio",
            "min_capital_buffer_ratio",
            "max_funding_pressure_ratio",
            "average_final_confidence",
        ):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(self, field_name, _require_ratio_decimal(field_name, value))
        for field_name in ("average_credit_spread_widening_bps", "max_signal_age_seconds"):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(self, field_name, _require_decimal(field_name, value))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, REASON_CODE_SEQUENCE),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_bank_stress_credit_digest(
    signals: Iterable[MarketResearchBankStressCreditDigestSignal],
    *,
    config: MarketResearchBankStressCreditDigestConfig,
    generated_at: datetime,
) -> MarketResearchBankStressCreditDigestReport:
    if type(config) is not MarketResearchBankStressCreditDigestConfig:
        raise ValueError(
            "config must be a MarketResearchBankStressCreditDigestConfig",
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
    reason_code_counts = _reason_code_counts(rows)
    reason_codes = tuple(count.reason_code for count in reason_code_counts)
    digest_status = _report_status(rows)
    return MarketResearchBankStressCreditDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        signal_count=_count(len(rows)),
        ready_signal_count=_status_count(rows, STATUS_READY),
        watch_signal_count=_status_count(rows, STATUS_WATCH),
        blocked_signal_count=_status_count(rows, STATUS_BLOCKED),
        deposit_flight_signal_count=_reason_count(rows, DEPOSIT_FLIGHT_REASON),
        credit_stress_signal_count=_reason_count(rows, CREDIT_STRESS_REASON),
        capital_buffer_thin_signal_count=_reason_count(
            rows,
            CAPITAL_BUFFER_THIN_REASON,
        ),
        funding_pressure_signal_count=_reason_count(rows, FUNDING_PRESSURE_REASON),
        stale_signal_count=_reason_count(rows, STALE_SIGNAL_REASON),
        thin_source_signal_count=_reason_count(rows, THIN_SOURCES_REASON),
        average_deposit_outflow_ratio=_average(row.deposit_outflow_ratio for row in rows),
        average_credit_spread_widening_bps=_average(
            (row.credit_spread_widening_bps for row in rows),
        ),
        min_capital_buffer_ratio=_minimum(row.capital_buffer_ratio for row in rows),
        max_funding_pressure_ratio=_maximum(row.funding_pressure_ratio for row in rows),
        average_final_confidence=_average(row.final_confidence for row in rows),
        max_signal_age_seconds=_maximum(row.signal_age_seconds for row in rows),
        rows=rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_bank_stress_credit_digest_payload(
    report: MarketResearchBankStressCreditDigestReport | dict[str, Any],
) -> dict[str, Any]:
    if isinstance(report, dict):
        return report
    if type(report) is not MarketResearchBankStressCreditDigestReport:
        raise ValueError(
            "report must be a MarketResearchBankStressCreditDigestReport",
        )
    return _payload_value(asdict(report))


def _build_row(
    signal: MarketResearchBankStressCreditDigestSignal,
    *,
    config: MarketResearchBankStressCreditDigestConfig,
    generated_at: datetime,
) -> MarketResearchBankStressCreditDigestRow:
    signal_age_seconds = _datetime_delta_seconds(generated_at, signal.observed_at)
    reason_codes = _row_reason_codes(signal, signal_age_seconds, config=config)
    reason_count = _count(sum(1 for reason_code in reason_codes if reason_code != READY_REASON))
    confidence_decay = _cap_ratio(config.confidence_decay_per_reason * reason_count)
    final_confidence = _cap_ratio(signal.base_confidence - confidence_decay)
    return MarketResearchBankStressCreditDigestRow(
        condition_id=signal.condition_id,
        research_key=signal.research_key,
        bank_segment=signal.bank_segment,
        digest_status=_row_status(reason_codes),
        observed_at=signal.observed_at,
        signal_age_seconds=signal_age_seconds,
        deposit_outflow_ratio=signal.deposit_outflow_ratio,
        credit_spread_widening_bps=signal.credit_spread_widening_bps,
        capital_buffer_ratio=signal.capital_buffer_ratio,
        funding_pressure_ratio=signal.funding_pressure_ratio,
        source_count=signal.source_count,
        base_confidence=signal.base_confidence,
        confidence_decay_factor=confidence_decay,
        final_confidence=final_confidence,
        redacted_public_signal_reference=_redact_public_reference(
            signal.public_signal_reference,
        ),
        signal_config_version=signal.signal_config_version,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    signal: MarketResearchBankStressCreditDigestSignal,
    signal_age_seconds: Decimal,
    *,
    config: MarketResearchBankStressCreditDigestConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if signal.deposit_outflow_ratio >= config.deposit_outflow_watch_ratio:
        codes.append(DEPOSIT_FLIGHT_REASON)
    if signal.credit_spread_widening_bps >= config.credit_spread_watch_bps:
        codes.append(CREDIT_STRESS_REASON)
    if signal.capital_buffer_ratio < config.min_capital_buffer_ratio:
        codes.append(CAPITAL_BUFFER_THIN_REASON)
    if signal.funding_pressure_ratio >= config.funding_pressure_watch_ratio:
        codes.append(FUNDING_PRESSURE_REASON)
    if signal_age_seconds > config.max_signal_age_seconds:
        codes.append(STALE_SIGNAL_REASON)
    if signal.source_count < config.min_source_count:
        codes.append(THIN_SOURCES_REASON)
    if not codes:
        codes.append(READY_REASON)
    return tuple(code for code in ROW_REASON_CODE_SEQUENCE if code in codes)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCKING_REASONS for reason_code in reason_codes):
        return STATUS_BLOCKED
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    return STATUS_WATCH


def _report_status(rows: tuple[MarketResearchBankStressCreditDigestRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_READY


def _reason_code_counts(
    rows: tuple[MarketResearchBankStressCreditDigestRow, ...],
) -> tuple[MarketResearchBankStressCreditDigestReasonCodeCount, ...]:
    if not rows:
        return (
            MarketResearchBankStressCreditDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ZERO,
                signal_ratio=ZERO,
            ),
        )
    total = _count(len(rows))
    counts: list[MarketResearchBankStressCreditDigestReasonCodeCount] = []
    for reason_code in REASON_CODE_SEQUENCE:
        count = _reason_count(rows, reason_code)
        if count == ZERO:
            continue
        counts.append(
            MarketResearchBankStressCreditDigestReasonCodeCount(
                reason_code=reason_code,
                count=count,
                signal_ratio=_ratio(count, total),
            ),
        )
    return tuple(counts)


def _normalize_signals(
    signals: Iterable[MarketResearchBankStressCreditDigestSignal],
) -> tuple[MarketResearchBankStressCreditDigestSignal, ...]:
    if isinstance(signals, (str, bytes)) or not isinstance(signals, Iterable):
        raise ValueError("signals must be an iterable of bank stress credit signals")
    normalized = tuple(signals)
    seen: set[tuple[str, str]] = set()
    for signal in normalized:
        if type(signal) is not MarketResearchBankStressCreditDigestSignal:
            raise ValueError(
                "signals must contain exactly MarketResearchBankStressCreditDigestSignal",
            )
        _require_hard_flags("signal", signal)
        key = (signal.condition_id, signal.research_key)
        if key in seen:
            raise ValueError("signals must not contain duplicate condition research pairs")
        seen.add(key)
    return normalized


def _normalize_rows(
    rows: tuple[MarketResearchBankStressCreditDigestRow, ...],
) -> tuple[MarketResearchBankStressCreditDigestRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, tuple):
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not MarketResearchBankStressCreditDigestRow:
            raise ValueError(
                "rows must contain exactly MarketResearchBankStressCreditDigestRow",
            )
        _require_hard_flags("row", row)
    return tuple(sorted(rows, key=_row_sort_key))


def _normalize_reason_code_counts(
    counts: tuple[MarketResearchBankStressCreditDigestReasonCodeCount, ...],
) -> tuple[MarketResearchBankStressCreditDigestReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)) or not isinstance(counts, tuple):
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not MarketResearchBankStressCreditDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain exactly "
                "MarketResearchBankStressCreditDigestReasonCodeCount",
            )
        _require_hard_flags("reason count", count)
    return tuple(sorted(counts, key=lambda count: _reason_rank(count.reason_code)))


def _normalize_reason_codes(
    reason_codes: tuple[str, ...],
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, tuple):
        raise ValueError("reason_codes must be a tuple")
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        try:
            _require_reason_code("reason_code", reason_code)
        except ValueError as exc:
            raise ValueError("reason_codes must contain supported values") from exc
        if reason_code not in sequence:
            raise ValueError("reason_codes must contain supported values")
    return tuple(sorted(dict.fromkeys(reason_codes), key=lambda code: sequence.index(code)))


def _validate_row(row: MarketResearchBankStressCreditDigestRow) -> None:
    if row.final_confidence > row.base_confidence:
        raise ValueError("final_confidence must not exceed base_confidence")
    if row.reason_codes == (READY_REASON,) and row.digest_status != STATUS_READY:
        raise ValueError("ready reason row must have ready digest_status")
    if row.digest_status == STATUS_READY and row.reason_codes != (READY_REASON,):
        raise ValueError("ready digest_status must only use the ready reason code")


def _validate_report(report: MarketResearchBankStressCreditDigestReport) -> None:
    rows = report.rows
    if report.signal_count != _count(len(rows)):
        raise ValueError("signal_count must equal rows length")
    expected_counts = {
        "ready_signal_count": _status_count(rows, STATUS_READY),
        "watch_signal_count": _status_count(rows, STATUS_WATCH),
        "blocked_signal_count": _status_count(rows, STATUS_BLOCKED),
        "deposit_flight_signal_count": _reason_count(rows, DEPOSIT_FLIGHT_REASON),
        "credit_stress_signal_count": _reason_count(rows, CREDIT_STRESS_REASON),
        "capital_buffer_thin_signal_count": _reason_count(
            rows,
            CAPITAL_BUFFER_THIN_REASON,
        ),
        "funding_pressure_signal_count": _reason_count(rows, FUNDING_PRESSURE_REASON),
        "stale_signal_count": _reason_count(rows, STALE_SIGNAL_REASON),
        "thin_source_signal_count": _reason_count(rows, THIN_SOURCES_REASON),
    }
    for field_name, expected in expected_counts.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    expected_reason_counts = _reason_code_counts(rows)
    if report.reason_code_counts != expected_reason_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(count.reason_code for count in expected_reason_counts):
        raise ValueError("reason_codes must match reason_code_counts")
    if report.digest_status != _report_status(rows):
        raise ValueError("digest_status must match row statuses")
    if report.recommended_next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    expected_aggregates = {
        "average_deposit_outflow_ratio": _average(
            (row.deposit_outflow_ratio for row in rows),
        ),
        "average_credit_spread_widening_bps": _average(
            (row.credit_spread_widening_bps for row in rows),
        ),
        "min_capital_buffer_ratio": _minimum(row.capital_buffer_ratio for row in rows),
        "max_funding_pressure_ratio": _maximum(
            (row.funding_pressure_ratio for row in rows),
        ),
        "average_final_confidence": _average(row.final_confidence for row in rows),
        "max_signal_age_seconds": _maximum(row.signal_age_seconds for row in rows),
    }
    for field_name, expected in expected_aggregates.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")


def _row_sort_key(
    row: MarketResearchBankStressCreditDigestRow,
) -> tuple[int, Decimal, Decimal, str, str]:
    return (
        _status_rank(row.digest_status),
        -row.deposit_outflow_ratio,
        -row.credit_spread_widening_bps,
        row.condition_id,
        row.research_key,
    )


def _status_count(
    rows: tuple[MarketResearchBankStressCreditDigestRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.digest_status == status))


def _reason_count(
    rows: tuple[MarketResearchBankStressCreditDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _status_rank(status: str) -> int:
    return {
        STATUS_BLOCKED: 0,
        STATUS_WATCH: 1,
        STATUS_READY: 2,
    }[status]


def _reason_rank(reason_code: str) -> int:
    return REASON_CODE_SEQUENCE.index(reason_code)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _require_status(field_name: str, value: str) -> None:
    if type(value) is not str or value not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")


def _require_reason_code(field_name: str, value: str) -> None:
    if type(value) is not str or value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a supported reason code")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")


def _require_public_string(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must be public and redacted")


def _require_public_reference(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if _join_parts("wal", "let") in lowered:
        raise ValueError(f"{field_name} must be public and redacted")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return _quantize(decimal_value)


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(decimal_value)


def _require_nonnegative_count_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return decimal_value


def _require_positive_count_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_nonnegative_count_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(decimal_value)


def _datetime_delta_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    seconds = (
        Decimal(delta.days * 86400 + delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    if seconds < ZERO:
        raise ValueError("observed_at must not be after generated_at")
    return _quantize(seconds)


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _cap_ratio(numerator / denominator)


def _average(values: Iterable[Decimal]) -> Decimal | None:
    items = tuple(values)
    if not items:
        return None
    return _quantize(sum(items, ZERO) / Decimal(len(items)))


def _minimum(values: Iterable[Decimal]) -> Decimal | None:
    items = tuple(values)
    if not items:
        return None
    return min(items)


def _maximum(values: Iterable[Decimal]) -> Decimal | None:
    items = tuple(values)
    if not items:
        return None
    return max(items)


def _cap_ratio(value: Decimal) -> Decimal:
    return _require_ratio_decimal("ratio", min(ONE, max(ZERO, value)))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _redact_public_reference(value: str) -> str:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        return f"sha256:{sha256(value.encode('utf-8')).hexdigest()[:12]}"
    return value


def _payload_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _payload_value(item) for key, item in value.items()}
    return value
