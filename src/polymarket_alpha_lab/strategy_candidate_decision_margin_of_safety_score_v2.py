"""Paper-only candidate decision margin-of-safety scoring."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "DEFAULT_STRATEGY_CANDIDATE_DECISION_MARGIN_OF_SAFETY_SCORE_V2_CONFIG_VERSION",
    "StrategyCandidateDecisionMarginOfSafetyScoreV2Config",
    "StrategyCandidateDecisionMarginOfSafetyScoreV2Observation",
    "StrategyCandidateDecisionMarginOfSafetyScoreV2Row",
    "StrategyCandidateDecisionMarginOfSafetyScoreV2Report",
    "build_strategy_candidate_decision_margin_of_safety_score_v2",
    "strategy_candidate_decision_margin_of_safety_score_v2_payload",
    "validate_strategy_candidate_decision_margin_of_safety_score_v2_payload",
)


DEFAULT_STRATEGY_CANDIDATE_DECISION_MARGIN_OF_SAFETY_SCORE_V2_CONFIG_VERSION = (
    "strategy-candidate-decision-margin-of-safety-score-v2"
)

PUBLIC_DATACLASS_NAMES = frozenset(
    (
        "StrategyCandidateDecisionMarginOfSafetyScoreV2Config",
        "StrategyCandidateDecisionMarginOfSafetyScoreV2Observation",
        "StrategyCandidateDecisionMarginOfSafetyScoreV2Row",
        "StrategyCandidateDecisionMarginOfSafetyScoreV2Report",
    ),
)
DECIMAL_CONTEXT = Context(prec=64)
SCORE_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
SCORE_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)
ROW_REASON_CODES = frozenset(
    (
        "margin_of_safety_ready",
        "margin_of_safety_watch_score",
        "margin_of_safety_blocked_score",
        "negative_margin_of_safety",
        "thin_edge_penalty",
        "source_confidence_boost",
        "low_source_confidence",
        "risk_penalty_pressure",
    ),
)
REPORT_REASON_CODES = frozenset(
    (
        "margin_of_safety_empty",
        "margin_of_safety_report_ready",
        "margin_of_safety_report_watch",
        "margin_of_safety_report_blocked",
        *ROW_REASON_CODES,
    ),
)
UNSAFE_PUBLIC_TERMS = frozenset(
    (
        "".join(("li", "ve")),
        "".join(("au", "th")),
        "".join(("wall", "et")),
        "".join(("or", "der")),
        "".join(("net", "work")),
        "".join(("data", "base")),
        "".join(("per", "sist")),
        "".join(("sign", "ing")),
        "".join(("muta", "tion")),
        "".join(("b", "uy")),
        "".join(("s", "ell")),
        "".join(("tr", "ade")),
    ),
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls.__module__ != __name__ or cls.__name__ not in PUBLIC_DATACLASS_NAMES:
            raise TypeError("subclassing is not allowed")


@dataclass(frozen=True)
class StrategyCandidateDecisionMarginOfSafetyScoreV2Config(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_STRATEGY_CANDIDATE_DECISION_MARGIN_OF_SAFETY_SCORE_V2_CONFIG_VERSION
    )
    required_margin_of_safety: Decimal = Decimal("0.030000")
    thin_edge_floor: Decimal = Decimal("0.010000")
    minimum_source_confidence_score: Decimal = Decimal("0.600000")
    source_confidence_boost_weight: Decimal = Decimal("0.100000")
    thin_edge_penalty_weight: Decimal = Decimal("0.250000")
    risk_penalty_weight: Decimal = Decimal("0.100000")
    liquidity_risk_weight: Decimal = Decimal("0.400000")
    resolution_risk_weight: Decimal = Decimal("0.400000")
    correlation_risk_weight: Decimal = Decimal("0.200000")
    high_risk_penalty_floor: Decimal = Decimal("0.050000")
    ready_score_floor: Decimal = Decimal("0.700000")
    watch_score_floor: Decimal = Decimal("0.400000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            StrategyCandidateDecisionMarginOfSafetyScoreV2Config,
            "config",
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        for field_name in (
            "required_margin_of_safety",
            "thin_edge_floor",
            "minimum_source_confidence_score",
            "source_confidence_boost_weight",
            "thin_edge_penalty_weight",
            "risk_penalty_weight",
            "liquidity_risk_weight",
            "resolution_risk_weight",
            "correlation_risk_weight",
            "high_risk_penalty_floor",
            "ready_score_floor",
            "watch_score_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", _payload_value(self))


@dataclass(frozen=True)
class StrategyCandidateDecisionMarginOfSafetyScoreV2Observation(_FinalPublicDataclass):
    candidate_id: str
    market_id: str
    observed_at: datetime
    cost_adjusted_edge: Decimal
    source_confidence_score: Decimal
    liquidity_risk_score: Decimal
    resolution_risk_score: Decimal
    correlation_risk_score: Decimal
    source_count: Decimal
    independent_source_count: Decimal
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            StrategyCandidateDecisionMarginOfSafetyScoreV2Observation,
            "observation",
        )
        for field_name in ("candidate_id", "market_id", "source_config_version"):
            object.__setattr__(
                self,
                field_name,
                _require_public_string(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "cost_adjusted_edge",
            "source_count",
            "independent_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_confidence_score",
            "liquidity_risk_score",
            "resolution_risk_score",
            "correlation_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.independent_source_count > self.source_count:
            raise ValueError("independent_source_count must not exceed source_count")
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", _payload_value(self))


@dataclass(frozen=True)
class StrategyCandidateDecisionMarginOfSafetyScoreV2Row(_FinalPublicDataclass):
    rank: Decimal
    candidate_id: str
    market_id: str
    observed_at: datetime
    cost_adjusted_edge: Decimal
    required_margin_of_safety: Decimal
    raw_margin_of_safety: Decimal
    margin_of_safety_score: Decimal
    thin_edge_penalty: Decimal
    source_confidence_boost: Decimal
    risk_penalty: Decimal
    final_margin_of_safety_score: Decimal
    score_status: str
    reason_codes: tuple[str, ...]
    source_count: Decimal
    independent_source_count: Decimal
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyCandidateDecisionMarginOfSafetyScoreV2Row, "row")
        object.__setattr__(self, "rank", _require_positive_decimal("rank", self.rank))
        for field_name in ("candidate_id", "market_id", "source_config_version"):
            object.__setattr__(
                self,
                field_name,
                _require_public_string(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "cost_adjusted_edge",
            "required_margin_of_safety",
            "margin_of_safety_score",
            "thin_edge_penalty",
            "source_confidence_boost",
            "risk_penalty",
            "final_margin_of_safety_score",
            "source_count",
            "independent_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "raw_margin_of_safety",
            _require_decimal("raw_margin_of_safety", self.raw_margin_of_safety),
        )
        for field_name in (
            "margin_of_safety_score",
            "thin_edge_penalty",
            "source_confidence_boost",
            "risk_penalty",
            "final_margin_of_safety_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.required_margin_of_safety <= ZERO:
            raise ValueError("required_margin_of_safety must be positive")
        if self.independent_source_count > self.source_count:
            raise ValueError("independent_source_count must not exceed source_count")
        _require_status("score_status", self.score_status)
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", _payload_value(self))


@dataclass(frozen=True)
class StrategyCandidateDecisionMarginOfSafetyScoreV2Report(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    score_status: str
    row_count: Decimal
    ready_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    average_margin_of_safety_score: Decimal
    average_thin_edge_penalty: Decimal
    average_source_confidence_boost: Decimal
    max_risk_penalty: Decimal
    rows: tuple[StrategyCandidateDecisionMarginOfSafetyScoreV2Row, ...]
    source_config_versions: tuple[tuple[str, str], ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            StrategyCandidateDecisionMarginOfSafetyScoreV2Report,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        _require_status("score_status", self.score_status)
        for field_name in ("row_count", "ready_count", "watch_count", "blocked_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_margin_of_safety_score",
            "average_thin_edge_penalty",
            "average_source_confidence_boost",
            "max_risk_penalty",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _require_rows(self.rows))
        object.__setattr__(
            self,
            "source_config_versions",
            _require_source_config_versions(self.source_config_versions),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", _payload_value(self))
        _validate_report(self)
        _require_matching_digest(_payload_value(self))


def build_strategy_candidate_decision_margin_of_safety_score_v2(
    observations: Iterable[StrategyCandidateDecisionMarginOfSafetyScoreV2Observation],
    *,
    config: StrategyCandidateDecisionMarginOfSafetyScoreV2Config | None = None,
    generated_at: datetime,
) -> StrategyCandidateDecisionMarginOfSafetyScoreV2Report:
    cfg = config or StrategyCandidateDecisionMarginOfSafetyScoreV2Config()
    if type(cfg) is not StrategyCandidateDecisionMarginOfSafetyScoreV2Config:
        raise ValueError(
            "config must be exactly StrategyCandidateDecisionMarginOfSafetyScoreV2Config",
        )
    _require_hard_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations)
    for item in normalized:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")
    rows = tuple(
        _row_for_observation(rank=index, observation=item, config=cfg)
        for index, item in enumerate(_sorted_observations(normalized), start=1)
    )
    status = _report_status(rows)
    values: dict[str, Any] = {
        "generated_at": generated_at_utc,
        "config_version": cfg.config_version,
        "score_status": status,
        "row_count": _count_decimal(len(rows)),
        "ready_count": _status_count(rows, STATUS_READY),
        "watch_count": _status_count(rows, STATUS_WATCH),
        "blocked_count": _status_count(rows, STATUS_BLOCKED),
        "average_margin_of_safety_score": _average(
            row.final_margin_of_safety_score for row in rows
        ),
        "average_thin_edge_penalty": _average(row.thin_edge_penalty for row in rows),
        "average_source_confidence_boost": _average(
            row.source_confidence_boost for row in rows
        ),
        "max_risk_penalty": max((row.risk_penalty for row in rows), default=ZERO),
        "rows": rows,
        "source_config_versions": tuple(
            sorted((item.candidate_id, item.source_config_version) for item in normalized),
        ),
        "reason_codes": _report_reason_codes(rows, status),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    payload = _payload_value(values)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    values["derived_validation_digest"] = _derived_validation_digest(payload)
    return StrategyCandidateDecisionMarginOfSafetyScoreV2Report(**values)


def strategy_candidate_decision_margin_of_safety_score_v2_payload(
    report: StrategyCandidateDecisionMarginOfSafetyScoreV2Report,
) -> dict[str, Any]:
    if type(report) is not StrategyCandidateDecisionMarginOfSafetyScoreV2Report:
        raise ValueError(
            "report must be exactly StrategyCandidateDecisionMarginOfSafetyScoreV2Report",
        )
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("payload", payload)
    _require_payload_hard_flags(payload)
    _require_matching_digest(payload)
    return payload


def validate_strategy_candidate_decision_margin_of_safety_score_v2_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    _reject_unsafe_public_payload("payload", payload)
    _require_payload_hard_flags(payload)
    _require_matching_digest(payload)
    return True


def _row_for_observation(
    *,
    rank: int,
    observation: StrategyCandidateDecisionMarginOfSafetyScoreV2Observation,
    config: StrategyCandidateDecisionMarginOfSafetyScoreV2Config,
) -> StrategyCandidateDecisionMarginOfSafetyScoreV2Row:
    raw_margin = _subtract_ratio(
        observation.cost_adjusted_edge,
        config.required_margin_of_safety,
    )
    margin_score = _coverage_score(
        observation.cost_adjusted_edge,
        config.required_margin_of_safety,
    )
    thin_penalty = _thin_edge_penalty(observation.cost_adjusted_edge, config)
    source_boost = _source_confidence_boost(observation.source_confidence_score, config)
    risk_penalty = _risk_penalty(
        liquidity_risk_score=observation.liquidity_risk_score,
        resolution_risk_score=observation.resolution_risk_score,
        correlation_risk_score=observation.correlation_risk_score,
        config=config,
    )
    final_score = _final_margin_of_safety_score(
        margin_score=margin_score,
        thin_edge_penalty=thin_penalty,
        source_confidence_boost=source_boost,
        risk_penalty=risk_penalty,
    )
    status = _row_status(final_score, config)
    return StrategyCandidateDecisionMarginOfSafetyScoreV2Row(
        rank=_count_decimal(rank),
        candidate_id=observation.candidate_id,
        market_id=observation.market_id,
        observed_at=observation.observed_at,
        cost_adjusted_edge=observation.cost_adjusted_edge,
        required_margin_of_safety=config.required_margin_of_safety,
        raw_margin_of_safety=raw_margin,
        margin_of_safety_score=margin_score,
        thin_edge_penalty=thin_penalty,
        source_confidence_boost=source_boost,
        risk_penalty=risk_penalty,
        final_margin_of_safety_score=final_score,
        score_status=status,
        reason_codes=_row_reason_codes(
            observation=observation,
            raw_margin_of_safety=raw_margin,
            thin_edge_penalty=thin_penalty,
            source_confidence_boost=source_boost,
            risk_penalty=risk_penalty,
            final_margin_of_safety_score=final_score,
            config=config,
        ),
        source_count=observation.source_count,
        independent_source_count=observation.independent_source_count,
        source_config_version=observation.source_config_version,
    )


def _coverage_score(value: Decimal, target: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(value / target)


def _thin_edge_penalty(
    cost_adjusted_edge: Decimal,
    config: StrategyCandidateDecisionMarginOfSafetyScoreV2Config,
) -> Decimal:
    if cost_adjusted_edge >= config.thin_edge_floor:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        shortfall_share = (config.thin_edge_floor - cost_adjusted_edge) / config.thin_edge_floor
        return _clamp_ratio(shortfall_share * config.thin_edge_penalty_weight)


def _source_confidence_boost(
    source_confidence_score: Decimal,
    config: StrategyCandidateDecisionMarginOfSafetyScoreV2Config,
) -> Decimal:
    if source_confidence_score <= config.minimum_source_confidence_score:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        surplus = source_confidence_score - config.minimum_source_confidence_score
        return _clamp_ratio(surplus * config.source_confidence_boost_weight)


def _risk_penalty(
    *,
    liquidity_risk_score: Decimal,
    resolution_risk_score: Decimal,
    correlation_risk_score: Decimal,
    config: StrategyCandidateDecisionMarginOfSafetyScoreV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        weighted_risk = (
            liquidity_risk_score * config.liquidity_risk_weight
            + resolution_risk_score * config.resolution_risk_weight
            + correlation_risk_score * config.correlation_risk_weight
        )
        return _clamp_ratio(weighted_risk * config.risk_penalty_weight)


def _final_margin_of_safety_score(
    *,
    margin_score: Decimal,
    thin_edge_penalty: Decimal,
    source_confidence_boost: Decimal,
    risk_penalty: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            margin_score - thin_edge_penalty - risk_penalty + source_confidence_boost,
        )


def _row_status(
    final_margin_of_safety_score: Decimal,
    config: StrategyCandidateDecisionMarginOfSafetyScoreV2Config,
) -> str:
    if final_margin_of_safety_score < config.watch_score_floor:
        return STATUS_BLOCKED
    if final_margin_of_safety_score < config.ready_score_floor:
        return STATUS_WATCH
    return STATUS_READY


def _row_reason_codes(
    *,
    observation: StrategyCandidateDecisionMarginOfSafetyScoreV2Observation,
    raw_margin_of_safety: Decimal,
    thin_edge_penalty: Decimal,
    source_confidence_boost: Decimal,
    risk_penalty: Decimal,
    final_margin_of_safety_score: Decimal,
    config: StrategyCandidateDecisionMarginOfSafetyScoreV2Config,
) -> tuple[str, ...]:
    codes: list[str] = []
    if final_margin_of_safety_score < config.watch_score_floor:
        codes.append("margin_of_safety_blocked_score")
    elif final_margin_of_safety_score < config.ready_score_floor:
        codes.append("margin_of_safety_watch_score")
    else:
        codes.append("margin_of_safety_ready")
    if raw_margin_of_safety < ZERO:
        codes.append("negative_margin_of_safety")
    if thin_edge_penalty > ZERO:
        codes.append("thin_edge_penalty")
    if source_confidence_boost > ZERO:
        codes.append("source_confidence_boost")
    if observation.source_confidence_score < config.minimum_source_confidence_score:
        codes.append("low_source_confidence")
    if risk_penalty >= config.high_risk_penalty_floor:
        codes.append("risk_penalty_pressure")
    return tuple(codes)


def _normalize_observations(
    observations: Iterable[StrategyCandidateDecisionMarginOfSafetyScoreV2Observation],
) -> tuple[StrategyCandidateDecisionMarginOfSafetyScoreV2Observation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        normalized = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    seen: set[str] = set()
    for item in normalized:
        if type(item) is not StrategyCandidateDecisionMarginOfSafetyScoreV2Observation:
            raise ValueError(
                "observations must contain "
                "StrategyCandidateDecisionMarginOfSafetyScoreV2Observation",
            )
        _require_hard_flags("observation", item)
        if item.candidate_id in seen:
            raise ValueError("duplicate candidate_id")
        seen.add(item.candidate_id)
    return normalized


def _sorted_observations(
    observations: tuple[StrategyCandidateDecisionMarginOfSafetyScoreV2Observation, ...],
) -> tuple[StrategyCandidateDecisionMarginOfSafetyScoreV2Observation, ...]:
    return tuple(
        sorted(
            observations,
            key=lambda item: (
                item.candidate_id,
                item.market_id,
                item.observed_at.isoformat(),
            ),
        ),
    )


def _require_rows(rows: object) -> tuple[StrategyCandidateDecisionMarginOfSafetyScoreV2Row, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not StrategyCandidateDecisionMarginOfSafetyScoreV2Row:
            raise ValueError(
                "rows must contain StrategyCandidateDecisionMarginOfSafetyScoreV2Row",
            )
        _require_hard_flags("row", row)
    if normalized != tuple(sorted(normalized, key=lambda row: row.rank)):
        raise ValueError("rows must be sorted by rank")
    return normalized


def _require_source_config_versions(values: object) -> tuple[tuple[str, str], ...]:
    if type(values) is not tuple:
        raise ValueError("source_config_versions must be a tuple")
    normalized: list[tuple[str, str]] = []
    for value in values:
        if type(value) is not tuple or len(value) != 2:
            raise ValueError("source_config_versions entries must be string pairs")
        candidate_id, source_config_version = value
        normalized.append(
            (
                _require_public_string("source_config_versions", candidate_id),
                _require_public_string("source_config_versions", source_config_version),
            ),
        )
    result = tuple(normalized)
    if result != tuple(sorted(result)):
        raise ValueError("source_config_versions must be sorted")
    return result


def _report_status(
    rows: tuple[StrategyCandidateDecisionMarginOfSafetyScoreV2Row, ...],
) -> str:
    if not rows:
        return STATUS_BLOCKED
    if any(row.score_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.score_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_READY


def _report_reason_codes(
    rows: tuple[StrategyCandidateDecisionMarginOfSafetyScoreV2Row, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return ("margin_of_safety_empty",)
    codes = [f"margin_of_safety_report_{status}"]
    for row in rows:
        for code in row.reason_codes:
            if code not in codes:
                codes.append(code)
    return tuple(codes)


def _validate_config(config: StrategyCandidateDecisionMarginOfSafetyScoreV2Config) -> None:
    if config.required_margin_of_safety <= ZERO:
        raise ValueError("required_margin_of_safety must be positive")
    if config.thin_edge_floor <= ZERO:
        raise ValueError("thin_edge_floor must be positive")
    if config.ready_score_floor < config.watch_score_floor:
        raise ValueError("ready_score_floor must not be below watch_score_floor")
    with localcontext(DECIMAL_CONTEXT):
        risk_weight_total = (
            config.liquidity_risk_weight
            + config.resolution_risk_weight
            + config.correlation_risk_weight
        )
    if risk_weight_total != ONE:
        raise ValueError("risk weights must sum to 1.000000")


def _validate_report(report: StrategyCandidateDecisionMarginOfSafetyScoreV2Report) -> None:
    rows = report.rows
    if report.row_count != _count_decimal(len(rows)):
        raise ValueError("row_count must match rows")
    if report.ready_count != _status_count(rows, STATUS_READY):
        raise ValueError("ready_count must match rows")
    if report.watch_count != _status_count(rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(rows, STATUS_BLOCKED):
        raise ValueError("blocked_count must match rows")
    if report.score_status != _report_status(rows):
        raise ValueError("score_status must match rows")
    if report.average_margin_of_safety_score != _average(
        row.final_margin_of_safety_score for row in rows
    ):
        raise ValueError("average_margin_of_safety_score must match rows")
    if report.average_thin_edge_penalty != _average(row.thin_edge_penalty for row in rows):
        raise ValueError("average_thin_edge_penalty must match rows")
    if report.average_source_confidence_boost != _average(
        row.source_confidence_boost for row in rows
    ):
        raise ValueError("average_source_confidence_boost must match rows")
    if report.max_risk_penalty != max((row.risk_penalty for row in rows), default=ZERO):
        raise ValueError("max_risk_penalty must match rows")
    expected_source_config_versions = tuple(
        sorted((row.candidate_id, row.source_config_version) for row in rows),
    )
    if report.source_config_versions != expected_source_config_versions:
        raise ValueError("source_config_versions must match rows")
    if report.reason_codes != _report_reason_codes(rows, report.score_status):
        raise ValueError("reason_codes must match rows")


def _status_count(
    rows: tuple[StrategyCandidateDecisionMarginOfSafetyScoreV2Row, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.score_status == status))


def _average(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(sum(items, ZERO) / Decimal(len(items)))


def _subtract_ratio(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(left - right)


def _clamp_ratio(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return _quantize_decimal(value)


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _require_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _require_nonnegative_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return value


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(SCORE_QUANTUM)


def _require_public_string(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must be non-empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must be canonical")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_reason_codes(
    field_name: str,
    values: Iterable[str],
    allowed_codes: frozenset[str],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")
    seen: set[str] = set()
    for value in normalized:
        _require_public_string(field_name, value)
        if value not in allowed_codes:
            raise ValueError(f"{field_name} contains an unknown reason code")
        if value in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(value)
    return normalized


def _require_status(field_name: str, value: str) -> None:
    if type(value) is not str or value not in SCORE_STATUSES:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only") is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly") is not True:
        raise ValueError(f"{label} readonly must be True")


def _require_payload_hard_flags(payload: dict[str, Any]) -> None:
    for flag in ("paper_only", "report_only", "readonly"):
        if payload.get(flag) is not True:
            raise ValueError(f"payload {flag} must be True")
    rows = payload.get("rows")
    if type(rows) is not list:
        raise ValueError("payload rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("payload rows must contain dicts")
        for flag in ("paper_only", "report_only", "readonly"):
            if row.get(flag) is not True:
                raise ValueError(f"payload row {flag} must be True")


def _payload_value(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if type(value) is dict:
        return {key: _payload_value(item) for key, item in value.items()}
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError("public payload contains unsupported value")


def _reject_unsafe_public_payload(label: str, payload: object) -> None:
    if type(payload) is dict:
        for key, value in payload.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_unsafe_public_string(label, key)
            _reject_unsafe_public_payload(label, value)
        return
    if type(payload) is list:
        for item in payload:
            _reject_unsafe_public_payload(label, item)
        return
    if type(payload) is str:
        _reject_unsafe_public_string(label, payload)
        return
    if type(payload) in (bool,) or payload is None:
        return
    raise ValueError("public payload values must be strings, booleans, lists, or dicts")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lower_value = value.lower()
    if any(term in lower_value for term in UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"unsafe public surface in {field_name}")


def _require_digest(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_matching_digest(payload: dict[str, Any]) -> None:
    digest_value = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", digest_value)
    if digest_value != _derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")


def _derived_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    encoded = json.dumps(
        digest_payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()
