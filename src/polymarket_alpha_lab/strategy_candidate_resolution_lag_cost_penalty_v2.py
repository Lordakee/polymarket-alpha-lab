"""Phase 1 resolution-lag cost penalty model for paper strategy candidates."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_STRATEGY_CANDIDATE_RESOLUTION_LAG_COST_PENALTY_V2_CONFIG_VERSION = (
    "strategy-candidate-resolution-lag-cost-penalty-v2-phase1"
)

_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_VALUE_QUANT = Decimal("0.000001")
_COUNT_QUANT = Decimal("1")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_HOURS_PER_DAY = Decimal("24.000000")
_DAYS_PER_YEAR = Decimal("365.000000")

_STATUSES = ("pass", "watch", "blocked")
_UNSAFE_SURFACE_FIELD_FRAGMENTS = (
    "auth",
    "broker",
    "cancel",
    "exchange_mutation",
    "live",
    "order",
    "private_key",
    "replace",
    "sign",
    "trade",
    "wallet",
)
_STATUS_REASON_BY_STATUS = {
    "blocked": "resolution_lag_cost_penalty_blocked",
    "pass": "resolution_lag_cost_penalty_passed",
    "watch": "resolution_lag_cost_penalty_watch",
}
_STATUS_REASON_ORDER = ("blocked", "pass", "watch")
_COST_REASON_FIELDS = (
    ("resolution_delay_probability_cost", "resolution_delay_penalty_present"),
    ("capital_lockup_probability_cost", "capital_lockup_penalty_present"),
    ("stale_evidence_probability_cost", "stale_evidence_penalty_present"),
    (
        "settlement_ambiguity_probability_cost",
        "settlement_ambiguity_penalty_present",
    ),
    ("exit_friction_probability_cost", "exit_friction_penalty_present"),
)

__all__ = (
    "DEFAULT_STRATEGY_CANDIDATE_RESOLUTION_LAG_COST_PENALTY_V2_CONFIG_VERSION",
    "StrategyCandidateResolutionLagCostPenaltyV2Config",
    "StrategyCandidateResolutionLagCostPenaltyV2Candidate",
    "StrategyCandidateResolutionLagCostPenaltyV2Row",
    "StrategyCandidateResolutionLagCostPenaltyV2Report",
    "build_strategy_candidate_resolution_lag_cost_penalty_v2",
    "strategy_candidate_resolution_lag_cost_penalty_v2_payload",
    "strategy_candidate_resolution_lag_cost_penalty_v2_digest",
)


@dataclass(frozen=True)
class StrategyCandidateResolutionLagCostPenaltyV2Config:
    config_version: str = (
        DEFAULT_STRATEGY_CANDIDATE_RESOLUTION_LAG_COST_PENALTY_V2_CONFIG_VERSION
    )
    resolution_delay_penalty_per_day: Decimal = Decimal("0.001000")
    capital_lockup_apr: Decimal = Decimal("0.120000")
    stale_evidence_penalty_per_day: Decimal = Decimal("0.002000")
    settlement_ambiguity_penalty_weight: Decimal = Decimal("0.050000")
    exit_friction_penalty_weight: Decimal = Decimal("1.000000")
    watch_net_probability_edge: Decimal = Decimal("0.020000")
    max_pass_penalty_to_edge_ratio: Decimal = Decimal("0.500000")
    max_watch_penalty_to_edge_ratio: Decimal = Decimal("0.800000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_hard_flags("StrategyCandidateResolutionLagCostPenaltyV2Config", self)
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_string("config_version", self.config_version),
        )
        for field_name in (
            "resolution_delay_penalty_per_day",
            "capital_lockup_apr",
            "stale_evidence_penalty_per_day",
            "settlement_ambiguity_penalty_weight",
            "exit_friction_penalty_weight",
            "watch_net_probability_edge",
            "max_pass_penalty_to_edge_ratio",
            "max_watch_penalty_to_edge_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.max_pass_penalty_to_edge_ratio > self.max_watch_penalty_to_edge_ratio:
            raise ValueError(
                "max_pass_penalty_to_edge_ratio must be less than or equal to "
                "max_watch_penalty_to_edge_ratio",
            )
        _reject_unsafe_fields(
            "StrategyCandidateResolutionLagCostPenaltyV2Config",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class StrategyCandidateResolutionLagCostPenaltyV2Candidate:
    candidate_id: str
    market_slug: str
    observed_at: datetime
    expected_probability_edge: Decimal
    entry_probability: Decimal
    resolution_delay_hours: Decimal
    capital_lockup_days: Decimal
    stale_evidence_hours: Decimal
    settlement_ambiguity_score: Decimal
    exit_friction_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_hard_flags("StrategyCandidateResolutionLagCostPenaltyV2Candidate", self)
        for field_name in ("candidate_id", "market_slug"):
            object.__setattr__(
                self,
                field_name,
                _require_canonical_string(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "expected_probability_edge",
            "entry_probability",
            "settlement_ambiguity_score",
            "exit_friction_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "resolution_delay_hours",
            "capital_lockup_days",
            "stale_evidence_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _reject_unsafe_fields(
            "StrategyCandidateResolutionLagCostPenaltyV2Candidate",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class StrategyCandidateResolutionLagCostPenaltyV2Row:
    candidate_id: str
    market_slug: str
    observed_at: datetime
    expected_probability_edge: Decimal
    entry_probability: Decimal
    resolution_delay_hours: Decimal
    capital_lockup_days: Decimal
    stale_evidence_hours: Decimal
    settlement_ambiguity_score: Decimal
    exit_friction_score: Decimal
    resolution_delay_probability_cost: Decimal
    capital_lockup_probability_cost: Decimal
    stale_evidence_probability_cost: Decimal
    settlement_ambiguity_probability_cost: Decimal
    exit_friction_probability_cost: Decimal
    total_lag_probability_penalty: Decimal
    penalty_adjusted_probability_edge: Decimal
    penalty_to_edge_ratio: Decimal
    edge_shortfall: Decimal
    penalty_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_hard_flags("StrategyCandidateResolutionLagCostPenaltyV2Row", self)
        for field_name in ("candidate_id", "market_slug"):
            object.__setattr__(
                self,
                field_name,
                _require_canonical_string(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "expected_probability_edge",
            "entry_probability",
            "settlement_ambiguity_score",
            "exit_friction_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "resolution_delay_hours",
            "capital_lockup_days",
            "stale_evidence_hours",
            "resolution_delay_probability_cost",
            "capital_lockup_probability_cost",
            "stale_evidence_probability_cost",
            "settlement_ambiguity_probability_cost",
            "exit_friction_probability_cost",
            "total_lag_probability_penalty",
            "penalty_to_edge_ratio",
            "edge_shortfall",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "penalty_adjusted_probability_edge",
            _normalize_decimal(
                "penalty_adjusted_probability_edge",
                self.penalty_adjusted_probability_edge,
            ),
        )
        _require_member("penalty_status", self.penalty_status, _STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row(self)
        _reject_unsafe_fields(
            "StrategyCandidateResolutionLagCostPenaltyV2Row",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class StrategyCandidateResolutionLagCostPenaltyV2Report:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    total_lag_probability_penalty: Decimal
    max_total_lag_probability_penalty: Decimal
    min_penalty_adjusted_probability_edge: Decimal
    max_penalty_to_edge_ratio: Decimal
    max_edge_shortfall: Decimal
    status: str
    rows: tuple[StrategyCandidateResolutionLagCostPenaltyV2Row, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_hard_flags("StrategyCandidateResolutionLagCostPenaltyV2Report", self)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_string("config_version", self.config_version),
        )
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "total_lag_probability_penalty",
            "max_total_lag_probability_penalty",
            "max_penalty_to_edge_ratio",
            "max_edge_shortfall",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_penalty_adjusted_probability_edge",
            _normalize_decimal(
                "min_penalty_adjusted_probability_edge",
                self.min_penalty_adjusted_probability_edge,
            ),
        )
        _require_member("status", self.status, _STATUSES)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_report(self)
        _reject_unsafe_fields(
            "StrategyCandidateResolutionLagCostPenaltyV2Report",
            _payload_value(asdict(self)),
        )


def build_strategy_candidate_resolution_lag_cost_penalty_v2(
    candidates: object,
    *,
    config: StrategyCandidateResolutionLagCostPenaltyV2Config | None = None,
    generated_at: datetime,
) -> StrategyCandidateResolutionLagCostPenaltyV2Report:
    if config is None:
        config = StrategyCandidateResolutionLagCostPenaltyV2Config()
    if type(config) is not StrategyCandidateResolutionLagCostPenaltyV2Config:
        raise ValueError(
            "config must be a StrategyCandidateResolutionLagCostPenaltyV2Config",
        )
    _require_hard_flags("StrategyCandidateResolutionLagCostPenaltyV2Config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_candidates = _normalize_candidates_or_rows(candidates)
    for candidate in normalized_candidates:
        if candidate.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")
    rows = _sorted_rows(
        tuple(
            _row_from_item(candidate, config=config)
            for candidate in normalized_candidates
        ),
    )
    return StrategyCandidateResolutionLagCostPenaltyV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        candidate_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        total_lag_probability_penalty=_sum_decimal(
            row.total_lag_probability_penalty for row in rows
        ),
        max_total_lag_probability_penalty=_max_decimal(
            row.total_lag_probability_penalty for row in rows
        ),
        min_penalty_adjusted_probability_edge=_min_decimal(
            row.penalty_adjusted_probability_edge for row in rows
        ),
        max_penalty_to_edge_ratio=_max_decimal(row.penalty_to_edge_ratio for row in rows),
        max_edge_shortfall=_max_decimal(row.edge_shortfall for row in rows),
        status=_report_status(rows),
        rows=rows,
        reason_codes=_report_reason_codes(rows),
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def strategy_candidate_resolution_lag_cost_penalty_v2_payload(
    report: StrategyCandidateResolutionLagCostPenaltyV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyCandidateResolutionLagCostPenaltyV2Report:
        _require_hard_flags("StrategyCandidateResolutionLagCostPenaltyV2Report", report)
        payload = _payload_value(asdict(report))
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        _reject_unsafe_fields("strategy candidate resolution lag cost penalty payload", payload)
        return payload
    if type(report) is dict:
        copied = _copy_payload(report)
        _require_payload_flags(copied)
        _reject_unsafe_fields("strategy candidate resolution lag cost penalty payload", copied)
        return copied
    raise ValueError("report must be a StrategyCandidateResolutionLagCostPenaltyV2Report")


def strategy_candidate_resolution_lag_cost_penalty_v2_digest(
    report: StrategyCandidateResolutionLagCostPenaltyV2Report | dict[str, Any],
) -> str:
    payload = strategy_candidate_resolution_lag_cost_penalty_v2_payload(report)
    encoded = json.dumps(
        payload,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _row_from_item(
    item: StrategyCandidateResolutionLagCostPenaltyV2Candidate
    | StrategyCandidateResolutionLagCostPenaltyV2Row,
    *,
    config: StrategyCandidateResolutionLagCostPenaltyV2Config,
) -> StrategyCandidateResolutionLagCostPenaltyV2Row:
    if type(item) is StrategyCandidateResolutionLagCostPenaltyV2Row:
        _require_hard_flags("StrategyCandidateResolutionLagCostPenaltyV2Row", item)
        return item
    resolution_delay_probability_cost = _mul_div(
        item.resolution_delay_hours,
        config.resolution_delay_penalty_per_day,
        _HOURS_PER_DAY,
    )
    capital_lockup_probability_cost = _capital_lockup_cost(item, config)
    stale_evidence_probability_cost = _mul_div(
        item.stale_evidence_hours,
        config.stale_evidence_penalty_per_day,
        _HOURS_PER_DAY,
    )
    settlement_ambiguity_probability_cost = _quantize(
        item.settlement_ambiguity_score * config.settlement_ambiguity_penalty_weight,
    )
    exit_friction_probability_cost = _quantize(
        item.exit_friction_score * config.exit_friction_penalty_weight,
    )
    total_lag_probability_penalty = _sum_decimal(
        (
            resolution_delay_probability_cost,
            capital_lockup_probability_cost,
            stale_evidence_probability_cost,
            settlement_ambiguity_probability_cost,
            exit_friction_probability_cost,
        ),
    )
    penalty_adjusted_probability_edge = _quantize(
        item.expected_probability_edge - total_lag_probability_penalty,
    )
    penalty_to_edge_ratio = _ratio(
        total_lag_probability_penalty,
        item.expected_probability_edge,
    )
    edge_shortfall = (
        _quantize(-penalty_adjusted_probability_edge)
        if penalty_adjusted_probability_edge < _ZERO
        else _ZERO
    )
    penalty_status = _penalty_status(
        penalty_adjusted_probability_edge=penalty_adjusted_probability_edge,
        penalty_to_edge_ratio=penalty_to_edge_ratio,
        config=config,
    )
    return StrategyCandidateResolutionLagCostPenaltyV2Row(
        candidate_id=item.candidate_id,
        market_slug=item.market_slug,
        observed_at=item.observed_at,
        expected_probability_edge=item.expected_probability_edge,
        entry_probability=item.entry_probability,
        resolution_delay_hours=item.resolution_delay_hours,
        capital_lockup_days=item.capital_lockup_days,
        stale_evidence_hours=item.stale_evidence_hours,
        settlement_ambiguity_score=item.settlement_ambiguity_score,
        exit_friction_score=item.exit_friction_score,
        resolution_delay_probability_cost=resolution_delay_probability_cost,
        capital_lockup_probability_cost=capital_lockup_probability_cost,
        stale_evidence_probability_cost=stale_evidence_probability_cost,
        settlement_ambiguity_probability_cost=settlement_ambiguity_probability_cost,
        exit_friction_probability_cost=exit_friction_probability_cost,
        total_lag_probability_penalty=total_lag_probability_penalty,
        penalty_adjusted_probability_edge=penalty_adjusted_probability_edge,
        penalty_to_edge_ratio=penalty_to_edge_ratio,
        edge_shortfall=edge_shortfall,
        penalty_status=penalty_status,
        reason_codes=_row_reason_codes(
            item.reason_codes,
            penalty_status=penalty_status,
            resolution_delay_probability_cost=resolution_delay_probability_cost,
            capital_lockup_probability_cost=capital_lockup_probability_cost,
            stale_evidence_probability_cost=stale_evidence_probability_cost,
            settlement_ambiguity_probability_cost=settlement_ambiguity_probability_cost,
            exit_friction_probability_cost=exit_friction_probability_cost,
        ),
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _capital_lockup_cost(
    item: StrategyCandidateResolutionLagCostPenaltyV2Candidate,
    config: StrategyCandidateResolutionLagCostPenaltyV2Config,
) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(
            item.capital_lockup_days
            * config.capital_lockup_apr
            * item.entry_probability
            / _DAYS_PER_YEAR,
        )


def _penalty_status(
    *,
    penalty_adjusted_probability_edge: Decimal,
    penalty_to_edge_ratio: Decimal,
    config: StrategyCandidateResolutionLagCostPenaltyV2Config,
) -> str:
    if (
        penalty_adjusted_probability_edge < _ZERO
        or penalty_to_edge_ratio > config.max_watch_penalty_to_edge_ratio
    ):
        return "blocked"
    if (
        penalty_adjusted_probability_edge < config.watch_net_probability_edge
        or penalty_to_edge_ratio > config.max_pass_penalty_to_edge_ratio
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    candidate_reasons: tuple[str, ...],
    *,
    penalty_status: str,
    resolution_delay_probability_cost: Decimal,
    capital_lockup_probability_cost: Decimal,
    stale_evidence_probability_cost: Decimal,
    settlement_ambiguity_probability_cost: Decimal,
    exit_friction_probability_cost: Decimal,
) -> tuple[str, ...]:
    reason_codes = list(candidate_reasons)
    _append_unique(reason_codes, _STATUS_REASON_BY_STATUS[penalty_status])
    cost_by_field = {
        "resolution_delay_probability_cost": resolution_delay_probability_cost,
        "capital_lockup_probability_cost": capital_lockup_probability_cost,
        "stale_evidence_probability_cost": stale_evidence_probability_cost,
        "settlement_ambiguity_probability_cost": settlement_ambiguity_probability_cost,
        "exit_friction_probability_cost": exit_friction_probability_cost,
    }
    for field_name, reason_code in _COST_REASON_FIELDS:
        if cost_by_field[field_name] > _ZERO:
            _append_unique(reason_codes, reason_code)
    return tuple(reason_codes)


def _report_reason_codes(
    rows: tuple[StrategyCandidateResolutionLagCostPenaltyV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("resolution_lag_cost_penalty_empty",)
    reason_codes: list[str] = []
    row_statuses = {row.penalty_status for row in rows}
    for status in _STATUS_REASON_ORDER:
        if status in row_statuses:
            _append_unique(reason_codes, _STATUS_REASON_BY_STATUS[status])
    for field_name, reason_code in _COST_REASON_FIELDS:
        if any(getattr(row, field_name) > _ZERO for row in rows):
            _append_unique(reason_codes, reason_code)
    return tuple(reason_codes)


def _report_status(rows: tuple[StrategyCandidateResolutionLagCostPenaltyV2Row, ...]) -> str:
    if any(row.penalty_status == "blocked" for row in rows):
        return "blocked"
    if any(row.penalty_status == "watch" for row in rows):
        return "watch"
    if not rows:
        return "watch"
    return "pass"


def _sorted_rows(
    rows: tuple[StrategyCandidateResolutionLagCostPenaltyV2Row, ...],
) -> tuple[StrategyCandidateResolutionLagCostPenaltyV2Row, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                row.penalty_adjusted_probability_edge,
                -row.total_lag_probability_penalty,
                row.candidate_id,
                row.market_slug,
            ),
        ),
    )


def _normalize_candidates_or_rows(
    value: object,
) -> tuple[
    StrategyCandidateResolutionLagCostPenaltyV2Candidate
    | StrategyCandidateResolutionLagCostPenaltyV2Row,
    ...,
]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise ValueError("candidates must be an iterable")
    items = tuple(value)
    candidate_ids: list[str] = []
    for item in items:
        if type(item) not in (
            StrategyCandidateResolutionLagCostPenaltyV2Candidate,
            StrategyCandidateResolutionLagCostPenaltyV2Row,
        ):
            raise ValueError(
                "candidates must contain "
                "StrategyCandidateResolutionLagCostPenaltyV2Candidate values",
            )
        _require_hard_flags("candidate", item)
        candidate_ids.append(item.candidate_id)
    if len(set(candidate_ids)) != len(candidate_ids):
        raise ValueError("duplicate candidate_id values are not allowed")
    return items


def _normalize_rows(
    value: object,
) -> tuple[StrategyCandidateResolutionLagCostPenaltyV2Row, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in value:
        if type(row) is not StrategyCandidateResolutionLagCostPenaltyV2Row:
            raise ValueError("rows must contain StrategyCandidateResolutionLagCostPenaltyV2Row")
        _require_hard_flags("row", row)
    return value


def _validate_row(row: StrategyCandidateResolutionLagCostPenaltyV2Row) -> None:
    expected_total = _sum_decimal(
        (
            row.resolution_delay_probability_cost,
            row.capital_lockup_probability_cost,
            row.stale_evidence_probability_cost,
            row.settlement_ambiguity_probability_cost,
            row.exit_friction_probability_cost,
        ),
    )
    if row.total_lag_probability_penalty != expected_total:
        raise ValueError("total_lag_probability_penalty must match component costs")
    if row.penalty_adjusted_probability_edge != _quantize(
        row.expected_probability_edge - row.total_lag_probability_penalty,
    ):
        raise ValueError("penalty_adjusted_probability_edge must match edge minus penalty")
    if row.penalty_to_edge_ratio != _ratio(
        row.total_lag_probability_penalty,
        row.expected_probability_edge,
    ):
        raise ValueError("penalty_to_edge_ratio must match penalty and edge")
    expected_shortfall = (
        _quantize(-row.penalty_adjusted_probability_edge)
        if row.penalty_adjusted_probability_edge < _ZERO
        else _ZERO
    )
    if row.edge_shortfall != expected_shortfall:
        raise ValueError("edge_shortfall must match negative adjusted edge")
    expected_status_reason = _STATUS_REASON_BY_STATUS[row.penalty_status]
    if expected_status_reason not in row.reason_codes:
        raise ValueError("reason_codes must include penalty status")


def _validate_report(report: StrategyCandidateResolutionLagCostPenaltyV2Report) -> None:
    rows = report.rows
    if report.candidate_count != _count(len(rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.total_lag_probability_penalty != _sum_decimal(
        row.total_lag_probability_penalty for row in rows
    ):
        raise ValueError("total_lag_probability_penalty must match rows")
    if report.max_total_lag_probability_penalty != _max_decimal(
        row.total_lag_probability_penalty for row in rows
    ):
        raise ValueError("max_total_lag_probability_penalty must match rows")
    if report.min_penalty_adjusted_probability_edge != _min_decimal(
        row.penalty_adjusted_probability_edge for row in rows
    ):
        raise ValueError("min_penalty_adjusted_probability_edge must match rows")
    if report.max_penalty_to_edge_ratio != _max_decimal(
        row.penalty_to_edge_ratio for row in rows
    ):
        raise ValueError("max_penalty_to_edge_ratio must match rows")
    if report.max_edge_shortfall != _max_decimal(row.edge_shortfall for row in rows):
        raise ValueError("max_edge_shortfall must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if rows != _sorted_rows(rows):
        raise ValueError("rows must be sorted deterministically")


def _status_count(
    rows: tuple[StrategyCandidateResolutionLagCostPenaltyV2Row, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.penalty_status == status))


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        total = _ZERO
        for value in values:
            total += value
        return _quantize(total)


def _max_decimal(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return _ZERO
    return _quantize(max(items))


def _min_decimal(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return _ZERO
    return _quantize(min(items))


def _mul_div(numerator: Decimal, multiplier: Decimal, denominator: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(numerator * multiplier / denominator)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(_COUNT_QUANT)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_VALUE_QUANT)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    decimal = _require_decimal(field_name, value)
    if decimal < Decimal("0"):
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal != decimal.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return decimal.quantize(_COUNT_QUANT)


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    decimal = _require_decimal(field_name, value)
    if decimal.as_tuple().exponent < -6:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return _quantize(decimal)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    return value


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for item in value:
        code = _require_canonical_string(field_name, item)
        _append_unique(normalized, code)
    return tuple(normalized)


def _append_unique(values: list[str], value: str) -> None:
    if value not in values:
        values.append(value)


def _payload_value(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(asdict(value))
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) is dict:
        payload: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            payload[key] = _payload_value(item)
        return payload
    if type(value) in (list, tuple):
        return [_payload_value(item) for item in value]
    if value is None or type(value) in (str, bool, int):
        return value
    if type(value) is float:
        raise ValueError("payload values must not be floats")
    raise ValueError("payload values must be JSON-compatible")


def _copy_payload(value: object) -> dict[str, Any]:
    copied = _copy_payload_value(value)
    if type(copied) is not dict:
        raise ValueError("payload must be a dict")
    return copied


def _copy_payload_value(value: object) -> Any:
    if type(value) is dict:
        copied: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            copied[key] = _copy_payload_value(item)
        return copied
    if type(value) is list:
        return [_copy_payload_value(item) for item in value]
    if value is None or type(value) in (str, bool):
        return value
    if type(value) in (int, float) and type(value) is not bool:
        raise ValueError("payload numeric values must be Decimal strings")
    raise ValueError("payload values must be JSON scalars")


def _require_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"payload {field_name} must be True")


def _reject_unsafe_fields(label: str, payload: object) -> None:
    for key in _iter_payload_keys(payload):
        lowered = key.lower()
        if any(fragment in lowered for fragment in _UNSAFE_SURFACE_FIELD_FRAGMENTS):
            raise ValueError(f"unsafe surface field in {label}: {key}")


def _iter_payload_keys(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_payload_keys(asdict(value))
    if type(value) is dict:
        keys: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            keys.append(key)
            keys.extend(_iter_payload_keys(item))
        return tuple(keys)
    if type(value) in (list, tuple):
        keys = []
        for item in value:
            keys.extend(_iter_payload_keys(item))
        return tuple(keys)
    return ()
