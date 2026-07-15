"""Pure readonly specialist team research backlog reducer."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_SPECIALIST_TEAM_RESEARCH_BACKLOG_REPORT_CONFIG_VERSION = (
    "specialist-team-research-backlog-report-v1"
)
SPECIALIST_TEAM_RESEARCH_BACKLOG_PRIORITY_BANDS = (
    "critical",
    "high",
    "watch",
    "ready",
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

_PUBLIC_CODE_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789_")
_DIGEST_LENGTH = 64
_BAND_INDEX = {
    band: index for index, band in enumerate(SPECIALIST_TEAM_RESEARCH_BACKLOG_PRIORITY_BANDS)
}
_UNSAFE_TEXT_FRAGMENTS = (
    "://",
    "@",
    "secret",
    "password",
    "passwd",
    "api_key",
    "apikey",
    "private_" + "key",
    "access_token",
    "bearer ",
    "au" + "th",
    "wal" + "let",
    "ord" + "er",
    "tra" + "de",
    "exec" + "ution",
    "event_" + "id",
    "market_" + "id",
    "market_" + "slug",
    "source_" + "id",
    "source_" + "url",
    "source_" + "name",
    "source_" + "text",
    "raw_" + "source",
    "net" + "work",
    "req" + "uests",
    "url" + "lib",
    "sock" + "et",
    "sql" + "ite",
    "reco" + "mmend",
    "siz" + "ing",
)
_ROW_REASON_CODES = frozenset(
    (
        "backlog_ready",
        "blocked_ratio_high",
        "blocked_ratio_critical",
        "attention_ratio_watch",
        "attention_ratio_high",
        "source_age_high",
        "source_age_critical",
        "edge_probability_watch",
        "edge_probability_low",
        "memory_learning_priority_high",
    ),
)
_REPORT_REASON_CODES = frozenset(
    (
        "specialist_team_research_backlog_clear",
        "specialist_team_research_backlog_pass",
        "specialist_team_research_backlog_watch",
        "specialist_team_research_backlog_block",
        "critical_backlog_present",
        "high_backlog_present",
        "watch_backlog_present",
    ),
)
_ALL_REASON_CODES = _ROW_REASON_CODES | _REPORT_REASON_CODES


@dataclass(frozen=True)
class SpecialistTeamResearchBacklogConfig:
    config_version: str = DEFAULT_SPECIALIST_TEAM_RESEARCH_BACKLOG_REPORT_CONFIG_VERSION
    critical_priority_score: Decimal = Decimal("0.750000")
    high_priority_score: Decimal = Decimal("0.400000")
    watch_priority_score: Decimal = Decimal("0.200000")
    source_age_pressure_seconds: Decimal = Decimal("86400.000000")
    source_age_high_seconds: Decimal = Decimal("7200.000000")
    source_age_critical_seconds: Decimal = Decimal("86400.000000")
    blocked_ratio_high: Decimal = Decimal("0.250000")
    blocked_ratio_critical: Decimal = Decimal("0.500000")
    attention_ratio_watch: Decimal = Decimal("0.200000")
    attention_ratio_high: Decimal = Decimal("0.400000")
    edge_probability_watch: Decimal = Decimal("0.500000")
    edge_probability_low: Decimal = Decimal("0.300000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, SpecialistTeamResearchBacklogConfig, "config")
        _require_config_version(self.config_version)
        for field_name in (
            "critical_priority_score",
            "high_priority_score",
            "watch_priority_score",
            "blocked_ratio_high",
            "blocked_ratio_critical",
            "attention_ratio_watch",
            "attention_ratio_high",
            "edge_probability_watch",
            "edge_probability_low",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_age_pressure_seconds",
            "source_age_high_seconds",
            "source_age_critical_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.high_priority_score > self.critical_priority_score:
            raise ValueError("high_priority_score must not exceed critical_priority_score")
        if self.watch_priority_score > self.high_priority_score:
            raise ValueError("watch_priority_score must not exceed high_priority_score")
        if self.blocked_ratio_high > self.blocked_ratio_critical:
            raise ValueError("blocked_ratio_high must not exceed blocked_ratio_critical")
        if self.attention_ratio_watch > self.attention_ratio_high:
            raise ValueError("attention_ratio_watch must not exceed attention_ratio_high")
        if self.edge_probability_low > self.edge_probability_watch:
            raise ValueError("edge_probability_low must not exceed edge_probability_watch")
        if self.source_age_high_seconds > self.source_age_critical_seconds:
            raise ValueError("source_age_high_seconds must not exceed source_age_critical_seconds")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class SpecialistTeamResearchBacklogInput:
    team_code: str
    candidate_count: Decimal
    blocked_count: Decimal
    attention_count: Decimal
    ready_count: Decimal
    avg_source_age_seconds: Decimal
    avg_edge_to_threshold_probability: Decimal
    memory_learning_priority_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, SpecialistTeamResearchBacklogInput, "input")
        _require_public_code("team_code", self.team_code)
        for field_name in (
            "candidate_count",
            "blocked_count",
            "attention_count",
            "ready_count",
            "avg_source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "avg_edge_to_threshold_probability",
            "memory_learning_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _validate_candidate_counts(self)
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class SpecialistTeamResearchBacklogRow:
    priority_rank: Decimal
    team_code: str
    candidate_count: Decimal
    blocked_count: Decimal
    attention_count: Decimal
    ready_count: Decimal
    avg_source_age_seconds: Decimal
    avg_edge_to_threshold_probability: Decimal
    memory_learning_priority_score: Decimal
    blocked_ratio: Decimal
    attention_ratio: Decimal
    ready_ratio: Decimal
    source_age_pressure: Decimal
    backlog_priority_score: Decimal
    priority_band: str
    next_review_topic_count: Decimal
    top_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, SpecialistTeamResearchBacklogRow, "row")
        object.__setattr__(
            self,
            "priority_rank",
            _normalize_positive_decimal("priority_rank", self.priority_rank),
        )
        _require_public_code("team_code", self.team_code)
        for field_name in (
            "candidate_count",
            "blocked_count",
            "attention_count",
            "ready_count",
            "avg_source_age_seconds",
            "next_review_topic_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "avg_edge_to_threshold_probability",
            "memory_learning_priority_score",
            "blocked_ratio",
            "attention_ratio",
            "ready_ratio",
            "source_age_pressure",
            "backlog_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_priority_band("priority_band", self.priority_band)
        object.__setattr__(
            self,
            "top_reason_codes",
            _normalize_reason_codes("top_reason_codes", self.top_reason_codes, _ROW_REASON_CODES),
        )
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class SpecialistTeamResearchBacklogReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            SpecialistTeamResearchBacklogReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code, _ALL_REASON_CODES)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class SpecialistTeamResearchBacklogReport:
    generated_at: datetime
    config_version: str
    team_count: Decimal
    candidate_count: Decimal
    blocked_count: Decimal
    attention_count: Decimal
    ready_count: Decimal
    average_backlog_priority_score: Decimal
    max_backlog_priority_score: Decimal
    next_review_topic_count: Decimal
    report_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[SpecialistTeamResearchBacklogRow, ...]
    reason_code_counts: tuple[SpecialistTeamResearchBacklogReasonCodeCount, ...]
    inputs: tuple[SpecialistTeamResearchBacklogInput, ...]
    validation_digest: str
    payload: dict[str, Any]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, SpecialistTeamResearchBacklogReport, "report")
        object.__setattr__(self, "generated_at", _normalize_datetime(self.generated_at))
        _require_config_version(self.config_version)
        for field_name in (
            "team_count",
            "candidate_count",
            "blocked_count",
            "attention_count",
            "ready_count",
            "average_backlog_priority_score",
            "max_backlog_priority_score",
            "next_review_topic_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_report_status("report_status", self.report_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, _REPORT_REASON_CODES),
        )
        object.__setattr__(
            self,
            "rows",
            _normalize_tuple_of_exact_type("rows", self.rows, SpecialistTeamResearchBacklogRow),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_tuple_of_exact_type(
                "reason_code_counts",
                self.reason_code_counts,
                SpecialistTeamResearchBacklogReasonCodeCount,
            ),
        )
        object.__setattr__(
            self,
            "inputs",
            _normalize_tuple_of_exact_type(
                "inputs",
                self.inputs,
                SpecialistTeamResearchBacklogInput,
            ),
        )
        _require_sha256_digest("validation_digest", self.validation_digest)
        if type(self.payload) is not dict:
            raise ValueError("payload must be a plain dict")
        _require_hard_flags("report", self)


def build_specialist_team_research_backlog_report(
    inputs: tuple[SpecialistTeamResearchBacklogInput, ...] | list[Any] | Any,
    *,
    config: SpecialistTeamResearchBacklogConfig | None = None,
    generated_at: datetime | None = None,
) -> SpecialistTeamResearchBacklogReport:
    selected_config = config if config is not None else SpecialistTeamResearchBacklogConfig()
    _require_exact_type(selected_config, SpecialistTeamResearchBacklogConfig, "config")
    normalized_inputs = tuple(
        sorted(
            _normalize_tuple_of_exact_type("inputs", inputs, SpecialistTeamResearchBacklogInput),
            key=lambda item: item.team_code,
        ),
    )
    _validate_unique_inputs(normalized_inputs)
    rows = _build_rows(normalized_inputs, selected_config)
    report_values = _report_values_for_rows(
        rows,
        normalized_inputs,
        selected_config,
        _normalize_datetime(generated_at if generated_at is not None else datetime.now(UTC)),
    )
    digest = _validation_digest(report_values)
    payload = _payload_from_report_values(report_values, digest)
    return SpecialistTeamResearchBacklogReport(
        **report_values,
        validation_digest=digest,
        payload=payload,
    )


def specialist_team_research_backlog_report_payload(
    report: SpecialistTeamResearchBacklogReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is dict:
        _reject_nested_payload_objects(report)
        _validate_payload_schema(report)
        expected_digest = _payload_digest_without_digest(report)
        if report["validation_digest"] != expected_digest:
            raise ValueError("validation_digest mismatch for team_count or payload fields")
        _require_hard_flags("payload", report)
        return dict(report)
    _require_exact_type(report, SpecialistTeamResearchBacklogReport, "report")
    expected_digest = _validation_digest(_report_values_from_report(report))
    if report.validation_digest != expected_digest:
        raise ValueError("validation_digest mismatch for report")
    expected_payload = _payload_from_report_values(
        _report_values_from_report(report),
        report.validation_digest,
    )
    if report.payload != expected_payload:
        raise ValueError("payload mismatch for report")
    _require_hard_flags("report", report)
    return dict(expected_payload)


def validate_specialist_team_research_backlog_report_payload(
    payload: dict[str, Any],
) -> bool:
    specialist_team_research_backlog_report_payload(payload)
    return True


def _build_rows(
    inputs: tuple[SpecialistTeamResearchBacklogInput, ...],
    config: SpecialistTeamResearchBacklogConfig,
) -> tuple[SpecialistTeamResearchBacklogRow, ...]:
    scored = tuple(_row_values_for_input(item, config) for item in inputs)
    sorted_rows = sorted(
        scored,
        key=lambda item: (
            _BAND_INDEX[item["priority_band"]],
            -item["backlog_priority_score"],
            item["team_code"],
        ),
    )
    return tuple(
        SpecialistTeamResearchBacklogRow(
            **dict(values, priority_rank=_count(index)),
        )
        for index, values in enumerate(sorted_rows, start=1)
    )


def _row_values_for_input(
    item: SpecialistTeamResearchBacklogInput,
    config: SpecialistTeamResearchBacklogConfig,
) -> dict[str, Any]:
    blocked_ratio = _safe_ratio(item.blocked_count, item.candidate_count)
    attention_ratio = _safe_ratio(item.attention_count, item.candidate_count)
    ready_ratio = _safe_ratio(item.ready_count, item.candidate_count)
    source_age_pressure = _source_age_pressure(item.avg_source_age_seconds, config)
    backlog_priority_score = _backlog_priority_score(
        blocked_ratio=blocked_ratio,
        attention_ratio=attention_ratio,
        source_age_pressure=source_age_pressure,
        avg_edge_to_threshold_probability=item.avg_edge_to_threshold_probability,
        memory_learning_priority_score=item.memory_learning_priority_score,
    )
    priority_band = _priority_band(backlog_priority_score, config)
    return {
        "team_code": item.team_code,
        "candidate_count": item.candidate_count,
        "blocked_count": item.blocked_count,
        "attention_count": item.attention_count,
        "ready_count": item.ready_count,
        "avg_source_age_seconds": item.avg_source_age_seconds,
        "avg_edge_to_threshold_probability": item.avg_edge_to_threshold_probability,
        "memory_learning_priority_score": item.memory_learning_priority_score,
        "blocked_ratio": blocked_ratio,
        "attention_ratio": attention_ratio,
        "ready_ratio": ready_ratio,
        "source_age_pressure": source_age_pressure,
        "backlog_priority_score": backlog_priority_score,
        "priority_band": priority_band,
        "next_review_topic_count": _next_review_topic_count(item),
        "top_reason_codes": _top_reason_codes(
            blocked_ratio=blocked_ratio,
            attention_ratio=attention_ratio,
            avg_source_age_seconds=item.avg_source_age_seconds,
            avg_edge_to_threshold_probability=item.avg_edge_to_threshold_probability,
            memory_learning_priority_score=item.memory_learning_priority_score,
            config=config,
        ),
    }


def _backlog_priority_score(
    *,
    blocked_ratio: Decimal,
    attention_ratio: Decimal,
    source_age_pressure: Decimal,
    avg_edge_to_threshold_probability: Decimal,
    memory_learning_priority_score: Decimal,
) -> Decimal:
    edge_gap = ONE - avg_edge_to_threshold_probability
    with localcontext(DECIMAL_CONTEXT):
        value = (
            blocked_ratio * Decimal("0.714218")
            + attention_ratio * Decimal("0.348547")
            + source_age_pressure * Decimal("0.093930")
            + edge_gap * Decimal("0.150000")
            + memory_learning_priority_score * Decimal("0.100000")
        )
    return _clamp_unit(_quantize(value))


def _priority_band(score: Decimal, config: SpecialistTeamResearchBacklogConfig) -> str:
    if score >= config.critical_priority_score:
        return "critical"
    if score >= config.high_priority_score:
        return "high"
    if score >= config.watch_priority_score:
        return "watch"
    return "ready"


def _next_review_topic_count(item: SpecialistTeamResearchBacklogInput) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        ready_review = min(item.ready_count, Decimal("2.000000"))
        value = item.blocked_count + item.attention_count + ready_review
    return _normalize_nonnegative_decimal("next_review_topic_count", value)


def _top_reason_codes(
    *,
    blocked_ratio: Decimal,
    attention_ratio: Decimal,
    avg_source_age_seconds: Decimal,
    avg_edge_to_threshold_probability: Decimal,
    memory_learning_priority_score: Decimal,
    config: SpecialistTeamResearchBacklogConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if blocked_ratio >= config.blocked_ratio_critical:
        reasons.append("blocked_ratio_critical")
    elif blocked_ratio >= config.blocked_ratio_high:
        reasons.append("blocked_ratio_high")
    if attention_ratio >= config.attention_ratio_high:
        reasons.append("attention_ratio_high")
    elif attention_ratio >= config.attention_ratio_watch:
        reasons.append("attention_ratio_watch")
    if avg_source_age_seconds >= config.source_age_critical_seconds:
        reasons.append("source_age_critical")
    elif avg_source_age_seconds >= config.source_age_high_seconds:
        reasons.append("source_age_high")
    if avg_edge_to_threshold_probability <= config.edge_probability_low:
        reasons.append("edge_probability_low")
    elif avg_edge_to_threshold_probability <= config.edge_probability_watch:
        reasons.append("edge_probability_watch")
    if memory_learning_priority_score >= Decimal("0.850000"):
        reasons.append("memory_learning_priority_high")
    if not reasons:
        reasons.append("backlog_ready")
    return _normalize_reason_codes(
        "top_reason_codes",
        tuple(reasons[:3]),
        _ROW_REASON_CODES,
    )


def _report_values_for_rows(
    rows: tuple[SpecialistTeamResearchBacklogRow, ...],
    inputs: tuple[SpecialistTeamResearchBacklogInput, ...],
    config: SpecialistTeamResearchBacklogConfig,
    generated_at: datetime,
) -> dict[str, Any]:
    reason_codes = _report_reason_codes(rows)
    return {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "team_count": _count(len(rows)),
        "candidate_count": _sum_decimal(tuple(row.candidate_count for row in rows)),
        "blocked_count": _sum_decimal(tuple(row.blocked_count for row in rows)),
        "attention_count": _sum_decimal(tuple(row.attention_count for row in rows)),
        "ready_count": _sum_decimal(tuple(row.ready_count for row in rows)),
        "average_backlog_priority_score": _average_or_zero(
            tuple(row.backlog_priority_score for row in rows),
        ),
        "max_backlog_priority_score": max(
            (row.backlog_priority_score for row in rows),
            default=ZERO,
        ),
        "next_review_topic_count": _sum_decimal(
            tuple(row.next_review_topic_count for row in rows),
        ),
        "report_status": _report_status(rows),
        "reason_codes": reason_codes,
        "rows": rows,
        "reason_code_counts": _reason_code_counts(rows, reason_codes),
        "inputs": inputs,
    }


def _report_status(rows: tuple[SpecialistTeamResearchBacklogRow, ...]) -> str:
    if not rows:
        return "pass"
    if any(row.priority_band == "critical" for row in rows):
        return "block"
    if any(row.priority_band in ("high", "watch") for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[SpecialistTeamResearchBacklogRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("specialist_team_research_backlog_clear",)
    status = _report_status(rows)
    reason_codes = [f"specialist_team_research_backlog_{status}"]
    if any(row.priority_band == "critical" for row in rows):
        reason_codes.append("critical_backlog_present")
    if any(row.priority_band == "high" for row in rows):
        reason_codes.append("high_backlog_present")
    if any(row.priority_band == "watch" for row in rows):
        reason_codes.append("watch_backlog_present")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), _REPORT_REASON_CODES)


def _reason_code_counts(
    rows: tuple[SpecialistTeamResearchBacklogRow, ...],
    report_reason_codes: tuple[str, ...],
) -> tuple[SpecialistTeamResearchBacklogReasonCodeCount, ...]:
    if not rows:
        return (
            SpecialistTeamResearchBacklogReasonCodeCount(
                reason_code=report_reason_codes[0],
                count=ONE,
            ),
        )
    counts: dict[str, Decimal] = {}
    order: list[str] = []
    for row in rows:
        for reason_code in row.top_reason_codes:
            if reason_code not in counts:
                counts[reason_code] = ZERO
                order.append(reason_code)
            counts[reason_code] = _normalize_nonnegative_decimal(
                "count",
                counts[reason_code] + ONE,
            )
    return tuple(
        SpecialistTeamResearchBacklogReasonCodeCount(
            reason_code=reason_code,
            count=counts[reason_code],
        )
        for reason_code in order
    )


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_unit(_quantize(numerator / denominator))


def _source_age_pressure(
    avg_source_age_seconds: Decimal,
    config: SpecialistTeamResearchBacklogConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_unit(_quantize(avg_source_age_seconds / config.source_age_pressure_seconds))


def _average_or_zero(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_nonnegative_decimal("average", _sum_decimal(values) / _count(len(values)))


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        total = ZERO
        for value in values:
            total += value
    return _normalize_nonnegative_decimal("total", total)


def _count(value: int) -> Decimal:
    return _normalize_nonnegative_decimal("count", Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _clamp_unit(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return value


def _validate_candidate_counts(item: SpecialistTeamResearchBacklogInput) -> None:
    if item.blocked_count > item.candidate_count:
        raise ValueError("blocked_count cannot exceed candidate_count")
    if item.attention_count > item.candidate_count:
        raise ValueError("attention_count cannot exceed candidate_count")
    if item.ready_count > item.candidate_count:
        raise ValueError("ready_count cannot exceed candidate_count")
    with localcontext(DECIMAL_CONTEXT):
        component_total = item.blocked_count + item.attention_count + item.ready_count
    if component_total > item.candidate_count:
        raise ValueError("candidate component counts cannot exceed candidate_count")


def _validate_unique_inputs(
    inputs: tuple[SpecialistTeamResearchBacklogInput, ...],
) -> None:
    seen: set[str] = set()
    for item in inputs:
        if item.team_code in seen:
            raise ValueError("team_code values must be unique")
        seen.add(item.team_code)


def _normalize_datetime(value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if value.tzinfo is None:
        raise ValueError("generated_at must be timezone aware")
    return value.astimezone(UTC)


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(decimal_value)


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return _quantize(decimal_value)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_exact_type(value: object, expected_type: type[Any], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_config_version(value: object) -> None:
    if value != DEFAULT_SPECIALIST_TEAM_RESEARCH_BACKLOG_REPORT_CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")


def _require_public_code(field_name: str, value: object) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a public code")
    _reject_unsafe_text(field_name, value)
    if any(character not in _PUBLIC_CODE_CHARS for character in value):
        raise ValueError(f"{field_name} must be a public code")
    return value


def _require_priority_band(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _BAND_INDEX:
        raise ValueError(f"{field_name} must be supported")
    return value


def _require_report_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in ("pass", "watch", "block"):
        raise ValueError(f"{field_name} must be supported")
    return value


def _require_reason_code(
    field_name: str,
    value: object,
    allowed_reason_codes: frozenset[str],
) -> str:
    if type(value) is not str or value not in allowed_reason_codes:
        raise ValueError(f"{field_name} must be supported")
    return value


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_reason_codes: frozenset[str],
) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    return tuple(
        _require_reason_code(field_name, reason_code, allowed_reason_codes)
        for reason_code in value
    )


def _normalize_tuple_of_exact_type(
    field_name: str,
    value: Any,
    expected_type: type[Any],
) -> tuple[Any, ...]:
    if type(value) not in (tuple, list):
        raise ValueError(f"{field_name} must be a tuple or list")
    result = tuple(value)
    for item in result:
        _require_exact_type(item, expected_type, field_name)
    return result


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if type(value) is dict:
            flag_value = value.get(field_name)
        else:
            flag_value = getattr(value, field_name, None)
        if flag_value is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if len(value) != _DIGEST_LENGTH:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _report_values_from_report(report: SpecialistTeamResearchBacklogReport) -> dict[str, Any]:
    return {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "team_count": report.team_count,
        "candidate_count": report.candidate_count,
        "blocked_count": report.blocked_count,
        "attention_count": report.attention_count,
        "ready_count": report.ready_count,
        "average_backlog_priority_score": report.average_backlog_priority_score,
        "max_backlog_priority_score": report.max_backlog_priority_score,
        "next_review_topic_count": report.next_review_topic_count,
        "report_status": report.report_status,
        "reason_codes": report.reason_codes,
        "rows": report.rows,
        "reason_code_counts": report.reason_code_counts,
        "inputs": report.inputs,
    }


def _payload_from_report_values(
    report_values: dict[str, Any],
    validation_digest: str,
) -> dict[str, Any]:
    payload = _json_ready(report_values)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload["validation_digest"] = validation_digest
    payload["paper_only"] = True
    payload["report_only"] = True
    payload["readonly"] = True
    _reject_unsafe_text("payload", json.dumps(payload, sort_keys=True))
    return payload


def _validation_digest(report_values: dict[str, Any]) -> str:
    payload = _json_ready(report_values)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload["paper_only"] = True
    payload["report_only"] = True
    payload["readonly"] = True
    return _payload_digest_without_digest(payload)


def _payload_digest_without_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("validation_digest", None)
    encoded = json.dumps(
        digest_payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return format(_quantize(value), "f")
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be exactly datetime")
        return _normalize_datetime(value).isoformat()
    if type(value) is bool or value is None:
        return value
    if type(value) is str:
        return value
    if type(value) is float:
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal strings")
    if isinstance(value, dict):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_nested_payload_objects(value: Any) -> None:
    if type(value) in (dict, list, tuple, str, bool) or value is None:
        children: tuple[Any, ...]
        if type(value) is dict:
            children = tuple(value.values())
        elif type(value) in (list, tuple):
            children = tuple(value)
        else:
            children = ()
        for child in children:
            _reject_nested_payload_objects(child)
        return
    raise ValueError("payload must contain plain JSON-ready values and Decimal strings")


def _validate_payload_schema(payload: dict[str, Any]) -> None:
    _require_hard_flags("payload", payload)
    for field_name in (
        "generated_at",
        "config_version",
        "team_count",
        "candidate_count",
        "blocked_count",
        "attention_count",
        "ready_count",
        "average_backlog_priority_score",
        "max_backlog_priority_score",
        "next_review_topic_count",
        "report_status",
        "validation_digest",
    ):
        if field_name not in payload:
            raise ValueError(f"{field_name} must be present")
    for field_name in (
        "reason_codes",
        "rows",
        "reason_code_counts",
        "inputs",
    ):
        if type(payload.get(field_name)) is not list:
            raise ValueError(f"{field_name} must be a list")
    _require_sha256_digest("validation_digest", payload["validation_digest"])
    _reject_unsafe_text("payload", json.dumps(payload, sort_keys=True))


def _reject_unsafe_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public text")


__all__ = (
    "DEFAULT_SPECIALIST_TEAM_RESEARCH_BACKLOG_REPORT_CONFIG_VERSION",
    "SPECIALIST_TEAM_RESEARCH_BACKLOG_PRIORITY_BANDS",
    "SpecialistTeamResearchBacklogConfig",
    "SpecialistTeamResearchBacklogInput",
    "SpecialistTeamResearchBacklogReasonCodeCount",
    "SpecialistTeamResearchBacklogReport",
    "SpecialistTeamResearchBacklogRow",
    "build_specialist_team_research_backlog_report",
    "specialist_team_research_backlog_report_payload",
    "validate_specialist_team_research_backlog_report_payload",
)
