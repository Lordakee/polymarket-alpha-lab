"""Pure read-only quality gate for forecast revision rows."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_FORECAST_REVISION_QUALITY_GATE_CONFIG_VERSION = (
    "forecast-revision-quality-gate-v0"
)

GATE_STATUSES = ("pass", "watch", "blocked")
GATE_NEXT_STEPS = {
    "pass": "continue_forecast_revision_monitoring",
    "watch": "review_forecast_revision_cadence",
    "blocked": "block_forecast_revision_until_remediated",
}
REASON_CODES = (
    "forecast_revision_quality_gate_passed",
    "forecast_revision_quality_gate_empty_rows",
    "forecast_revision_quality_gate_stale_revision_present",
    "forecast_revision_quality_gate_missing_rationale_present",
    "forecast_revision_quality_gate_probability_delta_out_of_bounds_present",
    "forecast_revision_quality_gate_stale_unchanged_forecast_present",
    "forecast_revision_quality_gate_stale_revision",
    "forecast_revision_quality_gate_missing_rationale",
    "forecast_revision_quality_gate_probability_delta_out_of_bounds",
    "forecast_revision_quality_gate_stale_unchanged_forecast",
)
REPORT_REASON_CODES = REASON_CODES[:6]
ROW_REASON_CODES = (REASON_CODES[0],) + REASON_CODES[6:]
BLOCKING_ROW_REASON_CODES = frozenset(
    (
        "forecast_revision_quality_gate_missing_rationale",
        "forecast_revision_quality_gate_probability_delta_out_of_bounds",
        "forecast_revision_quality_gate_stale_unchanged_forecast",
    )
)
ROW_STATUS_WEIGHT = {"blocked": 0, "watch": 1, "pass": 2}
DECIMAL_CONTEXT = Context(prec=64)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MIN_RATIONALE_CHARACTER_COUNT = Decimal("1.000000")
UNSAFE_PUBLIC_SURFACE_TOKENS = (
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
    "trading",
    "trade",
    "buy",
    "sell",
)

__all__ = (
    "DEFAULT_FORECAST_REVISION_QUALITY_GATE_CONFIG_VERSION",
    "ForecastRevisionQualityGateConfig",
    "ForecastRevisionQualityGateReport",
    "ForecastRevisionQualityGateRow",
    "ForecastRevisionRow",
    "build_forecast_revision_quality_gate",
    "forecast_revision_quality_gate_payload",
)


@dataclass(frozen=True)
class ForecastRevisionQualityGateConfig:
    config_version: str = DEFAULT_FORECAST_REVISION_QUALITY_GATE_CONFIG_VERSION
    max_revision_age_hours: Decimal = Decimal("24.000000")
    stale_unchanged_age_hours: Decimal = Decimal("48.000000")
    max_abs_probability_delta: Decimal = Decimal("0.300000")
    min_rationale_character_count: Decimal = MIN_RATIONALE_CHARACTER_COUNT
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_safe_canonical_string("config_version", self.config_version)
        for field_name in (
            "max_revision_age_hours",
            "stale_unchanged_age_hours",
            "max_abs_probability_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_rationale_character_count",
            _require_positive_whole_decimal(
                "min_rationale_character_count",
                self.min_rationale_character_count,
            ),
        )
        _require_hard_flags("ForecastRevisionQualityGateConfig", self)


@dataclass(frozen=True)
class ForecastRevisionRow:
    forecast_id: str
    revision_sequence: Decimal
    prior_probability: Decimal
    revised_probability: Decimal
    probability_delta: Decimal
    revision_age_hours: Decimal
    revision_rationale: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_safe_canonical_string("forecast_id", self.forecast_id)
        object.__setattr__(
            self,
            "revision_sequence",
            _require_positive_whole_decimal("revision_sequence", self.revision_sequence),
        )
        object.__setattr__(
            self,
            "prior_probability",
            _require_probability_decimal("prior_probability", self.prior_probability),
        )
        object.__setattr__(
            self,
            "revised_probability",
            _require_probability_decimal("revised_probability", self.revised_probability),
        )
        object.__setattr__(
            self,
            "probability_delta",
            _require_signed_probability_decimal("probability_delta", self.probability_delta),
        )
        object.__setattr__(
            self,
            "revision_age_hours",
            _require_nonnegative_decimal("revision_age_hours", self.revision_age_hours),
        )
        if type(self.revision_rationale) is not str:
            raise ValueError("revision_rationale must be a string")
        _reject_unsafe_public_surface("revision_rationale", self.revision_rationale)
        _require_hard_flags("ForecastRevisionRow", self)
        _validate_revision_row_consistency(self)


@dataclass(frozen=True)
class ForecastRevisionQualityGateRow:
    forecast_id: str
    revision_sequence: Decimal
    prior_probability: Decimal
    revised_probability: Decimal
    probability_delta: Decimal
    revision_age_hours: Decimal
    revision_rationale_present: bool
    unchanged_forecast: bool
    gate_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_safe_canonical_string("forecast_id", self.forecast_id)
        object.__setattr__(
            self,
            "revision_sequence",
            _require_positive_whole_decimal("revision_sequence", self.revision_sequence),
        )
        object.__setattr__(
            self,
            "prior_probability",
            _require_probability_decimal("prior_probability", self.prior_probability),
        )
        object.__setattr__(
            self,
            "revised_probability",
            _require_probability_decimal("revised_probability", self.revised_probability),
        )
        object.__setattr__(
            self,
            "probability_delta",
            _require_signed_probability_decimal("probability_delta", self.probability_delta),
        )
        object.__setattr__(
            self,
            "revision_age_hours",
            _require_nonnegative_decimal("revision_age_hours", self.revision_age_hours),
        )
        if type(self.revision_rationale_present) is not bool:
            raise ValueError("revision_rationale_present must be a bool")
        if type(self.unchanged_forecast) is not bool:
            raise ValueError("unchanged_forecast must be a bool")
        _require_gate_status("gate_status", self.gate_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                self.reason_codes,
                allowed_reason_codes=ROW_REASON_CODES,
            ),
        )
        _require_hard_flags("ForecastRevisionQualityGateRow", self)
        _validate_gate_row_consistency(self)


@dataclass(frozen=True)
class ForecastRevisionQualityGateReport:
    generated_at: datetime
    config_version: str
    max_revision_age_hours: Decimal
    stale_unchanged_age_hours: Decimal
    max_abs_probability_delta: Decimal
    gate_status: str
    gate_next_step: str
    forecast_count: Decimal
    revision_count: Decimal
    passing_revision_count: Decimal
    watch_revision_count: Decimal
    blocked_revision_count: Decimal
    passing_revision_ratio: Decimal | None
    watch_revision_ratio: Decimal | None
    blocked_revision_ratio: Decimal | None
    reason_codes: tuple[str, ...]
    rows: tuple[ForecastRevisionQualityGateRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_safe_canonical_string("config_version", self.config_version)
        for field_name in (
            "max_revision_age_hours",
            "stale_unchanged_age_hours",
            "max_abs_probability_delta",
            "forecast_count",
            "revision_count",
            "passing_revision_count",
            "watch_revision_count",
            "blocked_revision_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_gate_status("gate_status", self.gate_status)
        _require_safe_canonical_string("gate_next_step", self.gate_next_step)
        for field_name in (
            "passing_revision_ratio",
            "watch_revision_ratio",
            "blocked_revision_ratio",
        ):
            _require_optional_probability_decimal(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                self.reason_codes,
                allowed_reason_codes=REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(self, "rows", _normalize_gate_rows(self.rows))
        _require_hard_flags("ForecastRevisionQualityGateReport", self)
        _validate_report_consistency(self)
        expected_digest = _derived_validation_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report fields")
        _require_digest("derived_validation_digest", self.derived_validation_digest)


def build_forecast_revision_quality_gate(
    revision_rows: tuple[ForecastRevisionRow, ...] | list[ForecastRevisionRow],
    *,
    config: ForecastRevisionQualityGateConfig,
    generated_at: datetime,
) -> ForecastRevisionQualityGateReport:
    if type(config) is not ForecastRevisionQualityGateConfig:
        raise ValueError("config must be a ForecastRevisionQualityGateConfig")
    _require_hard_flags("ForecastRevisionQualityGateConfig", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    revisions = _normalize_revision_rows(revision_rows)
    rows = tuple(
        sorted(
            (
                _build_gate_row(revision, config=config)
                for revision in revisions
            ),
            key=_gate_row_sort_key,
        )
    )
    reason_codes = _report_reason_codes(rows)
    gate_status = _gate_status(reason_codes)

    return ForecastRevisionQualityGateReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        max_revision_age_hours=config.max_revision_age_hours,
        stale_unchanged_age_hours=config.stale_unchanged_age_hours,
        max_abs_probability_delta=config.max_abs_probability_delta,
        gate_status=gate_status,
        gate_next_step=GATE_NEXT_STEPS[gate_status],
        forecast_count=_count_decimal(len({row.forecast_id for row in rows})),
        revision_count=_count_decimal(len(rows)),
        passing_revision_count=_count_decimal(_status_count(rows, "pass")),
        watch_revision_count=_count_decimal(_status_count(rows, "watch")),
        blocked_revision_count=_count_decimal(_status_count(rows, "blocked")),
        passing_revision_ratio=_optional_ratio(_status_count(rows, "pass"), len(rows)),
        watch_revision_ratio=_optional_ratio(_status_count(rows, "watch"), len(rows)),
        blocked_revision_ratio=_optional_ratio(_status_count(rows, "blocked"), len(rows)),
        reason_codes=reason_codes,
        rows=rows,
    )


def forecast_revision_quality_gate_payload(
    report: ForecastRevisionQualityGateReport,
) -> dict[str, Any]:
    if type(report) is not ForecastRevisionQualityGateReport:
        raise ValueError("report must be a ForecastRevisionQualityGateReport")
    payload = _json_ready(report)
    _reject_unsafe_public_payload("forecast revision quality gate payload", payload)
    if not isinstance(payload, dict):
        raise ValueError("forecast revision quality gate payload must be an object")
    return payload


def _build_gate_row(
    revision: ForecastRevisionRow,
    *,
    config: ForecastRevisionQualityGateConfig,
) -> ForecastRevisionQualityGateRow:
    unchanged_forecast = revision.prior_probability == revision.revised_probability
    rationale_present = (
        _count_decimal(len(revision.revision_rationale.strip()))
        >= config.min_rationale_character_count
    )
    reason_codes = _row_reason_codes(
        revision_age_hours=revision.revision_age_hours,
        rationale_present=rationale_present,
        abs_probability_delta=abs(revision.probability_delta),
        unchanged_forecast=unchanged_forecast,
        config=config,
    )
    gate_status = _row_gate_status(reason_codes)

    return ForecastRevisionQualityGateRow(
        forecast_id=revision.forecast_id,
        revision_sequence=revision.revision_sequence,
        prior_probability=revision.prior_probability,
        revised_probability=revision.revised_probability,
        probability_delta=revision.probability_delta,
        revision_age_hours=revision.revision_age_hours,
        revision_rationale_present=rationale_present,
        unchanged_forecast=unchanged_forecast,
        gate_status=gate_status,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    revision_age_hours: Decimal,
    rationale_present: bool,
    abs_probability_delta: Decimal,
    unchanged_forecast: bool,
    config: ForecastRevisionQualityGateConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if revision_age_hours > config.max_revision_age_hours:
        reason_codes.append("forecast_revision_quality_gate_stale_revision")
    if not rationale_present:
        reason_codes.append("forecast_revision_quality_gate_missing_rationale")
    if abs_probability_delta > config.max_abs_probability_delta:
        reason_codes.append("forecast_revision_quality_gate_probability_delta_out_of_bounds")
    if unchanged_forecast and revision_age_hours > config.stale_unchanged_age_hours:
        reason_codes.append("forecast_revision_quality_gate_stale_unchanged_forecast")
    return tuple(reason_codes or ("forecast_revision_quality_gate_passed",))


def _row_gate_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("forecast_revision_quality_gate_passed",):
        return "pass"
    if any(reason_code in BLOCKING_ROW_REASON_CODES for reason_code in reason_codes):
        return "blocked"
    return "watch"


def _report_reason_codes(
    rows: tuple[ForecastRevisionQualityGateRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("forecast_revision_quality_gate_empty_rows",)
    reason_codes: set[str] = set()
    for row in rows:
        for reason_code in row.reason_codes:
            report_reason = _report_reason_code(reason_code)
            if report_reason != "forecast_revision_quality_gate_passed":
                reason_codes.add(report_reason)
    return tuple(
        reason_code for reason_code in REPORT_REASON_CODES if reason_code in reason_codes
    ) or ("forecast_revision_quality_gate_passed",)


def _report_reason_code(reason_code: str) -> str:
    if reason_code == "forecast_revision_quality_gate_passed":
        return reason_code
    return f"{reason_code}_present"


def _gate_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("forecast_revision_quality_gate_passed",):
        return "pass"
    if reason_codes == ("forecast_revision_quality_gate_empty_rows",):
        return "blocked"
    if any(
        reason_code
        in (
            "forecast_revision_quality_gate_missing_rationale_present",
            "forecast_revision_quality_gate_probability_delta_out_of_bounds_present",
            "forecast_revision_quality_gate_stale_unchanged_forecast_present",
        )
        for reason_code in reason_codes
    ):
        return "blocked"
    return "watch"


def _status_count(rows: tuple[ForecastRevisionQualityGateRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.gate_status == status)


def _optional_ratio(numerator: int, denominator: int) -> Decimal | None:
    if denominator == 0:
        return None
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(Decimal(numerator) / Decimal(denominator))


def _count_decimal(value: int) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(Decimal(value))


def _validate_revision_row_consistency(row: ForecastRevisionRow) -> None:
    with localcontext(DECIMAL_CONTEXT):
        expected_delta = _quantize(row.revised_probability - row.prior_probability)
    if row.probability_delta != expected_delta:
        raise ValueError("probability_delta must match probability revision movement")


def _validate_gate_row_consistency(row: ForecastRevisionQualityGateRow) -> None:
    expected_status = _row_gate_status(row.reason_codes)
    if row.gate_status != expected_status:
        raise ValueError("gate_status must match reason_codes")
    with localcontext(DECIMAL_CONTEXT):
        expected_delta = _quantize(row.revised_probability - row.prior_probability)
    if row.probability_delta != expected_delta:
        raise ValueError("probability_delta must match probability revision movement")


def _validate_report_consistency(report: ForecastRevisionQualityGateReport) -> None:
    if report.gate_next_step != GATE_NEXT_STEPS[report.gate_status]:
        raise ValueError("gate_next_step must match gate_status")
    if report.forecast_count != _count_decimal(len({row.forecast_id for row in report.rows})):
        raise ValueError("forecast_count must match rows")
    if report.revision_count != _count_decimal(len(report.rows)):
        raise ValueError("revision_count must match rows")
    if report.passing_revision_count != _count_decimal(_status_count(report.rows, "pass")):
        raise ValueError("passing_revision_count must match rows")
    if report.watch_revision_count != _count_decimal(_status_count(report.rows, "watch")):
        raise ValueError("watch_revision_count must match rows")
    if report.blocked_revision_count != _count_decimal(_status_count(report.rows, "blocked")):
        raise ValueError("blocked_revision_count must match rows")
    if report.passing_revision_ratio != _optional_ratio(
        _status_count(report.rows, "pass"),
        len(report.rows),
    ):
        raise ValueError("passing_revision_ratio must match counts")
    if report.watch_revision_ratio != _optional_ratio(
        _status_count(report.rows, "watch"),
        len(report.rows),
    ):
        raise ValueError("watch_revision_ratio must match counts")
    if report.blocked_revision_ratio != _optional_ratio(
        _status_count(report.rows, "blocked"),
        len(report.rows),
    ):
        raise ValueError("blocked_revision_ratio must match counts")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.gate_status != _gate_status(report.reason_codes):
        raise ValueError("gate_status must match reason_codes")


def _normalize_revision_rows(
    rows: tuple[ForecastRevisionRow, ...] | list[ForecastRevisionRow],
) -> tuple[ForecastRevisionRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("revision_rows must be a list or tuple")
    normalized = tuple(rows)
    seen_keys: set[tuple[str, Decimal]] = set()
    for row in normalized:
        if type(row) is not ForecastRevisionRow:
            raise ValueError("revision_rows must contain ForecastRevisionRow")
        _require_hard_flags("ForecastRevisionRow", row)
        _reject_unsafe_public_payload("revision_rows", _json_ready(row))
        key = (row.forecast_id, row.revision_sequence)
        if key in seen_keys:
            raise ValueError("forecast_id and revision_sequence pairs must be unique")
        seen_keys.add(key)
    return normalized


def _normalize_gate_rows(
    rows: tuple[ForecastRevisionQualityGateRow, ...],
) -> tuple[ForecastRevisionQualityGateRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ForecastRevisionQualityGateRow:
            raise ValueError("rows must contain ForecastRevisionQualityGateRow")
        _require_hard_flags("ForecastRevisionQualityGateRow", row)
        _reject_unsafe_public_payload("rows", _json_ready(row))
    if normalized != tuple(sorted(normalized, key=_gate_row_sort_key)):
        raise ValueError("rows must use deterministic revision quality sort")
    return normalized


def _normalize_reason_codes(
    value: object,
    *,
    allowed_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    normalized = tuple(value)
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    for reason_code in normalized:
        _require_safe_canonical_string("reason_codes", reason_code)
        if reason_code not in allowed_reason_codes:
            raise ValueError("reason_codes must contain known reason codes")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    expected = tuple(reason_code for reason_code in allowed_reason_codes if reason_code in normalized)
    if normalized != expected:
        raise ValueError("reason_codes must use deterministic reason sequence")
    return normalized


def _gate_row_sort_key(row: ForecastRevisionQualityGateRow) -> tuple[int, str, Decimal]:
    return (
        ROW_STATUS_WEIGHT[row.gate_status],
        row.forecast_id,
        row.revision_sequence,
    )


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_gate_status(field_name: str, value: object) -> None:
    _require_safe_canonical_string(field_name, value)
    if value not in GATE_STATUSES:
        raise ValueError(f"{field_name} must be a known gate status")


def _require_safe_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _reject_unsafe_public_surface(field_name, value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite() or value < ZERO:
        raise ValueError(f"{field_name} must be finite and nonnegative")
    return _quantize(value)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= ZERO or normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a positive whole Decimal")
    return normalized


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite() or value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return _quantize(value)


def _require_signed_probability_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite() or value < -ONE or value > ONE:
        raise ValueError(f"{field_name} must be between negative one and one")
    return _quantize(value)


def _require_optional_probability_decimal(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_probability_decimal(field_name, value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")


def _derived_validation_digest(report: ForecastRevisionQualityGateReport) -> str:
    digest_payload = _json_ready(report, exclude_report_digest=True)
    encoded = json.dumps(
        digest_payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: object, *, exclude_report_digest: bool = False) -> Any:
    if isinstance(value, Decimal):
        return format(value, ".6f")
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    if isinstance(value, tuple):
        return [
            _json_ready(item, exclude_report_digest=exclude_report_digest)
            for item in value
        ]
    if isinstance(value, list):
        return [
            _json_ready(item, exclude_report_digest=exclude_report_digest)
            for item in value
        ]
    if hasattr(value, "__dataclass_fields__"):
        return {
            field_name: _json_ready(
                getattr(value, field_name),
                exclude_report_digest=exclude_report_digest,
            )
            for field_name in value.__dataclass_fields__
            if not (
                exclude_report_digest
                and type(value) is ForecastRevisionQualityGateReport
                and field_name == "derived_validation_digest"
            )
        }
    return value


def _reject_unsafe_public_surface(field_name: str, value: str) -> None:
    lowered_value = value.casefold()
    for token in UNSAFE_PUBLIC_SURFACE_TOKENS:
        if token in lowered_value:
            raise ValueError(f"{field_name} contains unsafe surface")


def _reject_unsafe_public_payload(field_name: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError(f"{field_name} payload keys must be strings")
            _reject_unsafe_public_surface(field_name, key)
            _reject_unsafe_public_payload(field_name, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(field_name, item)
        return
    if isinstance(value, str):
        _reject_unsafe_public_surface(field_name, value)
