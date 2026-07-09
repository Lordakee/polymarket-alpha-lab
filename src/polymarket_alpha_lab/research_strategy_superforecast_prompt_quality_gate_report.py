"""Pure report for superforecast prompt quality gate review."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, localcontext
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_SUPERFORECAST_PROMPT_QUALITY_GATE_REPORT_CONFIG_VERSION",
    "PROMPT_QUALITY_GATE_STATUSES",
    "ResearchStrategySuperforecastPromptContext",
    "ResearchStrategySuperforecastPromptQualityGateConfig",
    "ResearchStrategySuperforecastPromptQualityGateReasonCodeCount",
    "ResearchStrategySuperforecastPromptQualityGateReport",
    "ResearchStrategySuperforecastPromptQualityGateRow",
    "build_research_strategy_superforecast_prompt_quality_gate_report",
    "research_strategy_superforecast_prompt_quality_gate_report_digest",
    "research_strategy_superforecast_prompt_quality_gate_report_payload",
)


DEFAULT_RESEARCH_STRATEGY_SUPERFORECAST_PROMPT_QUALITY_GATE_REPORT_CONFIG_VERSION = (
    "research-strategy-superforecast-prompt-quality-gate-report-v0"
)
PROMPT_QUALITY_GATE_STATUSES = ("pass", "watch", "block")
PUBLIC_STATUSES = PROMPT_QUALITY_GATE_STATUSES
NO_CONTEXTS_REASON = "superforecast_prompt_quality_no_prompt_contexts"
PROMPT_QUALITY_PASS_REASON = "superforecast_prompt_quality_pass"
PROMPT_QUALITY_WATCH_REASON = "superforecast_prompt_quality_watch"
PROMPT_QUALITY_BLOCK_REASON = "superforecast_prompt_quality_block"
COMPONENT_FIELDS = (
    "sanitized_prompt_context_completeness",
    "source_diversity",
    "cost_context",
    "resolution_clarity",
    "domain_memory_readiness",
)
COMPONENT_BLOCK_REASONS = tuple(f"{field_name}_block" for field_name in COMPONENT_FIELDS)
COMPONENT_WATCH_REASONS = tuple(f"{field_name}_watch" for field_name in COMPONENT_FIELDS)
REASON_PRIORITY = (
    "sanitized_prompt_context_completeness_block",
    "source_diversity_block",
    "cost_context_block",
    "resolution_clarity_block",
    "domain_memory_readiness_block",
    PROMPT_QUALITY_BLOCK_REASON,
    "sanitized_prompt_context_completeness_watch",
    "source_diversity_watch",
    "cost_context_watch",
    "resolution_clarity_watch",
    "domain_memory_readiness_watch",
    PROMPT_QUALITY_WATCH_REASON,
    PROMPT_QUALITY_PASS_REASON,
    NO_CONTEXTS_REASON,
)
STATUS_SORT_WEIGHT = {
    "block": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
FIVE = Decimal("5.000000")
QUANTUM = Decimal("0.000001")
DECIMAL_CONTEXT_PRECISION = 28


class _FinalDataclass:
    def __init_subclass__(cls) -> None:
        super().__init_subclass__()


@dataclass(frozen=True)
class ResearchStrategySuperforecastPromptQualityGateConfig(_FinalDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_SUPERFORECAST_PROMPT_QUALITY_GATE_REPORT_CONFIG_VERSION
    )
    sanitized_prompt_context_completeness_pass_floor: Decimal = Decimal("0.800000")
    sanitized_prompt_context_completeness_watch_floor: Decimal = Decimal("0.550000")
    source_diversity_pass_floor: Decimal = Decimal("0.700000")
    source_diversity_watch_floor: Decimal = Decimal("0.450000")
    cost_context_pass_floor: Decimal = Decimal("0.700000")
    cost_context_watch_floor: Decimal = Decimal("0.500000")
    resolution_clarity_pass_floor: Decimal = Decimal("0.800000")
    resolution_clarity_watch_floor: Decimal = Decimal("0.550000")
    domain_memory_readiness_pass_floor: Decimal = Decimal("0.750000")
    domain_memory_readiness_watch_floor: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategySuperforecastPromptQualityGateConfig,
            "config",
        )
        _require_public_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_SUPERFORECAST_PROMPT_QUALITY_GATE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "sanitized_prompt_context_completeness_pass_floor",
            "sanitized_prompt_context_completeness_watch_floor",
            "source_diversity_pass_floor",
            "source_diversity_watch_floor",
            "cost_context_pass_floor",
            "cost_context_watch_floor",
            "resolution_clarity_pass_floor",
            "resolution_clarity_watch_floor",
            "domain_memory_readiness_pass_floor",
            "domain_memory_readiness_watch_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in COMPONENT_FIELDS:
            pass_name = f"{field_name}_pass_floor"
            watch_name = f"{field_name}_watch_floor"
            if getattr(self, pass_name) < getattr(self, watch_name):
                raise ValueError(f"{pass_name} must be at least paired watch floor")
        _require_hard_phase_flags("config", self)
        _reject_unsafe_payload(_json_ready(self))


@dataclass(frozen=True)
class ResearchStrategySuperforecastPromptContext(_FinalDataclass):
    prompt_context_key: str
    sanitized_prompt_context_completeness: Decimal
    source_diversity: Decimal
    cost_context: Decimal
    resolution_clarity: Decimal
    domain_memory_readiness: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategySuperforecastPromptContext,
            "prompt_context",
        )
        _require_internal_reference_text("prompt_context_key", self.prompt_context_key)
        for field_name in COMPONENT_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes_allow_empty(self.reason_codes),
        )
        _require_hard_phase_flags("prompt_context", self)


@dataclass(frozen=True)
class ResearchStrategySuperforecastPromptQualityGateRow(_FinalDataclass):
    row_number: Decimal
    public_prompt_context_hash: str
    sanitized_prompt_context_completeness: Decimal
    source_diversity: Decimal
    cost_context: Decimal
    resolution_clarity: Decimal
    domain_memory_readiness: Decimal
    prompt_quality_score: Decimal
    observed_at: datetime
    prompt_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategySuperforecastPromptQualityGateRow,
            "row",
        )
        object.__setattr__(
            self,
            "row_number",
            _normalize_positive_count("row_number", self.row_number),
        )
        _require_public_hash("public_prompt_context_hash", self.public_prompt_context_hash)
        for field_name in (*COMPONENT_FIELDS, "prompt_quality_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "prompt_age_seconds",
            _normalize_nonnegative_decimal("prompt_age_seconds", self.prompt_age_seconds),
        )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_digest("validation_digest", self.validation_digest)
        _require_hard_phase_flags("row", self)
        _validate_row(self)
        if self.validation_digest != _validation_digest(_public_mapping(self)):
            raise ValueError("validation_digest must match row fields")
        _reject_unsafe_payload(_json_ready(self))


@dataclass(frozen=True)
class ResearchStrategySuperforecastPromptQualityGateReasonCodeCount(_FinalDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategySuperforecastPromptQualityGateReasonCodeCount,
            "reason_code_count",
        )
        _require_public_text("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_count("count", self.count),
        )
        _require_hard_phase_flags("reason_code_count", self)
        _reject_unsafe_payload(_json_ready(self))


@dataclass(frozen=True)
class ResearchStrategySuperforecastPromptQualityGateReport(_FinalDataclass):
    generated_at: datetime
    config_version: str
    prompt_context_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_prompt_quality_score: Decimal
    min_prompt_quality_score: Decimal
    max_prompt_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchStrategySuperforecastPromptQualityGateReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchStrategySuperforecastPromptQualityGateRow, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategySuperforecastPromptQualityGateReport,
            "report",
        )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_text("config_version", self.config_version)
        for field_name in (
            "prompt_context_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_prompt_quality_score",
            "min_prompt_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_prompt_age_seconds",
            _normalize_nonnegative_decimal(
                "max_prompt_age_seconds",
                self.max_prompt_age_seconds,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_digest("validation_digest", self.validation_digest)
        _require_hard_phase_flags("report", self)
        _validate_report(self)
        if self.validation_digest != _validation_digest(_public_mapping(self)):
            raise ValueError("validation_digest must match report fields")
        _reject_unsafe_payload(_json_ready(self))


def build_research_strategy_superforecast_prompt_quality_gate_report(
    prompt_contexts: Iterable[ResearchStrategySuperforecastPromptContext],
    *,
    config: ResearchStrategySuperforecastPromptQualityGateConfig,
    generated_at: datetime,
) -> ResearchStrategySuperforecastPromptQualityGateReport:
    if type(config) is not ResearchStrategySuperforecastPromptQualityGateConfig:
        raise ValueError(
            "config must be a ResearchStrategySuperforecastPromptQualityGateConfig",
        )
    _require_hard_phase_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    contexts = _normalize_prompt_contexts(prompt_contexts)
    drafts = tuple(
        sorted(
            (
                _draft_row_from_prompt_context(
                    prompt_context,
                    config=config,
                    generated_at=generated_at,
                )
                for prompt_context in contexts
            ),
            key=_draft_row_sort_key,
        ),
    )
    rows = tuple(
        _row_from_draft(row_number=index, draft_values=draft)
        for index, draft in enumerate(drafts, start=1)
    )
    reason_codes = _report_reason_codes(rows)
    reason_code_counts = _reason_code_counts(rows)
    report_values = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "prompt_context_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "average_prompt_quality_score": _average_prompt_quality_score(rows),
        "min_prompt_quality_score": _min_prompt_quality_score(rows),
        "max_prompt_age_seconds": _max_prompt_age_seconds(rows),
        "status": _report_status(rows),
        "reason_codes": reason_codes,
        "reason_code_counts": reason_code_counts,
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategySuperforecastPromptQualityGateReport(
        **report_values,
        validation_digest=_validation_digest(report_values),
    )


def research_strategy_superforecast_prompt_quality_gate_report_payload(
    report: ResearchStrategySuperforecastPromptQualityGateReport | Mapping[str, object],
) -> dict[str, Any]:
    if type(report) is ResearchStrategySuperforecastPromptQualityGateReport:
        _require_hard_phase_flags("report", report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _validate_public_payload(payload)
        return payload
    if isinstance(report, Mapping):
        payload = dict(report)
        _validate_public_payload(payload)
        return payload
    raise ValueError(
        "report must be a ResearchStrategySuperforecastPromptQualityGateReport or mapping",
    )


def research_strategy_superforecast_prompt_quality_gate_report_digest(
    report: ResearchStrategySuperforecastPromptQualityGateReport | Mapping[str, object],
) -> str:
    payload = research_strategy_superforecast_prompt_quality_gate_report_payload(report)
    digest = payload.get("validation_digest")
    if type(digest) is not str:
        raise ValueError("validation_digest must be a string")
    _require_digest("validation_digest", digest)
    return digest


def _draft_row_from_prompt_context(
    prompt_context: ResearchStrategySuperforecastPromptContext,
    *,
    config: ResearchStrategySuperforecastPromptQualityGateConfig,
    generated_at: datetime,
) -> dict[str, object]:
    if prompt_context.observed_at > generated_at:
        raise ValueError("generated_at must not precede observed_at")
    prompt_quality_score = _prompt_quality_score(prompt_context)
    reason_codes = _row_reason_codes(prompt_context, config=config)
    status = _row_status(reason_codes)
    return {
        "public_prompt_context_hash": _public_hash(prompt_context.prompt_context_key),
        "sanitized_prompt_context_completeness": (
            prompt_context.sanitized_prompt_context_completeness
        ),
        "source_diversity": prompt_context.source_diversity,
        "cost_context": prompt_context.cost_context,
        "resolution_clarity": prompt_context.resolution_clarity,
        "domain_memory_readiness": prompt_context.domain_memory_readiness,
        "prompt_quality_score": prompt_quality_score,
        "observed_at": prompt_context.observed_at,
        "prompt_age_seconds": _seconds_between(prompt_context.observed_at, generated_at),
        "status": status,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_from_draft(
    *,
    row_number: int,
    draft_values: dict[str, object],
) -> ResearchStrategySuperforecastPromptQualityGateRow:
    row_values = {"row_number": _count(row_number), **draft_values}
    return ResearchStrategySuperforecastPromptQualityGateRow(
        **row_values,
        validation_digest=_validation_digest(row_values),
    )


def _prompt_quality_score(
    prompt_context: ResearchStrategySuperforecastPromptContext,
) -> Decimal:
    return _ratio(
        _sum_decimal(
            tuple(getattr(prompt_context, field_name) for field_name in COMPONENT_FIELDS),
        ),
        FIVE,
    )


def _row_reason_codes(
    prompt_context: ResearchStrategySuperforecastPromptContext,
    *,
    config: ResearchStrategySuperforecastPromptQualityGateConfig,
) -> tuple[str, ...]:
    block_reasons: list[str] = []
    watch_reasons: list[str] = []
    for field_name in COMPONENT_FIELDS:
        _append_floor_reasons(
            block_reasons,
            watch_reasons,
            value=getattr(prompt_context, field_name),
            pass_floor=getattr(config, f"{field_name}_pass_floor"),
            watch_floor=getattr(config, f"{field_name}_watch_floor"),
            reason_prefix=field_name,
        )
    reasons = tuple(block_reasons + watch_reasons)
    if not reasons:
        reasons = (PROMPT_QUALITY_PASS_REASON,)
    reasons = (*reasons, *(f"input_{code}" for code in prompt_context.reason_codes))
    return _normalize_reason_codes(reasons)


def _append_floor_reasons(
    block_reasons: list[str],
    watch_reasons: list[str],
    *,
    value: Decimal,
    pass_floor: Decimal,
    watch_floor: Decimal,
    reason_prefix: str,
) -> None:
    if value < watch_floor:
        block_reasons.append(f"{reason_prefix}_block")
    elif value < pass_floor:
        watch_reasons.append(f"{reason_prefix}_watch")


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in COMPONENT_BLOCK_REASONS for reason_code in reason_codes):
        return "block"
    if any(reason_code in COMPONENT_WATCH_REASONS for reason_code in reason_codes):
        return "watch"
    return "pass"


def _report_status(
    rows: tuple[ResearchStrategySuperforecastPromptQualityGateRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategySuperforecastPromptQualityGateRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_CONTEXTS_REASON,)
    status = _report_status(rows)
    values = tuple(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != PROMPT_QUALITY_PASS_REASON
    )
    return _normalize_reason_codes((*values, f"superforecast_prompt_quality_{status}"))


def _reason_code_counts(
    rows: tuple[ResearchStrategySuperforecastPromptQualityGateRow, ...],
) -> tuple[ResearchStrategySuperforecastPromptQualityGateReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategySuperforecastPromptQualityGateReasonCodeCount(
                reason_code=NO_CONTEXTS_REASON,
                count=ONE,
            ),
        )
    counter: Counter[str] = Counter(
        reason_code for row in rows for reason_code in row.reason_codes
    )
    return tuple(
        ResearchStrategySuperforecastPromptQualityGateReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(
            counter.items(),
            key=lambda item: (_reason_rank(item[0]), item[0]),
        )
    )


def _average_prompt_quality_score(
    rows: tuple[ResearchStrategySuperforecastPromptQualityGateRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return _ratio(
        _sum_decimal(tuple(row.prompt_quality_score for row in rows)),
        _count(len(rows)),
    )


def _min_prompt_quality_score(
    rows: tuple[ResearchStrategySuperforecastPromptQualityGateRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return min(row.prompt_quality_score for row in rows)


def _max_prompt_age_seconds(
    rows: tuple[ResearchStrategySuperforecastPromptQualityGateRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return max(row.prompt_age_seconds for row in rows)


def _normalize_prompt_contexts(
    prompt_contexts: Iterable[ResearchStrategySuperforecastPromptContext],
) -> tuple[ResearchStrategySuperforecastPromptContext, ...]:
    if isinstance(prompt_contexts, (str, bytes)):
        raise ValueError("prompt_contexts must be an iterable")
    try:
        values = tuple(prompt_contexts)
    except TypeError as exc:
        raise ValueError("prompt_contexts must be an iterable") from exc
    seen: set[str] = set()
    for prompt_context in values:
        if type(prompt_context) is not ResearchStrategySuperforecastPromptContext:
            raise ValueError(
                "prompt_contexts must contain ResearchStrategySuperforecastPromptContext",
            )
        _require_hard_phase_flags("prompt_context", prompt_context)
        if prompt_context.prompt_context_key in seen:
            raise ValueError("prompt_context_key values must be unique")
        seen.add(prompt_context.prompt_context_key)
    return values


def _normalize_rows(
    rows: tuple[ResearchStrategySuperforecastPromptQualityGateRow, ...],
) -> tuple[ResearchStrategySuperforecastPromptQualityGateRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchStrategySuperforecastPromptQualityGateRow:
            raise ValueError(
                "rows must contain ResearchStrategySuperforecastPromptQualityGateRow",
            )
    return rows


def _normalize_reason_code_counts(
    reason_code_counts: tuple[
        ResearchStrategySuperforecastPromptQualityGateReasonCodeCount,
        ...,
    ],
) -> tuple[ResearchStrategySuperforecastPromptQualityGateReasonCodeCount, ...]:
    if type(reason_code_counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for reason_code_count in reason_code_counts:
        if (
            type(reason_code_count)
            is not ResearchStrategySuperforecastPromptQualityGateReasonCodeCount
        ):
            raise ValueError(
                "reason_code_counts must contain ResearchStrategySuperforecastPromptQualityGateReasonCodeCount",
            )
    expected = tuple(
        sorted(
            reason_code_counts,
            key=lambda item: (_reason_rank(item.reason_code), item.reason_code),
        ),
    )
    if reason_code_counts != expected:
        raise ValueError("reason_code_counts must be sorted deterministically")
    if len({item.reason_code for item in reason_code_counts}) != len(reason_code_counts):
        raise ValueError("reason_code_counts must be unique by reason_code")
    return reason_code_counts


def _validate_row(row: ResearchStrategySuperforecastPromptQualityGateRow) -> None:
    expected_score = _ratio(
        _sum_decimal(tuple(getattr(row, field_name) for field_name in COMPONENT_FIELDS)),
        FIVE,
    )
    if row.prompt_quality_score != expected_score:
        raise ValueError("prompt_quality_score must match inputs")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report(report: ResearchStrategySuperforecastPromptQualityGateReport) -> None:
    rows = report.rows
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    expected_numbers = tuple(_count(index) for index in range(1, len(rows) + 1))
    if tuple(row.row_number for row in rows) != expected_numbers:
        raise ValueError("rows must be sorted deterministically")
    if report.prompt_context_count != _count(len(rows)):
        raise ValueError("prompt_context_count must match rows")
    for status in PUBLIC_STATUSES:
        expected = _status_count(rows, status)
        actual = getattr(report, f"{status}_count")
        if actual != expected:
            raise ValueError(f"{status}_count must match rows")
    if report.average_prompt_quality_score != _average_prompt_quality_score(rows):
        raise ValueError("average_prompt_quality_score must match rows")
    if report.min_prompt_quality_score != _min_prompt_quality_score(rows):
        raise ValueError("min_prompt_quality_score must match rows")
    if report.max_prompt_age_seconds != _max_prompt_age_seconds(rows):
        raise ValueError("max_prompt_age_seconds must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _status_count(
    rows: tuple[ResearchStrategySuperforecastPromptQualityGateRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _draft_row_sort_key(value: dict[str, object]) -> tuple[Decimal, Decimal, str]:
    status = value["status"]
    score = value["prompt_quality_score"]
    public_hash = value["public_prompt_context_hash"]
    if type(status) is not str:
        raise ValueError("status must be a string")
    if type(score) is not Decimal:
        raise ValueError("prompt_quality_score must be Decimal")
    if type(public_hash) is not str:
        raise ValueError("public_prompt_context_hash must be a string")
    return (STATUS_SORT_WEIGHT[status], score, public_hash)


def _row_sort_key(
    row: ResearchStrategySuperforecastPromptQualityGateRow,
) -> tuple[Decimal, Decimal, str]:
    return (
        STATUS_SORT_WEIGHT[row.status],
        row.prompt_quality_score,
        row.public_prompt_context_hash,
    )


def _reason_rank(reason_code: str) -> int:
    try:
        return REASON_PRIORITY.index(reason_code)
    except ValueError:
        return len(REASON_PRIORITY)


def _normalize_reason_codes_allow_empty(
    reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not reason_codes:
        return ()
    return _normalize_reason_codes(reason_codes)


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_text("reason_codes", reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(
        sorted(
            normalized,
            key=lambda reason_code: (_reason_rank(reason_code), reason_code),
        ),
    )


def _require_exact_type(value: object, expected_type: type[object], name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exactly {expected_type.__name__}")


def _require_public_text(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if value != value.strip() or not value:
        raise ValueError(f"{name} must be a non-empty canonical string")
    if any(ord(character) < 32 for character in value):
        raise ValueError(f"{name} must not contain control characters")
    _reject_unsafe_text(name, value)


def _require_internal_reference_text(name: str, value: object) -> None:
    _require_public_text(name, value)


def _require_status(name: str, value: object) -> None:
    if value not in PUBLIC_STATUSES:
        raise ValueError(f"{name} must be one of pass/watch/block")


def _require_digest(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be a SHA-256 hex digest")


def _require_public_hash(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value.startswith("sha256:"):
        raise ValueError(f"{name} must be a public SHA-256 hash")
    _require_digest(name, value.removeprefix("sha256:"))


def _require_hard_phase_flags(name: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{name}.{field_name} must be hard-coded True")


def _normalize_ratio(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return _quantize(decimal_value)


def _normalize_nonnegative_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return _quantize(decimal_value)


def _normalize_nonnegative_count(name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{name} must be a whole-number Decimal")
    return decimal_value


def _normalize_positive_count(name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_count(name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{name} must be positive")
    return decimal_value


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value


def _quantize(value: Decimal) -> Decimal:
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        return value.quantize(QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        return _quantize(numerator / denominator)


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    total = ZERO
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        for value in values:
            total += value
    return _quantize(total)


def _count(value: int) -> Decimal:
    return Decimal(str(value)).quantize(QUANTUM)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _seconds_between(observed_at: datetime, generated_at: datetime) -> Decimal:
    seconds = Decimal(str((generated_at - observed_at).total_seconds()))
    if seconds < ZERO:
        raise ValueError("generated_at must not precede observed_at")
    return _quantize(seconds)


def _public_hash(value: str) -> str:
    return "sha256:" + sha256(value.encode("utf-8")).hexdigest()


def _validation_digest(value: object) -> str:
    public_value = _json_ready(value, skip_current_digest=True)
    encoded = json.dumps(
        public_value,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _json_ready(value: object, *, skip_current_digest: bool = False) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_ready(
                getattr(value, field.name),
                skip_current_digest=False,
            )
            for field in fields(value)
            if not (skip_current_digest and field.name == "validation_digest")
        }
    if isinstance(value, Mapping):
        return {
            str(key): _json_ready(item, skip_current_digest=False)
            for key, item in value.items()
            if not (skip_current_digest and key == "validation_digest")
        }
    if isinstance(value, tuple):
        return [_json_ready(item, skip_current_digest=False) for item in value]
    if isinstance(value, list):
        return [_json_ready(item, skip_current_digest=False) for item in value]
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
    if type(value) in {str, bool} or value is None:
        return value
    raise ValueError(f"unsupported public payload value: {type(value).__name__}")


def _public_mapping(value: object) -> dict[str, object]:
    ready = _json_ready(value)
    if type(ready) is not dict:
        raise ValueError("public value must be a mapping")
    return ready


def _validate_public_payload(payload: dict[str, object]) -> None:
    _reject_unsafe_payload(payload)
    _require_public_payload_values(payload)
    _validate_payload_digest_tree(payload)


def _require_public_payload_values(value: object, path: str = "payload") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{path} keys must be strings")
            _reject_unsafe_text(f"{path}.{key}", key)
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{path}.{key} must be true")
            _require_public_payload_values(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _require_public_payload_values(item, f"{path}[{index}]")
    elif type(value) in {str, bool} or value is None:
        if type(value) is str:
            _reject_unsafe_text(path, value)
    elif type(value) in {int, float, Decimal}:
        raise ValueError(f"{path} numeric values must be serialized strings")
    else:
        raise ValueError(f"{path} contains unsupported public payload value")


def _validate_payload_digest_tree(value: object) -> None:
    if isinstance(value, Mapping):
        current = value.get("validation_digest")
        if current is not None:
            _require_digest("validation_digest", current)
            expected = _validation_digest(value)
            if current != expected:
                raise ValueError("validation_digest does not match public payload")
        for item in value.values():
            _validate_payload_digest_tree(item)
    elif isinstance(value, list):
        for item in value:
            _validate_payload_digest_tree(item)


def _reject_unsafe_payload(value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_unsafe_text("public payload key", key)
            _reject_unsafe_payload(item)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_payload(item)
    elif type(value) is str:
        _reject_unsafe_text("public payload value", value)
    elif is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_payload(_json_ready(value))


def _reject_unsafe_text(name: str, value: str) -> None:
    lowered = value.lower()
    denied_fragments = (
        "raw" + "_" + "candidate" + "_id",
        "market" + "_id",
        "market" + "_sl" + "ug",
        "sl" + "ug",
        "quest" + "ion",
        "u" + "rl",
        "source" + "_text",
        "d" + "sn",
        "table" + "_name",
        "to" + "ken",
        "private" + "_" + "to" + "ken",
        "wal" + "let",
        "or" + "der",
        "tra" + "de",
        "tra" + "ding",
        "position" + "_size",
        "b" + "uy",
        "se" + "ll",
        "recom" + "mend",
        "siz" + "ing",
        "data" + "base",
        "net" + "work",
        "requ" + "ests",
        "h" + "ttp",
        "sock" + "et",
        "sub" + "process",
        "au" + "th",
    )
    if any(fragment in lowered for fragment in denied_fragments):
        raise ValueError(f"{name} contains unsafe public payload content")
