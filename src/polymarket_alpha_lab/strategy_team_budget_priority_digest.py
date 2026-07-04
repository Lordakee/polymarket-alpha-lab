"""Paper-only strategy team budget priority diagnostic reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, localcontext
from hashlib import sha256


__all__ = (
    "StrategyTeamBudgetPriorityDigestConfig",
    "StrategyTeamBudgetPriorityDigestReport",
    "StrategyTeamBudgetPriorityDigestRow",
    "StrategyTeamBudgetPriorityDigestTeam",
    "build_strategy_team_budget_priority_digest",
    "strategy_team_budget_priority_digest_payload",
)


DEFAULT_CONFIG_VERSION = "strategy-team-budget-priority-digest-v0"
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1.000000")
PRIORITIZE_BUDGET_MULTIPLE = Decimal("1.200000")
WATCH_BUDGET_MULTIPLE = Decimal("0.200000")
PRIORITIZE_SCORE_SPREAD = Decimal("0.250000")
ROW_STATUSES = ("prioritize", "watch", "deprioritize")
REPORT_STATUSES = ("pass", "watch", "blocked")
EMPTY_REASON_CODE = "strategy_team_budget_priority_digest_empty"
PRIORITIZED_REASON_CODE = "team_budget_prioritized"
WATCH_REASON_CODE = "team_budget_watch"
DEPRIORITIZED_REASON_CODE = "team_budget_deprioritized"
REPORT_REASON_PRIORITY = (
    PRIORITIZED_REASON_CODE,
    WATCH_REASON_CODE,
    DEPRIORITIZED_REASON_CODE,
    "drawdown_pressure_high",
    "unresolved_exposure_high",
    "capacity_headroom_low",
    EMPTY_REASON_CODE,
)
ROW_STATUS_SORT_PRIORITY = {"prioritize": 0, "watch": 1, "deprioritize": 2}
DECIMAL_CONTEXT = Context(prec=64)
SENSITIVE_REFERENCE_TOKENS = (
    "auth",
    "authorization",
    "secret",
    "token",
    "private",
    "key",
    "bearer",
    "dsn",
    "password",
    "wallet",
    "order",
    "cancel",
    "replace",
    "live-trading",
    "live_trading",
    "live trading",
)
UNSAFE_FIELD_FRAGMENTS = (
    "auth",
    "private_key",
    "exchange_mutation",
    "broker",
    "wallet",
    "order",
    "cancel",
    "replace",
    "sign",
    "trade",
    "trading",
)


@dataclass(frozen=True)
class StrategyTeamBudgetPriorityDigestConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    base_paper_budget: Decimal = Decimal("1000.000000")
    min_priority_score: Decimal = Decimal("0.250000")
    max_drawdown_pressure: Decimal = Decimal("0.700000")
    max_unresolved_exposure_share: Decimal = Decimal("0.600000")
    min_capacity_headroom: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "base_paper_budget",
            _normalize_positive_decimal("base_paper_budget", self.base_paper_budget),
        )
        for field_name in (
            "min_priority_score",
            "max_drawdown_pressure",
            "max_unresolved_exposure_share",
            "min_capacity_headroom",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_safety_flags("config", self)


@dataclass(frozen=True)
class StrategyTeamBudgetPriorityDigestTeam:
    team_id: str
    team_reference: str
    observed_at: datetime
    forecast_confidence: Decimal
    realized_learning_quality: Decimal
    paper_learning_quality: Decimal
    cost_aware_edge: Decimal
    drawdown_pressure: Decimal
    unresolved_exposure: Decimal
    paper_budget: Decimal
    capacity_utilization: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("team_id", self.team_id)
        _require_canonical_string("team_reference", self.team_reference)
        object.__setattr__(self, "team_reference", _redacted_reference(self.team_reference))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "forecast_confidence",
            "realized_learning_quality",
            "paper_learning_quality",
            "drawdown_pressure",
            "capacity_utilization",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "cost_aware_edge",
            _normalize_decimal("cost_aware_edge", self.cost_aware_edge),
        )
        object.__setattr__(
            self,
            "unresolved_exposure",
            _normalize_nonnegative_decimal("unresolved_exposure", self.unresolved_exposure),
        )
        object.__setattr__(
            self,
            "paper_budget",
            _normalize_positive_decimal("paper_budget", self.paper_budget),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _require_safety_flags("team", self)


@dataclass(frozen=True)
class StrategyTeamBudgetPriorityDigestRow:
    team_id: str
    redacted_team_reference: str
    observed_at: datetime
    forecast_confidence: Decimal
    realized_learning_quality: Decimal
    paper_learning_quality: Decimal
    combined_learning_quality: Decimal
    cost_aware_edge: Decimal
    drawdown_pressure: Decimal
    unresolved_exposure: Decimal
    paper_budget: Decimal
    unresolved_exposure_share: Decimal
    capacity_utilization: Decimal
    capacity_headroom: Decimal
    priority_score: Decimal
    recommended_paper_budget: Decimal
    priority_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("team_id", self.team_id)
        _require_canonical_string("redacted_team_reference", self.redacted_team_reference)
        _require_redacted_reference(self.redacted_team_reference)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "forecast_confidence",
            "realized_learning_quality",
            "paper_learning_quality",
            "combined_learning_quality",
            "drawdown_pressure",
            "capacity_utilization",
            "capacity_headroom",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "cost_aware_edge",
            _normalize_decimal("cost_aware_edge", self.cost_aware_edge),
        )
        for field_name in (
            "unresolved_exposure",
            "paper_budget",
            "unresolved_exposure_share",
            "priority_score",
            "recommended_paper_budget",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("priority_status", self.priority_status, ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _validate_row(self)
        _require_safety_flags("row", self)


@dataclass(frozen=True)
class StrategyTeamBudgetPriorityDigestReport:
    generated_at: datetime
    config_version: str
    team_count: Decimal
    prioritize_count: Decimal
    watch_count: Decimal
    deprioritize_count: Decimal
    total_recommended_paper_budget: Decimal
    max_priority_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyTeamBudgetPriorityDigestRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "team_count",
            "prioritize_count",
            "watch_count",
            "deprioritize_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "total_recommended_paper_budget",
            "max_priority_score",
        ):
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
        _require_safety_flags("report", self)


def build_strategy_team_budget_priority_digest(
    teams: Iterable[object],
    *,
    config: StrategyTeamBudgetPriorityDigestConfig,
    generated_at: datetime,
) -> StrategyTeamBudgetPriorityDigestReport:
    if type(config) is not StrategyTeamBudgetPriorityDigestConfig:
        raise ValueError("config must be a StrategyTeamBudgetPriorityDigestConfig")
    generated_at = _as_utc("generated_at", generated_at)
    _require_safety_flags("config", config)
    source_teams = _normalize_teams(teams)
    rows = tuple(
        sorted(
            (_row_from_team(team, config=config) for team in source_teams),
            key=_row_sort_key,
        ),
    )

    return StrategyTeamBudgetPriorityDigestReport(
        generated_at=generated_at,
        config_version=config.config_version,
        team_count=_count_decimal(len(rows)),
        prioritize_count=_status_count(rows, "prioritize"),
        watch_count=_status_count(rows, "watch"),
        deprioritize_count=_status_count(rows, "deprioritize"),
        total_recommended_paper_budget=_sum_decimal(
            row.recommended_paper_budget for row in rows
        ),
        max_priority_score=_max_priority_score(rows),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def strategy_team_budget_priority_digest_payload(
    report: StrategyTeamBudgetPriorityDigestReport,
) -> dict[str, object]:
    if type(report) is not StrategyTeamBudgetPriorityDigestReport:
        raise ValueError("report must be a StrategyTeamBudgetPriorityDigestReport")
    _require_safety_flags("report", report)
    return {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "team_count": _count_payload(report.team_count),
        "prioritize_count": _count_payload(report.prioritize_count),
        "watch_count": _count_payload(report.watch_count),
        "deprioritize_count": _count_payload(report.deprioritize_count),
        "total_recommended_paper_budget": _decimal_payload(
            report.total_recommended_paper_budget,
        ),
        "max_priority_score": _decimal_payload(report.max_priority_score),
        "status": report.status,
        "reason_codes": list(report.reason_codes),
        "rows": [_row_payload(row) for row in report.rows],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_payload(row: StrategyTeamBudgetPriorityDigestRow) -> dict[str, object]:
    _require_safety_flags("row", row)
    return {
        "team_id": row.team_id,
        "redacted_team_reference": row.redacted_team_reference,
        "observed_at": row.observed_at.isoformat(),
        "forecast_confidence": _decimal_payload(row.forecast_confidence),
        "realized_learning_quality": _decimal_payload(row.realized_learning_quality),
        "paper_learning_quality": _decimal_payload(row.paper_learning_quality),
        "combined_learning_quality": _decimal_payload(row.combined_learning_quality),
        "cost_aware_edge": _decimal_payload(row.cost_aware_edge),
        "drawdown_pressure": _decimal_payload(row.drawdown_pressure),
        "unresolved_exposure": _decimal_payload(row.unresolved_exposure),
        "paper_budget": _decimal_payload(row.paper_budget),
        "unresolved_exposure_share": _decimal_payload(row.unresolved_exposure_share),
        "capacity_utilization": _decimal_payload(row.capacity_utilization),
        "capacity_headroom": _decimal_payload(row.capacity_headroom),
        "priority_score": _decimal_payload(row.priority_score),
        "recommended_paper_budget": _decimal_payload(row.recommended_paper_budget),
        "priority_status": row.priority_status,
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_from_team(
    team: StrategyTeamBudgetPriorityDigestTeam,
    *,
    config: StrategyTeamBudgetPriorityDigestConfig,
) -> StrategyTeamBudgetPriorityDigestRow:
    combined_learning_quality = _average_decimal(
        team.realized_learning_quality,
        team.paper_learning_quality,
    )
    unresolved_exposure_share = _ratio_decimal(team.unresolved_exposure, team.paper_budget)
    capacity_headroom = _max_decimal(_subtract_decimal(ONE, team.capacity_utilization), _zero())
    priority_score = _priority_score(
        forecast_confidence=team.forecast_confidence,
        realized_learning_quality=team.realized_learning_quality,
        paper_learning_quality=team.paper_learning_quality,
        cost_aware_edge=team.cost_aware_edge,
        drawdown_pressure=team.drawdown_pressure,
        unresolved_exposure_share=unresolved_exposure_share,
        capacity_headroom=capacity_headroom,
    )
    priority_status, terminal_reason = _priority_status_and_reason(
        priority_score=priority_score,
        drawdown_pressure=team.drawdown_pressure,
        unresolved_exposure_share=unresolved_exposure_share,
        capacity_headroom=capacity_headroom,
        config=config,
    )
    return StrategyTeamBudgetPriorityDigestRow(
        team_id=team.team_id,
        redacted_team_reference=team.team_reference,
        observed_at=team.observed_at,
        forecast_confidence=team.forecast_confidence,
        realized_learning_quality=team.realized_learning_quality,
        paper_learning_quality=team.paper_learning_quality,
        combined_learning_quality=combined_learning_quality,
        cost_aware_edge=team.cost_aware_edge,
        drawdown_pressure=team.drawdown_pressure,
        unresolved_exposure=team.unresolved_exposure,
        paper_budget=team.paper_budget,
        unresolved_exposure_share=unresolved_exposure_share,
        capacity_utilization=team.capacity_utilization,
        capacity_headroom=capacity_headroom,
        priority_score=priority_score,
        recommended_paper_budget=_recommended_paper_budget(
            priority_status,
            config=config,
        ),
        priority_status=priority_status,
        reason_codes=_normalize_reason_codes(
            (
                *team.reason_codes,
                terminal_reason,
                *_quality_reason_codes(
                    team,
                    combined_learning_quality=combined_learning_quality,
                    unresolved_exposure_share=unresolved_exposure_share,
                    capacity_headroom=capacity_headroom,
                    config=config,
                ),
            ),
            require_nonempty=True,
        ),
    )


def _priority_score(
    *,
    forecast_confidence: Decimal,
    realized_learning_quality: Decimal,
    paper_learning_quality: Decimal,
    cost_aware_edge: Decimal,
    drawdown_pressure: Decimal,
    unresolved_exposure_share: Decimal,
    capacity_headroom: Decimal,
) -> Decimal:
    positive_edge = _max_decimal(cost_aware_edge, _zero())
    with localcontext(DECIMAL_CONTEXT):
        score = (
            (forecast_confidence * Decimal("0.400000"))
            + (realized_learning_quality * Decimal("0.200000"))
            + (paper_learning_quality * Decimal("0.150000"))
            + positive_edge
            + (capacity_headroom * Decimal("0.100000"))
            - (drawdown_pressure * Decimal("0.150000"))
            - (unresolved_exposure_share * Decimal("0.100000"))
        )
    return _max_decimal(score.quantize(QUANTUM), _zero())


def _priority_status_and_reason(
    *,
    priority_score: Decimal,
    drawdown_pressure: Decimal,
    unresolved_exposure_share: Decimal,
    capacity_headroom: Decimal,
    config: StrategyTeamBudgetPriorityDigestConfig,
) -> tuple[str, str]:
    if (
        priority_score < config.min_priority_score
        or drawdown_pressure > config.max_drawdown_pressure
        or unresolved_exposure_share > config.max_unresolved_exposure_share
        or capacity_headroom < config.min_capacity_headroom
    ):
        return "deprioritize", DEPRIORITIZED_REASON_CODE
    if priority_score >= _add_decimal(config.min_priority_score, PRIORITIZE_SCORE_SPREAD):
        return "prioritize", PRIORITIZED_REASON_CODE
    return "watch", WATCH_REASON_CODE


def _recommended_paper_budget(
    priority_status: str,
    *,
    config: StrategyTeamBudgetPriorityDigestConfig,
) -> Decimal:
    if priority_status == "prioritize":
        return _multiply_decimal(config.base_paper_budget, PRIORITIZE_BUDGET_MULTIPLE)
    if priority_status == "watch":
        return _multiply_decimal(config.base_paper_budget, WATCH_BUDGET_MULTIPLE)
    return _zero()


def _quality_reason_codes(
    team: StrategyTeamBudgetPriorityDigestTeam,
    *,
    combined_learning_quality: Decimal,
    unresolved_exposure_share: Decimal,
    capacity_headroom: Decimal,
    config: StrategyTeamBudgetPriorityDigestConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if team.forecast_confidence >= Decimal("0.800000"):
        reason_codes.append("forecast_confidence_strong")
    if combined_learning_quality >= Decimal("0.700000"):
        reason_codes.append("learning_quality_strong")
    if team.cost_aware_edge > ZERO:
        reason_codes.append("cost_aware_edge_positive")
    if team.drawdown_pressure > config.max_drawdown_pressure:
        reason_codes.append("drawdown_pressure_high")
    else:
        reason_codes.append("drawdown_pressure_contained")
    if unresolved_exposure_share > config.max_unresolved_exposure_share:
        reason_codes.append("unresolved_exposure_high")
    else:
        reason_codes.append("unresolved_exposure_contained")
    if capacity_headroom < config.min_capacity_headroom:
        reason_codes.append("capacity_headroom_low")
    else:
        reason_codes.append("capacity_available")
    return tuple(reason_codes)


def _normalize_teams(
    teams: Iterable[object],
) -> tuple[StrategyTeamBudgetPriorityDigestTeam, ...]:
    if isinstance(teams, (str, bytes)):
        raise ValueError("teams must be an iterable")
    try:
        rows = tuple(teams)
    except TypeError as exc:
        raise ValueError("teams must be an iterable") from exc
    normalized = tuple(_team_from_supplied_row(row) for row in rows)
    seen: set[str] = set()
    for row in normalized:
        if row.team_id in seen:
            raise ValueError("duplicate team_id")
        seen.add(row.team_id)
    return normalized


def _team_from_supplied_row(row: object) -> StrategyTeamBudgetPriorityDigestTeam:
    if type(row) is StrategyTeamBudgetPriorityDigestTeam:
        _require_safety_flags("team", row)
        return row
    raise ValueError("teams must contain StrategyTeamBudgetPriorityDigestTeam")


def _normalize_rows(
    rows: object,
) -> tuple[StrategyTeamBudgetPriorityDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not StrategyTeamBudgetPriorityDigestRow:
            raise ValueError("rows must contain StrategyTeamBudgetPriorityDigestRow")
        _require_safety_flags("row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be deterministically sorted")
    return normalized


def _row_sort_key(
    row: StrategyTeamBudgetPriorityDigestRow,
) -> tuple[int, Decimal, Decimal, str, str]:
    return (
        ROW_STATUS_SORT_PRIORITY[row.priority_status],
        -row.priority_score,
        -row.recommended_paper_budget,
        row.team_id,
        row.redacted_team_reference,
    )


def _status_count(
    rows: tuple[StrategyTeamBudgetPriorityDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.priority_status == status))


def _max_priority_score(rows: tuple[StrategyTeamBudgetPriorityDigestRow, ...]) -> Decimal:
    if not rows:
        return _zero()
    return max(row.priority_score for row in rows)


def _report_status(rows: tuple[StrategyTeamBudgetPriorityDigestRow, ...]) -> str:
    if any(row.priority_status != "prioritize" for row in rows) or not rows:
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[StrategyTeamBudgetPriorityDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    observed: set[str] = set()
    for row in rows:
        observed.update(row.reason_codes)
    return tuple(
        reason_code
        for reason_code in REPORT_REASON_PRIORITY
        if reason_code in observed
    )


def _validate_row(row: StrategyTeamBudgetPriorityDigestRow) -> None:
    if row.combined_learning_quality != _average_decimal(
        row.realized_learning_quality,
        row.paper_learning_quality,
    ):
        raise ValueError("combined_learning_quality must match learning inputs")
    if row.unresolved_exposure_share != _ratio_decimal(
        row.unresolved_exposure,
        row.paper_budget,
    ):
        raise ValueError("unresolved_exposure_share must match exposure and budget")
    if row.capacity_headroom != _max_decimal(
        _subtract_decimal(ONE, row.capacity_utilization),
        _zero(),
    ):
        raise ValueError("capacity_headroom must match utilization")


def _validate_report(report: StrategyTeamBudgetPriorityDigestReport) -> None:
    if report.team_count != _count_decimal(len(report.rows)):
        raise ValueError("team_count must match rows")
    if report.prioritize_count != _status_count(report.rows, "prioritize"):
        raise ValueError("prioritize_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.deprioritize_count != _status_count(report.rows, "deprioritize"):
        raise ValueError("deprioritize_count must match rows")
    if report.total_recommended_paper_budget != _sum_decimal(
        row.recommended_paper_budget for row in report.rows
    ):
        raise ValueError("total_recommended_paper_budget must match rows")
    if report.max_priority_score != _max_priority_score(report.rows):
        raise ValueError("max_priority_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_safety_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only") is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly") is not True:
        raise ValueError(f"readonly must be True for {label}")
    _reject_unsafe_fields(label, value)


def _reject_unsafe_fields(label: str, payload: object) -> None:
    for key in _iter_keys(payload):
        normalized_key = key.lower()
        if any(fragment in normalized_key for fragment in UNSAFE_FIELD_FRAGMENTS):
            raise ValueError(f"unsafe surface field in {label}: {key}")


def _iter_keys(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_keys(asdict(value))
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            keys.append(key)
            keys.extend(_iter_keys(item))
        return tuple(keys)
    if isinstance(value, (list, tuple)):
        keys = []
        for item in value:
            keys.extend(_iter_keys(item))
        return tuple(keys)
    return ()


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a nonnegative count Decimal")
    return normalized


def _normalize_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be a probability Decimal")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANTUM)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be quantizable") from exc


def _add_decimal(first: Decimal, second: Decimal, *rest: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        total = first + second
        for value in rest:
            total += value
        return total.quantize(QUANTUM)


def _subtract_decimal(first: Decimal, second: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (first - second).quantize(QUANTUM)


def _multiply_decimal(first: Decimal, second: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (first * second).quantize(QUANTUM)


def _ratio_decimal(numerator: Decimal, denominator: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANTUM)


def _average_decimal(first: Decimal, second: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return ((first + second) / Decimal("2")).quantize(QUANTUM)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        total = ZERO
        for value in values:
            total += value
        return total.quantize(QUANTUM)


def _max_decimal(first: Decimal, second: Decimal) -> Decimal:
    return first if first >= second else second


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _zero() -> Decimal:
    return ZERO.quantize(QUANTUM)


def _normalize_reason_codes(
    values: object,
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        reason_codes = tuple(values)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if require_nonempty and not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_canonical_reason_code("reason_codes", reason_code)
    return tuple(dict.fromkeys(reason_codes))


def _require_canonical_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    if value != value.lower() or value.strip() != value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    for part in value.split("_"):
        if not part or not part.isalnum() or part != part.lower():
            raise ValueError(f"{field_name} must contain canonical reason codes")


def _redacted_reference(team_reference: str) -> str:
    lowered = team_reference.lower()
    if any(token in lowered for token in SENSITIVE_REFERENCE_TOKENS):
        digest = sha256(team_reference.encode("utf-8")).hexdigest()[:16]
        return f"team_ref_{digest}"
    return team_reference


def _require_redacted_reference(value: str) -> None:
    lowered = value.lower()
    if any(token in lowered for token in SENSITIVE_REFERENCE_TOKENS):
        raise ValueError("redacted_team_reference must not expose sensitive tokens")


def _decimal_payload(value: Decimal) -> str:
    return format(_normalize_decimal("payload decimal", value), "f")


def _count_payload(value: Decimal) -> str:
    return str(int(_normalize_count_decimal("payload count", value)))
