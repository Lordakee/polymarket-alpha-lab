"""Public-safe specialist team routing drift monitor report."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
from typing import Any


DEFAULT_SPECIALIST_TEAM_ROUTING_DRIFT_MONITOR_CONFIG_VERSION = (
    "specialist-team-routing-drift-monitor-report-v0"
)

SPECIALIST_TEAM_ROUTING_DRIFT_MONITOR_STATUSES = ("pass", "watch", "block")

ZERO_DELTA = Decimal("0.000000")
ONE_DELTA = Decimal("1.000000")
MINUS_ONE_DELTA = Decimal("-1.000000")
DELTA_QUANTUM = Decimal("0.000001")

TEAM_CHANGED_REASON = "specialist_team_routing_drift_team_changed"
CONFIDENCE_DROP_BLOCK_REASON = "specialist_team_routing_drift_confidence_drop_block"
MEMORY_POLICY_BLOCK_REASON = "specialist_team_routing_drift_memory_policy_block"
SOURCE_QUORUM_BLOCK_REASON = "specialist_team_routing_drift_source_quorum_block"
CONFIDENCE_DROP_WATCH_REASON = "specialist_team_routing_drift_confidence_drop_watch"
MEMORY_POLICY_WATCH_REASON = "specialist_team_routing_drift_memory_policy_watch"
SOURCE_QUORUM_WATCH_REASON = "specialist_team_routing_drift_source_quorum_watch"
CLEAR_REASON = "specialist_team_routing_drift_clear"

REASON_CODE_SEQUENCE = (
    TEAM_CHANGED_REASON,
    CONFIDENCE_DROP_BLOCK_REASON,
    MEMORY_POLICY_BLOCK_REASON,
    SOURCE_QUORUM_BLOCK_REASON,
    CONFIDENCE_DROP_WATCH_REASON,
    MEMORY_POLICY_WATCH_REASON,
    SOURCE_QUORUM_WATCH_REASON,
    CLEAR_REASON,
)

MANUAL_NEXT_STEP_BY_STATUS = {
    "pass": "manual_no_action",
    "watch": "manual_review_routing_drift_evidence",
    "block": "manual_escalate_routing_drift_review",
}

PUBLIC_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789_.-")


def _join(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "raw",
        "candidate",
        "market",
        "slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "secret",
        "credential",
        _join("au", "th"),
        _join("wal", "let"),
        _join("or", "der"),
        _join("tra", "de"),
        "trading",
        _join("li", "ve"),
        "position",
        "sizing",
        "recommend",
    ),
)

__all__ = (
    "DEFAULT_SPECIALIST_TEAM_ROUTING_DRIFT_MONITOR_CONFIG_VERSION",
    "SPECIALIST_TEAM_ROUTING_DRIFT_MONITOR_STATUSES",
    "SpecialistTeamRoutingDriftMonitorConfig",
    "SpecialistTeamRoutingDriftMonitorInput",
    "SpecialistTeamRoutingDriftMonitorReport",
    "build_specialist_team_routing_drift_monitor_report",
    "specialist_team_routing_drift_monitor_report_digest",
    "specialist_team_routing_drift_monitor_report_payload",
)


class _FinalData:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalData and issubclass(base, _FinalData):
                raise TypeError(f"{base.__name__} child class is not allowed")


@dataclass(frozen=True)
class SpecialistTeamRoutingDriftMonitorConfig(_FinalData):
    config_version: str = DEFAULT_SPECIALIST_TEAM_ROUTING_DRIFT_MONITOR_CONFIG_VERSION
    watch_confidence_drop_threshold: Decimal = Decimal("-0.150000")
    block_confidence_drop_threshold: Decimal = Decimal("-0.300000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, SpecialistTeamRoutingDriftMonitorConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_public_label("config_version", self.config_version),
        )
        if self.config_version != DEFAULT_SPECIALIST_TEAM_ROUTING_DRIFT_MONITOR_CONFIG_VERSION:
            raise ValueError("config_version must be the supported version")
        for field_name in (
            "watch_confidence_drop_threshold",
            "block_confidence_drop_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_delta_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_confidence_drop_threshold > self.watch_confidence_drop_threshold:
            raise ValueError("block_confidence_drop_threshold must not exceed watch")
        if self.watch_confidence_drop_threshold > ZERO_DELTA:
            raise ValueError("watch_confidence_drop_threshold must not exceed zero")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class SpecialistTeamRoutingDriftMonitorInput(_FinalData):
    previous_primary_team: str
    current_primary_team: str
    route_confidence_delta: Decimal
    category_id: str
    memory_policy_status: str
    source_quorum_status: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, SpecialistTeamRoutingDriftMonitorInput, "input")
        for field_name in ("previous_primary_team", "current_primary_team", "category_id"):
            object.__setattr__(
                self,
                field_name,
                _require_public_label(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "route_confidence_delta",
            _require_delta_decimal("route_confidence_delta", self.route_confidence_delta),
        )
        for field_name in ("memory_policy_status", "source_quorum_status"):
            object.__setattr__(
                self,
                field_name,
                _require_status(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class SpecialistTeamRoutingDriftMonitorReport(_FinalData):
    config_version: str
    previous_primary_team: str
    current_primary_team: str
    route_confidence_delta: Decimal
    category_id: str
    memory_policy_status: str
    source_quorum_status: str
    routing_drift_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, SpecialistTeamRoutingDriftMonitorReport, "report")
        object.__setattr__(
            self,
            "config_version",
            _require_public_label("config_version", self.config_version),
        )
        if self.config_version != DEFAULT_SPECIALIST_TEAM_ROUTING_DRIFT_MONITOR_CONFIG_VERSION:
            raise ValueError("config_version must be the supported version")
        for field_name in ("previous_primary_team", "current_primary_team", "category_id"):
            object.__setattr__(
                self,
                field_name,
                _require_public_label(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "route_confidence_delta",
            _require_delta_decimal("route_confidence_delta", self.route_confidence_delta),
        )
        for field_name in ("memory_policy_status", "source_quorum_status"):
            object.__setattr__(
                self,
                field_name,
                _require_status(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "routing_drift_status",
            _require_status("routing_drift_status", self.routing_drift_status),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(self.reason_codes),
        )
        if self.routing_drift_status != _status_from_reason_codes(self.reason_codes):
            raise ValueError("routing_drift_status must match reason_codes")
        object.__setattr__(
            self,
            "manual_next_step",
            _require_public_label("manual_next_step", self.manual_next_step),
        )
        if self.manual_next_step != MANUAL_NEXT_STEP_BY_STATUS[self.routing_drift_status]:
            raise ValueError("manual_next_step must match routing_drift_status")
        _require_hard_flags("report", self)
        if self.derived_validation_digest:
            _require_sha256("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != _digest_from_payload(_report_payload(self)):
                raise ValueError("derived_validation_digest does not match report payload")
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _digest_from_payload(_report_payload(self)),
            )


def build_specialist_team_routing_drift_monitor_report(
    item: SpecialistTeamRoutingDriftMonitorInput,
    *,
    config: SpecialistTeamRoutingDriftMonitorConfig,
) -> SpecialistTeamRoutingDriftMonitorReport:
    _require_exact_type(item, SpecialistTeamRoutingDriftMonitorInput, "input")
    _require_exact_type(config, SpecialistTeamRoutingDriftMonitorConfig, "config")
    _require_hard_flags("input", item)
    _require_hard_flags("config", config)
    reason_codes = _row_reason_codes(item, config)
    status = _status_from_reason_codes(reason_codes)
    return SpecialistTeamRoutingDriftMonitorReport(
        config_version=config.config_version,
        previous_primary_team=item.previous_primary_team,
        current_primary_team=item.current_primary_team,
        route_confidence_delta=item.route_confidence_delta,
        category_id=item.category_id,
        memory_policy_status=item.memory_policy_status,
        source_quorum_status=item.source_quorum_status,
        routing_drift_status=status,
        reason_codes=reason_codes,
        manual_next_step=MANUAL_NEXT_STEP_BY_STATUS[status],
    )


def specialist_team_routing_drift_monitor_report_payload(
    report: SpecialistTeamRoutingDriftMonitorReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is SpecialistTeamRoutingDriftMonitorReport:
        _require_hard_flags("report", report)
        if report.derived_validation_digest != _digest_from_payload(_report_payload(report)):
            raise ValueError("derived_validation_digest does not match report payload")
        payload = _report_payload(report, include_digest=True)
        _reject_unsafe_public_payload("payload", payload)
        return payload
    if type(report) is dict:
        _require_hard_flags("payload", _PayloadFlags(report))
        supplied_digest = report.get("derived_validation_digest")
        if type(supplied_digest) is not str:
            raise ValueError("derived_validation_digest is required")
        _require_sha256("derived_validation_digest", supplied_digest)
        if supplied_digest != _digest_from_payload(report):
            raise ValueError("derived_validation_digest does not match report payload")
        _reject_unsafe_public_payload("payload", report)
        _require_public_payload_schema(report)
        return report
    raise ValueError("report must be a SpecialistTeamRoutingDriftMonitorReport")


def specialist_team_routing_drift_monitor_report_digest(
    report: SpecialistTeamRoutingDriftMonitorReport | dict[str, Any],
) -> str:
    payload = specialist_team_routing_drift_monitor_report_payload(report)
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest


@dataclass(frozen=True)
class _PayloadFlags:
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


def _row_reason_codes(
    item: SpecialistTeamRoutingDriftMonitorInput,
    config: SpecialistTeamRoutingDriftMonitorConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if item.previous_primary_team != item.current_primary_team:
        reasons.append(TEAM_CHANGED_REASON)
    if item.route_confidence_delta <= config.block_confidence_drop_threshold:
        reasons.append(CONFIDENCE_DROP_BLOCK_REASON)
    elif item.route_confidence_delta <= config.watch_confidence_drop_threshold:
        reasons.append(CONFIDENCE_DROP_WATCH_REASON)
    if item.memory_policy_status == "block":
        reasons.append(MEMORY_POLICY_BLOCK_REASON)
    elif item.memory_policy_status == "watch":
        reasons.append(MEMORY_POLICY_WATCH_REASON)
    if item.source_quorum_status == "block":
        reasons.append(SOURCE_QUORUM_BLOCK_REASON)
    elif item.source_quorum_status == "watch":
        reasons.append(SOURCE_QUORUM_WATCH_REASON)
    return _require_reason_codes(tuple(reasons) or (CLEAR_REASON,))


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if reason_codes != (CLEAR_REASON,):
        return "watch"
    return "pass"


def _require_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in REASON_CODE_SEQUENCE:
            raise ValueError("reason_codes must be supported")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    expected = tuple(
        reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in reason_codes
    )
    if reason_codes != expected:
        raise ValueError("reason_codes must be deterministic")
    if CLEAR_REASON in reason_codes and reason_codes != (CLEAR_REASON,):
        raise ValueError("clear reason must stand alone")
    return reason_codes


def _require_public_payload_schema(payload: dict[str, Any]) -> None:
    expected_keys = {
        "config_version",
        "previous_primary_team",
        "current_primary_team",
        "route_confidence_delta",
        "category_id",
        "memory_policy_status",
        "source_quorum_status",
        "routing_drift_status",
        "reason_codes",
        "manual_next_step",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    }
    actual_keys = set(payload)
    if actual_keys != expected_keys:
        raise ValueError("payload fields must match report schema")
    if payload["config_version"] != DEFAULT_SPECIALIST_TEAM_ROUTING_DRIFT_MONITOR_CONFIG_VERSION:
        raise ValueError("config_version must be the supported version")
    for field_name in ("previous_primary_team", "current_primary_team", "category_id"):
        _require_public_label(field_name, payload[field_name])
    delta = _require_delta_string("route_confidence_delta", payload["route_confidence_delta"])
    _require_status("memory_policy_status", payload["memory_policy_status"])
    _require_status("source_quorum_status", payload["source_quorum_status"])
    status = _require_status("routing_drift_status", payload["routing_drift_status"])
    reason_codes = _require_reason_codes(payload["reason_codes"])
    if status != _status_from_reason_codes(reason_codes):
        raise ValueError("routing_drift_status must match reason_codes")
    if payload["manual_next_step"] != MANUAL_NEXT_STEP_BY_STATUS[status]:
        raise ValueError("manual_next_step must match routing_drift_status")
    if str(delta) != payload["route_confidence_delta"]:
        raise ValueError("route_confidence_delta must be canonical")


def _report_payload(
    report: SpecialistTeamRoutingDriftMonitorReport,
    *,
    include_digest: bool = False,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "config_version": report.config_version,
        "previous_primary_team": report.previous_primary_team,
        "current_primary_team": report.current_primary_team,
        "route_confidence_delta": str(report.route_confidence_delta),
        "category_id": report.category_id,
        "memory_policy_status": report.memory_policy_status,
        "source_quorum_status": report.source_quorum_status,
        "routing_drift_status": report.routing_drift_status,
        "reason_codes": list(report.reason_codes),
        "manual_next_step": report.manual_next_step,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    if include_digest:
        payload["derived_validation_digest"] = report.derived_validation_digest
    return payload


def _digest_from_payload(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _require_exact_type(value: object, expected_type: type, label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_label(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be public text")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be public text")
    lowered = value.casefold()
    if any(character not in PUBLIC_CHARS for character in lowered):
        raise ValueError(f"{field_name} must be public text")
    if _has_unsafe_public_fragment(lowered):
        raise ValueError(f"{field_name} must be public text")
    return lowered


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in SPECIALIST_TEAM_ROUTING_DRIFT_MONITOR_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_delta_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < MINUS_ONE_DELTA:
        raise ValueError(f"{field_name} must be >= -1.000000")
    if value > ONE_DELTA:
        raise ValueError(f"{field_name} must be <= 1.000000")
    if value != value.quantize(DELTA_QUANTUM):
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return value.quantize(DELTA_QUANTUM)


def _require_delta_string(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        return _require_delta_decimal(field_name, Decimal(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _require_sha256(field_name: str, value: object) -> str:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")
    return value


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    current_path = path or label
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"{current_path}.{key} has unsafe public field")
            _reject_unsafe_public_payload(label, item, f"{current_path}.{key}")
        return
    if type(value) is list:
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(label, item, f"{current_path}[{index}]")
        return
    if type(value) is str:
        if value.strip() != value or _has_unsafe_public_fragment(value):
            raise ValueError(f"{current_path} has unsafe public value")
        return
    if type(value) is bool or value is None:
        return
    if type(value) in (int, float):
        raise ValueError(f"{current_path} must use Decimal-derived string values")
    raise ValueError(f"{current_path} is not JSON-ready")


def _has_unsafe_public_fragment(value: str) -> bool:
    lowered = value.casefold()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)
