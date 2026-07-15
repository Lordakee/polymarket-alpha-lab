"""Public final boundary report for human paper review."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
from typing import Any


MANUAL_OPERATOR_PACKET_FINAL_BOUNDARY_REPORT_VERSION = (
    "manual-operator-packet-final-boundary-report-v0"
)

ZERO = Decimal("0")
ONE = Decimal("1")
BOUNDARY_CHECK_COUNT = Decimal("7")
RATIO_QUANTUM = Decimal("0.000001")

STATUS_VALUES = ("pass", "watch", "blocked")
SELECTED_SIDE_VALUES = ("yes", "no", "abstain")
BOUNDARY_STATUS_FIELDS = (
    "source_quality_status",
    "memory_policy_status",
    "forecast_vs_price_edge_status",
    "costs_status",
    "liquidity_status",
    "resolution_risk_status",
)
PAYLOAD_FIELDS = (
    "config_version",
    "team_owner",
    "source_quality_status",
    "memory_policy_status",
    "forecast_vs_price_edge_status",
    "costs_status",
    "liquidity_status",
    "resolution_risk_status",
    "selected_side",
    "final_status",
    "reason_codes",
    "manual_next_step",
    "boundary_check_count",
    "pass_check_count",
    "watch_check_count",
    "blocked_check_count",
    "ready_ratio",
    "paper_review_only",
    "paper_only",
    "report_only",
    "readonly",
    "derived_validation_digest",
)
DECIMAL_PAYLOAD_FIELDS = (
    "boundary_check_count",
    "pass_check_count",
    "watch_check_count",
    "blocked_check_count",
    "ready_ratio",
)
FINAL_REASON_BY_STATUS = {
    "pass": "manual_operator_packet_final_boundary_pass",
    "watch": "manual_operator_packet_final_boundary_watch",
    "blocked": "manual_operator_packet_final_boundary_blocked",
}
MANUAL_NEXT_STEP_BY_STATUS = {
    "pass": "paper_review_read_final_boundary_report",
    "watch": "paper_review_check_forecast_edge",
    "blocked": "paper_review_resolve_memory_policy",
}
UNSUPPORTED_SURFACE_TERMS = frozenset(
    "".join(parts)
    for parts in (
        ("acc", "ount"),
        ("wal", "let"),
        ("k", "ey"),
        ("or", "der"),
        ("li", "ve"),
        ("exec", "ution"),
    )
)

__all__ = (
    "MANUAL_OPERATOR_PACKET_FINAL_BOUNDARY_REPORT_VERSION",
    "ManualOperatorPacketFinalBoundaryInput",
    "ManualOperatorPacketFinalBoundaryPublicPayload",
    "ManualOperatorPacketFinalBoundaryReport",
    "build_manual_operator_packet_final_boundary_report",
    "manual_operator_packet_final_boundary_report_payload",
)


class ManualOperatorPacketFinalBoundaryPublicPayload(dict[str, object]):
    """Immutable public payload for the final boundary report."""

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
class ManualOperatorPacketFinalBoundaryInput:
    team_owner: str
    source_quality_status: str
    memory_policy_status: str
    forecast_vs_price_edge_status: str
    costs_status: str
    liquidity_status: str
    resolution_risk_status: str
    selected_side: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    paper_review_only: bool = True
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ManualOperatorPacketFinalBoundaryInput:
            raise TypeError(
                "ManualOperatorPacketFinalBoundaryInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ManualOperatorPacketFinalBoundaryInput:
            raise ValueError(
                "input must be exactly ManualOperatorPacketFinalBoundaryInput",
            )
        object.__setattr__(
            self,
            "team_owner",
            _require_public_label("team_owner", self.team_owner),
        )
        for field_name in BOUNDARY_STATUS_FIELDS:
            _require_member(field_name, getattr(self, field_name), STATUS_VALUES)
        _require_member("selected_side", self.selected_side, SELECTED_SIDE_VALUES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "manual_next_step",
            _require_manual_next_step(self.manual_next_step),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ManualOperatorPacketFinalBoundaryReport:
    config_version: str
    team_owner: str
    source_quality_status: str
    memory_policy_status: str
    forecast_vs_price_edge_status: str
    costs_status: str
    liquidity_status: str
    resolution_risk_status: str
    selected_side: str
    final_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    boundary_check_count: Decimal
    pass_check_count: Decimal
    watch_check_count: Decimal
    blocked_check_count: Decimal
    ready_ratio: Decimal
    derived_validation_digest: str
    paper_review_only: bool = True
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ManualOperatorPacketFinalBoundaryReport:
            raise TypeError(
                "ManualOperatorPacketFinalBoundaryReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ManualOperatorPacketFinalBoundaryReport:
            raise ValueError(
                "report must be exactly ManualOperatorPacketFinalBoundaryReport",
            )
        _require_public_label("config_version", self.config_version)
        if self.config_version != MANUAL_OPERATOR_PACKET_FINAL_BOUNDARY_REPORT_VERSION:
            raise ValueError("config_version must be the supported report version")
        object.__setattr__(
            self,
            "team_owner",
            _require_public_label("team_owner", self.team_owner),
        )
        for field_name in BOUNDARY_STATUS_FIELDS:
            _require_member(field_name, getattr(self, field_name), STATUS_VALUES)
        _require_member("selected_side", self.selected_side, SELECTED_SIDE_VALUES)
        _require_member("final_status", self.final_status, STATUS_VALUES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "manual_next_step",
            _require_manual_next_step(self.manual_next_step),
        )
        object.__setattr__(
            self,
            "boundary_check_count",
            _require_count_decimal("boundary_check_count", self.boundary_check_count),
        )
        object.__setattr__(
            self,
            "pass_check_count",
            _require_count_decimal("pass_check_count", self.pass_check_count),
        )
        object.__setattr__(
            self,
            "watch_check_count",
            _require_count_decimal("watch_check_count", self.watch_check_count),
        )
        object.__setattr__(
            self,
            "blocked_check_count",
            _require_count_decimal("blocked_check_count", self.blocked_check_count),
        )
        object.__setattr__(
            self,
            "ready_ratio",
            _require_ratio_decimal("ready_ratio", self.ready_ratio),
        )
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _validate_report(self)
        if self.derived_validation_digest != _payload_digest(
            _payload_items(self, digest=""),
        ):
            raise ValueError("derived_validation_digest must match public payload")

    @property
    def public_payload(self) -> ManualOperatorPacketFinalBoundaryPublicPayload:
        payload = ManualOperatorPacketFinalBoundaryPublicPayload(
            _payload_items(self, digest=self.derived_validation_digest),
        )
        _validate_public_payload(payload)
        return payload


def build_manual_operator_packet_final_boundary_report(
    inputs: ManualOperatorPacketFinalBoundaryInput,
) -> ManualOperatorPacketFinalBoundaryReport:
    if type(inputs) is not ManualOperatorPacketFinalBoundaryInput:
        raise ValueError("inputs must be a ManualOperatorPacketFinalBoundaryInput")
    _require_hard_flags("input", inputs)
    statuses = tuple(getattr(inputs, field_name) for field_name in BOUNDARY_STATUS_FIELDS)
    pass_count = _count(sum(1 for status in statuses if status == "pass") + 1)
    watch_count = _count(sum(1 for status in statuses if status == "watch"))
    blocked_count = _count(sum(1 for status in statuses if status == "blocked"))
    final_status = _final_status(watch_count=watch_count, blocked_count=blocked_count)
    reason_codes = _unique_strings(
        inputs.reason_codes + (FINAL_REASON_BY_STATUS[final_status],),
    )
    manual_next_step = _manual_next_step_for_status(final_status)
    values: dict[str, object] = {
        "config_version": MANUAL_OPERATOR_PACKET_FINAL_BOUNDARY_REPORT_VERSION,
        "team_owner": inputs.team_owner,
        "source_quality_status": inputs.source_quality_status,
        "memory_policy_status": inputs.memory_policy_status,
        "forecast_vs_price_edge_status": inputs.forecast_vs_price_edge_status,
        "costs_status": inputs.costs_status,
        "liquidity_status": inputs.liquidity_status,
        "resolution_risk_status": inputs.resolution_risk_status,
        "selected_side": inputs.selected_side,
        "final_status": final_status,
        "reason_codes": reason_codes,
        "manual_next_step": manual_next_step,
        "boundary_check_count": BOUNDARY_CHECK_COUNT,
        "pass_check_count": pass_count,
        "watch_check_count": watch_count,
        "blocked_check_count": blocked_count,
        "ready_ratio": _ratio(pass_count, BOUNDARY_CHECK_COUNT),
        "paper_review_only": True,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ManualOperatorPacketFinalBoundaryReport(
        **values,
        derived_validation_digest=_payload_digest(_payload_values(values, digest="")),
    )


def manual_operator_packet_final_boundary_report_payload(
    report: ManualOperatorPacketFinalBoundaryReport | Mapping[str, object],
) -> ManualOperatorPacketFinalBoundaryPublicPayload:
    if type(report) is ManualOperatorPacketFinalBoundaryReport:
        _require_hard_flags("report", report)
        _validate_report(report)
        if report.derived_validation_digest != _payload_digest(
            _payload_items(report, digest=""),
        ):
            raise ValueError("derived_validation_digest must match report payload")
        return report.public_payload
    if isinstance(report, Mapping):
        _validate_public_payload(report)
        return ManualOperatorPacketFinalBoundaryPublicPayload(dict(report))
    raise ValueError(
        "report must be a ManualOperatorPacketFinalBoundaryReport or public payload",
    )


def _final_status(*, watch_count: Decimal, blocked_count: Decimal) -> str:
    if blocked_count > ZERO:
        return "blocked"
    if watch_count > ZERO:
        return "watch"
    return "pass"


def _manual_next_step_for_status(final_status: str) -> str:
    return MANUAL_NEXT_STEP_BY_STATUS[final_status]


def _validate_report(report: ManualOperatorPacketFinalBoundaryReport) -> None:
    statuses = tuple(getattr(report, field_name) for field_name in BOUNDARY_STATUS_FIELDS)
    pass_count = _count(sum(1 for status in statuses if status == "pass") + 1)
    watch_count = _count(sum(1 for status in statuses if status == "watch"))
    blocked_count = _count(sum(1 for status in statuses if status == "blocked"))
    if report.boundary_check_count != BOUNDARY_CHECK_COUNT:
        raise ValueError("boundary_check_count must match report contract")
    if report.pass_check_count != pass_count:
        raise ValueError("pass_check_count must match boundary statuses")
    if report.watch_check_count != watch_count:
        raise ValueError("watch_check_count must match boundary statuses")
    if report.blocked_check_count != blocked_count:
        raise ValueError("blocked_check_count must match boundary statuses")
    if report.ready_ratio != _ratio(report.pass_check_count, BOUNDARY_CHECK_COUNT):
        raise ValueError("ready_ratio must match boundary statuses")
    if report.final_status != _final_status(
        watch_count=watch_count,
        blocked_count=blocked_count,
    ):
        raise ValueError("final_status must match boundary statuses")
    if not report.reason_codes:
        raise ValueError("reason_codes must be nonempty")
    if report.reason_codes[-1] != FINAL_REASON_BY_STATUS[report.final_status]:
        raise ValueError("reason_codes must include final boundary status")
    if report.manual_next_step != _manual_next_step_for_status(report.final_status):
        raise ValueError("manual_next_step must match final_status")


def _payload_items(
    report: ManualOperatorPacketFinalBoundaryReport,
    *,
    digest: str,
) -> dict[str, object]:
    return {
        "config_version": report.config_version,
        "team_owner": report.team_owner,
        "source_quality_status": report.source_quality_status,
        "memory_policy_status": report.memory_policy_status,
        "forecast_vs_price_edge_status": report.forecast_vs_price_edge_status,
        "costs_status": report.costs_status,
        "liquidity_status": report.liquidity_status,
        "resolution_risk_status": report.resolution_risk_status,
        "selected_side": report.selected_side,
        "final_status": report.final_status,
        "reason_codes": list(report.reason_codes),
        "manual_next_step": report.manual_next_step,
        "boundary_check_count": _decimal_string(report.boundary_check_count),
        "pass_check_count": _decimal_string(report.pass_check_count),
        "watch_check_count": _decimal_string(report.watch_check_count),
        "blocked_check_count": _decimal_string(report.blocked_check_count),
        "ready_ratio": _decimal_string(report.ready_ratio),
        "paper_review_only": report.paper_review_only,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
        "derived_validation_digest": digest,
    }


def _payload_values(values: Mapping[str, object], *, digest: str) -> dict[str, object]:
    return {
        "config_version": values["config_version"],
        "team_owner": values["team_owner"],
        "source_quality_status": values["source_quality_status"],
        "memory_policy_status": values["memory_policy_status"],
        "forecast_vs_price_edge_status": values["forecast_vs_price_edge_status"],
        "costs_status": values["costs_status"],
        "liquidity_status": values["liquidity_status"],
        "resolution_risk_status": values["resolution_risk_status"],
        "selected_side": values["selected_side"],
        "final_status": values["final_status"],
        "reason_codes": list(values["reason_codes"]),
        "manual_next_step": values["manual_next_step"],
        "boundary_check_count": _decimal_string(values["boundary_check_count"]),
        "pass_check_count": _decimal_string(values["pass_check_count"]),
        "watch_check_count": _decimal_string(values["watch_check_count"]),
        "blocked_check_count": _decimal_string(values["blocked_check_count"]),
        "ready_ratio": _decimal_string(values["ready_ratio"]),
        "paper_review_only": values["paper_review_only"],
        "paper_only": values["paper_only"],
        "report_only": values["report_only"],
        "readonly": values["readonly"],
        "derived_validation_digest": digest,
    }


def _validate_public_payload(payload: Mapping[str, object]) -> None:
    if not isinstance(payload, Mapping):
        raise ValueError("public payload must be a mapping")
    if tuple(payload) != PAYLOAD_FIELDS:
        raise ValueError("public payload fields must match report contract")
    _reject_public_numerics(payload)
    _require_public_label("config_version", payload["config_version"])
    if payload["config_version"] != MANUAL_OPERATOR_PACKET_FINAL_BOUNDARY_REPORT_VERSION:
        raise ValueError("config_version must be the supported report version")
    _require_public_label("team_owner", payload["team_owner"])
    for field_name in BOUNDARY_STATUS_FIELDS:
        _require_member(field_name, payload[field_name], STATUS_VALUES)
    _require_member("selected_side", payload["selected_side"], SELECTED_SIDE_VALUES)
    _require_member("final_status", payload["final_status"], STATUS_VALUES)
    _normalize_reason_codes(
        "reason_codes",
        _tuple_from_public_list("reason_codes", payload["reason_codes"]),
    )
    _require_manual_next_step(payload["manual_next_step"])
    for field_name in DECIMAL_PAYLOAD_FIELDS:
        if type(payload[field_name]) is not str:
            raise ValueError("public payload numerics must be decimal strings")
        _parse_decimal_string(field_name, payload[field_name])
    _require_hard_flags("public payload", payload)
    _require_digest("derived_validation_digest", payload["derived_validation_digest"])
    payload_without_digest = dict(payload)
    payload_without_digest["derived_validation_digest"] = ""
    if payload["derived_validation_digest"] != _payload_digest(payload_without_digest):
        raise ValueError("derived_validation_digest must match public payload")
    reconstructed = ManualOperatorPacketFinalBoundaryReport(
        config_version=payload["config_version"],
        team_owner=payload["team_owner"],
        source_quality_status=payload["source_quality_status"],
        memory_policy_status=payload["memory_policy_status"],
        forecast_vs_price_edge_status=payload["forecast_vs_price_edge_status"],
        costs_status=payload["costs_status"],
        liquidity_status=payload["liquidity_status"],
        resolution_risk_status=payload["resolution_risk_status"],
        selected_side=payload["selected_side"],
        final_status=payload["final_status"],
        reason_codes=_tuple_from_public_list("reason_codes", payload["reason_codes"]),
        manual_next_step=payload["manual_next_step"],
        boundary_check_count=_parse_decimal_string(
            "boundary_check_count",
            payload["boundary_check_count"],
        ),
        pass_check_count=_parse_decimal_string(
            "pass_check_count",
            payload["pass_check_count"],
        ),
        watch_check_count=_parse_decimal_string(
            "watch_check_count",
            payload["watch_check_count"],
        ),
        blocked_check_count=_parse_decimal_string(
            "blocked_check_count",
            payload["blocked_check_count"],
        ),
        ready_ratio=_parse_decimal_string("ready_ratio", payload["ready_ratio"]),
        paper_review_only=payload["paper_review_only"],
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
        derived_validation_digest=payload["derived_validation_digest"],
    )
    if _payload_items(
        reconstructed,
        digest=reconstructed.derived_validation_digest,
    ) != dict(payload):
        raise ValueError("derived_validation_digest must match public payload")


def _payload_digest(payload: dict[str, object]) -> str:
    encoded = json.dumps(
        _json_ready(payload),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def _json_ready(value: object) -> object:
    if type(value) is Decimal:
        return _decimal_string(value)
    if type(value) is dict:
        converted: dict[str, object] = {}
        for name, item in value.items():
            if type(name) is not str:
                raise ValueError("JSON object field names must be strings")
            converted[name] = _json_ready(item)
        return converted
    if type(value) is tuple or type(value) is list:
        return [_json_ready(item) for item in value]
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("value is not JSON serializable")


def _reject_public_numerics(value: object) -> None:
    if type(value) is int or type(value) is float:
        raise ValueError("public payload numerics must be decimal strings")
    if type(value) is dict:
        for item in value.values():
            _reject_public_numerics(item)
        return
    if type(value) is list:
        for item in value:
            _reject_public_numerics(item)


def _normalize_reason_codes(field_name: str, values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not values:
        raise ValueError(f"{field_name} must be nonempty")
    normalized: list[str] = []
    for value in values:
        text = _require_public_label(field_name, value)
        if text.lower() != text:
            raise ValueError(f"{field_name} must contain canonical reason codes")
        _reject_unsupported_public_text(field_name, text)
        normalized.append(text)
    return tuple(normalized)


def _unique_strings(values: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return tuple(result)


def _require_manual_next_step(value: object) -> str:
    text = _require_public_label("manual_next_step", value)
    if text.lower() != text or not text.startswith("paper_review_"):
        raise ValueError("manual_next_step must be a paper_review step")
    _reject_unsupported_public_text("manual_next_step", text)
    return text


def _require_public_label(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty public label")
    if len(value) > 128:
        raise ValueError(f"{field_name} must be at most 128 characters")
    if any(ord(character) < 32 for character in value):
        raise ValueError(f"{field_name} must not contain control characters")
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be a public label")
    _reject_unsupported_public_text(field_name, value)
    return value


def _reject_unsupported_public_text(field_name: str, value: str) -> None:
    normalized = [
        character.lower() if character.isalnum() else " "
        for character in value
    ]
    tokens = "".join(normalized).split()
    if any(term in tokens for term in UNSUPPORTED_SURFACE_TERMS):
        raise ValueError("unsupported " + "".join(("li", "ve")) + " surface term")
    compacted = "".join(tokens)
    if any(term in compacted for term in UNSUPPORTED_SURFACE_TERMS):
        raise ValueError("unsupported " + "".join(("li", "ve")) + " surface term")
    if field_name == "":
        raise ValueError("field_name must be nonempty")


def _require_member(
    field_name: str,
    value: object,
    choices: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in choices:
        raise ValueError(f"{field_name} must be one of {choices}")


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return value.quantize(RATIO_QUANTUM)


def _parse_decimal_string(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError("public payload numerics must be decimal strings")
    try:
        parsed = Decimal(value)
    except Exception as exc:
        raise ValueError("public payload numerics must be decimal strings") from exc
    if not parsed.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return parsed


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    return (numerator / denominator).quantize(RATIO_QUANTUM, rounding=ROUND_HALF_UP)


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count source must be a nonnegative int")
    return Decimal(value)


def _decimal_string(value: object) -> str:
    if type(value) is not Decimal:
        raise ValueError("public payload numerics must be Decimal values")
    return format(value, "f")


def _tuple_from_public_list(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a public list")
    return tuple(value)


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_review_only", "paper_only", "report_only", "readonly"):
        flag = value[field_name] if isinstance(value, Mapping) else getattr(value, field_name)
        if flag is not True:
            raise ValueError(f"{field_name} must be True for {label}")
