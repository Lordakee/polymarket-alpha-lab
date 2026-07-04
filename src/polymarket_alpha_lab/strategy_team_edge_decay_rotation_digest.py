"""Paper-only strategy team edge-decay rotation diagnostic reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, localcontext
from hashlib import sha256
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


__all__ = (
    "StrategyTeamEdgeDecayRotationDigestConfig",
    "StrategyTeamEdgeDecayRotationDigestReport",
    "StrategyTeamEdgeDecayRotationDigestRow",
    "StrategyTeamEdgeDecayRotationDigestTeam",
    "build_strategy_team_edge_decay_rotation_digest",
    "strategy_team_edge_decay_rotation_digest_payload",
)


DEFAULT_CONFIG_VERSION = "strategy-team-edge-decay-rotation-digest-v0"
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
ROW_STATUSES = ("rotate_out", "watch", "hold")
REPORT_STATUSES = ("pass", "watch", "blocked")
EMPTY_REASON_CODE = "strategy_team_edge_decay_rotation_digest_empty"
ROTATE_OUT_REASON_CODE = "team_edge_decay_rotate_out"
WATCH_REASON_CODE = "team_edge_decay_watch"
HOLD_REASON_CODE = "team_edge_decay_hold"
REPORT_REASON_PRIORITY = (
    ROTATE_OUT_REASON_CODE,
    WATCH_REASON_CODE,
    HOLD_REASON_CODE,
    "edge_decay_high",
    "edge_decay_moderate",
    "edge_decay_low",
    "current_edge_nonpositive",
    "liquidity_capacity_low",
    "drawdown_pressure_high",
    "signal_freshness_stale",
    EMPTY_REASON_CODE,
)
ROW_REASON_PRIORITY = (
    "edge_decay_input",
    ROTATE_OUT_REASON_CODE,
    WATCH_REASON_CODE,
    HOLD_REASON_CODE,
    "edge_decay_high",
    "edge_decay_moderate",
    "edge_decay_low",
    "current_edge_positive",
    "current_edge_nonpositive",
    "liquidity_capacity_available",
    "liquidity_capacity_low",
    "drawdown_pressure_contained",
    "drawdown_pressure_high",
    "signal_freshness_available",
    "signal_freshness_stale",
    EMPTY_REASON_CODE,
)
ROW_STATUS_SORT_PRIORITY = {"rotate_out": 0, "watch": 1, "hold": 2}
REASON_CODE_SORT_PRIORITY = {
    reason_code: index for index, reason_code in enumerate(ROW_REASON_PRIORITY)
}
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
UNSAFE_SURFACE_FIELD_FRAGMENTS = (
    "auth",
    "private_key",
    "wallet",
    "account",
    "balance",
    "order",
    "cancel",
    "replace",
    "signed",
    "signing",
    "signature",
    "exchange_mutation",
)
PUBLIC_TEXT_FORBIDDEN_FRAGMENTS = (
    *SENSITIVE_REFERENCE_TOKENS,
    *UNSAFE_SURFACE_FIELD_FRAGMENTS,
)


@dataclass(frozen=True)
class StrategyTeamEdgeDecayRotationDigestConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    total_paper_capital: Decimal = Decimal("10000.000000")
    rotate_out_decay_ratio: Decimal = Decimal("0.400000")
    watch_decay_ratio: Decimal = Decimal("0.200000")
    block_drawdown_pressure: Decimal = Decimal("0.800000")
    min_liquidity_capacity_share: Decimal = Decimal("0.050000")
    min_signal_freshness: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "total_paper_capital",
            _normalize_positive_decimal("total_paper_capital", self.total_paper_capital),
        )
        for field_name in (
            "rotate_out_decay_ratio",
            "watch_decay_ratio",
            "block_drawdown_pressure",
            "min_liquidity_capacity_share",
            "min_signal_freshness",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_decay_ratio >= self.rotate_out_decay_ratio:
            raise ValueError("watch_decay_ratio must be below rotate_out_decay_ratio")
        require_paper_only_flags("config", self)


@dataclass(frozen=True)
class StrategyTeamEdgeDecayRotationDigestTeam:
    team_id: str
    team_reference: str
    observed_at: datetime
    peak_edge: Decimal
    current_edge: Decimal
    current_budget_share: Decimal
    liquidity_capacity_share: Decimal
    drawdown_pressure: Decimal
    signal_freshness: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_canonical_string("team_id", self.team_id)
        _require_canonical_string("team_reference", self.team_reference)
        object.__setattr__(self, "team_reference", _redacted_reference(self.team_reference))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "peak_edge",
            _normalize_positive_decimal("peak_edge", self.peak_edge),
        )
        object.__setattr__(
            self,
            "current_edge",
            _normalize_decimal("current_edge", self.current_edge),
        )
        for field_name in (
            "current_budget_share",
            "liquidity_capacity_share",
            "drawdown_pressure",
            "signal_freshness",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        require_paper_only_flags("team", self)


@dataclass(frozen=True)
class StrategyTeamEdgeDecayRotationDigestRow:
    team_id: str
    redacted_team_reference: str
    observed_at: datetime
    peak_edge: Decimal
    current_edge: Decimal
    current_budget_share: Decimal
    edge_decay_ratio: Decimal
    edge_retention_ratio: Decimal
    liquidity_capacity_share: Decimal
    drawdown_pressure: Decimal
    signal_freshness: Decimal
    recommended_paper_rotation: Decimal
    rotation_direction: str
    rotation_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_canonical_string("team_id", self.team_id)
        _require_public_canonical_string(
            "redacted_team_reference",
            self.redacted_team_reference,
        )
        _require_redacted_reference(self.redacted_team_reference)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "peak_edge",
            _normalize_positive_decimal("peak_edge", self.peak_edge),
        )
        object.__setattr__(
            self,
            "current_edge",
            _normalize_decimal("current_edge", self.current_edge),
        )
        for field_name in (
            "current_budget_share",
            "edge_decay_ratio",
            "edge_retention_ratio",
            "liquidity_capacity_share",
            "drawdown_pressure",
            "signal_freshness",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "recommended_paper_rotation",
            _normalize_nonnegative_decimal(
                "recommended_paper_rotation",
                self.recommended_paper_rotation,
            ),
        )
        _require_member(
            "rotation_direction",
            self.rotation_direction,
            ("decrease", "hold"),
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
class StrategyTeamEdgeDecayRotationDigestReport:
    generated_at: datetime
    config_version: str
    total_paper_capital: Decimal
    team_count: Decimal
    rotate_out_count: Decimal
    watch_count: Decimal
    hold_count: Decimal
    total_recommended_paper_rotation: Decimal
    max_edge_decay_ratio: Decimal
    average_edge_decay_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyTeamEdgeDecayRotationDigestRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_canonical_string("config_version", self.config_version)
        for field_name in (
            "total_paper_capital",
            "total_recommended_paper_rotation",
            "max_edge_decay_ratio",
            "average_edge_decay_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "team_count",
            "rotate_out_count",
            "watch_count",
            "hold_count",
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
        _reject_unsafe_public_payload("strategy team edge decay rotation digest", self)
        require_paper_only_flags("report", self)


def build_strategy_team_edge_decay_rotation_digest(
    teams: Iterable[object],
    *,
    config: StrategyTeamEdgeDecayRotationDigestConfig,
    generated_at: datetime,
) -> StrategyTeamEdgeDecayRotationDigestReport:
    if type(config) is not StrategyTeamEdgeDecayRotationDigestConfig:
        raise ValueError("config must be a StrategyTeamEdgeDecayRotationDigestConfig")
    generated_at = _as_utc("generated_at", generated_at)
    require_paper_only_flags("config", config)
    source_teams = _normalize_teams(teams)
    rows = tuple(
        sorted(
            (_row_from_team(team, config=config) for team in source_teams),
            key=_row_sort_key,
        ),
    )

    return StrategyTeamEdgeDecayRotationDigestReport(
        generated_at=generated_at,
        config_version=config.config_version,
        total_paper_capital=config.total_paper_capital,
        team_count=_count_decimal(len(rows)),
        rotate_out_count=_status_count(rows, "rotate_out"),
        watch_count=_status_count(rows, "watch"),
        hold_count=_status_count(rows, "hold"),
        total_recommended_paper_rotation=_sum_decimal(
            row.recommended_paper_rotation for row in rows
        ),
        max_edge_decay_ratio=_max_edge_decay_ratio(rows),
        average_edge_decay_ratio=_average_edge_decay_ratio(rows),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def strategy_team_edge_decay_rotation_digest_payload(
    report: StrategyTeamEdgeDecayRotationDigestReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyTeamEdgeDecayRotationDigestReport:
        require_paper_only_flags("report", report)
        _reject_unsafe_public_payload("strategy team edge decay rotation digest", report)
        return _report_payload(report)
    if type(report) is dict:
        _reject_unsafe_public_payload(
            "strategy team edge decay rotation digest payload",
            report,
        )
        ready = json_ready_no_floats(report)
        _reject_unsafe_public_payload(
            "strategy team edge decay rotation digest payload",
            ready,
        )
        require_paper_only_flags("payload", _DictFlags(ready))
        return ready
    raise ValueError("report must be a StrategyTeamEdgeDecayRotationDigestReport")


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


def _report_payload(report: StrategyTeamEdgeDecayRotationDigestReport) -> dict[str, Any]:
    return {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "total_paper_capital": _decimal_payload(report.total_paper_capital),
        "team_count": _count_payload(report.team_count),
        "rotate_out_count": _count_payload(report.rotate_out_count),
        "watch_count": _count_payload(report.watch_count),
        "hold_count": _count_payload(report.hold_count),
        "total_recommended_paper_rotation": _decimal_payload(
            report.total_recommended_paper_rotation,
        ),
        "max_edge_decay_ratio": _decimal_payload(report.max_edge_decay_ratio),
        "average_edge_decay_ratio": _decimal_payload(report.average_edge_decay_ratio),
        "status": report.status,
        "reason_codes": list(report.reason_codes),
        "rows": [_row_payload(row) for row in report.rows],
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _row_payload(row: StrategyTeamEdgeDecayRotationDigestRow) -> dict[str, Any]:
    return {
        "team_id": row.team_id,
        "redacted_team_reference": row.redacted_team_reference,
        "observed_at": row.observed_at.isoformat(),
        "peak_edge": _decimal_payload(row.peak_edge),
        "current_edge": _decimal_payload(row.current_edge),
        "current_budget_share": _decimal_payload(row.current_budget_share),
        "edge_decay_ratio": _decimal_payload(row.edge_decay_ratio),
        "edge_retention_ratio": _decimal_payload(row.edge_retention_ratio),
        "liquidity_capacity_share": _decimal_payload(row.liquidity_capacity_share),
        "drawdown_pressure": _decimal_payload(row.drawdown_pressure),
        "signal_freshness": _decimal_payload(row.signal_freshness),
        "recommended_paper_rotation": _decimal_payload(row.recommended_paper_rotation),
        "rotation_direction": row.rotation_direction,
        "rotation_status": row.rotation_status,
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _decimal_payload(value: Decimal) -> str:
    return format(_normalize_decimal("payload decimal", value), "f")


def _count_payload(value: Decimal) -> str:
    return str(int(_normalize_count_decimal("payload count", value)))


def _row_from_team(
    team: StrategyTeamEdgeDecayRotationDigestTeam,
    *,
    config: StrategyTeamEdgeDecayRotationDigestConfig,
) -> StrategyTeamEdgeDecayRotationDigestRow:
    edge_decay_ratio = _edge_decay_ratio(team.current_edge, team.peak_edge)
    edge_retention_ratio = _subtract_decimal(ONE, edge_decay_ratio)
    rotation_status, terminal_reason = _rotation_status_and_reason(
        edge_decay_ratio=edge_decay_ratio,
        current_edge=team.current_edge,
        liquidity_capacity_share=team.liquidity_capacity_share,
        drawdown_pressure=team.drawdown_pressure,
        signal_freshness=team.signal_freshness,
        config=config,
    )
    return StrategyTeamEdgeDecayRotationDigestRow(
        team_id=team.team_id,
        redacted_team_reference=team.team_reference,
        observed_at=team.observed_at,
        peak_edge=team.peak_edge,
        current_edge=team.current_edge,
        current_budget_share=team.current_budget_share,
        edge_decay_ratio=edge_decay_ratio,
        edge_retention_ratio=edge_retention_ratio,
        liquidity_capacity_share=team.liquidity_capacity_share,
        drawdown_pressure=team.drawdown_pressure,
        signal_freshness=team.signal_freshness,
        recommended_paper_rotation=_recommended_paper_rotation(
            current_budget_share=team.current_budget_share,
            edge_decay_ratio=edge_decay_ratio,
            rotation_status=rotation_status,
            config=config,
        ),
        rotation_direction=_rotation_direction(rotation_status),
        rotation_status=rotation_status,
        reason_codes=_normalize_reason_codes(
            (
                *team.reason_codes,
                terminal_reason,
                *_diagnostic_reason_codes(
                    edge_decay_ratio=edge_decay_ratio,
                    current_edge=team.current_edge,
                    liquidity_capacity_share=team.liquidity_capacity_share,
                    drawdown_pressure=team.drawdown_pressure,
                    signal_freshness=team.signal_freshness,
                    config=config,
                ),
            ),
            require_nonempty=True,
        ),
    )


def _edge_decay_ratio(current_edge: Decimal, peak_edge: Decimal) -> Decimal:
    if current_edge <= ZERO:
        return ONE
    decay = _ratio_decimal(_subtract_decimal(peak_edge, current_edge), peak_edge)
    if decay < ZERO:
        return ZERO
    if decay > ONE:
        return ONE
    return decay


def _rotation_status_and_reason(
    *,
    edge_decay_ratio: Decimal,
    current_edge: Decimal,
    liquidity_capacity_share: Decimal,
    drawdown_pressure: Decimal,
    signal_freshness: Decimal,
    config: StrategyTeamEdgeDecayRotationDigestConfig,
) -> tuple[str, str]:
    if (
        current_edge <= ZERO
        or liquidity_capacity_share < config.min_liquidity_capacity_share
        or drawdown_pressure >= config.block_drawdown_pressure
        or signal_freshness < config.min_signal_freshness
        or edge_decay_ratio >= config.rotate_out_decay_ratio
    ):
        return "rotate_out", ROTATE_OUT_REASON_CODE
    if edge_decay_ratio >= config.watch_decay_ratio:
        return "watch", WATCH_REASON_CODE
    return "hold", HOLD_REASON_CODE


def _recommended_paper_rotation(
    *,
    current_budget_share: Decimal,
    edge_decay_ratio: Decimal,
    rotation_status: str,
    config: StrategyTeamEdgeDecayRotationDigestConfig,
) -> Decimal:
    if rotation_status != "rotate_out":
        return ZERO
    return _multiply_decimal(
        config.total_paper_capital,
        _multiply_decimal(current_budget_share, edge_decay_ratio),
    )


def _diagnostic_reason_codes(
    *,
    edge_decay_ratio: Decimal,
    current_edge: Decimal,
    liquidity_capacity_share: Decimal,
    drawdown_pressure: Decimal,
    signal_freshness: Decimal,
    config: StrategyTeamEdgeDecayRotationDigestConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if edge_decay_ratio >= config.rotate_out_decay_ratio:
        reason_codes.append("edge_decay_high")
    elif edge_decay_ratio >= config.watch_decay_ratio:
        reason_codes.append("edge_decay_moderate")
    else:
        reason_codes.append("edge_decay_low")
    if current_edge > ZERO:
        reason_codes.append("current_edge_positive")
    else:
        reason_codes.append("current_edge_nonpositive")
    if liquidity_capacity_share < config.min_liquidity_capacity_share:
        reason_codes.append("liquidity_capacity_low")
    else:
        reason_codes.append("liquidity_capacity_available")
    if drawdown_pressure >= config.block_drawdown_pressure:
        reason_codes.append("drawdown_pressure_high")
    else:
        reason_codes.append("drawdown_pressure_contained")
    if signal_freshness < config.min_signal_freshness:
        reason_codes.append("signal_freshness_stale")
    else:
        reason_codes.append("signal_freshness_available")
    return tuple(reason_codes)


def _rotation_direction(rotation_status: str) -> str:
    if rotation_status == "rotate_out":
        return "decrease"
    return "hold"


def _normalize_teams(
    teams: Iterable[object],
) -> tuple[StrategyTeamEdgeDecayRotationDigestTeam, ...]:
    if isinstance(teams, (str, bytes)):
        raise ValueError("teams must be an iterable")
    try:
        normalized = tuple(teams)
    except TypeError as exc:
        raise ValueError("teams must be an iterable") from exc
    seen: set[str] = set()
    for team in normalized:
        if type(team) is not StrategyTeamEdgeDecayRotationDigestTeam:
            raise ValueError("team must be a StrategyTeamEdgeDecayRotationDigestTeam")
        require_paper_only_flags("team", team)
        if team.team_id in seen:
            raise ValueError("duplicate team_id")
        seen.add(team.team_id)
    return normalized


def _normalize_rows(
    rows: tuple[StrategyTeamEdgeDecayRotationDigestRow, ...],
) -> tuple[StrategyTeamEdgeDecayRotationDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not StrategyTeamEdgeDecayRotationDigestRow:
            raise ValueError("row must be a StrategyTeamEdgeDecayRotationDigestRow")
        require_paper_only_flags("row", row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be deterministically sorted")
    return rows


def _row_sort_key(
    row: StrategyTeamEdgeDecayRotationDigestRow,
) -> tuple[int, Decimal, Decimal, str, str]:
    return (
        ROW_STATUS_SORT_PRIORITY[row.rotation_status],
        -row.edge_decay_ratio,
        -row.recommended_paper_rotation,
        row.team_id,
        row.redacted_team_reference,
    )


def _status_count(
    rows: tuple[StrategyTeamEdgeDecayRotationDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.rotation_status == status))


def _max_edge_decay_ratio(
    rows: tuple[StrategyTeamEdgeDecayRotationDigestRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return max(row.edge_decay_ratio for row in rows)


def _average_edge_decay_ratio(
    rows: tuple[StrategyTeamEdgeDecayRotationDigestRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return _ratio_decimal(
        _sum_decimal(row.edge_decay_ratio for row in rows),
        _count_decimal(len(rows)),
    )


def _report_status(rows: tuple[StrategyTeamEdgeDecayRotationDigestRow, ...]) -> str:
    if not rows:
        return "watch"
    if any(row.rotation_status == "rotate_out" for row in rows):
        return "blocked"
    if any(row.rotation_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[StrategyTeamEdgeDecayRotationDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    found = {reason_code for row in rows for reason_code in row.reason_codes}
    return tuple(reason_code for reason_code in REPORT_REASON_PRIORITY if reason_code in found)


def _validate_row(row: StrategyTeamEdgeDecayRotationDigestRow) -> None:
    if row.edge_decay_ratio != _edge_decay_ratio(row.current_edge, row.peak_edge):
        raise ValueError("edge_decay_ratio must match edge inputs")
    if row.edge_retention_ratio != _subtract_decimal(ONE, row.edge_decay_ratio):
        raise ValueError("edge_retention_ratio must match edge_decay_ratio")
    if row.rotation_direction != _rotation_direction(row.rotation_status):
        raise ValueError("rotation_direction must match rotation_status")
    expected_status = _row_status(row.reason_codes)
    if row.rotation_status != expected_status:
        raise ValueError("rotation_status must match reason_codes")
    if row.rotation_status != "rotate_out" and row.recommended_paper_rotation != ZERO:
        raise ValueError("recommended_paper_rotation must be zero unless rotate_out")


def _validate_report(report: StrategyTeamEdgeDecayRotationDigestReport) -> None:
    if report.team_count != _count_decimal(len(report.rows)):
        raise ValueError("team_count must match rows")
    if report.rotate_out_count != _status_count(report.rows, "rotate_out"):
        raise ValueError("rotate_out_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.hold_count != _status_count(report.rows, "hold"):
        raise ValueError("hold_count must match rows")
    if report.total_recommended_paper_rotation != _sum_decimal(
        row.recommended_paper_rotation for row in report.rows
    ):
        raise ValueError("total_recommended_paper_rotation must match rows")
    if report.max_edge_decay_ratio != _max_edge_decay_ratio(report.rows):
        raise ValueError("max_edge_decay_ratio must match rows")
    if report.average_edge_decay_ratio != _average_edge_decay_ratio(report.rows):
        raise ValueError("average_edge_decay_ratio must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if ROTATE_OUT_REASON_CODE in reason_codes:
        return "rotate_out"
    if WATCH_REASON_CODE in reason_codes:
        return "watch"
    if HOLD_REASON_CODE in reason_codes:
        return "hold"
    raise ValueError("reason_codes must include a rotation status code")


def _reject_unsafe_surface_fields(label: str, payload: object) -> None:
    for key in _iter_keys(payload):
        normalized_key = key.lower()
        if any(fragment in normalized_key for fragment in UNSAFE_SURFACE_FIELD_FRAGMENTS):
            raise ValueError(f"unsafe live surface field in {label}: {key}")


def _iter_keys(value: object) -> tuple[str, ...]:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _iter_keys(json_ready_no_floats(value))
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


def _as_utc(field_name: str, value: Any) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: Any) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")


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
        lowered = reason_code.lower()
        if any(token in lowered for token in SENSITIVE_REFERENCE_TOKENS):
            raise ValueError("reason_codes must not contain sensitive content")
        if not all(char.islower() or char.isdigit() or char == "_" for char in reason_code):
            raise ValueError("reason_code must be lowercase snake case")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(sorted(normalized, key=_reason_code_sort_key))


def _reason_code_sort_key(reason_code: str) -> tuple[int, str]:
    return (
        REASON_CODE_SORT_PRIORITY.get(reason_code, len(REASON_CODE_SORT_PRIORITY)),
        reason_code,
    )


def _require_public_canonical_string(field_name: str, value: Any) -> None:
    _require_canonical_string(field_name, value)
    _require_no_sensitive_public_text(field_name, value)


def _require_redacted_reference(value: str) -> None:
    lowered = value.lower()
    if any(token in lowered for token in SENSITIVE_REFERENCE_TOKENS):
        raise ValueError("redacted_team_reference must not contain sensitive content")
    if not value.startswith("team_ref_"):
        raise ValueError("redacted_team_reference must be redacted")


def _redacted_reference(value: str) -> str:
    digest = sha256(value.encode("utf-8")).hexdigest()[:16]
    return f"team_ref_{digest}"


def _reject_unsafe_public_payload(label: str, payload: object) -> None:
    _reject_unsafe_surface_fields(label, payload)
    _reject_sensitive_public_values(payload)


def _reject_sensitive_public_values(payload: object) -> None:
    for value in _iter_string_values(payload):
        _require_no_sensitive_public_text("payload string value", value)


def _require_no_sensitive_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in PUBLIC_TEXT_FORBIDDEN_FRAGMENTS):
        raise ValueError(f"{field_name} must not contain sensitive content")


def _iter_string_values(value: object) -> tuple[str, ...]:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _iter_string_values(json_ready_no_floats(value))
    if type(value) is str:
        return (value,)
    if isinstance(value, dict):
        values: list[str] = []
        for item in value.values():
            values.extend(_iter_string_values(item))
        return tuple(values)
    if isinstance(value, (list, tuple)):
        values = []
        for item in value:
            values.extend(_iter_string_values(item))
        return tuple(values)
    return ()


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


def _ratio_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (left / right).quantize(QUANTUM)
