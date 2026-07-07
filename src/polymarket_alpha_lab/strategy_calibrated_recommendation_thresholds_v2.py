"""Phase 1 paper-only calibrated recommendation threshold report.

This module transforms caller-supplied in-memory candidates into a
deterministic read-only report. It performs no external IO and exposes no
execution surface.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
from hashlib import sha256
from json import dumps
from typing import Any, Iterable


DEFAULT_STRATEGY_CALIBRATED_RECOMMENDATION_THRESHOLDS_V2_CONFIG_VERSION = (
    "strategy-calibrated-recommendation-thresholds-v2"
)
DECIMAL_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
RECOMMENDATION_SIDES = ("no", "yes")
RECOMMENDATION_STATUSES = ("promote", "watch", "block")
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
UNSAFE_PUBLIC_FRAGMENTS = (
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
    "trade",
)


@dataclass(frozen=True)
class StrategyCalibratedRecommendationThresholdsV2Config:
    config_version: str
    base_block_edge_probability: Decimal
    base_watch_edge_probability: Decimal
    base_promote_edge_probability: Decimal
    historical_calibration_gap_weight: Decimal
    source_quality_gap_weight: Decimal
    liquidity_exit_gap_weight: Decimal
    resolution_risk_weight: Decimal
    specialist_quorum_gap_weight: Decimal
    min_historical_calibration_score: Decimal
    min_source_quality_score: Decimal
    max_cost_break_even_probability: Decimal
    min_liquidity_exit_feasibility_score: Decimal
    max_resolution_risk_score: Decimal
    min_specialist_quorum_score: Decimal
    max_observation_age_seconds: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_public_string("config_version", self.config_version)
        for field_name in (
            "base_block_edge_probability",
            "base_watch_edge_probability",
            "base_promote_edge_probability",
            "historical_calibration_gap_weight",
            "source_quality_gap_weight",
            "liquidity_exit_gap_weight",
            "resolution_risk_weight",
            "specialist_quorum_gap_weight",
            "min_historical_calibration_score",
            "min_source_quality_score",
            "max_cost_break_even_probability",
            "min_liquidity_exit_feasibility_score",
            "max_resolution_risk_score",
            "min_specialist_quorum_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_observation_age_seconds",
            _normalize_nonnegative_decimal(
                "max_observation_age_seconds",
                self.max_observation_age_seconds,
            ),
        )
        if self.base_block_edge_probability > self.base_watch_edge_probability:
            raise ValueError("base_block_edge_probability must not exceed watch")
        if self.base_watch_edge_probability > self.base_promote_edge_probability:
            raise ValueError("base_watch_edge_probability must not exceed promote")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class StrategyCalibratedRecommendationThresholdsV2Input:
    candidate_id: str
    market_id: str
    recommendation_side: str
    observed_at: datetime
    calibrated_edge_probability: Decimal
    historical_calibration_score: Decimal
    source_quality_score: Decimal
    cost_break_even_probability: Decimal
    liquidity_exit_feasibility_score: Decimal
    resolution_risk_score: Decimal
    specialist_quorum_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("candidate_id", "market_id"):
            _require_canonical_public_string(field_name, getattr(self, field_name))
        _require_member("recommendation_side", self.recommendation_side, RECOMMENDATION_SIDES)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "calibrated_edge_probability",
            "historical_calibration_score",
            "source_quality_score",
            "cost_break_even_probability",
            "liquidity_exit_feasibility_score",
            "resolution_risk_score",
            "specialist_quorum_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class StrategyCalibratedRecommendationThresholdsV2Row:
    candidate_id: str
    market_id: str
    recommendation_side: str
    observed_at: datetime
    calibrated_edge_probability: Decimal
    historical_calibration_score: Decimal
    source_quality_score: Decimal
    cost_break_even_probability: Decimal
    liquidity_exit_feasibility_score: Decimal
    resolution_risk_score: Decimal
    specialist_quorum_score: Decimal
    historical_calibration_gap_probability: Decimal
    source_quality_gap_probability: Decimal
    liquidity_exit_gap_probability: Decimal
    resolution_risk_adjustment_probability: Decimal
    specialist_quorum_gap_probability: Decimal
    threshold_adjustment_probability: Decimal
    derived_block_threshold_probability: Decimal
    derived_watch_threshold_probability: Decimal
    derived_promote_threshold_probability: Decimal
    margin_to_promote_threshold_probability: Decimal
    age_seconds: Decimal
    recommendation_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("candidate_id", "market_id"):
            _require_canonical_public_string(field_name, getattr(self, field_name))
        _require_member("recommendation_side", self.recommendation_side, RECOMMENDATION_SIDES)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "calibrated_edge_probability",
            "historical_calibration_score",
            "source_quality_score",
            "cost_break_even_probability",
            "liquidity_exit_feasibility_score",
            "resolution_risk_score",
            "specialist_quorum_score",
            "historical_calibration_gap_probability",
            "source_quality_gap_probability",
            "liquidity_exit_gap_probability",
            "resolution_risk_adjustment_probability",
            "specialist_quorum_gap_probability",
            "threshold_adjustment_probability",
            "derived_block_threshold_probability",
            "derived_watch_threshold_probability",
            "derived_promote_threshold_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "margin_to_promote_threshold_probability",
            _normalize_decimal(
                "margin_to_promote_threshold_probability",
                self.margin_to_promote_threshold_probability,
            ),
        )
        object.__setattr__(
            self,
            "age_seconds",
            _normalize_nonnegative_decimal("age_seconds", self.age_seconds),
        )
        _require_member(
            "recommendation_status",
            self.recommendation_status,
            RECOMMENDATION_STATUSES,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("row", self)
        _apply_or_verify_digest(self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class StrategyCalibratedRecommendationThresholdsV2Report:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    row_count: Decimal
    promote_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyCalibratedRecommendationThresholdsV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_public_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "row_count",
            "promote_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, RECOMMENDATION_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _apply_or_verify_digest(self)
        _validate_report_consistency(self)


def build_strategy_calibrated_recommendation_thresholds_v2_report(
    inputs: Iterable[StrategyCalibratedRecommendationThresholdsV2Input],
    *,
    config: StrategyCalibratedRecommendationThresholdsV2Config,
    generated_at: datetime,
) -> StrategyCalibratedRecommendationThresholdsV2Report:
    if type(config) is not StrategyCalibratedRecommendationThresholdsV2Config:
        raise ValueError(
            "config must be a StrategyCalibratedRecommendationThresholdsV2Config",
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
    return StrategyCalibratedRecommendationThresholdsV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        candidate_count=_count_decimal(len(normalized_inputs)),
        row_count=_count_decimal(len(rows)),
        promote_count=_status_count(rows, "promote"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def strategy_calibrated_recommendation_thresholds_v2_payload(
    report: StrategyCalibratedRecommendationThresholdsV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyCalibratedRecommendationThresholdsV2Report:
        _require_hard_flags("report", report)
        _verify_report_integrity(report)
        payload = _json_ready(asdict(report))
    elif type(report) is dict:
        _require_hard_flags("payload", _DictFlags(report))
        _reject_unsafe_public_payload("payload", report, public_payload=True)
        _verify_public_payload_integrity(report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a StrategyCalibratedRecommendationThresholdsV2Report",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload, public_payload=True)
    return payload


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


def _row_from_input(
    value: StrategyCalibratedRecommendationThresholdsV2Input,
    *,
    config: StrategyCalibratedRecommendationThresholdsV2Config,
    generated_at: datetime,
) -> StrategyCalibratedRecommendationThresholdsV2Row:
    observed_at = _as_utc("observed_at", value.observed_at)
    if observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    historical_gap = _floor_gap_adjustment(
        config.min_historical_calibration_score,
        value.historical_calibration_score,
        config.historical_calibration_gap_weight,
    )
    source_gap = _floor_gap_adjustment(
        config.min_source_quality_score,
        value.source_quality_score,
        config.source_quality_gap_weight,
    )
    liquidity_gap = _floor_gap_adjustment(
        config.min_liquidity_exit_feasibility_score,
        value.liquidity_exit_feasibility_score,
        config.liquidity_exit_gap_weight,
    )
    resolution_risk_adjustment = _multiply_decimal(
        value.resolution_risk_score,
        config.resolution_risk_weight,
    )
    quorum_gap = _floor_gap_adjustment(
        config.min_specialist_quorum_score,
        value.specialist_quorum_score,
        config.specialist_quorum_gap_weight,
    )
    threshold_adjustment = _sum_decimals(
        (
            value.cost_break_even_probability,
            historical_gap,
            source_gap,
            liquidity_gap,
            resolution_risk_adjustment,
            quorum_gap,
        ),
    )
    block_threshold = _add_decimal(config.base_block_edge_probability, threshold_adjustment)
    watch_threshold = _add_decimal(config.base_watch_edge_probability, threshold_adjustment)
    promote_threshold = _add_decimal(config.base_promote_edge_probability, threshold_adjustment)
    age_seconds = _seconds_between(generated_at, observed_at)
    status = _recommendation_status(
        value,
        derived_block_threshold_probability=block_threshold,
        derived_promote_threshold_probability=promote_threshold,
        age_seconds=age_seconds,
        config=config,
    )
    return StrategyCalibratedRecommendationThresholdsV2Row(
        candidate_id=value.candidate_id,
        market_id=value.market_id,
        recommendation_side=value.recommendation_side,
        observed_at=observed_at,
        calibrated_edge_probability=value.calibrated_edge_probability,
        historical_calibration_score=value.historical_calibration_score,
        source_quality_score=value.source_quality_score,
        cost_break_even_probability=value.cost_break_even_probability,
        liquidity_exit_feasibility_score=value.liquidity_exit_feasibility_score,
        resolution_risk_score=value.resolution_risk_score,
        specialist_quorum_score=value.specialist_quorum_score,
        historical_calibration_gap_probability=historical_gap,
        source_quality_gap_probability=source_gap,
        liquidity_exit_gap_probability=liquidity_gap,
        resolution_risk_adjustment_probability=resolution_risk_adjustment,
        specialist_quorum_gap_probability=quorum_gap,
        threshold_adjustment_probability=threshold_adjustment,
        derived_block_threshold_probability=block_threshold,
        derived_watch_threshold_probability=watch_threshold,
        derived_promote_threshold_probability=promote_threshold,
        margin_to_promote_threshold_probability=_subtract_decimal(
            value.calibrated_edge_probability,
            promote_threshold,
        ),
        age_seconds=age_seconds,
        recommendation_status=status,
        reason_codes=_row_reason_codes(
            value,
            derived_block_threshold_probability=block_threshold,
            derived_promote_threshold_probability=promote_threshold,
            age_seconds=age_seconds,
            status=status,
            config=config,
        ),
    )


def _recommendation_status(
    value: StrategyCalibratedRecommendationThresholdsV2Input,
    *,
    derived_block_threshold_probability: Decimal,
    derived_promote_threshold_probability: Decimal,
    age_seconds: Decimal,
    config: StrategyCalibratedRecommendationThresholdsV2Config,
) -> str:
    if (
        value.cost_break_even_probability > config.max_cost_break_even_probability
        or value.resolution_risk_score > config.max_resolution_risk_score
        or value.specialist_quorum_score < config.min_specialist_quorum_score
        or value.calibrated_edge_probability < derived_block_threshold_probability
    ):
        return "block"
    if (
        age_seconds > config.max_observation_age_seconds
        or value.historical_calibration_score < config.min_historical_calibration_score
        or value.source_quality_score < config.min_source_quality_score
        or value.liquidity_exit_feasibility_score < config.min_liquidity_exit_feasibility_score
        or value.calibrated_edge_probability < derived_promote_threshold_probability
    ):
        return "watch"
    return "promote"


def _row_reason_codes(
    value: StrategyCalibratedRecommendationThresholdsV2Input,
    *,
    derived_block_threshold_probability: Decimal,
    derived_promote_threshold_probability: Decimal,
    age_seconds: Decimal,
    status: str,
    config: StrategyCalibratedRecommendationThresholdsV2Config,
) -> tuple[str, ...]:
    codes = list(value.reason_codes)
    codes.extend(
        (
            "cost_break_even_applied",
            "historical_calibration_applied",
            "liquidity_exit_feasibility_applied",
            "resolution_risk_applied",
            "source_quality_applied",
            "specialist_quorum_applied",
        ),
    )
    if status == "promote":
        codes.append("promote_threshold_met")
    elif status == "watch":
        codes.append("watch_threshold_met")
    else:
        codes.append("block_threshold_met")
    if value.calibrated_edge_probability < derived_promote_threshold_probability:
        codes.append("promote_threshold_gap")
    if value.calibrated_edge_probability < derived_block_threshold_probability:
        codes.append("block_threshold_gap")
    if value.historical_calibration_score < config.min_historical_calibration_score:
        codes.append("historical_calibration_gap")
    if value.source_quality_score < config.min_source_quality_score:
        codes.append("source_quality_gap")
    if value.cost_break_even_probability > config.max_cost_break_even_probability:
        codes.append("cost_break_even_block")
    if value.liquidity_exit_feasibility_score < config.min_liquidity_exit_feasibility_score:
        codes.append("liquidity_exit_gap")
    if value.resolution_risk_score > config.max_resolution_risk_score:
        codes.append("resolution_risk_block")
    if value.specialist_quorum_score < config.min_specialist_quorum_score:
        codes.append("specialist_quorum_gap")
    if age_seconds > config.max_observation_age_seconds:
        codes.append("stale_observation")
    return _normalize_reason_codes("reason_codes", tuple(sorted(set(codes))))


def _report_status(rows: tuple[StrategyCalibratedRecommendationThresholdsV2Row, ...]) -> str:
    if _status_count(rows, "block") > ZERO:
        return "block"
    if _status_count(rows, "watch") > ZERO:
        return "watch"
    if _status_count(rows, "promote") > ZERO:
        return "promote"
    return "watch"


def _report_reason_codes(
    rows: tuple[StrategyCalibratedRecommendationThresholdsV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_calibrated_recommendation_set",)
    codes: list[str] = []
    if _status_count(rows, "block") > ZERO:
        codes.append("calibrated_recommendation_block")
    if _status_count(rows, "watch") > ZERO:
        codes.append("calibrated_recommendation_watch")
    if _status_count(rows, "promote") > ZERO:
        codes.append("calibrated_recommendation_promote")
    for row in rows:
        codes.extend(row.reason_codes)
    return _normalize_reason_codes("reason_codes", tuple(sorted(set(codes))))


def _row_sort_key(
    row: StrategyCalibratedRecommendationThresholdsV2Row,
) -> tuple[int, Decimal, str, str]:
    return (
        {"block": 0, "watch": 1, "promote": 2}[row.recommendation_status],
        row.calibrated_edge_probability,
        row.market_id,
        row.candidate_id,
    )


def _normalize_inputs(
    inputs: Iterable[StrategyCalibratedRecommendationThresholdsV2Input],
) -> tuple[StrategyCalibratedRecommendationThresholdsV2Input, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen_ids: set[str] = set()
    for value in normalized:
        if type(value) is not StrategyCalibratedRecommendationThresholdsV2Input:
            raise ValueError(
                "inputs must contain only StrategyCalibratedRecommendationThresholdsV2Input values",
            )
        _require_hard_flags("input", value)
        if value.candidate_id in seen_ids:
            raise ValueError("inputs must not contain duplicate candidate_id values")
        seen_ids.add(value.candidate_id)
    return normalized


def _normalize_rows(
    rows: Iterable[StrategyCalibratedRecommendationThresholdsV2Row],
) -> tuple[StrategyCalibratedRecommendationThresholdsV2Row, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    candidate_ids = tuple(row.candidate_id for row in normalized)
    if len(set(candidate_ids)) != len(candidate_ids):
        raise ValueError("rows must not contain duplicate candidate_id values")
    for row in normalized:
        if type(row) is not StrategyCalibratedRecommendationThresholdsV2Row:
            raise ValueError(
                "rows must contain StrategyCalibratedRecommendationThresholdsV2Row values",
            )
        _require_hard_flags("row", row)
        _verify_digest(row)
    return normalized


def _validate_row_consistency(row: StrategyCalibratedRecommendationThresholdsV2Row) -> None:
    expected_adjustment = _sum_decimals(
        (
            row.cost_break_even_probability,
            row.historical_calibration_gap_probability,
            row.source_quality_gap_probability,
            row.liquidity_exit_gap_probability,
            row.resolution_risk_adjustment_probability,
            row.specialist_quorum_gap_probability,
        ),
    )
    if row.threshold_adjustment_probability != expected_adjustment:
        raise ValueError("threshold_adjustment_probability does not match risk inputs")
    if row.derived_block_threshold_probability > row.derived_watch_threshold_probability:
        raise ValueError("derived block threshold must not exceed watch threshold")
    if row.derived_watch_threshold_probability > row.derived_promote_threshold_probability:
        raise ValueError("derived watch threshold must not exceed promote threshold")
    expected_margin = _subtract_decimal(
        row.calibrated_edge_probability,
        row.derived_promote_threshold_probability,
    )
    if row.margin_to_promote_threshold_probability != expected_margin:
        raise ValueError("margin_to_promote_threshold_probability does not match thresholds")


def _validate_report_consistency(
    report: StrategyCalibratedRecommendationThresholdsV2Report,
) -> None:
    row_count = _count_decimal(len(report.rows))
    if report.row_count != row_count:
        raise ValueError("row_count must match rows")
    if report.candidate_count != report.row_count:
        raise ValueError("candidate_count must match row_count")
    if report.row_count != report.promote_count + report.watch_count + report.block_count:
        raise ValueError("status counts must match row_count")
    if report.promote_count != _status_count(report.rows, "promote"):
        raise ValueError("promote_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if tuple(sorted(report.rows, key=_row_sort_key)) != report.rows:
        raise ValueError("rows must use deterministic ordering")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _verify_report_integrity(report: StrategyCalibratedRecommendationThresholdsV2Report) -> None:
    _validate_report_consistency(report)
    _verify_digest(report)
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
    digest_input = dict(payload)
    digest_input.pop("derived_validation_digest", None)
    encoded = dumps(
        _json_ready(digest_input),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    expected = sha256(encoded).hexdigest()
    if provided != expected:
        raise ValueError("derived_validation_digest does not match public payload")


def _status_count(
    rows: tuple[StrategyCalibratedRecommendationThresholdsV2Row, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.recommendation_status == status))


def _count_decimal(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return _quantize(Decimal(value))


def _floor_gap_adjustment(
    minimum_score: Decimal,
    observed_score: Decimal,
    weight: Decimal,
) -> Decimal:
    gap = _subtract_decimal(minimum_score, observed_score)
    if gap < ZERO:
        return _quantize(ZERO)
    return _multiply_decimal(gap, weight)


def _sum_decimals(values: tuple[Decimal, ...]) -> Decimal:
    return _quantize(sum(values, ZERO))


def _add_decimal(left: Decimal, right: Decimal) -> Decimal:
    return _quantize(left + right)


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    return _quantize(left - right)


def _multiply_decimal(left: Decimal, right: Decimal) -> Decimal:
    return _quantize(left * right)


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    total_seconds = _as_utc("later", later) - _as_utc("earlier", earlier)
    return _quantize(Decimal(str(total_seconds.total_seconds())))


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")


def _require_canonical_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public content")


def _require_member(field_name: str, value: object, members: tuple[str, ...]) -> None:
    if type(value) is not str or value not in members:
        raise ValueError(f"{field_name} must be a known value")


def _require_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    _require_decimal(field_name, value)
    return _quantize(value)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-number Decimal")
    return normalized


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must not exceed 1")
    return normalized


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    if isinstance(value, (set, frozenset)):
        raise ValueError(f"{field_name} must use deterministic ordered values")
    try:
        reason_codes = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        _require_reason_code(field_name, reason_code)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must not contain duplicates")
    if reason_codes != tuple(sorted(reason_codes)):
        raise ValueError(f"{field_name} must use deterministic ordered values")
    return reason_codes


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_public_string(field_name, value)
    if value.startswith("_") or value.endswith("_") or "__" in value:
        raise ValueError(f"{field_name} must be a canonical reason code")
    for character in value:
        if not (character.islower() or character.isdigit() or character == "_"):
            raise ValueError(f"{field_name} must be a canonical reason code")


def _apply_or_verify_digest(
    value: (
        StrategyCalibratedRecommendationThresholdsV2Row
        | StrategyCalibratedRecommendationThresholdsV2Report
    ),
) -> None:
    expected = _derived_digest(value)
    provided = value.derived_validation_digest
    if provided == "":
        object.__setattr__(value, "derived_validation_digest", expected)
        return
    _require_digest("derived_validation_digest", provided)
    if provided != expected:
        raise ValueError("derived_validation_digest does not match derived fields")


def _verify_digest(
    value: (
        StrategyCalibratedRecommendationThresholdsV2Row
        | StrategyCalibratedRecommendationThresholdsV2Report
    ),
) -> None:
    _require_digest("derived_validation_digest", value.derived_validation_digest)
    if value.derived_validation_digest != _derived_digest(value):
        raise ValueError("derived_validation_digest does not match derived fields")


def _derived_digest(
    value: (
        StrategyCalibratedRecommendationThresholdsV2Row
        | StrategyCalibratedRecommendationThresholdsV2Report
    ),
) -> str:
    digest_input = asdict(value)
    digest_input.pop("derived_validation_digest", None)
    encoded = dumps(
        _json_ready(digest_input),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    for character in value:
        if character not in "0123456789abcdef":
            raise ValueError(f"{field_name} must be a sha256 hex digest")


def _has_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower().replace("-", "_").replace(" ", "_")
    compact = "".join(character for character in lowered if character.isalnum())
    return any(
        fragment in lowered or fragment in compact
        for fragment in UNSAFE_PUBLIC_FRAGMENTS
    )


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    public_payload: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            item_path = field.name if not path else f"{path}.{field.name}"
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                item_path,
                public_payload=public_payload,
            )
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            _require_canonical_public_string("public_payload_key", key)
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True for {label}")
            _reject_unsafe_public_payload(
                label,
                item,
                item_path,
                public_payload=public_payload,
            )
        return
    if type(value) is list:
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(
                label,
                item,
                item_path,
                public_payload=public_payload,
            )
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(
                label,
                item,
                item_path,
                public_payload=public_payload,
            )
        return
    if type(value) is str:
        _require_canonical_public_string(current_path, value)
        return
    if isinstance(value, Decimal):
        if public_payload:
            raise ValueError(f"{current_path} must be a Decimal string")
        if type(value) is not Decimal:
            raise ValueError(f"{current_path} must be a Decimal")
        if not value.is_finite():
            raise ValueError(f"{current_path} must be finite")
        return
    if isinstance(value, datetime):
        if public_payload:
            raise ValueError(f"{current_path} must be an ISO datetime string")
        _as_utc(current_path, value)
        return
    if value is None or type(value) in (bool, int):
        return
    if isinstance(value, float):
        raise ValueError(f"{current_path} must not be a float")
    raise ValueError(f"{current_path} is not JSON serializable")


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return format(_quantize(value), "f")
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if value is None or type(value) in (str, int, bool):
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    raise ValueError("value is not JSON-ready")


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(DECIMAL_QUANTUM, rounding=ROUND_HALF_EVEN)


__all__ = (
    "DEFAULT_STRATEGY_CALIBRATED_RECOMMENDATION_THRESHOLDS_V2_CONFIG_VERSION",
    "DECIMAL_QUANTUM",
    "RECOMMENDATION_STATUSES",
    "StrategyCalibratedRecommendationThresholdsV2Config",
    "StrategyCalibratedRecommendationThresholdsV2Input",
    "StrategyCalibratedRecommendationThresholdsV2Report",
    "StrategyCalibratedRecommendationThresholdsV2Row",
    "build_strategy_calibrated_recommendation_thresholds_v2_report",
    "strategy_calibrated_recommendation_thresholds_v2_payload",
)
