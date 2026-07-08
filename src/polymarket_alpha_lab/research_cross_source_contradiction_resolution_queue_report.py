"""Pure public report reducer for cross-source contradiction resolution queues."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any

from .team_paper_guard import json_ready_no_floats, require_paper_only_flags


DEFAULT_RESEARCH_CROSS_SOURCE_CONTRADICTION_RESOLUTION_QUEUE_CONFIG_VERSION = (
    "research-cross-source-contradiction-resolution-queue-v0"
)

QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SIGNAL_COUNT = Decimal("5")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

SOURCE_CLASSES = ("derived_model", "official_reporting", "specialist_analysis")
QUEUE_STATUSES = ("pass", "watch", "block")
REPORT_STATUSES = ("pass", "watch", "block")
STATUS_RANK = {
    "block": Decimal("0"),
    "watch": Decimal("1"),
    "pass": Decimal("2"),
}

PASS_REASON = "contradiction_resolution_queue_passed"
GENERATED_RISK_REASONS = frozenset(
    (
        "aggregate_contradiction_severity_block",
        "aggregate_contradiction_severity_watch",
        "deadline_pressure_block",
        "deadline_pressure_watch",
        "freshness_risk_block",
        "freshness_risk_watch",
        "queue_score_block",
        "queue_score_watch",
        "reliability_gap_block",
        "reliability_gap_watch",
        "rule_ambiguity_block",
        "rule_ambiguity_watch",
    ),
)
SENSITIVE_TEXT_FRAGMENTS = (
    "sec" + "ret",
    "tok" + "en",
    "creden" + "tial",
    "pass" + "word",
    "post" + "gres://",
    "post" + "gresql://",
    "supa" + "base",
    "priv" + "ate_key",
    "priv" + "ate-key",
    "api" + "_key",
    "bearer ",
    "wall" + "et",
    "ord" + "er",
    "can" + "cel",
    "repl" + "ace",
    "au" + "th",
    "mar" + "ket",
    "slug",
    "question-",
    "condition-",
)
SENSITIVE_TEXT_MARKERS = ("://", "@")


@dataclass(frozen=True)
class ResearchCrossSourceContradictionResolutionQueueConfig:
    config_version: str = (
        DEFAULT_RESEARCH_CROSS_SOURCE_CONTRADICTION_RESOLUTION_QUEUE_CONFIG_VERSION
    )
    watch_queue_score: Decimal = Decimal("0.350000")
    block_queue_score: Decimal = Decimal("0.700000")
    stale_source_age_seconds: Decimal = Decimal("3600.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchCrossSourceContradictionResolutionQueueConfig:
            raise ValueError(
                "config must be a ResearchCrossSourceContradictionResolutionQueueConfig",
            )
        _require_public_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "watch_queue_score",
            _normalize_probability("watch_queue_score", self.watch_queue_score),
        )
        object.__setattr__(
            self,
            "block_queue_score",
            _normalize_probability("block_queue_score", self.block_queue_score),
        )
        object.__setattr__(
            self,
            "stale_source_age_seconds",
            _normalize_positive_decimal(
                "stale_source_age_seconds",
                self.stale_source_age_seconds,
            ),
        )
        if self.block_queue_score <= self.watch_queue_score:
            raise ValueError("block_queue_score must exceed watch_queue_score")
        require_paper_only_flags("config", self)


@dataclass(frozen=True)
class ResearchCrossSourceContradictionResolutionQueueInput:
    queue_item_id: str
    source_class_pair: tuple[str, str]
    observed_at: datetime
    aggregate_contradiction_severity: Decimal
    source_reliability_memory: Decimal
    source_age_seconds: Decimal
    rule_clarity: Decimal
    deadline_pressure: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchCrossSourceContradictionResolutionQueueInput:
            raise ValueError(
                "item must be a ResearchCrossSourceContradictionResolutionQueueInput",
            )
        _require_public_string("queue_item_id", self.queue_item_id)
        object.__setattr__(
            self,
            "source_class_pair",
            _normalize_source_class_pair(self.source_class_pair),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "aggregate_contradiction_severity",
            "source_reliability_memory",
            "rule_clarity",
            "deadline_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_age_seconds",
            _normalize_nonnegative_decimal("source_age_seconds", self.source_age_seconds),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        require_paper_only_flags("item", self)


@dataclass(frozen=True)
class ResearchCrossSourceContradictionResolutionQueueRow:
    queue_item_id: str
    source_class_pair: tuple[str, str]
    observed_at: datetime
    aggregate_contradiction_severity: Decimal
    source_reliability_memory: Decimal
    reliability_gap: Decimal
    source_age_seconds: Decimal
    freshness_risk: Decimal
    rule_clarity: Decimal
    rule_ambiguity: Decimal
    deadline_pressure: Decimal
    queue_score: Decimal
    queue_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchCrossSourceContradictionResolutionQueueRow:
            raise ValueError("row must be a ResearchCrossSourceContradictionResolutionQueueRow")
        _require_public_string("queue_item_id", self.queue_item_id)
        object.__setattr__(
            self,
            "source_class_pair",
            _normalize_source_class_pair(self.source_class_pair),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "aggregate_contradiction_severity",
            "source_reliability_memory",
            "reliability_gap",
            "freshness_risk",
            "rule_clarity",
            "rule_ambiguity",
            "deadline_pressure",
            "queue_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_age_seconds",
            _normalize_nonnegative_decimal("source_age_seconds", self.source_age_seconds),
        )
        _require_member("queue_status", self.queue_status, QUEUE_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row(self)
        require_paper_only_flags("row", self)


@dataclass(frozen=True)
class ResearchCrossSourceContradictionResolutionQueueReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchCrossSourceContradictionResolutionQueueReasonCodeCount:
            raise ValueError(
                "reason count must be a "
                "ResearchCrossSourceContradictionResolutionQueueReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        require_paper_only_flags("reason count", self)


@dataclass(frozen=True)
class ResearchCrossSourceContradictionResolutionQueueReport:
    generated_at: datetime
    config_version: str
    item_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_queue_score: Decimal
    max_aggregate_contradiction_severity: Decimal
    max_deadline_pressure: Decimal
    max_source_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchCrossSourceContradictionResolutionQueueReasonCodeCount, ...]
    rows: tuple[ResearchCrossSourceContradictionResolutionQueueRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchCrossSourceContradictionResolutionQueueReport:
            raise ValueError(
                "report must be a ResearchCrossSourceContradictionResolutionQueueReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in ("item_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_queue_score",
            "max_aggregate_contradiction_severity",
            "max_deadline_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_source_age_seconds",
            _normalize_nonnegative_decimal(
                "max_source_age_seconds",
                self.max_source_age_seconds,
            ),
        )
        _require_member("status", self.status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        require_paper_only_flags("report", self)


def build_research_cross_source_contradiction_resolution_queue_report(
    queue_items: Iterable[ResearchCrossSourceContradictionResolutionQueueInput],
    *,
    config: ResearchCrossSourceContradictionResolutionQueueConfig,
    generated_at: datetime,
) -> ResearchCrossSourceContradictionResolutionQueueReport:
    if type(config) is not ResearchCrossSourceContradictionResolutionQueueConfig:
        raise ValueError(
            "config must be a ResearchCrossSourceContradictionResolutionQueueConfig",
        )
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(queue_items)
    _reject_future_inputs(inputs, generated_at_utc)
    rows = tuple(
        sorted(
            (_row_from_input(item, config=config) for item in inputs),
            key=_row_sort_key,
        ),
    )
    return ResearchCrossSourceContradictionResolutionQueueReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        item_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        max_queue_score=_max_decimal(row.queue_score for row in rows),
        max_aggregate_contradiction_severity=_max_decimal(
            row.aggregate_contradiction_severity for row in rows
        ),
        max_deadline_pressure=_max_decimal(row.deadline_pressure for row in rows),
        max_source_age_seconds=_max_measure(row.source_age_seconds for row in rows),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_cross_source_contradiction_resolution_queue_payload(
    report: ResearchCrossSourceContradictionResolutionQueueReport,
) -> dict[str, Any]:
    if type(report) is not ResearchCrossSourceContradictionResolutionQueueReport:
        raise ValueError(
            "report must be a ResearchCrossSourceContradictionResolutionQueueReport",
        )
    require_paper_only_flags("report", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("report must serialize to a JSON object")
    return payload


def research_cross_source_contradiction_resolution_queue_digest(
    report: ResearchCrossSourceContradictionResolutionQueueReport,
) -> str:
    payload = research_cross_source_contradiction_resolution_queue_payload(report)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(canonical.encode("utf-8")).hexdigest()


def _row_from_input(
    item: ResearchCrossSourceContradictionResolutionQueueInput,
    *,
    config: ResearchCrossSourceContradictionResolutionQueueConfig,
) -> ResearchCrossSourceContradictionResolutionQueueRow:
    reliability_gap = _inverted_probability(item.source_reliability_memory)
    freshness_risk = _freshness_risk(item.source_age_seconds, config.stale_source_age_seconds)
    rule_ambiguity = _inverted_probability(item.rule_clarity)
    queue_score = _queue_score(
        aggregate_contradiction_severity=item.aggregate_contradiction_severity,
        reliability_gap=reliability_gap,
        freshness_risk=freshness_risk,
        rule_ambiguity=rule_ambiguity,
        deadline_pressure=item.deadline_pressure,
    )
    risk_reasons = _risk_reason_codes(
        item=item,
        reliability_gap=reliability_gap,
        freshness_risk=freshness_risk,
        rule_ambiguity=rule_ambiguity,
        queue_score=queue_score,
        config=config,
    )
    reason_codes = _normalize_reason_codes(
        "reason_codes",
        item.reason_codes + risk_reasons + (() if risk_reasons else (PASS_REASON,)),
    )
    return ResearchCrossSourceContradictionResolutionQueueRow(
        queue_item_id=item.queue_item_id,
        source_class_pair=item.source_class_pair,
        observed_at=item.observed_at,
        aggregate_contradiction_severity=item.aggregate_contradiction_severity,
        source_reliability_memory=item.source_reliability_memory,
        reliability_gap=reliability_gap,
        source_age_seconds=item.source_age_seconds,
        freshness_risk=freshness_risk,
        rule_clarity=item.rule_clarity,
        rule_ambiguity=rule_ambiguity,
        deadline_pressure=item.deadline_pressure,
        queue_score=queue_score,
        queue_status=_queue_status(reason_codes),
        reason_codes=reason_codes,
    )


def _queue_score(
    *,
    aggregate_contradiction_severity: Decimal,
    reliability_gap: Decimal,
    freshness_risk: Decimal,
    rule_ambiguity: Decimal,
    deadline_pressure: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(
            (
                aggregate_contradiction_severity
                + reliability_gap
                + freshness_risk
                + rule_ambiguity
                + deadline_pressure
            )
            / SIGNAL_COUNT,
        )


def _risk_reason_codes(
    *,
    item: ResearchCrossSourceContradictionResolutionQueueInput,
    reliability_gap: Decimal,
    freshness_risk: Decimal,
    rule_ambiguity: Decimal,
    queue_score: Decimal,
    config: ResearchCrossSourceContradictionResolutionQueueConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    _append_signal_reason(
        reasons,
        "aggregate_contradiction_severity",
        item.aggregate_contradiction_severity,
        config.watch_queue_score,
        config.block_queue_score,
    )
    _append_signal_reason(
        reasons,
        "reliability_gap",
        reliability_gap,
        config.watch_queue_score,
        config.block_queue_score,
    )
    _append_signal_reason(
        reasons,
        "freshness_risk",
        freshness_risk,
        config.watch_queue_score,
        config.block_queue_score,
    )
    _append_signal_reason(
        reasons,
        "rule_ambiguity",
        rule_ambiguity,
        config.watch_queue_score,
        config.block_queue_score,
    )
    _append_signal_reason(
        reasons,
        "deadline_pressure",
        item.deadline_pressure,
        config.watch_queue_score,
        config.block_queue_score,
    )
    _append_signal_reason(
        reasons,
        "queue_score",
        queue_score,
        config.watch_queue_score,
        config.block_queue_score,
    )
    return _normalize_reason_codes("risk reason_codes", tuple(reasons), allow_empty=True)


def _append_signal_reason(
    reasons: list[str],
    prefix: str,
    value: Decimal,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> None:
    if value >= block_threshold:
        reasons.append(f"{prefix}_block")
    elif value >= watch_threshold:
        reasons.append(f"{prefix}_watch")


def _queue_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return "block"
    if any(reason.endswith("_watch") for reason in reason_codes):
        return "watch"
    return "pass"


def _report_status(
    rows: tuple[ResearchCrossSourceContradictionResolutionQueueRow, ...],
) -> str:
    if any(row.queue_status == "block" for row in rows):
        return "block"
    if any(row.queue_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchCrossSourceContradictionResolutionQueueRow, ...],
) -> tuple[str, ...]:
    risk_reasons = tuple(
        sorted(
            {
                reason_code
                for row in rows
                for reason_code in row.reason_codes
                if reason_code in GENERATED_RISK_REASONS
            },
        ),
    )
    return risk_reasons or (PASS_REASON,)


def _reason_code_counts(
    rows: tuple[ResearchCrossSourceContradictionResolutionQueueRow, ...],
) -> tuple[ResearchCrossSourceContradictionResolutionQueueReasonCodeCount, ...]:
    counts = Counter(reason_code for row in rows for reason_code in row.reason_codes)
    return tuple(
        ResearchCrossSourceContradictionResolutionQueueReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    )


def _normalize_inputs(
    queue_items: Iterable[ResearchCrossSourceContradictionResolutionQueueInput],
) -> tuple[ResearchCrossSourceContradictionResolutionQueueInput, ...]:
    if isinstance(queue_items, (str, bytes)):
        raise ValueError("queue_items must be an iterable of queue inputs")
    try:
        items = tuple(queue_items)
    except TypeError as exc:
        raise ValueError("queue_items must be an iterable of queue inputs") from exc
    seen_ids: set[str] = set()
    normalized: list[ResearchCrossSourceContradictionResolutionQueueInput] = []
    for item in items:
        if type(item) is not ResearchCrossSourceContradictionResolutionQueueInput:
            raise ValueError(
                "queue_items must contain "
                "ResearchCrossSourceContradictionResolutionQueueInput values",
            )
        if item.queue_item_id in seen_ids:
            raise ValueError("duplicate queue_item_id")
        seen_ids.add(item.queue_item_id)
        normalized.append(item)
    return tuple(normalized)


def _reject_future_inputs(
    items: tuple[ResearchCrossSourceContradictionResolutionQueueInput, ...],
    generated_at: datetime,
) -> None:
    for item in items:
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")


def _normalize_rows(
    rows: tuple[ResearchCrossSourceContradictionResolutionQueueRow, ...],
) -> tuple[ResearchCrossSourceContradictionResolutionQueueRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchCrossSourceContradictionResolutionQueueRow:
            raise ValueError(
                "rows must contain ResearchCrossSourceContradictionResolutionQueueRow values",
            )
    return tuple(sorted(rows, key=_row_sort_key))


def _normalize_reason_code_counts(
    counts: tuple[ResearchCrossSourceContradictionResolutionQueueReasonCodeCount, ...],
) -> tuple[ResearchCrossSourceContradictionResolutionQueueReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    seen_codes: set[str] = set()
    normalized: list[ResearchCrossSourceContradictionResolutionQueueReasonCodeCount] = []
    for count in counts:
        if type(count) is not ResearchCrossSourceContradictionResolutionQueueReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchCrossSourceContradictionResolutionQueueReasonCodeCount values",
            )
        if count.reason_code in seen_codes:
            raise ValueError("duplicate reason_code")
        seen_codes.add(count.reason_code)
        normalized.append(count)
    return tuple(
        sorted(normalized, key=lambda count: (-int(count.count), count.reason_code)),
    )


def _normalize_source_class_pair(value: tuple[str, str]) -> tuple[str, str]:
    if type(value) is not tuple or len(value) != 2:
        raise ValueError("source_class_pair must contain two source classes")
    left, right = value
    _require_member("source_class_pair", left, SOURCE_CLASSES)
    _require_member("source_class_pair", right, SOURCE_CLASSES)
    if left == right:
        raise ValueError("source_class_pair must contain distinct source classes")
    return tuple(sorted((left, right)))


def _normalize_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...],
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_reason_code(field_name, reason_code)
        normalized.append(reason_code)
    if not normalized and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"{field_name} must not contain duplicates")
    return tuple(sorted(normalized))


def _normalize_report_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    normalized = _normalize_reason_codes("reason_codes", reason_codes)
    if normalized != (PASS_REASON,) and not all(
        reason_code in GENERATED_RISK_REASONS for reason_code in normalized
    ):
        raise ValueError("reason_codes must contain generated queue reasons only")
    return normalized


def _require_public_string(field_name: str, value: str) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty public string")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")
    if _contains_unsafe_public_text(value):
        raise ValueError(f"{field_name} must not contain private or identifying text")


def _require_reason_code(field_name: str, value: str) -> None:
    _require_public_string(field_name, value)
    if not all(character == "_" or character.isalnum() for character in value):
        raise ValueError(f"{field_name} must contain lowercase reason code text")
    if value.lower() != value:
        raise ValueError(f"{field_name} must contain lowercase reason code text")


def _require_member(field_name: str, value: str, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")
    if _contains_unsafe_public_text(value):
        raise ValueError(f"{field_name} must not contain private or identifying text")


def _contains_unsafe_public_text(value: str) -> bool:
    lowered = value.lower()
    return any(marker in lowered for marker in SENSITIVE_TEXT_MARKERS) or any(
        fragment in lowered for fragment in SENSITIVE_TEXT_FRAGMENTS
    )


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    offset = value.utcoffset()
    if value.tzinfo is None or offset is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_probability(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be non-negative")
    return normalized


def _normalize_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _normalize_nonnegative_count(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite() or value < ZERO or value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a non-negative whole Decimal")
    return value.quantize(COUNT_QUANTUM)


def _normalize_positive_count(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _max_decimal(values: Iterable[Decimal]) -> Decimal:
    return max(tuple(values), default=ZERO)


def _max_measure(values: Iterable[Decimal]) -> Decimal:
    return max(tuple(values), default=ZERO)


def _status_count(
    rows: tuple[ResearchCrossSourceContradictionResolutionQueueRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.queue_status == status))


def _inverted_probability(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(ONE - value)


def _freshness_risk(source_age_seconds: Decimal, stale_source_age_seconds: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        risk = source_age_seconds / stale_source_age_seconds
        return _quantize(ONE if risk > ONE else risk)


def _row_sort_key(
    row: ResearchCrossSourceContradictionResolutionQueueRow,
) -> tuple[Decimal, Decimal, tuple[str, str], str]:
    return (STATUS_RANK[row.queue_status], -row.queue_score, row.source_class_pair, row.queue_item_id)


def _validate_row(row: ResearchCrossSourceContradictionResolutionQueueRow) -> None:
    expected_score = _queue_score(
        aggregate_contradiction_severity=row.aggregate_contradiction_severity,
        reliability_gap=row.reliability_gap,
        freshness_risk=row.freshness_risk,
        rule_ambiguity=row.rule_ambiguity,
        deadline_pressure=row.deadline_pressure,
    )
    if row.queue_score != expected_score:
        raise ValueError("queue_score must match row inputs")
    if row.reliability_gap != _inverted_probability(row.source_reliability_memory):
        raise ValueError("reliability_gap must match source_reliability_memory")
    if row.rule_ambiguity != _inverted_probability(row.rule_clarity):
        raise ValueError("rule_ambiguity must match rule_clarity")
    if row.queue_status != _queue_status(row.reason_codes):
        raise ValueError("queue_status must match reason_codes")


def _validate_report(report: ResearchCrossSourceContradictionResolutionQueueReport) -> None:
    rows = report.rows
    if report.item_count != _count(len(rows)):
        raise ValueError("item_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.max_queue_score != _max_decimal(row.queue_score for row in rows):
        raise ValueError("max_queue_score must match rows")
    if report.max_aggregate_contradiction_severity != _max_decimal(
        row.aggregate_contradiction_severity for row in rows
    ):
        raise ValueError("max_aggregate_contradiction_severity must match rows")
    if report.max_deadline_pressure != _max_decimal(row.deadline_pressure for row in rows):
        raise ValueError("max_deadline_pressure must match rows")
    if report.max_source_age_seconds != _max_measure(row.source_age_seconds for row in rows):
        raise ValueError("max_source_age_seconds must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


__all__ = (
    "DEFAULT_RESEARCH_CROSS_SOURCE_CONTRADICTION_RESOLUTION_QUEUE_CONFIG_VERSION",
    "QUEUE_STATUSES",
    "REPORT_STATUSES",
    "ResearchCrossSourceContradictionResolutionQueueConfig",
    "ResearchCrossSourceContradictionResolutionQueueInput",
    "ResearchCrossSourceContradictionResolutionQueueReasonCodeCount",
    "ResearchCrossSourceContradictionResolutionQueueReport",
    "ResearchCrossSourceContradictionResolutionQueueRow",
    "build_research_cross_source_contradiction_resolution_queue_report",
    "research_cross_source_contradiction_resolution_queue_digest",
    "research_cross_source_contradiction_resolution_queue_payload",
)
