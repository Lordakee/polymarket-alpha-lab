"""Read-only go/no-go gate report before final manual decision."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
import re


MANUAL_DECISION_GO_NO_GO_GATE_REPORT_VERSION = (
    "manual-decision-go-no-go-gate-report-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
GATE_COUNT = Decimal("8.000000")

DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
PUBLIC_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")

GATE_FIELDS = (
    "quality_index_ready",
    "decision_memo_ready",
    "review_packet_index_ready",
    "operator_safety_ready",
    "export_manifest_ready",
    "manual_review_capacity_ready",
    "liquidity_exit_ready",
    "resolution_rule_clarity_ready",
)
BLOCKED_REASON_BY_FIELD = {
    "quality_index_ready": "quality_index_not_ready",
    "decision_memo_ready": "decision_memo_not_ready",
    "review_packet_index_ready": "review_packet_index_not_ready",
    "operator_safety_ready": "operator_safety_not_ready",
    "export_manifest_ready": "export_manifest_not_ready",
    "manual_review_capacity_ready": "manual_review_capacity_not_ready",
    "liquidity_exit_ready": "liquidity_exit_not_ready",
    "resolution_rule_clarity_ready": "resolution_rule_clarity_not_ready",
}
ATTENTION_REASON_BY_FIELD = {
    "quality_index_ready": "quality_index_requires_manual_attention",
    "decision_memo_ready": "decision_memo_requires_manual_attention",
    "review_packet_index_ready": "review_packet_index_requires_manual_attention",
    "operator_safety_ready": "operator_safety_requires_manual_attention",
    "export_manifest_ready": "export_manifest_requires_manual_attention",
    "manual_review_capacity_ready": "manual_review_capacity_requires_manual_attention",
    "liquidity_exit_ready": "liquidity_exit_requires_manual_attention",
    "resolution_rule_clarity_ready": "resolution_rule_clarity_requires_manual_attention",
}
PASS_REASON = "manual_decision_go_no_go_gate_pass"
ATTENTION_REASON = "manual_decision_go_no_go_gate_attention"
BLOCKED_REASON = "manual_decision_go_no_go_gate_blocked"
GO_BAND = "go"
ATTENTION_BAND = "attention"
NO_GO_BAND = "no_go"

PAYLOAD_KEYS = (
    "config_version",
    "ready_for_manual_decision",
    "go_no_go_band",
    "quality_index_ready",
    "decision_memo_ready",
    "review_packet_index_ready",
    "operator_safety_ready",
    "export_manifest_ready",
    "manual_review_capacity_ready",
    "liquidity_exit_ready",
    "resolution_rule_clarity_ready",
    "ready_gate_count",
    "blocked_gate_count",
    "blocked_reason_codes",
    "attention_reason_codes",
    "ready_ratio",
    "paper_only",
    "report_only",
    "readonly",
    "digest",
)
DECIMAL_PAYLOAD_KEYS = ("ready_gate_count", "blocked_gate_count", "ready_ratio")
UNSAFE_PUBLIC_TERMS = (
    "live",
    "trading",
    "trade",
    "auth",
    "wallet",
    "order",
    "execution",
    "network",
    "database",
    "persist",
    "mutation",
    "private_key",
    "secret",
    "token",
    "password",
    "api_key",
    "dsn",
    "postgres://",
    "postgresql://",
    "http://",
    "https://",
)

__all__ = (
    "MANUAL_DECISION_GO_NO_GO_GATE_REPORT_VERSION",
    "ManualDecisionGoNoGoGateInput",
    "ManualDecisionGoNoGoGatePublicPayload",
    "ManualDecisionGoNoGoGateReport",
    "build_manual_decision_go_no_go_gate_report",
    "manual_decision_go_no_go_gate_report_digest",
    "manual_decision_go_no_go_gate_report_payload",
)


class ManualDecisionGoNoGoGatePublicPayload(dict[str, object]):
    """Immutable public payload for this read-only gate report."""

    def __readonly(self, *args: object, **kwargs: object) -> None:
        raise TypeError("public_payload is immutable")

    __setitem__ = __readonly
    __delitem__ = __readonly
    clear = __readonly
    pop = __readonly
    popitem = __readonly
    setdefault = __readonly
    update = __readonly


@dataclass(frozen=True)
class ManualDecisionGoNoGoGateInput:
    quality_index_ready: bool
    decision_memo_ready: bool
    review_packet_index_ready: bool
    operator_safety_ready: bool
    export_manifest_ready: bool
    manual_review_capacity_ready: bool
    liquidity_exit_ready: bool
    resolution_rule_clarity_ready: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ManualDecisionGoNoGoGateInput:
            raise TypeError("ManualDecisionGoNoGoGateInput does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ManualDecisionGoNoGoGateInput:
            raise ValueError("input must be exactly ManualDecisionGoNoGoGateInput")
        for field_name in GATE_FIELDS:
            _require_bool(field_name, getattr(self, field_name))
        _require_hard_flags(self)


@dataclass(frozen=True)
class ManualDecisionGoNoGoGateReport:
    config_version: str
    ready_for_manual_decision: bool
    go_no_go_band: str
    quality_index_ready: bool
    decision_memo_ready: bool
    review_packet_index_ready: bool
    operator_safety_ready: bool
    export_manifest_ready: bool
    manual_review_capacity_ready: bool
    liquidity_exit_ready: bool
    resolution_rule_clarity_ready: bool
    ready_gate_count: Decimal
    blocked_gate_count: Decimal
    blocked_reason_codes: tuple[str, ...]
    attention_reason_codes: tuple[str, ...]
    ready_ratio: Decimal
    digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ManualDecisionGoNoGoGateReport:
            raise TypeError("ManualDecisionGoNoGoGateReport does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ManualDecisionGoNoGoGateReport:
            raise ValueError("report must be exactly ManualDecisionGoNoGoGateReport")
        _require_public_label("config_version", self.config_version)
        if self.config_version != MANUAL_DECISION_GO_NO_GO_GATE_REPORT_VERSION:
            raise ValueError("config_version must be the supported report version")
        _require_bool("ready_for_manual_decision", self.ready_for_manual_decision)
        _require_go_no_go_band(self.go_no_go_band)
        for field_name in GATE_FIELDS:
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "ready_gate_count",
            _require_count_decimal("ready_gate_count", self.ready_gate_count),
        )
        object.__setattr__(
            self,
            "blocked_gate_count",
            _require_count_decimal("blocked_gate_count", self.blocked_gate_count),
        )
        object.__setattr__(
            self,
            "blocked_reason_codes",
            _normalize_reason_codes(
                "blocked_reason_codes",
                self.blocked_reason_codes,
                tuple(BLOCKED_REASON_BY_FIELD.values()),
            ),
        )
        object.__setattr__(
            self,
            "attention_reason_codes",
            _normalize_reason_codes(
                "attention_reason_codes",
                self.attention_reason_codes,
                (PASS_REASON, ATTENTION_REASON, BLOCKED_REASON)
                + tuple(ATTENTION_REASON_BY_FIELD.values()),
            ),
        )
        object.__setattr__(
            self,
            "ready_ratio",
            _require_ratio_decimal("ready_ratio", self.ready_ratio),
        )
        _require_digest("digest", self.digest)
        _require_hard_flags(self)
        _validate_report(self)
        expected_digest = _payload_digest(_payload_items(self, digest=""))
        if self.digest != expected_digest:
            raise ValueError("digest must match public payload")

    @property
    def public_payload(self) -> ManualDecisionGoNoGoGatePublicPayload:
        payload = ManualDecisionGoNoGoGatePublicPayload(
            _payload_items(self, digest=self.digest),
        )
        _validate_public_payload(payload)
        return payload


def build_manual_decision_go_no_go_gate_report(
    inputs: ManualDecisionGoNoGoGateInput,
) -> ManualDecisionGoNoGoGateReport:
    """Build a deterministic read-only go/no-go gate report."""

    if type(inputs) is not ManualDecisionGoNoGoGateInput:
        raise ValueError("inputs must be a ManualDecisionGoNoGoGateInput")
    _require_hard_flags(inputs)
    gate_values = {field_name: getattr(inputs, field_name) for field_name in GATE_FIELDS}
    ready_count = _count(sum(1 for value in gate_values.values() if value is True))
    blocked_count = _count(sum(1 for value in gate_values.values() if value is not True))
    blocked_reason_codes = tuple(
        BLOCKED_REASON_BY_FIELD[field_name]
        for field_name in GATE_FIELDS
        if gate_values[field_name] is not True
    )
    values: dict[str, object] = {
        "config_version": MANUAL_DECISION_GO_NO_GO_GATE_REPORT_VERSION,
        "ready_for_manual_decision": not blocked_reason_codes,
        "go_no_go_band": _go_no_go_band(blocked_count),
        **gate_values,
        "ready_gate_count": ready_count,
        "blocked_gate_count": blocked_count,
        "blocked_reason_codes": blocked_reason_codes,
        "attention_reason_codes": _attention_reason_codes(blocked_reason_codes),
        "ready_ratio": _ratio(ready_count, GATE_COUNT),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ManualDecisionGoNoGoGateReport(
        **values,
        digest=_payload_digest(_payload_values(values, digest="")),
    )


def manual_decision_go_no_go_gate_report_payload(
    report: ManualDecisionGoNoGoGateReport | Mapping[str, object],
) -> ManualDecisionGoNoGoGatePublicPayload:
    if type(report) is ManualDecisionGoNoGoGateReport:
        _require_hard_flags(report)
        _validate_report(report)
        expected_digest = _payload_digest(_payload_items(report, digest=""))
        if report.digest != expected_digest:
            raise ValueError("digest must match report payload")
        return report.public_payload
    if isinstance(report, Mapping):
        _validate_public_payload(report)
        return ManualDecisionGoNoGoGatePublicPayload(report)
    raise ValueError("report must be a ManualDecisionGoNoGoGateReport or public payload")


def manual_decision_go_no_go_gate_report_digest(
    report: ManualDecisionGoNoGoGateReport,
) -> str:
    if type(report) is not ManualDecisionGoNoGoGateReport:
        raise ValueError("report must be a ManualDecisionGoNoGoGateReport")
    _require_hard_flags(report)
    _validate_report(report)
    return (
        "ManualDecisionGoNoGoGateReport("
        f"ready_for_manual_decision={str(report.ready_for_manual_decision).lower()}, "
        f"band={report.go_no_go_band}, "
        f"ready_ratio={report.ready_ratio}, "
        f"blocked={','.join(report.blocked_reason_codes) or 'none'}, "
        f"digest={report.digest})"
    )


def _go_no_go_band(blocked_count: Decimal) -> str:
    if blocked_count == ZERO:
        return GO_BAND
    if blocked_count >= Decimal("4.000000"):
        return NO_GO_BAND
    return ATTENTION_BAND


def _attention_reason_codes(blocked_reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if not blocked_reason_codes:
        return (PASS_REASON,)
    if len(blocked_reason_codes) >= 4:
        return (BLOCKED_REASON,)
    field_by_blocked_reason = {
        reason_code: field_name
        for field_name, reason_code in BLOCKED_REASON_BY_FIELD.items()
    }
    return (ATTENTION_REASON,) + tuple(
        ATTENTION_REASON_BY_FIELD[field_by_blocked_reason[reason_code]]
        for reason_code in blocked_reason_codes
    )


def _validate_report(report: ManualDecisionGoNoGoGateReport) -> None:
    gate_values = tuple(getattr(report, field_name) for field_name in GATE_FIELDS)
    ready_count = _count(sum(1 for value in gate_values if value is True))
    blocked_count = _count(sum(1 for value in gate_values if value is not True))
    if report.ready_gate_count != ready_count:
        raise ValueError("ready_gate_count must match ready gate values")
    if report.blocked_gate_count != blocked_count:
        raise ValueError("blocked_gate_count must match blocked gate values")
    if report.ready_ratio != _ratio(report.ready_gate_count, GATE_COUNT):
        raise ValueError("ready_ratio must match gate readiness")
    expected_blocked_reasons = tuple(
        BLOCKED_REASON_BY_FIELD[field_name]
        for field_name in GATE_FIELDS
        if getattr(report, field_name) is not True
    )
    if report.blocked_reason_codes != expected_blocked_reasons:
        raise ValueError("blocked_reason_codes must match gate readiness")
    if report.attention_reason_codes != _attention_reason_codes(
        report.blocked_reason_codes,
    ):
        raise ValueError("attention_reason_codes must match gate readiness")
    if report.ready_for_manual_decision is not (not report.blocked_reason_codes):
        raise ValueError("ready_for_manual_decision must match blocker status")
    if report.go_no_go_band != _go_no_go_band(report.blocked_gate_count):
        raise ValueError("go_no_go_band must match blocker count")


def _payload_items(
    report: ManualDecisionGoNoGoGateReport,
    *,
    digest: str,
) -> dict[str, object]:
    return {
        "config_version": report.config_version,
        "ready_for_manual_decision": report.ready_for_manual_decision,
        "go_no_go_band": report.go_no_go_band,
        "quality_index_ready": report.quality_index_ready,
        "decision_memo_ready": report.decision_memo_ready,
        "review_packet_index_ready": report.review_packet_index_ready,
        "operator_safety_ready": report.operator_safety_ready,
        "export_manifest_ready": report.export_manifest_ready,
        "manual_review_capacity_ready": report.manual_review_capacity_ready,
        "liquidity_exit_ready": report.liquidity_exit_ready,
        "resolution_rule_clarity_ready": report.resolution_rule_clarity_ready,
        "ready_gate_count": _decimal_string(report.ready_gate_count),
        "blocked_gate_count": _decimal_string(report.blocked_gate_count),
        "blocked_reason_codes": list(report.blocked_reason_codes),
        "attention_reason_codes": list(report.attention_reason_codes),
        "ready_ratio": _decimal_string(report.ready_ratio),
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
        "digest": digest,
    }


def _payload_values(values: Mapping[str, object], *, digest: str) -> dict[str, object]:
    return {
        "config_version": values["config_version"],
        "ready_for_manual_decision": values["ready_for_manual_decision"],
        "go_no_go_band": values["go_no_go_band"],
        "quality_index_ready": values["quality_index_ready"],
        "decision_memo_ready": values["decision_memo_ready"],
        "review_packet_index_ready": values["review_packet_index_ready"],
        "operator_safety_ready": values["operator_safety_ready"],
        "export_manifest_ready": values["export_manifest_ready"],
        "manual_review_capacity_ready": values["manual_review_capacity_ready"],
        "liquidity_exit_ready": values["liquidity_exit_ready"],
        "resolution_rule_clarity_ready": values["resolution_rule_clarity_ready"],
        "ready_gate_count": _decimal_string(values["ready_gate_count"]),
        "blocked_gate_count": _decimal_string(values["blocked_gate_count"]),
        "blocked_reason_codes": list(values["blocked_reason_codes"]),
        "attention_reason_codes": list(values["attention_reason_codes"]),
        "ready_ratio": _decimal_string(values["ready_ratio"]),
        "paper_only": values["paper_only"],
        "report_only": values["report_only"],
        "readonly": values["readonly"],
        "digest": digest,
    }


def _validate_public_payload(payload: Mapping[str, object]) -> None:
    if not isinstance(payload, Mapping):
        raise ValueError("public payload must be a mapping")
    if tuple(payload.keys()) != PAYLOAD_KEYS:
        raise ValueError("public payload keys must match report contract")
    for key in DECIMAL_PAYLOAD_KEYS:
        if type(payload[key]) is not str:
            raise ValueError("public payload numerics must be decimal strings")
        _parse_decimal_string(key, payload[key])
    for field_name in GATE_FIELDS:
        _require_bool(field_name, payload[field_name])
    _require_bool("ready_for_manual_decision", payload["ready_for_manual_decision"])
    _require_hard_flags(payload)
    _require_go_no_go_band(payload["go_no_go_band"])
    _require_digest("digest", payload["digest"])
    _normalize_reason_codes(
        "blocked_reason_codes",
        _tuple_from_payload("blocked_reason_codes", payload["blocked_reason_codes"]),
        tuple(BLOCKED_REASON_BY_FIELD.values()),
    )
    _normalize_reason_codes(
        "attention_reason_codes",
        _tuple_from_payload("attention_reason_codes", payload["attention_reason_codes"]),
        (PASS_REASON, ATTENTION_REASON, BLOCKED_REASON)
        + tuple(ATTENTION_REASON_BY_FIELD.values()),
    )
    _reject_unsafe_public_payload(payload)
    payload_without_digest = dict(payload)
    payload_without_digest["digest"] = ""
    if payload["digest"] != _payload_digest(payload_without_digest):
        raise ValueError("digest must match public payload")


def _require_bool(name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{name} must be exactly bool")
    return value


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        flag = value[field_name] if isinstance(value, Mapping) else getattr(value, field_name)
        if flag is not True:
            raise ValueError(f"{field_name} must be True")


def _require_count_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return decimal_value.quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _require_ratio_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value).quantize(
        QUANTUM,
        rounding=ROUND_HALF_UP,
    )
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return decimal_value


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return (numerator / denominator).quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _decimal_string(value: object) -> str:
    return str(_require_decimal("payload decimal", value).quantize(QUANTUM))


def _parse_decimal_string(name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{name} must be a decimal string")
    try:
        parsed = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{name} must be a decimal string") from exc
    if not parsed.is_finite():
        raise ValueError(f"{name} must be finite")
    if str(parsed.quantize(QUANTUM)) != value:
        raise ValueError(f"{name} must use six decimal places")
    return parsed


def _require_public_label(name: str, value: object) -> str:
    if type(value) is not str or not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{name} must be a public label")
    return value


def _require_digest(name: str, value: object) -> str:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{name} must be lowercase sha256 hex")
    return value


def _require_go_no_go_band(value: object) -> str:
    if value not in {GO_BAND, ATTENTION_BAND, NO_GO_BAND}:
        raise ValueError("go_no_go_band must be go, attention, or no_go")
    if type(value) is not str:
        raise ValueError("go_no_go_band must be exactly str")
    return value


def _normalize_reason_codes(
    name: str,
    reason_codes: object,
    allowed_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{name} must not contain duplicates")
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in allowed_codes:
            raise ValueError(f"{name} contains unsupported reason code")
    return reason_codes


def _tuple_from_payload(name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{name} must be a list in public payload")
    if not all(type(item) is str for item in value):
        raise ValueError(f"{name} must contain strings")
    return tuple(value)


def _payload_digest(payload: Mapping[str, object]) -> str:
    _reject_unsafe_public_payload(payload)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _reject_unsafe_public_payload(payload: object) -> None:
    serialized = json.dumps(payload, default=str, sort_keys=True).lower()
    for term in UNSAFE_PUBLIC_TERMS:
        if term in serialized:
            raise ValueError("public payload must not expose live trading/auth/wallet/order execution")
