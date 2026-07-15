"""Paper-only candidate memory context readiness report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import re


DEFAULT_CANDIDATE_MEMORY_CONTEXT_READINESS_REPORT_CONFIG_VERSION = (
    "candidate-memory-context-readiness-report-v0"
)
CANDIDATE_MEMORY_CONTEXT_READINESS_STATUSES = ("ready", "attention", "blocker")

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
REQUIRED_CONTEXT_COUNT = Decimal("7.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
CANDIDATE_REF_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,95}$")
REASON_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{1,127}$")

STATUS_RANK = {"ready": 0, "attention": 1, "blocker": 2}
REASON_SEQUENCE = (
    "team_route_missing_blocker",
    "memory_readiness_digest_missing_blocker",
    "event_category_memory_missing_blocker",
    "source_family_feedback_missing_blocker",
    "settled_outcome_calibration_missing_blocker",
    "specialist_memory_missing_blocker",
    "domain_memory_missing_attention",
    "manual_memory_refresh_attention",
    "memory_context_ready",
)
REPORT_REASON_SEQUENCE = (
    "candidate_memory_context_no_candidates_blocker",
    *REASON_SEQUENCE,
)

__all__ = (
    "DEFAULT_CANDIDATE_MEMORY_CONTEXT_READINESS_REPORT_CONFIG_VERSION",
    "CANDIDATE_MEMORY_CONTEXT_READINESS_STATUSES",
    "CandidateMemoryContextReadinessReasonCodeCount",
    "CandidateMemoryContextReadinessReport",
    "CandidateMemoryContextReadinessRow",
    "CandidateMemoryContextReadinessSignal",
    "build_candidate_memory_context_readiness_report",
    "candidate_memory_context_readiness_report_payload",
)


@dataclass(frozen=True)
class CandidateMemoryContextReadinessSignal:
    candidate_ref: str
    team_route_ready: bool
    memory_readiness_digest_ready: bool
    event_category_memory_ready: bool
    source_family_feedback_ready: bool
    settled_outcome_calibration_ready: bool
    specialist_memory_ready: bool
    domain_memory_ready: bool
    observed_at: datetime
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, CandidateMemoryContextReadinessSignal, "signal")
        _require_candidate_ref("candidate_ref", self.candidate_ref)
        for field_name in (
            "team_route_ready",
            "memory_readiness_digest_ready",
            "event_category_memory_ready",
            "source_family_feedback_ready",
            "settled_outcome_calibration_ready",
            "specialist_memory_ready",
            "domain_memory_ready",
        ):
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(self.reason_codes, require_nonempty=False),
        )
        _require_hard_flags("signal", self)


@dataclass(frozen=True)
class CandidateMemoryContextReadinessRow:
    public_row_number: Decimal
    status: str
    memory_context_ready: bool
    team_route_ready: bool
    memory_readiness_digest_ready: bool
    event_category_memory_ready: bool
    source_family_feedback_ready: bool
    settled_outcome_calibration_ready: bool
    specialist_memory_ready: bool
    domain_memory_ready: bool
    ready_context_count: Decimal
    missing_context_count: Decimal
    readiness_ratio: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, CandidateMemoryContextReadinessRow, "row")
        object.__setattr__(
            self,
            "public_row_number",
            _require_positive_count_decimal("public_row_number", self.public_row_number),
        )
        _require_status("status", self.status)
        for field_name in (
            "memory_context_ready",
            "team_route_ready",
            "memory_readiness_digest_ready",
            "event_category_memory_ready",
            "source_family_feedback_ready",
            "settled_outcome_calibration_ready",
            "specialist_memory_ready",
            "domain_memory_ready",
        ):
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "ready_context_count",
            _require_count_decimal("ready_context_count", self.ready_context_count),
        )
        object.__setattr__(
            self,
            "missing_context_count",
            _require_count_decimal("missing_context_count", self.missing_context_count),
        )
        object.__setattr__(
            self,
            "readiness_ratio",
            _require_ratio_decimal("readiness_ratio", self.readiness_ratio),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _require_hard_flags("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class CandidateMemoryContextReadinessReasonCodeCount:
    reason_code: str
    count: Decimal
    ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_codes((self.reason_code,), require_nonempty=True)
        object.__setattr__(
            self,
            "count",
            _require_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "ratio",
            _require_ratio_decimal("ratio", self.ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class CandidateMemoryContextReadinessReport:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    ready_count: Decimal
    attention_count: Decimal
    blocker_count: Decimal
    memory_context_ready_count: Decimal
    missing_context_count: Decimal
    ready_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[CandidateMemoryContextReadinessReasonCodeCount, ...]
    rows: tuple[CandidateMemoryContextReadinessRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, CandidateMemoryContextReadinessReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        if self.config_version != DEFAULT_CANDIDATE_MEMORY_CONTEXT_READINESS_REPORT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "candidate_count",
            "ready_count",
            "attention_count",
            "blocker_count",
            "memory_context_ready_count",
            "missing_context_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "ready_ratio",
            _require_ratio_decimal("ready_ratio", self.ready_ratio),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _require_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _require_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _require_rows(self.rows))
        _require_hard_flags("report", self)
        _validate_report(self)


def build_candidate_memory_context_readiness_report(
    signals: Iterable[CandidateMemoryContextReadinessSignal],
    *,
    generated_at: datetime,
) -> CandidateMemoryContextReadinessReport:
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_signals = _normalize_signals(signals)
    for signal in normalized_signals:
        if signal.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")
    row_values = tuple(sorted((_row_values_from_signal(signal) for signal in normalized_signals), key=_row_value_sort_key))
    rows = tuple(
        CandidateMemoryContextReadinessRow(
            public_row_number=_count(index),
            **_public_row_value(row_value),
        )
        for index, row_value in enumerate(row_values, start=1)
    )
    total = _count(len(rows))
    ready_count = _status_count(rows, "ready")
    attention_count = _status_count(rows, "attention")
    blocker_count = _status_count(rows, "blocker")
    reason_codes = _report_reason_codes(rows)

    return CandidateMemoryContextReadinessReport(
        generated_at=generated_at_utc,
        config_version=DEFAULT_CANDIDATE_MEMORY_CONTEXT_READINESS_REPORT_CONFIG_VERSION,
        candidate_count=total,
        ready_count=ready_count,
        attention_count=attention_count,
        blocker_count=blocker_count,
        memory_context_ready_count=_count(sum(row.memory_context_ready for row in rows)),
        missing_context_count=sum(
            (row.missing_context_count for row in rows),
            ZERO,
        ),
        ready_ratio=_ratio(ready_count, total),
        status=_report_status(rows),
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        rows=rows,
    )


def candidate_memory_context_readiness_report_payload(
    report: CandidateMemoryContextReadinessReport,
) -> dict[str, object]:
    if type(report) is not CandidateMemoryContextReadinessReport:
        raise ValueError("report must be a CandidateMemoryContextReadinessReport")
    _require_hard_flags("report", report)
    for row in report.rows:
        _require_hard_flags("row", row)
    for count in report.reason_code_counts:
        _require_hard_flags("reason_code_count", count)
    _validate_report(report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _row_values_from_signal(signal: CandidateMemoryContextReadinessSignal) -> dict[str, object]:
    ready_count = _count(
        sum(
            (
                signal.team_route_ready,
                signal.memory_readiness_digest_ready,
                signal.event_category_memory_ready,
                signal.source_family_feedback_ready,
                signal.settled_outcome_calibration_ready,
                signal.specialist_memory_ready,
                signal.domain_memory_ready,
            ),
        ),
    )
    missing_count = REQUIRED_CONTEXT_COUNT - ready_count
    reason_codes = _row_reason_codes(signal)
    return {
        "status": _row_status(reason_codes),
        "memory_context_ready": missing_count == ZERO,
        "team_route_ready": signal.team_route_ready,
        "memory_readiness_digest_ready": signal.memory_readiness_digest_ready,
        "event_category_memory_ready": signal.event_category_memory_ready,
        "source_family_feedback_ready": signal.source_family_feedback_ready,
        "settled_outcome_calibration_ready": signal.settled_outcome_calibration_ready,
        "specialist_memory_ready": signal.specialist_memory_ready,
        "domain_memory_ready": signal.domain_memory_ready,
        "ready_context_count": ready_count,
        "missing_context_count": missing_count,
        "readiness_ratio": _ratio(ready_count, REQUIRED_CONTEXT_COUNT),
        "observed_at": signal.observed_at,
        "reason_codes": reason_codes,
        "_candidate_ref": signal.candidate_ref,
    }


def _row_reason_codes(signal: CandidateMemoryContextReadinessSignal) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if not signal.team_route_ready:
        reason_codes.append("team_route_missing_blocker")
    if not signal.memory_readiness_digest_ready:
        reason_codes.append("memory_readiness_digest_missing_blocker")
    if not signal.event_category_memory_ready:
        reason_codes.append("event_category_memory_missing_blocker")
    if not signal.source_family_feedback_ready:
        reason_codes.append("source_family_feedback_missing_blocker")
    if not signal.settled_outcome_calibration_ready:
        reason_codes.append("settled_outcome_calibration_missing_blocker")
    if not signal.specialist_memory_ready:
        reason_codes.append("specialist_memory_missing_blocker")
    if not signal.domain_memory_ready:
        reason_codes.append("domain_memory_missing_attention")
    reason_codes.extend(signal.reason_codes)
    if not reason_codes:
        reason_codes.append("memory_context_ready")
    return _require_reason_codes(tuple(reason_codes), require_nonempty=True)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_blocker") for reason_code in reason_codes):
        return "blocker"
    if any(reason_code.endswith("_attention") for reason_code in reason_codes):
        return "attention"
    return "ready"


def _report_status(rows: tuple[CandidateMemoryContextReadinessRow, ...]) -> str:
    if not rows:
        return "blocker"
    if any(row.status == "blocker" for row in rows):
        return "blocker"
    if any(row.status == "attention" for row in rows):
        return "attention"
    return "ready"


def _report_reason_codes(
    rows: tuple[CandidateMemoryContextReadinessRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("candidate_memory_context_no_candidates_blocker",)
    found = {reason_code for row in rows for reason_code in row.reason_codes}
    return tuple(reason_code for reason_code in REASON_SEQUENCE if reason_code in found)


def _reason_code_counts(
    rows: tuple[CandidateMemoryContextReadinessRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[CandidateMemoryContextReadinessReasonCodeCount, ...]:
    if not rows:
        return (
            CandidateMemoryContextReadinessReasonCodeCount(
                reason_code="candidate_memory_context_no_candidates_blocker",
                count=ONE,
                ratio=ONE,
            ),
        )
    counts = Counter(reason_code for row in rows for reason_code in row.reason_codes)
    total = _count(len(rows))
    return tuple(
        CandidateMemoryContextReadinessReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
            ratio=_ratio(_count(counts[reason_code]), total),
        )
        for reason_code in reason_codes
        if reason_code in counts
    )


def _row_value_sort_key(row_value: dict[str, object]) -> tuple[int, str]:
    status = row_value["status"]
    if type(status) is not str:
        raise ValueError("status must be a string")
    candidate_ref = row_value["_candidate_ref"]
    if type(candidate_ref) is not str:
        raise ValueError("candidate_ref must be a string")
    return (-STATUS_RANK[status], candidate_ref)


def _public_row_value(row_value: dict[str, object]) -> dict[str, object]:
    return {key: value for key, value in row_value.items() if key != "_candidate_ref"}


def _row_sort_key(row: CandidateMemoryContextReadinessRow) -> tuple[int, Decimal]:
    return (-STATUS_RANK[row.status], row.public_row_number)


def _status_count(
    rows: tuple[CandidateMemoryContextReadinessRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _normalize_signals(
    signals: Iterable[CandidateMemoryContextReadinessSignal],
) -> tuple[CandidateMemoryContextReadinessSignal, ...]:
    if isinstance(signals, (str, bytes)):
        raise ValueError("signals must be an iterable")
    try:
        values = tuple(signals)
    except TypeError as exc:
        raise ValueError("signals must be an iterable") from exc
    refs: set[str] = set()
    for value in values:
        if type(value) is not CandidateMemoryContextReadinessSignal:
            raise ValueError(
                "signals must contain CandidateMemoryContextReadinessSignal values",
            )
        _require_hard_flags("signal", value)
        if value.candidate_ref in refs:
            raise ValueError("duplicate candidate_ref values are not allowed")
        refs.add(value.candidate_ref)
    return values


def _require_rows(
    rows: Iterable[CandidateMemoryContextReadinessRow],
) -> tuple[CandidateMemoryContextReadinessRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    values = tuple(rows)
    previous_sort_key: tuple[int, Decimal] | None = None
    expected_number = ONE
    for row in values:
        if type(row) is not CandidateMemoryContextReadinessRow:
            raise ValueError("rows must contain CandidateMemoryContextReadinessRow values")
        _require_hard_flags("row", row)
        if row.public_row_number != expected_number:
            raise ValueError("public_row_number values must be sequential")
        expected_number = _count(int(expected_number) + 1)
        sort_key = _row_sort_key(row)
        if previous_sort_key is not None and previous_sort_key > sort_key:
            raise ValueError("rows must be sorted deterministically")
        previous_sort_key = sort_key
    return values


def _require_reason_code_counts(
    values: Iterable[CandidateMemoryContextReadinessReasonCodeCount],
) -> tuple[CandidateMemoryContextReadinessReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    items = tuple(values)
    previous_index = -1
    seen: set[str] = set()
    for item in items:
        if type(item) is not CandidateMemoryContextReadinessReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain CandidateMemoryContextReadinessReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", item)
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        seen.add(item.reason_code)
        index = REPORT_REASON_SEQUENCE.index(item.reason_code)
        if index <= previous_index:
            raise ValueError("reason_code_counts must be sorted deterministically")
        previous_index = index
    return items


def _validate_row(row: CandidateMemoryContextReadinessRow) -> None:
    ready_context_count = _count(
        sum(
            (
                row.team_route_ready,
                row.memory_readiness_digest_ready,
                row.event_category_memory_ready,
                row.source_family_feedback_ready,
                row.settled_outcome_calibration_ready,
                row.specialist_memory_ready,
                row.domain_memory_ready,
            ),
        ),
    )
    missing_context_count = REQUIRED_CONTEXT_COUNT - ready_context_count
    if row.ready_context_count != ready_context_count:
        raise ValueError("ready_context_count must match row flags")
    if row.missing_context_count != missing_context_count:
        raise ValueError("missing_context_count must match row flags")
    if row.readiness_ratio != _ratio(ready_context_count, REQUIRED_CONTEXT_COUNT):
        raise ValueError("readiness_ratio must match row flags")
    if row.memory_context_ready != (missing_context_count == ZERO):
        raise ValueError("memory_context_ready must match row flags")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.memory_context_ready and row.reason_codes != ("memory_context_ready",):
        raise ValueError("ready rows must use memory_context_ready reason")


def _validate_report(report: CandidateMemoryContextReadinessReport) -> None:
    total = _count(len(report.rows))
    if report.candidate_count != total:
        raise ValueError("candidate_count must match rows")
    if report.ready_count != _status_count(report.rows, "ready"):
        raise ValueError("ready_count must match rows")
    if report.attention_count != _status_count(report.rows, "attention"):
        raise ValueError("attention_count must match rows")
    if report.blocker_count != _status_count(report.rows, "blocker"):
        raise ValueError("blocker_count must match rows")
    if report.memory_context_ready_count != _count(
        sum(row.memory_context_ready for row in report.rows),
    ):
        raise ValueError("memory_context_ready_count must match rows")
    if report.missing_context_count != sum(
        (row.missing_context_count for row in report.rows),
        ZERO,
    ):
        raise ValueError("missing_context_count must match rows")
    if report.ready_ratio != _ratio(report.ready_count, total):
        raise ValueError("ready_ratio must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _require_report_reason_codes(values: Iterable[str]) -> tuple[str, ...]:
    reason_codes = _require_reason_codes(tuple(values), require_nonempty=True)
    previous_index = -1
    for reason_code in reason_codes:
        index = REPORT_REASON_SEQUENCE.index(reason_code)
        if index <= previous_index:
            raise ValueError("reason_codes must be sorted deterministically")
        previous_index = index
    return reason_codes


def _require_reason_codes(
    values: Iterable[str],
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if require_nonempty and not values:
        raise ValueError("reason_codes must not be empty")
    normalized: list[str] = []
    seen: set[str] = set()
    for reason_code in values:
        if type(reason_code) is not str or not REASON_CODE_RE.fullmatch(reason_code):
            raise ValueError("reason_codes must contain canonical values")
        if reason_code not in REPORT_REASON_SEQUENCE:
            raise ValueError("reason_codes contains unsupported value")
        if reason_code not in seen:
            normalized.append(reason_code)
            seen.add(reason_code)
    return tuple(normalized)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in CANDIDATE_MEMORY_CONTEXT_READINESS_STATUSES:
        raise ValueError(f"{field_name} must be a supported status")


def _require_candidate_ref(field_name: str, value: object) -> None:
    if type(value) is not str or not CANDIDATE_REF_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a canonical public reference")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    return _quantize(value)


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_count_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime or value.tzinfo is None:
        raise ValueError(f"{field_name} must be a timezone-aware datetime")
    return value.astimezone(UTC)


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _json_ready(value: object) -> object:
    if isinstance(value, Decimal):
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if type(value) is bool or value is None or type(value) is str:
        return value
    raise ValueError("payload contains unsupported value")
