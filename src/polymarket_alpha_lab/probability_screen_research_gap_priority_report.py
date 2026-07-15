"""Readonly priority report for probability screen research gaps."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import InitVar, asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, localcontext
import hashlib
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_PROBABILITY_SCREEN_RESEARCH_GAP_PRIORITY_CONFIG_VERSION = (
    "probability-screen-research-gap-priority-v0"
)

DECIMAL_CONTEXT = Context(prec=64)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)
STATUS_RANK = {
    STATUS_BLOCK: 0,
    STATUS_WATCH: 1,
    STATUS_PASS: 2,
}

PASS_REASON = "research_gap_priority_pass"
WATCH_REASON = "research_gap_priority_watch"
BLOCK_REASON = "research_gap_priority_block"
SOURCE_GAP_PRESENT_REASON = "source_gap_present"
SOURCE_GAP_BLOCK_REASON = "source_gap_block"
CONTRADICTION_PRESENT_REASON = "contradiction_present"
CONTRADICTION_BLOCK_REASON = "contradiction_block"
RESOLUTION_RULE_MISSING_REASON = "resolution_rule_missing"
OFFICIAL_ANCHOR_WATCH_REASON = "official_anchor_watch"
OFFICIAL_ANCHOR_STALE_REASON = "official_anchor_stale"
MANUAL_URGENCY_HIGH_REASON = "manual_urgency_high"

STATUS_REASON_CODES = (PASS_REASON, WATCH_REASON, BLOCK_REASON)
ROW_REASON_CODES = (
    PASS_REASON,
    WATCH_REASON,
    BLOCK_REASON,
    SOURCE_GAP_PRESENT_REASON,
    SOURCE_GAP_BLOCK_REASON,
    CONTRADICTION_PRESENT_REASON,
    CONTRADICTION_BLOCK_REASON,
    RESOLUTION_RULE_MISSING_REASON,
    OFFICIAL_ANCHOR_WATCH_REASON,
    OFFICIAL_ANCHOR_STALE_REASON,
    MANUAL_URGENCY_HIGH_REASON,
)
REASON_CODE_SET = frozenset(ROW_REASON_CODES)

__all__ = (
    "DEFAULT_PROBABILITY_SCREEN_RESEARCH_GAP_PRIORITY_CONFIG_VERSION",
    "ProbabilityScreenResearchGapPriorityConfig",
    "ProbabilityScreenResearchGapPriorityInput",
    "ProbabilityScreenResearchGapPriorityRow",
    "ProbabilityScreenResearchGapPriorityReasonCodeCount",
    "ProbabilityScreenResearchGapPriorityReport",
    "build_probability_screen_research_gap_priority_report",
    "probability_screen_research_gap_priority_report_payload",
)


@dataclass(frozen=True)
class ProbabilityScreenResearchGapPriorityConfig:
    medium_priority_threshold: Decimal = Decimal("3.000000")
    high_priority_threshold: Decimal = Decimal("6.000000")
    source_gap_weight: Decimal = Decimal("1.000000")
    contradiction_weight: Decimal = Decimal("0.612500")
    resolution_rule_gap_weight: Decimal = Decimal("4.400000")
    official_anchor_staleness_weight: Decimal = Decimal("0.875000")
    manual_urgency_weight: Decimal = Decimal("1.000000")
    source_gap_block_count: Decimal = Decimal("2.000000")
    contradiction_block_count: Decimal = Decimal("2.000000")
    official_anchor_watch_staleness: Decimal = Decimal("0.500000")
    official_anchor_stale_staleness: Decimal = Decimal("1.000000")
    manual_urgency_high_threshold: Decimal = Decimal("0.750000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ProbabilityScreenResearchGapPriorityConfig, "config")
        for field_name in (
            "medium_priority_threshold",
            "high_priority_threshold",
            "source_gap_weight",
            "contradiction_weight",
            "resolution_rule_gap_weight",
            "official_anchor_staleness_weight",
            "manual_urgency_weight",
            "source_gap_block_count",
            "contradiction_block_count",
            "official_anchor_watch_staleness",
            "official_anchor_stale_staleness",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "manual_urgency_high_threshold",
            _unit_decimal(
                "manual_urgency_high_threshold",
                self.manual_urgency_high_threshold,
            ),
        )
        if self.high_priority_threshold <= self.medium_priority_threshold:
            raise ValueError("high_priority_threshold must exceed medium_priority_threshold")
        if self.official_anchor_stale_staleness < self.official_anchor_watch_staleness:
            raise ValueError(
                "official_anchor_stale_staleness must be at least watch staleness",
            )
        require_paper_only_flags("config", self)
        _reject_private_reference_fields("config", self)
        reject_unsafe_surface_fields("config", self)


@dataclass(frozen=True)
class ProbabilityScreenResearchGapPriorityInput:
    case_digest: str
    source_gap_count: Decimal
    contradiction_count: Decimal
    resolution_rule_gap: Decimal
    official_anchor_staleness: Decimal
    manual_urgency: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ProbabilityScreenResearchGapPriorityInput,
            "gap input",
        )
        _require_digest("case_digest", self.case_digest)
        for field_name in ("source_gap_count", "contradiction_count"):
            object.__setattr__(
                self,
                field_name,
                _count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("resolution_rule_gap", "official_anchor_staleness"):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "manual_urgency",
            _unit_decimal("manual_urgency", self.manual_urgency),
        )
        require_paper_only_flags("gap input", self)
        _reject_private_reference_fields("gap input", self)
        reject_unsafe_surface_fields("gap input", self)


@dataclass(frozen=True)
class ProbabilityScreenResearchGapPriorityRow:
    case_digest: str
    source_gap_count: Decimal
    contradiction_count: Decimal
    resolution_rule_gap: Decimal
    official_anchor_staleness: Decimal
    manual_urgency: Decimal
    gap_priority: Decimal
    priority_status: str
    manual_next_step: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    validation_config: InitVar[ProbabilityScreenResearchGapPriorityConfig | None] = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(
        self,
        validation_config: ProbabilityScreenResearchGapPriorityConfig | None,
    ) -> None:
        _require_exact_type(self, ProbabilityScreenResearchGapPriorityRow, "row")
        _require_digest("case_digest", self.case_digest)
        for field_name in ("source_gap_count", "contradiction_count"):
            object.__setattr__(
                self,
                field_name,
                _count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "resolution_rule_gap",
            "official_anchor_staleness",
            "gap_priority",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "manual_urgency",
            _unit_decimal("manual_urgency", self.manual_urgency),
        )
        _require_choice("priority_status", self.priority_status, STATUSES)
        _require_public_string("manual_next_step", self.manual_next_step)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_consistency(self, _normalize_validation_config(validation_config))
        require_paper_only_flags("row", self)
        _reject_private_reference_fields("row", self)
        reject_unsafe_surface_fields("row", self)
        _set_or_validate_digest(self, "row")


@dataclass(frozen=True)
class ProbabilityScreenResearchGapPriorityReasonCodeCount:
    reason_code: str
    row_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ProbabilityScreenResearchGapPriorityReasonCodeCount,
            "reason code count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "row_count",
            _count_decimal("row_count", self.row_count),
        )
        require_paper_only_flags("reason code count", self)
        _reject_private_reference_fields("reason code count", self)
        reject_unsafe_surface_fields("reason code count", self)


@dataclass(frozen=True)
class ProbabilityScreenResearchGapPriorityReport:
    generated_at: datetime
    config_version: str
    report_status: str
    case_count: Decimal
    high_priority_count: Decimal
    medium_priority_count: Decimal
    low_priority_count: Decimal
    mean_gap_priority: Decimal
    max_gap_priority: Decimal
    rows: tuple[ProbabilityScreenResearchGapPriorityRow, ...]
    reason_code_counts: tuple[ProbabilityScreenResearchGapPriorityReasonCodeCount, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ProbabilityScreenResearchGapPriorityReport, "report")
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_PROBABILITY_SCREEN_RESEARCH_GAP_PRIORITY_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_choice("report_status", self.report_status, STATUSES)
        for field_name in (
            "case_count",
            "high_priority_count",
            "medium_priority_count",
            "low_priority_count",
            "mean_gap_priority",
            "max_gap_priority",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_report_consistency(self)
        require_paper_only_flags("report", self)
        _reject_private_reference_fields("report", self)
        reject_unsafe_surface_fields("report", self)
        _set_or_validate_digest(self, "report")


def build_probability_screen_research_gap_priority_report(
    gaps: Iterable[ProbabilityScreenResearchGapPriorityInput],
    *,
    generated_at: datetime,
    config: ProbabilityScreenResearchGapPriorityConfig | None = None,
) -> ProbabilityScreenResearchGapPriorityReport:
    generated_at_utc = _as_utc("generated_at", generated_at)
    active_config = (
        ProbabilityScreenResearchGapPriorityConfig() if config is None else config
    )
    if type(active_config) is not ProbabilityScreenResearchGapPriorityConfig:
        raise ValueError("config must be ProbabilityScreenResearchGapPriorityConfig")
    require_paper_only_flags("config", active_config)
    normalized_gaps = _normalize_inputs(gaps)
    rows = tuple(
        sorted(
            (
                _row_from_input(gap_input, config=active_config)
                for gap_input in normalized_gaps
            ),
            key=_row_sort_key,
        ),
    )
    return ProbabilityScreenResearchGapPriorityReport(
        generated_at=generated_at_utc,
        config_version=DEFAULT_PROBABILITY_SCREEN_RESEARCH_GAP_PRIORITY_CONFIG_VERSION,
        report_status=_report_status(rows),
        case_count=_decimal_from_int(len(rows)),
        high_priority_count=_status_count(rows, STATUS_BLOCK),
        medium_priority_count=_status_count(rows, STATUS_WATCH),
        low_priority_count=_status_count(rows, STATUS_PASS),
        mean_gap_priority=_mean_decimal(row.gap_priority for row in rows),
        max_gap_priority=max((row.gap_priority for row in rows), default=ZERO),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows),
    )


def probability_screen_research_gap_priority_report_payload(
    report: ProbabilityScreenResearchGapPriorityReport,
) -> "FrozenJsonObject":
    if type(report) is not ProbabilityScreenResearchGapPriorityReport:
        raise ValueError(
            "report must be exactly ProbabilityScreenResearchGapPriorityReport",
        )
    require_paper_only_flags("report", report)
    _reject_private_reference_fields("report", report)
    reject_unsafe_surface_fields("report", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _reject_private_reference_fields("payload", payload)
    reject_unsafe_surface_fields("payload", payload)
    _require_payload_digest(payload)
    return _freeze_json_object(payload)


class FrozenJsonObject(dict[str, Any]):
    def __init__(self, value: dict[str, Any]) -> None:
        super().__init__(value)

    def __setitem__(self, key: str, value: Any) -> None:
        raise TypeError("payload is immutable")

    def __delitem__(self, key: str) -> None:
        raise TypeError("payload is immutable")

    def clear(self) -> None:
        raise TypeError("payload is immutable")

    def pop(self, key: str, default: Any = None) -> Any:
        raise TypeError("payload is immutable")

    def popitem(self) -> tuple[str, Any]:
        raise TypeError("payload is immutable")

    def setdefault(self, key: str, default: Any = None) -> Any:
        raise TypeError("payload is immutable")

    def update(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError("payload is immutable")

    def __ior__(self, other: object) -> "FrozenJsonObject":
        raise TypeError("payload is immutable")


class FrozenJsonArray(tuple[Any, ...]):
    def __eq__(self, other: object) -> bool:
        if isinstance(other, (list, tuple)):
            return tuple(self) == tuple(other)
        return False

    def append(self, value: Any) -> None:
        raise TypeError("payload is immutable")

    def extend(self, values: Any) -> None:
        raise TypeError("payload is immutable")


def _row_from_input(
    gap_input: ProbabilityScreenResearchGapPriorityInput,
    *,
    config: ProbabilityScreenResearchGapPriorityConfig,
) -> ProbabilityScreenResearchGapPriorityRow:
    gap_priority = _gap_priority(
        source_gap_count=gap_input.source_gap_count,
        contradiction_count=gap_input.contradiction_count,
        resolution_rule_gap=gap_input.resolution_rule_gap,
        official_anchor_staleness=gap_input.official_anchor_staleness,
        manual_urgency=gap_input.manual_urgency,
        config=config,
    )
    priority_status = _priority_status(gap_priority, config)
    return ProbabilityScreenResearchGapPriorityRow(
        case_digest=gap_input.case_digest,
        source_gap_count=gap_input.source_gap_count,
        contradiction_count=gap_input.contradiction_count,
        resolution_rule_gap=gap_input.resolution_rule_gap,
        official_anchor_staleness=gap_input.official_anchor_staleness,
        manual_urgency=gap_input.manual_urgency,
        gap_priority=gap_priority,
        priority_status=priority_status,
        manual_next_step=_manual_next_step(
            source_gap_count=gap_input.source_gap_count,
            contradiction_count=gap_input.contradiction_count,
            resolution_rule_gap=gap_input.resolution_rule_gap,
            official_anchor_staleness=gap_input.official_anchor_staleness,
            manual_urgency=gap_input.manual_urgency,
            config=config,
        ),
        reason_codes=_reason_codes_for_values(
            priority_status=priority_status,
            source_gap_count=gap_input.source_gap_count,
            contradiction_count=gap_input.contradiction_count,
            resolution_rule_gap=gap_input.resolution_rule_gap,
            official_anchor_staleness=gap_input.official_anchor_staleness,
            manual_urgency=gap_input.manual_urgency,
            config=config,
        ),
        validation_config=config,
    )


def _gap_priority(
    *,
    source_gap_count: Decimal,
    contradiction_count: Decimal,
    resolution_rule_gap: Decimal,
    official_anchor_staleness: Decimal,
    manual_urgency: Decimal,
    config: ProbabilityScreenResearchGapPriorityConfig,
) -> Decimal:
    return _quantize(
        (source_gap_count * config.source_gap_weight)
        + (contradiction_count * config.contradiction_weight)
        + (resolution_rule_gap * config.resolution_rule_gap_weight)
        + (official_anchor_staleness * config.official_anchor_staleness_weight)
        + (manual_urgency * config.manual_urgency_weight),
    )


def _priority_status(
    gap_priority: Decimal,
    config: ProbabilityScreenResearchGapPriorityConfig,
) -> str:
    if gap_priority >= config.high_priority_threshold:
        return STATUS_BLOCK
    if gap_priority >= config.medium_priority_threshold:
        return STATUS_WATCH
    return STATUS_PASS


def _reason_codes_for_values(
    *,
    priority_status: str,
    source_gap_count: Decimal,
    contradiction_count: Decimal,
    resolution_rule_gap: Decimal,
    official_anchor_staleness: Decimal,
    manual_urgency: Decimal,
    config: ProbabilityScreenResearchGapPriorityConfig,
) -> tuple[str, ...]:
    reason_codes = [_status_reason(priority_status)]
    if (
        contradiction_count >= config.contradiction_block_count
        and contradiction_count > ZERO
    ):
        reason_codes.append(CONTRADICTION_BLOCK_REASON)
    else:
        if source_gap_count >= config.source_gap_block_count and source_gap_count > ZERO:
            reason_codes.append(SOURCE_GAP_BLOCK_REASON)
        elif source_gap_count > ZERO:
            reason_codes.append(SOURCE_GAP_PRESENT_REASON)
        if contradiction_count > ZERO:
            reason_codes.append(CONTRADICTION_PRESENT_REASON)
    if resolution_rule_gap > ZERO:
        reason_codes.append(RESOLUTION_RULE_MISSING_REASON)
    if official_anchor_staleness >= config.official_anchor_stale_staleness:
        reason_codes.append(OFFICIAL_ANCHOR_STALE_REASON)
    elif official_anchor_staleness >= config.official_anchor_watch_staleness:
        reason_codes.append(OFFICIAL_ANCHOR_WATCH_REASON)
    if manual_urgency >= config.manual_urgency_high_threshold:
        reason_codes.append(MANUAL_URGENCY_HIGH_REASON)
    return tuple(reason_codes)


def _manual_next_step(
    *,
    source_gap_count: Decimal,
    contradiction_count: Decimal,
    resolution_rule_gap: Decimal,
    official_anchor_staleness: Decimal,
    manual_urgency: Decimal,
    config: ProbabilityScreenResearchGapPriorityConfig,
) -> str:
    if contradiction_count >= config.contradiction_block_count:
        return "resolve_contradictions_with_official_anchor"
    if official_anchor_staleness >= config.official_anchor_stale_staleness:
        return "refresh_official_anchor"
    if resolution_rule_gap > ZERO:
        return "define_resolution_rule"
    if source_gap_count >= config.source_gap_block_count:
        return "collect_missing_sources"
    if manual_urgency >= config.manual_urgency_high_threshold:
        return "manual_review_requested"
    return "ready_for_probability_screen"


def _status_reason(status: str) -> str:
    if status == STATUS_BLOCK:
        return BLOCK_REASON
    if status == STATUS_WATCH:
        return WATCH_REASON
    return PASS_REASON


def _report_status(rows: tuple[ProbabilityScreenResearchGapPriorityRow, ...]) -> str:
    if any(row.priority_status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.priority_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _normalize_inputs(
    gaps: Iterable[ProbabilityScreenResearchGapPriorityInput],
) -> tuple[ProbabilityScreenResearchGapPriorityInput, ...]:
    if isinstance(gaps, (str, bytes, dict)):
        raise ValueError("gaps must be an iterable of gap inputs")
    normalized = tuple(gaps)
    seen_case_digests: set[str] = set()
    for gap_input in normalized:
        if type(gap_input) is not ProbabilityScreenResearchGapPriorityInput:
            raise ValueError(
                "gaps must contain ProbabilityScreenResearchGapPriorityInput",
            )
        require_paper_only_flags("gap input", gap_input)
        if gap_input.case_digest in seen_case_digests:
            raise ValueError("case_digest values must be unique")
        seen_case_digests.add(gap_input.case_digest)
    return normalized


def _normalize_rows(
    rows: object,
) -> tuple[ProbabilityScreenResearchGapPriorityRow, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("rows must be a tuple or list")
    normalized = tuple(rows)
    seen_case_digests: set[str] = set()
    for row in normalized:
        if type(row) is not ProbabilityScreenResearchGapPriorityRow:
            raise ValueError("rows must contain ProbabilityScreenResearchGapPriorityRow")
        require_paper_only_flags("row", row)
        if row.case_digest in seen_case_digests:
            raise ValueError("rows case_digest values must be unique")
        seen_case_digests.add(row.case_digest)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sorting")
    return normalized


def _normalize_reason_code_counts(
    rows: object,
) -> tuple[ProbabilityScreenResearchGapPriorityReasonCodeCount, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("reason_code_counts must be a tuple or list")
    normalized = tuple(rows)
    seen_reason_codes: set[str] = set()
    for row in normalized:
        if type(row) is not ProbabilityScreenResearchGapPriorityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ProbabilityScreenResearchGapPriorityReasonCodeCount",
            )
        require_paper_only_flags("reason code count", row)
        if row.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen_reason_codes.add(row.reason_code)
    if normalized != tuple(sorted(normalized, key=lambda row: row.reason_code)):
        raise ValueError("reason_code_counts must use deterministic sorting")
    return normalized


def _row_sort_key(
    row: ProbabilityScreenResearchGapPriorityRow,
) -> tuple[int, Decimal, str]:
    return (
        STATUS_RANK[row.priority_status],
        -row.gap_priority,
        row.case_digest,
    )


def _reason_code_counts(
    rows: tuple[ProbabilityScreenResearchGapPriorityRow, ...],
) -> tuple[ProbabilityScreenResearchGapPriorityReasonCodeCount, ...]:
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        ProbabilityScreenResearchGapPriorityReasonCodeCount(
            reason_code=reason_code,
            row_count=count,
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _status_count(
    rows: tuple[ProbabilityScreenResearchGapPriorityRow, ...],
    status: str,
) -> Decimal:
    return _decimal_from_int(sum(1 for row in rows if row.priority_status == status))


def _mean_decimal(values: Iterable[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return ZERO
    return _quantize(sum(normalized, ZERO) / Decimal(len(normalized)))


def _normalize_validation_config(
    config: ProbabilityScreenResearchGapPriorityConfig | None,
) -> ProbabilityScreenResearchGapPriorityConfig:
    if config is None:
        return ProbabilityScreenResearchGapPriorityConfig()
    if type(config) is not ProbabilityScreenResearchGapPriorityConfig:
        raise ValueError(
            "validation_config must be ProbabilityScreenResearchGapPriorityConfig",
        )
    require_paper_only_flags("validation_config", config)
    return config


def _validate_row_consistency(
    row: ProbabilityScreenResearchGapPriorityRow,
    config: ProbabilityScreenResearchGapPriorityConfig,
) -> None:
    expected_gap_priority = _gap_priority(
        source_gap_count=row.source_gap_count,
        contradiction_count=row.contradiction_count,
        resolution_rule_gap=row.resolution_rule_gap,
        official_anchor_staleness=row.official_anchor_staleness,
        manual_urgency=row.manual_urgency,
        config=config,
    )
    if row.gap_priority != expected_gap_priority:
        raise ValueError("gap_priority must match research gap fields")
    expected_status = _priority_status(row.gap_priority, config)
    if row.priority_status != expected_status:
        raise ValueError("priority_status must match gap_priority")
    expected_next_step = _manual_next_step(
        source_gap_count=row.source_gap_count,
        contradiction_count=row.contradiction_count,
        resolution_rule_gap=row.resolution_rule_gap,
        official_anchor_staleness=row.official_anchor_staleness,
        manual_urgency=row.manual_urgency,
        config=config,
    )
    if row.manual_next_step != expected_next_step:
        raise ValueError("manual_next_step must match research gap fields")
    expected_reason_codes = _reason_codes_for_values(
        priority_status=row.priority_status,
        source_gap_count=row.source_gap_count,
        contradiction_count=row.contradiction_count,
        resolution_rule_gap=row.resolution_rule_gap,
        official_anchor_staleness=row.official_anchor_staleness,
        manual_urgency=row.manual_urgency,
        config=config,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match research gap fields")


def _validate_report_consistency(
    report: ProbabilityScreenResearchGapPriorityReport,
) -> None:
    expected_values = {
        "case_count": _decimal_from_int(len(report.rows)),
        "high_priority_count": _status_count(report.rows, STATUS_BLOCK),
        "medium_priority_count": _status_count(report.rows, STATUS_WATCH),
        "low_priority_count": _status_count(report.rows, STATUS_PASS),
        "mean_gap_priority": _mean_decimal(row.gap_priority for row in report.rows),
        "max_gap_priority": max((row.gap_priority for row in report.rows), default=ZERO),
    }
    for field_name, expected_value in expected_values.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    expected_reason_code_counts = _reason_code_counts(report.rows)
    if report.reason_code_counts != expected_reason_code_counts:
        raise ValueError("reason_code_counts must match rows")


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (tuple, list):
        raise ValueError("reason_codes must be a tuple or list")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
    if reason_codes[0] not in STATUS_REASON_CODES:
        raise ValueError("reason_codes must begin with a status reason")
    return reason_codes


def _set_or_validate_digest(value: object, label: str) -> None:
    current_digest = getattr(value, "derived_validation_digest")
    if current_digest == "":
        object.__setattr__(
            value,
            "derived_validation_digest",
            _derived_validation_digest(value, label),
        )
        return
    _require_digest("derived_validation_digest", current_digest)
    if current_digest != _derived_validation_digest(value, label):
        raise ValueError("derived_validation_digest does not match payload")


def _derived_validation_digest(value: object, label: str) -> str:
    ready_value = _json_ready_without_digest(value)
    _reject_private_reference_fields(f"{label} digest payload", ready_value)
    reject_unsafe_surface_fields(f"{label} digest payload", ready_value)
    canonical_payload = json.dumps(
        ready_value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()


def _json_ready_without_digest(value: object) -> dict[str, Any]:
    if not is_dataclass(value) or isinstance(value, type):
        raise ValueError("digest value must be a dataclass instance")
    ready = json_ready_no_floats(asdict(value))
    if type(ready) is not dict:
        raise ValueError("digest payload must be a JSON object")
    ready.pop("derived_validation_digest", None)
    return ready


def _require_payload_digest(payload: dict[str, Any]) -> None:
    supplied_digest = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", supplied_digest)
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest")
    canonical_payload = json.dumps(
        digest_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    expected_digest = hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()
    if supplied_digest != expected_digest:
        raise ValueError("derived_validation_digest does not match payload")


def _freeze_json_object(value: dict[str, Any]) -> FrozenJsonObject:
    return FrozenJsonObject({key: _freeze_json_value(item) for key, item in value.items()})


def _freeze_json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return _freeze_json_object(value)
    if isinstance(value, list):
        return FrozenJsonArray(_freeze_json_value(item) for item in value)
    return value


def _decimal_from_int(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _count_decimal(name: str, value: object) -> Decimal:
    normalized = _decimal(name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be integral")
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _unit_decimal(name: str, value: object) -> Decimal:
    normalized = _decimal(name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return normalized


def _nonnegative_decimal(name: str, value: object) -> Decimal:
    normalized = _decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANTUM)
    except InvalidOperation as exc:
        raise ValueError("decimal value cannot be quantized") from exc


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be exactly datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_digest(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be exactly str")
    if len(value) != 64:
        raise ValueError(f"{name} must be a sha256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be a lowercase sha256 digest")


def _require_public_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be exactly str")
    if not value:
        raise ValueError(f"{name} must not be empty")
    if any(character.isspace() for character in value):
        raise ValueError(f"{name} must not contain whitespace")
    if not all(
        character.isascii()
        and (character.islower() or character.isdigit() or character in "_-.")
        for character in value
    ):
        raise ValueError(f"{name} must be a public identifier")
    reject_unsafe_surface_fields(name, {value: True})


def _require_reason_code(name: str, value: object) -> None:
    _require_public_string(name, value)
    if value not in REASON_CODE_SET:
        raise ValueError(f"{name} is not a supported reason code")


def _require_choice(name: str, value: object, choices: tuple[str, ...]) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be exactly str")
    if value not in choices:
        raise ValueError(f"{name} must be one of {choices}")


def _reject_private_reference_fields(label: str, value: object) -> None:
    for key in _iter_keys(value):
        lowered = key.lower()
        if any(
            fragment in lowered
            for fragment in (
                "candidate_id",
                "market_id",
                "slug",
                "question",
                "url",
                "raw",
                "private",
                "token",
            )
        ):
            raise ValueError(f"private reference field in {label}: {key}")


def _iter_keys(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_keys(asdict(value))
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            keys.append(key)
            keys.extend(_iter_keys(item))
        return tuple(keys)
    if isinstance(value, (list, tuple)):
        keys = []
        for item in value:
            keys.extend(_iter_keys(item))
        return tuple(keys)
    return ()
