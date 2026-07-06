"""Pure Phase 1 specialist research queue learning value report."""

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


DEFAULT_TEAM_SPECIALIST_RESEARCH_QUEUE_LEARNING_VALUE_V2_CONFIG_VERSION = (
    "team-specialist-research-queue-learning-value-v2-phase-1"
)

TEAM_SPECIALIST_RESEARCH_QUEUE_LEARNING_VALUE_V2_STATUSES = (
    "empty",
    "low_value",
    "watch",
    "high_value",
)

HIGH_VALUE_REASON = "high_value_learning_opportunity"
WATCH_REASON = "learning_value_watch"
LOW_VALUE_REASON = "low_value_learning_signal"
STALE_LEARNING_REASON = "stale_learning_penalty"
HIGH_IMPACT_FEEDBACK_REASON = "high_impact_feedback_boost"
EMPTY_QUEUE_REASON = "empty_research_queue"

ROW_REASON_CODES = (
    HIGH_VALUE_REASON,
    WATCH_REASON,
    LOW_VALUE_REASON,
    STALE_LEARNING_REASON,
    HIGH_IMPACT_FEEDBACK_REASON,
)
REPORT_REASON_CODES = (
    HIGH_VALUE_REASON,
    WATCH_REASON,
    STALE_LEARNING_REASON,
    HIGH_IMPACT_FEEDBACK_REASON,
    LOW_VALUE_REASON,
    EMPTY_QUEUE_REASON,
)

COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
SECONDS_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SAFE_REF_PREFIXES = ("public:", "research:", "queue:", "lesson:")
UNSAFE_PUBLIC_TEXT_HEXES = (
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
UNSAFE_PUBLIC_TEXT_BLOCKS = tuple(
    bytes.fromhex(value).decode("ascii") for value in UNSAFE_PUBLIC_TEXT_HEXES
)


@dataclass(frozen=True)
class TeamSpecialistResearchQueueLearningValueConfigV2:
    config_version: str = DEFAULT_TEAM_SPECIALIST_RESEARCH_QUEUE_LEARNING_VALUE_V2_CONFIG_VERSION
    learning_signal_weight: Decimal = Decimal("0.350000")
    evidence_gap_weight: Decimal = Decimal("0.133333")
    queue_priority_weight: Decimal = Decimal("0.244444")
    high_impact_feedback_boost_weight: Decimal = Decimal("0.200000")
    stale_learning_penalty_weight: Decimal = Decimal("0.150000")
    stale_learning_after_seconds: Decimal = Decimal("1209600.000000")
    high_impact_feedback_threshold: Decimal = Decimal("0.750000")
    watch_learning_value_score: Decimal = Decimal("0.250000")
    high_value_learning_value_score: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamSpecialistResearchQueueLearningValueConfigV2:
            raise TypeError(
                "TeamSpecialistResearchQueueLearningValueConfigV2 does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "learning_signal_weight",
            "evidence_gap_weight",
            "queue_priority_weight",
            "high_impact_feedback_boost_weight",
            "stale_learning_penalty_weight",
            "high_impact_feedback_threshold",
            "watch_learning_value_score",
            "high_value_learning_value_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "stale_learning_after_seconds",
            _normalize_positive_decimal(
                "stale_learning_after_seconds",
                self.stale_learning_after_seconds,
            ),
        )
        if self.watch_learning_value_score > self.high_value_learning_value_score:
            raise ValueError(
                "watch_learning_value_score must be less than or equal to "
                "high_value_learning_value_score",
            )
        require_paper_only_flags("specialist research queue learning value config", self)
        _reject_public_payload("specialist research queue learning value config", self)


@dataclass(frozen=True)
class TeamSpecialistResearchQueueLearningValueInputV2:
    team_id: str
    specialist_id: str
    queue_item_id: str
    observed_at: datetime
    lesson_last_applied_at: datetime
    queue_age_seconds: Decimal
    learning_signal_score: Decimal
    feedback_impact_score: Decimal
    evidence_gap_score: Decimal
    queue_priority_score: Decimal
    public_research_refs: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamSpecialistResearchQueueLearningValueInputV2:
            raise TypeError(
                "TeamSpecialistResearchQueueLearningValueInputV2 does not support subclassing",
            )

    def __post_init__(self) -> None:
        for field_name in ("team_id", "specialist_id", "queue_item_id"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "lesson_last_applied_at",
            _as_utc("lesson_last_applied_at", self.lesson_last_applied_at),
        )
        object.__setattr__(
            self,
            "queue_age_seconds",
            _normalize_nonnegative_decimal("queue_age_seconds", self.queue_age_seconds),
        )
        for field_name in (
            "learning_signal_score",
            "feedback_impact_score",
            "evidence_gap_score",
            "queue_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "public_research_refs",
            _normalize_public_refs("public_research_refs", self.public_research_refs),
        )
        require_paper_only_flags("specialist research queue learning value input", self)
        _reject_public_payload("specialist research queue learning value input", self)


@dataclass(frozen=True)
class TeamSpecialistResearchQueueLearningValueRowV2:
    team_id: str
    specialist_id: str
    queue_item_id: str
    observed_at: datetime
    lesson_last_applied_at: datetime
    queue_age_seconds: Decimal
    learning_signal_score: Decimal
    feedback_impact_score: Decimal
    evidence_gap_score: Decimal
    queue_priority_score: Decimal
    stale_learning_penalty: Decimal
    high_impact_feedback_boost: Decimal
    learning_value_score: Decimal
    row_status: str
    public_research_refs: tuple[str, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamSpecialistResearchQueueLearningValueRowV2:
            raise TypeError(
                "TeamSpecialistResearchQueueLearningValueRowV2 does not support subclassing",
            )

    def __post_init__(self) -> None:
        for field_name in ("team_id", "specialist_id", "queue_item_id"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "lesson_last_applied_at",
            _as_utc("lesson_last_applied_at", self.lesson_last_applied_at),
        )
        object.__setattr__(
            self,
            "queue_age_seconds",
            _normalize_nonnegative_decimal("queue_age_seconds", self.queue_age_seconds),
        )
        for field_name in (
            "learning_signal_score",
            "feedback_impact_score",
            "evidence_gap_score",
            "queue_priority_score",
            "stale_learning_penalty",
            "high_impact_feedback_boost",
            "learning_value_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("row_status", self.row_status, ("low_value", "watch", "high_value"))
        object.__setattr__(
            self,
            "public_research_refs",
            _normalize_public_refs("public_research_refs", self.public_research_refs),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        require_paper_only_flags("specialist research queue learning value row", self)
        _reject_public_payload("specialist research queue learning value row", self)
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        if self.derived_validation_digest != _row_digest(self):
            raise ValueError("derived_validation_digest must match row fields")
        _validate_row(self)


@dataclass(frozen=True)
class TeamSpecialistResearchQueueLearningValueReportV2:
    generated_at: datetime
    config_version: str
    queue_item_count: Decimal
    high_value_count: Decimal
    watch_count: Decimal
    low_value_count: Decimal
    stale_learning_count: Decimal
    average_learning_value_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    learning_value_rows: tuple[TeamSpecialistResearchQueueLearningValueRowV2, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamSpecialistResearchQueueLearningValueReportV2:
            raise TypeError(
                "TeamSpecialistResearchQueueLearningValueReportV2 does not support subclassing",
            )

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "queue_item_count",
            "high_value_count",
            "watch_count",
            "low_value_count",
            "stale_learning_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_learning_value_score",
            _normalize_ratio(
                "average_learning_value_score",
                self.average_learning_value_score,
            ),
        )
        _require_status("status", self.status, TEAM_SPECIALIST_RESEARCH_QUEUE_LEARNING_VALUE_V2_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(
            self,
            "learning_value_rows",
            _normalize_learning_value_rows(self.learning_value_rows),
        )
        require_paper_only_flags("specialist research queue learning value report", self)
        _reject_public_payload("specialist research queue learning value report", self)
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        if self.derived_validation_digest != _report_digest(self):
            raise ValueError("derived_validation_digest must match report fields")
        _validate_report(self)


def build_team_specialist_research_queue_learning_value_v2(
    inputs: list[TeamSpecialistResearchQueueLearningValueInputV2]
    | tuple[TeamSpecialistResearchQueueLearningValueInputV2, ...],
    *,
    config: TeamSpecialistResearchQueueLearningValueConfigV2,
    generated_at: datetime,
) -> TeamSpecialistResearchQueueLearningValueReportV2:
    if type(config) is not TeamSpecialistResearchQueueLearningValueConfigV2:
        raise ValueError(
            "config must be a TeamSpecialistResearchQueueLearningValueConfigV2",
        )
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _normalize_inputs(inputs)
    _validate_input_dates(rows, generated_at_utc)
    learning_value_rows = tuple(
        sorted(
            (_learning_value_row(row, config, generated_at_utc) for row in rows),
            key=_row_sort_key,
        ),
    )
    report_parts = dict(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        queue_item_count=_count(len(learning_value_rows)),
        high_value_count=_count(
            sum(1 for row in learning_value_rows if row.row_status == "high_value"),
        ),
        watch_count=_count(sum(1 for row in learning_value_rows if row.row_status == "watch")),
        low_value_count=_count(
            sum(1 for row in learning_value_rows if row.row_status == "low_value"),
        ),
        stale_learning_count=_count(
            sum(1 for row in learning_value_rows if row.stale_learning_penalty > ZERO_RATIO),
        ),
        average_learning_value_score=_average_learning_value_score(learning_value_rows),
        status=_report_status(learning_value_rows),
        reason_codes=_report_reason_codes(learning_value_rows),
        learning_value_rows=learning_value_rows,
        paper_only=True,
        report_only=True,
        readonly=True,
    )
    return TeamSpecialistResearchQueueLearningValueReportV2(
        **report_parts,
        derived_validation_digest=_digest_public(report_parts),
    )


def team_specialist_research_queue_learning_value_v2_payload(
    report: TeamSpecialistResearchQueueLearningValueReportV2 | dict[str, object],
) -> dict[str, Any]:
    if type(report) is dict:
        _reject_public_payload("specialist research queue learning value payload", report)
        return _tupleify_payload_collections(report)
    if type(report) is not TeamSpecialistResearchQueueLearningValueReportV2:
        raise ValueError("report must be a TeamSpecialistResearchQueueLearningValueReportV2")
    require_paper_only_flags("report", report)
    if report.derived_validation_digest != _report_digest(report):
        raise ValueError("derived_validation_digest must match report fields")
    payload = json_ready_no_floats(report)
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")
    _reject_public_payload("specialist research queue learning value payload", payload)
    return _tupleify_payload_collections(payload)


def _normalize_inputs(
    inputs: list[TeamSpecialistResearchQueueLearningValueInputV2]
    | tuple[TeamSpecialistResearchQueueLearningValueInputV2, ...],
) -> tuple[TeamSpecialistResearchQueueLearningValueInputV2, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(inputs)
    for row in rows:
        if type(row) is not TeamSpecialistResearchQueueLearningValueInputV2:
            raise ValueError(
                "inputs must contain TeamSpecialistResearchQueueLearningValueInputV2 values",
            )
        require_paper_only_flags("input", row)
    return rows


def _validate_input_dates(
    rows: tuple[TeamSpecialistResearchQueueLearningValueInputV2, ...],
    generated_at: datetime,
) -> None:
    for row in rows:
        if row.observed_at > generated_at:
            raise ValueError("observed_at must be on or before generated_at")
        if row.lesson_last_applied_at > generated_at:
            raise ValueError("lesson_last_applied_at must be on or before generated_at")


def _learning_value_row(
    row: TeamSpecialistResearchQueueLearningValueInputV2,
    config: TeamSpecialistResearchQueueLearningValueConfigV2,
    generated_at: datetime,
) -> TeamSpecialistResearchQueueLearningValueRowV2:
    stale_penalty = _stale_learning_penalty(row, config, generated_at)
    feedback_boost = _high_impact_feedback_boost(row, config)
    learning_value_score = _learning_value_score(row, stale_penalty, feedback_boost, config)
    row_status = _row_status(learning_value_score, config)
    row_parts = dict(
        team_id=row.team_id,
        specialist_id=row.specialist_id,
        queue_item_id=row.queue_item_id,
        observed_at=row.observed_at,
        lesson_last_applied_at=row.lesson_last_applied_at,
        queue_age_seconds=row.queue_age_seconds,
        learning_signal_score=row.learning_signal_score,
        feedback_impact_score=row.feedback_impact_score,
        evidence_gap_score=row.evidence_gap_score,
        queue_priority_score=row.queue_priority_score,
        stale_learning_penalty=stale_penalty,
        high_impact_feedback_boost=feedback_boost,
        learning_value_score=learning_value_score,
        row_status=row_status,
        public_research_refs=row.public_research_refs,
        reason_codes=_row_reason_codes(row_status, stale_penalty, feedback_boost),
        paper_only=True,
        report_only=True,
        readonly=True,
    )
    return TeamSpecialistResearchQueueLearningValueRowV2(
        **row_parts,
        derived_validation_digest=_digest_public(row_parts),
    )


def _stale_learning_penalty(
    row: TeamSpecialistResearchQueueLearningValueInputV2,
    config: TeamSpecialistResearchQueueLearningValueConfigV2,
    generated_at: datetime,
) -> Decimal:
    lesson_age_seconds = _age_seconds(generated_at, row.lesson_last_applied_at)
    if lesson_age_seconds <= config.stale_learning_after_seconds:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            (lesson_age_seconds - config.stale_learning_after_seconds)
            / config.stale_learning_after_seconds,
        )


def _high_impact_feedback_boost(
    row: TeamSpecialistResearchQueueLearningValueInputV2,
    config: TeamSpecialistResearchQueueLearningValueConfigV2,
) -> Decimal:
    if row.feedback_impact_score < config.high_impact_feedback_threshold:
        return ZERO_RATIO
    return row.feedback_impact_score


def _learning_value_score(
    row: TeamSpecialistResearchQueueLearningValueInputV2,
    stale_penalty: Decimal,
    feedback_boost: Decimal,
    config: TeamSpecialistResearchQueueLearningValueConfigV2,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            row.learning_signal_score * config.learning_signal_weight
            + row.evidence_gap_score * config.evidence_gap_weight
            + row.queue_priority_score * config.queue_priority_weight
            + feedback_boost * config.high_impact_feedback_boost_weight
            - stale_penalty * config.stale_learning_penalty_weight,
        )


def _row_status(
    learning_value_score: Decimal,
    config: TeamSpecialistResearchQueueLearningValueConfigV2,
) -> str:
    if learning_value_score >= config.high_value_learning_value_score:
        return "high_value"
    if learning_value_score >= config.watch_learning_value_score:
        return "watch"
    return "low_value"


def _row_reason_codes(
    row_status: str,
    stale_penalty: Decimal,
    feedback_boost: Decimal,
) -> tuple[str, ...]:
    codes: set[str] = set()
    if row_status == "high_value":
        codes.add(HIGH_VALUE_REASON)
    elif row_status == "watch":
        codes.add(WATCH_REASON)
    else:
        codes.add(LOW_VALUE_REASON)
    if stale_penalty > ZERO_RATIO:
        codes.add(STALE_LEARNING_REASON)
    if feedback_boost > ZERO_RATIO:
        codes.add(HIGH_IMPACT_FEEDBACK_REASON)
    return tuple(code for code in ROW_REASON_CODES if code in codes)


def _report_status(
    rows: tuple[TeamSpecialistResearchQueueLearningValueRowV2, ...],
) -> str:
    if not rows:
        return "empty"
    if any(row.row_status == "high_value" for row in rows):
        return "high_value"
    if any(row.row_status == "watch" for row in rows):
        return "watch"
    return "low_value"


def _report_reason_codes(
    rows: tuple[TeamSpecialistResearchQueueLearningValueRowV2, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_QUEUE_REASON,)
    codes: set[str] = set()
    if any(row.row_status == "high_value" for row in rows):
        codes.add(HIGH_VALUE_REASON)
    elif any(row.row_status == "watch" for row in rows):
        codes.add(WATCH_REASON)
    else:
        codes.add(LOW_VALUE_REASON)
    if any(row.stale_learning_penalty > ZERO_RATIO for row in rows):
        codes.add(STALE_LEARNING_REASON)
    if any(row.high_impact_feedback_boost > ZERO_RATIO for row in rows):
        codes.add(HIGH_IMPACT_FEEDBACK_REASON)
    return tuple(code for code in REPORT_REASON_CODES if code in codes)


def _row_sort_key(
    row: TeamSpecialistResearchQueueLearningValueRowV2,
) -> tuple[int, Decimal, str, str, str]:
    return (
        -_status_rank(row.row_status),
        -row.learning_value_score,
        row.team_id,
        row.specialist_id,
        row.queue_item_id,
    )


def _status_rank(status: str) -> int:
    if status == "high_value":
        return 3
    if status == "watch":
        return 2
    if status == "low_value":
        return 1
    return 0


def _average_learning_value_score(
    rows: tuple[TeamSpecialistResearchQueueLearningValueRowV2, ...],
) -> Decimal:
    if not rows:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            sum((row.learning_value_score for row in rows), ZERO_RATIO)
            / Decimal(len(rows)),
        )


def _validate_row(row: TeamSpecialistResearchQueueLearningValueRowV2) -> None:
    if row.row_status == "high_value" and row.learning_value_score < Decimal("0.700000"):
        raise ValueError("row_status must match learning_value_score")
    if row.row_status == "watch" and not (
        Decimal("0.250000") <= row.learning_value_score < Decimal("0.700000")
    ):
        raise ValueError("row_status must match learning_value_score")
    if row.row_status == "low_value" and row.learning_value_score >= Decimal("0.250000"):
        raise ValueError("row_status must match learning_value_score")
    if row.reason_codes != _row_reason_codes(
        row.row_status,
        row.stale_learning_penalty,
        row.high_impact_feedback_boost,
    ):
        raise ValueError("reason_codes must match learning value fields")


def _validate_report(report: TeamSpecialistResearchQueueLearningValueReportV2) -> None:
    rows = report.learning_value_rows
    if report.queue_item_count != _count(len(rows)):
        raise ValueError("queue_item_count must match learning_value_rows")
    if report.high_value_count != _count(sum(1 for row in rows if row.row_status == "high_value")):
        raise ValueError("high_value_count must match learning_value_rows")
    if report.watch_count != _count(sum(1 for row in rows if row.row_status == "watch")):
        raise ValueError("watch_count must match learning_value_rows")
    if report.low_value_count != _count(sum(1 for row in rows if row.row_status == "low_value")):
        raise ValueError("low_value_count must match learning_value_rows")
    if report.stale_learning_count != _count(
        sum(1 for row in rows if row.stale_learning_penalty > ZERO_RATIO),
    ):
        raise ValueError("stale_learning_count must match learning_value_rows")
    if report.average_learning_value_score != _average_learning_value_score(rows):
        raise ValueError("average_learning_value_score must match learning_value_rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match learning_value_rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match learning_value_rows")
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("learning_value_rows must use deterministic sequence")


def _normalize_learning_value_rows(
    rows: tuple[TeamSpecialistResearchQueueLearningValueRowV2, ...],
) -> tuple[TeamSpecialistResearchQueueLearningValueRowV2, ...]:
    if type(rows) is not tuple:
        raise ValueError("learning_value_rows must be a tuple")
    for row in rows:
        if type(row) is not TeamSpecialistResearchQueueLearningValueRowV2:
            raise ValueError(
                "learning_value_rows must contain TeamSpecialistResearchQueueLearningValueRowV2 values",
            )
        require_paper_only_flags("learning value row", row)
    return rows


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
    normalized = []
    for item in value:
        _require_public_string(field_name, item)
        if not item.startswith(SAFE_REF_PREFIXES):
            raise ValueError(f"{field_name} contains an unsupported public reference")
        normalized.append(item)
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


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_RATIO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value.quantize(SECONDS_QUANTUM)


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    value = _normalize_nonnegative_decimal(field_name, value)
    if value <= ZERO_RATIO:
        raise ValueError(f"{field_name} must be positive")
    return value


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


def _require_status(field_name: str, value: object, allowed_statuses: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed_statuses:
        raise ValueError(f"{field_name} contains an unsupported status")


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


def _row_digest(row: TeamSpecialistResearchQueueLearningValueRowV2) -> str:
    return _digest_public(_row_digest_parts(row))


def _report_digest(report: TeamSpecialistResearchQueueLearningValueReportV2) -> str:
    return _digest_public(_report_digest_parts(report))


def _row_digest_parts(row: TeamSpecialistResearchQueueLearningValueRowV2) -> dict[str, object]:
    return {
        "team_id": row.team_id,
        "specialist_id": row.specialist_id,
        "queue_item_id": row.queue_item_id,
        "observed_at": row.observed_at,
        "lesson_last_applied_at": row.lesson_last_applied_at,
        "queue_age_seconds": row.queue_age_seconds,
        "learning_signal_score": row.learning_signal_score,
        "feedback_impact_score": row.feedback_impact_score,
        "evidence_gap_score": row.evidence_gap_score,
        "queue_priority_score": row.queue_priority_score,
        "stale_learning_penalty": row.stale_learning_penalty,
        "high_impact_feedback_boost": row.high_impact_feedback_boost,
        "learning_value_score": row.learning_value_score,
        "row_status": row.row_status,
        "public_research_refs": row.public_research_refs,
        "reason_codes": row.reason_codes,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _report_digest_parts(
    report: TeamSpecialistResearchQueueLearningValueReportV2,
) -> dict[str, object]:
    return {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "queue_item_count": report.queue_item_count,
        "high_value_count": report.high_value_count,
        "watch_count": report.watch_count,
        "low_value_count": report.low_value_count,
        "stale_learning_count": report.stale_learning_count,
        "average_learning_value_score": report.average_learning_value_score,
        "status": report.status,
        "reason_codes": report.reason_codes,
        "learning_value_rows": report.learning_value_rows,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _digest_public(value: object) -> str:
    ready = _digest_ready(value)
    _reject_public_payload("derived validation payload", ready)
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _digest_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _digest_ready(asdict(value))
    if isinstance(value, dict):
        return {
            key: _digest_ready(item)
            for key, item in value.items()
            if key != "derived_validation_digest"
        }
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if isinstance(value, (list, tuple)):
        return [_digest_ready(item) for item in value]
    if isinstance(value, (str, int, bool)) or value is None:
        return value
    raise ValueError("value is not digest serializable")


def _reject_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_public_payload(label, asdict(value))
        return
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
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_TEXT_BLOCKS)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _age_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    with localcontext(DECIMAL_CONTEXT):
        return (
            Decimal(delta.days) * SECONDS_PER_DAY
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / Decimal("1000000"))
        ).quantize(SECONDS_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _tupleify_payload_collections(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _tupleify_payload_collections(item) for key, item in value.items()}
    if isinstance(value, list):
        return tuple(_tupleify_payload_collections(item) for item in value)
    return value


__all__ = (
    "DEFAULT_TEAM_SPECIALIST_RESEARCH_QUEUE_LEARNING_VALUE_V2_CONFIG_VERSION",
    "TEAM_SPECIALIST_RESEARCH_QUEUE_LEARNING_VALUE_V2_STATUSES",
    "TeamSpecialistResearchQueueLearningValueConfigV2",
    "TeamSpecialistResearchQueueLearningValueInputV2",
    "TeamSpecialistResearchQueueLearningValueRowV2",
    "TeamSpecialistResearchQueueLearningValueReportV2",
    "build_team_specialist_research_queue_learning_value_v2",
    "team_specialist_research_queue_learning_value_v2_payload",
)
