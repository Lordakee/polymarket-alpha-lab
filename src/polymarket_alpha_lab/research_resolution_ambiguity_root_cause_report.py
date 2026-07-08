"""Pure public report for resolution ambiguity root-cause pressure."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, localcontext
from hashlib import sha256
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


SCORE_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT_PRECISION = 28

STATUSES = ("pass", "watch", "block")
ROOT_CAUSES = (
    "rule_clarity_gap",
    "source_consistency_gap",
    "contradiction_pressure",
    "oracle_lag",
    "edge_case_pressure",
)
REASON_CODES = (
    "contradiction_pressure_high",
    "contradiction_pressure_low",
    "contradiction_pressure_watch",
    "edge_case_pressure_high",
    "edge_case_pressure_low",
    "edge_case_pressure_watch",
    "oracle_lag_high",
    "oracle_lag_low",
    "oracle_lag_watch",
    "resolution_ambiguity_root_cause_block",
    "resolution_ambiguity_root_cause_pass",
    "resolution_ambiguity_root_cause_watch",
    "rule_clarity_gap_high",
    "rule_clarity_gap_low",
    "rule_clarity_gap_watch",
    "source_consistency_gap_high",
    "source_consistency_gap_low",
    "source_consistency_gap_watch",
)
_DIGEST_FIELD = "derived_validation_digest"


@dataclass(frozen=True)
class ResearchResolutionAmbiguityRootCauseConfig:
    config_version: str
    watch_pressure_threshold: Decimal
    block_pressure_threshold: Decimal
    oracle_lag_block_minutes: Decimal
    edge_case_block_count: Decimal
    rule_clarity_weight: Decimal
    source_consistency_weight: Decimal
    contradiction_pressure_weight: Decimal
    oracle_lag_weight: Decimal
    edge_case_weight: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("watch_pressure_threshold", "block_pressure_threshold"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.watch_pressure_threshold >= self.block_pressure_threshold:
            raise ValueError(
                "watch_pressure_threshold must be < block_pressure_threshold",
            )
        object.__setattr__(
            self,
            "oracle_lag_block_minutes",
            _normalize_positive_decimal(
                "oracle_lag_block_minutes",
                self.oracle_lag_block_minutes,
            ),
        )
        object.__setattr__(
            self,
            "edge_case_block_count",
            _normalize_positive_count("edge_case_block_count", self.edge_case_block_count),
        )
        for field_name in (
            "rule_clarity_weight",
            "source_consistency_weight",
            "contradiction_pressure_weight",
            "oracle_lag_weight",
            "edge_case_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_config_weights_total_one(self)
        require_paper_only_flags("ResearchResolutionAmbiguityRootCauseConfig", self)
        reject_unsafe_surface_fields("ambiguity root cause config", self)


@dataclass(frozen=True)
class ResearchResolutionAmbiguityRootCauseAggregate:
    rule_clarity_score: Decimal
    source_consistency_score: Decimal
    contradiction_pressure_score: Decimal
    oracle_lag_minutes: Decimal
    edge_case_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "rule_clarity_score",
            "source_consistency_score",
            "contradiction_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "oracle_lag_minutes",
            _normalize_nonnegative_decimal("oracle_lag_minutes", self.oracle_lag_minutes),
        )
        object.__setattr__(
            self,
            "edge_case_count",
            _normalize_nonnegative_count("edge_case_count", self.edge_case_count),
        )
        require_paper_only_flags("ResearchResolutionAmbiguityRootCauseAggregate", self)
        reject_unsafe_surface_fields("ambiguity root cause aggregate", self)


@dataclass(frozen=True)
class ResearchResolutionAmbiguityRootCauseRow:
    root_cause: str
    aggregate_value: Decimal
    pressure_score: Decimal
    weight: Decimal
    weighted_pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_member("root_cause", self.root_cause, ROOT_CAUSES)
        object.__setattr__(
            self,
            "aggregate_value",
            _normalize_nonnegative_decimal("aggregate_value", self.aggregate_value),
        )
        for field_name in ("pressure_score", "weight", "weighted_pressure_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _validate_row(self)
        require_paper_only_flags("ResearchResolutionAmbiguityRootCauseRow", self)
        reject_unsafe_surface_fields("ambiguity root cause row", self)
        _require_or_set_digest(self)


@dataclass(frozen=True)
class ResearchResolutionAmbiguityRootCauseReport:
    generated_at: datetime
    config_version: str
    ambiguity_pressure_score: Decimal
    status: str
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    rows: tuple[ResearchResolutionAmbiguityRootCauseRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "ambiguity_pressure_score",
            _normalize_probability(
                "ambiguity_pressure_score",
                self.ambiguity_pressure_score,
            ),
        )
        _require_member("status", self.status, STATUSES)
        for field_name in ("pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _validate_report(self)
        require_paper_only_flags("ResearchResolutionAmbiguityRootCauseReport", self)
        reject_unsafe_surface_fields("ambiguity root cause report", self)
        _require_or_set_digest(self)


def build_research_resolution_ambiguity_root_cause_report(
    aggregate: object,
    *,
    config: ResearchResolutionAmbiguityRootCauseConfig,
    generated_at: datetime,
) -> ResearchResolutionAmbiguityRootCauseReport:
    if type(config) is not ResearchResolutionAmbiguityRootCauseConfig:
        raise ValueError("config must be a ResearchResolutionAmbiguityRootCauseConfig")
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    aggregate_metrics = _coerce_aggregate(aggregate)
    rows = (
        _root_cause_row(
            root_cause="rule_clarity_gap",
            aggregate_value=aggregate_metrics.rule_clarity_score,
            pressure_score=ONE - aggregate_metrics.rule_clarity_score,
            weight=config.rule_clarity_weight,
            config=config,
        ),
        _root_cause_row(
            root_cause="source_consistency_gap",
            aggregate_value=aggregate_metrics.source_consistency_score,
            pressure_score=ONE - aggregate_metrics.source_consistency_score,
            weight=config.source_consistency_weight,
            config=config,
        ),
        _root_cause_row(
            root_cause="contradiction_pressure",
            aggregate_value=aggregate_metrics.contradiction_pressure_score,
            pressure_score=aggregate_metrics.contradiction_pressure_score,
            weight=config.contradiction_pressure_weight,
            config=config,
        ),
        _root_cause_row(
            root_cause="oracle_lag",
            aggregate_value=aggregate_metrics.oracle_lag_minutes,
            pressure_score=_ratio_pressure(
                aggregate_metrics.oracle_lag_minutes,
                config.oracle_lag_block_minutes,
            ),
            weight=config.oracle_lag_weight,
            config=config,
        ),
        _root_cause_row(
            root_cause="edge_case_pressure",
            aggregate_value=aggregate_metrics.edge_case_count,
            pressure_score=_ratio_pressure(
                aggregate_metrics.edge_case_count,
                config.edge_case_block_count,
            ),
            weight=config.edge_case_weight,
            config=config,
        ),
    )
    ambiguity_pressure_score = _sum_weighted_pressure(rows)
    status = _summary_status(rows)
    return ResearchResolutionAmbiguityRootCauseReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        ambiguity_pressure_score=ambiguity_pressure_score,
        status=status,
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        rows=rows,
        reason_codes=(f"resolution_ambiguity_root_cause_{status}",),
    )


def research_resolution_ambiguity_root_cause_report_payload(
    report: ResearchResolutionAmbiguityRootCauseReport,
) -> dict[str, Any]:
    if type(report) is not ResearchResolutionAmbiguityRootCauseReport:
        raise ValueError("report must be a ResearchResolutionAmbiguityRootCauseReport")
    require_paper_only_flags("report", report)
    payload = json_ready_no_floats(
        {
            "generated_at": report.generated_at,
            "config_version": report.config_version,
            "ambiguity_pressure_score": report.ambiguity_pressure_score,
            "status": report.status,
            "pass_count": report.pass_count,
            "watch_count": report.watch_count,
            "block_count": report.block_count,
            "rows": tuple(_row_payload(row) for row in report.rows),
            "reason_codes": report.reason_codes,
            "derived_validation_digest": report.derived_validation_digest,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    reject_unsafe_surface_fields("ambiguity root cause public payload", payload)
    return payload


def _root_cause_row(
    *,
    root_cause: str,
    aggregate_value: Decimal,
    pressure_score: Decimal,
    weight: Decimal,
    config: ResearchResolutionAmbiguityRootCauseConfig,
) -> ResearchResolutionAmbiguityRootCauseRow:
    normalized_pressure = _normalize_probability("pressure_score", pressure_score)
    return ResearchResolutionAmbiguityRootCauseRow(
        root_cause=root_cause,
        aggregate_value=aggregate_value,
        pressure_score=normalized_pressure,
        weight=weight,
        weighted_pressure_score=_weighted_pressure_score(normalized_pressure, weight),
        status=_pressure_status(normalized_pressure, config),
        reason_codes=(_root_cause_reason_code(root_cause, normalized_pressure, config),),
    )


def _row_payload(row: ResearchResolutionAmbiguityRootCauseRow) -> dict[str, object]:
    require_paper_only_flags("row", row)
    return {
        "root_cause": row.root_cause,
        "aggregate_value": row.aggregate_value,
        "pressure_score": row.pressure_score,
        "weight": row.weight,
        "weighted_pressure_score": row.weighted_pressure_score,
        "status": row.status,
        "reason_codes": row.reason_codes,
        "derived_validation_digest": row.derived_validation_digest,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _ratio_pressure(value: Decimal, denominator: Decimal) -> Decimal:
    if value >= denominator:
        return ONE
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        ratio = value / denominator
    return _normalize_probability("ratio_pressure", ratio)


def _weighted_pressure_score(pressure_score: Decimal, weight: Decimal) -> Decimal:
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        score = pressure_score * weight
    return _normalize_probability("weighted_pressure_score", score)


def _sum_weighted_pressure(
    rows: tuple[ResearchResolutionAmbiguityRootCauseRow, ...],
) -> Decimal:
    total = sum((row.weighted_pressure_score for row in rows), ZERO)
    return _normalize_probability("ambiguity_pressure_score", total)


def _pressure_status(
    pressure_score: Decimal,
    config: ResearchResolutionAmbiguityRootCauseConfig,
) -> str:
    if pressure_score < config.watch_pressure_threshold:
        return "pass"
    if pressure_score < config.block_pressure_threshold:
        return "watch"
    return "block"


def _root_cause_reason_code(
    root_cause: str,
    pressure_score: Decimal,
    config: ResearchResolutionAmbiguityRootCauseConfig,
) -> str:
    if pressure_score < config.watch_pressure_threshold:
        band = "low"
    elif pressure_score < config.block_pressure_threshold:
        band = "watch"
    else:
        band = "high"
    return f"{root_cause}_{band}"


def _summary_status(rows: tuple[ResearchResolutionAmbiguityRootCauseRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _status_count(
    rows: tuple[ResearchResolutionAmbiguityRootCauseRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _validate_row(row: ResearchResolutionAmbiguityRootCauseRow) -> None:
    expected_weighted = _weighted_pressure_score(row.pressure_score, row.weight)
    if row.weighted_pressure_score != expected_weighted:
        raise ValueError("weighted_pressure_score must match pressure_score and weight")
    expected_reason = _row_reason_code_from_status(row.root_cause, row.status)
    if row.reason_codes != (expected_reason,):
        raise ValueError("reason_codes must match root_cause and status")


def _row_reason_code_from_status(root_cause: str, status: str) -> str:
    if status == "pass":
        band = "low"
    elif status == "watch":
        band = "watch"
    else:
        band = "high"
    return f"{root_cause}_{band}"


def _validate_report(report: ResearchResolutionAmbiguityRootCauseReport) -> None:
    if tuple(row.root_cause for row in report.rows) != ROOT_CAUSES:
        raise ValueError("rows must follow root cause order")
    if report.ambiguity_pressure_score != _sum_weighted_pressure(report.rows):
        raise ValueError("ambiguity_pressure_score must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.status != _summary_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != (f"resolution_ambiguity_root_cause_{report.status}",):
        raise ValueError("reason_codes must match status")


def _coerce_aggregate(
    aggregate: object,
) -> ResearchResolutionAmbiguityRootCauseAggregate:
    if type(aggregate) is ResearchResolutionAmbiguityRootCauseAggregate:
        return aggregate
    return ResearchResolutionAmbiguityRootCauseAggregate(
        rule_clarity_score=_field_value(aggregate, "rule_clarity_score"),
        source_consistency_score=_field_value(aggregate, "source_consistency_score"),
        contradiction_pressure_score=_field_value(
            aggregate,
            "contradiction_pressure_score",
        ),
        oracle_lag_minutes=_field_value(aggregate, "oracle_lag_minutes"),
        edge_case_count=_field_value(aggregate, "edge_case_count"),
        paper_only=_field_value(aggregate, "paper_only", default=True),
        report_only=_field_value(aggregate, "report_only", default=True),
        readonly=_field_value(aggregate, "readonly", default=True),
    )


_MISSING = object()


def _field_value(row: object, field_name: str, *, default: object = _MISSING) -> Any:
    if hasattr(row, field_name):
        return getattr(row, field_name)
    if default is _MISSING:
        raise ValueError(f"{field_name} is required")
    return default


def _normalize_rows(rows: object) -> tuple[ResearchResolutionAmbiguityRootCauseRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must contain root cause rows")
    try:
        normalized = tuple(rows)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must contain root cause rows") from exc
    for row in normalized:
        if type(row) is not ResearchResolutionAmbiguityRootCauseRow:
            raise ValueError("rows must contain root cause rows")
    return normalized


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    normalized = _normalize_string_tuple(field_name, values)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    for value in normalized:
        _require_member(field_name, value, REASON_CODES)
        if value in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(value)
    return normalized


def _normalize_string_tuple(field_name: str, values: object) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must contain canonical strings")
    try:
        normalized = tuple(values)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must contain canonical strings") from exc
    for value in normalized:
        _require_canonical_string(field_name, value)
    return normalized


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must contain a canonical string")


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    return decimal_value.quantize(SCORE_QUANT)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= Decimal("0"):
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    normalized = decimal_value.quantize(COUNT_QUANT)
    if normalized != decimal_value:
        raise ValueError(f"{field_name} must be a whole Decimal count")
    if normalized < Decimal("0"):
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANT)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_config_weights_total_one(
    config: ResearchResolutionAmbiguityRootCauseConfig,
) -> None:
    total = (
        config.rule_clarity_weight
        + config.source_consistency_weight
        + config.contradiction_pressure_weight
        + config.oracle_lag_weight
        + config.edge_case_weight
    ).quantize(SCORE_QUANT)
    if total != ONE:
        raise ValueError("rule_clarity_weight must be part of weights totaling 1.000000")


def _require_or_set_digest(value: object) -> None:
    current = getattr(value, _DIGEST_FIELD)
    expected = _payload_digest(_payload_value(value, include_digest=False))
    if current == "":
        object.__setattr__(value, _DIGEST_FIELD, expected)
        return
    if type(current) is not str or current != expected:
        raise ValueError("derived_validation_digest must match payload fields")


def _payload_digest(value: object) -> str:
    payload = json_ready_no_floats(value)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _payload_value(value: object, *, include_digest: bool) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        payload: dict[str, object] = {}
        for field in fields(value):
            if not include_digest and field.name == _DIGEST_FIELD:
                continue
            payload[field.name] = _payload_value(getattr(value, field.name), include_digest=include_digest)
        return payload
    if isinstance(value, tuple):
        return tuple(_payload_value(item, include_digest=include_digest) for item in value)
    return value


__all__ = (
    "REASON_CODES",
    "ROOT_CAUSES",
    "STATUSES",
    "ResearchResolutionAmbiguityRootCauseAggregate",
    "ResearchResolutionAmbiguityRootCauseConfig",
    "ResearchResolutionAmbiguityRootCauseReport",
    "ResearchResolutionAmbiguityRootCauseRow",
    "build_research_resolution_ambiguity_root_cause_report",
    "research_resolution_ambiguity_root_cause_report_payload",
)
