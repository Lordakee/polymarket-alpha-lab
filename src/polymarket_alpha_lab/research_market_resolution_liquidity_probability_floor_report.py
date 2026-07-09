from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


_ZERO = Decimal("0")
_ONE = Decimal("1")
_QUANT = Decimal("0.000001")
_DECIMAL_CONTEXT = Context(prec=50, rounding=ROUND_HALF_EVEN)
_ALLOWED_STATUSES = frozenset(("pass", "watch", "block"))
_STATUS_SORT_KEY = {"block": 0, "watch": 1, "pass": 2}
_ROW_PAYLOAD_FIELDS = frozenset(
    (
        "analysis_rank",
        "observed_at",
        "floor_status",
        "effective_probability_floor",
        "probability_floor_gap",
        "liquidity_probability_floor",
        "resolution_probability_floor",
        "observed_probability",
        "liquidity_depth_score",
        "resolution_confidence_score",
        "evidence_freshness_score",
        "diagnostic_codes",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_REPORT_PAYLOAD_FIELDS = frozenset(
    (
        "generated_at",
        "config_version",
        "report_status",
        "input_count",
        "pass_count",
        "watch_count",
        "block_count",
        "minimum_effective_probability_floor",
        "average_effective_probability_floor",
        "minimum_liquidity_depth_score",
        "minimum_resolution_confidence_score",
        "rows",
        "diagnostic_codes",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_ROW_DIAGNOSTIC_PREFIXES = (
    "floor_status_",
    "probability_floor_",
    "liquidity_depth_",
    "resolution_confidence_",
)
_SURFACE_FRAGMENTS = (
    "candidate_id",
    "candidate_ids",
    "market_id",
    "market_ids",
    "market_slug",
    "market_slugs",
    "slug",
    "question",
    "source_url",
    "source_text",
    "http://",
    "https://",
    "://",
    "dsn",
    "database",
    "db_",
    "_db",
    "table_name",
    "table.",
    "token",
    "api_key",
    "secret",
    "auth",
    "wallet",
    "order",
    "trade",
    "trading",
    "live_trading",
    "execute",
    "execution",
    "sizing",
    "recommend",
    "recommendation",
    "notional",
    "position",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} does not support subclassing")


@dataclass(frozen=True)
class ResearchMarketResolutionLiquidityProbabilityFloorConfig(_FinalPublicDataclass):
    config_version: str
    pass_floor_threshold: Decimal
    block_floor_threshold: Decimal
    pass_liquidity_depth_score: Decimal
    block_liquidity_depth_score: Decimal
    pass_resolution_confidence_score: Decimal
    block_resolution_confidence_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            ResearchMarketResolutionLiquidityProbabilityFloorConfig,
        )
        _require_hard_flags("config", self)
        _require_safe_public_string("config_version", self.config_version)
        _require_probability("pass_floor_threshold", self.pass_floor_threshold)
        _require_probability("block_floor_threshold", self.block_floor_threshold)
        _require_probability(
            "pass_liquidity_depth_score",
            self.pass_liquidity_depth_score,
        )
        _require_probability(
            "block_liquidity_depth_score",
            self.block_liquidity_depth_score,
        )
        _require_probability(
            "pass_resolution_confidence_score",
            self.pass_resolution_confidence_score,
        )
        _require_probability(
            "block_resolution_confidence_score",
            self.block_resolution_confidence_score,
        )
        if self.block_floor_threshold > self.pass_floor_threshold:
            raise ValueError("block_floor_threshold must not exceed pass_floor_threshold")
        if self.block_liquidity_depth_score > self.pass_liquidity_depth_score:
            raise ValueError(
                "block_liquidity_depth_score must not exceed "
                "pass_liquidity_depth_score",
            )
        if (
            self.block_resolution_confidence_score
            > self.pass_resolution_confidence_score
        ):
            raise ValueError(
                "block_resolution_confidence_score must not exceed "
                "pass_resolution_confidence_score",
            )


@dataclass(frozen=True)
class ResearchMarketResolutionLiquidityProbabilityFloorObservation(
    _FinalPublicDataclass,
):
    observed_at: datetime
    observed_probability: Decimal
    liquidity_probability_floor: Decimal
    resolution_probability_floor: Decimal
    liquidity_depth_score: Decimal
    resolution_confidence_score: Decimal
    evidence_freshness_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "observation",
            self,
            ResearchMarketResolutionLiquidityProbabilityFloorObservation,
        )
        _require_hard_flags("observation", self)
        _require_datetime("observed_at", self.observed_at)
        _require_probability("observed_probability", self.observed_probability)
        _require_probability(
            "liquidity_probability_floor",
            self.liquidity_probability_floor,
        )
        _require_probability(
            "resolution_probability_floor",
            self.resolution_probability_floor,
        )
        _require_probability("liquidity_depth_score", self.liquidity_depth_score)
        _require_probability(
            "resolution_confidence_score",
            self.resolution_confidence_score,
        )
        _require_probability("evidence_freshness_score", self.evidence_freshness_score)


@dataclass(frozen=True)
class ResearchMarketResolutionLiquidityProbabilityFloorRow(_FinalPublicDataclass):
    analysis_rank: Decimal
    observed_at: datetime
    floor_status: str
    effective_probability_floor: Decimal
    probability_floor_gap: Decimal
    liquidity_probability_floor: Decimal
    resolution_probability_floor: Decimal
    observed_probability: Decimal
    liquidity_depth_score: Decimal
    resolution_confidence_score: Decimal
    evidence_freshness_score: Decimal
    diagnostic_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "row",
            self,
            ResearchMarketResolutionLiquidityProbabilityFloorRow,
        )
        _require_hard_flags("row", self)
        _require_positive_decimal("analysis_rank", self.analysis_rank)
        _require_datetime("observed_at", self.observed_at)
        _require_status("floor_status", self.floor_status)
        _require_probability(
            "effective_probability_floor",
            self.effective_probability_floor,
        )
        _require_finite_decimal("probability_floor_gap", self.probability_floor_gap)
        _require_probability(
            "liquidity_probability_floor",
            self.liquidity_probability_floor,
        )
        _require_probability(
            "resolution_probability_floor",
            self.resolution_probability_floor,
        )
        _require_probability("observed_probability", self.observed_probability)
        _require_probability("liquidity_depth_score", self.liquidity_depth_score)
        _require_probability(
            "resolution_confidence_score",
            self.resolution_confidence_score,
        )
        _require_probability("evidence_freshness_score", self.evidence_freshness_score)
        _require_diagnostic_codes("diagnostic_codes", self.diagnostic_codes)
        _validate_row_fields(self)
        _finalize_digest(self)


@dataclass(frozen=True)
class ResearchMarketResolutionLiquidityProbabilityFloorReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    report_status: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    minimum_effective_probability_floor: Decimal | None
    average_effective_probability_floor: Decimal | None
    minimum_liquidity_depth_score: Decimal | None
    minimum_resolution_confidence_score: Decimal | None
    rows: tuple[ResearchMarketResolutionLiquidityProbabilityFloorRow, ...]
    diagnostic_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "report",
            self,
            ResearchMarketResolutionLiquidityProbabilityFloorReport,
        )
        _validate_report_fields(self)
        _finalize_digest(self)


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def build_research_market_resolution_liquidity_probability_floor_report(
    observations: Iterable[ResearchMarketResolutionLiquidityProbabilityFloorObservation],
    *,
    config: ResearchMarketResolutionLiquidityProbabilityFloorConfig,
    generated_at: datetime,
) -> ResearchMarketResolutionLiquidityProbabilityFloorReport:
    if type(config) is not ResearchMarketResolutionLiquidityProbabilityFloorConfig:
        raise ValueError(
            "config must be a ResearchMarketResolutionLiquidityProbabilityFloorConfig",
        )
    _require_datetime("generated_at", generated_at)
    normalized = _normalize_observations(observations)
    row_inputs = tuple(_row_input(observation, config) for observation in normalized)
    sorted_row_inputs = sorted(
        row_inputs,
        key=_row_input_sort_key,
    )
    rows = tuple(
        ResearchMarketResolutionLiquidityProbabilityFloorRow(
            analysis_rank=Decimal(str(index + 1)),
            observed_at=item["observed_at"],
            floor_status=item["floor_status"],
            effective_probability_floor=item["effective_probability_floor"],
            probability_floor_gap=item["probability_floor_gap"],
            liquidity_probability_floor=item["liquidity_probability_floor"],
            resolution_probability_floor=item["resolution_probability_floor"],
            observed_probability=item["observed_probability"],
            liquidity_depth_score=item["liquidity_depth_score"],
            resolution_confidence_score=item["resolution_confidence_score"],
            evidence_freshness_score=item["evidence_freshness_score"],
            diagnostic_codes=item["diagnostic_codes"],
        )
        for index, item in enumerate(sorted_row_inputs)
    )
    pass_count = _count_rows(rows, "pass")
    watch_count = _count_rows(rows, "watch")
    block_count = _count_rows(rows, "block")
    input_count = Decimal(str(len(rows)))
    effective_floors = tuple(row.effective_probability_floor for row in rows)
    liquidity_scores = tuple(row.liquidity_depth_score for row in rows)
    confidence_scores = tuple(row.resolution_confidence_score for row in rows)
    report_status = _report_status(rows)
    return ResearchMarketResolutionLiquidityProbabilityFloorReport(
        generated_at=generated_at,
        config_version=config.config_version,
        report_status=report_status,
        input_count=input_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        minimum_effective_probability_floor=(
            min(effective_floors) if effective_floors else None
        ),
        average_effective_probability_floor=(
            _average(effective_floors)
            if input_count != _ZERO
            else None
        ),
        minimum_liquidity_depth_score=(
            min(liquidity_scores) if liquidity_scores else None
        ),
        minimum_resolution_confidence_score=(
            min(confidence_scores) if confidence_scores else None
        ),
        rows=rows,
        diagnostic_codes=_report_diagnostic_codes(report_status, rows),
    )


def research_market_resolution_liquidity_probability_floor_report_payload(
    report: ResearchMarketResolutionLiquidityProbabilityFloorReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchMarketResolutionLiquidityProbabilityFloorReport:
        _validate_report_integrity(report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _require_hard_flags("payload", _DictFlags(report))
        _reject_public_numerics("payload", report)
        _reject_unsafe_public_payload("payload", report)
        _require_public_statuses("payload", report)
        _validate_public_payload_schema(report)
        _verify_public_payload_integrity(report)
        validated_report = _report_from_public_payload(report)
        _validate_report_integrity(validated_report)
        payload = _json_ready(validated_report)
        if payload != report:
            raise ValueError("payload values must use canonical public schema encoding")
    else:
        raise ValueError(
            "report must be a ResearchMarketResolutionLiquidityProbabilityFloorReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_public_numerics("payload", payload)
    _reject_unsafe_public_payload("payload", payload)
    _require_public_statuses("payload", payload)
    _validate_public_payload_schema(payload)
    _verify_public_payload_integrity(payload)
    return payload


def _normalize_observations(
    observations: Iterable[ResearchMarketResolutionLiquidityProbabilityFloorObservation],
) -> tuple[ResearchMarketResolutionLiquidityProbabilityFloorObservation, ...]:
    if isinstance(observations, (str, bytes, dict)):
        raise ValueError("observations must be an iterable of observations")
    if not isinstance(observations, Iterable):
        raise ValueError("observations must be an iterable of observations")
    normalized = tuple(observations)
    for item in normalized:
        if type(item) is not ResearchMarketResolutionLiquidityProbabilityFloorObservation:
            raise ValueError(
                "observations must contain "
                "ResearchMarketResolutionLiquidityProbabilityFloorObservation",
            )
    return normalized


def _row_input_sort_key(item: dict[str, Any]) -> tuple[object, ...]:
    return (
        _STATUS_SORT_KEY[item["floor_status"]],
        item["effective_probability_floor"],
        item["liquidity_depth_score"],
        item["resolution_confidence_score"],
        item["observed_at"],
        item["observed_probability"],
        item["liquidity_probability_floor"],
        item["resolution_probability_floor"],
        item["evidence_freshness_score"],
        item["probability_floor_gap"],
        item["diagnostic_codes"],
    )


def _row_input(
    observation: ResearchMarketResolutionLiquidityProbabilityFloorObservation,
    config: ResearchMarketResolutionLiquidityProbabilityFloorConfig,
) -> dict[str, Any]:
    effective_floor = min(
        observation.observed_probability,
        observation.liquidity_probability_floor,
        observation.resolution_probability_floor,
    )
    status = _floor_status(observation, config, effective_floor)
    return {
        "observed_at": observation.observed_at,
        "floor_status": status,
        "effective_probability_floor": effective_floor,
        "probability_floor_gap": _quantized_difference(
            effective_floor,
            config.pass_floor_threshold,
        ),
        "liquidity_probability_floor": observation.liquidity_probability_floor,
        "resolution_probability_floor": observation.resolution_probability_floor,
        "observed_probability": observation.observed_probability,
        "liquidity_depth_score": observation.liquidity_depth_score,
        "resolution_confidence_score": observation.resolution_confidence_score,
        "evidence_freshness_score": observation.evidence_freshness_score,
        "diagnostic_codes": _row_diagnostic_codes(
            observation,
            config,
            effective_floor,
            status,
        ),
    }


def _floor_status(
    observation: ResearchMarketResolutionLiquidityProbabilityFloorObservation,
    config: ResearchMarketResolutionLiquidityProbabilityFloorConfig,
    effective_floor: Decimal,
) -> str:
    if (
        effective_floor < config.block_floor_threshold
        or observation.liquidity_depth_score < config.block_liquidity_depth_score
        or observation.resolution_confidence_score
        < config.block_resolution_confidence_score
    ):
        return "block"
    if (
        effective_floor >= config.pass_floor_threshold
        and observation.liquidity_depth_score >= config.pass_liquidity_depth_score
        and observation.resolution_confidence_score
        >= config.pass_resolution_confidence_score
    ):
        return "pass"
    return "watch"


def _row_diagnostic_codes(
    observation: ResearchMarketResolutionLiquidityProbabilityFloorObservation,
    config: ResearchMarketResolutionLiquidityProbabilityFloorConfig,
    effective_floor: Decimal,
    status: str,
) -> tuple[str, ...]:
    codes = [f"floor_status_{status}"]
    codes.append(
        _threshold_code(
            "probability_floor",
            effective_floor,
            config.block_floor_threshold,
            config.pass_floor_threshold,
        ),
    )
    codes.append(
        _threshold_code(
            "liquidity_depth",
            observation.liquidity_depth_score,
            config.block_liquidity_depth_score,
            config.pass_liquidity_depth_score,
        ),
    )
    codes.append(
        _threshold_code(
            "resolution_confidence",
            observation.resolution_confidence_score,
            config.block_resolution_confidence_score,
            config.pass_resolution_confidence_score,
        ),
    )
    return tuple(dict.fromkeys(codes))


def _threshold_code(
    prefix: str,
    value: Decimal,
    block_threshold: Decimal,
    pass_threshold: Decimal,
) -> str:
    if value < block_threshold:
        return f"{prefix}_block"
    if value >= pass_threshold:
        return f"{prefix}_pass"
    return f"{prefix}_watch"


def _report_status(
    rows: tuple[ResearchMarketResolutionLiquidityProbabilityFloorRow, ...],
) -> str:
    if not rows:
        return "watch"
    if any(row.floor_status == "block" for row in rows):
        return "block"
    if any(row.floor_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_diagnostic_codes(
    report_status: str,
    rows: tuple[ResearchMarketResolutionLiquidityProbabilityFloorRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("floor_input_empty_watch",)
    codes = [f"floor_report_{report_status}"]
    codes.extend(row.floor_status for row in rows)
    return tuple(dict.fromkeys(codes))


def _count_rows(
    rows: tuple[ResearchMarketResolutionLiquidityProbabilityFloorRow, ...],
    status: str,
) -> Decimal:
    return sum(
        (Decimal("1") for row in rows if row.floor_status == status),
        _ZERO,
    )


def _validate_row_fields(
    row: ResearchMarketResolutionLiquidityProbabilityFloorRow,
) -> None:
    if row.analysis_rank != row.analysis_rank.to_integral_value():
        raise ValueError("analysis_rank must be a whole Decimal")
    expected_effective_floor = min(
        row.observed_probability,
        row.liquidity_probability_floor,
        row.resolution_probability_floor,
    )
    if row.effective_probability_floor != expected_effective_floor:
        raise ValueError("effective_probability_floor must match row probability floors")
    if row.probability_floor_gap != _quantize(row.probability_floor_gap):
        raise ValueError("probability_floor_gap must use six decimal places")
    with localcontext(_DECIMAL_CONTEXT):
        implied_pass_floor = (
            row.effective_probability_floor - row.probability_floor_gap
        )
    if implied_pass_floor < _ZERO or implied_pass_floor > _ONE:
        raise ValueError("probability_floor_gap implies an invalid pass floor")
    if len(row.diagnostic_codes) != len(_ROW_DIAGNOSTIC_PREFIXES):
        raise ValueError("diagnostic_codes must match the row schema")
    for index, (code, prefix) in enumerate(
        zip(row.diagnostic_codes, _ROW_DIAGNOSTIC_PREFIXES, strict=True),
    ):
        allowed_codes = tuple(f"{prefix}{status}" for status in _ALLOWED_STATUSES)
        if code not in allowed_codes:
            raise ValueError("diagnostic_codes must match the row schema")
        if index == 0 and code != f"floor_status_{row.floor_status}":
            raise ValueError("diagnostic_codes must match floor_status")


def _row_sort_key(
    row: ResearchMarketResolutionLiquidityProbabilityFloorRow,
) -> tuple[object, ...]:
    return (
        _STATUS_SORT_KEY[row.floor_status],
        row.effective_probability_floor,
        row.liquidity_depth_score,
        row.resolution_confidence_score,
        row.observed_at,
        row.observed_probability,
        row.liquidity_probability_floor,
        row.resolution_probability_floor,
        row.evidence_freshness_score,
        row.probability_floor_gap,
        row.diagnostic_codes,
    )


def _validate_report_fields(
    report: ResearchMarketResolutionLiquidityProbabilityFloorReport,
) -> None:
    _require_hard_flags("report", report)
    _require_datetime("generated_at", report.generated_at)
    _require_safe_public_string("config_version", report.config_version)
    _require_status("report_status", report.report_status)
    _require_count("input_count", report.input_count)
    _require_count("pass_count", report.pass_count)
    _require_count("watch_count", report.watch_count)
    _require_count("block_count", report.block_count)
    _require_optional_probability(
        "minimum_effective_probability_floor",
        report.minimum_effective_probability_floor,
    )
    _require_optional_probability(
        "average_effective_probability_floor",
        report.average_effective_probability_floor,
    )
    _require_optional_probability(
        "minimum_liquidity_depth_score",
        report.minimum_liquidity_depth_score,
    )
    _require_optional_probability(
        "minimum_resolution_confidence_score",
        report.minimum_resolution_confidence_score,
    )
    if type(report.rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in report.rows:
        if type(row) is not ResearchMarketResolutionLiquidityProbabilityFloorRow:
            raise ValueError(
                "rows must contain "
                "ResearchMarketResolutionLiquidityProbabilityFloorRow",
            )
        _validate_row_fields(row)
    _require_diagnostic_codes("diagnostic_codes", report.diagnostic_codes)
    row_count = Decimal(str(len(report.rows)))
    if report.input_count != row_count:
        raise ValueError("input_count must match rows")
    if report.pass_count + report.watch_count + report.block_count != row_count:
        raise ValueError("status counts must match rows")
    if report.pass_count != _count_rows(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count_rows(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count_rows(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    for index, row in enumerate(report.rows, start=1):
        if row.analysis_rank != Decimal(str(index)):
            raise ValueError("analysis_rank must be contiguous and match row order")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic canonical ordering")
    expected_diagnostic_codes = _report_diagnostic_codes(
        report.report_status,
        report.rows,
    )
    if report.diagnostic_codes != expected_diagnostic_codes:
        raise ValueError("diagnostic_codes must match report rows")
    _require_summary_values(report)


def _require_summary_values(
    report: ResearchMarketResolutionLiquidityProbabilityFloorReport,
) -> None:
    if not report.rows:
        if report.minimum_effective_probability_floor is not None:
            raise ValueError("minimum_effective_probability_floor must be None")
        if report.average_effective_probability_floor is not None:
            raise ValueError("average_effective_probability_floor must be None")
        if report.minimum_liquidity_depth_score is not None:
            raise ValueError("minimum_liquidity_depth_score must be None")
        if report.minimum_resolution_confidence_score is not None:
            raise ValueError("minimum_resolution_confidence_score must be None")
        return
    effective_floors = tuple(row.effective_probability_floor for row in report.rows)
    liquidity_scores = tuple(row.liquidity_depth_score for row in report.rows)
    confidence_scores = tuple(row.resolution_confidence_score for row in report.rows)
    if report.minimum_effective_probability_floor != min(effective_floors):
        raise ValueError("minimum_effective_probability_floor must match rows")
    expected_average = _average(effective_floors)
    if report.average_effective_probability_floor != expected_average:
        raise ValueError("average_effective_probability_floor must match rows")
    if report.minimum_liquidity_depth_score != min(liquidity_scores):
        raise ValueError("minimum_liquidity_depth_score must match rows")
    if report.minimum_resolution_confidence_score != min(confidence_scores):
        raise ValueError("minimum_resolution_confidence_score must match rows")


def _validate_report_integrity(
    report: ResearchMarketResolutionLiquidityProbabilityFloorReport,
) -> None:
    _validate_report_fields(report)
    for row in report.rows:
        _verify_digest(row)
    _verify_digest(report)


def _validate_public_payload_schema(payload: dict[str, Any]) -> None:
    _require_exact_public_fields("payload", payload, _REPORT_PAYLOAD_FIELDS)
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("payload.rows must be a list")
    for index, row in enumerate(rows):
        if type(row) is not dict:
            raise ValueError("payload.rows must contain JSON objects")
        _require_exact_public_fields(
            f"payload.rows[{index}]",
            row,
            _ROW_PAYLOAD_FIELDS,
        )


def _require_exact_public_fields(
    label: str,
    payload: dict[str, Any],
    expected_fields: frozenset[str],
) -> None:
    if frozenset(payload) != expected_fields:
        raise ValueError(f"{label} fields do not match the public schema")


def _report_from_public_payload(
    payload: dict[str, Any],
) -> ResearchMarketResolutionLiquidityProbabilityFloorReport:
    rows_value = payload["rows"]
    if type(rows_value) is not list:
        raise ValueError("payload.rows must be a list")
    rows = tuple(
        _row_from_public_payload(index, row)
        for index, row in enumerate(rows_value)
    )
    return ResearchMarketResolutionLiquidityProbabilityFloorReport(
        generated_at=_public_datetime("generated_at", payload["generated_at"]),
        config_version=payload["config_version"],
        report_status=payload["report_status"],
        input_count=_public_decimal("input_count", payload["input_count"]),
        pass_count=_public_decimal("pass_count", payload["pass_count"]),
        watch_count=_public_decimal("watch_count", payload["watch_count"]),
        block_count=_public_decimal("block_count", payload["block_count"]),
        minimum_effective_probability_floor=_public_optional_decimal(
            "minimum_effective_probability_floor",
            payload["minimum_effective_probability_floor"],
        ),
        average_effective_probability_floor=_public_optional_decimal(
            "average_effective_probability_floor",
            payload["average_effective_probability_floor"],
        ),
        minimum_liquidity_depth_score=_public_optional_decimal(
            "minimum_liquidity_depth_score",
            payload["minimum_liquidity_depth_score"],
        ),
        minimum_resolution_confidence_score=_public_optional_decimal(
            "minimum_resolution_confidence_score",
            payload["minimum_resolution_confidence_score"],
        ),
        rows=rows,
        diagnostic_codes=_public_diagnostic_codes(
            "diagnostic_codes",
            payload["diagnostic_codes"],
        ),
        derived_validation_digest=payload["derived_validation_digest"],
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _row_from_public_payload(
    index: int,
    payload: object,
) -> ResearchMarketResolutionLiquidityProbabilityFloorRow:
    if type(payload) is not dict:
        raise ValueError("payload.rows must contain JSON objects")
    label = f"payload.rows[{index}]"
    return ResearchMarketResolutionLiquidityProbabilityFloorRow(
        analysis_rank=_public_decimal(
            f"{label}.analysis_rank",
            payload["analysis_rank"],
        ),
        observed_at=_public_datetime(
            f"{label}.observed_at",
            payload["observed_at"],
        ),
        floor_status=payload["floor_status"],
        effective_probability_floor=_public_decimal(
            f"{label}.effective_probability_floor",
            payload["effective_probability_floor"],
        ),
        probability_floor_gap=_public_decimal(
            f"{label}.probability_floor_gap",
            payload["probability_floor_gap"],
        ),
        liquidity_probability_floor=_public_decimal(
            f"{label}.liquidity_probability_floor",
            payload["liquidity_probability_floor"],
        ),
        resolution_probability_floor=_public_decimal(
            f"{label}.resolution_probability_floor",
            payload["resolution_probability_floor"],
        ),
        observed_probability=_public_decimal(
            f"{label}.observed_probability",
            payload["observed_probability"],
        ),
        liquidity_depth_score=_public_decimal(
            f"{label}.liquidity_depth_score",
            payload["liquidity_depth_score"],
        ),
        resolution_confidence_score=_public_decimal(
            f"{label}.resolution_confidence_score",
            payload["resolution_confidence_score"],
        ),
        evidence_freshness_score=_public_decimal(
            f"{label}.evidence_freshness_score",
            payload["evidence_freshness_score"],
        ),
        diagnostic_codes=_public_diagnostic_codes(
            f"{label}.diagnostic_codes",
            payload["diagnostic_codes"],
        ),
        derived_validation_digest=payload["derived_validation_digest"],
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _public_decimal(label: str, value: object) -> Decimal:
    if type(value) is not str or not value:
        raise ValueError(f"{label} must be a canonical Decimal string")
    try:
        parsed = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{label} must be a canonical Decimal string") from exc
    if not parsed.is_finite() or str(parsed) != value:
        raise ValueError(f"{label} must be a canonical finite Decimal string")
    return parsed


def _public_optional_decimal(label: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _public_decimal(label, value)


def _public_datetime(label: str, value: object) -> datetime:
    if type(value) is not str or not value:
        raise ValueError(f"{label} must be a canonical UTC datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{label} must be a canonical UTC datetime string") from exc
    _require_datetime(label, parsed)
    canonical = parsed.astimezone(UTC).isoformat()
    if value != canonical:
        raise ValueError(f"{label} must be a canonical UTC datetime string")
    return parsed


def _public_diagnostic_codes(label: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{label} must be a list")
    return tuple(value)


def _verify_public_payload_integrity(payload: dict[str, Any]) -> None:
    _verify_public_payload_digest("payload", payload)
    rows = payload.get("rows")
    if rows is None:
        return
    if type(rows) is not list:
        raise ValueError("payload.rows must be a list")
    for index, row in enumerate(rows):
        if type(row) is not dict:
            raise ValueError("payload.rows must contain JSON objects")
        _verify_public_payload_digest(f"payload.rows[{index}]", row)


def _verify_public_payload_digest(label: str, payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_digest(f"{label} derived_validation_digest", digest)
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    expected_digest = _canonical_digest(unsigned_payload)
    if digest != expected_digest:
        raise ValueError(f"{label} derived_validation_digest mismatch")


def _finalize_digest(value: object) -> None:
    digest = getattr(value, "derived_validation_digest", None)
    expected = _dataclass_digest(value)
    if digest == "":
        object.__setattr__(value, "derived_validation_digest", expected)
        return
    _require_digest("derived_validation_digest", digest)
    if digest != expected:
        raise ValueError("derived_validation_digest mismatch")


def _verify_digest(value: object) -> None:
    digest = getattr(value, "derived_validation_digest", None)
    _require_digest("derived_validation_digest", digest)
    if digest != _dataclass_digest(value):
        raise ValueError("derived_validation_digest mismatch")


def _dataclass_digest(value: object) -> str:
    payload = _json_ready(asdict(value))
    if type(payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return _canonical_digest(payload)


def _canonical_digest(payload: object) -> str:
    json_payload = _json_ready(payload)
    encoded = json.dumps(
        json_payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be a Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is bool:
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is str:
        return value
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if type(value) in (list, tuple):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _require_exact_type(label: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_digest(label: str, value: object) -> None:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{label} must be a lowercase sha256 digest")


def _require_probability(label: str, value: object) -> None:
    _require_finite_decimal(label, value)
    if value < _ZERO or value > _ONE:
        raise ValueError(f"{label} must be between 0 and 1")


def _require_optional_probability(label: str, value: object) -> None:
    if value is None:
        return
    _require_probability(label, value)


def _require_finite_decimal(label: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{label} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{label} must be finite")


def _require_positive_decimal(label: str, value: object) -> None:
    _require_finite_decimal(label, value)
    if value <= _ZERO:
        raise ValueError(f"{label} must be positive")


def _require_count(label: str, value: object) -> None:
    _require_finite_decimal(label, value)
    if value < _ZERO:
        raise ValueError(f"{label} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{label} must be a whole Decimal")


def _require_datetime(label: str, value: object) -> None:
    if type(value) is not datetime:
        raise ValueError(f"{label} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{label} must be timezone-aware")


def _require_status(label: str, value: object) -> None:
    if type(value) is not str or value not in _ALLOWED_STATUSES:
        raise ValueError(f"{label} status must be pass, watch, or block")


def _require_diagnostic_codes(label: str, value: object) -> None:
    if type(value) is not tuple:
        raise ValueError(f"{label} must be a tuple")
    for code in value:
        _require_safe_public_string(label, code)
    if len(value) != len(set(value)):
        raise ValueError(f"{label} must not contain duplicates")


def _require_safe_public_string(label: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{label} must be a nonempty string")
    if _has_unsafe_surface_fragment(value):
        raise ValueError(f"{label} has unsafe surface value")


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        raise ValueError("average requires at least one Decimal")
    with localcontext(_DECIMAL_CONTEXT):
        return (sum(values, _ZERO) / Decimal(str(len(values)))).quantize(_QUANT)


def _quantized_difference(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return (left - right).quantize(_QUANT)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANT)


def _reject_public_numerics(label: str, value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is Decimal:
        return
    if isinstance(value, float):
        raise ValueError(f"{label} public numeric value must not be a float")
    if type(value) is int:
        raise ValueError(f"{label} public numeric value must use Decimal")
    if is_dataclass(value) and not isinstance(value, type):
        _reject_public_numerics(label, asdict(value))
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_public_numerics(key, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_public_numerics(label, item)


def _require_public_statuses(label: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if key.endswith("_status"):
                _require_status(key, item)
            _require_public_statuses(key, item)
        return
    if type(value) is list:
        for item in value:
            _require_public_statuses(label, item)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if type(value) is str:
        if _has_unsafe_surface_fragment(value):
            raise ValueError(f"unsafe surface value in {label}")
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_surface_fragment(key):
                raise ValueError(f"unsafe surface field in {label}")
            _reject_unsafe_public_payload(key, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)


def _has_unsafe_surface_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in _SURFACE_FRAGMENTS)


__all__ = (
    "ResearchMarketResolutionLiquidityProbabilityFloorConfig",
    "ResearchMarketResolutionLiquidityProbabilityFloorObservation",
    "ResearchMarketResolutionLiquidityProbabilityFloorReport",
    "ResearchMarketResolutionLiquidityProbabilityFloorRow",
    "build_research_market_resolution_liquidity_probability_floor_report",
    "research_market_resolution_liquidity_probability_floor_report_payload",
)
