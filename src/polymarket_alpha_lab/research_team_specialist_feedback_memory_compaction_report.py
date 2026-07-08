"""Pure report-only reducer for sanitized specialist feedback memory compaction."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
from typing import Any, Iterable


DEFAULT_RESEARCH_TEAM_SPECIALIST_FEEDBACK_MEMORY_COMPACTION_REPORT_CONFIG_VERSION = (
    "research-team-specialist-feedback-memory-compaction-report-v0"
)
RESEARCH_TEAM_SPECIALIST_FEEDBACK_MEMORY_COMPACTION_STATUSES = (
    "pass",
    "watch",
    "block",
)
RESEARCH_TEAM_SPECIALIST_FEEDBACK_MEMORY_COMPACTION_REASON_CODES = (
    "no_feedback_memory_compaction_inputs",
    "feedback_absorption_block",
    "feedback_absorption_watch",
    "calibration_freshness_block",
    "calibration_freshness_watch",
    "error_recurrence_block",
    "error_recurrence_watch",
    "evidence_reuse_block",
    "evidence_reuse_watch",
    "review_latency_block",
    "review_latency_watch",
    "feedback_memory_compaction_block",
    "feedback_memory_compaction_watch",
    "feedback_memory_compaction_pass",
)

_DIGEST_FIELD = "derived_validation_digest"
_COUNT_QUANTUM = Decimal("1")
_SIX_PLACE_QUANTUM = Decimal("0.000001")
_ZERO_COUNT = Decimal("0")
_ZERO_SCORE = Decimal("0.000000")
_ONE_SCORE = Decimal("1.000000")
_SECONDS_PER_DAY = Decimal("86400")
_MICROSECONDS_PER_SECOND = Decimal("1000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_UP)
_STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
_ROW_REASON_SEQUENCE = RESEARCH_TEAM_SPECIALIST_FEEDBACK_MEMORY_COMPACTION_REASON_CODES[1:]
_REPORT_REASON_SEQUENCE = RESEARCH_TEAM_SPECIALIST_FEEDBACK_MEMORY_COMPACTION_REASON_CODES[1:-1]
_UNSAFE_PUBLIC_HEXES = (
    "63616e6469646174655f6964",
    "63616e6469646174652d",
    "6d61726b65745f6964",
    "6d61726b65745f736c7567",
    "7175657374696f6e",
    "736f757263655f75726c",
    "736f757263655f74657874",
    "687474703a2f2f",
    "68747470733a2f2f",
    "3a2f2f",
    "64736e",
    "706f7374677265733a2f2f",
    "7461626c655f6e616d65",
    "746f6b656e",
    "736563726574",
    "61757468",
    "77616c6c6574",
    "6f72646572",
    "7472616465",
    "74726164696e67",
    "627579",
    "73656c6c",
    "6e6574776f726b",
    "6461746162617365",
    "6c697665",
    "7265636f6d6d656e64",
    "73697a696e67",
)
_UNSAFE_PUBLIC_FRAGMENTS = tuple(
    bytes.fromhex(value).decode("ascii") for value in _UNSAFE_PUBLIC_HEXES
)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_SPECIALIST_FEEDBACK_MEMORY_COMPACTION_REPORT_CONFIG_VERSION",
    "RESEARCH_TEAM_SPECIALIST_FEEDBACK_MEMORY_COMPACTION_STATUSES",
    "RESEARCH_TEAM_SPECIALIST_FEEDBACK_MEMORY_COMPACTION_REASON_CODES",
    "ResearchTeamSpecialistFeedbackMemoryCompactionConfig",
    "ResearchTeamSpecialistFeedbackMemoryCompactionInput",
    "ResearchTeamSpecialistFeedbackMemoryCompactionReport",
    "ResearchTeamSpecialistFeedbackMemoryCompactionRow",
    "build_research_team_specialist_feedback_memory_compaction_report",
    "research_team_specialist_feedback_memory_compaction_report_payload",
)


@dataclass(frozen=True)
class ResearchTeamSpecialistFeedbackMemoryCompactionConfig:
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_SPECIALIST_FEEDBACK_MEMORY_COMPACTION_REPORT_CONFIG_VERSION
    )
    min_pass_feedback_absorption_ratio: Decimal = Decimal("0.800000")
    min_watch_feedback_absorption_ratio: Decimal = Decimal("0.500000")
    calibration_watch_age_seconds: Decimal = Decimal("604800.000000")
    calibration_block_age_seconds: Decimal = Decimal("2592000.000000")
    recurrence_watch_count: Decimal = Decimal("2")
    recurrence_block_count: Decimal = Decimal("5")
    recurrence_penalty_per_error: Decimal = Decimal("0.200000")
    min_pass_evidence_reuse_ratio: Decimal = Decimal("0.750000")
    min_watch_evidence_reuse_ratio: Decimal = Decimal("0.500000")
    review_latency_pass_seconds: Decimal = Decimal("86400.000000")
    review_latency_watch_seconds: Decimal = Decimal("172800.000000")
    review_latency_block_seconds: Decimal = Decimal("604800.000000")
    quality_pass_threshold: Decimal = Decimal("0.750000")
    quality_watch_threshold: Decimal = Decimal("0.500000")
    feedback_absorption_weight: Decimal = Decimal("0.250000")
    calibration_freshness_weight: Decimal = Decimal("0.200000")
    error_recurrence_weight: Decimal = Decimal("0.200000")
    evidence_reuse_weight: Decimal = Decimal("0.200000")
    review_latency_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchTeamSpecialistFeedbackMemoryCompactionConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            ResearchTeamSpecialistFeedbackMemoryCompactionConfig,
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_SPECIALIST_FEEDBACK_MEMORY_COMPACTION_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported version")
        for field_name in (
            "min_pass_feedback_absorption_ratio",
            "min_watch_feedback_absorption_ratio",
            "recurrence_penalty_per_error",
            "min_pass_evidence_reuse_ratio",
            "min_watch_evidence_reuse_ratio",
            "quality_pass_threshold",
            "quality_watch_threshold",
            "feedback_absorption_weight",
            "calibration_freshness_weight",
            "error_recurrence_weight",
            "evidence_reuse_weight",
            "review_latency_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "calibration_watch_age_seconds",
            "calibration_block_age_seconds",
            "review_latency_pass_seconds",
            "review_latency_watch_seconds",
            "review_latency_block_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_six_place_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("recurrence_watch_count", "recurrence_block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        if (
            self.min_pass_feedback_absorption_ratio
            <= self.min_watch_feedback_absorption_ratio
        ):
            raise ValueError(
                "min_pass_feedback_absorption_ratio must exceed watch threshold",
            )
        if self.calibration_block_age_seconds <= self.calibration_watch_age_seconds:
            raise ValueError("calibration_block_age_seconds must exceed watch threshold")
        if self.recurrence_block_count <= self.recurrence_watch_count:
            raise ValueError("recurrence_block_count must exceed watch threshold")
        if self.min_pass_evidence_reuse_ratio <= self.min_watch_evidence_reuse_ratio:
            raise ValueError("min_pass_evidence_reuse_ratio must exceed watch threshold")
        if self.review_latency_watch_seconds <= self.review_latency_pass_seconds:
            raise ValueError("review_latency_watch_seconds must exceed pass threshold")
        if self.review_latency_block_seconds <= self.review_latency_watch_seconds:
            raise ValueError("review_latency_block_seconds must exceed watch threshold")
        if self.quality_pass_threshold <= self.quality_watch_threshold:
            raise ValueError("quality_pass_threshold must exceed watch threshold")
        weight_sum = _six(
            self.feedback_absorption_weight
            + self.calibration_freshness_weight
            + self.error_recurrence_weight
            + self.evidence_reuse_weight
            + self.review_latency_weight,
        )
        if weight_sum != _ONE_SCORE:
            raise ValueError("weights must sum to 1")
        _require_hard_flags(self)
        _reject_unsafe_public_surface("config", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistFeedbackMemoryCompactionInput:
    team_ref: str
    specialist_ref: str
    feedback_memory_digest: str
    feedback_absorption_ratio: Decimal
    calibration_refreshed_at: datetime
    recurring_error_count: Decimal
    evidence_reuse_ratio: Decimal
    feedback_received_at: datetime
    review_completed_at: datetime
    sanitized_feedback_confirmed: bool = True
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchTeamSpecialistFeedbackMemoryCompactionInput does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "input",
            self,
            ResearchTeamSpecialistFeedbackMemoryCompactionInput,
        )
        for field_name in ("team_ref", "specialist_ref"):
            _require_public_label(field_name, getattr(self, field_name))
        _require_digest("feedback_memory_digest", self.feedback_memory_digest)
        for field_name in ("feedback_absorption_ratio", "evidence_reuse_ratio"):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "recurring_error_count",
            _normalize_nonnegative_count(
                "recurring_error_count",
                self.recurring_error_count,
            ),
        )
        for field_name in (
            "calibration_refreshed_at",
            "feedback_received_at",
            "review_completed_at",
        ):
            object.__setattr__(self, field_name, _as_utc(field_name, getattr(self, field_name)))
        if self.review_completed_at < self.feedback_received_at:
            raise ValueError("review_completed_at must be at or after feedback_received_at")
        if self.sanitized_feedback_confirmed is not True:
            raise ValueError("sanitized_feedback_confirmed must be True")
        _require_hard_flags(self)
        _reject_unsafe_public_surface("input", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistFeedbackMemoryCompactionRow:
    team_ref: str
    specialist_ref: str
    feedback_memory_digest: str
    feedback_absorption_ratio: Decimal
    calibration_refreshed_at: datetime
    recurring_error_count: Decimal
    evidence_reuse_ratio: Decimal
    feedback_received_at: datetime
    review_completed_at: datetime
    calibration_age_seconds: Decimal
    review_latency_seconds: Decimal
    calibration_freshness_score: Decimal
    error_recurrence_score: Decimal
    review_latency_score: Decimal
    long_term_memory_quality_score: Decimal
    row_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchTeamSpecialistFeedbackMemoryCompactionRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchTeamSpecialistFeedbackMemoryCompactionRow)
        for field_name in ("team_ref", "specialist_ref"):
            _require_public_label(field_name, getattr(self, field_name))
        _require_digest("feedback_memory_digest", self.feedback_memory_digest)
        for field_name in ("calibration_refreshed_at", "feedback_received_at", "review_completed_at"):
            object.__setattr__(self, field_name, _as_utc(field_name, getattr(self, field_name)))
        for field_name in ("feedback_absorption_ratio", "evidence_reuse_ratio"):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "recurring_error_count",
            _normalize_nonnegative_count(
                "recurring_error_count",
                self.recurring_error_count,
            ),
        )
        for field_name in ("calibration_age_seconds", "review_latency_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_six_place_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "calibration_freshness_score",
            "error_recurrence_score",
            "review_latency_score",
            "long_term_memory_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("row_status", self.row_status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        if self.review_completed_at < self.feedback_received_at:
            raise ValueError("review_completed_at must be at or after feedback_received_at")
        if self.row_status != _row_status(self.reason_codes):
            raise ValueError("row_status must match reason_codes")
        _require_hard_flags(self)
        _reject_unsafe_public_surface("row", self)
        _require_or_set_digest(self)


@dataclass(frozen=True)
class ResearchTeamSpecialistFeedbackMemoryCompactionReport:
    generated_at: datetime
    config_version: str
    status: str
    feedback_memory_count: Decimal
    row_count: Decimal
    specialist_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    absorption_gap_count: Decimal
    stale_calibration_count: Decimal
    recurrence_penalty_count: Decimal
    low_evidence_reuse_count: Decimal
    review_latency_breach_count: Decimal
    average_long_term_memory_quality_score: Decimal
    rows: tuple[ResearchTeamSpecialistFeedbackMemoryCompactionRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchTeamSpecialistFeedbackMemoryCompactionReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchTeamSpecialistFeedbackMemoryCompactionReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "feedback_memory_count",
            "row_count",
            "specialist_count",
            "pass_count",
            "watch_count",
            "block_count",
            "absorption_gap_count",
            "stale_calibration_count",
            "recurrence_penalty_count",
            "low_evidence_reuse_count",
            "review_latency_breach_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_long_term_memory_quality_score",
            _normalize_unit_decimal(
                "average_long_term_memory_quality_score",
                self.average_long_term_memory_quality_score,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_report(self)
        _require_hard_flags(self)
        _reject_unsafe_public_surface("report", self)
        _require_or_set_digest(self)

    @property
    def public_payload(self) -> dict[str, Any]:
        _validate_digest(self)
        payload = _payload_value(self)
        if type(payload) is not dict:
            raise ValueError("public_payload must be a JSON object")
        _require_hard_flags(_DictFlags(payload))
        _reject_unsafe_public_surface("public_payload", payload)
        _validate_payload_digest(payload)
        return payload


def build_research_team_specialist_feedback_memory_compaction_report(
    inputs: Iterable[ResearchTeamSpecialistFeedbackMemoryCompactionInput],
    *,
    config: ResearchTeamSpecialistFeedbackMemoryCompactionConfig,
    generated_at: datetime,
) -> ResearchTeamSpecialistFeedbackMemoryCompactionReport:
    _require_exact_type(
        "config",
        config,
        ResearchTeamSpecialistFeedbackMemoryCompactionConfig,
    )
    _require_hard_flags(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    items = _normalize_inputs(inputs)
    for item in items:
        if _seconds_between(item.calibration_refreshed_at, generated_at_utc) < _ZERO_SCORE:
            raise ValueError("generated_at must be at or after calibration_refreshed_at")
        if _seconds_between(item.review_completed_at, generated_at_utc) < _ZERO_SCORE:
            raise ValueError("generated_at must be at or after review_completed_at")
    rows = tuple(
        sorted(
            (_row_from_input(item, config=config, generated_at=generated_at_utc) for item in items),
            key=_row_sort_key,
        ),
    )
    return ResearchTeamSpecialistFeedbackMemoryCompactionReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_report_status(rows),
        feedback_memory_count=_count(len(items)),
        row_count=_count(len(rows)),
        specialist_count=_count(len({(row.team_ref, row.specialist_ref) for row in rows})),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        absorption_gap_count=_reason_count(
            rows,
            "feedback_absorption_watch",
            "feedback_absorption_block",
        ),
        stale_calibration_count=_reason_count(
            rows,
            "calibration_freshness_watch",
            "calibration_freshness_block",
        ),
        recurrence_penalty_count=_reason_count(
            rows,
            "error_recurrence_watch",
            "error_recurrence_block",
        ),
        low_evidence_reuse_count=_reason_count(
            rows,
            "evidence_reuse_watch",
            "evidence_reuse_block",
        ),
        review_latency_breach_count=_reason_count(
            rows,
            "review_latency_watch",
            "review_latency_block",
        ),
        average_long_term_memory_quality_score=_average_quality(rows),
        rows=rows,
        reason_codes=_report_reason_codes(rows),
    )


def research_team_specialist_feedback_memory_compaction_report_payload(
    report: ResearchTeamSpecialistFeedbackMemoryCompactionReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchTeamSpecialistFeedbackMemoryCompactionReport:
        _require_hard_flags(report)
        _reject_unsafe_public_surface("report", report)
        return report.public_payload
    if type(report) is dict:
        _require_hard_flags(_DictFlags(report))
        _reject_unsafe_public_surface("public_payload", report)
        _validate_payload_digest(report)
        return report
    raise ValueError(
        "report must be a ResearchTeamSpecialistFeedbackMemoryCompactionReport or public payload",
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
    item: ResearchTeamSpecialistFeedbackMemoryCompactionInput,
    *,
    config: ResearchTeamSpecialistFeedbackMemoryCompactionConfig,
    generated_at: datetime,
) -> ResearchTeamSpecialistFeedbackMemoryCompactionRow:
    calibration_age_seconds = _seconds_between(item.calibration_refreshed_at, generated_at)
    review_latency_seconds = _seconds_between(item.feedback_received_at, item.review_completed_at)
    calibration_freshness_score = _age_score(
        age_seconds=calibration_age_seconds,
        full_score_seconds=config.calibration_watch_age_seconds,
        no_score_seconds=config.calibration_block_age_seconds,
    )
    error_recurrence_score = _recurrence_score(item.recurring_error_count, config)
    review_latency_score = _age_score(
        age_seconds=review_latency_seconds,
        full_score_seconds=config.review_latency_pass_seconds,
        no_score_seconds=config.review_latency_block_seconds,
    )
    quality_score = _quality_score(
        item=item,
        calibration_freshness_score=calibration_freshness_score,
        error_recurrence_score=error_recurrence_score,
        review_latency_score=review_latency_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        item=item,
        calibration_age_seconds=calibration_age_seconds,
        review_latency_seconds=review_latency_seconds,
        quality_score=quality_score,
        config=config,
    )
    return ResearchTeamSpecialistFeedbackMemoryCompactionRow(
        team_ref=item.team_ref,
        specialist_ref=item.specialist_ref,
        feedback_memory_digest=item.feedback_memory_digest,
        feedback_absorption_ratio=item.feedback_absorption_ratio,
        calibration_refreshed_at=item.calibration_refreshed_at,
        recurring_error_count=item.recurring_error_count,
        evidence_reuse_ratio=item.evidence_reuse_ratio,
        feedback_received_at=item.feedback_received_at,
        review_completed_at=item.review_completed_at,
        calibration_age_seconds=calibration_age_seconds,
        review_latency_seconds=review_latency_seconds,
        calibration_freshness_score=calibration_freshness_score,
        error_recurrence_score=error_recurrence_score,
        review_latency_score=review_latency_score,
        long_term_memory_quality_score=quality_score,
        row_status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _quality_score(
    *,
    item: ResearchTeamSpecialistFeedbackMemoryCompactionInput,
    calibration_freshness_score: Decimal,
    error_recurrence_score: Decimal,
    review_latency_score: Decimal,
    config: ResearchTeamSpecialistFeedbackMemoryCompactionConfig,
) -> Decimal:
    return _six(
        item.feedback_absorption_ratio * config.feedback_absorption_weight
        + calibration_freshness_score * config.calibration_freshness_weight
        + error_recurrence_score * config.error_recurrence_weight
        + item.evidence_reuse_ratio * config.evidence_reuse_weight
        + review_latency_score * config.review_latency_weight,
    )


def _age_score(
    *,
    age_seconds: Decimal,
    full_score_seconds: Decimal,
    no_score_seconds: Decimal,
) -> Decimal:
    if age_seconds <= full_score_seconds:
        return _ONE_SCORE
    if age_seconds >= no_score_seconds:
        return _ZERO_SCORE
    return _six(_ONE_SCORE - (age_seconds / no_score_seconds))


def _recurrence_score(
    recurring_error_count: Decimal,
    config: ResearchTeamSpecialistFeedbackMemoryCompactionConfig,
) -> Decimal:
    score = _six(_ONE_SCORE - (recurring_error_count * config.recurrence_penalty_per_error))
    if score < _ZERO_SCORE:
        return _ZERO_SCORE
    return score


def _row_reason_codes(
    *,
    item: ResearchTeamSpecialistFeedbackMemoryCompactionInput,
    calibration_age_seconds: Decimal,
    review_latency_seconds: Decimal,
    quality_score: Decimal,
    config: ResearchTeamSpecialistFeedbackMemoryCompactionConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if item.feedback_absorption_ratio < config.min_watch_feedback_absorption_ratio:
        reasons.append("feedback_absorption_block")
    elif item.feedback_absorption_ratio < config.min_pass_feedback_absorption_ratio:
        reasons.append("feedback_absorption_watch")
    if calibration_age_seconds >= config.calibration_block_age_seconds:
        reasons.append("calibration_freshness_block")
    elif calibration_age_seconds >= config.calibration_watch_age_seconds:
        reasons.append("calibration_freshness_watch")
    if item.recurring_error_count >= config.recurrence_block_count:
        reasons.append("error_recurrence_block")
    elif item.recurring_error_count >= config.recurrence_watch_count:
        reasons.append("error_recurrence_watch")
    if item.evidence_reuse_ratio < config.min_watch_evidence_reuse_ratio:
        reasons.append("evidence_reuse_block")
    elif item.evidence_reuse_ratio < config.min_pass_evidence_reuse_ratio:
        reasons.append("evidence_reuse_watch")
    if review_latency_seconds >= config.review_latency_block_seconds:
        reasons.append("review_latency_block")
    elif review_latency_seconds >= config.review_latency_watch_seconds:
        reasons.append("review_latency_watch")
    if quality_score < config.quality_watch_threshold:
        reasons.append("feedback_memory_compaction_block")
    elif quality_score < config.quality_pass_threshold:
        reasons.append("feedback_memory_compaction_watch")
    elif not reasons:
        reasons.append("feedback_memory_compaction_pass")
    return tuple(reason for reason in _ROW_REASON_SEQUENCE if reason in reasons)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if reason_codes == ("feedback_memory_compaction_pass",):
        return "pass"
    return "watch"


def _report_status(
    rows: tuple[ResearchTeamSpecialistFeedbackMemoryCompactionRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.row_status == "block" for row in rows):
        return "block"
    if any(row.row_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTeamSpecialistFeedbackMemoryCompactionRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_feedback_memory_compaction_inputs",)
    present = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != "feedback_memory_compaction_pass"
    }
    if not present:
        return ("feedback_memory_compaction_pass",)
    return tuple(reason_code for reason_code in _REPORT_REASON_SEQUENCE if reason_code in present)


def _normalize_inputs(
    values: Iterable[ResearchTeamSpecialistFeedbackMemoryCompactionInput],
) -> tuple[ResearchTeamSpecialistFeedbackMemoryCompactionInput, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        items = tuple(values)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen: set[tuple[str, str, str]] = set()
    for item in items:
        _require_exact_type("input", item, ResearchTeamSpecialistFeedbackMemoryCompactionInput)
        _require_hard_flags(item)
        _reject_unsafe_public_surface("input", item)
        key = (item.team_ref, item.specialist_ref, item.feedback_memory_digest)
        if key in seen:
            raise ValueError("inputs must be unique")
        seen.add(key)
    return items


def _normalize_rows(
    values: Iterable[ResearchTeamSpecialistFeedbackMemoryCompactionRow],
) -> tuple[ResearchTeamSpecialistFeedbackMemoryCompactionRow, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("rows must contain feedback memory compaction rows")
    try:
        rows = tuple(values)
    except TypeError as exc:
        raise ValueError("rows must contain feedback memory compaction rows") from exc
    for row in rows:
        _require_exact_type("row", row, ResearchTeamSpecialistFeedbackMemoryCompactionRow)
        _require_hard_flags(row)
        _reject_unsafe_public_surface("row", row)
        _validate_digest(row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sort")
    if len({(row.team_ref, row.specialist_ref, row.feedback_memory_digest) for row in rows}) != len(rows):
        raise ValueError("rows must be unique")
    return rows


def _validate_report(report: ResearchTeamSpecialistFeedbackMemoryCompactionReport) -> None:
    if report.feedback_memory_count != _count(len(report.rows)):
        raise ValueError("feedback_memory_count must match rows")
    if report.row_count != _count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.specialist_count != _count(
        len({(row.team_ref, row.specialist_ref) for row in report.rows}),
    ):
        raise ValueError("specialist_count must match rows")
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
    if report.average_long_term_memory_quality_score != _average_quality(report.rows):
        raise ValueError("average_long_term_memory_quality_score must match rows")


def _row_sort_key(
    row: ResearchTeamSpecialistFeedbackMemoryCompactionRow,
) -> tuple[int, Decimal, str, str, str]:
    return (
        _STATUS_RANK[row.row_status],
        row.long_term_memory_quality_score,
        row.team_ref,
        row.specialist_ref,
        row.feedback_memory_digest,
    )


def _status_count(
    rows: tuple[ResearchTeamSpecialistFeedbackMemoryCompactionRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.row_status == status))


def _reason_count(
    rows: tuple[ResearchTeamSpecialistFeedbackMemoryCompactionRow, ...],
    watch_reason: str,
    block_reason: str,
) -> Decimal:
    return _count(
        sum(
            1
            for row in rows
            if watch_reason in row.reason_codes or block_reason in row.reason_codes
        ),
    )


def _average_quality(
    rows: tuple[ResearchTeamSpecialistFeedbackMemoryCompactionRow, ...],
) -> Decimal:
    if not rows:
        return _ZERO_SCORE
    return _six(
        sum((row.long_term_memory_quality_score for row in rows), _ZERO_SCORE)
        / _count(len(rows)),
    )


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    whole_seconds = Decimal(delta.days) * _SECONDS_PER_DAY + Decimal(delta.seconds)
    microseconds = Decimal(delta.microseconds) / _MICROSECONDS_PER_SECOND
    return _six(whole_seconds + microseconds)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(_COUNT_QUANTUM)


def _normalize_reason_codes(value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    if not reason_codes:
        raise ValueError("reason_codes must contain at least one value")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must not contain duplicates")
    for reason_code in reason_codes:
        _require_public_string("reason_codes", reason_code)
        if reason_code not in RESEARCH_TEAM_SPECIALIST_FEEDBACK_MEMORY_COMPACTION_REASON_CODES:
            raise ValueError("reason_codes contains an unsupported value")
    return reason_codes


def _require_public_label(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} must be public-safe")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_digest(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if not value.startswith("sha256:") or not _is_sha256_hex(value.removeprefix("sha256:")):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_status(field_name: str, value: object) -> None:
    if (
        type(value) is not str
        or value not in RESEARCH_TEAM_SPECIALIST_FEEDBACK_MEMORY_COMPACTION_STATUSES
    ):
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= _ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal_with_quantum(field_name, value, _COUNT_QUANTUM)
    if normalized < _ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_six_place_decimal(field_name, value)
    if normalized > _ONE_SCORE:
        raise ValueError(f"{field_name} must be at most one")
    return normalized


def _normalize_positive_six_place_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_six_place_decimal(field_name, value)
    if normalized <= _ZERO_SCORE:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_six_place_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal_with_quantum(field_name, value, _SIX_PLACE_QUANTUM)
    if normalized < _ZERO_SCORE:
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


def _six(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_SIX_PLACE_QUANTUM)


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
        if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
            raise ValueError(f"unsafe public label in {label}")


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


def _validate_digest(value: object) -> None:
    current = getattr(value, _DIGEST_FIELD)
    if type(current) is not str or current != _derived_digest(value):
        raise ValueError("derived_validation_digest does not match derived payload")
    if not _is_sha256_hex(current):
        raise ValueError("derived_validation_digest must be sha256 hex")


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
    if type(value) is Decimal:
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
    if type(value) is Decimal:
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
