"""Pure outcome-learning feedback queue report for public-safe review loops."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, fields, is_dataclass
from decimal import Decimal
from hashlib import sha256
from typing import Any, Iterable


DEFAULT_RESEARCH_OUTCOME_LEARNING_FEEDBACK_QUEUE_CONFIG_VERSION = (
    "research-outcome-learning-feedback-queue-report-v0"
)
RESEARCH_OUTCOME_LEARNING_FEEDBACK_QUEUE_PUBLIC_STATUSES = (
    "pass",
    "watch",
    "block",
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

_BASE_REASON_CODE = "research_outcome_learning_feedback_queue"
_SCOPE_REASON_CODE = "report_only_feedback_queue"
_EMPTY_REASON_CODE = "no_outcome_learning_feedback_items"

_UNSAFE_PARTS = (
    ("event", "_", "id"),
    ("raw", "_", "event"),
    ("market", "_", "id"),
    ("market", "_slug"),
    ("source", "_", "id"),
    ("source", "_url"),
    ("url",),
    ("http",),
    (":", "/", "/"),
    ("wallet",),
    ("auth",),
    ("order",),
    ("trade",),
    ("live",),
    ("recommendation",),
    ("sizing",),
    ("private", "_key"),
    ("secret",),
    ("token",),
)
_UNSAFE_TERMS = tuple("".join(parts) for parts in _UNSAFE_PARTS)


@dataclass(frozen=True)
class ResearchOutcomeLearningFeedbackQueueConfig:
    config_version: str = DEFAULT_RESEARCH_OUTCOME_LEARNING_FEEDBACK_QUEUE_CONFIG_VERSION
    watch_feedback_pressure_threshold: Decimal = Decimal("0.350000")
    block_feedback_pressure_threshold: Decimal = Decimal("0.700000")
    aggregate_forecast_error_weight: Decimal = Decimal("0.300000")
    evidence_miss_weight: Decimal = Decimal("0.250000")
    source_reliability_drift_weight: Decimal = Decimal("0.200000")
    cost_friction_miss_weight: Decimal = Decimal("0.150000")
    team_calibration_drift_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchOutcomeLearningFeedbackQueueConfig:
            raise ValueError("config must be a ResearchOutcomeLearningFeedbackQueueConfig")
        _require_safe_code("config_version", self.config_version)
        for field_name in (
            "watch_feedback_pressure_threshold",
            "block_feedback_pressure_threshold",
            "aggregate_forecast_error_weight",
            "evidence_miss_weight",
            "source_reliability_drift_weight",
            "cost_friction_miss_weight",
            "team_calibration_drift_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_feedback_pressure_threshold <= self.watch_feedback_pressure_threshold:
            raise ValueError(
                "block_feedback_pressure_threshold must exceed watch threshold",
            )
        if _config_weight_sum(self) != ONE:
            raise ValueError("config weights must sum to 1")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchOutcomeLearningFeedbackItem:
    learning_key: str
    outcome_count: Decimal
    aggregate_forecast_error: Decimal
    evidence_miss_score: Decimal
    source_reliability_drift: Decimal
    cost_friction_miss_score: Decimal
    team_calibration_drift: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchOutcomeLearningFeedbackItem:
            raise ValueError(
                "item must be a ResearchOutcomeLearningFeedbackItem",
            )
        _require_safe_code("learning_key", self.learning_key)
        object.__setattr__(
            self,
            "outcome_count",
            _normalize_whole_decimal("outcome_count", self.outcome_count),
        )
        for field_name in (
            "aggregate_forecast_error",
            "evidence_miss_score",
            "source_reliability_drift",
            "cost_friction_miss_score",
            "team_calibration_drift",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("item", self)


@dataclass(frozen=True)
class ResearchOutcomeLearningFeedbackQueueRow:
    learning_key: str
    outcome_count: Decimal
    aggregate_forecast_error: Decimal
    evidence_miss_score: Decimal
    source_reliability_drift: Decimal
    cost_friction_miss_score: Decimal
    team_calibration_drift: Decimal
    feedback_pressure: Decimal
    status: str
    queued: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchOutcomeLearningFeedbackQueueRow:
            raise ValueError("row must be a ResearchOutcomeLearningFeedbackQueueRow")
        _require_safe_code("learning_key", self.learning_key)
        object.__setattr__(
            self,
            "outcome_count",
            _normalize_whole_decimal("outcome_count", self.outcome_count),
        )
        for field_name in (
            "aggregate_forecast_error",
            "evidence_miss_score",
            "source_reliability_drift",
            "cost_friction_miss_score",
            "team_calibration_drift",
            "feedback_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        _require_bool("queued", self.queued)
        if self.queued != (self.status != "pass"):
            raise ValueError("queued must match status")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchOutcomeLearningFeedbackReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchOutcomeLearningFeedbackReasonCodeCount:
            raise ValueError(
                "reason_code_count must be a "
                "ResearchOutcomeLearningFeedbackReasonCodeCount",
            )
        _require_safe_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchOutcomeLearningFeedbackQueueReport:
    config_version: str
    item_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    queued_feedback_count: Decimal
    max_feedback_pressure: Decimal
    status: str
    rows: tuple[ResearchOutcomeLearningFeedbackQueueRow, ...]
    reason_code_counts: tuple[ResearchOutcomeLearningFeedbackReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchOutcomeLearningFeedbackQueueReport:
            raise ValueError("report must be a ResearchOutcomeLearningFeedbackQueueReport")
        _require_safe_code("config_version", self.config_version)
        for field_name in (
            "item_count",
            "pass_count",
            "watch_count",
            "block_count",
            "queued_feedback_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_feedback_pressure",
            _normalize_unit_decimal("max_feedback_pressure", self.max_feedback_pressure),
        )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _validate_report_consistency(self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_outcome_learning_feedback_queue_report_payload(self)


def build_research_outcome_learning_feedback_queue_report(
    items: Iterable[object],
    *,
    config: ResearchOutcomeLearningFeedbackQueueConfig,
) -> ResearchOutcomeLearningFeedbackQueueReport:
    if type(config) is not ResearchOutcomeLearningFeedbackQueueConfig:
        raise ValueError("config must be a ResearchOutcomeLearningFeedbackQueueConfig")
    _require_hard_flags("config", config)
    rows = _normalize_build_rows(items, config)
    reason_codes = _report_reason_codes(rows)
    report_values: dict[str, object] = {
        "config_version": config.config_version,
        "item_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "queued_feedback_count": _decimal_count(sum(1 for row in rows if row.queued)),
        "max_feedback_pressure": _max_feedback_pressure(rows),
        "status": _report_status(rows),
        "rows": rows,
        "reason_code_counts": _reason_code_counts(reason_codes, rows),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    report_values["derived_validation_digest"] = _digest_public(report_values)
    return ResearchOutcomeLearningFeedbackQueueReport(**report_values)  # type: ignore[arg-type]


def research_outcome_learning_feedback_queue_report_payload(
    report: ResearchOutcomeLearningFeedbackQueueReport,
) -> dict[str, Any]:
    if type(report) is not ResearchOutcomeLearningFeedbackQueueReport:
        raise ValueError("report must be a ResearchOutcomeLearningFeedbackQueueReport")
    _require_hard_flags("report", report)
    _validate_report_consistency(report)
    payload = _public_json(asdict(report))
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    validate_research_outcome_learning_feedback_queue_public_payload(payload)
    return payload


def validate_research_outcome_learning_feedback_queue_public_payload(
    payload: dict[str, Any],
    *,
    require_flags: bool = True,
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_entries(payload)
    _reject_numeric_public_values(payload)
    if require_flags:
        _require_public_payload_flags(payload)
    _require_public_status_values(payload)
    return True


def _normalize_build_rows(
    items: Iterable[object],
    config: ResearchOutcomeLearningFeedbackQueueConfig,
) -> tuple[ResearchOutcomeLearningFeedbackQueueRow, ...]:
    if isinstance(items, (str, bytes)):
        raise ValueError("items must be an iterable")
    try:
        values = tuple(items)
    except TypeError as exc:
        raise ValueError("items must be an iterable") from exc
    rows: list[ResearchOutcomeLearningFeedbackQueueRow] = []
    learning_keys: list[str] = []
    for value in values:
        if type(value) is ResearchOutcomeLearningFeedbackItem:
            _require_hard_flags("item", value)
            row = _row_from_item(value, config)
        elif type(value) is ResearchOutcomeLearningFeedbackQueueRow:
            _require_hard_flags("row", value)
            row = value
        else:
            raise ValueError(
                "items must contain ResearchOutcomeLearningFeedbackItem "
                "or ResearchOutcomeLearningFeedbackQueueRow values",
            )
        learning_keys.append(row.learning_key)
        rows.append(row)
    if len(set(learning_keys)) != len(learning_keys):
        raise ValueError("learning_key values must be unique")
    return tuple(sorted(rows, key=_row_sort_key))


def _row_from_item(
    item: ResearchOutcomeLearningFeedbackItem,
    config: ResearchOutcomeLearningFeedbackQueueConfig,
) -> ResearchOutcomeLearningFeedbackQueueRow:
    feedback_pressure = _normalize_unit_decimal(
        "feedback_pressure",
        item.aggregate_forecast_error * config.aggregate_forecast_error_weight
        + item.evidence_miss_score * config.evidence_miss_weight
        + item.source_reliability_drift * config.source_reliability_drift_weight
        + item.cost_friction_miss_score * config.cost_friction_miss_weight
        + item.team_calibration_drift * config.team_calibration_drift_weight,
    )
    status = _row_status(feedback_pressure, config)
    return ResearchOutcomeLearningFeedbackQueueRow(
        learning_key=item.learning_key,
        outcome_count=item.outcome_count,
        aggregate_forecast_error=item.aggregate_forecast_error,
        evidence_miss_score=item.evidence_miss_score,
        source_reliability_drift=item.source_reliability_drift,
        cost_friction_miss_score=item.cost_friction_miss_score,
        team_calibration_drift=item.team_calibration_drift,
        feedback_pressure=feedback_pressure,
        status=status,
        queued=status != "pass",
        reason_codes=_row_reason_codes(item, feedback_pressure, status, config),
    )


def _row_status(
    feedback_pressure: Decimal,
    config: ResearchOutcomeLearningFeedbackQueueConfig,
) -> str:
    if feedback_pressure >= config.block_feedback_pressure_threshold:
        return "block"
    if feedback_pressure >= config.watch_feedback_pressure_threshold:
        return "watch"
    return "pass"


def _row_reason_codes(
    item: ResearchOutcomeLearningFeedbackItem,
    feedback_pressure: Decimal,
    status: str,
    config: ResearchOutcomeLearningFeedbackQueueConfig,
) -> tuple[str, ...]:
    values = {
        _SCOPE_REASON_CODE,
        f"{_BASE_REASON_CODE}_{status}",
        f"feedback_pressure_{status}",
    }
    _add_metric_reason(
        values,
        "aggregate_forecast_error_miss",
        item.aggregate_forecast_error,
        config.watch_feedback_pressure_threshold,
    )
    _add_metric_reason(
        values,
        "evidence_miss",
        item.evidence_miss_score,
        config.watch_feedback_pressure_threshold,
    )
    _add_metric_reason(
        values,
        "source_reliability_drift",
        item.source_reliability_drift,
        config.watch_feedback_pressure_threshold,
    )
    _add_metric_reason(
        values,
        "cost_friction_miss",
        item.cost_friction_miss_score,
        config.watch_feedback_pressure_threshold,
    )
    _add_metric_reason(
        values,
        "team_calibration_drift",
        item.team_calibration_drift,
        config.watch_feedback_pressure_threshold,
    )
    for reason_code in item.reason_codes:
        values.add(f"input_{reason_code}")
    if feedback_pressure >= config.block_feedback_pressure_threshold:
        values.add("feedback_pressure_block_threshold_met")
    elif feedback_pressure >= config.watch_feedback_pressure_threshold:
        values.add("feedback_pressure_watch_threshold_met")
    else:
        values.add("feedback_pressure_below_queue_threshold")
    return tuple(sorted(values))


def _add_metric_reason(
    values: set[str],
    reason_code: str,
    value: Decimal,
    watch_threshold: Decimal,
) -> None:
    if value >= watch_threshold:
        values.add(reason_code)


def _report_status(rows: tuple[ResearchOutcomeLearningFeedbackQueueRow, ...]) -> str:
    if not rows or any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchOutcomeLearningFeedbackQueueRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (
            _EMPTY_REASON_CODE,
            f"{_BASE_REASON_CODE}_block",
            _SCOPE_REASON_CODE,
        )
    values = {_SCOPE_REASON_CODE}
    for row in rows:
        values.update(row.reason_codes)
    return tuple(sorted(values))


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[ResearchOutcomeLearningFeedbackQueueRow, ...],
) -> tuple[ResearchOutcomeLearningFeedbackReasonCodeCount, ...]:
    counts = {reason_code: ZERO for reason_code in reason_codes}
    if not rows:
        for reason_code in reason_codes:
            counts[reason_code] = Decimal("1")
    else:
        for row in rows:
            for reason_code in row.reason_codes:
                counts[reason_code] = counts.get(reason_code, ZERO) + Decimal("1")
    return tuple(
        ResearchOutcomeLearningFeedbackReasonCodeCount(
            reason_code=reason_code,
            count=counts[reason_code],
        )
        for reason_code in sorted(counts)
        if counts[reason_code] > ZERO
    )


def _normalize_rows(
    rows: object,
) -> tuple[ResearchOutcomeLearningFeedbackQueueRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchOutcomeLearningFeedbackQueueRow:
            raise ValueError(
                "rows must contain ResearchOutcomeLearningFeedbackQueueRow values",
            )
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    if rows != sorted_rows:
        raise ValueError("rows must use deterministic ordering")
    return rows


def _normalize_reason_code_counts(
    values: object,
) -> tuple[ResearchOutcomeLearningFeedbackReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for value in values:
        if type(value) is not ResearchOutcomeLearningFeedbackReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchOutcomeLearningFeedbackReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", value)
    sorted_values = tuple(sorted(values, key=lambda value: value.reason_code))
    if values != sorted_values:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return values


def _validate_report_consistency(
    report: ResearchOutcomeLearningFeedbackQueueReport,
) -> None:
    if report.item_count != _decimal_count(len(report.rows)):
        raise ValueError("item_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.queued_feedback_count != _decimal_count(
        sum(1 for row in report.rows if row.queued),
    ):
        raise ValueError("queued_feedback_count must match rows")
    if report.max_feedback_pressure != _max_feedback_pressure(report.rows):
        raise ValueError("max_feedback_pressure must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(
        report.reason_codes,
        report.rows,
    ):
        raise ValueError("reason_code_counts must match rows")
    if report.derived_validation_digest != _report_digest(report):
        raise ValueError("derived_validation_digest must match report payload")


def _status_count(
    rows: tuple[ResearchOutcomeLearningFeedbackQueueRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _max_feedback_pressure(
    rows: tuple[ResearchOutcomeLearningFeedbackQueueRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return max(row.feedback_pressure for row in rows)


def _row_sort_key(row: ResearchOutcomeLearningFeedbackQueueRow) -> tuple[Decimal, str]:
    return (-row.feedback_pressure, row.learning_key)


def _config_weight_sum(config: ResearchOutcomeLearningFeedbackQueueConfig) -> Decimal:
    return _normalize_decimal(
        "config_weight_sum",
        config.aggregate_forecast_error_weight
        + config.evidence_miss_weight
        + config.source_reliability_drift_weight
        + config.cost_friction_miss_weight
        + config.team_calibration_drift_weight,
    )


def _normalize_reason_codes(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not allow_empty and not value:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    for reason_code in value:
        _require_safe_code(field_name, reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
    return value


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    integral = normalized.to_integral_value()
    if normalized != integral:
        raise ValueError(f"{field_name} must be a whole count")
    return integral


def _normalize_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_whole_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        if isinstance(value, Decimal):
            raise ValueError(f"{field_name} must be an exact Decimal")
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value)


def _require_status(field_name: str, value: object) -> None:
    if (
        type(value) is not str
        or value not in RESEARCH_OUTCOME_LEARNING_FEEDBACK_QUEUE_PUBLIC_STATUSES
    ):
        raise ValueError(
            f"{field_name} must be one of "
            f"{RESEARCH_OUTCOME_LEARNING_FEEDBACK_QUEUE_PUBLIC_STATUSES!r}",
        )


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_safe_code(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if value.lower() != value:
        raise ValueError(f"{field_name} must be lowercase")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")
    for character in value:
        if not (
            "a" <= character <= "z"
            or "0" <= character <= "9"
            or character in {"_", "-"}
        ):
            raise ValueError(f"{field_name} must contain safe public characters")
    try:
        _reject_unsafe_public_entries(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} contains unsafe public text") from exc


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True in public payload")


def _require_public_status_values(value: object) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key == "status":
                _require_status("status", nested)
            _require_public_status_values(nested)
    elif isinstance(value, list):
        for nested in value:
            _require_public_status_values(nested)


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _report_digest(report: ResearchOutcomeLearningFeedbackQueueReport) -> str:
    return _digest_public(
        {
            field.name: getattr(report, field.name)
            for field in fields(report)
            if field.name != "derived_validation_digest"
        },
    )


def _digest_public(value: object) -> str:
    ready = _digest_ready(value)
    _reject_unsafe_public_entries(ready)
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _digest_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _digest_ready(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("digest Decimal value must be finite")
        return str(value)
    if isinstance(value, float):
        raise ValueError("digest value must not be a float")
    if isinstance(value, int) and not isinstance(value, bool):
        raise ValueError("digest value must not be an int")
    if isinstance(value, (str, bool)) or value is None:
        return value
    if isinstance(value, dict):
        ready: dict[str, object] = {}
        for key, nested in value.items():
            if type(key) is not str:
                raise ValueError("digest payload keys must be strings")
            if key == "derived_validation_digest":
                continue
            ready[key] = _digest_ready(nested)
        return ready
    if isinstance(value, tuple):
        return [_digest_ready(nested) for nested in value]
    if isinstance(value, list):
        return [_digest_ready(nested) for nested in value]
    raise ValueError("value is not digest serializable")


def _reject_unsafe_public_entries(value: object) -> None:
    for item in _iter_public_strings(value):
        lowered = item.lower()
        if any(term in lowered for term in _UNSAFE_TERMS):
            raise ValueError("unsafe public payload entry")


def _reject_numeric_public_values(value: object) -> None:
    if isinstance(value, Decimal):
        raise ValueError("numeric public payload values must be encoded strings")
    if isinstance(value, float):
        raise ValueError("numeric public payload values must be encoded strings")
    if isinstance(value, int) and not isinstance(value, bool):
        raise ValueError("numeric public payload values must be encoded strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_numeric_public_values(item)
    elif isinstance(value, list):
        for item in value:
            _reject_numeric_public_values(item)


def _iter_public_strings(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_public_strings(asdict(value))
    if isinstance(value, dict):
        items: list[str] = []
        for key, nested in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            items.append(key)
            items.extend(_iter_public_strings(nested))
        return tuple(items)
    if type(value) is str:
        return (value,)
    if isinstance(value, list):
        items = []
        for nested in value:
            items.extend(_iter_public_strings(nested))
        return tuple(items)
    return ()


def _public_json(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _public_json(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("public Decimal value must be finite")
        return str(value)
    if isinstance(value, float):
        raise ValueError("public value must not be a float")
    if isinstance(value, int) and not isinstance(value, bool):
        raise ValueError("public value must not be an int")
    if isinstance(value, (str, bool)):
        return value
    if isinstance(value, dict):
        converted: dict[str, Any] = {}
        for key, nested in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            converted[key] = _public_json(nested)
        return converted
    if isinstance(value, tuple):
        return [_public_json(nested) for nested in value]
    if isinstance(value, list):
        return [_public_json(nested) for nested in value]
    raise ValueError("public value must be scalar or container")


__all__ = (
    "DEFAULT_RESEARCH_OUTCOME_LEARNING_FEEDBACK_QUEUE_CONFIG_VERSION",
    "RESEARCH_OUTCOME_LEARNING_FEEDBACK_QUEUE_PUBLIC_STATUSES",
    "ResearchOutcomeLearningFeedbackQueueConfig",
    "ResearchOutcomeLearningFeedbackItem",
    "ResearchOutcomeLearningFeedbackQueueRow",
    "ResearchOutcomeLearningFeedbackReasonCodeCount",
    "ResearchOutcomeLearningFeedbackQueueReport",
    "build_research_outcome_learning_feedback_queue_report",
    "research_outcome_learning_feedback_queue_report_payload",
    "validate_research_outcome_learning_feedback_queue_public_payload",
)
