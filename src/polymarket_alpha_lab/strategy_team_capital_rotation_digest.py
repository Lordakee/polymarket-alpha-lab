"""Paper-only strategy team capital rotation diagnostic reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, localcontext
from hashlib import sha256
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


__all__ = (
    "StrategyTeamCapitalRotationDigestConfig",
    "StrategyTeamCapitalRotationDigestReport",
    "StrategyTeamCapitalRotationDigestRow",
    "StrategyTeamCapitalRotationDigestTeam",
    "build_strategy_team_capital_rotation_digest",
    "strategy_team_capital_rotation_digest_payload",
)


DEFAULT_CONFIG_VERSION = "strategy-team-capital-rotation-digest-v0"
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
ROW_STATUSES = ("pass", "watch", "blocked")
REPORT_STATUSES = ("pass", "watch", "blocked")
EMPTY_REASON_CODE = "strategy_team_capital_rotation_digest_empty"
PASS_REASON_CODE = "capital_rotation_pass"
WATCH_REASON_CODE = "capital_rotation_watch"
BLOCK_REASON_CODE = "capital_rotation_block"
REPORT_REASON_PRIORITY = (
    BLOCK_REASON_CODE,
    PASS_REASON_CODE,
    WATCH_REASON_CODE,
    "drawdown_pressure_high",
    "liquidity_capacity_low",
    "expected_edge_negative",
    EMPTY_REASON_CODE,
)
ROW_STATUS_SORT_PRIORITY = {"pass": 0, "watch": 1, "blocked": 2}
DECIMAL_CONTEXT = Context(prec=64)
SENSITIVE_REFERENCE_TOKENS = (
    "secret",
    "token",
    "private",
    "key",
    "bearer",
    "dsn",
    "password",
    "wallet",
)


@dataclass(frozen=True)
class StrategyTeamCapitalRotationDigestConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    total_paper_capital: Decimal = Decimal("10000.000000")
    minimum_rotation_score: Decimal = Decimal("0.050000")
    watch_rotation_gap: Decimal = Decimal("0.020000")
    block_drawdown_pressure: Decimal = Decimal("0.800000")
    min_liquidity_capacity_share: Decimal = Decimal("0.050000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "total_paper_capital",
            _normalize_positive_decimal("total_paper_capital", self.total_paper_capital),
        )
        for field_name in (
            "minimum_rotation_score",
            "watch_rotation_gap",
            "block_drawdown_pressure",
            "min_liquidity_capacity_share",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("config", self)


@dataclass(frozen=True)
class StrategyTeamCapitalRotationDigestTeam:
    team_id: str
    team_reference: str
    observed_at: datetime
    current_budget_share: Decimal
    target_budget_share: Decimal
    expected_edge: Decimal
    liquidity_capacity_share: Decimal
    drawdown_pressure: Decimal
    learning_value: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("team_id", self.team_id)
        _require_canonical_string("team_reference", self.team_reference)
        object.__setattr__(self, "team_reference", _redacted_reference(self.team_reference))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "current_budget_share",
            "target_budget_share",
            "liquidity_capacity_share",
            "drawdown_pressure",
            "learning_value",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "expected_edge",
            _normalize_decimal("expected_edge", self.expected_edge),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        require_paper_only_flags("team", self)


@dataclass(frozen=True)
class StrategyTeamCapitalRotationDigestRow:
    team_id: str
    redacted_team_reference: str
    observed_at: datetime
    current_budget_share: Decimal
    target_budget_share: Decimal
    budget_gap_share: Decimal
    expected_edge: Decimal
    liquidity_capacity_share: Decimal
    drawdown_pressure: Decimal
    learning_value: Decimal
    rotation_score: Decimal
    recommended_paper_rotation: Decimal
    rotation_direction: str
    rotation_status: str
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
            "current_budget_share",
            "target_budget_share",
            "liquidity_capacity_share",
            "drawdown_pressure",
            "learning_value",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "budget_gap_share",
            "expected_edge",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "rotation_score",
            "recommended_paper_rotation",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member(
            "rotation_direction",
            self.rotation_direction,
            ("increase", "decrease", "hold"),
        )
        _require_member("rotation_status", self.rotation_status, ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _validate_row(self)
        require_paper_only_flags("row", self)


@dataclass(frozen=True)
class StrategyTeamCapitalRotationDigestReport:
    generated_at: datetime
    config_version: str
    total_paper_capital: Decimal
    team_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    total_recommended_paper_rotation: Decimal
    net_target_budget_shift: Decimal
    max_rotation_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyTeamCapitalRotationDigestRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "total_paper_capital",
            "total_recommended_paper_rotation",
            "net_target_budget_shift",
            "max_rotation_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "team_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        reject_unsafe_surface_fields("strategy team capital rotation digest", self)
        require_paper_only_flags("report", self)


def build_strategy_team_capital_rotation_digest(
    teams: Iterable[object],
    *,
    config: StrategyTeamCapitalRotationDigestConfig,
    generated_at: datetime,
) -> StrategyTeamCapitalRotationDigestReport:
    if type(config) is not StrategyTeamCapitalRotationDigestConfig:
        raise ValueError("config must be a StrategyTeamCapitalRotationDigestConfig")
    generated_at = _as_utc("generated_at", generated_at)
    require_paper_only_flags("config", config)
    source_teams = _normalize_teams(teams)
    rows = tuple(
        sorted(
            (_row_from_team(team, config=config) for team in source_teams),
            key=_row_sort_key,
        ),
    )

    return StrategyTeamCapitalRotationDigestReport(
        generated_at=generated_at,
        config_version=config.config_version,
        total_paper_capital=config.total_paper_capital,
        team_count=_count_decimal(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        total_recommended_paper_rotation=_sum_decimal(
            row.recommended_paper_rotation for row in rows
        ),
        net_target_budget_shift=_sum_decimal(
            _abs_decimal(row.budget_gap_share) for row in rows
        ),
        max_rotation_score=_max_rotation_score(rows),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def strategy_team_capital_rotation_digest_payload(
    report: StrategyTeamCapitalRotationDigestReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyTeamCapitalRotationDigestReport:
        require_paper_only_flags("report", report)
        reject_unsafe_surface_fields("strategy team capital rotation digest", report)
        ready = json_ready_no_floats(report)
        _reject_sensitive_payload_strings("strategy team capital rotation digest", ready)
        reject_unsafe_surface_fields("strategy team capital rotation digest", ready)
        return ready
    if type(report) is dict:
        reject_unsafe_surface_fields(
            "strategy team capital rotation digest payload",
            report,
        )
        ready = json_ready_no_floats(report)
        _reject_sensitive_payload_strings(
            "strategy team capital rotation digest payload",
            ready,
        )
        _reject_flag_downgrades("strategy team capital rotation digest payload", ready)
        reject_unsafe_surface_fields("strategy team capital rotation digest payload", ready)
        require_paper_only_flags("payload", _DictFlags(ready))
        return ready
    raise ValueError("report must be a StrategyTeamCapitalRotationDigestReport")


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
    team: StrategyTeamCapitalRotationDigestTeam,
    *,
    config: StrategyTeamCapitalRotationDigestConfig,
) -> StrategyTeamCapitalRotationDigestRow:
    budget_gap_share = _subtract_decimal(team.target_budget_share, team.current_budget_share)
    rotation_direction = _rotation_direction(budget_gap_share)
    rotation_score = _rotation_score(
        budget_gap_share=budget_gap_share,
        expected_edge=team.expected_edge,
        liquidity_capacity_share=team.liquidity_capacity_share,
        drawdown_pressure=team.drawdown_pressure,
        learning_value=team.learning_value,
    )
    rotation_status, terminal_reason = _rotation_status_and_reason(
        budget_gap_share=budget_gap_share,
        rotation_score=rotation_score,
        expected_edge=team.expected_edge,
        liquidity_capacity_share=team.liquidity_capacity_share,
        drawdown_pressure=team.drawdown_pressure,
        config=config,
    )
    return StrategyTeamCapitalRotationDigestRow(
        team_id=team.team_id,
        redacted_team_reference=team.team_reference,
        observed_at=team.observed_at,
        current_budget_share=team.current_budget_share,
        target_budget_share=team.target_budget_share,
        budget_gap_share=budget_gap_share,
        expected_edge=team.expected_edge,
        liquidity_capacity_share=team.liquidity_capacity_share,
        drawdown_pressure=team.drawdown_pressure,
        learning_value=team.learning_value,
        rotation_score=rotation_score,
        recommended_paper_rotation=_recommended_paper_rotation(
            budget_gap_share=budget_gap_share,
            rotation_status=rotation_status,
            config=config,
        ),
        rotation_direction=rotation_direction,
        rotation_status=rotation_status,
        reason_codes=_normalize_reason_codes(
            (
                *team.reason_codes,
                terminal_reason,
                *_diagnostic_reason_codes(
                    budget_gap_share=budget_gap_share,
                    expected_edge=team.expected_edge,
                    liquidity_capacity_share=team.liquidity_capacity_share,
                    drawdown_pressure=team.drawdown_pressure,
                    learning_value=team.learning_value,
                    config=config,
                ),
            ),
            require_nonempty=True,
        ),
    )


def _rotation_score(
    *,
    budget_gap_share: Decimal,
    expected_edge: Decimal,
    liquidity_capacity_share: Decimal,
    drawdown_pressure: Decimal,
    learning_value: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            budget_gap_share
            + expected_edge
            + (learning_value * Decimal("0.050000"))
            + (liquidity_capacity_share * Decimal("0.010000"))
            - (drawdown_pressure * Decimal("0.210000"))
        )
        return _max_decimal(score.quantize(QUANTUM), ZERO)


def _rotation_status_and_reason(
    *,
    budget_gap_share: Decimal,
    rotation_score: Decimal,
    expected_edge: Decimal,
    liquidity_capacity_share: Decimal,
    drawdown_pressure: Decimal,
    config: StrategyTeamCapitalRotationDigestConfig,
) -> tuple[str, str]:
    if (
        expected_edge < ZERO
        or liquidity_capacity_share < config.min_liquidity_capacity_share
        or drawdown_pressure >= config.block_drawdown_pressure
    ):
        return "blocked", BLOCK_REASON_CODE
    if (
        budget_gap_share > config.watch_rotation_gap
        and rotation_score >= config.minimum_rotation_score
    ):
        return "pass", PASS_REASON_CODE
    return "watch", WATCH_REASON_CODE


def _recommended_paper_rotation(
    *,
    budget_gap_share: Decimal,
    rotation_status: str,
    config: StrategyTeamCapitalRotationDigestConfig,
) -> Decimal:
    if rotation_status != "pass" or budget_gap_share <= ZERO:
        return ZERO
    return _multiply_decimal(config.total_paper_capital, budget_gap_share)


def _diagnostic_reason_codes(
    *,
    budget_gap_share: Decimal,
    expected_edge: Decimal,
    liquidity_capacity_share: Decimal,
    drawdown_pressure: Decimal,
    learning_value: Decimal,
    config: StrategyTeamCapitalRotationDigestConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if budget_gap_share > config.watch_rotation_gap:
        reason_codes.append("budget_share_below_target")
    elif budget_gap_share < _negate_decimal(config.watch_rotation_gap):
        reason_codes.append("budget_share_above_target")
    else:
        reason_codes.append("budget_share_near_target")
    if expected_edge < ZERO:
        reason_codes.append("expected_edge_negative")
    elif expected_edge > ZERO:
        reason_codes.append("expected_edge_positive")
    else:
        reason_codes.append("expected_edge_flat")
    if liquidity_capacity_share < config.min_liquidity_capacity_share:
        reason_codes.append("liquidity_capacity_low")
    else:
        reason_codes.append("liquidity_capacity_available")
    if drawdown_pressure >= config.block_drawdown_pressure:
        reason_codes.append("drawdown_pressure_high")
    else:
        reason_codes.append("drawdown_pressure_contained")
    if learning_value >= Decimal("0.600000"):
        reason_codes.append("learning_value_high")
    elif learning_value >= Decimal("0.250000"):
        reason_codes.append("learning_value_moderate")
    else:
        reason_codes.append("learning_value_low")
    return tuple(reason_codes)


def _rotation_direction(budget_gap_share: Decimal) -> str:
    if budget_gap_share > ZERO:
        return "increase"
    if budget_gap_share < ZERO:
        return "decrease"
    return "hold"


def _normalize_teams(
    teams: Iterable[object],
) -> tuple[StrategyTeamCapitalRotationDigestTeam, ...]:
    if isinstance(teams, (str, bytes)):
        raise ValueError("teams must be an iterable")
    try:
        normalized = tuple(teams)
    except TypeError as exc:
        raise ValueError("teams must be an iterable") from exc
    for team in normalized:
        if type(team) is not StrategyTeamCapitalRotationDigestTeam:
            raise ValueError("team must be a StrategyTeamCapitalRotationDigestTeam")
        require_paper_only_flags("team", team)
    return normalized


def _normalize_rows(
    rows: tuple[StrategyTeamCapitalRotationDigestRow, ...],
) -> tuple[StrategyTeamCapitalRotationDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not StrategyTeamCapitalRotationDigestRow:
            raise ValueError("row must be a StrategyTeamCapitalRotationDigestRow")
        require_paper_only_flags("row", row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use stable sequence")
    return rows


def _row_sort_key(row: StrategyTeamCapitalRotationDigestRow) -> tuple[int, Decimal, str]:
    return (
        ROW_STATUS_SORT_PRIORITY[row.rotation_status],
        -row.rotation_score,
        row.team_id,
    )


def _status_count(
    rows: tuple[StrategyTeamCapitalRotationDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.rotation_status == status))


def _max_rotation_score(rows: tuple[StrategyTeamCapitalRotationDigestRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    return max(row.rotation_score for row in rows)


def _report_status(rows: tuple[StrategyTeamCapitalRotationDigestRow, ...]) -> str:
    if not rows:
        return "watch"
    if any(row.rotation_status == "blocked" for row in rows):
        return "blocked"
    if any(row.rotation_status == "pass" for row in rows):
        return "pass"
    return "watch"


def _report_reason_codes(
    rows: tuple[StrategyTeamCapitalRotationDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    found = {reason_code for row in rows for reason_code in row.reason_codes}
    return tuple(reason_code for reason_code in REPORT_REASON_PRIORITY if reason_code in found)


def _validate_row(row: StrategyTeamCapitalRotationDigestRow) -> None:
    if row.rotation_direction != _rotation_direction(row.budget_gap_share):
        raise ValueError("rotation_direction must match budget_gap_share")
    expected_status = _row_status(row.reason_codes)
    if row.rotation_status != expected_status:
        raise ValueError("rotation_status must match reason_codes")
    if row.rotation_status != "pass" and row.recommended_paper_rotation != ZERO:
        raise ValueError("recommended_paper_rotation must be zero unless status is pass")


def _validate_report(report: StrategyTeamCapitalRotationDigestReport) -> None:
    if report.team_count != _count_decimal(len(report.rows)):
        raise ValueError("team_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.total_recommended_paper_rotation != _sum_decimal(
        row.recommended_paper_rotation for row in report.rows
    ):
        raise ValueError("total_recommended_paper_rotation must match rows")
    if report.net_target_budget_shift != _sum_decimal(
        _abs_decimal(row.budget_gap_share) for row in report.rows
    ):
        raise ValueError("net_target_budget_shift must match rows")
    if report.max_rotation_score != _max_rotation_score(report.rows):
        raise ValueError("max_rotation_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if BLOCK_REASON_CODE in reason_codes:
        return "blocked"
    if PASS_REASON_CODE in reason_codes:
        return "pass"
    if WATCH_REASON_CODE in reason_codes:
        return "watch"
    raise ValueError("reason_codes must include a rotation status code")


def _as_utc(field_name: str, value: Any) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: Any) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")


def _require_public_string(field_name: str, value: Any) -> None:
    _require_canonical_string(field_name, value)
    if _contains_sensitive_content(value):
        raise ValueError(f"{field_name} must not contain sensitive content")


def _require_member(field_name: str, value: Any, members: tuple[str, ...]) -> None:
    if type(value) is not str or value not in members:
        raise ValueError(f"{field_name} must be a known value")


def _normalize_decimal(field_name: str, value: Any) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANTUM)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be quantizable") from exc


def _normalize_nonnegative_decimal(field_name: str, value: Any) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_decimal(field_name: str, value: Any) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_count_decimal(field_name: str, value: Any) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return normalized


def _normalize_probability_decimal(field_name: str, value: Any) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_reason_codes(
    reason_codes: tuple[str, ...],
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if require_nonempty and not reason_codes:
        raise ValueError("reason_codes must not be empty")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_canonical_string("reason_code", reason_code)
        if _contains_sensitive_content(reason_code):
            raise ValueError("reason_codes must not contain sensitive content")
        if not all(char.islower() or char.isdigit() or char == "_" for char in reason_code):
            raise ValueError("reason_code must be lowercase snake case")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(normalized)


def _require_redacted_reference(value: str) -> None:
    if _contains_sensitive_content(value):
        raise ValueError("redacted_team_reference must not contain sensitive content")
    if not value.startswith("team_ref_"):
        raise ValueError("redacted_team_reference must be redacted")


def _contains_sensitive_content(value: str) -> bool:
    lowered = value.lower()
    for token in SENSITIVE_REFERENCE_TOKENS:
        if token == "key":
            continue
        if token in lowered:
            return True
    return "key" in _split_reference_tokens(lowered)


def _split_reference_tokens(value: str) -> tuple[str, ...]:
    normalized = "".join(char if char.isalnum() else "_" for char in value)
    return tuple(part for part in normalized.split("_") if part)


def _reject_sensitive_payload_strings(label: str, value: Any) -> None:
    if isinstance(value, str):
        if _contains_sensitive_content(value):
            raise ValueError(f"sensitive string value in {label}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError(f"JSON object keys must be strings in {label}")
            _reject_sensitive_payload_strings(label, key)
            _reject_sensitive_payload_strings(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_sensitive_payload_strings(label, item)


def _reject_flag_downgrades(label: str, value: Any) -> None:
    if isinstance(value, dict):
        for field_name in ("paper_only", "report_only", "readonly"):
            if field_name in value and value[field_name] is not True:
                raise ValueError(f"{field_name} must be True in {label}")
        for item in value.values():
            _reject_flag_downgrades(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_flag_downgrades(label, item)


def _redacted_reference(value: str) -> str:
    digest = sha256(value.encode("utf-8")).hexdigest()[:16]
    return f"team_ref_{digest}"


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total = _add_decimal(total, value)
    return total


def _add_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (left + right).quantize(QUANTUM)


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (left - right).quantize(QUANTUM)


def _multiply_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (left * right).quantize(QUANTUM)


def _negate_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (-value).quantize(QUANTUM)


def _abs_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return abs(value).quantize(QUANTUM)


def _max_decimal(left: Decimal, right: Decimal) -> Decimal:
    if left >= right:
        return left
    return right
