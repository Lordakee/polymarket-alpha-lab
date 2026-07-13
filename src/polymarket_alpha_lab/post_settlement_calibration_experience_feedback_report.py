"""Read-only post-settlement calibration experience feedback report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, DecimalException, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_POST_SETTLEMENT_CALIBRATION_EXPERIENCE_CONFIG_VERSION = (
    "post-settlement-calibration-experience-feedback-v0"
)
POST_SETTLEMENT_CALIBRATION_EXPERIENCE_STATUSES = ("pass", "watch", "block")
QUEUE_PRIORITY_RANKS = {"high": 0, "medium": 1, "low": 2}

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

READY_REASON = "post_settlement_calibration_evidence_ready"
EMPTY_REASON = "no_settled_calibration_events"
RESIDUAL_WATCH_REASON = "prediction_residual_above_watch_threshold"
RESIDUAL_BLOCK_REASON = "prediction_residual_above_block_threshold"
DRIFT_WATCH_REASON = "team_calibration_drift_above_watch_threshold"
DRIFT_BLOCK_REASON = "team_calibration_drift_above_block_threshold"
READINESS_WATCH_REASON = "evidence_readiness_below_pass_threshold"
READINESS_BLOCK_REASON = "evidence_readiness_below_block_threshold"
LEARNING_WATCH_REASON = "retrospective_learning_pressure_watch"
LEARNING_BLOCK_REASON = "retrospective_learning_pressure_block"

PASS_NEXT_STEP = "archive_readonly_post_settlement_calibration_evidence"
WATCH_NEXT_STEP = "queue_long_term_memory_experience_review"
BLOCK_NEXT_STEP = "open_manual_post_settlement_calibration_packet"
EMPTY_NEXT_STEP = "manual_collect_settled_calibration_evidence"

PUBLIC_KEY_RE = re.compile(r"^[a-z][a-z0-9_.-]{0,127}$")
PUBLIC_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{0,127}$")
REASON_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{0,127}$")
HEX_RE = re.compile(r"^[0-9a-f]{64}$")

UNSAFE_KEY_FRAGMENTS = frozenset(("market", "slug", "question", "raw", "url"))
UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "persist",
        "database",
        "scrap",
        "supabase",
        "auth",
        "wallet",
        "order",
        "trade",
        "execute",
        "token",
        "secret",
        "api_key",
        "private_key",
    ),
)

__all__ = (
    "DEFAULT_POST_SETTLEMENT_CALIBRATION_EXPERIENCE_CONFIG_VERSION",
    "POST_SETTLEMENT_CALIBRATION_EXPERIENCE_STATUSES",
    "PostSettlementCalibrationExperienceConfig",
    "PostSettlementCalibrationExperienceEvent",
    "PostSettlementCalibrationExperienceRow",
    "PostSettlementCalibrationExperienceMemoryQueueItem",
    "PostSettlementCalibrationExperienceReasonCodeCount",
    "PostSettlementCalibrationExperienceReport",
    "build_post_settlement_calibration_experience_feedback_report",
    "post_settlement_calibration_experience_feedback_report_digest",
    "post_settlement_calibration_experience_feedback_report_payload",
    "validate_post_settlement_calibration_experience_feedback_public_payload",
)


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class PostSettlementCalibrationExperienceConfig(_FinalDataclass):
    config_version: str = DEFAULT_POST_SETTLEMENT_CALIBRATION_EXPERIENCE_CONFIG_VERSION
    prediction_residual_watch_threshold: Decimal = Decimal("0.150000")
    prediction_residual_block_threshold: Decimal = Decimal("0.500000")
    team_calibration_drift_watch_threshold: Decimal = Decimal("0.050000")
    team_calibration_drift_block_threshold: Decimal = Decimal("0.150000")
    evidence_readiness_pass_threshold: Decimal = Decimal("0.800000")
    evidence_readiness_block_threshold: Decimal = Decimal("0.500000")
    retrospective_learning_pressure_watch_threshold: Decimal = Decimal("0.250000")
    retrospective_learning_pressure_block_threshold: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        if self.config_version != DEFAULT_POST_SETTLEMENT_CALIBRATION_EXPERIENCE_CONFIG_VERSION:
            raise ValueError("config_version must be the supported version")
        for field_name in (
            "prediction_residual_watch_threshold",
            "prediction_residual_block_threshold",
            "team_calibration_drift_watch_threshold",
            "team_calibration_drift_block_threshold",
            "evidence_readiness_pass_threshold",
            "evidence_readiness_block_threshold",
            "retrospective_learning_pressure_watch_threshold",
            "retrospective_learning_pressure_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        if self.prediction_residual_watch_threshold > self.prediction_residual_block_threshold:
            raise ValueError("prediction residual watch threshold must not exceed block")
        if self.team_calibration_drift_watch_threshold > self.team_calibration_drift_block_threshold:
            raise ValueError("team calibration drift watch threshold must not exceed block")
        if self.evidence_readiness_block_threshold > self.evidence_readiness_pass_threshold:
            raise ValueError("evidence readiness block threshold must not exceed pass")
        if (
            self.retrospective_learning_pressure_watch_threshold
            > self.retrospective_learning_pressure_block_threshold
        ):
            raise ValueError("retrospective learning pressure watch threshold must not exceed block")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class PostSettlementCalibrationExperienceEvent(_FinalDataclass):
    event_key: str
    domain_team: str
    forecast_probability: Decimal
    settled_outcome_probability: Decimal
    baseline_team_calibration_error: Decimal
    settled_team_calibration_error: Decimal
    evidence_readiness_score: Decimal
    retrospective_learning_pressure: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "event_key",
            _require_public_key("event_key", self.event_key),
        )
        object.__setattr__(
            self,
            "domain_team",
            _require_public_code("domain_team", self.domain_team),
        )
        for field_name in (
            "forecast_probability",
            "baseline_team_calibration_error",
            "settled_team_calibration_error",
            "evidence_readiness_score",
            "retrospective_learning_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "settled_outcome_probability",
            _require_binary_probability(
                "settled_outcome_probability",
                self.settled_outcome_probability,
            ),
        )
        _require_hard_flags("event", self)


@dataclass(frozen=True)
class PostSettlementCalibrationExperienceRow(_FinalDataclass):
    event_key: str
    domain_team: str
    forecast_probability: Decimal
    settled_outcome_probability: Decimal
    baseline_team_calibration_error: Decimal
    settled_team_calibration_error: Decimal
    prediction_residual_probability: Decimal
    team_calibration_drift: Decimal
    evidence_readiness_score: Decimal
    retrospective_learning_pressure: Decimal
    long_term_memory_writeback_required: bool
    status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "event_key", _require_public_key("event_key", self.event_key))
        object.__setattr__(self, "domain_team", _require_public_code("domain_team", self.domain_team))
        for field_name in (
            "forecast_probability",
            "baseline_team_calibration_error",
            "settled_team_calibration_error",
            "prediction_residual_probability",
            "team_calibration_drift",
            "evidence_readiness_score",
            "retrospective_learning_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "settled_outcome_probability",
            _require_binary_probability(
                "settled_outcome_probability",
                self.settled_outcome_probability,
            ),
        )
        if type(self.long_term_memory_writeback_required) is not bool:
            raise ValueError("long_term_memory_writeback_required must be a bool")
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(self.reason_codes, allow_repeats=False),
        )
        _require_manual_next_step("manual_next_step", self.manual_next_step)
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class PostSettlementCalibrationExperienceMemoryQueueItem(_FinalDataclass):
    event_key: str
    domain_team: str
    prediction_residual_probability: Decimal
    team_calibration_drift: Decimal
    evidence_readiness_score: Decimal
    retrospective_learning_pressure: Decimal
    queue_priority: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "event_key", _require_public_key("event_key", self.event_key))
        object.__setattr__(self, "domain_team", _require_public_code("domain_team", self.domain_team))
        for field_name in (
            "prediction_residual_probability",
            "team_calibration_drift",
            "evidence_readiness_score",
            "retrospective_learning_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        if self.queue_priority not in ("medium", "high"):
            raise ValueError("queue_priority must be medium or high")
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(self.reason_codes, allow_repeats=False),
        )
        _require_manual_next_step("manual_next_step", self.manual_next_step)
        if self.manual_next_step == PASS_NEXT_STEP or not self.reason_codes:
            raise ValueError("queued experience must require manual review")
        _require_hard_flags("memory queue item", self)


@dataclass(frozen=True)
class PostSettlementCalibrationExperienceReasonCodeCount(_FinalDataclass):
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _require_positive_count("count", self.count))
        object.__setattr__(self, "row_ratio", _require_ratio("row_ratio", self.row_ratio))
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class PostSettlementCalibrationExperienceReport(_FinalDataclass):
    generated_at: datetime
    config_version: str
    effective_config: PostSettlementCalibrationExperienceConfig
    event_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    memory_writeback_queue_count: Decimal
    average_prediction_residual_probability: Decimal
    average_team_calibration_drift: Decimal
    max_prediction_residual_probability: Decimal
    max_team_calibration_drift: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[PostSettlementCalibrationExperienceReasonCodeCount, ...]
    manual_next_step: str
    rows: tuple[PostSettlementCalibrationExperienceRow, ...]
    memory_writeback_queue: tuple[PostSettlementCalibrationExperienceMemoryQueueItem, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if self.config_version != DEFAULT_POST_SETTLEMENT_CALIBRATION_EXPERIENCE_CONFIG_VERSION:
            raise ValueError("config_version must be the supported version")
        object.__setattr__(
            self,
            "effective_config",
            _require_effective_config(self.effective_config),
        )
        if self.config_version != self.effective_config.config_version:
            raise ValueError("config_version must match effective_config")
        for field_name in (
            "event_count",
            "pass_count",
            "watch_count",
            "block_count",
            "memory_writeback_queue_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_prediction_residual_probability",
            "average_team_calibration_drift",
            "max_prediction_residual_probability",
            "max_team_calibration_drift",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(self.reason_codes, allow_repeats=False),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _require_reason_code_counts(self.reason_code_counts),
        )
        _require_manual_next_step("manual_next_step", self.manual_next_step)
        object.__setattr__(self, "rows", _require_rows(self.rows))
        object.__setattr__(
            self,
            "memory_writeback_queue",
            _require_memory_queue(self.memory_writeback_queue),
        )
        _require_hard_flags("report", self)
        _validate_report(self)
        _require_or_set_digest(self)

    @property
    def payload(self) -> dict[str, Any]:
        return post_settlement_calibration_experience_feedback_report_payload(self)


def build_post_settlement_calibration_experience_feedback_report(
    events: Iterable[PostSettlementCalibrationExperienceEvent],
    *,
    generated_at: datetime,
    config: PostSettlementCalibrationExperienceConfig,
) -> PostSettlementCalibrationExperienceReport:
    if type(config) is not PostSettlementCalibrationExperienceConfig:
        raise ValueError("config must be a PostSettlementCalibrationExperienceConfig")
    effective_config = _revalidated_config_object(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (
                _row_from_event(event, effective_config)
                for event in _normalize_events(events)
            ),
            key=_row_key,
        ),
    )
    queue = tuple(
        sorted(
            (
                _queue_item_from_row(row)
                for row in rows
                if row.long_term_memory_writeback_required
            ),
            key=_queue_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    return PostSettlementCalibrationExperienceReport(
        generated_at=generated_at_utc,
        config_version=effective_config.config_version,
        effective_config=effective_config,
        event_count=_count(len(rows)),
        pass_count=_count(sum(row.status == "pass" for row in rows)),
        watch_count=_count(sum(row.status == "watch" for row in rows)),
        block_count=_count(sum(row.status == "block" for row in rows)),
        memory_writeback_queue_count=_count(len(queue)),
        average_prediction_residual_probability=_average(
            row.prediction_residual_probability for row in rows
        ),
        average_team_calibration_drift=_average(row.team_calibration_drift for row in rows),
        max_prediction_residual_probability=_max_ratio(
            row.prediction_residual_probability for row in rows
        ),
        max_team_calibration_drift=_max_ratio(row.team_calibration_drift for row in rows),
        status=_report_status(rows),
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
        manual_next_step=_report_manual_next_step(rows),
        rows=rows,
        memory_writeback_queue=queue,
    )


def post_settlement_calibration_experience_feedback_report_payload(
    report: PostSettlementCalibrationExperienceReport | Mapping[str, object],
) -> dict[str, Any]:
    if type(report) is PostSettlementCalibrationExperienceReport:
        canonical_report = _revalidated_report_object(report)
        payload = _public_json(canonical_report)
    elif isinstance(report, Mapping):
        source_payload = dict(report)
        return validate_post_settlement_calibration_experience_feedback_public_payload(
            source_payload,
        )
    else:
        raise ValueError("report must be a PostSettlementCalibrationExperienceReport")
    if type(payload) is not dict:
        raise ValueError("payload must be an object")
    _reject_unsafe_public_payload(payload)
    _reject_public_numeric_values(payload)
    return payload


def post_settlement_calibration_experience_feedback_report_digest(
    report: PostSettlementCalibrationExperienceReport,
) -> str:
    if type(report) is not PostSettlementCalibrationExperienceReport:
        raise ValueError("report must be a PostSettlementCalibrationExperienceReport")
    canonical_report = _revalidated_report_object(report)
    digest = _digest(_payload_without_digest(canonical_report))
    if canonical_report.derived_validation_digest != digest:
        raise ValueError("derived_validation_digest must match report payload")
    return digest


def _revalidated_report_object(
    report: PostSettlementCalibrationExperienceReport,
) -> PostSettlementCalibrationExperienceReport:
    _require_exact_object_type(report, PostSettlementCalibrationExperienceReport, "report")
    _require_exact_object_string("status", report.status)
    _require_exact_object_string("manual_next_step", report.manual_next_step)
    if (
        type(report.derived_validation_digest) is not str
        or HEX_RE.fullmatch(report.derived_validation_digest) is None
    ):
        raise ValueError("derived_validation_digest must be a sha256 digest")
    _require_exact_object_tuple("reason_codes", report.reason_codes)
    _require_exact_object_tuple("reason_code_counts", report.reason_code_counts)
    _require_exact_object_tuple("rows", report.rows)
    _require_exact_object_tuple(
        "memory_writeback_queue",
        report.memory_writeback_queue,
    )
    canonical_config = _revalidated_config_object(report.effective_config)
    canonical_rows = tuple(
        _revalidated_row_object(row, index=index)
        for index, row in enumerate(report.rows)
    )
    canonical_queue = tuple(
        _revalidated_memory_queue_item_object(item, index=index)
        for index, item in enumerate(report.memory_writeback_queue)
    )
    canonical_reason_counts = tuple(
        _revalidated_reason_code_count_object(item, index=index)
        for index, item in enumerate(report.reason_code_counts)
    )
    values = {field.name: getattr(report, field.name) for field in fields(report)}
    values["effective_config"] = canonical_config
    values["rows"] = canonical_rows
    values["memory_writeback_queue"] = canonical_queue
    values["reason_code_counts"] = canonical_reason_counts
    return PostSettlementCalibrationExperienceReport(**values)


def _revalidated_config_object(
    config: PostSettlementCalibrationExperienceConfig,
) -> PostSettlementCalibrationExperienceConfig:
    _require_exact_object_type(
        config,
        PostSettlementCalibrationExperienceConfig,
        "effective_config",
    )
    return PostSettlementCalibrationExperienceConfig(
        **{field.name: getattr(config, field.name) for field in fields(config)},
    )


def _revalidated_row_object(
    row: PostSettlementCalibrationExperienceRow,
    *,
    index: int,
) -> PostSettlementCalibrationExperienceRow:
    label = f"rows[{index}]"
    _require_exact_object_type(row, PostSettlementCalibrationExperienceRow, label)
    _require_exact_object_string(f"{label}.status", row.status)
    _require_exact_object_string(f"{label}.manual_next_step", row.manual_next_step)
    _require_exact_object_tuple(f"{label}.reason_codes", row.reason_codes)
    return PostSettlementCalibrationExperienceRow(
        **{field.name: getattr(row, field.name) for field in fields(row)},
    )


def _revalidated_memory_queue_item_object(
    item: PostSettlementCalibrationExperienceMemoryQueueItem,
    *,
    index: int,
) -> PostSettlementCalibrationExperienceMemoryQueueItem:
    label = f"memory_writeback_queue[{index}]"
    _require_exact_object_type(
        item,
        PostSettlementCalibrationExperienceMemoryQueueItem,
        label,
    )
    _require_exact_object_string(f"{label}.queue_priority", item.queue_priority)
    _require_exact_object_string(f"{label}.manual_next_step", item.manual_next_step)
    _require_exact_object_tuple(f"{label}.reason_codes", item.reason_codes)
    return PostSettlementCalibrationExperienceMemoryQueueItem(
        **{field.name: getattr(item, field.name) for field in fields(item)},
    )


def _revalidated_reason_code_count_object(
    item: PostSettlementCalibrationExperienceReasonCodeCount,
    *,
    index: int,
) -> PostSettlementCalibrationExperienceReasonCodeCount:
    _require_exact_object_type(
        item,
        PostSettlementCalibrationExperienceReasonCodeCount,
        f"reason_code_counts[{index}]",
    )
    return PostSettlementCalibrationExperienceReasonCodeCount(
        **{field.name: getattr(item, field.name) for field in fields(item)},
    )


def validate_post_settlement_calibration_experience_feedback_public_payload(
    payload: dict[str, Any],
) -> dict[str, Any]:
    if type(payload) is not dict:
        raise ValueError("payload must be an object")
    _require_exact_public_json_types(payload)
    _reject_unsafe_public_payload(payload)
    _require_public_payload_flags(payload)
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str or HEX_RE.fullmatch(digest) is None:
        raise ValueError("derived_validation_digest must be a sha256 digest")
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    if digest != _digest(unsigned):
        raise ValueError("derived_validation_digest must match report payload")
    report = _report_from_payload(payload)
    canonical = _public_json(report)
    if type(canonical) is not dict or canonical != payload:
        raise ValueError("payload must match canonical report payload")
    return canonical


def _report_from_payload(
    payload: dict[str, Any],
) -> PostSettlementCalibrationExperienceReport:
    _require_exact_payload_fields(
        "report payload",
        payload,
        PostSettlementCalibrationExperienceReport,
    )
    rows_value = payload["rows"]
    if type(rows_value) is not list:
        raise ValueError("rows must be a JSON array")
    queue_value = payload["memory_writeback_queue"]
    if type(queue_value) is not list:
        raise ValueError("memory_writeback_queue must be a JSON array")
    counts_value = payload["reason_code_counts"]
    if type(counts_value) is not list:
        raise ValueError("reason_code_counts must be a JSON array")
    try:
        return PostSettlementCalibrationExperienceReport(
            generated_at=_payload_datetime("generated_at", payload["generated_at"]),
            config_version=payload["config_version"],
            effective_config=_config_from_payload(payload["effective_config"]),
            event_count=_payload_decimal("event_count", payload["event_count"]),
            pass_count=_payload_decimal("pass_count", payload["pass_count"]),
            watch_count=_payload_decimal("watch_count", payload["watch_count"]),
            block_count=_payload_decimal("block_count", payload["block_count"]),
            memory_writeback_queue_count=_payload_decimal(
                "memory_writeback_queue_count",
                payload["memory_writeback_queue_count"],
            ),
            average_prediction_residual_probability=_payload_decimal(
                "average_prediction_residual_probability",
                payload["average_prediction_residual_probability"],
            ),
            average_team_calibration_drift=_payload_decimal(
                "average_team_calibration_drift",
                payload["average_team_calibration_drift"],
            ),
            max_prediction_residual_probability=_payload_decimal(
                "max_prediction_residual_probability",
                payload["max_prediction_residual_probability"],
            ),
            max_team_calibration_drift=_payload_decimal(
                "max_team_calibration_drift",
                payload["max_team_calibration_drift"],
            ),
            status=payload["status"],
            reason_codes=_payload_string_tuple("reason_codes", payload["reason_codes"]),
            reason_code_counts=tuple(
                _reason_code_count_from_payload(value, index=index)
                for index, value in enumerate(counts_value)
            ),
            manual_next_step=payload["manual_next_step"],
            rows=tuple(
                _row_from_payload(value, index=index)
                for index, value in enumerate(rows_value)
            ),
            memory_writeback_queue=tuple(
                _memory_queue_item_from_payload(value, index=index)
                for index, value in enumerate(queue_value)
            ),
            derived_validation_digest=payload["derived_validation_digest"],
            paper_only=payload["paper_only"],
            report_only=payload["report_only"],
            readonly=payload["readonly"],
        )
    except (ArithmeticError, KeyError, TypeError) as exc:
        raise ValueError("payload must materialize an exact report") from exc


def _config_from_payload(
    value: object,
) -> PostSettlementCalibrationExperienceConfig:
    if type(value) is not dict:
        raise ValueError("effective_config must be a JSON object")
    _require_exact_payload_fields(
        "effective_config",
        value,
        PostSettlementCalibrationExperienceConfig,
    )
    return PostSettlementCalibrationExperienceConfig(
        config_version=value["config_version"],
        prediction_residual_watch_threshold=_payload_decimal(
            "effective_config.prediction_residual_watch_threshold",
            value["prediction_residual_watch_threshold"],
        ),
        prediction_residual_block_threshold=_payload_decimal(
            "effective_config.prediction_residual_block_threshold",
            value["prediction_residual_block_threshold"],
        ),
        team_calibration_drift_watch_threshold=_payload_decimal(
            "effective_config.team_calibration_drift_watch_threshold",
            value["team_calibration_drift_watch_threshold"],
        ),
        team_calibration_drift_block_threshold=_payload_decimal(
            "effective_config.team_calibration_drift_block_threshold",
            value["team_calibration_drift_block_threshold"],
        ),
        evidence_readiness_pass_threshold=_payload_decimal(
            "effective_config.evidence_readiness_pass_threshold",
            value["evidence_readiness_pass_threshold"],
        ),
        evidence_readiness_block_threshold=_payload_decimal(
            "effective_config.evidence_readiness_block_threshold",
            value["evidence_readiness_block_threshold"],
        ),
        retrospective_learning_pressure_watch_threshold=_payload_decimal(
            "effective_config.retrospective_learning_pressure_watch_threshold",
            value["retrospective_learning_pressure_watch_threshold"],
        ),
        retrospective_learning_pressure_block_threshold=_payload_decimal(
            "effective_config.retrospective_learning_pressure_block_threshold",
            value["retrospective_learning_pressure_block_threshold"],
        ),
        paper_only=value["paper_only"],
        report_only=value["report_only"],
        readonly=value["readonly"],
    )


def _row_from_payload(
    value: object,
    *,
    index: int,
) -> PostSettlementCalibrationExperienceRow:
    if type(value) is not dict:
        raise ValueError(f"rows[{index}] must be a JSON object")
    _require_exact_payload_fields(
        f"rows[{index}]",
        value,
        PostSettlementCalibrationExperienceRow,
    )
    return PostSettlementCalibrationExperienceRow(
        event_key=value["event_key"],
        domain_team=value["domain_team"],
        forecast_probability=_payload_decimal(
            f"rows[{index}].forecast_probability",
            value["forecast_probability"],
        ),
        settled_outcome_probability=_payload_decimal(
            f"rows[{index}].settled_outcome_probability",
            value["settled_outcome_probability"],
        ),
        baseline_team_calibration_error=_payload_decimal(
            f"rows[{index}].baseline_team_calibration_error",
            value["baseline_team_calibration_error"],
        ),
        settled_team_calibration_error=_payload_decimal(
            f"rows[{index}].settled_team_calibration_error",
            value["settled_team_calibration_error"],
        ),
        prediction_residual_probability=_payload_decimal(
            f"rows[{index}].prediction_residual_probability",
            value["prediction_residual_probability"],
        ),
        team_calibration_drift=_payload_decimal(
            f"rows[{index}].team_calibration_drift",
            value["team_calibration_drift"],
        ),
        evidence_readiness_score=_payload_decimal(
            f"rows[{index}].evidence_readiness_score",
            value["evidence_readiness_score"],
        ),
        retrospective_learning_pressure=_payload_decimal(
            f"rows[{index}].retrospective_learning_pressure",
            value["retrospective_learning_pressure"],
        ),
        long_term_memory_writeback_required=value[
            "long_term_memory_writeback_required"
        ],
        status=value["status"],
        reason_codes=_payload_string_tuple(
            f"rows[{index}].reason_codes",
            value["reason_codes"],
        ),
        manual_next_step=value["manual_next_step"],
        paper_only=value["paper_only"],
        report_only=value["report_only"],
        readonly=value["readonly"],
    )


def _memory_queue_item_from_payload(
    value: object,
    *,
    index: int,
) -> PostSettlementCalibrationExperienceMemoryQueueItem:
    if type(value) is not dict:
        raise ValueError(f"memory_writeback_queue[{index}] must be a JSON object")
    _require_exact_payload_fields(
        f"memory_writeback_queue[{index}]",
        value,
        PostSettlementCalibrationExperienceMemoryQueueItem,
    )
    prefix = f"memory_writeback_queue[{index}]"
    return PostSettlementCalibrationExperienceMemoryQueueItem(
        event_key=value["event_key"],
        domain_team=value["domain_team"],
        prediction_residual_probability=_payload_decimal(
            f"{prefix}.prediction_residual_probability",
            value["prediction_residual_probability"],
        ),
        team_calibration_drift=_payload_decimal(
            f"{prefix}.team_calibration_drift",
            value["team_calibration_drift"],
        ),
        evidence_readiness_score=_payload_decimal(
            f"{prefix}.evidence_readiness_score",
            value["evidence_readiness_score"],
        ),
        retrospective_learning_pressure=_payload_decimal(
            f"{prefix}.retrospective_learning_pressure",
            value["retrospective_learning_pressure"],
        ),
        queue_priority=value["queue_priority"],
        reason_codes=_payload_string_tuple(
            f"{prefix}.reason_codes",
            value["reason_codes"],
        ),
        manual_next_step=value["manual_next_step"],
        paper_only=value["paper_only"],
        report_only=value["report_only"],
        readonly=value["readonly"],
    )


def _reason_code_count_from_payload(
    value: object,
    *,
    index: int,
) -> PostSettlementCalibrationExperienceReasonCodeCount:
    if type(value) is not dict:
        raise ValueError(f"reason_code_counts[{index}] must be a JSON object")
    _require_exact_payload_fields(
        f"reason_code_counts[{index}]",
        value,
        PostSettlementCalibrationExperienceReasonCodeCount,
    )
    prefix = f"reason_code_counts[{index}]"
    return PostSettlementCalibrationExperienceReasonCodeCount(
        reason_code=value["reason_code"],
        count=_payload_decimal(f"{prefix}.count", value["count"]),
        row_ratio=_payload_decimal(f"{prefix}.row_ratio", value["row_ratio"]),
        paper_only=value["paper_only"],
        report_only=value["report_only"],
        readonly=value["readonly"],
    )


def _require_exact_payload_fields(
    label: str,
    value: dict[str, Any],
    dataclass_type: type[object],
) -> None:
    expected = {field.name for field in fields(dataclass_type)}
    if set(value) != expected:
        raise ValueError(f"{label} must contain exactly the report fields")


def _payload_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        decimal = Decimal(value)
    except DecimalException as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    if not decimal.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return decimal


def _payload_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an ISO-8601 datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO-8601 datetime string") from exc
    return _as_utc(field_name, parsed)


def _payload_string_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a JSON array")
    return tuple(value)


def _row_from_event(
    event: PostSettlementCalibrationExperienceEvent,
    config: PostSettlementCalibrationExperienceConfig,
) -> PostSettlementCalibrationExperienceRow:
    residual = _abs_ratio(event.forecast_probability - event.settled_outcome_probability)
    drift = _abs_ratio(
        event.settled_team_calibration_error - event.baseline_team_calibration_error
    )
    reason_codes = _row_reason_codes(event, residual, drift, config)
    status = _status_from_reason_codes(reason_codes)
    return PostSettlementCalibrationExperienceRow(
        event_key=event.event_key,
        domain_team=event.domain_team,
        forecast_probability=event.forecast_probability,
        settled_outcome_probability=event.settled_outcome_probability,
        baseline_team_calibration_error=event.baseline_team_calibration_error,
        settled_team_calibration_error=event.settled_team_calibration_error,
        prediction_residual_probability=residual,
        team_calibration_drift=drift,
        evidence_readiness_score=event.evidence_readiness_score,
        retrospective_learning_pressure=event.retrospective_learning_pressure,
        long_term_memory_writeback_required=status != "pass",
        status=status,
        reason_codes=reason_codes,
        manual_next_step=_manual_next_step_for_status(status),
    )


def _row_reason_codes(
    event: (
        PostSettlementCalibrationExperienceEvent
        | PostSettlementCalibrationExperienceRow
    ),
    residual: Decimal,
    drift: Decimal,
    config: PostSettlementCalibrationExperienceConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if event.evidence_readiness_score < config.evidence_readiness_block_threshold:
        codes.append(READINESS_BLOCK_REASON)
    elif event.evidence_readiness_score < config.evidence_readiness_pass_threshold:
        codes.append(READINESS_WATCH_REASON)
    if residual >= config.prediction_residual_block_threshold:
        codes.append(RESIDUAL_BLOCK_REASON)
    elif residual >= config.prediction_residual_watch_threshold:
        codes.append(RESIDUAL_WATCH_REASON)
    if (
        event.retrospective_learning_pressure
        >= config.retrospective_learning_pressure_block_threshold
    ):
        codes.append(LEARNING_BLOCK_REASON)
    elif (
        event.retrospective_learning_pressure
        >= config.retrospective_learning_pressure_watch_threshold
    ):
        codes.append(LEARNING_WATCH_REASON)
    if drift >= config.team_calibration_drift_block_threshold:
        codes.append(DRIFT_BLOCK_REASON)
    elif drift >= config.team_calibration_drift_watch_threshold:
        codes.append(DRIFT_WATCH_REASON)
    if not codes:
        codes.append(READY_REASON)
    return tuple(codes)


def _queue_item_from_row(
    row: PostSettlementCalibrationExperienceRow,
) -> PostSettlementCalibrationExperienceMemoryQueueItem:
    return PostSettlementCalibrationExperienceMemoryQueueItem(
        event_key=row.event_key,
        domain_team=row.domain_team,
        prediction_residual_probability=row.prediction_residual_probability,
        team_calibration_drift=row.team_calibration_drift,
        evidence_readiness_score=row.evidence_readiness_score,
        retrospective_learning_pressure=row.retrospective_learning_pressure,
        queue_priority="high" if row.status == "block" else "medium",
        reason_codes=row.reason_codes,
        manual_next_step=row.manual_next_step,
    )


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(code.endswith("_block_threshold") or code.endswith("_block") for code in reason_codes):
        return "block"
    if reason_codes == (READY_REASON,):
        return "pass"
    return "watch"


def _manual_next_step_for_status(status: str) -> str:
    if status == "block":
        return BLOCK_NEXT_STEP
    if status == "watch":
        return WATCH_NEXT_STEP
    return PASS_NEXT_STEP


def _report_status(rows: tuple[PostSettlementCalibrationExperienceRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_manual_next_step(rows: tuple[PostSettlementCalibrationExperienceRow, ...]) -> str:
    if not rows:
        return EMPTY_NEXT_STEP
    return _manual_next_step_for_status(_report_status(rows))


def _report_reason_codes(
    rows: tuple[PostSettlementCalibrationExperienceRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    codes = {code for row in rows for code in row.reason_codes if code != READY_REASON}
    if not codes:
        return (READY_REASON,)
    return tuple(sorted(codes))


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[PostSettlementCalibrationExperienceRow, ...],
) -> tuple[PostSettlementCalibrationExperienceReasonCodeCount, ...]:
    if not rows:
        return (
            PostSettlementCalibrationExperienceReasonCodeCount(
                reason_code=EMPTY_REASON,
                count=_count(1),
                row_ratio=ZERO,
            ),
        )
    counter = Counter(code for row in rows for code in row.reason_codes)
    total = _count(len(rows))
    return tuple(
        PostSettlementCalibrationExperienceReasonCodeCount(
            reason_code=code,
            count=_count(counter[code]),
            row_ratio=_safe_ratio(_count(counter[code]), total),
        )
        for code in reason_codes
        if counter[code] > 0
    )


def _normalize_events(
    events: Iterable[PostSettlementCalibrationExperienceEvent],
) -> tuple[PostSettlementCalibrationExperienceEvent, ...]:
    if isinstance(events, (str, bytes)):
        raise ValueError("events must be an iterable of settled calibration events")
    normalized: list[PostSettlementCalibrationExperienceEvent] = []
    seen_event_keys: set[str] = set()
    for event in events:
        if type(event) is not PostSettlementCalibrationExperienceEvent:
            raise ValueError("events must contain PostSettlementCalibrationExperienceEvent")
        _require_hard_flags("event", event)
        if event.event_key in seen_event_keys:
            raise ValueError("event_key values must be unique")
        seen_event_keys.add(event.event_key)
        normalized.append(event)
    return tuple(normalized)


def _require_rows(rows: object) -> tuple[PostSettlementCalibrationExperienceRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen_event_keys: set[str] = set()
    for row in rows:
        if type(row) is not PostSettlementCalibrationExperienceRow:
            raise ValueError("rows must contain PostSettlementCalibrationExperienceRow")
        _require_hard_flags("row", row)
        if row.event_key in seen_event_keys:
            raise ValueError("row event_key values must be unique")
        seen_event_keys.add(row.event_key)
    sorted_rows = tuple(sorted(rows, key=_row_key))
    if rows != sorted_rows:
        raise ValueError("rows must be deterministically sorted")
    return rows


def _require_memory_queue(
    queue: object,
) -> tuple[PostSettlementCalibrationExperienceMemoryQueueItem, ...]:
    if type(queue) is not tuple:
        raise ValueError("memory_writeback_queue must be a tuple")
    for item in queue:
        if type(item) is not PostSettlementCalibrationExperienceMemoryQueueItem:
            raise ValueError(
                "memory_writeback_queue must contain "
                "PostSettlementCalibrationExperienceMemoryQueueItem",
            )
        _require_hard_flags("memory queue item", item)
    sorted_queue = tuple(sorted(queue, key=_queue_key))
    if queue != sorted_queue:
        raise ValueError("memory_writeback_queue must be deterministically sorted")
    return queue


def _require_reason_code_counts(
    values: object,
) -> tuple[PostSettlementCalibrationExperienceReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for value in values:
        if type(value) is not PostSettlementCalibrationExperienceReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "PostSettlementCalibrationExperienceReasonCodeCount",
            )
        _require_hard_flags("reason code count", value)
    sorted_values = tuple(sorted(values, key=lambda value: value.reason_code))
    if values != sorted_values:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return values


def _validate_row(
    row: PostSettlementCalibrationExperienceRow,
    *,
    config: PostSettlementCalibrationExperienceConfig | None = None,
) -> None:
    expected_residual = _abs_ratio(row.forecast_probability - row.settled_outcome_probability)
    if row.prediction_residual_probability != expected_residual:
        raise ValueError("prediction_residual_probability must match event probabilities")
    expected_drift = _abs_ratio(
        row.settled_team_calibration_error - row.baseline_team_calibration_error
    )
    if row.team_calibration_drift != expected_drift:
        raise ValueError("team_calibration_drift must match calibration errors")
    if config is not None:
        expected_reason_codes = _row_reason_codes(
            row,
            expected_residual,
            expected_drift,
            config,
        )
        if row.reason_codes != expected_reason_codes:
            raise ValueError("reason_codes must match effective config thresholds")
    if row.long_term_memory_writeback_required != (row.status != "pass"):
        raise ValueError("long_term_memory_writeback_required must match status")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.manual_next_step != _manual_next_step_for_status(row.status):
        raise ValueError("manual_next_step must match status")
    if row.status == "pass" and row.reason_codes != (READY_REASON,):
        raise ValueError("pass rows must contain only the ready reason code")
    if row.status != "pass" and READY_REASON in row.reason_codes:
        raise ValueError("queued rows must not contain ready reason code")


def _validate_report(report: PostSettlementCalibrationExperienceReport) -> None:
    config = _require_effective_config(report.effective_config)
    if report.config_version != config.config_version:
        raise ValueError("config_version must match effective_config")
    rows = _require_rows(report.rows)
    for row in rows:
        _require_hard_flags("row", row)
        _validate_row(row, config=config)
    queue = tuple(
        sorted(
            (
                _queue_item_from_row(row)
                for row in rows
                if row.long_term_memory_writeback_required
            ),
            key=_queue_key,
        ),
    )
    expected_values = {
        "event_count": _count(len(rows)),
        "pass_count": _count(sum(row.status == "pass" for row in rows)),
        "watch_count": _count(sum(row.status == "watch" for row in rows)),
        "block_count": _count(sum(row.status == "block" for row in rows)),
        "memory_writeback_queue_count": _count(len(queue)),
        "average_prediction_residual_probability": _average(
            row.prediction_residual_probability for row in rows
        ),
        "average_team_calibration_drift": _average(row.team_calibration_drift for row in rows),
        "max_prediction_residual_probability": _max_ratio(
            row.prediction_residual_probability for row in rows
        ),
        "max_team_calibration_drift": _max_ratio(row.team_calibration_drift for row in rows),
    }
    for field_name, expected in expected_values.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, rows):
        raise ValueError("reason_code_counts must match rows")
    if report.manual_next_step != _report_manual_next_step(rows):
        raise ValueError("manual_next_step must match rows")
    if report.memory_writeback_queue != queue:
        raise ValueError("memory_writeback_queue must match queued rows")


def _row_key(row: PostSettlementCalibrationExperienceRow) -> tuple[Decimal, Decimal, str]:
    return (
        -row.prediction_residual_probability,
        -row.team_calibration_drift,
        row.event_key,
    )


def _queue_key(
    item: PostSettlementCalibrationExperienceMemoryQueueItem,
) -> tuple[int, Decimal, Decimal, str]:
    return (
        QUEUE_PRIORITY_RANKS[item.queue_priority],
        -item.prediction_residual_probability,
        -item.team_calibration_drift,
        item.event_key,
    )


def _average(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    return _safe_ratio(sum(items, ZERO), _count(len(items)))


def _max_ratio(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    return max(items)


def _abs_ratio(value: Decimal) -> Decimal:
    return _require_ratio("absolute probability", abs(value))


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANTUM)


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count source must be a nonnegative int")
    return Decimal(value).quantize(QUANTUM)


def _require_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized.to_integral_value().quantize(QUANTUM)


def _require_exact_object_type(
    value: object,
    expected_type: type[object],
    label: str,
) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be an exact {expected_type.__name__}")


def _require_exact_object_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an exact string")


def _require_exact_object_tuple(field_name: str, value: object) -> None:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")


def _require_effective_config(
    value: object,
) -> PostSettlementCalibrationExperienceConfig:
    if type(value) is not PostSettlementCalibrationExperienceConfig:
        raise ValueError(
            "effective_config must be a PostSettlementCalibrationExperienceConfig",
        )
    canonical = PostSettlementCalibrationExperienceConfig(
        **{field.name: getattr(value, field.name) for field in fields(value)},
    )
    if _public_json(value) != _public_json(canonical):
        raise ValueError("effective_config must be canonical")
    return value


def _require_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be a ratio between 0 and 1")
    return normalized


def _require_binary_probability(field_name: str, value: object) -> Decimal:
    normalized = _require_ratio(field_name, value)
    if normalized not in (ZERO, ONE):
        raise ValueError(f"{field_name} must be a settled binary probability")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        if isinstance(value, Decimal):
            raise ValueError(f"{field_name} must be an exact Decimal")
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM)


def _require_public_key(field_name: str, value: object) -> str:
    _require_public_string(field_name, value)
    assert isinstance(value, str)
    if PUBLIC_KEY_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a public key")
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_KEY_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public text")
    return value


def _require_public_code(field_name: str, value: object) -> str:
    _require_public_string(field_name, value)
    assert isinstance(value, str)
    if PUBLIC_CODE_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a public code")
    return value


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value or any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must be canonical nonblank public text")
    if value.lower() != value:
        raise ValueError(f"{field_name} must be lowercase")
    if any(fragment in value.lower() for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public text")
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str or REASON_CODE_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a reason code")
    return value


def _require_reason_codes(
    value: object,
    *,
    allow_repeats: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not value:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    for reason_code in value:
        _require_reason_code("reason_codes", reason_code)
        if not allow_repeats and reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
    return value


def _require_status(field_name: str, value: object) -> None:
    if value not in POST_SETTLEMENT_CALIBRATION_EXPERIENCE_STATUSES:
        raise ValueError(f"{field_name} must be a supported status")


def _require_manual_next_step(field_name: str, value: object) -> None:
    if value not in (PASS_NEXT_STEP, WATCH_NEXT_STEP, BLOCK_NEXT_STEP, EMPTY_NEXT_STEP):
        raise ValueError(f"{field_name} must be a supported manual next step")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True in public payload")


def _require_or_set_digest(report: PostSettlementCalibrationExperienceReport) -> None:
    expected = _digest(_payload_without_digest(report))
    if report.derived_validation_digest:
        if HEX_RE.fullmatch(report.derived_validation_digest) is None:
            raise ValueError("derived_validation_digest must be a sha256 digest")
        if report.derived_validation_digest != expected:
            raise ValueError("derived_validation_digest must match report payload")
    else:
        object.__setattr__(report, "derived_validation_digest", expected)


def _payload_without_digest(report: PostSettlementCalibrationExperienceReport) -> dict[str, Any]:
    return {
        field.name: getattr(report, field.name)
        for field in fields(report)
        if field.name != "derived_validation_digest"
    }


def _digest(value: object) -> str:
    payload = _public_json(value)
    _reject_unsafe_public_payload(payload)
    _reject_public_numeric_values(payload)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _public_json(value: object) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _public_json(asdict(value))
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("public Decimal value must be finite")
        return str(value)
    if isinstance(value, float):
        raise ValueError("public value must not be a float")
    if isinstance(value, int) and not isinstance(value, bool):
        raise ValueError("public value must not be an int")
    if type(value) in (str, bool):
        return value
    if isinstance(value, str):
        raise ValueError("public string values must be exact strings")
    if isinstance(value, Mapping):
        converted: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            converted[key] = _public_json(item)
        return converted
    if isinstance(value, tuple):
        return [_public_json(item) for item in value]
    if isinstance(value, list):
        return [_public_json(item) for item in value]
    raise ValueError("public value must be scalar or container")


def _reject_unsafe_public_payload(value: object) -> None:
    encoded = json.dumps(value, sort_keys=True).lower()
    if any(fragment in encoded for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError("unsafe public payload")


def _require_exact_public_json_types(value: object) -> None:
    if value is None or type(value) in (str, bool):
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be exact strings")
            _require_exact_public_json_types(item)
        return
    if type(value) is list:
        for item in value:
            _require_exact_public_json_types(item)
        return
    if isinstance(value, (int, float, Decimal)):
        raise ValueError("public numeric values must be strings")
    if isinstance(value, str):
        raise ValueError("public string values must be exact strings")
    raise ValueError("public payload values must use exact JSON types")


def _reject_public_numeric_values(value: object) -> None:
    if type(value) in (int, float, Decimal):
        raise ValueError("public numeric values must be strings")
    if isinstance(value, Mapping):
        for item in value.values():
            _reject_public_numeric_values(item)
    elif isinstance(value, list):
        for item in value:
            _reject_public_numeric_values(item)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        if isinstance(value, datetime):
            raise ValueError(f"{field_name} must be an exact datetime")
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)
