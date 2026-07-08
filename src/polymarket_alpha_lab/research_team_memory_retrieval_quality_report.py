"""Pure report-only reducer for team memory retrieval quality."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
import json
from typing import Any, Iterable


DEFAULT_RESEARCH_TEAM_MEMORY_RETRIEVAL_QUALITY_REPORT_CONFIG_VERSION = (
    "research-team-memory-retrieval-quality-report-v0"
)
MEMORY_RETRIEVAL_QUALITY_STATUSES = ("pass", "watch", "block")
MEMORY_RETRIEVAL_QUALITY_REASON_CODES = (
    "no_memory_retrieval_quality_inputs",
    "memory_retrieval_conflicts_present",
    "memory_retrieval_insufficient",
    "memory_retrieval_low_relevance",
    "memory_retrieval_stale",
    "memory_retrieval_watch_age",
    "memory_retrieval_watch_sufficiency",
    "memory_retrieval_watch_relevance",
    "team_memory_retrieval_quality_block",
    "team_memory_retrieval_quality_watch",
    "team_memory_retrieval_quality_pass",
)

_DIGEST_FIELD = "derived_validation_digest"
_QUANTUM = Decimal("0.000001")
_COUNT_QUANTUM = Decimal("1")
_ZERO = Decimal("0.000000")
_ZERO_COUNT = Decimal("0")
_ONE = Decimal("1.000000")
_DECIMAL_CONTEXT = Context(prec=64)
_SECONDS_PER_DAY = Decimal("86400")
_MICROSECONDS_PER_SECOND = Decimal("1000000")
_STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
_ROW_REASON_PRIORITY = MEMORY_RETRIEVAL_QUALITY_REASON_CODES[1:]
_UNSAFE_PUBLIC_LABEL_FRAGMENTS = frozenset(
    (
        "candidate" "_" "id",
        "market" "_" "id",
        "market" "_" "slug",
        "ques" "tion",
        "source" "_" "url",
        "source" "_" "text",
        "dsn",
        "table" "_" "name",
        "private" "_" "token",
        "wal" "let",
        "acc" "ount",
        "or" "der",
        "private" "_" "key",
        "api" "_" "key",
        "sec" "ret",
        "cl" "ob",
        "au" "th",
        "net" "work",
        "reco" "mmend",
        "siz" "ing",
        "ad" "vice",
        "tr" "ade",
    ),
)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_MEMORY_RETRIEVAL_QUALITY_REPORT_CONFIG_VERSION",
    "MEMORY_RETRIEVAL_QUALITY_STATUSES",
    "MEMORY_RETRIEVAL_QUALITY_REASON_CODES",
    "ResearchTeamMemoryRetrievalQualityConfig",
    "ResearchTeamMemoryRetrievalQualityInput",
    "ResearchTeamMemoryRetrievalQualityReport",
    "ResearchTeamMemoryRetrievalQualityRow",
    "build_research_team_memory_retrieval_quality_report",
    "research_team_memory_retrieval_quality_report_payload",
)


@dataclass(frozen=True)
class ResearchTeamMemoryRetrievalQualityConfig:
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_MEMORY_RETRIEVAL_QUALITY_REPORT_CONFIG_VERSION
    )
    recent_memory_seconds: Decimal = Decimal("604800.000000")
    stale_memory_seconds: Decimal = Decimal("2592000.000000")
    relevance_pass_threshold: Decimal = Decimal("0.800000")
    relevance_watch_threshold: Decimal = Decimal("0.550000")
    sufficiency_pass_threshold: Decimal = Decimal("1.000000")
    sufficiency_watch_threshold: Decimal = Decimal("0.500000")
    quality_pass_threshold: Decimal = Decimal("0.800000")
    quality_watch_threshold: Decimal = Decimal("0.500000")
    recency_weight: Decimal = Decimal("0.250000")
    relevance_weight: Decimal = Decimal("0.250000")
    non_conflict_weight: Decimal = Decimal("0.250000")
    sufficiency_weight: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchTeamMemoryRetrievalQualityConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("config", self, ResearchTeamMemoryRetrievalQualityConfig)
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("recent_memory_seconds", "stale_memory_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.recent_memory_seconds <= _ZERO:
            raise ValueError("recent_memory_seconds must be positive")
        if self.stale_memory_seconds <= self.recent_memory_seconds:
            raise ValueError("stale_memory_seconds must exceed recent_memory_seconds")
        for field_name in (
            "relevance_pass_threshold",
            "relevance_watch_threshold",
            "sufficiency_pass_threshold",
            "sufficiency_watch_threshold",
            "quality_pass_threshold",
            "quality_watch_threshold",
            "recency_weight",
            "relevance_weight",
            "non_conflict_weight",
            "sufficiency_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.relevance_pass_threshold < self.relevance_watch_threshold:
            raise ValueError("relevance_pass_threshold must be at least watch threshold")
        if self.sufficiency_pass_threshold < self.sufficiency_watch_threshold:
            raise ValueError("sufficiency_pass_threshold must be at least watch threshold")
        if self.quality_pass_threshold < self.quality_watch_threshold:
            raise ValueError("quality_pass_threshold must be at least watch threshold")
        if _quantize(
            self.recency_weight
            + self.relevance_weight
            + self.non_conflict_weight
            + self.sufficiency_weight,
        ) != _ONE:
            raise ValueError("quality weights must sum to one")
        _require_hard_flags(self)
        _reject_unsafe_public_surface("config", self)


@dataclass(frozen=True)
class ResearchTeamMemoryRetrievalQualityInput:
    team_label: str
    retrieval_lane: str
    retrieved_memory_count: Decimal
    required_memory_count: Decimal
    latest_retrieved_memory_at: datetime
    semantic_relevance_score: Decimal
    conflict_count: Decimal
    redaction_confirmed: bool = True
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchTeamMemoryRetrievalQualityInput does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("retrieval_input", self, ResearchTeamMemoryRetrievalQualityInput)
        for field_name in ("team_label", "retrieval_lane"):
            _require_public_label(field_name, getattr(self, field_name))
        for field_name in (
            "retrieved_memory_count",
            "required_memory_count",
            "conflict_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        if self.required_memory_count <= _ZERO_COUNT:
            raise ValueError("required_memory_count must be positive")
        object.__setattr__(
            self,
            "latest_retrieved_memory_at",
            _as_utc("latest_retrieved_memory_at", self.latest_retrieved_memory_at),
        )
        object.__setattr__(
            self,
            "semantic_relevance_score",
            _normalize_ratio("semantic_relevance_score", self.semantic_relevance_score),
        )
        if self.redaction_confirmed is not True:
            raise ValueError("redaction_confirmed must be True")
        _require_hard_flags(self)
        _reject_unsafe_public_surface("retrieval_input", self)


@dataclass(frozen=True)
class ResearchTeamMemoryRetrievalQualityRow:
    team_label: str
    retrieval_lane: str
    retrieved_memory_count: Decimal
    required_memory_count: Decimal
    retrieval_coverage_ratio: Decimal
    memory_age_seconds: Decimal
    recency_score: Decimal
    semantic_relevance_score: Decimal
    conflict_count: Decimal
    non_conflict_score: Decimal
    sufficiency_score: Decimal
    decision_research_quality_score: Decimal
    row_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchTeamMemoryRetrievalQualityRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchTeamMemoryRetrievalQualityRow)
        for field_name in ("team_label", "retrieval_lane"):
            _require_public_label(field_name, getattr(self, field_name))
        for field_name in (
            "retrieved_memory_count",
            "required_memory_count",
            "conflict_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "retrieval_coverage_ratio",
            "recency_score",
            "semantic_relevance_score",
            "non_conflict_score",
            "sufficiency_score",
            "decision_research_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "memory_age_seconds",
            _normalize_nonnegative_decimal("memory_age_seconds", self.memory_age_seconds),
        )
        _require_status("row_status", self.row_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes_preserving_sequence(self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags(self)
        _reject_unsafe_public_surface("row", self)


@dataclass(frozen=True)
class ResearchTeamMemoryRetrievalQualityReport:
    generated_at: datetime
    config_version: str
    status: str
    input_count: Decimal
    row_count: Decimal
    team_count: Decimal
    lane_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    recent_count: Decimal
    relevant_count: Decimal
    non_conflicting_count: Decimal
    sufficient_count: Decimal
    average_decision_research_quality_score: Decimal
    rows: tuple[ResearchTeamMemoryRetrievalQualityRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchTeamMemoryRetrievalQualityReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchTeamMemoryRetrievalQualityReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "input_count",
            "row_count",
            "team_count",
            "lane_count",
            "pass_count",
            "watch_count",
            "block_count",
            "recent_count",
            "relevant_count",
            "non_conflicting_count",
            "sufficient_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_decision_research_quality_score",
            _normalize_ratio(
                "average_decision_research_quality_score",
                self.average_decision_research_quality_score,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes_preserving_sequence(self.reason_codes),
        )
        _validate_report_consistency(self)
        _require_hard_flags(self)
        _reject_unsafe_public_surface("report", self)
        _require_or_set_digest(self)

    @property
    def payload(self) -> dict[str, Any]:
        payload = _payload_value(self)
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        _reject_unsafe_public_surface("payload", payload)
        _require_hard_flags(_DictFlags(payload))
        _validate_payload_digest(payload)
        return payload


def build_research_team_memory_retrieval_quality_report(
    inputs: Iterable[ResearchTeamMemoryRetrievalQualityInput],
    *,
    generated_at: datetime,
    config: ResearchTeamMemoryRetrievalQualityConfig | None = None,
) -> ResearchTeamMemoryRetrievalQualityReport:
    if config is None:
        config = ResearchTeamMemoryRetrievalQualityConfig()
    _require_exact_type("config", config, ResearchTeamMemoryRetrievalQualityConfig)
    _require_hard_flags(config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized = _normalize_inputs(inputs)
    for value in normalized:
        if _seconds_between(value.latest_retrieved_memory_at, generated_at) < _ZERO:
            raise ValueError("generated_at must be at or after latest_retrieved_memory_at")
    rows = tuple(
        sorted(
            (_row_from_input(value, generated_at, config) for value in normalized),
            key=_row_sort_key,
        ),
    )
    return ResearchTeamMemoryRetrievalQualityReport(
        generated_at=generated_at,
        config_version=config.config_version,
        status=_report_status(rows),
        input_count=_decimal_count(len(normalized)),
        row_count=_decimal_count(len(rows)),
        team_count=_decimal_count(len({row.team_label for row in rows})),
        lane_count=_decimal_count(len({row.retrieval_lane for row in rows})),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        recent_count=_count_if(rows, lambda row: row.memory_age_seconds <= config.recent_memory_seconds),
        relevant_count=_count_if(
            rows,
            lambda row: row.semantic_relevance_score >= config.relevance_watch_threshold,
        ),
        non_conflicting_count=_count_if(rows, lambda row: row.conflict_count == _ZERO_COUNT),
        sufficient_count=_count_if(
            rows,
            lambda row: row.retrieval_coverage_ratio >= config.sufficiency_pass_threshold,
        ),
        average_decision_research_quality_score=_average_score(
            tuple(row.decision_research_quality_score for row in rows),
        ),
        rows=rows,
        reason_codes=_report_reason_codes(rows),
    )


def research_team_memory_retrieval_quality_report_payload(
    report: ResearchTeamMemoryRetrievalQualityReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchTeamMemoryRetrievalQualityReport:
        _require_hard_flags(report)
        _reject_unsafe_public_surface("report", report)
        return report.payload
    if type(report) is dict:
        _reject_unsafe_public_surface("payload", report)
        payload = _payload_value(report)
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        _require_hard_flags(_DictFlags(payload))
        _validate_payload_digest(payload)
        return payload
    raise ValueError(
        "report must be a ResearchTeamMemoryRetrievalQualityReport or payload",
    )


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _row_from_input(
    value: ResearchTeamMemoryRetrievalQualityInput,
    generated_at: datetime,
    config: ResearchTeamMemoryRetrievalQualityConfig,
) -> ResearchTeamMemoryRetrievalQualityRow:
    memory_age_seconds = _seconds_between(value.latest_retrieved_memory_at, generated_at)
    coverage_ratio = _bounded_ratio(value.retrieved_memory_count, value.required_memory_count)
    recency_score = _recency_score(memory_age_seconds, config)
    non_conflict_score = _ZERO if value.conflict_count > _ZERO_COUNT else _ONE
    sufficiency_score = coverage_ratio
    quality_score = _quality_score(
        recency_score=recency_score,
        relevance_score=value.semantic_relevance_score,
        non_conflict_score=non_conflict_score,
        sufficiency_score=sufficiency_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        memory_age_seconds=memory_age_seconds,
        relevance_score=value.semantic_relevance_score,
        conflict_count=value.conflict_count,
        sufficiency_score=sufficiency_score,
        quality_score=quality_score,
        config=config,
    )
    return ResearchTeamMemoryRetrievalQualityRow(
        team_label=value.team_label,
        retrieval_lane=value.retrieval_lane,
        retrieved_memory_count=value.retrieved_memory_count,
        required_memory_count=value.required_memory_count,
        retrieval_coverage_ratio=coverage_ratio,
        memory_age_seconds=memory_age_seconds,
        recency_score=recency_score,
        semantic_relevance_score=value.semantic_relevance_score,
        conflict_count=value.conflict_count,
        non_conflict_score=non_conflict_score,
        sufficiency_score=sufficiency_score,
        decision_research_quality_score=quality_score,
        row_status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _recency_score(
    memory_age_seconds: Decimal,
    config: ResearchTeamMemoryRetrievalQualityConfig,
) -> Decimal:
    if memory_age_seconds <= config.recent_memory_seconds:
        return _ONE
    if memory_age_seconds >= config.stale_memory_seconds:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(_ONE - (memory_age_seconds / config.stale_memory_seconds))


def _quality_score(
    *,
    recency_score: Decimal,
    relevance_score: Decimal,
    non_conflict_score: Decimal,
    sufficiency_score: Decimal,
    config: ResearchTeamMemoryRetrievalQualityConfig,
) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(
            (recency_score * config.recency_weight)
            + (relevance_score * config.relevance_weight)
            + (non_conflict_score * config.non_conflict_weight)
            + (sufficiency_score * config.sufficiency_weight),
        )


def _row_reason_codes(
    *,
    memory_age_seconds: Decimal,
    relevance_score: Decimal,
    conflict_count: Decimal,
    sufficiency_score: Decimal,
    quality_score: Decimal,
    config: ResearchTeamMemoryRetrievalQualityConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if conflict_count > _ZERO_COUNT:
        reasons.append("memory_retrieval_conflicts_present")
    if sufficiency_score < config.sufficiency_watch_threshold:
        reasons.append("memory_retrieval_insufficient")
    elif sufficiency_score < config.sufficiency_pass_threshold:
        reasons.append("memory_retrieval_watch_sufficiency")
    if relevance_score < config.relevance_watch_threshold:
        reasons.append("memory_retrieval_low_relevance")
    elif relevance_score < config.relevance_pass_threshold:
        reasons.append("memory_retrieval_watch_relevance")
    if memory_age_seconds >= config.stale_memory_seconds:
        reasons.append("memory_retrieval_stale")
    elif memory_age_seconds > config.recent_memory_seconds:
        reasons.append("memory_retrieval_watch_age")
    if conflict_count > _ZERO_COUNT or quality_score < config.quality_watch_threshold:
        reasons.append("team_memory_retrieval_quality_block")
    elif quality_score < config.quality_pass_threshold:
        reasons.append("team_memory_retrieval_quality_watch")
    else:
        reasons.append("team_memory_retrieval_quality_pass")
    return tuple(reason for reason in _ROW_REASON_PRIORITY if reason in reasons)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if "team_memory_retrieval_quality_block" in reason_codes:
        return "block"
    if "team_memory_retrieval_quality_watch" in reason_codes:
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchTeamMemoryRetrievalQualityRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.row_status == "block" for row in rows):
        return "block"
    if any(row.row_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTeamMemoryRetrievalQualityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_memory_retrieval_quality_inputs",)
    present = frozenset(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != "team_memory_retrieval_quality_pass"
    )
    if not present:
        return ("team_memory_retrieval_quality_pass",)
    return tuple(reason_code for reason_code in _ROW_REASON_PRIORITY if reason_code in present)


def _normalize_inputs(
    values: Iterable[ResearchTeamMemoryRetrievalQualityInput],
) -> tuple[ResearchTeamMemoryRetrievalQualityInput, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen_keys: set[tuple[str, str]] = set()
    for value in normalized:
        _require_exact_type("retrieval_input", value, ResearchTeamMemoryRetrievalQualityInput)
        _require_hard_flags(value)
        _reject_unsafe_public_surface("retrieval_input", value)
        key = (value.team_label, value.retrieval_lane)
        if key in seen_keys:
            raise ValueError("inputs must use unique team and retrieval lane labels")
        seen_keys.add(key)
    return normalized


def _normalize_rows(
    values: Iterable[ResearchTeamMemoryRetrievalQualityRow],
) -> tuple[ResearchTeamMemoryRetrievalQualityRow, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("rows must contain ResearchTeamMemoryRetrievalQualityRow values")
    try:
        rows = tuple(values)
    except TypeError as exc:
        raise ValueError(
            "rows must contain ResearchTeamMemoryRetrievalQualityRow values",
        ) from exc
    for row in rows:
        _require_exact_type("row", row, ResearchTeamMemoryRetrievalQualityRow)
        _require_hard_flags(row)
        _reject_unsafe_public_surface("row", row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sort")
    if len(set((row.team_label, row.retrieval_lane) for row in rows)) != len(rows):
        raise ValueError("rows must be unique")
    return rows


def _validate_row_consistency(row: ResearchTeamMemoryRetrievalQualityRow) -> None:
    if row.required_memory_count <= _ZERO_COUNT:
        raise ValueError("required_memory_count must be positive")
    if row.retrieval_coverage_ratio != _bounded_ratio(
        row.retrieved_memory_count,
        row.required_memory_count,
    ):
        raise ValueError("retrieval_coverage_ratio must match counts")
    expected_non_conflict = _ZERO if row.conflict_count > _ZERO_COUNT else _ONE
    if row.non_conflict_score != expected_non_conflict:
        raise ValueError("non_conflict_score must match conflict_count")
    if row.sufficiency_score != row.retrieval_coverage_ratio:
        raise ValueError("sufficiency_score must match retrieval_coverage_ratio")
    if row.row_status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("row_status must match reason_codes")


def _validate_report_consistency(
    report: ResearchTeamMemoryRetrievalQualityReport,
) -> None:
    if report.input_count != report.row_count:
        raise ValueError("input_count must match row_count")
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.team_count != _decimal_count(len({row.team_label for row in report.rows})):
        raise ValueError("team_count must match rows")
    if report.lane_count != _decimal_count(len({row.retrieval_lane for row in report.rows})):
        raise ValueError("lane_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted")
    if report.average_decision_research_quality_score != _average_score(
        tuple(row.decision_research_quality_score for row in report.rows),
    ):
        raise ValueError("average_decision_research_quality_score must match rows")


def _row_sort_key(
    row: ResearchTeamMemoryRetrievalQualityRow,
) -> tuple[int, Decimal, Decimal, Decimal, str, str]:
    return (
        _STATUS_RANK[row.row_status],
        row.decision_research_quality_score,
        row.semantic_relevance_score,
        -row.memory_age_seconds,
        row.team_label,
        row.retrieval_lane,
    )


def _status_count(
    rows: tuple[ResearchTeamMemoryRetrievalQualityRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.row_status == status))


def _count_if(
    rows: tuple[ResearchTeamMemoryRetrievalQualityRow, ...],
    predicate: Any,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if predicate(row)))


def _average_score(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(sum(values, _ZERO) / _decimal_count(len(values)))


def _bounded_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO_COUNT:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        ratio = _quantize(numerator / denominator)
    if ratio > _ONE:
        return _ONE
    return ratio


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    whole_seconds = Decimal(delta.days) * _SECONDS_PER_DAY + Decimal(delta.seconds)
    microseconds = Decimal(delta.microseconds) / _MICROSECONDS_PER_SECOND
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(whole_seconds + microseconds)


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(_COUNT_QUANTUM)


def _normalize_reason_codes_preserving_sequence(value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        normalized = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    if not normalized:
        raise ValueError("reason_codes must contain at least one value")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must not contain duplicates")
    for reason_code in normalized:
        _require_canonical_string("reason_codes", reason_code)
        if reason_code not in MEMORY_RETRIEVAL_QUALITY_REASON_CODES:
            raise ValueError("reason_codes contains an unsupported value")
    return normalized


def _require_public_label(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_LABEL_FRAGMENTS):
        raise ValueError(f"{field_name} must be public-safe")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in MEMORY_RETRIEVAL_QUALITY_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _normalize_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal_with_quantum(field_name, value, _COUNT_QUANTUM)
    if normalized < _ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != value:
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > _ONE:
        raise ValueError(f"{field_name} must be at most one")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal_with_quantum(field_name, value, _QUANTUM)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal_with_quantum(
    field_name: str,
    value: object,
    quantum: Decimal,
) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(_DECIMAL_CONTEXT):
        normalized = value.quantize(quantum)
    if normalized != value:
        if quantum == _COUNT_QUANTUM:
            raise ValueError(f"{field_name} must be a whole Decimal")
        raise ValueError(f"{field_name} must be quantized to 0.000001")
    return normalized


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(label: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _reject_unsafe_public_surface(label: str, value: object) -> None:
    for item in _surface_items(value):
        lowered = item.lower()
        if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_LABEL_FRAGMENTS):
            raise ValueError(f"unsafe public-safe label in {label}")


def _surface_items(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        items: list[str] = []
        for field in fields(value):
            items.append(field.name)
            items.extend(_surface_items(getattr(value, field.name)))
        return tuple(items)
    if isinstance(value, dict):
        items = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            items.append(key)
            items.extend(_surface_items(item))
        return tuple(items)
    if isinstance(value, (list, tuple)):
        items = []
        for item in value:
            items.extend(_surface_items(item))
        return tuple(items)
    if type(value) is str:
        return (value,)
    return ()


def _require_or_set_digest(value: object) -> None:
    current = getattr(value, _DIGEST_FIELD)
    if type(current) is not str:
        raise ValueError("derived_validation_digest must be a string")
    expected = _derived_digest(value)
    if current == "":
        object.__setattr__(value, _DIGEST_FIELD, expected)
        return
    if current != expected or not _is_sha256_hex(current):
        raise ValueError("derived_validation_digest does not match derived payload")


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    current = payload.get(_DIGEST_FIELD)
    if type(current) is not str:
        raise ValueError("derived_validation_digest must be present")
    if current != _derived_digest(payload) or not _is_sha256_hex(current):
        raise ValueError("derived_validation_digest does not match derived payload")


def _derived_digest(value: object) -> str:
    canonical = _canonical_digest_value(value)
    encoded = json.dumps(canonical, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return sha256(encoded).hexdigest()


def _is_sha256_hex(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def _canonical_digest_value(value: object) -> object:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _canonical_digest_value(getattr(value, field.name))
            for field in fields(value)
            if field.name != _DIGEST_FIELD
        }
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("digest Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) in (str, bool):
        return value
    if isinstance(value, tuple):
        return [_canonical_digest_value(item) for item in value]
    if isinstance(value, list):
        return [_canonical_digest_value(item) for item in value]
    if isinstance(value, dict):
        result: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            if key != _DIGEST_FIELD:
                result[key] = _canonical_digest_value(item)
        return result
    raise ValueError("unsupported digest value")


def _payload_value(value: object) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("public payload Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) in (str, bool):
        return value
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        result: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            result[key] = _payload_value(item)
        return result
    raise ValueError("unsupported payload value")
