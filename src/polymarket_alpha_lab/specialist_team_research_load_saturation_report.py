"""Pure readonly specialist team research load saturation report."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


CONFIG_VERSION = "specialist-team-research-load-saturation-report-v1"
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

LOAD_STATUSES = ("pass", "watch", "block")
REASON_CODES = (
    "specialist_research_load_clear",
    "no_available_specialists",
    "specialist_capacity_watch",
    "specialist_capacity_block",
    "urgent_research_items_present",
    "blocked_research_items_present",
    "research_age_watch",
    "research_age_block",
)
PUBLIC_CODE_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789_")
DIGEST_LENGTH = 64

WATCH_SATURATION_RATIO = Decimal("2.000000")
BLOCK_SATURATION_RATIO = Decimal("4.000000")
WATCH_AGE_HOURS = Decimal("24.000000")
BLOCK_AGE_HOURS = Decimal("72.000000")

NEXT_STEP_BY_STATUS = {
    "pass": "Manual review only; keep the specialist team load report on file.",
    "watch": "Manually rebalance specialist coverage before accepting new research intake.",
    "block": "Manually pause new research intake and assign specialist coverage.",
}

PAYLOAD_KEYS = (
    "generated_at",
    "config_version",
    "team_id",
    "open_research_items",
    "available_specialists",
    "urgent_items",
    "blocked_items",
    "average_age_hours",
    "load_status",
    "saturation_ratio",
    "reason_codes",
    "manual_next_step",
    "validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class SpecialistTeamResearchLoadSaturationReport:
    generated_at: datetime
    config_version: str
    team_id: str
    open_research_items: Decimal
    available_specialists: Decimal
    urgent_items: Decimal
    blocked_items: Decimal
    average_age_hours: Decimal
    load_status: str
    saturation_ratio: Decimal
    reason_codes: tuple[str, ...]
    manual_next_step: str
    validation_digest: str
    payload: dict[str, Any]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, SpecialistTeamResearchLoadSaturationReport, "report")
        object.__setattr__(self, "generated_at", _normalize_datetime(self.generated_at))
        if self.config_version != CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _require_public_code("team_id", self.team_id)
        for field_name in (
            "open_research_items",
            "available_specialists",
            "urgent_items",
            "blocked_items",
            "average_age_hours",
            "saturation_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _validate_item_counts(self)
        _require_load_status("load_status", self.load_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        if type(self.manual_next_step) is not str or not self.manual_next_step:
            raise ValueError("manual_next_step must be a non-empty string")
        _require_sha256_digest("validation_digest", self.validation_digest)
        if type(self.payload) is not dict:
            raise ValueError("payload must be a plain dict")
        _require_hard_flags("report", self)
        _validate_report(self)


def build_specialist_team_research_load_saturation_report(
    *,
    team_id: str,
    open_research_items: Decimal,
    available_specialists: Decimal,
    urgent_items: Decimal,
    blocked_items: Decimal,
    average_age_hours: Decimal,
    generated_at: datetime | None = None,
) -> SpecialistTeamResearchLoadSaturationReport:
    generated_at_utc = _normalize_datetime(generated_at if generated_at is not None else datetime.now(UTC))
    normalized_open = _normalize_nonnegative_decimal("open_research_items", open_research_items)
    normalized_available = _normalize_nonnegative_decimal(
        "available_specialists",
        available_specialists,
    )
    normalized_urgent = _normalize_nonnegative_decimal("urgent_items", urgent_items)
    normalized_blocked = _normalize_nonnegative_decimal("blocked_items", blocked_items)
    normalized_age = _normalize_nonnegative_decimal("average_age_hours", average_age_hours)
    values = {
        "generated_at": generated_at_utc,
        "config_version": CONFIG_VERSION,
        "team_id": _require_public_code("team_id", team_id),
        "open_research_items": normalized_open,
        "available_specialists": normalized_available,
        "urgent_items": normalized_urgent,
        "blocked_items": normalized_blocked,
        "average_age_hours": normalized_age,
        "saturation_ratio": _saturation_ratio(normalized_open, normalized_available),
    }
    _validate_raw_item_counts(
        open_research_items=values["open_research_items"],
        urgent_items=values["urgent_items"],
        blocked_items=values["blocked_items"],
    )
    reason_codes = _reason_codes(
        open_research_items=values["open_research_items"],
        available_specialists=values["available_specialists"],
        urgent_items=values["urgent_items"],
        blocked_items=values["blocked_items"],
        average_age_hours=values["average_age_hours"],
        saturation_ratio=values["saturation_ratio"],
    )
    load_status = _load_status(reason_codes)
    values["load_status"] = load_status
    values["reason_codes"] = reason_codes
    values["manual_next_step"] = NEXT_STEP_BY_STATUS[load_status]
    digest = _validation_digest(values)
    payload = _payload_from_values(values, digest)
    return SpecialistTeamResearchLoadSaturationReport(
        **values,
        validation_digest=digest,
        payload=payload,
    )


def specialist_team_research_load_saturation_report_payload(
    report: SpecialistTeamResearchLoadSaturationReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is SpecialistTeamResearchLoadSaturationReport:
        _require_hard_flags("report", report)
        expected_digest = _validation_digest(_values_from_report(report))
        if report.validation_digest != expected_digest:
            raise ValueError("validation_digest mismatch for report")
        expected_payload = _payload_from_values(_values_from_report(report), report.validation_digest)
        if report.payload != expected_payload:
            raise ValueError("payload mismatch for report")
        return dict(expected_payload)
    if type(report) is dict:
        _validate_payload_schema(report)
        _reject_public_numeric_values(report)
        _require_hard_flags("payload", report)
        expected_digest = _payload_digest_without_digest(report)
        if report["validation_digest"] != expected_digest:
            raise ValueError("validation_digest mismatch for saturation_ratio or payload fields")
        return dict(report)
    raise ValueError(
        "report must be a SpecialistTeamResearchLoadSaturationReport or payload dict",
    )


def _saturation_ratio(open_research_items: Decimal, available_specialists: Decimal) -> Decimal:
    if available_specialists == ZERO:
        return open_research_items
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_nonnegative_decimal(
            "saturation_ratio",
            open_research_items / available_specialists,
        )


def _reason_codes(
    *,
    open_research_items: Decimal,
    available_specialists: Decimal,
    urgent_items: Decimal,
    blocked_items: Decimal,
    average_age_hours: Decimal,
    saturation_ratio: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if available_specialists == ZERO and open_research_items > ZERO:
        reasons.append("no_available_specialists")
    if saturation_ratio >= BLOCK_SATURATION_RATIO or (
        available_specialists == ZERO and open_research_items > ZERO
    ):
        reasons.append("specialist_capacity_block")
    elif saturation_ratio >= WATCH_SATURATION_RATIO:
        reasons.append("specialist_capacity_watch")
    if urgent_items > ZERO:
        reasons.append("urgent_research_items_present")
    if blocked_items > ZERO:
        reasons.append("blocked_research_items_present")
    if average_age_hours >= BLOCK_AGE_HOURS:
        reasons.append("research_age_block")
    elif average_age_hours >= WATCH_AGE_HOURS:
        reasons.append("research_age_watch")
    if not reasons:
        reasons.append("specialist_research_load_clear")
    return _normalize_reason_codes(tuple(reasons))


def _load_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if "no_available_specialists" in reason_codes:
        return "block"
    if reason_codes != ("specialist_research_load_clear",):
        return "watch"
    return "pass"


def _validate_report(report: SpecialistTeamResearchLoadSaturationReport) -> None:
    if report.saturation_ratio != _saturation_ratio(
        report.open_research_items,
        report.available_specialists,
    ):
        raise ValueError("saturation_ratio must match load inputs")
    expected_reasons = _reason_codes(
        open_research_items=report.open_research_items,
        available_specialists=report.available_specialists,
        urgent_items=report.urgent_items,
        blocked_items=report.blocked_items,
        average_age_hours=report.average_age_hours,
        saturation_ratio=report.saturation_ratio,
    )
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match load inputs")
    if report.load_status != _load_status(report.reason_codes):
        raise ValueError("load_status must match reason_codes")
    if report.manual_next_step != NEXT_STEP_BY_STATUS[report.load_status]:
        raise ValueError("manual_next_step must match load_status")
    expected_payload = _payload_from_values(_values_from_report(report), report.validation_digest)
    if report.payload != expected_payload:
        raise ValueError("payload must match report fields")
    if report.validation_digest != _validation_digest(_values_from_report(report)):
        raise ValueError("validation_digest must match report fields")


def _validate_item_counts(report: SpecialistTeamResearchLoadSaturationReport) -> None:
    _validate_raw_item_counts(
        open_research_items=report.open_research_items,
        urgent_items=report.urgent_items,
        blocked_items=report.blocked_items,
    )


def _validate_raw_item_counts(
    *,
    open_research_items: Decimal,
    urgent_items: Decimal,
    blocked_items: Decimal,
) -> None:
    if blocked_items > open_research_items:
        raise ValueError("blocked_items cannot exceed open_research_items")
    if urgent_items > open_research_items:
        raise ValueError("urgent_items cannot exceed open_research_items")


def _values_from_report(report: SpecialistTeamResearchLoadSaturationReport) -> dict[str, Any]:
    return {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "team_id": report.team_id,
        "open_research_items": report.open_research_items,
        "available_specialists": report.available_specialists,
        "urgent_items": report.urgent_items,
        "blocked_items": report.blocked_items,
        "average_age_hours": report.average_age_hours,
        "load_status": report.load_status,
        "saturation_ratio": report.saturation_ratio,
        "reason_codes": report.reason_codes,
        "manual_next_step": report.manual_next_step,
    }


def _validation_digest(values: dict[str, Any]) -> str:
    payload = _payload_without_digest(values)
    payload["paper_only"] = True
    payload["report_only"] = True
    payload["readonly"] = True
    return _payload_digest_without_digest(payload)


def _payload_from_values(values: dict[str, Any], validation_digest: str) -> dict[str, Any]:
    payload = _payload_without_digest(values)
    payload["validation_digest"] = validation_digest
    payload["paper_only"] = True
    payload["report_only"] = True
    payload["readonly"] = True
    return payload


def _payload_without_digest(values: dict[str, Any]) -> dict[str, Any]:
    return {
        "generated_at": _normalize_datetime(values["generated_at"]).isoformat(),
        "config_version": values["config_version"],
        "team_id": values["team_id"],
        "open_research_items": _decimal_payload(values["open_research_items"]),
        "available_specialists": _decimal_payload(values["available_specialists"]),
        "urgent_items": _decimal_payload(values["urgent_items"]),
        "blocked_items": _decimal_payload(values["blocked_items"]),
        "average_age_hours": _decimal_payload(values["average_age_hours"]),
        "load_status": values["load_status"],
        "saturation_ratio": _decimal_payload(values["saturation_ratio"]),
        "reason_codes": list(values["reason_codes"]),
        "manual_next_step": values["manual_next_step"],
    }


def _payload_digest_without_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("validation_digest", None)
    encoded = json.dumps(
        digest_payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_payload_schema(payload: dict[str, Any]) -> None:
    if tuple(payload.keys()) != PAYLOAD_KEYS:
        raise ValueError("payload schema must match specialist team research load report")
    _require_sha256_digest("validation_digest", payload["validation_digest"])
    if payload["config_version"] != CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")
    _require_public_code("team_id", payload["team_id"])
    for field_name in (
        "open_research_items",
        "available_specialists",
        "urgent_items",
        "blocked_items",
        "average_age_hours",
        "saturation_ratio",
    ):
        _require_decimal_string(field_name, payload[field_name])
    _require_load_status("load_status", payload["load_status"])
    _normalize_reason_codes(tuple(payload["reason_codes"]))
    if payload["manual_next_step"] != NEXT_STEP_BY_STATUS[payload["load_status"]]:
        raise ValueError("manual_next_step must match load_status")


def _reject_public_numeric_values(value: Any) -> None:
    if type(value) in (int, float, Decimal):
        raise ValueError("public payload numeric values must be Decimal strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
    elif isinstance(value, list):
        for item in value:
            _reject_public_numeric_values(item)


def _normalize_datetime(value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if value.tzinfo is None:
        raise ValueError("generated_at must be timezone aware")
    return value.astimezone(UTC)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(decimal_value)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _decimal_payload(value: object) -> str:
    return format(_require_decimal("payload Decimal", value), "f")


def _require_decimal_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        parsed = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    if not parsed.is_finite():
        raise ValueError(f"{field_name} must be a finite Decimal string")
    if format(_quantize(parsed), "f") != value:
        raise ValueError(f"{field_name} must be a normalized Decimal string")
    return value


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _require_public_code(field_name: str, value: object) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a public code")
    if any(character not in PUBLIC_CODE_CHARS for character in value):
        raise ValueError(f"{field_name} must be a public code")
    return value


def _require_load_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in LOAD_STATUSES:
        raise ValueError(f"{field_name} must be supported")
    return value


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError("reason_codes must be a non-empty tuple")
    normalized: list[str] = []
    for reason_code in value:
        if type(reason_code) is not str or reason_code not in REASON_CODES:
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(normalized)


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if len(value) != DIGEST_LENGTH:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_exact_type(value: object, expected_type: type[Any], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if type(value) is dict:
            flag_value = value.get(field_name)
        else:
            flag_value = getattr(value, field_name, None)
        if flag_value is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        return _decimal_payload(value)
    if type(value) is datetime:
        return _normalize_datetime(value).isoformat()
    if type(value) in (str, bool) or value is None:
        return value
    if type(value) in (int, float):
        raise ValueError("JSON numeric value must use Decimal strings")
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")
