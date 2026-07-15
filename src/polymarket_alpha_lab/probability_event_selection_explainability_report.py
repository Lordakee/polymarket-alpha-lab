"""Paper-only explainability report for probability event selection."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any


DEFAULT_CONFIG_VERSION = "probability-event-selection-explainability-v0"
ZERO = Decimal("0")
QUANTUM = Decimal("0.000001")

COMPONENT_NAMES = (
    "screen",
    "team_route",
    "memory_policy",
    "source_quality",
    "cost_gate",
    "operator_packet",
)
COMPONENT_INPUTS = (
    "screen_status",
    "team_route_status",
    "memory_policy",
    "source_quality_status",
    "cost_gate_status",
    "operator_packet_status",
)
STATUSES = ("pass", "watch", "blocked")
SELECTION_STATUSES = ("ready", "watch", "blocked")
FORBIDDEN_PUBLIC_TERMS = (
    "account",
    "wallet",
    "key",
    "order",
    "live",
)


@dataclass(frozen=True)
class ProbabilityEventSelectionExplainabilityConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ProbabilityEventSelectionComponentStatus:
    component_name: str
    status: str
    reason_codes: tuple[str, ...]
    summary: str
    severity_score: Decimal = ZERO
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_component_name("component_name", self.component_name)
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_public_summary("summary", self.summary)
        object.__setattr__(
            self,
            "severity_score",
            _normalize_nonnegative_decimal("severity_score", self.severity_score),
        )
        _validate_component_reason_codes(self)
        _require_hard_flags("component_status", self)


@dataclass(frozen=True)
class ProbabilityEventSelectionExplainabilityReport:
    generated_at: datetime
    config_version: str
    selection_status: str
    selection_explanation: str
    component_count: int
    pass_count: int
    watch_count: int
    blocked_count: int
    component_statuses: tuple[ProbabilityEventSelectionComponentStatus, ...]
    blocked_reason_codes: tuple[str, ...]
    watch_reason_codes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_selection_status("selection_status", self.selection_status)
        _require_public_summary("selection_explanation", self.selection_explanation)
        for field_name in ("component_count", "pass_count", "watch_count", "blocked_count"):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "component_statuses",
            _normalize_component_statuses(self.component_statuses),
        )
        object.__setattr__(
            self,
            "blocked_reason_codes",
            _normalize_reason_codes("blocked_reason_codes", self.blocked_reason_codes),
        )
        object.__setattr__(
            self,
            "watch_reason_codes",
            _normalize_reason_codes("watch_reason_codes", self.watch_reason_codes),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_report_consistency(self)
        _require_hard_flags("explainability_report", self)

    @property
    def status(self) -> str:
        return self.selection_status


def build_probability_event_selection_explainability_report(
    *,
    screen_status: ProbabilityEventSelectionComponentStatus,
    team_route_status: ProbabilityEventSelectionComponentStatus,
    memory_policy: ProbabilityEventSelectionComponentStatus,
    source_quality_status: ProbabilityEventSelectionComponentStatus,
    cost_gate_status: ProbabilityEventSelectionComponentStatus,
    operator_packet_status: ProbabilityEventSelectionComponentStatus,
    config: ProbabilityEventSelectionExplainabilityConfig,
    generated_at: datetime,
) -> ProbabilityEventSelectionExplainabilityReport:
    if type(config) is not ProbabilityEventSelectionExplainabilityConfig:
        raise ValueError("config must be a ProbabilityEventSelectionExplainabilityConfig")
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    _require_hard_flags("config", config)

    component_statuses = (
        screen_status,
        team_route_status,
        memory_policy,
        source_quality_status,
        cost_gate_status,
        operator_packet_status,
    )
    _validate_builder_component_statuses(component_statuses)
    selection_status = _selection_status(component_statuses)

    return ProbabilityEventSelectionExplainabilityReport(
        generated_at=generated_at,
        config_version=config.config_version,
        selection_status=selection_status,
        selection_explanation=_selection_explanation(component_statuses, selection_status),
        component_count=len(component_statuses),
        pass_count=_status_count(component_statuses, "pass"),
        watch_count=_status_count(component_statuses, "watch"),
        blocked_count=_status_count(component_statuses, "blocked"),
        component_statuses=component_statuses,
        blocked_reason_codes=_reason_codes_for_status(component_statuses, "blocked"),
        watch_reason_codes=_reason_codes_for_status(component_statuses, "watch"),
        reason_codes=_report_reason_codes(component_statuses),
    )


def _selection_status(
    component_statuses: tuple[ProbabilityEventSelectionComponentStatus, ...],
) -> str:
    if any(row.status == "blocked" for row in component_statuses):
        return "blocked"
    if any(row.status == "watch" for row in component_statuses):
        return "watch"
    return "ready"


def _selection_explanation(
    component_statuses: tuple[ProbabilityEventSelectionComponentStatus, ...],
    selection_status: str,
) -> str:
    blocked_summaries = _summaries_for_status(component_statuses, "blocked")
    watch_summaries = _summaries_for_status(component_statuses, "watch")
    if selection_status == "blocked":
        explanation = (
            "Selection blocked for paper review: "
            f"{_join_summaries(blocked_summaries)}."
        )
        if watch_summaries:
            explanation = (
                f"{explanation} Watch items: {_join_summaries(watch_summaries)}."
            )
        return explanation
    if selection_status == "watch":
        return (
            "Selection needs watch review: "
            f"{_join_summaries(watch_summaries)}."
        )
    return (
        "Selection ready for paper review: "
        f"{_join_summaries(tuple(row.summary for row in component_statuses))}."
    )


def _summaries_for_status(
    component_statuses: tuple[ProbabilityEventSelectionComponentStatus, ...],
    status: str,
) -> tuple[str, ...]:
    return tuple(row.summary for row in component_statuses if row.status == status)


def _join_summaries(summaries: tuple[str, ...]) -> str:
    return "; ".join(summaries)


def _reason_codes_for_status(
    component_statuses: tuple[ProbabilityEventSelectionComponentStatus, ...],
    status: str,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    for component_status in component_statuses:
        if component_status.status != status:
            continue
        for reason_code in component_status.reason_codes:
            if reason_code not in reason_codes:
                reason_codes.append(reason_code)
    return tuple(reason_codes)


def _report_reason_codes(
    component_statuses: tuple[ProbabilityEventSelectionComponentStatus, ...],
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if any(row.status == "blocked" for row in component_statuses):
        reason_codes.append("blocked_selection_components_present")
    if any(row.status == "watch" for row in component_statuses):
        reason_codes.append("watch_selection_components_present")
    if not reason_codes:
        reason_codes.append("selection_ready")
    return tuple(reason_codes)


def _status_count(
    component_statuses: tuple[ProbabilityEventSelectionComponentStatus, ...],
    status: str,
) -> int:
    return sum(1 for row in component_statuses if row.status == status)


def _normalize_component_statuses(
    value: object,
) -> tuple[ProbabilityEventSelectionComponentStatus, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("component_statuses must be an iterable")
    try:
        component_statuses = tuple(value)
    except TypeError as exc:
        raise ValueError("component_statuses must be an iterable") from exc
    _validate_builder_component_statuses(component_statuses)
    return component_statuses


def _validate_builder_component_statuses(
    component_statuses: tuple[object, ...],
) -> None:
    if len(component_statuses) != len(COMPONENT_NAMES):
        raise ValueError("component_statuses must contain all selection components")
    for index, component_status in enumerate(component_statuses):
        if type(component_status) is not ProbabilityEventSelectionComponentStatus:
            raise ValueError("component_statuses must contain component status values")
        _require_hard_flags("component_status", component_status)
        expected_name = COMPONENT_NAMES[index]
        if component_status.component_name != expected_name:
            raise ValueError("component_statuses must match the required component order")


def _validate_report_consistency(
    report: ProbabilityEventSelectionExplainabilityReport,
) -> None:
    if report.component_count != len(report.component_statuses):
        raise ValueError("component_count must match component_statuses")
    if report.pass_count != _status_count(report.component_statuses, "pass"):
        raise ValueError("pass_count must match component_statuses")
    if report.watch_count != _status_count(report.component_statuses, "watch"):
        raise ValueError("watch_count must match component_statuses")
    if report.blocked_count != _status_count(report.component_statuses, "blocked"):
        raise ValueError("blocked_count must match component_statuses")
    if report.selection_status != _selection_status(report.component_statuses):
        raise ValueError("selection_status must match component_statuses")
    if report.blocked_reason_codes != _reason_codes_for_status(
        report.component_statuses,
        "blocked",
    ):
        raise ValueError("blocked_reason_codes must match component_statuses")
    if report.watch_reason_codes != _reason_codes_for_status(
        report.component_statuses,
        "watch",
    ):
        raise ValueError("watch_reason_codes must match component_statuses")
    if report.reason_codes != _report_reason_codes(report.component_statuses):
        raise ValueError("reason_codes must match component_statuses")
    if report.selection_explanation != _selection_explanation(
        report.component_statuses,
        report.selection_status,
    ):
        raise ValueError("selection_explanation must match component_statuses")


def _validate_component_reason_codes(
    component_status: ProbabilityEventSelectionComponentStatus,
) -> None:
    if component_status.status in ("watch", "blocked") and not component_status.reason_codes:
        raise ValueError("reason_codes are required for watch and blocked statuses")


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_canonical_string(field_name, reason_code)
        _reject_forbidden_terms(field_name, reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(normalized)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_component_name(field_name: str, value: object) -> None:
    if type(value) is not str or value not in COMPONENT_NAMES:
        raise ValueError(f"{field_name} must be a known selection component")
    _reject_forbidden_terms(field_name, value)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_selection_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SELECTION_STATUSES:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")


def _require_public_summary(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    _reject_forbidden_terms(field_name, value)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_hard_flags(field_name: str, value: Any) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")


def _reject_forbidden_terms(field_name: str, value: str) -> None:
    value_lower = value.lower()
    if any(term in value_lower for term in FORBIDDEN_PUBLIC_TERMS):
        raise ValueError(f"{field_name} contains unsafe public surface terms")


__all__ = (
    "FORBIDDEN_PUBLIC_TERMS",
    "ProbabilityEventSelectionComponentStatus",
    "ProbabilityEventSelectionExplainabilityConfig",
    "ProbabilityEventSelectionExplainabilityReport",
    "build_probability_event_selection_explainability_report",
)
