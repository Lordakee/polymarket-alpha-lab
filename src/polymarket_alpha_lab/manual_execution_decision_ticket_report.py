from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from typing import Any


DEFAULT_MANUAL_EXECUTION_DECISION_TICKET_REPORT_CONFIG_VERSION = (
    "manual-execution-decision-ticket-report-v0"
)
RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64)
SETTLEMENT_RISK_STATUSES = ("clear", "watch", "block")
SOURCE_QUORUM_STATUSES = ("met", "missing")
DECISION_STATUSES = ("ready_for_manual_review", "manual_review_watch", "blocked")


@dataclass(frozen=True)
class ManualExecutionDecisionTicketInput:
    ticket_id: str
    market_slug: str
    p_yes_forecast: Decimal
    market_probability: Decimal
    cost_adjusted_threshold: Decimal
    source_count: Decimal
    required_source_count: Decimal
    specialist_team: tuple[str, ...]
    proposed_position_share: Decimal
    max_position_share: Decimal
    settlement_risk_status: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "ticket input",
            self,
            ManualExecutionDecisionTicketInput,
        )
        _require_canonical_string("ticket_id", self.ticket_id)
        _require_canonical_string("market_slug", self.market_slug)
        for field_name in (
            "p_yes_forecast",
            "market_probability",
            "cost_adjusted_threshold",
            "proposed_position_share",
            "max_position_share",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("source_count", "required_source_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.required_source_count <= ZERO:
            raise ValueError("required_source_count must be positive")
        if self.max_position_share <= ZERO:
            raise ValueError("max_position_share must be positive")
        object.__setattr__(
            self,
            "specialist_team",
            _normalize_text_tuple("specialist_team", self.specialist_team),
        )
        if self.settlement_risk_status not in SETTLEMENT_RISK_STATUSES:
            raise ValueError("settlement_risk_status must be clear, watch, or block")
        _require_safety_flags(self)


@dataclass(frozen=True)
class ManualExecutionDecisionTicketReport:
    generated_at: datetime
    config_version: str
    ticket_id: str
    market_slug: str
    p_yes_forecast: Decimal
    market_probability: Decimal
    cost_adjusted_threshold: Decimal
    edge_to_market_probability: Decimal
    edge_to_threshold: Decimal
    source_count: Decimal
    required_source_count: Decimal
    source_quorum_status: str
    specialist_team: tuple[str, ...]
    proposed_position_share: Decimal
    max_position_share: Decimal
    max_position_blocker: str | None
    settlement_risk_status: str
    settlement_risk_blocker: str | None
    decision_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "ticket report",
            self,
            ManualExecutionDecisionTicketReport,
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MANUAL_EXECUTION_DECISION_TICKET_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the known config version")
        _require_canonical_string("ticket_id", self.ticket_id)
        _require_canonical_string("market_slug", self.market_slug)
        for field_name in (
            "p_yes_forecast",
            "market_probability",
            "cost_adjusted_threshold",
            "proposed_position_share",
            "max_position_share",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("edge_to_market_probability", "edge_to_threshold"):
            object.__setattr__(
                self,
                field_name,
                _require_quantized_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("source_count", "required_source_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.required_source_count <= ZERO:
            raise ValueError("required_source_count must be positive")
        if self.max_position_share <= ZERO:
            raise ValueError("max_position_share must be positive")
        if self.source_quorum_status not in SOURCE_QUORUM_STATUSES:
            raise ValueError("source_quorum_status must be met or missing")
        object.__setattr__(
            self,
            "specialist_team",
            _normalize_text_tuple("specialist_team", self.specialist_team),
        )
        _require_optional_canonical_string(
            "max_position_blocker",
            self.max_position_blocker,
        )
        if self.settlement_risk_status not in SETTLEMENT_RISK_STATUSES:
            raise ValueError("settlement_risk_status must be clear, watch, or block")
        _require_optional_canonical_string(
            "settlement_risk_blocker",
            self.settlement_risk_blocker,
        )
        if self.decision_status not in DECISION_STATUSES:
            raise ValueError("decision_status must be a known status")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_text_tuple("reason_codes", self.reason_codes),
        )
        _require_safety_flags(self)
        _validate_report(self)

    @property
    def payload(self) -> "FrozenJsonObject":
        return manual_execution_decision_ticket_report_payload(self)


def build_manual_execution_decision_ticket_report(
    ticket_input: ManualExecutionDecisionTicketInput,
    *,
    generated_at: datetime,
) -> ManualExecutionDecisionTicketReport:
    if type(ticket_input) is not ManualExecutionDecisionTicketInput:
        raise ValueError("ticket_input must be a ManualExecutionDecisionTicketInput")
    _require_safety_flags(ticket_input)
    generated_at_utc = _as_utc("generated_at", generated_at)
    edge_to_market_probability = _decimal_difference(
        ticket_input.p_yes_forecast,
        ticket_input.market_probability,
    )
    edge_to_threshold = _decimal_difference(
        ticket_input.p_yes_forecast,
        ticket_input.cost_adjusted_threshold,
    )
    source_quorum_status = (
        "met"
        if ticket_input.source_count >= ticket_input.required_source_count
        else "missing"
    )
    max_position_blocker = (
        "proposed position share exceeds max position share"
        if ticket_input.proposed_position_share > ticket_input.max_position_share
        else None
    )
    settlement_risk_blocker = (
        "settlement risk status is block"
        if ticket_input.settlement_risk_status == "block"
        else None
    )
    reason_codes = _reason_codes(
        edge_to_threshold=edge_to_threshold,
        source_quorum_status=source_quorum_status,
        max_position_blocker=max_position_blocker,
        settlement_risk_status=ticket_input.settlement_risk_status,
    )
    decision_status = _decision_status(
        reason_codes=reason_codes,
        settlement_risk_status=ticket_input.settlement_risk_status,
    )
    return ManualExecutionDecisionTicketReport(
        generated_at=generated_at_utc,
        config_version=DEFAULT_MANUAL_EXECUTION_DECISION_TICKET_REPORT_CONFIG_VERSION,
        ticket_id=ticket_input.ticket_id,
        market_slug=ticket_input.market_slug,
        p_yes_forecast=ticket_input.p_yes_forecast,
        market_probability=ticket_input.market_probability,
        cost_adjusted_threshold=ticket_input.cost_adjusted_threshold,
        edge_to_market_probability=edge_to_market_probability,
        edge_to_threshold=edge_to_threshold,
        source_count=ticket_input.source_count,
        required_source_count=ticket_input.required_source_count,
        source_quorum_status=source_quorum_status,
        specialist_team=ticket_input.specialist_team,
        proposed_position_share=ticket_input.proposed_position_share,
        max_position_share=ticket_input.max_position_share,
        max_position_blocker=max_position_blocker,
        settlement_risk_status=ticket_input.settlement_risk_status,
        settlement_risk_blocker=settlement_risk_blocker,
        decision_status=decision_status,
        reason_codes=reason_codes,
    )


def manual_execution_decision_ticket_report_payload(
    report: ManualExecutionDecisionTicketReport,
) -> "FrozenJsonObject":
    if type(report) is not ManualExecutionDecisionTicketReport:
        raise ValueError("report must be a ManualExecutionDecisionTicketReport")
    _require_safety_flags(report)
    return _freeze_json_object(
        {
            "generated_at": report.generated_at.isoformat(),
            "config_version": report.config_version,
            "ticket_id": report.ticket_id,
            "market_slug": report.market_slug,
            "p_yes_forecast": _decimal_text(report.p_yes_forecast),
            "market_probability": _decimal_text(report.market_probability),
            "cost_adjusted_threshold": _decimal_text(report.cost_adjusted_threshold),
            "edge_to_market_probability": _decimal_text(
                report.edge_to_market_probability,
            ),
            "edge_to_threshold": _decimal_text(report.edge_to_threshold),
            "source_count": _decimal_text(report.source_count),
            "required_source_count": _decimal_text(report.required_source_count),
            "source_quorum_status": report.source_quorum_status,
            "specialist_team": report.specialist_team,
            "proposed_position_share": _decimal_text(report.proposed_position_share),
            "max_position_share": _decimal_text(report.max_position_share),
            "max_position_blocker": report.max_position_blocker,
            "settlement_risk_status": report.settlement_risk_status,
            "settlement_risk_blocker": report.settlement_risk_blocker,
            "decision_status": report.decision_status,
            "reason_codes": report.reason_codes,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )


class FrozenJsonObject(dict[str, Any]):
    def __init__(self, value: dict[str, Any]) -> None:
        super().__init__(value)

    def __setitem__(self, key: str, value: Any) -> None:
        raise TypeError("payload is immutable")

    def __delitem__(self, key: str) -> None:
        raise TypeError("payload is immutable")

    def clear(self) -> None:
        raise TypeError("payload is immutable")

    def pop(self, key: str, default: Any = None) -> Any:
        raise TypeError("payload is immutable")

    def popitem(self) -> tuple[str, Any]:
        raise TypeError("payload is immutable")

    def setdefault(self, key: str, default: Any = None) -> Any:
        raise TypeError("payload is immutable")

    def update(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError("payload is immutable")

    def __ior__(self, other: object) -> "FrozenJsonObject":
        raise TypeError("payload is immutable")


class FrozenJsonArray(tuple[Any, ...]):
    def __eq__(self, other: object) -> bool:
        if isinstance(other, (list, tuple)):
            return tuple(self) == tuple(other)
        return False

    def append(self, value: Any) -> None:
        raise TypeError("payload is immutable")

    def extend(self, values: Any) -> None:
        raise TypeError("payload is immutable")


def _reason_codes(
    *,
    edge_to_threshold: Decimal,
    source_quorum_status: str,
    max_position_blocker: str | None,
    settlement_risk_status: str,
) -> tuple[str, ...]:
    codes: list[str] = []
    if edge_to_threshold < ZERO:
        codes.append("edge_below_cost_adjusted_threshold")
    if max_position_blocker is not None:
        codes.append("position_exceeds_max")
    if settlement_risk_status == "block":
        codes.append("settlement_risk_blocker")
    elif settlement_risk_status == "watch":
        codes.append("settlement_risk_watch")
    if source_quorum_status == "missing":
        codes.append("source_quorum_missing")
    if not codes:
        codes.append("ready_readonly_manual_ticket")
    return tuple(codes)


def _decision_status(
    *,
    reason_codes: tuple[str, ...],
    settlement_risk_status: str,
) -> str:
    blocking_codes = {
        "edge_below_cost_adjusted_threshold",
        "position_exceeds_max",
        "settlement_risk_blocker",
        "source_quorum_missing",
    }
    if any(reason_code in blocking_codes for reason_code in reason_codes):
        return "blocked"
    if settlement_risk_status == "watch":
        return "manual_review_watch"
    return "ready_for_manual_review"


def _validate_report(report: ManualExecutionDecisionTicketReport) -> None:
    if report.edge_to_market_probability != _decimal_difference(
        report.p_yes_forecast,
        report.market_probability,
    ):
        raise ValueError("edge_to_market_probability must match p_yes_forecast")
    if report.edge_to_threshold != _decimal_difference(
        report.p_yes_forecast,
        report.cost_adjusted_threshold,
    ):
        raise ValueError("edge_to_threshold must match cost_adjusted_threshold")
    expected_source_status = (
        "met" if report.source_count >= report.required_source_count else "missing"
    )
    if report.source_quorum_status != expected_source_status:
        raise ValueError("source_quorum_status must match source counts")
    expected_position_blocker = (
        "proposed position share exceeds max position share"
        if report.proposed_position_share > report.max_position_share
        else None
    )
    if report.max_position_blocker != expected_position_blocker:
        raise ValueError("max_position_blocker must match position shares")
    expected_settlement_blocker = (
        "settlement risk status is block"
        if report.settlement_risk_status == "block"
        else None
    )
    if report.settlement_risk_blocker != expected_settlement_blocker:
        raise ValueError("settlement_risk_blocker must match settlement status")
    expected_reasons = _reason_codes(
        edge_to_threshold=report.edge_to_threshold,
        source_quorum_status=report.source_quorum_status,
        max_position_blocker=report.max_position_blocker,
        settlement_risk_status=report.settlement_risk_status,
    )
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match report state")
    expected_status = _decision_status(
        reason_codes=report.reason_codes,
        settlement_risk_status=report.settlement_risk_status,
    )
    if report.decision_status != expected_status:
        raise ValueError("decision_status must match report state")


def _decimal_difference(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (left - right).quantize(RATIO_QUANTUM)


def _decimal_text(value: Decimal) -> str:
    return format(value, "f")


def _normalize_text_tuple(field_name: str, values: object) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be a tuple of strings")
    try:
        items = tuple(values)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be a tuple of strings") from exc
    if not items:
        raise ValueError(f"{field_name} must not be empty")
    for item in items:
        _require_canonical_string(field_name, item)
    if len(set(items)) != len(items):
        raise ValueError(f"{field_name} must not contain duplicates")
    return items


def _require_optional_canonical_string(field_name: str, value: str | None) -> None:
    if value is not None:
        _require_canonical_string(field_name, value)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if any(ord(character) < 32 for character in value):
        raise ValueError(f"{field_name} must not contain control characters")


def _require_quantized_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value != value.quantize(RATIO_QUANTUM):
        raise ValueError(f"{field_name} must use ratio quantum")
    return value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_quantized_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return value


def _require_exact_type(
    field_name: str,
    value: object,
    expected_type: type[object],
) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_safety_flags(value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only") is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly") is not True:
        raise ValueError("readonly must be True")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _freeze_json_object(value: dict[str, Any]) -> FrozenJsonObject:
    return FrozenJsonObject(
        {key: _freeze_json_value(item) for key, item in value.items()},
    )


def _freeze_json_value(value: Any) -> Any:
    if type(value) is dict:
        return _freeze_json_object(value)
    if type(value) is tuple:
        return FrozenJsonArray(_freeze_json_value(item) for item in value)
    return value


__all__ = (
    "DECISION_STATUSES",
    "DEFAULT_MANUAL_EXECUTION_DECISION_TICKET_REPORT_CONFIG_VERSION",
    "SETTLEMENT_RISK_STATUSES",
    "SOURCE_QUORUM_STATUSES",
    "FrozenJsonArray",
    "FrozenJsonObject",
    "ManualExecutionDecisionTicketInput",
    "ManualExecutionDecisionTicketReport",
    "build_manual_execution_decision_ticket_report",
    "manual_execution_decision_ticket_report_payload",
)
