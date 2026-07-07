"""Pure Phase 1 specialist source reliability learning queue."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_TEAM_SPECIALIST_SOURCE_RELIABILITY_LEARNING_QUEUE_V2_CONFIG_VERSION = (
    "team-specialist-source-reliability-learning-queue-v2-phase-1"
)
TEAM_SPECIALIST_SOURCE_RELIABILITY_LEARNING_QUEUE_V2_STATUSES = (
    "clear",
    "watch",
    "critical",
)

LOW_SOURCE_RELIABILITY_REASON = "low_source_reliability"
STALE_SOURCE_RELIABILITY_REASON = "stale_source_reliability"
CALIBRATION_FEEDBACK_BOOST_REASON = "calibration_feedback_boost"
LOW_RELIABILITY_SAMPLE_SIZE_REASON = "low_reliability_sample_size"
SOURCE_RELIABILITY_LEARNING_CLEAR_REASON = "source_reliability_learning_clear"
REPORT_CRITICAL_REASON = "source_reliability_learning_queue_critical"
REPORT_WATCH_REASON = "source_reliability_learning_queue_watch"
EMPTY_SOURCES_REASON = "source_reliability_learning_queue_empty_sources"

ITEM_REASON_CODES = (
    LOW_SOURCE_RELIABILITY_REASON,
    STALE_SOURCE_RELIABILITY_REASON,
    CALIBRATION_FEEDBACK_BOOST_REASON,
    LOW_RELIABILITY_SAMPLE_SIZE_REASON,
    SOURCE_RELIABILITY_LEARNING_CLEAR_REASON,
)
REPORT_REASON_CODES = (
    REPORT_CRITICAL_REASON,
    REPORT_WATCH_REASON,
    LOW_SOURCE_RELIABILITY_REASON,
    STALE_SOURCE_RELIABILITY_REASON,
    CALIBRATION_FEEDBACK_BOOST_REASON,
    LOW_RELIABILITY_SAMPLE_SIZE_REASON,
    SOURCE_RELIABILITY_LEARNING_CLEAR_REASON,
    EMPTY_SOURCES_REASON,
)

COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SAFE_REF_PREFIXES = ("public:", "source:", "reliability:", "calibration:", "lesson:")
PUBLIC_TEXT_HEXES = (
    "6c697665",
    "61757468",
    "77616c6c6574",
    "6f72646572",
    "6e6574776f726b",
    "6461746162617365",
    "70657273697374",
    "7369676e696e67",
    "6d75746174696f6e",
    "627579",
    "73656c6c",
    "7472616465",
)
PUBLIC_TEXT_BLOCKS = tuple(bytes.fromhex(value).decode("ascii") for value in PUBLIC_TEXT_HEXES)


@dataclass(frozen=True)
class TeamSpecialistSourceReliabilityLearningQueueV2Config:
    config_version: str = (
        DEFAULT_TEAM_SPECIALIST_SOURCE_RELIABILITY_LEARNING_QUEUE_V2_CONFIG_VERSION
    )
    low_reliability_weight: Decimal = Decimal("0.450000")
    stale_reliability_weight: Decimal = Decimal("0.250000")
    calibration_feedback_weight: Decimal = Decimal("0.200000")
    sample_size_weight: Decimal = Decimal("0.100000")
    stale_review_threshold_seconds: Decimal = Decimal("604800.000000")
    max_stale_review_seconds: Decimal = Decimal("2419200.000000")
    min_sample_count: Decimal = Decimal("5")
    calibration_feedback_boost_count: Decimal = Decimal("3")
    watch_priority_score: Decimal = Decimal("0.250000")
    critical_priority_score: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "low_reliability_weight",
            "stale_reliability_weight",
            "calibration_feedback_weight",
            "sample_size_weight",
            "watch_priority_score",
            "critical_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "stale_review_threshold_seconds",
            "max_stale_review_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_sample_count",
            "calibration_feedback_boost_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        _require_ratio_total(
            self.low_reliability_weight,
            self.stale_reliability_weight,
            self.calibration_feedback_weight,
            self.sample_size_weight,
        )
        if self.stale_review_threshold_seconds >= self.max_stale_review_seconds:
            raise ValueError(
                "stale_review_threshold_seconds must be less than max_stale_review_seconds",
            )
        if self.watch_priority_score > self.critical_priority_score:
            raise ValueError(
                "watch_priority_score must be less than or equal to critical_priority_score",
            )
        require_paper_only_flags("source reliability learning queue config", self)


@dataclass(frozen=True)
class TeamSpecialistSourceReliabilityLearningQueueInputV2:
    team_id: str
    specialist_id: str
    source_id: str
    source_family: str
    observed_at: datetime
    reliability_last_reviewed_at: datetime
    reliability_score: Decimal
    sample_count: Decimal
    calibration_feedback_count: Decimal
    public_source_refs: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("team_id", "specialist_id", "source_id", "source_family"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reliability_last_reviewed_at",
            _as_utc("reliability_last_reviewed_at", self.reliability_last_reviewed_at),
        )
        object.__setattr__(
            self,
            "reliability_score",
            _normalize_ratio("reliability_score", self.reliability_score),
        )
        for field_name in ("sample_count", "calibration_feedback_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "public_source_refs",
            _normalize_public_refs("public_source_refs", self.public_source_refs),
        )
        require_paper_only_flags("source reliability learning queue input", self)


@dataclass(frozen=True)
class TeamSpecialistSourceReliabilityLearningQueueItemV2:
    team_id: str
    specialist_id: str
    source_id: str
    source_family: str
    observation_count: Decimal
    latest_observed_at: datetime
    oldest_reliability_reviewed_at: datetime
    min_reliability_score: Decimal
    sample_count: Decimal
    calibration_feedback_count: Decimal
    low_reliability_component: Decimal
    stale_reliability_component: Decimal
    calibration_feedback_component: Decimal
    sample_size_gap: Decimal
    priority_score: Decimal
    queue_status: str
    public_source_refs: tuple[str, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("team_id", "specialist_id", "source_id", "source_family"):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "observation_count",
            "sample_count",
            "calibration_feedback_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        object.__setattr__(
            self,
            "oldest_reliability_reviewed_at",
            _as_utc("oldest_reliability_reviewed_at", self.oldest_reliability_reviewed_at),
        )
        for field_name in (
            "min_reliability_score",
            "low_reliability_component",
            "stale_reliability_component",
            "calibration_feedback_component",
            "sample_size_gap",
            "priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("queue_status", self.queue_status)
        object.__setattr__(
            self,
            "public_source_refs",
            _normalize_public_refs("public_source_refs", self.public_source_refs),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ITEM_REASON_CODES),
        )
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        if self.derived_validation_digest != _item_digest(self):
            raise ValueError("derived_validation_digest must match queue item fields")
        _validate_item(self)
        require_paper_only_flags("source reliability learning queue item", self)


@dataclass(frozen=True)
class TeamSpecialistSourceReliabilityLearningQueueReportV2:
    generated_at: datetime
    config_version: str
    team_count: Decimal
    specialist_team_count: Decimal
    source_count: Decimal
    observation_count: Decimal
    critical_count: Decimal
    watch_count: Decimal
    clear_count: Decimal
    average_priority_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    queue_items: tuple[TeamSpecialistSourceReliabilityLearningQueueItemV2, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "team_count",
            "specialist_team_count",
            "source_count",
            "observation_count",
            "critical_count",
            "watch_count",
            "clear_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_priority_score",
            _normalize_ratio("average_priority_score", self.average_priority_score),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(self, "queue_items", _normalize_queue_items(self.queue_items))
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        if self.derived_validation_digest != _report_digest(self):
            raise ValueError("derived_validation_digest must match report fields")
        _validate_report(self)
        require_paper_only_flags("source reliability learning queue report", self)


def build_team_specialist_source_reliability_learning_queue_v2(
    inputs: list[TeamSpecialistSourceReliabilityLearningQueueInputV2]
    | tuple[TeamSpecialistSourceReliabilityLearningQueueInputV2, ...],
    *,
    config: TeamSpecialistSourceReliabilityLearningQueueV2Config,
    generated_at: datetime,
) -> TeamSpecialistSourceReliabilityLearningQueueReportV2:
    if type(config) is not TeamSpecialistSourceReliabilityLearningQueueV2Config:
        raise ValueError(
            "config must be a TeamSpecialistSourceReliabilityLearningQueueV2Config",
        )
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _normalize_inputs(inputs)
    _validate_input_dates(rows, generated_at_utc)
    queue_items = tuple(
        sorted(
            (
                _queue_item(team_id, specialist_id, source_id, source_family, group, config, generated_at_utc)
                for team_id, specialist_id, source_id, source_family, group in _input_groups(rows)
            ),
            key=_queue_item_sort_key,
        ),
    )
    report_parts = dict(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        team_count=_count(len({item.team_id for item in queue_items})),
        specialist_team_count=_count(
            len({(item.team_id, item.specialist_id) for item in queue_items}),
        ),
        source_count=_count(len({item.source_id for item in queue_items})),
        observation_count=_sum_items(queue_items, "observation_count"),
        critical_count=_count(sum(1 for item in queue_items if item.queue_status == "critical")),
        watch_count=_count(sum(1 for item in queue_items if item.queue_status == "watch")),
        clear_count=_count(sum(1 for item in queue_items if item.queue_status == "clear")),
        average_priority_score=_average_priority_score(queue_items),
        status=_report_status(queue_items),
        reason_codes=_report_reason_codes(queue_items),
        queue_items=queue_items,
        paper_only=True,
        report_only=True,
        readonly=True,
    )
    return TeamSpecialistSourceReliabilityLearningQueueReportV2(
        **report_parts,
        derived_validation_digest=_digest_public(report_parts),
    )


def team_specialist_source_reliability_learning_queue_v2_payload(
    report: TeamSpecialistSourceReliabilityLearningQueueReportV2,
) -> dict[str, Any]:
    if type(report) is not TeamSpecialistSourceReliabilityLearningQueueReportV2:
        raise ValueError(
            "report must be a TeamSpecialistSourceReliabilityLearningQueueReportV2",
        )
    require_paper_only_flags("report", report)
    if report.derived_validation_digest != _report_digest(report):
        raise ValueError("derived_validation_digest must match report fields")
    payload = json_ready_no_floats(report)
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")
    _reject_public_payload("source reliability learning queue payload", payload)
    return _tupleify_payload_collections(payload)


def _normalize_inputs(
    inputs: list[TeamSpecialistSourceReliabilityLearningQueueInputV2]
    | tuple[TeamSpecialistSourceReliabilityLearningQueueInputV2, ...],
) -> tuple[TeamSpecialistSourceReliabilityLearningQueueInputV2, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(inputs)
    for row in rows:
        if type(row) is not TeamSpecialistSourceReliabilityLearningQueueInputV2:
            raise ValueError(
                "inputs must contain TeamSpecialistSourceReliabilityLearningQueueInputV2 values",
            )
        require_paper_only_flags("input", row)
    return rows


def _validate_input_dates(
    rows: tuple[TeamSpecialistSourceReliabilityLearningQueueInputV2, ...],
    generated_at: datetime,
) -> None:
    for row in rows:
        if row.observed_at > generated_at:
            raise ValueError("observed_at must be on or before generated_at")
        if row.reliability_last_reviewed_at > generated_at:
            raise ValueError("reliability_last_reviewed_at must be on or before generated_at")


def _input_groups(
    rows: tuple[TeamSpecialistSourceReliabilityLearningQueueInputV2, ...],
) -> tuple[
    tuple[
        str,
        str,
        str,
        str,
        tuple[TeamSpecialistSourceReliabilityLearningQueueInputV2, ...],
    ],
    ...,
]:
    keys = tuple(
        sorted(
            {
                (row.team_id, row.specialist_id, row.source_id, row.source_family)
                for row in rows
            },
        ),
    )
    return tuple(
        (
            team_id,
            specialist_id,
            source_id,
            source_family,
            tuple(
                row
                for row in rows
                if (
                    row.team_id,
                    row.specialist_id,
                    row.source_id,
                    row.source_family,
                )
                == (team_id, specialist_id, source_id, source_family)
            ),
        )
        for team_id, specialist_id, source_id, source_family in keys
    )


def _queue_item(
    team_id: str,
    specialist_id: str,
    source_id: str,
    source_family: str,
    rows: tuple[TeamSpecialistSourceReliabilityLearningQueueInputV2, ...],
    config: TeamSpecialistSourceReliabilityLearningQueueV2Config,
    generated_at: datetime,
) -> TeamSpecialistSourceReliabilityLearningQueueItemV2:
    min_reliability_score = min(row.reliability_score for row in rows)
    sample_count = _sum_inputs(rows, "sample_count")
    calibration_feedback_count = _sum_inputs(rows, "calibration_feedback_count")
    low_component = _low_reliability_component(min_reliability_score)
    stale_component = max(_stale_reliability_component(row, config, generated_at) for row in rows)
    calibration_component = _calibration_feedback_component(calibration_feedback_count, config)
    sample_gap = _sample_size_gap(sample_count, config)
    priority_score = _priority_score(
        low_component,
        stale_component,
        calibration_component,
        sample_gap,
        config,
    )
    queue_status = _queue_status(priority_score, config)
    public_source_refs = tuple(
        sorted({reference for row in rows for reference in row.public_source_refs}),
    )
    item_parts = dict(
        team_id=team_id,
        specialist_id=specialist_id,
        source_id=source_id,
        source_family=source_family,
        observation_count=_count(len(rows)),
        latest_observed_at=max(row.observed_at for row in rows),
        oldest_reliability_reviewed_at=min(row.reliability_last_reviewed_at for row in rows),
        min_reliability_score=min_reliability_score,
        sample_count=sample_count,
        calibration_feedback_count=calibration_feedback_count,
        low_reliability_component=low_component,
        stale_reliability_component=stale_component,
        calibration_feedback_component=calibration_component,
        sample_size_gap=sample_gap,
        priority_score=priority_score,
        queue_status=queue_status,
        public_source_refs=public_source_refs,
        reason_codes=_item_reason_codes(
            queue_status,
            low_component,
            stale_component,
            calibration_component,
            sample_gap,
        ),
        paper_only=True,
        report_only=True,
        readonly=True,
    )
    return TeamSpecialistSourceReliabilityLearningQueueItemV2(
        **item_parts,
        derived_validation_digest=_digest_public(item_parts),
    )


def _low_reliability_component(reliability_score: Decimal) -> Decimal:
    return _clamp_ratio(ONE_RATIO - reliability_score)


def _stale_reliability_component(
    row: TeamSpecialistSourceReliabilityLearningQueueInputV2,
    config: TeamSpecialistSourceReliabilityLearningQueueV2Config,
    generated_at: datetime,
) -> Decimal:
    age_seconds = _age_seconds(generated_at, row.reliability_last_reviewed_at)
    if age_seconds <= config.stale_review_threshold_seconds:
        return ZERO_RATIO
    if age_seconds >= config.max_stale_review_seconds:
        return ONE_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            (age_seconds - config.stale_review_threshold_seconds)
            / (config.max_stale_review_seconds - config.stale_review_threshold_seconds),
        )


def _calibration_feedback_component(
    calibration_feedback_count: Decimal,
    config: TeamSpecialistSourceReliabilityLearningQueueV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            calibration_feedback_count / config.calibration_feedback_boost_count,
        )


def _sample_size_gap(
    sample_count: Decimal,
    config: TeamSpecialistSourceReliabilityLearningQueueV2Config,
) -> Decimal:
    if sample_count >= config.min_sample_count:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio((config.min_sample_count - sample_count) / config.min_sample_count)


def _priority_score(
    low_component: Decimal,
    stale_component: Decimal,
    calibration_component: Decimal,
    sample_gap: Decimal,
    config: TeamSpecialistSourceReliabilityLearningQueueV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            low_component * config.low_reliability_weight
            + stale_component * config.stale_reliability_weight
            + calibration_component * config.calibration_feedback_weight
            + sample_gap * config.sample_size_weight,
        )


def _item_reason_codes(
    queue_status: str,
    low_component: Decimal,
    stale_component: Decimal,
    calibration_component: Decimal,
    sample_gap: Decimal,
) -> tuple[str, ...]:
    if queue_status == "clear":
        return (SOURCE_RELIABILITY_LEARNING_CLEAR_REASON,)
    codes: set[str] = set()
    if low_component > ZERO_RATIO:
        codes.add(LOW_SOURCE_RELIABILITY_REASON)
    if stale_component > ZERO_RATIO:
        codes.add(STALE_SOURCE_RELIABILITY_REASON)
    if calibration_component > ZERO_RATIO:
        codes.add(CALIBRATION_FEEDBACK_BOOST_REASON)
    if sample_gap > ZERO_RATIO:
        codes.add(LOW_RELIABILITY_SAMPLE_SIZE_REASON)
    if not codes:
        codes.add(SOURCE_RELIABILITY_LEARNING_CLEAR_REASON)
    return tuple(code for code in ITEM_REASON_CODES if code in codes)


def _report_reason_codes(
    items: tuple[TeamSpecialistSourceReliabilityLearningQueueItemV2, ...],
) -> tuple[str, ...]:
    if not items:
        return (EMPTY_SOURCES_REASON,)
    codes = {
        code
        for item in items
        if item.queue_status != "clear"
        for code in item.reason_codes
    }
    status = _report_status(items)
    if status == "critical":
        codes.add(REPORT_CRITICAL_REASON)
    elif status == "watch":
        codes.add(REPORT_WATCH_REASON)
    if not codes:
        codes.add(SOURCE_RELIABILITY_LEARNING_CLEAR_REASON)
    return tuple(code for code in REPORT_REASON_CODES if code in codes)


def _queue_status(
    priority_score: Decimal,
    config: TeamSpecialistSourceReliabilityLearningQueueV2Config,
) -> str:
    if priority_score >= config.critical_priority_score:
        return "critical"
    if priority_score >= config.watch_priority_score:
        return "watch"
    return "clear"


def _report_status(
    items: tuple[TeamSpecialistSourceReliabilityLearningQueueItemV2, ...],
) -> str:
    if not items:
        return "watch"
    if any(item.queue_status == "critical" for item in items):
        return "critical"
    if any(item.queue_status == "watch" for item in items):
        return "watch"
    return "clear"


def _queue_item_sort_key(
    item: TeamSpecialistSourceReliabilityLearningQueueItemV2,
) -> tuple[int, Decimal, str, str, str]:
    return (
        -_status_rank(item.queue_status),
        -item.priority_score,
        item.team_id,
        item.specialist_id,
        item.source_id,
    )


def _status_rank(status: str) -> int:
    if status == "critical":
        return 2
    if status == "watch":
        return 1
    return 0


def _age_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    with localcontext(DECIMAL_CONTEXT):
        return (
            Decimal(delta.days) * SECONDS_PER_DAY
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / Decimal("1000000"))
        ).quantize(RATIO_QUANTUM)


def _sum_inputs(
    rows: tuple[TeamSpecialistSourceReliabilityLearningQueueInputV2, ...],
    field_name: str,
) -> Decimal:
    return _normalize_count(
        field_name,
        sum((getattr(row, field_name) for row in rows), ZERO_COUNT),
    )


def _sum_items(
    items: tuple[TeamSpecialistSourceReliabilityLearningQueueItemV2, ...],
    field_name: str,
) -> Decimal:
    return _normalize_count(
        field_name,
        sum((getattr(item, field_name) for item in items), ZERO_COUNT),
    )


def _average_priority_score(
    items: tuple[TeamSpecialistSourceReliabilityLearningQueueItemV2, ...],
) -> Decimal:
    if not items:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            sum((item.priority_score for item in items), ZERO_RATIO) / Decimal(len(items)),
        )


def _validate_item(item: TeamSpecialistSourceReliabilityLearningQueueItemV2) -> None:
    if item.observation_count <= ZERO_COUNT:
        raise ValueError("observation_count must be positive")
    if item.reason_codes != _item_reason_codes(
        item.queue_status,
        item.low_reliability_component,
        item.stale_reliability_component,
        item.calibration_feedback_component,
        item.sample_size_gap,
    ):
        raise ValueError("reason_codes must match queue item components")


def _validate_report(report: TeamSpecialistSourceReliabilityLearningQueueReportV2) -> None:
    if report.team_count != _count(len({item.team_id for item in report.queue_items})):
        raise ValueError("team_count must match queue_items")
    if report.specialist_team_count != _count(
        len({(item.team_id, item.specialist_id) for item in report.queue_items}),
    ):
        raise ValueError("specialist_team_count must match queue_items")
    if report.source_count != _count(len({item.source_id for item in report.queue_items})):
        raise ValueError("source_count must match queue_items")
    if report.observation_count != _sum_items(report.queue_items, "observation_count"):
        raise ValueError("observation_count must match queue_items")
    if report.critical_count != _count(
        sum(1 for item in report.queue_items if item.queue_status == "critical"),
    ):
        raise ValueError("critical_count must match queue_items")
    if report.watch_count != _count(
        sum(1 for item in report.queue_items if item.queue_status == "watch"),
    ):
        raise ValueError("watch_count must match queue_items")
    if report.clear_count != _count(
        sum(1 for item in report.queue_items if item.queue_status == "clear"),
    ):
        raise ValueError("clear_count must match queue_items")
    if report.average_priority_score != _average_priority_score(report.queue_items):
        raise ValueError("average_priority_score must match queue_items")
    if report.status != _report_status(report.queue_items):
        raise ValueError("status must match queue_items")
    if report.reason_codes != _report_reason_codes(report.queue_items):
        raise ValueError("reason_codes must match queue_items")
    if report.queue_items != tuple(sorted(report.queue_items, key=_queue_item_sort_key)):
        raise ValueError("queue_items must use deterministic sequence")


def _normalize_queue_items(
    items: tuple[TeamSpecialistSourceReliabilityLearningQueueItemV2, ...],
) -> tuple[TeamSpecialistSourceReliabilityLearningQueueItemV2, ...]:
    if type(items) is not tuple:
        raise ValueError("queue_items must be a tuple")
    for item in items:
        if type(item) is not TeamSpecialistSourceReliabilityLearningQueueItemV2:
            raise ValueError(
                "queue_items must contain TeamSpecialistSourceReliabilityLearningQueueItemV2 values",
            )
        require_paper_only_flags("queue item", item)
    return items


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must contain reason code strings")
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    normalized: list[str] = []
    for item in value:
        if type(item) is not str or item not in allowed_reason_codes:
            raise ValueError(f"{field_name} contains an unknown reason code")
        if item in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        normalized.append(item)
        seen.add(item)
    expected = tuple(code for code in allowed_reason_codes if code in seen)
    if tuple(normalized) != expected:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return tuple(normalized)


def _normalize_public_refs(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must contain strings")
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    normalized: list[str] = []
    for item in value:
        _require_public_string(field_name, item)
        if not item.startswith(SAFE_REF_PREFIXES):
            raise ValueError(f"{field_name} contains an unsupported public reference")
        normalized.append(item)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    return tuple(normalized)


def _normalize_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return value.quantize(COUNT_QUANTUM)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    value = _normalize_count(field_name, value)
    if value <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return value


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value <= ZERO_RATIO:
        raise ValueError(f"{field_name} must be positive")
    return value.quantize(RATIO_QUANTUM)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_RATIO or value > ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return value.quantize(RATIO_QUANTUM)


def _clamp_ratio(value: Decimal) -> Decimal:
    if value < ZERO_RATIO:
        value = ZERO_RATIO
    if value > ONE_RATIO:
        value = ONE_RATIO
    return value.quantize(RATIO_QUANTUM)


def _require_ratio_total(*values: Decimal) -> None:
    with localcontext(DECIMAL_CONTEXT):
        if sum(values, ZERO_RATIO).quantize(RATIO_QUANTUM) != ONE_RATIO:
            raise ValueError("priority weights must sum to 1")


def _require_status(field_name: str, value: object) -> None:
    if value not in TEAM_SPECIALIST_SOURCE_RELIABILITY_LEARNING_QUEUE_V2_STATUSES:
        raise ValueError(f"{field_name} must be clear, watch, or critical")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _reject_public_text(field_name, value)


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")


def _item_digest(item: TeamSpecialistSourceReliabilityLearningQueueItemV2) -> str:
    return _digest_public(_item_digest_parts(item))


def _report_digest(report: TeamSpecialistSourceReliabilityLearningQueueReportV2) -> str:
    return _digest_public(_report_digest_parts(report))


def _item_digest_parts(
    item: TeamSpecialistSourceReliabilityLearningQueueItemV2,
) -> dict[str, object]:
    return {
        "team_id": item.team_id,
        "specialist_id": item.specialist_id,
        "source_id": item.source_id,
        "source_family": item.source_family,
        "observation_count": item.observation_count,
        "latest_observed_at": item.latest_observed_at,
        "oldest_reliability_reviewed_at": item.oldest_reliability_reviewed_at,
        "min_reliability_score": item.min_reliability_score,
        "sample_count": item.sample_count,
        "calibration_feedback_count": item.calibration_feedback_count,
        "low_reliability_component": item.low_reliability_component,
        "stale_reliability_component": item.stale_reliability_component,
        "calibration_feedback_component": item.calibration_feedback_component,
        "sample_size_gap": item.sample_size_gap,
        "priority_score": item.priority_score,
        "queue_status": item.queue_status,
        "public_source_refs": item.public_source_refs,
        "reason_codes": item.reason_codes,
        "paper_only": item.paper_only,
        "report_only": item.report_only,
        "readonly": item.readonly,
    }


def _report_digest_parts(
    report: TeamSpecialistSourceReliabilityLearningQueueReportV2,
) -> dict[str, object]:
    return {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "team_count": report.team_count,
        "specialist_team_count": report.specialist_team_count,
        "source_count": report.source_count,
        "observation_count": report.observation_count,
        "critical_count": report.critical_count,
        "watch_count": report.watch_count,
        "clear_count": report.clear_count,
        "average_priority_score": report.average_priority_score,
        "status": report.status,
        "reason_codes": report.reason_codes,
        "queue_items": report.queue_items,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _digest_public(value: object) -> str:
    ready = _digest_ready(value)
    _reject_public_payload("derived validation digest", ready)
    return hashlib.sha256(
        json.dumps(ready, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()


def _digest_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _digest_ready(asdict(value))
    return json_ready_no_floats(value)


def _reject_public_payload(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public key in {label}")
            if _public_text_has_block(key):
                raise ValueError(f"unsafe public key in {label}")
            _reject_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_payload(label, item)
        return
    if type(value) is float:
        raise ValueError(f"unsafe public value in {label}")
    if type(value) is str:
        _reject_public_text(label, value)


def _reject_public_text(field_name: str, value: str) -> None:
    if _public_text_has_block(value):
        raise ValueError(f"unsafe public value in {field_name}")


def _public_text_has_block(value: str) -> bool:
    normalized = "".join(character for character in value.lower() if character.isalnum())
    return any(block in normalized for block in PUBLIC_TEXT_BLOCKS)


def _tupleify_payload_collections(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _tupleify_payload_collections(item) for key, item in value.items()}
    if isinstance(value, list):
        return tuple(_tupleify_payload_collections(item) for item in value)
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


__all__ = (
    "DEFAULT_TEAM_SPECIALIST_SOURCE_RELIABILITY_LEARNING_QUEUE_V2_CONFIG_VERSION",
    "TEAM_SPECIALIST_SOURCE_RELIABILITY_LEARNING_QUEUE_V2_STATUSES",
    "TeamSpecialistSourceReliabilityLearningQueueV2Config",
    "TeamSpecialistSourceReliabilityLearningQueueInputV2",
    "TeamSpecialistSourceReliabilityLearningQueueItemV2",
    "TeamSpecialistSourceReliabilityLearningQueueReportV2",
    "build_team_specialist_source_reliability_learning_queue_v2",
    "team_specialist_source_reliability_learning_queue_v2_payload",
)
