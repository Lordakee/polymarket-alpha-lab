"""Public-safe reducer for domain playbook revision impact."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, localcontext
from hashlib import sha256
import json
from typing import Any, Iterable


DEFAULT_RESEARCH_TEAM_DOMAIN_PLAYBOOK_REVISION_IMPACT_REPORT_CONFIG_VERSION = (
    "research-team-domain-playbook-revision-impact-report-v0"
)
RESEARCH_TEAM_DOMAIN_PLAYBOOK_REVISION_IMPACT_STATUSES = (
    "pass",
    "watch",
    "block",
)
RESEARCH_TEAM_DOMAIN_PLAYBOOK_REVISION_IMPACT_REASON_CODES = (
    "domain_playbook_revision_impact_empty",
    "domain_playbook_revision_impact_clear",
    "domain_playbook_revision_impact_block",
    "domain_playbook_revision_impact_watch",
    "calibration_delta_block",
    "evidence_reuse_delta_block",
    "review_latency_regression_block",
    "unresolved_blocker_pressure_block",
    "calibration_delta_watch",
    "evidence_reuse_delta_watch",
    "review_latency_regression_watch",
    "unresolved_blocker_pressure_watch",
)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_DOMAIN_PLAYBOOK_REVISION_IMPACT_REPORT_CONFIG_VERSION",
    "RESEARCH_TEAM_DOMAIN_PLAYBOOK_REVISION_IMPACT_STATUSES",
    "RESEARCH_TEAM_DOMAIN_PLAYBOOK_REVISION_IMPACT_REASON_CODES",
    "ResearchTeamDomainPlaybookRevisionImpactConfig",
    "ResearchTeamDomainPlaybookRevisionImpactInput",
    "ResearchTeamDomainPlaybookRevisionImpactReport",
    "ResearchTeamDomainPlaybookRevisionImpactRow",
    "build_research_team_domain_playbook_revision_impact_report",
    "research_team_domain_playbook_revision_impact_report_payload",
)

_DIGEST_FIELD = "derived_validation_digest"
_COUNT_QUANTUM = Decimal("1")
_SIX_PLACE_QUANTUM = Decimal("0.000001")
_ZERO_COUNT = Decimal("0")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_NEGATIVE_ONE = Decimal("-1.000000")
_DECIMAL_CONTEXT = Context(prec=64)
_STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
_REPORT_REASON_SEQUENCE = (
    "domain_playbook_revision_impact_block",
    "domain_playbook_revision_impact_watch",
    "domain_playbook_revision_impact_clear",
    "calibration_delta_block",
    "evidence_reuse_delta_block",
    "review_latency_regression_block",
    "unresolved_blocker_pressure_block",
    "calibration_delta_watch",
    "evidence_reuse_delta_watch",
    "review_latency_regression_watch",
    "unresolved_blocker_pressure_watch",
    "domain_playbook_revision_impact_empty",
)
_ROW_REASON_SEQUENCE = (
    "calibration_delta_block",
    "evidence_reuse_delta_block",
    "review_latency_regression_block",
    "unresolved_blocker_pressure_block",
    "calibration_delta_watch",
    "evidence_reuse_delta_watch",
    "review_latency_regression_watch",
    "unresolved_blocker_pressure_watch",
    "domain_playbook_revision_impact_clear",
)
_UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate",
    "market",
    "slug",
    "ques" "tion",
    "source",
    "url",
    "dsn",
    "table",
    "tok" "en",
    "wal" "let",
    "acc" "ount",
    "or" "der",
    "tr" "ade",
    "li" "ve",
    "reco" "mmend",
    "siz" "ing",
    "au" "th",
    "net" "work",
    "private",
    "sec" "ret",
    "key",
)
_HEX_CHARS = frozenset("0123456789abcdef")


@dataclass(frozen=True)
class ResearchTeamDomainPlaybookRevisionImpactConfig:
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_DOMAIN_PLAYBOOK_REVISION_IMPACT_REPORT_CONFIG_VERSION
    )
    calibration_delta_block_floor: Decimal = Decimal("-0.050000")
    calibration_delta_watch_floor: Decimal = Decimal("0.000000")
    evidence_reuse_delta_block_floor: Decimal = Decimal("-0.100000")
    evidence_reuse_delta_watch_floor: Decimal = Decimal("0.000000")
    review_latency_watch_increase_seconds: Decimal = Decimal("900.000000")
    review_latency_block_increase_seconds: Decimal = Decimal("3600.000000")
    blocker_pressure_watch_ratio: Decimal = Decimal("0.250000")
    blocker_pressure_block_ratio: Decimal = Decimal("0.500000")
    pass_impact_pressure_ceiling: Decimal = Decimal("0.150000")
    watch_impact_pressure_ceiling: Decimal = Decimal("0.500000")
    calibration_delta_weight: Decimal = Decimal("0.300000")
    evidence_reuse_weight: Decimal = Decimal("0.250000")
    review_latency_weight: Decimal = Decimal("0.200000")
    unresolved_blocker_weight: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchTeamDomainPlaybookRevisionImpactConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("config", self, ResearchTeamDomainPlaybookRevisionImpactConfig)
        _require_safe_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_DOMAIN_PLAYBOOK_REVISION_IMPACT_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "calibration_delta_block_floor",
            "calibration_delta_watch_floor",
            "evidence_reuse_delta_block_floor",
            "evidence_reuse_delta_watch_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_signed_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "blocker_pressure_watch_ratio",
            "blocker_pressure_block_ratio",
            "pass_impact_pressure_ceiling",
            "watch_impact_pressure_ceiling",
            "calibration_delta_weight",
            "evidence_reuse_weight",
            "review_latency_weight",
            "unresolved_blocker_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "review_latency_watch_increase_seconds",
            "review_latency_block_increase_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.calibration_delta_block_floor >= self.calibration_delta_watch_floor:
            raise ValueError("calibration_delta_block_floor must be less than watch floor")
        if self.evidence_reuse_delta_block_floor >= self.evidence_reuse_delta_watch_floor:
            raise ValueError("evidence_reuse_delta_block_floor must be less than watch floor")
        if (
            self.review_latency_block_increase_seconds
            <= self.review_latency_watch_increase_seconds
        ):
            raise ValueError(
                "review_latency_block_increase_seconds must exceed watch increase",
            )
        if self.blocker_pressure_block_ratio <= self.blocker_pressure_watch_ratio:
            raise ValueError("blocker_pressure_block_ratio must exceed watch ratio")
        if self.pass_impact_pressure_ceiling > self.watch_impact_pressure_ceiling:
            raise ValueError(
                "pass_impact_pressure_ceiling must not exceed watch ceiling",
            )
        if _six(
            self.calibration_delta_weight
            + self.evidence_reuse_weight
            + self.review_latency_weight
            + self.unresolved_blocker_weight,
        ) != _ONE:
            raise ValueError("revision impact weights must sum to 1")
        _require_hard_flags("config", self)
        _reject_unsafe_public_surface("config", self)


@dataclass(frozen=True)
class ResearchTeamDomainPlaybookRevisionImpactInput:
    revision_ref: str
    team_label: str
    domain_label: str
    observed_at: datetime
    pre_calibration_score: Decimal
    post_calibration_score: Decimal
    pre_evidence_reuse_ratio: Decimal
    post_evidence_reuse_ratio: Decimal
    pre_review_latency_seconds: Decimal
    post_review_latency_seconds: Decimal
    unresolved_blocker_count: Decimal
    total_blocker_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchTeamDomainPlaybookRevisionImpactInput does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("input", self, ResearchTeamDomainPlaybookRevisionImpactInput)
        for field_name in ("revision_ref", "team_label", "domain_label"):
            _require_safe_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "pre_calibration_score",
            "post_calibration_score",
            "pre_evidence_reuse_ratio",
            "post_evidence_reuse_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "pre_review_latency_seconds",
            "post_review_latency_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("unresolved_blocker_count", "total_blocker_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.total_blocker_count <= _ZERO_COUNT:
            raise ValueError("total_blocker_count must be positive")
        if self.unresolved_blocker_count > self.total_blocker_count:
            raise ValueError("unresolved_blocker_count must not exceed total_blocker_count")
        _require_hard_flags("input", self)
        _reject_unsafe_public_surface("input", self)


@dataclass(frozen=True)
class ResearchTeamDomainPlaybookRevisionImpactRow:
    revision_ref_digest: str
    team_label: str
    domain_label: str
    observed_at: datetime
    pre_calibration_score: Decimal
    post_calibration_score: Decimal
    calibration_delta: Decimal
    pre_evidence_reuse_ratio: Decimal
    post_evidence_reuse_ratio: Decimal
    evidence_reuse_delta: Decimal
    pre_review_latency_seconds: Decimal
    post_review_latency_seconds: Decimal
    review_latency_change_seconds: Decimal
    unresolved_blocker_count: Decimal
    total_blocker_count: Decimal
    unresolved_blocker_pressure: Decimal
    impact_pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchTeamDomainPlaybookRevisionImpactRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchTeamDomainPlaybookRevisionImpactRow)
        _require_redacted_digest("revision_ref_digest", self.revision_ref_digest)
        for field_name in ("team_label", "domain_label"):
            _require_safe_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "pre_calibration_score",
            "post_calibration_score",
            "pre_evidence_reuse_ratio",
            "post_evidence_reuse_ratio",
            "unresolved_blocker_pressure",
            "impact_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("calibration_delta", "evidence_reuse_delta"):
            object.__setattr__(
                self,
                field_name,
                _normalize_signed_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "pre_review_latency_seconds",
            "post_review_latency_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "review_latency_change_seconds",
            _normalize_signed_decimal(
                "review_latency_change_seconds",
                self.review_latency_change_seconds,
            ),
        )
        for field_name in ("unresolved_blocker_count", "total_blocker_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.total_blocker_count <= _ZERO_COUNT:
            raise ValueError("total_blocker_count must be positive")
        if self.unresolved_blocker_count > self.total_blocker_count:
            raise ValueError("unresolved_blocker_count must not exceed total_blocker_count")
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _require_hard_flags("row", self)
        expected_digest = _digest_value(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match row fields")
        _validate_row_metrics(self)
        _reject_unsafe_public_surface("row", self)


@dataclass(frozen=True)
class ResearchTeamDomainPlaybookRevisionImpactReport:
    generated_at: datetime
    config_version: str
    revision_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    positive_calibration_delta_count: Decimal
    negative_calibration_delta_count: Decimal
    positive_evidence_reuse_delta_count: Decimal
    negative_evidence_reuse_delta_count: Decimal
    review_latency_improved_count: Decimal
    review_latency_regressed_count: Decimal
    unresolved_blocker_pressure_count: Decimal
    average_calibration_delta: Decimal
    average_evidence_reuse_delta: Decimal
    average_review_latency_change_seconds: Decimal
    average_unresolved_blocker_pressure: Decimal
    max_impact_pressure_score: Decimal
    average_impact_pressure_score: Decimal
    status: str
    rows: tuple[ResearchTeamDomainPlaybookRevisionImpactRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchTeamDomainPlaybookRevisionImpactReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchTeamDomainPlaybookRevisionImpactReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_safe_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_DOMAIN_PLAYBOOK_REVISION_IMPACT_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "revision_count",
            "pass_count",
            "watch_count",
            "block_count",
            "positive_calibration_delta_count",
            "negative_calibration_delta_count",
            "positive_evidence_reuse_delta_count",
            "negative_evidence_reuse_delta_count",
            "review_latency_improved_count",
            "review_latency_regressed_count",
            "unresolved_blocker_pressure_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_calibration_delta",
            "average_evidence_reuse_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_signed_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_review_latency_change_seconds",
            _normalize_signed_decimal(
                "average_review_latency_change_seconds",
                self.average_review_latency_change_seconds,
            ),
        )
        for field_name in (
            "average_unresolved_blocker_pressure",
            "max_impact_pressure_score",
            "average_impact_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _require_hard_flags("report", self)
        expected_digest = _digest_value(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report fields")
        _validate_report_metrics(self)
        _reject_unsafe_public_surface("report", self.public_payload)

    @property
    def public_payload(self) -> dict[str, Any]:
        _validate_report_digest(self)
        payload = _payload_value(self)
        if type(payload) is not dict:
            raise ValueError("public_payload must be a JSON object")
        _reject_unsafe_public_surface("public_payload", payload)
        _reject_non_string_numeric(payload)
        _validate_payload_digest(payload)
        return payload


def build_research_team_domain_playbook_revision_impact_report(
    revisions: Iterable[ResearchTeamDomainPlaybookRevisionImpactInput],
    *,
    config: ResearchTeamDomainPlaybookRevisionImpactConfig | None = None,
    generated_at: datetime,
) -> ResearchTeamDomainPlaybookRevisionImpactReport:
    if config is None:
        config = ResearchTeamDomainPlaybookRevisionImpactConfig()
    if type(config) is not ResearchTeamDomainPlaybookRevisionImpactConfig:
        raise ValueError("config must be a revision impact config")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    items = _normalize_inputs(revisions)
    for item in items:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must be on or before generated_at")
    rows = tuple(
        sorted(
            (_row_from_input(item, config) for item in items),
            key=_row_sort_key,
        ),
    )
    return ResearchTeamDomainPlaybookRevisionImpactReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        revision_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        positive_calibration_delta_count=_comparison_count(
            tuple(row.calibration_delta for row in rows),
            above_zero=True,
        ),
        negative_calibration_delta_count=_comparison_count(
            tuple(row.calibration_delta for row in rows),
            above_zero=False,
        ),
        positive_evidence_reuse_delta_count=_comparison_count(
            tuple(row.evidence_reuse_delta for row in rows),
            above_zero=True,
        ),
        negative_evidence_reuse_delta_count=_comparison_count(
            tuple(row.evidence_reuse_delta for row in rows),
            above_zero=False,
        ),
        review_latency_improved_count=_comparison_count(
            tuple(row.review_latency_change_seconds for row in rows),
            above_zero=False,
        ),
        review_latency_regressed_count=_comparison_count(
            tuple(row.review_latency_change_seconds for row in rows),
            above_zero=True,
        ),
        unresolved_blocker_pressure_count=_count(
            sum(row.unresolved_blocker_pressure > _ZERO for row in rows),
        ),
        average_calibration_delta=_average_decimal(
            tuple(row.calibration_delta for row in rows),
        ),
        average_evidence_reuse_delta=_average_decimal(
            tuple(row.evidence_reuse_delta for row in rows),
        ),
        average_review_latency_change_seconds=_average_decimal(
            tuple(row.review_latency_change_seconds for row in rows),
        ),
        average_unresolved_blocker_pressure=_average_ratio(
            tuple(row.unresolved_blocker_pressure for row in rows),
        ),
        max_impact_pressure_score=_max_ratio(
            tuple(row.impact_pressure_score for row in rows),
        ),
        average_impact_pressure_score=_average_ratio(
            tuple(row.impact_pressure_score for row in rows),
        ),
        status=_report_status(rows),
        rows=rows,
        reason_codes=_report_reason_codes(rows),
    )


def research_team_domain_playbook_revision_impact_report_payload(
    report: ResearchTeamDomainPlaybookRevisionImpactReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is dict:
        _reject_unsafe_public_surface("revision impact payload", report)
        _require_payload_hard_flags(report)
        _reject_non_string_numeric(report)
        _validate_payload_schema(report)
        _validate_payload_digest(report)
        return report
    if type(report) is not ResearchTeamDomainPlaybookRevisionImpactReport:
        raise ValueError("report must be a revision impact report or payload dict")
    _require_hard_flags("report", report)
    _validate_report_digest(report)
    return report.public_payload


def _validate_payload_schema(payload: dict[str, Any]) -> None:
    _require_payload_schema(
        "public report",
        payload,
        ResearchTeamDomainPlaybookRevisionImpactReport,
    )
    rows_value = payload["rows"]
    if type(rows_value) is not list:
        raise ValueError("public report schema requires rows to be a list")
    rows = tuple(
        _row_from_public_payload(row, index)
        for index, row in enumerate(rows_value, start=1)
    )
    decimal_fields = (
        "revision_count",
        "pass_count",
        "watch_count",
        "block_count",
        "positive_calibration_delta_count",
        "negative_calibration_delta_count",
        "positive_evidence_reuse_delta_count",
        "negative_evidence_reuse_delta_count",
        "review_latency_improved_count",
        "review_latency_regressed_count",
        "unresolved_blocker_pressure_count",
        "average_calibration_delta",
        "average_evidence_reuse_delta",
        "average_review_latency_change_seconds",
        "average_unresolved_blocker_pressure",
        "max_impact_pressure_score",
        "average_impact_pressure_score",
    )
    rebuilt = ResearchTeamDomainPlaybookRevisionImpactReport(
        generated_at=_datetime_from_public_payload(
            "generated_at",
            payload["generated_at"],
        ),
        config_version=_string_from_public_payload(
            "config_version",
            payload["config_version"],
        ),
        **{
            field_name: _decimal_from_public_payload(
                field_name,
                payload[field_name],
            )
            for field_name in decimal_fields
        },
        status=_string_from_public_payload("status", payload["status"]),
        rows=rows,
        reason_codes=_string_tuple_from_public_payload(
            "reason_codes",
            payload["reason_codes"],
        ),
        derived_validation_digest=_string_from_public_payload(
            _DIGEST_FIELD,
            payload[_DIGEST_FIELD],
        ),
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )
    if _payload_value(rebuilt) != payload:
        raise ValueError("public report schema must use canonical values")


def _row_from_public_payload(
    value: object,
    index: int,
) -> ResearchTeamDomainPlaybookRevisionImpactRow:
    label = f"public row {index}"
    if type(value) is not dict:
        raise ValueError(f"{label} schema must be an object")
    _require_payload_schema(
        label,
        value,
        ResearchTeamDomainPlaybookRevisionImpactRow,
    )
    decimal_fields = (
        "pre_calibration_score",
        "post_calibration_score",
        "calibration_delta",
        "pre_evidence_reuse_ratio",
        "post_evidence_reuse_ratio",
        "evidence_reuse_delta",
        "pre_review_latency_seconds",
        "post_review_latency_seconds",
        "review_latency_change_seconds",
        "unresolved_blocker_count",
        "total_blocker_count",
        "unresolved_blocker_pressure",
        "impact_pressure_score",
    )
    return ResearchTeamDomainPlaybookRevisionImpactRow(
        revision_ref_digest=_string_from_public_payload(
            f"{label} revision_ref_digest",
            value["revision_ref_digest"],
        ),
        team_label=_string_from_public_payload(
            f"{label} team_label",
            value["team_label"],
        ),
        domain_label=_string_from_public_payload(
            f"{label} domain_label",
            value["domain_label"],
        ),
        observed_at=_datetime_from_public_payload(
            f"{label} observed_at",
            value["observed_at"],
        ),
        **{
            field_name: _decimal_from_public_payload(
                f"{label} {field_name}",
                value[field_name],
            )
            for field_name in decimal_fields
        },
        status=_string_from_public_payload(
            f"{label} status",
            value["status"],
        ),
        reason_codes=_string_tuple_from_public_payload(
            f"{label} reason_codes",
            value["reason_codes"],
        ),
        derived_validation_digest=_string_from_public_payload(
            f"{label} {_DIGEST_FIELD}",
            value[_DIGEST_FIELD],
        ),
        paper_only=value["paper_only"],
        report_only=value["report_only"],
        readonly=value["readonly"],
    )


def _require_payload_schema(
    label: str,
    payload: dict[str, Any],
    expected_type: type[object],
) -> None:
    expected_fields = frozenset(field.name for field in fields(expected_type))
    if frozenset(payload) != expected_fields:
        raise ValueError(f"{label} schema must match")


def _string_from_public_payload(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _decimal_from_public_payload(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a decimal string")
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a decimal string") from exc


def _datetime_from_public_payload(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a datetime string")
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a datetime string") from exc


def _string_tuple_from_public_payload(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} schema must be a list")
    if any(type(item) is not str for item in value):
        raise ValueError(f"{field_name} must contain strings")
    return tuple(value)


def _row_from_input(
    item: ResearchTeamDomainPlaybookRevisionImpactInput,
    config: ResearchTeamDomainPlaybookRevisionImpactConfig,
) -> ResearchTeamDomainPlaybookRevisionImpactRow:
    calibration_delta = _signed_ratio(
        item.post_calibration_score - item.pre_calibration_score,
    )
    evidence_delta = _signed_ratio(
        item.post_evidence_reuse_ratio - item.pre_evidence_reuse_ratio,
    )
    review_latency_change = _six(
        item.post_review_latency_seconds - item.pre_review_latency_seconds,
    )
    blocker_pressure = _ratio(item.unresolved_blocker_count, item.total_blocker_count)
    impact_pressure_score = _impact_pressure_score(
        calibration_delta=calibration_delta,
        evidence_delta=evidence_delta,
        review_latency_change=review_latency_change,
        blocker_pressure=blocker_pressure,
        config=config,
    )
    status = _row_status(impact_pressure_score, config)
    return ResearchTeamDomainPlaybookRevisionImpactRow(
        revision_ref_digest=_redacted_digest(item.revision_ref),
        team_label=item.team_label,
        domain_label=item.domain_label,
        observed_at=item.observed_at,
        pre_calibration_score=item.pre_calibration_score,
        post_calibration_score=item.post_calibration_score,
        calibration_delta=calibration_delta,
        pre_evidence_reuse_ratio=item.pre_evidence_reuse_ratio,
        post_evidence_reuse_ratio=item.post_evidence_reuse_ratio,
        evidence_reuse_delta=evidence_delta,
        pre_review_latency_seconds=item.pre_review_latency_seconds,
        post_review_latency_seconds=item.post_review_latency_seconds,
        review_latency_change_seconds=review_latency_change,
        unresolved_blocker_count=item.unresolved_blocker_count,
        total_blocker_count=item.total_blocker_count,
        unresolved_blocker_pressure=blocker_pressure,
        impact_pressure_score=impact_pressure_score,
        status=status,
        reason_codes=_row_reason_codes(
            status=status,
            calibration_delta=calibration_delta,
            evidence_delta=evidence_delta,
            review_latency_change=review_latency_change,
            blocker_pressure=blocker_pressure,
            config=config,
        ),
    )


def _impact_pressure_score(
    *,
    calibration_delta: Decimal,
    evidence_delta: Decimal,
    review_latency_change: Decimal,
    blocker_pressure: Decimal,
    config: ResearchTeamDomainPlaybookRevisionImpactConfig,
) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return _ratio_clamp(
            _negative_delta_pressure(
                calibration_delta,
                config.calibration_delta_block_floor,
                config.calibration_delta_watch_floor,
            )
            * config.calibration_delta_weight
            + _negative_delta_pressure(
                evidence_delta,
                config.evidence_reuse_delta_block_floor,
                config.evidence_reuse_delta_watch_floor,
            )
            * config.evidence_reuse_weight
            + _positive_change_pressure(
                review_latency_change,
                config.review_latency_block_increase_seconds,
            )
            * config.review_latency_weight
            + _ratio_clamp(blocker_pressure / config.blocker_pressure_block_ratio)
            * config.unresolved_blocker_weight,
        )


def _negative_delta_pressure(
    delta: Decimal,
    block_floor: Decimal,
    watch_floor: Decimal,
) -> Decimal:
    if delta >= watch_floor:
        return _ZERO
    if delta <= block_floor:
        return _ONE
    with localcontext(_DECIMAL_CONTEXT):
        return _ratio_clamp((watch_floor - delta) / (watch_floor - block_floor))


def _positive_change_pressure(change: Decimal, block_increase: Decimal) -> Decimal:
    if change <= _ZERO:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _ratio_clamp(change / block_increase)


def _row_reason_codes(
    *,
    status: str,
    calibration_delta: Decimal,
    evidence_delta: Decimal,
    review_latency_change: Decimal,
    blocker_pressure: Decimal,
    config: ResearchTeamDomainPlaybookRevisionImpactConfig,
) -> tuple[str, ...]:
    if status == "pass":
        return ("domain_playbook_revision_impact_clear",)
    reasons: list[str] = []
    if calibration_delta <= config.calibration_delta_block_floor:
        reasons.append("calibration_delta_block")
    elif calibration_delta < config.calibration_delta_watch_floor:
        reasons.append("calibration_delta_watch")
    if evidence_delta <= config.evidence_reuse_delta_block_floor:
        reasons.append("evidence_reuse_delta_block")
    elif evidence_delta < config.evidence_reuse_delta_watch_floor:
        reasons.append("evidence_reuse_delta_watch")
    if review_latency_change >= config.review_latency_block_increase_seconds:
        reasons.append("review_latency_regression_block")
    elif review_latency_change >= config.review_latency_watch_increase_seconds:
        reasons.append("review_latency_regression_watch")
    if blocker_pressure >= config.blocker_pressure_block_ratio:
        reasons.append("unresolved_blocker_pressure_block")
    elif blocker_pressure >= config.blocker_pressure_watch_ratio:
        reasons.append("unresolved_blocker_pressure_watch")
    return tuple(reason for reason in _ROW_REASON_SEQUENCE if reason in reasons)


def _row_status(
    impact_pressure_score: Decimal,
    config: ResearchTeamDomainPlaybookRevisionImpactConfig,
) -> str:
    if impact_pressure_score <= config.pass_impact_pressure_ceiling:
        return "pass"
    if impact_pressure_score <= config.watch_impact_pressure_ceiling:
        return "watch"
    return "block"


def _report_status(rows: tuple[ResearchTeamDomainPlaybookRevisionImpactRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTeamDomainPlaybookRevisionImpactRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("domain_playbook_revision_impact_empty",)
    reasons: set[str] = set()
    if any(row.status == "block" for row in rows):
        reasons.add("domain_playbook_revision_impact_block")
    if any(row.status == "watch" for row in rows):
        reasons.add("domain_playbook_revision_impact_watch")
    if not reasons:
        reasons.add("domain_playbook_revision_impact_clear")
    for row in rows:
        reasons.update(row.reason_codes)
    reasons.discard("domain_playbook_revision_impact_clear")
    if not any(row.status != "pass" for row in rows):
        reasons.add("domain_playbook_revision_impact_clear")
    return tuple(reason for reason in _REPORT_REASON_SEQUENCE if reason in reasons)


def _row_sort_key(
    row: ResearchTeamDomainPlaybookRevisionImpactRow,
) -> tuple[Decimal, Decimal, str, str, str]:
    return (
        Decimal(_STATUS_RANK[row.status]),
        -row.impact_pressure_score,
        row.team_label,
        row.domain_label,
        row.revision_ref_digest,
    )


def _normalize_inputs(
    revisions: Iterable[ResearchTeamDomainPlaybookRevisionImpactInput],
) -> tuple[ResearchTeamDomainPlaybookRevisionImpactInput, ...]:
    if isinstance(revisions, (str, bytes)):
        raise ValueError("revisions must be an iterable")
    normalized = tuple(revisions)
    seen: set[str] = set()
    for item in normalized:
        if type(item) is not ResearchTeamDomainPlaybookRevisionImpactInput:
            raise ValueError("revisions must contain revision impact inputs")
        _require_hard_flags("input", item)
        if item.revision_ref in seen:
            raise ValueError("revision_ref values must be unique")
        seen.add(item.revision_ref)
    return normalized


def _normalize_rows(
    rows: object,
) -> tuple[ResearchTeamDomainPlaybookRevisionImpactRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchTeamDomainPlaybookRevisionImpactRow:
            raise ValueError("rows must contain revision impact rows")
        _require_hard_flags("row", row)
        if row.revision_ref_digest in seen:
            raise ValueError("rows must have unique revision digests")
        seen.add(row.revision_ref_digest)
    return normalized


def _validate_row_metrics(row: ResearchTeamDomainPlaybookRevisionImpactRow) -> None:
    if row.calibration_delta != _signed_ratio(
        row.post_calibration_score - row.pre_calibration_score,
    ):
        raise ValueError("calibration_delta must match pre and post calibration")
    if row.evidence_reuse_delta != _signed_ratio(
        row.post_evidence_reuse_ratio - row.pre_evidence_reuse_ratio,
    ):
        raise ValueError("evidence_reuse_delta must match pre and post evidence reuse")
    if row.review_latency_change_seconds != _six(
        row.post_review_latency_seconds - row.pre_review_latency_seconds,
    ):
        raise ValueError("review_latency_change_seconds must match pre and post latency")
    if row.unresolved_blocker_pressure != _ratio(
        row.unresolved_blocker_count,
        row.total_blocker_count,
    ):
        raise ValueError("unresolved_blocker_pressure must match blocker counts")


def _validate_report_metrics(report: ResearchTeamDomainPlaybookRevisionImpactReport) -> None:
    rows = report.rows
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted by status and impact pressure")
    if report.revision_count != _count(len(rows)):
        raise ValueError("revision_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.positive_calibration_delta_count != _comparison_count(
        tuple(row.calibration_delta for row in rows),
        above_zero=True,
    ):
        raise ValueError("positive_calibration_delta_count must match rows")
    if report.negative_calibration_delta_count != _comparison_count(
        tuple(row.calibration_delta for row in rows),
        above_zero=False,
    ):
        raise ValueError("negative_calibration_delta_count must match rows")
    if report.positive_evidence_reuse_delta_count != _comparison_count(
        tuple(row.evidence_reuse_delta for row in rows),
        above_zero=True,
    ):
        raise ValueError("positive_evidence_reuse_delta_count must match rows")
    if report.negative_evidence_reuse_delta_count != _comparison_count(
        tuple(row.evidence_reuse_delta for row in rows),
        above_zero=False,
    ):
        raise ValueError("negative_evidence_reuse_delta_count must match rows")
    if report.review_latency_improved_count != _comparison_count(
        tuple(row.review_latency_change_seconds for row in rows),
        above_zero=False,
    ):
        raise ValueError("review_latency_improved_count must match rows")
    if report.review_latency_regressed_count != _comparison_count(
        tuple(row.review_latency_change_seconds for row in rows),
        above_zero=True,
    ):
        raise ValueError("review_latency_regressed_count must match rows")
    if report.unresolved_blocker_pressure_count != _count(
        sum(row.unresolved_blocker_pressure > _ZERO for row in rows),
    ):
        raise ValueError("unresolved_blocker_pressure_count must match rows")
    if report.average_calibration_delta != _average_decimal(
        tuple(row.calibration_delta for row in rows),
    ):
        raise ValueError("average_calibration_delta must match rows")
    if report.average_evidence_reuse_delta != _average_decimal(
        tuple(row.evidence_reuse_delta for row in rows),
    ):
        raise ValueError("average_evidence_reuse_delta must match rows")
    if report.average_review_latency_change_seconds != _average_decimal(
        tuple(row.review_latency_change_seconds for row in rows),
    ):
        raise ValueError("average_review_latency_change_seconds must match rows")
    if report.average_unresolved_blocker_pressure != _average_ratio(
        tuple(row.unresolved_blocker_pressure for row in rows),
    ):
        raise ValueError("average_unresolved_blocker_pressure must match rows")
    if report.max_impact_pressure_score != _max_ratio(
        tuple(row.impact_pressure_score for row in rows),
    ):
        raise ValueError("max_impact_pressure_score must match rows")
    if report.average_impact_pressure_score != _average_ratio(
        tuple(row.impact_pressure_score for row in rows),
    ):
        raise ValueError("average_impact_pressure_score must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _status_count(
    rows: tuple[ResearchTeamDomainPlaybookRevisionImpactRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(row.status == status for row in rows))


def _comparison_count(values: tuple[Decimal, ...], *, above_zero: bool) -> Decimal:
    if above_zero:
        return _count(sum(value > _ZERO for value in values))
    return _count(sum(value < _ZERO for value in values))


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _six(sum(values, _ZERO) / Decimal(len(values)))


def _average_ratio(values: tuple[Decimal, ...]) -> Decimal:
    return _ratio_clamp(_average_decimal(values))


def _max_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _ratio_clamp(max(values))


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(_COUNT_QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= _ZERO_COUNT:
        raise ValueError("ratio denominator must be positive")
    with localcontext(_DECIMAL_CONTEXT):
        return _ratio_clamp(numerator / denominator)


def _ratio_clamp(value: Decimal) -> Decimal:
    normalized = _six(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _signed_ratio(value: Decimal) -> Decimal:
    normalized = _six(value)
    if normalized < _NEGATIVE_ONE:
        return _NEGATIVE_ONE
    if normalized > _ONE:
        return _ONE
    return normalized


def _six(value: Decimal) -> Decimal:
    return value.quantize(_SIX_PLACE_QUANTUM)


def _normalize_ratio_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value > _ONE:
        raise ValueError(f"{field_name} must not exceed one")
    if value != value.quantize(_SIX_PLACE_QUANTUM):
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return value.quantize(_SIX_PLACE_QUANTUM)


def _normalize_signed_ratio_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < _NEGATIVE_ONE:
        raise ValueError(f"{field_name} must be at least negative one")
    if value > _ONE:
        raise ValueError(f"{field_name} must not exceed one")
    if value != value.quantize(_SIX_PLACE_QUANTUM):
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return value.quantize(_SIX_PLACE_QUANTUM)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.quantize(_SIX_PLACE_QUANTUM):
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return value.quantize(_SIX_PLACE_QUANTUM)


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_signed_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value != value.quantize(_SIX_PLACE_QUANTUM):
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return value.quantize(_SIX_PLACE_QUANTUM)


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < _ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.quantize(_COUNT_QUANTUM):
        raise ValueError(f"{field_name} must be a whole Decimal")
    return value.quantize(_COUNT_QUANTUM)


def _normalize_reason_codes(value: object, *, require_nonempty: bool) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    normalized = tuple(value)
    if require_nonempty and not normalized:
        raise ValueError("reason_codes must not be empty")
    for reason_code in normalized:
        _require_reason_code(reason_code)
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    ordered = tuple(
        reason
        for reason in RESEARCH_TEAM_DOMAIN_PLAYBOOK_REVISION_IMPACT_REASON_CODES
        if reason in normalized
    )
    if ordered != normalized:
        raise ValueError("reason_codes must be deterministic")
    return normalized


def _require_reason_code(value: object) -> None:
    _require_safe_public_string("reason_code", value)
    if value not in RESEARCH_TEAM_DOMAIN_PLAYBOOK_REVISION_IMPACT_REASON_CODES:
        raise ValueError("reason_codes must contain known values")


def _require_status(field_name: str, value: object) -> None:
    _require_safe_public_string(field_name, value)
    if value not in RESEARCH_TEAM_DOMAIN_PLAYBOOK_REVISION_IMPACT_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_safe_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a safe public string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a safe public string")
    _reject_unsafe_text(value)


def _require_redacted_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a redacted digest")
    if not value.startswith("sha256:"):
        raise ValueError(f"{field_name} must be a redacted digest")
    digest = value.removeprefix("sha256:")
    if len(digest) != 64 or any(character not in _HEX_CHARS for character in digest):
        raise ValueError(f"{field_name} must be a redacted digest")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if len(value) != 64 or any(character not in _HEX_CHARS for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_exact_type(label: str, value: object, expected: type[object]) -> None:
    if type(value) is not expected:
        raise ValueError(f"{label} must be {expected.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _require_payload_hard_flags(payload: dict[str, Any]) -> None:
    if payload.get("paper_only") is not True:
        raise ValueError("payload paper_only must be True")
    if payload.get("report_only") is not True:
        raise ValueError("payload report_only must be True")
    if payload.get("readonly") is not True:
        raise ValueError("payload readonly must be True")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _redacted_digest(value: str) -> str:
    return "sha256:" + sha256(value.encode("utf-8")).hexdigest()


def _validate_report_digest(
    report: ResearchTeamDomainPlaybookRevisionImpactReport,
) -> None:
    _require_digest(_DIGEST_FIELD, report.derived_validation_digest)
    if report.derived_validation_digest != _digest_value(report):
        raise ValueError("derived_validation_digest must match report fields")
    for row in report.rows:
        _require_digest(_DIGEST_FIELD, row.derived_validation_digest)
        if row.derived_validation_digest != _digest_value(row):
            raise ValueError("derived_validation_digest must match row fields")


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get(_DIGEST_FIELD)
    _require_digest(_DIGEST_FIELD, digest)
    rows = payload.get("rows", ())
    if type(rows) not in (list, tuple):
        raise ValueError("payload rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("payload rows must contain objects")
        row_digest = row.get(_DIGEST_FIELD)
        _require_digest(_DIGEST_FIELD, row_digest)
        if row_digest != _digest_public(row):
            raise ValueError("derived_validation_digest must match row fields")
    if digest != _digest_public(payload):
        raise ValueError("derived_validation_digest must match report fields")


def _digest_value(value: object) -> str:
    payload = _payload_value(value)
    if type(payload) is not dict:
        raise ValueError("digest value must reduce to a dict")
    return _digest_public(payload)


def _digest_public(payload: dict[str, Any]) -> str:
    digest_payload = _digest_payload(payload)
    encoded = json.dumps(
        digest_payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _digest_payload(value: object) -> object:
    if type(value) is dict:
        return {
            key: _digest_payload(item)
            for key, item in value.items()
            if key != _DIGEST_FIELD
        }
    if type(value) in (list, tuple):
        return [_digest_payload(item) for item in value]
    return value


def _payload_value(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is dict:
        return {key: _payload_value(item) for key, item in value.items()}
    if type(value) in (list, tuple):
        return [_payload_value(item) for item in value]
    return value


def _reject_non_string_numeric(value: object) -> None:
    if type(value) in (int, float):
        raise ValueError("public payload numeric fields must use string values")
    if type(value) is dict:
        for item in value.values():
            _reject_non_string_numeric(item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_non_string_numeric(item)


def _reject_unsafe_public_surface(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_text(field.name)
            _reject_unsafe_public_surface(label, getattr(value, field.name))
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public payload in {label}")
            _reject_unsafe_text(key)
            _reject_unsafe_public_surface(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_surface(label, item)
        return
    if type(value) is str:
        _reject_unsafe_text(value)


def _reject_unsafe_text(value: str) -> None:
    normalized = value.lower()
    if value.strip() != value or "://" in normalized or "?" in normalized:
        raise ValueError("unsafe public payload")
    if any(fragment in normalized for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError("unsafe public payload")
