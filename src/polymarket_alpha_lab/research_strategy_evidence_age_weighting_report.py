"""Pure report-only evidence age weighting for public research review."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any


__all__ = (
    "ResearchStrategyEvidenceAgeWeightingConfig",
    "ResearchStrategyEvidenceAgeWeightingInput",
    "ResearchStrategyEvidenceAgeWeightingReasonCodeCount",
    "ResearchStrategyEvidenceAgeWeightingReport",
    "ResearchStrategyEvidenceAgeWeightingRow",
    "build_research_strategy_evidence_age_weighting_report",
    "research_strategy_evidence_age_weighting_report_digest",
    "research_strategy_evidence_age_weighting_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-strategy-evidence-age-weighting-report-v0"
STATUSES = frozenset(("pass", "watch", "block"))
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANT = Decimal("0.000001")
PUBLIC_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
REASON_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
LABEL_UNSAFE_TERMS = (
    "event",
    "market",
    "condition",
    "source",
    "raw",
    "slug",
    "url",
    "ref",
    "text",
    "_id",
    "-id",
    "id-",
)
PAYLOAD_DENIED_FRAGMENTS = (
    "event_id",
    "market_id",
    "market_slug",
    "condition_id",
    "source_id",
    "source_ref",
    "source_url",
    "source_text",
    "raw_event",
    "raw_market",
    "raw_source",
    "private" + "_key",
    "wal" + "let",
    "au" + "th",
    "or" + "der",
    "tra" + "de",
    "li" + "ve",
    "b" + "uy",
    "se" + "ll",
    "reco" + "mmend",
    "position_size",
)


class _Missing:
    pass


MISSING = _Missing()


@dataclass(frozen=True)
class ResearchStrategyEvidenceAgeWeightingConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    fresh_age_seconds: Decimal = Decimal("3600")
    stale_age_seconds: Decimal = Decimal("86400")
    watch_pressure_threshold: Decimal = Decimal("0.350000")
    block_pressure_threshold: Decimal = Decimal("0.700000")
    aggregate_age_weight: Decimal = Decimal("0.350000")
    source_reliability_weight: Decimal = Decimal("0.200000")
    contradiction_pressure_weight: Decimal = Decimal("0.200000")
    catalyst_pressure_weight: Decimal = Decimal("0.150000")
    resolution_proximity_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyEvidenceAgeWeightingConfig, "config")
        _require_public_label("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in ("fresh_age_seconds", "stale_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_age_seconds <= self.fresh_age_seconds:
            raise ValueError("stale_age_seconds must exceed fresh_age_seconds")
        for field_name in (
            "watch_pressure_threshold",
            "block_pressure_threshold",
            "aggregate_age_weight",
            "source_reliability_weight",
            "contradiction_pressure_weight",
            "catalyst_pressure_weight",
            "resolution_proximity_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_pressure_threshold <= self.watch_pressure_threshold:
            raise ValueError("block_pressure_threshold must exceed watch_pressure_threshold")
        weight_sum = _quantize(
            self.aggregate_age_weight
            + self.source_reliability_weight
            + self.contradiction_pressure_weight
            + self.catalyst_pressure_weight
            + self.resolution_proximity_weight,
        )
        if weight_sum != ONE:
            raise ValueError(
                "aggregate_age_weight, source_reliability_weight, "
                "contradiction_pressure_weight, catalyst_pressure_weight, "
                "and resolution_proximity_weight must sum to 1",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyEvidenceAgeWeightingInput:
    research_case_label: str
    evidence_bucket_label: str
    aggregate_evidence_age_seconds: Decimal
    source_reliability: Decimal
    contradiction_pressure: Decimal
    catalyst_pressure: Decimal
    resolution_proximity: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyEvidenceAgeWeightingInput, "input")
        _require_public_label("research_case_label", self.research_case_label)
        _require_public_label("evidence_bucket_label", self.evidence_bucket_label)
        object.__setattr__(
            self,
            "aggregate_evidence_age_seconds",
            _require_nonnegative_decimal(
                "aggregate_evidence_age_seconds",
                self.aggregate_evidence_age_seconds,
            ),
        )
        for field_name in (
            "source_reliability",
            "contradiction_pressure",
            "catalyst_pressure",
            "resolution_proximity",
        ):
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
class ResearchStrategyEvidenceAgeWeightingRow:
    research_case_label: str
    evidence_bucket_label: str
    aggregate_evidence_age_seconds: Decimal
    aggregate_age_pressure: Decimal
    source_reliability: Decimal
    source_reliability_gap: Decimal
    contradiction_pressure: Decimal
    catalyst_pressure: Decimal
    resolution_proximity: Decimal
    weighted_age_pressure: Decimal
    evidence_age_weight: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyEvidenceAgeWeightingRow, "row")
        _require_public_label("research_case_label", self.research_case_label)
        _require_public_label("evidence_bucket_label", self.evidence_bucket_label)
        object.__setattr__(
            self,
            "aggregate_evidence_age_seconds",
            _require_nonnegative_decimal(
                "aggregate_evidence_age_seconds",
                self.aggregate_evidence_age_seconds,
            ),
        )
        for field_name in (
            "aggregate_age_pressure",
            "source_reliability",
            "source_reliability_gap",
            "contradiction_pressure",
            "catalyst_pressure",
            "resolution_proximity",
            "weighted_age_pressure",
            "evidence_age_weight",
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
class ResearchStrategyEvidenceAgeWeightingReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyEvidenceAgeWeightingReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchStrategyEvidenceAgeWeightingReport:
    generated_at: datetime
    config_version: str
    case_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_weighted_age_pressure: Decimal | None
    max_aggregate_evidence_age_seconds: Decimal
    status: str
    rows: tuple[ResearchStrategyEvidenceAgeWeightingRow, ...]
    reason_code_counts: tuple[ResearchStrategyEvidenceAgeWeightingReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyEvidenceAgeWeightingReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in ("case_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_weighted_age_pressure",
            _require_optional_probability_decimal(
                "average_weighted_age_pressure",
                self.average_weighted_age_pressure,
            ),
        )
        object.__setattr__(
            self,
            "max_aggregate_evidence_age_seconds",
            _require_nonnegative_decimal(
                "max_aggregate_evidence_age_seconds",
                self.max_aggregate_evidence_age_seconds,
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
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        expected_digest = _digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")


def build_research_strategy_evidence_age_weighting_report(
    inputs: Iterable[object],
    *,
    config: ResearchStrategyEvidenceAgeWeightingConfig,
    generated_at: datetime,
) -> ResearchStrategyEvidenceAgeWeightingReport:
    if type(config) is not ResearchStrategyEvidenceAgeWeightingConfig:
        raise ValueError("config must be a ResearchStrategyEvidenceAgeWeightingConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(inputs)
    rows = tuple(
        _row_from_input(input_value, config=config)
        for input_value in sorted(input_rows, key=lambda value: value.research_case_label)
    )
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "case_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_weighted_age_pressure": _average_pressure(rows),
        "max_aggregate_evidence_age_seconds": _max_age(rows),
        "status": _report_status(rows),
        "rows": rows,
        "reason_code_counts": _reason_code_counts(rows, reason_codes),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyEvidenceAgeWeightingReport(
        **values,
        derived_validation_digest=_digest_from_values(values),
    )


def research_strategy_evidence_age_weighting_report_payload(
    report: ResearchStrategyEvidenceAgeWeightingReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategyEvidenceAgeWeightingReport:
        raise ValueError("report must be a ResearchStrategyEvidenceAgeWeightingReport")
    _require_hard_flags("report", report)
    _validate_report_consistency(report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_payload(payload)
    return payload


def research_strategy_evidence_age_weighting_report_digest(
    report: ResearchStrategyEvidenceAgeWeightingReport,
) -> str:
    payload = research_strategy_evidence_age_weighting_report_payload(report)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _row_from_input(
    input_value: ResearchStrategyEvidenceAgeWeightingInput,
    *,
    config: ResearchStrategyEvidenceAgeWeightingConfig,
) -> ResearchStrategyEvidenceAgeWeightingRow:
    aggregate_age_pressure = _age_pressure(
        input_value.aggregate_evidence_age_seconds,
        config=config,
    )
    source_reliability_gap = _quantize(ONE - input_value.source_reliability)
    weighted_age_pressure = _quantize(
        aggregate_age_pressure * config.aggregate_age_weight
        + source_reliability_gap * config.source_reliability_weight
        + input_value.contradiction_pressure * config.contradiction_pressure_weight
        + input_value.catalyst_pressure * config.catalyst_pressure_weight
        + input_value.resolution_proximity * config.resolution_proximity_weight,
    )
    evidence_age_weight = _quantize(ONE - weighted_age_pressure)
    status = _pressure_status(weighted_age_pressure, config=config)
    return ResearchStrategyEvidenceAgeWeightingRow(
        research_case_label=input_value.research_case_label,
        evidence_bucket_label=input_value.evidence_bucket_label,
        aggregate_evidence_age_seconds=input_value.aggregate_evidence_age_seconds,
        aggregate_age_pressure=aggregate_age_pressure,
        source_reliability=input_value.source_reliability,
        source_reliability_gap=source_reliability_gap,
        contradiction_pressure=input_value.contradiction_pressure,
        catalyst_pressure=input_value.catalyst_pressure,
        resolution_proximity=input_value.resolution_proximity,
        weighted_age_pressure=weighted_age_pressure,
        evidence_age_weight=evidence_age_weight,
        status=status,
        reason_codes=_row_reason_codes(
            input_value,
            status=status,
            aggregate_age_pressure=aggregate_age_pressure,
            source_reliability_gap=source_reliability_gap,
            config=config,
        ),
    )


def _age_pressure(
    aggregate_evidence_age_seconds: Decimal,
    *,
    config: ResearchStrategyEvidenceAgeWeightingConfig,
) -> Decimal:
    if aggregate_evidence_age_seconds <= config.fresh_age_seconds:
        return ZERO
    if aggregate_evidence_age_seconds >= config.stale_age_seconds:
        return ONE
    span = config.stale_age_seconds - config.fresh_age_seconds
    return _quantize((aggregate_evidence_age_seconds - config.fresh_age_seconds) / span)


def _pressure_status(
    pressure: Decimal,
    *,
    config: ResearchStrategyEvidenceAgeWeightingConfig,
) -> str:
    if pressure >= config.block_pressure_threshold:
        return "block"
    if pressure >= config.watch_pressure_threshold:
        return "watch"
    return "pass"


def _row_reason_codes(
    input_value: ResearchStrategyEvidenceAgeWeightingInput,
    *,
    status: str,
    aggregate_age_pressure: Decimal,
    source_reliability_gap: Decimal,
    config: ResearchStrategyEvidenceAgeWeightingConfig,
) -> tuple[str, ...]:
    codes = {
        f"aggregate_age_pressure_{_pressure_status(aggregate_age_pressure, config=config)}",
        f"source_reliability_gap_{_pressure_status(source_reliability_gap, config=config)}",
        f"contradiction_pressure_{_pressure_status(input_value.contradiction_pressure, config=config)}",
        f"catalyst_pressure_{_pressure_status(input_value.catalyst_pressure, config=config)}",
        f"resolution_proximity_{_pressure_status(input_value.resolution_proximity, config=config)}",
        f"evidence_age_weighting_{status}",
    }
    codes.update(f"input_{reason_code}" for reason_code in input_value.reason_codes)
    return tuple(sorted(codes))


def _report_reason_codes(
    rows: tuple[ResearchStrategyEvidenceAgeWeightingRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_evidence_age_weighting_inputs",)
    status = _report_status(rows)
    codes = {f"evidence_age_weighting_report_{status}"}
    if any(row.status == "block" for row in rows):
        codes.add("age_weighting_block_pressure_present")
    if any(row.status == "watch" for row in rows):
        codes.add("age_weighting_watch_pressure_present")
    if all(row.status == "pass" for row in rows):
        codes.add("age_weighting_inputs_pass")
    return tuple(sorted(codes))


def _report_status(rows: tuple[ResearchStrategyEvidenceAgeWeightingRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchStrategyEvidenceAgeWeightingRow, ...],
    report_reason_codes: tuple[str, ...],
) -> tuple[ResearchStrategyEvidenceAgeWeightingReasonCodeCount, ...]:
    counter: Counter[str] = Counter(report_reason_codes)
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        ResearchStrategyEvidenceAgeWeightingReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counter.items())
    )


def _average_pressure(
    rows: tuple[ResearchStrategyEvidenceAgeWeightingRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(sum((row.weighted_age_pressure for row in rows), ZERO) / len(rows))


def _max_age(rows: tuple[ResearchStrategyEvidenceAgeWeightingRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    return max(row.aggregate_evidence_age_seconds for row in rows)


def _status_count(
    rows: tuple[ResearchStrategyEvidenceAgeWeightingRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_inputs(
    rows: Iterable[object],
) -> tuple[ResearchStrategyEvidenceAgeWeightingInput, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("inputs must be an iterable")
    return tuple(_coerce_input(row) for row in rows)


def _coerce_input(value: object) -> ResearchStrategyEvidenceAgeWeightingInput:
    if type(value) is ResearchStrategyEvidenceAgeWeightingInput:
        _require_hard_flags("input", value)
        return value
    if not is_dataclass(value) or isinstance(value, type):
        raise ValueError("input must be a ResearchStrategyEvidenceAgeWeightingInput")
    values = {
        field.name: getattr(value, field.name, MISSING)
        for field in fields(ResearchStrategyEvidenceAgeWeightingInput)
    }
    missing = tuple(
        field_name
        for field_name, field_value in values.items()
        if field_value is MISSING
        and field_name not in ("reason_codes", "paper_only", "report_only", "readonly")
    )
    if missing:
        raise ValueError(f"input missing required fields: {', '.join(missing)}")
    values = {key: item for key, item in values.items() if item is not MISSING}
    return ResearchStrategyEvidenceAgeWeightingInput(**values)


def _normalize_rows(
    rows: object,
) -> tuple[ResearchStrategyEvidenceAgeWeightingRow, ...]:
    if not isinstance(rows, tuple):
        raise ValueError("rows must be a tuple")
    normalized: list[ResearchStrategyEvidenceAgeWeightingRow] = []
    for row in rows:
        if type(row) is not ResearchStrategyEvidenceAgeWeightingRow:
            raise ValueError("rows must contain ResearchStrategyEvidenceAgeWeightingRow")
        _require_hard_flags("row", row)
        normalized.append(row)
    sorted_rows = tuple(sorted(normalized, key=lambda row: row.research_case_label))
    if tuple(normalized) != sorted_rows:
        raise ValueError("rows must be sorted by research_case_label")
    return sorted_rows


def _normalize_reason_code_counts(
    values: object,
) -> tuple[ResearchStrategyEvidenceAgeWeightingReasonCodeCount, ...]:
    if not isinstance(values, tuple):
        raise ValueError("reason_code_counts must be a tuple")
    normalized: list[ResearchStrategyEvidenceAgeWeightingReasonCodeCount] = []
    for value in values:
        if type(value) is not ResearchStrategyEvidenceAgeWeightingReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyEvidenceAgeWeightingReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", value)
        normalized.append(value)
    sorted_values = tuple(sorted(normalized, key=lambda value: value.reason_code))
    if tuple(normalized) != sorted_values:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return sorted_values


def _normalize_reason_codes(
    label: str,
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise ValueError(f"{label} must be a tuple")
    normalized = tuple(sorted(set(value)))
    if not allow_empty and not normalized:
        raise ValueError(f"{label} must not be empty")
    for reason_code in normalized:
        _require_reason_code(label, reason_code)
    return normalized


def _validate_row_consistency(row: ResearchStrategyEvidenceAgeWeightingRow) -> None:
    if row.source_reliability_gap != _quantize(ONE - row.source_reliability):
        raise ValueError("source_reliability_gap must equal 1 minus source_reliability")
    if row.evidence_age_weight != _quantize(ONE - row.weighted_age_pressure):
        raise ValueError("evidence_age_weight must equal 1 minus weighted_age_pressure")


def _validate_report_consistency(report: ResearchStrategyEvidenceAgeWeightingReport) -> None:
    rows = report.rows
    if report.case_count != _decimal_count(len(rows)):
        raise ValueError("case_count must equal row count")
    if report.pass_count != _decimal_count(_status_count(rows, "pass")):
        raise ValueError("pass_count must equal pass row count")
    if report.watch_count != _decimal_count(_status_count(rows, "watch")):
        raise ValueError("watch_count must equal watch row count")
    if report.block_count != _decimal_count(_status_count(rows, "block")):
        raise ValueError("block_count must equal block row count")
    if report.average_weighted_age_pressure != _average_pressure(rows):
        raise ValueError("average_weighted_age_pressure must equal row average")
    if report.max_aggregate_evidence_age_seconds != _max_age(rows):
        raise ValueError("max_aggregate_evidence_age_seconds must equal row max")
    if report.status != _report_status(rows):
        raise ValueError("status must match row statuses")


def _report_values_without_digest(
    report: ResearchStrategyEvidenceAgeWeightingReport,
) -> dict[str, object]:
    return {
        field.name: getattr(report, field.name)
        for field in fields(report)
        if field.name != "derived_validation_digest"
    }


def _digest_from_values(values: dict[str, object]) -> str:
    payload = _payload_value(values)
    _reject_unsafe_payload(payload)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _payload_value(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(asdict(value))
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    return value


def _reject_unsafe_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_unsafe_fragment(str(key))
            _reject_unsafe_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_payload(item)
        return
    if type(value) is str:
        _reject_unsafe_fragment(value)


def _reject_unsafe_fragment(value: str) -> None:
    lower_value = value.lower()
    if any(fragment in lower_value for fragment in PAYLOAD_DENIED_FRAGMENTS):
        raise ValueError("payload contains unsafe public fragment")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_public_label(label: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{label} must be a string")
    if not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{label} must be a public label")
    lower_value = value.lower()
    if any(term in lower_value for term in LABEL_UNSAFE_TERMS):
        raise ValueError(f"{label} must not contain raw public identifiers")
    return value


def _require_reason_code(label: str, value: object) -> str:
    if type(value) is not str or not REASON_CODE_RE.fullmatch(value):
        raise ValueError(f"{label} must contain reason codes")
    return value


def _require_status(label: str, value: object) -> str:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{label} must be pass, watch, or block")
    return value


def _require_digest(label: str, value: object) -> str:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{label} must be a sha256 digest")
    return value


def _require_decimal(label: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{label} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{label} must be finite")
    return _quantize(value)


def _require_positive_decimal(label: str, value: object) -> Decimal:
    decimal_value = _require_decimal(label, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{label} must be positive")
    return decimal_value


def _require_nonnegative_decimal(label: str, value: object) -> Decimal:
    decimal_value = _require_decimal(label, value)
    if decimal_value < ZERO:
        raise ValueError(f"{label} must be nonnegative")
    return decimal_value


def _require_probability_decimal(label: str, value: object) -> Decimal:
    decimal_value = _require_decimal(label, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{label} must be between 0 and 1")
    return decimal_value


def _require_optional_probability_decimal(
    label: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_probability_decimal(label, value)


def _require_nonnegative_whole_decimal(label: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(label, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{label} must be a whole Decimal")
    return decimal_value


def _require_positive_whole_decimal(label: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_whole_decimal(label, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{label} must be positive")
    return decimal_value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _as_utc(label: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{label} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{label} must be timezone-aware")
    return value.astimezone(UTC)


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANT)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANT, rounding=ROUND_HALF_UP)
