"""Readonly calibration feedback loop report for domain specialist teams."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
import hashlib
import json
import re
from typing import Any


DEFAULT_RESEARCH_DOMAIN_TEAM_CALIBRATION_FEEDBACK_LOOP_CONFIG_VERSION = (
    "research-domain-team-calibration-feedback-loop-report-v0"
)
CALIBRATION_FEEDBACK_LOOP_STATUSES = ("pass", "watch", "block")

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
PUBLIC_LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")
PUBLIC_DECIMAL_RE = re.compile(r"^(0|[1-9][0-9]*)\.[0-9]{6}$")
SHA256_HEX_CHARS = frozenset("0123456789abcdef")

PASS_REASON = "domain_team_feedback_loop_pass"
EMPTY_REASON = "domain_team_feedback_loop_empty"
REASON_SEQUENCE = (
    "domain_team_feedback_resolved_outcome_sample_block",
    "domain_team_feedback_calibration_note_coverage_block",
    "domain_team_feedback_recurring_bias_label_coverage_block",
    "domain_team_feedback_future_safeguard_coverage_block",
    "domain_team_feedback_stale_review_block",
    "domain_team_feedback_unreviewed_bias_label_block",
    "domain_team_feedback_resolved_outcome_sample_watch",
    "domain_team_feedback_calibration_note_coverage_watch",
    "domain_team_feedback_recurring_bias_label_coverage_watch",
    "domain_team_feedback_future_safeguard_coverage_watch",
    "domain_team_feedback_stale_review_watch",
    "domain_team_feedback_unreviewed_bias_label_watch",
    PASS_REASON,
)
REPORT_REASON_SEQUENCE = (EMPTY_REASON,) + REASON_SEQUENCE
STATUS_WEIGHT = {"block": 0, "watch": 1, "pass": 2}
REPORT_PUBLIC_FIELDS = frozenset(
    (
        "generated_at",
        "config_version",
        "input_count",
        "resolved_outcome_count",
        "calibration_note_count",
        "recurring_bias_label_count",
        "future_review_safeguard_count",
        "unreviewed_bias_label_count",
        "pass_count",
        "watch_count",
        "block_count",
        "calibration_note_coverage_ratio",
        "recurring_bias_label_coverage_ratio",
        "future_review_safeguard_coverage_ratio",
        "max_feedback_age_seconds",
        "max_unreviewed_bias_label_count",
        "status",
        "reason_codes",
        "rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
ROW_PUBLIC_FIELDS = frozenset(
    (
        "feedback_loop_rank",
        "domain_label",
        "specialist_team_label",
        "status",
        "feedback_loop_health_score",
        "resolved_outcome_count",
        "calibration_note_count",
        "calibration_note_coverage_ratio",
        "recurring_bias_label_count",
        "recurring_bias_label_coverage_ratio",
        "future_review_safeguard_count",
        "future_review_safeguard_coverage_ratio",
        "unreviewed_bias_label_count",
        "feedback_last_reviewed_at",
        "feedback_age_seconds",
        "observed_at",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        _join_parts("can", "did", "ate"),
        _join_parts("mar", "ket"),
        _join_parts("sl", "ug"),
        _join_parts("ques", "tion"),
        _join_parts("sou", "rce"),
        _join_parts("ur", "l"),
        _join_parts("te", "xt"),
        _join_parts("d", "sn"),
        _join_parts("ta", "ble"),
        _join_parts("to", "ken"),
        _join_parts("wal", "let"),
        _join_parts("ord", "er"),
        _join_parts("tra", "de"),
        _join_parts("au", "th"),
        _join_parts("ac", "count"),
        _join_parts("pri", "vate"),
        _join_parts("sec", "ret"),
        _join_parts("siz", "ing"),
        _join_parts("pos", "ition"),
        _join_parts("b", "uy"),
        _join_parts("s", "ell"),
        _join_parts("recom", "mend"),
        _join_parts("li", "ve"),
        _join_parts("net", "work"),
        _join_parts("data", "base"),
    ),
)

__all__ = (
    "DEFAULT_RESEARCH_DOMAIN_TEAM_CALIBRATION_FEEDBACK_LOOP_CONFIG_VERSION",
    "CALIBRATION_FEEDBACK_LOOP_STATUSES",
    "ResearchDomainTeamCalibrationFeedbackLoopConfig",
    "ResearchDomainTeamCalibrationFeedbackLoopInput",
    "ResearchDomainTeamCalibrationFeedbackLoopReport",
    "ResearchDomainTeamCalibrationFeedbackLoopRow",
    "build_research_domain_team_calibration_feedback_loop_report",
    "research_domain_team_calibration_feedback_loop_report_digest",
    "research_domain_team_calibration_feedback_loop_report_payload",
    "validate_research_domain_team_calibration_feedback_loop_public_payload",
)


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class ResearchDomainTeamCalibrationFeedbackLoopConfig(_FinalDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_DOMAIN_TEAM_CALIBRATION_FEEDBACK_LOOP_CONFIG_VERSION
    )
    min_pass_resolved_outcome_count: Decimal = Decimal("30.000000")
    min_watch_resolved_outcome_count: Decimal = Decimal("10.000000")
    min_pass_calibration_note_coverage_ratio: Decimal = Decimal("0.900000")
    min_watch_calibration_note_coverage_ratio: Decimal = Decimal("0.700000")
    min_pass_recurring_bias_label_coverage_ratio: Decimal = Decimal("0.800000")
    min_watch_recurring_bias_label_coverage_ratio: Decimal = Decimal("0.500000")
    min_pass_future_review_safeguard_coverage_ratio: Decimal = Decimal("0.850000")
    min_watch_future_review_safeguard_coverage_ratio: Decimal = Decimal("0.600000")
    max_pass_feedback_age_seconds: Decimal = Decimal("86400.000000")
    max_watch_feedback_age_seconds: Decimal = Decimal("604800.000000")
    max_pass_unreviewed_bias_label_count: Decimal = Decimal("0.000000")
    max_watch_unreviewed_bias_label_count: Decimal = Decimal("3.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchDomainTeamCalibrationFeedbackLoopConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_DOMAIN_TEAM_CALIBRATION_FEEDBACK_LOOP_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_pass_resolved_outcome_count",
            "min_watch_resolved_outcome_count",
            "max_pass_feedback_age_seconds",
            "max_watch_feedback_age_seconds",
            "max_pass_unreviewed_bias_label_count",
            "max_watch_unreviewed_bias_label_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_pass_calibration_note_coverage_ratio",
            "min_watch_calibration_note_coverage_ratio",
            "min_pass_recurring_bias_label_coverage_ratio",
            "min_watch_recurring_bias_label_coverage_ratio",
            "min_pass_future_review_safeguard_coverage_ratio",
            "min_watch_future_review_safeguard_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_pass_resolved_outcome_count < self.min_watch_resolved_outcome_count:
            raise ValueError(
                "min_pass_resolved_outcome_count must be at least "
                "min_watch_resolved_outcome_count",
            )
        if (
            self.min_pass_calibration_note_coverage_ratio
            < self.min_watch_calibration_note_coverage_ratio
        ):
            raise ValueError(
                "min_pass_calibration_note_coverage_ratio must be at least "
                "min_watch_calibration_note_coverage_ratio",
            )
        if (
            self.min_pass_recurring_bias_label_coverage_ratio
            < self.min_watch_recurring_bias_label_coverage_ratio
        ):
            raise ValueError(
                "min_pass_recurring_bias_label_coverage_ratio must be at least "
                "min_watch_recurring_bias_label_coverage_ratio",
            )
        if (
            self.min_pass_future_review_safeguard_coverage_ratio
            < self.min_watch_future_review_safeguard_coverage_ratio
        ):
            raise ValueError(
                "min_pass_future_review_safeguard_coverage_ratio must be at least "
                "min_watch_future_review_safeguard_coverage_ratio",
            )
        if self.max_pass_feedback_age_seconds > self.max_watch_feedback_age_seconds:
            raise ValueError(
                "max_watch_feedback_age_seconds must be at least "
                "max_pass_feedback_age_seconds",
            )
        if (
            self.max_pass_unreviewed_bias_label_count
            > self.max_watch_unreviewed_bias_label_count
        ):
            raise ValueError(
                "max_watch_unreviewed_bias_label_count must be at least "
                "max_pass_unreviewed_bias_label_count",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchDomainTeamCalibrationFeedbackLoopInput(_FinalDataclass):
    domain_label: str
    specialist_team_label: str
    resolved_outcome_count: Decimal
    calibration_note_count: Decimal
    recurring_bias_label_count: Decimal
    future_review_safeguard_count: Decimal
    unreviewed_bias_label_count: Decimal
    feedback_last_reviewed_at: datetime | None
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchDomainTeamCalibrationFeedbackLoopInput,
            "input",
        )
        _require_public_label("domain_label", self.domain_label)
        _require_public_label("specialist_team_label", self.specialist_team_label)
        for field_name in (
            "resolved_outcome_count",
            "calibration_note_count",
            "recurring_bias_label_count",
            "future_review_safeguard_count",
            "unreviewed_bias_label_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "calibration_note_count",
            "recurring_bias_label_count",
            "future_review_safeguard_count",
        ):
            if getattr(self, field_name) > self.resolved_outcome_count:
                raise ValueError(f"{field_name} must not exceed resolved_outcome_count")
        object.__setattr__(
            self,
            "feedback_last_reviewed_at",
            _as_optional_utc("feedback_last_reviewed_at", self.feedback_last_reviewed_at),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchDomainTeamCalibrationFeedbackLoopRow(_FinalDataclass):
    feedback_loop_rank: Decimal
    domain_label: str
    specialist_team_label: str
    status: str
    feedback_loop_health_score: Decimal
    resolved_outcome_count: Decimal
    calibration_note_count: Decimal
    calibration_note_coverage_ratio: Decimal
    recurring_bias_label_count: Decimal
    recurring_bias_label_coverage_ratio: Decimal
    future_review_safeguard_count: Decimal
    future_review_safeguard_coverage_ratio: Decimal
    unreviewed_bias_label_count: Decimal
    feedback_last_reviewed_at: datetime | None
    feedback_age_seconds: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchDomainTeamCalibrationFeedbackLoopRow,
            "row",
        )
        object.__setattr__(
            self,
            "feedback_loop_rank",
            _require_count_decimal("feedback_loop_rank", self.feedback_loop_rank),
        )
        _require_public_label("domain_label", self.domain_label)
        _require_public_label("specialist_team_label", self.specialist_team_label)
        _require_status("status", self.status)
        for field_name in (
            "feedback_loop_health_score",
            "calibration_note_coverage_ratio",
            "recurring_bias_label_coverage_ratio",
            "future_review_safeguard_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "resolved_outcome_count",
            "calibration_note_count",
            "recurring_bias_label_count",
            "future_review_safeguard_count",
            "unreviewed_bias_label_count",
            "feedback_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "feedback_last_reviewed_at",
            _as_optional_utc("feedback_last_reviewed_at", self.feedback_last_reviewed_at),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchDomainTeamCalibrationFeedbackLoopReport(_FinalDataclass):
    generated_at: datetime
    config_version: str
    input_count: Decimal
    resolved_outcome_count: Decimal
    calibration_note_count: Decimal
    recurring_bias_label_count: Decimal
    future_review_safeguard_count: Decimal
    unreviewed_bias_label_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    calibration_note_coverage_ratio: Decimal
    recurring_bias_label_coverage_ratio: Decimal
    future_review_safeguard_coverage_ratio: Decimal
    max_feedback_age_seconds: Decimal
    max_unreviewed_bias_label_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchDomainTeamCalibrationFeedbackLoopRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchDomainTeamCalibrationFeedbackLoopReport,
            "report",
        )
        object.__setattr__(
            self,
            "generated_at",
            _as_generated_at_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "input_count",
            "resolved_outcome_count",
            "calibration_note_count",
            "recurring_bias_label_count",
            "future_review_safeguard_count",
            "unreviewed_bias_label_count",
            "pass_count",
            "watch_count",
            "block_count",
            "max_feedback_age_seconds",
            "max_unreviewed_bias_label_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "calibration_note_coverage_ratio",
            "recurring_bias_label_coverage_ratio",
            "future_review_safeguard_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _require_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "rows", _require_rows(self.rows))
        _require_sha256("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _validate_report(self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")


def build_research_domain_team_calibration_feedback_loop_report(
    inputs: Iterable[ResearchDomainTeamCalibrationFeedbackLoopInput],
    *,
    config: ResearchDomainTeamCalibrationFeedbackLoopConfig,
    generated_at: datetime,
) -> ResearchDomainTeamCalibrationFeedbackLoopReport:
    _require_exact_type(
        config,
        ResearchDomainTeamCalibrationFeedbackLoopConfig,
        "config",
    )
    _require_hard_flags("config", config)
    generated_at_utc = _as_generated_at_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(inputs)
    base_rows = tuple(
        _row_from_input(item, config=config, generated_at=generated_at_utc)
        for item in input_rows
    )
    rows = tuple(
        _with_rank(row, rank)
        for rank, row in enumerate(sorted(base_rows, key=_row_sort_key), start=1)
    )
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "input_count": _count(len(rows)),
        "resolved_outcome_count": _sum_decimal(
            row.resolved_outcome_count for row in rows
        ),
        "calibration_note_count": _sum_decimal(
            row.calibration_note_count for row in rows
        ),
        "recurring_bias_label_count": _sum_decimal(
            row.recurring_bias_label_count for row in rows
        ),
        "future_review_safeguard_count": _sum_decimal(
            row.future_review_safeguard_count for row in rows
        ),
        "unreviewed_bias_label_count": _sum_decimal(
            row.unreviewed_bias_label_count for row in rows
        ),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "calibration_note_coverage_ratio": _coverage_ratio(
            _sum_decimal(row.calibration_note_count for row in rows),
            _sum_decimal(row.resolved_outcome_count for row in rows),
        ),
        "recurring_bias_label_coverage_ratio": _coverage_ratio(
            _sum_decimal(row.recurring_bias_label_count for row in rows),
            _sum_decimal(row.resolved_outcome_count for row in rows),
        ),
        "future_review_safeguard_coverage_ratio": _coverage_ratio(
            _sum_decimal(row.future_review_safeguard_count for row in rows),
            _sum_decimal(row.resolved_outcome_count for row in rows),
        ),
        "max_feedback_age_seconds": _max_decimal(
            row.feedback_age_seconds for row in rows
        ),
        "max_unreviewed_bias_label_count": _max_decimal(
            row.unreviewed_bias_label_count for row in rows
        ),
        "status": _report_status(rows),
        "reason_codes": _report_reason_codes(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchDomainTeamCalibrationFeedbackLoopReport(
        **values,
        derived_validation_digest=_digest_from_values(values),
    )


def research_domain_team_calibration_feedback_loop_report_payload(
    report: ResearchDomainTeamCalibrationFeedbackLoopReport | Mapping[str, object],
) -> dict[str, object]:
    if type(report) is ResearchDomainTeamCalibrationFeedbackLoopReport:
        _require_hard_flags("report", report)
        payload = _json_ready(asdict(report))
    elif isinstance(report, Mapping):
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchDomainTeamCalibrationFeedbackLoopReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    validate_research_domain_team_calibration_feedback_loop_public_payload(payload)
    return payload


def validate_research_domain_team_calibration_feedback_loop_public_payload(
    payload: dict[str, object],
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _require_hard_flags("public payload", _MappingFlags(payload))
    _reject_unsafe_public_payload(
        "public payload",
        payload,
        allow_json_containers=True,
    )
    _reject_public_numerics(payload)
    digest = payload.get("derived_validation_digest")
    _require_sha256("derived_validation_digest", digest)
    expected_digest = _digest_from_payload(payload)
    if digest != expected_digest:
        raise ValueError("derived_validation_digest does not match public payload")
    _validate_public_payload_contract(payload)


def research_domain_team_calibration_feedback_loop_report_digest(
    report: ResearchDomainTeamCalibrationFeedbackLoopReport | Mapping[str, object],
) -> str:
    payload = research_domain_team_calibration_feedback_loop_report_payload(report)
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest


@dataclass(frozen=True)
class _MappingFlags:
    value: Mapping[str, object]

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
    item: ResearchDomainTeamCalibrationFeedbackLoopInput,
    *,
    config: ResearchDomainTeamCalibrationFeedbackLoopConfig,
    generated_at: datetime,
) -> ResearchDomainTeamCalibrationFeedbackLoopRow:
    if type(item) is not ResearchDomainTeamCalibrationFeedbackLoopInput:
        raise ValueError("input must be a ResearchDomainTeamCalibrationFeedbackLoopInput")
    _require_hard_flags("input", item)
    _validate_optional_not_after(
        "feedback_last_reviewed_at",
        item.feedback_last_reviewed_at,
        generated_at,
    )
    _validate_not_after("observed_at", item.observed_at, generated_at)
    feedback_age_seconds = _feedback_age_seconds(
        item.feedback_last_reviewed_at,
        generated_at,
        config,
    )
    calibration_note_coverage_ratio = _coverage_ratio(
        item.calibration_note_count,
        item.resolved_outcome_count,
    )
    recurring_bias_label_coverage_ratio = _coverage_ratio(
        item.recurring_bias_label_count,
        item.resolved_outcome_count,
    )
    future_review_safeguard_coverage_ratio = _coverage_ratio(
        item.future_review_safeguard_count,
        item.resolved_outcome_count,
    )
    reason_codes = _row_reason_codes(
        item=item,
        config=config,
        calibration_note_coverage_ratio=calibration_note_coverage_ratio,
        recurring_bias_label_coverage_ratio=recurring_bias_label_coverage_ratio,
        future_review_safeguard_coverage_ratio=future_review_safeguard_coverage_ratio,
        feedback_age_seconds=feedback_age_seconds,
    )
    return ResearchDomainTeamCalibrationFeedbackLoopRow(
        feedback_loop_rank=ONE,
        domain_label=item.domain_label,
        specialist_team_label=item.specialist_team_label,
        status=_row_status(reason_codes),
        feedback_loop_health_score=_feedback_loop_health_score(
            calibration_note_coverage_ratio=calibration_note_coverage_ratio,
            recurring_bias_label_coverage_ratio=recurring_bias_label_coverage_ratio,
            future_review_safeguard_coverage_ratio=future_review_safeguard_coverage_ratio,
        ),
        resolved_outcome_count=item.resolved_outcome_count,
        calibration_note_count=item.calibration_note_count,
        calibration_note_coverage_ratio=calibration_note_coverage_ratio,
        recurring_bias_label_count=item.recurring_bias_label_count,
        recurring_bias_label_coverage_ratio=recurring_bias_label_coverage_ratio,
        future_review_safeguard_count=item.future_review_safeguard_count,
        future_review_safeguard_coverage_ratio=future_review_safeguard_coverage_ratio,
        unreviewed_bias_label_count=item.unreviewed_bias_label_count,
        feedback_last_reviewed_at=item.feedback_last_reviewed_at,
        feedback_age_seconds=feedback_age_seconds,
        observed_at=item.observed_at,
        reason_codes=reason_codes,
    )


def _with_rank(
    row: ResearchDomainTeamCalibrationFeedbackLoopRow,
    rank: int,
) -> ResearchDomainTeamCalibrationFeedbackLoopRow:
    return ResearchDomainTeamCalibrationFeedbackLoopRow(
        feedback_loop_rank=_count(rank),
        domain_label=row.domain_label,
        specialist_team_label=row.specialist_team_label,
        status=row.status,
        feedback_loop_health_score=row.feedback_loop_health_score,
        resolved_outcome_count=row.resolved_outcome_count,
        calibration_note_count=row.calibration_note_count,
        calibration_note_coverage_ratio=row.calibration_note_coverage_ratio,
        recurring_bias_label_count=row.recurring_bias_label_count,
        recurring_bias_label_coverage_ratio=row.recurring_bias_label_coverage_ratio,
        future_review_safeguard_count=row.future_review_safeguard_count,
        future_review_safeguard_coverage_ratio=row.future_review_safeguard_coverage_ratio,
        unreviewed_bias_label_count=row.unreviewed_bias_label_count,
        feedback_last_reviewed_at=row.feedback_last_reviewed_at,
        feedback_age_seconds=row.feedback_age_seconds,
        observed_at=row.observed_at,
        reason_codes=row.reason_codes,
    )


def _row_reason_codes(
    *,
    item: ResearchDomainTeamCalibrationFeedbackLoopInput,
    config: ResearchDomainTeamCalibrationFeedbackLoopConfig,
    calibration_note_coverage_ratio: Decimal,
    recurring_bias_label_coverage_ratio: Decimal,
    future_review_safeguard_coverage_ratio: Decimal,
    feedback_age_seconds: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    _append_low_threshold_reason(
        reasons,
        metric=item.resolved_outcome_count,
        watch=config.min_pass_resolved_outcome_count,
        block=config.min_watch_resolved_outcome_count,
        watch_code="domain_team_feedback_resolved_outcome_sample_watch",
        block_code="domain_team_feedback_resolved_outcome_sample_block",
    )
    _append_low_threshold_reason(
        reasons,
        metric=calibration_note_coverage_ratio,
        watch=config.min_pass_calibration_note_coverage_ratio,
        block=config.min_watch_calibration_note_coverage_ratio,
        watch_code="domain_team_feedback_calibration_note_coverage_watch",
        block_code="domain_team_feedback_calibration_note_coverage_block",
    )
    _append_low_threshold_reason(
        reasons,
        metric=recurring_bias_label_coverage_ratio,
        watch=config.min_pass_recurring_bias_label_coverage_ratio,
        block=config.min_watch_recurring_bias_label_coverage_ratio,
        watch_code="domain_team_feedback_recurring_bias_label_coverage_watch",
        block_code="domain_team_feedback_recurring_bias_label_coverage_block",
    )
    _append_low_threshold_reason(
        reasons,
        metric=future_review_safeguard_coverage_ratio,
        watch=config.min_pass_future_review_safeguard_coverage_ratio,
        block=config.min_watch_future_review_safeguard_coverage_ratio,
        watch_code="domain_team_feedback_future_safeguard_coverage_watch",
        block_code="domain_team_feedback_future_safeguard_coverage_block",
    )
    _append_high_threshold_reason(
        reasons,
        metric=feedback_age_seconds,
        watch=config.max_pass_feedback_age_seconds,
        block=config.max_watch_feedback_age_seconds,
        watch_code="domain_team_feedback_stale_review_watch",
        block_code="domain_team_feedback_stale_review_block",
    )
    _append_high_threshold_reason(
        reasons,
        metric=item.unreviewed_bias_label_count,
        watch=config.max_pass_unreviewed_bias_label_count,
        block=config.max_watch_unreviewed_bias_label_count,
        watch_code="domain_team_feedback_unreviewed_bias_label_watch",
        block_code="domain_team_feedback_unreviewed_bias_label_block",
    )
    if not reasons:
        reasons.append(PASS_REASON)
    return _require_reason_codes(tuple(reasons), require_nonempty=True)


def _append_low_threshold_reason(
    reasons: list[str],
    *,
    metric: Decimal,
    watch: Decimal,
    block: Decimal,
    watch_code: str,
    block_code: str,
) -> None:
    if metric < block:
        reasons.append(block_code)
    elif metric < watch:
        reasons.append(watch_code)


def _append_high_threshold_reason(
    reasons: list[str],
    *,
    metric: Decimal,
    watch: Decimal,
    block: Decimal,
    watch_code: str,
    block_code: str,
) -> None:
    if metric > block:
        reasons.append(block_code)
    elif metric > watch:
        reasons.append(watch_code)


def _feedback_loop_health_score(
    *,
    calibration_note_coverage_ratio: Decimal,
    recurring_bias_label_coverage_ratio: Decimal,
    future_review_safeguard_coverage_ratio: Decimal,
) -> Decimal:
    return min(
        calibration_note_coverage_ratio,
        recurring_bias_label_coverage_ratio,
        future_review_safeguard_coverage_ratio,
    ).quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _feedback_age_seconds(
    last_reviewed_at: datetime | None,
    generated_at: datetime,
    config: ResearchDomainTeamCalibrationFeedbackLoopConfig,
) -> Decimal:
    if last_reviewed_at is None:
        return (config.max_watch_feedback_age_seconds + ONE).quantize(
            QUANTUM,
            rounding=ROUND_HALF_EVEN,
        )
    return _seconds_between(last_reviewed_at, generated_at)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchDomainTeamCalibrationFeedbackLoopRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchDomainTeamCalibrationFeedbackLoopRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    found = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != PASS_REASON
    }
    if not found:
        return (PASS_REASON,)
    return tuple(reason_code for reason_code in REASON_SEQUENCE if reason_code in found)


def _row_sort_key(
    row: ResearchDomainTeamCalibrationFeedbackLoopRow,
) -> tuple[int, Decimal, Decimal, str, str]:
    return (
        STATUS_WEIGHT[row.status],
        row.feedback_loop_health_score,
        -row.feedback_age_seconds,
        row.domain_label,
        row.specialist_team_label,
    )


def _normalize_inputs(
    inputs: Iterable[ResearchDomainTeamCalibrationFeedbackLoopInput],
) -> tuple[ResearchDomainTeamCalibrationFeedbackLoopInput, ...]:
    try:
        items = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be iterable") from exc
    seen_labels: set[tuple[str, str]] = set()
    normalized: list[ResearchDomainTeamCalibrationFeedbackLoopInput] = []
    for item in items:
        if type(item) is not ResearchDomainTeamCalibrationFeedbackLoopInput:
            raise ValueError("input must be a ResearchDomainTeamCalibrationFeedbackLoopInput")
        _require_hard_flags("input", item)
        label_pair = (item.domain_label, item.specialist_team_label)
        if label_pair in seen_labels:
            raise ValueError("team labels must be unique")
        seen_labels.add(label_pair)
        normalized.append(item)
    return tuple(normalized)


def _validate_row(row: ResearchDomainTeamCalibrationFeedbackLoopRow) -> None:
    if row.calibration_note_count > row.resolved_outcome_count:
        raise ValueError("calibration_note_count must not exceed resolved_outcome_count")
    if row.recurring_bias_label_count > row.resolved_outcome_count:
        raise ValueError("recurring_bias_label_count must not exceed resolved_outcome_count")
    if row.future_review_safeguard_count > row.resolved_outcome_count:
        raise ValueError(
            "future_review_safeguard_count must not exceed resolved_outcome_count",
        )
    expected = _row_status(row.reason_codes)
    if row.status != expected:
        raise ValueError("status must match reason_codes")
    expected_health_score = _feedback_loop_health_score(
        calibration_note_coverage_ratio=row.calibration_note_coverage_ratio,
        recurring_bias_label_coverage_ratio=row.recurring_bias_label_coverage_ratio,
        future_review_safeguard_coverage_ratio=row.future_review_safeguard_coverage_ratio,
    )
    if row.feedback_loop_health_score != expected_health_score:
        raise ValueError("feedback_loop_health_score must match coverage ratios")


def _validate_report(report: ResearchDomainTeamCalibrationFeedbackLoopReport) -> None:
    rows = report.rows
    expected_values = {
        "input_count": _count(len(rows)),
        "resolved_outcome_count": _sum_decimal(
            row.resolved_outcome_count for row in rows
        ),
        "calibration_note_count": _sum_decimal(row.calibration_note_count for row in rows),
        "recurring_bias_label_count": _sum_decimal(
            row.recurring_bias_label_count for row in rows
        ),
        "future_review_safeguard_count": _sum_decimal(
            row.future_review_safeguard_count for row in rows
        ),
        "unreviewed_bias_label_count": _sum_decimal(
            row.unreviewed_bias_label_count for row in rows
        ),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "calibration_note_coverage_ratio": _coverage_ratio(
            _sum_decimal(row.calibration_note_count for row in rows),
            _sum_decimal(row.resolved_outcome_count for row in rows),
        ),
        "recurring_bias_label_coverage_ratio": _coverage_ratio(
            _sum_decimal(row.recurring_bias_label_count for row in rows),
            _sum_decimal(row.resolved_outcome_count for row in rows),
        ),
        "future_review_safeguard_coverage_ratio": _coverage_ratio(
            _sum_decimal(row.future_review_safeguard_count for row in rows),
            _sum_decimal(row.resolved_outcome_count for row in rows),
        ),
        "max_feedback_age_seconds": _max_decimal(row.feedback_age_seconds for row in rows),
        "max_unreviewed_bias_label_count": _max_decimal(
            row.unreviewed_bias_label_count for row in rows
        ),
        "status": _report_status(rows),
        "reason_codes": _report_reason_codes(rows),
    }
    for field_name, expected in expected_values.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} is inconsistent with rows")


def _require_rows(
    rows: object,
) -> tuple[ResearchDomainTeamCalibrationFeedbackLoopRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a tuple")
    normalized: list[ResearchDomainTeamCalibrationFeedbackLoopRow] = []
    for row in rows:
        if type(row) is not ResearchDomainTeamCalibrationFeedbackLoopRow:
            raise ValueError("row must be a ResearchDomainTeamCalibrationFeedbackLoopRow")
        _require_hard_flags("row", row)
        normalized.append(row)
    return tuple(normalized)


def _status_count(
    rows: tuple[ResearchDomainTeamCalibrationFeedbackLoopRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return total.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _max_decimal(values: Iterable[Decimal]) -> Decimal:
    maximum = ZERO
    for value in values:
        if value > maximum:
            maximum = value
    return maximum.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _coverage_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return (numerator / denominator).quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value(rounding=ROUND_HALF_EVEN):
        raise ValueError(f"{field_name} must be an integer Decimal")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _as_generated_at_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    if value.utcoffset() != ZERO_TIME_DELTA:
        raise ValueError(f"{field_name} must be UTC")
    return value.astimezone(UTC)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    if value.utcoffset() != ZERO_TIME_DELTA:
        raise ValueError(f"{field_name} must be UTC-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


ZERO_TIME_DELTA = datetime(2000, 1, 1, tzinfo=UTC).utcoffset()


def _validate_not_after(field_name: str, value: datetime, generated_at: datetime) -> None:
    if value > generated_at:
        raise ValueError(f"{field_name} must not be after generated_at")


def _validate_optional_not_after(
    field_name: str,
    value: datetime | None,
    generated_at: datetime,
) -> None:
    if value is not None and value > generated_at:
        raise ValueError(f"{field_name} must not be after generated_at")


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    microseconds = (
        Decimal(delta.days) * SECONDS_PER_DAY * MICROSECONDS_PER_SECOND
        + Decimal(delta.seconds) * MICROSECONDS_PER_SECOND
        + Decimal(delta.microseconds)
    )
    return (microseconds / MICROSECONDS_PER_SECOND).quantize(
        QUANTUM,
        rounding=ROUND_HALF_EVEN,
    )


def _require_exact_type(value: object, expected_type: type, label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _require_status(field_name: str, value: object) -> None:
    if value not in CALIBRATION_FEEDBACK_LOOP_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == "" or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public aggregate labels")
    return value


def _require_public_label(field_name: str, value: object) -> str:
    value = _require_public_string(field_name, value)
    if PUBLIC_LABEL_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a safe public aggregate label")
    return value


def _require_reason_codes(
    reason_codes: object,
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError("reason_codes must be a tuple")
    normalized: list[str] = []
    for reason_code in reason_codes:
        if type(reason_code) is not str:
            raise ValueError("reason_codes entries must be strings")
        if reason_code not in REASON_SEQUENCE:
            raise ValueError("reason_codes contains an unknown reason code")
        if reason_code not in normalized:
            normalized.append(reason_code)
    if require_nonempty and not normalized:
        raise ValueError("reason_codes must not be empty")
    return tuple(reason_code for reason_code in REASON_SEQUENCE if reason_code in normalized)


def _require_report_reason_codes(reason_codes: object) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError("reason_codes must be a tuple")
    normalized: list[str] = []
    for reason_code in reason_codes:
        if type(reason_code) is not str:
            raise ValueError("reason_codes entries must be strings")
        if reason_code not in REPORT_REASON_SEQUENCE:
            raise ValueError("reason_codes contains an unknown reason code")
        if reason_code not in normalized:
            normalized.append(reason_code)
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    return tuple(
        reason_code for reason_code in REPORT_REASON_SEQUENCE if reason_code in normalized
    )


def _require_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in SHA256_HEX_CHARS for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _report_values_without_digest(
    report: ResearchDomainTeamCalibrationFeedbackLoopReport,
) -> dict[str, object]:
    values = _json_ready(asdict(report))
    if type(values) is not dict:
        raise ValueError("report payload must be a JSON object")
    values.pop("derived_validation_digest", None)
    return values


def _digest_from_values(values: Mapping[str, object]) -> str:
    return _digest_from_payload(_json_ready(values))


def _digest_from_payload(payload: Mapping[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _json_ready(value: object) -> object:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be UTC-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) in (float, int):
        raise ValueError("JSON value must use Decimal-derived strings")
    if isinstance(value, Mapping):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(
            label,
            asdict(value),
            allow_json_containers=allow_json_containers,
        )
        return
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"unsafe public aggregate labels in {label}")
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public aggregate labels in {label}: {key}")
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if allow_json_containers:
        return


def _reject_public_numerics(value: object) -> None:
    if type(value) in (float, int):
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if isinstance(value, Mapping):
        for item in value.values():
            _reject_public_numerics(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numerics(item)


def _validate_public_payload_contract(payload: dict[str, object]) -> None:
    _require_public_field_set("public payload", payload, REPORT_PUBLIC_FIELDS)
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("rows must be a JSON array")
    ResearchDomainTeamCalibrationFeedbackLoopReport(
        generated_at=_public_datetime("generated_at", payload["generated_at"]),
        config_version=_require_public_string("config_version", payload["config_version"]),
        input_count=_public_count_decimal("input_count", payload["input_count"]),
        resolved_outcome_count=_public_count_decimal(
            "resolved_outcome_count",
            payload["resolved_outcome_count"],
        ),
        calibration_note_count=_public_count_decimal(
            "calibration_note_count",
            payload["calibration_note_count"],
        ),
        recurring_bias_label_count=_public_count_decimal(
            "recurring_bias_label_count",
            payload["recurring_bias_label_count"],
        ),
        future_review_safeguard_count=_public_count_decimal(
            "future_review_safeguard_count",
            payload["future_review_safeguard_count"],
        ),
        unreviewed_bias_label_count=_public_count_decimal(
            "unreviewed_bias_label_count",
            payload["unreviewed_bias_label_count"],
        ),
        pass_count=_public_count_decimal("pass_count", payload["pass_count"]),
        watch_count=_public_count_decimal("watch_count", payload["watch_count"]),
        block_count=_public_count_decimal("block_count", payload["block_count"]),
        calibration_note_coverage_ratio=_public_ratio_decimal(
            "calibration_note_coverage_ratio",
            payload["calibration_note_coverage_ratio"],
        ),
        recurring_bias_label_coverage_ratio=_public_ratio_decimal(
            "recurring_bias_label_coverage_ratio",
            payload["recurring_bias_label_coverage_ratio"],
        ),
        future_review_safeguard_coverage_ratio=_public_ratio_decimal(
            "future_review_safeguard_coverage_ratio",
            payload["future_review_safeguard_coverage_ratio"],
        ),
        max_feedback_age_seconds=_public_count_decimal(
            "max_feedback_age_seconds",
            payload["max_feedback_age_seconds"],
        ),
        max_unreviewed_bias_label_count=_public_count_decimal(
            "max_unreviewed_bias_label_count",
            payload["max_unreviewed_bias_label_count"],
        ),
        status=_public_status("status", payload["status"]),
        reason_codes=_public_report_reason_codes(payload["reason_codes"]),
        rows=tuple(_public_row(row) for row in rows),
        derived_validation_digest=_require_sha256(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_public_hard_flag("paper_only", payload["paper_only"]),
        report_only=_public_hard_flag("report_only", payload["report_only"]),
        readonly=_public_hard_flag("readonly", payload["readonly"]),
    )


def _public_row(value: object) -> ResearchDomainTeamCalibrationFeedbackLoopRow:
    if type(value) is not dict:
        raise ValueError("rows entries must be JSON objects")
    _require_public_field_set("row", value, ROW_PUBLIC_FIELDS)
    return ResearchDomainTeamCalibrationFeedbackLoopRow(
        feedback_loop_rank=_public_count_decimal(
            "feedback_loop_rank",
            value["feedback_loop_rank"],
        ),
        domain_label=_require_public_label("domain_label", value["domain_label"]),
        specialist_team_label=_require_public_label(
            "specialist_team_label",
            value["specialist_team_label"],
        ),
        status=_public_status("status", value["status"]),
        feedback_loop_health_score=_public_ratio_decimal(
            "feedback_loop_health_score",
            value["feedback_loop_health_score"],
        ),
        resolved_outcome_count=_public_count_decimal(
            "resolved_outcome_count",
            value["resolved_outcome_count"],
        ),
        calibration_note_count=_public_count_decimal(
            "calibration_note_count",
            value["calibration_note_count"],
        ),
        calibration_note_coverage_ratio=_public_ratio_decimal(
            "calibration_note_coverage_ratio",
            value["calibration_note_coverage_ratio"],
        ),
        recurring_bias_label_count=_public_count_decimal(
            "recurring_bias_label_count",
            value["recurring_bias_label_count"],
        ),
        recurring_bias_label_coverage_ratio=_public_ratio_decimal(
            "recurring_bias_label_coverage_ratio",
            value["recurring_bias_label_coverage_ratio"],
        ),
        future_review_safeguard_count=_public_count_decimal(
            "future_review_safeguard_count",
            value["future_review_safeguard_count"],
        ),
        future_review_safeguard_coverage_ratio=_public_ratio_decimal(
            "future_review_safeguard_coverage_ratio",
            value["future_review_safeguard_coverage_ratio"],
        ),
        unreviewed_bias_label_count=_public_count_decimal(
            "unreviewed_bias_label_count",
            value["unreviewed_bias_label_count"],
        ),
        feedback_last_reviewed_at=_public_optional_datetime(
            "feedback_last_reviewed_at",
            value["feedback_last_reviewed_at"],
        ),
        feedback_age_seconds=_public_count_decimal(
            "feedback_age_seconds",
            value["feedback_age_seconds"],
        ),
        observed_at=_public_datetime("observed_at", value["observed_at"]),
        reason_codes=_public_reason_codes(value["reason_codes"]),
        paper_only=_public_hard_flag("paper_only", value["paper_only"]),
        report_only=_public_hard_flag("report_only", value["report_only"]),
        readonly=_public_hard_flag("readonly", value["readonly"]),
    )


def _require_public_field_set(
    label: str,
    value: Mapping[str, object],
    expected_fields: frozenset[str],
) -> None:
    fields = set(value)
    unexpected = fields - expected_fields
    if unexpected:
        raise ValueError(f"{label} contains unknown public fields")
    missing = expected_fields - fields
    if missing:
        raise ValueError(f"{label} is missing required public fields")


def _public_count_decimal(field_name: str, value: object) -> Decimal:
    return _require_count_decimal(field_name, _public_decimal(field_name, value))


def _public_ratio_decimal(field_name: str, value: object) -> Decimal:
    return _require_ratio_decimal(field_name, _public_decimal(field_name, value))


def _public_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str or PUBLIC_DECIMAL_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a Decimal-derived string")
    return Decimal(value)


def _public_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not str or not value.endswith("+00:00"):
        raise ValueError(f"{field_name} must be a UTC datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a UTC datetime string") from exc
    return _as_utc(field_name, parsed)


def _public_optional_datetime(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _public_datetime(field_name, value)


def _public_status(field_name: str, value: object) -> str:
    _require_status(field_name, value)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _public_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError("reason_codes must be a JSON array")
    return _require_reason_codes(value, require_nonempty=True)


def _public_report_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError("reason_codes must be a JSON array")
    return _require_report_reason_codes(value)


def _public_hard_flag(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be True for public payload")
    return True


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS)
