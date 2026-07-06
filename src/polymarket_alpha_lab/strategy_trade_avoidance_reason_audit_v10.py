"""Pure paper report reducer for candidate avoidance reason audits."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import reject_unsafe_surface_fields


DEFAULT_STRATEGY_AVOIDANCE_REASON_AUDIT_V10_CONFIG_VERSION = (
    "strategy-avoidance-reason-audit-v10"
)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

AVOIDANCE_STATUSES = ("clear", "review", "avoid")
LIQUIDITY_STATUSES = ("pass", "watch", "blocked")
RESOLUTION_RISK_TIERS = ("low", "medium", "high")
SOURCE_QUORUM_STATUSES = ("pass", "watch", "blocked")
TEAM_CAPACITY_STATUSES = ("available", "constrained", "blocked")
NO_AVOIDANCE_REASON = "no_avoidance_reason"
REASON_PRIORITY = (
    "liquidity_blocked",
    "source_quorum_blocked",
    "resolution_risk_high",
    "team_capacity_blocked",
    "edge_score_below_floor",
    "cost_drag_score_above_limit",
    "human_review_required",
    "liquidity_watch",
    "resolution_risk_medium",
    "source_quorum_watch",
    "team_capacity_constrained",
)
HARD_REASONS = frozenset(
    (
        "liquidity_blocked",
        "source_quorum_blocked",
        "resolution_risk_high",
        "team_capacity_blocked",
        "edge_score_below_floor",
        "cost_drag_score_above_limit",
    ),
)
REVIEW_REASONS = frozenset(
    (
        "human_review_required",
        "liquidity_watch",
        "resolution_risk_medium",
        "source_quorum_watch",
        "team_capacity_constrained",
    ),
)


@dataclass(frozen=True)
class StrategyAvoidanceReasonAuditV10Config:
    config_version: str = DEFAULT_STRATEGY_AVOIDANCE_REASON_AUDIT_V10_CONFIG_VERSION
    minimum_edge_score: Decimal = Decimal("0.550000")
    maximum_cost_drag_score: Decimal = Decimal("0.450000")
    clear_recheck_minutes: Decimal = Decimal("30.000000")
    review_recheck_minutes: Decimal = Decimal("120.000000")
    avoid_recheck_minutes: Decimal = Decimal("480.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_identifier("config_version", self.config_version)
        object.__setattr__(
            self,
            "minimum_edge_score",
            _normalize_ratio("minimum_edge_score", self.minimum_edge_score),
        )
        object.__setattr__(
            self,
            "maximum_cost_drag_score",
            _normalize_ratio("maximum_cost_drag_score", self.maximum_cost_drag_score),
        )
        for field_name in (
            "clear_recheck_minutes",
            "review_recheck_minutes",
            "avoid_recheck_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.minimum_edge_score < self.maximum_cost_drag_score:
            raise ValueError("config thresholds must keep edge floor above cost limit")
        if not (
            self.clear_recheck_minutes
            <= self.review_recheck_minutes
            <= self.avoid_recheck_minutes
        ):
            raise ValueError("recheck_minutes must ascend by severity")
        _require_flags("config", self)


@dataclass(frozen=True)
class StrategyAvoidanceReasonAuditV10Input:
    edge_score: Decimal
    cost_drag_score: Decimal
    liquidity_status: str
    resolution_risk_tier: str
    source_quorum_status: str
    human_review_required: bool
    team_capacity_status: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "edge_score",
            _normalize_ratio("edge_score", self.edge_score),
        )
        object.__setattr__(
            self,
            "cost_drag_score",
            _normalize_ratio("cost_drag_score", self.cost_drag_score),
        )
        object.__setattr__(
            self,
            "liquidity_status",
            _normalize_choice("liquidity_status", self.liquidity_status, LIQUIDITY_STATUSES),
        )
        object.__setattr__(
            self,
            "resolution_risk_tier",
            _normalize_choice(
                "resolution_risk_tier",
                self.resolution_risk_tier,
                RESOLUTION_RISK_TIERS,
            ),
        )
        object.__setattr__(
            self,
            "source_quorum_status",
            _normalize_choice(
                "source_quorum_status",
                self.source_quorum_status,
                SOURCE_QUORUM_STATUSES,
            ),
        )
        if type(self.human_review_required) is not bool:
            raise ValueError("human_review_required must be a bool")
        object.__setattr__(
            self,
            "team_capacity_status",
            _normalize_choice(
                "team_capacity_status",
                self.team_capacity_status,
                TEAM_CAPACITY_STATUSES,
            ),
        )
        _require_flags("input", self)


@dataclass(frozen=True)
class StrategyAvoidanceReasonAuditV10Payload:
    config_version: str
    edge_score: Decimal
    cost_drag_score: Decimal
    liquidity_status: str
    resolution_risk_tier: str
    source_quorum_status: str
    human_review_required: bool
    team_capacity_status: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_identifier("config_version", self.config_version)
        object.__setattr__(
            self,
            "edge_score",
            _normalize_ratio("edge_score", self.edge_score),
        )
        object.__setattr__(
            self,
            "cost_drag_score",
            _normalize_ratio("cost_drag_score", self.cost_drag_score),
        )
        object.__setattr__(
            self,
            "liquidity_status",
            _normalize_choice("liquidity_status", self.liquidity_status, LIQUIDITY_STATUSES),
        )
        object.__setattr__(
            self,
            "resolution_risk_tier",
            _normalize_choice(
                "resolution_risk_tier",
                self.resolution_risk_tier,
                RESOLUTION_RISK_TIERS,
            ),
        )
        object.__setattr__(
            self,
            "source_quorum_status",
            _normalize_choice(
                "source_quorum_status",
                self.source_quorum_status,
                SOURCE_QUORUM_STATUSES,
            ),
        )
        if type(self.human_review_required) is not bool:
            raise ValueError("human_review_required must be a bool")
        object.__setattr__(
            self,
            "team_capacity_status",
            _normalize_choice(
                "team_capacity_status",
                self.team_capacity_status,
                TEAM_CAPACITY_STATUSES,
            ),
        )
        _require_flags("payload", self)


@dataclass(frozen=True)
class StrategyAvoidanceReasonAuditV10Result:
    avoidance_status: str
    primary_avoidance_reason: str
    secondary_reasons: tuple[str, ...]
    recheck_minutes: Decimal
    payload: StrategyAvoidanceReasonAuditV10Payload
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "avoidance_status",
            _normalize_choice("avoidance_status", self.avoidance_status, AVOIDANCE_STATUSES),
        )
        _require_reason("primary_avoidance_reason", self.primary_avoidance_reason)
        object.__setattr__(
            self,
            "secondary_reasons",
            _normalize_reasons("secondary_reasons", self.secondary_reasons),
        )
        object.__setattr__(
            self,
            "recheck_minutes",
            _normalize_nonnegative_decimal("recheck_minutes", self.recheck_minutes),
        )
        if type(self.payload) is not StrategyAvoidanceReasonAuditV10Payload:
            raise ValueError("payload must be a StrategyAvoidanceReasonAuditV10Payload")
        _require_flags("payload", self.payload)
        if self.primary_avoidance_reason in self.secondary_reasons:
            raise ValueError("primary_avoidance_reason must not be repeated")
        if self.avoidance_status == "clear":
            if self.primary_avoidance_reason != NO_AVOIDANCE_REASON:
                raise ValueError("primary_avoidance_reason must match clear status")
            if self.secondary_reasons:
                raise ValueError("secondary_reasons must be empty for clear status")
        elif self.primary_avoidance_reason == NO_AVOIDANCE_REASON:
            raise ValueError("primary_avoidance_reason must explain non-clear status")
        if self.avoidance_status == "avoid" and (
            self.primary_avoidance_reason not in HARD_REASONS
        ):
            raise ValueError("primary_avoidance_reason must be a hard reason")
        if self.avoidance_status == "review" and (
            self.primary_avoidance_reason not in REVIEW_REASONS
        ):
            raise ValueError("primary_avoidance_reason must be a review reason")
        _require_flags("result", self)


def audit_strategy_avoidance_reason_v10(
    input_row: StrategyAvoidanceReasonAuditV10Input,
    *,
    config: StrategyAvoidanceReasonAuditV10Config | None = None,
) -> StrategyAvoidanceReasonAuditV10Result:
    if type(input_row) is not StrategyAvoidanceReasonAuditV10Input:
        raise ValueError("input_row must be a StrategyAvoidanceReasonAuditV10Input")
    cfg = config or StrategyAvoidanceReasonAuditV10Config()
    if type(cfg) is not StrategyAvoidanceReasonAuditV10Config:
        raise ValueError("config must be a StrategyAvoidanceReasonAuditV10Config")
    _require_flags("input", input_row)
    _require_flags("config", cfg)

    payload = StrategyAvoidanceReasonAuditV10Payload(
        config_version=cfg.config_version,
        edge_score=input_row.edge_score,
        cost_drag_score=input_row.cost_drag_score,
        liquidity_status=input_row.liquidity_status,
        resolution_risk_tier=input_row.resolution_risk_tier,
        source_quorum_status=input_row.source_quorum_status,
        human_review_required=input_row.human_review_required,
        team_capacity_status=input_row.team_capacity_status,
    )
    reasons = _reason_list(input_row, config=cfg)
    hard_reasons = tuple(reason for reason in reasons if reason in HARD_REASONS)
    if hard_reasons:
        status = "avoid"
        primary = _first_matching_reason(REASON_PRIORITY, hard_reasons)
        recheck_minutes = cfg.avoid_recheck_minutes
    elif reasons:
        status = "review"
        primary = (
            "human_review_required"
            if "human_review_required" in reasons
            else _first_matching_reason(REASON_PRIORITY, reasons)
        )
        recheck_minutes = cfg.review_recheck_minutes
    else:
        status = "clear"
        primary = NO_AVOIDANCE_REASON
        recheck_minutes = cfg.clear_recheck_minutes
    secondary_reasons = tuple(reason for reason in reasons if reason != primary)

    return StrategyAvoidanceReasonAuditV10Result(
        avoidance_status=status,
        primary_avoidance_reason=primary,
        secondary_reasons=secondary_reasons,
        recheck_minutes=recheck_minutes,
        payload=payload,
    )


def audit_strategy_avoidance_reason_v10_from_fields(
    *,
    edge_score: Decimal,
    cost_drag_score: Decimal,
    liquidity_status: str,
    resolution_risk_tier: str,
    source_quorum_status: str,
    human_review_required: bool,
    team_capacity_status: str,
    config: StrategyAvoidanceReasonAuditV10Config | None = None,
) -> StrategyAvoidanceReasonAuditV10Result:
    return audit_strategy_avoidance_reason_v10(
        StrategyAvoidanceReasonAuditV10Input(
            edge_score=edge_score,
            cost_drag_score=cost_drag_score,
            liquidity_status=liquidity_status,
            resolution_risk_tier=resolution_risk_tier,
            source_quorum_status=source_quorum_status,
            human_review_required=human_review_required,
            team_capacity_status=team_capacity_status,
        ),
        config=config,
    )


def strategy_avoidance_reason_audit_v10_payload(
    result: StrategyAvoidanceReasonAuditV10Result | dict[str, Any],
) -> dict[str, Any]:
    if type(result) is StrategyAvoidanceReasonAuditV10Result:
        _require_flags("result", result)
        reject_unsafe_surface_fields("strategy avoidance reason audit result", result)
        ready = _json_ready(result)
    elif type(result) is dict:
        reject_unsafe_surface_fields("strategy avoidance reason audit payload", result)
        ready = _json_ready(result)
    else:
        raise ValueError("result must be a StrategyAvoidanceReasonAuditV10Result")
    if type(ready) is not dict:
        raise ValueError("result payload must be a JSON object")
    _require_flags("payload", _DictFlags(ready))
    reject_unsafe_surface_fields("strategy avoidance reason audit payload", ready)
    return ready


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


def _reason_list(
    input_row: StrategyAvoidanceReasonAuditV10Input,
    *,
    config: StrategyAvoidanceReasonAuditV10Config,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if input_row.liquidity_status == "blocked":
        reasons.append("liquidity_blocked")
    elif input_row.liquidity_status == "watch":
        reasons.append("liquidity_watch")
    if input_row.source_quorum_status == "blocked":
        reasons.append("source_quorum_blocked")
    elif input_row.source_quorum_status == "watch":
        reasons.append("source_quorum_watch")
    if input_row.resolution_risk_tier == "high":
        reasons.append("resolution_risk_high")
    elif input_row.resolution_risk_tier == "medium":
        reasons.append("resolution_risk_medium")
    if input_row.team_capacity_status == "blocked":
        reasons.append("team_capacity_blocked")
    elif input_row.team_capacity_status == "constrained":
        reasons.append("team_capacity_constrained")
    if input_row.edge_score < config.minimum_edge_score:
        reasons.append("edge_score_below_floor")
    if input_row.cost_drag_score > config.maximum_cost_drag_score:
        reasons.append("cost_drag_score_above_limit")
    if input_row.human_review_required:
        reasons.append("human_review_required")
    return tuple(reason for reason in REASON_PRIORITY if reason in reasons)


def _first_matching_reason(
    candidates: tuple[str, ...],
    reasons: tuple[str, ...],
) -> str:
    for candidate in candidates:
        if candidate in reasons:
            return candidate
    raise ValueError("reason set is empty")


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _q(value)


def _q(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _normalize_choice(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> str:
    _require_identifier(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be a supported value")
    return value


def _require_identifier(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be a nonblank trimmed string")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")


def _require_reason(field_name: str, value: object) -> None:
    _require_identifier(field_name, value)
    if value != NO_AVOIDANCE_REASON and value not in REASON_PRIORITY:
        raise ValueError(f"{field_name} must be a supported reason")


def _normalize_reasons(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    for item in value:
        _require_reason(field_name, item)
        if item == NO_AVOIDANCE_REASON:
            raise ValueError(f"{field_name} must not include clear reason")
    if len(value) != len(set(value)):
        raise ValueError(f"{field_name} must be unique")
    return value


def _require_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if value is None:
        return None
    if type(value) is bool:
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is str:
        return value
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    raise ValueError("value is not JSON serializable")


__all__ = (
    "DEFAULT_STRATEGY_AVOIDANCE_REASON_AUDIT_V10_CONFIG_VERSION",
    "StrategyAvoidanceReasonAuditV10Config",
    "StrategyAvoidanceReasonAuditV10Input",
    "StrategyAvoidanceReasonAuditV10Payload",
    "StrategyAvoidanceReasonAuditV10Result",
    "audit_strategy_avoidance_reason_v10",
    "audit_strategy_avoidance_reason_v10_from_fields",
    "strategy_avoidance_reason_audit_v10_payload",
)
