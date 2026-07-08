"""Pure report for public forecast consensus health review."""

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
    "ResearchStrategyForecastConsensusHealthConfig",
    "ResearchStrategyForecastConsensusHealthInput",
    "ResearchStrategyForecastConsensusHealthReasonCodeCount",
    "ResearchStrategyForecastConsensusHealthReport",
    "ResearchStrategyForecastConsensusHealthRow",
    "build_research_strategy_forecast_consensus_health_report",
    "research_strategy_forecast_consensus_health_report_digest",
    "research_strategy_forecast_consensus_health_report_payload",
)

DEFAULT_CONFIG_VERSION = "research-strategy-forecast-consensus-health-report-v0"
STATUSES = ("pass", "watch", "block")
PRESSURE_FIELDS = (
    "team_confidence_dispersion",
    "calibration_drift",
    "contradiction_pressure",
)
QUALITY_FIELDS = (
    "evidence_freshness",
    "cost_input_quality",
)
ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")


class _Missing:
    pass


_MISSING = _Missing()


@dataclass(frozen=True)
class ResearchStrategyForecastConsensusHealthConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    pass_dimension_score: Decimal = Decimal("0.700000")
    watch_dimension_score: Decimal = Decimal("0.400000")
    pass_health_score: Decimal = Decimal("0.750000")
    watch_health_score: Decimal = Decimal("0.500000")
    confidence_alignment_weight: Decimal = Decimal("0.200000")
    calibration_stability_weight: Decimal = Decimal("0.200000")
    evidence_freshness_weight: Decimal = Decimal("0.200000")
    contradiction_resistance_weight: Decimal = Decimal("0.200000")
    cost_input_quality_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_label("config_version", self.config_version)
        for field_name in (
            "pass_dimension_score",
            "watch_dimension_score",
            "pass_health_score",
            "watch_health_score",
            "confidence_alignment_weight",
            "calibration_stability_weight",
            "evidence_freshness_weight",
            "contradiction_resistance_weight",
            "cost_input_quality_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_dimension_score <= self.watch_dimension_score:
            raise ValueError("pass_dimension_score must exceed watch_dimension_score")
        if self.pass_health_score <= self.watch_health_score:
            raise ValueError("pass_health_score must exceed watch_health_score")
        if _config_weight_sum(self) != ONE:
            raise ValueError(
                "confidence_alignment_weight, calibration_stability_weight, "
                "evidence_freshness_weight, contradiction_resistance_weight, "
                "and cost_input_quality_weight must sum to 1",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyForecastConsensusHealthInput:
    consensus_scope_label: str
    team_confidence_dispersion: Decimal
    calibration_drift: Decimal
    evidence_freshness: Decimal
    contradiction_pressure: Decimal
    cost_input_quality: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_label("consensus_scope_label", self.consensus_scope_label)
        for field_name in (*PRESSURE_FIELDS, *QUALITY_FIELDS):
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
class ResearchStrategyForecastConsensusHealthRow:
    consensus_scope_label: str
    team_confidence_dispersion: Decimal
    calibration_drift: Decimal
    evidence_freshness: Decimal
    contradiction_pressure: Decimal
    cost_input_quality: Decimal
    confidence_alignment_score: Decimal
    calibration_stability_score: Decimal
    evidence_freshness_score: Decimal
    contradiction_resistance_score: Decimal
    cost_input_quality_score: Decimal
    consensus_health_score: Decimal
    lowest_dimension_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_label("consensus_scope_label", self.consensus_scope_label)
        for field_name in (
            *PRESSURE_FIELDS,
            *QUALITY_FIELDS,
            "confidence_alignment_score",
            "calibration_stability_score",
            "evidence_freshness_score",
            "contradiction_resistance_score",
            "cost_input_quality_score",
            "consensus_health_score",
            "lowest_dimension_score",
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
class ResearchStrategyForecastConsensusHealthReasonCodeCount:
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
class ResearchStrategyForecastConsensusHealthReport:
    generated_at: datetime
    config_version: str
    scope_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_consensus_health_score: Decimal | None
    max_team_confidence_dispersion: Decimal | None
    max_calibration_drift: Decimal | None
    min_evidence_freshness: Decimal | None
    max_contradiction_pressure: Decimal | None
    min_cost_input_quality: Decimal | None
    status: str
    rows: tuple[ResearchStrategyForecastConsensusHealthRow, ...]
    reason_code_counts: tuple[
        ResearchStrategyForecastConsensusHealthReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        for field_name in ("scope_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_consensus_health_score",
            "max_team_confidence_dispersion",
            "max_calibration_drift",
            "min_evidence_freshness",
            "max_contradiction_pressure",
            "min_cost_input_quality",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_optional_probability_decimal(field_name, getattr(self, field_name)),
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


def build_research_strategy_forecast_consensus_health_report(
    inputs: Iterable[object],
    *,
    config: ResearchStrategyForecastConsensusHealthConfig,
    generated_at: datetime,
) -> ResearchStrategyForecastConsensusHealthReport:
    if type(config) is not ResearchStrategyForecastConsensusHealthConfig:
        raise ValueError(
            "config must be a ResearchStrategyForecastConsensusHealthConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_items = _normalize_inputs(inputs)
    rows = tuple(
        _health_row_from_input(item, config=config)
        for item in sorted(input_items, key=lambda item: item.consensus_scope_label)
    )
    reason_codes = _summary_reason_codes(rows)
    return ResearchStrategyForecastConsensusHealthReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        scope_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        average_consensus_health_score=_average_consensus_health_score(rows),
        max_team_confidence_dispersion=_max_or_none(
            row.team_confidence_dispersion for row in rows
        ),
        max_calibration_drift=_max_or_none(row.calibration_drift for row in rows),
        min_evidence_freshness=_min_or_none(row.evidence_freshness for row in rows),
        max_contradiction_pressure=_max_or_none(
            row.contradiction_pressure for row in rows
        ),
        min_cost_input_quality=_min_or_none(row.cost_input_quality for row in rows),
        status=_summary_status(reason_codes),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_strategy_forecast_consensus_health_report_payload(
    report: ResearchStrategyForecastConsensusHealthReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategyForecastConsensusHealthReport:
        raise ValueError(
            "report must be a ResearchStrategyForecastConsensusHealthReport",
        )
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    return payload


def research_strategy_forecast_consensus_health_report_digest(
    report: ResearchStrategyForecastConsensusHealthReport,
) -> str:
    payload = research_strategy_forecast_consensus_health_report_payload(report)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _health_row_from_input(
    item: ResearchStrategyForecastConsensusHealthInput,
    *,
    config: ResearchStrategyForecastConsensusHealthConfig,
) -> ResearchStrategyForecastConsensusHealthRow:
    confidence_alignment_score = _inverse_score(item.team_confidence_dispersion)
    calibration_stability_score = _inverse_score(item.calibration_drift)
    evidence_freshness_score = item.evidence_freshness
    contradiction_resistance_score = _inverse_score(item.contradiction_pressure)
    cost_input_quality_score = item.cost_input_quality
    score = _consensus_health_score(
        confidence_alignment_score=confidence_alignment_score,
        calibration_stability_score=calibration_stability_score,
        evidence_freshness_score=evidence_freshness_score,
        contradiction_resistance_score=contradiction_resistance_score,
        cost_input_quality_score=cost_input_quality_score,
        config=config,
    )
    lowest_dimension_score = min(
        confidence_alignment_score,
        calibration_stability_score,
        evidence_freshness_score,
        contradiction_resistance_score,
        cost_input_quality_score,
    )
    status = _row_status(
        consensus_health_score=score,
        lowest_dimension_score=lowest_dimension_score,
        config=config,
    )
    return ResearchStrategyForecastConsensusHealthRow(
        consensus_scope_label=item.consensus_scope_label,
        team_confidence_dispersion=item.team_confidence_dispersion,
        calibration_drift=item.calibration_drift,
        evidence_freshness=item.evidence_freshness,
        contradiction_pressure=item.contradiction_pressure,
        cost_input_quality=item.cost_input_quality,
        confidence_alignment_score=confidence_alignment_score,
        calibration_stability_score=calibration_stability_score,
        evidence_freshness_score=evidence_freshness_score,
        contradiction_resistance_score=contradiction_resistance_score,
        cost_input_quality_score=cost_input_quality_score,
        consensus_health_score=score,
        lowest_dimension_score=lowest_dimension_score,
        status=status,
        reason_codes=_row_reason_codes(item, status=status, config=config),
    )


def _consensus_health_score(
    *,
    confidence_alignment_score: Decimal,
    calibration_stability_score: Decimal,
    evidence_freshness_score: Decimal,
    contradiction_resistance_score: Decimal,
    cost_input_quality_score: Decimal,
    config: ResearchStrategyForecastConsensusHealthConfig,
) -> Decimal:
    with localcontext() as context:
        context.prec = 28
        score = (
            confidence_alignment_score * config.confidence_alignment_weight
            + calibration_stability_score * config.calibration_stability_weight
            + evidence_freshness_score * config.evidence_freshness_weight
            + contradiction_resistance_score * config.contradiction_resistance_weight
            + cost_input_quality_score * config.cost_input_quality_weight
        )
    return _quantize(score)


def _row_status(
    *,
    consensus_health_score: Decimal,
    lowest_dimension_score: Decimal,
    config: ResearchStrategyForecastConsensusHealthConfig,
) -> str:
    if (
        consensus_health_score < config.watch_health_score
        or lowest_dimension_score < config.watch_dimension_score
    ):
        return "block"
    if (
        consensus_health_score < config.pass_health_score
        or lowest_dimension_score < config.pass_dimension_score
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    item: ResearchStrategyForecastConsensusHealthInput,
    *,
    status: str,
    config: ResearchStrategyForecastConsensusHealthConfig,
) -> tuple[str, ...]:
    codes = {
        f"forecast_consensus_health_{status}",
        f"report_only_consensus_health_{status}",
        f"confidence_dispersion_{_pressure_status(item.team_confidence_dispersion, config)}",
        f"calibration_drift_{_pressure_status(item.calibration_drift, config)}",
        f"contradiction_pressure_{_pressure_status(item.contradiction_pressure, config)}",
        f"evidence_freshness_{_quality_status(item.evidence_freshness, config)}",
        f"cost_input_quality_{_quality_status(item.cost_input_quality, config)}",
    }
    for code in item.reason_codes:
        codes.add(f"input_{code}")
    return tuple(sorted(codes))


def _pressure_status(
    value: Decimal,
    config: ResearchStrategyForecastConsensusHealthConfig,
) -> str:
    if value >= config.watch_dimension_score:
        return "block"
    if value > ONE - config.pass_dimension_score:
        return "watch"
    return "pass"


def _quality_status(
    value: Decimal,
    config: ResearchStrategyForecastConsensusHealthConfig,
) -> str:
    if value < config.watch_dimension_score:
        return "block"
    if value < config.pass_dimension_score:
        return "watch"
    return "pass"


def _normalize_inputs(
    inputs: Iterable[object],
) -> tuple[ResearchStrategyForecastConsensusHealthInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        values = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    return tuple(_coerce_input(value) for value in values)


def _coerce_input(value: object) -> ResearchStrategyForecastConsensusHealthInput:
    if type(value) is ResearchStrategyForecastConsensusHealthInput:
        _require_hard_flags("input", value)
        return value
    _require_hard_flags("input", value)
    return ResearchStrategyForecastConsensusHealthInput(
        consensus_scope_label=_field_value(value, "consensus_scope_label"),
        team_confidence_dispersion=_field_value(value, "team_confidence_dispersion"),
        calibration_drift=_field_value(value, "calibration_drift"),
        evidence_freshness=_field_value(value, "evidence_freshness"),
        contradiction_pressure=_field_value(value, "contradiction_pressure"),
        cost_input_quality=_field_value(value, "cost_input_quality"),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _summary_reason_codes(
    rows: tuple[ResearchStrategyForecastConsensusHealthRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_forecast_consensus_health_inputs",)
    if all(row.status == "pass" for row in rows):
        return ("forecast_consensus_health_pass",)
    return tuple(sorted({code for row in rows for code in row.reason_codes}))


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("no_forecast_consensus_health_inputs",):
        return "block"
    if "forecast_consensus_health_block" in reason_codes:
        return "block"
    if "forecast_consensus_health_watch" in reason_codes:
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchStrategyForecastConsensusHealthRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchStrategyForecastConsensusHealthReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategyForecastConsensusHealthReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        ResearchStrategyForecastConsensusHealthReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counter.items(), key=lambda item: item[0])
    )


def _average_consensus_health_score(
    rows: tuple[ResearchStrategyForecastConsensusHealthRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(
        sum((row.consensus_health_score for row in rows), ZERO) / Decimal(len(rows)),
    )


def _status_count(
    rows: tuple[ResearchStrategyForecastConsensusHealthRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _max_or_none(values: Iterable[Decimal]) -> Decimal | None:
    items = tuple(values)
    if not items:
        return None
    return max(items)


def _min_or_none(values: Iterable[Decimal]) -> Decimal | None:
    items = tuple(values)
    if not items:
        return None
    return min(items)


def _normalize_rows(
    rows: tuple[ResearchStrategyForecastConsensusHealthRow, ...],
) -> tuple[ResearchStrategyForecastConsensusHealthRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchStrategyForecastConsensusHealthRow:
            raise ValueError(
                "rows must contain ResearchStrategyForecastConsensusHealthRow values",
            )
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.consensus_scope_label))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by consensus_scope_label")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchStrategyForecastConsensusHealthReasonCodeCount, ...],
) -> tuple[ResearchStrategyForecastConsensusHealthReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchStrategyForecastConsensusHealthReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyForecastConsensusHealthReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_row_consistency(
    row: ResearchStrategyForecastConsensusHealthRow,
) -> None:
    if row.confidence_alignment_score != _inverse_score(row.team_confidence_dispersion):
        raise ValueError("confidence_alignment_score must match team_confidence_dispersion")
    if row.calibration_stability_score != _inverse_score(row.calibration_drift):
        raise ValueError("calibration_stability_score must match calibration_drift")
    if row.evidence_freshness_score != row.evidence_freshness:
        raise ValueError("evidence_freshness_score must match evidence_freshness")
    if row.contradiction_resistance_score != _inverse_score(row.contradiction_pressure):
        raise ValueError("contradiction_resistance_score must match contradiction_pressure")
    if row.cost_input_quality_score != row.cost_input_quality:
        raise ValueError("cost_input_quality_score must match cost_input_quality")
    calculated_lowest = min(
        row.confidence_alignment_score,
        row.calibration_stability_score,
        row.evidence_freshness_score,
        row.contradiction_resistance_score,
        row.cost_input_quality_score,
    )
    if row.lowest_dimension_score != calculated_lowest:
        raise ValueError("lowest_dimension_score must match dimensions")
    highest_dimension = max(
        row.confidence_alignment_score,
        row.calibration_stability_score,
        row.evidence_freshness_score,
        row.contradiction_resistance_score,
        row.cost_input_quality_score,
    )
    if (
        row.consensus_health_score < row.lowest_dimension_score
        or row.consensus_health_score > highest_dimension
    ):
        raise ValueError("consensus_health_score must stay within dimension bounds")
    expected_code = f"forecast_consensus_health_{row.status}"
    if expected_code not in row.reason_codes:
        raise ValueError("status must match reason_codes")


def _validate_report_consistency(
    report: ResearchStrategyForecastConsensusHealthReport,
) -> None:
    if report.scope_count != _decimal_count(len(report.rows)):
        raise ValueError("scope_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_consensus_health_score != _average_consensus_health_score(report.rows):
        raise ValueError("average_consensus_health_score must match rows")
    if report.max_team_confidence_dispersion != _max_or_none(
        row.team_confidence_dispersion for row in report.rows
    ):
        raise ValueError("max_team_confidence_dispersion must match rows")
    if report.max_calibration_drift != _max_or_none(
        row.calibration_drift for row in report.rows
    ):
        raise ValueError("max_calibration_drift must match rows")
    if report.min_evidence_freshness != _min_or_none(
        row.evidence_freshness for row in report.rows
    ):
        raise ValueError("min_evidence_freshness must match rows")
    if report.max_contradiction_pressure != _max_or_none(
        row.contradiction_pressure for row in report.rows
    ):
        raise ValueError("max_contradiction_pressure must match rows")
    if report.min_cost_input_quality != _min_or_none(
        row.cost_input_quality for row in report.rows
    ):
        raise ValueError("min_cost_input_quality must match rows")
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


def _inverse_score(value: Decimal) -> Decimal:
    return _quantize(ONE - value)


def _config_weight_sum(config: ResearchStrategyForecastConsensusHealthConfig) -> Decimal:
    return _quantize(
        config.confidence_alignment_weight
        + config.calibration_stability_weight
        + config.evidence_freshness_weight
        + config.contradiction_resistance_weight
        + config.cost_input_quality_weight,
    )


def _require_public_label(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty public label")
    lowered = value.lower()
    for fragment in (
        "raw",
        "event_id",
        "event_slug",
        "market_id",
        "market_slug",
        "condition_id",
        "token_id",
        "source_id",
        "source_url",
        "source_reference",
    ):
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
