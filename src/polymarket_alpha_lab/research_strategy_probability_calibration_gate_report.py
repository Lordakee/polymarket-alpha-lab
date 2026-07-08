"""Pure aggregate probability calibration gate report."""

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
    "CALIBRATION_GATE_STATUSES",
    "DEFAULT_RESEARCH_STRATEGY_PROBABILITY_CALIBRATION_GATE_REPORT_CONFIG_VERSION",
    "ResearchStrategyProbabilityCalibrationGateConfig",
    "ResearchStrategyProbabilityCalibrationGateInput",
    "ResearchStrategyProbabilityCalibrationGateReasonCodeCount",
    "ResearchStrategyProbabilityCalibrationGateReport",
    "ResearchStrategyProbabilityCalibrationGateRow",
    "build_research_strategy_probability_calibration_gate_report",
    "research_strategy_probability_calibration_gate_report_digest",
    "research_strategy_probability_calibration_gate_report_payload",
)


DEFAULT_RESEARCH_STRATEGY_PROBABILITY_CALIBRATION_GATE_REPORT_CONFIG_VERSION = (
    "research-strategy-probability-calibration-gate-report-v0"
)
CALIBRATION_GATE_STATUSES = ("pass", "watch", "block")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
RATIO_QUANTUM = Decimal("0.000001")
COMPONENT_REASON_PRIORITY = (
    "prior_calibration_bucket_quality_block",
    "evidence_confidence_block",
    "disagreement_pressure_block",
    "stale_estimate_risk_block",
    "prior_calibration_bucket_quality_watch",
    "evidence_confidence_watch",
    "disagreement_pressure_watch",
    "stale_estimate_risk_watch",
)


class _Missing:
    pass


_MISSING = _Missing()


@dataclass(frozen=True)
class ResearchStrategyProbabilityCalibrationGateConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_PROBABILITY_CALIBRATION_GATE_REPORT_CONFIG_VERSION
    )
    min_pass_prior_calibration_bucket_quality: Decimal = Decimal("0.750000")
    min_watch_prior_calibration_bucket_quality: Decimal = Decimal("0.500000")
    min_pass_evidence_confidence: Decimal = Decimal("0.700000")
    min_watch_evidence_confidence: Decimal = Decimal("0.450000")
    max_pass_disagreement_pressure: Decimal = Decimal("0.150000")
    max_watch_disagreement_pressure: Decimal = Decimal("0.350000")
    max_pass_stale_estimate_age_seconds: Decimal = Decimal("86400.000000")
    max_watch_stale_estimate_age_seconds: Decimal = Decimal("259200.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyProbabilityCalibrationGateConfig,
            "config",
        )
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_PROBABILITY_CALIBRATION_GATE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_pass_prior_calibration_bucket_quality",
            "min_watch_prior_calibration_bucket_quality",
            "min_pass_evidence_confidence",
            "min_watch_evidence_confidence",
            "max_pass_disagreement_pressure",
            "max_watch_disagreement_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_stale_estimate_age_seconds",
            "max_watch_stale_estimate_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if (
            self.min_watch_prior_calibration_bucket_quality
            > self.min_pass_prior_calibration_bucket_quality
        ):
            raise ValueError("watch prior calibration threshold must not exceed pass")
        if self.min_watch_evidence_confidence > self.min_pass_evidence_confidence:
            raise ValueError("watch evidence confidence threshold must not exceed pass")
        if self.max_pass_disagreement_pressure > self.max_watch_disagreement_pressure:
            raise ValueError("pass disagreement threshold must not exceed watch")
        if (
            self.max_pass_stale_estimate_age_seconds
            > self.max_watch_stale_estimate_age_seconds
        ):
            raise ValueError("pass stale estimate threshold must not exceed watch")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyProbabilityCalibrationGateInput:
    research_key: str
    calibration_bucket_label: str
    prior_calibration_bucket_quality: Decimal
    evidence_confidence: Decimal
    disagreement_pressure: Decimal
    estimate_age_seconds: Decimal
    sample_count: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyProbabilityCalibrationGateInput,
            "input",
        )
        _require_public_label("research_key", self.research_key)
        _require_public_label("calibration_bucket_label", self.calibration_bucket_label)
        for field_name in (
            "prior_calibration_bucket_quality",
            "evidence_confidence",
            "disagreement_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "estimate_age_seconds",
            _require_nonnegative_decimal(
                "estimate_age_seconds",
                self.estimate_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "sample_count",
            _require_nonnegative_whole_decimal("sample_count", self.sample_count),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyProbabilityCalibrationGateRow:
    research_key: str
    calibration_bucket_label: str
    prior_calibration_bucket_quality: Decimal
    evidence_confidence: Decimal
    disagreement_pressure: Decimal
    estimate_age_seconds: Decimal
    sample_count: Decimal
    stale_estimate_risk: Decimal
    calibration_readiness_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyProbabilityCalibrationGateRow,
            "row",
        )
        _require_public_label("research_key", self.research_key)
        _require_public_label("calibration_bucket_label", self.calibration_bucket_label)
        for field_name in (
            "prior_calibration_bucket_quality",
            "evidence_confidence",
            "disagreement_pressure",
            "stale_estimate_risk",
            "calibration_readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "estimate_age_seconds",
            _require_nonnegative_decimal(
                "estimate_age_seconds",
                self.estimate_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "sample_count",
            _require_nonnegative_whole_decimal("sample_count", self.sample_count),
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
class ResearchStrategyProbabilityCalibrationGateReasonCodeCount:
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
class ResearchStrategyProbabilityCalibrationGateReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_calibration_readiness_score: Decimal | None
    min_prior_calibration_bucket_quality: Decimal
    min_evidence_confidence: Decimal
    max_disagreement_pressure: Decimal
    max_stale_estimate_risk: Decimal
    status: str
    rows: tuple[ResearchStrategyProbabilityCalibrationGateRow, ...]
    reason_code_counts: tuple[
        ResearchStrategyProbabilityCalibrationGateReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyProbabilityCalibrationGateReport,
            "report",
        )
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
            "average_calibration_readiness_score",
            _require_optional_ratio_decimal(
                "average_calibration_readiness_score",
                self.average_calibration_readiness_score,
            ),
        )
        for field_name in (
            "min_prior_calibration_bucket_quality",
            "min_evidence_confidence",
            "max_disagreement_pressure",
            "max_stale_estimate_risk",
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


def build_research_strategy_probability_calibration_gate_report(
    inputs: Iterable[object],
    *,
    config: ResearchStrategyProbabilityCalibrationGateConfig,
    generated_at: datetime,
) -> ResearchStrategyProbabilityCalibrationGateReport:
    if type(config) is not ResearchStrategyProbabilityCalibrationGateConfig:
        raise ValueError(
            "config must be a ResearchStrategyProbabilityCalibrationGateConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_items = _normalize_inputs(inputs)
    rows = tuple(
        _row_from_input(item, config=config)
        for item in sorted(
            input_items,
            key=lambda item: (item.research_key, item.calibration_bucket_label),
        )
    )
    reason_codes = _summary_reason_codes(rows)
    return ResearchStrategyProbabilityCalibrationGateReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        average_calibration_readiness_score=_average_readiness_score(rows),
        min_prior_calibration_bucket_quality=_minimum_row_value(
            rows,
            "prior_calibration_bucket_quality",
        ),
        min_evidence_confidence=_minimum_row_value(rows, "evidence_confidence"),
        max_disagreement_pressure=_maximum_row_value(rows, "disagreement_pressure"),
        max_stale_estimate_risk=_maximum_row_value(rows, "stale_estimate_risk"),
        status=_summary_status(reason_codes),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_strategy_probability_calibration_gate_report_payload(
    report: ResearchStrategyProbabilityCalibrationGateReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategyProbabilityCalibrationGateReport:
        raise ValueError(
            "report must be a ResearchStrategyProbabilityCalibrationGateReport",
        )
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    return payload


def research_strategy_probability_calibration_gate_report_digest(
    report: ResearchStrategyProbabilityCalibrationGateReport,
) -> str:
    payload = research_strategy_probability_calibration_gate_report_payload(report)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _row_from_input(
    item: ResearchStrategyProbabilityCalibrationGateInput,
    *,
    config: ResearchStrategyProbabilityCalibrationGateConfig,
) -> ResearchStrategyProbabilityCalibrationGateRow:
    stale_estimate_risk = _stale_estimate_risk(item.estimate_age_seconds, config)
    calibration_readiness_score = _calibration_readiness_score(
        prior_calibration_bucket_quality=item.prior_calibration_bucket_quality,
        evidence_confidence=item.evidence_confidence,
        disagreement_pressure=item.disagreement_pressure,
        stale_estimate_risk=stale_estimate_risk,
    )
    status = _row_status(item, config=config)
    return ResearchStrategyProbabilityCalibrationGateRow(
        research_key=item.research_key,
        calibration_bucket_label=item.calibration_bucket_label,
        prior_calibration_bucket_quality=item.prior_calibration_bucket_quality,
        evidence_confidence=item.evidence_confidence,
        disagreement_pressure=item.disagreement_pressure,
        estimate_age_seconds=item.estimate_age_seconds,
        sample_count=item.sample_count,
        stale_estimate_risk=stale_estimate_risk,
        calibration_readiness_score=calibration_readiness_score,
        status=status,
        reason_codes=_row_reason_codes(item, status=status, config=config),
    )


def _stale_estimate_risk(
    estimate_age_seconds: Decimal,
    config: ResearchStrategyProbabilityCalibrationGateConfig,
) -> Decimal:
    with localcontext() as context:
        context.prec = 28
        risk = estimate_age_seconds / config.max_watch_stale_estimate_age_seconds
    if risk > ONE:
        return ONE
    return _quantize(risk)


def _calibration_readiness_score(
    *,
    prior_calibration_bucket_quality: Decimal,
    evidence_confidence: Decimal,
    disagreement_pressure: Decimal,
    stale_estimate_risk: Decimal,
) -> Decimal:
    with localcontext() as context:
        context.prec = 28
        score = (
            prior_calibration_bucket_quality
            + evidence_confidence
            + (ONE - disagreement_pressure)
            + (ONE - stale_estimate_risk)
        ) / Decimal("4")
    return _quantize(score)


def _row_status(
    item: ResearchStrategyProbabilityCalibrationGateInput,
    *,
    config: ResearchStrategyProbabilityCalibrationGateConfig,
) -> str:
    if (
        item.prior_calibration_bucket_quality
        < config.min_watch_prior_calibration_bucket_quality
        or item.evidence_confidence < config.min_watch_evidence_confidence
        or item.disagreement_pressure > config.max_watch_disagreement_pressure
        or item.estimate_age_seconds > config.max_watch_stale_estimate_age_seconds
    ):
        return "block"
    if (
        item.prior_calibration_bucket_quality
        < config.min_pass_prior_calibration_bucket_quality
        or item.evidence_confidence < config.min_pass_evidence_confidence
        or item.disagreement_pressure > config.max_pass_disagreement_pressure
        or item.estimate_age_seconds > config.max_pass_stale_estimate_age_seconds
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    item: ResearchStrategyProbabilityCalibrationGateInput,
    *,
    status: str,
    config: ResearchStrategyProbabilityCalibrationGateConfig,
) -> tuple[str, ...]:
    codes = {
        f"probability_calibration_gate_{status}",
        f"manual_review_probability_calibration_{status}",
        (
            "prior_calibration_bucket_quality_"
            f"{_quality_status(item.prior_calibration_bucket_quality, config)}"
        ),
        f"evidence_confidence_{_confidence_status(item.evidence_confidence, config)}",
        f"disagreement_pressure_{_pressure_status(item.disagreement_pressure, config)}",
        f"stale_estimate_risk_{_age_status(item.estimate_age_seconds, config)}",
    }
    for code in item.reason_codes:
        codes.add(f"input_{code}")
    return tuple(sorted(codes))


def _quality_status(
    value: Decimal,
    config: ResearchStrategyProbabilityCalibrationGateConfig,
) -> str:
    if value < config.min_watch_prior_calibration_bucket_quality:
        return "block"
    if value < config.min_pass_prior_calibration_bucket_quality:
        return "watch"
    return "pass"


def _confidence_status(
    value: Decimal,
    config: ResearchStrategyProbabilityCalibrationGateConfig,
) -> str:
    if value < config.min_watch_evidence_confidence:
        return "block"
    if value < config.min_pass_evidence_confidence:
        return "watch"
    return "pass"


def _pressure_status(
    value: Decimal,
    config: ResearchStrategyProbabilityCalibrationGateConfig,
) -> str:
    if value > config.max_watch_disagreement_pressure:
        return "block"
    if value > config.max_pass_disagreement_pressure:
        return "watch"
    return "pass"


def _age_status(
    value: Decimal,
    config: ResearchStrategyProbabilityCalibrationGateConfig,
) -> str:
    if value > config.max_watch_stale_estimate_age_seconds:
        return "block"
    if value > config.max_pass_stale_estimate_age_seconds:
        return "watch"
    return "pass"


def _normalize_inputs(
    inputs: Iterable[object],
) -> tuple[ResearchStrategyProbabilityCalibrationGateInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        values = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    return tuple(_coerce_input(value) for value in values)


def _coerce_input(value: object) -> ResearchStrategyProbabilityCalibrationGateInput:
    if type(value) is ResearchStrategyProbabilityCalibrationGateInput:
        _require_hard_flags("input", value)
        return value
    _require_hard_flags("input", value)
    return ResearchStrategyProbabilityCalibrationGateInput(
        research_key=_field_value(value, "research_key"),
        calibration_bucket_label=_field_value(value, "calibration_bucket_label"),
        prior_calibration_bucket_quality=_field_value(
            value,
            "prior_calibration_bucket_quality",
        ),
        evidence_confidence=_field_value(value, "evidence_confidence"),
        disagreement_pressure=_field_value(value, "disagreement_pressure"),
        estimate_age_seconds=_field_value(value, "estimate_age_seconds"),
        sample_count=_field_value(value, "sample_count"),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _summary_reason_codes(
    rows: tuple[ResearchStrategyProbabilityCalibrationGateRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_probability_calibration_inputs",)
    if all(row.status == "pass" for row in rows):
        return ("probability_calibration_gate_pass",)
    codes: list[str] = []
    if any(row.status == "block" for row in rows):
        codes.append("probability_calibration_gate_block")
    elif any(row.status == "watch" for row in rows):
        codes.append("probability_calibration_gate_watch")
    row_codes = {code for row in rows for code in row.reason_codes}
    for code in COMPONENT_REASON_PRIORITY:
        if code in row_codes:
            codes.append(code)
    return tuple(codes)


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("no_probability_calibration_inputs",):
        return "block"
    if "probability_calibration_gate_block" in reason_codes:
        return "block"
    if "probability_calibration_gate_watch" in reason_codes:
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchStrategyProbabilityCalibrationGateRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchStrategyProbabilityCalibrationGateReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategyProbabilityCalibrationGateReasonCodeCount(
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
        ResearchStrategyProbabilityCalibrationGateReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
            row_ratio=_quantize(Decimal(count) / row_count),
        )
        for reason_code, count in sorted(counter.items(), key=lambda item: item[0])
    )


def _average_readiness_score(
    rows: tuple[ResearchStrategyProbabilityCalibrationGateRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(
        sum((row.calibration_readiness_score for row in rows), ZERO)
        / Decimal(len(rows)),
    )


def _minimum_row_value(
    rows: tuple[ResearchStrategyProbabilityCalibrationGateRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return min(getattr(row, field_name) for row in rows)


def _maximum_row_value(
    rows: tuple[ResearchStrategyProbabilityCalibrationGateRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _status_count(
    rows: tuple[ResearchStrategyProbabilityCalibrationGateRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_rows(
    rows: tuple[ResearchStrategyProbabilityCalibrationGateRow, ...],
) -> tuple[ResearchStrategyProbabilityCalibrationGateRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchStrategyProbabilityCalibrationGateRow:
            raise ValueError(
                "rows must contain ResearchStrategyProbabilityCalibrationGateRow values",
            )
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.research_key))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by research_key")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchStrategyProbabilityCalibrationGateReasonCodeCount, ...],
) -> tuple[ResearchStrategyProbabilityCalibrationGateReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchStrategyProbabilityCalibrationGateReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyProbabilityCalibrationGateReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_row_consistency(
    row: ResearchStrategyProbabilityCalibrationGateRow,
) -> None:
    expected_score = _calibration_readiness_score(
        prior_calibration_bucket_quality=row.prior_calibration_bucket_quality,
        evidence_confidence=row.evidence_confidence,
        disagreement_pressure=row.disagreement_pressure,
        stale_estimate_risk=row.stale_estimate_risk,
    )
    if row.calibration_readiness_score != expected_score:
        raise ValueError("calibration_readiness_score must match components")
    expected_status_code = f"probability_calibration_gate_{row.status}"
    if expected_status_code not in row.reason_codes:
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and any(
        code.endswith(("_watch", "_block")) for code in row.reason_codes
    ):
        raise ValueError("status must match component reason_codes")
    if row.status == "watch" and any(
        code.endswith("_block") for code in row.reason_codes
    ):
        raise ValueError("status must match component reason_codes")


def _validate_report_consistency(
    report: ResearchStrategyProbabilityCalibrationGateReport,
) -> None:
    if report.input_count != _decimal_count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_calibration_readiness_score != _average_readiness_score(
        report.rows,
    ):
        raise ValueError("average_calibration_readiness_score must match rows")
    if report.min_prior_calibration_bucket_quality != _minimum_row_value(
        report.rows,
        "prior_calibration_bucket_quality",
    ):
        raise ValueError("min_prior_calibration_bucket_quality must match rows")
    if report.min_evidence_confidence != _minimum_row_value(
        report.rows,
        "evidence_confidence",
    ):
        raise ValueError("min_evidence_confidence must match rows")
    if report.max_disagreement_pressure != _maximum_row_value(
        report.rows,
        "disagreement_pressure",
    ):
        raise ValueError("max_disagreement_pressure must match rows")
    if report.max_stale_estimate_risk != _maximum_row_value(
        report.rows,
        "stale_estimate_risk",
    ):
        raise ValueError("max_stale_estimate_risk must match rows")
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
    if type(value) is not str or value not in CALIBRATION_GATE_STATUSES:
        raise ValueError(f"{field_name} must be one of {CALIBRATION_GATE_STATUSES}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")
