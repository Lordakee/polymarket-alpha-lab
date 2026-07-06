"""Paper report reducer for research queue SLA breach forecasts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

DEFAULT_RESEARCH_QUEUE_SLA_BREACH_FORECAST_V10_CONFIG_VERSION = (
    "strategy-research-queue-sla-breach-forecast-v10"
)

DECIMAL_PRECISION = 64
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
CAPACITY_HEALTHY_THRESHOLD = Decimal("0.750000")
CAPACITY_CONSTRAINED_THRESHOLD = Decimal("0.500000")
CAPACITY_STRAINED_THRESHOLD = Decimal("0.300000")
HIGH_TICKET_PRESSURE_THRESHOLD = Decimal("8.000000")
ELEVATED_TICKET_PRESSURE_THRESHOLD = Decimal("5.000000")
HUMAN_REVIEW_BUFFER_MINUTES = Decimal("25.000000")
RESOLUTION_WINDOW_MULTIPLE = Decimal("2.000000")

ASSIGNED_PRIORITIES = ("low", "medium", "high", "urgent")
BREACH_RISK_STATUSES = ("on_track", "watch", "breach_likely")
ESCALATION_ACTIONS = ("monitor", "queue_owner_review", "page_research_lead")
PAYLOAD_FIELDS = (
    "config_version",
    "queue_lane",
    "assigned_priority",
    "team_capacity_score",
    "open_ticket_count",
    "average_resolution_minutes",
    "time_to_market_resolution_minutes",
    "human_review_required",
    "breach_risk_status",
    "expected_delay_minutes",
    "escalation_action",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class ResearchQueueSlaBreachForecastV10Input:
    queue_lane: str
    assigned_priority: str
    team_capacity_score: Decimal
    open_ticket_count: Decimal
    average_resolution_minutes: Decimal
    time_to_market_resolution_minutes: Decimal
    human_review_required: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "queue_lane", _require_token("queue_lane", self.queue_lane))
        object.__setattr__(
            self,
            "assigned_priority",
            _require_member("assigned_priority", self.assigned_priority, ASSIGNED_PRIORITIES),
        )
        object.__setattr__(
            self,
            "team_capacity_score",
            _normalize_unit_decimal("team_capacity_score", self.team_capacity_score),
        )
        object.__setattr__(
            self,
            "open_ticket_count",
            _normalize_whole_decimal("open_ticket_count", self.open_ticket_count),
        )
        object.__setattr__(
            self,
            "average_resolution_minutes",
            _normalize_positive_decimal(
                "average_resolution_minutes",
                self.average_resolution_minutes,
            ),
        )
        object.__setattr__(
            self,
            "time_to_market_resolution_minutes",
            _normalize_nonnegative_decimal(
                "time_to_market_resolution_minutes",
                self.time_to_market_resolution_minutes,
            ),
        )
        _require_bool("human_review_required", self.human_review_required)
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchQueueSlaBreachForecastV10Result:
    queue_lane: str
    assigned_priority: str
    team_capacity_score: Decimal
    open_ticket_count: Decimal
    average_resolution_minutes: Decimal
    time_to_market_resolution_minutes: Decimal
    human_review_required: bool
    breach_risk_status: str
    expected_delay_minutes: Decimal
    escalation_action: str
    reason_codes: tuple[str, ...]
    config_version: str = DEFAULT_RESEARCH_QUEUE_SLA_BREACH_FORECAST_V10_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_config_version(self.config_version)
        object.__setattr__(self, "queue_lane", _require_token("queue_lane", self.queue_lane))
        object.__setattr__(
            self,
            "assigned_priority",
            _require_member("assigned_priority", self.assigned_priority, ASSIGNED_PRIORITIES),
        )
        object.__setattr__(
            self,
            "team_capacity_score",
            _normalize_unit_decimal("team_capacity_score", self.team_capacity_score),
        )
        object.__setattr__(
            self,
            "open_ticket_count",
            _normalize_whole_decimal("open_ticket_count", self.open_ticket_count),
        )
        object.__setattr__(
            self,
            "average_resolution_minutes",
            _normalize_positive_decimal(
                "average_resolution_minutes",
                self.average_resolution_minutes,
            ),
        )
        object.__setattr__(
            self,
            "time_to_market_resolution_minutes",
            _normalize_nonnegative_decimal(
                "time_to_market_resolution_minutes",
                self.time_to_market_resolution_minutes,
            ),
        )
        _require_bool("human_review_required", self.human_review_required)
        object.__setattr__(
            self,
            "breach_risk_status",
            _require_member(
                "breach_risk_status",
                self.breach_risk_status,
                BREACH_RISK_STATUSES,
            ),
        )
        object.__setattr__(
            self,
            "expected_delay_minutes",
            _normalize_nonnegative_decimal(
                "expected_delay_minutes",
                self.expected_delay_minutes,
            ),
        )
        object.__setattr__(
            self,
            "escalation_action",
            _require_member("escalation_action", self.escalation_action, ESCALATION_ACTIONS),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("result", self)
        _validate_result(self)

    @property
    def payload(self) -> dict[str, Any]:
        return strategy_research_queue_sla_breach_forecast_v10_payload(self)


def strategy_research_queue_sla_breach_forecast_v10(
    queue: ResearchQueueSlaBreachForecastV10Input,
) -> ResearchQueueSlaBreachForecastV10Result:
    if type(queue) is not ResearchQueueSlaBreachForecastV10Input:
        raise ValueError("queue must be a ResearchQueueSlaBreachForecastV10Input")
    _require_hard_flags("input", queue)

    expected_delay_minutes = _expected_delay_minutes(queue)
    breach_risk_status = _breach_risk_status(queue, expected_delay_minutes)
    escalation_action = _escalation_action(queue, breach_risk_status)

    return ResearchQueueSlaBreachForecastV10Result(
        queue_lane=queue.queue_lane,
        assigned_priority=queue.assigned_priority,
        team_capacity_score=queue.team_capacity_score,
        open_ticket_count=queue.open_ticket_count,
        average_resolution_minutes=queue.average_resolution_minutes,
        time_to_market_resolution_minutes=queue.time_to_market_resolution_minutes,
        human_review_required=queue.human_review_required,
        breach_risk_status=breach_risk_status,
        expected_delay_minutes=expected_delay_minutes,
        escalation_action=escalation_action,
        reason_codes=_reason_codes(queue, expected_delay_minutes, breach_risk_status, escalation_action),
    )


def strategy_research_queue_sla_breach_forecast_v10_payload(
    report: ResearchQueueSlaBreachForecastV10Result | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchQueueSlaBreachForecastV10Result:
        _require_hard_flags("result", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _require_hard_flags("payload", _DictFlags(report))
        _reject_unsupported_payload_fields(report)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchQueueSlaBreachForecastV10Result")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsupported_payload_fields(payload)
    _require_hard_flags("payload", _DictFlags(payload))
    return payload


def _expected_delay_minutes(queue: ResearchQueueSlaBreachForecastV10Input) -> Decimal:
    queued_work_minutes = _normalize_nonnegative_decimal(
        "queued_work_minutes",
        queue.open_ticket_count * queue.average_resolution_minutes,
    )
    if queue.human_review_required:
        queued_work_minutes = _normalize_nonnegative_decimal(
            "queued_work_minutes",
            queued_work_minutes + HUMAN_REVIEW_BUFFER_MINUTES,
        )
    delay = queued_work_minutes - queue.time_to_market_resolution_minutes
    if delay <= ZERO:
        return ZERO
    return _normalize_nonnegative_decimal("expected_delay_minutes", delay)


def _breach_risk_status(
    queue: ResearchQueueSlaBreachForecastV10Input,
    expected_delay_minutes: Decimal,
) -> str:
    if expected_delay_minutes > ZERO:
        return "breach_likely"
    if queue.assigned_priority in {"high", "urgent"} and queue.human_review_required:
        return "watch"
    if queue.team_capacity_score < CAPACITY_CONSTRAINED_THRESHOLD:
        return "watch"
    if queue.open_ticket_count >= ELEVATED_TICKET_PRESSURE_THRESHOLD:
        return "watch"
    return "on_track"


def _escalation_action(
    queue: ResearchQueueSlaBreachForecastV10Input,
    breach_risk_status: str,
) -> str:
    if breach_risk_status == "breach_likely" and (
        queue.assigned_priority == "urgent"
        or queue.team_capacity_score < CAPACITY_STRAINED_THRESHOLD
    ):
        return "page_research_lead"
    if breach_risk_status in {"watch", "breach_likely"}:
        return "queue_owner_review"
    return "monitor"


def _reason_codes(
    queue: ResearchQueueSlaBreachForecastV10Input | ResearchQueueSlaBreachForecastV10Result,
    expected_delay_minutes: Decimal,
    breach_risk_status: str,
    escalation_action: str,
) -> tuple[str, ...]:
    codes = [
        f"priority_{queue.assigned_priority}",
        _capacity_reason_code(queue.team_capacity_score),
        _ticket_pressure_reason_code(queue.open_ticket_count),
        _resolution_window_reason_code(queue),
        "human_review_required" if queue.human_review_required else "human_review_not_required",
    ]
    if expected_delay_minutes > ZERO:
        codes.append("expected_delay_positive")
    if breach_risk_status == "breach_likely":
        codes.append("breach_risk_likely")
    else:
        codes.append(f"breach_risk_{breach_risk_status}")
    codes.append(f"escalation_{escalation_action}")
    return tuple(codes)


def _capacity_reason_code(team_capacity_score: Decimal) -> str:
    if team_capacity_score >= CAPACITY_HEALTHY_THRESHOLD:
        return "capacity_healthy"
    if team_capacity_score >= CAPACITY_CONSTRAINED_THRESHOLD:
        return "capacity_constrained"
    if team_capacity_score >= CAPACITY_STRAINED_THRESHOLD:
        return "capacity_strained"
    return "capacity_critical"


def _ticket_pressure_reason_code(open_ticket_count: Decimal) -> str:
    if open_ticket_count >= HIGH_TICKET_PRESSURE_THRESHOLD:
        return "ticket_pressure_high"
    if open_ticket_count >= ELEVATED_TICKET_PRESSURE_THRESHOLD:
        return "ticket_pressure_elevated"
    return "ticket_pressure_normal"


def _resolution_window_reason_code(
    queue: ResearchQueueSlaBreachForecastV10Input | ResearchQueueSlaBreachForecastV10Result,
) -> str:
    if (
        queue.time_to_market_resolution_minutes
        <= queue.average_resolution_minutes * RESOLUTION_WINDOW_MULTIPLE
    ):
        return "resolution_window_compressed"
    return "resolution_window_clear"


def _validate_result(report: ResearchQueueSlaBreachForecastV10Result) -> None:
    expected_status = _breach_risk_status(report, report.expected_delay_minutes)
    if report.breach_risk_status != expected_status:
        raise ValueError("breach_risk_status must match inputs")
    expected_action = _escalation_action(report, report.breach_risk_status)
    if report.escalation_action != expected_action:
        raise ValueError("escalation_action must match breach_risk_status")
    expected_reason_codes = _reason_codes(
        report,
        report.expected_delay_minutes,
        report.breach_risk_status,
        report.escalation_action,
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match queue SLA forecast")


def _require_config_version(value: str) -> None:
    if value != DEFAULT_RESEARCH_QUEUE_SLA_BREACH_FORECAST_V10_CONFIG_VERSION:
        raise ValueError(
            "config_version must be strategy-research-queue-sla-breach-forecast-v10",
        )


def _require_token(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value or value.lower() != value:
        raise ValueError(f"{field_name} must be lowercase without surrounding whitespace")
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789_.-")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must use lowercase token characters")
    return value


def _require_member(field_name: str, value: str, allowed_values: tuple[str, ...]) -> str:
    value = _require_token(field_name, value)
    if value not in allowed_values:
        allowed = ", ".join(allowed_values)
        raise ValueError(f"{field_name} must be one of: {allowed}")
    return value


def _require_bool(field_name: str, value: bool) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label} must be {field_name}")


def _normalize_unit_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _normalize_nonnegative_decimal(field_name, value)
    if value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return value


def _normalize_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _normalize_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be greater than zero")
    return value


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _normalize_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _normalize_whole_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext() as context:
        context.prec = DECIMAL_PRECISION
        return value.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _normalize_reason_codes(field_name: str, values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        normalized.append(_require_token(field_name, value))
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"{field_name} must not contain duplicates")
    return tuple(normalized)


def _reject_unsupported_payload_fields(payload: dict[str, Any]) -> None:
    for key in payload:
        if key not in PAYLOAD_FIELDS:
            raise ValueError(f"payload field is not supported: {key}")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, (str, bool)):
        return value
    if isinstance(value, dict):
        return _json_dict_ready(value)
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _json_dict_ready(value: dict[Any, Any]) -> dict[str, Any]:
    ready: dict[str, Any] = {}
    for key, item in value.items():
        if type(key) is not str:
            raise ValueError("JSON object keys must be strings")
        ready[key] = _json_ready(item)
    return ready


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        if "paper_only" not in self.value:
            return None
        return self.value["paper_only"]

    @property
    def report_only(self) -> object:
        if "report_only" not in self.value:
            return None
        return self.value["report_only"]

    @property
    def readonly(self) -> object:
        if "readonly" not in self.value:
            return None
        return self.value["readonly"]


__all__ = (
    "DEFAULT_RESEARCH_QUEUE_SLA_BREACH_FORECAST_V10_CONFIG_VERSION",
    "ResearchQueueSlaBreachForecastV10Input",
    "ResearchQueueSlaBreachForecastV10Result",
    "strategy_research_queue_sla_breach_forecast_v10",
    "strategy_research_queue_sla_breach_forecast_v10_payload",
)
