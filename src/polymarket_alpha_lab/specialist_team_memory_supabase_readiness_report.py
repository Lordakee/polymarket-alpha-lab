"""Paper-only specialist team memory Supabase readiness report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import re
from typing import Any


DEFAULT_SPECIALIST_TEAM_MEMORY_SUPABASE_READINESS_CONFIG_VERSION = (
    "specialist-team-memory-supabase-readiness-report-v0"
)
SPECIALIST_TEAM_MEMORY_SUPABASE_READINESS_STATUSES = (
    "ready",
    "attention",
    "blocker",
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
REQUIRED_SIGNAL_COUNT = Decimal("4.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
TEAM_LABEL_RE = re.compile(r"^team_[a-z0-9][a-z0-9_]{0,63}$")

STATUS_RANK = {"ready": 0, "attention": 1, "blocker": 2}
REASON_SEQUENCE = (
    "specialist_team_long_term_memory_table_blocker",
    "specialist_team_memory_event_table_blocker",
    "specialist_team_calibration_table_blocker",
    "specialist_team_memory_supabase_schema_contract_attention",
    "specialist_team_memory_supabase_ready",
)
REPORT_REASON_SEQUENCE = (
    "specialist_team_memory_supabase_no_specialist_teams",
    *REASON_SEQUENCE,
)

__all__ = (
    "DEFAULT_SPECIALIST_TEAM_MEMORY_SUPABASE_READINESS_CONFIG_VERSION",
    "SPECIALIST_TEAM_MEMORY_SUPABASE_READINESS_STATUSES",
    "SpecialistTeamMemorySupabaseReadinessReasonCodeCount",
    "SpecialistTeamMemorySupabaseReadinessReport",
    "SpecialistTeamMemorySupabaseReadinessRow",
    "SpecialistTeamMemorySupabaseReadinessSignal",
    "build_specialist_team_memory_supabase_readiness_report",
    "specialist_team_memory_supabase_readiness_report_payload",
)


@dataclass(frozen=True)
class SpecialistTeamMemorySupabaseReadinessSignal:
    specialist_team_label: str
    long_term_memory_table_ready: bool
    memory_event_table_ready: bool
    calibration_table_ready: bool
    local_supabase_schema_contract_ready: bool
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_team_label("specialist_team_label", self.specialist_team_label)
        for field_name in (
            "long_term_memory_table_ready",
            "memory_event_table_ready",
            "calibration_table_ready",
            "local_supabase_schema_contract_ready",
        ):
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("signal", self)


@dataclass(frozen=True)
class SpecialistTeamMemorySupabaseReadinessRow:
    specialist_team_label: str
    status: str
    long_term_memory_table_ready: bool
    memory_event_table_ready: bool
    calibration_table_ready: bool
    local_supabase_schema_contract_ready: bool
    ready_signal_count: Decimal
    required_signal_count: Decimal
    readiness_ratio: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_team_label("specialist_team_label", self.specialist_team_label)
        _require_status("status", self.status)
        for field_name in (
            "long_term_memory_table_ready",
            "memory_event_table_ready",
            "calibration_table_ready",
            "local_supabase_schema_contract_ready",
        ):
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "ready_signal_count",
            _require_count_decimal("ready_signal_count", self.ready_signal_count),
        )
        object.__setattr__(
            self,
            "required_signal_count",
            _require_count_decimal("required_signal_count", self.required_signal_count),
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


@dataclass(frozen=True)
class SpecialistTeamMemorySupabaseReadinessReasonCodeCount:
    reason_code: str
    specialist_team_count: Decimal
    specialist_team_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_codes((self.reason_code,), require_nonempty=True)
        object.__setattr__(
            self,
            "specialist_team_count",
            _require_count_decimal(
                "specialist_team_count",
                self.specialist_team_count,
            ),
        )
        object.__setattr__(
            self,
            "specialist_team_ratio",
            _require_ratio_decimal(
                "specialist_team_ratio",
                self.specialist_team_ratio,
            ),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class SpecialistTeamMemorySupabaseReadinessReport:
    generated_at: datetime
    config_version: str
    specialist_team_count: Decimal
    ready_count: Decimal
    attention_count: Decimal
    blocker_count: Decimal
    ready_ratio: Decimal
    attention_ratio: Decimal
    blocker_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[SpecialistTeamMemorySupabaseReadinessReasonCodeCount, ...]
    rows: tuple[SpecialistTeamMemorySupabaseReadinessRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        if self.config_version != DEFAULT_SPECIALIST_TEAM_MEMORY_SUPABASE_READINESS_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "specialist_team_count",
            "ready_count",
            "attention_count",
            "blocker_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("ready_ratio", "attention_ratio", "blocker_ratio"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
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


def build_specialist_team_memory_supabase_readiness_report(
    signals: Iterable[SpecialistTeamMemorySupabaseReadinessSignal],
    *,
    generated_at: datetime,
) -> SpecialistTeamMemorySupabaseReadinessReport:
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_signals = _normalize_signals(signals)
    rows = tuple(sorted((_row_from_signal(signal) for signal in normalized_signals), key=_row_sort_key))
    total = _count(len(rows))
    ready_count = _status_count(rows, "ready")
    attention_count = _status_count(rows, "attention")
    blocker_count = _status_count(rows, "blocker")
    reason_codes = _report_reason_codes(rows)

    return SpecialistTeamMemorySupabaseReadinessReport(
        generated_at=generated_at_utc,
        config_version=DEFAULT_SPECIALIST_TEAM_MEMORY_SUPABASE_READINESS_CONFIG_VERSION,
        specialist_team_count=total,
        ready_count=ready_count,
        attention_count=attention_count,
        blocker_count=blocker_count,
        ready_ratio=_ratio(ready_count, total),
        attention_ratio=_ratio(attention_count, total),
        blocker_ratio=_ratio(blocker_count, total),
        status=_report_status(rows),
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        rows=rows,
    )


def specialist_team_memory_supabase_readiness_report_payload(
    report: SpecialistTeamMemorySupabaseReadinessReport,
) -> dict[str, object]:
    if type(report) is not SpecialistTeamMemorySupabaseReadinessReport:
        raise ValueError("report must be a SpecialistTeamMemorySupabaseReadinessReport")
    _require_hard_flags("report", report)
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _row_from_signal(
    signal: SpecialistTeamMemorySupabaseReadinessSignal,
) -> SpecialistTeamMemorySupabaseReadinessRow:
    ready_signal_count = _count(
        sum(
            (
                signal.long_term_memory_table_ready,
                signal.memory_event_table_ready,
                signal.calibration_table_ready,
                signal.local_supabase_schema_contract_ready,
            ),
        ),
    )
    reason_codes = _row_reason_codes(signal)
    return SpecialistTeamMemorySupabaseReadinessRow(
        specialist_team_label=signal.specialist_team_label,
        status=_row_status(reason_codes),
        long_term_memory_table_ready=signal.long_term_memory_table_ready,
        memory_event_table_ready=signal.memory_event_table_ready,
        calibration_table_ready=signal.calibration_table_ready,
        local_supabase_schema_contract_ready=(
            signal.local_supabase_schema_contract_ready
        ),
        ready_signal_count=ready_signal_count,
        required_signal_count=REQUIRED_SIGNAL_COUNT,
        readiness_ratio=_ratio(ready_signal_count, REQUIRED_SIGNAL_COUNT),
        observed_at=signal.observed_at,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    signal: SpecialistTeamMemorySupabaseReadinessSignal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if not signal.long_term_memory_table_ready:
        reason_codes.append("specialist_team_long_term_memory_table_blocker")
    if not signal.memory_event_table_ready:
        reason_codes.append("specialist_team_memory_event_table_blocker")
    if not signal.calibration_table_ready:
        reason_codes.append("specialist_team_calibration_table_blocker")
    if (
        signal.long_term_memory_table_ready
        and signal.memory_event_table_ready
        and signal.calibration_table_ready
        and not signal.local_supabase_schema_contract_ready
    ):
        reason_codes.append(
            "specialist_team_memory_supabase_schema_contract_attention",
        )
    if not reason_codes:
        reason_codes.append("specialist_team_memory_supabase_ready")
    return _require_reason_codes(tuple(reason_codes), require_nonempty=True)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_blocker") for reason_code in reason_codes):
        return "blocker"
    if any(reason_code.endswith("_attention") for reason_code in reason_codes):
        return "attention"
    return "ready"


def _report_status(rows: tuple[SpecialistTeamMemorySupabaseReadinessRow, ...]) -> str:
    if any(row.status == "blocker" for row in rows):
        return "blocker"
    if any(row.status == "attention" for row in rows):
        return "attention"
    return "ready"


def _report_reason_codes(
    rows: tuple[SpecialistTeamMemorySupabaseReadinessRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("specialist_team_memory_supabase_no_specialist_teams",)
    found = {reason_code for row in rows for reason_code in row.reason_codes}
    return tuple(reason_code for reason_code in REASON_SEQUENCE if reason_code in found)


def _reason_code_counts(
    rows: tuple[SpecialistTeamMemorySupabaseReadinessRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[SpecialistTeamMemorySupabaseReadinessReasonCodeCount, ...]:
    if not rows:
        return ()
    counts = Counter(reason_code for row in rows for reason_code in row.reason_codes)
    total = _count(len(rows))
    return tuple(
        SpecialistTeamMemorySupabaseReadinessReasonCodeCount(
            reason_code=reason_code,
            specialist_team_count=_count(counts[reason_code]),
            specialist_team_ratio=_ratio(_count(counts[reason_code]), total),
        )
        for reason_code in reason_codes
        if reason_code in counts
    )


def _row_sort_key(row: SpecialistTeamMemorySupabaseReadinessRow) -> tuple[int, str]:
    return (-STATUS_RANK[row.status], row.specialist_team_label)


def _status_count(
    rows: tuple[SpecialistTeamMemorySupabaseReadinessRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _normalize_signals(
    signals: Iterable[SpecialistTeamMemorySupabaseReadinessSignal],
) -> tuple[SpecialistTeamMemorySupabaseReadinessSignal, ...]:
    if isinstance(signals, (str, bytes)):
        raise ValueError("signals must be an iterable")
    try:
        values = tuple(signals)
    except TypeError as exc:
        raise ValueError("signals must be an iterable") from exc
    labels: set[str] = set()
    for value in values:
        if type(value) is not SpecialistTeamMemorySupabaseReadinessSignal:
            raise ValueError(
                "signals must contain SpecialistTeamMemorySupabaseReadinessSignal values",
            )
        _require_hard_flags("signal", value)
        if value.specialist_team_label in labels:
            raise ValueError("specialist_team_label values must be unique")
        labels.add(value.specialist_team_label)
    return values


def _require_rows(
    rows: Iterable[SpecialistTeamMemorySupabaseReadinessRow],
) -> tuple[SpecialistTeamMemorySupabaseReadinessRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    values = tuple(rows)
    labels: set[str] = set()
    previous_sort_key: tuple[int, str] | None = None
    for row in values:
        if type(row) is not SpecialistTeamMemorySupabaseReadinessRow:
            raise ValueError("rows must contain SpecialistTeamMemorySupabaseReadinessRow values")
        _require_hard_flags("row", row)
        if row.specialist_team_label in labels:
            raise ValueError("rows must have unique specialist_team_label values")
        labels.add(row.specialist_team_label)
        sort_key = _row_sort_key(row)
        if previous_sort_key is not None and previous_sort_key > sort_key:
            raise ValueError("rows must be sorted deterministically")
        previous_sort_key = sort_key
    return values


def _require_reason_code_counts(
    values: Iterable[SpecialistTeamMemorySupabaseReadinessReasonCodeCount],
) -> tuple[SpecialistTeamMemorySupabaseReadinessReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    items = tuple(values)
    previous_index = -1
    seen: set[str] = set()
    for item in items:
        if type(item) is not SpecialistTeamMemorySupabaseReadinessReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain SpecialistTeamMemorySupabaseReadinessReasonCodeCount values",
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


def _validate_report(report: SpecialistTeamMemorySupabaseReadinessReport) -> None:
    total = _count(len(report.rows))
    if report.specialist_team_count != total:
        raise ValueError("specialist_team_count must match rows")
    if report.ready_count != _status_count(report.rows, "ready"):
        raise ValueError("ready_count must match rows")
    if report.attention_count != _status_count(report.rows, "attention"):
        raise ValueError("attention_count must match rows")
    if report.blocker_count != _status_count(report.rows, "blocker"):
        raise ValueError("blocker_count must match rows")
    if report.ready_ratio != _ratio(report.ready_count, total):
        raise ValueError("ready_ratio must match rows")
    if report.attention_ratio != _ratio(report.attention_count, total):
        raise ValueError("attention_ratio must match rows")
    if report.blocker_ratio != _ratio(report.blocker_count, total):
        raise ValueError("blocker_ratio must match rows")
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
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    reason_codes = tuple(values)
    if require_nonempty and not reason_codes:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    for reason_code in reason_codes:
        if type(reason_code) is not str:
            raise ValueError("reason_codes must contain strings")
        if reason_code not in REPORT_REASON_SEQUENCE:
            raise ValueError("reason_code is not supported")
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
    return reason_codes


def _require_team_label(name: str, value: object) -> None:
    if type(value) is not str or not TEAM_LABEL_RE.fullmatch(value):
        raise ValueError(f"{name} must be a public specialist team label")


def _require_status(name: str, value: object) -> None:
    if value not in SPECIALIST_TEAM_MEMORY_SUPABASE_READINESS_STATUSES:
        raise ValueError(f"{name} must be a supported readiness status")


def _require_bool(name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{name} must be a bool")


def _require_count_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return decimal_value


def _require_ratio_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_count_decimal(name, value)
    if decimal_value > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return decimal_value


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    quantized = value.quantize(QUANTUM)
    if value != quantized:
        raise ValueError(f"{name} must be quantized to six decimal places")
    return quantized


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANTUM)


def _as_utc(name: str, value: datetime) -> datetime:
    if type(value) is not datetime or value.tzinfo is None:
        raise ValueError(f"{name} must be UTC-aware")
    if value.utcoffset() != UTC.utcoffset(value):
        raise ValueError(f"{name} must be UTC")
    return value.astimezone(UTC)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} must keep {field_name}=True")


def _json_ready(value: object) -> object:
    if type(value) is dict:
        return {str(key): _json_ready(item) for key, item in value.items()}
    if type(value) in (tuple, list):
        return [_json_ready(item) for item in value]
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value
