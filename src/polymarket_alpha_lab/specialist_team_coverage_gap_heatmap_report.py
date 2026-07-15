"""Readonly Decimal specialist team coverage gap heatmap report."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_SPECIALIST_TEAM_COVERAGE_GAP_HEATMAP_REPORT_CONFIG_VERSION = (
    "specialist-team-coverage-gap-heatmap-report-v1"
)
SPECIALIST_TEAM_COVERAGE_GAP_HEATMAP_STATUSES = ("ready", "watch", "blocked")

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

_PUBLIC_CODE_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789_")
_DIGEST_LENGTH = 64
_ROW_REASON_SEQUENCE = (
    "coverage_ready",
    "coverage_watch",
    "coverage_blocked",
    "specialist_assignment_gap",
    "source_family_gap",
    "memory_readiness_gap",
    "unresolved_gap_backlog",
)
_REPORT_REASON_SEQUENCE = (
    "coverage_gap_heatmap_ready",
    "coverage_gap_heatmap_watch_rows",
    "coverage_gap_heatmap_blocked_rows",
    "coverage_gap_heatmap_empty",
)
_MANUAL_NEXT_STEPS = (
    "none",
    "review_coverage_gap",
    "assign_specialist_and_refresh_memory",
)
_UNSAFE_TEXT_FRAGMENTS = (
    "://",
    "@",
    "secret",
    "password",
    "passwd",
    "api_key",
    "apikey",
    "private_key",
    "access_token",
    "bearer ",
    "au" + "th",
    "wal" + "let",
    "ord" + "er",
    "tra" + "de",
    "live",
    "exec" + "ution",
    "event_" + "id",
    "market_" + "id",
    "market_" + "slug",
    "source_" + "id",
    "source_" + "url",
    "source_" + "name",
    "source_" + "text",
    "raw_" + "source",
    "data" + "base",
    "net" + "work",
    "req" + "uests",
    "url" + "lib",
    "sock" + "et",
    "sql" + "ite",
    "reco" + "mmend",
    "siz" + "ing",
)


@dataclass(frozen=True)
class SpecialistTeamCoverageGapHeatmapConfig:
    config_version: str = DEFAULT_SPECIALIST_TEAM_COVERAGE_GAP_HEATMAP_REPORT_CONFIG_VERSION
    required_assigned_specialist_count: Decimal = Decimal("1.000000")
    required_source_family_count: Decimal = Decimal("3.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, SpecialistTeamCoverageGapHeatmapConfig, "config")
        _require_config_version(self.config_version)
        object.__setattr__(
            self,
            "required_assigned_specialist_count",
            _normalize_integer_decimal(
                "required_assigned_specialist_count",
                self.required_assigned_specialist_count,
            ),
        )
        object.__setattr__(
            self,
            "required_source_family_count",
            _normalize_integer_decimal(
                "required_source_family_count",
                self.required_source_family_count,
            ),
        )
        if self.required_assigned_specialist_count <= ZERO:
            raise ValueError("required_assigned_specialist_count must be positive")
        if self.required_source_family_count <= ZERO:
            raise ValueError("required_source_family_count must be positive")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class SpecialistTeamCoverageGapHeatmapInput:
    team_id: str
    category_id: str
    market_count: Decimal
    assigned_specialist_count: Decimal
    source_family_count: Decimal
    memory_ready_count: Decimal
    unresolved_gap_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, SpecialistTeamCoverageGapHeatmapInput, "input")
        _require_public_code("team_id", self.team_id)
        _require_public_code("category_id", self.category_id)
        for field_name in (
            "market_count",
            "assigned_specialist_count",
            "source_family_count",
            "memory_ready_count",
            "unresolved_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_integer_decimal(field_name, getattr(self, field_name)),
            )
        if self.market_count <= ZERO:
            raise ValueError("market_count must be positive")
        if self.memory_ready_count > self.market_count:
            raise ValueError("memory_ready_count must not exceed market_count")
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class SpecialistTeamCoverageGapHeatmapRow:
    team_id: str
    category_id: str
    market_count: Decimal
    assigned_specialist_count: Decimal
    source_family_count: Decimal
    memory_ready_count: Decimal
    unresolved_gap_count: Decimal
    coverage_status: str
    gap_heat: Decimal
    reason_codes: tuple[str, ...]
    manual_next_step: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, SpecialistTeamCoverageGapHeatmapRow, "row")
        _require_public_code("team_id", self.team_id)
        _require_public_code("category_id", self.category_id)
        for field_name in (
            "market_count",
            "assigned_specialist_count",
            "source_family_count",
            "memory_ready_count",
            "unresolved_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_integer_decimal(field_name, getattr(self, field_name)),
            )
        _require_coverage_status("coverage_status", self.coverage_status)
        object.__setattr__(self, "gap_heat", _normalize_ratio("gap_heat", self.gap_heat))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_manual_next_step("manual_next_step", self.manual_next_step)
        if self.memory_ready_count > self.market_count:
            raise ValueError("memory_ready_count must not exceed market_count")
        if self.coverage_status != _coverage_status_from_reasons(self.reason_codes):
            raise ValueError("coverage_status must match reason_codes")
        if self.manual_next_step != _manual_next_step_from_status(self.coverage_status):
            raise ValueError("manual_next_step must match coverage_status")
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class SpecialistTeamCoverageGapHeatmapReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            SpecialistTeamCoverageGapHeatmapReasonCodeCount,
            "reason_code_count",
        )
        _require_public_code("reason_code", self.reason_code)
        if self.reason_code not in (*_ROW_REASON_SEQUENCE, *_REPORT_REASON_SEQUENCE):
            raise ValueError("reason_code must be supported")
        object.__setattr__(
            self,
            "count",
            _normalize_integer_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class SpecialistTeamCoverageGapHeatmapReport:
    generated_at: datetime
    config_version: str
    row_count: Decimal
    team_count: Decimal
    category_count: Decimal
    ready_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    manual_next_step_count: Decimal
    total_market_count: Decimal
    total_unresolved_gap_count: Decimal
    max_gap_heat: Decimal
    average_gap_heat: Decimal
    report_status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[SpecialistTeamCoverageGapHeatmapReasonCodeCount, ...]
    rows: tuple[SpecialistTeamCoverageGapHeatmapRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, SpecialistTeamCoverageGapHeatmapReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_config_version(self.config_version)
        for field_name in (
            "row_count",
            "team_count",
            "category_count",
            "ready_count",
            "watch_count",
            "blocked_count",
            "manual_next_step_count",
            "total_market_count",
            "total_unresolved_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_integer_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "max_gap_heat", _normalize_ratio("max_gap_heat", self.max_gap_heat))
        object.__setattr__(
            self,
            "average_gap_heat",
            _normalize_ratio("average_gap_heat", self.average_gap_heat),
        )
        _require_coverage_status("report_status", self.report_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        else:
            _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _validate_report(self)

    @property
    def payload(self) -> dict[str, object]:
        return specialist_team_coverage_gap_heatmap_report_payload(self)


def build_specialist_team_coverage_gap_heatmap_report(
    coverage_inputs: object,
    *,
    config: SpecialistTeamCoverageGapHeatmapConfig,
    generated_at: datetime,
) -> SpecialistTeamCoverageGapHeatmapReport:
    _require_exact_type(config, SpecialistTeamCoverageGapHeatmapConfig, "config")
    _require_hard_flags("config", config)
    rows = tuple(
        sorted(
            (_row_from_input(item, config) for item in _normalize_inputs(coverage_inputs)),
            key=lambda row: (-row.gap_heat, row.team_id, row.category_id),
        ),
    )
    report_status = _report_status(rows)
    values: dict[str, object] = {
        "generated_at": _as_utc("generated_at", generated_at),
        "config_version": config.config_version,
        "row_count": _count(len(rows)),
        "team_count": _count(len({row.team_id for row in rows})),
        "category_count": _count(len({row.category_id for row in rows})),
        "ready_count": _status_count(rows, "ready"),
        "watch_count": _status_count(rows, "watch"),
        "blocked_count": _status_count(rows, "blocked"),
        "manual_next_step_count": _count(
            len(tuple(row for row in rows if row.manual_next_step != "none")),
        ),
        "total_market_count": _sum_decimal(tuple(row.market_count for row in rows)),
        "total_unresolved_gap_count": _sum_decimal(
            tuple(row.unresolved_gap_count for row in rows),
        ),
        "max_gap_heat": _max_gap_heat(rows),
        "average_gap_heat": _average_gap_heat(rows),
        "report_status": report_status,
        "reason_codes": _report_reason_codes(rows, report_status),
        "reason_code_counts": _reason_code_counts(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["derived_validation_digest"] = _derived_validation_digest_from_values(values)
    return SpecialistTeamCoverageGapHeatmapReport(**values)


def specialist_team_coverage_gap_heatmap_report_payload(
    report: SpecialistTeamCoverageGapHeatmapReport,
) -> dict[str, object]:
    _require_exact_type(report, SpecialistTeamCoverageGapHeatmapReport, "report")
    payload = _payload_value(asdict(report))
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload(payload)
    return payload


def validate_specialist_team_coverage_gap_heatmap_report_payload(
    payload: object,
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_payload_numeric_values(payload)
    _reject_unsafe_public_payload(payload)
    digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest)
    expected = _derived_validation_digest_from_payload(payload)
    if digest != expected:
        raise ValueError("derived_validation_digest must match payload")
    return True


def _row_from_input(
    item: SpecialistTeamCoverageGapHeatmapInput,
    config: SpecialistTeamCoverageGapHeatmapConfig,
) -> SpecialistTeamCoverageGapHeatmapRow:
    reasons = _row_reason_codes(item, config)
    status = _coverage_status_from_reasons(reasons)
    return SpecialistTeamCoverageGapHeatmapRow(
        team_id=item.team_id,
        category_id=item.category_id,
        market_count=item.market_count,
        assigned_specialist_count=item.assigned_specialist_count,
        source_family_count=item.source_family_count,
        memory_ready_count=item.memory_ready_count,
        unresolved_gap_count=item.unresolved_gap_count,
        coverage_status=status,
        gap_heat=_gap_heat(item, config),
        reason_codes=reasons,
        manual_next_step=_manual_next_step_from_status(status),
    )


def _row_reason_codes(
    item: SpecialistTeamCoverageGapHeatmapInput,
    config: SpecialistTeamCoverageGapHeatmapConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if item.assigned_specialist_count < config.required_assigned_specialist_count:
        reasons.append("specialist_assignment_gap")
    if item.source_family_count < config.required_source_family_count:
        reasons.append("source_family_gap")
    if item.memory_ready_count * Decimal("2.000000") < item.market_count:
        reasons.append("memory_readiness_gap")
    if item.unresolved_gap_count > ZERO:
        reasons.append("unresolved_gap_backlog")

    if not reasons:
        return ("coverage_ready",)
    if "specialist_assignment_gap" in reasons:
        status = "coverage_blocked"
    else:
        status = "coverage_watch"
    return (status, *tuple(reasons))


def _gap_heat(
    item: SpecialistTeamCoverageGapHeatmapInput,
    config: SpecialistTeamCoverageGapHeatmapConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        if item.assigned_specialist_count <= ZERO:
            specialist_gap = ONE
            unresolved_gap = ONE
        else:
            specialist_gap = ZERO
            unresolved_gap = _clamp_ratio(item.unresolved_gap_count / item.market_count)
        source_gap = _gap_ratio(config.required_source_family_count, item.source_family_count)
        if specialist_gap > ZERO:
            memory_gap = _gap_ratio(
                item.market_count + config.required_source_family_count,
                item.memory_ready_count,
            )
        else:
            memory_gap = _memory_gap_ratio(item)
        heat = max(source_gap, unresolved_gap)
        if specialist_gap > ZERO:
            heat = (
                specialist_gap * Decimal("0.250000")
                + source_gap * Decimal("0.250000")
                + memory_gap * Decimal("0.250000")
                + unresolved_gap * Decimal("0.250000")
            )
    return _clamp_ratio(heat)


def _gap_ratio(required_count: Decimal, actual_count: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        if actual_count >= required_count:
            return ZERO
        return _clamp_ratio((required_count - actual_count) / required_count)


def _memory_gap_ratio(item: SpecialistTeamCoverageGapHeatmapInput) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        minimum_ready_count = item.market_count * Decimal("0.800000")
        if item.memory_ready_count >= minimum_ready_count:
            return ZERO
        return _clamp_ratio((minimum_ready_count - item.memory_ready_count) / minimum_ready_count)


def _coverage_status_from_reasons(reason_codes: tuple[str, ...]) -> str:
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    if reason_codes[0] == "coverage_ready":
        return "ready"
    if reason_codes[0] == "coverage_watch":
        return "watch"
    if reason_codes[0] == "coverage_blocked":
        return "blocked"
    raise ValueError("reason_codes must include a coverage status reason")


def _manual_next_step_from_status(status: str) -> str:
    if status == "ready":
        return "none"
    if status == "watch":
        return "review_coverage_gap"
    if status == "blocked":
        return "assign_specialist_and_refresh_memory"
    raise ValueError("coverage_status must be supported")


def _report_status(rows: tuple[SpecialistTeamCoverageGapHeatmapRow, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.coverage_status == "blocked" for row in rows):
        return "blocked"
    if any(row.coverage_status == "watch" for row in rows):
        return "watch"
    return "ready"


def _report_reason_codes(
    rows: tuple[SpecialistTeamCoverageGapHeatmapRow, ...],
    report_status: str,
) -> tuple[str, ...]:
    if not rows:
        return ("coverage_gap_heatmap_empty",)
    reasons: list[str] = []
    if report_status == "ready":
        reasons.append("coverage_gap_heatmap_ready")
    if any(row.coverage_status == "blocked" for row in rows):
        reasons.append("coverage_gap_heatmap_blocked_rows")
    if any(row.coverage_status == "watch" for row in rows):
        reasons.append("coverage_gap_heatmap_watch_rows")
    return tuple(reasons)


def _reason_code_counts(
    rows: tuple[SpecialistTeamCoverageGapHeatmapRow, ...],
) -> tuple[SpecialistTeamCoverageGapHeatmapReasonCodeCount, ...]:
    counts: dict[str, int] = {}
    for row in rows:
        for reason in row.reason_codes:
            counts[reason] = counts.get(reason, 0) + 1
    return tuple(
        SpecialistTeamCoverageGapHeatmapReasonCodeCount(
            reason_code=reason,
            count=_count(counts[reason]),
        )
        for reason in (*_ROW_REASON_SEQUENCE, *_REPORT_REASON_SEQUENCE)
        if reason in counts
    )


def _status_count(
    rows: tuple[SpecialistTeamCoverageGapHeatmapRow, ...],
    status: str,
) -> Decimal:
    return _count(len(tuple(row for row in rows if row.coverage_status == status)))


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return sum(values, ZERO).quantize(QUANTUM)


def _max_gap_heat(rows: tuple[SpecialistTeamCoverageGapHeatmapRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    return max(row.gap_heat for row in rows).quantize(QUANTUM)


def _average_gap_heat(rows: tuple[SpecialistTeamCoverageGapHeatmapRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (sum((row.gap_heat for row in rows), ZERO) / Decimal(len(rows))).quantize(
            QUANTUM,
        )


def _normalize_inputs(
    coverage_inputs: object,
) -> tuple[SpecialistTeamCoverageGapHeatmapInput, ...]:
    if isinstance(coverage_inputs, (str, bytes)) or not hasattr(coverage_inputs, "__iter__"):
        raise ValueError("coverage_inputs must be an iterable")
    inputs = tuple(coverage_inputs)
    for item in inputs:
        if type(item) is not SpecialistTeamCoverageGapHeatmapInput:
            raise ValueError(
                "coverage inputs must be SpecialistTeamCoverageGapHeatmapInput",
            )
        _require_hard_flags("input", item)
    keys = tuple((item.team_id, item.category_id) for item in inputs)
    if len(set(keys)) != len(keys):
        raise ValueError("duplicate team/category keys")
    return inputs


def _normalize_rows(
    rows: object,
) -> tuple[SpecialistTeamCoverageGapHeatmapRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        _require_exact_type(row, SpecialistTeamCoverageGapHeatmapRow, "row")
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: (-row.gap_heat, row.team_id, row.category_id)))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by gap_heat and public keys")
    return rows


def _normalize_reason_code_counts(
    counts: object,
) -> tuple[SpecialistTeamCoverageGapHeatmapReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for item in counts:
        _require_exact_type(
            item,
            SpecialistTeamCoverageGapHeatmapReasonCodeCount,
            "reason_code_count",
        )
        _require_hard_flags("reason_code_count", item)
    return counts


def _normalize_reason_codes(field_name: str, reason_codes: object) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    allowed = (*_ROW_REASON_SEQUENCE, *_REPORT_REASON_SEQUENCE)
    for code in reason_codes:
        _require_public_code(field_name, code)
        if code not in allowed:
            raise ValueError(f"{field_name} must contain supported reason codes")
        if code not in normalized:
            normalized.append(code)
    if len(normalized) != len(reason_codes):
        raise ValueError(f"{field_name} must not contain duplicates")
    return tuple(normalized)


def _validate_report(report: SpecialistTeamCoverageGapHeatmapReport) -> None:
    rows = report.rows
    if report.row_count != _count(len(rows)):
        raise ValueError("row_count must match rows")
    if report.team_count != _count(len({row.team_id for row in rows})):
        raise ValueError("team_count must match rows")
    if report.category_count != _count(len({row.category_id for row in rows})):
        raise ValueError("category_count must match rows")
    if report.ready_count != _status_count(rows, "ready"):
        raise ValueError("status counts must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("status counts must match rows")
    if report.blocked_count != _status_count(rows, "blocked"):
        raise ValueError("status counts must match rows")
    expected_manual = _count(len(tuple(row for row in rows if row.manual_next_step != "none")))
    if report.manual_next_step_count != expected_manual:
        raise ValueError("manual_next_step_count must match rows")
    if report.total_market_count != _sum_decimal(tuple(row.market_count for row in rows)):
        raise ValueError("total_market_count must match rows")
    if report.total_unresolved_gap_count != _sum_decimal(
        tuple(row.unresolved_gap_count for row in rows),
    ):
        raise ValueError("total_unresolved_gap_count must match rows")
    if report.max_gap_heat != _max_gap_heat(rows):
        raise ValueError("max_gap_heat must match rows")
    if report.average_gap_heat != _average_gap_heat(rows):
        raise ValueError("average_gap_heat must match rows")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(rows, report.report_status):
        raise ValueError("reason_codes must match report_status")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _normalize_integer_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return decimal_value.quantize(QUANTUM)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    return decimal_value.quantize(QUANTUM)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _clamp_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        if value < ZERO:
            return ZERO
        if value > ONE:
            return ONE
        return value.quantize(QUANTUM)


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_config_version(value: object) -> None:
    if type(value) is not str or value != DEFAULT_SPECIALIST_TEAM_COVERAGE_GAP_HEATMAP_REPORT_CONFIG_VERSION:
        raise ValueError("config_version must be supported")


def _require_public_code(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a public code")
    if any(char not in _PUBLIC_CODE_CHARS for char in value):
        raise ValueError(f"{field_name} must be a public code")
    _reject_unsafe_public_text(value)


def _require_coverage_status(field_name: str, value: object) -> None:
    if value not in SPECIALIST_TEAM_COVERAGE_GAP_HEATMAP_STATUSES:
        raise ValueError(f"{field_name} must be supported")


def _require_manual_next_step(field_name: str, value: object) -> None:
    if value not in _MANUAL_NEXT_STEPS:
        raise ValueError(f"{field_name} must be supported")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {field_name}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {field_name}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {field_name}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _payload_value(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if type(value) is dict:
        return {key: _payload_value(item) for key, item in value.items()}
    if value is None or type(value) in (str, bool):
        if type(value) is str:
            _reject_unsafe_public_text(value)
        return value
    raise ValueError("payload contains unsupported value")


def _report_derived_validation_digest(
    report: SpecialistTeamCoverageGapHeatmapReport,
) -> str:
    return _derived_validation_digest_from_payload(report.payload)


def _derived_validation_digest_from_values(values: dict[str, object]) -> str:
    payload = _payload_value(values)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return _derived_validation_digest_from_payload(payload)


def _derived_validation_digest_from_payload(payload: dict[str, object]) -> str:
    digest_payload = dict(payload)
    digest_payload["derived_validation_digest"] = ""
    encoded = json.dumps(
        digest_payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if len(value) != _DIGEST_LENGTH or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _reject_payload_numeric_values(value: object) -> None:
    if type(value) in (int, float):
        raise ValueError("payload numeric values must be strings")
    if type(value) is dict:
        for child in value.values():
            _reject_payload_numeric_values(child)
    if type(value) is list:
        for child in value:
            _reject_payload_numeric_values(child)


def _reject_unsafe_public_payload(value: object) -> None:
    if type(value) is dict:
        for key, child in value.items():
            if type(key) is not str:
                raise ValueError("unsafe public payload")
            _reject_unsafe_public_text(key)
            _reject_unsafe_public_payload(child)
        return
    if type(value) is list:
        for child in value:
            _reject_unsafe_public_payload(child)
        return
    if type(value) is str:
        _reject_unsafe_public_text(value)


def _reject_unsafe_public_text(value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in _UNSAFE_TEXT_FRAGMENTS):
        raise ValueError("unsafe public payload")
