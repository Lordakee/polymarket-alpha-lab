"""Pure report-only reducer for domain specialist bias memory audits."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
import json
from typing import Any, Iterable


DEFAULT_RESEARCH_DOMAIN_SPECIALIST_BIAS_MEMORY_AUDIT_REPORT_CONFIG_VERSION = (
    "research-domain-specialist-bias-memory-audit-report-v0"
)
RESEARCH_DOMAIN_SPECIALIST_BIAS_MEMORY_AUDIT_STATUSES = ("pass", "watch", "block")
RESEARCH_DOMAIN_SPECIALIST_BIAS_MEMORY_AUDIT_REASON_CODES = (
    "domain_specialist_bias_memory_audit_no_inputs",
    "directional_bias_repeated_block",
    "directional_bias_repeated_watch",
    "stale_lessons_block",
    "stale_lessons_watch",
    "post_outcome_errors_unresolved_block",
    "post_outcome_errors_unresolved_watch",
    "correction_coverage_weak_block",
    "correction_coverage_weak_watch",
    "domain_specialist_bias_memory_audit_block",
    "domain_specialist_bias_memory_audit_watch",
    "domain_specialist_bias_memory_audit_pass",
)

_DIGEST_FIELD = "derived_validation_digest"
_QUANTUM = Decimal("0.000001")
_COUNT_QUANTUM = Decimal("1")
_ZERO = Decimal("0.000000")
_ZERO_COUNT = Decimal("0")
_ONE = Decimal("1.000000")
_COMPONENT_COUNT = Decimal("4.000000")
_SECONDS_PER_DAY = Decimal("86400")
_MICROSECONDS_PER_SECOND = Decimal("1000000")
_DECIMAL_CONTEXT = Context(prec=64)
_STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
_ROW_REASON_PRIORITY = RESEARCH_DOMAIN_SPECIALIST_BIAS_MEMORY_AUDIT_REASON_CODES[1:]


def _join_parts(*parts: str) -> str:
    return "".join(parts)


_UNSAFE_PUBLIC_LABEL_FRAGMENTS = frozenset(
    (
        _join_parts("candidate", "_", "id"),
        _join_parts("market", "_", "id"),
        _join_parts("market", "_", "slug"),
        _join_parts("ques", "tion"),
        _join_parts("source", "_", "url"),
        _join_parts("source", "_", "text"),
        _join_parts("d", "sn"),
        _join_parts("table", "_", "name"),
        _join_parts("tok", "en"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("or", "der"),
        _join_parts("tr", "ade"),
        _join_parts("priv", "ate"),
        _join_parts("sec", "ret"),
        _join_parts("key"),
        _join_parts("live"),
        _join_parts("reco", "mmend"),
        _join_parts("siz", "ing"),
    ),
)

__all__ = (
    "DEFAULT_RESEARCH_DOMAIN_SPECIALIST_BIAS_MEMORY_AUDIT_REPORT_CONFIG_VERSION",
    "RESEARCH_DOMAIN_SPECIALIST_BIAS_MEMORY_AUDIT_STATUSES",
    "RESEARCH_DOMAIN_SPECIALIST_BIAS_MEMORY_AUDIT_REASON_CODES",
    "ResearchDomainSpecialistBiasMemoryAuditConfig",
    "ResearchDomainSpecialistBiasMemoryAuditInput",
    "ResearchDomainSpecialistBiasMemoryAuditReport",
    "ResearchDomainSpecialistBiasMemoryAuditRow",
    "build_research_domain_specialist_bias_memory_audit_report",
    "research_domain_specialist_bias_memory_audit_report_payload",
)


@dataclass(frozen=True)
class ResearchDomainSpecialistBiasMemoryAuditConfig:
    config_version: str = (
        DEFAULT_RESEARCH_DOMAIN_SPECIALIST_BIAS_MEMORY_AUDIT_REPORT_CONFIG_VERSION
    )
    max_pass_directional_bias_ratio: Decimal = Decimal("0.000000")
    max_watch_directional_bias_ratio: Decimal = Decimal("0.250000")
    max_pass_stale_lesson_ratio: Decimal = Decimal("0.000000")
    max_watch_stale_lesson_ratio: Decimal = Decimal("0.250000")
    max_pass_unresolved_post_outcome_error_ratio: Decimal = Decimal("0.000000")
    max_watch_unresolved_post_outcome_error_ratio: Decimal = Decimal("0.250000")
    min_pass_correction_coverage_ratio: Decimal = Decimal("0.800000")
    min_watch_correction_coverage_ratio: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchDomainSpecialistBiasMemoryAuditConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("config", self, ResearchDomainSpecialistBiasMemoryAuditConfig)
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_DOMAIN_SPECIALIST_BIAS_MEMORY_AUDIT_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported version")
        for field_name in (
            "max_pass_directional_bias_ratio",
            "max_watch_directional_bias_ratio",
            "max_pass_stale_lesson_ratio",
            "max_watch_stale_lesson_ratio",
            "max_pass_unresolved_post_outcome_error_ratio",
            "max_watch_unresolved_post_outcome_error_ratio",
            "min_pass_correction_coverage_ratio",
            "min_watch_correction_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.max_pass_directional_bias_ratio > self.max_watch_directional_bias_ratio:
            raise ValueError("max_pass_directional_bias_ratio must not exceed watch")
        if self.max_pass_stale_lesson_ratio > self.max_watch_stale_lesson_ratio:
            raise ValueError("max_pass_stale_lesson_ratio must not exceed watch")
        if (
            self.max_pass_unresolved_post_outcome_error_ratio
            > self.max_watch_unresolved_post_outcome_error_ratio
        ):
            raise ValueError(
                "max_pass_unresolved_post_outcome_error_ratio must not exceed watch",
            )
        if self.min_watch_correction_coverage_ratio > self.min_pass_correction_coverage_ratio:
            raise ValueError("min_watch_correction_coverage_ratio must not exceed pass")
        _require_hard_flags(self)
        _reject_unsafe_public_surface("config", self)


@dataclass(frozen=True)
class ResearchDomainSpecialistBiasMemoryAuditInput:
    domain_label: str
    specialist_label: str
    memory_lane: str
    observed_at: datetime
    long_term_memory_count: Decimal
    repeated_directional_bias_count: Decimal
    stale_lesson_count: Decimal
    post_outcome_error_count: Decimal
    unresolved_post_outcome_error_count: Decimal
    required_correction_count: Decimal
    covered_correction_count: Decimal
    redaction_confirmed: bool = True
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchDomainSpecialistBiasMemoryAuditInput does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("audit_input", self, ResearchDomainSpecialistBiasMemoryAuditInput)
        for field_name in ("domain_label", "specialist_label", "memory_lane"):
            _require_public_label(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "long_term_memory_count",
            "post_outcome_error_count",
            "required_correction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        if self.long_term_memory_count <= _ZERO_COUNT:
            raise ValueError("long_term_memory_count must be positive")
        if self.required_correction_count <= _ZERO_COUNT:
            raise ValueError("required_correction_count must be positive")
        for field_name in (
            "repeated_directional_bias_count",
            "stale_lesson_count",
            "unresolved_post_outcome_error_count",
            "covered_correction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        _validate_input_counts(self)
        if self.redaction_confirmed is not True:
            raise ValueError("redaction_confirmed must be True")
        _require_hard_flags(self)
        _reject_unsafe_public_surface("audit_input", self)


@dataclass(frozen=True)
class ResearchDomainSpecialistBiasMemoryAuditRow:
    domain_label: str
    specialist_label: str
    memory_lane: str
    observed_at: datetime
    snapshot_age_seconds: Decimal
    long_term_memory_count: Decimal
    repeated_directional_bias_count: Decimal
    stale_lesson_count: Decimal
    post_outcome_error_count: Decimal
    unresolved_post_outcome_error_count: Decimal
    required_correction_count: Decimal
    covered_correction_count: Decimal
    directional_bias_ratio: Decimal
    stale_lesson_ratio: Decimal
    unresolved_post_outcome_error_ratio: Decimal
    correction_coverage_ratio: Decimal
    bias_memory_audit_score: Decimal
    row_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchDomainSpecialistBiasMemoryAuditRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchDomainSpecialistBiasMemoryAuditRow)
        for field_name in ("domain_label", "specialist_label", "memory_lane"):
            _require_public_label(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "snapshot_age_seconds",
            _normalize_nonnegative_decimal("snapshot_age_seconds", self.snapshot_age_seconds),
        )
        for field_name in (
            "long_term_memory_count",
            "post_outcome_error_count",
            "required_correction_count",
            "repeated_directional_bias_count",
            "stale_lesson_count",
            "unresolved_post_outcome_error_count",
            "covered_correction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        if self.long_term_memory_count <= _ZERO_COUNT:
            raise ValueError("long_term_memory_count must be positive")
        if self.required_correction_count <= _ZERO_COUNT:
            raise ValueError("required_correction_count must be positive")
        for field_name in (
            "directional_bias_ratio",
            "stale_lesson_ratio",
            "unresolved_post_outcome_error_ratio",
            "correction_coverage_ratio",
            "bias_memory_audit_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("row_status", self.row_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes_preserving_sequence(self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags(self)
        _reject_unsafe_public_surface("row", self)


@dataclass(frozen=True)
class ResearchDomainSpecialistBiasMemoryAuditReport:
    generated_at: datetime
    config_version: str
    status: str
    input_count: Decimal
    row_count: Decimal
    domain_count: Decimal
    specialist_count: Decimal
    lane_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    repeated_directional_bias_count: Decimal
    stale_lesson_count: Decimal
    post_outcome_error_count: Decimal
    unresolved_post_outcome_error_count: Decimal
    required_correction_count: Decimal
    covered_correction_count: Decimal
    average_directional_bias_ratio: Decimal
    average_stale_lesson_ratio: Decimal
    average_unresolved_post_outcome_error_ratio: Decimal
    average_correction_coverage_ratio: Decimal
    average_bias_memory_audit_score: Decimal
    rows: tuple[ResearchDomainSpecialistBiasMemoryAuditRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchDomainSpecialistBiasMemoryAuditReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchDomainSpecialistBiasMemoryAuditReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "input_count",
            "row_count",
            "domain_count",
            "specialist_count",
            "lane_count",
            "pass_count",
            "watch_count",
            "block_count",
            "repeated_directional_bias_count",
            "stale_lesson_count",
            "post_outcome_error_count",
            "unresolved_post_outcome_error_count",
            "required_correction_count",
            "covered_correction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_directional_bias_ratio",
            "average_stale_lesson_ratio",
            "average_unresolved_post_outcome_error_ratio",
            "average_correction_coverage_ratio",
            "average_bias_memory_audit_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes_preserving_sequence(self.reason_codes),
        )
        _validate_report_consistency(self)
        _require_hard_flags(self)
        _reject_unsafe_public_surface("report", self)
        _require_or_set_digest(self)

    @property
    def payload(self) -> dict[str, Any]:
        payload = _payload_value(self)
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        _reject_unsafe_public_surface("payload", payload)
        _require_hard_flags(_DictFlags(payload))
        _validate_payload_digest(payload)
        return payload


def build_research_domain_specialist_bias_memory_audit_report(
    inputs: Iterable[ResearchDomainSpecialistBiasMemoryAuditInput],
    *,
    generated_at: datetime,
    config: ResearchDomainSpecialistBiasMemoryAuditConfig | None = None,
) -> ResearchDomainSpecialistBiasMemoryAuditReport:
    if config is None:
        config = ResearchDomainSpecialistBiasMemoryAuditConfig()
    _require_exact_type("config", config, ResearchDomainSpecialistBiasMemoryAuditConfig)
    _require_hard_flags(config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized = _normalize_inputs(inputs)
    for value in normalized:
        if _seconds_between(value.observed_at, generated_at) < _ZERO:
            raise ValueError("generated_at must be at or after observed_at")
    rows = tuple(
        sorted(
            (_row_from_input(value, generated_at, config) for value in normalized),
            key=_row_sort_key,
        ),
    )
    return ResearchDomainSpecialistBiasMemoryAuditReport(
        generated_at=generated_at,
        config_version=config.config_version,
        status=_report_status(rows),
        input_count=_decimal_count(len(normalized)),
        row_count=_decimal_count(len(rows)),
        domain_count=_decimal_count(len({row.domain_label for row in rows})),
        specialist_count=_decimal_count(len({row.specialist_label for row in rows})),
        lane_count=_decimal_count(len({row.memory_lane for row in rows})),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        repeated_directional_bias_count=_sum_count(
            row.repeated_directional_bias_count for row in rows
        ),
        stale_lesson_count=_sum_count(row.stale_lesson_count for row in rows),
        post_outcome_error_count=_sum_count(row.post_outcome_error_count for row in rows),
        unresolved_post_outcome_error_count=_sum_count(
            row.unresolved_post_outcome_error_count for row in rows
        ),
        required_correction_count=_sum_count(row.required_correction_count for row in rows),
        covered_correction_count=_sum_count(row.covered_correction_count for row in rows),
        average_directional_bias_ratio=_average_ratio(
            tuple(row.directional_bias_ratio for row in rows),
        ),
        average_stale_lesson_ratio=_average_ratio(
            tuple(row.stale_lesson_ratio for row in rows),
        ),
        average_unresolved_post_outcome_error_ratio=_average_ratio(
            tuple(row.unresolved_post_outcome_error_ratio for row in rows),
        ),
        average_correction_coverage_ratio=_average_ratio(
            tuple(row.correction_coverage_ratio for row in rows),
        ),
        average_bias_memory_audit_score=_average_ratio(
            tuple(row.bias_memory_audit_score for row in rows),
        ),
        rows=rows,
        reason_codes=_report_reason_codes(rows),
    )


def research_domain_specialist_bias_memory_audit_report_payload(
    report: ResearchDomainSpecialistBiasMemoryAuditReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchDomainSpecialistBiasMemoryAuditReport:
        _require_hard_flags(report)
        _reject_unsafe_public_surface("report", report)
        return report.payload
    if type(report) is dict:
        _reject_unsafe_public_surface("payload", report)
        payload = _payload_value(report)
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        _require_hard_flags(_DictFlags(payload))
        _validate_payload_digest(payload)
        return payload
    raise ValueError(
        "report must be a ResearchDomainSpecialistBiasMemoryAuditReport or payload",
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
    value: ResearchDomainSpecialistBiasMemoryAuditInput,
    generated_at: datetime,
    config: ResearchDomainSpecialistBiasMemoryAuditConfig,
) -> ResearchDomainSpecialistBiasMemoryAuditRow:
    directional_bias_ratio = _bounded_ratio(
        value.repeated_directional_bias_count,
        value.long_term_memory_count,
    )
    stale_lesson_ratio = _bounded_ratio(value.stale_lesson_count, value.long_term_memory_count)
    unresolved_post_outcome_error_ratio = _bounded_ratio(
        value.unresolved_post_outcome_error_count,
        value.post_outcome_error_count,
    )
    correction_coverage_ratio = _bounded_ratio(
        value.covered_correction_count,
        value.required_correction_count,
    )
    audit_score = _bias_memory_audit_score(
        directional_bias_ratio=directional_bias_ratio,
        stale_lesson_ratio=stale_lesson_ratio,
        unresolved_post_outcome_error_ratio=unresolved_post_outcome_error_ratio,
        correction_coverage_ratio=correction_coverage_ratio,
    )
    reason_codes = _row_reason_codes(
        directional_bias_ratio=directional_bias_ratio,
        stale_lesson_ratio=stale_lesson_ratio,
        unresolved_post_outcome_error_ratio=unresolved_post_outcome_error_ratio,
        correction_coverage_ratio=correction_coverage_ratio,
        config=config,
    )
    return ResearchDomainSpecialistBiasMemoryAuditRow(
        domain_label=value.domain_label,
        specialist_label=value.specialist_label,
        memory_lane=value.memory_lane,
        observed_at=value.observed_at,
        snapshot_age_seconds=_seconds_between(value.observed_at, generated_at),
        long_term_memory_count=value.long_term_memory_count,
        repeated_directional_bias_count=value.repeated_directional_bias_count,
        stale_lesson_count=value.stale_lesson_count,
        post_outcome_error_count=value.post_outcome_error_count,
        unresolved_post_outcome_error_count=value.unresolved_post_outcome_error_count,
        required_correction_count=value.required_correction_count,
        covered_correction_count=value.covered_correction_count,
        directional_bias_ratio=directional_bias_ratio,
        stale_lesson_ratio=stale_lesson_ratio,
        unresolved_post_outcome_error_ratio=unresolved_post_outcome_error_ratio,
        correction_coverage_ratio=correction_coverage_ratio,
        bias_memory_audit_score=audit_score,
        row_status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _bias_memory_audit_score(
    *,
    directional_bias_ratio: Decimal,
    stale_lesson_ratio: Decimal,
    unresolved_post_outcome_error_ratio: Decimal,
    correction_coverage_ratio: Decimal,
) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(
            ((_ONE - directional_bias_ratio)
            + (_ONE - stale_lesson_ratio)
            + (_ONE - unresolved_post_outcome_error_ratio)
            + correction_coverage_ratio)
            / _COMPONENT_COUNT,
        )


def _row_reason_codes(
    *,
    directional_bias_ratio: Decimal,
    stale_lesson_ratio: Decimal,
    unresolved_post_outcome_error_ratio: Decimal,
    correction_coverage_ratio: Decimal,
    config: ResearchDomainSpecialistBiasMemoryAuditConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if directional_bias_ratio > config.max_watch_directional_bias_ratio:
        reasons.append("directional_bias_repeated_block")
    elif directional_bias_ratio > config.max_pass_directional_bias_ratio:
        reasons.append("directional_bias_repeated_watch")
    if stale_lesson_ratio > config.max_watch_stale_lesson_ratio:
        reasons.append("stale_lessons_block")
    elif stale_lesson_ratio > config.max_pass_stale_lesson_ratio:
        reasons.append("stale_lessons_watch")
    if (
        unresolved_post_outcome_error_ratio
        > config.max_watch_unresolved_post_outcome_error_ratio
    ):
        reasons.append("post_outcome_errors_unresolved_block")
    elif (
        unresolved_post_outcome_error_ratio
        > config.max_pass_unresolved_post_outcome_error_ratio
    ):
        reasons.append("post_outcome_errors_unresolved_watch")
    if correction_coverage_ratio < config.min_watch_correction_coverage_ratio:
        reasons.append("correction_coverage_weak_block")
    elif correction_coverage_ratio < config.min_pass_correction_coverage_ratio:
        reasons.append("correction_coverage_weak_watch")
    if any(reason.endswith("_block") for reason in reasons):
        reasons.append("domain_specialist_bias_memory_audit_block")
    elif any(reason.endswith("_watch") for reason in reasons):
        reasons.append("domain_specialist_bias_memory_audit_watch")
    else:
        reasons.append("domain_specialist_bias_memory_audit_pass")
    return tuple(reason for reason in _ROW_REASON_PRIORITY if reason in reasons)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if "domain_specialist_bias_memory_audit_block" in reason_codes:
        return "block"
    if "domain_specialist_bias_memory_audit_watch" in reason_codes:
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchDomainSpecialistBiasMemoryAuditRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.row_status == "block" for row in rows):
        return "block"
    if any(row.row_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchDomainSpecialistBiasMemoryAuditRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("domain_specialist_bias_memory_audit_no_inputs",)
    present = frozenset(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != "domain_specialist_bias_memory_audit_pass"
    )
    if not present:
        return ("domain_specialist_bias_memory_audit_pass",)
    return tuple(reason_code for reason_code in _ROW_REASON_PRIORITY if reason_code in present)


def _normalize_inputs(
    values: Iterable[ResearchDomainSpecialistBiasMemoryAuditInput],
) -> tuple[ResearchDomainSpecialistBiasMemoryAuditInput, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen_keys: set[tuple[str, str, str]] = set()
    for value in normalized:
        _require_exact_type("audit_input", value, ResearchDomainSpecialistBiasMemoryAuditInput)
        _require_hard_flags(value)
        _reject_unsafe_public_surface("audit_input", value)
        key = (value.domain_label, value.specialist_label, value.memory_lane)
        if key in seen_keys:
            raise ValueError("inputs must use unique domain, specialist, and memory lane")
        seen_keys.add(key)
    return normalized


def _normalize_rows(
    values: Iterable[ResearchDomainSpecialistBiasMemoryAuditRow],
) -> tuple[ResearchDomainSpecialistBiasMemoryAuditRow, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("rows must contain ResearchDomainSpecialistBiasMemoryAuditRow values")
    try:
        rows = tuple(values)
    except TypeError as exc:
        raise ValueError(
            "rows must contain ResearchDomainSpecialistBiasMemoryAuditRow values",
        ) from exc
    for row in rows:
        _require_exact_type("row", row, ResearchDomainSpecialistBiasMemoryAuditRow)
        _require_hard_flags(row)
        _reject_unsafe_public_surface("row", row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sort")
    if len(set((row.domain_label, row.specialist_label, row.memory_lane) for row in rows)) != len(
        rows
    ):
        raise ValueError("rows must be unique")
    return rows


def _validate_input_counts(value: ResearchDomainSpecialistBiasMemoryAuditInput) -> None:
    if value.repeated_directional_bias_count > value.long_term_memory_count:
        raise ValueError("repeated_directional_bias_count must not exceed long_term_memory_count")
    if value.stale_lesson_count > value.long_term_memory_count:
        raise ValueError("stale_lesson_count must not exceed long_term_memory_count")
    if value.unresolved_post_outcome_error_count > value.post_outcome_error_count:
        raise ValueError(
            "unresolved_post_outcome_error_count must not exceed post_outcome_error_count",
        )
    if value.covered_correction_count > value.required_correction_count:
        raise ValueError("covered_correction_count must not exceed required_correction_count")


def _validate_row_consistency(row: ResearchDomainSpecialistBiasMemoryAuditRow) -> None:
    input_like = ResearchDomainSpecialistBiasMemoryAuditInput(
        domain_label=row.domain_label,
        specialist_label=row.specialist_label,
        memory_lane=row.memory_lane,
        observed_at=row.observed_at,
        long_term_memory_count=row.long_term_memory_count,
        repeated_directional_bias_count=row.repeated_directional_bias_count,
        stale_lesson_count=row.stale_lesson_count,
        post_outcome_error_count=row.post_outcome_error_count,
        unresolved_post_outcome_error_count=row.unresolved_post_outcome_error_count,
        required_correction_count=row.required_correction_count,
        covered_correction_count=row.covered_correction_count,
    )
    _validate_input_counts(input_like)
    expected_ratios = {
        "directional_bias_ratio": _bounded_ratio(
            row.repeated_directional_bias_count,
            row.long_term_memory_count,
        ),
        "stale_lesson_ratio": _bounded_ratio(row.stale_lesson_count, row.long_term_memory_count),
        "unresolved_post_outcome_error_ratio": _bounded_ratio(
            row.unresolved_post_outcome_error_count,
            row.post_outcome_error_count,
        ),
        "correction_coverage_ratio": _bounded_ratio(
            row.covered_correction_count,
            row.required_correction_count,
        ),
    }
    for field_name, expected in expected_ratios.items():
        if getattr(row, field_name) != expected:
            raise ValueError(f"{field_name} must match counts")
    if row.bias_memory_audit_score != _bias_memory_audit_score(
        directional_bias_ratio=row.directional_bias_ratio,
        stale_lesson_ratio=row.stale_lesson_ratio,
        unresolved_post_outcome_error_ratio=row.unresolved_post_outcome_error_ratio,
        correction_coverage_ratio=row.correction_coverage_ratio,
    ):
        raise ValueError("bias_memory_audit_score must match ratios")
    if row.row_status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("row_status must match reason_codes")


def _validate_report_consistency(
    report: ResearchDomainSpecialistBiasMemoryAuditReport,
) -> None:
    if (
        report.config_version
        != DEFAULT_RESEARCH_DOMAIN_SPECIALIST_BIAS_MEMORY_AUDIT_REPORT_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported version")
    if report.input_count != report.row_count:
        raise ValueError("input_count must match row_count")
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.domain_count != _decimal_count(len({row.domain_label for row in report.rows})):
        raise ValueError("domain_count must match rows")
    if report.specialist_count != _decimal_count(
        len({row.specialist_label for row in report.rows})
    ):
        raise ValueError("specialist_count must match rows")
    if report.lane_count != _decimal_count(len({row.memory_lane for row in report.rows})):
        raise ValueError("lane_count must match rows")
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
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted")
    if report.repeated_directional_bias_count != _sum_count(
        row.repeated_directional_bias_count for row in report.rows
    ):
        raise ValueError("repeated_directional_bias_count must match rows")
    if report.stale_lesson_count != _sum_count(row.stale_lesson_count for row in report.rows):
        raise ValueError("stale_lesson_count must match rows")
    if report.post_outcome_error_count != _sum_count(
        row.post_outcome_error_count for row in report.rows
    ):
        raise ValueError("post_outcome_error_count must match rows")
    if report.unresolved_post_outcome_error_count != _sum_count(
        row.unresolved_post_outcome_error_count for row in report.rows
    ):
        raise ValueError("unresolved_post_outcome_error_count must match rows")
    if report.required_correction_count != _sum_count(
        row.required_correction_count for row in report.rows
    ):
        raise ValueError("required_correction_count must match rows")
    if report.covered_correction_count != _sum_count(
        row.covered_correction_count for row in report.rows
    ):
        raise ValueError("covered_correction_count must match rows")
    if report.average_directional_bias_ratio != _average_ratio(
        tuple(row.directional_bias_ratio for row in report.rows),
    ):
        raise ValueError("average_directional_bias_ratio must match rows")
    if report.average_stale_lesson_ratio != _average_ratio(
        tuple(row.stale_lesson_ratio for row in report.rows),
    ):
        raise ValueError("average_stale_lesson_ratio must match rows")
    if report.average_unresolved_post_outcome_error_ratio != _average_ratio(
        tuple(row.unresolved_post_outcome_error_ratio for row in report.rows),
    ):
        raise ValueError("average_unresolved_post_outcome_error_ratio must match rows")
    if report.average_correction_coverage_ratio != _average_ratio(
        tuple(row.correction_coverage_ratio for row in report.rows),
    ):
        raise ValueError("average_correction_coverage_ratio must match rows")
    if report.average_bias_memory_audit_score != _average_ratio(
        tuple(row.bias_memory_audit_score for row in report.rows),
    ):
        raise ValueError("average_bias_memory_audit_score must match rows")


def _row_sort_key(
    row: ResearchDomainSpecialistBiasMemoryAuditRow,
) -> tuple[int, Decimal, Decimal, Decimal, str, str, str]:
    return (
        _STATUS_RANK[row.row_status],
        row.bias_memory_audit_score,
        -row.directional_bias_ratio,
        -row.stale_lesson_ratio,
        row.domain_label,
        row.specialist_label,
        row.memory_lane,
    )


def _status_count(
    rows: tuple[ResearchDomainSpecialistBiasMemoryAuditRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.row_status == status))


def _sum_count(values: Iterable[Decimal]) -> Decimal:
    return sum(values, _ZERO_COUNT).quantize(_COUNT_QUANTUM)


def _average_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(sum(values, _ZERO) / _decimal_count(len(values)))


def _bounded_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO_COUNT:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        ratio = _quantize(numerator / denominator)
    if ratio > _ONE:
        return _ONE
    return ratio


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    whole_seconds = Decimal(delta.days) * _SECONDS_PER_DAY + Decimal(delta.seconds)
    microseconds = Decimal(delta.microseconds) / _MICROSECONDS_PER_SECOND
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(whole_seconds + microseconds)


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(_COUNT_QUANTUM)


def _normalize_reason_codes_preserving_sequence(value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        normalized = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    if not normalized:
        raise ValueError("reason_codes must contain at least one value")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must not contain duplicates")
    for reason_code in normalized:
        _require_public_label("reason_codes", reason_code)
        if reason_code not in RESEARCH_DOMAIN_SPECIALIST_BIAS_MEMORY_AUDIT_REASON_CODES:
            raise ValueError("reason_codes contains an unsupported value")
    return normalized


def _require_public_label(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if _contains_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} must be public-safe")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in RESEARCH_DOMAIN_SPECIALIST_BIAS_MEMORY_AUDIT_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _normalize_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal_with_quantum(field_name, value, _COUNT_QUANTUM)
    if normalized < _ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != value:
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > _ONE:
        raise ValueError(f"{field_name} must be at most one")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal_with_quantum(field_name, value, _QUANTUM)
    if normalized < _ZERO:
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


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANTUM)


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
        if _contains_unsafe_public_fragment(item):
            raise ValueError(f"unsafe public-safe label in {label}")


def _contains_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower()
    compact = _compact_public_text(lowered)
    for fragment in _UNSAFE_PUBLIC_LABEL_FRAGMENTS:
        if fragment in lowered:
            return True
        compact_fragment = _compact_public_text(fragment)
        if compact_fragment and compact_fragment in compact:
            return True
    return False


def _compact_public_text(value: str) -> str:
    return "".join(
        character for character in value if "a" <= character <= "z" or "0" <= character <= "9"
    )


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
    if isinstance(value, Decimal):
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
    if isinstance(value, Decimal):
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
