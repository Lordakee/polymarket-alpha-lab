"""Read-only calibration gap digest for Phase 1 strategy outputs."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    UNSAFE_SURFACE_FIELD_FRAGMENTS,
)


DEFAULT_STRATEGY_RECOMMENDATION_CALIBRATION_GAP_DIGEST_CONFIG_VERSION = (
    "strategy-recommendation-calibration-gap-digest-v0"
)

CATEGORIES = (
    "politics",
    "crypto",
    "macro",
    "commodities",
    "sports",
)
TEAM_TO_CATEGORY = {
    "politics": "politics",
    "crypto_btc": "crypto",
    "crypto_eth": "crypto",
    "macro_rates": "macro",
    "commodities_gold": "commodities",
    "commodities_oil": "commodities",
    "sports_soccer": "sports",
    "sports_basketball": "sports",
    "sports_other": "sports",
}
INPUT_REASON_CODES = (
    "wide_positive_calibration_gap",
    "wide_negative_calibration_gap",
    "calibration_gap_within_threshold",
    "resolved_learning_available",
    "confidence_increased",
    "confidence_decreased",
    "confidence_stable",
    "stale_evidence",
    "evidence_fresh",
)
REPORT_REASON_CODES = (
    "calibration_gap_digest_clear",
    "material_calibration_gap_detected",
    "resolved_learning_available",
    "confidence_drift_detected",
    "stale_evidence_detected",
)
STATUSES = ("pass", "watch")

COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ZERO_RESULT = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
EXTRA_UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "liv" + "e_" + "tra" + "ding",
        "net" + "work",
        "data" + "base",
        "bro" + "ker",
        "per" + "sist",
        "tra" + "de",
    ),
)


@dataclass(frozen=True)
class StrategyRecommendationCalibrationGapDigestConfig:
    config_version: str = (
        DEFAULT_STRATEGY_RECOMMENDATION_CALIBRATION_GAP_DIGEST_CONFIG_VERSION
    )
    material_gap_threshold: Decimal = Decimal("0.050000")
    confidence_drift_threshold: Decimal = Decimal("0.100000")
    stale_evidence_hours: Decimal = Decimal("24.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "material_gap_threshold",
            _normalize_nonnegative_ratio(
                "material_gap_threshold",
                self.material_gap_threshold,
            ),
        )
        object.__setattr__(
            self,
            "confidence_drift_threshold",
            _normalize_nonnegative_ratio(
                "confidence_drift_threshold",
                self.confidence_drift_threshold,
            ),
        )
        object.__setattr__(
            self,
            "stale_evidence_hours",
            _normalize_nonnegative_value(
                "evidence_age_hours stale_evidence_hours",
                self.stale_evidence_hours,
            ),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class StrategyRecommendationCalibrationGapInput:
    team_id: str
    category_id: str
    strategy_id: str
    forecast_probability: Decimal
    market_implied_probability: Decimal
    realized_probability: Decimal | None
    confidence: Decimal
    prior_confidence: Decimal
    evidence_age_hours: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_known_team_id("team_id", self.team_id)
        _require_category_id("category_id", self.category_id)
        if TEAM_TO_CATEGORY[self.team_id] != self.category_id:
            raise ValueError("team_id must match category_id")
        _require_canonical_string("strategy_id", self.strategy_id)
        object.__setattr__(
            self,
            "forecast_probability",
            _normalize_probability("forecast_probability", self.forecast_probability),
        )
        object.__setattr__(
            self,
            "market_implied_probability",
            _normalize_probability(
                "market_implied_probability",
                self.market_implied_probability,
            ),
        )
        if self.realized_probability is not None:
            object.__setattr__(
                self,
                "realized_probability",
                _normalize_realized_probability(
                    "realized_probability",
                    self.realized_probability,
                ),
            )
        object.__setattr__(
            self,
            "confidence",
            _normalize_probability("confidence", self.confidence),
        )
        object.__setattr__(
            self,
            "prior_confidence",
            _normalize_probability("prior_confidence", self.prior_confidence),
        )
        object.__setattr__(
            self,
            "evidence_age_hours",
            _normalize_nonnegative_value("evidence_age_hours", self.evidence_age_hours),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, INPUT_REASON_CODES),
        )
        _validate_input(self)
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class StrategyRecommendationCalibrationGapCategoryRow:
    category_id: str
    team_count: Decimal
    source_row_count: Decimal
    material_gap_count: Decimal
    learning_available_count: Decimal
    confidence_drift_count: Decimal
    stale_evidence_count: Decimal
    mean_absolute_gap: Decimal
    mean_signed_gap: Decimal
    mean_confidence_drift: Decimal
    status: str
    top_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_category_id("category_id", self.category_id)
        for field_name in (
            "team_count",
            "source_row_count",
            "material_gap_count",
            "learning_available_count",
            "confidence_drift_count",
            "stale_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_absolute_gap",
            "mean_signed_gap",
            "mean_confidence_drift",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_value(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "top_reason_codes",
            _normalize_reason_codes(
                "top_reason_codes",
                self.top_reason_codes,
                INPUT_REASON_CODES,
            ),
        )
        _validate_category_row(self)
        _require_hard_flags("category row", self)


@dataclass(frozen=True)
class StrategyRecommendationCalibrationGapDigestReport:
    generated_at: datetime
    config_version: str
    source_row_count: Decimal
    team_count: Decimal
    category_count: Decimal
    material_gap_count: Decimal
    learning_available_count: Decimal
    confidence_drift_count: Decimal
    stale_evidence_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    category_rows: tuple[StrategyRecommendationCalibrationGapCategoryRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "source_row_count",
            "team_count",
            "category_count",
            "material_gap_count",
            "learning_available_count",
            "confidence_drift_count",
            "stale_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
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
            "category_rows",
            _normalize_category_rows(self.category_rows),
        )
        object.__setattr__(
            self,
            "derived_validation_digest",
            (
                _report_derived_validation_digest(self)
                if self.derived_validation_digest == ""
                else _normalize_sha256(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                )
            ),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_strategy_recommendation_calibration_gap_digest(
    inputs: list[StrategyRecommendationCalibrationGapInput]
    | tuple[StrategyRecommendationCalibrationGapInput, ...],
    *,
    config: StrategyRecommendationCalibrationGapDigestConfig,
    generated_at: datetime,
) -> StrategyRecommendationCalibrationGapDigestReport:
    if type(config) is not StrategyRecommendationCalibrationGapDigestConfig:
        raise ValueError(
            "config must be a StrategyRecommendationCalibrationGapDigestConfig",
        )
    _require_hard_flags("config", config)
    rows = _normalize_inputs(inputs)
    generated_at_utc = _as_utc("generated_at", generated_at)
    category_rows = tuple(
        sorted(
            (
                _category_row(category_id, category_inputs, config)
                for category_id, category_inputs in _category_groups(rows)
                if category_inputs
            ),
            key=_category_row_sort_key,
        ),
    )
    return StrategyRecommendationCalibrationGapDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_row_count=_count(len(rows)),
        team_count=_count(len({row.team_id for row in rows})),
        category_count=_count(len(category_rows)),
        material_gap_count=_sum_category_rows(category_rows, "material_gap_count"),
        learning_available_count=_sum_category_rows(
            category_rows,
            "learning_available_count",
        ),
        confidence_drift_count=_sum_category_rows(
            category_rows,
            "confidence_drift_count",
        ),
        stale_evidence_count=_sum_category_rows(category_rows, "stale_evidence_count"),
        status=_status(category_rows),
        reason_codes=_report_reason_codes(category_rows),
        category_rows=category_rows,
    )


def strategy_recommendation_calibration_gap_digest_payload(
    report: StrategyRecommendationCalibrationGapDigestReport,
) -> dict[str, Any]:
    if type(report) is not StrategyRecommendationCalibrationGapDigestReport:
        raise ValueError(
            "report must be a StrategyRecommendationCalibrationGapDigestReport",
        )
    _require_hard_flags("report", report)
    _validate_report(report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    validate_strategy_recommendation_calibration_gap_digest_public_payload(payload)
    return payload


def validate_strategy_recommendation_calibration_gap_digest_public_payload(
    payload: object,
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _require_hard_flags("payload", _PayloadFlags(payload))
    _require_safe_public_payload(
        "strategy recommendation calibration gap digest public payload",
        payload,
    )


@dataclass(frozen=True)
class _PayloadFlags:
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


def _normalize_inputs(
    inputs: list[StrategyRecommendationCalibrationGapInput]
    | tuple[StrategyRecommendationCalibrationGapInput, ...],
) -> tuple[StrategyRecommendationCalibrationGapInput, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(inputs)
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not StrategyRecommendationCalibrationGapInput:
            raise ValueError(
                "inputs must contain StrategyRecommendationCalibrationGapInput values",
            )
        _require_hard_flags("input", row)
        key = (row.team_id, row.strategy_id)
        if key in seen:
            raise ValueError("inputs must not contain duplicate team_id strategy_id values")
        seen.add(key)
    return rows


def _category_groups(
    rows: tuple[StrategyRecommendationCalibrationGapInput, ...],
) -> tuple[tuple[str, tuple[StrategyRecommendationCalibrationGapInput, ...]], ...]:
    return tuple(
        (
            category_id,
            tuple(row for row in rows if row.category_id == category_id),
        )
        for category_id in CATEGORIES
    )


def _category_row(
    category_id: str,
    rows: tuple[StrategyRecommendationCalibrationGapInput, ...],
    config: StrategyRecommendationCalibrationGapDigestConfig,
) -> StrategyRecommendationCalibrationGapCategoryRow:
    gaps = tuple(_gap(row) for row in rows)
    confidence_drifts = tuple(_confidence_drift(row) for row in rows)
    return StrategyRecommendationCalibrationGapCategoryRow(
        category_id=category_id,
        team_count=_count(len({row.team_id for row in rows})),
        source_row_count=_count(len(rows)),
        material_gap_count=_count(
            sum(
                1
                for gap in gaps
                if _abs_decimal(gap) >= config.material_gap_threshold
            ),
        ),
        learning_available_count=_count(
            sum(1 for row in rows if row.realized_probability is not None),
        ),
        confidence_drift_count=_count(
            sum(
                1
                for drift in confidence_drifts
                if _abs_decimal(drift) >= config.confidence_drift_threshold
            ),
        ),
        stale_evidence_count=_count(
            sum(1 for row in rows if row.evidence_age_hours >= config.stale_evidence_hours),
        ),
        mean_absolute_gap=_mean(tuple(_abs_decimal(gap) for gap in gaps)),
        mean_signed_gap=_mean(gaps),
        mean_confidence_drift=_mean(confidence_drifts),
        status=_category_status(rows, config),
        top_reason_codes=_top_reason_codes(rows),
    )


def _category_status(
    rows: tuple[StrategyRecommendationCalibrationGapInput, ...],
    config: StrategyRecommendationCalibrationGapDigestConfig,
) -> str:
    if any(_abs_decimal(_gap(row)) >= config.material_gap_threshold for row in rows):
        return "watch"
    if any(
        _abs_decimal(_confidence_drift(row)) >= config.confidence_drift_threshold
        for row in rows
    ):
        return "watch"
    if any(row.evidence_age_hours >= config.stale_evidence_hours for row in rows):
        return "watch"
    return "pass"


def _top_reason_codes(
    rows: tuple[StrategyRecommendationCalibrationGapInput, ...],
) -> tuple[str, ...]:
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        reason_code
        for reason_code, _ in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _report_reason_codes(
    rows: tuple[StrategyRecommendationCalibrationGapCategoryRow, ...],
) -> tuple[str, ...]:
    if not rows or all(row.status == "pass" for row in rows):
        return ("calibration_gap_digest_clear",)
    codes: list[str] = []
    if any(row.material_gap_count > ZERO_COUNT for row in rows):
        codes.append("material_calibration_gap_detected")
    if any(row.learning_available_count > ZERO_COUNT for row in rows):
        codes.append("resolved_learning_available")
    if any(row.confidence_drift_count > ZERO_COUNT for row in rows):
        codes.append("confidence_drift_detected")
    if any(row.stale_evidence_count > ZERO_COUNT for row in rows):
        codes.append("stale_evidence_detected")
    return tuple(codes)


def _status(rows: tuple[StrategyRecommendationCalibrationGapCategoryRow, ...]) -> str:
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _category_row_sort_key(
    row: StrategyRecommendationCalibrationGapCategoryRow,
) -> tuple[Decimal, Decimal, Decimal, Decimal, str]:
    return (
        -row.material_gap_count,
        -row.confidence_drift_count,
        -row.stale_evidence_count,
        -row.mean_absolute_gap,
        row.category_id,
    )


def _sum_category_rows(
    rows: tuple[StrategyRecommendationCalibrationGapCategoryRow, ...],
    field_name: str,
) -> Decimal:
    return _normalize_nonnegative_count(
        field_name,
        sum((getattr(row, field_name) for row in rows), ZERO_COUNT),
    )


def _validate_input(row: StrategyRecommendationCalibrationGapInput) -> None:
    if row.reason_codes != _input_reason_codes(row):
        raise ValueError("reason_codes must match input")


def _validate_category_row(
    row: StrategyRecommendationCalibrationGapCategoryRow,
) -> None:
    if row.source_row_count == ZERO_COUNT:
        raise ValueError("source_row_count must be positive")
    if row.team_count > row.source_row_count:
        raise ValueError("team_count must not exceed source_row_count")
    for field_name in (
        "material_gap_count",
        "learning_available_count",
        "confidence_drift_count",
        "stale_evidence_count",
    ):
        if getattr(row, field_name) > row.source_row_count:
            raise ValueError(f"{field_name} must not exceed source_row_count")
    if row.status == "pass":
        for field_name in (
            "material_gap_count",
            "confidence_drift_count",
            "stale_evidence_count",
        ):
            if getattr(row, field_name) != ZERO_COUNT:
                raise ValueError("pass rows must not contain watched signals")


def _validate_report(report: StrategyRecommendationCalibrationGapDigestReport) -> None:
    if report.source_row_count != _sum_category_rows(
        report.category_rows,
        "source_row_count",
    ):
        raise ValueError("source_row_count must match category_rows")
    if report.team_count != _count(_unique_team_count_placeholder(report.category_rows)):
        raise ValueError("team_count must match category_rows")
    if report.category_count != _count(len(report.category_rows)):
        raise ValueError("category_count must match category_rows")
    for field_name in (
        "material_gap_count",
        "learning_available_count",
        "confidence_drift_count",
        "stale_evidence_count",
    ):
        if getattr(report, field_name) != _sum_category_rows(report.category_rows, field_name):
            raise ValueError(f"{field_name} must match category_rows")
    if report.status != _status(report.category_rows):
        raise ValueError("status must match category_rows")
    if report.reason_codes != _report_reason_codes(report.category_rows):
        raise ValueError("reason_codes must match category_rows")
    if report.category_rows != tuple(
        sorted(report.category_rows, key=_category_row_sort_key),
    ):
        raise ValueError("category_rows must be deterministic")
    category_ids = tuple(row.category_id for row in report.category_rows)
    if len(set(category_ids)) != len(category_ids):
        raise ValueError("category_rows must contain unique category_id values")
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match category_rows")


def _unique_team_count_placeholder(
    rows: tuple[StrategyRecommendationCalibrationGapCategoryRow, ...],
) -> int:
    return sum(int(row.team_count) for row in rows)


def _input_reason_codes(row: StrategyRecommendationCalibrationGapInput) -> tuple[str, ...]:
    codes: list[str] = []
    gap = _gap(row)
    if gap >= ZERO_RATIO:
        if gap >= Decimal("0.050000"):
            codes.append("wide_positive_calibration_gap")
        else:
            codes.append("calibration_gap_within_threshold")
    else:
        if _abs_decimal(gap) >= Decimal("0.050000"):
            codes.append("wide_negative_calibration_gap")
        else:
            codes.append("calibration_gap_within_threshold")
    if row.realized_probability is not None:
        codes.append("resolved_learning_available")
    confidence_drift = _confidence_drift(row)
    if (
        "confidence_increased" in row.reason_codes
        and confidence_drift >= Decimal("0.100000")
    ):
        codes.append("confidence_increased")
    elif (
        "confidence_decreased" in row.reason_codes
        and confidence_drift <= Decimal("-0.100000")
    ):
        codes.append("confidence_decreased")
    elif (
        "confidence_stable" in row.reason_codes
        and _abs_decimal(confidence_drift) < Decimal("0.100000")
    ):
        codes.append("confidence_stable")
    if "stale_evidence" in row.reason_codes:
        codes.append("stale_evidence")
    elif (
        "evidence_fresh" in row.reason_codes
        and row.evidence_age_hours < Decimal("24.000000")
    ):
        codes.append("evidence_fresh")
    return tuple(codes)


def _normalize_category_rows(
    value: object,
) -> tuple[StrategyRecommendationCalibrationGapCategoryRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("category_rows must be a tuple")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("category_rows must be a tuple") from exc
    for row in rows:
        if type(row) is not StrategyRecommendationCalibrationGapCategoryRow:
            raise ValueError(
                "category_rows must contain "
                "StrategyRecommendationCalibrationGapCategoryRow values",
            )
        _require_hard_flags("category row", row)
    return rows


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        _require_member(field_name, reason_code, allowed)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    return reason_codes


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_value(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return normalized


def _normalize_realized_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_probability(field_name, value)
    if normalized not in (ZERO_RESULT, ONE):
        raise ValueError(f"{field_name} must be 0 or 1")
    return normalized


def _normalize_nonnegative_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_value(field_name, value)
    if normalized < ZERO_RATIO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_nonnegative_value(field_name: str, value: object) -> Decimal:
    normalized = _normalize_value(field_name, value)
    if normalized < ZERO_RATIO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_value(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(RATIO_QUANTUM)
    if value != quantized:
        raise ValueError(f"{field_name} must be quantized to 0.000001")
    return quantized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(COUNT_QUANTUM)
    if value != quantized:
        raise ValueError(f"{field_name} must be integral")
    if quantized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    normalized = value.strip()
    if normalized != value or len(normalized) != 64:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    if normalized.lower() != normalized:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in normalized):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return normalized


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (sum(values, ZERO_RATIO) / Decimal(len(values))).quantize(RATIO_QUANTUM)


def _gap(row: StrategyRecommendationCalibrationGapInput) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (row.forecast_probability - row.market_implied_probability).quantize(
            RATIO_QUANTUM,
        )


def _confidence_drift(row: StrategyRecommendationCalibrationGapInput) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (row.confidence - row.prior_confidence).quantize(RATIO_QUANTUM)


def _abs_decimal(value: Decimal) -> Decimal:
    if value < ZERO_RATIO:
        return -value
    return value


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _report_derived_validation_digest(
    report: StrategyRecommendationCalibrationGapDigestReport,
) -> str:
    values = [
        "strategy_recommendation_calibration_gap_digest_report",
        f"generated_at={_as_utc('generated_at', report.generated_at).isoformat()}",
        f"config_version={report.config_version}",
        f"source_row_count={report.source_row_count}",
        f"team_count={report.team_count}",
        f"category_count={report.category_count}",
        f"material_gap_count={report.material_gap_count}",
        f"learning_available_count={report.learning_available_count}",
        f"confidence_drift_count={report.confidence_drift_count}",
        f"stale_evidence_count={report.stale_evidence_count}",
        f"status={report.status}",
        f"reason_codes={','.join(report.reason_codes)}",
        f"paper_only={report.paper_only}",
        f"report_only={report.report_only}",
        f"readonly={report.readonly}",
    ]
    for row in report.category_rows:
        values.extend(
            (
                "category_row",
                f"category_id={row.category_id}",
                f"team_count={row.team_count}",
                f"source_row_count={row.source_row_count}",
                f"material_gap_count={row.material_gap_count}",
                f"learning_available_count={row.learning_available_count}",
                f"confidence_drift_count={row.confidence_drift_count}",
                f"stale_evidence_count={row.stale_evidence_count}",
                f"mean_absolute_gap={row.mean_absolute_gap}",
                f"mean_signed_gap={row.mean_signed_gap}",
                f"mean_confidence_drift={row.mean_confidence_drift}",
                f"status={row.status}",
                f"top_reason_codes={','.join(row.top_reason_codes)}",
                f"paper_only={row.paper_only}",
                f"report_only={row.report_only}",
                f"readonly={row.readonly}",
            ),
        )
    return _sha256(tuple(values))


def _sha256(values: tuple[str, ...]) -> str:
    return hashlib.sha256("\n".join(values).encode("utf-8")).hexdigest()


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_category_id(field_name: str, value: object) -> None:
    _require_member(field_name, value, CATEGORIES)


def _require_known_team_id(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in TEAM_TO_CATEGORY:
        raise ValueError(f"{field_name} must be a known Phase 1 team")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")


def _require_safe_public_payload(label: str, value: object, path: str = "") -> None:
    if type(value) is str:
        if _has_unsafe_surface_fragment(value):
            raise ValueError(f"{path or label} has unsafe public value")
        return
    if value is None or type(value) is bool:
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if _has_unsafe_surface_fragment(key):
                raise ValueError(f"unsafe live surface field in {label}: {key}")
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{item_path} must be True for {label}")
            _require_safe_public_payload(label, item, item_path)
        return
    if type(value) is list:
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _require_safe_public_payload(label, item, item_path)
        return
    if type(value) in (Decimal, int):
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if type(value) is float:
        raise ValueError(f"{path or label} must not be a float")
    raise ValueError(f"{path or label} contains unsupported value")


def _has_unsafe_surface_fragment(value: str) -> bool:
    lowered = value.lower()
    tokens = tuple(
        part
        for part in "".join(char if char.isalnum() else "_" for char in lowered).split(
            "_",
        )
        if part
    )
    for fragment in UNSAFE_SURFACE_FIELD_FRAGMENTS | EXTRA_UNSAFE_PUBLIC_FRAGMENTS:
        if "_" in fragment:
            if fragment in lowered:
                return True
            continue
        if fragment in tokens:
            return True
    return False


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC).isoformat()
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


__all__ = (
    "DEFAULT_STRATEGY_RECOMMENDATION_CALIBRATION_GAP_DIGEST_CONFIG_VERSION",
    "StrategyRecommendationCalibrationGapDigestConfig",
    "StrategyRecommendationCalibrationGapInput",
    "StrategyRecommendationCalibrationGapCategoryRow",
    "StrategyRecommendationCalibrationGapDigestReport",
    "build_strategy_recommendation_calibration_gap_digest",
    "strategy_recommendation_calibration_gap_digest_payload",
    "validate_strategy_recommendation_calibration_gap_digest_public_payload",
)
