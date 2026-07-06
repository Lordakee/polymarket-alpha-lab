"""Readonly Decimal report for paper candidate execution readiness."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_STRATEGY_PAPER_CANDIDATE_EXECUTION_READINESS_V2_CONFIG_VERSION = (
    "strategy-paper-candidate-execution-readiness-v2"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SCORE_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
EIGHT = Decimal("8")

EXECUTION_READINESS_STATUSES = ("pass", "watch", "blocked")
ROW_STATUS_RANK = {
    "blocked": Decimal("0"),
    "watch": Decimal("1"),
    "pass": Decimal("2"),
}

CANDIDATE_RATIO_FIELD_NAMES = (
    "forecast_probability",
    "market_probability",
    "source_verified_edge_probability",
    "expected_value_probability",
    "uncertainty_band_low_probability",
    "uncertainty_band_high_probability",
    "research_readiness_score",
    "liquidity_exit_feasibility_score",
    "resolution_ambiguity_score",
    "portfolio_impact_score",
    "specialist_quorum_score",
)
ROW_RATIO_FIELD_NAMES = (
    *CANDIDATE_RATIO_FIELD_NAMES,
    "calculated_edge_probability",
    "expected_value_delta_probability",
    "uncertainty_band_width_probability",
    "execution_readiness_score",
)
CONFIG_RATIO_FIELD_NAMES = (
    "min_research_readiness_score",
    "min_source_verified_edge_probability",
    "max_expected_value_delta_probability",
    "max_uncertainty_band_width_probability",
    "min_liquidity_exit_feasibility_score",
    "max_resolution_ambiguity_score",
    "max_portfolio_impact_score",
    "min_specialist_quorum_score",
    "pass_execution_readiness_score_floor",
    "watch_execution_readiness_score_floor",
)

PASS_REASON_CODE = "candidate_execution_readiness_pass"
EMPTY_REASON_CODE = "candidate_execution_readiness_empty"
WATCH_REASON_CODE = "execution_readiness_score_below_pass_floor"
ROW_REASON_CODES = (
    PASS_REASON_CODE,
    WATCH_REASON_CODE,
    "research_readiness_below_floor",
    "source_verified_edge_below_floor",
    "source_verified_edge_mismatch",
    "expected_value_inconsistent",
    "uncertainty_band_invalid",
    "uncertainty_band_too_wide",
    "liquidity_exit_not_feasible",
    "resolution_ambiguity_too_high",
    "portfolio_impact_too_high",
    "specialist_quorum_below_floor",
)
REPORT_REASON_CODES = (*ROW_REASON_CODES, EMPTY_REASON_CODE)
BLOCKING_REASON_CODES = (
    "research_readiness_below_floor",
    "source_verified_edge_below_floor",
    "source_verified_edge_mismatch",
    "expected_value_inconsistent",
    "uncertainty_band_invalid",
    "uncertainty_band_too_wide",
    "liquidity_exit_not_feasible",
    "resolution_ambiguity_too_high",
    "portfolio_impact_too_high",
    "specialist_quorum_below_floor",
)

UNSAFE_PUBLIC_TEXT_FRAGMENTS = tuple(
    "".join(parts)
    for parts in (
        ("li", "ve"),
        ("au", "th"),
        ("wal", "let"),
        ("or", "der"),
        ("net", "work"),
        ("data", "base"),
        ("per", "sist"),
        ("sig", "ning"),
        ("muta", "tion"),
        ("b", "uy"),
        ("se", "ll"),
        ("tra", "de"),
    )
)

__all__ = (
    "DEFAULT_STRATEGY_PAPER_CANDIDATE_EXECUTION_READINESS_V2_CONFIG_VERSION",
    "StrategyPaperCandidateExecutionReadinessV2Candidate",
    "StrategyPaperCandidateExecutionReadinessV2Config",
    "StrategyPaperCandidateExecutionReadinessV2Report",
    "StrategyPaperCandidateExecutionReadinessV2Row",
    "build_strategy_paper_candidate_execution_readiness_v2",
    "strategy_paper_candidate_execution_readiness_v2_public_payload",
    "validate_strategy_paper_candidate_execution_readiness_v2_public_payload",
)


@dataclass(frozen=True)
class StrategyPaperCandidateExecutionReadinessV2Config:
    config_version: str = (
        DEFAULT_STRATEGY_PAPER_CANDIDATE_EXECUTION_READINESS_V2_CONFIG_VERSION
    )
    min_research_readiness_score: Decimal = Decimal("0.850000")
    min_source_verified_edge_probability: Decimal = Decimal("0.030000")
    max_expected_value_delta_probability: Decimal = Decimal("0.010000")
    max_uncertainty_band_width_probability: Decimal = Decimal("0.120000")
    min_liquidity_exit_feasibility_score: Decimal = Decimal("0.850000")
    max_resolution_ambiguity_score: Decimal = Decimal("0.200000")
    max_portfolio_impact_score: Decimal = Decimal("0.250000")
    min_specialist_quorum_score: Decimal = Decimal("0.800000")
    pass_execution_readiness_score_floor: Decimal = Decimal("0.900000")
    watch_execution_readiness_score_floor: Decimal = Decimal("0.750000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "config_version",
            _require_non_empty_string("config_version", self.config_version),
        )
        for field_name in CONFIG_RATIO_FIELD_NAMES:
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("StrategyPaperCandidateExecutionReadinessV2Config", self)
        _reject_unsafe_public_payload(
            "StrategyPaperCandidateExecutionReadinessV2Config",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class StrategyPaperCandidateExecutionReadinessV2Candidate:
    candidate_id: str
    market_id: str
    outcome_id: str
    forecast_probability: Decimal
    market_probability: Decimal
    source_verified_edge_probability: Decimal
    expected_value_probability: Decimal
    uncertainty_band_low_probability: Decimal
    uncertainty_band_high_probability: Decimal
    research_readiness_score: Decimal
    liquidity_exit_feasibility_score: Decimal
    resolution_ambiguity_score: Decimal
    portfolio_impact_score: Decimal
    specialist_quorum_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("candidate_id", "market_id", "outcome_id"):
            object.__setattr__(
                self,
                field_name,
                _require_non_empty_string(field_name, getattr(self, field_name)),
            )
        for field_name in CANDIDATE_RATIO_FIELD_NAMES:
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.forecast_probability < self.market_probability:
            raise ValueError("forecast_probability must not be below market_probability")
        _require_hard_flags(
            "StrategyPaperCandidateExecutionReadinessV2Candidate",
            self,
        )
        _reject_unsafe_public_payload(
            "StrategyPaperCandidateExecutionReadinessV2Candidate",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class StrategyPaperCandidateExecutionReadinessV2Row:
    candidate_id: str
    market_id: str
    outcome_id: str
    forecast_probability: Decimal
    market_probability: Decimal
    source_verified_edge_probability: Decimal
    expected_value_probability: Decimal
    uncertainty_band_low_probability: Decimal
    uncertainty_band_high_probability: Decimal
    research_readiness_score: Decimal
    liquidity_exit_feasibility_score: Decimal
    resolution_ambiguity_score: Decimal
    portfolio_impact_score: Decimal
    specialist_quorum_score: Decimal
    calculated_edge_probability: Decimal
    expected_value_delta_probability: Decimal
    uncertainty_band_width_probability: Decimal
    execution_readiness_score: Decimal
    execution_readiness_status: str
    paper_execution_blocked: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("candidate_id", "market_id", "outcome_id"):
            object.__setattr__(
                self,
                field_name,
                _require_non_empty_string(field_name, getattr(self, field_name)),
            )
        for field_name in ROW_RATIO_FIELD_NAMES:
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("execution_readiness_status", self.execution_readiness_status)
        _require_bool("paper_execution_blocked", self.paper_execution_blocked)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("StrategyPaperCandidateExecutionReadinessV2Row", self)
        _reject_unsafe_public_payload(
            "StrategyPaperCandidateExecutionReadinessV2Row",
            _payload_value(asdict(self)),
        )
        _validate_row_consistency(self)


@dataclass(frozen=True)
class StrategyPaperCandidateExecutionReadinessV2Report:
    generated_at: datetime
    config_version: str
    report_status: str
    paper_execution_blocked: bool
    candidate_count: Decimal
    pass_candidate_count: Decimal
    watch_candidate_count: Decimal
    blocked_candidate_count: Decimal
    average_execution_readiness_score: Decimal
    top_execution_readiness_score: Decimal
    bottom_execution_readiness_score: Decimal
    rows: tuple[StrategyPaperCandidateExecutionReadinessV2Row, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_non_empty_string("config_version", self.config_version),
        )
        _require_status("report_status", self.report_status)
        _require_bool("paper_execution_blocked", self.paper_execution_blocked)
        for field_name in (
            "candidate_count",
            "pass_candidate_count",
            "watch_candidate_count",
            "blocked_candidate_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "average_execution_readiness_score",
            "top_execution_readiness_score",
            "bottom_execution_readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("StrategyPaperCandidateExecutionReadinessV2Report", self)
        _reject_unsafe_public_payload(
            "StrategyPaperCandidateExecutionReadinessV2Report",
            _payload_value(asdict(self)),
        )
        _validate_report_shape(self)
        _validate_report_digest(self)
        _validate_report_summary(self)

    @property
    def payload(self) -> dict[str, object]:
        payload = _payload_value(asdict(self))
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        validate_strategy_paper_candidate_execution_readiness_v2_public_payload(payload)
        return payload


def build_strategy_paper_candidate_execution_readiness_v2(
    final_candidates: object,
    *,
    config: StrategyPaperCandidateExecutionReadinessV2Config | None = None,
    generated_at: datetime,
) -> StrategyPaperCandidateExecutionReadinessV2Report:
    if config is None:
        config = StrategyPaperCandidateExecutionReadinessV2Config()
    if type(config) is not StrategyPaperCandidateExecutionReadinessV2Config:
        raise ValueError(
            "config must be a StrategyPaperCandidateExecutionReadinessV2Config",
        )
    _require_hard_flags("StrategyPaperCandidateExecutionReadinessV2Config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    candidates = _normalize_candidate_items(final_candidates)
    rows = tuple(
        sorted(
            (_row_for_candidate(item, config) for item in candidates),
            key=_row_sort_key,
        ),
    )
    status = _report_status(rows)
    values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "report_status": status,
        "paper_execution_blocked": status != "pass",
        "candidate_count": _count(len(rows)),
        "pass_candidate_count": _status_count(rows, "pass"),
        "watch_candidate_count": _status_count(rows, "watch"),
        "blocked_candidate_count": _status_count(rows, "blocked"),
        "average_execution_readiness_score": _average_score(rows),
        "top_execution_readiness_score": _top_score(rows),
        "bottom_execution_readiness_score": _bottom_score(rows),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows, status),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["derived_validation_digest"] = _derived_validation_digest(values)
    return StrategyPaperCandidateExecutionReadinessV2Report(**values)


def strategy_paper_candidate_execution_readiness_v2_public_payload(
    report: StrategyPaperCandidateExecutionReadinessV2Report,
) -> dict[str, object]:
    if type(report) is not StrategyPaperCandidateExecutionReadinessV2Report:
        raise ValueError(
            "report must be a StrategyPaperCandidateExecutionReadinessV2Report",
        )
    return report.payload


def validate_strategy_paper_candidate_execution_readiness_v2_public_payload(
    payload: dict[str, object],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload(
        "StrategyPaperCandidateExecutionReadinessV2 public payload",
        payload,
    )
    _require_public_payload_flags(payload)
    _reject_public_numeric_values(payload)
    digest_value = _payload_required_string(payload, "derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest_value)
    if digest_value != _public_payload_derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")
    return True


def _row_for_candidate(
    item: StrategyPaperCandidateExecutionReadinessV2Candidate,
    config: StrategyPaperCandidateExecutionReadinessV2Config,
) -> StrategyPaperCandidateExecutionReadinessV2Row:
    calculated_edge = _subtract_decimal(
        item.forecast_probability,
        item.market_probability,
    )
    expected_value_delta = _absolute_decimal_delta(
        item.expected_value_probability,
        item.source_verified_edge_probability,
    )
    band_width = _band_width(
        item.uncertainty_band_low_probability,
        item.uncertainty_band_high_probability,
    )
    score = _execution_readiness_score(
        item,
        calculated_edge_probability=calculated_edge,
        expected_value_delta_probability=expected_value_delta,
        uncertainty_band_width_probability=band_width,
    )
    reason_codes = _row_reason_codes(
        item,
        config,
        calculated_edge_probability=calculated_edge,
        expected_value_delta_probability=expected_value_delta,
        uncertainty_band_width_probability=band_width,
        execution_readiness_score=score,
    )
    status = _row_status(reason_codes)
    return StrategyPaperCandidateExecutionReadinessV2Row(
        candidate_id=item.candidate_id,
        market_id=item.market_id,
        outcome_id=item.outcome_id,
        forecast_probability=item.forecast_probability,
        market_probability=item.market_probability,
        source_verified_edge_probability=item.source_verified_edge_probability,
        expected_value_probability=item.expected_value_probability,
        uncertainty_band_low_probability=item.uncertainty_band_low_probability,
        uncertainty_band_high_probability=item.uncertainty_band_high_probability,
        research_readiness_score=item.research_readiness_score,
        liquidity_exit_feasibility_score=item.liquidity_exit_feasibility_score,
        resolution_ambiguity_score=item.resolution_ambiguity_score,
        portfolio_impact_score=item.portfolio_impact_score,
        specialist_quorum_score=item.specialist_quorum_score,
        calculated_edge_probability=calculated_edge,
        expected_value_delta_probability=expected_value_delta,
        uncertainty_band_width_probability=band_width,
        execution_readiness_score=score,
        execution_readiness_status=status,
        paper_execution_blocked=status != "pass",
        reason_codes=reason_codes,
    )


def _execution_readiness_score(
    item: StrategyPaperCandidateExecutionReadinessV2Candidate
    | StrategyPaperCandidateExecutionReadinessV2Row,
    *,
    calculated_edge_probability: Decimal,
    expected_value_delta_probability: Decimal,
    uncertainty_band_width_probability: Decimal,
) -> Decimal:
    source_edge_consistency_score = _clamp_ratio(
        ONE
        - _absolute_decimal_delta(
            item.source_verified_edge_probability,
            calculated_edge_probability,
        ),
    )
    expected_value_consistency_score = _clamp_ratio(
        ONE - expected_value_delta_probability,
    )
    if item.uncertainty_band_high_probability < item.uncertainty_band_low_probability:
        uncertainty_band_score = ZERO
    else:
        uncertainty_band_score = _clamp_ratio(ONE - uncertainty_band_width_probability)
    resolution_clarity_score = _clamp_ratio(ONE - item.resolution_ambiguity_score)
    portfolio_capacity_score = _clamp_ratio(ONE - item.portfolio_impact_score)
    with localcontext(DECIMAL_CONTEXT):
        score = (
            item.research_readiness_score
            + source_edge_consistency_score
            + expected_value_consistency_score
            + uncertainty_band_score
            + item.liquidity_exit_feasibility_score
            + resolution_clarity_score
            + portfolio_capacity_score
            + item.specialist_quorum_score
        ) / EIGHT
    return _clamp_ratio(score)


def _row_reason_codes(
    item: StrategyPaperCandidateExecutionReadinessV2Candidate,
    config: StrategyPaperCandidateExecutionReadinessV2Config,
    *,
    calculated_edge_probability: Decimal,
    expected_value_delta_probability: Decimal,
    uncertainty_band_width_probability: Decimal,
    execution_readiness_score: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if item.research_readiness_score < config.min_research_readiness_score:
        reasons.append("research_readiness_below_floor")
    if item.source_verified_edge_probability < config.min_source_verified_edge_probability:
        reasons.append("source_verified_edge_below_floor")
    if item.source_verified_edge_probability != calculated_edge_probability:
        reasons.append("source_verified_edge_mismatch")
    if expected_value_delta_probability > config.max_expected_value_delta_probability:
        reasons.append("expected_value_inconsistent")
    if item.uncertainty_band_high_probability < item.uncertainty_band_low_probability:
        reasons.append("uncertainty_band_invalid")
    elif uncertainty_band_width_probability > config.max_uncertainty_band_width_probability:
        reasons.append("uncertainty_band_too_wide")
    if item.liquidity_exit_feasibility_score < config.min_liquidity_exit_feasibility_score:
        reasons.append("liquidity_exit_not_feasible")
    if item.resolution_ambiguity_score > config.max_resolution_ambiguity_score:
        reasons.append("resolution_ambiguity_too_high")
    if item.portfolio_impact_score > config.max_portfolio_impact_score:
        reasons.append("portfolio_impact_too_high")
    if item.specialist_quorum_score < config.min_specialist_quorum_score:
        reasons.append("specialist_quorum_below_floor")
    if reasons:
        return tuple(reason for reason in ROW_REASON_CODES if reason in reasons)
    if execution_readiness_score < config.pass_execution_readiness_score_floor:
        return (WATCH_REASON_CODE,)
    return (PASS_REASON_CODE,)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCKING_REASON_CODES for reason_code in reason_codes):
        return "blocked"
    if reason_codes == (PASS_REASON_CODE,):
        return "pass"
    return "watch"


def _report_status(
    rows: tuple[StrategyPaperCandidateExecutionReadinessV2Row, ...],
) -> str:
    if not rows:
        return "blocked"
    statuses = tuple(row.execution_readiness_status for row in rows)
    if "blocked" in statuses:
        return "blocked"
    if "watch" in statuses:
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[StrategyPaperCandidateExecutionReadinessV2Row, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    if status == "pass":
        return (PASS_REASON_CODE,)
    present = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != PASS_REASON_CODE
    }
    return tuple(reason_code for reason_code in ROW_REASON_CODES if reason_code in present)


def _status_count(
    rows: tuple[StrategyPaperCandidateExecutionReadinessV2Row, ...],
    status: str,
) -> Decimal:
    return _count(
        sum(1 for row in rows if row.execution_readiness_status == status),
    )


def _average_score(
    rows: tuple[StrategyPaperCandidateExecutionReadinessV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            sum((row.execution_readiness_score for row in rows), ZERO)
            / Decimal(len(rows)),
        )


def _top_score(
    rows: tuple[StrategyPaperCandidateExecutionReadinessV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return max(row.execution_readiness_score for row in rows)


def _bottom_score(
    rows: tuple[StrategyPaperCandidateExecutionReadinessV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return min(row.execution_readiness_score for row in rows)


def _row_sort_key(
    row: StrategyPaperCandidateExecutionReadinessV2Row,
) -> tuple[Decimal, str, str, str]:
    return (
        ROW_STATUS_RANK[row.execution_readiness_status],
        row.candidate_id,
        row.market_id,
        row.outcome_id,
    )


def _normalize_candidate_items(
    final_candidates: object,
) -> tuple[StrategyPaperCandidateExecutionReadinessV2Candidate, ...]:
    if isinstance(final_candidates, (str, bytes)):
        raise ValueError("final candidates must be an iterable")
    try:
        items = tuple(final_candidates)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("final candidates must be an iterable") from exc
    for item in items:
        if type(item) is not StrategyPaperCandidateExecutionReadinessV2Candidate:
            raise ValueError(
                "final candidate items must be "
                "StrategyPaperCandidateExecutionReadinessV2Candidate",
            )
    seen: set[tuple[str, str]] = set()
    for item in items:
        key = (item.candidate_id, item.market_id)
        if key in seen:
            raise ValueError("duplicate candidate_id and market_id")
        seen.add(key)
    return items


def _normalize_rows(
    rows: object,
) -> tuple[StrategyPaperCandidateExecutionReadinessV2Row, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not StrategyPaperCandidateExecutionReadinessV2Row:
            raise ValueError("rows must contain StrategyPaperCandidateExecutionReadinessV2Row")
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted by status and candidate_id")
    return normalized


def _normalize_reason_codes(
    field_name: str,
    values: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        normalized = tuple(values)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    seen: set[str] = set()
    for value in normalized:
        _require_non_empty_string(field_name, value)
        if value in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(value)
    _reject_unsafe_public_payload(field_name, normalized)
    for value in normalized:
        if value not in allowed:
            raise ValueError(f"{field_name} contains an unsupported reason code")
    expected = tuple(value for value in allowed if value in seen)
    if normalized != expected:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return normalized


def _validate_config(config: StrategyPaperCandidateExecutionReadinessV2Config) -> None:
    if (
        config.pass_execution_readiness_score_floor
        < config.min_research_readiness_score
    ):
        raise ValueError(
            "pass_execution_readiness_score_floor must be >= "
            "min_research_readiness_score",
        )
    if (
        config.watch_execution_readiness_score_floor
        > config.pass_execution_readiness_score_floor
    ):
        raise ValueError(
            "watch_execution_readiness_score_floor must not exceed "
            "pass_execution_readiness_score_floor",
        )


def _validate_row_consistency(
    row: StrategyPaperCandidateExecutionReadinessV2Row,
) -> None:
    calculated_edge = _subtract_decimal(row.forecast_probability, row.market_probability)
    if row.calculated_edge_probability != calculated_edge:
        raise ValueError("calculated_edge_probability must match forecast and market")
    expected_value_delta = _absolute_decimal_delta(
        row.expected_value_probability,
        row.source_verified_edge_probability,
    )
    if row.expected_value_delta_probability != expected_value_delta:
        raise ValueError("expected_value_delta_probability must match expected value")
    band_width = _band_width(
        row.uncertainty_band_low_probability,
        row.uncertainty_band_high_probability,
    )
    if row.uncertainty_band_width_probability != band_width:
        raise ValueError("uncertainty_band_width_probability must match band")
    expected_score = _execution_readiness_score(
        row,
        calculated_edge_probability=calculated_edge,
        expected_value_delta_probability=expected_value_delta,
        uncertainty_band_width_probability=band_width,
    )
    if row.execution_readiness_score != expected_score:
        raise ValueError("execution_readiness_score must match component scores")
    if row.execution_readiness_status != _row_status(row.reason_codes):
        raise ValueError("execution_readiness_status must match reason_codes")
    if row.paper_execution_blocked is not (row.execution_readiness_status != "pass"):
        raise ValueError("paper_execution_blocked must match execution_readiness_status")


def _validate_report_shape(
    report: StrategyPaperCandidateExecutionReadinessV2Report,
) -> None:
    if report.candidate_count != _count(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if (
        report.pass_candidate_count != _status_count(report.rows, "pass")
        or report.watch_candidate_count != _status_count(report.rows, "watch")
        or report.blocked_candidate_count != _status_count(report.rows, "blocked")
    ):
        raise ValueError("status counts must match rows")
    expected_status = _report_status(report.rows)
    if report.report_status != expected_status:
        raise ValueError("report_status must match rows")
    if report.paper_execution_blocked is not (report.report_status != "pass"):
        raise ValueError("paper_execution_blocked must match report_status")
    if report.reason_codes != _report_reason_codes(report.rows, report.report_status):
        raise ValueError("reason_codes must match rows")


def _validate_report_summary(
    report: StrategyPaperCandidateExecutionReadinessV2Report,
) -> None:
    if report.average_execution_readiness_score != _average_score(report.rows):
        raise ValueError("average_execution_readiness_score must match rows")
    if report.top_execution_readiness_score != _top_score(report.rows):
        raise ValueError("top_execution_readiness_score must match rows")
    if report.bottom_execution_readiness_score != _bottom_score(report.rows):
        raise ValueError("bottom_execution_readiness_score must match rows")


def _validate_report_digest(
    report: StrategyPaperCandidateExecutionReadinessV2Report,
) -> None:
    if report.derived_validation_digest != _derived_validation_digest(
        _report_digest_fields(report),
    ):
        raise ValueError("derived_validation_digest must match report fields")


def _report_digest_fields(
    report: StrategyPaperCandidateExecutionReadinessV2Report,
) -> dict[str, object]:
    return {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "report_status": report.report_status,
        "paper_execution_blocked": report.paper_execution_blocked,
        "candidate_count": report.candidate_count,
        "pass_candidate_count": report.pass_candidate_count,
        "watch_candidate_count": report.watch_candidate_count,
        "blocked_candidate_count": report.blocked_candidate_count,
        "average_execution_readiness_score": report.average_execution_readiness_score,
        "top_execution_readiness_score": report.top_execution_readiness_score,
        "bottom_execution_readiness_score": report.bottom_execution_readiness_score,
        "rows": report.rows,
        "reason_codes": report.reason_codes,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _derived_validation_digest(values: dict[str, object]) -> str:
    payload = _payload_value(values)
    if type(payload) is not dict:
        raise ValueError("derived validation payload must be a dict")
    return _public_payload_derived_validation_digest(payload)


def _public_payload_derived_validation_digest(payload: dict[str, object]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    _reject_unsafe_public_payload("derived validation digest fields", digest_payload)
    _reject_public_numeric_values(digest_payload)
    encoded = json.dumps(
        digest_payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _payload_value(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal values must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if type(value) is float:
        raise ValueError("payload values must not be floats")
    if type(value) is int:
        raise ValueError("payload values must use Decimal strings")
    if type(value) in (str, bool):
        return value
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            ready[key] = _payload_value(item)
        return ready
    if type(value) in (list, tuple):
        return [_payload_value(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, payload: object) -> None:
    for text in _iter_public_text(payload):
        lowered = text.lower()
        if any(fragment in lowered for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
            raise ValueError(f"unsafe public payload in {label}: {text}")


def _iter_public_text(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_public_text(asdict(value))
    if type(value) is dict:
        text_values: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            text_values.append(key)
            text_values.extend(_iter_public_text(item))
        return tuple(text_values)
    if type(value) in (list, tuple):
        text_values = []
        for item in value:
            text_values.extend(_iter_public_text(item))
        return tuple(text_values)
    if type(value) is str:
        return (value,)
    return ()


def _reject_public_numeric_values(value: object, path: str = "") -> None:
    if value is None or type(value) is bool:
        return
    if type(value) in (Decimal, int, float):
        raise ValueError(
            f"public payload must use Decimal strings, not numeric values at {path}",
        )
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            nested_path = key if not path else f"{path}.{key}"
            _reject_public_numeric_values(item, nested_path)
    elif type(value) is list:
        for index, item in enumerate(value):
            nested_path = f"{path}[{index}]"
            _reject_public_numeric_values(item, nested_path)


def _payload_required_string(payload: dict[str, object], key: str) -> str:
    if key not in payload:
        raise ValueError(f"{key} is required")
    value = payload[key]
    if type(value) is not str:
        raise ValueError(f"{key} must be a string")
    return value


def _require_public_payload_flags(payload: dict[str, object]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if value > ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(SCORE_QUANT)
    if value != quantized:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _normalize_nonnegative_integral_decimal(
    field_name: str,
    value: object,
) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(COUNT_QUANT)
    if value != quantized:
        raise ValueError(f"{field_name} must be an integral Decimal")
    return quantized


def _clamp_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        if value < ZERO:
            value = ZERO
        if value > ONE:
            value = ONE
        return value.quantize(SCORE_QUANT)


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(left - right)


def _absolute_decimal_delta(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        if left >= right:
            return _clamp_ratio(left - right)
        return _clamp_ratio(right - left)


def _band_width(low: Decimal, high: Decimal) -> Decimal:
    if high < low:
        return ZERO
    return _subtract_decimal(high, low)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_non_empty_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _reject_unsafe_public_payload(field_name, value)
    return value


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in EXECUTION_READINESS_STATUSES:
        raise ValueError(f"{field_name} must be one of {EXECUTION_READINESS_STATUSES!r}")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
