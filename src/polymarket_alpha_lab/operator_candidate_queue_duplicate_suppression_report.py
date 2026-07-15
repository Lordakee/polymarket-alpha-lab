"""Pure in-memory candidate queue duplicate suppression readiness report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "DEFAULT_OPERATOR_CANDIDATE_QUEUE_DUPLICATE_SUPPRESSION_REPORT_CONFIG_VERSION",
    "OperatorCandidateQueueDuplicateSuppressionInput",
    "OperatorCandidateQueueDuplicateSuppressionReport",
    "build_operator_candidate_queue_duplicate_suppression_report",
    "operator_candidate_queue_duplicate_suppression_report_digest",
    "operator_candidate_queue_duplicate_suppression_report_payload",
)


DEFAULT_OPERATOR_CANDIDATE_QUEUE_DUPLICATE_SUPPRESSION_REPORT_CONFIG_VERSION = (
    "operator-candidate-queue-duplicate-suppression-report-v0"
)
COUNT_QUANTUM = Decimal("1.000000")
ZERO = Decimal("0.000000")
SUPPRESSION_STATUSES = ("ready", "watch", "blocked")
MANUAL_NEXT_STEPS = (
    "continue_manual_candidate_queue_review",
    "resolve_duplicate_markets_before_candidate_review",
    "compare_resolution_families_before_candidate_review",
    "compare_source_digests_before_candidate_review",
    "define_manual_suppression_rules_before_queue_review",
)
REASON_CODES = (
    "candidate_queue_duplicate_suppression_ready",
    "candidate_queue_duplicate_market_collision",
    "candidate_queue_same_resolution_family_collision",
    "candidate_queue_same_source_digest_collision",
    "candidate_queue_suppression_rules_missing",
)
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
UNSAFE_PUBLIC_FRAGMENTS = (
    "au" + "th",
    "credential",
    "private",
    "secret",
    "tok" + "en",
    "wal" + "let",
    "or" + "der",
    "broker",
    "buy",
    "sell",
    "trade",
    "network",
    "li" + "ve",
    "js" + "onl",
    "per" + "sist",
    "si" + "gn",
    "exec" + "ute",
    "exec" + "ution",
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
class OperatorCandidateQueueDuplicateSuppressionInput(_FinalPublicDataclass):
    candidate_count: Decimal
    duplicate_market_count: Decimal
    same_resolution_family_count: Decimal
    same_source_digest_count: Decimal
    suppression_rule_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, OperatorCandidateQueueDuplicateSuppressionInput, "input")
        for field_name in (
            "candidate_count",
            "duplicate_market_count",
            "same_resolution_family_count",
            "same_source_digest_count",
            "suppression_rule_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_at_most(
            "duplicate_market_count",
            self.duplicate_market_count,
            self.candidate_count,
        )
        _require_at_most(
            "same_resolution_family_count",
            self.same_resolution_family_count,
            self.candidate_count,
        )
        _require_at_most(
            "same_source_digest_count",
            self.same_source_digest_count,
            self.candidate_count,
        )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class OperatorCandidateQueueDuplicateSuppressionReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    duplicate_market_count: Decimal
    same_resolution_family_count: Decimal
    same_source_digest_count: Decimal
    suppression_rule_count: Decimal
    suppression_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, OperatorCandidateQueueDuplicateSuppressionReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "duplicate_market_count",
            "same_resolution_family_count",
            "same_source_digest_count",
            "suppression_rule_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_at_most(
            "duplicate_market_count",
            self.duplicate_market_count,
            self.candidate_count,
        )
        _require_at_most(
            "same_resolution_family_count",
            self.same_resolution_family_count,
            self.candidate_count,
        )
        _require_at_most(
            "same_source_digest_count",
            self.same_source_digest_count,
            self.candidate_count,
        )
        _require_member("suppression_status", self.suppression_status, SUPPRESSION_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_member("manual_next_step", self.manual_next_step, MANUAL_NEXT_STEPS)
        _require_digest("payload_digest", self.payload_digest)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        if self.payload_digest != _report_digest_from_values(self):
            raise ValueError("payload_digest must match report fields")

    @property
    def public_payload(self) -> dict[str, Any]:
        return operator_candidate_queue_duplicate_suppression_report_payload(self)


def build_operator_candidate_queue_duplicate_suppression_report(
    inputs: OperatorCandidateQueueDuplicateSuppressionInput,
    *,
    generated_at: datetime,
) -> OperatorCandidateQueueDuplicateSuppressionReport:
    if type(inputs) is not OperatorCandidateQueueDuplicateSuppressionInput:
        raise ValueError(
            "inputs must be an OperatorCandidateQueueDuplicateSuppressionInput",
        )
    generated_at = _as_utc("generated_at", generated_at)
    reason_codes = _reason_codes_for_inputs(inputs)
    suppression_status = _suppression_status(reason_codes)
    manual_next_step = _manual_next_step(reason_codes)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": (
            DEFAULT_OPERATOR_CANDIDATE_QUEUE_DUPLICATE_SUPPRESSION_REPORT_CONFIG_VERSION
        ),
        "candidate_count": inputs.candidate_count,
        "duplicate_market_count": inputs.duplicate_market_count,
        "same_resolution_family_count": inputs.same_resolution_family_count,
        "same_source_digest_count": inputs.same_source_digest_count,
        "suppression_rule_count": inputs.suppression_rule_count,
        "suppression_status": suppression_status,
        "reason_codes": reason_codes,
        "manual_next_step": manual_next_step,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["payload_digest"] = _payload_digest(values)
    return OperatorCandidateQueueDuplicateSuppressionReport(**values)  # type: ignore[arg-type]


def operator_candidate_queue_duplicate_suppression_report_payload(
    report: OperatorCandidateQueueDuplicateSuppressionReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is OperatorCandidateQueueDuplicateSuppressionReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        _reject_public_numeric_values(report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be an OperatorCandidateQueueDuplicateSuppressionReport or payload",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _validate_public_payload(payload)
    _reject_unsafe_public_payload("payload", payload)
    return payload


def operator_candidate_queue_duplicate_suppression_report_digest(
    report: OperatorCandidateQueueDuplicateSuppressionReport | dict[str, Any],
) -> str:
    if type(report) is OperatorCandidateQueueDuplicateSuppressionReport:
        return _report_digest_from_values(report)
    if type(report) is dict:
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        return _payload_digest(payload)
    raise ValueError(
        "report must be an OperatorCandidateQueueDuplicateSuppressionReport or payload",
    )


def _reason_codes_for_inputs(
    inputs: OperatorCandidateQueueDuplicateSuppressionInput,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if inputs.duplicate_market_count > ZERO:
        reasons.append("candidate_queue_duplicate_market_collision")
    if inputs.same_resolution_family_count > ZERO:
        reasons.append("candidate_queue_same_resolution_family_collision")
    if inputs.same_source_digest_count > ZERO:
        reasons.append("candidate_queue_same_source_digest_collision")
    if inputs.suppression_rule_count == ZERO:
        reasons.append("candidate_queue_suppression_rules_missing")
    if not reasons:
        reasons.append("candidate_queue_duplicate_suppression_ready")
    return tuple(reasons)


def _suppression_status(reason_codes: tuple[str, ...]) -> str:
    if "candidate_queue_duplicate_market_collision" in reason_codes:
        return "blocked"
    if reason_codes == ("candidate_queue_duplicate_suppression_ready",):
        return "ready"
    return "watch"


def _manual_next_step(reason_codes: tuple[str, ...]) -> str:
    if "candidate_queue_duplicate_market_collision" in reason_codes:
        return "resolve_duplicate_markets_before_candidate_review"
    if "candidate_queue_suppression_rules_missing" in reason_codes:
        return "define_manual_suppression_rules_before_queue_review"
    if "candidate_queue_same_resolution_family_collision" in reason_codes:
        return "compare_resolution_families_before_candidate_review"
    if "candidate_queue_same_source_digest_collision" in reason_codes:
        return "compare_source_digests_before_candidate_review"
    return "continue_manual_candidate_queue_review"


def _report_digest_from_values(
    report: OperatorCandidateQueueDuplicateSuppressionReport,
) -> str:
    return _payload_digest(_json_ready(_report_values_without_digest(report)))


def _report_values_without_digest(
    report: OperatorCandidateQueueDuplicateSuppressionReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("payload_digest", None)
    return values


def _payload_digest(payload: dict[str, object]) -> str:
    hash_payload = dict(payload)
    hash_payload.pop("payload_digest", None)
    canonical = json.dumps(
        _json_ready(hash_payload),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _validate_public_payload(payload: dict[str, Any]) -> None:
    expected_names = {
        field.name for field in fields(OperatorCandidateQueueDuplicateSuppressionReport)
    }
    if set(payload) != expected_names:
        raise ValueError("payload must contain exactly report fields")
    _require_hard_flags("payload", _DictFlags(payload))
    _as_utc("generated_at", payload["generated_at"])
    _require_public_string("config_version", payload["config_version"])
    for field_name in (
        "candidate_count",
        "duplicate_market_count",
        "same_resolution_family_count",
        "same_source_digest_count",
        "suppression_rule_count",
    ):
        _require_decimal_string(field_name, payload[field_name])
    candidate_count = Decimal(payload["candidate_count"])
    _require_at_most(
        "duplicate_market_count",
        Decimal(payload["duplicate_market_count"]),
        candidate_count,
    )
    _require_at_most(
        "same_resolution_family_count",
        Decimal(payload["same_resolution_family_count"]),
        candidate_count,
    )
    _require_at_most(
        "same_source_digest_count",
        Decimal(payload["same_source_digest_count"]),
        candidate_count,
    )
    _require_member("suppression_status", payload["suppression_status"], SUPPRESSION_STATUSES)
    _normalize_reason_codes("reason_codes", payload["reason_codes"])
    _require_member("manual_next_step", payload["manual_next_step"], MANUAL_NEXT_STEPS)
    _require_digest("payload_digest", payload["payload_digest"])
    if payload["payload_digest"] != _payload_digest(payload):
        raise ValueError("payload_digest must match payload values")


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


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must use the exact public dataclass type")


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        if isinstance(value, Decimal):
            raise ValueError(f"{field_name} must use plain Decimal")
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value.quantize(COUNT_QUANTUM)


def _require_at_most(field_name: str, value: Decimal, maximum: Decimal) -> None:
    if value > maximum:
        raise ValueError(f"{field_name} cannot exceed candidate_count")


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a sequence")
    normalized: list[str] = []
    for item in value:
        _require_member(field_name, item, REASON_CODES)
        if item not in normalized:
            normalized.append(item)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return tuple(normalized)


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of the supported values")


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    _reject_unsafe_public_text(field_name, value)
    return value


def _require_decimal_string(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        parsed = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    if parsed < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if str(parsed.quantize(COUNT_QUANTUM)) != value:
        raise ValueError(f"{field_name} must be canonical")
    return parsed


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is str:
        try:
            value = datetime.fromisoformat(value)
        except ValueError as exc:
            raise ValueError(f"{field_name} must be a valid datetime") from exc
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value.quantize(COUNT_QUANTUM))
    if isinstance(value, Decimal):
        raise ValueError("JSON Decimal value must use plain Decimal")
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float) or type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) in (str, bool):
        return value
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for name, item in value.items():
            if type(name) is not str:
                raise ValueError("JSON object names must be strings")
            ready[name] = _json_ready(item)
        return ready
    if type(value) in (list, tuple):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_public_numeric_values(value: object) -> None:
    if isinstance(value, float) or type(value) is int:
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if type(value) is dict:
        for item in value.values():
            _reject_public_numeric_values(item)
        return
    if type(value) is list:
        for item in value:
            _reject_public_numeric_values(item)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)
        return
    if type(value) in (Decimal, datetime, bool) or value is None:
        return
    if isinstance(value, float) or type(value) is int:
        raise ValueError("unsafe public payload numeric value")
    if type(value) is dict:
        for name, item in value.items():
            if type(name) is not str:
                raise ValueError("payload names must be strings")
            _reject_unsafe_public_text(label, name)
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    raise ValueError("unsafe public payload value")


def _reject_unsafe_public_text(label: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public value in {label}")
