"""Report-only domain expertise learning curve reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
import re
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_TEAM_DOMAIN_EXPERTISE_LEARNING_CURVE_CONFIG_VERSION",
    "ResearchTeamDomainExpertiseLearningCurveConfig",
    "ResearchTeamDomainExpertiseLearningCurveInput",
    "ResearchTeamDomainExpertiseLearningCurveReasonCodeCount",
    "ResearchTeamDomainExpertiseLearningCurveReport",
    "ResearchTeamDomainExpertiseLearningCurveRow",
    "build_research_team_domain_expertise_learning_curve_report",
    "research_team_domain_expertise_learning_curve_report_payload",
)


DEFAULT_RESEARCH_TEAM_DOMAIN_EXPERTISE_LEARNING_CURVE_CONFIG_VERSION = (
    "research-team-domain-expertise-learning-curve-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
PUBLIC_STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)

NO_INPUTS_REASON = "domain_expertise_learning_curve_no_inputs"
PASS_REASON = "domain_expertise_learning_curve_pass"
WATCH_REASON = "domain_expertise_learning_curve_watch"
BLOCK_REASON = "domain_expertise_learning_curve_block"
FORECAST_OUTCOMES_PASS_REASON = (
    "domain_expertise_learning_curve_forecast_outcomes_pass"
)
FORECAST_OUTCOMES_WATCH_REASON = (
    "domain_expertise_learning_curve_forecast_outcomes_watch"
)
FORECAST_OUTCOMES_BLOCK_REASON = (
    "domain_expertise_learning_curve_forecast_outcomes_block"
)
EVIDENCE_QUALITY_PASS_REASON = (
    "domain_expertise_learning_curve_evidence_quality_pass"
)
EVIDENCE_QUALITY_WATCH_REASON = (
    "domain_expertise_learning_curve_evidence_quality_watch"
)
EVIDENCE_QUALITY_BLOCK_REASON = (
    "domain_expertise_learning_curve_evidence_quality_block"
)
CORRECTION_LATENCY_PASS_REASON = (
    "domain_expertise_learning_curve_correction_latency_pass"
)
CORRECTION_LATENCY_WATCH_REASON = (
    "domain_expertise_learning_curve_correction_latency_watch"
)
CORRECTION_LATENCY_BLOCK_REASON = (
    "domain_expertise_learning_curve_correction_latency_block"
)
CALIBRATION_MOVEMENT_PASS_REASON = (
    "domain_expertise_learning_curve_calibration_movement_pass"
)
CALIBRATION_MOVEMENT_WATCH_REASON = (
    "domain_expertise_learning_curve_calibration_movement_watch"
)
CALIBRATION_REGRESSION_BLOCK_REASON = (
    "domain_expertise_learning_curve_calibration_regression_block"
)
PLAYBOOK_ADOPTION_PASS_REASON = (
    "domain_expertise_learning_curve_playbook_adoption_pass"
)
PLAYBOOK_ADOPTION_WATCH_REASON = (
    "domain_expertise_learning_curve_playbook_adoption_watch"
)
PLAYBOOK_ADOPTION_BLOCK_REASON = (
    "domain_expertise_learning_curve_playbook_adoption_block"
)

REASON_CODE_SEQUENCE = (
    CALIBRATION_MOVEMENT_PASS_REASON,
    CALIBRATION_MOVEMENT_WATCH_REASON,
    CALIBRATION_REGRESSION_BLOCK_REASON,
    CORRECTION_LATENCY_PASS_REASON,
    CORRECTION_LATENCY_WATCH_REASON,
    CORRECTION_LATENCY_BLOCK_REASON,
    EVIDENCE_QUALITY_PASS_REASON,
    EVIDENCE_QUALITY_WATCH_REASON,
    EVIDENCE_QUALITY_BLOCK_REASON,
    FORECAST_OUTCOMES_PASS_REASON,
    FORECAST_OUTCOMES_WATCH_REASON,
    FORECAST_OUTCOMES_BLOCK_REASON,
    NO_INPUTS_REASON,
    PASS_REASON,
    WATCH_REASON,
    BLOCK_REASON,
    PLAYBOOK_ADOPTION_PASS_REASON,
    PLAYBOOK_ADOPTION_WATCH_REASON,
    PLAYBOOK_ADOPTION_BLOCK_REASON,
)
BLOCKING_REASON_CODES = frozenset(
    (
        CALIBRATION_REGRESSION_BLOCK_REASON,
        CORRECTION_LATENCY_BLOCK_REASON,
        EVIDENCE_QUALITY_BLOCK_REASON,
        FORECAST_OUTCOMES_BLOCK_REASON,
        PLAYBOOK_ADOPTION_BLOCK_REASON,
        NO_INPUTS_REASON,
        BLOCK_REASON,
    ),
)
WATCH_REASON_CODES = frozenset(
    (
        CALIBRATION_MOVEMENT_WATCH_REASON,
        CORRECTION_LATENCY_WATCH_REASON,
        EVIDENCE_QUALITY_WATCH_REASON,
        FORECAST_OUTCOMES_WATCH_REASON,
        PLAYBOOK_ADOPTION_WATCH_REASON,
        WATCH_REASON,
    ),
)

NEXT_STEPS = {
    STATUS_PASS: "publish_domain_expertise_learning_curve_report",
    STATUS_WATCH: "watch_domain_expertise_learning_curve_report",
    STATUS_BLOCK: "block_domain_expertise_learning_curve_report",
}

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_UP)

LINK_PATTERN = re.compile(r"\b[a-z][a-z0-9+.-]*://[^\s)>\]]+", re.IGNORECASE)
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
HEX_ID_PATTERN = re.compile(r"\b0x[a-fA-F0-9]{40}\b")


def _join(*parts: str) -> str:
    return "".join(parts)


PRIVATE_MARKERS = (
    _join("api", "_key"),
    "apikey",
    _join("au", "th"),
    "bearer",
    _join("bu", "y"),
    _join("can", "didate"),
    _join("data", "base"),
    _join("ds", "n"),
    _join("li", "ve"),
    _join("mar", "ket"),
    _join("or", "der"),
    "password",
    _join("ques", "tion"),
    _join("re", "commend"),
    _join("sec", "ret"),
    _join("sel", "l"),
    _join("sig", "ning"),
    _join("slu", "g"),
    _join("sour", "ce"),
    _join("ta", "ble"),
    _join("te", "xt"),
    _join("to", "ken"),
    _join("tra", "de"),
    _join("ur", "l"),
    _join("wal", "let"),
)


class _NoSubclass:
    def __init_subclass__(cls) -> None:
        if _NoSubclass not in cls.__bases__:
            raise TypeError(f"{cls.__name__} does not support subclassing")


@dataclass(frozen=True)
class ResearchTeamDomainExpertiseLearningCurveConfig(_NoSubclass):
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_DOMAIN_EXPERTISE_LEARNING_CURVE_CONFIG_VERSION
    )
    min_pass_forecast_outcome_count: Decimal = Decimal("8.000000")
    min_watch_forecast_outcome_count: Decimal = Decimal("3.000000")
    min_pass_outcome_usefulness_ratio: Decimal = Decimal("0.750000")
    min_watch_outcome_usefulness_ratio: Decimal = Decimal("0.400000")
    min_pass_evidence_quality_score: Decimal = Decimal("0.750000")
    min_watch_evidence_quality_score: Decimal = Decimal("0.500000")
    max_pass_correction_latency_seconds: Decimal = Decimal("86400.000000")
    max_watch_correction_latency_seconds: Decimal = Decimal("604800.000000")
    min_pass_calibration_improvement: Decimal = Decimal("0.050000")
    min_watch_calibration_improvement: Decimal = Decimal("0.005000")
    min_pass_playbook_adoption_rate: Decimal = Decimal("0.750000")
    min_watch_playbook_adoption_rate: Decimal = Decimal("0.400000")
    outcome_usefulness_weight: Decimal = Decimal("0.103707")
    evidence_quality_weight: Decimal = Decimal("0.050000")
    correction_latency_weight: Decimal = Decimal("0.043351")
    calibration_movement_weight: Decimal = Decimal("0.352942")
    playbook_adoption_weight: Decimal = Decimal("0.450000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamDomainExpertiseLearningCurveConfig,
            "config",
        )
        _require_hard_flags("config", self)
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_DOMAIN_EXPERTISE_LEARNING_CURVE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_pass_forecast_outcome_count",
            "min_watch_forecast_outcome_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "min_pass_outcome_usefulness_ratio",
            "min_watch_outcome_usefulness_ratio",
            "min_pass_evidence_quality_score",
            "min_watch_evidence_quality_score",
            "min_pass_calibration_improvement",
            "min_watch_calibration_improvement",
            "min_pass_playbook_adoption_rate",
            "min_watch_playbook_adoption_rate",
            "outcome_usefulness_weight",
            "evidence_quality_weight",
            "correction_latency_weight",
            "calibration_movement_weight",
            "playbook_adoption_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_correction_latency_seconds",
            "max_watch_correction_latency_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_watch_forecast_outcome_count > self.min_pass_forecast_outcome_count:
            raise ValueError("watch forecast threshold must not exceed pass threshold")
        if self.min_watch_outcome_usefulness_ratio > self.min_pass_outcome_usefulness_ratio:
            raise ValueError("watch usefulness threshold must not exceed pass threshold")
        if self.min_watch_evidence_quality_score > self.min_pass_evidence_quality_score:
            raise ValueError("watch evidence threshold must not exceed pass threshold")
        if self.max_watch_correction_latency_seconds < self.max_pass_correction_latency_seconds:
            raise ValueError("watch latency threshold must not be below pass threshold")
        if self.min_watch_calibration_improvement > self.min_pass_calibration_improvement:
            raise ValueError("watch calibration threshold must not exceed pass threshold")
        if self.min_watch_playbook_adoption_rate > self.min_pass_playbook_adoption_rate:
            raise ValueError("watch playbook threshold must not exceed pass threshold")
        if _sum_decimal(
            (
                self.outcome_usefulness_weight,
                self.evidence_quality_weight,
                self.correction_latency_weight,
                self.calibration_movement_weight,
                self.playbook_adoption_weight,
            ),
        ) != ONE:
            raise ValueError("expertise learning weights must sum to 1.000000")


@dataclass(frozen=True)
class ResearchTeamDomainExpertiseLearningCurveInput(_NoSubclass):
    team_key: str
    domain_key: str
    learning_label: str
    observed_at: datetime
    forecast_outcome_count: Decimal
    useful_outcome_count: Decimal
    evidence_quality_score: Decimal
    correction_latency_seconds: Decimal
    calibration_error_before: Decimal
    calibration_error_after: Decimal
    playbook_adoption_rate: Decimal
    private_learning_note: str
    trace_marker: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamDomainExpertiseLearningCurveInput,
            "input",
        )
        _require_hard_flags("input", self)
        for field_name in ("team_key", "domain_key", "learning_label"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("forecast_outcome_count", "useful_outcome_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        if self.useful_outcome_count > self.forecast_outcome_count:
            raise ValueError("useful_outcome_count must not exceed forecast_outcome_count")
        for field_name in (
            "evidence_quality_score",
            "calibration_error_before",
            "calibration_error_after",
            "playbook_adoption_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "correction_latency_seconds",
            _require_nonnegative_decimal(
                "correction_latency_seconds",
                self.correction_latency_seconds,
            ),
        )
        _require_private_note("private_learning_note", self.private_learning_note)
        _require_private_note("trace_marker", self.trace_marker, allow_empty=True)


@dataclass(frozen=True)
class ResearchTeamDomainExpertiseLearningCurveRow(_NoSubclass):
    team_key: str
    domain_key: str
    learning_key: str
    public_learning_label: str
    observed_at: datetime
    forecast_outcome_count: Decimal
    useful_outcome_count: Decimal
    outcome_usefulness_score: Decimal
    evidence_quality_score: Decimal
    correction_latency_seconds: Decimal
    correction_latency_score: Decimal
    calibration_error_before: Decimal
    calibration_error_after: Decimal
    calibration_error_delta: Decimal
    calibration_movement_score: Decimal
    playbook_adoption_rate: Decimal
    expertise_learning_score: Decimal
    expertise_status: str
    public_learning_digest: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamDomainExpertiseLearningCurveRow, "row")
        _require_hard_flags("row", self)
        for field_name in ("team_key", "domain_key", "public_learning_label"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_public_digest("learning_key", self.learning_key)
        _require_public_digest("public_learning_digest", self.public_learning_digest)
        _require_public_status("expertise_status", self.expertise_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("forecast_outcome_count", "useful_outcome_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "correction_latency_seconds",
            _require_nonnegative_decimal(
                "correction_latency_seconds",
                self.correction_latency_seconds,
            ),
        )
        for field_name in (
            "outcome_usefulness_score",
            "evidence_quality_score",
            "correction_latency_score",
            "calibration_error_before",
            "calibration_error_after",
            "calibration_movement_score",
            "playbook_adoption_rate",
            "expertise_learning_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "calibration_error_delta",
            _require_delta_decimal("calibration_error_delta", self.calibration_error_delta),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if self.expertise_status != _status_from_reason_codes(self.reason_codes):
            raise ValueError("expertise_status must match reason_codes")
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchTeamDomainExpertiseLearningCurveReasonCodeCount(_NoSubclass):
    reason_code: str
    count: Decimal
    domain_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamDomainExpertiseLearningCurveReasonCodeCount,
            "reason_code_count",
        )
        _require_hard_flags("reason_code_count", self)
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_whole_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "domain_ratio",
            _require_ratio_decimal("domain_ratio", self.domain_ratio),
        )


@dataclass(frozen=True)
class ResearchTeamDomainExpertiseLearningCurveReport(_NoSubclass):
    generated_at: datetime
    config_version: str
    report_status: str
    next_step: str
    domain_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    forecast_outcome_count: Decimal
    useful_outcome_count: Decimal
    outcome_usefulness_ratio: Decimal
    average_evidence_quality_score: Decimal
    average_correction_latency_score: Decimal
    average_calibration_movement_score: Decimal
    average_playbook_adoption_rate: Decimal
    average_expertise_learning_score: Decimal
    rows: tuple[ResearchTeamDomainExpertiseLearningCurveRow, ...]
    reason_code_counts: tuple[ResearchTeamDomainExpertiseLearningCurveReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    @property
    def payload(self) -> dict[str, Any]:
        return _validated_public_report_payload(self)

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamDomainExpertiseLearningCurveReport, "report")
        _require_hard_flags("report", self)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_public_status("report_status", self.report_status)
        if self.next_step != NEXT_STEPS[self.report_status]:
            raise ValueError("next_step must match report_status")
        for field_name in (
            "domain_count",
            "pass_count",
            "watch_count",
            "block_count",
            "forecast_outcome_count",
            "useful_outcome_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "outcome_usefulness_ratio",
            "average_evidence_quality_score",
            "average_correction_latency_score",
            "average_calibration_movement_score",
            "average_playbook_adoption_rate",
            "average_expertise_learning_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows("rows", self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts("reason_code_counts", self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_report_counts_and_reasons(self)
        expected_digest = _derived_validation_digest(self)
        if self.derived_validation_digest:
            _require_hex_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest does not match report payload")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        _validate_report_averages(self)


def build_research_team_domain_expertise_learning_curve_report(
    rows: Iterable[ResearchTeamDomainExpertiseLearningCurveInput],
    *,
    config: ResearchTeamDomainExpertiseLearningCurveConfig | None = None,
    generated_at: datetime,
) -> ResearchTeamDomainExpertiseLearningCurveReport:
    cfg = config or ResearchTeamDomainExpertiseLearningCurveConfig()
    if type(cfg) is not ResearchTeamDomainExpertiseLearningCurveConfig:
        raise TypeError(
            "config must be exactly ResearchTeamDomainExpertiseLearningCurveConfig",
        )
    _require_hard_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_inputs("rows", rows)
    for row in input_rows:
        if row.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")

    report_rows = tuple(
        sorted(
            (_row_from_input(row, config=cfg) for row in input_rows),
            key=_row_sort_key,
        ),
    )
    _require_unique_learning_keys(report_rows)
    reason_counts = _reason_code_counts(report_rows)
    reason_codes = tuple(item.reason_code for item in reason_counts)
    report_status = _report_status(report_rows)
    return ResearchTeamDomainExpertiseLearningCurveReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        report_status=report_status,
        next_step=NEXT_STEPS[report_status],
        domain_count=_count_decimal(len(report_rows)),
        pass_count=_count_decimal(_status_count(report_rows, STATUS_PASS)),
        watch_count=_count_decimal(_status_count(report_rows, STATUS_WATCH)),
        block_count=_count_decimal(_status_count(report_rows, STATUS_BLOCK)),
        forecast_outcome_count=_sum_decimal(
            tuple(row.forecast_outcome_count for row in report_rows),
        ),
        useful_outcome_count=_sum_decimal(
            tuple(row.useful_outcome_count for row in report_rows),
        ),
        outcome_usefulness_ratio=_ratio(
            _sum_decimal(tuple(row.useful_outcome_count for row in report_rows)),
            _sum_decimal(tuple(row.forecast_outcome_count for row in report_rows)),
        ),
        average_evidence_quality_score=_average(
            tuple(row.evidence_quality_score for row in report_rows),
        ),
        average_correction_latency_score=_average(
            tuple(row.correction_latency_score for row in report_rows),
        ),
        average_calibration_movement_score=_average(
            tuple(row.calibration_movement_score for row in report_rows),
        ),
        average_playbook_adoption_rate=_average(
            tuple(row.playbook_adoption_rate for row in report_rows),
        ),
        average_expertise_learning_score=_average(
            tuple(row.expertise_learning_score for row in report_rows),
        ),
        rows=report_rows,
        reason_code_counts=reason_counts,
        reason_codes=reason_codes,
    )


def research_team_domain_expertise_learning_curve_report_payload(
    report: ResearchTeamDomainExpertiseLearningCurveReport,
) -> dict[str, Any]:
    return _validated_public_report_payload(report)


def _validated_public_report_payload(
    report: ResearchTeamDomainExpertiseLearningCurveReport,
) -> dict[str, Any]:
    if type(report) is not ResearchTeamDomainExpertiseLearningCurveReport:
        raise TypeError(
            "report must be exactly ResearchTeamDomainExpertiseLearningCurveReport",
        )
    _require_hard_flags("report", report)
    _validate_report_counts_and_reasons(report)
    _validate_report_averages(report)
    _require_hex_digest("derived_validation_digest", report.derived_validation_digest)
    expected_digest = _derived_validation_digest(report)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest does not match report payload")
    payload = _report_payload(report, include_digest=True)
    _validate_public_payload_schema(payload)
    return payload


def _row_from_input(
    row: ResearchTeamDomainExpertiseLearningCurveInput,
    *,
    config: ResearchTeamDomainExpertiseLearningCurveConfig,
) -> ResearchTeamDomainExpertiseLearningCurveRow:
    outcome_usefulness_score = _ratio(row.useful_outcome_count, row.forecast_outcome_count)
    correction_latency_score = _correction_latency_score(row, config=config)
    calibration_error_delta = _quantize(row.calibration_error_before - row.calibration_error_after)
    calibration_movement_score = _calibration_movement_score(
        calibration_error_delta,
        config=config,
    )
    reason_codes = _row_reason_codes(
        row,
        outcome_usefulness_score=outcome_usefulness_score,
        calibration_error_delta=calibration_error_delta,
        config=config,
    )
    expertise_status = _status_from_reason_codes(reason_codes)
    expertise_learning_score = _expertise_learning_score(
        outcome_usefulness_score=outcome_usefulness_score,
        evidence_quality_score=row.evidence_quality_score,
        correction_latency_score=correction_latency_score,
        calibration_movement_score=calibration_movement_score,
        playbook_adoption_rate=row.playbook_adoption_rate,
        config=config,
    )
    return ResearchTeamDomainExpertiseLearningCurveRow(
        team_key=row.team_key,
        domain_key=row.domain_key,
        learning_key=_learning_key(row),
        public_learning_label=row.learning_label,
        observed_at=row.observed_at,
        forecast_outcome_count=row.forecast_outcome_count,
        useful_outcome_count=row.useful_outcome_count,
        outcome_usefulness_score=outcome_usefulness_score,
        evidence_quality_score=row.evidence_quality_score,
        correction_latency_seconds=row.correction_latency_seconds,
        correction_latency_score=correction_latency_score,
        calibration_error_before=row.calibration_error_before,
        calibration_error_after=row.calibration_error_after,
        calibration_error_delta=calibration_error_delta,
        calibration_movement_score=calibration_movement_score,
        playbook_adoption_rate=row.playbook_adoption_rate,
        expertise_learning_score=expertise_learning_score,
        expertise_status=expertise_status,
        public_learning_digest=_public_digest(row.private_learning_note, row.trace_marker),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    row: ResearchTeamDomainExpertiseLearningCurveInput,
    *,
    outcome_usefulness_score: Decimal,
    calibration_error_delta: Decimal,
    config: ResearchTeamDomainExpertiseLearningCurveConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if (
        row.forecast_outcome_count >= config.min_pass_forecast_outcome_count
        and outcome_usefulness_score >= config.min_pass_outcome_usefulness_ratio
    ):
        reason_codes.append(FORECAST_OUTCOMES_PASS_REASON)
    elif (
        row.forecast_outcome_count >= config.min_watch_forecast_outcome_count
        and outcome_usefulness_score >= config.min_watch_outcome_usefulness_ratio
    ):
        reason_codes.append(FORECAST_OUTCOMES_WATCH_REASON)
    else:
        reason_codes.append(FORECAST_OUTCOMES_BLOCK_REASON)

    if row.evidence_quality_score >= config.min_pass_evidence_quality_score:
        reason_codes.append(EVIDENCE_QUALITY_PASS_REASON)
    elif row.evidence_quality_score >= config.min_watch_evidence_quality_score:
        reason_codes.append(EVIDENCE_QUALITY_WATCH_REASON)
    else:
        reason_codes.append(EVIDENCE_QUALITY_BLOCK_REASON)

    if row.correction_latency_seconds <= config.max_pass_correction_latency_seconds:
        reason_codes.append(CORRECTION_LATENCY_PASS_REASON)
    elif row.correction_latency_seconds <= config.max_watch_correction_latency_seconds:
        reason_codes.append(CORRECTION_LATENCY_WATCH_REASON)
    else:
        reason_codes.append(CORRECTION_LATENCY_BLOCK_REASON)

    if calibration_error_delta < ZERO:
        reason_codes.append(CALIBRATION_REGRESSION_BLOCK_REASON)
    elif calibration_error_delta >= config.min_pass_calibration_improvement:
        reason_codes.append(CALIBRATION_MOVEMENT_PASS_REASON)
    elif calibration_error_delta >= config.min_watch_calibration_improvement:
        reason_codes.append(CALIBRATION_MOVEMENT_WATCH_REASON)
    else:
        reason_codes.append(CALIBRATION_MOVEMENT_WATCH_REASON)

    if row.playbook_adoption_rate >= config.min_pass_playbook_adoption_rate:
        reason_codes.append(PLAYBOOK_ADOPTION_PASS_REASON)
    elif row.playbook_adoption_rate >= config.min_watch_playbook_adoption_rate:
        reason_codes.append(PLAYBOOK_ADOPTION_WATCH_REASON)
    else:
        reason_codes.append(PLAYBOOK_ADOPTION_BLOCK_REASON)

    status = _status_from_reason_codes(tuple(reason_codes))
    if status == STATUS_BLOCK:
        reason_codes.append(BLOCK_REASON)
    elif status == STATUS_WATCH:
        reason_codes.append(WATCH_REASON)
    else:
        reason_codes.append(PASS_REASON)
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _correction_latency_score(
    row: ResearchTeamDomainExpertiseLearningCurveInput,
    *,
    config: ResearchTeamDomainExpertiseLearningCurveConfig,
) -> Decimal:
    if config.max_watch_correction_latency_seconds == ZERO:
        return ZERO
    return _clamp_ratio(
        ONE - _ratio(
            row.correction_latency_seconds,
            config.max_watch_correction_latency_seconds,
        ),
    )


def _calibration_movement_score(
    calibration_error_delta: Decimal,
    *,
    config: ResearchTeamDomainExpertiseLearningCurveConfig,
) -> Decimal:
    if calibration_error_delta <= ZERO:
        return ZERO
    if config.min_pass_calibration_improvement == ZERO:
        return ONE
    return _clamp_ratio(calibration_error_delta / config.min_pass_calibration_improvement)


def _expertise_learning_score(
    *,
    outcome_usefulness_score: Decimal,
    evidence_quality_score: Decimal,
    correction_latency_score: Decimal,
    calibration_movement_score: Decimal,
    playbook_adoption_rate: Decimal,
    config: ResearchTeamDomainExpertiseLearningCurveConfig,
) -> Decimal:
    return _quantize(
        outcome_usefulness_score * config.outcome_usefulness_weight
        + evidence_quality_score * config.evidence_quality_weight
        + correction_latency_score * config.correction_latency_weight
        + calibration_movement_score * config.calibration_movement_weight
        + playbook_adoption_rate * config.playbook_adoption_weight,
    )


def _report_status(rows: tuple[ResearchTeamDomainExpertiseLearningCurveRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.expertise_status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.expertise_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCKING_REASON_CODES for reason_code in reason_codes):
        return STATUS_BLOCK
    if any(reason_code in WATCH_REASON_CODES for reason_code in reason_codes):
        return STATUS_WATCH
    return STATUS_PASS


def _reason_code_counts(
    rows: tuple[ResearchTeamDomainExpertiseLearningCurveRow, ...],
) -> tuple[ResearchTeamDomainExpertiseLearningCurveReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchTeamDomainExpertiseLearningCurveReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                domain_ratio=ZERO,
            ),
        )
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    domain_count = _count_decimal(len(rows))
    return tuple(
        ResearchTeamDomainExpertiseLearningCurveReasonCodeCount(
            reason_code=reason_code,
            count=counts[reason_code],
            domain_ratio=_ratio(counts[reason_code], domain_count),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _validate_row_consistency(row: ResearchTeamDomainExpertiseLearningCurveRow) -> None:
    if row.useful_outcome_count > row.forecast_outcome_count:
        raise ValueError("useful_outcome_count must not exceed forecast_outcome_count")
    if row.outcome_usefulness_score != _ratio(
        row.useful_outcome_count,
        row.forecast_outcome_count,
    ):
        raise ValueError("outcome_usefulness_score must match outcome counts")
    if row.calibration_error_delta != _quantize(
        row.calibration_error_before - row.calibration_error_after,
    ):
        raise ValueError("calibration_error_delta must match calibration errors")


def _validate_report_counts_and_reasons(
    report: ResearchTeamDomainExpertiseLearningCurveReport,
) -> None:
    rows = report.rows
    if report.domain_count != _count_decimal(len(rows)):
        raise ValueError("domain_count must match rows")
    if report.pass_count != _count_decimal(_status_count(rows, STATUS_PASS)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count_decimal(_status_count(rows, STATUS_WATCH)):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count_decimal(_status_count(rows, STATUS_BLOCK)):
        raise ValueError("block_count must match rows")
    if report.forecast_outcome_count != _sum_decimal(
        tuple(row.forecast_outcome_count for row in rows),
    ):
        raise ValueError("forecast_outcome_count must match rows")
    if report.useful_outcome_count != _sum_decimal(
        tuple(row.useful_outcome_count for row in rows),
    ):
        raise ValueError("useful_outcome_count must match rows")
    if report.outcome_usefulness_ratio != _ratio(
        report.useful_outcome_count,
        report.forecast_outcome_count,
    ):
        raise ValueError("outcome_usefulness_ratio must match outcome counts")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status must match rows")
    expected_reason_counts = _reason_code_counts(rows)
    if report.reason_code_counts != expected_reason_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")


def _validate_report_averages(report: ResearchTeamDomainExpertiseLearningCurveReport) -> None:
    rows = report.rows
    if report.average_evidence_quality_score != _average(
        tuple(row.evidence_quality_score for row in rows),
    ):
        raise ValueError("average_evidence_quality_score must match rows")
    if report.average_correction_latency_score != _average(
        tuple(row.correction_latency_score for row in rows),
    ):
        raise ValueError("average_correction_latency_score must match rows")
    if report.average_calibration_movement_score != _average(
        tuple(row.calibration_movement_score for row in rows),
    ):
        raise ValueError("average_calibration_movement_score must match rows")
    if report.average_playbook_adoption_rate != _average(
        tuple(row.playbook_adoption_rate for row in rows),
    ):
        raise ValueError("average_playbook_adoption_rate must match rows")
    if report.average_expertise_learning_score != _average(
        tuple(row.expertise_learning_score for row in rows),
    ):
        raise ValueError("average_expertise_learning_score must match rows")


def _normalize_inputs(
    field_name: str,
    rows: Iterable[ResearchTeamDomainExpertiseLearningCurveInput],
) -> tuple[ResearchTeamDomainExpertiseLearningCurveInput, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise TypeError(f"{field_name} must be an iterable")
    values = tuple(rows)
    for value in values:
        if type(value) is not ResearchTeamDomainExpertiseLearningCurveInput:
            raise TypeError(
                f"{field_name} must contain "
                "ResearchTeamDomainExpertiseLearningCurveInput values",
            )
        _require_hard_flags("input", value)
    return values


def _normalize_rows(
    field_name: str,
    rows: tuple[ResearchTeamDomainExpertiseLearningCurveRow, ...],
) -> tuple[ResearchTeamDomainExpertiseLearningCurveRow, ...]:
    if type(rows) is not tuple:
        raise TypeError(f"{field_name} must be exactly tuple")
    for row in rows:
        if type(row) is not ResearchTeamDomainExpertiseLearningCurveRow:
            raise TypeError(
                f"{field_name} must contain "
                "ResearchTeamDomainExpertiseLearningCurveRow values",
            )
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    _require_unique_learning_keys(sorted_rows)
    return sorted_rows


def _normalize_reason_code_counts(
    field_name: str,
    counts: tuple[ResearchTeamDomainExpertiseLearningCurveReasonCodeCount, ...],
) -> tuple[ResearchTeamDomainExpertiseLearningCurveReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise TypeError(f"{field_name} must be exactly tuple")
    for count in counts:
        if type(count) is not ResearchTeamDomainExpertiseLearningCurveReasonCodeCount:
            raise TypeError(
                f"{field_name} must contain "
                "ResearchTeamDomainExpertiseLearningCurveReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(sorted(counts, key=lambda item: _reason_rank(item.reason_code)))
    seen: set[str] = set()
    for count in sorted_counts:
        if count.reason_code in seen:
            raise ValueError("duplicate reason_code")
        seen.add(count.reason_code)
    return sorted_counts


def _normalize_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise TypeError(f"{field_name} must be exactly tuple")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
        if reason_code in normalized:
            raise ValueError("duplicate reason_code")
        normalized.append(reason_code)
    return tuple(sorted(normalized, key=_reason_rank))


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be exactly str")
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a known reason code")
    _require_safe_public_string(value)


def _row_sort_key(
    row: ResearchTeamDomainExpertiseLearningCurveRow,
) -> tuple[str, str, str, str]:
    return (row.team_key, row.domain_key, row.public_learning_label, row.learning_key)


def _require_unique_learning_keys(
    rows: tuple[ResearchTeamDomainExpertiseLearningCurveRow, ...],
) -> None:
    seen: set[str] = set()
    for row in rows:
        if row.learning_key in seen:
            raise ValueError("duplicate learning_key")
        seen.add(row.learning_key)


def _status_count(
    rows: tuple[ResearchTeamDomainExpertiseLearningCurveRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.expertise_status == status)


def _learning_key(row: ResearchTeamDomainExpertiseLearningCurveInput) -> str:
    return _public_digest(
        row.team_key,
        row.domain_key,
        row.learning_label,
        row.observed_at.isoformat(),
        _decimal_string(row.forecast_outcome_count),
        _decimal_string(row.useful_outcome_count),
        _decimal_string(row.evidence_quality_score),
        _decimal_string(row.correction_latency_seconds),
        _decimal_string(row.calibration_error_before),
        _decimal_string(row.calibration_error_after),
        _decimal_string(row.playbook_adoption_rate),
        row.private_learning_note,
        row.trace_marker,
    )


def _public_digest(*parts: str) -> str:
    return "sha256:" + sha256("\x1f".join(parts).encode("utf-8")).hexdigest()


def _derived_validation_digest(
    report: ResearchTeamDomainExpertiseLearningCurveReport,
) -> str:
    payload = _report_payload(report, include_digest=False)
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _report_payload(
    report: ResearchTeamDomainExpertiseLearningCurveReport,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    return {
        field.name: _payload_value(getattr(report, field.name))
        for field in fields(report)
        if include_digest or field.name != "derived_validation_digest"
    }


def _validate_public_payload_schema(payload: dict[str, Any]) -> None:
    _require_payload_keys(
        "public payload",
        payload,
        (
            "generated_at",
            "config_version",
            "report_status",
            "next_step",
            "domain_count",
            "pass_count",
            "watch_count",
            "block_count",
            "forecast_outcome_count",
            "useful_outcome_count",
            "outcome_usefulness_ratio",
            "average_evidence_quality_score",
            "average_correction_latency_score",
            "average_calibration_movement_score",
            "average_playbook_adoption_rate",
            "average_expertise_learning_score",
            "rows",
            "reason_code_counts",
            "reason_codes",
            "derived_validation_digest",
            "paper_only",
            "report_only",
            "readonly",
        ),
    )
    _require_public_datetime_string("generated_at", payload["generated_at"])
    _require_public_string("config_version", payload["config_version"])
    _require_public_status("report_status", payload["report_status"])
    if payload["next_step"] != NEXT_STEPS[payload["report_status"]]:
        raise ValueError("next_step must match report_status")
    for field_name in (
        "domain_count",
        "pass_count",
        "watch_count",
        "block_count",
        "forecast_outcome_count",
        "useful_outcome_count",
        "outcome_usefulness_ratio",
        "average_evidence_quality_score",
        "average_correction_latency_score",
        "average_calibration_movement_score",
        "average_playbook_adoption_rate",
        "average_expertise_learning_score",
    ):
        _require_public_decimal_string(field_name, payload[field_name])
    rows = _require_payload_list("rows", payload["rows"])
    for index, row in enumerate(rows):
        _validate_public_row_payload(f"rows[{index}]", row)
    reason_code_counts = _require_payload_list(
        "reason_code_counts",
        payload["reason_code_counts"],
    )
    for index, count in enumerate(reason_code_counts):
        _validate_public_reason_code_count_payload(
            f"reason_code_counts[{index}]",
            count,
        )
    _require_public_reason_code_list("reason_codes", payload["reason_codes"])
    _require_hex_digest("derived_validation_digest", payload["derived_validation_digest"])
    _require_payload_flags("public payload", payload)


def _validate_public_row_payload(label: str, value: object) -> None:
    row = _require_payload_dict(label, value)
    _require_payload_keys(
        label,
        row,
        (
            "team_key",
            "domain_key",
            "learning_key",
            "public_learning_label",
            "observed_at",
            "forecast_outcome_count",
            "useful_outcome_count",
            "outcome_usefulness_score",
            "evidence_quality_score",
            "correction_latency_seconds",
            "correction_latency_score",
            "calibration_error_before",
            "calibration_error_after",
            "calibration_error_delta",
            "calibration_movement_score",
            "playbook_adoption_rate",
            "expertise_learning_score",
            "expertise_status",
            "public_learning_digest",
            "reason_codes",
            "paper_only",
            "report_only",
            "readonly",
        ),
    )
    for field_name in ("team_key", "domain_key", "public_learning_label"):
        _require_public_string(f"{label}.{field_name}", row[field_name])
    _require_public_digest(f"{label}.learning_key", row["learning_key"])
    _require_public_digest(
        f"{label}.public_learning_digest",
        row["public_learning_digest"],
    )
    _require_public_datetime_string(f"{label}.observed_at", row["observed_at"])
    for field_name in (
        "forecast_outcome_count",
        "useful_outcome_count",
        "outcome_usefulness_score",
        "evidence_quality_score",
        "correction_latency_seconds",
        "correction_latency_score",
        "calibration_error_before",
        "calibration_error_after",
        "calibration_error_delta",
        "calibration_movement_score",
        "playbook_adoption_rate",
        "expertise_learning_score",
    ):
        _require_public_decimal_string(f"{label}.{field_name}", row[field_name])
    _require_public_status(f"{label}.expertise_status", row["expertise_status"])
    _require_public_reason_code_list(f"{label}.reason_codes", row["reason_codes"])
    _require_payload_flags(label, row)


def _validate_public_reason_code_count_payload(label: str, value: object) -> None:
    count = _require_payload_dict(label, value)
    _require_payload_keys(
        label,
        count,
        (
            "reason_code",
            "count",
            "domain_ratio",
            "paper_only",
            "report_only",
            "readonly",
        ),
    )
    _require_reason_code(f"{label}.reason_code", count["reason_code"])
    _require_public_decimal_string(f"{label}.count", count["count"])
    _require_public_decimal_string(f"{label}.domain_ratio", count["domain_ratio"])
    _require_payload_flags(label, count)


def _require_payload_dict(label: str, value: object) -> dict[str, Any]:
    if type(value) is not dict:
        raise ValueError(f"{label} must be a JSON object")
    return value


def _require_payload_list(label: str, value: object) -> list[Any]:
    if type(value) is not list:
        raise ValueError(f"{label} must be a JSON array")
    return value


def _require_payload_keys(
    label: str,
    payload: dict[str, Any],
    expected_keys: tuple[str, ...],
) -> None:
    if type(payload) is not dict:
        raise ValueError(f"{label} must be a JSON object")
    if tuple(payload) != expected_keys:
        raise ValueError(f"{label} schema mismatch")


def _require_payload_flags(label: str, payload: dict[str, Any]) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if payload.get(flag_name) is not True:
            raise ValueError(f"{label} must keep {flag_name}=True")


def _require_public_reason_code_list(label: str, value: object) -> None:
    values = _require_payload_list(label, value)
    for item in values:
        _require_reason_code(f"{label} item", item)
    if len(values) != len(set(values)):
        raise ValueError(f"{label} contains duplicate reason_code")


def _require_public_decimal_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    try:
        decimal_value = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a canonical Decimal string") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if _decimal_string(decimal_value) != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")


def _require_public_datetime_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a canonical datetime string") from exc
    if _as_utc(field_name, parsed).isoformat() != value:
        raise ValueError(f"{field_name} must be a canonical datetime string")


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        return _decimal_string(value)
    if type(value) is datetime:
        return value.isoformat()
    if type(value) is str:
        _require_safe_public_string(value)
        return value
    if type(value) is bool:
        return value
    if is_dataclass(value) and not isinstance(value, type):
        _require_payload_dataclass(value)
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    raise TypeError("payload contains unsupported value")


def _require_payload_dataclass(value: object) -> None:
    if type(value) not in (
        ResearchTeamDomainExpertiseLearningCurveReasonCodeCount,
        ResearchTeamDomainExpertiseLearningCurveReport,
        ResearchTeamDomainExpertiseLearningCurveRow,
    ):
        raise ValueError("payload contains unsupported dataclass")
    if hasattr(value, "paper_only"):
        _require_hard_flags("payload", value)


def _reason_rank(reason_code: str) -> int:
    try:
        return REASON_CODE_SEQUENCE.index(reason_code)
    except ValueError as exc:
        raise ValueError("unknown reason_code") from exc


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    return _quantize(sum(values, ZERO))


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _clamp_ratio(value: Decimal) -> Decimal:
    return min(ONE, max(ZERO, _quantize(value)))


def _count_decimal(value: int) -> Decimal:
    if type(value) is not int:
        raise TypeError("count value must be exactly int")
    if value < 0:
        raise ValueError("count value must be nonnegative")
    return _quantize(Decimal(value))


def _decimal_string(value: Decimal) -> str:
    return f"{_quantize(value):.6f}"


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        try:
            return value.quantize(QUANTUM)
        except InvalidOperation as exc:
            raise ValueError("Decimal value must be finite") from exc


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise TypeError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be in the unit interval")
    return decimal_value


def _require_delta_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < -ONE or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between -1 and 1")
    return decimal_value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise TypeError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    if value.microsecond != 0:
        raise ValueError(f"{field_name} must be a whole second")
    return value.astimezone(UTC)


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be exactly str")
    if not value or value != value.strip() or any(char.isspace() for char in value):
        raise ValueError(f"{field_name} must be canonical")
    _require_safe_public_string(value)
    return value


def _require_private_note(
    field_name: str,
    value: object,
    *,
    allow_empty: bool = False,
) -> None:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be exactly str")
    if value != value.strip():
        raise ValueError(f"{field_name} must be canonical")
    if not allow_empty and not value:
        raise ValueError(f"{field_name} must be nonempty")


def _require_public_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be exactly str")
    prefix = "sha256:"
    if not value.startswith(prefix) or len(value) != len(prefix) + 64:
        raise ValueError(f"{field_name} must be a public digest")
    suffix = value[len(prefix) :]
    if any(char not in "0123456789abcdef" for char in suffix):
        raise ValueError(f"{field_name} must be a public digest")


def _require_hex_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be exactly str")
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a lowercase SHA-256 digest")


def _require_public_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in PUBLIC_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_hard_flags(label: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{label} must keep {flag_name}=True")


def _require_exact_type(value: object, type_: type[object], label: str) -> None:
    if type(value) is not type_:
        raise TypeError(f"{label} must be exactly {type_.__name__}")


def _require_safe_public_string(value: str) -> None:
    if _contains_private_marker(value):
        raise ValueError("unsafe public payload surface")


def _contains_private_marker(value: str) -> bool:
    lower = value.lower()
    if LINK_PATTERN.search(value) or EMAIL_PATTERN.search(value) or HEX_ID_PATTERN.search(value):
        return True
    return any(
        re.search(rf"(?<![a-z0-9]){re.escape(marker)}(?![a-z0-9])", lower)
        for marker in PRIVATE_MARKERS
    )
