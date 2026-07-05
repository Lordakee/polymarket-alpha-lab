from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_PAYROLL_DIFFUSION_INDEX_DIGEST_CONFIG_VERSION = (
    "market-research-payroll-diffusion-index-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)
REASON_PREFIX = "market_research_payroll_diffusion_index_digest_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
READY_REASON = f"{REASON_PREFIX}ready"
CONTRACTION_REASON = f"{REASON_PREFIX}contraction"
DEEP_CONTRACTION_REASON = f"{REASON_PREFIX}deep_contraction"
NEGATIVE_PAYROLL_REASON = f"{REASON_PREFIX}negative_payroll"
CONSENSUS_MISS_REASON = f"{REASON_PREFIX}consensus_miss"
THIN_SOURCES_REASON = f"{REASON_PREFIX}thin_sources"
STALE_REPORT_REASON = f"{REASON_PREFIX}stale_report"
MISSING_ACK_REASON = f"{REASON_PREFIX}missing_acknowledgement"
SLOW_ACK_REASON = f"{REASON_PREFIX}slow_acknowledgement"
REASON_SEQUENCE = (
    CONTRACTION_REASON,
    CONSENSUS_MISS_REASON,
    STALE_REPORT_REASON,
    DEEP_CONTRACTION_REASON,
    MISSING_ACK_REASON,
    NEGATIVE_PAYROLL_REASON,
    READY_REASON,
    SLOW_ACK_REASON,
    THIN_SOURCES_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_SEQUENCE = (
    CONTRACTION_REASON,
    CONSENSUS_MISS_REASON,
    DEEP_CONTRACTION_REASON,
    MISSING_ACK_REASON,
    NEGATIVE_PAYROLL_REASON,
    SLOW_ACK_REASON,
    STALE_REPORT_REASON,
    THIN_SOURCES_REASON,
    READY_REASON,
)
NEXT_STEPS = {
    STATUS_READY: "allow_report_only_market_research_payroll_diffusion_index_digest",
    STATUS_WATCH: "watch_report_only_market_research_payroll_diffusion_index_digest",
    STATUS_BLOCKED: "block_report_only_market_research_payroll_diffusion_index_digest",
}

CTX = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROS = Decimal("1000000")


def _join(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_PARTS = frozenset(
    (
        _join("au", "th"),
        _join("can", "cel"),
        _join("data", "base"),
        _join("d", "b"),
        _join("net", "work"),
        _join("or", "der"),
        _join("re", "place"),
        _join("wal", "let"),
    ),
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_PAYROLL_DIFFUSION_INDEX_DIGEST_CONFIG_VERSION",
    "MarketResearchPayrollDiffusionIndexDigestConfig",
    "MarketResearchPayrollDiffusionIndexDigestInputRow",
    "MarketResearchPayrollDiffusionIndexDigestReasonCodeCount",
    "MarketResearchPayrollDiffusionIndexDigestReport",
    "MarketResearchPayrollDiffusionIndexDigestRow",
    "build_market_research_payroll_diffusion_index_digest",
    "market_research_payroll_diffusion_index_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchPayrollDiffusionIndexDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_PAYROLL_DIFFUSION_INDEX_DIGEST_CONFIG_VERSION
    )
    deep_contraction_threshold: Decimal = Decimal("45.000000")
    contraction_threshold: Decimal = Decimal("50.000000")
    consensus_miss_threshold: Decimal = Decimal("0.500000")
    max_report_age_seconds: Decimal = Decimal("3600.000000")
    max_acknowledgement_lag_seconds: Decimal = Decimal("900.000000")
    min_source_count: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchPayrollDiffusionIndexDigestConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPayrollDiffusionIndexDigestConfig:
            raise TypeError(
                "MarketResearchPayrollDiffusionIndexDigestConfig does not support subclassing",
            )
        _plain_str("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_PAYROLL_DIFFUSION_INDEX_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for name in (
            "deep_contraction_threshold",
            "contraction_threshold",
            "consensus_miss_threshold",
        ):
            object.__setattr__(self, name, _nonnegative_decimal(name, getattr(self, name)))
        for name in (
            "max_report_age_seconds",
            "max_acknowledgement_lag_seconds",
        ):
            object.__setattr__(self, name, _positive_decimal(name, getattr(self, name)))
        object.__setattr__(
            self,
            "min_source_count",
            _positive_count("min_source_count", self.min_source_count),
        )
        if self.deep_contraction_threshold >= self.contraction_threshold:
            raise ValueError(
                "deep_contraction_threshold must be below contraction_threshold",
            )
        _hard_flags(self)


@dataclass(frozen=True)
class MarketResearchPayrollDiffusionIndexDigestInputRow:
    research_key: str
    condition_id: str
    segment_key: str
    segment_name: str
    diffusion_index: Decimal
    previous_diffusion_index: Decimal
    consensus_diffusion_index: Decimal
    payroll_change: Decimal
    source_count: Decimal
    observed_at: datetime
    acknowledged_at: datetime | None
    source_reference: str
    input_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchPayrollDiffusionIndexDigestInputRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPayrollDiffusionIndexDigestInputRow:
            raise TypeError(
                "MarketResearchPayrollDiffusionIndexDigestInputRow does not support subclassing",
            )
        for name in (
            "research_key",
            "condition_id",
            "segment_key",
            "segment_name",
            "source_reference",
            "input_config_version",
        ):
            _plain_str(name, getattr(self, name))
        for name in (
            "diffusion_index",
            "previous_diffusion_index",
            "consensus_diffusion_index",
            "payroll_change",
        ):
            object.__setattr__(self, name, _decimal(name, getattr(self, name)))
        object.__setattr__(
            self,
            "source_count",
            _nonnegative_count("source_count", self.source_count),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        if self.acknowledged_at is not None:
            object.__setattr__(
                self,
                "acknowledged_at",
                _as_utc("acknowledged_at", self.acknowledged_at),
            )
            if self.acknowledged_at < self.observed_at:
                raise ValueError("acknowledged_at must not be before observed_at")
        _hard_flags(self)


@dataclass(frozen=True)
class MarketResearchPayrollDiffusionIndexDigestRow:
    research_key: str
    condition_id: str
    segment_key: str
    segment_name: str
    segment_status: str
    diffusion_index: Decimal
    previous_diffusion_index: Decimal
    consensus_diffusion_index: Decimal
    payroll_change: Decimal
    source_count: Decimal
    observed_at: datetime
    acknowledged_at: datetime | None
    report_age_seconds: Decimal
    acknowledgement_lag_seconds: Decimal | None
    diffusion_index_change: Decimal
    consensus_gap: Decimal
    redacted_source_reference: str
    input_config_version: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchPayrollDiffusionIndexDigestRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPayrollDiffusionIndexDigestRow:
            raise TypeError(
                "MarketResearchPayrollDiffusionIndexDigestRow does not support subclassing",
            )
        for name in (
            "research_key",
            "condition_id",
            "segment_key",
            "segment_name",
            "input_config_version",
        ):
            _plain_str(name, getattr(self, name))
        object.__setattr__(
            self,
            "redacted_source_reference",
            _redacted_source_reference(
                "redacted_source_reference",
                self.redacted_source_reference,
            ),
        )
        _status("segment_status", self.segment_status)
        for name in (
            "diffusion_index",
            "previous_diffusion_index",
            "consensus_diffusion_index",
            "payroll_change",
            "diffusion_index_change",
            "consensus_gap",
        ):
            object.__setattr__(self, name, _decimal(name, getattr(self, name)))
        object.__setattr__(
            self,
            "source_count",
            _nonnegative_count("source_count", self.source_count),
        )
        object.__setattr__(
            self,
            "report_age_seconds",
            _nonnegative_decimal("report_age_seconds", self.report_age_seconds),
        )
        if self.acknowledgement_lag_seconds is not None:
            object.__setattr__(
                self,
                "acknowledgement_lag_seconds",
                _nonnegative_decimal(
                    "acknowledgement_lag_seconds",
                    self.acknowledgement_lag_seconds,
                ),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        if self.acknowledged_at is not None:
            object.__setattr__(
                self,
                "acknowledged_at",
                _as_utc("acknowledged_at", self.acknowledged_at),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _reason_codes(self.reason_codes, ROW_REASON_SEQUENCE),
        )
        _validate_row_consistency(self)
        _hard_flags(self)


@dataclass(frozen=True)
class MarketResearchPayrollDiffusionIndexDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    segment_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchPayrollDiffusionIndexDigestReasonCodeCount does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPayrollDiffusionIndexDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchPayrollDiffusionIndexDigestReasonCodeCount "
                "does not support subclassing",
            )
        _reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _nonnegative_count("count", self.count))
        object.__setattr__(
            self,
            "segment_ratio",
            _ratio_decimal("segment_ratio", self.segment_ratio),
        )
        _hard_flags(self)


@dataclass(frozen=True)
class MarketResearchPayrollDiffusionIndexDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    segment_count: Decimal
    ready_segment_count: Decimal
    watch_segment_count: Decimal
    blocked_segment_count: Decimal
    contraction_segment_count: Decimal
    deep_contraction_segment_count: Decimal
    negative_payroll_segment_count: Decimal
    consensus_miss_count: Decimal
    thin_source_count: Decimal
    stale_report_count: Decimal
    missing_acknowledgement_count: Decimal
    slow_acknowledgement_count: Decimal
    average_diffusion_index: Decimal | None
    average_consensus_gap: Decimal | None
    contraction_ratio: Decimal
    max_report_age_seconds: Decimal | None
    rows: tuple[MarketResearchPayrollDiffusionIndexDigestRow, ...]
    reason_code_counts: tuple[MarketResearchPayrollDiffusionIndexDigestReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchPayrollDiffusionIndexDigestReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPayrollDiffusionIndexDigestReport:
            raise TypeError(
                "MarketResearchPayrollDiffusionIndexDigestReport does not support subclassing",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _plain_str("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_PAYROLL_DIFFUSION_INDEX_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _status("digest_status", self.digest_status)
        _plain_str("recommended_next_step", self.recommended_next_step)
        for name in (
            "segment_count",
            "ready_segment_count",
            "watch_segment_count",
            "blocked_segment_count",
            "contraction_segment_count",
            "deep_contraction_segment_count",
            "negative_payroll_segment_count",
            "consensus_miss_count",
            "thin_source_count",
            "stale_report_count",
            "missing_acknowledgement_count",
            "slow_acknowledgement_count",
        ):
            object.__setattr__(self, name, _nonnegative_count(name, getattr(self, name)))
        object.__setattr__(
            self,
            "contraction_ratio",
            _ratio_decimal("contraction_ratio", self.contraction_ratio),
        )
        for name in ("average_diffusion_index", "average_consensus_gap", "max_report_age_seconds"):
            value = getattr(self, name)
            if value is not None:
                if name == "max_report_age_seconds":
                    object.__setattr__(self, name, _nonnegative_decimal(name, value))
                else:
                    object.__setattr__(self, name, _decimal(name, value))
        object.__setattr__(self, "rows", _rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _reason_code_counts_tuple(self.reason_code_counts),
        )
        object.__setattr__(self, "reason_codes", _reason_codes(self.reason_codes, REASON_SEQUENCE))
        _validate_report_consistency(self)
        _hard_flags(self)


def build_market_research_payroll_diffusion_index_digest(
    rows: tuple[object, ...],
    *,
    config: MarketResearchPayrollDiffusionIndexDigestConfig,
    generated_at: datetime,
) -> MarketResearchPayrollDiffusionIndexDigestReport:
    if type(config) is not MarketResearchPayrollDiffusionIndexDigestConfig:
        raise ValueError("config must be a MarketResearchPayrollDiffusionIndexDigestConfig")
    _hard_flags(config)
    generated = _as_utc("generated_at", generated_at)
    source_rows = _input_rows(rows)
    built_rows = tuple(
        sorted(
            (_build_row(row, config=config, generated_at=generated) for row in source_rows),
            key=lambda row: (_status_sort_key(row.segment_status), row.segment_key, row.research_key),
        ),
    )
    reason_codes = _report_reasons(built_rows)
    segment_count = _count(len(built_rows))
    return MarketResearchPayrollDiffusionIndexDigestReport(
        generated_at=generated,
        config_version=config.config_version,
        digest_status=_report_status(built_rows),
        recommended_next_step=NEXT_STEPS[_report_status(built_rows)],
        segment_count=segment_count,
        ready_segment_count=_status_count(built_rows, STATUS_READY),
        watch_segment_count=_status_count(built_rows, STATUS_WATCH),
        blocked_segment_count=_status_count(built_rows, STATUS_BLOCKED),
        contraction_segment_count=_reason_count(built_rows, CONTRACTION_REASON),
        deep_contraction_segment_count=_reason_count(built_rows, DEEP_CONTRACTION_REASON),
        negative_payroll_segment_count=_reason_count(built_rows, NEGATIVE_PAYROLL_REASON),
        consensus_miss_count=_reason_count(built_rows, CONSENSUS_MISS_REASON),
        thin_source_count=_reason_count(built_rows, THIN_SOURCES_REASON),
        stale_report_count=_reason_count(built_rows, STALE_REPORT_REASON),
        missing_acknowledgement_count=_reason_count(built_rows, MISSING_ACK_REASON),
        slow_acknowledgement_count=_reason_count(built_rows, SLOW_ACK_REASON),
        average_diffusion_index=_average((row.diffusion_index for row in built_rows)),
        average_consensus_gap=_average((row.consensus_gap for row in built_rows)),
        contraction_ratio=_ratio(_reason_count(built_rows, CONTRACTION_REASON), segment_count),
        max_report_age_seconds=_max_decimal(row.report_age_seconds for row in built_rows),
        rows=built_rows,
        reason_code_counts=_report_reason_counts(reason_codes, built_rows),
        reason_codes=reason_codes,
    )


def market_research_payroll_diffusion_index_digest_payload(
    report: MarketResearchPayrollDiffusionIndexDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchPayrollDiffusionIndexDigestReport:
        raise ValueError("report must be a MarketResearchPayrollDiffusionIndexDigestReport")
    _hard_flags(report)
    return _payload(asdict(report))


def _build_row(
    row: MarketResearchPayrollDiffusionIndexDigestInputRow,
    *,
    config: MarketResearchPayrollDiffusionIndexDigestConfig,
    generated_at: datetime,
) -> MarketResearchPayrollDiffusionIndexDigestRow:
    if row.observed_at > generated_at:
        raise ValueError("observed_at cannot be future")
    report_age = _seconds_between(generated_at, row.observed_at)
    ack_lag = None
    if row.acknowledged_at is not None:
        ack_lag = _seconds_between(row.acknowledged_at, row.observed_at)
    diffusion_change = _quant(row.diffusion_index - row.previous_diffusion_index)
    consensus_gap = _quant(row.diffusion_index - row.consensus_diffusion_index)
    reasons = _row_reasons(row, report_age=report_age, acknowledgement_lag=ack_lag, config=config)
    return MarketResearchPayrollDiffusionIndexDigestRow(
        research_key=row.research_key,
        condition_id=row.condition_id,
        segment_key=row.segment_key,
        segment_name=row.segment_name,
        segment_status=_row_status(reasons),
        diffusion_index=row.diffusion_index,
        previous_diffusion_index=row.previous_diffusion_index,
        consensus_diffusion_index=row.consensus_diffusion_index,
        payroll_change=row.payroll_change,
        source_count=row.source_count,
        observed_at=row.observed_at,
        acknowledged_at=row.acknowledged_at,
        report_age_seconds=report_age,
        acknowledgement_lag_seconds=ack_lag,
        diffusion_index_change=diffusion_change,
        consensus_gap=consensus_gap,
        redacted_source_reference=_redact(row.source_reference),
        input_config_version=row.input_config_version,
        reason_codes=reasons,
    )


def _row_reasons(
    row: MarketResearchPayrollDiffusionIndexDigestInputRow,
    *,
    report_age: Decimal,
    acknowledgement_lag: Decimal | None,
    config: MarketResearchPayrollDiffusionIndexDigestConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if row.diffusion_index < config.contraction_threshold:
        reasons.append(CONTRACTION_REASON)
    if row.diffusion_index < config.deep_contraction_threshold:
        reasons.append(DEEP_CONTRACTION_REASON)
    if row.payroll_change < ZERO:
        reasons.append(NEGATIVE_PAYROLL_REASON)
    if row.diffusion_index - row.consensus_diffusion_index <= -config.consensus_miss_threshold:
        reasons.append(CONSENSUS_MISS_REASON)
    if row.source_count < config.min_source_count:
        reasons.append(THIN_SOURCES_REASON)
    if report_age > config.max_report_age_seconds:
        reasons.append(STALE_REPORT_REASON)
    if row.acknowledged_at is None:
        reasons.append(MISSING_ACK_REASON)
    elif acknowledgement_lag is not None and acknowledgement_lag > config.max_acknowledgement_lag_seconds:
        reasons.append(SLOW_ACK_REASON)
    if not reasons:
        reasons.append(READY_REASON)
    return _reason_codes(
        tuple(reason_code for reason_code in ROW_REASON_SEQUENCE if reason_code in reasons),
        ROW_REASON_SEQUENCE,
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if (
        DEEP_CONTRACTION_REASON in reason_codes
        or MISSING_ACK_REASON in reason_codes
        or THIN_SOURCES_REASON in reason_codes
    ):
        return STATUS_BLOCKED
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    return STATUS_WATCH


def _report_status(rows: tuple[MarketResearchPayrollDiffusionIndexDigestRow, ...]) -> str:
    if not rows or any(row.segment_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.segment_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_READY


def _status_sort_key(status: str) -> int:
    if status == STATUS_BLOCKED:
        return 0
    if status == STATUS_WATCH:
        return 1
    return 2


def _report_reasons(
    rows: tuple[MarketResearchPayrollDiffusionIndexDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    present = {reason_code for row in rows for reason_code in row.reason_codes}
    return _reason_codes(
        tuple(reason_code for reason_code in REASON_SEQUENCE if reason_code in present),
        REASON_SEQUENCE,
    )


def _report_reason_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[MarketResearchPayrollDiffusionIndexDigestRow, ...],
) -> tuple[MarketResearchPayrollDiffusionIndexDigestReasonCodeCount, ...]:
    total = _count(len(rows))
    if not rows:
        return (
            MarketResearchPayrollDiffusionIndexDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=Decimal("1.000000"),
                segment_ratio=ZERO,
            ),
        )
    return tuple(
        MarketResearchPayrollDiffusionIndexDigestReasonCodeCount(
            reason_code=reason_code,
            count=_reason_count(rows, reason_code),
            segment_ratio=_ratio(_reason_count(rows, reason_code), total),
        )
        for reason_code in reason_codes
    )


def _validate_row_consistency(row: MarketResearchPayrollDiffusionIndexDigestRow) -> None:
    if row.diffusion_index_change != _quant(row.diffusion_index - row.previous_diffusion_index):
        raise ValueError("diffusion_index_change must match diffusion indexes")
    if row.consensus_gap != _quant(row.diffusion_index - row.consensus_diffusion_index):
        raise ValueError("consensus_gap must match diffusion index and consensus")
    if row.acknowledged_at is None:
        if row.acknowledgement_lag_seconds is not None:
            raise ValueError("acknowledgement_lag_seconds must be absent without acknowledgement")
    else:
        if row.acknowledged_at < row.observed_at:
            raise ValueError("acknowledged_at must not be before observed_at")
        if row.acknowledgement_lag_seconds is None:
            raise ValueError("acknowledgement_lag_seconds is required with acknowledgement")
        if row.acknowledgement_lag_seconds != _seconds_between(
            row.acknowledged_at,
            row.observed_at,
        ):
            raise ValueError("acknowledgement_lag_seconds must match timestamps")
    if READY_REASON in row.reason_codes and row.reason_codes != (READY_REASON,):
        raise ValueError("reason_codes must not mix ready with blocking reasons")
    if row.segment_status != _row_status(row.reason_codes):
        raise ValueError("segment_status must match reason_codes")


def _validate_report_consistency(
    report: MarketResearchPayrollDiffusionIndexDigestReport,
) -> None:
    expected_counts = (
        ("segment_count", _count(len(report.rows))),
        ("ready_segment_count", _status_count(report.rows, STATUS_READY)),
        ("watch_segment_count", _status_count(report.rows, STATUS_WATCH)),
        ("blocked_segment_count", _status_count(report.rows, STATUS_BLOCKED)),
        ("contraction_segment_count", _reason_count(report.rows, CONTRACTION_REASON)),
        (
            "deep_contraction_segment_count",
            _reason_count(report.rows, DEEP_CONTRACTION_REASON),
        ),
        (
            "negative_payroll_segment_count",
            _reason_count(report.rows, NEGATIVE_PAYROLL_REASON),
        ),
        ("consensus_miss_count", _reason_count(report.rows, CONSENSUS_MISS_REASON)),
        ("thin_source_count", _reason_count(report.rows, THIN_SOURCES_REASON)),
        ("stale_report_count", _reason_count(report.rows, STALE_REPORT_REASON)),
        (
            "missing_acknowledgement_count",
            _reason_count(report.rows, MISSING_ACK_REASON),
        ),
        ("slow_acknowledgement_count", _reason_count(report.rows, SLOW_ACK_REASON)),
    )
    for field_name, expected_value in expected_counts:
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")

    if report.average_diffusion_index != _average(row.diffusion_index for row in report.rows):
        raise ValueError("average_diffusion_index must match rows")
    if report.average_consensus_gap != _average(row.consensus_gap for row in report.rows):
        raise ValueError("average_consensus_gap must match rows")
    if report.contraction_ratio != _ratio(
        report.contraction_segment_count,
        report.segment_count,
    ):
        raise ValueError("contraction_ratio must match rows")
    if report.max_report_age_seconds != _max_decimal(
        row.report_age_seconds for row in report.rows
    ):
        raise ValueError("max_report_age_seconds must match rows")
    if report.reason_codes != _report_reasons(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _report_reason_counts(
        report.reason_codes,
        report.rows,
    ):
        raise ValueError("reason_code_counts must match rows")
    if report.digest_status != _report_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")


def _status_count(rows: tuple[MarketResearchPayrollDiffusionIndexDigestRow, ...], status: str) -> Decimal:
    return _count(sum(1 for row in rows if row.segment_status == status))


def _reason_count(rows: tuple[MarketResearchPayrollDiffusionIndexDigestRow, ...], reason_code: str) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _input_rows(rows: tuple[object, ...]) -> tuple[MarketResearchPayrollDiffusionIndexDigestInputRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not MarketResearchPayrollDiffusionIndexDigestInputRow:
            raise ValueError("rows must contain MarketResearchPayrollDiffusionIndexDigestInputRow")
        _hard_flags(row)
    return rows


def _rows(rows: tuple[MarketResearchPayrollDiffusionIndexDigestRow, ...]) -> tuple[MarketResearchPayrollDiffusionIndexDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not MarketResearchPayrollDiffusionIndexDigestRow:
            raise ValueError("rows must contain MarketResearchPayrollDiffusionIndexDigestRow")
        _hard_flags(row)
    expected = tuple(
        sorted(
            rows,
            key=lambda row: (_status_sort_key(row.segment_status), row.segment_key, row.research_key),
        ),
    )
    if rows != expected:
        raise ValueError("rows must use deterministic ordering")
    return rows


def _reason_code_counts_tuple(
    values: tuple[MarketResearchPayrollDiffusionIndexDigestReasonCodeCount, ...],
) -> tuple[MarketResearchPayrollDiffusionIndexDigestReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for value in values:
        if type(value) is not MarketResearchPayrollDiffusionIndexDigestReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count rows")
        _hard_flags(value)
    expected = tuple(sorted(values, key=lambda item: REASON_SEQUENCE.index(item.reason_code)))
    if values != expected:
        raise ValueError("reason_code_counts must use deterministic ordering")
    return values


def _reason_codes(codes: tuple[str, ...], sequence: tuple[str, ...]) -> tuple[str, ...]:
    if type(codes) is not tuple or not codes:
        raise ValueError("reason_codes must be a nonempty tuple")
    for code in codes:
        _reason_code("reason_code", code)
        if code not in sequence:
            raise ValueError("reason_codes must contain supported values")
    if len(set(codes)) != len(codes):
        raise ValueError("reason_codes must be unique")
    expected = tuple(code for code in sequence if code in codes)
    if codes != expected:
        raise ValueError("reason_codes must use deterministic ordering")
    return codes


def _payload(value: Any) -> Any:
    if type(value) is Decimal:
        return f"{value.quantize(QUANT):f}"
    if type(value) is datetime:
        return value.isoformat()
    if isinstance(value, tuple):
        return [_payload(item) for item in value]
    if isinstance(value, list):
        return [_payload(item) for item in value]
    if isinstance(value, dict):
        return {key: _payload(item) for key, item in value.items()}
    return value


def _redact(value: str) -> str:
    return "sha256:" + sha256(value.encode("utf-8")).hexdigest()


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    diff = later - earlier
    return _quant(Decimal(diff.days * 86400 + diff.seconds) + Decimal(diff.microseconds) / MICROS)


def _average(values: Any) -> Decimal | None:
    collected = tuple(values)
    if not collected:
        return None
    return _ratio(sum(collected, ZERO), _count(len(collected)))


def _max_decimal(values: Any) -> Decimal | None:
    collected = tuple(values)
    if not collected:
        return None
    return max(collected).quantize(QUANT)


def _ratio(value: Decimal, total: Decimal) -> Decimal:
    if total == ZERO:
        return ZERO
    with localcontext(CTX):
        return _quant(value / total)


def _count(value: int) -> Decimal:
    return _quant(Decimal(value))


def _quant(value: Decimal) -> Decimal:
    with localcontext(CTX):
        return value.quantize(QUANT)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{name} must be timezone-aware")
    if value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _plain_str(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a plain str")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical nonempty str")
    lowered = value.lower()
    if any(part in lowered for part in UNSAFE_PUBLIC_PARTS):
        raise ValueError(f"{name} must not contain restricted text")
    return value


def _redacted_source_reference(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a plain str")
    prefix = "sha256:"
    if not value.startswith(prefix):
        raise ValueError(f"{name} must be redacted")
    digest = value[len(prefix) :]
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise ValueError(f"{name} must be redacted")
    return value


def _status(name: str, value: object) -> str:
    _plain_str(name, value)
    if value not in STATUSES:
        raise ValueError(f"{name} must be supported")
    return value


def _reason_code(name: str, value: object) -> str:
    _plain_str(name, value)
    if value not in REASON_SEQUENCE:
        raise ValueError(f"{name} must be supported")
    return value


def _decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _quant(value)


def _nonnegative_decimal(name: str, value: object) -> Decimal:
    result = _decimal(name, value)
    if result < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return result


def _positive_decimal(name: str, value: object) -> Decimal:
    result = _decimal(name, value)
    if result <= ZERO:
        raise ValueError(f"{name} must be positive")
    return result


def _ratio_decimal(name: str, value: object) -> Decimal:
    result = _nonnegative_decimal(name, value)
    if result > ONE:
        raise ValueError(f"{name} must be no greater than 1")
    return result


def _nonnegative_count(name: str, value: object) -> Decimal:
    result = _nonnegative_decimal(name, value)
    if result != result.to_integral_value():
        raise ValueError(f"{name} must be integral")
    return result


def _positive_count(name: str, value: object) -> Decimal:
    result = _nonnegative_count(name, value)
    if result <= ZERO:
        raise ValueError(f"{name} must be positive")
    return result


def _hard_flags(value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only") is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly") is not True:
        raise ValueError("readonly must be True")
