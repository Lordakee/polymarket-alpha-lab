"""Phase 1 readonly probability recommendation safety gate."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


__all__ = (
    "DEFAULT_STRATEGY_PROBABILITY_RECOMMENDATION_SAFETY_GATE_V2_CONFIG_VERSION",
    "StrategyProbabilityRecommendationSafetyGateV2Config",
    "StrategyProbabilityRecommendationSafetyGateV2Input",
    "StrategyProbabilityRecommendationSafetyGateV2ReasonCodeCount",
    "StrategyProbabilityRecommendationSafetyGateV2Report",
    "StrategyProbabilityRecommendationSafetyGateV2Row",
    "build_strategy_probability_recommendation_safety_gate_v2_report",
    "strategy_probability_recommendation_safety_gate_v2_payload",
)


DEFAULT_STRATEGY_PROBABILITY_RECOMMENDATION_SAFETY_GATE_V2_CONFIG_VERSION = (
    "strategy-probability-recommendation-safety-gate-v2"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUSES = ("pass", "watch", "blocked")
STATUS_WEIGHT = {
    "blocked": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}
NEXT_STEP_BY_STATUS = {
    "pass": "paper_monitor_only",
    "watch": "watch_recommendation",
    "blocked": "block_recommendation",
}
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
UNSAFE_PUBLIC_FRAGMENTS = (
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
    "trade",
)
ROW_REASON_PRIORITY = (
    "safety_category_concentration_excessive_blocked",
    "safety_cost_adjusted_edge_negative_blocked",
    "safety_evidence_quality_low_blocked",
    "safety_liquidity_exit_risk_high_blocked",
    "safety_cost_adjusted_edge_thin_watch",
    "safety_evidence_quality_thin_watch",
    "safety_quorum_weak_watch",
    "safety_resolution_risk_high_blocked",
    "safety_gate_clear",
)
REPORT_REASON_PRIORITY = (
    "safety_category_concentration_excessive_blocked",
    "safety_cost_adjusted_edge_thin_watch",
    "safety_cost_adjusted_edge_negative_blocked",
    "safety_evidence_quality_low_blocked",
    "safety_evidence_quality_thin_watch",
    "safety_liquidity_exit_risk_high_blocked",
    "safety_quorum_weak_watch",
    "safety_resolution_risk_high_blocked",
)
HEX_CHARS = frozenset("0123456789abcdef")


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise ValueError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class StrategyProbabilityRecommendationSafetyGateV2Config(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_STRATEGY_PROBABILITY_RECOMMENDATION_SAFETY_GATE_V2_CONFIG_VERSION
    )
    min_pass_cost_adjusted_edge: Decimal = Decimal("0.030000")
    min_watch_cost_adjusted_edge: Decimal = Decimal("0.010000")
    min_evidence_quality_score: Decimal = Decimal("0.700000")
    max_resolution_risk_score: Decimal = Decimal("0.400000")
    max_liquidity_exit_risk_score: Decimal = Decimal("0.500000")
    min_specialist_quorum_score: Decimal = Decimal("0.666667")
    max_category_concentration_share: Decimal = Decimal("0.350000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyProbabilityRecommendationSafetyGateV2Config, "config")
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_STRATEGY_PROBABILITY_RECOMMENDATION_SAFETY_GATE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_pass_cost_adjusted_edge",
            "min_watch_cost_adjusted_edge",
            "min_evidence_quality_score",
            "max_resolution_risk_score",
            "max_liquidity_exit_risk_score",
            "min_specialist_quorum_score",
            "max_category_concentration_share",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_watch_cost_adjusted_edge > self.min_pass_cost_adjusted_edge:
            raise ValueError("min_watch_cost_adjusted_edge must not exceed pass threshold")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class StrategyProbabilityRecommendationSafetyGateV2Input(_FinalPublicDataclass):
    recommendation_id: str
    category: str
    estimated_probability: Decimal
    market_price: Decimal
    fee_probability_cost: Decimal
    slippage_probability_cost: Decimal
    evidence_quality_score: Decimal
    resolution_risk_score: Decimal
    liquidity_exit_risk_score: Decimal
    specialist_quorum_score: Decimal
    category_concentration_share: Decimal
    observed_at: datetime
    source_config_version: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyProbabilityRecommendationSafetyGateV2Input, "input")
        for field_name in (
            "recommendation_id",
            "category",
            "source_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "estimated_probability",
            "market_price",
            "fee_probability_cost",
            "slippage_probability_cost",
            "evidence_quality_score",
            "resolution_risk_score",
            "liquidity_exit_risk_score",
            "specialist_quorum_score",
            "category_concentration_share",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class StrategyProbabilityRecommendationSafetyGateV2Row(_FinalPublicDataclass):
    recommendation_id: str
    category: str
    gate_status: str
    raw_probability_edge: Decimal
    total_probability_cost: Decimal
    cost_adjusted_edge: Decimal
    estimated_probability: Decimal
    market_price: Decimal
    fee_probability_cost: Decimal
    slippage_probability_cost: Decimal
    evidence_quality_score: Decimal
    resolution_risk_score: Decimal
    liquidity_exit_risk_score: Decimal
    specialist_quorum_score: Decimal
    category_concentration_share: Decimal
    observed_at: datetime
    source_config_version: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyProbabilityRecommendationSafetyGateV2Row, "row")
        for field_name in (
            "recommendation_id",
            "category",
            "source_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_status("gate_status", self.gate_status)
        for field_name in (
            "raw_probability_edge",
            "cost_adjusted_edge",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_signed_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "total_probability_cost",
            "estimated_probability",
            "market_price",
            "fee_probability_cost",
            "slippage_probability_cost",
            "evidence_quality_score",
            "resolution_risk_score",
            "liquidity_exit_risk_score",
            "specialist_quorum_score",
            "category_concentration_share",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class StrategyProbabilityRecommendationSafetyGateV2ReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    recommendation_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            StrategyProbabilityRecommendationSafetyGateV2ReasonCodeCount,
            "reason_code_count",
        )
        _require_public_string("reason_code", self.reason_code)
        object.__setattr__(self, "count", _require_count_decimal("count", self.count))
        object.__setattr__(
            self,
            "recommendation_ratio",
            _require_ratio_decimal("recommendation_ratio", self.recommendation_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class StrategyProbabilityRecommendationSafetyGateV2Report(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    recommendation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    min_cost_adjusted_edge: Decimal
    min_evidence_quality_score: Decimal
    max_resolution_risk_score: Decimal
    max_liquidity_exit_risk_score: Decimal
    min_specialist_quorum_score: Decimal
    max_category_concentration_share: Decimal
    status: str
    recommended_next_step: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[StrategyProbabilityRecommendationSafetyGateV2ReasonCodeCount, ...]
    rows: tuple[StrategyProbabilityRecommendationSafetyGateV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyProbabilityRecommendationSafetyGateV2Report, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_STRATEGY_PROBABILITY_RECOMMENDATION_SAFETY_GATE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "recommendation_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_cost_adjusted_edge",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_signed_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_evidence_quality_score",
            "max_resolution_risk_score",
            "max_liquidity_exit_risk_score",
            "min_specialist_quorum_score",
            "max_category_concentration_share",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        _require_public_string("recommended_next_step", self.recommended_next_step)
        if self.recommended_next_step != NEXT_STEP_BY_STATUS[self.status]:
            raise ValueError("recommended_next_step must match status")
        object.__setattr__(
            self,
            "reason_codes",
            _require_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _require_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _require_rows(self.rows))
        _validate_report_status(self)
        if self.derived_validation_digest:
            _require_sha256("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != _derived_validation_digest(self):
                raise ValueError("derived_validation_digest does not match report payload")
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _derived_validation_digest(self),
            )
        _validate_report_materialized_fields(self)
        _reject_unsafe_public_payload("report", self)
        _require_hard_flags("report", self)


def build_strategy_probability_recommendation_safety_gate_v2_report(
    recommendations: Iterable[StrategyProbabilityRecommendationSafetyGateV2Input],
    *,
    config: StrategyProbabilityRecommendationSafetyGateV2Config,
    generated_at: datetime,
) -> StrategyProbabilityRecommendationSafetyGateV2Report:
    if type(config) is not StrategyProbabilityRecommendationSafetyGateV2Config:
        raise ValueError(
            "config must be a StrategyProbabilityRecommendationSafetyGateV2Config",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(recommendations)
    rows = tuple(
        sorted(
            (
                _row_from_input(
                    item,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for item in inputs
            ),
            key=_row_sort_key,
        ),
    )
    status = _rollup_status(tuple(row.gate_status for row in rows))
    return StrategyProbabilityRecommendationSafetyGateV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        recommendation_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        min_cost_adjusted_edge=_min_decimal(
            tuple(row.cost_adjusted_edge for row in rows),
        ),
        min_evidence_quality_score=_min_decimal(
            tuple(row.evidence_quality_score for row in rows),
        ),
        max_resolution_risk_score=_max_decimal(
            tuple(row.resolution_risk_score for row in rows),
        ),
        max_liquidity_exit_risk_score=_max_decimal(
            tuple(row.liquidity_exit_risk_score for row in rows),
        ),
        min_specialist_quorum_score=_min_decimal(
            tuple(row.specialist_quorum_score for row in rows),
        ),
        max_category_concentration_share=_max_decimal(
            tuple(row.category_concentration_share for row in rows),
        ),
        status=status,
        recommended_next_step=NEXT_STEP_BY_STATUS[status],
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def strategy_probability_recommendation_safety_gate_v2_payload(
    report: StrategyProbabilityRecommendationSafetyGateV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyProbabilityRecommendationSafetyGateV2Report:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(report)
        if not isinstance(payload, dict):
            raise ValueError("report payload must be an object")
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        _reject_public_numeric_values(report)
        payload = _json_ready(report)
        if not isinstance(payload, dict):
            raise ValueError("report payload must be an object")
        _require_hard_flags("payload", _PayloadFlags(payload))
        supplied_digest = payload.get("derived_validation_digest")
        if type(supplied_digest) is not str:
            raise ValueError("derived_validation_digest is required")
        _require_sha256("derived_validation_digest", supplied_digest)
        if supplied_digest != _payload_validation_digest(payload):
            raise ValueError("derived_validation_digest does not match report payload")
        return payload
    raise ValueError(
        "report must be a StrategyProbabilityRecommendationSafetyGateV2Report",
    )


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


def _normalize_inputs(
    recommendations: Iterable[StrategyProbabilityRecommendationSafetyGateV2Input],
) -> tuple[StrategyProbabilityRecommendationSafetyGateV2Input, ...]:
    if isinstance(recommendations, (str, bytes)):
        raise ValueError("recommendations must be an iterable")
    try:
        items = tuple(recommendations)
    except TypeError as exc:
        raise ValueError("recommendations must be an iterable") from exc
    seen: set[str] = set()
    for item in items:
        if type(item) is not StrategyProbabilityRecommendationSafetyGateV2Input:
            raise ValueError(
                "recommendations must contain StrategyProbabilityRecommendationSafetyGateV2Input",
            )
        _require_hard_flags("input", item)
        if item.recommendation_id in seen:
            raise ValueError("recommendation_id values must be unique")
        seen.add(item.recommendation_id)
    return items


def _row_from_input(
    item: StrategyProbabilityRecommendationSafetyGateV2Input,
    *,
    config: StrategyProbabilityRecommendationSafetyGateV2Config,
    generated_at: datetime,
) -> StrategyProbabilityRecommendationSafetyGateV2Row:
    if item.observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    raw_edge = _quantize(item.estimated_probability - item.market_price)
    total_cost = _quantize(item.fee_probability_cost + item.slippage_probability_cost)
    cost_adjusted_edge = _quantize(raw_edge - total_cost)
    reason_codes = _row_reason_codes(
        item,
        cost_adjusted_edge=cost_adjusted_edge,
        config=config,
    )
    return StrategyProbabilityRecommendationSafetyGateV2Row(
        recommendation_id=item.recommendation_id,
        category=item.category,
        gate_status=_row_status(reason_codes),
        raw_probability_edge=raw_edge,
        total_probability_cost=total_cost,
        cost_adjusted_edge=cost_adjusted_edge,
        estimated_probability=item.estimated_probability,
        market_price=item.market_price,
        fee_probability_cost=item.fee_probability_cost,
        slippage_probability_cost=item.slippage_probability_cost,
        evidence_quality_score=item.evidence_quality_score,
        resolution_risk_score=item.resolution_risk_score,
        liquidity_exit_risk_score=item.liquidity_exit_risk_score,
        specialist_quorum_score=item.specialist_quorum_score,
        category_concentration_share=item.category_concentration_share,
        observed_at=item.observed_at,
        source_config_version=item.source_config_version,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    item: StrategyProbabilityRecommendationSafetyGateV2Input,
    *,
    cost_adjusted_edge: Decimal,
    config: StrategyProbabilityRecommendationSafetyGateV2Config,
) -> tuple[str, ...]:
    reasons = list(item.reason_codes)
    if cost_adjusted_edge < ZERO:
        reasons.append("safety_cost_adjusted_edge_negative_blocked")
    elif cost_adjusted_edge <= config.min_watch_cost_adjusted_edge:
        reasons.append("safety_cost_adjusted_edge_thin_watch")
    elif cost_adjusted_edge < config.min_pass_cost_adjusted_edge:
        reasons.append("safety_cost_adjusted_edge_thin_watch")

    evidence_block_threshold = _quantize(config.min_evidence_quality_score * Decimal("0.800000"))
    if item.evidence_quality_score < evidence_block_threshold:
        reasons.append("safety_evidence_quality_low_blocked")
    elif item.evidence_quality_score < config.min_evidence_quality_score:
        reasons.append("safety_evidence_quality_thin_watch")

    if item.resolution_risk_score > config.max_resolution_risk_score:
        reasons.append("safety_resolution_risk_high_blocked")

    if item.liquidity_exit_risk_score > config.max_liquidity_exit_risk_score:
        reasons.append("safety_liquidity_exit_risk_high_blocked")

    quorum_block_threshold = _quantize(config.min_specialist_quorum_score * Decimal("0.500000"))
    if item.specialist_quorum_score < quorum_block_threshold:
        reasons.append("safety_quorum_weak_watch")
    elif item.specialist_quorum_score < config.min_specialist_quorum_score:
        reasons.append("safety_quorum_weak_watch")

    if item.category_concentration_share > config.max_category_concentration_share:
        reasons.append("safety_category_concentration_excessive_blocked")

    if not any(reason.startswith("safety_") for reason in reasons):
        reasons.append("safety_gate_clear")
    return _require_reason_codes(tuple(reasons), require_nonempty=True)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_blocked") for reason_code in reason_codes):
        return "blocked"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _rollup_status(statuses: tuple[str, ...]) -> str:
    if any(status == "blocked" for status in statuses):
        return "blocked"
    if any(status == "watch" for status in statuses):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[StrategyProbabilityRecommendationSafetyGateV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("strategy_probability_safety_gate_empty",)
    status = _rollup_status(tuple(row.gate_status for row in rows))
    reason_codes = [f"strategy_probability_safety_gate_{'clear' if status == 'pass' else status}"]
    row_safety_reasons = frozenset(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code.startswith("safety_") and reason_code != "safety_gate_clear"
    )
    used: set[str] = set()

    def append_first(*candidates: str) -> None:
        for candidate in candidates:
            if candidate in row_safety_reasons:
                reason_codes.append(candidate)
                used.add(candidate)
                return

    append_first("safety_category_concentration_excessive_blocked")
    append_first(
        "safety_cost_adjusted_edge_thin_watch",
        "safety_cost_adjusted_edge_negative_blocked",
    )
    append_first(
        "safety_evidence_quality_low_blocked",
        "safety_evidence_quality_thin_watch",
    )
    append_first(
        "safety_liquidity_exit_risk_high_blocked",
    )
    append_first("safety_quorum_weak_watch")
    append_first("safety_resolution_risk_high_blocked")
    return tuple(reason_codes)


def _reason_code_counts(
    rows: tuple[StrategyProbabilityRecommendationSafetyGateV2Row, ...],
) -> tuple[StrategyProbabilityRecommendationSafetyGateV2ReasonCodeCount, ...]:
    if not rows:
        return ()
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    denominator = _count(len(rows))
    return tuple(
        StrategyProbabilityRecommendationSafetyGateV2ReasonCodeCount(
            reason_code=reason_code,
            count=count,
            recommendation_ratio=_ratio(count, denominator),
        )
        for count, reason_code in sorted(
            ((_count(count), reason_code) for reason_code, count in counter.items()),
            key=lambda item: (-item[0], item[1]),
        )
    )


def _row_sort_key(
    row: StrategyProbabilityRecommendationSafetyGateV2Row,
) -> tuple[Decimal, Decimal, str]:
    return (
        -STATUS_WEIGHT[row.gate_status],
        row.cost_adjusted_edge,
        row.recommendation_id,
    )


def _status_count(
    rows: tuple[StrategyProbabilityRecommendationSafetyGateV2Row, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.gate_status == status))


def _validate_row(row: StrategyProbabilityRecommendationSafetyGateV2Row) -> None:
    expected_raw_edge = _quantize(row.estimated_probability - row.market_price)
    if row.raw_probability_edge != expected_raw_edge:
        raise ValueError("raw_probability_edge must match probability less market price")
    expected_total_cost = _quantize(row.fee_probability_cost + row.slippage_probability_cost)
    if row.total_probability_cost != expected_total_cost:
        raise ValueError("total_probability_cost must match fee plus slippage cost")
    expected_cost_adjusted_edge = _quantize(row.raw_probability_edge - row.total_probability_cost)
    if row.cost_adjusted_edge != expected_cost_adjusted_edge:
        raise ValueError("cost_adjusted_edge must match raw edge less costs")
    if row.gate_status != _row_status(row.reason_codes):
        raise ValueError("gate_status must match reason_codes")


def _validate_report_status(report: StrategyProbabilityRecommendationSafetyGateV2Report) -> None:
    expected_status = _rollup_status(tuple(row.gate_status for row in report.rows))
    if report.status != expected_status:
        raise ValueError("status must match rows")
    if report.recommended_next_step != NEXT_STEP_BY_STATUS[report.status]:
        raise ValueError("recommended_next_step must match status")


def _validate_report_materialized_fields(
    report: StrategyProbabilityRecommendationSafetyGateV2Report,
) -> None:
    rows = report.rows
    expected_reason_counts = _reason_code_counts(rows)
    expected_reason_codes = _report_reason_codes(rows)
    checks = {
        "recommendation_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "blocked_count": _status_count(rows, "blocked"),
        "min_cost_adjusted_edge": _min_decimal(tuple(row.cost_adjusted_edge for row in rows)),
        "min_evidence_quality_score": _min_decimal(
            tuple(row.evidence_quality_score for row in rows),
        ),
        "max_resolution_risk_score": _max_decimal(
            tuple(row.resolution_risk_score for row in rows),
        ),
        "max_liquidity_exit_risk_score": _max_decimal(
            tuple(row.liquidity_exit_risk_score for row in rows),
        ),
        "min_specialist_quorum_score": _min_decimal(
            tuple(row.specialist_quorum_score for row in rows),
        ),
        "max_category_concentration_share": _max_decimal(
            tuple(row.category_concentration_share for row in rows),
        ),
    }
    for field_name, expected in checks.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != expected_reason_counts:
        raise ValueError("reason_code_counts must match rows")


def _require_rows(
    rows: tuple[StrategyProbabilityRecommendationSafetyGateV2Row, ...],
) -> tuple[StrategyProbabilityRecommendationSafetyGateV2Row, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not StrategyProbabilityRecommendationSafetyGateV2Row:
            raise ValueError("rows must contain StrategyProbabilityRecommendationSafetyGateV2Row")
        _require_hard_flags("row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted by status, edge, and recommendation_id")
    return normalized


def _require_reason_code_counts(
    rows: tuple[StrategyProbabilityRecommendationSafetyGateV2ReasonCodeCount, ...],
) -> tuple[StrategyProbabilityRecommendationSafetyGateV2ReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for row in normalized:
        if type(row) is not StrategyProbabilityRecommendationSafetyGateV2ReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain StrategyProbabilityRecommendationSafetyGateV2ReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", row)
    if normalized != tuple(
        sorted(normalized, key=lambda item: (-item.count, item.reason_code)),
    ):
        raise ValueError("reason_code_counts must be sorted by count and reason_code")
    if len({row.reason_code for row in normalized}) != len(normalized):
        raise ValueError("reason_code_counts reason_code values must be unique")
    return normalized


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    require_paper_only_flags(label, value)


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical non-empty string")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")
    _reject_unsafe_public_text(field_name, value)


def _require_reason_codes(
    reason_codes: tuple[str, ...],
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if require_nonempty and not normalized:
        raise ValueError("reason_codes must be non-empty")
    for reason_code in normalized:
        _require_public_string("reason_code", reason_code)
        if reason_code.lower() != reason_code:
            raise ValueError("reason_code must be lowercase")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    return tuple(
        sorted(
            normalized,
            key=lambda reason_code: (
                1 if reason_code.startswith("safety_") else 0,
                (
                    ROW_REASON_PRIORITY.index(reason_code)
                    if reason_code in ROW_REASON_PRIORITY
                    else len(ROW_REASON_PRIORITY)
                ),
                reason_code,
            ),
        ),
    )


def _require_report_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    normalized = _require_reason_codes(reason_codes, require_nonempty=True)
    return tuple(
        sorted(
            normalized,
            key=lambda reason_code: (
                0
                if reason_code.startswith("strategy_probability_safety_gate_")
                else 1,
                REPORT_REASON_PRIORITY.index(reason_code)
                if reason_code in REPORT_REASON_PRIORITY
                else len(REPORT_REASON_PRIORITY),
                reason_code,
            ),
        ),
    )


def _require_status(field_name: str, value: object) -> None:
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_signed_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < Decimal("-1.000000") or normalized > ONE:
        raise ValueError(f"{field_name} must be between -1 and 1")
    return normalized


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be non-negative")
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _count(value: int | Decimal) -> Decimal:
    if type(value) is Decimal:
        return _require_count_decimal("count", value)
    return _quantize(Decimal(value))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _min_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(min(values))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(max(values))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _derived_validation_digest(
    report: StrategyProbabilityRecommendationSafetyGateV2Report,
) -> str:
    payload = _json_ready(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be an object")
    return _payload_validation_digest(payload)


def _payload_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    canonical = json.dumps(
        digest_payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in HEX_CHARS for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) is bool:
        return value
    if type(value) is str:
        _reject_unsafe_public_text("payload", value)
        return value
    if type(value) in (int, float):
        raise ValueError("public numeric payload values must be Decimal strings")
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_text("payload key", key)
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_public_numeric_values(value: object) -> None:
    if type(value) in (int, float):
        raise ValueError("public numeric payload values must be Decimal strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_numeric_values(item)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_unsafe_public_text(f"{label} key", key)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public surface in {label}")
