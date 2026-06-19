"""Pure paper-only readiness reducer for recommendation gates."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext


__all__ = (
    "PaperRecommendationReadinessConfig",
    "PaperRecommendationReadinessGateInput",
    "PaperRecommendationReadinessRow",
    "PaperRecommendationReadinessReport",
    "build_paper_recommendation_readiness_report",
)


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64)
SIDES = ("yes", "no")
GATE_STATUSES = ("pass", "watch", "blocked")
READINESS_STATUSES = ("ready", "watch", "blocked")
READINESS_STATUS_RANK = {"ready": 0, "watch": 1, "blocked": 2}


@dataclass(frozen=True)
class PaperRecommendationReadinessConfig:
    config_version: str
    min_pass_net_probability_edge: Decimal
    max_watch_gate_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "min_pass_net_probability_edge",
            _normalize_probability(
                "min_pass_net_probability_edge",
                self.min_pass_net_probability_edge,
            ),
        )
        _require_nonnegative_int("max_watch_gate_count", self.max_watch_gate_count)
        _require_hard_flags(self)


@dataclass(frozen=True)
class PaperRecommendationReadinessGateInput:
    market_slug: str
    side: str
    gate_name: str
    gate_status: str
    adjusted_net_probability_edge: Decimal
    cost_per_share: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        _require_side("side", self.side)
        _require_canonical_string("gate_name", self.gate_name)
        _require_gate_status("gate_status", self.gate_status)
        object.__setattr__(
            self,
            "adjusted_net_probability_edge",
            _normalize_decimal(
                "adjusted_net_probability_edge",
                self.adjusted_net_probability_edge,
            ),
        )
        object.__setattr__(
            self,
            "cost_per_share",
            _normalize_nonnegative_decimal("cost_per_share", self.cost_per_share),
        )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_hard_flags(self)


@dataclass(frozen=True)
class PaperRecommendationReadinessRow:
    market_slug: str
    side: str
    readiness_status: str
    gate_count: int
    pass_gate_count: int
    watch_gate_count: int
    blocked_gate_count: int
    adjusted_net_probability_edge: Decimal
    total_cost_per_share: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        _require_side("side", self.side)
        _require_readiness_status("readiness_status", self.readiness_status)
        for field_name in (
            "gate_count",
            "pass_gate_count",
            "watch_gate_count",
            "blocked_gate_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "adjusted_net_probability_edge",
            _normalize_decimal(
                "adjusted_net_probability_edge",
                self.adjusted_net_probability_edge,
            ),
        )
        object.__setattr__(
            self,
            "total_cost_per_share",
            _normalize_nonnegative_decimal(
                "total_cost_per_share",
                self.total_cost_per_share,
            ),
        )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags(self)


@dataclass(frozen=True)
class PaperRecommendationReadinessReport:
    generated_at: datetime
    config_version: str
    input_count: int
    row_count: int
    ready_count: int
    watch_count: int
    blocked_count: int
    top_adjusted_net_probability_edge: Decimal
    total_cost_per_share: Decimal
    rows: tuple[PaperRecommendationReadinessRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "input_count",
            "row_count",
            "ready_count",
            "watch_count",
            "blocked_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "top_adjusted_net_probability_edge",
            _normalize_decimal(
                "top_adjusted_net_probability_edge",
                self.top_adjusted_net_probability_edge,
            ),
        )
        object.__setattr__(
            self,
            "total_cost_per_share",
            _normalize_nonnegative_decimal(
                "total_cost_per_share",
                self.total_cost_per_share,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_hard_flags(self)


def build_paper_recommendation_readiness_report(
    gate_inputs: Iterable[PaperRecommendationReadinessGateInput],
    *,
    config: PaperRecommendationReadinessConfig,
    generated_at: datetime,
) -> PaperRecommendationReadinessReport:
    if type(config) is not PaperRecommendationReadinessConfig:
        raise ValueError("config must be a PaperRecommendationReadinessConfig")
    generated_at = _as_utc(generated_at)
    _require_hard_flags(config)
    inputs = _normalize_gate_inputs(gate_inputs)
    if not inputs:
        raise ValueError("gate_inputs must contain at least one value")

    rows = tuple(
        sorted(
            (
                _row_from_group(group, config=config)
                for group in _group_inputs(inputs).values()
            ),
            key=_row_sort_key,
        ),
    )
    return PaperRecommendationReadinessReport(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=len(inputs),
        row_count=len(rows),
        ready_count=_readiness_count(rows, "ready"),
        watch_count=_readiness_count(rows, "watch"),
        blocked_count=_readiness_count(rows, "blocked"),
        top_adjusted_net_probability_edge=_top_adjusted_net_probability_edge(rows),
        total_cost_per_share=_total_cost_per_share(rows),
        rows=rows,
    )


def _row_from_group(
    values: tuple[PaperRecommendationReadinessGateInput, ...],
    *,
    config: PaperRecommendationReadinessConfig,
) -> PaperRecommendationReadinessRow:
    first = values[0]
    pass_gate_count = _gate_status_count(values, "pass")
    watch_gate_count = _gate_status_count(values, "watch")
    blocked_gate_count = _gate_status_count(values, "blocked")
    adjusted_edge = min(value.adjusted_net_probability_edge for value in values)
    total_cost = _sum_decimal(value.cost_per_share for value in values)
    readiness_status = _readiness_status(
        adjusted_edge=adjusted_edge,
        watch_gate_count=watch_gate_count,
        blocked_gate_count=blocked_gate_count,
        config=config,
    )
    reason_codes = _row_reason_codes(
        values=values,
        readiness_status=readiness_status,
        adjusted_edge=adjusted_edge,
        watch_gate_count=watch_gate_count,
        blocked_gate_count=blocked_gate_count,
        config=config,
    )
    return PaperRecommendationReadinessRow(
        market_slug=first.market_slug,
        side=first.side,
        readiness_status=readiness_status,
        gate_count=len(values),
        pass_gate_count=pass_gate_count,
        watch_gate_count=watch_gate_count,
        blocked_gate_count=blocked_gate_count,
        adjusted_net_probability_edge=adjusted_edge,
        total_cost_per_share=total_cost,
        reason_codes=reason_codes,
    )


def _readiness_status(
    *,
    adjusted_edge: Decimal,
    watch_gate_count: int,
    blocked_gate_count: int,
    config: PaperRecommendationReadinessConfig,
) -> str:
    if blocked_gate_count > 0:
        return "blocked"
    if watch_gate_count > config.max_watch_gate_count:
        return "blocked"
    if watch_gate_count > 0:
        return "watch"
    if adjusted_edge < config.min_pass_net_probability_edge:
        return "watch"
    return "ready"


def _row_reason_codes(
    *,
    values: tuple[PaperRecommendationReadinessGateInput, ...],
    readiness_status: str,
    adjusted_edge: Decimal,
    watch_gate_count: int,
    blocked_gate_count: int,
    config: PaperRecommendationReadinessConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    for value in values:
        reason_codes.extend(value.reason_codes)
    if blocked_gate_count > 0:
        reason_codes.append("readiness_blocked_gate")
    if watch_gate_count > config.max_watch_gate_count:
        reason_codes.append("readiness_watch_gate_limit_exceeded")
    elif watch_gate_count > 0:
        reason_codes.append("readiness_watch_gate")
    if readiness_status == "watch" and adjusted_edge < config.min_pass_net_probability_edge:
        reason_codes.append("below_readiness_edge_threshold")
    return _normalize_reason_codes(tuple(reason_codes))


def _group_inputs(
    values: tuple[PaperRecommendationReadinessGateInput, ...],
) -> dict[tuple[str, str], tuple[PaperRecommendationReadinessGateInput, ...]]:
    groups: dict[tuple[str, str], list[PaperRecommendationReadinessGateInput]] = {}
    for value in values:
        groups.setdefault((value.market_slug, value.side), []).append(value)
    return {key: tuple(group_values) for key, group_values in groups.items()}


def _normalize_gate_inputs(
    values: Iterable[PaperRecommendationReadinessGateInput],
) -> tuple[PaperRecommendationReadinessGateInput, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("gate_inputs must be an iterable")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError("gate_inputs must be an iterable") from exc
    for value in normalized:
        if type(value) is not PaperRecommendationReadinessGateInput:
            raise ValueError(
                "gate_inputs must contain PaperRecommendationReadinessGateInput values",
            )
        _require_hard_flags(value)
    return normalized


def _normalize_rows(
    values: Iterable[PaperRecommendationReadinessRow],
) -> tuple[PaperRecommendationReadinessRow, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(values)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in rows:
        if type(row) is not PaperRecommendationReadinessRow:
            raise ValueError("rows must contain PaperRecommendationReadinessRow values")
        _require_hard_flags(row)
    return rows


def _validate_row_consistency(row: PaperRecommendationReadinessRow) -> None:
    if row.gate_count != (
        row.pass_gate_count + row.watch_gate_count + row.blocked_gate_count
    ):
        raise ValueError("gate_count must match gate status counts")
    if row.gate_count <= 0:
        raise ValueError("gate_count must be positive")
    if row.blocked_gate_count > 0 and row.readiness_status != "blocked":
        raise ValueError("readiness_status must block blocked gates")


def _validate_report_consistency(report: PaperRecommendationReadinessReport) -> None:
    if report.row_count != len(report.rows):
        raise ValueError("row_count must match rows")
    if report.ready_count != _readiness_count(report.rows, "ready"):
        raise ValueError("ready_count must match rows")
    if report.watch_count != _readiness_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _readiness_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.row_count != report.ready_count + report.watch_count + report.blocked_count:
        raise ValueError("row_count must match readiness counts")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted")
    if report.top_adjusted_net_probability_edge != _top_adjusted_net_probability_edge(
        report.rows,
    ):
        raise ValueError("top_adjusted_net_probability_edge must match rows")
    if report.total_cost_per_share != _total_cost_per_share(report.rows):
        raise ValueError("total_cost_per_share must match rows")


def _row_sort_key(
    row: PaperRecommendationReadinessRow,
) -> tuple[int, Decimal, Decimal, str, str]:
    return (
        READINESS_STATUS_RANK[row.readiness_status],
        -row.adjusted_net_probability_edge,
        row.market_slug,
        row.side,
        row.total_cost_per_share,
    )


def _gate_status_count(
    values: tuple[PaperRecommendationReadinessGateInput, ...],
    gate_status: str,
) -> int:
    return sum(1 for value in values if value.gate_status == gate_status)


def _readiness_count(
    rows: tuple[PaperRecommendationReadinessRow, ...],
    readiness_status: str,
) -> int:
    return sum(1 for row in rows if row.readiness_status == readiness_status)


def _top_adjusted_net_probability_edge(
    rows: tuple[PaperRecommendationReadinessRow, ...],
) -> Decimal:
    if not rows:
        return _quantize(ZERO)
    return max(row.adjusted_net_probability_edge for row in rows)


def _total_cost_per_share(
    rows: tuple[PaperRecommendationReadinessRow, ...],
) -> Decimal:
    return _sum_decimal(row.total_cost_per_share for row in rows)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        with localcontext(DECIMAL_CONTEXT):
            total = _quantize(total + value)
    return total


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    if not normalized:
        raise ValueError("reason_codes must contain at least one value")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must not contain duplicates")
    for reason_code in normalized:
        _require_canonical_string("reason_codes", reason_code)
    return tuple(sorted(normalized))


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_side(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SIDES:
        raise ValueError(f"{field_name} must be yes or no")


def _require_gate_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in GATE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_readiness_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in READINESS_STATUSES:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


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
    normalized = _quantize(value)
    if normalized != value:
        raise ValueError(f"{field_name} must be quantized to 0.000001")
    return normalized


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _require_hard_flags(value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError("readonly must be True")


def _as_utc(value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
