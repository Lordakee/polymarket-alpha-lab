"""Pure report for primary and secondary resolution source consistency."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any


ZERO = Decimal("0.000000")
ONE = Decimal("1")
VALUE_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

CONSISTENT_REASON = "primary_secondary_resolution_consistent"
PRIMARY_MISSING_REASON = "primary_source_missing"
SECONDARY_MISSING_REASON = "secondary_source_missing"
SECONDARY_CONFLICT_REASON = "secondary_source_conflict"
SECONDARY_QUORUM_GAP_REASON = "secondary_consistency_quorum_gap"
FRESHNESS_WATCH_REASON = "freshness_gap_watch"

REASON_CODE_PRIORITY = (
    CONSISTENT_REASON,
    PRIMARY_MISSING_REASON,
    SECONDARY_MISSING_REASON,
    SECONDARY_CONFLICT_REASON,
    SECONDARY_QUORUM_GAP_REASON,
    FRESHNESS_WATCH_REASON,
)
REASON_CODES = frozenset(REASON_CODE_PRIORITY)
CONSISTENCY_STATUSES = ("consistent", "watch", "blocked")
MANUAL_NEXT_STEPS = (
    "no_manual_action_required",
    "attach_primary_resolution_source",
    "collect_secondary_resolution_source",
    "manual_adjudicate_conflicting_sources",
    "review_secondary_consistency_quorum",
    "refresh_resolution_source_timestamps",
)

FRESHNESS_WATCH_HOURS = Decimal("24.000000")

UNSAFE_PUBLIC_FRAGMENTS = (
    "http://",
    "https://",
    "www.",
    "url",
    "raw_market",
    "market_id",
    "market-",
    "market_",
    "raw market",
    "reference",
    " ref ",
    "\n",
    "\r",
    "\t",
)


@dataclass(frozen=True)
class SourceResolutionPrimarySecondaryConsistencyInput:
    primary_source_present: bool
    secondary_source_count: Decimal
    consistent_secondary_count: Decimal
    conflicting_secondary_count: Decimal
    freshness_gap_hours: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not SourceResolutionPrimarySecondaryConsistencyInput:
            raise TypeError(
                "SourceResolutionPrimarySecondaryConsistencyInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "consistency input",
            self,
            SourceResolutionPrimarySecondaryConsistencyInput,
        )
        object.__setattr__(
            self,
            "primary_source_present",
            _require_bool("primary_source_present", self.primary_source_present),
        )
        for field_name in (
            "secondary_source_count",
            "consistent_secondary_count",
            "conflicting_secondary_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "freshness_gap_hours",
            _normalize_nonnegative_decimal("freshness_gap_hours", self.freshness_gap_hours),
        )
        _require_hard_flags("consistency input", self)
        _validate_input_counts(self)
        _reject_unsafe_public_payload("consistency input", _payload_value(self))


@dataclass(frozen=True)
class SourceResolutionPrimarySecondaryConsistencyReport:
    primary_source_present: bool
    secondary_source_count: Decimal
    consistent_secondary_count: Decimal
    conflicting_secondary_count: Decimal
    freshness_gap_hours: Decimal
    consistency_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    public_payload: dict[str, Any]
    payload_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not SourceResolutionPrimarySecondaryConsistencyReport:
            raise TypeError(
                "SourceResolutionPrimarySecondaryConsistencyReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "report",
            self,
            SourceResolutionPrimarySecondaryConsistencyReport,
        )
        object.__setattr__(
            self,
            "primary_source_present",
            _require_bool("primary_source_present", self.primary_source_present),
        )
        for field_name in (
            "secondary_source_count",
            "consistent_secondary_count",
            "conflicting_secondary_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "freshness_gap_hours",
            _normalize_nonnegative_decimal("freshness_gap_hours", self.freshness_gap_hours),
        )
        _require_member("consistency_status", self.consistency_status, CONSISTENCY_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_member("manual_next_step", self.manual_next_step, MANUAL_NEXT_STEPS)
        object.__setattr__(
            self,
            "public_payload",
            _normalize_public_payload(self.public_payload),
        )
        _require_hard_flags("report", self)
        _validate_report(self)
        _reject_unsafe_public_payload("report", _payload_value(self))
        _set_or_validate_payload_digest(self)

    @property
    def payload(self) -> dict[str, Any]:
        return source_resolution_primary_secondary_consistency_report_payload(self)


def build_source_resolution_primary_secondary_consistency_report(
    source_item: SourceResolutionPrimarySecondaryConsistencyInput,
) -> SourceResolutionPrimarySecondaryConsistencyReport:
    if type(source_item) is not SourceResolutionPrimarySecondaryConsistencyInput:
        raise ValueError(
            "source_item must be a SourceResolutionPrimarySecondaryConsistencyInput",
        )
    _require_hard_flags("source_item", source_item)
    reason_codes = _reason_codes_for_input(source_item)
    consistency_status = _status_from_reason_codes(reason_codes)
    manual_next_step = _manual_next_step(reason_codes)
    public_payload = _public_payload(
        consistency_status=consistency_status,
        reason_codes=reason_codes,
        manual_next_step=manual_next_step,
    )
    return SourceResolutionPrimarySecondaryConsistencyReport(
        primary_source_present=source_item.primary_source_present,
        secondary_source_count=source_item.secondary_source_count,
        consistent_secondary_count=source_item.consistent_secondary_count,
        conflicting_secondary_count=source_item.conflicting_secondary_count,
        freshness_gap_hours=source_item.freshness_gap_hours,
        consistency_status=consistency_status,
        reason_codes=reason_codes,
        manual_next_step=manual_next_step,
        public_payload=public_payload,
    )


def source_resolution_primary_secondary_consistency_report_payload(
    report: SourceResolutionPrimarySecondaryConsistencyReport,
) -> dict[str, Any]:
    if type(report) is not SourceResolutionPrimarySecondaryConsistencyReport:
        raise ValueError(
            "report must be a SourceResolutionPrimarySecondaryConsistencyReport",
        )
    _validate_report(report)
    _validate_payload_digest(report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a dict")
    validate_source_resolution_primary_secondary_consistency_public_payload(payload)
    return dict(payload)


def validate_source_resolution_primary_secondary_consistency_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("public payload", payload)
    _require_public_payload_flags(payload)
    digest = _payload_required_string(payload, "payload_digest")
    _require_sha256_digest("payload_digest", digest)
    if digest != _payload_digest(payload):
        raise ValueError("payload_digest must match public payload")
    return True


def _reason_codes_for_input(
    source_item: SourceResolutionPrimarySecondaryConsistencyInput,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if not source_item.primary_source_present:
        reasons.append(PRIMARY_MISSING_REASON)
    if source_item.secondary_source_count == ZERO:
        reasons.append(SECONDARY_MISSING_REASON)
    if source_item.conflicting_secondary_count > ZERO:
        reasons.append(SECONDARY_CONFLICT_REASON)
    if (
        source_item.secondary_source_count > ZERO
        and source_item.consistent_secondary_count < source_item.secondary_source_count
    ):
        reasons.append(SECONDARY_QUORUM_GAP_REASON)
    if source_item.freshness_gap_hours >= FRESHNESS_WATCH_HOURS:
        reasons.append(FRESHNESS_WATCH_REASON)
    if not reasons:
        return (CONSISTENT_REASON,)
    return _normalize_reason_codes("reason_codes", tuple(reasons))


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (CONSISTENT_REASON,):
        return "consistent"
    if PRIMARY_MISSING_REASON in reason_codes or SECONDARY_CONFLICT_REASON in reason_codes:
        return "blocked"
    return "watch"


def _manual_next_step(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (CONSISTENT_REASON,):
        return "no_manual_action_required"
    if SECONDARY_CONFLICT_REASON in reason_codes:
        return "manual_adjudicate_conflicting_sources"
    if PRIMARY_MISSING_REASON in reason_codes:
        return "attach_primary_resolution_source"
    if SECONDARY_MISSING_REASON in reason_codes:
        return "collect_secondary_resolution_source"
    if SECONDARY_QUORUM_GAP_REASON in reason_codes:
        return "review_secondary_consistency_quorum"
    return "refresh_resolution_source_timestamps"


def _public_payload(
    *,
    consistency_status: str,
    reason_codes: tuple[str, ...],
    manual_next_step: str,
) -> dict[str, Any]:
    return {
        "consistency_status": consistency_status,
        "reason_codes": list(reason_codes),
        "manual_next_step": manual_next_step,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _normalize_public_payload(value: object) -> dict[str, Any]:
    if type(value) is not dict:
        raise ValueError("public_payload must be a dict")
    _reject_unsafe_public_payload("public_payload", value)
    _require_public_payload_flags(value)
    status = _payload_required_string(value, "consistency_status")
    _require_member("public_payload.consistency_status", status, CONSISTENCY_STATUSES)
    step = _payload_required_string(value, "manual_next_step")
    _require_member("public_payload.manual_next_step", step, MANUAL_NEXT_STEPS)
    reason_values = value.get("reason_codes")
    if type(reason_values) is not list:
        raise ValueError("public_payload.reason_codes must be a list")
    reason_codes = _normalize_reason_codes("public_payload.reason_codes", tuple(reason_values))
    return {
        "consistency_status": status,
        "reason_codes": list(reason_codes),
        "manual_next_step": step,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _validate_input_counts(
    source_item: SourceResolutionPrimarySecondaryConsistencyInput,
) -> None:
    if (
        source_item.consistent_secondary_count + source_item.conflicting_secondary_count
        > source_item.secondary_source_count
    ):
        raise ValueError("secondary counts must not exceed secondary_source_count")


def _validate_report(report: SourceResolutionPrimarySecondaryConsistencyReport) -> None:
    _validate_input_counts(
        SourceResolutionPrimarySecondaryConsistencyInput(
            primary_source_present=report.primary_source_present,
            secondary_source_count=report.secondary_source_count,
            consistent_secondary_count=report.consistent_secondary_count,
            conflicting_secondary_count=report.conflicting_secondary_count,
            freshness_gap_hours=report.freshness_gap_hours,
        ),
    )
    expected_reasons = _reason_codes_for_input(
        SourceResolutionPrimarySecondaryConsistencyInput(
            primary_source_present=report.primary_source_present,
            secondary_source_count=report.secondary_source_count,
            consistent_secondary_count=report.consistent_secondary_count,
            conflicting_secondary_count=report.conflicting_secondary_count,
            freshness_gap_hours=report.freshness_gap_hours,
        ),
    )
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match source consistency inputs")
    if report.consistency_status != _status_from_reason_codes(report.reason_codes):
        raise ValueError("consistency_status must match reason_codes")
    if report.manual_next_step != _manual_next_step(report.reason_codes):
        raise ValueError("manual_next_step must match reason_codes")
    if report.public_payload != _public_payload(
        consistency_status=report.consistency_status,
        reason_codes=report.reason_codes,
        manual_next_step=report.manual_next_step,
    ):
        raise ValueError("public_payload must match report fields")


def _set_or_validate_payload_digest(
    report: SourceResolutionPrimarySecondaryConsistencyReport,
) -> None:
    current = report.payload_digest
    expected = _payload_digest(report)
    if current == "":
        object.__setattr__(report, "payload_digest", expected)
        return
    _require_sha256_digest("payload_digest", current)
    if current != expected:
        raise ValueError("payload_digest must match report fields")


def _validate_payload_digest(
    report: SourceResolutionPrimarySecondaryConsistencyReport,
) -> None:
    current = _require_sha256_digest("payload_digest", report.payload_digest)
    if current != _payload_digest(report):
        raise ValueError("payload_digest must match report fields")


def _payload_digest(value: object) -> str:
    payload = _without_payload_digest(_payload_value(value))
    encoded = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _without_payload_digest(value: object) -> object:
    if type(value) is dict:
        return {
            field_name: _without_payload_digest(item)
            for field_name, item in value.items()
            if field_name != "payload_digest"
        }
    if type(value) is list:
        return [_without_payload_digest(item) for item in value]
    return value


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload values must be finite")
        return format(value, "f")
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is tuple or type(value) is list:
        return [_payload_value(item) for item in value]
    if type(value) is dict:
        return {field_name: _payload_value(item) for field_name, item in value.items()}
    return value


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    current_path = path or label
    if value is None or type(value) is bool:
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)
        return
    if isinstance(value, (Decimal, int, float)):
        raise ValueError(f"{current_path} must use Decimal strings, not numeric values")
    if type(value) is dict:
        for field_name, item in value.items():
            if type(field_name) is not str:
                raise ValueError("public payload field names must be strings")
            _reject_unsafe_public_field_name(field_name, current_path)
            item_path = field_name if not path else f"{path}.{field_name}"
            if field_name in ("paper_only", "report_only", "readonly") and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if type(value) is list:
        for index, item in enumerate(value):
            item_path = f"{current_path}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError(f"{current_path} is not public JSON serializable")


def _reject_unsafe_public_field_name(field_name: str, path: str) -> None:
    if _has_unsafe_public_fragment(field_name):
        raise ValueError(f"unsafe public payload field in {path}: {field_name}")


def _reject_unsafe_public_string(path: str, value: str) -> None:
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"unsafe public payload value in {path}")


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _require_public_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _payload_required_string(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_exact_type(label: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str or value not in REASON_CODES:
        raise ValueError(f"{field_name} must be a supported reason code")
    return value


def _normalize_reason_codes(field_name: str, value: tuple[object, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    normalized = tuple(_require_reason_code(field_name, item) for item in value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    sorted_values = tuple(
        reason_code
        for reason_code in REASON_CODE_PRIORITY
        if reason_code in normalized
    )
    if normalized != sorted_values:
        raise ValueError(f"{field_name} must be sorted deterministically")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(VALUE_QUANTUM)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        normalized = value.quantize(COUNT_QUANTUM)
    if normalized != value:
        raise ValueError(f"{field_name} must be a whole Decimal")
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")
