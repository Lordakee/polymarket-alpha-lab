"""Pure politics event team memory report."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


RESEARCH_POLITICS_EVENT_TEAM_MEMORY_REPORT_SLUG = (
    "research_politics_event_team_memory_report"
)
DEFAULT_RESEARCH_POLITICS_EVENT_TEAM_MEMORY_CONFIG_VERSION = (
    "research-politics-event-team-memory-v0"
)

STATUSES = ("pass", "watch", "block")
EMPTY_REASON = "politics_event_team_memory_empty"
PASS_REASON = "politics_event_team_memory_pass"
NO_PRECEDENT_BLOCK_REASON = "politics_event_team_memory_no_precedent_block"
CONTRADICTION_BLOCK_REASON = "politics_event_team_memory_contradiction_block"
UNRESOLVED_GAP_BLOCK_REASON = "politics_event_team_memory_unresolved_gap_block"
LOW_CONFIDENCE_BLOCK_REASON = "politics_event_team_memory_low_confidence_block"
LOW_CONFIDENCE_WATCH_REASON = "politics_event_team_memory_low_confidence_watch"
UNRESOLVED_GAP_WATCH_REASON = "politics_event_team_memory_unresolved_gap_watch"
ROW_REASON_CODES = (
    NO_PRECEDENT_BLOCK_REASON,
    CONTRADICTION_BLOCK_REASON,
    UNRESOLVED_GAP_BLOCK_REASON,
    LOW_CONFIDENCE_BLOCK_REASON,
    LOW_CONFIDENCE_WATCH_REASON,
    UNRESOLVED_GAP_WATCH_REASON,
    PASS_REASON,
)
REPORT_REASON_CODES = (EMPTY_REASON,) + ROW_REASON_CODES

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
STATUS_WEIGHT = {
    "block": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}


@dataclass(frozen=True)
class ResearchPoliticsEventTeamMemoryConfig:
    config_version: str = DEFAULT_RESEARCH_POLITICS_EVENT_TEAM_MEMORY_CONFIG_VERSION
    min_pass_memory_confidence_ratio: Decimal = Decimal("0.700000")
    min_watch_memory_confidence_ratio: Decimal = Decimal("0.500000")
    blocked_contradiction_count: Decimal = Decimal("2.000000")
    blocked_unresolved_gap_count: Decimal = Decimal("3.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "min_pass_memory_confidence_ratio",
            "min_watch_memory_confidence_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "blocked_contradiction_count",
            "blocked_unresolved_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        require_paper_only_flags("config", self)


@dataclass(frozen=True)
class ResearchPoliticsEventTeamMemoryInput:
    event_ref_sha256: str
    cluster_ref_sha256: str
    evidence_ref_sha256: str
    prior_event_count: Decimal
    resolved_precedent_count: Decimal
    unresolved_gap_count: Decimal
    contradiction_count: Decimal
    memory_confidence_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "event_ref_sha256",
            "cluster_ref_sha256",
            "evidence_ref_sha256",
        ):
            _require_sha256_digest(field_name, getattr(self, field_name))
        _normalize_memory_metrics(self)
        _validate_memory_shape(self)
        require_paper_only_flags("input", self)


@dataclass(frozen=True)
class ResearchPoliticsEventTeamMemoryRow:
    event_ref_sha256: str
    cluster_ref_sha256: str
    evidence_ref_sha256: str
    prior_event_count: Decimal
    resolved_precedent_count: Decimal
    unresolved_gap_count: Decimal
    contradiction_count: Decimal
    memory_confidence_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "event_ref_sha256",
            "cluster_ref_sha256",
            "evidence_ref_sha256",
        ):
            _require_sha256_digest(field_name, getattr(self, field_name))
        _normalize_memory_metrics(self)
        _validate_memory_shape(self)
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        require_paper_only_flags("row", self)


@dataclass(frozen=True)
class ResearchPoliticsEventTeamMemoryReport:
    generated_at: datetime
    config_version: str
    status: str
    event_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_memory_confidence_ratio: Decimal
    highest_unresolved_gap_count: Decimal
    rows: tuple[ResearchPoliticsEventTeamMemoryRow, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "event_count",
            "pass_count",
            "watch_count",
            "block_count",
            "highest_unresolved_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_memory_confidence_ratio",
            _require_ratio(
                "average_memory_confidence_ratio",
                self.average_memory_confidence_ratio,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        _validate_report(self)
        reject_unsafe_surface_fields("politics event team memory report", self)
        require_paper_only_flags("report", self)


def build_research_politics_event_team_memory_report(
    inputs: list[ResearchPoliticsEventTeamMemoryInput]
    | tuple[ResearchPoliticsEventTeamMemoryInput, ...],
    *,
    config: ResearchPoliticsEventTeamMemoryConfig,
    generated_at: datetime,
) -> ResearchPoliticsEventTeamMemoryReport:
    if type(config) is not ResearchPoliticsEventTeamMemoryConfig:
        raise ValueError("config must be a ResearchPoliticsEventTeamMemoryConfig")
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _build_rows(_normalize_inputs(inputs), config=config)
    return ResearchPoliticsEventTeamMemoryReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_report_status(rows),
        event_count=_count(len(rows)),
        pass_count=_row_status_count(rows, "pass"),
        watch_count=_row_status_count(rows, "watch"),
        block_count=_row_status_count(rows, "block"),
        average_memory_confidence_ratio=_average_memory_confidence_ratio(rows),
        highest_unresolved_gap_count=max(
            (row.unresolved_gap_count for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        rows=rows,
        reason_codes=_report_reason_codes(rows),
    )


def research_politics_event_team_memory_report_payload(
    report: ResearchPoliticsEventTeamMemoryReport,
) -> dict[str, Any]:
    if type(report) is not ResearchPoliticsEventTeamMemoryReport:
        raise ValueError("report must be a ResearchPoliticsEventTeamMemoryReport")
    _require_nested_flags(report)
    reject_unsafe_surface_fields("politics event team memory report", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be an object")
    return payload


def research_politics_event_team_memory_report_digest(
    report: ResearchPoliticsEventTeamMemoryReport,
) -> str:
    payload = research_politics_event_team_memory_report_payload(report)
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _build_rows(
    inputs: tuple[ResearchPoliticsEventTeamMemoryInput, ...],
    *,
    config: ResearchPoliticsEventTeamMemoryConfig,
) -> tuple[ResearchPoliticsEventTeamMemoryRow, ...]:
    rows = tuple(_build_row(input_row, config=config) for input_row in inputs)
    return tuple(sorted(rows, key=_row_sort_key))


def _build_row(
    input_row: ResearchPoliticsEventTeamMemoryInput,
    *,
    config: ResearchPoliticsEventTeamMemoryConfig,
) -> ResearchPoliticsEventTeamMemoryRow:
    reason_codes = _row_reason_codes(input_row, config=config)
    return ResearchPoliticsEventTeamMemoryRow(
        event_ref_sha256=input_row.event_ref_sha256,
        cluster_ref_sha256=input_row.cluster_ref_sha256,
        evidence_ref_sha256=input_row.evidence_ref_sha256,
        prior_event_count=input_row.prior_event_count,
        resolved_precedent_count=input_row.resolved_precedent_count,
        unresolved_gap_count=input_row.unresolved_gap_count,
        contradiction_count=input_row.contradiction_count,
        memory_confidence_ratio=input_row.memory_confidence_ratio,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    input_row: ResearchPoliticsEventTeamMemoryInput,
    *,
    config: ResearchPoliticsEventTeamMemoryConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if input_row.prior_event_count == ZERO or input_row.resolved_precedent_count == ZERO:
        reasons.append(NO_PRECEDENT_BLOCK_REASON)
    if input_row.contradiction_count >= config.blocked_contradiction_count:
        reasons.append(CONTRADICTION_BLOCK_REASON)
    if input_row.unresolved_gap_count >= config.blocked_unresolved_gap_count:
        reasons.append(UNRESOLVED_GAP_BLOCK_REASON)
    if input_row.memory_confidence_ratio < config.min_watch_memory_confidence_ratio:
        reasons.append(LOW_CONFIDENCE_BLOCK_REASON)
    elif input_row.memory_confidence_ratio < config.min_pass_memory_confidence_ratio:
        reasons.append(LOW_CONFIDENCE_WATCH_REASON)
    if (
        input_row.unresolved_gap_count > ZERO
        and UNRESOLVED_GAP_BLOCK_REASON not in reasons
    ):
        reasons.append(UNRESOLVED_GAP_WATCH_REASON)
    if not reasons:
        reasons.append(PASS_REASON)
    return tuple(reason for reason in ROW_REASON_CODES if reason in reasons)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if reason_codes == (PASS_REASON,):
        return "pass"
    return "watch"


def _report_status(rows: tuple[ResearchPoliticsEventTeamMemoryRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchPoliticsEventTeamMemoryRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    reasons = tuple(
        reason_code
        for reason_code in ROW_REASON_CODES
        if any(reason_code in row.reason_codes for row in rows)
    )
    if reasons:
        return reasons
    return (PASS_REASON,)


def _row_sort_key(
    row: ResearchPoliticsEventTeamMemoryRow,
) -> tuple[Decimal, Decimal, Decimal, Decimal, str, str, str]:
    return (
        -STATUS_WEIGHT[row.status],
        -row.contradiction_count,
        -row.unresolved_gap_count,
        row.memory_confidence_ratio,
        row.event_ref_sha256,
        row.cluster_ref_sha256,
        row.evidence_ref_sha256,
    )


def _normalize_inputs(
    value: object,
) -> tuple[ResearchPoliticsEventTeamMemoryInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(value)
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        if type(row) is not ResearchPoliticsEventTeamMemoryInput:
            raise ValueError("inputs must contain ResearchPoliticsEventTeamMemoryInput")
        require_paper_only_flags("input", row)
        key = (row.event_ref_sha256, row.cluster_ref_sha256, row.evidence_ref_sha256)
        if key in seen:
            raise ValueError("inputs must be unique by public refs")
        seen.add(key)
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                row.event_ref_sha256,
                row.cluster_ref_sha256,
                row.evidence_ref_sha256,
            ),
        ),
    )


def _normalize_rows(
    value: object,
) -> tuple[ResearchPoliticsEventTeamMemoryRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        if type(row) is not ResearchPoliticsEventTeamMemoryRow:
            raise ValueError("rows must contain ResearchPoliticsEventTeamMemoryRow")
        require_paper_only_flags("row", row)
        key = (row.event_ref_sha256, row.cluster_ref_sha256, row.evidence_ref_sha256)
        if key in seen:
            raise ValueError("rows must be unique by public refs")
        seen.add(key)
    return tuple(sorted(rows, key=_row_sort_key))


def _normalize_memory_metrics(value: object) -> None:
    for field_name in (
        "prior_event_count",
        "resolved_precedent_count",
        "unresolved_gap_count",
        "contradiction_count",
    ):
        object.__setattr__(
            value,
            field_name,
            _require_nonnegative_decimal(field_name, getattr(value, field_name)),
        )
    object.__setattr__(
        value,
        "memory_confidence_ratio",
        _require_ratio("memory_confidence_ratio", value.memory_confidence_ratio),
    )


def _validate_config(config: ResearchPoliticsEventTeamMemoryConfig) -> None:
    if config.min_pass_memory_confidence_ratio <= config.min_watch_memory_confidence_ratio:
        raise ValueError(
            "min_pass_memory_confidence_ratio must exceed "
            "min_watch_memory_confidence_ratio",
        )
    if config.blocked_contradiction_count <= ZERO:
        raise ValueError("blocked_contradiction_count must be positive")
    if config.blocked_unresolved_gap_count <= ZERO:
        raise ValueError("blocked_unresolved_gap_count must be positive")


def _validate_memory_shape(value: object) -> None:
    if value.resolved_precedent_count > value.prior_event_count:
        raise ValueError("resolved_precedent_count must not exceed prior_event_count")


def _validate_row(row: ResearchPoliticsEventTeamMemoryRow) -> None:
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.reason_codes == (PASS_REASON,):
        if row.unresolved_gap_count != ZERO:
            raise ValueError("pass rows cannot contain unresolved gaps")
        if row.contradiction_count != ZERO:
            raise ValueError("pass rows cannot contain contradictions")


def _validate_report(report: ResearchPoliticsEventTeamMemoryReport) -> None:
    if report.event_count != _count(len(report.rows)):
        raise ValueError("event_count must match rows")
    if report.pass_count != _row_status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _row_status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _row_status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.average_memory_confidence_ratio != _average_memory_confidence_ratio(
        report.rows,
    ):
        raise ValueError("average_memory_confidence_ratio must match rows")
    if report.highest_unresolved_gap_count != max(
        (row.unresolved_gap_count for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("highest_unresolved_gap_count must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sort")


def _row_status_count(
    rows: tuple[ResearchPoliticsEventTeamMemoryRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _average_memory_confidence_ratio(
    rows: tuple[ResearchPoliticsEventTeamMemoryRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (
            sum((row.memory_confidence_ratio for row in rows), ZERO) / _count(len(rows))
        ).quantize(QUANT)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANT)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        decimal_value = value.quantize(QUANT)
    if decimal_value != value:
        raise ValueError(f"{field_name} must use six decimal places")
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value == ZERO:
        return ZERO
    return decimal_value


def _require_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be at most one")
    return decimal_value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


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
        if type(reason_code) is not str or reason_code not in allowed:
            raise ValueError(f"{field_name} must contain known reason codes")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    if tuple(reason_code for reason_code in allowed if reason_code in reason_codes) != reason_codes:
        raise ValueError(f"{field_name} must be deterministic")
    return reason_codes


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be stripped")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_nested_flags(report: ResearchPoliticsEventTeamMemoryReport) -> None:
    require_paper_only_flags("report", report)
    for row in report.rows:
        require_paper_only_flags("row", row)


__all__ = (
    "DEFAULT_RESEARCH_POLITICS_EVENT_TEAM_MEMORY_CONFIG_VERSION",
    "RESEARCH_POLITICS_EVENT_TEAM_MEMORY_REPORT_SLUG",
    "ResearchPoliticsEventTeamMemoryConfig",
    "ResearchPoliticsEventTeamMemoryInput",
    "ResearchPoliticsEventTeamMemoryReport",
    "ResearchPoliticsEventTeamMemoryRow",
    "build_research_politics_event_team_memory_report",
    "research_politics_event_team_memory_report_digest",
    "research_politics_event_team_memory_report_payload",
)
