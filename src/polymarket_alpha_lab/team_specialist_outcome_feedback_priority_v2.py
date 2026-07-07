"""Phase 1 readonly priority report for resolved outcome feedback."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json


DEFAULT_TEAM_SPECIALIST_OUTCOME_FEEDBACK_PRIORITY_V2_CONFIG_VERSION = (
    "team-specialist-outcome-feedback-priority-v2"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SCORE_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")

PRIORITY_TIERS = ("high", "medium", "low")
REPORT_STATUSES = ("high", "watch", "blocked")
ROW_REASON_CODES = (
    "priority_high",
    "priority_medium",
    "priority_low",
    "forecast_error_high",
    "forecast_error_medium",
    "forecast_error_low",
    "confidence_gap_high",
    "confidence_gap_medium",
    "confidence_gap_low",
    "category_importance_high",
    "category_importance_medium",
    "category_importance_low",
    "source_contradiction_high",
    "source_contradiction_medium",
    "source_contradiction_low",
    "resolution_ambiguity_high",
    "resolution_ambiguity_medium",
    "resolution_ambiguity_low",
    "recency_current",
    "recency_aging",
    "recency_stale",
)
REPORT_REASON_CODES = (
    "outcome_feedback_priority_high_rows",
    "outcome_feedback_priority_medium_rows",
    "outcome_feedback_priority_low_rows",
    "outcome_feedback_priority_empty",
)
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
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

__all__ = (
    "DEFAULT_TEAM_SPECIALIST_OUTCOME_FEEDBACK_PRIORITY_V2_CONFIG_VERSION",
    "TeamSpecialistOutcomeFeedbackPriorityV2Config",
    "TeamSpecialistOutcomeFeedbackPriorityV2Input",
    "TeamSpecialistOutcomeFeedbackPriorityV2Row",
    "TeamSpecialistOutcomeFeedbackPriorityV2Report",
    "build_team_specialist_outcome_feedback_priority_v2",
)


@dataclass(frozen=True)
class TeamSpecialistOutcomeFeedbackPriorityV2Config:
    config_version: str = (
        DEFAULT_TEAM_SPECIALIST_OUTCOME_FEEDBACK_PRIORITY_V2_CONFIG_VERSION
    )
    forecast_error_weight: Decimal = Decimal("0.300000")
    confidence_gap_weight: Decimal = Decimal("0.200000")
    category_importance_weight: Decimal = Decimal("0.150000")
    source_contradiction_weight: Decimal = Decimal("0.150000")
    resolution_ambiguity_weight: Decimal = Decimal("0.100000")
    recency_weight: Decimal = Decimal("0.100000")
    max_recency_age_seconds: Decimal = Decimal("86400.000000")
    high_priority_floor: Decimal = Decimal("0.700000")
    medium_priority_floor: Decimal = Decimal("0.400000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "config_version",
            _require_non_empty_string("config_version", self.config_version),
        )
        for field_name in (
            "forecast_error_weight",
            "confidence_gap_weight",
            "category_importance_weight",
            "source_contradiction_weight",
            "resolution_ambiguity_weight",
            "recency_weight",
            "high_priority_floor",
            "medium_priority_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_recency_age_seconds",
            _normalize_positive_decimal(
                "max_recency_age_seconds",
                self.max_recency_age_seconds,
            ),
        )
        _validate_config(self)
        _require_hard_flags("TeamSpecialistOutcomeFeedbackPriorityV2Config", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistOutcomeFeedbackPriorityV2Config",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistOutcomeFeedbackPriorityV2Input:
    team_id: str
    specialist_id: str
    category_id: str
    market_id: str
    outcome_id: str
    forecast_probability: Decimal
    resolved_probability: Decimal
    confidence_score: Decimal
    category_importance_score: Decimal
    source_contradiction_score: Decimal
    resolution_ambiguity_score: Decimal
    resolved_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "team_id",
            "specialist_id",
            "category_id",
            "market_id",
            "outcome_id",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_non_empty_string(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "forecast_probability",
            "resolved_probability",
            "confidence_score",
            "category_importance_score",
            "source_contradiction_score",
            "resolution_ambiguity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "resolved_at", _as_utc("resolved_at", self.resolved_at))
        _require_hard_flags("TeamSpecialistOutcomeFeedbackPriorityV2Input", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistOutcomeFeedbackPriorityV2Input",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistOutcomeFeedbackPriorityV2Row:
    rank: Decimal
    team_id: str
    specialist_id: str
    category_id: str
    market_id: str
    outcome_id: str
    forecast_probability: Decimal
    resolved_probability: Decimal
    forecast_error_score: Decimal
    confidence_score: Decimal
    confidence_gap_score: Decimal
    category_importance_score: Decimal
    source_contradiction_score: Decimal
    resolution_ambiguity_score: Decimal
    recency_score: Decimal
    outcome_age_seconds: Decimal
    priority_score: Decimal
    priority_tier: str
    reason_codes: tuple[str, ...]
    row_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "rank",
            _normalize_positive_integral_decimal("rank", self.rank),
        )
        for field_name in (
            "team_id",
            "specialist_id",
            "category_id",
            "market_id",
            "outcome_id",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_non_empty_string(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "forecast_probability",
            "resolved_probability",
            "forecast_error_score",
            "confidence_score",
            "confidence_gap_score",
            "category_importance_score",
            "source_contradiction_score",
            "resolution_ambiguity_score",
            "recency_score",
            "priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "outcome_age_seconds",
            _normalize_nonnegative_decimal(
                "outcome_age_seconds",
                self.outcome_age_seconds,
            ),
        )
        _require_priority_tier("priority_tier", self.priority_tier)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_sha256_digest("row_digest", self.row_digest)
        _require_hard_flags("TeamSpecialistOutcomeFeedbackPriorityV2Row", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistOutcomeFeedbackPriorityV2Row",
            _payload_value(asdict(self)),
        )
        _validate_row_consistency(self)
        if self.row_digest != _row_digest_from_values(asdict(self)):
            raise ValueError("row_digest must match row fields")


@dataclass(frozen=True)
class TeamSpecialistOutcomeFeedbackPriorityV2Report:
    generated_at: datetime
    config_version: str
    priority_status: str
    item_count: Decimal
    high_priority_count: Decimal
    medium_priority_count: Decimal
    low_priority_count: Decimal
    average_priority_score: Decimal
    top_priority_score: Decimal
    bottom_priority_score: Decimal
    rows: tuple[TeamSpecialistOutcomeFeedbackPriorityV2Row, ...]
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
        _require_report_status("priority_status", self.priority_status)
        for field_name in (
            "item_count",
            "high_priority_count",
            "medium_priority_count",
            "low_priority_count",
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
            "average_priority_score",
            "top_priority_score",
            "bottom_priority_score",
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
        _require_hard_flags("TeamSpecialistOutcomeFeedbackPriorityV2Report", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistOutcomeFeedbackPriorityV2Report",
            _payload_value(asdict(self)),
        )
        _validate_report_consistency(self)

    @property
    def payload(self) -> dict[str, object]:
        payload = _payload_value(asdict(self))
        _reject_unsafe_public_payload(
            "TeamSpecialistOutcomeFeedbackPriorityV2Report.payload",
            payload,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_team_specialist_outcome_feedback_priority_v2(
    outcome_items: object,
    *,
    config: TeamSpecialistOutcomeFeedbackPriorityV2Config | None = None,
    generated_at: datetime,
) -> TeamSpecialistOutcomeFeedbackPriorityV2Report:
    if config is None:
        config = TeamSpecialistOutcomeFeedbackPriorityV2Config()
    if type(config) is not TeamSpecialistOutcomeFeedbackPriorityV2Config:
        raise ValueError(
            "config must be a TeamSpecialistOutcomeFeedbackPriorityV2Config",
        )
    _require_hard_flags("TeamSpecialistOutcomeFeedbackPriorityV2Config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    items = _normalize_outcome_items(outcome_items)
    for item in items:
        if item.resolved_at > generated_at_utc:
            raise ValueError("resolved_at must not be after generated_at")
    rows = tuple(
        _row_for_item(
            rank=Decimal(index).quantize(COUNT_QUANT),
            item=item,
            config=config,
            generated_at=generated_at_utc,
        )
        for index, item in enumerate(
            _sorted_items(items, generated_at_utc, config),
            start=1,
        )
    )
    status = _report_status(rows)
    values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "priority_status": status,
        "item_count": Decimal(len(rows)).quantize(COUNT_QUANT),
        "high_priority_count": _tier_count(rows, "high"),
        "medium_priority_count": _tier_count(rows, "medium"),
        "low_priority_count": _tier_count(rows, "low"),
        "average_priority_score": _average_score(rows),
        "top_priority_score": _top_score(rows),
        "bottom_priority_score": _bottom_score(rows),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["derived_validation_digest"] = _report_digest_from_values(values)
    return TeamSpecialistOutcomeFeedbackPriorityV2Report(**values)


def _sorted_items(
    items: tuple[TeamSpecialistOutcomeFeedbackPriorityV2Input, ...],
    generated_at: datetime,
    config: TeamSpecialistOutcomeFeedbackPriorityV2Config,
) -> tuple[TeamSpecialistOutcomeFeedbackPriorityV2Input, ...]:
    return tuple(
        sorted(
            items,
            key=lambda item: (
                -_priority_score(item, generated_at, config),
                item.team_id,
                item.specialist_id,
                item.category_id,
                item.market_id,
                item.outcome_id,
            ),
        ),
    )


def _row_for_item(
    *,
    rank: Decimal,
    item: TeamSpecialistOutcomeFeedbackPriorityV2Input,
    config: TeamSpecialistOutcomeFeedbackPriorityV2Config,
    generated_at: datetime,
) -> TeamSpecialistOutcomeFeedbackPriorityV2Row:
    forecast_error_score = _forecast_error_score(item)
    confidence_gap_score = _confidence_gap_score(item, forecast_error_score)
    outcome_age_seconds = _age_seconds(generated_at, item.resolved_at)
    recency_score = _recency_score(outcome_age_seconds, config.max_recency_age_seconds)
    priority_score = _score_from_components(
        forecast_error_score=forecast_error_score,
        confidence_gap_score=confidence_gap_score,
        category_importance_score=item.category_importance_score,
        source_contradiction_score=item.source_contradiction_score,
        resolution_ambiguity_score=item.resolution_ambiguity_score,
        recency_score=recency_score,
        config=config,
    )
    priority_tier = _priority_tier(priority_score, config)
    values = {
        "rank": rank,
        "team_id": item.team_id,
        "specialist_id": item.specialist_id,
        "category_id": item.category_id,
        "market_id": item.market_id,
        "outcome_id": item.outcome_id,
        "forecast_probability": item.forecast_probability,
        "resolved_probability": item.resolved_probability,
        "forecast_error_score": forecast_error_score,
        "confidence_score": item.confidence_score,
        "confidence_gap_score": confidence_gap_score,
        "category_importance_score": item.category_importance_score,
        "source_contradiction_score": item.source_contradiction_score,
        "resolution_ambiguity_score": item.resolution_ambiguity_score,
        "recency_score": recency_score,
        "outcome_age_seconds": outcome_age_seconds,
        "priority_score": priority_score,
        "priority_tier": priority_tier,
        "reason_codes": _row_reason_codes(
            forecast_error_score=forecast_error_score,
            confidence_gap_score=confidence_gap_score,
            category_importance_score=item.category_importance_score,
            source_contradiction_score=item.source_contradiction_score,
            resolution_ambiguity_score=item.resolution_ambiguity_score,
            recency_score=recency_score,
            priority_tier=priority_tier,
        ),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["row_digest"] = _row_digest_from_values(values)
    return TeamSpecialistOutcomeFeedbackPriorityV2Row(**values)


def _priority_score(
    item: TeamSpecialistOutcomeFeedbackPriorityV2Input,
    generated_at: datetime,
    config: TeamSpecialistOutcomeFeedbackPriorityV2Config,
) -> Decimal:
    forecast_error_score = _forecast_error_score(item)
    confidence_gap_score = _confidence_gap_score(item, forecast_error_score)
    outcome_age_seconds = _age_seconds(generated_at, item.resolved_at)
    recency_score = _recency_score(outcome_age_seconds, config.max_recency_age_seconds)
    return _score_from_components(
        forecast_error_score=forecast_error_score,
        confidence_gap_score=confidence_gap_score,
        category_importance_score=item.category_importance_score,
        source_contradiction_score=item.source_contradiction_score,
        resolution_ambiguity_score=item.resolution_ambiguity_score,
        recency_score=recency_score,
        config=config,
    )


def _score_from_components(
    *,
    forecast_error_score: Decimal,
    confidence_gap_score: Decimal,
    category_importance_score: Decimal,
    source_contradiction_score: Decimal,
    resolution_ambiguity_score: Decimal,
    recency_score: Decimal,
    config: TeamSpecialistOutcomeFeedbackPriorityV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            forecast_error_score * config.forecast_error_weight
            + confidence_gap_score * config.confidence_gap_weight
            + category_importance_score * config.category_importance_weight
            + source_contradiction_score * config.source_contradiction_weight
            + resolution_ambiguity_score * config.resolution_ambiguity_weight
            + recency_score * config.recency_weight
        )
        return _clamp_ratio(score)


def _forecast_error_score(item: TeamSpecialistOutcomeFeedbackPriorityV2Input) -> Decimal:
    return _clamp_ratio(abs(item.forecast_probability - item.resolved_probability))


def _confidence_gap_score(
    item: TeamSpecialistOutcomeFeedbackPriorityV2Input,
    forecast_error_score: Decimal,
) -> Decimal:
    forecast_accuracy_score = _clamp_ratio(ONE - forecast_error_score)
    return _clamp_ratio(abs(item.confidence_score - forecast_accuracy_score))


def _recency_score(age_seconds: Decimal, max_age_seconds: Decimal) -> Decimal:
    if age_seconds >= max_age_seconds:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(ONE - age_seconds / max_age_seconds)


def _priority_tier(
    score: Decimal,
    config: TeamSpecialistOutcomeFeedbackPriorityV2Config,
) -> str:
    if score >= config.high_priority_floor:
        return "high"
    if score >= config.medium_priority_floor:
        return "medium"
    return "low"


def _row_reason_codes(
    *,
    forecast_error_score: Decimal,
    confidence_gap_score: Decimal,
    category_importance_score: Decimal,
    source_contradiction_score: Decimal,
    resolution_ambiguity_score: Decimal,
    recency_score: Decimal,
    priority_tier: str,
) -> tuple[str, ...]:
    return (
        f"priority_{priority_tier}",
        _tier_reason(
            forecast_error_score,
            high=Decimal("0.500000"),
            medium=Decimal("0.200000"),
            high_reason="forecast_error_high",
            medium_reason="forecast_error_medium",
            low_reason="forecast_error_low",
        ),
        _tier_reason(
            confidence_gap_score,
            high=Decimal("0.500000"),
            medium=Decimal("0.200000"),
            high_reason="confidence_gap_high",
            medium_reason="confidence_gap_medium",
            low_reason="confidence_gap_low",
        ),
        _tier_reason(
            category_importance_score,
            high=Decimal("0.750000"),
            medium=Decimal("0.400000"),
            high_reason="category_importance_high",
            medium_reason="category_importance_medium",
            low_reason="category_importance_low",
        ),
        _tier_reason(
            source_contradiction_score,
            high=Decimal("0.500000"),
            medium=Decimal("0.100000"),
            high_reason="source_contradiction_high",
            medium_reason="source_contradiction_medium",
            low_reason="source_contradiction_low",
        ),
        _tier_reason(
            resolution_ambiguity_score,
            high=Decimal("0.500000"),
            medium=Decimal("0.200000"),
            high_reason="resolution_ambiguity_high",
            medium_reason="resolution_ambiguity_medium",
            low_reason="resolution_ambiguity_low",
        ),
        _tier_reason(
            recency_score,
            high=Decimal("0.750000"),
            medium=Decimal("0.250000"),
            high_reason="recency_current",
            medium_reason="recency_aging",
            low_reason="recency_stale",
        ),
    )


def _tier_reason(
    value: Decimal,
    *,
    high: Decimal,
    medium: Decimal,
    high_reason: str,
    medium_reason: str,
    low_reason: str,
) -> str:
    if value >= high:
        return high_reason
    if value >= medium:
        return medium_reason
    return low_reason


def _report_status(
    rows: tuple[TeamSpecialistOutcomeFeedbackPriorityV2Row, ...],
) -> str:
    if not rows:
        return "blocked"
    if any(row.priority_tier == "high" for row in rows):
        return "high"
    if any(row.priority_tier == "medium" for row in rows):
        return "watch"
    return "blocked"


def _report_reason_codes(
    rows: tuple[TeamSpecialistOutcomeFeedbackPriorityV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("outcome_feedback_priority_empty",)
    reasons: list[str] = []
    if any(row.priority_tier == "high" for row in rows):
        reasons.append("outcome_feedback_priority_high_rows")
    if any(row.priority_tier == "medium" for row in rows):
        reasons.append("outcome_feedback_priority_medium_rows")
    if any(row.priority_tier == "low" for row in rows):
        reasons.append("outcome_feedback_priority_low_rows")
    return tuple(reasons)


def _tier_count(
    rows: tuple[TeamSpecialistOutcomeFeedbackPriorityV2Row, ...],
    tier: str,
) -> Decimal:
    return Decimal(sum(1 for row in rows if row.priority_tier == tier)).quantize(
        COUNT_QUANT,
    )


def _average_score(
    rows: tuple[TeamSpecialistOutcomeFeedbackPriorityV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(sum(row.priority_score for row in rows) / Decimal(len(rows)))


def _top_score(rows: tuple[TeamSpecialistOutcomeFeedbackPriorityV2Row, ...]) -> Decimal:
    if not rows:
        return ZERO
    return max(row.priority_score for row in rows)


def _bottom_score(rows: tuple[TeamSpecialistOutcomeFeedbackPriorityV2Row, ...]) -> Decimal:
    if not rows:
        return ZERO
    return min(row.priority_score for row in rows)


def _normalize_outcome_items(
    value: object,
) -> tuple[TeamSpecialistOutcomeFeedbackPriorityV2Input, ...]:
    if isinstance(value, (str, bytes)) or not hasattr(value, "__iter__"):
        raise ValueError("outcome_items must be an iterable")
    items = tuple(value)
    for item in items:
        if type(item) is not TeamSpecialistOutcomeFeedbackPriorityV2Input:
            raise ValueError(
                "outcome items must be TeamSpecialistOutcomeFeedbackPriorityV2Input",
            )
        _require_hard_flags("TeamSpecialistOutcomeFeedbackPriorityV2Input", item)
    keys = tuple(
        (
            item.team_id,
            item.specialist_id,
            item.category_id,
            item.market_id,
            item.outcome_id,
        )
        for item in items
    )
    if len(set(keys)) != len(keys):
        raise ValueError("outcome items must not contain duplicate identities")
    return items


def _normalize_rows(value: object) -> tuple[TeamSpecialistOutcomeFeedbackPriorityV2Row, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in value:
        if type(row) is not TeamSpecialistOutcomeFeedbackPriorityV2Row:
            raise ValueError(
                "rows must contain TeamSpecialistOutcomeFeedbackPriorityV2Row",
            )
    return value


def _validate_config(config: TeamSpecialistOutcomeFeedbackPriorityV2Config) -> None:
    with localcontext(DECIMAL_CONTEXT):
        weights_total = (
            config.forecast_error_weight
            + config.confidence_gap_weight
            + config.category_importance_weight
            + config.source_contradiction_weight
            + config.resolution_ambiguity_weight
            + config.recency_weight
        ).quantize(SCORE_QUANT)
    if weights_total != ONE:
        raise ValueError("priority weights must sum to 1.000000")
    if config.medium_priority_floor > config.high_priority_floor:
        raise ValueError("medium_priority_floor must not exceed high_priority_floor")


def _validate_row_consistency(row: TeamSpecialistOutcomeFeedbackPriorityV2Row) -> None:
    if row.forecast_error_score != _clamp_ratio(
        abs(row.forecast_probability - row.resolved_probability),
    ):
        raise ValueError("forecast_error_score must match forecast and resolved")
    if row.confidence_gap_score != _confidence_gap_from_values(
        row.confidence_score,
        row.forecast_error_score,
    ):
        raise ValueError("confidence_gap_score must match confidence and forecast error")
    if f"priority_{row.priority_tier}" not in row.reason_codes:
        raise ValueError("reason_codes must include priority tier")


def _validate_report_consistency(
    report: TeamSpecialistOutcomeFeedbackPriorityV2Report,
) -> None:
    rows = report.rows
    if report.item_count != Decimal(len(rows)).quantize(COUNT_QUANT):
        raise ValueError("item_count must match rows")
    if (
        report.high_priority_count != _tier_count(rows, "high")
        or report.medium_priority_count != _tier_count(rows, "medium")
        or report.low_priority_count != _tier_count(rows, "low")
    ):
        raise ValueError("priority counts must match rows")
    if (
        report.high_priority_count
        + report.medium_priority_count
        + report.low_priority_count
        != report.item_count
    ):
        raise ValueError("priority counts must sum to item_count")
    _validate_rows_sorted(rows)
    expected_status = _report_status(rows)
    if report.priority_status != expected_status:
        raise ValueError("priority_status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match priority_status")
    if report.derived_validation_digest != _report_digest_from_values(asdict(report)):
        raise ValueError("derived_validation_digest must match report fields")
    if report.average_priority_score != _average_score(rows):
        raise ValueError("average_priority_score must match rows")
    if report.top_priority_score != _top_score(rows):
        raise ValueError("top_priority_score must match rows")
    if report.bottom_priority_score != _bottom_score(rows):
        raise ValueError("bottom_priority_score must match rows")


def _validate_rows_sorted(
    rows: tuple[TeamSpecialistOutcomeFeedbackPriorityV2Row, ...],
) -> None:
    expected = tuple(
        sorted(
            rows,
            key=lambda row: (
                -row.priority_score,
                row.team_id,
                row.specialist_id,
                row.category_id,
                row.market_id,
                row.outcome_id,
            ),
        ),
    )
    expected_ranks = tuple(
        Decimal(index).quantize(COUNT_QUANT) for index in range(1, len(rows) + 1)
    )
    actual_ranks = tuple(row.rank for row in rows)
    if rows != expected or actual_ranks != expected_ranks:
        raise ValueError("rows must be sorted by priority score and rank")


def _confidence_gap_from_values(
    confidence_score: Decimal,
    forecast_error_score: Decimal,
) -> Decimal:
    forecast_accuracy_score = _clamp_ratio(ONE - forecast_error_score)
    return _clamp_ratio(abs(confidence_score - forecast_accuracy_score))


def _age_seconds(generated_at: datetime, resolved_at: datetime) -> Decimal:
    delta = generated_at - resolved_at
    whole_seconds = delta.days * 86400 + delta.seconds
    total_microseconds = whole_seconds * 1000000 + delta.microseconds
    if total_microseconds < 0:
        raise ValueError("resolved_at must not be after generated_at")
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_nonnegative_decimal(
            "outcome_age_seconds",
            Decimal(total_microseconds) / MICROSECONDS_PER_SECOND,
        )


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_non_empty_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    normalized = value.strip()
    _reject_unsafe_public_payload(field_name, normalized)
    return normalized


def _require_priority_tier(field_name: str, value: object) -> None:
    _require_non_empty_string(field_name, value)
    if value not in PRIORITY_TIERS:
        raise ValueError(f"{field_name} must be high, medium, or low")


def _require_report_status(field_name: str, value: object) -> None:
    _require_non_empty_string(field_name, value)
    if value not in REPORT_STATUSES:
        raise ValueError(f"{field_name} must be high, watch, or blocked")


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    normalized = tuple(_require_non_empty_string(field_name, item) for item in value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    if any(item not in allowed for item in normalized):
        raise ValueError(f"{field_name} must contain known reason codes")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if value > ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(SCORE_QUANT)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(SCORE_QUANT)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    value = _normalize_nonnegative_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _normalize_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return value.quantize(COUNT_QUANT)


def _normalize_positive_integral_decimal(field_name: str, value: object) -> Decimal:
    value = _normalize_nonnegative_integral_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _clamp_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return min(ONE, max(ZERO, value)).quantize(SCORE_QUANT)


def _require_sha256_digest(field_name: str, value: object) -> None:
    _require_non_empty_string(field_name, value)
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {field_name}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {field_name}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {field_name}")


def _payload_value(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is dict:
        return {key: _payload_value(item) for key, item in value.items()}
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if value is None or type(value) in (str, bool):
        return value
    if type(value) in (int, float):
        raise ValueError("payload numeric values must be Decimal")
    raise ValueError("payload contains unsupported value")


def _row_digest_from_values(values: dict[str, object]) -> str:
    return _digest_from_values(values, "row_digest")


def _report_digest_from_values(values: dict[str, object]) -> str:
    return _digest_from_values(values, "derived_validation_digest")


def _digest_from_values(values: dict[str, object], digest_field: str) -> str:
    digest_payload = {
        key: _payload_value(item) for key, item in values.items() if key != digest_field
    }
    _reject_unsafe_public_payload("validation digest payload", digest_payload)
    encoded = json.dumps(
        digest_payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_text(label, field.name)
            item = getattr(value, field.name)
            if field.name in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"unsafe public payload in {label}")
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public payload in {label}")
            _reject_unsafe_public_text(label, key)
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"unsafe public payload in {label}")
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is bool or value is None:
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"unsafe public payload in {label}")
        return
    if type(value) in (int, float):
        raise ValueError(f"unsafe public payload in {label}")
    if type(value) is str:
        _reject_unsafe_public_text(label, value)
        return
    if type(value) is datetime:
        _as_utc("public payload datetime", value)
        return
    raise ValueError(f"unsafe public payload in {label}")


def _reject_unsafe_public_text(label: str, value: str) -> None:
    normalized = value.lower()
    if value.strip() != value:
        raise ValueError(f"unsafe public payload in {label}")
    if "://" in normalized or "?" in normalized:
        raise ValueError(f"unsafe public payload in {label}")
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"unsafe public payload in {label}")
