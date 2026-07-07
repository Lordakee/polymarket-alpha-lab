"""Paper-only research liquidity quality gate.

This module is a pure reducer for human research screening. It produces a
redacted, deterministic quality summary and does not persist, fetch, trade, or
construct order instructions.
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
GATE_STATUSES = ("pass", "watch", "block")
STATUS_PRIORITY = {"block": Decimal("0"), "watch": Decimal("1"), "pass": Decimal("2")}
ROW_REASON_ORDER = (
    "depth_coverage_block",
    "spread_block",
    "cost_block",
    "slippage_risk_block",
    "depth_coverage_watch",
    "spread_watch",
    "cost_watch",
    "slippage_risk_watch",
    "liquidity_quality_pass",
)
UNSAFE_PUBLIC_FRAGMENTS = (
    "raw",
    "candidate_id",
    "market_id",
    "market_slug",
    "question",
    "source",
    "ref",
    "url",
    "text",
    "dsn",
    "table",
    "token",
    "wallet",
    "auth",
    "order",
    "trade",
    "position",
    "buy",
    "sell",
    "recommendation",
)


@dataclass(frozen=True)
class ResearchLiquidityQualityGateConfig:
    config_version: str
    max_pass_spread: Decimal
    max_watch_spread: Decimal
    max_pass_total_cost: Decimal
    max_watch_total_cost: Decimal
    min_pass_depth_coverage_ratio: Decimal
    min_watch_depth_coverage_ratio: Decimal
    max_pass_slippage_risk_score: Decimal
    max_watch_slippage_risk_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_public_string("config_version", self.config_version)
        for field_name in (
            "max_pass_spread",
            "max_watch_spread",
            "max_pass_total_cost",
            "max_watch_total_cost",
            "min_pass_depth_coverage_ratio",
            "min_watch_depth_coverage_ratio",
            "max_pass_slippage_risk_score",
            "max_watch_slippage_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.max_pass_spread > self.max_watch_spread:
            raise ValueError("max_pass_spread must be at most max_watch_spread")
        if self.max_pass_total_cost > self.max_watch_total_cost:
            raise ValueError("max_pass_total_cost must be at most max_watch_total_cost")
        if self.max_pass_slippage_risk_score > self.max_watch_slippage_risk_score:
            raise ValueError(
                "max_pass_slippage_risk_score must be at most "
                "max_watch_slippage_risk_score",
            )
        if self.min_watch_depth_coverage_ratio <= ZERO:
            raise ValueError("min_watch_depth_coverage_ratio must be positive")
        if self.min_pass_depth_coverage_ratio < self.min_watch_depth_coverage_ratio:
            raise ValueError(
                "min_pass_depth_coverage_ratio must be at least "
                "min_watch_depth_coverage_ratio",
            )
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchLiquidityQualityGateCandidate:
    raw_candidate_id: str
    raw_market_id: str
    raw_market_slug: str
    raw_question: str
    source_reference: str
    source_url: str
    source_text: str
    observed_at: datetime
    target_size: Decimal
    available_depth: Decimal
    spread: Decimal
    fee_cost: Decimal
    impact_cost: Decimal
    slippage_cost: Decimal
    slippage_risk_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "raw_candidate_id",
            "raw_market_id",
            "raw_market_slug",
            "raw_question",
            "source_reference",
            "source_url",
            "source_text",
        ):
            _require_raw_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "target_size",
            "available_depth",
            "spread",
            "fee_cost",
            "impact_cost",
            "slippage_cost",
            "slippage_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.target_size <= ZERO:
            raise ValueError("target_size must be positive")
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchLiquidityQualityGateRow:
    review_rank: Decimal
    status: str
    reason_codes: tuple[str, ...]
    depth_coverage_band: str
    depth_coverage_ratio: Decimal
    spread: Decimal
    fee_cost: Decimal
    impact_cost: Decimal
    slippage_cost: Decimal
    total_cost: Decimal
    slippage_risk_score: Decimal
    slippage_risk_band: str
    liquidity_quality_score: Decimal
    observed_age_seconds: Decimal = ZERO
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "review_rank", _normalize_count("review_rank", self.review_rank))
        _require_member("status", self.status, GATE_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_member("depth_coverage_band", self.depth_coverage_band, ("deep", "adequate", "thin"))
        for field_name in (
            "depth_coverage_ratio",
            "spread",
            "fee_cost",
            "impact_cost",
            "slippage_cost",
            "total_cost",
            "slippage_risk_score",
            "liquidity_quality_score",
            "observed_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.liquidity_quality_score > ONE:
            raise ValueError("liquidity_quality_score must be at most one")
        _require_member("slippage_risk_band", self.slippage_risk_band, ("low", "elevated", "high"))
        _require_hard_flags(self)
        _validate_row_consistency(self)
        _apply_or_verify_digest(self)


@dataclass(frozen=True)
class ResearchLiquidityQualityGateReport:
    generated_at: datetime
    config_version: str
    status: str
    reason_codes: tuple[str, ...]
    item_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_spread: Decimal
    max_total_cost: Decimal
    min_depth_coverage_ratio: Decimal
    max_slippage_risk_score: Decimal
    average_liquidity_quality_score: Decimal
    rows: tuple[ResearchLiquidityQualityGateRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_public_string("config_version", self.config_version)
        _require_member("status", self.status, GATE_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        for field_name in ("item_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(self, field_name, _normalize_count(field_name, getattr(self, field_name)))
        for field_name in (
            "max_spread",
            "max_total_cost",
            "min_depth_coverage_ratio",
            "max_slippage_risk_score",
            "average_liquidity_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.average_liquidity_quality_score > ONE:
            raise ValueError("average_liquidity_quality_score must be at most one")
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags(self)
        _validate_report_consistency(self)
        _apply_or_verify_digest(self)


def build_research_liquidity_quality_gate_report(
    items: Iterable[ResearchLiquidityQualityGateCandidate],
    *,
    config: ResearchLiquidityQualityGateConfig,
    generated_at: datetime,
) -> ResearchLiquidityQualityGateReport:
    if type(config) is not ResearchLiquidityQualityGateConfig:
        raise ValueError("config must be a ResearchLiquidityQualityGateConfig")
    _require_hard_flags(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    candidates = _normalize_candidates(items)
    row_inputs = tuple(
        sorted(
            (
                _row_input_from_candidate(
                    candidate,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for candidate in candidates
            ),
            key=_row_input_sort_key,
        ),
    )
    rows = tuple(
        _row_from_input(row_input, review_rank=_count(index))
        for index, row_input in enumerate(row_inputs, start=1)
    )
    return ResearchLiquidityQualityGateReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        item_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        max_spread=_max_decimal(tuple(row.spread for row in rows)),
        max_total_cost=_max_decimal(tuple(row.total_cost for row in rows)),
        min_depth_coverage_ratio=_min_decimal(
            tuple(row.depth_coverage_ratio for row in rows),
        ),
        max_slippage_risk_score=_max_decimal(
            tuple(row.slippage_risk_score for row in rows),
        ),
        average_liquidity_quality_score=_average_decimal(
            tuple(row.liquidity_quality_score for row in rows),
        ),
        rows=rows,
    )


def research_liquidity_quality_gate_payload(
    report: ResearchLiquidityQualityGateReport,
) -> dict[str, Any]:
    if type(report) is not ResearchLiquidityQualityGateReport:
        raise ValueError("report must be a ResearchLiquidityQualityGateReport")
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


@dataclass(frozen=True)
class _RowInput:
    private_sort_key: tuple[str, str]
    observed_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    depth_coverage_band: str
    depth_coverage_ratio: Decimal
    spread: Decimal
    fee_cost: Decimal
    impact_cost: Decimal
    slippage_cost: Decimal
    total_cost: Decimal
    slippage_risk_score: Decimal
    slippage_risk_band: str
    liquidity_quality_score: Decimal


def _row_input_from_candidate(
    candidate: ResearchLiquidityQualityGateCandidate,
    *,
    config: ResearchLiquidityQualityGateConfig,
    generated_at: datetime,
) -> _RowInput:
    depth_coverage_ratio = _divide_decimal(candidate.available_depth, candidate.target_size)
    total_cost = _sum_decimals(
        (candidate.fee_cost, candidate.impact_cost, candidate.slippage_cost),
    )
    reason_codes = _row_reason_codes(
        depth_coverage_ratio=depth_coverage_ratio,
        spread=candidate.spread,
        total_cost=total_cost,
        slippage_risk_score=candidate.slippage_risk_score,
        config=config,
    )
    status = _row_status(reason_codes)
    return _RowInput(
        private_sort_key=(candidate.raw_market_id, candidate.raw_candidate_id),
        observed_age_seconds=_seconds_between(generated_at, candidate.observed_at),
        status=status,
        reason_codes=reason_codes,
        depth_coverage_band=_depth_band(depth_coverage_ratio, config),
        depth_coverage_ratio=depth_coverage_ratio,
        spread=candidate.spread,
        fee_cost=candidate.fee_cost,
        impact_cost=candidate.impact_cost,
        slippage_cost=candidate.slippage_cost,
        total_cost=total_cost,
        slippage_risk_score=candidate.slippage_risk_score,
        slippage_risk_band=_slippage_band(candidate.slippage_risk_score, config),
        liquidity_quality_score=_quality_score(
            depth_coverage_ratio=depth_coverage_ratio,
            spread=candidate.spread,
            total_cost=total_cost,
            slippage_risk_score=candidate.slippage_risk_score,
        ),
    )


def _row_from_input(row_input: _RowInput, *, review_rank: Decimal) -> ResearchLiquidityQualityGateRow:
    return ResearchLiquidityQualityGateRow(
        review_rank=review_rank,
        status=row_input.status,
        reason_codes=row_input.reason_codes,
        depth_coverage_band=row_input.depth_coverage_band,
        depth_coverage_ratio=row_input.depth_coverage_ratio,
        spread=row_input.spread,
        fee_cost=row_input.fee_cost,
        impact_cost=row_input.impact_cost,
        slippage_cost=row_input.slippage_cost,
        total_cost=row_input.total_cost,
        slippage_risk_score=row_input.slippage_risk_score,
        slippage_risk_band=row_input.slippage_risk_band,
        liquidity_quality_score=row_input.liquidity_quality_score,
        observed_age_seconds=row_input.observed_age_seconds,
    )


def _row_reason_codes(
    *,
    depth_coverage_ratio: Decimal,
    spread: Decimal,
    total_cost: Decimal,
    slippage_risk_score: Decimal,
    config: ResearchLiquidityQualityGateConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if depth_coverage_ratio < config.min_watch_depth_coverage_ratio:
        reason_codes.append("depth_coverage_block")
    elif depth_coverage_ratio < config.min_pass_depth_coverage_ratio:
        reason_codes.append("depth_coverage_watch")
    if spread > config.max_watch_spread:
        reason_codes.append("spread_block")
    elif spread > config.max_pass_spread:
        reason_codes.append("spread_watch")
    if total_cost > config.max_watch_total_cost:
        reason_codes.append("cost_block")
    elif total_cost > config.max_pass_total_cost:
        reason_codes.append("cost_watch")
    if slippage_risk_score > config.max_watch_slippage_risk_score:
        reason_codes.append("slippage_risk_block")
    elif slippage_risk_score > config.max_pass_slippage_risk_score:
        reason_codes.append("slippage_risk_watch")
    if not reason_codes:
        reason_codes.append("liquidity_quality_pass")
    return tuple(reason_codes)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchLiquidityQualityGateRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(rows: tuple[ResearchLiquidityQualityGateRow, ...]) -> tuple[str, ...]:
    status = _report_status(rows)
    reason_codes = [f"liquidity_quality_gate_{status}"]
    for candidate_code in ROW_REASON_ORDER:
        if any(candidate_code in row.reason_codes for row in rows):
            reason_codes.append(candidate_code)
    return tuple(reason_codes)


def _depth_band(
    depth_coverage_ratio: Decimal,
    config: ResearchLiquidityQualityGateConfig,
) -> str:
    if depth_coverage_ratio >= config.min_pass_depth_coverage_ratio:
        return "deep"
    if depth_coverage_ratio >= config.min_watch_depth_coverage_ratio:
        return "adequate"
    return "thin"


def _slippage_band(
    slippage_risk_score: Decimal,
    config: ResearchLiquidityQualityGateConfig,
) -> str:
    if slippage_risk_score <= config.max_pass_slippage_risk_score:
        return "low"
    if slippage_risk_score <= config.max_watch_slippage_risk_score:
        return "elevated"
    return "high"


def _quality_score(
    *,
    depth_coverage_ratio: Decimal,
    spread: Decimal,
    total_cost: Decimal,
    slippage_risk_score: Decimal,
) -> Decimal:
    depth_shortfall = ZERO if depth_coverage_ratio >= ONE else _subtract_decimal(ONE, depth_coverage_ratio)
    drag = _sum_decimals((depth_shortfall, spread, total_cost, slippage_risk_score))
    if drag >= ONE:
        return ZERO.quantize(QUANTUM)
    return _subtract_decimal(ONE, drag)


def _row_input_sort_key(row_input: _RowInput) -> tuple[Decimal, Decimal, Decimal, tuple[str, str]]:
    return (
        STATUS_PRIORITY[row_input.status],
        -row_input.liquidity_quality_score,
        row_input.total_cost,
        row_input.private_sort_key,
    )


def _row_sort_key(row: ResearchLiquidityQualityGateRow) -> tuple[Decimal, Decimal]:
    return STATUS_PRIORITY[row.status], row.review_rank


def _normalize_candidates(
    items: Iterable[ResearchLiquidityQualityGateCandidate],
) -> tuple[ResearchLiquidityQualityGateCandidate, ...]:
    if isinstance(items, (str, bytes)):
        raise ValueError("items must be an iterable of candidates")
    try:
        normalized = tuple(items)
    except TypeError as exc:
        raise ValueError("items must be an iterable of candidates") from exc
    seen: set[str] = set()
    for item in normalized:
        if type(item) is not ResearchLiquidityQualityGateCandidate:
            raise ValueError("items must contain ResearchLiquidityQualityGateCandidate values")
        _require_hard_flags(item)
        if item.raw_candidate_id in seen:
            raise ValueError("items must not contain duplicate raw_candidate_id values")
        seen.add(item.raw_candidate_id)
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchLiquidityQualityGateRow],
) -> tuple[ResearchLiquidityQualityGateRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not ResearchLiquidityQualityGateRow:
            raise ValueError("rows must contain ResearchLiquidityQualityGateRow values")
        _require_hard_flags(row)
        _verify_digest(row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted by status and review_rank")
    return normalized


def _validate_row_consistency(row: ResearchLiquidityQualityGateRow) -> None:
    if row.total_cost != _sum_decimals((row.fee_cost, row.impact_cost, row.slippage_cost)):
        raise ValueError("total_cost must match component costs")
    expected_status = _row_status(row.reason_codes)
    if row.status != expected_status:
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and row.reason_codes != ("liquidity_quality_pass",):
        raise ValueError("reason_codes must match pass status")
    if row.depth_coverage_band == "thin" and "depth_coverage_block" not in row.reason_codes:
        raise ValueError("depth_coverage_band must match reason_codes")
    if row.slippage_risk_band == "high" and "slippage_risk_block" not in row.reason_codes:
        raise ValueError("slippage_risk_band must match reason_codes")


def _validate_report_consistency(report: ResearchLiquidityQualityGateReport) -> None:
    if report.item_count != _count(len(report.rows)):
        raise ValueError("item_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    expected_rank = Decimal("1")
    for row in report.rows:
        if row.review_rank != _count(int(expected_rank)):
            raise ValueError("review_rank must be sequential")
        expected_rank += Decimal("1")
        _verify_digest(row)
    if report.max_spread != _max_decimal(tuple(row.spread for row in report.rows)):
        raise ValueError("max_spread must match rows")
    if report.max_total_cost != _max_decimal(tuple(row.total_cost for row in report.rows)):
        raise ValueError("max_total_cost must match rows")
    if report.min_depth_coverage_ratio != _min_decimal(
        tuple(row.depth_coverage_ratio for row in report.rows),
    ):
        raise ValueError("min_depth_coverage_ratio must match rows")
    if report.max_slippage_risk_score != _max_decimal(
        tuple(row.slippage_risk_score for row in report.rows),
    ):
        raise ValueError("max_slippage_risk_score must match rows")
    if report.average_liquidity_quality_score != _average_decimal(
        tuple(row.liquidity_quality_score for row in report.rows),
    ):
        raise ValueError("average_liquidity_quality_score must match rows")


def _status_count(rows: tuple[ResearchLiquidityQualityGateRow, ...], status: str) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO.quantize(QUANTUM)
    return _normalize_nonnegative_decimal("max_decimal", max(values))


def _min_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO.quantize(QUANTUM)
    return _normalize_nonnegative_decimal("min_decimal", min(values))


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO.quantize(QUANTUM)
    return _divide_decimal(_sum_decimals(values), Decimal(len(values)))


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


def _normalize_count(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
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
    return normalized


def _require_raw_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


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


def _apply_or_verify_digest(value: ResearchLiquidityQualityGateRow | ResearchLiquidityQualityGateReport) -> None:
    expected = _derived_digest(value)
    provided = value.derived_validation_digest
    if provided == "":
        object.__setattr__(value, "derived_validation_digest", expected)
        return
    _require_digest("derived_validation_digest", provided)
    if provided != expected:
        raise ValueError("derived_validation_digest does not match derived fields")


def _verify_digest(value: ResearchLiquidityQualityGateRow | ResearchLiquidityQualityGateReport) -> None:
    _require_digest("derived_validation_digest", value.derived_validation_digest)
    if value.derived_validation_digest != _derived_digest(value):
        raise ValueError("derived_validation_digest does not match derived fields")


def _derived_digest(value: ResearchLiquidityQualityGateRow | ResearchLiquidityQualityGateReport) -> str:
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
    "ResearchLiquidityQualityGateCandidate",
    "ResearchLiquidityQualityGateConfig",
    "ResearchLiquidityQualityGateReport",
    "ResearchLiquidityQualityGateRow",
    "build_research_liquidity_quality_gate_report",
    "research_liquidity_quality_gate_payload",
)
