"""Read-only specialist team learning dashboard readiness report."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_SPECIALIST_TEAM_LEARNING_DASHBOARD_CONFIG_VERSION = (
    "specialist-team-learning-dashboard-report-v0"
)
SPECIALIST_TEAM_LEARNING_DASHBOARD_BANDS = ("ready", "attention", "blocked")

READY_BAND = "ready"
ATTENTION_BAND = "attention"
BLOCKED_BAND = "blocked"

NO_SIGNALS_REASON = "learning_dashboard_no_signals"
TEAM_SCORECARD_REASON = "team_scorecard_not_ready"
POSTMORTEM_REASON = "postmortem_not_ready"
MEMORY_UPDATE_QUEUE_REASON = "memory_update_queue_not_ready"
LEARNING_FEEDBACK_REASON = "learning_feedback_not_ready"
OPERATING_CYCLE_REASON = "operating_cycle_not_ready"
DOMAIN_RISK_REGISTER_REASON = "domain_risk_register_not_ready"
RESEARCH_QUEUE_REASON = "research_queue_not_ready"
SUPABASE_MEMORY_REASON = "supabase_memory_not_ready"

ATTENTION_REASON_CODES = (
    TEAM_SCORECARD_REASON,
    POSTMORTEM_REASON,
    MEMORY_UPDATE_QUEUE_REASON,
    LEARNING_FEEDBACK_REASON,
)
BLOCKED_REASON_CODES = (
    OPERATING_CYCLE_REASON,
    DOMAIN_RISK_REGISTER_REASON,
    RESEARCH_QUEUE_REASON,
    SUPABASE_MEMORY_REASON,
)
REPORT_BLOCKED_REASON_CODES = (NO_SIGNALS_REASON, *BLOCKED_REASON_CODES)

SIGNAL_FIELDS = (
    "team_scorecard_ready",
    "postmortem_ready",
    "memory_update_queue_ready",
    "learning_feedback_ready",
    "operating_cycle_ready",
    "domain_risk_register_ready",
    "research_queue_ready",
    "supabase_memory_ready",
)
REQUIRED_SIGNAL_COUNT = Decimal("8.000000")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

__all__ = (
    "DEFAULT_SPECIALIST_TEAM_LEARNING_DASHBOARD_CONFIG_VERSION",
    "SPECIALIST_TEAM_LEARNING_DASHBOARD_BANDS",
    "SpecialistTeamLearningDashboardSignal",
    "SpecialistTeamLearningDashboardRow",
    "SpecialistTeamLearningDashboardReport",
    "build_specialist_team_learning_dashboard_report",
    "specialist_team_learning_dashboard_report_payload",
    "specialist_team_learning_dashboard_report_digest",
)


@dataclass(frozen=True)
class SpecialistTeamLearningDashboardSignal:
    team_scorecard_ready: bool
    postmortem_ready: bool
    memory_update_queue_ready: bool
    learning_feedback_ready: bool
    operating_cycle_ready: bool
    domain_risk_register_ready: bool
    research_queue_ready: bool
    supabase_memory_ready: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not SpecialistTeamLearningDashboardSignal:
            raise ValueError("signal must be exactly SpecialistTeamLearningDashboardSignal")
        for field_name in SIGNAL_FIELDS:
            _require_bool(field_name, getattr(self, field_name))
        _require_hard_flags("signal", self)


@dataclass(frozen=True)
class SpecialistTeamLearningDashboardRow:
    team_scorecard_ready: bool
    postmortem_ready: bool
    memory_update_queue_ready: bool
    learning_feedback_ready: bool
    operating_cycle_ready: bool
    domain_risk_register_ready: bool
    research_queue_ready: bool
    supabase_memory_ready: bool
    ready_signal_count: Decimal
    required_signal_count: Decimal
    ready_ratio: Decimal
    learning_dashboard_ready: bool
    dashboard_band: str
    blocked_reason_codes: tuple[str, ...]
    attention_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not SpecialistTeamLearningDashboardRow:
            raise ValueError("row must be exactly SpecialistTeamLearningDashboardRow")
        for field_name in SIGNAL_FIELDS:
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "ready_signal_count",
            _require_count_decimal("ready_signal_count", self.ready_signal_count),
        )
        object.__setattr__(
            self,
            "required_signal_count",
            _require_count_decimal("required_signal_count", self.required_signal_count),
        )
        object.__setattr__(
            self,
            "ready_ratio",
            _require_ratio_decimal("ready_ratio", self.ready_ratio),
        )
        _require_bool("learning_dashboard_ready", self.learning_dashboard_ready)
        _require_band("dashboard_band", self.dashboard_band)
        object.__setattr__(
            self,
            "blocked_reason_codes",
            _require_reason_codes(
                "blocked_reason_codes",
                self.blocked_reason_codes,
                BLOCKED_REASON_CODES,
            ),
        )
        object.__setattr__(
            self,
            "attention_reason_codes",
            _require_reason_codes(
                "attention_reason_codes",
                self.attention_reason_codes,
                ATTENTION_REASON_CODES,
            ),
        )
        _require_hard_flags("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class SpecialistTeamLearningDashboardReport:
    config_version: str
    signal_count: Decimal
    ready_signal_count: Decimal
    required_signal_count: Decimal
    ready_ratio: Decimal
    learning_dashboard_ready: bool
    dashboard_band: str
    blocked_reason_codes: tuple[str, ...]
    attention_reason_codes: tuple[str, ...]
    rows: tuple[SpecialistTeamLearningDashboardRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not SpecialistTeamLearningDashboardReport:
            raise ValueError("report must be exactly SpecialistTeamLearningDashboardReport")
        if self.config_version != DEFAULT_SPECIALIST_TEAM_LEARNING_DASHBOARD_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in ("signal_count", "ready_signal_count", "required_signal_count"):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "ready_ratio",
            _require_ratio_decimal("ready_ratio", self.ready_ratio),
        )
        _require_bool("learning_dashboard_ready", self.learning_dashboard_ready)
        _require_band("dashboard_band", self.dashboard_band)
        object.__setattr__(
            self,
            "blocked_reason_codes",
            _require_reason_codes(
                "blocked_reason_codes",
                self.blocked_reason_codes,
                REPORT_BLOCKED_REASON_CODES,
            ),
        )
        object.__setattr__(
            self,
            "attention_reason_codes",
            _require_reason_codes(
                "attention_reason_codes",
                self.attention_reason_codes,
                ATTENTION_REASON_CODES,
            ),
        )
        object.__setattr__(self, "rows", _require_rows(self.rows))
        _require_hard_flags("report", self)
        _validate_report(self)

    @property
    def public_payload(self) -> dict[str, Any]:
        return specialist_team_learning_dashboard_report_payload(self)

    @property
    def digest(self) -> str:
        return specialist_team_learning_dashboard_report_digest(self)


def build_specialist_team_learning_dashboard_report(
    signals: Iterable[SpecialistTeamLearningDashboardSignal],
) -> SpecialistTeamLearningDashboardReport:
    normalized_signals = _normalize_signals(signals)
    rows = tuple(_row_from_signal(signal) for signal in normalized_signals)
    signal_count = _count(len(rows))
    ready_signal_count = _sum_decimal(row.ready_signal_count for row in rows)
    required_signal_count = _sum_decimal(row.required_signal_count for row in rows)

    return SpecialistTeamLearningDashboardReport(
        config_version=DEFAULT_SPECIALIST_TEAM_LEARNING_DASHBOARD_CONFIG_VERSION,
        signal_count=signal_count,
        ready_signal_count=ready_signal_count,
        required_signal_count=required_signal_count,
        ready_ratio=_ratio(ready_signal_count, required_signal_count),
        learning_dashboard_ready=_report_ready(rows),
        dashboard_band=_report_band(rows),
        blocked_reason_codes=_report_blocked_reason_codes(rows),
        attention_reason_codes=_report_attention_reason_codes(rows),
        rows=rows,
    )


def specialist_team_learning_dashboard_report_payload(
    report: SpecialistTeamLearningDashboardReport,
) -> dict[str, Any]:
    if type(report) is not SpecialistTeamLearningDashboardReport:
        raise ValueError("report must be a SpecialistTeamLearningDashboardReport")
    _require_hard_flags("report", report)
    payload_source = asdict(report)
    payload = json_ready_no_floats(payload_source)
    if type(payload) is not dict:
        raise ValueError("public_payload must be a JSON object")
    payload["digest"] = _digest_for_payload(payload)
    return payload


def specialist_team_learning_dashboard_report_digest(
    report: SpecialistTeamLearningDashboardReport,
) -> str:
    if type(report) is not SpecialistTeamLearningDashboardReport:
        raise ValueError("report must be a SpecialistTeamLearningDashboardReport")
    _require_hard_flags("report", report)
    payload = json_ready_no_floats(asdict(report))
    if type(payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    return _digest_for_payload(payload)


def _row_from_signal(
    signal: SpecialistTeamLearningDashboardSignal,
) -> SpecialistTeamLearningDashboardRow:
    ready_signal_count = _ready_signal_count(signal)
    blocked_reason_codes = _blocked_reason_codes(signal)
    attention_reason_codes = _attention_reason_codes(signal)
    dashboard_band = _band(blocked_reason_codes, attention_reason_codes)

    return SpecialistTeamLearningDashboardRow(
        team_scorecard_ready=signal.team_scorecard_ready,
        postmortem_ready=signal.postmortem_ready,
        memory_update_queue_ready=signal.memory_update_queue_ready,
        learning_feedback_ready=signal.learning_feedback_ready,
        operating_cycle_ready=signal.operating_cycle_ready,
        domain_risk_register_ready=signal.domain_risk_register_ready,
        research_queue_ready=signal.research_queue_ready,
        supabase_memory_ready=signal.supabase_memory_ready,
        ready_signal_count=ready_signal_count,
        required_signal_count=REQUIRED_SIGNAL_COUNT,
        ready_ratio=_ratio(ready_signal_count, REQUIRED_SIGNAL_COUNT),
        learning_dashboard_ready=dashboard_band == READY_BAND,
        dashboard_band=dashboard_band,
        blocked_reason_codes=blocked_reason_codes,
        attention_reason_codes=attention_reason_codes,
    )


def _ready_signal_count(
    value: SpecialistTeamLearningDashboardSignal | SpecialistTeamLearningDashboardRow,
) -> Decimal:
    return _count(sum(1 for field_name in SIGNAL_FIELDS if getattr(value, field_name)))


def _blocked_reason_codes(
    value: SpecialistTeamLearningDashboardSignal | SpecialistTeamLearningDashboardRow,
) -> tuple[str, ...]:
    requested: list[str] = []
    if not value.operating_cycle_ready:
        requested.append(OPERATING_CYCLE_REASON)
    if not value.domain_risk_register_ready:
        requested.append(DOMAIN_RISK_REGISTER_REASON)
    if not value.research_queue_ready:
        requested.append(RESEARCH_QUEUE_REASON)
    if not value.supabase_memory_ready:
        requested.append(SUPABASE_MEMORY_REASON)
    return tuple(requested)


def _attention_reason_codes(
    value: SpecialistTeamLearningDashboardSignal | SpecialistTeamLearningDashboardRow,
) -> tuple[str, ...]:
    requested: list[str] = []
    if not value.team_scorecard_ready:
        requested.append(TEAM_SCORECARD_REASON)
    if not value.postmortem_ready:
        requested.append(POSTMORTEM_REASON)
    if not value.memory_update_queue_ready:
        requested.append(MEMORY_UPDATE_QUEUE_REASON)
    if not value.learning_feedback_ready:
        requested.append(LEARNING_FEEDBACK_REASON)
    return tuple(requested)


def _band(blocked: tuple[str, ...], attention: tuple[str, ...]) -> str:
    if blocked:
        return BLOCKED_BAND
    if attention:
        return ATTENTION_BAND
    return READY_BAND


def _report_ready(rows: tuple[SpecialistTeamLearningDashboardRow, ...]) -> bool:
    return bool(rows) and all(row.learning_dashboard_ready for row in rows)


def _report_band(rows: tuple[SpecialistTeamLearningDashboardRow, ...]) -> str:
    if not rows:
        return BLOCKED_BAND
    if any(row.dashboard_band == BLOCKED_BAND for row in rows):
        return BLOCKED_BAND
    if any(row.dashboard_band == ATTENTION_BAND for row in rows):
        return ATTENTION_BAND
    return READY_BAND


def _report_blocked_reason_codes(
    rows: tuple[SpecialistTeamLearningDashboardRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_SIGNALS_REASON,)
    requested = {reason for row in rows for reason in row.blocked_reason_codes}
    return tuple(reason for reason in BLOCKED_REASON_CODES if reason in requested)


def _report_attention_reason_codes(
    rows: tuple[SpecialistTeamLearningDashboardRow, ...],
) -> tuple[str, ...]:
    requested = {reason for row in rows for reason in row.attention_reason_codes}
    return tuple(reason for reason in ATTENTION_REASON_CODES if reason in requested)


def _normalize_signals(
    signals: Iterable[SpecialistTeamLearningDashboardSignal],
) -> tuple[SpecialistTeamLearningDashboardSignal, ...]:
    if isinstance(signals, (str, bytes)):
        raise ValueError("signals must be an iterable")
    try:
        rows = tuple(signals)
    except TypeError as exc:
        raise ValueError("signals must be an iterable") from exc
    for row in rows:
        if type(row) is not SpecialistTeamLearningDashboardSignal:
            raise ValueError(
                "signals must contain SpecialistTeamLearningDashboardSignal values",
            )
        _require_hard_flags("signal", row)
    return rows


def _require_rows(
    rows: Iterable[SpecialistTeamLearningDashboardRow],
) -> tuple[SpecialistTeamLearningDashboardRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not SpecialistTeamLearningDashboardRow:
            raise ValueError("rows must contain SpecialistTeamLearningDashboardRow values")
        _require_hard_flags("row", row)
    return normalized


def _validate_row(row: SpecialistTeamLearningDashboardRow) -> None:
    blocked_reason_codes = _blocked_reason_codes(row)
    attention_reason_codes = _attention_reason_codes(row)
    dashboard_band = _band(blocked_reason_codes, attention_reason_codes)
    expected_ready_signal_count = _ready_signal_count(row)
    expected_ready_ratio = _ratio(expected_ready_signal_count, row.required_signal_count)

    if row.required_signal_count != REQUIRED_SIGNAL_COUNT:
        raise ValueError("required_signal_count must match readiness signals")
    if row.ready_signal_count != expected_ready_signal_count:
        raise ValueError("ready_signal_count must match readiness signals")
    if row.ready_ratio != expected_ready_ratio:
        raise ValueError("ready_ratio must match readiness signals")
    if row.blocked_reason_codes != blocked_reason_codes:
        raise ValueError("blocked_reason_codes must match readiness signals")
    if row.attention_reason_codes != attention_reason_codes:
        raise ValueError("attention_reason_codes must match readiness signals")
    if row.dashboard_band != dashboard_band:
        raise ValueError("dashboard_band must match readiness signals")
    if row.learning_dashboard_ready != (dashboard_band == READY_BAND):
        raise ValueError("learning_dashboard_ready must match readiness signals")


def _validate_report(report: SpecialistTeamLearningDashboardReport) -> None:
    rows = report.rows
    expected_signal_count = _count(len(rows))
    expected_ready_signal_count = _sum_decimal(row.ready_signal_count for row in rows)
    expected_required_signal_count = _sum_decimal(row.required_signal_count for row in rows)

    if report.signal_count != expected_signal_count:
        raise ValueError("signal_count must match rows")
    if report.ready_signal_count != expected_ready_signal_count:
        raise ValueError("ready_signal_count must match rows")
    if report.required_signal_count != expected_required_signal_count:
        raise ValueError("required_signal_count must match rows")
    if report.ready_ratio != _ratio(
        expected_ready_signal_count,
        expected_required_signal_count,
    ):
        raise ValueError("ready_ratio must match rows")
    if report.learning_dashboard_ready != _report_ready(rows):
        raise ValueError("learning_dashboard_ready must match rows")
    if report.dashboard_band != _report_band(rows):
        raise ValueError("dashboard_band must match rows")
    if report.blocked_reason_codes != _report_blocked_reason_codes(rows):
        raise ValueError("blocked_reason_codes must match rows")
    if report.attention_reason_codes != _report_attention_reason_codes(rows):
        raise ValueError("attention_reason_codes must match rows")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_band(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SPECIALIST_TEAM_LEARNING_DASHBOARD_BANDS:
        raise ValueError(f"{field_name} must be ready, attention, or blocked")


def _require_reason_codes(
    field_name: str,
    value: Iterable[str],
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    allowed_ranks = {reason: index for index, reason in enumerate(allowed_values)}
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in allowed_ranks:
            raise ValueError(f"{field_name} must contain known values")
    expected = tuple(reason for reason in allowed_values if reason in reason_codes)
    if reason_codes != expected:
        raise ValueError(f"{field_name} must be deterministic")
    return reason_codes


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = _quantize(value)
    if quantized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = _quantize(value)
    if quantized < ZERO or quantized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return quantized


def _require_hard_flags(label: str, value: object) -> None:
    require_paper_only_flags(f"specialist team learning dashboard {label}", value)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    with localcontext(DECIMAL_CONTEXT):
        for value in values:
            total += value
    return _quantize(total)


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _digest_for_payload(payload: dict[str, Any]) -> str:
    payload_without_digest = dict(payload)
    payload_without_digest.pop("digest", None)
    encoded = json.dumps(
        payload_without_digest,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
