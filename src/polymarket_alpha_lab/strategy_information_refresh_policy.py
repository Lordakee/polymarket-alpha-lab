"""Pure read-only strategy information refresh policy.

The reducer turns caller-supplied in-memory signal snapshots into deterministic
paper/report/readonly refresh decisions. It performs no IO, persistence, network
access, credential handling, or execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_STRATEGY_INFORMATION_REFRESH_POLICY_CONFIG_VERSION = (
    "strategy-information-refresh-policy-v0"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
COUNT_QUANTUM = Decimal("1")
SECONDS_QUANTUM = Decimal("0.000001")
PROBABILITY_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0").quantize(COUNT_QUANTUM)
ZERO_SECONDS = Decimal("0").quantize(SECONDS_QUANTUM)
ZERO_PROBABILITY = Decimal("0").quantize(PROBABILITY_QUANTUM)
ONE_PROBABILITY = Decimal("1").quantize(PROBABILITY_QUANTUM)

SOURCE_CRITICALITIES = ("low", "medium", "high", "critical")
DECISIONS = ("refresh_now", "watch", "no_refresh")
DECISION_WEIGHT = {"refresh_now": 0, "watch": 1, "no_refresh": 2}

MARKET_CLOSE_IMMINENT_REASON = "market_close_imminent"
MARKET_CLOSE_APPROACHING_REASON = "market_close_approaching"
SOURCE_TIMESTAMP_MISSING_REASON = "source_timestamp_missing"
CRITICAL_SOURCE_STALE_REASON = "critical_source_stale"
SOURCE_STALE_REASON = "source_stale"
MATERIAL_PROBABILITY_MOVEMENT_REASON = "material_probability_movement"
NOTABLE_PROBABILITY_MOVEMENT_REASON = "notable_probability_movement"
TEAM_CONFIDENCE_REFRESH_NOW_REASON = "team_confidence_refresh_now"
TEAM_CONFIDENCE_WATCH_REASON = "team_confidence_watch"
NO_REFRESH_REASON = "information_refresh_not_needed"

REASON_CODES = (
    MARKET_CLOSE_IMMINENT_REASON,
    MARKET_CLOSE_APPROACHING_REASON,
    SOURCE_TIMESTAMP_MISSING_REASON,
    CRITICAL_SOURCE_STALE_REASON,
    SOURCE_STALE_REASON,
    MATERIAL_PROBABILITY_MOVEMENT_REASON,
    NOTABLE_PROBABILITY_MOVEMENT_REASON,
    TEAM_CONFIDENCE_REFRESH_NOW_REASON,
    TEAM_CONFIDENCE_WATCH_REASON,
    NO_REFRESH_REASON,
)

REFRESH_NOW_REASONS = (
    MARKET_CLOSE_IMMINENT_REASON,
    SOURCE_TIMESTAMP_MISSING_REASON,
    CRITICAL_SOURCE_STALE_REASON,
    MATERIAL_PROBABILITY_MOVEMENT_REASON,
    TEAM_CONFIDENCE_REFRESH_NOW_REASON,
)

__all__ = (
    "DEFAULT_STRATEGY_INFORMATION_REFRESH_POLICY_CONFIG_VERSION",
    "StrategyInformationRefreshPolicyConfig",
    "StrategyInformationRefreshPolicyDecision",
    "StrategyInformationRefreshPolicyReport",
    "StrategyInformationRefreshSignal",
    "build_strategy_information_refresh_policy",
    "strategy_information_refresh_policy_payload",
)


@dataclass(frozen=True)
class StrategyInformationRefreshPolicyConfig:
    config_version: str = DEFAULT_STRATEGY_INFORMATION_REFRESH_POLICY_CONFIG_VERSION
    refresh_now_close_window_seconds: Decimal = Decimal("900.000000")
    watch_close_window_seconds: Decimal = Decimal("3600.000000")
    source_stale_watch_seconds: Decimal = Decimal("3600.000000")
    source_stale_refresh_now_seconds: Decimal = Decimal("21600.000000")
    critical_source_stale_refresh_now_seconds: Decimal = Decimal("1800.000000")
    watch_probability_movement: Decimal = Decimal("0.030000")
    material_probability_movement: Decimal = Decimal("0.100000")
    team_confidence_watch_threshold: Decimal = Decimal("0.600000")
    team_confidence_refresh_now_threshold: Decimal = Decimal("0.350000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "refresh_now_close_window_seconds",
            "watch_close_window_seconds",
            "source_stale_watch_seconds",
            "source_stale_refresh_now_seconds",
            "critical_source_stale_refresh_now_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_seconds(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_probability_movement",
            "material_probability_movement",
            "team_confidence_watch_threshold",
            "team_confidence_refresh_now_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.refresh_now_close_window_seconds > self.watch_close_window_seconds:
            raise ValueError(
                "refresh_now_close_window_seconds must not exceed "
                "watch_close_window_seconds",
            )
        if self.source_stale_watch_seconds > self.source_stale_refresh_now_seconds:
            raise ValueError(
                "source_stale_watch_seconds must not exceed "
                "source_stale_refresh_now_seconds",
            )
        if self.watch_probability_movement > self.material_probability_movement:
            raise ValueError(
                "watch_probability_movement must not exceed "
                "material_probability_movement",
            )
        if (
            self.team_confidence_refresh_now_threshold
            > self.team_confidence_watch_threshold
        ):
            raise ValueError(
                "team_confidence_refresh_now_threshold must not exceed "
                "team_confidence_watch_threshold",
            )
        require_paper_only_flags("StrategyInformationRefreshPolicyConfig", self)


@dataclass(frozen=True)
class StrategyInformationRefreshSignal:
    market_id: str
    team_id: str
    market_close_time: datetime
    last_source_timestamp: datetime | None
    source_criticality: str
    previous_probability: Decimal
    current_probability: Decimal
    team_confidence: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("market_id", self.market_id)
        _require_public_string("team_id", self.team_id)
        object.__setattr__(
            self,
            "market_close_time",
            _as_utc("market_close_time", self.market_close_time),
        )
        object.__setattr__(
            self,
            "last_source_timestamp",
            _as_optional_utc("last_source_timestamp", self.last_source_timestamp),
        )
        _require_member("source_criticality", self.source_criticality, SOURCE_CRITICALITIES)
        for field_name in ("previous_probability", "current_probability", "team_confidence"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("StrategyInformationRefreshSignal", self)


@dataclass(frozen=True)
class StrategyInformationRefreshPolicyDecision:
    market_id: str
    team_id: str
    decision: str
    market_close_time: datetime
    time_to_close_seconds: Decimal
    last_source_timestamp: datetime | None
    source_age_seconds: Decimal | None
    source_criticality: str
    previous_probability: Decimal
    current_probability: Decimal
    probability_movement: Decimal
    team_confidence: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("market_id", self.market_id)
        _require_public_string("team_id", self.team_id)
        _require_member("decision", self.decision, DECISIONS)
        object.__setattr__(
            self,
            "market_close_time",
            _as_utc("market_close_time", self.market_close_time),
        )
        object.__setattr__(
            self,
            "time_to_close_seconds",
            _normalize_nonnegative_seconds(
                "time_to_close_seconds",
                self.time_to_close_seconds,
            ),
        )
        object.__setattr__(
            self,
            "last_source_timestamp",
            _as_optional_utc("last_source_timestamp", self.last_source_timestamp),
        )
        object.__setattr__(
            self,
            "source_age_seconds",
            _normalize_optional_nonnegative_seconds(
                "source_age_seconds",
                self.source_age_seconds,
            ),
        )
        _require_member("source_criticality", self.source_criticality, SOURCE_CRITICALITIES)
        for field_name in ("previous_probability", "current_probability", "team_confidence"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "probability_movement",
            _normalize_probability("probability_movement", self.probability_movement),
        )
        if self.probability_movement != _probability_movement(
            self.previous_probability,
            self.current_probability,
        ):
            raise ValueError("probability_movement must match probabilities")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_decision_reason_codes(self.decision, self.reason_codes)
        require_paper_only_flags("StrategyInformationRefreshPolicyDecision", self)


@dataclass(frozen=True)
class StrategyInformationRefreshPolicyReport:
    generated_at: datetime
    config_version: str
    signal_count: Decimal
    refresh_now_count: Decimal
    watch_count: Decimal
    no_refresh_count: Decimal
    decisions: tuple[StrategyInformationRefreshPolicyDecision, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "signal_count",
            "refresh_now_count",
            "watch_count",
            "no_refresh_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "decisions", _normalize_decisions(self.decisions))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        require_paper_only_flags("StrategyInformationRefreshPolicyReport", self)


def build_strategy_information_refresh_policy(
    signals: list[StrategyInformationRefreshSignal]
    | tuple[StrategyInformationRefreshSignal, ...],
    *,
    config: StrategyInformationRefreshPolicyConfig,
    generated_at: datetime,
) -> StrategyInformationRefreshPolicyReport:
    if type(config) is not StrategyInformationRefreshPolicyConfig:
        raise ValueError("config must be a StrategyInformationRefreshPolicyConfig")
    require_paper_only_flags("StrategyInformationRefreshPolicyConfig", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_signals = _normalize_signals(signals)
    decisions = tuple(
        sorted(
            (
                _decision_from_signal(
                    signal,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for signal in source_signals
            ),
            key=_decision_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(decisions)

    return StrategyInformationRefreshPolicyReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        signal_count=_count(len(decisions)),
        refresh_now_count=_decision_count(decisions, "refresh_now"),
        watch_count=_decision_count(decisions, "watch"),
        no_refresh_count=_decision_count(decisions, "no_refresh"),
        decisions=decisions,
        reason_codes=reason_codes,
    )


def strategy_information_refresh_policy_payload(
    report: StrategyInformationRefreshPolicyReport,
) -> dict[str, Any]:
    if type(report) is not StrategyInformationRefreshPolicyReport:
        raise ValueError("report must be a StrategyInformationRefreshPolicyReport")
    require_paper_only_flags("StrategyInformationRefreshPolicyReport", report)
    ready = json_ready_no_floats(report)
    if not isinstance(ready, dict):
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_values(ready)
    return ready


def _normalize_signals(value: object) -> tuple[StrategyInformationRefreshSignal, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("signals must be a list or tuple")
    signals = tuple(value)
    seen_market_ids: set[str] = set()
    for signal in signals:
        if type(signal) is not StrategyInformationRefreshSignal:
            raise ValueError(
                "signals must contain StrategyInformationRefreshSignal values",
            )
        require_paper_only_flags("StrategyInformationRefreshSignal", signal)
        if signal.market_id in seen_market_ids:
            raise ValueError("duplicate market_id values are not allowed")
        seen_market_ids.add(signal.market_id)
    return signals


def _decision_from_signal(
    signal: StrategyInformationRefreshSignal,
    *,
    config: StrategyInformationRefreshPolicyConfig,
    generated_at: datetime,
) -> StrategyInformationRefreshPolicyDecision:
    if signal.last_source_timestamp is not None and signal.last_source_timestamp > generated_at:
        raise ValueError("future last_source_timestamp values are not allowed")
    time_to_close_seconds = _time_to_close_seconds(signal.market_close_time, generated_at)
    source_age_seconds = _optional_age_seconds(signal.last_source_timestamp, generated_at)
    probability_movement = _probability_movement(
        signal.previous_probability,
        signal.current_probability,
    )
    reason_codes, source_forces_refresh_now = _reason_codes_for_signal(
        signal,
        config=config,
        time_to_close_seconds=time_to_close_seconds,
        source_age_seconds=source_age_seconds,
        probability_movement=probability_movement,
    )
    return StrategyInformationRefreshPolicyDecision(
        market_id=signal.market_id,
        team_id=signal.team_id,
        decision=_decision_from_reasons(reason_codes, source_forces_refresh_now),
        market_close_time=signal.market_close_time,
        time_to_close_seconds=time_to_close_seconds,
        last_source_timestamp=signal.last_source_timestamp,
        source_age_seconds=source_age_seconds,
        source_criticality=signal.source_criticality,
        previous_probability=signal.previous_probability,
        current_probability=signal.current_probability,
        probability_movement=probability_movement,
        team_confidence=signal.team_confidence,
        reason_codes=reason_codes,
    )


def _reason_codes_for_signal(
    signal: StrategyInformationRefreshSignal,
    *,
    config: StrategyInformationRefreshPolicyConfig,
    time_to_close_seconds: Decimal,
    source_age_seconds: Decimal | None,
    probability_movement: Decimal,
) -> tuple[tuple[str, ...], bool]:
    reasons: list[str] = []
    source_forces_refresh_now = False

    if time_to_close_seconds <= config.refresh_now_close_window_seconds:
        reasons.append(MARKET_CLOSE_IMMINENT_REASON)
    elif time_to_close_seconds <= config.watch_close_window_seconds:
        reasons.append(MARKET_CLOSE_APPROACHING_REASON)

    if source_age_seconds is None:
        reasons.append(SOURCE_TIMESTAMP_MISSING_REASON)
    elif (
        signal.source_criticality == "critical"
        and source_age_seconds >= config.critical_source_stale_refresh_now_seconds
    ):
        reasons.append(CRITICAL_SOURCE_STALE_REASON)
    elif source_age_seconds >= config.source_stale_refresh_now_seconds:
        reasons.append(SOURCE_STALE_REASON)
        source_forces_refresh_now = True
    elif source_age_seconds >= config.source_stale_watch_seconds:
        reasons.append(SOURCE_STALE_REASON)

    if probability_movement >= config.material_probability_movement:
        reasons.append(MATERIAL_PROBABILITY_MOVEMENT_REASON)
    elif probability_movement >= config.watch_probability_movement:
        reasons.append(NOTABLE_PROBABILITY_MOVEMENT_REASON)

    if signal.team_confidence <= config.team_confidence_refresh_now_threshold:
        reasons.append(TEAM_CONFIDENCE_REFRESH_NOW_REASON)
    elif signal.team_confidence <= config.team_confidence_watch_threshold:
        reasons.append(TEAM_CONFIDENCE_WATCH_REASON)

    if not reasons:
        reasons.append(NO_REFRESH_REASON)
    return (
        tuple(code for code in REASON_CODES if code in reasons),
        source_forces_refresh_now,
    )


def _decision_from_reasons(
    reason_codes: tuple[str, ...],
    source_forces_refresh_now: bool,
) -> str:
    if reason_codes == (NO_REFRESH_REASON,):
        return "no_refresh"
    if source_forces_refresh_now or any(code in REFRESH_NOW_REASONS for code in reason_codes):
        return "refresh_now"
    return "watch"


def _report_reason_codes(
    decisions: tuple[StrategyInformationRefreshPolicyDecision, ...],
) -> tuple[str, ...]:
    if not decisions:
        return (NO_REFRESH_REASON,)
    return tuple(
        code
        for code in REASON_CODES
        if any(code in decision.reason_codes for decision in decisions)
    )


def _decision_count(
    decisions: tuple[StrategyInformationRefreshPolicyDecision, ...],
    decision: str,
) -> Decimal:
    return _count(sum(1 for row in decisions if row.decision == decision))


def _normalize_decisions(
    value: object,
) -> tuple[StrategyInformationRefreshPolicyDecision, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("decisions must be a list or tuple")
    decisions = tuple(value)
    seen_market_ids: set[str] = set()
    for decision in decisions:
        if type(decision) is not StrategyInformationRefreshPolicyDecision:
            raise ValueError(
                "decisions must contain StrategyInformationRefreshPolicyDecision values",
            )
        require_paper_only_flags("StrategyInformationRefreshPolicyDecision", decision)
        if decision.market_id in seen_market_ids:
            raise ValueError("duplicate market_id values are not allowed")
        seen_market_ids.add(decision.market_id)
    return tuple(sorted(decisions, key=_decision_sort_key))


def _validate_decision_reason_codes(
    decision: str,
    reason_codes: tuple[str, ...],
) -> None:
    if reason_codes == (NO_REFRESH_REASON,):
        if decision != "no_refresh":
            raise ValueError("decision must match reason_codes")
        return
    if decision == "no_refresh":
        raise ValueError("decision must match reason_codes")


def _validate_report(report: StrategyInformationRefreshPolicyReport) -> None:
    expected_counts = {
        "signal_count": _count(len(report.decisions)),
        "refresh_now_count": _decision_count(report.decisions, "refresh_now"),
        "watch_count": _decision_count(report.decisions, "watch"),
        "no_refresh_count": _decision_count(report.decisions, "no_refresh"),
    }
    for field_name, expected in expected_counts.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match decisions")
    if report.reason_codes != _report_reason_codes(report.decisions):
        raise ValueError("reason_codes must match decisions")
    if report.decisions != tuple(sorted(report.decisions, key=_decision_sort_key)):
        raise ValueError("decisions must be deterministic")


def _decision_sort_key(
    decision: StrategyInformationRefreshPolicyDecision,
) -> tuple[int, str]:
    return (DECISION_WEIGHT[decision.decision], decision.market_id)


def _time_to_close_seconds(close_time: datetime, generated_at: datetime) -> Decimal:
    if close_time <= generated_at:
        return ZERO_SECONDS
    return _age_seconds(generated_at, close_time)


def _optional_age_seconds(value: datetime | None, generated_at: datetime) -> Decimal | None:
    if value is None:
        return None
    return _age_seconds(value, generated_at)


def _age_seconds(value: datetime, generated_at: datetime) -> Decimal:
    delta = generated_at - value
    seconds = Decimal(delta.days * 86_400 + delta.seconds)
    fractional_seconds = Decimal(delta.microseconds) / Decimal(1_000_000)
    with localcontext(DECIMAL_CONTEXT):
        return (seconds + fractional_seconds).quantize(SECONDS_QUANTUM)


def _probability_movement(
    previous_probability: Decimal,
    current_probability: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return abs(current_probability - previous_probability).quantize(PROBABILITY_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(COUNT_QUANTUM)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != _require_decimal(field_name, value):
        raise ValueError(f"{field_name} must be a whole number")
    return normalized


def _normalize_positive_seconds(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_seconds(field_name, value)
    if normalized <= ZERO_SECONDS:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_seconds(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(SECONDS_QUANTUM)
    if normalized < ZERO_SECONDS:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_optional_nonnegative_seconds(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_seconds(field_name, value)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(PROBABILITY_QUANTUM)
    if normalized < ZERO_PROBABILITY:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized > ONE_PROBABILITY:
        raise ValueError(f"{field_name} must be at most 1")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    for fragment in (
        "wallet",
        "account",
        "broker",
        "auth",
        "secret",
        "private_key",
    ):
        if fragment in lowered:
            raise ValueError(f"{field_name} must not name an unsafe live surface")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_member(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be known")


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    codes = tuple(value)
    if not codes:
        raise ValueError("reason_codes must not be empty")
    for code in codes:
        _require_member("reason_codes", code, REASON_CODES)
    if len(set(codes)) != len(codes):
        raise ValueError("reason_codes must be unique")
    if tuple(code for code in REASON_CODES if code in codes) != codes:
        raise ValueError("reason_codes must be deterministic")
    if NO_REFRESH_REASON in codes and len(codes) != 1:
        raise ValueError("information_refresh_not_needed must be alone")
    return codes


def _normalize_report_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    codes = tuple(value)
    if not codes:
        raise ValueError("reason_codes must not be empty")
    for code in codes:
        _require_member("reason_codes", code, REASON_CODES)
    if len(set(codes)) != len(codes):
        raise ValueError("reason_codes must be unique")
    if tuple(code for code in REASON_CODES if code in codes) != codes:
        raise ValueError("reason_codes must be deterministic")
    return codes


def _reject_unsafe_public_values(value: object) -> None:
    if isinstance(value, dict):
        for nested in value.values():
            _reject_unsafe_public_values(nested)
        return
    if isinstance(value, list):
        for nested in value:
            _reject_unsafe_public_values(nested)
        return
    if type(value) is str:
        lowered = value.lower()
        for fragment in (
            "wallet",
            "account",
            "order",
            "trade",
            "advice",
            "auth",
            "broker",
            "investment",
            "private_key",
            "secret",
        ):
            if fragment in lowered:
                raise ValueError("unsafe live surface value in payload")
