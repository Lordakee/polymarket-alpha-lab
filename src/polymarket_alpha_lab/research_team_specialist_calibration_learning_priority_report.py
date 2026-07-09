"""Public-safe specialist calibration learning priority report reducer."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_TEAM_SPECIALIST_CALIBRATION_LEARNING_PRIORITY_CONFIG_VERSION = (
    "research-team-specialist-calibration-learning-priority-report-v0"
)

STATUSES = ("pass", "watch", "block")

COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

STATUS_WEIGHT = {
    "block": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}

PASS_ROW_REASON_CODE = "specialist_calibration_learning_priority_clear"
EMPTY_REPORT_REASON_CODE = "specialist_calibration_learning_priority_no_rows"
REPORT_PASS_REASON_CODE = "specialist_calibration_learning_priority_report_pass"
REPORT_WATCH_REASON_CODE = "specialist_calibration_learning_priority_report_watch"
REPORT_BLOCK_REASON_CODE = "specialist_calibration_learning_priority_report_block"

RECENT_MISS_BLOCK_REASON = "specialist_learning_recent_miss_block"
CALIBRATION_AGE_BLOCK_REASON = "specialist_learning_calibration_age_block"
FEEDBACK_ABSORPTION_BLOCK_REASON = (
    "specialist_learning_feedback_absorption_block"
)
EVIDENCE_REUSE_BLOCK_REASON = "specialist_learning_evidence_reuse_block"
REVIEW_BACKLOG_BLOCK_REASON = "specialist_learning_review_backlog_block"
PRIORITY_SCORE_BLOCK_REASON = "specialist_learning_priority_score_block"

RECENT_MISS_WATCH_REASON = "specialist_learning_recent_miss_watch"
CALIBRATION_AGE_WATCH_REASON = "specialist_learning_calibration_age_watch"
FEEDBACK_ABSORPTION_WATCH_REASON = (
    "specialist_learning_feedback_absorption_watch"
)
EVIDENCE_REUSE_WATCH_REASON = "specialist_learning_evidence_reuse_watch"
REVIEW_BACKLOG_WATCH_REASON = "specialist_learning_review_backlog_watch"
PRIORITY_SCORE_WATCH_REASON = "specialist_learning_priority_score_watch"

BLOCK_REASON_CODES = (
    RECENT_MISS_BLOCK_REASON,
    CALIBRATION_AGE_BLOCK_REASON,
    FEEDBACK_ABSORPTION_BLOCK_REASON,
    EVIDENCE_REUSE_BLOCK_REASON,
    REVIEW_BACKLOG_BLOCK_REASON,
    PRIORITY_SCORE_BLOCK_REASON,
)
WATCH_REASON_CODES = (
    RECENT_MISS_WATCH_REASON,
    CALIBRATION_AGE_WATCH_REASON,
    FEEDBACK_ABSORPTION_WATCH_REASON,
    EVIDENCE_REUSE_WATCH_REASON,
    REVIEW_BACKLOG_WATCH_REASON,
    PRIORITY_SCORE_WATCH_REASON,
)
METRIC_BLOCK_REASON_CODES = BLOCK_REASON_CODES[:-1]
METRIC_WATCH_REASON_CODES = WATCH_REASON_CODES[:-1]
ROW_REASON_CODES = BLOCK_REASON_CODES + WATCH_REASON_CODES + (PASS_ROW_REASON_CODE,)
REPORT_REASON_PREFIX_BY_STATUS = {
    "pass": REPORT_PASS_REASON_CODE,
    "watch": REPORT_WATCH_REASON_CODE,
    "block": REPORT_BLOCK_REASON_CODE,
}
REPORT_REASON_CODES = (
    EMPTY_REPORT_REASON_CODE,
    REPORT_PASS_REASON_CODE,
    REPORT_WATCH_REASON_CODE,
    REPORT_BLOCK_REASON_CODE,
) + BLOCK_REASON_CODES + WATCH_REASON_CODES
REASON_CODE_COUNT_PRIORITY = (
    EMPTY_REPORT_REASON_CODE,
    *BLOCK_REASON_CODES,
    *WATCH_REASON_CODES,
    PASS_ROW_REASON_CODE,
)

HEX_CHARS = frozenset("0123456789abcdef")
SAFE_IDENTIFIER_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789_")
UNSAFE_IDENTIFIER_FRAGMENTS = frozenset(
    (
        "raw",
        "candidate",
        "market",
        "slug",
        "question",
        "source",
        "dsn",
        "table",
        "token",
        "secret",
        "auth",
        "wallet",
        "order",
        "trade",
        "trading",
        "buy",
        "sell",
        "recommend",
        "position",
    ),
)
UNSAFE_PUBLIC_KEY_FRAGMENTS = frozenset(
    (
        "raw",
        "candidate",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "secret",
        "auth",
        "wallet",
        "order",
        "trade",
        "trading",
        "buy",
        "sell",
        "recommend",
        "position",
    ),
)
UNSAFE_PUBLIC_VALUE_FRAGMENTS = frozenset(
    (
        "http://",
        "https://",
        "source_url",
        "source_text",
        "dsn",
        "token",
        "secret",
        "auth",
        "wallet",
        "order",
        "trade",
        "trading",
        "buy",
        "sell",
        "recommend",
        "position",
    ),
)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_SPECIALIST_CALIBRATION_LEARNING_PRIORITY_CONFIG_VERSION",
    "ResearchTeamSpecialistCalibrationLearningPriorityConfig",
    "ResearchTeamSpecialistCalibrationLearningPriorityInput",
    "ResearchTeamSpecialistCalibrationLearningPriorityRow",
    "ResearchTeamSpecialistCalibrationLearningPriorityReasonCodeCount",
    "ResearchTeamSpecialistCalibrationLearningPriorityReport",
    "build_research_team_specialist_calibration_learning_priority_report",
    "research_team_specialist_calibration_learning_priority_report_public_payload",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise ValueError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class ResearchTeamSpecialistCalibrationLearningPriorityConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_SPECIALIST_CALIBRATION_LEARNING_PRIORITY_CONFIG_VERSION
    )
    recent_miss_severity_weight: Decimal = Decimal("0.300000")
    calibration_age_weight: Decimal = Decimal("0.200000")
    feedback_absorption_weight: Decimal = Decimal("0.200000")
    evidence_reuse_quality_weight: Decimal = Decimal("0.150000")
    review_backlog_pressure_weight: Decimal = Decimal("0.150000")
    watch_priority_score_floor: Decimal = Decimal("0.300000")
    block_priority_score_floor: Decimal = Decimal("0.600000")
    watch_recent_miss_severity: Decimal = Decimal("0.150000")
    block_recent_miss_severity: Decimal = Decimal("0.350000")
    max_pass_calibration_age_days: Decimal = Decimal("14")
    max_watch_calibration_age_days: Decimal = Decimal("45")
    min_pass_feedback_absorption_ratio: Decimal = Decimal("0.850000")
    min_watch_feedback_absorption_ratio: Decimal = Decimal("0.650000")
    min_pass_evidence_reuse_quality: Decimal = Decimal("0.800000")
    min_watch_evidence_reuse_quality: Decimal = Decimal("0.600000")
    max_pass_review_backlog_pressure: Decimal = Decimal("0.400000")
    max_watch_review_backlog_pressure: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistCalibrationLearningPriorityConfig,
            "config",
        )
        _require_public_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_SPECIALIST_CALIBRATION_LEARNING_PRIORITY_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "recent_miss_severity_weight",
            "calibration_age_weight",
            "feedback_absorption_weight",
            "evidence_reuse_quality_weight",
            "review_backlog_pressure_weight",
            "watch_priority_score_floor",
            "block_priority_score_floor",
            "watch_recent_miss_severity",
            "block_recent_miss_severity",
            "min_pass_feedback_absorption_ratio",
            "min_watch_feedback_absorption_ratio",
            "min_pass_evidence_reuse_quality",
            "min_watch_evidence_reuse_quality",
            "max_pass_review_backlog_pressure",
            "max_watch_review_backlog_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_calibration_age_days",
            "max_watch_calibration_age_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistCalibrationLearningPriorityInput(_FinalPublicDataclass):
    specialist_key: str
    learning_track: str
    recent_miss_severity: Decimal
    calibration_age_days: Decimal
    feedback_absorption_ratio: Decimal
    evidence_reuse_quality: Decimal
    review_backlog_pressure: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistCalibrationLearningPriorityInput,
            "input",
        )
        _require_safe_identifier("specialist_key", self.specialist_key)
        _require_safe_identifier("learning_track", self.learning_track)
        object.__setattr__(
            self,
            "calibration_age_days",
            _require_count_decimal("calibration_age_days", self.calibration_age_days),
        )
        for field_name in (
            "recent_miss_severity",
            "feedback_absorption_ratio",
            "evidence_reuse_quality",
            "review_backlog_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistCalibrationLearningPriorityRow(_FinalPublicDataclass):
    specialist_key: str
    learning_track: str
    status: str
    recent_miss_severity: Decimal
    calibration_age_days: Decimal
    calibration_age_pressure_score: Decimal
    feedback_absorption_ratio: Decimal
    feedback_gap_score: Decimal
    evidence_reuse_quality: Decimal
    evidence_gap_score: Decimal
    review_backlog_pressure: Decimal
    learning_priority_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistCalibrationLearningPriorityRow,
            "row",
        )
        _require_safe_identifier("specialist_key", self.specialist_key)
        _require_safe_identifier("learning_track", self.learning_track)
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "calibration_age_days",
            _require_count_decimal("calibration_age_days", self.calibration_age_days),
        )
        for field_name in (
            "recent_miss_severity",
            "calibration_age_pressure_score",
            "feedback_absorption_ratio",
            "feedback_gap_score",
            "evidence_reuse_quality",
            "evidence_gap_score",
            "review_backlog_pressure",
            "learning_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _require_row_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistCalibrationLearningPriorityReasonCodeCount(
    _FinalPublicDataclass,
):
    reason_code: str
    count: Decimal
    specialist_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistCalibrationLearningPriorityReasonCodeCount,
            "reason_code_count",
        )
        _require_public_text("reason_code", self.reason_code)
        if self.reason_code not in REASON_CODE_COUNT_PRIORITY:
            raise ValueError("reason_code must be supported")
        object.__setattr__(self, "count", _require_count_decimal("count", self.count))
        object.__setattr__(
            self,
            "specialist_ratio",
            _require_ratio_decimal("specialist_ratio", self.specialist_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistCalibrationLearningPriorityReport(_FinalPublicDataclass):
    config_version: str
    specialist_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    learning_priority_team_count: Decimal
    average_learning_priority_score: Decimal
    max_learning_priority_score: Decimal
    min_learning_priority_score: Decimal
    average_recent_miss_severity: Decimal
    max_calibration_age_days: Decimal
    min_feedback_absorption_ratio: Decimal
    min_evidence_reuse_quality: Decimal
    max_review_backlog_pressure: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchTeamSpecialistCalibrationLearningPriorityReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchTeamSpecialistCalibrationLearningPriorityRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistCalibrationLearningPriorityReport,
            "report",
        )
        _require_public_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_SPECIALIST_CALIBRATION_LEARNING_PRIORITY_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "specialist_count",
            "pass_count",
            "watch_count",
            "block_count",
            "learning_priority_team_count",
            "max_calibration_age_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_learning_priority_score",
            "max_learning_priority_score",
            "min_learning_priority_score",
            "average_recent_miss_severity",
            "min_feedback_absorption_ratio",
            "min_evidence_reuse_quality",
            "max_review_backlog_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _require_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _require_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _require_reason_code_counts(self.reason_code_counts),
        )
        _require_hard_flags("report", self)
        if self.derived_validation_digest:
            _require_sha256("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != _derived_validation_digest(self):
                raise ValueError("derived_validation_digest does not match report payload")
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _derived_validation_digest(self),
            )
        _validate_report_materialized_fields(self)

    @property
    def public_payload(self) -> dict[str, Any]:
        return research_team_specialist_calibration_learning_priority_report_public_payload(
            self,
        )


def build_research_team_specialist_calibration_learning_priority_report(
    learning_items: Iterable[ResearchTeamSpecialistCalibrationLearningPriorityInput],
    *,
    config: ResearchTeamSpecialistCalibrationLearningPriorityConfig,
) -> ResearchTeamSpecialistCalibrationLearningPriorityReport:
    if type(config) is not ResearchTeamSpecialistCalibrationLearningPriorityConfig:
        raise ValueError(
            "config must be a ResearchTeamSpecialistCalibrationLearningPriorityConfig",
        )
    _require_hard_flags("config", config)
    items = _normalize_learning_items(learning_items)
    rows = tuple(
        sorted(
            (_row_for_learning_item(item, config=config) for item in items),
            key=_row_sort_key,
        ),
    )
    status = _rollup_status(tuple(row.status for row in rows))
    return ResearchTeamSpecialistCalibrationLearningPriorityReport(
        config_version=config.config_version,
        specialist_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        learning_priority_team_count=_learning_priority_team_count(rows),
        average_learning_priority_score=_mean_decimal(
            tuple(row.learning_priority_score for row in rows),
        ),
        max_learning_priority_score=_max_decimal(
            tuple(row.learning_priority_score for row in rows),
        ),
        min_learning_priority_score=_min_decimal(
            tuple(row.learning_priority_score for row in rows),
        ),
        average_recent_miss_severity=_mean_decimal(
            tuple(row.recent_miss_severity for row in rows),
        ),
        max_calibration_age_days=_max_decimal(
            tuple(row.calibration_age_days for row in rows),
            count=True,
        ),
        min_feedback_absorption_ratio=_min_decimal(
            tuple(row.feedback_absorption_ratio for row in rows),
        ),
        min_evidence_reuse_quality=_min_decimal(
            tuple(row.evidence_reuse_quality for row in rows),
        ),
        max_review_backlog_pressure=_max_decimal(
            tuple(row.review_backlog_pressure for row in rows),
        ),
        status=status,
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_team_specialist_calibration_learning_priority_report_public_payload(
    report: ResearchTeamSpecialistCalibrationLearningPriorityReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchTeamSpecialistCalibrationLearningPriorityReport:
        _require_hard_flags("report", report)
        _validate_report_materialized_fields(report)
        if report.derived_validation_digest != _derived_validation_digest(report):
            raise ValueError("derived_validation_digest does not match report payload")
        payload = _report_payload(report)
        _reject_unsafe_public_payload("payload", payload)
        _reject_public_numeric_values(payload)
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        _reject_public_numeric_values(report)
        _require_hard_flags("payload", _PayloadFlags(report))
        supplied_digest = report.get("derived_validation_digest")
        if type(supplied_digest) is not str:
            raise ValueError("derived_validation_digest is required")
        _require_sha256("derived_validation_digest", supplied_digest)
        if supplied_digest != _payload_validation_digest(report):
            raise ValueError("derived_validation_digest does not match report payload")
        return report
    raise ValueError(
        "report must be a ResearchTeamSpecialistCalibrationLearningPriorityReport",
    )


@dataclass(frozen=True)
class _PayloadFlags:
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


def _normalize_learning_items(
    learning_items: Iterable[ResearchTeamSpecialistCalibrationLearningPriorityInput],
) -> tuple[ResearchTeamSpecialistCalibrationLearningPriorityInput, ...]:
    if isinstance(learning_items, (str, bytes)):
        raise ValueError("learning_items must be an iterable")
    try:
        items = tuple(learning_items)
    except TypeError as exc:
        raise ValueError("learning_items must be an iterable") from exc
    seen: set[str] = set()
    for item in items:
        if type(item) is not ResearchTeamSpecialistCalibrationLearningPriorityInput:
            raise ValueError(
                "learning_items must contain "
                "ResearchTeamSpecialistCalibrationLearningPriorityInput",
            )
        _require_hard_flags("input", item)
        if item.specialist_key in seen:
            raise ValueError("specialist_key values must be unique")
        seen.add(item.specialist_key)
    return items


def _row_for_learning_item(
    item: ResearchTeamSpecialistCalibrationLearningPriorityInput,
    *,
    config: ResearchTeamSpecialistCalibrationLearningPriorityConfig,
) -> ResearchTeamSpecialistCalibrationLearningPriorityRow:
    calibration_age_pressure_score = _calibration_age_pressure_score(item, config)
    feedback_gap_score = _gap_score(item.feedback_absorption_ratio)
    evidence_gap_score = _gap_score(item.evidence_reuse_quality)
    learning_priority_score = _learning_priority_score(
        item,
        config=config,
        calibration_age_pressure_score=calibration_age_pressure_score,
        feedback_gap_score=feedback_gap_score,
        evidence_gap_score=evidence_gap_score,
    )
    reason_codes = _row_reason_codes(
        item,
        config=config,
        learning_priority_score=learning_priority_score,
    )
    return ResearchTeamSpecialistCalibrationLearningPriorityRow(
        specialist_key=item.specialist_key,
        learning_track=item.learning_track,
        status=_row_status(
            learning_priority_score,
            reason_codes,
            config=config,
        ),
        recent_miss_severity=item.recent_miss_severity,
        calibration_age_days=item.calibration_age_days,
        calibration_age_pressure_score=calibration_age_pressure_score,
        feedback_absorption_ratio=item.feedback_absorption_ratio,
        feedback_gap_score=feedback_gap_score,
        evidence_reuse_quality=item.evidence_reuse_quality,
        evidence_gap_score=evidence_gap_score,
        review_backlog_pressure=item.review_backlog_pressure,
        learning_priority_score=learning_priority_score,
        reason_codes=reason_codes,
    )


def _learning_priority_score(
    item: ResearchTeamSpecialistCalibrationLearningPriorityInput,
    *,
    config: ResearchTeamSpecialistCalibrationLearningPriorityConfig,
    calibration_age_pressure_score: Decimal,
    feedback_gap_score: Decimal,
    evidence_gap_score: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            item.recent_miss_severity * config.recent_miss_severity_weight
            + calibration_age_pressure_score * config.calibration_age_weight
            + feedback_gap_score * config.feedback_absorption_weight
            + evidence_gap_score * config.evidence_reuse_quality_weight
            + item.review_backlog_pressure * config.review_backlog_pressure_weight
        )
        return _clamp_ratio(score)


def _calibration_age_pressure_score(
    item: ResearchTeamSpecialistCalibrationLearningPriorityInput,
    config: ResearchTeamSpecialistCalibrationLearningPriorityConfig,
) -> Decimal:
    if config.max_watch_calibration_age_days == ZERO_COUNT:
        return ONE_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            item.calibration_age_days / config.max_watch_calibration_age_days,
        )


def _gap_score(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(ONE_RATIO - value)


def _row_reason_codes(
    item: ResearchTeamSpecialistCalibrationLearningPriorityInput,
    *,
    config: ResearchTeamSpecialistCalibrationLearningPriorityConfig,
    learning_priority_score: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if item.recent_miss_severity >= config.block_recent_miss_severity:
        reason_codes.append(RECENT_MISS_BLOCK_REASON)
    elif item.recent_miss_severity >= config.watch_recent_miss_severity:
        reason_codes.append(RECENT_MISS_WATCH_REASON)

    if item.calibration_age_days > config.max_watch_calibration_age_days:
        reason_codes.append(CALIBRATION_AGE_BLOCK_REASON)
    elif item.calibration_age_days > config.max_pass_calibration_age_days:
        reason_codes.append(CALIBRATION_AGE_WATCH_REASON)

    if item.feedback_absorption_ratio < config.min_watch_feedback_absorption_ratio:
        reason_codes.append(FEEDBACK_ABSORPTION_BLOCK_REASON)
    elif item.feedback_absorption_ratio < config.min_pass_feedback_absorption_ratio:
        reason_codes.append(FEEDBACK_ABSORPTION_WATCH_REASON)

    if item.evidence_reuse_quality < config.min_watch_evidence_reuse_quality:
        reason_codes.append(EVIDENCE_REUSE_BLOCK_REASON)
    elif item.evidence_reuse_quality < config.min_pass_evidence_reuse_quality:
        reason_codes.append(EVIDENCE_REUSE_WATCH_REASON)

    if item.review_backlog_pressure > config.max_watch_review_backlog_pressure:
        reason_codes.append(REVIEW_BACKLOG_BLOCK_REASON)
    elif item.review_backlog_pressure > config.max_pass_review_backlog_pressure:
        reason_codes.append(REVIEW_BACKLOG_WATCH_REASON)

    if not reason_codes:
        if learning_priority_score >= config.block_priority_score_floor:
            reason_codes.append(PRIORITY_SCORE_BLOCK_REASON)
        elif learning_priority_score >= config.watch_priority_score_floor:
            reason_codes.append(PRIORITY_SCORE_WATCH_REASON)
        else:
            reason_codes.append(PASS_ROW_REASON_CODE)
    return tuple(
        reason_code for reason_code in ROW_REASON_CODES if reason_code in reason_codes
    )


def _row_status(
    learning_priority_score: Decimal,
    reason_codes: tuple[str, ...],
    *,
    config: ResearchTeamSpecialistCalibrationLearningPriorityConfig,
) -> str:
    if (
        any(reason_code in BLOCK_REASON_CODES for reason_code in reason_codes)
        or learning_priority_score >= config.block_priority_score_floor
    ):
        return "block"
    if (
        any(reason_code in WATCH_REASON_CODES for reason_code in reason_codes)
        or learning_priority_score >= config.watch_priority_score_floor
    ):
        return "watch"
    return "pass"


def _rollup_status(statuses: tuple[str, ...]) -> str:
    if not statuses:
        return "block"
    if any(status == "block" for status in statuses):
        return "block"
    if any(status == "watch" for status in statuses):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTeamSpecialistCalibrationLearningPriorityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REPORT_REASON_CODE,)
    status = _rollup_status(tuple(row.status for row in rows))
    reason_codes = [REPORT_REASON_PREFIX_BY_STATUS[status]]
    row_reasons = frozenset(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != PASS_ROW_REASON_CODE
    )
    for reason_code in BLOCK_REASON_CODES + WATCH_REASON_CODES:
        if reason_code in row_reasons:
            reason_codes.append(reason_code)
    return tuple(reason_codes)


def _reason_code_counts(
    rows: tuple[ResearchTeamSpecialistCalibrationLearningPriorityRow, ...],
) -> tuple[ResearchTeamSpecialistCalibrationLearningPriorityReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchTeamSpecialistCalibrationLearningPriorityReasonCodeCount(
                reason_code=EMPTY_REPORT_REASON_CODE,
                count=_count(1),
                specialist_ratio=ONE_RATIO,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        for reason_code in row.reason_codes:
            counter[reason_code] += 1
    denominator = _count(len(rows))
    priority = {
        reason_code: index
        for index, reason_code in enumerate(REASON_CODE_COUNT_PRIORITY)
    }
    return tuple(
        ResearchTeamSpecialistCalibrationLearningPriorityReasonCodeCount(
            reason_code=reason_code,
            count=count,
            specialist_ratio=_ratio(count, denominator),
        )
        for count, reason_code in sorted(
            ((_count(count), reason_code) for reason_code, count in counter.items()),
            key=lambda item: (-item[0], priority.get(item[1], 999), item[1]),
        )
    )


def _row_sort_key(
    row: ResearchTeamSpecialistCalibrationLearningPriorityRow,
) -> tuple[Decimal, Decimal, Decimal, str, str]:
    return (
        -STATUS_WEIGHT[row.status],
        -row.learning_priority_score,
        -row.recent_miss_severity,
        row.learning_track,
        row.specialist_key,
    )


def _status_count(
    rows: tuple[ResearchTeamSpecialistCalibrationLearningPriorityRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(row.status == status for row in rows))


def _learning_priority_team_count(
    rows: tuple[ResearchTeamSpecialistCalibrationLearningPriorityRow, ...],
) -> Decimal:
    return _count(sum(row.status != "pass" for row in rows))


def _validate_config(
    config: ResearchTeamSpecialistCalibrationLearningPriorityConfig,
) -> None:
    with localcontext(DECIMAL_CONTEXT):
        weights_total = (
            config.recent_miss_severity_weight
            + config.calibration_age_weight
            + config.feedback_absorption_weight
            + config.evidence_reuse_quality_weight
            + config.review_backlog_pressure_weight
        ).quantize(RATIO_QUANTUM)
    if weights_total != ONE_RATIO:
        raise ValueError("weights must sum to 1.000000")
    if config.watch_priority_score_floor > config.block_priority_score_floor:
        raise ValueError(
            "block_priority_score_floor must be at least watch_priority_score_floor",
        )
    if config.watch_recent_miss_severity > config.block_recent_miss_severity:
        raise ValueError(
            "block_recent_miss_severity must be at least watch_recent_miss_severity",
        )
    if config.max_pass_calibration_age_days > config.max_watch_calibration_age_days:
        raise ValueError(
            "max_watch_calibration_age_days must be at least "
            "max_pass_calibration_age_days",
        )
    if (
        config.min_watch_feedback_absorption_ratio
        > config.min_pass_feedback_absorption_ratio
    ):
        raise ValueError(
            "min_watch_feedback_absorption_ratio must not exceed "
            "min_pass_feedback_absorption_ratio",
        )
    if config.min_watch_evidence_reuse_quality > config.min_pass_evidence_reuse_quality:
        raise ValueError(
            "min_watch_evidence_reuse_quality must not exceed "
            "min_pass_evidence_reuse_quality",
        )
    if config.max_pass_review_backlog_pressure > config.max_watch_review_backlog_pressure:
        raise ValueError(
            "max_watch_review_backlog_pressure must be at least "
            "max_pass_review_backlog_pressure",
        )


def _validate_row(
    row: ResearchTeamSpecialistCalibrationLearningPriorityRow,
) -> None:
    if PASS_ROW_REASON_CODE in row.reason_codes and row.status != "pass":
        raise ValueError("pass reason_codes must match pass status")


def _validate_report_materialized_fields(
    report: ResearchTeamSpecialistCalibrationLearningPriorityReport,
) -> None:
    rows = report.rows
    checks = {
        "specialist_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "learning_priority_team_count": _learning_priority_team_count(rows),
        "average_learning_priority_score": _mean_decimal(
            tuple(row.learning_priority_score for row in rows),
        ),
        "max_learning_priority_score": _max_decimal(
            tuple(row.learning_priority_score for row in rows),
        ),
        "min_learning_priority_score": _min_decimal(
            tuple(row.learning_priority_score for row in rows),
        ),
        "average_recent_miss_severity": _mean_decimal(
            tuple(row.recent_miss_severity for row in rows),
        ),
        "max_calibration_age_days": _max_decimal(
            tuple(row.calibration_age_days for row in rows),
            count=True,
        ),
        "min_feedback_absorption_ratio": _min_decimal(
            tuple(row.feedback_absorption_ratio for row in rows),
        ),
        "min_evidence_reuse_quality": _min_decimal(
            tuple(row.evidence_reuse_quality for row in rows),
        ),
        "max_review_backlog_pressure": _max_decimal(
            tuple(row.review_backlog_pressure for row in rows),
        ),
    }
    for field_name, expected in checks.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.status != _rollup_status(tuple(row.status for row in rows)):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _require_rows(
    rows: tuple[ResearchTeamSpecialistCalibrationLearningPriorityRow, ...],
) -> tuple[ResearchTeamSpecialistCalibrationLearningPriorityRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchTeamSpecialistCalibrationLearningPriorityRow:
            raise ValueError(
                "rows must contain "
                "ResearchTeamSpecialistCalibrationLearningPriorityRow",
            )
        _require_hard_flags("row", row)
        if row.specialist_key in seen:
            raise ValueError("rows must contain unique specialist_key values")
        seen.add(row.specialist_key)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted by status and priority")
    return normalized


def _require_reason_code_counts(
    rows: tuple[
        ResearchTeamSpecialistCalibrationLearningPriorityReasonCodeCount,
        ...,
    ],
) -> tuple[ResearchTeamSpecialistCalibrationLearningPriorityReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for row in normalized:
        if (
            type(row)
            is not ResearchTeamSpecialistCalibrationLearningPriorityReasonCodeCount
        ):
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchTeamSpecialistCalibrationLearningPriorityReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", row)
    if len({row.reason_code for row in normalized}) != len(normalized):
        raise ValueError("reason_code_counts reason_code values must be unique")
    return normalized


def _require_row_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not normalized:
        raise ValueError("reason_codes must be non-empty")
    for reason_code in normalized:
        _require_public_text("reason_code", reason_code)
        if reason_code not in ROW_REASON_CODES:
            raise ValueError("reason_code must be supported")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    if normalized != tuple(reason for reason in ROW_REASON_CODES if reason in normalized):
        raise ValueError("reason_codes must be sorted")
    if PASS_ROW_REASON_CODE in normalized and len(normalized) != 1:
        raise ValueError("pass reason_codes must not be mixed with priority reasons")
    return normalized


def _require_report_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not normalized:
        raise ValueError("reason_codes must be non-empty")
    for reason_code in normalized:
        _require_public_text("reason_code", reason_code)
        if reason_code not in REPORT_REASON_CODES:
            raise ValueError("reason_code must be supported")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    return normalized


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _require_safe_identifier(field_name: str, value: object) -> None:
    _require_public_text(field_name, value)
    if any(character not in SAFE_IDENTIFIER_CHARS for character in value):
        raise ValueError(f"{field_name} must be lowercase snake case")
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_IDENTIFIER_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public text")


def _require_public_text(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical non-empty string")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")
    _reject_unsafe_public_value(field_name, value)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if value.is_nan() or value.is_infinite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be non-negative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return normalized.quantize(COUNT_QUANTUM)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be non-negative")
    return _quantize_ratio(normalized)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE_RATIO:
        raise ValueError(f"{field_name} must be no greater than 1")
    return normalized


def _quantize_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _clamp_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return min(ONE_RATIO, max(ZERO_RATIO, value)).quantize(RATIO_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO_COUNT:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(RATIO_QUANTUM)


def _mean_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (sum(values, ZERO_RATIO) / Decimal(len(values))).quantize(RATIO_QUANTUM)


def _max_decimal(values: tuple[Decimal, ...], *, count: bool = False) -> Decimal:
    if not values:
        return ZERO_COUNT if count else ZERO_RATIO
    value = max(values)
    return value.quantize(COUNT_QUANTUM if count else RATIO_QUANTUM)


def _min_decimal(values: tuple[Decimal, ...], *, count: bool = False) -> Decimal:
    if not values:
        return ZERO_COUNT if count else ZERO_RATIO
    value = min(values)
    return value.quantize(COUNT_QUANTUM if count else RATIO_QUANTUM)


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if len(value) != 64 or any(character not in HEX_CHARS for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _derived_validation_digest(
    report: ResearchTeamSpecialistCalibrationLearningPriorityReport,
) -> str:
    payload = _report_payload_base(report)
    return _payload_validation_digest(payload)


def _payload_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = _strip_digest(payload)
    canonical = json.dumps(
        digest_payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _strip_digest(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _strip_digest(item)
            for key, item in sorted(value.items())
            if key != "derived_validation_digest"
        }
    if isinstance(value, list):
        return [_strip_digest(item) for item in value]
    return value


def _report_payload(
    report: ResearchTeamSpecialistCalibrationLearningPriorityReport,
) -> dict[str, Any]:
    payload = _report_payload_base(report)
    payload["derived_validation_digest"] = report.derived_validation_digest
    return payload


def _report_payload_base(
    report: ResearchTeamSpecialistCalibrationLearningPriorityReport,
) -> dict[str, Any]:
    return {
        "config_version": report.config_version,
        "specialist_count": str(report.specialist_count),
        "pass_count": str(report.pass_count),
        "watch_count": str(report.watch_count),
        "block_count": str(report.block_count),
        "learning_priority_team_count": str(report.learning_priority_team_count),
        "average_learning_priority_score": str(
            report.average_learning_priority_score,
        ),
        "max_learning_priority_score": str(report.max_learning_priority_score),
        "min_learning_priority_score": str(report.min_learning_priority_score),
        "average_recent_miss_severity": str(report.average_recent_miss_severity),
        "max_calibration_age_days": str(report.max_calibration_age_days),
        "min_feedback_absorption_ratio": str(
            report.min_feedback_absorption_ratio,
        ),
        "min_evidence_reuse_quality": str(report.min_evidence_reuse_quality),
        "max_review_backlog_pressure": str(report.max_review_backlog_pressure),
        "status": report.status,
        "reason_codes": list(report.reason_codes),
        "reason_code_counts": [
            _reason_code_count_payload(row) for row in report.reason_code_counts
        ],
        "rows": [_row_payload(row) for row in report.rows],
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _reason_code_count_payload(
    row: ResearchTeamSpecialistCalibrationLearningPriorityReasonCodeCount,
) -> dict[str, Any]:
    return {
        "reason_code": row.reason_code,
        "count": str(row.count),
        "specialist_ratio": str(row.specialist_ratio),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _row_payload(
    row: ResearchTeamSpecialistCalibrationLearningPriorityRow,
) -> dict[str, Any]:
    return {
        "specialist_digest": _public_digest(row.specialist_key),
        "track_digest": _public_digest(row.learning_track),
        "status": row.status,
        "recent_miss_severity": str(row.recent_miss_severity),
        "calibration_age_days": str(row.calibration_age_days),
        "calibration_age_pressure_score": str(row.calibration_age_pressure_score),
        "feedback_absorption_ratio": str(row.feedback_absorption_ratio),
        "feedback_gap_score": str(row.feedback_gap_score),
        "evidence_reuse_quality": str(row.evidence_reuse_quality),
        "evidence_gap_score": str(row.evidence_gap_score),
        "review_backlog_pressure": str(row.review_backlog_pressure),
        "learning_priority_score": str(row.learning_priority_score),
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _public_digest(value: str) -> str:
    return "sha256:" + sha256(value.encode("utf-8")).hexdigest()


def _reject_public_numeric_values(value: object) -> None:
    if type(value) in (int, float):
        raise ValueError("public payload numeric values must be Decimal-derived strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
    elif isinstance(value, list):
        for item in value:
            _reject_public_numeric_values(item)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_payload(field.name, getattr(value, field.name))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} contains unsafe public key")
            _reject_unsafe_public_key("public key", key)
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{key} must be True")
            _reject_unsafe_public_payload(key, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_value(label, value)


def _reject_unsafe_public_key(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_KEY_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public text")


def _reject_unsafe_public_value(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public text")
