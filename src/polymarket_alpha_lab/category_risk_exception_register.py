"""Read-only category risk exception register for Phase 1 review queues."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_CATEGORY_RISK_EXCEPTION_REGISTER_CONFIG_VERSION = (
    "category-risk-exception-register-v0"
)
CATEGORY_RISK_EXCEPTION_REGISTER_CATEGORIES = (
    "politics",
    "crypto",
    "macro",
    "commodities",
    "sports",
)
RISK_STATUSES = ("pass", "watch", "blocked")
SEVERITY_BUCKETS = ("low", "medium", "high", "critical")
ROW_REASON_CODES = (
    "category_risk_pass",
    "category_risk_watch",
    "category_risk_blocked",
    "category_review_queue_present",
)
INPUT_REASON_CODES = (
    "risk_exception_pass",
    "risk_exception_watch",
    "risk_exception_blocked",
)
REPORT_REASON_CODES = (
    "risk_exception_register_clear",
    "risk_exceptions_watch",
    "risk_exceptions_blocked",
    "risk_review_queue_present",
)

COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
LOW_MAX = Decimal("0.000000")
MEDIUM_MAX = Decimal("0.499999")
HIGH_MAX = Decimal("0.799999")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SHA256_HEX_LENGTH = 64
SHA256_HEX_CHARACTERS = frozenset("0123456789abcdef")

TEAM_TO_CATEGORY = {
    "politics": "politics",
    "crypto_btc": "crypto",
    "crypto_eth": "crypto",
    "macro_rates": "macro",
    "commodities_gold": "commodities",
    "commodities_oil": "commodities",
    "sports_soccer": "sports",
    "sports_basketball": "sports",
    "sports_other": "sports",
}
STATUS_WEIGHT = {
    "pass": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "blocked": Decimal("2.000000"),
}
BUCKET_WEIGHT = {
    "low": Decimal("0.000000"),
    "medium": Decimal("1.000000"),
    "high": Decimal("2.000000"),
    "critical": Decimal("3.000000"),
}


@dataclass(frozen=True)
class CategoryRiskExceptionRegisterConfig:
    config_version: str = DEFAULT_CATEGORY_RISK_EXCEPTION_REGISTER_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        require_paper_only_flags("CategoryRiskExceptionRegisterConfig", self)


@dataclass(frozen=True)
class CategoryRiskExceptionRegisterInput:
    team_id: str
    category_id: str
    exception_count: Decimal
    risk_status: str
    severity_score: Decimal
    review_queue_count: Decimal
    source_row_count: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_known_team_id("team_id", self.team_id)
        _require_category_id("category_id", self.category_id)
        if TEAM_TO_CATEGORY[self.team_id] != self.category_id:
            raise ValueError("team_id must match category_id")
        object.__setattr__(
            self,
            "exception_count",
            _normalize_nonnegative_count("exception_count", self.exception_count),
        )
        _require_member("risk_status", self.risk_status, RISK_STATUSES)
        object.__setattr__(
            self,
            "severity_score",
            _normalize_ratio("severity_score", self.severity_score),
        )
        object.__setattr__(
            self,
            "review_queue_count",
            _normalize_nonnegative_count("review_queue_count", self.review_queue_count),
        )
        object.__setattr__(
            self,
            "source_row_count",
            _normalize_nonnegative_count("source_row_count", self.source_row_count),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                INPUT_REASON_CODES,
            ),
        )
        _validate_input(self)
        require_paper_only_flags("CategoryRiskExceptionRegisterInput", self)


@dataclass(frozen=True)
class CategoryRiskExceptionRegisterRow:
    category_id: str
    team_count: Decimal
    source_row_count: Decimal
    exception_count: Decimal
    review_queue_count: Decimal
    severity_score: Decimal
    severity_bucket: str
    risk_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_category_id("category_id", self.category_id)
        for field_name in (
            "team_count",
            "source_row_count",
            "exception_count",
            "review_queue_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "severity_score",
            _normalize_ratio("severity_score", self.severity_score),
        )
        _require_member("severity_bucket", self.severity_bucket, SEVERITY_BUCKETS)
        _require_member("risk_status", self.risk_status, RISK_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        require_paper_only_flags("CategoryRiskExceptionRegisterRow", self)


@dataclass(frozen=True)
class CategoryRiskExceptionRegisterReport:
    generated_at: datetime
    config_version: str
    source_row_count: Decimal
    category_count: Decimal
    exception_count: Decimal
    review_queue_count: Decimal
    low_severity_count: Decimal
    medium_severity_count: Decimal
    high_severity_count: Decimal
    critical_severity_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    category_rows: tuple[CategoryRiskExceptionRegisterRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "source_row_count",
            "category_count",
            "exception_count",
            "review_queue_count",
            "low_severity_count",
            "medium_severity_count",
            "high_severity_count",
            "critical_severity_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, RISK_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(
            self,
            "category_rows",
            _normalize_rows(self.category_rows),
        )
        _validate_report(self)
        _normalize_report_derived_validation_digest(self)
        reject_unsafe_surface_fields("category risk exception register report", self)
        require_paper_only_flags("CategoryRiskExceptionRegisterReport", self)


def build_category_risk_exception_register_report(
    inputs: list[CategoryRiskExceptionRegisterInput]
    | tuple[CategoryRiskExceptionRegisterInput, ...],
    *,
    config: CategoryRiskExceptionRegisterConfig,
    generated_at: datetime,
) -> CategoryRiskExceptionRegisterReport:
    if type(config) is not CategoryRiskExceptionRegisterConfig:
        raise ValueError("config must be a CategoryRiskExceptionRegisterConfig")
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _normalize_inputs(inputs)
    category_rows = tuple(
        sorted(
            (
                _category_row(category_id, category_inputs)
                for category_id, category_inputs in _category_groups(rows)
                if category_inputs
            ),
            key=_category_row_sort_key,
        ),
    )
    return CategoryRiskExceptionRegisterReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_row_count=_sum_rows(category_rows, "source_row_count"),
        category_count=_count(len(category_rows)),
        exception_count=_sum_rows(category_rows, "exception_count"),
        review_queue_count=_sum_rows(category_rows, "review_queue_count"),
        low_severity_count=_bucket_count(category_rows, "low"),
        medium_severity_count=_bucket_count(category_rows, "medium"),
        high_severity_count=_bucket_count(category_rows, "high"),
        critical_severity_count=_bucket_count(category_rows, "critical"),
        status=_status_rollup(tuple(row.risk_status for row in category_rows)),
        reason_codes=_report_reason_codes(category_rows),
        category_rows=category_rows,
    )


def category_risk_exception_register_payload(
    report: CategoryRiskExceptionRegisterReport,
) -> dict[str, Any]:
    if type(report) is not CategoryRiskExceptionRegisterReport:
        raise ValueError("report must be a CategoryRiskExceptionRegisterReport")
    require_paper_only_flags("report", report)
    reject_unsafe_surface_fields("category risk exception register report", report)
    _validate_report_derived_validation_digest(report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("category risk exception register payload must be an object")
    reject_unsafe_surface_fields("category risk exception register payload", payload)
    return payload


def _normalize_inputs(
    inputs: list[CategoryRiskExceptionRegisterInput]
    | tuple[CategoryRiskExceptionRegisterInput, ...],
) -> tuple[CategoryRiskExceptionRegisterInput, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(inputs)
    seen_team_ids: set[str] = set()
    for row in rows:
        if type(row) is not CategoryRiskExceptionRegisterInput:
            raise ValueError(
                "inputs must contain CategoryRiskExceptionRegisterInput values",
            )
        require_paper_only_flags("input", row)
        if row.team_id in seen_team_ids:
            raise ValueError("inputs must not contain duplicate team_id values")
        seen_team_ids.add(row.team_id)
    return rows


def _category_groups(
    rows: tuple[CategoryRiskExceptionRegisterInput, ...],
) -> tuple[tuple[str, tuple[CategoryRiskExceptionRegisterInput, ...]], ...]:
    return tuple(
        (
            category_id,
            tuple(row for row in rows if row.category_id == category_id),
        )
        for category_id in CATEGORY_RISK_EXCEPTION_REGISTER_CATEGORIES
    )


def _category_row(
    category_id: str,
    rows: tuple[CategoryRiskExceptionRegisterInput, ...],
) -> CategoryRiskExceptionRegisterRow:
    exception_count = _sum_inputs(rows, "exception_count")
    review_queue_count = _sum_inputs(rows, "review_queue_count")
    severity_score = _max_ratio(tuple(row.severity_score for row in rows))
    risk_status = _status_rollup(tuple(row.risk_status for row in rows))
    return CategoryRiskExceptionRegisterRow(
        category_id=category_id,
        team_count=_count(len(rows)),
        source_row_count=_sum_inputs(rows, "source_row_count"),
        exception_count=exception_count,
        review_queue_count=review_queue_count,
        severity_score=severity_score,
        severity_bucket=_severity_bucket(severity_score),
        risk_status=risk_status,
        reason_codes=_row_reason_codes(risk_status, review_queue_count),
    )


def _row_reason_codes(risk_status: str, review_queue_count: Decimal) -> tuple[str, ...]:
    codes = [f"category_risk_{risk_status}"]
    if review_queue_count > ZERO_COUNT:
        codes.append("category_review_queue_present")
    return tuple(codes)


def _report_reason_codes(
    rows: tuple[CategoryRiskExceptionRegisterRow, ...],
) -> tuple[str, ...]:
    if not rows or all(row.exception_count == ZERO_COUNT for row in rows):
        return ("risk_exception_register_clear",)
    codes: list[str] = []
    status = _status_rollup(tuple(row.risk_status for row in rows))
    if status == "blocked":
        codes.append("risk_exceptions_blocked")
    elif status == "watch":
        codes.append("risk_exceptions_watch")
    if any(row.review_queue_count > ZERO_COUNT for row in rows):
        codes.append("risk_review_queue_present")
    return tuple(codes)


def _category_row_sort_key(
    row: CategoryRiskExceptionRegisterRow,
) -> tuple[Decimal, Decimal, Decimal, Decimal, str]:
    return (
        -STATUS_WEIGHT[row.risk_status],
        -BUCKET_WEIGHT[row.severity_bucket],
        -row.exception_count,
        -row.review_queue_count,
        row.category_id,
    )


def _status_rollup(statuses: tuple[str, ...]) -> str:
    if any(status == "blocked" for status in statuses):
        return "blocked"
    if any(status == "watch" for status in statuses):
        return "watch"
    return "pass"


def _severity_bucket(severity_score: Decimal) -> str:
    if severity_score <= LOW_MAX:
        return "low"
    if severity_score <= MEDIUM_MAX:
        return "medium"
    if severity_score <= HIGH_MAX:
        return "high"
    return "critical"


def _max_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_RATIO
    return _normalize_ratio("severity_score", max(values))


def _sum_inputs(
    rows: tuple[CategoryRiskExceptionRegisterInput, ...],
    field_name: str,
) -> Decimal:
    return _normalize_nonnegative_count(
        field_name,
        sum((getattr(row, field_name) for row in rows), ZERO_COUNT),
    )


def _sum_rows(
    rows: tuple[CategoryRiskExceptionRegisterRow, ...],
    field_name: str,
) -> Decimal:
    return _normalize_nonnegative_count(
        field_name,
        sum((getattr(row, field_name) for row in rows), ZERO_COUNT),
    )


def _bucket_count(
    rows: tuple[CategoryRiskExceptionRegisterRow, ...],
    severity_bucket: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.severity_bucket == severity_bucket))


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _validate_input(row: CategoryRiskExceptionRegisterInput) -> None:
    expected_reason_code = f"risk_exception_{row.risk_status}"
    if row.reason_codes != (expected_reason_code,):
        raise ValueError("reason_codes must match risk_status")
    if row.review_queue_count > row.exception_count:
        if row.exception_count == ZERO_COUNT:
            raise ValueError("review_queue_count requires exceptions")
        raise ValueError("review_queue_count must not exceed exception_count")
    if row.risk_status == "blocked" and row.exception_count == ZERO_COUNT:
        raise ValueError("blocked rows require exceptions")
    if row.risk_status == "watch" and row.exception_count == ZERO_COUNT:
        raise ValueError("watch rows require exceptions")
    if row.risk_status == "pass" and row.severity_score != ZERO_RATIO:
        raise ValueError("pass rows must use zero severity")
    if row.exception_count == ZERO_COUNT and row.severity_score != ZERO_RATIO:
        raise ValueError("severity_score requires exceptions")


def _validate_row(row: CategoryRiskExceptionRegisterRow) -> None:
    if row.review_queue_count > row.exception_count:
        raise ValueError("review_queue_count must not exceed exception_count")
    if row.exception_count == ZERO_COUNT:
        if row.review_queue_count != ZERO_COUNT:
            raise ValueError("review_queue_count requires exceptions")
        if row.risk_status != "pass":
            raise ValueError("empty category rows must pass")
        if row.severity_bucket != "low":
            raise ValueError("empty category rows must use low severity")
    if row.severity_bucket != _severity_bucket(row.severity_score):
        raise ValueError("severity_bucket must match severity_score")
    if row.reason_codes != _row_reason_codes(row.risk_status, row.review_queue_count):
        raise ValueError("reason_codes must match row status")


def _validate_report(report: CategoryRiskExceptionRegisterReport) -> None:
    if report.category_count != _count(len(report.category_rows)):
        raise ValueError("category_count must match category_rows")
    if report.source_row_count != _sum_rows(report.category_rows, "source_row_count"):
        raise ValueError("source_row_count must match category_rows")
    if report.exception_count != _sum_rows(report.category_rows, "exception_count"):
        raise ValueError("exception_count must match category_rows")
    if report.review_queue_count != _sum_rows(report.category_rows, "review_queue_count"):
        raise ValueError("review_queue_count must match category_rows")
    for field_name, severity_bucket in (
        ("low_severity_count", "low"),
        ("medium_severity_count", "medium"),
        ("high_severity_count", "high"),
        ("critical_severity_count", "critical"),
    ):
        if getattr(report, field_name) != _bucket_count(report.category_rows, severity_bucket):
            raise ValueError(f"{field_name} must match category_rows")
    if report.status != _status_rollup(tuple(row.risk_status for row in report.category_rows)):
        raise ValueError("status must match category_rows")
    if report.reason_codes != _report_reason_codes(report.category_rows):
        raise ValueError("reason_codes must match category_rows")
    if report.category_rows != tuple(
        sorted(report.category_rows, key=_category_row_sort_key),
    ):
        raise ValueError("category_rows must use deterministic ordering")


def _normalize_report_derived_validation_digest(
    report: CategoryRiskExceptionRegisterReport,
) -> None:
    expected_digest = _report_derived_validation_digest(report)
    if report.derived_validation_digest == "":
        object.__setattr__(report, "derived_validation_digest", expected_digest)
        return
    _require_sha256_hex("derived_validation_digest", report.derived_validation_digest)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")


def _validate_report_derived_validation_digest(
    report: CategoryRiskExceptionRegisterReport,
) -> None:
    _require_sha256_hex("derived_validation_digest", report.derived_validation_digest)
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _report_derived_validation_digest(
    report: CategoryRiskExceptionRegisterReport,
) -> str:
    payload = json_ready_no_floats(asdict(report))
    if type(payload) is not dict:
        raise ValueError("category risk exception register digest payload must be an object")
    payload.pop("derived_validation_digest", None)
    rendered = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _require_sha256_hex(field_name: str, value: object) -> str:
    if type(value) is not str or len(value) != SHA256_HEX_LENGTH:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    if any(character not in SHA256_HEX_CHARACTERS for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _normalize_rows(value: object) -> tuple[CategoryRiskExceptionRegisterRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("category_rows must be a tuple")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("category_rows must be a tuple") from exc
    for row in rows:
        if type(row) is not CategoryRiskExceptionRegisterRow:
            raise ValueError(
                "category_rows must contain CategoryRiskExceptionRegisterRow values",
            )
        require_paper_only_flags("category row", row)
    return rows


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        _require_member(field_name, reason_code, allowed)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    if tuple(code for code in allowed if code in reason_codes) != reason_codes:
        raise ValueError(f"{field_name} must be deterministic")
    return reason_codes


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


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_RATIO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_category_id(field_name: str, value: object) -> None:
    _require_member(field_name, value, CATEGORY_RISK_EXCEPTION_REGISTER_CATEGORIES)


def _require_known_team_id(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in TEAM_TO_CATEGORY:
        raise ValueError(f"{field_name} must be a known Phase 1 team")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


__all__ = (
    "DEFAULT_CATEGORY_RISK_EXCEPTION_REGISTER_CONFIG_VERSION",
    "CATEGORY_RISK_EXCEPTION_REGISTER_CATEGORIES",
    "CategoryRiskExceptionRegisterConfig",
    "CategoryRiskExceptionRegisterInput",
    "CategoryRiskExceptionRegisterReport",
    "CategoryRiskExceptionRegisterRow",
    "build_category_risk_exception_register_report",
    "category_risk_exception_register_payload",
)
