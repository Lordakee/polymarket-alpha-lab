"""Paper-only cost-aware event strategy reports."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any


__all__ = (
    "PaperCostAwareEventCostAssumptions",
    "PaperCostAwareEventMarketSnapshot",
    "PaperCostAwareEventSideResult",
    "PaperCostAwareEventStrategyConfig",
    "PaperCostAwareEventStrategyGateResult",
    "PaperCostAwareEventStrategyLog",
    "PaperCostAwareEventStrategyReport",
    "build_paper_cost_aware_event_strategy_report",
)


ZERO = Decimal("0")
ONE = Decimal("1")
COST_QUANTUM = Decimal("0.000001")

GATE_NAMES = (
    "data_integrity",
    "confidence",
    "spread",
    "resolution_risk",
    "yes_depth",
    "no_depth",
    "edge_threshold",
)
GATE_STATUSES = ("pass", "fail", "incomplete")
REPORT_STATUSES = (
    "paper_review_ready",
    "watch",
    "blocked_by_inputs",
    "blocked_by_risk",
    "blocked_by_cost",
    "no_paper_edge",
)
SIDES = ("yes", "no")


@dataclass(frozen=True)
class PaperCostAwareEventStrategyConfig:
    config_version: str
    min_confidence: Decimal = Decimal("0.7000")
    max_spread: Decimal = Decimal("0.0500")
    max_resolution_risk: Decimal = Decimal("0.2000")
    min_ask_size: Decimal = Decimal("1.0000")
    min_net_edge: Decimal = Decimal("0.0100")

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_probability_decimal("min_confidence", self.min_confidence)
        _require_nonnegative_decimal("max_spread", self.max_spread)
        _require_nonnegative_decimal("max_resolution_risk", self.max_resolution_risk)
        _require_positive_decimal("min_ask_size", self.min_ask_size)
        _require_nonnegative_decimal("min_net_edge", self.min_net_edge)


@dataclass(frozen=True)
class PaperCostAwareEventCostAssumptions:
    taker_fee_rate: Decimal
    slippage_cost_per_share: Decimal
    funding_cost_per_share: Decimal
    finalization_cost_per_share: Decimal
    time_cost_per_share: Decimal
    risk_cost_per_share: Decimal

    def __post_init__(self) -> None:
        for field_name in (
            "taker_fee_rate",
            "slippage_cost_per_share",
            "funding_cost_per_share",
            "finalization_cost_per_share",
            "time_cost_per_share",
            "risk_cost_per_share",
        ):
            _require_nonnegative_decimal(field_name, getattr(self, field_name))

    @property
    def non_fee_cost_per_share(self) -> Decimal:
        return _quantize_cost(
            self.slippage_cost_per_share
            + self.funding_cost_per_share
            + self.finalization_cost_per_share
            + self.time_cost_per_share
            + self.risk_cost_per_share
        )


@dataclass(frozen=True)
class PaperCostAwareEventMarketSnapshot:
    market_slug: str
    question: str
    fair_probability_yes: Decimal
    confidence: Decimal
    yes_bid: Decimal | None
    yes_ask: Decimal | None
    yes_ask_size: Decimal | None
    no_bid: Decimal | None
    no_ask: Decimal | None
    no_ask_size: Decimal | None
    spread: Decimal
    resolution_risk: Decimal

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("question", self.question)
        _require_probability_decimal("fair_probability_yes", self.fair_probability_yes)
        _require_probability_decimal("confidence", self.confidence)
        for field_name in ("yes_bid", "yes_ask", "no_bid", "no_ask"):
            _require_optional_price_decimal(field_name, getattr(self, field_name))
        for field_name in ("yes_ask_size", "no_ask_size"):
            _require_optional_nonnegative_decimal(field_name, getattr(self, field_name))
        _require_nonnegative_decimal("spread", self.spread)
        _require_nonnegative_decimal("resolution_risk", self.resolution_risk)


@dataclass(frozen=True)
class PaperCostAwareEventStrategyGateResult:
    gate_name: str
    status: str
    reason_code: str
    message: str
    observed_value: Decimal | int | str | None = None
    threshold: Decimal | int | str | None = None

    def __post_init__(self) -> None:
        if self.gate_name not in GATE_NAMES:
            raise ValueError("gate_name must be a known cost-aware event gate")
        if self.status not in GATE_STATUSES:
            raise ValueError("status must be a known cost-aware event gate status")
        _require_canonical_string("reason_code", self.reason_code)
        _require_canonical_string("message", self.message)
        _require_gate_value("observed_value", self.observed_value)
        _require_gate_value("threshold", self.threshold)


@dataclass(frozen=True)
class PaperCostAwareEventSideResult:
    side: str
    fair_probability: Decimal
    executable_price: Decimal | None
    ask_size: Decimal | None
    gross_edge_per_share: Decimal | None
    fee_cost_per_share: Decimal | None
    non_fee_cost_per_share: Decimal | None
    total_cost_per_share: Decimal | None
    net_edge_per_share: Decimal | None
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.side not in SIDES:
            raise ValueError("side must be yes or no")
        _require_probability_decimal("fair_probability", self.fair_probability)
        _require_optional_price_decimal("executable_price", self.executable_price)
        _require_optional_nonnegative_decimal("ask_size", self.ask_size)
        _require_optional_finite_decimal(
            "gross_edge_per_share",
            self.gross_edge_per_share,
        )
        _require_optional_nonnegative_decimal(
            "fee_cost_per_share",
            self.fee_cost_per_share,
        )
        _require_optional_nonnegative_decimal(
            "non_fee_cost_per_share",
            self.non_fee_cost_per_share,
        )
        _require_optional_nonnegative_decimal(
            "total_cost_per_share",
            self.total_cost_per_share,
        )
        _require_optional_finite_decimal("net_edge_per_share", self.net_edge_per_share)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_string_tuple("reason_codes", self.reason_codes),
        )


@dataclass(frozen=True)
class PaperCostAwareEventStrategyReport:
    generated_at: datetime
    config_version: str
    market_slug: str
    question: str
    fair_probability_yes: Decimal
    confidence: Decimal
    yes_bid: Decimal | None
    no_bid: Decimal | None
    spread: Decimal
    resolution_risk: Decimal
    selected_side: str
    status: str
    yes_result: PaperCostAwareEventSideResult
    no_result: PaperCostAwareEventSideResult
    gate_results: tuple[PaperCostAwareEventStrategyGateResult, ...]
    paper_only: bool = True
    report_only: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("question", self.question)
        _require_probability_decimal("fair_probability_yes", self.fair_probability_yes)
        _require_probability_decimal("confidence", self.confidence)
        _require_optional_price_decimal("yes_bid", self.yes_bid)
        _require_optional_price_decimal("no_bid", self.no_bid)
        _require_nonnegative_decimal("spread", self.spread)
        _require_nonnegative_decimal("resolution_risk", self.resolution_risk)
        if self.selected_side not in ("yes", "no", "none"):
            raise ValueError("selected_side must be yes, no, or none")
        if self.status not in REPORT_STATUSES:
            raise ValueError("status must be a known cost-aware event report status")
        if not isinstance(self.yes_result, PaperCostAwareEventSideResult):
            raise ValueError("yes_result must be a PaperCostAwareEventSideResult")
        if not isinstance(self.no_result, PaperCostAwareEventSideResult):
            raise ValueError("no_result must be a PaperCostAwareEventSideResult")
        if self.yes_result.side != "yes":
            raise ValueError("yes_result must describe the yes side")
        if self.no_result.side != "no":
            raise ValueError("no_result must describe the no side")
        object.__setattr__(
            self,
            "gate_results",
            _normalize_gate_tuple(self.gate_results),
        )
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")


@dataclass(frozen=True)
class PaperCostAwareEventStrategyLog:
    path: Path | str

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _normalize_log_path(self.path))

    def append(self, report: PaperCostAwareEventStrategyReport) -> None:
        if not isinstance(report, PaperCostAwareEventStrategyReport):
            raise ValueError("report must be a PaperCostAwareEventStrategyReport")
        _validate_report_tree(report)
        line = json.dumps(_json_ready(asdict(report)), allow_nan=False, sort_keys=True) + "\n"
        _validate_log_parent(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line)


def build_paper_cost_aware_event_strategy_report(
    snapshot: PaperCostAwareEventMarketSnapshot,
    *,
    cost_assumptions: PaperCostAwareEventCostAssumptions,
    config: PaperCostAwareEventStrategyConfig,
    generated_at: datetime,
) -> PaperCostAwareEventStrategyReport:
    if not isinstance(snapshot, PaperCostAwareEventMarketSnapshot):
        raise ValueError("snapshot must be a PaperCostAwareEventMarketSnapshot")
    if not isinstance(cost_assumptions, PaperCostAwareEventCostAssumptions):
        raise ValueError(
            "cost_assumptions must be a PaperCostAwareEventCostAssumptions",
        )
    if not isinstance(config, PaperCostAwareEventStrategyConfig):
        raise ValueError("config must be a PaperCostAwareEventStrategyConfig")
    if not isinstance(generated_at, datetime):
        raise ValueError("generated_at must be a datetime")

    yes_result = _side_result(
        side="yes",
        fair_probability=snapshot.fair_probability_yes,
        executable_price=snapshot.yes_ask,
        ask_size=snapshot.yes_ask_size,
        cost_assumptions=cost_assumptions,
        min_ask_size=config.min_ask_size,
        min_net_edge=config.min_net_edge,
    )
    no_result = _side_result(
        side="no",
        fair_probability=ONE - snapshot.fair_probability_yes,
        executable_price=snapshot.no_ask,
        ask_size=snapshot.no_ask_size,
        cost_assumptions=cost_assumptions,
        min_ask_size=config.min_ask_size,
        min_net_edge=config.min_net_edge,
    )

    gate_results = _gate_results(
        snapshot=snapshot,
        yes_result=yes_result,
        no_result=no_result,
        config=config,
    )
    selected_side = _selected_side(
        yes_result,
        no_result,
        gate_results,
        min_net_edge=config.min_net_edge,
    )
    status = _report_status(
        selected_side=selected_side,
        gate_results=gate_results,
        yes_result=yes_result,
        no_result=no_result,
        min_net_edge=config.min_net_edge,
    )

    return PaperCostAwareEventStrategyReport(
        generated_at=generated_at,
        config_version=config.config_version,
        market_slug=snapshot.market_slug,
        question=snapshot.question,
        fair_probability_yes=snapshot.fair_probability_yes,
        confidence=snapshot.confidence,
        yes_bid=snapshot.yes_bid,
        no_bid=snapshot.no_bid,
        spread=snapshot.spread,
        resolution_risk=snapshot.resolution_risk,
        selected_side=selected_side,
        status=status,
        yes_result=yes_result,
        no_result=no_result,
        gate_results=gate_results,
    )


def _side_result(
    *,
    side: str,
    fair_probability: Decimal,
    executable_price: Decimal | None,
    ask_size: Decimal | None,
    cost_assumptions: PaperCostAwareEventCostAssumptions,
    min_ask_size: Decimal,
    min_net_edge: Decimal,
) -> PaperCostAwareEventSideResult:
    reason_codes: list[str] = []
    if executable_price is None:
        reason_codes.append("missing_ask")
    if ask_size is None:
        reason_codes.append("missing_ask_size")
    elif ask_size <= ZERO or ask_size < min_ask_size:
        reason_codes.append("insufficient_ask_size")

    if executable_price is None:
        return PaperCostAwareEventSideResult(
            side=side,
            fair_probability=fair_probability,
            executable_price=executable_price,
            ask_size=ask_size,
            gross_edge_per_share=None,
            fee_cost_per_share=None,
            non_fee_cost_per_share=None,
            total_cost_per_share=None,
            net_edge_per_share=None,
            reason_codes=tuple(reason_codes),
        )

    gross_edge_per_share = fair_probability - executable_price
    fee_cost_per_share = _quantize_cost(
        cost_assumptions.taker_fee_rate * executable_price * (ONE - executable_price),
    )
    non_fee_cost_per_share = cost_assumptions.non_fee_cost_per_share
    total_cost_per_share = _quantize_cost(fee_cost_per_share + non_fee_cost_per_share)
    net_edge_per_share = _quantize_cost(gross_edge_per_share - total_cost_per_share)
    if net_edge_per_share < min_net_edge:
        reason_codes.append("low_net_edge")

    return PaperCostAwareEventSideResult(
        side=side,
        fair_probability=fair_probability,
        executable_price=executable_price,
        ask_size=ask_size,
        gross_edge_per_share=gross_edge_per_share,
        fee_cost_per_share=fee_cost_per_share,
        non_fee_cost_per_share=non_fee_cost_per_share,
        total_cost_per_share=total_cost_per_share,
        net_edge_per_share=net_edge_per_share,
        reason_codes=tuple(reason_codes) or ("paper_edge_complete",),
    )


def _gate_results(
    *,
    snapshot: PaperCostAwareEventMarketSnapshot,
    yes_result: PaperCostAwareEventSideResult,
    no_result: PaperCostAwareEventSideResult,
    config: PaperCostAwareEventStrategyConfig,
) -> tuple[PaperCostAwareEventStrategyGateResult, ...]:
    data_passes = yes_result.executable_price is not None or no_result.executable_price is not None
    yes_depth_passes = (
        yes_result.executable_price is not None
        and yes_result.ask_size is not None
        and yes_result.ask_size > ZERO
        and yes_result.ask_size >= config.min_ask_size
    )
    no_depth_passes = (
        no_result.executable_price is not None
        and no_result.ask_size is not None
        and no_result.ask_size > ZERO
        and no_result.ask_size >= config.min_ask_size
    )
    edge_passes = (
        _result_clears(yes_result, config.min_net_edge)
        or _result_clears(no_result, config.min_net_edge)
    )
    return (
        _gate(
            "data_integrity",
            "pass" if data_passes else "fail",
            "complete_inputs" if data_passes else "missing_executable_ask",
            "At least one executable ask is available.",
            "yes_or_no_ask",
            "one_executable_ask",
        ),
        _gate(
            "confidence",
            "pass" if snapshot.confidence >= config.min_confidence else "fail",
            "confidence_ready"
            if snapshot.confidence >= config.min_confidence
            else "low_confidence",
            "Confidence is at or above the configured minimum.",
            snapshot.confidence,
            config.min_confidence,
        ),
        _gate(
            "spread",
            "pass" if snapshot.spread <= config.max_spread else "fail",
            "spread_ready" if snapshot.spread <= config.max_spread else "wide_spread",
            "Spread is at or below the configured maximum.",
            snapshot.spread,
            config.max_spread,
        ),
        _gate(
            "resolution_risk",
            "pass" if snapshot.resolution_risk <= config.max_resolution_risk else "fail",
            "resolution_risk_ready"
            if snapshot.resolution_risk <= config.max_resolution_risk
            else "high_resolution_risk",
            "Resolution risk is at or below the configured maximum.",
            snapshot.resolution_risk,
            config.max_resolution_risk,
        ),
        _gate(
            "yes_depth",
            "pass" if yes_depth_passes else "fail",
            "yes_depth_ready" if yes_depth_passes else _depth_reason(yes_result),
            "YES ask depth is at or above the configured minimum.",
            yes_result.ask_size,
            config.min_ask_size,
        ),
        _gate(
            "no_depth",
            "pass" if no_depth_passes else "fail",
            "no_depth_ready" if no_depth_passes else _depth_reason(no_result),
            "NO ask depth is at or above the configured minimum.",
            no_result.ask_size,
            config.min_ask_size,
        ),
        _gate(
            "edge_threshold",
            "pass" if edge_passes else "fail",
            "net_edge_ready" if edge_passes else "low_net_edge",
            "At least one side has net edge at or above the configured minimum.",
            _best_net_edge(yes_result, no_result),
            config.min_net_edge,
        ),
    )


def _gate(
    gate_name: str,
    status: str,
    reason_code: str,
    message: str,
    observed_value: Decimal | int | str | None,
    threshold: Decimal | int | str | None,
) -> PaperCostAwareEventStrategyGateResult:
    return PaperCostAwareEventStrategyGateResult(
        gate_name=gate_name,
        status=status,
        reason_code=reason_code,
        message=message,
        observed_value=observed_value,
        threshold=threshold,
    )


def _selected_side(
    yes_result: PaperCostAwareEventSideResult,
    no_result: PaperCostAwareEventSideResult,
    gate_results: tuple[PaperCostAwareEventStrategyGateResult, ...],
    *,
    min_net_edge: Decimal,
) -> str:
    gates = {gate.gate_name: gate for gate in gate_results}
    if any(
        gates[gate_name].status != "pass"
        for gate_name in ("data_integrity", "confidence", "spread", "resolution_risk")
    ):
        return "none"
    choices = tuple(
        result
        for result in (yes_result, no_result)
        if _result_clears(result, min_net_edge)
        and gates[f"{result.side}_depth"].status == "pass"
    )
    if not choices:
        return "none"
    return max(choices, key=lambda result: result.net_edge_per_share).side


def _report_status(
    *,
    selected_side: str,
    gate_results: tuple[PaperCostAwareEventStrategyGateResult, ...],
    yes_result: PaperCostAwareEventSideResult,
    no_result: PaperCostAwareEventSideResult,
    min_net_edge: Decimal,
) -> str:
    gates = {gate.gate_name: gate for gate in gate_results}
    if gates["data_integrity"].status == "fail":
        return "blocked_by_inputs"
    if gates["yes_depth"].status == "fail" and gates["no_depth"].status == "fail":
        return "blocked_by_inputs"
    if any(
        gates[gate_name].status == "fail"
        for gate_name in ("confidence", "spread", "resolution_risk")
    ):
        return "blocked_by_risk"
    if selected_side != "none":
        return "paper_review_ready"
    if any(
        _watch_candidate(result, gates[f"{result.side}_depth"], min_net_edge)
        for result in (yes_result, no_result)
    ):
        return "watch"
    if any(
        _cost_removed_edge(result) and gates[f"{result.side}_depth"].status == "pass"
        for result in (yes_result, no_result)
    ):
        return "blocked_by_cost"
    return "no_paper_edge"


def _result_clears(
    result: PaperCostAwareEventSideResult,
    min_net_edge: Decimal,
) -> bool:
    return result.net_edge_per_share is not None and result.net_edge_per_share >= min_net_edge


def _watch_candidate(
    result: PaperCostAwareEventSideResult,
    depth_gate: PaperCostAwareEventStrategyGateResult,
    min_net_edge: Decimal,
) -> bool:
    return (
        depth_gate.status == "pass"
        and result.net_edge_per_share is not None
        and ZERO < result.net_edge_per_share < min_net_edge
    )


def _cost_removed_edge(
    result: PaperCostAwareEventSideResult,
) -> bool:
    return (
        result.gross_edge_per_share is not None
        and result.gross_edge_per_share > ZERO
        and result.net_edge_per_share is not None
        and result.net_edge_per_share <= ZERO
    )


def _depth_reason(result: PaperCostAwareEventSideResult) -> str:
    if result.executable_price is None:
        return f"missing_{result.side}_ask"
    if result.ask_size is None:
        return f"missing_{result.side}_ask_size"
    return f"insufficient_{result.side}_ask_size"


def _best_net_edge(
    yes_result: PaperCostAwareEventSideResult,
    no_result: PaperCostAwareEventSideResult,
) -> Decimal | None:
    values = tuple(
        result.net_edge_per_share
        for result in (yes_result, no_result)
        if result.net_edge_per_share is not None
    )
    return max(values) if values else None


def _as_utc(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError("datetime value is required")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: str) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_decimal(field_name: str, value: Decimal) -> None:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")


def _require_finite_decimal(field_name: str, value: Decimal) -> None:
    _require_decimal(field_name, value)
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_optional_finite_decimal(field_name: str, value: Decimal | None) -> None:
    if value is not None:
        _require_finite_decimal(field_name, value)


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> None:
    _require_finite_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_positive_decimal(field_name: str, value: Decimal) -> None:
    _require_finite_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")


def _require_optional_nonnegative_decimal(field_name: str, value: Decimal | None) -> None:
    if value is not None:
        _require_nonnegative_decimal(field_name, value)


def _require_probability_decimal(field_name: str, value: Decimal) -> None:
    _require_finite_decimal(field_name, value)
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")


def _require_optional_price_decimal(field_name: str, value: Decimal | None) -> None:
    if value is not None:
        _require_probability_decimal(field_name, value)


def _require_gate_value(field_name: str, value: Decimal | int | str | None) -> None:
    if value is None:
        return
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must not be a bool")
    if isinstance(value, Decimal):
        _require_finite_decimal(field_name, value)
        return
    if isinstance(value, int):
        return
    if isinstance(value, str):
        _require_canonical_string(field_name, value)
        return
    raise ValueError(f"{field_name} must be a Decimal, int, string, or None")


def _normalize_string_tuple(field_name: str, value: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    if not items:
        raise ValueError(f"{field_name} must contain at least one value")
    for item in items:
        _require_canonical_string(field_name, item)
    return items


def _normalize_gate_tuple(
    value: tuple[PaperCostAwareEventStrategyGateResult, ...],
) -> tuple[PaperCostAwareEventStrategyGateResult, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("gate_results must be an iterable")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError("gate_results must be an iterable") from exc
    if not all(isinstance(item, PaperCostAwareEventStrategyGateResult) for item in items):
        raise ValueError(
            "gate_results must contain PaperCostAwareEventStrategyGateResult values",
        )
    if tuple(item.gate_name for item in items) != GATE_NAMES:
        raise ValueError("gate_results must contain the cost-aware event gates")
    return items


def _quantize_cost(value: Decimal) -> Decimal:
    _require_finite_decimal("cost", value)
    return value.quantize(COST_QUANTUM)


def _validate_report_tree(report: PaperCostAwareEventStrategyReport) -> None:
    gate_results = tuple(
        PaperCostAwareEventStrategyGateResult(
            gate_name=gate.gate_name,
            status=gate.status,
            reason_code=gate.reason_code,
            message=gate.message,
            observed_value=gate.observed_value,
            threshold=gate.threshold,
        )
        for gate in report.gate_results
    )
    yes_result = PaperCostAwareEventSideResult(
        side=report.yes_result.side,
        fair_probability=report.yes_result.fair_probability,
        executable_price=report.yes_result.executable_price,
        ask_size=report.yes_result.ask_size,
        gross_edge_per_share=report.yes_result.gross_edge_per_share,
        fee_cost_per_share=report.yes_result.fee_cost_per_share,
        non_fee_cost_per_share=report.yes_result.non_fee_cost_per_share,
        total_cost_per_share=report.yes_result.total_cost_per_share,
        net_edge_per_share=report.yes_result.net_edge_per_share,
        reason_codes=report.yes_result.reason_codes,
    )
    no_result = PaperCostAwareEventSideResult(
        side=report.no_result.side,
        fair_probability=report.no_result.fair_probability,
        executable_price=report.no_result.executable_price,
        ask_size=report.no_result.ask_size,
        gross_edge_per_share=report.no_result.gross_edge_per_share,
        fee_cost_per_share=report.no_result.fee_cost_per_share,
        non_fee_cost_per_share=report.no_result.non_fee_cost_per_share,
        total_cost_per_share=report.no_result.total_cost_per_share,
        net_edge_per_share=report.no_result.net_edge_per_share,
        reason_codes=report.no_result.reason_codes,
    )
    PaperCostAwareEventStrategyReport(
        generated_at=report.generated_at,
        config_version=report.config_version,
        market_slug=report.market_slug,
        question=report.question,
        fair_probability_yes=report.fair_probability_yes,
        confidence=report.confidence,
        yes_bid=report.yes_bid,
        no_bid=report.no_bid,
        spread=report.spread,
        resolution_risk=report.resolution_risk,
        selected_side=report.selected_side,
        status=report.status,
        yes_result=yes_result,
        no_result=no_result,
        gate_results=gate_results,
        paper_only=report.paper_only,
        report_only=report.report_only,
    )


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        _require_finite_decimal("JSON Decimal value", value)
        return str(value)
    if isinstance(value, datetime):
        return _as_utc(value).isoformat()
    if isinstance(value, bool) or value is None or isinstance(value, (int, str)):
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, (tuple, list)):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for item_key, item_value in value.items():
            if not isinstance(item_key, str):
                raise ValueError("JSON object keys must be strings")
            ready[item_key] = _json_ready(item_value)
        return ready
    raise ValueError("value is not JSON serializable")


def _normalize_log_path(value: Path | str) -> Path:
    if isinstance(value, str):
        if not value.strip():
            raise ValueError("path must be nonblank")
        path = Path(value)
    elif isinstance(value, Path):
        path = value
    else:
        raise ValueError("path must be a Path or string")
    if path.exists() and path.is_dir():
        raise ValueError("path must not be an existing directory")
    _validate_log_parent(path)
    return path


def _validate_log_parent(path: Path) -> None:
    parent = path.parent
    while not parent.exists():
        if parent == parent.parent:
            break
        parent = parent.parent
    if parent.exists() and not parent.is_dir():
        raise ValueError("parent path must be a directory")
