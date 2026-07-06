"""Decimal-only paper gate for recommendation counter-evidence quorum."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any


_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_SECONDS_PER_DAY = Decimal("86400")
_MICROS_PER_SECOND = Decimal("1000000")
_SIDES = ("yes", "no")
_STATUSES = ("blocked", "discounted", "passed")
_STATUS_RANK = {"blocked": 0, "discounted": 1, "passed": 2}
_REASON_RANK = {
    "counter_evidence_blocked": 0,
    "counter_evidence_discounted": 1,
    "counter_evidence_quorum_met": 2,
    "counter_evidence_confidence_floor_gap": 3,
    "counter_evidence_family_quorum_gap": 4,
    "counter_evidence_independence_gap": 5,
    "counter_evidence_recency_gap": 6,
}
_REASON_CODES = frozenset(_REASON_RANK)


@dataclass(frozen=True)
class StrategyRecommendationCounterEvidenceQuorumGateV2Config:
    config_version: str
    min_counter_evidence_family_count: Decimal
    min_recent_family_count: Decimal
    min_independent_source_count: Decimal
    min_source_independence_score: Decimal
    max_counter_evidence_age_seconds: Decimal
    family_quorum_gap_discount: Decimal
    recency_gap_discount: Decimal
    independence_gap_discount: Decimal
    max_total_discount_before_block: Decimal
    min_adjusted_confidence: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationCounterEvidenceQuorumGateV2Config:
            raise ValueError(
                "config must be a StrategyRecommendationCounterEvidenceQuorumGateV2Config",
            )
        _require_text("config_version", self.config_version)
        for field_name in (
            "min_counter_evidence_family_count",
            "min_recent_family_count",
            "min_independent_source_count",
            "max_counter_evidence_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_source_independence_score",
            "family_quorum_gap_discount",
            "recency_gap_discount",
            "independence_gap_discount",
            "max_total_discount_before_block",
            "min_adjusted_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_flags("config", self)


@dataclass(frozen=True)
class StrategyRecommendationCounterEvidenceQuorumGateV2Recommendation:
    recommendation_id: str
    market_id: str
    recommendation_side: str
    base_confidence: Decimal
    recommended_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationCounterEvidenceQuorumGateV2Recommendation:
            raise ValueError(
                "recommendation must be a "
                "StrategyRecommendationCounterEvidenceQuorumGateV2Recommendation",
            )
        for field_name in ("recommendation_id", "market_id", "recommendation_side"):
            _require_text(field_name, getattr(self, field_name))
        if self.recommendation_side not in _SIDES:
            raise ValueError("recommendation_side must be yes or no")
        object.__setattr__(
            self,
            "base_confidence",
            _normalize_ratio("base_confidence", self.base_confidence),
        )
        object.__setattr__(
            self,
            "recommended_at",
            _as_utc("recommended_at", self.recommended_at),
        )
        _require_flags("recommendation", self)


@dataclass(frozen=True)
class StrategyRecommendationCounterEvidenceQuorumGateV2CounterEvidence:
    recommendation_id: str
    family_id: str
    source_id: str
    observed_at: datetime
    independence_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationCounterEvidenceQuorumGateV2CounterEvidence:
            raise ValueError(
                "counter evidence must be a "
                "StrategyRecommendationCounterEvidenceQuorumGateV2CounterEvidence",
            )
        for field_name in ("recommendation_id", "family_id", "source_id"):
            _require_text(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        object.__setattr__(
            self,
            "independence_score",
            _normalize_ratio("independence_score", self.independence_score),
        )
        _require_flags("counter evidence", self)


@dataclass(frozen=True)
class StrategyRecommendationCounterEvidenceQuorumGateV2Row:
    recommendation_id: str
    market_id: str
    recommendation_side: str
    base_confidence: Decimal
    adjusted_confidence: Decimal
    total_discount: Decimal
    family_count: Decimal
    recent_family_count: Decimal
    independent_source_count: Decimal
    average_independence_score: Decimal
    latest_counter_evidence_at: datetime | None
    latest_counter_evidence_age_seconds: Decimal | None
    gate_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationCounterEvidenceQuorumGateV2Row:
            raise ValueError("row must be a StrategyRecommendationCounterEvidenceQuorumGateV2Row")
        for field_name in ("recommendation_id", "market_id", "recommendation_side"):
            _require_text(field_name, getattr(self, field_name))
        if self.recommendation_side not in _SIDES:
            raise ValueError("recommendation_side must be yes or no")
        for field_name in (
            "base_confidence",
            "adjusted_confidence",
            "total_discount",
            "average_independence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "family_count",
            "recent_family_count",
            "independent_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.latest_counter_evidence_at is None:
            if self.latest_counter_evidence_age_seconds is not None:
                raise ValueError(
                    "latest_counter_evidence_age_seconds must be None without evidence",
                )
        else:
            object.__setattr__(
                self,
                "latest_counter_evidence_at",
                _as_utc("latest_counter_evidence_at", self.latest_counter_evidence_at),
            )
            if self.latest_counter_evidence_age_seconds is None:
                raise ValueError(
                    "latest_counter_evidence_age_seconds is required with evidence",
                )
            object.__setattr__(
                self,
                "latest_counter_evidence_age_seconds",
                _normalize_nonnegative_decimal(
                    "latest_counter_evidence_age_seconds",
                    self.latest_counter_evidence_age_seconds,
                ),
            )
        _require_status("gate_status", self.gate_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_flags("row", self)
        _check_row(self)


@dataclass(frozen=True)
class StrategyRecommendationCounterEvidenceQuorumGateV2Report:
    generated_at: datetime
    config_version: str
    recommendation_count: Decimal
    passed_count: Decimal
    discounted_count: Decimal
    blocked_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyRecommendationCounterEvidenceQuorumGateV2Row, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationCounterEvidenceQuorumGateV2Report:
            raise ValueError(
                "report must be a StrategyRecommendationCounterEvidenceQuorumGateV2Report",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_text("config_version", self.config_version)
        for field_name in (
            "recommendation_count",
            "passed_count",
            "discounted_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_flags("report", self)
        _check_report(self)


def build_strategy_recommendation_counter_evidence_quorum_gate_v2_report(
    recommendations: object,
    counter_evidence: object,
    *,
    config: StrategyRecommendationCounterEvidenceQuorumGateV2Config,
    generated_at: datetime,
) -> StrategyRecommendationCounterEvidenceQuorumGateV2Report:
    if type(config) is not StrategyRecommendationCounterEvidenceQuorumGateV2Config:
        raise ValueError(
            "config must be a StrategyRecommendationCounterEvidenceQuorumGateV2Config",
        )
    _require_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    recommendation_items = _normalize_recommendations(recommendations)
    evidence_items = _normalize_counter_evidence(
        counter_evidence,
        recommendation_ids=tuple(item.recommendation_id for item in recommendation_items),
    )
    for recommendation in recommendation_items:
        if recommendation.recommended_at > generated_at:
            raise ValueError("generated_at must not precede recommended_at")
    for evidence in evidence_items:
        if evidence.observed_at > generated_at:
            raise ValueError("generated_at must not precede observed_at")
    rows = tuple(
        sorted(
            (
                _row_for_recommendation(
                    recommendation,
                    tuple(
                        item
                        for item in evidence_items
                        if item.recommendation_id == recommendation.recommendation_id
                    ),
                    config=config,
                    generated_at=generated_at,
                )
                for recommendation in recommendation_items
            ),
            key=_row_sort_key,
        ),
    )
    return StrategyRecommendationCounterEvidenceQuorumGateV2Report(
        generated_at=generated_at,
        config_version=config.config_version,
        recommendation_count=_count(len(recommendation_items)),
        passed_count=_status_count(rows, "passed"),
        discounted_count=_status_count(rows, "discounted"),
        blocked_count=_status_count(rows, "blocked"),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def _row_for_recommendation(
    recommendation: StrategyRecommendationCounterEvidenceQuorumGateV2Recommendation,
    evidence_items: tuple[StrategyRecommendationCounterEvidenceQuorumGateV2CounterEvidence, ...],
    *,
    config: StrategyRecommendationCounterEvidenceQuorumGateV2Config,
    generated_at: datetime,
) -> StrategyRecommendationCounterEvidenceQuorumGateV2Row:
    family_count = _count(len({item.family_id for item in evidence_items}))
    recent_items = tuple(
        item
        for item in evidence_items
        if _age_seconds(generated_at, item.observed_at) <= config.max_counter_evidence_age_seconds
    )
    recent_family_count = _count(len({item.family_id for item in recent_items}))
    independent_recent_items = tuple(
        item
        for item in recent_items
        if item.independence_score >= config.min_source_independence_score
    )
    independent_source_count = _count(
        len({item.source_id for item in independent_recent_items}),
    )
    average_independence_score = _average(
        tuple(item.independence_score for item in recent_items),
    )
    latest_counter_evidence_at: datetime | None
    latest_counter_evidence_age_seconds: Decimal | None
    if evidence_items:
        latest_counter_evidence_at = max(item.observed_at for item in evidence_items)
        latest_counter_evidence_age_seconds = _age_seconds(
            generated_at,
            latest_counter_evidence_at,
        )
    else:
        latest_counter_evidence_at = None
        latest_counter_evidence_age_seconds = None

    family_gap = family_count < config.min_counter_evidence_family_count
    recency_gap = recent_family_count < config.min_recent_family_count
    independence_gap = (
        independent_source_count < config.min_independent_source_count
        or average_independence_score < config.min_source_independence_score
    )
    raw_discount = _raw_discount(
        family_gap=family_gap,
        recency_gap=recency_gap,
        independence_gap=independence_gap,
        config=config,
    )
    preblock_adjusted_confidence = _quantize(
        recommendation.base_confidence * (_ONE - _clamp_ratio(raw_discount)),
    )
    confidence_floor_gap = preblock_adjusted_confidence < config.min_adjusted_confidence
    is_blocked = (
        raw_discount > config.max_total_discount_before_block
        or confidence_floor_gap
    )
    if is_blocked:
        total_discount = _ONE
        adjusted_confidence = _ZERO
        gate_status = "blocked"
    else:
        total_discount = raw_discount
        adjusted_confidence = preblock_adjusted_confidence
        gate_status = "passed" if raw_discount == _ZERO else "discounted"
    return StrategyRecommendationCounterEvidenceQuorumGateV2Row(
        recommendation_id=recommendation.recommendation_id,
        market_id=recommendation.market_id,
        recommendation_side=recommendation.recommendation_side,
        base_confidence=recommendation.base_confidence,
        adjusted_confidence=adjusted_confidence,
        total_discount=total_discount,
        family_count=family_count,
        recent_family_count=recent_family_count,
        independent_source_count=independent_source_count,
        average_independence_score=average_independence_score,
        latest_counter_evidence_at=latest_counter_evidence_at,
        latest_counter_evidence_age_seconds=latest_counter_evidence_age_seconds,
        gate_status=gate_status,
        reason_codes=_row_reason_codes(
            gate_status=gate_status,
            family_gap=family_gap,
            recency_gap=recency_gap,
            independence_gap=independence_gap,
            confidence_floor_gap=confidence_floor_gap,
        ),
    )


def _raw_discount(
    *,
    family_gap: bool,
    recency_gap: bool,
    independence_gap: bool,
    config: StrategyRecommendationCounterEvidenceQuorumGateV2Config,
) -> Decimal:
    total = _ZERO
    if family_gap:
        total += config.family_quorum_gap_discount
    if recency_gap:
        total += config.recency_gap_discount
    if independence_gap:
        total += config.independence_gap_discount
    return _clamp_ratio(total)


def _row_reason_codes(
    *,
    gate_status: str,
    family_gap: bool,
    recency_gap: bool,
    independence_gap: bool,
    confidence_floor_gap: bool,
) -> tuple[str, ...]:
    if gate_status == "passed":
        return ("counter_evidence_quorum_met",)
    reasons: list[str] = [
        "counter_evidence_blocked"
        if gate_status == "blocked"
        else "counter_evidence_discounted",
    ]
    if confidence_floor_gap:
        reasons.append("counter_evidence_confidence_floor_gap")
    if family_gap:
        reasons.append("counter_evidence_family_quorum_gap")
    if independence_gap:
        reasons.append("counter_evidence_independence_gap")
    if recency_gap:
        reasons.append("counter_evidence_recency_gap")
    return _sort_reason_codes(tuple(reasons))


def _normalize_recommendations(
    recommendations: object,
) -> tuple[StrategyRecommendationCounterEvidenceQuorumGateV2Recommendation, ...]:
    if isinstance(recommendations, (str, bytes)):
        raise ValueError("recommendations must be an iterable")
    try:
        items = tuple(recommendations)
    except TypeError as exc:
        raise ValueError("recommendations must be an iterable") from exc
    seen: set[str] = set()
    for item in items:
        if type(item) is not StrategyRecommendationCounterEvidenceQuorumGateV2Recommendation:
            raise ValueError(
                "recommendations must contain "
                "StrategyRecommendationCounterEvidenceQuorumGateV2Recommendation",
            )
        _require_flags("recommendation", item)
        if item.recommendation_id in seen:
            raise ValueError("recommendations must not contain duplicate recommendation_id")
        seen.add(item.recommendation_id)
    return items


def _normalize_counter_evidence(
    counter_evidence: object,
    *,
    recommendation_ids: tuple[str, ...],
) -> tuple[StrategyRecommendationCounterEvidenceQuorumGateV2CounterEvidence, ...]:
    if isinstance(counter_evidence, (str, bytes)):
        raise ValueError("counter_evidence must be an iterable")
    try:
        items = tuple(counter_evidence)
    except TypeError as exc:
        raise ValueError("counter_evidence must be an iterable") from exc
    known = set(recommendation_ids)
    seen: set[tuple[str, str, str]] = set()
    for item in items:
        if type(item) is not StrategyRecommendationCounterEvidenceQuorumGateV2CounterEvidence:
            raise ValueError(
                "counter_evidence must contain "
                "StrategyRecommendationCounterEvidenceQuorumGateV2CounterEvidence",
            )
        _require_flags("counter evidence", item)
        if item.recommendation_id not in known:
            raise ValueError("counter_evidence references unknown recommendation")
        key = (item.recommendation_id, item.family_id, item.source_id)
        if key in seen:
            raise ValueError("counter_evidence must not contain duplicate family-source pairs")
        seen.add(key)
    return items


def _normalize_rows(
    rows: object,
) -> tuple[StrategyRecommendationCounterEvidenceQuorumGateV2Row, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        items = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for item in items:
        if type(item) is not StrategyRecommendationCounterEvidenceQuorumGateV2Row:
            raise ValueError("rows must contain StrategyRecommendationCounterEvidenceQuorumGateV2Row")
        _require_flags("row", item)
    if items != tuple(sorted(items, key=_row_sort_key)):
        raise ValueError("rows must be deterministically sorted")
    return items


def _row_sort_key(row: StrategyRecommendationCounterEvidenceQuorumGateV2Row) -> tuple[int, Decimal, str]:
    return (_STATUS_RANK[row.gate_status], -row.total_discount, row.recommendation_id)


def _status_count(
    rows: tuple[StrategyRecommendationCounterEvidenceQuorumGateV2Row, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.gate_status == status))


def _report_status(
    rows: tuple[StrategyRecommendationCounterEvidenceQuorumGateV2Row, ...],
) -> str:
    if any(row.gate_status == "blocked" for row in rows):
        return "blocked"
    if any(row.gate_status == "discounted" for row in rows):
        return "discounted"
    return "passed"


def _report_reason_codes(
    rows: tuple[StrategyRecommendationCounterEvidenceQuorumGateV2Row, ...],
) -> tuple[str, ...]:
    return _sort_reason_codes(
        tuple(dict.fromkeys(reason for row in rows for reason in row.reason_codes)),
    )


def _check_row(row: StrategyRecommendationCounterEvidenceQuorumGateV2Row) -> None:
    expected_reason = {
        "blocked": "counter_evidence_blocked",
        "discounted": "counter_evidence_discounted",
        "passed": "counter_evidence_quorum_met",
    }[row.gate_status]
    if expected_reason not in row.reason_codes:
        raise ValueError("reason_codes must include gate status reason")
    if row.gate_status == "passed" and row.total_discount != _ZERO:
        raise ValueError("passed rows must not have a discount")
    if row.gate_status == "blocked" and row.adjusted_confidence != _ZERO:
        raise ValueError("blocked rows must have zero adjusted confidence")


def _check_report(report: StrategyRecommendationCounterEvidenceQuorumGateV2Report) -> None:
    rows = report.rows
    if report.recommendation_count != _count(len(rows)):
        raise ValueError("recommendation_count must match rows")
    if report.passed_count != _status_count(rows, "passed"):
        raise ValueError("passed_count must match rows")
    if report.discounted_count != _status_count(rows, "discounted"):
        raise ValueError("discounted_count must match rows")
    if report.blocked_count != _status_count(rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    if delta.days < 0:
        raise ValueError("observed_at must not be in the future")
    total = (
        Decimal(delta.days) * _SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + Decimal(delta.microseconds) / _MICROS_PER_SECOND
    )
    return _quantize(total)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _clamp_ratio(value: Decimal) -> Decimal:
    value = _quantize(value)
    if value < _ZERO:
        return _ZERO
    if value > _ONE:
        return _ONE
    return value


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _normalize_ratio(field_name: str, value: Any) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize(value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_positive_decimal(field_name: str, value: Any) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: Any) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize(value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_reason_codes(field_name: str, reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of reason codes")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of reason codes") from exc
    if not normalized:
        raise ValueError(f"{field_name} must contain at least one reason code")
    for reason_code in normalized:
        _require_reason_code(field_name, reason_code)
    if normalized != _sort_reason_codes(normalized):
        raise ValueError(f"{field_name} must be sorted")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    return normalized


def _sort_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    unique = tuple(dict.fromkeys(reason_codes))
    for reason_code in unique:
        _require_reason_code("reason_codes", reason_code)
    return tuple(sorted(unique, key=lambda item: (_REASON_RANK[item], item)))


def _require_reason_code(field_name: str, value: Any) -> None:
    _require_text(field_name, value)
    if value not in _REASON_CODES:
        raise ValueError(f"{field_name} must contain known reason codes")


def _require_status(field_name: str, value: Any) -> None:
    _require_text(field_name, value)
    if value not in _STATUSES:
        raise ValueError(f"{field_name} must be a known status")


def _as_utc(field_name: str, value: Any) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_text(field_name: str, value: Any) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_flags(field_name: str, value: Any) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")
