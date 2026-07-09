"""Pure report-only analyst signal conflict memory router."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_RESEARCH_STRATEGY_TEAM_SIGNAL_CONFLICT_MEMORY_ROUTER_CONFIG_VERSION = (
    "research-strategy-team-signal-conflict-memory-router-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
SIGNAL_CONFLICT_MEMORY_ROUTE_STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)
_STATUS_SORT_WEIGHT = {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}
_DIRECTIONS = ("support", "neutral", "oppose")

_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_TWO = Decimal("2.000000")
_FIVE = Decimal("5.000000")
_QUANTUM = Decimal("0.000001")
_COUNT_QUANTUM = Decimal("1")
_MICROSECONDS_PER_SECOND = Decimal("1000000.000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

PASS_REASON = "analyst_signal_conflict_route_pass"
EMPTY_REASON = "analyst_signal_conflict_router_empty"
CALIBRATION_BLOCK_REASON = "calibration_memory_block"
CALIBRATION_WATCH_REASON = "calibration_memory_watch"
MEMORY_FRESHNESS_BLOCK_REASON = "memory_freshness_block"
MEMORY_FRESHNESS_WATCH_REASON = "memory_freshness_watch"
EVIDENCE_FRESHNESS_BLOCK_REASON = "evidence_freshness_block"
EVIDENCE_FRESHNESS_WATCH_REASON = "evidence_freshness_watch"
DISAGREEMENT_SEVERITY_BLOCK_REASON = "disagreement_severity_block"
DISAGREEMENT_SEVERITY_WATCH_REASON = "disagreement_severity_watch"
LIQUIDITY_COST_PRESSURE_BLOCK_REASON = "liquidity_cost_pressure_block"
LIQUIDITY_COST_PRESSURE_WATCH_REASON = "liquidity_cost_pressure_watch"

_BLOCK_REASONS = frozenset(
    (
        CALIBRATION_BLOCK_REASON,
        MEMORY_FRESHNESS_BLOCK_REASON,
        EVIDENCE_FRESHNESS_BLOCK_REASON,
        DISAGREEMENT_SEVERITY_BLOCK_REASON,
        LIQUIDITY_COST_PRESSURE_BLOCK_REASON,
    ),
)
_ROW_REASON_PRIORITY = (
    CALIBRATION_BLOCK_REASON,
    MEMORY_FRESHNESS_BLOCK_REASON,
    EVIDENCE_FRESHNESS_BLOCK_REASON,
    DISAGREEMENT_SEVERITY_BLOCK_REASON,
    LIQUIDITY_COST_PRESSURE_BLOCK_REASON,
    CALIBRATION_WATCH_REASON,
    MEMORY_FRESHNESS_WATCH_REASON,
    EVIDENCE_FRESHNESS_WATCH_REASON,
    DISAGREEMENT_SEVERITY_WATCH_REASON,
    LIQUIDITY_COST_PRESSURE_WATCH_REASON,
    PASS_REASON,
)
_REPORT_REASON_PRIORITY = _ROW_REASON_PRIORITY + (EMPTY_REASON,)

_NEXT_STEPS = {
    STATUS_PASS: "pass_analyst_signal_to_research_packet",
    STATUS_WATCH: "watch_analyst_signal_before_packet_use",
    STATUS_BLOCK: "block_analyst_signal_until_memory_review",
}

_UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate_id",
    "candidate",
    "market_id",
    "market_slug",
    "question",
    "http://",
    "https://",
    "source_url",
    "source_text",
    "raw_text",
    "dsn",
    "table_name",
    "token",
    "secret",
    "credential",
    "private_key",
    "wallet",
    "order",
    "trade",
    "live",
    "sizing",
    "recommendation",
    "recommend",
    "postgres://",
)

__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_TEAM_SIGNAL_CONFLICT_MEMORY_ROUTER_CONFIG_VERSION",
    "SIGNAL_CONFLICT_MEMORY_ROUTE_STATUSES",
    "ResearchStrategyTeamSignalConflictMemoryRouterConfig",
    "ResearchStrategyTeamSignalConflictMemoryRouterReport",
    "ResearchStrategyTeamSignalConflictMemoryRouterRow",
    "ResearchStrategyTeamSignalConflictMemoryRouterSignal",
    "build_research_strategy_team_signal_conflict_memory_router_report",
    "research_strategy_team_signal_conflict_memory_router_report_digest",
    "research_strategy_team_signal_conflict_memory_router_report_public_payload",
)


@dataclass(frozen=True)
class ResearchStrategyTeamSignalConflictMemoryRouterConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_TEAM_SIGNAL_CONFLICT_MEMORY_ROUTER_CONFIG_VERSION
    )
    min_pass_calibration_memory_score: Decimal = Decimal("0.700000")
    min_watch_calibration_memory_score: Decimal = Decimal("0.500000")
    max_pass_memory_age_seconds: Decimal = Decimal("7776000.000000")
    max_watch_memory_age_seconds: Decimal = Decimal("15552000.000000")
    max_pass_evidence_age_seconds: Decimal = Decimal("86400.000000")
    max_watch_evidence_age_seconds: Decimal = Decimal("259200.000000")
    max_pass_disagreement_severity: Decimal = Decimal("0.250000")
    max_watch_disagreement_severity: Decimal = Decimal("0.500000")
    max_pass_liquidity_cost_pressure: Decimal = Decimal("0.300000")
    max_watch_liquidity_cost_pressure: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyTeamSignalConflictMemoryRouterConfig:
            raise TypeError(
                "ResearchStrategyTeamSignalConflictMemoryRouterConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyTeamSignalConflictMemoryRouterConfig,
            "config",
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_text("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_TEAM_SIGNAL_CONFLICT_MEMORY_ROUTER_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_pass_calibration_memory_score",
            "min_watch_calibration_memory_score",
            "max_pass_disagreement_severity",
            "max_watch_disagreement_severity",
            "max_pass_liquidity_cost_pressure",
            "max_watch_liquidity_cost_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_memory_age_seconds",
            "max_watch_memory_age_seconds",
            "max_pass_evidence_age_seconds",
            "max_watch_evidence_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if (
            self.min_watch_calibration_memory_score
            > self.min_pass_calibration_memory_score
        ):
            raise ValueError(
                "min_watch_calibration_memory_score must not exceed pass",
            )
        if self.max_watch_memory_age_seconds < self.max_pass_memory_age_seconds:
            raise ValueError("max_watch_memory_age_seconds must be at least pass")
        if self.max_watch_evidence_age_seconds < self.max_pass_evidence_age_seconds:
            raise ValueError("max_watch_evidence_age_seconds must be at least pass")
        if self.max_pass_disagreement_severity > self.max_watch_disagreement_severity:
            raise ValueError(
                "max_pass_disagreement_severity must not exceed watch",
            )
        if (
            self.max_pass_liquidity_cost_pressure
            > self.max_watch_liquidity_cost_pressure
        ):
            raise ValueError(
                "max_pass_liquidity_cost_pressure must not exceed watch",
            )
        require_paper_only_flags("team signal conflict memory router config", self)


@dataclass(frozen=True)
class ResearchStrategyTeamSignalConflictMemoryRouterSignal:
    route_ref: str
    participant_role: str
    analyst_label: str
    team_label: str
    analyst_signal_direction: str
    team_signal_direction: str
    calibration_memory_score: Decimal
    memory_observed_at: datetime
    evidence_observed_at: datetime
    disagreement_severity: Decimal
    liquidity_cost_pressure: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyTeamSignalConflictMemoryRouterSignal:
            raise TypeError(
                "ResearchStrategyTeamSignalConflictMemoryRouterSignal does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyTeamSignalConflictMemoryRouterSignal,
            "signal",
        )
        object.__setattr__(
            self,
            "route_ref",
            _require_public_text("route_ref", self.route_ref),
        )
        if self.participant_role != "analyst":
            raise ValueError("participant_role must be analyst")
        object.__setattr__(self, "participant_role", self.participant_role)
        object.__setattr__(
            self,
            "analyst_label",
            _require_public_text("analyst_label", self.analyst_label),
        )
        object.__setattr__(
            self,
            "team_label",
            _require_public_text("team_label", self.team_label),
        )
        object.__setattr__(
            self,
            "analyst_signal_direction",
            _require_member(
                "analyst_signal_direction",
                self.analyst_signal_direction,
                _DIRECTIONS,
            ),
        )
        object.__setattr__(
            self,
            "team_signal_direction",
            _require_member(
                "team_signal_direction",
                self.team_signal_direction,
                _DIRECTIONS,
            ),
        )
        object.__setattr__(
            self,
            "calibration_memory_score",
            _normalize_unit_decimal(
                "calibration_memory_score",
                self.calibration_memory_score,
            ),
        )
        object.__setattr__(
            self,
            "memory_observed_at",
            _as_utc("memory_observed_at", self.memory_observed_at),
        )
        object.__setattr__(
            self,
            "evidence_observed_at",
            _as_utc("evidence_observed_at", self.evidence_observed_at),
        )
        object.__setattr__(
            self,
            "disagreement_severity",
            _normalize_unit_decimal(
                "disagreement_severity",
                self.disagreement_severity,
            ),
        )
        object.__setattr__(
            self,
            "liquidity_cost_pressure",
            _normalize_unit_decimal(
                "liquidity_cost_pressure",
                self.liquidity_cost_pressure,
            ),
        )
        require_paper_only_flags("team signal conflict memory router signal", self)


@dataclass(frozen=True)
class ResearchStrategyTeamSignalConflictMemoryRouterRow:
    route_ref: str
    participant_role: str
    analyst_label: str
    team_label: str
    analyst_signal_direction: str
    team_signal_direction: str
    calibration_memory_score: Decimal
    memory_observed_at: datetime
    evidence_observed_at: datetime
    memory_age_seconds: Decimal
    evidence_age_seconds: Decimal
    max_watch_memory_age_seconds: Decimal
    max_watch_evidence_age_seconds: Decimal
    disagreement_severity: Decimal
    liquidity_cost_pressure: Decimal
    memory_freshness_score: Decimal
    evidence_freshness_score: Decimal
    conflict_pressure_score: Decimal
    route_score: Decimal
    route_status: str
    analyst_next_step: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyTeamSignalConflictMemoryRouterRow:
            raise TypeError(
                "ResearchStrategyTeamSignalConflictMemoryRouterRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyTeamSignalConflictMemoryRouterRow, "row")
        for field_name in ("route_ref", "analyst_label", "team_label"):
            object.__setattr__(
                self,
                field_name,
                _require_public_text(field_name, getattr(self, field_name)),
            )
        if self.participant_role != "analyst":
            raise ValueError("participant_role must be analyst")
        object.__setattr__(
            self,
            "analyst_signal_direction",
            _require_member(
                "analyst_signal_direction",
                self.analyst_signal_direction,
                _DIRECTIONS,
            ),
        )
        object.__setattr__(
            self,
            "team_signal_direction",
            _require_member(
                "team_signal_direction",
                self.team_signal_direction,
                _DIRECTIONS,
            ),
        )
        object.__setattr__(
            self,
            "memory_observed_at",
            _as_utc("memory_observed_at", self.memory_observed_at),
        )
        object.__setattr__(
            self,
            "evidence_observed_at",
            _as_utc("evidence_observed_at", self.evidence_observed_at),
        )
        for field_name in (
            "calibration_memory_score",
            "disagreement_severity",
            "liquidity_cost_pressure",
            "memory_freshness_score",
            "evidence_freshness_score",
            "conflict_pressure_score",
            "route_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "memory_age_seconds",
            "evidence_age_seconds",
            "max_watch_memory_age_seconds",
            "max_watch_evidence_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "route_status",
            _require_member("route_status", self.route_status, SIGNAL_CONFLICT_MEMORY_ROUTE_STATUSES),
        )
        object.__setattr__(
            self,
            "analyst_next_step",
            _require_public_text("analyst_next_step", self.analyst_next_step),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, _ROW_REASON_PRIORITY),
        )
        _validate_row(self)
        require_paper_only_flags("team signal conflict memory router row", self)


@dataclass(frozen=True)
class ResearchStrategyTeamSignalConflictMemoryRouterReport:
    generated_at: datetime
    config_version: str
    signal_count: Decimal
    analyst_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_route_score: Decimal
    max_disagreement_severity: Decimal
    max_liquidity_cost_pressure: Decimal
    report_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchStrategyTeamSignalConflictMemoryRouterRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyTeamSignalConflictMemoryRouterReport:
            raise TypeError(
                "ResearchStrategyTeamSignalConflictMemoryRouterReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyTeamSignalConflictMemoryRouterReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_text("config_version", self.config_version),
        )
        for field_name in (
            "signal_count",
            "analyst_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_route_score",
            "max_disagreement_severity",
            "max_liquidity_cost_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "report_status",
            _require_member(
                "report_status",
                self.report_status,
                SIGNAL_CONFLICT_MEMORY_ROUTE_STATUSES,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                _REPORT_REASON_PRIORITY,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        require_paper_only_flags("team signal conflict memory router report", self)
        expected_digest = _derived_validation_digest(self)
        if self.derived_validation_digest:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report payload")
        object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def public_payload(self) -> dict[str, Any]:
        return research_strategy_team_signal_conflict_memory_router_report_public_payload(
            self,
        )


def build_research_strategy_team_signal_conflict_memory_router_report(
    signals: Iterable[ResearchStrategyTeamSignalConflictMemoryRouterSignal],
    *,
    config: ResearchStrategyTeamSignalConflictMemoryRouterConfig | None = None,
    generated_at: datetime,
) -> ResearchStrategyTeamSignalConflictMemoryRouterReport:
    cfg = (
        config
        if config is not None
        else ResearchStrategyTeamSignalConflictMemoryRouterConfig()
    )
    if type(cfg) is not ResearchStrategyTeamSignalConflictMemoryRouterConfig:
        raise ValueError(
            "config must be exactly ResearchStrategyTeamSignalConflictMemoryRouterConfig",
        )
    require_paper_only_flags("team signal conflict memory router config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_signals = _normalize_signals(signals)
    rows = tuple(
        sorted(
            (
                _row_from_signal(
                    signal,
                    config=cfg,
                    generated_at=generated_at_utc,
                )
                for signal in normalized_signals
            ),
            key=_row_sort_key,
        ),
    )
    report_status = _report_status(rows)
    return ResearchStrategyTeamSignalConflictMemoryRouterReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        signal_count=_count_decimal(len(rows)),
        analyst_count=_count_decimal(len({row.analyst_label for row in rows})),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        average_route_score=_average_route_score(rows),
        max_disagreement_severity=_max_decimal(
            row.disagreement_severity for row in rows
        ),
        max_liquidity_cost_pressure=_max_decimal(
            row.liquidity_cost_pressure for row in rows
        ),
        report_status=report_status,
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_strategy_team_signal_conflict_memory_router_report_public_payload(
    value: object,
) -> dict[str, Any]:
    _require_supported_payload_input(value)
    _reject_unsafe_public_payload(value)
    payload = _payload_value(value)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _validate_payload_flags(payload, "payload")
    _reject_unsafe_public_payload(payload)
    _reject_raw_payload_numbers(payload)
    _validate_payload_digest(payload)
    return payload


def research_strategy_team_signal_conflict_memory_router_report_digest(
    report: ResearchStrategyTeamSignalConflictMemoryRouterReport,
) -> str:
    if type(report) is not ResearchStrategyTeamSignalConflictMemoryRouterReport:
        raise ValueError(
            "report must be exactly ResearchStrategyTeamSignalConflictMemoryRouterReport",
        )
    return report.derived_validation_digest


def _row_from_signal(
    signal: ResearchStrategyTeamSignalConflictMemoryRouterSignal,
    *,
    config: ResearchStrategyTeamSignalConflictMemoryRouterConfig,
    generated_at: datetime,
) -> ResearchStrategyTeamSignalConflictMemoryRouterRow:
    memory_age_seconds = _age_seconds(generated_at, signal.memory_observed_at)
    evidence_age_seconds = _age_seconds(generated_at, signal.evidence_observed_at)
    memory_freshness_score = _freshness_score(
        memory_age_seconds,
        config.max_watch_memory_age_seconds,
    )
    evidence_freshness_score = _freshness_score(
        evidence_age_seconds,
        config.max_watch_evidence_age_seconds,
    )
    conflict_pressure_score = _ratio(
        signal.disagreement_severity + signal.liquidity_cost_pressure,
        _TWO,
    )
    reason_codes = _row_reason_codes(
        signal,
        memory_age_seconds=memory_age_seconds,
        evidence_age_seconds=evidence_age_seconds,
        config=config,
    )
    route_status = _status_from_reason_codes(reason_codes)
    return ResearchStrategyTeamSignalConflictMemoryRouterRow(
        route_ref=signal.route_ref,
        participant_role=signal.participant_role,
        analyst_label=signal.analyst_label,
        team_label=signal.team_label,
        analyst_signal_direction=signal.analyst_signal_direction,
        team_signal_direction=signal.team_signal_direction,
        calibration_memory_score=signal.calibration_memory_score,
        memory_observed_at=signal.memory_observed_at,
        evidence_observed_at=signal.evidence_observed_at,
        memory_age_seconds=memory_age_seconds,
        evidence_age_seconds=evidence_age_seconds,
        max_watch_memory_age_seconds=config.max_watch_memory_age_seconds,
        max_watch_evidence_age_seconds=config.max_watch_evidence_age_seconds,
        disagreement_severity=signal.disagreement_severity,
        liquidity_cost_pressure=signal.liquidity_cost_pressure,
        memory_freshness_score=memory_freshness_score,
        evidence_freshness_score=evidence_freshness_score,
        conflict_pressure_score=conflict_pressure_score,
        route_score=_route_score(
            signal.calibration_memory_score,
            memory_freshness_score,
            evidence_freshness_score,
            signal.disagreement_severity,
            signal.liquidity_cost_pressure,
        ),
        route_status=route_status,
        analyst_next_step=_NEXT_STEPS[route_status],
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    signal: ResearchStrategyTeamSignalConflictMemoryRouterSignal,
    *,
    memory_age_seconds: Decimal,
    evidence_age_seconds: Decimal,
    config: ResearchStrategyTeamSignalConflictMemoryRouterConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if signal.calibration_memory_score < config.min_watch_calibration_memory_score:
        reasons.append(CALIBRATION_BLOCK_REASON)
    elif signal.calibration_memory_score < config.min_pass_calibration_memory_score:
        reasons.append(CALIBRATION_WATCH_REASON)
    if memory_age_seconds > config.max_watch_memory_age_seconds:
        reasons.append(MEMORY_FRESHNESS_BLOCK_REASON)
    elif memory_age_seconds > config.max_pass_memory_age_seconds:
        reasons.append(MEMORY_FRESHNESS_WATCH_REASON)
    if evidence_age_seconds > config.max_watch_evidence_age_seconds:
        reasons.append(EVIDENCE_FRESHNESS_BLOCK_REASON)
    elif evidence_age_seconds > config.max_pass_evidence_age_seconds:
        reasons.append(EVIDENCE_FRESHNESS_WATCH_REASON)
    if signal.disagreement_severity > config.max_watch_disagreement_severity:
        reasons.append(DISAGREEMENT_SEVERITY_BLOCK_REASON)
    elif signal.disagreement_severity > config.max_pass_disagreement_severity:
        reasons.append(DISAGREEMENT_SEVERITY_WATCH_REASON)
    if signal.liquidity_cost_pressure > config.max_watch_liquidity_cost_pressure:
        reasons.append(LIQUIDITY_COST_PRESSURE_BLOCK_REASON)
    elif signal.liquidity_cost_pressure > config.max_pass_liquidity_cost_pressure:
        reasons.append(LIQUIDITY_COST_PRESSURE_WATCH_REASON)
    if not reasons:
        reasons.append(PASS_REASON)
    return _normalize_reason_codes("reason_codes", tuple(reasons), _ROW_REASON_PRIORITY)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason in _BLOCK_REASONS for reason in reason_codes):
        return STATUS_BLOCK
    if reason_codes == (PASS_REASON,):
        return STATUS_PASS
    return STATUS_WATCH


def _report_status(
    rows: tuple[ResearchStrategyTeamSignalConflictMemoryRouterRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.route_status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.route_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchStrategyTeamSignalConflictMemoryRouterRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    found = {reason for row in rows for reason in row.reason_codes}
    return tuple(reason for reason in _REPORT_REASON_PRIORITY if reason in found)


def _freshness_score(age_seconds: Decimal, max_watch_age_seconds: Decimal) -> Decimal:
    if max_watch_age_seconds == _ZERO:
        return _ONE if age_seconds == _ZERO else _ZERO
    if age_seconds >= max_watch_age_seconds:
        return _ZERO
    return _normalize_unit_decimal(
        "freshness_score",
        _ONE - _ratio(age_seconds, max_watch_age_seconds),
    )


def _route_score(
    calibration_memory_score: Decimal,
    memory_freshness_score: Decimal,
    evidence_freshness_score: Decimal,
    disagreement_severity: Decimal,
    liquidity_cost_pressure: Decimal,
) -> Decimal:
    return _ratio(
        calibration_memory_score
        + memory_freshness_score
        + evidence_freshness_score
        + (_ONE - disagreement_severity)
        + (_ONE - liquidity_cost_pressure),
        _FIVE,
    )


def _normalize_signals(
    signals: Iterable[ResearchStrategyTeamSignalConflictMemoryRouterSignal],
) -> tuple[ResearchStrategyTeamSignalConflictMemoryRouterSignal, ...]:
    if isinstance(signals, (str, bytes)):
        raise ValueError("signals must be an iterable")
    try:
        normalized = tuple(signals)
    except TypeError as exc:
        raise ValueError("signals must be an iterable") from exc
    route_refs: list[str] = []
    for signal in normalized:
        if type(signal) is not ResearchStrategyTeamSignalConflictMemoryRouterSignal:
            raise ValueError(
                "signals must contain ResearchStrategyTeamSignalConflictMemoryRouterSignal",
            )
        require_paper_only_flags("team signal conflict memory router signal", signal)
        route_refs.append(signal.route_ref)
    if len(set(route_refs)) != len(route_refs):
        raise ValueError("route_ref values must be unique")
    return normalized


def _normalize_rows(
    rows: object,
) -> tuple[ResearchStrategyTeamSignalConflictMemoryRouterRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not ResearchStrategyTeamSignalConflictMemoryRouterRow:
            raise ValueError(
                "rows must contain ResearchStrategyTeamSignalConflictMemoryRouterRow",
            )
        require_paper_only_flags("team signal conflict memory router row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    return normalized


def _row_sort_key(
    row: ResearchStrategyTeamSignalConflictMemoryRouterRow,
) -> tuple[int, str, str]:
    return (_STATUS_SORT_WEIGHT[row.route_status], row.route_ref, row.analyst_label)


def _validate_row(row: ResearchStrategyTeamSignalConflictMemoryRouterRow) -> None:
    if row.memory_freshness_score != _freshness_score(
        row.memory_age_seconds,
        row.max_watch_memory_age_seconds,
    ):
        raise ValueError("memory_freshness_score must match ages")
    if row.evidence_freshness_score != _freshness_score(
        row.evidence_age_seconds,
        row.max_watch_evidence_age_seconds,
    ):
        raise ValueError("evidence_freshness_score must match ages")
    if row.conflict_pressure_score != _ratio(
        row.disagreement_severity + row.liquidity_cost_pressure,
        _TWO,
    ):
        raise ValueError("conflict_pressure_score must match inputs")
    expected_route_score = _route_score(
        row.calibration_memory_score,
        row.memory_freshness_score,
        row.evidence_freshness_score,
        row.disagreement_severity,
        row.liquidity_cost_pressure,
    )
    if row.route_score != expected_route_score:
        raise ValueError("route_score must match inputs")
    if row.route_status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("route_status must match reason_codes")
    if row.analyst_next_step != _NEXT_STEPS[row.route_status]:
        raise ValueError("analyst_next_step must match route_status")


def _validate_report(report: ResearchStrategyTeamSignalConflictMemoryRouterReport) -> None:
    if report.signal_count != _count_decimal(len(report.rows)):
        raise ValueError("signal_count must match rows")
    if report.analyst_count != _count_decimal(len({row.analyst_label for row in report.rows})):
        raise ValueError("analyst_count must match rows")
    if report.pass_count != _status_count(report.rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    if report.average_route_score != _average_route_score(report.rows):
        raise ValueError("average_route_score must match rows")
    if report.max_disagreement_severity != _max_decimal(
        row.disagreement_severity for row in report.rows
    ):
        raise ValueError("max_disagreement_severity must match rows")
    if report.max_liquidity_cost_pressure != _max_decimal(
        row.liquidity_cost_pressure for row in report.rows
    ):
        raise ValueError("max_liquidity_cost_pressure must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _average_route_score(
    rows: tuple[ResearchStrategyTeamSignalConflictMemoryRouterRow, ...],
) -> Decimal:
    if not rows:
        return _ZERO
    return _ratio(
        _sum_decimal(row.route_score for row in rows),
        _count_decimal(len(rows)),
    )


def _status_count(
    rows: tuple[ResearchStrategyTeamSignalConflictMemoryRouterRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.route_status == status))


def _max_decimal(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return _ZERO
    return max(items)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = _ZERO
    for value in values:
        total += value
    return _quantize(total)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    elapsed = generated_at - observed_at
    age = Decimal(elapsed.days * 86400 + elapsed.seconds) + _ratio(
        Decimal(elapsed.microseconds),
        _MICROSECONDS_PER_SECOND,
    )
    if age < _ZERO:
        raise ValueError("observed timestamps must not be after generated_at")
    return _normalize_nonnegative_decimal("age_seconds", age)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        raise ValueError("denominator must not be zero")
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANTUM)


def _count_decimal(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value).quantize(_COUNT_QUANTUM)


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return value.quantize(_COUNT_QUANTUM)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    quantized = _quantize(value)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    quantized = _normalize_nonnegative_decimal(field_name, value)
    if quantized > _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return quantized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} must not contain unsafe public text")
    return value


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> str:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")
    return value


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    if not items:
        raise ValueError(f"{field_name} must not be empty")
    for item in items:
        _require_member(field_name, item, allowed)
    normalized = tuple(reason for reason in allowed if reason in items)
    if set(normalized) != set(items):
        raise ValueError(f"{field_name} contains unsupported values")
    return normalized


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a sha-256 hex digest")
    return value


def _require_supported_payload_input(value: object) -> None:
    if type(value) in (dict, ResearchStrategyTeamSignalConflictMemoryRouterReport):
        return
    raise ValueError("payload input must be a report or dict")


def _payload_value(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            key: _payload_value(item)
            for key, item in asdict(value).items()
        }
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("payload Decimal values must be finite")
        return format(value, "f")
    if isinstance(value, datetime):
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is float:
        raise ValueError("payload must not contain raw numeric values")
    if type(value) is int:
        raise ValueError("payload must not contain raw numeric values")
    if value is None or type(value) in (str, bool):
        return value
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        payload: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload object keys must be strings")
            payload[key] = _payload_value(item)
        return payload
    raise ValueError("payload value is not JSON serializable")


def _validate_payload_flags(payload: dict[str, Any], label: str) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")
    rows = payload.get("rows", ())
    if isinstance(rows, list):
        for row in rows:
            if isinstance(row, dict):
                _validate_payload_flags(row, "payload row")


def _reject_raw_payload_numbers(value: object) -> None:
    if type(value) in (int, float):
        raise ValueError("payload must not contain raw numeric values")
    if isinstance(value, dict):
        for item in value.values():
            _reject_raw_payload_numbers(item)
    elif isinstance(value, list):
        for item in value:
            _reject_raw_payload_numbers(item)


def _reject_unsafe_public_payload(value: object) -> None:
    for text in _iter_public_text(value):
        lowered = text.lower()
        if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
            raise ValueError("unsafe public payload content")


def _iter_public_text(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_public_text(asdict(value))
    if isinstance(value, dict):
        texts: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload object keys must be strings")
            texts.append(key)
            texts.extend(_iter_public_text(item))
        return tuple(texts)
    if isinstance(value, (list, tuple)):
        texts = []
        for item in value:
            texts.extend(_iter_public_text(item))
        return tuple(texts)
    if type(value) is str:
        return (value,)
    return ()


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", digest)
    expected = _payload_digest(payload)
    if digest != expected:
        raise ValueError("derived_validation_digest must match payload")


def _derived_validation_digest(
    report: ResearchStrategyTeamSignalConflictMemoryRouterReport,
) -> str:
    return _payload_digest(_payload_value(report))


def _payload_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()
