"""Pure report for expected value research input review quality."""

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
    "ResearchStrategyExpectedValueInput",
    "ResearchStrategyExpectedValueInputQualityConfig",
    "ResearchStrategyExpectedValueInputQualityReasonCodeCount",
    "ResearchStrategyExpectedValueInputQualityReport",
    "ResearchStrategyExpectedValueInputQualityRow",
    "build_research_strategy_expected_value_input_quality_report",
    "research_strategy_expected_value_input_quality_report_digest",
    "research_strategy_expected_value_input_quality_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-strategy-expected-value-input-quality-report-v0"
STATUSES = ("pass", "watch", "block")
COMPONENT_FIELDS = (
    "forecast_confidence",
    "cost_estimate_quality",
    "liquidity_quality",
    "resolution_clarity",
    "evidence_freshness",
)
ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")


class _Missing:
    pass


_MISSING = _Missing()


@dataclass(frozen=True)
class ResearchStrategyExpectedValueInputQualityConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    pass_component_quality: Decimal = Decimal("0.700000")
    watch_component_quality: Decimal = Decimal("0.400000")
    pass_quality_score: Decimal = Decimal("0.750000")
    watch_quality_score: Decimal = Decimal("0.500000")
    forecast_confidence_weight: Decimal = Decimal("0.200000")
    cost_estimate_quality_weight: Decimal = Decimal("0.200000")
    liquidity_quality_weight: Decimal = Decimal("0.200000")
    resolution_clarity_weight: Decimal = Decimal("0.200000")
    evidence_freshness_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_label("config_version", self.config_version)
        for field_name in (
            "pass_component_quality",
            "watch_component_quality",
            "pass_quality_score",
            "watch_quality_score",
            "forecast_confidence_weight",
            "cost_estimate_quality_weight",
            "liquidity_quality_weight",
            "resolution_clarity_weight",
            "evidence_freshness_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_component_quality <= self.watch_component_quality:
            raise ValueError("pass_component_quality must exceed watch_component_quality")
        if self.pass_quality_score <= self.watch_quality_score:
            raise ValueError("pass_quality_score must exceed watch_quality_score")
        if _config_weight_sum(self) != ONE:
            raise ValueError(
                "forecast_confidence_weight, cost_estimate_quality_weight, "
                "liquidity_quality_weight, resolution_clarity_weight, "
                "and evidence_freshness_weight must sum to 1",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyExpectedValueInput:
    research_key: str
    evidence_set_label: str
    forecast_confidence: Decimal
    cost_estimate_quality: Decimal
    liquidity_quality: Decimal
    resolution_clarity: Decimal
    evidence_freshness: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_label("research_key", self.research_key)
        _require_public_label("evidence_set_label", self.evidence_set_label)
        for field_name in COMPONENT_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyExpectedValueInputQualityRow:
    research_key: str
    evidence_set_label: str
    forecast_confidence: Decimal
    cost_estimate_quality: Decimal
    liquidity_quality: Decimal
    resolution_clarity: Decimal
    evidence_freshness: Decimal
    input_quality_score: Decimal
    lowest_component_quality: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_label("research_key", self.research_key)
        _require_public_label("evidence_set_label", self.evidence_set_label)
        for field_name in (
            *COMPONENT_FIELDS,
            "input_quality_score",
            "lowest_component_quality",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
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
class ResearchStrategyExpectedValueInputQualityReasonCodeCount:
    reason_code: str
    count: Decimal
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
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchStrategyExpectedValueInputQualityReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_input_quality_score: Decimal | None
    status: str
    rows: tuple[ResearchStrategyExpectedValueInputQualityRow, ...]
    reason_code_counts: tuple[
        ResearchStrategyExpectedValueInputQualityReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
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
            "average_input_quality_score",
            _require_optional_probability_decimal(
                "average_input_quality_score",
                self.average_input_quality_score,
            ),
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


def build_research_strategy_expected_value_input_quality_report(
    inputs: Iterable[object],
    *,
    config: ResearchStrategyExpectedValueInputQualityConfig,
    generated_at: datetime,
) -> ResearchStrategyExpectedValueInputQualityReport:
    if type(config) is not ResearchStrategyExpectedValueInputQualityConfig:
        raise ValueError(
            "config must be a ResearchStrategyExpectedValueInputQualityConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_items = _normalize_inputs(inputs)
    rows = tuple(
        _quality_row_from_input(item, config=config)
        for item in sorted(input_items, key=lambda item: item.research_key)
    )
    reason_codes = _summary_reason_codes(rows)
    return ResearchStrategyExpectedValueInputQualityReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        average_input_quality_score=_average_input_quality_score(rows),
        status=_summary_status(reason_codes),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_strategy_expected_value_input_quality_report_payload(
    report: ResearchStrategyExpectedValueInputQualityReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategyExpectedValueInputQualityReport:
        raise ValueError(
            "report must be a ResearchStrategyExpectedValueInputQualityReport",
        )
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    return payload


def research_strategy_expected_value_input_quality_report_digest(
    report: ResearchStrategyExpectedValueInputQualityReport,
) -> str:
    payload = research_strategy_expected_value_input_quality_report_payload(report)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _quality_row_from_input(
    item: ResearchStrategyExpectedValueInput,
    *,
    config: ResearchStrategyExpectedValueInputQualityConfig,
) -> ResearchStrategyExpectedValueInputQualityRow:
    score = _input_quality_score(item, config)
    lowest_component = min(getattr(item, field_name) for field_name in COMPONENT_FIELDS)
    status = _row_status(
        input_quality_score=score,
        lowest_component_quality=lowest_component,
        config=config,
    )
    return ResearchStrategyExpectedValueInputQualityRow(
        research_key=item.research_key,
        evidence_set_label=item.evidence_set_label,
        forecast_confidence=item.forecast_confidence,
        cost_estimate_quality=item.cost_estimate_quality,
        liquidity_quality=item.liquidity_quality,
        resolution_clarity=item.resolution_clarity,
        evidence_freshness=item.evidence_freshness,
        input_quality_score=score,
        lowest_component_quality=lowest_component,
        status=status,
        reason_codes=_row_reason_codes(item, status=status, config=config),
    )


def _input_quality_score(
    item: ResearchStrategyExpectedValueInput,
    config: ResearchStrategyExpectedValueInputQualityConfig,
) -> Decimal:
    with localcontext() as context:
        context.prec = 28
        score = (
            (item.forecast_confidence * config.forecast_confidence_weight)
            + (item.cost_estimate_quality * config.cost_estimate_quality_weight)
            + (item.liquidity_quality * config.liquidity_quality_weight)
            + (item.resolution_clarity * config.resolution_clarity_weight)
            + (item.evidence_freshness * config.evidence_freshness_weight)
        )
    return _quantize(score)


def _row_status(
    *,
    input_quality_score: Decimal,
    lowest_component_quality: Decimal,
    config: ResearchStrategyExpectedValueInputQualityConfig,
) -> str:
    if (
        input_quality_score < config.watch_quality_score
        or lowest_component_quality < config.watch_component_quality
    ):
        return "block"
    if (
        input_quality_score < config.pass_quality_score
        or lowest_component_quality < config.pass_component_quality
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    item: ResearchStrategyExpectedValueInput,
    *,
    status: str,
    config: ResearchStrategyExpectedValueInputQualityConfig,
) -> tuple[str, ...]:
    codes = {
        f"expected_value_input_quality_{status}",
        f"manual_review_input_quality_{status}",
    }
    for field_name in COMPONENT_FIELDS:
        codes.add(
            f"component_{field_name}_{_component_status(getattr(item, field_name), config)}",
        )
    for code in item.reason_codes:
        codes.add(f"input_{code}")
    return tuple(sorted(codes))


def _component_status(
    value: Decimal,
    config: ResearchStrategyExpectedValueInputQualityConfig,
) -> str:
    if value < config.watch_component_quality:
        return "block"
    if value < config.pass_component_quality:
        return "watch"
    return "pass"


def _normalize_inputs(
    inputs: Iterable[object],
) -> tuple[ResearchStrategyExpectedValueInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        values = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    return tuple(_coerce_input(value) for value in values)


def _coerce_input(value: object) -> ResearchStrategyExpectedValueInput:
    if type(value) is ResearchStrategyExpectedValueInput:
        _require_hard_flags("input", value)
        return value
    _require_hard_flags("input", value)
    return ResearchStrategyExpectedValueInput(
        research_key=_field_value(value, "research_key"),
        evidence_set_label=_field_value(value, "evidence_set_label"),
        forecast_confidence=_field_value(value, "forecast_confidence"),
        cost_estimate_quality=_field_value(value, "cost_estimate_quality"),
        liquidity_quality=_field_value(value, "liquidity_quality"),
        resolution_clarity=_field_value(value, "resolution_clarity"),
        evidence_freshness=_field_value(value, "evidence_freshness"),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _summary_reason_codes(
    rows: tuple[ResearchStrategyExpectedValueInputQualityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_expected_value_research_inputs",)
    if all(row.status == "pass" for row in rows):
        return ("expected_value_input_quality_pass",)
    return tuple(sorted({code for row in rows for code in row.reason_codes}))


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("no_expected_value_research_inputs",):
        return "block"
    if "expected_value_input_quality_block" in reason_codes:
        return "block"
    if "expected_value_input_quality_watch" in reason_codes:
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchStrategyExpectedValueInputQualityRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchStrategyExpectedValueInputQualityReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategyExpectedValueInputQualityReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        ResearchStrategyExpectedValueInputQualityReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counter.items(), key=lambda item: item[0])
    )


def _average_input_quality_score(
    rows: tuple[ResearchStrategyExpectedValueInputQualityRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(sum((row.input_quality_score for row in rows), ZERO) / Decimal(len(rows)))


def _status_count(
    rows: tuple[ResearchStrategyExpectedValueInputQualityRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_rows(
    rows: tuple[ResearchStrategyExpectedValueInputQualityRow, ...],
) -> tuple[ResearchStrategyExpectedValueInputQualityRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchStrategyExpectedValueInputQualityRow:
            raise ValueError(
                "rows must contain ResearchStrategyExpectedValueInputQualityRow values",
            )
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.research_key))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by research_key")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchStrategyExpectedValueInputQualityReasonCodeCount, ...],
) -> tuple[ResearchStrategyExpectedValueInputQualityReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchStrategyExpectedValueInputQualityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyExpectedValueInputQualityReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_row_consistency(
    row: ResearchStrategyExpectedValueInputQualityRow,
) -> None:
    calculated_lowest = min(getattr(row, field_name) for field_name in COMPONENT_FIELDS)
    if row.lowest_component_quality != calculated_lowest:
        raise ValueError("lowest_component_quality must match components")
    if row.status not in row.reason_codes:
        expected_code = f"expected_value_input_quality_{row.status}"
        if expected_code not in row.reason_codes:
            raise ValueError("status must match reason_codes")
    if row.status == "pass" and row.input_quality_score < Decimal("0.750000"):
        raise ValueError("input_quality_score must support pass status")
    if row.status == "watch" and (
        row.input_quality_score < Decimal("0.500000")
        or row.input_quality_score >= Decimal("0.750000")
        and row.lowest_component_quality >= Decimal("0.700000")
    ):
        raise ValueError("input_quality_score must support watch status")
    if row.status == "block" and (
        row.input_quality_score >= Decimal("0.500000")
        and row.lowest_component_quality >= Decimal("0.400000")
    ):
        raise ValueError("input_quality_score must support block status")


def _validate_report_consistency(
    report: ResearchStrategyExpectedValueInputQualityReport,
) -> None:
    if report.input_count != _decimal_count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_input_quality_score != _average_input_quality_score(report.rows):
        raise ValueError("average_input_quality_score must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _summary_status(report.reason_codes):
        raise ValueError("status must match reason_codes")


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


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _require_optional_probability_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_probability_decimal(field_name, value)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count input must be an int")
    if value < 0:
        raise ValueError("count input must be nonnegative")
    return Decimal(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _config_weight_sum(config: ResearchStrategyExpectedValueInputQualityConfig) -> Decimal:
    return _quantize(
        config.forecast_confidence_weight
        + config.cost_estimate_quality_weight
        + config.liquidity_quality_weight
        + config.resolution_clarity_weight
        + config.evidence_freshness_weight,
    )


def _require_public_label(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty public label")
    lowered = value.lower()
    for fragment in ("raw", "market_id", "market_slug", "condition_id", "token_id"):
        if fragment in lowered:
            raise ValueError(f"{field_name} must not expose raw identifiers")


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
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(sorted(set(normalized)))


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")
