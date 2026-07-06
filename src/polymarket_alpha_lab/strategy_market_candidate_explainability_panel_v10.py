"""Pure report reducer for market candidate explainability panel v10."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
TRIAGE_STATUSES = ("pass", "watch", "blocked")
EXPLANATION_STATUSES = ("ready", "needs_review", "blocked")
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")


@dataclass(frozen=True)
class StrategyMarketCandidateExplainabilityPanelV10Component:
    code: str
    label: str
    value: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_identifier("code", self.code)
        _require_public_text("label", self.label)
        object.__setattr__(self, "value", _normalize_decimal("value", self.value))
        require_paper_only_flags(
            "StrategyMarketCandidateExplainabilityPanelV10Component",
            self,
        )


@dataclass(frozen=True)
class StrategyMarketCandidateExplainabilityPanelV10Input:
    market_id: str
    triage_status: str
    edge_components: tuple[StrategyMarketCandidateExplainabilityPanelV10Component, ...]
    cost_components: tuple[StrategyMarketCandidateExplainabilityPanelV10Component, ...]
    risk_components: tuple[StrategyMarketCandidateExplainabilityPanelV10Component, ...]
    team_assignment: str
    missing_evidence_count: Decimal
    recommended_next_step: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_identifier("market_id", self.market_id)
        _require_triage_status("triage_status", self.triage_status)
        object.__setattr__(
            self,
            "edge_components",
            _normalize_components("edge_components", self.edge_components),
        )
        object.__setattr__(
            self,
            "cost_components",
            _normalize_nonnegative_components(
                "cost_components",
                self.cost_components,
            ),
        )
        object.__setattr__(
            self,
            "risk_components",
            _normalize_nonnegative_components(
                "risk_components",
                self.risk_components,
            ),
        )
        _require_public_text("team_assignment", self.team_assignment)
        object.__setattr__(
            self,
            "missing_evidence_count",
            _normalize_count_decimal(
                "missing_evidence_count",
                self.missing_evidence_count,
            ),
        )
        _require_public_text("recommended_next_step", self.recommended_next_step)
        require_paper_only_flags(
            "StrategyMarketCandidateExplainabilityPanelV10Input",
            self,
        )


@dataclass(frozen=True)
class StrategyMarketCandidateExplainabilityPanelV10Payload:
    market_id: str
    triage_status: str
    edge_components: tuple[StrategyMarketCandidateExplainabilityPanelV10Component, ...]
    cost_components: tuple[StrategyMarketCandidateExplainabilityPanelV10Component, ...]
    risk_components: tuple[StrategyMarketCandidateExplainabilityPanelV10Component, ...]
    edge_total: Decimal
    cost_total: Decimal
    risk_total: Decimal
    net_explainability_score: Decimal
    team_assignment: str
    missing_evidence_count: Decimal
    recommended_next_step: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_identifier("market_id", self.market_id)
        _require_triage_status("triage_status", self.triage_status)
        object.__setattr__(
            self,
            "edge_components",
            _normalize_components("edge_components", self.edge_components),
        )
        object.__setattr__(
            self,
            "cost_components",
            _normalize_nonnegative_components(
                "cost_components",
                self.cost_components,
            ),
        )
        object.__setattr__(
            self,
            "risk_components",
            _normalize_nonnegative_components(
                "risk_components",
                self.risk_components,
            ),
        )
        object.__setattr__(self, "edge_total", _normalize_decimal("edge_total", self.edge_total))
        object.__setattr__(
            self,
            "cost_total",
            _normalize_nonnegative_decimal("cost_total", self.cost_total),
        )
        object.__setattr__(
            self,
            "risk_total",
            _normalize_nonnegative_decimal("risk_total", self.risk_total),
        )
        object.__setattr__(
            self,
            "net_explainability_score",
            _normalize_decimal(
                "net_explainability_score",
                self.net_explainability_score,
            ),
        )
        _require_public_text("team_assignment", self.team_assignment)
        object.__setattr__(
            self,
            "missing_evidence_count",
            _normalize_count_decimal(
                "missing_evidence_count",
                self.missing_evidence_count,
            ),
        )
        _require_public_text("recommended_next_step", self.recommended_next_step)
        _validate_payload_totals(self)
        require_paper_only_flags(
            "StrategyMarketCandidateExplainabilityPanelV10Payload",
            self,
        )


@dataclass(frozen=True)
class StrategyMarketCandidateExplainabilityPanelV10Result:
    explanation_status: str
    summary_points: tuple[str, ...]
    blocking_points: tuple[str, ...]
    positive_points: tuple[str, ...]
    reason_codes: tuple[str, ...]
    payload: StrategyMarketCandidateExplainabilityPanelV10Payload
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_explanation_status("explanation_status", self.explanation_status)
        object.__setattr__(
            self,
            "summary_points",
            _normalize_texts("summary_points", self.summary_points, allow_empty=False),
        )
        object.__setattr__(
            self,
            "blocking_points",
            _normalize_texts("blocking_points", self.blocking_points, allow_empty=True),
        )
        object.__setattr__(
            self,
            "positive_points",
            _normalize_texts("positive_points", self.positive_points, allow_empty=True),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reasons("reason_codes", self.reason_codes, allow_empty=False),
        )
        if type(self.payload) is not StrategyMarketCandidateExplainabilityPanelV10Payload:
            raise ValueError(
                "payload must be a StrategyMarketCandidateExplainabilityPanelV10Payload",
            )
        require_paper_only_flags("payload", self.payload)
        if self.explanation_status != _status_from_reason_codes(self.reason_codes):
            raise ValueError("explanation_status must match reason_codes")
        if bool(self.blocking_points) != (self.explanation_status == "blocked"):
            raise ValueError("blocking_points must match explanation_status")
        require_paper_only_flags(
            "StrategyMarketCandidateExplainabilityPanelV10Result",
            self,
        )


def build_strategy_market_candidate_explainability_panel_v10_result(
    input_row: StrategyMarketCandidateExplainabilityPanelV10Input,
) -> StrategyMarketCandidateExplainabilityPanelV10Result:
    """Explain one candidate screening outcome without side effects."""

    if type(input_row) is not StrategyMarketCandidateExplainabilityPanelV10Input:
        raise ValueError(
            "input_row must be a StrategyMarketCandidateExplainabilityPanelV10Input",
        )
    require_paper_only_flags("input_row", input_row)

    edge_total = _component_total(input_row.edge_components)
    cost_total = _component_total(input_row.cost_components)
    risk_total = _component_total(input_row.risk_components)
    net_score = _quantize(edge_total - cost_total - risk_total)
    payload = StrategyMarketCandidateExplainabilityPanelV10Payload(
        market_id=input_row.market_id,
        triage_status=input_row.triage_status,
        edge_components=input_row.edge_components,
        cost_components=input_row.cost_components,
        risk_components=input_row.risk_components,
        edge_total=edge_total,
        cost_total=cost_total,
        risk_total=risk_total,
        net_explainability_score=net_score,
        team_assignment=input_row.team_assignment,
        missing_evidence_count=input_row.missing_evidence_count,
        recommended_next_step=input_row.recommended_next_step,
    )
    blocking_points = _blocking_points(payload)
    explanation_status = _explanation_status(payload, blocking_points)

    return StrategyMarketCandidateExplainabilityPanelV10Result(
        explanation_status=explanation_status,
        summary_points=_summary_points(payload),
        blocking_points=blocking_points,
        positive_points=_positive_points(payload),
        reason_codes=_reason_codes(payload, explanation_status),
        payload=payload,
    )


def explain_strategy_market_candidate_explainability_panel_v10(
    *,
    market_id: str,
    triage_status: str,
    edge_components: tuple[StrategyMarketCandidateExplainabilityPanelV10Component, ...],
    cost_components: tuple[StrategyMarketCandidateExplainabilityPanelV10Component, ...],
    risk_components: tuple[StrategyMarketCandidateExplainabilityPanelV10Component, ...],
    team_assignment: str,
    missing_evidence_count: Decimal,
    recommended_next_step: str,
) -> StrategyMarketCandidateExplainabilityPanelV10Result:
    input_row = StrategyMarketCandidateExplainabilityPanelV10Input(
        market_id=market_id,
        triage_status=triage_status,
        edge_components=edge_components,
        cost_components=cost_components,
        risk_components=risk_components,
        team_assignment=team_assignment,
        missing_evidence_count=missing_evidence_count,
        recommended_next_step=recommended_next_step,
    )
    return build_strategy_market_candidate_explainability_panel_v10_result(input_row)


def strategy_market_candidate_explainability_panel_v10_payload(
    result: StrategyMarketCandidateExplainabilityPanelV10Result | dict[str, Any],
) -> dict[str, Any]:
    if type(result) is StrategyMarketCandidateExplainabilityPanelV10Result:
        require_paper_only_flags("result", result)
        _reject_payload_values("result", result)
        ready = _json_ready(result)
    elif type(result) is dict:
        _reject_payload_values("payload", result)
        ready = _json_ready(result)
    else:
        raise ValueError(
            "result must be a StrategyMarketCandidateExplainabilityPanelV10Result",
        )
    if type(ready) is not dict:
        raise ValueError("result payload must be a JSON object")
    _require_payload_flags(ready)
    return ready


def _summary_points(
    payload: StrategyMarketCandidateExplainabilityPanelV10Payload,
) -> tuple[str, ...]:
    return (
        (
            f"Market {payload.market_id} is {payload.triage_status} and assigned to "
            f"{payload.team_assignment}."
        ),
        (
            f"Components: edge {_format_decimal(payload.edge_total)} less cost "
            f"{_format_decimal(payload.cost_total)} and risk "
            f"{_format_decimal(payload.risk_total)} leaves net explainability score "
            f"{_format_decimal(payload.net_explainability_score)}."
        ),
        (
            f"Evidence: {_format_decimal(payload.missing_evidence_count)} missing items; "
            f"next step {payload.recommended_next_step}."
        ),
    )


def _blocking_points(
    payload: StrategyMarketCandidateExplainabilityPanelV10Payload,
) -> tuple[str, ...]:
    points: list[str] = []
    if payload.triage_status == "blocked":
        points.append("Triage status is blocked; clear candidate blockers before promotion.")
    if payload.missing_evidence_count > ZERO:
        points.append(
            "Missing evidence count is "
            f"{_format_decimal(payload.missing_evidence_count)}; attach required evidence "
            "before promotion.",
        )
    if payload.net_explainability_score <= ZERO:
        points.append(
            "Net explainability score is not positive: "
            f"{_format_decimal(payload.net_explainability_score)}.",
        )
    return tuple(points)


def _positive_points(
    payload: StrategyMarketCandidateExplainabilityPanelV10Payload,
) -> tuple[str, ...]:
    points: list[str] = []
    if payload.edge_total > ZERO:
        points.append(f"Edge components contribute {_format_decimal(payload.edge_total)}.")
    if payload.net_explainability_score > ZERO:
        points.append(
            "Net explainability score is positive: "
            f"{_format_decimal(payload.net_explainability_score)}.",
        )
    if payload.missing_evidence_count == ZERO:
        points.append("No missing evidence items are reported.")
    points.append(f"Assigned team {payload.team_assignment} owns the next review.")
    return tuple(points)


def _explanation_status(
    payload: StrategyMarketCandidateExplainabilityPanelV10Payload,
    blocking_points: tuple[str, ...],
) -> str:
    if blocking_points:
        return "blocked"
    if payload.triage_status == "pass":
        return "ready"
    return "needs_review"


def _reason_codes(
    payload: StrategyMarketCandidateExplainabilityPanelV10Payload,
    explanation_status: str,
) -> tuple[str, ...]:
    codes = [f"candidate_explainability_{explanation_status}"]
    codes.append(f"candidate_triage_{payload.triage_status}")
    if payload.missing_evidence_count > ZERO:
        codes.append("candidate_missing_evidence_blocked")
    if payload.net_explainability_score > ZERO:
        codes.append("candidate_positive_net_score")
    else:
        codes.append("candidate_nonpositive_net_score_blocked")
    if payload.missing_evidence_count == ZERO:
        codes.append("candidate_evidence_complete")
    codes.append("candidate_team_assignment_ready")
    return _normalize_reasons("reason_codes", tuple(codes), allow_empty=False)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    first_code = reason_codes[0]
    if first_code == "candidate_explainability_blocked":
        return "blocked"
    if first_code == "candidate_explainability_ready":
        return "ready"
    if first_code == "candidate_explainability_needs_review":
        return "needs_review"
    raise ValueError("reason_codes must include a supported explanation status")


def _component_total(
    components: tuple[StrategyMarketCandidateExplainabilityPanelV10Component, ...],
) -> Decimal:
    total = ZERO
    for component in components:
        total = _quantize(total + component.value)
    return total


def _validate_payload_totals(
    payload: StrategyMarketCandidateExplainabilityPanelV10Payload,
) -> None:
    if payload.edge_total != _component_total(payload.edge_components):
        raise ValueError("edge_total must match edge_components")
    if payload.cost_total != _component_total(payload.cost_components):
        raise ValueError("cost_total must match cost_components")
    if payload.risk_total != _component_total(payload.risk_components):
        raise ValueError("risk_total must match risk_components")
    expected_net_score = _quantize(
        payload.edge_total - payload.cost_total - payload.risk_total,
    )
    if payload.net_explainability_score != expected_net_score:
        raise ValueError("net_explainability_score must match component totals")


def _normalize_components(
    field_name: str,
    value: object,
) -> tuple[StrategyMarketCandidateExplainabilityPanelV10Component, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of components")
    try:
        components = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of components") from exc
    for component in components:
        if type(component) is not StrategyMarketCandidateExplainabilityPanelV10Component:
            raise ValueError(
                f"{field_name} must contain "
                "StrategyMarketCandidateExplainabilityPanelV10Component rows",
            )
        require_paper_only_flags(field_name, component)
    return components


def _normalize_nonnegative_components(
    field_name: str,
    value: object,
) -> tuple[StrategyMarketCandidateExplainabilityPanelV10Component, ...]:
    components = _normalize_components(field_name, value)
    for component in components:
        if component.value < ZERO:
            raise ValueError(f"{field_name} must not contain negative values")
    return components


def _require_identifier(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")
    _reject_unsafe_text(field_name, value)


def _require_public_text(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be non-empty text")
    _reject_unsafe_text(field_name, value)


def _require_triage_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in TRIAGE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_explanation_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in EXPLANATION_STATUSES:
        raise ValueError(f"{field_name} must be ready, needs_review, or blocked")


def _normalize_reasons(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    return _normalize_texts(field_name, value, allow_empty=allow_empty)


def _normalize_texts(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    if not allow_empty and not items:
        raise ValueError(f"{field_name} must not be empty")
    for item in items:
        _require_public_text(field_name, item)
    if len(items) != len(set(items)):
        raise ValueError(f"{field_name} must not contain duplicate values")
    return items


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _format_decimal(value: Decimal) -> str:
    return str(_quantize(value))


def _reject_unsafe_text(field_name: str, value: str) -> None:
    normalized = value.lower()
    unsafe_fragments = (
        "wal" "let",
        "private" "_" "key",
        "submit" "_" "order",
        "place" "_" "order",
        "sign" "_" "order",
        "au" "th",
    )
    if any(fragment in normalized for fragment in unsafe_fragments):
        raise ValueError(f"{field_name} contains unsafe surface text")


def _require_payload_flags(value: dict[str, Any]) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if field_name not in value or value[field_name] is not True:
            raise ValueError(f"{field_name} must be True")


def _reject_payload_values(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_payload_values(label, asdict(value), path)
        return
    if type(value) is str:
        _reject_unsafe_text(path or label, value)
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or label} must use Decimal values")
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if type(value) is bool or value is None:
        return
    if isinstance(value, float):
        raise ValueError(f"{path or label} must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal values")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_text("payload key", key)
            item_path = key if not path else f"{path}.{key}"
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_payload_values(label, item, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_payload_values(label, item, item_path)
        return
    raise ValueError("value is not JSON serializable")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if type(value) is bool:
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is str:
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


__all__ = (
    "StrategyMarketCandidateExplainabilityPanelV10Component",
    "StrategyMarketCandidateExplainabilityPanelV10Input",
    "StrategyMarketCandidateExplainabilityPanelV10Payload",
    "StrategyMarketCandidateExplainabilityPanelV10Result",
    "build_strategy_market_candidate_explainability_panel_v10_result",
    "explain_strategy_market_candidate_explainability_panel_v10",
    "strategy_market_candidate_explainability_panel_v10_payload",
)
