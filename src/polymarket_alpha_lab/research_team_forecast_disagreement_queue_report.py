"""Pure report-only reducer for aggregate specialist forecast disagreement queues."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
import json
from typing import Any, Iterable, Sequence


DEFAULT_RESEARCH_TEAM_FORECAST_DISAGREEMENT_QUEUE_REPORT_CONFIG_VERSION = (
    "research-team-forecast-disagreement-queue-report-v0"
)
DISAGREEMENT_QUEUE_STATUSES = ("pass", "watch", "block")
REASON_CODES = (
    "no_disagreement_aggregates_supplied",
    "disagreement_severity_block",
    "memory_refresh_stale",
    "source_coverage_block",
    "review_capacity_block",
    "escalation_urgency_block",
    "disagreement_severity_watch",
    "memory_refresh_watch",
    "source_coverage_watch",
    "review_capacity_watch",
    "escalation_urgency_watch",
    "forecast_disagreement_queue_clear",
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
_ROW_REASON_PRIORITY = REASON_CODES[1:]
_UNSAFE_PUBLIC_LABEL_FRAGMENTS = frozenset(
    (
        "market" "_slug",
        "ques" "tion",
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
        "ad" "vice",
        "tr" "ade",
    ),
)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_FORECAST_DISAGREEMENT_QUEUE_REPORT_CONFIG_VERSION",
    "DISAGREEMENT_QUEUE_STATUSES",
    "REASON_CODES",
    "ResearchTeamForecastDisagreementAggregate",
    "ResearchTeamForecastDisagreementQueueConfig",
    "ResearchTeamForecastDisagreementQueueReport",
    "ResearchTeamForecastDisagreementQueueRow",
    "build_research_team_forecast_disagreement_queue_report",
    "research_team_forecast_disagreement_queue_report_payload",
)


@dataclass(frozen=True)
class ResearchTeamForecastDisagreementQueueConfig:
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_FORECAST_DISAGREEMENT_QUEUE_REPORT_CONFIG_VERSION
    )
    disagreement_watch_threshold: Decimal = Decimal("0.250000")
    disagreement_block_threshold: Decimal = Decimal("0.600000")
    memory_watch_seconds: Decimal = Decimal("43200.000000")
    memory_block_seconds: Decimal = Decimal("86400.000000")
    source_coverage_watch_threshold: Decimal = Decimal("1.000000")
    source_coverage_block_threshold: Decimal = Decimal("0.500000")
    review_capacity_watch_threshold: Decimal = Decimal("1.000000")
    review_capacity_block_threshold: Decimal = Decimal("0.500000")
    escalation_watch_threshold: Decimal = Decimal("0.500000")
    escalation_block_threshold: Decimal = Decimal("0.850000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchTeamForecastDisagreementQueueConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            ResearchTeamForecastDisagreementQueueConfig,
        )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "disagreement_watch_threshold",
            "disagreement_block_threshold",
            "source_coverage_watch_threshold",
            "source_coverage_block_threshold",
            "review_capacity_watch_threshold",
            "review_capacity_block_threshold",
            "escalation_watch_threshold",
            "escalation_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("memory_watch_seconds", "memory_block_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.disagreement_block_threshold < self.disagreement_watch_threshold:
            raise ValueError("disagreement_block_threshold must be at least watch threshold")
        if self.memory_block_seconds < self.memory_watch_seconds:
            raise ValueError("memory_block_seconds must be at least watch threshold")
        if self.source_coverage_block_threshold > self.source_coverage_watch_threshold:
            raise ValueError("source coverage block threshold must be at most watch threshold")
        if self.review_capacity_block_threshold > self.review_capacity_watch_threshold:
            raise ValueError("review capacity block threshold must be at most watch threshold")
        if self.escalation_block_threshold < self.escalation_watch_threshold:
            raise ValueError("escalation_block_threshold must be at least watch threshold")
        _require_hard_flags(self)
        _reject_unsafe_public_surface("config", self)


@dataclass(frozen=True)
class ResearchTeamForecastDisagreementAggregate:
    team_label: str
    queue_label: str
    specialist_count: Decimal
    forecast_count: Decimal
    mean_forecast_probability: Decimal
    median_forecast_probability: Decimal
    high_forecast_probability: Decimal
    low_forecast_probability: Decimal
    latest_memory_refresh_at: datetime
    covered_source_count: Decimal
    required_source_count: Decimal
    reviewers_available_count: Decimal
    review_items_waiting_count: Decimal
    escalation_urgency_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchTeamForecastDisagreementAggregate does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "aggregate",
            self,
            ResearchTeamForecastDisagreementAggregate,
        )
        for field_name in ("team_label", "queue_label"):
            _require_public_label(field_name, getattr(self, field_name))
        for field_name in (
            "specialist_count",
            "forecast_count",
            "covered_source_count",
            "required_source_count",
            "reviewers_available_count",
            "review_items_waiting_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_forecast_probability",
            "median_forecast_probability",
            "high_forecast_probability",
            "low_forecast_probability",
            "escalation_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_memory_refresh_at",
            _as_utc("latest_memory_refresh_at", self.latest_memory_refresh_at),
        )
        _validate_aggregate_consistency(self)
        _require_hard_flags(self)
        _reject_unsafe_public_surface("aggregate", self)


@dataclass(frozen=True)
class ResearchTeamForecastDisagreementQueueRow:
    team_label: str
    queue_label: str
    specialist_count: Decimal
    forecast_count: Decimal
    disagreement_severity: Decimal
    memory_age_seconds: Decimal
    source_coverage_ratio: Decimal
    review_capacity_ratio: Decimal
    escalation_urgency_score: Decimal
    queue_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchTeamForecastDisagreementQueueRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchTeamForecastDisagreementQueueRow)
        for field_name in ("team_label", "queue_label"):
            _require_public_label(field_name, getattr(self, field_name))
        for field_name in ("specialist_count", "forecast_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "memory_age_seconds",
            _normalize_nonnegative_decimal("memory_age_seconds", self.memory_age_seconds),
        )
        for field_name in (
            "disagreement_severity",
            "source_coverage_ratio",
            "review_capacity_ratio",
            "escalation_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("queue_status", self.queue_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes_preserving_sequence(self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags(self)
        _reject_unsafe_public_surface("row", self)


@dataclass(frozen=True)
class ResearchTeamForecastDisagreementQueueReport:
    generated_at: datetime
    config_version: str
    queue_status: str
    aggregate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_disagreement_severity: Decimal | None
    max_memory_age_seconds: Decimal | None
    min_source_coverage_ratio: Decimal | None
    min_review_capacity_ratio: Decimal | None
    max_escalation_urgency_score: Decimal | None
    rows: tuple[ResearchTeamForecastDisagreementQueueRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchTeamForecastDisagreementQueueReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchTeamForecastDisagreementQueueReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("queue_status", self.queue_status)
        for field_name in ("aggregate_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_disagreement_severity",
            "min_source_coverage_ratio",
            "min_review_capacity_ratio",
            "max_escalation_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_memory_age_seconds",
            _normalize_optional_nonnegative_decimal(
                "max_memory_age_seconds",
                self.max_memory_age_seconds,
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
        return payload


def build_research_team_forecast_disagreement_queue_report(
    aggregates: Sequence[ResearchTeamForecastDisagreementAggregate],
    *,
    generated_at: datetime,
    config: ResearchTeamForecastDisagreementQueueConfig | None = None,
) -> ResearchTeamForecastDisagreementQueueReport:
    if config is None:
        config = ResearchTeamForecastDisagreementQueueConfig()
    _require_exact_type("config", config, ResearchTeamForecastDisagreementQueueConfig)
    generated_at = _as_utc("generated_at", generated_at)
    normalized = _normalize_aggregates(aggregates)
    for aggregate in normalized:
        if _seconds_between(aggregate.latest_memory_refresh_at, generated_at) < _ZERO:
            raise ValueError("generated_at must be at or after latest_memory_refresh_at")
    rows = tuple(
        sorted(
            (_row_from_aggregate(aggregate, generated_at, config) for aggregate in normalized),
            key=_row_sort_key,
        ),
    )
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "queue_status": _report_status(rows),
        "aggregate_count": _decimal_count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "max_disagreement_severity": _max_or_none(
            tuple(row.disagreement_severity for row in rows),
        ),
        "max_memory_age_seconds": _max_or_none(
            tuple(row.memory_age_seconds for row in rows),
        ),
        "min_source_coverage_ratio": _min_or_none(
            tuple(row.source_coverage_ratio for row in rows),
        ),
        "min_review_capacity_ratio": _min_or_none(
            tuple(row.review_capacity_ratio for row in rows),
        ),
        "max_escalation_urgency_score": _max_or_none(
            tuple(row.escalation_urgency_score for row in rows),
        ),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchTeamForecastDisagreementQueueReport(**values)


def research_team_forecast_disagreement_queue_report_payload(
    report: ResearchTeamForecastDisagreementQueueReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchTeamForecastDisagreementQueueReport:
        _require_hard_flags(report)
        _reject_unsafe_public_surface("report", report)
        return report.payload
    if type(report) is dict:
        _reject_unsafe_public_surface("payload", report)
        payload = _payload_value(report)
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        _require_hard_flags(_DictFlags(payload))
        return payload
    raise ValueError(
        "report must be a ResearchTeamForecastDisagreementQueueReport or payload",
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


def _row_from_aggregate(
    aggregate: ResearchTeamForecastDisagreementAggregate,
    generated_at: datetime,
    config: ResearchTeamForecastDisagreementQueueConfig,
) -> ResearchTeamForecastDisagreementQueueRow:
    disagreement_severity = _quantize(
        aggregate.high_forecast_probability - aggregate.low_forecast_probability,
    )
    memory_age_seconds = _seconds_between(aggregate.latest_memory_refresh_at, generated_at)
    source_coverage_ratio = _bounded_ratio(
        aggregate.covered_source_count,
        aggregate.required_source_count,
    )
    review_capacity_ratio = _review_capacity_ratio(
        aggregate.reviewers_available_count,
        aggregate.review_items_waiting_count,
    )
    reason_codes = _reason_codes_for_metrics(
        disagreement_severity=disagreement_severity,
        memory_age_seconds=memory_age_seconds,
        source_coverage_ratio=source_coverage_ratio,
        review_capacity_ratio=review_capacity_ratio,
        escalation_urgency_score=aggregate.escalation_urgency_score,
        config=config,
    )
    return ResearchTeamForecastDisagreementQueueRow(
        team_label=aggregate.team_label,
        queue_label=aggregate.queue_label,
        specialist_count=aggregate.specialist_count,
        forecast_count=aggregate.forecast_count,
        disagreement_severity=disagreement_severity,
        memory_age_seconds=memory_age_seconds,
        source_coverage_ratio=source_coverage_ratio,
        review_capacity_ratio=review_capacity_ratio,
        escalation_urgency_score=aggregate.escalation_urgency_score,
        queue_status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _reason_codes_for_metrics(
    *,
    disagreement_severity: Decimal,
    memory_age_seconds: Decimal,
    source_coverage_ratio: Decimal,
    review_capacity_ratio: Decimal,
    escalation_urgency_score: Decimal,
    config: ResearchTeamForecastDisagreementQueueConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if disagreement_severity >= config.disagreement_block_threshold:
        reasons.append("disagreement_severity_block")
    elif disagreement_severity >= config.disagreement_watch_threshold:
        reasons.append("disagreement_severity_watch")
    if memory_age_seconds >= config.memory_block_seconds:
        reasons.append("memory_refresh_stale")
    elif memory_age_seconds >= config.memory_watch_seconds:
        reasons.append("memory_refresh_watch")
    if source_coverage_ratio < config.source_coverage_block_threshold:
        reasons.append("source_coverage_block")
    elif source_coverage_ratio < config.source_coverage_watch_threshold:
        reasons.append("source_coverage_watch")
    if review_capacity_ratio < config.review_capacity_block_threshold:
        reasons.append("review_capacity_block")
    elif review_capacity_ratio < config.review_capacity_watch_threshold:
        reasons.append("review_capacity_watch")
    if escalation_urgency_score >= config.escalation_block_threshold:
        reasons.append("escalation_urgency_block")
    elif escalation_urgency_score >= config.escalation_watch_threshold:
        reasons.append("escalation_urgency_watch")
    if not reasons:
        return ("forecast_disagreement_queue_clear",)
    return tuple(reason for reason in _ROW_REASON_PRIORITY if reason in reasons)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(
        reason_code.endswith("_block") or reason_code == "memory_refresh_stale"
        for reason_code in reason_codes
    ):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchTeamForecastDisagreementQueueRow, ...]) -> str:
    if any(row.queue_status == "block" for row in rows):
        return "block"
    if any(row.queue_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTeamForecastDisagreementQueueRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_disagreement_aggregates_supplied",)
    present = frozenset(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != "forecast_disagreement_queue_clear"
    )
    if not present:
        return ("forecast_disagreement_queue_clear",)
    return tuple(reason_code for reason_code in _ROW_REASON_PRIORITY if reason_code in present)


def _normalize_aggregates(
    values: Iterable[ResearchTeamForecastDisagreementAggregate],
) -> tuple[ResearchTeamForecastDisagreementAggregate, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("aggregates must be an iterable")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError("aggregates must be an iterable") from exc
    seen_keys: set[tuple[str, str]] = set()
    for value in normalized:
        _require_exact_type("aggregate", value, ResearchTeamForecastDisagreementAggregate)
        _require_hard_flags(value)
        _reject_unsafe_public_surface("aggregate", value)
        key = (value.team_label, value.queue_label)
        if key in seen_keys:
            raise ValueError("aggregates must use unique team and queue labels")
        seen_keys.add(key)
    return normalized


def _normalize_rows(
    values: Iterable[ResearchTeamForecastDisagreementQueueRow],
) -> tuple[ResearchTeamForecastDisagreementQueueRow, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("rows must contain ResearchTeamForecastDisagreementQueueRow values")
    try:
        rows = tuple(values)
    except TypeError as exc:
        raise ValueError(
            "rows must contain ResearchTeamForecastDisagreementQueueRow values",
        ) from exc
    for row in rows:
        _require_exact_type("row", row, ResearchTeamForecastDisagreementQueueRow)
        _require_hard_flags(row)
        _reject_unsafe_public_surface("row", row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sort")
    if len(set((row.team_label, row.queue_label) for row in rows)) != len(rows):
        raise ValueError("rows must be unique")
    return rows


def _validate_aggregate_consistency(
    aggregate: ResearchTeamForecastDisagreementAggregate,
) -> None:
    if aggregate.specialist_count <= _ZERO_COUNT:
        raise ValueError("specialist_count must be positive")
    if aggregate.forecast_count <= _ZERO_COUNT:
        raise ValueError("forecast_count must be positive")
    if aggregate.required_source_count <= _ZERO_COUNT:
        raise ValueError("required_source_count must be positive")
    if aggregate.covered_source_count > aggregate.required_source_count:
        raise ValueError("covered_source_count must be at most required_source_count")
    if aggregate.low_forecast_probability > aggregate.high_forecast_probability:
        raise ValueError("low_forecast_probability must be at most high_forecast_probability")
    if not (
        aggregate.low_forecast_probability
        <= aggregate.mean_forecast_probability
        <= aggregate.high_forecast_probability
    ):
        raise ValueError("mean_forecast_probability must be within aggregate bounds")
    if not (
        aggregate.low_forecast_probability
        <= aggregate.median_forecast_probability
        <= aggregate.high_forecast_probability
    ):
        raise ValueError("median_forecast_probability must be within aggregate bounds")


def _validate_row_consistency(row: ResearchTeamForecastDisagreementQueueRow) -> None:
    if row.specialist_count <= _ZERO_COUNT:
        raise ValueError("specialist_count must be positive")
    if row.forecast_count <= _ZERO_COUNT:
        raise ValueError("forecast_count must be positive")
    if row.queue_status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("queue_status must match reason_codes")


def _validate_report_consistency(
    report: ResearchTeamForecastDisagreementQueueReport,
) -> None:
    if report.aggregate_count != _decimal_count(len(report.rows)):
        raise ValueError("aggregate_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.queue_status != _report_status(report.rows):
        raise ValueError("queue_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted")
    if report.max_disagreement_severity != _max_or_none(
        tuple(row.disagreement_severity for row in report.rows),
    ):
        raise ValueError("max_disagreement_severity must match rows")
    if report.max_memory_age_seconds != _max_or_none(
        tuple(row.memory_age_seconds for row in report.rows),
    ):
        raise ValueError("max_memory_age_seconds must match rows")
    if report.min_source_coverage_ratio != _min_or_none(
        tuple(row.source_coverage_ratio for row in report.rows),
    ):
        raise ValueError("min_source_coverage_ratio must match rows")
    if report.min_review_capacity_ratio != _min_or_none(
        tuple(row.review_capacity_ratio for row in report.rows),
    ):
        raise ValueError("min_review_capacity_ratio must match rows")
    if report.max_escalation_urgency_score != _max_or_none(
        tuple(row.escalation_urgency_score for row in report.rows),
    ):
        raise ValueError("max_escalation_urgency_score must match rows")


def _row_sort_key(
    row: ResearchTeamForecastDisagreementQueueRow,
) -> tuple[int, Decimal, Decimal, Decimal, str, str]:
    return (
        _STATUS_RANK[row.queue_status],
        -row.escalation_urgency_score,
        -row.disagreement_severity,
        -row.memory_age_seconds,
        row.team_label,
        row.queue_label,
    )


def _status_count(
    rows: tuple[ResearchTeamForecastDisagreementQueueRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.queue_status == status))


def _max_or_none(values: tuple[Decimal, ...]) -> Decimal | None:
    if not values:
        return None
    return max(values)


def _min_or_none(values: tuple[Decimal, ...]) -> Decimal | None:
    if not values:
        return None
    return min(values)


def _review_capacity_ratio(available_count: Decimal, waiting_count: Decimal) -> Decimal:
    if waiting_count == _ZERO_COUNT:
        return _ONE
    return _bounded_ratio(available_count, waiting_count)


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
        if reason_code not in REASON_CODES:
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
    if type(value) is not str or value not in DISAGREEMENT_QUEUE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _normalize_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal_with_quantum(field_name, value, _COUNT_QUANTUM)
    if normalized < _ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != value:
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_optional_ratio(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _normalize_ratio(field_name, value)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > _ONE:
        raise ValueError(f"{field_name} must be at most one")
    return normalized


def _normalize_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_decimal(field_name, value)


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
        result: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            result[key] = _payload_value(item)
        return result
    raise ValueError("unsupported public payload value")
