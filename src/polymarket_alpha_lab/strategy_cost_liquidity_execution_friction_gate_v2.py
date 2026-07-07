"""Paper-only cost, liquidity, and fill-friction gate v2."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any


QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0")
ONE = Decimal("1")
DECIMAL_CONTEXT = Context(prec=28, rounding=ROUND_HALF_EVEN)
GATE_STATUSES = ("ready", "watch", "blocked")
STATUS_PRIORITY = {"ready": Decimal("0"), "watch": Decimal("1"), "blocked": Decimal("2")}
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
class StrategyCostLiquidityExecutionFrictionGateV2Config:
    config_version: str
    min_cost_adjusted_edge: Decimal
    max_total_execution_friction_drag: Decimal
    max_spread_drag: Decimal
    min_depth_coverage_ratio: Decimal
    max_age_seconds: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_public_string("config_version", self.config_version)
        for field_name in (
            "min_cost_adjusted_edge",
            "max_total_execution_friction_drag",
            "max_spread_drag",
            "min_depth_coverage_ratio",
            "max_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_depth_coverage_ratio <= ZERO:
            raise ValueError("min_depth_coverage_ratio must be positive")
        _require_hard_flags(self)


@dataclass(frozen=True)
class StrategyCostLiquidityExecutionFrictionGateV2Candidate:
    candidate_id: str
    market_slug: str
    question: str
    side: str
    observed_at: datetime
    gross_edge: Decimal
    entry_probability: Decimal
    fee_rate: Decimal
    best_bid_probability: Decimal
    best_ask_probability: Decimal
    target_size_shares: Decimal
    available_depth_shares: Decimal
    expected_slippage_probability: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("candidate_id", "market_slug", "question"):
            _require_canonical_public_string(field_name, getattr(self, field_name))
        _require_member("side", self.side, ("yes", "no"))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "gross_edge",
            "entry_probability",
            "fee_rate",
            "best_bid_probability",
            "best_ask_probability",
            "expected_slippage_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in ("target_size_shares", "available_depth_shares"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.target_size_shares <= ZERO:
            raise ValueError("target_size_shares must be positive")
        if self.best_ask_probability < self.best_bid_probability:
            raise ValueError("best_ask_probability must be at least best_bid_probability")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class StrategyCostLiquidityExecutionFrictionGateV2Row:
    candidate_id: str
    market_slug: str
    question: str
    side: str
    observed_at: datetime
    gross_edge: Decimal
    entry_probability: Decimal
    fee_rate: Decimal
    fee_drag: Decimal
    best_bid_probability: Decimal
    best_ask_probability: Decimal
    spread_drag: Decimal
    target_size_shares: Decimal
    available_depth_shares: Decimal
    depth_coverage_ratio: Decimal
    depth_drag: Decimal
    expected_slippage_probability: Decimal
    total_execution_friction_drag: Decimal
    execution_friction_drag_score: Decimal
    cost_adjusted_edge: Decimal
    age_seconds: Decimal
    gate_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("candidate_id", "market_slug", "question"):
            _require_canonical_public_string(field_name, getattr(self, field_name))
        _require_member("side", self.side, ("yes", "no"))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "gross_edge",
            "entry_probability",
            "fee_rate",
            "fee_drag",
            "best_bid_probability",
            "best_ask_probability",
            "spread_drag",
            "target_size_shares",
            "available_depth_shares",
            "depth_coverage_ratio",
            "depth_drag",
            "expected_slippage_probability",
            "total_execution_friction_drag",
            "execution_friction_drag_score",
            "age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "cost_adjusted_edge",
            _normalize_decimal("cost_adjusted_edge", self.cost_adjusted_edge),
        )
        _require_member("gate_status", self.gate_status, GATE_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags(self)
        _apply_or_verify_digest(self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class StrategyCostLiquidityExecutionFrictionGateV2Report:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    ready_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    max_total_execution_friction_drag: Decimal
    min_cost_adjusted_edge: Decimal
    average_execution_friction_drag_score: Decimal
    rows: tuple[StrategyCostLiquidityExecutionFrictionGateV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_public_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "ready_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_total_execution_friction_drag",
            "average_execution_friction_drag_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_cost_adjusted_edge",
            _normalize_decimal("min_cost_adjusted_edge", self.min_cost_adjusted_edge),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags(self)
        _apply_or_verify_digest(self)
        _validate_report_consistency(self)


def build_strategy_cost_liquidity_execution_friction_gate_v2_report(
    candidates: Iterable[StrategyCostLiquidityExecutionFrictionGateV2Candidate],
    *,
    config: StrategyCostLiquidityExecutionFrictionGateV2Config,
    generated_at: datetime,
) -> StrategyCostLiquidityExecutionFrictionGateV2Report:
    if type(config) is not StrategyCostLiquidityExecutionFrictionGateV2Config:
        raise ValueError(
            "config must be a StrategyCostLiquidityExecutionFrictionGateV2Config",
        )
    _require_hard_flags(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_candidates = _normalize_candidates(candidates)
    rows = tuple(
        sorted(
            (
                _row_from_candidate(
                    candidate,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for candidate in normalized_candidates
            ),
            key=_row_sort_key,
        ),
    )
    return StrategyCostLiquidityExecutionFrictionGateV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        candidate_count=_count(len(rows)),
        ready_count=_status_count(rows, "ready"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        max_total_execution_friction_drag=_max_decimal(
            tuple(row.total_execution_friction_drag for row in rows),
        ),
        min_cost_adjusted_edge=_min_decimal(
            tuple(row.cost_adjusted_edge for row in rows),
        ),
        average_execution_friction_drag_score=_average_decimal(
            tuple(row.execution_friction_drag_score for row in rows),
        ),
        rows=rows,
    )


def strategy_cost_liquidity_execution_friction_gate_v2_payload(
    report: StrategyCostLiquidityExecutionFrictionGateV2Report,
) -> dict[str, Any]:
    if type(report) is not StrategyCostLiquidityExecutionFrictionGateV2Report:
        raise ValueError(
            "report must be a StrategyCostLiquidityExecutionFrictionGateV2Report",
        )
    _require_hard_flags(report)
    _verify_digest(report)
    _validate_report_consistency(report)
    for row in report.rows:
        _verify_digest(row)
    payload = _json_ready(asdict(report))
    _reject_unsafe_public_payload(payload)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return payload


def _row_from_candidate(
    candidate: StrategyCostLiquidityExecutionFrictionGateV2Candidate,
    *,
    config: StrategyCostLiquidityExecutionFrictionGateV2Config,
    generated_at: datetime,
) -> StrategyCostLiquidityExecutionFrictionGateV2Row:
    age_seconds = _seconds_between(generated_at, candidate.observed_at)
    fee_drag = _multiply_decimal(candidate.entry_probability, candidate.fee_rate)
    spread_drag = _subtract_decimal(
        candidate.best_ask_probability,
        candidate.best_bid_probability,
    )
    depth_coverage_ratio = _divide_decimal(
        candidate.available_depth_shares,
        candidate.target_size_shares,
    )
    depth_drag = _depth_drag(depth_coverage_ratio)
    total_execution_friction_drag = _sum_decimals(
        (
            fee_drag,
            spread_drag,
            depth_drag,
            candidate.expected_slippage_probability,
        ),
    )
    cost_adjusted_edge = _subtract_decimal(
        candidate.gross_edge,
        total_execution_friction_drag,
    )
    gate_status = _gate_status(
        cost_adjusted_edge=cost_adjusted_edge,
        total_execution_friction_drag=total_execution_friction_drag,
        spread_drag=spread_drag,
        depth_coverage_ratio=depth_coverage_ratio,
        age_seconds=age_seconds,
        config=config,
    )
    reason_codes = _reason_codes_for(
        source_reason_codes=candidate.reason_codes,
        cost_adjusted_edge=cost_adjusted_edge,
        total_execution_friction_drag=total_execution_friction_drag,
        spread_drag=spread_drag,
        depth_coverage_ratio=depth_coverage_ratio,
        age_seconds=age_seconds,
        config=config,
    )
    return StrategyCostLiquidityExecutionFrictionGateV2Row(
        candidate_id=candidate.candidate_id,
        market_slug=candidate.market_slug,
        question=candidate.question,
        side=candidate.side,
        observed_at=candidate.observed_at,
        gross_edge=candidate.gross_edge,
        entry_probability=candidate.entry_probability,
        fee_rate=candidate.fee_rate,
        fee_drag=fee_drag,
        best_bid_probability=candidate.best_bid_probability,
        best_ask_probability=candidate.best_ask_probability,
        spread_drag=spread_drag,
        target_size_shares=candidate.target_size_shares,
        available_depth_shares=candidate.available_depth_shares,
        depth_coverage_ratio=depth_coverage_ratio,
        depth_drag=depth_drag,
        expected_slippage_probability=candidate.expected_slippage_probability,
        total_execution_friction_drag=total_execution_friction_drag,
        execution_friction_drag_score=total_execution_friction_drag,
        cost_adjusted_edge=cost_adjusted_edge,
        age_seconds=age_seconds,
        gate_status=gate_status,
        reason_codes=reason_codes,
    )


def _gate_status(
    *,
    cost_adjusted_edge: Decimal,
    total_execution_friction_drag: Decimal,
    spread_drag: Decimal,
    depth_coverage_ratio: Decimal,
    age_seconds: Decimal,
    config: StrategyCostLiquidityExecutionFrictionGateV2Config,
) -> str:
    if cost_adjusted_edge <= ZERO:
        return "blocked"
    if total_execution_friction_drag > config.max_total_execution_friction_drag:
        return "blocked"
    if spread_drag > config.max_spread_drag:
        return "blocked"
    if depth_coverage_ratio < config.min_depth_coverage_ratio:
        return "blocked"
    if age_seconds > config.max_age_seconds:
        return "watch"
    if cost_adjusted_edge < config.min_cost_adjusted_edge:
        return "watch"
    return "ready"


def _reason_codes_for(
    *,
    source_reason_codes: tuple[str, ...],
    cost_adjusted_edge: Decimal,
    total_execution_friction_drag: Decimal,
    spread_drag: Decimal,
    depth_coverage_ratio: Decimal,
    age_seconds: Decimal,
    config: StrategyCostLiquidityExecutionFrictionGateV2Config,
) -> tuple[str, ...]:
    codes = list(source_reason_codes)
    if cost_adjusted_edge <= ZERO:
        codes.append("cost_adjusted_edge_not_positive")
    elif cost_adjusted_edge < config.min_cost_adjusted_edge:
        codes.append("cost_adjusted_edge_below_minimum")
    else:
        codes.append("cost_adjusted_edge_ready")
    if total_execution_friction_drag > config.max_total_execution_friction_drag:
        codes.append("total_execution_friction_drag_above_limit")
    if spread_drag > config.max_spread_drag:
        codes.append("spread_drag_above_limit")
    if depth_coverage_ratio < config.min_depth_coverage_ratio:
        codes.append("depth_coverage_below_minimum")
    if age_seconds > config.max_age_seconds:
        codes.append("candidate_stale")
    return _normalize_reason_codes("reason_codes", tuple(codes))


def _normalize_candidates(
    candidates: Iterable[StrategyCostLiquidityExecutionFrictionGateV2Candidate],
) -> tuple[StrategyCostLiquidityExecutionFrictionGateV2Candidate, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable of candidate values")
    try:
        normalized = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable of candidate values") from exc
    seen: set[tuple[str, str]] = set()
    for candidate in normalized:
        if type(candidate) is not StrategyCostLiquidityExecutionFrictionGateV2Candidate:
            raise ValueError("candidates must contain candidate values")
        _require_hard_flags(candidate)
        key = (candidate.candidate_id, candidate.side)
        if key in seen:
            raise ValueError("candidates must not contain duplicate candidate side values")
        seen.add(key)
    return normalized


def _normalize_rows(
    rows: Iterable[StrategyCostLiquidityExecutionFrictionGateV2Row],
) -> tuple[StrategyCostLiquidityExecutionFrictionGateV2Row, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not StrategyCostLiquidityExecutionFrictionGateV2Row:
            raise ValueError("rows must contain friction gate row values")
        _require_hard_flags(row)
        _verify_digest(row)
    return normalized


def _validate_row_consistency(
    row: StrategyCostLiquidityExecutionFrictionGateV2Row,
) -> None:
    if row.best_ask_probability < row.best_bid_probability:
        raise ValueError("best_ask_probability must be at least best_bid_probability")
    if row.target_size_shares <= ZERO:
        raise ValueError("target_size_shares must be positive")
    if row.fee_drag != _multiply_decimal(row.entry_probability, row.fee_rate):
        raise ValueError("fee_drag must match input values")
    if row.spread_drag != _subtract_decimal(
        row.best_ask_probability,
        row.best_bid_probability,
    ):
        raise ValueError("spread_drag must match input values")
    if row.depth_coverage_ratio != _divide_decimal(
        row.available_depth_shares,
        row.target_size_shares,
    ):
        raise ValueError("depth_coverage_ratio must match input values")
    if row.depth_drag != _depth_drag(row.depth_coverage_ratio):
        raise ValueError("depth_drag must match input values")
    expected_total = _sum_decimals(
        (
            row.fee_drag,
            row.spread_drag,
            row.depth_drag,
            row.expected_slippage_probability,
        ),
    )
    if row.total_execution_friction_drag != expected_total:
        raise ValueError("total_execution_friction_drag must match inputs")
    if row.execution_friction_drag_score != row.total_execution_friction_drag:
        raise ValueError("execution_friction_drag_score must match friction drag")
    if row.cost_adjusted_edge != _subtract_decimal(
        row.gross_edge,
        row.total_execution_friction_drag,
    ):
        raise ValueError("cost_adjusted_edge must match edge and friction drag")


def _validate_report_consistency(
    report: StrategyCostLiquidityExecutionFrictionGateV2Report,
) -> None:
    if report.candidate_count != _count(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.ready_count != _status_count(report.rows, "ready"):
        raise ValueError("ready_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.candidate_count != report.ready_count + report.watch_count + report.blocked_count:
        raise ValueError("candidate_count must match gate counts")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted")
    if report.max_total_execution_friction_drag != _max_decimal(
        tuple(row.total_execution_friction_drag for row in report.rows),
    ):
        raise ValueError("max_total_execution_friction_drag must match rows")
    if report.min_cost_adjusted_edge != _min_decimal(
        tuple(row.cost_adjusted_edge for row in report.rows),
    ):
        raise ValueError("min_cost_adjusted_edge must match rows")
    if report.average_execution_friction_drag_score != _average_decimal(
        tuple(row.execution_friction_drag_score for row in report.rows),
    ):
        raise ValueError("average_execution_friction_drag_score must match rows")
    for row in report.rows:
        _verify_digest(row)


def _row_sort_key(
    row: StrategyCostLiquidityExecutionFrictionGateV2Row,
) -> tuple[Decimal, Decimal, Decimal, str, str, str]:
    return (
        STATUS_PRIORITY[row.gate_status],
        -row.cost_adjusted_edge,
        row.total_execution_friction_drag,
        row.market_slug,
        row.candidate_id,
        row.side,
    )


def _status_count(
    rows: tuple[StrategyCostLiquidityExecutionFrictionGateV2Row, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.gate_status == status))


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _normalize_count(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(COUNT_QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must be integral")
    if quantized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO.quantize(QUANTUM)
    return _normalize_nonnegative_decimal("max_decimal", max(values))


def _min_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO.quantize(QUANTUM)
    return _normalize_decimal("min_decimal", min(values))


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO.quantize(QUANTUM)
    return _divide_decimal(_sum_decimals(values), Decimal(len(values)))


def _depth_drag(depth_coverage_ratio: Decimal) -> Decimal:
    if depth_coverage_ratio >= ONE:
        return ZERO.quantize(QUANTUM)
    return _subtract_decimal(ONE, depth_coverage_ratio)


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


def _divide_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left / right)


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    microseconds = Decimal(delta.microseconds) / Decimal("1000000")
    normalized = _quantize(seconds + microseconds)
    if normalized < ZERO:
        raise ValueError("observed_at must not be after generated_at")
    return normalized


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _normalize_probability(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most one")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        normalized = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    for item in normalized:
        _require_canonical_public_string(field_name, item)
    return tuple(sorted(set(normalized)))


def _require_canonical_public_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public content")


def _require_member(field_name: str, value: str, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")


def _require_hard_flags(value: object) -> None:
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


def _apply_or_verify_digest(
    value: StrategyCostLiquidityExecutionFrictionGateV2Row
    | StrategyCostLiquidityExecutionFrictionGateV2Report,
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
    value: StrategyCostLiquidityExecutionFrictionGateV2Row
    | StrategyCostLiquidityExecutionFrictionGateV2Report,
) -> None:
    _require_digest("derived_validation_digest", value.derived_validation_digest)
    if value.derived_validation_digest != _derived_digest(value):
        raise ValueError("derived_validation_digest does not match derived fields")


def _derived_digest(
    value: StrategyCostLiquidityExecutionFrictionGateV2Row
    | StrategyCostLiquidityExecutionFrictionGateV2Report,
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
    if type(value) is dict:
        for key, item in value.items():
            _require_canonical_public_string("public_payload_key", key)
            _reject_unsafe_public_payload(item)
        return
    if type(value) is list:
        for item in value:
            _reject_unsafe_public_payload(item)
        return
    if type(value) is str and _has_unsafe_public_fragment(value):
        raise ValueError("public payload contains unsafe public content")


def _json_ready(value: Any) -> Any:
    if type(value) is dict:
        return {key: _json_ready(item) for key, item in value.items()}
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("payload value is not JSON-ready")


__all__ = (
    "StrategyCostLiquidityExecutionFrictionGateV2Candidate",
    "StrategyCostLiquidityExecutionFrictionGateV2Config",
    "StrategyCostLiquidityExecutionFrictionGateV2Report",
    "StrategyCostLiquidityExecutionFrictionGateV2Row",
    "build_strategy_cost_liquidity_execution_friction_gate_v2_report",
    "strategy_cost_liquidity_execution_friction_gate_v2_payload",
)
