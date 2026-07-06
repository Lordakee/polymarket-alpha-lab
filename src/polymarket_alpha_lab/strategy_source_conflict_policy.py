"""Pure strategy source conflict policy for paper-only review."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_STRATEGY_SOURCE_CONFLICT_POLICY_CONFIG_VERSION = (
    "strategy-source-conflict-policy-v0"
)
SOURCE_ROLES = ("official", "primary", "supporting")
STATUSES = ("pass", "watch", "blocked")
REASON_CODES = (
    "source_conflict_policy_pass",
    "primary_source_disagreement",
    "stale_vs_fresh_conflict",
    "official_source_override",
    "missing_arbitration",
    "source_conflict_policy_watch",
    "source_conflict_policy_blocked",
)

COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)


@dataclass(frozen=True)
class StrategySourceConflictPolicyConfig:
    config_version: str = DEFAULT_STRATEGY_SOURCE_CONFLICT_POLICY_CONFIG_VERSION
    freshness_window_seconds: Decimal = Decimal("3600.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "freshness_window_seconds",
            _normalize_positive_decimal(
                "freshness_window_seconds",
                self.freshness_window_seconds,
            ),
        )
        require_paper_only_flags("StrategySourceConflictPolicyConfig", self)


@dataclass(frozen=True)
class StrategySourceJudgment:
    strategy_id: str
    market_id: str
    source_family: str
    source_id: str
    source_role: str
    judgment_value: str
    observed_at: datetime
    arbitration_id: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "strategy_id",
            "market_id",
            "source_family",
            "source_id",
            "judgment_value",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_member("source_role", self.source_role, SOURCE_ROLES)
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        object.__setattr__(
            self,
            "arbitration_id",
            _normalize_optional_string("arbitration_id", self.arbitration_id),
        )
        reject_unsafe_surface_fields("strategy source judgment", self)
        require_paper_only_flags("StrategySourceJudgment", self)


@dataclass(frozen=True)
class StrategySourceConflictPolicyDecision:
    generated_at: datetime
    config_version: str
    strategy_id: str
    market_id: str
    source_count: Decimal
    primary_source_count: Decimal
    official_source_count: Decimal
    fresh_source_count: Decimal
    stale_source_count: Decimal
    primary_source_disagreement: bool
    stale_vs_fresh_conflict: bool
    official_source_override: bool
    missing_arbitration: bool
    conflict_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        for field_name in ("config_version", "strategy_id", "market_id"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "source_count",
            "primary_source_count",
            "official_source_count",
            "fresh_source_count",
            "stale_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "primary_source_disagreement",
            "stale_vs_fresh_conflict",
            "official_source_override",
            "missing_arbitration",
        ):
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "conflict_score",
            _normalize_ratio("conflict_score", self.conflict_score),
        )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        reject_unsafe_surface_fields("strategy source conflict policy decision", self)
        require_paper_only_flags("StrategySourceConflictPolicyDecision", self)
        _validate_decision(self)


def evaluate_strategy_source_conflict_policy(
    inputs: list[StrategySourceJudgment] | tuple[StrategySourceJudgment, ...],
    *,
    config: StrategySourceConflictPolicyConfig,
    generated_at: datetime,
) -> StrategySourceConflictPolicyDecision:
    if type(config) is not StrategySourceConflictPolicyConfig:
        raise ValueError("config must be a StrategySourceConflictPolicyConfig")
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _normalize_inputs(inputs, generated_at_utc)

    strategy_ids = {row.strategy_id for row in rows}
    market_ids = {row.market_id for row in rows}
    if len(strategy_ids) != 1:
        raise ValueError("inputs must map to exactly one strategy_id")
    if len(market_ids) != 1:
        raise ValueError("inputs must map to exactly one market_id")

    fresh_rows = tuple(
        row for row in rows if _is_fresh(row, config, generated_at_utc)
    )
    stale_rows = tuple(row for row in rows if row not in fresh_rows)
    primary_source_disagreement = _has_role_disagreement(rows, "primary")
    stale_vs_fresh_conflict = _has_stale_vs_fresh_conflict(fresh_rows, stale_rows)
    official_source_override = _has_official_source_override(fresh_rows, rows)
    has_disagreement = _has_disagreement(rows)
    missing_arbitration = (
        has_disagreement
        and not official_source_override
        and not _has_complete_arbitration(rows)
    )
    status = _decision_status(
        has_disagreement,
        primary_source_disagreement,
        stale_vs_fresh_conflict,
        official_source_override,
        missing_arbitration,
    )
    return StrategySourceConflictPolicyDecision(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        strategy_id=next(iter(strategy_ids)),
        market_id=next(iter(market_ids)),
        source_count=_count(len(rows)),
        primary_source_count=_count(sum(1 for row in rows if row.source_role == "primary")),
        official_source_count=_count(sum(1 for row in rows if row.source_role == "official")),
        fresh_source_count=_count(len(fresh_rows)),
        stale_source_count=_count(len(stale_rows)),
        primary_source_disagreement=primary_source_disagreement,
        stale_vs_fresh_conflict=stale_vs_fresh_conflict,
        official_source_override=official_source_override,
        missing_arbitration=missing_arbitration,
        conflict_score=_conflict_score(
            status,
            has_disagreement,
            stale_vs_fresh_conflict,
            official_source_override,
        ),
        status=status,
        reason_codes=_reason_codes(
            status,
            primary_source_disagreement,
            stale_vs_fresh_conflict,
            official_source_override,
            missing_arbitration,
        ),
    )


def strategy_source_conflict_policy_payload(
    decision: StrategySourceConflictPolicyDecision,
) -> dict[str, Any]:
    if type(decision) is not StrategySourceConflictPolicyDecision:
        raise ValueError("decision must be a StrategySourceConflictPolicyDecision")
    require_paper_only_flags("decision", decision)
    reject_unsafe_surface_fields("strategy source conflict policy decision", decision)
    payload = json_ready_no_floats(decision)
    if type(payload) is not dict:
        raise ValueError("decision payload must be a JSON object")
    return payload


def _normalize_inputs(
    inputs: list[StrategySourceJudgment] | tuple[StrategySourceJudgment, ...],
    generated_at: datetime,
) -> tuple[StrategySourceJudgment, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(inputs)
    if not rows:
        raise ValueError("inputs must not be empty")
    seen: set[tuple[str, str, str, str]] = set()
    for row in rows:
        if type(row) is not StrategySourceJudgment:
            raise ValueError("inputs must contain StrategySourceJudgment values")
        require_paper_only_flags("input", row)
        key = (row.strategy_id, row.market_id, row.source_family, row.source_id)
        if key in seen:
            raise ValueError(
                "inputs must not contain duplicate strategy_id/market_id/source_family/source_id values",
            )
        seen.add(key)
        if row.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    return rows


def _is_fresh(
    row: StrategySourceJudgment,
    config: StrategySourceConflictPolicyConfig,
    generated_at: datetime,
) -> bool:
    return _age_seconds(row, generated_at) <= config.freshness_window_seconds


def _age_seconds(row: StrategySourceJudgment, generated_at: datetime) -> Decimal:
    age_seconds = Decimal(str((generated_at - row.observed_at).total_seconds()))
    return age_seconds.quantize(RATIO_QUANTUM)


def _has_disagreement(rows: tuple[StrategySourceJudgment, ...]) -> bool:
    return len({row.judgment_value for row in rows}) > 1


def _has_role_disagreement(
    rows: tuple[StrategySourceJudgment, ...],
    source_role: str,
) -> bool:
    role_values = {row.judgment_value for row in rows if row.source_role == source_role}
    return len(role_values) > 1


def _has_stale_vs_fresh_conflict(
    fresh_rows: tuple[StrategySourceJudgment, ...],
    stale_rows: tuple[StrategySourceJudgment, ...],
) -> bool:
    if not fresh_rows or not stale_rows:
        return False
    fresh_values = {row.judgment_value for row in fresh_rows}
    stale_values = {row.judgment_value for row in stale_rows}
    return fresh_values != stale_values


def _has_official_source_override(
    fresh_rows: tuple[StrategySourceJudgment, ...],
    rows: tuple[StrategySourceJudgment, ...],
) -> bool:
    official_values = {
        row.judgment_value for row in fresh_rows if row.source_role == "official"
    }
    if len(official_values) != 1:
        return False
    official_value = next(iter(official_values))
    return any(row.judgment_value != official_value for row in rows)


def _has_complete_arbitration(rows: tuple[StrategySourceJudgment, ...]) -> bool:
    if not _has_disagreement(rows):
        return True
    arbitration_ids = {row.arbitration_id for row in rows}
    return len(arbitration_ids) == 1 and None not in arbitration_ids


def _decision_status(
    has_disagreement: bool,
    primary_source_disagreement: bool,
    stale_vs_fresh_conflict: bool,
    official_source_override: bool,
    missing_arbitration: bool,
) -> str:
    if primary_source_disagreement or missing_arbitration:
        return "blocked"
    if has_disagreement or stale_vs_fresh_conflict or official_source_override:
        return "watch"
    return "pass"


def _conflict_score(
    status: str,
    has_disagreement: bool,
    stale_vs_fresh_conflict: bool,
    official_source_override: bool,
) -> Decimal:
    if status == "blocked":
        return ONE_RATIO
    if stale_vs_fresh_conflict or official_source_override:
        return Decimal("0.600000")
    if has_disagreement:
        return Decimal("0.400000")
    return ZERO_RATIO


def _reason_codes(
    status: str,
    primary_source_disagreement: bool,
    stale_vs_fresh_conflict: bool,
    official_source_override: bool,
    missing_arbitration: bool,
) -> tuple[str, ...]:
    if status == "pass":
        return ("source_conflict_policy_pass",)
    codes: list[str] = []
    if primary_source_disagreement:
        codes.append("primary_source_disagreement")
    if stale_vs_fresh_conflict:
        codes.append("stale_vs_fresh_conflict")
    if official_source_override:
        codes.append("official_source_override")
    if missing_arbitration:
        codes.append("missing_arbitration")
    codes.append(f"source_conflict_policy_{status}")
    return tuple(codes)


def _validate_decision(row: StrategySourceConflictPolicyDecision) -> None:
    if row.primary_source_count > row.source_count:
        raise ValueError("primary_source_count must not exceed source_count")
    if row.official_source_count > row.source_count:
        raise ValueError("official_source_count must not exceed source_count")
    if row.fresh_source_count + row.stale_source_count != row.source_count:
        raise ValueError("fresh and stale source counts must match source_count")
    expected_status = _decision_status(
        row.conflict_score > ZERO_RATIO,
        row.primary_source_disagreement,
        row.stale_vs_fresh_conflict,
        row.official_source_override,
        row.missing_arbitration,
    )
    if row.status != expected_status:
        raise ValueError("status must match source conflict flags")
    expected_score = _conflict_score(
        row.status,
        row.conflict_score > ZERO_RATIO,
        row.stale_vs_fresh_conflict,
        row.official_source_override,
    )
    if row.conflict_score != expected_score:
        raise ValueError("conflict_score must match source conflict flags")
    expected_reasons = _reason_codes(
        row.status,
        row.primary_source_disagreement,
        row.stale_vs_fresh_conflict,
        row.official_source_override,
        row.missing_arbitration,
    )
    if row.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match source conflict flags")


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_member("reason_codes", reason_code, REASON_CODES)
    return reason_codes


def _normalize_optional_string(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    _require_canonical_string(field_name, value)
    return value


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value, RATIO_QUANTUM)
    if decimal_value <= ZERO_RATIO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_count(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value, COUNT_QUANTUM)
    if decimal_value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value, RATIO_QUANTUM)
    if decimal_value < ZERO_RATIO or decimal_value > ONE_RATIO:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _normalize_decimal(
    field_name: str,
    value: object,
    quantum: Decimal,
) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    decimal_value = value.quantize(quantum)
    if decimal_value != value:
        raise ValueError(f"{field_name} must use the required decimal precision")
    return decimal_value


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed_values:
        allowed = ", ".join(allowed_values)
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if not value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


__all__ = (
    "DEFAULT_STRATEGY_SOURCE_CONFLICT_POLICY_CONFIG_VERSION",
    "REASON_CODES",
    "SOURCE_ROLES",
    "STATUSES",
    "StrategySourceConflictPolicyConfig",
    "StrategySourceConflictPolicyDecision",
    "StrategySourceJudgment",
    "evaluate_strategy_source_conflict_policy",
    "strategy_source_conflict_policy_payload",
)
