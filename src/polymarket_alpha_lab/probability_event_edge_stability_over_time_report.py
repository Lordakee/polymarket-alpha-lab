from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Context, Decimal, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_PROBABILITY_EVENT_EDGE_STABILITY_OVER_TIME_CONFIG_VERSION = (
    "probability-event-edge-stability-over-time-v0"
)

__all__ = (
    "DEFAULT_PROBABILITY_EVENT_EDGE_STABILITY_OVER_TIME_CONFIG_VERSION",
    "ProbabilityEventEdgeStabilityOverTimeInput",
    "ProbabilityEventEdgeStabilityOverTimeReport",
    "build_probability_event_edge_stability_over_time_report",
    "probability_event_edge_stability_over_time_payload",
)


ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
DECIMAL_CONTEXT = Context(prec=64)
STATUSES = frozenset(("stable", "watch", "block"))
STALE_EDGE_AGE_HOURS = Decimal("72.000000")


@dataclass(frozen=True)
class ProbabilityEventEdgeStabilityOverTimeInput:
    initial_edge_probability: Decimal
    current_edge_probability: Decimal
    edge_age_hours: Decimal
    market_move_probability: Decimal
    stability_threshold_probability: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventEdgeStabilityOverTimeInput:
            raise ValueError(
                "input must be exactly ProbabilityEventEdgeStabilityOverTimeInput",
            )
        for field_name in (
            "initial_edge_probability",
            "current_edge_probability",
            "market_move_probability",
            "stability_threshold_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "edge_age_hours",
            _require_nonnegative_decimal("edge_age_hours", self.edge_age_hours),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ProbabilityEventEdgeStabilityOverTimeReport:
    config_version: str
    initial_edge_probability: Decimal
    current_edge_probability: Decimal
    edge_age_hours: Decimal
    market_move_probability: Decimal
    stability_threshold_probability: Decimal
    edge_stability_status: str
    edge_drift_probability: Decimal
    reason_codes: tuple[str, ...]
    manual_next_step: str
    payload_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventEdgeStabilityOverTimeReport:
            raise ValueError(
                "report must be exactly ProbabilityEventEdgeStabilityOverTimeReport",
            )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_PROBABILITY_EVENT_EDGE_STABILITY_OVER_TIME_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "initial_edge_probability",
            "current_edge_probability",
            "market_move_probability",
            "stability_threshold_probability",
            "edge_drift_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "edge_age_hours",
            _require_nonnegative_decimal("edge_age_hours", self.edge_age_hours),
        )
        _require_status("edge_stability_status", self.edge_stability_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_manual_next_step(self.manual_next_step)
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        _set_or_validate_digest(self)

    @property
    def public_payload(self) -> dict[str, Any]:
        return probability_event_edge_stability_over_time_payload(self)


def build_probability_event_edge_stability_over_time_report(
    *,
    initial_edge_probability: Decimal,
    current_edge_probability: Decimal,
    edge_age_hours: Decimal,
    market_move_probability: Decimal,
    stability_threshold_probability: Decimal,
) -> ProbabilityEventEdgeStabilityOverTimeReport:
    input_row = ProbabilityEventEdgeStabilityOverTimeInput(
        initial_edge_probability=initial_edge_probability,
        current_edge_probability=current_edge_probability,
        edge_age_hours=edge_age_hours,
        market_move_probability=market_move_probability,
        stability_threshold_probability=stability_threshold_probability,
    )
    edge_drift_probability = _abs_decimal(
        input_row.initial_edge_probability - input_row.current_edge_probability,
    )
    edge_stability_status = _edge_stability_status(
        edge_drift_probability=edge_drift_probability,
        edge_age_hours=input_row.edge_age_hours,
        market_move_probability=input_row.market_move_probability,
        stability_threshold_probability=input_row.stability_threshold_probability,
    )
    return ProbabilityEventEdgeStabilityOverTimeReport(
        config_version=DEFAULT_PROBABILITY_EVENT_EDGE_STABILITY_OVER_TIME_CONFIG_VERSION,
        initial_edge_probability=input_row.initial_edge_probability,
        current_edge_probability=input_row.current_edge_probability,
        edge_age_hours=input_row.edge_age_hours,
        market_move_probability=input_row.market_move_probability,
        stability_threshold_probability=input_row.stability_threshold_probability,
        edge_stability_status=edge_stability_status,
        edge_drift_probability=edge_drift_probability,
        reason_codes=_reason_codes(
            edge_stability_status=edge_stability_status,
            edge_drift_probability=edge_drift_probability,
            edge_age_hours=input_row.edge_age_hours,
            market_move_probability=input_row.market_move_probability,
            stability_threshold_probability=input_row.stability_threshold_probability,
        ),
        manual_next_step=_manual_next_step(edge_stability_status),
    )


def probability_event_edge_stability_over_time_payload(
    report: ProbabilityEventEdgeStabilityOverTimeReport,
) -> dict[str, Any]:
    if type(report) is not ProbabilityEventEdgeStabilityOverTimeReport:
        raise ValueError("report must be a ProbabilityEventEdgeStabilityOverTimeReport")
    _require_hard_flags("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _edge_stability_status(
    *,
    edge_drift_probability: Decimal,
    edge_age_hours: Decimal,
    market_move_probability: Decimal,
    stability_threshold_probability: Decimal,
) -> str:
    if (
        edge_drift_probability > stability_threshold_probability * Decimal("2.000000")
        or market_move_probability > stability_threshold_probability
        or edge_age_hours >= STALE_EDGE_AGE_HOURS
    ):
        return "block"
    if edge_drift_probability > stability_threshold_probability:
        return "watch"
    return "stable"


def _reason_codes(
    *,
    edge_stability_status: str,
    edge_drift_probability: Decimal,
    edge_age_hours: Decimal,
    market_move_probability: Decimal,
    stability_threshold_probability: Decimal,
) -> tuple[str, ...]:
    reason_codes = [f"edge_stability_{edge_stability_status}"]
    if edge_drift_probability > stability_threshold_probability:
        reason_codes.append("edge_drift_above_threshold")
    if edge_age_hours >= STALE_EDGE_AGE_HOURS:
        reason_codes.append("edge_stale_over_time")
    if market_move_probability > stability_threshold_probability:
        reason_codes.append("market_move_above_threshold")
    return tuple(reason_codes)


def _manual_next_step(edge_stability_status: str) -> str:
    if edge_stability_status == "block":
        return "manual_rebuild_required"
    if edge_stability_status == "watch":
        return "manual_review_edge_drift"
    return "continue_manual_watch"


def _validate_report_consistency(
    report: ProbabilityEventEdgeStabilityOverTimeReport,
) -> None:
    expected_drift = _abs_decimal(
        report.initial_edge_probability - report.current_edge_probability,
    )
    if report.edge_drift_probability != expected_drift:
        raise ValueError("edge_drift_probability must equal absolute edge movement")
    expected_status = _edge_stability_status(
        edge_drift_probability=expected_drift,
        edge_age_hours=report.edge_age_hours,
        market_move_probability=report.market_move_probability,
        stability_threshold_probability=report.stability_threshold_probability,
    )
    if report.edge_stability_status != expected_status:
        raise ValueError("edge_stability_status must match report inputs")
    expected_reason_codes = _reason_codes(
        edge_stability_status=expected_status,
        edge_drift_probability=expected_drift,
        edge_age_hours=report.edge_age_hours,
        market_move_probability=report.market_move_probability,
        stability_threshold_probability=report.stability_threshold_probability,
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match report inputs")
    if report.manual_next_step != _manual_next_step(expected_status):
        raise ValueError("manual_next_step must match edge_stability_status")


def _set_or_validate_digest(report: ProbabilityEventEdgeStabilityOverTimeReport) -> None:
    expected_digest = _payload_digest(_payload_without_digest(report))
    if report.payload_digest:
        _require_digest("payload_digest", report.payload_digest)
        if report.payload_digest != expected_digest:
            raise ValueError("payload_digest must match report payload")
        return
    object.__setattr__(report, "payload_digest", expected_digest)


def _payload_without_digest(
    report: ProbabilityEventEdgeStabilityOverTimeReport,
) -> dict[str, Any]:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload["payload_digest"] = ""
    return payload


def _payload_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(_ordered_json_value(payload), separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _ordered_json_value(value: object) -> Any:
    if isinstance(value, dict):
        return {str(item_key): _ordered_json_value(item) for item_key, item in sorted(value.items())}
    if isinstance(value, list):
        return [_ordered_json_value(item) for item in value]
    return value


def _json_ready(value: object) -> Any:
    if isinstance(value, Decimal):
        return format(value, ".6f")
    if is_dataclass(value) and not isinstance(value, type):
        return {
            key: _json_ready(item)
            for key, item in asdict(value).items()
            if key != "public_payload"
        }
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def _normalize_reason_codes(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError(f"{field_name} must be a nonempty tuple")
    normalized = tuple(_require_public_slug(field_name, item) for item in value)
    if normalized != tuple(sorted(set(normalized), key=normalized.index)):
        raise ValueError(f"{field_name} must not contain duplicates")
    return normalized


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_exact_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_exact_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_exact_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    return _quantize(value)


def _abs_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(abs(value))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a nonempty string")


def _require_public_slug(field_name: str, value: object) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a nonempty string")
    if not all(character.islower() or character.isdigit() or character == "_" for character in value):
        raise ValueError(f"{field_name} must be a public slug")
    return value


def _require_status(field_name: str, value: object) -> None:
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be stable, watch, or block")


def _require_manual_next_step(value: object) -> None:
    if value not in {
        "continue_manual_watch",
        "manual_review_edge_drift",
        "manual_rebuild_required",
    }:
        raise ValueError("manual_next_step must be supported")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if not all(character in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} must be {flag_name}")
