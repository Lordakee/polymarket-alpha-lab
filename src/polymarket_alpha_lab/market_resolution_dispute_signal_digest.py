"""Pure Phase 1 reducer for market resolution dispute signal digests."""

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from types import MappingProxyType
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_MARKET_RESOLUTION_DISPUTE_SIGNAL_DIGEST_CONFIG_VERSION = (
    "market-resolution-dispute-signal-digest-v0"
)

REDACTED_SENSITIVE_REFERENCE = "<redacted-sensitive-reference>"
PASS_REASON_CODE = "market_resolution_dispute_signal_digest_passed"
EMPTY_REASON_CODE = "market_resolution_dispute_signal_digest_empty_sources"
ROW_PASS_REASON_CODE = "market_resolution_dispute_signal_row_passed"
DIGEST_BLOCKED_REASON_CODE = "market_resolution_dispute_signal_digest_blocked"
DISPUTE_SIGNAL_WATCH_REASON_CODE = "resolution_dispute_signal_watch"
DISPUTE_SIGNAL_HIGH_REASON_CODE = "resolution_dispute_signal_high"
SOURCE_CONFLICT_REASON_CODE = "resolution_source_conflict"
UNRESOLVED_EVIDENCE_REASON_CODE = "resolution_unresolved_evidence_present"
STALE_SIGNAL_REASON_CODE = "resolution_evidence_stale"

STATUSES = ("pass", "watch", "blocked")
REASON_CODES = (
    DIGEST_BLOCKED_REASON_CODE,
    DISPUTE_SIGNAL_HIGH_REASON_CODE,
    DISPUTE_SIGNAL_WATCH_REASON_CODE,
    EMPTY_REASON_CODE,
    PASS_REASON_CODE,
    ROW_PASS_REASON_CODE,
    SOURCE_CONFLICT_REASON_CODE,
    STALE_SIGNAL_REASON_CODE,
    UNRESOLVED_EVIDENCE_REASON_CODE,
)
NEXT_STEPS_BY_STATUS = {
    "pass": "continue_resolution_monitoring",
    "watch": "review_resolution_dispute_signals",
    "blocked": "pause_resolution_sensitive_review",
}
STATUS_RANK = {"blocked": 0, "watch": 1, "pass": 2}

ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANT = Decimal("0.000001")
HOURS_PER_DAY = Decimal("24")

__all__ = (
    "DEFAULT_MARKET_RESOLUTION_DISPUTE_SIGNAL_DIGEST_CONFIG_VERSION",
    "MarketResolutionDisputeSignalDigestConfig",
    "MarketResolutionDisputeSignalInput",
    "MarketResolutionDisputeSignalRow",
    "MarketResolutionDisputeSignalReasonCodeCount",
    "MarketResolutionDisputeSignalDigestReport",
    "build_market_resolution_dispute_signal_digest",
    "market_resolution_dispute_signal_digest_payload",
)


@dataclass(frozen=True)
class MarketResolutionDisputeSignalDigestConfig:
    config_version: str = DEFAULT_MARKET_RESOLUTION_DISPUTE_SIGNAL_DIGEST_CONFIG_VERSION
    watch_dispute_signal_score: Decimal = Decimal("0.300000")
    blocked_dispute_signal_score: Decimal = Decimal("0.700000")
    stale_signal_after_hours: Decimal = Decimal("24.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not MarketResolutionDisputeSignalDigestConfig:
            raise ValueError(
                "config must be exactly MarketResolutionDisputeSignalDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "watch_dispute_signal_score",
            _require_ratio_decimal(
                "watch_dispute_signal_score",
                self.watch_dispute_signal_score,
            ),
        )
        object.__setattr__(
            self,
            "blocked_dispute_signal_score",
            _require_ratio_decimal(
                "blocked_dispute_signal_score",
                self.blocked_dispute_signal_score,
            ),
        )
        object.__setattr__(
            self,
            "stale_signal_after_hours",
            _require_nonnegative_decimal(
                "stale_signal_after_hours",
                self.stale_signal_after_hours,
            ),
        )
        if self.blocked_dispute_signal_score < self.watch_dispute_signal_score:
            raise ValueError(
                "blocked_dispute_signal_score must be >= watch_dispute_signal_score",
            )
        _require_hard_flags("MarketResolutionDisputeSignalDigestConfig", self)


@dataclass(frozen=True)
class MarketResolutionDisputeSignalInput:
    market_slug: str
    category: str
    source_name: str
    observed_at: datetime
    dispute_signal_score: Decimal
    resolution_source_count: Decimal
    conflicting_source_count: Decimal
    unresolved_evidence_count: Decimal
    sensitive_reference: str = REDACTED_SENSITIVE_REFERENCE
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not MarketResolutionDisputeSignalInput:
            raise ValueError(
                "input must be exactly MarketResolutionDisputeSignalInput",
            )
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("category", self.category)
        _require_canonical_string("source_name", self.source_name)
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        object.__setattr__(
            self,
            "dispute_signal_score",
            _require_ratio_decimal(
                "dispute_signal_score",
                self.dispute_signal_score,
            ),
        )
        for field_name in (
            "resolution_source_count",
            "conflicting_source_count",
            "unresolved_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.conflicting_source_count > self.resolution_source_count:
            raise ValueError(
                "conflicting_source_count must be <= resolution_source_count",
            )
        object.__setattr__(
            self,
            "sensitive_reference",
            _redacted_sensitive_reference(self.sensitive_reference),
        )
        _require_hard_flags("MarketResolutionDisputeSignalInput", self)


@dataclass(frozen=True)
class MarketResolutionDisputeSignalRow:
    market_slug: str
    category: str
    source_name: str
    observed_at: datetime
    status: str
    dispute_signal_score: Decimal
    resolution_source_count: Decimal
    conflicting_source_count: Decimal
    unresolved_evidence_count: Decimal
    stale_signal_count: Decimal
    sensitive_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not MarketResolutionDisputeSignalRow:
            raise ValueError("row must be exactly MarketResolutionDisputeSignalRow")
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("category", self.category)
        _require_canonical_string("source_name", self.source_name)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "dispute_signal_score",
            _require_ratio_decimal("dispute_signal_score", self.dispute_signal_score),
        )
        for field_name in (
            "resolution_source_count",
            "conflicting_source_count",
            "unresolved_evidence_count",
            "stale_signal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.conflicting_source_count > self.resolution_source_count:
            raise ValueError(
                "conflicting_source_count must be <= resolution_source_count",
            )
        if self.sensitive_reference != REDACTED_SENSITIVE_REFERENCE:
            raise ValueError("sensitive_reference must be redacted")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _validate_row_consistency(self)
        _require_hard_flags("MarketResolutionDisputeSignalRow", self)


@dataclass(frozen=True)
class MarketResolutionDisputeSignalReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not MarketResolutionDisputeSignalReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "MarketResolutionDisputeSignalReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _require_positive_decimal("count", self.count))
        _require_hard_flags("MarketResolutionDisputeSignalReasonCodeCount", self)


@dataclass(frozen=True)
class MarketResolutionDisputeSignalDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    market_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    conflict_ratio: Decimal
    blocked_ratio: Decimal
    max_dispute_signal_score: Decimal
    rows: tuple[MarketResolutionDisputeSignalRow, ...]
    reason_code_counts: tuple[MarketResolutionDisputeSignalReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not MarketResolutionDisputeSignalDigestReport:
            raise ValueError(
                "report must be exactly MarketResolutionDisputeSignalDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "market_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "conflict_ratio",
            "blocked_ratio",
            "max_dispute_signal_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
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
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _validate_report_consistency(self)
        _require_hard_flags("MarketResolutionDisputeSignalDigestReport", self)


def build_market_resolution_dispute_signal_digest(
    signals: object,
    *,
    config: MarketResolutionDisputeSignalDigestConfig,
    generated_at: datetime,
) -> MarketResolutionDisputeSignalDigestReport:
    if type(config) is not MarketResolutionDisputeSignalDigestConfig:
        raise ValueError("config must be a MarketResolutionDisputeSignalDigestConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_rows = _normalize_inputs(signals)
    rows = tuple(
        _row_from_signal(signal, config=config, generated_at=generated_at_utc)
        for signal in source_rows
    )
    reason_codes = _report_reason_codes(rows)
    status = _report_status(rows)
    market_count = Decimal(len(rows))
    pass_count = _sum_decimal(ONE for row in rows if row.status == "pass")
    watch_count = _sum_decimal(ONE for row in rows if row.status == "watch")
    blocked_count = _sum_decimal(ONE for row in rows if row.status == "blocked")
    total_sources = _sum_decimal(row.resolution_source_count for row in rows)
    total_conflicts = _sum_decimal(row.conflicting_source_count for row in rows)
    return MarketResolutionDisputeSignalDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=status,
        recommended_next_step=_expected_next_step(status, rows),
        market_count=market_count,
        pass_count=pass_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        conflict_ratio=_ratio(total_conflicts, total_sources),
        blocked_ratio=_ratio(blocked_count, market_count),
        max_dispute_signal_score=_max_score(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
        reason_codes=reason_codes,
    )


def market_resolution_dispute_signal_digest_payload(
    report: MarketResolutionDisputeSignalDigestReport,
) -> MappingProxyType:
    if type(report) is not MarketResolutionDisputeSignalDigestReport:
        raise ValueError("report must be a MarketResolutionDisputeSignalDigestReport")
    _validate_report_consistency(report)
    payload = json_ready_no_floats(asdict(report))
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")
    return MappingProxyType(payload)


def _normalize_inputs(signals: object) -> tuple[MarketResolutionDisputeSignalInput, ...]:
    if type(signals) not in (list, tuple):
        raise ValueError("signals must be a list or tuple")
    rows = tuple(signals)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not MarketResolutionDisputeSignalInput:
            raise ValueError("signals must contain MarketResolutionDisputeSignalInput")
        _require_hard_flags("signal", row)
        if row.market_slug in seen:
            raise ValueError("signals market_slug values must be unique")
        seen.add(row.market_slug)
    return tuple(sorted(rows, key=lambda row: row.market_slug))


def _row_from_signal(
    signal: MarketResolutionDisputeSignalInput,
    *,
    config: MarketResolutionDisputeSignalDigestConfig,
    generated_at: datetime,
) -> MarketResolutionDisputeSignalRow:
    stale_signal_count = ONE if _is_stale(signal, config, generated_at) else ZERO
    reason_codes = _row_reason_codes(
        signal,
        config=config,
        stale_signal_count=stale_signal_count,
    )
    return MarketResolutionDisputeSignalRow(
        market_slug=signal.market_slug,
        category=signal.category,
        source_name=signal.source_name,
        observed_at=signal.observed_at,
        status=_status_from_row_reason_codes(reason_codes),
        dispute_signal_score=signal.dispute_signal_score,
        resolution_source_count=signal.resolution_source_count,
        conflicting_source_count=signal.conflicting_source_count,
        unresolved_evidence_count=signal.unresolved_evidence_count,
        stale_signal_count=stale_signal_count,
        sensitive_reference=REDACTED_SENSITIVE_REFERENCE,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    signal: MarketResolutionDisputeSignalInput,
    *,
    config: MarketResolutionDisputeSignalDigestConfig,
    stale_signal_count: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if signal.dispute_signal_score >= config.blocked_dispute_signal_score:
        reason_codes.append(DISPUTE_SIGNAL_HIGH_REASON_CODE)
    elif signal.dispute_signal_score >= config.watch_dispute_signal_score:
        reason_codes.append(DISPUTE_SIGNAL_WATCH_REASON_CODE)
    if signal.conflicting_source_count > ZERO:
        reason_codes.append(SOURCE_CONFLICT_REASON_CODE)
    if signal.unresolved_evidence_count > ZERO:
        reason_codes.append(UNRESOLVED_EVIDENCE_REASON_CODE)
    if stale_signal_count > ZERO:
        reason_codes.append(STALE_SIGNAL_REASON_CODE)
    if not reason_codes:
        reason_codes.append(ROW_PASS_REASON_CODE)
    return tuple(sorted(reason_codes))


def _is_stale(
    signal: MarketResolutionDisputeSignalInput,
    config: MarketResolutionDisputeSignalDigestConfig,
    generated_at: datetime,
) -> bool:
    age_seconds = Decimal(str((generated_at - signal.observed_at).total_seconds()))
    age_hours = age_seconds / Decimal("3600")
    return age_hours > config.stale_signal_after_hours


def _status_from_row_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if DISPUTE_SIGNAL_HIGH_REASON_CODE in reason_codes:
        return "blocked"
    if any(reason_code != ROW_PASS_REASON_CODE for reason_code in reason_codes):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[MarketResolutionDisputeSignalRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    reason_codes = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != ROW_PASS_REASON_CODE
    }
    status = _report_status(rows)
    if status == "pass":
        return (PASS_REASON_CODE,)
    if status == "blocked":
        reason_codes.add(DIGEST_BLOCKED_REASON_CODE)
    return tuple(sorted(reason_codes))


def _report_status(rows: tuple[MarketResolutionDisputeSignalRow, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.status == "blocked" for row in rows):
        return "blocked"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _expected_next_step(
    status: str,
    rows: tuple[MarketResolutionDisputeSignalRow, ...],
) -> str:
    if status == "blocked" and not rows:
        return "review_resolution_dispute_signals"
    return NEXT_STEPS_BY_STATUS[status]


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[MarketResolutionDisputeSignalRow, ...],
) -> tuple[MarketResolutionDisputeSignalReasonCodeCount, ...]:
    counts: dict[str, Decimal] = {reason_code: ZERO for reason_code in reason_codes}
    if not rows:
        counts[EMPTY_REASON_CODE] = ONE
    elif reason_codes == (PASS_REASON_CODE,):
        counts[PASS_REASON_CODE] = ONE
    else:
        for row in rows:
            for reason_code in row.reason_codes:
                if reason_code == ROW_PASS_REASON_CODE:
                    continue
                counts[reason_code] = counts.get(reason_code, ZERO) + ONE
        if DIGEST_BLOCKED_REASON_CODE in counts:
            counts[DIGEST_BLOCKED_REASON_CODE] = ONE
    return tuple(
        MarketResolutionDisputeSignalReasonCodeCount(
            reason_code=reason_code,
            count=count,
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _normalize_rows(value: object) -> tuple[MarketResolutionDisputeSignalRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    rows = tuple(value)
    seen: set[str] = set()
    previous_key: tuple[int, Decimal, str] | None = None
    for row in rows:
        if type(row) is not MarketResolutionDisputeSignalRow:
            raise ValueError("rows must contain exact signal rows")
        _require_hard_flags("row", row)
        if row.market_slug in seen:
            raise ValueError("rows must contain unique market_slug values")
        key = (STATUS_RANK[row.status], -row.dispute_signal_score, row.market_slug)
        if previous_key is not None and previous_key > key:
            raise ValueError("rows must be deterministically sorted")
        previous_key = key
        seen.add(row.market_slug)
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[MarketResolutionDisputeSignalReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    rows = tuple(value)
    seen: set[str] = set()
    previous_key: tuple[Decimal, str] | None = None
    for row in rows:
        if type(row) is not MarketResolutionDisputeSignalReasonCodeCount:
            raise ValueError("reason_code_counts must contain exact reason count rows")
        _require_hard_flags("reason_code_count", row)
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        key = (-row.count, row.reason_code)
        if previous_key is not None and previous_key > key:
            raise ValueError("reason_code_counts must be deterministically sorted")
        previous_key = key
        seen.add(row.reason_code)
    return rows


def _normalize_reason_codes(
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    reason_codes = tuple(value)
    if not allow_empty and not reason_codes:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    previous: str | None = None
    for reason_code in reason_codes:
        _require_reason_code("reason_codes", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        if previous is not None and previous > reason_code:
            raise ValueError("reason_codes must be sorted")
        previous = reason_code
        seen.add(reason_code)
    return reason_codes


def _validate_row_consistency(row: MarketResolutionDisputeSignalRow) -> None:
    if row.status != _status_from_row_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and row.reason_codes != (ROW_PASS_REASON_CODE,):
        raise ValueError("pass rows must use pass reason code")
    if row.status != "pass" and row.reason_codes == (ROW_PASS_REASON_CODE,):
        raise ValueError("non-pass rows must not use pass reason code")


def _validate_report_consistency(
    report: MarketResolutionDisputeSignalDigestReport,
) -> None:
    rows = report.rows
    if report.recommended_next_step != _expected_next_step(report.digest_status, rows):
        raise ValueError("recommended_next_step must match digest_status")
    if report.market_count != Decimal(len(rows)):
        raise ValueError("market_count must match rows")
    if report.market_count != report.pass_count + report.watch_count + report.blocked_count:
        raise ValueError("status counts must sum to market_count")
    if report.pass_count != _sum_decimal(ONE for row in rows if row.status == "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _sum_decimal(ONE for row in rows if row.status == "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _sum_decimal(ONE for row in rows if row.status == "blocked"):
        raise ValueError("blocked_count must match rows")
    total_sources = _sum_decimal(row.resolution_source_count for row in rows)
    total_conflicts = _sum_decimal(row.conflicting_source_count for row in rows)
    if report.conflict_ratio != _ratio(total_conflicts, total_sources):
        raise ValueError("conflict_ratio must match rows")
    if report.blocked_ratio != _ratio(report.blocked_count, report.market_count):
        raise ValueError("blocked_ratio must match rows")
    if report.max_dispute_signal_score != _max_score(rows):
        raise ValueError("max_dispute_signal_score must match rows")
    if report.digest_status != _report_status(rows):
        raise ValueError("digest_status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, rows):
        raise ValueError("reason_code_counts must match rows")


def _max_score(rows: tuple[MarketResolutionDisputeSignalRow, ...]) -> Decimal:
    if not rows:
        return _quantize_ratio(ZERO)
    return max(row.dispute_signal_score for row in rows)


def _redacted_sensitive_reference(value: object) -> str:
    _require_canonical_string("sensitive_reference", value)
    return REDACTED_SENSITIVE_REFERENCE


def _require_hard_flags(label: str, value: object) -> None:
    require_paper_only_flags(label, value)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REASON_CODES:
        raise ValueError(f"{field_name} must be a known reason code")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite() or value < ZERO:
        raise ValueError(f"{field_name} must be a finite nonnegative Decimal")
    return value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    value = _require_nonnegative_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    value = _require_nonnegative_decimal(field_name, value)
    if value > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return _quantize_ratio(value)


def _quantize_ratio(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANT, rounding=ROUND_HALF_UP)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return _quantize_ratio(ZERO)
    return _quantize_ratio(numerator / denominator)


def _sum_decimal(values: Any) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return total
