"""Pure paper-only autonomous market screening scorer.

This module evaluates markets from a screening gate report and produces
a scored ranking that can be used by the execution pipeline to decide
which markets to propose for paper execution.

Scoring factors:
- confidence: LLM/probabilistic confidence score
- liquidity: order book depth at executable prices
- spread: bid-ask spread tightness
- edge: estimated edge over market price
- cost: total transaction cost (taker fee + slippage)
- risk: position concentration and resolution risk

This module is pure/reducer: no I/O, no DB, no exchange contact.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, localcontext, Context

from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate import (
    PaperAutonomousScreeningDecisionSupportGateReport,
)


__all__ = (
    "DEFAULT_AUTONOMOUS_MARKET_SCORER_CONFIG_VERSION",
    "AutonomousMarketScorerConfig",
    "AutonomousMarketScoreRow",
    "AutonomousMarketScorerReport",
    "build_autonomous_market_scorer_report",
)


DEFAULT_AUTONOMOUS_MARKET_SCORER_CONFIG_VERSION = "autonomous-market-scorer-v0"
DECIMAL_CONTEXT = Context(prec=64)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SCORE_STATUSES = ("scored", "skipped", "blocked")
SIDES = ("yes", "no", "none")


def _validate_hard_flags(label: str, obj: object) -> None:
    for field in ("paper_only", "report_only", "readonly"):
        if getattr(obj, field) is not True:
            raise ValueError(f"{field} must be True for {label}")


def _require_score_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SCORE_STATUSES:
        raise ValueError(f"{field_name} must be one of {SCORE_STATUSES}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field_name} must be a nonnegative int")


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{field_name} must be a positive int")


def _require_decimal(field_name: str, value: object) -> None:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")


def _require_nonnegative_decimal(field_name: str, value: object) -> None:
    _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_optional_decimal(field_name: str, value: object) -> None:
    if value is not None:
        _require_decimal(field_name, value)


def _require_optional_nonnegative_decimal(field_name: str, value: object) -> None:
    if value is not None:
        _require_nonnegative_decimal(field_name, value)


def _quantize(value: Decimal) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _as_utc(value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if value.tzinfo is None:
        raise ValueError("generated_at must be timezone-aware")
    return value.astimezone(UTC)


@dataclass(frozen=True)
class AutonomousMarketScorerConfig:
    config_version: str = DEFAULT_AUTONOMOUS_MARKET_SCORER_CONFIG_VERSION
    confidence_weight: Decimal = Decimal("0.300000")
    liquidity_weight: Decimal = Decimal("0.200000")
    spread_weight: Decimal = Decimal("0.150000")
    edge_weight: Decimal = Decimal("0.200000")
    cost_weight: Decimal = Decimal("0.100000")
    risk_weight: Decimal = Decimal("0.050000")
    min_total_score: Decimal = Decimal("0.100000")
    max_markets: int = 10
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("AutonomousMarketScorerConfig does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not AutonomousMarketScorerConfig:
            raise ValueError("config must be exactly AutonomousMarketScorerConfig")
        _require_canonical_string("config_version", self.config_version)
        for weight_name in (
            "confidence_weight",
            "liquidity_weight",
            "spread_weight",
            "edge_weight",
            "cost_weight",
            "risk_weight",
        ):
            _require_nonnegative_decimal(weight_name, getattr(self, weight_name))
        _require_nonnegative_decimal("min_total_score", self.min_total_score)
        _require_positive_int("max_markets", self.max_markets)
        _validate_hard_flags("config", self)


@dataclass(frozen=True)
class AutonomousMarketScoreRow:
    """Scored ranking row for a single market."""

    condition_id: str
    market_slug: str
    question: str
    scoring_side: str
    confidence_score: Decimal
    liquidity_score: Decimal
    spread_score: Decimal
    edge_score: Decimal
    cost_score: Decimal
    risk_score: Decimal
    total_score: Decimal
    score_status: str
    recommended_notional: Decimal
    estimated_edge: Decimal
    reason_codes: tuple[str, ...]

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("AutonomousMarketScoreRow does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not AutonomousMarketScoreRow:
            raise ValueError("row must be exactly AutonomousMarketScoreRow")
        _require_canonical_string("condition_id", self.condition_id)
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("question", self.question)
        if self.scoring_side not in SIDES:
            raise ValueError(f"scoring_side must be one of {SIDES}")
        for score_name in (
            "confidence_score",
            "liquidity_score",
            "spread_score",
            "edge_score",
            "cost_score",
            "risk_score",
            "total_score",
        ):
            _require_nonnegative_decimal(score_name, getattr(self, score_name))
        _require_score_status("score_status", self.score_status)
        _require_nonnegative_decimal("recommended_notional", self.recommended_notional)
        _require_nonnegative_decimal("estimated_edge", self.estimated_edge)
        _normalize_reason_codes(self.reason_codes)


@dataclass(frozen=True)
class AutonomousMarketScorerReport:
    """Aggregate report from autonomous market scoring."""

    generated_at: datetime
    config_version: str
    gate_status: str
    markets_scored: int
    markets_skipped: int
    markets_blocked: int
    top_total_score: Decimal
    average_total_score: Decimal
    total_recommended_notional: Decimal
    score_rows: tuple[AutonomousMarketScoreRow, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool
    report_only: bool
    readonly: bool

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("AutonomousMarketScorerReport does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not AutonomousMarketScorerReport:
            raise ValueError("report must be exactly AutonomousMarketScorerReport")
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.gate_status not in ("pass", "watch", "blocked"):
            raise ValueError("gate_status must be pass, watch, or blocked")
        _require_nonnegative_int("markets_scored", self.markets_scored)
        _require_nonnegative_int("markets_skipped", self.markets_skipped)
        _require_nonnegative_int("markets_blocked", self.markets_blocked)
        _require_nonnegative_decimal("top_total_score", self.top_total_score)
        _require_nonnegative_decimal("average_total_score", self.average_total_score)
        _require_nonnegative_decimal(
            "total_recommended_notional",
            self.total_recommended_notional,
        )
        if type(self.score_rows) is not tuple:
            raise ValueError("score_rows must be a tuple")
        for row in self.score_rows:
            if type(row) is not AutonomousMarketScoreRow:
                raise ValueError("score_rows entries must be AutonomousMarketScoreRow")
        _normalize_reason_codes(self.reason_codes)
        _validate_hard_flags("report", self)


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    previous: str | None = None
    for code in value:
        if not isinstance(code, str) or not code or code.strip() != code:
            raise ValueError("reason_codes entries must be canonical nonblank strings")
        if previous is not None and previous >= code:
            raise ValueError("reason_codes must be sorted and unique")
        previous = code
    return value


def build_autonomous_market_scorer_report(
    *,
    gate_report: PaperAutonomousScreeningDecisionSupportGateReport,
    config: AutonomousMarketScorerConfig = AutonomousMarketScorerConfig(),
    generated_at: datetime,
    market_data: tuple[dict[str, object], ...] = (),
) -> AutonomousMarketScorerReport:
    """Build a scored market report from a screening gate report.

    Uses the gate report's queue metrics to score markets. In v0, the
    scoring is based on the gate report's aggregate metrics since the
    gate report already aggregates downstream decision support. Future
    versions can accept raw market-level data for finer scoring.
    """
    if type(gate_report) is not PaperAutonomousScreeningDecisionSupportGateReport:
        raise ValueError(
            "gate_report must be exactly PaperAutonomousScreeningDecisionSupportGateReport",
        )
    if type(config) is not AutonomousMarketScorerConfig:
        raise ValueError("config must be exactly AutonomousMarketScorerConfig")
    _validate_hard_flags("config", config)
    generated_at_utc = _as_utc(generated_at)

    gate_status = gate_report.gate_status

    if gate_status == "blocked":
        return _build_blocked_report(
            generated_at=generated_at_utc,
            config=config,
            reason_code="autonomous_market_scorer_gate_blocked",
        )

    if gate_status == "watch":
        return _build_watch_report(
            generated_at=generated_at_utc,
            config=config,
            gate_report=gate_report,
            reason_code="autonomous_market_scorer_gate_watch",
        )

    # gate_status == "pass": score based on queue metrics
    with localcontext(DECIMAL_CONTEXT):
        ready_count = gate_report.queue_ready_count
        research_ready_count = gate_report.queue_research_ready_count
        total_ready_notional = gate_report.queue_total_ready_notional
        largest_ready_notional = gate_report.queue_largest_ready_notional
        top_priority_score = gate_report.queue_top_research_priority_score
        avg_priority_score = gate_report.queue_average_research_priority_score

        score_rows: list[AutonomousMarketScoreRow] = []
        markets_scored = 0
        markets_skipped = 0
        markets_blocked = 0

        # Use aggregate metrics from the gate report for v0 scoring.
        # Each "ready" market gets a composite score based on available metrics.
        if ready_count > 0 and total_ready_notional > ZERO:
            per_market_notional = _quantize(
                total_ready_notional / Decimal(ready_count),
            )
            # Cap per-market notional at largest ready notional
            if per_market_notional > largest_ready_notional:
                per_market_notional = largest_ready_notional

            # Build synthetic score rows from aggregate gate data
            # In v0, we produce a single aggregate score row representing
            # the top opportunity cluster identified by the gate.
            confidence = _quantize(
                min(top_priority_score, ONE),
            ) if top_priority_score > ZERO else ZERO
            liquidity = _quantize(
                min(
                    total_ready_notional / (Decimal(ready_count) * Decimal("10")),
                    ONE,
                ),
            )
            spread = _quantize(min(avg_priority_score, ONE)) if avg_priority_score > ZERO else ZERO
            edge = _quantize(confidence * Decimal("0.5"))
            cost = _quantize(Decimal("0.02"))  # 2% taker fee default
            risk = _quantize(ONE - liquidity)

            with localcontext(DECIMAL_CONTEXT):
                total_score = _quantize(
                    config.confidence_weight * confidence
                    + config.liquidity_weight * liquidity
                    + config.spread_weight * spread
                    + config.edge_weight * edge
                    + config.cost_weight * (ONE - cost)
                    + config.risk_weight * (ONE - risk),
                )

            if total_score >= config.min_total_score:
                score_rows.append(
                    AutonomousMarketScoreRow(
                        condition_id="aggregate_cluster",
                        market_slug="top_ready_cluster",
                        question=f"{ready_count} ready markets",
                        scoring_side="none",
                        confidence_score=confidence,
                        liquidity_score=liquidity,
                        spread_score=spread,
                        edge_score=edge,
                        cost_score=cost,
                        risk_score=risk,
                        total_score=total_score,
                        score_status="scored",
                        recommended_notional=per_market_notional,
                        estimated_edge=edge,
                        reason_codes=(
                            "autonomous_market_scorer_cluster_scored",
                        ),
                    ),
                )
                markets_scored += 1
            else:
                markets_skipped += 1

        total_reason_codes: list[str] = []
        if markets_scored > 0:
            total_reason_codes.append("autonomous_market_scorer_pass")
        if markets_skipped > 0:
            total_reason_codes.append("autonomous_market_scorer_below_threshold")
        if markets_scored == 0 and markets_skipped == 0:
            total_reason_codes.append("autonomous_market_scorer_no_ready_markets")

        gate_status_out = "pass" if markets_scored > 0 else "watch"
        top_total = max((r.total_score for r in score_rows), default=ZERO)
        avg_total = (
            _quantize(
                sum(r.total_score for r in score_rows) / Decimal(len(score_rows)),
            )
            if score_rows
            else ZERO
        )
        total_notional = sum(
            (r.recommended_notional for r in score_rows), ZERO,
        )

        return AutonomousMarketScorerReport(
            generated_at=generated_at_utc,
            config_version=config.config_version,
            gate_status=gate_status_out,
            markets_scored=markets_scored,
            markets_skipped=markets_skipped,
            markets_blocked=markets_blocked,
            top_total_score=top_total,
            average_total_score=avg_total,
            total_recommended_notional=total_notional,
            score_rows=tuple(score_rows),
            reason_codes=tuple(sorted(total_reason_codes)),
            paper_only=True,
            report_only=True,
            readonly=True,
        )


def _build_blocked_report(
    *,
    generated_at: datetime,
    config: AutonomousMarketScorerConfig,
    reason_code: str,
) -> AutonomousMarketScorerReport:
    return AutonomousMarketScorerReport(
        generated_at=generated_at,
        config_version=config.config_version,
        gate_status="blocked",
        markets_scored=0,
        markets_skipped=0,
        markets_blocked=1,
        top_total_score=ZERO,
        average_total_score=ZERO,
        total_recommended_notional=ZERO,
        score_rows=(),
        reason_codes=(reason_code,),
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _build_watch_report(
    *,
    generated_at: datetime,
    config: AutonomousMarketScorerConfig,
    gate_report: PaperAutonomousScreeningDecisionSupportGateReport,
    reason_code: str,
) -> AutonomousMarketScorerReport:
    return AutonomousMarketScorerReport(
        generated_at=generated_at,
        config_version=config.config_version,
        gate_status="watch",
        markets_scored=0,
        markets_skipped=1,
        markets_blocked=0,
        top_total_score=ZERO,
        average_total_score=ZERO,
        total_recommended_notional=ZERO,
        score_rows=(),
        reason_codes=(reason_code,),
        paper_only=True,
        report_only=True,
        readonly=True,
    )
