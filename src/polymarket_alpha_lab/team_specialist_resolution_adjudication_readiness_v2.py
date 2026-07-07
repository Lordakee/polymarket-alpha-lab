"""Pure in-memory Phase 1 resolution adjudication readiness report."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_taxonomy import require_team_category_pair


DEFAULT_TEAM_SPECIALIST_RESOLUTION_ADJUDICATION_READINESS_V2_CONFIG_VERSION = (
    "team-specialist-resolution-adjudication-readiness-v2-v0"
)
DEFAULT_TEAM_SPECIALIST_RESOLUTION_ADJUDICATION_READINESS_V2_VERSION = (
    DEFAULT_TEAM_SPECIALIST_RESOLUTION_ADJUDICATION_READINESS_V2_CONFIG_VERSION
)

COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
SECONDS_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

STATUSES = ("pass", "blocked")
DIMENSION_IDS = (
    "rule_familiarity",
    "official_source_coverage",
    "contradiction_handling",
    "close_urgency",
    "prior_error_rate",
    "reviewer_load",
)
MINIMUM_READY_DIMENSIONS = frozenset(
    (
        "rule_familiarity",
        "official_source_coverage",
        "contradiction_handling",
        "close_urgency",
    ),
)
MAXIMUM_READY_DIMENSIONS = frozenset(("prior_error_rate", "reviewer_load"))

REPORT_REASON_CODES = (
    "resolution_adjudication_readiness_clear",
    "rule_familiarity_below_threshold",
    "official_source_coverage_below_threshold",
    "contradiction_handling_below_threshold",
    "close_urgency_window_too_short",
    "prior_error_rate_above_threshold",
    "reviewer_load_above_threshold",
)
ROW_REASON_CODES = (
    "rule_familiarity_ready",
    "rule_familiarity_below_threshold",
    "official_source_coverage_ready",
    "official_source_coverage_below_threshold",
    "contradiction_handling_ready",
    "contradiction_handling_below_threshold",
    "close_urgency_ready",
    "close_urgency_window_too_short",
    "prior_error_rate_ready",
    "prior_error_rate_above_threshold",
    "reviewer_load_ready",
    "reviewer_load_above_threshold",
)
PASS_REASON_BY_DIMENSION = {
    "rule_familiarity": "rule_familiarity_ready",
    "official_source_coverage": "official_source_coverage_ready",
    "contradiction_handling": "contradiction_handling_ready",
    "close_urgency": "close_urgency_ready",
    "prior_error_rate": "prior_error_rate_ready",
    "reviewer_load": "reviewer_load_ready",
}
BLOCK_REASON_BY_DIMENSION = {
    "rule_familiarity": "rule_familiarity_below_threshold",
    "official_source_coverage": "official_source_coverage_below_threshold",
    "contradiction_handling": "contradiction_handling_below_threshold",
    "close_urgency": "close_urgency_window_too_short",
    "prior_error_rate": "prior_error_rate_above_threshold",
    "reviewer_load": "reviewer_load_above_threshold",
}
PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
REPORT_PUBLIC_FIELDS = frozenset(
    (
        "generated_at",
        "config_version",
        "team_id",
        "category_id",
        "specialist_id",
        "adjudication_case_id",
        "observed_at",
        "readiness_status",
        "reason_codes",
        "ready_dimension_count",
        "blocked_dimension_count",
        "rule_familiarity_score",
        "official_source_coverage_score",
        "contradiction_handling_score",
        "seconds_until_close",
        "prior_error_rate",
        "open_review_count",
        "dimension_rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
DIMENSION_ROW_PUBLIC_FIELDS = frozenset(
    (
        "dimension_id",
        "observed_value",
        "threshold_value",
        "dimension_status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
UNSAFE_PUBLIC_FRAGMENTS = (
    "li" "ve",
    "au" "th",
    "wa" "llet",
    "or" "der",
    "net" "work",
    "data" "base",
    "per" "sist",
    "sign" "ing",
    "muta" "tion",
    "bu" "y",
    "se" "ll",
    "tra" "de",
)


@dataclass(frozen=True)
class TeamSpecialistResolutionAdjudicationReadinessConfig:
    config_version: str = (
        DEFAULT_TEAM_SPECIALIST_RESOLUTION_ADJUDICATION_READINESS_V2_CONFIG_VERSION
    )
    min_rule_familiarity_score: Decimal = Decimal("0.800000")
    min_official_source_coverage_score: Decimal = Decimal("0.800000")
    min_contradiction_handling_score: Decimal = Decimal("0.800000")
    min_seconds_until_close: Decimal = Decimal("3600.000000")
    max_prior_error_rate: Decimal = Decimal("0.050000")
    max_open_review_count: Decimal = Decimal("3")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "min_rule_familiarity_score",
            "min_official_source_coverage_score",
            "min_contradiction_handling_score",
            "max_prior_error_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_seconds_until_close",
            _normalize_positive_seconds(
                "min_seconds_until_close",
                self.min_seconds_until_close,
            ),
        )
        object.__setattr__(
            self,
            "max_open_review_count",
            _normalize_nonnegative_count(
                "max_open_review_count",
                self.max_open_review_count,
            ),
        )
        _require_hard_flags("TeamSpecialistResolutionAdjudicationReadinessConfig", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class TeamSpecialistResolutionAdjudicationReadinessInput:
    team_id: str
    category_id: str
    specialist_id: str
    adjudication_case_id: str
    observed_at: datetime
    rule_familiarity_score: Decimal
    official_source_coverage_score: Decimal
    contradiction_handling_score: Decimal
    seconds_until_close: Decimal
    prior_error_rate: Decimal
    open_review_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        team_id, category_id = require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        object.__setattr__(self, "team_id", team_id)
        object.__setattr__(self, "category_id", category_id)
        _require_public_string("specialist_id", self.specialist_id)
        _require_public_string("adjudication_case_id", self.adjudication_case_id)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "rule_familiarity_score",
            "official_source_coverage_score",
            "contradiction_handling_score",
            "prior_error_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "seconds_until_close",
            _normalize_nonnegative_seconds(
                "seconds_until_close",
                self.seconds_until_close,
            ),
        )
        object.__setattr__(
            self,
            "open_review_count",
            _normalize_nonnegative_count("open_review_count", self.open_review_count),
        )
        _require_hard_flags("TeamSpecialistResolutionAdjudicationReadinessInput", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class TeamSpecialistResolutionAdjudicationReadinessDimensionRow:
    dimension_id: str
    observed_value: Decimal
    threshold_value: Decimal
    dimension_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_member("dimension_id", self.dimension_id, DIMENSION_IDS)
        object.__setattr__(
            self,
            "observed_value",
            _normalize_dimension_value(
                self.dimension_id,
                "observed_value",
                self.observed_value,
            ),
        )
        object.__setattr__(
            self,
            "threshold_value",
            _normalize_dimension_value(
                self.dimension_id,
                "threshold_value",
                self.threshold_value,
            ),
        )
        _require_member("dimension_status", self.dimension_status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        if self.dimension_status != _dimension_status(
            self.dimension_id,
            self.observed_value,
            self.threshold_value,
        ):
            raise ValueError("dimension_status must match observed value and threshold")
        if self.reason_codes != _dimension_reason_codes(
            self.dimension_id,
            self.dimension_status,
        ):
            raise ValueError("reason_codes must match dimension_status")
        _require_hard_flags(
            "TeamSpecialistResolutionAdjudicationReadinessDimensionRow",
            self,
        )
        _reject_unsafe_public_payload("dimension row", self)


@dataclass(frozen=True)
class TeamSpecialistResolutionAdjudicationReadinessReport:
    generated_at: datetime
    config_version: str
    team_id: str
    category_id: str
    specialist_id: str
    adjudication_case_id: str
    observed_at: datetime
    readiness_status: str
    reason_codes: tuple[str, ...]
    ready_dimension_count: Decimal
    blocked_dimension_count: Decimal
    rule_familiarity_score: Decimal
    official_source_coverage_score: Decimal
    contradiction_handling_score: Decimal
    seconds_until_close: Decimal
    prior_error_rate: Decimal
    open_review_count: Decimal
    dimension_rows: tuple[TeamSpecialistResolutionAdjudicationReadinessDimensionRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        team_id, category_id = require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        object.__setattr__(self, "team_id", team_id)
        object.__setattr__(self, "category_id", category_id)
        _require_public_string("specialist_id", self.specialist_id)
        _require_public_string("adjudication_case_id", self.adjudication_case_id)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_member("readiness_status", self.readiness_status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        for field_name in ("ready_dimension_count", "blocked_dimension_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "rule_familiarity_score",
            "official_source_coverage_score",
            "contradiction_handling_score",
            "prior_error_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "seconds_until_close",
            _normalize_nonnegative_seconds(
                "seconds_until_close",
                self.seconds_until_close,
            ),
        )
        object.__setattr__(
            self,
            "open_review_count",
            _normalize_nonnegative_count("open_review_count", self.open_review_count),
        )
        object.__setattr__(
            self,
            "dimension_rows",
            _normalize_dimension_rows(self.dimension_rows),
        )
        _require_hard_flags("TeamSpecialistResolutionAdjudicationReadinessReport", self)
        _reject_unsafe_public_payload("readiness report", self)
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report(self)
        if self.derived_validation_digest != _digest_for_report(self):
            raise ValueError("derived_validation_digest must match report payload")


def build_team_specialist_resolution_adjudication_readiness_v2_report(
    input_row: TeamSpecialistResolutionAdjudicationReadinessInput,
    *,
    config: TeamSpecialistResolutionAdjudicationReadinessConfig,
    generated_at: datetime,
) -> TeamSpecialistResolutionAdjudicationReadinessReport:
    if type(config) is not TeamSpecialistResolutionAdjudicationReadinessConfig:
        raise ValueError(
            "config must be a TeamSpecialistResolutionAdjudicationReadinessConfig",
        )
    if type(input_row) is not TeamSpecialistResolutionAdjudicationReadinessInput:
        raise ValueError(
            "input_row must be a TeamSpecialistResolutionAdjudicationReadinessInput",
        )
    _require_hard_flags("config", config)
    _require_hard_flags("input_row", input_row)
    generated_at_utc = _as_utc("generated_at", generated_at)
    if input_row.observed_at > generated_at_utc:
        raise ValueError("observed_at must not be in the future")
    rows = (
        _dimension_row(
            "rule_familiarity",
            input_row.rule_familiarity_score,
            config.min_rule_familiarity_score,
        ),
        _dimension_row(
            "official_source_coverage",
            input_row.official_source_coverage_score,
            config.min_official_source_coverage_score,
        ),
        _dimension_row(
            "contradiction_handling",
            input_row.contradiction_handling_score,
            config.min_contradiction_handling_score,
        ),
        _dimension_row(
            "close_urgency",
            input_row.seconds_until_close,
            config.min_seconds_until_close,
        ),
        _dimension_row(
            "prior_error_rate",
            input_row.prior_error_rate,
            config.max_prior_error_rate,
        ),
        _dimension_row(
            "reviewer_load",
            input_row.open_review_count,
            config.max_open_review_count,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "team_id": input_row.team_id,
        "category_id": input_row.category_id,
        "specialist_id": input_row.specialist_id,
        "adjudication_case_id": input_row.adjudication_case_id,
        "observed_at": input_row.observed_at,
        "readiness_status": _status_from_reason_codes(reason_codes),
        "reason_codes": reason_codes,
        "ready_dimension_count": _count(
            sum(1 for row in rows if row.dimension_status == "pass"),
        ),
        "blocked_dimension_count": _count(
            sum(1 for row in rows if row.dimension_status == "blocked"),
        ),
        "rule_familiarity_score": input_row.rule_familiarity_score,
        "official_source_coverage_score": input_row.official_source_coverage_score,
        "contradiction_handling_score": input_row.contradiction_handling_score,
        "seconds_until_close": input_row.seconds_until_close,
        "prior_error_rate": input_row.prior_error_rate,
        "open_review_count": input_row.open_review_count,
        "dimension_rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["derived_validation_digest"] = _digest_for_public_payload(_public_value(values))
    return TeamSpecialistResolutionAdjudicationReadinessReport(**values)


def team_specialist_resolution_adjudication_readiness_v2_payload(
    report: TeamSpecialistResolutionAdjudicationReadinessReport,
) -> dict[str, Any]:
    if type(report) is not TeamSpecialistResolutionAdjudicationReadinessReport:
        raise ValueError(
            "report must be a TeamSpecialistResolutionAdjudicationReadinessReport",
        )
    _require_hard_flags("report", report)
    _reject_unsafe_public_payload("readiness report", report)
    payload = _public_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be an object")
    return validate_team_specialist_resolution_adjudication_readiness_v2_payload(payload)


def validate_team_specialist_resolution_adjudication_readiness_v2_payload(
    payload: dict[str, Any],
) -> dict[str, Any]:
    if type(payload) is not dict:
        raise ValueError("payload must be an object")
    _reject_unsafe_public_payload("readiness payload", payload)
    digest = payload.get("derived_validation_digest")
    if digest is None:
        raise ValueError("derived_validation_digest is required")
    _require_sha256_digest("derived_validation_digest", digest)
    if digest != _digest_for_public_payload(payload):
        raise ValueError("derived_validation_digest must match report payload")
    report = _report_from_public_payload(payload)
    if _public_value(report) != payload:
        raise ValueError("payload must be canonical readiness report")
    return payload


def _report_from_public_payload(
    payload: dict[str, Any],
) -> TeamSpecialistResolutionAdjudicationReadinessReport:
    _require_payload_fields(
        payload,
        REPORT_PUBLIC_FIELDS,
        "payload fields must match readiness report",
    )
    return TeamSpecialistResolutionAdjudicationReadinessReport(
        generated_at=_datetime_from_public_payload(
            "generated_at",
            payload["generated_at"],
        ),
        config_version=_string_from_public_payload(
            "config_version",
            payload["config_version"],
        ),
        team_id=_string_from_public_payload("team_id", payload["team_id"]),
        category_id=_string_from_public_payload("category_id", payload["category_id"]),
        specialist_id=_string_from_public_payload(
            "specialist_id",
            payload["specialist_id"],
        ),
        adjudication_case_id=_string_from_public_payload(
            "adjudication_case_id",
            payload["adjudication_case_id"],
        ),
        observed_at=_datetime_from_public_payload(
            "observed_at",
            payload["observed_at"],
        ),
        readiness_status=_string_from_public_payload(
            "readiness_status",
            payload["readiness_status"],
        ),
        reason_codes=_tuple_from_public_payload(
            "reason_codes",
            payload["reason_codes"],
        ),
        ready_dimension_count=_decimal_from_public_payload(
            "ready_dimension_count",
            payload["ready_dimension_count"],
        ),
        blocked_dimension_count=_decimal_from_public_payload(
            "blocked_dimension_count",
            payload["blocked_dimension_count"],
        ),
        rule_familiarity_score=_decimal_from_public_payload(
            "rule_familiarity_score",
            payload["rule_familiarity_score"],
        ),
        official_source_coverage_score=_decimal_from_public_payload(
            "official_source_coverage_score",
            payload["official_source_coverage_score"],
        ),
        contradiction_handling_score=_decimal_from_public_payload(
            "contradiction_handling_score",
            payload["contradiction_handling_score"],
        ),
        seconds_until_close=_decimal_from_public_payload(
            "seconds_until_close",
            payload["seconds_until_close"],
        ),
        prior_error_rate=_decimal_from_public_payload(
            "prior_error_rate",
            payload["prior_error_rate"],
        ),
        open_review_count=_decimal_from_public_payload(
            "open_review_count",
            payload["open_review_count"],
        ),
        dimension_rows=_dimension_rows_from_public_payload(payload["dimension_rows"]),
        derived_validation_digest=_string_from_public_payload(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_bool_from_public_payload("paper_only", payload["paper_only"]),
        report_only=_bool_from_public_payload("report_only", payload["report_only"]),
        readonly=_bool_from_public_payload("readonly", payload["readonly"]),
    )


def _dimension_rows_from_public_payload(
    value: object,
) -> tuple[TeamSpecialistResolutionAdjudicationReadinessDimensionRow, ...]:
    if type(value) is not list:
        raise ValueError("dimension_rows must be a list")
    return tuple(_dimension_row_from_public_payload(item) for item in value)


def _dimension_row_from_public_payload(
    value: object,
) -> TeamSpecialistResolutionAdjudicationReadinessDimensionRow:
    if type(value) is not dict:
        raise ValueError("dimension_rows must contain objects")
    _require_payload_fields(
        value,
        DIMENSION_ROW_PUBLIC_FIELDS,
        "dimension row fields must match readiness dimension row",
    )
    return TeamSpecialistResolutionAdjudicationReadinessDimensionRow(
        dimension_id=_string_from_public_payload("dimension_id", value["dimension_id"]),
        observed_value=_decimal_from_public_payload(
            "observed_value",
            value["observed_value"],
        ),
        threshold_value=_decimal_from_public_payload(
            "threshold_value",
            value["threshold_value"],
        ),
        dimension_status=_string_from_public_payload(
            "dimension_status",
            value["dimension_status"],
        ),
        reason_codes=_tuple_from_public_payload("reason_codes", value["reason_codes"]),
        paper_only=_bool_from_public_payload("paper_only", value["paper_only"]),
        report_only=_bool_from_public_payload("report_only", value["report_only"]),
        readonly=_bool_from_public_payload("readonly", value["readonly"]),
    )


def _require_payload_fields(
    payload: dict[str, Any],
    expected_fields: frozenset[str],
    message: str,
) -> None:
    if frozenset(payload) != expected_fields:
        raise ValueError(message)


def _string_from_public_payload(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _decimal_from_public_payload(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        return Decimal(value)
    except InvalidOperation:
        raise ValueError(f"{field_name} must be a Decimal string") from None


def _datetime_from_public_payload(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an ISO datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        raise ValueError(f"{field_name} must be an ISO datetime string") from None
    return _as_utc(field_name, parsed)


def _tuple_from_public_payload(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return tuple(value)


def _bool_from_public_payload(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _dimension_row(
    dimension_id: str,
    observed_value: Decimal,
    threshold_value: Decimal,
) -> TeamSpecialistResolutionAdjudicationReadinessDimensionRow:
    status = _dimension_status(dimension_id, observed_value, threshold_value)
    return TeamSpecialistResolutionAdjudicationReadinessDimensionRow(
        dimension_id=dimension_id,
        observed_value=observed_value,
        threshold_value=threshold_value,
        dimension_status=status,
        reason_codes=_dimension_reason_codes(dimension_id, status),
    )


def _dimension_status(
    dimension_id: str,
    observed_value: Decimal,
    threshold_value: Decimal,
) -> str:
    if dimension_id in MINIMUM_READY_DIMENSIONS:
        if observed_value >= threshold_value:
            return "pass"
        return "blocked"
    if dimension_id in MAXIMUM_READY_DIMENSIONS:
        if observed_value <= threshold_value:
            return "pass"
        return "blocked"
    raise ValueError("dimension_id must be supported")


def _dimension_reason_codes(
    dimension_id: str,
    dimension_status: str,
) -> tuple[str, ...]:
    if dimension_status == "pass":
        return (PASS_REASON_BY_DIMENSION[dimension_id],)
    return (BLOCK_REASON_BY_DIMENSION[dimension_id],)


def _report_reason_codes(
    rows: tuple[TeamSpecialistResolutionAdjudicationReadinessDimensionRow, ...],
) -> tuple[str, ...]:
    blocked_codes = {
        row.reason_codes[0] for row in rows if row.dimension_status == "blocked"
    }
    if not blocked_codes:
        return ("resolution_adjudication_readiness_clear",)
    return tuple(code for code in REPORT_REASON_CODES if code in blocked_codes)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("resolution_adjudication_readiness_clear",):
        return "pass"
    return "blocked"


def _normalize_dimension_rows(
    value: object,
) -> tuple[TeamSpecialistResolutionAdjudicationReadinessDimensionRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("dimension_rows must be a list or tuple")
    rows = tuple(value)
    if len(rows) != len(DIMENSION_IDS):
        raise ValueError("dimension_rows must cover every readiness dimension")
    for row in rows:
        if type(row) is not TeamSpecialistResolutionAdjudicationReadinessDimensionRow:
            raise ValueError(
                "dimension_rows must contain readiness dimension rows",
            )
        _require_hard_flags("dimension row", row)
    if tuple(row.dimension_id for row in rows) != DIMENSION_IDS:
        raise ValueError("dimension_rows must use deterministic dimension sequence")
    return rows


def _validate_report(report: TeamSpecialistResolutionAdjudicationReadinessReport) -> None:
    if report.ready_dimension_count != _count(
        sum(1 for row in report.dimension_rows if row.dimension_status == "pass"),
    ):
        raise ValueError("ready_dimension_count must match dimension_rows")
    if report.blocked_dimension_count != _count(
        sum(1 for row in report.dimension_rows if row.dimension_status == "blocked"),
    ):
        raise ValueError("blocked_dimension_count must match dimension_rows")
    if report.ready_dimension_count + report.blocked_dimension_count != _count(
        len(report.dimension_rows),
    ):
        raise ValueError("dimension counts must match dimension_rows")
    expected_reason_codes = _report_reason_codes(report.dimension_rows)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match dimension_rows")
    if report.readiness_status != _status_from_reason_codes(report.reason_codes):
        raise ValueError("readiness_status must match reason_codes")
    dimension_values = {row.dimension_id: row.observed_value for row in report.dimension_rows}
    if report.rule_familiarity_score != dimension_values["rule_familiarity"]:
        raise ValueError("rule_familiarity_score must match dimension_rows")
    if report.official_source_coverage_score != dimension_values["official_source_coverage"]:
        raise ValueError("official_source_coverage_score must match dimension_rows")
    if report.contradiction_handling_score != dimension_values["contradiction_handling"]:
        raise ValueError("contradiction_handling_score must match dimension_rows")
    if report.seconds_until_close != dimension_values["close_urgency"]:
        raise ValueError("seconds_until_close must match dimension_rows")
    if report.prior_error_rate != dimension_values["prior_error_rate"]:
        raise ValueError("prior_error_rate must match dimension_rows")
    if report.open_review_count != dimension_values["reviewer_load"]:
        raise ValueError("open_review_count must match dimension_rows")


def _normalize_dimension_value(
    dimension_id: str,
    field_name: str,
    value: object,
) -> Decimal:
    if dimension_id == "close_urgency":
        return _normalize_nonnegative_seconds(field_name, value)
    if dimension_id == "reviewer_load":
        return _normalize_nonnegative_count(field_name, value)
    return _normalize_unit_decimal(field_name, value)


def _normalize_row_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if len(reason_codes) != 1:
        raise ValueError("reason_codes must contain exactly one value")
    _require_member("reason_codes", reason_codes[0], ROW_REASON_CODES)
    return reason_codes


def _normalize_report_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_member("reason_codes", reason_code, REPORT_REASON_CODES)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    if tuple(code for code in REPORT_REASON_CODES if code in reason_codes) != reason_codes:
        raise ValueError("reason_codes must be deterministic")
    if (
        reason_codes[0] == "resolution_adjudication_readiness_clear"
        and len(reason_codes) != 1
    ):
        raise ValueError("clear reason must be exclusive")
    return reason_codes


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(COUNT_QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must be integral")
    if quantized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_RATIO or value > ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0 and 1")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _normalize_positive_seconds(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_seconds(field_name, value)
    if normalized <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_seconds(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(SECONDS_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if "://" in value or "?" in value:
        raise ValueError(f"{field_name} has unsafe public value")
    _reject_unsafe_public_text(field_name, value, is_key=False)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            item_path = field.name if not path else f"{path}.{field.name}"
            _reject_unsafe_public_text(item_path, field.name, is_key=True)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                item_path,
            )
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            _reject_unsafe_public_text(item_path, key, is_key=True)
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True for {label}")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if type(value) in (list, tuple):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(label, item, f"{current_path}[{index}]")
        return
    if type(value) is str:
        _reject_unsafe_public_text(current_path, value, is_key=False)
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{current_path} must be finite")
        return
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{current_path} must be timezone-aware")
        return
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        raise ValueError(f"{current_path} must use Decimal-derived string values")
    if type(value) is float:
        raise ValueError(f"{current_path} must not be a float")
    raise ValueError(f"{current_path} is not JSON serializable")


def _reject_unsafe_public_text(path: str, value: str, *, is_key: bool) -> None:
    lowered = value.lower()
    if value.strip() != value:
        raise ValueError(f"{path} has unsafe public value")
    for fragment in UNSAFE_PUBLIC_FRAGMENTS:
        if fragment in lowered:
            if is_key:
                raise ValueError(f"{path} has unsafe public field")
            raise ValueError(f"{path} has unsafe public value")


def _public_value(value: Any) -> Any:
    _reject_unsafe_public_payload("public payload", value)
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _public_value(getattr(value, field.name)) for field in fields(value)}
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal values must be finite")
        return str(value)
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime values must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            ready[key] = _public_value(item)
        return ready
    if type(value) in (list, tuple):
        return [_public_value(item) for item in value]
    if type(value) in (str, bool):
        return value
    if type(value) is int:
        raise ValueError("integer values must use Decimal-derived strings")
    if type(value) is float:
        raise ValueError("float values are not allowed")
    raise ValueError("value is not JSON serializable")


def _digest_for_report(
    report: TeamSpecialistResolutionAdjudicationReadinessReport,
) -> str:
    return _digest_for_public_payload(_public_value(report))


def _digest_for_public_payload(payload: Any) -> str:
    if type(payload) is not dict:
        raise ValueError("payload must be an object")
    payload_without_digest = {
        key: value for key, value in payload.items() if key != "derived_validation_digest"
    }
    canonical = json.dumps(
        payload_without_digest,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    for character in value:
        if character not in "0123456789abcdef":
            raise ValueError(f"{field_name} must be a sha256 hex digest")


__all__ = (
    "DEFAULT_TEAM_SPECIALIST_RESOLUTION_ADJUDICATION_READINESS_V2_CONFIG_VERSION",
    "DEFAULT_TEAM_SPECIALIST_RESOLUTION_ADJUDICATION_READINESS_V2_VERSION",
    "DIMENSION_IDS",
    "REPORT_REASON_CODES",
    "ROW_REASON_CODES",
    "STATUSES",
    "TeamSpecialistResolutionAdjudicationReadinessConfig",
    "TeamSpecialistResolutionAdjudicationReadinessDimensionRow",
    "TeamSpecialistResolutionAdjudicationReadinessInput",
    "TeamSpecialistResolutionAdjudicationReadinessReport",
    "build_team_specialist_resolution_adjudication_readiness_v2_report",
    "team_specialist_resolution_adjudication_readiness_v2_payload",
    "validate_team_specialist_resolution_adjudication_readiness_v2_payload",
)
