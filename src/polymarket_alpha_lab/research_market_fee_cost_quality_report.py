"""Pure aggregate fee cost input quality report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, localcontext
import hashlib
import json
from typing import Any


__all__ = (
    "COST_INPUT_QUALITY_STATUSES",
    "DEFAULT_RESEARCH_MARKET_FEE_COST_QUALITY_REPORT_CONFIG_VERSION",
    "ResearchMarketFeeCostQualityConfig",
    "ResearchMarketFeeCostQualityInput",
    "ResearchMarketFeeCostQualityReasonCodeCount",
    "ResearchMarketFeeCostQualityReport",
    "ResearchMarketFeeCostQualityRow",
    "build_research_market_fee_cost_quality_report",
    "research_market_fee_cost_quality_report_digest",
    "research_market_fee_cost_quality_report_payload",
)


DEFAULT_RESEARCH_MARKET_FEE_COST_QUALITY_REPORT_CONFIG_VERSION = (
    "research-market-fee-cost-quality-report-v0"
)
COST_INPUT_QUALITY_STATUSES = ("pass", "watch", "block")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
RATIO_QUANTUM = Decimal("0.000001")
COMPONENT_REASON_PRIORITY = (
    "fee_assumption_block",
    "spread_drag_block",
    "settlement_friction_block",
    "depth_confidence_block",
    "stale_cost_input_block",
    "fee_assumption_watch",
    "spread_drag_watch",
    "settlement_friction_watch",
    "depth_confidence_watch",
    "stale_cost_input_watch",
)


class _Missing:
    pass


_MISSING = _Missing()


@dataclass(frozen=True)
class ResearchMarketFeeCostQualityConfig:
    config_version: str = DEFAULT_RESEARCH_MARKET_FEE_COST_QUALITY_REPORT_CONFIG_VERSION
    max_pass_fee_assumption_rate: Decimal = Decimal("0.020000")
    max_watch_fee_assumption_rate: Decimal = Decimal("0.040000")
    max_pass_spread_drag_rate: Decimal = Decimal("0.010000")
    max_watch_spread_drag_rate: Decimal = Decimal("0.030000")
    max_pass_settlement_friction_rate: Decimal = Decimal("0.005000")
    max_watch_settlement_friction_rate: Decimal = Decimal("0.020000")
    min_pass_depth_confidence: Decimal = Decimal("0.800000")
    min_watch_depth_confidence: Decimal = Decimal("0.550000")
    max_pass_cost_input_age_seconds: Decimal = Decimal("43200.000000")
    max_watch_cost_input_age_seconds: Decimal = Decimal("172800.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketFeeCostQualityConfig, "config")
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_FEE_COST_QUALITY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_pass_fee_assumption_rate",
            "max_watch_fee_assumption_rate",
            "max_pass_spread_drag_rate",
            "max_watch_spread_drag_rate",
            "max_pass_settlement_friction_rate",
            "max_watch_settlement_friction_rate",
            "min_pass_depth_confidence",
            "min_watch_depth_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_cost_input_age_seconds",
            "max_watch_cost_input_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.max_pass_fee_assumption_rate > self.max_watch_fee_assumption_rate:
            raise ValueError("pass fee assumption threshold must not exceed watch")
        if self.max_pass_spread_drag_rate > self.max_watch_spread_drag_rate:
            raise ValueError("pass spread drag threshold must not exceed watch")
        if (
            self.max_pass_settlement_friction_rate
            > self.max_watch_settlement_friction_rate
        ):
            raise ValueError("pass settlement friction threshold must not exceed watch")
        if self.min_watch_depth_confidence > self.min_pass_depth_confidence:
            raise ValueError("watch depth confidence threshold must not exceed pass")
        if self.max_pass_cost_input_age_seconds > self.max_watch_cost_input_age_seconds:
            raise ValueError("pass stale input threshold must not exceed watch")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketFeeCostQualityInput:
    research_key: str
    fee_assumption_rate: Decimal
    spread_drag_rate: Decimal
    settlement_friction_rate: Decimal
    depth_confidence: Decimal
    cost_input_age_seconds: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketFeeCostQualityInput, "input")
        _require_public_label("research_key", self.research_key)
        for field_name in (
            "fee_assumption_rate",
            "spread_drag_rate",
            "settlement_friction_rate",
            "depth_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "cost_input_age_seconds",
            _require_nonnegative_decimal(
                "cost_input_age_seconds",
                self.cost_input_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchMarketFeeCostQualityRow:
    research_key: str
    fee_assumption_rate: Decimal
    spread_drag_rate: Decimal
    settlement_friction_rate: Decimal
    depth_confidence: Decimal
    cost_input_age_seconds: Decimal
    stale_cost_input_risk: Decimal
    cost_input_quality_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketFeeCostQualityRow, "row")
        _require_public_label("research_key", self.research_key)
        for field_name in (
            "fee_assumption_rate",
            "spread_drag_rate",
            "settlement_friction_rate",
            "depth_confidence",
            "stale_cost_input_risk",
            "cost_input_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "cost_input_age_seconds",
            _require_nonnegative_decimal(
                "cost_input_age_seconds",
                self.cost_input_age_seconds,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchMarketFeeCostQualityReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchMarketFeeCostQualityReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_cost_input_quality_score: Decimal | None
    max_fee_assumption_rate: Decimal
    max_spread_drag_rate: Decimal
    max_settlement_friction_rate: Decimal
    min_depth_confidence: Decimal
    max_stale_cost_input_risk: Decimal
    status: str
    rows: tuple[ResearchMarketFeeCostQualityRow, ...]
    reason_code_counts: tuple[ResearchMarketFeeCostQualityReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketFeeCostQualityReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        for field_name in ("input_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_cost_input_quality_score",
            _require_optional_ratio_decimal(
                "average_cost_input_quality_score",
                self.average_cost_input_quality_score,
            ),
        )
        for field_name in (
            "max_fee_assumption_rate",
            "max_spread_drag_rate",
            "max_settlement_friction_rate",
            "min_depth_confidence",
            "max_stale_cost_input_risk",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("report", self)
        _validate_report_consistency(self)


def build_research_market_fee_cost_quality_report(
    inputs: Iterable[object],
    *,
    config: ResearchMarketFeeCostQualityConfig,
    generated_at: datetime,
) -> ResearchMarketFeeCostQualityReport:
    if type(config) is not ResearchMarketFeeCostQualityConfig:
        raise ValueError("config must be a ResearchMarketFeeCostQualityConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_items = _normalize_inputs(inputs)
    rows = tuple(
        _row_from_input(item, config=config)
        for item in sorted(input_items, key=lambda item: item.research_key)
    )
    reason_codes = _summary_reason_codes(rows)
    return ResearchMarketFeeCostQualityReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        average_cost_input_quality_score=_average_quality_score(rows),
        max_fee_assumption_rate=_maximum_row_value(rows, "fee_assumption_rate"),
        max_spread_drag_rate=_maximum_row_value(rows, "spread_drag_rate"),
        max_settlement_friction_rate=_maximum_row_value(
            rows,
            "settlement_friction_rate",
        ),
        min_depth_confidence=_minimum_row_value(rows, "depth_confidence"),
        max_stale_cost_input_risk=_maximum_row_value(rows, "stale_cost_input_risk"),
        status=_summary_status(reason_codes),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_market_fee_cost_quality_report_payload(
    report: ResearchMarketFeeCostQualityReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketFeeCostQualityReport:
        raise ValueError("report must be a ResearchMarketFeeCostQualityReport")
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    return payload


def research_market_fee_cost_quality_report_digest(
    report: ResearchMarketFeeCostQualityReport,
) -> str:
    payload = research_market_fee_cost_quality_report_payload(report)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _row_from_input(
    item: ResearchMarketFeeCostQualityInput,
    *,
    config: ResearchMarketFeeCostQualityConfig,
) -> ResearchMarketFeeCostQualityRow:
    stale_cost_input_risk = _stale_cost_input_risk(item.cost_input_age_seconds, config)
    cost_input_quality_score = _cost_input_quality_score(
        fee_assumption_rate=item.fee_assumption_rate,
        spread_drag_rate=item.spread_drag_rate,
        settlement_friction_rate=item.settlement_friction_rate,
        depth_confidence=item.depth_confidence,
        stale_cost_input_risk=stale_cost_input_risk,
    )
    status = _row_status(item, config=config)
    return ResearchMarketFeeCostQualityRow(
        research_key=item.research_key,
        fee_assumption_rate=item.fee_assumption_rate,
        spread_drag_rate=item.spread_drag_rate,
        settlement_friction_rate=item.settlement_friction_rate,
        depth_confidence=item.depth_confidence,
        cost_input_age_seconds=item.cost_input_age_seconds,
        stale_cost_input_risk=stale_cost_input_risk,
        cost_input_quality_score=cost_input_quality_score,
        status=status,
        reason_codes=_row_reason_codes(item, status=status, config=config),
    )


def _stale_cost_input_risk(
    cost_input_age_seconds: Decimal,
    config: ResearchMarketFeeCostQualityConfig,
) -> Decimal:
    with localcontext() as context:
        context.prec = 28
        risk = cost_input_age_seconds / config.max_watch_cost_input_age_seconds
    if risk > ONE:
        return ONE
    return _quantize(risk)


def _cost_input_quality_score(
    *,
    fee_assumption_rate: Decimal,
    spread_drag_rate: Decimal,
    settlement_friction_rate: Decimal,
    depth_confidence: Decimal,
    stale_cost_input_risk: Decimal,
) -> Decimal:
    with localcontext() as context:
        context.prec = 28
        score = (
            (ONE - fee_assumption_rate)
            + (ONE - spread_drag_rate)
            + (ONE - settlement_friction_rate)
            + depth_confidence
            + (ONE - stale_cost_input_risk)
        ) / Decimal("5")
    return _quantize(score)


def _row_status(
    item: ResearchMarketFeeCostQualityInput,
    *,
    config: ResearchMarketFeeCostQualityConfig,
) -> str:
    if (
        item.fee_assumption_rate > config.max_watch_fee_assumption_rate
        or item.spread_drag_rate > config.max_watch_spread_drag_rate
        or item.settlement_friction_rate > config.max_watch_settlement_friction_rate
        or item.depth_confidence < config.min_watch_depth_confidence
        or item.cost_input_age_seconds > config.max_watch_cost_input_age_seconds
    ):
        return "block"
    if (
        item.fee_assumption_rate > config.max_pass_fee_assumption_rate
        or item.spread_drag_rate > config.max_pass_spread_drag_rate
        or item.settlement_friction_rate > config.max_pass_settlement_friction_rate
        or item.depth_confidence < config.min_pass_depth_confidence
        or item.cost_input_age_seconds > config.max_pass_cost_input_age_seconds
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    item: ResearchMarketFeeCostQualityInput,
    *,
    status: str,
    config: ResearchMarketFeeCostQualityConfig,
) -> tuple[str, ...]:
    codes = {
        f"market_fee_cost_quality_{status}",
        f"manual_review_fee_cost_inputs_{status}",
        f"fee_assumption_{_fee_status(item.fee_assumption_rate, config)}",
        f"spread_drag_{_spread_status(item.spread_drag_rate, config)}",
        (
            "settlement_friction_"
            f"{_settlement_status(item.settlement_friction_rate, config)}"
        ),
        f"depth_confidence_{_depth_status(item.depth_confidence, config)}",
        f"stale_cost_input_{_age_status(item.cost_input_age_seconds, config)}",
    }
    for code in item.reason_codes:
        codes.add(f"input_{code}")
    return tuple(sorted(codes))


def _fee_status(value: Decimal, config: ResearchMarketFeeCostQualityConfig) -> str:
    if value > config.max_watch_fee_assumption_rate:
        return "block"
    if value > config.max_pass_fee_assumption_rate:
        return "watch"
    return "pass"


def _spread_status(value: Decimal, config: ResearchMarketFeeCostQualityConfig) -> str:
    if value > config.max_watch_spread_drag_rate:
        return "block"
    if value > config.max_pass_spread_drag_rate:
        return "watch"
    return "pass"


def _settlement_status(value: Decimal, config: ResearchMarketFeeCostQualityConfig) -> str:
    if value > config.max_watch_settlement_friction_rate:
        return "block"
    if value > config.max_pass_settlement_friction_rate:
        return "watch"
    return "pass"


def _depth_status(value: Decimal, config: ResearchMarketFeeCostQualityConfig) -> str:
    if value < config.min_watch_depth_confidence:
        return "block"
    if value < config.min_pass_depth_confidence:
        return "watch"
    return "pass"


def _age_status(value: Decimal, config: ResearchMarketFeeCostQualityConfig) -> str:
    if value > config.max_watch_cost_input_age_seconds:
        return "block"
    if value > config.max_pass_cost_input_age_seconds:
        return "watch"
    return "pass"


def _normalize_inputs(
    inputs: Iterable[object],
) -> tuple[ResearchMarketFeeCostQualityInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        values = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    return tuple(_coerce_input(value) for value in values)


def _coerce_input(value: object) -> ResearchMarketFeeCostQualityInput:
    if type(value) is ResearchMarketFeeCostQualityInput:
        _require_hard_flags("input", value)
        return value
    _require_hard_flags("input", value)
    return ResearchMarketFeeCostQualityInput(
        research_key=_field_value(value, "research_key"),
        fee_assumption_rate=_field_value(value, "fee_assumption_rate"),
        spread_drag_rate=_field_value(value, "spread_drag_rate"),
        settlement_friction_rate=_field_value(value, "settlement_friction_rate"),
        depth_confidence=_field_value(value, "depth_confidence"),
        cost_input_age_seconds=_field_value(value, "cost_input_age_seconds"),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _summary_reason_codes(
    rows: tuple[ResearchMarketFeeCostQualityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_fee_cost_inputs",)
    if all(row.status == "pass" for row in rows):
        return ("market_fee_cost_quality_pass",)
    codes: list[str] = []
    if any(row.status == "block" for row in rows):
        codes.append("market_fee_cost_quality_block")
    elif any(row.status == "watch" for row in rows):
        codes.append("market_fee_cost_quality_watch")
    row_codes = {code for row in rows for code in row.reason_codes}
    for code in COMPONENT_REASON_PRIORITY:
        if code in row_codes:
            codes.append(code)
    return tuple(codes)


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("no_fee_cost_inputs",):
        return "block"
    if "market_fee_cost_quality_block" in reason_codes:
        return "block"
    if "market_fee_cost_quality_watch" in reason_codes:
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchMarketFeeCostQualityRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchMarketFeeCostQualityReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketFeeCostQualityReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    row_count = Decimal(len(rows))
    return tuple(
        ResearchMarketFeeCostQualityReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
            row_ratio=_quantize(Decimal(count) / row_count),
        )
        for reason_code, count in sorted(counter.items(), key=lambda item: item[0])
    )


def _average_quality_score(
    rows: tuple[ResearchMarketFeeCostQualityRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(
        sum((row.cost_input_quality_score for row in rows), ZERO) / Decimal(len(rows)),
    )


def _minimum_row_value(
    rows: tuple[ResearchMarketFeeCostQualityRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return min(getattr(row, field_name) for row in rows)


def _maximum_row_value(
    rows: tuple[ResearchMarketFeeCostQualityRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _status_count(rows: tuple[ResearchMarketFeeCostQualityRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_rows(
    rows: tuple[ResearchMarketFeeCostQualityRow, ...],
) -> tuple[ResearchMarketFeeCostQualityRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchMarketFeeCostQualityRow:
            raise ValueError("rows must contain ResearchMarketFeeCostQualityRow values")
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.research_key))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by research_key")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchMarketFeeCostQualityReasonCodeCount, ...],
) -> tuple[ResearchMarketFeeCostQualityReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchMarketFeeCostQualityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketFeeCostQualityReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_row_consistency(row: ResearchMarketFeeCostQualityRow) -> None:
    expected_score = _cost_input_quality_score(
        fee_assumption_rate=row.fee_assumption_rate,
        spread_drag_rate=row.spread_drag_rate,
        settlement_friction_rate=row.settlement_friction_rate,
        depth_confidence=row.depth_confidence,
        stale_cost_input_risk=row.stale_cost_input_risk,
    )
    if row.cost_input_quality_score != expected_score:
        raise ValueError("cost_input_quality_score must match components")
    expected_status_code = f"market_fee_cost_quality_{row.status}"
    if expected_status_code not in row.reason_codes:
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and any(
        code.endswith(("_watch", "_block")) for code in row.reason_codes
    ):
        raise ValueError("status must match component reason_codes")
    if row.status == "watch" and any(code.endswith("_block") for code in row.reason_codes):
        raise ValueError("status must match component reason_codes")


def _validate_report_consistency(report: ResearchMarketFeeCostQualityReport) -> None:
    if report.input_count != _decimal_count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_cost_input_quality_score != _average_quality_score(report.rows):
        raise ValueError("average_cost_input_quality_score must match rows")
    if report.max_fee_assumption_rate != _maximum_row_value(
        report.rows,
        "fee_assumption_rate",
    ):
        raise ValueError("max_fee_assumption_rate must match rows")
    if report.max_spread_drag_rate != _maximum_row_value(report.rows, "spread_drag_rate"):
        raise ValueError("max_spread_drag_rate must match rows")
    if report.max_settlement_friction_rate != _maximum_row_value(
        report.rows,
        "settlement_friction_rate",
    ):
        raise ValueError("max_settlement_friction_rate must match rows")
    if report.min_depth_confidence != _minimum_row_value(report.rows, "depth_confidence"):
        raise ValueError("min_depth_confidence must match rows")
    if report.max_stale_cost_input_risk != _maximum_row_value(
        report.rows,
        "stale_cost_input_risk",
    ):
        raise ValueError("max_stale_cost_input_risk must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _summary_status(report.reason_codes):
        raise ValueError("status must match reason_codes")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _field_value(value: object, field_name: str, *, default: object = _MISSING) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            if field.name == field_name:
                return getattr(value, field_name)
    if hasattr(value, field_name):
        return getattr(value, field_name)
    if default is not _MISSING:
        return default
    raise ValueError(f"{field_name} is required")


def _payload_value(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(asdict(value))
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    return value


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _require_optional_ratio_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_ratio_decimal(field_name, value)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return _quantize(normalized)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(normalized)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return _quantize(normalized)


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return _quantize(normalized)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count input must be an int")
    if value < 0:
        raise ValueError("count input must be nonnegative")
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _require_public_label(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty public label")
    lowered = value.lower()
    forbidden_fragments = (
        "raw",
        "slug",
        "condition" + "_" + "id",
        "token" + "_" + "id",
        "market" + "_" + "id",
        "source" + "_" + "text",
        "quest" + "ion",
        "http",
        "://",
        "secret",
        "credential",
        "private",
    )
    if any(fragment in lowered for fragment in forbidden_fragments):
        raise ValueError(f"{field_name} must not expose raw labels")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    if value.lower() != value:
        raise ValueError(f"{field_name} must contain lowercase reason codes")
    if " " in value:
        raise ValueError(f"{field_name} must contain compact reason codes")


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_reason_code(field_name, value)
        if value not in normalized:
            normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(normalized)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in COST_INPUT_QUALITY_STATUSES:
        raise ValueError(f"{field_name} must be one of {COST_INPUT_QUALITY_STATUSES}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")
