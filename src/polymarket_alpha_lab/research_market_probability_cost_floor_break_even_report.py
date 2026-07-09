"""Report-only probability cost floor break-even research checks."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP, localcontext
import hashlib
import json
import re
from typing import Any, Iterable, Mapping


DEFAULT_RESEARCH_MARKET_PROBABILITY_COST_FLOOR_BREAK_EVEN_CONFIG_VERSION = (
    "research-market-probability-cost-floor-break-even-report-v1"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
STATUSES = ("pass", "watch", "block")
_STATUSES = frozenset(STATUSES)
_PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_UNSAFE_PUBLIC_TERMS = (
    "candidate_id",
    "raw_candidate",
    "market_id",
    "market_slug",
    "question",
    "source_url",
    "source_text",
    "dsn",
    "table_name",
    "token",
    "wallet",
    "order",
    "trade",
    "sizing",
    "recommendation",
    "auth",
    "network",
    "live",
)
_REASON_CODE_SEQUENCE = (
    "break_even_probability_above_one",
    "probability_floor_below_break_even",
    "thin_probability_margin",
    "probability_cost_floor_break_even_pass",
)
_STATUS_SORT = {"block": 0, "watch": 1, "pass": 2}


@dataclass(frozen=True)
class ResearchMarketProbabilityCostFloorBreakEvenConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_PROBABILITY_COST_FLOOR_BREAK_EVEN_CONFIG_VERSION
    )
    watch_margin_threshold: Decimal = Decimal("0.010000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketProbabilityCostFloorBreakEvenConfig does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketProbabilityCostFloorBreakEvenConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchMarketProbabilityCostFloorBreakEvenConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_PROBABILITY_COST_FLOOR_BREAK_EVEN_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "watch_margin_threshold",
            _require_nonnegative_probability_delta(
                "watch_margin_threshold",
                self.watch_margin_threshold,
            ),
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchMarketProbabilityCostFloorBreakEvenInput:
    market_probability: Decimal
    research_probability_floor: Decimal
    fee_probability_cost: Decimal = _ZERO
    slippage_probability_cost: Decimal = _ZERO
    impact_probability_cost: Decimal = _ZERO
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketProbabilityCostFloorBreakEvenInput does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketProbabilityCostFloorBreakEvenInput:
            raise ValueError(
                "input must be exactly ResearchMarketProbabilityCostFloorBreakEvenInput",
            )
        for field_name in ("market_probability", "research_probability_floor"):
            object.__setattr__(
                self,
                field_name,
                _require_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "fee_probability_cost",
            "slippage_probability_cost",
            "impact_probability_cost",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_probability_delta(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        _validate_total_probability_cost(self)
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchMarketProbabilityCostFloorBreakEvenRow:
    market_probability: Decimal
    research_probability_floor: Decimal
    fee_probability_cost: Decimal
    slippage_probability_cost: Decimal
    impact_probability_cost: Decimal
    total_probability_cost: Decimal
    break_even_probability: Decimal
    break_even_margin: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketProbabilityCostFloorBreakEvenRow does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketProbabilityCostFloorBreakEvenRow:
            raise ValueError(
                "row must be exactly ResearchMarketProbabilityCostFloorBreakEvenRow",
            )
        for field_name in ("market_probability", "research_probability_floor"):
            object.__setattr__(
                self,
                field_name,
                _require_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "fee_probability_cost",
            "slippage_probability_cost",
            "impact_probability_cost",
            "total_probability_cost",
            "break_even_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_probability_delta(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "break_even_margin",
            _require_probability_delta(
                "break_even_margin",
                self.break_even_margin,
            ),
        )
        _require_member("status", self.status, _STATUSES)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchMarketProbabilityCostFloorBreakEvenReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketProbabilityCostFloorBreakEvenReasonCodeCount does not "
            "support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketProbabilityCostFloorBreakEvenReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchMarketProbabilityCostFloorBreakEvenReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        _require_hard_flags("reason code count", self)
        _reject_unsafe_public_payload("reason code count", self)


@dataclass(frozen=True)
class ResearchMarketProbabilityCostFloorBreakEvenReport:
    generated_at: datetime
    config_version: str
    report_status: str
    case_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    below_break_even_count: Decimal
    impossible_break_even_count: Decimal
    min_break_even_margin: Decimal
    max_total_probability_cost: Decimal
    rows: tuple[ResearchMarketProbabilityCostFloorBreakEvenRow, ...]
    reason_code_counts: tuple[
        ResearchMarketProbabilityCostFloorBreakEvenReasonCodeCount,
        ...,
    ]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketProbabilityCostFloorBreakEvenReport does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketProbabilityCostFloorBreakEvenReport:
            raise ValueError(
                "report must be exactly "
                "ResearchMarketProbabilityCostFloorBreakEvenReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_PROBABILITY_COST_FLOOR_BREAK_EVEN_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_member("report_status", self.report_status, _STATUSES)
        for field_name in (
            "case_count",
            "pass_count",
            "watch_count",
            "block_count",
            "below_break_even_count",
            "impossible_break_even_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_break_even_margin",
            _require_probability_delta(
                "min_break_even_margin",
                self.min_break_even_margin,
            ),
        )
        object.__setattr__(
            self,
            "max_total_probability_cost",
            _require_nonnegative_probability_delta(
                "max_total_probability_cost",
                self.max_total_probability_cost,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
            return
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report fields")

    @property
    def payload(self) -> dict[str, Any]:
        payload = _json_ready(asdict(self))
        _reject_unsafe_public_payload(
            "ResearchMarketProbabilityCostFloorBreakEvenReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        return payload


def build_research_market_probability_cost_floor_break_even_report(
    rows: Iterable[ResearchMarketProbabilityCostFloorBreakEvenInput],
    *,
    generated_at: datetime,
    config: ResearchMarketProbabilityCostFloorBreakEvenConfig | None = None,
) -> ResearchMarketProbabilityCostFloorBreakEvenReport:
    """Build a deterministic report-only probability floor break-even snapshot."""

    if config is None:
        config = ResearchMarketProbabilityCostFloorBreakEvenConfig()
    if type(config) is not ResearchMarketProbabilityCostFloorBreakEvenConfig:
        raise ValueError(
            "config must be a ResearchMarketProbabilityCostFloorBreakEvenConfig",
        )
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(rows)
    report_rows = tuple(
        sorted(
            (_row_for_input(item, config) for item in normalized_inputs),
            key=_row_sort_key,
        ),
    )
    reason_code_counts = _reason_code_counts(report_rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "report_status": _report_status(report_rows),
        "case_count": _decimal_count(len(report_rows)),
        "pass_count": _status_count(report_rows, "pass"),
        "watch_count": _status_count(report_rows, "watch"),
        "block_count": _status_count(report_rows, "block"),
        "below_break_even_count": _reason_count(
            report_rows,
            "probability_floor_below_break_even",
        ),
        "impossible_break_even_count": _reason_count(
            report_rows,
            "break_even_probability_above_one",
        ),
        "min_break_even_margin": min(
            (row.break_even_margin for row in report_rows),
            default=_ZERO,
        ),
        "max_total_probability_cost": max(
            (row.total_probability_cost for row in report_rows),
            default=_ZERO,
        ),
        "rows": report_rows,
        "reason_code_counts": reason_code_counts,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchMarketProbabilityCostFloorBreakEvenReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def _row_for_input(
    item: ResearchMarketProbabilityCostFloorBreakEvenInput,
    config: ResearchMarketProbabilityCostFloorBreakEvenConfig,
) -> ResearchMarketProbabilityCostFloorBreakEvenRow:
    total_probability_cost = _total_probability_cost(item)
    break_even_probability = _quantize(item.market_probability + total_probability_cost)
    break_even_margin = _quantize(item.research_probability_floor - break_even_probability)
    reason_codes = _row_reason_codes(
        break_even_probability=break_even_probability,
        break_even_margin=break_even_margin,
        config=config,
    )
    return ResearchMarketProbabilityCostFloorBreakEvenRow(
        market_probability=item.market_probability,
        research_probability_floor=item.research_probability_floor,
        fee_probability_cost=item.fee_probability_cost,
        slippage_probability_cost=item.slippage_probability_cost,
        impact_probability_cost=item.impact_probability_cost,
        total_probability_cost=total_probability_cost,
        break_even_probability=break_even_probability,
        break_even_margin=break_even_margin,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    break_even_probability: Decimal,
    break_even_margin: Decimal,
    config: ResearchMarketProbabilityCostFloorBreakEvenConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if break_even_probability > _ONE:
        reason_codes.append("break_even_probability_above_one")
    if break_even_margin < _ZERO:
        reason_codes.append("probability_floor_below_break_even")
    if not reason_codes and break_even_margin <= config.watch_margin_threshold:
        reason_codes.append("thin_probability_margin")
    if not reason_codes:
        reason_codes.append("probability_cost_floor_break_even_pass")
    return _normalize_reason_codes(reason_codes)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if (
        "break_even_probability_above_one" in reason_codes
        or "probability_floor_below_break_even" in reason_codes
    ):
        return "block"
    if "thin_probability_margin" in reason_codes:
        return "watch"
    return "pass"


def _report_status(
    rows: tuple[ResearchMarketProbabilityCostFloorBreakEvenRow, ...],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _total_probability_cost(
    item: ResearchMarketProbabilityCostFloorBreakEvenInput
    | ResearchMarketProbabilityCostFloorBreakEvenRow,
) -> Decimal:
    with localcontext() as context:
        context.prec = 64
        return _quantize(
            item.fee_probability_cost
            + item.slippage_probability_cost
            + item.impact_probability_cost,
        )


def _validate_total_probability_cost(
    item: ResearchMarketProbabilityCostFloorBreakEvenInput
    | ResearchMarketProbabilityCostFloorBreakEvenRow,
) -> None:
    total_probability_cost = _total_probability_cost(item)
    if total_probability_cost > _ONE:
        raise ValueError("total_probability_cost must not exceed one")


def _validate_row_consistency(
    row: ResearchMarketProbabilityCostFloorBreakEvenRow,
) -> None:
    total_probability_cost = _total_probability_cost(row)
    if row.total_probability_cost != total_probability_cost:
        raise ValueError("total_probability_cost must match input costs")
    if row.break_even_probability != _quantize(
        row.market_probability + row.total_probability_cost,
    ):
        raise ValueError("break_even_probability must match market probability plus costs")
    if row.break_even_margin != _quantize(
        row.research_probability_floor - row.break_even_probability,
    ):
        raise ValueError("break_even_margin must match probability floor less break-even")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    expected_block_reasons: list[str] = []
    if row.break_even_probability > _ONE:
        expected_block_reasons.append("break_even_probability_above_one")
    if row.break_even_margin < _ZERO:
        expected_block_reasons.append("probability_floor_below_break_even")
    if expected_block_reasons:
        if row.reason_codes != tuple(expected_block_reasons):
            raise ValueError("reason_codes must match break-even fields")
        return
    if any(
        reason_code in row.reason_codes
        for reason_code in (
            "break_even_probability_above_one",
            "probability_floor_below_break_even",
        )
    ):
        raise ValueError("reason_codes must match break-even fields")
    if (
        row.reason_codes == ("probability_cost_floor_break_even_pass",)
        and row.break_even_margin <= _ZERO
    ):
        raise ValueError("reason_codes must match break-even fields")


def _validate_report_consistency(
    report: ResearchMarketProbabilityCostFloorBreakEvenReport,
) -> None:
    rows = report.rows
    if report.case_count != _decimal_count(len(rows)):
        raise ValueError("case_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.below_break_even_count != _reason_count(
        rows,
        "probability_floor_below_break_even",
    ):
        raise ValueError("below_break_even_count must match rows")
    if report.impossible_break_even_count != _reason_count(
        rows,
        "break_even_probability_above_one",
    ):
        raise ValueError("impossible_break_even_count must match rows")
    if report.min_break_even_margin != min(
        (row.break_even_margin for row in rows),
        default=_ZERO,
    ):
        raise ValueError("min_break_even_margin must match rows")
    if report.max_total_probability_cost != max(
        (row.total_probability_cost for row in rows),
        default=_ZERO,
    ):
        raise ValueError("max_total_probability_cost must match rows")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _normalize_inputs(
    value: Iterable[ResearchMarketProbabilityCostFloorBreakEvenInput],
) -> tuple[ResearchMarketProbabilityCostFloorBreakEvenInput, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable of break-even inputs")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rows must be an iterable of break-even inputs") from exc
    for row in rows:
        if type(row) is not ResearchMarketProbabilityCostFloorBreakEvenInput:
            raise ValueError(
                "rows must contain ResearchMarketProbabilityCostFloorBreakEvenInput",
            )
        _require_hard_flags("input", row)
    return tuple(sorted(rows, key=_input_sort_key))


def _normalize_rows(
    value: Iterable[ResearchMarketProbabilityCostFloorBreakEvenRow],
) -> tuple[ResearchMarketProbabilityCostFloorBreakEvenRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable of break-even rows")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rows must be an iterable of break-even rows") from exc
    for row in rows:
        if type(row) is not ResearchMarketProbabilityCostFloorBreakEvenRow:
            raise ValueError(
                "rows must contain ResearchMarketProbabilityCostFloorBreakEvenRow",
            )
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted deterministically")
    return rows


def _normalize_reason_code_counts(
    value: Iterable[ResearchMarketProbabilityCostFloorBreakEvenReasonCodeCount],
) -> tuple[ResearchMarketProbabilityCostFloorBreakEvenReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen_codes: set[str] = set()
    for row in rows:
        if type(row) is not ResearchMarketProbabilityCostFloorBreakEvenReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketProbabilityCostFloorBreakEvenReasonCodeCount",
            )
        _require_hard_flags("reason code count", row)
        if row.reason_code in seen_codes:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen_codes.add(row.reason_code)
    sorted_rows = tuple(sorted(rows, key=lambda row: _REASON_CODE_SEQUENCE.index(row.reason_code)))
    if rows != sorted_rows:
        raise ValueError("reason_code_counts must be sorted deterministically")
    return rows


def _reason_code_counts(
    rows: tuple[ResearchMarketProbabilityCostFloorBreakEvenRow, ...],
) -> tuple[ResearchMarketProbabilityCostFloorBreakEvenReasonCodeCount, ...]:
    counts: list[ResearchMarketProbabilityCostFloorBreakEvenReasonCodeCount] = []
    for reason_code in _REASON_CODE_SEQUENCE:
        count = _reason_count(rows, reason_code)
        if count > _ZERO:
            counts.append(
                ResearchMarketProbabilityCostFloorBreakEvenReasonCodeCount(
                    reason_code=reason_code,
                    count=count,
                ),
            )
    return tuple(counts)


def _input_sort_key(row: ResearchMarketProbabilityCostFloorBreakEvenInput) -> tuple[Decimal, ...]:
    return (
        row.market_probability,
        row.research_probability_floor,
        row.fee_probability_cost,
        row.slippage_probability_cost,
        row.impact_probability_cost,
    )


def _row_sort_key(
    row: ResearchMarketProbabilityCostFloorBreakEvenRow,
) -> tuple[int, Decimal, Decimal, Decimal, Decimal, Decimal, Decimal]:
    return (
        _STATUS_SORT[row.status],
        row.break_even_margin,
        row.market_probability,
        row.research_probability_floor,
        row.fee_probability_cost,
        row.slippage_probability_cost,
        row.impact_probability_cost,
    )


def _status_count(
    rows: tuple[ResearchMarketProbabilityCostFloorBreakEvenRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[ResearchMarketProbabilityCostFloorBreakEvenRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_member(field_name: str, value: object, members: frozenset[str]) -> str:
    if type(value) is not str or value not in members:
        raise ValueError(f"{field_name} must be a known value")
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    _require_public_identifier(field_name, value)
    if value not in _REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be supported")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_probability(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_probability_delta(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < -_ONE or normalized > _ONE:
        raise ValueError(f"{field_name} must be between negative one and one")
    return normalized


def _require_nonnegative_probability_delta(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal count")
    return _quantize(value)


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_QUANT)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _normalize_reason_codes(value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of reason codes")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of reason codes") from exc
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    if "probability_cost_floor_break_even_pass" in normalized and len(normalized) > 1:
        raise ValueError("pass reason must stand alone")
    if "thin_probability_margin" in normalized and len(normalized) > 1:
        raise ValueError("thin margin reason must stand alone")
    return tuple(
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in normalized
    )


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _report_values_without_digest(
    report: ResearchMarketProbabilityCostFloorBreakEvenReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload(
        "derived_validation_digest payload",
        payload,
        allow_json_containers=True,
    )
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return format(value, "f")
    if type(value) is datetime:
        return _as_utc("datetime payload value", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        if type(value) is list and not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)
        return
    if (
        value is None
        or type(value) is bool
        or type(value) is Decimal
        or type(value) is datetime
    ):
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


__all__ = (
    "DEFAULT_RESEARCH_MARKET_PROBABILITY_COST_FLOOR_BREAK_EVEN_CONFIG_VERSION",
    "STATUSES",
    "ResearchMarketProbabilityCostFloorBreakEvenConfig",
    "ResearchMarketProbabilityCostFloorBreakEvenInput",
    "ResearchMarketProbabilityCostFloorBreakEvenReasonCodeCount",
    "ResearchMarketProbabilityCostFloorBreakEvenReport",
    "ResearchMarketProbabilityCostFloorBreakEvenRow",
    "build_research_market_probability_cost_floor_break_even_report",
)
