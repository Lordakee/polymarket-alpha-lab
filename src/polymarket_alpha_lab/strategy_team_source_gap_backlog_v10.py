"""Pure readonly strategy team source gap backlog v10 reducer."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    UNSAFE_SURFACE_FIELD_FRAGMENTS,
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_STRATEGY_TEAM_SOURCE_GAP_BACKLOG_V10_CONFIG_VERSION = (
    "strategy-team-source-gap-backlog-v10"
)

COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
STALENESS_WEIGHT = Decimal("0.200000")
SOURCE_QUORUM_WEIGHT = Decimal("0.300000")
DISAGREEMENT_WEIGHT = Decimal("0.200000")
MARKET_URGENCY_WEIGHT = Decimal("0.200000")
CAPACITY_WEIGHT = Decimal("0.100000")
MEDIUM_PRIORITY_SCORE_THRESHOLD = Decimal("0.150000")

VALIDATION_DIGEST_ALGORITHM = "sha256"
HEX_DIGITS = frozenset("0123456789abcdef")

PRIORITY_BANDS = ("low", "medium", "high", "critical")
PRIORITY_STATUSES = ("clear", "low", "medium", "high", "critical")
RECOMMENDED_ACTIONS = (
    "monitor_source_backlog",
    "queue_source_gap_review",
    "assign_specialist_source_repair",
    "pause_market_until_source_gap_repaired",
)
ROW_REASON_CODES = (
    "team_source_gap_backlog_v10_clear",
    "team_source_gap_backlog_v10_stale_packets",
    "team_source_gap_backlog_v10_missing_source_quorum",
    "team_source_gap_backlog_v10_disagreement_backlog",
    "team_source_gap_backlog_v10_urgent_market",
    "team_source_gap_backlog_v10_specialist_capacity_shortfall",
)
REPORT_REASON_CODES = (
    "team_source_gap_backlog_v10_clear",
    "team_source_gap_backlog_v10_stale_packets",
    "team_source_gap_backlog_v10_missing_source_quorum",
    "team_source_gap_backlog_v10_disagreement_backlog",
    "team_source_gap_backlog_v10_urgent_market",
    "team_source_gap_backlog_v10_specialist_capacity_shortfall",
    "team_source_gap_backlog_v10_high_priority_present",
    "team_source_gap_backlog_v10_critical_priority_present",
)


@dataclass(frozen=True)
class StrategyTeamSourceGapBacklogV10Config:
    config_version: str = DEFAULT_STRATEGY_TEAM_SOURCE_GAP_BACKLOG_V10_CONFIG_VERSION
    stale_packet_pressure_count: Decimal = Decimal("3")
    disagreement_pressure_count: Decimal = Decimal("3")
    urgent_resolution_hours: Decimal = Decimal("6.000000")
    near_resolution_hours: Decimal = Decimal("24.000000")
    high_priority_score_threshold: Decimal = Decimal("0.350000")
    critical_priority_score_threshold: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("config", self, StrategyTeamSourceGapBacklogV10Config)
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "stale_packet_pressure_count",
            "disagreement_pressure_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("urgent_resolution_hours", "near_resolution_hours"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "high_priority_score_threshold",
            "critical_priority_score_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.urgent_resolution_hours >= self.near_resolution_hours:
            raise ValueError("near_resolution_hours must exceed urgent_resolution_hours")
        if self.high_priority_score_threshold > self.critical_priority_score_threshold:
            raise ValueError(
                "critical_priority_score_threshold must be at least "
                "high_priority_score_threshold",
            )
        _reject_unsafe_public_payload("config", self)
        _require_safety_flags("config", self)


@dataclass(frozen=True)
class StrategyTeamSourceGapBacklogV10Input:
    backlog_id: str
    team_id: str
    market_slug: str
    stale_packet_count: Decimal
    required_source_count: Decimal
    current_source_count: Decimal
    disagreement_backlog_count: Decimal
    hours_to_resolution: Decimal
    available_specialist_minutes: Decimal
    estimated_repair_minutes: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("input", self, StrategyTeamSourceGapBacklogV10Input)
        for field_name in ("backlog_id", "team_id", "market_slug"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "stale_packet_count",
            "current_source_count",
            "disagreement_backlog_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "required_source_count",
            _normalize_positive_count(
                "required_source_count",
                self.required_source_count,
            ),
        )
        for field_name in (
            "hours_to_resolution",
            "available_specialist_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "estimated_repair_minutes",
            _normalize_positive_decimal(
                "estimated_repair_minutes",
                self.estimated_repair_minutes,
            ),
        )
        _reject_unsafe_public_payload("input", self)
        _require_safety_flags("input", self)


@dataclass(frozen=True)
class StrategyTeamSourceGapBacklogV10Row:
    backlog_id: str
    team_id: str
    market_slug: str
    stale_packet_count: Decimal
    required_source_count: Decimal
    current_source_count: Decimal
    missing_source_count: Decimal
    disagreement_backlog_count: Decimal
    hours_to_resolution: Decimal
    available_specialist_minutes: Decimal
    estimated_repair_minutes: Decimal
    stale_packet_pressure: Decimal
    source_quorum_gap_ratio: Decimal
    disagreement_pressure: Decimal
    market_urgency: Decimal
    capacity_coverage_ratio: Decimal
    capacity_shortfall_minutes: Decimal
    capacity_shortfall_ratio: Decimal
    backlog_priority_score: Decimal
    priority_band: str
    recommended_action: str
    reason_codes: tuple[str, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("row", self, StrategyTeamSourceGapBacklogV10Row)
        for field_name in ("backlog_id", "team_id", "market_slug"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "stale_packet_count",
            "required_source_count",
            "current_source_count",
            "missing_source_count",
            "disagreement_backlog_count",
        ):
            normalizer = (
                _normalize_positive_count
                if field_name == "required_source_count"
                else _normalize_nonnegative_count
            )
            object.__setattr__(
                self,
                field_name,
                normalizer(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "hours_to_resolution",
            "available_specialist_minutes",
            "capacity_shortfall_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "estimated_repair_minutes",
            _normalize_positive_decimal(
                "estimated_repair_minutes",
                self.estimated_repair_minutes,
            ),
        )
        for field_name in (
            "stale_packet_pressure",
            "source_quorum_gap_ratio",
            "disagreement_pressure",
            "market_urgency",
            "capacity_coverage_ratio",
            "capacity_shortfall_ratio",
            "backlog_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member("priority_band", self.priority_band, PRIORITY_BANDS)
        _require_member("recommended_action", self.recommended_action, RECOMMENDED_ACTIONS)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        object.__setattr__(
            self,
            "validation_digest",
            _require_validation_digest("validation_digest", self.validation_digest),
        )
        _validate_row(self)
        _validate_row_digest(self)
        _reject_unsafe_public_payload("row", self)
        _require_safety_flags("row", self)

    @property
    def payload(self) -> dict[str, Any]:
        return _row_payload(self)


@dataclass(frozen=True)
class StrategyTeamSourceGapBacklogV10Report:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    backlog_item_count: Decimal
    critical_priority_count: Decimal
    high_priority_count: Decimal
    medium_priority_count: Decimal
    low_priority_count: Decimal
    total_missing_source_count: Decimal
    total_stale_packet_count: Decimal
    total_disagreement_backlog_count: Decimal
    total_estimated_repair_minutes: Decimal
    total_available_specialist_minutes: Decimal
    max_backlog_priority_score: Decimal
    mean_backlog_priority_score: Decimal
    priority_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyTeamSourceGapBacklogV10Row, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("report", self, StrategyTeamSourceGapBacklogV10Report)
        object.__setattr__(self, "generated_at", _as_exact_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "input_count",
            "backlog_item_count",
            "critical_priority_count",
            "high_priority_count",
            "medium_priority_count",
            "low_priority_count",
            "total_missing_source_count",
            "total_stale_packet_count",
            "total_disagreement_backlog_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "total_estimated_repair_minutes",
            "total_available_specialist_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_backlog_priority_score", "mean_backlog_priority_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member("priority_status", self.priority_status, PRIORITY_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "validation_digest",
            _require_validation_digest("validation_digest", self.validation_digest),
        )
        _validate_report(self)
        _validate_report_digest(self)
        _reject_unsafe_public_payload("report", self)
        _require_safety_flags("report", self)

    @property
    def payload(self) -> dict[str, Any]:
        return strategy_team_source_gap_backlog_v10_payload(self)


def build_strategy_team_source_gap_backlog_v10_report(
    rows: list[StrategyTeamSourceGapBacklogV10Input]
    | tuple[StrategyTeamSourceGapBacklogV10Input, ...],
    *,
    config: StrategyTeamSourceGapBacklogV10Config,
    generated_at: datetime,
) -> StrategyTeamSourceGapBacklogV10Report:
    if type(config) is not StrategyTeamSourceGapBacklogV10Config:
        raise ValueError("config must be a StrategyTeamSourceGapBacklogV10Config")
    _reject_unsafe_public_payload("config", config)
    _require_safety_flags("config", config)
    generated_at_utc = _as_exact_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(rows)
    report_rows = tuple(
        sorted(
            (_build_row(row, config) for row in input_rows),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(report_rows)
    priority_status = _report_priority_status(report_rows)
    return StrategyTeamSourceGapBacklogV10Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_count_from_length(len(input_rows)),
        backlog_item_count=_count_from_length(len(report_rows)),
        critical_priority_count=_priority_count(report_rows, "critical"),
        high_priority_count=_priority_count(report_rows, "high"),
        medium_priority_count=_priority_count(report_rows, "medium"),
        low_priority_count=_priority_count(report_rows, "low"),
        total_missing_source_count=_sum_count(
            row.missing_source_count for row in report_rows
        ),
        total_stale_packet_count=_sum_count(
            row.stale_packet_count for row in report_rows
        ),
        total_disagreement_backlog_count=_sum_count(
            row.disagreement_backlog_count for row in report_rows
        ),
        total_estimated_repair_minutes=_sum_decimal(
            row.estimated_repair_minutes for row in report_rows
        ),
        total_available_specialist_minutes=_sum_decimal(
            row.available_specialist_minutes for row in report_rows
        ),
        max_backlog_priority_score=_max_priority_score(report_rows),
        mean_backlog_priority_score=_mean_priority_score(report_rows),
        priority_status=priority_status,
        reason_codes=reason_codes,
        rows=report_rows,
        validation_digest=_report_validation_digest(
            generated_at=generated_at_utc,
            config_version=config.config_version,
            input_count=_count_from_length(len(input_rows)),
            backlog_item_count=_count_from_length(len(report_rows)),
            critical_priority_count=_priority_count(report_rows, "critical"),
            high_priority_count=_priority_count(report_rows, "high"),
            medium_priority_count=_priority_count(report_rows, "medium"),
            low_priority_count=_priority_count(report_rows, "low"),
            total_missing_source_count=_sum_count(
                row.missing_source_count for row in report_rows
            ),
            total_stale_packet_count=_sum_count(
                row.stale_packet_count for row in report_rows
            ),
            total_disagreement_backlog_count=_sum_count(
                row.disagreement_backlog_count for row in report_rows
            ),
            total_estimated_repair_minutes=_sum_decimal(
                row.estimated_repair_minutes for row in report_rows
            ),
            total_available_specialist_minutes=_sum_decimal(
                row.available_specialist_minutes for row in report_rows
            ),
            max_backlog_priority_score=_max_priority_score(report_rows),
            mean_backlog_priority_score=_mean_priority_score(report_rows),
            priority_status=priority_status,
            reason_codes=reason_codes,
            rows=report_rows,
        ),
    )


def strategy_team_source_gap_backlog_v10_payload(
    report: StrategyTeamSourceGapBacklogV10Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is dict:
        return _validated_public_payload(report)
    if type(report) is not StrategyTeamSourceGapBacklogV10Report:
        raise ValueError("report must be a StrategyTeamSourceGapBacklogV10Report")
    _reject_unsafe_public_payload("report", report)
    _require_safety_flags("report", report)
    payload = _report_payload(report)
    return _validated_public_payload(payload)


def _build_row(
    item: StrategyTeamSourceGapBacklogV10Input,
    config: StrategyTeamSourceGapBacklogV10Config,
) -> StrategyTeamSourceGapBacklogV10Row:
    missing_source_count = _missing_source_count(item)
    stale_packet_pressure = _pressure_ratio(
        item.stale_packet_count,
        config.stale_packet_pressure_count,
    )
    source_quorum_gap_ratio = _pressure_ratio(
        missing_source_count,
        item.required_source_count,
    )
    disagreement_pressure = _pressure_ratio(
        item.disagreement_backlog_count,
        config.disagreement_pressure_count,
    )
    market_urgency = _market_urgency(item, config)
    capacity_coverage_ratio = _capacity_coverage_ratio(item)
    capacity_shortfall_minutes = _capacity_shortfall_minutes(item)
    capacity_shortfall_ratio = _pressure_ratio(
        capacity_shortfall_minutes,
        item.estimated_repair_minutes,
    )
    backlog_priority_score = _backlog_priority_score(
        stale_packet_pressure=stale_packet_pressure,
        source_quorum_gap_ratio=source_quorum_gap_ratio,
        disagreement_pressure=disagreement_pressure,
        market_urgency=market_urgency,
        capacity_shortfall_ratio=capacity_shortfall_ratio,
    )
    priority_band = _priority_band(backlog_priority_score, config)
    reason_codes = _row_reason_codes(
        stale_packet_count=item.stale_packet_count,
        missing_source_count=missing_source_count,
        disagreement_backlog_count=item.disagreement_backlog_count,
        hours_to_resolution=item.hours_to_resolution,
        capacity_shortfall_minutes=capacity_shortfall_minutes,
        config=config,
    )
    return StrategyTeamSourceGapBacklogV10Row(
        backlog_id=item.backlog_id,
        team_id=item.team_id,
        market_slug=item.market_slug,
        stale_packet_count=item.stale_packet_count,
        required_source_count=item.required_source_count,
        current_source_count=item.current_source_count,
        missing_source_count=missing_source_count,
        disagreement_backlog_count=item.disagreement_backlog_count,
        hours_to_resolution=item.hours_to_resolution,
        available_specialist_minutes=item.available_specialist_minutes,
        estimated_repair_minutes=item.estimated_repair_minutes,
        stale_packet_pressure=stale_packet_pressure,
        source_quorum_gap_ratio=source_quorum_gap_ratio,
        disagreement_pressure=disagreement_pressure,
        market_urgency=market_urgency,
        capacity_coverage_ratio=capacity_coverage_ratio,
        capacity_shortfall_minutes=capacity_shortfall_minutes,
        capacity_shortfall_ratio=capacity_shortfall_ratio,
        backlog_priority_score=backlog_priority_score,
        priority_band=priority_band,
        recommended_action=_recommended_action(priority_band),
        reason_codes=reason_codes,
        validation_digest=_row_validation_digest(
            backlog_id=item.backlog_id,
            team_id=item.team_id,
            market_slug=item.market_slug,
            stale_packet_count=item.stale_packet_count,
            required_source_count=item.required_source_count,
            current_source_count=item.current_source_count,
            missing_source_count=missing_source_count,
            disagreement_backlog_count=item.disagreement_backlog_count,
            hours_to_resolution=item.hours_to_resolution,
            available_specialist_minutes=item.available_specialist_minutes,
            estimated_repair_minutes=item.estimated_repair_minutes,
            stale_packet_pressure=stale_packet_pressure,
            source_quorum_gap_ratio=source_quorum_gap_ratio,
            disagreement_pressure=disagreement_pressure,
            market_urgency=market_urgency,
            capacity_coverage_ratio=capacity_coverage_ratio,
            capacity_shortfall_minutes=capacity_shortfall_minutes,
            capacity_shortfall_ratio=capacity_shortfall_ratio,
            backlog_priority_score=backlog_priority_score,
            priority_band=priority_band,
            recommended_action=_recommended_action(priority_band),
            reason_codes=reason_codes,
        ),
    )


def _missing_source_count(item: StrategyTeamSourceGapBacklogV10Input) -> Decimal:
    missing_count = item.required_source_count - item.current_source_count
    if missing_count <= ZERO_COUNT:
        return ZERO_COUNT
    return _normalize_nonnegative_count("missing_source_count", missing_count)


def _pressure_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    with localcontext() as context:
        context.prec = len("9999999999999999999999999999999999999999999999999999999999999999")
        return _cap_probability(numerator / denominator)


def _market_urgency(
    item: StrategyTeamSourceGapBacklogV10Input,
    config: StrategyTeamSourceGapBacklogV10Config,
) -> Decimal:
    if item.hours_to_resolution <= config.urgent_resolution_hours:
        return ONE
    if item.hours_to_resolution >= config.near_resolution_hours:
        return ZERO
    with localcontext() as context:
        context.prec = len("9999999999999999999999999999999999999999999999999999999999999999")
        span = config.near_resolution_hours - config.urgent_resolution_hours
        remaining = config.near_resolution_hours - item.hours_to_resolution
        return _cap_probability(remaining / span)


def _capacity_coverage_ratio(item: StrategyTeamSourceGapBacklogV10Input) -> Decimal:
    return _pressure_ratio(
        item.available_specialist_minutes,
        item.estimated_repair_minutes,
    )


def _capacity_shortfall_minutes(item: StrategyTeamSourceGapBacklogV10Input) -> Decimal:
    shortfall = item.estimated_repair_minutes - item.available_specialist_minutes
    if shortfall <= ZERO:
        return ZERO
    return _normalize_nonnegative_decimal("capacity_shortfall_minutes", shortfall)


def _backlog_priority_score(
    *,
    stale_packet_pressure: Decimal,
    source_quorum_gap_ratio: Decimal,
    disagreement_pressure: Decimal,
    market_urgency: Decimal,
    capacity_shortfall_ratio: Decimal,
) -> Decimal:
    with localcontext() as context:
        context.prec = len("9999999999999999999999999999999999999999999999999999999999999999")
        score = (
            stale_packet_pressure * STALENESS_WEIGHT
            + source_quorum_gap_ratio * SOURCE_QUORUM_WEIGHT
            + disagreement_pressure * DISAGREEMENT_WEIGHT
            + market_urgency * MARKET_URGENCY_WEIGHT
            + capacity_shortfall_ratio * CAPACITY_WEIGHT
        )
        return _cap_probability(score)


def _priority_band(
    score: Decimal,
    config: StrategyTeamSourceGapBacklogV10Config,
) -> str:
    if score >= config.critical_priority_score_threshold:
        return "critical"
    if score >= config.high_priority_score_threshold:
        return "high"
    if score >= MEDIUM_PRIORITY_SCORE_THRESHOLD:
        return "medium"
    return "low"


def _recommended_action(priority_band: str) -> str:
    if priority_band == "critical":
        return "pause_market_until_source_gap_repaired"
    if priority_band == "high":
        return "assign_specialist_source_repair"
    if priority_band == "medium":
        return "queue_source_gap_review"
    return "monitor_source_backlog"


def _row_reason_codes(
    *,
    stale_packet_count: Decimal,
    missing_source_count: Decimal,
    disagreement_backlog_count: Decimal,
    hours_to_resolution: Decimal,
    capacity_shortfall_minutes: Decimal,
    config: StrategyTeamSourceGapBacklogV10Config,
) -> tuple[str, ...]:
    codes: list[str] = []
    if stale_packet_count > ZERO_COUNT:
        codes.append("team_source_gap_backlog_v10_stale_packets")
    if missing_source_count > ZERO_COUNT:
        codes.append("team_source_gap_backlog_v10_missing_source_quorum")
    if disagreement_backlog_count > ZERO_COUNT:
        codes.append("team_source_gap_backlog_v10_disagreement_backlog")
    if hours_to_resolution <= config.near_resolution_hours:
        codes.append("team_source_gap_backlog_v10_urgent_market")
    if capacity_shortfall_minutes > ZERO:
        codes.append("team_source_gap_backlog_v10_specialist_capacity_shortfall")
    if not codes:
        codes.append("team_source_gap_backlog_v10_clear")
    return _normalize_reason_codes("reason_codes", tuple(codes), ROW_REASON_CODES)


def _report_reason_codes(
    rows: tuple[StrategyTeamSourceGapBacklogV10Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("team_source_gap_backlog_v10_clear",)
    row_codes = tuple(reason_code for row in rows for reason_code in row.reason_codes)
    codes = [
        reason_code
        for reason_code in ROW_REASON_CODES
        if reason_code in row_codes and reason_code != "team_source_gap_backlog_v10_clear"
    ]
    if any(row.priority_band == "high" for row in rows):
        codes.append("team_source_gap_backlog_v10_high_priority_present")
    if any(row.priority_band == "critical" for row in rows):
        codes.append("team_source_gap_backlog_v10_critical_priority_present")
    if not codes:
        codes.append("team_source_gap_backlog_v10_clear")
    return _normalize_reason_codes("reason_codes", tuple(codes), REPORT_REASON_CODES)


def _report_priority_status(rows: tuple[StrategyTeamSourceGapBacklogV10Row, ...]) -> str:
    if not rows:
        return "clear"
    if any(row.priority_band == "critical" for row in rows):
        return "critical"
    if any(row.priority_band == "high" for row in rows):
        return "high"
    if any(row.priority_band == "medium" for row in rows):
        return "medium"
    return "low"


def _row_sort_key(
    row: StrategyTeamSourceGapBacklogV10Row,
) -> tuple[Decimal, Decimal, Decimal, str]:
    return (
        -row.backlog_priority_score,
        -row.missing_source_count,
        -row.stale_packet_count,
        row.backlog_id,
    )


def _normalize_inputs(
    rows: list[StrategyTeamSourceGapBacklogV10Input]
    | tuple[StrategyTeamSourceGapBacklogV10Input, ...],
) -> tuple[StrategyTeamSourceGapBacklogV10Input, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not StrategyTeamSourceGapBacklogV10Input:
            raise ValueError(
                "rows must contain StrategyTeamSourceGapBacklogV10Input values",
            )
        _reject_unsafe_public_payload("row", row)
        _require_safety_flags("row", row)
        if row.backlog_id in seen:
            raise ValueError("duplicate backlog_id")
        seen.add(row.backlog_id)
    return normalized


def _normalize_rows(
    rows: tuple[StrategyTeamSourceGapBacklogV10Row, ...],
) -> tuple[StrategyTeamSourceGapBacklogV10Row, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not StrategyTeamSourceGapBacklogV10Row:
            raise ValueError("rows must contain StrategyTeamSourceGapBacklogV10Row values")
        _reject_unsafe_public_payload("row", row)
        _require_safety_flags("row", row)
    return rows


def _priority_count(
    rows: tuple[StrategyTeamSourceGapBacklogV10Row, ...],
    priority_band: str,
) -> Decimal:
    return _sum_count(ONE_COUNT for row in rows if row.priority_band == priority_band)


def _sum_count(values: Any) -> Decimal:
    return _normalize_nonnegative_count("count", sum(values, ZERO_COUNT))


def _sum_decimal(values: Any) -> Decimal:
    return _normalize_nonnegative_decimal("total", sum(values, ZERO))


def _max_priority_score(rows: tuple[StrategyTeamSourceGapBacklogV10Row, ...]) -> Decimal:
    if not rows:
        return ZERO
    return max(row.backlog_priority_score for row in rows)


def _mean_priority_score(rows: tuple[StrategyTeamSourceGapBacklogV10Row, ...]) -> Decimal:
    if not rows:
        return ZERO
    with localcontext() as context:
        context.prec = len("9999999999999999999999999999999999999999999999999999999999999999")
        return _quantize_ratio(
            sum((row.backlog_priority_score for row in rows), ZERO)
            / Decimal(str(len(rows))),
        )


def _count_from_length(value: object) -> Decimal:
    return Decimal(str(value)).quantize(COUNT_QUANTUM)


ONE_COUNT = COUNT_QUANTUM


def _validate_row(row: StrategyTeamSourceGapBacklogV10Row) -> None:
    input_row = StrategyTeamSourceGapBacklogV10Input(
        backlog_id=row.backlog_id,
        team_id=row.team_id,
        market_slug=row.market_slug,
        stale_packet_count=row.stale_packet_count,
        required_source_count=row.required_source_count,
        current_source_count=row.current_source_count,
        disagreement_backlog_count=row.disagreement_backlog_count,
        hours_to_resolution=row.hours_to_resolution,
        available_specialist_minutes=row.available_specialist_minutes,
        estimated_repair_minutes=row.estimated_repair_minutes,
    )
    expected_missing_source_count = _missing_source_count(input_row)
    if row.missing_source_count != expected_missing_source_count:
        raise ValueError("missing_source_count must match row inputs")
    config = StrategyTeamSourceGapBacklogV10Config()
    expected_stale_packet_pressure = _pressure_ratio(
        row.stale_packet_count,
        config.stale_packet_pressure_count,
    )
    if row.stale_packet_pressure != expected_stale_packet_pressure:
        raise ValueError("stale_packet_pressure must match row inputs")
    expected_source_quorum_gap_ratio = _pressure_ratio(
        expected_missing_source_count,
        row.required_source_count,
    )
    if row.source_quorum_gap_ratio != expected_source_quorum_gap_ratio:
        raise ValueError("source_quorum_gap_ratio must match row inputs")
    expected_disagreement_pressure = _pressure_ratio(
        row.disagreement_backlog_count,
        config.disagreement_pressure_count,
    )
    if row.disagreement_pressure != expected_disagreement_pressure:
        raise ValueError("disagreement_pressure must match row inputs")
    expected_market_urgency = _market_urgency(input_row, config)
    if row.market_urgency != expected_market_urgency:
        raise ValueError("market_urgency must match row inputs")
    expected_capacity_coverage_ratio = _capacity_coverage_ratio(input_row)
    if row.capacity_coverage_ratio != expected_capacity_coverage_ratio:
        raise ValueError("capacity_coverage_ratio must match row inputs")
    expected_capacity_shortfall_minutes = _capacity_shortfall_minutes(input_row)
    if row.capacity_shortfall_minutes != expected_capacity_shortfall_minutes:
        raise ValueError("capacity_shortfall_minutes must match row inputs")
    expected_capacity_shortfall_ratio = _pressure_ratio(
        expected_capacity_shortfall_minutes,
        row.estimated_repair_minutes,
    )
    if row.capacity_shortfall_ratio != expected_capacity_shortfall_ratio:
        raise ValueError("capacity_shortfall_ratio must match row inputs")
    expected_backlog_priority_score = _backlog_priority_score(
        stale_packet_pressure=row.stale_packet_pressure,
        source_quorum_gap_ratio=row.source_quorum_gap_ratio,
        disagreement_pressure=row.disagreement_pressure,
        market_urgency=row.market_urgency,
        capacity_shortfall_ratio=row.capacity_shortfall_ratio,
    )
    if row.backlog_priority_score != expected_backlog_priority_score:
        raise ValueError("backlog_priority_score must match row inputs")
    expected_priority_band = _priority_band(expected_backlog_priority_score, config)
    if row.priority_band != expected_priority_band:
        raise ValueError("priority_band must match backlog_priority_score")
    expected_recommended_action = _recommended_action(expected_priority_band)
    if row.recommended_action != expected_recommended_action:
        raise ValueError("recommended_action must match priority_band")
    expected_reason_codes = _row_reason_codes(
        stale_packet_count=row.stale_packet_count,
        missing_source_count=expected_missing_source_count,
        disagreement_backlog_count=row.disagreement_backlog_count,
        hours_to_resolution=row.hours_to_resolution,
        capacity_shortfall_minutes=expected_capacity_shortfall_minutes,
        config=config,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row inputs")


def _validate_report(report: StrategyTeamSourceGapBacklogV10Report) -> None:
    if report.backlog_item_count != _count_from_length(len(report.rows)):
        raise ValueError("backlog_item_count must match rows")
    if report.input_count != report.backlog_item_count:
        raise ValueError("input_count must match backlog_item_count")
    if report.critical_priority_count != _priority_count(report.rows, "critical"):
        raise ValueError("critical_priority_count must match rows")
    if report.high_priority_count != _priority_count(report.rows, "high"):
        raise ValueError("high_priority_count must match rows")
    if report.medium_priority_count != _priority_count(report.rows, "medium"):
        raise ValueError("medium_priority_count must match rows")
    if report.low_priority_count != _priority_count(report.rows, "low"):
        raise ValueError("low_priority_count must match rows")
    if report.total_missing_source_count != _sum_count(
        row.missing_source_count for row in report.rows
    ):
        raise ValueError("total_missing_source_count must match rows")
    if report.total_stale_packet_count != _sum_count(
        row.stale_packet_count for row in report.rows
    ):
        raise ValueError("total_stale_packet_count must match rows")
    if report.total_disagreement_backlog_count != _sum_count(
        row.disagreement_backlog_count for row in report.rows
    ):
        raise ValueError("total_disagreement_backlog_count must match rows")
    if report.total_estimated_repair_minutes != _sum_decimal(
        row.estimated_repair_minutes for row in report.rows
    ):
        raise ValueError("total_estimated_repair_minutes must match rows")
    if report.total_available_specialist_minutes != _sum_decimal(
        row.available_specialist_minutes for row in report.rows
    ):
        raise ValueError("total_available_specialist_minutes must match rows")
    if report.max_backlog_priority_score != _max_priority_score(report.rows):
        raise ValueError("max_backlog_priority_score must match rows")
    if report.mean_backlog_priority_score != _mean_priority_score(report.rows):
        raise ValueError("mean_backlog_priority_score must match rows")
    if report.priority_status != _report_priority_status(report.rows):
        raise ValueError("priority_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be deterministic")


def _validate_row_digest(row: StrategyTeamSourceGapBacklogV10Row) -> None:
    expected_digest = _row_validation_digest(
        backlog_id=row.backlog_id,
        team_id=row.team_id,
        market_slug=row.market_slug,
        stale_packet_count=row.stale_packet_count,
        required_source_count=row.required_source_count,
        current_source_count=row.current_source_count,
        missing_source_count=row.missing_source_count,
        disagreement_backlog_count=row.disagreement_backlog_count,
        hours_to_resolution=row.hours_to_resolution,
        available_specialist_minutes=row.available_specialist_minutes,
        estimated_repair_minutes=row.estimated_repair_minutes,
        stale_packet_pressure=row.stale_packet_pressure,
        source_quorum_gap_ratio=row.source_quorum_gap_ratio,
        disagreement_pressure=row.disagreement_pressure,
        market_urgency=row.market_urgency,
        capacity_coverage_ratio=row.capacity_coverage_ratio,
        capacity_shortfall_minutes=row.capacity_shortfall_minutes,
        capacity_shortfall_ratio=row.capacity_shortfall_ratio,
        backlog_priority_score=row.backlog_priority_score,
        priority_band=row.priority_band,
        recommended_action=row.recommended_action,
        reason_codes=row.reason_codes,
    )
    if row.validation_digest != expected_digest:
        raise ValueError("validation_digest must match row")


def _validate_report_digest(report: StrategyTeamSourceGapBacklogV10Report) -> None:
    expected_digest = _report_validation_digest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        input_count=report.input_count,
        backlog_item_count=report.backlog_item_count,
        critical_priority_count=report.critical_priority_count,
        high_priority_count=report.high_priority_count,
        medium_priority_count=report.medium_priority_count,
        low_priority_count=report.low_priority_count,
        total_missing_source_count=report.total_missing_source_count,
        total_stale_packet_count=report.total_stale_packet_count,
        total_disagreement_backlog_count=report.total_disagreement_backlog_count,
        total_estimated_repair_minutes=report.total_estimated_repair_minutes,
        total_available_specialist_minutes=report.total_available_specialist_minutes,
        max_backlog_priority_score=report.max_backlog_priority_score,
        mean_backlog_priority_score=report.mean_backlog_priority_score,
        priority_status=report.priority_status,
        reason_codes=report.reason_codes,
        rows=report.rows,
    )
    if report.validation_digest != expected_digest:
        raise ValueError("validation_digest must match report")


def _row_validation_digest(
    *,
    backlog_id: str,
    team_id: str,
    market_slug: str,
    stale_packet_count: Decimal,
    required_source_count: Decimal,
    current_source_count: Decimal,
    missing_source_count: Decimal,
    disagreement_backlog_count: Decimal,
    hours_to_resolution: Decimal,
    available_specialist_minutes: Decimal,
    estimated_repair_minutes: Decimal,
    stale_packet_pressure: Decimal,
    source_quorum_gap_ratio: Decimal,
    disagreement_pressure: Decimal,
    market_urgency: Decimal,
    capacity_coverage_ratio: Decimal,
    capacity_shortfall_minutes: Decimal,
    capacity_shortfall_ratio: Decimal,
    backlog_priority_score: Decimal,
    priority_band: str,
    recommended_action: str,
    reason_codes: tuple[str, ...],
) -> str:
    return _sha256_digest(
        (
            VALIDATION_DIGEST_ALGORITHM,
            backlog_id,
            team_id,
            market_slug,
            _decimal_payload(stale_packet_count),
            _decimal_payload(required_source_count),
            _decimal_payload(current_source_count),
            _decimal_payload(missing_source_count),
            _decimal_payload(disagreement_backlog_count),
            _decimal_payload(hours_to_resolution),
            _decimal_payload(available_specialist_minutes),
            _decimal_payload(estimated_repair_minutes),
            _decimal_payload(stale_packet_pressure),
            _decimal_payload(source_quorum_gap_ratio),
            _decimal_payload(disagreement_pressure),
            _decimal_payload(market_urgency),
            _decimal_payload(capacity_coverage_ratio),
            _decimal_payload(capacity_shortfall_minutes),
            _decimal_payload(capacity_shortfall_ratio),
            _decimal_payload(backlog_priority_score),
            priority_band,
            recommended_action,
            "\x1f".join(reason_codes),
            "paper_only=True",
            "report_only=True",
            "readonly=True",
        ),
    )


def _report_validation_digest(
    *,
    generated_at: datetime,
    config_version: str,
    input_count: Decimal,
    backlog_item_count: Decimal,
    critical_priority_count: Decimal,
    high_priority_count: Decimal,
    medium_priority_count: Decimal,
    low_priority_count: Decimal,
    total_missing_source_count: Decimal,
    total_stale_packet_count: Decimal,
    total_disagreement_backlog_count: Decimal,
    total_estimated_repair_minutes: Decimal,
    total_available_specialist_minutes: Decimal,
    max_backlog_priority_score: Decimal,
    mean_backlog_priority_score: Decimal,
    priority_status: str,
    reason_codes: tuple[str, ...],
    rows: tuple[StrategyTeamSourceGapBacklogV10Row, ...],
) -> str:
    return _sha256_digest(
        (
            VALIDATION_DIGEST_ALGORITHM,
            generated_at.isoformat(),
            config_version,
            _decimal_payload(input_count),
            _decimal_payload(backlog_item_count),
            _decimal_payload(critical_priority_count),
            _decimal_payload(high_priority_count),
            _decimal_payload(medium_priority_count),
            _decimal_payload(low_priority_count),
            _decimal_payload(total_missing_source_count),
            _decimal_payload(total_stale_packet_count),
            _decimal_payload(total_disagreement_backlog_count),
            _decimal_payload(total_estimated_repair_minutes),
            _decimal_payload(total_available_specialist_minutes),
            _decimal_payload(max_backlog_priority_score),
            _decimal_payload(mean_backlog_priority_score),
            priority_status,
            "\x1f".join(reason_codes),
            "\x1e".join(row.validation_digest for row in rows),
            "paper_only=True",
            "report_only=True",
            "readonly=True",
        ),
    )


def _sha256_digest(parts: tuple[str, ...]) -> str:
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


def _report_payload(report: StrategyTeamSourceGapBacklogV10Report) -> dict[str, Any]:
    return {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "input_count": report.input_count,
        "backlog_item_count": report.backlog_item_count,
        "critical_priority_count": report.critical_priority_count,
        "high_priority_count": report.high_priority_count,
        "medium_priority_count": report.medium_priority_count,
        "low_priority_count": report.low_priority_count,
        "total_missing_source_count": report.total_missing_source_count,
        "total_stale_packet_count": report.total_stale_packet_count,
        "total_disagreement_backlog_count": report.total_disagreement_backlog_count,
        "total_estimated_repair_minutes": report.total_estimated_repair_minutes,
        "total_available_specialist_minutes": (
            report.total_available_specialist_minutes
        ),
        "max_backlog_priority_score": report.max_backlog_priority_score,
        "mean_backlog_priority_score": report.mean_backlog_priority_score,
        "priority_status": report.priority_status,
        "reason_codes": report.reason_codes,
        "rows": [_row_payload(row) for row in report.rows],
        "validation_digest": report.validation_digest,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_payload(row: StrategyTeamSourceGapBacklogV10Row) -> dict[str, Any]:
    return {
        "backlog_id": row.backlog_id,
        "team_id": row.team_id,
        "market_slug": row.market_slug,
        "stale_packet_count": row.stale_packet_count,
        "required_source_count": row.required_source_count,
        "current_source_count": row.current_source_count,
        "missing_source_count": row.missing_source_count,
        "disagreement_backlog_count": row.disagreement_backlog_count,
        "hours_to_resolution": row.hours_to_resolution,
        "available_specialist_minutes": row.available_specialist_minutes,
        "estimated_repair_minutes": row.estimated_repair_minutes,
        "stale_packet_pressure": row.stale_packet_pressure,
        "source_quorum_gap_ratio": row.source_quorum_gap_ratio,
        "disagreement_pressure": row.disagreement_pressure,
        "market_urgency": row.market_urgency,
        "capacity_coverage_ratio": row.capacity_coverage_ratio,
        "capacity_shortfall_minutes": row.capacity_shortfall_minutes,
        "capacity_shortfall_ratio": row.capacity_shortfall_ratio,
        "backlog_priority_score": row.backlog_priority_score,
        "priority_band": row.priority_band,
        "recommended_action": row.recommended_action,
        "reason_codes": row.reason_codes,
        "validation_digest": row.validation_digest,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _validated_public_payload(payload: dict[str, Any]) -> dict[str, Any]:
    _reject_unsafe_public_payload("payload", payload)
    ready = json_ready_no_floats(payload)
    if type(ready) is not dict:
        raise ValueError("payload must be a JSON object")
    _require_safety_flags("payload", _DictFlags(ready))
    report = _report_from_payload(ready)
    canonical_payload = _report_payload(report)
    canonical_ready = json_ready_no_floats(canonical_payload)
    if type(canonical_ready) is not dict:
        raise ValueError("payload must be a JSON object")
    _reject_unsafe_public_payload("payload", canonical_ready)
    return canonical_ready


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


def _report_from_payload(payload: dict[str, Any]) -> StrategyTeamSourceGapBacklogV10Report:
    rows_value = _payload_field(payload, "rows")
    if type(rows_value) is not list:
        raise ValueError("rows must be a list")
    rows = tuple(_row_from_payload(row_payload) for row_payload in rows_value)
    return StrategyTeamSourceGapBacklogV10Report(
        generated_at=_payload_datetime(payload, "generated_at"),
        config_version=_payload_canonical_string(payload, "config_version"),
        input_count=_payload_count(payload, "input_count"),
        backlog_item_count=_payload_count(payload, "backlog_item_count"),
        critical_priority_count=_payload_count(payload, "critical_priority_count"),
        high_priority_count=_payload_count(payload, "high_priority_count"),
        medium_priority_count=_payload_count(payload, "medium_priority_count"),
        low_priority_count=_payload_count(payload, "low_priority_count"),
        total_missing_source_count=_payload_count(
            payload,
            "total_missing_source_count",
        ),
        total_stale_packet_count=_payload_count(
            payload,
            "total_stale_packet_count",
        ),
        total_disagreement_backlog_count=_payload_count(
            payload,
            "total_disagreement_backlog_count",
        ),
        total_estimated_repair_minutes=_payload_decimal(
            payload,
            "total_estimated_repair_minutes",
        ),
        total_available_specialist_minutes=_payload_decimal(
            payload,
            "total_available_specialist_minutes",
        ),
        max_backlog_priority_score=_payload_decimal(
            payload,
            "max_backlog_priority_score",
        ),
        mean_backlog_priority_score=_payload_decimal(
            payload,
            "mean_backlog_priority_score",
        ),
        priority_status=_payload_member(payload, "priority_status", PRIORITY_STATUSES),
        reason_codes=_payload_reason_codes(payload, REPORT_REASON_CODES),
        rows=rows,
        validation_digest=_payload_validation_digest(payload),
        paper_only=_payload_flag(payload, "paper_only"),
        report_only=_payload_flag(payload, "report_only"),
        readonly=_payload_flag(payload, "readonly"),
    )


def _row_from_payload(payload: object) -> StrategyTeamSourceGapBacklogV10Row:
    if type(payload) is not dict:
        raise ValueError("rows must contain JSON objects")
    return StrategyTeamSourceGapBacklogV10Row(
        backlog_id=_payload_canonical_string(payload, "backlog_id"),
        team_id=_payload_canonical_string(payload, "team_id"),
        market_slug=_payload_canonical_string(payload, "market_slug"),
        stale_packet_count=_payload_count(payload, "stale_packet_count"),
        required_source_count=_payload_count(payload, "required_source_count"),
        current_source_count=_payload_count(payload, "current_source_count"),
        missing_source_count=_payload_count(payload, "missing_source_count"),
        disagreement_backlog_count=_payload_count(
            payload,
            "disagreement_backlog_count",
        ),
        hours_to_resolution=_payload_decimal(payload, "hours_to_resolution"),
        available_specialist_minutes=_payload_decimal(
            payload,
            "available_specialist_minutes",
        ),
        estimated_repair_minutes=_payload_decimal(
            payload,
            "estimated_repair_minutes",
        ),
        stale_packet_pressure=_payload_decimal(payload, "stale_packet_pressure"),
        source_quorum_gap_ratio=_payload_decimal(
            payload,
            "source_quorum_gap_ratio",
        ),
        disagreement_pressure=_payload_decimal(payload, "disagreement_pressure"),
        market_urgency=_payload_decimal(payload, "market_urgency"),
        capacity_coverage_ratio=_payload_decimal(
            payload,
            "capacity_coverage_ratio",
        ),
        capacity_shortfall_minutes=_payload_decimal(
            payload,
            "capacity_shortfall_minutes",
        ),
        capacity_shortfall_ratio=_payload_decimal(
            payload,
            "capacity_shortfall_ratio",
        ),
        backlog_priority_score=_payload_decimal(payload, "backlog_priority_score"),
        priority_band=_payload_member(payload, "priority_band", PRIORITY_BANDS),
        recommended_action=_payload_member(
            payload,
            "recommended_action",
            RECOMMENDED_ACTIONS,
        ),
        reason_codes=_payload_reason_codes(payload, ROW_REASON_CODES),
        validation_digest=_payload_validation_digest(payload),
        paper_only=_payload_flag(payload, "paper_only"),
        report_only=_payload_flag(payload, "report_only"),
        readonly=_payload_flag(payload, "readonly"),
    )


def _payload_field(payload: dict[str, Any], field_name: str) -> object:
    if field_name not in payload:
        raise ValueError(f"payload must include {field_name}")
    return payload[field_name]


def _payload_canonical_string(payload: dict[str, Any], field_name: str) -> str:
    value = _payload_field(payload, field_name)
    _require_canonical_string(field_name, value)
    return value


def _payload_decimal(payload: dict[str, Any], field_name: str) -> Decimal:
    value = _payload_field(payload, field_name)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        decimal_value = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    return _normalize_nonnegative_decimal(field_name, decimal_value)


def _payload_count(payload: dict[str, Any], field_name: str) -> Decimal:
    return _normalize_nonnegative_count(field_name, _payload_decimal(payload, field_name))


def _payload_datetime(payload: dict[str, Any], field_name: str) -> datetime:
    value = _payload_field(payload, field_name)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an ISO datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime string") from exc
    return _as_exact_utc(field_name, parsed)


def _payload_member(
    payload: dict[str, Any],
    field_name: str,
    allowed_values: tuple[str, ...],
) -> str:
    value = _payload_field(payload, field_name)
    _require_member(field_name, value, allowed_values)
    return value


def _payload_reason_codes(
    payload: dict[str, Any],
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    value = _payload_field(payload, "reason_codes")
    if type(value) is not list:
        raise ValueError("reason_codes must be a list")
    return _normalize_reason_codes("reason_codes", tuple(value), allowed_values)


def _payload_validation_digest(payload: dict[str, Any]) -> str:
    return _require_validation_digest(
        "validation_digest",
        _payload_field(payload, "validation_digest"),
    )


def _payload_flag(payload: dict[str, Any], field_name: str) -> bool:
    value = _payload_field(payload, field_name)
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return value


def _normalize_positive_count(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    integral_value = decimal_value.to_integral_value()
    if decimal_value != integral_value:
        raise ValueError(f"{field_name} must be a whole Decimal count")
    return integral_value.quantize(COUNT_QUANTUM)


def _normalize_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize_ratio(decimal_value)


def _normalize_probability(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _quantize_ratio(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _cap_probability(value: Decimal) -> Decimal:
    if value > ONE:
        return ONE
    if value < ZERO:
        return ZERO
    return _quantize_ratio(value)


def _as_exact_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is not UTC:
        raise ValueError(f"{field_name} must be UTC timezone-aware")
    return value


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be a known value")


def _normalize_reason_codes(
    field_name: str,
    values: tuple[str, ...],
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not values:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    for value in values:
        _require_canonical_string(field_name, value)
        if value not in allowed_values:
            raise ValueError(f"{field_name} contains unsupported value")
        if value in seen:
            raise ValueError(f"{field_name} contains duplicate value")
        seen.add(value)
    return tuple(value for value in allowed_values if value in seen)


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_safety_flags(label: str, value: object) -> None:
    try:
        require_paper_only_flags(label, value)
    except AttributeError as exc:
        raise ValueError(f"{label} must expose paper_only/report_only/readonly") from exc


def _require_validation_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a validation digest")
    if any(character not in HEX_DIGITS for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    if value != value.lower():
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    reject_unsafe_surface_fields(label, value)
    _reject_unsafe_public_values(label, value)


def _reject_unsafe_public_values(label: str, value: object) -> None:
    if type(value) is str:
        if _has_unsafe_public_value(value):
            raise ValueError(f"unsafe live surface value in {label}")
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{label} Decimal values must be exact Decimal")
        if not value.is_finite():
            raise ValueError(f"{label} Decimal values must be finite")
        return
    if type(value) in (bool, type(None), datetime):
        return
    if isinstance(value, dict):
        for item in value.values():
            _reject_unsafe_public_values(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_values(label, item)
        return
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        for field_name in value.__dataclass_fields__:
            _reject_unsafe_public_values(label, getattr(value, field_name))


def _has_unsafe_public_value(value: str) -> bool:
    lowered = value.lower()
    for fragment in UNSAFE_SURFACE_FIELD_FRAGMENTS:
        if fragment == "sign":
            tokens = lowered.replace("_", " ").replace("-", " ").split()
            if fragment in tokens:
                return True
            continue
        if fragment in lowered:
            return True
    return False


def _decimal_payload(value: Decimal) -> str:
    if type(value) is not Decimal:
        raise ValueError("payload decimal must be a Decimal")
    return format(value, "f")


__all__ = (
    "DEFAULT_STRATEGY_TEAM_SOURCE_GAP_BACKLOG_V10_CONFIG_VERSION",
    "PRIORITY_BANDS",
    "PRIORITY_STATUSES",
    "RECOMMENDED_ACTIONS",
    "ROW_REASON_CODES",
    "REPORT_REASON_CODES",
    "StrategyTeamSourceGapBacklogV10Config",
    "StrategyTeamSourceGapBacklogV10Input",
    "StrategyTeamSourceGapBacklogV10Row",
    "StrategyTeamSourceGapBacklogV10Report",
    "build_strategy_team_source_gap_backlog_v10_report",
    "strategy_team_source_gap_backlog_v10_payload",
)
