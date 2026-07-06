"""Paper-only probability edge cost gate v2.

Pure in-memory Decimal arithmetic over probability-event candidates. The module
produces immutable reports and JSON-ready payloads only.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
DECIMAL_CONTEXT = Context(prec=28, rounding=ROUND_HALF_EVEN)
GATE_STATUSES = ("ready", "watch", "blocked")
RISK_LABELS = ("low_cost_risk", "medium_cost_risk", "high_cost_risk")
STATUS_PRIORITY = {"ready": 0, "watch": 1, "blocked": 2}
RISK_PRIORITY = {
    "low_cost_risk": 0,
    "medium_cost_risk": 1,
    "high_cost_risk": 2,
}
UNSAFE_PUBLIC_FRAGMENTS = (
    "li" "ve",
    "au" "th",
    "wal" "let",
    "or" "der",
    "net" "work",
    "data" "base",
    "per" "sist",
    "sig" "ning",
    "muta" "tion",
    "b" "uy",
    "se" "ll",
    "tr" "ade",
)


@dataclass(frozen=True)
class StrategyProbabilityEdgeCostGateV2Config:
    config_version: str
    min_cost_adjusted_edge: Decimal
    min_liquidity_usdc: Decimal
    min_depth_shares: Decimal
    max_candidate_age_seconds: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_public_string("config_version", self.config_version)
        for field_name in (
            "min_cost_adjusted_edge",
            "min_liquidity_usdc",
            "min_depth_shares",
            "max_candidate_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_safety_flags(self)


@dataclass(frozen=True)
class StrategyProbabilityEdgeCostGateV2Candidate:
    candidate_id: str
    market_slug: str
    question: str
    side: str
    observed_at: datetime
    forecast_probability: Decimal
    market_probability: Decimal
    taker_fee_rate: Decimal
    spread_probability: Decimal
    expected_slippage_probability: Decimal
    settlement_delay_days: Decimal
    settlement_delay_penalty_rate: Decimal
    available_liquidity_usdc: Decimal
    available_depth_shares: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "candidate_id",
            "market_slug",
            "question",
        ):
            _require_canonical_public_string(field_name, getattr(self, field_name))
        if self.side not in ("yes", "no"):
            raise ValueError("side must be yes or no")
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "forecast_probability",
            "market_probability",
            "taker_fee_rate",
            "spread_probability",
            "expected_slippage_probability",
            "settlement_delay_penalty_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "settlement_delay_days",
            "available_liquidity_usdc",
            "available_depth_shares",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_safety_flags(self)


@dataclass(frozen=True)
class StrategyProbabilityEdgeCostGateV2Row:
    candidate_id: str
    market_slug: str
    question: str
    side: str
    observed_at: datetime
    forecast_probability: Decimal
    market_probability: Decimal
    gross_probability_edge: Decimal
    taker_fee_rate: Decimal
    taker_fee_cost_probability: Decimal
    spread_cost_probability: Decimal
    expected_slippage_probability: Decimal
    settlement_delay_days: Decimal
    settlement_delay_penalty_rate: Decimal
    settlement_delay_cost_probability: Decimal
    total_cost_probability: Decimal
    cost_adjusted_edge: Decimal
    age_seconds: Decimal
    available_liquidity_usdc: Decimal
    min_liquidity_usdc: Decimal
    liquidity_coverage_ratio: Decimal | None
    available_depth_shares: Decimal
    min_depth_shares: Decimal
    depth_coverage_ratio: Decimal | None
    gate_status: str
    risk_label: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "candidate_id",
            "market_slug",
            "question",
        ):
            _require_canonical_public_string(field_name, getattr(self, field_name))
        if self.side not in ("yes", "no"):
            raise ValueError("side must be yes or no")
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "forecast_probability",
            "market_probability",
            "taker_fee_rate",
            "spread_cost_probability",
            "expected_slippage_probability",
            "settlement_delay_penalty_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "gross_probability_edge",
            "cost_adjusted_edge",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "taker_fee_cost_probability",
            "settlement_delay_days",
            "settlement_delay_cost_probability",
            "total_cost_probability",
            "age_seconds",
            "available_liquidity_usdc",
            "min_liquidity_usdc",
            "available_depth_shares",
            "min_depth_shares",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "liquidity_coverage_ratio",
            _normalize_optional_nonnegative_decimal(
                "liquidity_coverage_ratio",
                self.liquidity_coverage_ratio,
            ),
        )
        object.__setattr__(
            self,
            "depth_coverage_ratio",
            _normalize_optional_nonnegative_decimal(
                "depth_coverage_ratio",
                self.depth_coverage_ratio,
            ),
        )
        if self.gate_status not in GATE_STATUSES:
            raise ValueError("gate_status must be a known gate status")
        if self.risk_label not in RISK_LABELS:
            raise ValueError("risk_label must be a known risk label")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_safety_flags(self)
        _apply_or_verify_digest(self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class StrategyProbabilityEdgeCostGateV2Report:
    generated_at: datetime
    config_version: str
    candidate_count: int
    row_count: int
    ready_count: int
    watch_count: int
    blocked_count: int
    first_observed_at: datetime | None
    latest_observed_at: datetime | None
    rows: tuple[StrategyProbabilityEdgeCostGateV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_public_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "row_count",
            "ready_count",
            "watch_count",
            "blocked_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "first_observed_at",
            _as_optional_utc("first_observed_at", self.first_observed_at),
        )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_optional_utc("latest_observed_at", self.latest_observed_at),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_safety_flags(self)
        _apply_or_verify_digest(self)
        _validate_report_consistency(self)


def build_strategy_probability_edge_cost_gate_v2_report(
    candidates: Iterable[StrategyProbabilityEdgeCostGateV2Candidate],
    *,
    config: StrategyProbabilityEdgeCostGateV2Config,
    generated_at: datetime,
) -> StrategyProbabilityEdgeCostGateV2Report:
    if type(config) is not StrategyProbabilityEdgeCostGateV2Config:
        raise ValueError("config must be a StrategyProbabilityEdgeCostGateV2Config")
    generated_at_utc = _as_utc("generated_at", generated_at)
    _require_safety_flags(config)

    normalized_candidates = _normalize_candidates(candidates)
    rows = tuple(
        sorted(
            (
                _row_from_candidate(
                    value,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for value in normalized_candidates
            ),
            key=_row_sort_key,
        ),
    )
    observed_times = tuple(row.observed_at for row in rows)
    return StrategyProbabilityEdgeCostGateV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        candidate_count=len(normalized_candidates),
        row_count=len(rows),
        ready_count=_status_count(rows, "ready"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        first_observed_at=min(observed_times) if observed_times else None,
        latest_observed_at=max(observed_times) if observed_times else None,
        rows=rows,
    )


def strategy_probability_edge_cost_gate_v2_payload(
    report: StrategyProbabilityEdgeCostGateV2Report,
) -> dict[str, Any]:
    if type(report) is not StrategyProbabilityEdgeCostGateV2Report:
        raise ValueError("report must be a StrategyProbabilityEdgeCostGateV2Report")
    _require_safety_flags(report)
    _verify_report_integrity(report)
    payload = _json_ready(asdict(report))
    _reject_unsafe_public_payload(payload)
    return payload


def _row_from_candidate(
    value: StrategyProbabilityEdgeCostGateV2Candidate,
    *,
    config: StrategyProbabilityEdgeCostGateV2Config,
    generated_at: datetime,
) -> StrategyProbabilityEdgeCostGateV2Row:
    observed_at = _as_utc("observed_at", value.observed_at)
    if observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    gross_probability_edge = _subtract_decimal(
        value.forecast_probability,
        value.market_probability,
    )
    taker_fee_cost_probability = _multiply_decimal(
        value.market_probability,
        value.taker_fee_rate,
    )
    settlement_delay_cost_probability = _multiply_decimal(
        value.settlement_delay_days,
        value.settlement_delay_penalty_rate,
    )
    total_cost_probability = _sum_decimals(
        (
            taker_fee_cost_probability,
            value.spread_probability,
            value.expected_slippage_probability,
            settlement_delay_cost_probability,
        ),
    )
    cost_adjusted_edge = _subtract_decimal(
        gross_probability_edge,
        total_cost_probability,
    )
    age_seconds = _seconds_between(generated_at, observed_at)
    liquidity_coverage_ratio = _optional_ratio(
        value.available_liquidity_usdc,
        config.min_liquidity_usdc,
    )
    depth_coverage_ratio = _optional_ratio(
        value.available_depth_shares,
        config.min_depth_shares,
    )
    gate_status = _status_for(
        cost_adjusted_edge=cost_adjusted_edge,
        min_cost_adjusted_edge=config.min_cost_adjusted_edge,
        age_seconds=age_seconds,
        max_candidate_age_seconds=config.max_candidate_age_seconds,
        available_liquidity_usdc=value.available_liquidity_usdc,
        min_liquidity_usdc=config.min_liquidity_usdc,
        available_depth_shares=value.available_depth_shares,
        min_depth_shares=config.min_depth_shares,
    )
    risk_label = _risk_label_for(gate_status)
    reason_codes = _reason_codes_for(
        source_reason_codes=value.reason_codes,
        cost_adjusted_edge=cost_adjusted_edge,
        min_cost_adjusted_edge=config.min_cost_adjusted_edge,
        age_seconds=age_seconds,
        max_candidate_age_seconds=config.max_candidate_age_seconds,
        available_liquidity_usdc=value.available_liquidity_usdc,
        min_liquidity_usdc=config.min_liquidity_usdc,
        available_depth_shares=value.available_depth_shares,
        min_depth_shares=config.min_depth_shares,
    )

    return StrategyProbabilityEdgeCostGateV2Row(
        candidate_id=value.candidate_id,
        market_slug=value.market_slug,
        question=value.question,
        side=value.side,
        observed_at=observed_at,
        forecast_probability=value.forecast_probability,
        market_probability=value.market_probability,
        gross_probability_edge=gross_probability_edge,
        taker_fee_rate=value.taker_fee_rate,
        taker_fee_cost_probability=taker_fee_cost_probability,
        spread_cost_probability=value.spread_probability,
        expected_slippage_probability=value.expected_slippage_probability,
        settlement_delay_days=value.settlement_delay_days,
        settlement_delay_penalty_rate=value.settlement_delay_penalty_rate,
        settlement_delay_cost_probability=settlement_delay_cost_probability,
        total_cost_probability=total_cost_probability,
        cost_adjusted_edge=cost_adjusted_edge,
        age_seconds=age_seconds,
        available_liquidity_usdc=value.available_liquidity_usdc,
        min_liquidity_usdc=config.min_liquidity_usdc,
        liquidity_coverage_ratio=liquidity_coverage_ratio,
        available_depth_shares=value.available_depth_shares,
        min_depth_shares=config.min_depth_shares,
        depth_coverage_ratio=depth_coverage_ratio,
        gate_status=gate_status,
        risk_label=risk_label,
        reason_codes=reason_codes,
    )


def _status_for(
    *,
    cost_adjusted_edge: Decimal,
    min_cost_adjusted_edge: Decimal,
    age_seconds: Decimal,
    max_candidate_age_seconds: Decimal,
    available_liquidity_usdc: Decimal,
    min_liquidity_usdc: Decimal,
    available_depth_shares: Decimal,
    min_depth_shares: Decimal,
) -> str:
    if cost_adjusted_edge <= ZERO:
        return "blocked"
    if available_liquidity_usdc < min_liquidity_usdc:
        return "blocked"
    if available_depth_shares < min_depth_shares:
        return "blocked"
    if age_seconds > max_candidate_age_seconds:
        return "watch"
    if cost_adjusted_edge < min_cost_adjusted_edge:
        return "watch"
    return "ready"


def _risk_label_for(gate_status: str) -> str:
    if gate_status == "blocked":
        return "high_cost_risk"
    if gate_status == "watch":
        return "medium_cost_risk"
    return "low_cost_risk"


def _reason_codes_for(
    *,
    source_reason_codes: tuple[str, ...],
    cost_adjusted_edge: Decimal,
    min_cost_adjusted_edge: Decimal,
    age_seconds: Decimal,
    max_candidate_age_seconds: Decimal,
    available_liquidity_usdc: Decimal,
    min_liquidity_usdc: Decimal,
    available_depth_shares: Decimal,
    min_depth_shares: Decimal,
) -> tuple[str, ...]:
    edge_codes = (
        ("edge_not_positive_after_costs",)
        if cost_adjusted_edge <= ZERO
        else (
            ("edge_below_minimum",)
            if cost_adjusted_edge < min_cost_adjusted_edge
            else ("cost_adjusted_edge_ready",)
        )
    )
    age_codes = ("candidate_stale",) if age_seconds > max_candidate_age_seconds else ()
    liquidity_codes = (
        ("liquidity_below_minimum",)
        if available_liquidity_usdc < min_liquidity_usdc
        else ()
    )
    depth_codes = (
        ("depth_below_minimum",)
        if available_depth_shares < min_depth_shares
        else ()
    )
    return _normalize_reason_codes(
        (
            *source_reason_codes,
            *edge_codes,
            *age_codes,
            *liquidity_codes,
            *depth_codes,
        ),
    )


def _row_sort_key(
    row: StrategyProbabilityEdgeCostGateV2Row,
) -> tuple[int, Decimal, int, Decimal, Decimal, Decimal, str, str, str]:
    return (
        STATUS_PRIORITY[row.gate_status],
        -row.cost_adjusted_edge,
        RISK_PRIORITY[row.risk_label],
        row.age_seconds,
        -(row.liquidity_coverage_ratio if row.liquidity_coverage_ratio is not None else ZERO),
        -(row.depth_coverage_ratio if row.depth_coverage_ratio is not None else ZERO),
        row.market_slug,
        row.candidate_id,
        row.side,
    )


def _status_count(rows: tuple[StrategyProbabilityEdgeCostGateV2Row, ...], status: str) -> int:
    return sum(1 for row in rows if row.gate_status == status)


def _normalize_candidates(
    candidates: Iterable[StrategyProbabilityEdgeCostGateV2Candidate],
) -> tuple[StrategyProbabilityEdgeCostGateV2Candidate, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError(
            "candidates must be an iterable of StrategyProbabilityEdgeCostGateV2Candidate values",
        )
    try:
        normalized = tuple(candidates)
    except TypeError as exc:
        raise ValueError(
            "candidates must be an iterable of StrategyProbabilityEdgeCostGateV2Candidate values",
        ) from exc
    for value in normalized:
        if type(value) is not StrategyProbabilityEdgeCostGateV2Candidate:
            raise ValueError(
                "candidates must contain only StrategyProbabilityEdgeCostGateV2Candidate values",
            )
        _require_safety_flags(value)
    return normalized


def _normalize_rows(
    rows: Iterable[StrategyProbabilityEdgeCostGateV2Row],
) -> tuple[StrategyProbabilityEdgeCostGateV2Row, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not StrategyProbabilityEdgeCostGateV2Row:
            raise ValueError("rows must contain StrategyProbabilityEdgeCostGateV2Row values")
        _require_safety_flags(row)
        _verify_digest(row)
    return normalized


def _validate_row_consistency(row: StrategyProbabilityEdgeCostGateV2Row) -> None:
    expected_gross_probability_edge = _subtract_decimal(
        row.forecast_probability,
        row.market_probability,
    )
    if row.gross_probability_edge != expected_gross_probability_edge:
        raise ValueError("gross_probability_edge does not match probabilities")
    expected_taker_fee_cost_probability = _multiply_decimal(
        row.market_probability,
        row.taker_fee_rate,
    )
    if row.taker_fee_cost_probability != expected_taker_fee_cost_probability:
        raise ValueError("taker_fee_cost_probability does not match inputs")
    expected_settlement_delay_cost_probability = _multiply_decimal(
        row.settlement_delay_days,
        row.settlement_delay_penalty_rate,
    )
    if row.settlement_delay_cost_probability != expected_settlement_delay_cost_probability:
        raise ValueError("settlement_delay_cost_probability does not match inputs")
    expected_total_cost_probability = _sum_decimals(
        (
            row.taker_fee_cost_probability,
            row.spread_cost_probability,
            row.expected_slippage_probability,
            row.settlement_delay_cost_probability,
        ),
    )
    if row.total_cost_probability != expected_total_cost_probability:
        raise ValueError("total_cost_probability does not match costs")
    expected_cost_adjusted_edge = _subtract_decimal(
        row.gross_probability_edge,
        row.total_cost_probability,
    )
    if row.cost_adjusted_edge != expected_cost_adjusted_edge:
        raise ValueError("cost_adjusted_edge does not match edge and costs")
    expected_liquidity_ratio = _optional_ratio(
        row.available_liquidity_usdc,
        row.min_liquidity_usdc,
    )
    if row.liquidity_coverage_ratio != expected_liquidity_ratio:
        raise ValueError("liquidity_coverage_ratio does not match inputs")
    expected_depth_ratio = _optional_ratio(
        row.available_depth_shares,
        row.min_depth_shares,
    )
    if row.depth_coverage_ratio != expected_depth_ratio:
        raise ValueError("depth_coverage_ratio does not match inputs")
    expected_status = _status_for(
        cost_adjusted_edge=row.cost_adjusted_edge,
        min_cost_adjusted_edge=_infer_min_edge(row),
        age_seconds=row.age_seconds,
        max_candidate_age_seconds=row.age_seconds if row.gate_status != "ready" else row.age_seconds,
        available_liquidity_usdc=row.available_liquidity_usdc,
        min_liquidity_usdc=row.min_liquidity_usdc,
        available_depth_shares=row.available_depth_shares,
        min_depth_shares=row.min_depth_shares,
    )
    if row.gate_status == "ready" and expected_status != "ready":
        raise ValueError("gate_status does not match row thresholds")
    if row.risk_label != _risk_label_for(row.gate_status):
        raise ValueError("risk_label does not match gate_status")


def _infer_min_edge(row: StrategyProbabilityEdgeCostGateV2Row) -> Decimal:
    if row.gate_status == "ready":
        return row.cost_adjusted_edge
    return _add_decimal(row.cost_adjusted_edge, QUANTUM)


def _validate_report_consistency(report: StrategyProbabilityEdgeCostGateV2Report) -> None:
    if report.row_count != len(report.rows):
        raise ValueError("row_count must match rows")
    if report.candidate_count != len(report.rows):
        raise ValueError("candidate_count must match rows")
    if report.ready_count != _status_count(report.rows, "ready"):
        raise ValueError("ready_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if tuple(sorted(report.rows, key=_row_sort_key)) != report.rows:
        raise ValueError("rows must be sorted by gate status and edge")
    observed_times = tuple(row.observed_at for row in report.rows)
    expected_first = min(observed_times) if observed_times else None
    expected_latest = max(observed_times) if observed_times else None
    if report.first_observed_at != expected_first:
        raise ValueError("first_observed_at must match rows")
    if report.latest_observed_at != expected_latest:
        raise ValueError("latest_observed_at must match rows")
    for row in report.rows:
        _verify_digest(row)


def _verify_report_integrity(report: StrategyProbabilityEdgeCostGateV2Report) -> None:
    _validate_report_consistency(report)
    _verify_digest(report)
    for row in report.rows:
        _verify_digest(row)


def _sum_decimals(values: tuple[Decimal, ...]) -> Decimal:
    total = ZERO
    for value in values:
        total = _add_decimal(total, value)
    return total


def _add_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left + right)


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left - right)


def _multiply_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left * right)


def _optional_ratio(numerator: Decimal, denominator: Decimal) -> Decimal | None:
    if denominator == ZERO:
        return None
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    microseconds = Decimal(delta.microseconds) / Decimal("1000000")
    return _quantize(seconds + microseconds)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _normalize_probability(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most one")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_optional_nonnegative_decimal(
    field_name: str,
    value: Decimal | None,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_decimal(field_name, value)


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    for reason_code in normalized:
        _require_canonical_public_string("reason_codes", reason_code)
    return tuple(sorted(set(normalized)))


def _require_canonical_public_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public content")


def _require_nonnegative_int(field_name: str, value: int) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_safety_flags(value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only") is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly") is not True:
        raise ValueError("readonly must be True")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _apply_or_verify_digest(
    value: StrategyProbabilityEdgeCostGateV2Row | StrategyProbabilityEdgeCostGateV2Report,
) -> None:
    expected = _derived_digest(value)
    provided = value.derived_validation_digest
    if provided == "":
        object.__setattr__(value, "derived_validation_digest", expected)
        return
    _require_digest("derived_validation_digest", provided)
    if provided != expected:
        raise ValueError("derived_validation_digest does not match derived fields")


def _verify_digest(
    value: StrategyProbabilityEdgeCostGateV2Row | StrategyProbabilityEdgeCostGateV2Report,
) -> None:
    _require_digest("derived_validation_digest", value.derived_validation_digest)
    if value.derived_validation_digest != _derived_digest(value):
        raise ValueError("derived_validation_digest does not match derived fields")


def _derived_digest(
    value: StrategyProbabilityEdgeCostGateV2Row | StrategyProbabilityEdgeCostGateV2Report,
) -> str:
    digest_input = asdict(value)
    digest_input.pop("derived_validation_digest", None)
    payload = _json_ready(digest_input)
    encoded = dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _require_digest(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    for character in value:
        if character not in "0123456789abcdef":
            raise ValueError(f"{field_name} must be a sha256 hex digest")


def _has_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _reject_unsafe_public_payload(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _require_canonical_public_string("public_payload_key", key)
            _reject_unsafe_public_payload(item)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(item)
    elif isinstance(value, str) and _has_unsafe_public_fragment(value):
        raise ValueError("public payload contains unsafe public content")


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, datetime):
        return value.isoformat()
    if value is None or type(value) in (str, int, bool):
        return value
    raise ValueError("payload value is not JSON-ready")


__all__ = (
    "StrategyProbabilityEdgeCostGateV2Candidate",
    "StrategyProbabilityEdgeCostGateV2Config",
    "StrategyProbabilityEdgeCostGateV2Report",
    "StrategyProbabilityEdgeCostGateV2Row",
    "build_strategy_probability_edge_cost_gate_v2_report",
    "strategy_probability_edge_cost_gate_v2_payload",
)
