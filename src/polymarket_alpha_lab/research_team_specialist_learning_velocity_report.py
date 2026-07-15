"""Report-only specialist team learning velocity reducer."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, DecimalException, ROUND_HALF_UP, localcontext
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_TEAM_SPECIALIST_LEARNING_VELOCITY_CONFIG_VERSION = (
    "research-team-specialist-learning-velocity-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_UP)
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_ANONYMIZED_SPECIALIST_TEAM_KEY_RE = re.compile(r"^anon_[0-9a-f]{64}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_STATUSES = frozenset(("pass", "watch", "block"))
_STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_UNSAFE_PUBLIC_TERMS = (
    "candidate",
    "market",
    "slug",
    "question",
    "source",
    "url",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "live",
    "auth",
    "network",
    "database",
    "sizing",
    "recommendation",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
)
_REASON_CODE_SEQUENCE = (
    "resolved_feedback_missing",
    "resolved_feedback_depth_watch",
    "memory_freshness_watch",
    "memory_freshness_block",
    "calibration_drift_watch",
    "calibration_drift_block",
    "workload_pressure_watch",
    "workload_pressure_block",
    "learning_velocity_score_watch",
    "learning_velocity_score_block",
    "specialist_learning_velocity_pass",
    "specialist_learning_velocity_empty",
)


class _NoSubclass:
    def __init_subclass__(cls) -> None:
        if _NoSubclass not in cls.__bases__:
            raise TypeError(f"{cls.__name__} does not support subclassing")


@dataclass(frozen=True)
class ResearchTeamSpecialistLearningVelocityConfig(_NoSubclass):
    config_version: str = DEFAULT_RESEARCH_TEAM_SPECIALIST_LEARNING_VELOCITY_CONFIG_VERSION
    min_resolved_outcome_feedback_count: Decimal = Decimal("4.000000")
    watch_learning_velocity_score: Decimal = Decimal("0.500000")
    block_learning_velocity_score: Decimal = Decimal("0.250000")
    watch_memory_age_seconds: Decimal = Decimal("604800.000000")
    block_memory_age_seconds: Decimal = Decimal("8640000.000000")
    watch_calibration_drift: Decimal = Decimal("0.050000")
    block_calibration_drift: Decimal = Decimal("0.100000")
    watch_workload_pressure: Decimal = Decimal("0.500000")
    block_workload_pressure: Decimal = Decimal("0.850000")
    resolved_feedback_depth_weight: Decimal = Decimal("0.237887")
    correction_follow_through_weight: Decimal = Decimal("0.108565")
    memory_freshness_weight: Decimal = Decimal("0.195884")
    calibration_stability_weight: Decimal = Decimal("0.284205")
    workload_capacity_weight: Decimal = Decimal("0.100000")
    velocity_signal_penalty: Decimal = Decimal("0.050000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamSpecialistLearningVelocityConfig, "config")
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_TEAM_SPECIALIST_LEARNING_VELOCITY_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "min_resolved_outcome_feedback_count",
            _require_nonnegative_whole_decimal(
                "min_resolved_outcome_feedback_count",
                self.min_resolved_outcome_feedback_count,
            ),
        )
        for field_name in ("watch_memory_age_seconds", "block_memory_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_resolved_outcome_feedback_count <= _ZERO:
            raise ValueError("min_resolved_outcome_feedback_count must be positive")
        if self.block_memory_age_seconds <= self.watch_memory_age_seconds:
            raise ValueError("block_memory_age_seconds must exceed watch_memory_age_seconds")
        for field_name in (
            "watch_learning_velocity_score",
            "block_learning_velocity_score",
            "watch_calibration_drift",
            "block_calibration_drift",
            "watch_workload_pressure",
            "block_workload_pressure",
            "resolved_feedback_depth_weight",
            "correction_follow_through_weight",
            "memory_freshness_weight",
            "calibration_stability_weight",
            "workload_capacity_weight",
            "velocity_signal_penalty",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_learning_velocity_score > self.watch_learning_velocity_score:
            raise ValueError(
                "block_learning_velocity_score must not exceed watch_learning_velocity_score",
            )
        if self.block_calibration_drift <= self.watch_calibration_drift:
            raise ValueError("block_calibration_drift must exceed watch_calibration_drift")
        if self.block_workload_pressure <= self.watch_workload_pressure:
            raise ValueError("block_workload_pressure must exceed watch_workload_pressure")
        for config_field in fields(self):
            if config_field.name in (
                "config_version",
                "paper_only",
                "report_only",
                "readonly",
            ):
                continue
            if getattr(self, config_field.name) != config_field.default:
                raise ValueError(
                    f"{config_field.name} must use supported default",
                )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)
        _store_public_snapshot(self)


@dataclass(frozen=True)
class ResearchTeamSpecialistLearningVelocityDomainFeedback(_NoSubclass):
    domain_key: str
    specialist_team_key: str
    observed_at: datetime
    resolved_outcome_feedback_count: Decimal
    correction_follow_through_rate: Decimal
    memory_age_seconds: Decimal
    calibration_drift: Decimal
    workload_pressure: Decimal
    feedback_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistLearningVelocityDomainFeedback,
            "domain feedback",
        )
        for field_name in ("domain_key", "feedback_config_version"):
            _require_public_identifier(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "specialist_team_key",
            _anonymize_specialist_team_key(self.specialist_team_key),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "resolved_outcome_feedback_count",
            _require_nonnegative_whole_decimal(
                "resolved_outcome_feedback_count",
                self.resolved_outcome_feedback_count,
            ),
        )
        object.__setattr__(
            self,
            "memory_age_seconds",
            _require_nonnegative_decimal("memory_age_seconds", self.memory_age_seconds),
        )
        for field_name in (
            "correction_follow_through_rate",
            "calibration_drift",
            "workload_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("domain feedback", self)
        _reject_unsafe_public_payload("domain feedback", self)
        _store_public_snapshot(self)


@dataclass(frozen=True)
class ResearchTeamSpecialistLearningVelocityDomainRow(_NoSubclass):
    domain_key: str
    specialist_team_key: str
    feedback_config_version: str
    observed_at: datetime
    resolved_outcome_feedback_count: Decimal
    resolved_feedback_depth_score: Decimal
    correction_follow_through_rate: Decimal
    memory_age_seconds: Decimal
    memory_freshness_score: Decimal
    calibration_drift: Decimal
    calibration_stability_score: Decimal
    workload_pressure: Decimal
    workload_capacity_score: Decimal
    learning_velocity_score: Decimal
    velocity_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamSpecialistLearningVelocityDomainRow, "row")
        for field_name in ("domain_key", "feedback_config_version"):
            _require_public_identifier(field_name, getattr(self, field_name))
        _require_anonymized_specialist_team_key(self.specialist_team_key)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "resolved_outcome_feedback_count",
            _require_nonnegative_whole_decimal(
                "resolved_outcome_feedback_count",
                self.resolved_outcome_feedback_count,
            ),
        )
        object.__setattr__(
            self,
            "memory_age_seconds",
            _require_nonnegative_decimal("memory_age_seconds", self.memory_age_seconds),
        )
        for field_name in (
            "resolved_feedback_depth_score",
            "correction_follow_through_rate",
            "memory_freshness_score",
            "calibration_drift",
            "calibration_stability_score",
            "workload_pressure",
            "workload_capacity_score",
            "learning_velocity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("velocity_status", self.velocity_status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)
        _store_public_snapshot(self)


@dataclass(frozen=True)
class ResearchTeamSpecialistLearningVelocityPublicPayloadItem(_NoSubclass):
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistLearningVelocityPublicPayloadItem,
            "public payload item",
        )
        _require_public_identifier("key", self.key)
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)
        _store_public_snapshot(self)


@dataclass(frozen=True)
class ResearchTeamSpecialistLearningVelocityReasonCodeCount(_NoSubclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistLearningVelocityReasonCodeCount,
            "reason code count",
        )
        _require_supported_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason code count", self)
        _reject_unsafe_public_payload("reason code count", self)
        _store_public_snapshot(self)


@dataclass(frozen=True)
class ResearchTeamSpecialistLearningVelocityReport(_NoSubclass):
    generated_at: datetime
    config_version: str
    report_status: str
    domain_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_learning_velocity_score: Decimal
    min_learning_velocity_score: Decimal
    max_workload_pressure: Decimal
    max_memory_age_seconds: Decimal
    rows: tuple[ResearchTeamSpecialistLearningVelocityDomainRow, ...]
    feedback_config_versions: tuple[tuple[str, str], ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchTeamSpecialistLearningVelocityReasonCodeCount,
        ...,
    ]
    public_payload: tuple[ResearchTeamSpecialistLearningVelocityPublicPayloadItem, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamSpecialistLearningVelocityReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_TEAM_SPECIALIST_LEARNING_VELOCITY_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _require_status("report_status", self.report_status)
        for field_name in (
            "domain_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "max_memory_age_seconds",
            _require_nonnegative_decimal(
                "max_memory_age_seconds",
                self.max_memory_age_seconds,
            ),
        )
        for field_name in (
            "average_learning_velocity_score",
            "min_learning_velocity_score",
            "max_workload_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "feedback_config_versions",
            _normalize_feedback_config_versions(self.feedback_config_versions),
        )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "public_payload", _normalize_public_payload(self.public_payload))
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")
        _store_public_snapshot(self)

    @property
    def payload(self) -> dict[str, object]:
        return research_team_specialist_learning_velocity_report_payload(self)


_PUBLIC_DATACLASS_TYPES = (
    ResearchTeamSpecialistLearningVelocityConfig,
    ResearchTeamSpecialistLearningVelocityDomainFeedback,
    ResearchTeamSpecialistLearningVelocityDomainRow,
    ResearchTeamSpecialistLearningVelocityPublicPayloadItem,
    ResearchTeamSpecialistLearningVelocityReasonCodeCount,
    ResearchTeamSpecialistLearningVelocityReport,
)


def build_research_team_specialist_learning_velocity_report(
    feedback: Sequence[ResearchTeamSpecialistLearningVelocityDomainFeedback],
    *,
    generated_at: datetime,
    config: ResearchTeamSpecialistLearningVelocityConfig | None = None,
    public_payload: Sequence[ResearchTeamSpecialistLearningVelocityPublicPayloadItem] = (),
) -> ResearchTeamSpecialistLearningVelocityReport:
    """Build a local report-only learning velocity snapshot by specialist domain."""

    if config is None:
        config = ResearchTeamSpecialistLearningVelocityConfig()
    if type(config) is not ResearchTeamSpecialistLearningVelocityConfig:
        raise ValueError("config must be a ResearchTeamSpecialistLearningVelocityConfig")
    _require_untampered_public_dataclass(config, "config")
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_feedback = _normalize_feedback(feedback)
    for item in normalized_feedback:
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    rows = tuple(
        sorted(
            (_row_from_feedback(item, config=config) for item in normalized_feedback),
            key=_row_sort_key,
        ),
    )
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "report_status": _report_status(rows),
        "domain_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_learning_velocity_score": _average(
            tuple(row.learning_velocity_score for row in rows),
        ),
        "min_learning_velocity_score": min(
            (row.learning_velocity_score for row in rows),
            default=_ZERO,
        ),
        "max_workload_pressure": max((row.workload_pressure for row in rows), default=_ZERO),
        "max_memory_age_seconds": max((row.memory_age_seconds for row in rows), default=_ZERO),
        "rows": rows,
        "feedback_config_versions": _feedback_config_versions(rows),
        "reason_codes": _report_reason_codes(rows),
        "reason_code_counts": _reason_code_counts(
            rows,
            _report_reason_codes(rows),
        ),
        "public_payload": _normalize_public_payload(public_payload),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchTeamSpecialistLearningVelocityReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_team_specialist_learning_velocity_report_digest(
    report: ResearchTeamSpecialistLearningVelocityReport | Mapping[str, Any],
) -> str:
    """Return the canonical sha256 digest for a validated public report."""

    if type(report) is ResearchTeamSpecialistLearningVelocityReport:
        _revalidate_report_for_payload(report)
        return _report_digest_from_values(_report_values_without_digest(report))
    if type(report) is dict:
        validate_research_team_specialist_learning_velocity_report_payload(report)
        return _require_sha256_digest(
            "derived_validation_digest",
            report["derived_validation_digest"],
        )
    raise ValueError(
        "report must be a ResearchTeamSpecialistLearningVelocityReport or exact dict payload",
    )


def research_team_specialist_learning_velocity_report_payload(
    report: ResearchTeamSpecialistLearningVelocityReport | Mapping[str, Any],
) -> dict[str, object]:
    """Return the strict JSON-ready public payload for a validated report."""

    if type(report) is ResearchTeamSpecialistLearningVelocityReport:
        _revalidate_report_for_payload(report)
        normalized_report = report
    elif type(report) is dict:
        validate_research_team_specialist_learning_velocity_report_payload(report)
        normalized_report = _report_from_public_payload(report)
    else:
        raise ValueError(
            "report must be a ResearchTeamSpecialistLearningVelocityReport or exact dict payload",
        )
    payload = _json_ready(normalized_report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _validate_public_payload_schema(payload)
    _reject_unsafe_public_payload(
        "ResearchTeamSpecialistLearningVelocityReport.payload",
        payload,
        allow_json_containers=True,
    )
    return payload


def validate_research_team_specialist_learning_velocity_report_payload(
    payload: Mapping[str, Any],
) -> None:
    """Validate and reconstruct an exact canonical public report mapping."""

    if type(payload) is not dict:
        raise ValueError("payload must be an exact dict")
    _validate_public_payload_schema(payload)
    _reject_unsafe_public_payload(
        "payload",
        payload,
        allow_json_containers=True,
    )
    digest = _require_sha256_digest(
        "derived_validation_digest",
        payload["derived_validation_digest"],
    )
    unsigned = {
        key: payload[key]
        for key in tuple(
            field.name
            for field in fields(ResearchTeamSpecialistLearningVelocityReport)
            if field.name != "derived_validation_digest"
        )
    }
    if digest != _report_digest_from_values(unsigned):
        raise ValueError("derived_validation_digest does not match report payload")
    _report_from_public_payload(payload)


def _report_from_public_payload(
    payload: dict[str, Any],
) -> ResearchTeamSpecialistLearningVelocityReport:
    _validate_public_payload_schema(payload)
    rows = _rows_from_public_payload(payload["rows"], "rows")
    if len({row.domain_key for row in rows}) != len(rows):
        raise ValueError("rows domain_key values must be unique")
    if tuple(sorted(rows, key=_row_sort_key)) != rows:
        raise ValueError("rows must be in canonical row order")
    feedback_config_versions = _feedback_versions_from_public_payload(
        payload["feedback_config_versions"],
        "feedback_config_versions",
    )
    reason_codes = _reason_codes_from_public_payload(
        payload["reason_codes"],
        "reason_codes",
    )
    reason_code_counts = _reason_counts_from_public_payload(
        payload["reason_code_counts"],
        "reason_code_counts",
    )
    public_payload = _public_items_from_public_payload(
        payload["public_payload"],
        "public_payload",
    )
    return ResearchTeamSpecialistLearningVelocityReport(
        generated_at=_datetime_from_public_payload(
            "generated_at",
            payload["generated_at"],
            "generated_at",
        ),
        config_version=_identifier_from_public_payload(
            "config_version",
            payload["config_version"],
            "config_version",
        ),
        report_status=_status_from_public_payload(
            "report_status",
            payload["report_status"],
            "report_status",
        ),
        domain_count=_decimal_from_public_payload(
            "domain_count",
            payload["domain_count"],
            "domain_count",
            _require_nonnegative_whole_decimal,
        ),
        pass_count=_decimal_from_public_payload(
            "pass_count",
            payload["pass_count"],
            "pass_count",
            _require_nonnegative_whole_decimal,
        ),
        watch_count=_decimal_from_public_payload(
            "watch_count",
            payload["watch_count"],
            "watch_count",
            _require_nonnegative_whole_decimal,
        ),
        block_count=_decimal_from_public_payload(
            "block_count",
            payload["block_count"],
            "block_count",
            _require_nonnegative_whole_decimal,
        ),
        average_learning_velocity_score=_decimal_from_public_payload(
            "average_learning_velocity_score",
            payload["average_learning_velocity_score"],
            "average_learning_velocity_score",
            _require_ratio_decimal,
        ),
        min_learning_velocity_score=_decimal_from_public_payload(
            "min_learning_velocity_score",
            payload["min_learning_velocity_score"],
            "min_learning_velocity_score",
            _require_ratio_decimal,
        ),
        max_workload_pressure=_decimal_from_public_payload(
            "max_workload_pressure",
            payload["max_workload_pressure"],
            "max_workload_pressure",
            _require_ratio_decimal,
        ),
        max_memory_age_seconds=_decimal_from_public_payload(
            "max_memory_age_seconds",
            payload["max_memory_age_seconds"],
            "max_memory_age_seconds",
            _require_nonnegative_decimal,
        ),
        rows=rows,
        feedback_config_versions=feedback_config_versions,
        reason_codes=reason_codes,
        reason_code_counts=reason_code_counts,
        public_payload=public_payload,
        derived_validation_digest=_require_sha256_digest(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_true_from_public_payload(payload["paper_only"], "paper_only"),
        report_only=_true_from_public_payload(payload["report_only"], "report_only"),
        readonly=_true_from_public_payload(payload["readonly"], "readonly"),
    )


def _row_from_public_payload(
    value: object,
    path: str,
) -> ResearchTeamSpecialistLearningVelocityDomainRow:
    _require_public_mapping_schema(
        value,
        tuple(field.name for field in fields(ResearchTeamSpecialistLearningVelocityDomainRow)),
        path,
    )
    return ResearchTeamSpecialistLearningVelocityDomainRow(
        domain_key=_identifier_from_public_payload(
            "domain_key",
            value["domain_key"],
            f"{path}.domain_key",
        ),
        specialist_team_key=_anonymized_key_from_public_payload(
            value["specialist_team_key"],
            f"{path}.specialist_team_key",
        ),
        feedback_config_version=_identifier_from_public_payload(
            "feedback_config_version",
            value["feedback_config_version"],
            f"{path}.feedback_config_version",
        ),
        observed_at=_datetime_from_public_payload(
            "observed_at",
            value["observed_at"],
            f"{path}.observed_at",
        ),
        resolved_outcome_feedback_count=_decimal_from_public_payload(
            "resolved_outcome_feedback_count",
            value["resolved_outcome_feedback_count"],
            f"{path}.resolved_outcome_feedback_count",
            _require_nonnegative_whole_decimal,
        ),
        resolved_feedback_depth_score=_decimal_from_public_payload(
            "resolved_feedback_depth_score",
            value["resolved_feedback_depth_score"],
            f"{path}.resolved_feedback_depth_score",
            _require_ratio_decimal,
        ),
        correction_follow_through_rate=_decimal_from_public_payload(
            "correction_follow_through_rate",
            value["correction_follow_through_rate"],
            f"{path}.correction_follow_through_rate",
            _require_ratio_decimal,
        ),
        memory_age_seconds=_decimal_from_public_payload(
            "memory_age_seconds",
            value["memory_age_seconds"],
            f"{path}.memory_age_seconds",
            _require_nonnegative_decimal,
        ),
        memory_freshness_score=_decimal_from_public_payload(
            "memory_freshness_score",
            value["memory_freshness_score"],
            f"{path}.memory_freshness_score",
            _require_ratio_decimal,
        ),
        calibration_drift=_decimal_from_public_payload(
            "calibration_drift",
            value["calibration_drift"],
            f"{path}.calibration_drift",
            _require_ratio_decimal,
        ),
        calibration_stability_score=_decimal_from_public_payload(
            "calibration_stability_score",
            value["calibration_stability_score"],
            f"{path}.calibration_stability_score",
            _require_ratio_decimal,
        ),
        workload_pressure=_decimal_from_public_payload(
            "workload_pressure",
            value["workload_pressure"],
            f"{path}.workload_pressure",
            _require_ratio_decimal,
        ),
        workload_capacity_score=_decimal_from_public_payload(
            "workload_capacity_score",
            value["workload_capacity_score"],
            f"{path}.workload_capacity_score",
            _require_ratio_decimal,
        ),
        learning_velocity_score=_decimal_from_public_payload(
            "learning_velocity_score",
            value["learning_velocity_score"],
            f"{path}.learning_velocity_score",
            _require_ratio_decimal,
        ),
        velocity_status=_status_from_public_payload(
            "velocity_status",
            value["velocity_status"],
            f"{path}.velocity_status",
        ),
        reason_codes=_reason_codes_from_public_payload(
            value["reason_codes"],
            f"{path}.reason_codes",
        ),
        paper_only=_true_from_public_payload(value["paper_only"], f"{path}.paper_only"),
        report_only=_true_from_public_payload(value["report_only"], f"{path}.report_only"),
        readonly=_true_from_public_payload(value["readonly"], f"{path}.readonly"),
    )


def _reason_count_from_public_payload(
    value: object,
    path: str,
) -> ResearchTeamSpecialistLearningVelocityReasonCodeCount:
    _require_public_mapping_schema(
        value,
        tuple(
            field.name
            for field in fields(ResearchTeamSpecialistLearningVelocityReasonCodeCount)
        ),
        path,
    )
    return ResearchTeamSpecialistLearningVelocityReasonCodeCount(
        reason_code=_reason_code_from_public_payload(
            value["reason_code"],
            f"{path}.reason_code",
        ),
        count=_decimal_from_public_payload(
            "count",
            value["count"],
            f"{path}.count",
            _require_nonnegative_whole_decimal,
        ),
        paper_only=_true_from_public_payload(value["paper_only"], f"{path}.paper_only"),
        report_only=_true_from_public_payload(value["report_only"], f"{path}.report_only"),
        readonly=_true_from_public_payload(value["readonly"], f"{path}.readonly"),
    )


def _public_item_from_public_payload(
    value: object,
    path: str,
) -> ResearchTeamSpecialistLearningVelocityPublicPayloadItem:
    _require_public_mapping_schema(
        value,
        tuple(
            field.name
            for field in fields(ResearchTeamSpecialistLearningVelocityPublicPayloadItem)
        ),
        path,
    )
    return ResearchTeamSpecialistLearningVelocityPublicPayloadItem(
        key=_identifier_from_public_payload("key", value["key"], f"{path}.key"),
        value=_text_from_public_payload(value["value"], f"{path}.value"),
        paper_only=_true_from_public_payload(value["paper_only"], f"{path}.paper_only"),
        report_only=_true_from_public_payload(value["report_only"], f"{path}.report_only"),
        readonly=_true_from_public_payload(value["readonly"], f"{path}.readonly"),
    )


def _rows_from_public_payload(
    value: object,
    path: str,
) -> tuple[ResearchTeamSpecialistLearningVelocityDomainRow, ...]:
    if type(value) is not list:
        raise ValueError(f"{path} must be a list")
    return tuple(
        _row_from_public_payload(item, f"{path}[{index}]")
        for index, item in enumerate(value)
    )


def _reason_counts_from_public_payload(
    value: object,
    path: str,
) -> tuple[ResearchTeamSpecialistLearningVelocityReasonCodeCount, ...]:
    if type(value) is not list:
        raise ValueError(f"{path} must be a list")
    counts = tuple(
        _reason_count_from_public_payload(item, f"{path}[{index}]")
        for index, item in enumerate(value)
    )
    if len({item.reason_code for item in counts}) != len(counts):
        raise ValueError(f"{path} reason_code values must be unique")
    if tuple(
        sorted(
            counts,
            key=lambda item: _REASON_CODE_SEQUENCE.index(item.reason_code),
        ),
    ) != counts:
        raise ValueError(f"{path} must be in canonical reason order")
    return counts


def _public_items_from_public_payload(
    value: object,
    path: str,
) -> tuple[ResearchTeamSpecialistLearningVelocityPublicPayloadItem, ...]:
    if type(value) is not list:
        raise ValueError(f"{path} must be a list")
    items = tuple(
        _public_item_from_public_payload(item, f"{path}[{index}]")
        for index, item in enumerate(value)
    )
    if len({item.key for item in items}) != len(items):
        raise ValueError(f"{path} key values must be unique")
    if tuple(sorted(items, key=lambda item: item.key)) != items:
        raise ValueError(f"{path} must be in canonical key order")
    return items


def _feedback_versions_from_public_payload(
    value: object,
    path: str,
) -> tuple[tuple[str, str], ...]:
    if type(value) is not list:
        raise ValueError(f"{path} must be a list")
    normalized: list[tuple[str, str]] = []
    for index, item in enumerate(value):
        if type(item) is not list or len(item) != 2:
            raise ValueError(f"{path}[{index}] must be a string pair")
        normalized.append(
            (
                _identifier_from_public_payload(
                    "domain_key",
                    item[0],
                    f"{path}[{index}][0]",
                ),
                _identifier_from_public_payload(
                    "feedback_config_version",
                    item[1],
                    f"{path}[{index}][1]",
                ),
            ),
        )
    result = tuple(normalized)
    if len({item[0] for item in result}) != len(result):
        raise ValueError(f"{path} domain_key values must be unique")
    if tuple(sorted(result)) != result:
        raise ValueError(f"{path} must be in canonical order")
    return result


def _reason_codes_from_public_payload(value: object, path: str) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{path} must be a list")
    reason_codes = tuple(
        _reason_code_from_public_payload(item, f"{path}[{index}]")
        for index, item in enumerate(value)
    )
    if _normalize_reason_codes(reason_codes) != reason_codes:
        raise ValueError(f"{path} must be canonical reason_codes")
    return reason_codes


def _require_public_mapping_schema(
    value: object,
    expected_keys: tuple[str, ...],
    path: str,
) -> None:
    if type(value) is not dict:
        raise ValueError(f"{path} must be an exact dict")
    _require_exact_payload_keys(path, value, expected_keys)


def _decimal_from_public_payload(
    field_name: str,
    value: object,
    path: str,
    normalizer: Any,
) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{path} must be a Decimal-derived string")
    try:
        raw_value = Decimal(value)
    except (DecimalException, ValueError) as exc:
        raise ValueError(f"{path} must be a Decimal-derived string") from exc
    try:
        normalized = normalizer(field_name, raw_value)
    except ValueError as exc:
        raise ValueError(f"{path} {exc}") from exc
    if value != str(normalized):
        raise ValueError(f"{path} must be a canonical Decimal-derived string")
    return normalized


def _datetime_from_public_payload(
    field_name: str,
    value: object,
    path: str,
) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{path} must be a canonical UTC datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{path} must be a canonical UTC datetime string") from exc
    normalized = _as_utc(field_name, parsed)
    if value != normalized.isoformat():
        raise ValueError(f"{path} must be a canonical UTC datetime string")
    return normalized


def _identifier_from_public_payload(
    field_name: str,
    value: object,
    path: str,
) -> str:
    try:
        return _require_public_identifier(field_name, value)
    except ValueError as exc:
        raise ValueError(f"{path} must be a public identifier") from exc


def _anonymized_key_from_public_payload(value: object, path: str) -> str:
    try:
        return _require_anonymized_specialist_team_key(value)
    except ValueError as exc:
        raise ValueError(f"{path} must be anonymized with sha256") from exc


def _text_from_public_payload(value: object, path: str) -> str:
    try:
        return _require_public_text("value", value)
    except ValueError as exc:
        raise ValueError(f"{path} must be public text") from exc


def _status_from_public_payload(field_name: str, value: object, path: str) -> str:
    try:
        return _require_status(field_name, value)
    except ValueError as exc:
        raise ValueError(f"{path} must be pass, watch, or block") from exc


def _reason_code_from_public_payload(value: object, path: str) -> str:
    try:
        return _require_supported_reason_code("reason_code", value)
    except ValueError as exc:
        raise ValueError(f"{path} must be a supported reason_code") from exc


def _true_from_public_payload(value: object, path: str) -> bool:
    if value is not True:
        raise ValueError(f"{path} must be True")
    return True


def _row_from_feedback(
    item: ResearchTeamSpecialistLearningVelocityDomainFeedback,
    *,
    config: ResearchTeamSpecialistLearningVelocityConfig,
) -> ResearchTeamSpecialistLearningVelocityDomainRow:
    (
        depth_score,
        memory_score,
        calibration_score,
        capacity_score,
        learning_velocity_score,
        status,
        reason_codes,
    ) = _derive_row_values(item, config=config)
    return ResearchTeamSpecialistLearningVelocityDomainRow(
        domain_key=item.domain_key,
        specialist_team_key=item.specialist_team_key,
        feedback_config_version=item.feedback_config_version,
        observed_at=item.observed_at,
        resolved_outcome_feedback_count=item.resolved_outcome_feedback_count,
        resolved_feedback_depth_score=depth_score,
        correction_follow_through_rate=item.correction_follow_through_rate,
        memory_age_seconds=item.memory_age_seconds,
        memory_freshness_score=memory_score,
        calibration_drift=item.calibration_drift,
        calibration_stability_score=calibration_score,
        workload_pressure=item.workload_pressure,
        workload_capacity_score=capacity_score,
        learning_velocity_score=learning_velocity_score,
        velocity_status=status,
        reason_codes=reason_codes,
    )


def _derive_row_values(
    item: (
        ResearchTeamSpecialistLearningVelocityDomainFeedback
        | ResearchTeamSpecialistLearningVelocityDomainRow
    ),
    *,
    config: ResearchTeamSpecialistLearningVelocityConfig,
) -> tuple[Decimal, Decimal, Decimal, Decimal, Decimal, str, tuple[str, ...]]:
    with localcontext(_DECIMAL_CONTEXT):
        depth_score = _clamp_ratio(
            item.resolved_outcome_feedback_count
            / config.min_resolved_outcome_feedback_count,
        )
        memory_score = _memory_freshness_score(item.memory_age_seconds, config)
        calibration_score = _clamp_ratio(_ONE - item.calibration_drift)
        capacity_score = _clamp_ratio(_ONE - item.workload_pressure)
        reason_codes = _row_reason_codes(
            item,
            config=config,
            depth_score=depth_score,
            memory_score=memory_score,
        )
        pre_penalty_score = _clamp_ratio(
            depth_score * config.resolved_feedback_depth_weight
            + item.correction_follow_through_rate
            * config.correction_follow_through_weight
            + memory_score * config.memory_freshness_weight
            + calibration_score * config.calibration_stability_weight
            + capacity_score * config.workload_capacity_weight,
        )
        penalty_count = Decimal(
            sum(
                1
                for reason_code in reason_codes
                if reason_code != "specialist_learning_velocity_pass"
            ),
        )
        learning_velocity_score = _clamp_ratio(
            pre_penalty_score - penalty_count * config.velocity_signal_penalty,
        )
        status = _row_status(
            learning_velocity_score=learning_velocity_score,
            reason_codes=reason_codes,
            config=config,
        )
        if status == "pass":
            reason_codes = ("specialist_learning_velocity_pass",)
        elif learning_velocity_score <= config.block_learning_velocity_score:
            reason_codes = _normalize_reason_codes(
                (*reason_codes, "learning_velocity_score_block"),
            )
        elif learning_velocity_score < config.watch_learning_velocity_score:
            reason_codes = _normalize_reason_codes(
                (*reason_codes, "learning_velocity_score_watch"),
            )
        return (
            depth_score,
            memory_score,
            calibration_score,
            capacity_score,
            learning_velocity_score,
            status,
            reason_codes,
        )


def _memory_freshness_score(
    memory_age_seconds: Decimal,
    config: ResearchTeamSpecialistLearningVelocityConfig,
) -> Decimal:
    if memory_age_seconds <= config.watch_memory_age_seconds:
        return _ONE
    if memory_age_seconds >= config.block_memory_age_seconds:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _clamp_ratio(
            (config.block_memory_age_seconds - memory_age_seconds)
            / (config.block_memory_age_seconds - config.watch_memory_age_seconds),
        )


def _row_reason_codes(
    item: (
        ResearchTeamSpecialistLearningVelocityDomainFeedback
        | ResearchTeamSpecialistLearningVelocityDomainRow
    ),
    *,
    config: ResearchTeamSpecialistLearningVelocityConfig,
    depth_score: Decimal,
    memory_score: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if item.resolved_outcome_feedback_count == _ZERO:
        reason_codes.append("resolved_feedback_missing")
    elif depth_score < _ONE:
        reason_codes.append("resolved_feedback_depth_watch")
    if memory_score == _ZERO or item.memory_age_seconds >= config.block_memory_age_seconds:
        reason_codes.append("memory_freshness_block")
    elif item.memory_age_seconds > config.watch_memory_age_seconds:
        reason_codes.append("memory_freshness_watch")
    if item.calibration_drift >= config.block_calibration_drift:
        reason_codes.append("calibration_drift_block")
    elif item.calibration_drift > config.watch_calibration_drift:
        reason_codes.append("calibration_drift_watch")
    if item.workload_pressure >= config.block_workload_pressure:
        reason_codes.append("workload_pressure_block")
    elif item.workload_pressure > config.watch_workload_pressure:
        reason_codes.append("workload_pressure_watch")
    return _normalize_reason_codes(tuple(reason_codes))


def _row_status(
    *,
    learning_velocity_score: Decimal,
    reason_codes: tuple[str, ...],
    config: ResearchTeamSpecialistLearningVelocityConfig,
) -> str:
    if any(reason_code.endswith("_block") or reason_code.endswith("_missing") for reason_code in reason_codes):
        return "block"
    if learning_velocity_score <= config.block_learning_velocity_score:
        return "block"
    if reason_codes or learning_velocity_score < config.watch_learning_velocity_score:
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchTeamSpecialistLearningVelocityDomainRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.velocity_status == "block" for row in rows):
        return "block"
    if any(row.velocity_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _normalize_feedback(
    feedback: Sequence[ResearchTeamSpecialistLearningVelocityDomainFeedback],
) -> tuple[ResearchTeamSpecialistLearningVelocityDomainFeedback, ...]:
    if isinstance(feedback, (str, bytes)) or not isinstance(feedback, Sequence):
        raise ValueError("feedback must be a sequence")
    normalized: list[ResearchTeamSpecialistLearningVelocityDomainFeedback] = []
    seen_domains: set[str] = set()
    for item in feedback:
        if type(item) is not ResearchTeamSpecialistLearningVelocityDomainFeedback:
            raise ValueError(
                "feedback items must be ResearchTeamSpecialistLearningVelocityDomainFeedback",
            )
        _require_untampered_public_dataclass(item, "domain feedback")
        _require_hard_flags("domain feedback", item)
        if item.domain_key in seen_domains:
            raise ValueError("domain_key values must be unique")
        seen_domains.add(item.domain_key)
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: (item.domain_key, item.specialist_team_key)))


def _normalize_rows(
    rows: Sequence[ResearchTeamSpecialistLearningVelocityDomainRow],
) -> tuple[ResearchTeamSpecialistLearningVelocityDomainRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchTeamSpecialistLearningVelocityDomainRow] = []
    seen_domains: set[str] = set()
    for row in rows:
        if type(row) is not ResearchTeamSpecialistLearningVelocityDomainRow:
            raise ValueError("rows must contain ResearchTeamSpecialistLearningVelocityDomainRow")
        _require_untampered_public_dataclass(row, "row")
        _require_hard_flags("row", row)
        if row.domain_key in seen_domains:
            raise ValueError("domain_key values must be unique")
        seen_domains.add(row.domain_key)
        normalized.append(row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_public_payload(
    public_payload: Sequence[ResearchTeamSpecialistLearningVelocityPublicPayloadItem],
) -> tuple[ResearchTeamSpecialistLearningVelocityPublicPayloadItem, ...]:
    if isinstance(public_payload, (str, bytes)) or not isinstance(public_payload, Sequence):
        raise ValueError("public_payload must be a sequence")
    normalized: list[ResearchTeamSpecialistLearningVelocityPublicPayloadItem] = []
    seen_keys: set[str] = set()
    for item in public_payload:
        if type(item) is not ResearchTeamSpecialistLearningVelocityPublicPayloadItem:
            raise ValueError(
                "public_payload items must be ResearchTeamSpecialistLearningVelocityPublicPayloadItem",
            )
        _require_untampered_public_dataclass(item, "public payload item")
        _require_hard_flags("public payload item", item)
        if item.key in seen_keys:
            raise ValueError("public_payload item key values must be unique")
        seen_keys.add(item.key)
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.key))


def _normalize_reason_code_counts(
    values: Sequence[ResearchTeamSpecialistLearningVelocityReasonCodeCount],
) -> tuple[ResearchTeamSpecialistLearningVelocityReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ValueError("reason_code_counts must be a sequence")
    normalized: list[ResearchTeamSpecialistLearningVelocityReasonCodeCount] = []
    seen_reason_codes: set[str] = set()
    for item in values:
        if type(item) is not ResearchTeamSpecialistLearningVelocityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchTeamSpecialistLearningVelocityReasonCodeCount",
            )
        _require_untampered_public_dataclass(item, "reason code count")
        _require_hard_flags("reason code count", item)
        if item.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen_reason_codes.add(item.reason_code)
        normalized.append(item)
    return tuple(
        sorted(
            normalized,
            key=lambda item: _REASON_CODE_SEQUENCE.index(item.reason_code),
        ),
    )


def _normalize_feedback_config_versions(
    values: Sequence[tuple[str, str]],
) -> tuple[tuple[str, str], ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ValueError("feedback_config_versions must be a sequence")
    normalized: list[tuple[str, str]] = []
    seen_domains: set[str] = set()
    for value in values:
        if type(value) is not tuple or len(value) != 2:
            raise ValueError("feedback_config_versions must contain pairs")
        domain_key, config_version = value
        _require_public_identifier("domain_key", domain_key)
        _require_public_identifier("feedback_config_version", config_version)
        if domain_key in seen_domains:
            raise ValueError("feedback_config_versions domain_key values must be unique")
        seen_domains.add(domain_key)
        normalized.append((domain_key, config_version))
    return tuple(sorted(normalized))


def _feedback_config_versions(
    rows: tuple[ResearchTeamSpecialistLearningVelocityDomainRow, ...],
) -> tuple[tuple[str, str], ...]:
    return tuple(sorted((row.domain_key, row.feedback_config_version) for row in rows))


def _validate_row_consistency(row: ResearchTeamSpecialistLearningVelocityDomainRow) -> None:
    (
        expected_depth_score,
        expected_memory_score,
        expected_calibration_score,
        expected_capacity_score,
        expected_learning_velocity_score,
        expected_status,
        expected_reason_codes,
    ) = _derive_row_values(
        row,
        config=ResearchTeamSpecialistLearningVelocityConfig(),
    )
    for field_name, expected in (
        ("resolved_feedback_depth_score", expected_depth_score),
        ("memory_freshness_score", expected_memory_score),
        ("calibration_stability_score", expected_calibration_score),
        ("workload_capacity_score", expected_capacity_score),
        ("learning_velocity_score", expected_learning_velocity_score),
        ("velocity_status", expected_status),
        ("reason_codes", expected_reason_codes),
    ):
        if getattr(row, field_name) != expected:
            raise ValueError(
                f"{field_name} must match source values and supported config",
            )


def _validate_report_consistency(report: ResearchTeamSpecialistLearningVelocityReport) -> None:
    if report.domain_count != _decimal_count(len(report.rows)):
        raise ValueError("domain_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_learning_velocity_score != _average(
        tuple(row.learning_velocity_score for row in report.rows),
    ):
        raise ValueError("average_learning_velocity_score must match rows")
    expected_min = min((row.learning_velocity_score for row in report.rows), default=_ZERO)
    if report.min_learning_velocity_score != expected_min:
        raise ValueError("min_learning_velocity_score must match rows")
    expected_max_workload = max((row.workload_pressure for row in report.rows), default=_ZERO)
    if report.max_workload_pressure != expected_max_workload:
        raise ValueError("max_workload_pressure must match rows")
    expected_max_memory = max((row.memory_age_seconds for row in report.rows), default=_ZERO)
    if report.max_memory_age_seconds != expected_max_memory:
        raise ValueError("max_memory_age_seconds must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(
        report.rows,
        report.reason_codes,
    ):
        raise ValueError("reason_code_counts must match rows")
    if any(row.observed_at > report.generated_at for row in report.rows):
        raise ValueError("row observed_at must not be after generated_at")
    if report.feedback_config_versions != _feedback_config_versions(report.rows):
        raise ValueError("feedback_config_versions must match report rows")


def _revalidate_report_for_payload(
    report: ResearchTeamSpecialistLearningVelocityReport,
) -> None:
    _require_exact_type(report, ResearchTeamSpecialistLearningVelocityReport, "report")
    _require_utc_datetime("generated_at", report.generated_at)
    _require_public_identifier("config_version", report.config_version)
    if report.config_version != DEFAULT_RESEARCH_TEAM_SPECIALIST_LEARNING_VELOCITY_CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")
    _require_status("report_status", report.report_status)
    for field_name in (
        "domain_count",
        "pass_count",
        "watch_count",
        "block_count",
    ):
        _require_canonical_nonnegative_whole_decimal(
            field_name,
            getattr(report, field_name),
        )
    _require_canonical_nonnegative_decimal(
        "max_memory_age_seconds",
        report.max_memory_age_seconds,
    )
    for field_name in (
        "average_learning_velocity_score",
        "min_learning_velocity_score",
        "max_workload_pressure",
    ):
        _require_canonical_ratio_decimal(field_name, getattr(report, field_name))
    if type(report.rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in report.rows:
        _revalidate_row_for_payload(row)
    if len({row.domain_key for row in report.rows}) != len(report.rows):
        raise ValueError("domain_key values must be unique")
    if tuple(sorted(report.rows, key=_row_sort_key)) != report.rows:
        raise ValueError("rows must be canonical")
    if type(report.feedback_config_versions) is not tuple:
        raise ValueError("feedback_config_versions must be a tuple")
    if (
        _normalize_feedback_config_versions(report.feedback_config_versions)
        != report.feedback_config_versions
    ):
        raise ValueError("feedback_config_versions must be canonical")
    if type(report.reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if _normalize_reason_codes(report.reason_codes) != report.reason_codes:
        raise ValueError("reason_codes must be canonical")
    if type(report.reason_code_counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for item in report.reason_code_counts:
        _revalidate_reason_code_count_for_payload(item)
    if _normalize_reason_code_counts(report.reason_code_counts) != report.reason_code_counts:
        raise ValueError("reason_code_counts must be canonical")
    if type(report.public_payload) is not tuple:
        raise ValueError("public_payload must be a tuple")
    for item in report.public_payload:
        _revalidate_public_payload_item_for_payload(item)
    if _normalize_public_payload(report.public_payload) != report.public_payload:
        raise ValueError("public_payload must be canonical")
    _require_sha256_digest(
        "derived_validation_digest",
        report.derived_validation_digest,
    )
    _validate_report_consistency(report)
    for row in report.rows:
        _require_untampered_public_dataclass(row, "row")
    for item in report.reason_code_counts:
        _require_untampered_public_dataclass(item, "reason code count")
    _require_hard_flags("report", report)
    _reject_unsafe_public_payload("report", report)
    _require_untampered_public_dataclass(report, "report")
    expected_digest = _report_digest_from_values(_report_values_without_digest(report))
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest does not match report payload")


def _revalidate_row_for_payload(row: object) -> None:
    if type(row) is not ResearchTeamSpecialistLearningVelocityDomainRow:
        raise ValueError(
            "rows must contain ResearchTeamSpecialistLearningVelocityDomainRow values",
        )
    _require_public_identifier("domain_key", row.domain_key)
    _require_anonymized_specialist_team_key(row.specialist_team_key)
    _require_public_identifier(
        "feedback_config_version",
        row.feedback_config_version,
    )
    _require_utc_datetime("observed_at", row.observed_at)
    _require_canonical_nonnegative_whole_decimal(
        "resolved_outcome_feedback_count",
        row.resolved_outcome_feedback_count,
    )
    _require_canonical_nonnegative_decimal(
        "memory_age_seconds",
        row.memory_age_seconds,
    )
    for field_name in (
        "resolved_feedback_depth_score",
        "correction_follow_through_rate",
        "memory_freshness_score",
        "calibration_drift",
        "calibration_stability_score",
        "workload_pressure",
        "workload_capacity_score",
        "learning_velocity_score",
    ):
        _require_canonical_ratio_decimal(field_name, getattr(row, field_name))
    _require_status("velocity_status", row.velocity_status)
    if type(row.reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if _normalize_reason_codes(row.reason_codes) != row.reason_codes:
        raise ValueError("reason_codes must be canonical")
    _validate_row_consistency(row)
    _require_hard_flags("row", row)
    _reject_unsafe_public_payload("row", row)


def _revalidate_public_payload_item_for_payload(item: object) -> None:
    if type(item) is not ResearchTeamSpecialistLearningVelocityPublicPayloadItem:
        raise ValueError(
            "public_payload items must be "
            "ResearchTeamSpecialistLearningVelocityPublicPayloadItem values",
        )
    _require_public_identifier("key", item.key)
    _require_public_text("value", item.value)
    _require_hard_flags("public payload item", item)
    _reject_unsafe_public_payload("public payload item", item)
    _require_untampered_public_dataclass(item, "public payload item")


def _revalidate_reason_code_count_for_payload(item: object) -> None:
    if type(item) is not ResearchTeamSpecialistLearningVelocityReasonCodeCount:
        raise ValueError(
            "reason_code_counts must contain "
            "ResearchTeamSpecialistLearningVelocityReasonCodeCount values",
        )
    _require_supported_reason_code("reason_code", item.reason_code)
    _require_canonical_nonnegative_whole_decimal("count", item.count)
    _require_hard_flags("reason code count", item)
    _reject_unsafe_public_payload("reason code count", item)


def _validate_public_payload_schema(payload: dict[str, object]) -> None:
    _require_exact_payload_keys(
        "report payload",
        payload,
        tuple(field.name for field in fields(ResearchTeamSpecialistLearningVelocityReport)),
    )
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("report payload rows must be a list")
    for index, row in enumerate(rows):
        if type(row) is not dict:
            raise ValueError("report payload rows must contain JSON objects")
        _require_exact_payload_keys(
            f"rows[{index}]",
            row,
            tuple(
                field.name
                for field in fields(ResearchTeamSpecialistLearningVelocityDomainRow)
            ),
        )
    feedback_config_versions = payload["feedback_config_versions"]
    if type(feedback_config_versions) is not list:
        raise ValueError("report payload feedback_config_versions must be a list")
    for value in feedback_config_versions:
        if (
            type(value) is not list
            or len(value) != 2
            or any(type(item) is not str for item in value)
        ):
            raise ValueError(
                "report payload feedback_config_versions must contain string pairs",
            )
    reason_code_counts = payload["reason_code_counts"]
    if type(reason_code_counts) is not list:
        raise ValueError("report payload reason_code_counts must be a list")
    for index, item in enumerate(reason_code_counts):
        if type(item) is not dict:
            raise ValueError("report payload reason_code_counts must contain JSON objects")
        _require_exact_payload_keys(
            f"reason_code_counts[{index}]",
            item,
            tuple(
                field.name
                for field in fields(
                    ResearchTeamSpecialistLearningVelocityReasonCodeCount,
                )
            ),
        )
    public_payload = payload["public_payload"]
    if type(public_payload) is not list:
        raise ValueError("report payload public_payload must be a list")
    for index, item in enumerate(public_payload):
        if type(item) is not dict:
            raise ValueError("report payload public_payload must contain JSON objects")
        _require_exact_payload_keys(
            f"public_payload[{index}]",
            item,
            tuple(
                field.name
                for field in fields(
                    ResearchTeamSpecialistLearningVelocityPublicPayloadItem,
                )
            ),
        )
    for flag_name in _PHASE_FLAG_FIELDS:
        if payload[flag_name] is not True:
            raise ValueError(f"{flag_name} must be True for report payload")


def _require_exact_payload_keys(
    label: str,
    payload: dict[str, object],
    expected_keys: tuple[str, ...],
) -> None:
    actual_keys = tuple(payload)
    if actual_keys == expected_keys:
        return
    if set(actual_keys) != set(expected_keys):
        raise ValueError(f"{label} schema must match expected fields")
    raise ValueError(f"{label} schema order must match expected fields")


def _report_reason_codes(
    rows: tuple[ResearchTeamSpecialistLearningVelocityDomainRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("specialist_learning_velocity_empty",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(
            reason_code
            for reason_code in row.reason_codes
            if reason_code != "specialist_learning_velocity_pass"
        )
    if not reason_codes:
        return ("specialist_learning_velocity_pass",)
    return _normalize_reason_codes(tuple(reason_codes))


def _reason_code_counts(
    rows: tuple[ResearchTeamSpecialistLearningVelocityDomainRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchTeamSpecialistLearningVelocityReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchTeamSpecialistLearningVelocityReasonCodeCount(
                reason_code="specialist_learning_velocity_empty",
                count=_decimal_count(1),
            ),
        )
    return tuple(
        ResearchTeamSpecialistLearningVelocityReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(
                sum(1 for row in rows if reason_code in row.reason_codes),
            ),
        )
        for reason_code in reason_codes
    )


def _status_count(
    rows: tuple[ResearchTeamSpecialistLearningVelocityDomainRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.velocity_status == status)


def _row_sort_key(
    row: ResearchTeamSpecialistLearningVelocityDomainRow,
) -> tuple[
    int,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    datetime,
    tuple[str, ...],
    str,
    str,
    str,
]:
    return (
        _STATUS_RANK[row.velocity_status],
        row.learning_velocity_score,
        row.resolved_feedback_depth_score,
        row.correction_follow_through_rate,
        row.memory_freshness_score,
        row.calibration_stability_score,
        row.workload_capacity_score,
        row.resolved_outcome_feedback_count,
        row.memory_age_seconds,
        row.calibration_drift,
        row.workload_pressure,
        row.observed_at,
        row.reason_codes,
        row.domain_key,
        row.specialist_team_key,
        row.feedback_config_version,
    )


def _require_exact_type(value: object, type_: type[object], label: str) -> None:
    if type(value) is not type_:
        raise ValueError(f"{label} must be exactly {type_.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    _reject_control_characters(field_name, value)
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _anonymize_specialist_team_key(value: object) -> str:
    if type(value) is not str:
        raise ValueError("specialist_team_key must be a string")
    if _ANONYMIZED_SPECIALIST_TEAM_KEY_RE.fullmatch(value):
        return value
    if value.strip() != value or not value:
        raise ValueError("specialist_team_key must be a non-empty private identifier")
    if len(value) > 512:
        raise ValueError("specialist_team_key must not exceed 512 characters")
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return f"anon_{digest}"


def _require_anonymized_specialist_team_key(value: object) -> str:
    if type(value) is not str or not _ANONYMIZED_SPECIALIST_TEAM_KEY_RE.fullmatch(value):
        raise ValueError("specialist_team_key must be anonymized with sha256")
    return value


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    _reject_control_characters(field_name, value)
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be non-empty public text")
    if len(value) > 512:
        raise ValueError(f"{field_name} must not exceed 512 characters")
    _reject_unsafe_public_string(field_name, value)
    return value


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    _reject_control_characters(field_name, value)
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered or "=" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


def _reject_control_characters(field_name: str, value: str) -> None:
    if any(ord(character) < 32 or 127 <= ord(character) <= 159 for character in value):
        raise ValueError(f"{field_name} contains control characters")


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_supported_reason_code(field_name: str, value: object) -> str:
    _require_public_identifier(field_name, value)
    if value not in _REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be supported")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not use signed zero")
    return value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    raw_value = _require_decimal(field_name, value)
    if raw_value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _require_six_decimal_places(field_name, raw_value)


def _require_nonnegative_whole_decimal(
    field_name: str,
    value: object,
) -> Decimal:
    raw_value = _require_decimal(field_name, value)
    if raw_value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(_DECIMAL_CONTEXT):
        if raw_value != raw_value.to_integral_value():
            raise ValueError(f"{field_name} must be a whole Decimal")
    return _require_six_decimal_places(field_name, raw_value)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    raw_value = _require_decimal(field_name, value)
    if raw_value < _ZERO or raw_value > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return _require_six_decimal_places(field_name, raw_value)


def _require_six_decimal_places(field_name: str, value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if value.as_tuple().exponent != _QUANT.as_tuple().exponent or value != normalized:
        raise ValueError(f"{field_name} must use six decimal places")
    return normalized


def _require_canonical_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal:
    normalized = _require_canonical_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_canonical_nonnegative_whole_decimal(
    field_name: str,
    value: object,
) -> Decimal:
    normalized = _require_canonical_nonnegative_decimal(field_name, value)
    with localcontext(_DECIMAL_CONTEXT):
        if normalized != normalized.to_integral_value():
            raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _require_canonical_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_canonical_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_canonical_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != _QUANT.as_tuple().exponent:
        raise ValueError(f"{field_name} must use six decimal places")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not use signed zero")
    return value


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _quantize(Decimal(value))


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _quantize(value: Decimal) -> Decimal:
    try:
        with localcontext(_DECIMAL_CONTEXT):
            normalized = value.quantize(_QUANT)
    except DecimalException as exc:
        raise ValueError("Decimal value exceeds supported range") from exc
    if normalized.is_zero():
        return _ZERO
    return normalized


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_identifier("reason_code", reason_code)
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in normalized
    )


def _store_public_snapshot(value: object) -> None:
    object.__setattr__(value, "_canonical_public_snapshot", _public_snapshot(value))


def _require_untampered_public_dataclass(value: object, label: str) -> None:
    expected = getattr(value, "_canonical_public_snapshot", None)
    if expected is None:
        raise ValueError(f"{label} canonical snapshot is missing")
    actual = _public_snapshot(value)
    if actual == expected:
        return
    for (field_name, expected_value), (_, actual_value) in zip(
        expected,
        actual,
        strict=True,
    ):
        if actual_value != expected_value:
            raise ValueError(f"{field_name} was modified after initialization")
    raise ValueError(f"{label} was modified after initialization")


def _public_snapshot(value: object) -> tuple[tuple[str, object], ...]:
    if not is_dataclass(value) or isinstance(value, type):
        raise ValueError("public snapshot requires a dataclass instance")
    return tuple(
        (field.name, _snapshot_ready(getattr(value, field.name)))
        for field in fields(value)
    )


def _snapshot_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return tuple(
            (field.name, _snapshot_ready(getattr(value, field.name)))
            for field in fields(value)
        )
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return value.isoformat()
    if type(value) is tuple:
        return tuple(_snapshot_ready(item) for item in value)
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_utc_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is not UTC:
        raise ValueError(f"{field_name} must use UTC")
    return value


def _report_values_without_digest(
    report: ResearchTeamSpecialistLearningVelocityReport,
) -> dict[str, object]:
    return {
        field.name: getattr(report, field.name)
        for field in fields(report)
        if field.name != "derived_validation_digest"
    }


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    if type(values) is not dict:
        raise ValueError("derived_validation_digest values must be a dict")
    expected_keys = tuple(
        field.name
        for field in fields(ResearchTeamSpecialistLearningVelocityReport)
        if field.name != "derived_validation_digest"
    )
    if tuple(values) != expected_keys:
        raise ValueError(
            "derived_validation_digest values must use the strict public schema",
        )
    payload = _json_ready(values)
    _reject_unsafe_public_payload(
        "derived_validation_digest payload",
        payload,
        allow_json_containers=True,
    )
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError("payload contains unknown dataclass")
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is Decimal:
        _require_canonical_decimal("Decimal payload value", value)
        return str(value)
    if type(value) is datetime:
        return _require_utc_datetime("datetime payload value", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    raise ValueError("payload value must use the strict public schema")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{current_path} contains unknown dataclass")
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        if type(value) is list and not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)
        return
    if value is None or type(value) is bool or type(value) is Decimal or type(value) is datetime:
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")


__all__ = (
    "DEFAULT_RESEARCH_TEAM_SPECIALIST_LEARNING_VELOCITY_CONFIG_VERSION",
    "ResearchTeamSpecialistLearningVelocityConfig",
    "ResearchTeamSpecialistLearningVelocityDomainFeedback",
    "ResearchTeamSpecialistLearningVelocityDomainRow",
    "ResearchTeamSpecialistLearningVelocityPublicPayloadItem",
    "ResearchTeamSpecialistLearningVelocityReasonCodeCount",
    "ResearchTeamSpecialistLearningVelocityReport",
    "build_research_team_specialist_learning_velocity_report",
    "research_team_specialist_learning_velocity_report_digest",
    "research_team_specialist_learning_velocity_report_payload",
    "validate_research_team_specialist_learning_velocity_report_payload",
)
