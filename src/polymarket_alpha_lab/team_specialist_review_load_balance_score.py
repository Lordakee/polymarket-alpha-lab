"""Pure readonly report for specialist review load balance score."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any
import json


DEFAULT_TEAM_SPECIALIST_REVIEW_LOAD_BALANCE_SCORE_CONFIG_VERSION = (
    "team-specialist-review-load-balance-score-v1"
)
TEAM_SPECIALIST_REVIEW_LOAD_BALANCE_SCORE_STATUSES = ("pass", "watch", "block")

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SCORE_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

REASON_CODES = (
    "review_load_balance_pass",
    "review_load_balance_watch",
    "review_load_balance_block",
    "assignment_pressure_clear",
    "assignment_pressure_watch",
    "assignment_pressure_block",
    "utilization_spread_clear",
    "utilization_spread_watch",
    "utilization_spread_block",
    "queue_depth_spread_clear",
    "queue_depth_spread_watch",
    "queue_depth_spread_block",
    "stale_review_spread_clear",
    "stale_review_spread_watch",
    "stale_review_spread_block",
    "overloaded_specialist_share_clear",
    "overloaded_specialist_share_watch",
    "overloaded_specialist_share_block",
    "review_load_balance_row_pass",
    "review_load_balance_row_assignment_pressure",
    "review_load_balance_row_over_capacity",
    "review_load_balance_row_stale_reviews",
)
UNSAFE_PUBLIC_FRAGMENTS = tuple(
    bytes.fromhex(value).decode("ascii")
    for value in (
        "726177",
        "3a2f2f",
        "68747470",
        "40",
        "3f",
        "6d61726b65745f6964",
        "63616e6469646174655f6964",
        "6d61726b65745f736c7567",
        "6d61726b65745f7175657374696f6e",
        "7175657374696f6e",
        "75726c",
        "736f757263655f726566",
        "736f757263655f72656673",
        "736f757263655f74657874",
        "64736e",
        "7461626c655f6e616d65",
        "746f6b656e",
        "736563726574",
        "61757468",
        "77616c6c6574",
        "6f72646572",
        "7472616465",
        "627579",
        "73656c6c",
        "7265636f6d6d656e646174696f6e",
        "706f736974696f6e",
        "706f736974696f6e5f73697a65",
        "706f736974696f6e2d73697a696e67",
        "6c697665",
        "6e6574776f726b",
        "6461746162617365",
        "70657273697374",
        "7375706162617365",
    )
)

__all__ = (
    "DEFAULT_TEAM_SPECIALIST_REVIEW_LOAD_BALANCE_SCORE_CONFIG_VERSION",
    "TEAM_SPECIALIST_REVIEW_LOAD_BALANCE_SCORE_STATUSES",
    "TeamSpecialistReviewLoadBalanceScoreConfig",
    "TeamSpecialistReviewLoadBalanceScoreInput",
    "TeamSpecialistReviewLoadBalanceScoreRow",
    "TeamSpecialistReviewLoadBalanceScoreReport",
    "score_team_specialist_review_load_balance",
    "team_specialist_review_load_balance_score_payload",
)


@dataclass(frozen=True)
class TeamSpecialistReviewLoadBalanceScoreConfig:
    config_version: str = (
        DEFAULT_TEAM_SPECIALIST_REVIEW_LOAD_BALANCE_SCORE_CONFIG_VERSION
    )
    assignment_pressure_weight: Decimal = Decimal("0.472500")
    capacity_utilization_spread_weight: Decimal = Decimal("0.296250")
    queue_depth_spread_weight: Decimal = Decimal("0.061250")
    stale_review_spread_weight: Decimal = Decimal("0.150000")
    overloaded_specialist_share_weight: Decimal = Decimal("0.020000")
    assignment_pressure_watch_floor: Decimal = Decimal("0.250000")
    assignment_pressure_block_floor: Decimal = Decimal("0.750000")
    capacity_utilization_spread_watch_floor: Decimal = Decimal("0.750000")
    capacity_utilization_spread_block_floor: Decimal = Decimal("1.500000")
    queue_depth_spread_watch_floor: Decimal = Decimal("0.500000")
    queue_depth_spread_block_floor: Decimal = Decimal("0.900000")
    stale_review_spread_watch_floor: Decimal = Decimal("0.150000")
    stale_review_spread_block_floor: Decimal = Decimal("0.500000")
    overloaded_specialist_share_watch_floor: Decimal = Decimal("0.250000")
    overloaded_specialist_share_block_floor: Decimal = Decimal("0.750000")
    overloaded_utilization_floor: Decimal = Decimal("1.000000")
    score_watch_floor: Decimal = Decimal("0.250000")
    score_block_floor: Decimal = Decimal("0.750000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistReviewLoadBalanceScoreConfig:
            raise ValueError(
                "config must be exactly TeamSpecialistReviewLoadBalanceScoreConfig",
            )
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        for field_name in (
            "assignment_pressure_weight",
            "capacity_utilization_spread_weight",
            "queue_depth_spread_weight",
            "stale_review_spread_weight",
            "overloaded_specialist_share_weight",
            "assignment_pressure_watch_floor",
            "assignment_pressure_block_floor",
            "queue_depth_spread_watch_floor",
            "queue_depth_spread_block_floor",
            "stale_review_spread_watch_floor",
            "stale_review_spread_block_floor",
            "overloaded_specialist_share_watch_floor",
            "overloaded_specialist_share_block_floor",
            "score_watch_floor",
            "score_block_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "capacity_utilization_spread_watch_floor",
            "capacity_utilization_spread_block_floor",
            "overloaded_utilization_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("TeamSpecialistReviewLoadBalanceScoreConfig", self)
        _reject_public_payload(
            "TeamSpecialistReviewLoadBalanceScoreConfig",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistReviewLoadBalanceScoreInput:
    team_id: str
    specialist_id: str
    assigned_review_count: Decimal
    active_review_count: Decimal
    stale_review_count: Decimal
    daily_review_capacity: Decimal
    completed_review_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistReviewLoadBalanceScoreInput:
            raise ValueError(
                "input must be exactly TeamSpecialistReviewLoadBalanceScoreInput",
            )
        object.__setattr__(
            self,
            "team_id",
            _require_public_string("team_id", self.team_id),
        )
        object.__setattr__(
            self,
            "specialist_id",
            _require_public_string("specialist_id", self.specialist_id),
        )
        for field_name in (
            "assigned_review_count",
            "active_review_count",
            "stale_review_count",
            "completed_review_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "daily_review_capacity",
            _normalize_positive_decimal(
                "daily_review_capacity",
                self.daily_review_capacity,
            ),
        )
        if self.stale_review_count > self.assigned_review_count:
            raise ValueError("stale_review_count must not exceed assigned_review_count")
        if self.active_review_count > self.assigned_review_count:
            raise ValueError("active_review_count must not exceed assigned_review_count")
        _require_hard_flags("TeamSpecialistReviewLoadBalanceScoreInput", self)
        _reject_public_payload(
            "TeamSpecialistReviewLoadBalanceScoreInput",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistReviewLoadBalanceScoreRow:
    rank: Decimal
    team_id: str
    specialist_id: str
    assigned_review_count: Decimal
    active_review_count: Decimal
    stale_review_count: Decimal
    daily_review_capacity: Decimal
    completed_review_count: Decimal
    assigned_review_share: Decimal
    capacity_share: Decimal
    expected_assigned_review_count: Decimal
    allocation_gap_count: Decimal
    absolute_allocation_gap_count: Decimal
    assignment_pressure: Decimal
    capacity_utilization_ratio: Decimal
    stale_review_ratio: Decimal
    row_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistReviewLoadBalanceScoreRow:
            raise ValueError(
                "row must be exactly TeamSpecialistReviewLoadBalanceScoreRow",
            )
        object.__setattr__(self, "rank", _normalize_count("rank", self.rank))
        if self.rank <= ZERO:
            raise ValueError("rank must be positive")
        object.__setattr__(
            self,
            "team_id",
            _require_public_string("team_id", self.team_id),
        )
        object.__setattr__(
            self,
            "specialist_id",
            _require_public_string("specialist_id", self.specialist_id),
        )
        for field_name in (
            "assigned_review_count",
            "active_review_count",
            "stale_review_count",
            "completed_review_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "daily_review_capacity",
            "expected_assigned_review_count",
            "absolute_allocation_gap_count",
            "capacity_utilization_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "allocation_gap_count",
            _normalize_decimal("allocation_gap_count", self.allocation_gap_count),
        )
        for field_name in (
            "assigned_review_share",
            "capacity_share",
            "assignment_pressure",
            "stale_review_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.daily_review_capacity <= ZERO:
            raise ValueError("daily_review_capacity must be positive")
        if self.stale_review_count > self.assigned_review_count:
            raise ValueError("stale_review_count must not exceed assigned_review_count")
        if self.active_review_count > self.assigned_review_count:
            raise ValueError("active_review_count must not exceed assigned_review_count")
        _require_status("row_status", self.row_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("TeamSpecialistReviewLoadBalanceScoreRow", self)
        _reject_public_payload(
            "TeamSpecialistReviewLoadBalanceScoreRow",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistReviewLoadBalanceScoreReport:
    config: TeamSpecialistReviewLoadBalanceScoreConfig
    specialist_count: Decimal
    total_assigned_review_count: Decimal
    total_active_review_count: Decimal
    total_stale_review_count: Decimal
    total_daily_review_capacity: Decimal
    max_assignment_pressure: Decimal
    capacity_utilization_spread: Decimal
    queue_depth_spread_ratio: Decimal
    stale_review_ratio_spread: Decimal
    overloaded_specialist_share: Decimal
    review_load_balance_score: Decimal
    load_balance_status: str
    report_status: str
    rebalance_research_queue: bool
    rows: tuple[TeamSpecialistReviewLoadBalanceScoreRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistReviewLoadBalanceScoreReport:
            raise ValueError(
                "report must be exactly TeamSpecialistReviewLoadBalanceScoreReport",
            )
        if type(self.config) is not TeamSpecialistReviewLoadBalanceScoreConfig:
            raise ValueError(
                "config must be a TeamSpecialistReviewLoadBalanceScoreConfig",
            )
        _require_hard_flags("TeamSpecialistReviewLoadBalanceScoreConfig", self.config)
        for field_name in (
            "specialist_count",
            "total_assigned_review_count",
            "total_active_review_count",
            "total_stale_review_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "total_daily_review_capacity",
            _normalize_nonnegative_decimal(
                "total_daily_review_capacity",
                self.total_daily_review_capacity,
            ),
        )
        for field_name in (
            "max_assignment_pressure",
            "queue_depth_spread_ratio",
            "stale_review_ratio_spread",
            "overloaded_specialist_share",
            "review_load_balance_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "capacity_utilization_spread",
            _normalize_nonnegative_decimal(
                "capacity_utilization_spread",
                self.capacity_utilization_spread,
            ),
        )
        _require_status("load_balance_status", self.load_balance_status)
        _require_status("report_status", self.report_status)
        if type(self.rebalance_research_queue) is not bool:
            raise ValueError("rebalance_research_queue must be a bool")
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("TeamSpecialistReviewLoadBalanceScoreReport", self)
        _reject_public_payload(
            "TeamSpecialistReviewLoadBalanceScoreReport",
            _payload_value(asdict(self)),
        )
        _validate_report_consistency(self)

    @property
    def payload(self) -> dict[str, Any]:
        payload = _payload_value(asdict(self))
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        _reject_public_payload(
            "TeamSpecialistReviewLoadBalanceScoreReport.payload",
            payload,
        )
        _verify_payload_digest(payload)
        return payload


def score_team_specialist_review_load_balance(
    review_load_signals: object,
    *,
    config: TeamSpecialistReviewLoadBalanceScoreConfig | None = None,
) -> TeamSpecialistReviewLoadBalanceScoreReport:
    if config is None:
        config = TeamSpecialistReviewLoadBalanceScoreConfig()
    if type(config) is not TeamSpecialistReviewLoadBalanceScoreConfig:
        raise ValueError("config must be a TeamSpecialistReviewLoadBalanceScoreConfig")
    _require_hard_flags("TeamSpecialistReviewLoadBalanceScoreConfig", config)
    inputs = _normalize_inputs(review_load_signals)
    rows = _rows_for_inputs(inputs, config)
    specialist_count = Decimal(len(rows)).quantize(COUNT_QUANT)
    total_assigned = _sum_count(row.assigned_review_count for row in rows)
    total_active = _sum_count(row.active_review_count for row in rows)
    total_stale = _sum_count(row.stale_review_count for row in rows)
    total_capacity = _sum_decimal(row.daily_review_capacity for row in rows)
    max_assignment_pressure = _max_ratio(row.assignment_pressure for row in rows)
    utilization_spread = _spread_decimal(
        (row.capacity_utilization_ratio for row in rows),
    )
    queue_depth_spread = _assigned_depth_spread(rows)
    stale_spread = _spread_ratio(row.stale_review_ratio for row in rows)
    overloaded_share = _overloaded_specialist_share(rows, config)
    score = _review_load_balance_score(
        config=config,
        max_assignment_pressure=max_assignment_pressure,
        capacity_utilization_spread=utilization_spread,
        queue_depth_spread_ratio=queue_depth_spread,
        stale_review_ratio_spread=stale_spread,
        overloaded_specialist_share=overloaded_share,
    )
    status = _load_balance_status(
        config=config,
        max_assignment_pressure=max_assignment_pressure,
        capacity_utilization_spread=utilization_spread,
        queue_depth_spread_ratio=queue_depth_spread,
        stale_review_ratio_spread=stale_spread,
        overloaded_specialist_share=overloaded_share,
        review_load_balance_score=score,
        specialist_count=specialist_count,
    )
    values: dict[str, object] = {
        "config": config,
        "specialist_count": specialist_count,
        "total_assigned_review_count": total_assigned,
        "total_active_review_count": total_active,
        "total_stale_review_count": total_stale,
        "total_daily_review_capacity": total_capacity,
        "max_assignment_pressure": max_assignment_pressure,
        "capacity_utilization_spread": utilization_spread,
        "queue_depth_spread_ratio": queue_depth_spread,
        "stale_review_ratio_spread": stale_spread,
        "overloaded_specialist_share": overloaded_share,
        "review_load_balance_score": score,
        "load_balance_status": status,
        "report_status": status,
        "rebalance_research_queue": status != "pass",
        "rows": rows,
        "reason_codes": _report_reason_codes(
            load_balance_status=status,
            config=config,
            max_assignment_pressure=max_assignment_pressure,
            capacity_utilization_spread=utilization_spread,
            queue_depth_spread_ratio=queue_depth_spread,
            stale_review_ratio_spread=stale_spread,
            overloaded_specialist_share=overloaded_share,
        ),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["derived_validation_digest"] = _derived_validation_digest(values)
    return TeamSpecialistReviewLoadBalanceScoreReport(**values)


def team_specialist_review_load_balance_score_payload(
    report: TeamSpecialistReviewLoadBalanceScoreReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is TeamSpecialistReviewLoadBalanceScoreReport:
        _require_hard_flags("TeamSpecialistReviewLoadBalanceScoreReport", report)
        return report.payload
    if type(report) is dict:
        payload = _payload_value(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a dict")
        _reject_public_payload(
            "TeamSpecialistReviewLoadBalanceScoreReport.payload",
            payload,
        )
        _require_hard_flags("payload", _DictFlags(payload))
        _verify_payload_digest(payload)
        return payload
    raise ValueError("report must be a TeamSpecialistReviewLoadBalanceScoreReport")


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


def _rows_for_inputs(
    inputs: tuple[TeamSpecialistReviewLoadBalanceScoreInput, ...],
    config: TeamSpecialistReviewLoadBalanceScoreConfig,
) -> tuple[TeamSpecialistReviewLoadBalanceScoreRow, ...]:
    sorted_inputs = tuple(sorted(inputs, key=lambda item: (item.team_id, item.specialist_id)))
    total_assigned = _sum_decimal(item.assigned_review_count for item in sorted_inputs)
    total_capacity = _sum_decimal(item.daily_review_capacity for item in sorted_inputs)
    return tuple(
        _row_for_input(
            rank=index,
            item=item,
            total_assigned_review_count=total_assigned,
            total_daily_review_capacity=total_capacity,
            config=config,
        )
        for index, item in enumerate(sorted_inputs, start=1)
    )


def _row_for_input(
    *,
    rank: int,
    item: TeamSpecialistReviewLoadBalanceScoreInput,
    total_assigned_review_count: Decimal,
    total_daily_review_capacity: Decimal,
    config: TeamSpecialistReviewLoadBalanceScoreConfig,
) -> TeamSpecialistReviewLoadBalanceScoreRow:
    assigned_share = _ratio_or_zero(
        item.assigned_review_count,
        total_assigned_review_count,
    )
    capacity_share = _ratio_or_zero(
        item.daily_review_capacity,
        total_daily_review_capacity,
    )
    with localcontext(DECIMAL_CONTEXT):
        expected_count = (total_assigned_review_count * capacity_share).quantize(
            SCORE_QUANT,
        )
        allocation_gap = (item.assigned_review_count - expected_count).quantize(
            SCORE_QUANT,
        )
    absolute_gap = _absolute_decimal(allocation_gap)
    assignment_pressure = _positive_assignment_pressure(
        allocation_gap,
        expected_count,
    )
    utilization = _ratio(item.assigned_review_count, item.daily_review_capacity)
    stale_ratio = _ratio_or_zero(item.stale_review_count, item.assigned_review_count)
    row_status = _row_status(
        assignment_pressure=assignment_pressure,
        capacity_utilization_ratio=utilization,
        stale_review_ratio=stale_ratio,
        config=config,
    )
    return TeamSpecialistReviewLoadBalanceScoreRow(
        rank=Decimal(rank).quantize(COUNT_QUANT),
        team_id=item.team_id,
        specialist_id=item.specialist_id,
        assigned_review_count=item.assigned_review_count,
        active_review_count=item.active_review_count,
        stale_review_count=item.stale_review_count,
        daily_review_capacity=item.daily_review_capacity,
        completed_review_count=item.completed_review_count,
        assigned_review_share=assigned_share,
        capacity_share=capacity_share,
        expected_assigned_review_count=expected_count,
        allocation_gap_count=allocation_gap,
        absolute_allocation_gap_count=absolute_gap,
        assignment_pressure=assignment_pressure,
        capacity_utilization_ratio=utilization,
        stale_review_ratio=stale_ratio,
        row_status=row_status,
        reason_codes=_row_reason_codes(
            assignment_pressure=assignment_pressure,
            capacity_utilization_ratio=utilization,
            stale_review_count=item.stale_review_count,
            row_status=row_status,
            config=config,
        ),
    )


def _review_load_balance_score(
    *,
    config: TeamSpecialistReviewLoadBalanceScoreConfig,
    max_assignment_pressure: Decimal,
    capacity_utilization_spread: Decimal,
    queue_depth_spread_ratio: Decimal,
    stale_review_ratio_spread: Decimal,
    overloaded_specialist_share: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            max_assignment_pressure * config.assignment_pressure_weight
            + _clamp_ratio(capacity_utilization_spread)
            * config.capacity_utilization_spread_weight
            + queue_depth_spread_ratio * config.queue_depth_spread_weight
            + stale_review_ratio_spread * config.stale_review_spread_weight
            + overloaded_specialist_share * config.overloaded_specialist_share_weight,
        )


def _load_balance_status(
    *,
    config: TeamSpecialistReviewLoadBalanceScoreConfig,
    max_assignment_pressure: Decimal,
    capacity_utilization_spread: Decimal,
    queue_depth_spread_ratio: Decimal,
    stale_review_ratio_spread: Decimal,
    overloaded_specialist_share: Decimal,
    review_load_balance_score: Decimal,
    specialist_count: Decimal,
) -> str:
    if (
        specialist_count == ZERO
        or max_assignment_pressure >= config.assignment_pressure_block_floor
        or capacity_utilization_spread
        >= config.capacity_utilization_spread_block_floor
        or queue_depth_spread_ratio >= config.queue_depth_spread_block_floor
        or stale_review_ratio_spread >= config.stale_review_spread_block_floor
        or overloaded_specialist_share
        >= config.overloaded_specialist_share_block_floor
        or review_load_balance_score >= config.score_block_floor
    ):
        return "block"
    if (
        max_assignment_pressure >= config.assignment_pressure_watch_floor
        or capacity_utilization_spread
        >= config.capacity_utilization_spread_watch_floor
        or queue_depth_spread_ratio >= config.queue_depth_spread_watch_floor
        or stale_review_ratio_spread >= config.stale_review_spread_watch_floor
        or overloaded_specialist_share
        >= config.overloaded_specialist_share_watch_floor
        or review_load_balance_score >= config.score_watch_floor
    ):
        return "watch"
    return "pass"


def _row_status(
    *,
    assignment_pressure: Decimal,
    capacity_utilization_ratio: Decimal,
    stale_review_ratio: Decimal,
    config: TeamSpecialistReviewLoadBalanceScoreConfig,
) -> str:
    if assignment_pressure >= config.assignment_pressure_block_floor:
        return "block"
    if (
        assignment_pressure >= config.assignment_pressure_watch_floor
        or capacity_utilization_ratio > config.overloaded_utilization_floor
        or stale_review_ratio >= config.stale_review_spread_watch_floor
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    assignment_pressure: Decimal,
    capacity_utilization_ratio: Decimal,
    stale_review_count: Decimal,
    row_status: str,
    config: TeamSpecialistReviewLoadBalanceScoreConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if assignment_pressure >= config.assignment_pressure_watch_floor:
        reasons.append("review_load_balance_row_assignment_pressure")
    if capacity_utilization_ratio > config.overloaded_utilization_floor:
        reasons.append("review_load_balance_row_over_capacity")
    if stale_review_count > ZERO and row_status != "pass":
        reasons.append("review_load_balance_row_stale_reviews")
    if row_status == "pass":
        reasons.append("review_load_balance_row_pass")
    return _normalize_reason_codes("reason_codes", tuple(reasons))


def _report_reason_codes(
    *,
    load_balance_status: str,
    config: TeamSpecialistReviewLoadBalanceScoreConfig,
    max_assignment_pressure: Decimal,
    capacity_utilization_spread: Decimal,
    queue_depth_spread_ratio: Decimal,
    stale_review_ratio_spread: Decimal,
    overloaded_specialist_share: Decimal,
) -> tuple[str, ...]:
    return _normalize_reason_codes(
        "reason_codes",
        (
            f"review_load_balance_{load_balance_status}",
            _band_reason(
                "assignment_pressure",
                max_assignment_pressure,
                config.assignment_pressure_watch_floor,
                config.assignment_pressure_block_floor,
            ),
            _band_reason(
                "utilization_spread",
                capacity_utilization_spread,
                config.capacity_utilization_spread_watch_floor,
                config.capacity_utilization_spread_block_floor,
            ),
            _band_reason(
                "queue_depth_spread",
                queue_depth_spread_ratio,
                config.queue_depth_spread_watch_floor,
                config.queue_depth_spread_block_floor,
            ),
            _band_reason(
                "stale_review_spread",
                stale_review_ratio_spread,
                config.stale_review_spread_watch_floor,
                config.stale_review_spread_block_floor,
            ),
            _band_reason(
                "overloaded_specialist_share",
                overloaded_specialist_share,
                config.overloaded_specialist_share_watch_floor,
                config.overloaded_specialist_share_block_floor,
            ),
        ),
    )


def _band_reason(
    stem: str,
    value: Decimal,
    watch_floor: Decimal,
    block_floor: Decimal,
) -> str:
    if value >= block_floor:
        return f"{stem}_block"
    if value >= watch_floor:
        return f"{stem}_watch"
    return f"{stem}_clear"


def _validate_config(config: TeamSpecialistReviewLoadBalanceScoreConfig) -> None:
    with localcontext(DECIMAL_CONTEXT):
        weights_total = (
            config.assignment_pressure_weight
            + config.capacity_utilization_spread_weight
            + config.queue_depth_spread_weight
            + config.stale_review_spread_weight
            + config.overloaded_specialist_share_weight
        ).quantize(SCORE_QUANT)
    if weights_total != ONE:
        raise ValueError("score weights must sum to 1.000000")
    if config.assignment_pressure_watch_floor > config.assignment_pressure_block_floor:
        raise ValueError(
            "assignment_pressure_watch_floor must not exceed "
            "assignment_pressure_block_floor",
        )
    if (
        config.capacity_utilization_spread_watch_floor
        > config.capacity_utilization_spread_block_floor
    ):
        raise ValueError(
            "capacity_utilization_spread_watch_floor must not exceed "
            "capacity_utilization_spread_block_floor",
        )
    if config.queue_depth_spread_watch_floor > config.queue_depth_spread_block_floor:
        raise ValueError(
            "queue_depth_spread_watch_floor must not exceed "
            "queue_depth_spread_block_floor",
        )
    if config.stale_review_spread_watch_floor > config.stale_review_spread_block_floor:
        raise ValueError(
            "stale_review_spread_watch_floor must not exceed "
            "stale_review_spread_block_floor",
        )
    if (
        config.overloaded_specialist_share_watch_floor
        > config.overloaded_specialist_share_block_floor
    ):
        raise ValueError(
            "overloaded_specialist_share_watch_floor must not exceed "
            "overloaded_specialist_share_block_floor",
        )
    if config.score_watch_floor > config.score_block_floor:
        raise ValueError("score_watch_floor must not exceed score_block_floor")


def _validate_report_consistency(
    report: TeamSpecialistReviewLoadBalanceScoreReport,
) -> None:
    if report.rows != _normalize_rows(report.rows):
        raise ValueError("rows must be sorted by team_id and specialist_id")
    if report.specialist_count != Decimal(len(report.rows)).quantize(COUNT_QUANT):
        raise ValueError("specialist_count must match rows")
    if report.total_assigned_review_count != _sum_decimal(
        row.assigned_review_count for row in report.rows
    ):
        raise ValueError("total_assigned_review_count must match rows")
    if report.total_active_review_count != _sum_decimal(
        row.active_review_count for row in report.rows
    ):
        raise ValueError("total_active_review_count must match rows")
    if report.total_stale_review_count != _sum_decimal(
        row.stale_review_count for row in report.rows
    ):
        raise ValueError("total_stale_review_count must match rows")
    if report.total_daily_review_capacity != _sum_decimal(
        row.daily_review_capacity for row in report.rows
    ):
        raise ValueError("total_daily_review_capacity must match rows")
    expected_max_assignment = _max_ratio(
        (row.assignment_pressure for row in report.rows),
    )
    if report.max_assignment_pressure != expected_max_assignment:
        raise ValueError("max_assignment_pressure must match rows")
    expected_utilization_spread = _spread_decimal(
        (row.capacity_utilization_ratio for row in report.rows),
    )
    if report.capacity_utilization_spread != expected_utilization_spread:
        raise ValueError("capacity_utilization_spread must match rows")
    expected_queue_spread = _assigned_depth_spread(report.rows)
    if report.queue_depth_spread_ratio != expected_queue_spread:
        raise ValueError("queue_depth_spread_ratio must match rows")
    expected_stale_spread = _spread_ratio(row.stale_review_ratio for row in report.rows)
    if report.stale_review_ratio_spread != expected_stale_spread:
        raise ValueError("stale_review_ratio_spread must match rows")
    expected_overloaded_share = _overloaded_specialist_share(report.rows, report.config)
    if report.overloaded_specialist_share != expected_overloaded_share:
        raise ValueError("overloaded_specialist_share must match rows")
    expected_score = _review_load_balance_score(
        config=report.config,
        max_assignment_pressure=report.max_assignment_pressure,
        capacity_utilization_spread=report.capacity_utilization_spread,
        queue_depth_spread_ratio=report.queue_depth_spread_ratio,
        stale_review_ratio_spread=report.stale_review_ratio_spread,
        overloaded_specialist_share=report.overloaded_specialist_share,
    )
    if report.review_load_balance_score != expected_score:
        raise ValueError("review_load_balance_score must match components")
    expected_status = _load_balance_status(
        config=report.config,
        max_assignment_pressure=report.max_assignment_pressure,
        capacity_utilization_spread=report.capacity_utilization_spread,
        queue_depth_spread_ratio=report.queue_depth_spread_ratio,
        stale_review_ratio_spread=report.stale_review_ratio_spread,
        overloaded_specialist_share=report.overloaded_specialist_share,
        review_load_balance_score=report.review_load_balance_score,
        specialist_count=report.specialist_count,
    )
    if report.load_balance_status != expected_status:
        raise ValueError("load_balance_status must match components")
    if report.report_status != report.load_balance_status:
        raise ValueError("report_status must match load_balance_status")
    if report.rebalance_research_queue is not (report.report_status != "pass"):
        raise ValueError("rebalance_research_queue must match report_status")
    if report.reason_codes != _report_reason_codes(
        load_balance_status=report.load_balance_status,
        config=report.config,
        max_assignment_pressure=report.max_assignment_pressure,
        capacity_utilization_spread=report.capacity_utilization_spread,
        queue_depth_spread_ratio=report.queue_depth_spread_ratio,
        stale_review_ratio_spread=report.stale_review_ratio_spread,
        overloaded_specialist_share=report.overloaded_specialist_share,
    ):
        raise ValueError("reason_codes must match components")
    if report.derived_validation_digest != _derived_validation_digest(asdict(report)):
        raise ValueError("derived_validation_digest must match report fields")


def _normalize_inputs(
    value: object,
) -> tuple[TeamSpecialistReviewLoadBalanceScoreInput, ...]:
    if isinstance(value, (str, bytes)) or not hasattr(value, "__iter__"):
        raise ValueError("review_load_signals must be an iterable")
    items = tuple(value)
    for item in items:
        if type(item) is not TeamSpecialistReviewLoadBalanceScoreInput:
            raise ValueError(
                "review_load_signals must contain "
                "TeamSpecialistReviewLoadBalanceScoreInput values",
            )
        _require_hard_flags("TeamSpecialistReviewLoadBalanceScoreInput", item)
    return items


def _normalize_rows(
    rows: object,
) -> tuple[TeamSpecialistReviewLoadBalanceScoreRow, ...]:
    if isinstance(rows, (str, bytes)) or not hasattr(rows, "__iter__"):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not TeamSpecialistReviewLoadBalanceScoreRow:
            raise ValueError(
                "rows must contain TeamSpecialistReviewLoadBalanceScoreRow values",
            )
        _require_hard_flags("TeamSpecialistReviewLoadBalanceScoreRow", row)
    return tuple(sorted(normalized, key=lambda row: (row.team_id, row.specialist_id)))


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("summed values must be exactly Decimal")
        with localcontext(DECIMAL_CONTEXT):
            total = (total + value).quantize(SCORE_QUANT)
    return total


def _sum_count(values: object) -> Decimal:
    return _sum_decimal(values).quantize(COUNT_QUANT)


def _max_ratio(values: object) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    return _clamp_ratio(max(items))


def _spread_ratio(values: object) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    return _clamp_ratio(max(items) - min(items))


def _spread_decimal(values: object) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (max(items) - min(items)).quantize(SCORE_QUANT)


def _assigned_depth_spread(
    rows: tuple[TeamSpecialistReviewLoadBalanceScoreRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    max_depth = max(row.assigned_review_count for row in rows)
    min_depth = min(row.assigned_review_count for row in rows)
    if max_depth == ZERO:
        return ZERO
    return _clamp_ratio(_ratio(max_depth - min_depth, max_depth))


def _overloaded_specialist_share(
    rows: tuple[TeamSpecialistReviewLoadBalanceScoreRow, ...],
    config: TeamSpecialistReviewLoadBalanceScoreConfig,
) -> Decimal:
    if not rows:
        return ZERO
    overloaded_count = sum(
        1
        for row in rows
        if row.capacity_utilization_ratio > config.overloaded_utilization_floor
    )
    return _ratio(Decimal(overloaded_count).quantize(COUNT_QUANT), Decimal(len(rows)))


def _positive_assignment_pressure(
    allocation_gap_count: Decimal,
    expected_assigned_review_count: Decimal,
) -> Decimal:
    if allocation_gap_count <= ZERO or expected_assigned_review_count <= ZERO:
        return ZERO
    return _clamp_ratio(_ratio(allocation_gap_count, expected_assigned_review_count))


def _absolute_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return abs(value).quantize(SCORE_QUANT)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(SCORE_QUANT)


def _ratio_or_zero(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _clamp_ratio(_ratio(numerator, denominator))


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize_decimal("ratio", value)
    if normalized < ZERO:
        return ZERO
    if normalized > ONE:
        return ONE
    return normalized


def _normalize_ratio(name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{name} must be between 0.000000 and 1.000000")
    return normalized


def _normalize_positive_decimal(name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(name, value)
    if normalized <= ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _normalize_count(name: str, value: Decimal) -> Decimal:
    _require_decimal(name, value)
    if value != value.to_integral_value():
        raise ValueError(f"{name} must be integral")
    if value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return value.quantize(COUNT_QUANT)


def _normalize_decimal(name: str, value: Decimal) -> Decimal:
    _require_decimal(name, value)
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if value.as_tuple().exponent < -6:
        raise ValueError(f"{name} must use six decimal places or fewer")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(SCORE_QUANT)


def _quantize_decimal(name: str, value: Decimal) -> Decimal:
    _require_decimal(name, value)
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(SCORE_QUANT)


def _require_decimal(name: str, value: Decimal) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be exactly Decimal")


def _require_public_string(name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{name} must be non-empty")
    if normalized != value:
        raise ValueError(f"{name} must not contain leading or trailing whitespace")
    if _has_unsafe_fragment(normalized):
        raise ValueError(f"{name} has unsafe public value")
    return normalized


def _require_status(name: str, value: str) -> None:
    if type(value) is not str or value not in TEAM_SPECIALIST_REVIEW_LOAD_BALANCE_SCORE_STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")


def _normalize_reason_codes(name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not hasattr(value, "__iter__"):
        raise ValueError(f"{name} must be an iterable")
    codes = tuple(value)
    if not codes:
        raise ValueError(f"{name} must not be empty")
    for code in codes:
        if type(code) is not str or code not in REASON_CODES:
            raise ValueError(f"{name} contains an unknown reason code")
        if _has_unsafe_fragment(code):
            raise ValueError(f"{name} contains unsafe public value")
    return codes


def _require_hard_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")


def _require_digest(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be a sha256 hex digest")


def _payload_value(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _payload_value(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return str(value)
    if isinstance(value, float):
        raise ValueError("payload value must not be a float")
    if type(value) is int:
        raise ValueError("payload value must use Decimal-derived strings")
    if type(value) in (str, bool):
        return value
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            ready[key] = _payload_value(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_payload_value(item) for item in value]
    raise ValueError("payload value is not supported")


def _reject_public_payload(label: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("unsafe public key")
            if _has_unsafe_fragment(key):
                raise ValueError(f"unsafe public key in {label}")
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{key} must be True")
            _reject_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_payload(label, item)
        return
    if type(value) is str and _has_unsafe_fragment(value):
        raise ValueError(f"unsafe public value in {label}")
    if isinstance(value, float) or type(value) is int:
        raise ValueError(f"unsafe numeric payload value in {label}")


def _has_unsafe_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _derived_validation_digest(value: object) -> str:
    payload = _payload_value(value)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a dict")
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    encoded = json.dumps(
        digest_payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _verify_payload_digest(payload: dict[str, Any]) -> None:
    _require_digest("derived_validation_digest", payload.get("derived_validation_digest"))
    if payload["derived_validation_digest"] != _derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")
