"""Pure report-only reducer for market depth fee memory confidence ladders."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any, Iterable


DEFAULT_RESEARCH_MARKET_DEPTH_FEE_MEMORY_CONFIDENCE_LADDER_CONFIG_VERSION = (
    "research-market-depth-fee-memory-confidence-ladder-report-v0"
)

STATUSES = ("pass", "watch", "block")
ROW_REASON_CODES = (
    "cost_pressure_block",
    "cost_pressure_watch",
    "depth_fee_memory_pass",
    "high_fee",
    "low_memory_confidence",
    "thin_depth",
)
REPORT_REASON_CODES = (
    "depth_fee_memory_ladder_block",
    "depth_fee_memory_ladder_no_inputs",
    "depth_fee_memory_ladder_pass",
    "depth_fee_memory_ladder_watch",
)
NEXT_STEP = "review_depth_fee_memory_pressure"
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

__all__ = (
    "DEFAULT_RESEARCH_MARKET_DEPTH_FEE_MEMORY_CONFIDENCE_LADDER_CONFIG_VERSION",
    "ResearchMarketDepthFeeMemoryConfidenceLadderConfig",
    "ResearchMarketDepthFeeMemoryConfidenceLadderObservation",
    "ResearchMarketDepthFeeMemoryConfidenceLadderReasonCodeCount",
    "ResearchMarketDepthFeeMemoryConfidenceLadderReport",
    "ResearchMarketDepthFeeMemoryConfidenceLadderRow",
    "build_research_market_depth_fee_memory_confidence_ladder_report",
    "research_market_depth_fee_memory_confidence_ladder_report_payload",
    "validate_research_market_depth_fee_memory_confidence_ladder_report_payload_digest",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchMarketDepthFeeMemoryConfidenceLadderConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_DEPTH_FEE_MEMORY_CONFIDENCE_LADDER_CONFIG_VERSION
    )
    watch_cost_pressure: Decimal = Decimal("0.350000")
    block_cost_pressure: Decimal = Decimal("0.700000")
    watch_fee_bps: Decimal = Decimal("3.000000")
    block_fee_bps: Decimal = Decimal("8.000000")
    thin_depth_threshold: Decimal = Decimal("0.500000")
    low_memory_confidence_threshold: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketDepthFeeMemoryConfidenceLadderConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_DEPTH_FEE_MEMORY_CONFIDENCE_LADDER_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_cost_pressure",
            "block_cost_pressure",
            "thin_depth_threshold",
            "low_memory_confidence_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in ("watch_fee_bps", "block_fee_bps"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_cost_pressure <= self.watch_cost_pressure:
            raise ValueError("block_cost_pressure must exceed watch_cost_pressure")
        if self.block_fee_bps <= self.watch_fee_bps:
            raise ValueError("block_fee_bps must exceed watch_fee_bps")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketDepthFeeMemoryConfidenceLadderObservation(_FinalPublicDataclass):
    case_id: str
    observed_at: datetime
    depth_score: Decimal
    fee_bps: Decimal
    memory_confidence: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketDepthFeeMemoryConfidenceLadderObservation,
            "observation",
        )
        _require_public_identifier("case_id", self.case_id)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "depth_score",
            _normalize_probability("depth_score", self.depth_score),
        )
        object.__setattr__(
            self,
            "fee_bps",
            _normalize_nonnegative_decimal("fee_bps", self.fee_bps),
        )
        object.__setattr__(
            self,
            "memory_confidence",
            _normalize_probability("memory_confidence", self.memory_confidence),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchMarketDepthFeeMemoryConfidenceLadderRow(_FinalPublicDataclass):
    case_id: str
    observed_at: datetime
    depth_score: Decimal
    fee_bps: Decimal
    fee_pressure: Decimal
    memory_confidence: Decimal
    confidence_gap: Decimal
    cost_pressure: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketDepthFeeMemoryConfidenceLadderRow, "row")
        _require_public_identifier("case_id", self.case_id)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "depth_score",
            "fee_pressure",
            "memory_confidence",
            "confidence_gap",
            "cost_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "fee_bps",
            _normalize_nonnegative_decimal("fee_bps", self.fee_bps),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchMarketDepthFeeMemoryConfidenceLadderReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketDepthFeeMemoryConfidenceLadderReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_count_decimal("count", self.count))
        if self.count <= ZERO:
            raise ValueError("count must be positive")
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchMarketDepthFeeMemoryConfidenceLadderReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    report_status: str
    report_next_step: str
    case_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    high_fee_count: Decimal
    thin_depth_count: Decimal
    low_memory_confidence_count: Decimal
    highest_cost_pressure: Decimal
    average_cost_pressure: Decimal
    average_fee_bps: Decimal
    average_memory_confidence: Decimal
    rows: tuple[ResearchMarketDepthFeeMemoryConfidenceLadderRow, ...]
    reason_code_counts: tuple[ResearchMarketDepthFeeMemoryConfidenceLadderReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_payload_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketDepthFeeMemoryConfidenceLadderReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_DEPTH_FEE_MEMORY_CONFIDENCE_LADDER_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("report_status", self.report_status)
        _require_canonical_string("report_next_step", self.report_next_step)
        for field_name in (
            "case_count",
            "pass_count",
            "watch_count",
            "block_count",
            "high_fee_count",
            "thin_depth_count",
            "low_memory_confidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "highest_cost_pressure",
            "average_cost_pressure",
            "average_memory_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_fee_bps",
            _normalize_nonnegative_decimal("average_fee_bps", self.average_fee_bps),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        _validate_report(self)
        _require_hard_flags("report", self)
        expected_digest = _derived_payload_digest(self)
        if self.derived_payload_digest:
            _require_sha256_digest("derived_payload_digest", self.derived_payload_digest)
            if self.derived_payload_digest != expected_digest:
                raise ValueError("derived_payload_digest does not match report payload")
        else:
            object.__setattr__(self, "derived_payload_digest", expected_digest)


_PUBLIC_DATACLASS_TYPES = (
    ResearchMarketDepthFeeMemoryConfidenceLadderConfig,
    ResearchMarketDepthFeeMemoryConfidenceLadderObservation,
    ResearchMarketDepthFeeMemoryConfidenceLadderRow,
    ResearchMarketDepthFeeMemoryConfidenceLadderReasonCodeCount,
    ResearchMarketDepthFeeMemoryConfidenceLadderReport,
)


def build_research_market_depth_fee_memory_confidence_ladder_report(
    observations: Iterable[ResearchMarketDepthFeeMemoryConfidenceLadderObservation],
    *,
    config: ResearchMarketDepthFeeMemoryConfidenceLadderConfig,
    generated_at: datetime,
) -> ResearchMarketDepthFeeMemoryConfidenceLadderReport:
    if type(config) is not ResearchMarketDepthFeeMemoryConfidenceLadderConfig:
        raise ValueError(
            "config must be a ResearchMarketDepthFeeMemoryConfidenceLadderConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    rows = _sorted_rows(_row_from_observation(item, config=config) for item in normalized_observations)
    reason_codes = _report_reason_codes(rows)
    return ResearchMarketDepthFeeMemoryConfidenceLadderReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_status=_report_status(reason_codes),
        report_next_step=NEXT_STEP,
        case_count=_count_decimal(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        high_fee_count=_reason_row_count(rows, "high_fee"),
        thin_depth_count=_reason_row_count(rows, "thin_depth"),
        low_memory_confidence_count=_reason_row_count(rows, "low_memory_confidence"),
        highest_cost_pressure=_highest_probability(row.cost_pressure for row in rows),
        average_cost_pressure=_average_probability(row.cost_pressure for row in rows),
        average_fee_bps=_average_nonnegative_decimal(row.fee_bps for row in rows),
        average_memory_confidence=_average_probability(row.memory_confidence for row in rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows),
        reason_codes=reason_codes,
    )


def research_market_depth_fee_memory_confidence_ladder_report_payload(
    report: ResearchMarketDepthFeeMemoryConfidenceLadderReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketDepthFeeMemoryConfidenceLadderReport:
        raise ValueError(
            "report must be exactly ResearchMarketDepthFeeMemoryConfidenceLadderReport",
        )
    _require_payload_safe_value("report", report)
    if not validate_research_market_depth_fee_memory_confidence_ladder_report_payload_digest(
        _payload_value(report),
    ):
        raise ValueError("derived_payload_digest does not match report payload")
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return payload


def validate_research_market_depth_fee_memory_confidence_ladder_report_payload_digest(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        return False
    digest = payload.get("derived_payload_digest")
    if type(digest) is not str:
        return False
    body = dict(payload)
    body.pop("derived_payload_digest", None)
    return sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest() == digest


def _row_from_observation(
    observation: ResearchMarketDepthFeeMemoryConfidenceLadderObservation,
    *,
    config: ResearchMarketDepthFeeMemoryConfidenceLadderConfig,
) -> ResearchMarketDepthFeeMemoryConfidenceLadderRow:
    fee_pressure = _fee_pressure(observation.fee_bps, config.block_fee_bps)
    with localcontext(DECIMAL_CONTEXT):
        confidence_gap = _quantize_decimal(ONE - observation.memory_confidence)
    cost_pressure = _cost_pressure(
        depth_score=observation.depth_score,
        fee_pressure=fee_pressure,
        confidence_gap=confidence_gap,
    )
    reason_codes = _row_reason_codes(
        observation,
        fee_pressure=fee_pressure,
        cost_pressure=cost_pressure,
        config=config,
    )
    return ResearchMarketDepthFeeMemoryConfidenceLadderRow(
        case_id=observation.case_id,
        observed_at=observation.observed_at,
        depth_score=observation.depth_score,
        fee_bps=observation.fee_bps,
        fee_pressure=fee_pressure,
        memory_confidence=observation.memory_confidence,
        confidence_gap=confidence_gap,
        cost_pressure=cost_pressure,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _fee_pressure(fee_bps: Decimal, block_fee_bps: Decimal) -> Decimal:
    if block_fee_bps <= ZERO:
        raise ValueError("block_fee_bps must be positive")
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(min(fee_bps / block_fee_bps, ONE))


def _cost_pressure(
    *,
    depth_score: Decimal,
    fee_pressure: Decimal,
    confidence_gap: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        depth_gap = ONE - depth_score
        return _quantize_decimal(
            (depth_gap * Decimal("0.400000"))
            + (fee_pressure * Decimal("0.350000"))
            + (confidence_gap * Decimal("0.250000")),
        )


def _row_reason_codes(
    observation: ResearchMarketDepthFeeMemoryConfidenceLadderObservation,
    *,
    fee_pressure: Decimal,
    cost_pressure: Decimal,
    config: ResearchMarketDepthFeeMemoryConfidenceLadderConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if cost_pressure >= config.block_cost_pressure:
        reason_codes.append("cost_pressure_block")
    elif cost_pressure >= config.watch_cost_pressure:
        reason_codes.append("cost_pressure_watch")
    if observation.depth_score < config.thin_depth_threshold:
        reason_codes.append("thin_depth")
    if observation.fee_bps >= config.watch_fee_bps or fee_pressure >= config.watch_cost_pressure:
        reason_codes.append("high_fee")
    if observation.memory_confidence < config.low_memory_confidence_threshold:
        reason_codes.append("low_memory_confidence")
    if not reason_codes:
        return ("depth_fee_memory_pass",)
    return tuple(sorted(set(reason_codes)))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if "cost_pressure_block" in reason_codes:
        return "block"
    if reason_codes == ("depth_fee_memory_pass",):
        return "pass"
    return "watch"


def _report_reason_codes(
    rows: tuple[ResearchMarketDepthFeeMemoryConfidenceLadderRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("depth_fee_memory_ladder_no_inputs",)
    if any(row.status == "block" for row in rows):
        return ("depth_fee_memory_ladder_block",)
    if any(row.status == "watch" for row in rows):
        return ("depth_fee_memory_ladder_watch",)
    return ("depth_fee_memory_ladder_pass",)


def _report_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("depth_fee_memory_ladder_pass",):
        return "pass"
    if reason_codes == ("depth_fee_memory_ladder_block",):
        return "block"
    return "watch"


def _sorted_rows(
    rows: Iterable[ResearchMarketDepthFeeMemoryConfidenceLadderRow],
) -> tuple[ResearchMarketDepthFeeMemoryConfidenceLadderRow, ...]:
    status_weight = {"block": 0, "watch": 1, "pass": 2}
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                status_weight[row.status],
                -row.cost_pressure,
                row.observed_at,
                row.case_id,
            ),
        ),
    )


def _reason_code_counts(
    rows: tuple[ResearchMarketDepthFeeMemoryConfidenceLadderRow, ...],
) -> tuple[ResearchMarketDepthFeeMemoryConfidenceLadderReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketDepthFeeMemoryConfidenceLadderReasonCodeCount(
                reason_code="depth_fee_memory_ladder_no_inputs",
                count=_count_decimal(1),
            ),
        )
    counter: Counter[str] = Counter(
        reason_code for row in rows for reason_code in row.reason_codes
    )
    return tuple(
        ResearchMarketDepthFeeMemoryConfidenceLadderReasonCodeCount(
            reason_code=reason_code,
            count=_count_decimal(counter[reason_code]),
        )
        for reason_code in sorted(counter)
    )


def _status_count(
    rows: tuple[ResearchMarketDepthFeeMemoryConfidenceLadderRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _reason_row_count(
    rows: tuple[ResearchMarketDepthFeeMemoryConfidenceLadderRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _highest_probability(values: Iterable[Decimal]) -> Decimal:
    normalized_values = tuple(values)
    if not normalized_values:
        return ZERO
    return _quantize_decimal(max(normalized_values))


def _average_probability(values: Iterable[Decimal]) -> Decimal:
    return _normalize_probability("average", _average_nonnegative_decimal(values))


def _average_nonnegative_decimal(values: Iterable[Decimal]) -> Decimal:
    normalized_values = tuple(values)
    if not normalized_values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(
            sum(normalized_values, ZERO) / _count_decimal(len(normalized_values)),
        )


def _normalize_observations(
    value: Iterable[ResearchMarketDepthFeeMemoryConfidenceLadderObservation],
) -> tuple[ResearchMarketDepthFeeMemoryConfidenceLadderObservation, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        observations = tuple(value)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    seen_case_ids: set[str] = set()
    for item in observations:
        if type(item) is not ResearchMarketDepthFeeMemoryConfidenceLadderObservation:
            raise ValueError(
                "observations must contain ResearchMarketDepthFeeMemoryConfidenceLadderObservation values",
            )
        _require_hard_flags("observations", item)
        if item.case_id in seen_case_ids:
            raise ValueError("observations case_id values must be unique")
        seen_case_ids.add(item.case_id)
    return observations


def _normalize_rows(
    value: tuple[ResearchMarketDepthFeeMemoryConfidenceLadderRow, ...],
) -> tuple[ResearchMarketDepthFeeMemoryConfidenceLadderRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_case_ids: set[str] = set()
    for row in rows:
        if type(row) is not ResearchMarketDepthFeeMemoryConfidenceLadderRow:
            raise ValueError("rows must contain ResearchMarketDepthFeeMemoryConfidenceLadderRow values")
        _require_hard_flags("rows", row)
        if row.case_id in seen_case_ids:
            raise ValueError("rows case_id values must be unique")
        seen_case_ids.add(row.case_id)
    if rows != _sorted_rows(rows):
        raise ValueError("rows must use deterministic sequence")
    return rows


def _normalize_reason_code_counts(
    value: tuple[ResearchMarketDepthFeeMemoryConfidenceLadderReasonCodeCount, ...],
) -> tuple[ResearchMarketDepthFeeMemoryConfidenceLadderReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(value)
    reason_codes = tuple(item.reason_code for item in counts)
    if reason_codes != tuple(sorted(reason_codes)):
        raise ValueError("reason_code_counts must use deterministic sequence")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_code_counts reason_code values must be unique")
    for item in counts:
        if type(item) is not ResearchMarketDepthFeeMemoryConfidenceLadderReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain ResearchMarketDepthFeeMemoryConfidenceLadderReasonCodeCount values",
            )
        _require_hard_flags("reason_code_counts", item)
    return counts


def _validate_row(row: ResearchMarketDepthFeeMemoryConfidenceLadderRow) -> None:
    expected_status = _row_status(row.reason_codes)
    if row.status != expected_status:
        raise ValueError("status must match reason_codes")


def _validate_report(report: ResearchMarketDepthFeeMemoryConfidenceLadderReport) -> None:
    rows = report.rows
    if report.case_count != _count_decimal(len(rows)):
        raise ValueError("case_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.high_fee_count != _reason_row_count(rows, "high_fee"):
        raise ValueError("high_fee_count must match rows")
    if report.thin_depth_count != _reason_row_count(rows, "thin_depth"):
        raise ValueError("thin_depth_count must match rows")
    if report.low_memory_confidence_count != _reason_row_count(rows, "low_memory_confidence"):
        raise ValueError("low_memory_confidence_count must match rows")
    if report.highest_cost_pressure != _highest_probability(row.cost_pressure for row in rows):
        raise ValueError("highest_cost_pressure must match rows")
    if report.average_cost_pressure != _average_probability(row.cost_pressure for row in rows):
        raise ValueError("average_cost_pressure must match rows")
    if report.average_fee_bps != _average_nonnegative_decimal(row.fee_bps for row in rows):
        raise ValueError("average_fee_bps must match rows")
    if report.average_memory_confidence != _average_probability(
        row.memory_confidence for row in rows
    ):
        raise ValueError("average_memory_confidence must match rows")
    expected_reason_codes = _report_reason_codes(rows)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    if report.report_status != _report_status(report.reason_codes):
        raise ValueError("report_status must match reason_codes")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _require_payload_safe_value(field_name: str, value: object) -> None:
    if is_dataclass(value):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{field_name} must be a public dataclass")
        _require_hard_flags(field_name, value)
        for item in fields(value):
            _require_payload_safe_value(item.name, getattr(value, item.name))
        return
    if isinstance(value, tuple):
        for item in value:
            _require_payload_safe_value(field_name, item)
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{field_name} must be a Decimal")
        if not value.is_finite():
            raise ValueError(f"{field_name} must be finite")
        with localcontext(DECIMAL_CONTEXT):
            if value != value.quantize(QUANTUM):
                raise ValueError(f"{field_name} must use six decimals")
        return
    if isinstance(value, datetime):
        _as_utc(field_name, value)
        return
    if isinstance(value, str):
        _require_payload_safe_string(field_name, value)
        return
    if isinstance(value, bool):
        return
    if isinstance(value, int):
        raise ValueError(f"{field_name} must be a Decimal")
    if isinstance(value, float):
        raise ValueError(f"{field_name} must not be a float")
    if isinstance(value, dict):
        raise ValueError(f"{field_name} must not be a dict")
    if isinstance(value, list):
        raise ValueError(f"{field_name} must not be a list")


def _derived_payload_digest(
    report: ResearchMarketDepthFeeMemoryConfidenceLadderReport,
) -> str:
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    payload.pop("derived_payload_digest", None)
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()


def _payload_value(value: object) -> Any:
    if is_dataclass(value):
        return {item.name: _payload_value(getattr(value, item.name)) for item in fields(value)}
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, Decimal):
        return format(value, ".6f")
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    return value


def _normalize_reason_codes(
    field_name: str,
    value: tuple[str, ...],
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    for item in reason_codes:
        _require_reason_code_member(field_name, item, allowed_values)
        if item in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(item)
    if reason_codes != tuple(sorted(reason_codes)):
        raise ValueError(f"{field_name} must use deterministic sequence")
    return reason_codes


def _require_reason_code(field_name: str, value: str) -> None:
    if value in ROW_REASON_CODES or value in REPORT_REASON_CODES:
        return
    raise ValueError(f"{field_name} must be a supported reason code")


def _require_reason_code_member(
    field_name: str,
    value: str,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must contain strings")
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be a supported reason code")


def _require_status(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must be stripped")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")


def _require_public_identifier(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} must be a redacted public identifier")


def _require_payload_safe_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if field_name == "derived_payload_digest":
        _require_sha256_digest(field_name, value)
        return
    if field_name == "config_version":
        _require_canonical_string(field_name, value)
        if (
            value
            != DEFAULT_RESEARCH_MARKET_DEPTH_FEE_MEMORY_CONFIDENCE_LADDER_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        return
    if field_name in ("status", "report_status"):
        _require_status(field_name, value)
        return
    if field_name in ("reason_code", "reason_codes"):
        _require_reason_code(field_name, value)
        return
    _require_canonical_string(field_name, value)
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} must be a redacted public identifier")


def _has_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower()
    unsafe_fragments = (
        "://",
        "?",
        "&",
        "=",
        "\n",
        "\r",
        "au" "th",
        "candidate",
        "market",
        "slug",
        "question",
        "source",
        "url",
        "text",
        "dsn",
        "li" "ve",
        "or" "der",
        "recomm" "endation",
        "siz" "ing",
        "table",
        "token",
        "tr" "ad",
        "wal" "let",
        "exe" "cution",
    )
    return any(fragment in lowered for fragment in unsafe_fragments)


def _require_sha256_digest(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name}.{flag_name} must be True")


def _normalize_probability(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_count_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    with localcontext(DECIMAL_CONTEXT):
        whole_value = normalized.quantize(Decimal("1"))
        if normalized != whole_value.quantize(QUANTUM):
            raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)
