"""Pure report-only domain-team signal memory router."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_RESEARCH_STRATEGY_DOMAIN_TEAM_SIGNAL_MEMORY_ROUTER_CONFIG_VERSION = (
    "research-strategy-domain-team-signal-memory-router-report-v0"
)
STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
RESEARCH_STRATEGY_DOMAIN_TEAM_SIGNAL_MEMORY_ROUTER_STATUSES = (
    STATUS_PASS,
    STATUS_WATCH,
    STATUS_BLOCK,
)

PASS_REASON = "domain_team_signal_memory_router_pass"
EMPTY_REASON = "domain_team_signal_memory_router_empty"
DOMAIN_MEMORY_BLOCK_REASON = "domain_memory_block"
DOMAIN_MEMORY_WATCH_REASON = "domain_memory_watch"
TEAM_SIGNAL_BLOCK_REASON = "team_signal_block"
TEAM_SIGNAL_WATCH_REASON = "team_signal_watch"
MEMORY_AGE_BLOCK_REASON = "memory_age_block"
MEMORY_AGE_WATCH_REASON = "memory_age_watch"
ROUTER_CONFLICT_BLOCK_REASON = "router_conflict_block"
ROUTER_CONFLICT_WATCH_REASON = "router_conflict_watch"

_BLOCK_REASONS = frozenset(
    (
        DOMAIN_MEMORY_BLOCK_REASON,
        TEAM_SIGNAL_BLOCK_REASON,
        MEMORY_AGE_BLOCK_REASON,
        ROUTER_CONFLICT_BLOCK_REASON,
    ),
)
_ROW_REASON_PRIORITY = (
    DOMAIN_MEMORY_BLOCK_REASON,
    TEAM_SIGNAL_BLOCK_REASON,
    MEMORY_AGE_BLOCK_REASON,
    ROUTER_CONFLICT_BLOCK_REASON,
    DOMAIN_MEMORY_WATCH_REASON,
    TEAM_SIGNAL_WATCH_REASON,
    MEMORY_AGE_WATCH_REASON,
    ROUTER_CONFLICT_WATCH_REASON,
    PASS_REASON,
)
_REPORT_REASON_PRIORITY = _ROW_REASON_PRIORITY + (EMPTY_REASON,)
_STATUS_SORT_WEIGHT = {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}
_NEXT_STEPS = {
    STATUS_PASS: "pass_signal_to_research_packet",
    STATUS_WATCH: "watch_signal_before_research_packet_use",
    STATUS_BLOCK: "block_signal_until_domain_team_memory_review",
}

_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_FOUR = Decimal("4.000000")
_QUANTUM = Decimal("0.000001")
_COUNT_QUANTUM = Decimal("1")
_MICROSECONDS_PER_SECOND = Decimal("1000000.000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

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
    "raw_candidate",
    "raw_market",
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
    "DEFAULT_RESEARCH_STRATEGY_DOMAIN_TEAM_SIGNAL_MEMORY_ROUTER_CONFIG_VERSION",
    "RESEARCH_STRATEGY_DOMAIN_TEAM_SIGNAL_MEMORY_ROUTER_STATUSES",
    "ResearchStrategyDomainTeamSignalMemoryRouterConfig",
    "ResearchStrategyDomainTeamSignalMemoryRouterReport",
    "ResearchStrategyDomainTeamSignalMemoryRouterRow",
    "ResearchStrategyDomainTeamSignalMemoryRouterSignal",
    "build_research_strategy_domain_team_signal_memory_router_report",
    "research_strategy_domain_team_signal_memory_router_report_digest",
    "research_strategy_domain_team_signal_memory_router_report_payload",
)


@dataclass(frozen=True)
class ResearchStrategyDomainTeamSignalMemoryRouterConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_DOMAIN_TEAM_SIGNAL_MEMORY_ROUTER_CONFIG_VERSION
    )
    min_pass_domain_memory_score: Decimal = Decimal("0.700000")
    min_watch_domain_memory_score: Decimal = Decimal("0.500000")
    min_pass_team_signal_score: Decimal = Decimal("0.700000")
    min_watch_team_signal_score: Decimal = Decimal("0.500000")
    max_pass_memory_age_seconds: Decimal = Decimal("604800.000000")
    max_watch_memory_age_seconds: Decimal = Decimal("1209600.000000")
    max_pass_router_conflict_score: Decimal = Decimal("0.250000")
    max_watch_router_conflict_score: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyDomainTeamSignalMemoryRouterConfig:
            raise TypeError(
                "ResearchStrategyDomainTeamSignalMemoryRouterConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyDomainTeamSignalMemoryRouterConfig,
            "config",
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_text("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_DOMAIN_TEAM_SIGNAL_MEMORY_ROUTER_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_pass_domain_memory_score",
            "min_watch_domain_memory_score",
            "min_pass_team_signal_score",
            "min_watch_team_signal_score",
            "max_pass_router_conflict_score",
            "max_watch_router_conflict_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_memory_age_seconds",
            "max_watch_memory_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_watch_domain_memory_score > self.min_pass_domain_memory_score:
            raise ValueError("min_watch_domain_memory_score must not exceed pass")
        if self.min_watch_team_signal_score > self.min_pass_team_signal_score:
            raise ValueError("min_watch_team_signal_score must not exceed pass")
        if self.max_watch_memory_age_seconds < self.max_pass_memory_age_seconds:
            raise ValueError("max_watch_memory_age_seconds must be at least pass")
        if self.max_pass_router_conflict_score > self.max_watch_router_conflict_score:
            raise ValueError("max_pass_router_conflict_score must not exceed watch")
        require_paper_only_flags("domain team signal memory router config", self)


@dataclass(frozen=True)
class ResearchStrategyDomainTeamSignalMemoryRouterSignal:
    route_ref: str
    domain_label: str
    team_label: str
    signal_label: str
    domain_memory_score: Decimal
    team_signal_score: Decimal
    memory_observed_at: datetime
    router_conflict_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyDomainTeamSignalMemoryRouterSignal:
            raise TypeError(
                "ResearchStrategyDomainTeamSignalMemoryRouterSignal does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyDomainTeamSignalMemoryRouterSignal,
            "signal",
        )
        for field_name in ("route_ref", "domain_label", "team_label", "signal_label"):
            object.__setattr__(
                self,
                field_name,
                _require_public_text(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "domain_memory_score",
            "team_signal_score",
            "router_conflict_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "memory_observed_at",
            _as_utc("memory_observed_at", self.memory_observed_at),
        )
        require_paper_only_flags("domain team signal memory router signal", self)


@dataclass(frozen=True)
class ResearchStrategyDomainTeamSignalMemoryRouterRow:
    route_ref: str
    domain_label: str
    team_label: str
    signal_label: str
    domain_memory_score: Decimal
    team_signal_score: Decimal
    memory_observed_at: datetime
    memory_age_seconds: Decimal
    max_watch_memory_age_seconds: Decimal
    router_conflict_score: Decimal
    memory_freshness_score: Decimal
    router_score: Decimal
    status: str
    router_next_step: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyDomainTeamSignalMemoryRouterRow:
            raise TypeError(
                "ResearchStrategyDomainTeamSignalMemoryRouterRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyDomainTeamSignalMemoryRouterRow, "row")
        for field_name in ("route_ref", "domain_label", "team_label", "signal_label"):
            object.__setattr__(
                self,
                field_name,
                _require_public_text(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "memory_observed_at",
            _as_utc("memory_observed_at", self.memory_observed_at),
        )
        for field_name in (
            "domain_memory_score",
            "team_signal_score",
            "router_conflict_score",
            "memory_freshness_score",
            "router_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("memory_age_seconds", "max_watch_memory_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "status", _require_status("status", self.status))
        object.__setattr__(
            self,
            "router_next_step",
            _require_public_text("router_next_step", self.router_next_step),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, _ROW_REASON_PRIORITY),
        )
        _validate_row(self)
        require_paper_only_flags("domain team signal memory router row", self)


@dataclass(frozen=True)
class ResearchStrategyDomainTeamSignalMemoryRouterReport:
    generated_at: datetime
    config_version: str
    signal_count: Decimal
    domain_count: Decimal
    team_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_router_score: Decimal
    lowest_domain_memory_score: Decimal
    lowest_team_signal_score: Decimal
    highest_router_conflict_score: Decimal
    highest_memory_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchStrategyDomainTeamSignalMemoryRouterRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyDomainTeamSignalMemoryRouterReport:
            raise TypeError(
                "ResearchStrategyDomainTeamSignalMemoryRouterReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyDomainTeamSignalMemoryRouterReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_text("config_version", self.config_version),
        )
        for field_name in (
            "signal_count",
            "domain_count",
            "team_count",
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
            "average_router_score",
            "lowest_domain_memory_score",
            "lowest_team_signal_score",
            "highest_router_conflict_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "highest_memory_age_seconds",
            _normalize_nonnegative_decimal(
                "highest_memory_age_seconds",
                self.highest_memory_age_seconds,
            ),
        )
        object.__setattr__(self, "status", _require_status("status", self.status))
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
        require_paper_only_flags("domain team signal memory router report", self)
        expected_digest = _derived_validation_digest(self)
        if self.derived_validation_digest:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report payload")
        object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def public_payload(self) -> dict[str, Any]:
        return research_strategy_domain_team_signal_memory_router_report_payload(self)


def build_research_strategy_domain_team_signal_memory_router_report(
    signals: Iterable[ResearchStrategyDomainTeamSignalMemoryRouterSignal],
    *,
    config: ResearchStrategyDomainTeamSignalMemoryRouterConfig | None = None,
    generated_at: datetime,
) -> ResearchStrategyDomainTeamSignalMemoryRouterReport:
    cfg = config or ResearchStrategyDomainTeamSignalMemoryRouterConfig()
    if type(cfg) is not ResearchStrategyDomainTeamSignalMemoryRouterConfig:
        raise ValueError(
            "config must be exactly ResearchStrategyDomainTeamSignalMemoryRouterConfig",
        )
    require_paper_only_flags("domain team signal memory router config", cfg)
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
    return ResearchStrategyDomainTeamSignalMemoryRouterReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        signal_count=_count_decimal(len(rows)),
        domain_count=_count_decimal(len({row.domain_label for row in rows})),
        team_count=_count_decimal(len({row.team_label for row in rows})),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        average_router_score=_average_router_score(rows),
        lowest_domain_memory_score=_min_decimal(row.domain_memory_score for row in rows),
        lowest_team_signal_score=_min_decimal(row.team_signal_score for row in rows),
        highest_router_conflict_score=_max_decimal(
            row.router_conflict_score for row in rows
        ),
        highest_memory_age_seconds=_max_decimal(row.memory_age_seconds for row in rows),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_strategy_domain_team_signal_memory_router_report_payload(
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


def research_strategy_domain_team_signal_memory_router_report_digest(
    report: ResearchStrategyDomainTeamSignalMemoryRouterReport,
) -> str:
    if type(report) is not ResearchStrategyDomainTeamSignalMemoryRouterReport:
        raise ValueError(
            "report must be exactly ResearchStrategyDomainTeamSignalMemoryRouterReport",
        )
    return report.derived_validation_digest


def _row_from_signal(
    signal: ResearchStrategyDomainTeamSignalMemoryRouterSignal,
    *,
    config: ResearchStrategyDomainTeamSignalMemoryRouterConfig,
    generated_at: datetime,
) -> ResearchStrategyDomainTeamSignalMemoryRouterRow:
    memory_age_seconds = _age_seconds(generated_at, signal.memory_observed_at)
    memory_freshness_score = _freshness_score(
        memory_age_seconds,
        config.max_watch_memory_age_seconds,
    )
    reason_codes = _row_reason_codes(
        signal,
        memory_age_seconds=memory_age_seconds,
        config=config,
    )
    status = _status_from_reason_codes(reason_codes)
    return ResearchStrategyDomainTeamSignalMemoryRouterRow(
        route_ref=signal.route_ref,
        domain_label=signal.domain_label,
        team_label=signal.team_label,
        signal_label=signal.signal_label,
        domain_memory_score=signal.domain_memory_score,
        team_signal_score=signal.team_signal_score,
        memory_observed_at=signal.memory_observed_at,
        memory_age_seconds=memory_age_seconds,
        max_watch_memory_age_seconds=config.max_watch_memory_age_seconds,
        router_conflict_score=signal.router_conflict_score,
        memory_freshness_score=memory_freshness_score,
        router_score=_router_score(
            signal.domain_memory_score,
            signal.team_signal_score,
            memory_freshness_score,
            signal.router_conflict_score,
        ),
        status=status,
        router_next_step=_NEXT_STEPS[status],
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    signal: ResearchStrategyDomainTeamSignalMemoryRouterSignal,
    *,
    memory_age_seconds: Decimal,
    config: ResearchStrategyDomainTeamSignalMemoryRouterConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if signal.domain_memory_score < config.min_watch_domain_memory_score:
        reasons.append(DOMAIN_MEMORY_BLOCK_REASON)
    elif signal.domain_memory_score < config.min_pass_domain_memory_score:
        reasons.append(DOMAIN_MEMORY_WATCH_REASON)
    if signal.team_signal_score < config.min_watch_team_signal_score:
        reasons.append(TEAM_SIGNAL_BLOCK_REASON)
    elif signal.team_signal_score < config.min_pass_team_signal_score:
        reasons.append(TEAM_SIGNAL_WATCH_REASON)
    if memory_age_seconds > config.max_watch_memory_age_seconds:
        reasons.append(MEMORY_AGE_BLOCK_REASON)
    elif memory_age_seconds > config.max_pass_memory_age_seconds:
        reasons.append(MEMORY_AGE_WATCH_REASON)
    if signal.router_conflict_score > config.max_watch_router_conflict_score:
        reasons.append(ROUTER_CONFLICT_BLOCK_REASON)
    elif signal.router_conflict_score > config.max_pass_router_conflict_score:
        reasons.append(ROUTER_CONFLICT_WATCH_REASON)
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
    rows: tuple[ResearchStrategyDomainTeamSignalMemoryRouterRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchStrategyDomainTeamSignalMemoryRouterRow, ...],
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
        "memory_freshness_score",
        _ONE - _ratio(age_seconds, max_watch_age_seconds),
    )


def _router_score(
    domain_memory_score: Decimal,
    team_signal_score: Decimal,
    memory_freshness_score: Decimal,
    router_conflict_score: Decimal,
) -> Decimal:
    return _ratio(
        domain_memory_score
        + team_signal_score
        + memory_freshness_score
        + (_ONE - router_conflict_score),
        _FOUR,
    )


def _normalize_signals(
    signals: Iterable[ResearchStrategyDomainTeamSignalMemoryRouterSignal],
) -> tuple[ResearchStrategyDomainTeamSignalMemoryRouterSignal, ...]:
    if isinstance(signals, (str, bytes)):
        raise ValueError("signals must be an iterable")
    try:
        normalized = tuple(signals)
    except TypeError as exc:
        raise ValueError("signals must be an iterable") from exc
    route_refs: list[str] = []
    for signal in normalized:
        if type(signal) is not ResearchStrategyDomainTeamSignalMemoryRouterSignal:
            raise ValueError(
                "signals must contain ResearchStrategyDomainTeamSignalMemoryRouterSignal",
            )
        require_paper_only_flags("domain team signal memory router signal", signal)
        route_refs.append(signal.route_ref)
    if len(set(route_refs)) != len(route_refs):
        raise ValueError("route_ref values must be unique")
    return normalized


def _normalize_rows(
    rows: object,
) -> tuple[ResearchStrategyDomainTeamSignalMemoryRouterRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not ResearchStrategyDomainTeamSignalMemoryRouterRow:
            raise ValueError(
                "rows must contain ResearchStrategyDomainTeamSignalMemoryRouterRow",
            )
        require_paper_only_flags("domain team signal memory router row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    return normalized


def _row_sort_key(
    row: ResearchStrategyDomainTeamSignalMemoryRouterRow,
) -> tuple[int, str, str, str]:
    return (_STATUS_SORT_WEIGHT[row.status], row.route_ref, row.domain_label, row.team_label)


def _validate_row(row: ResearchStrategyDomainTeamSignalMemoryRouterRow) -> None:
    if row.memory_freshness_score != _freshness_score(
        row.memory_age_seconds,
        row.max_watch_memory_age_seconds,
    ):
        raise ValueError("memory_freshness_score must match ages")
    expected_router_score = _router_score(
        row.domain_memory_score,
        row.team_signal_score,
        row.memory_freshness_score,
        row.router_conflict_score,
    )
    if row.router_score != expected_router_score:
        raise ValueError("router_score must match inputs")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.router_next_step != _NEXT_STEPS[row.status]:
        raise ValueError("router_next_step must match status")


def _validate_report(report: ResearchStrategyDomainTeamSignalMemoryRouterReport) -> None:
    if report.signal_count != _count_decimal(len(report.rows)):
        raise ValueError("signal_count must match rows")
    if report.domain_count != _count_decimal(len({row.domain_label for row in report.rows})):
        raise ValueError("domain_count must match rows")
    if report.team_count != _count_decimal(len({row.team_label for row in report.rows})):
        raise ValueError("team_count must match rows")
    if report.pass_count != _status_count(report.rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    if report.average_router_score != _average_router_score(report.rows):
        raise ValueError("average_router_score must match rows")
    if report.lowest_domain_memory_score != _min_decimal(
        row.domain_memory_score for row in report.rows
    ):
        raise ValueError("lowest_domain_memory_score must match rows")
    if report.lowest_team_signal_score != _min_decimal(
        row.team_signal_score for row in report.rows
    ):
        raise ValueError("lowest_team_signal_score must match rows")
    if report.highest_router_conflict_score != _max_decimal(
        row.router_conflict_score for row in report.rows
    ):
        raise ValueError("highest_router_conflict_score must match rows")
    if report.highest_memory_age_seconds != _max_decimal(
        row.memory_age_seconds for row in report.rows
    ):
        raise ValueError("highest_memory_age_seconds must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _average_router_score(
    rows: tuple[ResearchStrategyDomainTeamSignalMemoryRouterRow, ...],
) -> Decimal:
    if not rows:
        return _ZERO
    return _ratio(_sum_decimal(row.router_score for row in rows), _count_decimal(len(rows)))


def _status_count(
    rows: tuple[ResearchStrategyDomainTeamSignalMemoryRouterRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _min_decimal(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return _ZERO
    return min(items)


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
        raise ValueError(f"{field_name} has unsafe public text")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in RESEARCH_STRATEGY_DOMAIN_TEAM_SIGNAL_MEMORY_ROUTER_STATUSES:
        raise ValueError(
            f"{field_name} must be one of "
            f"{RESEARCH_STRATEGY_DOMAIN_TEAM_SIGNAL_MEMORY_ROUTER_STATUSES}",
        )
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
        if type(item) is not str or item not in allowed:
            raise ValueError(f"{field_name} contains unsupported values")
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
    if type(value) in (dict, ResearchStrategyDomainTeamSignalMemoryRouterReport):
        return
    raise ValueError("payload input must be a report or dict")


def _payload_value(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {key: _payload_value(item) for key, item in asdict(value).items()}
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal values must be finite")
        return format(value, "f")
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is float or type(value) is int:
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
    report: ResearchStrategyDomainTeamSignalMemoryRouterReport,
) -> str:
    return _payload_digest(_payload_value(report))


def _payload_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()
