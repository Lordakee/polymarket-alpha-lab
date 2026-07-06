"""Pure paper-only strategy team allocation policy."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any


__all__ = (
    "StrategyTeamAllocationPolicyConfig",
    "StrategyTeamAllocationPolicyReport",
    "StrategyTeamAllocationPolicyRow",
    "StrategyTeamAllocationPolicyTeam",
    "allocate_strategy_team_allocation_policy",
    "strategy_team_allocation_policy_payload",
)


ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
MEMORY_WEIGHT = Decimal("0.400000")
SOURCE_WEIGHT = Decimal("0.250000")
EDGE_WEIGHT = Decimal("0.250000")
CAPACITY_WEIGHT = Decimal("0.100000")
STATUSES = ("allocate", "watch", "blocked")
REPORT_STATUSES = ("allocated", "watch", "blocked")


@dataclass(frozen=True)
class StrategyTeamAllocationPolicyConfig:
    config_version: str
    base_paper_notional_cap: Decimal
    edge_full_score: Decimal
    min_allocation_score: Decimal
    strong_team_memory_score: Decimal
    strong_source_quality: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "base_paper_notional_cap",
            _normalize_positive_decimal(
                "base_paper_notional_cap",
                self.base_paper_notional_cap,
            ),
        )
        object.__setattr__(
            self,
            "edge_full_score",
            _normalize_positive_decimal("edge_full_score", self.edge_full_score),
        )
        for field_name in (
            "min_allocation_score",
            "strong_team_memory_score",
            "strong_source_quality",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class StrategyTeamAllocationPolicyTeam:
    team_id: str
    category: str
    team_memory_score: Decimal
    category_capacity: Decimal
    current_exposure: Decimal
    source_quality: Decimal
    cost_adjusted_edge: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("team_id", self.team_id)
        _require_canonical_string("category", self.category)
        object.__setattr__(
            self,
            "team_memory_score",
            _normalize_probability("team_memory_score", self.team_memory_score),
        )
        object.__setattr__(
            self,
            "category_capacity",
            _normalize_nonnegative_decimal("category_capacity", self.category_capacity),
        )
        object.__setattr__(
            self,
            "current_exposure",
            _normalize_nonnegative_decimal("current_exposure", self.current_exposure),
        )
        object.__setattr__(
            self,
            "source_quality",
            _normalize_probability("source_quality", self.source_quality),
        )
        object.__setattr__(
            self,
            "cost_adjusted_edge",
            _normalize_decimal("cost_adjusted_edge", self.cost_adjusted_edge),
        )
        if self.current_exposure > self.category_capacity:
            raise ValueError("current_exposure must not exceed category_capacity")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _require_hard_flags("team", self)


@dataclass(frozen=True)
class StrategyTeamAllocationPolicyRow:
    team_id: str
    category: str
    team_memory_score: Decimal
    category_capacity: Decimal
    current_exposure: Decimal
    source_quality: Decimal
    cost_adjusted_edge: Decimal
    available_capacity: Decimal
    capacity_headroom_ratio: Decimal
    allocation_score: Decimal
    paper_notional_cap: Decimal
    allocation_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("team_id", self.team_id)
        _require_canonical_string("category", self.category)
        for field_name in ("team_memory_score", "source_quality"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "category_capacity",
            "current_exposure",
            "available_capacity",
            "paper_notional_cap",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "cost_adjusted_edge",
            _normalize_decimal("cost_adjusted_edge", self.cost_adjusted_edge),
        )
        for field_name in ("capacity_headroom_ratio", "allocation_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member("allocation_status", self.allocation_status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        if self.current_exposure > self.category_capacity:
            raise ValueError("current_exposure must not exceed category_capacity")
        if self.available_capacity != self.category_capacity - self.current_exposure:
            raise ValueError("available_capacity must equal category_capacity less current_exposure")
        if self.paper_notional_cap > self.available_capacity:
            raise ValueError("paper_notional_cap must not exceed available_capacity")
        if self.allocation_status in {"watch", "blocked"} and self.paper_notional_cap != ZERO:
            raise ValueError("paper_notional_cap must be zero unless allocation_status is allocate")
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class StrategyTeamAllocationPolicyReport:
    generated_at: datetime
    config_version: str
    team_count: Decimal
    allocated_team_count: Decimal
    watch_team_count: Decimal
    blocked_team_count: Decimal
    total_available_capacity: Decimal
    total_paper_notional_cap: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyTeamAllocationPolicyRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "team_count",
            "allocated_team_count",
            "watch_team_count",
            "blocked_team_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("total_available_capacity", "total_paper_notional_cap"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags("report", self)


def allocate_strategy_team_allocation_policy(
    teams: tuple[StrategyTeamAllocationPolicyTeam, ...],
    *,
    config: StrategyTeamAllocationPolicyConfig,
    generated_at: datetime,
) -> StrategyTeamAllocationPolicyReport:
    if type(config) is not StrategyTeamAllocationPolicyConfig:
        raise ValueError("config must be a StrategyTeamAllocationPolicyConfig")
    normalized_teams = _normalize_teams(teams)
    rows = tuple(_row_from_team(team, config) for team in normalized_teams)
    return StrategyTeamAllocationPolicyReport(
        generated_at=generated_at,
        config_version=config.config_version,
        team_count=_count(len(rows)),
        allocated_team_count=_count(
            sum(1 for row in rows if row.allocation_status == "allocate"),
        ),
        watch_team_count=_count(
            sum(1 for row in rows if row.allocation_status == "watch"),
        ),
        blocked_team_count=_count(
            sum(1 for row in rows if row.allocation_status == "blocked"),
        ),
        total_available_capacity=sum(
            (row.available_capacity for row in rows),
            ZERO,
        ).quantize(QUANTUM),
        total_paper_notional_cap=sum(
            (row.paper_notional_cap for row in rows),
            ZERO,
        ).quantize(QUANTUM),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def strategy_team_allocation_policy_payload(
    report: StrategyTeamAllocationPolicyReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyTeamAllocationPolicyReport:
        _require_hard_flags("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a StrategyTeamAllocationPolicyReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
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


def _row_from_team(
    team: StrategyTeamAllocationPolicyTeam,
    config: StrategyTeamAllocationPolicyConfig,
) -> StrategyTeamAllocationPolicyRow:
    available_capacity = (team.category_capacity - team.current_exposure).quantize(QUANTUM)
    capacity_headroom_ratio = _ratio(available_capacity, team.category_capacity)
    allocation_score = _allocation_score(team, capacity_headroom_ratio, config)
    allocation_status = _allocation_status(team, available_capacity, allocation_score, config)
    paper_notional_cap = _paper_notional_cap(
        allocation_status,
        allocation_score,
        available_capacity,
        config,
    )
    return StrategyTeamAllocationPolicyRow(
        team_id=team.team_id,
        category=team.category,
        team_memory_score=team.team_memory_score,
        category_capacity=team.category_capacity,
        current_exposure=team.current_exposure,
        source_quality=team.source_quality,
        cost_adjusted_edge=team.cost_adjusted_edge,
        available_capacity=available_capacity,
        capacity_headroom_ratio=capacity_headroom_ratio,
        allocation_score=allocation_score,
        paper_notional_cap=paper_notional_cap,
        allocation_status=allocation_status,
        reason_codes=_row_reason_codes(
            team,
            config,
            available_capacity,
            allocation_score,
            allocation_status,
            paper_notional_cap,
        ),
    )


def _allocation_score(
    team: StrategyTeamAllocationPolicyTeam,
    capacity_headroom_ratio: Decimal,
    config: StrategyTeamAllocationPolicyConfig,
) -> Decimal:
    edge_score = _clamp_probability(team.cost_adjusted_edge / config.edge_full_score)
    return (
        (team.team_memory_score * MEMORY_WEIGHT)
        + (team.source_quality * SOURCE_WEIGHT)
        + (edge_score * EDGE_WEIGHT)
        + (capacity_headroom_ratio * CAPACITY_WEIGHT)
    ).quantize(QUANTUM)


def _allocation_status(
    team: StrategyTeamAllocationPolicyTeam,
    available_capacity: Decimal,
    allocation_score: Decimal,
    config: StrategyTeamAllocationPolicyConfig,
) -> str:
    if available_capacity <= ZERO:
        return "blocked"
    if team.cost_adjusted_edge <= ZERO or allocation_score < config.min_allocation_score:
        return "watch"
    return "allocate"


def _paper_notional_cap(
    allocation_status: str,
    allocation_score: Decimal,
    available_capacity: Decimal,
    config: StrategyTeamAllocationPolicyConfig,
) -> Decimal:
    if allocation_status != "allocate":
        return ZERO
    score_cap = (config.base_paper_notional_cap * allocation_score).quantize(QUANTUM)
    return min(score_cap, available_capacity).quantize(QUANTUM)


def _row_reason_codes(
    team: StrategyTeamAllocationPolicyTeam,
    config: StrategyTeamAllocationPolicyConfig,
    available_capacity: Decimal,
    allocation_score: Decimal,
    allocation_status: str,
    paper_notional_cap: Decimal,
) -> tuple[str, ...]:
    reason_codes = list(team.reason_codes)
    if allocation_status == "allocate":
        reason_codes.append("team_allocation_selected")
    elif allocation_status == "watch":
        reason_codes.append("team_allocation_watch")
    else:
        reason_codes.append("team_allocation_blocked")

    reason_codes.append(
        "team_memory_strong"
        if team.team_memory_score >= config.strong_team_memory_score
        else "team_memory_watch",
    )
    reason_codes.append(
        "source_quality_strong"
        if team.source_quality >= config.strong_source_quality
        else "source_quality_watch",
    )
    reason_codes.append(
        "cost_adjusted_edge_positive"
        if team.cost_adjusted_edge > ZERO
        else "cost_adjusted_edge_nonpositive",
    )
    reason_codes.append(
        "category_capacity_available"
        if available_capacity > ZERO
        else "category_capacity_exhausted",
    )
    if allocation_score < config.min_allocation_score:
        reason_codes.append("allocation_score_below_minimum")
    if (
        allocation_status == "allocate"
        and paper_notional_cap < (config.base_paper_notional_cap * allocation_score).quantize(QUANTUM)
    ):
        reason_codes.append("notional_cap_limited_by_capacity")
    return _dedupe(reason_codes)


def _report_status(rows: tuple[StrategyTeamAllocationPolicyRow, ...]) -> str:
    if any(row.allocation_status == "blocked" for row in rows):
        return "blocked"
    if any(row.allocation_status == "watch" for row in rows):
        return "watch"
    if rows:
        return "allocated"
    return "watch"


def _report_reason_codes(rows: tuple[StrategyTeamAllocationPolicyRow, ...]) -> tuple[str, ...]:
    if not rows:
        return ("team_allocation_no_inputs",)
    reason_codes: list[str] = []
    if any(row.allocation_status == "allocate" for row in rows):
        reason_codes.append("team_allocation_selected")
    if any(row.allocation_status == "watch" for row in rows):
        reason_codes.append("team_allocation_watch")
    if any(row.allocation_status == "blocked" for row in rows):
        reason_codes.append("team_allocation_blocked")
    for code in (
        "allocation_score_below_minimum",
        "notional_cap_limited_by_capacity",
        "category_capacity_exhausted",
    ):
        if any(code in row.reason_codes for row in rows):
            reason_codes.append(code)
    return _dedupe(reason_codes)


def _validate_report(report: StrategyTeamAllocationPolicyReport) -> None:
    if report.team_count != _count(len(report.rows)):
        raise ValueError("team_count must equal rows count")
    allocated = _count(sum(1 for row in report.rows if row.allocation_status == "allocate"))
    watched = _count(sum(1 for row in report.rows if row.allocation_status == "watch"))
    blocked = _count(sum(1 for row in report.rows if row.allocation_status == "blocked"))
    if report.allocated_team_count != allocated:
        raise ValueError("allocated_team_count must equal allocated rows count")
    if report.watch_team_count != watched:
        raise ValueError("watch_team_count must equal watch rows count")
    if report.blocked_team_count != blocked:
        raise ValueError("blocked_team_count must equal blocked rows count")
    total_available_capacity = sum((row.available_capacity for row in report.rows), ZERO)
    total_paper_notional_cap = sum((row.paper_notional_cap for row in report.rows), ZERO)
    if report.total_available_capacity != total_available_capacity.quantize(QUANTUM):
        raise ValueError("total_available_capacity must equal row sum")
    if report.total_paper_notional_cap != total_paper_notional_cap.quantize(QUANTUM):
        raise ValueError("total_paper_notional_cap must equal row sum")


def _normalize_teams(
    teams: tuple[StrategyTeamAllocationPolicyTeam, ...],
) -> tuple[StrategyTeamAllocationPolicyTeam, ...]:
    if not isinstance(teams, tuple):
        teams = tuple(teams)
    for team in teams:
        if type(team) is not StrategyTeamAllocationPolicyTeam:
            raise ValueError("teams must contain StrategyTeamAllocationPolicyTeam")
    return teams


def _normalize_rows(
    rows: tuple[StrategyTeamAllocationPolicyRow, ...],
) -> tuple[StrategyTeamAllocationPolicyRow, ...]:
    if not isinstance(rows, tuple):
        rows = tuple(rows)
    for row in rows:
        if type(row) is not StrategyTeamAllocationPolicyRow:
            raise ValueError("rows must contain StrategyTeamAllocationPolicyRow")
    return rows


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    return normalized


def _normalize_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integer count")
    return normalized


def _normalize_reason_codes(
    reason_codes: object,
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if not isinstance(reason_codes, tuple):
        reason_codes = tuple(reason_codes)
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_canonical_string("reason_code", reason_code)
        normalized.append(reason_code)
    if require_nonempty and not normalized:
        raise ValueError("reason_codes must not be empty")
    return _dedupe(normalized)


def _dedupe(reason_codes: list[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    normalized: list[str] = []
    for reason_code in reason_codes:
        if reason_code not in seen:
            normalized.append(reason_code)
            seen.add(reason_code)
    return tuple(normalized)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _clamp_probability(numerator / denominator)


def _clamp_probability(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be canonical")


def _require_member(field_name: str, value: str, allowed_values: tuple[str, ...]) -> None:
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
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
    if isinstance(value, (str, bool)) or value is None:
        return value
    raise ValueError("value is not JSON serializable")
