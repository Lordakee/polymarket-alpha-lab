"""Safe report-only reasoning trace summary for research screening."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    UNSAFE_SURFACE_FIELD_FRAGMENTS,
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


__all__ = (
    "ResearchScreeningReasoningTraceConfig",
    "ResearchScreeningReasoningTraceInput",
    "ResearchScreeningReasoningTraceReasonCodeCount",
    "ResearchScreeningReasoningTraceReport",
    "ResearchScreeningReasoningTraceRow",
    "build_research_screening_reasoning_trace_report",
    "research_screening_reasoning_trace_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-screening-reasoning-trace-report-v0"

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCK_STATUS = "block"
STATUSES = (PASS_STATUS, WATCH_STATUS, BLOCK_STATUS)

NO_INPUTS_REASON = "no_screening_traces"
PASS_REPORT_REASON = "research_screening_reasoning_trace_pass"
WATCH_REPORT_REASON = "research_screening_reasoning_trace_watch"
BLOCK_REPORT_REASON = "research_screening_reasoning_trace_block"

TRACE_PASS_REASON = "screening_trace_pass"
TRACE_WATCH_REASON = "screening_trace_watch"
TRACE_BLOCK_REASON = "screening_trace_block"
SCORE_WATCH_REASON = "screening_score_watch"
SCORE_BLOCK_REASON = "screening_score_block"
THIN_SOURCES_REASON = "screening_sources_thin"
REVIEW_PROMPTS_REASON = "screening_review_prompts_present"
BLOCKING_REASONS_REASON = "screening_blocking_reasons_present"

ROW_REASON_CODES = (
    BLOCKING_REASONS_REASON,
    REVIEW_PROMPTS_REASON,
    SCORE_BLOCK_REASON,
    SCORE_WATCH_REASON,
    THIN_SOURCES_REASON,
    TRACE_BLOCK_REASON,
    TRACE_WATCH_REASON,
    TRACE_PASS_REASON,
)

REPORT_PRESENT_REASONS = (
    BLOCKING_REASONS_REASON,
    REVIEW_PROMPTS_REASON,
    "screening_score_block_present",
    "screening_score_watch_present",
    "screening_sources_thin_present",
)

NUMERIC_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
UTC_OFFSET = timedelta(0)

PUBLIC_TEXT_FRAGMENTS = (
    *tuple(UNSAFE_SURFACE_FIELD_FRAGMENTS),
    "raw" "_id",
    "source" "_url",
    "raw" "_text",
    "market" "_question",
    "dsn",
    "table",
    "token",
    "http",
    "://",
    "www.",
    "bu" "y",
    "se" "ll",
    "po" "sition",
    "reco" "mmend",
)

PUBLIC_FIELD_FRAGMENTS = (
    "raw" "_id",
    "source" "_url",
    "raw" "_text",
    "market" "_question",
    "dsn",
    "table",
    "token",
)


class _Missing:
    pass


_MISSING = _Missing()


@dataclass(frozen=True)
class ResearchScreeningReasoningTraceConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    pass_score_threshold: Decimal = Decimal("0.700000")
    block_score_threshold: Decimal = Decimal("0.400000")
    min_scoring_source_count: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchScreeningReasoningTraceConfig:
            raise TypeError(
                "ResearchScreeningReasoningTraceConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchScreeningReasoningTraceConfig:
            raise ValueError(
                "config must be exactly ResearchScreeningReasoningTraceConfig",
            )
        _require_public_code("config_version", self.config_version)
        for field_name in ("pass_score_threshold", "block_score_threshold"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_scoring_source_count",
            _require_nonnegative_whole_decimal(
                "min_scoring_source_count",
                self.min_scoring_source_count,
            ),
        )
        if self.block_score_threshold > self.pass_score_threshold:
            raise ValueError(
                "block_score_threshold must not exceed pass_score_threshold",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchScreeningReasoningTraceInput:
    trace_key: str
    screening_stage: str
    scoring_source_codes: tuple[str, ...]
    screening_score: Decimal
    source_quality_score: Decimal
    source_agreement_score: Decimal
    freshness_score: Decimal
    safety_score: Decimal
    blocking_reason_codes: tuple[str, ...] = ()
    review_prompt_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchScreeningReasoningTraceInput:
            raise TypeError(
                "ResearchScreeningReasoningTraceInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchScreeningReasoningTraceInput:
            raise ValueError(
                "input must be exactly ResearchScreeningReasoningTraceInput",
            )
        _require_public_code("trace_key", self.trace_key)
        _require_public_code("screening_stage", self.screening_stage)
        object.__setattr__(
            self,
            "scoring_source_codes",
            _normalize_public_code_tuple(
                "scoring_source_codes",
                self.scoring_source_codes,
                allow_empty=False,
            ),
        )
        for field_name in (
            "screening_score",
            "source_quality_score",
            "source_agreement_score",
            "freshness_score",
            "safety_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "blocking_reason_codes",
            _normalize_public_code_tuple(
                "blocking_reason_codes",
                self.blocking_reason_codes,
                allow_empty=True,
            ),
        )
        object.__setattr__(
            self,
            "review_prompt_codes",
            _normalize_public_code_tuple(
                "review_prompt_codes",
                self.review_prompt_codes,
                allow_empty=True,
            ),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchScreeningReasoningTraceRow:
    trace_rank: Decimal
    trace_key: str
    screening_stage: str
    scoring_source_count: Decimal
    screening_score: Decimal
    source_quality_score: Decimal
    source_agreement_score: Decimal
    freshness_score: Decimal
    safety_score: Decimal
    blocking_reason_count: Decimal
    review_prompt_count: Decimal
    trace_status: str
    scoring_source_codes: tuple[str, ...]
    blocking_reason_codes: tuple[str, ...]
    review_prompt_codes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchScreeningReasoningTraceRow:
            raise TypeError(
                "ResearchScreeningReasoningTraceRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchScreeningReasoningTraceRow:
            raise ValueError("row must be exactly ResearchScreeningReasoningTraceRow")
        object.__setattr__(
            self,
            "trace_rank",
            _require_positive_whole_decimal("trace_rank", self.trace_rank),
        )
        _require_public_code("trace_key", self.trace_key)
        _require_public_code("screening_stage", self.screening_stage)
        for field_name in (
            "scoring_source_count",
            "blocking_reason_count",
            "review_prompt_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "screening_score",
            "source_quality_score",
            "source_agreement_score",
            "freshness_score",
            "safety_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("trace_status", self.trace_status)
        for field_name in (
            "scoring_source_codes",
            "blocking_reason_codes",
            "review_prompt_codes",
            "reason_codes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_public_code_tuple(
                    field_name,
                    getattr(self, field_name),
                    allow_empty=field_name != "reason_codes",
                ),
            )
        _require_hard_flags("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchScreeningReasoningTraceReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchScreeningReasoningTraceReasonCodeCount:
            raise TypeError(
                "ResearchScreeningReasoningTraceReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchScreeningReasoningTraceReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "ResearchScreeningReasoningTraceReasonCodeCount",
            )
        _require_public_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason count", self)


@dataclass(frozen=True)
class ResearchScreeningReasoningTraceReport:
    generated_at: datetime
    config_version: str
    input_trace_count: Decimal
    pass_trace_count: Decimal
    watch_trace_count: Decimal
    block_trace_count: Decimal
    review_prompt_trace_count: Decimal
    blocking_reason_trace_count: Decimal
    thin_source_trace_count: Decimal
    average_screening_score: Decimal
    min_screening_score: Decimal
    report_status: str
    rows: tuple[ResearchScreeningReasoningTraceRow, ...]
    reason_code_counts: tuple[ResearchScreeningReasoningTraceReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchScreeningReasoningTraceReport:
            raise TypeError(
                "ResearchScreeningReasoningTraceReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchScreeningReasoningTraceReport:
            raise ValueError(
                "report must be exactly ResearchScreeningReasoningTraceReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_code("config_version", self.config_version)
        for field_name in (
            "input_trace_count",
            "pass_trace_count",
            "watch_trace_count",
            "block_trace_count",
            "review_prompt_trace_count",
            "blocking_reason_trace_count",
            "thin_source_trace_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_screening_score", "min_screening_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("report_status", self.report_status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_public_code_tuple(
                "reason_codes",
                self.reason_codes,
                allow_empty=False,
            ),
        )
        _require_hard_flags("report", self)
        _validate_report(self)


def build_research_screening_reasoning_trace_report(
    inputs: list[ResearchScreeningReasoningTraceInput]
    | tuple[ResearchScreeningReasoningTraceInput, ...],
    *,
    config: ResearchScreeningReasoningTraceConfig,
    generated_at: datetime,
) -> ResearchScreeningReasoningTraceReport:
    if type(config) is not ResearchScreeningReasoningTraceConfig:
        raise ValueError("config must be a ResearchScreeningReasoningTraceConfig")
    _require_hard_flags("config", config)
    report_time = _as_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(inputs)
    drafts = tuple(_row_draft(row, config=config) for row in input_rows)
    rows = tuple(
        _build_row(rank, draft)
        for rank, draft in enumerate(sorted(drafts, key=_draft_sort_key), start=1)
    )
    return ResearchScreeningReasoningTraceReport(
        generated_at=report_time,
        config_version=config.config_version,
        input_trace_count=_count_from_int(len(input_rows)),
        pass_trace_count=_status_count(rows, PASS_STATUS),
        watch_trace_count=_status_count(rows, WATCH_STATUS),
        block_trace_count=_status_count(rows, BLOCK_STATUS),
        review_prompt_trace_count=_row_has_count(rows, REVIEW_PROMPTS_REASON),
        blocking_reason_trace_count=_row_has_count(rows, BLOCKING_REASONS_REASON),
        thin_source_trace_count=_row_has_count(rows, THIN_SOURCES_REASON),
        average_screening_score=_average_screening_score(rows),
        min_screening_score=_min_screening_score(rows),
        report_status=_report_status(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows),
        reason_codes=_report_reason_codes(rows),
    )


def research_screening_reasoning_trace_report_payload(
    report: ResearchScreeningReasoningTraceReport,
) -> dict[str, Any]:
    if type(report) is not ResearchScreeningReasoningTraceReport:
        raise ValueError("report must be a ResearchScreeningReasoningTraceReport")
    require_paper_only_flags("ResearchScreeningReasoningTraceReport", report)
    _require_report_surface_flags(report)
    payload = asdict(report)
    reject_unsafe_surface_fields("research screening reasoning trace payload", payload)
    _reject_public_surface_fields("research screening reasoning trace payload", payload)
    _reject_public_surface_values("research screening reasoning trace payload", payload)
    guarded = json_ready_no_floats(payload)
    if type(guarded) is not dict:
        raise ValueError("report payload must be an object")
    return guarded


def _row_draft(
    row: ResearchScreeningReasoningTraceInput,
    *,
    config: ResearchScreeningReasoningTraceConfig,
) -> tuple[
    ResearchScreeningReasoningTraceInput,
    Decimal,
    Decimal,
    Decimal,
    tuple[str, ...],
    str,
]:
    scoring_source_count = _count_from_int(len(row.scoring_source_codes))
    blocking_reason_count = _count_from_int(len(row.blocking_reason_codes))
    review_prompt_count = _count_from_int(len(row.review_prompt_codes))
    reason_codes = _row_reason_codes(
        screening_score=row.screening_score,
        scoring_source_count=scoring_source_count,
        blocking_reason_count=blocking_reason_count,
        review_prompt_count=review_prompt_count,
        config=config,
    )
    return (
        row,
        scoring_source_count,
        blocking_reason_count,
        review_prompt_count,
        reason_codes,
        _trace_status(reason_codes),
    )


def _build_row(
    rank: int,
    draft: tuple[
        ResearchScreeningReasoningTraceInput,
        Decimal,
        Decimal,
        Decimal,
        tuple[str, ...],
        str,
    ],
) -> ResearchScreeningReasoningTraceRow:
    (
        row,
        scoring_source_count,
        blocking_reason_count,
        review_prompt_count,
        reason_codes,
        trace_status,
    ) = draft
    return ResearchScreeningReasoningTraceRow(
        trace_rank=_count_from_int(rank),
        trace_key=row.trace_key,
        screening_stage=row.screening_stage,
        scoring_source_count=scoring_source_count,
        screening_score=row.screening_score,
        source_quality_score=row.source_quality_score,
        source_agreement_score=row.source_agreement_score,
        freshness_score=row.freshness_score,
        safety_score=row.safety_score,
        blocking_reason_count=blocking_reason_count,
        review_prompt_count=review_prompt_count,
        trace_status=trace_status,
        scoring_source_codes=row.scoring_source_codes,
        blocking_reason_codes=row.blocking_reason_codes,
        review_prompt_codes=row.review_prompt_codes,
        reason_codes=reason_codes,
    )


def _draft_sort_key(
    draft: tuple[
        ResearchScreeningReasoningTraceInput,
        Decimal,
        Decimal,
        Decimal,
        tuple[str, ...],
        str,
    ],
) -> tuple[int, Decimal, str, str]:
    row, _source_count, _block_count, _review_count, _reason_codes, trace_status = draft
    return (
        _status_rank(trace_status),
        row.screening_score,
        row.screening_stage,
        row.trace_key,
    )


def _row_sort_key(row: ResearchScreeningReasoningTraceRow) -> tuple[int, Decimal, str, str]:
    return (
        _status_rank(row.trace_status),
        row.screening_score,
        row.screening_stage,
        row.trace_key,
    )


def _row_reason_codes(
    *,
    screening_score: Decimal,
    scoring_source_count: Decimal,
    blocking_reason_count: Decimal,
    review_prompt_count: Decimal,
    config: ResearchScreeningReasoningTraceConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if blocking_reason_count > ZERO:
        reason_codes.append(BLOCKING_REASONS_REASON)
    if review_prompt_count > ZERO:
        reason_codes.append(REVIEW_PROMPTS_REASON)
    if screening_score < config.block_score_threshold:
        reason_codes.append(SCORE_BLOCK_REASON)
    elif screening_score < config.pass_score_threshold:
        reason_codes.append(SCORE_WATCH_REASON)
    if scoring_source_count < config.min_scoring_source_count:
        reason_codes.append(THIN_SOURCES_REASON)
    trace_status = _trace_status(tuple(reason_codes))
    if trace_status == BLOCK_STATUS:
        reason_codes.append(TRACE_BLOCK_REASON)
    elif trace_status == WATCH_STATUS:
        reason_codes.append(TRACE_WATCH_REASON)
    else:
        reason_codes.append(TRACE_PASS_REASON)
    return tuple(code for code in ROW_REASON_CODES if code in reason_codes)


def _trace_status(reason_codes: tuple[str, ...]) -> str:
    substantive_reasons = tuple(
        reason_code
        for reason_code in reason_codes
        if reason_code not in (TRACE_BLOCK_REASON, TRACE_WATCH_REASON, TRACE_PASS_REASON)
    )
    if (
        BLOCKING_REASONS_REASON in substantive_reasons
        or SCORE_BLOCK_REASON in substantive_reasons
    ):
        return BLOCK_STATUS
    if substantive_reasons:
        return WATCH_STATUS
    return PASS_STATUS


def _report_status(rows: tuple[ResearchScreeningReasoningTraceRow, ...]) -> str:
    if not rows:
        return BLOCK_STATUS
    if any(row.trace_status == BLOCK_STATUS for row in rows):
        return BLOCK_STATUS
    if any(row.trace_status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _report_reason_codes(
    rows: tuple[ResearchScreeningReasoningTraceRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    status = _report_status(rows)
    reason_codes: list[str] = [
        {
            PASS_STATUS: PASS_REPORT_REASON,
            WATCH_STATUS: WATCH_REPORT_REASON,
            BLOCK_STATUS: BLOCK_REPORT_REASON,
        }[status],
    ]
    row_reasons = {reason_code for row in rows for reason_code in row.reason_codes}
    if BLOCKING_REASONS_REASON in row_reasons:
        reason_codes.append(BLOCKING_REASONS_REASON)
    if REVIEW_PROMPTS_REASON in row_reasons:
        reason_codes.append(REVIEW_PROMPTS_REASON)
    if SCORE_BLOCK_REASON in row_reasons:
        reason_codes.append("screening_score_block_present")
    if SCORE_WATCH_REASON in row_reasons:
        reason_codes.append("screening_score_watch_present")
    if THIN_SOURCES_REASON in row_reasons:
        reason_codes.append("screening_sources_thin_present")
    return tuple(reason_codes)


def _reason_code_counts(
    rows: tuple[ResearchScreeningReasoningTraceRow, ...],
) -> tuple[ResearchScreeningReasoningTraceReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchScreeningReasoningTraceReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
            ),
        )
    counter: Counter[str] = Counter(
        reason_code for row in rows for reason_code in row.reason_codes
    )
    return tuple(
        ResearchScreeningReasoningTraceReasonCodeCount(
            reason_code=reason_code,
            count=_count_from_int(counter[reason_code]),
        )
        for reason_code in sorted(counter)
    )


def _normalize_inputs(
    value: object,
) -> tuple[ResearchScreeningReasoningTraceInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchScreeningReasoningTraceInput:
            raise ValueError(
                "inputs must contain ResearchScreeningReasoningTraceInput values",
            )
        _require_hard_flags("input", row)
        if row.trace_key in seen:
            raise ValueError("inputs must have unique trace_key values")
        seen.add(row.trace_key)
    return rows


def _normalize_rows(
    value: object,
) -> tuple[ResearchScreeningReasoningTraceRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for index, row in enumerate(rows, start=1):
        if type(row) is not ResearchScreeningReasoningTraceRow:
            raise ValueError(
                "rows must contain ResearchScreeningReasoningTraceRow values",
            )
        _require_hard_flags("row", row)
        if row.trace_rank != _count_from_int(index):
            raise ValueError("trace_rank must match row sequence")
        if row.trace_key in seen:
            raise ValueError("rows must have unique trace_key values")
        seen.add(row.trace_key)
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchScreeningReasoningTraceReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchScreeningReasoningTraceReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchScreeningReasoningTraceReasonCodeCount values",
            )
        _require_hard_flags("reason count", row)
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must have unique reason_code values")
        seen.add(row.reason_code)
    if rows != tuple(sorted(rows, key=lambda item: item.reason_code)):
        raise ValueError("reason_code_counts must be sorted")
    return rows


def _validate_row(row: ResearchScreeningReasoningTraceRow) -> None:
    if row.scoring_source_count != _count_from_int(len(row.scoring_source_codes)):
        raise ValueError("scoring_source_count must match scoring_source_codes")
    if row.blocking_reason_count != _count_from_int(len(row.blocking_reason_codes)):
        raise ValueError("blocking_reason_count must match blocking_reason_codes")
    if row.review_prompt_count != _count_from_int(len(row.review_prompt_codes)):
        raise ValueError("review_prompt_count must match review_prompt_codes")
    if row.trace_status != _trace_status(row.reason_codes):
        raise ValueError("trace_status must match reason_codes")
    if row.reason_codes != tuple(code for code in ROW_REASON_CODES if code in row.reason_codes):
        raise ValueError("reason_codes must use canonical sequence")


def _validate_report(report: ResearchScreeningReasoningTraceReport) -> None:
    if report.input_trace_count != _count_from_int(len(report.rows)):
        raise ValueError("input_trace_count must match rows")
    if report.pass_trace_count != _status_count(report.rows, PASS_STATUS):
        raise ValueError("pass_trace_count must match rows")
    if report.watch_trace_count != _status_count(report.rows, WATCH_STATUS):
        raise ValueError("watch_trace_count must match rows")
    if report.block_trace_count != _status_count(report.rows, BLOCK_STATUS):
        raise ValueError("block_trace_count must match rows")
    if report.review_prompt_trace_count != _row_has_count(rows=report.rows, reason=REVIEW_PROMPTS_REASON):
        raise ValueError("review_prompt_trace_count must match rows")
    if report.blocking_reason_trace_count != _row_has_count(rows=report.rows, reason=BLOCKING_REASONS_REASON):
        raise ValueError("blocking_reason_trace_count must match rows")
    if report.thin_source_trace_count != _row_has_count(rows=report.rows, reason=THIN_SOURCES_REASON):
        raise ValueError("thin_source_trace_count must match rows")
    if report.average_screening_score != _average_screening_score(report.rows):
        raise ValueError("average_screening_score must match rows")
    if report.min_screening_score != _min_screening_score(report.rows):
        raise ValueError("min_screening_score must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sorting")


def _status_count(
    rows: tuple[ResearchScreeningReasoningTraceRow, ...],
    status: str,
) -> Decimal:
    return _count_from_int(sum(1 for row in rows if row.trace_status == status))


def _row_has_count(
    rows: tuple[ResearchScreeningReasoningTraceRow, ...],
    reason: str,
) -> Decimal:
    return _count_from_int(sum(1 for row in rows if reason in row.reason_codes))


def _average_screening_score(
    rows: tuple[ResearchScreeningReasoningTraceRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return _quantize(sum((row.screening_score for row in rows), ZERO) / Decimal(len(rows)))


def _min_screening_score(rows: tuple[ResearchScreeningReasoningTraceRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    return min(row.screening_score for row in rows)


def _status_rank(status: str) -> int:
    if status == BLOCK_STATUS:
        return 0
    if status == WATCH_STATUS:
        return 1
    if status == PASS_STATUS:
        return 2
    raise ValueError("unknown status")


def _require_report_surface_flags(
    report: ResearchScreeningReasoningTraceReport,
) -> None:
    for row in report.rows:
        require_paper_only_flags("ResearchScreeningReasoningTraceRow", row)
    for row in report.reason_code_counts:
        require_paper_only_flags("ResearchScreeningReasoningTraceReasonCodeCount", row)


def _reject_public_surface_fields(label: str, payload: object) -> None:
    for key in _iter_payload_keys(payload):
        normalized = key.lower()
        if any(fragment in normalized for fragment in PUBLIC_FIELD_FRAGMENTS):
            raise ValueError(f"unsafe public surface field in {label}: {key}")


def _reject_public_surface_values(label: str, payload: object) -> None:
    for value in _iter_payload_string_values(payload):
        if _has_unsafe_public_text(value):
            raise ValueError(f"unsafe public string value in {label}")


def _iter_payload_keys(value: object) -> tuple[str, ...]:
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            keys.append(key)
            keys.extend(_iter_payload_keys(item))
        return tuple(keys)
    if isinstance(value, list):
        keys = []
        for item in value:
            keys.extend(_iter_payload_keys(item))
        return tuple(keys)
    return ()


def _iter_payload_string_values(value: object) -> tuple[str, ...]:
    if isinstance(value, dict):
        values: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            values.extend(_iter_payload_string_values(item))
        return tuple(values)
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(_iter_payload_string_values(item))
        return tuple(values)
    if type(value) is str:
        return (value,)
    return ()


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() != UTC_OFFSET:
        raise ValueError(f"{field_name} must be UTC-aware")
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


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return _quantize(normalized)


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return _quantize(normalized)


def _count_from_int(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(NUMERIC_QUANTUM)


def _require_public_code(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty public code")
    if _has_unsafe_public_text(value):
        raise ValueError(f"{field_name} has unsafe public string content")
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789_-"
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must contain deterministic public code text")


def _normalize_public_code_tuple(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for item in value:
        _require_public_code(field_name, item)
        normalized.append(item)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(sorted(set(normalized)))


def _has_unsafe_public_text(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in PUBLIC_TEXT_FRAGMENTS)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")


def _field_value(value: object, field_name: str, *, default: object = _MISSING) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            if field.name == field_name:
                return getattr(value, field_name)
    if hasattr(value, field_name):
        return getattr(value, field_name)
    if default is not _MISSING:
        return default
    raise ValueError(f"{field_name} is required")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if _field_value(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")
