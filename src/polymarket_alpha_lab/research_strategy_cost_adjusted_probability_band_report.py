"""Pure report-only cost-adjusted probability band report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any, Iterable


DEFAULT_RESEARCH_STRATEGY_COST_ADJUSTED_PROBABILITY_BAND_REPORT_CONFIG_VERSION = (
    "research-strategy-cost-adjusted-probability-band-report-v0"
)
RESEARCH_STRATEGY_COST_ADJUSTED_PROBABILITY_BAND_STATUSES = (
    "pass",
    "watch",
    "block",
)

RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_MARKET_BAND_POSITIONS = ("below_band", "inside_band", "above_band")
_UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate_ref",
    "market_ref",
    "market_slug",
    "question",
    "url",
    "dsn",
    "table",
    "token",
    "wal" + "let",
    "or" + "der",
    "trad" + "e",
    "li" + "ve",
    "private",
    "secret",
    "credential",
)

ROW_REASON_CODES = (
    "cost_adjusted_probability_band_pass",
    "model_confidence_block",
    "model_confidence_watch",
    "cost_drag_block",
    "cost_drag_watch",
    "liquidity_quality_block",
    "liquidity_quality_watch",
    "resolution_ambiguity_block",
    "resolution_ambiguity_watch",
    "band_width_block",
    "band_width_watch",
    "market_probability_distance_block",
    "market_probability_distance_watch",
)
REPORT_REASON_CODES = (
    "cost_adjusted_probability_band_report_block",
    "cost_adjusted_probability_band_report_empty",
    "cost_adjusted_probability_band_report_pass",
    "cost_adjusted_probability_band_report_watch",
    "model_confidence_review",
    "cost_drag_review",
    "liquidity_quality_review",
    "resolution_ambiguity_review",
    "band_width_review",
    "market_probability_distance_review",
)


@dataclass(frozen=True)
class ResearchStrategyCostAdjustedProbabilityBandConfig:
    config_version: str
    model_confidence_pass_floor: Decimal
    model_confidence_watch_floor: Decimal
    total_cost_drag_pass_ceiling: Decimal
    total_cost_drag_watch_ceiling: Decimal
    liquidity_quality_pass_floor: Decimal
    liquidity_quality_watch_floor: Decimal
    resolution_ambiguity_pass_ceiling: Decimal
    resolution_ambiguity_watch_ceiling: Decimal
    band_half_width_pass_ceiling: Decimal
    band_half_width_watch_ceiling: Decimal
    market_distance_pass_ceiling: Decimal
    market_distance_watch_ceiling: Decimal
    model_confidence_uncertainty_weight: Decimal
    liquidity_uncertainty_weight: Decimal
    resolution_ambiguity_uncertainty_weight: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_public_string("config_version", self.config_version)
        for field_name in (
            "model_confidence_pass_floor",
            "model_confidence_watch_floor",
            "total_cost_drag_pass_ceiling",
            "total_cost_drag_watch_ceiling",
            "liquidity_quality_pass_floor",
            "liquidity_quality_watch_floor",
            "resolution_ambiguity_pass_ceiling",
            "resolution_ambiguity_watch_ceiling",
            "band_half_width_pass_ceiling",
            "band_half_width_watch_ceiling",
            "market_distance_pass_ceiling",
            "market_distance_watch_ceiling",
            "model_confidence_uncertainty_weight",
            "liquidity_uncertainty_weight",
            "resolution_ambiguity_uncertainty_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_floor_pair(
            "model_confidence",
            self.model_confidence_pass_floor,
            self.model_confidence_watch_floor,
        )
        _require_ceiling_pair(
            "total_cost_drag",
            self.total_cost_drag_pass_ceiling,
            self.total_cost_drag_watch_ceiling,
        )
        _require_floor_pair(
            "liquidity_quality",
            self.liquidity_quality_pass_floor,
            self.liquidity_quality_watch_floor,
        )
        _require_ceiling_pair(
            "resolution_ambiguity",
            self.resolution_ambiguity_pass_ceiling,
            self.resolution_ambiguity_watch_ceiling,
        )
        _require_ceiling_pair(
            "band_half_width",
            self.band_half_width_pass_ceiling,
            self.band_half_width_watch_ceiling,
        )
        _require_ceiling_pair(
            "market_distance",
            self.market_distance_pass_ceiling,
            self.market_distance_watch_ceiling,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyCostAdjustedProbabilityBandInput:
    candidate_ref: str
    market_ref: str
    observed_at: datetime
    model_probability: Decimal
    model_confidence_score: Decimal
    market_probability: Decimal
    fee_probability_drag: Decimal
    spread_probability_drag: Decimal
    slippage_probability_drag: Decimal
    liquidity_quality_score: Decimal
    resolution_ambiguity_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("candidate_ref", "market_ref"):
            _require_canonical_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "model_probability",
            "model_confidence_score",
            "market_probability",
            "fee_probability_drag",
            "spread_probability_drag",
            "slippage_probability_drag",
            "liquidity_quality_score",
            "resolution_ambiguity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyCostAdjustedProbabilityBandReasonCodeCount:
    reason_code: str
    count: Decimal
    input_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_count("count", self.count),
        )
        object.__setattr__(
            self,
            "input_ratio",
            _normalize_probability("input_ratio", self.input_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchStrategyCostAdjustedProbabilityBandRow:
    candidate_ref: str
    market_ref: str
    observed_at: datetime
    model_probability: Decimal
    model_confidence_score: Decimal
    market_probability: Decimal
    fee_probability_drag: Decimal
    spread_probability_drag: Decimal
    slippage_probability_drag: Decimal
    total_cost_drag_probability: Decimal
    cost_adjusted_midpoint_probability: Decimal
    band_half_width_probability: Decimal
    cost_adjusted_lower_probability: Decimal
    cost_adjusted_upper_probability: Decimal
    market_distance_from_band: Decimal
    market_band_position: str
    liquidity_quality_score: Decimal
    resolution_ambiguity_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("candidate_ref", "market_ref"):
            _require_canonical_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "model_probability",
            "model_confidence_score",
            "market_probability",
            "fee_probability_drag",
            "spread_probability_drag",
            "slippage_probability_drag",
            "total_cost_drag_probability",
            "cost_adjusted_midpoint_probability",
            "band_half_width_probability",
            "cost_adjusted_lower_probability",
            "cost_adjusted_upper_probability",
            "market_distance_from_band",
            "liquidity_quality_score",
            "resolution_ambiguity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_market_band_position("market_band_position", self.market_band_position)
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("row", self)
        _apply_or_verify_digest(self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchStrategyCostAdjustedProbabilityBandReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    mean_model_confidence_score: Decimal
    mean_total_cost_drag_probability: Decimal
    mean_band_half_width_probability: Decimal
    mean_market_distance_from_band: Decimal
    mean_liquidity_quality_score: Decimal
    mean_resolution_ambiguity_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchStrategyCostAdjustedProbabilityBandReasonCodeCount, ...]
    rows: tuple[ResearchStrategyCostAdjustedProbabilityBandRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_public_string("config_version", self.config_version)
        for field_name in ("input_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_model_confidence_score",
            "mean_total_cost_drag_probability",
            "mean_band_half_width_probability",
            "mean_market_distance_from_band",
            "mean_liquidity_quality_score",
            "mean_resolution_ambiguity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _apply_or_verify_digest(self)
        _validate_report_consistency(self)


def build_research_strategy_cost_adjusted_probability_band_report(
    inputs: Iterable[ResearchStrategyCostAdjustedProbabilityBandInput],
    *,
    config: ResearchStrategyCostAdjustedProbabilityBandConfig,
    generated_at: datetime,
) -> ResearchStrategyCostAdjustedProbabilityBandReport:
    if type(config) is not ResearchStrategyCostAdjustedProbabilityBandConfig:
        raise ValueError(
            "config must be a ResearchStrategyCostAdjustedProbabilityBandConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (
                _row_from_input(
                    value,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for value in normalized_inputs
            ),
            key=_row_sort_key,
        ),
    )
    return ResearchStrategyCostAdjustedProbabilityBandReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        mean_model_confidence_score=_mean(
            tuple(row.model_confidence_score for row in rows),
        ),
        mean_total_cost_drag_probability=_mean(
            tuple(row.total_cost_drag_probability for row in rows),
        ),
        mean_band_half_width_probability=_mean(
            tuple(row.band_half_width_probability for row in rows),
        ),
        mean_market_distance_from_band=_mean(
            tuple(row.market_distance_from_band for row in rows),
        ),
        mean_liquidity_quality_score=_mean(
            tuple(row.liquidity_quality_score for row in rows),
        ),
        mean_resolution_ambiguity_score=_mean(
            tuple(row.resolution_ambiguity_score for row in rows),
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts_from_rows(rows),
        rows=rows,
    )


def research_strategy_cost_adjusted_probability_band_report_payload(
    report: ResearchStrategyCostAdjustedProbabilityBandReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyCostAdjustedProbabilityBandReport:
        _require_hard_flags("report", report)
        _verify_report_integrity(report)
        payload = _public_report_payload(report)
    elif type(report) is dict:
        _require_hard_flags("payload", _DictFlags(report))
        _reject_unsafe_public_payload("payload", report)
        _verify_public_payload_integrity(report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchStrategyCostAdjustedProbabilityBandReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


def _public_report_payload(
    report: ResearchStrategyCostAdjustedProbabilityBandReport,
) -> dict[str, Any]:
    payload = asdict(report)
    payload["rows"] = [
        _public_row_payload(index, row)
        for index, row in enumerate(report.rows, start=1)
    ]
    payload.pop("derived_validation_digest", None)
    public_payload = _json_ready(payload)
    if type(public_payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    public_payload["derived_validation_digest"] = _public_payload_digest(public_payload)
    _verify_public_payload_integrity(public_payload)
    return public_payload


def _public_row_payload(
    row_number: int,
    row: ResearchStrategyCostAdjustedProbabilityBandRow,
) -> dict[str, Any]:
    payload = asdict(row)
    for field_name in ("candidate_ref", "market_ref"):
        payload.pop(field_name, None)
    payload.pop("derived_validation_digest", None)
    payload["row_number"] = _count(row_number)
    public_payload = _json_ready(payload)
    if type(public_payload) is not dict:
        raise ValueError("row payload must be a JSON object")
    public_payload["derived_validation_digest"] = _public_payload_digest(public_payload)
    return public_payload


def _row_from_input(
    value: ResearchStrategyCostAdjustedProbabilityBandInput,
    *,
    config: ResearchStrategyCostAdjustedProbabilityBandConfig,
    generated_at: datetime,
) -> ResearchStrategyCostAdjustedProbabilityBandRow:
    observed_at = _as_utc("observed_at", value.observed_at)
    if observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    total_cost_drag_probability = _sum_decimals(
        (
            value.fee_probability_drag,
            value.spread_probability_drag,
            value.slippage_probability_drag,
        ),
    )
    cost_adjusted_midpoint_probability = _clamp_probability(
        _subtract_decimal(value.model_probability, total_cost_drag_probability),
    )
    band_half_width_probability = _band_half_width(
        value,
        total_cost_drag_probability=total_cost_drag_probability,
        config=config,
    )
    cost_adjusted_lower_probability = _clamp_probability(
        _subtract_decimal(cost_adjusted_midpoint_probability, band_half_width_probability),
    )
    cost_adjusted_upper_probability = _clamp_probability(
        _sum_decimals((cost_adjusted_midpoint_probability, band_half_width_probability)),
    )
    market_distance_from_band = _market_distance_from_band(
        market_probability=value.market_probability,
        lower_probability=cost_adjusted_lower_probability,
        upper_probability=cost_adjusted_upper_probability,
    )
    market_band_position = _market_band_position(
        market_probability=value.market_probability,
        lower_probability=cost_adjusted_lower_probability,
        upper_probability=cost_adjusted_upper_probability,
    )
    return ResearchStrategyCostAdjustedProbabilityBandRow(
        candidate_ref=value.candidate_ref,
        market_ref=value.market_ref,
        observed_at=observed_at,
        model_probability=value.model_probability,
        model_confidence_score=value.model_confidence_score,
        market_probability=value.market_probability,
        fee_probability_drag=value.fee_probability_drag,
        spread_probability_drag=value.spread_probability_drag,
        slippage_probability_drag=value.slippage_probability_drag,
        total_cost_drag_probability=total_cost_drag_probability,
        cost_adjusted_midpoint_probability=cost_adjusted_midpoint_probability,
        band_half_width_probability=band_half_width_probability,
        cost_adjusted_lower_probability=cost_adjusted_lower_probability,
        cost_adjusted_upper_probability=cost_adjusted_upper_probability,
        market_distance_from_band=market_distance_from_band,
        market_band_position=market_band_position,
        liquidity_quality_score=value.liquidity_quality_score,
        resolution_ambiguity_score=value.resolution_ambiguity_score,
        status=_row_status(
            value=value,
            total_cost_drag_probability=total_cost_drag_probability,
            band_half_width_probability=band_half_width_probability,
            market_distance_from_band=market_distance_from_band,
            config=config,
        ),
        reason_codes=_row_reason_codes(
            value=value,
            total_cost_drag_probability=total_cost_drag_probability,
            band_half_width_probability=band_half_width_probability,
            market_distance_from_band=market_distance_from_band,
            config=config,
        ),
    )


def _band_half_width(
    value: ResearchStrategyCostAdjustedProbabilityBandInput,
    *,
    total_cost_drag_probability: Decimal,
    config: ResearchStrategyCostAdjustedProbabilityBandConfig,
) -> Decimal:
    confidence_uncertainty = _multiply_decimal(
        _subtract_decimal(ONE, value.model_confidence_score),
        config.model_confidence_uncertainty_weight,
    )
    liquidity_uncertainty = _multiply_decimal(
        _subtract_decimal(ONE, value.liquidity_quality_score),
        config.liquidity_uncertainty_weight,
    )
    resolution_uncertainty = _multiply_decimal(
        value.resolution_ambiguity_score,
        config.resolution_ambiguity_uncertainty_weight,
    )
    return _clamp_probability(
        _sum_decimals(
            (
                total_cost_drag_probability,
                confidence_uncertainty,
                liquidity_uncertainty,
                resolution_uncertainty,
            ),
        ),
    )


def _row_status(
    *,
    value: ResearchStrategyCostAdjustedProbabilityBandInput,
    total_cost_drag_probability: Decimal,
    band_half_width_probability: Decimal,
    market_distance_from_band: Decimal,
    config: ResearchStrategyCostAdjustedProbabilityBandConfig,
) -> str:
    if (
        value.model_confidence_score < config.model_confidence_watch_floor
        or total_cost_drag_probability > config.total_cost_drag_watch_ceiling
        or value.liquidity_quality_score < config.liquidity_quality_watch_floor
        or value.resolution_ambiguity_score > config.resolution_ambiguity_watch_ceiling
        or band_half_width_probability > config.band_half_width_watch_ceiling
        or market_distance_from_band > config.market_distance_watch_ceiling
    ):
        return "block"
    if (
        value.model_confidence_score < config.model_confidence_pass_floor
        or total_cost_drag_probability > config.total_cost_drag_pass_ceiling
        or value.liquidity_quality_score < config.liquidity_quality_pass_floor
        or value.resolution_ambiguity_score > config.resolution_ambiguity_pass_ceiling
        or band_half_width_probability > config.band_half_width_pass_ceiling
        or market_distance_from_band > config.market_distance_pass_ceiling
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    value: ResearchStrategyCostAdjustedProbabilityBandInput,
    total_cost_drag_probability: Decimal,
    band_half_width_probability: Decimal,
    market_distance_from_band: Decimal,
    config: ResearchStrategyCostAdjustedProbabilityBandConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if value.model_confidence_score < config.model_confidence_watch_floor:
        codes.append("model_confidence_block")
    elif value.model_confidence_score < config.model_confidence_pass_floor:
        codes.append("model_confidence_watch")
    if total_cost_drag_probability > config.total_cost_drag_watch_ceiling:
        codes.append("cost_drag_block")
    elif total_cost_drag_probability > config.total_cost_drag_pass_ceiling:
        codes.append("cost_drag_watch")
    if value.liquidity_quality_score < config.liquidity_quality_watch_floor:
        codes.append("liquidity_quality_block")
    elif value.liquidity_quality_score < config.liquidity_quality_pass_floor:
        codes.append("liquidity_quality_watch")
    if value.resolution_ambiguity_score > config.resolution_ambiguity_watch_ceiling:
        codes.append("resolution_ambiguity_block")
    elif value.resolution_ambiguity_score > config.resolution_ambiguity_pass_ceiling:
        codes.append("resolution_ambiguity_watch")
    if band_half_width_probability > config.band_half_width_watch_ceiling:
        codes.append("band_width_block")
    elif band_half_width_probability > config.band_half_width_pass_ceiling:
        codes.append("band_width_watch")
    if market_distance_from_band > config.market_distance_watch_ceiling:
        codes.append("market_probability_distance_block")
    elif market_distance_from_band > config.market_distance_pass_ceiling:
        codes.append("market_probability_distance_watch")
    if not codes:
        codes.append("cost_adjusted_probability_band_pass")
    return _normalize_reason_codes("reason_codes", tuple(codes), ROW_REASON_CODES)


def _report_status(
    rows: tuple[ResearchStrategyCostAdjustedProbabilityBandRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyCostAdjustedProbabilityBandRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("cost_adjusted_probability_band_report_empty",)
    report_status = _report_status(rows)
    codes = [f"cost_adjusted_probability_band_report_{report_status}"]
    row_codes = tuple(code for row in rows for code in row.reason_codes)
    if any(code.startswith("model_confidence_") for code in row_codes):
        codes.append("model_confidence_review")
    if any(code.startswith("cost_drag_") for code in row_codes):
        codes.append("cost_drag_review")
    if any(code.startswith("liquidity_quality_") for code in row_codes):
        codes.append("liquidity_quality_review")
    if any(code.startswith("resolution_ambiguity_") for code in row_codes):
        codes.append("resolution_ambiguity_review")
    if any(code.startswith("band_width_") for code in row_codes):
        codes.append("band_width_review")
    if any(code.startswith("market_probability_distance_") for code in row_codes):
        codes.append("market_probability_distance_review")
    return _normalize_reason_codes("reason_codes", tuple(codes), REPORT_REASON_CODES)


def _row_sort_key(
    row: ResearchStrategyCostAdjustedProbabilityBandRow,
) -> tuple[int, Decimal, Decimal, Decimal, Decimal, Decimal, str]:
    return (
        {"block": 0, "watch": 1, "pass": 2}[row.status],
        -row.market_distance_from_band,
        -row.band_half_width_probability,
        -row.total_cost_drag_probability,
        row.model_confidence_score,
        row.liquidity_quality_score,
        row.candidate_ref,
    )


def _normalize_inputs(
    inputs: Iterable[ResearchStrategyCostAdjustedProbabilityBandInput],
) -> tuple[ResearchStrategyCostAdjustedProbabilityBandInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen_refs: set[str] = set()
    for value in normalized:
        if type(value) is not ResearchStrategyCostAdjustedProbabilityBandInput:
            raise ValueError(
                "inputs must contain ResearchStrategyCostAdjustedProbabilityBandInput values",
            )
        _require_hard_flags("input", value)
        if value.candidate_ref in seen_refs:
            raise ValueError("inputs must not contain duplicate candidate_ref values")
        seen_refs.add(value.candidate_ref)
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchStrategyCostAdjustedProbabilityBandRow],
) -> tuple[ResearchStrategyCostAdjustedProbabilityBandRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_refs: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchStrategyCostAdjustedProbabilityBandRow:
            raise ValueError(
                "rows must contain ResearchStrategyCostAdjustedProbabilityBandRow values",
            )
        _require_hard_flags("row", row)
        _verify_digest(row)
        if row.candidate_ref in seen_refs:
            raise ValueError("rows must not contain duplicate candidate_ref values")
        seen_refs.add(row.candidate_ref)
    return normalized


def _validate_row_consistency(
    row: ResearchStrategyCostAdjustedProbabilityBandRow,
) -> None:
    expected_cost = _sum_decimals(
        (
            row.fee_probability_drag,
            row.spread_probability_drag,
            row.slippage_probability_drag,
        ),
    )
    if row.total_cost_drag_probability != expected_cost:
        raise ValueError("total_cost_drag_probability does not match drag inputs")
    expected_midpoint = _clamp_probability(
        _subtract_decimal(row.model_probability, row.total_cost_drag_probability),
    )
    if row.cost_adjusted_midpoint_probability != expected_midpoint:
        raise ValueError("cost_adjusted_midpoint_probability does not match row inputs")
    expected_lower = _clamp_probability(
        _subtract_decimal(row.cost_adjusted_midpoint_probability, row.band_half_width_probability),
    )
    if row.cost_adjusted_lower_probability != expected_lower:
        raise ValueError("cost_adjusted_lower_probability does not match row inputs")
    expected_upper = _clamp_probability(
        _sum_decimals((row.cost_adjusted_midpoint_probability, row.band_half_width_probability)),
    )
    if row.cost_adjusted_upper_probability != expected_upper:
        raise ValueError("cost_adjusted_upper_probability does not match row inputs")
    expected_distance = _market_distance_from_band(
        market_probability=row.market_probability,
        lower_probability=row.cost_adjusted_lower_probability,
        upper_probability=row.cost_adjusted_upper_probability,
    )
    if row.market_distance_from_band != expected_distance:
        raise ValueError("market_distance_from_band does not match row inputs")
    expected_position = _market_band_position(
        market_probability=row.market_probability,
        lower_probability=row.cost_adjusted_lower_probability,
        upper_probability=row.cost_adjusted_upper_probability,
    )
    if row.market_band_position != expected_position:
        raise ValueError("market_band_position does not match row inputs")
    if row.status == "pass" and row.reason_codes != (
        "cost_adjusted_probability_band_pass",
    ):
        raise ValueError("pass rows must only contain pass reason code")
    if row.status == "watch" and not any(code.endswith("_watch") for code in row.reason_codes):
        raise ValueError("watch rows must contain watch reason code")
    if row.status == "block" and not any(code.endswith("_block") for code in row.reason_codes):
        raise ValueError("block rows must contain block reason code")


def _validate_report_consistency(
    report: ResearchStrategyCostAdjustedProbabilityBandReport,
) -> None:
    if report.input_count != _count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.input_count != report.pass_count + report.watch_count + report.block_count:
        raise ValueError("status counts must match input_count")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.mean_model_confidence_score != _mean(
        tuple(row.model_confidence_score for row in report.rows),
    ):
        raise ValueError("mean_model_confidence_score must match rows")
    if report.mean_total_cost_drag_probability != _mean(
        tuple(row.total_cost_drag_probability for row in report.rows),
    ):
        raise ValueError("mean_total_cost_drag_probability must match rows")
    if report.mean_band_half_width_probability != _mean(
        tuple(row.band_half_width_probability for row in report.rows),
    ):
        raise ValueError("mean_band_half_width_probability must match rows")
    if report.mean_market_distance_from_band != _mean(
        tuple(row.market_distance_from_band for row in report.rows),
    ):
        raise ValueError("mean_market_distance_from_band must match rows")
    if report.mean_liquidity_quality_score != _mean(
        tuple(row.liquidity_quality_score for row in report.rows),
    ):
        raise ValueError("mean_liquidity_quality_score must match rows")
    if report.mean_resolution_ambiguity_score != _mean(
        tuple(row.resolution_ambiguity_score for row in report.rows),
    ):
        raise ValueError("mean_resolution_ambiguity_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts_from_rows(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if tuple(sorted(report.rows, key=_row_sort_key)) != report.rows:
        raise ValueError("rows must use deterministic sequence")


def _verify_report_integrity(report: ResearchStrategyCostAdjustedProbabilityBandReport) -> None:
    _verify_digest(report)
    _validate_report_consistency(report)
    for row in report.rows:
        _verify_digest(row)


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
    provided = payload.get("derived_validation_digest")
    _require_digest(f"{label}.derived_validation_digest", provided)
    expected = _public_payload_digest(payload)
    if provided != expected:
        raise ValueError("derived_validation_digest does not match public payload")


def _public_payload_digest(payload: dict[str, Any]) -> str:
    digest_input = dict(payload)
    digest_input.pop("derived_validation_digest", None)
    encoded = dumps(
        _json_ready(digest_input),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _status_count(
    rows: tuple[ResearchStrategyCostAdjustedProbabilityBandRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_code_counts_from_rows(
    rows: tuple[ResearchStrategyCostAdjustedProbabilityBandRow, ...],
) -> tuple[ResearchStrategyCostAdjustedProbabilityBandReasonCodeCount, ...]:
    if not rows:
        return ()
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    denominator = _count(len(rows))
    return tuple(
        ResearchStrategyCostAdjustedProbabilityBandReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
            input_ratio=_divide_decimal(_count(count), denominator),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _normalize_reason_code_counts(
    value: Iterable[ResearchStrategyCostAdjustedProbabilityBandReasonCodeCount],
) -> tuple[ResearchStrategyCostAdjustedProbabilityBandReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for row in rows:
        if type(row) is not ResearchStrategyCostAdjustedProbabilityBandReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain ResearchStrategyCostAdjustedProbabilityBandReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", row)
    return rows


def _market_distance_from_band(
    *,
    market_probability: Decimal,
    lower_probability: Decimal,
    upper_probability: Decimal,
) -> Decimal:
    if market_probability < lower_probability:
        return _subtract_decimal(lower_probability, market_probability)
    if market_probability > upper_probability:
        return _subtract_decimal(market_probability, upper_probability)
    return ZERO.quantize(RATIO_QUANTUM)


def _market_band_position(
    *,
    market_probability: Decimal,
    lower_probability: Decimal,
    upper_probability: Decimal,
) -> str:
    if market_probability < lower_probability:
        return "below_band"
    if market_probability > upper_probability:
        return "above_band"
    return "inside_band"


def _sum_decimals(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO))


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left - right)


def _multiply_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left * right)


def _divide_decimal(left: Decimal, right: Decimal) -> Decimal:
    if right == ZERO:
        return ZERO.quantize(RATIO_QUANTUM)
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left / right)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO.quantize(RATIO_QUANTUM)
    return _divide_decimal(_sum_decimals(values), _count(len(values)))


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(RATIO_QUANTUM)


def _clamp_probability(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO.quantize(RATIO_QUANTUM)
    if value > ONE:
        return ONE.quantize(RATIO_QUANTUM)
    return _quantize(value)


def _normalize_probability(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return normalized


def _normalize_nonnegative_count(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _normalize_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_floor_pair(name: str, pass_floor: Decimal, watch_floor: Decimal) -> None:
    if pass_floor < watch_floor:
        raise ValueError(f"{name}_pass_floor must be at least {name}_watch_floor")


def _require_ceiling_pair(
    name: str,
    pass_ceiling: Decimal,
    watch_ceiling: Decimal,
) -> None:
    if watch_ceiling < pass_ceiling:
        raise ValueError(f"{name}_watch_ceiling must be at least {name}_pass_ceiling")


def _require_status(name: str, value: object) -> None:
    if (
        type(value) is not str
        or value not in RESEARCH_STRATEGY_COST_ADJUSTED_PROBABILITY_BAND_STATUSES
    ):
        raise ValueError(f"{name} must be pass, watch, or block")


def _require_market_band_position(name: str, value: object) -> None:
    if type(value) is not str or value not in _MARKET_BAND_POSITIONS:
        raise ValueError(f"{name} must be below_band, inside_band, or above_band")


def _require_reason_code(name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{name} must be a non-empty string")
    _require_canonical_public_string(name, value)
    if value not in ROW_REASON_CODES and value not in REPORT_REASON_CODES:
        raise ValueError(f"{name} is not supported")


def _normalize_reason_codes(
    name: str,
    value: tuple[str, ...],
    supported: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    for reason_code in value:
        _require_reason_code(name, reason_code)
        if reason_code not in supported:
            raise ValueError(f"{name} contains an unsupported reason code")
    if len(set(value)) != len(value):
        raise ValueError(f"{name} must not contain duplicates")
    return value


def _require_canonical_public_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{name} must be a canonical public string")


def _require_hard_flags(name: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{name} {field_name} must be True")


def _apply_or_verify_digest(value: object) -> None:
    provided = getattr(value, "derived_validation_digest")
    if provided:
        _verify_digest(value)
    else:
        object.__setattr__(value, "derived_validation_digest", _digest_for(value))


def _verify_digest(value: object) -> None:
    provided = getattr(value, "derived_validation_digest")
    _require_digest("derived_validation_digest", provided)
    if provided != _digest_for(value):
        raise ValueError("derived_validation_digest does not match payload")


def _require_digest(name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be a sha256 hex digest")


def _digest_for(value: object) -> str:
    payload = asdict(value)
    payload.pop("derived_validation_digest", None)
    encoded = dumps(
        _json_ready(payload),
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
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return str(value.quantize(RATIO_QUANTUM))
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is str:
        return value
    if type(value) is bool:
        return value
    if type(value) in (int, float):
        raise ValueError("numeric payload values must be Decimal-derived strings")
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


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if any(fragment in key.lower() for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
                raise ValueError(f"unsafe public field in {label}")
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str and any(
        fragment in value.lower() for fragment in _UNSAFE_PUBLIC_FRAGMENTS
    ):
        raise ValueError(f"unsafe public value in {label}")


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


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_COST_ADJUSTED_PROBABILITY_BAND_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_COST_ADJUSTED_PROBABILITY_BAND_STATUSES",
    "ResearchStrategyCostAdjustedProbabilityBandConfig",
    "ResearchStrategyCostAdjustedProbabilityBandInput",
    "ResearchStrategyCostAdjustedProbabilityBandReasonCodeCount",
    "ResearchStrategyCostAdjustedProbabilityBandRow",
    "ResearchStrategyCostAdjustedProbabilityBandReport",
    "build_research_strategy_cost_adjusted_probability_band_report",
    "research_strategy_cost_adjusted_probability_band_report_payload",
)
