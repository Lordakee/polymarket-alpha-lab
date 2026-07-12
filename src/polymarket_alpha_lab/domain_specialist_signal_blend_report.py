"""Read-only domain specialist probability signal blend report."""

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
    "DEFAULT_DOMAIN_SPECIALIST_SIGNAL_BLEND_REPORT_CONFIG_VERSION",
    "DomainSpecialistSignalBlendConfig",
    "DomainSpecialistSignalBlendInput",
    "DomainSpecialistSignalBlendReasonCodeCount",
    "DomainSpecialistSignalBlendReport",
    "DomainSpecialistSignalBlendRow",
    "build_domain_specialist_signal_blend_report",
    "domain_specialist_signal_blend_report_digest",
    "domain_specialist_signal_blend_report_payload",
)


DEFAULT_DOMAIN_SPECIALIST_SIGNAL_BLEND_REPORT_CONFIG_VERSION = (
    "domain-specialist-signal-blend-report-v0"
)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
RATIO_QUANTUM = Decimal("0.000001")
STATUS_VALUES = ("pass", "watch", "block")
EMPTY_REASON = "no_domain_specialist_probability_signals"
COMPONENT_REASON_PRIORITY = (
    "domain_specialist_signal_blend_pass",
    "domain_specialist_signal_blend_block",
    "team_calibration_confidence_block",
    "source_reliability_score_block",
    "cost_burden_ratio_block",
    "team_calibration_confidence_watch",
    "source_reliability_score_watch",
    "cost_burden_ratio_watch",
    "team_market_divergence_attention",
)


@dataclass(frozen=True)
class DomainSpecialistSignalBlendConfig:
    config_version: str = DEFAULT_DOMAIN_SPECIALIST_SIGNAL_BLEND_REPORT_CONFIG_VERSION
    min_pass_team_calibration_confidence: Decimal = Decimal("0.750000")
    min_watch_team_calibration_confidence: Decimal = Decimal("0.500000")
    min_pass_source_reliability_score: Decimal = Decimal("0.700000")
    min_watch_source_reliability_score: Decimal = Decimal("0.450000")
    max_pass_cost_burden_ratio: Decimal = Decimal("0.080000")
    max_watch_cost_burden_ratio: Decimal = Decimal("0.200000")
    team_signal_weight: Decimal = Decimal("0.500000")
    baseline_signal_weight: Decimal = Decimal("0.300000")
    market_signal_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, DomainSpecialistSignalBlendConfig, "config")
        _require_public_label("config_version", self.config_version)
        if self.config_version != DEFAULT_DOMAIN_SPECIALIST_SIGNAL_BLEND_REPORT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_pass_team_calibration_confidence",
            "min_watch_team_calibration_confidence",
            "min_pass_source_reliability_score",
            "min_watch_source_reliability_score",
            "max_pass_cost_burden_ratio",
            "max_watch_cost_burden_ratio",
            "team_signal_weight",
            "baseline_signal_weight",
            "market_signal_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if (
            self.min_watch_team_calibration_confidence
            > self.min_pass_team_calibration_confidence
        ):
            raise ValueError("watch team calibration threshold must not exceed pass")
        if self.min_watch_source_reliability_score > self.min_pass_source_reliability_score:
            raise ValueError("watch source reliability threshold must not exceed pass")
        if self.max_pass_cost_burden_ratio > self.max_watch_cost_burden_ratio:
            raise ValueError("pass cost burden threshold must not exceed watch")
        if _weight_sum(self) != ONE:
            raise ValueError("signal blend weights must sum to one")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class DomainSpecialistSignalBlendInput:
    signal_ref: str
    specialist_team: str
    domain: str
    team_forecast_probability: Decimal
    baseline_probability: Decimal
    market_probability: Decimal
    team_calibration_confidence: Decimal
    source_reliability_score: Decimal
    cost_burden_ratio: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, DomainSpecialistSignalBlendInput, "input")
        _require_public_label("signal_ref", self.signal_ref)
        _require_public_label("specialist_team", self.specialist_team)
        _require_public_label("domain", self.domain)
        for field_name in (
            "team_forecast_probability",
            "baseline_probability",
            "market_probability",
            "team_calibration_confidence",
            "source_reliability_score",
            "cost_burden_ratio",
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
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class DomainSpecialistSignalBlendRow:
    signal_ref: str
    specialist_team: str
    domain: str
    team_forecast_probability: Decimal
    baseline_probability: Decimal
    market_probability: Decimal
    team_calibration_confidence: Decimal
    source_reliability_score: Decimal
    cost_burden_ratio: Decimal
    blended_probability: Decimal
    blend_weight: Decimal
    confidence_band: Decimal
    observed_at: datetime
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, DomainSpecialistSignalBlendRow, "row")
        _require_public_label("signal_ref", self.signal_ref)
        _require_public_label("specialist_team", self.specialist_team)
        _require_public_label("domain", self.domain)
        for field_name in (
            "team_forecast_probability",
            "baseline_probability",
            "market_probability",
            "team_calibration_confidence",
            "source_reliability_score",
            "cost_burden_ratio",
            "blended_probability",
            "blend_weight",
            "confidence_band",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class DomainSpecialistSignalBlendReasonCodeCount:
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
class DomainSpecialistSignalBlendReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_blended_probability: Decimal | None
    average_blend_weight: Decimal | None
    max_confidence_band: Decimal
    status: str
    rows: tuple[DomainSpecialistSignalBlendRow, ...]
    reason_code_counts: tuple[DomainSpecialistSignalBlendReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, DomainSpecialistSignalBlendReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        if self.config_version != DEFAULT_DOMAIN_SPECIALIST_SIGNAL_BLEND_REPORT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in ("input_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_blended_probability",
            _require_optional_ratio_decimal(
                "average_blended_probability",
                self.average_blended_probability,
            ),
        )
        object.__setattr__(
            self,
            "average_blend_weight",
            _require_optional_ratio_decimal("average_blend_weight", self.average_blend_weight),
        )
        object.__setattr__(
            self,
            "max_confidence_band",
            _require_ratio_decimal("max_confidence_band", self.max_confidence_band),
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


def build_domain_specialist_signal_blend_report(
    inputs: Iterable[object],
    *,
    config: DomainSpecialistSignalBlendConfig,
    generated_at: datetime,
) -> DomainSpecialistSignalBlendReport:
    if type(config) is not DomainSpecialistSignalBlendConfig:
        raise ValueError("config must be a DomainSpecialistSignalBlendConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_items = _normalize_inputs(inputs)
    for item in input_items:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")
    rows = tuple(
        _row_from_input(item, config=config)
        for item in sorted(input_items, key=lambda item: (item.signal_ref, item.domain))
    )
    reason_codes = _summary_reason_codes(rows)
    return DomainSpecialistSignalBlendReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        average_blended_probability=_average_row_value(rows, "blended_probability"),
        average_blend_weight=_average_row_value(rows, "blend_weight"),
        max_confidence_band=_maximum_row_value(rows, "confidence_band"),
        status=_summary_status(reason_codes),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def domain_specialist_signal_blend_report_payload(
    report: DomainSpecialistSignalBlendReport,
) -> dict[str, Any]:
    if type(report) is not DomainSpecialistSignalBlendReport:
        raise ValueError("report must be a DomainSpecialistSignalBlendReport")
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    return payload


def domain_specialist_signal_blend_report_digest(
    report: DomainSpecialistSignalBlendReport,
) -> str:
    payload = domain_specialist_signal_blend_report_payload(report)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _row_from_input(
    item: DomainSpecialistSignalBlendInput,
    *,
    config: DomainSpecialistSignalBlendConfig,
) -> DomainSpecialistSignalBlendRow:
    blended_probability = _blended_probability(item, config)
    blend_weight = _blend_weight(item)
    confidence_band = _confidence_band(item)
    status = _row_status(item, config=config)
    return DomainSpecialistSignalBlendRow(
        signal_ref=item.signal_ref,
        specialist_team=item.specialist_team,
        domain=item.domain,
        team_forecast_probability=item.team_forecast_probability,
        baseline_probability=item.baseline_probability,
        market_probability=item.market_probability,
        team_calibration_confidence=item.team_calibration_confidence,
        source_reliability_score=item.source_reliability_score,
        cost_burden_ratio=item.cost_burden_ratio,
        blended_probability=blended_probability,
        blend_weight=blend_weight,
        confidence_band=confidence_band,
        observed_at=item.observed_at,
        status=status,
        reason_codes=_row_reason_codes(item, status=status, config=config),
    )


def _blended_probability(
    item: DomainSpecialistSignalBlendInput,
    config: DomainSpecialistSignalBlendConfig,
) -> Decimal:
    with localcontext() as context:
        context.prec = 28
        blended = (
            item.team_forecast_probability * config.team_signal_weight
            + item.baseline_probability * config.baseline_signal_weight
            + item.market_probability * config.market_signal_weight
        )
    return _quantize(blended)


def _blend_weight(item: DomainSpecialistSignalBlendInput) -> Decimal:
    with localcontext() as context:
        context.prec = 28
        weight = (
            item.team_calibration_confidence
            * item.source_reliability_score
            * (ONE - item.cost_burden_ratio)
        )
    return _quantize(weight)


def _confidence_band(item: DomainSpecialistSignalBlendInput) -> Decimal:
    values = (
        item.team_forecast_probability,
        item.baseline_probability,
        item.market_probability,
    )
    return _quantize(max(values) - min(values))


def _row_status(
    item: DomainSpecialistSignalBlendInput,
    *,
    config: DomainSpecialistSignalBlendConfig,
) -> str:
    if (
        item.team_calibration_confidence < config.min_watch_team_calibration_confidence
        or item.source_reliability_score < config.min_watch_source_reliability_score
        or item.cost_burden_ratio > config.max_watch_cost_burden_ratio
    ):
        return "block"
    if (
        item.team_calibration_confidence < config.min_pass_team_calibration_confidence
        or item.source_reliability_score < config.min_pass_source_reliability_score
        or item.cost_burden_ratio > config.max_pass_cost_burden_ratio
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    item: DomainSpecialistSignalBlendInput,
    *,
    status: str,
    config: DomainSpecialistSignalBlendConfig,
) -> tuple[str, ...]:
    codes = {
        f"domain_specialist_signal_blend_{status}",
        f"manual_review_domain_specialist_signal_blend_{status}",
    }
    codes.update(f"input_{code}" for code in item.reason_codes)
    calibration_status = _minimum_threshold_status(
        item.team_calibration_confidence,
        pass_threshold=config.min_pass_team_calibration_confidence,
        watch_threshold=config.min_watch_team_calibration_confidence,
    )
    source_status = _minimum_threshold_status(
        item.source_reliability_score,
        pass_threshold=config.min_pass_source_reliability_score,
        watch_threshold=config.min_watch_source_reliability_score,
    )
    cost_status = _maximum_threshold_status(
        item.cost_burden_ratio,
        pass_threshold=config.max_pass_cost_burden_ratio,
        watch_threshold=config.max_watch_cost_burden_ratio,
    )
    if calibration_status != "pass":
        codes.add(f"team_calibration_confidence_{calibration_status}")
    if source_status != "pass":
        codes.add(f"source_reliability_score_{source_status}")
    if cost_status != "pass":
        codes.add(f"cost_burden_ratio_{cost_status}")
    if abs(item.team_forecast_probability - item.market_probability) >= Decimal("0.200000"):
        codes.add("team_market_divergence_attention")
    if status == "pass":
        codes.discard("manual_review_domain_specialist_signal_blend_pass")
    return _sort_reason_codes(codes)


def _minimum_threshold_status(
    value: Decimal,
    *,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> str:
    if value < watch_threshold:
        return "block"
    if value < pass_threshold:
        return "watch"
    return "pass"


def _maximum_threshold_status(
    value: Decimal,
    *,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> str:
    if value > watch_threshold:
        return "block"
    if value > pass_threshold:
        return "watch"
    return "pass"


def _summary_reason_codes(
    rows: tuple[DomainSpecialistSignalBlendRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    reason_codes = {code for row in rows for code in row.reason_codes}
    if any(
        code.endswith("_block")
        or code.endswith("_watch")
        or code.endswith("_attention")
        for code in reason_codes
    ):
        reason_codes.discard("domain_specialist_signal_blend_pass")
    return tuple(
        code
        for code in COMPONENT_REASON_PRIORITY
        if code in reason_codes
    )


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if EMPTY_REASON in reason_codes:
        return "block"
    if any(code.endswith("_block") for code in reason_codes):
        return "block"
    if any(code.endswith("_watch") or code.endswith("_attention") for code in reason_codes):
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[DomainSpecialistSignalBlendRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[DomainSpecialistSignalBlendReasonCodeCount, ...]:
    if not rows:
        return (
            DomainSpecialistSignalBlendReasonCodeCount(
                reason_code=EMPTY_REASON,
                count=_decimal_count(1),
                row_ratio=ZERO,
            ),
        )
    counts = Counter(code for row in rows for code in row.reason_codes)
    row_count = _decimal_count(len(rows))
    return tuple(
        DomainSpecialistSignalBlendReasonCodeCount(
            reason_code=code,
            count=_decimal_count(counts[code]),
            row_ratio=_safe_ratio(_decimal_count(counts[code]), row_count),
        )
        for code in reason_codes
    )


def _validate_row_consistency(row: DomainSpecialistSignalBlendRow) -> None:
    if row.blended_probability != _quantize(
        row.team_forecast_probability * Decimal("0.500000")
        + row.baseline_probability * Decimal("0.300000")
        + row.market_probability * Decimal("0.200000"),
    ):
        raise ValueError("blended_probability must match signal blend formula")
    if row.blend_weight != _quantize(
        row.team_calibration_confidence
        * row.source_reliability_score
        * (ONE - row.cost_burden_ratio),
    ):
        raise ValueError("blend_weight must match confidence and reliability formula")
    if row.confidence_band != _quantize(
        max(
            row.team_forecast_probability,
            row.baseline_probability,
            row.market_probability,
        )
        - min(
            row.team_forecast_probability,
            row.baseline_probability,
            row.market_probability,
        ),
    ):
        raise ValueError("confidence_band must match probability spread")
    has_block = any(code.endswith("_block") for code in row.reason_codes)
    has_watch = any(
        code.endswith("_watch") or code.endswith("_attention")
        for code in row.reason_codes
    )
    if row.status == "block" and not has_block:
        raise ValueError("block row reason_codes must include a blocker")
    if row.status == "watch" and (has_block or not has_watch):
        raise ValueError("watch row reason_codes must include attention without blocker")
    if row.status == "pass" and (has_block or has_watch):
        raise ValueError("pass row reason_codes must not include blockers or attention")


def _validate_report_consistency(report: DomainSpecialistSignalBlendReport) -> None:
    rows = report.rows
    if tuple(sorted(rows, key=lambda row: (row.signal_ref, row.domain))) != rows:
        raise ValueError("rows must be sorted by signal_ref and domain")
    if report.input_count != _decimal_count(len(rows)):
        raise ValueError("input_count must equal row count")
    for status in STATUS_VALUES:
        expected = _decimal_count(_status_count(rows, status))
        if getattr(report, f"{status}_count") != expected:
            raise ValueError(f"{status}_count must equal rows with status")
    if report.average_blended_probability != _average_row_value(rows, "blended_probability"):
        raise ValueError("average_blended_probability must equal row average")
    if report.average_blend_weight != _average_row_value(rows, "blend_weight"):
        raise ValueError("average_blend_weight must equal row average")
    if report.max_confidence_band != _maximum_row_value(rows, "confidence_band"):
        raise ValueError("max_confidence_band must equal max row confidence_band")
    if report.reason_codes != _summary_reason_codes(rows):
        raise ValueError("reason_codes must summarize rows")
    if report.reason_code_counts != _reason_code_counts(rows, report.reason_codes):
        raise ValueError("reason_code_counts must summarize rows")
    if report.status != _summary_status(report.reason_codes):
        raise ValueError("status must summarize reasons")


def _normalize_inputs(values: Iterable[object]) -> tuple[DomainSpecialistSignalBlendInput, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("inputs must be an iterable of DomainSpecialistSignalBlendInput")
    normalized: list[DomainSpecialistSignalBlendInput] = []
    for value in values:
        if type(value) is not DomainSpecialistSignalBlendInput:
            raise ValueError("inputs must contain DomainSpecialistSignalBlendInput values")
        _require_hard_flags("input", value)
        normalized.append(value)
    return tuple(normalized)


def _normalize_rows(values: object) -> tuple[DomainSpecialistSignalBlendRow, ...]:
    if type(values) is not tuple:
        raise ValueError("rows must be a tuple")
    for value in values:
        if type(value) is not DomainSpecialistSignalBlendRow:
            raise ValueError("rows must contain DomainSpecialistSignalBlendRow values")
        _require_hard_flags("row", value)
    return values


def _normalize_reason_code_counts(
    values: object,
) -> tuple[DomainSpecialistSignalBlendReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for value in values:
        if type(value) is not DomainSpecialistSignalBlendReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain DomainSpecialistSignalBlendReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", value)
    return values


def _sort_reason_codes(values: set[str]) -> tuple[str, ...]:
    return tuple(sorted(values, key=lambda code: (_reason_sort_key(code), code)))


def _reason_sort_key(code: str) -> int:
    if code in COMPONENT_REASON_PRIORITY:
        return COMPONENT_REASON_PRIORITY.index(code)
    if code.startswith("input_"):
        return 100
    if code.startswith("manual_review_"):
        return 90
    return 80


def _average_row_value(
    rows: tuple[DomainSpecialistSignalBlendRow, ...],
    field_name: str,
) -> Decimal | None:
    if not rows:
        return None
    total = sum((getattr(row, field_name) for row in rows), ZERO)
    return _safe_ratio(total, _decimal_count(len(rows)))


def _maximum_row_value(
    rows: tuple[DomainSpecialistSignalBlendRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _status_count(rows: tuple[DomainSpecialistSignalBlendRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _weight_sum(config: DomainSpecialistSignalBlendConfig) -> Decimal:
    return _quantize(
        config.team_signal_weight
        + config.baseline_signal_weight
        + config.market_signal_weight,
    )


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext() as context:
        context.prec = 28
        result = numerator / denominator
    return _quantize(result)


def _payload_value(value: object) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime or value.tzinfo is None:
        raise ValueError(f"{field_name} must be a timezone-aware datetime")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be a {expected_type.__name__}")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} {flag_name} must be True")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    try:
        if not value.is_finite():
            raise ValueError(f"{field_name} must be finite")
        return value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _require_optional_ratio_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_ratio_decimal(field_name, value)


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


def _require_status(field_name: str, value: object) -> None:
    if value not in STATUS_VALUES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


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
