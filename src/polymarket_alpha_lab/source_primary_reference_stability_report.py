"""Pure report for primary source reference stability."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_SOURCE_PRIMARY_REFERENCE_STABILITY_REPORT_CONFIG_VERSION = (
    "source-primary-reference-stability-report-v0"
)

REFERENCE_STABILITY_STATUSES = ("stable", "watch", "blocked")

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
WATCH_SOURCE_AGE_HOURS = Decimal("24.000000")
BLOCK_SOURCE_AGE_HOURS = Decimal("48.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
DECIMAL_PAYLOAD_RE = re.compile(r"^(?:0|[1-9][0-9]*)\.[0-9]{6}$")

PRIMARY_REFERENCE_STABLE_REASON = "primary_reference_stable"
PRIMARY_REFERENCE_MISSING_REASON = "primary_reference_missing"
REFERENCE_DIGEST_CHANGED_REASON = "reference_digest_changed"
OFFICIAL_UPDATES_DETECTED_REASON = "official_updates_detected"
PRIMARY_REFERENCE_STALE_REASON = "primary_reference_stale"
FALLBACK_REFERENCES_PRESENT_REASON = "fallback_references_present"
STATUS_STABLE_REASON = "primary_reference_stability_stable"
STATUS_WATCH_REASON = "primary_reference_stability_watch"
STATUS_BLOCKED_REASON = "primary_reference_stability_blocked"

STATUS_REASON_BY_STATUS = {
    "stable": STATUS_STABLE_REASON,
    "watch": STATUS_WATCH_REASON,
    "blocked": STATUS_BLOCKED_REASON,
}
MANUAL_NEXT_STEP_BY_STATUS = {
    "stable": "continue_primary_reference_monitoring",
    "watch": "manual_refresh_primary_reference",
    "blocked": "manual_review_primary_reference_update",
}

REASON_CODES = (
    PRIMARY_REFERENCE_STABLE_REASON,
    PRIMARY_REFERENCE_MISSING_REASON,
    REFERENCE_DIGEST_CHANGED_REASON,
    OFFICIAL_UPDATES_DETECTED_REASON,
    PRIMARY_REFERENCE_STALE_REASON,
    FALLBACK_REFERENCES_PRESENT_REASON,
    STATUS_STABLE_REASON,
    STATUS_WATCH_REASON,
    STATUS_BLOCKED_REASON,
)

PAYLOAD_KEYS = frozenset(
    (
        "config_version",
        "reference_stability_status",
        "reason_codes",
        "manual_next_step",
        "primary_reference_present",
        "reference_digest_changed",
        "official_update_count",
        "source_age_hours",
        "fallback_reference_count",
        "payload_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)

__all__ = (
    "DEFAULT_SOURCE_PRIMARY_REFERENCE_STABILITY_REPORT_CONFIG_VERSION",
    "REFERENCE_STABILITY_STATUSES",
    "SourcePrimaryReferenceStabilityReport",
    "build_source_primary_reference_stability_report",
    "source_primary_reference_stability_public_payload",
    "source_primary_reference_stability_report",
    "validate_source_primary_reference_stability_payload_digest",
)


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class SourcePrimaryReferenceStabilityReport(_FinalDataclass):
    reference_stability_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    primary_reference_present: bool
    reference_digest_changed: bool
    official_update_count: Decimal
    source_age_hours: Decimal
    fallback_reference_count: Decimal
    payload_digest: str = ""
    config_version: str = DEFAULT_SOURCE_PRIMARY_REFERENCE_STABILITY_REPORT_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, SourcePrimaryReferenceStabilityReport, "report")
        _require_bool("primary_reference_present", self.primary_reference_present)
        _require_bool("reference_digest_changed", self.reference_digest_changed)
        for field_name in (
            "official_update_count",
            "source_age_hours",
            "fallback_reference_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("official_update_count", "fallback_reference_count"):
            _require_integer_count(field_name, getattr(self, field_name))
        _require_status(self.reference_stability_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_public_token("manual_next_step", self.manual_next_step)
        if (
            self.config_version
            != DEFAULT_SOURCE_PRIMARY_REFERENCE_STABILITY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_hard_flags(self)
        _validate_report(self)
        if self.payload_digest == "":
            object.__setattr__(
                self,
                "payload_digest",
                _payload_digest(_payload_without_digest(self)),
            )
        _require_digest("payload_digest", self.payload_digest)
        if self.payload_digest != _payload_digest(_payload_without_digest(self)):
            raise ValueError("payload_digest must match report payload")

    @property
    def public_payload(self) -> dict[str, Any]:
        return source_primary_reference_stability_public_payload(self)


def build_source_primary_reference_stability_report(
    *,
    primary_reference_present: bool,
    reference_digest_changed: bool,
    official_update_count: Decimal,
    source_age_hours: Decimal,
    fallback_reference_count: Decimal,
) -> SourcePrimaryReferenceStabilityReport:
    """Build a deterministic report-only primary reference stability result."""

    official_update_count = _require_nonnegative_decimal(
        "official_update_count",
        official_update_count,
    )
    source_age_hours = _require_nonnegative_decimal("source_age_hours", source_age_hours)
    fallback_reference_count = _require_nonnegative_decimal(
        "fallback_reference_count",
        fallback_reference_count,
    )
    _require_bool("primary_reference_present", primary_reference_present)
    _require_bool("reference_digest_changed", reference_digest_changed)
    _require_integer_count("official_update_count", official_update_count)
    _require_integer_count("fallback_reference_count", fallback_reference_count)

    status = _reference_stability_status(
        primary_reference_present=primary_reference_present,
        reference_digest_changed=reference_digest_changed,
        official_update_count=official_update_count,
        source_age_hours=source_age_hours,
        fallback_reference_count=fallback_reference_count,
    )
    reason_codes = _reason_codes(
        primary_reference_present=primary_reference_present,
        reference_digest_changed=reference_digest_changed,
        official_update_count=official_update_count,
        source_age_hours=source_age_hours,
        fallback_reference_count=fallback_reference_count,
        status=status,
    )
    manual_next_step = _manual_next_step(
        status=status,
        primary_reference_present=primary_reference_present,
    )
    values: dict[str, object] = {
        "reference_stability_status": status,
        "reason_codes": reason_codes,
        "manual_next_step": manual_next_step,
        "primary_reference_present": primary_reference_present,
        "reference_digest_changed": reference_digest_changed,
        "official_update_count": official_update_count,
        "source_age_hours": source_age_hours,
        "fallback_reference_count": fallback_reference_count,
        "config_version": DEFAULT_SOURCE_PRIMARY_REFERENCE_STABILITY_REPORT_CONFIG_VERSION,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return SourcePrimaryReferenceStabilityReport(
        **values,
        payload_digest=_payload_digest(values),
    )


def source_primary_reference_stability_report(
    *,
    primary_reference_present: bool,
    reference_digest_changed: bool,
    official_update_count: Decimal,
    source_age_hours: Decimal,
    fallback_reference_count: Decimal,
) -> SourcePrimaryReferenceStabilityReport:
    return build_source_primary_reference_stability_report(
        primary_reference_present=primary_reference_present,
        reference_digest_changed=reference_digest_changed,
        official_update_count=official_update_count,
        source_age_hours=source_age_hours,
        fallback_reference_count=fallback_reference_count,
    )


def source_primary_reference_stability_public_payload(
    report: SourcePrimaryReferenceStabilityReport,
) -> dict[str, Any]:
    if type(report) is not SourcePrimaryReferenceStabilityReport:
        raise ValueError("report must be a SourcePrimaryReferenceStabilityReport")
    _validate_report(report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("public_payload must be a JSON object")
    _validate_payload_shape(payload)
    if not validate_source_primary_reference_stability_payload_digest(payload):
        raise ValueError("payload_digest must match public payload")
    return payload


def validate_source_primary_reference_stability_payload_digest(
    payload: dict[str, Any],
) -> bool:
    try:
        _validate_payload_shape(payload)
    except ValueError:
        return False
    return payload["payload_digest"] == _payload_digest(payload)


def _reference_stability_status(
    *,
    primary_reference_present: bool,
    reference_digest_changed: bool,
    official_update_count: Decimal,
    source_age_hours: Decimal,
    fallback_reference_count: Decimal,
) -> str:
    if not primary_reference_present:
        return "blocked"
    if reference_digest_changed or official_update_count > ZERO:
        return "blocked"
    if source_age_hours >= BLOCK_SOURCE_AGE_HOURS:
        return "blocked"
    if source_age_hours > WATCH_SOURCE_AGE_HOURS:
        return "watch"
    if fallback_reference_count > ZERO:
        return "watch"
    return "stable"


def _reason_codes(
    *,
    primary_reference_present: bool,
    reference_digest_changed: bool,
    official_update_count: Decimal,
    source_age_hours: Decimal,
    fallback_reference_count: Decimal,
    status: str,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if not primary_reference_present:
        reasons.append(PRIMARY_REFERENCE_MISSING_REASON)
    if reference_digest_changed:
        reasons.append(REFERENCE_DIGEST_CHANGED_REASON)
    if official_update_count > ZERO:
        reasons.append(OFFICIAL_UPDATES_DETECTED_REASON)
    if source_age_hours > WATCH_SOURCE_AGE_HOURS:
        reasons.append(PRIMARY_REFERENCE_STALE_REASON)
    if fallback_reference_count > ZERO:
        reasons.append(FALLBACK_REFERENCES_PRESENT_REASON)
    if not reasons:
        return (PRIMARY_REFERENCE_STABLE_REASON,)
    reasons.append(STATUS_REASON_BY_STATUS[status])
    return tuple(reasons)


def _manual_next_step(*, status: str, primary_reference_present: bool) -> str:
    if not primary_reference_present:
        return "restore_primary_reference_before_use"
    return MANUAL_NEXT_STEP_BY_STATUS[status]


def _validate_report(report: SourcePrimaryReferenceStabilityReport) -> None:
    expected_status = _reference_stability_status(
        primary_reference_present=report.primary_reference_present,
        reference_digest_changed=report.reference_digest_changed,
        official_update_count=report.official_update_count,
        source_age_hours=report.source_age_hours,
        fallback_reference_count=report.fallback_reference_count,
    )
    if report.reference_stability_status != expected_status:
        raise ValueError("reference_stability_status must match inputs")
    expected_reasons = _reason_codes(
        primary_reference_present=report.primary_reference_present,
        reference_digest_changed=report.reference_digest_changed,
        official_update_count=report.official_update_count,
        source_age_hours=report.source_age_hours,
        fallback_reference_count=report.fallback_reference_count,
        status=report.reference_stability_status,
    )
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match inputs")
    expected_step = _manual_next_step(
        status=report.reference_stability_status,
        primary_reference_present=report.primary_reference_present,
    )
    if report.manual_next_step != expected_step:
        raise ValueError("manual_next_step must match inputs")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_status(value: str) -> None:
    if value not in REFERENCE_STABILITY_STATUSES:
        raise ValueError("reference_stability_status is not supported")


def _require_public_token(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not re.fullmatch(r"[a-z][a-z0-9_]{0,127}", value):
        raise ValueError(f"{field_name} must be a public token")


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        normalized = value.quantize(QUANTUM)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be non-negative")
    return normalized


def _require_integer_count(field_name: str, value: Decimal) -> None:
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be an integer count")


def _normalize_reason_codes(
    field_name: str,
    values: tuple[str, ...] | list[str],
) -> tuple[str, ...]:
    if type(values) not in (tuple, list):
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        if value not in REASON_CODES:
            raise ValueError(f"{field_name} contains an unsupported reason code")
        if value in normalized:
            raise ValueError(f"{field_name} must not contain duplicates")
        normalized.append(value)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return tuple(normalized)


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_hard_flags(value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only") is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly") is not True:
        raise ValueError("readonly must be True")


def _payload_without_digest(report: SourcePrimaryReferenceStabilityReport) -> dict[str, object]:
    values = asdict(report)
    values.pop("payload_digest", None)
    return values


def _payload_digest(payload: dict[str, Any]) -> str:
    ready = dict(payload)
    ready.pop("payload_digest", None)
    canonical = json.dumps(
        _json_ready(ready),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if is_dataclass(value):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        return _format_decimal(value)
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def _format_decimal(value: Decimal) -> str:
    with localcontext(DECIMAL_CONTEXT):
        normalized = value.quantize(QUANTUM)
    return format(normalized, "f")


def _validate_payload_shape(payload: dict[str, Any]) -> None:
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    if set(payload) != PAYLOAD_KEYS:
        raise ValueError("payload keys are not supported")
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")
    if payload["config_version"] != DEFAULT_SOURCE_PRIMARY_REFERENCE_STABILITY_REPORT_CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")
    if payload["reference_stability_status"] not in REFERENCE_STABILITY_STATUSES:
        raise ValueError("reference_stability_status is not supported")
    _require_public_token("manual_next_step", payload["manual_next_step"])
    if type(payload["primary_reference_present"]) is not bool:
        raise ValueError("primary_reference_present must be a bool")
    if type(payload["reference_digest_changed"]) is not bool:
        raise ValueError("reference_digest_changed must be a bool")
    if type(payload["reason_codes"]) is not list:
        raise ValueError("reason_codes must be a list")
    _normalize_reason_codes("reason_codes", payload["reason_codes"])
    for field_name in (
        "official_update_count",
        "source_age_hours",
        "fallback_reference_count",
    ):
        value = payload[field_name]
        if type(value) is not str or not DECIMAL_PAYLOAD_RE.fullmatch(value):
            raise ValueError(f"{field_name} must be a Decimal string")
    _require_digest("payload_digest", payload["payload_digest"])
    SourcePrimaryReferenceStabilityReport(
        reference_stability_status=payload["reference_stability_status"],
        reason_codes=tuple(payload["reason_codes"]),
        manual_next_step=payload["manual_next_step"],
        primary_reference_present=payload["primary_reference_present"],
        reference_digest_changed=payload["reference_digest_changed"],
        official_update_count=Decimal(payload["official_update_count"]),
        source_age_hours=Decimal(payload["source_age_hours"]),
        fallback_reference_count=Decimal(payload["fallback_reference_count"]),
        payload_digest=payload["payload_digest"],
        config_version=payload["config_version"],
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )
