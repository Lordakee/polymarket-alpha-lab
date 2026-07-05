"""Pure Phase 1 credit spread widening research reducer."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_MARKET_RESEARCH_CREDIT_SPREAD_WIDENING_DIGEST_CONFIG_VERSION = (
    "market-research-credit-spread-widening-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

NO_INPUTS_REASON = "market_research_credit_spread_widening_digest_no_inputs"
READY_REASON = "market_research_credit_spread_widening_digest_ready"
STALE_SIGNAL_REASON = "market_research_credit_spread_widening_digest_stale_signal"
BLOCK_WIDENING_REASON = (
    "market_research_credit_spread_widening_digest_block_widening"
)
WATCH_WIDENING_REASON = (
    "market_research_credit_spread_widening_digest_watch_widening"
)
SOURCE_FAMILY_GAP_REASON = (
    "market_research_credit_spread_widening_digest_source_family_gap"
)
STALE_SOURCE_RATIO_REASON = (
    "market_research_credit_spread_widening_digest_stale_source_ratio"
)

REASON_CODE_SEQUENCE = (
    STALE_SIGNAL_REASON,
    BLOCK_WIDENING_REASON,
    WATCH_WIDENING_REASON,
    SOURCE_FAMILY_GAP_REASON,
    STALE_SOURCE_RATIO_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    STALE_SIGNAL_REASON,
    BLOCK_WIDENING_REASON,
    WATCH_WIDENING_REASON,
    SOURCE_FAMILY_GAP_REASON,
    STALE_SOURCE_RATIO_REASON,
    READY_REASON,
)
BLOCKING_REASONS = (
    STALE_SIGNAL_REASON,
    BLOCK_WIDENING_REASON,
    SOURCE_FAMILY_GAP_REASON,
    STALE_SOURCE_RATIO_REASON,
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
STATUS_WEIGHT = {
    STATUS_BLOCKED: Decimal("2.000000"),
    STATUS_WATCH: Decimal("1.000000"),
    STATUS_READY: Decimal("0.000000"),
}


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("au", "th"),
        _join_parts("bro", "ker"),
        _join_parts("sig", "ning"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("ad", "vice"),
        _join_parts("net", "work"),
        _join_parts("data", "base"),
        _join_parts("per", "sist"),
        _join_parts("pay", "load"),
        _join_parts("sec", "ret"),
        _join_parts("to", "ken"),
        _join_parts("pri", "vate"),
        _join_parts("tra", "de"),
    ),
)


@dataclass(frozen=True)
class MarketResearchCreditSpreadWideningDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_CREDIT_SPREAD_WIDENING_DIGEST_CONFIG_VERSION
    )
    max_signal_age_seconds: Decimal = Decimal("7200.000000")
    watch_widening_bps: Decimal = Decimal("25.000000")
    block_widening_bps: Decimal = Decimal("75.000000")
    min_source_family_count: Decimal = Decimal("3.000000")
    max_stale_source_ratio: Decimal = Decimal("0.250000")
    confidence_decay_per_gap: Decimal = Decimal("0.100000")
    watch_confidence_threshold: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCreditSpreadWideningDigestConfig:
            raise TypeError(
                "MarketResearchCreditSpreadWideningDigestConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCreditSpreadWideningDigestConfig:
            raise ValueError(
                "config must be exactly MarketResearchCreditSpreadWideningDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "max_signal_age_seconds",
            "watch_widening_bps",
            "block_widening_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_source_family_count",
            _require_positive_count_decimal(
                "min_source_family_count",
                self.min_source_family_count,
            ),
        )
        for field_name in (
            "max_stale_source_ratio",
            "confidence_decay_per_gap",
            "watch_confidence_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_widening_bps <= self.watch_widening_bps:
            raise ValueError("block_widening_bps must exceed watch_widening_bps")
        require_paper_only_flags("config", self)


@dataclass(frozen=True)
class MarketResearchCreditSpreadWideningDigestSignal:
    condition_id: str
    credit_spread_key: str
    issuer_or_index: str
    public_signal_reference: str
    observed_at: datetime
    current_spread_bps: Decimal
    prior_spread_bps: Decimal
    spread_widening_bps: Decimal
    source_family_count: Decimal
    stale_source_ratio: Decimal
    base_confidence: Decimal
    signal_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCreditSpreadWideningDigestSignal:
            raise TypeError(
                "MarketResearchCreditSpreadWideningDigestSignal does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCreditSpreadWideningDigestSignal:
            raise ValueError(
                "signal must be exactly MarketResearchCreditSpreadWideningDigestSignal",
            )
        for field_name in (
            "condition_id",
            "credit_spread_key",
            "issuer_or_index",
            "signal_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_canonical_string("public_signal_reference", self.public_signal_reference)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("current_spread_bps", "prior_spread_bps"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "spread_widening_bps",
            _require_decimal("spread_widening_bps", self.spread_widening_bps),
        )
        object.__setattr__(
            self,
            "source_family_count",
            _require_nonnegative_count_decimal(
                "source_family_count",
                self.source_family_count,
            ),
        )
        for field_name in ("stale_source_ratio", "base_confidence"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _validate_signal(self)
        require_paper_only_flags("signal", self)


@dataclass(frozen=True)
class MarketResearchCreditSpreadWideningDigestRow:
    condition_id: str
    credit_spread_key: str
    issuer_or_index: str
    digest_status: str
    observed_at: datetime
    signal_age_seconds: Decimal
    current_spread_bps: Decimal
    prior_spread_bps: Decimal
    spread_widening_bps: Decimal
    source_family_count: Decimal
    stale_source_ratio: Decimal
    base_confidence: Decimal
    confidence_decay_factor: Decimal
    final_confidence: Decimal
    redacted_public_signal_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCreditSpreadWideningDigestRow:
            raise TypeError(
                "MarketResearchCreditSpreadWideningDigestRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCreditSpreadWideningDigestRow:
            raise ValueError(
                "row must be exactly MarketResearchCreditSpreadWideningDigestRow",
            )
        for field_name in ("condition_id", "credit_spread_key", "issuer_or_index"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_status("digest_status", self.digest_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "signal_age_seconds",
            "current_spread_bps",
            "prior_spread_bps",
            "source_family_count",
            "confidence_decay_factor",
            "final_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "spread_widening_bps",
            _require_decimal("spread_widening_bps", self.spread_widening_bps),
        )
        for field_name in ("stale_source_ratio", "base_confidence"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_canonical_string(
            "redacted_public_signal_reference",
            self.redacted_public_signal_reference,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                ROW_REASON_CODE_SEQUENCE,
            ),
        )
        _validate_row(self)
        require_paper_only_flags("row", self)


@dataclass(frozen=True)
class MarketResearchCreditSpreadWideningDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    signal_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCreditSpreadWideningDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchCreditSpreadWideningDigestReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCreditSpreadWideningDigestReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "MarketResearchCreditSpreadWideningDigestReasonCodeCount",
            )
        _require_member("reason_code", self.reason_code, REASON_CODE_SEQUENCE)
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
        require_paper_only_flags("reason count", self)


@dataclass(frozen=True)
class MarketResearchCreditSpreadWideningDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    signal_count: Decimal
    ready_signal_count: Decimal
    watch_signal_count: Decimal
    blocked_signal_count: Decimal
    stale_signal_count: Decimal
    watch_widening_signal_count: Decimal
    block_widening_signal_count: Decimal
    source_family_gap_signal_count: Decimal
    stale_source_signal_count: Decimal
    total_confidence_decay: Decimal
    average_final_confidence: Decimal
    average_spread_widening_bps: Decimal
    max_observed_signal_age_seconds: Decimal
    reason_code_counts: tuple[MarketResearchCreditSpreadWideningDigestReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    rows: tuple[MarketResearchCreditSpreadWideningDigestRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchCreditSpreadWideningDigestReport:
            raise TypeError(
                "MarketResearchCreditSpreadWideningDigestReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchCreditSpreadWideningDigestReport:
            raise ValueError(
                "report must be exactly MarketResearchCreditSpreadWideningDigestReport",
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
            "stale_signal_count",
            "watch_widening_signal_count",
            "block_widening_signal_count",
            "source_family_gap_signal_count",
            "stale_source_signal_count",
            "total_confidence_decay",
            "average_final_confidence",
            "max_observed_signal_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_spread_widening_bps",
            _require_decimal(
                "average_spread_widening_bps",
                self.average_spread_widening_bps,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REASON_CODE_SEQUENCE,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        require_paper_only_flags("report", self)


_PUBLIC_DATACLASS_TYPES = (
    MarketResearchCreditSpreadWideningDigestConfig,
    MarketResearchCreditSpreadWideningDigestReasonCodeCount,
    MarketResearchCreditSpreadWideningDigestReport,
    MarketResearchCreditSpreadWideningDigestRow,
    MarketResearchCreditSpreadWideningDigestSignal,
)


def build_market_research_credit_spread_widening_digest(
    inputs: list[MarketResearchCreditSpreadWideningDigestSignal]
    | tuple[MarketResearchCreditSpreadWideningDigestSignal, ...],
    *,
    config: MarketResearchCreditSpreadWideningDigestConfig,
    generated_at: datetime,
) -> MarketResearchCreditSpreadWideningDigestReport:
    if type(config) is not MarketResearchCreditSpreadWideningDigestConfig:
        raise ValueError(
            "config must be a MarketResearchCreditSpreadWideningDigestConfig",
        )
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    signals = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (_digest_row(signal, config, generated_at_utc) for signal in signals),
            key=_row_sort_key,
        ),
    )
    reason_code_counts = _reason_code_counts(rows)
    reason_codes = tuple(row.reason_code for row in reason_code_counts)
    digest_status = _status_rollup(tuple(row.digest_status for row in rows))
    return MarketResearchCreditSpreadWideningDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=_recommended_next_step(digest_status),
        signal_count=_count(len(rows)),
        ready_signal_count=_status_count(rows, STATUS_READY),
        watch_signal_count=_status_count(rows, STATUS_WATCH),
        blocked_signal_count=_status_count(rows, STATUS_BLOCKED),
        stale_signal_count=_reason_count(rows, STALE_SIGNAL_REASON),
        watch_widening_signal_count=_reason_count(rows, WATCH_WIDENING_REASON),
        block_widening_signal_count=_reason_count(rows, BLOCK_WIDENING_REASON),
        source_family_gap_signal_count=_reason_count(rows, SOURCE_FAMILY_GAP_REASON),
        stale_source_signal_count=_reason_count(rows, STALE_SOURCE_RATIO_REASON),
        total_confidence_decay=_sum_rows(rows, "confidence_decay_factor"),
        average_final_confidence=_average(rows, "final_confidence"),
        average_spread_widening_bps=_average(rows, "spread_widening_bps"),
        max_observed_signal_age_seconds=_max_rows(rows, "signal_age_seconds"),
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
        rows=rows,
    )


def market_research_credit_spread_widening_digest_payload(
    report: MarketResearchCreditSpreadWideningDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchCreditSpreadWideningDigestReport:
        raise ValueError("report must be a MarketResearchCreditSpreadWideningDigestReport")
    _require_payload_safe_value("report", report)
    payload = json_ready_no_floats(report)
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")
    return payload


def _digest_row(
    signal: MarketResearchCreditSpreadWideningDigestSignal,
    config: MarketResearchCreditSpreadWideningDigestConfig,
    generated_at: datetime,
) -> MarketResearchCreditSpreadWideningDigestRow:
    signal_age_seconds = _age_seconds(generated_at, signal.observed_at)
    reason_codes = _row_reason_codes(signal, config, signal_age_seconds)
    gap_count = sum(1 for reason_code in reason_codes if reason_code != READY_REASON)
    confidence_decay_factor = _min_ratio(
        config.confidence_decay_per_gap * Decimal(gap_count),
    )
    final_confidence = _max_ratio(signal.base_confidence - confidence_decay_factor)
    return MarketResearchCreditSpreadWideningDigestRow(
        condition_id=signal.condition_id,
        credit_spread_key=signal.credit_spread_key,
        issuer_or_index=signal.issuer_or_index,
        digest_status=_row_status(reason_codes, final_confidence, config),
        observed_at=signal.observed_at,
        signal_age_seconds=signal_age_seconds,
        current_spread_bps=signal.current_spread_bps,
        prior_spread_bps=signal.prior_spread_bps,
        spread_widening_bps=signal.spread_widening_bps,
        source_family_count=signal.source_family_count,
        stale_source_ratio=signal.stale_source_ratio,
        base_confidence=signal.base_confidence,
        confidence_decay_factor=confidence_decay_factor,
        final_confidence=final_confidence,
        redacted_public_signal_reference=_redact_reference(signal.public_signal_reference),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    signal: MarketResearchCreditSpreadWideningDigestSignal,
    config: MarketResearchCreditSpreadWideningDigestConfig,
    signal_age_seconds: Decimal,
) -> tuple[str, ...]:
    codes: list[str] = []
    if signal_age_seconds > config.max_signal_age_seconds:
        codes.append(STALE_SIGNAL_REASON)
    if signal.spread_widening_bps >= config.block_widening_bps:
        codes.append(BLOCK_WIDENING_REASON)
    elif signal.spread_widening_bps >= config.watch_widening_bps:
        codes.append(WATCH_WIDENING_REASON)
    if signal.source_family_count < config.min_source_family_count:
        codes.append(SOURCE_FAMILY_GAP_REASON)
    if signal.stale_source_ratio > config.max_stale_source_ratio:
        codes.append(STALE_SOURCE_RATIO_REASON)
    if not codes:
        codes.append(READY_REASON)
    return _normalize_reason_codes("reason_codes", tuple(codes), ROW_REASON_CODE_SEQUENCE)


def _row_status(
    reason_codes: tuple[str, ...],
    final_confidence: Decimal,
    config: MarketResearchCreditSpreadWideningDigestConfig,
) -> str:
    if any(reason_code in BLOCKING_REASONS for reason_code in reason_codes):
        return STATUS_BLOCKED
    if reason_codes != (READY_REASON,) or final_confidence < config.watch_confidence_threshold:
        return STATUS_WATCH
    return STATUS_READY


def _reason_code_counts(
    rows: tuple[MarketResearchCreditSpreadWideningDigestRow, ...],
) -> tuple[MarketResearchCreditSpreadWideningDigestReasonCodeCount, ...]:
    if not rows:
        return (
            MarketResearchCreditSpreadWideningDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                signal_ratio=ZERO,
            ),
        )
    signal_count = _count(len(rows))
    counts = []
    for reason_code in REASON_CODE_SEQUENCE:
        if reason_code == NO_INPUTS_REASON:
            continue
        count = _reason_count(rows, reason_code)
        if count > ZERO:
            counts.append(
                MarketResearchCreditSpreadWideningDigestReasonCodeCount(
                    reason_code=reason_code,
                    count=count,
                    signal_ratio=_ratio(count, signal_count),
                ),
            )
    return tuple(counts)


def _normalize_inputs(
    inputs: list[MarketResearchCreditSpreadWideningDigestSignal]
    | tuple[MarketResearchCreditSpreadWideningDigestSignal, ...],
) -> tuple[MarketResearchCreditSpreadWideningDigestSignal, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(inputs)
    seen_condition_ids: set[str] = set()
    for row in rows:
        if type(row) is not MarketResearchCreditSpreadWideningDigestSignal:
            raise ValueError(
                "inputs must contain MarketResearchCreditSpreadWideningDigestSignal "
                "values",
            )
        require_paper_only_flags("input", row)
        if row.condition_id in seen_condition_ids:
            raise ValueError("inputs must not contain duplicate condition_id values")
        seen_condition_ids.add(row.condition_id)
    return rows


def _row_sort_key(
    row: MarketResearchCreditSpreadWideningDigestRow,
) -> tuple[Decimal, Decimal, Decimal, str]:
    return (
        -STATUS_WEIGHT[row.digest_status],
        -row.spread_widening_bps,
        -row.signal_age_seconds,
        row.credit_spread_key,
    )


def _status_rollup(statuses: tuple[str, ...]) -> str:
    if not statuses:
        return STATUS_BLOCKED
    if any(status == STATUS_BLOCKED for status in statuses):
        return STATUS_BLOCKED
    if any(status == STATUS_WATCH for status in statuses):
        return STATUS_WATCH
    return STATUS_READY


def _recommended_next_step(status: str) -> str:
    if status == STATUS_READY:
        return "continue_report_only_market_research_credit_spread_widening_digest"
    if status == STATUS_WATCH:
        return "review_report_only_market_research_credit_spread_widening_digest"
    return "block_report_only_market_research_credit_spread_widening_digest"


def _reason_count(
    rows: tuple[MarketResearchCreditSpreadWideningDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _status_count(
    rows: tuple[MarketResearchCreditSpreadWideningDigestRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.digest_status == status))


def _sum_rows(
    rows: tuple[MarketResearchCreditSpreadWideningDigestRow, ...],
    field_name: str,
) -> Decimal:
    return _normalize_decimal(
        sum((getattr(row, field_name) for row in rows), ZERO),
    )


def _average(
    rows: tuple[MarketResearchCreditSpreadWideningDigestRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return _normalize_decimal(_sum_rows(rows, field_name) / _count(len(rows)))


def _max_rows(
    rows: tuple[MarketResearchCreditSpreadWideningDigestRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return _normalize_decimal(max(getattr(row, field_name) for row in rows))


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANT)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _normalize_decimal(numerator / denominator)


def _min_ratio(value: Decimal) -> Decimal:
    return _require_ratio_decimal("ratio", min(ONE, max(ZERO, value)))


def _max_ratio(value: Decimal) -> Decimal:
    return _require_ratio_decimal("ratio", max(ZERO, min(ONE, value)))


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    if observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    delta = generated_at - observed_at
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    micros = Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    return _require_nonnegative_decimal("signal_age_seconds", seconds + micros)


def _redact_reference(value: str) -> str:
    lowered = value.lower()
    if (
        "://" in lowered
        or "?" in lowered
        or any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS)
    ):
        digest = sha256(value.encode("utf-8")).hexdigest()[:12]
        return f"sha256:{digest}"
    return value


def _validate_signal(signal: MarketResearchCreditSpreadWideningDigestSignal) -> None:
    expected_widening = _normalize_decimal(
        signal.current_spread_bps - signal.prior_spread_bps,
    )
    if signal.spread_widening_bps != expected_widening:
        raise ValueError("spread_widening_bps must match current minus prior spread")


def _validate_row(row: MarketResearchCreditSpreadWideningDigestRow) -> None:
    if row.confidence_decay_factor > ONE:
        raise ValueError("confidence_decay_factor must be at most 1")
    if row.final_confidence > row.base_confidence:
        raise ValueError("final_confidence must not exceed base_confidence")
    if row.reason_codes == (READY_REASON,) and row.digest_status != STATUS_READY:
        raise ValueError("ready rows must use ready status")
    if row.reason_codes != (READY_REASON,) and row.digest_status == STATUS_READY:
        raise ValueError("non-ready rows must not use ready status")
    if row.reason_codes != _normalize_reason_codes(
        "reason_codes",
        row.reason_codes,
        ROW_REASON_CODE_SEQUENCE,
    ):
        raise ValueError("reason_codes must use deterministic sequence")


def _validate_report(report: MarketResearchCreditSpreadWideningDigestReport) -> None:
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
        ("stale_signal_count", STALE_SIGNAL_REASON),
        ("watch_widening_signal_count", WATCH_WIDENING_REASON),
        ("block_widening_signal_count", BLOCK_WIDENING_REASON),
        ("source_family_gap_signal_count", SOURCE_FAMILY_GAP_REASON),
        ("stale_source_signal_count", STALE_SOURCE_RATIO_REASON),
    ):
        if getattr(report, field_name) != _reason_count(report.rows, reason_code):
            raise ValueError(f"{field_name} must match rows")
    if report.total_confidence_decay != _sum_rows(report.rows, "confidence_decay_factor"):
        raise ValueError("total_confidence_decay must match rows")
    if report.average_final_confidence != _average(report.rows, "final_confidence"):
        raise ValueError("average_final_confidence must match rows")
    if report.average_spread_widening_bps != _average(report.rows, "spread_widening_bps"):
        raise ValueError("average_spread_widening_bps must match rows")
    if report.max_observed_signal_age_seconds != _max_rows(report.rows, "signal_age_seconds"):
        raise ValueError("max_observed_signal_age_seconds must match rows")
    if report.digest_status != _status_rollup(
        tuple(row.digest_status for row in report.rows),
    ):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step must match digest_status")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(row.reason_code for row in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sort")


def _normalize_rows(
    value: object,
) -> tuple[MarketResearchCreditSpreadWideningDigestRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be a tuple")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must be a tuple") from exc
    for row in rows:
        if type(row) is not MarketResearchCreditSpreadWideningDigestRow:
            raise ValueError(
                "rows must contain MarketResearchCreditSpreadWideningDigestRow values",
            )
        require_paper_only_flags("row", row)
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[MarketResearchCreditSpreadWideningDigestReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be a tuple")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_code_counts must be a tuple") from exc
    for row in rows:
        if type(row) is not MarketResearchCreditSpreadWideningDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchCreditSpreadWideningDigestReasonCodeCount values",
            )
        require_paper_only_flags("reason count", row)
    if len({row.reason_code for row in rows}) != len(rows):
        raise ValueError("reason_code_counts must be unique")
    if tuple(
        sorted(rows, key=lambda row: REASON_CODE_SEQUENCE.index(row.reason_code)),
    ) != rows:
        raise ValueError("reason_code_counts must use deterministic sequence")
    return rows


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        _require_member(field_name, reason_code, allowed)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    if tuple(reason_code for reason_code in allowed if reason_code in reason_codes) != reason_codes:
        raise ValueError(f"{field_name} must be deterministic")
    return reason_codes


def _require_status(field_name: str, value: object) -> None:
    _require_member(field_name, value, DIGEST_STATUSES)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must be public")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _normalize_decimal(value)


def _normalize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _require_payload_safe_value(field_name: str, value: object) -> None:
    if type(value) is Decimal:
        normalized = _require_decimal(field_name, value)
        if normalized != value:
            raise ValueError(f"{field_name} must be quantized to six decimals")
        return
    if type(value) is datetime:
        _as_utc(field_name, value)
        if value.tzinfo is not UTC:
            raise ValueError(f"{field_name} must be normalized to UTC")
        return
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{field_name} must be a supported public dataclass")
        require_paper_only_flags(field_name, value)
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
    raise ValueError(f"{field_name} must be safe for payload serialization")


def _reconstruct_public_dataclass(field_name: str, value: object) -> None:
    type_ = type(value)
    try:
        type_(**{field.name: getattr(value, field.name) for field in fields(value)})
    except (ArithmeticError, TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must remain constructor-valid") from exc


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


__all__ = (
    "DEFAULT_MARKET_RESEARCH_CREDIT_SPREAD_WIDENING_DIGEST_CONFIG_VERSION",
    "MarketResearchCreditSpreadWideningDigestConfig",
    "MarketResearchCreditSpreadWideningDigestReasonCodeCount",
    "MarketResearchCreditSpreadWideningDigestReport",
    "MarketResearchCreditSpreadWideningDigestRow",
    "MarketResearchCreditSpreadWideningDigestSignal",
    "build_market_research_credit_spread_widening_digest",
    "market_research_credit_spread_widening_digest_payload",
)
