"""Aggregate calibration backlog report for domain specialist teams."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_DOMAIN_SPECIALIST_CALIBRATION_BACKLOG_CONFIG_VERSION = (
    "research-domain-specialist-calibration-backlog-report-v1"
)
CALIBRATION_BACKLOG_STATUSES = ("pass", "watch", "block")

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
PUBLIC_LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")
HEX_CHARS = frozenset("0123456789abcdef")

REASON_SEQUENCE = (
    "domain_specialist_calibration_sample_scarcity_block",
    "domain_specialist_calibration_stale_feedback_block",
    "domain_specialist_calibration_error_taxonomy_coverage_block",
    "domain_specialist_calibration_queue_load_block",
    "domain_specialist_calibration_escalation_urgency_block",
    "domain_specialist_calibration_sample_scarcity_watch",
    "domain_specialist_calibration_stale_feedback_watch",
    "domain_specialist_calibration_error_taxonomy_coverage_watch",
    "domain_specialist_calibration_queue_load_watch",
    "domain_specialist_calibration_escalation_urgency_watch",
    "domain_specialist_calibration_backlog_clear",
)
REPORT_REASON_SEQUENCE = REASON_SEQUENCE[:-1]
EMPTY_REASON = "domain_specialist_calibration_backlog_empty"
ESCALATION_MODE_BY_STATUS = {
    "pass": "paper_calibration_monitor",
    "watch": "paper_calibration_backlog_watch",
    "block": "paper_calibration_backlog_block",
}


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_LABEL_FRAGMENTS = frozenset(
    (
        "http",
        "url",
        "raw",
        "market",
        "question",
        "candidate",
        "slug",
        "source",
        "text",
        "dsn",
        "table",
        "auth",
        "private",
        "token",
        "secret",
        "account",
        "credential",
        "api_key",
        "sizing",
        "recommendation",
        _join_parts("wal", "let"),
        _join_parts("ord", "er"),
        _join_parts("tra", "de"),
        _join_parts("li", "ve"),
        _join_parts("trad", "ing"),
        _join_parts("data", "base"),
        _join_parts("net", "work"),
        _join_parts("b", "uy"),
        _join_parts("s", "ell"),
    ),
)

__all__ = (
    "DEFAULT_RESEARCH_DOMAIN_SPECIALIST_CALIBRATION_BACKLOG_CONFIG_VERSION",
    "CALIBRATION_BACKLOG_STATUSES",
    "ResearchDomainSpecialistCalibrationBacklogConfig",
    "ResearchDomainSpecialistCalibrationBacklogInput",
    "ResearchDomainSpecialistCalibrationBacklogReasonCodeCount",
    "ResearchDomainSpecialistCalibrationBacklogReport",
    "ResearchDomainSpecialistCalibrationBacklogRow",
    "build_research_domain_specialist_calibration_backlog_report",
    "research_domain_specialist_calibration_backlog_report_digest",
    "research_domain_specialist_calibration_backlog_report_payload",
)


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class ResearchDomainSpecialistCalibrationBacklogConfig(_FinalDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_DOMAIN_SPECIALIST_CALIBRATION_BACKLOG_CONFIG_VERSION
    )
    min_pass_calibration_sample_count: Decimal = Decimal("100.000000")
    min_watch_calibration_sample_count: Decimal = Decimal("50.000000")
    max_pass_feedback_age_seconds: Decimal = Decimal("86400.000000")
    max_watch_feedback_age_seconds: Decimal = Decimal("604800.000000")
    min_pass_error_taxonomy_coverage_ratio: Decimal = Decimal("0.900000")
    min_watch_error_taxonomy_coverage_ratio: Decimal = Decimal("0.700000")
    max_pass_domain_queue_load_count: Decimal = Decimal("5.000000")
    max_watch_domain_queue_load_count: Decimal = Decimal("20.000000")
    escalation_watch_threshold: Decimal = Decimal("0.700000")
    escalation_block_threshold: Decimal = Decimal("0.900000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchDomainSpecialistCalibrationBacklogConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_DOMAIN_SPECIALIST_CALIBRATION_BACKLOG_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_pass_calibration_sample_count",
            "min_watch_calibration_sample_count",
            "max_pass_feedback_age_seconds",
            "max_watch_feedback_age_seconds",
            "max_pass_domain_queue_load_count",
            "max_watch_domain_queue_load_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_pass_error_taxonomy_coverage_ratio",
            "min_watch_error_taxonomy_coverage_ratio",
            "escalation_watch_threshold",
            "escalation_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if (
            self.min_pass_calibration_sample_count
            < self.min_watch_calibration_sample_count
        ):
            raise ValueError(
                "min_pass_calibration_sample_count must be at least "
                "min_watch_calibration_sample_count",
            )
        if self.max_pass_feedback_age_seconds > self.max_watch_feedback_age_seconds:
            raise ValueError(
                "max_watch_feedback_age_seconds must be at least "
                "max_pass_feedback_age_seconds",
            )
        if (
            self.min_pass_error_taxonomy_coverage_ratio
            < self.min_watch_error_taxonomy_coverage_ratio
        ):
            raise ValueError(
                "min_pass_error_taxonomy_coverage_ratio must be at least "
                "min_watch_error_taxonomy_coverage_ratio",
            )
        if self.max_pass_domain_queue_load_count > self.max_watch_domain_queue_load_count:
            raise ValueError(
                "max_watch_domain_queue_load_count must be at least "
                "max_pass_domain_queue_load_count",
            )
        if self.escalation_watch_threshold > self.escalation_block_threshold:
            raise ValueError(
                "escalation_block_threshold must be at least "
                "escalation_watch_threshold",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchDomainSpecialistCalibrationBacklogInput(_FinalDataclass):
    domain_label: str
    specialist_team_label: str
    calibration_sample_count: Decimal
    feedback_age_seconds: Decimal
    error_taxonomy_coverage_ratio: Decimal
    domain_queue_load_count: Decimal
    escalation_urgency_score: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchDomainSpecialistCalibrationBacklogInput,
            "input",
        )
        _require_public_label("domain_label", self.domain_label)
        _require_public_label("specialist_team_label", self.specialist_team_label)
        for field_name in (
            "calibration_sample_count",
            "feedback_age_seconds",
            "domain_queue_load_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "error_taxonomy_coverage_ratio",
            "escalation_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchDomainSpecialistCalibrationBacklogRow(_FinalDataclass):
    backlog_rank: Decimal
    domain_label: str
    specialist_team_label: str
    status: str
    backlog_pressure_score: Decimal
    calibration_sample_count: Decimal
    sample_scarcity_ratio: Decimal
    feedback_age_seconds: Decimal
    error_taxonomy_coverage_ratio: Decimal
    error_taxonomy_gap_ratio: Decimal
    domain_queue_load_count: Decimal
    domain_queue_load_ratio: Decimal
    escalation_urgency_score: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchDomainSpecialistCalibrationBacklogRow,
            "row",
        )
        object.__setattr__(self, "backlog_rank", _require_count_decimal("backlog_rank", self.backlog_rank))
        _require_public_label("domain_label", self.domain_label)
        _require_public_label("specialist_team_label", self.specialist_team_label)
        _require_status("status", self.status)
        for field_name in (
            "backlog_pressure_score",
            "sample_scarcity_ratio",
            "error_taxonomy_coverage_ratio",
            "error_taxonomy_gap_ratio",
            "domain_queue_load_ratio",
            "escalation_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "calibration_sample_count",
            "feedback_age_seconds",
            "domain_queue_load_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
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
class ResearchDomainSpecialistCalibrationBacklogReasonCodeCount(_FinalDataclass):
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchDomainSpecialistCalibrationBacklogReasonCodeCount,
            "reason_code_count",
        )
        _require_public_string("reason_code", self.reason_code)
        object.__setattr__(self, "count", _require_count_decimal("count", self.count))
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchDomainSpecialistCalibrationBacklogReport(_FinalDataclass):
    generated_at: datetime
    config_version: str
    input_count: Decimal
    backlog_item_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    backlog_ratio: Decimal
    max_backlog_pressure_score: Decimal
    min_calibration_sample_count: Decimal
    max_feedback_age_seconds: Decimal
    min_error_taxonomy_coverage_ratio: Decimal
    max_domain_queue_load_count: Decimal
    max_escalation_urgency_score: Decimal
    status: str
    escalation_mode: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchDomainSpecialistCalibrationBacklogReasonCodeCount, ...]
    rows: tuple[ResearchDomainSpecialistCalibrationBacklogRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchDomainSpecialistCalibrationBacklogReport,
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
            "backlog_item_count",
            "pass_count",
            "watch_count",
            "block_count",
            "min_calibration_sample_count",
            "max_feedback_age_seconds",
            "max_domain_queue_load_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "backlog_ratio",
            "max_backlog_pressure_score",
            "min_error_taxonomy_coverage_ratio",
            "max_escalation_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        _require_public_string("escalation_mode", self.escalation_mode)
        if self.escalation_mode != ESCALATION_MODE_BY_STATUS[self.status]:
            raise ValueError("escalation_mode must match status")
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
        object.__setattr__(self, "rows", _require_rows(self.rows))
        _require_sha256("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _validate_report(self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")


def build_research_domain_specialist_calibration_backlog_report(
    inputs: Iterable[ResearchDomainSpecialistCalibrationBacklogInput],
    *,
    config: ResearchDomainSpecialistCalibrationBacklogConfig,
    generated_at: datetime,
) -> ResearchDomainSpecialistCalibrationBacklogReport:
    _require_exact_type(
        config,
        ResearchDomainSpecialistCalibrationBacklogConfig,
        "config",
    )
    _require_hard_flags("config", config)
    generated_at_utc = _as_generated_at_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(inputs)
    base_rows = tuple(_row_from_input(item, config) for item in input_rows)
    rows = tuple(
        _with_rank(row, rank)
        for rank, row in enumerate(sorted(base_rows, key=_row_sort_key), start=1)
    )
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "input_count": _count(len(rows)),
        "backlog_item_count": _count(
            sum(1 for row in rows if row.status in ("watch", "block")),
        ),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "backlog_ratio": _ratio(
            _count(sum(1 for row in rows if row.status in ("watch", "block"))),
            _count(len(rows)),
        ),
        "max_backlog_pressure_score": _max_decimal(
            tuple(row.backlog_pressure_score for row in rows),
        ),
        "min_calibration_sample_count": _min_decimal(
            tuple(row.calibration_sample_count for row in rows),
        ),
        "max_feedback_age_seconds": _max_decimal(
            tuple(row.feedback_age_seconds for row in rows),
        ),
        "min_error_taxonomy_coverage_ratio": _min_ratio(
            tuple(row.error_taxonomy_coverage_ratio for row in rows),
        ),
        "max_domain_queue_load_count": _max_decimal(
            tuple(row.domain_queue_load_count for row in rows),
        ),
        "max_escalation_urgency_score": _max_decimal(
            tuple(row.escalation_urgency_score for row in rows),
        ),
        "status": _report_status(rows),
        "escalation_mode": ESCALATION_MODE_BY_STATUS[_report_status(rows)],
        "reason_codes": _report_reason_codes(rows),
        "reason_code_counts": _reason_code_counts(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchDomainSpecialistCalibrationBacklogReport(
        **values,
        derived_validation_digest=_digest_from_values(values),
    )


def research_domain_specialist_calibration_backlog_report_payload(
    report: ResearchDomainSpecialistCalibrationBacklogReport | Mapping[str, object],
) -> dict[str, object]:
    if type(report) is ResearchDomainSpecialistCalibrationBacklogReport:
        _require_hard_flags("report", report)
        payload = _json_ready(asdict(report))
    elif isinstance(report, Mapping):
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchDomainSpecialistCalibrationBacklogReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("report payload", _MappingFlags(payload))
    _reject_unsafe_public_payload("report payload", payload, allow_json_containers=True)
    expected_digest = _digest_from_payload(payload)
    if payload.get("derived_validation_digest") != expected_digest:
        raise ValueError("derived_validation_digest does not match report payload")
    return payload


def research_domain_specialist_calibration_backlog_report_digest(
    report: ResearchDomainSpecialistCalibrationBacklogReport | Mapping[str, object],
) -> str:
    payload = research_domain_specialist_calibration_backlog_report_payload(report)
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
    item: ResearchDomainSpecialistCalibrationBacklogInput,
    config: ResearchDomainSpecialistCalibrationBacklogConfig,
) -> ResearchDomainSpecialistCalibrationBacklogRow:
    sample_scarcity_ratio = _scarcity_ratio(
        item.calibration_sample_count,
        config.min_pass_calibration_sample_count,
    )
    error_taxonomy_gap_ratio = _clamp_ratio(ONE - item.error_taxonomy_coverage_ratio)
    domain_queue_load_ratio = _ratio_to_cap(
        item.domain_queue_load_count,
        config.max_watch_domain_queue_load_count,
    )
    reason_codes = _row_reason_codes(
        item=item,
        config=config,
    )
    return ResearchDomainSpecialistCalibrationBacklogRow(
        backlog_rank=ONE,
        domain_label=item.domain_label,
        specialist_team_label=item.specialist_team_label,
        status=_row_status(reason_codes),
        backlog_pressure_score=_backlog_pressure_score(
            sample_scarcity_ratio=sample_scarcity_ratio,
            feedback_age_seconds=item.feedback_age_seconds,
            error_taxonomy_gap_ratio=error_taxonomy_gap_ratio,
            domain_queue_load_count=item.domain_queue_load_count,
            escalation_urgency_score=item.escalation_urgency_score,
            config=config,
        ),
        calibration_sample_count=item.calibration_sample_count,
        sample_scarcity_ratio=sample_scarcity_ratio,
        feedback_age_seconds=item.feedback_age_seconds,
        error_taxonomy_coverage_ratio=item.error_taxonomy_coverage_ratio,
        error_taxonomy_gap_ratio=error_taxonomy_gap_ratio,
        domain_queue_load_count=item.domain_queue_load_count,
        domain_queue_load_ratio=domain_queue_load_ratio,
        escalation_urgency_score=item.escalation_urgency_score,
        observed_at=item.observed_at,
        reason_codes=reason_codes,
    )


def _with_rank(
    row: ResearchDomainSpecialistCalibrationBacklogRow,
    rank: int,
) -> ResearchDomainSpecialistCalibrationBacklogRow:
    return ResearchDomainSpecialistCalibrationBacklogRow(
        backlog_rank=_count(rank),
        domain_label=row.domain_label,
        specialist_team_label=row.specialist_team_label,
        status=row.status,
        backlog_pressure_score=row.backlog_pressure_score,
        calibration_sample_count=row.calibration_sample_count,
        sample_scarcity_ratio=row.sample_scarcity_ratio,
        feedback_age_seconds=row.feedback_age_seconds,
        error_taxonomy_coverage_ratio=row.error_taxonomy_coverage_ratio,
        error_taxonomy_gap_ratio=row.error_taxonomy_gap_ratio,
        domain_queue_load_count=row.domain_queue_load_count,
        domain_queue_load_ratio=row.domain_queue_load_ratio,
        escalation_urgency_score=row.escalation_urgency_score,
        observed_at=row.observed_at,
        reason_codes=row.reason_codes,
    )


def _row_reason_codes(
    *,
    item: ResearchDomainSpecialistCalibrationBacklogInput,
    config: ResearchDomainSpecialistCalibrationBacklogConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    _append_low_threshold_reason(
        reasons,
        metric=item.calibration_sample_count,
        watch=config.min_pass_calibration_sample_count,
        block=config.min_watch_calibration_sample_count,
        watch_code="domain_specialist_calibration_sample_scarcity_watch",
        block_code="domain_specialist_calibration_sample_scarcity_block",
    )
    _append_high_threshold_reason(
        reasons,
        metric=item.feedback_age_seconds,
        watch=config.max_pass_feedback_age_seconds,
        block=config.max_watch_feedback_age_seconds,
        watch_code="domain_specialist_calibration_stale_feedback_watch",
        block_code="domain_specialist_calibration_stale_feedback_block",
    )
    _append_low_threshold_reason(
        reasons,
        metric=item.error_taxonomy_coverage_ratio,
        watch=config.min_pass_error_taxonomy_coverage_ratio,
        block=config.min_watch_error_taxonomy_coverage_ratio,
        watch_code="domain_specialist_calibration_error_taxonomy_coverage_watch",
        block_code="domain_specialist_calibration_error_taxonomy_coverage_block",
    )
    _append_high_threshold_reason(
        reasons,
        metric=item.domain_queue_load_count,
        watch=config.max_pass_domain_queue_load_count,
        block=config.max_watch_domain_queue_load_count,
        watch_code="domain_specialist_calibration_queue_load_watch",
        block_code="domain_specialist_calibration_queue_load_block",
    )
    _append_high_threshold_reason(
        reasons,
        metric=item.escalation_urgency_score,
        watch=config.escalation_watch_threshold,
        block=config.escalation_block_threshold,
        watch_code="domain_specialist_calibration_escalation_urgency_watch",
        block_code="domain_specialist_calibration_escalation_urgency_block",
    )
    if not reasons:
        reasons.append("domain_specialist_calibration_backlog_clear")
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
        return
    if metric < watch:
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
    if metric >= block:
        reasons.append(block_code)
        return
    if metric >= watch:
        reasons.append(watch_code)


def _backlog_pressure_score(
    *,
    sample_scarcity_ratio: Decimal,
    feedback_age_seconds: Decimal,
    error_taxonomy_gap_ratio: Decimal,
    domain_queue_load_count: Decimal,
    escalation_urgency_score: Decimal,
    config: ResearchDomainSpecialistCalibrationBacklogConfig,
) -> Decimal:
    block_sample_scarcity = _scarcity_ratio(
        config.min_watch_calibration_sample_count,
        config.min_pass_calibration_sample_count,
    )
    block_error_gap = _clamp_ratio(ONE - config.min_watch_error_taxonomy_coverage_ratio)
    return _max_decimal(
        (
            _ratio_to_cap(sample_scarcity_ratio, block_sample_scarcity),
            _ratio_to_cap(feedback_age_seconds, config.max_watch_feedback_age_seconds),
            _ratio_to_cap(error_taxonomy_gap_ratio, block_error_gap),
            _ratio_to_cap(domain_queue_load_count, config.max_watch_domain_queue_load_count),
            _ratio_to_cap(escalation_urgency_score, config.escalation_block_threshold),
        ),
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return "block"
    if any(reason.endswith("_watch") for reason in reason_codes):
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchDomainSpecialistCalibrationBacklogRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchDomainSpecialistCalibrationBacklogRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    present = {reason for row in rows for reason in row.reason_codes}
    report_reasons = tuple(reason for reason in REPORT_REASON_SEQUENCE if reason in present)
    if report_reasons:
        return report_reasons
    return ("domain_specialist_calibration_backlog_clear",)


def _reason_code_counts(
    rows: tuple[ResearchDomainSpecialistCalibrationBacklogRow, ...],
) -> tuple[ResearchDomainSpecialistCalibrationBacklogReasonCodeCount, ...]:
    if not rows:
        return ()
    counter = Counter(reason for row in rows for reason in row.reason_codes)
    row_count = _count(len(rows))
    return tuple(
        ResearchDomainSpecialistCalibrationBacklogReasonCodeCount(
            reason_code=reason,
            count=_count(counter[reason]),
            row_ratio=_ratio(_count(counter[reason]), row_count),
        )
        for reason in REASON_SEQUENCE
        if counter[reason] > 0
    )


def _row_sort_key(row: ResearchDomainSpecialistCalibrationBacklogRow) -> tuple[object, ...]:
    return (
        -_status_rank(row.status),
        -row.backlog_pressure_score,
        -row.escalation_urgency_score,
        -row.feedback_age_seconds,
        -row.domain_queue_load_count,
        row.domain_label,
        row.specialist_team_label,
    )


def _status_rank(status: str) -> int:
    if status == "block":
        return 2
    if status == "watch":
        return 1
    return 0


def _status_count(
    rows: tuple[ResearchDomainSpecialistCalibrationBacklogRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _normalize_inputs(
    inputs: Iterable[ResearchDomainSpecialistCalibrationBacklogInput],
) -> tuple[ResearchDomainSpecialistCalibrationBacklogInput, ...]:
    rows = tuple(inputs)
    seen_team_labels: set[str] = set()
    for item in rows:
        _require_exact_type(
            item,
            ResearchDomainSpecialistCalibrationBacklogInput,
            "input",
        )
        _require_hard_flags("input", item)
        if item.specialist_team_label in seen_team_labels:
            raise ValueError("team labels must be unique")
        seen_team_labels.add(item.specialist_team_label)
    return rows


def _validate_row(row: ResearchDomainSpecialistCalibrationBacklogRow) -> None:
    if row.error_taxonomy_gap_ratio != _clamp_ratio(ONE - row.error_taxonomy_coverage_ratio):
        raise ValueError("error_taxonomy_gap_ratio must equal uncovered taxonomy share")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report(report: ResearchDomainSpecialistCalibrationBacklogReport) -> None:
    row_count = _count(len(report.rows))
    if report.input_count != row_count:
        raise ValueError("input_count must equal row count")
    if report.pass_count + report.watch_count + report.block_count != report.input_count:
        raise ValueError("status counts must equal input_count")
    if report.backlog_item_count != report.watch_count + report.block_count:
        raise ValueError("backlog_item_count must equal watch_count plus block_count")
    if report.backlog_ratio != _ratio(report.backlog_item_count, report.input_count):
        raise ValueError("backlog_ratio must match backlog_item_count divided by input_count")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")


def _require_rows(
    rows: tuple[ResearchDomainSpecialistCalibrationBacklogRow, ...],
) -> tuple[ResearchDomainSpecialistCalibrationBacklogRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        _require_exact_type(row, ResearchDomainSpecialistCalibrationBacklogRow, "row")
        _require_hard_flags("row", row)
    return rows


def _require_reason_code_counts(
    counts: tuple[ResearchDomainSpecialistCalibrationBacklogReasonCodeCount, ...],
) -> tuple[ResearchDomainSpecialistCalibrationBacklogReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        _require_exact_type(
            count,
            ResearchDomainSpecialistCalibrationBacklogReasonCodeCount,
            "reason_code_count",
        )
        _require_hard_flags("reason_code_count", count)
    return counts


def _require_report_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    if reason_codes == (EMPTY_REASON,):
        return reason_codes
    return _require_reason_codes(reason_codes, require_nonempty=True)


def _require_reason_codes(
    reason_codes: tuple[str, ...],
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if require_nonempty and not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_public_string("reason_code", reason_code)
        if reason_code not in REASON_SEQUENCE:
            raise ValueError("reason_code is not supported")
    return tuple(reason for reason in REASON_SEQUENCE if reason in set(reason_codes))


def _require_status(field_name: str, value: str) -> None:
    if value not in CALIBRATION_BACKLOG_STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")


def _require_public_string(field_name: str, value: str) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")


def _require_public_label(field_name: str, value: str) -> None:
    _require_public_string(field_name, value)
    if PUBLIC_LABEL_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a public aggregate label")
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_LABEL_FRAGMENTS):
        raise ValueError(f"{field_name} must be a public aggregate label")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be true")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be true")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be true")


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(value)


def _require_count_decimal(field_name: str, value: Decimal) -> Decimal:
    return _require_nonnegative_decimal(field_name, value)


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(value)


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    return value.astimezone(UTC)


def _as_generated_at_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    if value.tzinfo is not UTC:
        raise ValueError(f"{field_name} must be UTC")
    return value


def _require_sha256(field_name: str, value: str) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(character not in HEX_CHARS for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _scarcity_ratio(sample_count: Decimal, pass_count: Decimal) -> Decimal:
    if pass_count <= ZERO:
        raise ValueError("pass sample threshold must be positive")
    return _clamp_ratio((pass_count - sample_count) / pass_count)


def _ratio_to_cap(value: Decimal, cap: Decimal) -> Decimal:
    if cap <= ZERO:
        return ONE if value > ZERO else ZERO
    return _clamp_ratio(value / cap)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _clamp_ratio(numerator / denominator)


def _clamp_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        if value <= ZERO:
            return ZERO
        if value >= ONE:
            return ONE
        return _quantize(value)


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(max(values))


def _min_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(min(values))


def _min_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _require_ratio_decimal("min_ratio", min(values))


def _json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [_json_ready(item) for item in value]
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"unsupported payload value: {type(value).__name__}")


def _report_values_without_digest(
    report: ResearchDomainSpecialistCalibrationBacklogReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest")
    return values


def _digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return _digest_from_payload(payload)


def _digest_from_payload(payload: Mapping[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if type(value) is str:
        lowered = value.lower()
        if any(fragment in lowered for fragment in UNSAFE_LABEL_FRAGMENTS):
            raise ValueError(f"{label} must use public aggregate labels")
        return
    if allow_json_containers and isinstance(value, Mapping):
        for key, item in value.items():
            _reject_unsafe_public_payload(str(key), str(key))
            _reject_unsafe_public_payload(str(key), item, allow_json_containers=True)
        return
    if allow_json_containers and isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(label, item, allow_json_containers=True)
        return
    if hasattr(value, "__dataclass_fields__"):
        _reject_unsafe_public_payload(label, asdict(value), allow_json_containers=True)
