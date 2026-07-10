"""Pure Phase 1 report reducer for domain specialist memory retention."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_TEAM_DOMAIN_SPECIALIST_MEMORY_RETENTION_CONFIG_VERSION = (
    "research-team-domain-specialist-memory-retention-report-v0"
)

QUALITY_RETAINED = "retained"
QUALITY_WATCH = "watch"
QUALITY_WEAK = "weak"
QUALITY_BUCKETS = (QUALITY_RETAINED, QUALITY_WATCH, QUALITY_WEAK)

NO_INPUTS_REASON = "memory_retention_no_inputs"
REPORT_RETAINED_REASON = "memory_retention_report_retained"
REPORT_WATCH_REASON = "memory_retention_report_watch"
REPORT_WEAK_REASON = "memory_retention_report_weak"
RETAINED_REASON = "memory_retention_retained"
AGE_WATCH_REASON = "memory_retention_age_watch"
AGE_WEAK_REASON = "memory_retention_age_weak"
REUSE_WATCH_REASON = "memory_retention_reuse_watch"
REUSE_ABSENT_REASON = "memory_retention_reuse_absent"
FEEDBACK_WATCH_REASON = "memory_retention_feedback_watch"
FEEDBACK_ABSENT_REASON = "memory_retention_feedback_absent"
CONTRADICTION_WATCH_REASON = "memory_retention_contradiction_watch"
CONTRADICTION_WEAK_REASON = "memory_retention_contradiction_weak"
CALIBRATION_DRIFT_WATCH_REASON = "memory_retention_calibration_drift_watch"
CALIBRATION_DRIFT_WEAK_REASON = "memory_retention_calibration_drift_weak"

ROW_REASON_CODE_ORDER = (
    AGE_WEAK_REASON,
    REUSE_ABSENT_REASON,
    FEEDBACK_ABSENT_REASON,
    CONTRADICTION_WEAK_REASON,
    CALIBRATION_DRIFT_WEAK_REASON,
    AGE_WATCH_REASON,
    REUSE_WATCH_REASON,
    FEEDBACK_WATCH_REASON,
    CONTRADICTION_WATCH_REASON,
    CALIBRATION_DRIFT_WATCH_REASON,
    RETAINED_REASON,
)
REPORT_REASON_CODE_ORDER = (
    NO_INPUTS_REASON,
    REPORT_WEAK_REASON,
    REPORT_WATCH_REASON,
    REPORT_RETAINED_REASON,
) + ROW_REASON_CODE_ORDER

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
HALF = Decimal("0.500000")
ONE = Decimal("1.000000")
RETENTION_COMPONENT_COUNT = Decimal("5.000000")

MAX_RETAINED_AGE_SECONDS = Decimal("2592000.000000")
MAX_WATCH_AGE_SECONDS = Decimal("7776000.000000")
MIN_RETAINED_REUSE_COUNT = Decimal("3.000000")
MIN_WATCH_REUSE_COUNT = Decimal("1.000000")
MIN_RETAINED_FEEDBACK_COUNT = Decimal("2.000000")
MIN_WATCH_FEEDBACK_COUNT = Decimal("1.000000")
MAX_RETAINED_CONTRADICTION_COUNT = Decimal("0.000000")
MAX_WATCH_CONTRADICTION_COUNT = Decimal("1.000000")
MAX_RETAINED_CALIBRATION_DRIFT = Decimal("0.050000")
MAX_WATCH_CALIBRATION_DRIFT = Decimal("0.150000")

_BUCKET_RANK = {
    QUALITY_WEAK: 0,
    QUALITY_WATCH: 1,
    QUALITY_RETAINED: 2,
}
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_CANONICAL_DECIMAL_RE = re.compile(r"^(?:0|[1-9][0-9]*)\.[0-9]{6}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_UNSAFE_PUBLIC_COMPOUNDS = (
    "://",
    "account_id",
    "auth_token",
    "candidate_id",
    "condition_id",
    "database_url",
    "execution_id",
    "market_id",
    "market_slug",
    "order_id",
    "position_size",
    "private_key",
    "raw_candidate",
    "raw_market",
    "recommendation_id",
    "source_id",
    "source_text",
    "source_url",
    "trade_id",
    "wallet_address",
)
_UNSAFE_PUBLIC_TOKENS = frozenset(
    (
        "account",
        "auth",
        "credential",
        "database",
        "dsn",
        "endpoint",
        "execution",
        "live",
        "network",
        "order",
        "position",
        "private",
        "recommendation",
        "secret",
        "sizing",
        "token",
        "trade",
        "wallet",
    ),
)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_DOMAIN_SPECIALIST_MEMORY_RETENTION_CONFIG_VERSION",
    "QUALITY_BUCKETS",
    "ResearchTeamDomainSpecialistMemoryRetentionObservation",
    "ResearchTeamDomainSpecialistMemoryRetentionReport",
    "ResearchTeamDomainSpecialistMemoryRetentionRow",
    "build_research_team_domain_specialist_memory_retention_report",
    "research_team_domain_specialist_memory_retention_report_digest",
    "research_team_domain_specialist_memory_retention_report_payload",
    "validate_research_team_domain_specialist_memory_retention_report_payload",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchTeamDomainSpecialistMemoryRetentionObservation(_FinalPublicDataclass):
    team_key: str
    domain_key: str
    specialist_key: str
    memory_age_seconds: Decimal
    reuse_count: Decimal
    outcome_feedback_count: Decimal
    contradiction_count: Decimal
    calibration_drift: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "observation",
            self,
            ResearchTeamDomainSpecialistMemoryRetentionObservation,
        )
        for field_name in ("team_key", "domain_key", "specialist_key"):
            object.__setattr__(
                self,
                field_name,
                _require_public_identifier(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "memory_age_seconds",
            _require_nonnegative_decimal(
                "memory_age_seconds",
                self.memory_age_seconds,
            ),
        )
        for field_name in (
            "reuse_count",
            "outcome_feedback_count",
            "contradiction_count",
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
            "calibration_drift",
            _require_ratio_decimal("calibration_drift", self.calibration_drift),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchTeamDomainSpecialistMemoryRetentionRow(_FinalPublicDataclass):
    team_key: str
    domain_key: str
    specialist_key: str
    memory_age_seconds: Decimal
    reuse_count: Decimal
    outcome_feedback_count: Decimal
    contradiction_count: Decimal
    calibration_drift: Decimal
    retention_score: Decimal
    priority_rank: Decimal
    quality_bucket: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "row",
            self,
            ResearchTeamDomainSpecialistMemoryRetentionRow,
        )
        for field_name in ("team_key", "domain_key", "specialist_key"):
            object.__setattr__(
                self,
                field_name,
                _require_public_identifier(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "memory_age_seconds",
            _require_nonnegative_decimal(
                "memory_age_seconds",
                self.memory_age_seconds,
            ),
        )
        for field_name in (
            "reuse_count",
            "outcome_feedback_count",
            "contradiction_count",
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
            "calibration_drift",
            _require_ratio_decimal("calibration_drift", self.calibration_drift),
        )
        object.__setattr__(
            self,
            "retention_score",
            _require_ratio_decimal("retention_score", self.retention_score),
        )
        object.__setattr__(
            self,
            "priority_rank",
            _require_positive_whole_decimal("priority_rank", self.priority_rank),
        )
        object.__setattr__(
            self,
            "quality_bucket",
            _require_quality_bucket("quality_bucket", self.quality_bucket),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                ROW_REASON_CODE_ORDER,
            ),
        )
        expected_reasons = _row_reason_codes(
            memory_age_seconds=self.memory_age_seconds,
            reuse_count=self.reuse_count,
            outcome_feedback_count=self.outcome_feedback_count,
            contradiction_count=self.contradiction_count,
            calibration_drift=self.calibration_drift,
        )
        if self.reason_codes != expected_reasons:
            raise ValueError("reason_codes must match derived memory retention reasons")
        expected_score = _retention_score_from_reason_codes(expected_reasons)
        if self.retention_score != expected_score:
            raise ValueError("retention_score must match derived memory retention reasons")
        expected_bucket = _quality_bucket_from_row_reasons(expected_reasons)
        if self.quality_bucket != expected_bucket:
            raise ValueError("quality_bucket must match derived memory retention reasons")
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchTeamDomainSpecialistMemoryRetentionReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    report_quality_bucket: str
    memory_count: Decimal
    team_count: Decimal
    domain_count: Decimal
    specialist_count: Decimal
    retained_count: Decimal
    watch_count: Decimal
    weak_count: Decimal
    average_retention_score: Decimal
    rows: tuple[ResearchTeamDomainSpecialistMemoryRetentionRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "report",
            self,
            ResearchTeamDomainSpecialistMemoryRetentionReport,
        )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        if self.config_version != (
            DEFAULT_RESEARCH_TEAM_DOMAIN_SPECIALIST_MEMORY_RETENTION_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported report version")
        object.__setattr__(
            self,
            "report_quality_bucket",
            _require_quality_bucket(
                "report_quality_bucket",
                self.report_quality_bucket,
            ),
        )
        for field_name in (
            "memory_count",
            "team_count",
            "domain_count",
            "specialist_count",
            "retained_count",
            "watch_count",
            "weak_count",
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
            "average_retention_score",
            _require_ratio_decimal(
                "average_retention_score",
                self.average_retention_score,
            ),
        )
        object.__setattr__(self, "rows", _require_row_tuple(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODE_ORDER,
            ),
        )
        _validate_report_derived_values(self)
        _require_hard_flags("report", self)
        _require_or_set_report_digest(self)

    @property
    def public_payload(self) -> dict[str, Any]:
        return research_team_domain_specialist_memory_retention_report_payload(self)


def build_research_team_domain_specialist_memory_retention_report(
    observations: Sequence[ResearchTeamDomainSpecialistMemoryRetentionObservation],
    *,
    generated_at: datetime,
) -> ResearchTeamDomainSpecialistMemoryRetentionReport:
    """Reduce sanitized memory observations into quality buckets and reasons."""

    normalized_observations = _normalize_observations(observations)
    sorted_rows = tuple(
        sorted(
            (_row_from_observation(item) for item in normalized_observations),
            key=_row_sort_key,
        ),
    )
    rows = tuple(
        replace(row, priority_rank=_decimal_count(index))
        for index, row in enumerate(sorted_rows, start=1)
    )
    report_bucket = _report_quality_bucket(rows)
    reason_codes = _report_reason_codes(rows, report_bucket=report_bucket)
    values: dict[str, object] = {
        "generated_at": _as_utc("generated_at", generated_at),
        "config_version": (
            DEFAULT_RESEARCH_TEAM_DOMAIN_SPECIALIST_MEMORY_RETENTION_CONFIG_VERSION
        ),
        "report_quality_bucket": report_bucket,
        "memory_count": _decimal_count(len(rows)),
        "team_count": _decimal_count(len({row.team_key for row in rows})),
        "domain_count": _decimal_count(len({row.domain_key for row in rows})),
        "specialist_count": _decimal_count(
            len({row.specialist_key for row in rows}),
        ),
        "retained_count": _bucket_count(rows, QUALITY_RETAINED),
        "watch_count": _bucket_count(rows, QUALITY_WATCH),
        "weak_count": _bucket_count(rows, QUALITY_WEAK),
        "average_retention_score": _average_retention_score(rows),
        "rows": rows,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchTeamDomainSpecialistMemoryRetentionReport(
        **values,
        derived_validation_digest=_digest_for_values(values),
    )


def research_team_domain_specialist_memory_retention_report_payload(
    value: object,
) -> dict[str, Any]:
    if type(value) is ResearchTeamDomainSpecialistMemoryRetentionReport:
        _validate_report_derived_values(value)
        _require_hard_flags("report", value)
        expected_digest = _report_digest_from_report(value)
        if value.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match public payload")
        payload = _payload_value(value)
        if type(payload) is not dict:
            raise ValueError("public payload must be a JSON object")
        return validate_research_team_domain_specialist_memory_retention_report_payload(
            payload,
        )
    if type(value) is dict:
        return validate_research_team_domain_specialist_memory_retention_report_payload(
            value,
        )
    raise ValueError(
        "value must be a memory retention report or canonical public payload",
    )


def research_team_domain_specialist_memory_retention_report_digest(
    value: object,
) -> str:
    payload = research_team_domain_specialist_memory_retention_report_payload(value)
    return _require_sha256_digest(
        "derived_validation_digest",
        payload["derived_validation_digest"],
    )


def validate_research_team_domain_specialist_memory_retention_report_payload(
    payload: object,
) -> dict[str, Any]:
    if type(payload) is not dict:
        raise ValueError("public payload must be exactly dict")
    report = _report_from_public_payload(payload)
    canonical_payload = _payload_value(report)
    if type(canonical_payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    if canonical_payload != payload:
        raise ValueError("public payload schema values must be canonical")
    return canonical_payload


def _row_from_observation(
    observation: ResearchTeamDomainSpecialistMemoryRetentionObservation,
) -> ResearchTeamDomainSpecialistMemoryRetentionRow:
    reasons = _row_reason_codes(
        memory_age_seconds=observation.memory_age_seconds,
        reuse_count=observation.reuse_count,
        outcome_feedback_count=observation.outcome_feedback_count,
        contradiction_count=observation.contradiction_count,
        calibration_drift=observation.calibration_drift,
    )
    retention_score = _retention_score_from_reason_codes(reasons)
    return ResearchTeamDomainSpecialistMemoryRetentionRow(
        team_key=observation.team_key,
        domain_key=observation.domain_key,
        specialist_key=observation.specialist_key,
        memory_age_seconds=observation.memory_age_seconds,
        reuse_count=observation.reuse_count,
        outcome_feedback_count=observation.outcome_feedback_count,
        contradiction_count=observation.contradiction_count,
        calibration_drift=observation.calibration_drift,
        retention_score=retention_score,
        priority_rank=ONE,
        quality_bucket=_quality_bucket_from_row_reasons(reasons),
        reason_codes=reasons,
    )


def _row_reason_codes(
    *,
    memory_age_seconds: Decimal,
    reuse_count: Decimal,
    outcome_feedback_count: Decimal,
    contradiction_count: Decimal,
    calibration_drift: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if memory_age_seconds > MAX_WATCH_AGE_SECONDS:
        reasons.append(AGE_WEAK_REASON)
    elif memory_age_seconds > MAX_RETAINED_AGE_SECONDS:
        reasons.append(AGE_WATCH_REASON)

    if reuse_count < MIN_WATCH_REUSE_COUNT:
        reasons.append(REUSE_ABSENT_REASON)
    elif reuse_count < MIN_RETAINED_REUSE_COUNT:
        reasons.append(REUSE_WATCH_REASON)

    if outcome_feedback_count < MIN_WATCH_FEEDBACK_COUNT:
        reasons.append(FEEDBACK_ABSENT_REASON)
    elif outcome_feedback_count < MIN_RETAINED_FEEDBACK_COUNT:
        reasons.append(FEEDBACK_WATCH_REASON)

    if contradiction_count > MAX_WATCH_CONTRADICTION_COUNT:
        reasons.append(CONTRADICTION_WEAK_REASON)
    elif contradiction_count > MAX_RETAINED_CONTRADICTION_COUNT:
        reasons.append(CONTRADICTION_WATCH_REASON)

    if calibration_drift > MAX_WATCH_CALIBRATION_DRIFT:
        reasons.append(CALIBRATION_DRIFT_WEAK_REASON)
    elif calibration_drift > MAX_RETAINED_CALIBRATION_DRIFT:
        reasons.append(CALIBRATION_DRIFT_WATCH_REASON)

    if not reasons:
        reasons.append(RETAINED_REASON)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reasons),
        ROW_REASON_CODE_ORDER,
    )


def _quality_bucket_from_row_reasons(reason_codes: tuple[str, ...]) -> str:
    if any(
        reason in {
            AGE_WEAK_REASON,
            REUSE_ABSENT_REASON,
            FEEDBACK_ABSENT_REASON,
            CONTRADICTION_WEAK_REASON,
            CALIBRATION_DRIFT_WEAK_REASON,
        }
        for reason in reason_codes
    ):
        return QUALITY_WEAK
    if reason_codes == (RETAINED_REASON,):
        return QUALITY_RETAINED
    return QUALITY_WATCH


def _retention_score_from_reason_codes(
    reason_codes: tuple[str, ...],
) -> Decimal:
    component_scores = (
        _reason_dimension_score(
            reason_codes,
            weak_reason=AGE_WEAK_REASON,
            watch_reason=AGE_WATCH_REASON,
        ),
        _reason_dimension_score(
            reason_codes,
            weak_reason=REUSE_ABSENT_REASON,
            watch_reason=REUSE_WATCH_REASON,
        ),
        _reason_dimension_score(
            reason_codes,
            weak_reason=FEEDBACK_ABSENT_REASON,
            watch_reason=FEEDBACK_WATCH_REASON,
        ),
        _reason_dimension_score(
            reason_codes,
            weak_reason=CONTRADICTION_WEAK_REASON,
            watch_reason=CONTRADICTION_WATCH_REASON,
        ),
        _reason_dimension_score(
            reason_codes,
            weak_reason=CALIBRATION_DRIFT_WEAK_REASON,
            watch_reason=CALIBRATION_DRIFT_WATCH_REASON,
        ),
    )
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(component_scores, ZERO) / RETENTION_COMPONENT_COUNT)


def _reason_dimension_score(
    reason_codes: tuple[str, ...],
    *,
    weak_reason: str,
    watch_reason: str,
) -> Decimal:
    if weak_reason in reason_codes:
        return ZERO
    if watch_reason in reason_codes:
        return HALF
    return ONE


def _report_quality_bucket(
    rows: tuple[ResearchTeamDomainSpecialistMemoryRetentionRow, ...],
) -> str:
    if not rows or any(row.quality_bucket == QUALITY_WEAK for row in rows):
        return QUALITY_WEAK
    if any(row.quality_bucket == QUALITY_WATCH for row in rows):
        return QUALITY_WATCH
    return QUALITY_RETAINED


def _report_reason_codes(
    rows: tuple[ResearchTeamDomainSpecialistMemoryRetentionRow, ...],
    *,
    report_bucket: str,
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    report_reason = {
        QUALITY_RETAINED: REPORT_RETAINED_REASON,
        QUALITY_WATCH: REPORT_WATCH_REASON,
        QUALITY_WEAK: REPORT_WEAK_REASON,
    }[report_bucket]
    present = {reason for row in rows for reason in row.reason_codes}
    return (report_reason,) + tuple(
        reason for reason in ROW_REASON_CODE_ORDER if reason in present
    )


def _validate_report_derived_values(
    report: ResearchTeamDomainSpecialistMemoryRetentionReport,
) -> None:
    sorted_rows = tuple(sorted(report.rows, key=_row_sort_key))
    if report.rows != sorted_rows:
        raise ValueError("rows must use canonical quality and identifier order")
    identities = tuple(
        (row.team_key, row.domain_key, row.specialist_key)
        for row in report.rows
    )
    if len(frozenset(identities)) != len(identities):
        raise ValueError("row team/domain/specialist identities must be unique")
    expected_ranks = tuple(
        _decimal_count(index)
        for index in range(1, len(report.rows) + 1)
    )
    if tuple(row.priority_rank for row in report.rows) != expected_ranks:
        raise ValueError("priority_rank must match canonical row order")
    expected_memory_count = _decimal_count(len(report.rows))
    if report.memory_count != expected_memory_count:
        raise ValueError("memory_count must match rows")
    expected_team_count = _decimal_count(len({row.team_key for row in report.rows}))
    if report.team_count != expected_team_count:
        raise ValueError("team_count must match rows")
    expected_domain_count = _decimal_count(
        len({row.domain_key for row in report.rows}),
    )
    if report.domain_count != expected_domain_count:
        raise ValueError("domain_count must match rows")
    expected_specialist_count = _decimal_count(
        len({row.specialist_key for row in report.rows}),
    )
    if report.specialist_count != expected_specialist_count:
        raise ValueError("specialist_count must match rows")
    expected_retained_count = _bucket_count(report.rows, QUALITY_RETAINED)
    if report.retained_count != expected_retained_count:
        raise ValueError("retained_count must match rows")
    expected_watch_count = _bucket_count(report.rows, QUALITY_WATCH)
    if report.watch_count != expected_watch_count:
        raise ValueError("watch_count must match rows")
    expected_weak_count = _bucket_count(report.rows, QUALITY_WEAK)
    if report.weak_count != expected_weak_count:
        raise ValueError("weak_count must match rows")
    expected_average_score = _average_retention_score(report.rows)
    if report.average_retention_score != expected_average_score:
        raise ValueError("average_retention_score must match rows")
    expected_bucket = _report_quality_bucket(report.rows)
    if report.report_quality_bucket != expected_bucket:
        raise ValueError("report_quality_bucket must match rows")
    expected_reasons = _report_reason_codes(
        report.rows,
        report_bucket=expected_bucket,
    )
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match derived report quality")


def _report_from_public_payload(
    payload: dict[str, Any],
) -> ResearchTeamDomainSpecialistMemoryRetentionReport:
    _require_exact_payload_fields(
        "public payload",
        payload,
        ResearchTeamDomainSpecialistMemoryRetentionReport,
    )
    row_payloads = _require_public_list("rows", payload["rows"])
    rows = tuple(
        _row_from_public_payload(item, index=index)
        for index, item in enumerate(row_payloads)
    )
    return ResearchTeamDomainSpecialistMemoryRetentionReport(
        generated_at=_public_datetime("generated_at", payload["generated_at"]),
        config_version=_public_string("config_version", payload["config_version"]),
        report_quality_bucket=_public_string(
            "report_quality_bucket",
            payload["report_quality_bucket"],
        ),
        memory_count=_public_decimal("memory_count", payload["memory_count"]),
        team_count=_public_decimal("team_count", payload["team_count"]),
        domain_count=_public_decimal("domain_count", payload["domain_count"]),
        specialist_count=_public_decimal(
            "specialist_count",
            payload["specialist_count"],
        ),
        retained_count=_public_decimal("retained_count", payload["retained_count"]),
        watch_count=_public_decimal("watch_count", payload["watch_count"]),
        weak_count=_public_decimal("weak_count", payload["weak_count"]),
        average_retention_score=_public_decimal(
            "average_retention_score",
            payload["average_retention_score"],
        ),
        rows=rows,
        reason_codes=_public_string_tuple("reason_codes", payload["reason_codes"]),
        derived_validation_digest=_public_string(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_public_bool("paper_only", payload["paper_only"]),
        report_only=_public_bool("report_only", payload["report_only"]),
        readonly=_public_bool("readonly", payload["readonly"]),
    )


def _row_from_public_payload(
    value: object,
    *,
    index: int,
) -> ResearchTeamDomainSpecialistMemoryRetentionRow:
    field_name = f"rows[{index}]"
    payload = _require_public_dict(field_name, value)
    _require_exact_payload_fields(
        field_name,
        payload,
        ResearchTeamDomainSpecialistMemoryRetentionRow,
    )
    return ResearchTeamDomainSpecialistMemoryRetentionRow(
        team_key=_public_string(f"{field_name}.team_key", payload["team_key"]),
        domain_key=_public_string(f"{field_name}.domain_key", payload["domain_key"]),
        specialist_key=_public_string(
            f"{field_name}.specialist_key",
            payload["specialist_key"],
        ),
        memory_age_seconds=_public_decimal(
            f"{field_name}.memory_age_seconds",
            payload["memory_age_seconds"],
        ),
        reuse_count=_public_decimal(
            f"{field_name}.reuse_count",
            payload["reuse_count"],
        ),
        outcome_feedback_count=_public_decimal(
            f"{field_name}.outcome_feedback_count",
            payload["outcome_feedback_count"],
        ),
        contradiction_count=_public_decimal(
            f"{field_name}.contradiction_count",
            payload["contradiction_count"],
        ),
        calibration_drift=_public_decimal(
            f"{field_name}.calibration_drift",
            payload["calibration_drift"],
        ),
        retention_score=_public_decimal(
            f"{field_name}.retention_score",
            payload["retention_score"],
        ),
        priority_rank=_public_decimal(
            f"{field_name}.priority_rank",
            payload["priority_rank"],
        ),
        quality_bucket=_public_string(
            f"{field_name}.quality_bucket",
            payload["quality_bucket"],
        ),
        reason_codes=_public_string_tuple(
            f"{field_name}.reason_codes",
            payload["reason_codes"],
        ),
        paper_only=_public_bool(
            f"{field_name}.paper_only",
            payload["paper_only"],
        ),
        report_only=_public_bool(
            f"{field_name}.report_only",
            payload["report_only"],
        ),
        readonly=_public_bool(f"{field_name}.readonly", payload["readonly"]),
    )


def _normalize_observations(
    value: Sequence[ResearchTeamDomainSpecialistMemoryRetentionObservation],
) -> tuple[ResearchTeamDomainSpecialistMemoryRetentionObservation, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError("observations must be a sequence")
    observations = tuple(value)
    normalized: list[
        ResearchTeamDomainSpecialistMemoryRetentionObservation
    ] = []
    seen_identities: set[tuple[str, str, str]] = set()
    for item in observations:
        if type(item) is not ResearchTeamDomainSpecialistMemoryRetentionObservation:
            raise ValueError(
                "observations must contain memory retention observations",
            )
        normalized_item = replace(item)
        identity = (
            normalized_item.team_key,
            normalized_item.domain_key,
            normalized_item.specialist_key,
        )
        if identity in seen_identities:
            raise ValueError(
                "observation team/domain/specialist identities must be unique",
            )
        seen_identities.add(identity)
        normalized.append(normalized_item)
    return tuple(normalized)


def _require_row_tuple(
    value: tuple[ResearchTeamDomainSpecialistMemoryRetentionRow, ...],
) -> tuple[ResearchTeamDomainSpecialistMemoryRetentionRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be exactly tuple")
    normalized: list[ResearchTeamDomainSpecialistMemoryRetentionRow] = []
    for row in value:
        if type(row) is not ResearchTeamDomainSpecialistMemoryRetentionRow:
            raise ValueError("rows must contain memory retention rows")
        normalized.append(replace(row))
    return tuple(normalized)


def _row_sort_key(
    row: ResearchTeamDomainSpecialistMemoryRetentionRow,
) -> tuple[object, ...]:
    with localcontext(DECIMAL_CONTEXT):
        return (
            _BUCKET_RANK[row.quality_bucket],
            row.retention_score,
            -row.memory_age_seconds,
            row.reuse_count,
            row.outcome_feedback_count,
            -row.contradiction_count,
            -row.calibration_drift,
            row.team_key,
            row.domain_key,
            row.specialist_key,
            row.reason_codes,
        )


def _bucket_count(
    rows: tuple[ResearchTeamDomainSpecialistMemoryRetentionRow, ...],
    bucket: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.quality_bucket == bucket))


def _average_retention_score(
    rows: tuple[ResearchTeamDomainSpecialistMemoryRetentionRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        total = sum((row.retention_score for row in rows), ZERO)
        return _quantize(total / Decimal(len(rows)))


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _require_exact_type(field_name: str, value: object, expected: type[object]) -> None:
    if type(value) is not expected:
        raise ValueError(f"{field_name} must be exactly {expected.__name__}")


def _require_public_identifier(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be exactly str")
    if _PUBLIC_IDENTIFIER_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a canonical public identifier")
    lowered = value.lower()
    tokens = frozenset(part for part in re.split(r"[._-]+", lowered) if part)
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_COMPOUNDS) or (
        tokens & _UNSAFE_PUBLIC_TOKENS
    ):
        raise ValueError(
            f"{field_name} must be a privacy-safe public identifier",
        )
    return value


def _require_quality_bucket(field_name: str, value: str) -> str:
    if type(value) is not str or value not in QUALITY_BUCKETS:
        raise ValueError(f"{field_name} must be retained, watch, or weak")
    return value


def _normalize_reason_codes(
    field_name: str,
    value: tuple[str, ...],
    allowed_order: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError(f"{field_name} must be a nonempty tuple")
    if any(type(item) is not str for item in value):
        raise ValueError(f"{field_name} must contain strings")
    if len(frozenset(value)) != len(value):
        raise ValueError(f"{field_name} must not contain duplicates")
    unknown = frozenset(value).difference(allowed_order)
    if unknown:
        raise ValueError(f"{field_name} contains unknown reason codes")
    normalized = tuple(item for item in allowed_order if item in value)
    if normalized != value:
        raise ValueError(f"{field_name} must use canonical reason order")
    return normalized


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name) is not True:
            raise ValueError(f"{field_name} must keep {flag_name}=True")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    if value.microsecond != 0:
        raise ValueError(f"{field_name} must be a whole second")
    return value.astimezone(UTC)


def _require_raw_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be a finite Decimal")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not be signed zero")
    return value


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    return _quantize(_require_raw_decimal(field_name, value))


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    raw_value = _require_raw_decimal(field_name, value)
    if raw_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(raw_value)


def _require_nonnegative_whole_decimal(
    field_name: str,
    value: Decimal,
) -> Decimal:
    raw_value = _require_raw_decimal(field_name, value)
    if raw_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        if raw_value != raw_value.to_integral_value():
            raise ValueError(f"{field_name} must be whole")
    return _quantize(raw_value)


def _require_positive_whole_decimal(
    field_name: str,
    value: Decimal,
) -> Decimal:
    decimal_value = _require_nonnegative_whole_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    raw_value = _require_raw_decimal(field_name, value)
    if raw_value < ZERO or raw_value > ONE:
        raise ValueError(f"{field_name} must be in the unit interval")
    return _quantize(raw_value)


def _quantize(value: Decimal) -> Decimal:
    try:
        with localcontext(DECIMAL_CONTEXT):
            quantized = value.quantize(QUANT)
    except InvalidOperation as exc:
        raise ValueError("Decimal value cannot be quantized") from exc
    if quantized.is_zero() and quantized.is_signed():
        raise ValueError("Decimal value must not quantize to signed zero")
    return quantized


def _require_or_set_report_digest(
    report: ResearchTeamDomainSpecialistMemoryRetentionReport,
) -> None:
    if type(report.derived_validation_digest) is not str:
        raise ValueError("derived_validation_digest must be exactly str")
    expected_digest = _report_digest_from_report(report)
    if report.derived_validation_digest == "":
        object.__setattr__(report, "derived_validation_digest", expected_digest)
        return
    _require_sha256_digest(
        "derived_validation_digest",
        report.derived_validation_digest,
    )
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match public payload")


def _report_digest_from_report(
    report: ResearchTeamDomainSpecialistMemoryRetentionReport,
) -> str:
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return _canonical_digest(payload)


def _digest_for_values(values: dict[str, object]) -> str:
    return _canonical_digest(_payload_value(values))


def _canonical_digest(payload: object) -> str:
    encoded = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a lowercase SHA-256 digest")
    return value


def _payload_value(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is dict:
        return {key: _payload_value(item) for key, item in value.items()}
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
    return value


def _require_exact_payload_fields(
    field_name: str,
    payload: dict[str, Any],
    dataclass_type: type[object],
) -> None:
    expected_order = tuple(field.name for field in fields(dataclass_type))
    if set(payload) != set(expected_order):
        raise ValueError(f"{field_name} schema fields must match exactly")
    if tuple(payload) != expected_order:
        raise ValueError(f"{field_name} must use canonical field order")


def _require_public_dict(field_name: str, value: object) -> dict[str, Any]:
    if type(value) is not dict:
        raise ValueError(f"{field_name} must be exactly dict")
    return value


def _require_public_list(field_name: str, value: object) -> list[Any]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be exactly list")
    return value


def _public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be exactly str")
    return value


def _public_string_tuple(field_name: str, value: object) -> tuple[str, ...]:
    items = _require_public_list(field_name, value)
    if any(type(item) is not str for item in items):
        raise ValueError(f"{field_name} must contain strings")
    return tuple(items)


def _public_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must encode Decimal as str")
    if value.startswith("-"):
        try:
            parsed = Decimal(value)
        except InvalidOperation as exc:
            raise ValueError(f"{field_name} must encode Decimal as str") from exc
        if parsed.is_zero():
            raise ValueError(f"{field_name} must not be signed zero")
    if _CANONICAL_DECIMAL_RE.fullmatch(value) is None:
        raise ValueError(
            f"{field_name} must encode a canonical Decimal string",
        )
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must encode Decimal as str") from exc


def _public_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not str or not value.endswith("Z"):
        raise ValueError(f"{field_name} must be a canonical UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a canonical UTC timestamp") from exc
    return _as_utc(field_name, parsed)


def _public_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be exactly bool")
    return value
