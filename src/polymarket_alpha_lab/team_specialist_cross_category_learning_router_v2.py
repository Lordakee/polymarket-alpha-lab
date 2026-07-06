"""Readonly Decimal router for cross-category specialist learning transfer."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json


DEFAULT_TEAM_SPECIALIST_CROSS_CATEGORY_LEARNING_ROUTER_V2_CONFIG_VERSION = (
    "team-specialist-cross-category-learning-router-v2"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SCORE_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

ROUTE_STATUSES = ("route", "watch", "blocked")
ROUTER_STATUSES = ("route", "watch", "blocked")
ROW_REASON_CODES = (
    "cross_category_learning_route",
    "cross_category_learning_watch",
    "cross_category_learning_blocked",
    "specialist_fit_strong",
    "specialist_fit_watch",
    "specialist_fit_weak",
    "category_overlap_strong",
    "category_overlap_watch",
    "category_overlap_weak",
    "transfer_signal_strong",
    "transfer_signal_watch",
    "transfer_signal_weak",
    "evidence_quality_strong",
    "evidence_quality_watch",
    "evidence_quality_weak",
    "stale_memory_fresh",
    "stale_memory_watch",
    "stale_memory_stale",
)
REPORT_REASON_CODES = (
    "cross_category_learning_router_routed",
    "cross_category_learning_router_watch_rows",
    "cross_category_learning_router_blocked_rows",
    "cross_category_learning_router_empty",
)
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
    "DEFAULT_TEAM_SPECIALIST_CROSS_CATEGORY_LEARNING_ROUTER_V2_CONFIG_VERSION",
    "TeamSpecialistCrossCategoryLearningRouterV2Config",
    "TeamSpecialistCrossCategoryLearningRouterV2Input",
    "TeamSpecialistCrossCategoryLearningRouterV2Row",
    "TeamSpecialistCrossCategoryLearningRouterV2Report",
    "build_team_specialist_cross_category_learning_router_v2",
)


@dataclass(frozen=True)
class TeamSpecialistCrossCategoryLearningRouterV2Config:
    config_version: str = (
        DEFAULT_TEAM_SPECIALIST_CROSS_CATEGORY_LEARNING_ROUTER_V2_CONFIG_VERSION
    )
    specialist_fit_weight: Decimal = Decimal("0.350000")
    category_overlap_weight: Decimal = Decimal("0.250000")
    transfer_signal_weight: Decimal = Decimal("0.250000")
    evidence_quality_weight: Decimal = Decimal("0.150000")
    stale_memory_penalty_weight: Decimal = Decimal("0.250000")
    max_stale_memory_days: Decimal = Decimal("30")
    route_score_floor: Decimal = Decimal("0.800000")
    watch_score_floor: Decimal = Decimal("0.500000")
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
            "specialist_fit_weight",
            "category_overlap_weight",
            "transfer_signal_weight",
            "evidence_quality_weight",
            "stale_memory_penalty_weight",
            "route_score_floor",
            "watch_score_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_stale_memory_days",
            _normalize_positive_integral_decimal(
                "max_stale_memory_days",
                self.max_stale_memory_days,
            ),
        )
        _validate_config(self)
        _require_hard_flags("TeamSpecialistCrossCategoryLearningRouterV2Config", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistCrossCategoryLearningRouterV2Config",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistCrossCategoryLearningRouterV2Input:
    specialist_id: str
    source_category_id: str
    target_category_id: str
    specialist_fit_score: Decimal
    category_overlap_score: Decimal
    transfer_signal_score: Decimal
    evidence_quality_score: Decimal
    stale_memory_days: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "specialist_id",
            _require_non_empty_string("specialist_id", self.specialist_id),
        )
        object.__setattr__(
            self,
            "source_category_id",
            _require_non_empty_string("source_category_id", self.source_category_id),
        )
        object.__setattr__(
            self,
            "target_category_id",
            _require_non_empty_string("target_category_id", self.target_category_id),
        )
        if self.source_category_id == self.target_category_id:
            raise ValueError("source_category_id must differ from target_category_id")
        for field_name in (
            "specialist_fit_score",
            "category_overlap_score",
            "transfer_signal_score",
            "evidence_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "stale_memory_days",
            _normalize_nonnegative_integral_decimal(
                "stale_memory_days",
                self.stale_memory_days,
            ),
        )
        _require_hard_flags("TeamSpecialistCrossCategoryLearningRouterV2Input", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistCrossCategoryLearningRouterV2Input",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistCrossCategoryLearningRouterV2Row:
    rank: Decimal
    specialist_id: str
    source_category_id: str
    target_category_id: str
    category_pair_id: str
    specialist_fit_score: Decimal
    category_overlap_score: Decimal
    transfer_signal_score: Decimal
    evidence_quality_score: Decimal
    stale_memory_days: Decimal
    stale_memory_penalty: Decimal
    learning_route_score: Decimal
    route_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "rank",
            _normalize_positive_integral_decimal("rank", self.rank),
        )
        object.__setattr__(
            self,
            "specialist_id",
            _require_non_empty_string("specialist_id", self.specialist_id),
        )
        object.__setattr__(
            self,
            "source_category_id",
            _require_non_empty_string("source_category_id", self.source_category_id),
        )
        object.__setattr__(
            self,
            "target_category_id",
            _require_non_empty_string("target_category_id", self.target_category_id),
        )
        if self.source_category_id == self.target_category_id:
            raise ValueError("source_category_id must differ from target_category_id")
        object.__setattr__(
            self,
            "category_pair_id",
            _require_non_empty_string("category_pair_id", self.category_pair_id),
        )
        for field_name in (
            "specialist_fit_score",
            "category_overlap_score",
            "transfer_signal_score",
            "evidence_quality_score",
            "stale_memory_penalty",
            "learning_route_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "stale_memory_days",
            _normalize_nonnegative_integral_decimal(
                "stale_memory_days",
                self.stale_memory_days,
            ),
        )
        _require_route_status("route_status", self.route_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("TeamSpecialistCrossCategoryLearningRouterV2Row", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistCrossCategoryLearningRouterV2Row",
            _payload_value(asdict(self)),
        )
        _validate_row_consistency(self)


@dataclass(frozen=True)
class TeamSpecialistCrossCategoryLearningRouterV2Report:
    generated_at: datetime
    config_version: str
    router_status: str
    candidate_count: Decimal
    route_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    average_learning_route_score: Decimal
    top_learning_route_score: Decimal
    bottom_learning_route_score: Decimal
    rows: tuple[TeamSpecialistCrossCategoryLearningRouterV2Row, ...]
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
        _require_router_status("router_status", self.router_status)
        for field_name in (
            "candidate_count",
            "route_count",
            "watch_count",
            "blocked_count",
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
            "average_learning_route_score",
            "top_learning_route_score",
            "bottom_learning_route_score",
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
        _require_sha256_digest(
            "derived_validation_digest",
            self.derived_validation_digest,
        )
        _require_hard_flags("TeamSpecialistCrossCategoryLearningRouterV2Report", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistCrossCategoryLearningRouterV2Report",
            _payload_value(asdict(self)),
        )
        _validate_report_consistency(self)

    @property
    def payload(self) -> dict[str, object]:
        payload = _payload_value(asdict(self))
        _reject_unsafe_public_payload(
            "TeamSpecialistCrossCategoryLearningRouterV2Report.payload",
            payload,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_team_specialist_cross_category_learning_router_v2(
    learning_candidates: object,
    *,
    config: TeamSpecialistCrossCategoryLearningRouterV2Config | None = None,
    generated_at: datetime,
) -> TeamSpecialistCrossCategoryLearningRouterV2Report:
    if config is None:
        config = TeamSpecialistCrossCategoryLearningRouterV2Config()
    if type(config) is not TeamSpecialistCrossCategoryLearningRouterV2Config:
        raise ValueError(
            "config must be a TeamSpecialistCrossCategoryLearningRouterV2Config",
        )
    _require_hard_flags("TeamSpecialistCrossCategoryLearningRouterV2Config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    candidates = _normalize_learning_candidates(learning_candidates)

    rows = tuple(
        _row_for_candidate(rank=index, candidate=item, config=config)
        for index, item in enumerate(_sorted_candidates(candidates, config), start=1)
    )
    status = _router_status(rows)
    values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "router_status": status,
        "candidate_count": Decimal(len(rows)).quantize(COUNT_QUANT),
        "route_count": _status_count(rows, "route"),
        "watch_count": _status_count(rows, "watch"),
        "blocked_count": _status_count(rows, "blocked"),
        "average_learning_route_score": _average_score(rows),
        "top_learning_route_score": _top_score(rows),
        "bottom_learning_route_score": _bottom_score(rows),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows, status),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["derived_validation_digest"] = _derived_validation_digest(values)
    return TeamSpecialistCrossCategoryLearningRouterV2Report(**values)


def _sorted_candidates(
    candidates: tuple[TeamSpecialistCrossCategoryLearningRouterV2Input, ...],
    config: TeamSpecialistCrossCategoryLearningRouterV2Config,
) -> tuple[TeamSpecialistCrossCategoryLearningRouterV2Input, ...]:
    return tuple(
        sorted(
            candidates,
            key=lambda item: (
                -_score_for_candidate(item, config),
                item.specialist_id,
                item.source_category_id,
                item.target_category_id,
            ),
        ),
    )


def _row_for_candidate(
    *,
    rank: int,
    candidate: TeamSpecialistCrossCategoryLearningRouterV2Input,
    config: TeamSpecialistCrossCategoryLearningRouterV2Config,
) -> TeamSpecialistCrossCategoryLearningRouterV2Row:
    score = _score_for_candidate(candidate, config)
    status = _route_status(score, config)
    return TeamSpecialistCrossCategoryLearningRouterV2Row(
        rank=Decimal(rank).quantize(COUNT_QUANT),
        specialist_id=candidate.specialist_id,
        source_category_id=candidate.source_category_id,
        target_category_id=candidate.target_category_id,
        category_pair_id=_category_pair_id(candidate),
        specialist_fit_score=candidate.specialist_fit_score,
        category_overlap_score=candidate.category_overlap_score,
        transfer_signal_score=candidate.transfer_signal_score,
        evidence_quality_score=candidate.evidence_quality_score,
        stale_memory_days=candidate.stale_memory_days,
        stale_memory_penalty=_stale_memory_penalty(candidate.stale_memory_days, config),
        learning_route_score=score,
        route_status=status,
        reason_codes=_row_reason_codes(candidate, status, config),
    )


def _category_pair_id(
    candidate: TeamSpecialistCrossCategoryLearningRouterV2Input,
) -> str:
    return f"{candidate.source_category_id}__{candidate.target_category_id}"


def _score_for_candidate(
    candidate: TeamSpecialistCrossCategoryLearningRouterV2Input,
    config: TeamSpecialistCrossCategoryLearningRouterV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        base_score = (
            candidate.specialist_fit_score * config.specialist_fit_weight
            + candidate.category_overlap_score * config.category_overlap_weight
            + candidate.transfer_signal_score * config.transfer_signal_weight
            + candidate.evidence_quality_score * config.evidence_quality_weight
        )
        score = base_score - _stale_memory_penalty(candidate.stale_memory_days, config)
        return _clamp_ratio(score)


def _stale_memory_penalty(
    stale_memory_days: Decimal,
    config: TeamSpecialistCrossCategoryLearningRouterV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        stale_ratio = stale_memory_days / config.max_stale_memory_days
        return _clamp_ratio(stale_ratio * config.stale_memory_penalty_weight)


def _route_status(
    score: Decimal,
    config: TeamSpecialistCrossCategoryLearningRouterV2Config,
) -> str:
    if score >= config.route_score_floor:
        return "route"
    if score >= config.watch_score_floor:
        return "watch"
    return "blocked"


def _router_status(
    rows: tuple[TeamSpecialistCrossCategoryLearningRouterV2Row, ...],
) -> str:
    if not rows:
        return "blocked"
    if any(row.route_status == "blocked" for row in rows):
        return "blocked"
    if any(row.route_status == "watch" for row in rows):
        return "watch"
    return "route"


def _row_reason_codes(
    candidate: TeamSpecialistCrossCategoryLearningRouterV2Input,
    status: str,
    config: TeamSpecialistCrossCategoryLearningRouterV2Config,
) -> tuple[str, ...]:
    return (
        f"cross_category_learning_{status}",
        _tier_reason(
            candidate.specialist_fit_score,
            strong=Decimal("0.800000"),
            watch=Decimal("0.600000"),
            strong_reason="specialist_fit_strong",
            watch_reason="specialist_fit_watch",
            weak_reason="specialist_fit_weak",
        ),
        _tier_reason(
            candidate.category_overlap_score,
            strong=Decimal("0.800000"),
            watch=Decimal("0.600000"),
            strong_reason="category_overlap_strong",
            watch_reason="category_overlap_watch",
            weak_reason="category_overlap_weak",
        ),
        _tier_reason(
            candidate.transfer_signal_score,
            strong=Decimal("0.800000"),
            watch=Decimal("0.600000"),
            strong_reason="transfer_signal_strong",
            watch_reason="transfer_signal_watch",
            weak_reason="transfer_signal_weak",
        ),
        _tier_reason(
            candidate.evidence_quality_score,
            strong=Decimal("0.800000"),
            watch=Decimal("0.600000"),
            strong_reason="evidence_quality_strong",
            watch_reason="evidence_quality_watch",
            weak_reason="evidence_quality_weak",
        ),
        _stale_memory_reason(candidate.stale_memory_days, config),
    )


def _tier_reason(
    score: Decimal,
    *,
    strong: Decimal,
    watch: Decimal,
    strong_reason: str,
    watch_reason: str,
    weak_reason: str,
) -> str:
    if score >= strong:
        return strong_reason
    if score >= watch:
        return watch_reason
    return weak_reason


def _stale_memory_reason(
    stale_memory_days: Decimal,
    config: TeamSpecialistCrossCategoryLearningRouterV2Config,
) -> str:
    with localcontext(DECIMAL_CONTEXT):
        watch_floor = (config.max_stale_memory_days / Decimal("2")).quantize(COUNT_QUANT)
    if stale_memory_days >= config.max_stale_memory_days:
        return "stale_memory_stale"
    if stale_memory_days >= watch_floor:
        return "stale_memory_watch"
    return "stale_memory_fresh"


def _report_reason_codes(
    rows: tuple[TeamSpecialistCrossCategoryLearningRouterV2Row, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return ("cross_category_learning_router_empty",)
    if status == "route":
        return ("cross_category_learning_router_routed",)
    reasons: list[str] = []
    if any(row.route_status == "blocked" for row in rows):
        reasons.append("cross_category_learning_router_blocked_rows")
    if any(row.route_status == "watch" for row in rows):
        reasons.append("cross_category_learning_router_watch_rows")
    return tuple(reasons)


def _average_score(
    rows: tuple[TeamSpecialistCrossCategoryLearningRouterV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            sum((row.learning_route_score for row in rows), ZERO) / Decimal(len(rows)),
        )


def _top_score(rows: tuple[TeamSpecialistCrossCategoryLearningRouterV2Row, ...]) -> Decimal:
    if not rows:
        return ZERO
    return max(row.learning_route_score for row in rows).quantize(SCORE_QUANT)


def _bottom_score(
    rows: tuple[TeamSpecialistCrossCategoryLearningRouterV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return min(row.learning_route_score for row in rows).quantize(SCORE_QUANT)


def _status_count(
    rows: tuple[TeamSpecialistCrossCategoryLearningRouterV2Row, ...],
    status: str,
) -> Decimal:
    return Decimal(sum(1 for row in rows if row.route_status == status)).quantize(
        COUNT_QUANT,
    )


def _normalize_learning_candidates(
    learning_candidates: object,
) -> tuple[TeamSpecialistCrossCategoryLearningRouterV2Input, ...]:
    if type(learning_candidates) is str:
        raise ValueError("learning_candidates must be an iterable")
    try:
        candidates = tuple(learning_candidates)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("learning_candidates must be an iterable") from exc
    for item in candidates:
        if type(item) is not TeamSpecialistCrossCategoryLearningRouterV2Input:
            raise ValueError(
                "learning candidate items must be "
                "TeamSpecialistCrossCategoryLearningRouterV2Input",
            )
        _require_hard_flags("TeamSpecialistCrossCategoryLearningRouterV2Input", item)
    return candidates


def _normalize_rows(
    rows: object,
) -> tuple[TeamSpecialistCrossCategoryLearningRouterV2Row, ...]:
    if type(rows) is str:
        raise ValueError("rows must be a tuple of router rows")
    try:
        normalized = tuple(rows)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must be a tuple of router rows") from exc
    for row in normalized:
        if type(row) is not TeamSpecialistCrossCategoryLearningRouterV2Row:
            raise ValueError("rows must contain TeamSpecialistCrossCategoryLearningRouterV2Row")
        _require_hard_flags("TeamSpecialistCrossCategoryLearningRouterV2Row", row)
    return normalized


def _validate_config(config: TeamSpecialistCrossCategoryLearningRouterV2Config) -> None:
    with localcontext(DECIMAL_CONTEXT):
        weight_sum = (
            config.specialist_fit_weight
            + config.category_overlap_weight
            + config.transfer_signal_weight
            + config.evidence_quality_weight
        ).quantize(SCORE_QUANT)
    if weight_sum != ONE:
        raise ValueError("router weights must sum to 1.000000")
    if config.watch_score_floor > config.route_score_floor:
        raise ValueError("watch_score_floor must not exceed route_score_floor")


def _validate_row_consistency(
    row: TeamSpecialistCrossCategoryLearningRouterV2Row,
) -> None:
    if row.category_pair_id != f"{row.source_category_id}__{row.target_category_id}":
        raise ValueError("category_pair_id must match source and target category ids")
    if row.reason_codes[0] != f"cross_category_learning_{row.route_status}":
        raise ValueError("reason_codes must match route_status")


def _validate_report_consistency(
    report: TeamSpecialistCrossCategoryLearningRouterV2Report,
) -> None:
    rows = report.rows
    if report.candidate_count != Decimal(len(rows)).quantize(COUNT_QUANT):
        raise ValueError("candidate_count must match rows")
    if report.route_count + report.watch_count + report.blocked_count != report.candidate_count:
        raise ValueError("status counts must match rows")
    if report.route_count != _status_count(rows, "route"):
        raise ValueError("status counts must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("status counts must match rows")
    if report.blocked_count != _status_count(rows, "blocked"):
        raise ValueError("status counts must match rows")
    if report.router_status != _router_status(rows):
        raise ValueError("router_status must match rows")
    if report.reason_codes != _report_reason_codes(rows, report.router_status):
        raise ValueError("reason_codes must match router_status")
    expected_rank = Decimal("1")
    previous_score: Decimal | None = None
    previous_sort_key: tuple[str, str, str] | None = None
    for row in rows:
        if row.rank != expected_rank:
            raise ValueError("rows must be sorted by score and rank")
        sort_key = (row.specialist_id, row.source_category_id, row.target_category_id)
        if previous_score is not None:
            if row.learning_route_score > previous_score:
                raise ValueError("rows must be sorted by score and rank")
            if row.learning_route_score == previous_score and previous_sort_key is not None:
                if sort_key < previous_sort_key:
                    raise ValueError("rows must be sorted by score and rank")
        previous_score = row.learning_route_score
        previous_sort_key = sort_key
        expected_rank += Decimal("1")
    if report.derived_validation_digest != _derived_validation_digest(asdict(report)):
        raise ValueError("derived_validation_digest must match report fields")
    if report.average_learning_route_score != _average_score(rows):
        raise ValueError("average_learning_route_score must match rows")
    if report.top_learning_route_score != _top_score(rows):
        raise ValueError("top_learning_route_score must match rows")
    if report.bottom_learning_route_score != _bottom_score(rows):
        raise ValueError("bottom_learning_route_score must match rows")


def _require_route_status(field_name: str, value: object) -> None:
    _require_non_empty_string(field_name, value)
    if value not in ROUTE_STATUSES:
        raise ValueError(f"{field_name} must be one of {ROUTE_STATUSES}")


def _require_router_status(field_name: str, value: object) -> None:
    _require_non_empty_string(field_name, value)
    if value not in ROUTER_STATUSES:
        raise ValueError(f"{field_name} must be one of {ROUTER_STATUSES}")


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is str:
        raise ValueError(f"{field_name} must be a tuple of strings")
    try:
        values = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be a tuple of strings") from exc
    if not values:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in values:
        if type(reason_code) is not str or reason_code == "":
            raise ValueError(f"{field_name} must contain non-empty strings")
        if reason_code not in allowed_values:
            raise ValueError(f"{field_name} contains unknown reason code")
    return values


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_non_empty_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == "":
        raise ValueError(f"{field_name} must not be empty")
    return value


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    if decimal_value.as_tuple().exponent < -6:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return decimal_value.quantize(SCORE_QUANT)


def _normalize_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return decimal_value.quantize(COUNT_QUANT)


def _normalize_positive_integral_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_integral_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be > 0.000000")
    return decimal_value


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
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
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
    if value is None or type(value) in (str, int, bool):
        return value
    raise ValueError("payload contains unsupported value")


def _derived_validation_digest(values: dict[str, object]) -> str:
    digest_payload = {
        key: _payload_value(item)
        for key, item in values.items()
        if key != "derived_validation_digest"
    }
    _reject_unsafe_public_payload("derived validation digest payload", digest_payload)
    encoded = json.dumps(
        digest_payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public payload in {label}")
            _reject_unsafe_public_text(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is float:
        raise ValueError(f"unsafe public payload in {label}")
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"unsafe public payload in {label}")
