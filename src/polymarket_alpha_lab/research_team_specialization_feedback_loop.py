from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from .team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)
from .team_taxonomy import require_team_category_pair, require_team_id


__all__ = (
    "ResearchTeamSpecializationFeedbackLoopConfig",
    "ResearchTeamSpecializationFeedbackLoopReport",
    "ResearchTeamSpecializationFeedbackLoopRow",
    "TeamSpecializationFeedbackInput",
    "TeamSpecializationMemoryUpdateSuggestion",
    "build_research_team_specialization_feedback_loop_report",
    "research_team_specialization_feedback_loop_payload",
)


DEFAULT_CONFIG_VERSION = "research-team-specialization-feedback-loop-v0"
STATUSES = ("pass", "watch", "block")
ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")


class _Missing:
    pass


_MISSING = _Missing()


@dataclass(frozen=True)
class ResearchTeamSpecializationFeedbackLoopConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    pass_hit_rate: Decimal = Decimal("0.600000")
    watch_hit_rate: Decimal = Decimal("0.450000")
    pass_calibration_error: Decimal = Decimal("0.120000")
    watch_calibration_error: Decimal = Decimal("0.220000")
    max_watch_gap_ratio: Decimal = Decimal("0.300000")
    max_watch_stale_memory_ratio: Decimal = Decimal("0.300000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "pass_hit_rate",
            "watch_hit_rate",
            "pass_calibration_error",
            "watch_calibration_error",
            "max_watch_gap_ratio",
            "max_watch_stale_memory_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_hit_rate <= self.watch_hit_rate:
            raise ValueError("pass_hit_rate must be greater than watch_hit_rate")
        if self.pass_calibration_error >= self.watch_calibration_error:
            raise ValueError(
                "pass_calibration_error must be less than watch_calibration_error",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class TeamSpecializationFeedbackInput:
    team_id: str
    category_id: str
    evaluated_case_count: Decimal
    hit_count: Decimal
    mean_calibration_error: Decimal
    unresolved_information_gap_count: Decimal
    postmortem_feedback_count: Decimal
    stale_memory_item_count: Decimal
    updated_at: datetime
    gap_tags: tuple[str, ...] = ()
    feedback_tags: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        object.__setattr__(
            self,
            "evaluated_case_count",
            _require_positive_whole_decimal(
                "evaluated_case_count",
                self.evaluated_case_count,
            ),
        )
        for field_name in (
            "hit_count",
            "unresolved_information_gap_count",
            "postmortem_feedback_count",
            "stale_memory_item_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "mean_calibration_error",
            _require_probability_decimal(
                "mean_calibration_error",
                self.mean_calibration_error,
            ),
        )
        object.__setattr__(self, "updated_at", _as_utc("updated_at", self.updated_at))
        object.__setattr__(
            self,
            "gap_tags",
            _normalize_public_codes("gap_tags", self.gap_tags, allow_empty=True),
        )
        object.__setattr__(
            self,
            "feedback_tags",
            _normalize_public_codes("feedback_tags", self.feedback_tags, allow_empty=True),
        )
        _require_hard_flags("feedback input", self)
        _validate_input_consistency(self)


@dataclass(frozen=True)
class ResearchTeamSpecializationFeedbackLoopRow:
    team_id: str
    category_id: str
    evaluated_case_count: Decimal
    hit_count: Decimal
    hit_rate: Decimal
    mean_calibration_error: Decimal
    unresolved_information_gap_count: Decimal
    information_gap_ratio: Decimal
    postmortem_feedback_count: Decimal
    stale_memory_item_count: Decimal
    memory_stale_ratio: Decimal
    updated_at: datetime
    gap_tags: tuple[str, ...]
    feedback_tags: tuple[str, ...]
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        object.__setattr__(
            self,
            "evaluated_case_count",
            _require_positive_whole_decimal(
                "evaluated_case_count",
                self.evaluated_case_count,
            ),
        )
        for field_name in (
            "hit_count",
            "unresolved_information_gap_count",
            "postmortem_feedback_count",
            "stale_memory_item_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "hit_rate",
            "mean_calibration_error",
            "information_gap_ratio",
            "memory_stale_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "updated_at", _as_utc("updated_at", self.updated_at))
        object.__setattr__(
            self,
            "gap_tags",
            _normalize_public_codes("gap_tags", self.gap_tags, allow_empty=True),
        )
        object.__setattr__(
            self,
            "feedback_tags",
            _normalize_public_codes("feedback_tags", self.feedback_tags, allow_empty=True),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_public_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("feedback row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class TeamSpecializationMemoryUpdateSuggestion:
    team_id: str
    category_id: str
    status: str
    suggestion_codes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "suggestion_codes",
            _normalize_public_codes(
                "suggestion_codes",
                self.suggestion_codes,
                allow_empty=False,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_public_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("memory update suggestion", self)


@dataclass(frozen=True)
class ResearchTeamSpecializationFeedbackLoopReport:
    generated_at: datetime
    config_version: str
    team_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_hit_rate: Decimal | None
    average_calibration_error: Decimal | None
    status: str
    rows: tuple[ResearchTeamSpecializationFeedbackLoopRow, ...]
    memory_update_suggestions: tuple[TeamSpecializationMemoryUpdateSuggestion, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("team_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_hit_rate", "average_calibration_error"):
            object.__setattr__(
                self,
                field_name,
                _require_optional_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "memory_update_suggestions",
            _normalize_suggestions(self.memory_update_suggestions),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_public_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("feedback report", self)
        _validate_report_consistency(self)


def build_research_team_specialization_feedback_loop_report(
    feedback_rows: Iterable[object],
    *,
    config: ResearchTeamSpecializationFeedbackLoopConfig,
    generated_at: datetime,
) -> ResearchTeamSpecializationFeedbackLoopReport:
    if type(config) is not ResearchTeamSpecializationFeedbackLoopConfig:
        raise ValueError("config must be a ResearchTeamSpecializationFeedbackLoopConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    feedback_items = _normalize_feedback_inputs(feedback_rows)
    rows = tuple(
        _row_from_feedback(item=item, config=config)
        for item in sorted(feedback_items, key=lambda item: item.team_id)
    )
    suggestions = tuple(_suggestion_from_row(row) for row in rows)
    reason_codes = _summary_reason_codes(rows)
    return ResearchTeamSpecializationFeedbackLoopReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        team_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        average_hit_rate=_average_optional(tuple(row.hit_rate for row in rows)),
        average_calibration_error=_average_optional(
            tuple(row.mean_calibration_error for row in rows),
        ),
        status=_summary_status(rows),
        rows=rows,
        memory_update_suggestions=suggestions,
        reason_codes=reason_codes,
    )


def research_team_specialization_feedback_loop_payload(
    report: ResearchTeamSpecializationFeedbackLoopReport,
) -> dict[str, Any]:
    if type(report) is not ResearchTeamSpecializationFeedbackLoopReport:
        raise ValueError("report must be a ResearchTeamSpecializationFeedbackLoopReport")
    _require_hard_flags("report", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    reject_unsafe_surface_fields("feedback loop payload", payload)
    _reject_denied_public_values("feedback loop payload", payload)
    return payload


def _row_from_feedback(
    *,
    item: TeamSpecializationFeedbackInput,
    config: ResearchTeamSpecializationFeedbackLoopConfig,
) -> ResearchTeamSpecializationFeedbackLoopRow:
    hit_rate = _quantize(item.hit_count / item.evaluated_case_count)
    gap_ratio = _quantize(
        item.unresolved_information_gap_count / item.evaluated_case_count,
    )
    stale_ratio = _quantize(item.stale_memory_item_count / item.evaluated_case_count)
    status = _row_status(
        hit_rate=hit_rate,
        calibration_error=item.mean_calibration_error,
        gap_ratio=gap_ratio,
        feedback_count=item.postmortem_feedback_count,
        stale_ratio=stale_ratio,
        config=config,
    )
    reason_codes = _row_reason_codes(
        status=status,
        hit_rate=hit_rate,
        calibration_error=item.mean_calibration_error,
        gap_ratio=gap_ratio,
        feedback_count=item.postmortem_feedback_count,
        stale_ratio=stale_ratio,
        config=config,
    )
    return ResearchTeamSpecializationFeedbackLoopRow(
        team_id=item.team_id,
        category_id=item.category_id,
        evaluated_case_count=item.evaluated_case_count,
        hit_count=item.hit_count,
        hit_rate=hit_rate,
        mean_calibration_error=item.mean_calibration_error,
        unresolved_information_gap_count=item.unresolved_information_gap_count,
        information_gap_ratio=gap_ratio,
        postmortem_feedback_count=item.postmortem_feedback_count,
        stale_memory_item_count=item.stale_memory_item_count,
        memory_stale_ratio=stale_ratio,
        updated_at=item.updated_at,
        gap_tags=item.gap_tags,
        feedback_tags=item.feedback_tags,
        status=status,
        reason_codes=reason_codes,
    )


def _suggestion_from_row(
    row: ResearchTeamSpecializationFeedbackLoopRow,
) -> TeamSpecializationMemoryUpdateSuggestion:
    if row.status == "pass":
        suggestion_codes = ("keep_current_specialization_memory",)
        reason_codes = ("specialization_pass",)
    else:
        suggestions: set[str] = set()
        if row.mean_calibration_error > ZERO:
            suggestions.add("tighten_calibration_review")
        if row.information_gap_ratio > ZERO:
            suggestions.add(
                "resolve_information_gaps_before_research_reuse"
                if row.status == "block"
                else "triage_information_gaps",
            )
        if row.postmortem_feedback_count == ZERO:
            suggestions.add("capture_postmortem_feedback")
        if row.memory_stale_ratio > ZERO:
            suggestions.add(
                "rebuild_team_memory"
                if row.status == "block"
                else "refresh_team_memory",
            )
        if not suggestions:
            suggestions.add("refresh_team_memory")
        suggestion_codes = tuple(sorted(suggestions))
        reason_codes = (
            (
                "memory_update_required",
                "specialization_block",
            )
            if row.status == "block"
            else (
                "memory_update_needed",
                "specialization_watch",
            )
        )
    return TeamSpecializationMemoryUpdateSuggestion(
        team_id=row.team_id,
        category_id=row.category_id,
        status=row.status,
        suggestion_codes=suggestion_codes,
        reason_codes=reason_codes,
    )


def _normalize_feedback_inputs(
    feedback_rows: Iterable[object],
) -> tuple[TeamSpecializationFeedbackInput, ...]:
    if isinstance(feedback_rows, (str, bytes)):
        raise ValueError("feedback_rows must be an iterable")
    try:
        values = tuple(feedback_rows)
    except TypeError as exc:
        raise ValueError("feedback_rows must be an iterable") from exc
    return tuple(_coerce_feedback_input(value) for value in values)


def _coerce_feedback_input(value: object) -> TeamSpecializationFeedbackInput:
    if type(value) is TeamSpecializationFeedbackInput:
        _require_hard_flags("feedback input", value)
        return value
    _require_hard_flags("feedback input", value)
    return TeamSpecializationFeedbackInput(
        team_id=_field_value(value, "team_id"),
        category_id=_field_value(value, "category_id"),
        evaluated_case_count=_field_value(value, "evaluated_case_count"),
        hit_count=_field_value(value, "hit_count"),
        mean_calibration_error=_field_value(value, "mean_calibration_error"),
        unresolved_information_gap_count=_field_value(
            value,
            "unresolved_information_gap_count",
        ),
        postmortem_feedback_count=_field_value(value, "postmortem_feedback_count"),
        stale_memory_item_count=_field_value(value, "stale_memory_item_count"),
        updated_at=_field_value(value, "updated_at"),
        gap_tags=_field_value(value, "gap_tags", default=()),
        feedback_tags=_field_value(value, "feedback_tags", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _row_status(
    *,
    hit_rate: Decimal,
    calibration_error: Decimal,
    gap_ratio: Decimal,
    feedback_count: Decimal,
    stale_ratio: Decimal,
    config: ResearchTeamSpecializationFeedbackLoopConfig,
) -> str:
    if (
        hit_rate < config.watch_hit_rate
        or calibration_error > config.watch_calibration_error
        or gap_ratio > config.max_watch_gap_ratio
        or feedback_count == ZERO
        or stale_ratio > config.max_watch_stale_memory_ratio
    ):
        return "block"
    if (
        hit_rate < config.pass_hit_rate
        or calibration_error > config.pass_calibration_error
        or gap_ratio > _quantize(config.max_watch_gap_ratio / Decimal("2"))
        or stale_ratio > ZERO
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    hit_rate: Decimal,
    calibration_error: Decimal,
    gap_ratio: Decimal,
    feedback_count: Decimal,
    stale_ratio: Decimal,
    config: ResearchTeamSpecializationFeedbackLoopConfig,
) -> tuple[str, ...]:
    codes = {f"team_specialization_{status}"}
    codes.add(
        _component_reason(
            "historical_hit_rate",
            status,
            block=hit_rate < config.watch_hit_rate,
            watch=hit_rate < config.pass_hit_rate,
        ),
    )
    codes.add(
        _component_reason(
            "calibration_error",
            status,
            block=calibration_error > config.watch_calibration_error,
            watch=calibration_error > config.pass_calibration_error,
        ),
    )
    if gap_ratio > config.max_watch_gap_ratio:
        codes.add("information_gap_block")
    elif gap_ratio > _quantize(config.max_watch_gap_ratio / Decimal("2")):
        codes.add("information_gap_watch")
    else:
        codes.add("information_gap_controlled")
    codes.add("feedback_missing" if feedback_count == ZERO else "feedback_present")
    codes.add("memory_update_needed" if stale_ratio > ZERO else "memory_current")
    return tuple(sorted(codes))


def _component_reason(
    prefix: str,
    row_status: str,
    *,
    block: bool,
    watch: bool,
) -> str:
    if block:
        return f"{prefix}_block"
    if watch:
        return f"{prefix}_watch"
    if row_status == "block":
        return f"{prefix}_block"
    return f"{prefix}_pass"


def _summary_reason_codes(
    rows: tuple[ResearchTeamSpecializationFeedbackLoopRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_team_feedback",)
    if all(row.status == "pass" for row in rows):
        return ("team_specialization_pass",)
    return tuple(sorted({code for row in rows for code in row.reason_codes}))


def _summary_status(rows: tuple[ResearchTeamSpecializationFeedbackLoopRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _status_count(
    rows: tuple[ResearchTeamSpecializationFeedbackLoopRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _average_optional(values: tuple[Decimal, ...]) -> Decimal | None:
    if not values:
        return None
    return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _normalize_rows(
    rows: tuple[ResearchTeamSpecializationFeedbackLoopRow, ...],
) -> tuple[ResearchTeamSpecializationFeedbackLoopRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchTeamSpecializationFeedbackLoopRow:
            raise ValueError(
                "rows must contain ResearchTeamSpecializationFeedbackLoopRow values",
            )
        _require_hard_flags("feedback row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.team_id))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by team_id")
    return rows


def _normalize_suggestions(
    suggestions: tuple[TeamSpecializationMemoryUpdateSuggestion, ...],
) -> tuple[TeamSpecializationMemoryUpdateSuggestion, ...]:
    if type(suggestions) is not tuple:
        raise ValueError("memory_update_suggestions must be a tuple")
    for suggestion in suggestions:
        if type(suggestion) is not TeamSpecializationMemoryUpdateSuggestion:
            raise ValueError(
                "memory_update_suggestions must contain "
                "TeamSpecializationMemoryUpdateSuggestion values",
            )
        _require_hard_flags("memory update suggestion", suggestion)
    sorted_suggestions = tuple(sorted(suggestions, key=lambda item: item.team_id))
    if suggestions != sorted_suggestions:
        raise ValueError("memory_update_suggestions must be sorted by team_id")
    return suggestions


def _validate_input_consistency(item: TeamSpecializationFeedbackInput) -> None:
    _validate_count_bounds(
        evaluated_case_count=item.evaluated_case_count,
        hit_count=item.hit_count,
        unresolved_information_gap_count=item.unresolved_information_gap_count,
        stale_memory_item_count=item.stale_memory_item_count,
    )


def _validate_row_consistency(row: ResearchTeamSpecializationFeedbackLoopRow) -> None:
    _validate_count_bounds(
        evaluated_case_count=row.evaluated_case_count,
        hit_count=row.hit_count,
        unresolved_information_gap_count=row.unresolved_information_gap_count,
        stale_memory_item_count=row.stale_memory_item_count,
    )
    if row.hit_rate != _quantize(row.hit_count / row.evaluated_case_count):
        raise ValueError("hit_rate must match counts")
    if row.information_gap_ratio != _quantize(
        row.unresolved_information_gap_count / row.evaluated_case_count,
    ):
        raise ValueError("information_gap_ratio must match counts")
    if row.memory_stale_ratio != _quantize(
        row.stale_memory_item_count / row.evaluated_case_count,
    ):
        raise ValueError("memory_stale_ratio must match counts")
    expected_status = "pass"
    if any(code.endswith("_block") for code in row.reason_codes):
        expected_status = "block"
    elif any(code.endswith("_watch") for code in row.reason_codes):
        expected_status = "watch"
    if row.status != expected_status:
        raise ValueError("status must match reason_codes")


def _validate_count_bounds(
    *,
    evaluated_case_count: Decimal,
    hit_count: Decimal,
    unresolved_information_gap_count: Decimal,
    stale_memory_item_count: Decimal,
) -> None:
    if hit_count > evaluated_case_count:
        raise ValueError("hit_count must not exceed evaluated_case_count")
    if unresolved_information_gap_count > evaluated_case_count:
        raise ValueError(
            "unresolved_information_gap_count must not exceed evaluated_case_count",
        )
    if stale_memory_item_count > evaluated_case_count:
        raise ValueError("stale_memory_item_count must not exceed evaluated_case_count")


def _validate_report_consistency(
    report: ResearchTeamSpecializationFeedbackLoopReport,
) -> None:
    if report.team_count != _decimal_count(len(report.rows)):
        raise ValueError("team_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_hit_rate != _average_optional(tuple(row.hit_rate for row in report.rows)):
        raise ValueError("average_hit_rate must match rows")
    if report.average_calibration_error != _average_optional(
        tuple(row.mean_calibration_error for row in report.rows),
    ):
        raise ValueError("average_calibration_error must match rows")
    if report.status != _summary_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if tuple(item.team_id for item in report.memory_update_suggestions) != tuple(
        row.team_id for row in report.rows
    ):
        raise ValueError("memory_update_suggestions must match rows")


def _field_value(value: object, field_name: str, *, default: object = _MISSING) -> object:
    if is_dataclass(value):
        for field in fields(value):
            if field.name == field_name:
                return getattr(value, field_name)
    if hasattr(value, field_name):
        return getattr(value, field_name)
    if default is not _MISSING:
        return default
    raise ValueError(f"{field_name} is required")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _require_optional_probability_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_probability_decimal(field_name, value)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count value must be an int")
    if value < 0:
        raise ValueError("count value must be nonnegative")
    return Decimal(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")


def _normalize_public_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_public_code(field_name, value)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(sorted(set(normalized)))


def _require_public_code(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must contain public codes")
    if value.lower() != value:
        raise ValueError(f"{field_name} must contain public codes")
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789_.-")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must contain public codes")
    _reject_denied_public_values(field_name, value)


def _require_hard_flags(label: str, value: object) -> None:
    require_paper_only_flags(label, value)
    reject_unsafe_surface_fields(label, value)
    _reject_denied_public_values(label, value)


def _reject_denied_public_values(label: str, value: object) -> None:
    for item in _iter_public_strings(value):
        normalized = item.lower()
        if any(fragment in normalized for fragment in _denied_fragments()):
            raise ValueError(f"unsafe public value in {label}")


def _iter_public_strings(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        values: list[str] = []
        for field in fields(value):
            values.extend(_iter_public_strings(field.name))
            values.extend(_iter_public_strings(getattr(value, field.name)))
        return tuple(values)
    if isinstance(value, dict):
        values = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            values.extend(_iter_public_strings(key))
            values.extend(_iter_public_strings(item))
        return tuple(values)
    if isinstance(value, (list, tuple)):
        values = []
        for item in value:
            values.extend(_iter_public_strings(item))
        return tuple(values)
    if type(value) is str:
        return (value,)
    return ()


def _denied_fragments() -> tuple[str, ...]:
    return tuple(
        "".join(chr(code) for code in codes)
        for codes in (
            (99, 97, 110, 100, 105, 100, 97, 116, 101),
            (109, 97, 114, 107, 101, 116),
            (115, 111, 117, 114, 99, 101),
            (117, 114, 108),
            (116, 101, 120, 116),
            (100, 115, 110),
            (116, 97, 98, 108, 101),
            (116, 111, 107, 101, 110),
            (98, 117, 121),
            (115, 101, 108, 108),
            (112, 111, 115, 105, 116, 105, 111, 110),
            (114, 101, 99, 111, 109, 109, 101, 110, 100),
        )
    )
